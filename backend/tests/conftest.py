"""
測試配置檔案
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from extensions import db
from models.user import User
from models.travel_record import TravelRecord

@pytest.fixture(scope='module')
def test_app():
    """建立測試應用程式"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture(scope='module')
def test_client(test_app):
    """建立測試客戶端"""
    return test_app.test_client()

@pytest.fixture(scope='function')
def init_data(test_app):
    """初始化測試資料"""
    with test_app.app_context():
        user = User(
            username='admin',
            name='系統管理員',
            email='admin@test.com',
            role='admin',
            is_active=True
        )
        user.set_password('admin123')
        db.session.add(user)
        db.session.commit()
        
        yield {'user': user}
        
        db.session.delete(user)
        db.session.commit()

@pytest.fixture
def auth_token(test_client, init_data):
    """取得認證 Token"""
    response = test_client.post('/api/auth/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    data = response.get_json()
    return data['data']['token']



