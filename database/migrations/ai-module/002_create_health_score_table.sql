-- AI模块：健康评分表
-- 用于存储设备健康评分历史记录

-- 创建健康评分表
CREATE TABLE IF NOT EXISTS t_ai_health_score (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL COMMENT '设备ID',
    
    -- 评分结果
    total_score FLOAT NOT NULL COMMENT '总评分（0-100）',
    grade VARCHAR(20) NOT NULL COMMENT '健康等级: A-优秀/B-良好/C-一般/D-较差/F-危险',
    grade_code VARCHAR(20) COMMENT '等级代码: A_EXCELLENT/B_GOOD/C_NORMAL/D_POOR/F_CRITICAL',
    
    -- 各维度评分
    performance_score FLOAT COMMENT '性能指标评分',
    anomaly_score FLOAT COMMENT '异常频率评分',
    trend_score FLOAT COMMENT '趋势健康评分',
    uptime_score FLOAT COMMENT '运行时长评分',
    
    -- 权重配置
    performance_weight FLOAT DEFAULT 0.30 COMMENT '性能权重',
    anomaly_weight FLOAT DEFAULT 0.25 COMMENT '异常权重',
    trend_weight FLOAT DEFAULT 0.25 COMMENT '趋势权重',
    uptime_weight FLOAT DEFAULT 0.20 COMMENT '运行时长权重',
    
    -- 原始数据（用于追溯）
    anomaly_count INT COMMENT '异常数量',
    total_count INT COMMENT '总数据点数',
    trend_direction VARCHAR(20) COMMENT '趋势方向',
    uptime_hours FLOAT COMMENT '运行时长（小时）',
    
    -- 额外信息
    remarks TEXT COMMENT '备注',
    metadata JSONB COMMENT '元数据（性能指标等）',
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间'
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_health_device_id ON t_ai_health_score(device_id);
CREATE INDEX IF NOT EXISTS idx_health_created_at ON t_ai_health_score(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_health_grade ON t_ai_health_score(grade);
CREATE INDEX IF NOT EXISTS idx_health_total_score ON t_ai_health_score(total_score DESC);

-- 组合索引（常见查询）
CREATE INDEX IF NOT EXISTS idx_health_device_time ON t_ai_health_score(device_id, created_at DESC);

-- 添加表注释
COMMENT ON TABLE t_ai_health_score IS 'AI设备健康评分历史记录表';

-- 添加列注释
COMMENT ON COLUMN t_ai_health_score.id IS '主键ID';
COMMENT ON COLUMN t_ai_health_score.device_id IS '设备ID';
COMMENT ON COLUMN t_ai_health_score.total_score IS '综合健康评分（0-100）';
COMMENT ON COLUMN t_ai_health_score.grade IS '健康等级';
COMMENT ON COLUMN t_ai_health_score.performance_score IS '性能维度评分';
COMMENT ON COLUMN t_ai_health_score.anomaly_score IS '异常频率维度评分';
COMMENT ON COLUMN t_ai_health_score.trend_score IS '趋势健康维度评分';
COMMENT ON COLUMN t_ai_health_score.uptime_score IS '运行时长维度评分';

-- 插入一些测试数据（可选）
-- INSERT INTO t_ai_health_score (
--     device_id, total_score, grade, grade_code,
--     performance_score, anomaly_score, trend_score, uptime_score,
--     anomaly_count, total_count, trend_direction, uptime_hours
-- ) VALUES 
--     ('DEVICE001', 92.5, 'A-优秀', 'A_EXCELLENT', 95.0, 90.0, 92.0, 93.0, 2, 1000, '平稳', 720.0),
--     ('DEVICE002', 78.3, 'C-一般', 'C_NORMAL', 75.0, 80.0, 78.0, 80.0, 50, 1000, '下降', 600.0),
--     ('DEVICE003', 55.0, 'F-危险', 'F_CRITICAL', 50.0, 45.0, 60.0, 65.0, 150, 1000, '下降', 400.0);

