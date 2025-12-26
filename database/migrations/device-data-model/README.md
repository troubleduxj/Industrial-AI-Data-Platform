# 设备数据模型 - 数据库迁移脚本

## 📋 概述

本目录包含设备数据模型功能的所有数据库迁移脚本。这些脚本按照**向后兼容**的原则设计，确保100%安全，可完全回滚。

## 📁 文件清单

| 文件名 | 用途 | 执行顺序 |
|-------|------|---------|
| `execute_migration.sql` | **主执行脚本**（一键执行所有迁移） | 1 |
| `001_extend_device_field.sql` | 扩展 `t_device_field` 表 | 2 |
| `002_create_device_data_model.sql` | 创建 `t_device_data_model` 表 | 3 |
| `003_create_field_mapping.sql` | 创建 `t_device_field_mapping` 表 | 4 |
| `004_create_execution_log.sql` | 创建 `t_model_execution_log` 表 | 5 |
| `005_init_field_attributes.sql` | 初始化字段属性 | 6 |
| `006_create_default_mappings.sql` | 创建默认字段映射 | 7 |
| `007_create_default_models.sql` | 创建默认数据模型 | 8 |
| `rollback.sql` | **回滚脚本**（完全删除所有更改） | - |
| `README.md` | 本文档 | - |

## 🚀 快速开始

### 前置条件

1. ✅ PostgreSQL 12+ 已安装并运行
2. ✅ 数据库 `device_monitor` 已创建
3. ✅ 数据库已备份（⚠️ 强烈建议！）

### 一键执行（推荐）

```bash
# 进入迁移脚本目录
cd database/migrations/device-data-model

# 执行所有迁移
psql -h localhost -U postgres -d device_monitor -f execute_migration.sql
```

### 逐个执行（调试模式）

如果需要逐个执行脚本（便于调试），请按以下顺序：

```bash
# 1. 创建表
psql -h localhost -U postgres -d device_monitor -f 001_extend_device_field.sql
psql -h localhost -U postgres -d device_monitor -f 002_create_device_data_model.sql
psql -h localhost -U postgres -d device_monitor -f 003_create_field_mapping.sql
psql -h localhost -U postgres -d device_monitor -f 004_create_execution_log.sql

# 2. 数据迁移
psql -h localhost -U postgres -d device_monitor -f 005_init_field_attributes.sql
psql -h localhost -U postgres -d device_monitor -f 006_create_default_mappings.sql
psql -h localhost -U postgres -d device_monitor -f 007_create_default_models.sql
```

## ⚙️ 执行参数说明

### 连接参数

- `-h localhost` - 数据库主机地址
- `-U postgres` - 数据库用户名
- `-d device_monitor` - 数据库名称
- `-f script.sql` - 要执行的SQL文件

### 环境变量

```bash
# 设置密码（避免交互式输入）
export PGPASSWORD=your_password

# 或使用 .pgpass 文件（推荐）
echo "localhost:5432:device_monitor:postgres:your_password" > ~/.pgpass
chmod 600 ~/.pgpass
```

## 🔄 回滚操作

如果需要完全回滚所有更改：

```bash
# 执行回滚脚本
psql -h localhost -U postgres -d device_monitor -f rollback.sql
```

**回滚脚本将删除**:
- ✓ 3张新表（`t_device_data_model`, `t_device_field_mapping`, `t_model_execution_log`）
- ✓ 6个新列（`t_device_field` 表的扩展列）
- ✓ 所有触发器和函数
- ✓ 所有索引
- ✓ 前端菜单（隐藏，不删除）

**回滚不会影响**:
- ✓ 现有表（`t_device_type`, `t_device_info`, `t_device_field` 的原有列）
- ✓ 现有数据
- ✓ 现有功能

## ✅ 验证迁移结果

### 1. 检查表是否创建

```sql
-- 查询新建的表
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('t_device_data_model', 't_device_field_mapping', 't_model_execution_log');
```

预期结果：3行

### 2. 检查 t_device_field 表的新增列

```sql
-- 查询新增的列
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 't_device_field' 
AND column_name IN ('is_monitoring_key', 'is_ai_feature', 'aggregation_method', 'data_range', 'alarm_threshold', 'display_config');
```

预期结果：6行

### 3. 检查默认数据模型

```sql
-- 查询数据模型
SELECT model_code, model_name, model_type, is_active, is_default 
FROM t_device_data_model 
ORDER BY model_type;
```

预期结果：至少3行（realtime, statistics, ai_analysis）

### 4. 检查字段映射

```sql
-- 统计字段映射
SELECT device_type_code, COUNT(*) as mapping_count 
FROM t_device_field_mapping 
GROUP BY device_type_code;
```

预期结果：至少1行（welding）

## ⚠️ 注意事项

### 1. 向后兼容性保证

- ✅ **只ADD COLUMN**：对 `t_device_field` 表只添加新列，不修改现有列
- ✅ **所有新列允许NULL或有默认值**：现有数据完全不受影响
- ✅ **外键关联现有表**：不复制数据，保证一致性
- ✅ **独立新表**：不修改现有表结构

### 2. 数据库要求

- PostgreSQL 版本 ≥ 12（推荐 15+）
- JSONB 支持
- 足够的磁盘空间（建议预留至少 1GB）

### 3. 性能影响

- 迁移过程约需 **5-10分钟**（取决于现有数据量）
- 建议在**非高峰时段**执行
- 执行期间可能会锁表，业务系统可能短暂受影响

### 4. 备份策略

执行迁移前，**务必备份数据库**：

```bash
# 备份整个数据库
pg_dump -h localhost -U postgres device_monitor > backup_$(date +%Y%m%d_%H%M%S).sql

# 或只备份相关表
pg_dump -h localhost -U postgres -t t_device_type -t t_device_info -t t_device_field device_monitor > backup_partial_$(date +%Y%m%d_%H%M%S).sql
```

## 📊 执行结果示例

成功执行后，您应该看到类似以下输出：

```
=======================================================
✅ 迁移执行成功！
=======================================================

数据库表:
  ✓ t_device_field: 新增 6 列
  ✓ t_device_data_model: 3 条记录
  ✓ t_device_field_mapping: 50 条记录
  ✓ t_model_execution_log: 0 条记录

✅ t_device_field 扩展成功
✅ 默认数据模型创建成功 (3 个)
✅ 字段映射创建成功 (50 个)

=======================================================

创建的数据模型:
=======================================================
     model_code          |        model_name          | model_type  | version | is_active | is_default 
-------------------------+----------------------------+-------------+---------+-----------+------------
 welding_ai_anomaly_v1   | 焊接设备异常检测AI模型     | ai_analysis | 1.0     | t         | f
 welding_realtime_v1     | 焊接设备实时监控模型       | realtime    | 1.0     | t         | t
 welding_statistics_daily_v1 | 焊接设备每日统计模型   | statistics  | 1.0     | t         | f
(3 rows)

字段映射统计:
=======================================================
 device_type_code | mapping_count | tag_count | transform_count 
------------------+---------------+-----------+-----------------
 welding          |            50 |         5 |              15
(1 row)

✅ 迁移已成功完成！
```

## 🐛 故障排除

### 问题 1: 权限不足

**错误信息**: `ERROR: permission denied for table t_device_field`

**解决方法**:
```sql
-- 授予用户必要的权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;
```

### 问题 2: 表已存在

**错误信息**: `ERROR: relation "t_device_data_model" already exists`

**解决方法**:
1. 如果是重复执行，先执行回滚脚本
2. 或手动删除已存在的表

```bash
psql -h localhost -U postgres -d device_monitor -f rollback.sql
```

### 问题 3: 外键约束失败

**错误信息**: `ERROR: insert or update on table "t_device_data_model" violates foreign key constraint`

**解决方法**:
检查 `t_device_type` 表中是否存在对应的 `type_code`

```sql
SELECT type_code FROM t_device_type WHERE type_code = 'welding';
```

## 📞 技术支持

如遇问题，请联系：
- **技术负责人**: [待填写]
- **文档位置**: `docs/device-data-model/03-数据库设计.md`

## 📚 相关文档

- [00-设计方案总览](../../../docs/device-data-model/00-设计方案总览.md)
- [03-数据库设计](../../../docs/device-data-model/03-数据库设计.md)
- [06-实施计划](../../../docs/device-data-model/06-实施计划.md)
- [实施检查清单](../../../docs/device-data-model/实施检查清单.md)

---

**版本**: 1.0  
**最后更新**: 2025-11-03  
**状态**: ✅ 可用于生产环境

