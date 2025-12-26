-- 数据库性能优化 - 优化权限验证SQL查询语句（最小版）
-- API权限重构项目 - 任务3.5
-- 创建时间: 2025-01-10

-- ============================================================================
-- 1. 权限验证核心查询优化
-- ============================================================================

-- 1.1 单个权限验证查询
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

-- 1.2 角色权限验证查询
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

-- 1.3 API权限验证
CREATE OR REPLACE FUNCTION check_api_permission(
    p_user_id BIGINT,
    p_api_path VARCHAR(500),
    p_http_method VARCHAR(10)
) RETURNS BOOLEAN AS $$
DECLARE
    v_permission_code VARCHAR(255);
    v_is_public BOOLEAN;
BEGIN
    -- 检查API是否为公开接口
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
    RETURN check_user_permission(p_user_id, v_permission_code);
END;
$$ LANGUAGE plpgsql STABLE;

-- 显示优化完成信息
SELECT '✅ 权限验证SQL查询优化完成！' as status;