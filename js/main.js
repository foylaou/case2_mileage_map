// 第二案：地點里程與地圖報表系統 - JavaScript 功能

// 頁面載入時初始化
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
});

// 初始化頁面
function initializePage() {
    // 初始化功能
}

// API 基礎 URL - 使用相對路徑，適用於打包後的 exe 版本
const API_BASE_URL = window.location.origin + '/api';

// 取得 JWT Token
function getToken() {
    return localStorage.getItem('token');
}

// API 請求函數
async function apiRequest(endpoint, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    const token = getToken();
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.message || '請求失敗');
        }
        
        return result;
    } catch (error) {
        console.error('API 請求錯誤:', error);
        throw error;
    }
}

// 計算里程
async function calculateDistance() {
    try {
        const startLocation = document.getElementById('startLocation').value;
        const endLocation = document.getElementById('endLocation').value;
        const routeType = document.getElementById('routeType').value;
        
        if (!startLocation || !endLocation) {
            alert('請輸入起點和終點');
            return;
        }
        
        const result = await apiRequest('/mileage/calculate', 'POST', {
            start_location: startLocation,
            end_location: endLocation,
            route_type: routeType
        });
        
        if (result.status === 'success' && result.data) {
            const data = result.data;
            
            // 顯示結果
            document.getElementById('oneWayDistance').textContent = data.one_way_distance + ' km';
            document.getElementById('roundTripDistance').textContent = data.round_trip_distance + ' km';
            document.getElementById('estimatedTime').textContent = data.estimated_time;
            document.getElementById('routeDescription').textContent = data.route_description || '經由主要道路';
            document.getElementById('distanceResult').style.display = 'block';
            
            // TODO: 在地圖上顯示路線
            alert('里程計算完成');
        } else {
            throw new Error(result.message || '計算失敗');
        }
    } catch (error) {
        console.error('計算里程錯誤:', error);
        alert('計算里程失敗：' + error.message);
    }
}

// 地圖選點
function selectOnMap(type) {
    alert(`開啟地圖選點功能（${type}）（需整合地圖 API）`);
}

// 加入出差紀錄
async function addToRecord() {
    try {
        const startLocation = document.getElementById('startLocation').value;
        const endLocation = document.getElementById('endLocation').value;
        const oneWayDistance = document.getElementById('oneWayDistance').textContent;
        const roundTripDistance = document.getElementById('roundTripDistance').textContent;
        
        if (!startLocation || !endLocation || !oneWayDistance || oneWayDistance === '-') {
            alert('請先計算里程');
            return;
        }
        
        const result = await apiRequest('/mileage/records', 'POST', {
            travel_date: new Date().toISOString().split('T')[0],
            start_location: startLocation,
            end_location: endLocation,
            one_way_distance: parseFloat(oneWayDistance.replace(' km', '')),
            round_trip_distance: parseFloat(roundTripDistance.replace(' km', '')),
            estimated_time: document.getElementById('estimatedTime').textContent,
            route_type: document.getElementById('routeType').value,
            route_description: document.getElementById('routeDescription').textContent
        });
        
        if (result.status === 'success') {
            alert('已加入出差紀錄');
            updateTravelRecordTable();
        }
    } catch (error) {
        console.error('加入出差紀錄錯誤:', error);
        alert('加入出差紀錄失敗：' + error.message);
    }
}

// 更新出差紀錄表格
function updateTravelRecordTable() {
    const tableBody = document.getElementById('travelRecordTable');
    if (tableBody) {
        // 這裡應該從後端取得資料並更新表格
    }
}

// 匯入出差紀錄
async function importTravelRecord() {
    try {
        const fileInput = document.getElementById('importFile');
        const file = fileInput.files[0];
        
        if (!file) {
            alert('請選擇要匯入的檔案');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE_URL}/mileage/import`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getToken()}`
            },
            body: formData
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            alert(`成功匯入 ${result.data.imported_count} 筆資料`);
            updateTravelRecordTable();
        } else {
            throw new Error(result.message || '匯入失敗');
        }
    } catch (error) {
        console.error('匯入出差紀錄錯誤:', error);
        alert('匯入失敗：' + error.message);
    }
}

// 與系統資料比對
function compareWithSystem() {
    alert('資料比對功能需與後端 API 整合');
}

// 清除地圖
function clearMap() {
    document.getElementById('startLocation').value = '';
    document.getElementById('endLocation').value = '';
    document.getElementById('distanceResult').style.display = 'none';
    alert('地圖已清除');
}

// 匯出地圖
function exportMap() {
    alert('地圖匯出功能需與後端 API 整合');
}

// 匯出里程報表
function exportMileageReport(format) {
    alert(`匯出里程 ${format.toUpperCase()} 報表功能需與後端 API 整合`);
}

// 產生里程報表
async function generateMileageReport() {
    try {
        const reportType = document.getElementById('mileageReportType').value;
        const startDate = document.getElementById('mileageStartDate').value;
        const endDate = document.getElementById('mileageEndDate').value;
        const format = document.querySelector('input[name="mileageFormat"]:checked').value;
        const includeMap = document.getElementById('includeMap').checked;
        const includeRoute = document.getElementById('includeRoute').checked;
        const includeDistance = document.getElementById('includeDistance').checked;
        
        if (!reportType || !startDate || !endDate) {
            alert('請填寫完整資訊');
            return;
        }
        
        const reportData = {
            report_type: reportType,
            start_date: startDate,
            end_date: endDate,
            format: format,
            include_map: includeMap,
            include_route: includeRoute,
            include_distance: includeDistance
        };
        
        const response = await fetch(`${API_BASE_URL}/reports/mileage/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            },
            body: JSON.stringify(reportData)
        });
        
        if (!response.ok) {
            throw new Error('報表產生失敗');
        }
        
        // 下載檔案
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `里程報表_${new Date().toISOString().slice(0, 10)}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
    } catch (error) {
        console.error('產生報表錯誤:', error);
        alert('產生報表失敗：' + error.message);
    }
}

// 儲存地圖設定
function saveMapSettings() {
    const settings = {
        mapProvider: document.getElementById('mapProvider').value,
        googleApiKey: document.getElementById('googleApiKey').value
    };
    
    console.log('儲存地圖設定:', settings);
    alert('設定已儲存（需與後端 API 整合）');
}

// 切換密碼顯示
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const button = input.nextElementSibling;
    const icon = button.querySelector('i');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('bi-eye');
        icon.classList.add('bi-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('bi-eye-slash');
        icon.classList.add('bi-eye');
    }
}

