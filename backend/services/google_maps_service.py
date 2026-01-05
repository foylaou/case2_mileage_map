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
    def _annotate_map_info(self, image_path: str, km, origin_addr: str, dest_addr: str, 
                          origin_lat=None, origin_lng=None, dest_lat=None, dest_lng=None):
        """
        產生「報表型」地圖（推薦）：
        - 原地圖不被遮擋
        - 底部新增白色資訊欄：A/B 地址 + 系統產出時間
        - 左上角顯示 km badge
        - 地圖上顯示中文「起點」和「終點」標記
        """
        try:
            # 確保地址是字串且正確處理
            origin_addr = str(origin_addr) if origin_addr else ""
            dest_addr = str(dest_addr) if dest_addr else ""
            
            # 記錄地址資訊（用於除錯）
            logger.debug(f"標註地圖資訊 - 起點地址: {origin_addr[:50]}...")
            logger.debug(f"標註地圖資訊 - 終點地址: {dest_addr[:50]}...")
            
            base = Image.open(image_path).convert("RGB")
            W, H = base.size

            footer_h = 170  # 底部資訊欄高度（可調：150~220）

            canvas = Image.new("RGB", (W, H + footer_h), (255, 255, 255))
            canvas.paste(base, (0, 0))

            draw = ImageDraw.Draw(canvas)

            def load_font(size: int):
                """載入字體：優先使用專案字體，失敗則嘗試系統中文字體"""
                # 1. 優先：從專案路徑載入字體：backend/fonts/NotoSansCJK-Regular.ttc
                font_path = Path(__file__).parent.parent / "fonts" / "NotoSansCJK-Regular.ttc"
                
                if font_path.exists():
                    try:
                        font = ImageFont.truetype(str(font_path), size)
                        logger.debug(f"成功載入專案字體: {font_path}")
                        return font
                    except Exception as e:
                        logger.warning(f"無法載入專案字體 {font_path}: {str(e)}")
                
                # 2. 回退：嘗試載入系統中文字體
                system_fonts = []
                
                # Windows 系統字體
                if os.name == "nt":
                    windows_font_dir = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
                    system_fonts.extend([
                        windows_font_dir / "msjh.ttc",  # 微軟正黑體
                        windows_font_dir / "msjhbd.ttc",  # 微軟正黑體 Bold
                        windows_font_dir / "simsun.ttc",  # 新細明體
                        windows_font_dir / "mingliu.ttc",  # 細明體
                    ])
                # Linux 系統字體
                else:
                    system_fonts.extend([
                        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
                        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
                        Path("/usr/share/fonts/truetype/arphic/uming.ttc"),
                        Path("/usr/share/fonts/truetype/arphic/ukai.ttc"),
                        Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"),
                    ])
                
                # 嘗試載入系統字體
                for sys_font_path in system_fonts:
                    if sys_font_path.exists():
                        try:
                            font = ImageFont.truetype(str(sys_font_path), size)
                            logger.debug(f"成功載入系統字體: {sys_font_path}")
                            return font
                        except Exception as e:
                            logger.debug(f"無法載入系統字體 {sys_font_path}: {str(e)}")
                            continue
                
                # 3. 最後回退：使用預設字體（可能不支援中文，但至少不會報錯）
                logger.warning("無法載入任何中文字體，使用預設字體（可能無法顯示中文）")
                return ImageFont.load_default()

            font_km = load_font(32)
            font_text = load_font(26)
            font_marker = load_font(24)  # 標記文字字體
            
            # 測試字體是否能正確顯示中文
            test_text = "測試"
            try:
                test_bbox = draw.textbbox((0, 0), test_text, font=font_text)
                logger.debug(f"字體測試成功，可以顯示中文: {test_text}")
            except Exception as e:
                logger.warning(f"字體測試失敗，可能無法顯示中文: {str(e)}")

            def wrap_text(text: str, max_width_px: int, font: ImageFont.ImageFont) -> list[str]:
                text = (text or "").strip()
                if not text:
                    return [""]
                lines = []
                cur = ""
                for ch in text:
                    test = cur + ch
                    bbox = draw.textbbox((0, 0), test, font=font)
                    if (bbox[2] - bbox[0]) <= max_width_px:
                        cur = test
                    else:
                        if cur:
                            lines.append(cur)
                        cur = ch
                if cur:
                    lines.append(cur)
                return lines

            # 1) 左上角 km badge
            if km is not None:
                km_text = f"{km} km"
                x, y = 20, 20
                pad_x, pad_y = 14, 10
                bbox = draw.textbbox((x, y), km_text, font=font_km)
                draw.rectangle(
                    [bbox[0] - pad_x, bbox[1] - pad_y, bbox[2] + pad_x, bbox[3] + pad_y],
                    fill=(255, 255, 255),
                    outline=(220, 220, 220),
                    width=2,
                )
                draw.text((x, y), km_text, fill=(220, 0, 0), font=font_km)

            # 1.5) 在地圖上繪製中文「起點」和「終點」標記
            # 由於無法精確計算經緯度到像素的轉換，我們在標記附近繪製中文文字
            # 假設標記在地圖的左下（起點）和右上（終點）區域
            marker_radius = 15  # 標記圓圈半徑
            
            # 起點標記（左下區域）
            origin_x = int(W * 0.15)  # 左側 15% 位置
            origin_y = int(H * 0.85)  # 下方 85% 位置
            
            # 繪製紅色圓圈
            draw.ellipse(
                [origin_x - marker_radius, origin_y - marker_radius,
                 origin_x + marker_radius, origin_y + marker_radius],
                fill=(255, 0, 0),
                outline=(200, 0, 0),
                width=2
            )
            # 繪製「起」字
            origin_text = "起"
            origin_bbox = draw.textbbox((0, 0), origin_text, font=font_marker)
            origin_text_w = origin_bbox[2] - origin_bbox[0]
            origin_text_h = origin_bbox[3] - origin_bbox[1]
            draw.text(
                (origin_x - origin_text_w // 2, origin_y - origin_text_h // 2),
                origin_text,
                fill=(255, 255, 255),
                font=font_marker
            )
            # 在標記下方繪製「起點」文字
            start_label = "起點"
            start_bbox = draw.textbbox((0, 0), start_label, font=font_marker)
            start_label_w = start_bbox[2] - start_bbox[0]
            draw.rectangle(
                [origin_x - start_label_w // 2 - 6, origin_y + marker_radius + 2,
                 origin_x + start_label_w // 2 + 6, origin_y + marker_radius + 2 + (start_bbox[3] - start_bbox[1]) + 4],
                fill=(255, 255, 255),
                outline=(255, 0, 0),
                width=1
            )
            draw.text(
                (origin_x - start_label_w // 2, origin_y + marker_radius + 4),
                start_label,
                fill=(255, 0, 0),
                font=font_marker
            )
            
            # 終點標記（右上區域）
            dest_x = int(W * 0.85)  # 右側 85% 位置
            dest_y = int(H * 0.15)  # 上方 15% 位置
            
            # 繪製紅色圓圈
            draw.ellipse(
                [dest_x - marker_radius, dest_y - marker_radius,
                 dest_x + marker_radius, dest_y + marker_radius],
                fill=(255, 0, 0),
                outline=(200, 0, 0),
                width=2
            )
            # 繪製「終」字
            dest_text = "終"
            dest_bbox = draw.textbbox((0, 0), dest_text, font=font_marker)
            dest_text_w = dest_bbox[2] - dest_bbox[0]
            dest_text_h = dest_bbox[3] - dest_bbox[1]
            draw.text(
                (dest_x - dest_text_w // 2, dest_y - dest_text_h // 2),
                dest_text,
                fill=(255, 255, 255),
                font=font_marker
            )
            # 在標記下方繪製「終點」文字
            end_label = "終點"
            end_bbox = draw.textbbox((0, 0), end_label, font=font_marker)
            end_label_w = end_bbox[2] - end_bbox[0]
            draw.rectangle(
                [dest_x - end_label_w // 2 - 6, dest_y + marker_radius + 2,
                 dest_x + end_label_w // 2 + 6, dest_y + marker_radius + 2 + (end_bbox[3] - end_bbox[1]) + 4],
                fill=(255, 255, 255),
                outline=(255, 0, 0),
                width=1
            )
            draw.text(
                (dest_x - end_label_w // 2, dest_y + marker_radius + 4),
                end_label,
                fill=(255, 0, 0),
                font=font_marker
            )

            # 2) Footer 區
            footer_top = H
            draw.line([(0, footer_top), (W, footer_top)], fill=(220, 220, 220), width=2)

            left_x = 20
            top_y = footer_top + 20

            right_reserved = 420
            max_width = W - left_x - 20 - right_reserved
            if max_width < 300:
                max_width = W - left_x - 40

            a_label = f"A：{origin_addr}"
            b_label = f"B：{dest_addr}"

            a_lines = wrap_text(a_label, max_width, font_text)
            b_lines = wrap_text(b_label, max_width, font_text)

            sample_bbox = draw.textbbox((0, 0), "測", font=font_text)
            line_h = (sample_bbox[3] - sample_bbox[1]) + 10

            cur_y = top_y
            for line in a_lines:
                draw.text((left_x, cur_y), line, fill=(0, 0, 0), font=font_text)
                cur_y += line_h

            cur_y += 6
            for line in b_lines:
                draw.text((left_x, cur_y), line, fill=(0, 0, 0), font=font_text)
                cur_y += line_h

            gen_time = datetime.now().strftime("%Y/%m/%d %H:%M")
            time_text = f"系統產出時間：{gen_time}"

            tb = draw.textbbox((0, 0), time_text, font=font_text)
            tw = tb[2] - tb[0]
            th = tb[3] - tb[1]

            tx = W - tw - 20
            ty = footer_top + footer_h - th - 20

            pad_x, pad_y = 12, 8
            draw.rectangle(
                [tx - pad_x, ty - pad_y, tx + tw + pad_x, ty + th + pad_y],
                fill=(255, 255, 255),
                outline=(220, 220, 220),
                width=2,
            )
            draw.text((tx, ty), time_text, fill=(0, 0, 0), font=font_text)

            canvas.save(image_path)
            logger.info("地圖已改為 footer 報表樣式（km + A/B 地址 + 系統產出時間）")

        except Exception as e:
            logger.error(f"在地圖上加註資訊錯誤: {str(e)}")


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
            url_parts.append("size=1200x800")
            url_parts.append("maptype=roadmap")
            url_parts.append("format=png")

            # 主路線：只畫線（不使用 fillcolor）
            main_path = f"color:0x4285F4|weight:6|enc:{polyline}"
            url_parts.append(f"path={quote(main_path)}")

            # 替代路線：只畫線（不使用 fillcolor）
            if alternative_polylines:
                for alt_polyline in alternative_polylines:
                    alt_path = f"color:0x808080|weight:4|enc:{alt_polyline}"
                    url_parts.append(f"path={quote(alt_path)}")

            # 不在地圖 API 中加入標記，改為在 _annotate_map_info 中繪製中文標記
            # 這樣可以顯示中文「起點」和「終點」

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

            # 加註：公里數 + A/B 地址（formatted address）+ 系統產出時間 + 中文標記
            # 確保使用正確的中文地址
            origin_display_addr = origin_geo.get("formatted_address") if origin_geo else None
            if not origin_display_addr:
                origin_display_addr = origin_address
            dest_display_addr = destination_geo.get("formatted_address") if destination_geo else None
            if not dest_display_addr:
                dest_display_addr = destination_address
            
            logger.debug(f"標註地圖 - 起點地址: {origin_display_addr[:50] if origin_display_addr else 'None'}...")
            logger.debug(f"標註地圖 - 終點地址: {dest_display_addr[:50] if dest_display_addr else 'None'}...")
            
            self._annotate_map_info(
                str(output_path),
                distance_km,
                origin_display_addr or origin_address,
                dest_display_addr or destination_address,
                origin_geo.get("lat") if origin_geo else None,
                origin_geo.get("lng") if origin_geo else None,
                destination_geo.get("lat") if destination_geo else None,
                destination_geo.get("lng") if destination_geo else None,
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
            
            # 確保使用正確的中文地址
            origin_fmt = origin_geo.get("formatted_address") if origin_geo else None
            if not origin_fmt:
                origin_fmt = origin_address
            dest_fmt = dest_geo.get("formatted_address") if dest_geo else None
            if not dest_fmt:
                dest_fmt = destination_address
            
            logger.debug(f"簡單地圖標註 - 起點地址: {origin_fmt[:50] if origin_fmt else 'None'}...")
            logger.debug(f"簡單地圖標註 - 終點地址: {dest_fmt[:50] if dest_fmt else 'None'}...")

            # 取得座標（如果有的話）
            origin_lat = origin_geo.get("lat") if origin_geo else None
            origin_lng = origin_geo.get("lng") if origin_geo else None
            dest_lat = dest_geo.get("lat") if dest_geo else None
            dest_lng = dest_geo.get("lng") if dest_geo else None

            self._annotate_map_info(
                str(output_path), 
                distance_km, 
                origin_fmt, 
                dest_fmt,
                origin_lat,
                origin_lng,
                dest_lat,
                dest_lng
            )

            logger.info(f"成功下載簡單靜態地圖: {str(output_path)}")
            return str(output_path)

        except Exception as e:
            logger.error(f"下載簡單靜態地圖錯誤: {str(e)}")
            return None

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
