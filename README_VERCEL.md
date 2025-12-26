# Vercel 部署快速指南

## 快速開始

1. **將專案推送到 Git 倉庫**（GitHub/GitLab/Bitbucket）

2. **在 Vercel Dashboard 匯入專案**
   - 前往 https://vercel.com/dashboard
   - 點擊「Add New Project」
   - 選擇您的 Git 倉庫

3. **設定環境變數**
   在 Vercel Dashboard 的專案設定中，新增：
   ```
   SECRET_KEY=your-secret-key
   JWT_SECRET_KEY=your-jwt-secret-key
   DATABASE_URI=your-database-uri
   GOOGLE_MAPS_API_KEY=your-google-maps-api-key
   ```

4. **部署**
   - 點擊「Deploy」
   - 等待部署完成

## 重要提醒

⚠️ **資料庫**：Vercel 不支援本地檔案系統，必須使用外部資料庫（MySQL/PostgreSQL/MongoDB）

⚠️ **檔案儲存**：暫存檔案不會持久化，建議使用外部儲存服務（S3、Cloudinary 等）

⚠️ **Playwright**：在 Vercel 的 serverless 環境中可能無法正常運作，建議使用 Google Maps Static API

詳細說明請參考：`VERCEL_DEPLOY.md`

