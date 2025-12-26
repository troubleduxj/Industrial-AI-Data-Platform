#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色管理API控制器
提供角色管理的REST API接口
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field

from app.services.role_management_service import role_management_service
from app.core.auth_dependencies import get_current_user, require_superuser, require_admin
from app.models.admin import User
from app.core.unified_logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v2/admin/roles", tags=["角色管理"])


# Pydantic模型
class RoleCreateRequest(BaseModel):
    """角色创建请求模型"""
    role_name: str = Field(..., description="角色名称", max_length=20)
    role_key: Optional[str] = Field(None, description="角色权限字符串", max_length=100)
    role_sort: Optional[int] = Field(0, description="显示顺序")
    data_scope: Optional[str] = Field("1", description="数据权限范围")
    menu_check_strictly: Optional[bool] = Field(True, description="菜单树选择关联显示")
    dept_check_strictly: Optional[bool] = Field(True, description="部门树选择关联显示")
    status: Optional[str] = Field("0", description="角色状态", regex="^[01]$")
    remark: Optional[str] = Field(None, description="备注")
    parent_id: Optional[int] = Field(None, description="父角色ID")
    menu_ids: Optional[List[int]] = Field([], description="菜单权限ID列表")
    api_ids: Optional[List[int]] = Field([], description="API权限ID列表")


class RoleUpdateRequest(BaseModel):
    """角色更新请求模型"""
    role_name: Optional[str] = Field(None, description="角色名称", max_length=20)
    role_key: Optional[str] = Field(None, description="角色权限字符串", max_length=100)
    role_sort: Optional[int] = Field(None, description="显示顺序")
    data_scope: Optional[str] = Field(None, description="数据权限范围")
    menu_check_strictly: Optional[bool] = Field(None, description="菜单树选择关联显示")
    dept_check_strictly: Optional[bool] = Field(None, description="部门树选择关联显示")
    status: Optional[str] = Field(None, description="角色状态", regex="^[01]$")
    remark: Optional[str] = Field(None, description="备注")
    parent_id: Optional[int] = Field(None, description="父角色ID")
    menu_ids: Optional[List[int]] = Field(None, description="菜单权限ID列表")
    api_ids: Optional[List[int]] = Field(None, description="API权限ID列表")


class RoleStatusUpdateRequest(BaseModel):
    """角色状态更新请求模型"""
    status: str = Field(..., description="角色状态", regex="^[01]$")


class BatchStatusUpdateRequest(BaseModel):
    """批量状态更新请求模型"""
    role_ids: List[int] = Field(..., description="角色ID列表")
    status: str = Field(..., description="新状态", regex="^[01]$")


class RolePermissionAssignRequest(BaseModel):
    """角色权限分配请求模型"""
    menu_ids: Optional[List[int]] = Field(None, description="菜单权限ID列表")
    api_ids: Optional[List[int]] = Field(None, description="API权限ID列表")


class RoleResponse(BaseModel):
    """角色响应模型"""
    id: int
    role_name: str
    role_key: Optional[str] = None
    role_sort: Optional[int] = None
    data_scope: Optional[str] = None
    menu_check_strictly: bool = True
    dept_check_strictly: bool = True
    status: str = "0"
    remark: Optional[str] = None
    parent_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("/", summary="创建角色")
async def create_role(
    role_data: RoleCreateRequest,
    current_user: User = Depends(require_admin)
):
    """创建新角色
    
    只有管理员及以上权限可以创建角色。
    """
    try:
        logger.info(f"用户 {current_user.username} 创建角色: {role_data.role_name}")
        
        role = await role_management_service.create_role(role_data.dict())
        
        return {
            "success": True,
            "message": "角色创建成功",
            "data": {
                "id": role.id,
                "role_name": role.role_name,
                "role_key": role.role_key,
                "status": role.status
            }
        }
    
    except ValueError as e:
        logger.warning(f"创建角色失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建角色失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建角色失败: {str(e)}")


@router.get("/", summary="获取角色列表")
async def get_roles(
    status: Optional[str] = Query(None, description="状态过滤"),
    parent_id: Optional[int] = Query(None, description="父角色ID过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(get_current_user)
):
    """获取角色列表
    
    支持按状态、父角色等条件过滤，支持分页。
    """
    try:
        result = await role_management_service.get_roles(
            status=status,
            parent_id=parent_id,
            page=page,
            page_size=page_size
        )
        
        return {
            "success": True,
            "message": "获取角色列表成功",
            "data": result
        }
    
    except Exception as e:
        logger.error(f"获取角色列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取角色列表失败: {str(e)}")


@router.get("/{role_id}", summary="获取角色详情")
async def get_role(
    role_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取指定角色的详细信息"""
    try:
        role = await role_management_service.get_role(role_id)
        
        if not role:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        # 获取角色的菜单和API权限
        menus = await role_management_service.get_role_menus(role_id)
        apis = await role_management_service.get_role_apis(role_id)
        
        role_data = {
            "id": role.id,
            "role_name": role.role_name,
            "role_key": role.role_key,
            "role_sort": role.role_sort,
            "data_scope": role.data_scope,
            "menu_check_strictly": role.menu_check_strictly,
            "dept_check_strictly": role.dept_check_strictly,
            "status": role.status,
            "remark": role.remark,
            "parent_id": role.parent_id,
            "created_at": role.created_at.isoformat() if role.created_at else None,
            "updated_at": role.updated_at.isoformat() if role.updated_at else None,
            "menus": menus,
            "apis": apis
        }
        
        return {
            "success": True,
            "message": "获取角色详情成功",
            "data": role_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取角色详情失败: role_id={role_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"获取角色详情失败: {str(e)}")


@router.put("/{role_id}", summary="更新角色")
async def update_role(
    role_id: int,
    role_data: RoleUpdateRequest,
    current_user: User = Depends(require_admin)
):
    """更新角色信息
    
    只有管理员及以上权限可以更新角色。
    """
    try:
        logger.info(f"用户 {current_user.username} 更新角色: id={role_id}")
        
        # 过滤掉None值
        update_data = {k: v for k, v in role_data.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="没有提供更新数据")
        
        role = await role_management_service.update_role(role_id, update_data)
        
        if not role:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        return {
            "success": True,
            "message": "角色更新成功",
            "data": {
                "id": role.id,
                "role_name": role.role_name,
                "status": role.status
            }
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"更新角色失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新角色失败: role_id={role_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"更新角色失败: {str(e)}")


@router.delete("/{role_id}", summary="删除角色")
async def delete_role(
    role_id: int,
    current_user: User = Depends(require_admin)
):
    """删除角色
    
    执行软删除，只有管理员及以上权限可以删除角色。
    """
    try:
        logger.info(f"用户 {current_user.username} 删除角色: id={role_id}")
        
        success = await role_management_service.delete_role(role_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        return {
            "success": True,
            "message": "角色删除成功",
            "data": None
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"删除角色失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"删除角色失败: role_id={role_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"删除角色失败: {str(e)}")


@router.patch("/{role_id}/status", summary="更新角色状态")
async def update_role_status(
    role_id: int,
    status_data: RoleStatusUpdateRequest,
    current_user: User = Depends(require_admin)
):
    """更新角色状态
    
    可以启用或禁用角色，只有管理员及以上权限可以操作。
    """
    try:
        logger.info(f"用户 {current_user.username} 更新角色状态: id={role_id}, status={status_data.status}")
        
        success = await role_management_service.update_role_status(role_id, status_data.status)
        
        if not success:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        return {
            "success": True,
            "message": "角色状态更新成功",
            "data": None
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"更新角色状态失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新角色状态失败: role_id={role_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"更新角色状态失败: {str(e)}")


@router.post("/batch-update-status", summary="批量更新角色状态")
async def batch_update_role_status(
    batch_data: BatchStatusUpdateRequest,
    current_user: User = Depends(require_admin)
):
    """批量更新角色状态
    
    可以批量启用或禁用角色，只有管理员及以上权限可以操作。
    """
    try:
        if not batch_data.role_ids:
            raise HTTPException(status_code=400, detail="角色ID列表不能为空")
        
        logger.info(f"用户 {current_user.username} 批量更新角色状态: ids={batch_data.role_ids}, status={batch_data.status}")
        
        updated_count = await role_management_service.batch_update_role_status(
            batch_data.role_ids, batch_data.status
        )
        
        return {
            "success": True,
            "message": f"批量更新角色状态成功，共更新 {updated_count} 个角色",
            "data": {
                "updated_count": updated_count,
                "total_requested": len(batch_data.role_ids)
            }
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"批量更新角色状态失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"批量更新角色状态失败: error={e}")
        raise HTTPException(status_code=500, detail=f"批量更新角色状态失败: {str(e)}")


@router.get("/{role_id}/menus", summary="获取角色菜单权限")
async def get_role_menus(
    role_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取指定角色的菜单权限列表"""
    try:
        menus = await role_management_service.get_role_menus(role_id)
        
        return {
            "success": True,
            "message": "获取角色菜单权限成功",
            "data": {
                "role_id": role_id,
                "menus": menus,
                "total": len(menus)
            }
        }
    
    except Exception as e:
        logger.error(f"获取角色菜单权限失败: role_id={role_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"获取角色菜单权限失败: {str(e)}")


@router.get("/{role_id}/apis", summary="获取角色API权限")
async def get_role_apis(
    role_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取指定角色的API权限列表"""
    try:
        apis = await role_management_service.get_role_apis(role_id)
        
        return {
            "success": True,
            "message": "获取角色API权限成功",
            "data": {
                "role_id": role_id,
                "apis": apis,
                "total": len(apis)
            }
        }
    
    except Exception as e:
        logger.error(f"获取角色API权限失败: role_id={role_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"获取角色API权限失败: {str(e)}")


@router.post("/{role_id}/assign-menus", summary="为角色分配菜单权限")
async def assign_menus_to_role(
    role_id: int,
    menu_ids: List[int] = Body(..., description="菜单ID列表"),
    current_user: User = Depends(require_admin)
):
    """为角色分配菜单权限
    
    只有管理员及以上权限可以分配权限。
    """
    try:
        logger.info(f"用户 {current_user.username} 为角色分配菜单权限: role_id={role_id}, menu_count={len(menu_ids)}")
        
        success = await role_management_service.assign_menus_to_role(role_id, menu_ids)
        
        if not success:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        return {
            "success": True,
            "message": "菜单权限分配成功",
            "data": {
                "role_id": role_id,
                "assigned_menus": len(menu_ids)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分配菜单权限失败: role_id={role_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"分配菜单权限失败: {str(e)}")


@router.post("/{role_id}/assign-apis", summary="为角色分配API权限")
async def assign_apis_to_role(
    role_id: int,
    api_ids: List[int] = Body(..., description="API ID列表"),
    current_user: User = Depends(require_admin)
):
    """为角色分配API权限
    
    只有管理员及以上权限可以分配权限。
    """
    try:
        logger.info(f"用户 {current_user.username} 为角色分配API权限: role_id={role_id}, api_count={len(api_ids)}")
        
        success = await role_management_service.assign_apis_to_role(role_id, api_ids)
        
        if not success:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        return {
            "success": True,
            "message": "API权限分配成功",
            "data": {
                "role_id": role_id,
                "assigned_apis": len(api_ids)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分配API权限失败: role_id={role_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"分配API权限失败: {str(e)}")


@router.get("/{role_id}/users", summary="获取角色用户列表")
async def get_role_users(
    role_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取指定角色下的用户列表"""
    try:
        users = await role_management_service.get_role_users(role_id)
        
        return {
            "success": True,
            "message": "获取角色用户列表成功",
            "data": {
                "role_id": role_id,
                "users": users,
                "total": len(users)
            }
        }
    
    except Exception as e:
        logger.error(f"获取角色用户列表失败: role_id={role_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"获取角色用户列表失败: {str(e)}")


@router.get("/tree", summary="获取角色树结构")
async def get_role_tree(
    current_user: User = Depends(get_current_user)
):
    """获取角色的树形结构
    
    用于前端树形选择器等组件。
    """
    try:
        tree = await role_management_service.get_role_tree()
        
        return {
            "success": True,
            "message": "获取角色树结构成功",
            "data": tree
        }
    
    except Exception as e:
        logger.error(f"获取角色树结构失败: error={e}")
        raise HTTPException(status_code=500, detail=f"获取角色树结构失败: {str(e)}")


@router.get("/statistics", summary="获取角色统计信息")
async def get_role_statistics(
    current_user: User = Depends(get_current_user)
):
    """获取角色统计信息
    
    包括总数、状态分布、数据权限分布等。
    """
    try:
        stats = await role_management_service.get_role_statistics()
        
        return {
            "success": True,
            "message": "获取角色统计信息成功",
            "data": stats
        }
    
    except Exception as e:
        logger.error(f"获取角色统计信息失败: error={e}")
        raise HTTPException(status_code=500, detail=f"获取角色统计信息失败: {str(e)}")


# 健康检查端点
@router.get("/health", summary="角色管理服务健康检查")
async def health_check():
    """角色管理服务健康检查"""
    try:
        # 简单的健康检查：获取角色统计信息
        stats = await role_management_service.get_role_statistics()
        
        return {
            "success": True,
            "message": "角色管理服务运行正常",
            "data": {
                "status": "healthy",
                "total_roles": stats.get("total_roles", 0),
                "active_roles": stats.get("active_roles", 0),
                "timestamp": stats.get("timestamp")
            }
        }
    
    except Exception as e:
        logger.error(f"角色管理服务健康检查失败: error={e}")
        return {
            "success": False,
            "message": "角色管理服务异常",
            "data": {
                "status": "unhealthy",
                "error": str(e)
            }
        }