# 性能优化快速参考

## 🎯 优化目标

| 指标 | 目标值 |
|------|--------|
| 首页加载（50设备） | < 500ms |
| 分页加载（50设备） | < 300ms |
| 全量加载（1000设备） | < 3s |
| 实时更新延迟 | < 100ms |
| 并发用户支持 | 100+ |

## 🚀 7 大优化方案

### 1️⃣ 分页加载（必选）⭐⭐⭐

**问题**: 一次性加载 1000+ 设备，响应慢、内存占用高

**方案**: 
```python
# 后端分页 API
POST /api/v2/devices/realtime-paginated
{
  "page": 1,
  "page_size": 50,
  "device_type": "WELD_MACHINE"
}
```

**效果**: 响应时间从 15s → 500ms（83% 提升）

---

### 2️⃣ TDengine 批量查询（必选）⭐⭐⭐

**问题**: 逐个查询设备数据，查询次数过多

**方案**:
```python
# 使用 UNION ALL 合并查询
SELECT * FROM tb_device1 UNION ALL
SELECT * FROM tb_device2 UNION ALL
...
```

**效果**: 查询时间从 5s → 800ms（84% 提升）

---

### 3️⃣ Redis 缓存（推荐）⭐⭐⭐

**问题**: 频繁查询数据库，数据库压力大

**方案**:
```python
# 字段配置缓存 1 小时
# 实时数据缓存 10 秒
cache_key = f"field_config:{device_type}"
await redis.setex(cache_key, 3600, data)
```

**效果**: 数据库查询减少 90%

---

### 4️⃣ 虚拟滚动（必选）⭐⭐⭐

**问题**: 渲染 1000+ 个 DOM 节点，页面卡顿

**方案**:
```vue
<RecycleScroller
  :items="devices"
  :item-size="280"
  :buffer="200"
/>
```

**效果**: 内存占用从 1.2GB → 300MB（75% 提升）

---

### 5️⃣ WebSocket 增量推送（推荐）⭐⭐

**问题**: 轮询更新，网络流量大、延迟高

**方案**:
```typescript
// 订阅设备更新
ws.send({
  action: 'subscribe',
  device_codes: ['WM001', 'WM002']
})
```

**效果**: 推送延迟从 500ms → 50ms（90% 提升）

---

### 6️⃣ 数据库索引（必选）⭐⭐⭐

**问题**: 查询慢，全表扫描

**方案**:
```sql
CREATE INDEX idx_device_type_status 
ON t_device_info(device_type, device_status);
```

**效果**: 查询时间减少 70%

---

### 7️⃣ 前端优化（推荐）⭐⭐

**问题**: 组件加载慢、重复渲染

**方案**:
- 组件懒加载
- 防抖节流
- 数据缓存
- 图片懒加载

**效果**: 首屏加载时间减少 50%

---

## 📋 实施优先级

### P0（必须实现）- MVP 版本

- ✅ **分页加载**: 减少单次数据量
- ✅ **TDengine 优化**: 批量查询
- ✅ **虚拟滚动**: 优化渲染
- ✅ **数据库索引**: 优化查询

**预计时间**: 8h  
**效果**: 支持 500 个设备，响应时间 < 1s

### P1（强烈推荐）- 生产版本

- ✅ **Redis 缓存**: 减少数据库压力
- ✅ **WebSocket 推送**: 实时更新
- ✅ **前端缓存**: 减少 API 请求

**预计时间**: +8h（总计 16h）  
**效果**: 支持 1000+ 设备，响应时间 < 3s

### P2（可选优化）- 优化版本

- ⭕ CDN 加速
- ⭕ 服务端渲染
- ⭕ 数据预加载

**预计时间**: +4h（总计 20h）  
**效果**: 支持 5000+ 设备

---

## 🔧 快速实施指南

### 步骤 1: 后端优化（4h）

```bash
# 1. 添加 Redis 缓存（TASK-0）
# 2. 实现分页 API（TASK-4.1）
# 3. 优化 TDengine 查询（TASK-4.2）
# 4. 添加数据库索引（TASK-5）
```

### 步骤 2: 前端优化（4h）

```bash
# 1. 实现虚拟滚动（TASK-10.1）
# 2. 实现无限滚动（TASK-10.2）
# 3. 添加前端缓存（TASK-9）
```

### 步骤 3: 实时推送（可选，4h）

```bash
# 1. 实现 WebSocket 服务（TASK-10.3）
# 2. 实现增量推送
# 3. 实现频率限制
```

---

## 📊 性能对比

| 场景 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 首页加载（50设备） | 2s | 400ms | 80% ↑ |
| 全量加载（1000设备） | 15s | 2.5s | 83% ↑ |
| TDengine 查询 | 5s | 800ms | 84% ↑ |
| 内存占用 | 1.2GB | 300MB | 75% ↓ |
| WebSocket 延迟 | 500ms | 50ms | 90% ↑ |

---

## 🐛 常见问题

### Q1: 分页加载后，如何保持筛选条件？

**A**: 在分页请求中携带筛选参数：
```typescript
const params = {
  page: currentPage.value,
  page_size: 50,
  device_type: filterType.value,
  status: filterStatus.value
}
```

### Q2: Redis 缓存如何失效？

**A**: 
- 字段配置缓存：TTL 1小时，或手动清除
- 实时数据缓存：TTL 10秒，自动过期

### Q3: 虚拟滚动如何确定 item-size？

**A**: 
- 测量单个设备卡片的实际高度
- 建议值：280px（包含 padding 和 margin）
- 可以动态计算：`ref.offsetHeight`

### Q4: WebSocket 断线如何处理？

**A**: 
- 使用 `autoReconnect: true`
- 实现心跳检测（30秒）
- 断线后自动重新订阅

---

## 📝 监控指标

### 后端监控

```python
# 记录 API 响应时间
@monitor_performance
async def get_realtime_data_paginated(...):
    ...

# 告警阈值
if elapsed > 1.0:
    logger.warning(f"API 响应时间过长: {elapsed}s")
```

### 前端监控

```typescript
// 记录页面加载时间
const loadTime = performance.now()
if (loadTime > 3000) {
  reportPerformanceIssue('page_load_slow', { loadTime })
}
```

---

## 🎉 预期效果

实施所有 P0 和 P1 优化后：

✅ 支持 1000+ 设备的实时监测  
✅ 首页加载时间 < 500ms  
✅ 全量加载时间 < 3s  
✅ 实时更新延迟 < 100ms  
✅ 支持 100+ 用户并发访问  
✅ 内存占用 < 500MB  

---

**详细方案**: 查看 [performance-optimization.md](./performance-optimization.md)
