"""
Case 2: 地點里程與地圖報表系統 - 整合啟動程式（用於打包成 exe）
整合 Flask 後端和前端服務
- 本機 / exe：可自動開瀏覽器
- Render：不開瀏覽器、用 Render 分配的 PORT、host 0.0.0.0
"""
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

from flask import Flask, send_from_directory, request
from flask_cors import CORS
from dotenv import load_dotenv
from loguru import logger

# =========================
# Path 設定：區分 exe / 開發 / Render
# =========================
IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    BASE_DIR = Path(sys._MEIPASS)
    FRONTEND_DIR = BASE_DIR
else:
    BASE_DIR = Path(__file__).parent              # .../backend
    FRONTEND_DIR = BASE_DIR.parent                # repo 根目錄（index.html 在這）

sys.path.insert(0, str(BASE_DIR))

# =========================
# .env 載入（Render 用環境變數，不一定需要 .env）
# =========================
if IS_FROZEN:
    env_path = Path(sys.executable).parent / ".env"
    template_path = BASE_DIR / "env_template.txt"
else:
    env_path = BASE_DIR / ".env"
    template_path = BASE_DIR / "env_template.txt"

if (not env_path.exists()) and template_path.exists() and IS_FROZEN:
    # 只有 exe 才自動複製 .env（Render 不做）
    import shutil
    shutil.copy(template_path, env_path)
    logger.info(f"已從 {template_path} 建立 .env 檔案")

# Render 上通常用 Dashboard 的 Environment Variables，不一定有 .env
if env_path.exists():
    load_dotenv(env_path)

# =========================
# Flask app
# =========================
app = Flask(__name__, static_folder=None, template_folder=None)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your-secret-key-here")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-here")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False

# =========================
# DB 設定
# =========================
database_uri = os.getenv("DATABASE_URI", "")
if not database_uri:
    if IS_FROZEN:
        db_path = Path(sys.executable).parent / "mileage_map.db"
    else:
        db_path = BASE_DIR / "mileage_map.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    logger.info(f"未設定 DATABASE_URI，使用 SQLite：{db_path}")
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# =========================
# Extensions
# =========================
from extensions import db, jwt
db.init_app(app)
jwt.init_app(app)

# =========================
# CORS（Render 同網域其實不需要；保留但放寬到同源/你指定網域）
# =========================
# 你如果前端和後端同網域（Render web service 直接 serve HTML），其實不用 CORS。
# 但為了你之後可能分開部署，這裡允許：
# - localhost（本機）
# - Render 網域（你可以在環境變數填 FRONTEND_ORIGIN）
port = int(os.getenv("PORT", "5001"))

allowed_origins = [
    f"http://localhost:{port}",
    f"http://127.0.0.1:{port}",
]

frontend_origin = os.getenv("FRONTEND_ORIGIN", "").strip()
if frontend_origin:
    allowed_origins.append(frontend_origin)

CORS(
    app,
    resources={r"/api/*": {"origins": allowed_origins}},
    supports_credentials=False,
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    vary_header=True,
)

# =========================
# Logging
# =========================
if IS_FROZEN:
    logs_dir = Path(sys.executable).parent / "logs"
else:
    logs_dir = BASE_DIR / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

logger.add(
    str(logs_dir / "app.log"),
    rotation="1 day",
    retention="30 days",
    level="INFO",
    encoding="utf-8",
)

# =========================
# Blueprints
# =========================
from api import auth, mileage, reports, settings
from routes import upload_bp, calculate_bp, export_bp

app.register_blueprint(auth.bp, url_prefix="/api/auth")
app.register_blueprint(mileage.bp, url_prefix="/api/mileage")
app.register_blueprint(reports.bp, url_prefix="/api/reports")
app.register_blueprint(settings.bp, url_prefix="/api/settings")
app.register_blueprint(upload_bp, url_prefix="/api/upload")
app.register_blueprint(calculate_bp, url_prefix="/api/calculate")
app.register_blueprint(export_bp, url_prefix="/api/export")

from models import User, TravelRecord, SystemSetting

# =========================
# 必要目錄
# =========================
if IS_FROZEN:
    base_data_dir = Path(sys.executable).parent
    temp_maps_dir = base_data_dir / "temp" / "maps"
    output_dir = base_data_dir / "output"
else:
    temp_maps_dir = BASE_DIR / "temp" / "maps"
    output_dir = BASE_DIR / "output"

temp_maps_dir.mkdir(parents=True, exist_ok=True)
output_dir.mkdir(parents=True, exist_ok=True)

# =========================
# Frontend routes
# =========================
@app.get("/")
def index():
    """
    Render / 開發：repo 根目錄有 index.html
    exe：你可以把 index.html 也打包進去
    """
    # 你已經把 excel-upload.html 改名 index.html 了
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.get("/template")
def download_template():
    """
    下載 Excel 範本：template.xlsx
    請把 template.xlsx 放在 repo 根目錄（跟 index.html 同層）
    """
    return send_from_directory(
        FRONTEND_DIR,
        "template.xlsx",
        as_attachment=True,
        download_name="template.xlsx"
    )

@app.get("/<path:filename>")
def serve_frontend(filename):
    """服務前端檔案（HTML/CSS/JS/圖示等）"""
    if filename.endswith(".html"):
        return send_from_directory(FRONTEND_DIR, filename)

    if filename.startswith("css/"):
        css_file = filename.replace("css/", "")
        return send_from_directory(FRONTEND_DIR / "css", css_file)

    if filename.startswith("js/"):
        js_file = filename.replace("js/", "")
        return send_from_directory(FRONTEND_DIR / "js", js_file)

    # 讓 favicon 不要一直 404
    if filename == "favicon.ico":
        # 如果你有 favicon.ico 放在根目錄就會回傳；沒有就給 204
        f = FRONTEND_DIR / "favicon.ico"
        if f.exists():
            return send_from_directory(FRONTEND_DIR, "favicon.ico")
        return ("", 204)

    return {"error": "檔案不存在"}, 404

# =========================
# Health checks
# =========================
@app.get("/health")
def health():
    return {"status": "ok"}, 200

@app.get("/api/health")
def health_detailed():
    try:
        db_status = "connected"
        try:
            db.engine.connect()
        except Exception:
            db_status = "disconnected"

        return {"status": "healthy", "database": db_status}
    except Exception:
        return {"status": "healthy", "database": "unknown"}

@app.get("/temp/maps/<path:filename>")
def serve_map_image(filename):
    if (temp_maps_dir / filename).exists():
        return send_from_directory(str(temp_maps_dir), filename)
    return {"error": "檔案不存在"}, 404

# =========================
# exe 才開瀏覽器，Render 不開
# =========================
def open_browser():
    time.sleep(1.5)
    port = int(os.getenv("PORT", "5001"))
    url = f"http://localhost:{port}/"
    webbrowser.open(url)
    logger.info(f"已自動打開瀏覽器: {url}")

# =========================
# Entry
# =========================
if __name__ == "__main__":
    try:
        with app.app_context():
            db.create_all()
            logger.info("資料表初始化完成")
    except Exception as e:
        logger.warning(f"資料表初始化失敗: {str(e)}")

    # exe 才開瀏覽器
    if IS_FROZEN:
        t = threading.Thread(target=open_browser, daemon=True)
        t.start()

    # Render：PORT 由環境給、host 必須 0.0.0.0
    port = int(os.getenv("PORT", "5001"))

    # Render 會設 RENDER 或 PORT（至少有 PORT），我們用這個判斷是不是雲端
    IS_CLOUD = bool(os.getenv("RENDER")) or (not IS_FROZEN and os.getenv("PORT") is not None)

    host = "0.0.0.0" if IS_CLOUD else os.getenv("HOST", "127.0.0.1")
    debug = os.getenv("DEBUG", "False").lower() == "true"

    logger.info(f"啟動服務在 http://{host}:{port}")
    logger.info(f"前端頁面: http://{host}:{port}/")

    app.run(host=host, port=port, debug=debug, use_reloader=False)
