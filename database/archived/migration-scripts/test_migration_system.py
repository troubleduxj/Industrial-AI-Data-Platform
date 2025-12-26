#!/usr/bin/env python3
"""
分阶段迁移系统测试脚本
验证所有组件是否正常工作
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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_database_connection():
    """测试数据库连接"""
    logger.info("测试数据库连接...")
    
    try:
        import asyncpg
        
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            logger.error("未设置 DATABASE_URL 环境变量")
            return False
        
        conn = await asyncpg.connect(db_url)
        result = await conn.fetchval("SELECT 1")
        await conn.close()
        
        if result == 1:
            logger.info("✅ 数据库连接成功")
            return True
        else:
            logger.error("❌ 数据库连接测试失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        return False

async def test_component_imports():
    """测试组件导入"""
    logger.info("测试组件导入...")
    
    try:
        from phased_migration_strategy import PhasedMigrationStrategy, MigrationConfig
        from data_consistency_validator import DataConsistencyValidator
        from configurable_read_switch import ConfigurableReadSwitch
        from migration_alerting_system import MigrationAlertingSystem
        
        logger.info("✅ 所有组件导入成功")
        return True
        
    except ImportError as e:
        logger.error(f"❌ 组件导入失败: {e}")
        return False

async def test_system_initialization():
    """测试系统初始化"""
    logger.info("测试系统初始化...")
    
    try:
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            logger.error("未设置 DATABASE_URL 环境变量")
            return False
        
        from phased_migration_strategy import PhasedMigrationStrategy
        from data_consistency_validator import DataConsistencyValidator
        from configurable_read_switch import ConfigurableReadSwitch
        from migration_alerting_system import MigrationAlertingSystem
        
        # 初始化组件
        strategy = PhasedMigrationStrategy(db_url)
        validator = DataConsistencyValidator(db_url)
        switch = ConfigurableReadSwitch(db_url)
        alerting = MigrationAlertingSystem(db_url)
        
        # 连接测试
        await strategy.connect()
        await validator.connect()
        await switch.connect()
        await alerting.connect()
        
        logger.info("✅ 系统初始化成功")
        
        # 清理连接
        await strategy.disconnect()
        await validator.disconnect()
        await switch.disconnect()
        await alerting.disconnect()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 系统初始化失败: {e}")
        return False

async def test_configuration_files():
    """测试配置文件"""
    logger.info("测试配置文件...")
    
    config_files = [
        'migration_configs.json',
        'read_switch_configs.json',
        'alerting_config.json',
        'validation_rules.json'
    ]
    
    all_valid = True
    
    for config_file in config_files:
        try:
            if Path(config_file).exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    json.load(f)
                logger.info(f"✅ {config_file} 格式正确")
            else:
                logger.warning(f"⚠️  {config_file} 不存在")
        except json.JSONDecodeError as e:
            logger.error(f"❌ {config_file} JSON格式错误: {e}")
            all_valid = False
        except Exception as e:
            logger.error(f"❌ {config_file} 读取失败: {e}")
            all_valid = False
    
    return all_valid

async def test_migration_config_creation():
    """测试迁移配置创建"""
    logger.info("测试迁移配置创建...")
    
    try:
        from phased_migration_strategy import (
            PhasedMigrationStrategy, MigrationConfig, 
            MigrationPhase, ConsistencyLevel
        )
        
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            logger.error("未设置 DATABASE_URL 环境变量")
            return False
        
        strategy = PhasedMigrationStrategy(db_url)
        await strategy.connect()
        
        # 创建测试配置
        config = MigrationConfig(
            migration_id="test_migration",
            source_table="test_source",
            target_table="test_target",
            phase=MigrationPhase.PREPARATION,
            consistency_level=ConsistencyLevel.STRICT
        )
        
        # 注册配置
        success = await strategy.register_migration(config)
        
        await strategy.disconnect()
        
        if success:
            logger.info("✅ 迁移配置创建成功")
            return True
        else:
            logger.error("❌ 迁移配置创建失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 迁移配置创建测试失败: {e}")
        return False

async def test_alert_rule_creation():
    """测试告警规则创建"""
    logger.info("测试告警规则创建...")
    
    try:
        from migration_alerting_system import (
            MigrationAlertingSystem, AlertRule, 
            AlertType, AlertSeverity
        )
        
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            logger.error("未设置 DATABASE_URL 环境变量")
            return False
        
        alerting = MigrationAlertingSystem(db_url)
        await alerting.connect()
        
        # 创建测试告警规则
        rule = AlertRule(
            rule_id="test_alert_rule",
            rule_name="测试告警规则",
            alert_type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.INFO,
            condition="SELECT 1",
            threshold=1.0,
            duration=60
        )
        
        # 注册规则
        success = await alerting.register_alert_rule(rule)
        
        await alerting.disconnect()
        
        if success:
            logger.info("✅ 告警规则创建成功")
            return True
        else:
            logger.error("❌ 告警规则创建失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 告警规则创建测试失败: {e}")
        return False

async def run_comprehensive_test():
    """运行综合测试"""
    logger.info("开始分阶段迁移系统综合测试...")
    logger.info("=" * 60)
    
    tests = [
        ("数据库连接", test_database_connection),
        ("组件导入", test_component_imports),
        ("配置文件", test_configuration_files),
        ("系统初始化", test_system_initialization),
        ("迁移配置创建", test_migration_config_creation),
        ("告警规则创建", test_alert_rule_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 测试: {test_name}")
        try:
            result = await test_func()
            if result:
                passed += 1
                logger.info(f"✅ {test_name} - 通过")
            else:
                logger.error(f"❌ {test_name} - 失败")
        except Exception as e:
            logger.error(f"💥 {test_name} - 异常: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！系统准备就绪")
        return True
    else:
        logger.error(f"⚠️  {total - passed} 个测试失败，请检查相关问题")
        return False

async def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                 分阶段迁移系统测试工具                        ║
║                Migration System Test Tool                   ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # 检查环境变量
    if not os.getenv('DATABASE_URL'):
        print("⚠️  请先设置 DATABASE_URL 环境变量")
        print("例如: export DATABASE_URL='postgresql://user:password@localhost:5432/database'")
        return
    
    # 运行测试
    success = await run_comprehensive_test()
    
    if success:
        print("\n🚀 系统测试通过，可以开始使用分阶段迁移系统！")
        print("\n下一步:")
        print("1. 运行 python database/start_migration.py 开始迁移")
        print("2. 或者直接运行 python database/implement_phased_migration.py")
    else:
        print("\n❌ 系统测试失败，请解决上述问题后重试")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {e}")
        sys.exit(1)