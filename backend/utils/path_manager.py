"""
路徑管理工具
統一管理專案中的路徑，避免硬編碼絕對路徑
支援開發環境和打包後的 exe 環境
"""
import os
import sys
from pathlib import Path
from flask import current_app, has_app_context


def get_base_dir():
    """
    取得專案基礎目錄
    
    Returns:
        Path: 專案基礎目錄路徑
    """
    if getattr(sys, 'frozen', False):
        # 打包後的 exe 環境
        return Path(sys.executable).parent
    else:
        # 開發環境
        return Path(__file__).parent.parent


def get_temp_dir():
    """
    取得暫存目錄
    
    Returns:
        Path: 暫存目錄路徑
    """
    base_dir = get_base_dir()
    temp_dir = base_dir / 'temp'
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def get_temp_maps_dir():
    """
    取得地圖暫存目錄
    
    Returns:
        Path: 地圖暫存目錄路徑
    """
    base_dir = get_base_dir()
    temp_maps_dir = base_dir / 'temp' / 'maps'
    temp_maps_dir.mkdir(parents=True, exist_ok=True)
    return temp_maps_dir


def get_output_dir():
    """
    取得輸出目錄
    
    Returns:
        Path: 輸出目錄路徑
    """
    base_dir = get_base_dir()
    output_dir = base_dir / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_logs_dir():
    """
    取得日誌目錄
    
    Returns:
        Path: 日誌目錄路徑
    """
    base_dir = get_base_dir()
    logs_dir = base_dir / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_relative_path(file_path: str | Path) -> str:
    """
    將絕對路徑轉換為相對路徑（相對於專案根目錄）
    
    Args:
        file_path: 檔案路徑
    
    Returns:
        str: 相對路徑字串
    """
    base_dir = get_base_dir()
    file_path = Path(file_path)
    
    try:
        # 嘗試取得相對路徑
        relative_path = file_path.relative_to(base_dir)
        return str(relative_path).replace('\\', '/')
    except ValueError:
        # 如果無法取得相對路徑，返回檔案名稱
        return file_path.name


