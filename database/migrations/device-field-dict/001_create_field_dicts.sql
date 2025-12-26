-- ========================================
-- 创建设备字段相关的数据字典
-- ========================================
-- 包含：字段分组、字段分类
-- 创建时间：2025-11-25
-- ========================================

BEGIN;

-- =====================================================
-- 1. 创建字段分组字典类型
-- =====================================================

INSERT INTO t_sys_dict_type (
    type_code,
    type_name,
    description,
    created_at,
    updated_at
)
VALUES (
    'device_field_group',
    '设备字段分组',
    '设备字段的分组类型配置，用于前端分组展示',
    NOW(),
    NOW()
)
ON CONFLICT (type_code) DO UPDATE SET
    type_name = EXCLUDED.type_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- 插入字段分组数据
DO $$
DECLARE
    v_dict_type_id BIGINT;
BEGIN
    -- 获取字典类型ID
    SELECT id INTO v_dict_type_id
    FROM t_sys_dict_type
    WHERE type_code = 'device_field_group';
    
    -- 插入字段分组选项（先删除再插入）
    DELETE FROM t_sys_dict_data WHERE dict_type_id = v_dict_type_id;
    
    INSERT INTO t_sys_dict_data (
        dict_type_id,
        data_label,
        data_value,
        sort_order,
        is_enabled,
        description,
        created_at,
        updated_at
    )
    VALUES
    (v_dict_type_id, '📊 核心参数', 'core', 1, true, '最重要的核心参数，默认显示', NOW(), NOW()),
    (v_dict_type_id, '🌡️ 温度参数', 'temperature', 2, true, '温度相关参数', NOW(), NOW()),
    (v_dict_type_id, '⚡ 功率参数', 'power', 3, true, '功率、电流相关参数', NOW(), NOW()),
    (v_dict_type_id, '⚙️ 速度参数', 'speed', 4, true, '速度、转速相关参数', NOW(), NOW()),
    (v_dict_type_id, '📏 尺寸参数', 'dimension', 5, true, '尺寸、宽度相关参数', NOW(), NOW()),
    (v_dict_type_id, '💧 压力参数', 'pressure', 6, true, '压力、流体相关参数', NOW(), NOW()),
    (v_dict_type_id, '📋 其他参数', 'other', 98, true, '未分类参数', NOW(), NOW()),
    (v_dict_type_id, '默认分组', 'default', 99, true, '默认分组', NOW(), NOW());
    
    RAISE NOTICE '✓ 字段分组字典数据创建完成';
END $$;

-- =====================================================
-- 2. 创建字段分类字典类型
-- =====================================================

INSERT INTO t_sys_dict_type (
    type_code,
    type_name,
    description,
    created_at,
    updated_at
)
VALUES (
    'device_field_category',
    '设备字段分类',
    '设备字段的业务分类配置',
    NOW(),
    NOW()
)
ON CONFLICT (type_code) DO UPDATE SET
    type_name = EXCLUDED.type_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- 插入字段分类数据
DO $$
DECLARE
    v_dict_type_id BIGINT;
BEGIN
    -- 获取字典类型ID
    SELECT id INTO v_dict_type_id
    FROM t_sys_dict_type
    WHERE type_code = 'device_field_category';
    
    -- 插入字段分类选项（先删除再插入）
    DELETE FROM t_sys_dict_data WHERE dict_type_id = v_dict_type_id;
    
    INSERT INTO t_sys_dict_data (
        dict_type_id,
        data_label,
        data_value,
        sort_order,
        is_enabled,
        description,
        created_at,
        updated_at
    )
    VALUES
    (v_dict_type_id, '数据采集', 'data_collection', 1, true, '从设备采集的数据字段', NOW(), NOW()),
    (v_dict_type_id, '控制参数', 'control', 2, true, '用于控制设备的参数', NOW(), NOW()),
    (v_dict_type_id, '状态信息', 'status', 3, true, '设备状态相关信息', NOW(), NOW()),
    (v_dict_type_id, '其他', 'other', 99, true, '其他类型字段', NOW(), NOW());
    
    RAISE NOTICE '✓ 字段分类字典数据创建完成';
END $$;

COMMIT;

-- =====================================================
-- 3. 验证创建结果
-- =====================================================

SELECT '✅ 数据字典创建完成！' as 状态;

-- 显示字段分组字典
SELECT 
    '字段分组' as 字典类型,
    dd.data_label as 标签,
    dd.data_value as 值,
    dd.sort_order as 排序,
    dd.is_enabled as 启用状态,
    dd.description as 说明
FROM t_sys_dict_data dd
INNER JOIN t_sys_dict_type dt ON dd.dict_type_id = dt.id
WHERE dt.type_code = 'device_field_group'
ORDER BY dd.sort_order;

-- 显示字段分类字典
SELECT 
    '字段分类' as 字典类型,
    dd.data_label as 标签,
    dd.data_value as 值,
    dd.sort_order as 排序,
    dd.is_enabled as 启用状态,
    dd.description as 说明
FROM t_sys_dict_data dd
INNER JOIN t_sys_dict_type dt ON dd.dict_type_id = dt.id
WHERE dt.type_code = 'device_field_category'
ORDER BY dd.sort_order;
