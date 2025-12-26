@echo off
chcp 65001 >nul
echo ========================================
echo Vercel 自動部署腳本
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

echo [1/5] 檢查 Vercel CLI...
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
echo [2/5] 檢查 Git 倉庫...
git status >nul 2>&1
if %errorlevel% neq 0 (
    echo Git 倉庫未初始化，正在初始化...
    call git init
    call git add .
    call git commit -m "Initial commit for Vercel deployment"
    echo.
    echo ⚠️  請先將專案推送到 GitHub/GitLab/Bitbucket
    echo 然後再執行此腳本進行部署
    echo.
    echo 或者，您可以直接使用 Vercel Dashboard 部署：
    echo 1. 前往 https://vercel.com/dashboard
    echo 2. 點擊 "Add New Project"
    echo 3. 選擇您的 Git 倉庫
    echo.
    pause
    exit /b 0
) else (
    echo ✓ Git 倉庫已初始化
)

echo.
echo [3/5] 檢查環境變數設定...
if not exist .env (
    echo ⚠️  未找到 .env 檔案
    echo 請在 Vercel Dashboard 中設定以下環境變數：
    echo   - SECRET_KEY
    echo   - JWT_SECRET_KEY
    echo   - DATABASE_URI
    echo   - GOOGLE_MAPS_API_KEY
    echo.
)

echo.
echo [4/5] 登入 Vercel...
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
echo [5/5] 開始部署到 Vercel...
echo.
echo 這將部署到預覽環境，部署完成後會顯示 URL
echo 如需部署到生產環境，請執行: vercel --prod
echo.
pause

call vercel

echo.
echo ========================================
echo 部署完成！
echo ========================================
echo.
echo 如果部署成功，您會看到一個 Vercel URL
echo 請記下這個 URL，並在 Vercel Dashboard 中設定環境變數
echo.
pause

