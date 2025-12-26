-- ========================================
-- 添加报警规则配置菜单
-- ========================================

-- 先查看现有的报警相关菜单
SELECT id, name, path, menu_type, parent_id FROM t_sys_menu WHERE name LIKE '%报警%' OR name LIKE '%告警%' OR path LIKE '%alarm%';

-- 获取报警管理父菜单ID并插入报警规则菜单
DO $$
DECLARE
    v_parent_id BIGINT;
BEGIN
    -- 尝试多种方式查找父菜单
    -- 方式1: 按名称查找
    SELECT id INTO v_parent_id FROM t_sys_menu WHERE name IN ('报警管理', '告警管理', '告警中心') AND menu_type = 'catalog' LIMIT 1;
    
    -- 方式2: 如果没找到，按路径查找
    IF v_parent_id IS NULL THEN
        SELECT id INTO v_parent_id FROM t_sys_menu WHERE path = 'alarm' OR path = '/alarm' LIMIT 1;
    END IF;
    
    -- 方式3: 如果还没找到，查找包含alarm-info子菜单的父菜单
    IF v_parent_id IS NULL THEN
        SELECT parent_id INTO v_parent_id FROM t_sys_menu WHERE path = 'alarm-info' OR component LIKE '%alarm-info%' LIMIT 1;
    END IF;
    
    IF v_parent_id IS NOT NULL THEN
        RAISE NOTICE '找到父菜单ID: %', v_parent_id;
        
        -- 检查是否已存在
        IF NOT EXISTS (SELECT 1 FROM t_sys_menu WHERE name = '报警规则' AND parent_id = v_parent_id) THEN
            INSERT INTO t_sys_menu (
                menu_type, name, path, "order", parent_id, icon, is_hidden, component, keepalive, created_at, updated_at
            ) VALUES (
                'menu', '报警规则', 'alarm-rules', 3, v_parent_id, 'material-symbols:rule-settings', false, '/alarm/alarm-rules', false, NOW(), NOW()
            );
            RAISE NOTICE '✓ 报警规则菜单创建成功';
        ELSE
            RAISE NOTICE '⚠ 报警规则菜单已存在，跳过创建';
        END IF;
    ELSE
        RAISE NOTICE '⚠ 未找到报警管理父菜单，将创建完整的菜单结构';
        
        -- 创建报警管理父菜单
        INSERT INTO t_sys_menu (
            menu_type, name, path, "order", parent_id, icon, is_hidden, redirect, created_at, updated_at
        ) VALUES (
            'catalog', '报警管理', 'alarm', 5, 0, 'material-symbols:warning', false, '/alarm/alarm-rules', NOW(), NOW()
        ) RETURNING id INTO v_parent_id;
        
        RAISE NOTICE '✓ 创建报警管理父菜单，ID: %', v_parent_id;
        
        -- 创建报警规则子菜单
        INSERT INTO t_sys_menu (
            menu_type, name, path, "order", parent_id, icon, is_hidden, component, keepalive, created_at, updated_at
        ) VALUES (
            'menu', '报警规则', 'alarm-rules', 1, v_parent_id, 'material-symbols:rule-settings', false, '/alarm/alarm-rules', false, NOW(), NOW()
        );
        
        RAISE NOTICE '✓ 报警规则菜单创建成功';
    END IF;
END $$;

SELECT '✅ 报警规则菜单添加完成！' as status;

-- 验证结果
SELECT id, name, path, menu_type, parent_id, component FROM t_sys_menu WHERE name LIKE '%报警%' OR path LIKE '%alarm%' ORDER BY parent_id, "order";
