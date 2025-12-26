-- 第二案：地點里程與地圖報表系統 - 資料庫初始化腳本

-- 建立資料庫
CREATE DATABASE IF NOT EXISTS mileage_map CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE mileage_map;

-- 出差紀錄資料表
CREATE TABLE IF NOT EXISTS travel_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    travel_date DATE NOT NULL COMMENT '出差日期',
    start_location VARCHAR(200) NOT NULL COMMENT '起點',
    end_location VARCHAR(200) NOT NULL COMMENT '終點',
    one_way_distance DECIMAL(10, 2) COMMENT '單程距離（公里）',
    round_trip_distance DECIMAL(10, 2) COMMENT '往返距離（公里）',
    estimated_time VARCHAR(50) COMMENT '預估時間',
    route_type VARCHAR(20) DEFAULT 'driving' COMMENT '路線類型：driving, walking, transit',
    route_description TEXT COMMENT '路線說明',
    map_image_path VARCHAR(500) COMMENT '地圖圖片路徑',
    status VARCHAR(20) DEFAULT 'active' COMMENT '狀態：active, archived',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '建立時間',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新時間',
    INDEX idx_travel_date (travel_date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='出差紀錄資料表';

-- 系統設定資料表
CREATE TABLE IF NOT EXISTS system_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL COMMENT '設定鍵值',
    setting_value TEXT COMMENT '設定值（JSON格式）',
    setting_type VARCHAR(50) COMMENT '設定類型：map, system',
    description VARCHAR(500) COMMENT '說明',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '建立時間',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新時間'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系統設定資料表';

-- 使用者資料表（可與第一案共用或獨立）
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '帳號',
    password_hash VARCHAR(255) NOT NULL COMMENT '密碼雜湊',
    name VARCHAR(100) NOT NULL COMMENT '姓名',
    email VARCHAR(100) NOT NULL COMMENT '電子郵件',
    role VARCHAR(20) NOT NULL DEFAULT 'user' COMMENT '角色：admin, user',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否啟用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '建立時間',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新時間'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='使用者資料表';

-- 插入預設管理員（密碼：admin123）
INSERT INTO users (username, password_hash, name, email, role) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqJqZqZqZq', '系統管理員', 'admin@example.com', 'admin')
ON DUPLICATE KEY UPDATE username=username;









