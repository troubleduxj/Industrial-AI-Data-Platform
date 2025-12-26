@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo Database 目录清理脚本
echo ========================================
echo.
echo 此脚本将:
echo 1. 创建归档目录结构
echo 2. 移动临时文件到归档
echo 3. 删除不需要的文件
echo 4. 保留核心文件
echo.
echo 警告: 此操作会移动大量文件！
echo.

set /p confirm="确认执行清理？(输入 YES 继续): "
if /i not "%confirm%"=="YES" (
    echo 清理已取消
    pause
    exit /b 0
)

echo.
echo [1/10] 创建归档目录结构...
mkdir database\archived\reports 2>nul
mkdir database\archived\docs 2>nul
mkdir database\archived\migration-scripts 2>nul
mkdir database\archived\performance 2>nul
mkdir database\archived\tests 2>nul
mkdir database\archived\cleanup 2>nul
mkdir database\archived\temp 2>nul
echo   完成

echo.
echo [2/10] 移动任务报告 (20 个)...
move /Y database\task_*_completion_report.md database\archived\reports\ >nul 2>&1
echo   完成

echo.
echo [3/10] 移动迁移文档...
move /Y database\*_GUIDE.md database\archived\docs\ >nul 2>&1
move /Y database\README_*.md database\archived\docs\ >nul 2>&1
move /Y database\CLEANUP_SUMMARY.md database\archived\docs\ >nul 2>&1
move /Y database\table_cleanup_analysis.md database\archived\docs\ >nul 2>&1
move /Y database\permission_service_test_report.md database\archived\docs\ >nul 2>&1
echo   完成

echo.
echo [4/10] 移动迁移脚本...
move /Y database\*migration*.py database\archived\migration-scripts\ >nul 2>&1
move /Y database\run_*.py database\archived\migration-scripts\ >nul 2>&1
move /Y database\start_migration.py database\archived\migration-scripts\ >nul 2>&1
move /Y database\execute_*.py database\archived\migration-scripts\ >nul 2>&1
move /Y database\implement_*.py database\archived\migration-scripts\ >nul 2>&1
move /Y database\migrate*.py database\archived\migration-scripts\ >nul 2>&1
move /Y database\demo_migration.py database\archived\migration-scripts\ >nul 2>&1
move /Y database\fixed_migration_system.py database\archived\migration-scripts\ >nul 2>&1
move /Y database\simple_migration_system.py database\archived\migration-scripts\ >nul 2>&1
move /Y database\complete_migration_system.py database\archived\migration-scripts\ >nul 2>&1
move /Y database\phased_migration_strategy.py database\archived\migration-scripts\ >nul 2>&1
move /Y database\permission_migration_*.py database\archived\migration-scripts\ >nul 2>&1
echo   完成

echo.
echo [5/10] 移动性能优化文件...
move /Y database\*performance*.* database\archived\performance\ >nul 2>&1
move /Y database\*optimization*.* database\archived\performance\ >nul 2>&1
move /Y database\optimize_*.sql database\archived\performance\ >nul 2>&1
echo   完成

echo.
echo [6/10] 移动测试脚本...
move /Y database\test_*.py database\archived\tests\ >nul 2>&1
move /Y database\verify_*.py database\archived\tests\ >nul 2>&1
move /Y database\check_*.py database\archived\tests\ >nul 2>&1
move /Y database\data_consistency_validator.py database\archived\tests\ >nul 2>&1
echo   完成

echo.
echo [7/10] 移动清理脚本...
move /Y database\*cleanup*.* database\archived\cleanup\ >nul 2>&1
move /Y database\audit.py database\archived\cleanup\ >nul 2>&1
move /Y database\analyze_duplicate_tables.py database\archived\cleanup\ >nul 2>&1
echo   完成

echo.
echo [8/10] 移动临时文件...
move /Y database\alerting_config.json database\archived\temp\ >nul 2>&1
move /Y database\migration_configs.json database\archived\temp\ >nul 2>&1
move /Y database\read_switch_configs.json database\archived\temp\ >nul 2>&1
move /Y database\working_connection.txt database\archived\temp\ >nul 2>&1
move /Y database\configurable_read_switch.py database\archived\temp\ >nul 2>&1
move /Y database\diagnose_connection.py database\archived\temp\ >nul 2>&1
move /Y database\migration_alerting_system.py database\archived\temp\ >nul 2>&1
move /Y database\migration_config.py database\archived\temp\ >nul 2>&1
echo   完成

echo.
echo [9/10] 移动临时 SQL 文件...
move /Y database\add_batch_delete_permissions.sql database\archived\temp\ >nul 2>&1
move /Y database\add_components_menu.sql database\archived\temp\ >nul 2>&1
move /Y database\api_permission_migration.sql database\archived\temp\ >nul 2>&1
move /Y database\button_permissions_init.sql database\archived\temp\ >nul 2>&1
move /Y database\device_metadata_schema.sql database\archived\temp\ >nul 2>&1
move /Y database\fix_null_timestamps.sql database\archived\temp\ >nul 2>&1
move /Y database\initial_schema.sql database\archived\temp\ >nul 2>&1
move /Y database\manual_menu_migration.sql database\archived\temp\ >nul 2>&1
move /Y database\migration_script.sql database\archived\temp\ >nul 2>&1
move /Y database\update_menu_structure.sql database\archived\temp\ >nul 2>&1
echo   完成

echo.
echo [10/10] 删除不需要的文件...
del /F /Q database\device_monitor.db >nul 2>&1
del /F /Q database\config.json >nul 2>&1
echo   完成

echo.
echo ========================================
echo 清理完成！
echo ========================================
echo.
echo 清理结果:
echo   - 任务报告已归档到 archived/reports/
echo   - 迁移文档已归档到 archived/docs/
echo   - 迁移脚本已归档到 archived/migration-scripts/
echo   - 性能优化已归档到 archived/performance/
echo   - 测试脚本已归档到 archived/tests/
echo   - 清理脚本已归档到 archived/cleanup/
echo   - 临时文件已归档到 archived/temp/
echo.
echo 保留的核心文件:
echo   - init-scripts/ (初始化脚本)
echo   - migrations/ (正式迁移)
echo   - archived/ (归档文件)
echo   - config.json.example (配置模板)
echo   - validation_rules.json (验证规则)
echo   - README.md (主文档)
echo   - Makefile (构建工具)
echo.

REM 统计文件数量
echo 当前 database 目录文件数:
dir /b database\*.* 2>nul | find /c /v ""
echo.

pause
