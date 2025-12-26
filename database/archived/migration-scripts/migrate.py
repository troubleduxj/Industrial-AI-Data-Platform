#!/usr/bin/env python3
"""
分阶段数据库迁移 - 一键执行脚本
这是最终的执行入口，会自动处理所有前置条件并执行迁移
"""

import asyncio
import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """打印横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                🚀 分阶段数据库迁移                           ║
║              Phased Database Migration                       ║
║                                                              ║
║  一键执行完整的分阶段数据库迁移流程                          ║
║  Automated phased database migration execution              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 7):
        print("❌ 错误: 需要Python 3.7或更高版本")
        print(f"   当前版本: {sys.version}")
        return False
    
    print(f"✅ Python版本: {sys.version.split()[0]}")
    return True

def check_database_url():
    """检查数据库URL"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ 错误: 未设置 DATABASE_URL 环境变量")
        print("\n请设置数据库连接:")
        print("export DATABASE_URL='postgresql://user:password@localhost:5432/database'")
        print("\n示例:")
        print("export DATABASE_URL='postgresql://postgres:password@localhost:5432/mydb'")
        return False
    
    print("✅ 数据库连接已配置")
    return True

def install_dependencies():
    """安装Python依赖"""
    print("\n📦 检查并安装Python依赖...")
    
    required_packages = ['asyncpg', 'aiohttp']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} 已安装")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} 未安装")
    
    if missing_packages:
        print(f"\n正在安装缺失的依赖: {' '.join(missing_packages)}")
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install'
            ] + missing_packages, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 依赖安装成功")
                return True
            else:
                print(f"❌ 依赖安装失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ 安装依赖时发生错误: {e}")
            return False
    
    return True

def check_required_files():
    """检查必需文件"""
    print("\n📁 检查必需文件...")
    
    required_files = [
        'phased_migration_strategy.py',
        'data_consistency_validator.py',
        'configurable_read_switch.py',
        'migration_alerting_system.py',
        'execute_migration.py',
        'verify_system.py',
        'config.json'
    ]
    
    missing_files = []
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ 缺少必需文件: {missing_files}")
        return False
    
    return True

async def test_database_connection():
    """测试数据库连接"""
    print("\n🔗 测试数据库连接...")
    
    try:
        import asyncpg
        db_url = os.getenv('DATABASE_URL')
        
        conn = await asyncpg.connect(db_url)
        result = await conn.fetchval("SELECT 1")
        await conn.close()
        
        if result == 1:
            print("✅ 数据库连接测试成功")
            return True
        else:
            print("❌ 数据库连接测试失败")
            return False
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("\n请检查:")
        print("1. 数据库服务是否运行")
        print("2. 连接字符串是否正确")
        print("3. 用户名密码是否正确")
        print("4. 网络连接是否正常")
        return False

async def run_system_verification():
    """运行系统验证"""
    print("\n🔧 运行完整系统验证...")
    
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable, 'verify_system.py',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            print("✅ 系统验证通过")
            return True
        else:
            print("❌ 系统验证失败")
            print(stdout.decode())
            if stderr:
                print(stderr.decode())
            return False
    except Exception as e:
        print(f"❌ 系统验证异常: {e}")
        return False

async def execute_migration():
    """执行迁移"""
    print("\n🚀 开始执行分阶段数据库迁移...")
    print("=" * 60)
    print("这将执行以下6个阶段:")
    print("1. 准备阶段 - 配置初始化")
    print("2. 双写阶段 - 启用双写机制")
    print("3. 验证阶段 - 数据一致性检查")
    print("4. 读取切换阶段 - 渐进式切换")
    print("5. 清理阶段 - 禁用双写")
    print("6. 完成阶段 - 生成报告")
    print("=" * 60)
    
    confirm = input("\n确认开始迁移? (输入 'YES' 确认): ")
    if confirm != 'YES':
        print("❌ 迁移已取消")
        return False
    
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable, 'execute_migration.py',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        
        # 实时显示输出
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            print(line.decode().rstrip())
        
        await process.wait()
        
        if process.returncode == 0:
            return True
        else:
            return False
    except Exception as e:
        print(f"❌ 执行迁移时发生错误: {e}")
        return False

def show_post_migration_info():
    """显示迁移后信息"""
    info = """
🎉 分阶段数据库迁移执行完成！

📋 后续步骤:
1. 检查生成的报告文件:
   - validation_report_*.json
   - final_validation_report_*.json  
   - migration_summary_*.json

2. 验证应用程序功能:
   - 测试API接口
   - 验证权限系统
   - 检查数据完整性

3. 监控系统性能:
   - 响应时间
   - 数据库性能
   - 错误率

4. 清理工作:
   - 清理日志文件
   - 备份配置文件
   - 更新文档

📚 相关文档:
- IMPLEMENTATION_GUIDE.md - 实施指南
- PHASED_MIGRATION_MANUAL.md - 详细手册
- QUICK_START_GUIDE.md - 快速指南

🛠️ 如果遇到问题:
1. 查看日志文件: migration_execution.log
2. 运行系统验证: python verify_system.py
3. 查看故障排除指南
4. 考虑回滚操作

祝贺你成功完成分阶段数据库迁移！🎊
    """
    print(info)

async def main():
    """主函数"""
    print_banner()
    
    print("🔍 执行前置条件检查...")
    print("=" * 40)
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 检查数据库URL
    if not check_database_url():
        sys.exit(1)
    
    # 安装依赖
    if not install_dependencies():
        sys.exit(1)
    
    # 检查必需文件
    if not check_required_files():
        sys.exit(1)
    
    # 测试数据库连接
    if not await test_database_connection():
        sys.exit(1)
    
    # 运行系统验证
    if not await run_system_verification():
        print("\n❌ 系统验证失败，请解决问题后重试")
        sys.exit(1)
    
    print("\n✅ 所有前置条件检查通过！")
    print("=" * 40)
    
    # 执行迁移
    success = await execute_migration()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 迁移执行成功！")
        show_post_migration_info()
    else:
        print("\n" + "=" * 60)
        print("❌ 迁移执行失败！")
        print("\n🔧 故障排除:")
        print("1. 查看日志文件: migration_execution.log")
        print("2. 检查数据库状态")
        print("3. 验证配置文件")
        print("4. 考虑执行回滚操作")
        print("5. 查看 IMPLEMENTATION_GUIDE.md 获取详细帮助")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断执行")
        print("⚠️ 请检查系统状态并考虑回滚")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 执行过程中发生未预期错误: {e}")
        sys.exit(1)