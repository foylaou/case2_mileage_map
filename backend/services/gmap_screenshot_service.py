"""
Google Maps 路線截圖服務
使用 Playwright 截取 Google Maps 完整路線頁面（包含左側面板和右側地圖）
"""
from pathlib import Path
from typing import Optional
from urllib.parse import quote
from loguru import logger
import asyncio
import os

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright 未安裝，無法使用 Google Maps 截圖功能")


async def capture_route_screenshot(
    origin: str,
    destination: str,
    output_path: str | Path,
    viewport_width: int = 1500,
    viewport_height: int = 750,
    wait_timeout: int = 30000,
) -> Optional[str]:
    """
    使用 headless browser 開啟 Google Maps 的駕車路線畫面並截圖
    
    Args:
        origin: 起點地址或名稱
        destination: 終點地址或名稱
        output_path: 輸出圖片路徑
        viewport_width: 瀏覽器視窗寬度（預設 1500）
        viewport_height: 瀏覽器視窗高度（預設 750）
        wait_timeout: 等待頁面載入的超時時間（毫秒，預設 10000）
    
    Returns:
        str: 截圖檔案路徑，如果失敗則返回 None
    """
    if not PLAYWRIGHT_AVAILABLE:
        logger.error("Playwright 未安裝，無法截取 Google Maps 畫面")
        return None
    
    try:
        # 轉換為 Path 物件
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # URL encode 起點和終點
        origin_encoded = quote(origin)
        destination_encoded = quote(destination)
        
        # 構建 Google Maps 路線 URL
        maps_url = (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={origin_encoded}"
            f"&destination={destination_encoded}"
            f"&travelmode=driving"
        )
        
        logger.info(f"開始截取 Google Maps 路線: {origin} -> {destination}")
        logger.debug(f"Google Maps URL: {maps_url}")
        
        browser = None
        context = None
        page = None
        
        async with async_playwright() as p:
            # 啟動瀏覽器（使用 Chromium）
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )
            
            try:
                # 創建新頁面
                context = await browser.new_context(
                    viewport={'width': viewport_width, 'height': viewport_height},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = await context.new_page()
                
                try:
                    # 導航到 Google Maps 路線頁面
                    # 使用 'load' 而不是 'networkidle'，因為 Google Maps 會持續載入資源
                    await page.goto(maps_url, wait_until='load', timeout=wait_timeout)
                    
                    # 等待頁面基本載入完成
                    await page.wait_for_timeout(3000)  # 等待 3 秒讓頁面基本載入
                    
                    # 嘗試等待左側路線面板或地圖載入
                    # Google Maps 的路線面板可能有多種結構，使用更寬鬆的選擇器
                    try:
                        # 等待任何包含路線資訊的元素出現
                        await page.wait_for_selector(
                            'div[role="main"], [data-value="駕車"], [aria-label*="分鐘"], [aria-label*="公里"], canvas, [jsaction*="route"]',
                            timeout=15000
                        )
                        logger.debug("檢測到頁面元素")
                    except PlaywrightTimeoutError:
                        logger.warning("未檢測到特定元素，繼續等待...")
                    
                    # 額外等待頁面完全載入（包括地圖和路線）
                    await page.wait_for_timeout(8000)  # 等待 8 秒讓地圖和路線完全載入
                    
                    # 再等待一下確保所有內容都載入完成（包括左側面板的路線列表）
                    await page.wait_for_timeout(2000)
                    
                    # 截取整個視窗的截圖
                    await page.screenshot(
                        path=str(output_path),
                        full_page=False,  # 只截視窗大小
                        type='png'
                    )
                    
                    logger.info(f"成功截取 Google Maps 路線截圖: {output_path}")
                    
                    return str(output_path)
                    
                except PlaywrightTimeoutError as e:
                    logger.error(f"等待頁面載入超時: {str(e)}")
                    return None
                except Exception as e:
                    logger.error(f"截取 Google Maps 截圖時發生錯誤: {str(e)}")
                    return None
                finally:
                    # 確保 page 和 context 被正確關閉
                    if page:
                        try:
                            await page.close()
                        except Exception as e:
                            logger.warning(f"關閉 page 時發生錯誤: {str(e)}")
                    if context:
                        try:
                            await context.close()
                        except Exception as e:
                            logger.warning(f"關閉 context 時發生錯誤: {str(e)}")
            
            finally:
                # 確保 browser 被正確關閉
                if browser:
                    try:
                        await browser.close()
                        # 等待瀏覽器進程完全終止
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        logger.warning(f"關閉 browser 時發生錯誤: {str(e)}")
    
    except Exception as e:
        logger.error(f"Playwright 執行失敗: {str(e)}")
        return None


def capture_route_screenshot_sync(
    origin: str,
    destination: str,
    output_path: str | Path,
    viewport_width: int = 1500,
    viewport_height: int = 750,
    wait_timeout: int = 30000,
) -> Optional[str]:
    """
    同步版本的 Google Maps 路線截圖函數
    
    Args:
        origin: 起點地址或名稱
        destination: 終點地址或名稱
        output_path: 輸出圖片路徑
        viewport_width: 瀏覽器視窗寬度（預設 1500）
        viewport_height: 瀏覽器視窗高度（預設 750）
        wait_timeout: 等待頁面載入的超時時間（毫秒，預設 10000）
    
    Returns:
        str: 截圖檔案路徑，如果失敗則返回 None
    """
    if not PLAYWRIGHT_AVAILABLE:
        logger.error("Playwright 未安裝，無法截取 Google Maps 畫面")
        return None
    
    try:
        # 檢查是否有正在運行的 event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已經有運行的 loop，需要在新的執行緒中執行
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        capture_route_screenshot(origin, destination, output_path, viewport_width, viewport_height, wait_timeout)
                    )
                    return future.result(timeout=(wait_timeout / 1000) + 30)  # 額外給 30 秒緩衝
            else:
                return loop.run_until_complete(
                    capture_route_screenshot(origin, destination, output_path, viewport_width, viewport_height, wait_timeout)
                )
        except RuntimeError:
            # 沒有 event loop，直接使用 asyncio.run
            return asyncio.run(
                capture_route_screenshot(origin, destination, output_path, viewport_width, viewport_height, wait_timeout)
            )
    except Exception as e:
        logger.error(f"同步截圖函數執行失敗: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None
