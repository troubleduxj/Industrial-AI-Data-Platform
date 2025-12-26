-- 修复通知管理菜单的路由配置
-- 确保 component 字段格式正确，与前端 vueModules 匹配

-- 查看当前通知管理菜单配置
-- SELECT id, name, path, component, menu_type FROM t_sys_menu WHERE id BETWEEN 200 AND 210;

-- 修复子菜单的 component 字段（确保格式为 notification/xxx）
UPDATE t_sys_menu SET component = 'notification/list' WHERE id = 201;
UPDATE t_sys_menu SET component = 'notification/email-server' WHERE id = 202;
UPDATE t_sys_menu SET component = 'notification/email-template' WHERE id = 203;
UPDATE t_sys_menu SET component = 'notification/send-config' WHERE id = 204;

-- 确保一级菜单的 component 为 Layout
UPDATE t_sys_menu SET component = 'Layout' WHERE id = 200;

-- 确保子菜单的 path 是相对路径（不带前导斜杠）
UPDATE t_sys_menu SET path = 'list' WHERE id = 201;
UPDATE t_sys_menu SET path = 'email-server' WHERE id = 202;
UPDATE t_sys_menu SET path = 'email-template' WHERE id = 203;
UPDATE t_sys_menu SET path = 'send-config' WHERE id = 204;

-- 验证修复结果
SELECT id, name, path, component, menu_type FROM t_sys_menu WHERE id BETWEEN 200 AND 210;
