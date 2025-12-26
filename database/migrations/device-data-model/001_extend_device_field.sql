-- =====================================================
-- 001: 扩展 t_device_field 表
-- 
-- 目的: 为设备字段定义表添加元数据驱动所需的新字段
-- 原则: 只 ADD COLUMN，不 ALTER/DROP 现有列
-- 兼容性: 所有新列允许 NULL 或有默认值，100% 向后兼容
-- =====================================================

-- 开始事务
BEGIN;

-- 1. 添加监控相关字段
ALTER TABLE t_device_field 
ADD COLUMN IF NOT EXISTS is_monitoring_key BOOLEAN DEFAULT FALSE;

ALTER TABLE t_device_field 
ADD COLUMN IF NOT EXISTS is_ai_feature BOOLEAN DEFAULT FALSE;

-- 2. 添加聚合方法字段
ALTER TABLE t_device_field 
ADD COLUMN IF NOT EXISTS aggregation_method VARCHAR(20);

-- 3. 添加数据范围字段（JSONB格式）
ALTER TABLE t_device_field 
ADD COLUMN IF NOT EXISTS data_range JSONB;

-- 4. 添加报警阈值字段（JSONB格式）
ALTER TABLE t_device_field 
ADD COLUMN IF NOT EXISTS alarm_threshold JSONB;

-- 5. 添加显示配置字段（JSONB格式）
ALTER TABLE t_device_field 
ADD COLUMN IF NOT EXISTS display_config JSONB;

-- 6. 创建索引（提升查询性能）
CREATE INDEX IF NOT EXISTS idx_device_field_monitoring 
ON t_device_field(is_monitoring_key) 
WHERE is_monitoring_key = TRUE;

CREATE INDEX IF NOT EXISTS idx_device_field_ai 
ON t_device_field(is_ai_feature) 
WHERE is_ai_feature = TRUE;

-- 7. 添加表注释
COMMENT ON COLUMN t_device_field.is_monitoring_key IS '是否为实时监控关键字段（用于实时监控模型）';
COMMENT ON COLUMN t_device_field.is_ai_feature IS '是否为AI分析特征字段（用于AI模型训练）';
COMMENT ON COLUMN t_device_field.aggregation_method IS '聚合方法：avg/sum/max/min/count/first/last';
COMMENT ON COLUMN t_device_field.data_range IS '正常数据范围（JSONB）：{"min": 0, "max": 100}';
COMMENT ON COLUMN t_device_field.alarm_threshold IS '报警阈值配置（JSONB）：{"warning": 80, "critical": 90}';
COMMENT ON COLUMN t_device_field.display_config IS '前端显示配置（JSONB）：{"chart_type": "line", "color": "#1890ff"}';

-- 提交事务
COMMIT;

-- =====================================================
-- 验证脚本执行结果
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE '✅ 001_extend_device_field.sql 执行成功！';
    RAISE NOTICE '   - 新增字段: is_monitoring_key, is_ai_feature';
    RAISE NOTICE '   - 新增字段: aggregation_method, data_range';
    RAISE NOTICE '   - 新增字段: alarm_threshold, display_config';
    RAISE NOTICE '   - 创建索引: idx_device_field_monitoring, idx_device_field_ai';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  注意: 现有数据完全不受影响，所有新列默认为 NULL 或 FALSE';
END $$;

