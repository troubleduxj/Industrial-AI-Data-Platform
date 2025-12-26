-- 用户权限系统数据模型优化脚本
-- 任务: 1. 数据模型和数据库结构优化

-- 1. 优化菜单表结构
-- 添加缺失的字段和索引
ALTER TABLE t_sys_menu 
ADD COLUMN IF NOT EXISTS order_num INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS perms VARCHAR(100),
ADD COLUMN IF NOT EXISTS visible BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS status BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS is_frame BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS is_cache BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS query VARCHAR(255);

-- 修改现有字段类型和长度
ALTER TABLE t_sys_menu 
ALTER COLUMN path TYPE VARCHAR(200),
ALTER COLUMN component TYPE VARCHAR(255),
ALTER COLUMN parent_id TYPE BIGINT;

-- 添加菜单表索引
CREATE INDEX IF NOT EXISTS idx_menu_order_num ON t_sys_menu(order_num);
CREATE INDEX IF NOT EXISTS idx_menu_perms ON t_sys_menu(perms);
CREATE INDEX IF NOT EXISTS idx_menu_visible ON t_sys_menu(visible);
CREATE INDEX IF NOT EXISTS idx_menu_status ON t_sys_menu(status);

-- 添加字段注释
COMMENT ON COLUMN t_sys_menu.order_num IS '显示顺序';
COMMENT ON COLUMN t_sys_menu.perms IS '权限标识';
COMMENT ON COLUMN t_sys_menu.visible IS '显示状态';
COMMENT ON COLUMN t_sys_menu.status IS '菜单状态';
COMMENT ON COLUMN t_sys_menu.is_frame IS '是否外链';
COMMENT ON COLUMN t_sys_menu.is_cache IS '是否缓存';
COMMENT ON COLUMN t_sys_menu.query IS '路由参数';

-- 2. 修复角色菜单关联表的外键引用错误
-- 删除错误的表（如果存在）
DROP TABLE IF EXISTS t_sys_role_menu CASCADE;

-- 重新创建正确的角色菜单关联表
CREATE TABLE IF NOT EXISTS t_sys_role_menu (
    id BIGSERIAL PRIMARY KEY,
    role_id BIGINT NOT NULL REFERENCES t_sys_role(id) ON DELETE CASCADE,
    menu_id BIGINT NOT NULL REFERENCES t_sys_menu(id) ON DELETE CASCADE,
    CONSTRAINT uk_role_menu UNIQUE (role_id, menu_id)
);

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_role_menu_role_id ON t_sys_role_menu(role_id);
CREATE INDEX IF NOT EXISTS idx_role_menu_menu_id ON t_sys_role_menu(menu_id);

-- 添加注释
COMMENT ON TABLE t_sys_role_menu IS '角色菜单关联表';
COMMENT ON COLUMN t_sys_role_menu.role_id IS '角色ID';
COMMENT ON COLUMN t_sys_role_menu.menu_id IS '菜单ID';

-- 3. 修复角色API关联表的外键引用错误
-- 删除错误的表（如果存在）
DROP TABLE IF EXISTS t_sys_role_api CASCADE;

-- 重新创建正确的角色API关联表
CREATE TABLE IF NOT EXISTS t_sys_role_api (
    id BIGSERIAL PRIMARY KEY,
    role_id BIGINT NOT NULL REFERENCES t_sys_role(id) ON DELETE CASCADE,
    api_id BIGINT NOT NULL REFERENCES t_sys_api_endpoints(id) ON DELETE CASCADE,
    CONSTRAINT uk_role_api UNIQUE (role_id, api_id)
);

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_role_api_role_id ON t_sys_role_api(role_id);
CREATE INDEX IF NOT EXISTS idx_role_api_api_id ON t_sys_role_api(api_id);

-- 添加注释
COMMENT ON TABLE t_sys_role_api IS '角色API关联表';
COMMENT ON COLUMN t_sys_role_api.role_id IS '角色ID';
COMMENT ON COLUMN t_sys_role_api.api_id IS 'API端点ID';

-- 4. 优化用户表索引
-- 添加复合索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_user_status_del_flag ON t_sys_user(status, del_flag);
CREATE INDEX IF NOT EXISTS idx_user_type_status ON t_sys_user(user_type, status);

-- 5. 优化角色表索引
CREATE INDEX IF NOT EXISTS idx_role_status_del_flag ON t_sys_role(status, del_flag);

-- 6. 优化API端点表索引
CREATE INDEX IF NOT EXISTS idx_api_path_method ON t_sys_api_endpoints(api_path, http_method);
CREATE INDEX IF NOT EXISTS idx_api_status_public ON t_sys_api_endpoints(status, is_public);

-- 7. 为现有菜单数据设置默认值
UPDATE t_sys_menu SET 
    order_num = COALESCE("order", 0),
    visible = NOT COALESCE(is_hidden, FALSE),
    status = TRUE,
    is_frame = FALSE,
    is_cache = COALESCE(keepalive, TRUE)
WHERE order_num IS NULL OR visible IS NULL OR status IS NULL OR is_frame IS NULL OR is_cache IS NULL;

-- 8. 验证数据完整性
-- 检查是否有孤立的关联记录
DO $$
BEGIN
    -- 检查用户角色关联
    IF EXISTS (
        SELECT 1 FROM t_sys_user_role ur 
        LEFT JOIN t_sys_user u ON ur.user_id = u.id 
        LEFT JOIN t_sys_role r ON ur.role_id = r.id 
        WHERE u.id IS NULL OR r.id IS NULL
    ) THEN
        RAISE NOTICE '发现孤立的用户角色关联记录';
    END IF;
    
    -- 检查部门关联
    IF EXISTS (
        SELECT 1 FROM t_sys_user u 
        LEFT JOIN t_sys_dept d ON u.dept_id = d.id 
        WHERE u.dept_id IS NOT NULL AND d.id IS NULL
    ) THEN
        RAISE NOTICE '发现孤立的用户部门关联记录';
    END IF;
END $$;

-- 9. 创建权限系统相关的视图（可选）
CREATE OR REPLACE VIEW v_user_permissions AS
SELECT 
    u.id as user_id,
    u.username,
    u.user_type,
    r.id as role_id,
    r.role_name,
    ae.id as api_id,
    ae.api_code,
    ae.api_path,
    ae.http_method,
    ae.permission_code
FROM t_sys_user u
JOIN t_sys_user_role ur ON u.id = ur.user_id
JOIN t_sys_role r ON ur.role_id = r.id
JOIN t_sys_role_api ra ON r.id = ra.role_id
JOIN t_sys_api_endpoints ae ON ra.api_id = ae.id
WHERE u.status = '0' 
  AND u.del_flag = '0' 
  AND r.status = '0' 
  AND r.del_flag = '0'
  AND ae.status = 'active';

COMMENT ON VIEW v_user_permissions IS '用户权限视图 - 用于快速查询用户的API权限';

-- 10. 创建用户菜单权限视图
CREATE OR REPLACE VIEW v_user_menus AS
SELECT 
    u.id as user_id,
    u.username,
    r.id as role_id,
    r.role_name,
    m.id as menu_id,
    m.name as menu_name,
    m.path,
    m.component,
    m.menu_type,
    m.icon,
    m.order_num,
    m.parent_id,
    m.perms,
    m.visible,
    m.status
FROM t_sys_user u
JOIN t_sys_user_role ur ON u.id = ur.user_id
JOIN t_sys_role r ON ur.role_id = r.id
JOIN t_sys_role_menu rm ON r.id = rm.role_id
JOIN t_sys_menu m ON rm.menu_id = m.id
WHERE u.status = '0' 
  AND u.del_flag = '0' 
  AND r.status = '0' 
  AND r.del_flag = '0'
  AND m.status = TRUE
  AND m.visible = TRUE;

COMMENT ON VIEW v_user_menus IS '用户菜单权限视图 - 用于快速查询用户的菜单权限';

-- 完成优化
SELECT 'Permission system data model optimization completed successfully!' as result;