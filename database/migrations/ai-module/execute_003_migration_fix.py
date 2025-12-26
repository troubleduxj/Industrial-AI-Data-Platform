#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行003_optimize_predictions_table.sql迁移脚本
为t_ai_predictions表创建JSONB索引
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tortoise import Tortoise
from app.settings.config import Settings

settings = Settings()


async def execute_migration():
    """执行数据库迁移"""
    
    print("=" * 60)
    print("[开始] 执行AI模块数据库迁移")
    print("=" * 60)
    print()
    
    # 初始化数据库连接
    try:
        await Tortoise.init(
            db_url=settings.DATABASE_URL,
            modules={'models': ['app.models']}
        )
        print("[成功] 数据库连接成功")
        db_info = settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'N/A'
        print(f"   数据库: {db_info}")
        print()
    except Exception as e:
        print(f"[错误] 数据库连接失败: {e}")
        return False
    
    # 读取迁移SQL文件
    migration_file = Path(__file__).parent / "003_optimize_predictions_table.sql"
    
    if not migration_file.exists():
        print(f"[错误] 迁移文件不存在: {migration_file}")
        return False
    
    print(f"[读取] 迁移文件: {migration_file.name}")
    
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        print(f"[成功] 成功读取迁移文件 ({len(sql_content)} 字符)")
        print()
    except Exception as e:
        print(f"[错误] 读取迁移文件失败: {e}")
        return False
    
    # 执行SQL迁移
    print("[执行] 开始执行SQL迁移...")
    print("-" * 60)
    
    conn = Tortoise.get_connection("default")
    
    try:
        # 执行整个SQL脚本
        await conn.execute_script(sql_content)
        print("[成功] SQL迁移执行完成")
        print()
        
    except Exception as e:
        error_msg = str(e).lower()
        if 'already exists' in error_msg:
            print("[提示] 部分索引已存在，继续执行...")
        else:
            print(f"[错误] 执行迁移失败: {e}")
            return False
    
    # 验证索引创建
    print("[验证] 验证索引创建...")
    print("-" * 60)
    
    try:
        # 查询t_ai_predictions表的所有索引
        result = await conn.execute_query_dict("""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE tablename = 't_ai_predictions'
            ORDER BY indexname;
        """)
        
        if not result:
            print("[警告] 未找到t_ai_predictions表的索引")
        else:
            print(f"[成功] 找到 {len(result)} 个索引:")
            print()
            for idx in result:
                print(f"   * {idx['indexname']}")
            print()
        
    except Exception as e:
        print(f"[警告] 验证索引失败: {e}")
    
    # 测试查询性能
    print("[测试] 测试查询性能...")
    print("-" * 60)
    
    try:
        # 测试JSONB查询
        test_query = """
            EXPLAIN ANALYZE
            SELECT * FROM t_ai_predictions
            WHERE data_filters->>'device_code' = 'WLD-001'
            ORDER BY created_at DESC
            LIMIT 20;
        """
        
        result = await conn.execute_query(test_query)
        
        print("[查询计划]:")
        for row in result:
            line = row[0] if isinstance(row, (list, tuple)) else str(row)
            if 'Index Scan' in line or 'execution time' in line.lower() or 'Planning' in line:
                print(f"   {line}")
        print()
        
    except Exception as e:
        print(f"[警告] 查询性能测试失败: {e}")
    
    await Tortoise.close_connections()
    
    print("=" * 60)
    print("[完成] 迁移执行完成！")
    print("=" * 60)
    print()
    print("[后续步骤]:")
    print("   1. 测试API接口: python scripts/test_prediction_api.py")
    print("   2. 查看迁移日志")
    print("   3. 验证前端功能")
    print()
    
    return True


if __name__ == '__main__':
    try:
        result = asyncio.run(execute_migration())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n[中断] 迁移被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n[异常] 迁移执行异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

