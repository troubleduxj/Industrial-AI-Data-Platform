-- =====================================================
-- 工作流管理模块数据库表 (PostgreSQL版本)
-- 创建时间: 2024-11-26
-- 说明: 创建工作流定义、执行记录、模板、调度等相关表
-- 表命名规范: 系统相关表使用 t_sys_ 前缀
-- =====================================================

-- 1. 工作流定义表
CREATE TABLE IF NOT EXISTS t_sys_workflow (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    
    -- 分类信息
    type VARCHAR(30) NOT NULL DEFAULT 'custom',
    category VARCHAR(50),
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    
    -- 工作流定义（JSON格式）
    nodes JSONB NOT NULL DEFAULT '[]'::jsonb,
    connections JSONB NOT NULL DEFAULT '[]'::jsonb,
    
    -- 触发配置
    trigger_type VARCHAR(30) NOT NULL DEFAULT 'manual',
    trigger_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- 执行配置
    execution_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    timeout_seconds INTEGER NOT NULL DEFAULT 3600,
    retry_count INTEGER NOT NULL DEFAULT 0,
    retry_interval INTEGER NOT NULL DEFAULT 60,
    
    -- 通知配置
    notification_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- 关联配置
    related_device_types JSONB NOT NULL DEFAULT '[]'::jsonb,
    related_alarm_rules JSONB NOT NULL DEFAULT '[]'::jsonb,
    
    -- 状态
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    
    -- 统计信息
    execution_count INTEGER NOT NULL DEFAULT 0,
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    last_executed_at TIMESTAMP,
    
    -- 创建/更新人
    created_by BIGINT,
    created_by_name VARCHAR(50),
    updated_by BIGINT,
    updated_by_name VARCHAR(50),
    published_by BIGINT,
    published_at TIMESTAMP,
    
    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_sys_workflow_type ON t_sys_workflow(type);
CREATE INDEX IF NOT EXISTS idx_sys_workflow_priority ON t_sys_workflow(priority);
CREATE INDEX IF NOT EXISTS idx_sys_workflow_is_active ON t_sys_workflow(is_active);
CREATE INDEX IF NOT EXISTS idx_sys_workflow_is_published ON t_sys_workflow(is_published);
CREATE INDEX IF NOT EXISTS idx_sys_workflow_created_at ON t_sys_workflow(created_at);

COMMENT ON TABLE t_sys_workflow IS '工作流定义表';

-- 2. 工作流执行记录表
CREATE TABLE IF NOT EXISTS t_sys_workflow_execution (
    id BIGSERIAL PRIMARY KEY,
    workflow_id BIGINT NOT NULL REFERENCES t_sys_workflow(id) ON DELETE CASCADE,
    
    -- 执行信息
    execution_id VARCHAR(64) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    
    -- 触发信息
    trigger_type VARCHAR(30) NOT NULL,
    trigger_data JSONB,
    triggered_by BIGINT,
    triggered_by_name VARCHAR(50),
    
    -- 执行时间
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    
    -- 执行结果
    result JSONB,
    error_message TEXT,
    error_stack TEXT,
    
    -- 节点执行状态
    node_states JSONB NOT NULL DEFAULT '{}'::jsonb,
    current_node_id VARCHAR(64),
    
    -- 上下文数据
    context JSONB NOT NULL DEFAULT '{}'::jsonb,
    variables JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- 重试信息
    retry_count INTEGER NOT NULL DEFAULT 0,
    parent_execution_id VARCHAR(64),
    
    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sys_wf_exec_workflow_id ON t_sys_workflow_execution(workflow_id);
CREATE INDEX IF NOT EXISTS idx_sys_wf_exec_status ON t_sys_workflow_execution(status);
CREATE INDEX IF NOT EXISTS idx_sys_wf_exec_started_at ON t_sys_workflow_execution(started_at);
CREATE INDEX IF NOT EXISTS idx_sys_wf_exec_created_at ON t_sys_workflow_execution(created_at);

COMMENT ON TABLE t_sys_workflow_execution IS '工作流执行记录表';

-- 3. 工作流节点执行记录表
CREATE TABLE IF NOT EXISTS t_sys_workflow_node_execution (
    id BIGSERIAL PRIMARY KEY,
    execution_id BIGINT NOT NULL REFERENCES t_sys_workflow_execution(id) ON DELETE CASCADE,
    
    -- 节点信息
    node_id VARCHAR(64) NOT NULL,
    node_type VARCHAR(30) NOT NULL,
    node_name VARCHAR(100),
    
    -- 执行状态
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    
    -- 执行时间
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    
    -- 输入输出
    input_data JSONB,
    output_data JSONB,
    
    -- 错误信息
    error_message TEXT,
    error_details JSONB,
    
    -- 重试信息
    retry_count INTEGER NOT NULL DEFAULT 0,
    
    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sys_wf_node_exec_id ON t_sys_workflow_node_execution(execution_id);
CREATE INDEX IF NOT EXISTS idx_sys_wf_node_node_id ON t_sys_workflow_node_execution(node_id);
CREATE INDEX IF NOT EXISTS idx_sys_wf_node_status ON t_sys_workflow_node_execution(status);

COMMENT ON TABLE t_sys_workflow_node_execution IS '工作流节点执行记录表';

-- 4. 工作流模板表
CREATE TABLE IF NOT EXISTS t_sys_workflow_template (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    
    -- 分类
    type VARCHAR(30) NOT NULL,
    category VARCHAR(50),
    
    -- 模板定义
    nodes JSONB NOT NULL DEFAULT '[]'::jsonb,
    connections JSONB NOT NULL DEFAULT '[]'::jsonb,
    default_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- 状态
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- 使用统计
    usage_count INTEGER NOT NULL DEFAULT 0,
    
    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sys_wf_tpl_type ON t_sys_workflow_template(type);
CREATE INDEX IF NOT EXISTS idx_sys_wf_tpl_is_active ON t_sys_workflow_template(is_active);

COMMENT ON TABLE t_sys_workflow_template IS '工作流模板表';

-- 5. 工作流调度配置表
CREATE TABLE IF NOT EXISTS t_sys_workflow_schedule (
    id BIGSERIAL PRIMARY KEY,
    workflow_id BIGINT NOT NULL REFERENCES t_sys_workflow(id) ON DELETE CASCADE,
    
    -- 调度配置
    schedule_type VARCHAR(20) NOT NULL,
    cron_expression VARCHAR(100),
    interval_seconds INTEGER,
    execute_at TIMESTAMP,
    
    -- 时间范围
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    
    -- 状态
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_executed_at TIMESTAMP,
    next_execute_at TIMESTAMP,
    
    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sys_wf_sched_workflow_id ON t_sys_workflow_schedule(workflow_id);
CREATE INDEX IF NOT EXISTS idx_sys_wf_sched_is_active ON t_sys_workflow_schedule(is_active);
CREATE INDEX IF NOT EXISTS idx_sys_wf_sched_next_exec ON t_sys_workflow_schedule(next_execute_at);

COMMENT ON TABLE t_sys_workflow_schedule IS '工作流调度配置表';
