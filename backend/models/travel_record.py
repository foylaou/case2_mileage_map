"""
出差紀錄模型
"""
from datetime import datetime
from sqlalchemy import DECIMAL
from extensions import db

class TravelRecord(db.Model):
    """出差紀錄資料表"""
    __tablename__ = 'travel_records'
    
    id = db.Column(db.Integer, primary_key=True)
    travel_date = db.Column(db.Date, nullable=False, comment='出差日期')
    start_location = db.Column(db.String(200), nullable=False, comment='起點')
    end_location = db.Column(db.String(200), nullable=False, comment='終點')
    one_way_distance = db.Column(DECIMAL(10, 2), comment='單程距離（公里）')
    round_trip_distance = db.Column(DECIMAL(10, 2), comment='往返距離（公里）')
    estimated_time = db.Column(db.String(50), comment='預估時間')
    route_type = db.Column(db.String(20), default='driving', comment='路線類型：driving, walking, transit')
    route_description = db.Column(db.Text, comment='路線說明')
    map_image_path = db.Column(db.String(500), comment='地圖圖片路徑')
    status = db.Column(db.String(20), default='active', comment='狀態：active, archived')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='建立時間')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新時間')
    
    def to_dict(self):
        """轉換為字典"""
        return {
            'id': self.id,
            'travel_date': self.travel_date.isoformat() if self.travel_date else None,
            'start_location': self.start_location,
            'end_location': self.end_location,
            'one_way_distance': float(self.one_way_distance) if self.one_way_distance else 0,
            'round_trip_distance': float(self.round_trip_distance) if self.round_trip_distance else 0,
            'estimated_time': self.estimated_time,
            'route_type': self.route_type,
            'route_description': self.route_description,
            'map_image_path': self.map_image_path,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

