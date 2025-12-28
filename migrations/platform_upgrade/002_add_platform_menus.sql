-- 工业AI数据平台菜单升级脚本
-- 添加资产管理、AI引擎、特征工程等新功能菜单

-- 注意：执行前请确认当前最大菜单ID，避免ID冲突
-- 可以通过 SELECT MAX(id) FROM t_sys_menu; 查询

-- ============================================
-- 1. 添加资产管理主菜单
-- ============================================
INSERT INTO t_sys_menu (id, name, path, component, menu_type, icon, order_num, parent_id, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES 
(1001, '资产管理', '/assets', 'Layout', 'catalog', 'mdi:cube-outline', 10, NULL, NULL, true, true, false, true, NOW(), NOW());

-- 资产类别管理
INSERT INTO t_sys_menu (id, name, path, component, menu_type, icon, order_num, parent_id, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES 
(1002, '资产类别', 'categories', 'assets/categories/index', 'menu', 'mdi:folder-outline', 1, 1001, 'asset:category:list', true, true, false, true, NOW(), NOW());

-- 资产列表
INSERT INTO t_sys_menu (id, name, path, component, menu_type, icon, order_num, parent_id, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES 
(1003, '资产列表', 'list', 'assets/list/index', 'menu', 'mdi:format-list-bulleted', 2, 1001, 'asset:list', true, true, false, true, NOW(), NOW());

-- 资产监控
INSERT INTO t_sys_menu (id, name, path, component, menu_type, icon, order_num, parent_id, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES 
(1004, '资产监控', 'monitor', 'assets/monitor/index', 'menu', 'mdi:monitor-dashboard', 3, 1001, 'asset:monitor', true, true, false, true, NOW(), NOW());

-- ============================================
-- 2. 添加AI引擎主菜单
-- ============================================
INSERT INTO t_sys_menu (id, name, path, component, menu_type, icon, order_num, parent_id, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES 
(1010, 'AI引擎', '/ai-engine', 'Layout', 'catalog', 'mdi:brain', 20, NULL, NULL, true, true, false, true, NOW(), NOW());

-- 模型管理
INSERT INTO t_sys_menu (id, name, path, component, menu_type, icon, order_num, parent_id, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES 
(1011, '模型管理', 'models', 'ai-engine/models/index', 'menu', 'mdi:cube-scan', 1, 1010, 'ai:model:list', true, true, false, true, NOW(), NOW());

-- 模型版本
INSERT INTO t_sys_menu (id, name, path, component, menu_type, icon, order_num, parent_id, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES 
(1012, '模型版本', 'versions', 'ai-engine/versions/index', 'menu', 'mdi:source-branch', 2, 1010, 'ai:version:list', true, true, false, true, NOW(), NOW());

-- 预测服务
INSERT INTO t_sys_menu (id, name, path, component, menu_type, icon, order_num, parent_id, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES 
(1013, '预测服务', 'predictions', 'ai-engine/predictions/index', 'menu', 'mdi:chart-timeline-variant', 3, 1010, 'ai:prediction:list', true, true, false, true, NOW(), NOW());

-- ============================================
-- 3. 添加特征工程主菜单
-- ============================================
INSERT INTO t_sys_menu (id, name, path, component, menu_type, icon, order_num, parent_id, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES 
(1020, '特征工程', '/feature-engine', 'Layout', 'catalog', 'mdi:function-variant', 30, NULL, NULL, true, true, false, true, NOW(), NOW());

-- 特征定义
INSERT INTO t_sys_menu (id, name, path, component, menu_type, icon, order_num, parent_id, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES 
(1021, '特征定义', 'definitions', 'feature-engine/definitions/index', 'menu', 'mdi:code-tags', 1, 1020, 'feature:definition:list', true, true, false, true, NOW(), NOW());

-- 特征视图
INSERT INTO t_sys_menu (id, name, path, component, menu_type, icon, order_num, parent_id, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES 
(1022, '特征视图', 'views', 'feature-engine/views/index', 'menu', 'mdi:view-dashboard-outline', 2, 1020, 'feature:view:list', true, true, false, true, NOW(), NOW());

-- 流计算任务
INSERT INTO t_sys_menu (id, name, path, component, menu_type, icon, order_num, parent_id, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES 
(1023, '流计算任务', 'streams', 'feature-engine/streams/index', 'menu', 'mdi:pipe', 3, 1020, 'feature:stream:list', true, true, false, true, NOW(), NOW());

-- ============================================
-- 4. 添加数据迁移菜单（系统管理下）
-- ============================================
-- 假设系统管理的parent_id为某个值，需要根据实际情况调整
INSERT INTO t_sys_menu (id, name, path, component, menu_type, icon, order_num, parent_id, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES 
(1030, '数据迁移', '/migration', 'Layout', 'catalog', 'mdi:database-sync', 40, NULL, NULL, true, true, false, true, NOW(), NOW());

-- 迁移状态
INSERT INTO t_sys_menu (id, name, path, component, menu_type, icon, order_num, parent_id, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES 
(1031, '迁移状态', 'status', 'migration/status/index', 'menu', 'mdi:progress-check', 1, 1030, 'migration:status', true, true, false, true, NOW(), NOW());

-- 迁移记录
INSERT INTO t_sys_menu (id, name, path, component, menu_type, icon, order_num, parent_id, perms, visible, status, is_frame, is_cache, created_at, updated_at)
VALUES 
(1032, '迁移记录', 'records', 'migration/records/index', 'menu', 'mdi:history', 2, 1030, 'migration:records', true, true, false, true, NOW(), NOW());

-- ============================================
-- 5. 为管理员角色分配新菜单权限
-- ============================================
-- 假设管理员角色ID为1，需要根据实际情况调整
-- 首先查询管理员角色ID: SELECT id FROM t_sys_role WHERE role_key = 'admin';

-- 资产管理菜单权限
INSERT INTO t_sys_role_menu (role_id, menu_id) VALUES (1, 1001);
INSERT INTO t_sys_role_menu (role_id, menu_id) VALUES (1, 1002);
INSERT INTO t_sys_role_menu (role_id, menu_id) VALUES (1, 1003);
INSERT INTO t_sys_role_menu (role_id, menu_id) VALUES (1, 1004);

-- AI引擎菜单权限
INSERT INTO t_sys_role_menu (role_id, menu_id) VALUES (1, 1010);
INSERT INTO t_sys_role_menu (role_id, menu_id) VALUES (1, 1011);
INSERT INTO t_sys_role_menu (role_id, menu_id) VALUES (1, 1012);
INSERT INTO t_sys_role_menu (role_id, menu_id) VALUES (1, 1013);

-- 特征工程菜单权限
INSERT INTO t_sys_role_menu (role_id, menu_id) VALUES (1, 1020);
INSERT INTO t_sys_role_menu (role_id, menu_id) VALUES (1, 1021);
INSERT INTO t_sys_role_menu (role_id, menu_id) VALUES (1, 1022);
INSERT INTO t_sys_role_menu (role_id, menu_id) VALUES (1, 1023);

-- 数据迁移菜单权限
INSERT INTO t_sys_role_menu (role_id, menu_id) VALUES (1, 1030);
INSERT INTO t_sys_role_menu (role_id, menu_id) VALUES (1, 1031);
INSERT INTO t_sys_role_menu (role_id, menu_id) VALUES (1, 1032);

-- ============================================
-- 6. 清理菜单缓存（需要在应用中执行）
-- ============================================
-- 执行完SQL后，需要清理Redis中的菜单缓存
-- 可以通过以下方式：
-- 1. 重启后端服务
-- 2. 调用清理缓存API
-- 3. 执行 scripts/clear_menu_cache.py 脚本
