-- 为已有工作流按类型补齐卡片强调色（仅在accent_color为空时）
UPDATE t_sys_workflow SET accent_color = '#2f54eb' WHERE type = 'device_monitor' AND accent_color IS NULL;
UPDATE t_sys_workflow SET accent_color = '#722ed1' WHERE type = 'alarm_process' AND accent_color IS NULL;
UPDATE t_sys_workflow SET accent_color = '#13c2c2' WHERE type = 'data_collection' AND accent_color IS NULL;
UPDATE t_sys_workflow SET accent_color = '#faad14' WHERE type = 'maintenance' AND accent_color IS NULL;
UPDATE t_sys_workflow SET accent_color = '#1890ff' WHERE type = 'custom' AND accent_color IS NULL;
