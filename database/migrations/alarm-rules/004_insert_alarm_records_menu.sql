-- ========================================
-- 插入报警记录菜单
-- 父菜单ID: 28 (告警中心)
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
    '报警记录', 
    'alarm-records', 
    4, 
    28, 
    'material-symbols:history', 
    true,
    true,
    '/alarm/alarm-records', 
    true, 
    NOW(), 
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM t_sys_menu WHERE name = '报警记录' AND parent_id = 28
);
