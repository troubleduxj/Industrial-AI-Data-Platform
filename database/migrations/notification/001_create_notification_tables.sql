-- ========================================
-- 通知管理模块 - 数据库表创建
-- ========================================

BEGIN;

-- =====================================================
-- 1. 通知表 (t_sys_notification)
-- =====================================================

CREATE TABLE IF NOT EXISTS t_sys_notification (
    id BIGSERIAL PRIMARY KEY,
    
    -- 通知内容
    title VARCHAR(200) NOT NULL,
    content TEXT,
    notification_type VARCHAR(50) NOT NULL DEFAULT 'system',
    level VARCHAR(20) DEFAULT 'info',
    
    -- 发送范围
    scope VARCHAR(20) DEFAULT 'all',
    target_roles JSONB,
    target_users JSONB,
    
    -- 关联信息
    source_type VARCHAR(50),
    source_id BIGINT,
    link_url VARCHAR(500),
    
    -- 状态
    is_published BOOLEAN DEFAULT TRUE,
    publish_time TIMESTAMP,
    expire_time TIMESTAMP,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by BIGINT
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_sys_notification_type ON t_sys_notification(notification_type);
CREATE INDEX IF NOT EXISTS idx_sys_notification_scope ON t_sys_notification(scope);
CREATE INDEX IF NOT EXISTS idx_sys_notification_published ON t_sys_notification(is_published);
CREATE INDEX IF NOT EXISTS idx_sys_notification_publish_time ON t_sys_notification(publish_time);

COMMENT ON TABLE t_sys_notification IS '系统通知表';
COMMENT ON COLUMN t_sys_notification.notification_type IS '通知类型: announcement/alarm/task/system';
COMMENT ON COLUMN t_sys_notification.level IS '通知级别: info/warning/error';
COMMENT ON COLUMN t_sys_notification.scope IS '发送范围: all/role/user';

-- =====================================================
-- 2. 用户通知状态表 (t_sys_user_notification)
-- =====================================================

CREATE TABLE IF NOT EXISTS t_sys_user_notification (
    id BIGSERIAL PRIMARY KEY,
    
    user_id BIGINT NOT NULL,
    notification_id BIGINT NOT NULL REFERENCES t_sys_notification(id) ON DELETE CASCADE,
    
    is_read BOOLEAN DEFAULT FALSE,
    read_time TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, notification_id)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_sys_user_notification_user ON t_sys_user_notification(user_id);
CREATE INDEX IF NOT EXISTS idx_sys_user_notification_read ON t_sys_user_notification(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_sys_user_notification_deleted ON t_sys_user_notification(user_id, is_deleted);

COMMENT ON TABLE t_sys_user_notification IS '用户通知状态表';

COMMIT;

-- =====================================================
-- 3. 插入示例通知
-- =====================================================

INSERT INTO t_sys_notification (title, content, notification_type, level, scope, is_published, publish_time)
VALUES 
('欢迎使用设备监控系统', '感谢您使用本系统，如有问题请联系管理员。', 'announcement', 'info', 'all', true, NOW()),
('系统维护通知', '系统将于本周六凌晨2:00-4:00进行维护升级，届时系统将暂停服务。', 'announcement', 'warning', 'all', true, NOW())
ON CONFLICT DO NOTHING;

SELECT '✅ 通知管理表创建完成！' as status;
