@echo off
chcp 65001 > nul
echo ========================================
echo   启动前端 (端口: 5173)
echo ========================================
echo.

echo 清理Vite缓存...
if exist "node_modules\.vite" (
    rmdir /S /Q "node_modules\.vite"
    echo ✅ 缓存已清理
)

echo.
echo 启动中...
npm run dev

pause

