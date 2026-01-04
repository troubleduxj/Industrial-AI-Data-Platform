"""
元数据注册表

提供元数据的统一注册和查询接口。

迁移说明:
- 从 platform_v2.metadata.metadata_registry 迁移到 platform_core.metadata.metadata_registry
- 保持所有API接口不变
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MetadataRegistry:
    """
    元数据注册表
    
    提供元数据的缓存和快速查询功能。
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not MetadataRegistry._initialized:
            self._categories_cache: Dict[str, Dict[str, Any]] = {}
            self._signals_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}
            self._last_refresh: Optional[datetime] = None
            self._cache_ttl_seconds = 300  # 5分钟缓存
            MetadataRegistry._initialized = True
    
    async def refresh_cache(self, force: bool = False) -> None:
        """
        刷新元数据缓存
        
        Args:
            force: 是否强制刷新
        """
        if not force and self._last_refresh:
            elapsed = (datetime.now() - self._last_refresh).total_seconds()
            if elapsed < self._cache_ttl_seconds:
                return
        
        from app.models.platform_upgrade import AssetCategory, SignalDefinition
        
        # 刷新类别缓存
        categories = await AssetCategory.filter(is_active=True).all()
        self._categories_cache = {
            cat.code: {
                "id": cat.id,
                "code": cat.code,
                "name": cat.name,
                "tdengine_database": cat.tdengine_database,
                "tdengine_stable_prefix": cat.tdengine_stable_prefix,
                "industry": cat.industry,
                "config": cat.config
            }
            for cat in categories
        }
        
        # 刷新信号缓存
        self._signals_cache = {}
        for cat_code in self._categories_cache:
            cat_id = self._categories_cache[cat_code]["id"]
            signals = await SignalDefinition.filter(
                category_id=cat_id,
                is_active=True
            ).all()
            
            self._signals_cache[cat_code] = {
                sig.code: {
                    "id": sig.id,
                    "code": sig.code,
                    "name": sig.name,
                    "data_type": sig.data_type,
                    "unit": sig.unit,
                    "is_stored": sig.is_stored,
                    "is_realtime": sig.is_realtime,
                    "is_feature": sig.is_feature,
                    "value_range": sig.value_range,
                    "alarm_threshold": sig.alarm_threshold
                }
                for sig in signals
            }
        
        self._last_refresh = datetime.now()
        logger.info(f"元数据缓存刷新完成: {len(self._categories_cache)} 个类别")
    
    async def get_category(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取类别元数据
        
        Args:
            code: 类别编码
            
        Returns:
            Dict: 类别元数据，如果不存在返回None
        """
        await self.refresh_cache()
        return self._categories_cache.get(code)
    
    async def get_all_categories(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有类别元数据
        
        Returns:
            Dict: 所有类别元数据
        """
        await self.refresh_cache()
        return self._categories_cache.copy()
    
    async def get_signal(self, category_code: str, signal_code: str) -> Optional[Dict[str, Any]]:
        """
        获取信号元数据
        
        Args:
            category_code: 类别编码
            signal_code: 信号编码
            
        Returns:
            Dict: 信号元数据，如果不存在返回None
        """
        await self.refresh_cache()
        category_signals = self._signals_cache.get(category_code, {})
        return category_signals.get(signal_code)
    
    async def get_signals_by_category(self, category_code: str) -> Dict[str, Dict[str, Any]]:
        """
        获取类别下的所有信号元数据
        
        Args:
            category_code: 类别编码
            
        Returns:
            Dict: 信号元数据字典
        """
        await self.refresh_cache()
        return self._signals_cache.get(category_code, {}).copy()
    
    async def get_stored_signals(self, category_code: str) -> List[Dict[str, Any]]:
        """
        获取需要存储的信号列表
        
        Args:
            category_code: 类别编码
            
        Returns:
            List: 需要存储的信号列表
        """
        signals = await self.get_signals_by_category(category_code)
        return [s for s in signals.values() if s.get("is_stored")]
    
    async def get_realtime_signals(self, category_code: str) -> List[Dict[str, Any]]:
        """
        获取需要实时监控的信号列表
        
        Args:
            category_code: 类别编码
            
        Returns:
            List: 需要实时监控的信号列表
        """
        signals = await self.get_signals_by_category(category_code)
        return [s for s in signals.values() if s.get("is_realtime")]
    
    async def get_feature_signals(self, category_code: str) -> List[Dict[str, Any]]:
        """
        获取用于特征工程的信号列表
        
        Args:
            category_code: 类别编码
            
        Returns:
            List: 用于特征工程的信号列表
        """
        signals = await self.get_signals_by_category(category_code)
        return [s for s in signals.values() if s.get("is_feature")]
    
    def invalidate_cache(self) -> None:
        """使缓存失效"""
        self._last_refresh = None
        logger.info("元数据缓存已失效")
    
    def set_cache_ttl(self, seconds: int) -> None:
        """
        设置缓存TTL
        
        Args:
            seconds: 缓存有效期（秒）
        """
        self._cache_ttl_seconds = seconds


# 全局单例
metadata_registry = MetadataRegistry()
