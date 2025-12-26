# 快速启动指南

## 🚀 立即开始

### 方式 1: 使用 Kiro AI 助手（推荐）

直接在 Kiro 对话框中输入：

```
请帮我实现 .kiro/specs/device-dynamic-params 这个 Spec
```

Kiro 会自动：
1. 读取需求文档（requirements.md）
2. 读取设计文档（design.md）
3. 读取任务列表（tasks.md）
4. 按顺序实施所有任务

### 方式 2: 逐个任务实施

#### 第一步：后端 API 开发

```
请帮我实现 TASK-1: 创建设备字段 API 路由
参考文件: .kiro/specs/device-dynamic-params/tasks.md
```

完成后继续：

```
请帮我实现 TASK-2: 创建设备字段 Schema
```

#### 第二步：前端组件开发

```
请帮我实现 TASK-6: 创建设备字段 API 接口
```

#### 第三步：数据配置与测试

```
请帮我实现 TASK-11: 配置焊机监测字段
```

### 方式 3: 分阶段实施

#### 阶段 1: 后端开发（1-2天）

```
请帮我完成 .kiro/specs/device-dynamic-params 的阶段1（后端API开发）
包括 TASK-1 到 TASK-5
```

#### 阶段 2: 前端开发（1-2天）

```
请帮我完成 .kiro/specs/device-dynamic-params 的阶段2（前端组件开发）
包括 TASK-6 到 TASK-10
```

#### 阶段 3: 测试上线（0.5-1天）

```
请帮我完成 .kiro/specs/device-dynamic-params 的阶段3（数据配置与测试）
包括 TASK-11 到 TASK-15
```

## 📋 实施前检查清单

在开始实施前，请确认：

- [ ] 已阅读 requirements.md，理解所有验收标准
- [ ] 已阅读 design.md，理解架构设计和正确性属性
- [ ] 已阅读 tasks.md，了解任务依赖关系
- [ ] 后端开发环境已就绪（Python 3.9+, FastAPI）
- [ ] 前端开发环境已就绪（Node.js, Vue 3, TypeScript）
- [ ] 数据库已就绪（PostgreSQL, TDengine）
- [ ] 已备份现有代码

## 🎯 每个任务的验证步骤

### TASK-1 验证

```bash
# 启动后端服务
cd app
python run.py

# 测试 API
curl http://localhost:8001/api/v2/device-fields/monitoring-keys/WELD_MACHINE
```

### TASK-3 验证

```bash
# 测试实时数据接口
curl http://localhost:8001/api/v2/devices/WM001/realtime-with-config
```

### TASK-8 验证

```bash
# 启动前端服务
cd web
pnpm dev

# 访问 http://localhost:3000
# 检查组件是否正确渲染
```

### TASK-10 验证

```bash
# 访问实时监测页面
# http://localhost:3000/device-monitor/monitor

# 验证：
# 1. 设备卡片是否显示
# 2. 参数是否动态渲染
# 3. 不同设备类型参数是否不同
```

## 📊 进度跟踪

使用以下命令查看进度：

```bash
# 查看所有任务
cat .kiro/specs/device-dynamic-params/tasks.md | grep "^### TASK-"

# 查看已完成任务（手动更新 README.md 中的复选框）
cat .kiro/specs/device-dynamic-params/README.md | grep "\[x\]"
```

## 🐛 调试技巧

### 后端调试

```python
# 在代码中添加日志
import logging
logger = logging.getLogger(__name__)

logger.info(f"查询字段配置: {device_type_code}")
logger.debug(f"查询结果: {fields}")
```

### 前端调试

```typescript
// 在组件中添加日志
console.log('监测字段配置:', monitoringFields)
console.log('实时数据:', realtimeData)
```

### 数据库调试

```sql
-- 检查字段配置
SELECT * FROM t_device_field 
WHERE device_type_code = 'WELD_MACHINE' 
  AND is_monitoring_key = true;

-- 检查 TDengine 数据
SELECT * FROM tb_wm001 ORDER BY ts DESC LIMIT 10;
```

## 🎉 完成标准

当你看到以下结果时，说明实施成功：

1. ✅ 访问实时监测页面，看到设备卡片
2. ✅ 焊机显示 4 个参数（预设电流、预设电压、焊接电流、焊接电压）
3. ✅ 压力传感器显示 3 个参数（压力、温度、振动）
4. ✅ 参数带有图标和颜色
5. ✅ 数值正确格式化（保留2位小数）
6. ✅ 所有测试通过
7. ✅ 性能达标（响应时间 < 500ms）

## 📞 获取帮助

如果遇到问题，可以：

1. **查看设计文档**: `cat .kiro/specs/device-dynamic-params/design.md`
2. **查看任务详情**: `cat .kiro/specs/device-dynamic-params/tasks.md`
3. **查看方案文档**: `cat docs/device_test/设备类型动态参数展示方案.md`
4. **询问 Kiro**: "我在实施 TASK-X 时遇到了 [问题描述]，如何解决？"

## 🔄 迭代优化

完成基础实施后，可以考虑以下优化：

1. **添加字段分组**: 支持按类别分组显示参数
2. **添加阈值告警**: 参数超过阈值时高亮显示
3. **添加图表展示**: 支持配置参数的图表类型
4. **添加配置界面**: 提供可视化的字段配置管理界面
5. **添加 Redis 缓存**: 优化后端查询性能

---

**准备好了吗？让我们开始吧！** 🚀

在 Kiro 对话框中输入：

```
请帮我实现 .kiro/specs/device-dynamic-params 这个 Spec，从 TASK-1 开始
```
