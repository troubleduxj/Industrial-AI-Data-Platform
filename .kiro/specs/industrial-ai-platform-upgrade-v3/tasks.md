# 任务清单 - 工业AI数据平台升级 V3

## 任务概览

| 阶段 | 任务数 | 预估工时 | 优先级 |
|------|--------|----------|--------|
| 阶段1：代码整合 | 8 | 2-3周 | P0 |
| 阶段2：数据库迁移 | 5 | 1-2周 | P0 |
| 阶段3：API整合 | 6 | 2-3周 | P0 |
| 阶段4：前端整合 | 6 | 2-3周 | P1 |
| 阶段5：测试完善 | 5 | 1-2周 | P1 |
| 阶段6：文档建设 | 4 | 1周 | P1 |
| 阶段7：可观测性 | 4 | 1-2周 | P2 |
| 阶段8：高级功能 | 4 | 2-4周 | P2 |

---

## 阶段1：代码整合

### 1. platform_v2整合到platform_core
Status: not started

任务详情:
- 将platform_v2/metadata迁移到platform_core/metadata
- 将platform_v2/timeseries迁移到platform_core/timeseries
- 合并platform_v2/ingestion到platform_core/ingestion
- 更新所有import路径
- 删除platform_v2目录

需求引用: 需求1, 需求4

### 2. ai_engine子模块重命名
Status: not started

任务详情:
- 将feature_hub重命名为feature
- 将decision_engine重命名为decision
- 将model_registry和model_storage合并为model
- 更新所有import路径

需求引用: 需求4

### 3. 创建platform_core/asset模块
Status: not started

任务详情:
- 创建asset/models.py定义Asset和AssetCategory模型
- 创建asset/service.py实现AssetService
- 创建asset/repository.py实现数据访问层
- 从app/models/platform_upgrade.py迁移相关模型

需求引用: 需求1, 需求4

### 4. 创建platform_core/signal模块
Status: not started

任务详情:
- 创建signal/models.py定义SignalDefinition模型
- 创建signal/service.py实现SignalService
- 创建signal/repository.py实现数据访问层
- 从app/models/platform_upgrade.py迁移相关模型

需求引用: 需求1, 需求4

### 5. 清理app/services重复代码
Status: not started

任务详情:
- 识别app/services中与platform_core重复的服务
- 将业务逻辑迁移到platform_core
- 保留app/services作为API层的薄封装
- 更新所有调用点

需求引用: 需求1

### 6. 统一命名规范（device→asset）
Status: not started

任务详情:
- 全局搜索替换device_type为asset_category
- 全局搜索替换device_field为signal_definition
- 全局搜索替换device_info为asset
- 更新所有变量名、函数名、类名

需求引用: 需求1

### 7. 统一命名规范（field→signal）
Status: not started

任务详情:
- 全局搜索替换field_definition为signal_definition
- 全局搜索替换field_value为signal_value
- 更新所有相关代码

需求引用: 需求1

### 8. 检查点 - 代码整合完成
Status: not started

任务详情:
- 验证所有模块可正常导入
- 运行现有测试确保无回归
- 检查循环依赖
- 生成模块依赖图

需求引用: 需求1, 需求4

---

## 阶段2：数据库迁移

### 9. 创建数据库迁移脚本
Status: not started

任务详情:
- 创建migrations/v3_schema_rename.sql
- 编写表重命名SQL
- 编写列重命名SQL
- 编写外键更新SQL
- 编写索引更新SQL

需求引用: 需求5

### 10. 创建数据库回滚脚本
Status: not started

任务详情:
- 创建migrations/v3_schema_rollback.sql
- 编写反向重命名SQL
- 测试回滚流程

需求引用: 需求5

### 11. 更新ORM模型
Status: not started

任务详情:
- 更新app/models/platform_upgrade.py中的表名
- 更新所有外键引用
- 更新Tortoise ORM配置

需求引用: 需求5

### 12. 执行数据库迁移
Status: not started

任务详情:
- 在测试环境执行迁移
- 验证数据完整性
- 在生产环境执行迁移
- 验证应用正常运行

需求引用: 需求5

### 13. 检查点 - 数据库迁移完成
Status: not started

任务详情:
- 验证所有表已重命名
- 验证所有外键正常
- 验证所有索引正常
- 生成数据库ER图

需求引用: 需求5

---

## 阶段3：API整合

### 14. 创建v4 API基础结构
Status: not started

任务详情:
- 创建app/api/v4/__init__.py
- 创建统一响应格式
- 创建统一异常处理
- 创建统一分页规范

需求引用: 需求2

### 15. 实现v4资产管理API
Status: not started

任务详情:
- 创建app/api/v4/assets.py
- 创建app/api/v4/categories.py
- 创建app/api/v4/signals.py
- 整合v3相关API功能

需求引用: 需求2

### 16. 实现v4 AI引擎API
Status: not started

任务详情:
- 创建app/api/v4/models.py
- 创建app/api/v4/features.py
- 创建app/api/v4/decisions.py
- 整合v3相关API功能

需求引用: 需求2

### 17. 实现v4系统管理API
Status: not started

任务详情:
- 创建app/api/v4/system.py
- 创建app/api/v4/ingestion.py
- 创建app/api/v4/timeseries.py
- 整合v3相关API功能

需求引用: 需求2

### 18. 创建API兼容层
Status: not started

任务详情:
- 创建v2到v4的路由映射
- 创建v3到v4的路由映射
- 添加废弃警告响应头
- 编写迁移指南文档

需求引用: 需求2

### 19. 检查点 - API整合完成
Status: not started

任务详情:
- 验证所有v4 API正常工作
- 验证兼容层正常工作
- 生成OpenAPI文档
- 运行API测试

需求引用: 需求2

---

## 阶段4：前端整合

### 20. 创建v4 API客户端
Status: not started

任务详情:
- 创建web/src/api/v4/index.js
- 创建web/src/api/v4/assets.js
- 创建web/src/api/v4/ai.js
- 创建web/src/api/v4/system.js

需求引用: 需求3

### 21. 迁移资产管理页面
Status: not started

任务详情:
- 重构web/src/views/assets/为统一风格
- 移除device相关命名
- 使用v4 API
- 更新路由配置

需求引用: 需求3

### 22. 归档遗留页面
Status: not started

任务详情:
- 创建web/src/views/legacy/目录
- 移动旧设备监控页面
- 移动旧设备类型页面
- 添加废弃标记

需求引用: 需求3

### 23. 统一组件库
Status: not started

任务详情:
- 整理web/src/components/目录
- 移除重复组件
- 统一组件命名规范
- 更新组件导出

需求引用: 需求3

### 24. 更新导航菜单
Status: not started

任务详情:
- 移除旧设备监控菜单
- 更新菜单结构
- 添加新功能入口
- 更新菜单权限配置

需求引用: 需求3

### 25. 检查点 - 前端整合完成
Status: not started

任务详情:
- 验证所有页面正常访问
- 验证所有功能正常工作
- 检查控制台无错误
- 运行前端测试

需求引用: 需求3

---

## 阶段5：测试完善

### 26. 补充单元测试
Status: not started

任务详情:
- 为platform_core模块添加单元测试
- 为ai_engine模块添加单元测试
- 达到80%代码覆盖率
- 配置覆盖率报告

需求引用: 需求6

### 27. 添加集成测试
Status: not started

任务详情:
- 创建tests/integration/目录
- 添加资产管理流程测试
- 添加AI推理流程测试
- 添加数据采集流程测试

需求引用: 需求6

### 28. 添加端到端测试
Status: not started

任务详情:
- 配置Playwright测试环境
- 添加关键用户流程测试
- 添加页面截图对比
- 配置测试报告

需求引用: 需求6

### 29. 配置CI/CD流水线
Status: not started

任务详情:
- 创建.github/workflows/test.yml
- 配置自动运行测试
- 配置代码质量检查
- 配置自动部署

需求引用: 需求6

### 30. 检查点 - 测试完善完成
Status: not started

任务详情:
- 验证所有测试通过
- 验证覆盖率达标
- 验证CI/CD正常运行
- 生成测试报告

需求引用: 需求6

---

## 阶段6：文档建设

### 31. 更新README
Status: not started

任务详情:
- 重写项目介绍
- 更新功能列表
- 更新技术栈说明
- 更新快速开始指南

需求引用: 需求7

### 32. 编写架构文档
Status: not started

任务详情:
- 创建docs/architecture/目录
- 编写系统架构文档
- 编写模块设计文档
- 生成架构图

需求引用: 需求7

### 33. 生成API文档
Status: not started

任务详情:
- 配置自动生成OpenAPI文档
- 添加API使用示例
- 添加错误码说明
- 部署API文档站点

需求引用: 需求7

### 34. 编写开发者指南
Status: not started

任务详情:
- 创建docs/development/目录
- 编写开发环境搭建指南
- 编写代码规范文档
- 编写贡献指南

需求引用: 需求7

---

## 阶段7：可观测性

### 35. 集成Prometheus指标
Status: not started

任务详情:
- 安装prometheus-fastapi-instrumentator
- 添加业务指标
- 添加性能指标
- 配置指标端点

需求引用: 需求8

### 36. 配置Grafana仪表板
Status: not started

任务详情:
- 创建系统概览仪表板
- 创建API性能仪表板
- 创建业务指标仪表板
- 导出仪表板JSON

需求引用: 需求8

### 37. 添加链路追踪
Status: not started

任务详情:
- 集成OpenTelemetry
- 配置追踪导出
- 添加自定义Span
- 配置采样策略

需求引用: 需求8

### 38. 完善日志系统
Status: not started

任务详情:
- 配置结构化日志
- 添加请求ID追踪
- 配置日志级别
- 配置日志轮转

需求引用: 需求8

---

## 阶段8：高级功能

### 39. 实现多租户支持
Status: not started

任务详情:
- 创建租户模型
- 实现租户中间件
- 实现数据隔离
- 添加租户管理API

需求引用: 需求9

### 40. 实现插件系统
Status: not started

任务详情:
- 定义插件接口
- 实现插件加载器
- 创建示例插件
- 编写插件开发文档

需求引用: 需求10

### 41. 性能优化
Status: not started

任务详情:
- 添加Redis缓存
- 优化数据库查询
- 添加连接池配置
- 进行压力测试

需求引用: 需求9

### 42. 最终检查点 - V3升级完成
Status: not started

任务详情:
- 验证所有功能正常
- 验证所有测试通过
- 验证文档完整
- 发布V3版本

需求引用: 全部需求

---

## 注意事项

1. **优先级说明**
   - P0: 必须完成，阻塞后续任务
   - P1: 重要功能，应尽快完成
   - P2: 增强功能，可延后

2. **依赖关系**
   - 阶段2依赖阶段1完成
   - 阶段3依赖阶段1、2完成
   - 阶段4依赖阶段3完成
   - 阶段5-8可并行进行

3. **风险控制**
   - 每个阶段结束前必须完成检查点任务
   - 数据库迁移前必须备份
   - API变更必须保持向后兼容

4. **测试要求**
   - 每个任务完成后运行相关测试
   - 检查点任务必须运行全量测试
   - 保持测试覆盖率不下降

