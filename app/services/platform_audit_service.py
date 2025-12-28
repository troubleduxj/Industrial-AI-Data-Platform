#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工业AI数据平台审计日志服务
提供操作日志记录、敏感数据访问跟踪和日志查询分析

需求映射：
- 需求10.3: 敏感数据访问审计
- 需求7.5: 模型生命周期操作审计
"""

import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
from fastapi import Request

from app.core.unified_logger import get_logger
from app.models.audit_log import AuditLog, SecurityEvent

logger = get_logger(__name__)


class AuditActionType(Enum):
    """审计操作类型"""
    # 认证相关
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    
    # 资产管理
    ASSET_CATEGORY_CREATE = "ASSET_CATEGORY_CREATE"
    ASSET_CATEGORY_UPDATE = "ASSET_CATEGORY_UPDATE"
    ASSET_CATEGORY_DELETE = "ASSET_CATEGORY_DELETE"
    ASSET_CREATE = "ASSET_CREATE"
    ASSET_UPDATE = "ASSET_UPDATE"
    ASSET_DELETE = "ASSET_DELETE"
    
    # AI模型管理
    MODEL_REGISTER = "MODEL_REGISTER"
    MODEL_UPDATE = "MODEL_UPDATE"
    MODEL_DELETE = "MODEL_DELETE"
    MODEL_DEPLOY = "MODEL_DEPLOY"
    MODEL_ACTIVATE = "MODEL_ACTIVATE"
    MODEL_ROLLBACK = "MODEL_ROLLBACK"
    
    # 预测操作
    PREDICTION_REQUEST = "PREDICTION_REQUEST"
    BATCH_PREDICTION = "BATCH_PREDICTION"
    
    # 特征工程
    FEATURE_VIEW_CREATE = "FEATURE_VIEW_CREATE"
    FEATURE_VIEW_UPDATE = "FEATURE_VIEW_UPDATE"
    FEATURE_VIEW_DELETE = "FEATURE_VIEW_DELETE"
    FEATURE_VIEW_ACTIVATE = "FEATURE_VIEW_ACTIVATE"
    
    # 数据访问
    DATA_QUERY = "DATA_QUERY"
    DATA_EXPORT = "DATA_EXPORT"
    SENSITIVE_DATA_ACCESS = "SENSITIVE_DATA_ACCESS"
    
    # 系统操作
    SYSTEM_CONFIG_CHANGE = "SYSTEM_CONFIG_CHANGE"
    PERMISSION_CHANGE = "PERMISSION_CHANGE"
    ROLE_CHANGE = "ROLE_CHANGE"


class AuditRiskLevel(Enum):
    """审计风险等级"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SecurityEventType(Enum):
    """安全事件类型"""
    FAILED_LOGIN = "FAILED_LOGIN"
    BRUTE_FORCE_ATTEMPT = "BRUTE_FORCE_ATTEMPT"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    SUSPICIOUS_ACCESS = "SUSPICIOUS_ACCESS"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    DATA_BREACH_ATTEMPT = "DATA_BREACH_ATTEMPT"
    UNUSUAL_ACTIVITY = "UNUSUAL_ACTIVITY"
    MODEL_TAMPERING = "MODEL_TAMPERING"


# 操作风险等级映射
ACTION_RISK_LEVELS = {
    AuditActionType.LOGIN: AuditRiskLevel.LOW,
    AuditActionType.LOGOUT: AuditRiskLevel.LOW,
    AuditActionType.TOKEN_REFRESH: AuditRiskLevel.LOW,
    AuditActionType.PASSWORD_CHANGE: AuditRiskLevel.MEDIUM,
    
    AuditActionType.ASSET_CATEGORY_CREATE: AuditRiskLevel.MEDIUM,
    AuditActionType.ASSET_CATEGORY_UPDATE: AuditRiskLevel.MEDIUM,
    AuditActionType.ASSET_CATEGORY_DELETE: AuditRiskLevel.HIGH,
    AuditActionType.ASSET_CREATE: AuditRiskLevel.LOW,
    AuditActionType.ASSET_UPDATE: AuditRiskLevel.LOW,
    AuditActionType.ASSET_DELETE: AuditRiskLevel.MEDIUM,
    
    AuditActionType.MODEL_REGISTER: AuditRiskLevel.MEDIUM,
    AuditActionType.MODEL_UPDATE: AuditRiskLevel.MEDIUM,
    AuditActionType.MODEL_DELETE: AuditRiskLevel.HIGH,
    AuditActionType.MODEL_DEPLOY: AuditRiskLevel.HIGH,
    AuditActionType.MODEL_ACTIVATE: AuditRiskLevel.HIGH,
    AuditActionType.MODEL_ROLLBACK: AuditRiskLevel.HIGH,
    
    AuditActionType.PREDICTION_REQUEST: AuditRiskLevel.LOW,
    AuditActionType.BATCH_PREDICTION: AuditRiskLevel.MEDIUM,
    
    AuditActionType.FEATURE_VIEW_CREATE: AuditRiskLevel.MEDIUM,
    AuditActionType.FEATURE_VIEW_UPDATE: AuditRiskLevel.MEDIUM,
    AuditActionType.FEATURE_VIEW_DELETE: AuditRiskLevel.HIGH,
    AuditActionType.FEATURE_VIEW_ACTIVATE: AuditRiskLevel.MEDIUM,
    
    AuditActionType.DATA_QUERY: AuditRiskLevel.LOW,
    AuditActionType.DATA_EXPORT: AuditRiskLevel.MEDIUM,
    AuditActionType.SENSITIVE_DATA_ACCESS: AuditRiskLevel.HIGH,
    
    AuditActionType.SYSTEM_CONFIG_CHANGE: AuditRiskLevel.CRITICAL,
    AuditActionType.PERMISSION_CHANGE: AuditRiskLevel.HIGH,
    AuditActionType.ROLE_CHANGE: AuditRiskLevel.HIGH,
}


class PlatformAuditService:
    """平台审计服务"""
    
    def __init__(self):
        # 失败登录计数器（用于检测暴力破解）
        self._failed_login_counts: Dict[str, List[datetime]] = {}
        self._failed_login_threshold = 5  # 5次失败
        self._failed_login_window = 300  # 5分钟窗口
    
    async def log_operation(
        self,
        user_id: Optional[int],
        username: str,
        action_type: AuditActionType,
        resource_type: str,
        resource_id: Optional[str] = None,
        request: Optional[Request] = None,
        success: bool = True,
        extra_data: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None
    ) -> Optional[int]:
        """
        记录操作日志
        
        Args:
            user_id: 用户ID
            username: 用户名
            action_type: 操作类型
            resource_type: 资源类型
            resource_id: 资源ID
            request: 请求对象
            success: 操作是否成功
            extra_data: 额外数据
            duration_ms: 操作耗时
            
        Returns:
            int: 审计日志ID
        """
        try:
            # 确定风险等级
            risk_level = ACTION_RISK_LEVELS.get(action_type, AuditRiskLevel.LOW)
            if not success:
                # 失败操作提升风险等级
                if risk_level == AuditRiskLevel.LOW:
                    risk_level = AuditRiskLevel.MEDIUM
                elif risk_level == AuditRiskLevel.MEDIUM:
                    risk_level = AuditRiskLevel.HIGH
            
            # 获取请求信息
            user_ip = self._get_client_ip(request) if request else "unknown"
            user_agent = request.headers.get("user-agent", "") if request else ""
            request_method = request.method if request else "UNKNOWN"
            request_path = str(request.url.path) if request else ""
            request_params = dict(request.query_params) if request else {}
            
            # 创建审计日志
            audit_log = await AuditLog.create(
                user_id=user_id,
                username=username,
                user_ip=user_ip,
                user_agent=user_agent,
                action_type=action_type.value,
                action_name=self._get_action_name(action_type),
                resource_type=resource_type,
                resource_id=resource_id,
                permission_result=success,
                request_method=request_method,
                request_path=request_path,
                request_params=request_params,
                response_status=200 if success else 400,
                response_message="成功" if success else "失败",
                extra_data=extra_data or {},
                risk_level=risk_level.value,
                duration_ms=duration_ms
            )
            
            logger.info(
                f"审计日志: user={username}, action={action_type.value}, "
                f"resource={resource_type}/{resource_id}, success={success}"
            )
            
            return audit_log.id
            
        except Exception as e:
            logger.error(f"记录审计日志失败: {e}")
            return None
    
    async def log_model_lifecycle(
        self,
        user_id: int,
        username: str,
        model_id: int,
        model_name: str,
        action: str,
        version: Optional[str] = None,
        request: Optional[Request] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        记录模型生命周期操作
        
        Args:
            user_id: 用户ID
            username: 用户名
            model_id: 模型ID
            model_name: 模型名称
            action: 操作类型
            version: 模型版本
            request: 请求对象
            extra_data: 额外数据
            
        Returns:
            int: 审计日志ID
        """
        # 映射操作到审计类型
        action_mapping = {
            'register': AuditActionType.MODEL_REGISTER,
            'update': AuditActionType.MODEL_UPDATE,
            'delete': AuditActionType.MODEL_DELETE,
            'deploy': AuditActionType.MODEL_DEPLOY,
            'activate': AuditActionType.MODEL_ACTIVATE,
            'rollback': AuditActionType.MODEL_ROLLBACK,
        }
        
        action_type = action_mapping.get(action.lower(), AuditActionType.MODEL_UPDATE)
        
        log_data = {
            'model_name': model_name,
            'version': version,
            **(extra_data or {})
        }
        
        return await self.log_operation(
            user_id=user_id,
            username=username,
            action_type=action_type,
            resource_type='ai_model',
            resource_id=str(model_id),
            request=request,
            success=True,
            extra_data=log_data
        )
    
    async def log_sensitive_data_access(
        self,
        user_id: int,
        username: str,
        data_type: str,
        data_id: str,
        access_reason: str,
        request: Optional[Request] = None
    ) -> Optional[int]:
        """
        记录敏感数据访问
        
        Args:
            user_id: 用户ID
            username: 用户名
            data_type: 数据类型
            data_id: 数据ID
            access_reason: 访问原因
            request: 请求对象
            
        Returns:
            int: 审计日志ID
        """
        return await self.log_operation(
            user_id=user_id,
            username=username,
            action_type=AuditActionType.SENSITIVE_DATA_ACCESS,
            resource_type=data_type,
            resource_id=data_id,
            request=request,
            success=True,
            extra_data={
                'access_reason': access_reason,
                'is_sensitive': True
            }
        )
    
    async def log_failed_login(
        self,
        username: str,
        reason: str,
        request: Optional[Request] = None
    ) -> bool:
        """
        记录失败的登录尝试
        
        Args:
            username: 用户名
            reason: 失败原因
            request: 请求对象
            
        Returns:
            bool: 是否触发安全事件
        """
        user_ip = self._get_client_ip(request) if request else "unknown"
        
        # 记录审计日志
        await self.log_operation(
            user_id=None,
            username=username,
            action_type=AuditActionType.LOGIN,
            resource_type='auth',
            request=request,
            success=False,
            extra_data={'reason': reason}
        )
        
        # 检测暴力破解
        is_brute_force = await self._check_brute_force(user_ip)
        
        if is_brute_force:
            await self.create_security_event(
                event_type=SecurityEventType.BRUTE_FORCE_ATTEMPT,
                event_level="HIGH",
                event_title=f"检测到暴力破解尝试: {user_ip}",
                event_description=f"IP地址 {user_ip} 在短时间内多次登录失败",
                user_ip=user_ip,
                username=username,
                request=request,
                extra_data={'failed_attempts': self._failed_login_threshold}
            )
            return True
        
        return False
    
    async def _check_brute_force(self, user_ip: str) -> bool:
        """检测暴力破解"""
        now = datetime.now()
        window_start = now - timedelta(seconds=self._failed_login_window)
        
        # 清理过期记录
        if user_ip in self._failed_login_counts:
            self._failed_login_counts[user_ip] = [
                t for t in self._failed_login_counts[user_ip]
                if t > window_start
            ]
        else:
            self._failed_login_counts[user_ip] = []
        
        # 添加当前失败记录
        self._failed_login_counts[user_ip].append(now)
        
        # 检查是否超过阈值
        return len(self._failed_login_counts[user_ip]) >= self._failed_login_threshold
    
    async def create_security_event(
        self,
        event_type: SecurityEventType,
        event_level: str,
        event_title: str,
        event_description: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        user_ip: Optional[str] = None,
        request: Optional[Request] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        创建安全事件
        
        Args:
            event_type: 事件类型
            event_level: 事件级别
            event_title: 事件标题
            event_description: 事件描述
            user_id: 用户ID
            username: 用户名
            user_ip: 用户IP
            request: 请求对象
            extra_data: 额外数据
            
        Returns:
            int: 安全事件ID
        """
        try:
            if request and not user_ip:
                user_ip = self._get_client_ip(request)
            
            request_path = str(request.url.path) if request else ""
            request_method = request.method if request else ""
            
            event = await SecurityEvent.create(
                event_type=event_type.value,
                event_level=event_level,
                event_title=event_title,
                event_description=event_description,
                user_id=user_id,
                username=username,
                user_ip=user_ip,
                request_path=request_path,
                request_method=request_method,
                detection_rule=event_type.value,
                threat_score=self._calculate_threat_score(event_type, event_level),
                status="PENDING",
                extra_data=extra_data or {}
            )
            
            logger.warning(
                f"安全事件: type={event_type.value}, level={event_level}, "
                f"title={event_title}"
            )
            
            return event.id
            
        except Exception as e:
            logger.error(f"创建安全事件失败: {e}")
            return None
    
    def _calculate_threat_score(self, event_type: SecurityEventType, event_level: str) -> int:
        """计算威胁评分"""
        base_scores = {
            SecurityEventType.FAILED_LOGIN: 10,
            SecurityEventType.BRUTE_FORCE_ATTEMPT: 60,
            SecurityEventType.PERMISSION_DENIED: 20,
            SecurityEventType.SUSPICIOUS_ACCESS: 40,
            SecurityEventType.PRIVILEGE_ESCALATION: 80,
            SecurityEventType.DATA_BREACH_ATTEMPT: 90,
            SecurityEventType.UNUSUAL_ACTIVITY: 30,
            SecurityEventType.MODEL_TAMPERING: 70,
        }
        
        level_multipliers = {
            "LOW": 0.5,
            "MEDIUM": 1.0,
            "HIGH": 1.5,
            "CRITICAL": 2.0
        }
        
        base_score = base_scores.get(event_type, 20)
        multiplier = level_multipliers.get(event_level, 1.0)
        
        return min(100, int(base_score * multiplier))
    
    async def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        action_type: Optional[str] = None,
        resource_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        查询审计日志
        
        Args:
            user_id: 用户ID过滤
            action_type: 操作类型过滤
            resource_type: 资源类型过滤
            risk_level: 风险等级过滤
            start_time: 开始时间
            end_time: 结束时间
            page: 页码
            page_size: 每页大小
            
        Returns:
            Dict: 审计日志列表和分页信息
        """
        try:
            query = AuditLog.all()
            
            if user_id:
                query = query.filter(user_id=user_id)
            if action_type:
                query = query.filter(action_type=action_type)
            if resource_type:
                query = query.filter(resource_type=resource_type)
            if risk_level:
                query = query.filter(risk_level=risk_level)
            if start_time:
                query = query.filter(created_at__gte=start_time)
            if end_time:
                query = query.filter(created_at__lte=end_time)
            
            total = await query.count()
            
            logs = await query.order_by('-created_at')\
                             .offset((page - 1) * page_size)\
                             .limit(page_size)
            
            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "logs": [self._log_to_dict(log) for log in logs]
            }
            
        except Exception as e:
            logger.error(f"查询审计日志失败: {e}")
            return {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "logs": []
            }
    
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
        """
        查询安全事件
        
        Args:
            event_type: 事件类型过滤
            event_level: 事件级别过滤
            status: 状态过滤
            start_time: 开始时间
            end_time: 结束时间
            page: 页码
            page_size: 每页大小
            
        Returns:
            Dict: 安全事件列表和分页信息
        """
        try:
            query = SecurityEvent.all()
            
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
            
            total = await query.count()
            
            events = await query.order_by('-created_at')\
                               .offset((page - 1) * page_size)\
                               .limit(page_size)
            
            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "events": [self._event_to_dict(event) for event in events]
            }
            
        except Exception as e:
            logger.error(f"查询安全事件失败: {e}")
            return {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "events": []
            }
    
    async def get_audit_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取审计统计信息
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            Dict: 统计信息
        """
        try:
            if not start_time:
                start_time = datetime.now() - timedelta(days=7)
            if not end_time:
                end_time = datetime.now()
            
            query = AuditLog.filter(
                created_at__gte=start_time,
                created_at__lte=end_time
            )
            
            total_logs = await query.count()
            
            # 按操作类型统计
            action_stats = {}
            for action in AuditActionType:
                count = await query.filter(action_type=action.value).count()
                if count > 0:
                    action_stats[action.value] = count
            
            # 按风险等级统计
            risk_stats = {}
            for risk in AuditRiskLevel:
                count = await query.filter(risk_level=risk.value).count()
                if count > 0:
                    risk_stats[risk.value] = count
            
            # 失败操作统计
            failed_count = await query.filter(permission_result=False).count()
            
            # 安全事件统计
            event_query = SecurityEvent.filter(
                created_at__gte=start_time,
                created_at__lte=end_time
            )
            total_events = await event_query.count()
            pending_events = await event_query.filter(status="PENDING").count()
            
            return {
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "audit_logs": {
                    "total": total_logs,
                    "by_action": action_stats,
                    "by_risk_level": risk_stats,
                    "failed_operations": failed_count,
                    "success_rate": (total_logs - failed_count) / total_logs if total_logs > 0 else 1.0
                },
                "security_events": {
                    "total": total_events,
                    "pending": pending_events,
                    "handled": total_events - pending_events
                }
            }
            
        except Exception as e:
            logger.error(f"获取审计统计失败: {e}")
            return {}
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        if not request:
            return "unknown"
        
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _get_action_name(self, action_type: AuditActionType) -> str:
        """获取操作名称"""
        action_names = {
            AuditActionType.LOGIN: "用户登录",
            AuditActionType.LOGOUT: "用户登出",
            AuditActionType.TOKEN_REFRESH: "令牌刷新",
            AuditActionType.PASSWORD_CHANGE: "密码修改",
            AuditActionType.ASSET_CATEGORY_CREATE: "创建资产类别",
            AuditActionType.ASSET_CATEGORY_UPDATE: "更新资产类别",
            AuditActionType.ASSET_CATEGORY_DELETE: "删除资产类别",
            AuditActionType.ASSET_CREATE: "创建资产",
            AuditActionType.ASSET_UPDATE: "更新资产",
            AuditActionType.ASSET_DELETE: "删除资产",
            AuditActionType.MODEL_REGISTER: "注册AI模型",
            AuditActionType.MODEL_UPDATE: "更新AI模型",
            AuditActionType.MODEL_DELETE: "删除AI模型",
            AuditActionType.MODEL_DEPLOY: "部署AI模型",
            AuditActionType.MODEL_ACTIVATE: "激活AI模型",
            AuditActionType.MODEL_ROLLBACK: "回滚AI模型",
            AuditActionType.PREDICTION_REQUEST: "预测请求",
            AuditActionType.BATCH_PREDICTION: "批量预测",
            AuditActionType.FEATURE_VIEW_CREATE: "创建特征视图",
            AuditActionType.FEATURE_VIEW_UPDATE: "更新特征视图",
            AuditActionType.FEATURE_VIEW_DELETE: "删除特征视图",
            AuditActionType.FEATURE_VIEW_ACTIVATE: "激活特征视图",
            AuditActionType.DATA_QUERY: "数据查询",
            AuditActionType.DATA_EXPORT: "数据导出",
            AuditActionType.SENSITIVE_DATA_ACCESS: "敏感数据访问",
            AuditActionType.SYSTEM_CONFIG_CHANGE: "系统配置变更",
            AuditActionType.PERMISSION_CHANGE: "权限变更",
            AuditActionType.ROLE_CHANGE: "角色变更",
        }
        return action_names.get(action_type, action_type.value)
    
    def _log_to_dict(self, log: AuditLog) -> Dict[str, Any]:
        """将审计日志转换为字典"""
        return {
            'id': log.id,
            'user_id': log.user_id,
            'username': log.username,
            'user_ip': log.user_ip,
            'action_type': log.action_type,
            'action_name': log.action_name,
            'resource_type': log.resource_type,
            'resource_id': log.resource_id,
            'permission_result': log.permission_result,
            'request_method': log.request_method,
            'request_path': log.request_path,
            'response_status': log.response_status,
            'risk_level': log.risk_level,
            'duration_ms': log.duration_ms,
            'created_at': log.created_at.isoformat() if log.created_at else None
        }
    
    def _event_to_dict(self, event: SecurityEvent) -> Dict[str, Any]:
        """将安全事件转换为字典"""
        return {
            'id': event.id,
            'event_type': event.event_type,
            'event_level': event.event_level,
            'event_title': event.event_title,
            'event_description': event.event_description,
            'user_id': event.user_id,
            'username': event.username,
            'user_ip': event.user_ip,
            'threat_score': event.threat_score,
            'status': event.status,
            'handled_by': event.handled_by,
            'handled_at': event.handled_at.isoformat() if event.handled_at else None,
            'created_at': event.created_at.isoformat() if event.created_at else None
        }


# 全局审计服务实例
platform_audit_service = PlatformAuditService()
