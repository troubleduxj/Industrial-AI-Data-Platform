-- =====================================================
-- 工业AI数据平台 V2 升级 - 回滚脚本
-- 版本: V2.0
-- 创建时间: 2024-12-27
-- 描述: 回滚V2升级相关的数据库变更
-- =====================================================

-- ⚠️ 警告: 执行此脚本将删除V2升级创建的所有表和数据
-- 请确保在执行前已备份重要数据

-- =====================================================
-- 回滚阶段5：身份集成表
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '🔄 开始回滚阶段5: 身份集成表...';
    
    -- 删除触发器
    DROP TRIGGER IF EXISTS update_user_external_identities_updated_at ON t_user_external_identities;
    DROP TRIGGER IF EXISTS update_identity_providers_updated_at ON t_identity_providers;
    
    -- 删除表
    DROP TABLE IF EXISTS t_user_external_identities CASCADE;
    DROP TABLE IF EXISTS t_identity_providers CASCADE;
    
    -- 更新迁移版本状态
    UPDATE t_migration_versions SET execution_status = 'rolled_back' WHERE version = '005';
    
    RAISE NOTICE '✅ 阶段5回滚完成: 身份集成表已删除';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '⚠️ 阶段5回滚警告: %', SQLERRM;
END $$;


-- =====================================================
-- 回滚阶段4：数据采集层表
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '🔄 开始回滚阶段4: 数据采集层表...';
    
    -- 删除触发器
    DROP TRIGGER IF EXISTS trigger_dual_write_config_updated_at ON t_dual_write_config;
    DROP TRIGGER IF EXISTS trigger_data_sources_updated_at ON t_data_sources;
    
    -- 删除函数
    DROP FUNCTION IF EXISTS update_dual_write_config_updated_at();
    DROP FUNCTION IF EXISTS update_data_sources_updated_at();
    
    -- 删除表
    DROP TABLE IF EXISTS t_adapter_templates CASCADE;
    DROP TABLE IF EXISTS t_ingestion_statistics CASCADE;
    DROP TABLE IF EXISTS t_ingestion_error_logs CASCADE;
    DROP TABLE IF EXISTS t_dual_write_config CASCADE;
    DROP TABLE IF EXISTS t_data_sources CASCADE;
    
    -- 更新迁移版本状态
    UPDATE t_migration_versions SET execution_status = 'rolled_back' WHERE version = '004a';
    
    RAISE NOTICE '✅ 阶段4回滚完成: 数据采集层表已删除';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '⚠️ 阶段4回滚警告: %', SQLERRM;
END $$;


-- =====================================================
-- 回滚阶段3：决策引擎表
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '🔄 开始回滚阶段3: 决策引擎表...';
    
    -- 删除表
    DROP TABLE IF EXISTS t_decision_audit_logs CASCADE;
    DROP TABLE IF EXISTS t_decision_rules CASCADE;
    
    -- 更新迁移版本状态
    UPDATE t_migration_versions SET execution_status = 'rolled_back' WHERE version = '003';
    
    RAISE NOTICE '✅ 阶段3回滚完成: 决策引擎表已删除';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '⚠️ 阶段3回滚警告: %', SQLERRM;
END $$;


-- =====================================================
-- 回滚阶段1：平台核心表
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '🔄 开始回滚阶段1: 平台核心表...';
    
    -- 删除表（按依赖顺序）
    DROP TABLE IF EXISTS t_migration_record CASCADE;
    DROP TABLE IF EXISTS t_schema_version CASCADE;
    DROP TABLE IF EXISTS t_feature_view CASCADE;
    DROP TABLE IF EXISTS t_feature_definition CASCADE;
    DROP TABLE IF EXISTS t_ai_prediction CASCADE;
    DROP TABLE IF EXISTS t_ai_model_version CASCADE;
    DROP TABLE IF EXISTS t_ai_model CASCADE;
    DROP TABLE IF EXISTS t_asset CASCADE;
    DROP TABLE IF EXISTS t_signal_definition CASCADE;
    DROP TABLE IF EXISTS t_asset_category CASCADE;
    
    -- 更新迁移版本状态
    UPDATE t_migration_versions SET execution_status = 'rolled_back' WHERE version = '001';
    
    RAISE NOTICE '✅ 阶段1回滚完成: 平台核心表已删除';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '⚠️ 阶段1回滚警告: %', SQLERRM;
END $$;


-- =====================================================
-- 更新V2整体状态
-- =====================================================

DO $$
BEGIN
    UPDATE t_migration_versions SET execution_status = 'rolled_back' WHERE version = 'V2.0';
    RAISE NOTICE '✅ V2 回滚完成';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '⚠️ 更新V2状态警告: %', SQLERRM;
END $$;


-- =====================================================
-- 显示回滚后状态
-- =====================================================

SELECT version, description, execution_status, executed_at 
FROM t_migration_versions 
ORDER BY executed_at;
