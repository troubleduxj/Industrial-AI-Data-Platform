"""
应用设备字段数据字典配置
"""
import psycopg2
import sys
from pathlib import Path

# 数据库配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'devicemonitor',
    'user': 'postgres',
    'password': 'Hanatech@123'
}

def execute_sql_file(filepath: str):
    """执行SQL文件"""
    try:
        print(f"📄 读取SQL文件: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print("🔌 连接数据库...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor()
        
        print("📝 执行SQL脚本...")
        cursor.execute(sql_content)
        
        # 获取所有结果
        try:
            while True:
                if cursor.description:
                    results = cursor.fetchall()
                    if results:
                        print("\n📊 执行结果:")
                        for row in results:
                            print(f"  {row}")
                if not cursor.nextset():
                    break
        except Exception:
            pass
        
        conn.commit()
        print("\n✅ SQL脚本执行成功！")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ 数据库错误: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False
    except FileNotFoundError:
        print(f"\n❌ 文件不存在: {filepath}")
        return False
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def main():
    print("=" * 70)
    print("  设备字段数据字典配置")
    print("=" * 70)
    
    # 获取当前脚本所在目录
    script_dir = Path(__file__).parent
    sql_file = script_dir / "001_create_field_dicts.sql"
    
    if execute_sql_file(str(sql_file)):
        print("\n" + "=" * 70)
        print("  ✅ 数据字典配置完成！")
        print("=" * 70)
        print("\n📋 后续步骤:")
        print("  1. 重启后端服务（如果正在运行）")
        print("  2. 修改前端代码加载数据字典")
        print("  3. 重启前端服务")
        print("  4. 清除浏览器缓存")
        print("  5. 测试字段分组和分类功能")
        print("\n💡 管理数据字典:")
        print("  访问: 系统管理 → 数据字典")
        print("  可以添加、修改、删除字段分组和分类")
        return 0
    else:
        print("\n" + "=" * 70)
        print("  ❌ 数据字典配置失败！")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
