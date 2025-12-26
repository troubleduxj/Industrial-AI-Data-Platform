-- =====================================================
-- 设备类型动态参数展示 - 监测字段配置
-- 功能：配置焊机和压力传感器的监测关键字段
-- 创建时间：2025-11-20
-- =====================================================

-- =====================================================
-- TASK-11: 配置焊机监测字段
-- =====================================================

-- 1. 更新焊机的预设电流字段
UPDATE t_device_field 
SET 
    is_monitoring_key = true,
    sort_order = 1,
    display_config = '{"icon": "⚡", "color": "#1890ff"}'::jsonb
WHERE device_type_code = 'welding' 
  AND field_code = 'preset_current';

-- 如果字段不存在，则插入
INSERT INTO t_device_field (
    device_type_code,
    field_name,
    field_code,
    field_type,
    field_category,
    unit,
    description,
    is_required,
    sort_order,
    is_active,
    is_monitoring_key,
    is_ai_feature,
    aggregation_method,
    data_range,
    alarm_threshold,
    display_config,
    created_at,
    updated_at
)
SELECT 
    'welding',
    '预设电流',
    'preset_current',
    'float',
    'data_collection',
    'A',
    '焊机预设电流值',
    true,
    1,
    true,
    true,
    true,
    'avg',
    '{"min": 0, "max": 500}'::jsonb,
    '{"warning": 400, "critical": 450}'::jsonb,
    '{"icon": "⚡", "color": "#1890ff"}'::jsonb,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM t_device_field 
    WHERE device_type_code = 'welding' AND field_code = 'preset_current'
);

-- 2. 更新焊机的预设电压字段
UPDATE t_device_field 
SET 
    is_monitoring_key = true,
    sort_order = 2,
    display_config = '{"icon": "🔌", "color": "#52c41a"}'::jsonb
WHERE device_type_code = 'welding' 
  AND field_code = 'preset_voltage';

-- 如果字段不存在，则插入
INSERT INTO t_device_field (
    device_type_code,
    field_name,
    field_code,
    field_type,
    field_category,
    unit,
    description,
    is_required,
    sort_order,
    is_active,
    is_monitoring_key,
    is_ai_feature,
    aggregation_method,
    data_range,
    alarm_threshold,
    display_config,
    created_at,
    updated_at
)
SELECT 
    'welding',
    '预设电压',
    'preset_voltage',
    'float',
    'data_collection',
    'V',
    '焊机预设电压值',
    true,
    2,
    true,
    true,
    true,
    'avg',
    '{"min": 0, "max": 100}'::jsonb,
    '{"warning": 80, "critical": 90}'::jsonb,
    '{"icon": "🔌", "color": "#52c41a"}'::jsonb,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM t_device_field 
    WHERE device_type_code = 'welding' AND field_code = 'preset_voltage'
);

-- 3. 更新焊机的焊接电流字段
UPDATE t_device_field 
SET 
    is_monitoring_key = true,
    sort_order = 3,
    display_config = '{"icon": "⚡", "color": "#fa8c16"}'::jsonb
WHERE device_type_code = 'welding' 
  AND field_code = 'welding_current';

-- 如果字段不存在，则插入
INSERT INTO t_device_field (
    device_type_code,
    field_name,
    field_code,
    field_type,
    field_category,
    unit,
    description,
    is_required,
    sort_order,
    is_active,
    is_monitoring_key,
    is_ai_feature,
    aggregation_method,
    data_range,
    alarm_threshold,
    display_config,
    created_at,
    updated_at
)
SELECT 
    'welding',
    '焊接电流',
    'welding_current',
    'float',
    'data_collection',
    'A',
    '焊机实际焊接电流值',
    true,
    3,
    true,
    true,
    true,
    'avg',
    '{"min": 0, "max": 500}'::jsonb,
    '{"warning": 400, "critical": 450}'::jsonb,
    '{"icon": "⚡", "color": "#fa8c16"}'::jsonb,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM t_device_field 
    WHERE device_type_code = 'welding' AND field_code = 'welding_current'
);

-- 4. 更新焊机的焊接电压字段
UPDATE t_device_field 
SET 
    is_monitoring_key = true,
    sort_order = 4,
    display_config = '{"icon": "🔌", "color": "#faad14"}'::jsonb
WHERE device_type_code = 'welding' 
  AND field_code = 'welding_voltage';

-- 如果字段不存在，则插入
INSERT INTO t_device_field (
    device_type_code,
    field_name,
    field_code,
    field_type,
    field_category,
    unit,
    description,
    is_required,
    sort_order,
    is_active,
    is_monitoring_key,
    is_ai_feature,
    aggregation_method,
    data_range,
    alarm_threshold,
    display_config,
    created_at,
    updated_at
)
SELECT 
    'welding',
    '焊接电压',
    'welding_voltage',
    'float',
    'data_collection',
    'V',
    '焊机实际焊接电压值',
    true,
    4,
    true,
    true,
    true,
    'avg',
    '{"min": 0, "max": 100}'::jsonb,
    '{"warning": 80, "critical": 90}'::jsonb,
    '{"icon": "🔌", "color": "#faad14"}'::jsonb,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM t_device_field 
    WHERE device_type_code = 'welding' AND field_code = 'welding_voltage'
);

-- =====================================================
-- TASK-12: 配置压力传感器监测字段
-- =====================================================

-- 首先确保压力传感器设备类型存在
INSERT INTO t_device_type (
    type_name,
    type_code,
    tdengine_stable_name,
    description,
    icon,
    is_active,
    device_count,
    created_at,
    updated_at
)
SELECT 
    '智能压力传感器',
    'PRESSURE_SENSOR_V1',
    'st_pressure_sensor',
    '用于监测管道压力的智能传感器，支持实时数据采集和异常检测',
    'mdi:gauge',
    true,
    0,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM t_device_type WHERE type_code = 'PRESSURE_SENSOR_V1'
);

-- 1. 配置压力值字段
INSERT INTO t_device_field (
    device_type_code,
    field_name,
    field_code,
    field_type,
    field_category,
    unit,
    description,
    is_required,
    sort_order,
    is_active,
    is_monitoring_key,
    is_ai_feature,
    aggregation_method,
    data_range,
    alarm_threshold,
    display_config,
    created_at,
    updated_at
)
SELECT 
    'PRESSURE_SENSOR_V1',
    '压力值',
    'pressure',
    'float',
    'data_collection',
    'MPa',
    '当前压力读数',
    true,
    1,
    true,
    true,
    true,
    'avg',
    '{"min": 0, "max": 10}'::jsonb,
    '{"warning": 8, "critical": 9.5}'::jsonb,
    '{"icon": "📊", "color": "#1890ff"}'::jsonb,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM t_device_field 
    WHERE device_type_code = 'PRESSURE_SENSOR_V1' AND field_code = 'pressure'
);

-- 2. 配置温度字段
INSERT INTO t_device_field (
    device_type_code,
    field_name,
    field_code,
    field_type,
    field_category,
    unit,
    description,
    is_required,
    sort_order,
    is_active,
    is_monitoring_key,
    is_ai_feature,
    aggregation_method,
    data_range,
    alarm_threshold,
    display_config,
    created_at,
    updated_at
)
SELECT 
    'PRESSURE_SENSOR_V1',
    '温度',
    'temperature',
    'float',
    'data_collection',
    '°C',
    '传感器温度',
    true,
    2,
    true,
    true,
    true,
    'avg',
    '{"min": -20, "max": 80}'::jsonb,
    '{"warning": 70, "critical": 75}'::jsonb,
    '{"icon": "🌡️", "color": "#ff4d4f"}'::jsonb,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM t_device_field 
    WHERE device_type_code = 'PRESSURE_SENSOR_V1' AND field_code = 'temperature'
);

-- 3. 配置振动值字段
INSERT INTO t_device_field (
    device_type_code,
    field_name,
    field_code,
    field_type,
    field_category,
    unit,
    description,
    is_required,
    sort_order,
    is_active,
    is_monitoring_key,
    is_ai_feature,
    aggregation_method,
    data_range,
    alarm_threshold,
    display_config,
    created_at,
    updated_at
)
SELECT 
    'PRESSURE_SENSOR_V1',
    '振动值',
    'vibration',
    'float',
    'data_collection',
    'mm/s',
    '设备振动强度',
    false,
    3,
    true,
    true,
    true,
    'max',
    '{"min": 0, "max": 50}'::jsonb,
    '{"warning": 40, "critical": 45}'::jsonb,
    '{"icon": "📳", "color": "#faad14"}'::jsonb,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM t_device_field 
    WHERE device_type_code = 'PRESSURE_SENSOR_V1' AND field_code = 'vibration'
);

-- 4. 配置设备状态字段
INSERT INTO t_device_field (
    device_type_code,
    field_name,
    field_code,
    field_type,
    field_category,
    unit,
    description,
    is_required,
    sort_order,
    is_active,
    is_monitoring_key,
    aggregation_method,
    created_at,
    updated_at
)
SELECT 
    'PRESSURE_SENSOR_V1',
    '设备状态',
    'status',
    'string',
    'data_collection',
    NULL,
    '设备运行状态：online/offline/error/maintenance',
    true,
    4,
    true,
    true,
    'last',
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM t_device_field 
    WHERE device_type_code = 'PRESSURE_SENSOR_V1' AND field_code = 'status'
);

-- =====================================================
-- 验证配置结果
-- =====================================================

-- 查询焊机的监测字段
SELECT 
    device_type_code,
    field_name,
    field_code,
    field_type,
    unit,
    sort_order,
    is_monitoring_key,
    display_config
FROM t_device_field
WHERE device_type_code = 'welding' 
  AND is_monitoring_key = true
  AND is_active = true
ORDER BY sort_order;

-- 查询压力传感器的监测字段
SELECT 
    device_type_code,
    field_name,
    field_code,
    field_type,
    unit,
    sort_order,
    is_monitoring_key,
    display_config
FROM t_device_field
WHERE device_type_code = 'PRESSURE_SENSOR_V1' 
  AND is_monitoring_key = true
  AND is_active = true
ORDER BY sort_order;

-- 统计监测字段数量
SELECT 
    device_type_code,
    COUNT(*) as monitoring_field_count
FROM t_device_field
WHERE is_monitoring_key = true 
  AND is_active = true
GROUP BY device_type_code
ORDER BY device_type_code;
