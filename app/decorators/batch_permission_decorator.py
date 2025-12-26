"""
批量操作权限装饰器
"""
import functools
from typing import List, Any, Optional, Callable
from fastapi import HTTPException, Depends, Request
from app.services.batch_operation_service import (
    batch_operation_service, 
    BatchOperationRequest, 
    BatchOperationType
)
from app.core.auth_dependencies import get_current_user
from app.models.admin import User
from app.core.unified_logger import get_logger

logger = get_logger(__name__)


def require_batch_permission(
    resource_type: str,
    operation_type: BatchOperationType,
    item_ids_param: str = "ids",
    reason_param: Optional[str] = None,
    additional_data_param: Optional[str] = None
):
    """
    批量操作权限装饰器
    
    Args:
        resource_type: 资源类型 (如: users, roles, devices)
        operation_type: 操作类型 (BatchOperationType枚举)
        item_ids_param: 包含项目ID列表的参数名
        reason_param: 包含操作原因的参数名
        additional_data_param: 包含额外数据的参数名
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取请求对象和当前用户
            request = None
            current_user = None
            
            # 从参数中提取Request和User对象
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                elif isinstance(arg, Admin):
                    current_user = arg
            
            # 从kwargs中查找
            if not request:
                request = kwargs.get('request')
            if not current_user:
                current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(status_code=401, detail="未认证用户")
            
            # 提取批量操作参数
            item_ids = kwargs.get(item_ids_param)
            if not item_ids:
                # 尝试从请求体中获取
                if hasattr(request, 'json') and callable(request.json):
                    try:
                        body = await request.json()
                        item_ids = body.get(item_ids_param, [])
                    except:
                        pass
            
            if not item_ids or not isinstance(item_ids, list):
                raise HTTPException(
                    status_code=400, 
                    detail=f"缺少有效的{item_ids_param}参数"
                )
            
            # 获取操作原因和额外数据
            reason = kwargs.get(reason_param) if reason_param else None
            additional_data = kwargs.get(additional_data_param) if additional_data_param else None
            
            # 创建批量操作请求
            batch_request = BatchOperationRequest(
                user_id=current_user.id,
                resource_type=resource_type,
                operation_type=operation_type,
                item_ids=item_ids,
                additional_data=additional_data,
                reason=reason
            )
            
            # 检查批量操作权限
            permission_result = await batch_operation_service.check_batch_operation_permission(
                batch_request, current_user
            )
            
            if not permission_result.success:
                logger.warning(f"批量操作权限检查失败: 用户{current_user.username}, 资源{resource_type}, 操作{operation_type.value}")
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": permission_result.error_message or "批量操作权限不足",
                        "total_requested": permission_result.total_requested,
                        "total_denied": permission_result.total_denied,
                        "warnings": permission_result.warnings
                    }
                )
            
            # 如果有部分项目被拒绝，更新参数
            if permission_result.total_allowed < permission_result.total_requested:
                logger.info(f"批量操作部分允许: 请求{permission_result.total_requested}项, 允许{permission_result.total_allowed}项")
                kwargs[item_ids_param] = permission_result.allowed_items
                
                # 将权限检查结果添加到kwargs中，供业务逻辑使用
                kwargs['_batch_permission_result'] = permission_result
            
            # 执行原始函数
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def batch_delete_permission(resource_type: str, item_ids_param: str = "ids"):
    """批量删除权限装饰器"""
    return require_batch_permission(
        resource_type=resource_type,
        operation_type=BatchOperationType.DELETE,
        item_ids_param=item_ids_param,
        reason_param="reason"
    )


def batch_update_permission(resource_type: str, item_ids_param: str = "ids"):
    """批量更新权限装饰器"""
    return require_batch_permission(
        resource_type=resource_type,
        operation_type=BatchOperationType.UPDATE,
        item_ids_param=item_ids_param
    )


def batch_deactivate_permission(resource_type: str, item_ids_param: str = "ids"):
    """批量停用权限装饰器"""
    return require_batch_permission(
        resource_type=resource_type,
        operation_type=BatchOperationType.DEACTIVATE,
        item_ids_param=item_ids_param,
        reason_param="reason"
    )


class BatchPermissionChecker:
    """批量权限检查器类"""
    
    @staticmethod
    async def check_and_filter_items(
        user: Admin,
        resource_type: str,
        operation_type: BatchOperationType,
        item_ids: List[Any],
        reason: Optional[str] = None,
        additional_data: Optional[dict] = None
    ) -> dict:
        """
        检查并过滤项目
        
        Returns:
            dict: 包含允许的项目、拒绝的项目和权限检查结果
        """
        batch_request = BatchOperationRequest(
            user_id=user.id,
            resource_type=resource_type,
            operation_type=operation_type,
            item_ids=item_ids,
            additional_data=additional_data,
            reason=reason
        )
        
        permission_result = await batch_operation_service.check_batch_operation_permission(
            batch_request, user
        )
        
        return {
            "success": permission_result.success,
            "allowed_items": permission_result.allowed_items,
            "denied_items": permission_result.denied_items,
            "protected_items": permission_result.protected_items,
            "permission_result": permission_result
        }
    
    @staticmethod
    async def validate_batch_operation(
        user: Admin,
        resource_type: str,
        operation_type: BatchOperationType,
        item_ids: List[Any],
        raise_on_failure: bool = True
    ) -> bool:
        """
        验证批量操作权限
        
        Args:
            user: 当前用户
            resource_type: 资源类型
            operation_type: 操作类型
            item_ids: 项目ID列表
            raise_on_failure: 失败时是否抛出异常
            
        Returns:
            bool: 是否有权限执行操作
        """
        batch_request = BatchOperationRequest(
            user_id=user.id,
            resource_type=resource_type,
            operation_type=operation_type,
            item_ids=item_ids
        )
        
        permission_result = await batch_operation_service.check_batch_operation_permission(
            batch_request, user
        )
        
        if not permission_result.success and raise_on_failure:
            raise HTTPException(
                status_code=403,
                detail=permission_result.error_message or "批量操作权限不足"
            )
        
        return permission_result.success


# 便捷的权限检查器实例
batch_permission_checker = BatchPermissionChecker()