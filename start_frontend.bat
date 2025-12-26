@echo off
chcp 65001 >nul
title 前端服務 - Case 2 里程地圖系統
color 0B

echo ========================================
echo   啟動前端服務
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
echo   前端地址: http://localhost:8000
echo   主要頁面: http://localhost:8000/excel-upload.html
echo   其他頁面:
echo     - http://localhost:8000/index.html
echo     - http://localhost:8000/mileage-map.html
echo     - http://localhost:8000/reports.html
echo     - http://localhost:8000/settings.html
echo.
echo ========================================
echo   正在啟動前端服務...
echo ========================================
echo.
echo 💡 提示：
echo   - 服務啟動後，瀏覽器會自動開啟
echo   - 按 Ctrl+C 可停止服務
echo   - 請確保後端服務已啟動（http://localhost:5001）
echo.
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

REM 啟動 Python HTTP Server
echo 正在啟動 Python HTTP Server...
echo.
py -m http.server 8000

REM 如果服務意外停止，顯示訊息
echo.
echo ========================================
echo   服務已停止
echo ========================================
echo.
pause




