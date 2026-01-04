"""
平台服务适配层

提供API层与platform_core之间的薄封装，统一服务调用路径。
此模块作为app/services的入口点，将所有核心业务逻辑委托给platform_core。

Requirements: 7.4 - 服务调用路径统一
"""
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# =====================================================
# 资产服务适配器
# =====================================================

class AssetServiceAdapter:
    """
    资产服务适配器
    
    封装platform_core.asset.AssetService，提供API层友好的接口。
    """
    
    def __init__(self):
        self._service = None
    
    @property
    def service(self):
        """延迟加载platform_core服务"""
        if self._service is None:
            from platform_core.asset.service import AssetService
            self._service = AssetService()
        return self._service
    
    async def get_asset(self, asset_id: int) -> Optional[Dict[str, Any]]:
        """获取单个资产"""
        dto = await self.service.get_asset(asset_id)
        return dto.to_dict() if dto else None
    
    async def get_asset_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """根据编码获取资产"""
        dto = await self.service.get_asset_by_code(code)
        return dto.to_dict() if dto else None
    
    async def list_assets(
        self,
        category_id: Optional[int] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
        location: Optional[str] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """分页查询资产列表"""
        assets, total = await self.service.list_assets(
            category_id=category_id,
            status=status,
            is_active=is_active,
            location=location,
            department=department,
            search=search,
            page=page,
            page_size=page_size
        )
        return [a.to_dict() for a in assets], total
    
    async def create_asset(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建资产"""
        dto = await self.service.create_asset(data)
        return dto.to_dict()
    
    async def update_asset(self, asset_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新资产"""
        dto = await self.service.update_asset(asset_id, data)
        return dto.to_dict() if dto else None
    
    async def delete_asset(self, asset_id: int) -> bool:
        """删除资产"""
        return await self.service.delete_asset(asset_id)
    
    async def update_asset_status(self, asset_id: int, status: str) -> Optional[Dict[str, Any]]:
        """更新资产状态"""
        dto = await self.service.update_asset_status(asset_id, status)
        return dto.to_dict() if dto else None
    
    async def get_status_statistics(self, category_id: Optional[int] = None) -> Dict[str, int]:
        """获取资产状态统计"""
        return await self.service.get_status_statistics(category_id)


class AssetCategoryServiceAdapter:
    """
    资产类别服务适配器
    
    封装platform_core.asset.AssetCategoryService，提供API层友好的接口。
    """
    
    def __init__(self):
        self._service = None
    
    @property
    def service(self):
        """延迟加载platform_core服务"""
        if self._service is None:
            from platform_core.asset.service import AssetCategoryService
            self._service = AssetCategoryService()
        return self._service
    
    async def get_category(self, category_id: int) -> Optional[Dict[str, Any]]:
        """获取单个资产类别"""
        dto = await self.service.get_category(category_id)
        return dto.to_dict() if dto else None
    
    async def get_category_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """根据编码获取资产类别"""
        dto = await self.service.get_category_by_code(code)
        return dto.to_dict() if dto else None
    
    async def list_categories(
        self,
        industry: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """分页查询资产类别列表"""
        categories, total = await self.service.list_categories(
            industry=industry,
            is_active=is_active,
            search=search,
            page=page,
            page_size=page_size
        )
        return [c.to_dict() for c in categories], total
    
    async def get_all_active_categories(self) -> List[Dict[str, Any]]:
        """获取所有激活的资产类别"""
        categories = await self.service.get_all_active_categories()
        return [c.to_dict() for c in categories]
    
    async def create_category(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建资产类别"""
        dto = await self.service.create_category(data)
        return dto.to_dict()
    
    async def update_category(self, category_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新资产类别"""
        dto = await self.service.update_category(category_id, data)
        return dto.to_dict() if dto else None
    
    async def delete_category(self, category_id: int) -> bool:
        """删除资产类别"""
        return await self.service.delete_category(category_id)


# =====================================================
# 信号服务适配器
# =====================================================

class SignalServiceAdapter:
    """
    信号服务适配器
    
    封装platform_core.signal.SignalService，提供API层友好的接口。
    """
    
    def __init__(self):
        self._service = None
    
    @property
    def service(self):
        """延迟加载platform_core服务"""
        if self._service is None:
            from platform_core.signal.service import SignalService
            self._service = SignalService()
        return self._service
    
    async def get_signal(self, signal_id: int) -> Optional[Dict[str, Any]]:
        """获取单个信号定义"""
        dto = await self.service.get_signal(signal_id)
        return dto.to_dict() if dto else None
    
    async def get_signal_by_code(self, category_id: int, code: str) -> Optional[Dict[str, Any]]:
        """根据类别ID和编码获取信号定义"""
        dto = await self.service.get_signal_by_code(category_id, code)
        return dto.to_dict() if dto else None
    
    async def get_signals_by_category(
        self,
        category_id: int,
        is_active: bool = True
    ) -> List[Dict[str, Any]]:
        """获取指定类别下的所有信号定义"""
        signals = await self.service.get_signals_by_category(category_id, is_active)
        return [s.to_dict() for s in signals]
    
    async def get_stored_signals(self, category_id: int) -> List[Dict[str, Any]]:
        """获取指定类别下需要存储的信号定义"""
        signals = await self.service.get_stored_signals(category_id)
        return [s.to_dict() for s in signals]
    
    async def get_realtime_signals(self, category_id: int) -> List[Dict[str, Any]]:
        """获取指定类别下需要实时监控的信号定义"""
        signals = await self.service.get_realtime_signals(category_id)
        return [s.to_dict() for s in signals]
    
    async def list_signals(
        self,
        category_id: Optional[int] = None,
        is_stored: Optional[bool] = None,
        is_realtime: Optional[bool] = None,
        is_feature: Optional[bool] = None,
        is_active: Optional[bool] = None,
        field_group: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """分页查询信号定义列表"""
        signals, total = await self.service.list_signals(
            category_id=category_id,
            is_stored=is_stored,
            is_realtime=is_realtime,
            is_feature=is_feature,
            is_active=is_active,
            field_group=field_group,
            search=search,
            page=page,
            page_size=page_size
        )
        return [s.to_dict() for s in signals], total
    
    async def create_signal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建信号定义"""
        dto = await self.service.create_signal(data)
        return dto.to_dict()
    
    async def update_signal(self, signal_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新信号定义"""
        dto = await self.service.update_signal(signal_id, data)
        return dto.to_dict() if dto else None
    
    async def delete_signal(self, signal_id: int) -> bool:
        """删除信号定义"""
        return await self.service.delete_signal(signal_id)


# =====================================================
# TDengine服务适配器
# =====================================================

class TDengineServiceAdapter:
    """
    TDengine服务适配器
    
    封装platform_core.timeseries，提供API层友好的接口。
    """
    
    def __init__(self, server_name: Optional[str] = None):
        self.server_name = server_name
        self._client = None
        self._schema_manager = None
    
    @property
    def client(self):
        """延迟加载TDengine客户端"""
        if self._client is None:
            from platform_core.timeseries import get_tdengine_client
            self._client = get_tdengine_client(self.server_name)
        return self._client
    
    @property
    def schema_manager(self):
        """延迟加载Schema管理器"""
        if self._schema_manager is None:
            from platform_core.timeseries import schema_manager
            self._schema_manager = schema_manager
        return self._schema_manager
    
    async def health_check(self) -> Dict[str, Any]:
        """执行健康检查"""
        return await self.client.health_check()
    
    async def execute_query(self, sql: str, database: Optional[str] = None) -> Dict[str, Any]:
        """执行查询"""
        result = await self.client.query(sql, database)
        return {"data": result}
    
    async def get_databases(self) -> List[str]:
        """获取数据库列表"""
        return await self.client.get_databases()
    
    async def get_tables(self, database: str) -> List[str]:
        """获取表列表"""
        return await self.client.get_tables(database)
    
    async def sync_category_schema(self, category_code: str) -> bool:
        """同步资产类别的TDengine Schema"""
        return await self.schema_manager.sync_category_schema(category_code)
    
    async def create_child_table(
        self,
        stable_name: str,
        asset_code: str,
        asset_id: int,
        database: str = "devicemonitor"
    ) -> bool:
        """为资产创建子表"""
        return await self.schema_manager.create_child_table(
            stable_name, asset_code, asset_id, database
        )
    
    async def sync_all_categories(self) -> Dict[str, bool]:
        """同步所有激活类别的Schema"""
        return await self.schema_manager.sync_all_categories()
    
    async def get_schema_history(self, category_code: str) -> List[Dict[str, Any]]:
        """获取Schema变更历史"""
        return await self.schema_manager.get_schema_history(category_code)


# =====================================================
# 元数据服务适配器
# =====================================================

class MetadataServiceAdapter:
    """
    元数据服务适配器
    
    封装platform_core.metadata，提供API层友好的接口。
    """
    
    def __init__(self):
        self._registry = None
    
    @property
    def registry(self):
        """延迟加载元数据注册表"""
        if self._registry is None:
            from platform_core.metadata import metadata_registry
            self._registry = metadata_registry
        return self._registry
    
    async def get_category(self, code: str) -> Optional[Dict[str, Any]]:
        """获取类别元数据"""
        return await self.registry.get_category(code)
    
    async def get_all_categories(self) -> Dict[str, Dict[str, Any]]:
        """获取所有类别元数据"""
        return await self.registry.get_all_categories()
    
    async def get_signal(self, category_code: str, signal_code: str) -> Optional[Dict[str, Any]]:
        """获取信号元数据"""
        return await self.registry.get_signal(category_code, signal_code)
    
    async def get_signals_by_category(self, category_code: str) -> Dict[str, Dict[str, Any]]:
        """获取类别下的所有信号元数据"""
        return await self.registry.get_signals_by_category(category_code)
    
    async def refresh_cache(self, force: bool = False) -> None:
        """刷新元数据缓存"""
        await self.registry.refresh_cache(force)
    
    def invalidate_cache(self) -> None:
        """使缓存失效"""
        self.registry.invalidate_cache()


# =====================================================
# 全局服务实例
# =====================================================

# 资产服务
asset_service = AssetServiceAdapter()
asset_category_service = AssetCategoryServiceAdapter()

# 信号服务
signal_service = SignalServiceAdapter()

# TDengine服务
tdengine_service = TDengineServiceAdapter()

# 元数据服务
metadata_service = MetadataServiceAdapter()


# =====================================================
# 便捷函数
# =====================================================

def get_asset_service() -> AssetServiceAdapter:
    """获取资产服务实例"""
    return asset_service


def get_asset_category_service() -> AssetCategoryServiceAdapter:
    """获取资产类别服务实例"""
    return asset_category_service


def get_signal_service() -> SignalServiceAdapter:
    """获取信号服务实例"""
    return signal_service


def get_tdengine_service(server_name: Optional[str] = None) -> TDengineServiceAdapter:
    """获取TDengine服务实例"""
    if server_name:
        return TDengineServiceAdapter(server_name)
    return tdengine_service


def get_metadata_service() -> MetadataServiceAdapter:
    """获取元数据服务实例"""
    return metadata_service
