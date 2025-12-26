#!/usr/bin/env python3
"""
完整的API权限重构数据库迁移
基于原始架构文档创建完整的表结构
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 设置环境变量
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

def print_banner():
    """打印横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║              🚀 完整API权限重构数据库迁移                    ║
║           Complete API Permission Refactor Migration        ║
╠══════════════════════════════════════════════════════════════╣
║  基于原始架构文档的完整迁移                                  ║
║  数据库: devicemonitor                                       ║
║  开始时间: {time}                           ║
╚══════════════════════════════════════════════════════════════╝
    """.format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print(banner)

async def test_database_connection():
    """测试数据库连接"""
    logger.info("测试数据库连接...")
    
    try:
        import asyncpg
        
        db_url = os.environ['DATABASE_URL']
        logger.info(f"连接到: {db_url.split('@')[1]}")
        
        conn = await asyncpg.connect(db_url)
        result = await conn.fetchval("SELECT version()")
        await conn.close()
        
        logger.info(f"数据库连接成功")
        logger.info(f"PostgreSQL版本: {result.split(',')[0]}")
        return True
        
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return Falseasy
nc def create_complete_schema():
    """创建完整的数据库架构"""
    logger.info("创建完整的数据库架构...")
    
    try:
        import asyncpg
        
        db_url = os.environ['DATABASE_URL']
        conn = await asyncpg.connect(db_url)
        
        # 1. 系统用户表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS t_sys_users (
                id BIGSERIAL PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(100) UNIQUE,
                phone VARCHAR(20),
                password_hash VARCHAR(255) NOT NULL,
                real_name VARCHAR(100),
                avatar_url VARCHAR(500),
                department_id BIGINT,
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'locked')),
                last_login_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by BIGINT,
                updated_by BIGINT
            );
            
            CREATE INDEX IF NOT EXISTS idx_sys_users_username ON t_sys_users(username);
            CREATE INDEX IF NOT EXISTS idx_sys_users_email ON t_sys_users(email);
            CREATE INDEX IF NOT EXISTS idx_sys_users_department_id ON t_sys_users(department_id);
            CREATE INDEX IF NOT EXISTS idx_sys_users_status ON t_sys_users(status);
            CREATE INDEX IF NOT EXISTS idx_sys_users_created_at ON t_sys_users(created_at);
            
            COMMENT ON TABLE t_sys_users IS '系统用户表';
        """)
        
        # 2. 系统角色表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS t_sys_roles (
                id BIGSERIAL PRIMARY KEY,
                role_code VARCHAR(50) NOT NULL UNIQUE,
                role_name VARCHAR(100) NOT NULL,
                description TEXT,
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by BIGINT,
                updated_by BIGINT
            );
            
            CREATE INDEX IF NOT EXISTS idx_sys_roles_role_code ON t_sys_roles(role_code);
            CREATE INDEX IF NOT EXISTS idx_sys_roles_status ON t_sys_roles(status);
            CREATE INDEX IF NOT EXISTS idx_sys_roles_sort_order ON t_sys_roles(sort_order);
            
            COMMENT ON TABLE t_sys_roles IS '系统角色表';
        """)
        
        # 3. 用户角色关联表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS t_sys_user_roles (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                role_id BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by BIGINT,
                
                UNIQUE(user_id, role_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_sys_user_roles_user_id ON t_sys_user_roles(user_id);
            CREATE INDEX IF NOT EXISTS idx_sys_user_roles_role_id ON t_sys_user_roles(role_id);
            
            COMMENT ON TABLE t_sys_user_roles IS '用户角色关联表';
        """)
        
        # 4. 系统部门表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS t_sys_departments (
                id BIGSERIAL PRIMARY KEY,
                dept_code VARCHAR(50) NOT NULL UNIQUE,
                dept_name VARCHAR(100) NOT NULL,
                parent_id BIGINT DEFAULT 0,
                leader_id BIGINT,
                phone VARCHAR(20),
                email VARCHAR(100),
                address TEXT,
                sort_order INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by BIGINT,
                updated_by BIGINT
            );
            
            CREATE INDEX IF NOT EXISTS idx_sys_departments_dept_code ON t_sys_departments(dept_code);
            CREATE INDEX IF NOT EXISTS idx_sys_departments_parent_id ON t_sys_departments(parent_id);
            CREATE INDEX IF NOT EXISTS idx_sys_departments_leader_id ON t_sys_departments(leader_id);
            CREATE INDEX IF NOT EXISTS idx_sys_departments_sort_order ON t_sys_departments(sort_order);
            
            COMMENT ON TABLE t_sys_departments IS '系统部门表';
        """)
        
        # 5. 系统菜单表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS t_sys_menus (
                id BIGSERIAL PRIMARY KEY,
                menu_code VARCHAR(50) NOT NULL UNIQUE,
                menu_name VARCHAR(100) NOT NULL,
                parent_id BIGINT DEFAULT 0,
                menu_type VARCHAR(20) DEFAULT 'menu' CHECK (menu_type IN ('directory', 'menu', 'button')),
                route_path VARCHAR(200),
                component_path VARCHAR(200),
                permission_code VARCHAR(100),
                icon VARCHAR(100),
                sort_order INTEGER DEFAULT 0,
                is_visible BOOLEAN DEFAULT TRUE,
                is_cached BOOLEAN DEFAULT FALSE,
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by BIGINT,
                updated_by BIGINT
            );
            
            CREATE INDEX IF NOT EXISTS idx_sys_menus_menu_code ON t_sys_menus(menu_code);
            CREATE INDEX IF NOT EXISTS idx_sys_menus_parent_id ON t_sys_menus(parent_id);
            CREATE INDEX IF NOT EXISTS idx_sys_menus_menu_type ON t_sys_menus(menu_type);
            CREATE INDEX IF NOT EXISTS idx_sys_menus_sort_order ON t_sys_menus(sort_order);
            
            COMMENT ON TABLE t_sys_menus IS '系统菜单表';
        """)
        
        logger.info("系统核心表创建完成")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"创建数据库架构失败: {e}")
        return Falseas
ync def create_api_tables():
    """创建API相关表"""
    logger.info("创建API相关表...")
    
    try:
        import asyncpg
        
        db_url = os.environ['DATABASE_URL']
        conn = await asyncpg.connect(db_url)
        
        # 6. API分组表 (更新现有表结构)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS t_sys_api_groups (
                id BIGSERIAL PRIMARY KEY,
                group_code VARCHAR(50) NOT NULL UNIQUE,
                group_name VARCHAR(100) NOT NULL,
                parent_id BIGINT DEFAULT 0,
                description TEXT,
                sort_order INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_sys_api_groups_group_code ON t_sys_api_groups(group_code);
            CREATE INDEX IF NOT EXISTS idx_sys_api_groups_parent_id ON t_sys_api_groups(parent_id);
            CREATE INDEX IF NOT EXISTS idx_sys_api_groups_sort_order ON t_sys_api_groups(sort_order);
            
            COMMENT ON TABLE t_sys_api_groups IS 'API分组表';
        """)
        
        # 7. API接口表 (更新现有表结构)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS t_sys_api_endpoints (
                id BIGSERIAL PRIMARY KEY,
                api_code VARCHAR(100) NOT NULL UNIQUE,
                api_name VARCHAR(200) NOT NULL,
                api_path VARCHAR(500) NOT NULL,
                http_method VARCHAR(10) NOT NULL CHECK (http_method IN ('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD')),
                group_id BIGINT NOT NULL,
                description TEXT,
                version VARCHAR(10) DEFAULT 'v2',
                is_public BOOLEAN DEFAULT FALSE,
                is_deprecated BOOLEAN DEFAULT FALSE,
                rate_limit INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'testing')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by BIGINT,
                updated_by BIGINT
            );
            
            CREATE UNIQUE INDEX IF NOT EXISTS uk_sys_api_endpoints_method_path ON t_sys_api_endpoints(http_method, api_path);
            CREATE INDEX IF NOT EXISTS idx_sys_api_endpoints_api_code ON t_sys_api_endpoints(api_code);
            CREATE INDEX IF NOT EXISTS idx_sys_api_endpoints_group_id ON t_sys_api_endpoints(group_id);
            CREATE INDEX IF NOT EXISTS idx_sys_api_endpoints_method ON t_sys_api_endpoints(http_method);
            CREATE INDEX IF NOT EXISTS idx_sys_api_endpoints_version ON t_sys_api_endpoints(version);
            CREATE INDEX IF NOT EXISTS idx_sys_api_endpoints_status ON t_sys_api_endpoints(status);
            
            COMMENT ON TABLE t_sys_api_endpoints IS 'API接口表';
        """)
        
        # 8. 角色权限关联表 (更新现有表结构)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS t_sys_role_permissions (
                id BIGSERIAL PRIMARY KEY,
                role_id BIGINT NOT NULL,
                api_id BIGINT NOT NULL,
                permission_type VARCHAR(10) DEFAULT 'allow' CHECK (permission_type IN ('allow', 'deny')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by BIGINT,
                
                UNIQUE(role_id, api_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_sys_role_permissions_role_id ON t_sys_role_permissions(role_id);
            CREATE INDEX IF NOT EXISTS idx_sys_role_permissions_api_id ON t_sys_role_permissions(api_id);
            
            COMMENT ON TABLE t_sys_role_permissions IS '角色权限关联表';
        """)
        
        # 9. 数据迁移记录表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS t_sys_migration_logs (
                id BIGSERIAL PRIMARY KEY,
                migration_name VARCHAR(200) NOT NULL,
                migration_type VARCHAR(20) NOT NULL CHECK (migration_type IN ('schema', 'data', 'permission', 'api')),
                version VARCHAR(20) NOT NULL,
                description TEXT,
                sql_content TEXT,
                rollback_sql TEXT,
                status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'success', 'failed', 'rolled_back')),
                error_message TEXT,
                execution_time_ms INTEGER,
                executed_at TIMESTAMP NULL,
                rolled_back_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by BIGINT
            );
            
            CREATE INDEX IF NOT EXISTS idx_sys_migration_logs_migration_type ON t_sys_migration_logs(migration_type);
            CREATE INDEX IF NOT EXISTS idx_sys_migration_logs_version ON t_sys_migration_logs(version);
            CREATE INDEX IF NOT EXISTS idx_sys_migration_logs_status ON t_sys_migration_logs(status);
            CREATE INDEX IF NOT EXISTS idx_sys_migration_logs_executed_at ON t_sys_migration_logs(executed_at);
            
            COMMENT ON TABLE t_sys_migration_logs IS '数据迁移记录表';
        """)
        
        # 10. 权限迁移映射表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS t_sys_permission_migrations (
                id BIGSERIAL PRIMARY KEY,
                old_permission VARCHAR(255) NOT NULL UNIQUE,
                new_permission VARCHAR(255) NOT NULL,
                migration_batch VARCHAR(50) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                migrated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_sys_permission_migrations_new_permission ON t_sys_permission_migrations(new_permission);
            CREATE INDEX IF NOT EXISTS idx_sys_permission_migrations_migration_batch ON t_sys_permission_migrations(migration_batch);
            
            COMMENT ON TABLE t_sys_permission_migrations IS '权限迁移映射表';
        """)
        
        logger.info("API相关表创建完成")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"创建API表失败: {e}")
        return Falsea
sync def create_device_tables():
    """创建设备管理相关表"""
    logger.info("创建设备管理相关表...")
    
    try:
        import asyncpg
        
        db_url = os.environ['DATABASE_URL']
        conn = await asyncpg.connect(db_url)
        
        # 11. 设备类型表 (更新现有表结构)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS t_device_types (
                id BIGSERIAL PRIMARY KEY,
                type_code VARCHAR(50) NOT NULL UNIQUE,
                type_name VARCHAR(100) NOT NULL,
                description TEXT,
                manufacturer VARCHAR(100),
                model_series VARCHAR(100),
                specifications JSONB,
                sort_order INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by BIGINT,
                updated_by BIGINT
            );
            
            CREATE INDEX IF NOT EXISTS idx_device_types_type_code ON t_device_types(type_code);
            CREATE INDEX IF NOT EXISTS idx_device_types_manufacturer ON t_device_types(manufacturer);
            CREATE INDEX IF NOT EXISTS idx_device_types_status ON t_device_types(status);
            
            COMMENT ON TABLE t_device_types IS '设备类型表';
        """)
        
        # 12. 设备资产表 (更新现有表结构)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS t_device_assets (
                id BIGSERIAL PRIMARY KEY,
                device_code VARCHAR(50) NOT NULL UNIQUE,
                device_name VARCHAR(200) NOT NULL,
                type_id BIGINT NOT NULL,
                manufacturer VARCHAR(100),
                model VARCHAR(100),
                serial_number VARCHAR(100),
                purchase_date DATE,
                warranty_date DATE,
                location VARCHAR(200),
                department_id BIGINT,
                responsible_user_id BIGINT,
                ip_address INET,
                mac_address MACADDR,
                status VARCHAR(20) DEFAULT 'offline' CHECK (status IN ('online', 'offline', 'maintenance', 'fault', 'retired')),
                health_score DECIMAL(5,2) DEFAULT 100.00,
                last_maintenance_at TIMESTAMP NULL,
                next_maintenance_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by BIGINT,
                updated_by BIGINT
            );
            
            CREATE INDEX IF NOT EXISTS idx_device_assets_device_code ON t_device_assets(device_code);
            CREATE INDEX IF NOT EXISTS idx_device_assets_type_id ON t_device_assets(type_id);
            CREATE INDEX IF NOT EXISTS idx_device_assets_department_id ON t_device_assets(department_id);
            CREATE INDEX IF NOT EXISTS idx_device_assets_responsible_user_id ON t_device_assets(responsible_user_id);
            CREATE INDEX IF NOT EXISTS idx_device_assets_status ON t_device_assets(status);
            CREATE INDEX IF NOT EXISTS idx_device_assets_ip_address ON t_device_assets(ip_address);
            
            COMMENT ON TABLE t_device_assets IS '设备资产表';
        """)
        
        # 13. 设备维护记录表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS t_device_maintenance_records (
                id BIGSERIAL PRIMARY KEY,
                device_id BIGINT NOT NULL,
                maintenance_type VARCHAR(20) NOT NULL CHECK (maintenance_type IN ('routine', 'repair', 'upgrade', 'inspection')),
                title VARCHAR(200) NOT NULL,
                description TEXT,
                maintenance_date TIMESTAMP NOT NULL,
                duration_minutes INTEGER,
                technician_id BIGINT,
                cost DECIMAL(10,2),
                parts_used JSONB,
                status VARCHAR(20) DEFAULT 'planned' CHECK (status IN ('planned', 'in_progress', 'completed', 'cancelled')),
                result VARCHAR(20) CHECK (result IN ('success', 'partial', 'failed')),
                notes TEXT,
                attachments JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by BIGINT,
                updated_by BIGINT
            );
            
            CREATE INDEX IF NOT EXISTS idx_device_maintenance_records_device_id ON t_device_maintenance_records(device_id);
            CREATE INDEX IF NOT EXISTS idx_device_maintenance_records_maintenance_type ON t_device_maintenance_records(maintenance_type);
            CREATE INDEX IF NOT EXISTS idx_device_maintenance_records_maintenance_date ON t_device_maintenance_records(maintenance_date);
            CREATE INDEX IF NOT EXISTS idx_device_maintenance_records_technician_id ON t_device_maintenance_records(technician_id);
            CREATE INDEX IF NOT EXISTS idx_device_maintenance_records_status ON t_device_maintenance_records(status);
            
            COMMENT ON TABLE t_device_maintenance_records IS '设备维护记录表';
        """)
        
        logger.info("设备管理相关表创建完成")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"创建设备表失败: {e}")
        return Falseasync d
ef insert_initial_data():
    """插入初始化数据"""
    logger.info("插入初始化数据...")
    
    try:
        import asyncpg
        
        db_url = os.environ['DATABASE_URL']
        conn = await asyncpg.connect(db_url)
        
        # 插入默认API分组
        await conn.execute("""
            INSERT INTO t_sys_api_groups (group_code, group_name, parent_id, description, sort_order) VALUES
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
            ON CONFLICT (group_code) DO UPDATE SET
                group_name = EXCLUDED.group_name,
                description = EXCLUDED.description,
                sort_order = EXCLUDED.sort_order;
        """)
        
        # 插入默认角色
        await conn.execute("""
            INSERT INTO t_sys_roles (role_code, role_name, description, status, sort_order) VALUES
            ('super_admin', '超级管理员', '系统超级管理员，拥有所有权限', 'active', 1),
            ('admin', '系统管理员', '系统管理员，拥有大部分管理权限', 'active', 2),
            ('user', '普通用户', '普通用户，拥有基础功能权限', 'active', 3)
            ON CONFLICT (role_code) DO UPDATE SET
                role_name = EXCLUDED.role_name,
                description = EXCLUDED.description;
        """)
        
        # 插入默认部门
        await conn.execute("""
            INSERT INTO t_sys_departments (dept_code, dept_name, parent_id, description, sort_order) VALUES
            ('root', '根部门', 0, '系统根部门', 1),
            ('tech', '技术部', 1, '技术开发部门', 1),
            ('ops', '运维部', 1, '系统运维部门', 2),
            ('business', '业务部', 1, '业务管理部门', 3)
            ON CONFLICT (dept_code) DO UPDATE SET
                dept_name = EXCLUDED.dept_name,
                description = EXCLUDED.description;
        """)
        
        logger.info("初始化数据插入完成")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"插入初始化数据失败: {e}")
        return False

async def migrate_existing_data():
    """迁移现有数据"""
    logger.info("迁移现有数据...")
    
    try:
        import asyncpg
        
        db_url = os.environ['DATABASE_URL']
        conn = await asyncpg.connect(db_url)
        
        # 检查并迁移API数据
        api_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'api'
            )
        """)
        
        if api_exists:
            # 获取源表数据
            source_data = await conn.fetch("SELECT * FROM api")
            logger.info(f"找到 {len(source_data)} 条API记录")
            
            migrated_count = 0
            for record in source_data:
                try:
                    # 根据实际的源表结构调整字段映射
                    api_code = record.get('code', f"api_{record.get('id', migrated_count)}")
                    api_name = record.get('name', record.get('title', f"API {record.get('id', migrated_count)}"))
                    api_path = record.get('path', record.get('url', f"/api/unknown/{record.get('id', migrated_count)}"))
                    http_method = record.get('method', 'GET').upper()
                    description = record.get('description', record.get('desc', ''))
                    
                    # 根据API路径确定分组
                    group_id = 1  # 默认分组
                    if '/user' in api_path or '/users' in api_path:
                        group_id = 2  # 用户管理
                    elif '/role' in api_path or '/roles' in api_path:
                        group_id = 3  # 角色管理
                    elif '/device' in api_path:
                        group_id = 7  # 设备管理
                    elif '/ai' in api_path:
                        group_id = 12  # AI监控
                    
                    await conn.execute("""
                        INSERT INTO t_sys_api_endpoints 
                        (api_code, api_name, api_path, http_method, group_id, description, version, status)
                        VALUES ($1, $2, $3, $4, $5, $6, 'v2', 'active')
                        ON CONFLICT (api_code) DO UPDATE SET
                            api_name = EXCLUDED.api_name,
                            api_path = EXCLUDED.api_path,
                            http_method = EXCLUDED.http_method,
                            group_id = EXCLUDED.group_id,
                            description = EXCLUDED.description,
                            updated_at = CURRENT_TIMESTAMP
                    """, api_code, api_name, api_path, http_method, group_id, description)
                    
                    migrated_count += 1
                    
                except Exception as e:
                    logger.warning(f"迁移记录失败: {e}")
                    continue
            
            logger.info(f"成功迁移 {migrated_count} 条API记录")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"迁移现有数据失败: {e}")
        return Falseasync def c
reate_views():
    """创建常用视图"""
    logger.info("创建常用视图...")
    
    try:
        import asyncpg
        
        db_url = os.environ['DATABASE_URL']
        conn = await asyncpg.connect(db_url)
        
        # 用户权限汇总视图
        await conn.execute("""
            CREATE OR REPLACE VIEW v_user_permissions AS
            SELECT 
                u.id as user_id,
                u.username,
                u.real_name,
                r.role_code,
                r.role_name,
                ae.api_path,
                ae.http_method,
                ae.api_name,
                ag.group_name as api_group
            FROM t_sys_users u
            JOIN t_sys_user_roles ur ON u.id = ur.user_id
            JOIN t_sys_roles r ON ur.role_id = r.id
            JOIN t_sys_role_permissions rp ON r.id = rp.role_id
            JOIN t_sys_api_endpoints ae ON rp.api_id = ae.id
            JOIN t_sys_api_groups ag ON ae.group_id = ag.id
            WHERE u.status = 'active' 
              AND r.status = 'active' 
              AND ae.status = 'active'
              AND rp.permission_type = 'allow';
        """)
        
        # 设备状态统计视图
        await conn.execute("""
            CREATE OR REPLACE VIEW v_device_status_summary AS
            SELECT 
                dt.type_name,
                da.status,
                COUNT(*) as device_count,
                AVG(da.health_score) as avg_health_score
            FROM t_device_assets da
            JOIN t_device_types dt ON da.type_id = dt.id
            GROUP BY dt.type_name, da.status;
        """)
        
        # 部门用户统计视图
        await conn.execute("""
            CREATE OR REPLACE VIEW v_department_user_stats AS
            SELECT 
                d.dept_code,
                d.dept_name,
                COUNT(u.id) as user_count,
                COUNT(CASE WHEN u.status = 'active' THEN 1 END) as active_user_count,
                COUNT(CASE WHEN u.last_login_at > CURRENT_TIMESTAMP - INTERVAL '30 days' THEN 1 END) as recent_login_count
            FROM t_sys_departments d
            LEFT JOIN t_sys_users u ON d.id = u.department_id
            WHERE d.status = 'active'
            GROUP BY d.id, d.dept_code, d.dept_name;
        """)
        
        logger.info("常用视图创建完成")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"创建视图失败: {e}")
        return False

async def verify_complete_migration():
    """验证完整迁移结果"""
    logger.info("验证完整迁移结果...")
    
    try:
        import asyncpg
        
        db_url = os.environ['DATABASE_URL']
        conn = await asyncpg.connect(db_url)
        
        # 检查所有表
        tables = await conn.fetch("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_name = t.table_name AND table_schema = 'public') as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public' 
            AND table_name LIKE 't_sys_%' OR table_name LIKE 't_device_%'
            ORDER BY table_name
        """)
        
        logger.info("完整表结构验证:")
        for table in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table['table_name']}")
            logger.info(f"   - {table['table_name']}: {table['column_count']} 列, {count} 条记录")
        
        # 检查视图
        views = await conn.fetch("""
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = 'public' 
            AND table_name LIKE 'v_%'
            ORDER BY table_name
        """)
        
        logger.info("视图验证:")
        for view in views:
            logger.info(f"   - {view['table_name']}: 视图已创建")
        
        await conn.close()
        logger.info("完整迁移验证完成")
        return True
        
    except Exception as e:
        logger.error(f"验证完整迁移失败: {e}")
        return False

async def main():
    """主函数"""
    print_banner()
    
    try:
        # 1. 测试数据库连接
        if not await test_database_connection():
            logger.error("数据库连接失败，迁移终止")
            return False
        
        # 2. 创建完整的数据库架构
        if not await create_complete_schema():
            logger.error("创建系统核心表失败，迁移终止")
            return False
        
        # 3. 创建API相关表
        if not await create_api_tables():
            logger.error("创建API表失败，迁移终止")
            return False
        
        # 4. 创建设备管理表
        if not await create_device_tables():
            logger.error("创建设备表失败，迁移终止")
            return False
        
        # 5. 插入初始化数据
        if not await insert_initial_data():
            logger.error("插入初始化数据失败")
            return False
        
        # 6. 迁移现有数据
        if not await migrate_existing_data():
            logger.error("迁移现有数据失败")
            return False
        
        # 7. 创建视图
        if not await create_views():
            logger.error("创建视图失败")
            return False
        
        # 8. 验证迁移结果
        if not await verify_complete_migration():
            logger.error("迁移验证失败")
            return False
        
        # 9. 完成
        print("\n" + "=" * 60)
        print("🎉 完整API权限重构数据库迁移执行成功！")
        print("=" * 60)
        print("\n📋 迁移完成:")
        print("✅ 系统核心表已创建 (用户、角色、部门、菜单)")
        print("✅ API管理表已创建 (分组、接口、权限)")
        print("✅ 设备管理表已创建 (类型、资产、维护)")
        print("✅ 迁移记录表已创建")
        print("✅ 初始化数据已插入")
        print("✅ 现有数据已迁移")
        print("✅ 常用视图已创建")
        print("✅ 迁移结果已验证")
        print("\n📄 日志文件: complete_migration.log")
        print("🎊 恭喜完成完整的API权限重构迁移！")
        
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断执行")
        return False
    except Exception as e:
        logger.error(f"执行过程中发生错误: {e}")
        print(f"\n💥 执行失败: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)