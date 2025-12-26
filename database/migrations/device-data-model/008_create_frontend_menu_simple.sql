-- ============================================
-- 数据模型管理 - 前端菜单创建脚本（简化版）
-- ============================================
-- 说明: 创建"数据模型管理"菜单及其子菜单
-- 创建日期: 2025-11-03
-- 版本: 2.0 - 使用正确的字段名
-- ============================================

BEGIN;

-- ============================================
-- 1. 创建根菜单
-- ============================================

DO $$
DECLARE
    v_parent_menu_id INTEGER;
    v_admin_role_id INTEGER;
BEGIN
    -- 查询根菜单是否存在
    SELECT id INTO v_parent_menu_id 
    FROM t_sys_menu 
    WHERE path = '/data-model';
    
    -- 如果不存在，创建根菜单
    IF v_parent_menu_id IS NULL THEN
        INSERT INTO t_sys_menu (
            parent_id, 
            name, 
            path, 
            icon, 
            order_num, 
            visible,
            menu_type
        ) VALUES (
            NULL,
            '数据模型管理',
            '/data-model',
            'database',
            50,
            true,
            'menu'
        ) RETURNING id INTO v_parent_menu_id;
        
        RAISE NOTICE '✓ 创建根菜单: 数据模型管理 (ID: %)', v_parent_menu_id;
    ELSE
        RAISE NOTICE '✓ 根菜单已存在 (ID: %)', v_parent_menu_id;
    END IF;
    
    -- ============================================
    -- 2. 创建子菜单
    -- ============================================
    
    -- 2.1 模型配置管理
    IF NOT EXISTS (SELECT 1 FROM t_sys_menu WHERE path = '/data-model/config') THEN
        INSERT INTO t_sys_menu (parent_id, name, path, icon, order_num, visible, menu_type)
        VALUES (v_parent_menu_id, '模型配置管理', '/data-model/config', 'settings', 1, true, 'menu');
        RAISE NOTICE '  ✓ 创建子菜单: 模型配置管理';
    END IF;
    
    -- 2.2 字段映射管理
    IF NOT EXISTS (SELECT 1 FROM t_sys_menu WHERE path = '/data-model/mapping') THEN
        INSERT INTO t_sys_menu (parent_id, name, path, icon, order_num, visible, menu_type)
        VALUES (v_parent_menu_id, '字段映射管理', '/data-model/mapping', 'link', 2, true, 'menu');
        RAISE NOTICE '  ✓ 创建子菜单: 字段映射管理';
    END IF;
    
    -- 2.3 预览与测试
    IF NOT EXISTS (SELECT 1 FROM t_sys_menu WHERE path = '/data-model/preview') THEN
        INSERT INTO t_sys_menu (parent_id, name, path, icon, order_num, visible, menu_type)
        VALUES (v_parent_menu_id, '预览与测试', '/data-model/preview', 'eye', 3, true, 'menu');
        RAISE NOTICE '  ✓ 创建子菜单: 预览与测试';
    END IF;
    
    -- ============================================
    -- 3. 为 admin 角色分配权限
    -- ============================================
    
    -- 查找 admin 角色
    SELECT id INTO v_admin_role_id 
    FROM t_sys_role 
    WHERE role_name LIKE '%管理员%' OR role_name LIKE '%admin%'
    LIMIT 1;
    
    IF v_admin_role_id IS NOT NULL THEN
        -- 为所有数据模型菜单分配权限
        INSERT INTO t_sys_role_menu (role_id, menu_id)
        SELECT v_admin_role_id, m.id
        FROM t_sys_menu m
        WHERE m.path LIKE '/data-model%'
        ON CONFLICT DO NOTHING;
        
        RAISE NOTICE '✓ 为 admin 角色分配权限';
    ELSE
        RAISE NOTICE '! 警告: 找不到 admin 角色';
    END IF;
    
    -- ============================================
    -- 4. 验证结果
    -- ============================================
    
    RAISE NOTICE '========================================';
    RAISE NOTICE '✓ 菜单创建完成！';
    RAISE NOTICE '========================================';
END $$;

COMMIT;

-- 查看创建结果
SELECT 
    m.id,
    m.parent_id,
    m.name,
    m.path,
    m.icon,
    m.order_num,
    m.visible
FROM t_sys_menu m
WHERE m.path LIKE '/data-model%'
ORDER BY COALESCE(m.parent_id, m.id), m.order_num;

