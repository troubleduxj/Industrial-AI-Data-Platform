-- =====================================================
-- 工作流管理菜单和权限配置
-- 创建时间: 2024-11-26
-- =====================================================

-- 查找流程编排父菜单ID
SET @parent_menu_id = (SELECT id FROM sys_menu WHERE path = 'flow-settings' LIMIT 1);

-- 如果父菜单不存在，先创建
INSERT INTO sys_menu (menu_type, name, path, `order`, parent_id, icon, is_hidden, component, keepalive, redirect, created_at, updated_at)
SELECT 1, '流程编排', 'flow-settings', 60, 0, 'material-symbols:account-tree', 0, 'Layout', 0, '/flow-settings/workflow-manage', NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE path = 'flow-settings');

-- 重新获取父菜单ID
SET @parent_menu_id = (SELECT id FROM sys_menu WHERE path = 'flow-settings' LIMIT 1);

-- 插入工作流管理菜单
INSERT INTO sys_menu (menu_type, name, path, `order`, parent_id, icon, is_hidden, component, keepalive, created_at, updated_at)
SELECT 1, '工作流管理', 'workflow-manage', 1, @parent_menu_id, 'material-symbols:workflow-outline', 0, '/flow-settings/workflow-manage', 0, NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE path = 'workflow-manage' AND parent_id = @parent_menu_id);

-- 插入工作流设计菜单
INSERT INTO sys_menu (menu_type, name, path, `order`, parent_id, icon, is_hidden, component, keepalive, created_at, updated_at)
SELECT 1, '工作流设计', 'workflow-design', 2, @parent_menu_id, 'material-symbols:design-services-outline', 0, '/flow-settings/workflow-design', 0, NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE path = 'workflow-design' AND parent_id = @parent_menu_id);

-- 获取工作流管理菜单ID
SET @workflow_manage_id = (SELECT id FROM sys_menu WHERE path = 'workflow-manage' AND parent_id = @parent_menu_id LIMIT 1);

-- 插入工作流管理按钮权限
INSERT INTO sys_menu (menu_type, name, path, `order`, parent_id, icon, is_hidden, perms, created_at, updated_at)
SELECT 2, '新建工作流', '', 1, @workflow_manage_id, 'material-symbols:add', 0, 'POST /api/v2/workflows', NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'POST /api/v2/workflows' AND parent_id = @workflow_manage_id);

INSERT INTO sys_menu (menu_type, name, path, `order`, parent_id, icon, is_hidden, perms, created_at, updated_at)
SELECT 2, '编辑工作流', '', 2, @workflow_manage_id, 'material-symbols:edit', 0, 'PUT /api/v2/workflows/{id}', NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'PUT /api/v2/workflows/{id}' AND parent_id = @workflow_manage_id);

INSERT INTO sys_menu (menu_type, name, path, `order`, parent_id, icon, is_hidden, perms, created_at, updated_at)
SELECT 2, '删除工作流', '', 3, @workflow_manage_id, 'material-symbols:delete', 0, 'DELETE /api/v2/workflows/{id}', NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'DELETE /api/v2/workflows/{id}' AND parent_id = @workflow_manage_id);

INSERT INTO sys_menu (menu_type, name, path, `order`, parent_id, icon, is_hidden, perms, created_at, updated_at)
SELECT 2, '发布工作流', '', 4, @workflow_manage_id, 'material-symbols:publish', 0, 'POST /api/v2/workflows/{id}/publish', NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'POST /api/v2/workflows/{id}/publish' AND parent_id = @workflow_manage_id);

INSERT INTO sys_menu (menu_type, name, path, `order`, parent_id, icon, is_hidden, perms, created_at, updated_at)
SELECT 2, '执行工作流', '', 5, @workflow_manage_id, 'material-symbols:play-arrow', 0, 'POST /api/v2/workflows/{id}/execute', NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'POST /api/v2/workflows/{id}/execute' AND parent_id = @workflow_manage_id);

-- 获取工作流设计菜单ID
SET @workflow_design_id = (SELECT id FROM sys_menu WHERE path = 'workflow-design' AND parent_id = @parent_menu_id LIMIT 1);

-- 插入工作流设计按钮权限
INSERT INTO sys_menu (menu_type, name, path, `order`, parent_id, icon, is_hidden, perms, created_at, updated_at)
SELECT 2, '保存设计', '', 1, @workflow_design_id, 'material-symbols:save', 0, 'PUT /api/v2/workflows/{id}/design', NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'PUT /api/v2/workflows/{id}/design' AND parent_id = @workflow_design_id);

INSERT INTO sys_menu (menu_type, name, path, `order`, parent_id, icon, is_hidden, perms, created_at, updated_at)
SELECT 2, '导出工作流', '', 2, @workflow_design_id, 'material-symbols:download', 0, 'GET /api/v2/workflows/{id}/export', NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'GET /api/v2/workflows/{id}/export' AND parent_id = @workflow_design_id);

INSERT INTO sys_menu (menu_type, name, path, `order`, parent_id, icon, is_hidden, perms, created_at, updated_at)
SELECT 2, '导入工作流', '', 3, @workflow_design_id, 'material-symbols:upload', 0, 'POST /api/v2/workflows/import', NOW(), NOW()
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE perms = 'POST /api/v2/workflows/import' AND parent_id = @workflow_design_id);

-- 为管理员角色分配工作流相关菜单权限
INSERT INTO sys_role_menu (role_id, menu_id)
SELECT 1, id FROM sys_menu 
WHERE (path IN ('flow-settings', 'workflow-manage', 'workflow-design') 
   OR perms LIKE '%/api/v2/workflows%')
AND id NOT IN (SELECT menu_id FROM sys_role_menu WHERE role_id = 1);
