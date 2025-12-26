-- 创建Mock数据表
-- 用于存储API Mock规则，便于系统演示和测试

CREATE TABLE IF NOT EXISTS t_sys_mock_data (
    id BIGSERIAL PRIMARY KEY,
    
    -- 基本信息
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    
    -- 匹配规则
    method VARCHAR(10) NOT NULL,
    url_pattern VARCHAR(500) NOT NULL,
    
    -- Mock响应
    response_data JSONB NOT NULL,
    response_code INTEGER DEFAULT 200,
    delay INTEGER DEFAULT 0,
    
    -- 控制字段
    enabled BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,
    
    -- 统计字段
    hit_count INTEGER DEFAULT 0,
    last_hit_time TIMESTAMP,
    
    -- 创建者信息
    creator_id BIGINT,
    creator_name VARCHAR(64),
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_mock_data_name ON t_sys_mock_data(name);
CREATE INDEX idx_mock_data_method ON t_sys_mock_data(method);
CREATE INDEX idx_mock_data_url_pattern ON t_sys_mock_data(url_pattern);
CREATE INDEX idx_mock_data_enabled ON t_sys_mock_data(enabled);
CREATE INDEX idx_mock_data_priority ON t_sys_mock_data(priority);
CREATE INDEX idx_mock_data_creator_id ON t_sys_mock_data(creator_id);
CREATE INDEX idx_mock_data_enabled_priority ON t_sys_mock_data(enabled, priority);

-- 添加注释
COMMENT ON TABLE t_sys_mock_data IS 'Mock数据表 - 用于模拟API响应';
COMMENT ON COLUMN t_sys_mock_data.name IS '规则名称';
COMMENT ON COLUMN t_sys_mock_data.description IS '规则描述';
COMMENT ON COLUMN t_sys_mock_data.method IS 'HTTP方法 (GET/POST/PUT/DELETE等)';
COMMENT ON COLUMN t_sys_mock_data.url_pattern IS 'URL匹配模式，支持通配符';
COMMENT ON COLUMN t_sys_mock_data.response_data IS '响应数据(JSON格式)';
COMMENT ON COLUMN t_sys_mock_data.response_code IS 'HTTP响应状态码';
COMMENT ON COLUMN t_sys_mock_data.delay IS '延迟时间(毫秒)';
COMMENT ON COLUMN t_sys_mock_data.enabled IS '是否启用';
COMMENT ON COLUMN t_sys_mock_data.priority IS '优先级(数字越大越优先)';
COMMENT ON COLUMN t_sys_mock_data.hit_count IS '命中次数';
COMMENT ON COLUMN t_sys_mock_data.last_hit_time IS '最后命中时间';

-- 插入示例Mock规则
INSERT INTO t_sys_mock_data (
    name, description, method, url_pattern, response_data, response_code, enabled, priority
) VALUES 
(
    '示例-设备列表Mock', 
    '返回模拟的设备列表数据', 
    'GET', 
    '/api/v2/devices',
    '{"code": 200, "message": "成功", "data": {"items": [{"id": 1, "name": "演示设备1", "type": "焊机", "status": "在线"}], "total": 1}}'::jsonb,
    200,
    FALSE,
    0
),
(
    '示例-用户信息Mock',
    '返回模拟的用户信息',
    'GET',
    '/api/v2/users/*',
    '{"code": 200, "message": "成功", "data": {"id": 1, "username": "演示用户", "email": "demo@example.com"}}'::jsonb,
    200,
    FALSE,
    0
);

SELECT '✅ Mock数据表创建成功！' AS result;

