@echo off
chcp 65001 >nul
echo ========================================
echo 设备字段配置管理 - 权限修复
echo ========================================
echo.

set PGPASSWORD=Hanatech@123
set PSQL_PATH=psql

echo 正在执行权限修复...
echo.

%PSQL_PATH% -U postgres -h 127.0.0.1 -p 5432 -d devicemonitor -f fix_admin_permissions.sql

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo ✅ 权限修复完成！
    echo ========================================
    echo.
    echo 请执行以下操作：
    echo 1. 重新登录系统（清除旧的 token）
    echo 2. 访问 系统管理 -^> 设备字段配置
    echo 3. 验证新增、编辑、删除按钮是否可见
    echo.
) else (
    echo.
    echo ========================================
    echo ❌ 权限修复失败！
    echo ========================================
    echo.
    echo 可能的原因：
    echo 1. psql 命令未安装或不在 PATH 中
    echo 2. 数据库连接失败
    echo 3. SQL 脚本执行出错
    echo.
    echo 请检查错误信息并重试
    echo.
)

pause
