-- AI模块：异常记录表
-- 用于存储AI检测到的设备异常数据

-- 创建异常记录表
CREATE TABLE IF NOT EXISTS t_ai_anomaly_record (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL COMMENT '设备ID',
    metric_name VARCHAR(100) NOT NULL COMMENT '指标名称',
    
    -- 异常值信息
    anomaly_value FLOAT NOT NULL COMMENT '异常值',
    expected_value FLOAT COMMENT '期望值（正常值）',
    deviation FLOAT COMMENT '偏差量',
    
    -- 检测信息
    detection_method VARCHAR(50) NOT NULL COMMENT '检测方法: statistical/isolation_forest/combined',
    severity VARCHAR(20) NOT NULL COMMENT '严重程度: 正常/轻微/中等/严重/危险',
    severity_code VARCHAR(20) COMMENT '严重程度代码: NORMAL/SLIGHT/MODERATE/SEVERE/CRITICAL',
    anomaly_score FLOAT COMMENT '异常分数',
    z_score FLOAT COMMENT 'Z分数（统计方法）',
    
    -- 时间信息
    anomaly_timestamp TIMESTAMP COMMENT '异常发生时间',
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '检测时间',
    
    -- 处理状态
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态: active/acknowledged/resolved/ignored',
    acknowledged_by VARCHAR(50) COMMENT '确认人',
    acknowledged_at TIMESTAMP COMMENT '确认时间',
    resolved_by VARCHAR(50) COMMENT '解决人',
    resolved_at TIMESTAMP COMMENT '解决时间',
    
    -- 备注
    remarks TEXT COMMENT '备注',
    
    -- 额外信息（JSON格式）
    extra_info JSONB COMMENT '额外信息',
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_anomaly_device_id ON t_ai_anomaly_record(device_id);
CREATE INDEX IF NOT EXISTS idx_anomaly_metric_name ON t_ai_anomaly_record(metric_name);
CREATE INDEX IF NOT EXISTS idx_anomaly_detected_at ON t_ai_anomaly_record(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_anomaly_severity ON t_ai_anomaly_record(severity);
CREATE INDEX IF NOT EXISTS idx_anomaly_status ON t_ai_anomaly_record(status);
CREATE INDEX IF NOT EXISTS idx_anomaly_timestamp ON t_ai_anomaly_record(anomaly_timestamp DESC);

-- 组合索引（常见查询）
CREATE INDEX IF NOT EXISTS idx_anomaly_device_metric ON t_ai_anomaly_record(device_id, metric_name, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_anomaly_status_detected ON t_ai_anomaly_record(status, detected_at DESC);

-- 添加表注释
COMMENT ON TABLE t_ai_anomaly_record IS 'AI异常检测记录表';

-- 添加列注释
COMMENT ON COLUMN t_ai_anomaly_record.id IS '主键ID';
COMMENT ON COLUMN t_ai_anomaly_record.device_id IS '设备ID';
COMMENT ON COLUMN t_ai_anomaly_record.metric_name IS '指标名称（如温度、压力等）';
COMMENT ON COLUMN t_ai_anomaly_record.anomaly_value IS '检测到的异常值';
COMMENT ON COLUMN t_ai_anomaly_record.expected_value IS '期望的正常值';
COMMENT ON COLUMN t_ai_anomaly_record.deviation IS '偏差量（异常值-期望值）';
COMMENT ON COLUMN t_ai_anomaly_record.detection_method IS '检测方法';
COMMENT ON COLUMN t_ai_anomaly_record.severity IS '异常严重程度';
COMMENT ON COLUMN t_ai_anomaly_record.anomaly_score IS '异常分数（0-1或更高）';
COMMENT ON COLUMN t_ai_anomaly_record.status IS '处理状态';

-- 插入一些测试数据（可选）
-- INSERT INTO t_ai_anomaly_record (device_id, metric_name, anomaly_value, expected_value, deviation, detection_method, severity, severity_code, anomaly_score)
-- VALUES 
--     ('DEVICE001', 'temperature', 85.5, 25.0, 60.5, 'statistical', '严重', 'SEVERE', 5.2),
--     ('DEVICE001', 'pressure', 1200.0, 1013.0, 187.0, 'isolation_forest', '中等', 'MODERATE', 0.85),
--     ('DEVICE002', 'humidity', 95.0, 60.0, 35.0, 'combined', '轻微', 'SLIGHT', 3.5);

