#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知管理 API v2
提供通知的CRUD操作（管理员）
"""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel, Field

from app.models.notification import Notification, UserNotification
from app.core.response_formatter_v2 import create_formatter
from app.core.pagination import get_pagination_params, create_pagination_response
from app.log import logger

router = APIRouter(tags=["通知管理"])


# =====================================================
# Pydantic 模型
# =====================================================

class NotificationCreate(BaseModel):
    """创建通知"""
    title: str = Field(..., description="标题")
    content: Optional[str] = Field(None, description="内容")
    notification_type: str = Field("announcement", description="类型")
    level: str = Field("info", description="级别")
    scope: str = Field("all", description="范围")
    target_roles: Optional[List[int]] = Field(None, description="目标角色")
    target_users: Optional[List[int]] = Field(None, description="目标用户")
    link_url: Optional[str] = Field(None, description="跳转链接")
    is_published: bool = Field(True, description="是否发布")
    expire_time: Optional[datetime] = Field(None, description="过期时间")


class NotificationUpdate(BaseModel):
    """更新通知"""
    title: Optional[str] = None
    content: Optional[str] = None
    notification_type: Optional[str] = None
    level: Optional[str] = None
    scope: Optional[str] = None
    target_roles: Optional[List[int]] = None
    target_users: Optional[List[int]] = None
    link_url: Optional[str] = None
    expire_time: Optional[datetime] = None


# =====================================================
# API 路由
# =====================================================

@router.get("", summary="获取通知列表")
async def get_notifications(
    notification_type: Optional[str] = Query(None, description="通知类型"),
    is_published: Optional[bool] = Query(None, description="是否发布"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    pagination: dict = Depends(get_pagination_params)
):
    """获取通知列表（管理员）"""
    try:
        query = Notification.all()
        
        if notification_type:
            query = query.filter(notification_type=notification_type)
        if is_published is not None:
            query = query.filter(is_published=is_published)
        if search:
            query = query.filter(title__icontains=search)
        
        total = await query.count()
        notifications = await query.offset(pagination["offset"]).limit(pagination["limit"]).order_by("-created_at")
        
        items = []
        for n in notifications:
            items.append({
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "notification_type": n.notification_type,
                "level": n.level,
                "scope": n.scope,
                "target_roles": n.target_roles,
                "target_users": n.target_users,
                "link_url": n.link_url,
                "is_published": n.is_published,
                "publish_time": n.publish_time.isoformat() if n.publish_time else None,
                "expire_time": n.expire_time.isoformat() if n.expire_time else None,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            })
        
        paginated = create_pagination_response(
            data=items,
            total=total,
            page=pagination["page"],
            page_size=pagination["page_size"]
        )
        
        formatter = create_formatter()
        return formatter.success(data=paginated, message=f"获取通知列表成功，共{total}条")
        
    except Exception as e:
        logger.error(f"获取通知列表失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取通知列表失败")


@router.get("/{notification_id}", summary="获取通知详情")
async def get_notification(notification_id: int):
    """获取通知详情"""
    try:
        n = await Notification.get_or_none(id=notification_id)
        if not n:
            formatter = create_formatter()
            return formatter.error(message="通知不存在", code=404)
        
        data = {
            "id": n.id,
            "title": n.title,
            "content": n.content,
            "notification_type": n.notification_type,
            "level": n.level,
            "scope": n.scope,
            "target_roles": n.target_roles,
            "target_users": n.target_users,
            "link_url": n.link_url,
            "is_published": n.is_published,
            "publish_time": n.publish_time.isoformat() if n.publish_time else None,
            "expire_time": n.expire_time.isoformat() if n.expire_time else None,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        
        formatter = create_formatter()
        return formatter.success(data=data, message="获取通知详情成功")
        
    except Exception as e:
        logger.error(f"获取通知详情失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取通知详情失败")


@router.post("", summary="创建通知")
async def create_notification(data: NotificationCreate):
    """创建通知"""
    try:
        now = datetime.now()
        
        n = await Notification.create(
            title=data.title,
            content=data.content,
            notification_type=data.notification_type,
            level=data.level,
            scope=data.scope,
            target_roles=data.target_roles,
            target_users=data.target_users,
            link_url=data.link_url,
            is_published=data.is_published,
            publish_time=now if data.is_published else None,
            expire_time=data.expire_time,
        )
        
        logger.info(f"创建通知成功: {n.title}")
        
        formatter = create_formatter()
        return formatter.success(data={"id": n.id}, message="创建通知成功")
        
    except Exception as e:
        logger.error(f"创建通知失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="创建通知失败")


@router.put("/{notification_id}", summary="更新通知")
async def update_notification(notification_id: int, data: NotificationUpdate):
    """更新通知"""
    try:
        n = await Notification.get_or_none(id=notification_id)
        if not n:
            formatter = create_formatter()
            return formatter.error(message="通知不存在", code=404)
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(n, key, value)
        
        n.updated_at = datetime.now()
        await n.save()
        
        logger.info(f"更新通知成功: {n.title}")
        
        formatter = create_formatter()
        return formatter.success(data={"id": n.id}, message="更新通知成功")
        
    except Exception as e:
        logger.error(f"更新通知失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="更新通知失败")


@router.delete("/{notification_id}", summary="删除通知")
async def delete_notification(notification_id: int):
    """删除通知"""
    try:
        n = await Notification.get_or_none(id=notification_id)
        if not n:
            formatter = create_formatter()
            return formatter.error(message="通知不存在", code=404)
        
        await n.delete()
        
        logger.info(f"删除通知成功: {notification_id}")
        
        formatter = create_formatter()
        return formatter.success(message="删除通知成功")
        
    except Exception as e:
        logger.error(f"删除通知失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="删除通知失败")


@router.post("/{notification_id}/publish", summary="发布通知")
async def publish_notification(notification_id: int):
    """发布通知"""
    try:
        n = await Notification.get_or_none(id=notification_id)
        if not n:
            formatter = create_formatter()
            return formatter.error(message="通知不存在", code=404)
        
        n.is_published = True
        n.publish_time = datetime.now()
        n.updated_at = datetime.now()
        await n.save()
        
        logger.info(f"发布通知成功: {n.title}")
        
        formatter = create_formatter()
        return formatter.success(data={"id": n.id}, message="发布通知成功")
        
    except Exception as e:
        logger.error(f"发布通知失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="发布通知失败")


@router.post("/{notification_id}/unpublish", summary="撤回通知")
async def unpublish_notification(notification_id: int):
    """撤回通知"""
    try:
        n = await Notification.get_or_none(id=notification_id)
        if not n:
            formatter = create_formatter()
            return formatter.error(message="通知不存在", code=404)
        
        n.is_published = False
        n.updated_at = datetime.now()
        await n.save()
        
        logger.info(f"撤回通知成功: {n.title}")
        
        formatter = create_formatter()
        return formatter.success(data={"id": n.id}, message="撤回通知成功")
        
    except Exception as e:
        logger.error(f"撤回通知失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="撤回通知失败")
