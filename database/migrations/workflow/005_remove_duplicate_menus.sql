-- =====================================================
-- 清理工作流重复菜单记录
-- 问题：流程编排相关菜单被重复插入
-- 保留原有记录(ID较小的)，删除重复记录(ID较大的)
-- 执行时间: 2024-11-26
-- 状态: 已执行
-- =====================================================

-- 1. 删除重复的角色-菜单关联 (删除了7条)
DELETE FROM t_sys_role_menu WHERE menu_id IN (152, 153, 154, 155, 156, 157, 158);

-- 2. 删除重复的按钮权限 (删除了4条)
DELETE FROM t_sys_menu WHERE id IN (155, 156, 157, 158);

-- 3. 删除重复的子菜单 (删除了2条)
DELETE FROM t_sys_menu WHERE id IN (153, 154);

-- 4. 删除重复的父目录 (删除了1条)
DELETE FROM t_sys_menu WHERE id = 152;

-- 5. 修复path格式 (更新了1条)
UPDATE t_sys_menu SET path = 'flow-settings' WHERE id = 27 AND path = '/flow-settings';

-- 6. 添加缺失的执行工作流按钮
INSERT INTO t_sys_menu (menu_type, name, path, order_num, parent_id, icon, visible, perms, created_at, updated_at)
SELECT 'button', '执行工作流', '', 5, 35, 'material-symbols:play-arrow', true, 
       'POST /api/v2/workflows/{id}/execute', NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM t_sys_menu WHERE perms = 'POST /api/v2/workflows/{id}/execute');

-- 7. 确保管理员角色有工作流菜单权限
INSERT INTO t_sys_role_menu (role_id, menu_id)
SELECT 1, id FROM t_sys_menu 
WHERE (path IN ('flow-settings', 'workflow-manage', 'workflow-design')
       OR perms LIKE '%/api/v2/workflows%')
AND id NOT IN (SELECT menu_id FROM t_sys_role_menu WHERE role_id = 1);
