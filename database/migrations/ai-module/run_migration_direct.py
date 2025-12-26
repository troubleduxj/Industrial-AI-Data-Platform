#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接执行SQL迁移 - 使用配置对象
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import asyncpg
except ImportError:
    print("[ERROR] asyncpg not installed")
    sys.exit(1)

from app.settings.config import Settings

settings = Settings()


async def execute_migration():
    """执行数据库迁移"""
    
    print("=" * 60)
    print("[START] AI Module Database Migration")
    print("=" * 60)
    print()
    
    # 从Settings对象获取连接信息
    pg_creds = settings.tortoise_orm.connections.postgres.credentials
    
    host = pg_creds.host
    port = pg_creds.port
    database = pg_creds.database
    user = pg_creds.user
    password = pg_creds.password
    
    print(f"[CONNECT] {host}:{port}/{database}")
    print(f"[USER] {user}")
    print()
    
    # 连接数据库
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            timeout=30
        )
        print("[SUCCESS] Database connected")
        print()
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        print()
        print("[TIP] Please check:")
        print("   1. PostgreSQL is running")
        print("   2. Connection config in app/.env.dev")
        print("   3. User permissions")
        return False
    
    # 读取SQL文件
    migration_file = Path(__file__).parent / "003_optimize_predictions_table.sql"
    
    if not migration_file.exists():
        print(f"[ERROR] File not found: {migration_file}")
        return False
    
    print(f"[READ] {migration_file.name}")
    
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        print(f"[SUCCESS] Read {len(sql_content)} chars")
        print()
    except Exception as e:
        print(f"[ERROR] Read failed: {e}")
        return False
    
    # 执行SQL
    print("[EXECUTE] Running SQL...")
    print("-" * 60)
    
    try:
        await conn.execute(sql_content)
        print("[SUCCESS] Migration completed")
        print()
    except Exception as e:
        error_msg = str(e).lower()
        if 'already exists' in error_msg:
            print("[INFO] Indexes already exist (OK)")
        else:
            print(f"[ERROR] Failed: {e}")
            await conn.close()
            return False
    
    # 验证索引
    print("[VERIFY] Checking indexes...")
    print("-" * 60)
    
    try:
        indexes = await conn.fetch("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 't_ai_predictions'
            ORDER BY indexname;
        """)
        
        if indexes:
            print(f"[SUCCESS] Found {len(indexes)} indexes:")
            for idx in indexes:
                print(f"   * {idx['indexname']}")
            print()
        else:
            print("[WARNING] No indexes found")
            print("[TIP] Table may not exist yet")
    except Exception as e:
        print(f"[WARNING] Verify failed: {e}")
    
    # 性能测试
    print("[TEST] Query performance...")
    print("-" * 60)
    
    try:
        result = await conn.fetch("""
            EXPLAIN ANALYZE
            SELECT * FROM t_ai_predictions
            WHERE data_filters->>'device_code' = 'WLD-001'
            ORDER BY created_at DESC
            LIMIT 20;
        """)
        
        print("[QUERY PLAN]:")
        for row in result:
            line = list(row.values())[0]
            if 'Index Scan' in line or 'time' in line.lower():
                print(f"   {line}")
        print()
    except Exception as e:
        if 'does not exist' in str(e).lower():
            print("[INFO] Table doesn't exist yet (OK)")
        else:
            print(f"[WARNING] Test failed: {e}")
    
    await conn.close()
    
    print("=" * 60)
    print("[COMPLETE] Migration Done!")
    print("=" * 60)
    print()
    print("[NEXT]:")
    print("   1. Test API: python scripts/test_prediction_api.py")
    print("   2. Verify frontend")
    print()
    
    return True


if __name__ == '__main__':
    try:
        result = asyncio.run(execute_migration())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n[EXCEPTION] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

