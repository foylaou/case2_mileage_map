# -*- mode: python ; coding: utf-8 -*-
"""
Case 2: 地點里程與地圖報表系統 - PyInstaller 打包配置
"""

import os
from pathlib import Path

# 專案根目錄
BASE_DIR = Path(SPECPATH)
BACKEND_DIR = BASE_DIR
FRONTEND_DIR = BASE_DIR.parent

# 收集前端檔案
frontend_files = []
excel_html = FRONTEND_DIR / 'excel-upload.html'
if excel_html.exists():
    frontend_files.append((str(excel_html), '.'))

# 收集 CSS 檔案
css_files = []
css_dir = FRONTEND_DIR / 'css'
if css_dir.exists():
    for css_file in css_dir.glob('*.css'):
        css_files.append((str(css_file), 'css'))

# 收集 JS 檔案
js_files = []
js_dir = FRONTEND_DIR / 'js'
if js_dir.exists():
    for js_file in js_dir.glob('*.js'):
        js_files.append((str(js_file), 'js'))

# 收集環境變數模板
datas = frontend_files + css_files + js_files
if (BACKEND_DIR / 'env_template.txt').exists():
    datas.append((str(BACKEND_DIR / 'env_template.txt'), '.'))

a = Analysis(
    [str(BACKEND_DIR / 'main.py')],
    pathex=[str(BACKEND_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'flask',
        'flask_cors',
        'flask_jwt_extended',
        'flask_sqlalchemy',
        'sqlalchemy',
        'pymysql',
        'dotenv',
        'loguru',
        'googlemaps',
        'requests',
        'openpyxl',
        'pandas',
        'reportlab',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'docx',
        'asyncio',
        'concurrent.futures',
        'api.auth',
        'api.mileage',
        'api.reports',
        'api.settings',
        'routes.upload',
        'routes.calculate',
        'routes.export',
        'services.excel_service',
        'services.google_maps_service',
        'services.gmap_screenshot_service',
        'services.map_overlay_service',
        'services.google_maps_template_service',
        'services.place_mapping',
        'services.word_service',
        'models.user',
        'models.travel_record',
        'models.setting',
        'utils.report_generator',
        'utils.log_sanitizer',
        'extensions',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pathlib'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Case2_里程地圖系統',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # 關閉 UPX 壓縮以避免問題
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 顯示控制台視窗（用於查看日誌）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以指定 .ico 檔案路徑
)

