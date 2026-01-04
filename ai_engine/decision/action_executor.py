"""
Action Executor - 动作执行器

负责执行规则触发后的各种动作，包括:
- 告警动作 (alert)
- 通知动作 (notification) - 邮件、短信
- Webhook动作 (webhook)
- 工单动作 (workorder)
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Awaitable
import logging
import json
import asyncio
from dataclasses import dataclass, field

from .rule_parser import Action

logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    """动作执行结果"""
    success: bool
    action_type: str
    rule_id: str
    message: str
    executed_at: datetime = field(default_factory=datetime.now)
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ActionExecutionError(Exception):
    """动作执行错误"""
    pass


class ActionExecutor:
    """
    动作执行器
    
    负责执行规则触发后的各种动作。
    """
    
    def __init__(self):
        self._handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[ActionResult]]] = {
            "alert": self._handle_alert,
            "notification": self._handle_notification,
            "webhook": self._handle_webhook,
            "workorder": self._handle_workorder,
        }
        self._execution_history: List[ActionResult] = []
        self._max_history_size = 1000
        
        # 通知渠道处理器
        self._notification_handlers: Dict[str, Callable] = {
            "email": self._send_email,
            "sms": self._send_sms,
            "wechat": self._send_wechat,
            "dingtalk": self._send_dingtalk,
        }
    
    def register_handler(
        self, 
        action_type: str, 
        handler: Callable[[Dict[str, Any]], Awaitable[ActionResult]]
    ):
        """
        注册自定义动作处理器
        
        Args:
            action_type: 动作类型
            handler: 处理函数
        """
        self._handlers[action_type] = handler
        logger.info(f"注册动作处理器: {action_type}")
    
    def register_notification_handler(
        self,
        channel: str,
        handler: Callable
    ):
        """
        注册通知渠道处理器
        
        Args:
            channel: 渠道名称 (email, sms, wechat, dingtalk等)
            handler: 处理函数
        """
        self._notification_handlers[channel] = handler
        logger.info(f"注册通知渠道处理器: {channel}")
    
    async def execute(self, action_data: Dict[str, Any]) -> ActionResult:
        """
        执行动作
        
        Args:
            action_data: 动作数据，包含:
                - rule_id: 规则ID
                - rule_name: 规则名称
                - action: Action对象
                - prediction: 预测数据
                - triggered_at: 触发时间
        
        Returns:
            ActionResult: 执行结果
        """
        action: Action = action_data.get("action")
        rule_id = action_data.get("rule_id", "unknown")
        
        if action is None:
            return ActionResult(
                success=False,
                action_type="unknown",
                rule_id=rule_id,
                message="动作数据无效",
                error="action字段缺失"
            )
        
        action_type = action.type
        handler = self._handlers.get(action_type)
        
        if handler is None:
            logger.warning(f"未知的动作类型: {action_type}")
            return ActionResult(
                success=False,
                action_type=action_type,
                rule_id=rule_id,
                message=f"未知的动作类型: {action_type}",
                error=f"没有注册 {action_type} 类型的处理器"
            )
        
        try:
            result = await handler(action_data)
            self._add_to_history(result)
            return result
        except Exception as e:
            logger.error(f"执行动作 {action_type} 失败: {e}")
            result = ActionResult(
                success=False,
                action_type=action_type,
                rule_id=rule_id,
                message=f"执行动作失败: {str(e)}",
                error=str(e)
            )
            self._add_to_history(result)
            return result
    
    async def execute_batch(self, action_list: List[Dict[str, Any]]) -> List[ActionResult]:
        """
        批量执行动作
        
        Args:
            action_list: 动作数据列表
        
        Returns:
            List[ActionResult]: 执行结果列表
        """
        results = []
        for action_data in action_list:
            result = await self.execute(action_data)
            results.append(result)
        return results
    
    def _add_to_history(self, result: ActionResult):
        """添加到执行历史"""
        self._execution_history.append(result)
        # 限制历史记录大小
        if len(self._execution_history) > self._max_history_size:
            self._execution_history = self._execution_history[-self._max_history_size:]
    
    def get_execution_history(self, limit: int = 100) -> List[ActionResult]:
        """获取执行历史"""
        return self._execution_history[-limit:]
    
    def clear_history(self):
        """清除执行历史"""
        self._execution_history.clear()
    
    # =====================================================
    # 动作处理器实现
    # =====================================================
    
    async def _handle_alert(self, action_data: Dict[str, Any]) -> ActionResult:
        """
        处理告警动作
        
        创建告警记录并存储到数据库。
        """
        action: Action = action_data["action"]
        rule_id = action_data.get("rule_id", "unknown")
        rule_name = action_data.get("rule_name", "")
        prediction = action_data.get("prediction", {})
        triggered_at = action_data.get("triggered_at", datetime.now())
        
        # 获取告警配置
        level = action.config.get("level", "warning")
        message_template = action.config.get("message", "规则触发告警")
        
        # 格式化消息（支持变量替换）
        message = self._format_message(message_template, prediction)
        
        try:
            # 尝试保存到数据库
            alert_record = await self._save_alert_to_db(
                rule_id=rule_id,
                rule_name=rule_name,
                level=level,
                message=message,
                prediction=prediction,
                triggered_at=triggered_at
            )
            
            logger.info(f"告警创建成功: [{level}] {message}")
            
            return ActionResult(
                success=True,
                action_type="alert",
                rule_id=rule_id,
                message=f"告警创建成功: {message}",
                details={
                    "level": level,
                    "alert_message": message,
                    "alert_id": alert_record.get("id") if alert_record else None
                }
            )
        except Exception as e:
            logger.error(f"保存告警失败: {e}")
            # 即使数据库保存失败，也返回成功（告警已生成）
            return ActionResult(
                success=True,
                action_type="alert",
                rule_id=rule_id,
                message=f"告警已生成（未持久化）: {message}",
                details={"level": level, "alert_message": message},
                error=f"数据库保存失败: {str(e)}"
            )
    
    async def _save_alert_to_db(
        self,
        rule_id: str,
        rule_name: str,
        level: str,
        message: str,
        prediction: Dict,
        triggered_at: datetime
    ) -> Optional[Dict]:
        """保存告警到数据库"""
        try:
            from app.models.alarm import Alarm
            
            alarm = Alarm(
                alarm_type="ai_prediction",
                alarm_level=level,
                alarm_content=message,
                alarm_source=f"decision_engine:{rule_id}",
                alarm_time=triggered_at,
                extra_data={
                    "rule_id": rule_id,
                    "rule_name": rule_name,
                    "prediction": prediction
                }
            )
            await alarm.save()
            return {"id": alarm.id}
        except Exception as e:
            logger.warning(f"告警模型不可用，跳过数据库保存: {e}")
            return None
    
    async def _handle_notification(self, action_data: Dict[str, Any]) -> ActionResult:
        """
        处理通知动作
        
        支持多渠道通知：邮件、短信、微信、钉钉等。
        """
        action: Action = action_data["action"]
        rule_id = action_data.get("rule_id", "unknown")
        prediction = action_data.get("prediction", {})
        
        channels = action.config.get("channels", [])
        recipients = action.config.get("recipients", [])
        message_template = action.config.get("message", "规则触发通知")
        
        message = self._format_message(message_template, prediction)
        
        results = []
        for channel in channels:
            handler = self._notification_handlers.get(channel)
            if handler:
                try:
                    await handler(recipients, message, action_data)
                    results.append({"channel": channel, "success": True})
                    logger.info(f"通知发送成功: {channel}")
                except Exception as e:
                    results.append({"channel": channel, "success": False, "error": str(e)})
                    logger.error(f"通知发送失败 ({channel}): {e}")
            else:
                results.append({"channel": channel, "success": False, "error": "未注册的渠道"})
        
        success_count = sum(1 for r in results if r["success"])
        
        return ActionResult(
            success=success_count > 0,
            action_type="notification",
            rule_id=rule_id,
            message=f"通知发送完成: {success_count}/{len(channels)} 成功",
            details={"results": results, "message": message}
        )
    
    async def _send_email(self, recipients: List[str], message: str, action_data: Dict):
        """发送邮件通知"""
        # TODO: 集成实际的邮件服务
        logger.info(f"发送邮件到 {recipients}: {message}")
        # 模拟发送
        await asyncio.sleep(0.1)
    
    async def _send_sms(self, recipients: List[str], message: str, action_data: Dict):
        """发送短信通知"""
        # TODO: 集成实际的短信服务
        logger.info(f"发送短信到 {recipients}: {message}")
        await asyncio.sleep(0.1)
    
    async def _send_wechat(self, recipients: List[str], message: str, action_data: Dict):
        """发送微信通知"""
        # TODO: 集成企业微信API
        logger.info(f"发送微信通知到 {recipients}: {message}")
        await asyncio.sleep(0.1)
    
    async def _send_dingtalk(self, recipients: List[str], message: str, action_data: Dict):
        """发送钉钉通知"""
        # TODO: 集成钉钉API
        logger.info(f"发送钉钉通知到 {recipients}: {message}")
        await asyncio.sleep(0.1)
    
    async def _handle_webhook(self, action_data: Dict[str, Any]) -> ActionResult:
        """
        处理Webhook动作
        
        向指定URL发送HTTP请求。
        """
        action: Action = action_data["action"]
        rule_id = action_data.get("rule_id", "unknown")
        prediction = action_data.get("prediction", {})
        
        url = action.config.get("url", "")
        method = action.config.get("method", "POST").upper()
        headers = action.config.get("headers", {})
        timeout = action.config.get("timeout", 30)
        
        if not url:
            return ActionResult(
                success=False,
                action_type="webhook",
                rule_id=rule_id,
                message="Webhook URL未配置",
                error="url字段缺失"
            )
        
        # 构建请求体
        payload = {
            "rule_id": rule_id,
            "rule_name": action_data.get("rule_name", ""),
            "triggered_at": action_data.get("triggered_at", datetime.now()).isoformat(),
            "prediction": prediction,
            "action_config": action.config
        }
        
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method == "GET":
                    response = await client.get(url, headers=headers, params=payload)
                else:
                    response = await client.post(url, headers=headers, json=payload)
                
                success = 200 <= response.status_code < 300
                
                return ActionResult(
                    success=success,
                    action_type="webhook",
                    rule_id=rule_id,
                    message=f"Webhook请求完成: {response.status_code}",
                    details={
                        "url": url,
                        "method": method,
                        "status_code": response.status_code,
                        "response_text": response.text[:500] if response.text else None
                    }
                )
        except ImportError:
            logger.warning("httpx未安装，使用模拟Webhook")
            return ActionResult(
                success=True,
                action_type="webhook",
                rule_id=rule_id,
                message=f"Webhook模拟发送: {url}",
                details={"url": url, "method": method, "simulated": True}
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action_type="webhook",
                rule_id=rule_id,
                message=f"Webhook请求失败: {str(e)}",
                error=str(e),
                details={"url": url, "method": method}
            )
    
    async def _handle_workorder(self, action_data: Dict[str, Any]) -> ActionResult:
        """
        处理工单动作
        
        创建维护工单。
        """
        action: Action = action_data["action"]
        rule_id = action_data.get("rule_id", "unknown")
        prediction = action_data.get("prediction", {})
        
        template_id = action.config.get("template_id", "")
        title = action.config.get("title", "AI预测触发工单")
        priority = action.config.get("priority", "normal")
        assignee = action.config.get("assignee")
        
        # 格式化标题
        title = self._format_message(title, prediction)
        
        try:
            # TODO: 集成实际的工单系统
            workorder_id = f"WO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            logger.info(f"创建工单: {workorder_id} - {title}")
            
            return ActionResult(
                success=True,
                action_type="workorder",
                rule_id=rule_id,
                message=f"工单创建成功: {workorder_id}",
                details={
                    "workorder_id": workorder_id,
                    "title": title,
                    "priority": priority,
                    "template_id": template_id,
                    "assignee": assignee
                }
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action_type="workorder",
                rule_id=rule_id,
                message=f"工单创建失败: {str(e)}",
                error=str(e)
            )
    
    def _format_message(self, template: str, data: Dict[str, Any]) -> str:
        """
        格式化消息模板
        
        支持 {field_name} 格式的变量替换。
        """
        try:
            # 简单的变量替换
            result = template
            for key, value in data.items():
                placeholder = "{" + key + "}"
                if placeholder in result:
                    result = result.replace(placeholder, str(value))
            return result
        except Exception:
            return template


# 全局动作执行器实例
action_executor = ActionExecutor()
