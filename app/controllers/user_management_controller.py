#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户管理API控制器
提供用户管理的REST API接口
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field, EmailStr

from app.services.user_management_service import user_management_service
from app.core.auth_dependencies import get_current_user, require_superuser, require_admin
from app.models.admin import User
from app.core.unified_logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v2/admin/users", tags=["用户管理"])


# Pydantic模型
class UserCreateRequest(BaseModel):
    """用户创建请求模型"""
    username: str = Field(..., description="用户名", max_length=20)
    nick_name: Optional[str] = Field(None, description="昵称", max_length=30)
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone_number: Optional[str] = Field(None, description="电话号码", max_length=20)
    sex: Optional[str] = Field(None, description="性别", max_length=10)
    avatar: Optional[str] = Field(None, description="头像URL", max_length=255)
    password: Optional[str] = Field(None, description="密码", min_length=6)
    user_type: Optional[str] = Field("00", description="用户类型", regex="^(00|01)$")
    status: Optional[str] = Field("0", description="用户状态", regex="^[01]$")
    remark: Optional[str] = Field(None, description="备注")
    dept_id: Optional[int] = Field(None, description="部门ID")
    role_ids: Optional[List[int]] = Field([], description="角色ID列表")


class UserUpdateRequest(BaseModel):
    """用户更新请求模型"""
    username: Optional[str] = Field(None, description="用户名", max_length=20)
    nick_name: Optional[str] = Field(None, description="昵称", max_length=30)
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone_number: Optional[str] = Field(None, description="电话号码", max_length=20)
    sex: Optional[str] = Field(None, description="性别", max_length=10)
    avatar: Optional[str] = Field(None, description="头像URL", max_length=255)
    password: Optional[str] = Field(None, description="密码", min_length=6)
    user_type: Optional[str] = Field(None, description="用户类型", regex="^(00|01)$")
    status: Optional[str] = Field(None, description="用户状态", regex="^[01]$")
    remark: Optional[str] = Field(None, description="备注")
    dept_id: Optional[int] = Field(None, description="部门ID")
    role_ids: Optional[List[int]] = Field(None, description="角色ID列表")


class UserStatusUpdateRequest(BaseModel):
    """用户状态更新请求模型"""
    status: str = Field(..., description="用户状态", regex="^[01]$")


class PasswordResetRequest(BaseModel):
    """密码重置请求模型"""
    new_password: Optional[str] = Field(None, description="新密码", min_length=6)


class PasswordChangeRequest(BaseModel):
    """密码修改请求模型"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., description="新密码", min_length=6)


class BatchStatusUpdateRequest(BaseModel):
    """批量状态更新请求模型"""
    user_ids: List[int] = Field(..., description="用户ID列表")
    status: str = Field(..., description="新状态", regex="^[01]$")


class BatchPasswordResetRequest(BaseModel):
    """批量密码重置请求模型"""
    user_ids: List[int] = Field(..., description="用户ID列表")


class UserRoleAssignRequest(BaseModel):
    """用户角色分配请求模型"""
    role_ids: List[int] = Field(..., description="角色ID列表")


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    nick_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    sex: Optional[str] = None
    avatar: Optional[str] = None
    user_type: str = "00"
    status: str = "0"
    remark: Optional[str] = None
    login_ip: Optional[str] = None
    login_date: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_superuser: bool = False
    is_active: bool = True


@router.post("/", summary="创建用户")
async def create_user(
    user_data: UserCreateRequest,
    current_user: User = Depends(require_admin)
):
    """创建新用户
    
    只有管理员及以上权限可以创建用户。
    """
    try:
        logger.info(f"用户 {current_user.username} 创建用户: {user_data.username}")
        
        user = await user_management_service.create_user(user_data.dict())
        
        return {
            "success": True,
            "message": "用户创建成功",
            "data": {
                "id": user.id,
                "username": user.username,
                "nick_name": user.nick_name,
                "email": user.email,
                "status": user.status
            }
        }
    
    except ValueError as e:
        logger.warning(f"创建用户失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建用户失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建用户失败: {str(e)}")


@router.get("/", summary="获取用户列表")
async def get_users(
    status: Optional[str] = Query(None, description="状态过滤"),
    user_type: Optional[str] = Query(None, description="用户类型过滤"),
    dept_id: Optional[int] = Query(None, description="部门ID过滤"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(get_current_user)
):
    """获取用户列表
    
    支持按状态、用户类型、部门等条件过滤，支持关键词搜索和分页。
    """
    try:
        result = await user_management_service.get_users(
            status=status,
            user_type=user_type,
            dept_id=dept_id,
            keyword=keyword,
            page=page,
            page_size=page_size
        )
        
        return {
            "success": True,
            "message": "获取用户列表成功",
            "data": result
        }
    
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户列表失败: {str(e)}")


@router.get("/{user_id}", summary="获取用户详情")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取指定用户的详细信息"""
    try:
        user = await user_management_service.get_user(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 获取用户角色
        roles = await user_management_service.get_user_roles(user_id)
        
        # 获取部门信息
        dept_info = None
        if user.dept:
            dept_info = {
                "id": user.dept.id,
                "dept_name": user.dept.dept_name
            }
        
        user_data = {
            "id": user.id,
            "username": user.username,
            "nick_name": user.nick_name,
            "email": user.email,
            "phone_number": user.phone_number,
            "sex": user.sex,
            "avatar": user.avatar,
            "user_type": user.user_type,
            "status": user.status,
            "remark": user.remark,
            "login_ip": user.login_ip,
            "login_date": user.login_date.isoformat() if user.login_date else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "is_superuser": user.is_superuser,
            "is_active": user.is_active,
            "roles": roles,
            "dept": dept_info
        }
        
        return {
            "success": True,
            "message": "获取用户详情成功",
            "data": user_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户详情失败: user_id={user_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"获取用户详情失败: {str(e)}")


@router.put("/{user_id}", summary="更新用户")
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    current_user: User = Depends(require_admin)
):
    """更新用户信息
    
    只有管理员及以上权限可以更新用户。
    """
    try:
        logger.info(f"用户 {current_user.username} 更新用户: id={user_id}")
        
        # 过滤掉None值
        update_data = {k: v for k, v in user_data.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="没有提供更新数据")
        
        user = await user_management_service.update_user(user_id, update_data)
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return {
            "success": True,
            "message": "用户更新成功",
            "data": {
                "id": user.id,
                "username": user.username,
                "nick_name": user.nick_name,
                "status": user.status
            }
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"更新用户失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新用户失败: user_id={user_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"更新用户失败: {str(e)}")


@router.delete("/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin)
):
    """删除用户
    
    执行软删除，只有管理员及以上权限可以删除用户。
    """
    try:
        logger.info(f"用户 {current_user.username} 删除用户: id={user_id}")
        
        success = await user_management_service.delete_user(user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return {
            "success": True,
            "message": "用户删除成功",
            "data": None
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"删除用户失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"删除用户失败: user_id={user_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"删除用户失败: {str(e)}")


@router.patch("/{user_id}/status", summary="更新用户状态")
async def update_user_status(
    user_id: int,
    status_data: UserStatusUpdateRequest,
    current_user: User = Depends(require_admin)
):
    """更新用户状态
    
    可以启用或禁用用户，只有管理员及以上权限可以操作。
    """
    try:
        logger.info(f"用户 {current_user.username} 更新用户状态: id={user_id}, status={status_data.status}")
        
        success = await user_management_service.update_user_status(user_id, status_data.status)
        
        if not success:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return {
            "success": True,
            "message": "用户状态更新成功",
            "data": None
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"更新用户状态失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新用户状态失败: user_id={user_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"更新用户状态失败: {str(e)}")


@router.post("/{user_id}/reset-password", summary="重置用户密码")
async def reset_user_password(
    user_id: int,
    reset_data: PasswordResetRequest,
    current_user: User = Depends(require_admin)
):
    """重置用户密码
    
    只有管理员及以上权限可以重置用户密码。
    """
    try:
        logger.info(f"用户 {current_user.username} 重置用户密码: id={user_id}")
        
        success = await user_management_service.reset_user_password(user_id, reset_data.new_password)
        
        if not success:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return {
            "success": True,
            "message": "用户密码重置成功",
            "data": None
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"重置用户密码失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"重置用户密码失败: user_id={user_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"重置用户密码失败: {str(e)}")


@router.post("/{user_id}/change-password", summary="修改用户密码")
async def change_user_password(
    user_id: int,
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user)
):
    """修改用户密码
    
    用户可以修改自己的密码，管理员可以修改任何用户的密码。
    """
    try:
        # 检查权限：用户只能修改自己的密码，除非是管理员
        if user_id != current_user.id and not current_user.is_superuser:
            # 检查是否为管理员
            user_roles = await current_user.roles.all()
            is_admin = any(role.role_key == 'admin' for role in user_roles)
            if not is_admin:
                raise HTTPException(status_code=403, detail="权限不足")
        
        logger.info(f"用户 {current_user.username} 修改用户密码: id={user_id}")
        
        success = await user_management_service.change_user_password(
            user_id, password_data.old_password, password_data.new_password
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return {
            "success": True,
            "message": "用户密码修改成功",
            "data": None
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"修改用户密码失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"修改用户密码失败: user_id={user_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"修改用户密码失败: {str(e)}")


@router.post("/batch-update-status", summary="批量更新用户状态")
async def batch_update_user_status(
    batch_data: BatchStatusUpdateRequest,
    current_user: User = Depends(require_admin)
):
    """批量更新用户状态
    
    可以批量启用或禁用用户，只有管理员及以上权限可以操作。
    """
    try:
        if not batch_data.user_ids:
            raise HTTPException(status_code=400, detail="用户ID列表不能为空")
        
        logger.info(f"用户 {current_user.username} 批量更新用户状态: ids={batch_data.user_ids}, status={batch_data.status}")
        
        updated_count = await user_management_service.batch_update_user_status(
            batch_data.user_ids, batch_data.status
        )
        
        return {
            "success": True,
            "message": f"批量更新用户状态成功，共更新 {updated_count} 个用户",
            "data": {
                "updated_count": updated_count,
                "total_requested": len(batch_data.user_ids)
            }
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"批量更新用户状态失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"批量更新用户状态失败: error={e}")
        raise HTTPException(status_code=500, detail=f"批量更新用户状态失败: {str(e)}")


@router.post("/batch-reset-password", summary="批量重置用户密码")
async def batch_reset_user_password(
    batch_data: BatchPasswordResetRequest,
    current_user: User = Depends(require_admin)
):
    """批量重置用户密码
    
    只有管理员及以上权限可以批量重置密码。
    """
    try:
        if not batch_data.user_ids:
            raise HTTPException(status_code=400, detail="用户ID列表不能为空")
        
        logger.info(f"用户 {current_user.username} 批量重置用户密码: ids={batch_data.user_ids}")
        
        updated_count = await user_management_service.batch_reset_user_password(batch_data.user_ids)
        
        return {
            "success": True,
            "message": f"批量重置用户密码成功，共重置 {updated_count} 个用户密码",
            "data": {
                "updated_count": updated_count,
                "total_requested": len(batch_data.user_ids)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量重置用户密码失败: error={e}")
        raise HTTPException(status_code=500, detail=f"批量重置用户密码失败: {str(e)}")


@router.get("/{user_id}/roles", summary="获取用户角色")
async def get_user_roles(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取指定用户的角色列表"""
    try:
        roles = await user_management_service.get_user_roles(user_id)
        
        return {
            "success": True,
            "message": "获取用户角色成功",
            "data": {
                "user_id": user_id,
                "roles": roles,
                "total": len(roles)
            }
        }
    
    except Exception as e:
        logger.error(f"获取用户角色失败: user_id={user_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"获取用户角色失败: {str(e)}")


@router.post("/{user_id}/assign-roles", summary="为用户分配角色")
async def assign_roles_to_user(
    user_id: int,
    role_data: UserRoleAssignRequest,
    current_user: User = Depends(require_admin)
):
    """为用户分配角色
    
    只有管理员及以上权限可以分配角色。
    """
    try:
        logger.info(f"用户 {current_user.username} 为用户分配角色: user_id={user_id}, role_count={len(role_data.role_ids)}")
        
        success = await user_management_service.assign_roles_to_user(user_id, role_data.role_ids)
        
        if not success:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return {
            "success": True,
            "message": "角色分配成功",
            "data": {
                "user_id": user_id,
                "assigned_roles": len(role_data.role_ids)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分配角色失败: user_id={user_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"分配角色失败: {str(e)}")


@router.get("/statistics", summary="获取用户统计信息")
async def get_user_statistics(
    current_user: User = Depends(get_current_user)
):
    """获取用户统计信息
    
    包括总数、状态分布、用户类型分布等。
    """
    try:
        stats = await user_management_service.get_user_statistics()
        
        return {
            "success": True,
            "message": "获取用户统计信息成功",
            "data": stats
        }
    
    except Exception as e:
        logger.error(f"获取用户统计信息失败: error={e}")
        raise HTTPException(status_code=500, detail=f"获取用户统计信息失败: {str(e)}")


@router.get("/profile", summary="获取当前用户信息")
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """获取当前登录用户的详细信息"""
    try:
        # 获取用户角色
        roles = await user_management_service.get_user_roles(current_user.id)
        
        # 获取部门信息
        dept_info = None
        if current_user.dept:
            dept_info = {
                "id": current_user.dept.id,
                "dept_name": current_user.dept.dept_name
            }
        
        user_data = {
            "id": current_user.id,
            "username": current_user.username,
            "nick_name": current_user.nick_name,
            "email": current_user.email,
            "phone_number": current_user.phone_number,
            "sex": current_user.sex,
            "avatar": current_user.avatar,
            "user_type": current_user.user_type,
            "status": current_user.status,
            "remark": current_user.remark,
            "login_ip": current_user.login_ip,
            "login_date": current_user.login_date.isoformat() if current_user.login_date else None,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None,
            "is_superuser": current_user.is_superuser,
            "is_active": current_user.is_active,
            "roles": roles,
            "dept": dept_info
        }
        
        return {
            "success": True,
            "message": "获取用户信息成功",
            "data": user_data
        }
    
    except Exception as e:
        logger.error(f"获取当前用户信息失败: error={e}")
        raise HTTPException(status_code=500, detail=f"获取用户信息失败: {str(e)}")


# 健康检查端点
@router.get("/health", summary="用户管理服务健康检查")
async def health_check():
    """用户管理服务健康检查"""
    try:
        # 简单的健康检查：获取用户统计信息
        stats = await user_management_service.get_user_statistics()
        
        return {
            "success": True,
            "message": "用户管理服务运行正常",
            "data": {
                "status": "healthy",
                "total_users": stats.get("total_users", 0),
                "active_users": stats.get("active_users", 0),
                "timestamp": stats.get("timestamp")
            }
        }
    
    except Exception as e:
        logger.error(f"用户管理服务健康检查失败: error={e}")
        return {
            "success": False,
            "message": "用户管理服务异常",
            "data": {
                "status": "unhealthy",
                "error": str(e)
            }
        }