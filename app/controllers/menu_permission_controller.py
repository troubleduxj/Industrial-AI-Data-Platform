#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
菜单权限管理API控制器
提供菜单权限管理的REST API接口
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field

from app.services.menu_permission_service import menu_permission_service
from app.core.auth_dependencies import get_current_user, require_superuser, require_admin
from app.models.admin import User
from app.schemas.menus import MenuType
from app.core.unified_logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v2/admin/menus", tags=["菜单权限管理"])


# Pydantic模型
class MenuCreateRequest(BaseModel):
    """菜单创建请求模型"""
    name: str = Field(..., description="菜单名称", max_length=20)
    path: Optional[str] = Field(None, description="路由路径", max_length=200)
    component: Optional[str] = Field(None, description="组件路径", max_length=255)
    menu_type: Optional[str] = Field("M", description="菜单类型")
    icon: Optional[str] = Field(None, description="菜单图标", max_length=100)
    order_num: Optional[int] = Field(0, description="显示顺序")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    perms: Optional[str] = Field(None, description="权限标识", max_length=100)
    visible: Optional[bool] = Field(True, description="显示状态")
    status: Optional[bool] = Field(True, description="菜单状态")
    is_frame: Optional[bool] = Field(False, description="是否外链")
    is_cache: Optional[bool] = Field(True, description="是否缓存")
    query: Optional[str] = Field(None, description="路由参数", max_length=255)


class MenuUpdateRequest(BaseModel):
    """菜单更新请求模型"""
    name: Optional[str] = Field(None, description="菜单名称", max_length=20)
    path: Optional[str] = Field(None, description="路由路径", max_length=200)
    component: Optional[str] = Field(None, description="组件路径", max_length=255)
    menu_type: Optional[str] = Field(None, description="菜单类型")
    icon: Optional[str] = Field(None, description="菜单图标", max_length=100)
    order_num: Optional[int] = Field(None, description="显示顺序")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    perms: Optional[str] = Field(None, description="权限标识", max_length=100)
    visible: Optional[bool] = Field(None, description="显示状态")
    status: Optional[bool] = Field(None, description="菜单状态")
    is_frame: Optional[bool] = Field(None, description="是否外链")
    is_cache: Optional[bool] = Field(None, description="是否缓存")
    query: Optional[str] = Field(None, description="路由参数", max_length=255)


class MenuStatusUpdateRequest(BaseModel):
    """菜单状态更新请求模型"""
    status: bool = Field(..., description="菜单状态")


class MenuVisibilityUpdateRequest(BaseModel):
    """菜单可见性更新请求模型"""
    visible: bool = Field(..., description="菜单可见性")


class BatchStatusUpdateRequest(BaseModel):
    """批量状态更新请求模型"""
    menu_ids: List[int] = Field(..., description="菜单ID列表")
    status: bool = Field(..., description="新状态")


class MenuResponse(BaseModel):
    """菜单响应模型"""
    id: int
    name: str
    path: Optional[str] = None
    component: Optional[str] = None
    menu_type: Optional[str] = None
    icon: Optional[str] = None
    order_num: int = 0
    parent_id: Optional[int] = None
    perms: Optional[str] = None
    visible: bool = True
    status: bool = True
    is_frame: bool = False
    is_cache: bool = True
    query: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.get("/user-menus", summary="获取当前用户菜单")
async def get_current_user_menus(
    include_hidden: bool = Query(False, description="是否包含隐藏菜单"),
    tree_format: bool = Query(True, description="是否返回树形结构"),
    current_user: User = Depends(get_current_user)
):
    """获取当前登录用户的菜单列表
    
    根据用户权限动态生成菜单，支持树形结构和列表格式。
    """
    try:
        if tree_format:
            menus = await menu_permission_service.get_user_menu_tree(
                current_user.id, include_hidden
            )
        else:
            menus = await menu_permission_service.get_user_menus(
                current_user.id, include_hidden
            )
        
        return {
            "success": True,
            "message": "获取用户菜单成功",
            "data": {
                "menus": menus,
                "total": len(menus),
                "user_id": current_user.id,
                "tree_format": tree_format
            }
        }
    
    except Exception as e:
        logger.error(f"获取用户菜单失败: user_id={current_user.id}, error={e}")
        raise HTTPException(status_code=500, detail=f"获取用户菜单失败: {str(e)}")


@router.get("/user-menus/{user_id}", summary="获取指定用户菜单")
async def get_user_menus(
    user_id: int,
    include_hidden: bool = Query(False, description="是否包含隐藏菜单"),
    tree_format: bool = Query(True, description="是否返回树形结构"),
    current_user: User = Depends(require_admin)
):
    """获取指定用户的菜单列表
    
    只有管理员及以上权限可以查看其他用户的菜单。
    """
    try:
        logger.info(f"用户 {current_user.username} 查看用户菜单: user_id={user_id}")
        
        if tree_format:
            menus = await menu_permission_service.get_user_menu_tree(
                user_id, include_hidden
            )
        else:
            menus = await menu_permission_service.get_user_menus(
                user_id, include_hidden
            )
        
        return {
            "success": True,
            "message": "获取用户菜单成功",
            "data": {
                "menus": menus,
                "total": len(menus),
                "user_id": user_id,
                "tree_format": tree_format
            }
        }
    
    except Exception as e:
        logger.error(f"获取用户菜单失败: user_id={user_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"获取用户菜单失败: {str(e)}")


@router.get("/permissions", summary="获取当前用户菜单权限")
async def get_current_user_menu_permissions(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的菜单权限标识列表"""
    try:
        permissions = await menu_permission_service.get_menu_permissions(current_user.id)
        
        return {
            "success": True,
            "message": "获取菜单权限成功",
            "data": {
                "permissions": permissions,
                "total": len(permissions),
                "user_id": current_user.id
            }
        }
    
    except Exception as e:
        logger.error(f"获取菜单权限失败: user_id={current_user.id}, error={e}")
        raise HTTPException(status_code=500, detail=f"获取菜单权限失败: {str(e)}")


@router.get("/check-permission", summary="检查菜单权限")
async def check_menu_permission(
    permission: str = Query(..., description="权限标识"),
    current_user: User = Depends(get_current_user)
):
    """检查当前用户是否有特定菜单权限"""
    try:
        has_permission = await menu_permission_service.check_menu_permission(
            current_user.id, permission
        )
        
        return {
            "success": True,
            "message": "权限检查完成",
            "data": {
                "has_permission": has_permission,
                "permission": permission,
                "user_id": current_user.id
            }
        }
    
    except Exception as e:
        logger.error(f"检查菜单权限失败: user_id={current_user.id}, permission={permission}, error={e}")
        raise HTTPException(status_code=500, detail=f"检查菜单权限失败: {str(e)}")


@router.post("/", summary="创建菜单")
async def create_menu(
    menu_data: MenuCreateRequest,
    current_user: User = Depends(require_admin)
):
    """创建新菜单
    
    只有管理员及以上权限可以创建菜单。
    """
    try:
        logger.info(f"用户 {current_user.username} 创建菜单: {menu_data.name}")
        
        menu = await menu_permission_service.create_menu(menu_data.dict())
        
        return {
            "success": True,
            "message": "菜单创建成功",
            "data": {
                "id": menu.id,
                "name": menu.name,
                "path": menu.path,
                "menu_type": menu.menu_type.value if menu.menu_type else None
            }
        }
    
    except ValueError as e:
        logger.warning(f"创建菜单失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建菜单失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建菜单失败: {str(e)}")


@router.get("/", summary="获取菜单列表")
async def get_menus(
    menu_type: Optional[str] = Query(None, description="菜单类型过滤"),
    status: Optional[bool] = Query(None, description="状态过滤"),
    visible: Optional[bool] = Query(None, description="可见性过滤"),
    parent_id: Optional[int] = Query(None, description="父菜单ID过滤"),
    tree_format: bool = Query(False, description="是否返回树形结构"),
    current_user: User = Depends(get_current_user)
):
    """获取菜单列表
    
    支持按菜单类型、状态、可见性等条件过滤，支持树形结构。
    """
    try:
        if tree_format:
            menus = await menu_permission_service.get_menu_tree(
                menu_type=menu_type, status=status, visible=visible
            )
        else:
            menus = await menu_permission_service.get_all_menus(
                menu_type=menu_type, status=status, visible=visible, parent_id=parent_id
            )
        
        return {
            "success": True,
            "message": "获取菜单列表成功",
            "data": {
                "menus": menus,
                "total": len(menus),
                "tree_format": tree_format
            }
        }
    
    except Exception as e:
        logger.error(f"获取菜单列表失败: error={e}")
        raise HTTPException(status_code=500, detail=f"获取菜单列表失败: {str(e)}")


@router.get("/{menu_id}", summary="获取菜单详情")
async def get_menu(
    menu_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取指定菜单的详细信息"""
    try:
        menu = await menu_permission_service.get_menu_by_id(menu_id)
        
        if not menu:
            raise HTTPException(status_code=404, detail="菜单不存在")
        
        return {
            "success": True,
            "message": "获取菜单详情成功",
            "data": menu
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取菜单详情失败: menu_id={menu_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"获取菜单详情失败: {str(e)}")


@router.put("/{menu_id}", summary="更新菜单")
async def update_menu(
    menu_id: int,
    menu_data: MenuUpdateRequest,
    current_user: User = Depends(require_admin)
):
    """更新菜单信息
    
    只有管理员及以上权限可以更新菜单。
    """
    try:
        logger.info(f"用户 {current_user.username} 更新菜单: id={menu_id}")
        
        # 过滤掉None值
        update_data = {k: v for k, v in menu_data.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="没有提供更新数据")
        
        menu = await menu_permission_service.update_menu(menu_id, update_data)
        
        if not menu:
            raise HTTPException(status_code=404, detail="菜单不存在")
        
        return {
            "success": True,
            "message": "菜单更新成功",
            "data": {
                "id": menu.id,
                "name": menu.name,
                "status": menu.status
            }
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"更新菜单失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新菜单失败: menu_id={menu_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"更新菜单失败: {str(e)}")


@router.delete("/{menu_id}", summary="删除菜单")
async def delete_menu(
    menu_id: int,
    current_user: User = Depends(require_admin)
):
    """删除菜单
    
    执行软删除，只有管理员及以上权限可以删除菜单。
    """
    try:
        logger.info(f"用户 {current_user.username} 删除菜单: id={menu_id}")
        
        success = await menu_permission_service.delete_menu(menu_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="菜单不存在")
        
        return {
            "success": True,
            "message": "菜单删除成功",
            "data": None
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"删除菜单失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"删除菜单失败: menu_id={menu_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"删除菜单失败: {str(e)}")


@router.patch("/{menu_id}/status", summary="更新菜单状态")
async def update_menu_status(
    menu_id: int,
    status_data: MenuStatusUpdateRequest,
    current_user: User = Depends(require_admin)
):
    """更新菜单状态
    
    可以启用或禁用菜单，只有管理员及以上权限可以操作。
    """
    try:
        logger.info(f"用户 {current_user.username} 更新菜单状态: id={menu_id}, status={status_data.status}")
        
        success = await menu_permission_service.update_menu_status(menu_id, status_data.status)
        
        if not success:
            raise HTTPException(status_code=404, detail="菜单不存在")
        
        return {
            "success": True,
            "message": "菜单状态更新成功",
            "data": None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新菜单状态失败: menu_id={menu_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"更新菜单状态失败: {str(e)}")


@router.patch("/{menu_id}/visibility", summary="更新菜单可见性")
async def update_menu_visibility(
    menu_id: int,
    visibility_data: MenuVisibilityUpdateRequest,
    current_user: User = Depends(require_admin)
):
    """更新菜单可见性
    
    可以显示或隐藏菜单，只有管理员及以上权限可以操作。
    """
    try:
        logger.info(f"用户 {current_user.username} 更新菜单可见性: id={menu_id}, visible={visibility_data.visible}")
        
        success = await menu_permission_service.update_menu_visibility(menu_id, visibility_data.visible)
        
        if not success:
            raise HTTPException(status_code=404, detail="菜单不存在")
        
        return {
            "success": True,
            "message": "菜单可见性更新成功",
            "data": None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新菜单可见性失败: menu_id={menu_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"更新菜单可见性失败: {str(e)}")


@router.post("/batch-update-status", summary="批量更新菜单状态")
async def batch_update_menu_status(
    batch_data: BatchStatusUpdateRequest,
    current_user: User = Depends(require_admin)
):
    """批量更新菜单状态
    
    可以批量启用或禁用菜单，只有管理员及以上权限可以操作。
    """
    try:
        if not batch_data.menu_ids:
            raise HTTPException(status_code=400, detail="菜单ID列表不能为空")
        
        logger.info(f"用户 {current_user.username} 批量更新菜单状态: ids={batch_data.menu_ids}, status={batch_data.status}")
        
        updated_count = await menu_permission_service.batch_update_menu_status(
            batch_data.menu_ids, batch_data.status
        )
        
        return {
            "success": True,
            "message": f"批量更新菜单状态成功，共更新 {updated_count} 个菜单",
            "data": {
                "updated_count": updated_count,
                "total_requested": len(batch_data.menu_ids)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量更新菜单状态失败: error={e}")
        raise HTTPException(status_code=500, detail=f"批量更新菜单状态失败: {str(e)}")


@router.post("/refresh-cache/{user_id}", summary="刷新用户菜单缓存")
async def refresh_user_menu_cache(
    user_id: int,
    current_user: User = Depends(require_admin)
):
    """刷新指定用户的菜单缓存
    
    只有管理员及以上权限可以刷新缓存。
    """
    try:
        logger.info(f"用户 {current_user.username} 刷新用户菜单缓存: user_id={user_id}")
        
        success = await menu_permission_service.refresh_user_menu_cache(user_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="刷新缓存失败")
        
        return {
            "success": True,
            "message": "用户菜单缓存刷新成功",
            "data": {
                "user_id": user_id
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新用户菜单缓存失败: user_id={user_id}, error={e}")
        raise HTTPException(status_code=500, detail=f"刷新用户菜单缓存失败: {str(e)}")


@router.get("/statistics", summary="获取菜单统计信息")
async def get_menu_statistics(
    current_user: User = Depends(get_current_user)
):
    """获取菜单统计信息
    
    包括总数、状态分布、类型分布等。
    """
    try:
        stats = await menu_permission_service.get_menu_statistics()
        
        return {
            "success": True,
            "message": "获取菜单统计信息成功",
            "data": stats
        }
    
    except Exception as e:
        logger.error(f"获取菜单统计信息失败: error={e}")
        raise HTTPException(status_code=500, detail=f"获取菜单统计信息失败: {str(e)}")


# 健康检查端点
@router.get("/health", summary="菜单权限服务健康检查")
async def health_check():
    """菜单权限服务健康检查"""
    try:
        # 简单的健康检查：获取菜单统计信息
        stats = await menu_permission_service.get_menu_statistics()
        
        return {
            "success": True,
            "message": "菜单权限服务运行正常",
            "data": {
                "status": "healthy",
                "total_menus": stats.get("total_menus", 0),
                "active_menus": stats.get("active_menus", 0),
                "timestamp": stats.get("timestamp")
            }
        }
    
    except Exception as e:
        logger.error(f"菜单权限服务健康检查失败: error={e}")
        return {
            "success": False,
            "message": "菜单权限服务异常",
            "data": {
                "status": "unhealthy",
                "error": str(e)
            }
        }