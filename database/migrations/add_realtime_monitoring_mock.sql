-- ========================================
-- 添加设备实时监测Mock规则
-- 用于设备实时监测页面 (/api/v2/devices/realtime/monitoring)
-- ========================================

-- 插入实时监测Mock规则
INSERT INTO t_sys_mock_data (
    name, 
    description, 
    method, 
    url_pattern, 
    response_data, 
    response_code, 
    delay, 
    enabled, 
    priority
) VALUES (
    '模拟设备-实时监测数据',
    '设备实时监测页面的实时数据（包含所有模拟设备）',
    'GET',
    '/api/v2/devices/realtime/monitoring',
    '{
      "success": true,
      "code": 200,
      "message": "获取实时监测数据成功",
      "data": {
        "items": [
          {
            "device_id": 1001,
            "device_code": "SIM-DEV-001",
            "device_name": "模拟温控设备A",
            "device_type": "simulation",
            "install_location": "模拟车间-A区",
            "status": "运行中",
            "online": true,
            "timestamp": "2025-10-30T14:00:00Z",
            "realtime_data": {
              "temperature": 45.8,
              "pressure": 2.3,
              "flow_rate": 125.6,
              "power_consumption": 2.15,
              "vibration": 0.8,
              "efficiency": 92.5,
              "voltage": 220.5,
              "current": 9.8,
              "runtime_hours": 1256.5
            },
            "health_status": "良好",
            "health_score": 95.8,
            "last_maintenance": "2025-10-25",
            "next_maintenance": "2025-11-25",
            "alarms": []
          },
          {
            "device_id": 1002,
            "device_code": "SIM-DEV-002",
            "device_name": "模拟压力监测设备B",
            "device_type": "simulation",
            "install_location": "模拟车间-B区",
            "status": "运行中",
            "online": true,
            "timestamp": "2025-10-30T14:00:00Z",
            "realtime_data": {
              "temperature": 48.2,
              "pressure": 2.8,
              "flow_rate": 135.2,
              "power_consumption": 2.35,
              "vibration": 0.95,
              "efficiency": 93.2,
              "voltage": 220.8,
              "current": 10.7,
              "runtime_hours": 1180.3
            },
            "health_status": "良好",
            "health_score": 96.2,
            "last_maintenance": "2025-10-20",
            "next_maintenance": "2025-11-20",
            "alarms": []
          },
          {
            "device_id": 1003,
            "device_code": "SIM-DEV-003",
            "device_name": "模拟流量计设备C",
            "device_type": "simulation",
            "install_location": "模拟车间-C区",
            "status": "运行中",
            "online": true,
            "timestamp": "2025-10-30T14:00:00Z",
            "realtime_data": {
              "temperature": 42.5,
              "pressure": 2.1,
              "flow_rate": 142.8,
              "power_consumption": 2.05,
              "vibration": 0.72,
              "efficiency": 94.1,
              "voltage": 220.2,
              "current": 9.3,
              "runtime_hours": 1305.7
            },
            "health_status": "优秀",
            "health_score": 97.5,
            "last_maintenance": "2025-10-22",
            "next_maintenance": "2025-11-22",
            "alarms": []
          },
          {
            "device_id": 1004,
            "device_code": "SIM-DEV-004",
            "device_name": "模拟能耗监控设备D",
            "device_type": "simulation",
            "install_location": "模拟车间-D区",
            "status": "维护中",
            "online": false,
            "timestamp": "2025-10-30T14:00:00Z",
            "realtime_data": {
              "temperature": 0,
              "pressure": 0,
              "flow_rate": 0,
              "power_consumption": 0,
              "vibration": 0,
              "efficiency": 0,
              "voltage": 0,
              "current": 0,
              "runtime_hours": 985.2
            },
            "health_status": "维护中",
            "health_score": 0,
            "last_maintenance": "2025-10-28",
            "next_maintenance": "2025-11-28",
            "alarms": [
              {
                "level": "info",
                "message": "设备正在进行定期维护",
                "timestamp": "2025-10-28T10:00:00Z"
              }
            ]
          },
          {
            "device_id": 1005,
            "device_code": "SIM-DEV-005",
            "device_name": "模拟振动传感设备E",
            "device_type": "simulation",
            "install_location": "模拟车间-E区",
            "status": "运行中",
            "online": true,
            "timestamp": "2025-10-30T14:00:00Z",
            "realtime_data": {
              "temperature": 46.5,
              "pressure": 2.4,
              "flow_rate": 128.3,
              "power_consumption": 2.18,
              "vibration": 0.85,
              "efficiency": 92.8,
              "voltage": 220.6,
              "current": 9.9,
              "runtime_hours": 1425.8
            },
            "health_status": "良好",
            "health_score": 96.0,
            "last_maintenance": "2025-10-18",
            "next_maintenance": "2025-11-18",
            "alarms": []
          }
        ],
        "total": 5,
        "online_count": 4,
        "offline_count": 1,
        "summary": {
          "total_devices": 5,
          "online_devices": 4,
          "offline_devices": 1,
          "maintenance_devices": 1,
          "avg_efficiency": 92.9,
          "avg_health_score": 97.1,
          "total_power_consumption": 8.73,
          "alarm_count": 1
        }
      },
      "timestamp": "2025-10-30T14:00:00Z"
    }',
    200,
    300,
    false,
    100
) ON CONFLICT DO NOTHING;

-- 验证插入
SELECT 
    id,
    name,
    url_pattern,
    method,
    enabled,
    description
FROM t_sys_mock_data
WHERE name = '模拟设备-实时监测数据';

-- 完成提示
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ 实时监测Mock规则插入完成！';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE '新增规则:';
    RAISE NOTICE '  • 模拟设备-实时监测数据';
    RAISE NOTICE '  • URL: /api/v2/devices/realtime/monitoring';
    RAISE NOTICE '  • 包含5台设备的实时数据';
    RAISE NOTICE '';
    RAISE NOTICE '下一步操作:';
    RAISE NOTICE '  1. 刷新Mock管理页面';
    RAISE NOTICE '  2. 启用"模拟设备-实时监测数据"规则';
    RAISE NOTICE '  3. 访问设备实时监测页面查看效果';
    RAISE NOTICE '';
END $$;

