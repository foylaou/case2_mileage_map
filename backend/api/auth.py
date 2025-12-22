"""
認證 API（與第一案共用或獨立）
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.user import User
from extensions import db
from loguru import logger
from utils.log_sanitizer import sanitize_log_input

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['POST'])
def login():
    """使用者登入"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'status': 'error', 'message': '請輸入帳號和密碼'}), 400
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({'status': 'error', 'message': '帳號或密碼錯誤'}), 401
        
        if not user.is_active:
            return jsonify({'status': 'error', 'message': '帳號已停用'}), 403
        
        access_token = create_access_token(identity=user.id)
        
        # 清理使用者名稱以防止日誌注入（CVE-2024-1681）
        safe_username = sanitize_log_input(username)
        logger.info(f"使用者登入成功: {safe_username}")
        
        return jsonify({
            'status': 'success',
            'message': '登入成功',
            'data': {
                'token': access_token,
                'user': user.to_dict()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"登入錯誤: {str(e)}")
        return jsonify({'status': 'error', 'message': '登入失敗'}), 500

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """取得目前使用者資訊"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'status': 'error', 'message': '使用者不存在'}), 404
        
        return jsonify({
            'status': 'success',
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"取得使用者資訊錯誤: {str(e)}")
        return jsonify({'status': 'error', 'message': '取得使用者資訊失敗'}), 500



