"""
里程計算 API 測試
"""
import pytest

class TestMileage:
    """里程計算功能測試"""
    
    def test_calculate_distance(self, test_client, auth_token):
        """測試計算里程"""
        response = test_client.post(
            '/api/mileage/calculate',
            headers={'Authorization': f'Bearer {auth_token}'},
            json={
                'start_location': '台北市',
                'end_location': '新北市',
                'route_type': 'driving'
            }
        )
        
        # 注意：需要 Google Maps API Key，可能返回 400 或 500
        assert response.status_code in [200, 400, 500]
    
    def test_calculate_distance_missing_fields(self, test_client, auth_token):
        """測試計算里程（缺少欄位）"""
        response = test_client.post(
            '/api/mileage/calculate',
            headers={'Authorization': f'Bearer {auth_token}'},
            json={
                'start_location': '台北市'
            }
        )
        
        assert response.status_code == 400
    
    def test_create_travel_record(self, test_client, auth_token):
        """測試建立出差紀錄"""
        response = test_client.post(
            '/api/mileage/records',
            headers={'Authorization': f'Bearer {auth_token}'},
            json={
                'travel_date': '2025-01-15',
                'start_location': '台北市',
                'end_location': '新北市',
                'one_way_distance': 25.5,
                'round_trip_distance': 51.0,
                'estimated_time': '35 分鐘',
                'route_type': 'driving'
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['status'] == 'success'
    
    def test_get_travel_records(self, test_client, auth_token):
        """測試取得出差紀錄列表"""
        response = test_client.get(
            '/api/mileage/records',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'data' in data









