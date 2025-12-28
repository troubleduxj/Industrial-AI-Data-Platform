-- 工业AI数据平台升级 - 数据库迁移脚本
-- 版本: 001
-- 描述: 创建平台升级核心表

-- =====================================================
-- 阶段1：元数据驱动核心表
-- =====================================================

-- 资产类别表
CREATE TABLE IF NOT EXISTS t_asset_category (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(100),
    industry VARCHAR(50),
    tdengine_database VARCHAR(100) NOT NULL,
    tdengine_stable_prefix VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    asset_count INTEGER DEFAULT 0,
    config JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_asset_category_code ON t_asset_category(code);
CREATE INDEX IF NOT EXISTS idx_asset_category_active_industry ON t_asset_category(is_active, industry);

COMMENT ON TABLE t_asset_category IS '资产类别表';
COMMENT ON COLUMN t_asset_category.code IS '类别编码';
COMMENT ON COLUMN t_asset_category.name IS '类别名称';
COMMENT ON COLUMN t_asset_category.industry IS '所属行业';
COMMENT ON COLUMN t_asset_category.tdengine_database IS 'TDengine数据库名';
COMMENT ON COLUMN t_asset_category.tdengine_stable_prefix IS '超级表前缀';

-- 信号定义表
CREATE TABLE IF NOT EXISTS t_signal_definition (
    id BIGSERIAL PRIMARY KEY,
    category_id BIGINT NOT NULL REFERENCES t_asset_category(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    data_type VARCHAR(20) NOT NULL,
    unit VARCHAR(20),
    is_stored BOOLEAN DEFAULT TRUE,
    is_realtime BOOLEAN DEFAULT TRUE,
    is_feature BOOLEAN DEFAULT FALSE,
    is_alarm_enabled BOOLEAN DEFAULT FALSE,
    value_range JSONB,
    validation_rules JSONB,
    alarm_threshold JSONB,
    aggregation_method VARCHAR(20),
    display_config JSONB,
    sort_order INTEGER DEFAULT 0,
    field_group VARCHAR(50) DEFAULT 'default',
    is_default_visible BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    UNIQUE(category_id, code)
);

CREATE INDEX IF NOT EXISTS idx_signal_definition_category ON t_signal_definition(category_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_signal_definition_realtime ON t_signal_definition(is_realtime);
CREATE INDEX IF NOT EXISTS idx_signal_definition_feature ON t_signal_definition(is_feature);
CREATE INDEX IF NOT EXISTS idx_signal_definition_active ON t_signal_definition(is_active);

COMMENT ON TABLE t_signal_definition IS '信号定义表';
COMMENT ON COLUMN t_signal_definition.code IS '信号编码';
COMMENT ON COLUMN t_signal_definition.data_type IS '数据类型: float/int/bool/string/double/bigint';
COMMENT ON COLUMN t_signal_definition.is_stored IS '是否存储到时序数据库';
COMMENT ON COLUMN t_signal_definition.is_realtime IS '是否实时监控';
COMMENT ON COLUMN t_signal_definition.is_feature IS '是否用于特征工程';

-- 资产表
CREATE TABLE IF NOT EXISTS t_asset (
    id BIGSERIAL PRIMARY KEY,
    category_id BIGINT NOT NULL REFERENCES t_asset_category(id) ON DELETE RESTRICT,
    code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    attributes JSONB DEFAULT '{}',
    location VARCHAR(255),
    status VARCHAR(20) DEFAULT 'offline',
    manufacturer VARCHAR(100),
    model VARCHAR(50),
    serial_number VARCHAR(100),
    install_date DATE,
    department VARCHAR(100),
    team VARCHAR(100),
    ip_address VARCHAR(50),
    mac_address VARCHAR(50),
    is_locked BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_asset_code ON t_asset(code);
CREATE INDEX IF NOT EXISTS idx_asset_name ON t_asset(name);
CREATE INDEX IF NOT EXISTS idx_asset_category_status ON t_asset(category_id, status);
CREATE INDEX IF NOT EXISTS idx_asset_location ON t_asset(location);
CREATE INDEX IF NOT EXISTS idx_asset_status ON t_asset(status);
CREATE INDEX IF NOT EXISTS idx_asset_active ON t_asset(is_active);

COMMENT ON TABLE t_asset IS '资产表';
COMMENT ON COLUMN t_asset.code IS '资产编号';
COMMENT ON COLUMN t_asset.attributes IS '静态属性(JSONB)';
COMMENT ON COLUMN t_asset.status IS '状态: online/offline/error/maintenance';

-- =====================================================
-- 阶段2：AI引擎核心表
-- =====================================================

-- AI模型表
CREATE TABLE IF NOT EXISTS t_ai_model (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    algorithm VARCHAR(50) NOT NULL,
    target_signal VARCHAR(50) NOT NULL,
    description TEXT,
    category_id BIGINT NOT NULL REFERENCES t_asset_category(id) ON DELETE RESTRICT,
    hyperparameters JSONB DEFAULT '{}',
    feature_config JSONB DEFAULT '{}',
    training_config JSONB,
    status VARCHAR(20) DEFAULT 'draft',
    is_active BOOLEAN DEFAULT FALSE,
    created_by BIGINT,
    updated_by BIGINT,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ai_model_code ON t_ai_model(code);
CREATE INDEX IF NOT EXISTS idx_ai_model_category_status ON t_ai_model(category_id, status);
CREATE INDEX IF NOT EXISTS idx_ai_model_algorithm ON t_ai_model(algorithm);
CREATE INDEX IF NOT EXISTS idx_ai_model_active ON t_ai_model(is_active);

COMMENT ON TABLE t_ai_model IS 'AI模型表';
COMMENT ON COLUMN t_ai_model.algorithm IS '算法类型: isolation_forest/arima/xgboost/lstm';
COMMENT ON COLUMN t_ai_model.status IS '状态: draft/training/trained/deployed/archived';

-- AI模型版本表
CREATE TABLE IF NOT EXISTS t_ai_model_version (
    id BIGSERIAL PRIMARY KEY,
    model_id BIGINT NOT NULL REFERENCES t_ai_model(id) ON DELETE CASCADE,
    version VARCHAR(20) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    file_hash VARCHAR(64),
    training_start_time TIMESTAMP WITHOUT TIME ZONE,
    training_end_time TIMESTAMP WITHOUT TIME ZONE,
    training_data_range JSONB,
    training_samples BIGINT,
    metrics JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'staging',
    deployed_at TIMESTAMP WITHOUT TIME ZONE,
    deployed_by BIGINT,
    release_notes TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    UNIQUE(model_id, version)
);

CREATE INDEX IF NOT EXISTS idx_ai_model_version_model_status ON t_ai_model_version(model_id, status);
CREATE INDEX IF NOT EXISTS idx_ai_model_version_status ON t_ai_model_version(status);

COMMENT ON TABLE t_ai_model_version IS 'AI模型版本表';
COMMENT ON COLUMN t_ai_model_version.status IS '状态: staging/prod/archived';

-- AI预测结果表
CREATE TABLE IF NOT EXISTS t_ai_prediction (
    id BIGSERIAL PRIMARY KEY,
    model_version_id BIGINT NOT NULL REFERENCES t_ai_model_version(id) ON DELETE RESTRICT,
    asset_id BIGINT NOT NULL REFERENCES t_asset(id) ON DELETE CASCADE,
    input_data JSONB NOT NULL,
    predicted_value DOUBLE PRECISION NOT NULL,
    confidence DOUBLE PRECISION,
    prediction_details JSONB,
    prediction_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    target_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    actual_value DOUBLE PRECISION,
    actual_recorded_at TIMESTAMP WITHOUT TIME ZONE,
    is_anomaly BOOLEAN,
    anomaly_score DOUBLE PRECISION,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ai_prediction_asset_time ON t_ai_prediction(asset_id, prediction_time);
CREATE INDEX IF NOT EXISTS idx_ai_prediction_model_time ON t_ai_prediction(model_version_id, prediction_time);
CREATE INDEX IF NOT EXISTS idx_ai_prediction_anomaly ON t_ai_prediction(is_anomaly);

COMMENT ON TABLE t_ai_prediction IS 'AI预测结果表';

-- =====================================================
-- 阶段3：特征工程表
-- =====================================================

-- 特征定义表
CREATE TABLE IF NOT EXISTS t_feature_definition (
    id BIGSERIAL PRIMARY KEY,
    category_id BIGINT NOT NULL REFERENCES t_asset_category(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,
    description TEXT,
    calculation_config JSONB NOT NULL,
    output_type VARCHAR(20) DEFAULT 'double',
    output_unit VARCHAR(20),
    stream_name VARCHAR(100),
    target_table VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    UNIQUE(category_id, code)
);

CREATE INDEX IF NOT EXISTS idx_feature_definition_category_active ON t_feature_definition(category_id, is_active);

COMMENT ON TABLE t_feature_definition IS '特征定义表';
COMMENT ON COLUMN t_feature_definition.calculation_config IS '计算配置(JSON DSL)';

-- 特征视图表
CREATE TABLE IF NOT EXISTS t_feature_view (
    id BIGSERIAL PRIMARY KEY,
    category_id BIGINT NOT NULL REFERENCES t_asset_category(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,
    description TEXT,
    feature_codes JSONB NOT NULL,
    stream_name VARCHAR(100),
    target_stable VARCHAR(100),
    status VARCHAR(20) DEFAULT 'draft',
    is_active BOOLEAN DEFAULT TRUE,
    last_quality_check TIMESTAMP WITHOUT TIME ZONE,
    quality_score DOUBLE PRECISION,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    UNIQUE(category_id, code)
);

CREATE INDEX IF NOT EXISTS idx_feature_view_category_status ON t_feature_view(category_id, status);

COMMENT ON TABLE t_feature_view IS '特征视图表';
COMMENT ON COLUMN t_feature_view.status IS '状态: draft/active/paused/archived';

-- =====================================================
-- 阶段4：Schema版本控制表
-- =====================================================

CREATE TABLE IF NOT EXISTS t_schema_version (
    id BIGSERIAL PRIMARY KEY,
    category_id BIGINT NOT NULL REFERENCES t_asset_category(id) ON DELETE CASCADE,
    version VARCHAR(20) NOT NULL,
    change_type VARCHAR(20) NOT NULL,
    change_details JSONB NOT NULL,
    executed_sql TEXT,
    execution_status VARCHAR(20) NOT NULL,
    execution_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    execution_duration_ms INTEGER,
    error_message TEXT,
    executed_by BIGINT,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_schema_version_category ON t_schema_version(category_id, version);
CREATE INDEX IF NOT EXISTS idx_schema_version_status ON t_schema_version(execution_status);
CREATE INDEX IF NOT EXISTS idx_schema_version_time ON t_schema_version(execution_time);

COMMENT ON TABLE t_schema_version IS 'Schema版本控制表';
COMMENT ON COLUMN t_schema_version.change_type IS '变更类型: create/add_column/modify/drop';
COMMENT ON COLUMN t_schema_version.execution_status IS '执行状态: success/failed/rolled_back';

-- =====================================================
-- 阶段5：数据迁移跟踪表
-- =====================================================

CREATE TABLE IF NOT EXISTS t_migration_record (
    id BIGSERIAL PRIMARY KEY,
    migration_name VARCHAR(100) NOT NULL,
    migration_type VARCHAR(50) NOT NULL,
    source_table VARCHAR(100) NOT NULL,
    target_table VARCHAR(100) NOT NULL,
    total_records BIGINT DEFAULT 0,
    migrated_records BIGINT DEFAULT 0,
    failed_records BIGINT DEFAULT 0,
    skipped_records BIGINT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    started_at TIMESTAMP WITHOUT TIME ZONE,
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    error_details JSONB,
    executed_by BIGINT,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_migration_record_status ON t_migration_record(status);
CREATE INDEX IF NOT EXISTS idx_migration_record_type ON t_migration_record(migration_type);
CREATE INDEX IF NOT EXISTS idx_migration_record_started ON t_migration_record(started_at);

COMMENT ON TABLE t_migration_record IS '数据迁移记录表';
COMMENT ON COLUMN t_migration_record.status IS '状态: pending/running/completed/failed/rolled_back';
