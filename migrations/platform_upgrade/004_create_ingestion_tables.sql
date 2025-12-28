-- =====================================================
-- 数据采集层数据库表
-- 工业AI数据平台 V2 升级
-- 
-- 需求: 5.1 - 数据源配置和管理
-- =====================================================

-- 数据源配置表
-- 存储各种协议的数据源配置信息
CREATE TABLE IF NOT EXISTS t_data_sources (
    id BIGSERIAL PRIMARY KEY,
    
    -- 基础信息
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- 协议配置
    protocol VARCHAR(20) NOT NULL,  -- mqtt, http, modbus, opcua
    config JSONB NOT NULL,          -- 协议特定配置
    
    -- 关联资产类别（可选）
    category_id BIGINT REFERENCES t_asset_category(id) ON DELETE SET NULL,
    
    -- 状态管理
    enabled BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) DEFAULT 'stopped',  -- stopped, starting, running, stopping, error, reconnecting
    
    -- 统计信息
    last_connected_at TIMESTAMP,
    last_disconnected_at TIMESTAMP,
    error_count INT DEFAULT 0,
    success_count BIGINT DEFAULT 0,
    total_bytes_received BIGINT DEFAULT 0,
    
    -- 重试配置
    retry_config JSONB DEFAULT '{"max_attempts": 3, "initial_delay": 1.0, "strategy": "exponential_jitter"}',
    
    -- 数据处理配置
    validation_enabled BOOLEAN DEFAULT TRUE,
    transform_config JSONB,  -- 数据转换配置
    
    -- 审计字段
    created_by BIGINT,
    updated_by BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_data_sources_protocol ON t_data_sources(protocol);
CREATE INDEX IF NOT EXISTS idx_data_sources_enabled ON t_data_sources(enabled);
CREATE INDEX IF NOT EXISTS idx_data_sources_status ON t_data_sources(status);
CREATE INDEX IF NOT EXISTS idx_data_sources_category ON t_data_sources(category_id);

-- 添加注释
COMMENT ON TABLE t_data_sources IS '数据源配置表';
COMMENT ON COLUMN t_data_sources.protocol IS '协议类型: mqtt, http, modbus, opcua';
COMMENT ON COLUMN t_data_sources.config IS '协议特定配置，JSON格式';
COMMENT ON COLUMN t_data_sources.status IS '运行状态: stopped, starting, running, stopping, error, reconnecting';


-- =====================================================
-- 双写配置表
-- 管理新旧数据结构的双写模式
-- =====================================================

CREATE TABLE IF NOT EXISTS t_dual_write_config (
    id BIGSERIAL PRIMARY KEY,
    
    -- 关联资产类别（NULL表示全局配置）
    category_id BIGINT REFERENCES t_asset_category(id) ON DELETE CASCADE,
    
    -- 配置
    enabled BOOLEAN DEFAULT FALSE,
    
    -- 写入目标配置
    write_to_new BOOLEAN DEFAULT TRUE,   -- 写入新结构
    write_to_old BOOLEAN DEFAULT TRUE,   -- 写入旧结构
    
    -- 错误处理
    fail_on_old_error BOOLEAN DEFAULT FALSE,  -- 旧结构写入失败是否影响主流程
    
    -- 一致性验证配置
    verify_enabled BOOLEAN DEFAULT FALSE,
    verify_interval_hours INT DEFAULT 24,
    last_verify_time TIMESTAMP,
    last_verify_result JSONB,
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- 唯一约束：每个类别只能有一条配置
    UNIQUE(category_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_dual_write_config_enabled ON t_dual_write_config(enabled);
CREATE INDEX IF NOT EXISTS idx_dual_write_config_category ON t_dual_write_config(category_id);

-- 添加注释
COMMENT ON TABLE t_dual_write_config IS '双写配置表';
COMMENT ON COLUMN t_dual_write_config.category_id IS '资产类别ID，NULL表示全局配置';
COMMENT ON COLUMN t_dual_write_config.fail_on_old_error IS '旧结构写入失败是否影响主流程';


-- =====================================================
-- 数据源错误日志表
-- 记录数据采集过程中的错误
-- =====================================================

CREATE TABLE IF NOT EXISTS t_ingestion_error_logs (
    id BIGSERIAL PRIMARY KEY,
    
    -- 关联数据源
    source_id BIGINT REFERENCES t_data_sources(id) ON DELETE CASCADE,
    source_name VARCHAR(100),
    
    -- 错误信息
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    error_stack TEXT,
    
    -- 上下文
    context JSONB,
    
    -- 重试信息
    attempt INT DEFAULT 0,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    
    -- 时间
    created_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_ingestion_error_logs_source ON t_ingestion_error_logs(source_id);
CREATE INDEX IF NOT EXISTS idx_ingestion_error_logs_type ON t_ingestion_error_logs(error_type);
CREATE INDEX IF NOT EXISTS idx_ingestion_error_logs_time ON t_ingestion_error_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_ingestion_error_logs_resolved ON t_ingestion_error_logs(resolved);

-- 添加注释
COMMENT ON TABLE t_ingestion_error_logs IS '数据采集错误日志表';


-- =====================================================
-- 数据源统计表
-- 存储数据源的历史统计信息
-- =====================================================

CREATE TABLE IF NOT EXISTS t_ingestion_statistics (
    id BIGSERIAL PRIMARY KEY,
    
    -- 关联数据源
    source_id BIGINT REFERENCES t_data_sources(id) ON DELETE CASCADE,
    
    -- 统计时间段
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    period_type VARCHAR(20) NOT NULL,  -- minute, hour, day
    
    -- 统计数据
    data_points_count BIGINT DEFAULT 0,
    bytes_received BIGINT DEFAULT 0,
    error_count INT DEFAULT 0,
    success_rate FLOAT DEFAULT 0,
    avg_latency_ms FLOAT DEFAULT 0,
    max_latency_ms FLOAT DEFAULT 0,
    
    -- 时间
    created_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_ingestion_statistics_source ON t_ingestion_statistics(source_id);
CREATE INDEX IF NOT EXISTS idx_ingestion_statistics_period ON t_ingestion_statistics(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_ingestion_statistics_type ON t_ingestion_statistics(period_type);

-- 添加注释
COMMENT ON TABLE t_ingestion_statistics IS '数据采集统计表';
COMMENT ON COLUMN t_ingestion_statistics.period_type IS '统计周期类型: minute, hour, day';


-- =====================================================
-- 协议适配器配置模板表
-- 存储各协议的默认配置模板
-- =====================================================

CREATE TABLE IF NOT EXISTS t_adapter_templates (
    id BIGSERIAL PRIMARY KEY,
    
    -- 基础信息
    name VARCHAR(100) NOT NULL,
    protocol VARCHAR(20) NOT NULL,
    description TEXT,
    
    -- 配置模板
    config_template JSONB NOT NULL,
    
    -- 配置Schema（用于前端表单生成）
    config_schema JSONB,
    
    -- 状态
    is_builtin BOOLEAN DEFAULT FALSE,  -- 是否内置模板
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_adapter_templates_protocol ON t_adapter_templates(protocol);
CREATE INDEX IF NOT EXISTS idx_adapter_templates_active ON t_adapter_templates(is_active);

-- 添加注释
COMMENT ON TABLE t_adapter_templates IS '协议适配器配置模板表';


-- =====================================================
-- 插入内置适配器模板
-- =====================================================

INSERT INTO t_adapter_templates (name, protocol, description, config_template, config_schema, is_builtin)
VALUES 
(
    'MQTT默认模板',
    'mqtt',
    'MQTT协议默认配置模板',
    '{
        "host": "localhost",
        "port": 1883,
        "username": "",
        "password": "",
        "topics": ["#"],
        "client_id": "",
        "qos": 1,
        "keepalive": 60,
        "clean_session": true,
        "reconnect_interval": 5,
        "max_reconnect_attempts": 10
    }',
    '{
        "type": "object",
        "required": ["host", "port", "topics"],
        "properties": {
            "host": {"type": "string", "title": "主机地址"},
            "port": {"type": "integer", "title": "端口", "default": 1883},
            "username": {"type": "string", "title": "用户名"},
            "password": {"type": "string", "title": "密码", "format": "password"},
            "topics": {"type": "array", "title": "订阅主题", "items": {"type": "string"}},
            "client_id": {"type": "string", "title": "客户端ID"},
            "qos": {"type": "integer", "title": "QoS级别", "enum": [0, 1, 2], "default": 1},
            "keepalive": {"type": "integer", "title": "心跳间隔(秒)", "default": 60}
        }
    }',
    true
),
(
    'HTTP轮询默认模板',
    'http',
    'HTTP轮询协议默认配置模板',
    '{
        "url": "",
        "method": "GET",
        "headers": {},
        "params": {},
        "body": null,
        "poll_interval": 5,
        "timeout": 30,
        "retry_count": 3,
        "retry_delay": 1,
        "verify_ssl": true,
        "auth": null,
        "response_format": "json",
        "data_path": ""
    }',
    '{
        "type": "object",
        "required": ["url"],
        "properties": {
            "url": {"type": "string", "title": "请求URL", "format": "uri"},
            "method": {"type": "string", "title": "请求方法", "enum": ["GET", "POST", "PUT"], "default": "GET"},
            "headers": {"type": "object", "title": "请求头"},
            "poll_interval": {"type": "integer", "title": "轮询间隔(秒)", "default": 5},
            "timeout": {"type": "integer", "title": "超时时间(秒)", "default": 30},
            "data_path": {"type": "string", "title": "数据路径", "description": "响应中数据的JSON路径，如 data.items"}
        }
    }',
    true
)
ON CONFLICT DO NOTHING;


-- =====================================================
-- 更新触发器
-- =====================================================

-- 数据源更新时间触发器
CREATE OR REPLACE FUNCTION update_data_sources_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_data_sources_updated_at ON t_data_sources;
CREATE TRIGGER trigger_data_sources_updated_at
    BEFORE UPDATE ON t_data_sources
    FOR EACH ROW
    EXECUTE FUNCTION update_data_sources_updated_at();

-- 双写配置更新时间触发器
CREATE OR REPLACE FUNCTION update_dual_write_config_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_dual_write_config_updated_at ON t_dual_write_config;
CREATE TRIGGER trigger_dual_write_config_updated_at
    BEFORE UPDATE ON t_dual_write_config
    FOR EACH ROW
    EXECUTE FUNCTION update_dual_write_config_updated_at();
