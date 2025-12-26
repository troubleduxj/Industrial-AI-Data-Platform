#!/usr/bin/env python3
"""
数据库迁移自动化脚本
实现迁移执行和回滚的自动化管理
"""

import asyncio
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from migration_system import DatabaseMigrationSystem, Migration, MigrationType

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MigrationAutomation:
    """迁移自动化管理器"""
    
    def __init__(self, db_url: str, migrations_dir: str = "database/migrations"):
        self.migration_system = DatabaseMigrationSystem(db_url, migrations_dir)
        self.migrations_dir = Path(migrations_dir)
        self.predefined_migrations = []
        
        # 确保迁移目录存在
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化预定义迁移
        self._init_predefined_migrations()
    
    def _init_predefined_migrations(self):
        """初始化预定义迁移"""
        self.predefined_migrations = [
            # 1. 表结构标准化迁移
            Migration(
                id="001_standardize_table_names",
                name="标准化表名",
                description="将现有表名标准化为t_前缀格式",
                version="2.0.0",
                migration_type=MigrationType.SCHEMA,
                up_sql=self._get_table_standardization_sql(),
                down_sql=self._get_table_standardization_rollback_sql(),
                dependencies=[]
            ),
            
            # 2. 创建API分组数据迁移
            Migration(
                id="002_migrate_api_groups",
                name="迁移API分组数据",
                description="将现有API数据迁移到新的分组结构",
                version="2.0.0",
                migration_type=MigrationType.DATA,
                up_sql=self._get_api_groups_migration_sql(),
                down_sql=self._get_api_groups_rollback_sql(),
                dependencies=["001_standardize_table_names"]
            ),
            
            # 3. 权限数据迁移
            Migration(
                id="003_migrate_permissions",
                name="迁移权限数据",
                description="将v1权限数据迁移到v2格式",
                version="2.0.0",
                migration_type=MigrationType.PERMISSION,
                up_sql=self._get_permission_migration_sql(),
                down_sql=self._get_permission_rollback_sql(),
                dependencies=["002_migrate_api_groups"]
            ),
            
            # 4. 创建性能优化索引
            Migration(
                id="004_create_performance_indexes",
                name="创建性能优化索引",
                description="为权限查询创建优化索引",
                version="2.0.0",
                migration_type=MigrationType.INDEX,
                up_sql=self._get_performance_indexes_sql(),
                down_sql=self._get_performance_indexes_rollback_sql(),
                dependencies=["003_migrate_permissions"]
            ),
            
            # 5. 创建业务视图
            Migration(
                id="005_create_business_views",
                name="创建业务视图",
                description="创建常用的业务查询视图",
                version="2.0.0",
                migration_type=MigrationType.VIEW,
                up_sql=self._get_business_views_sql(),
                down_sql=self._get_business_views_rollback_sql(),
                dependencies=["004_create_performance_indexes"]
            ),
            
            # 6. 创建权限验证函数
            Migration(
                id="006_create_permission_functions",
                name="创建权限验证函数",
                description="创建v2权限验证相关函数",
                version="2.0.0",
                migration_type=MigrationType.FUNCTION,
                up_sql=self._get_permission_functions_sql(),
                down_sql=self._get_permission_functions_rollback_sql(),
                dependencies=["005_create_business_views"]
            )
        ]
    
    def _get_table_standardization_sql(self) -> str:
        """获取表结构标准化SQL"""
        return """
        -- 表结构标准化迁移
        -- 注意: 这里只是示例，实际实现需要根据具体的表结构调整
        
        -- 1. 重命名现有表为标准格式
        DO $$ 
        BEGIN
            -- 检查表是否存在，如果存在则重命名
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user') THEN
                ALTER TABLE "user" RENAME TO t_sys_users;
            END IF;
            
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'role') THEN
                ALTER TABLE "role" RENAME TO t_sys_roles;
            END IF;
            
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'api') THEN
                ALTER TABLE "api" RENAME TO t_sys_apis_old;
            END IF;
            
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'menu') THEN
                ALTER TABLE "menu" RENAME TO t_sys_menus;
            END IF;
            
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'dept') THEN
                ALTER TABLE "dept" RENAME TO t_sys_departments;
            END IF;
            
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'dept_closure') THEN
                ALTER TABLE "dept_closure" RENAME TO t_sys_department_closure;
            END IF;
            
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'auditlog') THEN
                ALTER TABLE "auditlog" RENAME TO t_sys_audit_logs;
            END IF;
        END $$;
        
        -- 2. 更新外键约束名称
        DO $$
        DECLARE
            constraint_record RECORD;
        BEGIN
            -- 更新外键约束以匹配新表名
            FOR constraint_record IN 
                SELECT constraint_name, table_name 
                FROM information_schema.table_constraints 
                WHERE constraint_type = 'FOREIGN KEY'
                AND table_name LIKE 't_sys_%'
            LOOP
                -- 这里需要根据实际情况调整外键约束
                -- 示例代码，实际需要更详细的处理
                NULL;
            END LOOP;
        END $$;
        
        -- 3. 记录迁移日志
        INSERT INTO t_sys_migration_logs (migration_id, migration_name, migration_type, version, description, status)
        VALUES ('001_standardize_table_names', '标准化表名', 'schema', '2.0.0', '表结构标准化完成', 'success')
        ON CONFLICT (migration_id) DO NOTHING;
        """
    
    def _get_table_standardization_rollback_sql(self) -> str:
        """获取表结构标准化回滚SQL"""
        return """
        -- 表结构标准化回滚
        DO $$ 
        BEGIN
            -- 恢复原始表名
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 't_sys_users') THEN
                ALTER TABLE t_sys_users RENAME TO "user";
            END IF;
            
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 't_sys_roles') THEN
                ALTER TABLE t_sys_roles RENAME TO "role";
            END IF;
            
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 't_sys_apis_old') THEN
                ALTER TABLE t_sys_apis_old RENAME TO "api";
            END IF;
            
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 't_sys_menus') THEN
                ALTER TABLE t_sys_menus RENAME TO "menu";
            END IF;
            
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 't_sys_departments') THEN
                ALTER TABLE t_sys_departments RENAME TO "dept";
            END IF;
            
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 't_sys_department_closure') THEN
                ALTER TABLE t_sys_department_closure RENAME TO "dept_closure";
            END IF;
            
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 't_sys_audit_logs') THEN
                ALTER TABLE t_sys_audit_logs RENAME TO "auditlog";
            END IF;
        END $$;
        """
    
    def _get_api_groups_migration_sql(self) -> str:
        """获取API分组迁移SQL"""
        return """
        -- API分组数据迁移
        
        -- 1. 从现有API数据中提取分组信息并插入到新表
        INSERT INTO t_sys_api_endpoints (api_code, api_name, api_path, http_method, group_id, description, version)
        SELECT 
            LOWER(REPLACE(CONCAT(method, '_', path), '/', '_')) as api_code,
            COALESCE(summary, CONCAT(method, ' ', path)) as api_name,
            CASE 
                WHEN path LIKE '/user/%' THEN REPLACE(path, '/user/', '/api/v2/users/')
                WHEN path LIKE '/role/%' THEN REPLACE(path, '/role/', '/api/v2/roles/')
                WHEN path LIKE '/menu/%' THEN REPLACE(path, '/menu/', '/api/v2/menus/')
                WHEN path LIKE '/dept/%' THEN REPLACE(path, '/dept/', '/api/v2/departments/')
                WHEN path LIKE '/device/%' THEN REPLACE(path, '/device/', '/api/v2/devices/')
                ELSE CONCAT('/api/v2', path)
            END as api_path,
            method as http_method,
            CASE 
                WHEN path LIKE '/user/%' THEN (SELECT id FROM t_sys_api_groups WHERE group_code = 'system.users')
                WHEN path LIKE '/role/%' THEN (SELECT id FROM t_sys_api_groups WHERE group_code = 'system.roles')
                WHEN path LIKE '/menu/%' THEN (SELECT id FROM t_sys_api_groups WHERE group_code = 'system.menus')
                WHEN path LIKE '/dept/%' THEN (SELECT id FROM t_sys_api_groups WHERE group_code = 'system.departments')
                WHEN path LIKE '/device/%' THEN (SELECT id FROM t_sys_api_groups WHERE group_code = 'device.info')
                ELSE (SELECT id FROM t_sys_api_groups WHERE group_code = 'system')
            END as group_id,
            summary as description,
            'v2' as version
        FROM t_sys_apis_old
        WHERE NOT EXISTS (
            SELECT 1 FROM t_sys_api_endpoints 
            WHERE api_code = LOWER(REPLACE(CONCAT(t_sys_apis_old.method, '_', t_sys_apis_old.path), '/', '_'))
        );
        
        -- 2. 记录迁移统计
        INSERT INTO t_sys_migration_logs (migration_id, migration_name, migration_type, version, description, status)
        VALUES ('002_migrate_api_groups', 'API分组数据迁移', 'data', '2.0.0', 
                CONCAT('迁移了 ', (SELECT COUNT(*) FROM t_sys_api_endpoints), ' 个API接口'), 'success')
        ON CONFLICT (migration_id) DO NOTHING;
        """
    
    def _get_api_groups_rollback_sql(self) -> str:
        """获取API分组回滚SQL"""
        return """
        -- API分组数据回滚
        DELETE FROM t_sys_api_endpoints WHERE version = 'v2';
        """
    
    def _get_permission_migration_sql(self) -> str:
        """获取权限迁移SQL"""
        return """
        -- 权限数据迁移
        
        -- 1. 创建权限映射数据
        INSERT INTO t_sys_permission_migrations (
            old_permission, new_permission, api_path, http_method, api_group, 
            migration_type, confidence_score, migration_batch, notes
        )
        SELECT 
            CONCAT(a.method, ' ', a.path) as old_permission,
            CONCAT(ae.http_method, ' ', ae.api_path) as new_permission,
            ae.api_path,
            ae.http_method,
            ag.group_name as api_group,
            'auto' as migration_type,
            0.9 as confidence_score,
            'batch_001' as migration_batch,
            CONCAT('从 ', a.path, ' 迁移到 ', ae.api_path) as notes
        FROM t_sys_apis_old a
        JOIN t_sys_api_endpoints ae ON LOWER(REPLACE(CONCAT(a.method, '_', a.path), '/', '_')) = ae.api_code
        JOIN t_sys_api_groups ag ON ae.group_id = ag.id
        WHERE NOT EXISTS (
            SELECT 1 FROM t_sys_permission_migrations 
            WHERE old_permission = CONCAT(a.method, ' ', a.path)
        );
        
        -- 2. 创建新的角色权限关联表
        CREATE TABLE IF NOT EXISTS t_sys_role_permissions (
            id BIGSERIAL PRIMARY KEY,
            role_id BIGINT NOT NULL,
            api_id BIGINT NOT NULL,
            permission_type VARCHAR(20) DEFAULT 'allow',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            CONSTRAINT fk_role_permissions_role FOREIGN KEY (role_id) REFERENCES t_sys_roles(id) ON DELETE CASCADE,
            CONSTRAINT fk_role_permissions_api FOREIGN KEY (api_id) REFERENCES t_sys_api_endpoints(id) ON DELETE CASCADE,
            CONSTRAINT uk_role_api UNIQUE (role_id, api_id)
        );
        
        -- 3. 迁移角色权限数据
        INSERT INTO t_sys_role_permissions (role_id, api_id, permission_type)
        SELECT DISTINCT
            ra.role_id,
            ae.id as api_id,
            'allow' as permission_type
        FROM role_api ra
        JOIN t_sys_apis_old a ON ra.api_id = a.id
        JOIN t_sys_api_endpoints ae ON LOWER(REPLACE(CONCAT(a.method, '_', a.path), '/', '_')) = ae.api_code
        WHERE NOT EXISTS (
            SELECT 1 FROM t_sys_role_permissions 
            WHERE role_id = ra.role_id AND api_id = ae.id
        );
        
        -- 4. 记录迁移统计
        INSERT INTO t_sys_migration_logs (migration_id, migration_name, migration_type, version, description, status)
        VALUES ('003_migrate_permissions', '权限数据迁移', 'permission', '2.0.0', 
                CONCAT('迁移了 ', (SELECT COUNT(*) FROM t_sys_permission_migrations), ' 个权限映射'), 'success')
        ON CONFLICT (migration_id) DO NOTHING;
        """
    
    def _get_permission_rollback_sql(self) -> str:
        """获取权限迁移回滚SQL"""
        return """
        -- 权限数据迁移回滚
        DROP TABLE IF EXISTS t_sys_role_permissions;
        DELETE FROM t_sys_permission_migrations WHERE migration_batch = 'batch_001';
        """
    
    def _get_performance_indexes_sql(self) -> str:
        """获取性能优化索引SQL"""
        return """
        -- 创建性能优化索引
        
        -- 1. 用户权限查询优化索引
        CREATE INDEX IF NOT EXISTS idx_user_roles_composite ON t_sys_user_roles(user_id, role_id);
        CREATE INDEX IF NOT EXISTS idx_role_permissions_composite ON t_sys_role_permissions(role_id, api_id, permission_type);
        CREATE INDEX IF NOT EXISTS idx_api_endpoints_lookup ON t_sys_api_endpoints(http_method, api_path, status);
        
        -- 2. 权限验证覆盖索引
        CREATE INDEX IF NOT EXISTS idx_user_permissions_covering ON t_sys_user_roles(user_id) 
        INCLUDE (role_id) WHERE role_id IS NOT NULL;
        
        CREATE INDEX IF NOT EXISTS idx_role_api_permissions_covering ON t_sys_role_permissions(role_id, permission_type) 
        INCLUDE (api_id) WHERE permission_type = 'allow';
        
        -- 3. API查询优化索引
        CREATE INDEX IF NOT EXISTS idx_api_endpoints_group_status ON t_sys_api_endpoints(group_id, status) 
        WHERE status = 'active';
        
        CREATE INDEX IF NOT EXISTS idx_api_groups_hierarchy ON t_sys_api_groups(parent_id, sort_order) 
        WHERE status = 'active';
        
        -- 4. 权限迁移查询索引
        CREATE INDEX IF NOT EXISTS idx_permission_migrations_confidence ON t_sys_permission_migrations(confidence_score DESC, is_active) 
        WHERE is_active = TRUE;
        
        CREATE INDEX IF NOT EXISTS idx_permission_migrations_group_type ON t_sys_permission_migrations(api_group, migration_type);
        
        -- 5. 审计日志查询索引
        CREATE INDEX IF NOT EXISTS idx_audit_logs_user_time ON t_sys_audit_logs(user_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_path_method ON t_sys_audit_logs(path, method, created_at DESC);
        
        -- 记录索引创建
        INSERT INTO t_sys_migration_logs (migration_id, migration_name, migration_type, version, description, status)
        VALUES ('004_create_performance_indexes', '创建性能优化索引', 'index', '2.0.0', '创建了权限查询优化索引', 'success')
        ON CONFLICT (migration_id) DO NOTHING;
        """
    
    def _get_performance_indexes_rollback_sql(self) -> str:
        """获取性能优化索引回滚SQL"""
        return """
        -- 删除性能优化索引
        DROP INDEX IF EXISTS idx_user_roles_composite;
        DROP INDEX IF EXISTS idx_role_permissions_composite;
        DROP INDEX IF EXISTS idx_api_endpoints_lookup;
        DROP INDEX IF EXISTS idx_user_permissions_covering;
        DROP INDEX IF EXISTS idx_role_api_permissions_covering;
        DROP INDEX IF EXISTS idx_api_endpoints_group_status;
        DROP INDEX IF EXISTS idx_api_groups_hierarchy;
        DROP INDEX IF EXISTS idx_permission_migrations_confidence;
        DROP INDEX IF EXISTS idx_permission_migrations_group_type;
        DROP INDEX IF EXISTS idx_audit_logs_user_time;
        DROP INDEX IF EXISTS idx_audit_logs_path_method;
        """
    
    def _get_business_views_sql(self) -> str:
        """获取业务视图SQL"""
        return """
        -- 创建业务视图
        
        -- 1. 用户权限详情视图
        CREATE OR REPLACE VIEW v_user_permissions AS
        SELECT 
            u.id as user_id,
            u.username,
            u.alias as display_name,
            r.id as role_id,
            r.name as role_name,
            ae.id as api_id,
            ae.api_code,
            ae.api_name,
            ae.api_path,
            ae.http_method,
            ag.group_name as api_group,
            rp.permission_type,
            u.is_active as user_active,
            ae.status as api_status
        FROM t_sys_users u
        JOIN t_sys_user_roles ur ON u.id = ur.user_id
        JOIN t_sys_roles r ON ur.role_id = r.id
        JOIN t_sys_role_permissions rp ON r.id = rp.role_id
        JOIN t_sys_api_endpoints ae ON rp.api_id = ae.id
        JOIN t_sys_api_groups ag ON ae.group_id = ag.id
        WHERE u.is_active = TRUE 
          AND ae.status = 'active'
          AND rp.permission_type = 'allow';
        
        -- 2. 角色权限统计视图
        CREATE OR REPLACE VIEW v_role_permission_stats AS
        SELECT 
            r.id as role_id,
            r.name as role_name,
            r.desc as role_description,
            COUNT(rp.api_id) as total_permissions,
            COUNT(DISTINCT ag.id) as api_groups_count,
            COUNT(DISTINCT ur.user_id) as users_count,
            STRING_AGG(DISTINCT ag.group_name, ', ' ORDER BY ag.group_name) as api_groups
        FROM t_sys_roles r
        LEFT JOIN t_sys_role_permissions rp ON r.id = rp.role_id AND rp.permission_type = 'allow'
        LEFT JOIN t_sys_api_endpoints ae ON rp.api_id = ae.id AND ae.status = 'active'
        LEFT JOIN t_sys_api_groups ag ON ae.group_id = ag.id
        LEFT JOIN t_sys_user_roles ur ON r.id = ur.role_id
        GROUP BY r.id, r.name, r.desc
        ORDER BY r.name;
        
        -- 3. API使用统计视图
        CREATE OR REPLACE VIEW v_api_usage_stats AS
        SELECT 
            ae.id as api_id,
            ae.api_code,
            ae.api_name,
            ae.api_path,
            ae.http_method,
            ag.group_name as api_group,
            COUNT(DISTINCT rp.role_id) as roles_count,
            COUNT(DISTINCT ur.user_id) as users_count,
            ae.is_public,
            ae.is_deprecated,
            ae.status
        FROM t_sys_api_endpoints ae
        JOIN t_sys_api_groups ag ON ae.group_id = ag.id
        LEFT JOIN t_sys_role_permissions rp ON ae.id = rp.api_id AND rp.permission_type = 'allow'
        LEFT JOIN t_sys_user_roles ur ON rp.role_id = ur.role_id
        GROUP BY ae.id, ae.api_code, ae.api_name, ae.api_path, ae.http_method, 
                 ag.group_name, ae.is_public, ae.is_deprecated, ae.status
        ORDER BY ag.group_name, ae.api_path;
        
        -- 4. 部门用户权限视图
        CREATE OR REPLACE VIEW v_department_user_permissions AS
        SELECT 
            d.id as department_id,
            d.name as department_name,
            u.id as user_id,
            u.username,
            u.alias as display_name,
            COUNT(DISTINCT r.id) as roles_count,
            COUNT(DISTINCT ae.id) as permissions_count,
            STRING_AGG(DISTINCT r.name, ', ' ORDER BY r.name) as roles,
            STRING_AGG(DISTINCT ag.group_name, ', ' ORDER BY ag.group_name) as api_groups
        FROM t_sys_departments d
        JOIN t_sys_users u ON d.id = u.dept_id
        LEFT JOIN t_sys_user_roles ur ON u.id = ur.user_id
        LEFT JOIN t_sys_roles r ON ur.role_id = r.id
        LEFT JOIN t_sys_role_permissions rp ON r.id = rp.role_id AND rp.permission_type = 'allow'
        LEFT JOIN t_sys_api_endpoints ae ON rp.api_id = ae.id AND ae.status = 'active'
        LEFT JOIN t_sys_api_groups ag ON ae.group_id = ag.id
        WHERE u.is_active = TRUE
        GROUP BY d.id, d.name, u.id, u.username, u.alias
        ORDER BY d.name, u.username;
        
        -- 记录视图创建
        INSERT INTO t_sys_migration_logs (migration_id, migration_name, migration_type, version, description, status)
        VALUES ('005_create_business_views', '创建业务视图', 'view', '2.0.0', '创建了4个常用业务查询视图', 'success')
        ON CONFLICT (migration_id) DO NOTHING;
        """
    
    def _get_business_views_rollback_sql(self) -> str:
        """获取业务视图回滚SQL"""
        return """
        -- 删除业务视图
        DROP VIEW IF EXISTS v_user_permissions;
        DROP VIEW IF EXISTS v_role_permission_stats;
        DROP VIEW IF EXISTS v_api_usage_stats;
        DROP VIEW IF EXISTS v_department_user_permissions;
        """
    
    def _get_permission_functions_sql(self) -> str:
        """获取权限验证函数SQL"""
        return """
        -- 创建权限验证函数
        
        -- 1. 检查用户权限函数
        CREATE OR REPLACE FUNCTION check_user_permission(
            p_user_id BIGINT,
            p_api_path VARCHAR,
            p_http_method VARCHAR
        )
        RETURNS BOOLEAN AS $
        DECLARE
            has_permission BOOLEAN := FALSE;
        BEGIN
            SELECT EXISTS(
                SELECT 1
                FROM t_sys_users u
                JOIN t_sys_user_roles ur ON u.id = ur.user_id
                JOIN t_sys_role_permissions rp ON ur.role_id = rp.role_id
                JOIN t_sys_api_endpoints ae ON rp.api_id = ae.id
                WHERE u.id = p_user_id
                  AND u.is_active = TRUE
                  AND ae.api_path = p_api_path
                  AND ae.http_method = p_http_method
                  AND ae.status = 'active'
                  AND rp.permission_type = 'allow'
            ) INTO has_permission;
            
            RETURN has_permission;
        END;
        $ LANGUAGE plpgsql;
        
        -- 2. 获取用户所有权限函数
        CREATE OR REPLACE FUNCTION get_user_permissions(p_user_id BIGINT)
        RETURNS TABLE(
            api_code VARCHAR,
            api_path VARCHAR,
            http_method VARCHAR,
            api_group VARCHAR
        ) AS $
        BEGIN
            RETURN QUERY
            SELECT 
                ae.api_code,
                ae.api_path,
                ae.http_method,
                ag.group_name
            FROM t_sys_users u
            JOIN t_sys_user_roles ur ON u.id = ur.user_id
            JOIN t_sys_role_permissions rp ON ur.role_id = rp.role_id
            JOIN t_sys_api_endpoints ae ON rp.api_id = ae.id
            JOIN t_sys_api_groups ag ON ae.group_id = ag.id
            WHERE u.id = p_user_id
              AND u.is_active = TRUE
              AND ae.status = 'active'
              AND rp.permission_type = 'allow'
            ORDER BY ag.group_name, ae.api_path;
        END;
        $ LANGUAGE plpgsql;
        
        -- 3. 批量检查权限函数
        CREATE OR REPLACE FUNCTION batch_check_permissions(
            p_user_id BIGINT,
            p_api_requests JSONB
        )
        RETURNS JSONB AS $
        DECLARE
            request JSONB;
            result JSONB := '{}';
            permission_key VARCHAR;
            has_permission BOOLEAN;
        BEGIN
            FOR request IN SELECT jsonb_array_elements(p_api_requests)
            LOOP
                permission_key := request->>'method' || ' ' || request->>'path';
                
                SELECT check_user_permission(
                    p_user_id,
                    request->>'path',
                    request->>'method'
                ) INTO has_permission;
                
                result := result || jsonb_build_object(permission_key, has_permission);
            END LOOP;
            
            RETURN result;
        END;
        $ LANGUAGE plpgsql;
        
        -- 4. 权限继承检查函数
        CREATE OR REPLACE FUNCTION check_permission_inheritance(
            p_role_id BIGINT,
            p_api_path VARCHAR,
            p_http_method VARCHAR
        )
        RETURNS BOOLEAN AS $
        DECLARE
            has_direct_permission BOOLEAN := FALSE;
            has_inherited_permission BOOLEAN := FALSE;
        BEGIN
            -- 检查直接权限
            SELECT EXISTS(
                SELECT 1
                FROM t_sys_role_permissions rp
                JOIN t_sys_api_endpoints ae ON rp.api_id = ae.id
                WHERE rp.role_id = p_role_id
                  AND ae.api_path = p_api_path
                  AND ae.http_method = p_http_method
                  AND ae.status = 'active'
                  AND rp.permission_type = 'allow'
            ) INTO has_direct_permission;
            
            -- 如果有直接权限，返回true
            IF has_direct_permission THEN
                RETURN TRUE;
            END IF;
            
            -- 检查通配符权限 (例如 GET /api/v2/users/* 包含 GET /api/v2/users/123)
            SELECT EXISTS(
                SELECT 1
                FROM t_sys_role_permissions rp
                JOIN t_sys_api_endpoints ae ON rp.api_id = ae.id
                WHERE rp.role_id = p_role_id
                  AND ae.http_method = p_http_method
                  AND ae.status = 'active'
                  AND rp.permission_type = 'allow'
                  AND (
                    p_api_path LIKE REPLACE(ae.api_path, '*', '%')
                    OR ae.api_path LIKE '%*'
                  )
            ) INTO has_inherited_permission;
            
            RETURN has_inherited_permission;
        END;
        $ LANGUAGE plpgsql;
        
        -- 记录函数创建
        INSERT INTO t_sys_migration_logs (migration_id, migration_name, migration_type, version, description, status)
        VALUES ('006_create_permission_functions', '创建权限验证函数', 'function', '2.0.0', '创建了4个权限验证相关函数', 'success')
        ON CONFLICT (migration_id) DO NOTHING;
        """
    
    def _get_permission_functions_rollback_sql(self) -> str:
        """获取权限验证函数回滚SQL"""
        return """
        -- 删除权限验证函数
        DROP FUNCTION IF EXISTS check_user_permission(BIGINT, VARCHAR, VARCHAR);
        DROP FUNCTION IF EXISTS get_user_permissions(BIGINT);
        DROP FUNCTION IF EXISTS batch_check_permissions(BIGINT, JSONB);
        DROP FUNCTION IF EXISTS check_permission_inheritance(BIGINT, VARCHAR, VARCHAR);
        """
    
    async def run_all_migrations(self) -> bool:
        """运行所有预定义迁移"""
        logger.info("开始运行所有预定义迁移...")
        
        try:
            await self.migration_system.connect()
            
            # 初始化迁移系统
            await self.migration_system.initialize_migration_system()
            
            # 创建数据库版本
            await self.migration_system.create_database_version("2.0.0", "API v2权限重构版本")
            
            # 注册所有预定义迁移
            for migration in self.predefined_migrations:
                await self.migration_system.register_migration(migration)
            
            # 按依赖顺序执行迁移
            success_count = 0
            for migration in self.predefined_migrations:
                logger.info(f"执行迁移: {migration.name}")
                
                if await self.migration_system.execute_migration(migration.id):
                    success_count += 1
                    logger.info(f"✅ 迁移 {migration.name} 执行成功")
                else:
                    logger.error(f"❌ 迁移 {migration.name} 执行失败")
                    return False
            
            # 设置当前版本
            await self.migration_system.set_current_version("2.0.0")
            
            logger.info(f"🎉 所有迁移执行完成! 成功执行 {success_count}/{len(self.predefined_migrations)} 个迁移")
            return True
            
        except Exception as e:
            logger.error(f"迁移执行过程中发生错误: {e}")
            return False
        finally:
            await self.migration_system.disconnect()
    
    async def rollback_all_migrations(self) -> bool:
        """回滚所有迁移"""
        logger.info("开始回滚所有迁移...")
        
        try:
            await self.migration_system.connect()
            
            # 按相反顺序回滚迁移
            success_count = 0
            for migration in reversed(self.predefined_migrations):
                logger.info(f"回滚迁移: {migration.name}")
                
                if await self.migration_system.rollback_migration(migration.id):
                    success_count += 1
                    logger.info(f"✅ 迁移 {migration.name} 回滚成功")
                else:
                    logger.warning(f"⚠️ 迁移 {migration.name} 回滚失败或未执行")
            
            logger.info(f"🔄 迁移回滚完成! 成功回滚 {success_count} 个迁移")
            return True
            
        except Exception as e:
            logger.error(f"迁移回滚过程中发生错误: {e}")
            return False
        finally:
            await self.migration_system.disconnect()
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """获取迁移状态"""
        try:
            await self.migration_system.connect()
            status = await self.migration_system.get_migration_status()
            return status
        except Exception as e:
            logger.error(f"获取迁移状态失败: {e}")
            return {}
        finally:
            await self.migration_system.disconnect()
    
    async def validate_migrations(self) -> bool:
        """验证迁移结果"""
        logger.info("验证迁移结果...")
        
        try:
            await self.migration_system.connect()
            
            # 执行权限迁移验证
            validation_results = await self.migration_system.connection.fetch(
                "SELECT * FROM validate_permission_migration()"
            )
            
            all_passed = True
            for result in validation_results:
                status = result['status']
                message = result['message']
                
                if status == 'PASS':
                    logger.info(f"✅ {message}")
                elif status == 'WARN':
                    logger.warning(f"⚠️ {message}")
                    # 警告不算失败
                else:
                    logger.error(f"❌ {message}")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            logger.error(f"验证迁移结果失败: {e}")
            return False
        finally:
            await self.migration_system.disconnect()

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据库迁移自动化工具')
    parser.add_argument('--db-url', required=True, help='数据库连接URL')
    parser.add_argument('--action', choices=['migrate', 'rollback', 'status', 'validate'], 
                       default='migrate', help='执行的操作')
    parser.add_argument('--migrations-dir', default='database/migrations', 
                       help='迁移文件目录')
    
    args = parser.parse_args()
    
    automation = MigrationAutomation(args.db_url, args.migrations_dir)
    
    try:
        if args.action == 'migrate':
            success = await automation.run_all_migrations()
            if success:
                print("🎉 迁移执行成功!")
                # 验证迁移结果
                if await automation.validate_migrations():
                    print("✅ 迁移验证通过!")
                    sys.exit(0)
                else:
                    print("⚠️ 迁移验证有警告，请检查日志")
                    sys.exit(1)
            else:
                print("❌ 迁移执行失败!")
                sys.exit(1)
        
        elif args.action == 'rollback':
            success = await automation.rollback_all_migrations()
            if success:
                print("🔄 迁移回滚成功!")
                sys.exit(0)
            else:
                print("❌ 迁移回滚失败!")
                sys.exit(1)
        
        elif args.action == 'status':
            status = await automation.get_migration_status()
            print("📊 迁移状态:")
            print(json.dumps(status, indent=2, ensure_ascii=False))
            sys.exit(0)
        
        elif args.action == 'validate':
            success = await automation.validate_migrations()
            if success:
                print("✅ 迁移验证通过!")
                sys.exit(0)
            else:
                print("❌ 迁移验证失败!")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序执行错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())