"""
安全监控和日志记录模块
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import Request


class SecurityEventType(Enum):
    """安全事件类型"""
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    XSS_ATTACK_DETECTED = "xss_attack_detected"
    SQL_INJECTION_DETECTED = "sql_injection_detected"
    MALICIOUS_INPUT_DETECTED = "malicious_input_detected"
    SUSPICIOUS_REQUEST = "suspicious_request"
    AUTHENTICATION_FAILURE = "authentication_failure"
    PERMISSION_DENIED = "permission_denied"
    UNUSUAL_ACTIVITY = "unusual_activity"


class SecurityLevel(Enum):
    """安全级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """安全事件数据结构"""
    event_type: SecurityEventType
    level: SecurityLevel
    timestamp: datetime
    client_ip: str
    user_agent: str
    path: str
    method: str
    details: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['level'] = self.level.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class SecurityMonitor:
    """安全监控器"""
    
    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self.events: deque = deque(maxlen=max_events)
        self.ip_stats: Dict[str, Dict] = defaultdict(lambda: {
            'request_count': 0,
            'blocked_count': 0,
            'last_activity': None,
            'event_types': defaultdict(int)
        })
        self.logger = logging.getLogger(__name__)
        
        # 配置安全日志格式
        security_handler = logging.StreamHandler()
        security_formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
        )
        security_handler.setFormatter(security_formatter)
        self.logger.addHandler(security_handler)
        self.logger.setLevel(logging.WARNING)
    
    def record_event(self, event: SecurityEvent):
        """记录安全事件"""
        # 添加到事件队列
        self.events.append(event)
        
        # 更新IP统计
        ip_stat = self.ip_stats[event.client_ip]
        ip_stat['request_count'] += 1
        ip_stat['last_activity'] = event.timestamp
        ip_stat['event_types'][event.event_type.value] += 1
        
        if event.level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            ip_stat['blocked_count'] += 1
        
        # 记录日志
        self._log_event(event)
        
        # 检查是否需要触发警报
        self._check_alert_conditions(event)
    
    def _log_event(self, event: SecurityEvent):
        """记录事件日志"""
        log_message = f"Security Event: {event.event_type.value} | IP: {event.client_ip} | Path: {event.path}"
        
        if event.level == SecurityLevel.LOW:
            self.logger.info(log_message)
        elif event.level == SecurityLevel.MEDIUM:
            self.logger.warning(log_message)
        elif event.level == SecurityLevel.HIGH:
            self.logger.error(log_message)
        elif event.level == SecurityLevel.CRITICAL:
            self.logger.critical(log_message)
        
        # 详细日志
        self.logger.debug(f"Security Event Details: {event.to_json()}")
    
    def _check_alert_conditions(self, event: SecurityEvent):
        """检查警报条件"""
        ip_stat = self.ip_stats[event.client_ip]
        
        # 检查短时间内的多次攻击
        recent_events = self.get_recent_events_by_ip(
            event.client_ip, 
            minutes=5
        )
        
        if len(recent_events) >= 10:
            self._trigger_alert(
                f"IP {event.client_ip} 在5分钟内触发了{len(recent_events)}次安全事件",
                SecurityLevel.CRITICAL
            )
        
        # 检查多种攻击类型
        if len(ip_stat['event_types']) >= 3:
            self._trigger_alert(
                f"IP {event.client_ip} 尝试了多种攻击类型: {list(ip_stat['event_types'].keys())}",
                SecurityLevel.HIGH
            )
    
    def _trigger_alert(self, message: str, level: SecurityLevel):
        """触发安全警报"""
        alert_message = f"SECURITY ALERT [{level.value.upper()}]: {message}"
        
        if level == SecurityLevel.CRITICAL:
            self.logger.critical(alert_message)
        else:
            self.logger.error(alert_message)
        
        # 这里可以添加其他警报机制，如发送邮件、短信等
        # self._send_email_alert(alert_message)
        # self._send_webhook_alert(alert_message)
    
    def get_recent_events(self, minutes: int = 60) -> List[SecurityEvent]:
        """获取最近的安全事件"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [
            event for event in self.events 
            if event.timestamp >= cutoff_time
        ]
    
    def get_recent_events_by_ip(self, ip: str, minutes: int = 60) -> List[SecurityEvent]:
        """获取特定IP的最近安全事件"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [
            event for event in self.events 
            if event.client_ip == ip and event.timestamp >= cutoff_time
        ]
    
    def get_ip_statistics(self, ip: str) -> Dict[str, Any]:
        """获取IP统计信息"""
        return dict(self.ip_stats[ip])
    
    def get_top_threat_ips(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取威胁最大的IP列表"""
        ip_threats = []
        
        for ip, stats in self.ip_stats.items():
            threat_score = (
                stats['blocked_count'] * 10 +  # 被阻止的请求权重更高
                len(stats['event_types']) * 5 +  # 攻击类型多样性
                stats['request_count']  # 总请求数
            )
            
            ip_threats.append({
                'ip': ip,
                'threat_score': threat_score,
                'blocked_count': stats['blocked_count'],
                'request_count': stats['request_count'],
                'event_types': dict(stats['event_types']),
                'last_activity': stats['last_activity'].isoformat() if stats['last_activity'] else None
            })
        
        return sorted(ip_threats, key=lambda x: x['threat_score'], reverse=True)[:limit]
    
    def get_security_summary(self) -> Dict[str, Any]:
        """获取安全摘要"""
        recent_events = self.get_recent_events(60)  # 最近1小时
        
        event_type_counts = defaultdict(int)
        level_counts = defaultdict(int)
        
        for event in recent_events:
            event_type_counts[event.event_type.value] += 1
            level_counts[event.level.value] += 1
        
        return {
            'total_events': len(self.events),
            'recent_events_count': len(recent_events),
            'unique_ips': len(self.ip_stats),
            'event_type_distribution': dict(event_type_counts),
            'level_distribution': dict(level_counts),
            'top_threat_ips': self.get_top_threat_ips(5)
        }
    
    def is_ip_suspicious(self, ip: str) -> bool:
        """判断IP是否可疑"""
        if ip not in self.ip_stats:
            return False
        
        stats = self.ip_stats[ip]
        
        # 可疑条件
        if stats['blocked_count'] > 5:  # 被阻止次数过多
            return True
        
        if len(stats['event_types']) >= 3:  # 攻击类型多样
            return True
        
        # 检查最近的活动频率
        recent_events = self.get_recent_events_by_ip(ip, 10)
        if len(recent_events) > 20:  # 10分钟内超过20次事件
            return True
        
        return False
    
    def cleanup_old_events(self, days: int = 7):
        """清理旧的安全事件"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # 清理事件队列中的旧事件
        self.events = deque([
            event for event in self.events 
            if event.timestamp >= cutoff_time
        ], maxlen=self.max_events)
        
        # 清理IP统计中的过期数据
        for ip, stats in list(self.ip_stats.items()):
            if stats['last_activity'] and stats['last_activity'] < cutoff_time:
                del self.ip_stats[ip]


class SecurityEventLogger:
    """安全事件记录器"""
    
    def __init__(self, monitor: SecurityMonitor):
        self.monitor = monitor
    
    def log_rate_limit_exceeded(self, request: Request, limit: int, window: int):
        """记录频率限制超出事件"""
        event = SecurityEvent(
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            level=SecurityLevel.MEDIUM,
            timestamp=datetime.now(),
            client_ip=self._get_client_ip(request),
            user_agent=request.headers.get('User-Agent', 'unknown'),
            path=request.url.path,
            method=request.method,
            details={
                'limit': limit,
                'window': window,
                'message': f'Rate limit exceeded: {limit} requests per {window} seconds'
            }
        )
        self.monitor.record_event(event)
    
    def log_xss_attack(self, request: Request, malicious_content: str):
        """记录XSS攻击事件"""
        event = SecurityEvent(
            event_type=SecurityEventType.XSS_ATTACK_DETECTED,
            level=SecurityLevel.HIGH,
            timestamp=datetime.now(),
            client_ip=self._get_client_ip(request),
            user_agent=request.headers.get('User-Agent', 'unknown'),
            path=request.url.path,
            method=request.method,
            details={
                'malicious_content': malicious_content[:500],  # 限制长度
                'message': 'XSS attack pattern detected in request'
            }
        )
        self.monitor.record_event(event)
    
    def log_sql_injection(self, request: Request, malicious_content: str):
        """记录SQL注入攻击事件"""
        event = SecurityEvent(
            event_type=SecurityEventType.SQL_INJECTION_DETECTED,
            level=SecurityLevel.HIGH,
            timestamp=datetime.now(),
            client_ip=self._get_client_ip(request),
            user_agent=request.headers.get('User-Agent', 'unknown'),
            path=request.url.path,
            method=request.method,
            details={
                'malicious_content': malicious_content[:500],
                'message': 'SQL injection pattern detected in request'
            }
        )
        self.monitor.record_event(event)
    
    def log_malicious_input(self, request: Request, input_data: str, attack_type: str):
        """记录恶意输入事件"""
        event = SecurityEvent(
            event_type=SecurityEventType.MALICIOUS_INPUT_DETECTED,
            level=SecurityLevel.MEDIUM,
            timestamp=datetime.now(),
            client_ip=self._get_client_ip(request),
            user_agent=request.headers.get('User-Agent', 'unknown'),
            path=request.url.path,
            method=request.method,
            details={
                'input_data': input_data[:500],
                'attack_type': attack_type,
                'message': f'Malicious input detected: {attack_type}'
            }
        )
        self.monitor.record_event(event)
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else '127.0.0.1'


# 全局安全监控实例
security_monitor = SecurityMonitor()
security_event_logger = SecurityEventLogger(security_monitor)