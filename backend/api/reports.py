"""
報表 API
"""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required
from models.travel_record import TravelRecord
from utils.report_generator import ExcelReportGenerator, PDFReportGenerator
from extensions import db
from datetime import datetime
from loguru import logger
import tempfile

bp = Blueprint('reports', __name__)

@bp.route('/mileage/generate', methods=['POST'])
@jwt_required()
def generate_mileage_report():
    """產生里程報表"""
    try:
        data = request.get_json()
        report_type = data.get('report_type', 'detail')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        format_type = data.get('format', 'excel')
        include_map = data.get('include_map', True)
        include_route = data.get('include_route', True)
        include_distance = data.get('include_distance', True)
        
        # 建立查詢
        query = TravelRecord.query.filter_by(status='active')
        
        if start_date:
            query = query.filter(TravelRecord.travel_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(TravelRecord.travel_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        records = query.order_by(TravelRecord.travel_date.desc()).all()
        record_data = [record.to_dict() for record in records]
        
        # 產生報表
        if format_type == 'excel':
            generator = ExcelReportGenerator()
            generator.generate_mileage_report(record_data, report_type, include_map, include_route, include_distance)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
            generator.save(temp_file.name)
            temp_file.close()
            
            return send_file(
                temp_file.name,
                as_attachment=True,
                download_name=f'里程報表_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
        elif format_type == 'pdf':
            generator = PDFReportGenerator()
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            generator.generate_mileage_report(record_data, report_type, temp_file.name, include_map, include_route, include_distance)
            temp_file.close()
            
            return send_file(
                temp_file.name,
                as_attachment=True,
                download_name=f'里程報表_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
                mimetype='application/pdf'
            )
        
        return jsonify({'status': 'error', 'message': '不支援的報表格式'}), 400
        
    except Exception as e:
        logger.error(f"產生報表錯誤: {str(e)}")
        return jsonify({'status': 'error', 'message': '產生報表失敗'}), 500



