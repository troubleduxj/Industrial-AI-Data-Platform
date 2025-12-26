#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版数据库迁移脚本 - 直接执行SQL
执行003_optimize_predictions_table.sql迁移脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("[错误] 需要安装psycopg2: pip install psycopg2-binary")
    sys.exit(1)

from app.settings.config import Settings

settings = Settings()


def execute_migration():
    """执行数据库迁移"""
    
    print("=" * 60)
    print("[开始] 执行AI模块数据库迁移")
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
            print("[错误] 无法解析数据库URL格式")
            return False
    else:
        print("[错误] 不支持的数据库URL格式")
        return False
    
    print(f"[连接] 数据库: {host}:{port}/{database}")
    print(f"[用户] {user}")
    print()
    
    # 连接数据库
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print("[成功] 数据库连接成功")
        print()
    except Exception as e:
        print(f"[错误] 数据库连接失败: {e}")
        print()
        print("[提示] 请检查:")
        print("   1. PostgreSQL服务是否运行")
        print("   2. 数据库连接配置是否正确 (app/.env.dev)")
        print("   3. 数据库用户权限是否足够")
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
    
    cursor = conn.cursor()
    
    try:
        # 执行SQL脚本
        cursor.execute(sql_content)
        print("[成功] SQL迁移执行完成")
        print()
        
    except Exception as e:
        error_msg = str(e).lower()
        if 'already exists' in error_msg:
            print("[提示] 部分索引已存在，这是正常的")
            print(f"   详细信息: {e}")
        else:
            print(f"[错误] 执行迁移失败: {e}")
            cursor.close()
            conn.close()
            return False
    
    # 验证索引创建
    print("[验证] 验证索引创建...")
    print("-" * 60)
    
    try:
        cursor.execute("""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE tablename = 't_ai_predictions'
            ORDER BY indexname;
        """)
        
        indexes = cursor.fetchall()
        
        if not indexes:
            print("[警告] 未找到t_ai_predictions表的索引")
            print("[提示] 可能表还不存在，请先创建表")
        else:
            print(f"[成功] 找到 {len(indexes)} 个索引:")
            print()
            for idx_name, idx_def in indexes:
                print(f"   * {idx_name}")
            print()
        
    except Exception as e:
        print(f"[警告] 验证索引失败: {e}")
        print("[提示] 可能表还不存在")
    
    # 测试查询性能
    print("[测试] 测试查询性能...")
    print("-" * 60)
    
    try:
        cursor.execute("""
            EXPLAIN ANALYZE
            SELECT * FROM t_ai_predictions
            WHERE data_filters->>'device_code' = 'WLD-001'
            ORDER BY created_at DESC
            LIMIT 20;
        """)
        
        result = cursor.fetchall()
        
        print("[查询计划]:")
        for row in result:
            line = row[0]
            if 'Index Scan' in line or 'execution time' in line.lower() or 'Planning' in line:
                print(f"   {line}")
        print()
        
    except Exception as e:
        if 'does not exist' in str(e).lower():
            print("[提示] 表t_ai_predictions不存在，跳过性能测试")
            print("   这是正常的，索引会在表创建后生效")
        else:
            print(f"[警告] 查询性能测试失败: {e}")
    
    cursor.close()
    conn.close()
    
    print("=" * 60)
    print("[完成] 迁移执行完成！")
    print("=" * 60)
    print()
    print("[后续步骤]:")
    print("   1. 如果表不存在，请先创建t_ai_predictions表")
    print("   2. 测试API接口: python scripts/test_prediction_api.py")
    print("   3. 验证前端功能")
    print()
    
    return True


if __name__ == '__main__':
    try:
        result = execute_migration()
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n[中断] 迁移被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n[异常] 迁移执行异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

