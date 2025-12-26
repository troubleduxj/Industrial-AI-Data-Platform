"""
部门权限控制器
提供部门权限管理的API接口
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from pydantic import BaseModel, Field

from app.core.auth_dependencies import get_current_user
from app.models.admin import User
from app.services.department_permission_service import department_permission_service
from app.middleware.department_permission_middleware import department_permission_middleware
from app.middleware.data_permission_middleware import data_permission_middleware
from app.security.department_security_checker import department_security_checker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/department", tags=["部门权限"])


class DepartmentAccessRequest(BaseModel):
    """部门访问权限请求"""
    department_id: int = Field(..., description="部门ID")
    operation: str = Field(default="read", description="操作类型")


class CrossDepartmentAccessRequest(BaseModel):
    """跨部门访问权限请求"""
    source_department_id: int = Field(..., description="源部门ID")
    target_department_id: int = Field(..., description="目标部门ID")


class BatchOperationRequest(BaseModel):
    """批量操作权限请求"""
    target_ids: List[int] = Field(..., description="目标数据ID列表")
    operation: str = Field(default="delete", description="操作类型")
    resource_type: str = Field(..., description="资源类型")


class DepartmentIsolationRequest(BaseModel):
    """部门隔离验证请求"""
    department_ids: List[int] = Field(..., description="部门ID列表")
    operation: str = Field(default="read", description="操作类型")


@router.get("/accessible", summary="获取用户可访问的部门列表")
async def get_accessible_departments(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """获取当前用户可访问的部门列表"""
    try:
        result = await department_permission_middleware.get_user_accessible_departments(request)
        
        if result.get("success", False):
            return {
                "code": 200,
                "message": result.get("message"),
                "data": {
                    "departments": result.get("departments", []),
                    "total": result.get("total", 0)
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "获取可访问部门列表失败")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取可访问部门列表失败: error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )


@router.post("/check-access", summary="检查部门访问权限")
async def check_department_access(
    request_data: DepartmentAccessRequest,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """检查用户对指定部门的访问权限"""
    try:
        result = await department_permission_middleware.check_department_access(
            request, request_data.department_id
        )
        
        return {
            "code": 200,
            "message": "部门访问权限检查完成",
            "data": {
                "allowed": result.get("allowed", False),
                "reason": result.get("reason"),
                "message": result.get("message"),
                "department_id": request_data.department_id,
                "operation": request_data.operation
            }
        }
        
    except Exception as e:
        logger.error(f"检查部门访问权限失败: error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"权限检查失败: {str(e)}"
        )


@router.post("/check-cross-access", summary="检查跨部门访问权限")
async def check_cross_department_access(
    request_data: CrossDepartmentAccessRequest,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """检查用户的跨部门访问权限"""
    try:
        result = await department_permission_middleware.validate_cross_department_access(
            request, 
            request_data.source_department_id, 
            request_data.target_department_id
        )
        
        return {
            "code": 200,
            "message": "跨部门访问权限检查完成",
            "data": {
                "allowed": result.get("allowed", False),
                "reason": result.get("reason"),
                "message": result.get("message"),
                "source_department_id": request_data.source_department_id,
                "target_department_id": request_data.target_department_id
            }
        }
        
    except Exception as e:
        logger.error(f"检查跨部门访问权限失败: error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"跨部门权限检查失败: {str(e)}"
        )


@router.get("/scope", summary="获取用户部门权限范围")
async def get_user_department_scope(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的部门权限范围信息"""
    try:
        scope_info = await department_permission_service.get_user_department_scope(current_user.id)
        
        return {
            "code": 200,
            "message": "获取用户部门权限范围成功",
            "data": scope_info
        }
        
    except Exception as e:
        logger.error(f"获取用户部门权限范围失败: error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取权限范围失败: {str(e)}"
        )


@router.post("/data/check-access", summary="检查数据访问权限")
async def check_data_access_permission(
    department_id: int = Query(..., description="数据所属部门ID"),
    operation: str = Query(default="read", description="操作类型"),
    current_user: User = Depends(get_current_user)
):
    """检查用户对特定部门数据的访问权限"""
    try:
        result = await data_permission_middleware.check_data_access_permission(
            current_user, department_id, operation
        )
        
        return {
            "code": 200,
            "message": "数据访问权限检查完成",
            "data": {
                "allowed": result.get("allowed", False),
                "reason": result.get("reason"),
                "message": result.get("message"),
                "department_id": department_id,
                "operation": operation
            }
        }
        
    except Exception as e:
        logger.error(f"检查数据访问权限失败: error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据权限检查失败: {str(e)}"
        )


@router.post("/batch/validate-permission", summary="验证批量操作权限")
async def validate_batch_operation_permission(
    request_data: BatchOperationRequest,
    current_user: User = Depends(get_current_user)
):
    """验证用户的批量操作权限"""
    try:
        # 这里需要根据资源类型定义获取部门ID的函数
        async def get_department_func(target_id: int) -> Optional[int]:
            # 简化实现，实际应该根据资源类型查询对应的部门ID
            # 例如：如果是设备，查询设备表的department_id字段
            return 1  # 示例返回
        
        result = await data_permission_middleware.validate_batch_operation_permission(
            current_user, 
            request_data.target_ids,
            get_department_func,
            request_data.operation
        )
        
        return {
            "code": 200,
            "message": "批量操作权限验证完成",
            "data": {
                "allowed": result.get("allowed", False),
                "reason": result.get("reason"),
                "message": result.get("message"),
                "allowed_ids": result.get("allowed_ids", []),
                "denied_ids": result.get("denied_ids", []),
                "operation": request_data.operation,
                "resource_type": request_data.resource_type
            }
        }
        
    except Exception as e:
        logger.error(f"验证批量操作权限失败: error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量操作权限验证失败: {str(e)}"
        )


@router.get("/data/statistics", summary="获取部门数据统计")
async def get_department_data_statistics(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """获取用户可访问的部门数据统计"""
    try:
        result = await data_permission_middleware.get_department_data_statistics(request)
        
        if result.get("success", False):
            return {
                "code": 200,
                "message": result.get("message"),
                "data": result.get("data", {})
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "获取部门数据统计失败")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取部门数据统计失败: error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取数据统计失败: {str(e)}"
        )


@router.post("/security/validate-isolation", summary="验证部门隔离")
async def validate_department_isolation(
    request_data: DepartmentIsolationRequest,
    current_user: User = Depends(get_current_user)
):
    """验证部门隔离完整性"""
    try:
        result = await department_security_checker.validate_department_isolation(
            current_user, 
            request_data.department_ids,
            request_data.operation
        )
        
        return {
            "code": 200,
            "message": "部门隔离验证完成",
            "data": {
                "valid": result.get("valid", False),
                "reason": result.get("reason"),
                "message": result.get("message"),
                "violations": result.get("violations", []),
                "department_ids": request_data.department_ids,
                "operation": request_data.operation
            }
        }
        
    except Exception as e:
        logger.error(f"验证部门隔离失败: error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"部门隔离验证失败: {str(e)}"
        )


@router.post("/security/check-leakage-risk", summary="检查数据泄露风险")
async def check_data_leakage_risk(
    query_conditions: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """检查查询操作的数据泄露风险"""
    try:
        result = await department_security_checker.check_data_leakage_risk(
            current_user, query_conditions
        )
        
        return {
            "code": 200,
            "message": "数据泄露风险检查完成",
            "data": {
                "safe": result.get("safe", False),
                "risk_level": result.get("risk_level", "unknown"),
                "message": result.get("message"),
                "risks": result.get("risks", []),
                "recommendations": result.get("recommendations", [])
            }
        }
        
    except Exception as e:
        logger.error(f"检查数据泄露风险失败: error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据泄露风险检查失败: {str(e)}"
        )


@router.get("/security/summary", summary="获取用户安全摘要")
async def get_user_security_summary(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的安全摘要"""
    try:
        result = await department_security_checker.get_security_summary(current_user.id)
        
        return {
            "code": 200,
            "message": "获取用户安全摘要成功",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"获取用户安全摘要失败: error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取安全摘要失败: {str(e)}"
        )


@router.post("/hierarchy/validate", summary="验证部门层级访问权限")
async def validate_department_hierarchy(
    parent_department_id: int = Query(..., description="父部门ID"),
    child_department_id: int = Query(..., description="子部门ID"),
    current_user: User = Depends(get_current_user)
):
    """验证用户对部门层级关系的访问权限"""
    try:
        result = await department_security_checker.validate_department_hierarchy(
            current_user, parent_department_id, child_department_id
        )
        
        return {
            "code": 200,
            "message": "部门层级访问权限验证完成",
            "data": {
                "valid": result.get("valid", False),
                "reason": result.get("reason"),
                "message": result.get("message"),
                "parent_department_id": parent_department_id,
                "child_department_id": child_department_id
            }
        }
        
    except Exception as e:
        logger.error(f"验证部门层级访问权限失败: error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"部门层级权限验证失败: {str(e)}"
        )


@router.post("/audit/access", summary="审计部门访问操作")
async def audit_department_access(
    operation: str = Query(..., description="操作类型"),
    resource_type: str = Query(..., description="资源类型"),
    resource_ids: List[int] = Query(..., description="资源ID列表"),
    department_ids: List[int] = Query(..., description="涉及的部门ID列表"),
    current_user: User = Depends(get_current_user)
):
    """审计用户的部门访问操作"""
    try:
        result = await department_security_checker.audit_department_access(
            current_user, operation, resource_type, resource_ids, department_ids
        )
        
        return {
            "code": 200,
            "message": "部门访问审计完成",
            "data": {
                "success": result.get("success", False),
                "message": result.get("message"),
                "audit_id": result.get("audit_id"),
                "security_status": result.get("security_status")
            }
        }
        
    except Exception as e:
        logger.error(f"审计部门访问操作失败: error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"访问审计失败: {str(e)}"
        )