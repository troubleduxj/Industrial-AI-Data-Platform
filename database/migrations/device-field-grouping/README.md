# 设备字段分组功能

## 📋 功能说明

为解决设备监测字段过多导致卡片高度过大的问题，实现字段分组折叠显示功能。

**核心特性**:
- ✅ 字段分组管理（core/temperature/power/other等）
- ✅ 默认显示控制（核心字段默认显示，其他折叠）
- ✅ 分组排序（控制分组显示顺序）
- ✅ 一键展开/收起所有分组
- ✅ 美观的动画效果

---

## 🎯 实现效果

### 默认状态（卡片高度约300px）

```
┌─────────────────────────────┐
│ 🏭 EXT001 - 1号挤出机       │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ 🟢 运行中                    │
│                              │
│ 📊 核心参数 (4/11)          │
│ 🌡️ 熔体温度: 285.6 °C      │
│ 📊 熔体压力: 30.2 MPa       │
│ ⚙️ 螺杆转速: 95.5 rpm       │
│ ⚡ 电机扭矩: 68.5 %         │
│                              │
│ ▼ 🌡️ 温度参数 (5个)        │
│ ▼ 📋 其他参数 (2个)         │
│ [展开全部]                   │
│                              │
│ 📍 挤出车间-A区              │
│ [查看历史] [分析设备]        │
└─────────────────────────────┘
```

### 展开状态

```
┌─────────────────────────────┐
│ 🏭 EXT001 - 1号挤出机       │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ 🟢 运行中                    │
│                              │
│ 📊 核心参数 (4/11)          │
│ 🌡️ 熔体温度: 285.6 °C      │
│ 📊 熔体压力: 30.2 MPa       │
│ ⚙️ 螺杆转速: 95.5 rpm       │
│ ⚡ 电机扭矩: 68.5 %         │
│                              │
│ ▲ 🌡️ 温度参数 (5个)        │
│   🌡️ 1区温度: 230.5 °C    │
│   🌡️ 2区温度: 250.2 °C    │
│   🌡️ 3区温度: 270.8 °C    │
│   🌡️ 4区温度: 280.3 °C    │
│   🌡️ 5区温度: 290.1 °C    │
│                              │
│ ▲ 📋 其他参数 (2个)         │
│   ⚡ 主电机电流: 245.3 A    │
│   📦 喂料速度: 1050.0 kg/h  │
│                              │
│ [收起全部]                   │
│                              │
│ 📍 挤出车间-A区              │
│ [查看历史] [分析设备]        │
└─────────────────────────────┘
```

---

## 🚀 快速开始

### 步骤1：执行数据库迁移

```bash
# 方式1：使用psql
psql -U postgres -d devicemonitor -f database/migrations/device-field-grouping/001_add_field_grouping.sql

# 方式2：使用Python脚本
python scripts/apply_field_grouping.py
```

### 步骤2：重启后端服务

```bash
# 重启后端以加载新的Schema
python run.py
```

### 步骤3：刷新前端

```bash
# 前端会自动使用新组件
# 刷新浏览器即可看到效果
```

---

## 📊 数据库变更

### 新增字段

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| field_group | VARCHAR(50) | 'default' | 字段分组标识 |
| is_default_visible | BOOLEAN | true | 是否默认显示 |
| group_order | INT | 0 | 分组排序顺序 |

### 新增索引

```sql
-- 提升分组查询性能
CREATE INDEX idx_device_field_group 
ON t_device_field(device_type_code, field_group, is_default_visible);

CREATE INDEX idx_device_field_visible 
ON t_device_field(device_type_code, is_default_visible, sort_order);
```

---

## 🎨 字段分组配置

### 分组类型

| 分组代码 | 分组名称 | 图标 | 说明 |
|---------|---------|------|------|
| core | 核心参数 | 📊 | 最重要的参数，默认显示 |
| temperature | 温度参数 | 🌡️ | 温度相关参数 |
| power | 功率参数 | ⚡ | 功率、电流相关参数 |
| speed | 速度参数 | ⚙️ | 速度、转速相关参数 |
| dimension | 尺寸参数 | 📏 | 尺寸、宽度相关参数 |
| other | 其他参数 | 📋 | 其他未分类参数 |

### 配置原则

1. **核心字段**: 不超过4个，默认显示
2. **其他字段**: 按类型分组，默认折叠
3. **分组排序**: core(1) → temperature(2) → power(3) → other(999)

---

## 📝 配置示例

### 布鲁克纳挤出机配置

```sql
-- 核心参数（4个，默认显示）
UPDATE t_device_field 
SET field_group = 'core',
    is_default_visible = true,
    group_order = 1
WHERE device_type_code = 'BRUCKNER_EXTRUDER' 
  AND field_code IN ('melt_temperature', 'melt_pressure', 'screw_speed', 'motor_torque');

-- 温度参数（5个，默认折叠）
UPDATE t_device_field 
SET field_group = 'temperature',
    is_default_visible = false,
    group_order = 2
WHERE device_type_code = 'BRUCKNER_EXTRUDER' 
  AND field_code IN ('zone1_temp', 'zone2_temp', 'zone3_temp', 'zone4_temp', 'zone5_temp');

-- 其他参数（2个，默认折叠）
UPDATE t_device_field 
SET field_group = 'other',
    is_default_visible = false,
    group_order = 3
WHERE device_type_code = 'BRUCKNER_EXTRUDER' 
  AND field_code IN ('motor_current', 'feed_rate');
```

### 自定义设备配置

```sql
-- 为你的设备类型配置字段分组
UPDATE t_device_field 
SET field_group = 'core',           -- 分组类型
    is_default_visible = true,      -- 是否默认显示
    group_order = 1                 -- 分组排序
WHERE device_type_code = 'YOUR_DEVICE_TYPE' 
  AND field_code IN ('field1', 'field2', 'field3', 'field4');
```

---

## 🔍 验证配置

### 查询字段分组统计

```sql
SELECT 
    device_type_code,
    field_group,
    is_default_visible,
    COUNT(*) as field_count
FROM t_device_field
WHERE device_type_code = 'BRUCKNER_EXTRUDER'
  AND is_active = true
GROUP BY device_type_code, field_group, is_default_visible
ORDER BY group_order, is_default_visible DESC;
```

### 查看默认显示字段

```sql
SELECT 
    device_type_code,
    field_name,
    field_code,
    field_group,
    is_default_visible,
    sort_order
FROM t_device_field
WHERE device_type_code = 'BRUCKNER_EXTRUDER'
  AND is_active = true
ORDER BY is_default_visible DESC, sort_order;
```

---

## 📦 文件清单

```
database/migrations/device-field-grouping/
├── 001_add_field_grouping.sql          # 数据库迁移脚本
└── README.md                            # 本文件

web/src/components/device/
├── DynamicMonitoringData.vue           # 原组件（保留）
└── GroupedMonitoringData.vue           # 新分组组件

app/schemas/
└── device_field.py                     # 更新Schema（新增3个字段）
```

---

## 🎯 已配置设备

### 布鲁克纳设备（6种）

| 设备类型 | 总字段 | 默认显示 | 折叠字段 | 状态 |
|---------|--------|---------|---------|------|
| BRUCKNER_EXTRUDER | 11 | 4 | 7 | ✅ |
| BRUCKNER_DIE | 6 | 3 | 3 | ✅ |
| BRUCKNER_CHILL_ROLL | 7 | 4 | 3 | ✅ |
| BRUCKNER_MDO_STRETCH | 6 | 4 | 2 | ✅ |
| BRUCKNER_TDO_TENTER | 9 | 4 | 5 | ✅ |
| BRUCKNER_THICKNESS | 5 | 5 | 0 | ✅ |

---

## 🔧 自定义配置

### 为新设备类型配置分组

1. **确定核心字段**（不超过4个）
2. **按类型分组其他字段**
3. **执行SQL配置**

```sql
-- 示例：配置新设备类型
UPDATE t_device_field 
SET field_group = 'core',
    is_default_visible = true,
    group_order = 1
WHERE device_type_code = 'NEW_DEVICE_TYPE' 
  AND field_code IN ('key_field1', 'key_field2', 'key_field3', 'key_field4');
```

### 调整现有配置

```sql
-- 将某个字段改为默认显示
UPDATE t_device_field 
SET is_default_visible = true
WHERE device_type_code = 'DEVICE_TYPE' 
  AND field_code = 'field_code';

-- 修改字段分组
UPDATE t_device_field 
SET field_group = 'temperature'
WHERE device_type_code = 'DEVICE_TYPE' 
  AND field_code = 'temp_field';
```

---

## 📈 性能优化

### 索引优化

已创建的索引可以显著提升查询性能：

```sql
-- 分组查询索引
idx_device_field_group (device_type_code, field_group, is_default_visible)

-- 可见性查询索引
idx_device_field_visible (device_type_code, is_default_visible, sort_order)
```

### 查询优化

前端组件会自动：
- 只查询激活的字段（is_active = true）
- 按分组和排序加载
- 使用计算属性缓存结果

---

## ✅ 预期效果

实施后：
- ✅ 卡片高度统一（约300-350px）
- ✅ 一屏显示更多设备（提升50%+）
- ✅ 核心信息突出显示
- ✅ 详细信息按需查看
- ✅ 用户体验大幅提升

---

## 🐛 故障排查

### 问题1：字段分组不生效

**检查**:
```sql
-- 查看字段配置
SELECT field_code, field_group, is_default_visible 
FROM t_device_field 
WHERE device_type_code = 'YOUR_TYPE';
```

**解决**: 确保已执行迁移脚本并重启后端

### 问题2：所有字段都显示

**检查**: 确认 `is_default_visible` 字段值

**解决**:
```sql
UPDATE t_device_field 
SET is_default_visible = false
WHERE device_type_code = 'YOUR_TYPE' 
  AND field_code NOT IN ('core_field1', 'core_field2');
```

### 问题3：分组顺序不对

**检查**: 查看 `group_order` 值

**解决**:
```sql
UPDATE t_device_field 
SET group_order = 2
WHERE device_type_code = 'YOUR_TYPE' 
  AND field_group = 'temperature';
```

---

## 📞 技术支持

如需帮助，请参考：
- [设备卡片字段过多优化方案](../../docs/device_test/设备卡片字段过多优化方案.md)
- [设备类型动态参数展示方案](../../docs/device_test/设备类型动态参数展示方案.md)

---

**最后更新**: 2025-11-25  
**版本**: v1.0  
**状态**: ✅ 已实施
