"""
里程計算 API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.travel_record import TravelRecord
from services.google_maps_service import GoogleMapsService
from extensions import db
from datetime import datetime
from loguru import logger
import pandas as pd
import os

bp = Blueprint('mileage', __name__)
map_service = GoogleMapsService()

@bp.route('/calculate', methods=['POST'])
@jwt_required()
def calculate_distance():
    """計算里程"""
    try:
        data = request.get_json()
        start_location = data.get('start_location')
        end_location = data.get('end_location')
        route_type = data.get('route_type', 'driving')
        
        if not start_location or not end_location:
            return jsonify({'status': 'error', 'message': '請輸入起點和終點'}), 400
        
        # 計算距離
        result = map_service.calculate_distance(start_location, end_location, route_type)
        
        if not result or not result.get('success'):
            error_msg = result.get('error', '無法計算距離，請檢查地點是否正確') if result else '無法計算距離，請檢查地點是否正確'
            return jsonify({'status': 'error', 'message': error_msg}), 400
        
        # 轉換為統一格式
        return jsonify({
            'status': 'success',
            'data': {
                'one_way_distance': result.get('one_way_km', 0),
                'round_trip_distance': result.get('round_trip_km', 0),
                'estimated_time': result.get('estimated_time', ''),
                'navigation_url': result.get('navigation_url', '')
            }
        }), 200
        
    except Exception as e:
        logger.error(f"計算里程錯誤: {str(e)}")
        return jsonify({'status': 'error', 'message': '計算里程失敗'}), 500

@bp.route('/records', methods=['GET', 'POST'])
@jwt_required()
def travel_records():
    """出差紀錄管理"""
    try:
        if request.method == 'GET':
            # 取得出差紀錄列表
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            query = TravelRecord.query.filter_by(status='active')
            
            if start_date:
                query = query.filter(TravelRecord.travel_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
            if end_date:
                query = query.filter(TravelRecord.travel_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
            
            records = query.order_by(TravelRecord.travel_date.desc()).all()
            
            return jsonify({
                'status': 'success',
                'data': [record.to_dict() for record in records]
            }), 200
        
        elif request.method == 'POST':
            # 新增出差紀錄
            data = request.get_json()
            
            record = TravelRecord(
                travel_date=datetime.strptime(data.get('travel_date'), '%Y-%m-%d').date(),
                start_location=data.get('start_location'),
                end_location=data.get('end_location'),
                one_way_distance=data.get('one_way_distance'),
                round_trip_distance=data.get('round_trip_distance'),
                estimated_time=data.get('estimated_time'),
                route_type=data.get('route_type', 'driving'),
                route_description=data.get('route_description')
            )
            
            db.session.add(record)
            db.session.commit()
            
            logger.info(f"新增出差紀錄成功: {record.id}")
            
            return jsonify({
                'status': 'success',
                'message': '出差紀錄新增成功',
                'data': record.to_dict()
            }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"出差紀錄管理錯誤: {str(e)}")
        return jsonify({'status': 'error', 'message': '操作失敗'}), 500

@bp.route('/import', methods=['POST'])
@jwt_required()
def import_travel_records():
    """匯入出差紀錄"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': '沒有選擇檔案'}), 400
        
        file = request.files['file']
        filename = file.filename
        
        if not filename:
            return jsonify({'status': 'error', 'message': '沒有選擇檔案'}), 400
        
        # 儲存暫存檔案
        temp_path = f"temp/{filename}"
        os.makedirs('temp', exist_ok=True)
        file.save(temp_path)
        
        # 讀取 Excel 或 CSV
        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(temp_path)
        elif filename.endswith('.csv'):
            df = pd.read_csv(temp_path, encoding='utf-8')
        else:
            return jsonify({'status': 'error', 'message': '不支援的檔案格式'}), 400
        
        # 解析資料並匯入
        imported_count = 0
        for _, row in df.iterrows():
            try:
                record = TravelRecord(
                    travel_date=pd.to_datetime(row.get('日期', row.get('travel_date'))).date(),
                    start_location=str(row.get('起點', row.get('start_location', ''))),
                    end_location=str(row.get('終點', row.get('end_location', ''))),
                    one_way_distance=float(row.get('單程距離', row.get('one_way_distance', 0))),
                    round_trip_distance=float(row.get('往返距離', row.get('round_trip_distance', 0))),
                    route_type='driving'
                )
                db.session.add(record)
                imported_count += 1
            except Exception as e:
                logger.warning(f"匯入資料行錯誤: {str(e)}")
                continue
        
        db.session.commit()
        
        # 刪除暫存檔案
        os.remove(temp_path)
        
        logger.info(f"匯入出差紀錄成功: {imported_count} 筆")
        
        return jsonify({
            'status': 'success',
            'message': f'成功匯入 {imported_count} 筆資料',
            'data': {'imported_count': imported_count}
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"匯入出差紀錄錯誤: {str(e)}")
        return jsonify({'status': 'error', 'message': '匯入失敗'}), 500

@bp.route('/compare', methods=['POST'])
@jwt_required()
def compare_records():
    """比對出差紀錄"""
    try:
        data = request.get_json()
        record_ids = data.get('record_ids', [])
        
        if not record_ids:
            return jsonify({'status': 'error', 'message': '請選擇要比對的紀錄'}), 400
        
        records = TravelRecord.query.filter(TravelRecord.id.in_(record_ids)).all()
        
        # 重新計算距離並比對
        comparison_results = []
        for record in records:
            calculated = map_service.calculate_distance(
                record.start_location,
                record.end_location,
                record.route_type
            )
            
            if calculated and calculated.get('success'):
                calculated_distance = calculated.get('one_way_km', 0)
                difference = abs(
                    float(record.one_way_distance) - calculated_distance
                )
                comparison_results.append({
                    'record_id': record.id,
                    'original_distance': float(record.one_way_distance),
                    'calculated_distance': calculated_distance,
                    'difference': round(difference, 2),
                    'status': 'match' if difference < 1 else 'mismatch'
                })
        
        return jsonify({
            'status': 'success',
            'data': comparison_results
        }), 200
        
    except Exception as e:
        logger.error(f"比對出差紀錄錯誤: {str(e)}")
        return jsonify({'status': 'error', 'message': '比對失敗'}), 500



