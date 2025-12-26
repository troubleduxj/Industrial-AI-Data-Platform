-- =====================================================
-- AI预测管理Mock规则
-- =====================================================
-- 文件: 004_insert_ai_prediction_mock_rules.sql
-- 目的: 为AI预测管理API接口添加Mock数据配置
-- 创建时间: 2025-11-05
-- =====================================================

BEGIN;

-- 删除旧的AI预测相关Mock规则（如果存在）
DELETE FROM t_sys_mock_data 
WHERE url_pattern LIKE '%/ai-monitor/predictions%'
   OR url_pattern LIKE '%/ai/trend-prediction%';

-- =====================================================
-- 1. 批量创建预测任务 Mock
-- =====================================================

INSERT INTO t_sys_mock_data (
    name, description, method, url_pattern, response_data, response_code, 
    delay, enabled, priority, creator_id, creator_name, created_at, updated_at
) VALUES (
    'AI预测-批量创建预测任务',
    '模拟批量创建多个设备的预测任务，返回创建成功的预测列表',
    'POST',
    '/api/v2/ai-monitor/predictions/batch',
    '{
        "success": true,
        "code": 201,
        "message": "批量预测任务创建完成，成功 3 个，失败 0 个",
        "data": {
            "predictions": [
                {
                    "id": 1,
                    "prediction_name": "WLD-001-temperature-预测-24h",
                    "device_code": "WLD-001",
                    "device_name": "焊接设备01",
                    "metric_name": "temperature",
                    "status": "pending",
                    "progress": 0,
                    "prediction_horizon": 24,
                    "model_type": "ARIMA",
                    "created_at": "2025-11-05T10:00:00Z"
                },
                {
                    "id": 2,
                    "prediction_name": "WLD-002-temperature-预测-24h",
                    "device_code": "WLD-002",
                    "device_name": "焊接设备02",
                    "metric_name": "temperature",
                    "status": "pending",
                    "progress": 0,
                    "prediction_horizon": 24,
                    "model_type": "ARIMA",
                    "created_at": "2025-11-05T10:00:10Z"
                },
                {
                    "id": 3,
                    "prediction_name": "WLD-003-temperature-预测-24h",
                    "device_code": "WLD-003",
                    "device_name": "焊接设备03",
                    "metric_name": "temperature",
                    "status": "pending",
                    "progress": 0,
                    "prediction_horizon": 24,
                    "model_type": "ARIMA",
                    "created_at": "2025-11-05T10:00:20Z"
                }
            ],
            "total": 3,
            "successful": 3,
            "failed": 0,
            "failed_devices": []
        }
    }'::jsonb,
    201,
    500,
    true,
    100,
    1,
    'admin',
    NOW(),
    NOW()
);

-- =====================================================
-- 2. 查询预测历史 Mock
-- =====================================================

INSERT INTO t_sys_mock_data (
    name, description, method, url_pattern, response_data, response_code, 
    delay, enabled, priority, creator_id, creator_name, created_at, updated_at
) VALUES (
    'AI预测-查询设备预测历史',
    '模拟查询指定设备的预测历史记录，支持分页',
    'GET',
    '/api/v2/ai-monitor/predictions/history',
    '{
        "success": true,
        "code": 200,
        "message": "成功查询到 5 条预测历史记录",
        "data": {
            "items": [
                {
                    "id": 1,
                    "prediction_name": "WLD-001-temperature-预测-24h",
                    "device_code": "WLD-001",
                    "device_name": "焊接设备01",
                    "metric_name": "temperature",
                    "status": "completed",
                    "progress": 100,
                    "prediction_horizon": 24,
                    "model_type": "ARIMA",
                    "accuracy_score": 0.92,
                    "created_at": "2025-11-05T10:00:00Z",
                    "completed_at": "2025-11-05T10:05:00Z"
                },
                {
                    "id": 2,
                    "prediction_name": "WLD-001-pressure-预测-24h",
                    "device_code": "WLD-001",
                    "device_name": "焊接设备01",
                    "metric_name": "pressure",
                    "status": "completed",
                    "progress": 100,
                    "prediction_horizon": 24,
                    "model_type": "ARIMA",
                    "accuracy_score": 0.88,
                    "created_at": "2025-11-04T10:00:00Z",
                    "completed_at": "2025-11-04T10:05:00Z"
                }
            ],
            "total": 5,
            "page": 1,
            "page_size": 20,
            "pages": 1
        }
    }'::jsonb,
    200,
    300,
    true,
    100,
    1,
    'admin',
    NOW(),
    NOW()
);

-- =====================================================
-- 3. 获取预测列表 Mock
-- =====================================================

INSERT INTO t_sys_mock_data (
    name, description, method, url_pattern, response_data, response_code, 
    delay, enabled, priority, creator_id, creator_name, created_at, updated_at
) VALUES (
    'AI预测-获取预测列表',
    '模拟获取所有预测任务列表，支持筛选和分页',
    'GET',
    '/api/v2/ai-monitor/predictions',
    '{
        "success": true,
        "code": 200,
        "message": "获取预测列表成功",
        "data": {
            "items": [
                {
                    "id": 1,
                    "prediction_name": "WLD-001-temperature-预测-24h",
                    "device_code": "WLD-001",
                    "metric_name": "temperature",
                    "status": "completed",
                    "progress": 100,
                    "accuracy_score": 0.92
                },
                {
                    "id": 2,
                    "prediction_name": "WLD-002-temperature-预测-24h",
                    "device_code": "WLD-002",
                    "metric_name": "temperature",
                    "status": "running",
                    "progress": 65,
                    "accuracy_score": null
                },
                {
                    "id": 3,
                    "prediction_name": "WLD-003-pressure-预测-48h",
                    "device_code": "WLD-003",
                    "metric_name": "pressure",
                    "status": "pending",
                    "progress": 0,
                    "accuracy_score": null
                }
            ],
            "total": 15,
            "page": 1,
            "page_size": 20,
            "pages": 1
        }
    }'::jsonb,
    200,
    200,
    true,
    100,
    1,
    'admin',
    NOW(),
    NOW()
);

-- =====================================================
-- 4. 获取预测详情 Mock
-- =====================================================

INSERT INTO t_sys_mock_data (
    name, description, method, url_pattern, response_data, response_code, 
    delay, enabled, priority, creator_id, creator_name, created_at, updated_at
) VALUES (
    'AI预测-获取预测详情',
    '模拟获取单个预测任务的详细信息，包含完整的预测结果数据',
    'GET',
    '/api/v2/ai-monitor/predictions/*',
    '{
        "success": true,
        "code": 200,
        "message": "获取预测详情成功",
        "data": {
            "id": 1,
            "prediction_name": "WLD-001-temperature-预测-24h",
            "description": "设备WLD-001的temperature指标24小时预测",
            "device_code": "WLD-001",
            "device_name": "焊接设备01",
            "metric_name": "temperature",
            "target_variable": "temperature",
            "prediction_horizon": 24,
            "model_type": "ARIMA",
            "status": "completed",
            "progress": 100,
            "accuracy_score": 0.92,
            "result_data": {
                "predictions": [
                    {"time": "2025-11-05T11:00:00Z", "value": 85.2, "confidence": 0.92, "lower_bound": 82.5, "upper_bound": 87.9},
                    {"time": "2025-11-05T12:00:00Z", "value": 86.1, "confidence": 0.91, "lower_bound": 83.3, "upper_bound": 88.9},
                    {"time": "2025-11-05T13:00:00Z", "value": 87.3, "confidence": 0.89, "lower_bound": 84.5, "upper_bound": 90.1},
                    {"time": "2025-11-05T14:00:00Z", "value": 88.5, "confidence": 0.88, "lower_bound": 85.6, "upper_bound": 91.4}
                ],
                "metadata": {
                    "device_code": "WLD-001",
                    "device_name": "焊接设备01",
                    "metric_name": "temperature",
                    "prediction_method": "ARIMA",
                    "total_points": 24,
                    "avg_confidence": 0.89,
                    "data_period_start": "2025-10-29T00:00:00Z",
                    "data_period_end": "2025-11-05T00:00:00Z"
                }
            },
            "created_at": "2025-11-05T10:00:00Z",
            "completed_at": "2025-11-05T10:05:00Z"
        }
    }'::jsonb,
    200,
    200,
    true,
    100,
    1,
    'admin',
    NOW(),
    NOW()
);

-- =====================================================
-- 5. 趋势预测执行 Mock
-- =====================================================

INSERT INTO t_sys_mock_data (
    name, description, method, url_pattern, response_data, response_code, 
    delay, enabled, priority, creator_id, creator_name, created_at, updated_at
) VALUES (
    'AI趋势预测-执行预测',
    '模拟执行趋势预测，返回预测结果和趋势分析',
    'POST',
    '/api/v2/ai/trend-prediction/predict',
    '{
        "success": true,
        "code": 200,
        "message": "成功预测 5 步，趋势: 上升",
        "data": {
            "predictions": [
                {"step": 1, "predicted_value": 85.2, "lower_bound": 82.1, "upper_bound": 88.3},
                {"step": 2, "predicted_value": 86.5, "lower_bound": 83.3, "upper_bound": 89.7},
                {"step": 3, "predicted_value": 87.8, "lower_bound": 84.5, "upper_bound": 91.1},
                {"step": 4, "predicted_value": 89.1, "lower_bound": 85.7, "upper_bound": 92.5},
                {"step": 5, "predicted_value": 90.4, "lower_bound": 86.9, "upper_bound": 93.9}
            ],
            "method_used": "arima",
            "data_points": 30,
            "prediction_steps": 5,
            "trend_direction": "上升",
            "evaluation": {
                "mae": 2.3,
                "rmse": 3.1,
                "mape": 2.8
            }
        }
    }'::jsonb,
    200,
    800,
    true,
    100,
    1,
    'admin',
    NOW(),
    NOW()
);

-- =====================================================
-- 6. 批量趋势预测 Mock
-- =====================================================

INSERT INTO t_sys_mock_data (
    name, description, method, url_pattern, response_data, response_code, 
    delay, enabled, priority, creator_id, creator_name, created_at, updated_at
) VALUES (
    'AI趋势预测-批量预测',
    '模拟批量趋势预测，返回多个设备的预测结果',
    'POST',
    '/api/v2/ai/trend-prediction/predict/batch',
    '{
        "success": true,
        "code": 200,
        "message": "批量预测完成，成功: 3/3",
        "data": {
            "results": {
                "WLD-001": {
                    "predictions": [
                        {"value": 85.2, "lower_bound": 82.1, "upper_bound": 88.3},
                        {"value": 86.5, "lower_bound": 83.3, "upper_bound": 89.7}
                    ],
                    "method": "arima",
                    "trend": "上升"
                },
                "WLD-002": {
                    "predictions": [
                        {"value": 92.1, "lower_bound": 89.0, "upper_bound": 95.2},
                        {"value": 91.8, "lower_bound": 88.6, "upper_bound": 95.0}
                    ],
                    "method": "arima",
                    "trend": "平稳"
                }
            },
            "total_devices": 3,
            "success_count": 3,
            "failed_devices": []
        }
    }'::jsonb,
    200,
    1200,
    true,
    100,
    1,
    'admin',
    NOW(),
    NOW()
);

-- =====================================================
-- 7. 预测方法对比 Mock
-- =====================================================

INSERT INTO t_sys_mock_data (
    name, description, method, url_pattern, response_data, response_code, 
    delay, enabled, priority, creator_id, creator_name, created_at, updated_at
) VALUES (
    'AI趋势预测-方法对比',
    '模拟对比多种预测方法的效果，返回最佳推荐',
    'POST',
    '/api/v2/ai/trend-prediction/compare',
    '{
        "success": true,
        "code": 200,
        "message": "方法对比完成，推荐使用: arima",
        "data": {
            "comparisons": [
                {
                    "method": "arima",
                    "predictions": [{"value": 85.2}, {"value": 86.5}],
                    "trend": "上升",
                    "evaluation": {"mae": 2.1, "rmse": 2.8, "mape": 2.5}
                },
                {
                    "method": "ma",
                    "predictions": [{"value": 84.8}, {"value": 85.2}],
                    "trend": "平稳",
                    "evaluation": {"mae": 3.2, "rmse": 4.1, "mape": 3.8}
                },
                {
                    "method": "ema",
                    "predictions": [{"value": 85.5}, {"value": 86.8}],
                    "trend": "上升",
                    "evaluation": {"mae": 2.5, "rmse": 3.3, "mape": 2.9}
                }
            ],
            "best_method": "arima",
            "data_points": 30
        }
    }'::jsonb,
    200,
    1500,
    true,
    100,
    1,
    'admin',
    NOW(),
    NOW()
);

-- =====================================================
-- 8. 获取支持的预测方法 Mock
-- =====================================================

INSERT INTO t_sys_mock_data (
    name, description, method, url_pattern, response_data, response_code, 
    delay, enabled, priority, creator_id, creator_name, created_at, updated_at
) VALUES (
    'AI趋势预测-获取预测方法',
    '返回系统支持的所有预测方法及其说明',
    'GET',
    '/api/v2/ai/trend-prediction/methods',
    '{
        "success": true,
        "code": 200,
        "message": "成功获取预测方法列表",
        "data": {
            "arima": {
                "name": "ARIMA时间序列模型",
                "description": "自回归移动平均模型，适用于有趋势和季节性的数据",
                "适用场景": ["中长期预测", "复杂趋势", "季节性数据"],
                "min_data_points": 20
            },
            "ma": {
                "name": "简单移动平均",
                "description": "计算固定窗口的平均值进行预测",
                "适用场景": ["短期预测", "平稳数据"],
                "min_data_points": 5
            },
            "ema": {
                "name": "指数平滑",
                "description": "对最近的数据赋予更高权重",
                "适用场景": ["短中期预测", "趋势变化"],
                "min_data_points": 10
            },
            "lr": {
                "name": "线性回归",
                "description": "拟合线性趋势进行预测",
                "适用场景": ["线性趋势", "长期预测"],
                "min_data_points": 10
            }
        }
    }'::jsonb,
    200,
    100,
    true,
    100,
    1,
    'admin',
    NOW(),
    NOW()
);

-- =====================================================
-- 9. 创建单个预测任务 Mock
-- =====================================================

INSERT INTO t_sys_mock_data (
    name, description, method, url_pattern, response_data, response_code, 
    delay, enabled, priority, creator_id, creator_name, created_at, updated_at
) VALUES (
    'AI预测-创建预测任务',
    '模拟创建单个预测任务',
    'POST',
    '/api/v2/ai-monitor/predictions',
    '{
        "success": true,
        "code": 201,
        "message": "创建预测任务成功",
        "data": {
            "id": 99,
            "prediction_name": "新建预测任务",
            "device_code": "WLD-001",
            "metric_name": "temperature",
            "status": "pending",
            "progress": 0,
            "prediction_horizon": 24,
            "model_type": "ARIMA",
            "created_at": "2025-11-05T10:00:00Z"
        }
    }'::jsonb,
    201,
    300,
    true,
    100,
    1,
    'admin',
    NOW(),
    NOW()
);

-- =====================================================
-- 10. 删除预测任务 Mock
-- =====================================================

INSERT INTO t_sys_mock_data (
    name, description, method, url_pattern, response_data, response_code, 
    delay, enabled, priority, creator_id, creator_name, created_at, updated_at
) VALUES (
    'AI预测-删除预测',
    '模拟删除预测任务',
    'DELETE',
    '/api/v2/ai-monitor/predictions/*',
    '{
        "success": true,
        "code": 200,
        "message": "删除预测成功",
        "data": {
            "deleted_id": 1
        }
    }'::jsonb,
    200,
    200,
    true,
    90,
    1,
    'admin',
    NOW(),
    NOW()
);

-- =====================================================
-- 11. 导出预测报告 Mock
-- =====================================================

INSERT INTO t_sys_mock_data (
    name, description, method, url_pattern, response_data, response_code, 
    delay, enabled, priority, creator_id, creator_name, created_at, updated_at
) VALUES (
    'AI预测-导出报告',
    '模拟导出预测报告（返回文件下载信息）',
    'GET',
    '/api/v2/ai-monitor/predictions/*/export',
    '{
        "success": true,
        "code": 200,
        "message": "报告导出成功",
        "data": {
            "filename": "prediction_report_20251105.json",
            "url": "/exports/predictions/prediction_report_20251105.json",
            "size": 15680
        }
    }'::jsonb,
    200,
    1000,
    true,
    90,
    1,
    'admin',
    NOW(),
    NOW()
);

-- =====================================================
-- 12. 批量删除预测 Mock
-- =====================================================

INSERT INTO t_sys_mock_data (
    name, description, method, url_pattern, response_data, response_code, 
    delay, enabled, priority, creator_id, creator_name, created_at, updated_at
) VALUES (
    'AI预测-批量删除',
    '模拟批量删除多个预测任务',
    'POST',
    '/api/v2/ai-monitor/predictions/batch-delete',
    '{
        "success": true,
        "code": 200,
        "message": "批量删除完成，成功 3 个，失败 0 个",
        "data": {
            "success_count": 3,
            "failed_count": 0,
            "failed_ids": [],
            "errors": []
        }
    }'::jsonb,
    200,
    400,
    true,
    90,
    1,
    'admin',
    NOW(),
    NOW()
);

COMMIT;

-- =====================================================
-- 验证Mock规则
-- =====================================================

-- 查看所有AI预测相关的Mock规则
SELECT 
    id,
    name,
    method,
    url_pattern,
    enabled,
    priority,
    created_at
FROM t_sys_mock_data
WHERE url_pattern LIKE '%ai%prediction%'
   OR url_pattern LIKE '%trend-prediction%'
ORDER BY priority DESC, created_at DESC;

-- =====================================================
-- 说明
-- =====================================================

-- 这些Mock规则用于：
-- 1. 系统演示 - 无需真实后端即可展示AI预测功能
-- 2. 前端开发 - 前端开发时可以独立测试
-- 3. 快速验证 - 快速验证前端UI和交互逻辑
-- 4. 性能测试 - 模拟不同延迟测试前端性能

-- 使用方式：
-- 1. 在Mock数据管理页面启用相应的Mock规则
-- 2. 前端会自动拦截匹配的API请求
-- 3. 返回配置的Mock响应数据

-- 注意：
-- - 默认所有规则都是启用状态（enabled=true）
-- - 优先级都设置为100（高优先级）
-- - 可以在管理页面中调整优先级和启用状态

-- 回滚SQL（如需删除这些Mock规则）：
-- DELETE FROM t_sys_mock_data WHERE url_pattern LIKE '%ai%prediction%';

