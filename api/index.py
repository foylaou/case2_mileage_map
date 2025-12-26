"""
Vercel Serverless Function 入口
將 Flask 應用程式包裝為 Vercel serverless function
"""
import sys
import os
from pathlib import Path

# 添加 backend 目錄到 Python 路徑
backend_dir = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_dir))

# 設定環境變數（Vercel 會自動提供）
# 確保在 Vercel 環境中使用正確的設定
os.environ.setdefault('DEBUG', 'False')
os.environ.setdefault('HOST', '0.0.0.0')

# 獲取 Vercel 部署的域名（從環境變數）
def get_allowed_origins():
    """動態獲取允許的來源"""
    origins = []
    
    # 從環境變數獲取（Vercel 會設定 VERCEL_URL）
    vercel_url = os.getenv('VERCEL_URL')
    if vercel_url:
        # 確保使用 https
        if not vercel_url.startswith('http'):
            vercel_url = f'https://{vercel_url}'
        origins.append(vercel_url)
    
    # 從環境變數獲取自訂域名
    custom_domain = os.getenv('CUSTOM_DOMAIN')
    if custom_domain:
        origins.append(f'https://{custom_domain}')
    
    # 開發環境支援
    if os.getenv('VERCEL_ENV') != 'production':
        origins.extend([
            'http://localhost:5001',
            'http://127.0.0.1:5001',
        ])
    
    # 如果沒有設定任何來源，使用預設值（允許所有來源，僅用於開發）
    if not origins:
        origins = ['*']
    
    return origins

# 設定 CORS 允許的來源（在導入 app 之前設定）
allowed_origins_env = get_allowed_origins()
os.environ['ALLOWED_ORIGINS'] = ','.join(allowed_origins_env)

# 導入 Flask 應用程式
from app import app

# 調整 CORS 設定以支援 Vercel 域名
from flask_cors import CORS

# 重新設定 CORS（覆蓋 app.py 中的設定）
CORS(
    app,
    resources={r"/api/*": {"origins": allowed_origins_env}},
    supports_credentials=False,
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    vary_header=True,
    expose_headers=[]
)

# Vercel serverless function handler
# Vercel 的 Python runtime 會自動尋找名為 'app' 的變數
# 並將其作為 WSGI 應用程式使用

# 初始化資料表（在應用程式啟動時執行一次）
try:
    with app.app_context():
        from extensions import db
        db.create_all()
except Exception:
    pass  # 如果資料庫未連線，跳過

# Vercel 會自動使用 app 物件作為 WSGI 應用程式
# 不需要定義 handler 函數，Vercel 會自動處理
__all__ = ['app']

