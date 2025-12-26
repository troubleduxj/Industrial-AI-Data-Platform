-- ============================================
-- 添加"统一配置管理"菜单
-- ============================================
-- 说明: 
-- 1. 在"元数据管理"下添加"统一配置管理"菜单
-- 2. 授予 admin 权限
-- ============================================

BEGIN;

DO $$
DECLARE
    v_meta_menu_id INTEGER;
    v_unified_menu_id INTEGER;
    v_admin_role_id INTEGER;
BEGIN
    -- 1. 获取 "元数据管理" 父菜单 ID
    SELECT id INTO v_meta_menu_id FROM t_sys_menu WHERE path = '/metadata' AND parent_id IS NULL;
    
    IF v_meta_menu_id IS NULL THEN
        RAISE EXCEPTION '未找到元数据管理菜单，请先执行 001_create_metadata_menu.sql';
    END IF;

    -- 2. 检查/创建 "统一配置管理" 菜单
    SELECT id INTO v_unified_menu_id FROM t_sys_menu WHERE path = '/metadata/unified';
    
    IF v_unified_menu_id IS NULL THEN
        INSERT INTO t_sys_menu (
            parent_id, name, path, icon, order_num, visible, menu_type, component, created_at, updated_at
        ) VALUES (
            v_meta_menu_id, 
            '统一配置管理', 
            '/metadata/unified', 
            'settings', 
            0, -- 排在最前面
            true, 
            'menu', 
            'metadata/unified/index', 
            NOW(), 
            NOW()
        ) RETURNING id INTO v_unified_menu_id;
        RAISE NOTICE '创建菜单: 统一配置管理 (ID: %)', v_unified_menu_id;
    ELSE
        UPDATE t_sys_menu SET
            name = '统一配置管理',
            icon = 'settings',
            order_num = 0,
            component = 'metadata/unified/index',
            visible = true,
            updated_at = NOW()
        WHERE id = v_unified_menu_id;
        RAISE NOTICE '更新菜单: 统一配置管理 (ID: %)', v_unified_menu_id;
    END IF;

    -- 3. 授予 admin 权限
    SELECT id INTO v_admin_role_id FROM t_sys_role WHERE role_key = 'admin';
    
    IF v_admin_role_id IS NOT NULL THEN
        INSERT INTO t_sys_role_menu (role_id, menu_id, created_at, updated_at)
        SELECT v_admin_role_id, v_unified_menu_id, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM t_sys_role_menu WHERE role_id = v_admin_role_id AND menu_id = v_unified_menu_id);
        
        RAISE NOTICE '已授予 admin 角色权限';
    END IF;

END $$;

COMMIT;
