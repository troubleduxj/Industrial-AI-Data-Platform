-- ========================================
-- 设备字段配置管理界面 - 数据库配置脚本
-- ========================================
-- 功能：为设备字段配置管理界面添加菜单和权限
-- 执行：psql -U postgres -d devicemonitor -f setup.sql
-- ========================================

BEGIN;

-- 1. 添加菜单
INSERT INTO t_menu (
    name, path, component, permission, parent_id, sort_order,
    icon, menu_type, is_visible, is_cache, created_at, updated_at
)
SELECT
    '设备字段配置',
    '/system/device-field',
    'system/device-field/index',
    'system:device-field:view',
    id,  -- 系统管理菜单的 ID
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

-- 2. 添加 API 权限
INSERT INTO t_api_permission (
    api_path, api_method, api_name, api_group, description, is_public, created_at, updated_at
)
VALUES
('/api/v2/device-fields/monitoring-keys/{device_type_code}', 'GET', '获取监测关键字段', '设备字段配置', '获取设备类型的监测关键字段配置', false, NOW(), NOW()),
('/api/v2/device-fields', 'POST', '创建设备字段', '设备字段配置', '创建设备字段配置', false, NOW(), NOW()),
('/api/v2/device-fields/{field_id}', 'PUT', '更新设备字段', '设备字段配置', '更新设备字段配置', false, NOW(), NOW()),
('/api/v2/device-fields/{field_id}', 'DELETE', '删除设备字段', '设备字段配置', '删除设备字段配置', false, NOW(), NOW()),
('/api/v2/device-fields/cache/clear', 'POST', '清除字段缓存', '设备字段配置', '清除设备字段配置缓存', false, NOW(), NOW())
ON CONFLICT (api_path, api_method) DO NOTHING;

-- 3. 为管理员角色分配菜单权限
INSERT INTO t_role_menu (role_id, menu_id, created_at)
SELECT r.id, m.id, NOW()
FROM t_role r, t_menu m
WHERE r.role_key = 'admin'
  AND m.name = '设备字段配置'
  AND NOT EXISTS (
    SELECT 1 FROM t_role_menu rm
    WHERE rm.role_id = r.id AND rm.menu_id = m.id
  );

-- 4. 为管理员角色分配 API 权限
INSERT INTO t_role_api (role_id, api_id, created_at)
SELECT r.id, a.id, NOW()
FROM t_role r, t_api_permission a
WHERE r.role_key = 'admin'
  AND a.api_group = '设备字段配置'
  AND NOT EXISTS (
    SELECT 1 FROM t_role_api ra
    WHERE ra.role_id = r.id AND ra.api_id = a.id
  );

COMMIT;

-- 5. 验证配置
SELECT '✅ 配置完成！' as status;
SELECT '菜单配置' as type, name, path, permission FROM t_menu WHERE name = '设备字段配置'
UNION ALL
SELECT 'API权限' as type, api_name, api_path, api_method FROM t_api_permission WHERE api_group = '设备字段配置';
