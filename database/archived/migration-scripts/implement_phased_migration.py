#!/usr/bin/env python3
"""
分阶段数据库迁移实施脚本
按照操作手册的流程，完整实施分阶段迁移策略
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# 导入迁移系统组件
from phased_migration_strategy import (
    PhasedMigrationStrategy, MigrationConfig, MigrationPhase, ConsistencyLevel
)
from data_consistency_validator import (
    DataConsistencyValidator, ValidationLevel
)
from configurable_read_switch import (
    ConfigurableReadSwitch, SwitchConfig, SwitchStrategy, ReadSource, SwitchStatus
)
from migration_alerting_system import (
    MigrationAlertingSystem, AlertRule, AlertType, AlertSeverity, NotificationChannel
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phased_migration_implementation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PhasedMigrationImplementor:
    """分阶段迁移实施器"""
    
    def __init__(self, config_file: str = "database/config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.db_url = self.config.get('database_url')
        
        # 初始化组件
        self.strategy = PhasedMigrationStrategy(self.db_url)
        self.validator = DataConsistencyValidator(self.db_url)
        self.switch = ConfigurableReadSwitch(self.db_url)
        self.alerting = MigrationAlertingSystem(self.db_url)
        
        # 迁移状态
        self.current_migrations: Dict[str, Dict] = {}
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "database_url": os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/database'),
            "migrations": [
                {
                    "migration_id": "api_permission_migration",
                    "source_table": "api",
                    "target_table": "t_sys_api_endpoints",
                    "description": "API权限系统迁移"
                },
                {
                    "migration_id": "user_permission_migration", 
                    "source_table": "user_permissions",
                    "target_table": "t_sys_user_permissions",
                    "description": "用户权限迁移"
                }
            ],
            "monitoring": {
                "enabled": True,
                "interval": 30
            }
        }
    
    async def initialize_systems(self):
        """初始化所有系统组件"""
        logger.info("初始化分阶段迁移系统...")
        
        try:
            # 连接所有组件
            await self.strategy.connect()
            await self.validator.connect()
            await self.switch.connect()
            await self.alerting.connect()
            
            logger.info("所有系统组件初始化完成")
            
        except Exception as e:
            logger.error(f"系统初始化失败: {e}")
            raise
    
    async def cleanup_systems(self):
        """清理系统资源"""
        logger.info("清理系统资源...")
        
        try:
            await self.strategy.disconnect()
            await self.validator.disconnect()
            await self.switch.disconnect()
            await self.alerting.disconnect()
            
            logger.info("系统资源清理完成")
            
        except Exception as e:
            logger.error(f"系统清理失败: {e}")
    
    async def phase1_preparation(self, migration_config: Dict[str, Any]) -> bool:
        """阶段1：准备阶段"""
        migration_id = migration_config['migration_id']
        logger.info(f"开始阶段1：准备阶段 - {migration_id}")
        
        try:
            # 1.1 创建迁移配置
            config = MigrationConfig(
                migration_id=migration_id,
                source_table=migration_config['source_table'],
                target_table=migration_config['target_table'],
                phase=MigrationPhase.PREPARATION,
                consistency_level=ConsistencyLevel.STRICT,
                dual_write_enabled=False,
                read_from_target=False,
                validation_enabled=True,
                auto_switch_threshold=0.99,
                rollback_enabled=True
            )
            
            # 注册迁移配置
            success = await self.strategy.register_migration(config)
            if not success:
                logger.error(f"注册迁移配置失败: {migration_id}")
                return False
            
            # 1.2 设置告警规则
            await self._setup_alert_rules(migration_id)
            
            # 1.3 初始数据一致性检查
            logger.info(f"执行初始数据一致性检查: {migration_id}")
            initial_result = await self.validator.validate_table_consistency(
                migration_config['source_table'],
                migration_config['target_table'],
                ValidationLevel.BASIC
            )
            
            logger.info(f"初始一致性分数: {initial_result.consistency_score:.4f}")
            
            # 更新迁移状态
            self.current_migrations[migration_id] = {
                'config': migration_config,
                'phase': MigrationPhase.PREPARATION,
                'initial_consistency': initial_result.consistency_score,
                'start_time': datetime.now()
            }
            
            logger.info(f"阶段1完成 - {migration_id}")
            return True
            
        except Exception as e:
            logger.error(f"阶段1失败 - {migration_id}: {e}")
            return False
    
    async def _setup_alert_rules(self, migration_id: str):
        """设置告警规则"""
        rules = [
            AlertRule(
                rule_id=f"{migration_id}_failure",
                rule_name=f"{migration_id} 迁移失败告警",
                alert_type=AlertType.MIGRATION_FAILURE,
                severity=AlertSeverity.CRITICAL,
                condition=f"SELECT COUNT(*) FROM t_sys_migration_logs WHERE migration_id = '{migration_id}' AND status = 'failed' AND created_at > NOW() - INTERVAL '5 minutes'",
                threshold=1.0,
                duration=60,
                auto_recovery=True,
                recovery_action="retry_migration"
            ),
            AlertRule(
                rule_id=f"{migration_id}_consistency",
                rule_name=f"{migration_id} 数据一致性告警",
                alert_type=AlertType.CONSISTENCY_ISSUE,
                severity=AlertSeverity.ERROR,
                condition=f"SELECT AVG(consistency_ratio) FROM t_sys_consistency_checks WHERE migration_id = '{migration_id}' AND created_at > NOW() - INTERVAL '10 minutes'",
                threshold=0.95,
                duration=300
            ),
            AlertRule(
                rule_id=f"{migration_id}_dual_write",
                rule_name=f"{migration_id} 双写错误告警",
                alert_type=AlertType.DUAL_WRITE_ERROR,
                severity=AlertSeverity.WARNING,
                condition=f"SELECT COUNT(*) FROM t_sys_dual_write_logs WHERE migration_id = '{migration_id}' AND (source_success = FALSE OR target_success = FALSE) AND created_at > NOW() - INTERVAL '5 minutes'",
                threshold=10.0,
                duration=120
            )
        ]
        
        for rule in rules:
            await self.alerting.register_alert_rule(rule)
    
    async def phase2_dual_write(self, migration_id: str) -> bool:
        """阶段2：双写阶段"""
        logger.info(f"开始阶段2：双写阶段 - {migration_id}")
        
        try:
            # 2.1 启用双写
            success = await self.strategy.enable_dual_write(migration_id)
            if not success:
                logger.error(f"启用双写失败: {migration_id}")
                return False
            
            # 2.2 更新迁移阶段
            await self.strategy.update_migration_phase(migration_id, MigrationPhase.DUAL_WRITE)
            
            # 2.3 等待双写稳定运行
            logger.info(f"等待双写稳定运行 - {migration_id}")
            await asyncio.sleep(30)  # 等待30秒让双写稳定
            
            # 2.4 检查双写指标
            metrics = await self.strategy.get_dual_write_metrics(migration_id, hours=1)
            if metrics.get('total_operations', 0) > 0:
                success_rate = metrics.get('success_rate', 0)
                logger.info(f"双写成功率: {success_rate:.4f}")
                
                if success_rate < 0.95:
                    logger.warning(f"双写成功率过低: {success_rate:.4f}")
                    return False
            
            # 更新状态
            self.current_migrations[migration_id]['phase'] = MigrationPhase.DUAL_WRITE
            self.current_migrations[migration_id]['dual_write_enabled'] = True
            
            logger.info(f"阶段2完成 - {migration_id}")
            return True
            
        except Exception as e:
            logger.error(f"阶段2失败 - {migration_id}: {e}")
            return False
    
    async def phase3_validation(self, migration_id: str) -> bool:
        """阶段3：验证阶段"""
        logger.info(f"开始阶段3：验证阶段 - {migration_id}")
        
        try:
            migration_info = self.current_migrations[migration_id]
            config = migration_info['config']
            
            # 3.1 更新迁移阶段
            await self.strategy.update_migration_phase(migration_id, MigrationPhase.VALIDATION)
            
            # 3.2 执行详细的数据一致性检查
            logger.info(f"执行详细数据一致性检查 - {migration_id}")
            validation_result = await self.validator.validate_table_consistency(
                config['source_table'],
                config['target_table'],
                ValidationLevel.DETAILED,
                sample_size=10000
            )
            
            logger.info(f"详细一致性分数: {validation_result.consistency_score:.4f}")
            logger.info(f"发现差异数量: {len(validation_result.differences)}")
            
            # 3.3 分析验证结果
            if validation_result.consistency_score < 0.99:
                logger.warning(f"一致性分数低于阈值: {validation_result.consistency_score:.4f}")
                
                # 输出差异详情
                for diff in validation_result.differences[:10]:  # 只显示前10个差异
                    logger.warning(f"差异: {diff.difference_type.value} - {diff.description}")
                
                # 可以选择继续或回滚
                if validation_result.consistency_score < 0.95:
                    logger.error("一致性分数过低，建议回滚")
                    return False
            
            # 3.4 导出验证报告
            report_file = await self.validator.export_validation_report(
                validation_result.validation_id,
                f"validation_report_{migration_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            logger.info(f"验证报告已导出: {report_file}")
            
            # 更新状态
            self.current_migrations[migration_id]['phase'] = MigrationPhase.VALIDATION
            self.current_migrations[migration_id]['validation_score'] = validation_result.consistency_score
            self.current_migrations[migration_id]['validation_report'] = report_file
            
            logger.info(f"阶段3完成 - {migration_id}")
            return True
            
        except Exception as e:
            logger.error(f"阶段3失败 - {migration_id}: {e}")
            return False
    
    async def phase4_read_switch(self, migration_id: str) -> bool:
        """阶段4：读取切换阶段"""
        logger.info(f"开始阶段4：读取切换阶段 - {migration_id}")
        
        try:
            migration_info = self.current_migrations[migration_id]
            config = migration_info['config']
            
            # 4.1 更新迁移阶段
            await self.strategy.update_migration_phase(migration_id, MigrationPhase.READ_SWITCH)
            
            # 4.2 创建读取切换配置
            switch_config = SwitchConfig(
                config_id=f"{migration_id}_switch",
                table_name=config['source_table'],
                current_source=ReadSource.SOURCE,
                target_source=ReadSource.TARGET,
                strategy=SwitchStrategy.GRADUAL,
                switch_percentage=0.0,
                conditions={
                    "consistency_threshold": 0.99,
                    "error_rate_threshold": 0.01,
                    "latency_threshold": 100
                },
                rollback_enabled=True,
                auto_rollback_threshold=0.05,
                status=SwitchStatus.INACTIVE
            )
            
            # 注册切换配置
            success = await self.switch.register_switch_config(switch_config)
            if not success:
                logger.error(f"注册切换配置失败: {migration_id}")
                return False
            
            # 4.3 激活切换
            await self.switch.activate_switch(switch_config.config_id)
            
            # 4.4 渐进式切换
            switch_percentages = [10, 25, 50, 75, 100]
            
            for percentage in switch_percentages:
                logger.info(f"切换到 {percentage}% - {migration_id}")
                
                # 更新切换百分比
                await self.switch.update_switch_percentage(switch_config.config_id, percentage)
                
                # 等待稳定
                await asyncio.sleep(60)  # 等待1分钟观察
                
                # 检查切换指标
                analytics = await self.switch.get_switch_analytics(switch_config.config_id, hours=1)
                
                # 检查错误率
                error_analysis = analytics.get('error_analysis', [])
                if error_analysis:
                    total_errors = sum(error['error_count'] for error in error_analysis)
                    if total_errors > 10:  # 如果错误太多，暂停切换
                        logger.warning(f"错误数量过多: {total_errors}，暂停切换")
                        await asyncio.sleep(120)  # 等待2分钟
                
                logger.info(f"切换到 {percentage}% 完成 - {migration_id}")
            
            # 4.5 验证切换结果
            final_analytics = await self.switch.get_switch_analytics(switch_config.config_id, hours=2)
            logger.info(f"最终切换分析: {json.dumps(final_analytics, indent=2, default=str)}")
            
            # 更新状态
            self.current_migrations[migration_id]['phase'] = MigrationPhase.READ_SWITCH
            self.current_migrations[migration_id]['switch_config_id'] = switch_config.config_id
            self.current_migrations[migration_id]['switch_completed'] = True
            
            logger.info(f"阶段4完成 - {migration_id}")
            return True
            
        except Exception as e:
            logger.error(f"阶段4失败 - {migration_id}: {e}")
            # 尝试回滚
            try:
                switch_config_id = self.current_migrations[migration_id].get('switch_config_id')
                if switch_config_id:
                    await self.switch.rollback_switch(switch_config_id)
            except:
                pass
            return False
    
    async def phase5_cleanup(self, migration_id: str) -> bool:
        """阶段5：清理阶段"""
        logger.info(f"开始阶段5：清理阶段 - {migration_id}")
        
        try:
            migration_info = self.current_migrations[migration_id]
            config = migration_info['config']
            
            # 5.1 更新迁移阶段
            await self.strategy.update_migration_phase(migration_id, MigrationPhase.CLEANUP)
            
            # 5.2 禁用双写
            await self.strategy.disable_dual_write(migration_id)
            
            # 5.3 最终验证
            logger.info(f"执行最终数据一致性检查 - {migration_id}")
            final_validation = await self.validator.validate_table_consistency(
                config['source_table'],
                config['target_table'],
                ValidationLevel.COMPREHENSIVE
            )
            
            logger.info(f"最终一致性分数: {final_validation.consistency_score:.4f}")
            
            # 5.4 导出最终报告
            final_report = await self.validator.export_validation_report(
                final_validation.validation_id,
                f"final_validation_report_{migration_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            logger.info(f"最终验证报告已导出: {final_report}")
            
            # 5.5 停用切换配置
            switch_config_id = migration_info.get('switch_config_id')
            if switch_config_id:
                await self.switch.deactivate_switch(switch_config_id)
            
            # 更新状态
            self.current_migrations[migration_id]['phase'] = MigrationPhase.CLEANUP
            self.current_migrations[migration_id]['final_consistency'] = final_validation.consistency_score
            self.current_migrations[migration_id]['final_report'] = final_report
            
            logger.info(f"阶段5完成 - {migration_id}")
            return True
            
        except Exception as e:
            logger.error(f"阶段5失败 - {migration_id}: {e}")
            return False
    
    async def phase6_completion(self, migration_id: str) -> bool:
        """阶段6：完成阶段"""
        logger.info(f"开始阶段6：完成阶段 - {migration_id}")
        
        try:
            # 6.1 更新迁移阶段
            await self.strategy.update_migration_phase(migration_id, MigrationPhase.COMPLETED)
            
            # 6.2 生成迁移总结报告
            migration_info = self.current_migrations[migration_id]
            
            summary_report = {
                'migration_id': migration_id,
                'start_time': migration_info['start_time'].isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration': str(datetime.now() - migration_info['start_time']),
                'initial_consistency': migration_info.get('initial_consistency', 0),
                'validation_consistency': migration_info.get('validation_score', 0),
                'final_consistency': migration_info.get('final_consistency', 0),
                'phases_completed': [
                    'preparation', 'dual_write', 'validation', 
                    'read_switch', 'cleanup', 'completed'
                ],
                'reports_generated': [
                    migration_info.get('validation_report'),
                    migration_info.get('final_report')
                ],
                'success': True
            }
            
            # 保存总结报告
            summary_file = f"migration_summary_{migration_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary_report, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"迁移总结报告已生成: {summary_file}")
            
            # 更新状态
            self.current_migrations[migration_id]['phase'] = MigrationPhase.COMPLETED
            self.current_migrations[migration_id]['summary_report'] = summary_file
            self.current_migrations[migration_id]['completed'] = True
            
            logger.info(f"🎉 迁移完成 - {migration_id}")
            logger.info(f"总耗时: {datetime.now() - migration_info['start_time']}")
            logger.info(f"最终一致性分数: {migration_info.get('final_consistency', 'N/A')}")
            
            return True
            
        except Exception as e:
            logger.error(f"阶段6失败 - {migration_id}: {e}")
            return False
    
    async def rollback_migration(self, migration_id: str) -> bool:
        """回滚迁移"""
        logger.warning(f"开始回滚迁移 - {migration_id}")
        
        try:
            migration_info = self.current_migrations.get(migration_id)
            if not migration_info:
                logger.error(f"迁移信息不存在: {migration_id}")
                return False
            
            # 1. 回滚读取切换
            switch_config_id = migration_info.get('switch_config_id')
            if switch_config_id:
                await self.switch.rollback_switch(switch_config_id)
                logger.info(f"读取切换已回滚 - {migration_id}")
            
            # 2. 禁用双写
            if migration_info.get('dual_write_enabled'):
                await self.strategy.disable_dual_write(migration_id)
                logger.info(f"双写已禁用 - {migration_id}")
            
            # 3. 回滚迁移状态
            await self.strategy.rollback_migration(migration_id)
            
            # 4. 更新本地状态
            self.current_migrations[migration_id]['phase'] = MigrationPhase.PREPARATION
            self.current_migrations[migration_id]['rolled_back'] = True
            self.current_migrations[migration_id]['rollback_time'] = datetime.now()
            
            logger.info(f"迁移回滚完成 - {migration_id}")
            return True
            
        except Exception as e:
            logger.error(f"迁移回滚失败 - {migration_id}: {e}")
            return False
    
    async def run_single_migration(self, migration_config: Dict[str, Any]) -> bool:
        """运行单个迁移"""
        migration_id = migration_config['migration_id']
        logger.info(f"开始执行迁移: {migration_id}")
        
        try:
            # 执行各个阶段
            phases = [
                ("准备阶段", self.phase1_preparation),
                ("双写阶段", lambda mid: self.phase2_dual_write(mid)),
                ("验证阶段", lambda mid: self.phase3_validation(mid)),
                ("读取切换阶段", lambda mid: self.phase4_read_switch(mid)),
                ("清理阶段", lambda mid: self.phase5_cleanup(mid)),
                ("完成阶段", lambda mid: self.phase6_completion(mid))
            ]
            
            for phase_name, phase_func in phases:
                logger.info(f"执行{phase_name} - {migration_id}")
                
                if phase_name == "准备阶段":
                    success = await phase_func(migration_config)
                else:
                    success = await phase_func(migration_id)
                
                if not success:
                    logger.error(f"{phase_name}失败 - {migration_id}")
                    
                    # 询问是否回滚
                    logger.warning(f"是否回滚迁移 {migration_id}? (建议回滚)")
                    await self.rollback_migration(migration_id)
                    return False
                
                logger.info(f"{phase_name}完成 - {migration_id}")
                
                # 在每个阶段之间稍作等待
                if phase_name != "完成阶段":
                    await asyncio.sleep(10)
            
            logger.info(f"✅ 迁移成功完成: {migration_id}")
            return True
            
        except Exception as e:
            logger.error(f"迁移执行失败 - {migration_id}: {e}")
            await self.rollback_migration(migration_id)
            return False
    
    async def run_all_migrations(self) -> bool:
        """运行所有配置的迁移"""
        logger.info("开始执行所有迁移...")
        
        migrations = self.config.get('migrations', [])
        if not migrations:
            logger.warning("没有配置迁移任务")
            return True
        
        success_count = 0
        total_count = len(migrations)
        
        for migration_config in migrations:
            migration_id = migration_config['migration_id']
            logger.info(f"开始迁移 {success_count + 1}/{total_count}: {migration_id}")
            
            success = await self.run_single_migration(migration_config)
            if success:
                success_count += 1
                logger.info(f"✅ 迁移成功: {migration_id}")
            else:
                logger.error(f"❌ 迁移失败: {migration_id}")
        
        logger.info(f"迁移完成统计: {success_count}/{total_count} 成功")
        
        return success_count == total_count
    
    async def start_monitoring(self):
        """启动监控系统"""
        if self.config.get('monitoring', {}).get('enabled', False):
            logger.info("启动监控系统...")
            
            # 在后台启动监控
            monitoring_task = asyncio.create_task(
                self.alerting.start_monitoring(
                    self.config.get('monitoring', {}).get('interval', 30)
                )
            )
            
            return monitoring_task
        else:
            logger.info("监控系统未启用")
            return None
    
    async def generate_final_report(self) -> str:
        """生成最终报告"""
        logger.info("生成最终迁移报告...")
        
        report = {
            'execution_time': datetime.now().isoformat(),
            'total_migrations': len(self.current_migrations),
            'successful_migrations': len([m for m in self.current_migrations.values() if m.get('completed', False)]),
            'failed_migrations': len([m for m in self.current_migrations.values() if m.get('rolled_back', False)]),
            'migrations_detail': self.current_migrations,
            'system_config': self.config
        }
        
        report_file = f"final_migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"最终报告已生成: {report_file}")
        return report_file

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='分阶段数据库迁移实施工具')
    parser.add_argument('--config', default='database/config.json', help='配置文件路径')
    parser.add_argument('--migration-id', help='指定单个迁移ID')
    parser.add_argument('--dry-run', action='store_true', help='试运行模式')
    parser.add_argument('--skip-monitoring', action='store_true', help='跳过监控启动')
    
    args = parser.parse_args()
    
    # 创建实施器
    implementor = PhasedMigrationImplementor(args.config)
    
    try:
        # 初始化系统
        await implementor.initialize_systems()
        
        # 启动监控（如果需要）
        monitoring_task = None
        if not args.skip_monitoring:
            monitoring_task = await implementor.start_monitoring()
        
        # 执行迁移
        if args.migration_id:
            # 执行指定迁移
            migration_config = None
            for config in implementor.config.get('migrations', []):
                if config['migration_id'] == args.migration_id:
                    migration_config = config
                    break
            
            if migration_config:
                if args.dry_run:
                    logger.info(f"试运行模式 - 将执行迁移: {args.migration_id}")
                else:
                    await implementor.run_single_migration(migration_config)
            else:
                logger.error(f"未找到迁移配置: {args.migration_id}")
        else:
            # 执行所有迁移
            if args.dry_run:
                logger.info("试运行模式 - 将执行所有配置的迁移")
                for config in implementor.config.get('migrations', []):
                    logger.info(f"  - {config['migration_id']}: {config.get('description', '')}")
            else:
                await implementor.run_all_migrations()
        
        # 生成最终报告
        if not args.dry_run:
            await implementor.generate_final_report()
        
        # 停止监控
        if monitoring_task:
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass
    
    except KeyboardInterrupt:
        logger.info("用户中断执行")
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)
    finally:
        # 清理资源
        await implementor.cleanup_systems()
        logger.info("分阶段迁移实施完成")

if __name__ == "__main__":
    asyncio.run(main())