@echo off
chcp 65001 >nul
echo ========================================
echo 使用 Vercel API Token 自動部署
echo ========================================
echo.
echo 這個方式可以完全自動化部署，無需瀏覽器互動
echo.
echo 步驟：
echo 1. 前往 https://vercel.com/account/tokens
echo 2. 點擊 "Create Token"
echo 3. 輸入 Token 名稱（例如：deployment-token）
echo 4. 選擇過期時間（建議：Never）
echo 5. 點擊 "Create"
echo 6. 複製生成的 Token
echo.
set /p token=請貼上您的 Vercel API Token: 

if "%token%"=="" (
    echo [錯誤] Token 不能為空
    pause
    exit /b 1
)

echo.
echo 正在使用 Token 登入...
call vercel login --token %token%

if %errorlevel% neq 0 (
    echo [錯誤] 登入失敗，請檢查 Token 是否正確
    pause
    exit /b 1
)

echo.
echo ✓ 登入成功
echo.
echo 開始部署...
echo.

call vercel --yes

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo ✓ 部署成功！
    echo ========================================
    echo.
    echo 請記下上面顯示的 Vercel URL
    echo 並在 Vercel Dashboard 中設定環境變數
    echo.
) else (
    echo.
    echo [錯誤] 部署失敗
    echo.
)

pause

