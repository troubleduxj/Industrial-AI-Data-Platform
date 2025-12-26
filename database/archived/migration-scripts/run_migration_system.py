#!/usr/bin/env python3
"""
数据库迁移系统统一入口脚本
提供简化的命令行接口来管理数据库迁移和版本控制
"""

import asyncio
import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(str(Path(__file__).parent))

from migration_system import DatabaseMigrationSystem
from migration_automation import MigrationAutomation
from migration_monitor import MigrationMonitor, MigrationLogAnalyzer, MONITOR_CONFIG

def print_banner():
    """打印系统横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    数据库迁移和版本控制系统                    ║
║                   Database Migration & Version Control        ║
╠══════════════════════════════════════════════════════════════╣
║  功能: 数据库迁移、版本控制、监控告警、性能分析                ║
║  版本: 2.0.0                                                 ║
║  作者: API权限重构项目组                                      ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def get_db_url_from_env():
    """从环境变量获取数据库URL"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        # 尝试从配置文件读取
        config_file = Path('database/config.json')
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    db_url = config.get('database_url')
            except:
                pass
    
    if not db_url:
        db_url = "postgresql://user:password@localhost:5432/database"
        print(f"⚠️  未找到数据库配置，使用默认URL: {db_url}")
    
    return db_url

async def init_system(db_url: str):
    """初始化迁移系统"""
    print("🔧 初始化数据库迁移系统...")
    
    migration_system = DatabaseMigrationSystem(db_url)
    
    try:
        await migration_system.connect()
        await migration_system.initialize_migration_system()
        
        # 创建初始版本
        await migration_system.create_database_version("2.0.0", "API v2权限重构版本")
        await migration_system.set_current_version("2.0.0")
        
        print("✅ 迁移系统初始化完成")
        return True
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False
    finally:
        await migration_system.disconnect()

async def run_migrations(db_url: str, dry_run: bool = False):
    """运行迁移"""
    print(f"🚀 开始执行迁移 {'(干运行模式)' if dry_run else '(实际执行)'}")
    
    automation = MigrationAutomation(db_url)
    
    if dry_run:
        print("📋 预定义迁移列表:")
        for i, migration in enumerate(automation.predefined_migrations, 1):
            print(f"  {i}. {migration.name} ({migration.migration_type.value})")
            print(f"     描述: {migration.description}")
            print(f"     依赖: {migration.dependencies or '无'}")
            print()
        return True
    
    success = await automation.run_all_migrations()
    
    if success:
        print("🎉 所有迁移执行成功!")
        
        # 验证迁移结果
        print("🔍 验证迁移结果...")
        if await automation.validate_migrations():
            print("✅ 迁移验证通过!")
            return True
        else:
            print("⚠️ 迁移验证有警告，请检查日志")
            return False
    else:
        print("❌ 迁移执行失败!")
        return False

async def rollback_migrations(db_url: str):
    """回滚迁移"""
    print("🔄 开始回滚迁移...")
    
    # 确认操作
    response = input("⚠️  确定要回滚所有迁移吗？这将撤销所有数据库更改 (y/N): ")
    if response.lower() != 'y':
        print("取消回滚操作")
        return True
    
    automation = MigrationAutomation(db_url)
    success = await automation.rollback_all_migrations()
    
    if success:
        print("✅ 迁移回滚成功!")
        return True
    else:
        print("❌ 迁移回滚失败!")
        return False

async def show_status(db_url: str):
    """显示迁移状态"""
    print("📊 获取迁移状态...")
    
    automation = MigrationAutomation(db_url)
    status = await automation.get_migration_status()
    
    if status:
        print("\n" + "="*60)
        print("📈 迁移状态概览")
        print("="*60)
        print(f"当前版本: {status.get('current_version', 'N/A')}")
        print(f"总迁移数: {status.get('total_migrations', 0)}")
        print(f"成功执行: {status.get('successful', 0)}")
        print(f"执行失败: {status.get('failed', 0)}")
        print(f"待处理: {status.get('pending', 0)}")
        print(f"已回滚: {status.get('rolled_back', 0)}")
        
        if status.get('total_migrations', 0) > 0:
            success_rate = status.get('successful', 0) / status.get('total_migrations', 1) * 100
            print(f"成功率: {success_rate:.1f}%")
        
        print("="*60)
    else:
        print("❌ 无法获取迁移状态")

async def start_monitoring(db_url: str, interval: int = 30):
    """启动监控"""
    print(f"👁️  启动迁移监控 (检查间隔: {interval}秒)")
    print("按 Ctrl+C 停止监控")
    
    monitor = MigrationMonitor(db_url, MONITOR_CONFIG)
    
    try:
        await monitor.start_monitoring(interval)
    except KeyboardInterrupt:
        monitor.stop_monitoring()
        print("\n监控已停止")

async def show_dashboard(db_url: str):
    """显示仪表板"""
    print("📊 生成迁移仪表板...")
    
    monitor = MigrationMonitor(db_url, MONITOR_CONFIG)
    
    try:
        await monitor.connect()
        dashboard = await monitor.get_migration_dashboard()
        
        print("\n" + "="*80)
        print("📊 迁移仪表板")
        print("="*80)
        
        # 显示指标
        metrics = dashboard.get('metrics', {})
        print(f"总迁移数: {metrics.get('total_migrations', 0)}")
        print(f"成功数: {metrics.get('successful_migrations', 0)}")
        print(f"失败数: {metrics.get('failed_migrations', 0)}")
        print(f"待处理数: {metrics.get('pending_migrations', 0)}")
        print(f"成功率: {metrics.get('success_rate', 0):.2%}")
        print(f"平均执行时间: {metrics.get('avg_execution_time', 0):.0f}ms")
        
        # 显示最近迁移
        recent_migrations = dashboard.get('recent_migrations', [])
        if recent_migrations:
            print(f"\n📋 最近迁移 (最新{len(recent_migrations)}个):")
            for migration in recent_migrations:
                status_icon = "✅" if migration['status'] == 'success' else "❌" if migration['status'] == 'failed' else "⏳"
                print(f"  {status_icon} {migration['migration_name']} ({migration['status']})")
        
        # 显示告警
        alerts = dashboard.get('recent_alerts', [])
        if alerts:
            print(f"\n🚨 活跃告警 ({len(alerts)}个):")
            for alert in alerts:
                severity_icon = {"LOW": "ℹ️", "MEDIUM": "⚠️", "HIGH": "🔥", "CRITICAL": "💥"}.get(alert['severity'], "⚠️")
                print(f"  {severity_icon} [{alert['severity']}] {alert['title']}")
        else:
            print("\n✅ 无活跃告警")
        
        print("="*80)
        
    except Exception as e:
        print(f"❌ 获取仪表板数据失败: {e}")
    finally:
        await monitor.disconnect()

async def analyze_performance(db_url: str):
    """分析性能"""
    print("📈 分析迁移性能...")
    
    analyzer = MigrationLogAnalyzer(db_url)
    
    try:
        performance = await analyzer.analyze_performance()
        failures = await analyzer.analyze_failures()
        
        print("\n" + "="*60)
        print("📈 性能分析报告")
        print("="*60)
        
        # 整体统计
        overall = performance.get('overall_stats', {})
        if overall:
            print(f"最短执行时间: {overall.get('min_time', 0):.0f}ms")
            print(f"最长执行时间: {overall.get('max_time', 0):.0f}ms")
            print(f"平均执行时间: {overall.get('avg_time', 0):.0f}ms")
            print(f"中位数执行时间: {overall.get('median_time', 0):.0f}ms")
            print(f"95%分位数: {overall.get('p95_time', 0):.0f}ms")
        
        # 按类型统计
        type_perf = performance.get('type_performance', [])
        if type_perf:
            print(f"\n📊 按类型性能统计:")
            for stat in type_perf:
                print(f"  {stat['migration_type']}: 平均{stat['avg_time']:.0f}ms ({stat['count']}个)")
        
        # 失败分析
        failure_stats = failures.get('failure_stats', {})
        if failure_stats and failure_stats.get('total_failures', 0) > 0:
            print(f"\n🚨 失败分析:")
            print(f"总失败数: {failure_stats.get('total_failures', 0)}")
            print(f"失败类型数: {failure_stats.get('failed_types', 0)}")
            print(f"失败天数: {failure_stats.get('failure_days', 0)}")
        
        print("="*60)
        
    except Exception as e:
        print(f"❌ 性能分析失败: {e}")

async def export_report(db_url: str, output_file: str = None):
    """导出报告"""
    print("📄 导出迁移报告...")
    
    monitor = MigrationMonitor(db_url, MONITOR_CONFIG)
    
    try:
        await monitor.connect()
        report_file = await monitor.export_migration_report(output_file)
        
        if report_file:
            print(f"✅ 报告已导出: {report_file}")
            return True
        else:
            print("❌ 报告导出失败")
            return False
            
    except Exception as e:
        print(f"❌ 导出报告失败: {e}")
        return False
    finally:
        await monitor.disconnect()

async def interactive_menu(db_url: str):
    """交互式菜单"""
    while True:
        print("\n" + "="*60)
        print("🎛️  数据库迁移系统 - 交互式菜单")
        print("="*60)
        print("1. 初始化迁移系统")
        print("2. 查看迁移状态")
        print("3. 执行迁移 (预览)")
        print("4. 执行迁移 (实际)")
        print("5. 回滚迁移")
        print("6. 显示仪表板")
        print("7. 启动监控")
        print("8. 性能分析")
        print("9. 导出报告")
        print("0. 退出")
        print("="*60)
        
        try:
            choice = input("请选择操作 (0-9): ").strip()
            
            if choice == '0':
                print("👋 再见!")
                break
            elif choice == '1':
                await init_system(db_url)
            elif choice == '2':
                await show_status(db_url)
            elif choice == '3':
                await run_migrations(db_url, dry_run=True)
            elif choice == '4':
                await run_migrations(db_url, dry_run=False)
            elif choice == '5':
                await rollback_migrations(db_url)
            elif choice == '6':
                await show_dashboard(db_url)
            elif choice == '7':
                interval = input("监控间隔(秒，默认30): ").strip()
                interval = int(interval) if interval.isdigit() else 30
                await start_monitoring(db_url, interval)
            elif choice == '8':
                await analyze_performance(db_url)
            elif choice == '9':
                output = input("输出文件名(可选): ").strip() or None
                await export_report(db_url, output)
            else:
                print("❌ 无效选择，请重试")
                
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，退出程序")
            break
        except Exception as e:
            print(f"❌ 操作失败: {e}")
            input("按回车键继续...")

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='数据库迁移和版本控制系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s --init                    # 初始化迁移系统
  %(prog)s --migrate                 # 执行所有迁移
  %(prog)s --migrate --dry-run       # 预览迁移(不实际执行)
  %(prog)s --rollback                # 回滚所有迁移
  %(prog)s --status                  # 查看迁移状态
  %(prog)s --dashboard               # 显示仪表板
  %(prog)s --monitor                 # 启动监控
  %(prog)s --analyze                 # 性能分析
  %(prog)s --export report.json      # 导出报告
  %(prog)s --interactive             # 交互式菜单
        """
    )
    
    parser.add_argument('--db-url', help='数据库连接URL (可通过环境变量DATABASE_URL设置)')
    parser.add_argument('--init', action='store_true', help='初始化迁移系统')
    parser.add_argument('--migrate', action='store_true', help='执行迁移')
    parser.add_argument('--rollback', action='store_true', help='回滚迁移')
    parser.add_argument('--status', action='store_true', help='查看迁移状态')
    parser.add_argument('--dashboard', action='store_true', help='显示仪表板')
    parser.add_argument('--monitor', action='store_true', help='启动监控')
    parser.add_argument('--analyze', action='store_true', help='性能分析')
    parser.add_argument('--export', metavar='FILE', help='导出报告到文件')
    parser.add_argument('--interactive', action='store_true', help='交互式菜单')
    parser.add_argument('--dry-run', action='store_true', help='干运行模式(仅预览)')
    parser.add_argument('--interval', type=int, default=30, help='监控间隔(秒)')
    
    args = parser.parse_args()
    
    # 显示横幅
    print_banner()
    
    # 获取数据库URL
    db_url = args.db_url or get_db_url_from_env()
    
    try:
        # 根据参数执行相应操作
        if args.interactive:
            await interactive_menu(db_url)
        elif args.init:
            success = await init_system(db_url)
            sys.exit(0 if success else 1)
        elif args.migrate:
            success = await run_migrations(db_url, args.dry_run)
            sys.exit(0 if success else 1)
        elif args.rollback:
            success = await rollback_migrations(db_url)
            sys.exit(0 if success else 1)
        elif args.status:
            await show_status(db_url)
        elif args.dashboard:
            await show_dashboard(db_url)
        elif args.monitor:
            await start_monitoring(db_url, args.interval)
        elif args.analyze:
            await analyze_performance(db_url)
        elif args.export:
            success = await export_report(db_url, args.export)
            sys.exit(0 if success else 1)
        else:
            # 默认显示交互式菜单
            await interactive_menu(db_url)
            
    except KeyboardInterrupt:
        print("\n👋 用户中断，程序退出")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 程序执行错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())