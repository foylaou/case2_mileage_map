@echo off
chcp 65001 >nul
echo ========================================
echo Vercel 部署助手
echo ========================================
echo.
echo 請選擇部署方式：
echo.
echo [1] 使用 Vercel Dashboard（推薦，最簡單）
echo [2] 使用命令列（需要先登入 Vercel）
echo [3] 查看部署說明文件
echo [0] 取消
echo.
set /p choice=請輸入選項 (1/2/3/0): 

if "%choice%"=="1" goto dashboard
if "%choice%"=="2" goto cli
if "%choice%"=="3" goto help
if "%choice%"=="0" goto end
goto invalid

:dashboard
echo.
echo ========================================
echo 使用 Vercel Dashboard 部署
echo ========================================
echo.
echo 步驟：
echo 1. 將專案推送到 GitHub（如果還沒有）
echo 2. 前往 https://vercel.com/dashboard
echo 3. 點擊 "Add New Project"
echo 4. 選擇您的 GitHub 倉庫
echo 5. 設定環境變數（見下方）
echo 6. 點擊 "Deploy"
echo.
echo 必須設定的環境變數：
echo   - SECRET_KEY
echo   - JWT_SECRET_KEY
echo   - DATABASE_URI
echo   - GOOGLE_MAPS_API_KEY
echo.
echo 詳細說明請參考：VERCEL_DEPLOY.md
echo.
pause
goto end

:cli
echo.
echo ========================================
echo 使用命令列部署
echo ========================================
echo.
echo 正在檢查 Vercel CLI...
vercel --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Vercel CLI 未安裝，正在安裝...
    call npm install -g vercel
    if %errorlevel% neq 0 (
        echo [錯誤] Vercel CLI 安裝失敗
        pause
        goto end
    )
)

echo.
echo 正在檢查登入狀態...
vercel whoami >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo 需要先登入 Vercel
    echo 這將在瀏覽器中打開登入頁面
    echo.
    pause
    call vercel login
    if %errorlevel% neq 0 (
        echo [錯誤] 登入失敗
        pause
        goto end
    )
)

echo.
echo 開始部署到預覽環境...
echo.
call vercel

echo.
echo 如需部署到生產環境，請執行：vercel --prod
echo.
pause
goto end

:help
echo.
echo 正在打開部署說明文件...
start "" "VERCEL_DEPLOY.md"
pause
goto end

:invalid
echo.
echo [錯誤] 無效的選項
pause
goto end

:end
echo.
echo 感謝使用！
exit /b 0

