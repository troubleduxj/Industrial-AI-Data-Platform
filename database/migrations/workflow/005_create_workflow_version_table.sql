-- 工作流版本历史表
-- 用于存储工作流的版本历史，支持版本对比和回滚

-- 创建版本历史表
CREATE TABLE IF NOT EXISTS t_sys_workflow_version (
    id BIGSERIAL PRIMARY KEY,
    workflow_id BIGINT NOT NULL REFERENCES t_sys_workflow(id) ON DELETE CASCADE,
    
    -- 版本信息
    version VARCHAR(20) NOT NULL,
    version_name VARCHAR(100),
    description TEXT,
    
    -- 工作流快照（JSON格式）
    snapshot JSONB NOT NULL,
    
    -- 变更信息
    change_type VARCHAR(20) DEFAULT 'update',
    change_summary TEXT,
    
    -- 状态
    is_published BOOLEAN DEFAULT FALSE,
    is_current BOOLEAN DEFAULT FALSE,
    
    -- 创建人
    created_by BIGINT,
    created_by_name VARCHAR(50),
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_workflow_version_workflow_id ON t_sys_workflow_version(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_version_version ON t_sys_workflow_version(version);
CREATE INDEX IF NOT EXISTS idx_workflow_version_is_current ON t_sys_workflow_version(is_current);
CREATE INDEX IF NOT EXISTS idx_workflow_version_created_at ON t_sys_workflow_version(created_at);

-- 添加注释
COMMENT ON TABLE t_sys_workflow_version IS '工作流版本历史表';
COMMENT ON COLUMN t_sys_workflow_version.workflow_id IS '关联工作流ID';
COMMENT ON COLUMN t_sys_workflow_version.version IS '版本号';
COMMENT ON COLUMN t_sys_workflow_version.version_name IS '版本名称';
COMMENT ON COLUMN t_sys_workflow_version.snapshot IS '工作流快照';
COMMENT ON COLUMN t_sys_workflow_version.change_type IS '变更类型: create/update/publish/rollback';
COMMENT ON COLUMN t_sys_workflow_version.is_published IS '是否为发布版本';
COMMENT ON COLUMN t_sys_workflow_version.is_current IS '是否为当前版本';
