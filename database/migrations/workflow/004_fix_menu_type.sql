-- =====================================================
-- 修复工作流菜单类型
-- 将 M/C/F 修改为 catalog/menu/button
-- =====================================================

-- 修复流程编排父菜单类型
UPDATE t_sys_menu SET menu_type = 'catalog' WHERE path = 'flow-settings' AND menu_type = 'M';

-- 修复工作流管理和设计菜单类型
UPDATE t_sys_menu SET menu_type = 'menu' WHERE path IN ('workflow-manage', 'workflow-design') AND menu_type = 'C';

-- 修复按钮权限类型
UPDATE t_sys_menu SET menu_type = 'button' WHERE perms LIKE '%/api/v2/workflows%' AND menu_type = 'F';

-- 删除重复的菜单（如果有）
-- 保留ID较小的记录
DELETE FROM t_sys_menu 
WHERE id IN (
    SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (PARTITION BY path, parent_id ORDER BY id) as rn
        FROM t_sys_menu 
        WHERE path IN ('flow-settings', 'workflow-manage', 'workflow-design')
    ) t WHERE rn > 1
);
