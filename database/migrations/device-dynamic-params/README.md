# 设备监测字段配置迁移

## 📋 说明

本目录包含设备类型动态参数展示功能的数据库配置脚本。

## 📁 文件说明

- `001_configure_monitoring_fields.sql` - SQL 迁移脚本
- `apply_monitoring_fields.py` - Python 执行脚本
- `README.md` - 本文件

## 🎯 配置内容

### TASK-11: 焊机监测字段

配置焊机（`welding`）的 4 个监测关键字段：

1. **预设电流** (`preset_current`)
   - 类型: float
   - 单位: A
   - 图标: ⚡
   - 颜色: #1890ff

2. **预设电压** (`preset_voltage`)
   - 类型: float
   - 单位: V
   - 图标: 🔌
   - 颜色: #52c41a

3. **焊接电流** (`welding_current`)
   - 类型: float
   - 单位: A
   - 图标: ⚡
   - 颜色: #fa8c16

4. **焊接电压** (`welding_voltage`)
   - 类型: float
   - 单位: V
   - 图标: 🔌
   - 颜色: #faad14

### TASK-12: 压力传感器监测字段

配置压力传感器（`PRESSURE_SENSOR_V1`）的 4 个监测关键字段：

1. **压力值** (`pressure`)
   - 类型: float
   - 单位: MPa
   - 图标: 📊
   - 颜色: #1890ff

2. **温度** (`temperature`)
   - 类型: float
   - 单位: °C
   - 图标: 🌡️
   - 颜色: #ff4d4f

3. **振动值** (`vibration`)
   - 类型: float
   - 单位: mm/s
   - 图标: 📳
   - 颜色: #faad14

4. **设备状态** (`status`)
   - 类型: string
   - 单位: 无
   - 说明: online/offline/error/maintenance

## 🚀 使用方法

### 方式 1: 使用 Python 脚本（推荐）

```bash
# 在项目根目录执行
python database/migrations/device-dynamic-params/apply_monitoring_fields.py
```

### 方式 2: 直接执行 SQL

```bash
# 使用 psql 命令行工具
psql -U postgres -d devicemonitor -f database/migrations/device-dynamic-params/001_configure_monitoring_fields.sql

# 或使用其他数据库客户端工具（如 DBeaver、pgAdmin）
# 打开 001_configure_monitoring_fields.sql 文件并执行
```

## ✅ 验证配置

### 查询焊机监测字段

```sql
SELECT 
    field_name,
    field_code,
    field_type,
    unit,
    sort_order,
    display_config
FROM t_device_field
WHERE device_type_code = 'welding' 
  AND is_monitoring_key = true
  AND is_active = true
ORDER BY sort_order;
```

### 查询压力传感器监测字段

```sql
SELECT 
    field_name,
    field_code,
    field_type,
    unit,
    sort_order,
    display_config
FROM t_device_field
WHERE device_type_code = 'PRESSURE_SENSOR_V1' 
  AND is_monitoring_key = true
  AND is_active = true
ORDER BY sort_order;
```

### 测试 API

```bash
# 测试焊机字段配置
curl http://localhost:8001/api/v2/device-fields/monitoring-keys/welding

# 测试压力传感器字段配置
curl http://localhost:8001/api/v2/device-fields/monitoring-keys/PRESSURE_SENSOR_V1
```

## 📝 注意事项

1. **幂等性**: SQL 脚本使用 `INSERT ... WHERE NOT EXISTS` 和 `UPDATE` 语句，可以安全地重复执行
2. **数据库连接**: 确保数据库连接配置正确（`app/settings/config.py`）
3. **权限**: 确保数据库用户有 INSERT 和 UPDATE 权限
4. **备份**: 建议在执行前备份数据库

## 🔄 回滚

如果需要回滚配置，可以执行以下 SQL：

```sql
-- 取消焊机字段的监测标记
UPDATE t_device_field 
SET is_monitoring_key = false
WHERE device_type_code = 'welding' 
  AND field_code IN ('preset_current', 'preset_voltage', 'welding_current', 'welding_voltage');

-- 删除压力传感器字段（如果是新创建的）
DELETE FROM t_device_field 
WHERE device_type_code = 'PRESSURE_SENSOR_V1';

-- 删除压力传感器设备类型（如果是新创建的）
DELETE FROM t_device_type 
WHERE type_code = 'PRESSURE_SENSOR_V1';
```

## 📚 相关文档

- [设备类型动态参数展示方案](../../../docs/device_test/设备类型动态参数展示方案.md)
- [Spec 实施进度](../../../.kiro/specs/device-dynamic-params/IMPLEMENTATION_PROGRESS.md)
- [MVP 完成报告](../../../.kiro/specs/device-dynamic-params/MVP_COMPLETED.md)
