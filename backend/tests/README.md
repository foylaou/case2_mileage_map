# 測試腳本說明

## 安全性測試

### test_cors_security.py

CORS 安全檢查腳本，用於驗證以下 CVE 的修補：

- **CVE-2024-6221** (7.5) - Improper Access Control
- **CVE-2024-1681** (5.3) - Improper Output Neutralization for Logs
- **CVE-2024-6866** (5.3) - Case-Insensitive Path Matching
- **CVE-2024-6844** (5.3) - Inconsistent CORS Matching due to '+' handling

#### 執行方式

**方式一：直接執行**
```bash
cd backend
python tests/test_cors_security.py
```

**方式二：使用 pytest（如果已安裝）**
```bash
cd backend
python -m pytest tests/test_cors_security.py -v
```

#### 測試前準備

1. 確保 Flask 應用程式正在運行：
   ```bash
   cd backend
   python main.py
   ```

2. 在另一個終端執行測試腳本

#### 測試內容

1. **白名單 Origin 檢查** - 驗證只有允許的 origin 才能取得 CORS 標頭
2. **Path 大小寫敏感性** - 驗證大小寫不一致路徑被正確拒絕（預期行為）
3. **Path '+' 字元處理** - 驗證 '+' 字元不會造成 CORS 規則誤配
4. **CORS Methods 和 Headers** - 驗證允許的方法和標頭設定正確
5. **Credentials 設定** - 驗證 supports_credentials=False
6. **非 API 路徑** - 驗證非 API 路徑不允許 CORS

#### 預期結果

所有測試應該通過（PASS），表示 CORS 安全設定正確。

**重要說明：**
- Path 大小寫不一致的路徑（如 `/API/*`, `/Api/*`）被拒絕是**預期的安全行為**
- 這是為了修補 CVE-2024-6866 而採用的設計，不是漏洞
- 測試腳本會將此行為標示為 "Expected Reject"

## 功能測試

### test_mileage.py

里程計算功能測試（現有測試）

