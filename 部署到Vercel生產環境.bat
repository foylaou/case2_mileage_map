@echo off
chcp 65001 >nul
echo ========================================
echo Vercel 生產環境部署腳本
echo ========================================
echo.

REM 檢查 Node.js 是否安裝
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] 未檢測到 Node.js
    echo 請先安裝 Node.js: https://nodejs.org/
    pause
    exit /b 1
)

echo [1/4] 檢查 Vercel CLI...
vercel --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Vercel CLI 未安裝，正在安裝...
    call npm install -g vercel
    if %errorlevel% neq 0 (
        echo [錯誤] Vercel CLI 安裝失敗
        pause
        exit /b 1
    )
    echo ✓ Vercel CLI 安裝成功
) else (
    echo ✓ Vercel CLI 已安裝
)

echo.
echo [2/4] 檢查登入狀態...
vercel whoami >nul 2>&1
if %errorlevel% neq 0 (
    echo 請在瀏覽器中完成 Vercel 登入...
    call vercel login
    if %errorlevel% neq 0 (
        echo [錯誤] Vercel 登入失敗
        pause
        exit /b 1
    )
) else (
    echo ✓ 已登入 Vercel
)

echo.
echo [3/4] 檢查環境變數...
echo ⚠️  請確認已在 Vercel Dashboard 中設定以下環境變數：
echo   - SECRET_KEY
echo   - JWT_SECRET_KEY
echo   - DATABASE_URI
echo   - GOOGLE_MAPS_API_KEY
echo.
echo 如果尚未設定，請前往 Vercel Dashboard 設定後再繼續
echo.
pause

echo.
echo [4/4] 開始部署到生產環境...
echo.
echo ⚠️  這將部署到生產環境（production）
echo.
pause

call vercel --prod

echo.
echo ========================================
echo 部署完成！
echo ========================================
echo.
echo 您的應用程式已部署到生產環境
echo 請記下 Vercel 提供的 URL
echo.
pause

