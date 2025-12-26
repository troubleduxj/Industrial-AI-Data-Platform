#!/usr/bin/env python3
"""
简化的数据库迁移脚本
针对PostgreSQL 17的API权限重构迁移
"""

import subprocess
import sys
import os

def install_dependencies():
    """安装必要的依赖"""
    print("📦 安装Python依赖...")
    
    try:
        # 安装asyncpg
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', 'asyncpg'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ asyncpg 安装成功")
        else:
            print(f"❌ asyncpg 安装失败: {result.stderr}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ 安装依赖失败: {e}")
        return False

def create_migration_sql():
    """创建迁移SQL脚本"""
    print("📝 创建迁移SQL脚本...")
    
    sql_content = """
-- API权限重构数据库迁移脚本
-- 针对PostgreSQL 17

-- 1. 创建API分组表
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

-- 插入默认API分组
INSERT INTO t_sys_api_groups (id, group_code, group_name, description, sort_order) 
VALUES (1, 'default', '默认分组', '默认API分组', 0)
ON CONFLICT (group_code) DO NOTHING;

-- 2. 创建API端点表
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
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_api_endpoint_status CHECK (status IN ('active', 'inactive', 'deprecated')),
    CONSTRAINT chk_http_method CHECK (http_method IN ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS')),
    FOREIGN KEY (group_id) REFERENCES t_sys_api_groups(id)
);

-- 3. 创建用户权限表
CREATE TABLE IF NOT EXISTS t_sys_user_permissions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    permission_code VARCHAR(255) NOT NULL,
    resource_id VARCHAR(100),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by BIGINT,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, permission_code, resource_id)
);

-- 4. 创建角色权限表
CREATE TABLE IF NOT EXISTS t_sys_role_permissions (
    id BIGSERIAL PRIMARY KEY,
    role_id BIGINT NOT NULL,
    permission_code VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(role_id, permission_code, resource_type)
);

-- 5. 创建索引
CREATE INDEX IF NOT EXISTS idx_api_endpoints_path ON t_sys_api_endpoints(api_path);
CREATE INDEX IF NOT EXISTS idx_api_endpoints_method ON t_sys_api_endpoints(http_method);
CREATE INDEX IF NOT EXISTS idx_api_endpoints_group ON t_sys_api_endpoints(group_id);
CREATE INDEX IF NOT EXISTS idx_api_endpoints_status ON t_sys_api_endpoints(status);

CREATE INDEX IF NOT EXISTS idx_user_permissions_user ON t_sys_user_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_permissions_code ON t_sys_user_permissions(permission_code);
CREATE INDEX IF NOT EXISTS idx_user_permissions_active ON t_sys_user_permissions(is_active);

CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON t_sys_role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_code ON t_sys_role_permissions(permission_code);
CREATE INDEX IF NOT EXISTS idx_role_permissions_active ON t_sys_role_permissions(is_active);

-- 6. 数据迁移（如果源表存在）
-- 迁移API数据
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'api') THEN
        INSERT INTO t_sys_api_endpoints (
            api_code, api_name, api_path, http_method, group_id, 
            description, version, is_public, status, created_at, updated_at
        )
        SELECT 
            COALESCE(code, 'api_' || id::text) as api_code,
            COALESCE(name, path) as api_name,
            path as api_path,
            COALESCE(method, 'GET') as http_method,
            1 as group_id,
            description,
            'v2' as version,
            COALESCE(is_public, false) as is_public,
            CASE 
                WHEN status = 1 THEN 'active'
                WHEN status = 0 THEN 'inactive'
                ELSE 'active'
            END as status,
            COALESCE(created_at, CURRENT_TIMESTAMP) as created_at,
            COALESCE(updated_at, CURRENT_TIMESTAMP) as updated_at
        FROM api
        ON CONFLICT (api_code) DO UPDATE SET
            api_name = EXCLUDED.api_name,
            api_path = EXCLUDED.api_path,
            http_method = EXCLUDED.http_method,
            description = EXCLUDED.description,
            updated_at = CURRENT_TIMESTAMP;
        
        RAISE NOTICE 'API数据迁移完成';
    ELSE
        RAISE NOTICE '源表api不存在，跳过API数据迁移';
    END IF;
END $$;

-- 迁移用户权限数据
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'user_permissions') THEN
        INSERT INTO t_sys_user_permissions (
            user_id, permission_code, resource_id, granted_at, 
            granted_by, expires_at, is_active, created_at, updated_at
        )
        SELECT 
            user_id,
            permission_code,
            resource_id,
            COALESCE(granted_at, CURRENT_TIMESTAMP) as granted_at,
            granted_by,
            expires_at,
            COALESCE(is_active, true) as is_active,
            COALESCE(created_at, CURRENT_TIMESTAMP) as created_at,
            COALESCE(updated_at, CURRENT_TIMESTAMP) as updated_at
        FROM user_permissions
        ON CONFLICT (user_id, permission_code, resource_id) DO UPDATE SET
            granted_at = EXCLUDED.granted_at,
            is_active = EXCLUDED.is_active,
            updated_at = CURRENT_TIMESTAMP;
        
        RAISE NOTICE '用户权限数据迁移完成';
    ELSE
        RAISE NOTICE '源表user_permissions不存在，跳过用户权限数据迁移';
    END IF;
END $$;

-- 迁移角色权限数据
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'role_permissions') THEN
        INSERT INTO t_sys_role_permissions (
            role_id, permission_code, resource_type, is_active, created_at, updated_at
        )
        SELECT 
            role_id,
            permission_code,
            resource_type,
            COALESCE(is_active, true) as is_active,
            COALESCE(created_at, CURRENT_TIMESTAMP) as created_at,
            COALESCE(updated_at, CURRENT_TIMESTAMP) as updated_at
        FROM role_permissions
        ON CONFLICT (role_id, permission_code, resource_type) DO UPDATE SET
            is_active = EXCLUDED.is_active,
            updated_at = CURRENT_TIMESTAMP;
        
        RAISE NOTICE '角色权限数据迁移完成';
    ELSE
        RAISE NOTICE '源表role_permissions不存在，跳过角色权限数据迁移';
    END IF;
END $$;

-- 7. 显示迁移结果
SELECT 
    'API端点' as 表名,
    COUNT(*) as 记录数
FROM t_sys_api_endpoints
UNION ALL
SELECT 
    '用户权限' as 表名,
    COUNT(*) as 记录数
FROM t_sys_user_permissions
UNION ALL
SELECT 
    '角色权限' as 表名,
    COUNT(*) as 记录数
FROM t_sys_role_permissions;

-- 迁移完成
SELECT '🎉 API权限重构数据库迁移完成！' as 状态;
    """
    
    try:
        with open('migration_script.sql', 'w', encoding='utf-8') as f:
            f.write(sql_content)
        
        print("✅ 迁移SQL脚本已创建: migration_script.sql")
        return True
    except Exception as e:
        print(f"❌ 创建SQL脚本失败: {e}")
        return False

def run_migration():
    """执行迁移"""
    print("🚀 执行数据库迁移...")
    
    # 数据库连接信息
    db_config = {
        'host': '127.0.0.1',
        'port': '5432',
        'user': 'postgres',
        'password': 'Hanatech@123',
        'database': 'devicemonitor'
    }
    
    try:
        # 使用psql命令执行迁移
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['password']
        
        result = subprocess.run([
            'psql',
            '-h', db_config['host'],
            '-p', db_config['port'],
            '-U', db_config['user'],
            '-d', db_config['database'],
            '-f', 'migration_script.sql'
        ], env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 数据库迁移执行成功")
            print("📊 迁移结果:")
            print(result.stdout)
            return True
        else:
            print(f"❌ 数据库迁移失败: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ 未找到psql命令")
        print("请确保PostgreSQL客户端已安装并在PATH中")
        return False
    except Exception as e:
        print(f"❌ 执行迁移失败: {e}")
        return False

def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                🚀 API权限重构 - 简化迁移                     ║
║              PostgreSQL 17 - Simple Migration               ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # 1. 安装依赖
    if not install_dependencies():
        print("❌ 依赖安装失败，迁移终止")
        return False
    
    # 2. 创建迁移脚本
    if not create_migration_sql():
        print("❌ 创建迁移脚本失败，迁移终止")
        return False
    
    # 3. 执行迁移
    if not run_migration():
        print("❌ 迁移执行失败")
        return False
    
    print("""
🎉 API权限重构数据库迁移完成！

📋 已完成的工作:
✅ 创建了新的权限系统表结构
✅ 迁移了现有的API数据
✅ 迁移了现有的权限数据
✅ 创建了必要的索引

📄 生成的文件:
- migration_script.sql (迁移脚本)

🎊 恭喜完成API权限重构迁移！
    """)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)