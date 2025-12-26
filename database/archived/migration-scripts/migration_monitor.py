#!/usr/bin/env python3
"""
数据库迁移监控和日志记录系统
实时监控迁移过程，记录详细日志，提供告警机制
"""

import asyncio
import json
import logging
import time
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import asyncpg
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MigrationAlert:
    """迁移告警数据结构"""
    alert_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    title: str
    message: str
    migration_id: Optional[str] = None
    timestamp: datetime = None
    resolved: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class MigrationMetrics:
    """迁移指标数据结构"""
    total_migrations: int = 0
    successful_migrations: int = 0
    failed_migrations: int = 0
    pending_migrations: int = 0
    rolled_back_migrations: int = 0
    avg_execution_time: float = 0.0
    total_execution_time: float = 0.0
    success_rate: float = 0.0
    last_migration_time: Optional[datetime] = None

class MigrationMonitor:
    """迁移监控器"""
    
    def __init__(self, db_url: str, config: Dict[str, Any] = None):
        self.db_url = db_url
        self.connection: Optional[asyncpg.Connection] = None
        self.config = config or {}
        self.alerts: List[MigrationAlert] = []
        self.metrics = MigrationMetrics()
        self.monitoring_active = False
        self.alert_handlers: List[Callable] = []
        
        # 配置告警阈值
        self.alert_thresholds = {
            'max_execution_time': self.config.get('max_execution_time', 300000),  # 5分钟
            'max_failure_rate': self.config.get('max_failure_rate', 0.1),  # 10%
            'max_pending_time': self.config.get('max_pending_time', 3600),  # 1小时
            'min_success_rate': self.config.get('min_success_rate', 0.9)  # 90%
        }
        
        # 配置通知设置
        self.notification_config = self.config.get('notifications', {})
        
        # 初始化告警处理器
        self._init_alert_handlers()
    
    def _init_alert_handlers(self):
        """初始化告警处理器"""
        # 邮件告警处理器
        if self.notification_config.get('email', {}).get('enabled', False):
            self.alert_handlers.append(self._send_email_alert)
        
        # 日志告警处理器
        self.alert_handlers.append(self._log_alert)
        
        # Webhook告警处理器
        if self.notification_config.get('webhook', {}).get('enabled', False):
            self.alert_handlers.append(self._send_webhook_alert)
    
    async def connect(self):
        """连接数据库"""
        try:
            self.connection = await asyncpg.connect(self.db_url)
            logger.info("监控器数据库连接成功")
        except Exception as e:
            logger.error(f"监控器数据库连接失败: {e}")
            raise
    
    async def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            await self.connection.close()
            logger.info("监控器数据库连接已关闭")
    
    async def start_monitoring(self, interval: int = 30):
        """开始监控"""
        logger.info(f"开始迁移监控，检查间隔: {interval}秒")
        self.monitoring_active = True
        
        try:
            await self.connect()
            
            while self.monitoring_active:
                await self._collect_metrics()
                await self._check_alerts()
                await asyncio.sleep(interval)
                
        except Exception as e:
            logger.error(f"监控过程中发生错误: {e}")
            await self._trigger_alert(MigrationAlert(
                alert_type="MONITOR_ERROR",
                severity="HIGH",
                title="监控系统错误",
                message=f"监控过程中发生错误: {str(e)}"
            ))
        finally:
            await self.disconnect()
    
    def stop_monitoring(self):
        """停止监控"""
        logger.info("停止迁移监控")
        self.monitoring_active = False
    
    async def _collect_metrics(self):
        """收集迁移指标"""
        try:
            # 查询迁移统计信息
            stats = await self.connection.fetchrow("""
                SELECT 
                    COUNT(*) as total_migrations,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_migrations,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_migrations,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_migrations,
                    COUNT(CASE WHEN status = 'rolled_back' THEN 1 END) as rolled_back_migrations,
                    AVG(execution_time_ms) as avg_execution_time,
                    SUM(execution_time_ms) as total_execution_time,
                    MAX(executed_at) as last_migration_time
                FROM t_sys_migration_logs
            """)
            
            if stats:
                self.metrics.total_migrations = stats['total_migrations'] or 0
                self.metrics.successful_migrations = stats['successful_migrations'] or 0
                self.metrics.failed_migrations = stats['failed_migrations'] or 0
                self.metrics.pending_migrations = stats['pending_migrations'] or 0
                self.metrics.rolled_back_migrations = stats['rolled_back_migrations'] or 0
                self.metrics.avg_execution_time = float(stats['avg_execution_time'] or 0)
                self.metrics.total_execution_time = float(stats['total_execution_time'] or 0)
                self.metrics.last_migration_time = stats['last_migration_time']
                
                # 计算成功率
                if self.metrics.total_migrations > 0:
                    self.metrics.success_rate = self.metrics.successful_migrations / self.metrics.total_migrations
                else:
                    self.metrics.success_rate = 0.0
            
            logger.debug(f"指标收集完成: {asdict(self.metrics)}")
            
        except Exception as e:
            logger.error(f"收集指标失败: {e}")
    
    async def _check_alerts(self):
        """检查告警条件"""
        try:
            # 检查执行时间过长的迁移
            await self._check_long_running_migrations()
            
            # 检查失败率过高
            await self._check_failure_rate()
            
            # 检查长时间未执行的待处理迁移
            await self._check_stale_pending_migrations()
            
            # 检查成功率过低
            await self._check_low_success_rate()
            
            # 检查数据库连接状态
            await self._check_database_health()
            
        except Exception as e:
            logger.error(f"检查告警失败: {e}")
    
    async def _check_long_running_migrations(self):
        """检查执行时间过长的迁移"""
        long_running = await self.connection.fetch("""
            SELECT migration_id, migration_name, execution_time_ms, executed_at
            FROM t_sys_migration_logs
            WHERE status = 'running' 
              AND (EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - executed_at)) * 1000) > $1
        """, self.alert_thresholds['max_execution_time'])
        
        for migration in long_running:
            await self._trigger_alert(MigrationAlert(
                alert_type="LONG_RUNNING_MIGRATION",
                severity="HIGH",
                title="迁移执行时间过长",
                message=f"迁移 {migration['migration_name']} 执行时间超过阈值",
                migration_id=migration['migration_id']
            ))
    
    async def _check_failure_rate(self):
        """检查失败率"""
        if self.metrics.total_migrations > 0:
            failure_rate = self.metrics.failed_migrations / self.metrics.total_migrations
            if failure_rate > self.alert_thresholds['max_failure_rate']:
                await self._trigger_alert(MigrationAlert(
                    alert_type="HIGH_FAILURE_RATE",
                    severity="CRITICAL",
                    title="迁移失败率过高",
                    message=f"当前失败率: {failure_rate:.2%}, 阈值: {self.alert_thresholds['max_failure_rate']:.2%}"
                ))
    
    async def _check_stale_pending_migrations(self):
        """检查长时间未执行的待处理迁移"""
        stale_pending = await self.connection.fetch("""
            SELECT migration_id, migration_name, created_at
            FROM t_sys_migration_logs
            WHERE status = 'pending' 
              AND EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - created_at)) > $1
        """, self.alert_thresholds['max_pending_time'])
        
        for migration in stale_pending:
            await self._trigger_alert(MigrationAlert(
                alert_type="STALE_PENDING_MIGRATION",
                severity="MEDIUM",
                title="待处理迁移时间过长",
                message=f"迁移 {migration['migration_name']} 待处理时间超过阈值",
                migration_id=migration['migration_id']
            ))
    
    async def _check_low_success_rate(self):
        """检查成功率过低"""
        if (self.metrics.total_migrations > 0 and 
            self.metrics.success_rate < self.alert_thresholds['min_success_rate']):
            await self._trigger_alert(MigrationAlert(
                alert_type="LOW_SUCCESS_RATE",
                severity="HIGH",
                title="迁移成功率过低",
                message=f"当前成功率: {self.metrics.success_rate:.2%}, 最低要求: {self.alert_thresholds['min_success_rate']:.2%}"
            ))
    
    async def _check_database_health(self):
        """检查数据库健康状态"""
        try:
            # 简单的数据库连接测试
            await self.connection.fetchval("SELECT 1")
        except Exception as e:
            await self._trigger_alert(MigrationAlert(
                alert_type="DATABASE_CONNECTION_ERROR",
                severity="CRITICAL",
                title="数据库连接异常",
                message=f"数据库连接检查失败: {str(e)}"
            ))
    
    async def _trigger_alert(self, alert: MigrationAlert):
        """触发告警"""
        # 检查是否是重复告警
        if self._is_duplicate_alert(alert):
            return
        
        self.alerts.append(alert)
        logger.warning(f"触发告警: {alert.title} - {alert.message}")
        
        # 执行所有告警处理器
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"告警处理器执行失败: {e}")
    
    def _is_duplicate_alert(self, alert: MigrationAlert) -> bool:
        """检查是否是重复告警"""
        # 检查最近5分钟内是否有相同类型的告警
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        for existing_alert in self.alerts:
            if (existing_alert.alert_type == alert.alert_type and
                existing_alert.migration_id == alert.migration_id and
                existing_alert.timestamp > cutoff_time and
                not existing_alert.resolved):
                return True
        
        return False
    
    async def _log_alert(self, alert: MigrationAlert):
        """日志告警处理器"""
        log_level = {
            'LOW': logging.INFO,
            'MEDIUM': logging.WARNING,
            'HIGH': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }.get(alert.severity, logging.WARNING)
        
        logger.log(log_level, f"[{alert.severity}] {alert.title}: {alert.message}")
    
    async def _send_email_alert(self, alert: MigrationAlert):
        """邮件告警处理器"""
        email_config = self.notification_config.get('email', {})
        
        if not email_config.get('enabled', False):
            return
        
        try:
            # 创建邮件内容
            msg = MimeMultipart()
            msg['From'] = email_config['from']
            msg['To'] = ', '.join(email_config['to'])
            msg['Subject'] = f"[{alert.severity}] 数据库迁移告警: {alert.title}"
            
            # 邮件正文
            body = f"""
数据库迁移告警通知

告警类型: {alert.alert_type}
严重程度: {alert.severity}
告警标题: {alert.title}
告警消息: {alert.message}
迁移ID: {alert.migration_id or 'N/A'}
告警时间: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

当前迁移状态:
- 总迁移数: {self.metrics.total_migrations}
- 成功数: {self.metrics.successful_migrations}
- 失败数: {self.metrics.failed_migrations}
- 待处理数: {self.metrics.pending_migrations}
- 成功率: {self.metrics.success_rate:.2%}

请及时处理相关问题。

此邮件由数据库迁移监控系统自动发送。
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
            
            logger.info(f"告警邮件发送成功: {alert.title}")
            
        except Exception as e:
            logger.error(f"发送告警邮件失败: {e}")
    
    async def _send_webhook_alert(self, alert: MigrationAlert):
        """Webhook告警处理器"""
        webhook_config = self.notification_config.get('webhook', {})
        
        if not webhook_config.get('enabled', False):
            return
        
        try:
            import aiohttp
            
            payload = {
                'alert_type': alert.alert_type,
                'severity': alert.severity,
                'title': alert.title,
                'message': alert.message,
                'migration_id': alert.migration_id,
                'timestamp': alert.timestamp.isoformat(),
                'metrics': asdict(self.metrics)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_config['url'],
                    json=payload,
                    headers=webhook_config.get('headers', {}),
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook告警发送成功: {alert.title}")
                    else:
                        logger.error(f"Webhook告警发送失败: HTTP {response.status}")
                        
        except Exception as e:
            logger.error(f"发送Webhook告警失败: {e}")
    
    async def get_migration_dashboard(self) -> Dict[str, Any]:
        """获取迁移仪表板数据"""
        await self._collect_metrics()
        
        # 获取最近的迁移记录
        recent_migrations = await self.connection.fetch("""
            SELECT migration_id, migration_name, migration_type, status, 
                   execution_time_ms, executed_at, error_message
            FROM t_sys_migration_logs
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        # 获取按类型分组的统计
        type_stats = await self.connection.fetch("""
            SELECT migration_type, 
                   COUNT(*) as total,
                   COUNT(CASE WHEN status = 'success' THEN 1 END) as successful,
                   COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                   AVG(execution_time_ms) as avg_time
            FROM t_sys_migration_logs
            GROUP BY migration_type
            ORDER BY migration_type
        """)
        
        # 获取最近的告警
        recent_alerts = [
            asdict(alert) for alert in self.alerts[-10:]
            if not alert.resolved
        ]
        
        return {
            'metrics': asdict(self.metrics),
            'recent_migrations': [dict(m) for m in recent_migrations],
            'type_statistics': [dict(t) for t in type_stats],
            'recent_alerts': recent_alerts,
            'alert_thresholds': self.alert_thresholds,
            'monitoring_active': self.monitoring_active,
            'last_update': datetime.now().isoformat()
        }
    
    async def resolve_alert(self, alert_id: int) -> bool:
        """解决告警"""
        try:
            if 0 <= alert_id < len(self.alerts):
                self.alerts[alert_id].resolved = True
                logger.info(f"告警已解决: {self.alerts[alert_id].title}")
                return True
            return False
        except Exception as e:
            logger.error(f"解决告警失败: {e}")
            return False
    
    async def get_migration_logs(self, migration_id: Optional[str] = None, 
                               limit: int = 100) -> List[Dict[str, Any]]:
        """获取迁移日志"""
        try:
            if migration_id:
                logs = await self.connection.fetch("""
                    SELECT * FROM t_sys_migration_logs
                    WHERE migration_id = $1
                    ORDER BY created_at DESC
                """, migration_id)
            else:
                logs = await self.connection.fetch("""
                    SELECT * FROM t_sys_migration_logs
                    ORDER BY created_at DESC
                    LIMIT $1
                """, limit)
            
            return [dict(log) for log in logs]
            
        except Exception as e:
            logger.error(f"获取迁移日志失败: {e}")
            return []
    
    async def export_migration_report(self, output_file: str = None) -> str:
        """导出迁移报告"""
        if output_file is None:
            output_file = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            dashboard_data = await self.get_migration_dashboard()
            
            # 添加详细的迁移日志
            all_logs = await self.get_migration_logs(limit=1000)
            dashboard_data['all_migration_logs'] = all_logs
            
            # 添加告警历史
            dashboard_data['alert_history'] = [asdict(alert) for alert in self.alerts]
            
            # 保存到文件
            output_path = Path(output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(dashboard_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"迁移报告已导出: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"导出迁移报告失败: {e}")
            return ""

class MigrationLogAnalyzer:
    """迁移日志分析器"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.connection: Optional[asyncpg.Connection] = None
    
    async def connect(self):
        """连接数据库"""
        self.connection = await asyncpg.connect(self.db_url)
    
    async def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            await self.connection.close()
    
    async def analyze_performance(self) -> Dict[str, Any]:
        """分析迁移性能"""
        try:
            await self.connect()
            
            # 执行时间分析
            time_stats = await self.connection.fetchrow("""
                SELECT 
                    MIN(execution_time_ms) as min_time,
                    MAX(execution_time_ms) as max_time,
                    AVG(execution_time_ms) as avg_time,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY execution_time_ms) as median_time,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time_ms) as p95_time
                FROM t_sys_migration_logs
                WHERE status = 'success' AND execution_time_ms IS NOT NULL
            """)
            
            # 按类型分析
            type_performance = await self.connection.fetch("""
                SELECT 
                    migration_type,
                    COUNT(*) as count,
                    AVG(execution_time_ms) as avg_time,
                    MIN(execution_time_ms) as min_time,
                    MAX(execution_time_ms) as max_time
                FROM t_sys_migration_logs
                WHERE status = 'success' AND execution_time_ms IS NOT NULL
                GROUP BY migration_type
                ORDER BY avg_time DESC
            """)
            
            # 时间趋势分析
            time_trend = await self.connection.fetch("""
                SELECT 
                    DATE_TRUNC('hour', executed_at) as hour,
                    COUNT(*) as migrations_count,
                    AVG(execution_time_ms) as avg_time
                FROM t_sys_migration_logs
                WHERE status = 'success' AND executed_at IS NOT NULL
                GROUP BY DATE_TRUNC('hour', executed_at)
                ORDER BY hour DESC
                LIMIT 24
            """)
            
            return {
                'overall_stats': dict(time_stats) if time_stats else {},
                'type_performance': [dict(t) for t in type_performance],
                'time_trend': [dict(t) for t in time_trend]
            }
            
        except Exception as e:
            logger.error(f"性能分析失败: {e}")
            return {}
        finally:
            await self.disconnect()
    
    async def analyze_failures(self) -> Dict[str, Any]:
        """分析迁移失败"""
        try:
            await self.connect()
            
            # 失败统计
            failure_stats = await self.connection.fetchrow("""
                SELECT 
                    COUNT(*) as total_failures,
                    COUNT(DISTINCT migration_type) as failed_types,
                    COUNT(DISTINCT DATE_TRUNC('day', executed_at)) as failure_days
                FROM t_sys_migration_logs
                WHERE status = 'failed'
            """)
            
            # 按类型分析失败
            type_failures = await self.connection.fetch("""
                SELECT 
                    migration_type,
                    COUNT(*) as failure_count,
                    STRING_AGG(DISTINCT SUBSTRING(error_message, 1, 100), '; ') as common_errors
                FROM t_sys_migration_logs
                WHERE status = 'failed'
                GROUP BY migration_type
                ORDER BY failure_count DESC
            """)
            
            # 最近的失败记录
            recent_failures = await self.connection.fetch("""
                SELECT migration_id, migration_name, migration_type, 
                       error_message, executed_at
                FROM t_sys_migration_logs
                WHERE status = 'failed'
                ORDER BY executed_at DESC
                LIMIT 10
            """)
            
            return {
                'failure_stats': dict(failure_stats) if failure_stats else {},
                'type_failures': [dict(t) for t in type_failures],
                'recent_failures': [dict(f) for f in recent_failures]
            }
            
        except Exception as e:
            logger.error(f"失败分析失败: {e}")
            return {}
        finally:
            await self.disconnect()

# 使用示例和配置
MONITOR_CONFIG = {
    'max_execution_time': 300000,  # 5分钟
    'max_failure_rate': 0.1,       # 10%
    'max_pending_time': 3600,      # 1小时
    'min_success_rate': 0.9,       # 90%
    'notifications': {
        'email': {
            'enabled': False,  # 需要配置SMTP信息
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'use_tls': True,
            'username': 'monitor@example.com',
            'password': 'password',
            'from': 'monitor@example.com',
            'to': ['admin@example.com']
        },
        'webhook': {
            'enabled': False,  # 需要配置Webhook URL
            'url': 'https://hooks.slack.com/services/xxx/yyy/zzz',
            'headers': {
                'Content-Type': 'application/json'
            }
        }
    }
}

async def main():
    """主函数示例"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库迁移监控工具')
    parser.add_argument('--db-url', required=True, help='数据库连接URL')
    parser.add_argument('--action', choices=['monitor', 'dashboard', 'analyze', 'export'], 
                       default='monitor', help='执行的操作')
    parser.add_argument('--interval', type=int, default=30, help='监控间隔(秒)')
    parser.add_argument('--output', help='输出文件路径')
    
    args = parser.parse_args()
    
    if args.action == 'monitor':
        monitor = MigrationMonitor(args.db_url, MONITOR_CONFIG)
        try:
            await monitor.start_monitoring(args.interval)
        except KeyboardInterrupt:
            monitor.stop_monitoring()
            print("监控已停止")
    
    elif args.action == 'dashboard':
        monitor = MigrationMonitor(args.db_url, MONITOR_CONFIG)
        try:
            await monitor.connect()
            dashboard = await monitor.get_migration_dashboard()
            print(json.dumps(dashboard, indent=2, ensure_ascii=False, default=str))
        finally:
            await monitor.disconnect()
    
    elif args.action == 'analyze':
        analyzer = MigrationLogAnalyzer(args.db_url)
        performance = await analyzer.analyze_performance()
        failures = await analyzer.analyze_failures()
        
        analysis = {
            'performance_analysis': performance,
            'failure_analysis': failures,
            'generated_at': datetime.now().isoformat()
        }
        
        print(json.dumps(analysis, indent=2, ensure_ascii=False, default=str))
    
    elif args.action == 'export':
        monitor = MigrationMonitor(args.db_url, MONITOR_CONFIG)
        try:
            await monitor.connect()
            output_file = await monitor.export_migration_report(args.output)
            print(f"报告已导出: {output_file}")
        finally:
            await monitor.disconnect()

if __name__ == "__main__":
    asyncio.run(main())