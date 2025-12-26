-- 通知管理模块 - 一级菜单
-- 创建时间: 2025-11-25
-- 字段说明: id, parent_id, name, path, component, icon, order_num, menu_type, perms, visible, status, is_frame, is_cache

-- 先删除旧的通知管理菜单（如果在系统管理下）
DELETE FROM t_sys_menu WHERE path = '/system/notification';
DELETE FROM t_sys_menu WHERE id BETWEEN 200 AND 2050;

-- 1. 创建通知管理一级菜单 (menu_type: catalog=目录, menu=菜单, button=按钮)
INSERT INTO t_sys_menu (id, parent_id, name, path, component, icon, order_num, menu_type, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES (200, 0, '通知管理', '/notification', 'Layout', 'ant-design:notification-outlined', 85, 'catalog', NULL, TRUE, TRUE, FALSE, FALSE, NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    path = EXCLUDED.path,
    icon = EXCLUDED.icon,
    order_num = EXCLUDED.order_num,
    updated_at = NOW();

-- 2. 通知列表
INSERT INTO t_sys_menu (id, parent_id, name, path, component, icon, order_num, menu_type, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES (201, 200, '通知列表', 'list', 'notification/list', 'ant-design:unordered-list-outlined', 1, 'menu', NULL, TRUE, TRUE, FALSE, FALSE, NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    path = EXCLUDED.path,
    component = EXCLUDED.component,
    order_num = EXCLUDED.order_num,
    updated_at = NOW();

-- 3. 邮件服务器配置
INSERT INTO t_sys_menu (id, parent_id, name, path, component, icon, order_num, menu_type, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES (202, 200, '邮件服务器', 'email-server', 'notification/email-server', 'ant-design:mail-outlined', 2, 'menu', NULL, TRUE, TRUE, FALSE, FALSE, NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    path = EXCLUDED.path,
    component = EXCLUDED.component,
    order_num = EXCLUDED.order_num,
    updated_at = NOW();

-- 4. 邮件模板
INSERT INTO t_sys_menu (id, parent_id, name, path, component, icon, order_num, menu_type, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES (203, 200, '邮件模板', 'email-template', 'notification/email-template', 'ant-design:file-text-outlined', 3, 'menu', NULL, TRUE, TRUE, FALSE, FALSE, NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    path = EXCLUDED.path,
    component = EXCLUDED.component,
    order_num = EXCLUDED.order_num,
    updated_at = NOW();

-- 5. 发送配置
INSERT INTO t_sys_menu (id, parent_id, name, path, component, icon, order_num, menu_type, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES (204, 200, '发送配置', 'send-config', 'notification/send-config', 'ant-design:setting-outlined', 4, 'menu', NULL, TRUE, TRUE, FALSE, FALSE, NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    path = EXCLUDED.path,
    component = EXCLUDED.component,
    order_num = EXCLUDED.order_num,
    updated_at = NOW();

-- 6. 添加按钮权限

-- 通知列表按钮
INSERT INTO t_sys_menu (id, parent_id, name, path, component, icon, order_num, menu_type, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES 
(2011, 201, '新增通知', NULL, NULL, NULL, 1, 'button', 'notification:list:create', FALSE, TRUE, FALSE, FALSE, NOW(), NOW()),
(2012, 201, '编辑通知', NULL, NULL, NULL, 2, 'button', 'notification:list:update', FALSE, TRUE, FALSE, FALSE, NOW(), NOW()),
(2013, 201, '删除通知', NULL, NULL, NULL, 3, 'button', 'notification:list:delete', FALSE, TRUE, FALSE, FALSE, NOW(), NOW()),
(2014, 201, '发布通知', NULL, NULL, NULL, 4, 'button', 'notification:list:publish', FALSE, TRUE, FALSE, FALSE, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 邮件服务器按钮
INSERT INTO t_sys_menu (id, parent_id, name, path, component, icon, order_num, menu_type, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES 
(2021, 202, '新增服务器', NULL, NULL, NULL, 1, 'button', 'notification:email-server:create', FALSE, TRUE, FALSE, FALSE, NOW(), NOW()),
(2022, 202, '编辑服务器', NULL, NULL, NULL, 2, 'button', 'notification:email-server:update', FALSE, TRUE, FALSE, FALSE, NOW(), NOW()),
(2023, 202, '删除服务器', NULL, NULL, NULL, 3, 'button', 'notification:email-server:delete', FALSE, TRUE, FALSE, FALSE, NOW(), NOW()),
(2024, 202, '测试连接', NULL, NULL, NULL, 4, 'button', 'notification:email-server:test', FALSE, TRUE, FALSE, FALSE, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 邮件模板按钮
INSERT INTO t_sys_menu (id, parent_id, name, path, component, icon, order_num, menu_type, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES 
(2031, 203, '新增模板', NULL, NULL, NULL, 1, 'button', 'notification:email-template:create', FALSE, TRUE, FALSE, FALSE, NOW(), NOW()),
(2032, 203, '编辑模板', NULL, NULL, NULL, 2, 'button', 'notification:email-template:update', FALSE, TRUE, FALSE, FALSE, NOW(), NOW()),
(2033, 203, '删除模板', NULL, NULL, NULL, 3, 'button', 'notification:email-template:delete', FALSE, TRUE, FALSE, FALSE, NOW(), NOW()),
(2034, 203, '预览模板', NULL, NULL, NULL, 4, 'button', 'notification:email-template:preview', FALSE, TRUE, FALSE, FALSE, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 发送配置按钮
INSERT INTO t_sys_menu (id, parent_id, name, path, component, icon, order_num, menu_type, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES 
(2041, 204, '编辑配置', NULL, NULL, NULL, 1, 'button', 'notification:send-config:update', FALSE, TRUE, FALSE, FALSE, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 7. 为管理员角色分配权限
INSERT INTO t_sys_role_menu (role_id, menu_id)
SELECT 1, id FROM t_sys_menu WHERE id IN (200, 201, 202, 203, 204, 2011, 2012, 2013, 2014, 2021, 2022, 2023, 2024, 2031, 2032, 2033, 2034, 2041)
ON CONFLICT DO NOTHING;
