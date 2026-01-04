"""
决策引擎模块 (Decision)

将AI预测结果转化为告警和动作，实现预测性维护的完整闭环。

主要组件:
- RuleParser: 规则DSL解析器
- RuleRuntime: 规则运行时引擎
- ActionExecutor: 动作执行器
- AuditLogger: 审计日志记录器

注意: 此模块从 ai_engine/decision_engine 重命名而来，保持API兼容性。
"""

from .rule_parser import (
    RuleParser,
    Rule,
    Condition,
    ConditionGroup,
    Action,
    ConditionOperator,
    LogicalOperator,
    RuleParseError,
    RuleValidationError,
)

from .rule_runtime import (
    RuleRuntime,
    RuleEvaluationError,
    rule_runtime,
)

from .action_executor import (
    ActionExecutor,
    ActionResult,
    ActionExecutionError,
    action_executor,
)

from .audit_logger import (
    AuditLogger,
    AuditLogEntry,
    audit_logger,
)

__all__ = [
    # Rule Parser
    "RuleParser",
    "Rule",
    "Condition",
    "ConditionGroup",
    "Action",
    "ConditionOperator",
    "LogicalOperator",
    "RuleParseError",
    "RuleValidationError",
    # Rule Runtime
    "RuleRuntime",
    "RuleEvaluationError",
    "rule_runtime",
    # Action Executor
    "ActionExecutor",
    "ActionResult",
    "ActionExecutionError",
    "action_executor",
    # Audit Logger
    "AuditLogger",
    "AuditLogEntry",
    "audit_logger",
]
