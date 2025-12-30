@echo off
chcp 65001 >nul
echo ========================================
echo Vercel 一鍵自動部署
echo ========================================
echo.

REM 檢查 Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] 未檢測到 Node.js，請先安裝 Node.js
    echo 下載地址: https://nodejs.org/
    pause
    exit /b 1
)

REM 檢查並安裝 Vercel CLI
echo [1/4] 檢查 Vercel CLI...
vercel --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安裝 Vercel CLI...
    call npm install -g vercel
    if %errorlevel% neq 0 (
        echo [錯誤] Vercel CLI 安裝失敗
        pause
        exit /b 1
    )
)
echo ✓ Vercel CLI 已就緒

REM 檢查登入狀態
echo.
echo [2/4] 檢查 Vercel 登入狀態...
vercel whoami >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ⚠️  尚未登入 Vercel
    echo.
    echo 正在嘗試自動登入...
    echo 這將在瀏覽器中打開登入頁面
    echo 請完成登入後，腳本會自動繼續...
    echo.
    call vercel login
    if %errorlevel% neq 0 (
        echo.
        echo [錯誤] 登入失敗
        echo.
        echo 替代方案：使用 API Token 登入
        echo 1. 前往 https://vercel.com/account/tokens
        echo 2. 創建一個新的 Token
        echo 3. 執行: vercel login --token YOUR_TOKEN
        echo.
        pause
        exit /b 1
    )
) else (
    echo ✓ 已登入 Vercel
)

REM 檢查專案配置
echo.
echo [3/4] 檢查專案配置...
if not exist "vercel.json" (
    echo [錯誤] 找不到 vercel.json 配置檔案
    pause
    exit /b 1
)
if not exist "api\index.py" (
    echo [錯誤] 找不到 api\index.py 檔案
    pause
    exit /b 1
)
echo ✓ 專案配置完整

REM 開始部署
echo.
echo [4/4] 開始部署到 Vercel...
echo.
echo 這將部署到預覽環境
echo 部署完成後會顯示 URL
echo.
echo 正在部署，請稍候...
echo.

call vercel --yes --force

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo ✓ 部署成功！
    echo ========================================
    echo.
    echo 重要提醒：
    echo 1. 請記下上面顯示的 Vercel URL
    echo 2. 前往 Vercel Dashboard 設定環境變數：
    echo    - SECRET_KEY
    echo    - JWT_SECRET_KEY
    echo    - DATABASE_URI
    echo    - GOOGLE_MAPS_API_KEY
    echo.
    echo 設定環境變數後，應用程式才能正常運作
    echo.
) else (
    echo.
    echo ========================================
    echo [錯誤] 部署失敗
    echo ========================================
    echo.
    echo 可能的原因：
    echo 1. 網路連線問題
    echo 2. Vercel 服務暫時不可用
    echo 3. 專案配置有誤
    echo.
    echo 請檢查上面的錯誤訊息，或稍後再試
    echo.
)

pause

