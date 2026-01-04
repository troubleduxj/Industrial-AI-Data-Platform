"""
Audit Logger - 决策审计日志记录器

记录决策引擎规则触发的完整审计日志，包括:
- 规则触发时间
- 触发时的数据快照
- 条件配置快照
- 执行的动作
- 执行结果
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import time
from dataclasses import dataclass, field, asdict

from .rule_parser import Rule

logger = logging.getLogger(__name__)


@dataclass
class AuditLogEntry:
    """审计日志条目"""
    rule_id: str
    rule_name: str
    trigger_time: datetime
    trigger_data: Dict[str, Any]
    conditions_snapshot: Dict[str, Any]
    actions_executed: List[Dict[str, Any]]
    result: str = "success"  # success, partial, failed
    error_message: Optional[str] = None
    execution_duration_ms: Optional[int] = None
    asset_id: Optional[int] = None
    prediction_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["trigger_time"] = self.trigger_time.isoformat()
        return data


class AuditLogger:
    """
    决策审计日志记录器
    
    负责记录规则触发的完整审计日志。
    """
    
    def __init__(self):
        self._memory_logs: List[AuditLogEntry] = []
        self._max_memory_logs = 1000
        self._db_enabled = True
    
    def enable_db_logging(self):
        """启用数据库日志"""
        self._db_enabled = True
    
    def disable_db_logging(self):
        """禁用数据库日志"""
        self._db_enabled = False
    
    async def log_trigger(
        self,
        rule: Rule,
        prediction: Dict[str, Any],
        triggered_at: Optional[datetime] = None,
        actions_executed: Optional[List[Dict[str, Any]]] = None,
        result: str = "success",
        error_message: Optional[str] = None,
        execution_duration_ms: Optional[int] = None
    ) -> AuditLogEntry:
        """
        记录规则触发日志
        
        Args:
            rule: 触发的规则
            prediction: 预测数据
            triggered_at: 触发时间
            actions_executed: 执行的动作列表
            result: 执行结果
            error_message: 错误信息
            execution_duration_ms: 执行耗时
        
        Returns:
            AuditLogEntry: 审计日志条目
        """
        if triggered_at is None:
            triggered_at = datetime.now()
        
        if actions_executed is None:
            actions_executed = [a.to_dict() for a in rule.actions]
        
        entry = AuditLogEntry(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            trigger_time=triggered_at,
            trigger_data=prediction,
            conditions_snapshot=rule.conditions.to_dict(),
            actions_executed=actions_executed,
            result=result,
            error_message=error_message,
            execution_duration_ms=execution_duration_ms,
            asset_id=prediction.get("asset_id"),
            prediction_id=prediction.get("prediction_id")
        )
        
        # 添加到内存日志
        self._add_to_memory(entry)
        
        # 保存到数据库
        if self._db_enabled:
            await self._save_to_db(entry)
        
        logger.info(
            f"审计日志: 规则 {rule.rule_id} 触发, "
            f"结果: {result}, "
            f"动作数: {len(actions_executed)}"
        )
        
        return entry
    
    def log_trigger_sync(
        self,
        rule: Rule,
        prediction: Dict[str, Any],
        triggered_at: Optional[datetime] = None,
        actions_executed: Optional[List[Dict[str, Any]]] = None,
        result: str = "success",
        error_message: Optional[str] = None
    ) -> AuditLogEntry:
        """
        同步版本的日志记录（不保存到数据库）
        
        用于测试或不需要持久化的场景。
        """
        if triggered_at is None:
            triggered_at = datetime.now()
        
        if actions_executed is None:
            actions_executed = [a.to_dict() for a in rule.actions]
        
        entry = AuditLogEntry(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            trigger_time=triggered_at,
            trigger_data=prediction,
            conditions_snapshot=rule.conditions.to_dict(),
            actions_executed=actions_executed,
            result=result,
            error_message=error_message,
            asset_id=prediction.get("asset_id"),
            prediction_id=prediction.get("prediction_id")
        )
        
        self._add_to_memory(entry)
        return entry
    
    def _add_to_memory(self, entry: AuditLogEntry):
        """添加到内存日志"""
        self._memory_logs.append(entry)
        # 限制内存日志大小
        if len(self._memory_logs) > self._max_memory_logs:
            self._memory_logs = self._memory_logs[-self._max_memory_logs:]
    
    async def _save_to_db(self, entry: AuditLogEntry):
        """保存到数据库"""
        try:
            from app.models.platform_upgrade import DecisionAuditLog
            
            audit_log = DecisionAuditLog(
                rule_id=entry.rule_id,
                rule_name=entry.rule_name,
                trigger_time=entry.trigger_time,
                trigger_data=entry.trigger_data,
                conditions_snapshot=entry.conditions_snapshot,
                actions_executed=entry.actions_executed,
                result=entry.result,
                error_message=entry.error_message,
                execution_duration_ms=entry.execution_duration_ms,
                asset_id=entry.asset_id,
                prediction_id=entry.prediction_id
            )
            await audit_log.save()
            logger.debug(f"审计日志已保存到数据库: {audit_log.id}")
            
        except Exception as e:
            logger.warning(f"保存审计日志到数据库失败: {e}")
    
    def get_memory_logs(
        self,
        rule_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """
        获取内存中的审计日志
        
        Args:
            rule_id: 可选，按规则ID过滤
            limit: 返回数量限制
        
        Returns:
            List[AuditLogEntry]: 审计日志列表
        """
        logs = self._memory_logs
        
        if rule_id:
            logs = [log for log in logs if log.rule_id == rule_id]
        
        return logs[-limit:]
    
    def clear_memory_logs(self):
        """清除内存日志"""
        self._memory_logs.clear()
    
    async def query_logs(
        self,
        rule_id: Optional[str] = None,
        asset_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        result: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        从数据库查询审计日志
        
        Args:
            rule_id: 规则ID过滤
            asset_id: 资产ID过滤
            start_time: 开始时间
            end_time: 结束时间
            result: 结果过滤
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            List[Dict]: 审计日志列表
        """
        try:
            from app.models.platform_upgrade import DecisionAuditLog
            
            query = DecisionAuditLog.all()
            
            if rule_id:
                query = query.filter(rule_id=rule_id)
            if asset_id:
                query = query.filter(asset_id=asset_id)
            if start_time:
                query = query.filter(trigger_time__gte=start_time)
            if end_time:
                query = query.filter(trigger_time__lte=end_time)
            if result:
                query = query.filter(result=result)
            
            logs = await query.order_by("-trigger_time").offset(offset).limit(limit)
            
            return [
                {
                    "id": log.id,
                    "rule_id": log.rule_id,
                    "rule_name": log.rule_name,
                    "trigger_time": log.trigger_time.isoformat(),
                    "trigger_data": log.trigger_data,
                    "conditions_snapshot": log.conditions_snapshot,
                    "actions_executed": log.actions_executed,
                    "result": log.result,
                    "error_message": log.error_message,
                    "execution_duration_ms": log.execution_duration_ms,
                    "asset_id": log.asset_id,
                    "prediction_id": log.prediction_id,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                }
                for log in logs
            ]
            
        except Exception as e:
            logger.error(f"查询审计日志失败: {e}")
            return []
    
    async def get_statistics(
        self,
        rule_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取审计日志统计信息
        
        Args:
            rule_id: 规则ID过滤
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            Dict: 统计信息
        """
        try:
            from app.models.platform_upgrade import DecisionAuditLog
            from tortoise.functions import Count
            
            query = DecisionAuditLog.all()
            
            if rule_id:
                query = query.filter(rule_id=rule_id)
            if start_time:
                query = query.filter(trigger_time__gte=start_time)
            if end_time:
                query = query.filter(trigger_time__lte=end_time)
            
            total = await query.count()
            success_count = await query.filter(result="success").count()
            partial_count = await query.filter(result="partial").count()
            failed_count = await query.filter(result="failed").count()
            
            return {
                "total": total,
                "success": success_count,
                "partial": partial_count,
                "failed": failed_count,
                "success_rate": success_count / total if total > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"获取审计日志统计失败: {e}")
            return {
                "total": 0,
                "success": 0,
                "partial": 0,
                "failed": 0,
                "success_rate": 0
            }


# 全局审计日志记录器实例
audit_logger = AuditLogger()
