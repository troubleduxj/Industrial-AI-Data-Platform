-- 决策引擎数据库表迁移脚本
-- 工业AI数据平台 V2 升级
-- 创建时间: 2024-12-26

-- =====================================================
-- 决策规则表
-- =====================================================
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

-- 索引
CREATE INDEX IF NOT EXISTS idx_decision_rules_enabled_priority ON t_decision_rules(enabled, priority);
CREATE INDEX IF NOT EXISTS idx_decision_rules_category ON t_decision_rules(category_id);
CREATE INDEX IF NOT EXISTS idx_decision_rules_model ON t_decision_rules(model_id);
CREATE INDEX IF NOT EXISTS idx_decision_rules_rule_id ON t_decision_rules(rule_id);

-- 注释
COMMENT ON TABLE t_decision_rules IS '决策规则表';
COMMENT ON COLUMN t_decision_rules.rule_id IS '规则ID';
COMMENT ON COLUMN t_decision_rules.name IS '规则名称';
COMMENT ON COLUMN t_decision_rules.description IS '规则描述';
COMMENT ON COLUMN t_decision_rules.conditions IS '条件配置(JSON DSL)';
COMMENT ON COLUMN t_decision_rules.actions IS '动作配置(JSON DSL)';
COMMENT ON COLUMN t_decision_rules.priority IS '优先级(数字越小优先级越高)';
COMMENT ON COLUMN t_decision_rules.enabled IS '是否启用';
COMMENT ON COLUMN t_decision_rules.cooldown_seconds IS '冷却时间(秒)';

-- =====================================================
-- 决策审计日志表
-- =====================================================
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

-- 索引
CREATE INDEX IF NOT EXISTS idx_decision_audit_rule_time ON t_decision_audit_logs(rule_id, trigger_time);
CREATE INDEX IF NOT EXISTS idx_decision_audit_time ON t_decision_audit_logs(trigger_time);
CREATE INDEX IF NOT EXISTS idx_decision_audit_result ON t_decision_audit_logs(result);
CREATE INDEX IF NOT EXISTS idx_decision_audit_asset ON t_decision_audit_logs(asset_id);

-- 注释
COMMENT ON TABLE t_decision_audit_logs IS '决策审计日志表';
COMMENT ON COLUMN t_decision_audit_logs.rule_id IS '规则ID';
COMMENT ON COLUMN t_decision_audit_logs.rule_name IS '规则名称';
COMMENT ON COLUMN t_decision_audit_logs.trigger_time IS '触发时间';
COMMENT ON COLUMN t_decision_audit_logs.trigger_data IS '触发时的数据快照';
COMMENT ON COLUMN t_decision_audit_logs.conditions_snapshot IS '条件配置快照';
COMMENT ON COLUMN t_decision_audit_logs.actions_executed IS '执行的动作列表';
COMMENT ON COLUMN t_decision_audit_logs.result IS '执行结果: success/partial/failed';
COMMENT ON COLUMN t_decision_audit_logs.error_message IS '错误信息';
COMMENT ON COLUMN t_decision_audit_logs.execution_duration_ms IS '执行耗时(毫秒)';
