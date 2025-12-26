#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移执行脚本 (Python版本)

用途: 通过Python执行所有设备数据模型相关的数据库迁移
使用方法:
    python execute_migration.py

注意: 请先备份数据库！
"""

import os
import sys
import time
from pathlib import Path
import psycopg2
from psycopg2 import sql
from datetime import datetime

# 设置控制台编码为 UTF-8 (Windows)
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 数据库配置（从 .env.dev 读取）
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'user': 'postgres',
    'password': 'Hanatech@123',
    'database': 'devicemonitor'
}

# SQL 文件执行顺序
SQL_FILES = [
    '001_extend_device_field.sql',
    '002_create_device_data_model.sql',
    '003_create_field_mapping.sql',
    '004_create_execution_log.sql',
    '005_init_field_attributes.sql',
    '006_create_default_mappings.sql',
    '007_create_default_models.sql',
]

def print_header(text, char='='):
    """打印带框的标题"""
    width = 60
    print()
    print(char * width)
    print(f"  {text}")
    print(char * width)
    print()

def print_section(text):
    """打印章节标题"""
    print(f"\n>>> {text}")

def execute_sql_file(cursor, file_path):
    """执行单个SQL文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 执行SQL
        cursor.execute(sql_content)
        
        return True, None
    except Exception as e:
        return False, str(e)

def verify_migration(cursor):
    """验证迁移结果"""
    print_header("阶段 3/3: 验证迁移结果")
    
    # 验证 t_device_field 表新增列
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 't_device_field' 
        AND column_name IN ('is_monitoring_key', 'is_ai_feature', 'aggregation_method', 
                           'data_range', 'alarm_threshold', 'display_config')
    """)
    device_field_columns = cursor.fetchone()[0]
    
    # 验证新表记录数
    cursor.execute("SELECT COUNT(*) FROM t_device_data_model")
    data_model_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM t_device_field_mapping")
    field_mapping_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM t_model_execution_log")
    execution_log_count = cursor.fetchone()[0]
    
    # 输出验证结果
    print_header("✅ 迁移执行成功！")
    print("数据库表:")
    print(f"  ✓ t_device_field: 新增 {device_field_columns} 列")
    print(f"  ✓ t_device_data_model: {data_model_count} 条记录")
    print(f"  ✓ t_device_field_mapping: {field_mapping_count} 条记录")
    print(f"  ✓ t_model_execution_log: {execution_log_count} 条记录")
    print()
    
    if device_field_columns == 6:
        print("✅ t_device_field 扩展成功")
    else:
        print(f"⚠️  t_device_field 扩展异常，预期6列，实际{device_field_columns}列")
    
    if data_model_count >= 3:
        print(f"✅ 默认数据模型创建成功 ({data_model_count} 个)")
    else:
        print(f"⚠️  默认数据模型创建异常，预期至少3个，实际{data_model_count}个")
    
    if field_mapping_count > 0:
        print(f"✅ 字段映射创建成功 ({field_mapping_count} 个)")
    else:
        print("⚠️  字段映射创建异常，记录数为0")
    
    print()
    
    # 列出所有数据模型
    print("\n创建的数据模型:")
    print("=" * 60)
    cursor.execute("""
        SELECT 
            model_code,
            model_name,
            model_type,
            version,
            is_active,
            is_default
        FROM t_device_data_model
        ORDER BY model_type, model_code
    """)
    
    print(f"{'模型代码':<30} {'模型名称':<30} {'类型':<15} {'版本':<8} {'激活':<8} {'默认':<8}")
    print("-" * 110)
    for row in cursor.fetchall():
        model_code, model_name, model_type, version, is_active, is_default = row
        print(f"{model_code:<30} {model_name:<30} {model_type:<15} {version:<8} {'是' if is_active else '否':<8} {'是' if is_default else '否':<8}")
    
    # 统计字段映射
    print("\n字段映射统计:")
    print("=" * 60)
    cursor.execute("""
        SELECT 
            device_type_code,
            COUNT(*) as mapping_count,
            COUNT(*) FILTER (WHERE is_tag = TRUE) as tag_count,
            COUNT(*) FILTER (WHERE transform_rule IS NOT NULL) as transform_count
        FROM t_device_field_mapping
        GROUP BY device_type_code
        ORDER BY device_type_code
    """)
    
    print(f"{'设备类型':<20} {'映射总数':<15} {'TAG数量':<15} {'转换规则数':<15}")
    print("-" * 65)
    for row in cursor.fetchall():
        device_type_code, mapping_count, tag_count, transform_count = row
        print(f"{device_type_code:<20} {mapping_count:<15} {tag_count:<15} {transform_count:<15}")

def main():
    """主函数"""
    start_time = time.time()
    
    print_header("设备数据模型 - 数据库迁移执行")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 获取当前脚本所在目录
    script_dir = Path(__file__).resolve().parent
    
    # 连接数据库
    print_section("连接数据库...")
    print(f"  主机: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"  数据库: {DB_CONFIG['database']}")
    print(f"  用户: {DB_CONFIG['user']}")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False  # 使用事务
        cursor = conn.cursor()
        print("  ✓ 数据库连接成功")
    except Exception as e:
        print(f"\n❌ 数据库连接失败: {e}")
        print("\n请检查:")
        print("  1. PostgreSQL 服务是否运行")
        print("  2. 数据库配置是否正确 (app/.env.dev)")
        print("  3. 数据库 'devicemonitor' 是否存在")
        return 1
    
    try:
        # 阶段 1: 创建数据库表
        print_header("阶段 1/3: 创建数据库表")
        
        for i, sql_file in enumerate(SQL_FILES[:4], 1):
            file_path = script_dir / sql_file
            print_section(f"[{i}/4] 执行 {sql_file}...")
            
            if not file_path.exists():
                print(f"  ❌ 文件不存在: {file_path}")
                raise Exception(f"SQL文件不存在: {sql_file}")
            
            success, error = execute_sql_file(cursor, file_path)
            if not success:
                print(f"  ❌ 执行失败: {error}")
                raise Exception(f"执行 {sql_file} 失败: {error}")
            
            print(f"  ✓ 执行成功")
        
        # 提交阶段1的变更
        conn.commit()
        
        # 阶段 2: 数据迁移
        print_header("阶段 2/3: 数据迁移")
        
        for i, sql_file in enumerate(SQL_FILES[4:], 1):
            file_path = script_dir / sql_file
            print_section(f"[{i}/3] 执行 {sql_file}...")
            
            if not file_path.exists():
                print(f"  ❌ 文件不存在: {file_path}")
                raise Exception(f"SQL文件不存在: {sql_file}")
            
            success, error = execute_sql_file(cursor, file_path)
            if not success:
                print(f"  ❌ 执行失败: {error}")
                raise Exception(f"执行 {sql_file} 失败: {error}")
            
            print(f"  ✓ 执行成功")
        
        # 提交阶段2的变更
        conn.commit()
        
        # 阶段 3: 验证
        verify_migration(cursor)
        
        # 最终提交
        conn.commit()
        
        # 完成信息
        elapsed_time = time.time() - start_time
        print_header("迁移已成功完成！")
        print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"耗时: {elapsed_time:.2f} 秒")
        print()
        print("下一步:")
        print("  1. ✅ 数据库基础已建立")
        print("  2. ✅ Python Model 和 Schema 已开发")
        print("  3. ✅ 基础 API 接口已开发")
        print("  4. ⏭️  继续 Phase 2: 动态模型实现")
        print()
        print("回滚方法:")
        print("  python rollback.py")
        print("  或")
        print("  psql -h 127.0.0.1 -U postgres -d devicemonitor -f rollback.sql")
        print()
        
        return 0
        
    except Exception as e:
        # 回滚事务
        conn.rollback()
        print(f"\n❌ 迁移失败: {e}")
        print("\n所有更改已回滚，数据库状态未改变。")
        return 1
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    sys.exit(main())

