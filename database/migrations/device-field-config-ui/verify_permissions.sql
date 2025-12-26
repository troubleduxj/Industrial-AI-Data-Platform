-- ========================================
-- 验证设备字段配置管理的权限配置
-- ========================================

-- 1. 检查菜单是否存在
SELECT 
    '菜单配置' as 检查项,
    CASE WHEN COUNT(*) > 0 THEN '✅ 已配置' ELSE '❌ 未配置' END as 状态,
    COUNT(*) as 数量
FROM t_menu 
WHERE name = '设备字段配置';

-- 2. 检查 API 权限是否存在
SELECT 
    'API权限' as 检查项,
    CASE WHEN COUNT(*) >= 5 THEN '✅ 已配置' ELSE '❌ 未配置' END as 状态,
    COUNT(*) as 数量
FROM t_api_permission 
WHERE api_group = '设备字段配置';

-- 3. 检查管理员角色的菜单权限
SELECT 
    '管理员菜单权限' as 检查项,
    CASE WHEN COUNT(*) > 0 THEN '✅ 已配置' ELSE '❌ 未配置' END as 状态,
    COUNT(*) as 数量
FROM t_role_menu rm
JOIN t_role r ON rm.role_id = r.id
JOIN t_menu m ON rm.menu_id = m.id
WHERE r.role_key = 'admin' AND m.name = '设备字段配置';

-- 4. 检查管理员角色的 API 权限
SELECT 
    '管理员API权限' as 检查项,
    CASE WHEN COUNT(*) >= 5 THEN '✅ 已配置' ELSE '❌ 未配置' END as 状态,
    COUNT(*) as 数量
FROM t_role_api ra
JOIN t_role r ON ra.role_id = r.id
JOIN t_api_permission a ON ra.api_id = a.id
WHERE r.role_key = 'admin' AND a.api_group = '设备字段配置';

-- 5. 列出所有相关的 API 权限
SELECT 
    api_name as API名称,
    api_method as 方法,
    api_path as 路径,
    is_public as 是否公开
FROM t_api_permission 
WHERE api_group = '设备字段配置'
ORDER BY api_method, api_path;
