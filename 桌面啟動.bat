@echo off
chcp 65001 >nul
title 啟動完整服務 - Case 2 里程地圖系統
color 0E

echo ========================================
echo   啟動完整服務
echo   Case 2: 地點里程與地圖報表系統
echo ========================================
echo.

REM ========================================
REM 請修改下面的路徑為您的專案實際位置
REM ========================================
REM 如果 bat 檔在專案目錄中，使用這一行（預設）
set PROJECT_DIR=%~dp0

REM 如果 bat 檔在桌面，請取消下面一行的註解並修改為您的專案路徑
REM 例如：set PROJECT_DIR=C:\Users\您的用戶名\Downloads\1107\1107\case2_mileage_map
REM set PROJECT_DIR=C:\Users\l0987\Downloads\1107\1107\case2_mileage_map

REM 檢查專案目錄是否存在
if not exist "%PROJECT_DIR%backend\main.py" (
    echo ❌ 錯誤：找不到專案目錄
    echo.
    echo 當前嘗試的路徑: %PROJECT_DIR%
    echo.
    echo 請執行以下步驟：
    echo 1. 用記事本打開此 bat 檔
    echo 2. 找到「set PROJECT_DIR=」這一行
    echo 3. 取消註解並修改為您的專案完整路徑
    echo    例如：set PROJECT_DIR=C:\Users\您的用戶名\Downloads\1107\1107\case2_mileage_map
    echo.
    pause
    exit /b 1
)

REM 切換到專案根目錄
cd /d "%PROJECT_DIR%"
if errorlevel 1 (
    echo ❌ 錯誤：無法切換到專案目錄
    pause
    exit /b 1
)

echo ✅ 目錄檢查完成
echo   專案路徑: %PROJECT_DIR%
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
where python >nul 2>&1
if errorlevel 1 (
    echo ❌ 錯誤：找不到 Python
    echo 請確認 Python 已安裝並加入 PATH
    pause
    exit /b 1
)

REM 啟動整合服務（使用 main.py，整合前端和後端）
echo 正在啟動整合服務（前端+後端）...
start "Case 2 里程地圖系統" cmd /k "cd /d %PROJECT_DIR%backend && python main.py"

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
