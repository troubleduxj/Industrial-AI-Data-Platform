-- ========================================
-- 修复设备字段配置管理 - 新增按钮权限
-- ========================================
-- 确保超级管理员拥有新增设备字段的权限
-- 创建时间：2025-11-25
-- ========================================

BEGIN;

-- 1. 确保 POST /api/v2/device-fields API 权限存在
INSERT INTO t_api_permission (
    api_path, 
    api_method, 
    api_name, 
    api_group, 
    description, 
    is_public, 
    created_at, 
    updated_at
)
VALUES
(
    '/api/v2/device-fields', 
    'POST', 
    '创建设备字段', 
    '设备字段配置', 
    '创建设备字段配置', 
    false, 
    NOW(), 
    NOW()
)
ON CONFLICT (api_path, api_method) DO UPDATE SET
    api_name = EXCLUDED.api_name,
    api_group = EXCLUDED.api_group,
    description = EXCLUDED.description,
    updated_at = NOW();

-- 2. 获取 API 权限 ID
DO $$
DECLARE
    v_api_id INTEGER;
    v_role_id INTEGER;
BEGIN
    -- 获取 API 权限 ID
    SELECT id INTO v_api_id
    FROM t_api_permission
    WHERE api_path = '/api/v2/device-fields' AND api_method = 'POST';
    
    -- 为所有 admin 角色分配权限
    FOR v_role_id IN 
        SELECT id FROM t_role WHERE role_key = 'admin'
    LOOP
        -- 检查是否已存在
        IF NOT EXISTS (
            SELECT 1 FROM t_role_api 
            WHERE role_id = v_role_id AND api_id = v_api_id
        ) THEN
            -- 插入权限关联
            INSERT INTO t_role_api (role_id, api_id, created_at)
            VALUES (v_role_id, v_api_id, NOW());
            
            RAISE NOTICE '✓ 为角色 ID % 添加了 POST /api/v2/device-fields 权限', v_role_id;
        ELSE
            RAISE NOTICE '○ 角色 ID % 已有 POST /api/v2/device-fields 权限', v_role_id;
        END IF;
    END LOOP;
END $$;

-- 3. 同时确保其他相关 API 权限
INSERT INTO t_api_permission (
    api_path, api_method, api_name, api_group, description, is_public, created_at, updated_at
)
VALUES
('/api/v2/device-fields/{field_id}', 'PUT', '更新设备字段', '设备字段配置', '更新设备字段配置', false, NOW(), NOW()),
('/api/v2/device-fields/{field_id}', 'DELETE', '删除设备字段', '设备字段配置', '删除设备字段配置', false, NOW(), NOW()),
('/api/v2/device-fields/{field_id}', 'GET', '获取设备字段详情', '设备字段配置', '获取单个设备字段详情', false, NOW(), NOW()),
('/api/v2/device-fields/monitoring-keys/{device_type_code}', 'GET', '获取监测关键字段', '设备字段配置', '获取设备类型的监测关键字段配置', false, NOW(), NOW()),
('/api/v2/device-fields/cache/clear', 'POST', '清除字段缓存', '设备字段配置', '清除设备字段配置缓存', false, NOW(), NOW())
ON CONFLICT (api_path, api_method) DO UPDATE SET
    api_name = EXCLUDED.api_name,
    api_group = EXCLUDED.api_group,
    description = EXCLUDED.description,
    updated_at = NOW();

-- 4. 为所有超级管理员用户分配所有设备字段配置相关的 API 权限
INSERT INTO t_role_api (role_id, api_id, created_at)
SELECT r.id, a.id, NOW()
FROM t_role r
CROSS JOIN t_api_permission a
WHERE r.role_key = 'admin'
  AND a.api_group = '设备字段配置'
  AND NOT EXISTS (
    SELECT 1 FROM t_role_api ra
    WHERE ra.role_id = r.id AND ra.api_id = a.id
  );

COMMIT;

-- 5. 验证配置
SELECT '✅ 新增按钮权限修复完成！' as 状态;

-- 显示 POST 权限配置
SELECT 
    '权限详情' as 类型,
    api_path as API路径,
    api_method as 方法,
    api_name as 名称,
    api_group as 分组
FROM t_api_permission 
WHERE api_path = '/api/v2/device-fields' AND api_method = 'POST';

-- 显示管理员是否拥有该权限
SELECT 
    r.role_name as 角色名称,
    r.role_key as 角色标识,
    COUNT(ra.id) as 拥有权限数,
    CASE 
        WHEN COUNT(ra.id) > 0 THEN '✅ 已授权'
        ELSE '❌ 未授权'
    END as 授权状态
FROM t_role r
LEFT JOIN t_role_api ra ON r.id = ra.role_id
LEFT JOIN t_api_permission a ON ra.api_id = a.id
WHERE r.role_key = 'admin'
  AND (a.api_path = '/api/v2/device-fields' AND a.api_method = 'POST' OR a.id IS NULL)
GROUP BY r.id, r.role_name, r.role_key;

-- 显示所有设备字段配置相关权限
SELECT 
    '所有相关权限' as 说明,
    api_method as 方法,
    api_path as 路径,
    api_name as 名称
FROM t_api_permission 
WHERE api_group = '设备字段配置'
ORDER BY api_method, api_path;

