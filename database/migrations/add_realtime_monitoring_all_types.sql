-- ========================================
-- 添加包含多种设备类型的实时监测Mock规则
-- 支持 welding, test2, simulation 等多种类型
-- ========================================

-- 更新实时监测Mock规则，包含多种设备类型
-- 如果规则已存在，先删除
DELETE FROM t_sys_mock_data WHERE name = '模拟设备-实时监测数据（多类型）';

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
    '模拟设备-实时监测数据（多类型）',
    '设备实时监测页面的实时数据（包含welding、test2、simulation等类型）',
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
            "device_type_name": "模拟设备",
            "install_location": "模拟车间-A区",
            "status": "运行中",
            "online": true,
            "timestamp": "2025-10-30T15:00:00Z",
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
            "device_id": 2001,
            "device_code": "WELD-001",
            "device_name": "焊接设备1号",
            "device_type": "welding",
            "device_type_name": "焊接设备",
            "install_location": "焊接车间-A区",
            "status": "运行中",
            "online": true,
            "timestamp": "2025-10-30T15:00:00Z",
            "realtime_data": {
              "temperature": 850.2,
              "pressure": 0.8,
              "welding_current": 180.5,
              "welding_voltage": 28.3,
              "wire_speed": 8.5,
              "gas_flow": 15.2,
              "power_consumption": 12.5,
              "efficiency": 88.5,
              "runtime_hours": 2156.3
            },
            "health_status": "良好",
            "health_score": 92.3,
            "last_maintenance": "2025-10-15",
            "next_maintenance": "2025-11-15",
            "alarms": []
          },
          {
            "device_id": 2002,
            "device_code": "WELD-002",
            "device_name": "焊接设备2号",
            "device_type": "welding",
            "device_type_name": "焊接设备",
            "install_location": "焊接车间-B区",
            "status": "运行中",
            "online": true,
            "timestamp": "2025-10-30T15:00:00Z",
            "realtime_data": {
              "temperature": 865.8,
              "pressure": 0.85,
              "welding_current": 195.2,
              "welding_voltage": 29.8,
              "wire_speed": 9.2,
              "gas_flow": 16.5,
              "power_consumption": 13.8,
              "efficiency": 90.2,
              "runtime_hours": 2305.7
            },
            "health_status": "优秀",
            "health_score": 95.1,
            "last_maintenance": "2025-10-12",
            "next_maintenance": "2025-11-12",
            "alarms": []
          },
          {
            "device_id": 3001,
            "device_code": "TEST2-001",
            "device_name": "测试设备2-001",
            "device_type": "test2",
            "device_type_name": "测试设备2",
            "install_location": "测试车间-A区",
            "status": "运行中",
            "online": true,
            "timestamp": "2025-10-30T15:00:00Z",
            "realtime_data": {
              "temperature": 38.5,
              "pressure": 1.5,
              "flow_rate": 95.3,
              "power_consumption": 1.85,
              "vibration": 0.65,
              "efficiency": 91.2,
              "voltage": 220.3,
              "current": 8.4,
              "runtime_hours": 856.2
            },
            "health_status": "良好",
            "health_score": 93.5,
            "last_maintenance": "2025-10-20",
            "next_maintenance": "2025-11-20",
            "alarms": []
          },
          {
            "device_id": 3002,
            "device_code": "TEST2-002",
            "device_name": "测试设备2-002",
            "device_type": "test2",
            "device_type_name": "测试设备2",
            "install_location": "测试车间-B区",
            "status": "待机",
            "online": true,
            "timestamp": "2025-10-30T15:00:00Z",
            "realtime_data": {
              "temperature": 25.2,
              "pressure": 0,
              "flow_rate": 0,
              "power_consumption": 0.15,
              "vibration": 0.05,
              "efficiency": 0,
              "voltage": 220.1,
              "current": 0.7,
              "runtime_hours": 652.8
            },
            "health_status": "待机",
            "health_score": 100,
            "last_maintenance": "2025-10-18",
            "next_maintenance": "2025-11-18",
            "alarms": []
          }
        ],
        "total": 5,
        "online_count": 5,
        "offline_count": 0,
        "summary": {
          "total_devices": 5,
          "online_devices": 5,
          "offline_devices": 0,
          "maintenance_devices": 0,
          "avg_efficiency": 72.5,
          "avg_health_score": 95.3,
          "total_power_consumption": 30.43,
          "alarm_count": 0
        }
      },
      "timestamp": "2025-10-30T15:00:00Z"
    }',
    200,
    300,
    false,
    110
) ON CONFLICT DO NOTHING;

-- 删除旧的单一类型规则（如果存在）
UPDATE t_sys_mock_data 
SET enabled = false, 
    priority = 50,
    description = description || ' [已废弃，请使用多类型版本]'
WHERE name = '模拟设备-实时监测数据' 
  AND name != '模拟设备-实时监测数据（多类型）';

-- 验证插入
SELECT 
    id,
    name,
    url_pattern,
    method,
    enabled,
    priority,
    description
FROM t_sys_mock_data
WHERE name LIKE '%实时监测%'
ORDER BY priority DESC;

-- 完成提示
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ 多类型实时监测Mock规则更新完成！';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE '新增/更新规则:';
    RAISE NOTICE '  • 模拟设备-实时监测数据（多类型）';
    RAISE NOTICE '  • URL: /api/v2/devices/realtime/monitoring';
    RAISE NOTICE '  • 优先级: 110（高于单类型版本）';
    RAISE NOTICE '';
    RAISE NOTICE '包含设备类型:';
    RAISE NOTICE '  • simulation (模拟设备) - 1台';
    RAISE NOTICE '  • welding (焊接设备) - 2台';
    RAISE NOTICE '  • test2 (测试设备2) - 2台';
    RAISE NOTICE '';
    RAISE NOTICE '设备状态:';
    RAISE NOTICE '  • 运行中: 4台';
    RAISE NOTICE '  • 待机: 1台';
    RAISE NOTICE '';
    RAISE NOTICE '下一步操作:';
    RAISE NOTICE '  1. 刷新Mock管理页面';
    RAISE NOTICE '  2. 禁用旧规则"模拟设备-实时监测数据"（如果存在）';
    RAISE NOTICE '  3. 启用新规则"模拟设备-实时监测数据（多类型）"';
    RAISE NOTICE '  4. 访问设备实时监测页面';
    RAISE NOTICE '  5. 现在任何设备类型筛选都能看到对应数据！';
    RAISE NOTICE '';
END $$;

