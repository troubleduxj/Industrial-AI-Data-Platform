#!/usr/bin/env python3
"""
报警规则系统 - 数据库迁移脚本

执行方式：
    python apply_alarm_rules.py

功能：
    1. 创建报警规则表和报警记录表
    2. 插入示例报警规则
    3. 添加报警规则菜单
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import psycopg2
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
    print(f"\n执行: {sql_file_path}")
    
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        conn = get_db_connection()
        conn.autocommit = True
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql_content)
            print(f"  ✅ 执行成功")
            return True
        except Exception as e:
            print(f"  ❌ 执行失败: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
            
    except FileNotFoundError:
        print(f"  ❌ 文件不存在: {sql_file_path}")
        return False
    except Exception as e:
        print(f"  ❌ 执行出错: {e}")
        return False


def verify_tables():
    """验证表是否创建成功"""
    print("\n📊 验证表创建:")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查报警规则表
        cursor.execute("SELECT COUNT(*) FROM t_alarm_rule")
        rule_count = cursor.fetchone()[0]
        print(f"  ✅ t_alarm_rule: {rule_count} 条规则")
        
        # 检查报警记录表
        cursor.execute("SELECT COUNT(*) FROM t_alarm_record")
        record_count = cursor.fetchone()[0]
        print(f"  ✅ t_alarm_record: {record_count} 条记录")
        
        # 检查菜单
        cursor.execute("SELECT COUNT(*) FROM t_sys_menu WHERE name = '报警规则'")
        menu_count = cursor.fetchone()[0]
        print(f"  ✅ 报警规则菜单: {'已创建' if menu_count > 0 else '未创建'}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ 验证失败: {e}")
        return False


def main():
    print("=" * 60)
    print("  报警规则系统 - 数据库迁移")
    print("=" * 60)
    
    script_dir = Path(__file__).parent
    
    # 执行SQL文件
    sql_files = [
        "001_create_alarm_tables.sql",
        "002_add_alarm_rules_menu.sql",
    ]
    
    success = True
    for sql_file in sql_files:
        sql_path = script_dir / sql_file
        if sql_path.exists():
            if not execute_sql_file(str(sql_path)):
                success = False
        else:
            print(f"  ⚠ 跳过不存在的文件: {sql_file}")
    
    # 验证
    verify_tables()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 报警规则系统数据库迁移完成！")
        print("\n下一步:")
        print("  1. 重启后端服务")
        print("  2. 刷新前端页面")
        print("  3. 访问 报警管理 > 报警规则 页面")
    else:
        print("❌ 部分迁移失败，请检查错误信息")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
