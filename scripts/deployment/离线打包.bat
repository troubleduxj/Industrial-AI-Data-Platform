@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo 设备监控系统 - 完全离线部署包
echo ========================================
echo.
echo 此脚本将:
echo 1. 使用 npm 重新安装前端依赖 (替代 pnpm)
echo 2. 打包完整的 node_modules
echo 3. 创建可在无网络环境部署的包
echo 4. 自动添加时间戳和版本号
echo.
echo 注意: 此过程会临时修改前端依赖安装方式
echo.

REM ========================================
REM 生成时间戳和版本号
REM ========================================
set PROJECT_ROOT=%~dp0..\..

REM 获取当前日期时间（格式：YYYYMMDD_HHMMSS）
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%

REM 尝试从 Git 获取版本号
for /f "delims=" %%i in ('git describe --tags --abbrev^=0 2^>nul') do set GIT_VERSION=%%i
if "%GIT_VERSION%"=="" (
    REM 如果没有 Git 标签，使用默认版本
    set VERSION=v1.0.0
) else (
    set VERSION=%GIT_VERSION%
)

REM 去除版本号中的 'v' 前缀（如果有）
set VERSION_NUM=%VERSION:v=%

REM 构建打包目录名称
set PACKAGE_NAME=offline_deploy_%VERSION_NUM%_%TIMESTAMP%
set PACKAGE_DIR=%PROJECT_ROOT%\releases\%PACKAGE_NAME%
set OFFLINE_PKG=%PACKAGE_DIR%\offline_packages
set TEMP_WEB=%PROJECT_ROOT%\web_npm_temp

echo ========================================
echo 打包信息
echo ========================================
echo 版本号: %VERSION%
echo 时间戳: %TIMESTAMP%
echo 打包目录: releases\%PACKAGE_NAME%
echo ========================================
echo.

echo 是否继续？此操作会创建临时目录用于 npm 安装
pause

REM 检查环境
echo.
echo [检查] 验证环境...
if not exist "%PROJECT_ROOT%\.venv" (
    echo [错误] 未找到 .venv 虚拟环境
    pause
    exit /b 1
)

echo [成功] 环境检查通过
echo.

echo [1/9] 创建部署包目录...
REM 创建 releases 主目录
if not exist "%PROJECT_ROOT%\releases" (
    mkdir "%PROJECT_ROOT%\releases"
    echo 创建 releases 目录
)

REM 创建本次打包目录
if exist "%PACKAGE_DIR%" (
    echo 警告: 目录已存在，将覆盖
    rmdir /s /q "%PACKAGE_DIR%"
)
mkdir "%PACKAGE_DIR%"
mkdir "%OFFLINE_PKG%"

REM 创建版本信息文件
(
echo 打包信息
echo ========================================
echo 版本号: %VERSION%
echo 打包时间: %date% %time%
echo 时间戳: %TIMESTAMP%
echo 打包目录: %PACKAGE_NAME%
echo ========================================
) > "%PACKAGE_DIR%\VERSION_INFO.txt"

echo [成功] 创建目录: %PACKAGE_NAME%

echo.
echo [2/9] 创建临时目录并使用 npm 安装前端依赖...
if exist "%TEMP_WEB%" (
    rmdir /s /q "%TEMP_WEB%"
)
mkdir "%TEMP_WEB%"

echo 复制前端配置文件...
copy "%PROJECT_ROOT%\web\package.json" "%TEMP_WEB%\" >nul
copy "%PROJECT_ROOT%\web\*.js" "%TEMP_WEB%\" >nul 2>&1
copy "%PROJECT_ROOT%\web\*.ts" "%TEMP_WEB%\" >nul 2>&1
copy "%PROJECT_ROOT%\web\*.html" "%TEMP_WEB%\" >nul 2>&1

echo 使用 npm 安装依赖 (这可能需要几分钟)...
cd "%TEMP_WEB%"
call npm install
if errorlevel 1 (
    echo [错误] npm 安装失败
    cd "%PROJECT_ROOT%"
    pause
    exit /b 1
)
cd "%PROJECT_ROOT%"
echo [成功] npm 依赖安装完成

echo.
echo [3/9] 复制项目代码...
REM 后端代码
xcopy "%PROJECT_ROOT%\app" "%PACKAGE_DIR%\app\" /E /I /Q
REM 前端代码
xcopy "%PROJECT_ROOT%\web\src" "%PACKAGE_DIR%\web\src\" /E /I /Q
xcopy "%PROJECT_ROOT%\web\public" "%PACKAGE_DIR%\web\public\" /E /I /Q
xcopy "%PROJECT_ROOT%\web\build" "%PACKAGE_DIR%\web\build\" /E /I /Q
xcopy "%PROJECT_ROOT%\web\i18n" "%PACKAGE_DIR%\web\i18n\" /E /I /Q
xcopy "%PROJECT_ROOT%\web\settings" "%PACKAGE_DIR%\web\settings\" /E /I /Q
REM 共享代码包（重要！）
xcopy "%PROJECT_ROOT%\packages" "%PACKAGE_DIR%\packages\" /E /I /Q
REM 前端配置文件
copy "%PROJECT_ROOT%\web\*.json" "%PACKAGE_DIR%\web\" >nul 2>&1
copy "%PROJECT_ROOT%\web\*.js" "%PACKAGE_DIR%\web\" >nul 2>&1
copy "%PROJECT_ROOT%\web\*.ts" "%PACKAGE_DIR%\web\" >nul 2>&1
copy "%PROJECT_ROOT%\web\*.html" "%PACKAGE_DIR%\web\" >nul 2>&1
copy "%PROJECT_ROOT%\web\.env*" "%PACKAGE_DIR%\web\" >nul 2>&1
REM 数据库迁移
xcopy "%PROJECT_ROOT%\migrations" "%PACKAGE_DIR%\migrations\" /E /I /Q
REM 配置文件
copy "%PROJECT_ROOT%\requirements.txt" "%PACKAGE_DIR%\" >nul
copy "%PROJECT_ROOT%\.env.example" "%PACKAGE_DIR%\" >nul
copy "%PROJECT_ROOT%\README.md" "%PACKAGE_DIR%\" >nul
copy "%PROJECT_ROOT%\run.py" "%PACKAGE_DIR%\" >nul 2>&1

echo.
echo [4/9] 下载 Python 依赖包...
cd "%PROJECT_ROOT%"
call .venv\Scripts\activate
pip download -r requirements.txt -d "%OFFLINE_PKG%" --no-cache-dir
if errorlevel 1 (
    echo [警告] 部分包下载失败，但会继续...
)

echo.
echo [5/9] 使用临时 npm 环境构建前端...
echo 复制源代码到临时目录...
xcopy "%PROJECT_ROOT%\web\src" "%TEMP_WEB%\src\" /E /I /Q
xcopy "%PROJECT_ROOT%\web\public" "%TEMP_WEB%\public\" /E /I /Q
xcopy "%PROJECT_ROOT%\web\build" "%TEMP_WEB%\build\" /E /I /Q
xcopy "%PROJECT_ROOT%\web\i18n" "%TEMP_WEB%\i18n\" /E /I /Q
xcopy "%PROJECT_ROOT%\web\settings" "%TEMP_WEB%\settings\" /E /I /Q
if exist "%PROJECT_ROOT%\web\.eslint-global-variables.json" (
    copy "%PROJECT_ROOT%\web\.eslint-global-variables.json" "%TEMP_WEB%\" >nul
)
if exist "%PROJECT_ROOT%\web\unocss.config.js" (
    copy "%PROJECT_ROOT%\web\unocss.config.js" "%TEMP_WEB%\" >nul
)

cd "%TEMP_WEB%"
call npm run build
if errorlevel 1 (
    echo [错误] 前端构建失败
    cd "%PROJECT_ROOT%"
    pause
    exit /b 1
)

echo 复制构建产物...
xcopy "%TEMP_WEB%\dist" "%PACKAGE_DIR%\web\dist\" /E /I /Q
cd "%PROJECT_ROOT%"
echo [成功] 前端构建完成

echo.
echo [6/9] 打包 npm 版本的 node_modules...
echo 使用 tar 压缩 (保留所有文件)...
tar -czf "%PACKAGE_DIR%\web_node_modules.tar.gz" -C "%TEMP_WEB%" node_modules
if errorlevel 1 (
    echo [警告] tar 压缩失败，尝试使用 PowerShell...
    powershell -Command "Compress-Archive -Path '%TEMP_WEB%\node_modules' -DestinationPath '%PACKAGE_DIR%\web_node_modules.zip' -CompressionLevel Optimal -Force"
    if errorlevel 1 (
        echo [错误] node_modules 打包失败
        pause
        exit /b 1
    )
    echo [成功] 使用 ZIP 格式打包
) else (
    echo [成功] 使用 tar.gz 格式打包
)

echo.
echo [7/9] 清理临时目录...
if exist "%TEMP_WEB%" (
    rmdir /s /q "%TEMP_WEB%"
    echo [成功] 临时目录已清理
)

echo.
echo [8/9] 创建部署脚本...

REM Python 依赖安装脚本
(
echo @echo off
echo chcp 65001 ^>nul
echo echo ========================================
echo echo 安装 Python 依赖
echo echo ========================================
echo echo.
echo.
echo if not exist .venv ^(
echo     echo [1/2] 创建虚拟环境...
echo     python -m venv .venv
echo     if errorlevel 1 ^(
echo         echo [错误] 虚拟环境创建失败
echo         pause
echo         exit /b 1
echo     ^)
echo ^) else ^(
echo     echo [跳过] 虚拟环境已存在
echo ^)
echo.
echo echo [2/2] 安装依赖...
echo call .venv\Scripts\activate
echo pip install --no-index --find-links=offline_packages -r requirements.txt
echo.
echo if errorlevel 1 ^(
echo     echo [错误] 依赖安装失败
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo ========================================
echo echo Python 依赖安装完成！
echo echo ========================================
echo pause
) > "%PACKAGE_DIR%\1-安装Python依赖.bat"

REM 前端依赖安装脚本（带进度提示）
(
echo @echo off
echo chcp 65001 ^>nul
echo echo ========================================
echo echo 安装前端依赖
echo echo ========================================
echo echo.
echo.
echo cd web
echo if exist node_modules ^(
echo     echo [警告] node_modules 已存在，删除中...
echo     rmdir /s /q node_modules
echo ^)
echo.
echo echo 解压 node_modules ^(这可能需要几分钟，请耐心等待...^)
echo echo.
echo if exist ..\web_node_modules.tar.gz ^(
echo     echo 使用 tar 解压...
echo     echo 正在解压，请稍候...
echo     echo.
echo     REM 启动进度提示
echo     start /b cmd /c "for /L %%%%i in ^(1,1,100^) do ^(echo 解压中... %%%%i%% ^& timeout /t 2 /nobreak ^>nul^)"
echo     tar -xzf ..\web_node_modules.tar.gz
echo     taskkill /f /im cmd.exe /fi "WINDOWTITLE eq 解压中*" ^>nul 2^>^&1
echo     if errorlevel 1 ^(
echo         echo.
echo         echo [错误] tar 解压失败
echo         pause
echo         exit /b 1
echo     ^)
echo ^) else if exist ..\web_node_modules.zip ^(
echo     echo 使用 PowerShell 解压...
echo     echo 正在解压大文件，这可能需要 5-10 分钟...
echo     echo 请不要关闭窗口，解压过程中不会有进度显示
echo     echo.
echo     echo 开始时间: %%time%%
echo     powershell -Command "$ProgressPreference='Continue'; Write-Host '正在解压...'; Expand-Archive -Path '..\web_node_modules.zip' -DestinationPath '.' -Force; Write-Host '解压完成！'"
echo     if errorlevel 1 ^(
echo         echo.
echo         echo [错误] 解压失败
echo         pause
echo         exit /b 1
echo     ^)
echo     echo 完成时间: %%time%%
echo ^) else ^(
echo     echo [错误] 未找到前端依赖包文件
echo     pause
echo     exit /b 1
echo ^)
echo cd ..
echo.
echo echo ========================================
echo echo 前端依赖安装完成！
echo echo ========================================
echo pause
) > "%PACKAGE_DIR%\2-安装前端依赖.bat"

REM 一键部署脚本（带进度条）
(
echo @echo off
echo chcp 65001 ^>nul
echo setlocal enabledelayedexpansion
echo.
echo REM 设置日志文件
echo set LOG_FILE=deploy_%%date:~0,4%%%%date:~5,2%%%%date:~8,2%%_%%time:~0,2%%%%time:~3,2%%%%time:~6,2%%.log
echo set LOG_FILE=%%LOG_FILE: =0%%
echo.
echo echo ========================================
echo echo 设备监控系统 - 一键部署
echo echo ========================================
echo echo 日志文件: %%LOG_FILE%%
echo echo.
echo echo 部署进度: [步骤 1/3]
echo echo [%%date%% %%time%%] 部署开始 ^>^> %%LOG_FILE%%
echo echo.
echo.
echo echo ┌────────────────────────────────────────┐
echo echo │  步骤 1/3: 安装 Python 依赖            │
echo echo └────────────────────────────────────────┘
echo echo [%%date%% %%time%%] [步骤 1/3] 安装 Python 依赖... ^>^> %%LOG_FILE%%
echo echo.
echo if not exist .venv ^(
echo     echo [1/2] 创建虚拟环境...
echo     python -m venv .venv
echo     if errorlevel 1 ^(
echo         echo [错误] 虚拟环境创建失败
echo         echo [%%date%% %%time%%] [错误] 虚拟环境创建失败 ^>^> %%LOG_FILE%%
echo         pause
echo         exit /b 1
echo     ^)
echo ^) else ^(
echo     echo [跳过] 虚拟环境已存在
echo ^)
echo.
echo echo [2/2] 安装 Python 依赖包...
echo call .venv\Scripts\activate
echo pip install --no-index --find-links=offline_packages -r requirements.txt
echo if errorlevel 1 ^(
echo     echo [错误] Python 依赖安装失败
echo     echo [%%date%% %%time%%] [错误] Python 依赖安装失败 ^>^> %%LOG_FILE%%
echo     pause
echo     exit /b 1
echo ^)
echo echo.
echo echo ✓ Python 依赖安装完成
echo echo [%%date%% %%time%%] [成功] Python 依赖安装完成 ^>^> %%LOG_FILE%%
echo echo.
echo echo ========================================
echo echo.
echo echo 按任意键继续 [步骤 2/3]...
echo pause ^>nul
echo echo.
echo echo ========================================
echo echo 部署进度: [步骤 2/3]
echo echo ========================================
echo echo.
echo echo ┌────────────────────────────────────────┐
echo echo │  步骤 2/3: 安装前端依赖                │
echo echo │  ^(解压大文件，需要 5-10 分钟^)         │
echo echo └────────────────────────────────────────┘
echo echo [%%date%% %%time%%] [步骤 2/3] 安装前端依赖... ^>^> %%LOG_FILE%%
echo echo.
echo cd web
echo if exist node_modules ^(
echo     echo 清理旧的 node_modules...
echo     rmdir /s /q node_modules
echo ^)
echo.
echo echo 正在解压 node_modules...
echo echo 提示: 解压过程中窗口可能看起来无响应，这是正常的
echo echo       请耐心等待，不要关闭窗口
echo echo.
echo echo 开始时间: %%time%%
echo echo ----------------------------------------
echo if exist ..\web_node_modules.tar.gz ^(
echo     echo 使用 tar 解压...
echo     tar -xzf ..\web_node_modules.tar.gz
echo     if errorlevel 1 ^(
echo         echo.
echo         echo [错误] tar 解压失败
echo         echo [%%date%% %%time%%] [错误] tar 解压失败 ^>^> ..\%%LOG_FILE%%
echo         cd ..
echo         pause
echo         exit /b 1
echo     ^)
echo ^) else if exist ..\web_node_modules.zip ^(
echo     echo 使用 PowerShell 解压...
echo     powershell -Command "$ProgressPreference='Continue'; Expand-Archive -Path '..\web_node_modules.zip' -DestinationPath '.' -Force"
echo     if errorlevel 1 ^(
echo         echo.
echo         echo [错误] 解压失败
echo         echo [%%date%% %%time%%] [错误] 解压失败 ^>^> ..\%%LOG_FILE%%
echo         cd ..
echo         pause
echo         exit /b 1
echo     ^)
echo ^) else ^(
echo     echo [错误] 未找到前端依赖包文件
echo     cd ..
echo     pause
echo     exit /b 1
echo ^)
echo echo ----------------------------------------
echo echo 完成时间: %%time%%
echo cd ..
echo echo.
echo echo ✓ 前端依赖安装完成
echo echo [%%date%% %%time%%] [成功] 前端依赖安装完成 ^>^> %%LOG_FILE%%
echo echo.
echo echo ========================================
echo echo.
echo echo 按任意键继续 [步骤 3/3]...
echo pause ^>nul
echo echo.
echo echo ========================================
echo echo 部署进度: [步骤 3/3]
echo echo ========================================
echo echo.
echo echo ┌────────────────────────────────────────┐
echo echo │  步骤 3/3: 配置环境                    │
echo echo └────────────────────────────────────────┘
echo echo [%%date%% %%time%%] [步骤 3/3] 配置环境... ^>^> %%LOG_FILE%%
echo echo.
echo if not exist .env ^(
echo     echo 创建 .env 配置文件...
echo     copy .env.example .env ^>nul
echo     echo.
echo     echo [重要] 请配置数据库连接信息
echo     echo        即将打开配置文件编辑器
echo     echo [%%date%% %%time%%] 创建 .env 配置文件 ^>^> %%LOG_FILE%%
echo     echo.
echo     pause
echo     notepad .env
echo ^) else ^(
echo     echo .env 文件已存在，跳过创建
echo     echo [%%date%% %%time%%] .env 文件已存在 ^>^> %%LOG_FILE%%
echo ^)
echo.
echo echo ✓ 环境配置完成
echo echo.
echo echo ========================================
echo echo.
echo echo ========================================
echo echo 部署完成！
echo echo ========================================
echo echo [%%date%% %%time%%] 部署完成 ^>^> %%LOG_FILE%%
echo echo.
echo echo ✓ 所有步骤已完成
echo echo.
echo echo 启动命令:
echo echo   后端: 双击 启动后端.bat
echo echo   前端: 双击 启动前端.bat
echo echo.
echo echo 访问地址: http://localhost:8000
echo echo 默认账号: admin / admin123
echo echo.
echo echo 日志文件: %%LOG_FILE%%
echo echo.
echo pause
) > "%PACKAGE_DIR%\完整部署.bat"

REM 启动脚本
(
echo @echo off
echo chcp 65001 ^>nul
echo echo ========================================
echo echo 启动后端服务
echo echo ========================================
echo echo.
echo call .venv\Scripts\activate
echo python run.py
) > "%PACKAGE_DIR%\启动后端.bat"

REM 启动前端脚本
(
echo @echo off
echo chcp 65001 ^>nul
echo echo ========================================
echo echo 启动前端服务
echo echo ========================================
echo echo.
echo cd web
echo npm run dev
) > "%PACKAGE_DIR%\启动前端.bat"

echo.
echo [9/9] 创建部署说明...
(
echo ========================================
echo 设备监控系统 - 完全离线部署包
echo ========================================
echo.
echo 打包时间: %date% %time%
echo.
echo ## 特点
echo.
echo - 完全离线部署，无需网络连接
echo - 使用 npm 打包，兼容性好
echo - 包含所有依赖，开箱即用
echo.
echo ## 前置要求
echo.
echo 目标服务器需要安装:
echo 1. Python 3.11.9
echo 2. Node.js 18+ ^(包含 npm^)
echo 3. TDengine 3.x
echo.
echo 注意: 不需要 pnpm，使用 npm 即可
echo.
echo ## 包含内容
echo.
echo 1. 项目源代码
echo    - app/          后端代码
echo    - web/          前端代码
echo    - migrations/   数据库迁移
echo.
echo 2. Python 依赖包
echo    - offline_packages/  所有 .whl 包
echo    - requirements.txt   依赖列表
echo.
echo 3. 前端依赖 (npm 版本)
echo    - web_node_modules.tar.gz  完整的 node_modules
echo    - 包含所有依赖, 无需网络
echo.
echo 4. 部署脚本
echo    - 完整部署.bat          一键部署 (推荐)
echo    - 1-安装Python依赖.bat  单独安装 Python
echo    - 2-安装前端依赖.bat    单独安装前端
echo    - 启动后端.bat          启动后端服务
echo    - 启动前端.bat          启动前端服务
echo.
echo ## 快速部署
echo.
echo 1. 将整个 offline_deploy_complete 目录复制到目标服务器
echo 2. 双击运行: 完整部署.bat
echo 3. 按提示完成每个步骤
echo 4. 编辑 .env 文件配置数据库
echo.
echo ## 启动服务
echo.
echo 后端: 双击 启动后端.bat
echo 前端: 双击 启动前端.bat
echo.
echo 访问: http://localhost:8000
echo 默认账号: admin / admin123
echo.
echo ## 文件大小说明
echo.
echo node_modules 压缩包可能较大 (几百MB), 这是正常的。
echo 包含了所有前端依赖, 确保离线环境可用。
echo.
) > "%PACKAGE_DIR%\部署说明.txt"

echo.
echo ========================================
echo 完全离线部署包创建完成！
echo ========================================
echo.
echo 打包信息:
echo   版本号: %VERSION%
echo   时间戳: %TIMESTAMP%
echo   打包名称: %PACKAGE_NAME%
echo.
echo 部署包位置: 
echo   %PACKAGE_DIR%
echo.
echo 关键文件检查:
if exist "%PACKAGE_DIR%\完整部署.bat" (
    echo [√] 完整部署.bat
) else (
    echo [×] 完整部署.bat 缺失
)

if exist "%OFFLINE_PKG%" (
    echo [√] Python 依赖包目录
) else (
    echo [×] Python 依赖包目录缺失
)

if exist "%PACKAGE_DIR%\web_node_modules.tar.gz" (
    echo [√] 前端依赖包 ^(tar.gz^)
    dir "%PACKAGE_DIR%\web_node_modules.tar.gz" | find "web_node_modules.tar.gz"
) else if exist "%PACKAGE_DIR%\web_node_modules.zip" (
    echo [√] 前端依赖包 ^(zip^)
    dir "%PACKAGE_DIR%\web_node_modules.zip" | find "web_node_modules.zip"
) else (
    echo [×] 前端依赖包缺失
)

if exist "%PACKAGE_DIR%\web\dist" (
    echo [√] 前端构建产物
) else (
    echo [×] 前端构建产物缺失
)

echo.
echo ========================================
echo 下一步操作
echo ========================================
echo.
echo 1. 打包文件位于: releases\%PACKAGE_NAME%
echo 2. 将整个目录传输到目标服务器
echo 3. 在目标服务器上运行 完整部署.bat
echo 4. 使用 npm 解压依赖 (无需网络)
echo 5. 启动服务
echo.
echo 历史版本管理:
echo   - 所有打包版本保存在 releases\ 目录
echo   - 可以保留多个版本便于回滚
echo   - 建议定期清理旧版本
echo.
echo 注意: 目标服务器只需要 Node.js (包含 npm), 不需要 pnpm
echo.

REM 列出最近的打包版本
echo ========================================
echo 最近的打包版本 (最多显示5个):
echo ========================================
dir /b /o-d "%PROJECT_ROOT%\releases" | findstr "offline_deploy_" | more +0 | findstr /n "^" | findstr "^[1-5]:"
echo.

pause
