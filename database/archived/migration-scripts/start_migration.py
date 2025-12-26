#!/usr/bin/env python3
"""
分阶段数据库迁移启动脚本
简化的启动接口，方便用户快速开始迁移
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

from implement_phased_migration import PhasedMigrationImplementor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_startup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                   分阶段数据库迁移系统                        ║
║                  Phased Database Migration                   ║
╠══════════════════════════════════════════════════════════════╣
║  版本: 1.0.0                                                ║
║  功能: 双写机制 | 一致性验证 | 配置化切换 | 智能告警          ║
║  作者: Kiro AI Assistant                                    ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_prerequisites():
    """检查前置条件"""
    logger.info("检查前置条件...")
    
    # 检查必要的文件
    required_files = [
        'phased_migration_strategy.py',
        'data_consistency_validator.py',
        'configurable_read_switch.py',
        'migration_alerting_system.py',
        'implement_phased_migration.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"缺少必要文件: {missing_files}")
        return False
    
    # 检查配置文件
    config_file = 'config.json'
    if not Path(config_file).exists():
        logger.warning(f"配置文件不存在: {config_file}")
        logger.info("将使用默认配置...")
    
    # 检查数据库连接
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        logger.warning("未设置 DATABASE_URL 环境变量")
        logger.info("请设置数据库连接字符串，例如:")
        logger.info("export DATABASE_URL='postgresql://user:password@localhost:5432/database'")
        return False
    
    logger.info("前置条件检查通过")
    return True

def create_default_config():
    """创建默认配置文件"""
    logger.info("创建默认配置文件...")
    
    default_config = {
        "database_url": os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/database'),
        "migrations": [
            {
                "migration_id": "api_permission_migration",
                "source_table": "api",
                "target_table": "t_sys_api_endpoints",
                "description": "API权限系统迁移"
            }
        ],
        "monitoring": {
            "enabled": True,
            "interval": 30
        },
        "validation": {
            "default_level": "detailed",
            "sample_size": 10000
        },
        "switch": {
            "default_strategy": "gradual",
            "switch_intervals": [10, 25, 50, 75, 100],
            "wait_time_seconds": 60
        },
        "alerting": {
            "enabled": True,
            "check_interval": 60
        }
    }
    
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(default_config, f, ensure_ascii=False, indent=2)
    
    logger.info("默认配置文件已创建: config.json")

async def interactive_setup():
    """交互式设置"""
    print("\n🔧 交互式设置")
    print("=" * 50)
    
    # 数据库连接
    db_url = input("请输入数据库连接URL (回车使用环境变量): ").strip()
    if not db_url:
        db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("❌ 必须提供数据库连接URL")
        return None
    
    # 迁移配置
    print("\n📋 配置迁移任务")
    migrations = []
    
    while True:
        print(f"\n配置第 {len(migrations) + 1} 个迁移任务:")
        migration_id = input("迁移ID (例如: api_permission_migration): ").strip()
        if not migration_id:
            break
        
        source_table = input("源表名: ").strip()
        target_table = input("目标表名: ").strip()
        description = input("描述 (可选): ").strip()
        
        if source_table and target_table:
            migrations.append({
                "migration_id": migration_id,
                "source_table": source_table,
                "target_table": target_table,
                "description": description or f"{source_table} 到 {target_table} 的迁移"
            })
            print(f"✅ 已添加迁移: {migration_id}")
        
        if input("\n是否继续添加迁移? (y/N): ").lower() != 'y':
            break
    
    if not migrations:
        print("❌ 至少需要配置一个迁移任务")
        return None
    
    # 监控设置
    print("\n📊 监控设置")
    monitoring_enabled = input("启用监控? (Y/n): ").lower() != 'n'
    monitoring_interval = 30
    if monitoring_enabled:
        try:
            interval_input = input("监控间隔(秒) [30]: ").strip()
            if interval_input:
                monitoring_interval = int(interval_input)
        except ValueError:
            pass
    
    # 生成配置
    config = {
        "database_url": db_url,
        "migrations": migrations,
        "monitoring": {
            "enabled": monitoring_enabled,
            "interval": monitoring_interval
        },
        "validation": {
            "default_level": "detailed",
            "sample_size": 10000
        },
        "switch": {
            "default_strategy": "gradual",
            "switch_intervals": [10, 25, 50, 75, 100],
            "wait_time_seconds": 60
        },
        "alerting": {
            "enabled": True,
            "check_interval": 60
        }
    }
    
    return config

async def run_migration_wizard():
    """运行迁移向导"""
    print("\n🚀 迁移执行向导")
    print("=" * 50)
    
    # 选择执行模式
    print("\n请选择执行模式:")
    print("1. 执行所有迁移")
    print("2. 执行指定迁移")
    print("3. 试运行模式")
    print("4. 仅启动监控")
    
    choice = input("\n请选择 (1-4): ").strip()
    
    if choice == '1':
        return {'mode': 'all'}
    elif choice == '2':
        migration_id = input("请输入迁移ID: ").strip()
        if migration_id:
            return {'mode': 'single', 'migration_id': migration_id}
    elif choice == '3':
        return {'mode': 'dry_run'}
    elif choice == '4':
        return {'mode': 'monitor_only'}
    
    return None

async def main():
    """主函数"""
    print_banner()
    
    # 检查前置条件
    if not check_prerequisites():
        print("\n❌ 前置条件检查失败，请解决上述问题后重试")
        return
    
    # 检查配置文件
    config_file = 'config.json'
    if not Path(config_file).exists():
        print("\n📝 未找到配置文件，开始交互式设置...")
        config = await interactive_setup()
        if not config:
            print("❌ 配置设置失败")
            return
        
        # 保存配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"✅ 配置已保存到: {config_file}")
    
    # 运行迁移向导
    execution_config = await run_migration_wizard()
    if not execution_config:
        print("❌ 执行配置失败")
        return
    
    # 确认执行
    print(f"\n📋 执行计划:")
    print(f"   模式: {execution_config['mode']}")
    if 'migration_id' in execution_config:
        print(f"   迁移ID: {execution_config['migration_id']}")
    
    confirm = input("\n确认执行? (y/N): ").lower()
    if confirm != 'y':
        print("❌ 用户取消执行")
        return
    
    # 开始执行
    print(f"\n🚀 开始执行迁移...")
    print(f"   开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 创建实施器
        implementor = PhasedMigrationImplementor(config_file)
        
        # 初始化系统
        await implementor.initialize_systems()
        
        # 根据模式执行
        if execution_config['mode'] == 'all':
            success = await implementor.run_all_migrations()
        elif execution_config['mode'] == 'single':
            # 查找指定迁移
            migration_config = None
            for config in implementor.config.get('migrations', []):
                if config['migration_id'] == execution_config['migration_id']:
                    migration_config = config
                    break
            
            if migration_config:
                success = await implementor.run_single_migration(migration_config)
            else:
                print(f"❌ 未找到迁移: {execution_config['migration_id']}")
                success = False
        elif execution_config['mode'] == 'dry_run':
            print("🔍 试运行模式 - 将执行以下迁移:")
            for config in implementor.config.get('migrations', []):
                print(f"   - {config['migration_id']}: {config.get('description', '')}")
            success = True
        elif execution_config['mode'] == 'monitor_only':
            print("📊 仅启动监控模式...")
            monitoring_task = await implementor.start_monitoring()
            if monitoring_task:
                print("✅ 监控系统已启动，按 Ctrl+C 停止")
                try:
                    await monitoring_task
                except KeyboardInterrupt:
                    monitoring_task.cancel()
                    print("\n📊 监控系统已停止")
            success = True
        
        # 生成报告
        if execution_config['mode'] not in ['dry_run', 'monitor_only']:
            report_file = await implementor.generate_final_report()
            print(f"\n📊 最终报告: {report_file}")
        
        # 清理资源
        await implementor.cleanup_systems()
        
        # 显示结果
        if success:
            print(f"\n✅ 迁移执行成功!")
            print(f"   结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"\n❌ 迁移执行失败!")
            print(f"   请查看日志文件获取详细信息")
    
    except KeyboardInterrupt:
        print(f"\n⚠️  用户中断执行")
    except Exception as e:
        print(f"\n❌ 执行过程中发生错误: {e}")
        logger.error(f"执行失败: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 再见!")
    except Exception as e:
        print(f"\n💥 启动失败: {e}")
        sys.exit(1)