"""
日誌清理工具
用於防止日誌注入攻擊（CVE-2024-1681: Improper Output Neutralization for Logs）
"""
import re


def sanitize_log_input(text: str, max_length: int = 200) -> str:
    """
    清理使用者輸入，防止日誌注入攻擊
    
    Args:
        text: 要清理的文字
        max_length: 最大長度限制
    
    Returns:
        清理後的安全文字
    """
    if not text:
        return ""
    
    # 轉換為字串
    text = str(text)
    
    # 限制長度
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    # 移除或替換危險字元（CR/LF 等控制字元）
    # 移除換行符號和回車符號
    text = re.sub(r'[\r\n]', ' ', text)
    
    # 移除其他控制字元（ASCII 0-31，除了常見的空白字元）
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    
    # 移除可能用於注入的特殊字元序列
    # 例如：%n, %r, %t 等格式化字元（如果日誌系統使用格式化）
    text = text.replace('%n', '')
    text = text.replace('%r', '')
    text = text.replace('%t', '')
    
    # 移除多餘的空白字元
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def sanitize_filename(filename: str) -> str:
    """
    清理檔案名稱，防止路徑注入和日誌注入
    
    Args:
        filename: 檔案名稱
    
    Returns:
        清理後的檔案名稱
    """
    if not filename:
        return ""
    
    # 只保留檔案名稱部分（移除路徑）
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # 使用 sanitize_log_input 清理
    filename = sanitize_log_input(filename, max_length=255)
    
    # 移除可能的路徑字元
    filename = re.sub(r'[<>:"|?*]', '_', filename)
    
    return filename


def sanitize_path(path: str) -> str:
    """
    清理路徑，防止路徑注入和日誌注入
    
    Args:
        path: 路徑字串
    
    Returns:
        清理後的路徑
    """
    if not path:
        return ""
    
    # 使用 sanitize_log_input 清理
    path = sanitize_log_input(path, max_length=500)
    
    # 移除危險的路徑模式
    path = re.sub(r'\.\./', '', path)
    path = re.sub(r'\.\.\\', '', path)
    
    return path




