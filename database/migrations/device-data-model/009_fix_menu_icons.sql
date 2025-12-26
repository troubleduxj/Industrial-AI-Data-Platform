-- ========================================
-- 修复数据模型菜单图标
-- ========================================
-- 将简单的图标名称更新为标准的 iconify 图标名称
--
-- 图标说明：
-- - mdi:database: 数据库图标（根菜单）
-- - mdi:cog-outline: 设置/配置图标（模型配置管理）
-- - mdi:link-variant: 链接/映射图标（字段映射管理）
-- - mdi:eye-outline: 眼睛/预览图标（预览与测试）
-- ========================================

-- 更新根菜单图标
UPDATE t_sys_menu
SET icon = 'mdi:database'
WHERE name = '数据模型管理'
  AND path = '/data-model';

-- 更新子菜单图标
UPDATE t_sys_menu
SET icon = 'mdi:cog-outline'
WHERE name = '模型配置管理'
  AND path = '/data-model/config';

UPDATE t_sys_menu
SET icon = 'mdi:link-variant'
WHERE name = '字段映射管理'
  AND path = '/data-model/mapping';

UPDATE t_sys_menu
SET icon = 'mdi:eye-outline'
WHERE name = '预览与测试'
  AND path = '/data-model/preview';

