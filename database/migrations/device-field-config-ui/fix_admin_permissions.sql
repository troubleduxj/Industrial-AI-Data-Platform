-- ========================================
-- 修复管理员权限 - 设备字段配置管理
-- ========================================
-- 确保超级管理员拥有设备字段配置的所有权限
-- ========================================

BEGIN;

-- 1. 确保菜单存在
INSERT INTO t_menu (
    name, path, component, permission, parent_id, sort_order,
    icon, menu_type, is_visible, is_cache, created_at, updated_at
)
SELECT
    '设备字段配置',
    '/system/device-field',
    'system/device-field/index',
    'system:device-field:view',
    id,
    5,
    'SettingsOutline',
    'menu',
    true,
    true,
    NOW(),
    NOW()
FROM t_menu
WHERE name = '系统管理'
LIMIT 1
ON CONFLICT DO NOTHING;

-- 2. 确保 API 权限存在
INSERT INTO t_api_permission (
    api_path, api_method, api_name, api_group, description, is_public, created_at, updated_at
)
VALUES
('/api/v2/device-fields/monitoring-keys/{device_type_code}', 'GET', '获取监测关键字段', '设备字段配置', '获取设备类型的监测关键字段配置', false, NOW(), NOW()),
('/api/v2/device-fields', 'POST', '创建设备字段', '设备字段配置', '创建设备字段配置', false, NOW(), NOW()),
('/api/v2/device-fields/{field_id}', 'PUT', '更新设备字段', '设备字段配置', '更新设备字段配置', false, NOW(), NOW()),
('/api/v2/device-fields/{field_id}', 'DELETE', '删除设备字段', '设备字段配置', '删除设备字段配置', false, NOW(), NOW()),
('/api/v2/device-fields/cache/clear', 'POST', '清除字段缓存', '设备字段配置', '清除设备字段配置缓存', false, NOW(), NOW())
ON CONFLICT (api_path, api_method) DO UPDATE SET
    api_name = EXCLUDED.api_name,
    api_group = EXCLUDED.api_group,
    description = EXCLUDED.description,
    updated_at = NOW();

-- 3. 为所有超级管理员用户分配菜单权限
INSERT INTO t_role_menu (role_id, menu_id, created_at)
SELECT r.id, m.id, NOW()
FROM t_role r
CROSS JOIN t_menu m
WHERE r.role_key = 'admin'
  AND m.name = '设备字段配置'
  AND NOT EXISTS (
    SELECT 1 FROM t_role_menu rm
    WHERE rm.role_id = r.id AND rm.menu_id = m.id
  );

-- 4. 为所有超级管理员用户分配 API 权限
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
SELECT '✅ 权限修复完成！' as 状态;

-- 显示配置结果
SELECT '菜单' as 类型, name as 名称, path as 路径, permission as 权限标识 
FROM t_menu 
WHERE name = '设备字段配置'
UNION ALL
SELECT 'API' as 类型, api_name as 名称, api_path as 路径, api_method as 权限标识
FROM t_api_permission 
WHERE api_group = '设备字段配置'
ORDER BY 类型, 名称;

-- 显示管理员权限统计
SELECT 
    '管理员权限统计' as 说明,
    (SELECT COUNT(*) FROM t_role_menu rm 
     JOIN t_role r ON rm.role_id = r.id 
     JOIN t_menu m ON rm.menu_id = m.id 
     WHERE r.role_key = 'admin' AND m.name = '设备字段配置') as 菜单权限数,
    (SELECT COUNT(*) FROM t_role_api ra 
     JOIN t_role r ON ra.role_id = r.id 
     JOIN t_api_permission a ON ra.api_id = a.id 
     WHERE r.role_key = 'admin' AND a.api_group = '设备字段配置') as API权限数;
