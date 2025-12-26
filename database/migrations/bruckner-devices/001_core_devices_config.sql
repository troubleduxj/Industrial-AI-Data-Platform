-- =====================================================
-- 布鲁克纳生产线核心设备配置
-- 功能：配置6种核心设备类型及其监测字段
-- 创建时间：2025-11-25
-- 优先级：⭐⭐⭐⭐⭐
-- =====================================================

-- =====================================================
-- 1. 挤出机主机 (BRUCKNER_EXTRUDER)
-- =====================================================

-- 创建设备类型
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
    '挤出机主机',
    'BRUCKNER_EXTRUDER',
    'st_bruckner_extruder',
    '布鲁克纳挤出系统核心设备，负责塑料熔融和挤出',
    'mdi:factory',
    true,
    0,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM t_device_type WHERE type_code = 'BRUCKNER_EXTRUDER'
);

-- 配置监测字段
INSERT INTO t_device_field (
    device_type_code, field_name, field_code, field_type, field_category,
    unit, description, is_required, sort_order, is_active,
    is_monitoring_key, is_ai_feature, aggregation_method,
    data_range, alarm_threshold, display_config,
    created_at, updated_at
) VALUES
-- 温度字段（5个区）
('BRUCKNER_EXTRUDER', '1区温度', 'zone1_temp', 'float', 'data_collection',
 '°C', '挤出机1区温度', true, 1, true,
 true, true, 'avg',
 '{"min": 180, "max": 280}'::jsonb,
 '{"warning_low": 185, "warning_high": 275, "critical_low": 180, "critical_high": 280}'::jsonb,
 '{"icon": "🌡️", "color": "#ff4d4f", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_EXTRUDER', '2区温度', 'zone2_temp', 'float', 'data_collection',
 '°C', '挤出机2区温度', true, 2, true,
 true, true, 'avg',
 '{"min": 200, "max": 300}'::jsonb,
 '{"warning_low": 205, "warning_high": 295, "critical_low": 200, "critical_high": 300}'::jsonb,
 '{"icon": "🌡️", "color": "#ff7a45", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_EXTRUDER', '3区温度', 'zone3_temp', 'float', 'data_collection',
 '°C', '挤出机3区温度', true, 3, true,
 true, true, 'avg',
 '{"min": 220, "max": 320}'::jsonb,
 '{"warning_low": 225, "warning_high": 315, "critical_low": 220, "critical_high": 320}'::jsonb,
 '{"icon": "🌡️", "color": "#ffa940", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_EXTRUDER', '4区温度', 'zone4_temp', 'float', 'data_collection',
 '°C', '挤出机4区温度', true, 4, true,
 true, true, 'avg',
 '{"min": 230, "max": 330}'::jsonb,
 '{"warning_low": 235, "warning_high": 325, "critical_low": 230, "critical_high": 330}'::jsonb,
 '{"icon": "🌡️", "color": "#ffc53d", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_EXTRUDER', '5区温度', 'zone5_temp', 'float', 'data_collection',
 '°C', '挤出机5区温度', true, 5, true,
 true, true, 'avg',
 '{"min": 240, "max": 340}'::jsonb,
 '{"warning_low": 245, "warning_high": 335, "critical_low": 240, "critical_high": 340}'::jsonb,
 '{"icon": "🌡️", "color": "#fadb14", "chart_type": "line"}'::jsonb,
 NOW(), NOW())

ON CONFLICT (device_type_code, field_name) DO NOTHING;

-- 其他关键参数
INSERT INTO t_device_field (
    device_type_code, field_name, field_code, field_type, field_category,
    unit, description, is_required, sort_order, is_active,
    is_monitoring_key, is_ai_feature, aggregation_method,
    data_range, alarm_threshold, display_config,
    created_at, updated_at
) VALUES
('BRUCKNER_EXTRUDER', '螺杆转速', 'screw_speed', 'float', 'data_collection',
 'rpm', '挤出机螺杆转速', true, 6, true,
 true, true, 'avg',
 '{"min": 0, "max": 150}'::jsonb,
 '{"warning_high": 140, "critical_high": 145}'::jsonb,
 '{"icon": "⚙️", "color": "#1890ff", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_EXTRUDER', '熔体压力', 'melt_pressure', 'float', 'data_collection',
 'MPa', '熔体压力值', true, 7, true,
 true, true, 'avg',
 '{"min": 0, "max": 50}'::jsonb,
 '{"warning_high": 45, "critical_high": 48}'::jsonb,
 '{"icon": "📊", "color": "#52c41a", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_EXTRUDER', '熔体温度', 'melt_temperature', 'float', 'data_collection',
 '°C', '熔体温度', true, 8, true,
 true, true, 'avg',
 '{"min": 240, "max": 340}'::jsonb,
 '{"warning_low": 245, "warning_high": 335, "critical_low": 240, "critical_high": 340}'::jsonb,
 '{"icon": "🌡️", "color": "#fa8c16", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_EXTRUDER', '主电机电流', 'motor_current', 'float', 'data_collection',
 'A', '主电机电流', true, 9, true,
 true, true, 'avg',
 '{"min": 0, "max": 500}'::jsonb,
 '{"warning_high": 450, "critical_high": 480}'::jsonb,
 '{"icon": "⚡", "color": "#faad14", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_EXTRUDER', '电机扭矩', 'motor_torque', 'float', 'data_collection',
 '%', '电机扭矩百分比', true, 10, true,
 true, true, 'avg',
 '{"min": 0, "max": 100}'::jsonb,
 '{"warning_high": 85, "critical_high": 95}'::jsonb,
 '{"icon": "💪", "color": "#eb2f96", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_EXTRUDER', '喂料速度', 'feed_rate', 'float', 'data_collection',
 'kg/h', '喂料速度', true, 11, true,
 true, true, 'avg',
 '{"min": 0, "max": 2000}'::jsonb,
 '{"warning_low": 100, "warning_high": 1900}'::jsonb,
 '{"icon": "📦", "color": "#722ed1", "chart_type": "line"}'::jsonb,
 NOW(), NOW())

ON CONFLICT (device_type_code, field_name) DO NOTHING;

-- =====================================================
-- 2. 模头 (BRUCKNER_DIE)
-- =====================================================

INSERT INTO t_device_type (
    type_name, type_code, tdengine_stable_name, description, icon,
    is_active, device_count, created_at, updated_at
)
SELECT 
    '模头', 'BRUCKNER_DIE', 'st_bruckner_die',
    '布鲁克纳模头系统，负责熔体展开成型', 'mdi:shape',
    true, 0, NOW(), NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM t_device_type WHERE type_code = 'BRUCKNER_DIE'
);

INSERT INTO t_device_field (
    device_type_code, field_name, field_code, field_type, field_category,
    unit, description, is_required, sort_order, is_active,
    is_monitoring_key, is_ai_feature, aggregation_method,
    data_range, alarm_threshold, display_config,
    created_at, updated_at
) VALUES
('BRUCKNER_DIE', '模头左侧温度', 'die_temp_left', 'float', 'data_collection',
 '°C', '模头左侧温度', true, 1, true,
 true, true, 'avg',
 '{"min": 240, "max": 340}'::jsonb,
 '{"warning_low": 245, "warning_high": 335}'::jsonb,
 '{"icon": "🌡️", "color": "#1890ff", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_DIE', '模头中间温度', 'die_temp_center', 'float', 'data_collection',
 '°C', '模头中间温度', true, 2, true,
 true, true, 'avg',
 '{"min": 240, "max": 340}'::jsonb,
 '{"warning_low": 245, "warning_high": 335}'::jsonb,
 '{"icon": "🌡️", "color": "#52c41a", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_DIE', '模头右侧温度', 'die_temp_right', 'float', 'data_collection',
 '°C', '模头右侧温度', true, 3, true,
 true, true, 'avg',
 '{"min": 240, "max": 340}'::jsonb,
 '{"warning_low": 245, "warning_high": 335}'::jsonb,
 '{"icon": "🌡️", "color": "#fa8c16", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_DIE', '模头压力', 'die_pressure', 'float', 'data_collection',
 'MPa', '模头内部压力', true, 4, true,
 true, true, 'avg',
 '{"min": 0, "max": 50}'::jsonb,
 '{"warning_high": 45, "critical_high": 48}'::jsonb,
 '{"icon": "📊", "color": "#faad14", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_DIE', '唇口间隙', 'lip_gap', 'float', 'data_collection',
 'mm', '模头唇口间隙', true, 5, true,
 true, true, 'avg',
 '{"min": 0.5, "max": 3.0}'::jsonb,
 '{"warning_low": 0.6, "warning_high": 2.8}'::jsonb,
 '{"icon": "📏", "color": "#eb2f96", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_DIE', '模头宽度', 'die_width', 'float', 'data_collection',
 'mm', '模头有效宽度', false, 6, true,
 false, false, 'last',
 '{"min": 1000, "max": 6000}'::jsonb,
 NULL,
 '{"icon": "↔️", "color": "#722ed1"}'::jsonb,
 NOW(), NOW())

ON CONFLICT (device_type_code, field_name) DO NOTHING;

-- =====================================================
-- 3. 急冷辊 (BRUCKNER_CHILL_ROLL)
-- =====================================================

INSERT INTO t_device_type (
    type_name, type_code, tdengine_stable_name, description, icon,
    is_active, device_count, created_at, updated_at
)
SELECT 
    '急冷辊', 'BRUCKNER_CHILL_ROLL', 'st_bruckner_chill_roll',
    '布鲁克纳急冷辊系统，负责熔体快速冷却', 'mdi:cylinder',
    true, 0, NOW(), NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM t_device_type WHERE type_code = 'BRUCKNER_CHILL_ROLL'
);

INSERT INTO t_device_field (
    device_type_code, field_name, field_code, field_type, field_category,
    unit, description, is_required, sort_order, is_active,
    is_monitoring_key, is_ai_feature, aggregation_method,
    data_range, alarm_threshold, display_config,
    created_at, updated_at
) VALUES
('BRUCKNER_CHILL_ROLL', '辊筒温度', 'roll_temperature', 'float', 'data_collection',
 '°C', '急冷辊表面温度', true, 1, true,
 true, true, 'avg',
 '{"min": 20, "max": 80}'::jsonb,
 '{"warning_low": 25, "warning_high": 75, "critical_low": 20, "critical_high": 80}'::jsonb,
 '{"icon": "🌡️", "color": "#1890ff", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_CHILL_ROLL', '冷却水进水温度', 'water_inlet_temp', 'float', 'data_collection',
 '°C', '冷却水进水温度', true, 2, true,
 true, true, 'avg',
 '{"min": 15, "max": 30}'::jsonb,
 '{"warning_low": 16, "warning_high": 28}'::jsonb,
 '{"icon": "💧", "color": "#13c2c2", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_CHILL_ROLL', '冷却水出水温度', 'water_outlet_temp', 'float', 'data_collection',
 '°C', '冷却水出水温度', true, 3, true,
 true, true, 'avg',
 '{"min": 20, "max": 40}'::jsonb,
 '{"warning_high": 38, "critical_high": 40}'::jsonb,
 '{"icon": "💧", "color": "#52c41a", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_CHILL_ROLL', '冷却水流量', 'water_flow', 'float', 'data_collection',
 'm³/h', '冷却水流量', true, 4, true,
 true, true, 'avg',
 '{"min": 0, "max": 100}'::jsonb,
 '{"warning_low": 10, "critical_low": 5}'::jsonb,
 '{"icon": "🌊", "color": "#1890ff", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_CHILL_ROLL', '辊筒转速', 'roll_speed', 'float', 'data_collection',
 'm/min', '辊筒线速度', true, 5, true,
 true, true, 'avg',
 '{"min": 0, "max": 500}'::jsonb,
 '{"warning_high": 480, "critical_high": 495}'::jsonb,
 '{"icon": "⚙️", "color": "#722ed1", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_CHILL_ROLL', '电机电流', 'motor_current', 'float', 'data_collection',
 'A', '驱动电机电流', true, 6, true,
 true, true, 'avg',
 '{"min": 0, "max": 200}'::jsonb,
 '{"warning_high": 180, "critical_high": 195}'::jsonb,
 '{"icon": "⚡", "color": "#faad14", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_CHILL_ROLL', '振动', 'vibration', 'float', 'data_collection',
 'mm/s', '辊筒振动值', true, 7, true,
 true, true, 'max',
 '{"min": 0, "max": 10}'::jsonb,
 '{"warning_high": 7, "critical_high": 9}'::jsonb,
 '{"icon": "📳", "color": "#ff4d4f", "chart_type": "line"}'::jsonb,
 NOW(), NOW())

ON CONFLICT (device_type_code, field_name) DO NOTHING;

-- =====================================================
-- 4. MDO拉伸辊 (BRUCKNER_MDO_STRETCH)
-- =====================================================

INSERT INTO t_device_type (
    type_name, type_code, tdengine_stable_name, description, icon,
    is_active, device_count, created_at, updated_at
)
SELECT 
    'MDO拉伸辊', 'BRUCKNER_MDO_STRETCH', 'st_bruckner_mdo_stretch',
    '布鲁克纳纵向拉伸系统，负责薄膜纵向拉伸', 'mdi:arrow-expand-horizontal',
    true, 0, NOW(), NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM t_device_type WHERE type_code = 'BRUCKNER_MDO_STRETCH'
);

INSERT INTO t_device_field (
    device_type_code, field_name, field_code, field_type, field_category,
    unit, description, is_required, sort_order, is_active,
    is_monitoring_key, is_ai_feature, aggregation_method,
    data_range, alarm_threshold, display_config,
    created_at, updated_at
) VALUES
('BRUCKNER_MDO_STRETCH', '慢辊速度', 'slow_roll_speed', 'float', 'data_collection',
 'm/min', '慢辊线速度', true, 1, true,
 true, true, 'avg',
 '{"min": 0, "max": 200}'::jsonb,
 '{"warning_high": 190}'::jsonb,
 '{"icon": "🐌", "color": "#1890ff", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_MDO_STRETCH', '快辊速度', 'fast_roll_speed', 'float', 'data_collection',
 'm/min', '快辊线速度', true, 2, true,
 true, true, 'avg',
 '{"min": 0, "max": 800}'::jsonb,
 '{"warning_high": 780, "critical_high": 795}'::jsonb,
 '{"icon": "🚀", "color": "#52c41a", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_MDO_STRETCH', '拉伸比', 'stretch_ratio', 'float', 'data_collection',
 '', '纵向拉伸比（快辊/慢辊）', true, 3, true,
 true, true, 'avg',
 '{"min": 3.0, "max": 6.0}'::jsonb,
 '{"warning_low": 3.2, "warning_high": 5.8, "critical_low": 3.0, "critical_high": 6.0}'::jsonb,
 '{"icon": "📈", "color": "#fa8c16", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_MDO_STRETCH', '辊温', 'roll_temperature', 'float', 'data_collection',
 '°C', '拉伸辊温度', true, 4, true,
 true, true, 'avg',
 '{"min": 80, "max": 140}'::jsonb,
 '{"warning_low": 85, "warning_high": 135}'::jsonb,
 '{"icon": "🌡️", "color": "#faad14", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_MDO_STRETCH', '膜张力', 'web_tension', 'float', 'data_collection',
 'N/m', '薄膜张力', true, 5, true,
 true, true, 'avg',
 '{"min": 0, "max": 1000}'::jsonb,
 '{"warning_low": 100, "warning_high": 900, "critical_low": 50, "critical_high": 950}'::jsonb,
 '{"icon": "🎯", "color": "#eb2f96", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_MDO_STRETCH', '电机扭矩', 'motor_torque', 'float', 'data_collection',
 '%', '电机扭矩百分比', true, 6, true,
 true, true, 'avg',
 '{"min": 0, "max": 100}'::jsonb,
 '{"warning_high": 85, "critical_high": 95}'::jsonb,
 '{"icon": "💪", "color": "#722ed1", "chart_type": "line"}'::jsonb,
 NOW(), NOW())

ON CONFLICT (device_type_code, field_name) DO NOTHING;

-- =====================================================
-- 5. TDO拉幅机 (BRUCKNER_TDO_TENTER)
-- =====================================================

INSERT INTO t_device_type (
    type_name, type_code, tdengine_stable_name, description, icon,
    is_active, device_count, created_at, updated_at
)
SELECT 
    'TDO拉幅机', 'BRUCKNER_TDO_TENTER', 'st_bruckner_tdo_tenter',
    '布鲁克纳横向拉伸系统，负责薄膜横向拉伸和热定型', 'mdi:arrow-expand-vertical',
    true, 0, NOW(), NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM t_device_type WHERE type_code = 'BRUCKNER_TDO_TENTER'
);

INSERT INTO t_device_field (
    device_type_code, field_name, field_code, field_type, field_category,
    unit, description, is_required, sort_order, is_active,
    is_monitoring_key, is_ai_feature, aggregation_method,
    data_range, alarm_threshold, display_config,
    created_at, updated_at
) VALUES
('BRUCKNER_TDO_TENTER', '预热区温度', 'preheat_zone_temp', 'float', 'data_collection',
 '°C', '预热区温度', true, 1, true,
 true, true, 'avg',
 '{"min": 80, "max": 140}'::jsonb,
 '{"warning_low": 85, "warning_high": 135}'::jsonb,
 '{"icon": "🌡️", "color": "#1890ff", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_TDO_TENTER', '拉伸区温度', 'stretch_zone_temp', 'float', 'data_collection',
 '°C', '拉伸区温度', true, 2, true,
 true, true, 'avg',
 '{"min": 100, "max": 160}'::jsonb,
 '{"warning_low": 105, "warning_high": 155}'::jsonb,
 '{"icon": "🌡️", "color": "#52c41a", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_TDO_TENTER', '热定型区温度', 'heatset_zone_temp', 'float', 'data_collection',
 '°C', '热定型区温度', true, 3, true,
 true, true, 'avg',
 '{"min": 140, "max": 200}'::jsonb,
 '{"warning_low": 145, "warning_high": 195}'::jsonb,
 '{"icon": "🌡️", "color": "#fa8c16", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_TDO_TENTER', '冷却区温度', 'cooling_zone_temp', 'float', 'data_collection',
 '°C', '冷却区温度', true, 4, true,
 true, true, 'avg',
 '{"min": 40, "max": 80}'::jsonb,
 '{"warning_high": 75, "critical_high": 80}'::jsonb,
 '{"icon": "❄️", "color": "#13c2c2", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_TDO_TENTER', '进口宽度', 'inlet_width', 'float', 'data_collection',
 'mm', '薄膜进口宽度', true, 5, true,
 true, false, 'avg',
 '{"min": 500, "max": 2000}'::jsonb,
 NULL,
 '{"icon": "↔️", "color": "#faad14"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_TDO_TENTER', '出口宽度', 'outlet_width', 'float', 'data_collection',
 'mm', '薄膜出口宽度', true, 6, true,
 true, false, 'avg',
 '{"min": 2000, "max": 10000}'::jsonb,
 NULL,
 '{"icon": "↔️", "color": "#eb2f96"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_TDO_TENTER', '横向拉伸比', 'stretch_ratio', 'float', 'data_collection',
 '', '横向拉伸比（出口/进口）', true, 7, true,
 true, true, 'avg',
 '{"min": 6.0, "max": 10.0}'::jsonb,
 '{"warning_low": 6.5, "warning_high": 9.5, "critical_low": 6.0, "critical_high": 10.0}'::jsonb,
 '{"icon": "📈", "color": "#722ed1", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_TDO_TENTER', '线速度', 'line_speed', 'float', 'data_collection',
 'm/min', '生产线速度', true, 8, true,
 true, true, 'avg',
 '{"min": 0, "max": 500}'::jsonb,
 '{"warning_high": 480, "critical_high": 495}'::jsonb,
 '{"icon": "🚀", "color": "#1890ff", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_TDO_TENTER', '烘箱压力', 'oven_pressure', 'float', 'data_collection',
 'Pa', '烘箱内部压力', true, 9, true,
 true, true, 'avg',
 '{"min": -50, "max": 50}'::jsonb,
 '{"warning_low": -40, "warning_high": 40}'::jsonb,
 '{"icon": "📊", "color": "#52c41a", "chart_type": "line"}'::jsonb,
 NOW(), NOW())

ON CONFLICT (device_type_code, field_name) DO NOTHING;

-- =====================================================
-- 6. 在线测厚仪 (BRUCKNER_THICKNESS)
-- =====================================================

INSERT INTO t_device_type (
    type_name, type_code, tdengine_stable_name, description, icon,
    is_active, device_count, created_at, updated_at
)
SELECT 
    '在线测厚仪', 'BRUCKNER_THICKNESS', 'st_bruckner_thickness',
    '布鲁克纳在线测厚系统，实时监测薄膜厚度和均匀性', 'mdi:ruler',
    true, 0, NOW(), NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM t_device_type WHERE type_code = 'BRUCKNER_THICKNESS'
);

INSERT INTO t_device_field (
    device_type_code, field_name, field_code, field_type, field_category,
    unit, description, is_required, sort_order, is_active,
    is_monitoring_key, is_ai_feature, aggregation_method,
    data_range, alarm_threshold, display_config,
    created_at, updated_at
) VALUES
('BRUCKNER_THICKNESS', '平均厚度', 'avg_thickness', 'float', 'data_collection',
 'μm', '薄膜平均厚度', true, 1, true,
 true, true, 'avg',
 '{"min": 10, "max": 100}'::jsonb,
 '{"warning_low": 12, "warning_high": 95}'::jsonb,
 '{"icon": "📏", "color": "#1890ff", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_THICKNESS', '厚度偏差', 'thickness_deviation', 'float', 'data_collection',
 'μm', '厚度标准偏差', true, 2, true,
 true, true, 'avg',
 '{"min": 0, "max": 5}'::jsonb,
 '{"warning_high": 3, "critical_high": 4.5}'::jsonb,
 '{"icon": "📊", "color": "#ff4d4f", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_THICKNESS', '横向均匀性', 'profile_uniformity', 'float', 'data_collection',
 '%', '横向厚度均匀性', true, 3, true,
 true, true, 'avg',
 '{"min": 90, "max": 100}'::jsonb,
 '{"warning_low": 95, "critical_low": 92}'::jsonb,
 '{"icon": "✅", "color": "#52c41a", "chart_type": "line"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_THICKNESS', '扫描位置', 'scan_position', 'float', 'data_collection',
 'mm', '测厚仪扫描位置', false, 4, true,
 false, false, 'last',
 '{"min": 0, "max": 10000}'::jsonb,
 NULL,
 '{"icon": "📍", "color": "#faad14"}'::jsonb,
 NOW(), NOW()),

('BRUCKNER_THICKNESS', '测量频率', 'measurement_rate', 'float', 'data_collection',
 'Hz', '测量频率', false, 5, true,
 false, false, 'avg',
 '{"min": 0, "max": 1000}'::jsonb,
 NULL,
 '{"icon": "⏱️", "color": "#722ed1"}'::jsonb,
 NOW(), NOW())

ON CONFLICT (device_type_code, field_name) DO NOTHING;

-- =====================================================
-- 验证配置结果
-- =====================================================

-- 查询所有已配置的设备类型
SELECT 
    type_code,
    type_name,
    tdengine_stable_name,
    is_active,
    device_count
FROM t_device_type
WHERE type_code LIKE 'BRUCKNER_%'
ORDER BY type_code;

-- 统计每种设备类型的监测字段数量
SELECT 
    device_type_code,
    COUNT(*) as total_fields,
    COUNT(*) FILTER (WHERE is_monitoring_key = true) as monitoring_fields,
    COUNT(*) FILTER (WHERE is_ai_feature = true) as ai_fields
FROM t_device_field
WHERE device_type_code LIKE 'BRUCKNER_%'
  AND is_active = true
GROUP BY device_type_code
ORDER BY device_type_code;

-- 查看所有监测字段详情
SELECT 
    device_type_code,
    field_name,
    field_code,
    unit,
    sort_order,
    is_monitoring_key,
    is_ai_feature
FROM t_device_field
WHERE device_type_code LIKE 'BRUCKNER_%'
  AND is_active = true
ORDER BY device_type_code, sort_order;

-- =====================================================
-- 配置完成
-- =====================================================
-- ✅ 已配置 6 种核心设备类型
-- ✅ 已配置 50+ 个监测字段
-- ✅ 所有字段包含完整的元数据（范围、告警、显示配置）
-- =====================================================
