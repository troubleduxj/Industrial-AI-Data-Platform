"""
批量操作权限控制器
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Query, Body
from pydantic import BaseModel, Field
from app.core.auth_dependencies import get_current_user
from app.models.admin import User
from app.services.batch_operation_service import (
    batch_operation_service, 
    BatchOperationType, 
    BatchOperationRequest,
    ProtectionLevel
)
from app.decorators.batch_permission_decorator import batch_permission_checker
from app.core.unified_logger import get_logger

logger = get_logger(__name__)


router = APIRouter(tags=["批量操作权限控制"])


class BatchPermissionCheckRequest(BaseModel):
    """批量权限检查请求"""
    resource_type: str = Field(..., description="资源类型")
    operation_type: str = Field(..., description="操作类型")
    item_ids: List[Any] = Field(..., description="项目ID列表")
    reason: Optional[str] = Field(None, description="操作原因")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="额外数据")


class BatchPermissionCheckResponse(BaseModel):
    """批量权限检查响应"""
    success: bool = Field(..., description="是否成功")
    allowed_items: List[Any] = Field(..., description="允许的项目")
    denied_items: List[Any] = Field(..., description="拒绝的项目")
    protected_items: List[Any] = Field(..., description="受保护的项目")
    total_requested: int = Field(..., description="请求总数")
    total_allowed: int = Field(..., description="允许总数")
    total_denied: int = Field(..., description="拒绝总数")
    warnings: Optional[List[str]] = Field(None, description="警告信息")
    error_message: Optional[str] = Field(None, description="错误信息")


class BatchOperationLimitsResponse(BaseModel):
    """批量操作限制响应"""
    resource_type: str = Field(..., description="资源类型")
    operations: Dict[str, Dict[str, Any]] = Field(..., description="操作限制")


@router.post("/check-permission", response_model=BatchPermissionCheckResponse)
async def check_batch_permission(
    request: Request,
    check_request: BatchPermissionCheckRequest,
    current_user: Admin = Depends(get_current_user)
):
    """检查批量操作权限"""
    try:
        # 验证操作类型
        try:
            operation_type = BatchOperationType(check_request.operation_type.upper())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的操作类型: {check_request.operation_type}"
            )
        
        # 创建批量操作请求
        batch_request = BatchOperationRequest(
            user_id=current_user.id,
            resource_type=check_request.resource_type,
            operation_type=operation_type,
            item_ids=check_request.item_ids,
            additional_data=check_request.additional_data,
            reason=check_request.reason
        )
        
        # 执行权限检查
        result = await batch_operation_service.check_batch_operation_permission(
            batch_request, current_user
        )
        
        return BatchPermissionCheckResponse(
            success=result.success,
            allowed_items=result.allowed_items,
            denied_items=result.denied_items,
            protected_items=result.protected_items,
            total_requested=result.total_requested,
            total_allowed=result.total_allowed,
            total_denied=result.total_denied,
            warnings=result.warnings,
            error_message=result.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量权限检查失败: {e}")
        raise HTTPException(status_code=500, detail="批量权限检查失败")


@router.get("/limits/{resource_type}", response_model=BatchOperationLimitsResponse)
async def get_batch_operation_limits(
    resource_type: str,
    current_user: Admin = Depends(get_current_user)
):
    """获取批量操作限制"""
    try:
        limits = batch_operation_service.get_operation_limits(resource_type)
        
        return BatchOperationLimitsResponse(
            resource_type=resource_type,
            operations=limits
        )
        
    except Exception as e:
        logger.error(f"获取批量操作限制失败: {e}")
        raise HTTPException(status_code=500, detail="获取批量操作限制失败")


@router.get("/supported-resources")
async def get_supported_resources(
    current_user: Admin = Depends(get_current_user)
):
    """获取支持的资源类型"""
    try:
        supported_resources = list(batch_operation_service.default_rules.keys())
        
        resource_info = {}
        for resource_type in supported_resources:
            limits = batch_operation_service.get_operation_limits(resource_type)
            resource_info[resource_type] = {
                "supported_operations": list(limits.keys()),
                "operation_details": limits
            }
        
        return {
            "code": 200,
            "message": "获取支持的资源类型成功",
            "data": {
                "supported_resources": supported_resources,
                "resource_details": resource_info
            }
        }
        
    except Exception as e:
        logger.error(f"获取支持的资源类型失败: {e}")
        raise HTTPException(status_code=500, detail="获取支持的资源类型失败")


@router.get("/operation-types")
async def get_operation_types(
    current_user: Admin = Depends(get_current_user)
):
    """获取支持的操作类型"""
    try:
        operation_types = [
            {
                "value": op.value,
                "label": {
                    "DELETE": "删除",
                    "UPDATE": "更新",
                    "CREATE": "创建",
                    "EXPORT": "导出",
                    "IMPORT": "导入",
                    "ACTIVATE": "激活",
                    "DEACTIVATE": "停用"
                }.get(op.value, op.value)
            }
            for op in BatchOperationType
        ]
        
        return {
            "code": 200,
            "message": "获取操作类型成功",
            "data": operation_types
        }
        
    except Exception as e:
        logger.error(f"获取操作类型失败: {e}")
        raise HTTPException(status_code=500, detail="获取操作类型失败")


@router.get("/protection-levels")
async def get_protection_levels(
    current_user: Admin = Depends(get_current_user)
):
    """获取保护级别"""
    try:
        protection_levels = [
            {
                "value": level.value,
                "label": {
                    "NONE": "无保护",
                    "LOW": "低保护",
                    "MEDIUM": "中保护",
                    "HIGH": "高保护",
                    "CRITICAL": "关键保护"
                }.get(level.value, level.value),
                "description": {
                    "NONE": "无特殊保护措施",
                    "LOW": "基础权限检查",
                    "MEDIUM": "增强权限检查和审计",
                    "HIGH": "严格权限检查，需要审批",
                    "CRITICAL": "最高级别保护，需要多重审批"
                }.get(level.value, "")
            }
            for level in ProtectionLevel
        ]
        
        return {
            "code": 200,
            "message": "获取保护级别成功",
            "data": protection_levels
        }
        
    except Exception as e:
        logger.error(f"获取保护级别失败: {e}")
        raise HTTPException(status_code=500, detail="获取保护级别失败")


@router.post("/validate-items")
async def validate_batch_items(
    request: Request,
    resource_type: str = Body(..., description="资源类型"),
    operation_type: str = Body(..., description="操作类型"),
    item_ids: List[Any] = Body(..., description="项目ID列表"),
    current_user: Admin = Depends(get_current_user)
):
    """验证批量操作项目"""
    try:
        # 验证操作类型
        try:
            operation_enum = BatchOperationType(operation_type.upper())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的操作类型: {operation_type}"
            )
        
        # 使用权限检查器验证
        result = await batch_permission_checker.check_and_filter_items(
            user=current_user,
            resource_type=resource_type,
            operation_type=operation_enum,
            item_ids=item_ids
        )
        
        return {
            "code": 200,
            "message": "项目验证完成",
            "data": {
                "validation_result": result["success"],
                "allowed_items": result["allowed_items"],
                "denied_items": result["denied_items"],
                "protected_items": result["protected_items"],
                "summary": {
                    "total_requested": len(item_ids),
                    "total_allowed": len(result["allowed_items"]),
                    "total_denied": len(result["denied_items"]),
                    "total_protected": len(result["protected_items"])
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证批量操作项目失败: {e}")
        raise HTTPException(status_code=500, detail="验证批量操作项目失败")


@router.get("/user-permissions/{resource_type}")
async def get_user_batch_permissions(
    resource_type: str,
    current_user: Admin = Depends(get_current_user)
):
    """获取用户的批量操作权限"""
    try:
        # 获取资源的操作限制
        limits = batch_operation_service.get_operation_limits(resource_type)
        
        # 检查用户对每种操作的权限
        user_permissions = {}
        
        for operation_type_str, operation_info in limits.items():
            try:
                operation_type = BatchOperationType(operation_type_str)
                
                # 创建测试请求（空的项目列表）
                test_request = BatchOperationRequest(
                    user_id=current_user.id,
                    resource_type=resource_type,
                    operation_type=operation_type,
                    item_ids=[]
                )
                
                # 获取操作规则
                rule = batch_operation_service._get_operation_rule(resource_type, operation_type)
                if rule:
                    # 检查基础权限
                    has_permission = await batch_operation_service._check_basic_permissions(current_user, rule)
                    
                    user_permissions[operation_type_str] = {
                        "allowed": has_permission,
                        "max_items": operation_info["max_items"],
                        "protection_level": operation_info["protection_level"],
                        "approval_required": operation_info["approval_required"],
                        "audit_required": operation_info["audit_required"],
                        "required_permissions": operation_info["required_permissions"]
                    }
                
            except ValueError:
                continue
        
        return {
            "code": 200,
            "message": "获取用户批量操作权限成功",
            "data": {
                "resource_type": resource_type,
                "user_id": current_user.id,
                "username": current_user.username,
                "is_superuser": current_user.is_superuser,
                "permissions": user_permissions
            }
        }
        
    except Exception as e:
        logger.error(f"获取用户批量操作权限失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户批量操作权限失败")


@router.post("/simulate-operation")
async def simulate_batch_operation(
    request: Request,
    check_request: BatchPermissionCheckRequest,
    current_user: Admin = Depends(get_current_user)
):
    """模拟批量操作（仅检查权限，不执行实际操作）"""
    try:
        # 验证操作类型
        try:
            operation_type = BatchOperationType(check_request.operation_type.upper())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的操作类型: {check_request.operation_type}"
            )
        
        # 创建批量操作请求
        batch_request = BatchOperationRequest(
            user_id=current_user.id,
            resource_type=check_request.resource_type,
            operation_type=operation_type,
            item_ids=check_request.item_ids,
            additional_data=check_request.additional_data,
            reason=check_request.reason
        )
        
        # 执行权限检查
        result = await batch_operation_service.check_batch_operation_permission(
            batch_request, current_user
        )
        
        # 生成模拟结果
        simulation_result = {
            "would_succeed": result.success,
            "permission_check": {
                "allowed_items": result.allowed_items,
                "denied_items": result.denied_items,
                "protected_items": result.protected_items,
                "total_requested": result.total_requested,
                "total_allowed": result.total_allowed,
                "total_denied": result.total_denied
            },
            "warnings": result.warnings,
            "error_message": result.error_message,
            "estimated_impact": {
                "items_affected": len(result.allowed_items),
                "items_protected": len(result.protected_items),
                "success_rate": len(result.allowed_items) / len(check_request.item_ids) * 100 if check_request.item_ids else 0
            }
        }
        
        return {
            "code": 200,
            "message": "批量操作模拟完成",
            "data": simulation_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"模拟批量操作失败: {e}")
        raise HTTPException(status_code=500, detail="模拟批量操作失败")