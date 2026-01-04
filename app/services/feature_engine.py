# 特征工程引擎 - 自动化特征计算与管理
# 实现需求3：自动化特征工程

"""
核心功能：
1. 基于JSON DSL定义特征计算逻辑
2. 自动生成TDengine流计算SQL
3. 特征血缘关系管理
4. 特征质量监控
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from loguru import logger


# =====================================================
# 常量定义
# =====================================================

class AggregationFunction(str, Enum):
    """支持的聚合函数"""
    AVG = "avg"
    SUM = "sum"
    MAX = "max"
    MIN = "min"
    COUNT = "count"
    STDDEV = "stddev"
    FIRST = "first"
    LAST = "last"
    DIFF = "diff"
    DERIVATIVE = "derivative"
    SPREAD = "spread"
    PERCENTILE = "percentile"
    
    @classmethod
    def values(cls) -> List[str]:
        return [e.value for e in cls]


class DataType(str, Enum):
    """支持的数据类型"""
    FLOAT = "float"
    INT = "int"
    BOOL = "bool"
    STRING = "string"
    DOUBLE = "double"
    BIGINT = "bigint"
    TIMESTAMP = "timestamp"


# 时间窗口正则表达式
WINDOW_PATTERN = re.compile(r'^(\d+)(s|m|h|d|w)$')

# 默认配置
DEFAULT_WINDOW = "1h"
DEFAULT_SLIDE_INTERVAL = "10m"
DEFAULT_GROUP_BY = ["asset_id"]


# =====================================================
# 数据类定义
# =====================================================

@dataclass
class ParsedFeatureConfig:
    """解析后的特征配置"""
    name: str
    source_signal: str
    function: str
    window: str
    slide_interval: str
    filters: Dict[str, Any]
    group_by: List[str]
    percentile_value: Optional[int] = None
    description: Optional[str] = None
    output_type: str = "double"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "source_signal": self.source_signal,
            "function": self.function,
            "window": self.window,
            "slide_interval": self.slide_interval,
            "filters": self.filters,
            "group_by": self.group_by,
            "percentile_value": self.percentile_value,
            "description": self.description,
            "output_type": self.output_type
        }


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, error: str):
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        self.warnings.append(warning)


# =====================================================
# 特征定义DSL解析器
# =====================================================

class FeatureDSLParser:
    """
    特征定义DSL解析器
    
    支持的DSL格式:
    {
        "name": "avg_current_1h",           # 必填：特征名称
        "source_signal": "current",          # 必填：源信号
        "function": "avg",                   # 必填：聚合函数
        "window": "1h",                      # 可选：时间窗口，默认1h
        "slide_interval": "10m",             # 可选：滑动间隔，默认10m
        "filters": {"status": "online"},     # 可选：过滤条件
        "group_by": ["asset_id"],            # 可选：分组字段
        "percentile": 95,                    # 可选：百分位数（仅percentile函数）
        "description": "1小时平均电流"        # 可选：描述
    }
    """
    
    # 支持的聚合函数
    SUPPORTED_FUNCTIONS = AggregationFunction.values()
    
    # 需要额外参数的函数
    FUNCTIONS_WITH_PARAMS = {"percentile"}
    
    # 函数输出类型映射
    FUNCTION_OUTPUT_TYPES = {
        "count": "bigint",
        "avg": "double",
        "sum": "double",
        "max": "double",
        "min": "double",
        "stddev": "double",
        "first": "double",
        "last": "double",
        "diff": "double",
        "derivative": "double",
        "spread": "double",
        "percentile": "double"
    }
    
    @classmethod
    def parse_feature_config(cls, config: Dict[str, Any]) -> ParsedFeatureConfig:
        """
        解析特征配置
        
        Args:
            config: 原始特征配置字典
            
        Returns:
            ParsedFeatureConfig: 解析后的标准化配置
            
        Raises:
            ValueError: 配置无效时抛出
        """
        # 验证配置
        validation = cls.validate_config(config)
        if not validation.is_valid:
            raise ValueError(f"特征配置无效: {'; '.join(validation.errors)}")
        
        # 提取并标准化字段
        name = config.get("name", "").strip()
        source_signal = config.get("source_signal", "").strip()
        function = config.get("function", "avg").lower().strip()
        window = config.get("window", DEFAULT_WINDOW).strip()
        slide_interval = config.get("slide_interval", DEFAULT_SLIDE_INTERVAL).strip()
        filters = config.get("filters", {})
        group_by = config.get("group_by", DEFAULT_GROUP_BY.copy())
        percentile_value = config.get("percentile") if function == "percentile" else None
        description = config.get("description")
        
        # 确定输出类型
        output_type = cls.FUNCTION_OUTPUT_TYPES.get(function, "double")
        
        return ParsedFeatureConfig(
            name=name,
            source_signal=source_signal,
            function=function,
            window=window,
            slide_interval=slide_interval,
            filters=filters if isinstance(filters, dict) else {},
            group_by=group_by if isinstance(group_by, list) else [group_by],
            percentile_value=percentile_value,
            description=description,
            output_type=output_type
        )
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> ValidationResult:
        """
        验证特征配置
        
        Args:
            config: 特征配置字典
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True)
        
        # 检查是否为字典
        if not isinstance(config, dict):
            result.add_error("配置必须是字典类型")
            return result
        
        # 验证必填字段
        cls._validate_required_fields(config, result)
        
        # 如果必填字段验证失败，直接返回
        if not result.is_valid:
            return result
        
        # 验证聚合函数
        cls._validate_function(config, result)
        
        # 验证时间窗口
        cls._validate_window(config.get("window", DEFAULT_WINDOW), "window", result)
        
        # 验证滑动间隔
        if "slide_interval" in config:
            cls._validate_window(config["slide_interval"], "slide_interval", result)
        
        # 验证过滤条件
        cls._validate_filters(config.get("filters", {}), result)
        
        # 验证分组字段
        cls._validate_group_by(config.get("group_by", DEFAULT_GROUP_BY), result)
        
        # 验证特征名称格式
        cls._validate_name_format(config.get("name", ""), result)
        
        return result
    
    @classmethod
    def _validate_required_fields(cls, config: Dict, result: ValidationResult):
        """验证必填字段"""
        required_fields = ["name", "source_signal", "function"]
        
        for field_name in required_fields:
            value = config.get(field_name)
            if value is None:
                result.add_error(f"缺少必填字段: {field_name}")
            elif isinstance(value, str) and not value.strip():
                result.add_error(f"字段 {field_name} 不能为空")
    
    @classmethod
    def _validate_function(cls, config: Dict, result: ValidationResult):
        """验证聚合函数"""
        function = config.get("function", "").lower().strip()
        
        if function not in cls.SUPPORTED_FUNCTIONS:
            result.add_error(
                f"不支持的聚合函数: {function}。"
                f"支持的函数: {', '.join(cls.SUPPORTED_FUNCTIONS)}"
            )
            return
        
        # 检查需要额外参数的函数
        if function == "percentile":
            percentile = config.get("percentile")
            if percentile is None:
                result.add_error("percentile函数需要指定percentile参数")
            elif not isinstance(percentile, (int, float)):
                result.add_error("percentile参数必须是数字")
            elif not (0 <= percentile <= 100):
                result.add_error("percentile参数必须在0-100之间")
    
    @classmethod
    def _validate_window(cls, window: str, field_name: str, result: ValidationResult):
        """验证时间窗口格式"""
        if not isinstance(window, str):
            result.add_error(f"{field_name} 必须是字符串类型")
            return
        
        window = window.strip()
        if not WINDOW_PATTERN.match(window):
            result.add_error(
                f"{field_name} 格式无效: {window}。"
                f"有效格式: 数字+单位(s/m/h/d/w)，例如: 1h, 30m, 1d"
            )
    
    @classmethod
    def _validate_filters(cls, filters: Any, result: ValidationResult):
        """验证过滤条件"""
        if filters is None:
            return
        
        if not isinstance(filters, dict):
            result.add_error("filters 必须是字典类型")
            return
        
        # 检查过滤条件的值类型
        for key, value in filters.items():
            if not isinstance(key, str):
                result.add_error(f"过滤条件的键必须是字符串: {key}")
            if value is not None and not isinstance(value, (str, int, float, bool, list)):
                result.add_error(f"过滤条件 {key} 的值类型不支持: {type(value)}")
    
    @classmethod
    def _validate_group_by(cls, group_by: Any, result: ValidationResult):
        """验证分组字段"""
        if group_by is None:
            return
        
        if isinstance(group_by, str):
            # 单个字段，转换为列表
            return
        
        if not isinstance(group_by, list):
            result.add_error("group_by 必须是字符串或字符串列表")
            return
        
        for item in group_by:
            if not isinstance(item, str):
                result.add_error(f"group_by 中的元素必须是字符串: {item}")
    
    @classmethod
    def _validate_name_format(cls, name: str, result: ValidationResult):
        """验证特征名称格式"""
        if not name:
            return
        
        # 特征名称应该是有效的标识符
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
            result.add_error(
                f"特征名称格式无效: {name}。"
                f"名称必须以字母或下划线开头，只能包含字母、数字和下划线"
            )
        
        # 检查长度
        if len(name) > 64:
            result.add_error(f"特征名称过长: {len(name)}字符，最大64字符")
    
    @classmethod
    def validate_function(cls, function: str) -> bool:
        """
        验证聚合函数是否支持
        
        Args:
            function: 聚合函数名称
            
        Returns:
            bool: 是否支持
        """
        return function.lower().strip() in cls.SUPPORTED_FUNCTIONS
    
    @classmethod
    def parse_window_to_seconds(cls, window: str) -> int:
        """
        将时间窗口转换为秒数
        
        Args:
            window: 时间窗口字符串，如 "1h", "30m"
            
        Returns:
            int: 秒数
        """
        match = WINDOW_PATTERN.match(window.strip())
        if not match:
            raise ValueError(f"无效的时间窗口格式: {window}")
        
        value = int(match.group(1))
        unit = match.group(2)
        
        unit_multipliers = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400,
            'w': 604800
        }
        
        return value * unit_multipliers[unit]
    
    @classmethod
    def get_supported_functions(cls) -> List[str]:
        """获取支持的聚合函数列表"""
        return cls.SUPPORTED_FUNCTIONS.copy()
    
    @classmethod
    def get_function_description(cls, function: str) -> str:
        """获取聚合函数描述"""
        descriptions = {
            "avg": "计算平均值",
            "sum": "计算总和",
            "max": "获取最大值",
            "min": "获取最小值",
            "count": "计算数量",
            "stddev": "计算标准差",
            "first": "获取第一个值",
            "last": "获取最后一个值",
            "diff": "计算差值",
            "derivative": "计算导数",
            "spread": "计算极差(最大值-最小值)",
            "percentile": "计算百分位数"
        }
        return descriptions.get(function.lower(), "未知函数")


# =====================================================
# 批量解析器
# =====================================================

class BatchFeatureParser:
    """批量特征解析器"""
    
    @staticmethod
    def parse_multiple(configs: List[Dict[str, Any]]) -> Tuple[List[ParsedFeatureConfig], List[Dict]]:
        """
        批量解析特征配置
        
        Args:
            configs: 特征配置列表
            
        Returns:
            Tuple[List[ParsedFeatureConfig], List[Dict]]: 
                成功解析的配置列表和失败的配置信息
        """
        parsed_configs = []
        failed_configs = []
        
        for i, config in enumerate(configs):
            try:
                parsed = FeatureDSLParser.parse_feature_config(config)
                parsed_configs.append(parsed)
            except ValueError as e:
                failed_configs.append({
                    "index": i,
                    "config": config,
                    "error": str(e)
                })
        
        return parsed_configs, failed_configs
    
    @staticmethod
    def validate_multiple(configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量验证特征配置
        
        Args:
            configs: 特征配置列表
            
        Returns:
            Dict: 验证结果汇总
        """
        results = {
            "total": len(configs),
            "valid": 0,
            "invalid": 0,
            "details": []
        }
        
        for i, config in enumerate(configs):
            validation = FeatureDSLParser.validate_config(config)
            detail = {
                "index": i,
                "name": config.get("name", f"config_{i}"),
                "is_valid": validation.is_valid,
                "errors": validation.errors,
                "warnings": validation.warnings
            }
            results["details"].append(detail)
            
            if validation.is_valid:
                results["valid"] += 1
            else:
                results["invalid"] += 1
        
        return results


# =====================================================
# 全局实例
# =====================================================

feature_dsl_parser = FeatureDSLParser()
batch_feature_parser = BatchFeatureParser()


# =====================================================
# TDengine流计算SQL生成器
# =====================================================

class TDengineStreamGenerator:
    """
    TDengine流计算SQL生成器
    
    根据特征配置自动生成TDengine流计算SQL语句
    """
    
    def __init__(self, database: str = "devicemonitor"):
        self._td_client = None
        self.database = database
    
    @property
    def td_client(self):
        """延迟加载TDengine客户端"""
        if self._td_client is None:
            try:
                from app.core.tdengine_connector import td_client
                self._td_client = td_client
            except ImportError:
                logger.warning("TDengine客户端未配置，使用模拟模式")
                self._td_client = None
        return self._td_client
    
    def generate_stream_sql(
        self, 
        category_code: str, 
        feature_configs: List[Dict[str, Any]],
        database: Optional[str] = None
    ) -> str:
        """
        生成流计算SQL
        
        Args:
            category_code: 资产类别编码
            feature_configs: 特征配置列表
            database: 数据库名称（可选）
            
        Returns:
            str: 生成的SQL语句
        """
        db = database or self.database
        
        # 解析所有特征配置
        parsed_configs = []
        for config in feature_configs:
            parsed = FeatureDSLParser.parse_feature_config(config)
            parsed_configs.append(parsed)
        
        if not parsed_configs:
            raise ValueError("至少需要一个特征配置")
        
        # 1. 构建SELECT子句
        select_items = self._build_select_clause(parsed_configs)
        
        # 2. 构建FROM子句
        source_table = f"{db}.raw_{category_code}"
        
        # 3. 构建WHERE子句
        where_clause = self._build_where_clause(parsed_configs)
        
        # 4. 构建PARTITION BY子句（TDengine 3.0+）
        partition_clause = self._build_partition_clause(parsed_configs)
        
        # 5. 构建INTERVAL子句
        interval_clause = self._build_interval_clause(parsed_configs[0])
        
        # 6. 组装完整SQL
        sql_parts = [
            "SELECT",
            f"    {', '.join(select_items)}",
            f"FROM {source_table}"
        ]
        
        if where_clause:
            sql_parts.append(f"WHERE {where_clause}")
        
        if partition_clause:
            sql_parts.append(f"PARTITION BY {partition_clause}")
        
        sql_parts.append(interval_clause)
        
        return "\n".join(sql_parts)
    
    def _build_select_clause(self, configs: List[ParsedFeatureConfig]) -> List[str]:
        """构建SELECT子句"""
        select_items = ["_wstart as ts"]
        
        for config in configs:
            function = config.function.upper()
            source_signal = config.source_signal
            feature_name = config.name
            
            # 构建聚合表达式
            if function == "PERCENTILE":
                percentile = config.percentile_value or 50
                select_items.append(
                    f"PERCENTILE({source_signal}, {percentile}) as {feature_name}"
                )
            elif function == "DERIVATIVE":
                select_items.append(f"DERIVATIVE({source_signal}, 1s) as {feature_name}")
            elif function == "SPREAD":
                select_items.append(f"SPREAD({source_signal}) as {feature_name}")
            elif function == "DIFF":
                select_items.append(f"DIFF({source_signal}) as {feature_name}")
            else:
                select_items.append(f"{function}({source_signal}) as {feature_name}")
        
        return select_items
    
    def _build_where_clause(self, configs: List[ParsedFeatureConfig]) -> str:
        """构建WHERE子句"""
        conditions = []
        
        # 合并所有配置的过滤条件
        all_filters = {}
        for config in configs:
            all_filters.update(config.filters)
        
        for key, value in all_filters.items():
            if isinstance(value, str):
                conditions.append(f"{key} = '{value}'")
            elif isinstance(value, bool):
                conditions.append(f"{key} = {str(value).lower()}")
            elif isinstance(value, (int, float)):
                conditions.append(f"{key} = {value}")
            elif isinstance(value, list):
                # IN 条件
                if all(isinstance(v, str) for v in value):
                    values_str = ", ".join(f"'{v}'" for v in value)
                else:
                    values_str = ", ".join(str(v) for v in value)
                conditions.append(f"{key} IN ({values_str})")
        
        return " AND ".join(conditions) if conditions else ""
    
    def _build_partition_clause(self, configs: List[ParsedFeatureConfig]) -> str:
        """构建PARTITION BY子句"""
        # 使用第一个配置的group_by
        group_by = configs[0].group_by if configs else DEFAULT_GROUP_BY
        
        # 过滤掉时间相关的分组（由INTERVAL处理）
        partition_fields = [f for f in group_by if f not in ("ts", "_wstart", "_wend")]
        
        return ", ".join(partition_fields) if partition_fields else "tbname"
    
    def _build_interval_clause(self, config: ParsedFeatureConfig) -> str:
        """构建INTERVAL子句"""
        window = config.window
        slide_interval = config.slide_interval
        
        if slide_interval and slide_interval != window:
            return f"INTERVAL({window}) SLIDING({slide_interval})"
        else:
            return f"INTERVAL({window})"
    
    def generate_create_stream_sql(
        self,
        stream_name: str,
        target_table: str,
        select_sql: str,
        trigger_mode: str = "AT_ONCE",
        watermark: str = "5s",
        ignore_expired: bool = True
    ) -> str:
        """
        生成CREATE STREAM语句
        
        Args:
            stream_name: 流计算名称
            target_table: 目标表名
            select_sql: SELECT查询语句
            trigger_mode: 触发模式 (AT_ONCE, WINDOW_CLOSE, MAX_DELAY)
            watermark: 水位线
            ignore_expired: 是否忽略过期数据
            
        Returns:
            str: CREATE STREAM SQL语句
        """
        options = []
        
        if trigger_mode:
            options.append(f"TRIGGER {trigger_mode}")
        
        if watermark:
            options.append(f"WATERMARK {watermark}")
        
        if ignore_expired:
            options.append("IGNORE EXPIRED 1")
        
        options_str = " ".join(options)
        
        sql = f"""CREATE STREAM IF NOT EXISTS {stream_name}
{options_str}
INTO {target_table}
AS
{select_sql}"""
        
        return sql
    
    def generate_feature_stable_sql(
        self,
        table_name: str,
        feature_configs: List[Dict[str, Any]],
        database: Optional[str] = None
    ) -> str:
        """
        生成特征超级表创建SQL
        
        Args:
            table_name: 表名
            feature_configs: 特征配置列表
            database: 数据库名称
            
        Returns:
            str: CREATE STABLE SQL语句
        """
        db = database or self.database
        
        # 构建列定义
        columns = ["ts TIMESTAMP"]
        
        for config in feature_configs:
            parsed = FeatureDSLParser.parse_feature_config(config)
            feature_name = parsed.name
            output_type = parsed.output_type.upper()
            
            # 映射输出类型
            type_mapping = {
                "DOUBLE": "DOUBLE",
                "BIGINT": "BIGINT",
                "FLOAT": "FLOAT",
                "INT": "INT"
            }
            col_type = type_mapping.get(output_type, "DOUBLE")
            columns.append(f"{feature_name} {col_type}")
        
        # 构建TAG定义
        tags = ["asset_id BIGINT"]
        
        columns_str = ",\n    ".join(columns)
        tags_str = ",\n    ".join(tags)
        
        sql = f"""CREATE STABLE IF NOT EXISTS {db}.{table_name} (
    {columns_str}
) TAGS (
    {tags_str}
)"""
        
        return sql
    
    async def create_stream(
        self,
        stream_name: str,
        target_table: str,
        select_sql: str,
        **kwargs
    ) -> bool:
        """
        创建流计算任务
        
        Args:
            stream_name: 流计算名称
            target_table: 目标表名
            select_sql: SELECT查询语句
            **kwargs: 其他CREATE STREAM选项
            
        Returns:
            bool: 创建是否成功
        """
        try:
            # 1. 删除已存在的流
            await self._drop_stream_if_exists(stream_name)
            
            # 2. 生成CREATE STREAM SQL
            create_sql = self.generate_create_stream_sql(
                stream_name, target_table, select_sql, **kwargs
            )
            
            logger.debug(f"创建流计算SQL:\n{create_sql}")
            
            # 3. 执行创建
            if self.td_client:
                await self.td_client.execute(create_sql)
            else:
                logger.warning(f"TDengine客户端未配置，跳过流计算创建: {stream_name}")
                return True
            
            logger.info(f"✅ 流计算创建成功: {stream_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建流计算失败: {e}")
            return False
    
    async def _drop_stream_if_exists(self, stream_name: str):
        """删除已存在的流"""
        try:
            if self.td_client:
                drop_sql = f"DROP STREAM IF EXISTS {stream_name}"
                await self.td_client.execute(drop_sql)
                logger.debug(f"已删除旧流计算: {stream_name}")
        except Exception as e:
            logger.debug(f"删除流计算时出错（可忽略）: {e}")
    
    async def list_streams(self) -> List[Dict[str, Any]]:
        """列出所有流计算任务"""
        try:
            if self.td_client:
                result = await self.td_client.query("SHOW STREAMS")
                return result
            return []
        except Exception as e:
            logger.error(f"获取流计算列表失败: {e}")
            return []
    
    async def get_stream_status(self, stream_name: str) -> Optional[Dict[str, Any]]:
        """获取流计算状态"""
        try:
            streams = await self.list_streams()
            for stream in streams:
                if stream.get("stream_name") == stream_name:
                    return stream
            return None
        except Exception as e:
            logger.error(f"获取流计算状态失败: {e}")
            return None


# =====================================================
# 特征质量监控
# =====================================================

@dataclass
class QualityMetrics:
    """质量指标"""
    completeness: float  # 完整性 0-1
    freshness: float     # 新鲜度 0-1
    distribution: float  # 分布正常度 0-1
    validity: float      # 有效性 0-1
    
    @property
    def overall_score(self) -> float:
        """综合评分"""
        weights = {
            "completeness": 0.3,
            "freshness": 0.3,
            "distribution": 0.2,
            "validity": 0.2
        }
        return (
            self.completeness * weights["completeness"] +
            self.freshness * weights["freshness"] +
            self.distribution * weights["distribution"] +
            self.validity * weights["validity"]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "completeness": self.completeness,
            "freshness": self.freshness,
            "distribution": self.distribution,
            "validity": self.validity,
            "overall_score": self.overall_score
        }


class FeatureQualityMonitor:
    """
    特征质量监控器
    
    监控特征数据的质量指标：
    - 完整性：数据点是否完整
    - 新鲜度：数据是否及时更新
    - 分布：数据分布是否正常
    - 有效性：数据值是否在合理范围内
    """
    
    def __init__(self, database: str = "devicemonitor"):
        self._td_client = None
        self.database = database
        
        # 质量阈值配置
        self.thresholds = {
            "freshness_warning_seconds": 3600,    # 1小时
            "freshness_critical_seconds": 7200,   # 2小时
            "completeness_expected_interval": 600, # 10分钟一个数据点
            "null_ratio_threshold": 0.1,          # 空值比例阈值
            "outlier_std_multiplier": 3           # 异常值标准差倍数
        }
    
    @property
    def td_client(self):
        """延迟加载TDengine客户端"""
        if self._td_client is None:
            try:
                from app.core.tdengine_connector import td_client
                self._td_client = td_client
            except ImportError:
                logger.warning("TDengine客户端未配置")
                self._td_client = None
        return self._td_client
    
    async def check_feature_quality(
        self,
        category_code: str,
        view_name: str,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        检查特征质量
        
        Args:
            category_code: 资产类别编码
            view_name: 特征视图名称
            time_range_hours: 检查的时间范围（小时）
            
        Returns:
            Dict: 质量检查报告
        """
        table_name = f"feat_{category_code}_{view_name}"
        full_table_name = f"{self.database}.{table_name}"
        
        try:
            # 1. 检查数据完整性
            completeness = await self._check_completeness(
                full_table_name, time_range_hours
            )
            
            # 2. 检查数据新鲜度
            freshness = await self._check_freshness(full_table_name)
            
            # 3. 检查数据分布
            distribution = await self._check_distribution(
                full_table_name, time_range_hours
            )
            
            # 4. 检查数据有效性
            validity = await self._check_validity(
                full_table_name, time_range_hours
            )
            
            # 5. 构建质量指标
            metrics = QualityMetrics(
                completeness=completeness,
                freshness=freshness,
                distribution=distribution,
                validity=validity
            )
            
            # 6. 生成质量报告
            report = {
                "table_name": table_name,
                "database": self.database,
                "time_range_hours": time_range_hours,
                "check_time": datetime.now().isoformat(),
                "metrics": metrics.to_dict(),
                "quality_score": metrics.overall_score,
                "status": self._get_quality_status(metrics.overall_score),
                "recommendations": self._generate_recommendations(metrics)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"检查特征质量失败: {e}")
            return {
                "table_name": table_name,
                "error": str(e),
                "check_time": datetime.now().isoformat(),
                "status": "error"
            }
    
    async def _check_completeness(
        self,
        table_name: str,
        time_range_hours: int
    ) -> float:
        """
        检查数据完整性
        
        计算实际数据点数量与预期数量的比例
        """
        try:
            if not self.td_client:
                return 0.8  # 模拟值
            
            # 查询数据点数量
            sql = f"""
            SELECT COUNT(*) as total_count
            FROM {table_name}
            WHERE ts >= NOW() - INTERVAL {time_range_hours} HOUR
            """
            
            result = await self.td_client.query(sql)
            total_count = result[0]["total_count"] if result else 0
            
            # 计算预期数据点数量
            # 假设每个时间窗口产生一个数据点
            expected_interval = self.thresholds["completeness_expected_interval"]
            expected_count = (time_range_hours * 3600) / expected_interval
            
            # 计算完整性比例
            completeness = min(total_count / expected_count, 1.0) if expected_count > 0 else 0.0
            
            return completeness
            
        except Exception as e:
            logger.error(f"检查完整性失败: {e}")
            return 0.0
    
    async def _check_freshness(self, table_name: str) -> float:
        """
        检查数据新鲜度
        
        基于最新数据的时间戳计算新鲜度
        """
        try:
            if not self.td_client:
                return 0.9  # 模拟值
            
            sql = f"""
            SELECT LAST(ts) as latest_time
            FROM {table_name}
            """
            
            result = await self.td_client.query(sql)
            if not result or not result[0].get("latest_time"):
                return 0.0
            
            latest_time = result[0]["latest_time"]
            if isinstance(latest_time, str):
                latest_time = datetime.fromisoformat(latest_time.replace('Z', '+00:00'))
            
            # 计算时间差
            time_diff = datetime.now() - latest_time.replace(tzinfo=None)
            diff_seconds = time_diff.total_seconds()
            
            # 根据时间差计算新鲜度
            warning_threshold = self.thresholds["freshness_warning_seconds"]
            critical_threshold = self.thresholds["freshness_critical_seconds"]
            
            if diff_seconds <= warning_threshold:
                # 在警告阈值内，线性衰减从1.0到0.7
                freshness = 1.0 - (diff_seconds / warning_threshold) * 0.3
            elif diff_seconds <= critical_threshold:
                # 在临界阈值内，线性衰减从0.7到0.3
                ratio = (diff_seconds - warning_threshold) / (critical_threshold - warning_threshold)
                freshness = 0.7 - ratio * 0.4
            else:
                # 超过临界阈值，快速衰减
                extra_hours = (diff_seconds - critical_threshold) / 3600
                freshness = max(0.3 - extra_hours * 0.1, 0.0)
            
            return freshness
            
        except Exception as e:
            logger.error(f"检查新鲜度失败: {e}")
            return 0.0
    
    async def _check_distribution(
        self,
        table_name: str,
        time_range_hours: int
    ) -> float:
        """
        检查数据分布
        
        检测数据是否存在异常分布
        """
        try:
            if not self.td_client:
                return 0.85  # 模拟值
            
            # 获取表的列信息
            columns = await self._get_numeric_columns(table_name)
            
            if not columns:
                return 1.0  # 没有数值列，认为分布正常
            
            distribution_scores = []
            
            for column in columns[:5]:  # 最多检查5个列
                score = await self._check_column_distribution(
                    table_name, column, time_range_hours
                )
                distribution_scores.append(score)
            
            # 返回平均分布得分
            return sum(distribution_scores) / len(distribution_scores) if distribution_scores else 1.0
            
        except Exception as e:
            logger.error(f"检查分布失败: {e}")
            return 0.5
    
    async def _check_column_distribution(
        self,
        table_name: str,
        column: str,
        time_range_hours: int
    ) -> float:
        """检查单列的分布"""
        try:
            sql = f"""
            SELECT 
                AVG({column}) as avg_val,
                STDDEV({column}) as std_val,
                MIN({column}) as min_val,
                MAX({column}) as max_val,
                COUNT({column}) as count_val
            FROM {table_name}
            WHERE ts >= NOW() - INTERVAL {time_range_hours} HOUR
            """
            
            result = await self.td_client.query(sql)
            if not result:
                return 1.0
            
            stats = result[0]
            avg_val = stats.get("avg_val", 0)
            std_val = stats.get("std_val", 0)
            min_val = stats.get("min_val", 0)
            max_val = stats.get("max_val", 0)
            
            # 检查是否有异常
            if std_val == 0:
                # 标准差为0，数据可能有问题
                return 0.5
            
            # 检查极值是否在合理范围内
            std_multiplier = self.thresholds["outlier_std_multiplier"]
            lower_bound = avg_val - std_multiplier * std_val
            upper_bound = avg_val + std_multiplier * std_val
            
            if min_val < lower_bound or max_val > upper_bound:
                # 存在异常值
                return 0.7
            
            return 1.0
            
        except Exception:
            return 0.5
    
    async def _check_validity(
        self,
        table_name: str,
        time_range_hours: int
    ) -> float:
        """
        检查数据有效性
        
        检查空值比例和无效值
        """
        try:
            if not self.td_client:
                return 0.95  # 模拟值
            
            # 获取数值列
            columns = await self._get_numeric_columns(table_name)
            
            if not columns:
                return 1.0
            
            validity_scores = []
            
            for column in columns[:5]:
                score = await self._check_column_validity(
                    table_name, column, time_range_hours
                )
                validity_scores.append(score)
            
            return sum(validity_scores) / len(validity_scores) if validity_scores else 1.0
            
        except Exception as e:
            logger.error(f"检查有效性失败: {e}")
            return 0.5
    
    async def _check_column_validity(
        self,
        table_name: str,
        column: str,
        time_range_hours: int
    ) -> float:
        """检查单列的有效性"""
        try:
            sql = f"""
            SELECT 
                COUNT(*) as total,
                COUNT({column}) as non_null
            FROM {table_name}
            WHERE ts >= NOW() - INTERVAL {time_range_hours} HOUR
            """
            
            result = await self.td_client.query(sql)
            if not result:
                return 1.0
            
            total = result[0].get("total", 0)
            non_null = result[0].get("non_null", 0)
            
            if total == 0:
                return 1.0
            
            # 计算非空比例
            non_null_ratio = non_null / total
            
            # 如果空值比例超过阈值，降低有效性得分
            null_threshold = self.thresholds["null_ratio_threshold"]
            null_ratio = 1 - non_null_ratio
            
            if null_ratio <= null_threshold:
                return 1.0
            else:
                # 线性降低得分
                return max(1.0 - (null_ratio - null_threshold) * 5, 0.0)
            
        except Exception:
            return 0.5
    
    async def _get_numeric_columns(self, table_name: str) -> List[str]:
        """获取表的数值列"""
        try:
            if not self.td_client:
                return []
            
            result = await self.td_client.query(f"DESCRIBE {table_name}")
            
            numeric_types = {"FLOAT", "DOUBLE", "INT", "BIGINT", "SMALLINT", "TINYINT"}
            columns = []
            
            for row in result:
                field = row.get("Field", row.get("field", ""))
                col_type = row.get("Type", row.get("type", "")).upper()
                
                # 跳过时间戳和TAG列
                if field.lower() in ("ts", "_wstart", "_wend"):
                    continue
                if row.get("Note", row.get("note", "")).upper() == "TAG":
                    continue
                
                if any(t in col_type for t in numeric_types):
                    columns.append(field)
            
            return columns
            
        except Exception as e:
            logger.error(f"获取数值列失败: {e}")
            return []
    
    def _get_quality_status(self, score: float) -> str:
        """根据得分获取质量状态"""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.7:
            return "good"
        elif score >= 0.5:
            return "warning"
        else:
            return "critical"
    
    def _generate_recommendations(self, metrics: QualityMetrics) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if metrics.completeness < 0.7:
            recommendations.append(
                "数据完整性较低，请检查数据采集是否正常运行"
            )
        
        if metrics.freshness < 0.7:
            recommendations.append(
                "数据新鲜度较低，请检查流计算任务是否正常执行"
            )
        
        if metrics.distribution < 0.7:
            recommendations.append(
                "数据分布存在异常，建议检查数据源或添加异常值过滤"
            )
        
        if metrics.validity < 0.7:
            recommendations.append(
                "数据有效性较低，存在较多空值或无效值，请检查数据质量"
            )
        
        if not recommendations:
            recommendations.append("数据质量良好，无需特别处理")
        
        return recommendations
    
    async def get_quality_history(
        self,
        category_code: str,
        view_name: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        获取质量历史记录
        
        从数据库获取历史质量检查记录
        """
        try:
            from app.models.platform_upgrade import FeatureView
            
            view = await FeatureView.filter(
                category__code=category_code,
                code=view_name
            ).first()
            
            if not view:
                return []
            
            # 这里可以扩展为从专门的质量记录表获取历史
            # 目前返回最新的质量检查结果
            return [{
                "check_time": view.last_quality_check.isoformat() if view.last_quality_check else None,
                "quality_score": view.quality_score
            }]
            
        except Exception as e:
            logger.error(f"获取质量历史失败: {e}")
            return []
    
    async def save_quality_report(
        self,
        category_code: str,
        view_name: str,
        report: Dict[str, Any]
    ) -> bool:
        """保存质量报告到数据库"""
        try:
            from app.models.platform_upgrade import FeatureView
            
            view = await FeatureView.filter(
                category__code=category_code,
                code=view_name
            ).first()
            
            if view:
                view.last_quality_check = datetime.now()
                view.quality_score = report.get("quality_score", 0)
                await view.save()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"保存质量报告失败: {e}")
            return False


# =====================================================
# 特征管理器
# =====================================================

class FeatureManager:
    """
    特征管理器
    
    统一管理特征的创建、更新、查询和删除
    
    集成功能:
    - FeatureStore: 特征表自动创建和Schema演进 (需求6.1, 6.4)
    - LineageTracker: 特征血缘追踪 (需求6.5)
    """
    
    def __init__(self, database: str = "devicemonitor"):
        self.database = database
        self.sql_generator = TDengineStreamGenerator(database)
        self.quality_monitor = FeatureQualityMonitor(database)
        self._td_client = None
        
        # 集成特征存储和血缘追踪 (需求6.1, 6.5)
        from ai_engine.feature import FeatureStore, LineageTracker
        self.feature_store = FeatureStore(database)
        self.lineage_tracker = LineageTracker()
    
    @property
    def td_client(self):
        """延迟加载TDengine客户端"""
        if self._td_client is None:
            try:
                from app.core.tdengine_connector import td_client
                self._td_client = td_client
            except ImportError:
                logger.warning("TDengine客户端未配置")
                self._td_client = None
        return self._td_client
    
    async def create_feature_view(
        self,
        category_code: str,
        view_name: str,
        feature_configs: List[Dict[str, Any]],
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建特征视图
        
        实现需求6.1: 当激活特征视图时，平台应自动创建feat_{category}_{view}超级表
        实现需求6.2: 特征表应包含时间戳、资产ID和所有特征列
        实现需求6.5: 记录特征血缘信息
        
        Args:
            category_code: 资产类别编码
            view_name: 视图名称
            feature_configs: 特征配置列表
            description: 视图描述
            
        Returns:
            Dict: 创建结果
        """
        try:
            logger.info(f"创建特征视图: {category_code}/{view_name}")
            
            # 1. 验证所有特征配置
            parsed_configs, failed = BatchFeatureParser.parse_multiple(feature_configs)
            
            if failed:
                return {
                    "success": False,
                    "error": "部分特征配置无效",
                    "failed_configs": failed
                }
            
            if not parsed_configs:
                return {
                    "success": False,
                    "error": "没有有效的特征配置"
                }
            
            # 2. 生成表名和流名
            target_table = f"feat_{category_code}_{view_name}"
            stream_name = f"stream_{category_code}_{view_name}"
            
            # 3. 使用FeatureStore创建特征超级表 (需求6.1, 6.2)
            table_created = await self.feature_store.create_feature_table(
                category_code, view_name, feature_configs
            )
            
            if not table_created:
                # 回退到旧方法
                logger.warning("FeatureStore创建表失败，使用旧方法")
                await self._create_feature_stable(target_table, feature_configs)
            
            # 4. 记录特征血缘信息 (需求6.5)
            lineage_count = await self.lineage_tracker.record_lineages_batch(
                category_code, view_name, feature_configs
            )
            logger.info(f"✅ 特征血缘记录成功: {lineage_count}/{len(feature_configs)} 个特征")
            
            # 5. 生成流计算SQL
            select_sql = self.sql_generator.generate_stream_sql(
                category_code, feature_configs
            )
            
            # 6. 创建流计算
            stream_success = await self.sql_generator.create_stream(
                stream_name,
                f"{self.database}.{target_table}",
                select_sql
            )
            
            if not stream_success:
                return {
                    "success": False,
                    "error": "创建流计算失败"
                }
            
            # 7. 保存特征定义到数据库
            await self._save_feature_view(
                category_code, view_name, feature_configs,
                stream_name, target_table, description
            )
            
            logger.info(f"✅ 特征视图创建成功: {view_name}")
            
            return {
                "success": True,
                "view_name": view_name,
                "target_table": target_table,
                "stream_name": stream_name,
                "feature_count": len(parsed_configs),
                "lineage_count": lineage_count,
                "select_sql": select_sql
            }
            
        except Exception as e:
            logger.error(f"❌ 创建特征视图失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _create_feature_stable(
        self,
        table_name: str,
        feature_configs: List[Dict[str, Any]]
    ):
        """创建特征超级表"""
        create_sql = self.sql_generator.generate_feature_stable_sql(
            table_name, feature_configs
        )
        
        logger.debug(f"创建特征表SQL:\n{create_sql}")
        
        if self.td_client:
            await self.td_client.execute(create_sql)
            logger.info(f"✅ 特征表创建成功: {table_name}")
        else:
            logger.warning(f"TDengine客户端未配置，跳过表创建: {table_name}")
    
    async def _save_feature_view(
        self,
        category_code: str,
        view_name: str,
        feature_configs: List[Dict[str, Any]],
        stream_name: str,
        target_table: str,
        description: Optional[str]
    ):
        """保存特征视图到数据库"""
        try:
            from app.models.platform_upgrade import (
                AssetCategory, FeatureDefinition, FeatureView
            )
            
            # 获取资产类别
            category = await AssetCategory.get_or_none(code=category_code)
            if not category:
                logger.warning(f"资产类别不存在: {category_code}")
                return
            
            # 创建特征视图记录
            view, created = await FeatureView.get_or_create(
                category=category,
                code=view_name,
                defaults={
                    "name": view_name,
                    "description": description,
                    "feature_codes": [c.get("name") for c in feature_configs],
                    "stream_name": stream_name,
                    "target_stable": target_table,
                    "status": "active",
                    "is_active": True
                }
            )
            
            if not created:
                # 更新现有视图
                view.feature_codes = [c.get("name") for c in feature_configs]
                view.stream_name = stream_name
                view.target_stable = target_table
                view.status = "active"
                await view.save()
            
            # 创建特征定义记录
            for config in feature_configs:
                parsed = FeatureDSLParser.parse_feature_config(config)
                
                await FeatureDefinition.update_or_create(
                    category=category,
                    code=f"{view_name}_{parsed.name}",
                    defaults={
                        "name": parsed.name,
                        "description": parsed.description,
                        "calculation_config": config,
                        "output_type": parsed.output_type,
                        "stream_name": stream_name,
                        "target_table": target_table,
                        "is_active": True
                    }
                )
            
            logger.info(f"✅ 特征定义保存成功: {len(feature_configs)} 个特征")
            
        except Exception as e:
            logger.error(f"保存特征定义失败: {e}")
    
    async def get_feature_data(
        self,
        category_code: str,
        view_name: str,
        asset_id: int,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000,
        feature_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取特征数据
        
        实现需求6.3: 当查询特征数据时，平台应支持按资产、时间范围和特征名筛选
        
        Args:
            category_code: 资产类别编码
            view_name: 视图名称
            asset_id: 资产ID
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回记录数限制
            feature_names: 特征名称列表 (可选，为空则查询所有特征)
            
        Returns:
            List[Dict]: 特征数据列表
        """
        try:
            # 使用FeatureStore查询特征数据 (需求6.3)
            return await self.feature_store.query_features(
                category_code=category_code,
                view_name=view_name,
                asset_id=asset_id,
                feature_names=feature_names,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
        except Exception as e:
            logger.error(f"获取特征数据失败: {e}")
            # 回退到旧方法
            table_name = f"{self.database}.feat_{category_code}_{view_name}"
            
            sql = f"""
            SELECT * FROM {table_name}
            WHERE asset_id = {asset_id}
            AND ts >= '{start_time.isoformat()}'
            AND ts <= '{end_time.isoformat()}'
            ORDER BY ts DESC
            LIMIT {limit}
            """
            
            try:
                if self.td_client:
                    result = await self.td_client.query(sql)
                    return result
                return []
            except Exception as e2:
                logger.error(f"回退查询也失败: {e2}")
                return []
    
    async def list_feature_views(
        self,
        category_code: str
    ) -> List[Dict[str, Any]]:
        """
        列出特征视图
        
        Args:
            category_code: 资产类别编码
            
        Returns:
            List[Dict]: 特征视图列表
        """
        try:
            from app.models.platform_upgrade import AssetCategory, FeatureView
            
            category = await AssetCategory.get_or_none(code=category_code)
            if not category:
                return []
            
            views = await FeatureView.filter(
                category=category,
                is_active=True
            ).all()
            
            result = []
            for view in views:
                result.append({
                    "id": view.id,
                    "name": view.name,
                    "code": view.code,
                    "description": view.description,
                    "feature_codes": view.feature_codes,
                    "stream_name": view.stream_name,
                    "target_stable": view.target_stable,
                    "status": view.status,
                    "quality_score": view.quality_score,
                    "last_quality_check": view.last_quality_check.isoformat() if view.last_quality_check else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取特征视图列表失败: {e}")
            return []
    
    async def delete_feature_view(
        self,
        category_code: str,
        view_name: str
    ) -> bool:
        """
        删除特征视图
        
        Args:
            category_code: 资产类别编码
            view_name: 视图名称
            
        Returns:
            bool: 删除是否成功
        """
        try:
            stream_name = f"stream_{category_code}_{view_name}"
            
            # 1. 删除流计算
            if self.td_client:
                try:
                    await self.td_client.execute(f"DROP STREAM IF EXISTS {stream_name}")
                except Exception:
                    pass
            
            # 2. 更新数据库记录
            from app.models.platform_upgrade import AssetCategory, FeatureView, FeatureDefinition
            
            category = await AssetCategory.get_or_none(code=category_code)
            if category:
                # 软删除视图
                await FeatureView.filter(
                    category=category,
                    code=view_name
                ).update(is_active=False, status="archived")
                
                # 软删除相关特征定义
                await FeatureDefinition.filter(
                    category=category,
                    code__startswith=f"{view_name}_"
                ).update(is_active=False)
            
            logger.info(f"✅ 特征视图删除成功: {view_name}")
            return True
            
        except Exception as e:
            logger.error(f"删除特征视图失败: {e}")
            return False
    
    async def check_view_quality(
        self,
        category_code: str,
        view_name: str
    ) -> Dict[str, Any]:
        """
        检查特征视图质量
        
        Args:
            category_code: 资产类别编码
            view_name: 视图名称
            
        Returns:
            Dict: 质量报告
        """
        report = await self.quality_monitor.check_feature_quality(
            category_code, view_name
        )
        
        # 保存质量报告
        await self.quality_monitor.save_quality_report(
            category_code, view_name, report
        )
        
        return report
    
    async def get_feature_lineage(
        self,
        category_code: str,
        view_name: str,
        feature_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取特征血缘信息
        
        实现需求6.5: 平台应提供特征血缘追踪，记录特征的来源信号和计算逻辑
        
        Args:
            category_code: 资产类别编码
            view_name: 视图名称
            feature_name: 特征名称
            
        Returns:
            Optional[Dict]: 血缘信息
        """
        lineage = await self.lineage_tracker.get_lineage(
            category_code, view_name, feature_name
        )
        return lineage.to_dict() if lineage else None
    
    async def get_downstream_features(
        self,
        signal_code: str,
        category_code: Optional[str] = None
    ) -> List[str]:
        """
        获取依赖某信号的所有特征
        
        实现需求6.5: 特征血缘追踪
        
        Args:
            signal_code: 信号编码
            category_code: 资产类别编码 (可选，用于过滤)
            
        Returns:
            List[str]: 依赖该信号的特征列表
        """
        return await self.lineage_tracker.get_downstream_features(
            signal_code, category_code
        )
    
    async def evolve_feature_schema(
        self,
        category_code: str,
        view_name: str,
        new_features: List[Dict[str, Any]]
    ) -> bool:
        """
        特征Schema演进 - 添加新特征列
        
        实现需求6.4: 当特征定义变更时，平台应支持特征表的Schema演进
        
        Args:
            category_code: 资产类别编码
            view_name: 视图名称
            new_features: 新增特征配置列表
            
        Returns:
            bool: 演进是否成功
        """
        try:
            # 1. 使用FeatureStore进行Schema演进
            success = await self.feature_store.evolve_schema(
                category_code, view_name, new_features
            )
            
            if not success:
                return False
            
            # 2. 记录新特征的血缘信息
            await self.lineage_tracker.record_lineages_batch(
                category_code, view_name, new_features
            )
            
            logger.info(f"✅ Schema演进成功: {category_code}/{view_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Schema演进失败: {e}")
            return False


# =====================================================
# 全局实例
# =====================================================

# DSL解析器
feature_dsl_parser = FeatureDSLParser()
batch_feature_parser = BatchFeatureParser()

# 流计算生成器
stream_generator = TDengineStreamGenerator()

# 质量监控器
feature_quality_monitor = FeatureQualityMonitor()

# 特征管理器
feature_manager = FeatureManager()


# =====================================================
# 便捷函数
# =====================================================

def parse_feature_config(config: Dict[str, Any]) -> ParsedFeatureConfig:
    """解析特征配置的便捷函数"""
    return FeatureDSLParser.parse_feature_config(config)


def validate_feature_config(config: Dict[str, Any]) -> ValidationResult:
    """验证特征配置的便捷函数"""
    return FeatureDSLParser.validate_config(config)


def get_supported_functions() -> List[str]:
    """获取支持的聚合函数列表"""
    return FeatureDSLParser.get_supported_functions()
