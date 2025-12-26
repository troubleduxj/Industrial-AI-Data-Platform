-- 检查菜单记录
SELECT id, parent_id, name, path, visible, menu_type, order_num
FROM t_sys_menu 
WHERE path LIKE '/data-model%' 
ORDER BY COALESCE(parent_id, id), order_num;

-- 检查权限分配
SELECT r.id as role_id, r.role_name, m.id as menu_id, m.name as menu_name, m.path
FROM t_sys_role r
JOIN t_sys_role_menu rm ON r.id = rm.role_id
JOIN t_sys_menu m ON rm.menu_id = m.id
WHERE m.path LIKE '/data-model%'
ORDER BY r.id, m.id;

-- 检查当前用户的角色
SELECT u.id, u.username, r.id as role_id, r.role_name
FROM t_sys_user u
JOIN t_sys_user_role ur ON u.id = ur.user_id
JOIN t_sys_role r ON ur.role_id = r.id
LIMIT 10;

