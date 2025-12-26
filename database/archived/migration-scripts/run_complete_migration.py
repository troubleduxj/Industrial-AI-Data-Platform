#!/usr/bin/env python3
"""
运行完整数据库迁移的简化脚本
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append(str(Path(__file__).parent))

try:
    from complete_migration_system import CompleteMigrationSystem
except ImportError as e:
    print(f"❌ 导入迁移系统失败: {e}")
    print("请确保 complete_migration_system.py 文件存在")
    sys.exit(1)

async def main():
    """主函数"""
    print("🚀 启动完整数据库迁移系统...")
    
    # 检查数据库连接配置
    if not os.environ.get('DATABASE_URL'):
        print("⚠️ 未设置 DATABASE_URL 环境变量，使用默认配置")
        os.environ['DATABASE_URL'] = 'postgresql://postgres:Hanatech%40123@127.0.0.1:5432/devicemonitor'
    
    try:
        # 创建迁移系统实例
        migration_system = CompleteMigrationSystem()
        
        # 运行完整迁移
        success = await migration_system.run_complete_migration()
        
        if success:
            print("\n" + "="*60)
            print("🎉 数据库迁移成功完成！")
            print("="*60)
            print("✅ 所有表结构已创建")
            print("✅ 现有数据已迁移")
            print("✅ 索引和约束已建立")
            print("✅ 迁移报告已生成")
            print("="*60)
            return 0
        else:
            print("\n" + "="*60)
            print("❌ 数据库迁移失败！")
            print("="*60)
            print("请检查日志文件 complete_migration.log 获取详细信息")
            print("="*60)
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断迁移过程")
        return 1
    except Exception as e:
        print(f"\n❌ 迁移过程中发生未预期错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)