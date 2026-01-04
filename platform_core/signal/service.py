"""
信号业务服务层

提供信号定义管理的核心业务逻辑，封装Repository操作并添加业务规则。
"""
from typing import Optional, List, Tuple, Dict, Any

from .models import SignalDefinitionDTO
from .repository import SignalRepository


class SignalService:
    """
    信号管理服务
    
    提供信号定义的业务逻辑处理，包括CRUD操作、分组管理和统计功能。
    """
    
    # 有效的数据类型
    VALID_DATA_TYPES = ["float", "int", "bool", "string", "double", "bigint"]
    
    # 有效的聚合方法
    VALID_AGGREGATION_METHODS = ["avg", "sum", "max", "min", "count", "first", "last"]
    
    def __init__(self):
        self.repo = SignalRepository()
    
    async def get_signal(self, signal_id: int) -> Optional[SignalDefinitionDTO]:
        """
        获取单个信号定义
        
        Args:
            signal_id: 信号定义ID
            
        Returns:
            SignalDefinitionDTO对象或None
        """
        signal = await self.repo.get_by_id(signal_id)
        if not signal:
            return None
        return SignalDefinitionDTO.from_orm(signal)
    
    async def get_signal_by_code(
        self,
        category_id: int,
        code: str
    ) -> Optional[SignalDefinitionDTO]:
        """
        根据类别ID和编码获取信号定义
        
        Args:
            category_id: 资产类别ID
            code: 信号编码
            
        Returns:
            SignalDefinitionDTO对象或None
        """
        signal = await self.repo.get_by_code(category_id, code)
        if not signal:
            return None
        return SignalDefinitionDTO.from_orm(signal)
    
    async def get_signals_by_category(
        self,
        category_id: int,
        is_active: bool = True
    ) -> List[SignalDefinitionDTO]:
        """
        获取指定类别下的所有信号定义
        
        Args:
            category_id: 资产类别ID
            is_active: 是否只获取激活的信号
            
        Returns:
            SignalDefinitionDTO列表
        """
        signals = await self.repo.get_by_category(category_id, is_active)
        return [SignalDefinitionDTO.from_orm(s) for s in signals]
    
    async def get_stored_signals(self, category_id: int) -> List[SignalDefinitionDTO]:
        """
        获取指定类别下需要存储的信号定义
        
        Args:
            category_id: 资产类别ID
            
        Returns:
            SignalDefinitionDTO列表
        """
        signals = await self.repo.get_stored_signals(category_id)
        return [SignalDefinitionDTO.from_orm(s) for s in signals]
    
    async def get_realtime_signals(self, category_id: int) -> List[SignalDefinitionDTO]:
        """
        获取指定类别下需要实时监控的信号定义
        
        Args:
            category_id: 资产类别ID
            
        Returns:
            SignalDefinitionDTO列表
        """
        signals = await self.repo.get_realtime_signals(category_id)
        return [SignalDefinitionDTO.from_orm(s) for s in signals]
    
    async def get_feature_signals(self, category_id: int) -> List[SignalDefinitionDTO]:
        """
        获取指定类别下用于特征工程的信号定义
        
        Args:
            category_id: 资产类别ID
            
        Returns:
            SignalDefinitionDTO列表
        """
        signals = await self.repo.get_feature_signals(category_id)
        return [SignalDefinitionDTO.from_orm(s) for s in signals]
    
    async def get_alarm_signals(self, category_id: int) -> List[SignalDefinitionDTO]:
        """
        获取指定类别下启用报警的信号定义
        
        Args:
            category_id: 资产类别ID
            
        Returns:
            SignalDefinitionDTO列表
        """
        signals = await self.repo.get_alarm_signals(category_id)
        return [SignalDefinitionDTO.from_orm(s) for s in signals]
    
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
    ) -> Tuple[List[SignalDefinitionDTO], int]:
        """
        分页查询信号定义列表
        
        Args:
            category_id: 资产类别ID筛选
            is_stored: 是否存储筛选
            is_realtime: 是否实时监控筛选
            is_feature: 是否特征工程筛选
            is_active: 激活状态筛选
            field_group: 字段分组筛选
            search: 搜索关键词
            page: 页码
            page_size: 每页数量
            
        Returns:
            (SignalDefinitionDTO列表, 总数)
        """
        signals, total = await self.repo.list_signals(
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
        return [SignalDefinitionDTO.from_orm(s) for s in signals], total
    
    async def get_signals_by_group(
        self,
        category_id: int,
        field_group: str,
        is_active: bool = True
    ) -> List[SignalDefinitionDTO]:
        """
        获取指定类别和分组下的信号定义
        
        Args:
            category_id: 资产类别ID
            field_group: 字段分组
            is_active: 是否只获取激活的信号
            
        Returns:
            SignalDefinitionDTO列表
        """
        signals = await self.repo.get_by_group(category_id, field_group, is_active)
        return [SignalDefinitionDTO.from_orm(s) for s in signals]
    
    async def get_visible_signals(self, category_id: int) -> List[SignalDefinitionDTO]:
        """
        获取指定类别下默认可见的信号定义
        
        Args:
            category_id: 资产类别ID
            
        Returns:
            SignalDefinitionDTO列表
        """
        signals = await self.repo.get_visible_signals(category_id)
        return [SignalDefinitionDTO.from_orm(s) for s in signals]
    
    async def create_signal(self, data: Dict[str, Any]) -> SignalDefinitionDTO:
        """
        创建信号定义
        
        Args:
            data: 信号定义数据字典
            
        Returns:
            创建的SignalDefinitionDTO对象
            
        Raises:
            ValueError: 如果信号编码已存在或数据类型无效
        """
        category_id = data.get("category_id")
        code = data.get("code", "")
        
        # 验证类别存在
        if not category_id:
            raise ValueError("资产类别ID不能为空")
        
        # 验证编码唯一性（在同一类别下）
        existing = await self.repo.get_by_code(category_id, code)
        if existing:
            raise ValueError(f"信号编码 '{code}' 在该类别下已存在")
        
        # 验证数据类型
        data_type = data.get("data_type", "float")
        if data_type not in self.VALID_DATA_TYPES:
            raise ValueError(f"无效的数据类型 '{data_type}'，有效值为: {self.VALID_DATA_TYPES}")
        
        # 验证聚合方法
        aggregation_method = data.get("aggregation_method")
        if aggregation_method and aggregation_method not in self.VALID_AGGREGATION_METHODS:
            raise ValueError(f"无效的聚合方法 '{aggregation_method}'，有效值为: {self.VALID_AGGREGATION_METHODS}")
        
        signal = await self.repo.create(data)
        return SignalDefinitionDTO.from_orm(signal)
    
    async def update_signal(
        self,
        signal_id: int,
        data: Dict[str, Any]
    ) -> Optional[SignalDefinitionDTO]:
        """
        更新信号定义
        
        Args:
            signal_id: 信号定义ID
            data: 更新数据字典
            
        Returns:
            更新后的SignalDefinitionDTO对象或None
            
        Raises:
            ValueError: 如果新编码已被其他信号使用或数据类型无效
        """
        # 获取原信号信息
        original = await self.repo.get_by_id(signal_id)
        if not original:
            return None
        
        # 如果更新编码，验证唯一性
        if "code" in data:
            category_id = data.get("category_id", original.category_id)
            existing = await self.repo.get_by_code(category_id, data["code"])
            if existing and existing.id != signal_id:
                raise ValueError(f"信号编码 '{data['code']}' 在该类别下已被其他信号使用")
        
        # 验证数据类型
        if "data_type" in data:
            if data["data_type"] not in self.VALID_DATA_TYPES:
                raise ValueError(f"无效的数据类型 '{data['data_type']}'，有效值为: {self.VALID_DATA_TYPES}")
        
        # 验证聚合方法
        if "aggregation_method" in data and data["aggregation_method"]:
            if data["aggregation_method"] not in self.VALID_AGGREGATION_METHODS:
                raise ValueError(f"无效的聚合方法 '{data['aggregation_method']}'，有效值为: {self.VALID_AGGREGATION_METHODS}")
        
        signal = await self.repo.update(signal_id, data)
        if not signal:
            return None
        return SignalDefinitionDTO.from_orm(signal)
    
    async def delete_signal(self, signal_id: int) -> bool:
        """
        删除信号定义
        
        Args:
            signal_id: 信号定义ID
            
        Returns:
            是否删除成功
        """
        return await self.repo.delete(signal_id)
    
    async def toggle_signal_active(
        self,
        signal_id: int,
        is_active: bool
    ) -> Optional[SignalDefinitionDTO]:
        """
        切换信号定义的激活状态
        
        Args:
            signal_id: 信号定义ID
            is_active: 新的激活状态
            
        Returns:
            更新后的SignalDefinitionDTO对象或None
        """
        return await self.update_signal(signal_id, {"is_active": is_active})
    
    async def toggle_signal_stored(
        self,
        signal_id: int,
        is_stored: bool
    ) -> Optional[SignalDefinitionDTO]:
        """
        切换信号定义的存储状态
        
        Args:
            signal_id: 信号定义ID
            is_stored: 新的存储状态
            
        Returns:
            更新后的SignalDefinitionDTO对象或None
        """
        return await self.update_signal(signal_id, {"is_stored": is_stored})
    
    async def toggle_signal_realtime(
        self,
        signal_id: int,
        is_realtime: bool
    ) -> Optional[SignalDefinitionDTO]:
        """
        切换信号定义的实时监控状态
        
        Args:
            signal_id: 信号定义ID
            is_realtime: 新的实时监控状态
            
        Returns:
            更新后的SignalDefinitionDTO对象或None
        """
        return await self.update_signal(signal_id, {"is_realtime": is_realtime})
    
    async def toggle_signal_feature(
        self,
        signal_id: int,
        is_feature: bool
    ) -> Optional[SignalDefinitionDTO]:
        """
        切换信号定义的特征工程状态
        
        Args:
            signal_id: 信号定义ID
            is_feature: 新的特征工程状态
            
        Returns:
            更新后的SignalDefinitionDTO对象或None
        """
        return await self.update_signal(signal_id, {"is_feature": is_feature})
    
    async def update_alarm_threshold(
        self,
        signal_id: int,
        alarm_threshold: Dict[str, Any],
        is_alarm_enabled: bool = True
    ) -> Optional[SignalDefinitionDTO]:
        """
        更新信号定义的报警阈值
        
        Args:
            signal_id: 信号定义ID
            alarm_threshold: 报警阈值配置
            is_alarm_enabled: 是否启用报警
            
        Returns:
            更新后的SignalDefinitionDTO对象或None
        """
        return await self.update_signal(signal_id, {
            "alarm_threshold": alarm_threshold,
            "is_alarm_enabled": is_alarm_enabled
        })
    
    async def get_signal_groups(self, category_id: int) -> List[str]:
        """
        获取指定类别下的所有字段分组
        
        Args:
            category_id: 资产类别ID
            
        Returns:
            字段分组列表
        """
        return await self.repo.get_groups(category_id)
    
    async def count_signals(
        self,
        category_id: int,
        is_active: bool = True
    ) -> int:
        """
        统计指定类别下的信号数量
        
        Args:
            category_id: 资产类别ID
            is_active: 是否只统计激活的信号
            
        Returns:
            信号数量
        """
        return await self.repo.count_by_category(category_id, is_active)
    
    async def update_sort_order(self, signal_id: int, sort_order: int) -> bool:
        """
        更新信号定义的排序
        
        Args:
            signal_id: 信号定义ID
            sort_order: 新的排序值
            
        Returns:
            是否更新成功
        """
        return await self.repo.update_sort_order(signal_id, sort_order)
    
    async def batch_update_sort_order(
        self,
        updates: List[Dict[str, int]]
    ) -> int:
        """
        批量更新信号定义的排序
        
        Args:
            updates: 更新列表，每项包含 {"id": signal_id, "sort_order": new_order}
            
        Returns:
            更新的记录数
        """
        return await self.repo.batch_update_sort_order(updates)
    
    async def get_signals_grouped(
        self,
        category_id: int
    ) -> Dict[str, List[SignalDefinitionDTO]]:
        """
        获取指定类别下按分组组织的信号定义
        
        Args:
            category_id: 资产类别ID
            
        Returns:
            按分组组织的信号定义字典
        """
        signals = await self.get_signals_by_category(category_id)
        
        grouped = {}
        for signal in signals:
            group = signal.field_group or "default"
            if group not in grouped:
                grouped[group] = []
            grouped[group].append(signal)
        
        return grouped
