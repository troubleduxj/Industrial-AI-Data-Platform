-- =====================================================
-- AI预测表优化 - JSONB索引创建
-- =====================================================
-- 文件: 003_optimize_predictions_table.sql
-- 目的: 为t_ai_predictions表的data_filters字段创建JSONB索引，优化设备关联查询性能
-- 创建时间: 2025-11-05
-- 作者: AI Module Team
-- =====================================================

-- 说明：
-- 本迁移文件基于"阶段1核心完善-最终方案"，采用JSONB索引方式实现设备关联查询，
-- 而不是添加冗余的device_code字段。
-- 
-- 预期性能：
-- - JSONB + 表达式索引查询时间: ~1.2ms
-- - 相比无索引提升: ~450ms -> 1.2ms
-- - 磁盘空间增加: ~5-10%

BEGIN;

-- =====================================================
-- 1. GIN索引（通用JSONB查询）
-- =====================================================
-- 用途: 支持各种JSONB查询操作，包括包含(contains)、存在性检查等
-- 适用场景: 复杂的JSONB查询、多字段联合查询

CREATE INDEX IF NOT EXISTS idx_predictions_data_filters_gin 
ON t_ai_predictions USING GIN (data_filters);

COMMENT ON INDEX idx_predictions_data_filters_gin IS 
'JSONB通用查询索引 - 支持复杂的data_filters查询操作';


-- =====================================================
-- 2. 表达式索引（高频查询路径优化）
-- =====================================================

-- 2.1 设备代码索引
-- 用途: 快速查询指定设备的预测记录
-- 查询示例: WHERE data_filters->>'device_code' = 'WLD-001'

CREATE INDEX IF NOT EXISTS idx_predictions_device_code 
ON t_ai_predictions ((data_filters->>'device_code'));

COMMENT ON INDEX idx_predictions_device_code IS 
'设备代码快速查询索引 - 优化按设备查询预测历史的性能';


-- 2.2 指标名称索引
-- 用途: 快速查询指定指标的预测记录
-- 查询示例: WHERE data_filters->>'metric_name' = 'temperature'

CREATE INDEX IF NOT EXISTS idx_predictions_metric_name 
ON t_ai_predictions ((data_filters->>'metric_name'));

COMMENT ON INDEX idx_predictions_metric_name IS 
'指标名称快速查询索引 - 优化按指标类型查询的性能';


-- =====================================================
-- 3. 复合索引（最常用查询模式）
-- =====================================================

-- 3.1 设备+指标+时间复合索引
-- 用途: 优化最常见的查询场景 - 查询某设备某指标的最新预测
-- 查询示例: WHERE data_filters->>'device_code' = 'WLD-001' 
--           AND data_filters->>'metric_name' = 'temperature'
--           ORDER BY created_at DESC

CREATE INDEX IF NOT EXISTS idx_predictions_device_metric_time 
ON t_ai_predictions (
    (data_filters->>'device_code'),
    (data_filters->>'metric_name'),
    created_at DESC
);

COMMENT ON INDEX idx_predictions_device_metric_time IS 
'设备+指标+时间复合查询索引 - 优化查询特定设备和指标的最新预测记录';


-- 3.2 设备+时间索引
-- 用途: 查询某设备的所有预测历史（不限指标）
-- 查询示例: WHERE data_filters->>'device_code' = 'WLD-001' 
--           ORDER BY created_at DESC

CREATE INDEX IF NOT EXISTS idx_predictions_device_time 
ON t_ai_predictions (
    (data_filters->>'device_code'),
    created_at DESC
);

COMMENT ON INDEX idx_predictions_device_time IS 
'设备+时间复合查询索引 - 优化查询设备所有预测历史';


-- =====================================================
-- 4. 状态索引（筛选已完成的预测）
-- =====================================================
-- 用途: 快速筛选特定状态的预测记录
-- 查询示例: WHERE status = 'completed' ORDER BY created_at DESC

CREATE INDEX IF NOT EXISTS idx_predictions_status_time 
ON t_ai_predictions (status, created_at DESC) 
WHERE status IN ('completed', 'failed');

COMMENT ON INDEX idx_predictions_status_time IS 
'状态+时间部分索引 - 优化查询已完成或失败的预测记录（排除pending/running状态以节省空间）';


-- =====================================================
-- 5. 数据源索引（按数据源查询）
-- =====================================================
-- 用途: 按数据源表查询相关预测
-- 查询示例: WHERE data_source = 't_device_realtime_data'

CREATE INDEX IF NOT EXISTS idx_predictions_data_source 
ON t_ai_predictions (data_source);

COMMENT ON INDEX idx_predictions_data_source IS 
'数据源索引 - 支持按数据源表筛选预测任务';


-- =====================================================
-- 6. 创建人+时间索引（个人预测记录查询）
-- =====================================================
-- 用途: 查询某用户创建的预测历史
-- 查询示例: WHERE created_by = 123 ORDER BY created_at DESC

CREATE INDEX IF NOT EXISTS idx_predictions_creator_time 
ON t_ai_predictions (created_by, created_at DESC) 
WHERE created_by IS NOT NULL;

COMMENT ON INDEX idx_predictions_creator_time IS 
'创建人+时间索引 - 优化查询用户个人的预测历史';


-- =====================================================
-- 7. 验证索引创建
-- =====================================================

-- 查看所有创建的索引
DO $$
DECLARE
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE tablename = 't_ai_predictions'
    AND indexname LIKE 'idx_predictions_%';
    
    RAISE NOTICE '✅ t_ai_predictions表索引数量: %', index_count;
    
    IF index_count >= 7 THEN
        RAISE NOTICE '✅ 所有索引创建成功！';
    ELSE
        RAISE WARNING '⚠️  索引数量少于预期，请检查';
    END IF;
END $$;


-- =====================================================
-- 8. 性能测试查询（可选，用于验证）
-- =====================================================

-- 说明：以下查询用于测试索引效果，需要有测试数据才能执行
-- 取消注释以执行性能测试

-- 8.1 测试设备代码查询性能
-- EXPLAIN ANALYZE
-- SELECT * FROM t_ai_predictions
-- WHERE data_filters->>'device_code' = 'WLD-001'
--   AND status = 'completed'
-- ORDER BY created_at DESC
-- LIMIT 20;

-- 8.2 测试设备+指标复合查询性能
-- EXPLAIN ANALYZE
-- SELECT * FROM t_ai_predictions
-- WHERE data_filters->>'device_code' = 'WLD-001'
--   AND data_filters->>'metric_name' = 'temperature'
-- ORDER BY created_at DESC
-- LIMIT 10;

-- 8.3 测试GIN索引查询性能
-- EXPLAIN ANALYZE
-- SELECT * FROM t_ai_predictions
-- WHERE data_filters @> '{"device_code": "WLD-001", "metric_name": "temperature"}'::jsonb
-- ORDER BY created_at DESC
-- LIMIT 10;


COMMIT;


-- =====================================================
-- 索引使用指南
-- =====================================================

-- 推荐的查询写法：

-- ✅ 使用表达式索引（推荐）：
-- SELECT * FROM t_ai_predictions 
-- WHERE data_filters->>'device_code' = 'WLD-001';

-- ✅ 使用GIN索引（适用于多字段查询）：
-- SELECT * FROM t_ai_predictions 
-- WHERE data_filters @> '{"device_code": "WLD-001"}'::jsonb;

-- ✅ 复合查询（最优性能）：
-- SELECT * FROM t_ai_predictions 
-- WHERE data_filters->>'device_code' = 'WLD-001'
--   AND data_filters->>'metric_name' = 'temperature'
-- ORDER BY created_at DESC;

-- ❌ 避免的查询写法：
-- SELECT * FROM t_ai_predictions 
-- WHERE data_filters::text LIKE '%WLD-001%';  -- 无法使用索引


-- =====================================================
-- 回滚脚本（如需回滚，执行以下语句）
-- =====================================================

-- DROP INDEX IF EXISTS idx_predictions_data_filters_gin;
-- DROP INDEX IF EXISTS idx_predictions_device_code;
-- DROP INDEX IF EXISTS idx_predictions_metric_name;
-- DROP INDEX IF EXISTS idx_predictions_device_metric_time;
-- DROP INDEX IF EXISTS idx_predictions_device_time;
-- DROP INDEX IF EXISTS idx_predictions_status_time;
-- DROP INDEX IF EXISTS idx_predictions_data_source;
-- DROP INDEX IF EXISTS idx_predictions_creator_time;

