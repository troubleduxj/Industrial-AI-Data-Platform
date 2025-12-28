-- =====================================================
-- 工业AI数据平台 V2 升级 - 整合迁移脚本
-- 版本: V2.0
-- 创建时间: 2024-12-27
-- 描述: 整合所有V2升级相关的数据库迁移脚本
-- =====================================================

-- 本脚本整合以下迁移:
-- 001_create_platform_tables.sql - 平台核心表
-- 002_add_platform_menus.sql - 平台菜单
-- 003_create_decision_engine_tables.sql - 决策引擎表
-- 004_create_ingestion_tables.sql - 数据采集层表
-- 004_create_prediction_tables.sql - 预测结果表 (TDengine)
-- 005_create_identity_tables.sql - 身份集成表

-- =====================================================
-- 迁移版本跟踪表
-- =====================================================

CREATE TABLE IF NOT EXISTS t_migration_versions (
    id BIGSERIAL PRIMARY KEY,
    version VARCHAR(20) NOT NULL UNIQUE,
    description TEXT,
    script_name VARCHAR(100) NOT NULL,
    executed_at TIMESTAMP DEFAULT NOW(),
    execution_status VARCHAR(20) DEFAULT 'success',
    execution_duration_ms INT,
    rollback_script TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_migration_versions_version ON t_migration_versions(version);
CREATE INDEX IF NOT EXISTS idx_migration_versions_status ON t_migration_versions(execution_status);

COMMENT ON TABLE t_migration_versions IS '迁移版本跟踪表';
COMMENT ON COLUMN t_migration_versions.version IS '迁移版本号';
COMMENT ON COLUMN t_migration_versions.script_name IS '脚本文件名';
COMMENT ON COLUMN t_migration_versions.execution_status IS '执行状态: success/failed/rolled_back';
COMMENT ON COLUMN t_migration_versions.rollback_script IS '回滚脚本';


-- =====================================================
-- 阶段1：平台核心表 (001)
-- =====================================================

-- 检查是否已执行过此迁移
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM t_migration_versions WHERE version = '001') THEN
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
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_asset_category_code ON t_asset_category(code);
        CREATE INDEX IF NOT EXISTS idx_asset_category_active_industry ON t_asset_category(is_active, industry);

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
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            UNIQUE(category_id, code)
        );

        CREATE INDEX IF NOT EXISTS idx_signal_definition_category ON t_signal_definition(category_id, sort_order);
        CREATE INDEX IF NOT EXISTS idx_signal_definition_realtime ON t_signal_definition(is_realtime);
        CREATE INDEX IF NOT EXISTS idx_signal_definition_feature ON t_signal_definition(is_feature);
        CREATE INDEX IF NOT EXISTS idx_signal_definition_active ON t_signal_definition(is_active);

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
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_asset_code ON t_asset(code);
        CREATE INDEX IF NOT EXISTS idx_asset_name ON t_asset(name);
        CREATE INDEX IF NOT EXISTS idx_asset_category_status ON t_asset(category_id, status);
        CREATE INDEX IF NOT EXISTS idx_asset_location ON t_asset(location);
        CREATE INDEX IF NOT EXISTS idx_asset_status ON t_asset(status);
        CREATE INDEX IF NOT EXISTS idx_asset_active ON t_asset(is_active);

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
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_ai_model_code ON t_ai_model(code);
        CREATE INDEX IF NOT EXISTS idx_ai_model_category_status ON t_ai_model(category_id, status);
        CREATE INDEX IF NOT EXISTS idx_ai_model_algorithm ON t_ai_model(algorithm);
        CREATE INDEX IF NOT EXISTS idx_ai_model_active ON t_ai_model(is_active);

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
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            UNIQUE(model_id, version)
        );

        CREATE INDEX IF NOT EXISTS idx_ai_model_version_model_status ON t_ai_model_version(model_id, status);
        CREATE INDEX IF NOT EXISTS idx_ai_model_version_status ON t_ai_model_version(status);

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
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_ai_prediction_asset_time ON t_ai_prediction(asset_id, prediction_time);
        CREATE INDEX IF NOT EXISTS idx_ai_prediction_model_time ON t_ai_prediction(model_version_id, prediction_time);
        CREATE INDEX IF NOT EXISTS idx_ai_prediction_anomaly ON t_ai_prediction(is_anomaly);

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
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            UNIQUE(category_id, code)
        );

        CREATE INDEX IF NOT EXISTS idx_feature_definition_category_active ON t_feature_definition(category_id, is_active);

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
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            UNIQUE(category_id, code)
        );

        CREATE INDEX IF NOT EXISTS idx_feature_view_category_status ON t_feature_view(category_id, status);

        -- Schema版本控制表
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
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_schema_version_category ON t_schema_version(category_id, version);
        CREATE INDEX IF NOT EXISTS idx_schema_version_status ON t_schema_version(execution_status);
        CREATE INDEX IF NOT EXISTS idx_schema_version_time ON t_schema_version(execution_time);

        -- 数据迁移跟踪表
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
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_migration_record_status ON t_migration_record(status);
        CREATE INDEX IF NOT EXISTS idx_migration_record_type ON t_migration_record(migration_type);
        CREATE INDEX IF NOT EXISTS idx_migration_record_started ON t_migration_record(started_at);

        -- 记录迁移版本
        INSERT INTO t_migration_versions (version, description, script_name)
        VALUES ('001', '平台核心表创建', '001_create_platform_tables.sql');
        
        RAISE NOTICE '✅ 迁移 001 执行完成: 平台核心表';
    ELSE
        RAISE NOTICE '⏭️ 迁移 001 已执行，跳过';
    END IF;
END $$;



-- =====================================================
-- 阶段2：决策引擎表 (003)
-- =====================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM t_migration_versions WHERE version = '003') THEN
        -- 决策规则表
        CREATE TABLE IF NOT EXISTS t_decision_rules (
            id BIGSERIAL PRIMARY KEY,
            rule_id VARCHAR(64) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            category_id BIGINT REFERENCES t_asset_category(id) ON DELETE SET NULL,
            model_id BIGINT REFERENCES t_ai_model(id) ON DELETE SET NULL,
            conditions JSONB NOT NULL,
            actions JSONB NOT NULL,
            priority INT DEFAULT 0,
            enabled BOOLEAN DEFAULT TRUE,
            cooldown_seconds INT DEFAULT 0,
            created_by BIGINT,
            updated_by BIGINT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_decision_rules_enabled_priority ON t_decision_rules(enabled, priority);
        CREATE INDEX IF NOT EXISTS idx_decision_rules_category ON t_decision_rules(category_id);
        CREATE INDEX IF NOT EXISTS idx_decision_rules_model ON t_decision_rules(model_id);
        CREATE INDEX IF NOT EXISTS idx_decision_rules_rule_id ON t_decision_rules(rule_id);

        -- 决策审计日志表
        CREATE TABLE IF NOT EXISTS t_decision_audit_logs (
            id BIGSERIAL PRIMARY KEY,
            rule_id VARCHAR(64) NOT NULL,
            rule_name VARCHAR(100),
            asset_id BIGINT REFERENCES t_asset(id) ON DELETE SET NULL,
            prediction_id BIGINT REFERENCES t_ai_prediction(id) ON DELETE SET NULL,
            trigger_time TIMESTAMP NOT NULL,
            trigger_data JSONB,
            conditions_snapshot JSONB,
            actions_executed JSONB,
            result VARCHAR(20) DEFAULT 'success',
            error_message TEXT,
            execution_duration_ms INT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_decision_audit_rule_time ON t_decision_audit_logs(rule_id, trigger_time);
        CREATE INDEX IF NOT EXISTS idx_decision_audit_time ON t_decision_audit_logs(trigger_time);
        CREATE INDEX IF NOT EXISTS idx_decision_audit_result ON t_decision_audit_logs(result);
        CREATE INDEX IF NOT EXISTS idx_decision_audit_asset ON t_decision_audit_logs(asset_id);

        -- 记录迁移版本
        INSERT INTO t_migration_versions (version, description, script_name)
        VALUES ('003', '决策引擎表创建', '003_create_decision_engine_tables.sql');
        
        RAISE NOTICE '✅ 迁移 003 执行完成: 决策引擎表';
    ELSE
        RAISE NOTICE '⏭️ 迁移 003 已执行，跳过';
    END IF;
END $$;


-- =====================================================
-- 阶段3：数据采集层表 (004a)
-- =====================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM t_migration_versions WHERE version = '004a') THEN
        -- 数据源配置表
        CREATE TABLE IF NOT EXISTS t_data_sources (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            protocol VARCHAR(20) NOT NULL,
            config JSONB NOT NULL,
            category_id BIGINT REFERENCES t_asset_category(id) ON DELETE SET NULL,
            enabled BOOLEAN DEFAULT TRUE,
            status VARCHAR(20) DEFAULT 'stopped',
            last_connected_at TIMESTAMP,
            last_disconnected_at TIMESTAMP,
            error_count INT DEFAULT 0,
            success_count BIGINT DEFAULT 0,
            total_bytes_received BIGINT DEFAULT 0,
            retry_config JSONB DEFAULT '{"max_attempts": 3, "initial_delay": 1.0, "strategy": "exponential_jitter"}',
            validation_enabled BOOLEAN DEFAULT TRUE,
            transform_config JSONB,
            created_by BIGINT,
            updated_by BIGINT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_data_sources_protocol ON t_data_sources(protocol);
        CREATE INDEX IF NOT EXISTS idx_data_sources_enabled ON t_data_sources(enabled);
        CREATE INDEX IF NOT EXISTS idx_data_sources_status ON t_data_sources(status);
        CREATE INDEX IF NOT EXISTS idx_data_sources_category ON t_data_sources(category_id);

        -- 双写配置表
        CREATE TABLE IF NOT EXISTS t_dual_write_config (
            id BIGSERIAL PRIMARY KEY,
            category_id BIGINT REFERENCES t_asset_category(id) ON DELETE CASCADE,
            enabled BOOLEAN DEFAULT FALSE,
            write_to_new BOOLEAN DEFAULT TRUE,
            write_to_old BOOLEAN DEFAULT TRUE,
            fail_on_old_error BOOLEAN DEFAULT FALSE,
            verify_enabled BOOLEAN DEFAULT FALSE,
            verify_interval_hours INT DEFAULT 24,
            last_verify_time TIMESTAMP,
            last_verify_result JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(category_id)
        );

        CREATE INDEX IF NOT EXISTS idx_dual_write_config_enabled ON t_dual_write_config(enabled);
        CREATE INDEX IF NOT EXISTS idx_dual_write_config_category ON t_dual_write_config(category_id);

        -- 数据源错误日志表
        CREATE TABLE IF NOT EXISTS t_ingestion_error_logs (
            id BIGSERIAL PRIMARY KEY,
            source_id BIGINT REFERENCES t_data_sources(id) ON DELETE CASCADE,
            source_name VARCHAR(100),
            error_type VARCHAR(100) NOT NULL,
            error_message TEXT NOT NULL,
            error_stack TEXT,
            context JSONB,
            attempt INT DEFAULT 0,
            resolved BOOLEAN DEFAULT FALSE,
            resolved_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_ingestion_error_logs_source ON t_ingestion_error_logs(source_id);
        CREATE INDEX IF NOT EXISTS idx_ingestion_error_logs_type ON t_ingestion_error_logs(error_type);
        CREATE INDEX IF NOT EXISTS idx_ingestion_error_logs_time ON t_ingestion_error_logs(created_at);
        CREATE INDEX IF NOT EXISTS idx_ingestion_error_logs_resolved ON t_ingestion_error_logs(resolved);

        -- 数据源统计表
        CREATE TABLE IF NOT EXISTS t_ingestion_statistics (
            id BIGSERIAL PRIMARY KEY,
            source_id BIGINT REFERENCES t_data_sources(id) ON DELETE CASCADE,
            period_start TIMESTAMP NOT NULL,
            period_end TIMESTAMP NOT NULL,
            period_type VARCHAR(20) NOT NULL,
            data_points_count BIGINT DEFAULT 0,
            bytes_received BIGINT DEFAULT 0,
            error_count INT DEFAULT 0,
            success_rate FLOAT DEFAULT 0,
            avg_latency_ms FLOAT DEFAULT 0,
            max_latency_ms FLOAT DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_ingestion_statistics_source ON t_ingestion_statistics(source_id);
        CREATE INDEX IF NOT EXISTS idx_ingestion_statistics_period ON t_ingestion_statistics(period_start, period_end);
        CREATE INDEX IF NOT EXISTS idx_ingestion_statistics_type ON t_ingestion_statistics(period_type);

        -- 协议适配器配置模板表
        CREATE TABLE IF NOT EXISTS t_adapter_templates (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            protocol VARCHAR(20) NOT NULL,
            description TEXT,
            config_template JSONB NOT NULL,
            config_schema JSONB,
            is_builtin BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_adapter_templates_protocol ON t_adapter_templates(protocol);
        CREATE INDEX IF NOT EXISTS idx_adapter_templates_active ON t_adapter_templates(is_active);

        -- 插入内置适配器模板
        INSERT INTO t_adapter_templates (name, protocol, description, config_template, config_schema, is_builtin)
        VALUES 
        (
            'MQTT默认模板',
            'mqtt',
            'MQTT协议默认配置模板',
            '{"host": "localhost", "port": 1883, "username": "", "password": "", "topics": ["#"], "client_id": "", "qos": 1, "keepalive": 60, "clean_session": true, "reconnect_interval": 5, "max_reconnect_attempts": 10}',
            '{"type": "object", "required": ["host", "port", "topics"], "properties": {"host": {"type": "string", "title": "主机地址"}, "port": {"type": "integer", "title": "端口", "default": 1883}, "username": {"type": "string", "title": "用户名"}, "password": {"type": "string", "title": "密码", "format": "password"}, "topics": {"type": "array", "title": "订阅主题", "items": {"type": "string"}}, "client_id": {"type": "string", "title": "客户端ID"}, "qos": {"type": "integer", "title": "QoS级别", "enum": [0, 1, 2], "default": 1}, "keepalive": {"type": "integer", "title": "心跳间隔(秒)", "default": 60}}}',
            true
        ),
        (
            'HTTP轮询默认模板',
            'http',
            'HTTP轮询协议默认配置模板',
            '{"url": "", "method": "GET", "headers": {}, "params": {}, "body": null, "poll_interval": 5, "timeout": 30, "retry_count": 3, "retry_delay": 1, "verify_ssl": true, "auth": null, "response_format": "json", "data_path": ""}',
            '{"type": "object", "required": ["url"], "properties": {"url": {"type": "string", "title": "请求URL", "format": "uri"}, "method": {"type": "string", "title": "请求方法", "enum": ["GET", "POST", "PUT"], "default": "GET"}, "headers": {"type": "object", "title": "请求头"}, "poll_interval": {"type": "integer", "title": "轮询间隔(秒)", "default": 5}, "timeout": {"type": "integer", "title": "超时时间(秒)", "default": 30}, "data_path": {"type": "string", "title": "数据路径", "description": "响应中数据的JSON路径，如 data.items"}}}',
            true
        )
        ON CONFLICT DO NOTHING;

        -- 更新触发器
        CREATE OR REPLACE FUNCTION update_data_sources_updated_at()
        RETURNS TRIGGER AS $func$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $func$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS trigger_data_sources_updated_at ON t_data_sources;
        CREATE TRIGGER trigger_data_sources_updated_at
            BEFORE UPDATE ON t_data_sources
            FOR EACH ROW
            EXECUTE FUNCTION update_data_sources_updated_at();

        CREATE OR REPLACE FUNCTION update_dual_write_config_updated_at()
        RETURNS TRIGGER AS $func$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $func$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS trigger_dual_write_config_updated_at ON t_dual_write_config;
        CREATE TRIGGER trigger_dual_write_config_updated_at
            BEFORE UPDATE ON t_dual_write_config
            FOR EACH ROW
            EXECUTE FUNCTION update_dual_write_config_updated_at();

        -- 记录迁移版本
        INSERT INTO t_migration_versions (version, description, script_name)
        VALUES ('004a', '数据采集层表创建', '004_create_ingestion_tables.sql');
        
        RAISE NOTICE '✅ 迁移 004a 执行完成: 数据采集层表';
    ELSE
        RAISE NOTICE '⏭️ 迁移 004a 已执行，跳过';
    END IF;
END $$;


-- =====================================================
-- 阶段4：身份集成表 (005)
-- =====================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM t_migration_versions WHERE version = '005') THEN
        -- 身份提供商配置表
        CREATE TABLE IF NOT EXISTS t_identity_providers (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL,
            type VARCHAR(20) NOT NULL,
            config JSONB NOT NULL DEFAULT '{}',
            enabled BOOLEAN DEFAULT TRUE,
            priority INT DEFAULT 0,
            role_mapping JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_identity_providers_enabled ON t_identity_providers(enabled);
        CREATE INDEX IF NOT EXISTS idx_identity_providers_type ON t_identity_providers(type);
        CREATE INDEX IF NOT EXISTS idx_identity_providers_priority ON t_identity_providers(enabled, priority);

        -- 用户外部身份关联表
        CREATE TABLE IF NOT EXISTS t_user_external_identities (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            provider_id BIGINT NOT NULL REFERENCES t_identity_providers(id) ON DELETE CASCADE,
            external_id VARCHAR(255) NOT NULL,
            external_username VARCHAR(100),
            last_login_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(provider_id, external_id)
        );

        CREATE INDEX IF NOT EXISTS idx_user_external_identities_user ON t_user_external_identities(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_external_identities_provider ON t_user_external_identities(provider_id);
        CREATE INDEX IF NOT EXISTS idx_user_external_identities_external ON t_user_external_identities(external_id);

        -- 更新时间戳触发器
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $func$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $func$ language 'plpgsql';

        DROP TRIGGER IF EXISTS update_identity_providers_updated_at ON t_identity_providers;
        CREATE TRIGGER update_identity_providers_updated_at
            BEFORE UPDATE ON t_identity_providers
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();

        DROP TRIGGER IF EXISTS update_user_external_identities_updated_at ON t_user_external_identities;
        CREATE TRIGGER update_user_external_identities_updated_at
            BEFORE UPDATE ON t_user_external_identities
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();

        -- 记录迁移版本
        INSERT INTO t_migration_versions (version, description, script_name)
        VALUES ('005', '身份集成表创建', '005_create_identity_tables.sql');
        
        RAISE NOTICE '✅ 迁移 005 执行完成: 身份集成表';
    ELSE
        RAISE NOTICE '⏭️ 迁移 005 已执行，跳过';
    END IF;
END $$;


-- =====================================================
-- 完成标记
-- =====================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM t_migration_versions WHERE version = 'V2.0') THEN
        INSERT INTO t_migration_versions (version, description, script_name)
        VALUES ('V2.0', '工业AI数据平台V2升级完成', 'v2_consolidated_migration.sql');
        
        RAISE NOTICE '✅ V2 整合迁移全部完成';
    ELSE
        RAISE NOTICE '⏭️ V2 整合迁移已执行';
    END IF;
END $$;

-- 显示迁移状态
SELECT version, description, script_name, executed_at, execution_status 
FROM t_migration_versions 
ORDER BY executed_at;
