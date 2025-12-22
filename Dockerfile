# 1. 基底映像檔
FROM python:3.11-slim

# 2. 安裝系統依賴
# 安裝 Playwright 需要的瀏覽器依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxkbcommon0 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# 3. 設定工作目錄
WORKDIR /app

# 4. 複製整個專案內容到容器中
COPY . .

# 5. 安裝 Python 依賴
RUN pip install --no-cache-dir -r backend/requirements.txt

# 6. 安裝 Playwright 瀏覽器
RUN playwright install --with-deps

# 7. 設定環境變數
# 讓 Flask 監聽所有網路介面
ENV HOST=0.0.0.0
# Flask 運行的端口
ENV PORT=5001
# 設定為生產模式
ENV FLASK_ENV=production
# 讓 Python 不要緩衝 stdout 和 stderr
ENV PYTHONUNBUFFERED=1


# 8. 開放端口
EXPOSE 5001

# 9. 啟動命令
CMD ["python", "backend/main.py"]
