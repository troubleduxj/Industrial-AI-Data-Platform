-- 按钮权限初始化SQL脚本 (PostgreSQL版本)
-- 为系统中的主要页面创建按钮级别的权限控制
-- 执行时间: 2025-10-29

-- ============================================================
-- 用户管理页面的按钮权限
-- ============================================================

DO $$
DECLARE
    user_menu_id INTEGER;
    role_menu_id INTEGER;
    menu_menu_id INTEGER;
    dept_menu_id INTEGER;
    device_menu_id INTEGER;
    repair_menu_id INTEGER;
    dict_type_menu_id INTEGER;
    dict_data_menu_id INTEGER;
BEGIN
    -- 查找用户管理菜单的ID
    SELECT id INTO user_menu_id FROM t_sys_menu WHERE name = '用户管理' AND menu_type = 'menu' LIMIT 1;
    
    IF user_menu_id IS NOT NULL THEN
        -- 新建用户
        INSERT INTO t_sys_menu (
            name, path, component, menu_type, icon, order_num, 
            parent_id, perms, visible, status, is_frame, is_cache
        ) VALUES (
            '新建用户', '', '', 'button', 'material-symbols:add', 1,
            user_menu_id, 'POST /api/v2/users', true, true, false, false
        ) ON CONFLICT DO NOTHING;

        -- 编辑用户
        INSERT INTO t_sys_menu (
            name, path, component, menu_type, icon, order_num, 
            parent_id, perms, visible, status, is_frame, is_cache
        ) VALUES (
            '编辑用户', '', '', 'button', 'material-symbols:edit', 2,
            user_menu_id, 'PUT /api/v2/users/{id}', true, true, false, false
        ) ON CONFLICT DO NOTHING;

        -- 删除用户
        INSERT INTO t_sys_menu (
            name, path, component, menu_type, icon, order_num, 
            parent_id, perms, visible, status, is_frame, is_cache
        ) VALUES (
            '删除用户', '', '', 'button', 'material-symbols:delete', 3,
            user_menu_id, 'DELETE /api/v2/users/{id}', true, true, false, false
        ) ON CONFLICT DO NOTHING;

        -- 重置密码
        INSERT INTO t_sys_menu (
            name, path, component, menu_type, icon, order_num, 
            parent_id, perms, visible, status, is_frame, is_cache
        ) VALUES (
            '重置密码', '', '', 'button', 'material-symbols:lock-reset', 4,
            user_menu_id, 'POST /api/v2/users/{id}/actions/reset-password', true, true, false, false
        ) ON CONFLICT DO NOTHING;

        -- 批量删除用户
        INSERT INTO t_sys_menu (
            name, path, component, menu_type, icon, order_num, 
            parent_id, perms, visible, status, is_frame, is_cache
        ) VALUES (
            '批量删除用户', '', '', 'button', 'material-symbols:delete-sweep', 5,
            user_menu_id, 'DELETE /api/v2/users/batch', true, true, false, false
        ) ON CONFLICT DO NOTHING;

        -- 导出用户
        INSERT INTO t_sys_menu (
            name, path, component, menu_type, icon, order_num, 
            parent_id, perms, visible, status, is_frame, is_cache
        ) VALUES (
            '导出用户', '', '', 'button', 'material-symbols:download', 6,
            user_menu_id, 'GET /api/v2/users/export', true, true, false, false
        ) ON CONFLICT DO NOTHING;
        
        RAISE NOTICE '✅ 用户管理按钮权限创建完成 (6个)';
    ELSE
        RAISE NOTICE '⚠️  未找到"用户管理"菜单';
    END IF;

    -- ============================================================
    -- 角色管理页面的按钮权限
    -- ============================================================
    
    SELECT id INTO role_menu_id FROM t_sys_menu WHERE name = '角色管理' AND menu_type = 'menu' LIMIT 1;
    
    IF role_menu_id IS NOT NULL THEN
        INSERT INTO t_sys_menu (
            name, path, component, menu_type, icon, order_num, 
            parent_id, perms, visible, status, is_frame, is_cache
        ) VALUES 
            ('新建角色', '', '', 'button', 'material-symbols:add', 1,
             role_menu_id, 'POST /api/v2/roles', true, true, false, false),
            ('编辑角色', '', '', 'button', 'material-symbols:edit', 2,
             role_menu_id, 'PUT /api/v2/roles/{id}', true, true, false, false),
            ('删除角色', '', '', 'button', 'material-symbols:delete', 3,
             role_menu_id, 'DELETE /api/v2/roles/{id}', true, true, false, false),
            ('分配权限', '', '', 'button', 'material-symbols:key', 4,
             role_menu_id, 'POST /api/v2/roles/{id}/permissions', true, true, false, false)
        ON CONFLICT DO NOTHING;
        
        RAISE NOTICE '✅ 角色管理按钮权限创建完成 (4个)';
    ELSE
        RAISE NOTICE '⚠️  未找到"角色管理"菜单';
    END IF;

    -- ============================================================
    -- 菜单管理页面的按钮权限
    -- ============================================================
    
    SELECT id INTO menu_menu_id FROM t_sys_menu WHERE name = '菜单管理' AND menu_type = 'menu' LIMIT 1;
    
    IF menu_menu_id IS NOT NULL THEN
        INSERT INTO t_sys_menu (
            name, path, component, menu_type, icon, order_num, 
            parent_id, perms, visible, status, is_frame, is_cache
        ) VALUES 
            ('新建菜单', '', '', 'button', 'material-symbols:add', 1,
             menu_menu_id, 'POST /api/v2/menus', true, true, false, false),
            ('编辑菜单', '', '', 'button', 'material-symbols:edit', 2,
             menu_menu_id, 'PUT /api/v2/menus/{id}', true, true, false, false),
            ('删除菜单', '', '', 'button', 'material-symbols:delete', 3,
             menu_menu_id, 'DELETE /api/v2/menus/{id}', true, true, false, false)
        ON CONFLICT DO NOTHING;
        
        RAISE NOTICE '✅ 菜单管理按钮权限创建完成 (3个)';
    ELSE
        RAISE NOTICE '⚠️  未找到"菜单管理"菜单';
    END IF;

    -- ============================================================
    -- 部门管理页面的按钮权限
    -- ============================================================
    
    SELECT id INTO dept_menu_id FROM t_sys_menu WHERE name = '部门管理' AND menu_type = 'menu' LIMIT 1;
    
    IF dept_menu_id IS NOT NULL THEN
        INSERT INTO t_sys_menu (
            name, path, component, menu_type, icon, order_num, 
            parent_id, perms, visible, status, is_frame, is_cache
        ) VALUES 
            ('新建部门', '', '', 'button', 'material-symbols:add', 1,
             dept_menu_id, 'POST /api/v2/departments', true, true, false, false),
            ('编辑部门', '', '', 'button', 'material-symbols:edit', 2,
             dept_menu_id, 'PUT /api/v2/departments/{id}', true, true, false, false),
            ('删除部门', '', '', 'button', 'material-symbols:delete', 3,
             dept_menu_id, 'DELETE /api/v2/departments/{id}', true, true, false, false)
        ON CONFLICT DO NOTHING;
        
        RAISE NOTICE '✅ 部门管理按钮权限创建完成 (3个)';
    ELSE
        RAISE NOTICE '⚠️  未找到"部门管理"菜单';
    END IF;

    -- ============================================================
    -- 设备管理页面的按钮权限
    -- ============================================================
    
    SELECT id INTO device_menu_id FROM t_sys_menu WHERE name = '设备基础信息' AND menu_type = 'menu' LIMIT 1;
    
    IF device_menu_id IS NOT NULL THEN
        INSERT INTO t_sys_menu (
            name, path, component, menu_type, icon, order_num, 
            parent_id, perms, visible, status, is_frame, is_cache
        ) VALUES 
            ('新建设备', '', '', 'button', 'material-symbols:add', 1,
             device_menu_id, 'POST /api/v2/devices', true, true, false, false),
            ('编辑设备', '', '', 'button', 'material-symbols:edit', 2,
             device_menu_id, 'PUT /api/v2/devices/{id}', true, true, false, false),
            ('删除设备', '', '', 'button', 'material-symbols:delete', 3,
             device_menu_id, 'DELETE /api/v2/devices/{id}', true, true, false, false),
            ('导出设备', '', '', 'button', 'material-symbols:download', 4,
             device_menu_id, 'GET /api/v2/devices/export', true, true, false, false)
        ON CONFLICT DO NOTHING;
        
        RAISE NOTICE '✅ 设备管理按钮权限创建完成 (4个)';
    ELSE
        RAISE NOTICE '⚠️  未找到"设备基础信息"菜单';
    END IF;

    -- ============================================================
    -- 维修记录页面的按钮权限
    -- ============================================================
    
    SELECT id INTO repair_menu_id FROM t_sys_menu WHERE name = '维修记录' AND menu_type = 'menu' LIMIT 1;
    
    IF repair_menu_id IS NOT NULL THEN
        INSERT INTO t_sys_menu (
            name, path, component, menu_type, icon, order_num, 
            parent_id, perms, visible, status, is_frame, is_cache
        ) VALUES 
            ('新建维修记录', '', '', 'button', 'material-symbols:add', 1,
             repair_menu_id, 'POST /api/v2/device/maintenance/repair-records', true, true, false, false),
            ('编辑维修记录', '', '', 'button', 'material-symbols:edit', 2,
             repair_menu_id, 'PUT /api/v2/device/maintenance/repair-records/{id}', true, true, false, false),
            ('删除维修记录', '', '', 'button', 'material-symbols:delete', 3,
             repair_menu_id, 'DELETE /api/v2/device/maintenance/repair-records/{id}', true, true, false, false),
            ('导出维修记录', '', '', 'button', 'material-symbols:download', 4,
             repair_menu_id, 'GET /api/v2/device/maintenance/repair-records/export', true, true, false, false)
        ON CONFLICT DO NOTHING;
        
        RAISE NOTICE '✅ 维修记录按钮权限创建完成 (4个)';
    ELSE
        RAISE NOTICE '⚠️  未找到"维修记录"菜单';
    END IF;

    -- ============================================================
    -- 字典类型管理页面的按钮权限
    -- ============================================================
    
    SELECT id INTO dict_type_menu_id FROM t_sys_menu WHERE name = '字典类型' AND menu_type = 'menu' LIMIT 1;
    
    IF dict_type_menu_id IS NOT NULL THEN
        INSERT INTO t_sys_menu (
            name, path, component, menu_type, icon, order_num, 
            parent_id, perms, visible, status, is_frame, is_cache
        ) VALUES 
            ('新建字典类型', '', '', 'button', 'material-symbols:add', 1,
             dict_type_menu_id, 'POST /api/v2/dict-types', true, true, false, false),
            ('编辑字典类型', '', '', 'button', 'material-symbols:edit', 2,
             dict_type_menu_id, 'PUT /api/v2/dict-types/{id}', true, true, false, false),
            ('删除字典类型', '', '', 'button', 'material-symbols:delete', 3,
             dict_type_menu_id, 'DELETE /api/v2/dict-types/{id}', true, true, false, false)
        ON CONFLICT DO NOTHING;
        
        RAISE NOTICE '✅ 字典类型按钮权限创建完成 (3个)';
    ELSE
        RAISE NOTICE '⚠️  未找到"字典类型"菜单';
    END IF;

    -- ============================================================
    -- 字典数据管理页面的按钮权限
    -- ============================================================
    
    SELECT id INTO dict_data_menu_id FROM t_sys_menu WHERE name = '字典数据' AND menu_type = 'menu' LIMIT 1;
    
    IF dict_data_menu_id IS NOT NULL THEN
        INSERT INTO t_sys_menu (
            name, path, component, menu_type, icon, order_num, 
            parent_id, perms, visible, status, is_frame, is_cache
        ) VALUES 
            ('新建字典数据', '', '', 'button', 'material-symbols:add', 1,
             dict_data_menu_id, 'POST /api/v2/dict-data', true, true, false, false),
            ('编辑字典数据', '', '', 'button', 'material-symbols:edit', 2,
             dict_data_menu_id, 'PUT /api/v2/dict-data/{id}', true, true, false, false),
            ('删除字典数据', '', '', 'button', 'material-symbols:delete', 3,
             dict_data_menu_id, 'DELETE /api/v2/dict-data/{id}', true, true, false, false)
        ON CONFLICT DO NOTHING;
        
        RAISE NOTICE '✅ 字典数据按钮权限创建完成 (3个)';
    ELSE
        RAISE NOTICE '⚠️  未找到"字典数据"菜单';
    END IF;

END $$;

-- ============================================================
-- 查询已创建的按钮权限统计
-- ============================================================

SELECT 
    COUNT(*) as "按钮权限总数",
    COUNT(DISTINCT parent_id) as "涉及菜单数"
FROM t_sys_menu 
WHERE menu_type = 'button';

-- 查看各菜单下的按钮权限
SELECT 
    pm.name as "父菜单",
    m.name as "按钮名称",
    m.perms as "权限标识",
    m.order_num as "排序"
FROM t_sys_menu m
LEFT JOIN t_sys_menu pm ON m.parent_id = pm.id
WHERE m.menu_type = 'button'
ORDER BY pm.name, m.order_num;

