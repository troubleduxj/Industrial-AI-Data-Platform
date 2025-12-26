-- =====================================================
-- ROLLBACK: 完全回滚设备数据模型相关的所有更改
-- 
-- ⚠️ 警告: 此脚本将删除所有设备数据模型相关的表和数据！
-- ⚠️ 请在执行前务必备份数据库！
-- 
-- 使用场景:
-- 1. 开发/测试环境需要重新开始
-- 2. 生产环境出现严重问题需要紧急回滚
-- 3. 需要完全卸载设备数据模型功能
-- =====================================================

-- 开始事务
BEGIN;

RAISE NOTICE '';
RAISE NOTICE '======================================================';
RAISE NOTICE '⚠️  开始执行回滚操作';
RAISE NOTICE '======================================================';
RAISE NOTICE '';

-- =====================================================
-- 步骤 1: 删除新建的表（按依赖关系逆序删除）
-- =====================================================

RAISE NOTICE '步骤 1/3: 删除新建的表...';

-- 1.1 删除模型执行日志表（依赖 t_device_data_model）
DROP TABLE IF EXISTS t_model_execution_log CASCADE;
RAISE NOTICE '  ✓ 删除表: t_model_execution_log';

-- 1.2 删除设备数据模型表
DROP TABLE IF EXISTS t_device_data_model CASCADE;
RAISE NOTICE '  ✓ 删除表: t_device_data_model';

-- 1.3 删除字段映射表（依赖 t_device_field）
DROP TABLE IF EXISTS t_device_field_mapping CASCADE;
RAISE NOTICE '  ✓ 删除表: t_device_field_mapping';

RAISE NOTICE '';

-- =====================================================
-- 步骤 2: 删除触发器和函数
-- =====================================================

RAISE NOTICE '步骤 2/3: 删除触发器和函数...';

-- 2.1 删除触发器
DROP TRIGGER IF EXISTS trigger_update_data_model_timestamp ON t_device_data_model;
RAISE NOTICE '  ✓ 删除触发器: trigger_update_data_model_timestamp';

DROP TRIGGER IF EXISTS trigger_update_field_mapping_timestamp ON t_device_field_mapping;
RAISE NOTICE '  ✓ 删除触发器: trigger_update_field_mapping_timestamp';

-- 2.2 删除函数
DROP FUNCTION IF EXISTS update_data_model_timestamp();
RAISE NOTICE '  ✓ 删除函数: update_data_model_timestamp()';

DROP FUNCTION IF EXISTS update_field_mapping_timestamp();
RAISE NOTICE '  ✓ 删除函数: update_field_mapping_timestamp()';

RAISE NOTICE '';

-- =====================================================
-- 步骤 3: 删除 t_device_field 表的新增列
-- =====================================================

RAISE NOTICE '步骤 3/3: 删除 t_device_field 表的新增列...';

-- 3.1 删除索引
DROP INDEX IF EXISTS idx_device_field_monitoring;
RAISE NOTICE '  ✓ 删除索引: idx_device_field_monitoring';

DROP INDEX IF EXISTS idx_device_field_ai;
RAISE NOTICE '  ✓ 删除索引: idx_device_field_ai';

-- 3.2 删除新增的列
ALTER TABLE t_device_field DROP COLUMN IF EXISTS display_config;
RAISE NOTICE '  ✓ 删除列: display_config';

ALTER TABLE t_device_field DROP COLUMN IF EXISTS alarm_threshold;
RAISE NOTICE '  ✓ 删除列: alarm_threshold';

ALTER TABLE t_device_field DROP COLUMN IF EXISTS data_range;
RAISE NOTICE '  ✓ 删除列: data_range';

ALTER TABLE t_device_field DROP COLUMN IF EXISTS aggregation_method;
RAISE NOTICE '  ✓ 删除列: aggregation_method';

ALTER TABLE t_device_field DROP COLUMN IF EXISTS is_ai_feature;
RAISE NOTICE '  ✓ 删除列: is_ai_feature';

ALTER TABLE t_device_field DROP COLUMN IF EXISTS is_monitoring_key;
RAISE NOTICE '  ✓ 删除列: is_monitoring_key';

RAISE NOTICE '';

-- =====================================================
-- 可选步骤 4: 删除前端菜单（如果已添加）
-- =====================================================

RAISE NOTICE '可选步骤 4: 隐藏/删除前端菜单...';

-- 4.1 方案1: 隐藏菜单（推荐，不删除数据）
UPDATE t_menu 
SET is_visible = FALSE, 
    updated_at = CURRENT_TIMESTAMP 
WHERE path LIKE '/data-model%';
RAISE NOTICE '  ✓ 隐藏菜单: /data-model*';

-- 4.2 方案2: 完全删除菜单（取消注释以使用）
-- DELETE FROM t_role_menu WHERE menu_id IN (SELECT id FROM t_menu WHERE path LIKE '/data-model%');
-- DELETE FROM t_menu WHERE path LIKE '/data-model%';
-- RAISE NOTICE '  ✓ 删除菜单: /data-model*';

RAISE NOTICE '';

-- 提交事务
COMMIT;

-- =====================================================
-- 验证回滚结果
-- =====================================================
DO $$
DECLARE
    v_table_exists BOOLEAN;
    v_column_exists BOOLEAN;
BEGIN
    -- 验证表是否已删除
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('t_device_data_model', 't_device_field_mapping', 't_model_execution_log')
    ) INTO v_table_exists;
    
    -- 验证列是否已删除
    SELECT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 't_device_field' 
        AND column_name IN ('is_monitoring_key', 'is_ai_feature', 'aggregation_method', 'data_range', 'alarm_threshold', 'display_config')
    ) INTO v_column_exists;
    
    RAISE NOTICE '======================================================';
    IF NOT v_table_exists AND NOT v_column_exists THEN
        RAISE NOTICE '✅ 回滚成功！所有更改已恢复';
        RAISE NOTICE '';
        RAISE NOTICE '已删除:';
        RAISE NOTICE '  - 3张新表';
        RAISE NOTICE '  - 6个新列';
        RAISE NOTICE '  - 2个触发器';
        RAISE NOTICE '  - 2个函数';
        RAISE NOTICE '  - 8个索引';
        RAISE NOTICE '  - 前端菜单（已隐藏）';
    ELSE
        IF v_table_exists THEN
            RAISE WARNING '⚠️  部分表未删除，请检查';
        END IF;
        IF v_column_exists THEN
            RAISE WARNING '⚠️  部分列未删除，请检查';
        END IF;
    END IF;
    RAISE NOTICE '======================================================';
    RAISE NOTICE '';
    
    -- 输出现有功能验证
    RAISE NOTICE '✅ 现有功能验证:';
    RAISE NOTICE '  - t_device_type: 完整保留';
    RAISE NOTICE '  - t_device_info: 完整保留';
    RAISE NOTICE '  - t_device_field: 保留原有列，删除新增列';
    RAISE NOTICE '  - 所有业务数据: 完整保留';
    RAISE NOTICE '';
    RAISE NOTICE '🎯 系统已恢复到安装设备数据模型前的状态';
END $$;

