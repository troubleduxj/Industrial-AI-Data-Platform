"""
WebSocket连接管理器

实现WebSocket连接的建立、断开和管理功能。
支持用户认证验证和连接状态管理。

需求: 3.1 - 当客户端连接WebSocket时，平台应建立持久连接并进行身份验证
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional, Any, List
from dataclasses import dataclass, field

from fastapi import WebSocket, WebSocketDisconnect, status

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """WebSocket连接信息"""
    user_id: int
    websocket: WebSocket
    connected_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    subscribed_assets: Set[int] = field(default_factory=set)
    
    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity = datetime.now()


class ConnectionManager:
    """
    WebSocket连接管理器
    
    负责管理所有WebSocket连接，包括：
    - 连接建立和断开
    - 用户认证验证
    - 订阅管理
    - 消息推送
    """
    
    def __init__(self):
        # 用户ID -> 连接信息
        self._connections: Dict[int, ConnectionInfo] = {}
        # 资产ID -> 订阅的用户ID集合
        self._asset_subscriptions: Dict[int, Set[int]] = {}
        # 锁，用于线程安全操作
        self._lock = asyncio.Lock()
        
    @property
    def active_connections(self) -> int:
        """获取活跃连接数"""
        return len(self._connections)
    
    @property
    def total_subscriptions(self) -> int:
        """获取总订阅数"""
        return sum(len(users) for users in self._asset_subscriptions.values())
    
    async def connect(self, websocket: WebSocket, user_id: int) -> bool:
        """
        建立WebSocket连接
        
        Args:
            websocket: WebSocket连接对象
            user_id: 用户ID
            
        Returns:
            bool: 连接是否成功建立
        """
        try:
            await websocket.accept()
            
            async with self._lock:
                # 如果用户已有连接，先断开旧连接
                if user_id in self._connections:
                    old_conn = self._connections[user_id]
                    try:
                        await old_conn.websocket.close(
                            code=status.WS_1008_POLICY_VIOLATION,
                            reason="新连接已建立"
                        )
                    except Exception:
                        pass
                    # 清理旧订阅
                    self._cleanup_user_subscriptions(user_id)
                
                # 创建新连接信息
                conn_info = ConnectionInfo(
                    user_id=user_id,
                    websocket=websocket
                )
                self._connections[user_id] = conn_info
            
            logger.info(f"WebSocket连接建立: user_id={user_id}")
            
            # 发送连接成功消息
            await self._send_message(websocket, {
                "type": "connection",
                "status": "connected",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"WebSocket连接失败: user_id={user_id}, error={e}")
            return False
    
    async def disconnect(self, user_id: int):
        """
        断开WebSocket连接
        
        Args:
            user_id: 用户ID
        """
        async with self._lock:
            if user_id in self._connections:
                conn_info = self._connections[user_id]
                
                # 清理订阅
                self._cleanup_user_subscriptions(user_id)
                
                # 移除连接
                del self._connections[user_id]
                
                logger.info(f"WebSocket连接断开: user_id={user_id}")
    
    def _cleanup_user_subscriptions(self, user_id: int):
        """
        清理用户的所有订阅（内部方法，需在锁内调用）
        
        Args:
            user_id: 用户ID
        """
        if user_id in self._connections:
            subscribed_assets = self._connections[user_id].subscribed_assets.copy()
            for asset_id in subscribed_assets:
                if asset_id in self._asset_subscriptions:
                    self._asset_subscriptions[asset_id].discard(user_id)
                    # 如果没有订阅者了，移除资产订阅记录
                    if not self._asset_subscriptions[asset_id]:
                        del self._asset_subscriptions[asset_id]
    
    async def subscribe(self, user_id: int, asset_ids: List[int]) -> bool:
        """
        订阅资产数据
        
        Args:
            user_id: 用户ID
            asset_ids: 资产ID列表
            
        Returns:
            bool: 订阅是否成功
        """
        async with self._lock:
            if user_id not in self._connections:
                logger.warning(f"订阅失败: 用户未连接 user_id={user_id}")
                return False
            
            conn_info = self._connections[user_id]
            
            for asset_id in asset_ids:
                # 添加到资产订阅映射
                if asset_id not in self._asset_subscriptions:
                    self._asset_subscriptions[asset_id] = set()
                self._asset_subscriptions[asset_id].add(user_id)
                
                # 添加到用户订阅列表
                conn_info.subscribed_assets.add(asset_id)
            
            conn_info.update_activity()
            
        logger.info(f"订阅成功: user_id={user_id}, assets={asset_ids}")
        return True
    
    async def unsubscribe(self, user_id: int, asset_ids: List[int]) -> bool:
        """
        取消订阅资产数据
        
        Args:
            user_id: 用户ID
            asset_ids: 资产ID列表
            
        Returns:
            bool: 取消订阅是否成功
        """
        async with self._lock:
            if user_id not in self._connections:
                return False
            
            conn_info = self._connections[user_id]
            
            for asset_id in asset_ids:
                # 从资产订阅映射中移除
                if asset_id in self._asset_subscriptions:
                    self._asset_subscriptions[asset_id].discard(user_id)
                    if not self._asset_subscriptions[asset_id]:
                        del self._asset_subscriptions[asset_id]
                
                # 从用户订阅列表中移除
                conn_info.subscribed_assets.discard(asset_id)
            
            conn_info.update_activity()
            
        logger.info(f"取消订阅: user_id={user_id}, assets={asset_ids}")
        return True
    
    def get_asset_subscribers(self, asset_id: int) -> Set[int]:
        """
        获取资产的订阅者列表
        
        Args:
            asset_id: 资产ID
            
        Returns:
            Set[int]: 订阅该资产的用户ID集合
        """
        return self._asset_subscriptions.get(asset_id, set()).copy()
    
    def get_user_subscriptions(self, user_id: int) -> Set[int]:
        """
        获取用户订阅的资产列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            Set[int]: 用户订阅的资产ID集合
        """
        if user_id in self._connections:
            return self._connections[user_id].subscribed_assets.copy()
        return set()
    
    def is_connected(self, user_id: int) -> bool:
        """
        检查用户是否已连接
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否已连接
        """
        return user_id in self._connections
    
    async def push_to_user(self, user_id: int, message: Dict[str, Any]) -> bool:
        """
        向指定用户推送消息
        
        Args:
            user_id: 用户ID
            message: 消息内容
            
        Returns:
            bool: 推送是否成功
        """
        if user_id not in self._connections:
            return False
        
        conn_info = self._connections[user_id]
        try:
            await self._send_message(conn_info.websocket, message)
            conn_info.update_activity()
            return True
        except Exception as e:
            logger.error(f"推送失败: user_id={user_id}, error={e}")
            # 连接可能已断开，清理连接
            await self.disconnect(user_id)
            return False
    
    async def push_to_asset_subscribers(self, asset_id: int, data: Dict[str, Any]) -> int:
        """
        向资产订阅者推送数据
        
        Args:
            asset_id: 资产ID
            data: 数据内容
            
        Returns:
            int: 成功推送的用户数
        """
        subscribers = self.get_asset_subscribers(asset_id)
        if not subscribers:
            return 0
        
        message = {
            "type": "asset_data",
            "asset_id": asset_id,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "quality": data.get("quality", "good")
        }
        
        success_count = 0
        failed_users = []
        
        for user_id in subscribers:
            if await self.push_to_user(user_id, message):
                success_count += 1
            else:
                failed_users.append(user_id)
        
        if failed_users:
            logger.warning(f"部分推送失败: asset_id={asset_id}, failed_users={failed_users}")
        
        return success_count
    
    async def push_alert(self, user_id: int, alert: Dict[str, Any]) -> bool:
        """
        推送告警通知
        
        Args:
            user_id: 用户ID
            alert: 告警内容
            
        Returns:
            bool: 推送是否成功
        """
        message = {
            "type": "alert",
            "alert": alert,
            "timestamp": datetime.now().isoformat()
        }
        return await self.push_to_user(user_id, message)
    
    async def broadcast(self, message: Dict[str, Any]) -> int:
        """
        广播消息给所有连接的用户
        
        Args:
            message: 消息内容
            
        Returns:
            int: 成功推送的用户数
        """
        success_count = 0
        user_ids = list(self._connections.keys())
        
        for user_id in user_ids:
            if await self.push_to_user(user_id, message):
                success_count += 1
        
        return success_count
    
    async def _send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """
        发送消息到WebSocket
        
        Args:
            websocket: WebSocket连接
            message: 消息内容
        """
        await websocket.send_text(json.dumps(message, ensure_ascii=False))
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        获取连接统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            "active_connections": self.active_connections,
            "total_subscriptions": self.total_subscriptions,
            "subscribed_assets": len(self._asset_subscriptions),
            "connections": [
                {
                    "user_id": conn.user_id,
                    "connected_at": conn.connected_at.isoformat(),
                    "last_activity": conn.last_activity.isoformat(),
                    "subscribed_assets_count": len(conn.subscribed_assets)
                }
                for conn in self._connections.values()
            ]
        }


# 全局连接管理器实例
connection_manager = ConnectionManager()
