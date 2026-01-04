# 需求文档 - V3系统优化整合

## 项目介绍

本规范定义了工业AI数据平台V3版本的系统优化整合需求。基于已完成的V3规格设计（industrial-ai-platform-upgrade-v3），本阶段专注于**实际执行代码整合、遗留清理、API统一和测试完善**，将设计转化为可运行的生产代码。

## 当前状态

### 已有设计文档
- `.kiro/specs/industrial-ai-platform-upgrade-v3/requirements.md` - 完整需求定义
- `.kiro/specs/industrial-ai-platform-upgrade-v3/design.md` - 架构设计方案
- `.kiro/specs/industrial-ai-platform-upgrade-v3/tasks.md` - 42项任务清单
- `docs/Industrial AI Data Platform/V3_UPGRADE_ANALYSIS.md` - 升级分析报告

### 待执行工作
根据V3任务清单，共8个阶段42项任务，本spec聚焦于**阶段1-3的核心整合工作**：
- 阶段1：代码整合（8项任务）
- 阶段2：数据库迁移（5项任务）
- 阶段3：API整合（6项任务）

## 术语表

- **Platform_Core**: 整合后的核心平台模块，包含asset、signal、metadata、timeseries、ingestion、realtime子模块
- **AI_Engine**: AI引擎模块，包含model、inference、feature、decision子模块
- **Legacy_Code**: 待清理的遗留代码，包括platform_v2目录和device相关命名
- **Unified_API**: 整合后的v4版本API
- **Migration_Script**: 数据库迁移脚本

## 需求

### 需求1：platform_v2模块整合

**用户故事：** 作为开发者，我希望platform_v2的代码被整合到platform_core，以便消除重复代码和统一模块结构。

#### 验收标准

1. WHEN整合完成时，platform_v2/metadata目录的代码应迁移到platform_core/metadata
2. WHEN整合完成时，platform_v2/timeseries目录的代码应迁移到platform_core/timeseries
3. WHEN整合完成时，platform_v2/ingestion的功能应合并到platform_core/ingestion
4. WHEN整合完成时，所有引用platform_v2的import语句应更新为platform_core
5. WHEN整合完成时，platform_v2目录应被删除
6. THE Platform_Core SHALL提供统一的__init__.py导出所有公共接口

### 需求2：创建asset和signal模块

**用户故事：** 作为开发者，我希望有独立的asset和signal模块，以便清晰管理资产和信号相关的业务逻辑。

#### 验收标准

1. THE Platform_Core SHALL包含asset子模块，定义Asset和AssetCategory模型
2. THE Platform_Core SHALL包含signal子模块，定义SignalDefinition模型
3. WHEN创建asset模块时，应包含models.py、service.py、repository.py文件
4. WHEN创建signal模块时，应包含models.py、service.py、repository.py文件
5. THE asset模块 SHALL从app/models/platform_upgrade.py迁移相关模型定义
6. THE signal模块 SHALL从app/models/platform_upgrade.py迁移相关模型定义

### 需求3：ai_engine子模块重命名

**用户故事：** 作为开发者，我希望ai_engine的子模块命名更简洁一致，以便提高代码可读性。

#### 验收标准

1. WHEN重命名完成时，feature_hub目录应重命名为feature
2. WHEN重命名完成时，decision_engine目录应重命名为decision
3. WHEN重命名完成时，model_registry和model_storage应合并为model目录
4. WHEN重命名完成时，所有引用旧模块名的import语句应更新
5. THE AI_Engine SHALL保持所有现有功能正常工作

### 需求4：统一命名规范

**用户故事：** 作为开发者，我希望代码中的命名统一使用asset/signal，以便消除device/field的混用。

#### 验收标准

1. WHEN命名统一完成时，所有device_type相关命名应改为asset_category
2. WHEN命名统一完成时，所有device_field相关命名应改为signal_definition
3. WHEN命名统一完成时，所有device_info相关命名应改为asset
4. WHEN命名统一完成时，所有field_value相关命名应改为signal_value
5. THE Platform_Core SHALL提供命名映射文档，记录所有变更

### 需求5：数据库Schema迁移

**用户故事：** 作为DBA，我希望数据库表名和列名与代码命名一致，以便降低维护成本。

#### 验收标准

1. THE Migration_Script SHALL将device_types表重命名为asset_categories
2. THE Migration_Script SHALL将device_fields表重命名为signal_definitions
3. THE Migration_Script SHALL将device_info表重命名为assets
4. THE Migration_Script SHALL更新所有相关的外键约束
5. THE Migration_Script SHALL更新所有相关的索引
6. THE Platform_Core SHALL提供回滚脚本，支持迁移失败时恢复
7. IF迁移失败，THEN Platform_Core SHALL自动执行回滚并报告错误

### 需求6：创建统一v4 API

**用户故事：** 作为前端开发者，我希望使用统一的v4 API，以便减少API版本混乱。

#### 验收标准

1. THE Unified_API SHALL整合v2和v3的所有功能到/api/v4/路径
2. THE Unified_API SHALL提供统一的响应格式，包含code、message、data、meta字段
3. THE Unified_API SHALL提供统一的错误处理和错误码
4. THE Unified_API SHALL提供统一的分页规范
5. WHEN v4 API发布时，应提供v2/v3到v4的兼容层
6. THE Unified_API SHALL遵循OpenAPI 3.1规范

### 需求7：清理重复服务代码

**用户故事：** 作为开发者，我希望app/services中的重复代码被清理，以便明确服务层职责。

#### 验收标准

1. WHEN清理完成时，app/services中与platform_core重复的服务应被移除
2. WHEN清理完成时，app/services应只保留API层的薄封装
3. THE Platform_Core SHALL承担所有核心业务逻辑
4. WHEN清理完成时，所有调用点应更新为使用platform_core的服务

### 需求8：测试验证

**用户故事：** 作为QA工程师，我希望整合后的代码有完整的测试覆盖，以便确保无回归问题。

#### 验收标准

1. WHEN每个阶段完成时，应运行现有测试确保无回归
2. THE Platform_Core SHALL为新创建的模块提供单元测试
3. THE Platform_Core SHALL提供集成测试验证模块间交互
4. IF测试失败，THEN整合工作应暂停并修复问题
5. THE Platform_Core SHALL达到80%以上的代码覆盖率

