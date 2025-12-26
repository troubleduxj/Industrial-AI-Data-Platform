#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行Mock规则插入脚本
为AI预测管理添加Mock接口配置
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncpg
from app.settings.config import Settings

settings = Settings()


async def main():
    """主函数"""
    print("=" * 70)
    print("  Insert AI Prediction Mock Rules")
    print("=" * 70)
    print()
    
    pg_creds = settings.tortoise_orm.connections.postgres.credentials
    
    conn = await asyncpg.connect(
        host=pg_creds.host,
        port=pg_creds.port,
        database=pg_creds.database,
        user=pg_creds.user,
        password=pg_creds.password
    )
    
    print(f"[CONNECT] {pg_creds.host}:{pg_creds.port}/{pg_creds.database}")
    print("[SUCCESS] Database connected")
    print()
    
    # 读取SQL文件
    sql_file = Path(__file__).parent / "004_insert_ai_prediction_mock_rules.sql"
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"[READ] {sql_file.name}")
    print(f"[INFO] Content: {len(sql_content)} chars")
    print()
    
    # 执行SQL
    print("[EXECUTE] Inserting mock rules...")
    print("-" * 70)
    
    try:
        await conn.execute(sql_content)
        print("[SUCCESS] Mock rules inserted")
        print()
    except Exception as e:
        print(f"[ERROR] {e}")
        await conn.close()
        return 1
    
    # 验证结果
    print("[VERIFY] Checking inserted rules...")
    print("-" * 70)
    
    rows = await conn.fetch("""
        SELECT id, name, method, url_pattern, enabled
        FROM t_sys_mock_data
        WHERE url_pattern LIKE '%ai%prediction%'
           OR url_pattern LIKE '%trend-prediction%'
        ORDER BY priority DESC, id;
    """)
    
    if rows:
        print(f"[SUCCESS] Found {len(rows)} AI prediction mock rules:")
        print()
        for i, row in enumerate(rows, 1):
            status = "[ON]" if row['enabled'] else "[OFF]"
            print(f"   [{i}] {status} {row['method']:6} {row['url_pattern']}")
            print(f"       {row['name']}")
        print()
    else:
        print("[WARNING] No mock rules found")
    
    await conn.close()
    
    print("=" * 70)
    print("[COMPLETE] Mock rules configuration done!")
    print("=" * 70)
    print()
    print("[NEXT STEPS]:")
    print("   1. Visit Mock Management page in system")
    print("   2. Check 'AI Prediction' related mock rules")
    print("   3. Toggle rules on/off as needed")
    print("   4. Test frontend with mock data")
    print()
    
    return 0


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

