#!/bin/bash
# Linux/Mac 前端啟動腳本

echo "啟動前端服務..."
echo ""
echo "前端服務將運行在 http://localhost:8000"
echo "請在瀏覽器開啟: http://localhost:8000/excel-upload.html"
echo "按 Ctrl+C 停止服務"
echo ""
python3 -m http.server 8000








