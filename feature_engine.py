# 特征工程引擎 - 自动化特征计算与管理
# 此文件为向后兼容层，实际实现在 app/services/feature_engine.py

"""
核心功能：
1. 基于JSON DSL定义特征计算逻辑
2. 自动生成TDengine流计算SQL
3. 特征血缘关系管理
4. 特征质量监控

注意：此文件保留用于向后兼容，新代码请使用 app/services/feature_engine.py
"""

# 从新的服务模块导入所有组件
from app.services.feature_engine import (
    # 常量和枚举
    AggregationFunction,
    DataType,
    DEFAULT_WINDOW,
    DEFAULT_SLIDE_INTERVAL,
    DEFAULT_GROUP_BY,
    
    # 数据类
    ParsedFeatureConfig,
    ValidationResult,
    QualityMetrics,
    
    # 核心类
    FeatureDSLParser,
    BatchFeatureParser,
    TDengineStreamGenerator,
    FeatureQualityMonitor,
    FeatureManager,
    
    # 全局实例
    feature_dsl_parser,
    batch_feature_parser,
    stream_generator,
    feature_quality_monitor,
    feature_manager,
    
    # 便捷函数
    parse_feature_config,
    validate_feature_config,
    get_supported_functions,
)

# 为了向后兼容，保留原有的导出
__all__ = [
    # 枚举
    "AggregationFunction",
    "DataType",
    
    # 数据类
    "ParsedFeatureConfig",
    "ValidationResult",
    "QualityMetrics",
    
    # 核心类
    "FeatureDSLParser",
    "BatchFeatureParser",
    "TDengineStreamGenerator",
    "FeatureQualityMonitor",
    "FeatureManager",
    
    # 全局实例
    "feature_dsl_parser",
    "batch_feature_parser",
    "stream_generator",
    "feature_quality_monitor",
    "feature_manager",
    
    # 便捷函数
    "parse_feature_config",
    "validate_feature_config",
    "get_supported_functions",
]


# =====================================================
# 使用示例
# =====================================================

async def example_usage():
    """特征工程使用示例"""
    import asyncio
    from datetime import datetime, timedelta
    
    # 1. 定义特征配置
    feature_configs = [
        {
            "name": "avg_current_1h",
            "source_signal": "current",
            "function": "avg",
            "window": "1h",
            "slide_interval": "10m"
        },
        {
            "name": "max_temp_1h", 
            "source_signal": "temperature",
            "function": "max",
            "window": "1h",
            "slide_interval": "10m"
        },
        {
            "name": "vibration_stddev_1h",
            "source_signal": "vibration", 
            "function": "stddev",
            "window": "1h",
            "slide_interval": "10m"
        }
    ]
    
    # 2. 创建特征视图
    result = await feature_manager.create_feature_view(
        category_code="motor",
        view_name="health_features",
        feature_configs=feature_configs
    )
    
    print(f"特征视图创建结果: {result}")
    
    # 3. 获取特征数据
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=2)
    
    feature_data = await feature_manager.get_feature_data(
        category_code="motor",
        view_name="health_features", 
        asset_id=1,
        start_time=start_time,
        end_time=end_time
    )
    
    print(f"获取到 {len(feature_data)} 条特征数据")
    
    # 4. 检查特征质量
    quality_report = await feature_manager.check_view_quality(
        category_code="motor",
        view_name="health_features"
    )
    
    print(f"特征质量报告: {quality_report}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())