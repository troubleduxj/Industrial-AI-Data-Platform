#!/usr/bin/env python3
"""
应用通知管理路由修复
修复菜单的 component 字段格式
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from tortoise import Tortoise
from app.settings import settings


async def apply_fix():
    """应用路由修复"""
    print("=" * 60)
    print("通知管理路由修复脚本")
    print("=" * 60)
    
    # 修复数据库URL格式
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgres://", 1)
    
    # 连接数据库
    await Tortoise.init(
        db_url=db_url,
        modules={"models": ["app.models.admin"]}
    )
    
    conn = Tortoise.get_connection("default")
    
    try:
        # 查看当前配置
        print("\n📋 当前通知管理菜单配置:")
        result = await conn.execute_query(
            "SELECT id, name, path, component, menu_type FROM t_sys_menu WHERE id BETWEEN 200 AND 210"
        )
        for row in result[1]:
            print(f"  ID={row['id']}, name={row['name']}, path={row['path']}, component={row['component']}, type={row['menu_type']}")
        
        # 修复 component 字段（移除前导斜杠）
        print("\n🔧 修复 component 字段...")
        
        fixes = [
            (201, 'notification/list'),
            (202, 'notification/email-server'),
            (203, 'notification/email-template'),
            (204, 'notification/send-config'),
        ]
        
        for menu_id, component in fixes:
            await conn.execute_query(
                f"UPDATE t_sys_menu SET component = '{component}' WHERE id = {menu_id}"
            )
            print(f"  ✅ 更新菜单 ID={menu_id} component='{component}'")
        
        # 确保一级菜单的 component 为 Layout
        await conn.execute_query(
            "UPDATE t_sys_menu SET component = 'Layout' WHERE id = 200"
        )
        print("  ✅ 更新菜单 ID=200 component='Layout'")
        
        # 验证修复结果
        print("\n📋 修复后的配置:")
        result = await conn.execute_query(
            "SELECT id, name, path, component, menu_type FROM t_sys_menu WHERE id BETWEEN 200 AND 210"
        )
        for row in result[1]:
            print(f"  ID={row['id']}, name={row['name']}, path={row['path']}, component={row['component']}, type={row['menu_type']}")
        
        print("\n✅ 路由修复完成！")
        print("\n⚠️  请重新登录或刷新页面以使更改生效")
        
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        raise
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(apply_fix())
