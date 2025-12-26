#!/usr/bin/env python3
"""
分阶段数据库迁移主启动脚本
提供用户友好的界面来执行完整的迁移流程
"""

import asyncio
import os
import sys
import subprocess
from pathlib import Path

def print_welcome():
    """打印欢迎信息"""
    welcome = """
╔══════════════════════════════════════════════════════════════╗
║                🚀 分阶段数据库迁移系统                       ║
║              Phased Database Migration System               ║
╠══════════════════════════════════════════════════════════════╣
║  欢迎使用分阶段数据库迁移系统！                              ║
║  本系统将帮助您安全、可靠地执行数据库迁移。                  ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(welcome)

def check_environment():
    """检查环境"""
    print("🔍 检查环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ 需要Python 3.7或更高版本")
        return False
    
    print(f"✅ Python版本: {sys.version.split()[0]}")
    
    # 检查数据库URL
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ 未设置 DATABASE_URL 环境变量")
        print("\n请设置数据库连接:")
        print("export DATABASE_URL='postgresql://user:password@localhost:5432/database'")
        return False
    
    print("✅ 数据库连接已配置")
    
    # 检查必要文件
    required_files = [
        'verify_system.py',
        'execute_migration.py',
        'config.json'
    ]
    
    for file in required_files:
        if not Path(file).exists():
            print(f"❌ 缺少必要文件: {file}")
            return False
    
    print("✅ 必要文件检查通过")
    return True

def install_dependencies():
    """安装依赖"""
    print("\n📦 安装Python依赖...")
    
    try:
        # 检查是否已安装
        import asyncpg
        import aiohttp
        print("✅ 依赖已安装")
        return True
    except ImportError:
        pass
    
    try:
        print("正在安装 asyncpg aiohttp...")
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', 'asyncpg', 'aiohttp'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 依赖安装成功")
            return True
        else:
            print(f"❌ 依赖安装失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 安装依赖时发生错误: {e}")
        return False

async def run_system_verification():
    """运行系统验证"""
    print("\n🔧 运行系统验证...")
    
    try:
        # 运行验证脚本
        process = await asyncio.create_subprocess_exec(
            sys.executable, 'verify_system.py',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            print(stdout.decode())
            return True
        else:
            print("❌ 系统验证失败")
            print(stdout.decode())
            if stderr:
                print(stderr.decode())
            return False
            
    except Exception as e:
        print(f"❌ 运行系统验证时发生错误: {e}")
        return False

async def run_migration():
    """运行迁移"""
    print("\n🚀 开始执行分阶段数据库迁移...")
    print("这可能需要几分钟时间，请耐心等待...")
    
    try:
        # 运行迁移脚本
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
            print("\n🎉 迁移执行成功！")
            return True
        else:
            print("\n❌ 迁移执行失败")
            return False
            
    except Exception as e:
        print(f"❌ 运行迁移时发生错误: {e}")
        return False

def show_menu():
    """显示菜单"""
    menu = """
请选择操作:
1. 🔍 系统验证 - 检查系统是否准备就绪
2. 🚀 执行迁移 - 运行完整的分阶段迁移
3. 📚 查看文档 - 显示可用文档
4. 🛠️ 故障排除 - 显示常见问题解决方案
5. ❌ 退出

请输入选项 (1-5): """
    
    return input(menu).strip()

def show_documentation():
    """显示文档"""
    docs = """
📚 可用文档:

1. QUICK_START_GUIDE.md - 快速开始指南
2. PHASED_MIGRATION_MANUAL.md - 详细操作手册  
3. README_PHASED_MIGRATION.md - 系统概述
4. README_MIGRATION_SYSTEM.md - 原系统说明

使用方法:
  cat QUICK_START_GUIDE.md
  或在编辑器中打开相应文件
    """
    print(docs)

def show_troubleshooting():
    """显示故障排除"""
    troubleshooting = """
🛠️ 常见问题解决方案:

1. 数据库连接问题:
   - 检查 DATABASE_URL 环境变量
   - 确认数据库服务正在运行
   - 验证用户名和密码

2. 依赖安装问题:
   - 运行: pip install asyncpg aiohttp
   - 检查Python版本 (需要3.7+)
   - 考虑使用虚拟环境

3. 文件缺失问题:
   - 确认所有Python文件都存在
   - 检查配置文件是否正确

4. 权限问题:
   - 确认数据库用户有足够权限
   - 检查文件读写权限

5. 迁移失败:
   - 查看日志文件: migration_execution.log
   - 检查数据库表结构
   - 考虑回滚操作

如需更多帮助，请查看详细文档或日志文件。
    """
    print(troubleshooting)

async def main():
    """主函数"""
    print_welcome()
    
    # 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败，请解决上述问题后重试")
        return
    
    # 安装依赖
    if not install_dependencies():
        print("\n❌ 依赖安装失败，请手动安装后重试")
        return
    
    # 主循环
    while True:
        try:
            choice = show_menu()
            
            if choice == '1':
                # 系统验证
                success = await run_system_verification()
                if success:
                    print("\n✅ 系统验证通过，可以执行迁移")
                else:
                    print("\n❌ 系统验证失败，请解决问题后重试")
            
            elif choice == '2':
                # 执行迁移
                print("\n⚠️ 即将开始数据库迁移，这是一个重要操作！")
                confirm = input("确认执行迁移? (输入 'YES' 确认): ")
                
                if confirm == 'YES':
                    success = await run_migration()
                    if success:
                        print("\n🎊 恭喜！迁移执行成功！")
                        print("请验证应用程序功能并监控系统性能。")
                        break
                    else:
                        print("\n❌ 迁移执行失败，请查看日志并考虑回滚。")
                else:
                    print("❌ 迁移已取消")
            
            elif choice == '3':
                # 查看文档
                show_documentation()
            
            elif choice == '4':
                # 故障排除
                show_troubleshooting()
            
            elif choice == '5':
                # 退出
                print("👋 再见！")
                break
            
            else:
                print("❌ 无效选项，请重新选择")
            
            # 等待用户按键继续
            if choice in ['1', '2', '3', '4']:
                input("\n按回车键继续...")
                print("\n" + "="*60)
        
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，再见！")
            break
        except Exception as e:
            print(f"\n💥 发生错误: {e}")
            print("请重试或查看故障排除指南")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 再见！")
    except Exception as e:
        print(f"\n💥 启动失败: {e}")
        sys.exit(1)