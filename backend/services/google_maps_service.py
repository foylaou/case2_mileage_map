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
    def _load_cjk_font(self, size: int) -> ImageFont.ImageFont:
        """
        載入 CJK（中日韓）字型，固定從 backend/assets/fonts/ 讀取
        
        Args:
            size: 字型大小
            
        Returns:
            ImageFont.ImageFont: 載入的字型物件
            
        Raises:
            FileNotFoundError: 如果字型檔案不存在
            OSError: 如果無法載入字型檔案
        """
        # 固定從 backend/assets/fonts/ 讀取字型檔
        assets_fonts_dir = Path(__file__).parent.parent / "assets" / "fonts"
        
        # 嘗試載入的字型檔名稱（按優先順序）
        font_names = [
            "NotoSansCJKtc-Regular.otf",  # 繁體中文（推薦）
            "NotoSansCJK-Regular.ttc",     # CJK 通用
            "NotoSansCJKsc-Regular.otf",   # 簡體中文
            "NotoSansCJKjp-Regular.otf",   # 日文
        ]
        
        for font_name in font_names:
            font_path = assets_fonts_dir / font_name
            if font_path.exists():
                try:
                    font = ImageFont.truetype(str(font_path), size)
                    logger.info(f"✓ 成功載入專案字型: {font_path} (大小: {size})")
                    return font
                except Exception as e:
                    logger.warning(f"✗ 無法載入字型 {font_path}: {str(e)}")
                    continue
        
        # 如果專案內字型都無法載入，嘗試使用系統字型 (Windows)
        if os.name == "nt":
            windows_font_dir = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
            system_fonts = [
                "msjh.ttc",     # 微軟正黑體
                "msjhbd.ttc",   # 微軟正黑體 粗體
                "simsun.ttc",   # 新細明體
                "mingliu.ttc",  # 細明體
                "arial.ttf",    # Arial (英文 fallback)
            ]
            
            for font_name in system_fonts:
                font_path = windows_font_dir / font_name
                if font_path.exists():
                    try:
                        font = ImageFont.truetype(str(font_path), size)
                        logger.info(f"✓ 使用系統字型: {font_path} (大小: {size})")
                        return font
                    except Exception as e:
                        continue

        # 如果所有字型都無法載入，拋出錯誤
        error_msg = (
            f"無法載入任何 CJK 字型檔案。請確認字型檔案存在於 {assets_fonts_dir}\n"
            f"或是 Windows 系統字型 (msjh.ttc)"
        )
        logger.error(f"⚠ {error_msg}")
        raise FileNotFoundError(error_msg)

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
            
            # --- 樣式設定 ---
            # 1. Header 區域
            header_font_size = int(32 * scale)  # 標題字大一點
            padding_base = int(20 * scale)
            header_padding_y = int(35 * scale)
            
            # 準備文字
            # 格式：10/22 高雄市...至 高雄市...往返,核銷 19.1 公里。
            rt_km = round_trip_km if round_trip_km is not None else (distance_km * 2 if distance_km else 0)
            header_text = f"{date_str} {origin_addr}至 {dest_addr}往返，核銷 {rt_km} 公里。"
            
            # 載入字型
            try:
                font_header = self._load_cjk_font(header_font_size)
                # Badge 字型 (大, 紅色)
                font_badge_num = self._load_cjk_font(int(48 * scale))
                font_badge_unit = self._load_cjk_font(int(32 * scale))
            except FileNotFoundError:
                logger.warning("無法載入 CJK 字型，使用預設字型")
                font_header = ImageFont.load_default()
                font_badge_num = ImageFont.load_default()
                font_badge_unit = ImageFont.load_default()

            # 計算 Header 高度
            temp_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
            bbox = temp_draw.textbbox((0, 0), header_text, font=font_header)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            
            # 給予足夠的 Header 高度
            header_h = int(text_h + (header_padding_y * 1.5))
            
            # 建立新畫布
            canvas = Image.new("RGB", (W, H + header_h), (255, 255, 255))
            
            # 繪製 Header 文字
            draw = ImageDraw.Draw(canvas)
            # 靠左，留點邊距
            draw.text((padding_base, header_padding_y // 2), header_text, fill=(0, 0, 0), font=font_header)
            
            # 貼上地圖 (在 Header 下方)
            canvas.paste(base, (0, header_h))
            
            # --- Badge 設定 (單程公里數) ---
            # 位置：地圖左上角 (Header下方 + padding)
            if distance_km is not None:
                badge_text_num = f"{distance_km}"
                badge_text_unit = "km"
                
                # 計算 Badge 大小
                bbox_num = draw.textbbox((0, 0), badge_text_num, font=font_badge_num)
                bbox_unit = draw.textbbox((0, 0), badge_text_unit, font=font_badge_unit)
                
                # Badge 內容寬度
                num_w = bbox_num[2] - bbox_num[0]
                unit_w = bbox_unit[2] - bbox_unit[0]
                total_text_w = num_w + int(10 * scale) + unit_w
                total_text_h = max(bbox_num[3]-bbox_num[1], bbox_unit[3]-bbox_unit[1])
                
                badge_w = total_text_w + int(40 * scale) # 左右 padding
                badge_h = total_text_h + int(20 * scale) # 上下 padding
                
                badge_x = padding_base
                badge_y = header_h + padding_base # 地圖區塊的左上角
                
                # 繪製 Badge 背景 (白底)
                draw.rectangle(
                    [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
                    fill=(255, 255, 255),
                    outline=None
                )
                
                # 繪製 Badge 文字 (紅字)
                # 數字
                curr_x = badge_x + int(20 * scale)
                # 垂直置中 (概略)
                num_y = badge_y + (badge_h - (bbox_num[3]-bbox_num[1])) // 2 - int(4*scale)
                draw.text((curr_x, num_y), badge_text_num, fill=(255, 0, 0), font=font_badge_num)
                
                # 單位
                curr_x += num_w + int(10 * scale)
                unit_y = badge_y + (badge_h - (bbox_unit[3]-bbox_unit[1])) // 2
                draw.text((curr_x, unit_y), badge_text_unit, fill=(255, 0, 0), font=font_badge_unit)

            # 存檔
            canvas.save(image_path)
            logger.info("地圖已套用 Header 樣式（日期/路徑核銷資訊 + 紅色 KM Badge）")

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
            self.annotate_map_info(
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

            self.annotate_map_info(str(output_path), distance_km, origin_fmt, dest_fmt)

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
