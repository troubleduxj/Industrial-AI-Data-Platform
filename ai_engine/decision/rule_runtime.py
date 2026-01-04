"""
Rule Runtime Engine - 规则运行时引擎

实现规则的加载、评估和执行功能。

主要功能:
- 从数据库加载规则
- 评估预测结果是否满足规则条件
- 按优先级排序规则
- 管理规则冷却时间
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import logging
import asyncio

from .rule_parser import (
    Rule,
    RuleParser,
    Condition,
    ConditionGroup,
    Action,
    ConditionOperator,
    LogicalOperator,
)

logger = logging.getLogger(__name__)


class RuleEvaluationError(Exception):
    """规则评估错误"""
    pass


class RuleRuntime:
    """
    规则运行时引擎
    
    负责加载规则、评估预测结果、管理冷却时间。
    """
    
    def __init__(self):
        self._rules: Dict[str, Rule] = {}
        self._cooldowns: Dict[str, datetime] = {}
        self._audit_logger = None  # 延迟初始化
    
    def set_audit_logger(self, audit_logger):
        """设置审计日志记录器"""
        self._audit_logger = audit_logger
    
    @property
    def rules(self) -> Dict[str, Rule]:
        """获取所有已加载的规则"""
        return self._rules.copy()
    
    @property
    def rule_count(self) -> int:
        """获取规则数量"""
        return len(self._rules)
    
    def add_rule(self, rule: Rule):
        """
        添加规则到运行时
        
        Args:
            rule: 规则对象
        """
        self._rules[rule.rule_id] = rule
        logger.info(f"添加规则: {rule.rule_id} - {rule.name}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """
        移除规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 是否成功移除
        """
        if rule_id in self._rules:
            del self._rules[rule_id]
            # 同时清除冷却时间
            self._cooldowns.pop(rule_id, None)
            logger.info(f"移除规则: {rule_id}")
            return True
        return False
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """获取规则"""
        return self._rules.get(rule_id)
    
    def enable_rule(self, rule_id: str) -> bool:
        """启用规则"""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = True
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """禁用规则"""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = False
            return True
        return False
    
    async def load_rules_from_db(self) -> int:
        """
        从数据库加载所有启用的规则
        
        Returns:
            int: 加载的规则数量
        """
        try:
            # 延迟导入避免循环依赖
            from app.models.platform_upgrade import DecisionRule
            
            db_rules = await DecisionRule.filter(enabled=True).all()
            
            loaded_count = 0
            for db_rule in db_rules:
                try:
                    rule_dict = {
                        "rule_id": db_rule.rule_id,
                        "name": db_rule.name,
                        "description": db_rule.description,
                        "enabled": db_rule.enabled,
                        "priority": db_rule.priority,
                        "conditions": db_rule.conditions,
                        "actions": db_rule.actions,
                        "cooldown_seconds": db_rule.cooldown_seconds,
                        "category_id": db_rule.category_id,
                        "model_id": db_rule.model_id,
                    }
                    rule = RuleParser.parse(rule_dict)
                    self.add_rule(rule)
                    loaded_count += 1
                except Exception as e:
                    logger.error(f"加载规则失败 {db_rule.rule_id}: {e}")
            
            logger.info(f"从数据库加载了 {loaded_count} 条规则")
            return loaded_count
            
        except Exception as e:
            logger.error(f"从数据库加载规则失败: {e}")
            return 0
    
    def load_rules_from_dicts(self, rule_dicts: List[Dict[str, Any]]) -> int:
        """
        从字典列表加载规则（用于测试或配置文件）
        
        Args:
            rule_dicts: 规则字典列表
            
        Returns:
            int: 成功加载的规则数量
        """
        loaded_count = 0
        for rule_dict in rule_dicts:
            try:
                rule = RuleParser.parse(rule_dict)
                self.add_rule(rule)
                loaded_count += 1
            except Exception as e:
                logger.error(f"加载规则失败: {e}")
        return loaded_count
    
    async def evaluate(self, prediction: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        评估预测结果，返回触发的动作列表
        
        Args:
            prediction: 预测结果字典，包含:
                - model_id: 模型ID
                - asset_id: 资产ID
                - predicted_value: 预测值
                - confidence: 置信度
                - 其他自定义字段
        
        Returns:
            List[Dict]: 触发的动作列表，每个元素包含:
                - rule_id: 规则ID
                - rule_name: 规则名称
                - action: 动作对象
                - prediction: 原始预测数据
                - triggered_at: 触发时间
        """
        triggered_actions = []
        
        # 获取所有启用的规则，按优先级排序（数字越小优先级越高）
        enabled_rules = [r for r in self._rules.values() if r.enabled]
        sorted_rules = sorted(enabled_rules, key=lambda r: r.priority)
        
        for rule in sorted_rules:
            # 检查冷却时间
            if self._is_in_cooldown(rule.rule_id):
                logger.debug(f"规则 {rule.rule_id} 在冷却期内，跳过")
                continue
            
            # 检查模型ID匹配（如果规则指定了模型）
            if rule.model_id is not None:
                if prediction.get("model_id") != rule.model_id:
                    continue
            
            # 检查类别ID匹配（如果规则指定了类别）
            if rule.category_id is not None:
                if prediction.get("category_id") != rule.category_id:
                    continue
            
            # 评估条件
            try:
                if self._evaluate_conditions(rule.conditions, prediction):
                    triggered_at = datetime.now()
                    
                    # 记录审计日志
                    if self._audit_logger:
                        await self._audit_logger.log_trigger(
                            rule=rule,
                            prediction=prediction,
                            triggered_at=triggered_at
                        )
                    
                    # 收集动作
                    for action in rule.actions:
                        triggered_actions.append({
                            "rule_id": rule.rule_id,
                            "rule_name": rule.name,
                            "action": action,
                            "prediction": prediction,
                            "triggered_at": triggered_at,
                        })
                    
                    # 设置冷却时间
                    if rule.cooldown_seconds > 0:
                        self._set_cooldown(rule.rule_id, rule.cooldown_seconds)
                    
                    logger.info(f"规则 {rule.rule_id} 被触发，产生 {len(rule.actions)} 个动作")
                    
            except Exception as e:
                logger.error(f"评估规则 {rule.rule_id} 时出错: {e}")
        
        return triggered_actions
    
    def evaluate_sync(self, prediction: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        同步版本的评估方法（不记录审计日志）
        
        用于测试或不需要审计日志的场景。
        """
        triggered_actions = []
        
        enabled_rules = [r for r in self._rules.values() if r.enabled]
        sorted_rules = sorted(enabled_rules, key=lambda r: r.priority)
        
        for rule in sorted_rules:
            if self._is_in_cooldown(rule.rule_id):
                continue
            
            if rule.model_id is not None:
                if prediction.get("model_id") != rule.model_id:
                    continue
            
            if rule.category_id is not None:
                if prediction.get("category_id") != rule.category_id:
                    continue
            
            try:
                if self._evaluate_conditions(rule.conditions, prediction):
                    triggered_at = datetime.now()
                    
                    for action in rule.actions:
                        triggered_actions.append({
                            "rule_id": rule.rule_id,
                            "rule_name": rule.name,
                            "action": action,
                            "prediction": prediction,
                            "triggered_at": triggered_at,
                        })
                    
                    if rule.cooldown_seconds > 0:
                        self._set_cooldown(rule.rule_id, rule.cooldown_seconds)
                        
            except Exception as e:
                logger.error(f"评估规则 {rule.rule_id} 时出错: {e}")
        
        return triggered_actions
    
    def _evaluate_conditions(
        self, 
        conditions: ConditionGroup, 
        data: Dict[str, Any]
    ) -> bool:
        """
        评估条件组
        
        Args:
            conditions: 条件组
            data: 数据字典
            
        Returns:
            bool: 条件是否满足
        """
        results = []
        
        for rule in conditions.rules:
            if isinstance(rule, ConditionGroup):
                # 递归评估嵌套条件组
                result = self._evaluate_conditions(rule, data)
            else:
                # 评估单个条件
                result = self._evaluate_single_condition(rule, data)
            results.append(result)
        
        # 根据逻辑运算符组合结果
        if conditions.type == LogicalOperator.AND:
            return all(results)
        else:  # OR
            return any(results)
    
    def _evaluate_single_condition(
        self, 
        condition: Condition, 
        data: Dict[str, Any]
    ) -> bool:
        """
        评估单个条件
        
        Args:
            condition: 条件对象
            data: 数据字典
            
        Returns:
            bool: 条件是否满足
        """
        signal_value = data.get(condition.field)
        
        # 如果字段不存在，条件不满足
        if signal_value is None:
            return False
        
        operator = condition.operator
        target_value = condition.value
        
        try:
            if operator == ConditionOperator.EQ:
                return signal_value == target_value
            
            elif operator == ConditionOperator.NE:
                return signal_value != target_value
            
            elif operator == ConditionOperator.GT:
                return signal_value > target_value
            
            elif operator == ConditionOperator.GTE:
                return signal_value >= target_value
            
            elif operator == ConditionOperator.LT:
                return signal_value < target_value
            
            elif operator == ConditionOperator.LTE:
                return signal_value <= target_value
            
            elif operator == ConditionOperator.IN:
                return signal_value in target_value
            
            elif operator == ConditionOperator.NOT_IN:
                return signal_value not in target_value
            
            elif operator == ConditionOperator.BETWEEN:
                if isinstance(target_value, (list, tuple)) and len(target_value) == 2:
                    return target_value[0] <= signal_value <= target_value[1]
                return False
            
            elif operator == ConditionOperator.CONTAINS:
                return str(target_value) in str(signal_value)
            
            elif operator == ConditionOperator.STARTS_WITH:
                return str(signal_value).startswith(str(target_value))
            
            elif operator == ConditionOperator.ENDS_WITH:
                return str(signal_value).endswith(str(target_value))
            
            else:
                logger.warning(f"未知的运算符: {operator}")
                return False
                
        except Exception as e:
            logger.error(f"评估条件时出错: {e}")
            return False
    
    def _is_in_cooldown(self, rule_id: str) -> bool:
        """
        检查规则是否在冷却期
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 是否在冷却期
        """
        if rule_id not in self._cooldowns:
            return False
        
        cooldown_until = self._cooldowns[rule_id]
        if datetime.now() >= cooldown_until:
            # 冷却期已过，清除记录
            del self._cooldowns[rule_id]
            return False
        
        return True
    
    def _set_cooldown(self, rule_id: str, seconds: int):
        """
        设置规则冷却时间
        
        Args:
            rule_id: 规则ID
            seconds: 冷却秒数
        """
        if seconds > 0:
            self._cooldowns[rule_id] = datetime.now() + timedelta(seconds=seconds)
            logger.debug(f"规则 {rule_id} 进入冷却期 {seconds} 秒")
    
    def clear_cooldown(self, rule_id: str):
        """清除规则冷却时间"""
        self._cooldowns.pop(rule_id, None)
    
    def clear_all_cooldowns(self):
        """清除所有冷却时间"""
        self._cooldowns.clear()
    
    def get_cooldown_remaining(self, rule_id: str) -> Optional[int]:
        """
        获取规则剩余冷却时间（秒）
        
        Returns:
            Optional[int]: 剩余秒数，如果不在冷却期返回None
        """
        if rule_id not in self._cooldowns:
            return None
        
        cooldown_until = self._cooldowns[rule_id]
        remaining = (cooldown_until - datetime.now()).total_seconds()
        
        if remaining <= 0:
            del self._cooldowns[rule_id]
            return None
        
        return int(remaining)


# 全局规则运行时实例
rule_runtime = RuleRuntime()
