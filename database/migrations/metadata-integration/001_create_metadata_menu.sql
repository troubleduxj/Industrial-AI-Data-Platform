-- ============================================
-- 元数据管理 - 前端菜单迁移脚本
-- ============================================
-- 说明: 
-- 1. 创建"元数据管理"一级菜单 (Category)
-- 2. 迁移"数据模型管理"到"元数据管理"下
-- 3. 迁移"设备字段配置"到"元数据管理"下
-- 4. 清理旧的菜单入口
-- 创建日期: 2025-12-01
-- ============================================

BEGIN;

-- 1. 创建一级菜单：元数据管理 (/metadata)
DO $$
DECLARE
    v_meta_menu_id INTEGER;
    v_sys_menu_id INTEGER;
    v_data_model_id INTEGER;
    v_field_config_id INTEGER;
    v_admin_role_id INTEGER;
BEGIN
    -- ------------------------------------------------
    -- 1.1 创建/获取 "元数据管理" 一级菜单
    -- ------------------------------------------------
    SELECT id INTO v_meta_menu_id FROM t_sys_menu WHERE path = '/metadata' AND parent_id IS NULL;
    
    IF v_meta_menu_id IS NULL THEN
        INSERT INTO t_sys_menu (
            parent_id, name, path, icon, order_num, visible, menu_type, component, created_at, updated_at
        ) VALUES (
            NULL, 
            '元数据管理', 
            '/metadata', 
            'database', 
            20, 
            true, 
            'catalog', -- 目录类型
            'Layout', 
            NOW(), 
            NOW()
        ) RETURNING id INTO v_meta_menu_id;
        RAISE NOTICE '创建一级菜单: 元数据管理 (ID: %)', v_meta_menu_id;
    ELSE
        -- 更新现有菜单属性确保一致性
        UPDATE t_sys_menu SET 
            name = '元数据管理',
            icon = 'database',
            order_num = 20,
            menu_type = 'catalog',
            component = 'Layout',
            updated_at = NOW()
        WHERE id = v_meta_menu_id;
        RAISE NOTICE '更新一级菜单: 元数据管理 (ID: %)', v_meta_menu_id;
    END IF;

    -- ------------------------------------------------
    -- 1.2 迁移 "数据模型管理" (/data-model -> /metadata/models)
    -- ------------------------------------------------
    SELECT id INTO v_data_model_id FROM t_sys_menu WHERE path = '/data-model';
    
    IF v_data_model_id IS NOT NULL THEN
        -- 更新父ID和路径
        UPDATE t_sys_menu SET 
            parent_id = v_meta_menu_id,
            path = '/metadata/models',
            name = '数据模型管理',
            icon = 'chart-graph',
            order_num = 2,
            menu_type = 'menu',
            component = 'data-model/config/index', -- 指向配置页作为主入口
            updated_at = NOW()
        WHERE id = v_data_model_id;
        
        -- 更新子菜单路径前缀
        UPDATE t_sys_menu SET 
            path = REPLACE(path, '/data-model/', '/metadata/models/')
        WHERE parent_id = v_data_model_id;
        
        RAISE NOTICE '迁移数据模型管理到新结构 (ID: %)', v_data_model_id;
    ELSE
        -- 如果不存在则创建
        INSERT INTO t_sys_menu (
            parent_id, name, path, icon, order_num, visible, menu_type, component, created_at, updated_at
        ) VALUES (
            v_meta_menu_id,
            '数据模型管理',
            '/metadata/models',
            'chart-graph',
            2,
            true,
            'menu',
            'data-model/config/index',
            NOW(),
            NOW()
        ) RETURNING id INTO v_data_model_id;
        RAISE NOTICE '创建数据模型管理菜单 (ID: %)', v_data_model_id;
    END IF;

    -- ------------------------------------------------
    -- 1.3 迁移 "设备字段配置" (原 /system/device-field -> /metadata/fields)
    -- ------------------------------------------------
    -- 查找旧的字段配置菜单 (可能在系统管理下)
    SELECT id INTO v_field_config_id FROM t_sys_menu WHERE path = '/system/device-field';
    
    IF v_field_config_id IS NOT NULL THEN
        UPDATE t_sys_menu SET 
            parent_id = v_meta_menu_id,
            path = '/metadata/fields',
            name = '字段配置管理',
            icon = 'list',
            order_num = 1,
            menu_type = 'menu',
            component = 'metadata/fields/index', -- 使用新组件路径
            updated_at = NOW()
        WHERE id = v_field_config_id;
        RAISE NOTICE '迁移字段配置管理到新结构 (ID: %)', v_field_config_id;
    ELSE
        -- 检查是否已经存在于新位置
        SELECT id INTO v_field_config_id FROM t_sys_menu WHERE path = '/metadata/fields';
        
        IF v_field_config_id IS NULL THEN
            INSERT INTO t_sys_menu (
                parent_id, name, path, icon, order_num, visible, menu_type, component, created_at, updated_at
            ) VALUES (
                v_meta_menu_id,
                '字段配置管理',
                '/metadata/fields',
                'list',
                1,
                true,
                'menu',
                'metadata/fields/index',
                NOW(),
                NOW()
            ) RETURNING id INTO v_field_config_id;
            RAISE NOTICE '创建字段配置管理菜单 (ID: %)', v_field_config_id;
        ELSE
            RAISE NOTICE '字段配置管理菜单已存在 (ID: %)', v_field_config_id;
        END IF;
    END IF;

    -- ------------------------------------------------
    -- 1.4 确保 admin 角色拥有新菜单权限
    -- ------------------------------------------------
    SELECT id INTO v_admin_role_id FROM t_sys_role WHERE role_key = 'admin';
    
    IF v_admin_role_id IS NOT NULL THEN
        -- 授予一级菜单权限
        INSERT INTO t_sys_role_menu (role_id, menu_id, created_at, updated_at)
        SELECT v_admin_role_id, v_meta_menu_id, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM t_sys_role_menu WHERE role_id = v_admin_role_id AND menu_id = v_meta_menu_id);
        
        -- 授予子菜单权限
        INSERT INTO t_sys_role_menu (role_id, menu_id, created_at, updated_at)
        SELECT v_admin_role_id, id, NOW(), NOW()
        FROM t_sys_menu 
        WHERE parent_id = v_meta_menu_id
        AND NOT EXISTS (SELECT 1 FROM t_sys_role_menu WHERE role_id = v_admin_role_id AND menu_id = t_sys_menu.id);
        
        -- 授予孙子菜单权限 (如果有)
        INSERT INTO t_sys_role_menu (role_id, menu_id, created_at, updated_at)
        SELECT v_admin_role_id, id, NOW(), NOW()
        FROM t_sys_menu 
        WHERE parent_id IN (SELECT id FROM t_sys_menu WHERE parent_id = v_meta_menu_id)
        AND NOT EXISTS (SELECT 1 FROM t_sys_role_menu WHERE role_id = v_admin_role_id AND menu_id = t_sys_menu.id);
        
        RAISE NOTICE '已刷新 admin 角色权限';
    END IF;

END $$;

COMMIT;
