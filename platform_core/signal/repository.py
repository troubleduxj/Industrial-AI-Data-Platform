"""
信号数据访问层

提供信号定义的数据库操作，封装ORM查询逻辑。
"""
from typing import Optional, List, Tuple, Dict, Any


class SignalRepository:
    """
    信号定义数据仓库
    
    提供信号定义的CRUD操作和查询方法。
    """
    
    @staticmethod
    async def get_by_id(signal_id: int) -> Optional["SignalDefinition"]:
        """
        根据ID获取信号定义
        
        Args:
            signal_id: 信号定义ID
            
        Returns:
            SignalDefinition对象或None
        """
        from app.models.platform_upgrade import SignalDefinition
        return await SignalDefinition.get_or_none(id=signal_id).prefetch_related("category")
    
    @staticmethod
    async def get_by_code(category_id: int, code: str) -> Optional["SignalDefinition"]:
        """
        根据类别ID和编码获取信号定义
        
        Args:
            category_id: 资产类别ID
            code: 信号编码
            
        Returns:
            SignalDefinition对象或None
        """
        from app.models.platform_upgrade import SignalDefinition
        return await SignalDefinition.get_or_none(
            category_id=category_id,
            code=code
        ).prefetch_related("category")
    
    @staticmethod
    async def get_by_category(
        category_id: int,
        is_active: bool = True
    ) -> List["SignalDefinition"]:
        """
        获取指定类别下的所有信号定义
        
        Args:
            category_id: 资产类别ID
            is_active: 是否只获取激活的信号
            
        Returns:
            信号定义列表
        """
        from app.models.platform_upgrade import SignalDefinition
        
        query = SignalDefinition.filter(category_id=category_id)
        if is_active:
            query = query.filter(is_active=True)
        
        return await query.order_by("sort_order").all()
    
    @staticmethod
    async def get_stored_signals(category_id: int) -> List["SignalDefinition"]:
        """
        获取指定类别下需要存储的信号定义
        
        Args:
            category_id: 资产类别ID
            
        Returns:
            信号定义列表
        """
        from app.models.platform_upgrade import SignalDefinition
        
        return await SignalDefinition.filter(
            category_id=category_id,
            is_stored=True,
            is_active=True
        ).order_by("sort_order").all()
    
    @staticmethod
    async def get_realtime_signals(category_id: int) -> List["SignalDefinition"]:
        """
        获取指定类别下需要实时监控的信号定义
        
        Args:
            category_id: 资产类别ID
            
        Returns:
            信号定义列表
        """
        from app.models.platform_upgrade import SignalDefinition
        
        return await SignalDefinition.filter(
            category_id=category_id,
            is_realtime=True,
            is_active=True
        ).order_by("sort_order").all()
    
    @staticmethod
    async def get_feature_signals(category_id: int) -> List["SignalDefinition"]:
        """
        获取指定类别下用于特征工程的信号定义
        
        Args:
            category_id: 资产类别ID
            
        Returns:
            信号定义列表
        """
        from app.models.platform_upgrade import SignalDefinition
        
        return await SignalDefinition.filter(
            category_id=category_id,
            is_feature=True,
            is_active=True
        ).order_by("sort_order").all()
    
    @staticmethod
    async def get_alarm_signals(category_id: int) -> List["SignalDefinition"]:
        """
        获取指定类别下启用报警的信号定义
        
        Args:
            category_id: 资产类别ID
            
        Returns:
            信号定义列表
        """
        from app.models.platform_upgrade import SignalDefinition
        
        return await SignalDefinition.filter(
            category_id=category_id,
            is_alarm_enabled=True,
            is_active=True
        ).order_by("sort_order").all()
    
    @staticmethod
    async def list_signals(
        category_id: Optional[int] = None,
        is_stored: Optional[bool] = None,
        is_realtime: Optional[bool] = None,
        is_feature: Optional[bool] = None,
        is_active: Optional[bool] = None,
        field_group: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List["SignalDefinition"], int]:
        """
        分页查询信号定义列表
        
        Args:
            category_id: 资产类别ID筛选
            is_stored: 是否存储筛选
            is_realtime: 是否实时监控筛选
            is_feature: 是否特征工程筛选
            is_active: 激活状态筛选
            field_group: 字段分组筛选
            search: 搜索关键词（匹配code或name）
            page: 页码
            page_size: 每页数量
            
        Returns:
            (信号定义列表, 总数)
        """
        from app.models.platform_upgrade import SignalDefinition
        
        query = SignalDefinition.all()
        
        if category_id is not None:
            query = query.filter(category_id=category_id)
        if is_stored is not None:
            query = query.filter(is_stored=is_stored)
        if is_realtime is not None:
            query = query.filter(is_realtime=is_realtime)
        if is_feature is not None:
            query = query.filter(is_feature=is_feature)
        if is_active is not None:
            query = query.filter(is_active=is_active)
        if field_group is not None:
            query = query.filter(field_group=field_group)
        if search:
            query = query.filter(
                code__icontains=search
            ) | query.filter(
                name__icontains=search
            )
        
        total = await query.count()
        offset = (page - 1) * page_size
        signals = await query.prefetch_related("category").order_by("sort_order").offset(offset).limit(page_size)
        
        return list(signals), total
    
    @staticmethod
    async def get_by_group(
        category_id: int,
        field_group: str,
        is_active: bool = True
    ) -> List["SignalDefinition"]:
        """
        获取指定类别和分组下的信号定义
        
        Args:
            category_id: 资产类别ID
            field_group: 字段分组
            is_active: 是否只获取激活的信号
            
        Returns:
            信号定义列表
        """
        from app.models.platform_upgrade import SignalDefinition
        
        query = SignalDefinition.filter(
            category_id=category_id,
            field_group=field_group
        )
        if is_active:
            query = query.filter(is_active=True)
        
        return await query.order_by("sort_order").all()
    
    @staticmethod
    async def get_visible_signals(category_id: int) -> List["SignalDefinition"]:
        """
        获取指定类别下默认可见的信号定义
        
        Args:
            category_id: 资产类别ID
            
        Returns:
            信号定义列表
        """
        from app.models.platform_upgrade import SignalDefinition
        
        return await SignalDefinition.filter(
            category_id=category_id,
            is_default_visible=True,
            is_active=True
        ).order_by("sort_order").all()
    
    @staticmethod
    async def create(data: Dict[str, Any]) -> "SignalDefinition":
        """
        创建信号定义
        
        Args:
            data: 信号定义数据字典
            
        Returns:
            创建的SignalDefinition对象
        """
        from app.models.platform_upgrade import SignalDefinition
        
        signal = await SignalDefinition.create(**data)
        return await SignalDefinition.get(id=signal.id).prefetch_related("category")
    
    @staticmethod
    async def update(signal_id: int, data: Dict[str, Any]) -> Optional["SignalDefinition"]:
        """
        更新信号定义
        
        Args:
            signal_id: 信号定义ID
            data: 更新数据字典
            
        Returns:
            更新后的SignalDefinition对象或None
        """
        from app.models.platform_upgrade import SignalDefinition
        
        signal = await SignalDefinition.get_or_none(id=signal_id)
        if not signal:
            return None
        
        await signal.update_from_dict(data).save()
        return await SignalDefinition.get(id=signal_id).prefetch_related("category")
    
    @staticmethod
    async def delete(signal_id: int) -> bool:
        """
        删除信号定义
        
        Args:
            signal_id: 信号定义ID
            
        Returns:
            是否删除成功
        """
        from app.models.platform_upgrade import SignalDefinition
        
        deleted_count = await SignalDefinition.filter(id=signal_id).delete()
        return deleted_count > 0
    
    @staticmethod
    async def count_by_category(category_id: int, is_active: bool = True) -> int:
        """
        统计指定类别下的信号数量
        
        Args:
            category_id: 资产类别ID
            is_active: 是否只统计激活的信号
            
        Returns:
            信号数量
        """
        from app.models.platform_upgrade import SignalDefinition
        
        query = SignalDefinition.filter(category_id=category_id)
        if is_active:
            query = query.filter(is_active=True)
        
        return await query.count()
    
    @staticmethod
    async def get_groups(category_id: int) -> List[str]:
        """
        获取指定类别下的所有字段分组
        
        Args:
            category_id: 资产类别ID
            
        Returns:
            字段分组列表
        """
        from app.models.platform_upgrade import SignalDefinition
        
        results = await SignalDefinition.filter(
            category_id=category_id,
            is_active=True
        ).distinct().values_list("field_group", flat=True)
        
        return [r for r in results if r]
    
    @staticmethod
    async def update_sort_order(signal_id: int, sort_order: int) -> bool:
        """
        更新信号定义的排序
        
        Args:
            signal_id: 信号定义ID
            sort_order: 新的排序值
            
        Returns:
            是否更新成功
        """
        from app.models.platform_upgrade import SignalDefinition
        
        updated_count = await SignalDefinition.filter(id=signal_id).update(sort_order=sort_order)
        return updated_count > 0
    
    @staticmethod
    async def batch_update_sort_order(updates: List[Dict[str, int]]) -> int:
        """
        批量更新信号定义的排序
        
        Args:
            updates: 更新列表，每项包含 {"id": signal_id, "sort_order": new_order}
            
        Returns:
            更新的记录数
        """
        from app.models.platform_upgrade import SignalDefinition
        
        updated_count = 0
        for update in updates:
            count = await SignalDefinition.filter(id=update["id"]).update(sort_order=update["sort_order"])
            updated_count += count
        
        return updated_count
