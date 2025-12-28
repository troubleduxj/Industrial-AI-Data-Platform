#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工业AI数据平台安全API
提供JWT认证、权限验证和审计日志接口

需求映射：
- 需求10.1: JWT令牌认证
- 需求10.2: 基于角色的访问控制
- 需求10.3: 敏感数据访问审计
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from pydantic import BaseModel, Field

from app.services.platform_security_service import (
    platform_security_service,
    ResourceType,
    ActionType,
    PlatformRole
)
from app.services.platform_audit_service import (
    platform_audit_service,
    AuditActionType
)
from app.core.auth_dependencies import get_current_user, get_current_active_user
from app.models.admin import User
from app.core.unified_logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/security", tags=["安全管理"])


# ==================== 请求/响应模型 ====================

class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    user: dict = Field(..., description="用户信息")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class PermissionCheckRequest(BaseModel):
    """权限检查请求"""
    resource_type: str = Field(..., description="资源类型")
    action: str = Field(..., description="操作类型")
    resource_id: Optional[str] = Field(None, description="资源ID")


class PermissionCheckResponse(BaseModel):
    """权限检查响应"""
    has_permission: bool = Field(..., description="是否有权限")
    reason: str = Field(..., description="原因")


class UserPermissionsResponse(BaseModel):
    """用户权限响应"""
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    is_superuser: bool = Field(..., description="是否超级用户")
    roles: List[str] = Field(..., description="角色列表")
    permissions: dict = Field(..., description="权限映射")


class AuditLogQuery(BaseModel):
    """审计日志查询参数"""
    user_id: Optional[int] = Field(None, description="用户ID")
    action_type: Optional[str] = Field(None, description="操作类型")
    resource_type: Optional[str] = Field(None, description="资源类型")
    risk_level: Optional[str] = Field(None, description="风险等级")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(50, ge=1, le=100, description="每页大小")


class SecurityEventQuery(BaseModel):
    """安全事件查询参数"""
    event_type: Optional[str] = Field(None, description="事件类型")
    event_level: Optional[str] = Field(None, description="事件级别")
    status: Optional[str] = Field(None, description="状态")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(50, ge=1, le=100, description="每页大小")


# ==================== 认证接口 ====================

@router.post("/login", response_model=LoginResponse, summary="用户登录")
async def login(request: Request, login_data: LoginRequest):
    """
    用户登录认证
    
    - 验证用户凭据
    - 生成JWT访问令牌和刷新令牌
    - 记录登录审计日志
    """
    try:
        result = await platform_security_service.authenticate_user(
            username=login_data.username,
            password=login_data.password,
            request=request
        )
        
        return {
            "success": True,
            "message": "登录成功",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        # 记录失败的登录尝试
        await platform_audit_service.log_failed_login(
            username=login_data.username,
            reason="认证失败",
            request=request
        )
        raise


@router.post("/refresh", summary="刷新令牌")
async def refresh_token(request: Request, refresh_data: RefreshTokenRequest):
    """
    刷新访问令牌
    
    - 验证刷新令牌
    - 生成新的访问令牌和刷新令牌
    """
    result = await platform_security_service.refresh_access_token(refresh_data.refresh_token)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新令牌无效或已过期"
        )
    
    return {
        "success": True,
        "message": "令牌刷新成功",
        "data": result,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/logout", summary="用户登出")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    用户登出
    
    - 将当前令牌加入黑名单
    - 清除刷新令牌
    - 记录登出审计日志
    """
    # 从请求头获取令牌
    authorization = request.headers.get("Authorization")
    token = authorization[7:] if authorization and authorization.startswith("Bearer ") else None
    
    if token:
        await platform_security_service.logout(token, current_user.id, request)
    
    return {
        "success": True,
        "message": "登出成功",
        "data": None,
        "timestamp": datetime.now().isoformat()
    }


# ==================== 权限接口 ====================

@router.post("/check-permission", response_model=PermissionCheckResponse, summary="检查权限")
async def check_permission(
    request: Request,
    check_data: PermissionCheckRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    检查用户是否有特定权限
    
    - 验证用户对指定资源的操作权限
    - 记录敏感操作的审计日志
    """
    try:
        resource_type = ResourceType(check_data.resource_type)
        action = ActionType(check_data.action)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的资源类型或操作类型"
        )
    
    has_permission, reason = await platform_security_service.check_permission(
        user_id=current_user.id,
        resource_type=resource_type,
        action=action,
        resource_id=check_data.resource_id,
        request=request
    )
    
    return {
        "success": True,
        "message": "权限检查完成",
        "data": {
            "has_permission": has_permission,
            "reason": reason
        },
        "timestamp": datetime.now().isoformat()
    }


@router.get("/permissions", response_model=UserPermissionsResponse, summary="获取用户权限")
async def get_user_permissions(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前用户的所有权限
    
    - 返回用户角色列表
    - 返回用户权限映射
    """
    permissions = await platform_security_service.get_user_permissions(current_user.id)
    
    return {
        "success": True,
        "message": "获取权限成功",
        "data": permissions,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/roles", summary="获取平台角色列表")
async def get_platform_roles(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取平台支持的角色列表
    """
    roles = [
        {
            "key": role.value,
            "name": {
                PlatformRole.ADMIN: "系统管理员",
                PlatformRole.DATA_SCIENTIST: "数据科学家",
                PlatformRole.MLOPS_ENGINEER: "MLOps工程师",
                PlatformRole.OPERATOR: "运营人员",
                PlatformRole.VIEWER: "只读用户"
            }.get(role, role.value),
            "description": {
                PlatformRole.ADMIN: "拥有所有权限",
                PlatformRole.DATA_SCIENTIST: "可以创建和管理AI模型",
                PlatformRole.MLOPS_ENGINEER: "可以部署和激活模型",
                PlatformRole.OPERATOR: "可以管理资产和执行预测",
                PlatformRole.VIEWER: "只读访问权限"
            }.get(role, "")
        }
        for role in PlatformRole
    ]
    
    return {
        "success": True,
        "message": "获取角色列表成功",
        "data": roles,
        "timestamp": datetime.now().isoformat()
    }


# ==================== 审计日志接口 ====================

@router.get("/audit-logs", summary="查询审计日志")
async def get_audit_logs(
    user_id: Optional[int] = Query(None, description="用户ID"),
    action_type: Optional[str] = Query(None, description="操作类型"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    risk_level: Optional[str] = Query(None, description="风险等级"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(get_current_active_user)
):
    """
    查询审计日志
    
    - 支持多条件过滤
    - 支持分页查询
    - 需要管理员权限查看所有日志
    """
    # 非管理员只能查看自己的日志
    if not current_user.is_superuser:
        user_id = current_user.id
    
    result = await platform_audit_service.get_audit_logs(
        user_id=user_id,
        action_type=action_type,
        resource_type=resource_type,
        risk_level=risk_level,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size
    )
    
    return {
        "success": True,
        "message": "查询成功",
        "data": result,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/security-events", summary="查询安全事件")
async def get_security_events(
    event_type: Optional[str] = Query(None, description="事件类型"),
    event_level: Optional[str] = Query(None, description="事件级别"),
    status: Optional[str] = Query(None, description="状态"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(get_current_active_user)
):
    """
    查询安全事件
    
    - 需要管理员权限
    - 支持多条件过滤
    - 支持分页查询
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    result = await platform_audit_service.get_security_events(
        event_type=event_type,
        event_level=event_level,
        status=status,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size
    )
    
    return {
        "success": True,
        "message": "查询成功",
        "data": result,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/audit-statistics", summary="获取审计统计")
async def get_audit_statistics(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取审计统计信息
    
    - 需要管理员权限
    - 返回操作统计、风险统计、安全事件统计
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    result = await platform_audit_service.get_audit_statistics(
        start_time=start_time,
        end_time=end_time
    )
    
    return {
        "success": True,
        "message": "获取统计成功",
        "data": result,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/action-types", summary="获取操作类型列表")
async def get_action_types(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取支持的审计操作类型列表
    """
    action_types = [
        {"key": action.value, "name": action.value}
        for action in AuditActionType
    ]
    
    return {
        "success": True,
        "message": "获取操作类型成功",
        "data": action_types,
        "timestamp": datetime.now().isoformat()
    }
