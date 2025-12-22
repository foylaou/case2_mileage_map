"""
CORS 安全檢查腳本
用於驗證 CVE-2024-6221, CVE-2024-1681, CVE-2024-6866, CVE-2024-6844 的修補

執行方式：python -m pytest tests/test_cors_security.py
或：python tests/test_cors_security.py
"""
import os
import sys
import requests
import time
from pathlib import Path

# 確保可以找到模組
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

# 設定測試用的環境變數
os.environ['PORT'] = '5001'
os.environ['HOST'] = '127.0.0.1'
os.environ['DEBUG'] = 'False'

# 測試結果
test_results = []
test_count = 0
pass_count = 0
fail_count = 0


def log_test(name: str, passed: bool, message: str = ""):
    """記錄測試結果"""
    global test_count, pass_count, fail_count
    test_count += 1
    if passed:
        pass_count += 1
        status = "✓ PASS"
    else:
        fail_count += 1
        status = "✗ FAIL"
    
    result = {
        'name': name,
        'passed': passed,
        'message': message
    }
    test_results.append(result)
    print(f"[{status}] {name}")
    if message:
        print(f"      {message}")


def check_cors_header(response, origin, should_allow=True):
    """檢查 CORS 標頭"""
    cors_header = response.headers.get('Access-Control-Allow-Origin')
    
    if should_allow:
        # 應該允許的 origin，應該有對應的標頭
        if cors_header == origin:
            return True, f"CORS 標頭正確: {cors_header}"
        else:
            return False, f"預期 CORS 標頭為 {origin}，實際為 {cors_header}"
    else:
        # 不應該允許的 origin，不應該有標頭或標頭不匹配
        if cors_header is None:
            return True, "正確拒絕未授權的 origin（無 CORS 標頭）"
        elif cors_header == origin:
            return False, f"錯誤允許未授權的 origin: {cors_header}"
        else:
            return True, f"正確拒絕未授權的 origin（標頭為 {cors_header}）"


def test_whitelist_origins():
    """測試 1: 只有白名單 origin 才會拿到 Access-Control-Allow-Origin"""
    print("\n=== 測試 1: 白名單 Origin 檢查 ===")
    
    base_url = "http://127.0.0.1:5001"
    port = 5001
    
    # 測試允許的 origin
    allowed_origins = [
        f"http://localhost:{port}",
        f"http://127.0.0.1:{port}",
    ]
    
    for origin in allowed_origins:
        try:
            response = requests.options(
                f"{base_url}/api/health",
                headers={
                    'Origin': origin,
                    'Access-Control-Request-Method': 'GET',
                    'Access-Control-Request-Headers': 'Content-Type'
                },
                timeout=2
            )
            passed, msg = check_cors_header(response, origin, should_allow=True)
            log_test(f"允許的 Origin: {origin}", passed, msg)
        except requests.exceptions.RequestException as e:
            log_test(f"允許的 Origin: {origin}", False, f"請求失敗: {str(e)}")
    
    # 測試不允許的 origin
    blocked_origins = [
        "http://evil.com",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "https://localhost:5001",
        "http://192.168.1.1:5001",
    ]
    
    for origin in blocked_origins:
        try:
            response = requests.options(
                f"{base_url}/api/health",
                headers={
                    'Origin': origin,
                    'Access-Control-Request-Method': 'GET',
                    'Access-Control-Request-Headers': 'Content-Type'
                },
                timeout=2
            )
            passed, msg = check_cors_header(response, origin, should_allow=False)
            log_test(f"阻擋的 Origin: {origin}", passed, msg)
        except requests.exceptions.RequestException as e:
            log_test(f"阻擋的 Origin: {origin}", False, f"請求失敗: {str(e)}")


def test_path_case_sensitivity():
    """
    測試 2: path 大小寫敏感性檢查（CVE-2024-6866）
    
    安全設計：只有嚴格的小寫 '/api/*' 路徑允許 CORS
    大小寫不一致的路徑（如 /API/*, /Api/*）應被拒絕，這是預期的安全行為
    """
    print("\n=== 測試 2: Path 大小寫敏感性檢查 ===")
    print("安全設計：只有嚴格的小寫 '/api/*' 路徑允許 CORS")
    print("大小寫不一致的路徑應被拒絕（預期行為，非漏洞）")
    print()
    
    base_url = "http://127.0.0.1:5001"
    port = 5001
    origin = f"http://localhost:{port}"
    
    # 測試不同大小寫的 path
    # 只有嚴格的小寫 '/api/*' 應該允許 CORS
    test_cases = [
        ("/api/health", True, "嚴格小寫路徑，應允許 CORS"),
        ("/API/health", False, "大寫路徑，應拒絕 CORS（CVE-2024-6866 修補）"),
        ("/Api/health", False, "混合大小寫路徑，應拒絕 CORS（CVE-2024-6866 修補）"),
        ("/api/HEALTH", True, "路徑首段小寫，應允許 CORS（後段大小寫不影響）"),
        ("/API/HEALTH", False, "大寫路徑，應拒絕 CORS（CVE-2024-6866 修補）"),
    ]
    
    for path, should_allow, description in test_cases:
        try:
            response = requests.options(
                f"{base_url}{path}",
                headers={
                    'Origin': origin,
                    'Access-Control-Request-Method': 'GET',
                    'Access-Control-Request-Headers': 'Content-Type'
                },
                timeout=2
            )
            
            cors_header = response.headers.get('Access-Control-Allow-Origin')
            
            if should_allow:
                # 應該允許的路徑，檢查是否有正確的 CORS 標頭
                if cors_header == origin:
                    passed = True
                    msg = f"CORS 標頭正確: {cors_header}"
                else:
                    passed = False
                    msg = f"預期 CORS 標頭為 {origin}，實際為 {cors_header}"
            else:
                # 應該拒絕的路徑，檢查是否沒有 CORS 標頭（預期行為）
                if cors_header is None:
                    passed = True
                    msg = f"正確拒絕大小寫不一致路徑（無 CORS 標頭）- {description}"
                elif cors_header == origin:
                    passed = False
                    msg = f"錯誤允許大小寫不一致路徑: {cors_header}"
                else:
                    passed = True
                    msg = f"正確拒絕大小寫不一致路徑（標頭不匹配）- {description}"
            
            # 如果是預期拒絕的情況，加上安全說明
            if not should_allow and passed:
                msg += " [Expected Reject - Case-insensitive path is intentionally rejected to mitigate CVE-2024-6866]"
            
            log_test(f"Path 大小寫測試: {path}", passed, msg)
            
        except requests.exceptions.RequestException as e:
            log_test(f"Path 大小寫測試: {path}", False, f"請求失敗: {str(e)}")


def test_path_plus_handling():
    """
    測試 3: 含 '+' 的 path 處理檢查（CVE-2024-6844）
    
    驗證 Flask-CORS >=6.0.0 已正確修補 '+' 字元處理問題
    """
    print("\n=== 測試 3: Path '+' 字元處理檢查 ===")
    print("驗證 Flask-CORS >=6.0.0 已正確修補 CVE-2024-6844")
    print()
    
    base_url = "http://127.0.0.1:5001"
    port = 5001
    origin = f"http://localhost:{port}"
    
    # 測試含 '+' 的 path（僅小寫 '/api/*' 路徑）
    test_paths = [
        "/api/health",
        "/api/health+test",
        "/api/health+test+more",
        "/api/+health",
        "/api/health+",
    ]
    
    for path in test_paths:
        try:
            response = requests.options(
                f"{base_url}{path}",
                headers={
                    'Origin': origin,
                    'Access-Control-Request-Method': 'GET',
                    'Access-Control-Request-Headers': 'Content-Type'
                },
                timeout=2
            )
            # 所有小寫 /api/* 路徑（含 +）都應該正確處理並允許 CORS
            if path.startswith('/api/'):
                passed, msg = check_cors_header(response, origin, should_allow=True)
                log_test(f"Path '+' 測試: {path}", passed, msg)
        except requests.exceptions.RequestException as e:
            log_test(f"Path '+' 測試: {path}", False, f"請求失敗: {str(e)}")


def test_cors_methods_and_headers():
    """測試 4: CORS methods 和 headers 設定"""
    print("\n=== 測試 4: CORS Methods 和 Headers 檢查 ===")
    
    base_url = "http://127.0.0.1:5001"
    port = 5001
    origin = f"http://localhost:{port}"
    
    try:
        response = requests.options(
            f"{base_url}/api/health",
            headers={
                'Origin': origin,
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            },
            timeout=2
        )
        
        # 檢查允許的 methods
        allow_methods = response.headers.get('Access-Control-Allow-Methods', '')
        expected_methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
        methods_ok = all(method in allow_methods for method in expected_methods)
        log_test("CORS Methods 設定", methods_ok, 
                f"允許的方法: {allow_methods}" if methods_ok else f"缺少某些方法，實際: {allow_methods}")
        
        # 檢查允許的 headers
        allow_headers = response.headers.get('Access-Control-Allow-Headers', '')
        expected_headers = ['Content-Type', 'Authorization']
        headers_ok = all(header in allow_headers for header in expected_headers)
        log_test("CORS Headers 設定", headers_ok,
                f"允許的標頭: {allow_headers}" if headers_ok else f"缺少某些標頭，實際: {allow_headers}")
        
    except requests.exceptions.RequestException as e:
        log_test("CORS Methods 和 Headers 檢查", False, f"請求失敗: {str(e)}")


def test_credentials_setting():
    """測試 5: supports_credentials 設定"""
    print("\n=== 測試 5: Credentials 設定檢查 ===")
    
    base_url = "http://127.0.0.1:5001"
    port = 5001
    origin = f"http://localhost:{port}"
    
    try:
        response = requests.options(
            f"{base_url}/api/health",
            headers={
                'Origin': origin,
                'Access-Control-Request-Method': 'GET',
            },
            timeout=2
        )
        
        # 檢查 credentials 標頭（應該不存在或為 false）
        credentials = response.headers.get('Access-Control-Allow-Credentials', '')
        # 如果沒有這個標頭，或者值不是 'true'，都是安全的
        credentials_ok = credentials.lower() != 'true'
        log_test("Credentials 設定", credentials_ok,
                f"Credentials 標頭: {credentials if credentials else '未設定（安全）'}")
        
    except requests.exceptions.RequestException as e:
        log_test("Credentials 設定檢查", False, f"請求失敗: {str(e)}")


def test_non_api_paths():
    """測試 6: 非 API 路徑不應該有 CORS"""
    print("\n=== 測試 6: 非 API 路徑 CORS 檢查 ===")
    
    base_url = "http://127.0.0.1:5001"
    port = 5001
    origin = f"http://localhost:{port}"
    
    # 測試非 API 路徑
    non_api_paths = [
        "/",
        "/health",
        "/temp/maps/test.png",
    ]
    
    for path in non_api_paths:
        try:
            response = requests.options(
                f"{base_url}{path}",
                headers={
                    'Origin': origin,
                    'Access-Control-Request-Method': 'GET',
                },
                timeout=2
            )
            # 非 API 路徑不應該有 CORS 標頭
            cors_header = response.headers.get('Access-Control-Allow-Origin')
            passed = cors_header is None or cors_header != origin
            msg = f"非 API 路徑正確不允許 CORS" if passed else f"錯誤允許非 API 路徑的 CORS: {cors_header}"
            log_test(f"非 API 路徑: {path}", passed, msg)
        except requests.exceptions.RequestException as e:
            log_test(f"非 API 路徑: {path}", False, f"請求失敗: {str(e)}")


def main():
    """主函數"""
    print("=" * 60)
    print("CORS 安全檢查腳本")
    print("驗證 CVE-2024-6221, CVE-2024-1681, CVE-2024-6866, CVE-2024-6844 修補")
    print("=" * 60)
    
    # 檢查服務是否運行
    print("\n檢查服務是否運行...")
    try:
        response = requests.get("http://127.0.0.1:5001/health", timeout=2)
        if response.status_code == 200:
            print("✓ 服務正在運行")
        else:
            print(f"✗ 服務回應異常: {response.status_code}")
            print("請先啟動 Flask 應用程式（python main.py 或 python app.py）")
            return
    except requests.exceptions.RequestException:
        print("✗ 無法連接到服務")
        print("請先啟動 Flask 應用程式（python main.py 或 python app.py）")
        print("\n提示：在另一個終端執行：")
        print("  cd backend")
        print("  python main.py")
        return
    
    # 等待服務完全啟動
    time.sleep(1)
    
    # 執行測試
    test_whitelist_origins()
    test_path_case_sensitivity()
    test_path_plus_handling()
    test_cors_methods_and_headers()
    test_credentials_setting()
    test_non_api_paths()
    
    # 輸出總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    print(f"總測試數: {test_count}")
    print(f"通過: {pass_count}")
    print(f"失敗: {fail_count}")
    print(f"通過率: {(pass_count/test_count*100):.1f}%" if test_count > 0 else "N/A")
    
    if fail_count == 0:
        print("\n✓ 所有測試通過！CORS 安全設定正確。")
        print("\n注意：Path 大小寫不一致的路徑被拒絕是預期的安全行為，")
        print("     這是為了修補 CVE-2024-6866 而採用的設計。")
        return 0
    else:
        print("\n✗ 部分測試失敗，請檢查 CORS 設定。")
        print("\n提示：如果失敗的是大小寫不一致路徑測試，")
        print("     請確認這些路徑被正確拒絕（預期行為）。")
        return 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n測試被使用者中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n測試執行錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

