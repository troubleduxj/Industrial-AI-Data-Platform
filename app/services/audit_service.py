"""
权限审计服务
"""
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import Request
from app.core.unified_logger import get_logger

logger = get_logger(__name__)
import time


class AuditService:
    """权限审计服务"""
    
    # 操作类型常量
    ACTION_LOGIN = "LOGIN"
    ACTION_LOGOUT = "LOGOUT"
    ACTION_PERMISSION_CHECK = "PERMISSION_CHECK"
    ACTION_API_ACCESS = "API_ACCESS"
    ACTION_MENU_ACCESS = "MENU_ACCESS"
    ACTION_ROLE_CHANGE = "ROLE_CHANGE"
    ACTION_PERMISSION_CHANGE = "PERMISSION_CHANGE"
    ACTION_BATCH_OPERATION = "BATCH_OPERATION"
    ACTION_SENSITIVE_OPERATION = "SENSITIVE_OPERATION"
    
    # 风险等级
    RISK_LOW = "LOW"
    RISK_MEDIUM = "MEDIUM"
    RISK_HIGH = "HIGH"
    RISK_CRITICAL = "CRITICAL"
    
    # 事件类型
    EVENT_FAILED_LOGIN = "FAILED_LOGIN"
    EVENT_PERMISSION_DENIED = "PERMISSION_DENIED"
    EVENT_SUSPICIOUS_ACCESS = "SUSPICIOUS_ACCESS"
    EVENT_PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    EVENT_BATCH_OPERATION = "BATCH_OPERATION"
    EVENT_UNUSUAL_ACTIVITY = "UNUSUAL_ACTIVITY"

    async def log_authentication(
        self,
        user_id: Optional[int],
        username: str,
        action_type: str,
        success: bool,
        request: Request,
        extra_data: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None
    ):
        """记录认证日志"""
        try:
            from app.models.audit_log import AuditLog
            
            # 确定风险等级
            risk_level = self.RISK_LOW if success else self.RISK_MEDIUM
            
            audit_log = await AuditLog.create(
                user_id=user_id,
                username=username,
                user_ip=self._get_client_ip(request),
                user_agent=request.headers.get("user-agent", ""),
                action_type=action_type,
                action_name=f"用户{action_type.lower()}",
                resource_type="AUTH",
                permission_result=success,
                request_method=request.method,
                request_path=str(request.url.path),
                response_status=200 if success else 401,
                response_message="成功" if success else "认证失败",
                extra_data=extra_data or {},
                risk_level=risk_level,
                duration_ms=duration_ms
            )
            
            logger.info(f"记录认证日志: {username} {action_type} {'成功' if success else '失败'}")
            
        except Exception as e:
            logger.error(f"记录认证日志失败: {e}")

    async def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        action_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        risk_level: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """获取审计日志"""
        try:
            from app.models.audit_log import AuditLog
            
            query = AuditLog.all()
            
            # 添加过滤条件
            if user_id:
                query = query.filter(user_id=user_id)
            if action_type:
                query = query.filter(action_type=action_type)
            if start_time:
                query = query.filter(created_at__gte=start_time)
            if end_time:
                query = query.filter(created_at__lte=end_time)
            if risk_level:
                query = query.filter(risk_level=risk_level)
            
            # 获取总数
            total = await query.count()
            
            # 分页查询
            logs = await query.order_by('-created_at')\
                             .offset((page - 1) * page_size)\
                             .limit(page_size)
            
            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "logs": [await self._log_to_dict(log) for log in logs]
            }
            
        except Exception as e:
            logger.error(f"获取审计日志失败: {e}")
            return {"total": 0, "page": page, "page_size": page_size, "logs": []}

    async def get_security_events(
        self,
        event_type: Optional[str] = None,
        event_level: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """获取安全事件"""
        try:
            from app.models.audit_log import SecurityEvent
            
            query = SecurityEvent.all()
            
            # 添加过滤条件
            if event_type:
                query = query.filter(event_type=event_type)
            if event_level:
                query = query.filter(event_level=event_level)
            if status:
                query = query.filter(status=status)
            if start_time:
                query = query.filter(created_at__gte=start_time)
            if end_time:
                query = query.filter(created_at__lte=end_time)
            
            # 获取总数
            total = await query.count()
            
            # 分页查询
            events = await query.order_by('-created_at')\
                               .offset((page - 1) * page_size)\
                               .limit(page_size)
            
            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "events": [await self._event_to_dict(event) for event in events]
            }
            
        except Exception as e:
            logger.error(f"获取安全事件失败: {e}")
            return {"total": 0, "page": page, "page_size": page_size, "events": []}

    async def handle_security_event(
        self,
        event_id: int,
        handled_by: int,
        handle_note: str
    ) -> Optional[Dict[str, Any]]:
        """处理安全事件"""
        try:
            from app.models.audit_log import SecurityEvent
            
            event = await SecurityEvent.get_or_none(id=event_id)
            if not event:
                return None
            
            event.status = "HANDLED"
            event.handled_by = handled_by
            event.handled_at = datetime.utcnow()
            event.handle_note = handle_note
            
            await event.save()
            
            return await self._event_to_dict(event)
            
        except Exception as e:
            logger.error(f"处理安全事件失败: {e}")
            return None

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def _log_to_dict(self, log) -> Dict[str, Any]:
        """将日志对象转换为字典"""
        return {
            'id': log.id,
            'user_id': log.user_id,
            'username': log.username,
            'user_ip': log.user_ip,
            'user_agent': log.user_agent,
            'action_type': log.action_type,
            'action_name': log.action_name,
            'resource_type': log.resource_type,
            'resource_id': log.resource_id,
            'permission_code': log.permission_code,
            'permission_result': log.permission_result,
            'request_method': log.request_method,
            'request_path': log.request_path,
            'request_params': log.request_params,
            'response_status': log.response_status,
            'response_message': log.response_message,
            'extra_data': log.extra_data,
            'risk_level': log.risk_level,
            'created_at': log.created_at.isoformat() if log.created_at else None,
            'duration_ms': log.duration_ms
        }
    
    async def _event_to_dict(self, event) -> Dict[str, Any]:
        """将安全事件对象转换为字典"""
        return {
            'id': event.id,
            'event_type': event.event_type,
            'event_level': event.event_level,
            'event_title': event.event_title,
            'event_description': event.event_description,
            'user_id': event.user_id,
            'username': event.username,
            'user_ip': event.user_ip,
            'request_path': event.request_path,
            'request_method': event.request_method,
            'detection_rule': event.detection_rule,
            'threat_score': event.threat_score,
            'status': event.status,
            'handled_by': event.handled_by,
            'handled_at': event.handled_at.isoformat() if event.handled_at else None,
            'handle_note': event.handle_note,
            'extra_data': event.extra_data,
            'created_at': event.created_at.isoformat() if event.created_at else None
        }


# 全局审计服务实例
audit_service = AuditService()