#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据验证器

实现数据采集层的数据验证功能。
支持类型验证、范围验证和自定义验证规则。

需求: 5.2 - 数据验证和格式转换
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Union, Callable

from platform_core.ingestion.adapters.base_adapter import DataPoint

logger = logging.getLogger(__name__)


class DataType(str, Enum):
    """数据类型枚举"""
    FLOAT = "float"
    DOUBLE = "double"
    INT = "int"
    BIGINT = "bigint"
    BOOL = "bool"
    STRING = "string"
    TIMESTAMP = "timestamp"


class ValidationResult(str, Enum):
    """验证结果枚举"""
    VALID = "valid"
    INVALID_TYPE = "invalid_type"
    OUT_OF_RANGE = "out_of_range"
    VALIDATION_RULE_FAILED = "validation_rule_failed"
    UNKNOWN_SIGNAL = "unknown_signal"


@dataclass
class SignalValidationResult:
    """信号验证结果"""
    signal_code: str
    is_valid: bool
    result: ValidationResult
    original_value: Any
    converted_value: Any = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_code": self.signal_code,
            "is_valid": self.is_valid,
            "result": self.result.value,
            "original_value": self.original_value,
            "converted_value": self.converted_value,
            "error_message": self.error_message,
        }


@dataclass
class DataPointValidationResult:
    """数据点验证结果"""
    is_valid: bool
    data_point: DataPoint
    signal_results: List[SignalValidationResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def valid_signals(self) -> Dict[str, Any]:
        """获取有效的信号数据"""
        return {
            r.signal_code: r.converted_value if r.converted_value is not None else r.original_value
            for r in self.signal_results
            if r.is_valid
        }
    
    @property
    def invalid_signals(self) -> List[str]:
        """获取无效的信号列表"""
        return [r.signal_code for r in self.signal_results if not r.is_valid]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "signal_results": [r.to_dict() for r in self.signal_results],
            "errors": self.errors,
            "warnings": self.warnings,
            "valid_signal_count": len(self.valid_signals),
            "invalid_signal_count": len(self.invalid_signals),
        }


@dataclass
class SignalDefinitionConfig:
    """信号定义配置"""
    code: str
    name: str
    data_type: DataType
    unit: Optional[str] = None
    value_range: Optional[Dict[str, Any]] = None  # {"min": 0, "max": 100}
    validation_rules: Optional[Dict[str, Any]] = None
    is_required: bool = False
    default_value: Any = None
    allow_null: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SignalDefinitionConfig":
        """从字典创建"""
        data_type = data.get("data_type", "float")
        if isinstance(data_type, str):
            data_type = DataType(data_type.lower())
        
        return cls(
            code=data.get("code", ""),
            name=data.get("name", ""),
            data_type=data_type,
            unit=data.get("unit"),
            value_range=data.get("value_range"),
            validation_rules=data.get("validation_rules"),
            is_required=data.get("is_required", False),
            default_value=data.get("default_value"),
            allow_null=data.get("allow_null", True),
        )


class DataValidator:
    """
    数据验证器
    
    根据信号定义验证数据点的类型和值范围。
    
    使用示例:
    ```python
    validator = DataValidator()
    
    # 加载信号定义
    await validator.load_signal_definitions("motor")
    
    # 或手动设置
    validator.set_signal_definitions("motor", {
        "temperature": SignalDefinitionConfig(
            code="temperature",
            name="温度",
            data_type=DataType.FLOAT,
            value_range={"min": -40, "max": 150}
        )
    })
    
    # 验证数据点
    result = validator.validate(data_point, "motor")
    if result.is_valid:
        # 使用验证后的数据
        valid_signals = result.valid_signals
    ```
    """
    
    def __init__(self, strict_mode: bool = False):
        """
        初始化验证器
        
        Args:
            strict_mode: 严格模式，未知信号将被视为无效
        """
        self._signal_definitions: Dict[str, Dict[str, SignalDefinitionConfig]] = {}
        self._strict_mode = strict_mode
        self._custom_validators: Dict[str, Callable] = {}
    
    # =====================================================
    # 信号定义管理
    # =====================================================
    
    async def load_signal_definitions(self, category_code: str) -> bool:
        """
        从数据库加载信号定义
        
        Args:
            category_code: 资产类别编码
        
        Returns:
            bool: 加载是否成功
        """
        try:
            from app.models.platform_upgrade import SignalDefinition, AssetCategory
            
            category = await AssetCategory.get_or_none(code=category_code)
            if not category:
                logger.warning(f"资产类别不存在: {category_code}")
                return False
            
            signals = await SignalDefinition.filter(
                category_id=category.id,
                is_active=True
            ).all()
            
            definitions = {}
            for signal in signals:
                definitions[signal.code] = SignalDefinitionConfig(
                    code=signal.code,
                    name=signal.name,
                    data_type=DataType(signal.data_type.lower()),
                    unit=signal.unit,
                    value_range=signal.value_range,
                    validation_rules=signal.validation_rules,
                    is_required=False,
                    allow_null=True,
                )
            
            self._signal_definitions[category_code] = definitions
            logger.info(f"已加载 {len(definitions)} 个信号定义: {category_code}")
            return True
            
        except ImportError:
            logger.warning("无法导入数据库模型，请手动设置信号定义")
            return False
        except Exception as e:
            logger.error(f"加载信号定义失败: {e}")
            return False
    
    def set_signal_definitions(
        self,
        category_code: str,
        definitions: Dict[str, SignalDefinitionConfig]
    ):
        """
        手动设置信号定义
        
        Args:
            category_code: 资产类别编码
            definitions: 信号定义字典 {信号编码: 配置}
        """
        self._signal_definitions[category_code] = definitions
    
    def get_signal_definitions(self, category_code: str) -> Dict[str, SignalDefinitionConfig]:
        """获取信号定义"""
        return self._signal_definitions.get(category_code, {})
    
    def clear_signal_definitions(self, category_code: Optional[str] = None):
        """清除信号定义"""
        if category_code:
            self._signal_definitions.pop(category_code, None)
        else:
            self._signal_definitions.clear()
    
    # =====================================================
    # 自定义验证器
    # =====================================================
    
    def register_validator(self, name: str, validator: Callable[[Any, Dict], Tuple[bool, str]]):
        """
        注册自定义验证器
        
        Args:
            name: 验证器名称
            validator: 验证函数，接收(value, params)，返回(is_valid, error_message)
        """
        self._custom_validators[name] = validator
    
    # =====================================================
    # 验证方法
    # =====================================================
    
    def validate(
        self,
        data_point: DataPoint,
        category_code: str,
        skip_unknown: bool = True
    ) -> DataPointValidationResult:
        """
        验证数据点
        
        Args:
            data_point: 数据点
            category_code: 资产类别编码
            skip_unknown: 是否跳过未知信号
        
        Returns:
            DataPointValidationResult: 验证结果
        """
        result = DataPointValidationResult(
            is_valid=True,
            data_point=data_point,
        )
        
        definitions = self._signal_definitions.get(category_code, {})
        
        # 验证每个信号
        for signal_code, value in data_point.signals.items():
            signal_result = self._validate_signal(
                signal_code,
                value,
                definitions.get(signal_code),
                skip_unknown
            )
            result.signal_results.append(signal_result)
            
            if not signal_result.is_valid:
                result.is_valid = False
                result.errors.append(signal_result.error_message or f"信号 {signal_code} 验证失败")
        
        # 检查必需信号
        for code, definition in definitions.items():
            if definition.is_required and code not in data_point.signals:
                result.is_valid = False
                result.errors.append(f"缺少必需信号: {code}")
        
        return result
    
    def _validate_signal(
        self,
        signal_code: str,
        value: Any,
        definition: Optional[SignalDefinitionConfig],
        skip_unknown: bool
    ) -> SignalValidationResult:
        """
        验证单个信号
        
        Args:
            signal_code: 信号编码
            value: 信号值
            definition: 信号定义
            skip_unknown: 是否跳过未知信号
        
        Returns:
            SignalValidationResult: 验证结果
        """
        # 未知信号处理
        if definition is None:
            if self._strict_mode and not skip_unknown:
                return SignalValidationResult(
                    signal_code=signal_code,
                    is_valid=False,
                    result=ValidationResult.UNKNOWN_SIGNAL,
                    original_value=value,
                    error_message=f"未知信号: {signal_code}"
                )
            else:
                # 跳过未知信号，视为有效
                return SignalValidationResult(
                    signal_code=signal_code,
                    is_valid=True,
                    result=ValidationResult.VALID,
                    original_value=value,
                    converted_value=value,
                )
        
        # 空值处理
        if value is None:
            if definition.allow_null:
                return SignalValidationResult(
                    signal_code=signal_code,
                    is_valid=True,
                    result=ValidationResult.VALID,
                    original_value=value,
                    converted_value=definition.default_value,
                )
            else:
                return SignalValidationResult(
                    signal_code=signal_code,
                    is_valid=False,
                    result=ValidationResult.INVALID_TYPE,
                    original_value=value,
                    error_message=f"信号 {signal_code} 不允许为空"
                )
        
        # 类型验证和转换
        is_valid_type, converted_value, type_error = self._validate_type(
            value, definition.data_type
        )
        
        if not is_valid_type:
            return SignalValidationResult(
                signal_code=signal_code,
                is_valid=False,
                result=ValidationResult.INVALID_TYPE,
                original_value=value,
                error_message=f"信号 {signal_code} 类型错误: {type_error}"
            )
        
        # 范围验证
        if definition.value_range:
            is_valid_range, range_error = self._validate_range(
                converted_value, definition.value_range
            )
            
            if not is_valid_range:
                return SignalValidationResult(
                    signal_code=signal_code,
                    is_valid=False,
                    result=ValidationResult.OUT_OF_RANGE,
                    original_value=value,
                    converted_value=converted_value,
                    error_message=f"信号 {signal_code} 超出范围: {range_error}"
                )
        
        # 自定义验证规则
        if definition.validation_rules:
            is_valid_rules, rules_error = self._validate_rules(
                converted_value, definition.validation_rules
            )
            
            if not is_valid_rules:
                return SignalValidationResult(
                    signal_code=signal_code,
                    is_valid=False,
                    result=ValidationResult.VALIDATION_RULE_FAILED,
                    original_value=value,
                    converted_value=converted_value,
                    error_message=f"信号 {signal_code} 验证规则失败: {rules_error}"
                )
        
        return SignalValidationResult(
            signal_code=signal_code,
            is_valid=True,
            result=ValidationResult.VALID,
            original_value=value,
            converted_value=converted_value,
        )
    
    def _validate_type(
        self,
        value: Any,
        expected_type: DataType
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        验证并转换数据类型
        
        Args:
            value: 原始值
            expected_type: 期望类型
        
        Returns:
            Tuple[bool, Any, Optional[str]]: (是否有效, 转换后的值, 错误信息)
        """
        try:
            if expected_type in (DataType.FLOAT, DataType.DOUBLE):
                if isinstance(value, (int, float)):
                    return True, float(value), None
                elif isinstance(value, str):
                    return True, float(value), None
                else:
                    return False, None, f"无法转换为浮点数: {type(value).__name__}"
            
            elif expected_type in (DataType.INT, DataType.BIGINT):
                if isinstance(value, int):
                    return True, value, None
                elif isinstance(value, float):
                    return True, int(value), None
                elif isinstance(value, str):
                    return True, int(float(value)), None
                else:
                    return False, None, f"无法转换为整数: {type(value).__name__}"
            
            elif expected_type == DataType.BOOL:
                if isinstance(value, bool):
                    return True, value, None
                elif isinstance(value, (int, float)):
                    return True, bool(value), None
                elif isinstance(value, str):
                    lower_value = value.lower()
                    if lower_value in ("true", "1", "yes", "on"):
                        return True, True, None
                    elif lower_value in ("false", "0", "no", "off"):
                        return True, False, None
                    else:
                        return False, None, f"无法转换为布尔值: {value}"
                else:
                    return False, None, f"无法转换为布尔值: {type(value).__name__}"
            
            elif expected_type == DataType.STRING:
                return True, str(value), None
            
            elif expected_type == DataType.TIMESTAMP:
                if isinstance(value, datetime):
                    return True, value, None
                elif isinstance(value, str):
                    try:
                        return True, datetime.fromisoformat(value.replace("Z", "+00:00")), None
                    except ValueError:
                        return False, None, f"无效的时间戳格式: {value}"
                elif isinstance(value, (int, float)):
                    if value > 1e12:
                        return True, datetime.fromtimestamp(value / 1000), None
                    else:
                        return True, datetime.fromtimestamp(value), None
                else:
                    return False, None, f"无法转换为时间戳: {type(value).__name__}"
            
            else:
                return True, value, None
                
        except (ValueError, TypeError) as e:
            return False, None, str(e)
    
    def _validate_range(
        self,
        value: Any,
        value_range: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        验证值范围
        
        Args:
            value: 值
            value_range: 范围配置 {"min": 0, "max": 100}
        
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误信息)
        """
        if not isinstance(value, (int, float)):
            return True, None  # 非数值类型不验证范围
        
        min_val = value_range.get("min")
        max_val = value_range.get("max")
        
        if min_val is not None and value < min_val:
            return False, f"值 {value} 小于最小值 {min_val}"
        
        if max_val is not None and value > max_val:
            return False, f"值 {value} 大于最大值 {max_val}"
        
        return True, None
    
    def _validate_rules(
        self,
        value: Any,
        rules: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        验证自定义规则
        
        Args:
            value: 值
            rules: 验证规则配置
        
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误信息)
        """
        # 正则表达式验证
        if "pattern" in rules:
            pattern = rules["pattern"]
            if isinstance(value, str) and not re.match(pattern, value):
                return False, f"值不匹配正则表达式: {pattern}"
        
        # 枚举值验证
        if "enum" in rules:
            allowed_values = rules["enum"]
            if value not in allowed_values:
                return False, f"值不在允许的枚举值中: {allowed_values}"
        
        # 自定义验证器
        if "validator" in rules:
            validator_name = rules["validator"]
            validator_params = rules.get("validator_params", {})
            
            if validator_name in self._custom_validators:
                validator = self._custom_validators[validator_name]
                is_valid, error = validator(value, validator_params)
                if not is_valid:
                    return False, error
        
        return True, None
    
    # =====================================================
    # 批量验证
    # =====================================================
    
    def validate_batch(
        self,
        data_points: List[DataPoint],
        category_code: str,
        skip_unknown: bool = True
    ) -> List[DataPointValidationResult]:
        """
        批量验证数据点
        
        Args:
            data_points: 数据点列表
            category_code: 资产类别编码
            skip_unknown: 是否跳过未知信号
        
        Returns:
            List[DataPointValidationResult]: 验证结果列表
        """
        return [
            self.validate(dp, category_code, skip_unknown)
            for dp in data_points
        ]
    
    def filter_valid(
        self,
        data_points: List[DataPoint],
        category_code: str
    ) -> List[DataPoint]:
        """
        过滤出有效的数据点
        
        Args:
            data_points: 数据点列表
            category_code: 资产类别编码
        
        Returns:
            List[DataPoint]: 有效的数据点列表
        """
        valid_points = []
        
        for dp in data_points:
            result = self.validate(dp, category_code)
            if result.is_valid:
                # 使用转换后的信号值创建新的数据点
                valid_dp = DataPoint(
                    asset_code=dp.asset_code,
                    timestamp=dp.timestamp,
                    signals=result.valid_signals,
                    quality=dp.quality,
                    source=dp.source,
                    metadata=dp.metadata,
                )
                valid_points.append(valid_dp)
        
        return valid_points
    
    # =====================================================
    # 统计方法
    # =====================================================
    
    def get_validation_stats(
        self,
        results: List[DataPointValidationResult]
    ) -> Dict[str, Any]:
        """
        获取验证统计信息
        
        Args:
            results: 验证结果列表
        
        Returns:
            Dict: 统计信息
        """
        total = len(results)
        valid_count = sum(1 for r in results if r.is_valid)
        invalid_count = total - valid_count
        
        # 按错误类型统计
        error_types: Dict[str, int] = {}
        for result in results:
            for signal_result in result.signal_results:
                if not signal_result.is_valid:
                    error_type = signal_result.result.value
                    error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total": total,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "valid_rate": valid_count / total if total > 0 else 0,
            "error_types": error_types,
        }
