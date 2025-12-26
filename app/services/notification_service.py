#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知服务
提供通知创建、发送等功能
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from app.models.notification import Notification, UserNotification
from app.log import logger


class NotificationService:
    """通知服务类"""
    
    # 报警级别到通知级别的映射
    ALARM_LEVEL_MAP = {
        "emergency": "error",
        "critical": "error", 
        "warning": "warning",
        "info": "info"
    }
    
    @classmethod
    async def create_notification(
        cls,
        title: str,
        content: str,
        notification_type: str = "system",
        level: str = "info",
        scope: str = "all",
        target_roles: Optional[List[int]] = None,
        target_users: Optional[List[int]] = None,
        link_url: Optional[str] = None,
        expire_days: Optional[int] = None,
        auto_publish: bool = True,
        created_by: Optional[int] = None
    ) -> Optional[Notification]:
        """
        创建通知
        
        Args:
            title: 通知标题
            content: 通知内容
            notification_type: 通知类型 (announcement/alarm/task/system)
            level: 通知级别 (info/warning/error)
            scope: 发送范围 (all/role/user)
            target_roles: 目标角色ID列表
            target_users: 目标用户ID列表
            link_url: 跳转链接
            expire_days: 过期天数
            auto_publish: 是否自动发布
            created_by: 创建者ID
        """
        try:
            expire_time = None
            if expire_days:
                from datetime import timedelta
                expire_time = datetime.now() + timedelta(days=expire_days)

            notification = await Notification.create(
                title=title,
                content=content,
                notification_type=notification_type,
                level=level,
                scope=scope,
                target_roles=target_roles or [],
                target_users=target_users or [],
                link_url=link_url,
                expire_time=expire_time,
                is_published=auto_publish,
                publish_time=datetime.now() if auto_publish else None,
                created_by=created_by
            )
            
            logger.info(f"创建通知成功: {title}, ID: {notification.id}")
            return notification
            
        except Exception as e:
            logger.error(f"创建通知失败: {str(e)}", exc_info=True)
            return None
    
    @classmethod
    async def create_alarm_notification(
        cls,
        alarm_data: Dict[str, Any],
        auto_publish: bool = True
    ) -> Optional[Notification]:
        """
        根据报警数据创建通知
        
        Args:
            alarm_data: 报警数据字典
            auto_publish: 是否自动发布
        """
        try:
            rule_name = alarm_data.get("rule_name", "未知规则")
            device_code = alarm_data.get("device_code", "未知设备")
            device_name = alarm_data.get("device_name") or device_code
            alarm_level = alarm_data.get("alarm_level", "warning")
            alarm_content = alarm_data.get("alarm_content", "")
            field_name = alarm_data.get("field_name", "")
            trigger_value = alarm_data.get("trigger_value", "")
            alarm_id = alarm_data.get("id")
            
            # 构建通知标题和内容
            level_text = {
                "emergency": "🚨 紧急",
                "critical": "⚠️ 严重",
                "warning": "⚡ 警告"
            }.get(alarm_level, "📢 提示")
            
            title = f"{level_text} {rule_name}"
            content = f"设备 [{device_name}] 触发报警\n"
            content += f"参数: {field_name}\n"
            content += f"当前值: {trigger_value}\n"
            content += f"详情: {alarm_content}"
            
            # 构建跳转链接
            link_url = f"/alarm/alarm-records?alarm_id={alarm_id}" if alarm_id else "/alarm/alarm-records"
            
            # 映射通知级别
            notification_level = cls.ALARM_LEVEL_MAP.get(alarm_level, "warning")
            
            return await cls.create_notification(
                title=title,
                content=content,
                notification_type="alarm",
                level=notification_level,
                scope="all",  # 报警通知发送给所有用户
                link_url=link_url,
                expire_days=7,  # 报警通知7天后过期
                auto_publish=auto_publish
            )
            
        except Exception as e:
            logger.error(f"创建报警通知失败: {str(e)}", exc_info=True)
            return None
    
    @classmethod
    async def create_batch_alarm_notifications(
        cls,
        alarms: List[Dict[str, Any]]
    ) -> List[Notification]:
        """
        批量创建报警通知
        
        Args:
            alarms: 报警数据列表
        """
        notifications = []
        for alarm in alarms:
            notification = await cls.create_alarm_notification(alarm)
            if notification:
                notifications.append(notification)
        return notifications
    
    @classmethod
    async def mark_as_read(
        cls,
        notification_id: int,
        user_id: int
    ) -> bool:
        """标记通知为已读"""
        try:
            un, created = await UserNotification.get_or_create(
                user_id=user_id,
                notification_id=notification_id,
                defaults={"is_read": True, "read_time": datetime.now()}
            )
            
            if not created and not un.is_read:
                un.is_read = True
                un.read_time = datetime.now()
                await un.save()
            
            return True
        except Exception as e:
            logger.error(f"标记已读失败: {str(e)}")
            return False
    
    @classmethod
    async def get_unread_count(cls, user_id: int) -> int:
        """获取用户未读通知数量"""
        try:
            from tortoise.expressions import Q
            now = datetime.now()
            
            # 获取有效通知总数
            total = await Notification.filter(is_published=True).filter(
                Q(expire_time__isnull=True) | Q(expire_time__gt=now)
            ).count()
            
            # 获取已读数量
            read_count = await UserNotification.filter(
                user_id=user_id, is_read=True, is_deleted=False
            ).count()
            
            # 获取已删除数量
            deleted_count = await UserNotification.filter(
                user_id=user_id, is_deleted=True
            ).count()
            
            return max(0, total - read_count - deleted_count)
            
        except Exception as e:
            logger.error(f"获取未读数量失败: {str(e)}")
            return 0


# 便捷函数
async def create_alarm_notification(alarm_data: Dict[str, Any]) -> Optional[Notification]:
    """创建报警通知的便捷函数"""
    return await NotificationService.create_alarm_notification(alarm_data)


async def create_system_notification(
    title: str,
    content: str,
    level: str = "info",
    link_url: Optional[str] = None
) -> Optional[Notification]:
    """创建系统通知的便捷函数"""
    return await NotificationService.create_notification(
        title=title,
        content=content,
        notification_type="system",
        level=level,
        link_url=link_url
    )
