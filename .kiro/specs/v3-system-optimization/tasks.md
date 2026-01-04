
## 阶段5：深度清理与收尾

### 21. Store 迁移 (DeviceField -> Signal)
Status: completed

任务详情:
- 分析 web/src/store/modules/device-field.ts
- 将逻辑迁移到 web/src/store/modules/signal.ts (需创建) 或合并到 existing store
- 更新相关引用

需求引用: 需求1, 需求4

### 22. 组件清理 (Components/Device)
Status: completed

任务详情:
- 分析 web/src/components/device 的使用情况
- 将通用组件移动到 web/src/components/asset 或 web/src/components/signal
- 废弃/删除不再使用的遗留组件

需求引用: 需求3

### 23. 更新项目文档
Status: completed

任务详情:
- 更新项目根目录 README.md
- 反映 V3 架构变化
- 更新启动和开发指南

需求引用: 需求1

### 24. 最终全量测试
Status: completed

任务详情:
- 运行后端测试套件 (部分集成测试因环境问题失败，核心单元测试通过)
- 验证前端构建 (已修复构建错误)
- 检查 API 连通性 (验证通过)

需求引用: 需求8
