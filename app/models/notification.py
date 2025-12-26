#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知管理模型
"""

from tortoise import fields
from app.models.base import BaseModel, TimestampMixin


class Notification(TimestampMixin, BaseModel):
    """通知模型"""
    
    # 通知内容
    title = fields.CharField(max_length=200, description="标题")
    content = fields.TextField(null=True, description="内容")
    notification_type = fields.CharField(max_length=50, default="system", description="通知类型")
    level = fields.CharField(max_length=20, default="info", description="通知级别")
    
    # 发送范围
    scope = fields.CharField(max_length=20, default="all", description="发送范围")
    target_roles = fields.JSONField(null=True, description="目标角色ID列表")
    target_users = fields.JSONField(null=True, description="目标用户ID列表")
    
    # 关联信息
    source_type = fields.CharField(max_length=50, null=True, description="来源类型")
    source_id = fields.BigIntField(null=True, description="来源ID")
    link_url = fields.CharField(max_length=500, null=True, description="跳转链接")
    
    # 状态
    is_published = fields.BooleanField(default=True, description="是否发布")
    publish_time = fields.DatetimeField(null=True, description="发布时间")
    expire_time = fields.DatetimeField(null=True, description="过期时间")
    
    # 创建人
    created_by = fields.BigIntField(null=True, description="创建人ID")
    
    class Meta:
        table = "t_sys_notification"
        table_description = "系统通知表"
        ordering = ["-publish_time", "-created_at"]


class UserNotification(BaseModel):
    """用户通知状态模型"""
    
    user_id = fields.BigIntField(description="用户ID")
    notification = fields.ForeignKeyField(
        "models.Notification",
        related_name="user_notifications",
        on_delete=fields.CASCADE,
        description="通知"
    )
    
    is_read = fields.BooleanField(default=False, description="是否已读")
    read_time = fields.DatetimeField(null=True, description="阅读时间")
    is_deleted = fields.BooleanField(default=False, description="是否删除")
    
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    
    class Meta:
        table = "t_sys_user_notification"
        table_description = "用户通知状态表"
        unique_together = [("user_id", "notification")]
