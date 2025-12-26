# 布鲁克纳生产线设备配置

## 📋 概述

本目录包含布鲁克纳双向拉伸薄膜生产线核心设备的配置脚本。

**配置内容**:
- ✅ 6种核心设备类型
- ✅ 50+个监测字段
- ✅ 完整的元数据配置（范围、告警、显示）
- ✅ TDengine超级表定义

## 🎯 核心设备类型

| 序号 | 设备类型 | 设备编码 | 监测字段数 | 优先级 |
|------|---------|---------|-----------|--------|
| 1 | 挤出机主机 | BRUCKNER_EXTRUDER | 11 | ⭐⭐⭐⭐⭐ |
| 2 | 模头 | BRUCKNER_DIE | 6 | ⭐⭐⭐⭐⭐ |
| 3 | 急冷辊 | BRUCKNER_CHILL_ROLL | 7 | ⭐⭐⭐⭐⭐ |
| 4 | MDO拉伸辊 | BRUCKNER_MDO_STRETCH | 6 | ⭐⭐⭐⭐⭐ |
| 5 | TDO拉幅机 | BRUCKNER_TDO_TENTER | 9 | ⭐⭐⭐⭐⭐ |
| 6 | 在线测厚仪 | BRUCKNER_THICKNESS | 5 | ⭐⭐⭐⭐⭐ |

**总计**: 44个监测字段

## 🚀 快速开始

### 步骤1：执行SQL配置脚本

```bash
# 连接到PostgreSQL数据库
psql -U postgres -d devicemonitor

# 执行配置脚本
\i database/migrations/bruckner-devices/001_core_devices_config.sql
```

**或者使用Python脚本**:

```bash
# 激活虚拟环境
.venv\Scripts\activate

# 执行配置
python -c "
import asyncio
from tortoise import Tortoise
from pathlib import Path

async def run():
    await Tortoise.init(
        db_url='postgres://postgres:Hanatech@123@127.0.0.1:5432/devicemonitor',
        modules={'models': ['app.models.device', 'app.models.admin']}
    )
    
    sql_file = Path('database/migrations/bruckner-devices/001_core_devices_config.sql')
    sql = sql_file.read_text(encoding='utf-8')
    
    # 执行SQL（需要手动分割执行）
    print('请手动执行SQL文件')
    
    await Tortoise.close_connections()

asyncio.run(run())
"
```

### 步骤2：创建设备实例和测试数据

```bash
# 执行测试数据生成脚本
python create_bruckner_devices_with_data.py
```

**脚本功能**:
- ✅ 创建8台设备实例
- ✅ 创建TDengine超级表和子表
- ✅ 生成24小时历史数据（每5分钟一条）

### 步骤3：验证配置

```bash
# 验证设备类型
python -c "
import asyncio
from tortoise import Tortoise
from app.models.device import DeviceType

async def check():
    await Tortoise.init(
        db_url='postgres://postgres:Hanatech@123@127.0.0.1:5432/devicemonitor',
        modules={'models': ['app.models.device']}
    )
    
    types = await DeviceType.filter(type_code__startswith='BRUCKNER_').all()
    print(f'✓ 已配置 {len(types)} 种设备类型:')
    for t in types:
        print(f'  - {t.type_code}: {t.type_name}')
    
    await Tortoise.close_connections()

asyncio.run(check())
"
```

## 📊 设备实例清单

### 挤出机主机 (2台)
- **EXT001**: 1号挤出机 - 挤出车间-A区
- **EXT002**: 2号挤出机 - 挤出车间-B区

### 模头 (1台)
- **DIE001**: 1号模头 - 铸片车间-A区

### 急冷辊 (2台)
- **CR001**: 1号急冷辊 - 铸片车间-A区
- **CR002**: 2号急冷辊 - 铸片车间-A区

### MDO拉伸辊 (1台)
- **MDO001**: 纵向拉伸机组 - 拉伸车间-MDO区

### TDO拉幅机 (1台)
- **TDO001**: 横向拉幅机 - 拉伸车间-TDO区

### 在线测厚仪 (1台)
- **THK001**: 在线测厚仪 - 后处理车间

## 🔧 监测字段详情

### 1. 挤出机主机 (BRUCKNER_EXTRUDER)

| 字段名 | 字段代码 | 单位 | 正常范围 | 告警阈值 |
|--------|---------|------|---------|---------|
| 1区温度 | zone1_temp | °C | 180-280 | 185-275 |
| 2区温度 | zone2_temp | °C | 200-300 | 205-295 |
| 3区温度 | zone3_temp | °C | 220-320 | 225-315 |
| 4区温度 | zone4_temp | °C | 230-330 | 235-325 |
| 5区温度 | zone5_temp | °C | 240-340 | 245-335 |
| 螺杆转速 | screw_speed | rpm | 0-150 | <140 |
| 熔体压力 | melt_pressure | MPa | 0-50 | <45 |
| 熔体温度 | melt_temperature | °C | 240-340 | 245-335 |
| 主电机电流 | motor_current | A | 0-500 | <450 |
| 电机扭矩 | motor_torque | % | 0-100 | <85 |
| 喂料速度 | feed_rate | kg/h | 0-2000 | 100-1900 |

### 2. 模头 (BRUCKNER_DIE)

| 字段名 | 字段代码 | 单位 | 正常范围 | 告警阈值 |
|--------|---------|------|---------|---------|
| 模头左侧温度 | die_temp_left | °C | 240-340 | 245-335 |
| 模头中间温度 | die_temp_center | °C | 240-340 | 245-335 |
| 模头右侧温度 | die_temp_right | °C | 240-340 | 245-335 |
| 模头压力 | die_pressure | MPa | 0-50 | <45 |
| 唇口间隙 | lip_gap | mm | 0.5-3.0 | 0.6-2.8 |
| 模头宽度 | die_width | mm | 1000-6000 | - |

### 3. 急冷辊 (BRUCKNER_CHILL_ROLL)

| 字段名 | 字段代码 | 单位 | 正常范围 | 告警阈值 |
|--------|---------|------|---------|---------|
| 辊筒温度 | roll_temperature | °C | 20-80 | 25-75 |
| 冷却水进水温度 | water_inlet_temp | °C | 15-30 | 16-28 |
| 冷却水出水温度 | water_outlet_temp | °C | 20-40 | <38 |
| 冷却水流量 | water_flow | m³/h | 0-100 | >10 |
| 辊筒转速 | roll_speed | m/min | 0-500 | <480 |
| 电机电流 | motor_current | A | 0-200 | <180 |
| 振动 | vibration | mm/s | 0-10 | <7 |

### 4. MDO拉伸辊 (BRUCKNER_MDO_STRETCH)

| 字段名 | 字段代码 | 单位 | 正常范围 | 告警阈值 |
|--------|---------|------|---------|---------|
| 慢辊速度 | slow_roll_speed | m/min | 0-200 | <190 |
| 快辊速度 | fast_roll_speed | m/min | 0-800 | <780 |
| 拉伸比 | stretch_ratio | - | 3.0-6.0 | 3.2-5.8 |
| 辊温 | roll_temperature | °C | 80-140 | 85-135 |
| 膜张力 | web_tension | N/m | 0-1000 | 100-900 |
| 电机扭矩 | motor_torque | % | 0-100 | <85 |

### 5. TDO拉幅机 (BRUCKNER_TDO_TENTER)

| 字段名 | 字段代码 | 单位 | 正常范围 | 告警阈值 |
|--------|---------|------|---------|---------|
| 预热区温度 | preheat_zone_temp | °C | 80-140 | 85-135 |
| 拉伸区温度 | stretch_zone_temp | °C | 100-160 | 105-155 |
| 热定型区温度 | heatset_zone_temp | °C | 140-200 | 145-195 |
| 冷却区温度 | cooling_zone_temp | °C | 40-80 | <75 |
| 进口宽度 | inlet_width | mm | 500-2000 | - |
| 出口宽度 | outlet_width | mm | 2000-10000 | - |
| 横向拉伸比 | stretch_ratio | - | 6.0-10.0 | 6.5-9.5 |
| 线速度 | line_speed | m/min | 0-500 | <480 |
| 烘箱压力 | oven_pressure | Pa | -50-50 | -40-40 |

### 6. 在线测厚仪 (BRUCKNER_THICKNESS)

| 字段名 | 字段代码 | 单位 | 正常范围 | 告警阈值 |
|--------|---------|------|---------|---------|
| 平均厚度 | avg_thickness | μm | 10-100 | 12-95 |
| 厚度偏差 | thickness_deviation | μm | 0-5 | <3 |
| 横向均匀性 | profile_uniformity | % | 90-100 | >95 |
| 扫描位置 | scan_position | mm | 0-10000 | - |
| 测量频率 | measurement_rate | Hz | 0-1000 | - |

## 📈 TDengine表结构

### 超级表命名规则
```
st_bruckner_{device_type}
```

### 子表命名规则
```
tb_{device_code}
```

### 示例
- 超级表: `st_bruckner_extruder`
- 子表: `tb_ext001`, `tb_ext002`

## 🔍 验证查询

### 查询设备类型
```sql
SELECT type_code, type_name, device_count
FROM t_device_type
WHERE type_code LIKE 'BRUCKNER_%'
ORDER BY type_code;
```

### 查询监测字段
```sql
SELECT 
    device_type_code,
    field_name,
    field_code,
    unit,
    is_monitoring_key
FROM t_device_field
WHERE device_type_code LIKE 'BRUCKNER_%'
  AND is_active = true
ORDER BY device_type_code, sort_order;
```

### 查询设备实例
```sql
SELECT 
    device_code,
    device_name,
    device_type,
    install_location
FROM t_device_info
WHERE device_type LIKE 'BRUCKNER_%'
ORDER BY device_type, device_code;
```

### 查询TDengine数据
```sql
-- 查询挤出机最新数据
SELECT * FROM st_bruckner_extruder 
WHERE device_code = 'EXT001' 
ORDER BY ts DESC 
LIMIT 10;

-- 查询所有设备最新数据
SELECT LAST(*) FROM st_bruckner_extruder GROUP BY device_code;
```

## 🎨 前端显示配置

每个字段都包含 `display_config` JSON配置：

```json
{
  "icon": "🌡️",
  "color": "#1890ff",
  "chart_type": "line"
}
```

**图标说明**:
- 🌡️ 温度
- ⚡ 电流
- 📊 压力
- ⚙️ 转速
- 💧 水流
- 📏 尺寸
- 📈 比率
- 🎯 张力

## 📝 注意事项

1. **数据范围**: 所有字段都配置了合理的数据范围
2. **告警阈值**: 核心参数配置了warning和critical两级告警
3. **聚合方法**: 大部分字段使用avg聚合，振动使用max
4. **AI特征**: 所有监测字段都标记为AI特征字段
5. **排序**: 字段按重要性排序，便于前端展示

## 🚀 下一步

1. **前端集成**: 在设备监控页面展示这些设备
2. **实时数据**: 配置WebSocket推送实时数据
3. **告警规则**: 配置告警规则和通知
4. **AI分析**: 使用这些数据进行质量溯源和预测性维护

## 📞 支持

如有问题，请参考：
- [设备类型划分方案](../../docs/jskh/布鲁克纳设备类型划分方案.md)
- [AI应用结合分析报告](../../docs/jskh/AI应用结合分析报告.md)
- [新增设备类型指南](../../docs/device_test/新增设备类型与AI检测实现指南.md)
