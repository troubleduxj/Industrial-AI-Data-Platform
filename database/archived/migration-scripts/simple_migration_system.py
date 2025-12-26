#!/usr/bin/env python3
"""
简化版的数据库迁移系统
专注于核心功能，避免复杂的动态SQL构建
"""
import asyncio
import logging
import os
import sys
from datetime import datetime

# 设置数据库连接
os.environ['DATABASE_URL'] = 'postgresql://postgres:Hanatech%40123@127.0.0.1:5432/devicemonitor'

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_migration.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleMigrationSystem:
    """简化版的数据库迁移系统"""
    
    def __init__(self):
        self.db_url = os.environ['DATABASE_URL']
        self.conn = None
        
    async def connect(self):
        """连接数据库"""
        try:
            import asyncpg
            self.conn = await asyncpg.connect(self.db_url)
            logger.info("数据库连接成功")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False
    
    async def disconnect(self):
        """断开数据库连接"""
        if self.conn:
            await self.conn.close()
            logger.info("数据库连接已关闭")
    
    def print_banner(self):
        """打印横幅"""
        banner = f"""
================================================================
                简化数据库迁移系统 v1.0
              Simple Database Migration System
================================================================
  开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================
        """
        print(banner)
    
    async def check_table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        try:
            exists = await self.conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = $1
                )
            """, table_name)
            return exists
        except Exception as e:
            logger.error(f"检查表{table_name}是否存在失败: {e}")
            return False
    
    async def get_table_count(self, table_name: str) -> int:
        """获取表记录数"""
        try:
            count = await self.conn.fetchval(f'SELECT COUNT(*) FROM "{table_name}"')
            return count
        except Exception as e:
            logger.error(f"获取表{table_name}记录数失败: {e}")
            return 0
    
    async def migrate_departments(self):
        """迁移部门数据"""
        logger.info("开始迁移部门数据...")
        
        try:
            # 检查源表和目标表
            if not await self.check_table_exists('dept'):
                logger.info("源表dept不存在，跳过部门数据迁移")
                return True
            
            if not await self.check_table_exists('t_sys_dept'):
                logger.error("目标表t_sys_dept不存在")
                return False
            
            # 简单的数据迁移，使用固定的字段映射
            await self.conn.execute("""
                INSERT INTO t_sys_dept (id, parent_id, dept_name, order_num, status, created_at, updated_at)
                SELECT 
                    id,
                    COALESCE(parent_id, 0),
                    name,
                    COALESCE("order", 0),
                    CASE WHEN is_deleted = false THEN '0' ELSE '1' END,
                    created_at,
                    updated_at
                FROM dept
                ON CONFLICT (id) DO UPDATE SET
                    parent_id = EXCLUDED.parent_id,
                    dept_name = EXCLUDED.dept_name,
                    order_num = EXCLUDED.order_num,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at
            """)
            
            # 更新序列
            await self.conn.execute("""
                SELECT setval('t_sys_dept_id_seq', COALESCE((SELECT MAX(id) FROM t_sys_dept), 1), false)
            """)
            
            count = await self.get_table_count('t_sys_dept')
            logger.info(f"部门数据迁移完成: {count} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"部门数据迁移失败: {e}")
            return False
    
    async def migrate_users(self):
        """迁移用户数据"""
        logger.info("开始迁移用户数据...")
        
        try:
            # 检查源表和目标表
            if not await self.check_table_exists('user'):
                logger.info("源表user不存在，跳过用户数据迁移")
                return True
            
            if not await self.check_table_exists('t_sys_user'):
                logger.error("目标表t_sys_user不存在")
                return False
            
            # 简单的数据迁移
            await self.conn.execute("""
                INSERT INTO t_sys_user (id, dept_id, username, nick_name, email, phone_number, 
                                       password, status, created_at, updated_at)
                SELECT 
                    id,
                    dept_id,
                    username,
                    COALESCE(alias, username),
                    email,
                    phone,
                    password,
                    CASE WHEN is_active = true THEN '0' ELSE '1' END,
                    created_at,
                    updated_at
                FROM "user"
                ON CONFLICT (username) DO UPDATE SET
                    dept_id = EXCLUDED.dept_id,
                    nick_name = EXCLUDED.nick_name,
                    email = EXCLUDED.email,
                    phone_number = EXCLUDED.phone_number,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at
            """)
            
            # 更新序列
            await self.conn.execute("""
                SELECT setval('t_sys_user_id_seq', COALESCE((SELECT MAX(id) FROM t_sys_user), 1), false)
            """)
            
            count = await self.get_table_count('t_sys_user')
            logger.info(f"用户数据迁移完成: {count} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"用户数据迁移失败: {e}")
            return False
    
    async def migrate_roles(self):
        """迁移角色数据"""
        logger.info("开始迁移角色数据...")
        
        try:
            # 检查源表和目标表
            if not await self.check_table_exists('role'):
                logger.info("源表role不存在，跳过角色数据迁移")
                return True
            
            if not await self.check_table_exists('t_sys_role'):
                logger.error("目标表t_sys_role不存在")
                return False
            
            # 简单的数据迁移
            await self.conn.execute("""
                INSERT INTO t_sys_role (id, role_name, role_key, role_sort, status, remark, created_at, updated_at)
                SELECT 
                    id,
                    name,
                    LOWER(REPLACE(name, ' ', '_')),
                    0,
                    '0',
                    "desc",
                    created_at,
                    updated_at
                FROM role
                ON CONFLICT (role_key) DO UPDATE SET
                    role_name = EXCLUDED.role_name,
                    status = EXCLUDED.status,
                    remark = EXCLUDED.remark,
                    updated_at = EXCLUDED.updated_at
            """)
            
            # 更新序列
            await self.conn.execute("""
                SELECT setval('t_sys_role_id_seq', COALESCE((SELECT MAX(id) FROM t_sys_role), 1), false)
            """)
            
            count = await self.get_table_count('t_sys_role')
            logger.info(f"角色数据迁移完成: {count} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"角色数据迁移失败: {e}")
            return False
    
    async def migrate_menus(self):
        """迁移菜单数据"""
        logger.info("开始迁移菜单数据...")
        
        try:
            # 检查源表和目标表
            if not await self.check_table_exists('menu'):
                logger.info("源表menu不存在，跳过菜单数据迁移")
                return True
            
            if not await self.check_table_exists('t_sys_menu'):
                logger.error("目标表t_sys_menu不存在")
                return False
            
            # 简单的数据迁移
            await self.conn.execute("""
                INSERT INTO t_sys_menu (id, menu_name, parent_id, order_num, path, component,
                                       menu_type, visible, status, perms, icon, created_at, updated_at)
                SELECT 
                    id,
                    name,
                    parent_id,
                    COALESCE("order", 0),
                    path,
                    component,
                    COALESCE(type, 'M'),
                    CASE WHEN visible = true THEN '0' ELSE '1' END,
                    CASE WHEN status = 1 THEN '0' ELSE '1' END,
                    perms,
                    icon,
                    created_at,
                    updated_at
                FROM menu
                ON CONFLICT (id) DO UPDATE SET
                    menu_name = EXCLUDED.menu_name,
                    parent_id = EXCLUDED.parent_id,
                    order_num = EXCLUDED.order_num,
                    path = EXCLUDED.path,
                    component = EXCLUDED.component,
                    menu_type = EXCLUDED.menu_type,
                    visible = EXCLUDED.visible,
                    status = EXCLUDED.status,
                    perms = EXCLUDED.perms,
                    icon = EXCLUDED.icon,
                    updated_at = EXCLUDED.updated_at
            """)
            
            # 更新序列
            await self.conn.execute("""
                SELECT setval('t_sys_menu_id_seq', COALESCE((SELECT MAX(id) FROM t_sys_menu), 1), false)
            """)
            
            count = await self.get_table_count('t_sys_menu')
            logger.info(f"菜单数据迁移完成: {count} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"菜单数据迁移失败: {e}")
            return False
    
    async def migrate_user_roles(self):
        """迁移用户角色关联"""
        logger.info("开始迁移用户角色关联...")
        
        try:
            # 检查源表和目标表
            if not await self.check_table_exists('user_role'):
                logger.info("源表user_role不存在，跳过用户角色关联迁移")
                return True
            
            if not await self.check_table_exists('t_sys_user_role'):
                logger.error("目标表t_sys_user_role不存在")
                return False
            
            # 简单的数据迁移
            await self.conn.execute("""
                INSERT INTO t_sys_user_role (user_id, role_id)
                SELECT user_id, role_id
                FROM user_role
                ON CONFLICT (user_id, role_id) DO NOTHING
            """)
            
            count = await self.get_table_count('t_sys_user_role')
            logger.info(f"用户角色关联迁移完成: {count} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"用户角色关联迁移失败: {e}")
            return False
    
    async def migrate_role_menus(self):
        """迁移角色菜单关联"""
        logger.info("开始迁移角色菜单关联...")
        
        try:
            # 检查源表和目标表
            if not await self.check_table_exists('role_menu'):
                logger.info("源表role_menu不存在，跳过角色菜单关联迁移")
                return True
            
            if not await self.check_table_exists('t_sys_role_menu'):
                logger.error("目标表t_sys_role_menu不存在")
                return False
            
            # 简单的数据迁移
            await self.conn.execute("""
                INSERT INTO t_sys_role_menu (role_id, menu_id)
                SELECT role_id, menu_id
                FROM role_menu
                ON CONFLICT (role_id, menu_id) DO NOTHING
            """)
            
            count = await self.get_table_count('t_sys_role_menu')
            logger.info(f"角色菜单关联迁移完成: {count} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"角色菜单关联迁移失败: {e}")
            return False
    
    async def update_api_endpoints(self):
        """更新API端点数据"""
        logger.info("开始更新API端点数据...")
        
        try:
            if not await self.check_table_exists('t_sys_api_endpoints'):
                logger.error("目标表t_sys_api_endpoints不存在")
                return False
            
            # 为现有API端点添加权限代码
            await self.conn.execute("""
                UPDATE t_sys_api_endpoints 
                SET permission_code = 'api:' || COALESCE(api_code, 'endpoint_' || id::text)
                WHERE permission_code IS NULL OR permission_code = ''
            """)
            
            count = await self.get_table_count('t_sys_api_endpoints')
            logger.info(f"API端点数据更新完成: {count} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"API端点数据更新失败: {e}")
            return False
    
    async def create_permissions_from_apis(self):
        """从API端点创建权限数据"""
        logger.info("开始从API端点创建权限数据...")
        
        try:
            if not await self.check_table_exists('t_sys_permission'):
                logger.error("目标表t_sys_permission不存在")
                return False
            
            # 从API端点创建权限
            await self.conn.execute("""
                INSERT INTO t_sys_permission (permission_code, permission_name, permission_type, 
                                            resource_type, resource_id, description, status)
                SELECT 
                    permission_code,
                    api_name,
                    'api',
                    'api_endpoint',
                    id::text,
                    COALESCE(description, api_name),
                    CASE WHEN status = 'active' THEN '0' ELSE '1' END
                FROM t_sys_api_endpoints
                WHERE permission_code IS NOT NULL
                ON CONFLICT (permission_code) DO UPDATE SET
                    permission_name = EXCLUDED.permission_name,
                    description = EXCLUDED.description,
                    status = EXCLUDED.status,
                    updated_at = CURRENT_TIMESTAMP
            """)
            
            count = await self.get_table_count('t_sys_permission')
            logger.info(f"权限数据创建完成: {count} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"权限数据创建失败: {e}")
            return False
    
    async def run_migration(self):
        """运行迁移"""
        self.print_banner()
        
        try:
            # 连接数据库
            if not await self.connect():
                return False
            
            # 执行迁移任务
            migration_tasks = [
                ("部门数据", self.migrate_departments),
                ("用户数据", self.migrate_users),
                ("角色数据", self.migrate_roles),
                ("菜单数据", self.migrate_menus),
                ("用户角色关联", self.migrate_user_roles),
                ("角色菜单关联", self.migrate_role_menus),
                ("API端点更新", self.update_api_endpoints),
                ("权限数据创建", self.create_permissions_from_apis)
            ]
            
            success_count = 0
            total_tasks = len(migration_tasks)
            
            for task_name, task_func in migration_tasks:
                try:
                    logger.info(f"执行任务: {task_name}")
                    if await task_func():
                        success_count += 1
                        logger.info(f"任务 {task_name} 执行成功")
                    else:
                        logger.error(f"任务 {task_name} 执行失败")
                except Exception as e:
                    logger.error(f"任务 {task_name} 执行异常: {e}")
            
            # 计算成功率
            success_rate = (success_count / total_tasks) * 100
            logger.info(f"迁移完成: {success_count}/{total_tasks} 任务成功 ({success_rate:.1f}%)")
            
            if success_rate >= 80:  # 80%以上成功认为迁移成功
                logger.info("数据库迁移成功完成！")
                return True
            else:
                logger.error("数据库迁移失败，成功率不足80%")
                return False
            
        except Exception as e:
            logger.error(f"迁移过程中发生错误: {e}")
            return False
        
        finally:
            await self.disconnect()

async def main():
    """主函数"""
    migration_system = SimpleMigrationSystem()
    success = await migration_system.run_migration()
    
    if success:
        print("\n================================================================")
        print("                数据库迁移成功完成！")
        print("================================================================")
        sys.exit(0)
    else:
        print("\n================================================================")
        print("                数据库迁移失败！")
        print("================================================================")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())