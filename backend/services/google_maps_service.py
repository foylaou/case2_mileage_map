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
    def _annotate_map_info(self, image_path: str, km, origin_addr: str, dest_addr: str):
        """
        在地圖圖片上加註：
        - 左上：公里數（可選）
        - 左下：A: 起點地址、B: 終點地址（formatted address）
        - 右下：系統產出時間：YYYY/MM/DD HH:MM
        """
        try:
            img = Image.open(image_path)
            if img.mode != "RGBA":
                img = img.convert("RGBA")

            overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)

            # ---- 字體（跨平台找字型）----
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
                for d in linux_font_dirs:
                    if os.path.exists(d):
                        font_paths.extend([
                            os.path.join(d, "DroidSansFallbackFull.ttf"),
                            os.path.join(d, "LiberationSans-Regular.ttf"),
                        ])

            for fp in font_paths:
                if os.path.exists(fp):
                    try:
                        font = ImageFont.truetype(fp, 28)  # 地址較長，稍小避免爆版
                        break
                    except Exception:
                        continue

            if font is None:
                font = ImageFont.load_default()

            def wrap_text(text: str, max_width_px: int) -> list[str]:
                text = (text or "").strip()
                if not text:
                    return [""]
                lines = []
                current = ""
                for ch in text:
                    test = current + ch
                    bbox = draw.textbbox((0, 0), test, font=font)
                    if (bbox[2] - bbox[0]) <= max_width_px:
                        current = test
                    else:
                        if current:
                            lines.append(current)
                        current = ch
                if current:
                    lines.append(current)
                return lines

            W, H = img.size
            padding = 12

            # 左上：公里數
            if km is not None:
                km_text = f"{km} km"
                x, y = 20, 20
                bbox = draw.textbbox((x, y), km_text, font=font)
                draw.rectangle(
                    [bbox[0] - padding, bbox[1] - padding, bbox[2] + padding, bbox[3] + padding],
                    fill=(255, 255, 255, 210),
                )
                draw.text((x, y), km_text, fill=(220, 0, 0, 255), font=font)

            # 左下：A/B 地址
            max_text_width = int(W * 0.72)
            a_label = f"A：{origin_addr}"
            b_label = f"B：{dest_addr}"

            a_lines = wrap_text(a_label, max_text_width)
            b_lines = wrap_text(b_label, max_text_width)
            lines = a_lines + b_lines

            line_h = (draw.textbbox((0, 0), "測", font=font)[3] + 8)
            block_h = line_h * len(lines) + padding * 2

            start_x = 20
            start_y = H - block_h - 20

            draw.rectangle(
                [start_x - padding, start_y - padding, start_x + max_text_width + padding, start_y + block_h],
                fill=(255, 255, 255, 210),
            )

            cur_y = start_y
            for line in lines:
                draw.text((start_x, cur_y), line, fill=(0, 0, 0, 255), font=font)
                cur_y += line_h

            # 右下：系統產出時間
            gen_time = datetime.now().strftime("%Y/%m/%d %H:%M")
            time_text = f"系統產出時間：{gen_time}"

            tb = draw.textbbox((0, 0), time_text, font=font)
            tw = tb[2] - tb[0]
            th = tb[3] - tb[1]

            tx = W - tw - 20
            ty = H - th - 20

            draw.rectangle(
                [tx - padding, ty - padding, tx + tw + padding, ty + th + padding],
                fill=(255, 255, 255, 210),
            )
            draw.text((tx, ty), time_text, fill=(0, 0, 0, 255), font=font)

            # 合成
            img = Image.alpha_composite(img, overlay)

            # 存成 RGB（避免透明通道造成顯示差異）
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            background.save(image_path)

            logger.info("成功在地圖上加註公里數、A/B 地址與系統產出時間")

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

            origin_marker = f"color:0xFF0000|label:A|{origin_geo['lat']},{origin_geo['lng']}"
            url_parts.append(f"markers={quote(origin_marker)}")

            destination_marker = f"color:0x00FF00|label:B|{destination_geo['lat']},{destination_geo['lng']}"
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
            self._annotate_map_info(
                str(output_path),
                distance_km,
                origin_geo.get("formatted_address", origin_address),
                destination_geo.get("formatted_address", destination_address),
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

            self._annotate_map_info(str(output_path), distance_km, origin_fmt, dest_fmt)

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
