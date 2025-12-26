from typing import Optional
import logging
import traceback
from datetime import datetime

import jwt
from fastapi import Depends, Header, HTTPException, Request

from app.core.ctx import CTX_USER_ID
from app.models import Role, User
from app.settings import settings
import os
from app.core.tdengine_connector import TDengineConnector
from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    APIException
)
from app.core.cache import cache_manager, permission_cache
from app.core.detailed_logger import detailed_logger
from app.core.error_enhancement_middleware import error_context_collector

logger = logging.getLogger(__name__)


async def get_tdengine_connector() -> TDengineConnector:
    # TDengine连接配置（从环境变量读取，默认值为开发环境配置）
    host = os.getenv("TDENGINE_HOST", "localhost")
    port = int(os.getenv("TDENGINE_PORT", "6041"))
    user = os.getenv("TDENGINE_USER", "root")
    password = os.getenv("TDENGINE_PASSWORD", "taosdata")
    # Fix: Load database from settings/env
    database = os.getenv("TDENGINE_DATABASE", settings.TDENGINE_DATABASE)
    
    logger.info(f"TDengine连接配置: host={host}, port={port}, user={user}, database={database}")
    
    return TDengineConnector(host=host, port=port, user=user, password=password, database=database)


class AuthControl:
    @classmethod
    async def is_authed(
        cls, 
        token: Optional[str] = Header(None, description="token验证"),
        authorization: Optional[str] = Header(None, description="Authorization头"),
        request: Request = None  # 添加 request 参数
    ) -> Optional["User"]:
        auth_start_time = datetime.now()
        user = None
        auth_token = None
        
        try:
            # 优先使用token头，如果没有则尝试从Authorization头提取
            auth_token = token
            if not auth_token and authorization:
                # 从Authorization头提取token（支持Bearer格式）
                if authorization.startswith("Bearer "):
                    auth_token = authorization[7:]  # 移除"Bearer "前缀
                else:
                    auth_token = authorization
            
            # 如果 Header 中都没有，尝试从 request.query_params 获取 (临时兼容)
            if not auth_token and request:
                auth_token = request.query_params.get("token")
            
            # 记录认证调试信息
            debug_info = detailed_logger.log_authentication_debug(
                token=auth_token,
                auth_result="开始认证",
                error_details=None
            )
            
            # 检查token是否存在
            if not auth_token:
                detailed_logger.log_authentication_debug(
                    token=None,
                    auth_result="失败 - 缺少令牌",
                    error_details={"reason": "TOKEN_MISSING"}
                )
                raise AuthenticationException(
                    message="缺少访问令牌",
                    details={"error_code": "TOKEN_MISSING"}
                )
            
            # TODO: 简化开发环境认证 - 后期需要移除
            if auth_token == "dev":
                user = await User.filter().first()
                user_id = user.id
                detailed_logger.log_authentication_debug(
                    token=auth_token,
                    user_info={"user_id": user_id, "username": user.username},
                    auth_result="成功 - 开发模式",
                    error_details=None
                )
            else:
                # 解码JWT令牌
                decode_data = jwt.decode(auth_token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
                user_id = decode_data.get("user_id")
                
                # 查询用户信息（简化数据库操作）
                user = await User.filter(id=user_id).first()
                
                if user:
                    # 将用户信息注入 request.state (如果 request 存在)
                    if request:
                        request.state.user = user
                        request.state.user_id = user.id

                    detailed_logger.log_authentication_debug(
                        token=auth_token,
                        user_info={
                            "user_id": user.id, 
                            "username": user.username,
                            "is_superuser": user.is_superuser,
                            "status": getattr(user, 'status', 'unknown')
                        },
                        auth_result="成功 - JWT验证",
                        error_details=None
                    )
                
            if not user:
                detailed_logger.log_authentication_debug(
                    token=auth_token,
                    auth_result="失败 - 用户不存在",
                    error_details={"reason": "USER_NOT_FOUND", "user_id": user_id}
                )
                raise AuthenticationException(
                    message="用户不存在或已被禁用",
                    details={"error_code": "USER_NOT_FOUND", "user_id": user_id}
                )
            
            # 设置用户上下文
            CTX_USER_ID.set(int(user.id))
            
            # 记录认证性能指标
            auth_duration = (datetime.now() - auth_start_time).total_seconds() * 1000
            detailed_logger.log_performance_metrics(
                operation_name="user_authentication",
                duration_ms=auth_duration,
                additional_metrics={
                    "user_id": user.id,
                    "auth_method": "dev" if auth_token == "dev" else "jwt",
                    "success": True
                }
            )
            
            return user
            
        except jwt.DecodeError as e:
            detailed_logger.log_authentication_debug(
                token=auth_token,
                auth_result="失败 - JWT解码错误",
                error_details={"reason": "TOKEN_DECODE_ERROR", "error": str(e)}
            )
            raise AuthenticationException(
                message="无效的访问令牌",
                details={"error_code": "TOKEN_INVALID", "debug_info": str(e)}
            )
        except jwt.ExpiredSignatureError as e:
            detailed_logger.log_authentication_debug(
                token=auth_token,
                auth_result="失败 - 令牌过期",
                error_details={"reason": "TOKEN_EXPIRED", "error": str(e)}
            )
            raise AuthenticationException(
                message="登录已过期，请重新登录",
                details={"error_code": "TOKEN_EXPIRED", "debug_info": str(e)}
            )
        except AuthenticationException:
            # 重新抛出自定义认证异常
            raise
        except Exception as e:
            # 记录详细的系统错误信息
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
                "token_provided": auth_token is not None,
                "token_length": len(auth_token) if auth_token else 0
            }
            
            detailed_logger.log_authentication_debug(
                token=auth_token,
                auth_result="失败 - 系统错误",
                error_details=error_details
            )
            
            # 在开发环境提供更详细的错误信息
            if settings.DEBUG:
                raise APIException(
                    message=f"认证错误[{type(e).__name__}]: {str(e)}",
                    code=500,
                    error_code="AUTHENTICATION_SYSTEM_ERROR",
                    details=error_details
                )
            else:
                raise APIException(
                    message="认证失败，请重新登录",
                    code=500,
                    error_code="AUTHENTICATION_SYSTEM_ERROR"
                )


class PermissionControl:
    @classmethod
    async def has_permission(cls, request: Request, current_user: User = Depends(AuthControl.is_authed)) -> None:
        """
        增强的权限验证中间件，支持缓存机制和详细调试信息
        """
        permission_start_time = datetime.now()
        method = request.method
        path = request.url.path
        
        # 超级管理员直接通过
        if current_user.is_superuser:
            detailed_logger.log_business_event(
                event_name="permission_check",
                entity_type="user",
                entity_id=str(current_user.id),
                action="superuser_bypass",
                user_id=current_user.id,
                details={
                    "method": method,
                    "path": path,
                    "result": "允许 - 超级管理员"
                }
            )
            return
        
        try:
            # 尝试从缓存获取用户API权限
            cached_permissions = await permission_cache.get_user_api_permissions(current_user.id)
            
            if cached_permissions is not None:
                # 使用缓存的权限数据
                permission_apis = set(tuple(perm) for perm in cached_permissions)
                detailed_logger.log_performance_metrics(
                    operation_name="permission_cache_hit",
                    duration_ms=0,
                    additional_metrics={
                        "user_id": current_user.id,
                        "cache_hit": True,
                        "permissions_count": len(permission_apis)
                    }
                )
            else:
                # 缓存不存在，从数据库查询
                db_start_time = datetime.now()
                permission_apis = await cls._fetch_user_permissions(current_user)
                db_duration = (datetime.now() - db_start_time).total_seconds() * 1000
                
                # 将权限数据存入缓存
                permission_list = [list(perm) for perm in permission_apis]
                await permission_cache.set_user_api_permissions(current_user.id, permission_list)
                
                detailed_logger.log_performance_metrics(
                    operation_name="permission_db_query",
                    duration_ms=db_duration,
                    additional_metrics={
                        "user_id": current_user.id,
                        "cache_hit": False,
                        "permissions_count": len(permission_apis),
                        "cached": True
                    }
                )
            
            # 检查权限
            has_permission = (method, path) in permission_apis
            
            if not has_permission:
                # 获取用户角色信息用于错误详情
                roles = await cls._get_user_roles(current_user.id)
                
                # 记录权限拒绝事件
                detailed_logger.log_business_event(
                    event_name="permission_denied",
                    entity_type="user",
                    entity_id=str(current_user.id),
                    action="access_denied",
                    user_id=current_user.id,
                    details={
                        "method": method,
                        "path": path,
                        "required_permission": f"{method} {path}",
                        "user_roles": [role.get('name', '') for role in roles],
                        "total_permissions": len(permission_apis)
                    }
                )
                
                raise AuthorizationException(
                    message="权限不足，无法访问该资源",
                    details={
                        "error_code": "INSUFFICIENT_PERMISSIONS",
                        "required_permission": f"{method} {path}",
                        "user_id": current_user.id,
                        "username": current_user.username,
                        "user_roles": [role.get('name', '') for role in roles],
                        "debug_info": {
                            "total_permissions": len(permission_apis),
                            "method": method,
                            "path": path
                        } if settings.DEBUG else None
                    }
                )
            else:
                # 记录成功的权限验证
                detailed_logger.log_business_event(
                    event_name="permission_granted",
                    entity_type="user",
                    entity_id=str(current_user.id),
                    action="access_granted",
                    user_id=current_user.id,
                    details={
                        "method": method,
                        "path": path,
                        "permission_matched": f"{method} {path}"
                    }
                )
            
            # 记录权限检查性能指标
            permission_duration = (datetime.now() - permission_start_time).total_seconds() * 1000
            detailed_logger.log_performance_metrics(
                operation_name="permission_check",
                duration_ms=permission_duration,
                additional_metrics={
                    "user_id": current_user.id,
                    "method": method,
                    "path": path,
                    "result": "granted" if has_permission else "denied",
                    "cache_used": cached_permissions is not None
                }
            )
                
        except AuthorizationException:
            # 重新抛出授权异常
            raise
        except Exception as e:
            # 记录详细的权限检查错误
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc() if settings.DEBUG else None,
                "user_id": current_user.id,
                "method": method,
                "path": path
            }
            
            detailed_logger.log_business_event(
                event_name="permission_check_error",
                entity_type="user",
                entity_id=str(current_user.id),
                action="system_error",
                user_id=current_user.id,
                details=error_details
            )
            
            logger.error(f"权限检查过程中发生错误: {str(e)}")
            
            if settings.DEBUG:
                raise APIException(
                    message=f"权限检查错误[{type(e).__name__}]: {str(e)}",
                    code=500,
                    error_code="PERMISSION_CHECK_ERROR",
                    details=error_details
                )
            else:
                raise APIException(
                    message="权限检查过程中发生错误",
                    code=500,
                    error_code="PERMISSION_CHECK_ERROR"
                )
    
    @classmethod
    async def _fetch_user_permissions(cls, user: User) -> set:
        """
        从数据库获取用户权限
        """
        roles: list[Role] = await user.roles
        if not roles:
            raise AuthorizationException(
                message="用户未分配任何角色",
                details={
                    "error_code": "NO_ROLE_ASSIGNED",
                    "user_id": user.id,
                    "username": user.username
                }
            )
        
        # 获取所有角色的API权限
        apis = []
        for role in roles:
            role_apis = await role.apis
            apis.extend(role_apis)
        
        # 去重并返回权限集合
        permission_apis = set((api.http_method, api.api_path) for api in apis)
        return permission_apis
    
    @classmethod
    async def _get_user_roles(cls, user_id: int) -> list:
        """
        获取用户角色信息（优先从缓存获取）
        """
        # 尝试从缓存获取
        cached_roles = await permission_cache.get_user_roles(user_id)
        if cached_roles is not None:
            return cached_roles
        
        # 从数据库查询
        user = await User.get(id=user_id)
        roles = await user.roles
        role_list = [{"id": role.id, "name": role.role_name, "desc": role.desc} for role in roles]
        
        # 缓存角色信息
        await permission_cache.set_user_roles(user_id, role_list)
        return role_list
    
    @classmethod
    async def check_specific_permission(cls, user_id: int, resource: str, action: str) -> bool:
        """
        检查用户是否具有特定资源的特定操作权限
        用于细粒度权限控制
        """
        try:
            # 检查超级管理员
            user = await User.get(id=user_id)
            if user.is_superuser:
                return True
            
            # 尝试从缓存获取
            cached_result = await permission_cache.get_user_permission(user_id, resource, action)
            if cached_result is not None:
                return cached_result
            
            # 从数据库查询权限
            has_permission = await cls._check_permission_from_db(user_id, resource, action)
            
            # 缓存结果
            await permission_cache.set_user_permission(user_id, resource, action, has_permission)
            
            return has_permission
            
        except Exception as e:
            logger.error(f"检查特定权限失败 user_id={user_id}, resource={resource}, action={action}: {e}")
            return False
    
    @classmethod
    async def _check_permission_from_db(cls, user_id: int, resource: str, action: str) -> bool:
        """
        从数据库检查权限
        这里可以根据实际需求实现更复杂的权限逻辑
        """
        try:
            user = await User.get(id=user_id)
            roles = await user.roles
            
            # 这里可以扩展为更复杂的权限检查逻辑
            # 目前简化为检查用户是否有任何角色
            return len(roles) > 0
            
        except Exception as e:
            logger.error(f"数据库权限检查失败: {e}")
            return False
    
    @classmethod
    async def invalidate_user_cache(cls, user_id: int) -> int:
        """
        清除用户权限缓存
        当用户角色或权限发生变更时调用
        """
        return await permission_cache.invalidate_user_permissions(user_id)
    
    @classmethod
    async def invalidate_role_cache(cls, role_id: int) -> int:
        """
        清除角色相关权限缓存
        当角色权限发生变更时调用
        """
        return await permission_cache.invalidate_role_permissions(role_id)
    
DependAuth = Depends(AuthControl.is_authed)
DependPermission = Depends(PermissionControl.has_permission)
