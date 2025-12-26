-- ============================================
-- 数据模型管理 - 前端菜单创建脚本
-- ============================================
-- 说明: 创建"数据模型管理"一级菜单及其子菜单
-- 创建日期: 2025-11-03
-- 版本: 1.0
-- ============================================

-- 开始事务
BEGIN;

-- ============================================
-- 1. 创建一级菜单：数据模型管理
-- ============================================

-- 检查菜单是否已存在
DO $$
DECLARE
    v_menu_id INTEGER;
BEGIN
    -- 检查一级菜单是否已存在
    SELECT id INTO v_menu_id 
    FROM t_sys_menu 
    WHERE path = '/data-model' AND parent_id IS NULL;
    
    IF v_menu_id IS NULL THEN
        -- 插入一级菜单
        INSERT INTO t_sys_menu (
            parent_id, 
            name, 
            path, 
            icon, 
            sort_order, 
            is_visible,
            menu_type,
            component,
            created_at,
            updated_at
        ) VALUES (
            NULL,                           -- 一级菜单，parent_id 为 NULL
            '数据模型管理',                   -- 菜单名称
            '/data-model',                  -- 路由路径
            'database',                     -- 图标（使用常见图标名）
            50,                             -- 排序（放在中间位置）
            true,                           -- 可见
            'menu',                         -- 菜单类型
            'Layout',                       -- 使用布局组件
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        ) RETURNING id INTO v_menu_id;
        
        RAISE NOTICE '✓ 创建一级菜单: 数据模型管理 (ID: %)', v_menu_id;
    ELSE
        RAISE NOTICE '✓ 一级菜单已存在: 数据模型管理 (ID: %)', v_menu_id;
    END IF;
END $$;

-- ============================================
-- 2. 创建子菜单
-- ============================================

DO $$
DECLARE
    v_parent_id INTEGER;
    v_submenu_id INTEGER;
BEGIN
    -- 获取父菜单ID
    SELECT id INTO v_parent_id 
    FROM t_sys_menu 
    WHERE path = '/data-model' AND parent_id IS NULL;
    
    IF v_parent_id IS NULL THEN
        RAISE EXCEPTION '错误: 找不到父菜单 /data-model';
    END IF;
    
    -- ----------------------------------------
    -- 2.1 子菜单：模型配置管理
    -- ----------------------------------------
    SELECT id INTO v_submenu_id 
    FROM t_sys_menu 
    WHERE path = '/data-model/config' AND parent_id = v_parent_id;
    
    IF v_submenu_id IS NULL THEN
        INSERT INTO t_sys_menu (
            parent_id, 
            name, 
            path, 
            icon, 
            sort_order, 
            is_visible,
            menu_type,
            component,
            created_at,
            updated_at
        ) VALUES (
            v_parent_id,                    -- 父菜单ID
            '模型配置管理',                   -- 菜单名称
            '/data-model/config',           -- 路由路径
            'settings',                     -- 图标
            1,                              -- 排序
            true,                           -- 可见
            'menu',                         -- 菜单类型
            'data-model/config/index',      -- 组件路径
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        ) RETURNING id INTO v_submenu_id;
        
        RAISE NOTICE '  ✓ 创建子菜单: 模型配置管理 (ID: %)', v_submenu_id;
    ELSE
        RAISE NOTICE '  ✓ 子菜单已存在: 模型配置管理 (ID: %)', v_submenu_id;
    END IF;
    
    -- ----------------------------------------
    -- 2.2 子菜单：字段映射管理
    -- ----------------------------------------
    SELECT id INTO v_submenu_id 
    FROM t_sys_menu 
    WHERE path = '/data-model/mapping' AND parent_id = v_parent_id;
    
    IF v_submenu_id IS NULL THEN
        INSERT INTO t_sys_menu (
            parent_id, 
            name, 
            path, 
            icon, 
            sort_order, 
            is_visible,
            menu_type,
            component,
            created_at,
            updated_at
        ) VALUES (
            v_parent_id,
            '字段映射管理',
            '/data-model/mapping',
            'link',
            2,
            true,
            'menu',
            'data-model/mapping/index',
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        ) RETURNING id INTO v_submenu_id;
        
        RAISE NOTICE '  ✓ 创建子菜单: 字段映射管理 (ID: %)', v_submenu_id;
    ELSE
        RAISE NOTICE '  ✓ 子菜单已存在: 字段映射管理 (ID: %)', v_submenu_id;
    END IF;
    
    -- ----------------------------------------
    -- 2.3 子菜单：预览与测试
    -- ----------------------------------------
    SELECT id INTO v_submenu_id 
    FROM t_sys_menu 
    WHERE path = '/data-model/preview' AND parent_id = v_parent_id;
    
    IF v_submenu_id IS NULL THEN
        INSERT INTO t_sys_menu (
            parent_id, 
            name, 
            path, 
            icon, 
            sort_order, 
            is_visible,
            menu_type,
            component,
            created_at,
            updated_at
        ) VALUES (
            v_parent_id,
            '预览与测试',
            '/data-model/preview',
            'eye',
            3,
            true,
            'menu',
            'data-model/preview/index',
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        ) RETURNING id INTO v_submenu_id;
        
        RAISE NOTICE '  ✓ 创建子菜单: 预览与测试 (ID: %)', v_submenu_id;
    ELSE
        RAISE NOTICE '  ✓ 子菜单已存在: 预览与测试 (ID: %)', v_submenu_id;
    END IF;
END $$;

-- ============================================
-- 3. 为 admin 角色分配菜单权限
-- ============================================

DO $$
DECLARE
    v_admin_role_id INTEGER;
    v_menu_record RECORD;
    v_exists BOOLEAN;
BEGIN
    -- 获取 admin 角色ID
    SELECT id INTO v_admin_role_id 
    FROM t_role 
    WHERE role_code = 'admin' OR role_name = '超级管理员' 
    LIMIT 1;
    
    IF v_admin_role_id IS NULL THEN
        RAISE NOTICE '! 警告: 找不到 admin 角色，跳过权限分配';
        RETURN;
    END IF;
    
    RAISE NOTICE '✓ 找到 admin 角色 (ID: %)', v_admin_role_id;
    
    -- 为所有数据模型管理菜单分配权限
    FOR v_menu_record IN 
        SELECT id, name, path 
        FROM t_sys_menu 
        WHERE path LIKE '/data-model%'
    LOOP
        -- 检查权限是否已存在
        SELECT EXISTS(
            SELECT 1 
            FROM t_role_menu 
            WHERE role_id = v_admin_role_id 
            AND menu_id = v_menu_record.id
        ) INTO v_exists;
        
        IF NOT v_exists THEN
            INSERT INTO t_role_menu (role_id, menu_id, created_at, updated_at)
            VALUES (
                v_admin_role_id, 
                v_menu_record.id,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            );
            
            RAISE NOTICE '  ✓ 为 admin 分配权限: % (%)', v_menu_record.name, v_menu_record.path;
        ELSE
            RAISE NOTICE '  ✓ admin 权限已存在: % (%)', v_menu_record.name, v_menu_record.path;
        END IF;
    END LOOP;
END $$;

-- ============================================
-- 4. 验证创建结果
-- ============================================

DO $$
DECLARE
    v_menu_count INTEGER;
    v_permission_count INTEGER;
BEGIN
    -- 统计创建的菜单数量
    SELECT COUNT(*) INTO v_menu_count 
    FROM t_sys_menu 
    WHERE path LIKE '/data-model%';
    
    -- 统计分配的权限数量
    SELECT COUNT(*) INTO v_permission_count 
    FROM t_role_menu rm
    JOIN t_sys_menu m ON rm.menu_id = m.id
    WHERE m.path LIKE '/data-model%';
    
    RAISE NOTICE '========================================';
    RAISE NOTICE '✓ 菜单创建完成！';
    RAISE NOTICE '  - 创建菜单数量: %', v_menu_count;
    RAISE NOTICE '  - 权限分配数量: %', v_permission_count;
    RAISE NOTICE '========================================';
END $$;

-- 提交事务
COMMIT;

-- ============================================
-- 验证查询（可选执行）
-- ============================================

-- 查看创建的菜单
SELECT 
    m.id,
    m.parent_id,
    m.name,
    m.path,
    m.icon,
    m.sort_order,
    m.is_visible,
    m.component
FROM t_sys_menu m
WHERE m.path LIKE '/data-model%'
ORDER BY 
    COALESCE(m.parent_id, m.id),
    m.sort_order;

-- 查看 admin 角色的权限
SELECT 
    r.role_name,
    m.name AS menu_name,
    m.path,
    m.component
FROM t_role_menu rm
JOIN t_role r ON rm.role_id = r.id
JOIN t_sys_menu m ON rm.menu_id = m.id
WHERE m.path LIKE '/data-model%'
ORDER BY m.sort_order;

