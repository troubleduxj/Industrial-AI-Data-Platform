-- =====================================================
-- 005: 初始化现有字段的新属性
-- 
-- 目的: 为t_device_field表中现有的焊接设备字段设置元数据
-- 原则: 只 UPDATE 数据，不修改表结构
-- 兼容性: 100% 向后兼容
-- =====================================================

-- 开始事务
BEGIN;

-- =====================================================
-- 1. 标记实时监控关键字段
-- =====================================================
UPDATE t_device_field 
SET 
    is_monitoring_key = TRUE,
    aggregation_method = 'avg',
    updated_at = CURRENT_TIMESTAMP
WHERE device_type_code = 'welding' 
AND field_code IN (
    'avg_current',      -- 平均电流
    'avg_voltage',      -- 平均电压
    'spec_match_rate',  -- 规范匹配率
    'wire_consumption', -- 焊丝消耗
    'duration_sec'      -- 焊接时长
);

-- =====================================================
-- 2. 标记AI特征字段
-- =====================================================
UPDATE t_device_field 
SET 
    is_ai_feature = TRUE,
    updated_at = CURRENT_TIMESTAMP
WHERE device_type_code = 'welding' 
AND field_type IN ('int', 'float', 'double')
AND is_active = TRUE
AND field_code IN (
    'avg_current',
    'avg_voltage',
    'spec_match_rate',
    'wire_consumption',
    'duration_sec',
    'weld_count',
    'max_current',
    'min_current',
    'max_voltage',
    'min_voltage'
);

-- =====================================================
-- 3. 设置数据范围（正常值范围）
-- =====================================================

-- 平均电流（0-500A）
UPDATE t_device_field 
SET 
    data_range = '{"min": 0, "max": 500}'::jsonb,
    alarm_threshold = '{"warning": 400, "critical": 450}'::jsonb,
    updated_at = CURRENT_TIMESTAMP
WHERE device_type_code = 'welding' 
AND field_code = 'avg_current';

-- 平均电压（0-50V）
UPDATE t_device_field 
SET 
    data_range = '{"min": 0, "max": 50}'::jsonb,
    alarm_threshold = '{"warning": 40, "critical": 45}'::jsonb,
    updated_at = CURRENT_TIMESTAMP
WHERE device_type_code = 'welding' 
AND field_code = 'avg_voltage';

-- 规范匹配率（0-100%）
UPDATE t_device_field 
SET 
    data_range = '{"min": 0, "max": 100}'::jsonb,
    alarm_threshold = '{"warning": 80, "critical": 70}'::jsonb,
    updated_at = CURRENT_TIMESTAMP
WHERE device_type_code = 'welding' 
AND field_code = 'spec_match_rate';

-- 焊丝消耗（0-10000g）
UPDATE t_device_field 
SET 
    data_range = '{"min": 0, "max": 10000}'::jsonb,
    alarm_threshold = '{"warning": 8000, "critical": 9000}'::jsonb,
    updated_at = CURRENT_TIMESTAMP
WHERE device_type_code = 'welding' 
AND field_code = 'wire_consumption';

-- 焊接时长（0-3600秒）
UPDATE t_device_field 
SET 
    data_range = '{"min": 0, "max": 3600}'::jsonb,
    updated_at = CURRENT_TIMESTAMP
WHERE device_type_code = 'welding' 
AND field_code = 'duration_sec';

-- =====================================================
-- 4. 设置显示配置（前端展示）
-- =====================================================

-- 电流类字段 - 折线图 + 蓝色
UPDATE t_device_field 
SET 
    display_config = '{"chart_type": "line", "color": "#1890ff", "unit_position": "suffix", "decimals": 1}'::jsonb,
    updated_at = CURRENT_TIMESTAMP
WHERE device_type_code = 'welding' 
AND field_code LIKE '%current%';

-- 电压类字段 - 折线图 + 绿色
UPDATE t_device_field 
SET 
    display_config = '{"chart_type": "line", "color": "#52c41a", "unit_position": "suffix", "decimals": 1}'::jsonb,
    updated_at = CURRENT_TIMESTAMP
WHERE device_type_code = 'welding' 
AND field_code LIKE '%voltage%';

-- 百分比类字段 - 折线图 + 橙色
UPDATE t_device_field 
SET 
    display_config = '{"chart_type": "line", "color": "#faad14", "unit_position": "suffix", "decimals": 1}'::jsonb,
    updated_at = CURRENT_TIMESTAMP
WHERE device_type_code = 'welding' 
AND field_code IN ('spec_match_rate');

-- 计数类字段 - 柱状图 + 紫色
UPDATE t_device_field 
SET 
    display_config = '{"chart_type": "bar", "color": "#722ed1", "unit_position": "suffix", "decimals": 0}'::jsonb,
    updated_at = CURRENT_TIMESTAMP
WHERE device_type_code = 'welding' 
AND field_code IN ('weld_count');

-- =====================================================
-- 5. 设置聚合方法
-- =====================================================

-- 平均值聚合
UPDATE t_device_field 
SET 
    aggregation_method = 'avg',
    updated_at = CURRENT_TIMESTAMP
WHERE device_type_code = 'welding' 
AND field_code IN ('avg_current', 'avg_voltage', 'spec_match_rate');

-- 求和聚合
UPDATE t_device_field 
SET 
    aggregation_method = 'sum',
    updated_at = CURRENT_TIMESTAMP
WHERE device_type_code = 'welding' 
AND field_code IN ('wire_consumption', 'duration_sec', 'weld_count');

-- 最大值聚合
UPDATE t_device_field 
SET 
    aggregation_method = 'max',
    updated_at = CURRENT_TIMESTAMP
WHERE device_type_code = 'welding' 
AND field_code IN ('max_current', 'max_voltage');

-- 最小值聚合
UPDATE t_device_field 
SET 
    aggregation_method = 'min',
    updated_at = CURRENT_TIMESTAMP
WHERE device_type_code = 'welding' 
AND field_code IN ('min_current', 'min_voltage');

-- 提交事务
COMMIT;

-- =====================================================
-- 验证脚本执行结果
-- =====================================================
DO $$
DECLARE
    v_monitoring_count INTEGER;
    v_ai_count INTEGER;
    v_range_count INTEGER;
    v_display_count INTEGER;
BEGIN
    -- 统计更新结果
    SELECT COUNT(*) INTO v_monitoring_count 
    FROM t_device_field 
    WHERE device_type_code = 'welding' AND is_monitoring_key = TRUE;
    
    SELECT COUNT(*) INTO v_ai_count 
    FROM t_device_field 
    WHERE device_type_code = 'welding' AND is_ai_feature = TRUE;
    
    SELECT COUNT(*) INTO v_range_count 
    FROM t_device_field 
    WHERE device_type_code = 'welding' AND data_range IS NOT NULL;
    
    SELECT COUNT(*) INTO v_display_count 
    FROM t_device_field 
    WHERE device_type_code = 'welding' AND display_config IS NOT NULL;
    
    -- 输出结果
    RAISE NOTICE '✅ 005_init_field_attributes.sql 执行成功！';
    RAISE NOTICE '   - 实时监控关键字段: % 个', v_monitoring_count;
    RAISE NOTICE '   - AI特征字段: % 个', v_ai_count;
    RAISE NOTICE '   - 设置数据范围: % 个', v_range_count;
    RAISE NOTICE '   - 设置显示配置: % 个', v_display_count;
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  注意: 只更新了焊接设备类型，其他设备类型不受影响';
END $$;

