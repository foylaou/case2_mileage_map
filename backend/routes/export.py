"""
匯出功能路由
"""
from flask import Blueprint, request, jsonify, send_file
from services.excel_service import ExcelService
from services.word_service import WordService
from services.google_maps_template_service import generate_google_maps_style_html
from loguru import logger
import os

bp = Blueprint('export', __name__)
excel_service = ExcelService()
word_service = WordService()


@bp.route('/excel', methods=['POST'])
def export_excel():
    """
    匯出更新後的 Excel 檔案
    
    請求:
        {
            "file_path": "原始檔案路徑",
            "records": 包含計算結果的紀錄列表
        }
    
    回應:
        Excel 檔案下載
    """
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        records = data.get('records', [])
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({
                'status': 'error',
                'message': '原始檔案不存在'
            }), 400
        
        if not records:
            return jsonify({
                'status': 'error',
                'message': '沒有資料可匯出'
            }), 400
        
        # 更新 Excel 檔案
        output_path = excel_service.add_calculation_results(file_path, records)
        
        # 回傳檔案
        return send_file(
            output_path,
            as_attachment=True,
            download_name=os.path.basename(output_path),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"匯出 Excel 錯誤: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'匯出失敗: {str(e)}'
        }), 500


@bp.route('/word', methods=['POST'])
def export_word():
    """
    匯出 Word 報表（依計畫別）
    
    請求:
        {
            "project_name": "計畫別名稱",
            "records": 該計畫別的紀錄列表（含計算結果）,
            "fixed_origin": "固定起點地址（可選）"
        }
    
    回應:
        Word 檔案下載
    """
    try:
        data = request.get_json()
        project_name = data.get('project_name', '未分類')
        records = data.get('records', [])
        fixed_origin = data.get('fixed_origin', '')
        
        if not records:
            return jsonify({
                'status': 'error',
                'message': '沒有資料可匯出'
            }), 400
        
        # 產生 Word 報表
        word_path = word_service.generate_report(project_name, records, fixed_origin)
        
        # 回傳檔案
        return send_file(
            word_path,
            as_attachment=True,
            download_name=os.path.basename(word_path),
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        logger.error(f"匯出 Word 錯誤: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'匯出失敗: {str(e)}'
        }), 500


@bp.route('/word/batch', methods=['POST'])
def export_word_batch():
    """
    批次匯出多個計畫別的 Word 報表
    
    請求:
        {
            "projects": {
                "計畫別名稱1": [records...],
                "計畫別名稱2": [records...],
                ...
            },
            "fixed_origin": "固定起點地址（可選）"
        }
    
    回應:
        ZIP 壓縮檔（包含所有 Word 檔案）
    """
    try:
        data = request.get_json()
        projects = data.get('projects', {})
        fixed_origin = data.get('fixed_origin', '')
        
        if not projects:
            return jsonify({
                'status': 'error',
                'message': '沒有資料可匯出'
            }), 400
        
        # 產生所有 Word 報表
        word_files = []
        for project_name, records in projects.items():
            try:
                word_path = word_service.generate_report(project_name, records, fixed_origin)
                word_files.append({
                    'path': word_path,
                    'name': os.path.basename(word_path)
                })
            except Exception as e:
                logger.error(f"產生 {project_name} 報表錯誤: {str(e)}")
                continue
        
        if not word_files:
            return jsonify({
                'status': 'error',
                'message': '無法產生任何報表'
            }), 500
        
        # 建立 ZIP 壓縮檔
        import zipfile
        from datetime import datetime
        
        zip_dir = 'output'
        os.makedirs(zip_dir, exist_ok=True)
        
        zip_filename = f"里程報表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        zip_path = os.path.join(zip_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for word_file in word_files:
                zipf.write(word_file['path'], word_file['name'])
        
        logger.info(f"成功產生 ZIP 壓縮檔: {zip_path}, 包含 {len(word_files)} 個 Word 檔案")
        
        # 回傳 ZIP 檔案
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )
        
    except Exception as e:
        logger.error(f"批次匯出 Word 錯誤: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'匯出失敗: {str(e)}'
        }), 500


@bp.route('/html', methods=['POST'])
def export_html():
    """
    匯出 Google Maps 風格的 HTML 檔案（單筆記錄）
    
    請求:
        {
            "record": 單筆記錄（含計算結果）,
            "fixed_origin": "固定起點地址（可選）"
        }
    
    回應:
        HTML 檔案下載
    """
    try:
        data = request.get_json()
        record = data.get('record')
        fixed_origin = data.get('fixed_origin', '')
        
        if not record:
            return jsonify({
                'status': 'error',
                'message': '沒有資料可匯出'
            }), 400
        
        # 產生 Google Maps 風格 HTML
        html_path = generate_google_maps_style_html(
            record=record,
            output_path=None,  # 自動生成檔名
            fixed_origin=fixed_origin
        )
        
        # 回傳檔案
        return send_file(
            html_path,
            as_attachment=True,
            download_name=os.path.basename(html_path),
            mimetype='text/html'
        )
        
    except Exception as e:
        logger.error(f"匯出 HTML 錯誤: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'匯出失敗: {str(e)}'
        }), 500

