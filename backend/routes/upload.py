"""
Excel 上傳路由
"""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.excel_service import ExcelService
from services.place_mapping import PlaceMappingService
from loguru import logger
from utils.log_sanitizer import sanitize_filename, sanitize_path
from utils.path_manager import get_temp_dir, get_relative_path
from pathlib import Path
import os

bp = Blueprint('upload', __name__)
excel_service = ExcelService()
place_mapping = PlaceMappingService()


def check_auth():
    """檢查認證（可選）"""
    try:
        # 嘗試取得 JWT identity，如果沒有 token 也不會報錯
        identity = get_jwt_identity()
        return identity is not None
    except:
        return False


@bp.route('/excel', methods=['POST'])
def upload_excel():
    """
    上傳 Excel 檔案並解析
    
    請求:
        - file: Excel 檔案
        - fixed_origin: 固定起點地址（可選）
    
    回應:
        - 解析後的資料（依計畫別分組）
    """
    try:
        logger.info("收到 Excel 上傳請求")
        
        if 'file' not in request.files:
            logger.warning("上傳請求中沒有檔案")
            return jsonify({
                'status': 'error',
                'message': '沒有選擇檔案'
            }), 400
        
        file = request.files['file']
        fixed_origin = request.form.get('fixed_origin', '')
        
        if not file.filename:
            logger.warning("檔案名稱為空")
            return jsonify({
                'status': 'error',
                'message': '沒有選擇檔案'
            }), 400
        
        # 清理檔案名稱以防止日誌注入（CVE-2024-1681）
        safe_filename = sanitize_filename(file.filename)
        logger.info(f"開始處理檔案: {safe_filename}, 大小: {file.content_length} bytes")
        
        # 檢查檔案格式
        if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
            logger.warning(f"不支援的檔案格式: {safe_filename}")
            return jsonify({
                'status': 'error',
                'message': '只支援 Excel 檔案格式 (.xlsx, .xls)'
            }), 400
        
        # 儲存暫存檔案（使用相對路徑）
        logger.info("儲存暫存檔案...")
        temp_dir = get_temp_dir()
        
        temp_path = temp_dir / file.filename
        file.save(str(temp_path))
        # 清理路徑以防止日誌注入（CVE-2024-1681）
        safe_path = sanitize_path(get_relative_path(temp_path))
        logger.info(f"檔案已儲存至: {safe_path}")
        
        # 解析 Excel
        logger.info("開始解析 Excel 檔案...")
        parse_result = excel_service.parse_excel(str(temp_path))
        logger.info(f"Excel 解析完成，結果: {parse_result.get('success', False)}")
        
        if not parse_result['success']:
            # 刪除暫存檔案
            if temp_path.exists():
                temp_path.unlink()
            return jsonify({
                'status': 'error',
                'message': parse_result['error']
            }), 400
        
        records = parse_result['data']
        
        # 依計畫別分組
        logger.info(f"開始分組，共 {len(records)} 筆資料")
        grouped_records = excel_service.group_by_project(records)
        logger.info(f"分組完成，共 {len(grouped_records)} 個計畫別")
        
        # 儲存檔案路徑到 session（用於後續處理）
        # 這裡我們將檔案路徑存在 records 的 metadata 中
        result = {
            'status': 'success',
            'message': f'成功解析 {parse_result["total_count"]} 筆資料',
            'data': {
                'file_path': str(temp_path),
                'total_count': parse_result['total_count'],
                'projects': {}
            }
        }
        
        # 轉換分組資料格式
        logger.info("轉換分組資料格式...")
        for project_name, project_records in grouped_records.items():
            result['data']['projects'][project_name] = {
                'name': project_name,
                'count': len(project_records),
                'records': project_records
            }
        
        # 清理檔案名稱以防止日誌注入（CVE-2024-1681）
        logger.info(f"成功上傳並解析 Excel: {safe_filename}, {len(grouped_records)} 個計畫別, 共 {parse_result['total_count']} 筆資料")
        logger.info("準備返回結果...")
        
        return jsonify(result), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"上傳 Excel 錯誤: {str(e)}")
        logger.error(f"錯誤詳情:\n{error_trace}")
        return jsonify({
            'status': 'error',
            'message': f'上傳失敗: {str(e)}'
        }), 500


@bp.route('/preview', methods=['POST'])
@jwt_required()
def preview_data():
    """
    預覽解析後的資料（用於前端顯示）
    """
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({
                'status': 'error',
                'message': '檔案不存在'
            }), 400
        
        # 重新解析（如果需要）
        parse_result = excel_service.parse_excel(file_path)
        
        if not parse_result['success']:
            return jsonify({
                'status': 'error',
                'message': parse_result['error']
            }), 400
        
        # 依計畫別分組
        grouped_records = excel_service.group_by_project(parse_result['data'])
        
        return jsonify({
            'status': 'success',
            'data': {
                'projects': grouped_records,
                'total_count': parse_result['total_count']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"預覽資料錯誤: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'預覽失敗: {str(e)}'
        }), 500

