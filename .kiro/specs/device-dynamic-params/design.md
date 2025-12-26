# 设备类型动态参数展示 - 设计文档

## 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                    前端层 (Vue3)                         │
│  ┌──────────────────┐  ┌──────────────────────────┐    │
│  │ 实时监测页面      │  │ DynamicMonitoringData    │    │
│  │ monitor/index.vue│  │ 组件                      │    │
│  └────────┬─────────┘  └──────────┬───────────────┘    │
│           │                       │                      │
│  ┌────────▼───────────────────────▼───────────────┐    │
│  │      Pinia Store (字段配置缓存)                 │    │
│  └────────┬─────────────────────────────────────┬─┘    │
└───────────┼─────────────────────────────────────┼──────┘
            │                                     │
            │ HTTP API                            │
            │                                     │
┌───────────▼─────────────────────────────────────▼──────┐
│                    后端层 (FastAPI)                     │
│  ┌──────────────────┐  ┌──────────────────────────┐   │
│  │ DeviceFieldAPI   │  │ DeviceAPI                 │   │
│  │ 字段配置接口      │  │ 设备数据接口              │   │
│  └────────┬─────────┘  └──────────┬───────────────┘   │
│           │                       │                     │
│  ┌────────▼───────────────────────▼───────────────┐   │
│  │      Service Layer (业务逻辑层)                 │   │
│  └────────┬─────────────────────────────────────┬─┘   │
└───────────┼─────────────────────────────────────┼─────┘
            │                                     │
    ┌───────▼────────┐                   ┌───────▼────────┐
    │  PostgreSQL    │                   │   TDengine     │
    │  (字段配置)     │                   │  (实时数据)     │
    └────────────────┘                   └────────────────┘
```

## 正确性属性

### P-1: 字段配置查询正确性
**对应需求**: AC-1

**属性**: 给定设备类型代码，系统必须返回该类型所有标记为监测关键字段的配置

**形式化**:
```
∀ device_type_code ∈ DeviceTypes:
  fields = query_monitoring_fields(device_type_code)
  ⇒ ∀ f ∈ fields: 
      f.device_type_code = device_type_code ∧
      f.is_monitoring_key = true ∧
      f.is_active = true
```

**验证方法**:
- 单元测试: 测试不同设备类型的字段查询
- 集成测试: 验证数据库查询结果
- 边界测试: 不存在的设备类型返回空列表

### P-2: 字段排序正确性
**对应需求**: AC-1

**属性**: 返回的字段列表必须按 sort_order 升序排列

**形式化**:
```
fields = query_monitoring_fields(device_type_code)
⇒ ∀ i, j: 0 ≤ i < j < len(fields)
    ⇒ fields[i].sort_order ≤ fields[j].sort_order
```

**验证方法**:
- 单元测试: 验证排序逻辑
- 属性测试: 使用不同 sort_order 组合测试

### P-3: 实时数据与配置一致性
**对应需求**: AC-2

**属性**: 返回的实时数据字段必须与字段配置中的 field_code 一致

**形式化**:
```
response = get_realtime_with_config(device_code)
monitoring_fields = response.monitoring_fields
realtime_data = response.realtime_data

⇒ ∀ f ∈ monitoring_fields:
    f.field_code ∈ keys(realtime_data) ∨ realtime_data[f.field_code] = null
```

**验证方法**:
- 集成测试: 验证 TDengine 查询结果
- Mock 测试: 模拟不同数据场景

### P-4: 批量查询性能优化
**对应需求**: AC-3

**属性**: 批量查询时，相同设备类型的字段配置只查询一次

**形式化**:
```
devices = [d1, d2, d3, ...]
device_types = unique([d.device_type for d in devices])

query_count = count_field_config_queries(devices)
⇒ query_count = len(device_types)
```

**验证方法**:
- 性能测试: 监控数据库查询次数
- 单元测试: 验证缓存逻辑

### P-5: 前端数值格式化正确性
**对应需求**: AC-4

**属性**: 数值必须根据字段类型正确格式化

**形式化**:
```
∀ field, value:
  field.field_type = 'float' ⇒ format(value) = round(value, 2)
  field.field_type = 'int' ⇒ format(value) = round(value)
  value = null ⇒ format(value) = '--'
```

**验证方法**:
- 单元测试: 测试格式化函数
- 快照测试: 验证渲染结果

### P-6: 缓存一致性
**对应需求**: AC-5

**属性**: 缓存的字段配置必须与数据库保持一致

**形式化**:
```
cache_data = get_from_cache(device_type_code)
db_data = query_from_db(device_type_code)

⇒ cache_data = null ∨ cache_data = db_data
```

**验证方法**:
- 单元测试: 验证缓存读写逻辑
- 集成测试: 验证缓存失效机制

## 数据模型

### 字段配置模型

```typescript
interface DeviceField {
  id: number
  device_type_code: string      // 设备类型代码
  field_name: string             // 字段显示名称
  field_code: string             // 字段代码（用于数据匹配）
  field_type: 'float' | 'int' | 'string' | 'boolean'
  unit?: string                  // 单位
  is_monitoring_key: boolean     // 是否为监测关键字段
  sort_order: number             // 显示顺序
  display_config?: {             // 显示配置
    icon?: string                // 图标
    color?: string               // 颜色
    chart_type?: string          // 图表类型
  }
  is_active: boolean             // 是否启用
}
```

### 设备实时数据模型

```typescript
interface DeviceRealtimeWithConfig {
  device_code: string
  device_name: string
  device_type: string
  monitoring_fields: DeviceField[]
  realtime_data: Record<string, number | string | null>
}
```

## API 设计

### API-1: 查询监测字段配置

```
GET /api/v2/device-fields/monitoring-keys/{device_type_code}

Response:
{
  "code": 200,
  "message": "success",
  "data": DeviceField[]
}

Error Cases:
- 404: 设备类型不存在
- 500: 服务器错误
```

### API-2: 获取设备实时数据及配置

```
GET /api/v2/devices/{device_code}/realtime-with-config

Response:
{
  "code": 200,
  "message": "success",
  "data": DeviceRealtimeWithConfig
}

Error Cases:
- 404: 设备不存在
- 500: TDengine 查询失败
```

### API-3: 批量获取设备数据

```
POST /api/v2/devices/batch-realtime-with-config

Request:
{
  "device_codes": string[]
}

Response:
{
  "code": 200,
  "message": "success",
  "data": DeviceRealtimeWithConfig[]
}

Error Cases:
- 400: 设备数量超过限制
- 500: 服务器错误
```

## 组件设计

### DynamicMonitoringData 组件

**职责**: 根据字段配置动态渲染监测参数

**Props**:
```typescript
interface Props {
  monitoringFields: DeviceField[]  // 字段配置
  realtimeData: Record<string, any> // 实时数据
  loading?: boolean                 // 加载状态
}
```

**核心方法**:
```typescript
// 格式化数值
function formatValue(value: any, field: DeviceField): string

// 获取字段图标
function getFieldIcon(field: DeviceField): string

// 获取字段颜色
function getFieldColor(field: DeviceField): string
```

## 数据流设计

### 流程 1: 页面初始化加载

```
1. 用户访问实时监测页面
2. 前端获取设备列表
3. 提取所有设备编码
4. 调用批量查询 API
5. 后端按设备类型分组
6. 查询字段配置（每种类型一次）
7. 查询 TDengine 实时数据
8. 组装返回数据
9. 前端缓存字段配置
10. 渲染设备卡片
```

### 流程 2: 单个设备详情查看

```
1. 用户点击设备卡片
2. 检查缓存中是否有字段配置
3. 如有缓存，直接使用
4. 如无缓存，调用字段配置 API
5. 缓存字段配置
6. 调用实时数据 API
7. 渲染设备详情
```

## 性能优化策略

### 后端优化

1. **字段配置缓存**: 使用 Redis 缓存字段配置，TTL 1小时
2. **批量查询优化**: 按设备类型分组，减少数据库查询
3. **数据库索引**: 在 device_type_code, is_monitoring_key 上建立索引
4. **连接池**: TDengine 使用连接池，避免频繁建立连接

### 前端优化

1. **Pinia 缓存**: 会话期间缓存字段配置
2. **虚拟滚动**: 设备列表使用虚拟滚动，只渲染可见区域
3. **防抖节流**: 筛选操作使用防抖，避免频繁请求
4. **骨架屏**: 加载时显示骨架屏，提升用户体验

## 错误处理

### 后端错误处理

```python
try:
    fields = await DeviceField.filter(...).all()
except Exception as e:
    logger.error(f"查询字段配置失败: {e}")
    raise HTTPException(status_code=500, detail="查询字段配置失败")
```

### 前端错误处理

```typescript
try {
  const response = await deviceFieldApi.getMonitoringKeys(deviceType)
  return response.data
} catch (error) {
  console.error('获取字段配置失败:', error)
  message.error('获取字段配置失败，请稍后重试')
  return []
}
```

## 测试策略

### 单元测试

- 后端: 测试字段查询、数据格式化、排序逻辑
- 前端: 测试组件渲染、数值格式化、缓存逻辑

### 集成测试

- API 测试: 测试所有 API 端点
- 数据库测试: 测试字段配置查询
- TDengine 测试: 测试实时数据查询

### E2E 测试

- 页面加载测试
- 设备卡片渲染测试
- 不同设备类型展示测试

## 安全考虑

1. **权限控制**: 字段配置查询需要登录权限
2. **输入验证**: 验证设备类型代码格式
3. **SQL 注入防护**: 使用 ORM 参数化查询
4. **XSS 防护**: 前端对字段名称进行转义

## 兼容性方案

### 向后兼容

- 保留现有焊机硬编码逻辑作为降级方案
- 如果字段配置查询失败，使用默认配置
- 逐步迁移现有设备类型到新方案

### 降级策略

```typescript
// 如果动态配置失败，使用硬编码配置
const fallbackFields = {
  'WELD_MACHINE': [
    { field_code: 'preset_current', field_name: '预设电流', unit: 'A' },
    // ...
  ]
}
```
