"""
使用者模型（與第一案共用或獨立）
"""
from datetime import datetime
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """使用者資料表"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, comment='帳號')
    password_hash = db.Column(db.String(255), nullable=False, comment='密碼雜湊')
    name = db.Column(db.String(100), nullable=False, comment='姓名')
    email = db.Column(db.String(100), nullable=False, comment='電子郵件')
    role = db.Column(db.String(20), nullable=False, default='user', comment='角色：admin, user')
    is_active = db.Column(db.Boolean, default=True, comment='是否啟用')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='建立時間')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新時間')
    
    def set_password(self, password):
        """設定密碼"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """驗證密碼"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """轉換為字典"""
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }



