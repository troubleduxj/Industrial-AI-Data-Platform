-- ========================================
-- 设备参数报警监测系统 - 数据库表创建
-- ========================================
-- 版本: v1.0
-- 创建时间: 2025-11-25
-- ========================================

BEGIN;

-- =====================================================
-- 1. 报警规则表 (t_alarm_rule)
-- =====================================================

CREATE TABLE IF NOT EXISTS t_alarm_rule (
    id BIGSERIAL PRIMARY KEY,
    
    -- 基本信息
    rule_name VARCHAR(100) NOT NULL,
    rule_code VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    
    -- 关联信息
    device_type_code VARCHAR(50) NOT NULL,
    device_field_id BIGINT,
    field_code VARCHAR(50) NOT NULL,
    field_name VARCHAR(100),
    
    -- 阈值配置 (JSONB)
    threshold_config JSONB NOT NULL DEFAULT '{}',
    
    -- 触发条件 (JSONB)
    trigger_condition JSONB DEFAULT '{"consecutive_count": 1}',
    
    -- 报警级别
    alarm_level VARCHAR(20) DEFAULT 'warning',
    
    -- 通知配置 (JSONB)
    notification_config JSONB DEFAULT '{"channels": ["websocket"]}',
    
    -- 状态
    is_enabled BOOLEAN DEFAULT TRUE,
    priority INT DEFAULT 0,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by BIGINT,
    updated_by BIGINT
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_alarm_rule_device_type ON t_alarm_rule(device_type_code);
CREATE INDEX IF NOT EXISTS idx_alarm_rule_field ON t_alarm_rule(field_code);
CREATE INDEX IF NOT EXISTS idx_alarm_rule_enabled ON t_alarm_rule(is_enabled);

COMMENT ON TABLE t_alarm_rule IS '报警规则配置表';
COMMENT ON COLUMN t_alarm_rule.rule_name IS '规则名称';
COMMENT ON COLUMN t_alarm_rule.rule_code IS '规则代码（唯一）';
COMMENT ON COLUMN t_alarm_rule.device_type_code IS '设备类型代码';
COMMENT ON COLUMN t_alarm_rule.field_code IS '监测字段代码';
COMMENT ON COLUMN t_alarm_rule.threshold_config IS '阈值配置JSON';
COMMENT ON COLUMN t_alarm_rule.trigger_condition IS '触发条件JSON';
COMMENT ON COLUMN t_alarm_rule.alarm_level IS '默认报警级别: info/warning/critical/emergency';

-- =====================================================
-- 2. 报警记录表 (t_alarm_record)
-- =====================================================

CREATE TABLE IF NOT EXISTS t_alarm_record (
    id BIGSERIAL PRIMARY KEY,
    
    -- 关联信息
    rule_id BIGINT REFERENCES t_alarm_rule(id) ON DELETE SET NULL,
    device_id BIGINT,
    device_code VARCHAR(64) NOT NULL,
    device_name VARCHAR(100),
    device_type_code VARCHAR(50),
    
    -- 报警信息
    alarm_code VARCHAR(50) NOT NULL,
    alarm_level VARCHAR(20) NOT NULL,
    alarm_title VARCHAR(200) NOT NULL,
    alarm_content TEXT,
    
    -- 触发数据
    field_code VARCHAR(50),
    field_name VARCHAR(100),
    trigger_value DECIMAL(20,6),
    threshold_value JSONB,
    
    -- 时间信息
    triggered_at TIMESTAMP NOT NULL,
    recovered_at TIMESTAMP,
    duration_seconds INT,
    
    -- 处理信息
    status VARCHAR(20) DEFAULT 'active',
    acknowledged_at TIMESTAMP,
    acknowledged_by BIGINT,
    acknowledged_by_name VARCHAR(50),
    resolved_at TIMESTAMP,
    resolved_by BIGINT,
    resolved_by_name VARCHAR(50),
    resolution_notes TEXT,
    
    -- 通知状态
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_channels JSONB,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_alarm_record_device ON t_alarm_record(device_code);
CREATE INDEX IF NOT EXISTS idx_alarm_record_rule ON t_alarm_record(rule_id);
CREATE INDEX IF NOT EXISTS idx_alarm_record_status ON t_alarm_record(status);
CREATE INDEX IF NOT EXISTS idx_alarm_record_level ON t_alarm_record(alarm_level);
CREATE INDEX IF NOT EXISTS idx_alarm_record_time ON t_alarm_record(triggered_at);
CREATE INDEX IF NOT EXISTS idx_alarm_record_device_time ON t_alarm_record(device_code, triggered_at);

COMMENT ON TABLE t_alarm_record IS '报警记录表';
COMMENT ON COLUMN t_alarm_record.status IS '状态: active/acknowledged/resolved/closed';
COMMENT ON COLUMN t_alarm_record.alarm_level IS '报警级别: info/warning/critical/emergency';

COMMIT;

-- =====================================================
-- 3. 插入示例报警规则
-- =====================================================

INSERT INTO t_alarm_rule (rule_name, rule_code, description, device_type_code, field_code, field_name, threshold_config, trigger_condition, alarm_level, is_enabled)
VALUES 
-- 焊机温度监测
('焊机温度过高报警', 'WELD_TEMP_HIGH', '监测焊机温度，超过阈值时报警', 'welding', 'temperature', '温度', 
 '{"type": "upper", "warning": {"max": 60}, "critical": {"max": 75}, "emergency": {"max": 85}}',
 '{"consecutive_count": 3, "duration_seconds": 30}',
 'warning', true),

-- 焊机电流监测
('焊接电流异常报警', 'WELD_CURRENT_ABNORMAL', '监测焊接电流，超出正常范围时报警', 'welding', 'welding_current', '焊接电流',
 '{"type": "range", "warning": {"min": 50, "max": 300}, "critical": {"min": 30, "max": 350}}',
 '{"consecutive_count": 2}',
 'warning', true),

-- 压力传感器监测
('压力超限报警', 'PRESSURE_LIMIT', '监测压力传感器数值，超出安全范围时报警', 'pressure_sensor', 'pressure', '压力值',
 '{"type": "range", "warning": {"min": 0.5, "max": 4.5}, "critical": {"min": 0.2, "max": 4.8}}',
 '{"consecutive_count": 1}',
 'warning', true)

ON CONFLICT (rule_code) DO UPDATE SET
    rule_name = EXCLUDED.rule_name,
    description = EXCLUDED.description,
    threshold_config = EXCLUDED.threshold_config,
    updated_at = NOW();

SELECT '✅ 报警规则表创建完成！' as status;
