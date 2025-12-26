# 报警规则系统 - 数据库迁移

## 概述

本迁移脚本为设备参数报警监测系统创建必要的数据库表和菜单。

## 包含内容

1. **t_alarm_rule** - 报警规则配置表
2. **t_alarm_record** - 报警记录表
3. 报警规则菜单
4. 报警记录菜单

## 文件说明

- `001_create_alarm_tables.sql` - 创建报警规则表和报警记录表
- `002_add_alarm_rules_menu.sql` - 添加报警规则菜单（使用函数方式）
- `003_insert_alarm_rules_menu.sql` - 直接插入报警规则菜单（推荐）
- `004_insert_alarm_records_menu.sql` - 插入报警记录菜单
- `apply_alarm_rules.py` - Python执行脚本

## 执行方式

```bash
cd database/migrations/alarm-rules
python apply_alarm_rules.py
```

或手动执行SQL：

```bash
psql -h 127.0.0.1 -U postgres -d devicemonitor -f 001_create_alarm_tables.sql
psql -h 127.0.0.1 -U postgres -d devicemonitor -f 002_add_alarm_rules_menu.sql
```

## 示例规则

迁移脚本会自动创建3条示例报警规则：

| 规则名称 | 设备类型 | 监测字段 | 阈值类型 |
|---------|---------|---------|---------|
| 焊机温度过高报警 | welding | temperature | 上限检测 |
| 焊接电流异常报警 | welding | welding_current | 范围检测 |
| 压力超限报警 | pressure_sensor | pressure | 范围检测 |

## 验证

执行后访问：报警管理 > 报警规则

## 功能说明

### 阈值类型

- **range** - 范围检测：值需在 min~max 范围内
- **upper** - 上限检测：值不能超过 max
- **lower** - 下限检测：值不能低于 min
- **change_rate** - 变化率检测：检测值的变化速率

### 报警级别

- **info** - 信息
- **warning** - 警告
- **critical** - 严重
- **emergency** - 紧急

### 触发条件

- `consecutive_count` - 连续N次超阈值才触发
- `duration_seconds` - 持续N秒才触发
