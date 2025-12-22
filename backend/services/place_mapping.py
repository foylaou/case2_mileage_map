"""
地點名稱對應地址服務
"""
from loguru import logger


class PlaceMappingService:
    """地點名稱對應地址服務類別"""
    
    def __init__(self):
        # 可擴充的地點名稱對應表
        self.place_address_map = {
            "安環高雄處": "高雄市前鎮區復興四路12號",
            "總公司": "台北市信義區信義路五段7號",
            # 經濟部產業園區管理局：請確認正確地址後更新
            # 目前使用臨時地址，請根據實際地址更新
            "經濟部產業園區管理局": "高雄市前鎮區中一路2號",
            "高雄市政府": "高雄市苓雅區四維三路2號",
            "科技園區": "新竹市東區新安路2號",
            "工業區管理處": "台中市西屯區工業區一路2號",
            # 可在此新增更多對應
        }
    
    def get_address(self, place_name):
        """
        取得地點對應的完整地址
        
        Args:
            place_name: 地點名稱
            
        Returns:
            str: 完整地址，如果找不到則回傳 None
        """
        try:
            # 去除空白
            place_name = place_name.strip() if place_name else ""
            
            if not place_name:
                return None
            
            # 從對應表查找
            if place_name in self.place_address_map:
                return self.place_address_map[place_name]
            
            # 嘗試模糊匹配（部分匹配）
            for key, address in self.place_address_map.items():
                if key in place_name or place_name in key:
                    logger.info(f"模糊匹配成功: {place_name} -> {key} -> {address}")
                    return address
            
            return None
            
        except Exception as e:
            logger.error(f"取得地點地址錯誤: {str(e)}")
            return None
    
    def add_mapping(self, place_name, address):
        """
        新增地點對應
        
        Args:
            place_name: 地點名稱
            address: 完整地址
        """
        try:
            self.place_address_map[place_name] = address
            logger.info(f"新增地點對應: {place_name} -> {address}")
        except Exception as e:
            logger.error(f"新增地點對應錯誤: {str(e)}")
    
    def get_all_mappings(self):
        """
        取得所有對應
        
        Returns:
            dict: 所有地點對應
        """
        return self.place_address_map.copy()


