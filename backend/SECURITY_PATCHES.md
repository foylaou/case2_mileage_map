# 安全修補說明

## 修補的 CVE

本專案已修補以下 flask-cors 相關的 CVE：

1. **CVE-2024-6221 (7.5)** - Improper Access Control
2. **CVE-2024-1681 (5.3)** - Improper Output Neutralization for Logs
3. **CVE-2024-6866 (5.3)** - Case-Insensitive Path Matching in corydolphin/flask-cors
4. **CVE-2024-6844 (5.3)** - Inconsistent CORS Matching due to '+' handling in URL path

## 修補內容

### 1. 升級 Flask-CORS 版本

- **檔案**: `requirements.txt`
- **變更**: Flask-CORS 從 4.0.0 升級到 >=6.0.0
- **說明**: 新版本已修補上述所有 CVE

### 2. CORS 設定改為白名單方式

- **檔案**: `backend/main.py`, `backend/app.py`
- **變更**: 
  - 從 `CORS(app)` 改為明確的白名單設定
  - 只允許本機前端來源：`http://localhost:{port}` 和 `http://127.0.0.1:{port}`
  - 只對 `/api/*` 路徑啟用 CORS
  - 設定 `supports_credentials=False`
  - 明確指定允許的 methods 和 headers
  - 設定 `vary_header=True` 確保正確的 CORS 標頭變更

**修補的 CVE**:
- CVE-2024-6221: 透過白名單限制避免不當存取控制
- CVE-2024-6866: 新版本已修補大小寫匹配問題
- CVE-2024-6844: 新版本已修補 '+' 字元處理問題

### 3. 日誌安全修補

- **檔案**: 
  - `backend/utils/log_sanitizer.py` (新增)
  - `backend/routes/upload.py`
  - `backend/api/auth.py`
- **變更**:
  - 新增日誌清理工具函數，防止日誌注入攻擊
  - 所有使用者輸入（檔案名稱、路徑、使用者名稱）在記錄到日誌前都會經過清理
  - 移除 CR/LF 等控制字元，防止 log injection

**修補的 CVE**:
- CVE-2024-1681: 透過清理使用者輸入防止日誌注入攻擊

### 4. DEBUG 模式預設關閉

- **檔案**: `backend/main.py`, `backend/app.py`
- **變更**: 確保 production 環境預設 `DEBUG=False`
- **說明**: 避免 debug log 洩露敏感資訊

### 5. 自動化安全檢查

- **檔案**: `backend/security_check.py` (新增)
- **功能**: 
  - 驗證白名單 origin 檢查
  - 驗證 path 大小寫敏感性
  - 驗證 path '+' 字元處理
  - 驗證 CORS methods 和 headers 設定
  - 驗證 credentials 設定
  - 驗證非 API 路徑不允許 CORS

**使用方式**:
```bash
cd backend
python tests/test_cors_security.py
```

詳細說明請參考 `tests/README.md`

**重要說明：**
- Path 大小寫不一致的 CORS 行為是設計刻意限制，非漏洞
- 測試腳本會將大小寫不一致路徑的拒絕行為標示為 "Expected Reject"
- 這是為了修補 CVE-2024-6866 而採用的安全設計

## 測試驗證

執行安全檢查腳本：

```bash
# 1. 啟動 Flask 應用程式（在另一個終端）
cd backend
python main.py

# 2. 執行安全檢查（在新終端）
cd backend
python security_check.py
```

預期結果：所有測試應該通過（PASS）

## 相容性說明

- Flask-CORS >=6.0.0 與 Flask 3.0.0 相容
- 本修補不影響現有功能（exe 本機使用）
- 前端需要確保使用正確的 origin（localhost 或 127.0.0.1）

## 注意事項

1. 升級後請執行 `pip install -r requirements.txt` 更新套件
2. 如果前端使用其他 origin，需要更新 `allowed_origins` 列表
3. 日誌清理工具會自動處理所有使用者輸入，無需手動呼叫（已在關鍵位置整合）

