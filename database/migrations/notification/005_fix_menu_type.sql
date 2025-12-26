-- 修复通知管理菜单的 menu_type 字段
-- menu_type 应该是: catalog(目录), menu(菜单), button(按钮)

-- 修复一级菜单（目录）
UPDATE t_sys_menu SET menu_type = 'catalog' WHERE id = 200;

-- 修复二级菜单（菜单）
UPDATE t_sys_menu SET menu_type = 'menu' WHERE id IN (201, 202, 203, 204);

-- 修复按钮
UPDATE t_sys_menu SET menu_type = 'button' WHERE id IN (2011, 2012, 2013, 2014, 2021, 2022, 2023, 2024, 2031, 2032, 2033, 2034, 2041);

-- 同时修复 visible 和 status 字段（按钮应该是 visible=false）
UPDATE t_sys_menu SET visible = FALSE WHERE id IN (2011, 2012, 2013, 2014, 2021, 2022, 2023, 2024, 2031, 2032, 2033, 2034, 2041);

-- 修复 status 字段（所有菜单应该是启用状态）
UPDATE t_sys_menu SET status = TRUE WHERE id BETWEEN 200 AND 2050;
