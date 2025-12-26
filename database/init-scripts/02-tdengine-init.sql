-- TDengine 时序数据库初始化脚本
-- 设备监控系统 - 一步部署

-- 创建数据库
CREATE DATABASE IF NOT EXISTS devicemonitor KEEP 365 DAYS 10 ROWS 4096 UPDATE 1;

-- 使用数据库
USE devicemonitor;

-- 创建设备数据超级表
CREATE STABLE IF NOT EXISTS device_data (
    ts TIMESTAMP,
    temperature FLOAT,
    humidity FLOAT,
    pressure FLOAT,
    voltage FLOAT,
    current FLOAT,
    power FLOAT,
    status INT,
    error_code INT,
    signal_strength INT
) TAGS (
    device_id NCHAR(100),
    device_type NCHAR(50),
    location NCHAR(200),
    group_id NCHAR(50)
);

-- 创建设备状态超级表
CREATE STABLE IF NOT EXISTS device_status (
    ts TIMESTAMP,
    online BOOL,
    last_heartbeat TIMESTAMP,
    cpu_usage FLOAT,
    memory_usage FLOAT,
    disk_usage FLOAT,
    network_status INT
) TAGS (
    device_id NCHAR(100),
    device_type NCHAR(50),
    location NCHAR(200)
);

-- 创建设备事件超级表
CREATE STABLE IF NOT EXISTS device_events (
    ts TIMESTAMP,
    event_type NCHAR(50),
    event_level INT,
    event_message NCHAR(500),
    event_data NCHAR(1000)
) TAGS (
    device_id NCHAR(100),
    device_type NCHAR(50),
    source NCHAR(100)
);

-- 创建系统监控超级表
CREATE STABLE IF NOT EXISTS system_metrics (
    ts TIMESTAMP,
    metric_name NCHAR(100),
    metric_value FLOAT,
    metric_unit NCHAR(20)
) TAGS (
    metric_type NCHAR(50),
    source NCHAR(100)
);

-- 创建示例设备表（用于测试）
CREATE TABLE IF NOT EXISTS device_001 USING device_data TAGS ('DEVICE_001', 'SENSOR', 'Building_A_Floor_1', 'GROUP_A');
CREATE TABLE IF NOT EXISTS device_002 USING device_data TAGS ('DEVICE_002', 'CONTROLLER', 'Building_A_Floor_2', 'GROUP_A');
CREATE TABLE IF NOT EXISTS device_003 USING device_data TAGS ('DEVICE_003', 'GATEWAY', 'Building_B_Floor_1', 'GROUP_B');

-- 创建对应的状态表
CREATE TABLE IF NOT EXISTS status_001 USING device_status TAGS ('DEVICE_001', 'SENSOR', 'Building_A_Floor_1');
CREATE TABLE IF NOT EXISTS status_002 USING device_status TAGS ('DEVICE_002', 'CONTROLLER', 'Building_A_Floor_2');
CREATE TABLE IF NOT EXISTS status_003 USING device_status TAGS ('DEVICE_003', 'GATEWAY', 'Building_B_Floor_1');

-- 插入一些示例数据
INSERT INTO device_001 VALUES 
    (NOW, 25.5, 60.2, 1013.25, 3.3, 0.5, 1.65, 1, 0, 85),
    (NOW - 1m, 25.3, 60.5, 1013.20, 3.2, 0.48, 1.54, 1, 0, 84),
    (NOW - 2m, 25.7, 59.8, 1013.30, 3.4, 0.52, 1.77, 1, 0, 86);

INSERT INTO device_002 VALUES 
    (NOW, 28.2, 55.1, 1012.80, 5.0, 1.2, 6.0, 1, 0, 92),
    (NOW - 1m, 28.0, 55.3, 1012.75, 4.9, 1.18, 5.78, 1, 0, 91),
    (NOW - 2m, 28.4, 54.9, 1012.85, 5.1, 1.22, 6.22, 1, 0, 93);

INSERT INTO device_003 VALUES 
    (NOW, 22.8, 65.5, 1014.10, 12.0, 2.5, 30.0, 1, 0, 78),
    (NOW - 1m, 22.6, 65.8, 1014.05, 11.9, 2.48, 29.5, 1, 0, 77),
    (NOW - 2m, 23.0, 65.2, 1014.15, 12.1, 2.52, 30.5, 1, 0, 79);

-- 插入状态数据
INSERT INTO status_001 VALUES 
    (NOW, true, NOW, 15.5, 45.2, 25.8, 1),
    (NOW - 1m, true, NOW - 1m, 15.3, 45.0, 25.6, 1);

INSERT INTO status_002 VALUES 
    (NOW, true, NOW, 22.1, 38.5, 42.3, 1),
    (NOW - 1m, true, NOW - 1m, 21.8, 38.2, 42.1, 1);

INSERT INTO status_003 VALUES 
    (NOW, true, NOW, 35.2, 62.1, 78.5, 1),
    (NOW - 1m, true, NOW - 1m, 34.8, 61.8, 78.2, 1);

-- 创建一些有用的视图（TDengine 3.0+ 支持）
-- 最新设备数据视图
-- CREATE VIEW IF NOT EXISTS latest_device_data AS 
-- SELECT LAST(*) FROM device_data GROUP BY device_id;

-- 输出初始化完成信息
SELECT 'TDengine database initialization completed successfully!' as status;
SELECT COUNT(*) as device_tables_created FROM information_schema.ins_tables WHERE db_name='devicemonitor' AND stable_name='device_data';
SELECT COUNT(*) as status_tables_created FROM information_schema.ins_tables WHERE db_name='devicemonitor' AND stable_name='device_status';