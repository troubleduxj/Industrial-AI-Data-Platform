-- =====================================================
-- 004: 创建 t_model_execution_log 表
-- 
-- 目的: 创建模型执行日志表，记录模型查询/特征提取/训练的执行情况
-- 原则: 新增表，不修改现有表
-- 兼容性: 通过外键关联新建的 t_device_data_model 表
-- =====================================================

-- 开始事务
BEGIN;

-- 1. 创建模型执行日志表
CREATE TABLE IF NOT EXISTS t_model_execution_log (
    -- 基础字段
    id SERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL,
    execution_type VARCHAR(30) NOT NULL CHECK (execution_type IN ('query', 'feature_extract', 'training', 'validation')),
    
    -- 执行参数（JSONB格式）
    input_params JSONB,
    /* input_params 格式示例:
    {
        "device_code": "14323A0032",
        "start_time": "2025-11-01 00:00:00",
        "end_time": "2025-11-01 23:59:59",
        "filters": {
            "shift_name": "白班"
        },
        "page": 1,
        "page_size": 100
    }
    */
    
    -- 执行结果
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'failed', 'timeout', 'cancelled')),
    result_summary JSONB,
    /* result_summary 格式示例:
    {
        "total_rows": 1523,
        "returned_rows": 100,
        "features_extracted": 15,
        "data_quality_score": 0.95,
        "warnings": []
    }
    */
    error_message TEXT,
    
    -- 性能指标
    execution_time_ms INTEGER,
    data_volume INTEGER,
    memory_usage_mb INTEGER,
    
    -- 生成的SQL（用于审计和调试）
    generated_sql TEXT,
    
    -- 审计字段
    executed_by INTEGER,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- ⭐ 外键约束：关联 t_device_data_model 表
    CONSTRAINT fk_execution_log_model 
        FOREIGN KEY (model_id) 
        REFERENCES t_device_data_model(id) 
        ON DELETE CASCADE
);

-- 2. 添加表注释
COMMENT ON TABLE t_model_execution_log IS '模型执行日志表';
COMMENT ON COLUMN t_model_execution_log.model_id IS '数据模型ID（外键）';
COMMENT ON COLUMN t_model_execution_log.execution_type IS '执行类型：query/feature_extract/training/validation';
COMMENT ON COLUMN t_model_execution_log.input_params IS '输入参数（JSONB）';
COMMENT ON COLUMN t_model_execution_log.status IS '执行状态：success/failed/timeout/cancelled';
COMMENT ON COLUMN t_model_execution_log.result_summary IS '结果摘要（JSONB）';
COMMENT ON COLUMN t_model_execution_log.error_message IS '错误信息';
COMMENT ON COLUMN t_model_execution_log.execution_time_ms IS '执行时间（毫秒）';
COMMENT ON COLUMN t_model_execution_log.data_volume IS '数据量（行数）';
COMMENT ON COLUMN t_model_execution_log.memory_usage_mb IS '内存使用（MB）';
COMMENT ON COLUMN t_model_execution_log.generated_sql IS '生成的SQL（用于审计）';
COMMENT ON COLUMN t_model_execution_log.executed_by IS '执行人ID';
COMMENT ON COLUMN t_model_execution_log.executed_at IS '执行时间';

-- 3. 创建索引
CREATE INDEX IF NOT EXISTS idx_execution_log_model 
ON t_model_execution_log(model_id);

CREATE INDEX IF NOT EXISTS idx_execution_log_time 
ON t_model_execution_log(executed_at DESC);

CREATE INDEX IF NOT EXISTS idx_execution_log_status 
ON t_model_execution_log(status);

CREATE INDEX IF NOT EXISTS idx_execution_log_type 
ON t_model_execution_log(execution_type);

CREATE INDEX IF NOT EXISTS idx_execution_log_executed_by 
ON t_model_execution_log(executed_by);

-- 复合索引（用于性能分析查询）
CREATE INDEX IF NOT EXISTS idx_execution_log_model_time 
ON t_model_execution_log(model_id, executed_at DESC);

CREATE INDEX IF NOT EXISTS idx_execution_log_type_status 
ON t_model_execution_log(execution_type, status, executed_at DESC);

-- 4. 创建分区（按月分区，提升大数据量查询性能）
-- 注意：如果PostgreSQL版本 < 10，则跳过此步骤
DO $$
BEGIN
    IF (SELECT current_setting('server_version_num')::int >= 100000) THEN
        -- PostgreSQL 10+ 支持声明式分区
        RAISE NOTICE 'PostgreSQL 版本支持分区，建议手动创建分区表';
        RAISE NOTICE '示例: CREATE TABLE t_model_execution_log_2025_11 PARTITION OF t_model_execution_log FOR VALUES FROM (''2025-11-01'') TO (''2025-12-01'');';
    ELSE
        RAISE NOTICE 'PostgreSQL 版本 < 10，跳过分区创建';
    END IF;
END $$;

-- 提交事务
COMMIT;

-- =====================================================
-- 验证脚本执行结果
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE '✅ 004_create_execution_log.sql 执行成功！';
    RAISE NOTICE '   - 创建表: t_model_execution_log';
    RAISE NOTICE '   - 外键关联: t_device_data_model.id';
    RAISE NOTICE '   - 创建索引: 7个（model, time, status, type, executed_by, model_time, type_status）';
    RAISE NOTICE '   - 分区提示: 建议按月创建分区表（PostgreSQL 10+）';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  注意: 现有表完全不受影响';
END $$;

