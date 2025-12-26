@echo off
chcp 65001 >nul
echo ========================================
echo 清理 Vite 缓存并重启开发服务器
echo ========================================
echo.

echo 1. 停止开发服务器（如果正在运行）...
taskkill /F /IM node.exe 2>nul
timeout /t 2 >nul

echo 2. 清理 Vite 缓存...
if exist node_modules\.vite (
    rmdir /s /q node_modules\.vite
    echo    ✅ Vite 缓存已清理
) else (
    echo    ⚠️  Vite 缓存目录不存在
)

echo 3. 清理 dist 目录...
if exist dist (
    rmdir /s /q dist
    echo    ✅ dist 目录已清理
) else (
    echo    ⚠️  dist 目录不存在
)

echo.
echo ========================================
echo ✅ 缓存清理完成！
echo ========================================
echo.
echo 请手动执行以下命令启动开发服务器：
echo    cd web
echo    npm run dev
echo.
echo 或者在新的命令行窗口中执行：
echo    pnpm dev
echo.

pause
