-- =====================================================
-- 002: 创建 t_device_data_model 表
-- 
-- 目的: 创建设备数据模型定义表，支持实时监控/统计分析/AI特征三种模型类型
-- 原则: 新增表，不修改现有表
-- 兼容性: 通过外键关联现有 t_device_type 表
-- =====================================================

-- 开始事务
BEGIN;

-- 1. 创建设备数据模型表
CREATE TABLE IF NOT EXISTS t_device_data_model (
    -- 基础字段
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_code VARCHAR(50) NOT NULL,
    device_type_code VARCHAR(50) NOT NULL,
    model_type VARCHAR(30) NOT NULL CHECK (model_type IN ('realtime', 'statistics', 'ai_analysis')),
    
    -- 字段选择配置（JSONB格式）
    selected_fields JSONB NOT NULL,
    /* selected_fields 格式示例:
    [
        {
            "field_code": "avg_current",
            "alias": "电流",
            "weight": 1.0,
            "is_required": true,
            "transform": null
        },
        {
            "field_code": "avg_voltage",
            "alias": "电压",
            "weight": 1.0,
            "is_required": true,
            "transform": null
        }
    ]
    */
    
    -- 聚合配置（用于 statistics 类型）
    aggregation_config JSONB,
    /* aggregation_config 格式示例:
    {
        "time_window": "1h",
        "interval": "5m",
        "methods": ["avg", "max", "min", "sum"],
        "group_by": ["device_code", "shift_name"],
        "custom_expressions": {
            "power": "avg_current * avg_voltage",
            "efficiency": "weld_count / duration_sec * 3600"
        }
    }
    */
    
    -- AI配置（用于 ai_analysis 类型）
    ai_config JSONB,
    /* ai_config 格式示例:
    {
        "algorithm": "anomaly_detection",
        "features": ["avg_current", "avg_voltage", "spec_match_rate"],
        "normalization": "min-max",
        "window_size": 100,
        "missing_value_strategy": "interpolate",
        "outlier_threshold": 3.0,
        "training_params": {
            "contamination": 0.1,
            "n_estimators": 100
        }
    }
    */
    
    -- 版本管理
    version VARCHAR(20) NOT NULL DEFAULT '1.0',
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    description TEXT,
    
    -- ⭐ 外键约束：关联现有表
    CONSTRAINT fk_data_model_device_type 
        FOREIGN KEY (device_type_code) 
        REFERENCES t_device_type(type_code) 
        ON DELETE CASCADE,
    
    -- 审计字段
    created_by INTEGER,
    updated_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 唯一性约束
    CONSTRAINT uk_model_code_version UNIQUE (model_code, version)
);

-- 2. 添加表注释
COMMENT ON TABLE t_device_data_model IS '设备数据模型定义表';
COMMENT ON COLUMN t_device_data_model.model_name IS '模型名称（中文）';
COMMENT ON COLUMN t_device_data_model.model_code IS '模型编码（唯一标识）';
COMMENT ON COLUMN t_device_data_model.device_type_code IS '设备类型代码（外键关联t_device_type）';
COMMENT ON COLUMN t_device_data_model.model_type IS '模型类型：realtime/statistics/ai_analysis';
COMMENT ON COLUMN t_device_data_model.selected_fields IS '选中的字段列表（JSONB数组）';
COMMENT ON COLUMN t_device_data_model.aggregation_config IS '聚合配置（JSONB对象，用于统计分析）';
COMMENT ON COLUMN t_device_data_model.ai_config IS 'AI配置（JSONB对象，用于AI分析）';
COMMENT ON COLUMN t_device_data_model.version IS '模型版本';
COMMENT ON COLUMN t_device_data_model.is_active IS '是否激活（只能有一个版本激活）';
COMMENT ON COLUMN t_device_data_model.is_default IS '是否为默认模型';

-- 3. 创建索引
CREATE INDEX IF NOT EXISTS idx_data_model_device_type 
ON t_device_data_model(device_type_code);

CREATE INDEX IF NOT EXISTS idx_data_model_type 
ON t_device_data_model(model_type);

CREATE INDEX IF NOT EXISTS idx_data_model_active 
ON t_device_data_model(device_type_code, model_type, is_active) 
WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_data_model_code 
ON t_device_data_model(model_code);

CREATE INDEX IF NOT EXISTS idx_data_model_created_at 
ON t_device_data_model(created_at DESC);

-- 4. 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_data_model_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_data_model_timestamp
BEFORE UPDATE ON t_device_data_model
FOR EACH ROW
EXECUTE FUNCTION update_data_model_timestamp();

-- 提交事务
COMMIT;

-- =====================================================
-- 验证脚本执行结果
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE '✅ 002_create_device_data_model.sql 执行成功！';
    RAISE NOTICE '   - 创建表: t_device_data_model';
    RAISE NOTICE '   - 外键关联: t_device_type.type_code';
    RAISE NOTICE '   - 唯一约束: (model_code, version)';
    RAISE NOTICE '   - 创建索引: 5个（device_type, type, active, code, created_at）';
    RAISE NOTICE '   - 创建触发器: update_data_model_timestamp';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  注意: 现有表完全不受影响';
END $$;

