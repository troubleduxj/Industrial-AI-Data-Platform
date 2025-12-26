#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用设备监测字段配置
执行 SQL 迁移脚本，配置焊机和压力传感器的监测字段
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tortoise import Tortoise
from app.settings.config import settings


async def apply_monitoring_fields():
    """应用监测字段配置"""
    print("=" * 60)
    print("  应用设备监测字段配置")
    print("=" * 60)
    
    try:
        # 初始化数据库连接
        print("\n📦 正在连接数据库...")
        # 构建 Tortoise ORM 兼容的数据库 URL (使用 postgres:// 而不是 postgresql://)
        creds = settings.tortoise_orm.connections.postgres.credentials
        db_url = f"postgres://{creds.user}:{creds.password}@{creds.host}:{creds.port}/{creds.database}"
        print(f"📍 数据库: {creds.database} @ {creds.host}:{creds.port}")
        await Tortoise.init(
            db_url=db_url,
            modules={"models": ["app.models.device", "app.models.admin", "app.models.system"]}
        )
        print("✅ 数据库连接成功")
        
        # 获取数据库连接
        conn = Tortoise.get_connection("default")
        
        # 读取 SQL 文件
        sql_file = Path(__file__).parent / "001_configure_monitoring_fields.sql"
        print(f"\n📄 正在读取 SQL 文件: {sql_file}")
        
        if not sql_file.exists():
            print(f"❌ SQL 文件不存在: {sql_file}")
            return False
        
        sql_content = sql_file.read_text(encoding='utf-8')
        print("✅ SQL 文件读取成功")
        
        # 分割 SQL 语句（按分号分割，但跳过注释）
        print("\n🔧 正在执行 SQL 语句...")
        statements = []
        current_statement = []
        
        for line in sql_content.split('\n'):
            # 跳过注释行
            if line.strip().startswith('--'):
                continue
            
            current_statement.append(line)
            
            # 如果行以分号结尾，表示一个语句结束
            if line.strip().endswith(';'):
                statement = '\n'.join(current_statement).strip()
                if statement and not statement.startswith('--'):
                    statements.append(statement)
                current_statement = []
        
        # 执行每个 SQL 语句
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(statements, 1):
            try:
                # 跳过 SELECT 查询（验证语句）
                if statement.strip().upper().startswith('SELECT'):
                    print(f"  ⏭️  跳过查询语句 {i}/{len(statements)}")
                    continue
                
                await conn.execute_query(statement)
                success_count += 1
                print(f"  ✅ 执行成功 {i}/{len(statements)}")
            except Exception as e:
                error_count += 1
                print(f"  ⚠️  执行失败 {i}/{len(statements)}: {str(e)}")
        
        print(f"\n📊 执行统计:")
        print(f"  - 总语句数: {len(statements)}")
        print(f"  - 成功: {success_count}")
        print(f"  - 失败: {error_count}")
        
        # 验证配置结果
        print("\n🔍 验证配置结果...")
        
        # 查询焊机的监测字段
        welding_fields = await conn.execute_query_dict("""
            SELECT 
                device_type_code,
                field_name,
                field_code,
                field_type,
                unit,
                sort_order,
                is_monitoring_key
            FROM t_device_field
            WHERE device_type_code = 'welding' 
              AND is_monitoring_key = true
              AND is_active = true
            ORDER BY sort_order
        """)
        
        print(f"\n✅ 焊机监测字段配置 (共 {len(welding_fields)} 个):")
        for field in welding_fields:
            print(f"  - {field['field_name']} ({field['field_code']}): {field['field_type']} {field['unit'] or ''}")
        
        # 查询压力传感器的监测字段
        pressure_fields = await conn.execute_query_dict("""
            SELECT 
                device_type_code,
                field_name,
                field_code,
                field_type,
                unit,
                sort_order,
                is_monitoring_key
            FROM t_device_field
            WHERE device_type_code = 'PRESSURE_SENSOR_V1' 
              AND is_monitoring_key = true
              AND is_active = true
            ORDER BY sort_order
        """)
        
        print(f"\n✅ 压力传感器监测字段配置 (共 {len(pressure_fields)} 个):")
        for field in pressure_fields:
            print(f"  - {field['field_name']} ({field['field_code']}): {field['field_type']} {field['unit'] or ''}")
        
        print("\n" + "=" * 60)
        print("  ✅ 配置完成！")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 配置失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 关闭数据库连接
        await Tortoise.close_connections()
        print("\n📦 数据库连接已关闭")


async def main():
    """主函数"""
    success = await apply_monitoring_fields()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
