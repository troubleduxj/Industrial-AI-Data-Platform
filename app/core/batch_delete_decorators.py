"""
批量删除权限装饰器

提供便捷的权限装饰器和依赖注入函数，包括：
- 函数装饰器
- FastAPI依赖注入
- 权限检查工具

需求映射：
- 需求6.2: 后端权限验证
- 需求6.3: 细粒度权限检查
- 需求6.5: 权限一致性
"""

from typing import List, Optional, Callable, Any
from functools import wraps
import logging

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models.admin import User
from app.core.dependency import AuthControl
from app.core.permissions import (
    batch_delete_permission_checker, 
    PermissionCondition,
    BatchDeletePermission
)
from app.core.response_formatter_v2 import ResponseFormatterV2, APIv2ErrorDetail

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


def require_batch_delete_permission(
    resource_type: str,
    conditions: Optional[List[PermissionCondition]] = None,
    error_message: Optional[str] = None
):
    """
    批量删除权限装饰器
    
    Args:
        resource_type: 资源类型 (api, dict_type, dict_data等)
        conditions: 权限条件列表
        error_message: 自定义错误消息
    
    Usage:
        @require_batch_delete_permission("api", [PermissionCondition.EXCLUDE_SYSTEM_ITEMS])
        async def batch_delete_apis(request: Request, current_user: User = DependAuth):
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中提取request和current_user
            request = None
            current_user = None
            
            # 检查位置参数
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                elif isinstance(arg, User):
                    current_user = arg
            
            # 检查关键字参数
            if not request:
                request = kwargs.get('request')
            if not current_user:
                current_user = kwargs.get('current_user')
            
            # 验证必要参数
            if not current_user:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "message": "用户未认证",
                        "error_code": "AUTHENTICATION_REQUIRED"
                    }
                )
            
            # 检查权限
            has_permission, reason = await batch_delete_permission_checker.check_batch_delete_permission(
                current_user, resource_type, "batch_delete", conditions
            )
            
            if not has_permission:
                error_msg = error_message or f"批量删除{resource_type}权限不足"
                
                # 如果有request对象，使用ResponseFormatterV2格式化错误
                if request:
                    formatter = ResponseFormatterV2(request)
                    error_response = formatter.forbidden(
                        message=error_msg,
                        details=[APIv2ErrorDetail(
                            field="permission",
                            code="BATCH_DELETE_PERMISSION_DENIED",
                            message=reason or "权限不足",
                            value=f"{resource_type}:batch_delete"
                        )],
                        suggestion="请联系管理员分配相应的批量删除权限"
                    )
                    raise HTTPException(status_code=403, detail=error_response)
                else:
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "message": error_msg,
                            "reason": reason,
                            "error_code": "BATCH_DELETE_PERMISSION_DENIED"
                        }
                    )
            
            # 权限检查通过，执行原函数
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_specific_permission(permission: BatchDeletePermission):
    """
    特定权限装饰器
    
    Args:
        permission: 批量删除权限枚举值
    
    Usage:
        @require_specific_permission(BatchDeletePermission.API_BATCH_DELETE)
        async def batch_delete_apis(request: Request, current_user: User = DependAuth):
            pass
    """
    # 解析权限字符串
    resource_type, action = permission.value.split(":")
    
    return require_batch_delete_permission(
        resource_type=resource_type,
        conditions=None,
        error_message=f"缺少权限: {permission.value}"
    )


class BatchDeletePermissionDependency:
    """批量删除权限依赖类"""
    
    def __init__(
        self,
        resource_type: str,
        conditions: Optional[List[PermissionCondition]] = None,
        error_message: Optional[str] = None
    ):
        self.resource_type = resource_type
        self.conditions = conditions
        self.error_message = error_message
    
    async def __call__(
        self,
        request: Request,
        current_user: User = Depends(AuthControl.is_authed)
    ) -> User:
        """依赖注入函数"""
        # 检查权限
        has_permission, reason = await batch_delete_permission_checker.check_batch_delete_permission(
            current_user, self.resource_type, "batch_delete", self.conditions
        )
        
        if not has_permission:
            error_msg = self.error_message or f"批量删除{self.resource_type}权限不足"
            
            formatter = ResponseFormatterV2(request)
            error_response = formatter.forbidden(
                message=error_msg,
                details=[APIv2ErrorDetail(
                    field="permission",
                    code="BATCH_DELETE_PERMISSION_DENIED",
                    message=reason or "权限不足",
                    value=f"{self.resource_type}:batch_delete"
                )],
                suggestion="请联系管理员分配相应的批量删除权限"
            )
            raise HTTPException(status_code=403, detail=error_response)
        
        return current_user


# 预定义的权限依赖

def BatchDeleteAPIDependency():
    """API批量删除权限依赖"""
    return BatchDeletePermissionDependency(
        resource_type="api",
        conditions=[PermissionCondition.EXCLUDE_SYSTEM_ITEMS]
    )


def BatchDeleteDictTypeDependency():
    """字典类型批量删除权限依赖"""
    return BatchDeletePermissionDependency(
        resource_type="dict_type",
        conditions=[PermissionCondition.EXCLUDE_SYSTEM_ITEMS]
    )


def BatchDeleteDictDataDependency():
    """字典数据批量删除权限依赖"""
    return BatchDeletePermissionDependency(
        resource_type="dict_data",
        conditions=[PermissionCondition.EXCLUDE_SYSTEM_ITEMS]
    )


def BatchDeleteSystemParamDependency():
    """系统参数批量删除权限依赖"""
    return BatchDeletePermissionDependency(
        resource_type="system_param",
        conditions=[PermissionCondition.EXCLUDE_SYSTEM_ITEMS]
    )


def BatchDeleteDeptDependency():
    """部门批量删除权限依赖"""
    return BatchDeletePermissionDependency(
        resource_type="dept",
        conditions=[
            PermissionCondition.EXCLUDE_SYSTEM_ITEMS,
            PermissionCondition.EXCLUDE_REFERENCED_ITEMS
        ]
    )


def BatchDeleteUserDependency():
    """用户批量删除权限依赖"""
    return BatchDeletePermissionDependency(
        resource_type="user",
        conditions=[
            PermissionCondition.EXCLUDE_SYSTEM_ITEMS,
            PermissionCondition.EXCLUDE_REFERENCED_ITEMS
        ]
    )


def BatchDeleteRoleDependency():
    """角色批量删除权限依赖"""
    return BatchDeletePermissionDependency(
        resource_type="role",
        conditions=[
            PermissionCondition.EXCLUDE_SYSTEM_ITEMS,
            PermissionCondition.EXCLUDE_REFERENCED_ITEMS
        ]
    )


def BatchDeleteMenuDependency():
    """菜单批量删除权限依赖"""
    return BatchDeletePermissionDependency(
        resource_type="menu",
        conditions=[
            PermissionCondition.EXCLUDE_SYSTEM_ITEMS,
            PermissionCondition.EXCLUDE_REFERENCED_ITEMS
        ]
    )


# 便捷的依赖注入函数

def DependBatchDeleteAPI():
    """API批量删除权限依赖注入"""
    return Depends(BatchDeleteAPIDependency())


def DependBatchDeleteDictType():
    """字典类型批量删除权限依赖注入"""
    return Depends(BatchDeleteDictTypeDependency())


def DependBatchDeleteDictData():
    """字典数据批量删除权限依赖注入"""
    return Depends(BatchDeleteDictDataDependency())


def DependBatchDeleteSystemParam():
    """系统参数批量删除权限依赖注入"""
    return Depends(BatchDeleteSystemParamDependency())


def DependBatchDeleteDept():
    """部门批量删除权限依赖注入"""
    return Depends(BatchDeleteDeptDependency())


def DependBatchDeleteUser():
    """用户批量删除权限依赖注入"""
    return Depends(BatchDeleteUserDependency())


def DependBatchDeleteRole():
    """角色批量删除权限依赖注入"""
    return Depends(BatchDeleteRoleDependency())


def DependBatchDeleteMenu():
    """菜单批量删除权限依赖注入"""
    return Depends(BatchDeleteMenuDependency())


# 权限检查工具函数

async def check_user_batch_delete_permission(
    user: User,
    resource_type: str,
    conditions: Optional[List[PermissionCondition]] = None
) -> tuple[bool, Optional[str]]:
    """
    检查用户批量删除权限的工具函数
    
    Args:
        user: 用户对象
        resource_type: 资源类型
        conditions: 权限条件列表
        
    Returns:
        tuple: (是否有权限, 权限不足的原因)
    """
    return await batch_delete_permission_checker.check_batch_delete_permission(
        user, resource_type, "batch_delete", conditions
    )


async def validate_batch_delete_items(
    user: User,
    items: List[Any],
    resource_type: str,
    conditions: Optional[List[PermissionCondition]] = None
) -> dict:
    """
    验证批量删除项目权限的工具函数
    
    Args:
        user: 用户对象
        items: 要删除的项目列表
        resource_type: 资源类型
        conditions: 权限条件列表
        
    Returns:
        dict: 验证结果，包含允许和拒绝的项目
    """
    allowed_items = []
    denied_items = []
    
    for item in items:
        has_permission, reason = await batch_delete_permission_checker.check_item_delete_permission(
            user, item, resource_type, conditions
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


class PermissionError(Exception):
    """权限错误异常"""
    
    def __init__(self, message: str, error_code: str = "PERMISSION_DENIED", details: Optional[dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


def handle_permission_error(func: Callable):
    """权限错误处理装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except PermissionError as e:
            # 从参数中获取request对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get('request')
            
            if request:
                formatter = ResponseFormatterV2(request)
                error_response = formatter.forbidden(
                    message=e.message,
                    details=[APIv2ErrorDetail(
                        field="permission",
                        code=e.error_code,
                        message=e.message,
                        value=e.details
                    )]
                )
                raise HTTPException(status_code=403, detail=error_response)
            else:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": e.message,
                        "error_code": e.error_code,
                        "details": e.details
                    }
                )
        except Exception as e:
            logger.error(f"权限检查过程中发生未知错误: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "权限检查过程中发生系统错误",
                    "error_code": "PERMISSION_CHECK_SYSTEM_ERROR"
                }
            )
    
    return wrapper