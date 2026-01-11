# 字體檔案說明

此目錄用於存放專案所需的中文字體檔案。

## 必需字體檔案

請將以下字體檔案放入此目錄：

- `NotoSansTC-Regular.ttf` - Noto Sans 繁體中文正體字型

## 下載方式

### 方式一：從 Google Fonts 下載

1. 前往 [Google Fonts - Noto Sans TC](https://fonts.google.com/noto/specimen/Noto+Sans+TC)
2. 點擊「Download family」
3. 解壓縮後找到 `NotoSansTC-Regular.ttf`
4. 將檔案複製到此目錄

### 方式二：使用 wget（Linux/Mac）

```bash
cd backend/assets/fonts
wget https://github.com/google/fonts/raw/main/ofl/notosanstc/NotoSansTC-Regular.ttf
```

### 方式三：使用 curl（Windows PowerShell）

```powershell
cd backend\assets\fonts
curl -L -o NotoSansTC-Regular.ttf https://github.com/google/fonts/raw/main/ofl/notosanstc/NotoSansTC-Regular.ttf
```

## 注意事項

- 字體檔案會納入 Git 版本控制
- 如果字體檔案不存在，系統會自動使用系統字體（Windows 使用微軟正黑體，Linux 使用 Noto CJK）
- 專案字體優先於系統字體載入

