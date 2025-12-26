-- =====================================================
-- 007: 创建默认数据模型
-- 
-- 目的: 为焊接设备创建3个默认数据模型（实时监控/统计分析/AI特征）
-- 原则: 只 INSERT 数据，不修改表结构
-- 兼容性: 100% 向后兼容
-- =====================================================

-- 开始事务
BEGIN;

-- =====================================================
-- 1. 创建实时监控模型
-- =====================================================
INSERT INTO t_device_data_model (
    model_name,
    model_code,
    device_type_code,
    model_type,
    selected_fields,
    aggregation_config,
    ai_config,
    version,
    is_active,
    is_default,
    description,
    created_by,
    updated_by
) VALUES (
    '焊接设备实时监控模型',
    'welding_realtime_v1',
    'welding',
    'realtime',
    '[
        {
            "field_code": "device_code",
            "alias": "设备编号",
            "weight": 1.0,
            "is_required": true,
            "transform": null
        },
        {
            "field_code": "ts",
            "alias": "时间戳",
            "weight": 1.0,
            "is_required": true,
            "transform": null
        },
        {
            "field_code": "avg_current",
            "alias": "平均电流",
            "weight": 1.5,
            "is_required": true,
            "transform": null
        },
        {
            "field_code": "avg_voltage",
            "alias": "平均电压",
            "weight": 1.5,
            "is_required": true,
            "transform": null
        },
        {
            "field_code": "spec_match_rate",
            "alias": "规范匹配率",
            "weight": 2.0,
            "is_required": true,
            "transform": null
        },
        {
            "field_code": "wire_consumption",
            "alias": "焊丝消耗",
            "weight": 1.0,
            "is_required": false,
            "transform": null
        },
        {
            "field_code": "duration_sec",
            "alias": "焊接时长",
            "weight": 1.0,
            "is_required": false,
            "transform": null
        }
    ]'::jsonb,
    NULL,  -- 实时监控不需要聚合配置
    NULL,  -- 实时监控不需要AI配置
    '1.0',
    TRUE,   -- 激活
    TRUE,   -- 设为默认
    '用于实时监控焊接设备关键参数的数据模型，包含电流、电压、规范匹配率等核心指标',
    1,      -- 系统管理员
    1
) ON CONFLICT (model_code, version) DO NOTHING;

-- =====================================================
-- 2. 创建统计分析模型
-- =====================================================
INSERT INTO t_device_data_model (
    model_name,
    model_code,
    device_type_code,
    model_type,
    selected_fields,
    aggregation_config,
    ai_config,
    version,
    is_active,
    is_default,
    description,
    created_by,
    updated_by
) VALUES (
    '焊接设备每日统计模型',
    'welding_statistics_daily_v1',
    'welding',
    'statistics',
    '[
        {
            "field_code": "device_code",
            "alias": "设备编号",
            "weight": 1.0,
            "is_required": true,
            "transform": null
        },
        {
            "field_code": "team_name",
            "alias": "班组名称",
            "weight": 1.0,
            "is_required": false,
            "transform": null
        },
        {
            "field_code": "shift_name",
            "alias": "班次名称",
            "weight": 1.0,
            "is_required": false,
            "transform": null
        },
        {
            "field_code": "avg_current",
            "alias": "平均电流",
            "weight": 1.5,
            "is_required": true,
            "transform": null
        },
        {
            "field_code": "avg_voltage",
            "alias": "平均电压",
            "weight": 1.5,
            "is_required": true,
            "transform": null
        },
        {
            "field_code": "spec_match_rate",
            "alias": "规范匹配率",
            "weight": 2.0,
            "is_required": true,
            "transform": null
        },
        {
            "field_code": "wire_consumption",
            "alias": "焊丝消耗",
            "weight": 1.0,
            "is_required": false,
            "transform": null
        },
        {
            "field_code": "duration_sec",
            "alias": "焊接时长",
            "weight": 1.0,
            "is_required": false,
            "transform": null
        },
        {
            "field_code": "weld_count",
            "alias": "焊接次数",
            "weight": 1.0,
            "is_required": false,
            "transform": null
        }
    ]'::jsonb,
    '{
        "time_window": "1d",
        "interval": "1h",
        "methods": ["avg", "max", "min", "sum", "count"],
        "group_by": ["device_code", "team_name", "shift_name"],
        "custom_expressions": {
            "total_power": "AVG(avg_current * avg_voltage)",
            "efficiency": "SUM(weld_count) / SUM(duration_sec) * 3600",
            "avg_wire_rate": "SUM(wire_consumption) / SUM(duration_sec) * 3600"
        },
        "filters": {
            "min_duration": 1,
            "max_duration": 3600
        }
    }'::jsonb,
    NULL,  -- 统计分析不需要AI配置
    '1.0',
    TRUE,   -- 激活
    FALSE,  -- 不设为默认（实时监控是默认）
    '用于每日焊接设备统计分析的数据模型，支持按班组、班次聚合，计算效率和功率等衍生指标',
    1,
    1
) ON CONFLICT (model_code, version) DO NOTHING;

-- =====================================================
-- 3. 创建AI特征提取模型
-- =====================================================
INSERT INTO t_device_data_model (
    model_name,
    model_code,
    device_type_code,
    model_type,
    selected_fields,
    aggregation_config,
    ai_config,
    version,
    is_active,
    is_default,
    description,
    created_by,
    updated_by
) VALUES (
    '焊接设备异常检测AI模型',
    'welding_ai_anomaly_v1',
    'welding',
    'ai_analysis',
    '[
        {
            "field_code": "avg_current",
            "alias": "平均电流",
            "weight": 1.5,
            "is_required": true,
            "transform": "normalize"
        },
        {
            "field_code": "avg_voltage",
            "alias": "平均电压",
            "weight": 1.5,
            "is_required": true,
            "transform": "normalize"
        },
        {
            "field_code": "spec_match_rate",
            "alias": "规范匹配率",
            "weight": 2.0,
            "is_required": true,
            "transform": "normalize"
        },
        {
            "field_code": "wire_consumption",
            "alias": "焊丝消耗",
            "weight": 1.2,
            "is_required": true,
            "transform": "normalize"
        },
        {
            "field_code": "duration_sec",
            "alias": "焊接时长",
            "weight": 1.0,
            "is_required": true,
            "transform": "normalize"
        },
        {
            "field_code": "max_current",
            "alias": "最大电流",
            "weight": 1.0,
            "is_required": false,
            "transform": "normalize"
        },
        {
            "field_code": "min_current",
            "alias": "最小电流",
            "weight": 1.0,
            "is_required": false,
            "transform": "normalize"
        },
        {
            "field_code": "max_voltage",
            "alias": "最大电压",
            "weight": 1.0,
            "is_required": false,
            "transform": "normalize"
        },
        {
            "field_code": "min_voltage",
            "alias": "最小电压",
            "weight": 1.0,
            "is_required": false,
            "transform": "normalize"
        }
    ]'::jsonb,
    NULL,  -- AI特征提取不需要聚合配置
    '{
        "algorithm": "isolation_forest",
        "purpose": "anomaly_detection",
        "features": [
            "avg_current",
            "avg_voltage",
            "spec_match_rate",
            "wire_consumption",
            "duration_sec",
            "max_current",
            "min_current",
            "max_voltage",
            "min_voltage"
        ],
        "normalization": "min-max",
        "window_size": 100,
        "missing_value_strategy": "interpolate",
        "outlier_threshold": 3.0,
        "training_params": {
            "contamination": 0.05,
            "n_estimators": 100,
            "max_samples": "auto",
            "random_state": 42
        },
        "feature_engineering": {
            "power": "avg_current * avg_voltage",
            "current_variance": "max_current - min_current",
            "voltage_variance": "max_voltage - min_voltage",
            "wire_rate": "wire_consumption / duration_sec"
        }
    }'::jsonb,
    '1.0',
    TRUE,   -- 激活
    FALSE,  -- 不设为默认
    '用于焊接设备异常检测的AI模型，基于Isolation Forest算法，提取9个核心特征并进行归一化处理',
    1,
    1
) ON CONFLICT (model_code, version) DO NOTHING;

-- 提交事务
COMMIT;

-- =====================================================
-- 验证脚本执行结果
-- =====================================================
DO $$
DECLARE
    v_realtime_count INTEGER;
    v_statistics_count INTEGER;
    v_ai_count INTEGER;
    v_active_count INTEGER;
BEGIN
    -- 统计模型结果
    SELECT COUNT(*) INTO v_realtime_count 
    FROM t_device_data_model 
    WHERE device_type_code = 'welding' AND model_type = 'realtime';
    
    SELECT COUNT(*) INTO v_statistics_count 
    FROM t_device_data_model 
    WHERE device_type_code = 'welding' AND model_type = 'statistics';
    
    SELECT COUNT(*) INTO v_ai_count 
    FROM t_device_data_model 
    WHERE device_type_code = 'welding' AND model_type = 'ai_analysis';
    
    SELECT COUNT(*) INTO v_active_count 
    FROM t_device_data_model 
    WHERE device_type_code = 'welding' AND is_active = TRUE;
    
    -- 输出结果
    RAISE NOTICE '✅ 007_create_default_models.sql 执行成功！';
    RAISE NOTICE '   - 实时监控模型: % 个', v_realtime_count;
    RAISE NOTICE '   - 统计分析模型: % 个', v_statistics_count;
    RAISE NOTICE '   - AI特征模型: % 个', v_ai_count;
    RAISE NOTICE '   - 已激活模型: % 个', v_active_count;
    RAISE NOTICE '';
    RAISE NOTICE '🎯 模型代码:';
    RAISE NOTICE '   - welding_realtime_v1 (默认)';
    RAISE NOTICE '   - welding_statistics_daily_v1';
    RAISE NOTICE '   - welding_ai_anomaly_v1';
END $$;

