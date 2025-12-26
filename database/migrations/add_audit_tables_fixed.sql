-- 审计系统数据库迁移脚本
-- 创建审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username VARCHAR(50),
    user_ip VARCHAR(45),
    user_agent VARCHAR(500),
    action_type VARCHAR(50),
    action_name VARCHAR(100),
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    permission_code VARCHAR(100),
    permission_result BOOLEAN,
    request_method VARCHAR(10),
    request_path VARCHAR(500),
    request_params TEXT,
    response_status INTEGER,
    response_message TEXT,
    extra_data TEXT,
    risk_level VARCHAR(20) DEFAULT 'LOW',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER
);

-- 创建安全事件表
CREATE TABLE IF NOT EXISTS security_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type VARCHAR(50),
    event_level VARCHAR(20),
    event_title VARCHAR(200),
    event_description TEXT,
    user_id INTEGER,
    username VARCHAR(50),
    user_ip VARCHAR(45),
    request_path VARCHAR(500),
    request_method VARCHAR(10),
    detection_rule VARCHAR(100),
    threat_score INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'PENDING',
    handled_by INTEGER,
    handled_at DATETIME,
    handle_note TEXT,
    extra_data TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 创建审计日志索引
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_username ON audit_logs(username);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action_type ON audit_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_risk_level ON audit_logs(risk_level);
CREATE INDEX IF NOT EXISTS idx_audit_logs_permission_result ON audit_logs(permission_result);

-- 创建安全事件索引
CREATE INDEX IF NOT EXISTS idx_security_events_event_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_security_events_event_level ON security_events(event_level);
CREATE INDEX IF NOT EXISTS idx_security_events_user_id ON security_events(user_id);
CREATE INDEX IF NOT EXISTS idx_security_events_status ON security_events(status);
CREATE INDEX IF NOT EXISTS idx_security_events_created_at ON security_events(created_at);
CREATE INDEX IF NOT EXISTS idx_security_events_threat_score ON security_events(threat_score);

-- 插入示例审计日志
INSERT OR IGNORE INTO audit_logs (
    user_id, username, user_ip, action_type, action_name, 
    resource_type, permission_result, request_method, request_path,
    response_status, response_message, risk_level, created_at
) VALUES 
(1, 'admin', '127.0.0.1', 'LOGIN', '用户登录', 'AUTH', 1, 'POST', '/api/v2/auth/login', 200, '登录成功', 'LOW', datetime('now', '-1 hour')),
(1, 'admin', '127.0.0.1', 'PERMISSION_CHECK', '权限验证', 'API', 1, 'GET', '/api/v2/users', 200, '权限验证通过', 'LOW', datetime('now', '-30 minutes')),
(2, 'demo_user', '192.168.1.100', 'PERMISSION_CHECK', '权限验证', 'API', 0, 'DELETE', '/api/v2/users/1', 403, '权限不足', 'MEDIUM', datetime('now', '-15 minutes'));

-- 插入示例安全事件
INSERT OR IGNORE INTO security_events (
    event_type, event_level, event_title, event_description,
    user_id, username, user_ip, request_path, request_method,
    detection_rule, threat_score, status, created_at
) VALUES 
('PERMISSION_DENIED', 'MEDIUM', '频繁权限拒绝', '用户demo_user在10分钟内权限验证失败5次', 
 2, 'demo_user', '192.168.1.100', '/api/v2/users', 'GET', 
 'PERMISSION_DENIED_THRESHOLD', 50, 'PENDING', datetime('now', '-10 minutes')),
('FAILED_LOGIN', 'HIGH', '频繁登录失败', '用户test_user在5分钟内登录失败6次',
 NULL, 'test_user', '192.168.1.200', '/api/v2/auth/login', 'POST',
 'FAILED_LOGIN_THRESHOLD', 70, 'PENDING', datetime('now', '-5 minutes'));