#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知发送配置 API
"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel

from app.models.email import NotificationConfig
from app.core.response_formatter_v2 import create_formatter
from app.core.pagination import get_pagination_params, create_pagination_response
from app.log import logger

router = APIRouter(tags=["通知发送配置"])


class ChannelsConfig(BaseModel):
    site: bool = True
    email: bool = False
    sms: bool = False


class RetryConfig(BaseModel):
    enabled: bool = True
    max_retries: int = 3
    retry_interval: int = 60


class RateLimitConfig(BaseModel):
    enabled: bool = False
    max_per_hour: int = 100


class SilentPeriodConfig(BaseModel):
    enabled: bool = False
    start_time: str = "22:00"
    end_time: str = "08:00"


class NotificationConfigUpdate(BaseModel):
    channels: Optional[ChannelsConfig] = None
    email_template_id: Optional[int] = None
    retry_config: Optional[RetryConfig] = None
    rate_limit: Optional[RateLimitConfig] = None
    silent_period: Optional[SilentPeriodConfig] = None
    is_enabled: Optional[bool] = None
    remark: Optional[str] = None


@router.get("", summary="获取通知发送配置列表")
async def get_notification_configs(
    notification_type: Optional[str] = Query(None, description="通知类型"),
    pagination: dict = Depends(get_pagination_params)
):
    """获取通知发送配置列表"""
    try:
        query = NotificationConfig.all()
        
        if notification_type:
            query = query.filter(notification_type=notification_type)
        
        total = await query.count()
        configs = await query.order_by("id").offset(pagination["offset"]).limit(pagination["limit"])
        
        items = []
        for c in configs:
            items.append({
                "id": c.id,
                "notification_type": c.notification_type,
                "type_name": c.type_name,
                "channels": c.channels,
                "email_template_id": c.email_template_id,
                "retry_config": c.retry_config,
                "rate_limit": c.rate_limit,
                "silent_period": c.silent_period,
                "is_enabled": c.is_enabled,
                "remark": c.remark,
            })
        
        paginated = create_pagination_response(
            data=items, total=total, page=pagination["page"], page_size=pagination["page_size"]
        )
        
        formatter = create_formatter()
        return formatter.success(data=paginated, message="获取成功")
        
    except Exception as e:
        logger.error(f"获取通知配置列表失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取失败")


@router.get("/{config_id}", summary="获取通知发送配置详情")
async def get_notification_config(config_id: int):
    """获取通知发送配置详情"""
    try:
        config = await NotificationConfig.get_or_none(id=config_id)
        if not config:
            formatter = create_formatter()
            return formatter.error(message="配置不存在", code=404)
        
        data = {
            "id": config.id,
            "notification_type": config.notification_type,
            "type_name": config.type_name,
            "channels": config.channels,
            "email_template_id": config.email_template_id,
            "retry_config": config.retry_config,
            "rate_limit": config.rate_limit,
            "silent_period": config.silent_period,
            "is_enabled": config.is_enabled,
            "remark": config.remark,
        }
        
        formatter = create_formatter()
        return formatter.success(data=data, message="获取成功")
        
    except Exception as e:
        logger.error(f"获取通知配置详情失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取失败")


@router.put("/{config_id}", summary="更新通知发送配置")
async def update_notification_config(config_id: int, data: NotificationConfigUpdate):
    """更新通知发送配置"""
    try:
        config = await NotificationConfig.get_or_none(id=config_id)
        if not config:
            formatter = create_formatter()
            return formatter.error(message="配置不存在", code=404)
        
        update_data = {}
        
        if data.channels is not None:
            update_data["channels"] = data.channels.model_dump()
        if data.email_template_id is not None:
            update_data["email_template_id"] = data.email_template_id
        if data.retry_config is not None:
            update_data["retry_config"] = data.retry_config.model_dump()
        if data.rate_limit is not None:
            update_data["rate_limit"] = data.rate_limit.model_dump()
        if data.silent_period is not None:
            update_data["silent_period"] = data.silent_period.model_dump()
        if data.is_enabled is not None:
            update_data["is_enabled"] = data.is_enabled
        if data.remark is not None:
            update_data["remark"] = data.remark
        
        if update_data:
            update_data["updated_at"] = datetime.now()
            await NotificationConfig.filter(id=config_id).update(**update_data)
        
        formatter = create_formatter()
        return formatter.success(message="更新成功")
        
    except Exception as e:
        logger.error(f"更新通知配置失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="更新失败")


@router.get("/by-type/{notification_type}", summary="根据类型获取配置")
async def get_config_by_type(notification_type: str):
    """根据通知类型获取配置"""
    try:
        config = await NotificationConfig.get_or_none(notification_type=notification_type)
        if not config:
            # 返回默认配置
            data = {
                "notification_type": notification_type,
                "channels": {"site": True, "email": False, "sms": False},
                "retry_config": {"enabled": True, "max_retries": 3, "retry_interval": 60},
                "rate_limit": {"enabled": False, "max_per_hour": 100},
                "silent_period": {"enabled": False, "start_time": "22:00", "end_time": "08:00"},
                "is_enabled": True,
            }
        else:
            data = {
                "id": config.id,
                "notification_type": config.notification_type,
                "type_name": config.type_name,
                "channels": config.channels,
                "email_template_id": config.email_template_id,
                "retry_config": config.retry_config,
                "rate_limit": config.rate_limit,
                "silent_period": config.silent_period,
                "is_enabled": config.is_enabled,
            }
        
        formatter = create_formatter()
        return formatter.success(data=data, message="获取成功")
        
    except Exception as e:
        logger.error(f"获取通知配置失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取失败")
