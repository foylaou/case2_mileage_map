# 第二案：地點里程與地圖報表系統

## 專案說明

本專案為「地點里程與地圖報表系統」，提供 Excel 上傳、自動計算里程、Google Map 圖片下載、Word 報表匯出等功能。

## 系統架構

- **後端**：Python Flask
- **前端**：HTML + JavaScript + Bootstrap 5
- **資料庫**：MySQL（可選）
- **API 服務**：Google Maps API（Directions API、Static Maps API）

## 快速開始

### 1. 環境準備

#### 後端環境

```bash
# 進入後端目錄
cd case2_mileage_map/backend

# 建立虛擬環境（建議）
python -m venv venv

# 啟動虛擬環境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安裝相依套件
pip install -r requirements.txt
```

#### 環境變數設定

複製 `env_template.txt` 為 `.env` 並填入實際值：

```bash
cp env_template.txt .env
```

編輯 `.env` 檔案：

```env
# 應用程式設定
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
DEBUG=False
HOST=0.0.0.0
PORT=5001

# 資料庫設定（可選，如果不需要資料庫功能可省略）
DATABASE_URI=mysql+pymysql://user:password@localhost/mileage_map

# Google Maps API 設定（必要）
GOOGLE_MAPS_API_KEY=your-google-maps-api-key-here
```

### 2. 建立必要目錄

```bash
cd case2_mileage_map/backend

# 建立暫存和輸出目錄
mkdir -p temp/maps
mkdir -p output
mkdir -p logs
```

### 3. 安裝必要套件

```bash
cd case2_mileage_map/backend

# 安裝所有相依套件
py -m pip install -r requirements.txt
```

**注意：** 如果遇到 Pillow 安裝問題（Python 3.13），可以單獨安裝其他套件：

```bash
py -m pip install Flask Flask-CORS Flask-JWT-Extended Flask-SQLAlchemy PyMySQL googlemaps requests openpyxl python-docx pandas reportlab python-dotenv loguru
```

### 4. 啟動後端服務

#### 方式一：雙擊啟動（最簡單，推薦）

**Windows:**
直接在專案根目錄雙擊 `啟動後端服務.bat` 即可啟動後端服務。

#### 方式二：使用啟動腳本

**Windows:**
```bash
cd case2_mileage_map/backend
start.bat
```

**Linux/Mac:**
```bash
cd case2_mileage_map/backend
chmod +x start.sh
./start.sh
```

#### 方式三：手動啟動

**Windows:**
```bash
cd case2_mileage_map/backend
py app.py
```

**Linux/Mac:**
```bash
cd case2_mileage_map/backend
python app.py
```

後端服務將運行在：**http://localhost:5001**

**啟動成功後應該看到：**
```
啟動 Flask 服務在 http://0.0.0.0:5001
健康檢查: http://localhost:5001/health
 * Running on http://127.0.0.1:5001
```

#### 驗證後端服務

在瀏覽器開啟以下網址確認服務是否正常：

- **簡單健康檢查**：http://localhost:5001/health
  - 應該回傳：`{"status": "ok"}`

- **詳細健康檢查**：http://localhost:5001/api/health
  - 回傳服務和資料庫狀態

### 5. 啟動前端

前端為純 HTML/JavaScript，有多種啟動方式：

#### 方式一：雙擊啟動（最簡單，推薦）

**Windows:**
直接在專案根目錄雙擊 `啟動前端服務.bat` 或 `start_frontend.bat` 即可啟動前端服務。

**Linux/Mac:**
```bash
cd case2_mileage_map
chmod +x start_frontend.sh
./start_frontend.sh
```

#### 方式二：使用 Python HTTP Server

```bash
# 在 case2_mileage_map 目錄下執行
python -m http.server 8000
```

然後在瀏覽器開啟：http://localhost:8000/excel-upload.html

#### 方式三：使用 Node.js http-server

```bash
# 安裝 http-server（如果尚未安裝）
npm install -g http-server

# 在 case2_mileage_map 目錄下執行
http-server -p 8000
```

然後在瀏覽器開啟：http://localhost:8000/excel-upload.html

#### 方式四：直接開啟（不推薦，可能有 CORS 問題）

直接在瀏覽器中開啟 `excel-upload.html`

## 功能說明

### Excel 上傳與解析

1. 上傳 Excel 檔案（支援 `.xlsx`、`.xls`）
2. 系統自動解析必要欄位：
   - 部門
   - 姓名
   - 計畫別（ProjectName）
   - 起點名稱
   - 出差日期時間（開始）
   - 出差日期時間（結束）
   - 目的地名稱
   - IsDriving（是否自駕，Y/N）
3. 依計畫別自動分組
4. 依出差日期排序

### 里程計算

- 使用 Google Maps Directions API 計算距離
- 支援批次計算
- 自動下載靜態地圖圖片
- 產生 Google Maps 導航 URL

### 報表匯出

- **Excel 匯出**：更新後的 Excel 檔案（含計算結果）
- **Word 匯出**：依計畫別產生 Word 報表（含地圖圖片）
- **批次匯出**：一次匯出所有計畫別的 Word 報表（ZIP 壓縮檔）

## API 端點

### 健康檢查

- `GET /health` - 簡單健康檢查，回傳 `{"status": "ok"}`
- `GET /api/health` - 詳細健康檢查（含資料庫狀態）

### 上傳相關

- `POST /api/upload/excel` - 上傳並解析 Excel 檔案

### 計算相關

- `POST /api/calculate/distance` - 計算單筆距離
- `POST /api/calculate/batch` - 批次計算多筆距離

### 匯出相關

- `POST /api/export/excel` - 匯出更新後的 Excel 檔案
- `POST /api/export/word` - 匯出單一計畫別的 Word 報表
- `POST /api/export/word/batch` - 批次匯出多個計畫別的 Word 報表（ZIP）

## 檔案結構

```
case2_mileage_map/
├── backend/
│   ├── app.py                    # Flask 主應用程式
│   ├── routes/                   # 新功能路由
│   │   ├── upload.py            # Excel 上傳路由
│   │   ├── calculate.py          # 里程計算路由
│   │   └── export.py            # 匯出功能路由
│   ├── services/                 # 服務層
│   │   ├── excel_service.py      # Excel 處理服務
│   │   ├── google_maps_service.py # Google Maps API 服務
│   │   ├── word_service.py       # Word 報表產生服務
│   │   └── place_mapping.py      # 地點名稱對應服務
│   ├── api/                      # 原有 API 路由
│   ├── models/                   # 資料模型
│   ├── utils/                    # 工具函式
│   ├── temp/                     # 暫存檔案目錄
│   │   └── maps/                 # 靜態地圖圖片
│   ├── output/                    # 匯出檔案目錄
│   ├── logs/                      # 日誌檔案目錄
│   ├── requirements.txt          # Python 相依套件
│   └── env_template.txt          # 環境變數範本
├── excel-upload.html             # Excel 上傳主頁面
├── index.html                    # 原有首頁
├── css/                          # 樣式檔案
├── js/                           # JavaScript 檔案
└── README.md                     # 本檔案
```

## 測試用 Excel 格式

Excel 檔案應包含以下欄位：

| 部門 | 姓名 | 計畫別 | 起點名稱 | 出差日期時間（開始） | 出差日期時間（結束） | 目的地名稱 | IsDriving |
|------|------|--------|----------|---------------------|---------------------|------------|-----------|
| 研發部 | 張三 | IDA智慧工安 | 安環高雄處 | 2024-01-15 09:00 | 2024-01-15 17:00 | 經濟部產業園區管理局 | Y |

## 常見問題

### Q: 無法連接到後端服務

**檢查步驟：**

1. 確認後端服務是否已啟動
   ```bash
   # 檢查健康狀態
   curl http://localhost:5001/health
   # 或直接在瀏覽器開啟
   http://localhost:5001/health
   ```

2. 確認 port 5001 沒有被其他程式占用
   ```bash
   # Windows
   netstat -ano | findstr :5001
   
   # Linux/Mac
   lsof -i :5001
   ```

3. 檢查防火牆設定

4. 確認前端 API URL 設定正確（`http://localhost:5001/api`）

### Q: Google Maps API 錯誤

- 確認 API Key 已正確設定在 `.env` 檔案中
- 確認已啟用 Directions API 和 Static Maps API
- 檢查 API 使用配額

### Q: 地點名稱找不到對應地址

- 可在 `backend/services/place_mapping.py` 中新增地點對應
- 系統會嘗試使用 Google Maps Geocoding API 自動解析

## 開發說明

### 後端開發

- 使用 Flask 框架
- 遵循 RESTful API 設計
- 所有錯誤都有適當的錯誤處理和日誌記錄

### 前端開發

- 純 HTML/JavaScript，無需編譯
- 使用 Bootstrap 5 作為 UI 框架
- API 呼叫使用 Fetch API

## 授權

本專案為內部使用專案。
