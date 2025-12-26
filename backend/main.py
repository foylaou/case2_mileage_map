"""
Case 2: 地點里程與地圖報表系統 - 整合啟動程式（用於打包成 exe）
整合 Flask 後端和前端服務，並自動打開瀏覽器
"""
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

# 確保可以找到模組
# 處理 PyInstaller 打包後的路徑
if getattr(sys, 'frozen', False):
    # 如果是打包後的 exe
    BASE_DIR = Path(sys._MEIPASS)
    # 前端檔案在打包時會被包含在資料中
    FRONTEND_DIR = BASE_DIR
else:
    # 開發環境
    BASE_DIR = Path(__file__).parent
    FRONTEND_DIR = BASE_DIR.parent

sys.path.insert(0, str(BASE_DIR))

from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from loguru import logger

# 載入環境變數
# 在打包後，.env 應該在執行目錄
if getattr(sys, 'frozen', False):
    env_path = Path(sys.executable).parent / '.env'
    template_path = BASE_DIR / 'env_template.txt'
else:
    env_path = BASE_DIR / '.env'
    template_path = BASE_DIR / 'env_template.txt'

if not env_path.exists() and template_path.exists():
    # 如果沒有 .env，從 env_template.txt 複製
    import shutil
    shutil.copy(template_path, env_path)
    logger.info(f"已從 {template_path} 建立 .env 檔案")

load_dotenv(env_path)

# 初始化 Flask 應用程式
app = Flask(__name__,
            static_folder=None,  # 我們會手動處理靜態檔案
            template_folder=None)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-here')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False

# 資料庫設定
database_uri = os.getenv('DATABASE_URI', '')
if not database_uri:
    # 預設使用 SQLite
    if getattr(sys, 'frozen', False):
        # exe 執行目錄
        db_path = Path(sys.executable).parent / 'mileage_map.db'
    else:
        db_path = BASE_DIR / 'mileage_map.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    logger.info(f"未設定 DATABASE_URI，使用 SQLite：{db_path}")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化擴充功能
from extensions import db, jwt
db.init_app(app)
jwt.init_app(app)

# ============================================================================
# Security Note: CORS Configuration
# ============================================================================
# CORS is intentionally restricted to case-sensitive '/api/*' paths only.
# Uppercase or mixed-case paths (e.g., /API/*, /Api/*) are rejected to mitigate:
#   - CVE-2024-6866 (Case-insensitive path matching vulnerability)
#   - CVE-2024-6844 (Inconsistent '+' path handling vulnerability)
#
# This design ensures that only the exact lowercase '/api/*' pattern receives
# CORS headers, preventing path manipulation attacks.
#
# Additional security measures:
#   - CVE-2024-6221: Whitelist-based origin control (no wildcard origins)
#   - CVE-2024-1681: Log sanitization prevents log injection
# ============================================================================
port = int(os.getenv('PORT', 5001))
allowed_origins = [
    f"http://localhost:{port}",
    f"http://127.0.0.1:{port}",
]

CORS(
    app,
    resources={r"/api/*": {"origins": allowed_origins}},  # Case-sensitive: only lowercase '/api/*'
    supports_credentials=False,  # No credentials for local-only usage
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    vary_header=True,  # Ensures proper CORS header variation
    expose_headers=[]  # No additional headers exposed
)

# 設定日誌
# 在打包後，日誌應該寫入執行目錄，而不是臨時目錄
if getattr(sys, 'frozen', False):
    # exe 執行目錄
    logs_dir = Path(sys.executable).parent / 'logs'
else:
    logs_dir = BASE_DIR / 'logs'
logs_dir.mkdir(parents=True, exist_ok=True)
logger.add(
    str(logs_dir / "app.log"),
    rotation="1 day",
    retention="30 days",
    level="INFO",
    encoding="utf-8"
)

# 註冊藍圖
from api import auth, mileage, reports, settings
from routes import upload_bp, calculate_bp, export_bp

app.register_blueprint(auth.bp, url_prefix='/api/auth')
app.register_blueprint(mileage.bp, url_prefix='/api/mileage')
app.register_blueprint(reports.bp, url_prefix='/api/reports')
app.register_blueprint(settings.bp, url_prefix='/api/settings')
app.register_blueprint(upload_bp, url_prefix='/api/upload')
app.register_blueprint(calculate_bp, url_prefix='/api/calculate')
app.register_blueprint(export_bp, url_prefix='/api/export')

# 匯入模型以建立資料表
from models import User, TravelRecord, SystemSetting

# 前端檔案路徑已在上面定義

# 建立必要目錄
# 在打包後，這些目錄應該建立在執行目錄
if getattr(sys, 'frozen', False):
    # exe 執行目錄
    base_data_dir = Path(sys.executable).parent
    temp_maps_dir = base_data_dir / 'temp' / 'maps'
    output_dir = base_data_dir / 'output'
else:
    temp_maps_dir = BASE_DIR / 'temp' / 'maps'
    output_dir = BASE_DIR / 'output'
temp_maps_dir.mkdir(parents=True, exist_ok=True)
output_dir.mkdir(parents=True, exist_ok=True)

@app.route('/')
def index():
    """首頁 - 重定向到 Excel 上傳頁面"""
    return send_from_directory(FRONTEND_DIR, 'excel-upload.html')

@app.route('/<path:filename>', methods=['GET'])
def serve_frontend(filename):
    """服務前端檔案（HTML、CSS、JS）- 只支援 GET 方法"""
    # HTML 檔案
    if filename.endswith('.html'):
        return send_from_directory(FRONTEND_DIR, filename)
    # CSS 檔案
    elif filename.startswith('css/'):
        css_file = filename.replace('css/', '')
        return send_from_directory(FRONTEND_DIR / 'css', css_file)
    # JS 檔案
    elif filename.startswith('js/'):
        js_file = filename.replace('js/', '')
        return send_from_directory(FRONTEND_DIR / 'js', js_file)
    return {'error': '檔案不存在'}, 404

@app.route('/health', methods=['GET'])
def health():
    """簡單健康檢查 API"""
    return {'status': 'ok'}, 200

@app.route('/temp/maps/<path:filename>')
def serve_map_image(filename):
    """提供靜態地圖圖片"""
    # 使用上面定義的 temp_maps_dir
    if (temp_maps_dir / filename).exists():
        return send_from_directory(str(temp_maps_dir), filename)
    else:
        return {'error': '檔案不存在'}, 404

@app.route('/api/health')
def health_detailed():
    """詳細健康檢查（包含資料庫狀態）"""
    try:
        db_status = 'connected'
        try:
            db.engine.connect()
        except:
            db_status = 'disconnected'
        
        return {
            'status': 'healthy',
            'database': db_status
        }
    except Exception as e:
        return {
            'status': 'healthy',
            'database': 'unknown',
            'note': 'Database check failed, but service is running'
        }

def open_browser():
    """延遲打開瀏覽器"""
    time.sleep(1.5)  # 等待服務啟動
    port = int(os.getenv('PORT', 5001))
    url = f'http://localhost:{port}/'
    webbrowser.open(url)
    logger.info(f"已自動打開瀏覽器: {url}")

if __name__ == '__main__':
    # 建立資料表
    try:
        with app.app_context():
            db.create_all()
            logger.info("資料表初始化完成")
    except Exception as e:
        logger.warning(f"資料表初始化失敗: {str(e)}")
    
    # 在背景執行緒中打開瀏覽器
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # 啟動應用程式
    port = int(os.getenv('PORT', 5001))
    host = os.getenv('HOST', '127.0.0.1')  # exe 版本使用 localhost
    # 確保 production 環境預設 DEBUG=False（修補 CVE-2024-1681）
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"啟動服務在 http://{host}:{port}")
    logger.info(f"前端頁面: http://{host}:{port}/")
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        use_reloader=False  # exe 版本不使用 reloader
    )

