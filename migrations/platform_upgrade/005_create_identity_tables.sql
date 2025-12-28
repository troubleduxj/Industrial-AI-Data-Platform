-- =====================================================
-- 企业身份集成数据库表
-- 版本: 005
-- 描述: 创建身份提供商和用户外部身份关联表
-- 需求: 10.5
-- =====================================================

-- 身份提供商配置表
-- 存储LDAP、OAuth2等身份提供商的配置信息
CREATE TABLE IF NOT EXISTS t_identity_providers (
    id BIGSERIAL PRIMARY KEY,
    
    -- 基础信息
    name VARCHAR(50) UNIQUE NOT NULL,
    type VARCHAR(20) NOT NULL,  -- ldap, oauth2, saml
    
    -- 配置 (JSONB格式)
    -- LDAP配置示例: {"server": "ldap://...", "base_dn": "...", "bind_dn": "...", "bind_password": "..."}
    -- OAuth2配置示例: {"client_id": "...", "client_secret": "...", "authorization_url": "...", "token_url": "...", "userinfo_url": "..."}
    config JSONB NOT NULL DEFAULT '{}',
    
    -- 状态
    enabled BOOLEAN DEFAULT TRUE,
    priority INT DEFAULT 0,  -- 优先级，数字越小优先级越高
    
    -- 角色映射 (JSONB格式)
    -- 示例: {"admin_group": 1, "user_group": 2}
    role_mapping JSONB,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_identity_providers_enabled ON t_identity_providers(enabled);
CREATE INDEX IF NOT EXISTS idx_identity_providers_type ON t_identity_providers(type);
CREATE INDEX IF NOT EXISTS idx_identity_providers_priority ON t_identity_providers(enabled, priority);

-- 添加注释
COMMENT ON TABLE t_identity_providers IS '身份提供商配置表';
COMMENT ON COLUMN t_identity_providers.name IS '提供商名称，唯一标识';
COMMENT ON COLUMN t_identity_providers.type IS '提供商类型: ldap, oauth2, saml';
COMMENT ON COLUMN t_identity_providers.config IS '提供商配置，JSON格式';
COMMENT ON COLUMN t_identity_providers.enabled IS '是否启用';
COMMENT ON COLUMN t_identity_providers.priority IS '优先级，数字越小优先级越高';
COMMENT ON COLUMN t_identity_providers.role_mapping IS '组到角色的映射关系';


-- 用户外部身份关联表
-- 关联本地用户与外部身份提供商的用户
CREATE TABLE IF NOT EXISTS t_user_external_identities (
    id BIGSERIAL PRIMARY KEY,
    
    -- 关联本地用户
    user_id BIGINT NOT NULL,
    
    -- 关联身份提供商
    provider_id BIGINT NOT NULL REFERENCES t_identity_providers(id) ON DELETE CASCADE,
    
    -- 外部身份信息
    external_id VARCHAR(255) NOT NULL,  -- 外部系统中的用户ID
    external_username VARCHAR(100),      -- 外部系统中的用户名
    
    -- 登录信息
    last_login_at TIMESTAMP,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- 唯一约束：同一提供商下的外部ID唯一
    UNIQUE(provider_id, external_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_user_external_identities_user ON t_user_external_identities(user_id);
CREATE INDEX IF NOT EXISTS idx_user_external_identities_provider ON t_user_external_identities(provider_id);
CREATE INDEX IF NOT EXISTS idx_user_external_identities_external ON t_user_external_identities(external_id);

-- 添加注释
COMMENT ON TABLE t_user_external_identities IS '用户外部身份关联表';
COMMENT ON COLUMN t_user_external_identities.user_id IS '本地用户ID';
COMMENT ON COLUMN t_user_external_identities.provider_id IS '身份提供商ID';
COMMENT ON COLUMN t_user_external_identities.external_id IS '外部系统中的用户ID';
COMMENT ON COLUMN t_user_external_identities.external_username IS '外部系统中的用户名';
COMMENT ON COLUMN t_user_external_identities.last_login_at IS '最后登录时间';


-- =====================================================
-- 初始化数据
-- =====================================================

-- 插入示例LDAP提供商配置（可选，用于演示）
-- INSERT INTO t_identity_providers (name, type, config, enabled, priority, role_mapping)
-- VALUES (
--     'corporate_ldap',
--     'ldap',
--     '{
--         "server": "ldap://ldap.example.com:389",
--         "base_dn": "dc=example,dc=com",
--         "user_search_base": "ou=users,dc=example,dc=com",
--         "group_search_base": "ou=groups,dc=example,dc=com",
--         "user_filter": "(uid={username})",
--         "use_ssl": false,
--         "use_tls": true
--     }',
--     false,
--     10,
--     '{"cn=admins,ou=groups,dc=example,dc=com": 1, "cn=users,ou=groups,dc=example,dc=com": 2}'
-- );

-- 插入示例OAuth2提供商配置（可选，用于演示）
-- INSERT INTO t_identity_providers (name, type, config, enabled, priority, role_mapping)
-- VALUES (
--     'azure_ad',
--     'oauth2',
--     '{
--         "client_id": "your-client-id",
--         "client_secret": "your-client-secret",
--         "authorization_url": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize",
--         "token_url": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
--         "userinfo_url": "https://graph.microsoft.com/v1.0/me",
--         "scope": "openid profile email"
--     }',
--     false,
--     20,
--     '{"admin_role": 1, "user_role": 2}'
-- );


-- =====================================================
-- 更新时间戳触发器
-- =====================================================

-- 创建更新时间戳函数（如果不存在）
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为身份提供商表创建触发器
DROP TRIGGER IF EXISTS update_identity_providers_updated_at ON t_identity_providers;
CREATE TRIGGER update_identity_providers_updated_at
    BEFORE UPDATE ON t_identity_providers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 为用户外部身份表创建触发器
DROP TRIGGER IF EXISTS update_user_external_identities_updated_at ON t_user_external_identities;
CREATE TRIGGER update_user_external_identities_updated_at
    BEFORE UPDATE ON t_user_external_identities
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- =====================================================
-- 回滚脚本（如需回滚，执行以下语句）
-- =====================================================
-- DROP TRIGGER IF EXISTS update_user_external_identities_updated_at ON t_user_external_identities;
-- DROP TRIGGER IF EXISTS update_identity_providers_updated_at ON t_identity_providers;
-- DROP TABLE IF EXISTS t_user_external_identities;
-- DROP TABLE IF EXISTS t_identity_providers;
