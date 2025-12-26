#!/usr/bin/env python3
"""
修复版的完整数据库迁移系统
解决字符编码和字段映射问题
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import traceback

# 设置数据库连接
os.environ['DATABASE_URL'] = 'postgresql://postgres:Hanatech%40123@127.0.0.1:5432/devicemonitor'

# 配置日志 - 移除emoji避免编码问题
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fixed_migration.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FixedMigrationSystem:
    """修复版的数据库迁移系统"""
    
    def __init__(self):
        self.db_url = os.environ['DATABASE_URL']
        self.conn = None
        self.migration_batch = f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
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
                完整数据库迁移系统 v2.0
              Complete Database Migration System
================================================================
  API权限重构项目 - 数据库迁移
  迁移批次: {self.migration_batch}
  开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================
        """
        print(banner)
    
    async def analyze_current_schema(self) -> Dict:
        """分析当前数据库架构"""
        logger.info("分析当前数据库架构...")
        
        try:
            # 获取所有表
            tables = await self.conn.fetch("""
                SELECT table_name, 
                       (SELECT COUNT(*) FROM information_schema.columns 
                        WHERE table_name = t.table_name AND table_schema = 'public') as column_count
                FROM information_schema.tables t
                WHERE table_schema = 'public' 
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            logger.info(f"当前数据库包含 {len(tables)} 个表:")
            current_schema = {}
            
            for table in tables:
                table_name = table['table_name']
                
                # 获取记录数
                try:
                    count = await self.conn.fetchval(f'SELECT COUNT(*) FROM "{table_name}"')
                except:
                    count = 0
                
                current_schema[table_name] = {
                    'record_count': count
                }
                
                logger.info(f"  - {table_name}: {count} 条记录")
            
            return current_schema
            
        except Exception as e:
            logger.error(f"分析当前架构失败: {e}")
            return {}
    
    async def create_migration_log_table(self):
        """创建迁移日志表"""
        logger.info("创建迁移日志表...")
        
        try:
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS t_sys_migration_logs (
                    id BIGSERIAL PRIMARY KEY,
                    migration_name VARCHAR(200) NOT NULL,
                    migration_type VARCHAR(20) NOT NULL,
                    version VARCHAR(20) NOT NULL,
                    description TEXT,
                    sql_content TEXT,
                    rollback_sql TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    error_message TEXT,
                    execution_time_ms INTEGER,
                    executed_at TIMESTAMP,
                    rolled_back_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by BIGINT
                );
                
                CREATE INDEX IF NOT EXISTS idx_migration_type ON t_sys_migration_logs(migration_type);
                CREATE INDEX IF NOT EXISTS idx_migration_status ON t_sys_migration_logs(status);
                CREATE INDEX IF NOT EXISTS idx_executed_at ON t_sys_migration_logs(executed_at);
            """)
            
            logger.info("迁移日志表创建完成")
            return True
            
        except Exception as e:
            logger.error(f"创建迁移日志表失败: {e}")
            return False
    
    async def log_migration(self, name: str, migration_type: str, version: str, 
                          description: str, sql_content: str = "", rollback_sql: str = ""):
        """记录迁移日志"""
        try:
            migration_id = await self.conn.fetchval("""
                INSERT INTO t_sys_migration_logs 
                (migration_name, migration_type, version, description, sql_content, rollback_sql, status)
                VALUES ($1, $2, $3, $4, $5, $6, 'pending')
                RETURNING id
            """, name, migration_type, version, description, sql_content, rollback_sql)
            
            return migration_id
        except Exception as e:
            logger.error(f"记录迁移日志失败: {e}")
            return None
    
    async def update_migration_status(self, migration_id: int, status: str, 
                                    error_message: str = "", execution_time: int = 0):
        """更新迁移状态"""
        try:
            await self.conn.execute("""
                UPDATE t_sys_migration_logs 
                SET status = $2, error_message = $3, execution_time_ms = $4,
                    executed_at = CASE WHEN $2 IN ('success', 'failed') THEN CURRENT_TIMESTAMP ELSE executed_at END
                WHERE id = $1
            """, migration_id, status, error_message, execution_time)
        except Exception as e:
            logger.error(f"更新迁移状态失败: {e}")
    
    async def check_and_fix_existing_tables(self):
        """检查并修复现有表结构"""
        logger.info("检查并修复现有表结构...")
        
        try:
            # 检查现有的t_sys_api_endpoints表结构
            api_endpoints_exists = await self.conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 't_sys_api_endpoints'
                )
            """)
            
            if api_endpoints_exists:
                # 检查permission_code字段是否存在
                permission_code_exists = await self.conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                          AND table_name = 't_sys_api_endpoints'
                          AND column_name = 'permission_code'
                    )
                """)
                
                if not permission_code_exists:
                    logger.info("添加permission_code字段到t_sys_api_endpoints表")
                    await self.conn.execute("""
                        ALTER TABLE t_sys_api_endpoints 
                        ADD COLUMN IF NOT EXISTS permission_code VARCHAR(255)
                    """)
            
            # 检查其他可能缺失的字段
            tables_to_check = [
                ('t_sys_dept', 'dept_name', 'VARCHAR(100)'),
                ('t_sys_user', 'nick_name', 'VARCHAR(100)'),
                ('t_sys_role', 'role_name', 'VARCHAR(100)'),
                ('t_sys_menu', 'menu_name', 'VARCHAR(100)'),
                ('t_sys_permission', 'permission_code', 'VARCHAR(255)')
            ]
            
            for table_name, column_name, column_type in tables_to_check:
                table_exists = await self.conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = $1
                    )
                """, table_name)
                
                if table_exists:
                    column_exists = await self.conn.fetchval("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_schema = 'public' 
                              AND table_name = $1
                              AND column_name = $2
                        )
                    """, table_name, column_name)
                    
                    if not column_exists:
                        logger.info(f"添加{column_name}字段到{table_name}表")
                        await self.conn.execute(f"""
                            ALTER TABLE {table_name} 
                            ADD COLUMN IF NOT EXISTS {column_name} {column_type}
                        """)
            
            logger.info("表结构检查和修复完成")
            return True
            
        except Exception as e:
            logger.error(f"表结构检查和修复失败: {e}")
            return False
    
    async def migrate_departments_safe(self):
        """安全迁移部门数据"""
        logger.info("迁移部门数据...")
        
        try:
            # 检查旧表是否存在
            dept_exists = await self.conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'dept'
                )
            """)
            
            if not dept_exists:
                logger.info("旧部门表不存在，跳过迁移")
                return True
            
            # 检查旧表的字段结构
            old_columns = await self.conn.fetch("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'dept' AND table_schema = 'public'
            """)
            
            old_column_names = [col['column_name'] for col in old_columns]
            logger.info(f"旧部门表字段: {old_column_names}")
            
            # 构建动态SQL
            select_fields = []
            if 'id' in old_column_names:
                select_fields.append('id')
            if 'parent_id' in old_column_names:
                select_fields.append('COALESCE(parent_id, 0) as parent_id')
            else:
                select_fields.append('0 as parent_id')
            
            # 处理部门名称字段的不同可能性
            if 'dept_name' in old_column_names:
                select_fields.append('dept_name')
            elif 'name' in old_column_names:
                select_fields.append('name as dept_name')
            elif 'department_name' in old_column_names:
                select_fields.append('department_name as dept_name')
            else:
                select_fields.append("'未知部门' as dept_name")
            
            if 'order_num' in old_column_names:
                select_fields.append('COALESCE(order_num, 0) as order_num')
            else:
                select_fields.append('0 as order_num')
            
            # 处理状态字段
            if 'status' in old_column_names:
                select_fields.append("CASE WHEN status = 1 THEN '0' ELSE '1' END as status")
            else:
                select_fields.append("'0' as status")
            
            # 处理时间字段
            if 'create_time' in old_column_names:
                select_fields.append('COALESCE(create_time, CURRENT_TIMESTAMP) as created_at')
            else:
                select_fields.append('CURRENT_TIMESTAMP as created_at')
                
            if 'update_time' in old_column_names:
                select_fields.append('COALESCE(update_time, CURRENT_TIMESTAMP) as updated_at')
            else:
                select_fields.append('CURRENT_TIMESTAMP as updated_at')
            
            # 执行迁移
            sql = f"""
                INSERT INTO t_sys_dept (id, parent_id, dept_name, order_num, status, created_at, updated_at)
                SELECT {', '.join(select_fields)}
                FROM dept
                ON CONFLICT (id) DO UPDATE SET
                    parent_id = EXCLUDED.parent_id,
                    dept_name = EXCLUDED.dept_name,
                    order_num = EXCLUDED.order_num,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at
            """
            
            await self.conn.execute(sql)
            
            # 更新序列
            await self.conn.execute("""
                SELECT setval('t_sys_dept_id_seq', COALESCE((SELECT MAX(id) FROM t_sys_dept), 1), false)
            """)
            
            dept_count = await self.conn.fetchval("SELECT COUNT(*) FROM t_sys_dept")
            logger.info(f"部门数据迁移完成: {dept_count} 条")
            return True
            
        except Exception as e:
            logger.error(f"部门数据迁移失败: {e}")
            return False
    
    async def migrate_users_safe(self):
        """安全迁移用户数据"""
        logger.info("迁移用户数据...")
        
        try:
            # 检查旧表是否存在
            user_exists = await self.conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'user'
                )
            """)
            
            if not user_exists:
                logger.info("旧用户表不存在，跳过迁移")
                return True
            
            # 检查旧表的字段结构
            old_columns = await self.conn.fetch("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'user' AND table_schema = 'public'
            """)
            
            old_column_names = [col['column_name'] for col in old_columns]
            logger.info(f"旧用户表字段: {old_column_names}")
            
            # 构建动态SQL
            select_fields = []
            if 'id' in old_column_names:
                select_fields.append('id')
            if 'dept_id' in old_column_names:
                select_fields.append('dept_id')
            else:
                select_fields.append('NULL as dept_id')
            
            if 'username' in old_column_names:
                select_fields.append('username')
            
            # 处理昵称字段
            if 'nick_name' in old_column_names:
                select_fields.append('COALESCE(nick_name, username) as nick_name')
            elif 'nickname' in old_column_names:
                select_fields.append('COALESCE(nickname, username) as nick_name')
            elif 'real_name' in old_column_names:
                select_fields.append('COALESCE(real_name, username) as nick_name')
            else:
                select_fields.append('username as nick_name')
            
            if 'email' in old_column_names:
                select_fields.append('email')
            else:
                select_fields.append('NULL as email')
                
            if 'phone' in old_column_names:
                select_fields.append('phone as phone_number')
            elif 'phone_number' in old_column_names:
                select_fields.append('phone_number')
            else:
                select_fields.append('NULL as phone_number')
            
            if 'password' in old_column_names:
                select_fields.append('password')
            else:
                select_fields.append("'default_password' as password")
            
            # 处理状态字段
            if 'status' in old_column_names:
                select_fields.append("CASE WHEN status = 1 THEN '0' ELSE '1' END as status")
            else:
                select_fields.append("'0' as status")
            
            # 处理时间字段
            if 'create_time' in old_column_names:
                select_fields.append('COALESCE(create_time, CURRENT_TIMESTAMP) as created_at')
            else:
                select_fields.append('CURRENT_TIMESTAMP as created_at')
                
            if 'update_time' in old_column_names:
                select_fields.append('COALESCE(update_time, CURRENT_TIMESTAMP) as updated_at')
            else:
                select_fields.append('CURRENT_TIMESTAMP as updated_at')
            
            # 执行迁移
            sql = f"""
                INSERT INTO t_sys_user (id, dept_id, username, nick_name, email, phone_number, 
                                       password, status, created_at, updated_at)
                SELECT {', '.join(select_fields)}
                FROM "user"
                ON CONFLICT (username) DO UPDATE SET
                    dept_id = EXCLUDED.dept_id,
                    nick_name = EXCLUDED.nick_name,
                    email = EXCLUDED.email,
                    phone_number = EXCLUDED.phone_number,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at
            """
            
            await self.conn.execute(sql)
            
            # 更新序列
            await self.conn.execute("""
                SELECT setval('t_sys_user_id_seq', COALESCE((SELECT MAX(id) FROM t_sys_user), 1), false)
            """)
            
            user_count = await self.conn.fetchval("SELECT COUNT(*) FROM t_sys_user")
            logger.info(f"用户数据迁移完成: {user_count} 条")
            return True
            
        except Exception as e:
            logger.error(f"用户数据迁移失败: {e}")
            return False
    
    async def migrate_roles_safe(self):
        """安全迁移角色数据"""
        logger.info("迁移角色数据...")
        
        try:
            # 检查旧表是否存在
            role_exists = await self.conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'role'
                )
            """)
            
            if not role_exists:
                logger.info("旧角色表不存在，跳过迁移")
                return True
            
            # 检查旧表的字段结构
            old_columns = await self.conn.fetch("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'role' AND table_schema = 'public'
            """)
            
            old_column_names = [col['column_name'] for col in old_columns]
            logger.info(f"旧角色表字段: {old_column_names}")
            
            # 构建动态SQL
            select_fields = []
            if 'id' in old_column_names:
                select_fields.append('id')
            
            # 处理角色名称字段
            if 'role_name' in old_column_names:
                select_fields.append('role_name')
            elif 'name' in old_column_names:
                select_fields.append('name as role_name')
            else:
                select_fields.append("'未知角色' as role_name")
            
            # 处理角色键值
            if 'role_key' in old_column_names:
                select_fields.append('COALESCE(role_key, LOWER(REPLACE(role_name, \' \', \'_\'))) as role_key')
            elif 'key' in old_column_names:
                select_fields.append('COALESCE(key, LOWER(REPLACE(role_name, \' \', \'_\'))) as role_key')
            else:
                select_fields.append('LOWER(REPLACE(COALESCE(role_name, name, \'unknown\'), \' \', \'_\')) as role_key')
            
            if 'role_sort' in old_column_names:
                select_fields.append('COALESCE(role_sort, 0) as role_sort')
            elif 'sort' in old_column_names:
                select_fields.append('COALESCE(sort, 0) as role_sort')
            else:
                select_fields.append('0 as role_sort')
            
            # 处理状态字段
            if 'status' in old_column_names:
                select_fields.append("CASE WHEN status = 1 THEN '0' ELSE '1' END as status")
            else:
                select_fields.append("'0' as status")
            
            if 'remark' in old_column_names:
                select_fields.append('remark')
            else:
                select_fields.append('NULL as remark')
            
            # 处理时间字段
            if 'create_time' in old_column_names:
                select_fields.append('COALESCE(create_time, CURRENT_TIMESTAMP) as created_at')
            else:
                select_fields.append('CURRENT_TIMESTAMP as created_at')
                
            if 'update_time' in old_column_names:
                select_fields.append('COALESCE(update_time, CURRENT_TIMESTAMP) as updated_at')
            else:
                select_fields.append('CURRENT_TIMESTAMP as updated_at')
            
            # 执行迁移
            sql = f"""
                INSERT INTO t_sys_role (id, role_name, role_key, role_sort, status, remark, created_at, updated_at)
                SELECT {', '.join(select_fields)}
                FROM role
                ON CONFLICT (role_key) DO UPDATE SET
                    role_name = EXCLUDED.role_name,
                    role_sort = EXCLUDED.role_sort,
                    status = EXCLUDED.status,
                    remark = EXCLUDED.remark,
                    updated_at = EXCLUDED.updated_at
            """
            
            await self.conn.execute(sql)
            
            # 更新序列
            await self.conn.execute("""
                SELECT setval('t_sys_role_id_seq', COALESCE((SELECT MAX(id) FROM t_sys_role), 1), false)
            """)
            
            role_count = await self.conn.fetchval("SELECT COUNT(*) FROM t_sys_role")
            logger.info(f"角色数据迁移完成: {role_count} 条")
            return True
            
        except Exception as e:
            logger.error(f"角色数据迁移失败: {e}")
            return False
    
    async def run_complete_migration(self):
        """运行完整迁移"""
        self.print_banner()
        
        try:
            # 连接数据库
            if not await self.connect():
                return False
            
            # 分析当前架构
            current_schema = await self.analyze_current_schema()
            if not current_schema:
                logger.error("无法分析当前数据库架构")
                return False
            
            # 创建迁移日志表
            if not await self.create_migration_log_table():
                logger.error("无法创建迁移日志表")
                return False
            
            # 检查并修复现有表结构
            if not await self.check_and_fix_existing_tables():
                logger.error("表结构检查和修复失败")
                return False
            
            # 安全迁移数据
            migration_tasks = [
                ("部门数据", self.migrate_departments_safe),
                ("用户数据", self.migrate_users_safe),
                ("角色数据", self.migrate_roles_safe)
            ]
            
            success_count = 0
            for task_name, task_func in migration_tasks:
                try:
                    logger.info(f"开始迁移{task_name}...")
                    if await task_func():
                        success_count += 1
                        logger.info(f"{task_name}迁移成功")
                    else:
                        logger.error(f"{task_name}迁移失败")
                except Exception as e:
                    logger.error(f"{task_name}迁移异常: {e}")
            
            logger.info(f"数据迁移完成: {success_count}/{len(migration_tasks)} 成功")
            
            if success_count >= len(migration_tasks) * 0.7:  # 70%以上成功认为迁移成功
                logger.info("数据库迁移成功完成！")
                return True
            else:
                logger.error("数据库迁移部分失败")
                return False
            
        except Exception as e:
            logger.error(f"迁移过程中发生错误: {e}")
            logger.error(traceback.format_exc())
            return False
        
        finally:
            await self.disconnect()

async def main():
    """主函数"""
    migration_system = FixedMigrationSystem()
    success = await migration_system.run_complete_migration()
    
    if success:
        print("\n数据库迁移成功完成！")
        sys.exit(0)
    else:
        print("\n数据库迁移失败！")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())