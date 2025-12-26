-- 数据库性能优化 - 优化权限验证SQL查询语句（简化版）
-- API权限重构项目 - 任务3.5
-- 创建时间: 2025-01-10

-- ============================================================================
-- 1. 权限验证核心查询优化
-- ============================================================================

-- 1.1 单个权限验证查询（最常用）
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
    
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql STABLE;

-- 2.2 批量权限检查（简化版）
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
    )
    SELECT 
        pl.perm_code,
        CASE 
            WHEN up.permission_code IS NOT NULL 
            THEN TRUE 
            ELSE FALSE 
        END as has_permission
    FROM permission_list pl
    LEFT JOIN user_perms up ON pl.perm_code = up.permission_code;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- 3. 查询性能分析视图
-- ============================================================================

-- 3.1 权限查询性能统计视图
CREATE OR REPLACE VIEW v_permission_query_stats AS
SELECT 
    schemaname,
    relname as tablename,
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
WHERE relname IN ('t_sys_api_endpoints', 't_sys_user_permissions', 't_sys_role_permissions');

-- 3.2 索引使用统计视图
CREATE OR REPLACE VIEW v_permission_index_stats AS
SELECT 
    schemaname,
    relname as tablename,
    indexrelname as indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE relname IN ('t_sys_api_endpoints', 't_sys_user_permissions', 't_sys_role_permissions')
ORDER BY idx_scan DESC;

-- ============================================================================
-- 4. 性能测试查询
-- ============================================================================

-- 4.1 权限验证性能测试
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
    exec_time NUMERIC;
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