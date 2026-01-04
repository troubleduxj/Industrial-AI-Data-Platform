"""
Rule DSL Parser - 规则DSL解析器

实现规则DSL的解析、验证和序列化功能。

规则DSL示例:
{
    "rule_id": "rule_001",
    "name": "电机过热预警",
    "description": "当预测温度超过阈值时触发告警",
    "enabled": true,
    "priority": 1,
    "conditions": {
        "type": "AND",
        "rules": [
            {"field": "predicted_value", "operator": "gt", "value": 80},
            {"field": "confidence", "operator": "gte", "value": 0.8}
        ]
    },
    "actions": [
        {"type": "alert", "level": "warning", "message": "预测温度超过80°C"}
    ],
    "cooldown_seconds": 300
}
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple, Union
from enum import Enum
import json
import copy


class ConditionOperator(str, Enum):
    """条件运算符枚举"""
    EQ = "eq"           # 等于
    NE = "ne"           # 不等于
    GT = "gt"           # 大于
    GTE = "gte"         # 大于等于
    LT = "lt"           # 小于
    LTE = "lte"         # 小于等于
    IN = "in"           # 在列表中
    NOT_IN = "not_in"   # 不在列表中
    BETWEEN = "between" # 在范围内
    CONTAINS = "contains"  # 包含（字符串）
    STARTS_WITH = "starts_with"  # 以...开头
    ENDS_WITH = "ends_with"      # 以...结尾


class LogicalOperator(str, Enum):
    """逻辑运算符枚举"""
    AND = "AND"
    OR = "OR"


@dataclass
class Condition:
    """单个条件"""
    field: str
    operator: ConditionOperator
    value: Any
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "field": self.field,
            "operator": self.operator.value if isinstance(self.operator, ConditionOperator) else self.operator,
            "value": self.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Condition":
        """从字典创建"""
        operator = data["operator"]
        if isinstance(operator, str):
            operator = ConditionOperator(operator)
        return cls(
            field=data["field"],
            operator=operator,
            value=data["value"]
        )


@dataclass
class ConditionGroup:
    """条件组（支持AND/OR组合）"""
    type: LogicalOperator
    rules: List[Union[Condition, "ConditionGroup"]]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type.value if isinstance(self.type, LogicalOperator) else self.type,
            "rules": [
                r.to_dict() for r in self.rules
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConditionGroup":
        """从字典创建"""
        logical_type = data["type"]
        if isinstance(logical_type, str):
            logical_type = LogicalOperator(logical_type)
        
        rules = []
        for rule_data in data.get("rules", []):
            # 判断是条件还是条件组
            if "type" in rule_data and "rules" in rule_data:
                # 嵌套的条件组
                rules.append(cls.from_dict(rule_data))
            else:
                # 单个条件
                rules.append(Condition.from_dict(rule_data))
        
        return cls(type=logical_type, rules=rules)


@dataclass
class Action:
    """动作定义"""
    type: str  # alert, notification, webhook, workorder
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {"type": self.type}
        result.update(self.config)
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Action":
        """从字典创建"""
        action_type = data.get("type", "")
        config = {k: v for k, v in data.items() if k != "type"}
        return cls(type=action_type, config=config)


@dataclass
class Rule:
    """完整规则定义"""
    rule_id: str
    name: str
    enabled: bool
    priority: int
    conditions: ConditionGroup
    actions: List[Action]
    cooldown_seconds: int = 0
    description: Optional[str] = None
    category_id: Optional[int] = None
    model_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "rule_id": self.rule_id,
            "name": self.name,
            "enabled": self.enabled,
            "priority": self.priority,
            "conditions": self.conditions.to_dict(),
            "actions": [a.to_dict() for a in self.actions],
            "cooldown_seconds": self.cooldown_seconds,
        }
        if self.description is not None:
            result["description"] = self.description
        if self.category_id is not None:
            result["category_id"] = self.category_id
        if self.model_id is not None:
            result["model_id"] = self.model_id
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Rule":
        """从字典创建"""
        return cls(
            rule_id=data["rule_id"],
            name=data["name"],
            enabled=data.get("enabled", True),
            priority=data.get("priority", 0),
            conditions=ConditionGroup.from_dict(data["conditions"]),
            actions=[Action.from_dict(a) for a in data.get("actions", [])],
            cooldown_seconds=data.get("cooldown_seconds", 0),
            description=data.get("description"),
            category_id=data.get("category_id"),
            model_id=data.get("model_id"),
        )


class RuleParseError(Exception):
    """规则解析错误"""
    pass


class RuleValidationError(Exception):
    """规则验证错误"""
    pass


class RuleParser:
    """规则DSL解析器"""
    
    # 必需字段
    REQUIRED_FIELDS = ["rule_id", "name", "conditions", "actions"]
    
    # 有效的动作类型
    VALID_ACTION_TYPES = ["alert", "notification", "webhook", "workorder"]
    
    # 有效的告警级别
    VALID_ALERT_LEVELS = ["info", "warning", "error", "critical"]
    
    @staticmethod
    def parse(rule_dict: Dict[str, Any]) -> Rule:
        """
        解析规则DSL为Rule对象
        
        Args:
            rule_dict: 规则DSL字典
            
        Returns:
            Rule: 解析后的规则对象
            
        Raises:
            RuleParseError: 解析失败时抛出
        """
        try:
            # 先验证格式
            is_valid, errors = RuleParser.validate(rule_dict)
            if not is_valid:
                raise RuleParseError(f"规则格式验证失败: {'; '.join(errors)}")
            
            return Rule.from_dict(rule_dict)
        except RuleParseError:
            raise
        except Exception as e:
            raise RuleParseError(f"规则解析失败: {str(e)}")
    
    @staticmethod
    def validate(rule_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证规则DSL格式
        
        Args:
            rule_dict: 规则DSL字典
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误列表)
        """
        errors = []
        
        # 检查必需字段
        for field in RuleParser.REQUIRED_FIELDS:
            if field not in rule_dict:
                errors.append(f"缺少必需字段: {field}")
        
        if errors:
            return False, errors
        
        # 验证rule_id
        rule_id = rule_dict.get("rule_id", "")
        if not isinstance(rule_id, str) or not rule_id.strip():
            errors.append("rule_id必须是非空字符串")
        
        # 验证name
        name = rule_dict.get("name", "")
        if not isinstance(name, str) or not name.strip():
            errors.append("name必须是非空字符串")
        
        # 验证enabled
        if "enabled" in rule_dict and not isinstance(rule_dict["enabled"], bool):
            errors.append("enabled必须是布尔值")
        
        # 验证priority
        if "priority" in rule_dict:
            priority = rule_dict["priority"]
            if not isinstance(priority, int):
                errors.append("priority必须是整数")
        
        # 验证cooldown_seconds
        if "cooldown_seconds" in rule_dict:
            cooldown = rule_dict["cooldown_seconds"]
            if not isinstance(cooldown, int) or cooldown < 0:
                errors.append("cooldown_seconds必须是非负整数")
        
        # 验证conditions
        conditions_errors = RuleParser._validate_conditions(rule_dict.get("conditions", {}))
        errors.extend(conditions_errors)
        
        # 验证actions
        actions_errors = RuleParser._validate_actions(rule_dict.get("actions", []))
        errors.extend(actions_errors)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_conditions(conditions: Dict[str, Any], path: str = "conditions") -> List[str]:
        """验证条件配置"""
        errors = []
        
        if not isinstance(conditions, dict):
            errors.append(f"{path}必须是字典")
            return errors
        
        # 检查type字段
        if "type" not in conditions:
            errors.append(f"{path}缺少type字段")
        else:
            cond_type = conditions["type"]
            if cond_type not in [op.value for op in LogicalOperator]:
                errors.append(f"{path}.type必须是AND或OR")
        
        # 检查rules字段
        if "rules" not in conditions:
            errors.append(f"{path}缺少rules字段")
        else:
            rules = conditions["rules"]
            if not isinstance(rules, list):
                errors.append(f"{path}.rules必须是列表")
            elif len(rules) == 0:
                errors.append(f"{path}.rules不能为空")
            else:
                for i, rule in enumerate(rules):
                    rule_path = f"{path}.rules[{i}]"
                    if "type" in rule and "rules" in rule:
                        # 嵌套条件组
                        errors.extend(RuleParser._validate_conditions(rule, rule_path))
                    else:
                        # 单个条件
                        errors.extend(RuleParser._validate_single_condition(rule, rule_path))
        
        return errors
    
    @staticmethod
    def _validate_single_condition(condition: Dict[str, Any], path: str) -> List[str]:
        """验证单个条件"""
        errors = []
        
        if not isinstance(condition, dict):
            errors.append(f"{path}必须是字典")
            return errors
        
        # 检查field
        if "field" not in condition:
            errors.append(f"{path}缺少field字段")
        elif not isinstance(condition["field"], str) or not condition["field"].strip():
            errors.append(f"{path}.field必须是非空字符串")
        
        # 检查operator
        if "operator" not in condition:
            errors.append(f"{path}缺少operator字段")
        else:
            operator = condition["operator"]
            valid_operators = [op.value for op in ConditionOperator]
            if operator not in valid_operators:
                errors.append(f"{path}.operator无效，有效值: {valid_operators}")
        
        # 检查value
        if "value" not in condition:
            errors.append(f"{path}缺少value字段")
        else:
            # 根据operator验证value类型
            operator = condition.get("operator", "")
            value = condition["value"]
            
            if operator in ["in", "not_in"]:
                if not isinstance(value, list):
                    errors.append(f"{path}.value对于{operator}运算符必须是列表")
            elif operator == "between":
                if not isinstance(value, list) or len(value) != 2:
                    errors.append(f"{path}.value对于between运算符必须是包含两个元素的列表")
        
        return errors
    
    @staticmethod
    def _validate_actions(actions: List[Dict[str, Any]]) -> List[str]:
        """验证动作配置"""
        errors = []
        
        if not isinstance(actions, list):
            errors.append("actions必须是列表")
            return errors
        
        if len(actions) == 0:
            errors.append("actions不能为空")
            return errors
        
        for i, action in enumerate(actions):
            path = f"actions[{i}]"
            
            if not isinstance(action, dict):
                errors.append(f"{path}必须是字典")
                continue
            
            # 检查type
            if "type" not in action:
                errors.append(f"{path}缺少type字段")
            else:
                action_type = action["type"]
                if action_type not in RuleParser.VALID_ACTION_TYPES:
                    errors.append(f"{path}.type无效，有效值: {RuleParser.VALID_ACTION_TYPES}")
                
                # 根据类型验证必需配置
                if action_type == "alert":
                    if "level" in action:
                        if action["level"] not in RuleParser.VALID_ALERT_LEVELS:
                            errors.append(f"{path}.level无效，有效值: {RuleParser.VALID_ALERT_LEVELS}")
                
                elif action_type == "notification":
                    if "channels" not in action:
                        errors.append(f"{path}缺少channels字段")
                    elif not isinstance(action["channels"], list):
                        errors.append(f"{path}.channels必须是列表")
                
                elif action_type == "webhook":
                    if "url" not in action:
                        errors.append(f"{path}缺少url字段")
        
        return errors
    
    @staticmethod
    def serialize(rule: Rule) -> Dict[str, Any]:
        """
        序列化Rule对象为DSL字典
        
        Args:
            rule: 规则对象
            
        Returns:
            Dict[str, Any]: 规则DSL字典
        """
        return rule.to_dict()
    
    @staticmethod
    def to_json(rule: Rule, indent: int = 2) -> str:
        """
        序列化Rule对象为JSON字符串
        
        Args:
            rule: 规则对象
            indent: 缩进空格数
            
        Returns:
            str: JSON字符串
        """
        return json.dumps(rule.to_dict(), ensure_ascii=False, indent=indent)
    
    @staticmethod
    def from_json(json_str: str) -> Rule:
        """
        从JSON字符串解析规则
        
        Args:
            json_str: JSON字符串
            
        Returns:
            Rule: 规则对象
        """
        try:
            rule_dict = json.loads(json_str)
            return RuleParser.parse(rule_dict)
        except json.JSONDecodeError as e:
            raise RuleParseError(f"JSON解析失败: {str(e)}")
