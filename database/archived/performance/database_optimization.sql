-- 数据库索引优化脚本
-- 生成时间: 944880.328

-- 注意: 在生产环境执行前请先备份数据库
-- 建议在低峰期执行以减少对系统性能的影响

-- User 模型索引优化
--------------------------------------------------
-- 外键字段 roles 建议添加索引以提高关联查询性能
CREATE INDEX idx_user_roles ON user (roles);

-- 字段 created_at 是频繁查询字段，建议添加索引
CREATE INDEX idx_user_created_at ON user (created_at);

-- 字段 updated_at 是频繁查询字段，建议添加索引
CREATE INDEX idx_user_updated_at ON user (updated_at);

-- Role 模型索引优化
--------------------------------------------------
-- 外键字段 menus 建议添加索引以提高关联查询性能
CREATE INDEX idx_role_menus ON role (menus);

-- 外键字段 apis 建议添加索引以提高关联查询性能
CREATE INDEX idx_role_apis ON role (apis);

-- 外键字段 user_roles 建议添加索引以提高关联查询性能
CREATE INDEX idx_role_user_roles ON role (user_roles);

-- 字段 created_at 是频繁查询字段，建议添加索引
CREATE INDEX idx_role_created_at ON role (created_at);

-- 字段 updated_at 是频繁查询字段，建议添加索引
CREATE INDEX idx_role_updated_at ON role (updated_at);

-- Api 模型索引优化
--------------------------------------------------
-- 外键字段 role_apis 建议添加索引以提高关联查询性能
CREATE INDEX idx_api_role_apis ON api (role_apis);

-- 字段 created_at 是频繁查询字段，建议添加索引
CREATE INDEX idx_api_created_at ON api (created_at);

-- 字段 updated_at 是频繁查询字段，建议添加索引
CREATE INDEX idx_api_updated_at ON api (updated_at);

-- Menu 模型索引优化
--------------------------------------------------
-- 外键字段 role_menus 建议添加索引以提高关联查询性能
CREATE INDEX idx_menu_role_menus ON menu (role_menus);

-- 字段 created_at 是频繁查询字段，建议添加索引
CREATE INDEX idx_menu_created_at ON menu (created_at);

-- 字段 updated_at 是频繁查询字段，建议添加索引
CREATE INDEX idx_menu_updated_at ON menu (updated_at);

-- 字段 is_hidden 是频繁查询字段，建议添加索引
CREATE INDEX idx_menu_is_hidden ON menu (is_hidden);

-- 菜单层级和排序查询
CREATE INDEX idx_menu_parent_id_order ON menu (parent_id, order);

-- Dept 模型索引优化
--------------------------------------------------
-- 外键字段 ancestors 建议添加索引以提高关联查询性能
CREATE INDEX idx_dept_ancestors ON dept (ancestors);

-- 外键字段 descendants 建议添加索引以提高关联查询性能
CREATE INDEX idx_dept_descendants ON dept (descendants);

-- 字段 created_at 是频繁查询字段，建议添加索引
CREATE INDEX idx_dept_created_at ON dept (created_at);

-- 字段 updated_at 是频繁查询字段，建议添加索引
CREATE INDEX idx_dept_updated_at ON dept (updated_at);

-- AuditLog 模型索引优化
--------------------------------------------------
-- 字段 created_at 是频繁查询字段，建议添加索引
CREATE INDEX idx_auditlog_created_at ON auditlog (created_at);

-- 字段 updated_at 是频繁查询字段，建议添加索引
CREATE INDEX idx_auditlog_updated_at ON auditlog (updated_at);

-- 按用户和时间查询审计日志
CREATE INDEX idx_auditlog_user_id_created_at ON auditlog (user_id, created_at);

-- 按模块和时间查询审计日志
CREATE INDEX idx_auditlog_module_created_at ON auditlog (module, created_at);

-- DeviceInfo 模型索引优化
--------------------------------------------------
-- 外键字段 history_data 建议添加索引以提高关联查询性能
CREATE INDEX idx_t_device_info_history_data ON t_device_info (history_data);

-- 外键字段 realtime_data 建议添加索引以提高关联查询性能
CREATE INDEX idx_t_device_info_realtime_data ON t_device_info (realtime_data);

-- 字段 created_at 是频繁查询字段，建议添加索引
CREATE INDEX idx_t_device_info_created_at ON t_device_info (created_at);

-- 字段 updated_at 是频繁查询字段，建议添加索引
CREATE INDEX idx_t_device_info_updated_at ON t_device_info (updated_at);

-- 字段 team_name 是频繁查询字段，建议添加索引
CREATE INDEX idx_t_device_info_team_name ON t_device_info (team_name);

-- 字段 is_locked 是频繁查询字段，建议添加索引
CREATE INDEX idx_t_device_info_is_locked ON t_device_info (is_locked);

-- DeviceType 模型索引优化
--------------------------------------------------
-- 字段 created_at 是频繁查询字段，建议添加索引
CREATE INDEX idx_t_device_type_created_at ON t_device_type (created_at);

-- 字段 updated_at 是频繁查询字段，建议添加索引
CREATE INDEX idx_t_device_type_updated_at ON t_device_type (updated_at);

-- DeviceRealTimeData 模型索引优化
--------------------------------------------------
-- 外键字段 device 建议添加索引以提高关联查询性能
CREATE INDEX idx_t_device_realtime_data_device ON t_device_realtime_data (device);

-- 字段 created_at 是频繁查询字段，建议添加索引
CREATE INDEX idx_t_device_realtime_data_created_at ON t_device_realtime_data (created_at);

-- 字段 updated_at 是频繁查询字段，建议添加索引
CREATE INDEX idx_t_device_realtime_data_updated_at ON t_device_realtime_data (updated_at);

-- 字段 status 是频繁查询字段，建议添加索引
CREATE INDEX idx_t_device_realtime_data_status ON t_device_realtime_data (status);

-- 字段 data_timestamp 是频繁查询字段，建议添加索引
CREATE INDEX idx_t_device_realtime_data_data_timestamp ON t_device_realtime_data (data_timestamp);

-- 字段 device_id 是频繁查询字段，建议添加索引
CREATE INDEX idx_t_device_realtime_data_device_id ON t_device_realtime_data (device_id);

-- 设备实时数据按设备和时间查询
CREATE INDEX idx_t_device_realtime_data_device_id_data_timestamp ON t_device_realtime_data (device_id, data_timestamp);

-- 按状态和时间查询设备数据
CREATE INDEX idx_t_device_realtime_data_status_data_timestamp ON t_device_realtime_data (status, data_timestamp);

-- DeviceHistoryData 模型索引优化
--------------------------------------------------
-- 外键字段 device 建议添加索引以提高关联查询性能
CREATE INDEX idx_t_device_history_data_device ON t_device_history_data (device);

-- 字段 created_at 是频繁查询字段，建议添加索引
CREATE INDEX idx_t_device_history_data_created_at ON t_device_history_data (created_at);

-- 字段 updated_at 是频繁查询字段，建议添加索引
CREATE INDEX idx_t_device_history_data_updated_at ON t_device_history_data (updated_at);

-- 字段 status 是频繁查询字段，建议添加索引
CREATE INDEX idx_t_device_history_data_status ON t_device_history_data (status);

-- 字段 data_timestamp 是频繁查询字段，建议添加索引
CREATE INDEX idx_t_device_history_data_data_timestamp ON t_device_history_data (data_timestamp);

-- 字段 device_id 是频繁查询字段，建议添加索引
CREATE INDEX idx_t_device_history_data_device_id ON t_device_history_data (device_id);

-- 设备历史数据按设备和时间查询
CREATE INDEX idx_t_device_history_data_device_id_data_timestamp ON t_device_history_data (device_id, data_timestamp);

-- 按状态和时间查询历史数据
CREATE INDEX idx_t_device_history_data_status_data_timestamp ON t_device_history_data (status, data_timestamp);
