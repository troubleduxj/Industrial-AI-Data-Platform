-- =====================================================
-- 工业AI数据平台 V3 升级 - Schema重命名回滚脚本
-- 版本: V3.0
-- 创建时间: 2024-12-28
-- 描述: 回滚V3 Schema重命名迁移，恢复到旧的device命名规范
-- =====================================================

-- ⚠️ 警告: 执行此脚本将回滚V3 Schema重命名迁移
-- ⚠️ 注意: 此脚本将表名和列名恢复到旧的device命名规范
-- 请确保在执行前已备份重要数据

-- =====================================================
-- 回滚阶段4: 索引回滚
-- =====================================================

DO $
BEGIN
    RAISE NOTICE '🔄 开始回滚阶段4: 索引回滚...';
    
    -- 删除新命名的索引（如果需要恢复旧索引）
    -- 注意: 索引在表重命名时会自动保留，这里主要是清理新添加的索引
    
    -- 删除 t_asset_category 新索引
    DROP INDEX IF EXISTS idx_asset_category_code;
    DROP INDEX IF EXISTS idx_asset_category_active_industry;
    
    -- 删除 t_signal_definition 新索引
    DROP INDEX IF EXISTS idx_signal_definition_category;
    DROP INDEX IF EXISTS idx_signal_definition_realtime;
    DROP INDEX IF EXISTS idx_signal_definition_feature;
    DROP INDEX IF EXISTS idx_signal_definition_active;
    
    -- 删除 t_asset 新索引
    DROP INDEX IF EXISTS idx_asset_code;
    DROP INDEX IF EXISTS idx_asset_name;
    DROP INDEX IF EXISTS idx_asset_category_status;
    DROP INDEX IF EXISTS idx_asset_location;
    DROP INDEX IF EXISTS idx_asset_status;
    DROP INDEX IF EXISTS idx_asset_active;
    
    -- 更新迁移版本状态
    UPDATE t_migration_versions SET execution_status = 'rolled_back' WHERE version = 'V3.0-004';
    
    RAISE NOTICE '✅ 阶段4回滚完成: 索引已清理';
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '⚠️ 阶段4回滚警告: %', SQLERRM;
END $;


-- =====================================================
-- 回滚阶段3: 外键约束回滚
-- =====================================================

DO $
BEGIN
    RAISE NOTICE '🔄 开始回滚阶段3: 外键约束回滚...';
    
    -- 删除新添加的外键约束
    ALTER TABLE IF EXISTS t_signal_definition DROP CONSTRAINT IF EXISTS fk_signal_definition_category;
    ALTER TABLE IF EXISTS t_asset DROP CONSTRAINT IF EXISTS fk_asset_category;
    
    -- 更新迁移版本状态
    UPDATE t_migration_versions SET execution_status = 'rolled_back' WHERE version = 'V3.0-003';
    
    RAISE NOTICE '✅ 阶段3回滚完成: 外键约束已清理';
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '⚠️ 阶段3回滚警告: %', SQLERRM;
END $;

-- =====================================================
-- 回滚阶段2: 列重命名回滚 (category_id → device_type_id)
-- =====================================================

DO $
BEGIN
    RAISE NOTICE '🔄 开始回滚阶段2: 列重命名回滚...';
    
    -- 2.1 回滚 t_signal_definition.category_id → device_type_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 't_signal_definition' 
        AND column_name = 'category_id'
        AND table_schema = 'public'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 't_signal_definition' 
            AND column_name = 'device_type_id'
            AND table_schema = 'public'
        ) THEN
            ALTER TABLE t_signal_definition RENAME COLUMN category_id TO device_type_id;
            RAISE NOTICE '   ✅ 列 t_signal_definition.category_id 已回滚为 device_type_id';
        END IF;
    END IF;
    
    -- 2.2 回滚 t_asset.category_id → device_type_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 't_asset' 
        AND column_name = 'category_id'
        AND table_schema = 'public'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 't_asset' 
            AND column_name = 'device_type_id'
            AND table_schema = 'public'
        ) THEN
            ALTER TABLE t_asset RENAME COLUMN category_id TO device_type_id;
            RAISE NOTICE '   ✅ 列 t_asset.category_id 已回滚为 device_type_id';
        END IF;
    END IF;
    
    -- 2.3 回滚 t_ai_model.category_id → device_type_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 't_ai_model' 
        AND column_name = 'category_id'
        AND table_schema = 'public'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 't_ai_model' 
            AND column_name = 'device_type_id'
            AND table_schema = 'public'
        ) THEN
            ALTER TABLE t_ai_model RENAME COLUMN category_id TO device_type_id;
            RAISE NOTICE '   ✅ 列 t_ai_model.category_id 已回滚为 device_type_id';
        END IF;
    END IF;
    
    -- 2.4 回滚 t_feature_definition.category_id → device_type_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 't_feature_definition' 
        AND column_name = 'category_id'
        AND table_schema = 'public'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 't_feature_definition' 
            AND column_name = 'device_type_id'
            AND table_schema = 'public'
        ) THEN
            ALTER TABLE t_feature_definition RENAME COLUMN category_id TO device_type_id;
            RAISE NOTICE '   ✅ 列 t_feature_definition.category_id 已回滚为 device_type_id';
        END IF;
    END IF;
    
    -- 2.5 回滚 t_feature_view.category_id → device_type_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 't_feature_view' 
        AND column_name = 'category_id'
        AND table_schema = 'public'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 't_feature_view' 
            AND column_name = 'device_type_id'
            AND table_schema = 'public'
        ) THEN
            ALTER TABLE t_feature_view RENAME COLUMN category_id TO device_type_id;
            RAISE NOTICE '   ✅ 列 t_feature_view.category_id 已回滚为 device_type_id';
        END IF;
    END IF;
    
    -- 2.6 回滚 t_schema_version.category_id → device_type_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 't_schema_version' 
        AND column_name = 'category_id'
        AND table_schema = 'public'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 't_schema_version' 
            AND column_name = 'device_type_id'
            AND table_schema = 'public'
        ) THEN
            ALTER TABLE t_schema_version RENAME COLUMN category_id TO device_type_id;
            RAISE NOTICE '   ✅ 列 t_schema_version.category_id 已回滚为 device_type_id';
        END IF;
    END IF;
    
    -- 2.7 回滚 t_decision_rules.category_id → device_type_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 't_decision_rules' 
        AND column_name = 'category_id'
        AND table_schema = 'public'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 't_decision_rules' 
            AND column_name = 'device_type_id'
            AND table_schema = 'public'
        ) THEN
            ALTER TABLE t_decision_rules RENAME COLUMN category_id TO device_type_id;
            RAISE NOTICE '   ✅ 列 t_decision_rules.category_id 已回滚为 device_type_id';
        END IF;
    END IF;
    
    -- 2.8 回滚 t_data_sources.category_id → device_type_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 't_data_sources' 
        AND column_name = 'category_id'
        AND table_schema = 'public'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 't_data_sources' 
            AND column_name = 'device_type_id'
            AND table_schema = 'public'
        ) THEN
            ALTER TABLE t_data_sources RENAME COLUMN category_id TO device_type_id;
            RAISE NOTICE '   ✅ 列 t_data_sources.category_id 已回滚为 device_type_id';
        END IF;
    END IF;
    
    -- 2.9 回滚 t_dual_write_config.category_id → device_type_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 't_dual_write_config' 
        AND column_name = 'category_id'
        AND table_schema = 'public'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 't_dual_write_config' 
            AND column_name = 'device_type_id'
            AND table_schema = 'public'
        ) THEN
            ALTER TABLE t_dual_write_config RENAME COLUMN category_id TO device_type_id;
            RAISE NOTICE '   ✅ 列 t_dual_write_config.category_id 已回滚为 device_type_id';
        END IF;
    END IF;
    
    -- 更新迁移版本状态
    UPDATE t_migration_versions SET execution_status = 'rolled_back' WHERE version = 'V3.0-002';
    
    RAISE NOTICE '✅ 阶段2回滚完成: 列重命名已回滚';
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '⚠️ 阶段2回滚警告: %', SQLERRM;
END $;


-- =====================================================
-- 回滚阶段1: 表重命名回滚
-- =====================================================

DO $
BEGIN
    RAISE NOTICE '🔄 开始回滚阶段1: 表重命名回滚...';
    
    -- 1.1 回滚 t_asset_category → device_types
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_asset_category' AND table_schema = 'public') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'device_types' AND table_schema = 'public') THEN
            ALTER TABLE t_asset_category RENAME TO device_types;
            RAISE NOTICE '   ✅ 表 t_asset_category 已回滚为 device_types';
        ELSE
            RAISE NOTICE '   ⚠️ 表 device_types 已存在，跳过回滚';
        END IF;
    ELSE
        RAISE NOTICE '   ℹ️ 表 t_asset_category 不存在，无需回滚';
    END IF;
    
    -- 1.2 回滚 t_signal_definition → device_fields
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_signal_definition' AND table_schema = 'public') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'device_fields' AND table_schema = 'public') THEN
            ALTER TABLE t_signal_definition RENAME TO device_fields;
            RAISE NOTICE '   ✅ 表 t_signal_definition 已回滚为 device_fields';
        ELSE
            RAISE NOTICE '   ⚠️ 表 device_fields 已存在，跳过回滚';
        END IF;
    ELSE
        RAISE NOTICE '   ℹ️ 表 t_signal_definition 不存在，无需回滚';
    END IF;
    
    -- 1.3 回滚 t_asset → device_info
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_asset' AND table_schema = 'public') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'device_info' AND table_schema = 'public') THEN
            ALTER TABLE t_asset RENAME TO device_info;
            RAISE NOTICE '   ✅ 表 t_asset 已回滚为 device_info';
        ELSE
            RAISE NOTICE '   ⚠️ 表 device_info 已存在，跳过回滚';
        END IF;
    ELSE
        RAISE NOTICE '   ℹ️ 表 t_asset 不存在，无需回滚';
    END IF;
    
    -- 更新迁移版本状态
    UPDATE t_migration_versions SET execution_status = 'rolled_back' WHERE version = 'V3.0-001';
    
    RAISE NOTICE '✅ 阶段1回滚完成: 表重命名已回滚';
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '⚠️ 阶段1回滚警告: %', SQLERRM;
END $;

-- =====================================================
-- 更新V3整体状态
-- =====================================================

DO $
BEGIN
    -- 更新迁移记录状态
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_migration_record' AND table_schema = 'public') THEN
        UPDATE t_migration_record 
        SET status = 'rolled_back', completed_at = NOW(), updated_at = NOW()
        WHERE migration_name = 'v3_schema_rename';
        RAISE NOTICE '   ✅ 迁移记录状态已更新为 rolled_back';
    END IF;
    
    -- 更新V3.0整体状态
    UPDATE t_migration_versions SET execution_status = 'rolled_back', executed_at = NOW() WHERE version = 'V3.0';
    
    RAISE NOTICE '✅ V3.0 Schema重命名回滚完成';
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '⚠️ 更新V3状态警告: %', SQLERRM;
END $;

-- =====================================================
-- 显示回滚后状态
-- =====================================================

SELECT 
    version, 
    description, 
    execution_status, 
    executed_at 
FROM t_migration_versions 
WHERE version LIKE 'V3.0%'
ORDER BY executed_at;

-- =====================================================
-- 验证回滚结果
-- =====================================================

DO $
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '📊 V3 Schema重命名回滚验证报告';
    RAISE NOTICE '================================';
    
    -- 检查旧表是否恢复
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'device_types' AND table_schema = 'public') THEN
        RAISE NOTICE '✅ 表 device_types 已恢复';
    ELSE
        RAISE NOTICE '⚠️ 表 device_types 未恢复';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'device_fields' AND table_schema = 'public') THEN
        RAISE NOTICE '✅ 表 device_fields 已恢复';
    ELSE
        RAISE NOTICE '⚠️ 表 device_fields 未恢复';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'device_info' AND table_schema = 'public') THEN
        RAISE NOTICE '✅ 表 device_info 已恢复';
    ELSE
        RAISE NOTICE '⚠️ 表 device_info 未恢复';
    END IF;
    
    -- 检查新表是否已删除/重命名
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_asset_category' AND table_schema = 'public') THEN
        RAISE NOTICE '⚠️ 新表 t_asset_category 仍然存在';
    ELSE
        RAISE NOTICE '✅ 新表 t_asset_category 已处理';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_signal_definition' AND table_schema = 'public') THEN
        RAISE NOTICE '⚠️ 新表 t_signal_definition 仍然存在';
    ELSE
        RAISE NOTICE '✅ 新表 t_signal_definition 已处理';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_asset' AND table_schema = 'public') THEN
        RAISE NOTICE '⚠️ 新表 t_asset 仍然存在';
    ELSE
        RAISE NOTICE '✅ 新表 t_asset 已处理';
    END IF;
    
    RAISE NOTICE '================================';
END $;
