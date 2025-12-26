@echo off
chcp 65001 >nul
echo ========================================
echo Case 2: 地點里程與地圖報表系統
echo 開發模式啟動
echo ========================================
echo.

REM 檢查 Python 是否安裝
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 未找到 Python，請先安裝 Python
    pause
    exit /b 1
)

echo [資訊] 正在啟動服務...
echo [資訊] 服務將在 http://localhost:5001/ 啟動
echo [資訊] 瀏覽器將自動打開
echo.
echo 按 Ctrl+C 可停止服務
echo.

REM 啟動服務
python main.py

pause


