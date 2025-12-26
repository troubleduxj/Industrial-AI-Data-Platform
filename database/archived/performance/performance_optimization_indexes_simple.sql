-- 数据库性能优化 - 权限查询核心索引（简化版）
-- API权限重构项目 - 任务3.5
-- 创建时间: 2025-01-10

-- ============================================================================
-- 1. 权限查询核心索引
-- ============================================================================

-- 1.1 API端点表索引优化
CREATE INDEX IF NOT EXISTS idx_api_endpoints_path_method 
ON t_sys_api_endpoints(api_path, http_method) 
WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_api_endpoints_code_active 
ON t_sys_api_endpoints(api_code) 
WHERE status = 'active' AND is_deprecated = false;

CREATE INDEX IF NOT EXISTS idx_api_endpoints_group_status 
ON t_sys_api_endpoints(group_id, status);

CREATE INDEX IF NOT EXISTS idx_api_endpoints_version_status 
ON t_sys_api_endpoints(version, status) 
WHERE is_deprecated = false;

-- 1.2 用户权限表索引优化
CREATE INDEX IF NOT EXISTS idx_user_permissions_user_active 
ON t_sys_user_permissions(user_id, is_active) 
WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_user_permissions_code_user 
ON t_sys_user_permissions(permission_code, user_id) 
WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_user_permissions_expires 
ON t_sys_user_permissions(expires_at) 
WHERE expires_at IS NOT NULL AND is_active = true;

CREATE INDEX IF NOT EXISTS idx_user_permissions_resource 
ON t_sys_user_permissions(user_id, resource_id, permission_code) 
WHERE is_active = true;

-- 1.3 角色权限表索引优化
CREATE INDEX IF NOT EXISTS idx_role_permissions_role_active 
ON t_sys_role_permissions(role_id, is_active) 
WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_role_permissions_code_role 
ON t_sys_role_permissions(permission_code, role_id) 
WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_role_permissions_resource_type 
ON t_sys_role_permissions(role_id, resource_type, permission_code) 
WHERE is_active = true;

-- ============================================================================
-- 2. 覆盖索引优化
-- ============================================================================

-- 2.1 API端点覆盖索引
CREATE INDEX IF NOT EXISTS idx_api_endpoints_permission_check 
ON t_sys_api_endpoints(api_path, http_method, api_code, status, is_public) 
WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_api_endpoints_list_query 
ON t_sys_api_endpoints(group_id, status, api_name, api_code) 
WHERE status IN ('active', 'inactive');

-- 2.2 用户权限覆盖索引
CREATE INDEX IF NOT EXISTS idx_user_permissions_check_cover 
ON t_sys_user_permissions(user_id, permission_code, is_active, expires_at) 
WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_user_permissions_list_cover 
ON t_sys_user_permissions(user_id, is_active, permission_code, resource_id, granted_at) 
WHERE is_active = true;

-- 2.3 角色权限覆盖索引
CREATE INDEX IF NOT EXISTS idx_role_permissions_check_cover 
ON t_sys_role_permissions(role_id, permission_code, is_active, resource_type) 
WHERE is_active = true;

-- ============================================================================
-- 3. 复合查询索引
-- ============================================================================

-- 3.1 权限验证复合查询索引
CREATE INDEX IF NOT EXISTS idx_user_perm_resource_composite 
ON t_sys_user_permissions(user_id, permission_code, resource_id, is_active, expires_at) 
WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_role_perm_type_composite 
ON t_sys_role_permissions(role_id, permission_code, resource_type, is_active) 
WHERE is_active = true;

-- 3.2 API查询复合索引
CREATE INDEX IF NOT EXISTS idx_api_path_method_status_composite 
ON t_sys_api_endpoints(api_path, http_method, status, version) 
WHERE status = 'active' AND is_deprecated = false;

-- ============================================================================
-- 4. 显示创建的索引统计
-- ============================================================================

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

-- 权限查询核心索引创建完成
SELECT '✅ 权限查询核心索引创建完成！' as status;