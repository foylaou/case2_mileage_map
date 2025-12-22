@echo off
chcp 65001 >nul
title 啟動完整服務 - Case 2 里程地圖系統
color 0E

echo ========================================
echo   啟動完整服務
echo   Case 2: 地點里程與地圖報表系統
echo ========================================
echo.

REM 切換到專案根目錄
cd /d "%~dp0"
if errorlevel 1 (
    echo ❌ 錯誤：無法切換到專案目錄
    pause
    exit /b 1
)

echo ✅ 目錄檢查完成
echo.
echo ========================================
echo   服務資訊
echo ========================================
echo   整合服務: http://localhost:5001
echo   主要頁面: http://localhost:5001/
echo.
echo ========================================
echo   正在啟動服務...
echo ========================================
echo.

REM 檢查 Python 是否可用
where py >nul 2>&1
if errorlevel 1 (
    echo ❌ 錯誤：找不到 Python
    echo 請確認 Python 已安裝並加入 PATH
    pause
    exit /b 1
)

REM 啟動整合服務（使用 main.py，整合前端和後端）
echo 正在啟動整合服務（前端+後端）...
start "Case 2 里程地圖系統" cmd /k "cd /d %~dp0backend && py main.py"

REM 等待服務啟動
echo 等待服務啟動（5秒）...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo   ✅ 服務啟動完成
echo ========================================
echo.
echo 📋 服務狀態：
echo   ✅ 整合服務：http://localhost:5001
echo.
echo 📋 使用方式：
echo   1. 瀏覽器會自動開啟應用程式
echo   2. 或手動開啟：http://localhost:5001/
echo   3. 服務視窗標題為「Case 2 里程地圖系統」
echo.
echo 💡 提示：
echo   - 關閉對應的視窗即可停止該服務
echo   - 或按 Ctrl+C 停止服務
echo.
echo ========================================
echo   正在開啟瀏覽器...
echo ========================================
echo.

REM 開啟瀏覽器
timeout /t 2 /nobreak >nul
start http://localhost:5001/

echo ✅ 瀏覽器已開啟
echo.
echo 服務正在運行中，請保持視窗開啟
echo 要停止服務，請關閉對應的服務視窗
echo.
pause




