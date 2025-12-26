-- ========================================
-- 插入通知管理菜单
-- 父菜单ID: 1 (系统管理)
-- ========================================

-- 直接插入，如果已存在则忽略
INSERT INTO t_sys_menu (
    menu_type, 
    name, 
    path, 
    order_num, 
    parent_id, 
    icon, 
    visible,
    status,
    component, 
    is_cache, 
    created_at, 
    updated_at
) 
SELECT 
    'menu', 
    '通知管理', 
    'notification', 
    15, 
    1, 
    'material-symbols:notifications', 
    true,
    true,
    '/system/notification', 
    true, 
    NOW(), 
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM t_sys_menu WHERE name = '通知管理' AND parent_id = 1
);
