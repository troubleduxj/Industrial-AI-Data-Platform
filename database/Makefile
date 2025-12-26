# 分阶段数据库迁移系统 Makefile

.PHONY: help install test demo start clean

# 默认目标
help:
	@echo "分阶段数据库迁移系统"
	@echo "====================="
	@echo ""
	@echo "可用命令:"
	@echo "  install    - 安装依赖"
	@echo "  test       - 运行系统测试"
	@echo "  demo       - 运行演示"
	@echo "  start      - 启动迁移向导"
	@echo "  clean      - 清理日志文件"
	@echo "  setup      - 初始化环境"
	@echo ""
	@echo "使用示例:"
	@echo "  make setup"
	@echo "  make test"
	@echo "  make start"

# 安装依赖
install:
	@echo "安装Python依赖..."
	pip install asyncpg aiohttp
	@echo "✅ 依赖安装完成"

# 设置环境
setup: install
	@echo "设置环境..."
	@if [ -z "$$DATABASE_URL" ]; then \
		echo "⚠️  请设置 DATABASE_URL 环境变量"; \
		echo "例如: export DATABASE_URL='postgresql://user:password@localhost:5432/database'"; \
		exit 1; \
	fi
	@echo "✅ 环境设置完成"

# 运行系统测试
test: setup
	@echo "运行系统测试..."
	python test_migration_system.py

# 运行演示
demo: setup
	@echo "运行迁移演示..."
	python demo_migration.py

# 启动迁移向导
start: setup
	@echo "启动迁移向导..."
	python start_migration.py

# 运行完整迁移实施
migrate: setup
	@echo "运行完整迁移实施..."
	python implement_phased_migration.py --config config.json

# 仅启动监控
monitor: setup
	@echo "启动监控系统..."
	python migration_alerting_system.py --db-url "$$DATABASE_URL" --action monitor

# 检查迁移状态
status: setup
	@echo "检查迁移状态..."
	python phased_migration_strategy.py --db-url "$$DATABASE_URL" --action status

# 数据一致性验证
validate: setup
	@echo "执行数据一致性验证..."
	@if [ -z "$$SOURCE_TABLE" ] || [ -z "$$TARGET_TABLE" ]; then \
		echo "请设置 SOURCE_TABLE 和 TARGET_TABLE 环境变量"; \
		echo "例如: make validate SOURCE_TABLE=api TARGET_TABLE=t_sys_api_endpoints"; \
		exit 1; \
	fi
	python data_consistency_validator.py --db-url "$$DATABASE_URL" --source-table "$$SOURCE_TABLE" --target-table "$$TARGET_TABLE" --level detailed

# 切换分析
switch-analytics: setup
	@echo "获取切换分析..."
	@if [ -z "$$CONFIG_ID" ]; then \
		echo "请设置 CONFIG_ID 环境变量"; \
		echo "例如: make switch-analytics CONFIG_ID=api_gradual_switch"; \
		exit 1; \
	fi
	python configurable_read_switch.py --db-url "$$DATABASE_URL" --action analytics --config-id "$$CONFIG_ID"

# 告警统计
alert-stats: setup
	@echo "获取告警统计..."
	python migration_alerting_system.py --db-url "$$DATABASE_URL" --action statistics --days 7

# 清理日志文件
clean:
	@echo "清理日志文件..."
	rm -f *.log
	rm -f migration_*.json
	rm -f validation_*.json
	rm -f alert_*.json
	rm -f final_*.json
	@echo "✅ 日志文件清理完成"

# 创建配置文件
config:
	@echo "创建配置文件..."
	@if [ ! -f config.json ]; then \
		cp config.json.example config.json; \
		echo "✅ 配置文件已创建: config.json"; \
		echo "请编辑配置文件以适应您的环境"; \
	else \
		echo "⚠️  配置文件已存在: config.json"; \
	fi

# 备份配置
backup-config:
	@echo "备份配置文件..."
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	cp config.json config_backup_$$timestamp.json 2>/dev/null || true; \
	cp migration_configs.json migration_configs_backup_$$timestamp.json 2>/dev/null || true; \
	cp read_switch_configs.json read_switch_configs_backup_$$timestamp.json 2>/dev/null || true; \
	cp alerting_config.json alerting_config_backup_$$timestamp.json 2>/dev/null || true; \
	echo "✅ 配置文件备份完成"

# 恢复配置
restore-config:
	@echo "恢复配置文件..."
	@if [ -z "$$BACKUP_TIMESTAMP" ]; then \
		echo "请指定备份时间戳"; \
		echo "例如: make restore-config BACKUP_TIMESTAMP=20240110_120000"; \
		exit 1; \
	fi
	@cp config_backup_$$BACKUP_TIMESTAMP.json config.json 2>/dev/null || echo "未找到主配置备份"; \
	cp migration_configs_backup_$$BACKUP_TIMESTAMP.json migration_configs.json 2>/dev/null || echo "未找到迁移配置备份"; \
	cp read_switch_configs_backup_$$BACKUP_TIMESTAMP.json read_switch_configs.json 2>/dev/null || echo "未找到切换配置备份"; \
	cp alerting_config_backup_$$BACKUP_TIMESTAMP.json alerting_config.json 2>/dev/null || echo "未找到告警配置备份"; \
	echo "✅ 配置文件恢复完成"

# 生成文档
docs:
	@echo "生成文档..."
	@echo "📚 可用文档:"
	@echo "  - QUICK_START_GUIDE.md     快速开始指南"
	@echo "  - PHASED_MIGRATION_MANUAL.md  详细操作手册"
	@echo "  - README_MIGRATION_SYSTEM.md  系统说明"

# 显示系统信息
info:
	@echo "系统信息"
	@echo "========"
	@echo "Python版本: $$(python --version)"
	@echo "当前目录: $$(pwd)"
	@echo "数据库URL: $${DATABASE_URL:-未设置}"
	@echo ""
	@echo "配置文件状态:"
	@ls -la *.json 2>/dev/null || echo "  无配置文件"
	@echo ""
	@echo "日志文件:"
	@ls -la *.log 2>/dev/null || echo "  无日志文件"

# 完整的端到端测试
e2e-test: setup test demo
	@echo "✅ 端到端测试完成"

# 执行实际迁移
execute: setup
	@echo "执行分阶段数据库迁移..."
	python execute_migration.py

# 验证系统
verify: setup
	@echo "验证系统准备状态..."
	python verify_system.py

# 一键执行迁移（最简单）
migrate:
	@echo "一键执行分阶段数据库迁移..."
	python migrate.py

# 运行完整迁移流程（交互式）
migrate-interactive: setup
	@echo "启动分阶段迁移系统..."
	python run_phased_migration.py

# 快速开始（推荐新用户使用）
quickstart: install config test
	@echo ""
	@echo "🎉 快速开始设置完成！"
	@echo ""
	@echo "下一步:"
	@echo "1. 设置数据库连接: export DATABASE_URL='postgresql://user:password@localhost:5432/database'"
	@echo "2. 编辑配置文件: vi config.json"
	@echo "3. 验证系统: make verify"
	@echo "4. 执行迁移: make migrate"

# 帮助信息（详细版）
help-detailed:
	@echo "分阶段数据库迁移系统 - 详细帮助"
	@echo "=================================="
	@echo ""
	@echo "🚀 快速开始:"
	@echo "  make quickstart    - 新用户推荐，完整设置"
	@echo "  make setup         - 安装依赖和检查环境"
	@echo "  make test          - 运行系统测试"
	@echo "  make demo          - 运行功能演示"
	@echo "  make start         - 启动交互式迁移向导"
	@echo ""
	@echo "🔧 配置管理:"
	@echo "  make config        - 创建默认配置文件"
	@echo "  make backup-config - 备份当前配置"
	@echo "  make restore-config BACKUP_TIMESTAMP=20240110_120000 - 恢复配置"
	@echo ""
	@echo "📊 监控和分析:"
	@echo "  make monitor       - 启动监控系统"
	@echo "  make status        - 检查迁移状态"
	@echo "  make alert-stats   - 获取告警统计"
	@echo ""
	@echo "🔍 验证和切换:"
	@echo "  make validate SOURCE_TABLE=api TARGET_TABLE=t_sys_api_endpoints"
	@echo "  make switch-analytics CONFIG_ID=api_gradual_switch"
	@echo ""
	@echo "🧹 维护:"
	@echo "  make clean         - 清理日志文件"
	@echo "  make info          - 显示系统信息"
	@echo ""
	@echo "📚 文档:"
	@echo "  make docs          - 查看可用文档"
	@echo ""
	@echo "🔗 环境变量:"
	@echo "  DATABASE_URL       - 数据库连接字符串（必需）"
	@echo "  SOURCE_TABLE       - 源表名（验证时使用）"
	@echo "  TARGET_TABLE       - 目标表名（验证时使用）"
	@echo "  CONFIG_ID          - 切换配置ID（分析时使用）"