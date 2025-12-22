"""
Google Maps 風格模板服務
用於生成模擬 Google Maps 介面的 HTML 或圖片檔案
"""
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
import os
from datetime import datetime


def generate_google_maps_style_html(
    record: Dict[str, Any],
    output_path: Optional[str | Path] = None,
    fixed_origin: Optional[str] = None
) -> str:
    """
    生成 Google Maps 風格的 HTML 檔案
    
    Args:
        record: 包含行程資訊的記錄字典
        output_path: 輸出 HTML 檔案路徑（可選）
        fixed_origin: 固定起點地址（可選）
    
    Returns:
        str: HTML 檔案路徑
    """
    try:
        # 取得資料
        travel_date = record.get('出差日期時間（開始）')
        if isinstance(travel_date, datetime):
            date_str = travel_date.strftime('%m/%d')
        elif isinstance(travel_date, str):
            try:
                date_obj = datetime.strptime(travel_date, '%Y-%m-%d')
                date_str = date_obj.strftime('%m/%d')
            except:
                date_str = str(travel_date)
        else:
            date_str = str(travel_date)
        
        # 起點和終點
        origin_name = record.get('起點名稱', '')
        destination_name = record.get('目的地名稱', '')
        
        # 使用固定起點或原始起點
        if fixed_origin:
            origin_display = fixed_origin
        else:
            origin_display = origin_name
        
        # 取得完整地址
        origin_address = (
            record.get('OriginAddress') or 
            record.get('起點地址') or 
            record.get('origin_address') or
            origin_display
        )
        destination_address = (
            record.get('DestinationAddress') or 
            record.get('終點地址') or 
            record.get('destination_address') or
            destination_name
        )
        
        # 往返公里數
        round_trip_km = record.get('RoundTripKm', 0)
        if round_trip_km is None:
            round_trip_km = 0
        
        # 格式化公里數
        if isinstance(round_trip_km, float):
            if round_trip_km == int(round_trip_km):
                round_trip_km_display = str(int(round_trip_km))
            else:
                round_trip_km_display = f"{round(round_trip_km, 1):.1f}"
        else:
            if round_trip_km == int(round_trip_km):
                round_trip_km_display = str(int(round_trip_km))
            else:
                round_trip_km_display = str(round_trip_km)
        
        # 取得時間
        duration_text = record.get('DurationText') or record.get('EstimatedTime') or ''
        
        # 地圖圖片路徑
        map_image_path = record.get('StaticMapImage', '')
        map_image_url = ''
        if map_image_path and os.path.exists(map_image_path):
            # 轉換為相對路徑或絕對路徑 URL
            map_image_url = f"file:///{os.path.abspath(map_image_path).replace(os.sep, '/')}"
        
        # 生成 HTML
        html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>行程詳情 - {date_str}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Microsoft JhengHei', '微軟正黑體', Arial, sans-serif;
            background-color: #f5f5f5;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .title-bar {{
            background-color: white;
            padding: 16px 24px;
            border-bottom: 1px solid #e0e0e0;
            font-size: 16px;
            font-weight: 500;
            color: #202124;
        }}
        
        .main-layout {{
            display: flex;
            height: calc(100vh - 60px);
            min-height: 600px;
        }}
        
        .left-panel {{
            width: 400px;
            background-color: white;
            border-right: 1px solid #e0e0e0;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }}
        
        .route-inputs {{
            padding: 16px;
            border-bottom: 1px solid #f0f0f0;
        }}
        
        .route-input {{
            display: flex;
            align-items: flex-start;
            margin-bottom: 8px;
            padding: 12px;
            background-color: #f8f9fa;
            border-radius: 4px;
            font-size: 14px;
            color: #202124;
            border: 1px solid #e0e0e0;
        }}
        
        .route-input:last-child {{
            margin-bottom: 0;
        }}
        
        .route-input .icon {{
            width: 20px;
            height: 20px;
            margin-right: 12px;
            margin-top: 2px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            flex-shrink: 0;
        }}
        
        .route-input.origin .icon {{
            color: #4285f4;
        }}
        
        .route-input.destination .icon {{
            color: #ea4335;
        }}
        
        .route-input.waypoint .icon {{
            color: #fbbc04;
        }}
        
        .route-input .address {{
            flex: 1;
            word-break: break-word;
        }}
        
        .route-summary {{
            padding: 16px;
            margin-top: auto;
            border-top: 1px solid #f0f0f0;
            background-color: #fafafa;
        }}
        
        .summary-item {{
            display: flex;
            align-items: center;
            margin-bottom: 8px;
            font-size: 14px;
            color: #5f6368;
        }}
        
        .summary-item:last-child {{
            margin-bottom: 0;
        }}
        
        .summary-item .icon {{
            width: 20px;
            height: 20px;
            margin-right: 8px;
        }}
        
        .summary-stats {{
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid #e0e0e0;
            font-size: 16px;
            font-weight: 500;
            color: #202124;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
        }}
        
        .summary-stats .time {{
            color: #5f6368;
            margin-right: 12px;
        }}
        
        .summary-stats .separator {{
            color: #5f6368;
            margin: 0 8px;
        }}
        
        .summary-stats .distance {{
            color: #202124;
        }}
        
        .map-container {{
            flex: 1;
            position: relative;
            background-color: #e5e5e5;
            overflow: hidden;
        }}
        
        .map-image {{
            width: 100%;
            height: 100%;
            object-fit: contain;
            background-color: #e5e5e5;
        }}
        
        .map-overlay {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            background-color: white;
            padding: 10px 14px;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            font-size: 13px;
            color: #202124;
            line-height: 1.4;
        }}
        
        .map-overlay .time {{
            color: #5f6368;
            margin-bottom: 2px;
            font-size: 12px;
        }}
        
        .map-overlay .distance {{
            font-weight: 500;
            color: #202124;
            font-size: 13px;
        }}
        
        @media print {{
            .container {{
                box-shadow: none;
            }}
            
            .main-layout {{
                height: auto;
                min-height: 600px;
            }}
            
            .left-panel {{
                overflow: visible;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 標題列 -->
        <div class="title-bar">
            {date_str}{origin_display}至{destination_name}往返，核銷{round_trip_km_display}公里。
        </div>
        
        <!-- 主佈局：左側資訊欄 + 右側地圖 -->
        <div class="main-layout">
            <!-- 左側資訊欄 -->
            <div class="left-panel">
                <div class="route-inputs">
                    <div class="route-input origin">
                        <div class="icon">●</div>
                        <div class="address">{origin_address}</div>
                    </div>
                    <div class="route-input destination">
                        <div class="icon">●</div>
                        <div class="address">{destination_address}</div>
                    </div>
                    <div class="route-input waypoint">
                        <div class="icon">●</div>
                        <div class="address">{origin_address}</div>
                    </div>
                </div>
                
                <div class="route-summary">
                    <div class="summary-item">
                        <div class="icon">🚗</div>
                        <div>途經國道一號</div>
                    </div>
                    <div class="summary-stats">
                        {f'<span class="time">{duration_text}</span><span class="separator">/</span>' if duration_text else ''}
                        <span class="distance">{round_trip_km_display} 公里</span>
                    </div>
                </div>
            </div>
            
            <!-- 右側地圖 -->
            <div class="map-container">
                {f'<img src="{map_image_url}" alt="地圖路線" class="map-image">' if map_image_url else '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #5f6368;">無地圖圖片</div>'}
                <div class="map-overlay">
                    {f'<div class="time">{duration_text}</div>' if duration_text else ''}
                    <div class="distance">{round_trip_km_display} 公里</div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""
        
        # 決定輸出路徑
        if output_path is None:
            output_dir = Path('output')
            output_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = output_dir / f"google_maps_style_{timestamp}.html"
        else:
            output_path = Path(output_path)
        
        # 確保輸出目錄存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 儲存 HTML 檔案
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"成功生成 Google Maps 風格 HTML: {output_path}")
        
        return str(output_path)
        
    except Exception as e:
        logger.error(f"生成 Google Maps 風格 HTML 失敗: {str(e)}")
        raise

