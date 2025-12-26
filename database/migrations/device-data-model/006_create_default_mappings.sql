-- =====================================================
-- 006: 创建默认字段映射
-- 
-- 目的: 为焊接设备创建PostgreSQL与TDengine的字段映射关系
-- 原则: 只 INSERT 数据，不修改表结构
-- 兼容性: 100% 向后兼容
-- =====================================================

-- 开始事务
BEGIN;

-- =====================================================
-- 1. 为焊接设备创建字段映射
-- =====================================================

-- 插入焊接设备的所有字段映射
INSERT INTO t_device_field_mapping (
    device_type_code,
    tdengine_database,
    tdengine_stable,
    tdengine_column,
    device_field_id,
    transform_rule,
    is_tag,
    is_active
)
SELECT 
    'welding' as device_type_code,
    'hlzg_db' as tdengine_database,
    'welding_record_his' as tdengine_stable,
    df.field_code as tdengine_column,
    df.id as device_field_id,
    -- 根据字段类型设置默认转换规则
    CASE 
        WHEN df.field_code LIKE '%current%' AND df.unit = 'mA' THEN
            '{"type": "unit_conversion", "from": "mA", "to": "A", "factor": 0.001}'::jsonb
        WHEN df.field_code LIKE '%_rate%' THEN
            '{"type": "percentage", "max": 100, "min": 0}'::jsonb
        ELSE
            NULL
    END as transform_rule,
    -- 标记TAG列（根据字段分类判断）
    CASE 
        WHEN df.field_code IN ('device_code', 'team_name', 'shift_name', 'operator_name', 'operator_code', 'workpiece_code') THEN
            TRUE
        ELSE
            FALSE
    END as is_tag,
    df.is_active as is_active
FROM t_device_field df
WHERE df.device_type_code = 'welding'
AND df.is_active = TRUE
-- 避免重复插入
AND NOT EXISTS (
    SELECT 1 
    FROM t_device_field_mapping dfm 
    WHERE dfm.device_field_id = df.id
);

-- =====================================================
-- 2. 设置特定字段的转换规则
-- =====================================================

-- 电流字段：范围限制 + 单位转换
UPDATE t_device_field_mapping 
SET transform_rule = '{
    "type": "composite",
    "rules": [
        {"type": "range_limit", "min": 0, "max": 500},
        {"type": "round", "decimals": 1}
    ]
}'::jsonb
WHERE tdengine_stable = 'welding_record_his' 
AND tdengine_column IN ('avg_current', 'max_current', 'min_current');

-- 电压字段：范围限制
UPDATE t_device_field_mapping 
SET transform_rule = '{
    "type": "composite",
    "rules": [
        {"type": "range_limit", "min": 0, "max": 50},
        {"type": "round", "decimals": 1}
    ]
}'::jsonb
WHERE tdengine_stable = 'welding_record_his' 
AND tdengine_column IN ('avg_voltage', 'max_voltage', 'min_voltage');

-- 百分比字段：范围限制 0-100
UPDATE t_device_field_mapping 
SET transform_rule = '{
    "type": "composite",
    "rules": [
        {"type": "range_limit", "min": 0, "max": 100},
        {"type": "round", "decimals": 1}
    ]
}'::jsonb
WHERE tdengine_stable = 'welding_record_his' 
AND tdengine_column = 'spec_match_rate';

-- 时间戳字段：时区转换
UPDATE t_device_field_mapping 
SET transform_rule = '{
    "type": "timestamp",
    "from_timezone": "UTC",
    "to_timezone": "Asia/Shanghai",
    "format": "YYYY-MM-DD HH:mm:ss"
}'::jsonb
WHERE tdengine_stable = 'welding_record_his' 
AND tdengine_column IN ('ts', 'weld_end_time');

-- 字符串字段：清理空格
UPDATE t_device_field_mapping 
SET transform_rule = '{
    "type": "string_clean",
    "trim": true,
    "to_upper": false
}'::jsonb
WHERE tdengine_stable = 'welding_record_his' 
AND tdengine_column IN ('team_name', 'shift_name', 'operator_name', 'workpiece_code')
AND is_tag = TRUE;

-- =====================================================
-- 3. 创建其他设备类型的映射（如果存在）
-- =====================================================

-- 为切割设备创建映射（如果存在）
INSERT INTO t_device_field_mapping (
    device_type_code,
    tdengine_database,
    tdengine_stable,
    tdengine_column,
    device_field_id,
    transform_rule,
    is_tag,
    is_active
)
SELECT 
    'cutting' as device_type_code,
    'hlzg_db' as tdengine_database,
    'cutting_record_his' as tdengine_stable,
    df.field_code as tdengine_column,
    df.id as device_field_id,
    NULL as transform_rule,
    CASE 
        WHEN df.field_code IN ('device_code', 'operator_name') THEN TRUE
        ELSE FALSE
    END as is_tag,
    df.is_active as is_active
FROM t_device_field df
WHERE df.device_type_code = 'cutting'
AND df.is_active = TRUE
AND NOT EXISTS (
    SELECT 1 
    FROM t_device_field_mapping dfm 
    WHERE dfm.device_field_id = df.id
);

-- 为装配设备创建映射（如果存在）
INSERT INTO t_device_field_mapping (
    device_type_code,
    tdengine_database,
    tdengine_stable,
    tdengine_column,
    device_field_id,
    transform_rule,
    is_tag,
    is_active
)
SELECT 
    'assembly' as device_type_code,
    'hlzg_db' as tdengine_database,
    'assembly_record_his' as tdengine_stable,
    df.field_code as tdengine_column,
    df.id as device_field_id,
    NULL as transform_rule,
    CASE 
        WHEN df.field_code IN ('device_code', 'operator_name') THEN TRUE
        ELSE FALSE
    END as is_tag,
    df.is_active as is_active
FROM t_device_field df
WHERE df.device_type_code = 'assembly'
AND df.is_active = TRUE
AND NOT EXISTS (
    SELECT 1 
    FROM t_device_field_mapping dfm 
    WHERE dfm.device_field_id = df.id
);

-- 提交事务
COMMIT;

-- =====================================================
-- 验证脚本执行结果
-- =====================================================
DO $$
DECLARE
    v_welding_count INTEGER;
    v_cutting_count INTEGER;
    v_assembly_count INTEGER;
    v_tag_count INTEGER;
    v_transform_count INTEGER;
BEGIN
    -- 统计映射结果
    SELECT COUNT(*) INTO v_welding_count 
    FROM t_device_field_mapping 
    WHERE device_type_code = 'welding';
    
    SELECT COUNT(*) INTO v_cutting_count 
    FROM t_device_field_mapping 
    WHERE device_type_code = 'cutting';
    
    SELECT COUNT(*) INTO v_assembly_count 
    FROM t_device_field_mapping 
    WHERE device_type_code = 'assembly';
    
    SELECT COUNT(*) INTO v_tag_count 
    FROM t_device_field_mapping 
    WHERE is_tag = TRUE;
    
    SELECT COUNT(*) INTO v_transform_count 
    FROM t_device_field_mapping 
    WHERE transform_rule IS NOT NULL;
    
    -- 输出结果
    RAISE NOTICE '✅ 006_create_default_mappings.sql 执行成功！';
    RAISE NOTICE '   - 焊接设备映射: % 个', v_welding_count;
    RAISE NOTICE '   - 切割设备映射: % 个', v_cutting_count;
    RAISE NOTICE '   - 装配设备映射: % 个', v_assembly_count;
    RAISE NOTICE '   - TAG列: % 个', v_tag_count;
    RAISE NOTICE '   - 有转换规则: % 个', v_transform_count;
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  注意: 映射基于现有字段定义自动生成';
END $$;

