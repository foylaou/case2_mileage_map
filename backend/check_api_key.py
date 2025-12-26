"""
檢查 Google Maps API Key 設定
"""
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')

print("=" * 50)
print("Google Maps API Key 檢查")
print("=" * 50)
print()

if not api_key:
    print("❌ 錯誤：未設定 GOOGLE_MAPS_API_KEY")
    print()
    print("請在 .env 檔案中設定：")
    print("GOOGLE_MAPS_API_KEY=your-api-key-here")
    print()
    print("取得 API Key 步驟：")
    print("1. 前往 https://console.cloud.google.com/")
    print("2. 建立新專案或選擇現有專案")
    print("3. 啟用 Google Maps Directions API 和 Static Maps API")
    print("4. 建立 API Key")
    print("5. 將 API Key 填入 .env 檔案")
    exit(1)
else:
    print(f"✅ 已設定 API Key: {api_key[:20]}...{api_key[-10:]}")
    print()
    
    # 測試 API Key 是否有效
    try:
        import googlemaps
        gmaps = googlemaps.Client(key=api_key)
        
        # 簡單測試：地理編碼
        result = gmaps.geocode("台北101", language='zh-TW')
        if result:
            print("✅ API Key 有效，可以正常使用")
            print(f"   測試結果：成功取得「台北101」的地理座標")
        else:
            print("⚠️  API Key 可能無效，無法取得地理座標")
    except Exception as e:
        print(f"❌ API Key 測試失敗: {str(e)}")
        print()
        print("可能的原因：")
        print("1. API Key 無效或已過期")
        print("2. 未啟用必要的 API（Directions API、Static Maps API）")
        print("3. API Key 有使用限制（IP、HTTP referrer 等）")

print()
print("=" * 50)

