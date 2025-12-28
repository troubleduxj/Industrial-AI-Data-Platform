# 工业AI数据平台 V2 升级迁移指南

## 概述

本目录包含工业AI数据平台V2升级所需的所有数据库迁移脚本。

## 迁移脚本清单

| 版本 | 脚本文件 | 描述 | 数据库 |
|------|----------|------|--------|
| 001 | 001_create_platform_tables.sql | 平台核心表（资产、信号、AI模型等） | PostgreSQL |
| 002 | 002_add_platform_menus.sql | 平台菜单配置 | PostgreSQL |
| 003 | 003_create_decision_engine_tables.sql | 决策引擎表（规则、审计日志） | PostgreSQL |
| 004a | 004_create_ingestion_tables.sql | 数据采集层表（数据源、双写配置） | PostgreSQL |
| 004b | 004_create_prediction_tables.sql | 预测结果超级表 | TDengine |
| 005 | 005_create_identity_tables.sql | 身份集成表（LDAP、OAuth2） | PostgreSQL |

## 整合脚本

- **v2_consolidated_migration.sql**: 整合所有PostgreSQL迁移的单一脚本
- **v2_rollback.sql**: 回滚脚本，用于撤销V2升级

## 使用方法

### 方式1: 使用Python迁移脚本（推荐）

```bash
# 完整迁移
python scripts/migration/run_v2_migration.py

# 模拟运行（不实际执行）
python scripts/migration/run_v2_migration.py --dry-run

# 仅验证迁移状态
python scripts/migration/run_v2_migration.py --validate-only

# 执行回滚
python scripts/migration/run_v2_migration.py --rollback

# 跳过TDengine迁移
python scripts/migration/run_v2_migration.py --skip-tdengine
```

### 方式2: 直接执行SQL脚本

#### PostgreSQL迁移

```bash
# 使用整合脚本（推荐）
psql -h localhost -U postgres -d your_database -f migrations/platform_upgrade/v2_consolidated_migration.sql

# 或者按顺序执行单独脚本
psql -h localhost -U postgres -d your_database -f migrations/platform_upgrade/001_create_platform_tables.sql
psql -h localhost -U postgres -d your_database -f migrations/platform_upgrade/002_add_platform_menus.sql
psql -h localhost -U postgres -d your_database -f migrations/platform_upgrade/003_create_decision_engine_tables.sql
psql -h localhost -U postgres -d your_database -f migrations/platform_upgrade/004_create_ingestion_tables.sql
psql -h localhost -U postgres -d your_database -f migrations/platform_upgrade/005_create_identity_tables.sql
```

#### TDengine迁移

```bash
# 连接TDengine并执行
taos -h localhost -u root -p taosdata -f migrations/platform_upgrade/004_create_prediction_tables.sql
```

### 方式3: 回滚

```bash
# 使用Python脚本回滚
python scripts/migration/run_v2_migration.py --rollback

# 或直接执行SQL回滚脚本
psql -h localhost -U postgres -d your_database -f migrations/platform_upgrade/v2_rollback.sql
```

## 迁移版本跟踪

迁移执行后，版本信息会记录在 `t_migration_versions` 表中：

```sql
SELECT version, description, script_name, executed_at, execution_status 
FROM t_migration_versions 
ORDER BY executed_at;
```

## 注意事项

1. **备份数据**: 执行迁移前请务必备份数据库
2. **执行顺序**: 如果手动执行，请按版本号顺序执行
3. **TDengine**: TDengine迁移需要单独执行，不包含在整合脚本中
4. **幂等性**: 迁移脚本设计为幂等的，可以安全地重复执行
5. **回滚**: 回滚操作会删除V2升级创建的所有表和数据

## 表结构说明

### 核心表

- `t_asset_category`: 资产类别
- `t_signal_definition`: 信号定义
- `t_asset`: 资产
- `t_ai_model`: AI模型
- `t_ai_model_version`: AI模型版本
- `t_ai_prediction`: AI预测结果

### 决策引擎表

- `t_decision_rules`: 决策规则
- `t_decision_audit_logs`: 决策审计日志

### 数据采集层表

- `t_data_sources`: 数据源配置
- `t_dual_write_config`: 双写配置
- `t_ingestion_error_logs`: 采集错误日志
- `t_ingestion_statistics`: 采集统计
- `t_adapter_templates`: 适配器模板

### 身份集成表

- `t_identity_providers`: 身份提供商
- `t_user_external_identities`: 用户外部身份

### TDengine超级表

- `pred_{category}`: 预测结果超级表（如 pred_motor, pred_pump）
- `feat_{category}`: 特征存储超级表

## 故障排除

### 迁移失败

1. 检查数据库连接配置
2. 查看迁移日志: `logs/v2_migration_*.log`
3. 检查 `t_migration_versions` 表中的执行状态

### 回滚失败

1. 检查是否有外键依赖
2. 手动删除依赖表后重试
3. 联系数据库管理员

## 联系方式

如有问题，请联系开发团队。
