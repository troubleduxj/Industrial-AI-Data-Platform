# 设备类型动态参数展示 - 需求文档

## 功能概述

实现基于元数据驱动的设备类型参数动态展示功能，使得不同设备类型在实时监测页面能够展示各自特定的监测参数，无需修改前端代码。

## 业务背景

当前系统的实时监测页面硬编码了焊机的监测参数（预设电流、预设电压、焊接电流、焊接电压），导致：
- 新增设备类型时需要修改前端代码
- 不同设备类型无法展示各自特有的参数
- 维护成本高，扩展性差

## 目标用户

- **运维人员**: 需要查看不同设备类型的实时监测数据
- **系统管理员**: 需要配置设备类型的监测参数
- **开发人员**: 需要快速集成新的设备类型

## 核心需求

### AC-1: 后端提供字段配置查询接口

**描述**: 系统应提供API接口，根据设备类型代码查询该类型的监测关键字段配置

**验收标准**:
- 接口路径: `GET /api/v2/device-fields/monitoring-keys/{device_type_code}`
- 返回字段包含: field_name, field_code, field_type, unit, sort_order, display_config
- 只返回 is_monitoring_key=true 且 is_active=true 的字段
- 按 sort_order 升序排序
- 响应时间 < 200ms

**示例**:
```json
GET /api/v2/device-fields/monitoring-keys/WELD_MACHINE

Response:
{
  "code": 200,
  "data": [
    {
      "id": 1,
      "field_name": "预设电流",
      "field_code": "preset_current",
      "field_type": "float",
      "unit": "A",
      "sort_order": 1,
      "display_config": {
        "icon": "⚡",
        "color": "#1890ff"
      }
    }
  ]
}
```

### AC-2: 后端提供设备实时数据及配置接口

**描述**: 系统应提供API接口，一次性返回设备的实时数据和字段配置

**验收标准**:
- 接口路径: `GET /api/v2/devices/{device_code}/realtime-with-config`
- 返回内容包含: 设备信息、监测字段配置、实时数据
- 实时数据从 TDengine 查询最新一条记录
- 字段配置根据设备类型自动匹配
- 响应时间 < 500ms

**示例**:
```json
GET /api/v2/devices/WM001/realtime-with-config

Response:
{
  "code": 200,
  "data": {
    "device_code": "WM001",
    "device_name": "1号焊机",
    "device_type": "WELD_MACHINE",
    "monitoring_fields": [...],
    "realtime_data": {
      "preset_current": 150.5,
      "preset_voltage": 28.3
    }
  }
}
```

### AC-3: 后端提供批量查询接口

**描述**: 系统应支持批量查询多个设备的实时数据和配置，优化性能

**验收标准**:
- 接口路径: `POST /api/v2/devices/batch-realtime-with-config`
- 请求体包含设备编码列表
- 按设备类型分组查询字段配置，避免重复查询
- 支持最多 100 个设备同时查询
- 响应时间 < 500ms (50个设备)

### AC-3.1: 后端提供分页查询接口（性能优化）

**描述**: 系统应支持分页查询设备实时数据，支持大规模设备场景

**验收标准**:
- 接口路径: `POST /api/v2/devices/realtime-paginated`
- 支持分页参数: page, page_size
- 支持筛选条件: device_type, status
- 返回分页信息: total, page, page_size, total_pages
- 响应时间 < 500ms (50个设备/页)
- 支持 1000+ 设备的分页查询

### AC-4: 前端动态渲染监测参数

**描述**: 实时监测页面的设备卡片应根据字段配置动态渲染参数

**验收标准**:
- 创建 DynamicMonitoringData 组件
- 根据 monitoring_fields 配置动态生成参数行
- 支持显示字段图标、名称、数值、单位
- 支持自定义颜色显示
- 数值格式化: float 保留2位小数，int 取整
- 空值显示为 "--"

### AC-5: 前端缓存字段配置

**描述**: 前端应缓存设备类型的字段配置，减少API请求

**验收标准**:
- 使用 Pinia store 管理字段配置缓存
- 缓存 key 为设备类型代码
- 首次查询后缓存，后续直接使用缓存
- 提供清除缓存方法
- 缓存有效期: 会话期间

### AC-6: 数据库配置监测字段

**描述**: 系统管理员可以通过数据库配置设备类型的监测字段

**验收标准**:
- 使用 t_device_field 表的 is_monitoring_key 字段标识
- 支持配置字段显示顺序 (sort_order)
- 支持配置显示属性 (display_config: icon, color)
- 支持启用/禁用字段 (is_active)
- 配置后立即生效（清除前端缓存）

## 非功能需求

### NFR-1: 性能要求
- 单个设备查询响应时间 < 500ms
- 批量查询(50个设备) 响应时间 < 500ms
- 全量加载(1000个设备) 响应时间 < 3s
- 前端渲染 100 个设备卡片 < 1s
- WebSocket 实时更新延迟 < 100ms
- 支持 100+ 用户并发访问

### NFR-2: 可扩展性要求
- 支持 1000+ 设备的实时监测
- 支持分页加载，每页 50-100 个设备
- 支持虚拟滚动，优化大列表渲染
- 支持 Redis 缓存，减少数据库压力

### NFR-3: 兼容性要求
- 兼容现有焊机设备的展示
- 支持新增任意设备类型
- 不影响现有功能

### NFR-4: 可维护性要求
- 新增设备类型无需修改代码
- 配置变更无需重启服务
- 提供配置示例和文档
- 提供性能监控和告警

## 约束条件

- 必须使用现有的 t_device_field 表结构
- 必须兼容现有的 TDengine 数据查询
- 前端必须使用 Vue 3 + TypeScript
- 后端必须使用 FastAPI

### AC-7: 性能优化支持（大规模设备场景）

**描述**: 系统应支持大规模设备（1000+）的性能优化

**验收标准**:
- 支持 Redis 缓存字段配置和实时数据
- 支持 TDengine 批量并行查询
- 支持前端虚拟滚动渲染
- 支持 WebSocket 增量推送
- 全量加载 1000 个设备响应时间 < 3s
- 提供性能监控指标

## 参考文档

- #[[file:../../../docs/device_test/设备类型动态参数展示方案.md]]
- #[[file:../../../app/models/device.py]]
- #[[file:./performance-optimization.md]] - 大规模设备性能优化方案
