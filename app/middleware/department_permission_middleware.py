"""
部门权限中间件
实现部门数据权限范围控制和跨部门访问权限验证
"""

import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

from app.services.department_permission_service import department_permission_service
from app.core.auth_dependencies import get_current_user
from app.models.admin import User

logger = logging.getLogger(__name__)


class DepartmentPermissionMiddleware:
    """部门权限中间件"""
    
    def __init__(self):
        self.department_service = department_permission_service
    
    async def check_department_access(
        self, 
        request: Request, 
        target_department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        检查部门访问权限
        
        Args:
            request: FastAPI请求对象
            target_department_id: 目标部门ID
            
        Returns:
            Dict: 权限检查结果
        """
        try:
            # 获取当前用户
            user = await self._get_current_user_from_request(request)
            if not user:
                return {
                    "allowed": False,
                    "reason": "authentication_required",
                    "message": "需要用户认证"
                }
            
            # 超级用户拥有所有权限
            if user.is_superuser:
                return {
                    "allowed": True,
                    "reason": "super_user",
                    "message": "超级用户拥有所有权限"
                }
            
            # 如果没有指定目标部门，从请求中提取
            if target_department_id is None:
                target_department_id = await self._extract_department_from_request(request)
            
            # 如果仍然没有部门ID，允许访问（可能是全局数据）
            if target_department_id is None:
                return {
                    "allowed": True,
                    "reason": "no_department_restriction",
                    "message": "无部门限制的数据访问"
                }
            
            # 检查部门访问权限
            has_access = await self.department_service.check_department_access_permission(
                user.id, target_department_id
            )
            
            if has_access:
                return {
                    "allowed": True,
                    "reason": "department_access_granted",
                    "message": f"用户有权限访问部门ID为{target_department_id}的数据"
                }
            else:
                return {
                    "allowed": False,
                    "reason": "department_access_denied",
                    "message": f"用户无权限访问部门ID为{target_department_id}的数据"
                }
                
        except Exception as e:
            logger.error(f"部门访问权限检查失败: error={str(e)}")
            return {
                "allowed": False,
                "reason": "permission_check_error",
                "message": f"权限检查过程中发生错误: {str(e)}"
            }
    
    async def _get_current_user_from_request(self, request: Request) -> Optional[User]:
        """
        从请求中获取当前用户
        
        Args:
            request: FastAPI请求对象
            
        Returns:
            Optional[User]: 用户对象
        """
        try:
            # 尝试从请求状态中获取用户（如果已经通过认证中间件）
            if hasattr(request.state, 'user'):
                return request.state.user
            
            # 如果没有，尝试通过认证依赖获取
            authorization = request.headers.get('Authorization')
            if not authorization:
                return None
            
            # 简化实现，实际应该调用认证服务
            # user = await get_current_user(authorization)
            # return user
            
            return None
            
        except Exception as e:
            logger.error(f"获取当前用户失败: error={str(e)}")
            return None
    
    async def _extract_department_from_request(self, request: Request) -> Optional[int]:
        """
        从请求中提取部门ID
        
        Args:
            request: FastAPI请求对象
            
        Returns:
            Optional[int]: 部门ID
        """
        try:
            # 从查询参数中提取
            department_id = request.query_params.get('department_id')
            if department_id:
                return int(department_id)
            
            # 从路径参数中提取
            path_params = getattr(request, 'path_params', {})
            department_id = path_params.get('department_id')
            if department_id:
                return int(department_id)
            
            # 从请求体中提取（如果是POST/PUT请求）
            if request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    body = await request.json()
                    department_id = body.get('department_id')
                    if department_id:
                        return int(department_id)
                except:
                    pass
            
            return None
            
        except Exception as e:
            logger.error(f"从请求中提取部门ID失败: error={str(e)}")
            return None
    
    async def enforce_department_permission(
        self, 
        request: Request, 
        target_department_id: Optional[int] = None,
        raise_exception: bool = True
    ) -> bool:
        """
        强制执行部门权限检查
        
        Args:
            request: FastAPI请求对象
            target_department_id: 目标部门ID
            raise_exception: 是否在权限不足时抛出异常
            
        Returns:
            bool: 是否有权限
            
        Raises:
            HTTPException: 权限不足时抛出
        """
        result = await self.check_department_access(request, target_department_id)
        
        if not result.get('allowed', False):
            if raise_exception:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "department_access_denied",
                        "message": result.get('message', '部门访问权限不足'),
                        "reason": result.get('reason', 'unknown')
                    }
                )
            return False
        
        return True
    
    async def get_user_accessible_departments(self, request: Request) -> Dict[str, Any]:
        """
        获取用户可访问的部门列表
        
        Args:
            request: FastAPI请求对象
            
        Returns:
            Dict: 包含部门列表的响应
        """
        try:
            user = await self._get_current_user_from_request(request)
            if not user:
                return {
                    "success": False,
                    "message": "需要用户认证",
                    "departments": []
                }
            
            departments = await self.department_service.get_accessible_departments(user.id)
            
            return {
                "success": True,
                "message": "获取可访问部门列表成功",
                "departments": departments,
                "total": len(departments)
            }
            
        except Exception as e:
            logger.error(f"获取用户可访问部门列表失败: error={str(e)}")
            return {
                "success": False,
                "message": f"获取部门列表失败: {str(e)}",
                "departments": []
            }
    
    async def validate_cross_department_access(
        self, 
        request: Request, 
        source_department_id: int, 
        target_department_id: int
    ) -> Dict[str, Any]:
        """
        验证跨部门访问权限
        
        Args:
            request: FastAPI请求对象
            source_department_id: 源部门ID
            target_department_id: 目标部门ID
            
        Returns:
            Dict: 验证结果
        """
        try:
            user = await self._get_current_user_from_request(request)
            if not user:
                return {
                    "allowed": False,
                    "reason": "authentication_required",
                    "message": "需要用户认证"
                }
            
            # 超级用户拥有所有权限
            if user.is_superuser:
                return {
                    "allowed": True,
                    "reason": "super_user",
                    "message": "超级用户拥有跨部门访问权限"
                }
            
            # 检查用户是否有权限访问源部门和目标部门
            source_access = await self.department_service.check_department_access_permission(
                user.id, source_department_id
            )
            target_access = await self.department_service.check_department_access_permission(
                user.id, target_department_id
            )
            
            if not source_access:
                return {
                    "allowed": False,
                    "reason": "source_department_access_denied",
                    "message": f"用户无权限访问源部门ID为{source_department_id}的数据"
                }
            
            if not target_access:
                return {
                    "allowed": False,
                    "reason": "target_department_access_denied",
                    "message": f"用户无权限访问目标部门ID为{target_department_id}的数据"
                }
            
            # 检查是否有跨部门访问权限
            scope_info = await self.department_service.get_user_department_scope(user.id)
            if not scope_info.get('can_cross_department', False):
                return {
                    "allowed": False,
                    "reason": "cross_department_permission_denied",
                    "message": "用户没有跨部门访问权限"
                }
            
            return {
                "allowed": True,
                "reason": "cross_department_access_granted",
                "message": "跨部门访问权限验证通过"
            }
            
        except Exception as e:
            logger.error(f"跨部门访问权限验证失败: error={str(e)}")
            return {
                "allowed": False,
                "reason": "validation_error",
                "message": f"权限验证过程中发生错误: {str(e)}"
            }


# 创建全局实例
department_permission_middleware = DepartmentPermissionMiddleware()


# 装饰器函数
def require_department_permission(department_id: Optional[int] = None):
    """
    部门权限装饰器
    
    Args:
        department_id: 部门ID，如果为None则从请求中提取
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # 检查部门权限
            await department_permission_middleware.enforce_department_permission(
                request, department_id
            )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_cross_department_permission():
    """
    跨部门权限装饰器
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # 从请求中提取源部门和目标部门ID
            source_dept = request.query_params.get('source_department_id')
            target_dept = request.query_params.get('target_department_id')
            
            if source_dept and target_dept:
                result = await department_permission_middleware.validate_cross_department_access(
                    request, int(source_dept), int(target_dept)
                )
                if not result.get('allowed', False):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={
                            "error": "cross_department_access_denied",
                            "message": result.get('message', '跨部门访问权限不足'),
                            "reason": result.get('reason', 'unknown')
                        }
                    )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator