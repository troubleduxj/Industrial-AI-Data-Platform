#!/usr/bin/env python3
"""
分阶段数据库迁移演示脚本
展示完整的迁移流程
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('demo_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def demo_migration():
    """演示迁移流程"""
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                   分阶段数据库迁移演示                        ║
║                  Migration System Demo                      ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # 检查环境
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ 请设置 DATABASE_URL 环境变量")
        print("例如: export DATABASE_URL='postgresql://user:password@localhost:5432/database'")
        return
    
    print(f"🔗 数据库连接: {db_url[:50]}...")
    
    try:
        # 导入组件
        from phased_migration_strategy import (
            PhasedMigrationStrategy, MigrationConfig, 
            MigrationPhase, ConsistencyLevel
        )
        from data_consistency_validator import (
            DataConsistencyValidator, ValidationLevel
        )
        from configurable_read_switch import (
            ConfigurableReadSwitch, SwitchConfig, 
            SwitchStrategy, ReadSource, SwitchStatus
        )
        from migration_alerting_system import (
            MigrationAlertingSystem, AlertRule, 
            AlertType, AlertSeverity
        )
        
        print("✅ 组件导入成功")
        
        # 初始化组件
        strategy = PhasedMigrationStrategy(db_url)
        validator = DataConsistencyValidator(db_url)
        switch = ConfigurableReadSwitch(db_url)
        alerting = MigrationAlertingSystem(db_url)
        
        print("🔧 初始化系统组件...")
        await strategy.connect()
        await validator.connect()
        await switch.connect()
        await alerting.connect()
        print("✅ 系统组件初始化完成")
        
        # 演示1：创建迁移配置
        print("\n📋 演示1：创建迁移配置")
        print("-" * 40)
        
        migration_config = MigrationConfig(
            migration_id="demo_api_migration",
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
        
        success = await strategy.register_migration(migration_config)
        if success:
            print("✅ 迁移配置创建成功")
        else:
            print("❌ 迁移配置创建失败")
        
        # 演示2：设置告警规则
        print("\n🚨 演示2：设置告警规则")
        print("-" * 40)
        
        alert_rule = AlertRule(
            rule_id="demo_migration_failure",
            rule_name="演示迁移失败告警",
            alert_type=AlertType.MIGRATION_FAILURE,
            severity=AlertSeverity.CRITICAL,
            condition="SELECT COUNT(*) FROM t_sys_migration_logs WHERE migration_id = 'demo_api_migration' AND status = 'failed' AND created_at > NOW() - INTERVAL '5 minutes'",
            threshold=1.0,
            duration=60,
            auto_recovery=False
        )
        
        success = await alerting.register_alert_rule(alert_rule)
        if success:
            print("✅ 告警规则创建成功")
        else:
            print("❌ 告警规则创建失败")
        
        # 演示3：数据一致性验证（模拟）
        print("\n🔍 演示3：数据一致性验证")
        print("-" * 40)
        
        print("📊 模拟数据一致性检查...")
        print("   - 检查记录数量...")
        print("   - 检查主键匹配...")
        print("   - 检查字段值...")
        print("✅ 一致性检查完成（模拟）")
        print("   一致性分数: 0.9850")
        print("   发现差异: 15 个")
        print("   建议: 修复字段映射问题")
        
        # 演示4：配置读取切换
        print("\n🔄 演示4：配置读取切换")
        print("-" * 40)
        
        switch_config = SwitchConfig(
            config_id="demo_api_switch",
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
        
        success = await switch.register_switch_config(switch_config)
        if success:
            print("✅ 切换配置创建成功")
        else:
            print("❌ 切换配置创建失败")
        
        # 演示5：模拟渐进式切换
        print("\n📈 演示5：模拟渐进式切换")
        print("-" * 40)
        
        await switch.activate_switch(switch_config.config_id)
        print("✅ 切换已激活")
        
        switch_percentages = [10, 25, 50, 75, 100]
        for percentage in switch_percentages:
            print(f"🔄 切换到 {percentage}%...")
            await switch.update_switch_percentage(switch_config.config_id, percentage)
            await asyncio.sleep(1)  # 模拟等待
            print(f"   ✅ {percentage}% 切换完成")
        
        # 演示6：获取系统状态
        print("\n📊 演示6：获取系统状态")
        print("-" * 40)
        
        migration_status = await strategy.get_migration_status("demo_api_migration")
        if migration_status:
            print("📋 迁移状态:")
            print(f"   迁移ID: {migration_status.get('migration_id', 'N/A')}")
            config_info = migration_status.get('config', {})
            print(f"   当前阶段: {config_info.get('phase', 'N/A')}")
            print(f"   双写状态: {'启用' if config_info.get('dual_write_enabled') else '禁用'}")
            print(f"   读取源: {'目标表' if config_info.get('read_from_target') else '源表'}")
        
        switch_status = await switch.get_switch_status("demo_api_switch")
        if switch_status:
            print("\n🔄 切换状态:")
            config_info = switch_status.get('config', {})
            print(f"   配置ID: {config_info.get('config_id', 'N/A')}")
            print(f"   切换策略: {config_info.get('strategy', 'N/A')}")
            print(f"   切换百分比: {config_info.get('switch_percentage', 0)}%")
            print(f"   状态: {config_info.get('status', 'N/A')}")
        
        # 演示7：清理演示数据
        print("\n🧹 演示7：清理演示数据")
        print("-" * 40)
        
        await switch.deactivate_switch("demo_api_switch")
        print("✅ 切换配置已停用")
        
        # 清理连接
        await strategy.disconnect()
        await validator.disconnect()
        await switch.disconnect()
        await alerting.disconnect()
        print("✅ 系统资源已清理")
        
        print("\n🎉 演示完成！")
        print("\n📝 演示总结:")
        print("   ✅ 迁移配置创建")
        print("   ✅ 告警规则设置")
        print("   ✅ 一致性验证（模拟）")
        print("   ✅ 读取切换配置")
        print("   ✅ 渐进式切换演示")
        print("   ✅ 系统状态查询")
        print("   ✅ 资源清理")
        
        print("\n🚀 下一步:")
        print("   1. 运行 python start_migration.py 开始实际迁移")
        print("   2. 查看 QUICK_START_GUIDE.md 了解详细用法")
        print("   3. 查看 PHASED_MIGRATION_MANUAL.md 了解完整操作手册")
        
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}", exc_info=True)
        print(f"\n❌ 演示失败: {e}")
        
        # 尝试清理资源
        try:
            await strategy.disconnect()
            await validator.disconnect()
            await switch.disconnect()
            await alerting.disconnect()
        except:
            pass

async def main():
    """主函数"""
    try:
        await demo_migration()
    except KeyboardInterrupt:
        print("\n👋 演示被用户中断")
    except Exception as e:
        print(f"\n💥 演示启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())