#!/usr/bin/env python3
"""
实际执行分阶段数据库迁移
使用现有配置直接执行迁移
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入现有配置
from migration_config import config as migration_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('actual_migration_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def print_banner():
    """打印执行横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                 🚀 API权限重构 - 数据库迁移                  ║
║              API Permission Refactor Migration              ║
╠══════════════════════════════════════════════════════════════╣
║  开始时间: {time}                           ║
║  迁移模式: 分阶段安全迁移                                    ║
╚══════════════════════════════════════════════════════════════╝
    """.format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print(banner)

async def check_database_connection():
    """检查数据库连接"""
    logger.info("🔗 检查数据库连接...")
    
    try:
        import asyncpg
        
        db_url = migration_config.DATABASE_URL
        logger.info(f"数据库连接: {db_url[:50]}...")
        
        conn = await asyncpg.connect(db_url)
        result = await conn.fetchval("SELECT 1")
        await conn.close()
        
        if result == 1:
            logger.info("✅ 数据库连接成功")
            return True
        else:
            logger.error("❌ 数据库连接测试失败")
            return False
    except ImportError:
        logger.error("❌ 缺少 asyncpg 依赖")
        logger.info("请运行: pip install asyncpg aiohttp")
        return False
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        return False

async def initialize_migration_system():
    """初始化迁移系统"""
    logger.info("🔧 初始化迁移系统...")
    
    try:
        from phased_migration_strategy import (
            PhasedMigrationStrategy, MigrationConfig, 
            MigrationPhase, ConsistencyLevel
        )
        from migration_alerting_system import (
            MigrationAlertingSystem, AlertRule, 
            AlertType, AlertSeverity
        )
        
        db_url = migration_config.DATABASE_URL
        
        # 初始化组件
        strategy = PhasedMigrationStrategy(db_url)
        alerting = MigrationAlertingSystem(db_url)
        
        await strategy.connect()
        await alerting.connect()
        
        logger.info("✅ 迁移系统初始化完成")
        return strategy, alerting
        
    except Exception as e:
        logger.error(f"❌ 迁移系统初始化失败: {e}")
        raise

async def execute_api_permission_migration():
    """执行API权限迁移"""
    logger.info("🎯 开始执行API权限迁移...")
    
    try:
        # 初始化系统
        strategy, alerting = await initialize_migration_system()
        
        # 阶段1：准备阶段
        logger.info("📋 阶段1：准备阶段")
        logger.info("-" * 40)
        
        from phased_migration_strategy import MigrationConfig, MigrationPhase, ConsistencyLevel
        
        # 创建API权限迁移配置
        api_config = MigrationConfig(
            migration_id="api_permission_migration",
            source_table="api",
            target_table="t_sys_api_endpoints",
            phase=MigrationPhase.PREPARATION,
            consistency_level=ConsistencyLevel.STRICT,
            dual_write_enabled=False,
            read_from_target=False,
            validation_enabled=True,
            auto_switch_threshold=0.99,
            rollback_enabled=True
        )
        
        # 注册迁移配置
        success = await strategy.register_migration(api_config)
        if not success:
            logger.error("❌ 迁移配置注册失败")
            return False
        
        logger.info("✅ 迁移配置已注册")
        
        # 设置告警规则
        from migration_alerting_system import AlertRule, AlertType, AlertSeverity
        
        alert_rule = AlertRule(
            rule_id="api_migration_failure",
            rule_name="API迁移失败告警",
            alert_type=AlertType.MIGRATION_FAILURE,
            severity=AlertSeverity.CRITICAL,
            condition="SELECT COUNT(*) FROM t_sys_migration_logs WHERE migration_id = 'api_permission_migration' AND status = 'failed' AND created_at > NOW() - INTERVAL '5 minutes'",
            threshold=1.0,
            duration=60,
            auto_recovery=False
        )
        
        await alerting.register_alert_rule(alert_rule)
        logger.info("✅ 告警规则已设置")
        
        # 阶段2：双写阶段
        logger.info("\n🔄 阶段2：双写阶段")
        logger.info("-" * 40)
        
        # 启用双写
        success = await strategy.enable_dual_write("api_permission_migration")
        if not success:
            logger.error("❌ 启用双写失败")
            return False
        
        logger.info("✅ 双写已启用")
        
        # 更新迁移阶段
        await strategy.update_migration_phase("api_permission_migration", MigrationPhase.DUAL_WRITE)
        logger.info("✅ 迁移阶段已更新为双写阶段")
        
        # 等待双写稳定运行
        logger.info("⏳ 等待双写稳定运行（30秒）...")
        await asyncio.sleep(30)
        
        # 阶段3：验证阶段
        logger.info("\n🔍 阶段3：验证阶段")
        logger.info("-" * 40)
        
        from data_consistency_validator import DataConsistencyValidator, ValidationLevel
        
        validator = DataConsistencyValidator(migration_config.DATABASE_URL)
        await validator.connect()
        
        # 更新迁移阶段
        await strategy.update_migration_phase("api_permission_migration", MigrationPhase.VALIDATION)
        logger.info("✅ 迁移阶段已更新为验证阶段")
        
        # 执行数据一致性检查
        logger.info("🔍 执行数据一致性检查...")
        validation_result = await validator.validate_table_consistency(
            "api",
            "t_sys_api_endpoints",
            ValidationLevel.DETAILED,
            sample_size=5000
        )
        
        logger.info(f"📊 一致性分数: {validation_result.consistency_score:.4f}")
        logger.info(f"📋 发现差异数量: {len(validation_result.differences)}")
        
        # 导出验证报告
        report_file = await validator.export_validation_report(
            validation_result.validation_id,
            f"api_migration_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        logger.info(f"📄 验证报告已导出: {report_file}")
        
        await validator.disconnect()
        
        # 阶段4：读取切换阶段
        logger.info("\n🔀 阶段4：读取切换阶段")
        logger.info("-" * 40)
        
        from configurable_read_switch import (
            ConfigurableReadSwitch, SwitchConfig, 
            SwitchStrategy, ReadSource, SwitchStatus
        )
        
        switch = ConfigurableReadSwitch(migration_config.DATABASE_URL)
        await switch.connect()
        
        # 更新迁移阶段
        await strategy.update_migration_phase("api_permission_migration", MigrationPhase.READ_SWITCH)
        logger.info("✅ 迁移阶段已更新为读取切换阶段")
        
        # 创建读取切换配置
        switch_config = SwitchConfig(
            config_id="api_migration_switch",
            table_name="api",
            current_source=ReadSource.SOURCE,
            target_source=ReadSource.TARGET,
            strategy=SwitchStrategy.GRADUAL,
            switch_percentage=0.0,
            conditions={
                "consistency_threshold": 0.99,
                "error_rate_threshold": 0.01
            },
            rollback_enabled=True,
            auto_rollback_threshold=0.05,
            status=SwitchStatus.INACTIVE
        )
        
        # 注册并激活切换配置
        await switch.register_switch_config(switch_config)
        await switch.activate_switch(switch_config.config_id)
        logger.info("✅ 切换配置已激活")
        
        # 渐进式切换
        switch_percentages = [10, 25, 50, 75, 100]
        
        for percentage in switch_percentages:
            logger.info(f"🔄 切换到 {percentage}%...")
            await switch.update_switch_percentage(switch_config.config_id, percentage)
            
            # 等待稳定
            logger.info(f"⏳ 等待稳定运行（30秒）...")
            await asyncio.sleep(30)
            
            logger.info(f"✅ 切换到 {percentage}% 完成")
        
        await switch.disconnect()
        
        # 阶段5：清理阶段
        logger.info("\n🧹 阶段5：清理阶段")
        logger.info("-" * 40)
        
        # 更新迁移阶段
        await strategy.update_migration_phase("api_permission_migration", MigrationPhase.CLEANUP)
        logger.info("✅ 迁移阶段已更新为清理阶段")
        
        # 禁用双写
        await strategy.disable_dual_write("api_permission_migration")
        logger.info("✅ 双写已禁用")
        
        # 最终验证
        validator = DataConsistencyValidator(migration_config.DATABASE_URL)
        await validator.connect()
        
        logger.info("🔍 执行最终数据一致性检查...")
        final_validation = await validator.validate_table_consistency(
            "api",
            "t_sys_api_endpoints",
            ValidationLevel.COMPREHENSIVE
        )
        
        logger.info(f"📊 最终一致性分数: {final_validation.consistency_score:.4f}")
        
        # 导出最终报告
        final_report = await validator.export_validation_report(
            final_validation.validation_id,
            f"final_api_migration_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        logger.info(f"📄 最终验证报告已导出: {final_report}")
        
        await validator.disconnect()
        
        # 阶段6：完成阶段
        logger.info("\n🏁 阶段6：完成阶段")
        logger.info("-" * 40)
        
        # 更新迁移阶段
        await strategy.update_migration_phase("api_permission_migration", MigrationPhase.COMPLETED)
        logger.info("✅ 迁移阶段已更新为完成阶段")
        
        # 生成迁移总结报告
        summary_report = {
            'migration_id': 'api_permission_migration',
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat(),
            'phases_completed': [
                'preparation', 'dual_write', 'validation', 
                'read_switch', 'cleanup', 'completed'
            ],
            'validation_score': validation_result.consistency_score,
            'final_validation_score': final_validation.consistency_score,
            'reports_generated': [report_file, final_report],
            'success': True
        }
        
        # 保存总结报告
        summary_file = f"api_migration_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_report, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"📄 迁移总结报告已生成: {summary_file}")
        
        # 清理连接
        await strategy.disconnect()
        await alerting.disconnect()
        
        logger.info("🎉 API权限迁移全部完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ API权限迁移失败: {e}")
        return False

async def main():
    """主函数"""
    print_banner()
    
    try:
        # 检查数据库连接
        if not await check_database_connection():
            logger.error("❌ 数据库连接检查失败，迁移终止")
            return False
        
        # 执行API权限迁移
        success = await execute_api_permission_migration()
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 API权限重构数据库迁移执行成功！")
            print("=" * 60)
            print("\n📋 后续步骤:")
            print("1. 检查生成的验证报告")
            print("2. 测试API功能")
            print("3. 验证权限系统")
            print("4. 监控系统性能")
            print("5. 更新应用配置")
            print("\n🎊 恭喜完成API权限重构迁移！")
            return True
        else:
            print("\n" + "=" * 60)
            print("❌ API权限重构数据库迁移执行失败！")
            print("=" * 60)
            print("\n🔧 故障排除:")
            print("1. 查看日志文件: actual_migration_execution.log")
            print("2. 检查数据库状态")
            print("3. 验证表结构")
            print("4. 考虑执行回滚操作")
            return False
            
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断执行")
        print("⚠️ 请检查系统状态并考虑回滚")
        return False
    except Exception as e:
        logger.error(f"💥 执行过程中发生未预期错误: {e}")
        print(f"\n💥 执行失败: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)