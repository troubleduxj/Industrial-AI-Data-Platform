#!/usr/bin/env python3
"""
完整的数据库迁移系统
基于API权限重构项目需求的完整迁移解决方案
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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('complete_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CompleteMigrationSystem:
    """完整的数据库迁移系统"""
    
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
╔══════════════════════════════════════════════════════════════╗
║                 🚀 完整数据库迁移系统                        ║
║              Complete Database Migration System             ║
╠══════════════════════════════════════════════════════════════╣
║  API权限重构项目 - 数据库迁移                                ║
║  迁移批次: {self.migration_batch}                    ║
║  开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                           ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    async def analyze_current_schema(self) -> Dict:
        """分析当前数据库架构"""
        logger.info("🔍 分析当前数据库架构...")
        
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
                
                # 获取表的列信息
                columns = await self.conn.fetch("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = $1 AND table_schema = 'public'
                    ORDER BY ordinal_position
                """, table_name)
                
                # 获取记录数
                try:
                    count = await self.conn.fetchval(f'SELECT COUNT(*) FROM "{table_name}"')
                except:
                    count = 0
                
                current_schema[table_name] = {
                    'columns': [dict(col) for col in columns],
                    'record_count': count
                }
                
                logger.info(f"  - {table_name}: {len(columns)} 列, {count} 条记录")
            
            return current_schema
            
        except Exception as e:
            logger.error(f"分析当前架构失败: {e}")
            return {}
    
    async def create_migration_log_table(self):
        """创建迁移日志表"""
        logger.info("📝 创建迁移日志表...")
        
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
                    created_by BIGINT,
                    
                    CONSTRAINT chk_migration_type CHECK (migration_type IN ('schema', 'data', 'permission', 'api')),
                    CONSTRAINT chk_migration_status CHECK (status IN ('pending', 'running', 'success', 'failed', 'rolled_back'))
                );
                
                CREATE INDEX IF NOT EXISTS idx_migration_type ON t_sys_migration_logs(migration_type);
                CREATE INDEX IF NOT EXISTS idx_migration_status ON t_sys_migration_logs(status);
                CREATE INDEX IF NOT EXISTS idx_executed_at ON t_sys_migration_logs(executed_at);
            """)
            
            logger.info("✅ 迁移日志表创建完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建迁移日志表失败: {e}")
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
    
    async def create_standard_tables(self):
        """创建标准化表结构"""
        logger.info("🏗️ 创建标准化表结构...")
        
        # 表创建脚本列表
        table_scripts = [
            # 1. 系统配置表
            {
                'name': '系统配置表',
                'sql': """
                    CREATE TABLE IF NOT EXISTS t_sys_config (
                        id BIGSERIAL PRIMARY KEY,
                        config_key VARCHAR(100) NOT NULL UNIQUE,
                        config_value TEXT,
                        config_type VARCHAR(20) DEFAULT 'string',
                        description TEXT,
                        is_system BOOLEAN DEFAULT FALSE,
                        is_encrypted BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT chk_sys_config_type CHECK (config_type IN ('string', 'number', 'boolean', 'json', 'array'))
                    );
                """
            },
            # 2. 系统字典类型表
            {
                'name': '系统字典类型表',
                'sql': """
                    CREATE TABLE IF NOT EXISTS t_sys_dict_type (
                        id BIGSERIAL PRIMARY KEY,
                        dict_name VARCHAR(100) NOT NULL,
                        dict_type VARCHAR(100) NOT NULL UNIQUE,
                        status VARCHAR(1) DEFAULT '0',
                        remark TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT chk_sys_dict_type_status CHECK (status IN ('0', '1'))
                    );
                """
            },
            # 3. 系统字典数据表
            {
                'name': '系统字典数据表',
                'sql': """
                    CREATE TABLE IF NOT EXISTS t_sys_dict_data (
                        id BIGSERIAL PRIMARY KEY,
                        dict_sort INTEGER DEFAULT 0,
                        dict_label VARCHAR(100) NOT NULL,
                        dict_value VARCHAR(100) NOT NULL,
                        dict_type VARCHAR(100) NOT NULL,
                        css_class VARCHAR(100),
                        list_class VARCHAR(100),
                        is_default BOOLEAN DEFAULT FALSE,
                        status VARCHAR(1) DEFAULT '0',
                        remark TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT chk_sys_dict_data_status CHECK (status IN ('0', '1'))
                    );
                """
            },
            # 4. 部门表
            {
                'name': '部门表',
                'sql': """
                    CREATE TABLE IF NOT EXISTS t_sys_dept (
                        id BIGSERIAL PRIMARY KEY,
                        parent_id BIGINT DEFAULT 0,
                        ancestors VARCHAR(500) DEFAULT '',
                        dept_name VARCHAR(30) NOT NULL,
                        order_num INTEGER DEFAULT 0,
                        leader VARCHAR(20),
                        phone VARCHAR(11),
                        email VARCHAR(50),
                        status VARCHAR(1) DEFAULT '0',
                        del_flag VARCHAR(1) DEFAULT '0',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT chk_sys_dept_status CHECK (status IN ('0', '1')),
                        CONSTRAINT chk_sys_dept_del_flag CHECK (del_flag IN ('0', '2'))
                    );
                """
            },
            # 5. 用户表
            {
                'name': '用户表',
                'sql': """
                    CREATE TABLE IF NOT EXISTS t_sys_user (
                        id BIGSERIAL PRIMARY KEY,
                        dept_id BIGINT,
                        username VARCHAR(30) NOT NULL UNIQUE,
                        nick_name VARCHAR(30) NOT NULL,
                        user_type VARCHAR(2) DEFAULT '00',
                        email VARCHAR(50),
                        phone_number VARCHAR(11),
                        sex VARCHAR(1) DEFAULT '0',
                        avatar VARCHAR(100),
                        password VARCHAR(100) NOT NULL,
                        status VARCHAR(1) DEFAULT '0',
                        del_flag VARCHAR(1) DEFAULT '0',
                        login_ip VARCHAR(128),
                        login_date TIMESTAMP,
                        remark TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT chk_sys_user_sex CHECK (sex IN ('0', '1', '2')),
                        CONSTRAINT chk_sys_user_status CHECK (status IN ('0', '1')),
                        CONSTRAINT chk_sys_user_del_flag CHECK (del_flag IN ('0', '2'))
                    );
                """
            },
            # 6. 角色表
            {
                'name': '角色表',
                'sql': """
                    CREATE TABLE IF NOT EXISTS t_sys_role (
                        id BIGSERIAL PRIMARY KEY,
                        role_name VARCHAR(30) NOT NULL,
                        role_key VARCHAR(100) NOT NULL UNIQUE,
                        role_sort INTEGER NOT NULL,
                        data_scope VARCHAR(1) DEFAULT '1',
                        menu_check_strictly BOOLEAN DEFAULT TRUE,
                        dept_check_strictly BOOLEAN DEFAULT TRUE,
                        status VARCHAR(1) DEFAULT '0',
                        del_flag VARCHAR(1) DEFAULT '0',
                        remark TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT chk_sys_role_data_scope CHECK (data_scope IN ('1', '2', '3', '4', '5')),
                        CONSTRAINT chk_sys_role_status CHECK (status IN ('0', '1')),
                        CONSTRAINT chk_sys_role_del_flag CHECK (del_flag IN ('0', '2'))
                    );
                """
            },
            # 7. 用户角色关联表
            {
                'name': '用户角色关联表',
                'sql': """
                    CREATE TABLE IF NOT EXISTS t_sys_user_role (
                        user_id BIGINT NOT NULL,
                        role_id BIGINT NOT NULL,
                        PRIMARY KEY (user_id, role_id)
                    );
                """
            },
            # 8. 菜单表
            {
                'name': '菜单表',
                'sql': """
                    CREATE TABLE IF NOT EXISTS t_sys_menu (
                        id BIGSERIAL PRIMARY KEY,
                        menu_name VARCHAR(50) NOT NULL,
                        parent_id BIGINT DEFAULT 0,
                        order_num INTEGER DEFAULT 0,
                        path VARCHAR(200),
                        component VARCHAR(255),
                        query_param VARCHAR(255),
                        is_frame INTEGER DEFAULT 1,
                        is_cache INTEGER DEFAULT 0,
                        menu_type VARCHAR(1) NOT NULL,
                        visible VARCHAR(1) DEFAULT '0',
                        status VARCHAR(1) DEFAULT '0',
                        perms VARCHAR(100),
                        icon VARCHAR(100),
                        remark TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT chk_sys_menu_is_frame CHECK (is_frame IN (0, 1)),
                        CONSTRAINT chk_sys_menu_is_cache CHECK (is_cache IN (0, 1)),
                        CONSTRAINT chk_sys_menu_menu_type CHECK (menu_type IN ('M', 'C', 'F')),
                        CONSTRAINT chk_sys_menu_visible CHECK (visible IN ('0', '1')),
                        CONSTRAINT chk_sys_menu_status CHECK (status IN ('0', '1'))
                    );
                """
            },
            # 9. 角色菜单关联表
            {
                'name': '角色菜单关联表',
                'sql': """
                    CREATE TABLE IF NOT EXISTS t_sys_role_menu (
                        role_id BIGINT NOT NULL,
                        menu_id BIGINT NOT NULL,
                        PRIMARY KEY (role_id, menu_id)
                    );
                """
            },
            # 10. API分组表
            {
                'name': 'API分组表',
                'sql': """
                    CREATE TABLE IF NOT EXISTS t_sys_api_groups (
                        id BIGSERIAL PRIMARY KEY,
                        group_code VARCHAR(50) NOT NULL UNIQUE,
                        group_name VARCHAR(100) NOT NULL,
                        parent_id BIGINT DEFAULT 0,
                        description TEXT,
                        sort_order INTEGER DEFAULT 0,
                        status VARCHAR(20) DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT chk_api_group_status CHECK (status IN ('active', 'inactive', 'deprecated'))
                    );
                """
            },
            # 11. API端点表
            {
                'name': 'API端点表',
                'sql': """
                    CREATE TABLE IF NOT EXISTS t_sys_api_endpoints (
                        id BIGSERIAL PRIMARY KEY,
                        api_code VARCHAR(100) NOT NULL UNIQUE,
                        api_name VARCHAR(200) NOT NULL,
                        api_path VARCHAR(500) NOT NULL,
                        http_method VARCHAR(10) NOT NULL,
                        group_id BIGINT NOT NULL DEFAULT 1,
                        description TEXT,
                        version VARCHAR(10) DEFAULT 'v2',
                        is_public BOOLEAN DEFAULT FALSE,
                        is_deprecated BOOLEAN DEFAULT FALSE,
                        rate_limit INTEGER DEFAULT 0,
                        auth_required BOOLEAN DEFAULT TRUE,
                        permission_code VARCHAR(255),
                        tags JSONB DEFAULT '[]',
                        request_schema JSONB,
                        response_schema JSONB,
                        status VARCHAR(20) DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT chk_http_method CHECK (http_method IN ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS')),
                        CONSTRAINT chk_api_endpoint_status CHECK (status IN ('active', 'inactive', 'deprecated'))
                    );
                """
            },
            # 12. 权限表
            {
                'name': '权限表',
                'sql': """
                    CREATE TABLE IF NOT EXISTS t_sys_permission (
                        id BIGSERIAL PRIMARY KEY,
                        permission_code VARCHAR(255) NOT NULL UNIQUE,
                        permission_name VARCHAR(200) NOT NULL,
                        permission_type VARCHAR(20) NOT NULL DEFAULT 'api',
                        resource_type VARCHAR(50),
                        resource_id VARCHAR(100),
                        description TEXT,
                        parent_id BIGINT DEFAULT 0,
                        sort_order INTEGER DEFAULT 0,
                        status VARCHAR(1) DEFAULT '0',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT chk_permission_type CHECK (permission_type IN ('api', 'menu', 'button', 'data')),
                        CONSTRAINT chk_permission_status CHECK (status IN ('0', '1'))
                    );
                """
            },
            # 13. 角色权限关联表
            {
                'name': '角色权限关联表',
                'sql': """
                    CREATE TABLE IF NOT EXISTS t_sys_role_permission (
                        id BIGSERIAL PRIMARY KEY,
                        role_id BIGINT NOT NULL,
                        permission_id BIGINT NOT NULL,
                        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        granted_by BIGINT,
                        UNIQUE(role_id, permission_id)
                    );
                """
            },
            # 14. 用户权限表
            {
                'name': '用户权限表',
                'sql': """
                    CREATE TABLE IF NOT EXISTS t_sys_user_permission (
                        id BIGSERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        permission_id BIGINT NOT NULL,
                        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        granted_by BIGINT,
                        expires_at TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        UNIQUE(user_id, permission_id)
                    );
                """
            }
        ]
        
        success_count = 0
        for script in table_scripts:
            try:
                migration_id = await self.log_migration(
                    f"create_table_{script['name']}", 
                    'schema', 
                    'v2.0', 
                    f"创建{script['name']}", 
                    script['sql']
                )
                
                start_time = datetime.now()
                await self.conn.execute(script['sql'])
                execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                
                await self.update_migration_status(migration_id, 'success', '', execution_time)
                logger.info(f"✅ {script['name']} 创建成功")
                success_count += 1
                
            except Exception as e:
                await self.update_migration_status(migration_id, 'failed', str(e))
                logger.error(f"❌ {script['name']} 创建失败: {e}")
        
        logger.info(f"📊 表结构创建完成: {success_count}/{len(table_scripts)} 成功")
        return success_count == len(table_scripts)
    
    async def create_indexes(self):
        """创建索引"""
        logger.info("🔍 创建数据库索引...")
        
        index_scripts = [
            "CREATE INDEX IF NOT EXISTS idx_api_endpoints_code ON t_sys_api_endpoints(api_code);",
            "CREATE INDEX IF NOT EXISTS idx_api_endpoints_path ON t_sys_api_endpoints(api_path);",
            "CREATE INDEX IF NOT EXISTS idx_api_endpoints_method ON t_sys_api_endpoints(http_method);",
            "CREATE INDEX IF NOT EXISTS idx_api_endpoints_group ON t_sys_api_endpoints(group_id);",
            "CREATE INDEX IF NOT EXISTS idx_api_endpoints_status ON t_sys_api_endpoints(status);",
            "CREATE INDEX IF NOT EXISTS idx_permission_code ON t_sys_permission(permission_code);",
            "CREATE INDEX IF NOT EXISTS idx_permission_type ON t_sys_permission(permission_type);",
            "CREATE INDEX IF NOT EXISTS idx_permission_status ON t_sys_permission(status);",
            "CREATE INDEX IF NOT EXISTS idx_user_username ON t_sys_user(username);",
            "CREATE INDEX IF NOT EXISTS idx_user_status ON t_sys_user(status);",
            "CREATE INDEX IF NOT EXISTS idx_user_dept ON t_sys_user(dept_id);",
            "CREATE INDEX IF NOT EXISTS idx_role_key ON t_sys_role(role_key);",
            "CREATE INDEX IF NOT EXISTS idx_role_status ON t_sys_role(status);"
        ]
        
        success_count = 0
        for sql in index_scripts:
            try:
                await self.conn.execute(sql)
                success_count += 1
            except Exception as e:
                logger.error(f"创建索引失败: {sql} - {e}")
        
        logger.info(f"✅ 索引创建完成: {success_count}/{len(index_scripts)} 成功")
        return success_count == len(index_scripts)   
 
    async def migrate_existing_data(self):
        """迁移现有数据"""
        logger.info("📦 开始迁移现有数据...")
        
        migration_tasks = [
            self.migrate_departments,
            self.migrate_users,
            self.migrate_roles,
            self.migrate_user_roles,
            self.migrate_menus,
            self.migrate_role_menus,
            self.migrate_api_groups,
            self.migrate_api_endpoints,
            self.migrate_permissions
        ]
        
        success_count = 0
        for task in migration_tasks:
            try:
                if await task():
                    success_count += 1
            except Exception as e:
                logger.error(f"迁移任务失败 {task.__name__}: {e}")
        
        logger.info(f"📊 数据迁移完成: {success_count}/{len(migration_tasks)} 成功")
        return success_count == len(migration_tasks)
    
    async def migrate_departments(self):
        """迁移部门数据"""
        logger.info("🏢 迁移部门数据...")
        
        try:
            # 检查旧表是否存在
            dept_exists = await self.conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'dept'
                )
            """)
            
            if not dept_exists:
                logger.info("⚠️ 旧部门表不存在，跳过迁移")
                return True
            
            migration_id = await self.log_migration(
                "migrate_departments", 
                'data', 
                'v2.0', 
                "迁移部门数据从dept表到t_sys_dept表"
            )
            
            start_time = datetime.now()
            
            # 迁移部门数据
            await self.conn.execute("""
                INSERT INTO t_sys_dept (id, parent_id, dept_name, order_num, status, created_at, updated_at)
                SELECT id, 
                       COALESCE(parent_id, 0), 
                       dept_name,
                       COALESCE(order_num, 0), 
                       CASE WHEN status = 1 THEN '0' ELSE '1' END,
                       COALESCE(create_time, CURRENT_TIMESTAMP),
                       COALESCE(update_time, CURRENT_TIMESTAMP)
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
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            dept_count = await self.conn.fetchval("SELECT COUNT(*) FROM t_sys_dept")
            
            await self.update_migration_status(migration_id, 'success', '', execution_time)
            logger.info(f"✅ 部门数据迁移完成: {dept_count} 条")
            return True
            
        except Exception as e:
            await self.update_migration_status(migration_id, 'failed', str(e))
            logger.error(f"❌ 部门数据迁移失败: {e}")
            return False
    
    async def migrate_users(self):
        """迁移用户数据"""
        logger.info("👤 迁移用户数据...")
        
        try:
            # 检查旧表是否存在
            user_exists = await self.conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'user'
                )
            """)
            
            if not user_exists:
                logger.info("⚠️ 旧用户表不存在，跳过迁移")
                return True
            
            migration_id = await self.log_migration(
                "migrate_users", 
                'data', 
                'v2.0', 
                "迁移用户数据从user表到t_sys_user表"
            )
            
            start_time = datetime.now()
            
            # 迁移用户数据
            await self.conn.execute("""
                INSERT INTO t_sys_user (id, dept_id, username, nick_name, email, phone_number, 
                                       password, status, created_at, updated_at)
                SELECT id, 
                       dept_id, 
                       username, 
                       COALESCE(nick_name, username),
                       email, 
                       phone,
                       password,
                       CASE WHEN status = 1 THEN '0' ELSE '1' END,
                       COALESCE(create_time, CURRENT_TIMESTAMP),
                       COALESCE(update_time, CURRENT_TIMESTAMP)
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
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            user_count = await self.conn.fetchval("SELECT COUNT(*) FROM t_sys_user")
            
            await self.update_migration_status(migration_id, 'success', '', execution_time)
            logger.info(f"✅ 用户数据迁移完成: {user_count} 条")
            return True
            
        except Exception as e:
            await self.update_migration_status(migration_id, 'failed', str(e))
            logger.error(f"❌ 用户数据迁移失败: {e}")
            return False
    
    async def migrate_roles(self):
        """迁移角色数据"""
        logger.info("🎭 迁移角色数据...")
        
        try:
            # 检查旧表是否存在
            role_exists = await self.conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'role'
                )
            """)
            
            if not role_exists:
                logger.info("⚠️ 旧角色表不存在，跳过迁移")
                return True
            
            migration_id = await self.log_migration(
                "migrate_roles", 
                'data', 
                'v2.0', 
                "迁移角色数据从role表到t_sys_role表"
            )
            
            start_time = datetime.now()
            
            # 迁移角色数据
            await self.conn.execute("""
                INSERT INTO t_sys_role (id, role_name, role_key, role_sort, status, remark, created_at, updated_at)
                SELECT id, 
                       role_name, 
                       COALESCE(role_key, LOWER(REPLACE(role_name, ' ', '_'))),
                       COALESCE(role_sort, 0),
                       CASE WHEN status = 1 THEN '0' ELSE '1' END,
                       remark,
                       COALESCE(create_time, CURRENT_TIMESTAMP),
                       COALESCE(update_time, CURRENT_TIMESTAMP)
                FROM role
                ON CONFLICT (role_key) DO UPDATE SET
                    role_name = EXCLUDED.role_name,
                    role_sort = EXCLUDED.role_sort,
                    status = EXCLUDED.status,
                    remark = EXCLUDED.remark,
                    updated_at = EXCLUDED.updated_at
            """)
            
            # 更新序列
            await self.conn.execute("""
                SELECT setval('t_sys_role_id_seq', COALESCE((SELECT MAX(id) FROM t_sys_role), 1), false)
            """)
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            role_count = await self.conn.fetchval("SELECT COUNT(*) FROM t_sys_role")
            
            await self.update_migration_status(migration_id, 'success', '', execution_time)
            logger.info(f"✅ 角色数据迁移完成: {role_count} 条")
            return True
            
        except Exception as e:
            await self.update_migration_status(migration_id, 'failed', str(e))
            logger.error(f"❌ 角色数据迁移失败: {e}")
            return False
    
    async def migrate_user_roles(self):
        """迁移用户角色关联"""
        logger.info("🔗 迁移用户角色关联...")
        
        try:
            # 检查旧表是否存在
            user_role_exists = await self.conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'user_role'
                )
            """)
            
            if not user_role_exists:
                logger.info("⚠️ 旧用户角色关联表不存在，跳过迁移")
                return True
            
            migration_id = await self.log_migration(
                "migrate_user_roles", 
                'data', 
                'v2.0', 
                "迁移用户角色关联从user_role表到t_sys_user_role表"
            )
            
            start_time = datetime.now()
            
            # 迁移用户角色关联
            await self.conn.execute("""
                INSERT INTO t_sys_user_role (user_id, role_id)
                SELECT user_id, role_id
                FROM user_role
                ON CONFLICT (user_id, role_id) DO NOTHING
            """)
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            user_role_count = await self.conn.fetchval("SELECT COUNT(*) FROM t_sys_user_role")
            
            await self.update_migration_status(migration_id, 'success', '', execution_time)
            logger.info(f"✅ 用户角色关联迁移完成: {user_role_count} 条")
            return True
            
        except Exception as e:
            await self.update_migration_status(migration_id, 'failed', str(e))
            logger.error(f"❌ 用户角色关联迁移失败: {e}")
            return False
    
    async def migrate_menus(self):
        """迁移菜单数据"""
        logger.info("📋 迁移菜单数据...")
        
        try:
            # 检查旧表是否存在
            menu_exists = await self.conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'menu'
                )
            """)
            
            if not menu_exists:
                logger.info("⚠️ 旧菜单表不存在，跳过迁移")
                return True
            
            migration_id = await self.log_migration(
                "migrate_menus", 
                'data', 
                'v2.0', 
                "迁移菜单数据从menu表到t_sys_menu表"
            )
            
            start_time = datetime.now()
            
            # 迁移菜单数据
            await self.conn.execute("""
                INSERT INTO t_sys_menu (id, menu_name, parent_id, order_num, path, component,
                                       menu_type, visible, status, perms, icon, created_at, updated_at)
                SELECT id, 
                       menu_name, 
                       parent_id, 
                       COALESCE(order_num, 0),
                       path, 
                       component,
                       COALESCE(menu_type, 'M'),
                       CASE WHEN visible = 1 THEN '0' ELSE '1' END,
                       CASE WHEN status = 1 THEN '0' ELSE '1' END,
                       perms, 
                       icon,
                       COALESCE(create_time, CURRENT_TIMESTAMP),
                       COALESCE(update_time, CURRENT_TIMESTAMP)
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
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            menu_count = await self.conn.fetchval("SELECT COUNT(*) FROM t_sys_menu")
            
            await self.update_migration_status(migration_id, 'success', '', execution_time)
            logger.info(f"✅ 菜单数据迁移完成: {menu_count} 条")
            return True
            
        except Exception as e:
            await self.update_migration_status(migration_id, 'failed', str(e))
            logger.error(f"❌ 菜单数据迁移失败: {e}")
            return False
    
    async def migrate_role_menus(self):
        """迁移角色菜单关联"""
        logger.info("🔗 迁移角色菜单关联...")
        
        try:
            # 检查旧表是否存在
            role_menu_exists = await self.conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'role_menu'
                )
            """)
            
            if not role_menu_exists:
                logger.info("⚠️ 旧角色菜单关联表不存在，跳过迁移")
                return True
            
            migration_id = await self.log_migration(
                "migrate_role_menus", 
                'data', 
                'v2.0', 
                "迁移角色菜单关联从role_menu表到t_sys_role_menu表"
            )
            
            start_time = datetime.now()
            
            # 迁移角色菜单关联
            await self.conn.execute("""
                INSERT INTO t_sys_role_menu (role_id, menu_id)
                SELECT role_id, menu_id
                FROM role_menu
                ON CONFLICT (role_id, menu_id) DO NOTHING
            """)
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            role_menu_count = await self.conn.fetchval("SELECT COUNT(*) FROM t_sys_role_menu")
            
            await self.update_migration_status(migration_id, 'success', '', execution_time)
            logger.info(f"✅ 角色菜单关联迁移完成: {role_menu_count} 条")
            return True
            
        except Exception as e:
            await self.update_migration_status(migration_id, 'failed', str(e))
            logger.error(f"❌ 角色菜单关联迁移失败: {e}")
            return False
    
    async def migrate_api_groups(self):
        """迁移API分组数据"""
        logger.info("📁 迁移API分组数据...")
        
        try:
            migration_id = await self.log_migration(
                "migrate_api_groups", 
                'data', 
                'v2.0', 
                "创建标准API分组数据"
            )
            
            start_time = datetime.now()
            
            # 插入标准API分组
            api_groups = [
                ('system', '系统管理', 0, '系统核心功能管理', 1),
                ('system.users', '用户管理', 1, '用户账户管理', 1),
                ('system.roles', '角色管理', 1, '角色权限管理', 2),
                ('system.menus', '菜单管理', 1, '系统菜单管理', 3),
                ('system.departments', '部门管理', 1, '组织架构管理', 4),
                ('system.apis', 'API管理', 1, 'API接口管理', 5),
                ('devices', '设备管理', 0, '设备相关功能', 2),
                ('devices.assets', '设备信息', 7, '设备基础信息管理', 1),
                ('devices.types', '设备类型', 7, '设备类型管理', 2),
                ('devices.monitoring', '设备监控', 7, '设备状态监控', 3),
                ('devices.maintenance', '设备维护', 7, '设备维护管理', 4),
                ('ai', 'AI监控', 0, 'AI智能监控功能', 3),
                ('ai.predictions', '趋势预测', 12, 'AI趋势预测', 1),
                ('ai.models', '模型管理', 12, 'AI模型管理', 2),
                ('ai.annotations', '数据标注', 12, '数据标注管理', 3),
                ('ai.health', '健康评分', 12, '设备健康评分', 4),
                ('ai.analysis', '智能分析', 12, '智能分析功能', 5),
                ('alarms', '报警管理', 0, '报警信息管理', 4),
                ('statistics', '统计分析', 0, '数据统计分析', 5),
                ('dashboard', '仪表板', 0, '数据仪表板', 6)
            ]
            
            for group_code, group_name, parent_id, description, sort_order in api_groups:
                await self.conn.execute("""
                    INSERT INTO t_sys_api_groups (group_code, group_name, parent_id, description, sort_order)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (group_code) DO UPDATE SET
                        group_name = EXCLUDED.group_name,
                        parent_id = EXCLUDED.parent_id,
                        description = EXCLUDED.description,
                        sort_order = EXCLUDED.sort_order,
                        updated_at = CURRENT_TIMESTAMP
                """, group_code, group_name, parent_id, description, sort_order)
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            group_count = await self.conn.fetchval("SELECT COUNT(*) FROM t_sys_api_groups")
            
            await self.update_migration_status(migration_id, 'success', '', execution_time)
            logger.info(f"✅ API分组数据迁移完成: {group_count} 条")
            return True
            
        except Exception as e:
            await self.update_migration_status(migration_id, 'failed', str(e))
            logger.error(f"❌ API分组数据迁移失败: {e}")
            return False    

    async def migrate_api_endpoints(self):
        """迁移API端点数据"""
        logger.info("🔌 迁移API端点数据...")
        
        try:
            migration_id = await self.log_migration(
                "migrate_api_endpoints", 
                'data', 
                'v2.0', 
                "迁移API端点数据并标准化路径格式"
            )
            
            start_time = datetime.now()
            
            # 检查旧API表是否存在
            api_exists = await self.conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'api'
                )
            """)
            
            if api_exists:
                # 从旧API表迁移数据
                await self.conn.execute("""
                    INSERT INTO t_sys_api_endpoints (api_code, api_name, api_path, http_method, 
                                                   group_id, description, permission_code, status, created_at, updated_at)
                    SELECT 
                        COALESCE(code, 'api_' || id::text) as api_code,
                        COALESCE(name, title, 'API ' || id::text) as api_name,
                        CASE 
                            WHEN path LIKE '/api/v2/%' THEN path
                            WHEN path LIKE '/api/%' THEN REPLACE(path, '/api/', '/api/v2/')
                            ELSE '/api/v2' || path
                        END as api_path,
                        UPPER(COALESCE(method, 'GET')) as http_method,
                        1 as group_id,  -- 默认分组
                        COALESCE(description, remark, '') as description,
                        'api:' || COALESCE(code, 'api_' || id::text) as permission_code,
                        CASE WHEN status = 1 THEN 'active' ELSE 'inactive' END,
                        COALESCE(create_time, CURRENT_TIMESTAMP),
                        COALESCE(update_time, CURRENT_TIMESTAMP)
                    FROM api
                    ON CONFLICT (api_code) DO UPDATE SET
                        api_name = EXCLUDED.api_name,
                        api_path = EXCLUDED.api_path,
                        http_method = EXCLUDED.http_method,
                        description = EXCLUDED.description,
                        permission_code = EXCLUDED.permission_code,
                        status = EXCLUDED.status,
                        updated_at = EXCLUDED.updated_at
                """)
            
            # 添加标准API端点
            standard_apis = [
                # 系统管理API
                ('system.users.list', '用户列表', '/api/v2/system/users', 'GET', 2, '获取用户列表'),
                ('system.users.create', '创建用户', '/api/v2/system/users', 'POST', 2, '创建新用户'),
                ('system.users.update', '更新用户', '/api/v2/system/users/{id}', 'PUT', 2, '更新用户信息'),
                ('system.users.delete', '删除用户', '/api/v2/system/users/{id}', 'DELETE', 2, '删除用户'),
                ('system.users.detail', '用户详情', '/api/v2/system/users/{id}', 'GET', 2, '获取用户详情'),
                
                ('system.roles.list', '角色列表', '/api/v2/system/roles', 'GET', 3, '获取角色列表'),
                ('system.roles.create', '创建角色', '/api/v2/system/roles', 'POST', 3, '创建新角色'),
                ('system.roles.update', '更新角色', '/api/v2/system/roles/{id}', 'PUT', 3, '更新角色信息'),
                ('system.roles.delete', '删除角色', '/api/v2/system/roles/{id}', 'DELETE', 3, '删除角色'),
                ('system.roles.permissions', '角色权限', '/api/v2/system/roles/{id}/permissions', 'GET', 3, '获取角色权限'),
                
                ('system.menus.list', '菜单列表', '/api/v2/system/menus', 'GET', 4, '获取菜单列表'),
                ('system.menus.tree', '菜单树', '/api/v2/system/menus/tree', 'GET', 4, '获取菜单树结构'),
                ('system.menus.create', '创建菜单', '/api/v2/system/menus', 'POST', 4, '创建新菜单'),
                ('system.menus.update', '更新菜单', '/api/v2/system/menus/{id}', 'PUT', 4, '更新菜单信息'),
                ('system.menus.delete', '删除菜单', '/api/v2/system/menus/{id}', 'DELETE', 4, '删除菜单'),
                
                ('system.departments.list', '部门列表', '/api/v2/system/departments', 'GET', 5, '获取部门列表'),
                ('system.departments.tree', '部门树', '/api/v2/system/departments/tree', 'GET', 5, '获取部门树结构'),
                ('system.departments.create', '创建部门', '/api/v2/system/departments', 'POST', 5, '创建新部门'),
                ('system.departments.update', '更新部门', '/api/v2/system/departments/{id}', 'PUT', 5, '更新部门信息'),
                ('system.departments.delete', '删除部门', '/api/v2/system/departments/{id}', 'DELETE', 5, '删除部门'),
                
                # 设备管理API
                ('devices.assets.list', '设备列表', '/api/v2/devices/assets', 'GET', 8, '获取设备列表'),
                ('devices.assets.create', '创建设备', '/api/v2/devices/assets', 'POST', 8, '创建新设备'),
                ('devices.assets.update', '更新设备', '/api/v2/devices/assets/{id}', 'PUT', 8, '更新设备信息'),
                ('devices.assets.delete', '删除设备', '/api/v2/devices/assets/{id}', 'DELETE', 8, '删除设备'),
                ('devices.assets.detail', '设备详情', '/api/v2/devices/assets/{id}', 'GET', 8, '获取设备详情'),
                ('devices.assets.status', '设备状态', '/api/v2/devices/assets/{id}/status', 'GET', 8, '获取设备状态'),
                
                ('devices.types.list', '设备类型列表', '/api/v2/devices/types', 'GET', 9, '获取设备类型列表'),
                ('devices.types.create', '创建设备类型', '/api/v2/devices/types', 'POST', 9, '创建新设备类型'),
                ('devices.types.update', '更新设备类型', '/api/v2/devices/types/{id}', 'PUT', 9, '更新设备类型'),
                ('devices.types.delete', '删除设备类型', '/api/v2/devices/types/{id}', 'DELETE', 9, '删除设备类型'),
                
                ('devices.monitoring.realtime', '实时监控', '/api/v2/devices/monitoring/realtime', 'GET', 10, '获取实时监控数据'),
                ('devices.monitoring.history', '历史数据', '/api/v2/devices/monitoring/history', 'GET', 10, '获取历史监控数据'),
                ('devices.monitoring.alerts', '监控告警', '/api/v2/devices/monitoring/alerts', 'GET', 10, '获取监控告警'),
                
                ('devices.maintenance.list', '维护记录', '/api/v2/devices/maintenance', 'GET', 11, '获取维护记录'),
                ('devices.maintenance.create', '创建维护', '/api/v2/devices/maintenance', 'POST', 11, '创建维护记录'),
                ('devices.maintenance.update', '更新维护', '/api/v2/devices/maintenance/{id}', 'PUT', 11, '更新维护记录'),
                ('devices.maintenance.schedule', '维护计划', '/api/v2/devices/maintenance/schedule', 'GET', 11, '获取维护计划'),
                
                # AI监控API
                ('ai.predictions.list', '预测列表', '/api/v2/ai/predictions', 'GET', 13, '获取AI预测列表'),
                ('ai.predictions.create', '创建预测', '/api/v2/ai/predictions', 'POST', 13, '创建AI预测任务'),
                ('ai.predictions.result', '预测结果', '/api/v2/ai/predictions/{id}/result', 'GET', 13, '获取预测结果'),
                
                ('ai.models.list', '模型列表', '/api/v2/ai/models', 'GET', 14, '获取AI模型列表'),
                ('ai.models.create', '创建模型', '/api/v2/ai/models', 'POST', 14, '创建AI模型'),
                ('ai.models.train', '训练模型', '/api/v2/ai/models/{id}/train', 'POST', 14, '训练AI模型'),
                ('ai.models.deploy', '部署模型', '/api/v2/ai/models/{id}/deploy', 'POST', 14, '部署AI模型'),
                
                ('ai.annotations.list', '标注列表', '/api/v2/ai/annotations', 'GET', 15, '获取数据标注列表'),
                ('ai.annotations.create', '创建标注', '/api/v2/ai/annotations', 'POST', 15, '创建数据标注'),
                ('ai.annotations.export', '导出标注', '/api/v2/ai/annotations/export', 'GET', 15, '导出标注数据'),
                
                ('ai.health.score', '健康评分', '/api/v2/ai/health/score', 'GET', 16, '获取设备健康评分'),
                ('ai.health.trend', '健康趋势', '/api/v2/ai/health/trend', 'GET', 16, '获取健康趋势'),
                ('ai.health.report', '健康报告', '/api/v2/ai/health/report', 'GET', 16, '获取健康报告'),
                
                ('ai.analysis.anomaly', '异常分析', '/api/v2/ai/analysis/anomaly', 'GET', 17, '异常检测分析'),
                ('ai.analysis.pattern', '模式分析', '/api/v2/ai/analysis/pattern', 'GET', 17, '模式识别分析'),
                ('ai.analysis.correlation', '关联分析', '/api/v2/ai/analysis/correlation', 'GET', 17, '关联性分析'),
                
                # 报警管理API
                ('alarms.list', '报警列表', '/api/v2/alarms', 'GET', 18, '获取报警列表'),
                ('alarms.create', '创建报警', '/api/v2/alarms', 'POST', 18, '创建报警规则'),
                ('alarms.update', '更新报警', '/api/v2/alarms/{id}', 'PUT', 18, '更新报警规则'),
                ('alarms.acknowledge', '确认报警', '/api/v2/alarms/{id}/acknowledge', 'POST', 18, '确认报警'),
                ('alarms.statistics', '报警统计', '/api/v2/alarms/statistics', 'GET', 18, '获取报警统计'),
                
                # 统计分析API
                ('statistics.overview', '概览统计', '/api/v2/statistics/overview', 'GET', 19, '获取概览统计'),
                ('statistics.devices', '设备统计', '/api/v2/statistics/devices', 'GET', 19, '获取设备统计'),
                ('statistics.performance', '性能统计', '/api/v2/statistics/performance', 'GET', 19, '获取性能统计'),
                ('statistics.usage', '使用统计', '/api/v2/statistics/usage', 'GET', 19, '获取使用统计'),
                ('statistics.export', '导出统计', '/api/v2/statistics/export', 'GET', 19, '导出统计数据'),
                
                # 仪表板API
                ('dashboard.overview', '仪表板概览', '/api/v2/dashboard/overview', 'GET', 20, '获取仪表板概览'),
                ('dashboard.widgets', '仪表板组件', '/api/v2/dashboard/widgets', 'GET', 20, '获取仪表板组件'),
                ('dashboard.config', '仪表板配置', '/api/v2/dashboard/config', 'GET', 20, '获取仪表板配置'),
                ('dashboard.update', '更新配置', '/api/v2/dashboard/config', 'PUT', 20, '更新仪表板配置')
            ]
            
            for api_code, api_name, api_path, http_method, group_id, description in standard_apis:
                await self.conn.execute("""
                    INSERT INTO t_sys_api_endpoints (api_code, api_name, api_path, http_method, 
                                                   group_id, description, permission_code, version, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, 'v2', 'active')
                    ON CONFLICT (api_code) DO UPDATE SET
                        api_name = EXCLUDED.api_name,
                        api_path = EXCLUDED.api_path,
                        http_method = EXCLUDED.http_method,
                        group_id = EXCLUDED.group_id,
                        description = EXCLUDED.description,
                        permission_code = EXCLUDED.permission_code,
                        updated_at = CURRENT_TIMESTAMP
                """, api_code, api_name, api_path, http_method, group_id, description, f"api:{api_code}")
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            api_count = await self.conn.fetchval("SELECT COUNT(*) FROM t_sys_api_endpoints")
            
            await self.update_migration_status(migration_id, 'success', '', execution_time)
            logger.info(f"✅ API端点数据迁移完成: {api_count} 条")
            return True
            
        except Exception as e:
            await self.update_migration_status(migration_id, 'failed', str(e))
            logger.error(f"❌ API端点数据迁移失败: {e}")
            return False
    
    async def migrate_permissions(self):
        """迁移权限数据"""
        logger.info("🔐 迁移权限数据...")
        
        try:
            migration_id = await self.log_migration(
                "migrate_permissions", 
                'permission', 
                'v2.0', 
                "创建标准权限数据并迁移现有权限"
            )
            
            start_time = datetime.now()
            
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
                    description,
                    CASE WHEN status = 'active' THEN '0' ELSE '1' END
                FROM t_sys_api_endpoints
                WHERE permission_code IS NOT NULL
                ON CONFLICT (permission_code) DO UPDATE SET
                    permission_name = EXCLUDED.permission_name,
                    description = EXCLUDED.description,
                    status = EXCLUDED.status,
                    updated_at = CURRENT_TIMESTAMP
            """)
            
            # 从菜单创建权限
            await self.conn.execute("""
                INSERT INTO t_sys_permission (permission_code, permission_name, permission_type, 
                                            resource_type, resource_id, description, status)
                SELECT 
                    perms,
                    menu_name,
                    'menu',
                    'menu',
                    id::text,
                    '菜单权限: ' || menu_name,
                    status
                FROM t_sys_menu
                WHERE perms IS NOT NULL AND perms != ''
                ON CONFLICT (permission_code) DO UPDATE SET
                    permission_name = EXCLUDED.permission_name,
                    description = EXCLUDED.description,
                    status = EXCLUDED.status,
                    updated_at = CURRENT_TIMESTAMP
            """)
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            permission_count = await self.conn.fetchval("SELECT COUNT(*) FROM t_sys_permission")
            
            await self.update_migration_status(migration_id, 'success', '', execution_time)
            logger.info(f"✅ 权限数据迁移完成: {permission_count} 条")
            return True
            
        except Exception as e:
            await self.update_migration_status(migration_id, 'failed', str(e))
            logger.error(f"❌ 权限数据迁移失败: {e}")
            return False
    
    async def create_foreign_keys(self):
        """创建外键约束"""
        logger.info("🔗 创建外键约束...")
        
        foreign_key_scripts = [
            "ALTER TABLE t_sys_user ADD CONSTRAINT fk_user_dept FOREIGN KEY (dept_id) REFERENCES t_sys_dept(id) ON DELETE SET NULL;",
            "ALTER TABLE t_sys_user_role ADD CONSTRAINT fk_user_role_user FOREIGN KEY (user_id) REFERENCES t_sys_user(id) ON DELETE CASCADE;",
            "ALTER TABLE t_sys_user_role ADD CONSTRAINT fk_user_role_role FOREIGN KEY (role_id) REFERENCES t_sys_role(id) ON DELETE CASCADE;",
            "ALTER TABLE t_sys_role_menu ADD CONSTRAINT fk_role_menu_role FOREIGN KEY (role_id) REFERENCES t_sys_role(id) ON DELETE CASCADE;",
            "ALTER TABLE t_sys_role_menu ADD CONSTRAINT fk_role_menu_menu FOREIGN KEY (menu_id) REFERENCES t_sys_menu(id) ON DELETE CASCADE;",
            "ALTER TABLE t_sys_api_endpoints ADD CONSTRAINT fk_api_endpoint_group FOREIGN KEY (group_id) REFERENCES t_sys_api_groups(id) ON DELETE RESTRICT;",
            "ALTER TABLE t_sys_role_permission ADD CONSTRAINT fk_role_permission_role FOREIGN KEY (role_id) REFERENCES t_sys_role(id) ON DELETE CASCADE;",
            "ALTER TABLE t_sys_role_permission ADD CONSTRAINT fk_role_permission_permission FOREIGN KEY (permission_id) REFERENCES t_sys_permission(id) ON DELETE CASCADE;",
            "ALTER TABLE t_sys_user_permission ADD CONSTRAINT fk_user_permission_user FOREIGN KEY (user_id) REFERENCES t_sys_user(id) ON DELETE CASCADE;",
            "ALTER TABLE t_sys_user_permission ADD CONSTRAINT fk_user_permission_permission FOREIGN KEY (permission_id) REFERENCES t_sys_permission(id) ON DELETE CASCADE;"
        ]
        
        success_count = 0
        for sql in foreign_key_scripts:
            try:
                await self.conn.execute(sql)
                success_count += 1
            except Exception as e:
                # 外键可能已存在，记录但不中断
                logger.warning(f"外键创建跳过: {sql} - {e}")
        
        logger.info(f"✅ 外键约束创建完成: {success_count}/{len(foreign_key_scripts)} 成功")
        return True
    
    async def generate_migration_report(self):
        """生成迁移报告"""
        logger.info("📊 生成迁移报告...")
        
        try:
            # 获取迁移统计
            migration_stats = await self.conn.fetch("""
                SELECT migration_type, status, COUNT(*) as count
                FROM t_sys_migration_logs
                WHERE created_at >= CURRENT_DATE
                GROUP BY migration_type, status
                ORDER BY migration_type, status
            """)
            
            # 获取表统计
            table_stats = await self.conn.fetch("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                  AND tablename LIKE 't_sys_%'
                ORDER BY tablename
            """)
            
            # 生成报告
            report = {
                'migration_batch': self.migration_batch,
                'generated_at': datetime.now().isoformat(),
                'migration_statistics': [dict(row) for row in migration_stats],
                'table_statistics': [dict(row) for row in table_stats],
                'summary': {
                    'total_migrations': len(migration_stats),
                    'successful_migrations': sum(row['count'] for row in migration_stats if row['status'] == 'success'),
                    'failed_migrations': sum(row['count'] for row in migration_stats if row['status'] == 'failed')
                }
            }
            
            # 保存报告
            report_file = f"migration_report_{self.migration_batch}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📋 迁移报告已生成: {report_file}")
            
            # 打印摘要
            print("\n" + "="*60)
            print("📊 迁移摘要报告")
            print("="*60)
            print(f"迁移批次: {self.migration_batch}")
            print(f"总迁移数: {report['summary']['total_migrations']}")
            print(f"成功迁移: {report['summary']['successful_migrations']}")
            print(f"失败迁移: {report['summary']['failed_migrations']}")
            print("="*60)
            
            return True
            
        except Exception as e:
            logger.error(f"生成迁移报告失败: {e}")
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
                logger.error("❌ 无法分析当前数据库架构")
                return False
            
            # 创建迁移日志表
            if not await self.create_migration_log_table():
                logger.error("❌ 无法创建迁移日志表")
                return False
            
            # 创建标准表结构
            if not await self.create_standard_tables():
                logger.error("❌ 表结构创建失败")
                return False
            
            # 创建索引
            if not await self.create_indexes():
                logger.error("❌ 索引创建失败")
                return False
            
            # 迁移现有数据
            if not await self.migrate_existing_data():
                logger.error("❌ 数据迁移失败")
                return False
            
            # 创建外键约束
            if not await self.create_foreign_keys():
                logger.error("❌ 外键约束创建失败")
                return False
            
            # 生成迁移报告
            if not await self.generate_migration_report():
                logger.error("❌ 迁移报告生成失败")
                return False
            
            logger.info("🎉 完整数据库迁移成功完成！")
            return True
            
        except Exception as e:
            logger.error(f"❌ 迁移过程中发生错误: {e}")
            logger.error(traceback.format_exc())
            return False
        
        finally:
            await self.disconnect()

async def main():
    """主函数"""
    migration_system = CompleteMigrationSystem()
    success = await migration_system.run_complete_migration()
    
    if success:
        print("\n🎉 数据库迁移成功完成！")
        sys.exit(0)
    else:
        print("\n❌ 数据库迁移失败！")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())