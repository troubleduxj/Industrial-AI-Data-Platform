-- ========================================
-- 维修记录相关数据字典
-- ========================================
-- 高优先级字段：故障原因、损坏类别、设备类别、品牌
-- 创建时间：2025-11-25
-- ========================================

BEGIN;

-- =====================================================
-- 1. 设备类别字典 (repair_device_category)
-- =====================================================

INSERT INTO t_sys_dict_type (
    type_code,
    type_name,
    description,
    created_at,
    updated_at
)
VALUES (
    'repair_device_category',
    '维修设备类别',
    '维修记录中的设备类别选项，如焊机类型等',
    NOW(),
    NOW()
)
ON CONFLICT (type_code) DO UPDATE SET
    type_name = EXCLUDED.type_name,
    description = EXCLUDED.description,
    updated_at = NOW();

DO $$
DECLARE
    v_dict_type_id BIGINT;
BEGIN
    SELECT id INTO v_dict_type_id
    FROM t_sys_dict_type
    WHERE type_code = 'repair_device_category';
    
    DELETE FROM t_sys_dict_data WHERE dict_type_id = v_dict_type_id;
    
    INSERT INTO t_sys_dict_data (
        dict_type_id, data_label, data_value, sort_order, is_enabled, description, created_at, updated_at
    )
    VALUES
    (v_dict_type_id, '二氧化碳保护焊机', '二氧化碳保护焊机', 1, true, 'CO2气体保护焊机', NOW(), NOW()),
    (v_dict_type_id, '氩弧焊机', '氩弧焊机', 2, true, 'TIG/氩弧焊机', NOW(), NOW()),
    (v_dict_type_id, '电焊机', '电焊机', 3, true, '手工电弧焊机', NOW(), NOW()),
    (v_dict_type_id, '等离子切割机', '等离子切割机', 4, true, '等离子切割设备', NOW(), NOW()),
    (v_dict_type_id, '埋弧焊机', '埋弧焊机', 5, true, '埋弧自动焊机', NOW(), NOW()),
    (v_dict_type_id, '点焊机', '点焊机', 6, true, '电阻点焊机', NOW(), NOW()),
    (v_dict_type_id, '激光焊机', '激光焊机', 7, true, '激光焊接设备', NOW(), NOW());
    
    RAISE NOTICE '✓ 设备类别字典创建完成';
END $$;

-- =====================================================
-- 2. 设备品牌字典 (device_brand)
-- =====================================================

INSERT INTO t_sys_dict_type (
    type_code,
    type_name,
    description,
    created_at,
    updated_at
)
VALUES (
    'device_brand',
    '设备品牌',
    '设备品牌选项，包含国内外主流焊机品牌',
    NOW(),
    NOW()
)
ON CONFLICT (type_code) DO UPDATE SET
    type_name = EXCLUDED.type_name,
    description = EXCLUDED.description,
    updated_at = NOW();

DO $$
DECLARE
    v_dict_type_id BIGINT;
BEGIN
    SELECT id INTO v_dict_type_id
    FROM t_sys_dict_type
    WHERE type_code = 'device_brand';
    
    DELETE FROM t_sys_dict_data WHERE dict_type_id = v_dict_type_id;
    
    INSERT INTO t_sys_dict_data (
        dict_type_id, data_label, data_value, sort_order, is_enabled, description, created_at, updated_at
    )
    VALUES
    -- 国际品牌
    (v_dict_type_id, '松下', '松下', 1, true, 'Panasonic 日本品牌', NOW(), NOW()),
    (v_dict_type_id, '林肯', '林肯', 2, true, 'Lincoln Electric 美国品牌', NOW(), NOW()),
    (v_dict_type_id, '米勒', '米勒', 3, true, 'Miller 美国品牌', NOW(), NOW()),
    (v_dict_type_id, '伊萨', '伊萨', 4, true, 'ESAB 瑞典品牌', NOW(), NOW()),
    (v_dict_type_id, '福尼斯', '福尼斯', 5, true, 'Fronius 奥地利品牌', NOW(), NOW()),
    (v_dict_type_id, 'OTC', 'OTC', 6, true, 'OTC/大阪变压器 日本品牌', NOW(), NOW()),
    -- 国产品牌
    (v_dict_type_id, '奥太', '奥太', 10, true, '山东奥太电气', NOW(), NOW()),
    (v_dict_type_id, '瑞凌', '瑞凌', 11, true, '深圳瑞凌实业', NOW(), NOW()),
    (v_dict_type_id, '佳士', '佳士', 12, true, '深圳佳士科技', NOW(), NOW()),
    (v_dict_type_id, '时代', '时代', 13, true, '北京时代科技', NOW(), NOW()),
    (v_dict_type_id, '凯尔达', '凯尔达', 14, true, '杭州凯尔达', NOW(), NOW()),
    (v_dict_type_id, '华意隆', '华意隆', 15, true, '深圳华意隆', NOW(), NOW()),
    (v_dict_type_id, '其他', '其他', 99, true, '其他品牌', NOW(), NOW());
    
    RAISE NOTICE '✓ 设备品牌字典创建完成';
END $$;

-- =====================================================
-- 3. 故障原因字典 (repair_fault_reason)
-- =====================================================

INSERT INTO t_sys_dict_type (
    type_code,
    type_name,
    description,
    created_at,
    updated_at
)
VALUES (
    'repair_fault_reason',
    '故障原因',
    '维修记录中的故障原因分类',
    NOW(),
    NOW()
)
ON CONFLICT (type_code) DO UPDATE SET
    type_name = EXCLUDED.type_name,
    description = EXCLUDED.description,
    updated_at = NOW();

DO $$
DECLARE
    v_dict_type_id BIGINT;
BEGIN
    SELECT id INTO v_dict_type_id
    FROM t_sys_dict_type
    WHERE type_code = 'repair_fault_reason';
    
    DELETE FROM t_sys_dict_data WHERE dict_type_id = v_dict_type_id;
    
    INSERT INTO t_sys_dict_data (
        dict_type_id, data_label, data_value, sort_order, is_enabled, description, created_at, updated_at
    )
    VALUES
    (v_dict_type_id, '操作不当', '操作不当', 1, true, '人员操作失误导致的故障', NOW(), NOW()),
    (v_dict_type_id, '老化磨损', '老化磨损', 2, true, '设备长期使用导致的自然磨损', NOW(), NOW()),
    (v_dict_type_id, '环境因素', '环境因素', 3, true, '温度、湿度、灰尘等环境因素', NOW(), NOW()),
    (v_dict_type_id, '设备缺陷', '设备缺陷', 4, true, '设备本身设计或制造缺陷', NOW(), NOW()),
    (v_dict_type_id, '维护不当', '维护不当', 5, true, '日常维护保养不到位', NOW(), NOW()),
    (v_dict_type_id, '电源问题', '电源问题', 6, true, '电压不稳、电源故障等', NOW(), NOW()),
    (v_dict_type_id, '过载使用', '过载使用', 7, true, '超负荷运行导致的故障', NOW(), NOW()),
    (v_dict_type_id, '配件损坏', '配件损坏', 8, true, '易损件或配件损坏', NOW(), NOW()),
    (v_dict_type_id, '外力损坏', '外力损坏', 9, true, '碰撞、跌落等外力造成', NOW(), NOW()),
    (v_dict_type_id, '其他原因', '其他原因', 99, true, '其他未分类原因', NOW(), NOW());
    
    RAISE NOTICE '✓ 故障原因字典创建完成';
END $$;

-- =====================================================
-- 4. 损坏类别字典 (repair_damage_category)
-- =====================================================

INSERT INTO t_sys_dict_type (
    type_code,
    type_name,
    description,
    created_at,
    updated_at
)
VALUES (
    'repair_damage_category',
    '损坏类别',
    '维修记录中的损坏类别分类，用于责任判定',
    NOW(),
    NOW()
)
ON CONFLICT (type_code) DO UPDATE SET
    type_name = EXCLUDED.type_name,
    description = EXCLUDED.description,
    updated_at = NOW();

DO $$
DECLARE
    v_dict_type_id BIGINT;
BEGIN
    SELECT id INTO v_dict_type_id
    FROM t_sys_dict_type
    WHERE type_code = 'repair_damage_category';
    
    DELETE FROM t_sys_dict_data WHERE dict_type_id = v_dict_type_id;
    
    INSERT INTO t_sys_dict_data (
        dict_type_id, data_label, data_value, sort_order, is_enabled, description, created_at, updated_at
    )
    VALUES
    (v_dict_type_id, '正常损坏', '正常损坏', 1, true, '正常使用过程中的自然损耗', NOW(), NOW()),
    (v_dict_type_id, '非正常损坏', '非正常损坏', 2, true, '非正常使用导致的损坏', NOW(), NOW()),
    (v_dict_type_id, '人为损坏', '人为损坏', 3, true, '人为因素造成的损坏，需追责', NOW(), NOW()),
    (v_dict_type_id, '意外损坏', '意外损坏', 4, true, '不可预见的意外事故造成', NOW(), NOW()),
    (v_dict_type_id, '质量问题', '质量问题', 5, true, '产品质量问题导致的损坏', NOW(), NOW());
    
    RAISE NOTICE '✓ 损坏类别字典创建完成';
END $$;

COMMIT;

-- =====================================================
-- 验证创建结果
-- =====================================================

SELECT '✅ 维修记录字典数据创建完成！' as 状态;

-- 显示所有创建的字典类型
SELECT 
    type_code as 字典代码,
    type_name as 字典名称,
    description as 说明
FROM t_sys_dict_type
WHERE type_code IN ('repair_device_category', 'device_brand', 'repair_fault_reason', 'repair_damage_category')
ORDER BY type_code;

-- 显示各字典的数据项数量
SELECT 
    dt.type_name as 字典名称,
    COUNT(dd.id) as 数据项数量
FROM t_sys_dict_type dt
LEFT JOIN t_sys_dict_data dd ON dt.id = dd.dict_type_id
WHERE dt.type_code IN ('repair_device_category', 'device_brand', 'repair_fault_reason', 'repair_damage_category')
GROUP BY dt.type_name
ORDER BY dt.type_name;
