-- ========================================
-- 直接插入报警规则菜单
-- 父菜单ID: 28 (告警中心)
-- ========================================

-- 检查是否已存在，然后插入
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM t_sys_menu WHERE name = '报警规则' AND parent_id = 28) THEN
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
        ) VALUES (
            'menu', 
            '报警规则', 
            'alarm-rules', 
            3, 
            28, 
            'material-symbols:rule-settings', 
            true,
            true,
            '/alarm/alarm-rules', 
            true, 
            NOW(), 
            NOW()
        );
        RAISE NOTICE '✓ 报警规则菜单创建成功';
    ELSE
        RAISE NOTICE '⚠ 报警规则菜单已存在';
    END IF;
END $$;

-- 验证
SELECT id, name, path, menu_type, parent_id, component 
FROM t_sys_menu 
WHERE parent_id = 28 
ORDER BY order_num;
