#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知管理模块 - 数据库迁移执行脚本
"""

import os
import sys
import psycopg2
from pathlib import Path

# 数据库连接配置
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "127.0.0.1"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "Hanatech@123"),
    "database": os.getenv("POSTGRES_DATABASE", "devicemonitor"),
}


def execute_sql_file(cursor, filepath):
    """执行SQL文件"""
    print(f"\n📄 执行: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    try:
        cursor.execute(sql_content)
        print(f"   ✅ 执行成功")
        return True
    except Exception as e:
        print(f"   ❌ 执行失败: {str(e)}")
        return False


def main():
    print("=" * 50)
    print("通知管理模块 - 数据库迁移")
    print("=" * 50)
    
    # 获取当前目录
    current_dir = Path(__file__).parent
    
    # SQL文件列表（按顺序执行）
    sql_files = [
        "001_create_notification_tables.sql",
        "003_create_email_tables.sql",
        "004_create_notification_menu.sql",
    ]
    
    try:
        # 连接数据库
        print(f"\n🔗 连接数据库: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cursor = conn.cursor()
        print("   ✅ 连接成功")
        
        # 执行SQL文件
        success_count = 0
        for sql_file in sql_files:
            filepath = current_dir / sql_file
            if filepath.exists():
                if execute_sql_file(cursor, filepath):
                    success_count += 1
            else:
                print(f"\n⚠️ 文件不存在: {sql_file}")
        
        # 验证表是否创建成功
        print("\n📊 验证表结构:")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN (
                't_sys_notification', 't_sys_user_notification',
                't_sys_email_server', 't_sys_email_template',
                't_sys_notification_config', 't_sys_email_log'
            )
        """)
        tables = cursor.fetchall()
        for table in tables:
            print(f"   ✅ 表 {table[0]} 已创建")
        
        # 验证菜单是否创建成功
        print("\n📋 验证菜单:")
        cursor.execute("""
            SELECT id, name, path 
            FROM t_sys_menu 
            WHERE id BETWEEN 200 AND 204
            ORDER BY id
        """)
        menus = cursor.fetchall()
        for menu in menus:
            print(f"   ✅ 菜单 '{menu[1]}' (ID: {menu[0]}, 路径: {menu[2]}) 已创建")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 50)
        print(f"✅ 迁移完成! 成功执行 {success_count}/{len(sql_files)} 个文件")
        print("=" * 50)
        
    except psycopg2.Error as e:
        print(f"\n❌ 数据库错误: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 执行错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
