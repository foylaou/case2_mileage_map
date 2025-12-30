@echo off
chcp 65001 >nul
title Vercel 自動部署
color 0A
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║          Vercel 自動部署腳本 - 一鍵部署                ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

REM 檢查 Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [✗] 未檢測到 Node.js
    echo.
    echo 正在打開 Node.js 下載頁面...
    start https://nodejs.org/
    echo 請先安裝 Node.js，然後重新執行此腳本
    pause
    exit /b 1
)
echo [✓] Node.js 已安裝

REM 檢查/安裝 Vercel CLI
echo [1/5] 檢查 Vercel CLI...
vercel --version >nul 2>&1
if %errorlevel% neq 0 (
    echo     正在安裝 Vercel CLI（這可能需要幾分鐘）...
    call npm install -g vercel --silent
    if %errorlevel% neq 0 (
        echo [✗] Vercel CLI 安裝失敗
        pause
        exit /b 1
    )
)
for /f "tokens=*" %%i in ('vercel --version') do set VERCEL_VERSION=%%i
echo     [✓] Vercel CLI %VERCEL_VERSION%

REM 檢查登入狀態
echo.
echo [2/5] 檢查 Vercel 登入狀態...
vercel whoami >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('vercel whoami') do set VERCEL_USER=%%i
    echo     [✓] 已登入為: %VERCEL_USER%
    goto deploy
)

REM 需要登入
echo     [⚠] 尚未登入 Vercel
echo.
echo ═══════════════════════════════════════════════════════════
echo 登入方式選擇
echo ═══════════════════════════════════════════════════════════
echo.
echo [1] 使用瀏覽器登入（推薦，簡單快速）
echo [2] 使用 API Token 登入（完全自動化，無需瀏覽器）
echo [0] 取消
echo.
set /p login_choice=請選擇 (1/2/0): 

if "%login_choice%"=="0" exit /b 0
if "%login_choice%"=="2" goto token_login
if not "%login_choice%"=="1" goto invalid_choice

REM 瀏覽器登入
echo.
echo [3/5] 正在打開瀏覽器登入頁面...
echo     請在瀏覽器中完成登入
echo     完成後，腳本會自動繼續...
echo.
call vercel login
if %errorlevel% neq 0 (
    echo [✗] 登入失敗
    pause
    exit /b 1
)
goto deploy

:token_login
echo.
echo ═══════════════════════════════════════════════════════════
echo 使用 API Token 登入
echo ═══════════════════════════════════════════════════════════
echo.
echo 獲取 Token 的步驟：
echo 1. 前往 https://vercel.com/account/tokens
echo 2. 點擊 "Create Token"
echo 3. 輸入 Token 名稱（例如：deployment）
echo 4. 選擇過期時間（建議：Never）
echo 5. 點擊 "Create"
echo 6. 複製生成的 Token
echo.
echo 正在打開 Token 創建頁面...
start https://vercel.com/account/tokens
echo.
set /p token=請貼上您的 Vercel API Token: 

if "%token%"=="" (
    echo [✗] Token 不能為空
    pause
    exit /b 1
)

echo.
echo [3/5] 正在使用 Token 登入...
call vercel login --token %token%
if %errorlevel% neq 0 (
    echo [✗] 登入失敗，請檢查 Token 是否正確
    pause
    exit /b 1
)
echo     [✓] 登入成功

:deploy
REM 檢查專案配置
echo.
echo [4/5] 檢查專案配置...
if not exist "vercel.json" (
    echo [✗] 找不到 vercel.json
    pause
    exit /b 1
)
if not exist "api\index.py" (
    echo [✗] 找不到 api\index.py
    pause
    exit /b 1
)
echo     [✓] 專案配置完整

REM 開始部署
echo.
echo [5/5] 開始部署到 Vercel...
echo.
echo ═══════════════════════════════════════════════════════════
echo 正在部署，請稍候...
echo ═══════════════════════════════════════════════════════════
echo.

call vercel --yes --force

if %errorlevel% equ 0 (
    echo.
    echo ╔══════════════════════════════════════════════════════════╗
    echo ║                    ✓ 部署成功！                          ║
    echo ╚══════════════════════════════════════════════════════════╝
    echo.
    echo ═══════════════════════════════════════════════════════════
    echo 重要：設定環境變數
    echo ═══════════════════════════════════════════════════════════
    echo.
    echo 部署完成後，請前往 Vercel Dashboard 設定環境變數：
    echo.
    echo   1. 前往: https://vercel.com/dashboard
    echo   2. 選擇您的專案
    echo   3. 進入 Settings ^> Environment Variables
    echo   4. 新增以下環境變數：
    echo.
    echo      • SECRET_KEY
    echo      • JWT_SECRET_KEY
    echo      • DATABASE_URI
    echo      • GOOGLE_MAPS_API_KEY
    echo.
    echo 設定完成後，應用程式才能正常運作
    echo.
    echo 正在打開 Vercel Dashboard...
    timeout /t 3 >nul
    start https://vercel.com/dashboard
) else (
    echo.
    echo ╔══════════════════════════════════════════════════════════╗
    echo ║                    ✗ 部署失敗                            ║
    echo ╚══════════════════════════════════════════════════════════╝
    echo.
    echo 可能的原因：
    echo   • 網路連線問題
    echo   • Vercel 服務暫時不可用
    echo   • 專案配置有誤
    echo.
    echo 請檢查上面的錯誤訊息，或稍後再試
    echo.
)

pause
exit /b 0

:invalid_choice
echo [✗] 無效的選項
pause
exit /b 1

