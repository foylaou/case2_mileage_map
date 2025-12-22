"""
系統設定 API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from models.setting import SystemSetting
from extensions import db
from loguru import logger
import json

bp = Blueprint('settings', __name__)

@bp.route('/map', methods=['GET', 'POST'])
@jwt_required()
def map_settings():
    """地圖服務設定"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # 檢查權限
        if user.role != 'admin':
            return jsonify({'status': 'error', 'message': '權限不足'}), 403
        
        if request.method == 'GET':
            # 取得設定
            setting = SystemSetting.query.filter_by(setting_key='map_service').first()
            if setting:
                return jsonify({
                    'status': 'success',
                    'data': json.loads(setting.setting_value)
                }), 200
            return jsonify({'status': 'success', 'data': {}}), 200
        
        elif request.method == 'POST':
            # 儲存設定
            data = request.get_json()
            
            setting = SystemSetting.query.filter_by(setting_key='map_service').first()
            if not setting:
                setting = SystemSetting(
                    setting_key='map_service',
                    setting_type='map',
                    description='地圖服務設定'
                )
                db.session.add(setting)
            
            setting.setting_value = json.dumps(data, ensure_ascii=False)
            db.session.commit()
            
            logger.info("地圖服務設定已更新")
            
            return jsonify({
                'status': 'success',
                'message': '設定已儲存'
            }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"地圖服務設定錯誤: {str(e)}")
        return jsonify({'status': 'error', 'message': '設定失敗'}), 500



