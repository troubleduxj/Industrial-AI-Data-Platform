-- 将主题管理和组件管理从系统设置移动到高级设置
-- 日期: 2025-10-30

-- 查看当前菜单结构
SELECT 
    m.id, 
    m.name as "菜单名称", 
    m.parent_id as "父ID",
    p.name as "父菜单名称",
    m.sort as "排序",
    m.component as "组件路径"
FROM t_sys_menu m
LEFT JOIN t_sys_menu p ON m.parent_id = p.id
WHERE m.name IN ('系统设置', '高级设置', '主题管理', '组件管理', 'Mock数据管理')
ORDER BY m.parent_id NULLS FIRST, m.sort;

-- 开始事务
BEGIN;

-- 获取高级设置的ID
DO $$
DECLARE
    v_advanced_settings_id INTEGER;
    v_theme_mgmt_id INTEGER;
    v_component_mgmt_id INTEGER;
    v_mock_data_id INTEGER;
BEGIN
    -- 查找高级设置菜单ID
    SELECT id INTO v_advanced_settings_id 
    FROM t_sys_menu 
    WHERE name = '高级设置';
    
    IF v_advanced_settings_id IS NULL THEN
        RAISE EXCEPTION '未找到"高级设置"菜单';
    END IF;
    
    RAISE NOTICE '高级设置菜单ID: %', v_advanced_settings_id;
    
    -- 查找主题管理菜单ID并更新
    SELECT id INTO v_theme_mgmt_id 
    FROM t_sys_menu 
    WHERE name = '主题管理';
    
    IF v_theme_mgmt_id IS NOT NULL THEN
        UPDATE t_sys_menu 
        SET parent_id = v_advanced_settings_id, 
            sort = 200
        WHERE id = v_theme_mgmt_id;
        RAISE NOTICE '✓ 已将"主题管理" (ID: %) 移动到"高级设置"，排序: 200', v_theme_mgmt_id;
    ELSE
        RAISE NOTICE '⚠ 未找到"主题管理"菜单';
    END IF;
    
    -- 查找组件管理菜单ID并更新
    SELECT id INTO v_component_mgmt_id 
    FROM t_sys_menu 
    WHERE name = '组件管理';
    
    IF v_component_mgmt_id IS NOT NULL THEN
        UPDATE t_sys_menu 
        SET parent_id = v_advanced_settings_id, 
            sort = 300
        WHERE id = v_component_mgmt_id;
        RAISE NOTICE '✓ 已将"组件管理" (ID: %) 移动到"高级设置"，排序: 300', v_component_mgmt_id;
    ELSE
        RAISE NOTICE '⚠ 未找到"组件管理"菜单';
    END IF;
    
    -- 更新Mock数据管理的排序
    SELECT id INTO v_mock_data_id 
    FROM t_sys_menu 
    WHERE name = 'Mock数据管理';
    
    IF v_mock_data_id IS NOT NULL THEN
        UPDATE t_sys_menu 
        SET sort = 100
        WHERE id = v_mock_data_id;
        RAISE NOTICE '✓ 已更新"Mock数据管理" (ID: %) 排序: 100', v_mock_data_id;
    END IF;
    
END $$;

-- 提交事务
COMMIT;

-- 查看更新后的菜单结构
SELECT 
    m.id, 
    m.name as "菜单名称", 
    m.parent_id as "父ID",
    p.name as "父菜单名称",
    m.sort as "排序",
    m.component as "组件路径"
FROM t_sys_menu m
LEFT JOIN t_sys_menu p ON m.parent_id = p.id
WHERE m.name IN ('高级设置', '主题管理', '组件管理', 'Mock数据管理')
   OR m.id = (SELECT id FROM t_sys_menu WHERE name = '高级设置')
ORDER BY m.parent_id NULLS FIRST, m.sort;

-- 验证高级设置的子菜单数量
SELECT 
    '高级设置子菜单统计' as "统计项",
    COUNT(*) as "子菜单数量"
FROM t_sys_menu
WHERE parent_id = (SELECT id FROM t_sys_menu WHERE name = '高级设置');

