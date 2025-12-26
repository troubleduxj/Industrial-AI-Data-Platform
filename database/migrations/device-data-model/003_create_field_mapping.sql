-- =====================================================
-- 003: 创建 t_device_field_mapping 表
-- 
-- 目的: 创建PostgreSQL字段与TDengine列的映射关系表
-- 原则: 新增表，不修改现有表
-- 兼容性: 通过外键关联现有 t_device_field 表
-- =====================================================

-- 开始事务
BEGIN;

-- 1. 创建字段映射表
CREATE TABLE IF NOT EXISTS t_device_field_mapping (
    -- 基础字段
    id SERIAL PRIMARY KEY,
    device_type_code VARCHAR(50) NOT NULL,
    
    -- TDengine信息
    tdengine_database VARCHAR(100) NOT NULL,
    tdengine_stable VARCHAR(100) NOT NULL,
    tdengine_column VARCHAR(100) NOT NULL,
    
    -- ⭐ 关联字段定义ID（外键）
    device_field_id INTEGER NOT NULL,
    
    -- 数据转换规则（JSONB格式）
    transform_rule JSONB,
    /* transform_rule 格式示例:
    {
        "type": "expression",
        "expression": "value * 0.001",
        "conditions": [
            {"if": "value < 0", "then": 0},
            {"if": "value > 500", "then": 500}
        ],
        "unit_conversion": {
            "from": "mA",
            "to": "A",
            "factor": 0.001
        }
    }
    */
    
    -- 标记字段
    is_tag BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- ⭐ 外键约束：关联现有 t_device_field 表
    CONSTRAINT fk_field_mapping_device_field 
        FOREIGN KEY (device_field_id) 
        REFERENCES t_device_field(id) 
        ON DELETE CASCADE,
    
    -- 唯一性约束：同一超级表的同一列只能映射一次
    CONSTRAINT uk_stable_column 
        UNIQUE (tdengine_stable, tdengine_column)
);

-- 2. 添加表注释
COMMENT ON TABLE t_device_field_mapping IS '设备字段映射表（PostgreSQL ↔ TDengine）';
COMMENT ON COLUMN t_device_field_mapping.device_type_code IS '设备类型代码';
COMMENT ON COLUMN t_device_field_mapping.tdengine_database IS 'TDengine数据库名';
COMMENT ON COLUMN t_device_field_mapping.tdengine_stable IS 'TDengine超级表名';
COMMENT ON COLUMN t_device_field_mapping.tdengine_column IS 'TDengine列名';
COMMENT ON COLUMN t_device_field_mapping.device_field_id IS '关联的字段定义ID（外键）';
COMMENT ON COLUMN t_device_field_mapping.transform_rule IS '数据转换规则（JSONB），支持表达式和条件转换';
COMMENT ON COLUMN t_device_field_mapping.is_tag IS '是否为TDengine TAG列';
COMMENT ON COLUMN t_device_field_mapping.is_active IS '是否激活';

-- 3. 创建索引
CREATE INDEX IF NOT EXISTS idx_field_mapping_device_type 
ON t_device_field_mapping(device_type_code);

CREATE INDEX IF NOT EXISTS idx_field_mapping_field_id 
ON t_device_field_mapping(device_field_id);

CREATE INDEX IF NOT EXISTS idx_field_mapping_stable 
ON t_device_field_mapping(tdengine_stable);

CREATE INDEX IF NOT EXISTS idx_field_mapping_database 
ON t_device_field_mapping(tdengine_database, tdengine_stable);

CREATE INDEX IF NOT EXISTS idx_field_mapping_tag 
ON t_device_field_mapping(is_tag) 
WHERE is_tag = TRUE;

CREATE INDEX IF NOT EXISTS idx_field_mapping_active 
ON t_device_field_mapping(device_type_code, is_active) 
WHERE is_active = TRUE;

-- 4. 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_field_mapping_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_field_mapping_timestamp
BEFORE UPDATE ON t_device_field_mapping
FOR EACH ROW
EXECUTE FUNCTION update_field_mapping_timestamp();

-- 提交事务
COMMIT;

-- =====================================================
-- 验证脚本执行结果
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE '✅ 003_create_field_mapping.sql 执行成功！';
    RAISE NOTICE '   - 创建表: t_device_field_mapping';
    RAISE NOTICE '   - 外键关联: t_device_field.id';
    RAISE NOTICE '   - 唯一约束: (tdengine_stable, tdengine_column)';
    RAISE NOTICE '   - 创建索引: 6个（device_type, field_id, stable, database, tag, active）';
    RAISE NOTICE '   - 创建触发器: update_field_mapping_timestamp';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  注意: 现有表完全不受影响';
END $$;

