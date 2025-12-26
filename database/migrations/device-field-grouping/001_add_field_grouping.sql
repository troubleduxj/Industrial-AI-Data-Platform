-- =====================================================
-- 设备字段分组功能 - 数据库迁移
-- 功能：添加字段分组、默认显示、分组排序字段
-- 创建时间：2025-11-25
-- =====================================================

-- 1. 添加字段分组相关列
ALTER TABLE t_device_field 
ADD COLUMN IF NOT EXISTS field_group VARCHAR(50) DEFAULT 'default' COMMENT '字段分组：core/temperature/power/other';

ALTER TABLE t_device_field 
ADD COLUMN IF NOT EXISTS is_default_visible BOOLEAN DEFAULT true COMMENT '是否默认显示（卡片上直接可见）';

ALTER TABLE t_device_field 
ADD COLUMN IF NOT EXISTS group_order INT DEFAULT 0 COMMENT '分组排序顺序';

-- 2. 创建索引以提升查询性能
CREATE INDEX IF NOT EXISTS idx_device_field_group 
ON t_device_field(device_type_code, field_group, is_default_visible);

CREATE INDEX IF NOT EXISTS idx_device_field_visible 
ON t_device_field(device_type_code, is_default_visible, sort_order);

-- 3. 为现有字段设置默认值
-- 将所有现有字段标记为默认显示（保持向后兼容）
UPDATE t_device_field 
SET field_group = 'default',
    is_default_visible = true,
    group_order = 0
WHERE field_group IS NULL;

-- =====================================================
-- 配置布鲁克纳挤出机字段分组
-- =====================================================

-- 核心参数组（默认显示）
UPDATE t_device_field 
SET field_group = 'core',
    is_default_visible = true,
    group_order = 1
WHERE device_type_code = 'BRUCKNER_EXTRUDER' 
  AND field_code IN ('melt_temperature', 'melt_pressure', 'screw_speed', 'motor_torque');

-- 温度参数组（默认折叠）
UPDATE t_device_field 
SET field_group = 'temperature',
    is_default_visible = false,
    group_order = 2
WHERE device_type_code = 'BRUCKNER_EXTRUDER' 
  AND field_code IN ('zone1_temp', 'zone2_temp', 'zone3_temp', 'zone4_temp', 'zone5_temp');

-- 其他参数组（默认折叠）
UPDATE t_device_field 
SET field_group = 'other',
    is_default_visible = false,
    group_order = 3
WHERE device_type_code = 'BRUCKNER_EXTRUDER' 
  AND field_code IN ('motor_current', 'feed_rate');

-- =====================================================
-- 配置其他布鲁克纳设备字段分组
-- =====================================================

-- 模头：核心参数
UPDATE t_device_field 
SET field_group = 'core',
    is_default_visible = true,
    group_order = 1
WHERE device_type_code = 'BRUCKNER_DIE' 
  AND field_code IN ('die_temp_center', 'die_pressure', 'lip_gap');

-- 模头：温度参数
UPDATE t_device_field 
SET field_group = 'temperature',
    is_default_visible = false,
    group_order = 2
WHERE device_type_code = 'BRUCKNER_DIE' 
  AND field_code IN ('die_temp_left', 'die_temp_right');

-- 模头：其他参数
UPDATE t_device_field 
SET field_group = 'other',
    is_default_visible = false,
    group_order = 3
WHERE device_type_code = 'BRUCKNER_DIE' 
  AND field_code = 'die_width';

-- 急冷辊：核心参数
UPDATE t_device_field 
SET field_group = 'core',
    is_default_visible = true,
    group_order = 1
WHERE device_type_code = 'BRUCKNER_CHILL_ROLL' 
  AND field_code IN ('roll_temperature', 'water_flow', 'roll_speed', 'vibration');

-- 急冷辊：温度参数
UPDATE t_device_field 
SET field_group = 'temperature',
    is_default_visible = false,
    group_order = 2
WHERE device_type_code = 'BRUCKNER_CHILL_ROLL' 
  AND field_code IN ('water_inlet_temp', 'water_outlet_temp');

-- 急冷辊：其他参数
UPDATE t_device_field 
SET field_group = 'other',
    is_default_visible = false,
    group_order = 3
WHERE device_type_code = 'BRUCKNER_CHILL_ROLL' 
  AND field_code = 'motor_current';

-- MDO拉伸辊：核心参数
UPDATE t_device_field 
SET field_group = 'core',
    is_default_visible = true,
    group_order = 1
WHERE device_type_code = 'BRUCKNER_MDO_STRETCH' 
  AND field_code IN ('stretch_ratio', 'web_tension', 'roll_temperature', 'motor_torque');

-- MDO拉伸辊：速度参数
UPDATE t_device_field 
SET field_group = 'speed',
    is_default_visible = false,
    group_order = 2
WHERE device_type_code = 'BRUCKNER_MDO_STRETCH' 
  AND field_code IN ('slow_roll_speed', 'fast_roll_speed');

-- TDO拉幅机：核心参数
UPDATE t_device_field 
SET field_group = 'core',
    is_default_visible = true,
    group_order = 1
WHERE device_type_code = 'BRUCKNER_TDO_TENTER' 
  AND field_code IN ('stretch_ratio', 'line_speed', 'heatset_zone_temp', 'oven_pressure');

-- TDO拉幅机：温度参数
UPDATE t_device_field 
SET field_group = 'temperature',
    is_default_visible = false,
    group_order = 2
WHERE device_type_code = 'BRUCKNER_TDO_TENTER' 
  AND field_code IN ('preheat_zone_temp', 'stretch_zone_temp', 'cooling_zone_temp');

-- TDO拉幅机：尺寸参数
UPDATE t_device_field 
SET field_group = 'dimension',
    is_default_visible = false,
    group_order = 3
WHERE device_type_code = 'BRUCKNER_TDO_TENTER' 
  AND field_code IN ('inlet_width', 'outlet_width');

-- 在线测厚仪：全部为核心参数（字段较少）
UPDATE t_device_field 
SET field_group = 'core',
    is_default_visible = true,
    group_order = 1
WHERE device_type_code = 'BRUCKNER_THICKNESS';

-- =====================================================
-- 验证配置结果
-- =====================================================

-- 查看字段分组统计
SELECT 
    device_type_code,
    field_group,
    is_default_visible,
    COUNT(*) as field_count
FROM t_device_field
WHERE device_type_code LIKE 'BRUCKNER_%'
  AND is_active = true
GROUP BY device_type_code, field_group, is_default_visible
ORDER BY device_type_code, group_order, is_default_visible DESC;

-- 查看每种设备的默认显示字段数量
SELECT 
    device_type_code,
    COUNT(*) FILTER (WHERE is_default_visible = true) as visible_fields,
    COUNT(*) FILTER (WHERE is_default_visible = false) as hidden_fields,
    COUNT(*) as total_fields
FROM t_device_field
WHERE device_type_code LIKE 'BRUCKNER_%'
  AND is_active = true
GROUP BY device_type_code
ORDER BY device_type_code;

-- =====================================================
-- 配置完成
-- =====================================================
-- ✅ 已添加 3 个新字段
-- ✅ 已创建 2 个索引
-- ✅ 已配置布鲁克纳设备字段分组
-- ✅ 核心字段：默认显示（不超过4个）
-- ✅ 其他字段：按类型分组，默认折叠
-- =====================================================
