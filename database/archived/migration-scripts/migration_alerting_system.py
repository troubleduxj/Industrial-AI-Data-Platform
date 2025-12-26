#!/usr/bin/env python3
"""
数据库迁移监控和告警系统
提供实时监控、智能告警、自动恢复和通知机制
"""

import asyncio
import json
import logging
import time
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import asyncpg
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import aiohttp
import threading

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_alerting.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """告警严重程度枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertType(Enum):
    """告警类型枚举"""
    MIGRATION_FAILURE = "migration_failure"
    CONSISTENCY_ISSUE = "consistency_issue"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    DUAL_WRITE_ERROR = "dual_write_error"
    SWITCH_FAILURE = "switch_failure"
    THRESHOLD_EXCEEDED = "threshold_exceeded"
    SYSTEM_ERROR = "system_error"
    RECOVERY_SUCCESS = "recovery_success"

class AlertStatus(Enum):
    """告警状态枚举"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

class NotificationChannel(Enum):
    """通知渠道枚举"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SMS = "sms"
    SLACK = "slack"
    DINGTALK = "dingtalk"

@dataclass
class AlertRule:
    """告警规则"""
    rule_id: str
    rule_name: str
    alert_type: AlertType
    severity: AlertSeverity
    condition: str  # SQL条件或Python表达式
    threshold: float
    duration: int  # 持续时间（秒）
    enabled: bool = True
    notification_channels: List[NotificationChannel] = None
    suppression_duration: int = 300  # 抑制时间（秒）
    auto_recovery: bool = False
    recovery_action: str = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.notification_channels is None:
            self.notification_channels = [NotificationChannel.EMAIL]
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class Alert:
    """告警实例"""
    alert_id: str
    rule_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    details: Dict[str, Any]
    status: AlertStatus = AlertStatus.ACTIVE
    first_occurred: datetime = None
    last_occurred: datetime = None
    acknowledged_at: datetime = None
    resolved_at: datetime = None
    acknowledged_by: str = None
    resolved_by: str = None
    notification_sent: bool = False
    recovery_attempted: bool = False
    
    def __post_init__(self):
        if self.first_occurred is None:
            self.first_occurred = datetime.now()
        if self.last_occurred is None:
            self.last_occurred = datetime.now()

@dataclass
class NotificationConfig:
    """通知配置"""
    channel: NotificationChannel
    enabled: bool = True
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}

class MigrationAlertingSystem:
    """迁移告警系统"""
    
    def __init__(self, db_url: str, config_file: str = None):
        self.db_url = db_url
        self.connection: Optional[asyncpg.Connection] = None
        self.config_file = config_file or "database/alerting_config.json"
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.notification_configs: Dict[NotificationChannel, NotificationConfig] = {}
        self.monitoring_active = False
        self.recovery_handlers: Dict[str, Callable] = {}
        
        # 线程锁
        self._lock = threading.RLock()
        
        # 加载配置
        self._load_configurations()
    
    def _load_configurations(self):
        """加载告警配置"""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 加载告警规则
                for rule_data in data.get('alert_rules', []):
                    rule = AlertRule(**rule_data)
                    rule.alert_type = AlertType(rule_data['alert_type'])
                    rule.severity = AlertSeverity(rule_data['severity'])
                    rule.notification_channels = [
                        NotificationChannel(ch) for ch in rule_data.get('notification_channels', ['email'])
                    ]
                    self.alert_rules[rule.rule_id] = rule
                
                # 加载通知配置
                for channel_data in data.get('notification_configs', []):
                    channel = NotificationChannel(channel_data['channel'])
                    config = NotificationConfig(**channel_data)
                    config.channel = channel
                    self.notification_configs[channel] = config
                    
                logger.info(f"加载了 {len(self.alert_rules)} 个告警规则和 {len(self.notification_configs)} 个通知配置")
            else:
                logger.warning(f"配置文件不存在: {config_path}")
                self._create_default_configs()
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            self._create_default_configs()
    
    def _create_default_configs(self):
        """创建默认配置"""
        # 创建默认告警规则
        default_rules = [
            AlertRule(
                rule_id="migration_failure_rule",
                rule_name="迁移失败告警",
                alert_type=AlertType.MIGRATION_FAILURE,
                severity=AlertSeverity.CRITICAL,
                condition="SELECT COUNT(*) FROM t_sys_migration_logs WHERE status = 'failed' AND created_at > NOW() - INTERVAL '5 minutes'",
                threshold=1.0,
                duration=60,
                auto_recovery=True,
                recovery_action="retry_failed_migrations"
            ),
            AlertRule(
                rule_id="consistency_issue_rule",
                rule_name="数据一致性问题告警",
                alert_type=AlertType.CONSISTENCY_ISSUE,
                severity=AlertSeverity.ERROR,
                condition="SELECT AVG(consistency_ratio) FROM t_sys_consistency_checks WHERE created_at > NOW() - INTERVAL '10 minutes'",
                threshold=0.95,
                duration=300
            ),
            AlertRule(
                rule_id="dual_write_error_rule",
                rule_name="双写错误告警",
                alert_type=AlertType.DUAL_WRITE_ERROR,
                severity=AlertSeverity.WARNING,
                condition="SELECT COUNT(*) FROM t_sys_dual_write_logs WHERE (source_success = FALSE OR target_success = FALSE) AND created_at > NOW() - INTERVAL '5 minutes'",
                threshold=10.0,
                duration=120
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.rule_id] = rule
        
        # 创建默认通知配置
        self.notification_configs[NotificationChannel.EMAIL] = NotificationConfig(
            channel=NotificationChannel.EMAIL,
            config={
                "smtp_server": "smtp.example.com",
                "smtp_port": 587,
                "username": "alert@example.com",
                "password": "password",
                "from_email": "alert@example.com",
                "to_emails": ["admin@example.com"],
                "use_tls": True
            }
        )
    
    def _save_configurations(self):
        """保存告警配置"""
        try:
            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'alert_rules': [
                    {
                        **asdict(rule),
                        'alert_type': rule.alert_type.value,
                        'severity': rule.severity.value,
                        'notification_channels': [ch.value for ch in rule.notification_channels]
                    }
                    for rule in self.alert_rules.values()
                ],
                'notification_configs': [
                    {
                        **asdict(config),
                        'channel': config.channel.value
                    }
                    for config in self.notification_configs.values()
                ],
                'updated_at': datetime.now().isoformat()
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                
            logger.info(f"配置已保存到: {config_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    async def connect(self):
        """连接数据库"""
        try:
            self.connection = await asyncpg.connect(self.db_url)
            await self._initialize_alerting_tables()
            logger.info("迁移告警系统数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    async def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            await self.connection.close()
            logger.info("迁移告警系统数据库连接已关闭")
    
    async def _initialize_alerting_tables(self):
        """初始化告警相关表"""
        # 创建告警规则表
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS t_sys_alert_rules (
                id BIGSERIAL PRIMARY KEY,
                rule_id VARCHAR(100) NOT NULL UNIQUE,
                rule_name VARCHAR(200) NOT NULL,
                alert_type VARCHAR(50) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                condition_sql TEXT NOT NULL,
                threshold_value DECIMAL(10,4) NOT NULL,
                duration_seconds INTEGER NOT NULL,
                enabled BOOLEAN DEFAULT TRUE,
                notification_channels JSONB DEFAULT '["email"]',
                suppression_duration INTEGER DEFAULT 300,
                auto_recovery BOOLEAN DEFAULT FALSE,
                recovery_action VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                CONSTRAINT chk_alert_type CHECK (alert_type IN ('migration_failure', 'consistency_issue', 'performance_degradation', 'dual_write_error', 'switch_failure', 'threshold_exceeded', 'system_error', 'recovery_success')),
                CONSTRAINT chk_severity CHECK (severity IN ('info', 'warning', 'error', 'critical'))
            );
            
            CREATE INDEX IF NOT EXISTS idx_alert_rules_id ON t_sys_alert_rules(rule_id);
            CREATE INDEX IF NOT EXISTS idx_alert_rules_type ON t_sys_alert_rules(alert_type);
            CREATE INDEX IF NOT EXISTS idx_alert_rules_enabled ON t_sys_alert_rules(enabled);
        """)
        
        # 创建告警实例表
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS t_sys_alerts (
                id BIGSERIAL PRIMARY KEY,
                alert_id VARCHAR(100) NOT NULL UNIQUE,
                rule_id VARCHAR(100) NOT NULL,
                alert_type VARCHAR(50) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                title VARCHAR(500) NOT NULL,
                message TEXT NOT NULL,
                details JSONB,
                status VARCHAR(20) DEFAULT 'active',
                first_occurred TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_occurred TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acknowledged_at TIMESTAMP NULL,
                resolved_at TIMESTAMP NULL,
                acknowledged_by VARCHAR(100),
                resolved_by VARCHAR(100),
                notification_sent BOOLEAN DEFAULT FALSE,
                recovery_attempted BOOLEAN DEFAULT FALSE,
                
                FOREIGN KEY (rule_id) REFERENCES t_sys_alert_rules(rule_id),
                CONSTRAINT chk_alert_status CHECK (status IN ('active', 'acknowledged', 'resolved', 'suppressed'))
            );
            
            CREATE INDEX IF NOT EXISTS idx_alerts_id ON t_sys_alerts(alert_id);
            CREATE INDEX IF NOT EXISTS idx_alerts_rule ON t_sys_alerts(rule_id);
            CREATE INDEX IF NOT EXISTS idx_alerts_type ON t_sys_alerts(alert_type);
            CREATE INDEX IF NOT EXISTS idx_alerts_severity ON t_sys_alerts(severity);
            CREATE INDEX IF NOT EXISTS idx_alerts_status ON t_sys_alerts(status);
            CREATE INDEX IF NOT EXISTS idx_alerts_occurred ON t_sys_alerts(first_occurred);
        """)
        
        # 创建通知记录表
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS t_sys_alert_notifications (
                id BIGSERIAL PRIMARY KEY,
                alert_id VARCHAR(100) NOT NULL,
                channel VARCHAR(20) NOT NULL,
                recipient VARCHAR(200) NOT NULL,
                subject VARCHAR(500),
                content TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT,
                
                FOREIGN KEY (alert_id) REFERENCES t_sys_alerts(alert_id),
                CONSTRAINT chk_notification_channel CHECK (channel IN ('email', 'webhook', 'sms', 'slack', 'dingtalk'))
            );
            
            CREATE INDEX IF NOT EXISTS idx_alert_notifications_alert ON t_sys_alert_notifications(alert_id);
            CREATE INDEX IF NOT EXISTS idx_alert_notifications_channel ON t_sys_alert_notifications(channel);
            CREATE INDEX IF NOT EXISTS idx_alert_notifications_sent ON t_sys_alert_notifications(sent_at);
        """)
    
    async def register_alert_rule(self, rule: AlertRule) -> bool:
        """注册告警规则"""
        try:
            with self._lock:
                self.alert_rules[rule.rule_id] = rule
            
            # 保存到数据库
            await self.connection.execute("""
                INSERT INTO t_sys_alert_rules 
                (rule_id, rule_name, alert_type, severity, condition_sql, threshold_value,
                 duration_seconds, enabled, notification_channels, suppression_duration,
                 auto_recovery, recovery_action)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (rule_id) DO UPDATE SET
                    rule_name = EXCLUDED.rule_name,
                    alert_type = EXCLUDED.alert_type,
                    severity = EXCLUDED.severity,
                    condition_sql = EXCLUDED.condition_sql,
                    threshold_value = EXCLUDED.threshold_value,
                    duration_seconds = EXCLUDED.duration_seconds,
                    enabled = EXCLUDED.enabled,
                    notification_channels = EXCLUDED.notification_channels,
                    suppression_duration = EXCLUDED.suppression_duration,
                    auto_recovery = EXCLUDED.auto_recovery,
                    recovery_action = EXCLUDED.recovery_action,
                    updated_at = CURRENT_TIMESTAMP
            """, 
                rule.rule_id, rule.rule_name, rule.alert_type.value, rule.severity.value,
                rule.condition, rule.threshold, rule.duration, rule.enabled,
                json.dumps([ch.value for ch in rule.notification_channels]),
                rule.suppression_duration, rule.auto_recovery, rule.recovery_action
            )
            
            self._save_configurations()
            logger.info(f"告警规则已注册: {rule.rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"注册告警规则失败: {e}")
            return False
    
    def register_recovery_handler(self, action_name: str, handler: Callable):
        """注册恢复处理器"""
        self.recovery_handlers[action_name] = handler
        logger.info(f"恢复处理器已注册: {action_name}")
    
    async def start_monitoring(self, check_interval: int = 60):
        """开始监控"""
        logger.info(f"开始迁移告警监控，检查间隔: {check_interval}秒")
        self.monitoring_active = True
        
        try:
            while self.monitoring_active:
                await self._check_alert_rules()
                await self._process_active_alerts()
                await self._cleanup_resolved_alerts()
                await asyncio.sleep(check_interval)
                
        except Exception as e:
            logger.error(f"监控过程中发生错误: {e}")
        finally:
            self.monitoring_active = False
    
    def stop_monitoring(self):
        """停止监控"""
        logger.info("停止迁移告警监控")
        self.monitoring_active = False
    
    async def _check_alert_rules(self):
        """检查告警规则"""
        try:
            for rule in self.alert_rules.values():
                if not rule.enabled:
                    continue
                
                try:
                    # 执行条件查询
                    result = await self.connection.fetchval(rule.condition)
                    
                    # 检查阈值
                    triggered = False
                    if rule.alert_type in [AlertType.CONSISTENCY_ISSUE]:
                        # 对于一致性问题，值低于阈值时触发
                        triggered = result < rule.threshold
                    else:
                        # 对于其他类型，值高于阈值时触发
                        triggered = result > rule.threshold
                    
                    if triggered:
                        await self._trigger_alert(rule, result)
                    else:
                        await self._resolve_alert_if_exists(rule.rule_id)
                        
                except Exception as e:
                    logger.error(f"检查告警规则失败 {rule.rule_id}: {e}")
                    
        except Exception as e:
            logger.error(f"检查告警规则失败: {e}")
    
    async def _trigger_alert(self, rule: AlertRule, trigger_value: float):
        """触发告警"""
        try:
            # 检查是否已存在活跃告警
            existing_alert = None
            for alert in self.active_alerts.values():
                if alert.rule_id == rule.rule_id and alert.status == AlertStatus.ACTIVE:
                    existing_alert = alert
                    break
            
            if existing_alert:
                # 更新现有告警的最后发生时间
                existing_alert.last_occurred = datetime.now()
                await self._update_alert_in_db(existing_alert)
                return
            
            # 创建新告警
            alert_id = f"alert_{rule.rule_id}_{int(time.time())}"
            
            alert = Alert(
                alert_id=alert_id,
                rule_id=rule.rule_id,
                alert_type=rule.alert_type,
                severity=rule.severity,
                title=f"{rule.rule_name}",
                message=f"触发条件: {rule.condition}, 当前值: {trigger_value}, 阈值: {rule.threshold}",
                details={
                    'trigger_value': trigger_value,
                    'threshold': rule.threshold,
                    'condition': rule.condition,
                    'rule_name': rule.rule_name
                }
            )
            
            with self._lock:
                self.active_alerts[alert_id] = alert
            
            # 保存到数据库
            await self._save_alert_to_db(alert)
            
            # 发送通知
            await self._send_notifications(alert, rule)
            
            # 尝试自动恢复
            if rule.auto_recovery and rule.recovery_action:
                await self._attempt_auto_recovery(alert, rule)
            
            logger.warning(f"告警已触发: {alert.title}")
            
        except Exception as e:
            logger.error(f"触发告警失败: {e}")
    
    async def _resolve_alert_if_exists(self, rule_id: str):
        """如果存在则解决告警"""
        try:
            for alert_id, alert in list(self.active_alerts.items()):
                if alert.rule_id == rule_id and alert.status == AlertStatus.ACTIVE:
                    alert.status = AlertStatus.RESOLVED
                    alert.resolved_at = datetime.now()
                    alert.resolved_by = "system"
                    
                    await self._update_alert_in_db(alert)
                    
                    # 发送恢复通知
                    await self._send_recovery_notification(alert)
                    
                    logger.info(f"告警已自动解决: {alert.title}")
                    break
                    
        except Exception as e:
            logger.error(f"解决告警失败: {e}")
    
    async def _save_alert_to_db(self, alert: Alert):
        """保存告警到数据库"""
        try:
            await self.connection.execute("""
                INSERT INTO t_sys_alerts 
                (alert_id, rule_id, alert_type, severity, title, message, details,
                 status, first_occurred, last_occurred, notification_sent, recovery_attempted)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """, 
                alert.alert_id, alert.rule_id, alert.alert_type.value, alert.severity.value,
                alert.title, alert.message, json.dumps(alert.details),
                alert.status.value, alert.first_occurred, alert.last_occurred,
                alert.notification_sent, alert.recovery_attempted
            )
            
        except Exception as e:
            logger.error(f"保存告警到数据库失败: {e}")
    
    async def _update_alert_in_db(self, alert: Alert):
        """更新数据库中的告警"""
        try:
            await self.connection.execute("""
                UPDATE t_sys_alerts SET
                    status = $1,
                    last_occurred = $2,
                    acknowledged_at = $3,
                    resolved_at = $4,
                    acknowledged_by = $5,
                    resolved_by = $6,
                    notification_sent = $7,
                    recovery_attempted = $8
                WHERE alert_id = $9
            """, 
                alert.status.value, alert.last_occurred, alert.acknowledged_at,
                alert.resolved_at, alert.acknowledged_by, alert.resolved_by,
                alert.notification_sent, alert.recovery_attempted, alert.alert_id
            )
            
        except Exception as e:
            logger.error(f"更新告警失败: {e}")
    
    async def _send_notifications(self, alert: Alert, rule: AlertRule):
        """发送通知"""
        try:
            for channel in rule.notification_channels:
                if channel in self.notification_configs:
                    config = self.notification_configs[channel]
                    if config.enabled:
                        await self._send_notification(alert, channel, config)
            
            alert.notification_sent = True
            await self._update_alert_in_db(alert)
            
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
    
    async def _send_notification(self, alert: Alert, channel: NotificationChannel, 
                               config: NotificationConfig):
        """发送单个通知"""
        try:
            if channel == NotificationChannel.EMAIL:
                await self._send_email_notification(alert, config)
            elif channel == NotificationChannel.WEBHOOK:
                await self._send_webhook_notification(alert, config)
            elif channel == NotificationChannel.SLACK:
                await self._send_slack_notification(alert, config)
            elif channel == NotificationChannel.DINGTALK:
                await self._send_dingtalk_notification(alert, config)
            
            # 记录通知发送
            await self._record_notification(alert, channel, True)
            
        except Exception as e:
            logger.error(f"发送 {channel.value} 通知失败: {e}")
            await self._record_notification(alert, channel, False, str(e))
    
    async def _send_email_notification(self, alert: Alert, config: NotificationConfig):
        """发送邮件通知"""
        try:
            email_config = config.config
            
            # 创建邮件内容
            msg = MimeMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = ', '.join(email_config['to_emails'])
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            # 邮件正文
            body = f"""
数据库迁移告警通知

告警ID: {alert.alert_id}
告警类型: {alert.alert_type.value}
严重程度: {alert.severity.value}
告警标题: {alert.title}
告警消息: {alert.message}
首次发生: {alert.first_occurred.strftime('%Y-%m-%d %H:%M:%S')}
最后发生: {alert.last_occurred.strftime('%Y-%m-%d %H:%M:%S')}

详细信息:
{json.dumps(alert.details, indent=2, ensure_ascii=False)}

请及时处理相关问题。

此邮件由数据库迁移告警系统自动发送。
            """
            
            msg.attach(MimeText(body, 'plain', 'utf-8'))
            
            # 发送邮件
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            if email_config.get('use_tls', True):
                server.starttls()
            if email_config.get('username') and email_config.get('password'):
                server.login(email_config['username'], email_config['password'])
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"邮件通知发送成功: {alert.alert_id}")
            
        except Exception as e:
            logger.error(f"发送邮件通知失败: {e}")
            raise
    
    async def _send_webhook_notification(self, alert: Alert, config: NotificationConfig):
        """发送Webhook通知"""
        try:
            webhook_config = config.config
            
            payload = {
                'alert_id': alert.alert_id,
                'rule_id': alert.rule_id,
                'alert_type': alert.alert_type.value,
                'severity': alert.severity.value,
                'title': alert.title,
                'message': alert.message,
                'details': alert.details,
                'status': alert.status.value,
                'first_occurred': alert.first_occurred.isoformat(),
                'last_occurred': alert.last_occurred.isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_config['url'],
                    json=payload,
                    headers=webhook_config.get('headers', {}),
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook通知发送成功: {alert.alert_id}")
                    else:
                        raise Exception(f"HTTP {response.status}")
                        
        except Exception as e:
            logger.error(f"发送Webhook通知失败: {e}")
            raise
    
    async def _send_slack_notification(self, alert: Alert, config: NotificationConfig):
        """发送Slack通知"""
        try:
            slack_config = config.config
            
            color_map = {
                AlertSeverity.INFO: "good",
                AlertSeverity.WARNING: "warning", 
                AlertSeverity.ERROR: "danger",
                AlertSeverity.CRITICAL: "danger"
            }
            
            payload = {
                "attachments": [
                    {
                        "color": color_map.get(alert.severity, "warning"),
                        "title": alert.title,
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "告警ID",
                                "value": alert.alert_id,
                                "short": True
                            },
                            {
                                "title": "严重程度",
                                "value": alert.severity.value.upper(),
                                "short": True
                            },
                            {
                                "title": "告警类型",
                                "value": alert.alert_type.value,
                                "short": True
                            },
                            {
                                "title": "发生时间",
                                "value": alert.first_occurred.strftime('%Y-%m-%d %H:%M:%S'),
                                "short": True
                            }
                        ],
                        "ts": int(alert.first_occurred.timestamp())
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    slack_config['webhook_url'],
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Slack通知发送成功: {alert.alert_id}")
                    else:
                        raise Exception(f"HTTP {response.status}")
                        
        except Exception as e:
            logger.error(f"发送Slack通知失败: {e}")
            raise
    
    async def _send_dingtalk_notification(self, alert: Alert, config: NotificationConfig):
        """发送钉钉通知"""
        try:
            dingtalk_config = config.config
            
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": f"数据库迁移告警: {alert.title}",
                    "text": f"""
## 数据库迁移告警

**告警ID**: {alert.alert_id}

**告警类型**: {alert.alert_type.value}

**严重程度**: {alert.severity.value.upper()}

**告警标题**: {alert.title}

**告警消息**: {alert.message}

**发生时间**: {alert.first_occurred.strftime('%Y-%m-%d %H:%M:%S')}

**详细信息**: 
```json
{json.dumps(alert.details, indent=2, ensure_ascii=False)}
```

请及时处理相关问题。
                    """
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    dingtalk_config['webhook_url'],
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"钉钉通知发送成功: {alert.alert_id}")
                    else:
                        raise Exception(f"HTTP {response.status}")
                        
        except Exception as e:
            logger.error(f"发送钉钉通知失败: {e}")
            raise
    
    async def _record_notification(self, alert: Alert, channel: NotificationChannel,
                                 success: bool, error_message: str = None):
        """记录通知发送结果"""
        try:
            config = self.notification_configs.get(channel)
            recipient = "unknown"
            
            if config and config.config:
                if channel == NotificationChannel.EMAIL:
                    recipient = ', '.join(config.config.get('to_emails', []))
                elif channel in [NotificationChannel.WEBHOOK, NotificationChannel.SLACK, NotificationChannel.DINGTALK]:
                    recipient = config.config.get('webhook_url', config.config.get('url', 'webhook'))
            
            await self.connection.execute("""
                INSERT INTO t_sys_alert_notifications 
                (alert_id, channel, recipient, subject, content, success, error_message)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, 
                alert.alert_id, channel.value, recipient, alert.title, alert.message,
                success, error_message
            )
            
        except Exception as e:
            logger.error(f"记录通知结果失败: {e}")
    
    async def _send_recovery_notification(self, alert: Alert):
        """发送恢复通知"""
        try:
            rule = self.alert_rules.get(alert.rule_id)
            if not rule:
                return
            
            # 创建恢复通知
            recovery_alert = Alert(
                alert_id=f"recovery_{alert.alert_id}",
                rule_id=alert.rule_id,
                alert_type=AlertType.RECOVERY_SUCCESS,
                severity=AlertSeverity.INFO,
                title=f"告警已恢复: {alert.title}",
                message=f"原告警已自动恢复，告警ID: {alert.alert_id}",
                details={
                    'original_alert_id': alert.alert_id,
                    'recovery_time': datetime.now().isoformat()
                }
            )
            
            await self._send_notifications(recovery_alert, rule)
            
        except Exception as e:
            logger.error(f"发送恢复通知失败: {e}")
    
    async def _attempt_auto_recovery(self, alert: Alert, rule: AlertRule):
        """尝试自动恢复"""
        try:
            if not rule.recovery_action or alert.recovery_attempted:
                return
            
            alert.recovery_attempted = True
            await self._update_alert_in_db(alert)
            
            # 执行恢复操作
            if rule.recovery_action in self.recovery_handlers:
                handler = self.recovery_handlers[rule.recovery_action]
                success = await handler(alert, rule)
                
                if success:
                    logger.info(f"自动恢复成功: {alert.alert_id}")
                    alert.status = AlertStatus.RESOLVED
                    alert.resolved_at = datetime.now()
                    alert.resolved_by = "auto_recovery"
                    await self._update_alert_in_db(alert)
                else:
                    logger.warning(f"自动恢复失败: {alert.alert_id}")
            else:
                logger.warning(f"未找到恢复处理器: {rule.recovery_action}")
                
        except Exception as e:
            logger.error(f"自动恢复失败: {e}")
    
    async def _process_active_alerts(self):
        """处理活跃告警"""
        try:
            current_time = datetime.now()
            
            for alert in list(self.active_alerts.values()):
                # 检查告警抑制
                rule = self.alert_rules.get(alert.rule_id)
                if rule and alert.status == AlertStatus.ACTIVE:
                    time_since_last = (current_time - alert.last_occurred).total_seconds()
                    if time_since_last > rule.suppression_duration:
                        alert.status = AlertStatus.SUPPRESSED
                        await self._update_alert_in_db(alert)
                        
        except Exception as e:
            logger.error(f"处理活跃告警失败: {e}")
    
    async def _cleanup_resolved_alerts(self):
        """清理已解决的告警"""
        try:
            current_time = datetime.now()
            cleanup_threshold = current_time - timedelta(hours=24)
            
            # 从内存中移除旧的已解决告警
            to_remove = []
            for alert_id, alert in self.active_alerts.items():
                if (alert.status in [AlertStatus.RESOLVED, AlertStatus.SUPPRESSED] and
                    alert.resolved_at and alert.resolved_at < cleanup_threshold):
                    to_remove.append(alert_id)
            
            for alert_id in to_remove:
                del self.active_alerts[alert_id]
            
            if to_remove:
                logger.info(f"清理了 {len(to_remove)} 个已解决的告警")
                
        except Exception as e:
            logger.error(f"清理已解决告警失败: {e}")
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """确认告警"""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.now()
                alert.acknowledged_by = acknowledged_by
                
                await self._update_alert_in_db(alert)
                logger.info(f"告警已确认: {alert_id} by {acknowledged_by}")
                return True
            else:
                logger.warning(f"告警不存在: {alert_id}")
                return False
                
        except Exception as e:
            logger.error(f"确认告警失败: {e}")
            return False
    
    async def resolve_alert(self, alert_id: str, resolved_by: str) -> bool:
        """解决告警"""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.now()
                alert.resolved_by = resolved_by
                
                await self._update_alert_in_db(alert)
                await self._send_recovery_notification(alert)
                
                logger.info(f"告警已解决: {alert_id} by {resolved_by}")
                return True
            else:
                logger.warning(f"告警不存在: {alert_id}")
                return False
                
        except Exception as e:
            logger.error(f"解决告警失败: {e}")
            return False
    
    async def get_active_alerts(self, severity: AlertSeverity = None, 
                              alert_type: AlertType = None) -> List[Dict[str, Any]]:
        """获取活跃告警"""
        try:
            alerts = []
            for alert in self.active_alerts.values():
                if alert.status == AlertStatus.ACTIVE:
                    if severity and alert.severity != severity:
                        continue
                    if alert_type and alert.alert_type != alert_type:
                        continue
                    alerts.append(asdict(alert))
            
            return sorted(alerts, key=lambda x: x['first_occurred'], reverse=True)
            
        except Exception as e:
            logger.error(f"获取活跃告警失败: {e}")
            return []
    
    async def get_alert_statistics(self, days: int = 7) -> Dict[str, Any]:
        """获取告警统计"""
        try:
            stats = await self.connection.fetchrow("""
                SELECT 
                    COUNT(*) as total_alerts,
                    COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_alerts,
                    COUNT(CASE WHEN severity = 'error' THEN 1 END) as error_alerts,
                    COUNT(CASE WHEN severity = 'warning' THEN 1 END) as warning_alerts,
                    COUNT(CASE WHEN severity = 'info' THEN 1 END) as info_alerts,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_alerts,
                    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_alerts,
                    AVG(EXTRACT(EPOCH FROM (COALESCE(resolved_at, NOW()) - first_occurred))) as avg_resolution_time
                FROM t_sys_alerts
                WHERE first_occurred > NOW() - INTERVAL '%s days'
            """ % days)
            
            # 按类型统计
            type_stats = await self.connection.fetch("""
                SELECT 
                    alert_type,
                    COUNT(*) as count,
                    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_count
                FROM t_sys_alerts
                WHERE first_occurred > NOW() - INTERVAL '%s days'
                GROUP BY alert_type
                ORDER BY count DESC
            """ % days)
            
            # 按时间统计
            hourly_stats = await self.connection.fetch("""
                SELECT 
                    DATE_TRUNC('hour', first_occurred) as hour,
                    COUNT(*) as alert_count
                FROM t_sys_alerts
                WHERE first_occurred > NOW() - INTERVAL '%s days'
                GROUP BY DATE_TRUNC('hour', first_occurred)
                ORDER BY hour DESC
                LIMIT 24
            """ % days)
            
            return {
                'overall_stats': dict(stats) if stats else {},
                'type_statistics': [dict(t) for t in type_stats],
                'hourly_statistics': [dict(h) for h in hourly_stats],
                'time_range_days': days,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取告警统计失败: {e}")
            return {}
    
    async def export_alert_report(self, days: int = 7, output_file: str = None) -> str:
        """导出告警报告"""
        if output_file is None:
            output_file = f"alert_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            # 获取告警统计
            statistics = await self.get_alert_statistics(days)
            
            # 获取活跃告警
            active_alerts = await self.get_active_alerts()
            
            # 获取最近的告警
            recent_alerts = await self.connection.fetch("""
                SELECT * FROM t_sys_alerts
                WHERE first_occurred > NOW() - INTERVAL '%s days'
                ORDER BY first_occurred DESC
                LIMIT 100
            """ % days)
            
            # 构建报告
            report = {
                'alert_statistics': statistics,
                'active_alerts': active_alerts,
                'recent_alerts': [dict(alert) for alert in recent_alerts],
                'alert_rules': [asdict(rule) for rule in self.alert_rules.values()],
                'export_time': datetime.now().isoformat()
            }
            
            # 保存到文件
            output_path = Path(output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"告警报告已导出: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"导出告警报告失败: {e}")
            return ""

# 默认配置示例
DEFAULT_ALERTING_CONFIG = {
    "alert_rules": [
        {
            "rule_id": "migration_failure_rule",
            "rule_name": "迁移失败告警",
            "alert_type": "migration_failure",
            "severity": "critical",
            "condition": "SELECT COUNT(*) FROM t_sys_migration_logs WHERE status = 'failed' AND created_at > NOW() - INTERVAL '5 minutes'",
            "threshold": 1.0,
            "duration": 60,
            "enabled": True,
            "notification_channels": ["email"],
            "suppression_duration": 300,
            "auto_recovery": True,
            "recovery_action": "retry_failed_migrations"
        }
    ],
    "notification_configs": [
        {
            "channel": "email",
            "enabled": True,
            "config": {
                "smtp_server": "smtp.example.com",
                "smtp_port": 587,
                "username": "alert@example.com",
                "password": "password",
                "from_email": "alert@example.com",
                "to_emails": ["admin@example.com"],
                "use_tls": True
            }
        }
    ]
}

async def main():
    """主函数示例"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库迁移告警系统')
    parser.add_argument('--db-url', required=True, help='数据库连接URL')
    parser.add_argument('--config-file', help='配置文件路径')
    parser.add_argument('--action', 
                       choices=['monitor', 'status', 'acknowledge', 'resolve', 'statistics', 'export'],
                       default='monitor', help='执行的操作')
    parser.add_argument('--alert-id', help='告警ID')
    parser.add_argument('--user', help='操作用户')
    parser.add_argument('--days', type=int, default=7, help='统计天数')
    parser.add_argument('--output', help='输出文件路径')
    
    args = parser.parse_args()
    
    alerting_system = MigrationAlertingSystem(args.db_url, args.config_file)
    
    try:
        await alerting_system.connect()
        
        if args.action == 'monitor':
            try:
                await alerting_system.start_monitoring()
            except KeyboardInterrupt:
                alerting_system.stop_monitoring()
                print("监控已停止")
        
        elif args.action == 'status':
            active_alerts = await alerting_system.get_active_alerts()
            print(f"活跃告警数量: {len(active_alerts)}")
            for alert in active_alerts:
                print(f"- {alert['alert_id']}: {alert['title']} ({alert['severity']})")
        
        elif args.action == 'acknowledge':
            if not args.alert_id or not args.user:
                print("需要指定 --alert-id 和 --user")
                return
            success = await alerting_system.acknowledge_alert(args.alert_id, args.user)
            print(f"确认告警: {'成功' if success else '失败'}")
        
        elif args.action == 'resolve':
            if not args.alert_id or not args.user:
                print("需要指定 --alert-id 和 --user")
                return
            success = await alerting_system.resolve_alert(args.alert_id, args.user)
            print(f"解决告警: {'成功' if success else '失败'}")
        
        elif args.action == 'statistics':
            stats = await alerting_system.get_alert_statistics(args.days)
            print(json.dumps(stats, indent=2, ensure_ascii=False, default=str))
        
        elif args.action == 'export':
            report_file = await alerting_system.export_alert_report(args.days, args.output)
            print(f"报告已导出: {report_file}")
    
    finally:
        await alerting_system.disconnect()

if __name__ == "__main__":
    asyncio.run(main())