-- ========================================
-- Mock数据规则 - 系统核心API模拟数据
-- 生成时间: 2025-10-30
-- 说明: 包含认证、用户、菜单、角色、设备等核心API的Mock规则
-- ========================================

-- 清空现有Mock规则（可选，谨慎使用）
-- TRUNCATE TABLE t_sys_mock_data CASCADE;

-- 获取高级设置菜单ID
DO $$
DECLARE
    v_advanced_settings_id INTEGER;
BEGIN
    SELECT id INTO v_advanced_settings_id 
    FROM t_sys_menu 
    WHERE name = '高级设置';
    
    -- 确保Mock数据管理菜单的parent_id正确
    IF v_advanced_settings_id IS NOT NULL THEN
        UPDATE t_sys_menu 
        SET parent_id = v_advanced_settings_id 
        WHERE name = 'Mock数据管理' AND parent_id != v_advanced_settings_id;
    END IF;
END $$;

-- ========================================
-- 1. 认证相关Mock规则
-- ========================================

-- 1.1 用户登录成功
INSERT INTO t_sys_mock_data (name, url_pattern, method, response_status, response_data, delay, priority, enabled, description, created_at, updated_at)
VALUES (
    '登录成功Mock',
    '/api/v2/auth/login',
    'POST',
    200,
    '{
      "success": true,
      "code": 200,
      "message": "登录成功",
      "data": {
        "access_token": "mock_jwt_token_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        "refresh_token": "mock_refresh_token_abc123xyz",
        "token_type": "bearer",
        "expires_in": 604800,
        "user": {
          "id": 1,
          "username": "admin",
          "email": "admin@example.com",
          "isActive": true,
          "isSuperuser": true,
          "last_login": "2025-10-30T12:00:00",
          "created_at": "2024-01-01T00:00:00"
        }
      },
      "timestamp": "2025-10-30T12:00:00Z"
    }',
    300,
    100,
    false,
    '模拟用户登录成功场景',
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- 1.2 登录失败 - 密码错误
INSERT INTO t_sys_mock_data (name, url_pattern, method, response_status, response_data, delay, priority, enabled, description, created_at, updated_at)
VALUES (
    '登录失败-密码错误',
    '/api/v2/auth/login',
    'POST',
    401,
    '{
      "success": false,
      "code": 401,
      "message": "用户名或密码错误",
      "error": {
        "type": "AUTHENTICATION_ERROR",
        "details": "Invalid credentials"
      },
      "timestamp": "2025-10-30T12:00:00Z"
    }',
    200,
    90,
    false,
    '模拟登录失败场景',
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- 1.3 获取当前用户信息
INSERT INTO t_sys_mock_data (name, url_pattern, method, response_status, response_data, delay, priority, enabled, description, created_at, updated_at)
VALUES (
    '获取用户信息Mock',
    '/api/v2/auth/user',
    'GET',
    200,
    '{
      "success": true,
      "code": 200,
      "message": "获取用户信息成功",
      "data": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "nickName": "系统管理员",
        "phone": "13800138000",
        "isActive": true,
        "isSuperuser": true,
        "avatar": "/static/avatars/default.png",
        "dept": {
          "id": 1,
          "name": "技术部"
        },
        "roles": [
          {
            "id": 1,
            "name": "超级管理员",
            "description": "系统超级管理员"
          }
        ],
        "last_login": "2025-10-30T12:00:00",
        "created_at": "2024-01-01T00:00:00"
      },
      "timestamp": "2025-10-30T12:00:00Z"
    }',
    200,
    100,
    false,
    '模拟获取当前用户信息',
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- ========================================
-- 2. 用户管理Mock规则
-- ========================================

-- 2.1 获取用户列表
INSERT INTO t_sys_mock_data (name, url_pattern, method, response_status, response_data, delay, priority, enabled, description, created_at, updated_at)
VALUES (
    '用户列表Mock',
    '/api/v2/users.*',
    'GET',
    200,
    '{
      "success": true,
      "code": 200,
      "message": "获取用户列表成功",
      "data": {
        "items": [
          {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "nickName": "超级管理员",
            "phone": "13800138000",
            "isActive": true,
            "isSuperuser": true,
            "dept": {"id": 1, "name": "技术部"},
            "roles": [{"id": 1, "name": "超级管理员"}],
            "created_at": "2024-01-01T00:00:00"
          },
          {
            "id": 2,
            "username": "user001",
            "email": "user001@example.com",
            "nickName": "测试用户1",
            "phone": "13800138001",
            "isActive": true,
            "isSuperuser": false,
            "dept": {"id": 2, "name": "测试部"},
            "roles": [{"id": 2, "name": "普通用户"}],
            "created_at": "2024-02-01T00:00:00"
          },
          {
            "id": 3,
            "username": "user002",
            "email": "user002@example.com",
            "nickName": "测试用户2",
            "phone": "13800138002",
            "isActive": true,
            "isSuperuser": false,
            "dept": {"id": 2, "name": "测试部"},
            "roles": [{"id": 2, "name": "普通用户"}],
            "created_at": "2024-03-01T00:00:00"
          }
        ],
        "total": 3,
        "page": 1,
        "pageSize": 20,
        "totalPages": 1
      },
      "timestamp": "2025-10-30T12:00:00Z"
    }',
    400,
    80,
    false,
    '模拟用户列表查询',
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- ========================================
-- 3. 菜单管理Mock规则
-- ========================================

-- 3.1 获取用户菜单
INSERT INTO t_sys_mock_data (name, url_pattern, method, response_status, response_data, delay, priority, enabled, description, created_at, updated_at)
VALUES (
    '用户菜单Mock',
    '/api/v2/base/usermenu',
    'GET',
    200,
    '{
      "success": true,
      "code": 200,
      "message": "获取用户菜单成功",
      "data": [
        {
          "id": 1,
          "name": "工作台",
          "path": "/workbench",
          "component": "workbench/index",
          "icon": "dashboard",
          "sort": 1,
          "meta": {
            "title": "工作台",
            "icon": "dashboard",
            "order": 1
          }
        },
        {
          "id": 2,
          "name": "设备管理",
          "path": "/device",
          "icon": "devices",
          "sort": 2,
          "children": [
            {
              "id": 21,
              "name": "设备列表",
              "path": "/device/list",
              "component": "device/list/index",
              "icon": "list",
              "sort": 1
            },
            {
              "id": 22,
              "name": "设备监控",
              "path": "/device/monitor",
              "component": "device/monitor/index",
              "icon": "monitor",
              "sort": 2
            }
          ]
        },
        {
          "id": 3,
          "name": "系统设置",
          "path": "/system",
          "icon": "settings",
          "sort": 10,
          "children": [
            {
              "id": 31,
              "name": "用户管理",
              "path": "/system/user",
              "component": "system/user/index",
              "icon": "user",
              "sort": 1
            },
            {
              "id": 32,
              "name": "角色管理",
              "path": "/system/role",
              "component": "system/role/index",
              "icon": "role",
              "sort": 2
            },
            {
              "id": 33,
              "name": "菜单管理",
              "path": "/system/menu",
              "component": "system/menu/index",
              "icon": "menu",
              "sort": 3
            }
          ]
        }
      ],
      "timestamp": "2025-10-30T12:00:00Z"
    }',
    300,
    100,
    false,
    '模拟获取用户菜单树',
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- 3.2 获取菜单列表
INSERT INTO t_sys_mock_data (name, url_pattern, method, response_status, response_data, delay, priority, enabled, description, created_at, updated_at)
VALUES (
    '菜单列表Mock',
    '/api/v2/menus.*',
    'GET',
    200,
    '{
      "success": true,
      "code": 200,
      "message": "获取菜单列表成功",
      "data": {
        "items": [
          {
            "id": 1,
            "name": "工作台",
            "path": "/workbench",
            "component": "workbench/index",
            "icon": "dashboard",
            "parent_id": 0,
            "sort": 1,
            "menu_type": "menu",
            "is_hidden": false
          },
          {
            "id": 2,
            "name": "设备管理",
            "path": "/device",
            "icon": "devices",
            "parent_id": 0,
            "sort": 2,
            "menu_type": "catalog",
            "is_hidden": false
          }
        ],
        "total": 2,
        "page": 1,
        "pageSize": 20
      },
      "timestamp": "2025-10-30T12:00:00Z"
    }',
    350,
    80,
    false,
    '模拟菜单列表查询',
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- ========================================
-- 4. 角色管理Mock规则
-- ========================================

-- 4.1 获取角色列表
INSERT INTO t_sys_mock_data (name, url_pattern, method, response_status, response_data, delay, priority, enabled, description, created_at, updated_at)
VALUES (
    '角色列表Mock',
    '/api/v2/roles.*',
    'GET',
    200,
    '{
      "success": true,
      "code": 200,
      "message": "获取角色列表成功",
      "data": {
        "items": [
          {
            "id": 1,
            "name": "超级管理员",
            "description": "系统超级管理员，拥有所有权限",
            "is_active": true,
            "user_count": 1,
            "menu_count": 20,
            "api_count": 100,
            "created_at": "2024-01-01T00:00:00"
          },
          {
            "id": 2,
            "name": "普通用户",
            "description": "普通系统用户",
            "is_active": true,
            "user_count": 10,
            "menu_count": 10,
            "api_count": 30,
            "created_at": "2024-01-01T00:00:00"
          },
          {
            "id": 3,
            "name": "设备管理员",
            "description": "设备管理相关权限",
            "is_active": true,
            "user_count": 3,
            "menu_count": 8,
            "api_count": 40,
            "created_at": "2024-02-01T00:00:00"
          }
        ],
        "total": 3,
        "page": 1,
        "pageSize": 20
      },
      "timestamp": "2025-10-30T12:00:00Z"
    }',
    400,
    80,
    false,
    '模拟角色列表查询',
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- ========================================
-- 5. 设备管理Mock规则
-- ========================================

-- 5.1 获取设备列表
INSERT INTO t_sys_mock_data (name, url_pattern, method, response_status, response_data, delay, priority, enabled, description, created_at, updated_at)
VALUES (
    '设备列表Mock',
    '/api/v2/devices.*',
    'GET',
    200,
    '{
      "success": true,
      "code": 200,
      "message": "获取设备列表成功",
      "data": {
        "items": [
          {
            "id": 1,
            "device_code": "DEV-001",
            "device_name": "生产设备A",
            "device_type": "生产设备",
            "manufacturer": "XX制造商",
            "device_model": "Model-A1",
            "install_location": "车间A-101",
            "status": "运行中",
            "is_locked": false,
            "online_address": "192.168.1.101",
            "team_name": "生产一组",
            "created_at": "2024-01-01T00:00:00"
          },
          {
            "id": 2,
            "device_code": "DEV-002",
            "device_name": "生产设备B",
            "device_type": "生产设备",
            "manufacturer": "YY制造商",
            "device_model": "Model-B2",
            "install_location": "车间A-102",
            "status": "维护中",
            "is_locked": true,
            "online_address": "192.168.1.102",
            "team_name": "生产二组",
            "created_at": "2024-01-15T00:00:00"
          },
          {
            "id": 3,
            "device_code": "DEV-003",
            "device_name": "检测设备C",
            "device_type": "检测设备",
            "manufacturer": "ZZ制造商",
            "device_model": "Model-C3",
            "install_location": "检测室",
            "status": "运行中",
            "is_locked": false,
            "online_address": "192.168.1.103",
            "team_name": "质检组",
            "created_at": "2024-02-01T00:00:00"
          }
        ],
        "total": 3,
        "page": 1,
        "pageSize": 20,
        "totalPages": 1
      },
      "timestamp": "2025-10-30T12:00:00Z"
    }',
    500,
    80,
    false,
    '模拟设备列表查询',
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- 5.2 获取设备统计
INSERT INTO t_sys_mock_data (name, url_pattern, method, response_status, response_data, delay, priority, enabled, description, created_at, updated_at)
VALUES (
    '设备统计Mock',
    '/api/v2/devices/statistics',
    'GET',
    200,
    '{
      "success": true,
      "code": 200,
      "message": "获取设备统计成功",
      "data": {
        "total": 150,
        "online": 120,
        "offline": 20,
        "maintenance": 10,
        "by_type": [
          {"type": "生产设备", "count": 80},
          {"type": "检测设备", "count": 30},
          {"type": "辅助设备", "count": 40}
        ],
        "by_status": [
          {"status": "运行中", "count": 120},
          {"status": "停机", "count": 20},
          {"status": "维护中", "count": 10}
        ],
        "health_score": 85.5
      },
      "timestamp": "2025-10-30T12:00:00Z"
    }',
    300,
    90,
    false,
    '模拟设备统计数据',
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- ========================================
-- 6. 系统参数Mock规则
-- ========================================

-- 6.1 获取系统参数
INSERT INTO t_sys_mock_data (name, url_pattern, method, response_status, response_data, delay, priority, enabled, description, created_at, updated_at)
VALUES (
    '系统参数Mock',
    '/api/v2/system-params.*',
    'GET',
    200,
    '{
      "success": true,
      "code": 200,
      "message": "获取系统参数成功",
      "data": {
        "param_key": "SYSTEM_NAME",
        "param_value": "设备监控系统",
        "param_type": "string",
        "description": "系统名称",
        "is_enabled": true
      },
      "timestamp": "2025-10-30T12:00:00Z"
    }',
    200,
    70,
    false,
    '模拟系统参数查询',
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- ========================================
-- 7. 错误场景Mock规则
-- ========================================

-- 7.1 模拟网络超时
INSERT INTO t_sys_mock_data (name, url_pattern, method, response_status, response_data, delay, priority, enabled, description, created_at, updated_at)
VALUES (
    '网络超时Mock',
    '/api/v2/test/timeout',
    'GET',
    504,
    '{
      "success": false,
      "code": 504,
      "message": "请求超时",
      "error": {
        "type": "TIMEOUT_ERROR",
        "details": "Request timeout after 10 seconds"
      },
      "timestamp": "2025-10-30T12:00:00Z"
    }',
    10000,
    100,
    false,
    '模拟网络超时场景',
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- 7.2 模拟服务器错误
INSERT INTO t_sys_mock_data (name, url_pattern, method, response_status, response_data, delay, priority, enabled, description, created_at, updated_at)
VALUES (
    '服务器错误Mock',
    '/api/v2/test/error',
    'GET',
    500,
    '{
      "success": false,
      "code": 500,
      "message": "服务器内部错误",
      "error": {
        "type": "INTERNAL_SERVER_ERROR",
        "details": "An unexpected error occurred"
      },
      "timestamp": "2025-10-30T12:00:00Z"
    }',
    200,
    100,
    false,
    '模拟服务器错误场景',
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- 7.3 模拟权限不足
INSERT INTO t_sys_mock_data (name, url_pattern, method, response_status, response_data, delay, priority, enabled, description, created_at, updated_at)
VALUES (
    '权限不足Mock',
    '/api/v2/test/forbidden',
    'GET',
    403,
    '{
      "success": false,
      "code": 403,
      "message": "没有权限访问该资源",
      "error": {
        "type": "PERMISSION_DENIED",
        "details": "Insufficient permissions"
      },
      "timestamp": "2025-10-30T12:00:00Z"
    }',
    200,
    100,
    false,
    '模拟权限不足场景',
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- ========================================
-- 8. 特殊场景Mock规则
-- ========================================

-- 8.1 模拟数据加载中
INSERT INTO t_sys_mock_data (name, url_pattern, method, response_status, response_data, delay, priority, enabled, description, created_at, updated_at)
VALUES (
    '数据加载中Mock',
    '/api/v2/test/loading',
    'GET',
    200,
    '{
      "success": true,
      "code": 200,
      "message": "数据加载中",
      "data": {
        "status": "loading",
        "progress": 50,
        "message": "正在加载数据..."
      },
      "timestamp": "2025-10-30T12:00:00Z"
    }',
    3000,
    100,
    false,
    '模拟数据加载中的场景（3秒延迟）',
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- 8.2 模拟空数据
INSERT INTO t_sys_mock_data (name, url_pattern, method, response_status, response_data, delay, priority, enabled, description, created_at, updated_at)
VALUES (
    '空数据Mock',
    '/api/v2/test/empty',
    'GET',
    200,
    '{
      "success": true,
      "code": 200,
      "message": "查询成功",
      "data": {
        "items": [],
        "total": 0,
        "page": 1,
        "pageSize": 20
      },
      "timestamp": "2025-10-30T12:00:00Z"
    }',
    200,
    100,
    false,
    '模拟空数据场景',
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- ========================================
-- 查看插入结果
-- ========================================

SELECT 
    id,
    name,
    url_pattern,
    method,
    response_status,
    enabled,
    priority,
    hit_count,
    description
FROM t_sys_mock_data
ORDER BY priority DESC, id;

-- 统计
SELECT 
    '总Mock规则数' as "统计项",
    COUNT(*) as "数量"
FROM t_sys_mock_data
UNION ALL
SELECT 
    '已启用规则数',
    COUNT(*)
FROM t_sys_mock_data
WHERE enabled = true
UNION ALL
SELECT 
    '已禁用规则数',
    COUNT(*)
FROM t_sys_mock_data
WHERE enabled = false;

-- 完成提示
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ Mock规则插入完成！';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE '下一步操作:';
    RAISE NOTICE '1. 刷新浏览器页面 (Ctrl + Shift + R)';
    RAISE NOTICE '2. 访问: 高级设置 → Mock数据管理';
    RAISE NOTICE '3. 查看已插入的Mock规则';
    RAISE NOTICE '4. 根据需要启用对应的规则';
    RAISE NOTICE '';
    RAISE NOTICE '注意:';
    RAISE NOTICE '- 所有规则默认为禁用状态 (enabled=false)';
    RAISE NOTICE '- 使用前需要在页面上启用对应的规则';
    RAISE NOTICE '- 测试完成后记得禁用Mock功能';
    RAISE NOTICE '';
END $$;

