#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复设备字段配置管理的权限
确保超级管理员拥有所有必要的权限
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tortoise import Tortoise
from app.settings.config import settings


async def fix_permissions():
    """修复权限配置"""
    try:
        # 初始化数据库连接
        await Tortoise.init(
            db_url=settings.DATABASE_URL,
            modules={'models': ['app.models.admin', 'app.models.system', 'app.models.device']}
        )
        
        print("=" * 60)
        print("开始修复设备字段配置管理权限...")
        print("=" * 60)
        
        # 读取并执行 SQL 脚本
        sql_file = Path(__file__).parent / 'fix_admin_permissions.sql'
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 获取数据库连接
        conn = Tortoise.get_connection("default")
        
        # 执行 SQL（分段执行，因为包含多个语句）
        sql_statements = sql_content.split(';')
        for statement in sql_statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    await conn.execute_query(statement)
                except Exception as e:
                    # 忽略一些预期的错误（如已存在的记录）
                    if 'duplicate' not in str(e).lower() and 'already exists' not in str(e).lower():
                        print(f"警告: {e}")
        
        print("\n✅ 权限修复完成！")
        print("\n请执行以下操作：")
        print("1. 重新登录系统")
        print("2. 访问 系统管理 -> 设备字段配置")
        print("3. 验证新增、编辑、删除按钮是否可见")
        
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(fix_permissions())
