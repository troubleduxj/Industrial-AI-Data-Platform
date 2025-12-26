-- ========================================
-- 修复设备字段配置管理 - 新增按钮权限 (V2)
-- ========================================
-- 使用正确的表名: t_sys_api_endpoints, t_sys_role_api
-- 创建时间：2025-11-25
-- ========================================

BEGIN;

-- 1. 确保 POST /api/v2/device-fields API 权限存在
INSERT INTO t_sys_api_endpoints (
    api_code,
    api_name, 
    api_path, 
    http_method,
    group_id,
    description,
    is_public,
    created_at, 
    updated_at
)
VALUES
(
    'device_field_create',
    '创建设备字段', 
    '/api/v2/device-fields', 
    'POST',
    (SELECT id FROM t_sys_api_groups WHERE group_code = 'device_field' LIMIT 1),
    '创建设备字段配置', 
    false, 
    NOW(), 
    NOW()
)
ON CONFLICT (api_path, http_method) DO UPDATE SET
    api_name = EXCLUDED.api_name,
    api_code = EXCLUDED.api_code,
    description = EXCLUDED.description,
    updated_at = NOW();

-- 2. 为所有 admin 角色分配权限
DO $$
DECLARE
    v_api_id BIGINT;
    v_role_id BIGINT;
    v_count INTEGER := 0;
BEGIN
    -- 获取 API 权限 ID
    SELECT id INTO v_api_id
    FROM t_sys_api_endpoints
    WHERE api_path = '/api/v2/device-fields' AND http_method = 'POST';
    
    IF v_api_id IS NULL THEN
        RAISE EXCEPTION 'API权限不存在: POST /api/v2/device-fields';
    END IF;
    
    -- 为所有 admin 角色分配权限
    FOR v_role_id IN 
        SELECT id FROM t_sys_role WHERE role_code = 'admin'
    LOOP
        -- 检查是否已存在
        IF NOT EXISTS (
            SELECT 1 FROM t_sys_role_api 
            WHERE role_id = v_role_id AND api_id = v_api_id
        ) THEN
            -- 插入权限关联
            INSERT INTO t_sys_role_api (role_id, api_id)
            VALUES (v_role_id, v_api_id);
            
            v_count := v_count + 1;
            RAISE NOTICE '✓ 为角色 ID % 添加了 POST /api/v2/device-fields 权限', v_role_id;
        ELSE
            RAISE NOTICE '○ 角色 ID % 已有 POST /api/v2/device-fields 权限', v_role_id;
        END IF;
    END LOOP;
    
    RAISE NOTICE '✅ 共为 % 个admin角色添加了权限', v_count;
END $$;

-- 3. 同时确保其他相关 API 权限存在
INSERT INTO t_sys_api_endpoints (
    api_code, api_name, api_path, http_method, group_id, description, is_public, created_at, updated_at
)
VALUES
('device_field_update', '更新设备字段', '/api/v2/device-fields/{field_id}', 'PUT', 
 (SELECT id FROM t_sys_api_groups WHERE group_code = 'device_field' LIMIT 1), 
 '更新设备字段配置', false, NOW(), NOW()),
 
('device_field_delete', '删除设备字段', '/api/v2/device-fields/{field_id}', 'DELETE', 
 (SELECT id FROM t_sys_api_groups WHERE group_code = 'device_field' LIMIT 1), 
 '删除设备字段配置', false, NOW(), NOW()),
 
('device_field_get', '获取设备字段详情', '/api/v2/device-fields/{field_id}', 'GET', 
 (SELECT id FROM t_sys_api_groups WHERE group_code = 'device_field' LIMIT 1), 
 '获取单个设备字段详情', false, NOW(), NOW()),
 
('device_field_monitoring_keys', '获取监测关键字段', '/api/v2/device-fields/monitoring-keys/{device_type_code}', 'GET', 
 (SELECT id FROM t_sys_api_groups WHERE group_code = 'device_field' LIMIT 1), 
 '获取设备类型的监测关键字段配置', false, NOW(), NOW()),
 
('device_field_cache_clear', '清除字段缓存', '/api/v2/device-fields/cache/clear', 'POST', 
 (SELECT id FROM t_sys_api_groups WHERE group_code = 'device_field' LIMIT 1), 
 '清除设备字段配置缓存', false, NOW(), NOW())
 
ON CONFLICT (api_path, http_method) DO UPDATE SET
    api_name = EXCLUDED.api_name,
    api_code = EXCLUDED.api_code,
    description = EXCLUDED.description,
    updated_at = NOW();

-- 4. 为所有超级管理员用户分配所有设备字段配置相关的 API 权限
INSERT INTO t_sys_role_api (role_id, api_id)
SELECT r.id, a.id
FROM t_sys_role r
CROSS JOIN t_sys_api_endpoints a
INNER JOIN t_sys_api_groups g ON a.group_id = g.id
WHERE r.role_code = 'admin'
  AND g.group_code = 'device_field'
  AND NOT EXISTS (
    SELECT 1 FROM t_sys_role_api ra
    WHERE ra.role_id = r.id AND ra.api_id = a.id
  );

COMMIT;

-- 5. 验证配置
SELECT '✅ 新增按钮权限修复完成！' as 状态;

-- 显示 POST 权限配置
SELECT 
    '权限详情' as 类型,
    api_code as API代码,
    api_path as API路径,
    http_method as 方法,
    api_name as 名称,
    g.group_name as 分组
FROM t_sys_api_endpoints a
LEFT JOIN t_sys_api_groups g ON a.group_id = g.id
WHERE api_path = '/api/v2/device-fields' AND http_method = 'POST';

-- 显示管理员是否拥有该权限
SELECT 
    r.role_name as 角色名称,
    r.role_code as 角色标识,
    COUNT(ra.api_id) as 拥有权限数,
    CASE 
        WHEN COUNT(ra.api_id) > 0 THEN '✅ 已授权'
        ELSE '❌ 未授权'
    END as 授权状态
FROM t_sys_role r
LEFT JOIN t_sys_role_api ra ON r.id = ra.role_id
LEFT JOIN t_sys_api_endpoints a ON ra.api_id = a.id
WHERE r.role_code = 'admin'
  AND (a.api_path = '/api/v2/device-fields' AND a.http_method = 'POST' OR a.id IS NULL)
GROUP BY r.id, r.role_name, r.role_code;

-- 显示所有设备字段配置相关权限
SELECT 
    '所有相关权限' as 说明,
    a.http_method as 方法,
    a.api_path as 路径,
    a.api_name as 名称,
    g.group_name as 分组
FROM t_sys_api_endpoints a
LEFT JOIN t_sys_api_groups g ON a.group_id = g.id
WHERE g.group_code = 'device_field'
ORDER BY a.http_method, a.api_path;
