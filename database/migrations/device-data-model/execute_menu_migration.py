#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行前端菜单创建脚本

用途: 创建"数据模型管理"前端菜单
使用方法:
    python execute_menu_migration.py
"""

import sys
from pathlib import Path
import psycopg2
from psycopg2 import sql

# 设置控制台编码为 UTF-8 (Windows)
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 数据库配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'user': 'postgres',
    'password': 'Hanatech@123',
    'database': 'devicemonitor'
}

def execute_menu_migration():
    """执行菜单创建脚本"""
    print("=" * 60)
    print("  执行前端菜单创建脚本")
    print("=" * 60)
    print()
    
    # 获取SQL文件路径
    script_dir = Path(__file__).resolve().parent
    sql_file = script_dir / "008_create_frontend_menu_simple.sql"
    
    if not sql_file.exists():
        print(f"❌ SQL文件不存在: {sql_file}")
        return 1
    
    # 连接数据库
    print(f"连接数据库: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor()
        print("✓ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return 1
    
    try:
        # 读取并执行SQL
        print(f"\n执行SQL文件: {sql_file.name}")
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        cursor.execute(sql_content)
        conn.commit()
        
        # 验证结果
        print("\n验证菜单创建...")
        cursor.execute("""
            SELECT id, name, path, parent_id 
            FROM t_sys_menu 
            WHERE path LIKE '/data-model%'
            ORDER BY COALESCE(parent_id, id), order_num
        """)
        menus = cursor.fetchall()
        
        print(f"\n✓ 创建菜单数量: {len(menus)}")
        print("\n创建的菜单:")
        print("-" * 60)
        for menu_id, name, path, parent_id in menus:
            indent = "  " if parent_id else ""
            print(f"{indent}[{menu_id}] {name} ({path})")
        
        # 验证权限
        cursor.execute("""
            SELECT COUNT(*) 
            FROM t_sys_role_menu rm
            JOIN t_sys_menu m ON rm.menu_id = m.id
            WHERE m.path LIKE '/data-model%'
        """)
        permission_count = cursor.fetchone()[0]
        
        print(f"\n✓ 分配权限数量: {permission_count}")
        print("\n" + "=" * 60)
        print("✅ 菜单创建成功！")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 执行失败: {e}")
        print("所有更改已回滚。")
        return 1
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    sys.exit(execute_menu_migration())

