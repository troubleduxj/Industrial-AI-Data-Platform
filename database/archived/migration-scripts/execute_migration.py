#!/usr/bin/env python3
"""
实际执行分阶段数据库迁移
按照制定的策略执行完整的迁移流程
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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def print_banner():
    """打印执行横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                 🚀 分阶段数据库迁移执行                      ║
║                Phased Database Migration Execution          ║
╠══════════════════════════════════════════════════════════════╣
║  开始时间: {time}                           ║
║  执行模式: 生产环境迁移                                      ║
╚══════════════════════════════════════════════════════════════╝
    """.format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print(banner)

async def check_prerequisites():
    """检查前置条件"""
    logger.info("🔍 检查前置条件...")
    
    # 检查数据库连接
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        logger.error("❌ 未设置 DATABASE_URL 环境变量")
        logger.info("请设置: export DATABASE_URL='postgresql://user:password@localhost:5432/database'")
        return False
    
    # 检查必要文件
    required_files = [
        'phased_migration_strategy.py',
        'data_consistency_validator.py', 
        'configurable_read_switch.py',
        'migration_alerting_system.py',
        'config.json'
    ]
    
    for file in required_files:
        if not Path(file).exists():
            logger.error(f"❌ 缺少必要文件: {file}")
            return False
    
    # 测试数据库连接
    try:
        import asyncpg
        conn = await asyncpg.connect(db_url)
        await conn.fetchval("SELECT 1")
        await conn.close()
        logger.info("✅ 数据库连接测试成功")
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        return False
    
    logger.info("✅ 前置条件检查通过")
    return True

async def execute_migration_phase_1():
    """阶段1：准备阶段"""
    logger.info("🔧 阶段1：准备阶段")
    logger.info("=" * 50)
    
    try:
        from phased_migration_strategy import (
            PhasedMigrationStrategy, MigrationConfig, 
            MigrationPhase, ConsistencyLevel
        )
        from migration_alerting_system import (
            MigrationAlertingSystem, AlertRule, 
            AlertType, AlertSeverity
        )
        
        db_url = os.getenv('DATABASE_URL')
        
        # 初始化组件
        strategy = PhasedMigrationStrategy(db_url)
        alerting = MigrationAlertingSystem(db_url)
        
        await strategy.connect()
        await alerting.connect()
        
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
        if success:
            logger.info("✅ API权限迁移配置已注册")
        else:
            logger.error("❌ API权限迁移配置注册失败")
            return False
        
        # 设置告警规则
        alert_rules = [
            AlertRule(
                rule_id="api_migration_failure",
                rule_name="API迁移失败告警",
                alert_type=AlertType.MIGRATION_FAILURE,
                severity=AlertSeverity.CRITICAL,
                condition="SELECT COUNT(*) FROM t_sys_migration_logs WHERE migration_id = 'api_permission_migration' AND status = 'failed' AND created_at > NOW() - INTERVAL '5 minutes'",
                threshold=1.0,
                duration=60,
                auto_recovery=True,
                recovery_action="retry_migration"
            ),
            AlertRule(
                rule_id="api_consistency_issue",
                rule_name="API数据一致性问题",
                alert_type=AlertType.CONSISTENCY_ISSUE,
                severity=AlertSeverity.ERROR,
                condition="SELECT AVG(consistency_ratio) FROM t_sys_consistency_checks WHERE migration_id = 'api_permission_migration' AND created_at > NOW() - INTERVAL '10 minutes'",
                threshold=0.95,
                duration=300
            )
        ]
        
        for rule in alert_rules:
            await alerting.register_alert_rule(rule)
        
        logger.info("✅ 告警规则已设置")
        
        await strategy.disconnect()
        await alerting.disconnect()
        
        logger.info("🎉 阶段1完成：准备阶段")
        return True
        
    except Exception as e:
        logger.error(f"❌ 阶段1失败: {e}")
        return False

async def execute_migration_phase_2():
    """阶段2：双写阶段"""
    logger.info("🔄 阶段2：双写阶段")
    logger.info("=" * 50)
    
    try:
        from phased_migration_strategy import PhasedMigrationStrategy, MigrationPhase
        
        db_url = os.getenv('DATABASE_URL')
        strategy = PhasedMigrationStrategy(db_url)
        await strategy.connect()
        
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
        
        # 检查双写指标
        metrics = await strategy.get_dual_write_metrics("api_permission_migration", hours=1)
        if metrics.get('total_operations', 0) > 0:
            success_rate = metrics.get('success_rate', 0)
            logger.info(f"📊 双写成功率: {success_rate:.4f}")
            
            if success_rate < 0.95:
                logger.warning(f"⚠️ 双写成功率过低: {success_rate:.4f}")
                return False
        
        await strategy.disconnect()
        
        logger.info("🎉 阶段2完成：双写阶段")
        return True
        
    except Exception as e:
        logger.error(f"❌ 阶段2失败: {e}")
        return False

async def execute_migration_phase_3():
    """阶段3：验证阶段"""
    logger.info("🔍 阶段3：验证阶段")
    logger.info("=" * 50)
    
    try:
        from phased_migration_strategy import PhasedMigrationStrategy, MigrationPhase
        from data_consistency_validator import DataConsistencyValidator, ValidationLevel
        
        db_url = os.getenv('DATABASE_URL')
        strategy = PhasedMigrationStrategy(db_url)
        validator = DataConsistencyValidator(db_url)
        
        await strategy.connect()
        await validator.connect()
        
        # 更新迁移阶段
        await strategy.update_migration_phase("api_permission_migration", MigrationPhase.VALIDATION)
        logger.info("✅ 迁移阶段已更新为验证阶段")
        
        # 执行详细的数据一致性检查
        logger.info("🔍 执行详细数据一致性检查...")
        validation_result = await validator.validate_table_consistency(
            "api",
            "t_sys_api_endpoints", 
            ValidationLevel.DETAILED,
            sample_size=10000
        )
        
        logger.info(f"📊 一致性分数: {validation_result.consistency_score:.4f}")
        logger.info(f"📋 发现差异数量: {len(validation_result.differences)}")
        
        # 分析验证结果
        if validation_result.consistency_score < 0.99:
            logger.warning(f"⚠️ 一致性分数低于阈值: {validation_result.consistency_score:.4f}")
            
            # 显示前5个差异
            for i, diff in enumerate(validation_result.differences[:5]):
                logger.warning(f"差异 {i+1}: {diff.difference_type.value} - {diff.description}")
            
            if validation_result.consistency_score < 0.95:
                logger.error("❌ 一致性分数过低，建议回滚")
                return False
        
        # 导出验证报告
        report_file = await validator.export_validation_report(
            validation_result.validation_id,
            f"validation_report_api_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        logger.info(f"📄 验证报告已导出: {report_file}")
        
        await strategy.disconnect()
        await validator.disconnect()
        
        logger.info("🎉 阶段3完成：验证阶段")
        return True
        
    except Exception as e:
        logger.error(f"❌ 阶段3失败: {e}")
        return False

async def execute_migration_phase_4():
    """阶段4：读取切换阶段"""
    logger.info("🔀 阶段4：读取切换阶段")
    logger.info("=" * 50)
    
    try:
        from phased_migration_strategy import PhasedMigrationStrategy, MigrationPhase
        from configurable_read_switch import (
            ConfigurableReadSwitch, SwitchConfig, 
            SwitchStrategy, ReadSource, SwitchStatus
        )
        
        db_url = os.getenv('DATABASE_URL')
        strategy = PhasedMigrationStrategy(db_url)
        switch = ConfigurableReadSwitch(db_url)
        
        await strategy.connect()
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
                "error_rate_threshold": 0.01,
                "latency_threshold": 100
            },
            rollback_enabled=True,
            auto_rollback_threshold=0.05,
            status=SwitchStatus.INACTIVE
        )
        
        # 注册切换配置
        success = await switch.register_switch_config(switch_config)
        if not success:
            logger.error("❌ 注册切换配置失败")
            return False
        
        logger.info("✅ 切换配置已注册")
        
        # 激活切换
        await switch.activate_switch(switch_config.config_id)
        logger.info("✅ 切换已激活")
        
        # 渐进式切换
        switch_percentages = [10, 25, 50, 75, 100]
        
        for percentage in switch_percentages:
            logger.info(f"🔄 切换到 {percentage}%...")
            
            # 更新切换百分比
            await switch.update_switch_percentage(switch_config.config_id, percentage)
            
            # 等待稳定
            logger.info(f"⏳ 等待稳定运行（60秒）...")
            await asyncio.sleep(60)
            
            # 检查切换指标
            analytics = await switch.get_switch_analytics(switch_config.config_id, hours=1)
            
            # 检查错误率
            error_analysis = analytics.get('error_analysis', [])
            if error_analysis:
                total_errors = sum(error['error_count'] for error in error_analysis)
                if total_errors > 10:
                    logger.warning(f"⚠️ 错误数量过多: {total_errors}，暂停切换")
                    await asyncio.sleep(120)
            
            logger.info(f"✅ 切换到 {percentage}% 完成")
        
        # 验证切换结果
        final_analytics = await switch.get_switch_analytics(switch_config.config_id, hours=2)
        logger.info("📊 最终切换分析:")
        
        user_distribution = final_analytics.get('user_distribution', [])
        for dist in user_distribution:
            logger.info(f"  {dist['selected_source']}: {dist['total_requests']} 请求")
        
        await strategy.disconnect()
        await switch.disconnect()
        
        logger.info("🎉 阶段4完成：读取切换阶段")
        return True
        
    except Exception as e:
        logger.error(f"❌ 阶段4失败: {e}")
        return False

async def execute_migration_phase_5():
    """阶段5：清理阶段"""
    logger.info("🧹 阶段5：清理阶段")
    logger.info("=" * 50)
    
    try:
        from phased_migration_strategy import PhasedMigrationStrategy, MigrationPhase
        from data_consistency_validator import DataConsistencyValidator, ValidationLevel
        from configurable_read_switch import ConfigurableReadSwitch
        
        db_url = os.getenv('DATABASE_URL')
        strategy = PhasedMigrationStrategy(db_url)
        validator = DataConsistencyValidator(db_url)
        switch = ConfigurableReadSwitch(db_url)
        
        await strategy.connect()
        await validator.connect()
        await switch.connect()
        
        # 更新迁移阶段
        await strategy.update_migration_phase("api_permission_migration", MigrationPhase.CLEANUP)
        logger.info("✅ 迁移阶段已更新为清理阶段")
        
        # 禁用双写
        await strategy.disable_dual_write("api_permission_migration")
        logger.info("✅ 双写已禁用")
        
        # 最终验证
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
            f"final_validation_report_api_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        logger.info(f"📄 最终验证报告已导出: {final_report}")
        
        # 停用切换配置
        await switch.deactivate_switch("api_migration_switch")
        logger.info("✅ 切换配置已停用")
        
        await strategy.disconnect()
        await validator.disconnect()
        await switch.disconnect()
        
        logger.info("🎉 阶段5完成：清理阶段")
        return True
        
    except Exception as e:
        logger.error(f"❌ 阶段5失败: {e}")
        return False

async def execute_migration_phase_6():
    """阶段6：完成阶段"""
    logger.info("🏁 阶段6：完成阶段")
    logger.info("=" * 50)
    
    try:
        from phased_migration_strategy import PhasedMigrationStrategy, MigrationPhase
        
        db_url = os.getenv('DATABASE_URL')
        strategy = PhasedMigrationStrategy(db_url)
        await strategy.connect()
        
        # 更新迁移阶段
        await strategy.update_migration_phase("api_permission_migration", MigrationPhase.COMPLETED)
        logger.info("✅ 迁移阶段已更新为完成阶段")
        
        # 生成迁移总结报告
        summary_report = {
            'migration_id': 'api_permission_migration',
            'start_time': datetime.now().isoformat(),  # 实际应该记录开始时间
            'end_time': datetime.now().isoformat(),
            'phases_completed': [
                'preparation', 'dual_write', 'validation', 
                'read_switch', 'cleanup', 'completed'
            ],
            'success': True,
            'final_status': 'COMPLETED'
        }
        
        # 保存总结报告
        summary_file = f"migration_summary_api_permission_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_report, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"📄 迁移总结报告已生成: {summary_file}")
        
        await strategy.disconnect()
        
        logger.info("🎉 阶段6完成：完成阶段")
        logger.info("🎊 API权限迁移全部完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 阶段6失败: {e}")
        return False

async def execute_full_migration():
    """执行完整的分阶段迁移"""
    start_time = datetime.now()
    
    print_banner()
    
    # 检查前置条件
    if not await check_prerequisites():
        logger.error("❌ 前置条件检查失败，迁移终止")
        return False
    
    # 执行各个阶段
    phases = [
        ("阶段1：准备阶段", execute_migration_phase_1),
        ("阶段2：双写阶段", execute_migration_phase_2),
        ("阶段3：验证阶段", execute_migration_phase_3),
        ("阶段4：读取切换阶段", execute_migration_phase_4),
        ("阶段5：清理阶段", execute_migration_phase_5),
        ("阶段6：完成阶段", execute_migration_phase_6)
    ]
    
    for phase_name, phase_func in phases:
        logger.info(f"\n🚀 开始执行 {phase_name}")
        
        try:
            success = await phase_func()
            if not success:
                logger.error(f"❌ {phase_name} 执行失败")
                logger.warning("🔄 建议执行回滚操作")
                return False
            
            logger.info(f"✅ {phase_name} 执行成功")
            
            # 在阶段之间稍作等待
            if phase_name != "阶段6：完成阶段":
                logger.info("⏳ 等待10秒后继续下一阶段...")
                await asyncio.sleep(10)
                
        except Exception as e:
            logger.error(f"💥 {phase_name} 执行异常: {e}")
            return False
    
    # 计算总耗时
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info("\n" + "=" * 60)
    logger.info("🎉 分阶段数据库迁移执行完成！")
    logger.info(f"⏱️  总耗时: {duration}")
    logger.info(f"📅 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"📅 结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    return True

async def main():
    """主函数"""
    try:
        success = await execute_full_migration()
        
        if success:
            print("\n🎊 恭喜！分阶段数据库迁移执行成功！")
            print("\n📋 后续步骤:")
            print("1. 检查生成的报告文件")
            print("2. 验证应用程序功能")
            print("3. 监控系统性能")
            print("4. 清理临时文件")
        else:
            print("\n❌ 分阶段数据库迁移执行失败！")
            print("\n🔧 故障排除:")
            print("1. 查看日志文件: migration_execution.log")
            print("2. 检查数据库连接")
            print("3. 验证配置文件")
            print("4. 考虑执行回滚操作")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断执行")
        print("⚠️ 请检查系统状态并考虑回滚")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 执行过程中发生未预期错误: {e}")
        print(f"\n💥 执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())