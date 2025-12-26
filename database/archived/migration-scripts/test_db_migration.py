#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移测试脚本
用于测试设备元数据表的创建和功能

使用方法:
    python test_db_migration.py

功能:
    1. 测试数据库连接
    2. 验证表结构
    3. 测试数据插入和查询
    4. 验证存储过程和视图
"""

import os
import sys
import psycopg2
from pathlib import Path
import json
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.settings.config import settings

def get_db_connection():
    """获取数据库连接"""
    try:
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            database=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

def test_database_connection():
    """测试数据库连接"""
    print("1. 测试数据库连接...")
    
    conn = get_db_connection()
    if not conn:
        print("✗ 数据库连接失败")
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✓ 数据库连接成功")
        print(f"  PostgreSQL版本: {version.split(',')[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ 数据库查询失败: {e}")
        return False

def test_table_structure():
    """测试表结构"""
    print("\n2. 测试表结构...")
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # 检查核心表是否存在
        tables = ['t_device_type', 't_device_info', 't_device_field']
        
        for table in tables:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (table,))
            
            exists = cursor.fetchone()[0]
            if exists:
                print(f"✓ 表 {table} 存在")
                
                # 获取表的列信息
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = %s
                    ORDER BY ordinal_position;
                """, (table,))
                
                columns = cursor.fetchall()
                print(f"  列数: {len(columns)}")
                for col in columns[:3]:  # 只显示前3列
                    print(f"    - {col[0]} ({col[1]})")
                if len(columns) > 3:
                    print(f"    ... 还有{len(columns)-3}列")
            else:
                print(f"✗ 表 {table} 不存在")
                return False
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ 表结构检查失败: {e}")
        return False

def test_initial_data():
    """测试初始数据"""
    print("\n3. 测试初始数据...")
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # 检查设备类型数据
        cursor.execute("SELECT COUNT(*) FROM t_device_type;")
        type_count = cursor.fetchone()[0]
        print(f"✓ 设备类型数量: {type_count}")
        
        if type_count > 0:
            cursor.execute("""
                SELECT type_name, type_code, tdengine_stable_name 
                FROM t_device_type 
                ORDER BY created_at;
            """)
            types = cursor.fetchall()
            for t in types:
                print(f"  - {t[0]} ({t[1]}) -> {t[2]}")
        
        # 检查字段定义数据
        cursor.execute("SELECT COUNT(*) FROM t_device_field;")
        field_count = cursor.fetchone()[0]
        print(f"✓ 字段定义数量: {field_count}")
        
        if field_count > 0:
            cursor.execute("""
                SELECT dt.type_name, COUNT(df.id) as field_count
                FROM t_device_type dt
                LEFT JOIN t_device_field df ON dt.id = df.device_type_id
                GROUP BY dt.id, dt.type_name;
            """)
            field_stats = cursor.fetchall()
            for stat in field_stats:
                print(f"  - {stat[0]}: {stat[1]}个字段")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ 初始数据检查失败: {e}")
        return False

def test_stored_procedures():
    """测试存储过程"""
    print("\n4. 测试存储过程...")
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # 测试获取设备类型字段函数
        cursor.execute("SELECT get_device_type_fields('welding');")
        fields = cursor.fetchall()
        
        if fields:
            print(f"✓ get_device_type_fields函数正常，返回{len(fields)}个字段")
            for field in fields[:3]:  # 显示前3个字段
                field_info = field[0]  # 函数返回的是复合类型
                print(f"  - {field_info}")
        else:
            print("✗ get_device_type_fields函数返回空结果")
        
        # 测试获取TDengine表名函数
        cursor.execute("SELECT get_tdengine_stable_name('welding');")
        stable_name = cursor.fetchone()[0]
        
        if stable_name:
            print(f"✓ get_tdengine_stable_name函数正常，返回: {stable_name}")
        else:
            print("✗ get_tdengine_stable_name函数返回空结果")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ 存储过程测试失败: {e}")
        return False

def test_views():
    """测试视图"""
    print("\n5. 测试视图...")
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # 测试设备类型详情视图
        cursor.execute("SELECT COUNT(*) FROM v_device_type_detail;")
        view_count = cursor.fetchone()[0]
        print(f"✓ v_device_type_detail视图正常，{view_count}条记录")
        
        if view_count > 0:
            cursor.execute("""
                SELECT type_name, device_count, field_count 
                FROM v_device_type_detail 
                LIMIT 3;
            """)
            details = cursor.fetchall()
            for detail in details:
                print(f"  - {detail[0]}: {detail[1]}个设备, {detail[2]}个字段")
        
        # 测试设备完整信息视图（可能为空）
        cursor.execute("SELECT COUNT(*) FROM v_device_full_info;")
        device_count = cursor.fetchone()[0]
        print(f"✓ v_device_full_info视图正常，{device_count}条记录")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ 视图测试失败: {e}")
        return False

def test_data_operations():
    """测试数据操作"""
    print("\n6. 测试数据操作...")
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # 测试插入设备信息
        test_device_id = f"TEST_DEVICE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 获取焊接设备类型ID
        cursor.execute("SELECT id FROM t_device_type WHERE type_code = 'welding';")
        welding_type_id = cursor.fetchone()[0]
        
        # 插入测试设备
        cursor.execute("""
            INSERT INTO t_device_info (device_id, device_name, device_type_id, location, metadata)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            test_device_id,
            "测试焊接设备",
            welding_type_id,
            "测试车间",
            json.dumps({"test": True, "created_by": "migration_test"})
        ))
        
        device_info_id = cursor.fetchone()[0]
        print(f"✓ 测试设备插入成功，ID: {device_info_id}")
        
        # 查询测试设备
        cursor.execute("""
            SELECT device_id, device_name, type_name, location
            FROM v_device_full_info
            WHERE device_id = %s;
        """, (test_device_id,))
        
        device_info = cursor.fetchone()
        if device_info:
            print(f"✓ 测试设备查询成功: {device_info[1]} ({device_info[2]})")
        
        # 清理测试数据
        cursor.execute("DELETE FROM t_device_info WHERE id = %s;", (device_info_id,))
        print("✓ 测试数据清理完成")
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ 数据操作测试失败: {e}")
        if conn:
            conn.rollback()
        return False

def main():
    """主函数"""
    print("设备元数据表迁移测试")
    print("="*50)
    
    tests = [
        test_database_connection,
        test_table_structure,
        test_initial_data,
        test_stored_procedures,
        test_views,
        test_data_operations
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print(f"\n测试失败，停止后续测试")
            break
    
    print("\n" + "="*50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有测试通过，数据库迁移成功！")
        return True
    else:
        print("✗ 部分测试失败，请检查数据库配置和迁移脚本")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)