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
import math
from PIL import Image, ImageDraw, ImageFont
import textwrap

load_dotenv()


class GoogleMapsService:
    """Google Maps API 服務類別"""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
        self.gmaps = None
        if self.api_key:
            try:
                self.gmaps = googlemaps.Client(key=self.api_key)
            except Exception as e:
                logger.error(f"初始化 Google Maps 客戶端錯誤: {str(e)}")

    def calculate_distance(self, origin, destination, route_type="driving"):
        """
        計算距離
        """
        try:
            if not self.gmaps:
                return {"success": False, "error": "Google Maps API Key 未設定"}

            directions_result = self.gmaps.directions(
                origin,
                destination,
                mode=route_type,
                language="zh-TW",
            )

            if not directions_result:
                return {"success": False, "error": "無法計算路線，請檢查地址是否正確"}

            route = directions_result[0]
            leg = route["legs"][0]

            distance_km = leg["distance"]["value"] / 1000
            duration_text = leg["duration"]["text"]
            duration_seconds = leg["duration"]["value"]

            navigation_url = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}"

            return {
                "success": True,
                "one_way_km": round(distance_km, 2),
                "round_trip_km": round(distance_km * 2, 2),
                "estimated_time": duration_text,
                "estimated_seconds": duration_seconds,
                "navigation_url": navigation_url,
                "route": route,
            }

        except Exception as e:
            logger.error(f"計算距離錯誤: {str(e)}")
            return {"success": False, "error": f"計算距離失敗: {str(e)}"}

    def download_static_map(self, origin, destination, output_path=None):
        """
        下載靜態地圖圖片（簡易版）
        """
        try:
            if not self.api_key:
                return None

            origin_geo = self.geocode(origin)
            destination_geo = self.geocode(destination)

            if not origin_geo or not destination_geo:
                logger.warning(f"無法取得地理座標: {origin} -> {destination}")
                return None

            static_map_url = (
                f"https://maps.googleapis.com/maps/api/staticmap?"
                f"size=800x600&"
                f"markers=color:red|label:S|{origin_geo['lat']},{origin_geo['lng']}&"
                f"markers=color:green|label:E|{destination_geo['lat']},{destination_geo['lng']}&"
                f"path=color:0x0000ff|weight:5|{origin_geo['lat']},{origin_geo['lng']}|{destination_geo['lat']},{destination_geo['lng']}&"
                f"key={self.api_key}"
            )

            response = requests.get(static_map_url, timeout=30)
            if response.status_code != 200:
                logger.error(f"下載靜態地圖失敗: HTTP {response.status_code}")
                return None

            if not output_path:
                maps_dir = get_temp_maps_dir()
                filename = f"map_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(origin + destination) % 10000}.png"
                output_path = maps_dir / filename

            with open(str(output_path), "wb") as f:
                f.write(response.content)

            logger.info(f"成功下載靜態地圖: {str(output_path)}")
            return str(output_path)

        except Exception as e:
            logger.error(f"下載靜態地圖錯誤: {str(e)}")
            return None

    def geocode(self, address):
        """
        地址地理編碼
        """
        try:
            if not self.gmaps:
                return None

            geocode_result = self.gmaps.geocode(address, language="zh-TW")
            if geocode_result:
                location = geocode_result[0]["geometry"]["location"]
                return {
                    "lat": location["lat"],
                    "lng": location["lng"],
                    "formatted_address": geocode_result[0]["formatted_address"],
                }

            return None

        except Exception as e:
            logger.error(f"地理編碼錯誤: {str(e)}")
            return None

    def resolve_place_name(self, place_name, place_address_map):
        """
        解析地點名稱對應地址
        """
        try:
            if place_name in place_address_map:
                return place_address_map[place_name]

            geocode_result = self.geocode(place_name)
            if geocode_result:
                return geocode_result["formatted_address"]

            return None

        except Exception as e:
            logger.error(f"解析地點名稱錯誤: {str(e)}")
            return None

    def get_route_detail(self, origin_address, dest_address, alternatives=True):
        """
        取得詳細路線導航資訊（包含主要路線和替代路線）
        """
        try:
            if not self.gmaps:
                return {"success": False, "error": "Google Maps API Key 未設定"}

            directions_result = self.gmaps.directions(
                origin_address,
                dest_address,
                mode="driving",
                language="zh-TW",
                alternatives=alternatives,
            )

            if not directions_result:
                return {"success": False, "error": "無法取得路線，請檢查地址是否正確"}

            main_route = directions_result[0]
            main_leg = main_route["legs"][0]

            distance_km = main_leg["distance"]["value"] / 1000

            duration_text = main_leg["duration"]["text"]
            duration_seconds = main_leg["duration"]["value"]

            main_polyline = main_route["overview_polyline"]["points"]

            alternative_polylines = []
            if len(directions_result) > 1:
                for alt_route in directions_result[1:]:
                    if "overview_polyline" in alt_route:
                        alternative_polylines.append(alt_route["overview_polyline"]["points"])

            steps = []
            for step in main_leg["steps"]:
                html_instructions = step.get("html_instructions", "")
                clean_instruction = self._clean_html_tags(html_instructions)
                distance_text = step["distance"]["text"]
                step_desc = f"{clean_instruction} ({distance_text})"
                steps.append(step_desc)

            from urllib.parse import quote
            origin_encoded = quote(origin_address)
            dest_encoded = quote(dest_address)
            map_url = (
                f"https://www.google.com/maps/dir/?api=1"
                f"&origin={origin_encoded}"
                f"&destination={dest_encoded}"
                f"&travelmode=driving"
            )

            route_steps_text = "\n".join([f"{i+1}. {s}" for i, s in enumerate(steps)])

            return {
                "success": True,
                "distance_km": round(distance_km, 2),
                "round_trip_km": round(distance_km * 2, 2),
                "estimated_time": duration_text,
                "estimated_seconds": duration_seconds,
                "steps": steps,
                "step_count": len(steps),
                "polyline": main_polyline,
                "alternative_polylines": alternative_polylines,
                "map_url": map_url,
                "route_steps_text": route_steps_text,
            }

        except Exception as e:
            logger.error(f"取得路線詳情錯誤: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "error": f"取得路線詳情失敗: {str(e)}"}

    def _clean_html_tags(self, html_text):
        """
        清除 HTML 標籤
        """
        clean_text = re.sub(r"<[^>]+>", "", html_text)
        clean_text = clean_text.replace("&nbsp;", " ")
        clean_text = clean_text.replace("&amp;", "&")
        clean_text = clean_text.replace("&lt;", "<")
        clean_text = clean_text.replace("&gt;", ">")
        clean_text = clean_text.replace("&quot;", '"')
        return clean_text.strip()

    # =========================
    # NEW: map annotation (km + A/B formatted address + generated time)
    # =========================
    def _load_cjk_font(self, size: int):
        from PIL import ImageFont
        import os

        candidates = []

        # Windows
        if os.name == "nt":
            win = os.environ.get("WINDIR", "C:/Windows")
            candidates += [
                os.path.join(win, "Fonts", "msjh.ttc"),   # 微軟正黑體
                os.path.join(win, "Fonts", "msjhbd.ttc"),
                os.path.join(win, "Fonts", "simsun.ttc"),
                os.path.join(win, "Fonts", "kaiu.ttf"),
                os.path.join(win, "Fonts", "arial.ttf"),
            ]
            # Add user local fonts just in case
            local = os.environ.get("LOCALAPPDATA", "")
            if local:
                 candidates.append(os.path.join(local, "Microsoft", "Windows", "Fonts", "msjh.ttc"))
        else:
            # Render / Ubuntu 常見 Noto CJK 路徑
            candidates += [
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJKtc-Regular.otf",
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/truetype/noto/NotoSansTC-Regular.otf",
                "/usr/share/fonts/truetype/noto/NotoSansTC-Regular.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
            
        # 專案內建字型 (最高優先級)
        assets_fonts_dir = Path(__file__).parent.parent / "assets" / "fonts"
        candidates.insert(0, str(assets_fonts_dir / "msjh.ttc"))
        candidates.insert(1, str(assets_fonts_dir / "NotoSansCJKtc-Regular.otf"))

        for fp in candidates:
            if fp and os.path.exists(fp):
                try:
                    # 嘗試不同的 index，針對 TTC
                    if fp.lower().endswith('.ttc'):
                        try:
                            return ImageFont.truetype(fp, size, index=0)
                        except:
                             return ImageFont.truetype(fp, size, index=1)
                    return ImageFont.truetype(fp, size)
                except Exception:
                    continue

        return ImageFont.load_default()

    def annotate_map_info(self, image_path: str, distance_km, origin_addr: str, dest_addr: str, round_trip_km=None, date_text=None):
        """
        產生符合使用者需求的「報表型」地圖：
        1. 頂部 Header：日期 + 起點 + 終點 + 往返核銷里程
        2. 地圖左上角 Badge：單程公里數 (紅字白底)
        """
        try:
            # 確保內容是字串
            origin_addr = str(origin_addr).replace("台灣", "") if origin_addr else "" # 移除重複的台灣若有
            # 簡單優化地址顯示
            if origin_addr.startswith("號"): origin_addr = origin_addr[1:]
            
            dest_addr = str(dest_addr).replace("台灣", "") if dest_addr else ""
            
            # 日期處理
            date_str = ""
            if date_text:
                try:
                    # 嘗試解析日期字串，格式化為 MM/DD
                    # 假設輸入可能是 YYYY-MM-DD 或 YYYY/MM/DD
                    dt = None
                    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"]:
                        try:
                            dt = datetime.strptime(str(date_text).split(' ')[0], fmt)
                            break
                        except ValueError:
                            continue
                    if dt:
                        date_str = dt.strftime("%m/%d")
                    else:
                        date_str = str(date_text)
                except:
                    date_str = str(date_text)
            
            # 若無日期，使用當日
            if not date_str:
                date_str = datetime.now().strftime("%m/%d")

            base = Image.open(image_path).convert("RGB")
            W, H = base.size

            # 計算縮放比例（以 1000px 為基準）
            scale = max(W / 1000.0, 0.8)
            
            # 刪除舊的 Header 邏輯，改用 Overlay
            # 建立可繪圖物件 (直接在地圖圖層上畫)
            draw = ImageDraw.Draw(base, "RGBA") # 確保支援 alpha
            
            import textwrap

            # -----------------------------------------------
            # 1. 左上角 Badge (KM)
            # -----------------------------------------------
            if distance_km is not None:
                km_text = f"{distance_km} km"
                font_km = self._load_cjk_font(int(40 * scale))
                
                dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))
                bbox = dummy.textbbox((0, 0), km_text, font=font_km)
                w = bbox[2] - bbox[0] + int(30 * scale)
                h = bbox[3] - bbox[1] + int(20 * scale)
                
                x, y = int(20 * scale), int(20 * scale)
                
                # 陰影
                draw.rounded_rectangle([x+2, y+2, x+w+2, y+h+2], radius=10, fill=(0,0,0,100))
                # 白底
                draw.rounded_rectangle([x, y, x+w, y+h], radius=10, fill=(255,255,255,230))
                # 紅字
                text_x = x + int(15 * scale)
                text_y = y + int(10 * scale)
                draw.text((text_x, text_y), km_text, fill=(200, 0, 0), font=font_km)

            # -----------------------------------------------
            # 2. 左下角 Address Box (A/B) - 半透明白底
            # -----------------------------------------------
            font_addr = self._load_cjk_font(int(24 * scale))
            
            # 定義文字內容
            origin_full = f"A (起點): {origin_addr}"
            dest_full = f"B (終點): {dest_addr}"
            
            # 計算最大寬度 (例如圖片寬度的 60%)
            max_text_width = int(W * 0.6)
            
            # 使用 textwrap 換行
            # 先估算字元數... 不太準，直接用 PIL 計算並手動換行比較複雜
            # 簡單做法：按字數切，假設全形寬度
            # 24px font, max 600px width => 25 chars
            char_limit = int(max_text_width / (24 * scale))
             
            origin_wrapped = textwrap.fill(origin_full, width=char_limit)
            dest_wrapped = textwrap.fill(dest_full, width=char_limit)
            full_text = origin_wrapped + "\n" + dest_wrapped
            
            # 計算包圍盒
            dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))
            bbox = dummy.textmultilinebbox((0, 0), full_text, font=font_addr, spacing=4)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            
            box_w = text_w + int(30 * scale)
            box_h = text_h + int(30 * scale)
            
            # 左下角位置 (padding 20)
            box_x = int(20 * scale)
            box_y = H - box_h - int(20 * scale)
            
            # 如果跟 Badge 重疊 (雖然 Badge 在左上，Address 在左下，通常不會，除非地圖很矮)
            # 畫半透明框
            # PIL Draw.rectangle 不支援 alpha fill on RGB image unless "RGBA" mode
            # 這裡我們確認 base 已經是 RGB (from line 329)，需要轉 RGBA 才能畫半透明
             
            # 畫框
            overlay = Image.new('RGBA', base.size, (0,0,0,0))
            draw_ov = ImageDraw.Draw(overlay)
            draw_ov.rounded_rectangle(
                [box_x, box_y, box_x + box_w, box_y + box_h],
                radius=10, 
                fill=(255, 255, 255, 200) # 半透明白
            )
            # 畫線條區隔 A 和 B (可選，這裡省略)

            # 畫文字
            text_start_x = box_x + int(15 * scale)
            text_start_y = box_y + int(15 * scale)
            
            # 分開畫顏色 (A紅色 B紅色 其他黑色)
            # 這裡簡單處理：全部黑色，A/B 前綴稍微區別? 無法混色 in one string
            # 直接畫全黑即可，清楚最重要
            draw_ov.text((text_start_x, text_start_y), full_text, fill=(0, 0, 0), font=font_addr, spacing=4)
            
            # 合併
            base = base.convert("RGBA")
            base = Image.alpha_composite(base, overlay)
            base = base.convert("RGB")

            # -----------------------------------------------
            # 3. 右下角 Timestamp
            # -----------------------------------------------
            # 格式：System Generated: YYYY/MM/DD HH:MM
            ts_str = f"系統產出時間: {datetime.now().strftime('%Y/%m/%d %H:%M')}"
            font_ts = self._load_cjk_font(int(20 * scale))
            
            bbox_ts = dummy.textbbox((0, 0), ts_str, font=font_ts)
            ts_w = bbox_ts[2] - bbox_ts[0]
            ts_h = bbox_ts[3] - bbox_ts[1]
            
            ts_x = W - ts_w - int(20 * scale)
            ts_y = H - ts_h - int(20 * scale)
            
            # 加個白色暈開效果 (Halo) 增加可讀性
            draw = ImageDraw.Draw(base) # RGB mode now
            halo_r = 2
            for ox in range(-halo_r, halo_r+1):
                for oy in range(-halo_r, halo_r+1):
                    draw.text((ts_x+ox, ts_y+oy), ts_str, font=font_ts, fill=(255,255,255))
            
            draw.text((ts_x, ts_y), ts_str, font=font_ts, fill=(50, 50, 50))

            # 存檔
            base.save(image_path)
            logger.info("地圖已套用 Burn-in 樣式（KM + Address Overlay + Timestamp）")

        except Exception as e:
            logger.error(f"在地圖上標註 Header 資訊錯誤: {str(e)}")


    def download_static_map_with_polyline(
        self,
        polyline,
        origin_address,
        destination_address,
        distance_km=None,
        output_path=None,
        alternative_polylines=None,
    ):
        """
        下載帶路線 polyline 的靜態地圖圖片（使用 Google Maps 官方樣式）
        - 移除 fillcolor，避免出現藍色/灰色半透明面積
        - 下載後用 PIL 加註：公里數 + A/B formatted address + 系統產出時間
        """
        try:
            if not self.api_key:
                return None

            origin_geo = self.geocode(origin_address)
            destination_geo = self.geocode(destination_address)

            if not origin_geo or not destination_geo:
                logger.warning(f"無法取得地理座標: {origin_address} -> {destination_address}")
                return self._download_simple_static_map(
                    polyline, origin_address, destination_address, distance_km, output_path
                )

            from urllib.parse import quote

            url_parts = []
            url_parts.append("maptype=roadmap")
            url_parts.append("format=png")

            # 計算合適的 zoom 和 center
            W, H = 1200, 800
            zoom, center_lat, center_lng = self._choose_zoom_for_two_points(
                origin_geo["lat"], origin_geo["lng"],
                destination_geo["lat"], destination_geo["lng"],
                W, H, padding_px=120
            )

            url_parts.append(f"size={W}x{H}")
            url_parts.append(f"zoom={zoom}")
            url_parts.append(f"center={center_lat},{center_lng}")

            # 主路線：只畫線（不使用 fillcolor）
            main_path = f"color:0x4285F4|weight:6|enc:{polyline}"
            url_parts.append(f"path={quote(main_path)}")

            # 替代路線：只畫線（不使用 fillcolor）
            if alternative_polylines:
                for alt_polyline in alternative_polylines:
                    alt_path = f"color:0x808080|weight:4|enc:{alt_polyline}"
                    url_parts.append(f"path={quote(alt_path)}")

            # 起點：紅色標記，標籤 A
            origin_marker = f"color:0xFF0000|label:A|{origin_geo['lat']},{origin_geo['lng']}"
            url_parts.append(f"markers={quote(origin_marker)}")

            # 終點：紅色標記，標籤 B
            destination_marker = f"color:0xFF0000|label:B|{destination_geo['lat']},{destination_geo['lng']}"
            url_parts.append(f"markers={quote(destination_marker)}")

            url_parts.append(f"key={self.api_key}")

            static_map_url = f"https://maps.googleapis.com/maps/api/staticmap?{'&'.join(url_parts)}"
            logger.debug(f"Static Maps API URL 長度: {len(static_map_url)} 字元")

            response = requests.get(static_map_url, timeout=30)
            if response.status_code != 200:
                logger.error(f"下載靜態地圖失敗: HTTP {response.status_code}, Response: {response.text[:200]}")
                return self._download_simple_static_map(
                    polyline, origin_address, destination_address, distance_km, output_path
                )

            if not response.content.startswith(b"\x89PNG"):
                error_text = response.text[:500] if hasattr(response, "text") else str(response.content[:200])
                logger.error(f"下載的內容不是有效的 PNG 圖片: {error_text}")
                return self._download_simple_static_map(
                    polyline, origin_address, destination_address, distance_km, output_path
                )

            if not output_path:
                maps_dir = get_temp_maps_dir()
                filename = f"map_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(origin_address + destination_address) % 10000}.png"
                output_path = maps_dir / filename
            else:
                output_path = Path(output_path)

            with open(str(output_path), "wb") as f:
                f.write(response.content)

            # 加註：公里數 + A/B 地址（formatted address）+ 系統產出時間
            # 加註：公里數 + A/B 地址（formatted address）+ 系統產出時間
            # 1. 先加整體資訊（km + 右下時間）
            self.annotate_map_info(
                str(output_path),
                distance_km,
                origin_geo.get("formatted_address", origin_address),
                destination_geo.get("formatted_address", destination_address),
            )

            # 2. 再加：A/B marker 旁邊的地址（貼近點）
            self._annotate_ab_near_markers(
                str(output_path),
                origin_geo["lat"], origin_geo["lng"],
                destination_geo["lat"], destination_geo["lng"],
                origin_geo.get("formatted_address", origin_address),
                destination_geo.get("formatted_address", destination_address),
                zoom=zoom,
                center_lat=center_lat,
                center_lng=center_lng,
            )

            logger.info(f"成功下載 Google Maps 官方樣式靜態地圖: {str(output_path)}")
            return str(output_path)

        except Exception as e:
            logger.error(f"下載靜態地圖錯誤: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return self._download_simple_static_map(
                polyline, origin_address, destination_address, distance_km, output_path
            )

    def _download_simple_static_map(self, polyline, origin_address, destination_address, distance_km=None, output_path=None):
        """
        回退方法：使用簡單的靜態地圖（當官方樣式失敗時使用）
        也會加註：公里數 + A/B 地址 + 系統產出時間（確保一致）
        """
        try:
            if not self.api_key:
                return None

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

            with open(str(output_path), "wb") as f:
                f.write(response.content)

            # 嘗試拿 formatted address（沒有就用原字串）
            origin_geo = self.geocode(origin_address) or {}
            dest_geo = self.geocode(destination_address) or {}
            origin_fmt = origin_geo.get("formatted_address", origin_address)
            dest_fmt = dest_geo.get("formatted_address", destination_address)

            self.annotate_map_info(str(output_path), distance_km, origin_fmt, dest_fmt)

            logger.info(f"成功下載簡單靜態地圖: {str(output_path)}")
            return str(output_path)

        except Exception as e:
            logger.error(f"下載簡單靜態地圖錯誤: {str(e)}")
            return None
       
    def _draw_ab_markers(self, draw, ax, ay, bx, by):
        """
        手動繪製 A/B 點 Marker (確保一定看得到)
        """
        # 圓點半徑
        r = 12

        # A: 紅色 (起點)
        draw.ellipse((ax - r, ay - r, ax + r, ay + r), fill=(255, 0, 0, 255), outline=(255, 255, 255, 255), width=3)
        # B: 綠色 (終點)
        draw.ellipse((bx - r, by - r, bx + r, by + r), fill=(0, 180, 0, 255), outline=(255, 255, 255, 255), width=3)
        
        # 在圓點中間畫上 A / B 文字 (選擇性)
        font_marker = ImageFont.load_default()
        # 簡單置中 A
        draw.text((ax-3, ay-5), "A", fill=(255,255,255), font=font_marker)
        # 簡單置中 B
        draw.text((bx-3, by-5), "B", fill=(255,255,255), font=font_marker)

    def _annotate_ab_near_markers(self, image_path: str, a_lat, a_lng, b_lat, b_lng, a_addr: str, b_addr: str,
                                  zoom: int, center_lat: float, center_lng: float):
        """
        將 A/B 地址畫在 A/B 點旁邊（貼近 marker）
        """
        try:
            img = Image.open(image_path)
            if img.mode != "RGBA":
                img = img.convert("RGBA")

            overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)

            # 字型（使用新的通用載入邏輯）
            font = self._load_cjk_font(24)

            W, H = img.size

            # 轉成像素座標
            ax, ay = self._latlng_to_pixel(a_lat, a_lng, zoom, W, H, center_lat, center_lng)
            bx, by = self._latlng_to_pixel(b_lat, b_lng, zoom, W, H, center_lat, center_lng)

            # 1. 先畫 A/B 圓點（不靠 Google markers）
            self._draw_ab_markers(draw, ax, ay, bx, by)

            # 2. 再畫 A/B 地址框
            a_text = f"A點：{a_addr}"
            b_text = f"B點：{b_addr}"

            # 預設放右上（避免壓到 marker），如果超出邊界就換位置
            def place_box(px, py, text, prefer="right"):
                offset = 20 # 避開 marker 半徑
                max_w = int(W * 0.42)

                # 候選位置：右上、右下、左上、左下
                candidates = []
                if prefer == "right":
                    candidates = [
                        (px + offset, py - 60),
                        (px + offset, py + offset),
                        (px - max_w - offset, py - 60),
                        (px - max_w - offset, py + offset),
                    ]
                else:
                    candidates = [
                        (px - max_w - offset, py - 60),
                        (px - max_w - offset, py + offset),
                        (px + offset, py - 60),
                        (px + offset, py + offset),
                    ]

                for (x, y) in candidates:
                    # 先畫在暫存 overlay 上試 bbox
                    tmp = Image.new("RGBA", overlay.size, (0, 0, 0, 0))
                    tmp_draw = ImageDraw.Draw(tmp)
                    bb = self._draw_label_box(tmp_draw, text, x, y, font, max_width=max_w)
                    l, t, r, b = bb
                    if l >= 8 and t >= 8 and r <= W - 8 and b <= H - 8:
                        # 真正畫到 overlay
                        self._draw_label_box(draw, text, x, y, font, max_width=max_w)
                        return

                # 都不行就硬放（但 clamp 到邊界）
                x = min(max(8, int(px + offset)), W - max_w - 8)
                y = min(max(8, int(py + offset)), H - 80)
                self._draw_label_box(draw, text, x, y, font, max_width=max_w)

            place_box(ax, ay, a_text, prefer="right")
            place_box(bx, by, b_text, prefer="left")

            img = Image.alpha_composite(img, overlay)

            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            background.save(image_path)
            logger.info("地圖已加註 A/B Marker 旁地址 (Advanced Burn-in + Manual Markers)")

        except Exception as e:
            logger.error(f"標註 A/B Marker 旁地址錯誤: {e}")
            import traceback
            logger.error(traceback.format_exc())

    # 仍保留：舊版只加 km 的功能（如果其他地方還在用）
    def _add_km_text_to_map(self, image_path, km):
        """
        在地圖圖片上加入公里數文字（舊版）
        """
        try:
            img = Image.open(image_path)
            if img.mode != "RGBA":
                img = img.convert("RGBA")

            overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)

            text = f"{km} km"

            font = None
            font_paths = []

            if os.name == "nt":
                windows_font_dir = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts")
                font_paths.extend([
                    os.path.join(windows_font_dir, "msjh.ttc"),
                    os.path.join(windows_font_dir, "simsun.ttc"),
                    os.path.join(windows_font_dir, "arial.ttf"),
                ])
            else:
                linux_font_dirs = [
                    "/usr/share/fonts/truetype/droid",
                    "/usr/share/fonts/truetype/liberation",
                    "/usr/share/fonts/TTF",
                ]
                for font_dir in linux_font_dirs:
                    if os.path.exists(font_dir):
                        font_paths.extend([
                            os.path.join(font_dir, "DroidSansFallbackFull.ttf"),
                            os.path.join(font_dir, "LiberationSans-Regular.ttf"),
                        ])

            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, 36)
                        break
                    except Exception:
                        continue

            if font is None:
                font = ImageFont.load_default()

            x, y = 20, 20
            bbox = draw.textbbox((x, y), text, font=font)
            padding = 10
            draw.rectangle(
                [bbox[0] - padding, bbox[1] - padding, bbox[2] + padding, bbox[3] + padding],
                fill=(255, 255, 255, 200),
            )
            draw.text((x, y), text, fill=(255, 0, 0, 255), font=font)

            img = Image.alpha_composite(img, overlay)

            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background

            img.save(image_path)
            logger.info(f"成功在地圖上添加公里數: {km} km")

        except Exception as e:
            logger.error(f"在地圖上添加公里數錯誤: {str(e)}")
