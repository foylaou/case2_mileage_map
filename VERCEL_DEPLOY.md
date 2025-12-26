# Vercel 部署指南

本文件說明如何將「地點里程與地圖報表系統」部署到 Vercel。

## 前置需求

1. **Vercel 帳號**：前往 [vercel.com](https://vercel.com) 註冊
2. **Vercel CLI**（可選）：`npm i -g vercel`
3. **Git 倉庫**：將專案推送到 GitHub/GitLab/Bitbucket

## 部署步驟

### 方式一：透過 Vercel Dashboard（推薦）

1. **登入 Vercel Dashboard**
   - 前往 https://vercel.com/dashboard
   - 使用 GitHub/GitLab/Bitbucket 帳號登入

2. **匯入專案**
   - 點擊「Add New Project」
   - 選擇您的 Git 倉庫
   - 選擇專案根目錄（`case2_mileage_map`）

3. **設定專案**
   - **Framework Preset**: 選擇「Other」或「Python」
   - **Root Directory**: `./`（專案根目錄）
   - **Build Command**: 留空（不需要建置）
   - **Output Directory**: 留空
   - **Install Command**: `pip install -r backend/requirements.txt`

4. **設定環境變數**
   在 Vercel Dashboard 的專案設定中，新增以下環境變數：

   ```
   SECRET_KEY=your-secret-key-here
   JWT_SECRET_KEY=your-jwt-secret-key-here
   DEBUG=False
   DATABASE_URI=your-database-uri-here
   GOOGLE_MAPS_API_KEY=your-google-maps-api-key-here
   CUSTOM_DOMAIN=your-custom-domain.com（可選）
   ```

   **重要說明**：
   - `DATABASE_URI`：Vercel 不支援本地檔案系統，必須使用外部資料庫（如 MySQL、PostgreSQL、MongoDB Atlas）
   - `GOOGLE_MAPS_API_KEY`：必須設定有效的 Google Maps API Key
   - `CUSTOM_DOMAIN`：如果使用自訂域名，請設定此變數

5. **部署**
   - 點擊「Deploy」
   - 等待部署完成
   - 部署完成後，Vercel 會提供一個 URL（例如：`https://your-project.vercel.app`）

### 方式二：透過 Vercel CLI

1. **安裝 Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **登入 Vercel**
   ```bash
   vercel login
   ```

3. **部署**
   ```bash
   # 在專案根目錄執行
   vercel
   
   # 生產環境部署
   vercel --prod
   ```

4. **設定環境變數**
   ```bash
   vercel env add SECRET_KEY
   vercel env add JWT_SECRET_KEY
   vercel env add DATABASE_URI
   vercel env add GOOGLE_MAPS_API_KEY
   # ... 其他環境變數
   ```

## 專案結構說明

```
case2_mileage_map/
├── api/
│   └── index.py          # Vercel serverless function 入口
├── backend/              # Flask 後端應用程式
│   ├── app.py            # Flask 應用程式主檔案
│   ├── requirements.txt  # Python 相依套件
│   └── ...
├── excel-upload.html     # 前端頁面
├── vercel.json          # Vercel 配置檔案
├── .vercelignore        # Vercel 忽略檔案
└── VERCEL_DEPLOY.md     # 本文件
```

## 重要注意事項

### 1. 資料庫設定

Vercel 的 serverless 環境不支援本地檔案系統，因此：

- **不能使用 SQLite**：必須使用外部資料庫服務
- **推薦選項**：
  - **MySQL**: 使用 PlanetScale、AWS RDS、Google Cloud SQL
  - **PostgreSQL**: 使用 Supabase、Neon、AWS RDS
  - **MongoDB**: 使用 MongoDB Atlas

**範例 DATABASE_URI**：
```
# MySQL
DATABASE_URI=mysql+pymysql://user:password@host:port/database

# PostgreSQL
DATABASE_URI=postgresql://user:password@host:port/database

# MongoDB（需要調整程式碼以使用 pymongo）
DATABASE_URI=mongodb+srv://user:password@cluster.mongodb.net/database
```

### 2. 檔案儲存

Vercel 的 serverless 環境是**無狀態**的，因此：

- **暫存檔案**（`temp/`、`output/`）：不會持久化，每次請求後可能被清除
- **建議解決方案**：
  - 使用 **Vercel Blob Storage**（Vercel 提供的儲存服務）
  - 使用 **AWS S3**、**Google Cloud Storage**、**Cloudinary** 等外部儲存服務
  - 將檔案直接回傳給前端，不儲存在伺服器

### 3. Playwright/Headless Browser

Playwright 在 Vercel 的 serverless 環境中**可能無法正常運作**，因為：

- 需要安裝 Chromium 瀏覽器
- 需要較大的記憶體和執行時間
- Vercel 的免費方案有執行時間限制（10 秒）

**建議解決方案**：
- 使用 **Google Maps Static API** 替代 Playwright 截圖
- 使用 **外部服務**（如 Browserless.io）來執行 headless browser
- 將截圖功能移到**獨立的服務**（如 AWS Lambda、Google Cloud Functions）

### 4. CORS 設定

CORS 已自動調整以支援 Vercel 域名：

- 自動從 `VERCEL_URL` 環境變數獲取部署域名
- 支援自訂域名（透過 `CUSTOM_DOMAIN` 環境變數）
- 開發環境仍支援 `localhost`

### 5. 環境變數

所有敏感資訊（API Key、資料庫連線字串）都應透過 Vercel Dashboard 設定，**不要**提交到 Git 倉庫。

## 測試部署

部署完成後，測試以下端點：

1. **健康檢查**：`https://your-project.vercel.app/health`
2. **API 根路徑**：`https://your-project.vercel.app/`
3. **前端頁面**：`https://your-project.vercel.app/`
4. **API 端點**：`https://your-project.vercel.app/api/health`

## 疑難排解

### 問題 1：部署失敗

- 檢查 `requirements.txt` 是否包含所有相依套件
- 確認 Python 版本（Vercel 預設使用 Python 3.11）
- 查看 Vercel 部署日誌中的錯誤訊息

### 問題 2：資料庫連線失敗

- 確認 `DATABASE_URI` 環境變數已正確設定
- 確認資料庫服務允許來自 Vercel IP 的連線
- 檢查資料庫服務的連線限制（某些免費方案有連線數限制）

### 問題 3：CORS 錯誤

- 確認 `VERCEL_URL` 環境變數已自動設定
- 如果使用自訂域名，確認 `CUSTOM_DOMAIN` 已設定
- 檢查瀏覽器開發者工具中的 CORS 錯誤訊息

### 問題 4：檔案上傳/下載失敗

- 確認已使用外部儲存服務（Vercel 不支援本地檔案系統）
- 檢查檔案大小限制（Vercel 有請求大小限制）

## 進階設定

### 自訂域名

1. 在 Vercel Dashboard 中，進入專案設定
2. 選擇「Domains」
3. 新增您的域名
4. 按照指示設定 DNS 記錄
5. 設定 `CUSTOM_DOMAIN` 環境變數

### 持續部署（CI/CD）

Vercel 會自動監聽 Git 倉庫的推送，並自動部署：

- **main/master 分支**：自動部署到生產環境
- **其他分支**：自動部署到預覽環境

## 相關資源

- [Vercel 文件](https://vercel.com/docs)
- [Vercel Python Runtime](https://vercel.com/docs/runtimes/python)
- [Flask 部署指南](https://flask.palletsprojects.com/en/latest/deploying/)

## 支援

如有問題，請查看：
- Vercel 部署日誌
- 專案 GitHub Issues
- Vercel 社群論壇

