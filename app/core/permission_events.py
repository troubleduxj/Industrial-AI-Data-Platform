# -*- coding: utf-8 -*-
"""
权限变更事件监听和处理模块
实现权限变更的实时监听和缓存更新
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from app.core.permission_cache import permission_cache_manager
from app.models.admin import User, Role, SysApiEndpoint, HttpAuditLog

logger = logging.getLogger(__name__)


class PermissionEventType(Enum):
    """权限事件类型"""
    USER_ROLE_ASSIGNED = "user_role_assigned"      # 用户分配角色
    USER_ROLE_REMOVED = "user_role_removed"        # 用户移除角色
    ROLE_PERMISSION_ASSIGNED = "role_permission_assigned"  # 角色分配权限
    ROLE_PERMISSION_REMOVED = "role_permission_removed"    # 角色移除权限
    USER_STATUS_CHANGED = "user_status_changed"    # 用户状态变更
    ROLE_STATUS_CHANGED = "role_status_changed"    # 角色状态变更
    API_PERMISSION_CHANGED = "api_permission_changed"  # API权限变更


class PermissionEvent:
    """权限变更事件"""
    
    def __init__(
        self,
        event_type: PermissionEventType,
        user_id: Optional[int] = None,
        role_id: Optional[int] = None,
        api_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        operator_id: Optional[int] = None
    ):
        self.event_type = event_type
        self.user_id = user_id
        self.role_id = role_id
        self.api_id = api_id
        self.details = details or {}
        self.operator_id = operator_id
        self.timestamp = datetime.now()


class PermissionEventHandler:
    """权限事件处理器"""
    
    def __init__(self):
        self.event_handlers = {
            PermissionEventType.USER_ROLE_ASSIGNED: self._handle_user_role_assigned,
            PermissionEventType.USER_ROLE_REMOVED: self._handle_user_role_removed,
            PermissionEventType.ROLE_PERMISSION_ASSIGNED: self._handle_role_permission_assigned,
            PermissionEventType.ROLE_PERMISSION_REMOVED: self._handle_role_permission_removed,
            PermissionEventType.USER_STATUS_CHANGED: self._handle_user_status_changed,
            PermissionEventType.ROLE_STATUS_CHANGED: self._handle_role_status_changed,
            PermissionEventType.API_PERMISSION_CHANGED: self._handle_api_permission_changed,
        }
    
    async def handle_event(self, event: PermissionEvent):
        """处理权限变更事件"""
        try:
            handler = self.event_handlers.get(event.event_type)
            if handler:
                await handler(event)
                await self._log_permission_change(event)
                logger.info(f"权限事件处理完成: {event.event_type.value}")
            else:
                logger.warning(f"未找到事件处理器: {event.event_type.value}")
        except Exception as e:
            logger.error(f"处理权限事件失败 {event.event_type.value}: {e}")
    
    async def _handle_user_role_assigned(self, event: PermissionEvent):
        """处理用户角色分配事件"""
        if event.user_id:
            role_ids = event.details.get("role_ids", [])
            await permission_cache_event_handler.on_user_role_changed(
                event.user_id, [], role_ids
            )
            logger.info(f"用户 {event.user_id} 分配角色后清除权限缓存")
    
    async def _handle_user_role_removed(self, event: PermissionEvent):
        """处理用户角色移除事件"""
        if event.user_id:
            role_ids = event.details.get("role_ids", [])
            await permission_cache_event_handler.on_user_role_changed(
                event.user_id, role_ids, []
            )
            logger.info(f"用户 {event.user_id} 移除角色后清除权限缓存")
    
    async def _handle_role_permission_assigned(self, event: PermissionEvent):
        """处理角色权限分配事件"""
        if event.role_id:
            await permission_cache_event_handler.on_role_permission_changed(event.role_id)
            logger.info(f"角色 {event.role_id} 分配权限后清除相关权限缓存")
    
    async def _handle_role_permission_removed(self, event: PermissionEvent):
        """处理角色权限移除事件"""
        if event.role_id:
            await permission_cache_event_handler.on_role_permission_changed(event.role_id)
            logger.info(f"角色 {event.role_id} 移除权限后清除相关权限缓存")
    
    async def _handle_user_status_changed(self, event: PermissionEvent):
        """处理用户状态变更事件"""
        if event.user_id:
            new_status = event.details.get("new_status", True)
            await permission_cache_event_handler.on_user_status_changed(
                event.user_id, new_status
            )
            logger.info(f"用户 {event.user_id} 状态变更后清除权限缓存")
    
    async def _handle_role_status_changed(self, event: PermissionEvent):
        """处理角色状态变更事件"""
        if event.role_id:
            await permission_cache_event_handler.on_role_permission_changed(event.role_id)
            logger.info(f"角色 {event.role_id} 状态变更后清除相关权限缓存")
    
    async def _handle_api_permission_changed(self, event: PermissionEvent):
        """处理API权限变更事件"""
        # 清除所有权限缓存，因为API权限变更可能影响所有用户
        from app.core.redis_cache import cache_invalidation_manager
        await cache_invalidation_manager.invalidate_by_type("permission")
        logger.info("API权限变更后清除所有权限缓存")
    
    async def _log_permission_change(self, event: PermissionEvent):
        """记录权限变更日志"""
        try:
            # 构建日志详情
            log_details = {
                "event_type": event.event_type.value,
                "user_id": event.user_id,
                "role_id": event.role_id,
                "api_id": event.api_id,
                "details": event.details,
                "timestamp": event.timestamp.isoformat()
            }
            
            # 记录权限变更审计日志
            try:
                audit_log = AuditLog(
                    user_id=event.operator_id or 0,
                    username="system",
                    module="权限管理",
                    summary=f"权限变更: {event.event_type.value}",
                    method="SYSTEM",
                    path="/permission/change",
                    status=200,
                    response_time=0,
                    request_args=log_details,
                    response_body={"success": True}
                )
                await audit_log.save()
                logger.debug(f"权限变更审计日志已记录: {event.event_type.value}")
            except Exception as audit_error:
                logger.error(f"记录权限变更审计日志失败: {audit_error}")
            
        except Exception as e:
            logger.error(f"记录权限变更日志失败: {e}")


class PermissionEventManager:
    """权限事件管理器"""
    
    def __init__(self):
        self.handler = PermissionEventHandler()
        self.event_queue = []  # 简单的内存队列，生产环境可以使用Redis队列
    
    async def emit_event(self, event: PermissionEvent):
        """发出权限变更事件"""
        try:
            # 立即处理事件
            await self.handler.handle_event(event)
        except Exception as e:
            logger.error(f"发出权限事件失败: {e}")
            # 可以考虑将失败的事件加入重试队列
    
    async def emit_user_role_assigned(
        self, 
        user_id: int, 
        role_ids: List[int], 
        operator_id: Optional[int] = None
    ):
        """发出用户角色分配事件"""
        event = PermissionEvent(
            event_type=PermissionEventType.USER_ROLE_ASSIGNED,
            user_id=user_id,
            details={"role_ids": role_ids},
            operator_id=operator_id
        )
        await self.emit_event(event)
    
    async def emit_user_role_removed(
        self, 
        user_id: int, 
        role_ids: List[int], 
        operator_id: Optional[int] = None
    ):
        """发出用户角色移除事件"""
        event = PermissionEvent(
            event_type=PermissionEventType.USER_ROLE_REMOVED,
            user_id=user_id,
            details={"role_ids": role_ids},
            operator_id=operator_id
        )
        await self.emit_event(event)
    
    async def emit_role_permission_assigned(
        self, 
        role_id: int, 
        api_ids: List[int], 
        operator_id: Optional[int] = None
    ):
        """发出角色权限分配事件"""
        event = PermissionEvent(
            event_type=PermissionEventType.ROLE_PERMISSION_ASSIGNED,
            role_id=role_id,
            details={"api_ids": api_ids},
            operator_id=operator_id
        )
        await self.emit_event(event)
    
    async def emit_role_permission_removed(
        self, 
        role_id: int, 
        api_ids: List[int], 
        operator_id: Optional[int] = None
    ):
        """发出角色权限移除事件"""
        event = PermissionEvent(
            event_type=PermissionEventType.ROLE_PERMISSION_REMOVED,
            role_id=role_id,
            details={"api_ids": api_ids},
            operator_id=operator_id
        )
        await self.emit_event(event)
    
    async def emit_user_status_changed(
        self, 
        user_id: int, 
        old_status: bool, 
        new_status: bool, 
        operator_id: Optional[int] = None
    ):
        """发出用户状态变更事件"""
        event = PermissionEvent(
            event_type=PermissionEventType.USER_STATUS_CHANGED,
            user_id=user_id,
            details={"old_status": old_status, "new_status": new_status},
            operator_id=operator_id
        )
        await self.emit_event(event)
    
    async def emit_role_status_changed(
        self, 
        role_id: int, 
        old_status: bool, 
        new_status: bool, 
        operator_id: Optional[int] = None
    ):
        """发出角色状态变更事件"""
        event = PermissionEvent(
            event_type=PermissionEventType.ROLE_STATUS_CHANGED,
            role_id=role_id,
            details={"old_status": old_status, "new_status": new_status},
            operator_id=operator_id
        )
        await self.emit_event(event)
    
    async def emit_api_permission_changed(
        self, 
        api_id: int, 
        changes: Dict[str, Any], 
        operator_id: Optional[int] = None
    ):
        """发出API权限变更事件"""
        event = PermissionEvent(
            event_type=PermissionEventType.API_PERMISSION_CHANGED,
            api_id=api_id,
            details={"changes": changes},
            operator_id=operator_id
        )
        await self.emit_event(event)


# 全局权限事件管理器实例
permission_event_manager = PermissionEventManager()