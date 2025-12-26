#!/usr/bin/env python3
"""
数据库迁移和版本控制系统
实现数据库迁移记录表、权限迁移映射表和版本控制机制
"""

import asyncio
import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncpg
from enum import Enum

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_migration_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MigrationStatus(Enum):
    """迁移状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class MigrationType(Enum):
    """迁移类型枚举"""
    SCHEMA = "schema"
    DATA = "data"
    PERMISSION = "permission"
    INDEX = "index"
    VIEW = "view"
    FUNCTION = "function"

@dataclass
class Migration:
    """迁移定义"""
    id: str
    name: str
    description: str
    version: str
    migration_type: MigrationType
    up_sql: str
    down_sql: str
    dependencies: List[str] = None
    checksum: str = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.checksum is None:
            self.checksum = self._calculate_checksum()
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def _calculate_checksum(self) -> str:
        """计算迁移脚本的校验和"""
        content = f"{self.up_sql}{self.down_sql}"
        return hashlib.sha256(content.encode()).hexdigest()

class DatabaseMigrationSystem:
    """数据库迁移和版本控制系统"""
    
    def __init__(self, db_url: str, migrations_dir: str = "database/migrations"):
        self.db_url = db_url
        self.migrations_dir = Path(migrations_dir)
        self.connection: Optional[asyncpg.Connection] = None
        self.migrations: Dict[str, Migration] = {}
        
        # 确保迁移目录存在
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
    
    async def connect(self):
        """连接数据库"""
        try:
            self.connection = await asyncpg.connect(self.db_url)
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    async def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            await self.connection.close()
            logger.info("数据库连接已关闭")
    
    async def initialize_migration_system(self):
        """初始化迁移系统"""
        logger.info("初始化数据库迁移系统...")
        
        # 创建迁移系统核心表
        await self._create_migration_tables()
        
        # 创建权限迁移相关表
        await self._create_permission_migration_tables()
        
        # 创建业务视图
        await self._create_business_views()
        
        # 创建迁移管理函数
        await self._create_migration_functions()
        
        logger.info("数据库迁移系统初始化完成")
    
    async def _create_migration_tables(self):
        """创建迁移系统核心表"""
        logger.info("创建迁移系统核心表...")
        
        # 1. 数据库迁移记录表
        migration_logs_sql = """
        CREATE TABLE IF NOT EXISTS t_sys_migration_logs (
            id BIGSERIAL PRIMARY KEY,
            migration_id VARCHAR(100) NOT NULL UNIQUE,
            migration_name VARCHAR(200) NOT NULL,
            migration_type VARCHAR(50) NOT NULL,
            version VARCHAR(20) NOT NULL,
            description TEXT,
            up_sql TEXT,
            down_sql TEXT,
            checksum VARCHAR(64) NOT NULL,
            dependencies JSONB DEFAULT '[]',
            status VARCHAR(20) DEFAULT 'pending',
            error_message TEXT,
            execution_time_ms INTEGER,
            executed_at TIMESTAMP NULL,
            rolled_back_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(100) DEFAULT 'system',
            
            CONSTRAINT chk_migration_status CHECK (status IN ('pending', 'running', 'success', 'failed', 'rolled_back')),
            CONSTRAINT chk_migration_type CHECK (migration_type IN ('schema', 'data', 'permission', 'index', 'view', 'function'))
        );
        
        -- 创建索引
        CREATE INDEX IF NOT EXISTS idx_migration_logs_migration_id ON t_sys_migration_logs(migration_id);
        CREATE INDEX IF NOT EXISTS idx_migration_logs_type ON t_sys_migration_logs(migration_type);
        CREATE INDEX IF NOT EXISTS idx_migration_logs_version ON t_sys_migration_logs(version);
        CREATE INDEX IF NOT EXISTS idx_migration_logs_status ON t_sys_migration_logs(status);
        CREATE INDEX IF NOT EXISTS idx_migration_logs_executed_at ON t_sys_migration_logs(executed_at);
        
        -- 添加表注释
        COMMENT ON TABLE t_sys_migration_logs IS '数据库迁移记录表';
        COMMENT ON COLUMN t_sys_migration_logs.migration_id IS '迁移唯一标识';
        COMMENT ON COLUMN t_sys_migration_logs.migration_name IS '迁移名称';
        COMMENT ON COLUMN t_sys_migration_logs.migration_type IS '迁移类型';
        COMMENT ON COLUMN t_sys_migration_logs.version IS '版本号';
        COMMENT ON COLUMN t_sys_migration_logs.up_sql IS '升级SQL脚本';
        COMMENT ON COLUMN t_sys_migration_logs.down_sql IS '回滚SQL脚本';
        COMMENT ON COLUMN t_sys_migration_logs.checksum IS 'SQL脚本校验和';
        COMMENT ON COLUMN t_sys_migration_logs.dependencies IS '依赖的迁移ID列表';
        COMMENT ON COLUMN t_sys_migration_logs.status IS '迁移状态';
        COMMENT ON COLUMN t_sys_migration_logs.execution_time_ms IS '执行时间(毫秒)';
        """
        
        # 2. 数据库版本控制表
        version_control_sql = """
        CREATE TABLE IF NOT EXISTS t_sys_database_versions (
            id BIGSERIAL PRIMARY KEY,
            version VARCHAR(20) NOT NULL UNIQUE,
            description TEXT,
            migration_count INTEGER DEFAULT 0,
            is_current BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            activated_at TIMESTAMP NULL,
            
            CONSTRAINT chk_only_one_current CHECK (
                NOT is_current OR (
                    SELECT COUNT(*) FROM t_sys_database_versions WHERE is_current = TRUE
                ) <= 1
            )
        );
        
        -- 创建索引
        CREATE INDEX IF NOT EXISTS idx_database_versions_version ON t_sys_database_versions(version);
        CREATE INDEX IF NOT EXISTS idx_database_versions_current ON t_sys_database_versions(is_current);
        
        -- 添加表注释
        COMMENT ON TABLE t_sys_database_versions IS '数据库版本控制表';
        COMMENT ON COLUMN t_sys_database_versions.version IS '版本号';
        COMMENT ON COLUMN t_sys_database_versions.migration_count IS '该版本包含的迁移数量';
        COMMENT ON COLUMN t_sys_database_versions.is_current IS '是否为当前版本';
        """
        
        await self.connection.execute(migration_logs_sql)
        await self.connection.execute(version_control_sql)
        
        logger.info("迁移系统核心表创建完成")
    
    async def _create_permission_migration_tables(self):
        """创建权限迁移相关表"""
        logger.info("创建权限迁移相关表...")
        
        # 权限迁移映射表
        permission_migrations_sql = """
        CREATE TABLE IF NOT EXISTS t_sys_permission_migrations (
            id BIGSERIAL PRIMARY KEY,
            old_permission VARCHAR(255) NOT NULL UNIQUE,
            new_permission VARCHAR(255) NOT NULL,
            api_path VARCHAR(500) NOT NULL,
            http_method VARCHAR(10) NOT NULL,
            api_group VARCHAR(100) NOT NULL,
            migration_type VARCHAR(20) NOT NULL DEFAULT 'auto',
            confidence_score DECIMAL(3,2) NOT NULL DEFAULT 0.0,
            migration_batch VARCHAR(50) NOT NULL,
            notes TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            migrated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            CONSTRAINT chk_confidence_score CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
            CONSTRAINT chk_migration_type CHECK (migration_type IN ('auto', 'manual', 'direct', 'inferred'))
        );
        
        -- 创建索引
        CREATE INDEX IF NOT EXISTS idx_permission_migrations_old ON t_sys_permission_migrations(old_permission);
        CREATE INDEX IF NOT EXISTS idx_permission_migrations_new ON t_sys_permission_migrations(new_permission);
        CREATE INDEX IF NOT EXISTS idx_permission_migrations_api_path ON t_sys_permission_migrations(api_path);
        CREATE INDEX IF NOT EXISTS idx_permission_migrations_method ON t_sys_permission_migrations(http_method);
        CREATE INDEX IF NOT EXISTS idx_permission_migrations_group ON t_sys_permission_migrations(api_group);
        CREATE INDEX IF NOT EXISTS idx_permission_migrations_batch ON t_sys_permission_migrations(migration_batch);
        CREATE INDEX IF NOT EXISTS idx_permission_migrations_confidence ON t_sys_permission_migrations(confidence_score);
        CREATE INDEX IF NOT EXISTS idx_permission_migrations_active ON t_sys_permission_migrations(is_active);
        
        -- 添加表注释
        COMMENT ON TABLE t_sys_permission_migrations IS '权限迁移映射表';
        COMMENT ON COLUMN t_sys_permission_migrations.old_permission IS '旧权限标识';
        COMMENT ON COLUMN t_sys_permission_migrations.new_permission IS '新权限标识';
        COMMENT ON COLUMN t_sys_permission_migrations.api_path IS 'API路径';
        COMMENT ON COLUMN t_sys_permission_migrations.http_method IS 'HTTP方法';
        COMMENT ON COLUMN t_sys_permission_migrations.api_group IS 'API分组';
        COMMENT ON COLUMN t_sys_permission_migrations.migration_type IS '迁移类型';
        COMMENT ON COLUMN t_sys_permission_migrations.confidence_score IS '置信度分数(0-1)';
        COMMENT ON COLUMN t_sys_permission_migrations.migration_batch IS '迁移批次';
        """
        
        # API分组表
        api_groups_sql = """
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
        
        -- 创建索引
        CREATE INDEX IF NOT EXISTS idx_api_groups_code ON t_sys_api_groups(group_code);
        CREATE INDEX IF NOT EXISTS idx_api_groups_parent ON t_sys_api_groups(parent_id);
        CREATE INDEX IF NOT EXISTS idx_api_groups_status ON t_sys_api_groups(status);
        CREATE INDEX IF NOT EXISTS idx_api_groups_sort ON t_sys_api_groups(sort_order);
        
        -- 添加表注释
        COMMENT ON TABLE t_sys_api_groups IS 'API分组表';
        COMMENT ON COLUMN t_sys_api_groups.group_code IS '分组编码';
        COMMENT ON COLUMN t_sys_api_groups.group_name IS '分组名称';
        COMMENT ON COLUMN t_sys_api_groups.parent_id IS '父分组ID';
        COMMENT ON COLUMN t_sys_api_groups.sort_order IS '排序顺序';
        """
        
        # API接口表
        api_endpoints_sql = """
        CREATE TABLE IF NOT EXISTS t_sys_api_endpoints (
            id BIGSERIAL PRIMARY KEY,
            api_code VARCHAR(100) NOT NULL UNIQUE,
            api_name VARCHAR(200) NOT NULL,
            api_path VARCHAR(500) NOT NULL,
            http_method VARCHAR(10) NOT NULL,
            group_id BIGINT NOT NULL,
            description TEXT,
            version VARCHAR(10) DEFAULT 'v2',
            is_public BOOLEAN DEFAULT FALSE,
            is_deprecated BOOLEAN DEFAULT FALSE,
            rate_limit INTEGER DEFAULT 0,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            CONSTRAINT fk_api_endpoints_group FOREIGN KEY (group_id) REFERENCES t_sys_api_groups(id),
            CONSTRAINT chk_api_endpoint_status CHECK (status IN ('active', 'inactive', 'deprecated')),
            CONSTRAINT chk_http_method CHECK (http_method IN ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'))
        );
        
        -- 创建唯一索引
        CREATE UNIQUE INDEX IF NOT EXISTS idx_api_endpoints_method_path ON t_sys_api_endpoints(http_method, api_path);
        
        -- 创建其他索引
        CREATE INDEX IF NOT EXISTS idx_api_endpoints_code ON t_sys_api_endpoints(api_code);
        CREATE INDEX IF NOT EXISTS idx_api_endpoints_group ON t_sys_api_endpoints(group_id);
        CREATE INDEX IF NOT EXISTS idx_api_endpoints_version ON t_sys_api_endpoints(version);
        CREATE INDEX IF NOT EXISTS idx_api_endpoints_status ON t_sys_api_endpoints(status);
        CREATE INDEX IF NOT EXISTS idx_api_endpoints_public ON t_sys_api_endpoints(is_public);
        
        -- 添加表注释
        COMMENT ON TABLE t_sys_api_endpoints IS 'API接口表';
        COMMENT ON COLUMN t_sys_api_endpoints.api_code IS 'API编码';
        COMMENT ON COLUMN t_sys_api_endpoints.api_name IS 'API名称';
        COMMENT ON COLUMN t_sys_api_endpoints.api_path IS 'API路径';
        COMMENT ON COLUMN t_sys_api_endpoints.http_method IS 'HTTP方法';
        COMMENT ON COLUMN t_sys_api_endpoints.group_id IS '所属分组ID';
        COMMENT ON COLUMN t_sys_api_endpoints.version IS 'API版本';
        COMMENT ON COLUMN t_sys_api_endpoints.is_public IS '是否公开API';
        COMMENT ON COLUMN t_sys_api_endpoints.is_deprecated IS '是否已废弃';
        COMMENT ON COLUMN t_sys_api_endpoints.rate_limit IS '速率限制(每分钟请求数)';
        """
        
        await self.connection.execute(permission_migrations_sql)
        await self.connection.execute(api_groups_sql)
        await self.connection.execute(api_endpoints_sql)
        
        # 插入默认API分组
        default_groups_sql = """
        INSERT INTO t_sys_api_groups (group_code, group_name, parent_id, description, sort_order) VALUES
        ('system', '系统管理', 0, '系统核心功能管理', 1),
        ('system.users', '用户管理', 1, '用户账户管理', 1),
        ('system.roles', '角色管理', 1, '角色权限管理', 2),
        ('system.menus', '菜单管理', 1, '菜单配置管理', 3),
        ('system.departments', '部门管理', 1, '组织架构管理', 4),
        ('device', '设备管理', 0, '设备信息和监控管理', 2),
        ('device.info', '设备信息', 6, '设备基础信息管理', 1),
        ('device.types', '设备类型', 6, '设备类型配置', 2),
        ('device.maintenance', '设备维护', 6, '设备维护记录', 3),
        ('device.processes', '工艺管理', 6, '设备工艺流程', 4),
        ('ai', 'AI监控', 0, 'AI预测和智能分析', 3),
        ('ai.predictions', 'AI预测', 11, '趋势预测功能', 1),
        ('ai.models', '模型管理', 11, 'AI模型管理', 2),
        ('ai.annotations', '数据标注', 11, '数据标注管理', 3),
        ('ai.health', '健康评分', 11, '设备健康评分', 4),
        ('statistics', '统计分析', 0, '数据统计和分析报告', 4),
        ('dashboard', '仪表板', 0, '概览和仪表板数据', 5),
        ('alarms', '报警管理', 0, '报警处理和统计', 6)
        ON CONFLICT (group_code) DO NOTHING;
        """
        
        await self.connection.execute(default_groups_sql)
        
        logger.info("权限迁移相关表创建完成")
    
    async def _create_business_views(self):
        """创建常用业务视图"""
        logger.info("创建常用业务视图...")
        
        # 1. 迁移状态概览视图
        migration_overview_view = """
        CREATE OR REPLACE VIEW v_migration_overview AS
        SELECT 
            version,
            COUNT(*) as total_migrations,
            COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_migrations,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_migrations,
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_migrations,
            COUNT(CASE WHEN status = 'rolled_back' THEN 1 END) as rolled_back_migrations,
            AVG(execution_time_ms) as avg_execution_time,
            MAX(executed_at) as last_migration_time
        FROM t_sys_migration_logs
        GROUP BY version
        ORDER BY version DESC;
        
        COMMENT ON VIEW v_migration_overview IS '迁移状态概览视图';
        """
        
        # 2. 权限迁移统计视图
        permission_migration_stats_view = """
        CREATE OR REPLACE VIEW v_permission_migration_stats AS
        SELECT 
            api_group,
            migration_type,
            COUNT(*) as total_mappings,
            AVG(confidence_score) as avg_confidence,
            COUNT(CASE WHEN confidence_score >= 0.9 THEN 1 END) as high_confidence_count,
            COUNT(CASE WHEN confidence_score >= 0.7 AND confidence_score < 0.9 THEN 1 END) as medium_confidence_count,
            COUNT(CASE WHEN confidence_score < 0.7 THEN 1 END) as low_confidence_count,
            COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active_mappings
        FROM t_sys_permission_migrations
        GROUP BY api_group, migration_type
        ORDER BY api_group, migration_type;
        
        COMMENT ON VIEW v_permission_migration_stats IS '权限迁移统计视图';
        """
        
        # 3. API分组层次视图
        api_group_hierarchy_view = """
        CREATE OR REPLACE VIEW v_api_group_hierarchy AS
        WITH RECURSIVE group_tree AS (
            -- 根节点
            SELECT 
                id, group_code, group_name, parent_id, description, sort_order, status,
                0 as level,
                group_code as path,
                ARRAY[id] as id_path
            FROM t_sys_api_groups 
            WHERE parent_id = 0
            
            UNION ALL
            
            -- 子节点
            SELECT 
                g.id, g.group_code, g.group_name, g.parent_id, g.description, g.sort_order, g.status,
                gt.level + 1,
                gt.path || '.' || g.group_code,
                gt.id_path || g.id
            FROM t_sys_api_groups g
            JOIN group_tree gt ON g.parent_id = gt.id
        )
        SELECT 
            id, group_code, group_name, parent_id, description, sort_order, status,
            level, path, id_path,
            (SELECT COUNT(*) FROM t_sys_api_endpoints WHERE group_id = group_tree.id) as api_count
        FROM group_tree
        ORDER BY path, sort_order;
        
        COMMENT ON VIEW v_api_group_hierarchy IS 'API分组层次结构视图';
        """
        
        # 4. API接口详情视图
        api_endpoint_details_view = """
        CREATE OR REPLACE VIEW v_api_endpoint_details AS
        SELECT 
            ae.id,
            ae.api_code,
            ae.api_name,
            ae.api_path,
            ae.http_method,
            ae.description,
            ae.version,
            ae.is_public,
            ae.is_deprecated,
            ae.rate_limit,
            ae.status,
            ag.group_code,
            ag.group_name,
            ag.parent_id as group_parent_id,
            (SELECT path FROM v_api_group_hierarchy WHERE id = ae.group_id) as group_path,
            ae.created_at,
            ae.updated_at
        FROM t_sys_api_endpoints ae
        JOIN t_sys_api_groups ag ON ae.group_id = ag.id
        ORDER BY ag.sort_order, ae.api_path;
        
        COMMENT ON VIEW v_api_endpoint_details IS 'API接口详情视图';
        """
        
        # 5. 迁移执行历史视图
        migration_execution_history_view = """
        CREATE OR REPLACE VIEW v_migration_execution_history AS
        SELECT 
            migration_id,
            migration_name,
            migration_type,
            version,
            status,
            execution_time_ms,
            executed_at,
            rolled_back_at,
            created_by,
            CASE 
                WHEN status = 'success' AND rolled_back_at IS NULL THEN '已完成'
                WHEN status = 'success' AND rolled_back_at IS NOT NULL THEN '已回滚'
                WHEN status = 'failed' THEN '执行失败'
                WHEN status = 'running' THEN '执行中'
                WHEN status = 'pending' THEN '等待执行'
                ELSE '未知状态'
            END as status_desc,
            CASE 
                WHEN execution_time_ms < 1000 THEN execution_time_ms || 'ms'
                WHEN execution_time_ms < 60000 THEN ROUND(execution_time_ms / 1000.0, 2) || 's'
                ELSE ROUND(execution_time_ms / 60000.0, 2) || 'min'
            END as execution_time_display
        FROM t_sys_migration_logs
        WHERE executed_at IS NOT NULL
        ORDER BY executed_at DESC;
        
        COMMENT ON VIEW v_migration_execution_history IS '迁移执行历史视图';
        """
        
        await self.connection.execute(migration_overview_view)
        await self.connection.execute(permission_migration_stats_view)
        await self.connection.execute(api_group_hierarchy_view)
        await self.connection.execute(api_endpoint_details_view)
        await self.connection.execute(migration_execution_history_view)
        
        logger.info("常用业务视图创建完成")
    
    async def _create_migration_functions(self):
        """创建迁移管理函数"""
        logger.info("创建迁移管理函数...")
        
        # 1. 获取当前数据库版本函数
        get_current_version_function = """
        CREATE OR REPLACE FUNCTION get_current_database_version()
        RETURNS VARCHAR AS $
        DECLARE
            current_ver VARCHAR;
        BEGIN
            SELECT version INTO current_ver
            FROM t_sys_database_versions
            WHERE is_current = TRUE;
            
            RETURN COALESCE(current_ver, '0.0.0');
        END;
        $ LANGUAGE plpgsql;
        
        COMMENT ON FUNCTION get_current_database_version() IS '获取当前数据库版本';
        """
        
        # 2. 检查迁移依赖函数
        check_migration_dependencies_function = """
        CREATE OR REPLACE FUNCTION check_migration_dependencies(migration_deps JSONB)
        RETURNS BOOLEAN AS $
        DECLARE
            dep_id VARCHAR;
            dep_status VARCHAR;
        BEGIN
            -- 如果没有依赖，直接返回true
            IF migration_deps IS NULL OR jsonb_array_length(migration_deps) = 0 THEN
                RETURN TRUE;
            END IF;
            
            -- 检查每个依赖是否已成功执行
            FOR dep_id IN SELECT jsonb_array_elements_text(migration_deps)
            LOOP
                SELECT status INTO dep_status
                FROM t_sys_migration_logs
                WHERE migration_id = dep_id;
                
                -- 如果依赖不存在或未成功执行，返回false
                IF dep_status IS NULL OR dep_status != 'success' THEN
                    RETURN FALSE;
                END IF;
            END LOOP;
            
            RETURN TRUE;
        END;
        $ LANGUAGE plpgsql;
        
        COMMENT ON FUNCTION check_migration_dependencies(JSONB) IS '检查迁移依赖是否满足';
        """
        
        # 3. 记录迁移执行函数
        record_migration_execution_function = """
        CREATE OR REPLACE FUNCTION record_migration_execution(
            p_migration_id VARCHAR,
            p_status VARCHAR,
            p_execution_time_ms INTEGER DEFAULT NULL,
            p_error_message TEXT DEFAULT NULL
        )
        RETURNS VOID AS $
        BEGIN
            UPDATE t_sys_migration_logs
            SET 
                status = p_status,
                execution_time_ms = COALESCE(p_execution_time_ms, execution_time_ms),
                error_message = p_error_message,
                executed_at = CASE WHEN p_status IN ('success', 'failed') THEN CURRENT_TIMESTAMP ELSE executed_at END
            WHERE migration_id = p_migration_id;
            
            -- 如果是成功状态，更新版本信息
            IF p_status = 'success' THEN
                UPDATE t_sys_database_versions
                SET migration_count = migration_count + 1
                WHERE version = (
                    SELECT version FROM t_sys_migration_logs WHERE migration_id = p_migration_id
                );
            END IF;
        END;
        $ LANGUAGE plpgsql;
        
        COMMENT ON FUNCTION record_migration_execution(VARCHAR, VARCHAR, INTEGER, TEXT) IS '记录迁移执行结果';
        """
        
        # 4. 获取待执行迁移函数
        get_pending_migrations_function = """
        CREATE OR REPLACE FUNCTION get_pending_migrations()
        RETURNS TABLE(
            migration_id VARCHAR,
            migration_name VARCHAR,
            migration_type VARCHAR,
            version VARCHAR,
            dependencies JSONB,
            can_execute BOOLEAN
        ) AS $
        BEGIN
            RETURN QUERY
            SELECT 
                ml.migration_id,
                ml.migration_name,
                ml.migration_type,
                ml.version,
                ml.dependencies,
                check_migration_dependencies(ml.dependencies) as can_execute
            FROM t_sys_migration_logs ml
            WHERE ml.status = 'pending'
            ORDER BY ml.version, ml.created_at;
        END;
        $ LANGUAGE plpgsql;
        
        COMMENT ON FUNCTION get_pending_migrations() IS '获取待执行的迁移列表';
        """
        
        # 5. 权限迁移验证函数
        validate_permission_migration_function = """
        CREATE OR REPLACE FUNCTION validate_permission_migration()
        RETURNS TABLE(
            validation_type VARCHAR,
            old_count BIGINT,
            new_count BIGINT,
            status VARCHAR,
            message TEXT
        ) AS $
        DECLARE
            old_api_count BIGINT;
            new_mapping_count BIGINT;
            high_confidence_count BIGINT;
            low_confidence_count BIGINT;
            active_mapping_count BIGINT;
        BEGIN
            -- 统计原有API数量
            SELECT COUNT(*) INTO old_api_count FROM api;
            
            -- 统计权限映射数量
            SELECT COUNT(*) INTO new_mapping_count FROM t_sys_permission_migrations;
            SELECT COUNT(*) INTO active_mapping_count FROM t_sys_permission_migrations WHERE is_active = TRUE;
            
            -- 统计置信度分布
            SELECT COUNT(*) INTO high_confidence_count 
            FROM t_sys_permission_migrations WHERE confidence_score >= 0.9;
            
            SELECT COUNT(*) INTO low_confidence_count 
            FROM t_sys_permission_migrations WHERE confidence_score < 0.7;
            
            -- 返回验证结果
            RETURN QUERY SELECT 
                'api_coverage'::VARCHAR,
                old_api_count,
                new_mapping_count,
                CASE WHEN old_api_count = new_mapping_count THEN 'PASS' ELSE 'WARN' END::VARCHAR,
                ('原有API: ' || old_api_count || ', 权限映射: ' || new_mapping_count)::TEXT;
            
            RETURN QUERY SELECT 
                'active_mappings'::VARCHAR,
                active_mapping_count,
                new_mapping_count,
                CASE WHEN active_mapping_count = new_mapping_count THEN 'PASS' ELSE 'WARN' END::VARCHAR,
                ('活跃映射: ' || active_mapping_count || ' / ' || new_mapping_count)::TEXT;
            
            RETURN QUERY SELECT 
                'high_confidence'::VARCHAR,
                high_confidence_count,
                0::BIGINT,
                'INFO'::VARCHAR,
                ('高置信度映射: ' || high_confidence_count)::TEXT;
            
            RETURN QUERY SELECT 
                'low_confidence'::VARCHAR,
                low_confidence_count,
                0::BIGINT,
                CASE WHEN low_confidence_count > 0 THEN 'WARN' ELSE 'PASS' END::VARCHAR,
                ('低置信度映射: ' || low_confidence_count || ' (需要人工检查)')::TEXT;
        END;
        $ LANGUAGE plpgsql;
        
        COMMENT ON FUNCTION validate_permission_migration() IS '验证权限迁移结果';
        """
        
        # 6. 更新时间触发器函数
        update_timestamp_function = """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $ LANGUAGE plpgsql;
        
        COMMENT ON FUNCTION update_updated_at_column() IS '自动更新updated_at字段的触发器函数';
        """
        
        await self.connection.execute(get_current_version_function)
        await self.connection.execute(check_migration_dependencies_function)
        await self.connection.execute(record_migration_execution_function)
        await self.connection.execute(get_pending_migrations_function)
        await self.connection.execute(validate_permission_migration_function)
        await self.connection.execute(update_timestamp_function)
        
        # 创建触发器
        triggers_sql = """
        -- 为相关表添加更新时间触发器
        DROP TRIGGER IF EXISTS update_permission_migrations_updated_at ON t_sys_permission_migrations;
        CREATE TRIGGER update_permission_migrations_updated_at 
            BEFORE UPDATE ON t_sys_permission_migrations
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        
        DROP TRIGGER IF EXISTS update_api_groups_updated_at ON t_sys_api_groups;
        CREATE TRIGGER update_api_groups_updated_at 
            BEFORE UPDATE ON t_sys_api_groups
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        
        DROP TRIGGER IF EXISTS update_api_endpoints_updated_at ON t_sys_api_endpoints;
        CREATE TRIGGER update_api_endpoints_updated_at 
            BEFORE UPDATE ON t_sys_api_endpoints
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
        
        await self.connection.execute(triggers_sql)
        
        logger.info("迁移管理函数创建完成")
    
    async def register_migration(self, migration: Migration) -> bool:
        """注册迁移"""
        try:
            # 检查迁移是否已存在
            existing = await self.connection.fetchval(
                "SELECT id FROM t_sys_migration_logs WHERE migration_id = $1",
                migration.id
            )
            
            if existing:
                logger.warning(f"迁移 {migration.id} 已存在")
                return False
            
            # 插入迁移记录
            await self.connection.execute("""
                INSERT INTO t_sys_migration_logs 
                (migration_id, migration_name, migration_type, version, description, 
                 up_sql, down_sql, checksum, dependencies, created_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, 
                migration.id,
                migration.name,
                migration.migration_type.value,
                migration.version,
                migration.description,
                migration.up_sql,
                migration.down_sql,
                migration.checksum,
                json.dumps(migration.dependencies),
                'system'
            )
            
            self.migrations[migration.id] = migration
            logger.info(f"迁移 {migration.id} 注册成功")
            return True
            
        except Exception as e:
            logger.error(f"注册迁移失败: {e}")
            return False
    
    async def execute_migration(self, migration_id: str) -> bool:
        """执行迁移"""
        try:
            # 获取迁移信息
            migration_info = await self.connection.fetchrow("""
                SELECT migration_id, migration_name, up_sql, dependencies, status
                FROM t_sys_migration_logs
                WHERE migration_id = $1
            """, migration_id)
            
            if not migration_info:
                logger.error(f"迁移 {migration_id} 不存在")
                return False
            
            if migration_info['status'] == 'success':
                logger.info(f"迁移 {migration_id} 已执行过")
                return True
            
            # 检查依赖
            dependencies = json.loads(migration_info['dependencies'] or '[]')
            if not await self._check_dependencies(dependencies):
                logger.error(f"迁移 {migration_id} 的依赖未满足")
                return False
            
            # 更新状态为运行中
            await self.connection.execute(
                "UPDATE t_sys_migration_logs SET status = 'running' WHERE migration_id = $1",
                migration_id
            )
            
            # 执行迁移SQL
            start_time = datetime.now()
            
            async with self.connection.transaction():
                await self.connection.execute(migration_info['up_sql'])
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # 更新状态为成功
            await self.connection.execute("""
                UPDATE t_sys_migration_logs 
                SET status = 'success', execution_time_ms = $2, executed_at = CURRENT_TIMESTAMP
                WHERE migration_id = $1
            """, migration_id, execution_time)
            
            logger.info(f"迁移 {migration_id} 执行成功，耗时: {execution_time}ms")
            return True
            
        except Exception as e:
            # 更新状态为失败
            await self.connection.execute("""
                UPDATE t_sys_migration_logs 
                SET status = 'failed', error_message = $2, executed_at = CURRENT_TIMESTAMP
                WHERE migration_id = $1
            """, migration_id, str(e))
            
            logger.error(f"迁移 {migration_id} 执行失败: {e}")
            return False
    
    async def rollback_migration(self, migration_id: str) -> bool:
        """回滚迁移"""
        try:
            # 获取迁移信息
            migration_info = await self.connection.fetchrow("""
                SELECT migration_id, migration_name, down_sql, status
                FROM t_sys_migration_logs
                WHERE migration_id = $1
            """, migration_id)
            
            if not migration_info:
                logger.error(f"迁移 {migration_id} 不存在")
                return False
            
            if migration_info['status'] != 'success':
                logger.error(f"迁移 {migration_id} 未成功执行，无法回滚")
                return False
            
            # 执行回滚SQL
            start_time = datetime.now()
            
            async with self.connection.transaction():
                await self.connection.execute(migration_info['down_sql'])
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # 更新状态为已回滚
            await self.connection.execute("""
                UPDATE t_sys_migration_logs 
                SET status = 'rolled_back', execution_time_ms = $2, rolled_back_at = CURRENT_TIMESTAMP
                WHERE migration_id = $1
            """, migration_id, execution_time)
            
            logger.info(f"迁移 {migration_id} 回滚成功，耗时: {execution_time}ms")
            return True
            
        except Exception as e:
            logger.error(f"迁移 {migration_id} 回滚失败: {e}")
            return False
    
    async def _check_dependencies(self, dependencies: List[str]) -> bool:
        """检查依赖是否满足"""
        if not dependencies:
            return True
        
        for dep_id in dependencies:
            status = await self.connection.fetchval(
                "SELECT status FROM t_sys_migration_logs WHERE migration_id = $1",
                dep_id
            )
            if status != 'success':
                return False
        
        return True
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """获取迁移状态"""
        stats = await self.connection.fetchrow("""
            SELECT 
                COUNT(*) as total_migrations,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as successful,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                COUNT(CASE WHEN status = 'rolled_back' THEN 1 END) as rolled_back
            FROM t_sys_migration_logs
        """)
        
        current_version = await self.connection.fetchval("SELECT get_current_database_version()")
        
        return {
            'current_version': current_version,
            'total_migrations': stats['total_migrations'],
            'successful': stats['successful'],
            'failed': stats['failed'],
            'pending': stats['pending'],
            'rolled_back': stats['rolled_back']
        }
    
    async def create_database_version(self, version: str, description: str = None) -> bool:
        """创建数据库版本"""
        try:
            await self.connection.execute("""
                INSERT INTO t_sys_database_versions (version, description)
                VALUES ($1, $2)
            """, version, description)
            
            logger.info(f"数据库版本 {version} 创建成功")
            return True
            
        except Exception as e:
            logger.error(f"创建数据库版本失败: {e}")
            return False
    
    async def set_current_version(self, version: str) -> bool:
        """设置当前数据库版本"""
        try:
            async with self.connection.transaction():
                # 清除当前版本标记
                await self.connection.execute(
                    "UPDATE t_sys_database_versions SET is_current = FALSE"
                )
                
                # 设置新的当前版本
                await self.connection.execute(
                    "UPDATE t_sys_database_versions SET is_current = TRUE, activated_at = CURRENT_TIMESTAMP WHERE version = $1",
                    version
                )
            
            logger.info(f"当前数据库版本设置为: {version}")
            return True
            
        except Exception as e:
            logger.error(f"设置当前版本失败: {e}")
            return False

# 使用示例
async def main():
    """主函数示例"""
    db_url = "postgresql://user:password@localhost:5432/database"
    
    migration_system = DatabaseMigrationSystem(db_url)
    
    try:
        await migration_system.connect()
        
        # 初始化迁移系统
        await migration_system.initialize_migration_system()
        
        # 创建数据库版本
        await migration_system.create_database_version("2.0.0", "API v2权限重构版本")
        await migration_system.set_current_version("2.0.0")
        
        # 获取迁移状态
        status = await migration_system.get_migration_status()
        print(f"迁移状态: {status}")
        
    except Exception as e:
        logger.error(f"迁移系统运行错误: {e}")
    finally:
        await migration_system.disconnect()

if __name__ == "__main__":
    asyncio.run(main())