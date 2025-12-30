@echo off
chcp 65001 >nul
echo ========================================
echo Vercel 自動部署腳本
echo ========================================
echo.

REM 檢查 Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] 未檢測到 Node.js
    pause
    exit /b 1
)

REM 檢查 Vercel CLI
vercel --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安裝 Vercel CLI...
    call npm install -g vercel
)

echo.
echo 正在檢查 Vercel 登入狀態...
vercel whoami >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ⚠️  需要先登入 Vercel
    echo.
    echo 方式一：使用瀏覽器登入（推薦）
    echo   執行: vercel login
    echo   然後在瀏覽器中完成登入
    echo.
    echo 方式二：使用 API Token（完全自動化）
    echo   1. 前往 https://vercel.com/account/tokens
    echo   2. 創建一個新的 Token
    echo   3. 執行: vercel login --token YOUR_TOKEN
    echo.
    echo 正在嘗試使用瀏覽器登入...
    echo 請在瀏覽器中完成登入，然後按任意鍵繼續...
    call vercel login
    if %errorlevel% neq 0 (
        echo [錯誤] 登入失敗
        pause
        exit /b 1
    )
)

echo.
echo ✓ 已登入 Vercel
echo.
echo 開始部署到 Vercel...
echo.
echo 這將部署到預覽環境
echo 部署完成後會顯示 URL
echo.

REM 使用非互動式參數部署
call vercel --yes

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo ✓ 部署成功！
    echo ========================================
    echo.
    echo 請記下上面顯示的 Vercel URL
    echo 並在 Vercel Dashboard 中設定環境變數：
    echo   - SECRET_KEY
    echo   - JWT_SECRET_KEY
    echo   - DATABASE_URI
    echo   - GOOGLE_MAPS_API_KEY
    echo.
) else (
    echo.
    echo [錯誤] 部署失敗
    echo 請檢查錯誤訊息
    echo.
)

pause

