"""
实时推送服务

实现Redis发布订阅集成和数据推送逻辑。

需求: 3.2 - 当资产数据更新时，平台应在1秒内将数据推送到订阅的客户端
需求: 3.6 - 当推送数据时，平台应包含时间戳和数据质量标识
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ============================================================================
# 消息格式定义和创建函数
# ============================================================================

VALID_QUALITY_VALUES = ["good", "bad", "uncertain"]
VALID_MESSAGE_TYPES = ["asset_data", "alert", "prediction", "connection", "system"]


def create_asset_data_message(
    asset_id: int,
    data: Dict[str, Any],
    quality: str = "good",
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    创建资产数据消息
    
    Args:
        asset_id: 资产ID
        data: 数据内容
        quality: 数据质量标识 (good/bad/uncertain)
        timestamp: 时间戳（ISO格式），默认为当前时间
        
    Returns:
        Dict: 格式化的消息
    """
    if quality not in VALID_QUALITY_VALUES:
        quality = "good"
    
    return {
        "type": "asset_data",
        "asset_id": asset_id,
        "data": data,
        "timestamp": timestamp or datetime.now().isoformat(),
        "quality": quality
    }


def create_alert_message(
    alert: Dict[str, Any],
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    创建告警消息
    
    Args:
        alert: 告警内容
        timestamp: 时间戳（ISO格式），默认为当前时间
        
    Returns:
        Dict: 格式化的消息
    """
    return {
        "type": "alert",
        "alert": alert,
        "timestamp": timestamp or datetime.now().isoformat()
    }


def create_prediction_message(
    asset_id: int,
    model_id: int,
    prediction: Dict[str, Any],
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    创建预测结果消息
    
    Args:
        asset_id: 资产ID
        model_id: 模型ID
        prediction: 预测结果
        timestamp: 时间戳
        
    Returns:
        Dict: 格式化的消息
    """
    return {
        "type": "prediction",
        "asset_id": asset_id,
        "model_id": model_id,
        "prediction": prediction,
        "timestamp": timestamp or datetime.now().isoformat(),
        "quality": "good"
    }


def create_system_message(
    event: str,
    details: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    创建系统消息
    
    Args:
        event: 事件类型
        details: 详细信息
        timestamp: 时间戳
        
    Returns:
        Dict: 格式化的消息
    """
    return {
        "type": "system",
        "event": event,
        "details": details or {},
        "timestamp": timestamp or datetime.now().isoformat()
    }


def validate_message_format(message: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    验证消息格式
    
    Args:
        message: 消息内容
        
    Returns:
        Tuple[bool, List[str]]: (是否有效, 错误列表)
    """
    errors = []
    
    # 检查type字段
    if "type" not in message:
        errors.append("缺少type字段")
    elif message["type"] not in VALID_MESSAGE_TYPES:
        errors.append(f"无效的type值: {message['type']}")
    
    # 检查timestamp字段
    if "timestamp" not in message:
        errors.append("缺少timestamp字段")
    else:
        try:
            datetime.fromisoformat(message["timestamp"])
        except (ValueError, TypeError):
            errors.append("timestamp格式无效")
    
    # 根据消息类型检查特定字段
    msg_type = message.get("type")
    
    if msg_type == "asset_data":
        if "asset_id" not in message:
            errors.append("asset_data消息缺少asset_id字段")
        if "data" not in message:
            errors.append("asset_data消息缺少data字段")
        if "quality" not in message:
            errors.append("asset_data消息缺少quality字段")
        elif message.get("quality") not in VALID_QUALITY_VALUES:
            errors.append(f"无效的quality值: {message.get('quality')}")
    
    elif msg_type == "alert":
        if "alert" not in message:
            errors.append("alert消息缺少alert字段")
    
    elif msg_type == "prediction":
        if "asset_id" not in message:
            errors.append("prediction消息缺少asset_id字段")
        if "prediction" not in message:
            errors.append("prediction消息缺少prediction字段")
    
    return len(errors) == 0, errors


# ============================================================================
# 实时推送服务
# ============================================================================

@dataclass
class PushStats:
    """推送统计信息"""
    total_pushed: int = 0
    total_failed: int = 0
    last_push_time: Optional[datetime] = None
    messages_per_second: float = 0.0


class RealtimePushService:
    """
    实时数据推送服务
    
    负责：
    - 订阅Redis数据更新通道
    - 将数据推送到WebSocket客户端
    - 管理推送统计
    """
    
    def __init__(self):
        self._redis_client = None
        self._running = False
        self._push_task: Optional[asyncio.Task] = None
        self._stats = PushStats()
        self._message_handlers: Dict[str, Callable] = {}
        
        # 导入连接管理器（延迟导入避免循环依赖）
        self._connection_manager = None
        self._subscription_manager = None
    
    @property
    def connection_manager(self):
        """获取连接管理器"""
        if self._connection_manager is None:
            from .websocket_server import connection_manager
            self._connection_manager = connection_manager
        return self._connection_manager
    
    @property
    def subscription_manager(self):
        """获取订阅管理器"""
        if self._subscription_manager is None:
            from .subscription_manager import subscription_manager
            self._subscription_manager = subscription_manager
        return self._subscription_manager
    
    async def initialize(self, redis_client=None):
        """
        初始化推送服务
        
        Args:
            redis_client: Redis客户端实例
        """
        if redis_client:
            self._redis_client = redis_client
        else:
            # 尝试从应用获取Redis客户端
            try:
                from app.core.redis import get_redis_client
                client = await get_redis_client()
                self._redis_client = client.redis
            except Exception as e:
                logger.warning(f"无法获取Redis客户端: {e}")
    
    async def start(self):
        """启动推送服务"""
        if self._running:
            logger.warning("推送服务已在运行")
            return
        
        self._running = True
        
        if self._redis_client:
            self._push_task = asyncio.create_task(self._subscribe_to_data_updates())
            logger.info("实时推送服务已启动")
        else:
            logger.warning("Redis客户端未配置，推送服务以本地模式运行")
    
    async def stop(self):
        """停止推送服务"""
        self._running = False
        
        if self._push_task:
            self._push_task.cancel()
            try:
                await self._push_task
            except asyncio.CancelledError:
                pass
            self._push_task = None
        
        logger.info("实时推送服务已停止")
    
    async def _subscribe_to_data_updates(self):
        """订阅Redis数据更新通道"""
        try:
            pubsub = self._redis_client.pubsub()
            await pubsub.subscribe(
                "asset_data_updates",
                "alert_updates",
                "prediction_updates"
            )
            
            logger.info("已订阅Redis数据更新通道")
            
            while self._running:
                try:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=1.0
                    )
                    
                    if message and message.get("type") == "message":
                        channel = message.get("channel", "")
                        data = message.get("data", "")
                        
                        if isinstance(data, bytes):
                            data = data.decode("utf-8")
                        
                        await self._handle_redis_message(channel, data)
                    
                    await asyncio.sleep(0.01)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"处理Redis消息失败: {e}")
                    await asyncio.sleep(1)
            
            await pubsub.unsubscribe()
            
        except Exception as e:
            logger.error(f"Redis订阅失败: {e}")
    
    async def _handle_redis_message(self, channel: str, data: str):
        """
        处理Redis消息
        
        Args:
            channel: 通道名称
            data: 消息数据
        """
        try:
            message_data = json.loads(data)
            
            if channel == "asset_data_updates":
                await self._handle_asset_data_update(message_data)
            elif channel == "alert_updates":
                await self._handle_alert_update(message_data)
            elif channel == "prediction_updates":
                await self._handle_prediction_update(message_data)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
    
    async def _handle_asset_data_update(self, data: Dict[str, Any]):
        """处理资产数据更新"""
        asset_id = data.get("asset_id")
        if not asset_id:
            return
        
        message = create_asset_data_message(
            asset_id=asset_id,
            data=data.get("data", {}),
            quality=data.get("quality", "good"),
            timestamp=data.get("timestamp")
        )
        
        await self.push_to_asset_subscribers(asset_id, message)
    
    async def _handle_alert_update(self, data: Dict[str, Any]):
        """处理告警更新"""
        alert = data.get("alert", data)
        asset_id = alert.get("asset_id")
        
        message = create_alert_message(alert)
        
        if asset_id:
            # 推送给资产订阅者
            await self.push_to_asset_subscribers(asset_id, message, data_type="alert")
        else:
            # 广播给所有用户
            await self.broadcast(message)
    
    async def _handle_prediction_update(self, data: Dict[str, Any]):
        """处理预测结果更新"""
        asset_id = data.get("asset_id")
        model_id = data.get("model_id")
        prediction = data.get("prediction", {})
        
        if not asset_id:
            return
        
        message = create_prediction_message(
            asset_id=asset_id,
            model_id=model_id,
            prediction=prediction,
            timestamp=data.get("timestamp")
        )
        
        await self.push_to_asset_subscribers(asset_id, message, data_type="prediction")
    
    async def push_to_asset_subscribers(
        self,
        asset_id: int,
        message: Dict[str, Any],
        data_type: str = "asset_data"
    ) -> int:
        """
        向资产订阅者推送消息
        
        Args:
            asset_id: 资产ID
            message: 消息内容
            data_type: 数据类型
            
        Returns:
            int: 成功推送的用户数
        """
        # 获取应该接收数据的用户
        subscribers = self.subscription_manager.filter_subscribers_for_asset(
            asset_id, data_type
        )
        
        if not subscribers:
            return 0
        
        success_count = 0
        
        for user_id in subscribers:
            if await self.connection_manager.push_to_user(user_id, message):
                success_count += 1
                self._stats.total_pushed += 1
            else:
                self._stats.total_failed += 1
        
        self._stats.last_push_time = datetime.now()
        
        return success_count
    
    async def push_to_user(self, user_id: int, message: Dict[str, Any]) -> bool:
        """
        向指定用户推送消息
        
        Args:
            user_id: 用户ID
            message: 消息内容
            
        Returns:
            bool: 是否成功
        """
        success = await self.connection_manager.push_to_user(user_id, message)
        
        if success:
            self._stats.total_pushed += 1
        else:
            self._stats.total_failed += 1
        
        self._stats.last_push_time = datetime.now()
        
        return success
    
    async def broadcast(self, message: Dict[str, Any]) -> int:
        """
        广播消息给所有连接的用户
        
        Args:
            message: 消息内容
            
        Returns:
            int: 成功推送的用户数
        """
        count = await self.connection_manager.broadcast(message)
        self._stats.total_pushed += count
        self._stats.last_push_time = datetime.now()
        return count
    
    async def publish_asset_data(
        self,
        asset_id: int,
        data: Dict[str, Any],
        quality: str = "good"
    ):
        """
        发布资产数据更新（通过Redis）
        
        Args:
            asset_id: 资产ID
            data: 数据内容
            quality: 数据质量
        """
        if not self._redis_client:
            # 本地模式，直接推送
            message = create_asset_data_message(asset_id, data, quality)
            await self.push_to_asset_subscribers(asset_id, message)
            return
        
        message = {
            "asset_id": asset_id,
            "data": data,
            "quality": quality,
            "timestamp": datetime.now().isoformat()
        }
        
        await self._redis_client.publish(
            "asset_data_updates",
            json.dumps(message, ensure_ascii=False)
        )
    
    async def publish_alert(self, alert: Dict[str, Any]):
        """
        发布告警更新（通过Redis）
        
        Args:
            alert: 告警内容
        """
        if not self._redis_client:
            message = create_alert_message(alert)
            asset_id = alert.get("asset_id")
            if asset_id:
                await self.push_to_asset_subscribers(asset_id, message, "alert")
            else:
                await self.broadcast(message)
            return
        
        await self._redis_client.publish(
            "alert_updates",
            json.dumps({"alert": alert}, ensure_ascii=False)
        )
    
    async def publish_prediction(
        self,
        asset_id: int,
        model_id: int,
        prediction: Dict[str, Any]
    ):
        """
        发布预测结果更新（通过Redis）
        
        Args:
            asset_id: 资产ID
            model_id: 模型ID
            prediction: 预测结果
        """
        if not self._redis_client:
            message = create_prediction_message(asset_id, model_id, prediction)
            await self.push_to_asset_subscribers(asset_id, message, "prediction")
            return
        
        message = {
            "asset_id": asset_id,
            "model_id": model_id,
            "prediction": prediction,
            "timestamp": datetime.now().isoformat()
        }
        
        await self._redis_client.publish(
            "prediction_updates",
            json.dumps(message, ensure_ascii=False)
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取推送统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            "running": self._running,
            "total_pushed": self._stats.total_pushed,
            "total_failed": self._stats.total_failed,
            "last_push_time": self._stats.last_push_time.isoformat() if self._stats.last_push_time else None,
            "redis_connected": self._redis_client is not None
        }


# 全局推送服务实例
push_service = RealtimePushService()
