-- 数据库性能优化 - 权限查询核心索引
-- API权限重构项目 - 任务3.5
-- 创建时间: 2025-01-10

-- ============================================================================
-- 1. 权限查询核心索引
-- ============================================================================

-- 1.1 API端点表索引优化
-- 基础索引
CREATE INDEX IF NOT EXISTS idx_api_endpoints_path_method 
ON t_sys_api_endpoints(api_path, http_method) 
WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_api_endpoints_code_active 
ON t_sys_api_endpoints(api_code) 
WHERE status = 'active' AND is_deprecated = false;

CREATE INDEX IF NOT EXISTS idx_api_endpoints_group_status 
ON t_sys_api_endpoints(group_id, status);

-- 版本查询索引
CREATE INDEX IF NOT EXISTS idx_api_endpoints_version_status 
ON t_sys_api_endpoints(version, status) 
WHERE is_deprecated = false;

-- 1.2 用户权限表索引优化
-- 用户权限查询核心索引
CREATE INDEX IF NOT EXISTS idx_user_permissions_user_active 
ON t_sys_user_permissions(user_id, is_active) 
WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_user_permissions_code_user 
ON t_sys_user_permissions(permission_code, user_id) 
WHERE is_active = true;

-- 权限过期查询索引
CREATE INDEX IF NOT EXISTS idx_user_permissions_expires 
ON t_sys_user_permissions(expires_at) 
WHERE expires_at IS NOT NULL AND is_active = true;

-- 资源权限查询索引
CREATE INDEX IF NOT EXISTS idx_user_permissions_resource 
ON t_sys_user_permissions(user_id, resource_id, permission_code) 
WHERE is_active = true;

-- 1.3 角色权限表索引优化
-- 角色权限查询核心索引
CREATE INDEX IF NOT EXISTS idx_role_permissions_role_active 
ON t_sys_role_permissions(role_id, is_active) 
WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_role_permissions_code_role 
ON t_sys_role_permissions(permission_code, role_id) 
WHERE is_active = true;

-- 资源类型权限查询索引
CREATE INDEX IF NOT EXISTS idx_role_permissions_resource_type 
ON t_sys_role_permissions(role_id, resource_type, permission_code) 
WHERE is_active = true;

-- 1.4 用户角色关联表索引（假设存在）
-- 如果存在用户角色关联表，创建相应索引
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 't_sys_user_roles') THEN
        -- 用户角色查询索引
        EXECUTE 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_roles_user_id ON t_sys_user_roles(user_id)';
        EXECUTE 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_roles_role_id ON t_sys_user_roles(role_id)';
        EXECUTE 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_roles_user_role ON t_sys_user_roles(user_id, role_id)';
        
        RAISE NOTICE '用户角色关联表索引创建完成';
    ELSE
        RAISE NOTICE '用户角色关联表不存在，跳过相关索引创建';
    END IF;
END $$;

-- ============================================================================
-- 2. 覆盖索引优化（包含所有查询需要的列）
-- ============================================================================

-- 2.1 API端点覆盖索引
-- 权限验证查询覆盖索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_endpoints_permission_check 
ON t_sys_api_endpoints(api_path, http_method, api_code, status, is_public) 
WHERE status = 'active';

-- API列表查询覆盖索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_endpoints_list_query 
ON t_sys_api_endpoints(group_id, status, sort_order, api_name, api_code) 
WHERE status IN ('active', 'inactive');

-- 2.2 用户权限覆盖索引
-- 用户权限检查覆盖索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_permissions_check_cover 
ON t_sys_user_permissions(user_id, permission_code, is_active, expires_at) 
WHERE is_active = true;

-- 用户权限列表覆盖索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_permissions_list_cover 
ON t_sys_user_permissions(user_id, is_active, permission_code, resource_id, granted_at) 
WHERE is_active = true;

-- 2.3 角色权限覆盖索引
-- 角色权限检查覆盖索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_role_permissions_check_cover 
ON t_sys_role_permissions(role_id, permission_code, is_active, resource_type) 
WHERE is_active = true;

-- ============================================================================
-- 3. 复合查询索引
-- ============================================================================

-- 3.1 权限验证复合查询索引
-- 用户+权限+资源复合查询
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_perm_resource_composite 
ON t_sys_user_permissions(user_id, permission_code, resource_id, is_active, expires_at) 
WHERE is_active = true;

-- 角色+权限+资源类型复合查询
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_role_perm_type_composite 
ON t_sys_role_permissions(role_id, permission_code, resource_type, is_active) 
WHERE is_active = true;

-- 3.2 API查询复合索引
-- API路径+方法+状态复合查询
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_path_method_status_composite 
ON t_sys_api_endpoints(api_path, http_method, status, version) 
WHERE status = 'active' AND is_deprecated = false;

-- ============================================================================
-- 4. 分区表索引（如果使用分区）
-- ============================================================================

-- 4.1 按时间分区的权限日志表索引（如果存在）
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 't_sys_permission_logs') THEN
        -- 权限日志时间索引
        EXECUTE 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_permission_logs_created_at ON t_sys_permission_logs(created_at DESC)';
        EXECUTE 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_permission_logs_user_time ON t_sys_permission_logs(user_id, created_at DESC)';
        
        RAISE NOTICE '权限日志表索引创建完成';
    ELSE
        RAISE NOTICE '权限日志表不存在，跳过相关索引创建';
    END IF;
END $$;

-- ============================================================================
-- 5. 唯一约束索引
-- ============================================================================

-- 5.1 确保唯一约束索引存在
-- API端点唯一约束
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS uk_api_endpoints_code 
ON t_sys_api_endpoints(api_code);

CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS uk_api_endpoints_path_method 
ON t_sys_api_endpoints(api_path, http_method) 
WHERE status != 'deprecated';

-- 用户权限唯一约束
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS uk_user_permissions_unique 
ON t_sys_user_permissions(user_id, permission_code, COALESCE(resource_id, '')) 
WHERE is_active = true;

-- 角色权限唯一约束
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS uk_role_permissions_unique 
ON t_sys_role_permissions(role_id, permission_code, COALESCE(resource_type, '')) 
WHERE is_active = true;

-- ============================================================================
-- 6. 索引创建完成统计
-- ============================================================================

-- 显示创建的索引统计
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND tablename IN ('t_sys_api_endpoints', 't_sys_user_permissions', 't_sys_role_permissions')
  AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

-- 显示索引大小统计
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND tablename IN ('t_sys_api_endpoints', 't_sys_user_permissions', 't_sys_role_permissions')
  AND indexname LIKE 'idx_%'
ORDER BY pg_relation_size(indexname::regclass) DESC;

-- 权限查询核心索引创建完成
SELECT '✅ 权限查询核心索引创建完成！' as status;