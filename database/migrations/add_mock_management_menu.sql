-- 添加Mock数据管理菜单到高级设置分类下
-- 假设高级设置菜单的名称为"高级设置"或"系统设置"，需要根据实际情况调整

-- 方案1: 如果有"高级设置"菜单
DO $$
DECLARE
    parent_menu_id BIGINT;
    new_menu_id BIGINT;
BEGIN
    -- 查找"高级设置"菜单的ID（尝试多种可能的名称）
    SELECT id INTO parent_menu_id 
    FROM t_sys_menu 
    WHERE name IN ('高级设置', '系统设置', '系统配置', 'Advanced Settings')
      AND menu_type IN ('catalog', 'menu')
    LIMIT 1;
    
    -- 如果找不到，使用NULL（顶级菜单）
    IF parent_menu_id IS NULL THEN
        RAISE NOTICE '未找到"高级设置"菜单，将创建为顶级菜单';
        parent_menu_id := NULL;
    ELSE
        RAISE NOTICE '找到父菜单ID: %', parent_menu_id;
    END IF;
    
    -- 插入Mock管理菜单
    INSERT INTO t_sys_menu (
        name,
        path,
        component,
        menu_type,
        icon,
        order_num,
        parent_id,
        perms,
        visible,
        status,
        is_frame,
        is_cache,
        created_at,
        updated_at
    ) VALUES (
        'Mock数据管理',
        '/advanced-settings/mock-data',
        'advanced-settings/mock-data/index',
        'menu',
        'material-symbols:data-object',
        100,
        parent_menu_id,
        NULL,
        TRUE,
        TRUE,
        FALSE,
        TRUE,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    )
    RETURNING id INTO new_menu_id;
    
    RAISE NOTICE '✅ Mock管理菜单创建成功！菜单ID: %', new_menu_id;
    
    -- 返回结果
    RAISE NOTICE '菜单名称: Mock数据管理';
    RAISE NOTICE '路由路径: /advanced-settings/mock-data';
    RAISE NOTICE '组件路径: advanced-settings/mock-data/index';
    RAISE NOTICE '父菜单ID: %', COALESCE(parent_menu_id::TEXT, '无（顶级菜单）');
    
END $$;

-- 查询确认
SELECT 
    m.id,
    m.name,
    m.path,
    m.component,
    m.menu_type,
    m.parent_id,
    p.name as parent_name
FROM t_sys_menu m
LEFT JOIN t_sys_menu p ON m.parent_id = p.id
WHERE m.name = 'Mock数据管理';

