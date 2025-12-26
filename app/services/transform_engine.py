# -*- coding: utf-8 -*-
"""
数据转换引擎

功能：
1. 应用字段转换规则
2. 支持多种转换类型（表达式、映射、范围限制等）
3. 单位转换
4. 数据清洗

作者：AI Assistant
日期：2025-11-03
"""

from typing import Dict, Any, List, Optional, Union
from decimal import Decimal
from datetime import datetime
from app.core.exceptions import APIException
import logging

logger = logging.getLogger(__name__)
import re
import math


class TransformEngine:
    """
    数据转换引擎
    
    核心功能：
    - 应用转换规则（transform_rule）
    - 支持表达式转换（如：value * 0.001）
    - 支持映射转换（如：1 -> "正常", 0 -> "异常"）
    - 支持范围限制（如：限制在 [0, 100] 之间）
    - 支持单位转换（如：mA -> A）
    - 支持组合转换（多个规则按顺序执行）
    """
    
    # 支持的转换类型
    TRANSFORM_TYPES = {
        'expression',   # 表达式转换
        'mapping',      # 映射转换
        'range_limit',  # 范围限制
        'unit',         # 单位转换
        'round',        # 四舍五入
        'composite'     # 组合转换
    }
    
    def __init__(self):
        """初始化转换引擎"""
        pass
    
    def apply_transform(
        self,
        value: Any,
        transform_rule: Optional[Dict[str, Any]],
        field_name: str = "unknown"
    ) -> Any:
        """
        应用转换规则
        
        Args:
            value: 原始值
            transform_rule: 转换规则（JSON 格式）
            field_name: 字段名称（用于日志）
        
        Returns:
            转换后的值
        
        Raises:
            APIException: 转换失败
        """
        # 如果没有转换规则，直接返回原值
        if not transform_rule or value is None:
            return value
        
        try:
            # 获取转换类型
            transform_type = transform_rule.get('type')
            
            if not transform_type:
                logger.warning(f"[数据转换] 转换规则缺少 'type' 字段: {field_name}")
                return value
            
            if transform_type not in self.TRANSFORM_TYPES:
                logger.warning(f"[数据转换] 不支持的转换类型: {transform_type}")
                return value
            
            # 根据转换类型调用相应的处理方法
            if transform_type == 'expression':
                return self._apply_expression(value, transform_rule, field_name)
            elif transform_type == 'mapping':
                return self._apply_mapping(value, transform_rule, field_name)
            elif transform_type == 'range_limit':
                return self._apply_range_limit(value, transform_rule, field_name)
            elif transform_type == 'unit':
                return self._apply_unit_conversion(value, transform_rule, field_name)
            elif transform_type == 'round':
                return self._apply_round(value, transform_rule, field_name)
            elif transform_type == 'composite':
                return self._apply_composite(value, transform_rule, field_name)
            else:
                return value
                
        except Exception as e:
            logger.error(f"[数据转换] 转换失败: field={field_name}, value={value}, error={e}")
            # 转换失败时返回原值，不中断处理
            return value
    
    def _apply_expression(
        self,
        value: Any,
        rule: Dict[str, Any],
        field_name: str
    ) -> Any:
        """
        应用表达式转换
        
        表达式格式示例:
        {
            "type": "expression",
            "expression": "value * 0.001",  # 将 mA 转换为 A
            "description": "毫安转安培"
        }
        
        Args:
            value: 原始值
            rule: 转换规则
            field_name: 字段名
        
        Returns:
            转换后的值
        """
        expression = rule.get('expression')
        if not expression:
            return value
        
        # 验证表达式安全性（仅允许基本数学运算）
        if not self._is_safe_expression(expression):
            logger.warning(f"[数据转换] 表达式不安全，拒绝执行: {expression}")
            return value
        
        try:
            # 转换为数值类型
            if isinstance(value, str):
                value = float(value)
            
            # 执行表达式（使用安全的 eval）
            result = eval(
                expression,
                {"__builtins__": {}},  # 禁用内置函数
                {
                    "value": value,
                    "abs": abs,
                    "round": round,
                    "min": min,
                    "max": max,
                    "math": math
                }
            )
            
            logger.debug(f"[数据转换] 表达式转换: {field_name} = {value} -> {result}")
            return result
            
        except Exception as e:
            logger.error(f"[数据转换] 表达式执行失败: {expression}, error={e}")
            return value
    
    def _apply_mapping(
        self,
        value: Any,
        rule: Dict[str, Any],
        field_name: str
    ) -> Any:
        """
        应用映射转换
        
        映射格式示例:
        {
            "type": "mapping",
            "mappings": {
                "0": "异常",
                "1": "正常",
                "2": "警告"
            },
            "default": "未知"
        }
        
        Args:
            value: 原始值
            rule: 转换规则
            field_name: 字段名
        
        Returns:
            映射后的值
        """
        mappings = rule.get('mappings', {})
        default_value = rule.get('default', value)
        
        # 将值转换为字符串作为 key
        key = str(value)
        
        result = mappings.get(key, default_value)
        
        logger.debug(f"[数据转换] 映射转换: {field_name} = {value} -> {result}")
        return result
    
    def _apply_range_limit(
        self,
        value: Any,
        rule: Dict[str, Any],
        field_name: str
    ) -> Any:
        """
        应用范围限制
        
        范围限制格式示例:
        {
            "type": "range_limit",
            "min": 0,
            "max": 100,
            "clip": true  # true: 截断, false: 超出范围返回 null
        }
        
        Args:
            value: 原始值
            rule: 转换规则
            field_name: 字段名
        
        Returns:
            限制后的值
        """
        min_value = rule.get('min')
        max_value = rule.get('max')
        clip = rule.get('clip', True)
        
        try:
            # 转换为数值
            if isinstance(value, str):
                value = float(value)
            
            # 检查并限制范围
            if min_value is not None and value < min_value:
                if clip:
                    result = min_value
                    logger.debug(f"[数据转换] 范围限制（下限）: {field_name} = {value} -> {result}")
                    return result
                else:
                    logger.warning(f"[数据转换] 值低于下限，返回 null: {field_name} = {value} < {min_value}")
                    return None
            
            if max_value is not None and value > max_value:
                if clip:
                    result = max_value
                    logger.debug(f"[数据转换] 范围限制（上限）: {field_name} = {value} -> {result}")
                    return result
                else:
                    logger.warning(f"[数据转换] 值超过上限，返回 null: {field_name} = {value} > {max_value}")
                    return None
            
            return value
            
        except Exception as e:
            logger.error(f"[数据转换] 范围限制失败: {field_name}, error={e}")
            return value
    
    def _apply_unit_conversion(
        self,
        value: Any,
        rule: Dict[str, Any],
        field_name: str
    ) -> Any:
        """
        应用单位转换
        
        单位转换格式示例:
        {
            "type": "unit",
            "from_unit": "mA",
            "to_unit": "A",
            "factor": 0.001
        }
        
        Args:
            value: 原始值
            rule: 转换规则
            field_name: 字段名
        
        Returns:
            转换后的值
        """
        from_unit = rule.get('from_unit')
        to_unit = rule.get('to_unit')
        factor = rule.get('factor', 1.0)
        
        try:
            # 转换为数值
            if isinstance(value, str):
                value = float(value)
            
            result = value * factor
            
            logger.debug(f"[数据转换] 单位转换: {field_name} = {value} {from_unit} -> {result} {to_unit}")
            return result
            
        except Exception as e:
            logger.error(f"[数据转换] 单位转换失败: {field_name}, error={e}")
            return value
    
    def _apply_round(
        self,
        value: Any,
        rule: Dict[str, Any],
        field_name: str
    ) -> Any:
        """
        应用四舍五入
        
        四舍五入格式示例:
        {
            "type": "round",
            "decimals": 2  # 保留小数位数
        }
        
        Args:
            value: 原始值
            rule: 转换规则
            field_name: 字段名
        
        Returns:
            四舍五入后的值
        """
        # 默认为 3 位小数 (用户需求: 监测卡片上关于数值类型的监测参数，默认保留3位小数)
        decimals = rule.get('decimals', 3)
        
        try:
            # 转换为数值
            if isinstance(value, str):
                value = float(value)
            
            # 如果是浮点数，进行四舍五入
            if isinstance(value, float):
                result = round(value, decimals)
                logger.debug(f"[数据转换] 四舍五入: {field_name} = {value} -> {result}")
                return result
            
            return value
            
        except Exception as e:
            logger.error(f"[数据转换] 四舍五入失败: {field_name}, error={e}")
            return value
    
    def _apply_composite(
        self,
        value: Any,
        rule: Dict[str, Any],
        field_name: str
    ) -> Any:
        """
        应用组合转换（按顺序执行多个转换规则）
        
        组合转换格式示例:
        {
            "type": "composite",
            "rules": [
                {"type": "expression", "expression": "value * 0.001"},
                {"type": "range_limit", "min": 0, "max": 100},
                {"type": "round", "decimals": 2}
            ]
        }
        
        Args:
            value: 原始值
            rule: 转换规则
            field_name: 字段名
        
        Returns:
            转换后的值
        """
        rules = rule.get('rules', [])
        
        if not rules:
            return value
        
        result = value
        for sub_rule in rules:
            result = self.apply_transform(result, sub_rule, field_name)
        
        logger.debug(f"[数据转换] 组合转换: {field_name} = {value} -> {result} (共 {len(rules)} 步)")
        return result
    
    def _is_safe_expression(self, expression: str) -> bool:
        """
        验证表达式安全性
        
        Args:
            expression: 表达式字符串
        
        Returns:
            是否安全
        """
        # 仅允许：数字、变量名、基本运算符、数学函数
        allowed_pattern = r'^[a-zA-Z0-9_\s\+\-\*\/\(\)\.,]+$'
        
        if not re.match(allowed_pattern, expression):
            return False
        
        # 禁止的关键词
        forbidden_keywords = [
            'import', 'exec', 'eval', 'compile', 'open', 'file',
            '__', 'globals', 'locals', 'vars', 'dir'
        ]
        
        expression_lower = expression.lower()
        for keyword in forbidden_keywords:
            if keyword in expression_lower:
                return False
        
        return True
    
    def batch_transform(
        self,
        data: Dict[str, Any],
        field_mappings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量应用转换规则
        
        Args:
            data: 原始数据字典
            field_mappings: 字段映射列表（包含转换规则）
        
        Returns:
            转换后的数据字典
        """
        transformed_data = {}
        
        for mapping in field_mappings:
            field_code = mapping.get('field_code')
            tdengine_column = mapping.get('tdengine_column')
            transform_rule = mapping.get('transform_rule')
            
            # 从原始数据中获取值
            value = data.get(tdengine_column)
            
            if value is not None:
                # 应用转换规则
                transformed_value = self.apply_transform(
                    value=value,
                    transform_rule=transform_rule,
                    field_name=field_code
                )
                
                # 用户需求: 监测卡片上关于数值类型的监测参数，默认保留3位小数
                # 即使没有配置转换规则，也对浮点数应用默认的 3 位小数处理
                if isinstance(transformed_value, float):
                    transformed_value = round(transformed_value, 3)
                
                transformed_data[field_code] = transformed_value
            else:
                transformed_data[field_code] = None
        
        return transformed_data
    
    def get_transform_summary(
        self,
        transform_rule: Optional[Dict[str, Any]]
    ) -> str:
        """
        获取转换规则的可读描述
        
        Args:
            transform_rule: 转换规则
        
        Returns:
            转换规则描述
        """
        if not transform_rule:
            return "无转换"
        
        transform_type = transform_rule.get('type', 'unknown')
        
        if transform_type == 'expression':
            return f"表达式: {transform_rule.get('expression', '?')}"
        elif transform_type == 'mapping':
            mappings_count = len(transform_rule.get('mappings', {}))
            return f"映射: {mappings_count} 个映射值"
        elif transform_type == 'range_limit':
            min_val = transform_rule.get('min', '?')
            max_val = transform_rule.get('max', '?')
            return f"范围限制: [{min_val}, {max_val}]"
        elif transform_type == 'unit':
            from_unit = transform_rule.get('from_unit', '?')
            to_unit = transform_rule.get('to_unit', '?')
            return f"单位转换: {from_unit} -> {to_unit}"
        elif transform_type == 'round':
            decimals = transform_rule.get('decimals', 0)
            return f"四舍五入: {decimals} 位小数"
        elif transform_type == 'composite':
            rules_count = len(transform_rule.get('rules', []))
            return f"组合转换: {rules_count} 步"
        else:
            return f"未知转换类型: {transform_type}"


# 创建全局实例
transform_engine = TransformEngine()

