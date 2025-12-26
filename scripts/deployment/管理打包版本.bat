@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set PROJECT_ROOT=%~dp0..\..
set RELEASES_DIR=%PROJECT_ROOT%\releases

echo ========================================
echo 离线部署包版本管理工具
echo ========================================
echo.

if not exist "%RELEASES_DIR%" (
    echo 未找到 releases 目录
    echo 请先运行打包脚本创建部署包
    pause
    exit /b 1
)

:MENU
echo.
echo 请选择操作:
echo.
echo [1] 列出所有版本
echo [2] 查看版本详情
echo [3] 删除指定版本
echo [4] 清理旧版本 (保留最近N个)
echo [5] 压缩指定版本
echo [6] 计算目录大小
echo [0] 退出
echo.
set /p choice="请输入选项 (0-6): "

if "%choice%"=="1" goto LIST_ALL
if "%choice%"=="2" goto VIEW_DETAIL
if "%choice%"=="3" goto DELETE_VERSION
if "%choice%"=="4" goto CLEANUP_OLD
if "%choice%"=="5" goto COMPRESS_VERSION
if "%choice%"=="6" goto CALC_SIZE
if "%choice%"=="0" goto END
goto MENU

:LIST_ALL
echo.
echo ========================================
echo 所有打包版本
echo ========================================
echo.

set count=0
for /f "delims=" %%d in ('dir /b /o-d "%RELEASES_DIR%"') do (
    set /a count+=1
    set "dir_name=%%d"
    
    REM 提取版本号和时间戳
    for /f "tokens=2,3 delims=_" %%a in ("!dir_name!") do (
        set "version=%%a"
        set "timestamp=%%b"
    )
    
    REM 格式化时间戳显示
    set "date_part=!timestamp:~0,8!"
    set "time_part=!timestamp:~8,6!"
    set "formatted_date=!date_part:~0,4!-!date_part:~4,2!-!date_part:~6,2!"
    set "formatted_time=!time_part:~0,2!:!time_part:~2,2!:!time_part:~4,2!"
    
    echo [!count!] %%d
    echo     版本: !version!
    echo     时间: !formatted_date! !formatted_time!
    
    REM 检查版本信息文件
    if exist "%RELEASES_DIR%\%%d\VERSION_INFO.txt" (
        echo     信息: 已包含版本信息文件
    )
    echo.
)

if !count!==0 (
    echo 未找到任何打包版本
)

goto MENU

:VIEW_DETAIL
echo.
set /p version_name="请输入版本目录名称: "

if not exist "%RELEASES_DIR%\%version_name%" (
    echo 错误: 版本不存在
    goto MENU
)

echo.
echo ========================================
echo 版本详情: %version_name%
echo ========================================
echo.

REM 显示版本信息文件
if exist "%RELEASES_DIR%\%version_name%\VERSION_INFO.txt" (
    type "%RELEASES_DIR%\%version_name%\VERSION_INFO.txt"
    echo.
)

REM 显示目录大小
echo 正在计算目录大小...
set total_size=0
for /r "%RELEASES_DIR%\%version_name%" %%f in (*) do (
    set /a total_size+=%%~zf
)
set /a size_mb=!total_size! / 1048576
echo 目录大小: !size_mb! MB
echo.

REM 显示关键文件
echo 关键文件:
if exist "%RELEASES_DIR%\%version_name%\完整部署.bat" echo   [√] 完整部署.bat
if exist "%RELEASES_DIR%\%version_name%\offline_packages" echo   [√] offline_packages\
if exist "%RELEASES_DIR%\%version_name%\web_node_modules.tar.gz" echo   [√] web_node_modules.tar.gz
if exist "%RELEASES_DIR%\%version_name%\web_node_modules.zip" echo   [√] web_node_modules.zip
if exist "%RELEASES_DIR%\%version_name%\web\dist" echo   [√] web\dist\
echo.

goto MENU

:DELETE_VERSION
echo.
echo 警告: 此操作将永久删除指定版本！
echo.
set /p version_name="请输入要删除的版本目录名称: "

if not exist "%RELEASES_DIR%\%version_name%" (
    echo 错误: 版本不存在
    goto MENU
)

echo.
echo 确认删除: %version_name%
set /p confirm="输入 YES 确认删除: "

if /i "%confirm%"=="YES" (
    echo 正在删除...
    rmdir /s /q "%RELEASES_DIR%\%version_name%"
    echo [成功] 版本已删除
) else (
    echo [取消] 删除操作已取消
)

goto MENU

:CLEANUP_OLD
echo.
set /p keep_count="保留最近多少个版本？(默认5): "
if "%keep_count%"=="" set keep_count=5

echo.
echo 将保留最近 %keep_count% 个版本，删除其他版本
set /p confirm="输入 YES 确认: "

if /i not "%confirm%"=="YES" (
    echo [取消] 清理操作已取消
    goto MENU
)

echo.
echo 正在清理旧版本...

set count=0
for /f "delims=" %%d in ('dir /b /o-d "%RELEASES_DIR%"') do (
    set /a count+=1
    if !count! GTR %keep_count% (
        echo 删除: %%d
        rmdir /s /q "%RELEASES_DIR%\%%d"
    ) else (
        echo 保留: %%d
    )
)

echo.
echo [成功] 清理完成
goto MENU

:COMPRESS_VERSION
echo.
set /p version_name="请输入要压缩的版本目录名称: "

if not exist "%RELEASES_DIR%\%version_name%" (
    echo 错误: 版本不存在
    goto MENU
)

echo.
echo 正在压缩 %version_name%...
echo 这可能需要几分钟，请稍候...

REM 使用 PowerShell 压缩
powershell -Command "Compress-Archive -Path '%RELEASES_DIR%\%version_name%' -DestinationPath '%RELEASES_DIR%\%version_name%.zip' -CompressionLevel Optimal -Force"

if errorlevel 1 (
    echo [错误] 压缩失败
) else (
    echo [成功] 压缩完成: %version_name%.zip
    
    REM 显示压缩文件大小
    for %%f in ("%RELEASES_DIR%\%version_name%.zip") do (
        set /a size_mb=%%~zf / 1048576
        echo 压缩包大小: !size_mb! MB
    )
)

goto MENU

:CALC_SIZE
echo.
echo 正在计算所有版本的总大小...
echo.

set total_size=0
set version_count=0

for /f "delims=" %%d in ('dir /b /o-d "%RELEASES_DIR%"') do (
    if exist "%RELEASES_DIR%\%%d\VERSION_INFO.txt" (
        set /a version_count+=1
        
        REM 计算单个版本大小
        set dir_size=0
        for /r "%RELEASES_DIR%\%%d" %%f in (*) do (
            set /a dir_size+=%%~zf
        )
        
        set /a size_mb=!dir_size! / 1048576
        set /a total_size+=!dir_size!
        
        echo %%d: !size_mb! MB
    )
)

set /a total_mb=!total_size! / 1048576
set /a total_gb=!total_mb! / 1024

echo.
echo ========================================
echo 统计信息
echo ========================================
echo 版本数量: !version_count!
echo 总大小: !total_mb! MB (!total_gb! GB)
echo.

goto MENU

:END
echo.
echo 再见！
pause
exit /b 0
