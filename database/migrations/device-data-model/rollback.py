#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库回滚脚本 (Python版本)

用途: 完全回滚设备数据模型相关的所有更改
使用方法:
    python rollback.py

警告: 此脚本将删除所有设备数据模型相关的表和数据！
请在执行前务必备份数据库！
"""

import sys
import psycopg2
from pathlib import Path
from datetime import datetime

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

def print_header(text, char='='):
    """打印带框的标题"""
    width = 60
    print()
    print(char * width)
    print(f"  {text}")
    print(char * width)
    print()

def main():
    """主函数"""
    print_header("设备数据模型 - 数据库回滚")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("警告: 此操作将删除以下内容:")
    print("  - t_model_execution_log 表")
    print("  - t_device_data_model 表")
    print("  - t_device_field_mapping 表")
    print("  - t_device_field 表的6个新增列")
    print("  - 所有相关的索引、触发器和函数")
    print()
    
    # 连接数据库
    print("连接数据库...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor()
        print(f"  数据库连接成功 ({DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']})")
    except Exception as e:
        print(f"\n数据库连接失败: {e}")
        return 1
    
    try:
        # 步骤 1: 删除新建的表
        print_header("步骤 1/3: 删除新建的表")
        
        tables = [
            't_model_execution_log',
            't_device_data_model',
            't_device_field_mapping'
        ]
        
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            print(f"  [删除表] {table}")
        
        conn.commit()
        
        # 步骤 2: 删除触发器和函数
        print_header("步骤 2/3: 删除触发器和函数")
        
        cursor.execute("DROP TRIGGER IF EXISTS trigger_update_data_model_timestamp ON t_device_data_model")
        print("  [删除触发器] trigger_update_data_model_timestamp")
        
        cursor.execute("DROP TRIGGER IF EXISTS trigger_update_field_mapping_timestamp ON t_device_field_mapping")
        print("  [删除触发器] trigger_update_field_mapping_timestamp")
        
        cursor.execute("DROP FUNCTION IF EXISTS update_data_model_timestamp()")
        print("  [删除函数] update_data_model_timestamp()")
        
        cursor.execute("DROP FUNCTION IF EXISTS update_field_mapping_timestamp()")
        print("  [删除函数] update_field_mapping_timestamp()")
        
        conn.commit()
        
        # 步骤 3: 删除 t_device_field 表的新增列
        print_header("步骤 3/3: 删除 t_device_field 表的新增列")
        
        # 删除索引
        indexes = [
            'idx_device_field_monitoring',
            'idx_device_field_ai'
        ]
        
        for index in indexes:
            cursor.execute(f"DROP INDEX IF EXISTS {index}")
            print(f"  [删除索引] {index}")
        
        # 删除列
        columns = [
            'display_config',
            'alarm_threshold',
            'data_range',
            'aggregation_method',
            'is_ai_feature',
            'is_monitoring_key'
        ]
        
        for column in columns:
            cursor.execute(f"ALTER TABLE t_device_field DROP COLUMN IF EXISTS {column}")
            print(f"  [删除列] t_device_field.{column}")
        
        conn.commit()
        
        # 完成信息
        print_header("回滚已成功完成！")
        print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("已删除:")
        print("  - 3张新表")
        print("  - 6个新列")
        print("  - 所有触发器和函数")
        print("  - 所有相关索引")
        print()
        print("现有表和数据未受影响:")
        print("  - t_device_type")
        print("  - t_device_info")
        print("  - t_device_field (原有列)")
        print()
        print("可以重新执行迁移:")
        print("  python execute_migration.py")
        print()
        
        return 0
        
    except Exception as e:
        conn.rollback()
        print(f"\n回滚失败: {e}")
        print("\n所有更改已回滚。")
        return 1
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    sys.exit(main())

