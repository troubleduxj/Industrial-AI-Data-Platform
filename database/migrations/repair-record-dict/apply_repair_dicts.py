#!/usr/bin/env python3
"""
维修记录字典数据应用脚本

执行方式：
    python apply_repair_dicts.py

功能：
    - 创建维修记录相关的数据字典
    - 包含：设备类别、设备品牌、故障原因、损坏类别
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# 加载环境变量
env_path = project_root / "app" / ".env.dev"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv(project_root / ".env")


def get_db_connection():
    """获取数据库连接"""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        database=os.getenv("POSTGRES_DB", "devicemonitor"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres")
    )


def execute_sql_file(sql_file_path: str) -> bool:
    """执行SQL文件"""
    print(f"\n{'='*60}")
    print(f"执行SQL文件: {sql_file_path}")
    print(f"{'='*60}")
    
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        conn = get_db_connection()
        conn.autocommit = False
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql_content)
            conn.commit()
            print("✅ SQL执行成功！")
            
            # 验证结果
            verify_results(cursor)
            
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"❌ SQL执行失败: {e}")
            return False
            
        finally:
            cursor.close()
            conn.close()
            
    except FileNotFoundError:
        print(f"❌ SQL文件不存在: {sql_file_path}")
        return False
    except Exception as e:
        print(f"❌ 执行出错: {e}")
        return False


def verify_results(cursor):
    """验证字典数据创建结果"""
    print("\n📊 验证创建结果:")
    print("-" * 40)
    
    dict_types = [
        ('repair_device_category', '维修设备类别'),
        ('device_brand', '设备品牌'),
        ('repair_fault_reason', '故障原因'),
        ('repair_damage_category', '损坏类别')
    ]
    
    for type_code, type_name in dict_types:
        cursor.execute("""
            SELECT COUNT(dd.id)
            FROM t_sys_dict_type dt
            LEFT JOIN t_sys_dict_data dd ON dt.id = dd.dict_type_id
            WHERE dt.type_code = %s
        """, (type_code,))
        
        count = cursor.fetchone()[0]
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {type_name}: {count} 条数据")


def show_dict_data():
    """显示所有字典数据"""
    print("\n📋 字典数据详情:")
    print("=" * 60)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        dict_types = [
            'repair_device_category',
            'device_brand', 
            'repair_fault_reason',
            'repair_damage_category'
        ]
        
        for type_code in dict_types:
            cursor.execute("""
                SELECT dt.type_name, dd.data_label, dd.data_value, dd.sort_order
                FROM t_sys_dict_type dt
                JOIN t_sys_dict_data dd ON dt.id = dd.dict_type_id
                WHERE dt.type_code = %s AND dd.is_enabled = true
                ORDER BY dd.sort_order
            """, (type_code,))
            
            rows = cursor.fetchall()
            if rows:
                print(f"\n【{rows[0][0]}】")
                for row in rows:
                    print(f"  - {row[1]} ({row[2]})")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")


def main():
    print("=" * 60)
    print("  维修记录字典数据应用脚本")
    print("=" * 60)
    
    # 获取SQL文件路径
    script_dir = Path(__file__).parent
    sql_file = script_dir / "001_create_repair_dicts.sql"
    
    if execute_sql_file(str(sql_file)):
        show_dict_data()
        print("\n" + "=" * 60)
        print("✅ 维修记录字典数据创建完成！")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ 字典数据创建失败，请检查错误信息")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
