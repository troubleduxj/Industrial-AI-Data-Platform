# 工作流管理模块

## 概述

工作流管理模块提供可视化的流程编排能力，支持设备监控、报警处理、数据采集、维护保养等业务场景的自动化流程设计和执行。

## 功能特性

### 1. 工作流管理
- 工作流的创建、编辑、删除
- 工作流启用/禁用
- 工作流发布/取消发布
- 工作流复制
- 工作流导入/导出

### 2. 可视化设计器
- 拖拽式节点编辑
- 多种节点类型支持
- 节点连接线绘制
- 画布缩放/平移/网格对齐
- 撤销/重做历史记录
- 工作流验证

### 3. 节点类型

| 类别 | 节点 | 说明 |
|------|------|------|
| 基础节点 | start | 开始节点 |
| | end | 结束节点 |
| | process | 处理节点 |
| | transform | 数据转换 |
| | filter | 数据过滤 |
| 控制节点 | condition | 条件判断 |
| | loop | 循环 |
| | timer | 定时器 |
| | parallel | 并行执行 |
| | merge | 合并 |
| | delay | 延时 |
| 集成节点 | api | API调用 |
| | database | 数据库操作 |

### 4. 工作流类型

| 类型代码 | 名称 | 应用场景 |
|----------|------|----------|
| device_monitor | 设备监控流程 | 实时监控设备状态，异常时触发报警 |
| alarm_process | 报警处理流程 | 自动处理报警，通知相关人员 |
| data_collection | 数据采集流程 | 定时采集设备数据 |
| maintenance | 维护保养流程 | 根据设备状态生成维护提醒 |
| custom | 自定义流程 | 用户自定义业务流程 |

### 5. 触发方式

| 触发类型 | 说明 |
|----------|------|
| manual | 手动触发 |
| schedule | 定时触发（支持Cron表达式） |
| event | 事件触发 |
| webhook | Webhook触发 |

## 数据库表结构

### t_workflow - 工作流定义表
存储工作流的基本信息、节点定义、连接定义等。

### t_workflow_execution - 工作流执行记录表
记录每次工作流执行的状态、结果、耗时等信息。

### t_workflow_node_execution - 节点执行记录表
记录每个节点的执行详情。

### t_workflow_template - 工作流模板表
存储预置的工作流模板。

### t_workflow_schedule - 工作流调度配置表
存储定时执行的调度配置。

## 部署步骤

### 1. 执行数据库迁移

```bash
# 方式一：使用Python脚本
python database/migrations/workflow/apply_workflow.py

# 方式二：手动执行SQL
mysql -u root -p device_monitor < database/migrations/workflow/001_create_workflow_tables.sql
mysql -u root -p device_monitor < database/migrations/workflow/002_insert_workflow_menu.sql
mysql -u root -p device_monitor < database/migrations/workflow/003_insert_workflow_templates.sql
```

### 2. 重启后端服务

```bash
# 重启后端服务以加载新的API路由
python run.py
```

### 3. 刷新前端页面

刷新浏览器，重新登录以获取新的菜单权限。

## API 接口

### 工作流管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v2/workflows | 获取工作流列表 |
| GET | /api/v2/workflows/{id} | 获取工作流详情 |
| POST | /api/v2/workflows | 创建工作流 |
| PUT | /api/v2/workflows/{id} | 更新工作流 |
| DELETE | /api/v2/workflows/{id} | 删除工作流 |
| PUT | /api/v2/workflows/{id}/toggle | 启用/禁用工作流 |
| POST | /api/v2/workflows/{id}/publish | 发布工作流 |
| POST | /api/v2/workflows/{id}/duplicate | 复制工作流 |

### 工作流设计

| 方法 | 路径 | 说明 |
|------|------|------|
| PUT | /api/v2/workflows/{id}/design | 保存工作流设计 |
| POST | /api/v2/workflows/{id}/validate | 验证工作流 |

### 工作流执行

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v2/workflows/{id}/execute | 执行工作流 |
| GET | /api/v2/workflows/{id}/executions | 获取执行记录 |
| GET | /api/v2/workflows/executions/{execution_id} | 获取执行详情 |
| POST | /api/v2/workflows/executions/{execution_id}/cancel | 取消执行 |

### 工作流模板

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v2/workflows/templates | 获取模板列表 |
| GET | /api/v2/workflows/templates/{id} | 获取模板详情 |
| POST | /api/v2/workflows/templates/{id}/use | 使用模板创建工作流 |
| POST | /api/v2/workflows/{id}/save-as-template | 保存为模板 |

### 导入导出

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v2/workflows/{id}/export | 导出工作流 |
| POST | /api/v2/workflows/import | 导入工作流 |

## 预置模板

系统预置了以下工作流模板：

1. **设备状态监控流程** - 监控设备状态，异常时触发报警
2. **报警自动处理流程** - 自动处理报警，创建工单
3. **定时数据采集流程** - 定时采集设备数据
4. **设备维护提醒流程** - 自动生成维护提醒
5. **简单审批流程** - 通用审批流程

## 注意事项

1. 工作流必须包含开始节点和结束节点
2. 工作流发布前需要通过验证
3. 已发布的工作流才能执行
4. 执行中的工作流可以取消
5. 定时触发需要配置调度任务

## 后续扩展

- [ ] 集成Celery实现异步任务队列
- [ ] 支持更多节点类型（邮件、短信、钉钉等）
- [ ] 工作流版本管理
- [ ] 执行日志可视化
- [ ] 性能监控和统计
