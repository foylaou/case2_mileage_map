"""
Word 報表產生服務
"""
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from datetime import datetime
from loguru import logger
from utils.path_manager import get_output_dir
from pathlib import Path
import os


class WordService:
    """Word 報表產生服務類別"""
    
    def __init__(self):
        self.output_dir = get_output_dir()
    
    def _format_km(self, value):
        """
        格式化公里數（與 mileage_report_demo 一致）
        - 若為整數，顯示整數（例如：19）
        - 否則顯示一位小數（例如：19.1）
        
        Args:
            value: 公里數值（float 或 int）
        
        Returns:
            str: 格式化後的公里數字串
        """
        try:
            # 轉換為 float
            km = float(value) if value is not None else 0.0
            
            # 判斷是否為整數
            if km == int(km):
                return str(int(km))
            else:
                return f"{km:.1f}"
                
        except Exception as e:
            logger.error(f"公里數格式化失敗: {e}")
            return str(value) if value is not None else "0"
    
    def _format_mmdd(self, date_value):
        """
        將日期格式化為 M/D 格式（不含前導 0）
        參考 mileage_report_demo 的格式
        
        Args:
            date_value: datetime 物件或字串
        
        Returns:
            str: M/D 格式的日期字串（例如：7/12、10/22）
        """
        try:
            if isinstance(date_value, datetime):
                dt = date_value
            elif isinstance(date_value, str):
                try:
                    dt = datetime.strptime(date_value, '%Y-%m-%d')
                except ValueError:
                    try:
                        dt = datetime.fromisoformat(date_value)
                    except ValueError:
                        logger.warning(f"無法解析日期字串: {date_value}")
                        return str(date_value)
            else:
                logger.warning(f"不支援的日期類型: {type(date_value)}")
                return str(date_value)
            
            # 格式化為 M/D（不含前導 0）
            month = dt.month
            day = dt.day
            return f"{month}/{day}"
            
        except Exception as e:
            logger.error(f"日期格式化失敗: {e}")
            return str(date_value)
    
    def generate_report(self, project_name, records, fixed_origin=None, page_break_per_record=True):
        """
        產生 Word 報表（與 mileage_report_demo 一致）
        
        Args:
            project_name: 計畫別名稱
            records: 該計畫別的紀錄列表（需包含計算結果）
            fixed_origin: 固定起點地址（可選）
            page_break_per_record: 是否每筆記錄換頁（預設 True，與 mileage_report_demo 一致）
            
        Returns:
            str: Word 檔案路徑
        """
        try:
            # 建立 Word 文件
            doc = Document()
            
            # 依日期排序
            sorted_records = sorted(
                records,
                key=lambda x: x.get('出差日期時間（開始）', datetime.min),
                reverse=False
            )
            
            # 處理每筆紀錄
            for idx, record in enumerate(sorted_records):
                try:
                    logger.info(f"處理第 {idx + 1}/{len(sorted_records)} 筆記錄")
                    
                    # 第二筆開始換頁（與 mileage_report_demo 一致）
                    if idx > 0:
                        doc.add_page_break()
                    
                    # 取得資料
                    travel_date = record.get('出差日期時間（開始）')
                    date_str = self._format_mmdd(travel_date)
                    
                    # 起點和終點
                    origin_name = record.get('起點名稱', '')
                    destination_name = record.get('目的地名稱', '')
                    
                    # 使用固定起點或原始起點
                    if fixed_origin:
                        origin_display = fixed_origin
                    else:
                        origin_display = origin_name
                    
                    # 取得完整地址（用於標題，包含郵遞區號）
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
                    km_str = self._format_km(round_trip_km)
                    
                    # 建立標題 - 格式：7/12804 高雄市鼓山區裕誠路1091號至832 高雄市林園區石化二路10號往返,核銷62公里。
                    # 根據圖片，標題應包含完整地址（含郵遞區號）
                    title_text = f"{date_str}{origin_address}至{destination_address}往返,核銷{km_str}公里。"
                    
                    logger.debug(f"  標題: {title_text}")
                    
                    # 加入標題段落
                    title_paragraph = doc.add_paragraph(title_text)
                    title_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    
                    # 設定標題格式（加粗、字體大小 18pt，與 mileage_report_demo 一致）
                    for run in title_paragraph.runs:
                        run.bold = True
                        run.font.size = Pt(18)
                    
                    # 插入 Google Maps 路線截圖（完整截圖，包含左側面板和右側地圖）
                    map_image_path = record.get('StaticMapImage')
                    if map_image_path and os.path.exists(map_image_path):
                        try:
                            logger.debug(f"  插入圖片: {map_image_path}")
                            picture_paragraph = doc.add_paragraph()
                            picture_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            run = picture_paragraph.add_run()
                            # 使用 6.5 英吋寬度（與 mileage_report_demo 一致）
                            run.add_picture(map_image_path, width=Inches(6.5))
                        except Exception as e:
                            logger.error(f"  插入圖片失敗: {e}")
                            # 插入錯誤提示文字
                            error_paragraph = doc.add_paragraph()
                            error_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            error_run = error_paragraph.add_run("本筆地圖截圖失敗")
                            error_run.font.size = Pt(14)
                    else:
                        logger.warning(f"  沒有地圖圖片: {map_image_path}")
                        # 插入錯誤提示文字
                        error_paragraph = doc.add_paragraph()
                        error_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        error_run = error_paragraph.add_run("本筆地圖截圖失敗")
                        error_run.font.size = Pt(14)
                
                except Exception as e:
                    logger.error(f"處理第 {idx + 1} 筆記錄時發生錯誤: {e}")
                    # 繼續處理下一筆
                    continue
            
            # 儲存檔案
            safe_project_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"{safe_project_name}_里程報表.docx"
            file_path = self.output_dir / filename
            
            try:
                doc.save(str(file_path))
                logger.info(f"報表已儲存: {str(file_path)}")
                return str(file_path)
            except Exception as e:
                logger.error(f"儲存報表失敗: {e}")
                raise
            
        except Exception as e:
            logger.error(f"產生 Word 報表錯誤: {str(e)}")
            raise
    
# 移除不需要的方法（與 mileage_report_demo 一致，不使用表格）








