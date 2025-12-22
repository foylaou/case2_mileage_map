"""
地圖圖片疊加服務
用於在地圖圖片上疊加距離和時間資訊框
"""
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from loguru import logger
import os


def add_distance_overlay(
    image_path: str | Path,
    distance_km: float,
    duration_text: Optional[str] = None,
    output_path: Optional[str | Path] = None,
) -> str:
    """
    讀取一張地圖圖片，在左下角畫一個白色資訊框，顯示距離（跟可選的時間），
    回傳處理後圖片的路徑（如果 output_path 為 None，可以覆寫原檔或在檔名後面加 _overlay）。
    
    Args:
        image_path: 原始地圖圖片路徑
        distance_km: 距離（公里）
        duration_text: 時間文字（可選），例如 "1 小時 21 分"
        output_path: 輸出圖片路徑（可選），如果為 None 則在原檔名後加 _overlay
    
    Returns:
        str: 處理後圖片的路徑
    """
    try:
        # 轉換為 Path 物件
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"圖片檔案不存在: {image_path}")
        
        # 讀取原始圖片
        img = Image.open(image_path)
        # 轉換為 RGBA 模式以支援半透明效果
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 創建一個臨時的 RGB 圖片用於繪製（因為 ImageDraw 在 RGBA 模式下繪製半透明有問題）
        img_rgb = img.convert('RGB')
        draw = ImageDraw.Draw(img_rgb)
        
        # 格式化距離文字
        distance_text = _format_distance(distance_km)
        
        # 準備要顯示的文字
        lines = []
        if duration_text:
            lines.append(duration_text)
        lines.append(f"{distance_text} 公里")
        
        # 計算文字大小和框的大小
        # 使用較大的字體，類似 Google Maps 的風格
        try:
            # 嘗試使用系統字體（Windows）
            font_size = 24
            font_paths = [
                "C:/Windows/Fonts/msjh.ttc",  # 微軟正黑體
                "C:/Windows/Fonts/simsun.ttc",  # 新細明體
                "C:/Windows/Fonts/arial.ttf",  # Arial
            ]
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, font_size)
                        break
                    except:
                        continue
            
            # 如果找不到字體，使用預設字體
            if font is None:
                font = ImageFont.load_default()
                logger.warning("使用預設字體，可能顯示效果不佳")
        except Exception as e:
            logger.warning(f"載入字體失敗，使用預設字體: {e}")
            font = ImageFont.load_default()
        
        # 計算每行文字的大小
        line_heights = []
        line_widths = []
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_widths.append(bbox[2] - bbox[0])
            line_heights.append(bbox[3] - bbox[1])
        
        # 框的尺寸
        padding = 12  # 內邊距
        line_spacing = 6  # 行距
        max_width = max(line_widths) + padding * 2
        total_height = sum(line_heights) + padding * 2 + line_spacing * (len(lines) - 1)
        
        # 框的位置（左下角，留一些邊距）
        margin = 20  # 距離邊緣的距離
        box_x = margin
        box_y = img.height - total_height - margin
        
        # 繪製白色背景框（帶圓角和陰影效果）
        # 先畫陰影（稍微偏移的灰色矩形，使用較淺的灰色）
        shadow_offset = 3
        shadow_rect = [
            box_x + shadow_offset,
            box_y + shadow_offset,
            box_x + max_width + shadow_offset,
            box_y + total_height + shadow_offset
        ]
        draw.rectangle(shadow_rect, fill=(180, 180, 180))  # 灰色陰影
        
        # 畫白色主框
        box_rect = [
            box_x,
            box_y,
            box_x + max_width,
            box_y + total_height
        ]
        draw.rectangle(box_rect, fill=(255, 255, 255), outline=(200, 200, 200), width=2)
        
        # 繪製文字
        current_y = box_y + padding
        for i, line in enumerate(lines):
            # 計算文字位置（置中對齊）
            line_width = line_widths[i]
            text_x = box_x + (max_width - line_width) // 2
            
            # 使用 textbbox 來正確定位文字（考慮字體的 baseline）
            bbox = draw.textbbox((text_x, current_y), line, font=font)
            # 調整 Y 位置，確保文字不會被切到
            text_y = current_y - bbox[1] if bbox[1] < 0 else current_y
            
            # 繪製文字（黑色）
            draw.text((text_x, text_y), line, fill=(0, 0, 0), font=font)
            
            # 更新下一行的 Y 位置
            current_y += line_heights[i] + line_spacing
        
        # 決定輸出路徑
        if output_path is None:
            # 在原檔名後加 _overlay
            output_path = image_path.parent / f"{image_path.stem}_overlay{image_path.suffix}"
        else:
            output_path = Path(output_path)
        
        # 確保輸出目錄存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 儲存處理後的圖片（轉回 RGB 模式）
        img_rgb.save(output_path, quality=95)
        logger.info(f"成功在地圖圖片上疊加資訊框: {output_path}")
        
        return str(output_path)
        
    except Exception as e:
        logger.error(f"疊加地圖資訊框失敗: {str(e)}")
        raise


def _format_distance(distance_km: float) -> str:
    """
    格式化距離，與 WordService 中的格式一致
    
    Args:
        distance_km: 距離（公里）
    
    Returns:
        str: 格式化後的距離文字
    """
    if distance_km is None:
        return "0"
    
    # 如果是整數，顯示整數；如果有小數，顯示一位小數
    if isinstance(distance_km, float):
        if distance_km == int(distance_km):
            return str(int(distance_km))
        else:
            return f"{round(distance_km, 1):.1f}"
    else:
        if distance_km == int(distance_km):
            return str(int(distance_km))
        else:
            return str(distance_km)

