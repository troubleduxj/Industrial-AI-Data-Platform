-- ========================================
-- 模拟设备分类 - 完整Mock数据
-- 包含：基础信息、实时数据、历史数据
-- 生成时间: 2025-10-30
-- ========================================

-- ========================================
-- 1. 模拟设备分类 - 基础信息
-- ========================================

INSERT INTO t_sys_mock_data (
    name, description, method, url_pattern, response_data, 
    response_code, delay, enabled, priority
) VALUES (
    '模拟设备分类-设备列表',
    '模拟设备分类的设备列表数据',
    'GET',
    '/api/v2/devices.*device_type=simulation',
    '{
      "success": true,
      "code": 200,
      "message": "获取设备列表成功",
      "data": {
        "items": [
          {
            "id": 1001,
            "device_code": "SIM-DEV-001",
            "device_name": "模拟温控设备A",
            "device_type": "simulation",
            "device_type_name": "模拟设备",
            "manufacturer": "虚拟制造商",
            "device_model": "SIM-TC-100",
            "install_location": "模拟车间-A区",
            "status": "运行中",
            "is_locked": false,
            "online_address": "192.168.100.101",
            "team_name": "模拟运维组A",
            "last_maintenance_date": "2025-10-25",
            "next_maintenance_date": "2025-11-25",
            "purchase_date": "2024-01-15",
            "warranty_date": "2027-01-15",
            "description": "用于模拟温度控制的虚拟设备",
            "created_at": "2024-01-15T10:00:00",
            "updated_at": "2025-10-30T10:00:00"
          },
          {
            "id": 1002,
            "device_code": "SIM-DEV-002",
            "device_name": "模拟压力监测设备B",
            "device_type": "simulation",
            "device_type_name": "模拟设备",
            "manufacturer": "虚拟制造商",
            "device_model": "SIM-PM-200",
            "install_location": "模拟车间-B区",
            "status": "运行中",
            "is_locked": false,
            "online_address": "192.168.100.102",
            "team_name": "模拟运维组B",
            "last_maintenance_date": "2025-10-20",
            "next_maintenance_date": "2025-11-20",
            "purchase_date": "2024-02-01",
            "warranty_date": "2027-02-01",
            "description": "用于模拟压力监测的虚拟设备",
            "created_at": "2024-02-01T10:00:00",
            "updated_at": "2025-10-30T10:00:00"
          },
          {
            "id": 1003,
            "device_code": "SIM-DEV-003",
            "device_name": "模拟流量计设备C",
            "device_type": "simulation",
            "device_type_name": "模拟设备",
            "manufacturer": "虚拟制造商",
            "device_model": "SIM-FM-300",
            "install_location": "模拟车间-C区",
            "status": "运行中",
            "is_locked": false,
            "online_address": "192.168.100.103",
            "team_name": "模拟运维组C",
            "last_maintenance_date": "2025-10-22",
            "next_maintenance_date": "2025-11-22",
            "purchase_date": "2024-03-10",
            "warranty_date": "2027-03-10",
            "description": "用于模拟流量监测的虚拟设备",
            "created_at": "2024-03-10T10:00:00",
            "updated_at": "2025-10-30T10:00:00"
          },
          {
            "id": 1004,
            "device_code": "SIM-DEV-004",
            "device_name": "模拟能耗监控设备D",
            "device_type": "simulation",
            "device_type_name": "模拟设备",
            "manufacturer": "虚拟制造商",
            "device_model": "SIM-EM-400",
            "install_location": "模拟车间-D区",
            "status": "维护中",
            "is_locked": true,
            "online_address": "192.168.100.104",
            "team_name": "模拟运维组D",
            "last_maintenance_date": "2025-10-28",
            "next_maintenance_date": "2025-11-28",
            "purchase_date": "2024-04-20",
            "warranty_date": "2027-04-20",
            "description": "用于模拟能耗监控的虚拟设备",
            "created_at": "2024-04-20T10:00:00",
            "updated_at": "2025-10-30T10:00:00"
          },
          {
            "id": 1005,
            "device_code": "SIM-DEV-005",
            "device_name": "模拟振动传感设备E",
            "device_type": "simulation",
            "device_type_name": "模拟设备",
            "manufacturer": "虚拟制造商",
            "device_model": "SIM-VS-500",
            "install_location": "模拟车间-E区",
            "status": "运行中",
            "is_locked": false,
            "online_address": "192.168.100.105",
            "team_name": "模拟运维组E",
            "last_maintenance_date": "2025-10-18",
            "next_maintenance_date": "2025-11-18",
            "purchase_date": "2024-05-15",
            "warranty_date": "2027-05-15",
            "description": "用于模拟振动监测的虚拟设备",
            "created_at": "2024-05-15T10:00:00",
            "updated_at": "2025-10-30T10:00:00"
          }
        ],
        "total": 5,
        "page": 1,
        "page_size": 20,
        "total_pages": 1
      },
      "meta": {
        "timestamp": "2025-10-30T12:00:00Z",
        "request_id": "sim-devices-list-001"
      },
      "timestamp": "2025-10-30T12:00:00Z"
    }',
    200,
    400,
    false,
    100
) ON CONFLICT DO NOTHING;

-- ========================================
-- 2. 模拟设备 - 详情信息
-- ========================================

INSERT INTO t_sys_mock_data (
    name, description, method, url_pattern, response_data, 
    response_code, delay, enabled, priority
) VALUES (
    '模拟设备-详情信息',
    '模拟设备的详细信息',
    'GET',
    '/api/v2/devices/100[1-5]$',
    '{
      "success": true,
      "code": 200,
      "message": "获取设备详情成功",
      "data": {
        "id": 1001,
        "device_code": "SIM-DEV-001",
        "device_name": "模拟温控设备A",
        "device_type": "simulation",
        "device_type_name": "模拟设备",
        "manufacturer": "虚拟制造商",
        "device_model": "SIM-TC-100",
        "install_location": "模拟车间-A区",
        "status": "运行中",
        "is_locked": false,
        "online_address": "192.168.100.101",
        "team_name": "模拟运维组A",
        "specifications": {
          "温度范围": "0-100°C",
          "精度": "±0.1°C",
          "功率": "2.5kW",
          "电压": "220V",
          "重量": "85kg"
        },
        "last_maintenance_date": "2025-10-25",
        "next_maintenance_date": "2025-11-25",
        "purchase_date": "2024-01-15",
        "warranty_date": "2027-01-15",
        "description": "用于模拟温度控制的虚拟设备，支持精确温度控制和实时监测",
        "maintenance_history": [
          {
            "date": "2025-10-25",
            "type": "定期维护",
            "content": "检查温度传感器，校准控制系统",
            "operator": "张维护"
          },
          {
            "date": "2025-09-25",
            "type": "定期维护",
            "content": "清洁设备，更换过滤器",
            "operator": "李工程"
          }
        ],
        "created_at": "2024-01-15T10:00:00",
        "updated_at": "2025-10-30T10:00:00"
      },
      "timestamp": "2025-10-30T12:00:00Z"
    }',
    200,
    300,
    false,
    90
) ON CONFLICT DO NOTHING;

-- ========================================
-- 3. 模拟设备 - 实时数据
-- ========================================

INSERT INTO t_sys_mock_data (
    name, description, method, url_pattern, response_data, 
    response_code, delay, enabled, priority
) VALUES (
    '模拟设备-实时数据',
    '模拟设备的实时运行数据',
    'GET',
    '/api/v2/devices/100[1-5]/realtime',
    '{
      "success": true,
      "code": 200,
      "message": "获取实时数据成功",
      "data": {
        "device_id": 1001,
        "device_code": "SIM-DEV-001",
        "device_name": "模拟温控设备A",
        "timestamp": "2025-10-30T12:00:00Z",
        "status": "running",
        "online": true,
        "metrics": {
          "temperature": {
            "value": 45.8,
            "unit": "°C",
            "status": "normal",
            "threshold_min": 0,
            "threshold_max": 100
          },
          "pressure": {
            "value": 2.3,
            "unit": "MPa",
            "status": "normal",
            "threshold_min": 0,
            "threshold_max": 5
          },
          "flow_rate": {
            "value": 125.6,
            "unit": "L/min",
            "status": "normal",
            "threshold_min": 0,
            "threshold_max": 200
          },
          "power_consumption": {
            "value": 2.15,
            "unit": "kW",
            "status": "normal",
            "threshold_min": 0,
            "threshold_max": 3
          },
          "vibration": {
            "value": 0.8,
            "unit": "mm/s",
            "status": "normal",
            "threshold_min": 0,
            "threshold_max": 5
          },
          "efficiency": {
            "value": 92.5,
            "unit": "%",
            "status": "good"
          }
        },
        "alarms": [],
        "last_update": "2025-10-30T12:00:00Z"
      },
      "timestamp": "2025-10-30T12:00:00Z"
    }',
    200,
    200,
    false,
    100
) ON CONFLICT DO NOTHING;

-- ========================================
-- 4. 模拟设备 - 历史数据（前一天）
-- ========================================

INSERT INTO t_sys_mock_data (
    name, description, method, url_pattern, response_data, 
    response_code, delay, enabled, priority
) VALUES (
    '模拟设备-历史数据',
    '模拟设备前一天（2025-10-29）的24小时历史数据',
    'GET',
    '/api/v2/devices/100[1-5]/history',
    '{
      "success": true,
      "code": 200,
      "message": "获取历史数据成功",
      "data": {
        "device_id": 1001,
        "device_code": "SIM-DEV-001",
        "device_name": "模拟温控设备A",
        "date_range": {
          "start": "2025-10-29T00:00:00Z",
          "end": "2025-10-29T23:59:59Z"
        },
        "data_points": [
          {
            "timestamp": "2025-10-29T00:00:00Z",
            "temperature": 42.3,
            "pressure": 2.1,
            "flow_rate": 118.5,
            "power_consumption": 2.0,
            "vibration": 0.7,
            "efficiency": 91.2,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T01:00:00Z",
            "temperature": 43.1,
            "pressure": 2.15,
            "flow_rate": 120.3,
            "power_consumption": 2.05,
            "vibration": 0.75,
            "efficiency": 91.5,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T02:00:00Z",
            "temperature": 44.5,
            "pressure": 2.2,
            "flow_rate": 122.1,
            "power_consumption": 2.1,
            "vibration": 0.8,
            "efficiency": 91.8,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T03:00:00Z",
            "temperature": 45.2,
            "pressure": 2.25,
            "flow_rate": 123.7,
            "power_consumption": 2.12,
            "vibration": 0.78,
            "efficiency": 92.0,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T04:00:00Z",
            "temperature": 46.0,
            "pressure": 2.3,
            "flow_rate": 125.2,
            "power_consumption": 2.15,
            "vibration": 0.82,
            "efficiency": 92.3,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T05:00:00Z",
            "temperature": 45.8,
            "pressure": 2.28,
            "flow_rate": 124.8,
            "power_consumption": 2.14,
            "vibration": 0.79,
            "efficiency": 92.2,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T06:00:00Z",
            "temperature": 45.5,
            "pressure": 2.26,
            "flow_rate": 124.0,
            "power_consumption": 2.13,
            "vibration": 0.77,
            "efficiency": 92.1,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T07:00:00Z",
            "temperature": 46.2,
            "pressure": 2.32,
            "flow_rate": 126.1,
            "power_consumption": 2.16,
            "vibration": 0.83,
            "efficiency": 92.4,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T08:00:00Z",
            "temperature": 47.1,
            "pressure": 2.35,
            "flow_rate": 127.5,
            "power_consumption": 2.18,
            "vibration": 0.85,
            "efficiency": 92.6,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T09:00:00Z",
            "temperature": 47.8,
            "pressure": 2.38,
            "flow_rate": 128.9,
            "power_consumption": 2.2,
            "vibration": 0.87,
            "efficiency": 92.8,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T10:00:00Z",
            "temperature": 48.2,
            "pressure": 2.4,
            "flow_rate": 130.0,
            "power_consumption": 2.22,
            "vibration": 0.88,
            "efficiency": 93.0,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T11:00:00Z",
            "temperature": 48.5,
            "pressure": 2.42,
            "flow_rate": 131.2,
            "power_consumption": 2.24,
            "vibration": 0.9,
            "efficiency": 93.1,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T12:00:00Z",
            "temperature": 49.0,
            "pressure": 2.45,
            "flow_rate": 132.5,
            "power_consumption": 2.26,
            "vibration": 0.92,
            "efficiency": 93.3,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T13:00:00Z",
            "temperature": 48.8,
            "pressure": 2.43,
            "flow_rate": 131.8,
            "power_consumption": 2.25,
            "vibration": 0.91,
            "efficiency": 93.2,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T14:00:00Z",
            "temperature": 48.3,
            "pressure": 2.4,
            "flow_rate": 130.5,
            "power_consumption": 2.23,
            "vibration": 0.89,
            "efficiency": 93.0,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T15:00:00Z",
            "temperature": 47.9,
            "pressure": 2.38,
            "flow_rate": 129.2,
            "power_consumption": 2.21,
            "vibration": 0.87,
            "efficiency": 92.8,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T16:00:00Z",
            "temperature": 47.5,
            "pressure": 2.35,
            "flow_rate": 128.0,
            "power_consumption": 2.19,
            "vibration": 0.85,
            "efficiency": 92.6,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T17:00:00Z",
            "temperature": 46.8,
            "pressure": 2.32,
            "flow_rate": 126.5,
            "power_consumption": 2.17,
            "vibration": 0.83,
            "efficiency": 92.4,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T18:00:00Z",
            "temperature": 46.0,
            "pressure": 2.28,
            "flow_rate": 125.0,
            "power_consumption": 2.14,
            "vibration": 0.81,
            "efficiency": 92.2,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T19:00:00Z",
            "temperature": 45.3,
            "pressure": 2.25,
            "flow_rate": 123.5,
            "power_consumption": 2.12,
            "vibration": 0.79,
            "efficiency": 91.9,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T20:00:00Z",
            "temperature": 44.8,
            "pressure": 2.22,
            "flow_rate": 122.0,
            "power_consumption": 2.1,
            "vibration": 0.77,
            "efficiency": 91.7,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T21:00:00Z",
            "temperature": 44.2,
            "pressure": 2.19,
            "flow_rate": 120.8,
            "power_consumption": 2.08,
            "vibration": 0.75,
            "efficiency": 91.5,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T22:00:00Z",
            "temperature": 43.5,
            "pressure": 2.16,
            "flow_rate": 119.5,
            "power_consumption": 2.05,
            "vibration": 0.73,
            "efficiency": 91.3,
            "status": "running"
          },
          {
            "timestamp": "2025-10-29T23:00:00Z",
            "temperature": 42.8,
            "pressure": 2.13,
            "flow_rate": 118.2,
            "power_consumption": 2.02,
            "vibration": 0.71,
            "efficiency": 91.0,
            "status": "running"
          }
        ],
        "statistics": {
          "temperature": {
            "min": 42.3,
            "max": 49.0,
            "avg": 46.1,
            "unit": "°C"
          },
          "pressure": {
            "min": 2.1,
            "max": 2.45,
            "avg": 2.29,
            "unit": "MPa"
          },
          "flow_rate": {
            "min": 118.2,
            "max": 132.5,
            "avg": 125.4,
            "unit": "L/min"
          },
          "power_consumption": {
            "min": 2.0,
            "max": 2.26,
            "avg": 2.15,
            "unit": "kW"
          },
          "vibration": {
            "min": 0.7,
            "max": 0.92,
            "avg": 0.81,
            "unit": "mm/s"
          },
          "efficiency": {
            "min": 91.0,
            "max": 93.3,
            "avg": 92.2,
            "unit": "%"
          },
          "total_runtime": 24.0,
          "downtime": 0,
            "availability": 100.0
        }
      },
      "timestamp": "2025-10-30T12:00:00Z"
    }',
    200,
    500,
    false,
    100
) ON CONFLICT DO NOTHING;

-- ========================================
-- 5. 模拟设备 - 统计数据
-- ========================================

INSERT INTO t_sys_mock_data (
    name, description, method, url_pattern, response_data, 
    response_code, delay, enabled, priority
) VALUES (
    '模拟设备-统计数据',
    '模拟设备分类的统计数据',
    'GET',
    '/api/v2/devices/statistics.*device_type=simulation',
    '{
      "success": true,
      "code": 200,
      "message": "获取统计数据成功",
      "data": {
        "total_devices": 5,
        "online_devices": 4,
        "offline_devices": 0,
        "maintenance_devices": 1,
        "by_status": [
          {
            "status": "运行中",
            "count": 4,
            "percentage": 80.0
          },
          {
            "status": "维护中",
            "count": 1,
            "percentage": 20.0
          }
        ],
        "by_location": [
          {
            "location": "模拟车间-A区",
            "count": 1
          },
          {
            "location": "模拟车间-B区",
            "count": 1
          },
          {
            "location": "模拟车间-C区",
            "count": 1
          },
          {
            "location": "模拟车间-D区",
            "count": 1
          },
          {
            "location": "模拟车间-E区",
            "count": 1
          }
        ],
        "health_score": 95.8,
        "avg_efficiency": 92.3,
        "total_energy_consumption": 10.75,
        "avg_runtime_hours": 23.5
      },
      "timestamp": "2025-10-30T12:00:00Z"
    }',
    200,
    300,
    false,
    90
) ON CONFLICT DO NOTHING;

-- ========================================
-- 查看插入结果
-- ========================================

SELECT 
    id,
    name,
    url_pattern,
    method,
    response_code,
    enabled,
    priority,
    description
FROM t_sys_mock_data
WHERE description LIKE '%模拟设备%'
ORDER BY priority DESC, id;

-- 统计
SELECT 
    '模拟设备Mock规则数' as "统计项",
    COUNT(*) as "数量"
FROM t_sys_mock_data
WHERE description LIKE '%模拟设备%';

-- 完成提示
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ 模拟设备Mock规则插入完成！';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE '已插入的Mock规则:';
    RAISE NOTICE '  1. 模拟设备分类-设备列表 (5台设备)';
    RAISE NOTICE '  2. 模拟设备-详情信息';
    RAISE NOTICE '  3. 模拟设备-实时数据';
    RAISE NOTICE '  4. 模拟设备-历史数据 (2025-10-29全天24小时)';
    RAISE NOTICE '  5. 模拟设备-统计数据';
    RAISE NOTICE '';
    RAISE NOTICE '模拟设备包含:';
    RAISE NOTICE '  • SIM-DEV-001: 模拟温控设备A';
    RAISE NOTICE '  • SIM-DEV-002: 模拟压力监测设备B';
    RAISE NOTICE '  • SIM-DEV-003: 模拟流量计设备C';
    RAISE NOTICE '  • SIM-DEV-004: 模拟能耗监控设备D (维护中)';
    RAISE NOTICE '  • SIM-DEV-005: 模拟振动传感设备E';
    RAISE NOTICE '';
    RAISE NOTICE '数据内容:';
    RAISE NOTICE '  • 基础信息: 设备编号、型号、位置等';
    RAISE NOTICE '  • 实时数据: 温度、压力、流量、功耗、振动、效率';
    RAISE NOTICE '  • 历史数据: 2025-10-29 全天24小时数据点';
    RAISE NOTICE '  • 统计数据: 设备状态、位置分布、健康评分';
    RAISE NOTICE '';
    RAISE NOTICE '下一步操作:';
    RAISE NOTICE '  1. 刷新浏览器页面 (Ctrl + Shift + R)';
    RAISE NOTICE '  2. 访问: 高级设置 → Mock数据管理';
    RAISE NOTICE '  3. 启用对应的Mock规则';
    RAISE NOTICE '  4. 启用Mock全局开关';
    RAISE NOTICE '  5. 访问设备管理页面查看模拟设备';
    RAISE NOTICE '';
END $$;

