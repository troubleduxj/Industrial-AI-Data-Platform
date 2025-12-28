#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工业AI数据平台安全服务
提供JWT认证、基于角色的访问控制和安全审计功能

需求映射：
- 需求10.1: JWT令牌认证
- 需求10.2: 基于角色的访问控制
- 需求10.3: 敏感数据访问审计
"""

import jwt
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from fastapi import HTTPException, status, Request
from enum import Enum

from app.models.admin import User, Role
from app.settings.config import settings
from app.core.redis_cache import redis_cache_manager
from app.core.unified_logger import get_logger
from app.services.auth_service import auth_service, TokenBlacklistManager
from app.services.permission_service import permission_service
from app.services.audit_service import audit_service

logger = get_logger(__name__)


class PlatformRole(Enum):
    """平台角色枚举"""
    ADMIN = "admin"  # 系统管理员
    DATA_SCIENTIST = "data_scientist"  # 数据科学家
    MLOPS_ENGINEER = "mlops_engineer"  # MLOps工程师
    OPERATOR = "operator"  # 运营人员
    VIEWER = "viewer"  # 只读用户


class ResourceType(Enum):
    """资源类型枚举"""
    ASSET_CATEGORY = "asset_category"
    ASSET = "asset"
    AI_MODEL = "ai_model"
    FEATURE_VIEW = "feature_view"
    PREDICTION = "prediction"
    SIGNAL_DEFINITION = "signal_definition"


class ActionType(Enum):
    """操作类型枚举"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    DEPLOY = "deploy"
    ACTIVATE = "activate"
    PREDICT = "predict"


# 角色权限矩阵
ROLE_PERMISSIONS = {
    PlatformRole.ADMIN: {
        ResourceType.ASSET_CATEGORY: [ActionType.CREATE, ActionType.READ, ActionType.UPDATE, ActionType.DELETE],
        ResourceType.ASSET: [ActionType.CREATE, ActionType.READ, ActionType.UPDATE, ActionType.DELETE],
        ResourceType.AI_MODEL: [ActionType.CREATE, ActionType.READ, ActionType.UPDATE, ActionType.DELETE, ActionType.DEPLOY, ActionType.ACTIVATE],
        ResourceType.FEATURE_VIEW: [ActionType.CREATE, ActionType.READ, ActionType.UPDATE, ActionType.DELETE],
        ResourceType.PREDICTION: [ActionType.CREATE, ActionType.READ, ActionType.PREDICT],
        ResourceType.SIGNAL_DEFINITION: [ActionType.CREATE, ActionType.READ, ActionType.UPDATE, ActionType.DELETE],
    },
    PlatformRole.DATA_SCIENTIST: {
        ResourceType.ASSET_CATEGORY: [ActionType.READ],
        ResourceType.ASSET: [ActionType.READ],
        ResourceType.AI_MODEL: [ActionType.CREATE, ActionType.READ, ActionType.UPDATE, ActionType.DEPLOY, ActionType.ACTIVATE],
        ResourceType.FEATURE_VIEW: [ActionType.CREATE, ActionType.READ, ActionType.UPDATE],
        ResourceType.PREDICTION: [ActionType.CREATE, ActionType.READ, ActionType.PREDICT],
        ResourceType.SIGNAL_DEFINITION: [ActionType.READ],
    },
    PlatformRole.MLOPS_ENGINEER: {
        ResourceType.ASSET_CATEGORY: [ActionType.READ],
        ResourceType.ASSET: [ActionType.READ],
        ResourceType.AI_MODEL: [ActionType.READ, ActionType.DEPLOY, ActionType.ACTIVATE],
        ResourceType.FEATURE_VIEW: [ActionType.READ],
        ResourceType.PREDICTION: [ActionType.READ],
        ResourceType.SIGNAL_DEFINITION: [ActionType.READ],
    },
    PlatformRole.OPERATOR: {
        ResourceType.ASSET_CATEGORY: [ActionType.READ],
        ResourceType.ASSET: [ActionType.CREATE, ActionType.READ, ActionType.UPDATE],
        ResourceType.AI_MODEL: [ActionType.READ],
        ResourceType.FEATURE_VIEW: [ActionType.READ],
        ResourceType.PREDICTION: [ActionType.READ, ActionType.PREDICT],
        ResourceType.SIGNAL_DEFINITION: [ActionType.READ],
    },
    PlatformRole.VIEWER: {
        ResourceType.ASSET_CATEGORY: [ActionType.READ],
        ResourceType.ASSET: [ActionType.READ],
        ResourceType.AI_MODEL: [ActionType.READ],
        ResourceType.FEATURE_VIEW: [ActionType.READ],
        ResourceType.PREDICTION: [ActionType.READ],
        ResourceType.SIGNAL_DEFINITION: [ActionType.READ],
    },
}


class PlatformSecurityService:
    """平台安全服务"""
    
    def __init__(self):
        self.auth_service = auth_service
        self.permission_service = permission_service
        self.audit_service = audit_service
        self.blacklist_manager = TokenBlacklistManager()
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = 7
        
        # 敏感操作列表
        self.sensitive_operations = [
            (ResourceType.AI_MODEL, ActionType.DELETE),
            (ResourceType.AI_MODEL, ActionType.DEPLOY),
            (ResourceType.AI_MODEL, ActionType.ACTIVATE),
            (ResourceType.ASSET_CATEGORY, ActionType.DELETE),
            (ResourceType.FEATURE_VIEW, ActionType.DELETE),
        ]
    
    async def authenticate_user(
        self,
        username: str,
        password: str,
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """
        用户认证
        
        Args:
            username: 用户名
            password: 密码
            request: 请求对象
            
        Returns:
            Dict: 包含令牌和用户信息的字典
            
        Raises:
            HTTPException: 认证失败时抛出
        """
        from app.schemas.login import CredentialsSchema
        import time
        
        start_time = time.time()
        
        try:
            credentials = CredentialsSchema(username=username, password=password)
            user = await self.auth_service.authenticate(credentials)
            
            # 生成令牌
            tokens = await self.auth_service.generate_tokens(user)
            
            # 更新最后登录时间
            await self.auth_service.update_last_login(user)
            
            # 获取用户角色
            user_roles = await self._get_user_platform_roles(user)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # 记录认证日志
            if request:
                await self.audit_service.log_authentication(
                    user_id=user.id,
                    username=user.username,
                    action_type="LOGIN",
                    success=True,
                    request=request,
                    extra_data={"roles": [r.value for r in user_roles]},
                    duration_ms=duration_ms
                )
            
            logger.info(f"用户认证成功: {username}")
            
            return {
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "token_type": "bearer",
                "expires_in": tokens["expires_in"],
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "is_superuser": user.is_superuser,
                    "roles": [r.value for r in user_roles]
                }
            }
            
        except HTTPException:
            # 记录失败的认证尝试
            if request:
                await self.audit_service.log_authentication(
                    user_id=None,
                    username=username,
                    action_type="LOGIN",
                    success=False,
                    request=request,
                    extra_data={"reason": "认证失败"}
                )
            raise
        except Exception as e:
            logger.error(f"用户认证失败: {e}")
            if request:
                await self.audit_service.log_authentication(
                    user_id=None,
                    username=username,
                    action_type="LOGIN",
                    success=False,
                    request=request,
                    extra_data={"reason": str(e)}
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="认证服务暂时不可用"
            )
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            Dict: 令牌载荷，验证失败返回None
        """
        return await self.auth_service.verify_token(token)
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        刷新访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            Dict: 新的令牌信息
        """
        return await self.auth_service.refresh_token(refresh_token)
    
    async def logout(
        self,
        token: str,
        user_id: int,
        request: Optional[Request] = None
    ) -> bool:
        """
        用户登出
        
        Args:
            token: 访问令牌
            user_id: 用户ID
            request: 请求对象
            
        Returns:
            bool: 登出是否成功
        """
        result = await self.auth_service.logout(token, user_id)
        
        if request:
            user = await User.get_or_none(id=user_id)
            await self.audit_service.log_authentication(
                user_id=user_id,
                username=user.username if user else "unknown",
                action_type="LOGOUT",
                success=result,
                request=request
            )
        
        return result
    
    async def check_permission(
        self,
        user_id: int,
        resource_type: ResourceType,
        action: ActionType,
        resource_id: Optional[str] = None,
        request: Optional[Request] = None
    ) -> Tuple[bool, str]:
        """
        检查用户权限
        
        Args:
            user_id: 用户ID
            resource_type: 资源类型
            action: 操作类型
            resource_id: 资源ID
            request: 请求对象
            
        Returns:
            Tuple[bool, str]: (是否有权限, 原因)
        """
        try:
            # 获取用户
            user = await User.get_or_none(id=user_id)
            if not user:
                return False, "用户不存在"
            
            if not user.is_active:
                return False, "用户账户已被禁用"
            
            # 超级用户拥有所有权限
            if user.is_superuser:
                # 记录敏感操作
                if self._is_sensitive_operation(resource_type, action):
                    await self._log_sensitive_access(
                        user, resource_type, action, resource_id, True, request
                    )
                return True, "超级用户权限"
            
            # 获取用户平台角色
            user_roles = await self._get_user_platform_roles(user)
            
            # 检查角色权限
            has_permission = False
            for role in user_roles:
                if role in ROLE_PERMISSIONS:
                    role_perms = ROLE_PERMISSIONS[role]
                    if resource_type in role_perms:
                        if action in role_perms[resource_type]:
                            has_permission = True
                            break
            
            # 记录敏感操作
            if self._is_sensitive_operation(resource_type, action):
                await self._log_sensitive_access(
                    user, resource_type, action, resource_id, has_permission, request
                )
            
            if has_permission:
                return True, f"角色权限: {[r.value for r in user_roles]}"
            else:
                return False, f"缺少权限: {resource_type.value}:{action.value}"
                
        except Exception as e:
            logger.error(f"权限检查失败: user_id={user_id}, error={e}")
            return False, f"权限检查失败: {str(e)}"
    
    async def _get_user_platform_roles(self, user: User) -> List[PlatformRole]:
        """获取用户的平台角色"""
        roles = []
        
        # 超级用户自动获得管理员角色
        if user.is_superuser:
            roles.append(PlatformRole.ADMIN)
            return roles
        
        # 从数据库角色映射到平台角色
        try:
            db_roles = await user.roles.filter(status='0', del_flag='0').all()
            
            for db_role in db_roles:
                role_key = db_role.role_key.lower() if db_role.role_key else ""
                
                if "admin" in role_key:
                    roles.append(PlatformRole.ADMIN)
                elif "data_scientist" in role_key or "scientist" in role_key:
                    roles.append(PlatformRole.DATA_SCIENTIST)
                elif "mlops" in role_key or "engineer" in role_key:
                    roles.append(PlatformRole.MLOPS_ENGINEER)
                elif "operator" in role_key or "ops" in role_key:
                    roles.append(PlatformRole.OPERATOR)
                else:
                    roles.append(PlatformRole.VIEWER)
            
            # 如果没有匹配的角色，默认为查看者
            if not roles:
                roles.append(PlatformRole.VIEWER)
                
        except Exception as e:
            logger.error(f"获取用户角色失败: {e}")
            roles.append(PlatformRole.VIEWER)
        
        return list(set(roles))  # 去重
    
    def _is_sensitive_operation(self, resource_type: ResourceType, action: ActionType) -> bool:
        """检查是否为敏感操作"""
        return (resource_type, action) in self.sensitive_operations
    
    async def _log_sensitive_access(
        self,
        user: User,
        resource_type: ResourceType,
        action: ActionType,
        resource_id: Optional[str],
        granted: bool,
        request: Optional[Request]
    ):
        """记录敏感数据访问"""
        try:
            from app.models.audit_log import AuditLog
            
            risk_level = "HIGH" if not granted else "MEDIUM"
            
            await AuditLog.create(
                user_id=user.id,
                username=user.username,
                user_ip=self._get_client_ip(request) if request else "unknown",
                user_agent=request.headers.get("user-agent", "") if request else "",
                action_type="SENSITIVE_OPERATION",
                action_name=f"{action.value} {resource_type.value}",
                resource_type=resource_type.value,
                resource_id=resource_id,
                permission_result=granted,
                request_method=request.method if request else "UNKNOWN",
                request_path=str(request.url.path) if request else "",
                response_status=200 if granted else 403,
                response_message="已授权" if granted else "权限拒绝",
                risk_level=risk_level,
                extra_data={
                    "operation": f"{resource_type.value}:{action.value}",
                    "is_sensitive": True
                }
            )
            
            logger.info(
                f"敏感操作记录: user={user.username}, "
                f"operation={resource_type.value}:{action.value}, "
                f"granted={granted}"
            )
            
        except Exception as e:
            logger.error(f"记录敏感操作失败: {e}")
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        if not request:
            return "unknown"
        
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def get_user_permissions(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户的所有权限
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 用户权限信息
        """
        try:
            user = await User.get_or_none(id=user_id)
            if not user:
                return {"error": "用户不存在"}
            
            user_roles = await self._get_user_platform_roles(user)
            
            # 汇总所有角色的权限
            permissions = {}
            for role in user_roles:
                if role in ROLE_PERMISSIONS:
                    for resource, actions in ROLE_PERMISSIONS[role].items():
                        if resource.value not in permissions:
                            permissions[resource.value] = []
                        permissions[resource.value].extend([a.value for a in actions])
            
            # 去重
            for resource in permissions:
                permissions[resource] = list(set(permissions[resource]))
            
            return {
                "user_id": user_id,
                "username": user.username,
                "is_superuser": user.is_superuser,
                "roles": [r.value for r in user_roles],
                "permissions": permissions
            }
            
        except Exception as e:
            logger.error(f"获取用户权限失败: {e}")
            return {"error": str(e)}


# 全局平台安全服务实例
platform_security_service = PlatformSecurityService()
