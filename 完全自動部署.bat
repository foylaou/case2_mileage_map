@echo off
chcp 65001 >nul
echo ========================================
echo Vercel 完全自動部署腳本
echo ========================================
echo.
echo 這個腳本會嘗試自動完成所有部署步驟
echo.

REM 檢查必要工具
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] 需要安裝 Node.js
    start https://nodejs.org/
    pause
    exit /b 1
)

REM 安裝/檢查 Vercel CLI
vercel --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安裝 Vercel CLI...
    call npm install -g vercel --silent
)

echo.
echo ========================================
echo 方式一：嘗試使用現有登入狀態
echo ========================================
echo.

vercel whoami >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ 已登入，開始部署...
    echo.
    call vercel --yes --force
    if %errorlevel% equ 0 (
        echo.
        echo ========================================
        echo ✓ 部署成功！
        echo ========================================
        echo.
        echo 請記下上面顯示的 Vercel URL
        echo 並在 Vercel Dashboard 中設定環境變數
        echo.
        pause
        exit /b 0
    )
)

echo.
echo ========================================
echo 方式二：使用 API Token（推薦，完全自動化）
echo ========================================
echo.
echo 如果您有 Vercel API Token，可以完全自動化部署
echo.
echo 獲取 Token 的步驟：
echo 1. 前往 https://vercel.com/account/tokens
echo 2. 點擊 "Create Token"
echo 3. 輸入名稱並創建
echo 4. 複製 Token
echo.
set /p use_token=是否使用 API Token 部署？(Y/N): 

if /i "%use_token%"=="Y" (
    set /p token=請貼上您的 Vercel API Token: 
    if not "%token%"=="" (
        echo.
        echo 正在使用 Token 登入並部署...
        call vercel --token %token% --yes --force
        if %errorlevel% equ 0 (
            echo.
            echo ========================================
            echo ✓ 部署成功！
            echo ========================================
            echo.
            pause
            exit /b 0
        )
    )
)

echo.
echo ========================================
echo 方式三：使用瀏覽器登入
echo ========================================
echo.
echo 這將在瀏覽器中打開登入頁面
echo 完成登入後，腳本會自動繼續部署
echo.
pause

call vercel login
if %errorlevel% neq 0 (
    echo [錯誤] 登入失敗
    pause
    exit /b 1
)

echo.
echo ✓ 登入成功，開始部署...
echo.

call vercel --yes --force

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo ✓ 部署成功！
    echo ========================================
    echo.
) else (
    echo.
    echo [錯誤] 部署失敗
    echo.
)

pause

