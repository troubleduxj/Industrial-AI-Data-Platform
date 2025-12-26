"""
批量删除权限中间件

实现批量删除操作的权限控制中间件，包括：
- 请求拦截和权限验证
- 与现有中间件系统的集成
- 权限缓存和性能优化

需求映射：
- 需求6.2: 后端权限验证
- 需求6.3: 细粒度权限检查
- 需求6.5: 权限一致性
"""

import logging
from typing import Dict, Optional, Tuple
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.models.admin import User
from app.core.dependency import AuthControl
from app.core.permissions import batch_delete_permission_checker, PermissionCondition
from app.core.response_formatter_v2 import ResponseFormatterV2, APIv2ErrorDetail

logger = logging.getLogger(__name__)


class BatchDeletePermissionMiddleware(BaseHTTPMiddleware):
    """批量删除权限中间件"""
    
    def __init__(self, app, **kwargs):
        super().__init__(app)
        self.permission_checker = batch_delete_permission_checker
        
        # 定义需要权限检查的路径和对应的资源类型
        self.protected_paths = {
            "/api/v2/apis/batch": {
                "resource_type": "api",
                "action": "batch_delete",
                "conditions": [PermissionCondition.EXCLUDE_SYSTEM_ITEMS]
            },
            "/api/v2/dict-types/batch": {
                "resource_type": "dict_type",
                "action": "batch_delete",
                "conditions": [PermissionCondition.EXCLUDE_SYSTEM_ITEMS]
            },
            "/api/v2/dict-data/batch": {
                "resource_type": "dict_data",
                "action": "batch_delete",
                "conditions": [PermissionCondition.EXCLUDE_SYSTEM_ITEMS]
            },
            "/api/v2/system-params/batch": {
                "resource_type": "system_param",
                "action": "batch_delete",
                "conditions": [PermissionCondition.EXCLUDE_SYSTEM_ITEMS]
            },
            "/api/v2/departments/batch": {
                "resource_type": "dept",
                "action": "batch_delete",
                "conditions": [
                    PermissionCondition.EXCLUDE_SYSTEM_ITEMS,
                    PermissionCondition.EXCLUDE_REFERENCED_ITEMS
                ]
            },
            "/api/v2/users/batch": {
                "resource_type": "user",
                "action": "batch_delete",
                "conditions": [
                    PermissionCondition.EXCLUDE_SYSTEM_ITEMS,
                    PermissionCondition.EXCLUDE_REFERENCED_ITEMS
                ]
            },
            "/api/v2/roles/batch": {
                "resource_type": "role",
                "action": "batch_delete",
                "conditions": [
                    PermissionCondition.EXCLUDE_SYSTEM_ITEMS,
                    PermissionCondition.EXCLUDE_REFERENCED_ITEMS
                ]
            },
            "/api/v2/menus/batch": {
                "resource_type": "menu",
                "action": "batch_delete",
                "conditions": [
                    PermissionCondition.EXCLUDE_SYSTEM_ITEMS,
                    PermissionCondition.EXCLUDE_REFERENCED_ITEMS
                ]
            }
        }
        
        # 启用权限检查的开关
        self.enable_permission_check = kwargs.get('enable_permission_check', True)
        
        # 白名单路径（不需要权限检查）
        self.whitelist_paths = kwargs.get('whitelist_paths', [
            "/api/v1/",  # V1 API不检查
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health"
        ])
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """处理请求并进行权限检查"""
        
        # 如果权限检查被禁用，直接通过
        if not self.enable_permission_check:
            return await call_next(request)
        
        # 检查是否为需要权限验证的批量删除请求
        if await self._should_check_permission(request):
            permission_result = await self._check_batch_delete_permission(request)
            if permission_result:
                return permission_result
        
        # 执行实际请求
        response = await call_next(request)
        
        # 记录权限检查结果（如果需要）
        await self._log_permission_check(request, response)
        
        return response
    
    async def _should_check_permission(self, request: Request) -> bool:
        """判断是否需要进行权限检查"""
        path = request.url.path
        method = request.method
        
        # 只检查DELETE方法
        if method != "DELETE":
            return False
        
        # 检查白名单
        for whitelist_path in self.whitelist_paths:
            if path.startswith(whitelist_path):
                return False
        
        # 检查是否为受保护的批量删除路径
        return path in self.protected_paths
    
    async def _check_batch_delete_permission(self, request: Request) -> Optional[Response]:
        """检查批量删除权限"""
        try:
            # 获取当前用户
            current_user = await self._get_current_user(request)
            if not current_user:
                return self._create_auth_error_response(request, "用户未认证")
            
            # 获取路径配置
            path = request.url.path
            path_config = self.protected_paths.get(path)
            if not path_config:
                return None
            
            # 检查权限
            has_permission, reason = await self.permission_checker.check_batch_delete_permission(
                current_user,
                path_config["resource_type"],
                path_config["action"],
                path_config.get("conditions")
            )
            
            if not has_permission:
                return self._create_permission_error_response(
                    request, 
                    path_config["resource_type"], 
                    reason
                )
            
            # 权限检查通过
            return None
            
        except Exception as e:
            logger.error(f"批量删除权限检查失败: {str(e)}")
            return self._create_system_error_response(request, str(e))
    
    async def _get_current_user(self, request: Request) -> Optional[User]:
        """获取当前用户"""
        try:
            # 从请求头获取token
            token = request.headers.get("token") or request.headers.get("authorization")
            if not token:
                return None
            
            # 如果是Bearer格式，提取token
            if token.startswith("Bearer "):
                token = token[7:]
            
            # 使用现有的认证控制器验证用户
            user = await AuthControl.is_authed(token)
            return user
            
        except Exception as e:
            logger.error(f"获取当前用户失败: {str(e)}")
            return None
    
    def _create_auth_error_response(self, request: Request, message: str) -> Response:
        """创建认证错误响应"""
        formatter = ResponseFormatterV2(request)
        response_data = formatter.unauthorized(
            message=message,
            error_code="AUTHENTICATION_REQUIRED"
        )
        
        return JSONResponse(
            status_code=401,
            content=response_data
        )
    
    def _create_permission_error_response(
        self, 
        request: Request, 
        resource_type: str, 
        reason: Optional[str]
    ) -> Response:
        """创建权限错误响应"""
        formatter = ResponseFormatterV2(request)
        
        response_data = formatter.forbidden(
            message=f"批量删除{resource_type}权限不足",
            details=[APIv2ErrorDetail(
                field="permission",
                code="BATCH_DELETE_PERMISSION_DENIED",
                message=reason or "权限不足",
                value=f"{resource_type}:batch_delete"
            )],
            suggestion="请联系管理员分配相应的批量删除权限"
        )
        
        return JSONResponse(
            status_code=403,
            content=response_data
        )
    
    def _create_system_error_response(self, request: Request, error_detail: str) -> Response:
        """创建系统错误响应"""
        formatter = ResponseFormatterV2(request)
        
        response_data = formatter.internal_error(
            message="权限检查过程中发生系统错误",
            error_detail=error_detail,
            component="batch_delete_permission_middleware"
        )
        
        return JSONResponse(
            status_code=500,
            content=response_data
        )
    
    async def _log_permission_check(self, request: Request, response: Response):
        """记录权限检查日志"""
        try:
            path = request.url.path
            method = request.method
            status_code = response.status_code
            
            # 只记录权限相关的请求
            if path in self.protected_paths and method == "DELETE":
                logger.info(
                    f"批量删除权限检查 - "
                    f"路径: {path}, "
                    f"方法: {method}, "
                    f"状态码: {status_code}, "
                    f"时间: {datetime.now().isoformat()}"
                )
                
        except Exception as e:
            logger.error(f"记录权限检查日志失败: {str(e)}")


class BatchDeletePermissionValidator:
    """批量删除权限验证器（用于手动验证）"""
    
    def __init__(self):
        self.permission_checker = batch_delete_permission_checker
    
    async def validate_request_permission(
        self,
        request: Request,
        current_user: User,
        resource_type: str,
        conditions: Optional[list] = None
    ) -> Tuple[bool, Optional[str]]:
        """验证请求权限"""
        try:
            return await self.permission_checker.check_batch_delete_permission(
                current_user, resource_type, "batch_delete", conditions
            )
        except Exception as e:
            logger.error(f"权限验证失败: {str(e)}")
            return False, f"权限验证失败: {str(e)}"
    
    async def validate_items_permission(
        self,
        current_user: User,
        items: list,
        resource_type: str,
        conditions: Optional[list] = None
    ) -> Dict[str, any]:
        """验证项目权限"""
        try:
            allowed_items = []
            denied_items = []
            
            for item in items:
                has_permission, reason = await self.permission_checker.check_item_delete_permission(
                    current_user, item, resource_type, conditions
                )
                
                if has_permission:
                    allowed_items.append(item)
                else:
                    denied_items.append({
                        "item": item,
                        "reason": reason
                    })
            
            return {
                "allowed_items": allowed_items,
                "denied_items": denied_items,
                "allowed_count": len(allowed_items),
                "denied_count": len(denied_items)
            }
            
        except Exception as e:
            logger.error(f"项目权限验证失败: {str(e)}")
            return {
                "allowed_items": [],
                "denied_items": [{"item": item, "reason": f"验证失败: {str(e)}"} for item in items],
                "allowed_count": 0,
                "denied_count": len(items)
            }


# 全局权限验证器实例
batch_delete_permission_validator = BatchDeletePermissionValidator()


def create_batch_delete_permission_middleware(app, **kwargs):
    """创建批量删除权限中间件实例"""
    return BatchDeletePermissionMiddleware(app, **kwargs)


# 权限检查工具函数

async def check_batch_delete_request_permission(
    request: Request,
    current_user: User,
    resource_type: str,
    conditions: Optional[list] = None
) -> Tuple[bool, Optional[str]]:
    """检查批量删除请求权限的便捷函数"""
    return await batch_delete_permission_validator.validate_request_permission(
        request, current_user, resource_type, conditions
    )


async def filter_items_by_permission(
    current_user: User,
    items: list,
    resource_type: str,
    conditions: Optional[list] = None
) -> Dict[str, any]:
    """根据权限过滤项目的便捷函数"""
    return await batch_delete_permission_validator.validate_items_permission(
        current_user, items, resource_type, conditions
    )