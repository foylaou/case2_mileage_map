"""
系統設定模型
"""
from datetime import datetime
from extensions import db

class SystemSetting(db.Model):
    """系統設定資料表"""
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False, comment='設定鍵值')
    setting_value = db.Column(db.Text, comment='設定值（JSON格式）')
    setting_type = db.Column(db.String(50), comment='設定類型：map, system')
    description = db.Column(db.String(500), comment='說明')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='建立時間')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新時間')
    
    def to_dict(self):
        """轉換為字典"""
        return {
            'id': self.id,
            'setting_key': self.setting_key,
            'setting_value': self.setting_value,
            'setting_type': self.setting_type,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }



