"""
批量操作API示例
展示如何使用批量操作权限控制
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Body
from pydantic import BaseModel, Field
from app.core.auth_dependencies import get_current_user
from app.models.admin import User
from app.decorators.batch_permission_decorator import (
    batch_delete_permission,
    batch_update_permission,
    batch_deactivate_permission,
    batch_permission_checker
)
from app.services.batch_operation_service import BatchOperationType
from app.controllers.batch_operation_controller import router as batch_controller_router
from app.core.unified_logger import get_logger

logger = get_logger(__name__)


router = APIRouter()

# 包含批量操作控制器的路由
router.include_router(batch_controller_router, prefix="/control")


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    ids: List[int] = Field(..., description="要删除的ID列表")
    reason: Optional[str] = Field(None, description="删除原因")


class BatchUpdateRequest(BaseModel):
    """批量更新请求"""
    ids: List[int] = Field(..., description="要更新的ID列表")
    data: dict = Field(..., description="更新数据")


class BatchDeactivateRequest(BaseModel):
    """批量停用请求"""
    ids: List[int] = Field(..., description="要停用的ID列表")
    reason: Optional[str] = Field(None, description="停用原因")


class BatchOperationResponse(BaseModel):
    """批量操作响应"""
    success: bool = Field(..., description="是否成功")
    processed_count: int = Field(..., description="处理数量")
    failed_count: int = Field(..., description="失败数量")
    details: Optional[dict] = Field(None, description="详细信息")


# 用户批量操作示例
@router.delete("/users/batch")
@batch_delete_permission(resource_type="users")
async def batch_delete_users(
    request: Request,
    delete_request: BatchDeleteRequest,
    current_user: Admin = Depends(get_current_user)
):
    """批量删除用户"""
    try:
        # 获取权限检查结果（由装饰器注入）
        permission_result = request.state.__dict__.get('_batch_permission_result')
        
        # 实际的删除逻辑
        deleted_count = 0
        failed_count = 0
        
        # 这里应该实现实际的删除逻辑
        # 注意：delete_request.ids 已经被装饰器过滤，只包含允许删除的项目
        for user_id in delete_request.ids:
            try:
                # 模拟删除操作
                logger.info(f"删除用户 {user_id}")
                deleted_count += 1
            except Exception as e:
                logger.error(f"删除用户 {user_id} 失败: {e}")
                failed_count += 1
        
        return {
            "code": 200,
            "message": f"批量删除完成，成功 {deleted_count} 项，失败 {failed_count} 项",
            "data": {
                "success": failed_count == 0,
                "processed_count": deleted_count,
                "failed_count": failed_count,
                "permission_info": {
                    "total_requested": permission_result.total_requested if permission_result else len(delete_request.ids),
                    "total_allowed": permission_result.total_allowed if permission_result else len(delete_request.ids),
                    "protected_items": permission_result.protected_items if permission_result else []
                } if permission_result else None
            }
        }
        
    except Exception as e:
        logger.error(f"批量删除用户失败: {e}")
        raise HTTPException(status_code=500, detail="批量删除用户失败")


@router.put("/users/batch")
@batch_update_permission(resource_type="users")
async def batch_update_users(
    request: Request,
    update_request: BatchUpdateRequest,
    current_user: Admin = Depends(get_current_user)
):
    """批量更新用户"""
    try:
        # 实际的更新逻辑
        updated_count = 0
        failed_count = 0
        
        for user_id in update_request.ids:
            try:
                # 模拟更新操作
                logger.info(f"更新用户 {user_id}: {update_request.data}")
                updated_count += 1
            except Exception as e:
                logger.error(f"更新用户 {user_id} 失败: {e}")
                failed_count += 1
        
        return {
            "code": 200,
            "message": f"批量更新完成，成功 {updated_count} 项，失败 {failed_count} 项",
            "data": {
                "success": failed_count == 0,
                "processed_count": updated_count,
                "failed_count": failed_count
            }
        }
        
    except Exception as e:
        logger.error(f"批量更新用户失败: {e}")
        raise HTTPException(status_code=500, detail="批量更新用户失败")


@router.post("/users/batch-deactivate")
@batch_deactivate_permission(resource_type="users")
async def batch_deactivate_users(
    request: Request,
    deactivate_request: BatchDeactivateRequest,
    current_user: Admin = Depends(get_current_user)
):
    """批量停用用户"""
    try:
        # 实际的停用逻辑
        deactivated_count = 0
        failed_count = 0
        
        for user_id in deactivate_request.ids:
            try:
                # 模拟停用操作
                logger.info(f"停用用户 {user_id}, 原因: {deactivate_request.reason}")
                deactivated_count += 1
            except Exception as e:
                logger.error(f"停用用户 {user_id} 失败: {e}")
                failed_count += 1
        
        return {
            "code": 200,
            "message": f"批量停用完成，成功 {deactivated_count} 项，失败 {failed_count} 项",
            "data": {
                "success": failed_count == 0,
                "processed_count": deactivated_count,
                "failed_count": failed_count
            }
        }
        
    except Exception as e:
        logger.error(f"批量停用用户失败: {e}")
        raise HTTPException(status_code=500, detail="批量停用用户失败")


# 角色批量操作示例
@router.delete("/roles/batch")
@batch_delete_permission(resource_type="roles")
async def batch_delete_roles(
    request: Request,
    delete_request: BatchDeleteRequest,
    current_user: Admin = Depends(get_current_user)
):
    """批量删除角色"""
    try:
        deleted_count = 0
        failed_count = 0
        
        for role_id in delete_request.ids:
            try:
                # 模拟删除操作
                logger.info(f"删除角色 {role_id}")
                deleted_count += 1
            except Exception as e:
                logger.error(f"删除角色 {role_id} 失败: {e}")
                failed_count += 1
        
        return {
            "code": 200,
            "message": f"批量删除角色完成，成功 {deleted_count} 项，失败 {failed_count} 项",
            "data": {
                "success": failed_count == 0,
                "processed_count": deleted_count,
                "failed_count": failed_count
            }
        }
        
    except Exception as e:
        logger.error(f"批量删除角色失败: {e}")
        raise HTTPException(status_code=500, detail="批量删除角色失败")


# 设备批量操作示例
@router.delete("/devices/batch")
@batch_delete_permission(resource_type="devices")
async def batch_delete_devices(
    request: Request,
    delete_request: BatchDeleteRequest,
    current_user: Admin = Depends(get_current_user)
):
    """批量删除设备"""
    try:
        deleted_count = 0
        failed_count = 0
        
        for device_id in delete_request.ids:
            try:
                # 模拟删除操作
                logger.info(f"删除设备 {device_id}")
                deleted_count += 1
            except Exception as e:
                logger.error(f"删除设备 {device_id} 失败: {e}")
                failed_count += 1
        
        return {
            "code": 200,
            "message": f"批量删除设备完成，成功 {deleted_count} 项，失败 {failed_count} 项",
            "data": {
                "success": failed_count == 0,
                "processed_count": deleted_count,
                "failed_count": failed_count
            }
        }
        
    except Exception as e:
        logger.error(f"批量删除设备失败: {e}")
        raise HTTPException(status_code=500, detail="批量删除设备失败")


@router.put("/devices/batch")
@batch_update_permission(resource_type="devices")
async def batch_update_devices(
    request: Request,
    update_request: BatchUpdateRequest,
    current_user: Admin = Depends(get_current_user)
):
    """批量更新设备"""
    try:
        updated_count = 0
        failed_count = 0
        
        for device_id in update_request.ids:
            try:
                # 模拟更新操作
                logger.info(f"更新设备 {device_id}: {update_request.data}")
                updated_count += 1
            except Exception as e:
                logger.error(f"更新设备 {device_id} 失败: {e}")
                failed_count += 1
        
        return {
            "code": 200,
            "message": f"批量更新设备完成，成功 {updated_count} 项，失败 {failed_count} 项",
            "data": {
                "success": failed_count == 0,
                "processed_count": updated_count,
                "failed_count": failed_count
            }
        }
        
    except Exception as e:
        logger.error(f"批量更新设备失败: {e}")
        raise HTTPException(status_code=500, detail="批量更新设备失败")


# 手动权限检查示例
@router.post("/manual-check-example")
async def manual_permission_check_example(
    request: Request,
    resource_type: str = Body(..., description="资源类型"),
    operation_type: str = Body(..., description="操作类型"),
    item_ids: List[int] = Body(..., description="项目ID列表"),
    current_user: Admin = Depends(get_current_user)
):
    """手动权限检查示例"""
    try:
        # 手动使用权限检查器
        operation_enum = BatchOperationType(operation_type.upper())
        
        result = await batch_permission_checker.check_and_filter_items(
            user=current_user,
            resource_type=resource_type,
            operation_type=operation_enum,
            item_ids=item_ids
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=403,
                detail="批量操作权限不足"
            )
        
        # 只处理允许的项目
        allowed_items = result["allowed_items"]
        
        # 模拟处理逻辑
        processed_items = []
        for item_id in allowed_items:
            processed_items.append({
                "id": item_id,
                "status": "processed",
                "message": f"成功处理项目 {item_id}"
            })
        
        return {
            "code": 200,
            "message": "手动权限检查示例完成",
            "data": {
                "permission_check": result,
                "processed_items": processed_items,
                "summary": {
                    "total_requested": len(item_ids),
                    "total_processed": len(processed_items),
                    "total_denied": len(result["denied_items"]),
                    "total_protected": len(result["protected_items"])
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"手动权限检查示例失败: {e}")
        raise HTTPException(status_code=500, detail="手动权限检查示例失败")