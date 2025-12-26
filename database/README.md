# 🚀 分阶段数据库迁移系统

## 快速开始

### 最简单的方式（推荐）

```bash
# 1. 设置数据库连接
export DATABASE_URL="postgresql://user:password@localhost:5432/database"

# 2. 一键执行迁移
cd database
python migrate.py
```

### 使用Makefile

```bash
# 1. 设置数据库连接
export DATABASE_URL="postgresql://user:password@localhost:5432/database"

# 2. 执行迁移
cd database
make migrate
```

## 📋 可用脚本

| 脚本 | 用途 | 推荐度 |
|------|------|--------|
| `migrate.py` | 一键执行完整迁移 | ⭐⭐⭐⭐⭐ |
| `run_phased_migration.py` | 交互式迁移界面 | ⭐⭐⭐⭐ |
| `execute_migration.py` | 直接执行迁移 | ⭐⭐⭐ |
| `verify_system.py` | 系统验证 | ⭐⭐⭐⭐ |
| `demo_migration.py` | 功能演示 | ⭐⭐⭐ |
| `test_migration_system.py` | 系统测试 | ⭐⭐⭐ |

## 🎯 迁移阶段

系统将自动执行以下6个阶段：

1. **准备阶段** - 配置初始化和基础验证
2. **双写阶段** - 启用双写机制确保数据同步
3. **验证阶段** - 全面的数据一致性检查
4. **读取切换阶段** - 渐进式切换读取源
5. **清理阶段** - 禁用双写和最终验证
6. **完成阶段** - 生成报告和系统清理

## 📚 文档

- **[实施指南](IMPLEMENTATION_GUIDE.md)** - 详细的实施步骤
- **[快速开始](QUICK_START_GUIDE.md)** - 新用户入门指南
- **[操作手册](PHASED_MIGRATION_MANUAL.md)** - 完整的操作流程
- **[系统概述](README_PHASED_MIGRATION.md)** - 架构和特性说明

## 🛠️ 故障排除

如果遇到问题：

1. **检查日志**: `migration_execution.log`
2. **验证系统**: `python verify_system.py`
3. **查看文档**: `IMPLEMENTATION_GUIDE.md`
4. **回滚操作**: 查看手册中的回滚指南

## ⚡ Makefile命令

```bash
make migrate              # 一键执行迁移
make migrate-interactive  # 交互式迁移
make verify              # 验证系统
make test                # 运行测试
make demo                # 功能演示
make clean               # 清理日志
```

## 🎉 完成

恭喜！你现在拥有了一个完整的分阶段数据库迁移系统。

**开始迁移：**
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/database"
cd database
python migrate.py
```

祝你迁移顺利！🚀