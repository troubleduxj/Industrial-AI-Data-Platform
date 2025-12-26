-- =====================================================
-- 工作流管理模块数据库表
-- 创建时间: 2024-11-26
-- 说明: 创建工作流定义、执行记录、模板、调度等相关表
-- =====================================================

-- 1. 工作流定义表
CREATE TABLE IF NOT EXISTS `t_workflow` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `name` VARCHAR(100) NOT NULL COMMENT '工作流名称',
    `code` VARCHAR(50) NOT NULL COMMENT '工作流代码',
    `description` TEXT NULL COMMENT '工作流描述',
    
    -- 分类信息
    `type` VARCHAR(30) NOT NULL DEFAULT 'custom' COMMENT '工作流类型: device_monitor/alarm_process/data_collection/maintenance/custom',
    `category` VARCHAR(50) NULL COMMENT '工作流分类',
    `priority` VARCHAR(20) NOT NULL DEFAULT 'medium' COMMENT '优先级: low/medium/high/urgent',
    
    -- 工作流定义（JSON格式）
    `nodes` JSON NOT NULL COMMENT '节点定义',
    `connections` JSON NOT NULL COMMENT '连接定义',
    
    -- 触发配置
    `trigger_type` VARCHAR(30) NOT NULL DEFAULT 'manual' COMMENT '触发类型: manual/schedule/event/webhook',
    `trigger_config` JSON NOT NULL COMMENT '触发配置',
    
    -- 执行配置
    `execution_config` JSON NOT NULL COMMENT '执行配置',
    `timeout_seconds` INT NOT NULL DEFAULT 3600 COMMENT '超时时间(秒)',
    `retry_count` INT NOT NULL DEFAULT 0 COMMENT '重试次数',
    `retry_interval` INT NOT NULL DEFAULT 60 COMMENT '重试间隔(秒)',
    
    -- 通知配置
    `notification_config` JSON NOT NULL COMMENT '通知配置',
    
    -- 关联配置
    `related_device_types` JSON NOT NULL COMMENT '关联设备类型',
    `related_alarm_rules` JSON NOT NULL COMMENT '关联报警规则',
    
    -- 状态
    `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
    `is_published` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已发布',
    `version` VARCHAR(20) NOT NULL DEFAULT '1.0.0' COMMENT '版本号',
    
    -- 统计信息
    `execution_count` INT NOT NULL DEFAULT 0 COMMENT '执行次数',
    `success_count` INT NOT NULL DEFAULT 0 COMMENT '成功次数',
    `failure_count` INT NOT NULL DEFAULT 0 COMMENT '失败次数',
    `last_executed_at` DATETIME NULL COMMENT '最后执行时间',
    
    -- 创建/更新人
    `created_by` BIGINT NULL COMMENT '创建人ID',
    `created_by_name` VARCHAR(50) NULL COMMENT '创建人姓名',
    `updated_by` BIGINT NULL COMMENT '更新人ID',
    `updated_by_name` VARCHAR(50) NULL COMMENT '更新人姓名',
    `published_by` BIGINT NULL COMMENT '发布人ID',
    `published_at` DATETIME NULL COMMENT '发布时间',
    
    -- 时间戳
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_code` (`code`),
    KEY `idx_type` (`type`),
    KEY `idx_priority` (`priority`),
    KEY `idx_is_active` (`is_active`),
    KEY `idx_is_published` (`is_published`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作流定义表';


-- 2. 工作流执行记录表
CREATE TABLE IF NOT EXISTS `t_workflow_execution` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `workflow_id` BIGINT NOT NULL COMMENT '工作流ID',
    
    -- 执行信息
    `execution_id` VARCHAR(64) NOT NULL COMMENT '执行ID',
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '执行状态: pending/running/success/failed/cancelled/timeout',
    
    -- 触发信息
    `trigger_type` VARCHAR(30) NOT NULL COMMENT '触发类型',
    `trigger_data` JSON NULL COMMENT '触发数据',
    `triggered_by` BIGINT NULL COMMENT '触发人ID',
    `triggered_by_name` VARCHAR(50) NULL COMMENT '触发人姓名',
    
    -- 执行时间
    `started_at` DATETIME NULL COMMENT '开始时间',
    `completed_at` DATETIME NULL COMMENT '完成时间',
    `duration_ms` INT NULL COMMENT '执行时长(毫秒)',
    
    -- 执行结果
    `result` JSON NULL COMMENT '执行结果',
    `error_message` TEXT NULL COMMENT '错误信息',
    `error_stack` TEXT NULL COMMENT '错误堆栈',
    
    -- 节点执行状态
    `node_states` JSON NOT NULL COMMENT '节点执行状态',
    `current_node_id` VARCHAR(64) NULL COMMENT '当前节点ID',
    
    -- 上下文数据
    `context` JSON NOT NULL COMMENT '执行上下文',
    `variables` JSON NOT NULL COMMENT '变量数据',
    
    -- 重试信息
    `retry_count` INT NOT NULL DEFAULT 0 COMMENT '已重试次数',
    `parent_execution_id` VARCHAR(64) NULL COMMENT '父执行ID(重试时)',
    
    -- 时间戳
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_execution_id` (`execution_id`),
    KEY `idx_workflow_id` (`workflow_id`),
    KEY `idx_status` (`status`),
    KEY `idx_started_at` (`started_at`),
    KEY `idx_created_at` (`created_at`),
    CONSTRAINT `fk_execution_workflow` FOREIGN KEY (`workflow_id`) REFERENCES `t_workflow` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作流执行记录表';


-- 3. 工作流节点执行记录表
CREATE TABLE IF NOT EXISTS `t_workflow_node_execution` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `execution_id` BIGINT NOT NULL COMMENT '执行记录ID',
    
    -- 节点信息
    `node_id` VARCHAR(64) NOT NULL COMMENT '节点ID',
    `node_type` VARCHAR(30) NOT NULL COMMENT '节点类型',
    `node_name` VARCHAR(100) NULL COMMENT '节点名称',
    
    -- 执行状态
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '执行状态: pending/running/success/failed/skipped',
    
    -- 执行时间
    `started_at` DATETIME NULL COMMENT '开始时间',
    `completed_at` DATETIME NULL COMMENT '完成时间',
    `duration_ms` INT NULL COMMENT '执行时长(毫秒)',
    
    -- 输入输出
    `input_data` JSON NULL COMMENT '输入数据',
    `output_data` JSON NULL COMMENT '输出数据',
    
    -- 错误信息
    `error_message` TEXT NULL COMMENT '错误信息',
    `error_details` JSON NULL COMMENT '错误详情',
    
    -- 重试信息
    `retry_count` INT NOT NULL DEFAULT 0 COMMENT '重试次数',
    
    -- 时间戳
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    KEY `idx_execution_id` (`execution_id`),
    KEY `idx_node_id` (`node_id`),
    KEY `idx_status` (`status`),
    CONSTRAINT `fk_node_execution` FOREIGN KEY (`execution_id`) REFERENCES `t_workflow_execution` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作流节点执行记录表';


-- 4. 工作流模板表
CREATE TABLE IF NOT EXISTS `t_workflow_template` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `name` VARCHAR(100) NOT NULL COMMENT '模板名称',
    `code` VARCHAR(50) NOT NULL COMMENT '模板代码',
    `description` TEXT NULL COMMENT '模板描述',
    
    -- 分类
    `type` VARCHAR(30) NOT NULL COMMENT '模板类型',
    `category` VARCHAR(50) NULL COMMENT '模板分类',
    
    -- 模板定义
    `nodes` JSON NOT NULL COMMENT '节点定义',
    `connections` JSON NOT NULL COMMENT '连接定义',
    `default_config` JSON NOT NULL COMMENT '默认配置',
    
    -- 状态
    `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
    `is_system` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否系统模板',
    
    -- 使用统计
    `usage_count` INT NOT NULL DEFAULT 0 COMMENT '使用次数',
    
    -- 时间戳
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_code` (`code`),
    KEY `idx_type` (`type`),
    KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作流模板表';


-- 5. 工作流调度配置表
CREATE TABLE IF NOT EXISTS `t_workflow_schedule` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `workflow_id` BIGINT NOT NULL COMMENT '工作流ID',
    
    -- 调度配置
    `schedule_type` VARCHAR(20) NOT NULL COMMENT '调度类型: cron/interval/once',
    `cron_expression` VARCHAR(100) NULL COMMENT 'Cron表达式',
    `interval_seconds` INT NULL COMMENT '间隔秒数',
    `execute_at` DATETIME NULL COMMENT '执行时间(单次)',
    
    -- 时间范围
    `start_time` DATETIME NULL COMMENT '开始时间',
    `end_time` DATETIME NULL COMMENT '结束时间',
    
    -- 状态
    `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
    `last_executed_at` DATETIME NULL COMMENT '最后执行时间',
    `next_execute_at` DATETIME NULL COMMENT '下次执行时间',
    
    -- 时间戳
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    KEY `idx_workflow_id` (`workflow_id`),
    KEY `idx_is_active` (`is_active`),
    KEY `idx_next_execute_at` (`next_execute_at`),
    CONSTRAINT `fk_schedule_workflow` FOREIGN KEY (`workflow_id`) REFERENCES `t_workflow` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作流调度配置表';
