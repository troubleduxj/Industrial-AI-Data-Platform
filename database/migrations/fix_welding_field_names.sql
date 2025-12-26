-- 修复焊机设备监测参数名称显示问题
-- 将 'weld_current_weld_current' 修复为 '焊接电流'
-- 将 'weld_voltage_weld_voltage' 修复为 '焊接电压'

-- 1. 先处理可能存在的名称冲突（删除旧的/不使用的同名字段）
DELETE FROM t_device_field 
WHERE device_type_code = 'welding' 
  AND field_name = '焊接电流' 
  AND field_code != 'weld_current';

DELETE FROM t_device_field 
WHERE device_type_code = 'welding' 
  AND field_name = '焊接电压' 
  AND field_code != 'weld_voltage';

-- 2. 更新字段名称
UPDATE t_device_field 
SET field_name = '焊接电流',
    unit = 'A',
    description = '实时焊接电流',
    display_config = '{"icon": "⚡", "color": "#fa8c16"}'::jsonb
WHERE device_type_code = 'welding' 
  AND field_code = 'weld_current';

UPDATE t_device_field 
SET field_name = '焊接电压',
    unit = 'V',
    description = '实时焊接电压',
    display_config = '{"icon": "🔌", "color": "#faad14"}'::jsonb
WHERE device_type_code = 'welding' 
  AND field_code = 'weld_voltage';

-- 3. 验证更新结果
SELECT id, device_type_code, field_name, field_code, is_active 
FROM t_device_field 
WHERE device_type_code = 'welding' 
  AND field_code IN ('weld_current', 'weld_voltage');
