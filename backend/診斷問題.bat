@echo off
chcp 65001 >nul
echo ========================================
echo 系統診斷工具
echo ========================================
echo.

echo [1] 檢查 Python 環境...
python --version
if %errorlevel% neq 0 (
    echo ✗ Python 未安裝或不在 PATH 中
    echo   請先安裝 Python 3.8 或更高版本
    pause
    exit /b 1
)
echo ✓ Python 已安裝
echo.

echo [2] 檢查是否在正確目錄...
if not exist "app.py" (
    echo ✗ 找不到 app.py，請確認在 backend 目錄下執行
    echo   當前目錄: %CD%
    pause
    exit /b 1
)
echo ✓ 目錄正確
echo.

echo [3] 檢查必要目錄...
if not exist "temp" mkdir temp
if not exist "temp\maps" mkdir temp\maps
if not exist "output" mkdir output
if not exist "logs" mkdir logs
echo ✓ 目錄已建立
echo.

echo [4] 檢查 .env 檔案...
if not exist ".env" (
    echo ⚠ 找不到 .env 檔案
    if exist "env_template.txt" (
        echo   正在從 env_template.txt 複製...
        copy env_template.txt .env >nul
        echo ✓ 已建立 .env 檔案，請編輯填入 Google Maps API Key
    ) else (
        echo ✗ 找不到 env_template.txt
    )
) else (
    echo ✓ .env 檔案存在
)
echo.

echo [5] 檢查端口 5001 是否被占用...
netstat -ano | findstr ":5001" >nul
if %errorlevel% equ 0 (
    echo ⚠ 端口 5001 已被占用
    echo   正在顯示占用進程...
    netstat -ano | findstr ":5001"
    echo.
    echo   請關閉占用端口的程式，或修改 .env 中的 PORT 設定
) else (
    echo ✓ 端口 5001 可用
)
echo.

echo [6] 檢查 Python 套件...
echo   正在檢查必要套件...
python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo ✗ Flask 未安裝
    echo   請執行: pip install -r requirements.txt
) else (
    echo ✓ Flask 已安裝
)

python -c "import flask_cors" 2>nul
if %errorlevel% neq 0 (
    echo ✗ Flask-CORS 未安裝
) else (
    echo ✓ Flask-CORS 已安裝
)

python -c "from dotenv import load_dotenv" 2>nul
if %errorlevel% neq 0 (
    echo ✗ python-dotenv 未安裝
) else (
    echo ✓ python-dotenv 已安裝
)
echo.

echo [7] 嘗試啟動服務...
echo   如果出現錯誤，請查看下方訊息
echo.
echo ========================================
echo 啟動服務...
echo ========================================
echo.

python app.py

pause


