-- =====================================================
-- 工作流系统模板数据 (PostgreSQL版本)
-- 创建时间: 2024-11-26
-- 使用正确的表名: t_sys_workflow_template
-- =====================================================

-- 1. 设备状态监控流程模板
INSERT INTO t_sys_workflow_template (name, code, description, type, category, nodes, connections, default_config, is_system, created_at, updated_at)
VALUES (
    '设备状态监控流程',
    'tpl_device_monitor_basic',
    '监控设备运行状态，当设备状态异常时自动触发报警通知',
    'device_monitor',
    '设备监控',
    '[{"id": "node_start", "type": "start", "name": "开始", "x": 100, "y": 200}, {"id": "node_check", "type": "condition", "name": "状态检查", "x": 300, "y": 200}, {"id": "node_alarm", "type": "process", "name": "触发报警", "x": 500, "y": 100}, {"id": "node_notify", "type": "process", "name": "发送通知", "x": 700, "y": 100}, {"id": "node_log", "type": "process", "name": "记录日志", "x": 500, "y": 300}, {"id": "node_end", "type": "end", "name": "结束", "x": 900, "y": 200}]'::jsonb,
    '[{"id": "conn_1", "fromNodeId": "node_start", "toNodeId": "node_check"}, {"id": "conn_2", "fromNodeId": "node_check", "toNodeId": "node_alarm", "label": "异常"}, {"id": "conn_3", "fromNodeId": "node_check", "toNodeId": "node_log", "label": "正常"}, {"id": "conn_4", "fromNodeId": "node_alarm", "toNodeId": "node_notify"}, {"id": "conn_5", "fromNodeId": "node_notify", "toNodeId": "node_end"}, {"id": "conn_6", "fromNodeId": "node_log", "toNodeId": "node_end"}]'::jsonb,
    '{"trigger_config": {"event_type": "device_status_change"}, "notification_config": {"channels": ["websocket", "email"]}}'::jsonb,
    true, NOW(), NOW()
) ON CONFLICT (code) DO UPDATE SET updated_at = NOW();

-- 2. 报警处理流程模板
INSERT INTO t_sys_workflow_template (name, code, description, type, category, nodes, connections, default_config, is_system, created_at, updated_at)
VALUES (
    '报警自动处理流程',
    'tpl_alarm_process_auto',
    '自动处理设备报警，包括报警确认、通知相关人员、创建工单',
    'alarm_process',
    '报警处理',
    '[{"id": "node_start", "type": "start", "name": "报警触发", "x": 100, "y": 200}, {"id": "node_level", "type": "condition", "name": "级别判断", "x": 300, "y": 200}, {"id": "node_urgent", "type": "process", "name": "紧急处理", "x": 500, "y": 100}, {"id": "node_normal", "type": "process", "name": "常规处理", "x": 500, "y": 300}, {"id": "node_ticket", "type": "process", "name": "创建工单", "x": 700, "y": 200}, {"id": "node_end", "type": "end", "name": "结束", "x": 900, "y": 200}]'::jsonb,
    '[{"id": "conn_1", "fromNodeId": "node_start", "toNodeId": "node_level"}, {"id": "conn_2", "fromNodeId": "node_level", "toNodeId": "node_urgent", "label": "紧急"}, {"id": "conn_3", "fromNodeId": "node_level", "toNodeId": "node_normal", "label": "警告"}, {"id": "conn_4", "fromNodeId": "node_urgent", "toNodeId": "node_ticket"}, {"id": "conn_5", "fromNodeId": "node_normal", "toNodeId": "node_ticket"}, {"id": "conn_6", "fromNodeId": "node_ticket", "toNodeId": "node_end"}]'::jsonb,
    '{"trigger_config": {"event_type": "alarm_triggered"}, "notification_config": {"on_failure": true, "channels": ["websocket", "sms"]}}'::jsonb,
    true, NOW(), NOW()
) ON CONFLICT (code) DO UPDATE SET updated_at = NOW();

-- 3. 定时数据采集流程模板
INSERT INTO t_sys_workflow_template (name, code, description, type, category, nodes, connections, default_config, is_system, created_at, updated_at)
VALUES (
    '定时数据采集流程',
    'tpl_data_collection_schedule',
    '定时采集设备数据并存储到数据库，支持数据清洗和转换',
    'data_collection',
    '数据采集',
    '[{"id": "node_start", "type": "start", "name": "定时触发", "x": 100, "y": 200}, {"id": "node_fetch", "type": "api", "name": "获取设备数据", "x": 300, "y": 200}, {"id": "node_transform", "type": "transform", "name": "数据转换", "x": 500, "y": 200}, {"id": "node_filter", "type": "filter", "name": "数据过滤", "x": 700, "y": 200}, {"id": "node_save", "type": "database", "name": "保存数据", "x": 900, "y": 200}, {"id": "node_end", "type": "end", "name": "结束", "x": 1100, "y": 200}]'::jsonb,
    '[{"id": "conn_1", "fromNodeId": "node_start", "toNodeId": "node_fetch"}, {"id": "conn_2", "fromNodeId": "node_fetch", "toNodeId": "node_transform"}, {"id": "conn_3", "fromNodeId": "node_transform", "toNodeId": "node_filter"}, {"id": "conn_4", "fromNodeId": "node_filter", "toNodeId": "node_save"}, {"id": "conn_5", "fromNodeId": "node_save", "toNodeId": "node_end"}]'::jsonb,
    '{"trigger_config": {"cron_expression": "*/5 * * * *"}, "execution_config": {"timeout_seconds": 300}}'::jsonb,
    true, NOW(), NOW()
) ON CONFLICT (code) DO UPDATE SET updated_at = NOW();

-- 4. 设备维护提醒流程模板
INSERT INTO t_sys_workflow_template (name, code, description, type, category, nodes, connections, default_config, is_system, created_at, updated_at)
VALUES (
    '设备维护提醒流程',
    'tpl_maintenance_reminder',
    '根据设备运行时间和维护周期，自动生成维护提醒和工单',
    'maintenance',
    '维护保养',
    '[{"id": "node_start", "type": "start", "name": "开始检查", "x": 100, "y": 200}, {"id": "node_query", "type": "database", "name": "查询设备", "x": 300, "y": 200}, {"id": "node_loop", "type": "loop", "name": "遍历设备", "x": 500, "y": 200}, {"id": "node_create", "type": "process", "name": "创建维护单", "x": 700, "y": 200}, {"id": "node_notify", "type": "process", "name": "通知负责人", "x": 900, "y": 200}, {"id": "node_end", "type": "end", "name": "结束", "x": 1100, "y": 200}]'::jsonb,
    '[{"id": "conn_1", "fromNodeId": "node_start", "toNodeId": "node_query"}, {"id": "conn_2", "fromNodeId": "node_query", "toNodeId": "node_loop"}, {"id": "conn_3", "fromNodeId": "node_loop", "toNodeId": "node_create"}, {"id": "conn_4", "fromNodeId": "node_create", "toNodeId": "node_notify"}, {"id": "conn_5", "fromNodeId": "node_notify", "toNodeId": "node_end"}]'::jsonb,
    '{"trigger_config": {"cron_expression": "0 9 * * 1"}, "notification_config": {"channels": ["email"]}}'::jsonb,
    true, NOW(), NOW()
) ON CONFLICT (code) DO UPDATE SET updated_at = NOW();

-- 5. 简单审批流程模板
INSERT INTO t_sys_workflow_template (name, code, description, type, category, nodes, connections, default_config, is_system, created_at, updated_at)
VALUES (
    '简单审批流程',
    'tpl_simple_approval',
    '通用的简单审批流程，支持单级审批',
    'custom',
    '审批流程',
    '[{"id": "node_start", "type": "start", "name": "提交申请", "x": 100, "y": 200}, {"id": "node_approve", "type": "process", "name": "审批", "x": 300, "y": 200}, {"id": "node_check", "type": "condition", "name": "审批结果", "x": 500, "y": 200}, {"id": "node_pass", "type": "process", "name": "审批通过", "x": 700, "y": 100}, {"id": "node_reject", "type": "process", "name": "审批拒绝", "x": 700, "y": 300}, {"id": "node_end", "type": "end", "name": "结束", "x": 900, "y": 200}]'::jsonb,
    '[{"id": "conn_1", "fromNodeId": "node_start", "toNodeId": "node_approve"}, {"id": "conn_2", "fromNodeId": "node_approve", "toNodeId": "node_check"}, {"id": "conn_3", "fromNodeId": "node_check", "toNodeId": "node_pass", "label": "通过"}, {"id": "conn_4", "fromNodeId": "node_check", "toNodeId": "node_reject", "label": "拒绝"}, {"id": "conn_5", "fromNodeId": "node_pass", "toNodeId": "node_end"}, {"id": "conn_6", "fromNodeId": "node_reject", "toNodeId": "node_end"}]'::jsonb,
    '{"notification_config": {"on_start": true, "on_success": true, "channels": ["websocket", "email"]}}'::jsonb,
    true, NOW(), NOW()
) ON CONFLICT (code) DO UPDATE SET updated_at = NOW();
