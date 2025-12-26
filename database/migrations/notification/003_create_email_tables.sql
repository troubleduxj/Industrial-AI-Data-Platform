-- 通知管理模块 - 邮件相关表
-- 创建时间: 2025-11-25

-- 1. 邮件服务器配置表
CREATE TABLE IF NOT EXISTS t_sys_email_server (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL DEFAULT 587,
    username VARCHAR(255),
    password VARCHAR(255),
    encryption VARCHAR(20) DEFAULT 'tls',
    from_email VARCHAR(255) NOT NULL,
    from_name VARCHAR(100),
    is_default BOOLEAN DEFAULT FALSE,
    is_enabled BOOLEAN DEFAULT TRUE,
    test_status VARCHAR(20) DEFAULT 'untested',
    last_test_time TIMESTAMP,
    last_test_result TEXT,
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER
);

COMMENT ON TABLE t_sys_email_server IS '邮件服务器配置表';
COMMENT ON COLUMN t_sys_email_server.name IS '配置名称';
COMMENT ON COLUMN t_sys_email_server.host IS 'SMTP服务器地址';
COMMENT ON COLUMN t_sys_email_server.port IS '端口号';
COMMENT ON COLUMN t_sys_email_server.encryption IS '加密方式: none/ssl/tls';
COMMENT ON COLUMN t_sys_email_server.test_status IS '测试状态: untested/success/failed';

-- 2. 邮件模板表
CREATE TABLE IF NOT EXISTS t_sys_email_template (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    variables JSONB DEFAULT '[]',
    template_type VARCHAR(50) NOT NULL DEFAULT 'custom',
    is_system BOOLEAN DEFAULT FALSE,
    is_enabled BOOLEAN DEFAULT TRUE,
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER
);

COMMENT ON TABLE t_sys_email_template IS '邮件模板表';
COMMENT ON COLUMN t_sys_email_template.code IS '模板代码';
COMMENT ON COLUMN t_sys_email_template.variables IS '可用变量: [{name, description, example}]';
COMMENT ON COLUMN t_sys_email_template.template_type IS '模板类型: alarm/announcement/task/custom';
COMMENT ON COLUMN t_sys_email_template.is_system IS '是否系统预设模板';

-- 3. 发送配置表
CREATE TABLE IF NOT EXISTS t_sys_notification_config (
    id SERIAL PRIMARY KEY,
    notification_type VARCHAR(50) NOT NULL UNIQUE,
    type_name VARCHAR(100) NOT NULL,
    channels JSONB DEFAULT '{"site": true, "email": false, "sms": false}',
    email_template_id INTEGER REFERENCES t_sys_email_template(id),
    retry_config JSONB DEFAULT '{"enabled": true, "max_retries": 3, "retry_interval": 60}',
    rate_limit JSONB DEFAULT '{"enabled": false, "max_per_hour": 100}',
    silent_period JSONB DEFAULT '{"enabled": false, "start_time": "22:00", "end_time": "08:00"}',
    is_enabled BOOLEAN DEFAULT TRUE,
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE t_sys_notification_config IS '通知发送配置表';
COMMENT ON COLUMN t_sys_notification_config.channels IS '发送渠道: site站内信/email邮件/sms短信';
COMMENT ON COLUMN t_sys_notification_config.retry_config IS '重试配置';
COMMENT ON COLUMN t_sys_notification_config.rate_limit IS '频率限制';
COMMENT ON COLUMN t_sys_notification_config.silent_period IS '静默时段';

-- 4. 邮件发送记录表
CREATE TABLE IF NOT EXISTS t_sys_email_log (
    id SERIAL PRIMARY KEY,
    notification_id INTEGER,
    template_id INTEGER,
    server_id INTEGER,
    to_email VARCHAR(255) NOT NULL,
    to_name VARCHAR(100),
    subject VARCHAR(255) NOT NULL,
    content TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE t_sys_email_log IS '邮件发送记录表';
COMMENT ON COLUMN t_sys_email_log.status IS '发送状态: pending/sending/sent/failed';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_email_server_default ON t_sys_email_server(is_default) WHERE is_default = TRUE;
CREATE INDEX IF NOT EXISTS idx_email_template_code ON t_sys_email_template(code);
CREATE INDEX IF NOT EXISTS idx_email_template_type ON t_sys_email_template(template_type);
CREATE INDEX IF NOT EXISTS idx_notification_config_type ON t_sys_notification_config(notification_type);
CREATE INDEX IF NOT EXISTS idx_email_log_status ON t_sys_email_log(status);
CREATE INDEX IF NOT EXISTS idx_email_log_created ON t_sys_email_log(created_at);

-- 插入默认邮件模板
INSERT INTO t_sys_email_template (code, name, subject, content, variables, template_type, is_system) VALUES
('alarm_notification', '报警通知模板', '【报警通知】{{rule_name}} - {{device_name}}', 
'<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <div style="background: #f56c6c; color: white; padding: 20px; text-align: center;">
    <h2 style="margin: 0;">⚠️ 设备报警通知</h2>
  </div>
  <div style="padding: 20px; background: #fff; border: 1px solid #eee;">
    <p>尊敬的用户：</p>
    <p>您的设备触发了报警，详情如下：</p>
    <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
      <tr><td style="padding: 8px; border: 1px solid #ddd; background: #f9f9f9;">设备名称</td><td style="padding: 8px; border: 1px solid #ddd;">{{device_name}}</td></tr>
      <tr><td style="padding: 8px; border: 1px solid #ddd; background: #f9f9f9;">报警规则</td><td style="padding: 8px; border: 1px solid #ddd;">{{rule_name}}</td></tr>
      <tr><td style="padding: 8px; border: 1px solid #ddd; background: #f9f9f9;">报警级别</td><td style="padding: 8px; border: 1px solid #ddd;">{{alarm_level}}</td></tr>
      <tr><td style="padding: 8px; border: 1px solid #ddd; background: #f9f9f9;">触发时间</td><td style="padding: 8px; border: 1px solid #ddd;">{{triggered_at}}</td></tr>
      <tr><td style="padding: 8px; border: 1px solid #ddd; background: #f9f9f9;">详细信息</td><td style="padding: 8px; border: 1px solid #ddd;">{{alarm_content}}</td></tr>
    </table>
    <p>请及时处理！</p>
  </div>
  <div style="padding: 15px; background: #f5f5f5; text-align: center; font-size: 12px; color: #999;">
    此邮件由系统自动发送，请勿回复
  </div>
</div>',
'[{"name": "device_name", "description": "设备名称"}, {"name": "rule_name", "description": "规则名称"}, {"name": "alarm_level", "description": "报警级别"}, {"name": "triggered_at", "description": "触发时间"}, {"name": "alarm_content", "description": "报警内容"}]',
'alarm', TRUE),

('system_announcement', '系统公告模板', '【系统公告】{{title}}',
'<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <div style="background: #409eff; color: white; padding: 20px; text-align: center;">
    <h2 style="margin: 0;">📢 系统公告</h2>
  </div>
  <div style="padding: 20px; background: #fff; border: 1px solid #eee;">
    <h3 style="color: #333;">{{title}}</h3>
    <div style="line-height: 1.8; color: #666;">{{content}}</div>
    <p style="color: #999; font-size: 12px; margin-top: 20px;">发布时间：{{publish_time}}</p>
  </div>
  <div style="padding: 15px; background: #f5f5f5; text-align: center; font-size: 12px; color: #999;">
    此邮件由系统自动发送，请勿回复
  </div>
</div>',
'[{"name": "title", "description": "公告标题"}, {"name": "content", "description": "公告内容"}, {"name": "publish_time", "description": "发布时间"}]',
'announcement', TRUE)
ON CONFLICT (code) DO NOTHING;

-- 插入默认发送配置
INSERT INTO t_sys_notification_config (notification_type, type_name, channels) VALUES
('alarm', '报警通知', '{"site": true, "email": true, "sms": false}'),
('announcement', '系统公告', '{"site": true, "email": false, "sms": false}'),
('task', '任务提醒', '{"site": true, "email": false, "sms": false}'),
('system', '系统消息', '{"site": true, "email": false, "sms": false}')
ON CONFLICT (notification_type) DO NOTHING;
