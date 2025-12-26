-- ============================================
-- 元数据管理 - 菜单清理与重组
-- ============================================
-- 说明: 
-- 1. 将 "设备分类管理" (ID 16) 移动到 "元数据管理" (ID 169) 下
-- 2. 隐藏/清理冗余的旧菜单 (如果有)
-- ============================================

BEGIN;

-- 1. 移动设备分类管理
UPDATE t_sys_menu 
SET parent_id = 169, 
    order_num = 10  -- 排在最前面作为基础
WHERE id = 16;

-- 2. 尝试隐藏旧的 "数据模型管理" (如果有)
-- 注意：之前查询没找到，但为了保险起见，按路径匹配
UPDATE t_sys_menu 
SET visible = false 
WHERE path = '/data-model';

-- 3. 尝试隐藏旧的 "设备字段配置" (如果有)
UPDATE t_sys_menu 
SET visible = false 
WHERE path = '/device/fields';

COMMIT;
