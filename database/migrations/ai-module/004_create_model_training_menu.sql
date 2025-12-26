-- 004_create_model_training_menu.sql
-- Create Model Training menu and ensure parent AI Monitor menu exists

DO $$
DECLARE
    v_parent_id INTEGER;
    v_menu_id INTEGER;
    v_admin_role_id INTEGER;
BEGIN
    -- 1. Find or Create Parent Menu (/ai-monitor)
    SELECT id INTO v_parent_id FROM t_sys_menu WHERE path = '/ai-monitor';
    
    IF v_parent_id IS NULL THEN
        INSERT INTO t_sys_menu (
            name, path, component, menu_type, visible, status, icon, order_num, parent_id
        ) VALUES (
            'AI监控', '/ai-monitor', 'Layout', 'catalog', true, true, 'mdi:robot-outline', 3, 0
        ) RETURNING id INTO v_parent_id;
        RAISE NOTICE 'Created parent menu AI Monitor (ID: %)', v_parent_id;
    ELSE
        RAISE NOTICE 'Found existing parent menu AI Monitor (ID: %)', v_parent_id;
    END IF;

    -- 2. Create Model Training Menu
    SELECT id INTO v_menu_id FROM t_sys_menu WHERE path = '/ai-monitor/model-training';

    IF v_menu_id IS NULL THEN
        INSERT INTO t_sys_menu (
            name, path, component, menu_type, visible, status, icon, order_num, parent_id, perms, is_cache
        ) VALUES (
            '模型训练', 
            '/ai-monitor/model-training', 
            'ai-monitor/model-training/index', 
            'menu', 
            true, 
            true, 
            'mdi:school', 
            6, 
            v_parent_id, 
            'ai:model:training',
            true
        ) RETURNING id INTO v_menu_id;
        RAISE NOTICE 'Created Model Training menu (ID: %)', v_menu_id;
    ELSE
        RAISE NOTICE 'Model Training menu already exists (ID: %)', v_menu_id;
    END IF;

    -- 3. Assign to Admin Role
    -- Find admin role (usually id 1 or name 'admin' or '超级管理员')
    SELECT id INTO v_admin_role_id FROM t_sys_role WHERE role_key = 'admin' OR role_name = '超级管理员' LIMIT 1;
    
    IF v_admin_role_id IS NOT NULL THEN
        -- Check if permission already exists
        IF NOT EXISTS (SELECT 1 FROM t_role_menu WHERE role_id = v_admin_role_id AND menu_id = v_menu_id) THEN
            INSERT INTO t_role_menu (role_id, menu_id) VALUES (v_admin_role_id, v_menu_id);
            RAISE NOTICE 'Assigned permission to Admin role (ID: %)', v_admin_role_id;
        ELSE
            RAISE NOTICE 'Permission already exists for Admin role';
        END IF;
    ELSE
        RAISE WARNING 'Admin role not found';
    END IF;

END $$;
