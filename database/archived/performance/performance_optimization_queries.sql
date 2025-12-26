-- 数据库性能优化 - 优化权限验证SQL查询语句
-- API权限重构项目 - 任务3.5
-- 创建时间: 2025-01-10

-- ============================================================================
-- 1. 权限验证核心查询优化
-- ============================================================================

-- 1.1 单个权限验证查询（最常用）
-- 优化前的查询（避免使用）
/*
SELECT COUNT(*) > 0 as has_permission
FROM t_sys_user_permissions up
WHERE up.user_id = $1 
  AND up.permission_code = $2 
  AND up.is_active = true
  AND (up.expires_at IS NULL OR up.expires_at > NOW());
*/

-- 优化后的查询（推荐使用）
-- 使用EXISTS替代COUNT，利用覆盖索引
CREATE OR REPLACE FUNCTION check_user_permission(
    p_user_id BIGINT,
    p_permission_code VARCHAR(255),
    p_resource_id VARCHAR(100) DEFAULT NULL
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 
        FROM t_sys_user_permissions up
        WHERE up.user_id = p_user_id 
          AND up.permission_code = p_permission_code
          AND (p_resource_id IS NULL OR up.resource_id = p_resource_id OR up.resource_id IS NULL)
          AND up.is_active = true
          AND (up.expires_at IS NULL OR up.expires_at > NOW())
        LIMIT 1
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- 1.2 角色权限验证查询优化
CREATE OR REPLACE FUNCTION check_role_permission(
    p_role_id BIGINT,
    p_permission_code VARCHAR(255),
    p_resource_type VARCHAR(100) DEFAULT NULL
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 
        FROM t_sys_role_permissions rp
        WHERE rp.role_id = p_role_id 
          AND rp.permission_code = p_permission_code
          AND (p_resource_type IS NULL OR rp.resource_type = p_resource_type OR rp.resource_type IS NULL)
          AND rp.is_active = true
        LIMIT 1
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- 1.3 用户通过角色的权限验证（复合查询优化）
CREATE OR REPLACE FUNCTION check_user_role_permission(
    p_user_id BIGINT,
    p_permission_code VARCHAR(255),
    p_resource_type VARCHAR(100) DEFAULT NULL
) RETURNS BOOLEAN AS $$
BEGIN
    -- 假设存在用户角色关联表
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 't_sys_user_roles') THEN
        RETURN EXISTS (
            SELECT 1 
            FROM t_sys_user_roles ur
            INNER JOIN t_sys_role_permissions rp ON ur.role_id = rp.role_id
            WHERE ur.user_id = p_user_id 
              AND rp.permission_code = p_permission_code
              AND (p_resource_type IS NULL OR rp.resource_type = p_resource_type OR rp.resource_type IS NULL)
              AND rp.is_active = true
            LIMIT 1
        );
    ELSE
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- 2. API权限验证查询优化
-- ============================================================================

-- 2.1 API端点权限验证
CREATE OR REPLACE FUNCTION check_api_permission(
    p_user_id BIGINT,
    p_api_path VARCHAR(500),
    p_http_method VARCHAR(10)
) RETURNS BOOLEAN AS $$
DECLARE
    v_permission_code VARCHAR(255);
    v_is_public BOOLEAN;
BEGIN
    -- 首先检查API是否为公开接口
    SELECT 
        CONCAT(ae.http_method, ' ', ae.api_path) as permission_code,
        ae.is_public
    INTO v_permission_code, v_is_public
    FROM t_sys_api_endpoints ae
    WHERE ae.api_path = p_api_path 
      AND ae.http_method = p_http_method
      AND ae.status = 'active'
      AND ae.is_deprecated = false
    LIMIT 1;
    
    -- 如果API不存在，拒绝访问
    IF v_permission_code IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- 如果是公开接口，允许访问
    IF v_is_public THEN
        RETURN TRUE;
    END IF;
    
    -- 检查用户直接权限
    IF check_user_permission(p_user_id, v_permission_code) THEN
        RETURN TRUE;
    END IF;
    
    -- 检查用户角色权限
    IF check_user_role_permission(p_user_id, v_permission_code) THEN
        RETURN TRUE;
    END IF;
    
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql STABLE;

-- 2.2 批量API权限检查（减少数据库往返）
CREATE OR REPLACE FUNCTION check_user_permissions_batch(
    p_user_id BIGINT,
    p_permission_codes VARCHAR(255)[]
) RETURNS TABLE(permission_code VARCHAR(255), has_permission BOOLEAN) AS $$
BEGIN
    RETURN QUERY
    WITH permission_list AS (
        SELECT unnest(p_permission_codes) as perm_code
    ),
    user_perms AS (
        SELECT up.permission_code
        FROM t_sys_user_permissions up
        WHERE up.user_id = p_user_id 
          AND up.permission_code = ANY(p_permission_codes)
          AND up.is_active = true
          AND (up.expires_at IS NULL OR up.expires_at > NOW())
    ),
    role_perms AS (
        SELECT rp.permission_code
        FROM t_sys_user_roles ur
        INNER JOIN t_sys_role_permissions rp ON ur.role_id = rp.role_id
        WHERE ur.user_id = p_user_id 
          AND rp.permission_code = ANY(p_permission_codes)
          AND rp.is_active = true
    )
    SELECT 
        pl.perm_code,
        CASE 
            WHEN up.permission_code IS NOT NULL OR rp.permission_code IS NOT NULL 
            THEN TRUE 
            ELSE FALSE 
        END as has_permission
    FROM permission_list pl
    LEFT JOIN user_perms up ON pl.perm_code = up.permission_code
    LEFT JOIN role_perms rp ON pl.perm_code = rp.permission_code;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- 3. 权限查询缓存优化
-- ============================================================================

-- 3.1 用户权限缓存视图（物化视图）
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_user_permissions_cache AS
SELECT 
    up.user_id,
    up.permission_code,
    up.resource_id,
    up.is_active,
    up.expires_at,
    up.granted_at,
    'direct' as permission_source
FROM t_sys_user_permissions up
WHERE up.is_active = true
  AND (up.expires_at IS NULL OR up.expires_at > NOW())

UNION ALL

SELECT 
    ur.user_id,
    rp.permission_code,
    rp.resource_type as resource_id,
    rp.is_active,
    NULL as expires_at,
    rp.created_at as granted_at,
    'role' as permission_source
FROM t_sys_user_roles ur
INNER JOIN t_sys_role_permissions rp ON ur.role_id = rp.role_id
WHERE rp.is_active = true;

-- 为物化视图创建索引
CREATE INDEX IF NOT EXISTS idx_mv_user_permissions_user_code 
ON mv_user_permissions_cache(user_id, permission_code);

CREATE INDEX IF NOT EXISTS idx_mv_user_permissions_user_active 
ON mv_user_permissions_cache(user_id, is_active);

-- 3.2 权限缓存刷新函数
CREATE OR REPLACE FUNCTION refresh_user_permissions_cache() RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_user_permissions_cache;
    
    -- 记录刷新时间
    INSERT INTO t_sys_cache_refresh_log (cache_name, refreshed_at)
    VALUES ('mv_user_permissions_cache', NOW())
    ON CONFLICT (cache_name) DO UPDATE SET
        refreshed_at = NOW(),
        refresh_count = t_sys_cache_refresh_log.refresh_count + 1;
END;
$$ LANGUAGE plpgsql;

-- 创建缓存刷新日志表
CREATE TABLE IF NOT EXISTS t_sys_cache_refresh_log (
    cache_name VARCHAR(100) PRIMARY KEY,
    refreshed_at TIMESTAMP DEFAULT NOW(),
    refresh_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- 4. 查询性能分析视图
-- ============================================================================

-- 4.1 权限查询性能统计视图
CREATE OR REPLACE VIEW v_permission_query_stats AS
SELECT 
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    n_tup_hot_upd,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables 
WHERE tablename IN ('t_sys_api_endpoints', 't_sys_user_permissions', 't_sys_role_permissions', 't_sys_user_roles');

-- 4.2 索引使用统计视图
CREATE OR REPLACE VIEW v_permission_index_stats AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename IN ('t_sys_api_endpoints', 't_sys_user_permissions', 't_sys_role_permissions', 't_sys_user_roles')
ORDER BY idx_scan DESC;

-- 4.3 慢查询分析（需要开启pg_stat_statements扩展）
CREATE OR REPLACE VIEW v_permission_slow_queries AS
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements 
WHERE query ILIKE '%t_sys_%permission%' 
   OR query ILIKE '%check_%permission%'
ORDER BY mean_time DESC
LIMIT 20;

-- ============================================================================
-- 5. 查询优化建议函数
-- ============================================================================

-- 5.1 权限表查询优化建议
CREATE OR REPLACE FUNCTION analyze_permission_query_performance() 
RETURNS TABLE(
    table_name TEXT,
    issue_type TEXT,
    description TEXT,
    recommendation TEXT
) AS $$
BEGIN
    RETURN QUERY
    -- 检查顺序扫描过多的表
    SELECT 
        t.tablename::TEXT,
        'high_seq_scan'::TEXT,
        format('表 %s 顺序扫描次数: %s, 索引扫描次数: %s', t.tablename, t.seq_scan, t.idx_scan)::TEXT,
        '考虑添加适当的索引或优化查询条件'::TEXT
    FROM pg_stat_user_tables t
    WHERE t.tablename IN ('t_sys_api_endpoints', 't_sys_user_permissions', 't_sys_role_permissions')
      AND t.seq_scan > t.idx_scan * 2
      AND t.seq_scan > 1000
    
    UNION ALL
    
    -- 检查未使用的索引
    SELECT 
        i.tablename::TEXT,
        'unused_index'::TEXT,
        format('索引 %s 很少被使用: 扫描次数 %s', i.indexname, i.idx_scan)::TEXT,
        '考虑删除未使用的索引以节省存储空间和提高写入性能'::TEXT
    FROM pg_stat_user_indexes i
    WHERE i.tablename IN ('t_sys_api_endpoints', 't_sys_user_permissions', 't_sys_role_permissions')
      AND i.idx_scan < 100
      AND i.indexname NOT LIKE '%_pkey'
    
    UNION ALL
    
    -- 检查需要VACUUM的表
    SELECT 
        t.tablename::TEXT,
        'need_vacuum'::TEXT,
        format('表 %s 死元组数量: %s, 活元组数量: %s', t.tablename, t.n_dead_tup, t.n_live_tup)::TEXT,
        '建议执行VACUUM操作清理死元组'::TEXT
    FROM pg_stat_user_tables t
    WHERE t.tablename IN ('t_sys_api_endpoints', 't_sys_user_permissions', 't_sys_role_permissions')
      AND t.n_dead_tup > t.n_live_tup * 0.1
      AND t.n_dead_tup > 1000;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 6. 性能测试查询
-- ============================================================================

-- 6.1 权限验证性能测试
CREATE OR REPLACE FUNCTION test_permission_query_performance(
    p_test_user_id BIGINT DEFAULT 1,
    p_iterations INTEGER DEFAULT 1000
) RETURNS TABLE(
    test_name TEXT,
    avg_time_ms NUMERIC,
    min_time_ms NUMERIC,
    max_time_ms NUMERIC,
    total_time_ms NUMERIC
) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    i INTEGER;
    times NUMERIC[];
    current_time NUMERIC;
BEGIN
    -- 测试1: 单个权限检查
    times := ARRAY[]::NUMERIC[];
    FOR i IN 1..p_iterations LOOP
        start_time := clock_timestamp();
        PERFORM check_user_permission(p_test_user_id, 'GET /api/v2/users');
        end_time := clock_timestamp();
        current_time := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;
        times := array_append(times, current_time);
    END LOOP;
    
    RETURN QUERY SELECT 
        'single_permission_check'::TEXT,
        (SELECT AVG(t) FROM unnest(times) t),
        (SELECT MIN(t) FROM unnest(times) t),
        (SELECT MAX(t) FROM unnest(times) t),
        (SELECT SUM(t) FROM unnest(times) t);
    
    -- 测试2: API权限检查
    times := ARRAY[]::NUMERIC[];
    FOR i IN 1..p_iterations LOOP
        start_time := clock_timestamp();
        PERFORM check_api_permission(p_test_user_id, '/api/v2/users', 'GET');
        end_time := clock_timestamp();
        current_time := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;
        times := array_append(times, current_time);
    END LOOP;
    
    RETURN QUERY SELECT 
        'api_permission_check'::TEXT,
        (SELECT AVG(t) FROM unnest(times) t),
        (SELECT MIN(t) FROM unnest(times) t),
        (SELECT MAX(t) FROM unnest(times) t),
        (SELECT SUM(t) FROM unnest(times) t);
    
    -- 测试3: 批量权限检查
    times := ARRAY[]::NUMERIC[];
    FOR i IN 1..p_iterations LOOP
        start_time := clock_timestamp();
        PERFORM * FROM check_user_permissions_batch(
            p_test_user_id, 
            ARRAY['GET /api/v2/users', 'POST /api/v2/users', 'PUT /api/v2/users/{id}']
        );
        end_time := clock_timestamp();
        current_time := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;
        times := array_append(times, current_time);
    END LOOP;
    
    RETURN QUERY SELECT 
        'batch_permission_check'::TEXT,
        (SELECT AVG(t) FROM unnest(times) t),
        (SELECT MIN(t) FROM unnest(times) t),
        (SELECT MAX(t) FROM unnest(times) t),
        (SELECT SUM(t) FROM unnest(times) t);
END;
$$ LANGUAGE plpgsql;

-- 显示优化完成信息
SELECT '✅ 权限验证SQL查询优化完成！' as status;