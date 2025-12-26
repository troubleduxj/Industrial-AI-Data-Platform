# 设备字段数据字典配置

## 📋 概述

将设备字段的分组和分类配置从硬编码改为数据字典方式，支持通过界面动态管理。

## 🎯 包含的字典

### 1. 字段分组 (device_field_group)

用于前端分组展示设备字段。

| 标签 | 值 | 排序 | 说明 |
|-----|---|------|------|
| 📊 核心参数 | core | 1 | 最重要的核心参数 |
| 🌡️ 温度参数 | temperature | 2 | 温度相关参数 |
| ⚡ 功率参数 | power | 3 | 功率、电流相关参数 |
| ⚙️ 速度参数 | speed | 4 | 速度、转速相关参数 |
| 📏 尺寸参数 | dimension | 5 | 尺寸、宽度相关参数 |
| 💧 压力参数 | pressure | 6 | 压力、流体相关参数 |
| 📋 其他参数 | other | 98 | 未分类参数 |
| 默认分组 | default | 99 | 默认分组 |

### 2. 字段分类 (device_field_category)

用于业务逻辑分类。

| 标签 | 值 | 排序 | 说明 |
|-----|---|------|------|
| 数据采集 | data_collection | 1 | 从设备采集的数据字段 |
| 控制参数 | control | 2 | 用于控制设备的参数 |
| 状态信息 | status | 3 | 设备状态相关信息 |
| 其他 | other | 99 | 其他类型字段 |

## 🚀 执行步骤

### 方法1: 使用Python脚本（推荐）

```bash
# 1. 进入迁移目录
cd database/migrations/device-field-dict

# 2. 执行脚本
python apply_field_dicts.py
```

### 方法2: 直接执行SQL

```bash
# 使用psql
psql -h 127.0.0.1 -U postgres -d devicemonitor -f 001_create_field_dicts.sql

# 或使用其他数据库工具
```

## 📊 验证结果

执行成功后会显示：

```
✅ 数据字典创建完成！

字段分组:
  📊 核心参数 (core)
  🌡️ 温度参数 (temperature)
  ...

字段分类:
  数据采集 (data_collection)
  控制参数 (control)
  ...
```

## 🔧 管理数据字典

### 通过界面管理

1. 登录系统
2. 访问 **系统管理 → 数据字典**
3. 找到对应的字典类型：
   - **设备字段分组** (device_field_group)
   - **设备字段分类** (device_field_category)
4. 可以进行：
   - 添加新选项
   - 修改现有选项
   - 调整排序
   - 启用/禁用选项

### 添加新分组示例

1. 进入"设备字段分组"字典
2. 点击"新增"
3. 填写信息：
   - **数据标签**: `🔊 声音参数`
   - **数据值**: `sound`
   - **排序**: `7`
   - **启用状态**: 是
   - **说明**: 声音、噪音相关参数
4. 保存

## 📝 前端代码修改

修改后的前端代码会自动从数据字典加载选项，无需重新编译即可生效。

详见: `docs/device_test/字段分组分类-数据字典实现.md`

## ⚠️ 注意事项

1. **不要删除正在使用的选项**
   - 先检查是否有字段使用该分组/分类
   - 如需删除，先将字段改为其他分组/分类

2. **保持 data_value 的稳定性**
   - data_value 是存储在数据库中的值
   - 修改后会影响已有字段的显示
   - 建议只修改 data_label（显示标签）

3. **排序规则**
   - 数字越小越靠前
   - 建议预留间隔（如：1, 2, 3...）方便插入新选项
   - 默认/其他类选项建议排在最后（98, 99）

## 🔄 回滚

如需回滚，执行：

```sql
-- 删除字段分组字典
DELETE FROM t_sys_dict_data 
WHERE dict_type_id IN (
    SELECT id FROM t_sys_dict_type 
    WHERE type_code = 'device_field_group'
);

DELETE FROM t_sys_dict_type 
WHERE type_code = 'device_field_group';

-- 删除字段分类字典
DELETE FROM t_sys_dict_data 
WHERE dict_type_id IN (
    SELECT id FROM t_sys_dict_type 
    WHERE type_code = 'device_field_category'
);

DELETE FROM t_sys_dict_type 
WHERE type_code = 'device_field_category';
```

## 📚 相关文档

- `docs/device_test/字段分组维护指南.md` - 字段分组维护指南
- `docs/device_test/字段分组分类-数据字典实现.md` - 数据字典实现文档

---

**创建时间**: 2025-11-25  
**版本**: 1.0
