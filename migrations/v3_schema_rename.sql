-- =====================================================
-- 工业AI数据平台 V3 升级 - Schema重命名迁移脚本
-- 版本: V3.0
-- 创建时间: 2024-12-28
-- 描述: 将旧的device相关命名迁移到新的asset/signal命名规范
-- =====================================================

-- 本脚本处理以下重命名:
-- 1. 表重命名: device_types → asset_categories (如果存在旧表)
-- 2. 表重命名: device_fields → signal_definitions (如果存在旧表)
-- 3. 表重命名: device_info → assets (如果存在旧表)
-- 4. 列重命名: device_type_id → category_id
-- 5. 外键约束更新
-- 6. 索引更新

-- ⚠️ 注意: 此脚本设计为幂等的，可以安全地多次执行
-- ⚠️ 建议: 执行前请备份数据库

-- =====================================================
-- 确保迁移版本跟踪表存在
-- =====================================================

CREATE TABLE IF NOT EXISTS t_migration_versions (
    id BIGSERIAL PRIMARY KEY,
    version VARCHAR(20) NOT NULL UNIQUE,
    description TEXT,
    script_name VARCHAR(100) NOT NULL,
    executed_at TIMESTAMP DEFAULT NOW(),
    execution_status VARCHAR(20) DEFAULT 'success',
    execution_duration_ms INT,
    rollback_script TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_migration_versions_version ON t_migration_versions(version);
CREATE INDEX IF NOT EXISTS idx_migration_versions_status ON t_migration_versions(execution_status);

-- =====================================================
-- 阶段1: 表重命名 (device_types → t_asset_category)
-- =====================================================

DO $
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    duration_ms INT;
BEGIN
    start_time := clock_timestamp();
    
    -- 检查是否已执行过此迁移
    IF EXISTS (SELECT 1 FROM t_migration_versions WHERE version = 'V3.0-001' AND execution_status = 'success') THEN
        RAISE NOTICE '⏭️ 迁移 V3.0-001 已执行，跳过表重命名';
        RETURN;
    END IF;
    
    RAISE NOTICE '🔄 开始阶段1: 表重命名...';
    
    -- 1.1 重命名 device_types → t_asset_category (如果存在旧表且新表不存在)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'device_types' AND table_schema = 'public') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_asset_category' AND table_schema = 'public') THEN
            ALTER TABLE device_types RENAME TO t_asset_category;
            RAISE NOTICE '   ✅ 表 device_types 已重命名为 t_asset_category';
        ELSE
            RAISE NOTICE '   ⚠️ 表 t_asset_category 已存在，跳过 device_types 重命名';
        END IF;
    ELSE
        RAISE NOTICE '   ℹ️ 表 device_types 不存在，无需重命名';
    END IF;
    
    -- 1.2 重命名 device_fields → t_signal_definition (如果存在旧表且新表不存在)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'device_fields' AND table_schema = 'public') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_signal_definition' AND table_schema = 'public') THEN
            ALTER TABLE device_fields RENAME TO t_signal_definition;
            RAISE NOTICE '   ✅ 表 device_fields 已重命名为 t_signal_definition';
        ELSE
            RAISE NOTICE '   ⚠️ 表 t_signal_definition 已存在，跳过 device_fields 重命名';
        END IF;
    ELSE
        RAISE NOTICE '   ℹ️ 表 device_fields 不存在，无需重命名';
    END IF;
    
    -- 1.3 重命名 device_info → t_asset (如果存在旧表且新表不存在)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'device_info' AND table_schema = 'public') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_asset' AND table_schema = 'public') THEN
            ALTER TABLE device_info RENAME TO t_asset;
            RAISE NOTICE '   ✅ 表 device_info 已重命名为 t_asset';
        ELSE
            RAISE NOTICE '   ⚠️ 表 t_asset 已存在，跳过 device_info 重命名';
        END IF;
    ELSE
        RAISE NOTICE '   ℹ️ 表 device_info 不存在，无需重命名';
    END IF;
    
    end_time := clock_timestamp();
    duration_ms := EXTRACT(MILLISECONDS FROM (end_time - start_time))::INT;
    
    -- 记录迁移版本
    INSERT INTO t_migration_versions (version, description, script_name, execution_duration_ms, rollback_script)
    VALUES ('V3.0-001', '表重命名: device_* → asset/signal', 'v3_schema_rename.sql', duration_ms, 'v3_schema_rollback.sql')
    ON CONFLICT (version) DO UPDATE SET execution_status = 'success', executed_at = NOW();
    
    RAISE NOTICE '✅ 阶段1完成: 表重命名 (耗时: % ms)', duration_ms;
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '❌ 阶段1失败: %', SQLERRM;
    -- 记录失败状态
    INSERT INTO t_migration_versions (version, description, script_name, execution_status)
    VALUES ('V3.0-001', '表重命名失败: ' || SQLERRM, 'v3_schema_rename.sql', 'failed')
    ON CONFLICT (version) DO UPDATE SET execution_status = 'failed', executed_at = NOW();
    RAISE;
END $;


-- =====================================================
-- 阶段2: 列重命名 (device_type_id → category_id)
-- =====================================================

DO $
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    duration_ms INT;
BEGIN
    start_time := clock_timestamp();
    
    -- 检查是否已执行过此迁移
    IF EXISTS (SELECT 1 FROM t_migration_versions WHERE version = 'V3.0-002' AND execution_status = 'success') THEN
        RAISE NOTICE '⏭️ 迁移 V3.0-002 已执行，跳过列重命名';
        RETURN;
    END IF;
    
    RAISE NOTICE '🔄 开始阶段2: 列重命名...';
    
    -- 2.1 重命名 t_signal_definition.device_type_id → category_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 't_signal_definition' 
        AND column_name = 'device_type_id'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE t_signal_definition RENAME COLUMN device_type_id TO category_id;
        RAISE NOTICE '   ✅ 列 t_signal_definition.device_type_id 已重命名为 category_id';
    ELSE
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 't_signal_definition' 
            AND column_name = 'category_id'
            AND table_schema = 'public'
        ) THEN
            RAISE NOTICE '   ℹ️ 列 t_signal_definition.category_id 已存在，无需重命名';
        ELSE
            RAISE NOTICE '   ⚠️ 表 t_signal_definition 不存在或缺少相关列';
        END IF;
    END IF;
    
    -- 2.2 重命名 t_asset.device_type_id → category_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 't_asset' 
        AND column_name = 'device_type_id'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE t_asset RENAME COLUMN device_type_id TO category_id;
        RAISE NOTICE '   ✅ 列 t_asset.device_type_id 已重命名为 category_id';
    ELSE
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 't_asset' 
            AND column_name = 'category_id'
            AND table_schema = 'public'
        ) THEN
            RAISE NOTICE '   ℹ️ 列 t_asset.category_id 已存在，无需重命名';
        ELSE
            RAISE NOTICE '   ⚠️ 表 t_asset 不存在或缺少相关列';
        END IF;
    END IF;
    
    -- 2.3 重命名 t_ai_model.device_type_id → category_id (如果存在)
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 't_ai_model' 
        AND column_name = 'device_type_id'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE t_ai_model RENAME COLUMN device_type_id TO category_id;
        RAISE NOTICE '   ✅ 列 t_ai_model.device_type_id 已重命名为 category_id';
    ELSE
        RAISE NOTICE '   ℹ️ 列 t_ai_model.device_type_id 不存在，无需重命名';
    END IF;
    
    -- 2.4 重命名 t_feature_definition.device_type_id → category_id (如果存在)
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 't_feature_definition' 
        AND column_name = 'device_type_id'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE t_feature_definition RENAME COLUMN device_type_id TO category_id;
        RAISE NOTICE '   ✅ 列 t_feature_definition.device_type_id 已重命名为 category_id';
    ELSE
        RAISE NOTICE '   ℹ️ 列 t_feature_definition.device_type_id 不存在，无需重命名';
    END IF;
    
    -- 2.5 重命名 t_feature_view.device_type_id → category_id (如果存在)
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 't_feature_view' 
        AND column_name = 'device_type_id'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE t_feature_view RENAME COLUMN device_type_id TO category_id;
        RAISE NOTICE '   ✅ 列 t_feature_view.device_type_id 已重命名为 category_id';
    ELSE
        RAISE NOTICE '   ℹ️ 列 t_feature_view.device_type_id 不存在，无需重命名';
    END IF;
    
    -- 2.6 重命名 t_schema_version.device_type_id → category_id (如果存在)
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 't_schema_version' 
        AND column_name = 'device_type_id'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE t_schema_version RENAME COLUMN device_type_id TO category_id;
        RAISE NOTICE '   ✅ 列 t_schema_version.device_type_id 已重命名为 category_id';
    ELSE
        RAISE NOTICE '   ℹ️ 列 t_schema_version.device_type_id 不存在，无需重命名';
    END IF;
    
    -- 2.7 重命名 t_decision_rules.device_type_id → category_id (如果存在)
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 't_decision_rules' 
        AND column_name = 'device_type_id'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE t_decision_rules RENAME COLUMN device_type_id TO category_id;
        RAISE NOTICE '   ✅ 列 t_decision_rules.device_type_id 已重命名为 category_id';
    ELSE
        RAISE NOTICE '   ℹ️ 列 t_decision_rules.device_type_id 不存在，无需重命名';
    END IF;
    
    -- 2.8 重命名 t_data_sources.device_type_id → category_id (如果存在)
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 't_data_sources' 
        AND column_name = 'device_type_id'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE t_data_sources RENAME COLUMN device_type_id TO category_id;
        RAISE NOTICE '   ✅ 列 t_data_sources.device_type_id 已重命名为 category_id';
    ELSE
        RAISE NOTICE '   ℹ️ 列 t_data_sources.device_type_id 不存在，无需重命名';
    END IF;
    
    -- 2.9 重命名 t_dual_write_config.device_type_id → category_id (如果存在)
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 't_dual_write_config' 
        AND column_name = 'device_type_id'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE t_dual_write_config RENAME COLUMN device_type_id TO category_id;
        RAISE NOTICE '   ✅ 列 t_dual_write_config.device_type_id 已重命名为 category_id';
    ELSE
        RAISE NOTICE '   ℹ️ 列 t_dual_write_config.device_type_id 不存在，无需重命名';
    END IF;
    
    end_time := clock_timestamp();
    duration_ms := EXTRACT(MILLISECONDS FROM (end_time - start_time))::INT;
    
    -- 记录迁移版本
    INSERT INTO t_migration_versions (version, description, script_name, execution_duration_ms, rollback_script)
    VALUES ('V3.0-002', '列重命名: device_type_id → category_id', 'v3_schema_rename.sql', duration_ms, 'v3_schema_rollback.sql')
    ON CONFLICT (version) DO UPDATE SET execution_status = 'success', executed_at = NOW();
    
    RAISE NOTICE '✅ 阶段2完成: 列重命名 (耗时: % ms)', duration_ms;
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '❌ 阶段2失败: %', SQLERRM;
    INSERT INTO t_migration_versions (version, description, script_name, execution_status)
    VALUES ('V3.0-002', '列重命名失败: ' || SQLERRM, 'v3_schema_rename.sql', 'failed')
    ON CONFLICT (version) DO UPDATE SET execution_status = 'failed', executed_at = NOW();
    RAISE;
END $;


-- =====================================================
-- 阶段3: 外键约束更新
-- =====================================================

DO $
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    duration_ms INT;
    constraint_rec RECORD;
BEGIN
    start_time := clock_timestamp();
    
    -- 检查是否已执行过此迁移
    IF EXISTS (SELECT 1 FROM t_migration_versions WHERE version = 'V3.0-003' AND execution_status = 'success') THEN
        RAISE NOTICE '⏭️ 迁移 V3.0-003 已执行，跳过外键约束更新';
        RETURN;
    END IF;
    
    RAISE NOTICE '🔄 开始阶段3: 外键约束更新...';
    
    -- 3.1 查找并更新引用旧表名的外键约束
    -- 注意: PostgreSQL在表重命名时会自动更新外键引用，但约束名称可能需要更新
    
    -- 查找包含 'device' 的外键约束名称
    FOR constraint_rec IN 
        SELECT 
            tc.constraint_name,
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = 'public'
        AND (tc.constraint_name LIKE '%device%' OR tc.constraint_name LIKE '%field%')
    LOOP
        RAISE NOTICE '   ℹ️ 发现旧命名外键约束: % (表: %, 列: %)', 
            constraint_rec.constraint_name, 
            constraint_rec.table_name, 
            constraint_rec.column_name;
        -- 注意: 重命名外键约束需要先删除再创建，这里只记录，不自动修改
        -- 因为这可能会影响数据完整性
    END LOOP;
    
    -- 3.2 确保新表之间的外键关系正确
    -- t_signal_definition.category_id → t_asset_category.id
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_signal_definition' AND table_schema = 'public') THEN
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_asset_category' AND table_schema = 'public') THEN
            -- 检查外键是否存在
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = 't_signal_definition'
                AND tc.constraint_type = 'FOREIGN KEY'
                AND kcu.column_name = 'category_id'
            ) THEN
                -- 添加外键约束
                BEGIN
                    ALTER TABLE t_signal_definition 
                    ADD CONSTRAINT fk_signal_definition_category 
                    FOREIGN KEY (category_id) REFERENCES t_asset_category(id) ON DELETE CASCADE;
                    RAISE NOTICE '   ✅ 添加外键约束: fk_signal_definition_category';
                EXCEPTION WHEN OTHERS THEN
                    RAISE NOTICE '   ⚠️ 添加外键约束失败 (可能已存在): %', SQLERRM;
                END;
            ELSE
                RAISE NOTICE '   ℹ️ 外键约束 t_signal_definition.category_id 已存在';
            END IF;
        END IF;
    END IF;
    
    -- t_asset.category_id → t_asset_category.id
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_asset' AND table_schema = 'public') THEN
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_asset_category' AND table_schema = 'public') THEN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = 't_asset'
                AND tc.constraint_type = 'FOREIGN KEY'
                AND kcu.column_name = 'category_id'
            ) THEN
                BEGIN
                    ALTER TABLE t_asset 
                    ADD CONSTRAINT fk_asset_category 
                    FOREIGN KEY (category_id) REFERENCES t_asset_category(id) ON DELETE RESTRICT;
                    RAISE NOTICE '   ✅ 添加外键约束: fk_asset_category';
                EXCEPTION WHEN OTHERS THEN
                    RAISE NOTICE '   ⚠️ 添加外键约束失败 (可能已存在): %', SQLERRM;
                END;
            ELSE
                RAISE NOTICE '   ℹ️ 外键约束 t_asset.category_id 已存在';
            END IF;
        END IF;
    END IF;
    
    end_time := clock_timestamp();
    duration_ms := EXTRACT(MILLISECONDS FROM (end_time - start_time))::INT;
    
    -- 记录迁移版本
    INSERT INTO t_migration_versions (version, description, script_name, execution_duration_ms, rollback_script)
    VALUES ('V3.0-003', '外键约束更新', 'v3_schema_rename.sql', duration_ms, 'v3_schema_rollback.sql')
    ON CONFLICT (version) DO UPDATE SET execution_status = 'success', executed_at = NOW();
    
    RAISE NOTICE '✅ 阶段3完成: 外键约束更新 (耗时: % ms)', duration_ms;
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '❌ 阶段3失败: %', SQLERRM;
    INSERT INTO t_migration_versions (version, description, script_name, execution_status)
    VALUES ('V3.0-003', '外键约束更新失败: ' || SQLERRM, 'v3_schema_rename.sql', 'failed')
    ON CONFLICT (version) DO UPDATE SET execution_status = 'failed', executed_at = NOW();
    RAISE;
END $;


-- =====================================================
-- 阶段4: 索引更新
-- =====================================================

DO $
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    duration_ms INT;
    idx_rec RECORD;
BEGIN
    start_time := clock_timestamp();
    
    -- 检查是否已执行过此迁移
    IF EXISTS (SELECT 1 FROM t_migration_versions WHERE version = 'V3.0-004' AND execution_status = 'success') THEN
        RAISE NOTICE '⏭️ 迁移 V3.0-004 已执行，跳过索引更新';
        RETURN;
    END IF;
    
    RAISE NOTICE '🔄 开始阶段4: 索引更新...';
    
    -- 4.1 查找包含旧命名的索引
    FOR idx_rec IN 
        SELECT indexname, tablename, indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND (indexname LIKE '%device%' OR indexname LIKE '%field%')
        AND indexname NOT LIKE '%signal%'
        AND indexname NOT LIKE '%asset%'
    LOOP
        RAISE NOTICE '   ℹ️ 发现旧命名索引: % (表: %)', idx_rec.indexname, idx_rec.tablename;
        -- 索引重命名需要谨慎处理，这里只记录
    END LOOP;
    
    -- 4.2 确保新表有正确的索引
    -- t_asset_category 索引
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_asset_category' AND table_schema = 'public') THEN
        CREATE INDEX IF NOT EXISTS idx_asset_category_code ON t_asset_category(code);
        CREATE INDEX IF NOT EXISTS idx_asset_category_active_industry ON t_asset_category(is_active, industry);
        RAISE NOTICE '   ✅ t_asset_category 索引已确保存在';
    END IF;
    
    -- t_signal_definition 索引
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_signal_definition' AND table_schema = 'public') THEN
        CREATE INDEX IF NOT EXISTS idx_signal_definition_category ON t_signal_definition(category_id, sort_order);
        CREATE INDEX IF NOT EXISTS idx_signal_definition_realtime ON t_signal_definition(is_realtime);
        CREATE INDEX IF NOT EXISTS idx_signal_definition_feature ON t_signal_definition(is_feature);
        CREATE INDEX IF NOT EXISTS idx_signal_definition_active ON t_signal_definition(is_active);
        RAISE NOTICE '   ✅ t_signal_definition 索引已确保存在';
    END IF;
    
    -- t_asset 索引
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_asset' AND table_schema = 'public') THEN
        CREATE INDEX IF NOT EXISTS idx_asset_code ON t_asset(code);
        CREATE INDEX IF NOT EXISTS idx_asset_name ON t_asset(name);
        CREATE INDEX IF NOT EXISTS idx_asset_category_status ON t_asset(category_id, status);
        CREATE INDEX IF NOT EXISTS idx_asset_location ON t_asset(location);
        CREATE INDEX IF NOT EXISTS idx_asset_status ON t_asset(status);
        CREATE INDEX IF NOT EXISTS idx_asset_active ON t_asset(is_active);
        RAISE NOTICE '   ✅ t_asset 索引已确保存在';
    END IF;
    
    end_time := clock_timestamp();
    duration_ms := EXTRACT(MILLISECONDS FROM (end_time - start_time))::INT;
    
    -- 记录迁移版本
    INSERT INTO t_migration_versions (version, description, script_name, execution_duration_ms, rollback_script)
    VALUES ('V3.0-004', '索引更新', 'v3_schema_rename.sql', duration_ms, 'v3_schema_rollback.sql')
    ON CONFLICT (version) DO UPDATE SET execution_status = 'success', executed_at = NOW();
    
    RAISE NOTICE '✅ 阶段4完成: 索引更新 (耗时: % ms)', duration_ms;
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '❌ 阶段4失败: %', SQLERRM;
    INSERT INTO t_migration_versions (version, description, script_name, execution_status)
    VALUES ('V3.0-004', '索引更新失败: ' || SQLERRM, 'v3_schema_rename.sql', 'failed')
    ON CONFLICT (version) DO UPDATE SET execution_status = 'failed', executed_at = NOW();
    RAISE;
END $;


-- =====================================================
-- 阶段5: 记录迁移完成
-- =====================================================

DO $
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    duration_ms INT;
BEGIN
    start_time := clock_timestamp();
    
    -- 检查是否已执行过此迁移
    IF EXISTS (SELECT 1 FROM t_migration_versions WHERE version = 'V3.0' AND execution_status = 'success') THEN
        RAISE NOTICE '⏭️ V3.0 迁移已完成';
        RETURN;
    END IF;
    
    RAISE NOTICE '🔄 开始阶段5: 记录迁移完成...';
    
    -- 记录迁移到 t_migration_record 表
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_migration_record' AND table_schema = 'public') THEN
        INSERT INTO t_migration_record (
            migration_name,
            migration_type,
            source_table,
            target_table,
            status,
            started_at,
            completed_at,
            created_at,
            updated_at
        ) VALUES (
            'v3_schema_rename',
            'schema_rename',
            'device_types, device_fields, device_info',
            't_asset_category, t_signal_definition, t_asset',
            'completed',
            NOW(),
            NOW(),
            NOW(),
            NOW()
        );
        RAISE NOTICE '   ✅ 迁移记录已添加到 t_migration_record';
    END IF;
    
    end_time := clock_timestamp();
    duration_ms := EXTRACT(MILLISECONDS FROM (end_time - start_time))::INT;
    
    -- 记录V3.0整体完成
    INSERT INTO t_migration_versions (version, description, script_name, execution_duration_ms, rollback_script)
    VALUES ('V3.0', '工业AI数据平台V3 Schema重命名完成', 'v3_schema_rename.sql', duration_ms, 'v3_schema_rollback.sql')
    ON CONFLICT (version) DO UPDATE SET execution_status = 'success', executed_at = NOW();
    
    RAISE NOTICE '✅ V3.0 Schema重命名迁移全部完成';
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '❌ 阶段5失败: %', SQLERRM;
    INSERT INTO t_migration_versions (version, description, script_name, execution_status)
    VALUES ('V3.0', 'V3迁移完成记录失败: ' || SQLERRM, 'v3_schema_rename.sql', 'failed')
    ON CONFLICT (version) DO UPDATE SET execution_status = 'failed', executed_at = NOW();
    RAISE;
END $;

-- =====================================================
-- 显示迁移状态
-- =====================================================

SELECT 
    version, 
    description, 
    script_name, 
    executed_at, 
    execution_status,
    execution_duration_ms
FROM t_migration_versions 
WHERE version LIKE 'V3.0%'
ORDER BY executed_at;

-- =====================================================
-- 验证表结构
-- =====================================================

DO $
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '📊 V3 Schema重命名迁移验证报告';
    RAISE NOTICE '================================';
    
    -- 检查核心表
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_asset_category' AND table_schema = 'public') THEN
        RAISE NOTICE '✅ 表 t_asset_category 存在';
    ELSE
        RAISE NOTICE '❌ 表 t_asset_category 不存在';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_signal_definition' AND table_schema = 'public') THEN
        RAISE NOTICE '✅ 表 t_signal_definition 存在';
    ELSE
        RAISE NOTICE '❌ 表 t_signal_definition 不存在';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_asset' AND table_schema = 'public') THEN
        RAISE NOTICE '✅ 表 t_asset 存在';
    ELSE
        RAISE NOTICE '❌ 表 t_asset 不存在';
    END IF;
    
    -- 检查旧表是否已删除/重命名
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'device_types' AND table_schema = 'public') THEN
        RAISE NOTICE '⚠️ 旧表 device_types 仍然存在';
    ELSE
        RAISE NOTICE '✅ 旧表 device_types 已处理';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'device_fields' AND table_schema = 'public') THEN
        RAISE NOTICE '⚠️ 旧表 device_fields 仍然存在';
    ELSE
        RAISE NOTICE '✅ 旧表 device_fields 已处理';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'device_info' AND table_schema = 'public') THEN
        RAISE NOTICE '⚠️ 旧表 device_info 仍然存在';
    ELSE
        RAISE NOTICE '✅ 旧表 device_info 已处理';
    END IF;
    
    RAISE NOTICE '================================';
END $;
