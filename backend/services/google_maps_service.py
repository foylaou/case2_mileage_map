"""
Google Maps API 服務
"""
import googlemaps
import requests
import os
import re
from loguru import logger
from dotenv import load_dotenv
from datetime import datetime
from utils.path_manager import get_temp_maps_dir
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

load_dotenv()


class GoogleMapsService:
    """Google Maps API 服務類別"""
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
        self.gmaps = None
        if self.api_key:
            try:
                self.gmaps = googlemaps.Client(key=self.api_key)
            except Exception as e:
                logger.error(f"初始化 Google Maps 客戶端錯誤: {str(e)}")
    
    def calculate_distance(self, origin, destination, route_type='driving'):
        """
        計算距離
        
        Args:
            origin: 起點地址
            destination: 終點地址
            route_type: 路線類型 (driving, walking, transit)
            
        Returns:
            dict: 包含距離、時間、導航 URL 等資訊
        """
        try:
            if not self.gmaps:
                return {
                    'success': False,
                    'error': 'Google Maps API Key 未設定'
                }
            
            # 使用 Directions API 計算路線
            directions_result = self.gmaps.directions(
                origin,
                destination,
                mode=route_type,
                language='zh-TW'
            )
            
            if not directions_result:
                return {
                    'success': False,
                    'error': '無法計算路線，請檢查地址是否正確'
                }
            
            route = directions_result[0]
            leg = route['legs'][0]
            
            # 取得距離和時間
            distance_km = leg['distance']['value'] / 1000  # 轉換為公里
            duration_text = leg['duration']['text']
            duration_seconds = leg['duration']['value']
            
            # 產生導航 URL
            navigation_url = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}"
            
            return {
                'success': True,
                'one_way_km': round(distance_km, 2),
                'round_trip_km': round(distance_km * 2, 2),
                'estimated_time': duration_text,
                'estimated_seconds': duration_seconds,
                'navigation_url': navigation_url,
                'route': route
            }
            
        except Exception as e:
            logger.error(f"計算距離錯誤: {str(e)}")
            return {
                'success': False,
                'error': f'計算距離失敗: {str(e)}'
            }
    
    def download_static_map(self, origin, destination, output_path=None):
        """
        下載靜態地圖圖片
        
        Args:
            origin: 起點地址
            destination: 終點地址
            output_path: 輸出檔案路徑（可選）
            
        Returns:
            str: 地圖檔案路徑
        """
        try:
            if not self.api_key:
                return None
            
            # 先取得座標
            origin_geo = self.geocode(origin)
            destination_geo = self.geocode(destination)
            
            if not origin_geo or not destination_geo:
                logger.warning(f"無法取得地理座標: {origin} -> {destination}")
                return None
            
            # 建立靜態地圖 URL
            static_map_url = (
                f"https://maps.googleapis.com/maps/api/staticmap?"
                f"size=800x600&"
                f"markers=color:red|label:S|{origin_geo['lat']},{origin_geo['lng']}&"
                f"markers=color:green|label:E|{destination_geo['lat']},{destination_geo['lng']}&"
                f"path=color:0x0000ff|weight:5|{origin_geo['lat']},{origin_geo['lng']}|{destination_geo['lat']},{destination_geo['lng']}&"
                f"key={self.api_key}"
            )
            
            # 下載圖片
            response = requests.get(static_map_url)
            
            if response.status_code != 200:
                logger.error(f"下載靜態地圖失敗: HTTP {response.status_code}")
                return None
            
            # 儲存檔案（使用相對路徑）
            if not output_path:
                maps_dir = get_temp_maps_dir()
                filename = f"map_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(origin + destination) % 10000}.png"
                output_path = maps_dir / filename
            
            with open(str(output_path), 'wb') as f:
                f.write(response.content)
            
            logger.info(f"成功下載靜態地圖: {str(output_path)}")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"下載靜態地圖錯誤: {str(e)}")
            return None
    
    def geocode(self, address):
        """
        地址地理編碼
        
        Args:
            address: 地址字串
            
        Returns:
            dict: 包含經緯度和格式化地址
        """
        try:
            if not self.gmaps:
                return None
            
            geocode_result = self.gmaps.geocode(address, language='zh-TW')
            
            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                return {
                    'lat': location['lat'],
                    'lng': location['lng'],
                    'formatted_address': geocode_result[0]['formatted_address']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"地理編碼錯誤: {str(e)}")
            return None
    
    def resolve_place_name(self, place_name, place_address_map):
        """
        解析地點名稱對應地址
        
        Args:
            place_name: 地點名稱
            place_address_map: 地點名稱對應表
            
        Returns:
            str: 完整地址，如果找不到則回傳 None
        """
        try:
            # 先從對應表查找
            if place_name in place_address_map:
                return place_address_map[place_name]
            
            # 如果對應表找不到，嘗試直接使用名稱進行地理編碼
            geocode_result = self.geocode(place_name)
            if geocode_result:
                return geocode_result['formatted_address']
            
            return None
            
        except Exception as e:
            logger.error(f"解析地點名稱錯誤: {str(e)}")
            return None
    
    def get_route_detail(self, origin_address, dest_address, alternatives=True):
        """
        取得詳細路線導航資訊（包含主要路線和替代路線）
        
        Args:
            origin_address: 起點地址
            dest_address: 終點地址
            alternatives: 是否取得替代路線（預設 True）
            
        Returns:
            dict: 包含總公里數、逐步導航指示、polyline、Google Map 網址、替代路線
            {
                "distance_km": 13.1,
                "steps": [
                    "由○○路向東行駛 300 公尺",
                    "遇到○○路向左轉",
                    ...
                ],
                "polyline": "abcxyz....",  # 主要路線
                "alternative_polylines": ["polyline1", "polyline2"],  # 替代路線（如果有的話）
                "map_url": "https://www.google.com/maps/dir/?api=1&origin=...&destination=...&travelmode=driving",
                "step_count": 導航步驟數,
                "route_steps_text": "純文字格式的路線指示（供 Word 使用）"
            }
        """
        try:
            if not self.gmaps:
                return {
                    'success': False,
                    'error': 'Google Maps API Key 未設定'
                }
            
            # 使用 Directions API 取得路線（包含替代路線）
            directions_result = self.gmaps.directions(
                origin_address,
                dest_address,
                mode='driving',
                language='zh-TW',
                alternatives=alternatives  # 取得替代路線
            )
            
            if not directions_result:
                return {
                    'success': False,
                    'error': '無法取得路線，請檢查地址是否正確'
                }
            
            # 主要路線（第一個結果）
            main_route = directions_result[0]
            main_leg = main_route['legs'][0]
            
            # 取得總距離（單程）
            distance_km = main_leg['distance']['value'] / 1000  # 轉換為公里
            
            # 取得時間資訊
            duration_text = main_leg['duration']['text']
            duration_seconds = main_leg['duration']['value']
            
            # 取得主要路線的 polyline
            main_polyline = main_route['overview_polyline']['points']
            
            # 取得替代路線的 polylines（如果有）
            alternative_polylines = []
            if len(directions_result) > 1:
                for alt_route in directions_result[1:]:  # 跳過第一個（主要路線）
                    if 'overview_polyline' in alt_route:
                        alt_polyline = alt_route['overview_polyline']['points']
                        alternative_polylines.append(alt_polyline)
            
            # 解析主要路線的每個步驟
            steps = []
            for step in main_leg['steps']:
                # 取得 HTML 格式的指示
                html_instructions = step.get('html_instructions', '')
                
                # 清除 HTML 標籤
                clean_instruction = self._clean_html_tags(html_instructions)
                
                # 取得距離和時間
                distance_text = step['distance']['text']
                duration_text = step['duration']['text']
                
                # 組合步驟描述
                step_desc = f"{clean_instruction} ({distance_text})"
                steps.append(step_desc)
            
            # 產生 Google Map 網址
            from urllib.parse import quote
            origin_encoded = quote(origin_address)
            dest_encoded = quote(dest_address)
            map_url = f"https://www.google.com/maps/dir/?api=1&origin={origin_encoded}&destination={dest_encoded}&travelmode=driving"
            
            # 產生純文字格式的路線指示（供 Word 使用）
            route_steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
            
            return {
                'success': True,
                'distance_km': round(distance_km, 2),
                'round_trip_km': round(distance_km * 2, 2),
                'estimated_time': duration_text,  # 新增：時間文字
                'estimated_seconds': duration_seconds,  # 新增：時間秒數
                'steps': steps,
                'step_count': len(steps),
                'polyline': main_polyline,
                'alternative_polylines': alternative_polylines,  # 新增：替代路線
                'map_url': map_url,
                'route_steps_text': route_steps_text
            }
            
        except Exception as e:
            logger.error(f"取得路線詳情錯誤: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': f'取得路線詳情失敗: {str(e)}'
            }
    
    def _clean_html_tags(self, html_text):
        """
        清除 HTML 標籤
        
        Args:
            html_text: 包含 HTML 標籤的文字
            
        Returns:
            str: 清除標籤後的純文字
        """
        # 移除 HTML 標籤
        clean_text = re.sub(r'<[^>]+>', '', html_text)
        
        # 替換 HTML 實體
        clean_text = clean_text.replace('&nbsp;', ' ')
        clean_text = clean_text.replace('&amp;', '&')
        clean_text = clean_text.replace('&lt;', '<')
        clean_text = clean_text.replace('&gt;', '>')
        clean_text = clean_text.replace('&quot;', '"')
        
        return clean_text.strip()
    
    def download_static_map_with_polyline(self, polyline, origin_address, destination_address, distance_km=None, output_path=None, alternative_polylines=None):
        """
        下載帶路線 polyline 的靜態地圖圖片（使用 Google Maps 官方樣式）
        
        使用 Directions API + Static Maps API 產生完全符合 Google Maps 網頁版樣式的地圖
        包含：官方道路底圖、藍色主要路線、灰色替代路線、起點/終點標記
        
        Args:
            polyline: 主要路線編碼字串（來自 Directions API）
            origin_address: 起點地址（用於標記和地理編碼）
            destination_address: 終點地址（用於標記和地理編碼）
            distance_km: 公里數（會顯示在地圖上）
            output_path: 輸出檔案路徑（可選）
            alternative_polylines: 替代路線的 polyline 列表（可選）
            
        Returns:
            str: 地圖檔案路徑
        """
        try:
            if not self.api_key:
                return None
            
            # 獲取起點和終點的座標（用於標記）
            origin_geo = self.geocode(origin_address)
            destination_geo = self.geocode(destination_address)
            
            if not origin_geo or not destination_geo:
                logger.warning(f"無法取得地理座標: {origin_address} -> {destination_address}")
                # 如果無法取得座標，回退到簡單方式
                return self._download_simple_static_map(polyline, origin_address, destination_address, distance_km, output_path)
            
            from urllib.parse import quote
            
            # 構建 Static Maps API URL 參數
            url_parts = []
            
            # 基本參數
            url_parts.append("size=1200x800")  # 更大的尺寸以顯示更多細節
            url_parts.append("maptype=roadmap")  # 使用道路地圖（Google Maps 官方樣式）
            url_parts.append("format=png")  # PNG 格式
            
            # 主要路線：使用 Google Maps 官方的藍色（#4285F4）
            # weight=6: 路線粗細（符合 Google Maps 網頁版主要路線）
            # fillcolor: 路線填充顏色（半透明藍色，符合官方樣式）
            main_path = f"color:0x4285F4|weight:6|fillcolor:0x4285F480|enc:{polyline}"
            url_parts.append(f"path={quote(main_path)}")
            
            # 替代路線：使用灰色（#808080），較細的線條
            # 符合 Google Maps 網頁版顯示替代路線的方式
            if alternative_polylines:
                for alt_polyline in alternative_polylines:
                    alt_path = f"color:0x808080|weight:4|fillcolor:0x80808040|enc:{alt_polyline}"
                    url_parts.append(f"path={quote(alt_path)}")
            
            # 起點標記：紅色圓點（Google Maps 官方起點顏色）
            # 使用 icon 參數可以自訂標記樣式，但這裡使用預設的紅色標記
            origin_marker = f"color:0xFF0000|label:A|{origin_geo['lat']},{origin_geo['lng']}"
            url_parts.append(f"markers={quote(origin_marker)}")
            
            # 終點標記：綠色圓點（Google Maps 官方終點顏色）
            destination_marker = f"color:0x00FF00|label:B|{destination_geo['lat']},{destination_geo['lng']}"
            url_parts.append(f"markers={quote(destination_marker)}")
            
            # API Key
            url_parts.append(f"key={self.api_key}")
            
            # 構建完整的 Static Maps API URL
            static_map_url = f"https://maps.googleapis.com/maps/api/staticmap?{'&'.join(url_parts)}"
            
            logger.debug(f"Static Maps API URL 長度: {len(static_map_url)} 字元")
            
            # 下載圖片
            response = requests.get(static_map_url, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"下載靜態地圖失敗: HTTP {response.status_code}, Response: {response.text[:200]}")
                # 如果失敗，回退到簡單方式
                return self._download_simple_static_map(polyline, origin_address, destination_address, distance_km, output_path)
            
            # 檢查回應是否為圖片
            if not response.content.startswith(b'\x89PNG'):
                error_text = response.text[:500] if hasattr(response, 'text') else str(response.content[:200])
                logger.error(f"下載的內容不是有效的 PNG 圖片: {error_text}")
                return self._download_simple_static_map(polyline, origin_address, destination_address, distance_km, output_path)
            
            # 儲存檔案（使用相對路徑）
            if not output_path:
                maps_dir = get_temp_maps_dir()
                filename = f"map_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(origin_address + destination_address) % 10000}.png"
                output_path = maps_dir / filename
            else:
                output_path = Path(output_path)
            
            with open(str(output_path), 'wb') as f:
                f.write(response.content)
            
            # 如果有公里數，在地圖上加字（使用更符合 Google Maps 風格的樣式）
            if distance_km is not None:
                self._add_km_text_to_map(str(output_path), distance_km)
            
            logger.info(f"成功下載 Google Maps 官方樣式靜態地圖: {str(output_path)}")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"下載靜態地圖錯誤: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # 如果出錯，回退到簡單方式
            return self._download_simple_static_map(polyline, origin_address, destination_address, distance_km, output_path)
    
    def _download_simple_static_map(self, polyline, origin_address, destination_address, distance_km=None, output_path=None):
        """
        回退方法：使用簡單的靜態地圖（當官方樣式失敗時使用）
        """
        try:
            if not self.api_key:
                return None
            
            # 簡單的靜態地圖 URL
            static_map_url = (
                f"https://maps.googleapis.com/maps/api/staticmap?"
                f"size=800x600&"
                f"maptype=roadmap&"
                f"path=enc:{polyline}&"
                f"key={self.api_key}"
            )
            
            response = requests.get(static_map_url, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"下載簡單靜態地圖失敗: HTTP {response.status_code}")
                return None
            
            if not output_path:
                maps_dir = get_temp_maps_dir()
                filename = f"map_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(origin_address + destination_address) % 10000}.png"
                output_path = maps_dir / filename
            else:
                output_path = Path(output_path)
            
            with open(str(output_path), 'wb') as f:
                f.write(response.content)
            
            if distance_km is not None:
                self._add_km_text_to_map(str(output_path), distance_km)
            
            logger.info(f"成功下載簡單靜態地圖: {str(output_path)}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"下載簡單靜態地圖錯誤: {str(e)}")
            return None
    
    def _add_km_text_to_map(self, image_path, km):
        """
        在地圖圖片上加入公里數文字
        
        Args:
            image_path: 地圖圖片路徑
            km: 公里數
        """
        try:
            # 開啟圖片
            img = Image.open(image_path)
            
            # 如果圖片是 RGB 模式，轉換為 RGBA 以支援半透明
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # 創建一個新的 RGBA 圖片用於繪製
            overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            
            # 設定文字
            text = f"{km} km"
            
            # 嘗試載入字型（如果找不到，使用預設字型）
            # 使用跨平台字體路徑檢測，避免硬編碼絕對路徑
            font = None
            font_paths = []
            
            # Windows 字體路徑
            if os.name == 'nt':
                windows_font_dir = os.path.join(os.environ.get('WINDIR', 'C:/Windows'), 'Fonts')
                font_paths.extend([
                    os.path.join(windows_font_dir, 'msjh.ttc'),  # 微軟正黑體
                    os.path.join(windows_font_dir, 'simsun.ttc'),  # 新細明體
                    os.path.join(windows_font_dir, 'arial.ttf'),  # Arial
                ])
            
            # Linux 字體路徑
            elif os.name == 'posix':
                linux_font_dirs = [
                    '/usr/share/fonts/truetype/droid',
                    '/usr/share/fonts/truetype/liberation',
                    '/usr/share/fonts/TTF',
                ]
                for font_dir in linux_font_dirs:
                    if os.path.exists(font_dir):
                        font_paths.extend([
                            os.path.join(font_dir, 'DroidSansFallbackFull.ttf'),
                            os.path.join(font_dir, 'LiberationSans-Regular.ttf'),
                        ])
            
            # 嘗試載入字體
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, 36)
                        break
                    except Exception:
                        continue
            
            # 如果找不到字體，使用預設字型
            if font is None:
                font = ImageFont.load_default()
            
            # 計算文字位置（左上角）
            x, y = 20, 20
            
            # 繪製背景（白色半透明矩形）
            bbox = draw.textbbox((x, y), text, font=font)
            padding = 10
            draw.rectangle(
                [bbox[0] - padding, bbox[1] - padding, bbox[2] + padding, bbox[3] + padding],
                fill=(255, 255, 255, 200)  # RGBA 顏色
            )
            
            # 繪製文字（紅色）
            draw.text((x, y), text, fill=(255, 0, 0, 255), font=font)  # RGBA 顏色
            
            # 將 overlay 合成到原圖上
            img = Image.alpha_composite(img, overlay)
            
            # 如果原圖是 RGB，轉回 RGB 模式以節省空間
            if img.mode == 'RGBA':
                # 創建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # 使用 alpha 通道作為 mask
                img = background
            
            # 儲存圖片
            img.save(image_path)
            
            logger.info(f"成功在地圖上添加公里數: {km} km")
            
        except Exception as e:
            logger.error(f"在地圖上添加公里數錯誤: {str(e)}")





