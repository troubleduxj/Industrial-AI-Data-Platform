-- =====================================================
-- 预测结果时序存储表结构
-- 需求: 4.2 - TDengine应使用pred_{category}超级表结构
-- =====================================================

-- 说明：
-- 本迁移脚本定义了预测结果在TDengine中的存储结构
-- 使用超级表(STABLE)模式，支持按资产类别动态创建子表
-- 表命名规范: pred_{category_code} 作为超级表名
-- 子表命名规范: pred_{category_code}_{asset_code}

-- =====================================================
-- 预测结果超级表模板
-- =====================================================

-- 通用预测结果超级表模板
-- 实际使用时，需要根据资产类别动态创建
-- 例如: pred_motor, pred_pump, pred_compressor 等

-- 创建示例超级表 (电机类别)
CREATE STABLE IF NOT EXISTS pred_motor (
    ts TIMESTAMP,                           -- 预测时间戳
    model_id INT,                           -- 模型ID
    model_version NCHAR(32),                -- 模型版本号
    predicted_value DOUBLE,                 -- 预测值
    confidence DOUBLE,                      -- 置信度 (0-1)
    is_anomaly BOOL,                        -- 是否异常
    anomaly_score DOUBLE,                   -- 异常分数
    target_time TIMESTAMP,                  -- 目标预测时间
    actual_value DOUBLE,                    -- 实际值（用于后续评估）
    prediction_details NCHAR(2048)          -- 预测详情JSON
) TAGS (
    asset_id BIGINT,                        -- 资产ID
    asset_code NCHAR(64)                    -- 资产编码
);

-- 创建示例超级表 (泵类别)
CREATE STABLE IF NOT EXISTS pred_pump (
    ts TIMESTAMP,
    model_id INT,
    model_version NCHAR(32),
    predicted_value DOUBLE,
    confidence DOUBLE,
    is_anomaly BOOL,
    anomaly_score DOUBLE,
    target_time TIMESTAMP,
    actual_value DOUBLE,
    prediction_details NCHAR(2048)
) TAGS (
    asset_id BIGINT,
    asset_code NCHAR(64)
);

-- 创建示例超级表 (压缩机类别)
CREATE STABLE IF NOT EXISTS pred_compressor (
    ts TIMESTAMP,
    model_id INT,
    model_version NCHAR(32),
    predicted_value DOUBLE,
    confidence DOUBLE,
    is_anomaly BOOL,
    anomaly_score DOUBLE,
    target_time TIMESTAMP,
    actual_value DOUBLE,
    prediction_details NCHAR(2048)
) TAGS (
    asset_id BIGINT,
    asset_code NCHAR(64)
);

-- =====================================================
-- 子表创建示例
-- =====================================================

-- 子表会在运行时根据资产动态创建
-- 示例:
-- CREATE TABLE pred_motor_MOTOR001 USING pred_motor TAGS (1, 'MOTOR001');
-- CREATE TABLE pred_pump_PUMP001 USING pred_pump TAGS (2, 'PUMP001');

-- =====================================================
-- 索引说明
-- =====================================================

-- TDengine自动为时间戳列创建索引
-- TAGS列自动建立索引，支持高效的按资产查询
-- 查询示例:
-- SELECT * FROM pred_motor WHERE asset_code = 'MOTOR001' AND ts >= NOW() - 1h;
-- SELECT AVG(predicted_value) FROM pred_motor WHERE ts >= NOW() - 24h GROUP BY asset_code;

-- =====================================================
-- 数据保留策略
-- =====================================================

-- 建议配置数据保留策略（根据实际需求调整）
-- ALTER DATABASE {database_name} KEEP 365;  -- 保留365天数据

-- =====================================================
-- 超级表创建SQL模板（供程序动态使用）
-- =====================================================

-- 以下是程序动态创建超级表时使用的SQL模板:
/*
CREATE STABLE IF NOT EXISTS pred_{category_code} (
    ts TIMESTAMP,
    model_id INT,
    model_version NCHAR(32),
    predicted_value DOUBLE,
    confidence DOUBLE,
    is_anomaly BOOL,
    anomaly_score DOUBLE,
    target_time TIMESTAMP,
    actual_value DOUBLE,
    prediction_details NCHAR(2048)
) TAGS (
    asset_id BIGINT,
    asset_code NCHAR(64)
);
*/

-- 子表创建SQL模板:
/*
CREATE TABLE IF NOT EXISTS pred_{category_code}_{asset_code}
USING pred_{category_code}
TAGS ({asset_id}, '{asset_code}');
*/
