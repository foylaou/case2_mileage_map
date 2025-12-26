"""
Excel 處理服務
"""
import pandas as pd
import openpyxl
from openpyxl import load_workbook
from datetime import datetime
from loguru import logger
from utils.path_manager import get_output_dir
from pathlib import Path
import os


class ExcelService:
    """Excel 處理服務類別"""
    
    def __init__(self):
        self.required_columns = [
            '部門', '姓名', '計畫別', '起點名稱', '出差日期時間（開始）',
            '出差日期時間（結束）', '目的地名稱'
        ]
        # IsDriving 不從 Excel 讀取，由前端上傳後設定
    
    def _get_sort_key(self, date_value):
        """
        取得排序鍵值，處理 NaT 和 None
        
        Args:
            date_value: 日期時間值（可能是 datetime, str, None, NaT）
            
        Returns:
            datetime: 用於排序的日期時間物件
        """
        if date_value is None:
            return datetime.min
        
        # 如果是字串，嘗試轉換
        if isinstance(date_value, str):
            try:
                return pd.to_datetime(date_value)
            except:
                return datetime.min
        
        # 如果是 pandas Timestamp
        if isinstance(date_value, pd.Timestamp):
            if pd.isna(date_value):
                return datetime.min
            return date_value.to_pydatetime()
        
        # 如果是 datetime 物件
        if isinstance(date_value, datetime):
            return date_value
        
        return datetime.min
    
    def parse_excel(self, file_path):
        """
        解析 Excel 檔案
        
        Args:
            file_path: Excel 檔案路徑
            
        Returns:
            dict: 包含解析結果和資料
        """
        try:
            logger.info(f"開始讀取 Excel 檔案: {file_path}")
            # 讀取 Excel
            df = pd.read_excel(file_path, engine='openpyxl')
            logger.info(f"Excel 檔案讀取完成，共 {len(df)} 行, {len(df.columns)} 欄")
            
            # 標準化欄位名稱（支援中英文）
            # 注意：IsDriving 和「是否自駕」不從 Excel 讀取，會被移除
            column_mapping = {
                '部門': '部門',
                '姓名': '姓名',
                '計畫別': '計畫別',
                'ProjectName': '計畫別',
                '起點名稱': '起點名稱',
                '出差日期時間（開始）': '出差日期時間（開始）',
                '出差日期時間（結束）': '出差日期時間（結束）',
                '目的地名稱': '目的地名稱'
            }
            
            # 重新命名欄位
            df = df.rename(columns=column_mapping)
            
            # 檢查必要欄位
            missing_columns = []
            for col in self.required_columns:
                if col not in df.columns:
                    missing_columns.append(col)
            
            if missing_columns:
                return {
                    'success': False,
                    'error': f'缺少必要欄位: {", ".join(missing_columns)}',
                    'data': None
                }
            
            # 處理日期時間欄位
            if '出差日期時間（開始）' in df.columns:
                df['出差日期時間（開始）'] = pd.to_datetime(
                    df['出差日期時間（開始）'], errors='coerce'
                )
            if '出差日期時間（結束）' in df.columns:
                df['出差日期時間（結束）'] = pd.to_datetime(
                    df['出差日期時間（結束）'], errors='coerce'
                )
            
            # IsDriving 不從 Excel 讀取，一律預設為 'N'（由前端上傳後由使用者勾選）
            # 如果 Excel 中有 IsDriving 欄位，忽略它
            if 'IsDriving' in df.columns:
                df = df.drop(columns=['IsDriving'])
            if '是否自駕' in df.columns:
                df = df.drop(columns=['是否自駕'])
            
            # 一律設定為 'N'（預設非自駕）
            df['IsDriving'] = 'N'
            
            # 新增計算結果欄位（初始為空）
            df['OneWayKm'] = None
            df['RoundTripKm'] = None
            df['GoogleMapUrl'] = None
            df['StaticMapImage'] = None
            df['StepCount'] = None
            df['Polyline'] = None
            df['RouteSteps'] = None
            
            # 轉換為字典列表，並處理 NaT 值
            records = []
            for _, row in df.iterrows():
                record = {}
                for col in df.columns:
                    value = row[col]
                    # 處理 NaT (Not a Time) 值
                    if pd.isna(value):
                        record[col] = None
                    # 處理 datetime 物件，轉換為字串或 None
                    elif isinstance(value, pd.Timestamp):
                        if pd.isna(value):
                            record[col] = None
                        else:
                            record[col] = value.isoformat()
                    else:
                        record[col] = value
                records.append(record)
            
            logger.info(f"成功解析 Excel 檔案: {len(records)} 筆資料")
            
            return {
                'success': True,
                'data': records,
                'total_count': len(records)
            }
            
        except Exception as e:
            logger.error(f"解析 Excel 檔案錯誤: {str(e)}")
            return {
                'success': False,
                'error': f'解析 Excel 檔案失敗: {str(e)}',
                'data': None
            }
    
    def group_by_project(self, records):
        """
        依計畫別分組
        
        Args:
            records: 資料列表
            
        Returns:
            dict: 以計畫別為 key 的分組資料
        """
        try:
            grouped = {}
            
            for record in records:
                project_name = record.get('計畫別', '未分類')
                
                if project_name not in grouped:
                    grouped[project_name] = []
                
                grouped[project_name].append(record)
            
            # 每個計畫別內部依出差日期排序
            for project_name in grouped:
                grouped[project_name].sort(
                    key=lambda x: self._get_sort_key(x.get('出差日期時間（開始）')),
                    reverse=False
                )
            
            logger.info(f"成功分組: {len(grouped)} 個計畫別")
            
            return grouped
            
        except Exception as e:
            logger.error(f"分組錯誤: {str(e)}")
            return {}
    
    def add_calculation_results(self, file_path, records):
        """
        將計算結果寫回 Excel
        
        Args:
            file_path: 原始 Excel 檔案路徑
            records: 包含計算結果的資料列表
            
        Returns:
            str: 更新後的 Excel 檔案路徑
        """
        try:
            # 讀取原始 Excel
            wb = load_workbook(file_path)
            ws = wb.active
            
            # 找到欄位索引
            headers = [cell.value for cell in ws[1]]
            
            # 新增欄位（如果不存在）
            new_columns = ['OneWayKm', 'RoundTripKm', 'GoogleMapUrl', 'StaticMapImage', 'IsDriving', 'StepCount', 'Polyline', 'RouteSteps']
            for col in new_columns:
                if col not in headers:
                    headers.append(col)
                    ws.cell(row=1, column=len(headers), value=col)
            
            # 建立欄位索引對應
            col_index = {col: idx + 1 for idx, col in enumerate(headers)}
            
            # 更新資料
            for idx, record in enumerate(records, start=2):
                if 'OneWayKm' in record and record['OneWayKm'] is not None:
                    ws.cell(row=idx, column=col_index['OneWayKm'], value=record['OneWayKm'])
                if 'RoundTripKm' in record and record['RoundTripKm'] is not None:
                    ws.cell(row=idx, column=col_index['RoundTripKm'], value=record['RoundTripKm'])
                if 'GoogleMapUrl' in record and record['GoogleMapUrl']:
                    ws.cell(row=idx, column=col_index['GoogleMapUrl'], value=record['GoogleMapUrl'])
                if 'StaticMapImage' in record and record['StaticMapImage']:
                    ws.cell(row=idx, column=col_index['StaticMapImage'], value=record['StaticMapImage'])
                if 'IsDriving' in record:
                    ws.cell(row=idx, column=col_index['IsDriving'], value=record['IsDriving'])
                if 'StepCount' in record and record['StepCount'] is not None:
                    ws.cell(row=idx, column=col_index['StepCount'], value=record['StepCount'])
                if 'Polyline' in record and record['Polyline']:
                    ws.cell(row=idx, column=col_index['Polyline'], value=record['Polyline'])
                if 'RouteSteps' in record and record['RouteSteps']:
                    ws.cell(row=idx, column=col_index['RouteSteps'], value=record['RouteSteps'])
            
            # 儲存更新後的檔案
            output_dir = get_output_dir()
            
            output_filename = f"updated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            output_path = output_dir / output_filename
            
            wb.save(str(output_path))
            logger.info(f"成功更新 Excel 檔案: {str(output_path)}")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"更新 Excel 檔案錯誤: {str(e)}")
            raise


