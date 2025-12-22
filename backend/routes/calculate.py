"""
里程計算路由
"""
from flask import Blueprint, request, jsonify
from services.google_maps_service import GoogleMapsService
from services.place_mapping import PlaceMappingService
from services.gmap_screenshot_service import capture_route_screenshot_sync
from loguru import logger
from utils.log_sanitizer import sanitize_log_input
from datetime import datetime
import os

bp = Blueprint('calculate', __name__)
maps_service = GoogleMapsService()
place_mapping = PlaceMappingService()


@bp.route('/distance', methods=['POST'])
def calculate_distance():
    """
    計算單筆距離
    
    請求:
        {
            "origin": "地址字串",
            "destination": "地址字串"
        }
    
    回應:
        {
            "one_way_km": 單程公里數,
            "round_trip_km": 往返公里數,
            "navigation_url": Google Map 導航網址,
            "map_image_path": 靜態地圖檔案路徑
        }
    """
    try:
        data = request.get_json()
        origin = data.get('origin', '').strip()
        destination = data.get('destination', '').strip()
        
        if not origin or not destination:
            return jsonify({
                'status': 'error',
                'message': '請提供起點和終點'
            }), 400
        
        # 解析地點名稱（如果需要的話）
        origin_address = place_mapping.get_address(origin) or origin
        destination_address = place_mapping.get_address(destination) or destination
        
        # 計算距離
        result = maps_service.calculate_distance(origin_address, destination_address)
        
        if not result['success']:
            return jsonify({
                'status': 'error',
                'message': result.get('error', '計算距離失敗')
            }), 400
        
        # 下載靜態地圖
        map_image_path = maps_service.download_static_map(
            origin_address,
            destination_address
        )
        
        response_data = {
            'status': 'success',
            'data': {
                'one_way_km': result['one_way_km'],
                'round_trip_km': result['round_trip_km'],
                'estimated_time': result['estimated_time'],
                'navigation_url': result['navigation_url'],
                'map_image_path': map_image_path,
                'origin_address': origin_address,
                'destination_address': destination_address
            }
        }
        
        # 清理使用者輸入以防止日誌注入（CVE-2024-1681）
        safe_origin = sanitize_log_input(origin)
        safe_destination = sanitize_log_input(destination)
        logger.info(f"成功計算距離: {safe_origin} -> {safe_destination}, {result['one_way_km']} 公里")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"計算距離錯誤: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'計算距離失敗: {str(e)}'
        }), 500


@bp.route('/batch', methods=['POST'])
def calculate_batch():
    """
    批次計算多筆距離
    
    請求:
        {
            "records": [
                {
                    "起點名稱": "...",
                    "目的地名稱": "...",
                    "IsDriving": "Y" or "N",
                    ...
                },
                ...
            ],
            "fixed_origin": "固定起點地址（可選）"
        }
    
    回應:
        {
            "records": 更新後的紀錄列表（含計算結果）
        }
    """
    try:
        data = request.get_json()
        records = data.get('records', [])
        fixed_origin = data.get('fixed_origin', '')
        
        if not records:
            return jsonify({
                'status': 'error',
                'message': '沒有提供資料'
            }), 400
        
        # 處理每筆紀錄
        updated_records = []
        errors = []
        
        for idx, record in enumerate(records):
            try:
                # 只計算 IsDriving=Y 的紀錄
                is_driving = record.get('IsDriving', 'N')
                if is_driving.upper() != 'Y':
                    # 不計算，但保留原始資料
                    updated_records.append(record)
                    continue
                
                # 取得起點和終點
                origin_name = record.get('起點名稱', '')
                destination_name = record.get('目的地名稱', '')
                
                if not origin_name or not destination_name:
                    errors.append(f"第 {idx + 1} 筆資料缺少起點或終點")
                    updated_records.append(record)
                    continue
                
                # 使用固定起點或原始起點
                if fixed_origin:
                    origin_address = fixed_origin
                else:
                    # 優先使用 Google Maps 地理編碼解析地點名稱
                    # 如果解析失敗，再嘗試地址對應表
                    origin_geocode = maps_service.geocode(origin_name)
                    if origin_geocode:
                        origin_address = origin_geocode['formatted_address']
                        logger.info(f"第 {idx + 1} 筆資料起點 Google Maps 解析成功: {origin_name} -> {origin_address}")
                    else:
                        # Google Maps 解析失敗，嘗試地址對應表
                        mapped_origin = place_mapping.get_address(origin_name)
                        origin_address = mapped_origin if mapped_origin else origin_name
                        if mapped_origin:
                            logger.info(f"第 {idx + 1} 筆資料起點使用對應表: {origin_name} -> {origin_address}")
                        else:
                            logger.warning(f"第 {idx + 1} 筆資料起點無法解析，使用原始名稱: {origin_name}")
                
                # 優先使用 Google Maps 地理編碼解析終點名稱
                destination_geocode = maps_service.geocode(destination_name)
                if destination_geocode:
                    destination_address = destination_geocode['formatted_address']
                    logger.info(f"第 {idx + 1} 筆資料終點 Google Maps 解析成功: {destination_name} -> {destination_address}")
                else:
                    # Google Maps 解析失敗，嘗試地址對應表
                    mapped_destination = place_mapping.get_address(destination_name)
                    destination_address = mapped_destination if mapped_destination else destination_name
                    if mapped_destination:
                        logger.info(f"第 {idx + 1} 筆資料終點使用對應表: {destination_name} -> {destination_address}")
                    else:
                        logger.warning(f"第 {idx + 1} 筆資料終點無法解析，使用原始名稱: {destination_name}")
                
                # 檢查起點和終點是否相同
                if origin_address == destination_address and origin_name == destination_name:
                    # 如果地址和名稱都相同，則無法計算
                    errors.append(f"第 {idx + 1} 筆資料起點和終點完全相同: {origin_name}")
                    logger.warning(f"第 {idx + 1} 筆資料起點和終點完全相同: {origin_name}")
                    updated_records.append(record)
                    continue
                elif origin_address == destination_address and origin_name != destination_name:
                    # 如果對應後的地址相同，但原始名稱不同，改用原始名稱進行計算
                    logger.info(f"第 {idx + 1} 筆資料對應地址相同，改用原始名稱計算: {origin_name} -> {destination_name}")
                    origin_address = origin_name
                    destination_address = destination_name
                
                # 記錄實際使用的地址（用於除錯）
                logger.info(f"第 {idx + 1} 筆資料計算: {origin_name} ({origin_address}) -> {destination_name} ({destination_address})")
                
                # 使用新的 get_route_detail 取得詳細路線資訊
                route_detail = maps_service.get_route_detail(origin_address, destination_address)
                
                if not route_detail['success']:
                    error_msg = route_detail.get('error', '未知錯誤')
                    errors.append(f"第 {idx + 1} 筆資料計算失敗: {error_msg}")
                    logger.warning(f"第 {idx + 1} 筆資料計算失敗: {origin_address} -> {destination_address}, 錯誤: {error_msg}")
                    # 即使計算失敗，也保留原始資料
                    updated_records.append(record)
                    continue
                
                # 檢查距離是否為 0（可能是地址解析失敗）
                distance_km = route_detail.get('distance_km', 0)
                if distance_km == 0:
                    errors.append(f"第 {idx + 1} 筆資料計算結果為 0 公里，請檢查地址是否正確: {origin_address} -> {destination_address}")
                    logger.warning(f"第 {idx + 1} 筆資料計算結果為 0 公里: {origin_address} -> {destination_address}")
                    # 即使距離為 0，也保留原始資料，但不更新距離欄位
                    updated_records.append(record)
                    continue
                
                # 使用 Playwright 截取 Google Maps 完整路線頁面（包含左側面板和右側地圖）
                screenshot_path = None
                try:
                    # 準備輸出路徑
                    temp_maps_dir = 'temp/maps'
                    os.makedirs(temp_maps_dir, exist_ok=True)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]  # 包含毫秒
                    screenshot_filename = f"gmap_route_{timestamp}.png"
                    screenshot_path = os.path.join(temp_maps_dir, screenshot_filename)
                    
                    # 使用 Playwright 截取 Google Maps 路線頁面
                    logger.info(f"開始使用 Playwright 截取 Google Maps 路線: {origin_address} -> {destination_address}")
                    screenshot_result = capture_route_screenshot_sync(
                        origin=origin_address,
                        destination=destination_address,
                        output_path=screenshot_path,
                        viewport_width=1500,
                        viewport_height=750
                    )
                    
                    if screenshot_result:
                        screenshot_path = screenshot_result
                        logger.info(f"成功截取 Google Maps 路線截圖: {screenshot_path}")
                    else:
                        logger.warning("Playwright 截圖失敗，回退使用靜態地圖")
                        screenshot_path = None
                        
                except Exception as e:
                    logger.warning(f"Playwright 截圖過程發生錯誤: {str(e)}，回退使用靜態地圖")
                    screenshot_path = None
                
                # 如果 Playwright 截圖失敗，回退使用原本的靜態地圖
                if not screenshot_path or not os.path.exists(screenshot_path):
                    logger.info("回退使用靜態地圖")
                    map_image_path = maps_service.download_static_map_with_polyline(
                        route_detail['polyline'],
                        origin_address,
                        destination_address,
                        distance_km=route_detail['distance_km']
                    )
                    if map_image_path:
                        screenshot_path = map_image_path
                
                # 更新紀錄
                record['OneWayKm'] = route_detail['distance_km']
                record['RoundTripKm'] = route_detail['round_trip_km']
                record['GoogleMapUrl'] = route_detail['map_url']
                record['StepCount'] = route_detail['step_count']
                record['Polyline'] = route_detail['polyline']
                record['RouteSteps'] = route_detail['route_steps_text']
                
                # 保存完整地址（用於 Word 報表顯示）
                record['OriginAddress'] = origin_address
                record['DestinationAddress'] = destination_address
                
                # 保存時間資訊（如果有）
                if 'estimated_time' in route_detail:
                    record['EstimatedTime'] = route_detail['estimated_time']
                
                # 將地圖路徑轉換為相對路徑（用於前端顯示）
                if screenshot_path:
                    # 將絕對路徑轉換為相對路徑，例如：temp/maps/gmap_route_xxx.png
                    record['StaticMapImage'] = screenshot_path.replace('\\', '/')
                else:
                    record['StaticMapImage'] = None
                
                updated_records.append(record)
                
            except Exception as e:
                logger.error(f"處理第 {idx + 1} 筆資料錯誤: {str(e)}")
                errors.append(f"第 {idx + 1} 筆資料處理失敗: {str(e)}")
                updated_records.append(record)
        
        response_data = {
            'status': 'success',
            'data': {
                'records': updated_records,
                'total_count': len(updated_records),
                'calculated_count': sum(1 for r in updated_records if r.get('OneWayKm') is not None),
                'errors': errors
            }
        }
        
        if errors:
            response_data['message'] = f'部分資料計算失敗: {len(errors)} 筆'
        else:
            response_data['message'] = f'成功計算 {response_data["data"]["calculated_count"]} 筆資料'
        
        logger.info(f"批次計算完成: {len(updated_records)} 筆, 成功 {response_data['data']['calculated_count']} 筆")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"批次計算錯誤: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'批次計算失敗: {str(e)}'
        }), 500

