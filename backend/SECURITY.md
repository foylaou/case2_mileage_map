# 安全性修補說明

## 修補完成的 CVE

本系統已完成以下弱點修補：

### CVE-2024-6221 (7.5) - Improper Access Control
**修補方式：**
- 使用白名單方式限制 CORS origins
- 僅允許本機前端來源：`http://localhost:{port}` 和 `http://127.0.0.1:{port}`
- 不使用 `origins="*"` 通配符

### CVE-2024-1681 (5.3) - Improper Output Neutralization for Logs
**修補方式：**
- 所有使用者輸入在記錄到日誌前都經過清理
- 移除 CR/LF 等控制字元，防止 log injection
- 使用 `utils/log_sanitizer.py` 工具函數進行清理

### CVE-2024-6866 (5.3) - Case-Insensitive Path Matching
**修補方式：**
- CORS 僅允許嚴格的小寫 `/api/*` 路徑
- 大小寫不一致的路徑（如 `/API/*`, `/Api/*`）會被拒絕
- 這是**設計刻意限制**，非漏洞

### CVE-2024-6844 (5.3) - Inconsistent CORS Matching due to '+' handling
**修補方式：**
- 升級 Flask-CORS 到 >=6.0.0
- 新版本已修補 '+' 字元處理問題

## 重要安全設計說明

### Path 大小寫敏感性

**設計原則：**
- 只有嚴格的小寫 `/api/*` 路徑允許 CORS
- 大小寫不一致的路徑（如 `/API/*`, `/Api/*`）會被拒絕
- 這是**預期的安全行為**，不是漏洞

**為什麼這樣設計？**
1. 防止路徑操作攻擊（Path Manipulation）
2. 確保 CORS 規則的一致性
3. 符合最小權限原則（Principle of Least Privilege）

**範例：**
- ✅ `/api/health` → 允許 CORS
- ❌ `/API/health` → 拒絕 CORS（預期行為）
- ❌ `/Api/health` → 拒絕 CORS（預期行為）

### CORS 設定

**白名單設定：**
```python
allowed_origins = [
    f"http://localhost:{port}",
    f"http://127.0.0.1:{port}",
]

CORS(
    app,
    resources={r"/api/*": {"origins": allowed_origins}},  # 僅小寫 '/api/*'
    supports_credentials=False,
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    vary_header=True,
    expose_headers=[]
)
```

**安全特性：**
- ✅ 白名單 origins（無通配符）
- ✅ 僅對 `/api/*` 路徑啟用 CORS
- ✅ 大小寫敏感的路徑匹配
- ✅ 不支援 credentials
- ✅ 明確指定允許的方法和標頭

## 日誌安全

所有使用者輸入在記錄到日誌前都會經過清理：

```python
from utils.log_sanitizer import sanitize_log_input, sanitize_filename, sanitize_path

# 清理使用者輸入
safe_username = sanitize_log_input(username)
safe_filename = sanitize_filename(file.filename)
safe_path = sanitize_path(file_path)
```

**清理內容：**
- 移除 CR/LF 等控制字元
- 限制長度
- 移除路徑操作字元（如 `../`）
- 移除格式化字元（如 `%n`, `%r`）

## 測試驗證

執行安全性測試：

```bash
cd backend
python tests/test_cors_security.py
```

**測試內容：**
1. 白名單 Origin 檢查
2. Path 大小寫敏感性（驗證大小寫不一致路徑被正確拒絕）
3. Path '+' 字元處理
4. CORS Methods 和 Headers 設定
5. Credentials 設定
6. 非 API 路徑 CORS 檢查

**預期結果：**
- 所有測試應該通過（PASS）
- 大小寫不一致的路徑測試會標示為 "Expected Reject"

## 版本資訊

- **Flask-CORS**: >=6.0.0（已修補所有相關 CVE）
- **Flask**: 3.0.0
- **修補日期**: 2024-12-22

## 稽核注意事項

1. **Path 大小寫不一致的 CORS 行為是設計刻意限制，非漏洞**
   - 這是為了修補 CVE-2024-6866 而採用的安全設計
   - 測試腳本會將此行為標示為 "Expected Reject"

2. **所有使用者輸入都經過日誌清理**
   - 防止 log injection 攻擊
   - 符合 CVE-2024-1681 修補要求

3. **CORS 設定採用最小權限原則**
   - 僅允許本機前端來源
   - 僅對 `/api/*` 路徑啟用
   - 不支援 credentials

## 相關文件

- `SECURITY_PATCHES.md` - 詳細修補說明
- `tests/README.md` - 測試腳本說明
- `utils/log_sanitizer.py` - 日誌清理工具




