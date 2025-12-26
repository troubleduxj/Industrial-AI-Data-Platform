#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流模块数据库迁移脚本 (PostgreSQL版本)
执行方式: python database/migrations/workflow/apply_workflow_pg.py
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def get_db_config():
    """获取数据库配置"""
    from dotenv import load_dotenv
    load_dotenv(project_root / '.env')
    
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'devicemonitor'),
    }


def execute_sql_file(cursor, filepath):
    """执行SQL文件 - 整体执行"""
    print(f"\n📄 执行SQL文件: {Path(filepath).name}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    try:
        cursor.execute(sql_content)
        print(f"  ✅ 执行成功")
        return True
    except Exception as e:
        error_msg = str(e)
        if 'already exists' in error_msg or 'duplicate key' in error_msg.lower():
            print(f"  ⚠️ 部分对象已存在，跳过")
            return True
        else:
            print(f"  ❌ 错误: {error_msg}")
            return False


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 工作流模块数据库迁移 (PostgreSQL)")
    print("=" * 60)
    
    try:
        import psycopg2
    except ImportError:
        print("❌ 需要安装 psycopg2: pip install psycopg2-binary")
        sys.exit(1)
    
    # 获取数据库配置
    db_config = get_db_config()
    print(f"\n📡 连接数据库: {db_config['host']}:{db_config['port']}/{db_config['database']}")
    
    try:
        # 连接数据库
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )
        cursor = conn.cursor()
        
        # SQL文件列表（按顺序执行）
        migration_dir = Path(__file__).parent
        sql_files = [
            '001_create_workflow_tables_pg.sql',
            '002_insert_workflow_menu_pg.sql',
            '003_insert_workflow_templates_pg.sql',
            '004_fix_menu_type.sql',  # 修复菜单类型
        ]
        
        all_success = True
        for sql_file in sql_files:
            filepath = migration_dir / sql_file
            if filepath.exists():
                success = execute_sql_file(cursor, filepath)
                if success:
                    conn.commit()
                else:
                    conn.rollback()
                    all_success = False
            else:
                print(f"\n⚠️ 文件不存在: {sql_file}")
        
        if all_success:
            print("\n" + "=" * 60)
            print("✅ 工作流模块数据库迁移完成!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("⚠️ 迁移完成，但有部分错误，请检查日志")
            print("=" * 60)
        
        # 显示创建的表
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name LIKE 't_workflow%'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print("\n📋 已创建的工作流相关表:")
        for table in tables:
            print(f"   - {table[0]}")
        
        # 显示模板数量
        try:
            cursor.execute("SELECT COUNT(*) FROM t_workflow_template")
            count = cursor.fetchone()[0]
            print(f"\n📋 已导入的工作流模板: {count} 个")
        except:
            pass
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
