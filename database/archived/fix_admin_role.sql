-- 为 admin 用户分配管理员角色

BEGIN;

-- 检查 admin 用户和管理员角色
DO $$
DECLARE
    v_admin_user_id INTEGER;
    v_admin_role_id INTEGER;
    v_exists BOOLEAN;
BEGIN
    -- 获取 admin 用户ID
    SELECT id INTO v_admin_user_id 
    FROM t_sys_user 
    WHERE username = 'admin'
    LIMIT 1;
    
    -- 获取管理员角色ID
    SELECT id INTO v_admin_role_id
    FROM t_sys_role
    WHERE role_name LIKE '%管理员%'
    LIMIT 1;
    
    IF v_admin_user_id IS NULL THEN
        RAISE NOTICE '❌ 错误: 找不到 admin 用户';
        RETURN;
    END IF;
    
    IF v_admin_role_id IS NULL THEN
        RAISE NOTICE '❌ 错误: 找不到管理员角色';
        RETURN;
    END IF;
    
    RAISE NOTICE '✓ admin 用户 ID: %', v_admin_user_id;
    RAISE NOTICE '✓ 管理员角色 ID: %', v_admin_role_id;
    
    -- 检查关联是否已存在
    SELECT EXISTS(
        SELECT 1 
        FROM t_sys_user_role 
        WHERE user_id = v_admin_user_id AND role_id = v_admin_role_id
    ) INTO v_exists;
    
    IF v_exists THEN
        RAISE NOTICE '✓ admin 用户已关联管理员角色';
    ELSE
        -- 创建关联
        INSERT INTO t_sys_user_role (user_id, role_id, created_at, updated_at)
        VALUES (v_admin_user_id, v_admin_role_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
        
        RAISE NOTICE '✅ 成功为 admin 用户分配管理员角色';
    END IF;
END $$;

COMMIT;

-- 验证
SELECT 
    u.id, 
    u.username, 
    STRING_AGG(r.role_name, ', ') as roles
FROM t_sys_user u
LEFT JOIN t_sys_user_role ur ON u.id = ur.user_id
LEFT JOIN t_sys_role r ON ur.role_id = r.id
WHERE u.username = 'admin'
GROUP BY u.id, u.username;

