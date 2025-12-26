-- 为设备类型表添加图标字段
-- 执行时间: 2025-11-12

-- 添加icon字段
ALTER TABLE t_device_type ADD COLUMN IF NOT EXISTS icon VARCHAR(100);

-- 添加注释
COMMENT ON COLUMN t_device_type.icon IS '设备类型图标（Iconify图标名称）';

-- 为现有数据设置默认图标
UPDATE t_device_type SET icon = 'material-symbols:precision-manufacturing' WHERE icon IS NULL;
