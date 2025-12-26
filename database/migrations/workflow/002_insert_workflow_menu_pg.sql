-- =====================================================
-- 工作流管理菜单和权限配置 (PostgreSQL版本)
-- 创建时间: 2024-11-26
-- 使用正确的表名和字段名
-- menu_type: catalog(目录), menu(菜单), button(按钮)
-- =====================================================

-- 插入流程编排父菜单（如果不存在）
INSERT INTO t_sys_menu (menu_type, name, path, order_num, parent_id, icon, visible, component, is_cache, created_at, updated_at)
SELECT 'catalog', '流程编排', 'flow-settings', 60, 0, 'material-symbols:account-tree', true, 'Layout', false, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM t_sys_menu WHERE path = 'flow-settings');

-- 插入工作流管理菜单
INSERT INTO t_sys_menu (menu_type, name, path, order_num, parent_id, icon, visible, component, is_cache, created_at, updated_at)
SELECT 'menu', '工作流管理', 'workflow-manage', 1, 
    (SELECT id FROM t_sys_menu WHERE path = 'flow-settings' LIMIT 1),
    'material-symbols:workflow-outline', true, '/flow-settings/workflow-manage', false, NOW(), NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM t_sys_menu WHERE path = 'workflow-manage' 
    AND parent_id = (SELECT id FROM t_sys_menu WHERE path = 'flow-settings' LIMIT 1)
);

-- 插入工作流设计菜单
INSERT INTO t_sys_menu (menu_type, name, path, order_num, parent_id, icon, visible, component, is_cache, created_at, updated_at)
SELECT 'menu', '工作流设计', 'workflow-design', 2, 
    (SELECT id FROM t_sys_menu WHERE path = 'flow-settings' LIMIT 1),
    'material-symbols:design-services-outline', true, '/flow-settings/workflow-design', false, NOW(), NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM t_sys_menu WHERE path = 'workflow-design' 
    AND parent_id = (SELECT id FROM t_sys_menu WHERE path = 'flow-settings' LIMIT 1)
);

-- 插入工作流管理按钮权限
INSERT INTO t_sys_menu (menu_type, name, path, order_num, parent_id, icon, visible, perms, created_at, updated_at)
SELECT 'button', '新建工作流', '', 1, 
    (SELECT id FROM t_sys_menu WHERE path = 'workflow-manage' AND parent_id = (SELECT id FROM t_sys_menu WHERE path = 'flow-settings' LIMIT 1) LIMIT 1),
    'material-symbols:add', true, 'POST /api/v2/workflows', NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM t_sys_menu WHERE perms = 'POST /api/v2/workflows');

INSERT INTO t_sys_menu (menu_type, name, path, order_num, parent_id, icon, visible, perms, created_at, updated_at)
SELECT 'button', '编辑工作流', '', 2, 
    (SELECT id FROM t_sys_menu WHERE path = 'workflow-manage' AND parent_id = (SELECT id FROM t_sys_menu WHERE path = 'flow-settings' LIMIT 1) LIMIT 1),
    'material-symbols:edit', true, 'PUT /api/v2/workflows/{id}', NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM t_sys_menu WHERE perms = 'PUT /api/v2/workflows/{id}');

INSERT INTO t_sys_menu (menu_type, name, path, order_num, parent_id, icon, visible, perms, created_at, updated_at)
SELECT 'button', '删除工作流', '', 3, 
    (SELECT id FROM t_sys_menu WHERE path = 'workflow-manage' AND parent_id = (SELECT id FROM t_sys_menu WHERE path = 'flow-settings' LIMIT 1) LIMIT 1),
    'material-symbols:delete', true, 'DELETE /api/v2/workflows/{id}', NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM t_sys_menu WHERE perms = 'DELETE /api/v2/workflows/{id}');

INSERT INTO t_sys_menu (menu_type, name, path, order_num, parent_id, icon, visible, perms, created_at, updated_at)
SELECT 'button', '发布工作流', '', 4, 
    (SELECT id FROM t_sys_menu WHERE path = 'workflow-manage' AND parent_id = (SELECT id FROM t_sys_menu WHERE path = 'flow-settings' LIMIT 1) LIMIT 1),
    'material-symbols:publish', true, 'POST /api/v2/workflows/{id}/publish', NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM t_sys_menu WHERE perms = 'POST /api/v2/workflows/{id}/publish');

INSERT INTO t_sys_menu (menu_type, name, path, order_num, parent_id, icon, visible, perms, created_at, updated_at)
SELECT 'button', '执行工作流', '', 5, 
    (SELECT id FROM t_sys_menu WHERE path = 'workflow-manage' AND parent_id = (SELECT id FROM t_sys_menu WHERE path = 'flow-settings' LIMIT 1) LIMIT 1),
    'material-symbols:play-arrow', true, 'POST /api/v2/workflows/{id}/execute', NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM t_sys_menu WHERE perms = 'POST /api/v2/workflows/{id}/execute');

-- 插入工作流设计按钮权限
INSERT INTO t_sys_menu (menu_type, name, path, order_num, parent_id, icon, visible, perms, created_at, updated_at)
SELECT 'button', '保存设计', '', 1, 
    (SELECT id FROM t_sys_menu WHERE path = 'workflow-design' AND parent_id = (SELECT id FROM t_sys_menu WHERE path = 'flow-settings' LIMIT 1) LIMIT 1),
    'material-symbols:save', true, 'PUT /api/v2/workflows/{id}/design', NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM t_sys_menu WHERE perms = 'PUT /api/v2/workflows/{id}/design');

INSERT INTO t_sys_menu (menu_type, name, path, order_num, parent_id, icon, visible, perms, created_at, updated_at)
SELECT 'button', '导出工作流', '', 2, 
    (SELECT id FROM t_sys_menu WHERE path = 'workflow-design' AND parent_id = (SELECT id FROM t_sys_menu WHERE path = 'flow-settings' LIMIT 1) LIMIT 1),
    'material-symbols:download', true, 'GET /api/v2/workflows/{id}/export', NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM t_sys_menu WHERE perms = 'GET /api/v2/workflows/{id}/export');

INSERT INTO t_sys_menu (menu_type, name, path, order_num, parent_id, icon, visible, perms, created_at, updated_at)
SELECT 'button', '导入工作流', '', 3, 
    (SELECT id FROM t_sys_menu WHERE path = 'workflow-design' AND parent_id = (SELECT id FROM t_sys_menu WHERE path = 'flow-settings' LIMIT 1) LIMIT 1),
    'material-symbols:upload', true, 'POST /api/v2/workflows/import', NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM t_sys_menu WHERE perms = 'POST /api/v2/workflows/import');

-- 为管理员角色分配工作流相关菜单权限
INSERT INTO t_sys_role_menu (role_id, menu_id)
SELECT 1, id FROM t_sys_menu 
WHERE (path IN ('flow-settings', 'workflow-manage', 'workflow-design') 
   OR perms LIKE '%/api/v2/workflows%')
AND id NOT IN (SELECT menu_id FROM t_sys_role_menu WHERE role_id = 1);
