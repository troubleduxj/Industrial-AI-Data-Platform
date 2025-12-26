#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备元数据表迁移脚本
用于创建支持多设备类型的PostgreSQL表结构

使用方法:
    python migrate_device_metadata.py

功能:
    1. 创建设备类型、设备信息、设备字段三个核心表
    2. 创建相关索引和触发器
    3. 插入初始数据（焊接设备类型）
    4. 创建查询视图和存储过程
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.settings.config import settings

def get_db_connection():
    """获取数据库连接"""
    try:
        postgres_creds = settings.tortoise_orm.connections.postgres.credentials
        conn = psycopg2.connect(
            host=postgres_creds.host,
            port=postgres_creds.port,
            database=postgres_creds.database,
            user=postgres_creds.user,
            password=postgres_creds.password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

def execute_sql_file(conn, sql_file_path):
    """执行SQL文件"""
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        cursor = conn.cursor()
        
        # 智能分割SQL语句，处理存储过程中的$$
        sql_statements = []
        current_statement = ""
        in_function = False
        
        for line in sql_content.split('\n'):
            line = line.strip()
            if not line or line.startswith('--'):
                continue
                
            current_statement += line + '\n'
            
            # 检测函数开始和结束
            if '$$' in line:
                in_function = not in_function
            
            # 如果不在函数内且遇到分号，则结束当前语句
            if not in_function and line.endswith(';'):
                if current_statement.strip():
                    sql_statements.append(current_statement.strip())
                current_statement = ""
        
        # 添加最后一个语句（如果有）
        if current_statement.strip():
            sql_statements.append(current_statement.strip())
        
        for i, statement in enumerate(sql_statements):
            try:
                print(f"执行SQL语句 {i+1}/{len(sql_statements)}...")
                cursor.execute(statement)
                print(f"✓ 语句 {i+1} 执行成功")
            except Exception as e:
                print(f"✗ 语句 {i+1} 执行失败: {e}")
                print(f"失败的SQL: {statement[:100]}...")
                # 继续执行其他语句，不中断整个过程
                continue
        
        cursor.close()
        print("\n所有SQL语句执行完成")
        return True
        
    except Exception as e:
        print(f"执行SQL文件失败: {e}")
        return False

def check_tables_exist(conn):
    """检查表是否创建成功"""
    try:
        cursor = conn.cursor()
        
        # 检查核心表
        tables_to_check = ['t_device_type', 't_device_info', 't_device_field']
        
        for table in tables_to_check:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (table,))
            
            exists = cursor.fetchone()[0]
            if exists:
                print(f"✓ 表 {table} 创建成功")
            else:
                print(f"✗ 表 {table} 创建失败")
        
        # 检查初始数据
        cursor.execute("SELECT COUNT(*) FROM t_device_type WHERE type_code = 'welding';")
        welding_count = cursor.fetchone()[0]
        
        if welding_count > 0:
            print(f"✓ 焊接设备类型数据插入成功 (共{welding_count}条记录)")
        else:
            print("✗ 焊接设备类型数据插入失败")
        
        # 检查字段定义
        cursor.execute("""
            SELECT COUNT(*) FROM t_device_field df
            JOIN t_device_type dt ON df.device_type_code = dt.type_code
            WHERE dt.type_code = 'welding';
        """)
        field_count = cursor.fetchone()[0]
        
        if field_count > 0:
            print(f"✓ 焊接设备字段定义插入成功 (共{field_count}个字段)")
        else:
            print("✗ 焊接设备字段定义插入失败")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"检查表结构失败: {e}")
        return False

def show_migration_summary(conn):
    """显示迁移结果摘要"""
    try:
        cursor = conn.cursor()
        
        print("\n" + "="*50)
        print("数据库迁移结果摘要")
        print("="*50)
        
        # 显示设备类型信息
        cursor.execute("""
            SELECT type_name, type_code, tdengine_stable_name, 
                   (SELECT COUNT(*) FROM t_device_field WHERE device_type_code = t_device_type.type_code) as field_count
            FROM t_device_type;
        """)
        
        device_types = cursor.fetchall()
        print(f"\n设备类型 ({len(device_types)}个):")
        for dt in device_types:
            print(f"  - {dt[0]} ({dt[1]}) -> {dt[2]} [{dt[3]}个字段]")
        
        # 显示字段定义
        cursor.execute("""
            SELECT dt.type_name, df.field_name, df.field_type, df.is_tag
            FROM t_device_field df
            JOIN t_device_type dt ON df.device_type_code = dt.type_code
            ORDER BY dt.type_name, df.sort_order;
        """)
        
        fields = cursor.fetchall()
        current_type = None
        for field in fields:
            if field[0] != current_type:
                current_type = field[0]
                print(f"\n{current_type}字段定义:")
            tag_marker = "[TAG]" if field[3] else ""
            print(f"  - {field[1]} ({field[2]}) {tag_marker}")
        
        cursor.close()
        
    except Exception as e:
        print(f"显示摘要失败: {e}")

def main():
    """主函数"""
    print("开始执行设备元数据表迁移...")
    print("="*50)
    
    # 获取数据库连接
    conn = get_db_connection()
    if not conn:
        print("无法连接到数据库，迁移终止")
        return False
    
    try:
        # 执行SQL文件
        sql_file_path = Path(__file__).parent / "device_metadata_schema.sql"
        
        if not sql_file_path.exists():
            print(f"SQL文件不存在: {sql_file_path}")
            return False
        
        print(f"执行SQL文件: {sql_file_path}")
        if not execute_sql_file(conn, sql_file_path):
            print("SQL文件执行失败")
            return False
        
        # 检查表创建结果
        print("\n检查表创建结果...")
        if not check_tables_exist(conn):
            print("表创建检查失败")
            return False
        
        # 显示迁移摘要
        show_migration_summary(conn)
        
        print("\n" + "="*50)
        print("✓ 设备元数据表迁移完成！")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"迁移过程中发生错误: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)