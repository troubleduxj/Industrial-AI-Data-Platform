#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用asyncpg执行数据库迁移脚本
执行003_optimize_predictions_table.sql迁移脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import asyncpg
except ImportError:
    print("[ERROR] Need to install asyncpg: pip install asyncpg")
    sys.exit(1)

from app.settings.config import Settings

settings = Settings()


async def execute_migration():
    """执行数据库迁移"""
    
    print("=" * 60)
    print("[START] Execute AI module database migration")
    print("=" * 60)
    print()
    
    # 解析数据库URL
    db_url = settings.DATABASE_URL
    
    # 从URL提取连接信息
    # 格式: postgresql://user:password@host:port/database
    if db_url.startswith('postgresql://'):
        url_parts = db_url.replace('postgresql://', '').split('@')
        if len(url_parts) == 2:
            auth_part = url_parts[0]
            host_part = url_parts[1]
            
            user, password = auth_part.split(':')
            host_port_db = host_part.split('/')
            host_port = host_port_db[0].split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 5432
            database = host_port_db[1] if len(host_port_db) > 1 else 'postgres'
        else:
            print("[ERROR] Cannot parse database URL format")
            return False
    else:
        print("[ERROR] Unsupported database URL format")
        return False
    
    print(f"[CONNECT] Database: {host}:{port}/{database}")
    print(f"[USER] {user}")
    print()
    
    # 连接数据库
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        print("[SUCCESS] Database connection successful")
        print()
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        print()
        print("[TIP] Please check:")
        print("   1. PostgreSQL service is running")
        print("   2. Database connection config is correct (app/.env.dev)")
        print("   3. Database user has sufficient permissions")
        return False
    
    # 读取迁移SQL文件
    migration_file = Path(__file__).parent / "003_optimize_predictions_table.sql"
    
    if not migration_file.exists():
        print(f"[ERROR] Migration file not found: {migration_file}")
        return False
    
    print(f"[READ] Migration file: {migration_file.name}")
    
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        print(f"[SUCCESS] Successfully read migration file ({len(sql_content)} chars)")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to read migration file: {e}")
        return False
    
    # 执行SQL迁移
    print("[EXECUTE] Start executing SQL migration...")
    print("-" * 60)
    
    try:
        # 执行SQL脚本
        await conn.execute(sql_content)
        print("[SUCCESS] SQL migration executed successfully")
        print()
        
    except Exception as e:
        error_msg = str(e).lower()
        if 'already exists' in error_msg:
            print("[INFO] Some indexes already exist, this is normal")
            print(f"   Details: {e}")
        else:
            print(f"[ERROR] Migration execution failed: {e}")
            await conn.close()
            return False
    
    # 验证索引创建
    print("[VERIFY] Verifying index creation...")
    print("-" * 60)
    
    try:
        indexes = await conn.fetch("""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE tablename = 't_ai_predictions'
            ORDER BY indexname;
        """)
        
        if not indexes:
            print("[WARNING] No indexes found for t_ai_predictions table")
            print("[TIP] Table may not exist yet, please create table first")
        else:
            print(f"[SUCCESS] Found {len(indexes)} indexes:")
            print()
            for idx in indexes:
                print(f"   * {idx['indexname']}")
            print()
        
    except Exception as e:
        print(f"[WARNING] Index verification failed: {e}")
        print("[TIP] Table may not exist yet")
    
    # 测试查询性能
    print("[TEST] Testing query performance...")
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
            line = row['QUERY PLAN'] if 'QUERY PLAN' in row else str(row)
            if 'Index Scan' in line or 'execution time' in line.lower() or 'Planning' in line:
                print(f"   {line}")
        print()
        
    except Exception as e:
        if 'does not exist' in str(e).lower():
            print("[INFO] Table t_ai_predictions does not exist, skipping performance test")
            print("   This is normal, indexes will take effect after table creation")
        else:
            print(f"[WARNING] Query performance test failed: {e}")
    
    await conn.close()
    
    print("=" * 60)
    print("[COMPLETE] Migration execution completed!")
    print("=" * 60)
    print()
    print("[NEXT STEPS]:")
    print("   1. If table doesn't exist, create t_ai_predictions table first")
    print("   2. Test API: python scripts/test_prediction_api.py")
    print("   3. Verify frontend functionality")
    print()
    
    return True


if __name__ == '__main__':
    try:
        result = asyncio.run(execute_migration())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[EXCEPTION] Migration execution exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

