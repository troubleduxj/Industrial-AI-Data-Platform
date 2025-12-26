#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流模块数据库迁移脚本
执行方式: python database/migrations/workflow/apply_workflow.py
"""

import os
import sys
import pymysql
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 从环境变量或配置文件获取数据库连接信息
def get_db_config():
    """获取数据库配置"""
    from dotenv import load_dotenv
    load_dotenv(project_root / '.env')
    
    return {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'device_monitor'),
        'charset': 'utf8mb4'
    }


def execute_sql_file(cursor, filepath):
    """执行SQL文件"""
    print(f"\n📄 执行SQL文件: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 分割SQL语句
    statements = []
    current_statement = []
    
    for line in sql_content.split('\n'):
        # 跳过注释和空行
        stripped = line.strip()
        if stripped.startswith('--') or not stripped:
            continue
        
        current_statement.append(line)
        
        if stripped.endswith(';'):
            statements.append('\n'.join(current_statement))
            current_statement = []
    
    # 执行每条语句
    success_count = 0
    error_count = 0
    
    for stmt in statements:
        stmt = stmt.strip()
        if not stmt:
            continue
        
        try:
            cursor.execute(stmt)
            success_count += 1
        except pymysql.Error as e:
            error_code = e.args[0]
            # 忽略表已存在、重复键等常见错误
            if error_code in [1050, 1060, 1061, 1062, 1065, 1146]:
                print(f"  ⚠️ 跳过: {e.args[1][:50]}...")
            else:
                print(f"  ❌ 错误: {e}")
                error_count += 1
    
    print(f"  ✅ 成功执行 {success_count} 条语句, {error_count} 条错误")
    return error_count == 0


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 工作流模块数据库迁移")
    print("=" * 60)
    
    # 获取数据库配置
    db_config = get_db_config()
    print(f"\n📡 连接数据库: {db_config['host']}:{db_config['port']}/{db_config['database']}")
    
    try:
        # 连接数据库
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        # SQL文件列表（按顺序执行）
        migration_dir = Path(__file__).parent
        sql_files = [
            '001_create_workflow_tables.sql',
            '002_insert_workflow_menu.sql',
            '003_insert_workflow_templates.sql',
        ]
        
        all_success = True
        for sql_file in sql_files:
            filepath = migration_dir / sql_file
            if filepath.exists():
                success = execute_sql_file(cursor, filepath)
                if not success:
                    all_success = False
            else:
                print(f"\n⚠️ 文件不存在: {sql_file}")
        
        # 提交事务
        conn.commit()
        
        if all_success:
            print("\n" + "=" * 60)
            print("✅ 工作流模块数据库迁移完成!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("⚠️ 迁移完成，但有部分错误，请检查日志")
            print("=" * 60)
        
        # 显示创建的表
        cursor.execute("SHOW TABLES LIKE 't_workflow%'")
        tables = cursor.fetchall()
        print("\n📋 已创建的工作流相关表:")
        for table in tables:
            print(f"   - {table[0]}")
        
        cursor.close()
        conn.close()
        
    except pymysql.Error as e:
        print(f"\n❌ 数据库连接失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
