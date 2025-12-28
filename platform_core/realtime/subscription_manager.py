"""
订阅管理器

实现资产订阅和取消订阅功能，支持批量订阅。

需求: 3.3 - 当客户端订阅特定资产时，平台应只推送该资产的相关数据
需求: 3.5 - 平台应支持批量订阅多个资产的实时数据
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Set, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SubscriptionType(str, Enum):
    """订阅类型"""
    ASSET_DATA = "asset_data"       # 资产数据
    ALERT = "alert"                 # 告警
    PREDICTION = "prediction"       # 预测结果
    ALL = "all"                     # 所有类型


@dataclass
class Subscription:
    """订阅信息"""
    user_id: int
    asset_id: int
    subscription_type: SubscriptionType = SubscriptionType.ASSET_DATA
    created_at: datetime = field(default_factory=datetime.now)
    filters: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def key(self) -> str:
        """生成订阅唯一键"""
        return f"{self.user_id}:{self.asset_id}:{self.subscription_type.value}"


class SubscriptionManager:
    """
    订阅管理器
    
    负责管理用户对资产的订阅关系，支持：
    - 单个资产订阅/取消订阅
    - 批量资产订阅/取消订阅
    - 订阅类型过滤
    - 订阅查询
    """
    
    def __init__(self):
        # 订阅键 -> 订阅信息
        self._subscriptions: Dict[str, Subscription] = {}
        # 用户ID -> 订阅键集合
        self._user_subscriptions: Dict[int, Set[str]] = {}
        # 资产ID -> 订阅键集合
        self._asset_subscriptions: Dict[int, Set[str]] = {}
        # 锁
        self._lock = asyncio.Lock()
    
    async def subscribe(
        self,
        user_id: int,
        asset_id: int,
        subscription_type: SubscriptionType = SubscriptionType.ASSET_DATA,
        filters: Optional[Dict[str, Any]] = None
    ) -> Subscription:
        """
        订阅单个资产
        
        Args:
            user_id: 用户ID
            asset_id: 资产ID
            subscription_type: 订阅类型
            filters: 过滤条件
            
        Returns:
            Subscription: 订阅信息
        """
        subscription = Subscription(
            user_id=user_id,
            asset_id=asset_id,
            subscription_type=subscription_type,
            filters=filters or {}
        )
        
        async with self._lock:
            key = subscription.key
            
            # 添加到订阅映射
            self._subscriptions[key] = subscription
            
            # 添加到用户订阅索引
            if user_id not in self._user_subscriptions:
                self._user_subscriptions[user_id] = set()
            self._user_subscriptions[user_id].add(key)
            
            # 添加到资产订阅索引
            if asset_id not in self._asset_subscriptions:
                self._asset_subscriptions[asset_id] = set()
            self._asset_subscriptions[asset_id].add(key)
        
        logger.info(f"订阅成功: user={user_id}, asset={asset_id}, type={subscription_type.value}")
        return subscription
    
    async def subscribe_batch(
        self,
        user_id: int,
        asset_ids: List[int],
        subscription_type: SubscriptionType = SubscriptionType.ASSET_DATA,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Subscription]:
        """
        批量订阅多个资产
        
        Args:
            user_id: 用户ID
            asset_ids: 资产ID列表
            subscription_type: 订阅类型
            filters: 过滤条件
            
        Returns:
            List[Subscription]: 订阅信息列表
        """
        subscriptions = []
        
        for asset_id in asset_ids:
            subscription = await self.subscribe(
                user_id=user_id,
                asset_id=asset_id,
                subscription_type=subscription_type,
                filters=filters
            )
            subscriptions.append(subscription)
        
        logger.info(f"批量订阅成功: user={user_id}, assets={asset_ids}, count={len(subscriptions)}")
        return subscriptions
    
    async def unsubscribe(
        self,
        user_id: int,
        asset_id: int,
        subscription_type: Optional[SubscriptionType] = None
    ) -> bool:
        """
        取消订阅单个资产
        
        Args:
            user_id: 用户ID
            asset_id: 资产ID
            subscription_type: 订阅类型（None表示取消所有类型）
            
        Returns:
            bool: 是否成功取消
        """
        async with self._lock:
            removed = False
            
            if subscription_type:
                # 取消特定类型的订阅
                key = f"{user_id}:{asset_id}:{subscription_type.value}"
                if key in self._subscriptions:
                    self._remove_subscription(key)
                    removed = True
            else:
                # 取消所有类型的订阅
                for sub_type in SubscriptionType:
                    key = f"{user_id}:{asset_id}:{sub_type.value}"
                    if key in self._subscriptions:
                        self._remove_subscription(key)
                        removed = True
        
        if removed:
            logger.info(f"取消订阅: user={user_id}, asset={asset_id}")
        return removed
    
    async def unsubscribe_batch(
        self,
        user_id: int,
        asset_ids: List[int],
        subscription_type: Optional[SubscriptionType] = None
    ) -> int:
        """
        批量取消订阅
        
        Args:
            user_id: 用户ID
            asset_ids: 资产ID列表
            subscription_type: 订阅类型
            
        Returns:
            int: 成功取消的订阅数
        """
        count = 0
        for asset_id in asset_ids:
            if await self.unsubscribe(user_id, asset_id, subscription_type):
                count += 1
        
        logger.info(f"批量取消订阅: user={user_id}, count={count}")
        return count
    
    async def unsubscribe_all(self, user_id: int) -> int:
        """
        取消用户的所有订阅
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 取消的订阅数
        """
        async with self._lock:
            if user_id not in self._user_subscriptions:
                return 0
            
            keys = list(self._user_subscriptions[user_id])
            for key in keys:
                self._remove_subscription(key)
            
            count = len(keys)
        
        logger.info(f"取消所有订阅: user={user_id}, count={count}")
        return count
    
    def _remove_subscription(self, key: str):
        """
        移除订阅（内部方法，需在锁内调用）
        
        Args:
            key: 订阅键
        """
        if key not in self._subscriptions:
            return
        
        subscription = self._subscriptions[key]
        user_id = subscription.user_id
        asset_id = subscription.asset_id
        
        # 从订阅映射中移除
        del self._subscriptions[key]
        
        # 从用户索引中移除
        if user_id in self._user_subscriptions:
            self._user_subscriptions[user_id].discard(key)
            if not self._user_subscriptions[user_id]:
                del self._user_subscriptions[user_id]
        
        # 从资产索引中移除
        if asset_id in self._asset_subscriptions:
            self._asset_subscriptions[asset_id].discard(key)
            if not self._asset_subscriptions[asset_id]:
                del self._asset_subscriptions[asset_id]
    
    def get_user_subscriptions(self, user_id: int) -> List[Subscription]:
        """
        获取用户的所有订阅
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[Subscription]: 订阅列表
        """
        if user_id not in self._user_subscriptions:
            return []
        
        return [
            self._subscriptions[key]
            for key in self._user_subscriptions[user_id]
            if key in self._subscriptions
        ]
    
    def get_user_subscribed_assets(self, user_id: int) -> Set[int]:
        """
        获取用户订阅的资产ID集合
        
        Args:
            user_id: 用户ID
            
        Returns:
            Set[int]: 资产ID集合
        """
        subscriptions = self.get_user_subscriptions(user_id)
        return {sub.asset_id for sub in subscriptions}
    
    def get_asset_subscribers(
        self,
        asset_id: int,
        subscription_type: Optional[SubscriptionType] = None
    ) -> List[Subscription]:
        """
        获取资产的所有订阅者
        
        Args:
            asset_id: 资产ID
            subscription_type: 订阅类型过滤
            
        Returns:
            List[Subscription]: 订阅列表
        """
        if asset_id not in self._asset_subscriptions:
            return []
        
        subscriptions = [
            self._subscriptions[key]
            for key in self._asset_subscriptions[asset_id]
            if key in self._subscriptions
        ]
        
        if subscription_type:
            subscriptions = [
                sub for sub in subscriptions
                if sub.subscription_type == subscription_type or sub.subscription_type == SubscriptionType.ALL
            ]
        
        return subscriptions
    
    def get_asset_subscriber_ids(
        self,
        asset_id: int,
        subscription_type: Optional[SubscriptionType] = None
    ) -> Set[int]:
        """
        获取资产订阅者的用户ID集合
        
        Args:
            asset_id: 资产ID
            subscription_type: 订阅类型过滤
            
        Returns:
            Set[int]: 用户ID集合
        """
        subscriptions = self.get_asset_subscribers(asset_id, subscription_type)
        return {sub.user_id for sub in subscriptions}
    
    def is_subscribed(
        self,
        user_id: int,
        asset_id: int,
        subscription_type: Optional[SubscriptionType] = None
    ) -> bool:
        """
        检查用户是否订阅了指定资产
        
        Args:
            user_id: 用户ID
            asset_id: 资产ID
            subscription_type: 订阅类型
            
        Returns:
            bool: 是否已订阅
        """
        if subscription_type:
            key = f"{user_id}:{asset_id}:{subscription_type.value}"
            return key in self._subscriptions
        else:
            # 检查任意类型的订阅
            for sub_type in SubscriptionType:
                key = f"{user_id}:{asset_id}:{sub_type.value}"
                if key in self._subscriptions:
                    return True
            return False
    
    def should_receive_data(
        self,
        user_id: int,
        asset_id: int,
        data_type: str = "asset_data"
    ) -> bool:
        """
        检查用户是否应该接收指定资产的数据
        
        用于数据过滤，确保用户只收到订阅的资产数据
        
        Args:
            user_id: 用户ID
            asset_id: 资产ID
            data_type: 数据类型
            
        Returns:
            bool: 是否应该接收
        """
        # 映射数据类型到订阅类型
        type_mapping = {
            "asset_data": SubscriptionType.ASSET_DATA,
            "alert": SubscriptionType.ALERT,
            "prediction": SubscriptionType.PREDICTION
        }
        
        subscription_type = type_mapping.get(data_type, SubscriptionType.ASSET_DATA)
        
        # 检查是否订阅了特定类型或ALL类型
        return (
            self.is_subscribed(user_id, asset_id, subscription_type) or
            self.is_subscribed(user_id, asset_id, SubscriptionType.ALL)
        )
    
    def filter_subscribers_for_asset(
        self,
        asset_id: int,
        data_type: str = "asset_data"
    ) -> Set[int]:
        """
        过滤出应该接收指定资产数据的用户
        
        Args:
            asset_id: 资产ID
            data_type: 数据类型
            
        Returns:
            Set[int]: 应该接收数据的用户ID集合
        """
        type_mapping = {
            "asset_data": SubscriptionType.ASSET_DATA,
            "alert": SubscriptionType.ALERT,
            "prediction": SubscriptionType.PREDICTION
        }
        
        subscription_type = type_mapping.get(data_type, SubscriptionType.ASSET_DATA)
        
        # 获取订阅了特定类型的用户
        specific_subscribers = self.get_asset_subscriber_ids(asset_id, subscription_type)
        
        # 获取订阅了ALL类型的用户
        all_subscribers = self.get_asset_subscriber_ids(asset_id, SubscriptionType.ALL)
        
        return specific_subscribers | all_subscribers
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取订阅统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            "total_subscriptions": len(self._subscriptions),
            "total_users": len(self._user_subscriptions),
            "total_assets": len(self._asset_subscriptions),
            "subscriptions_by_type": {
                sub_type.value: sum(
                    1 for sub in self._subscriptions.values()
                    if sub.subscription_type == sub_type
                )
                for sub_type in SubscriptionType
            }
        }


# 全局订阅管理器实例
subscription_manager = SubscriptionManager()
