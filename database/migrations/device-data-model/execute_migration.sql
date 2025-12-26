-- =====================================================
-- 主执行脚本: 按顺序执行所有迁移
-- 
-- 用途: 一次性执行所有设备数据模型相关的数据库迁移
-- 使用方法:
--   psql -h localhost -U postgres -d device_monitor -f execute_migration.sql
-- 
-- ⚠️ 注意: 请先备份数据库！
-- =====================================================

\set ON_ERROR_STOP on

-- 显示执行信息
\echo ''
\echo '======================================================='
\echo '  设备数据模型 - 数据库迁移执行'
\echo '======================================================='
\echo ''
\echo '开始时间:' `date`
\echo ''

-- 设置时区
SET timezone = 'Asia/Shanghai';

-- =====================================================
-- 阶段 1: 创建数据库表
-- =====================================================

\echo '======================================================='
\echo '阶段 1/3: 创建数据库表'
\echo '======================================================='
\echo ''

\echo '>>> 执行 001_extend_device_field.sql ...'
\i 001_extend_device_field.sql
\echo ''

\echo '>>> 执行 002_create_device_data_model.sql ...'
\i 002_create_device_data_model.sql
\echo ''

\echo '>>> 执行 003_create_field_mapping.sql ...'
\i 003_create_field_mapping.sql
\echo ''

\echo '>>> 执行 004_create_execution_log.sql ...'
\i 004_create_execution_log.sql
\echo ''

-- =====================================================
-- 阶段 2: 数据迁移
-- =====================================================

\echo '======================================================='
\echo '阶段 2/3: 数据迁移'
\echo '======================================================='
\echo ''

\echo '>>> 执行 005_init_field_attributes.sql ...'
\i 005_init_field_attributes.sql
\echo ''

\echo '>>> 执行 006_create_default_mappings.sql ...'
\i 006_create_default_mappings.sql
\echo ''

\echo '>>> 执行 007_create_default_models.sql ...'
\i 007_create_default_models.sql
\echo ''

-- =====================================================
-- 阶段 3: 验证
-- =====================================================

\echo '======================================================='
\echo '阶段 3/3: 验证迁移结果'
\echo '======================================================='
\echo ''

DO $$
DECLARE
    v_device_field_columns INTEGER;
    v_data_model_count INTEGER;
    v_field_mapping_count INTEGER;
    v_execution_log_count INTEGER;
BEGIN
    -- 验证 t_device_field 表新增列
    SELECT COUNT(*) INTO v_device_field_columns
    FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 't_device_field' 
    AND column_name IN ('is_monitoring_key', 'is_ai_feature', 'aggregation_method', 'data_range', 'alarm_threshold', 'display_config');
    
    -- 验证新表记录数
    SELECT COUNT(*) INTO v_data_model_count FROM t_device_data_model;
    SELECT COUNT(*) INTO v_field_mapping_count FROM t_device_field_mapping;
    SELECT COUNT(*) INTO v_execution_log_count FROM t_model_execution_log;
    
    -- 输出验证结果
    RAISE NOTICE '======================================================';
    RAISE NOTICE '✅ 迁移执行成功！';
    RAISE NOTICE '======================================================';
    RAISE NOTICE '';
    RAISE NOTICE '数据库表:';
    RAISE NOTICE '  ✓ t_device_field: 新增 % 列', v_device_field_columns;
    RAISE NOTICE '  ✓ t_device_data_model: % 条记录', v_data_model_count;
    RAISE NOTICE '  ✓ t_device_field_mapping: % 条记录', v_field_mapping_count;
    RAISE NOTICE '  ✓ t_model_execution_log: % 条记录', v_execution_log_count;
    RAISE NOTICE '';
    
    IF v_device_field_columns = 6 THEN
        RAISE NOTICE '✅ t_device_field 扩展成功';
    ELSE
        RAISE WARNING '⚠️  t_device_field 扩展异常，预期6列，实际%列', v_device_field_columns;
    END IF;
    
    IF v_data_model_count >= 3 THEN
        RAISE NOTICE '✅ 默认数据模型创建成功 (% 个)', v_data_model_count;
    ELSE
        RAISE WARNING '⚠️  默认数据模型创建异常，预期至少3个，实际%个', v_data_model_count;
    END IF;
    
    IF v_field_mapping_count > 0 THEN
        RAISE NOTICE '✅ 字段映射创建成功 (% 个)', v_field_mapping_count;
    ELSE
        RAISE WARNING '⚠️  字段映射创建异常，记录数为0';
    END IF;
    
    RAISE NOTICE '';
    RAISE NOTICE '======================================================';
END $$;

-- 列出所有数据模型
\echo ''
\echo '创建的数据模型:'
\echo '======================================================='
SELECT 
    model_code,
    model_name,
    model_type,
    version,
    is_active,
    is_default
FROM t_device_data_model
ORDER BY model_type, model_code;

-- 统计字段映射
\echo ''
\echo '字段映射统计:'
\echo '======================================================='
SELECT 
    device_type_code,
    COUNT(*) as mapping_count,
    COUNT(*) FILTER (WHERE is_tag = TRUE) as tag_count,
    COUNT(*) FILTER (WHERE transform_rule IS NOT NULL) as transform_count
FROM t_device_field_mapping
GROUP BY device_type_code
ORDER BY device_type_code;

-- 显示完成信息
\echo ''
\echo '======================================================='
\echo '完成时间:' `date`
\echo '======================================================='
\echo ''
\echo '✅ 迁移已成功完成！'
\echo ''
\echo '下一步:'
\echo '  1. 开发 Python Model 和 Schema'
\echo '  2. 开发基础 API 接口'
\echo '  3. 开发前端界面'
\echo ''
\echo '回滚方法:'
\echo '  psql -h localhost -U postgres -d device_monitor -f rollback.sql'
\echo ''

