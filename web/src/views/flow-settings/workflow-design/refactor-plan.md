# 工作流设计功能拆分规划

## 📋 概述

基于对当前 `index.vue` 文件（2052行）的完整分析，制定以下功能拆分规划，将单一大文件重构为模块化的组件架构。

## 📁 目录结构规划

```
workflow-design/
├── index.vue                    # 主入口文件（简化版，约200行）
├── components/                  # 组件目录
│   ├── Canvas/                 # 画布相关组件
│   │   ├── WorkflowCanvas.vue  # 主画布组件
│   │   ├── CanvasGrid.vue      # 网格背景
│   │   ├── CanvasToolbar.vue   # 画布工具栏（撤销、重做、缩放等）
│   │   └── CanvasControls.vue  # 缩放控制组件
│   ├── Nodes/                  # 节点相关组件
│   │   ├── NodeLibrary.vue     # 左侧节点库
│   │   ├── WorkflowNode.vue    # 通用工作流节点组件
│   │   ├── NodeTypes/          # 特定节点类型组件
│   │   │   ├── StartNode.vue   # 开始节点
│   │   │   ├── EndNode.vue     # 结束节点
│   │   │   ├── ProcessNode.vue # 处理节点
│   │   │   ├── ConditionNode.vue # 条件节点
│   │   │   ├── ApiNode.vue     # API节点
│   │   │   ├── DatabaseNode.vue # 数据库节点
│   │   │   ├── TimerNode.vue   # 定时器节点
│   │   │   └── index.js        # 节点类型导出
│   │   └── NodeProperties.vue  # 节点属性配置面板
│   ├── Connections/            # 连接相关组件
│   │   ├── ConnectionLine.vue  # 连接线组件
│   │   ├── ConnectionPoint.vue # 连接点组件
│   │   ├── TempConnection.vue  # 临时连接线
│   │   └── ConnectionManager.vue # 连接管理器
│   ├── UI/                     # 通用UI组件
│   │   ├── ContextMenu.vue     # 右键菜单
│   │   ├── SearchPanel.vue     # 搜索面板
│   │   ├── PropertiesDrawer.vue # 属性抽屉
│   │   └── StatusIndicator.vue # 状态指示器
│   └── Layout/                 # 布局组件
│       ├── LeftToolbar.vue     # 左侧工具栏
│       ├── WorkflowHeader.vue  # 工作流头部
│       └── RightSidebar.vue    # 右侧边栏
├── composables/                # 组合式函数（业务逻辑）
│   ├── useCanvas.js           # 画布操作（缩放、平移、拖拽）
│   ├── useNodes.js            # 节点管理（增删改查、选择）
│   ├── useConnections.js      # 连接管理（创建、删除、验证）
│   ├── useDragDrop.js         # 拖拽功能（节点拖拽、画布拖拽）
│   ├── useHistory.js          # 历史记录（撤销、重做）
│   ├── useKeyboard.js         # 键盘快捷键
│   ├── useContextMenu.js      # 右键菜单逻辑
│   ├── useSelection.js        # 选择管理（单选、多选）
│   └── useWorkflow.js         # 工作流管理（保存、导入、导出）
├── utils/                      # 工具函数
│   ├── nodeTypes.js           # 节点类型定义和配置
│   ├── pathCalculator.js      # 贝塞尔曲线路径计算
│   ├── gridUtils.js           # 网格工具（对齐、吸附）
│   ├── coordinateUtils.js     # 坐标转换工具
│   ├── validationUtils.js     # 连接验证工具
│   └── exportUtils.js         # 导入导出工具
├── stores/                     # 状态管理（Pinia）
│   ├── workflowStore.js       # 工作流全局状态
│   ├── canvasStore.js         # 画布状态（缩放、偏移）
│   ├── nodeStore.js           # 节点状态管理
│   ├── connectionStore.js     # 连接状态管理
│   └── selectionStore.js      # 选择状态管理
├── styles/                     # 样式文件
│   ├── variables.scss         # CSS变量定义
│   ├── mixins.scss           # 样式混入
│   ├── components.scss        # 组件通用样式
│   ├── animations.scss        # 动画定义
│   └── responsive.scss        # 响应式样式
└── types/                      # TypeScript类型定义
    ├── node.ts               # 节点相关类型
    ├── connection.ts         # 连接相关类型
    ├── workflow.ts           # 工作流类型
    └── canvas.ts             # 画布类型
```

## 🎯 功能模块详细划分

### 1. 画布模块 (Canvas)
**职责**: 画布渲染、缩放、平移、网格显示
- **WorkflowCanvas.vue** (约150行): 主画布容器，处理鼠标事件
- **CanvasGrid.vue** (约50行): 网格背景渲染
- **CanvasToolbar.vue** (约100行): 工具栏按钮（撤销、重做、适应屏幕等）
- **useCanvas.js** (约200行): 画布操作逻辑

### 2. 节点模块 (Nodes)
**职责**: 节点渲染、拖拽、属性配置
- **NodeLibrary.vue** (约150行): 左侧节点库，分类展示
- **WorkflowNode.vue** (约200行): 通用节点组件
- **NodeTypes/** (每个约50-100行): 特定类型节点组件
- **NodeProperties.vue** (约300行): 属性配置面板
- **useNodes.js** (约250行): 节点管理逻辑

### 3. 连接模块 (Connections)
**职责**: 连接线渲染、连接创建、路径计算
- **ConnectionLine.vue** (约100行): 连接线SVG渲染
- **ConnectionPoint.vue** (约80行): 连接点组件
- **TempConnection.vue** (约60行): 临时连接线
- **useConnections.js** (约300行): 连接管理逻辑

### 4. 交互模块 (Interactions)
**职责**: 用户交互处理
- **useDragDrop.js** (约200行): 拖拽功能实现
- **useKeyboard.js** (约100行): 键盘快捷键
- **useContextMenu.js** (约150行): 右键菜单逻辑
- **useHistory.js** (约100行): 撤销重做功能

### 5. 数据管理模块 (Data)
**职责**: 状态管理、数据持久化
- **stores/** (每个约100-150行): Pinia状态管理
- **utils/** (每个约50-100行): 工具函数
- **types/** (每个约50行): TypeScript类型定义

## 💡 拆分优势

### 开发效率
1. **模块化开发**: 每个功能独立，便于并行开发
2. **代码复用**: 组件可在其他页面复用
3. **易于测试**: 单元测试更容易编写和维护
4. **团队协作**: 减少代码冲突，提高协作效率

### 代码质量
1. **单一职责**: 每个文件职责明确
2. **可读性强**: 代码结构清晰，易于理解
3. **可维护性**: 修改某个功能不影响其他模块
4. **可扩展性**: 新增功能更容易实现

### 性能优化
1. **按需加载**: 可实现组件懒加载
2. **代码分割**: 减少初始包大小
3. **缓存优化**: 独立模块便于缓存

## 🚀 实施计划

### 阶段1: 基础架构搭建 (1-2天)
- [ ] 创建目录结构
- [ ] 设置基础组件框架
- [ ] 配置状态管理
- [ ] 建立类型定义

### 阶段2: 画布模块拆分 (2-3天)
- [ ] 拆分画布组件
- [ ] 实现缩放平移功能
- [ ] 网格背景组件
- [ ] 工具栏组件

### 阶段3: 节点模块拆分 (3-4天)
- [ ] 节点库组件
- [ ] 通用节点组件
- [ ] 特定节点类型组件
- [ ] 节点属性面板

### 阶段4: 连接模块拆分 (2-3天)
- [ ] 连接线组件
- [ ] 连接点组件
- [ ] 连接创建逻辑
- [ ] 路径计算优化

### 阶段5: 交互功能完善 (2天)
- [ ] 拖拽功能优化
- [ ] 键盘快捷键
- [ ] 右键菜单
- [ ] 历史记录

### 阶段6: 样式和优化 (1-2天)
- [ ] 样式文件整理
- [ ] 响应式优化
- [ ] 性能优化
- [ ] 测试和调试

## 📝 注意事项

1. **向后兼容**: 确保重构后功能完全一致
2. **渐进式迁移**: 可以逐步迁移，不影响现有功能
3. **测试覆盖**: 每个模块都需要充分测试
4. **文档更新**: 及时更新开发文档
5. **性能监控**: 重构后需要监控性能变化

## 🎯 预期收益

- **代码行数**: 从2052行拆分为多个小文件，平均每个文件50-200行
- **维护成本**: 降低50%以上
- **开发效率**: 提升30%以上
- **代码质量**: 显著提升可读性和可维护性
- **团队协作**: 支持多人并行开发

---

**请确认此拆分规划是否符合您的期望，我将开始实施第一阶段的工作。**