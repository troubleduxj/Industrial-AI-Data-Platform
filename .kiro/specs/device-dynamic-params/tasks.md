# 设备类型动态参数展示 - 任务列表

## 任务概览

本 Spec 包含 3 个主要阶段，共 20 个任务（包含 5 个性能优化任务）。

## 阶段 1: 后端 API 开发

### TASK-0: 搭建 Redis 缓存服务
**对应需求**: AC-7, NFR-1  
**对应属性**: P-4  
**优先级**: P0  
**预计时间**: 2h

**描述**: 搭建 Redis 缓存服务，用于缓存字段配置和实时数据

**实现文件**:
- `app/services/cache_service.py` (新建)
- `app/core/redis.py` (新建或修改)
- `app/settings/config.py` (修改，添加 Redis 配置)

**验收标准**:
- [ ] 配置 Redis 连接
- [ ] 创建 DeviceDataCacheService 类
- [ ] 实现字段配置缓存（TTL 1小时）
- [ ] 实现实时数据缓存（TTL 10秒）
- [ ] 实现批量获取缓存方法
- [ ] 添加缓存失效机制

**测试要求**:
- [ ] 单元测试: 测试缓存读写
- [ ] 单元测试: 测试缓存过期
- [ ] 集成测试: 测试 Redis 连接

---

### TASK-1: 创建设备字段 API 路由
**对应需求**: AC-1  
**对应属性**: P-1, P-2  
**优先级**: P0  
**预计时间**: 2h

**描述**: 创建设备字段配置查询的 API 路由和控制器

**实现文件**:
- `app/api/v2/device_field.py` (新建)
- `app/api/v2/__init__.py` (修改，注册路由)

**验收标准**:
- [ ] 创建 `/api/v2/device-fields/monitoring-keys/{device_type_code}` 端点
- [ ] 实现字段查询逻辑，筛选 is_monitoring_key=true 和 is_active=true
- [ ] 按 sort_order 升序排序
- [ ] 返回标准响应格式
- [ ] 添加错误处理

**测试要求**:
- [ ] 单元测试: 测试查询逻辑
- [ ] 集成测试: 测试 API 端点
- [ ] 边界测试: 不存在的设备类型

---

### TASK-2: 创建设备字段 Schema
**对应需求**: AC-1  
**优先级**: P0  
**预计时间**: 1h

**描述**: 创建设备字段的 Pydantic Schema

**实现文件**:
- `app/schemas/device_field.py` (新建)

**验收标准**:
- [ ] 创建 DeviceFieldSchema
- [ ] 包含所有必要字段
- [ ] 添加字段验证规则
- [ ] 添加示例数据

**测试要求**:
- [ ] 单元测试: 测试 Schema 验证

---

### TASK-3: 扩展设备实时数据 API
**对应需求**: AC-2  
**对应属性**: P-3  
**优先级**: P0  
**预计时间**: 3h

**描述**: 扩展设备 API，支持返回实时数据和字段配置

**实现文件**:
- `app/api/v2/device.py` (修改)
- `app/services/device_service.py` (修改)

**验收标准**:
- [ ] 创建 `/api/v2/devices/{device_code}/realtime-with-config` 端点
- [ ] 查询设备信息
- [ ] 查询设备类型的字段配置
- [ ] 从 TDengine 查询实时数据
- [ ] 组装返回数据
- [ ] 响应时间 < 500ms

**测试要求**:
- [ ] 单元测试: 测试数据组装逻辑
- [ ] 集成测试: 测试完整流程
- [ ] 性能测试: 验证响应时间

---

### TASK-4: 实现批量查询 API
**对应需求**: AC-3  
**对应属性**: P-4  
**优先级**: P1  
**预计时间**: 3h

**描述**: 实现批量查询多个设备的实时数据和配置

**实现文件**:
- `app/api/v2/device.py` (修改)
- `app/services/device_service.py` (修改)

**验收标准**:
- [ ] 创建 `/api/v2/devices/batch-realtime-with-config` 端点
- [ ] 按设备类型分组查询字段配置
- [ ] 批量查询 TDengine 数据
- [ ] 支持最多 100 个设备
- [ ] 响应时间 < 500ms (50个设备)

**测试要求**:
- [ ] 单元测试: 测试分组逻辑
- [ ] 性能测试: 测试批量查询性能
- [ ] 边界测试: 测试设备数量限制

---

### TASK-4.1: 实现分页查询 API（性能优化）
**对应需求**: AC-3.1, AC-7, NFR-1  
**对应属性**: P-4  
**优先级**: P0  
**预计时间**: 3h

**描述**: 实现分页查询设备实时数据，支持大规模设备场景

**实现文件**:
- `app/api/v2/device.py` (修改)
- `app/services/device_service.py` (修改)

**验收标准**:
- [ ] 创建 `/api/v2/devices/realtime-paginated` 端点
- [ ] 支持分页参数: page, page_size
- [ ] 支持筛选条件: device_type, status
- [ ] 返回分页信息: total, page, page_size, total_pages
- [ ] 集成 Redis 缓存
- [ ] 响应时间 < 500ms (50个设备/页)

**测试要求**:
- [ ] 单元测试: 测试分页逻辑
- [ ] 性能测试: 测试 1000 个设备的分页查询
- [ ] 集成测试: 测试缓存集成

---

### TASK-4.2: 优化 TDengine 批量查询
**对应需求**: AC-7, NFR-1  
**对应属性**: P-4  
**优先级**: P0  
**预计时间**: 3h

**描述**: 优化 TDengine 批量查询性能，使用 UNION ALL 和并行查询

**实现文件**:
- `app/services/tdengine_service.py` (新建或修改)

**验收标准**:
- [ ] 实现 batch_query_tdengine_parallel 方法
- [ ] 使用 UNION ALL 合并查询
- [ ] 支持分批查询（每批 100 个设备）
- [ ] 使用异步并行查询
- [ ] 查询 100 个设备响应时间 < 1s

**测试要求**:
- [ ] 单元测试: 测试查询逻辑
- [ ] 性能测试: 对比优化前后的查询时间
- [ ] 压力测试: 测试并发查询

---

### TASK-5: 添加数据库索引优化
**对应需求**: NFR-1  
**优先级**: P1  
**预计时间**: 1h

**描述**: 为字段查询添加数据库索引

**实现文件**:
- `migrations/` (新建迁移文件)

**验收标准**:
- [ ] 在 device_type_code 上创建索引
- [ ] 在 (device_type_code, is_monitoring_key) 上创建复合索引
- [ ] 在 (device_type_code, sort_order) 上创建复合索引
- [ ] 验证查询性能提升

**测试要求**:
- [ ] 性能测试: 对比索引前后的查询时间

---

## 阶段 2: 前端组件开发

### TASK-6: 创建设备字段 API 接口
**对应需求**: AC-4  
**优先级**: P0  
**预计时间**: 1h

**描述**: 创建前端调用设备字段 API 的接口定义

**实现文件**:
- `web/src/api/device-field.ts` (新建)

**验收标准**:
- [ ] 定义 DeviceField 接口
- [ ] 实现 getMonitoringKeys 方法
- [ ] 添加错误处理
- [ ] 添加 TypeScript 类型定义

**测试要求**:
- [ ] 单元测试: 测试 API 调用

---

### TASK-7: 扩展设备 API 接口
**对应需求**: AC-2, AC-3  
**优先级**: P0  
**预计时间**: 1h

**描述**: 扩展设备 API 接口，支持新的端点

**实现文件**:
- `web/src/api/device-v2.ts` (修改)

**验收标准**:
- [ ] 定义 DeviceRealtimeWithConfig 接口
- [ ] 实现 getRealtimeWithConfig 方法
- [ ] 实现 batchGetRealtimeWithConfig 方法
- [ ] 添加 TypeScript 类型定义

**测试要求**:
- [ ] 单元测试: 测试接口定义

---

### TASK-8: 创建 DynamicMonitoringData 组件
**对应需求**: AC-4  
**对应属性**: P-5  
**优先级**: P0  
**预计时间**: 3h

**描述**: 创建动态渲染监测参数的 Vue 组件

**实现文件**:
- `web/src/components/device/DynamicMonitoringData.vue` (新建)

**验收标准**:
- [ ] 接收 monitoringFields 和 realtimeData props
- [ ] 动态渲染参数行
- [ ] 支持显示图标、名称、数值、单位
- [ ] 支持自定义颜色
- [ ] 实现数值格式化函数
- [ ] 空值显示为 "--"
- [ ] 添加加载状态

**测试要求**:
- [ ] 单元测试: 测试格式化函数
- [ ] 组件测试: 测试渲染逻辑
- [ ] 快照测试: 验证渲染结果

---

### TASK-9: 创建设备字段 Store
**对应需求**: AC-5  
**对应属性**: P-6  
**优先级**: P1  
**预计时间**: 2h

**描述**: 创建 Pinia store 管理字段配置缓存

**实现文件**:
- `web/src/store/modules/device-field.ts` (新建)

**验收标准**:
- [ ] 创建 useDeviceFieldStore
- [ ] 实现字段配置缓存 Map
- [ ] 实现 getMonitoringFields 方法（带缓存）
- [ ] 实现 clearCache 方法
- [ ] 缓存 key 为设备类型代码

**测试要求**:
- [ ] 单元测试: 测试缓存读写
- [ ] 单元测试: 测试缓存失效

---

### TASK-10: 修改实时监测页面
**对应需求**: AC-4  
**优先级**: P0  
**预计时间**: 4h

**描述**: 修改实时监测页面，集成动态参数展示

**实现文件**:
- `web/src/views/device-monitor/monitor/index.vue` (修改)

**验收标准**:
- [ ] 导入 DynamicMonitoringData 组件
- [ ] 调用分页查询 API 获取数据
- [ ] 替换硬编码的参数展示
- [ ] 保持现有的布局和样式
- [ ] 添加加载状态处理
- [ ] 添加错误处理

**测试要求**:
- [ ] E2E 测试: 测试页面加载
- [ ] E2E 测试: 测试设备卡片渲染

---

### TASK-10.1: 实现虚拟滚动（性能优化）
**对应需求**: AC-7, NFR-1, NFR-2  
**优先级**: P0  
**预计时间**: 2h

**描述**: 使用虚拟滚动优化大列表渲染性能

**实现文件**:
- `web/src/views/device-monitor/monitor/index.vue` (修改)
- `package.json` (添加 vue-virtual-scroller 依赖)

**验收标准**:
- [ ] 安装 vue-virtual-scroller
- [ ] 使用 RecycleScroller 组件
- [ ] 配置 item-size 和 buffer
- [ ] 渲染 1000 个设备卡片 < 1s
- [ ] 滚动流畅，无卡顿

**测试要求**:
- [ ] 性能测试: 测试渲染时间
- [ ] 性能测试: 测试滚动性能
- [ ] E2E 测试: 测试虚拟滚动功能

---

### TASK-10.2: 实现无限滚动加载
**对应需求**: AC-3.1, NFR-2  
**优先级**: P1  
**预计时间**: 2h

**描述**: 实现无限滚动，自动加载更多设备

**实现文件**:
- `web/src/views/device-monitor/monitor/index.vue` (修改)
- `web/src/composables/useInfiniteScroll.ts` (新建)

**验收标准**:
- [ ] 使用 @vueuse/core 的 useInfiniteScroll
- [ ] 滚动到底部自动加载下一页
- [ ] 显示加载状态
- [ ] 支持加载失败重试
- [ ] 加载完所有数据后停止

**测试要求**:
- [ ] E2E 测试: 测试无限滚动
- [ ] E2E 测试: 测试加载状态

---

### TASK-10.3: 实现 WebSocket 实时更新（可选）
**对应需求**: AC-7, NFR-1  
**优先级**: P2  
**预计时间**: 4h

**描述**: 使用 WebSocket 实现设备数据的实时推送更新

**实现文件**:
- `web/src/composables/useDeviceRealtime.ts` (新建)
- `app/api/v2/websocket.py` (新建)
- `app/services/websocket_service.py` (新建)

**验收标准**:
- [ ] 创建 WebSocket 连接
- [ ] 实现设备订阅/取消订阅
- [ ] 实现增量数据推送
- [ ] 实现频率限制（1秒/次）
- [ ] 实现自动重连
- [ ] 推送延迟 < 100ms

**测试要求**:
- [ ] 单元测试: 测试订阅逻辑
- [ ] 集成测试: 测试 WebSocket 连接
- [ ] 性能测试: 测试推送延迟

---

## 阶段 3: 数据配置与测试

### TASK-11: 配置焊机监测字段
**对应需求**: AC-6  
**优先级**: P0  
**预计时间**: 0.5h

**描述**: 在数据库中配置焊机的监测字段

**实现文件**:
- SQL 脚本或数据迁移

**验收标准**:
- [ ] 更新 preset_current 字段配置
- [ ] 更新 preset_voltage 字段配置
- [ ] 更新 welding_current 字段配置
- [ ] 更新 welding_voltage 字段配置
- [ ] 设置 is_monitoring_key = true
- [ ] 设置 sort_order
- [ ] 配置 display_config (icon, color)

**测试要求**:
- [ ] 验证数据库配置正确

---

### TASK-12: 配置压力传感器监测字段
**对应需求**: AC-6  
**优先级**: P1  
**预计时间**: 0.5h

**描述**: 在数据库中配置压力传感器的监测字段

**实现文件**:
- SQL 脚本或数据迁移

**验收标准**:
- [ ] 更新 pressure 字段配置
- [ ] 更新 temperature 字段配置
- [ ] 更新 vibration 字段配置
- [ ] 设置 is_monitoring_key = true
- [ ] 设置 sort_order
- [ ] 配置 display_config

**测试要求**:
- [ ] 验证数据库配置正确

---

### TASK-13: 编写 API 集成测试
**对应需求**: 所有 AC  
**优先级**: P1  
**预计时间**: 2h

**描述**: 编写完整的 API 集成测试

**实现文件**:
- `tests/api/test_device_field.py` (新建)
- `tests/api/test_device_realtime.py` (修改)

**验收标准**:
- [ ] 测试字段配置查询 API
- [ ] 测试实时数据查询 API
- [ ] 测试批量查询 API
- [ ] 测试错误场景
- [ ] 测试性能要求

**测试要求**:
- [ ] 所有测试通过
- [ ] 代码覆盖率 > 80%

---

### TASK-14: 编写前端组件测试
**对应需求**: AC-4, AC-5  
**优先级**: P1  
**预计时间**: 2h

**描述**: 编写前端组件和 Store 的单元测试

**实现文件**:
- `web/src/components/device/__tests__/DynamicMonitoringData.spec.ts` (新建)
- `web/src/store/modules/__tests__/device-field.spec.ts` (新建)

**验收标准**:
- [ ] 测试 DynamicMonitoringData 组件渲染
- [ ] 测试数值格式化函数
- [ ] 测试 Store 缓存逻辑
- [ ] 测试错误处理

**测试要求**:
- [ ] 所有测试通过
- [ ] 代码覆盖率 > 80%

---

### TASK-15: E2E 测试和文档
**对应需求**: 所有 AC  
**优先级**: P2  
**预计时间**: 2h

**描述**: 编写端到端测试和使用文档

**实现文件**:
- `tests/e2e/test_device_monitor.py` (新建)
- `docs/device_test/设备字段配置指南.md` (新建)

**验收标准**:
- [ ] E2E 测试覆盖主要流程
- [ ] 编写配置指南文档
- [ ] 编写 API 使用文档
- [ ] 添加配置示例

**测试要求**:
- [ ] E2E 测试通过

---

## 任务依赖关系

```
TASK-1 (字段API) ──┐
                   ├──> TASK-3 (实时数据API) ──> TASK-4 (批量API)
TASK-2 (Schema) ───┘                                │
                                                     │
TASK-6 (前端API) ──┐                                │
                   ├──> TASK-8 (动态组件) ──────────┤
TASK-7 (扩展API) ──┘         │                      │
                             │                      │
                    TASK-9 (Store) ─────────────────┤
                                                     │
                                                     ▼
                                            TASK-10 (页面集成)
                                                     │
                                                     ▼
TASK-11 (焊机配置) ──┐                              │
                     ├──> TASK-13 (API测试) ────────┤
TASK-12 (传感器配置)─┘         │                    │
                               │                    │
                      TASK-14 (组件测试) ───────────┤
                                                     │
                                                     ▼
                                            TASK-15 (E2E测试)
```

## 时间估算

- **阶段 1 (后端)**: 18h（包含性能优化）
- **阶段 2 (前端)**: 19h（包含性能优化）
- **阶段 3 (配置测试)**: 7h
- **总计**: 44h (约 5.5 个工作日)

### 最小可行版本（MVP）
如果时间紧张，可以先实现核心功能，性能优化后续迭代：
- **阶段 1 (核心后端)**: 10h（TASK-1 到 TASK-5）
- **阶段 2 (核心前端)**: 11h（TASK-6 到 TASK-10）
- **阶段 3 (配置测试)**: 7h
- **MVP 总计**: 28h (约 3.5 个工作日)

### 性能优化版本（推荐）
包含所有性能优化功能：
- **总计**: 44h (约 5.5 个工作日)

## 风险评估

### 高风险
- TDengine 查询性能可能不达标 → 需要优化查询或添加缓存

### 中风险
- 现有代码兼容性问题 → 需要充分测试
- 字段配置复杂度增加 → 需要提供配置工具

### 低风险
- 前端渲染性能 → 已有虚拟滚动方案
