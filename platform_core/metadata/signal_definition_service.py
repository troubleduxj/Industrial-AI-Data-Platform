"""
信号定义管理服务

提供信号定义的CRUD操作和业务逻辑。

迁移说明:
- 从 platform_v2.metadata.signal_definition_service 迁移到 platform_core.metadata.signal_definition_service
- 保持所有API接口不变
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SignalDefinitionService:
    """
    信号定义管理服务
    
    提供信号定义的创建、查询、更新、删除等操作。
    """
    
    @staticmethod
    async def create_signal(
        category_id: int,
        code: str,
        name: str,
        data_type: str,
        unit: Optional[str] = None,
        is_stored: bool = True,
        is_realtime: bool = True,
        is_feature: bool = False,
        is_alarm_enabled: bool = False,
        value_range: Optional[Dict[str, Any]] = None,
        validation_rules: Optional[Dict[str, Any]] = None,
        alarm_threshold: Optional[Dict[str, Any]] = None,
        aggregation_method: Optional[str] = None,
        display_config: Optional[Dict[str, Any]] = None,
        sort_order: int = 0,
        field_group: str = "default"
    ) -> "SignalDefinition":
        """
        创建信号定义
        
        Args:
            category_id: 资产类别ID
            code: 信号编码
            name: 信号名称
            data_type: 数据类型 (float/int/bool/string/double/bigint)
            unit: 单位
            is_stored: 是否存储到时序数据库
            is_realtime: 是否实时监控
            is_feature: 是否用于特征工程
            is_alarm_enabled: 是否启用报警
            value_range: 值范围
            validation_rules: 验证规则
            alarm_threshold: 报警阈值
            aggregation_method: 聚合方法
            display_config: 前端显示配置
            sort_order: 排序
            field_group: 字段分组
            
        Returns:
            SignalDefinition: 创建的信号定义对象
        """
        from app.models.platform_upgrade import SignalDefinition
        
        try:
            signal = await SignalDefinition.create(
                category_id=category_id,
                code=code,
                name=name,
                data_type=data_type,
                unit=unit,
                is_stored=is_stored,
                is_realtime=is_realtime,
                is_feature=is_feature,
                is_alarm_enabled=is_alarm_enabled,
                value_range=value_range,
                validation_rules=validation_rules,
                alarm_threshold=alarm_threshold,
                aggregation_method=aggregation_method,
                display_config=display_config,
                sort_order=sort_order,
                field_group=field_group,
                is_active=True,
                is_default_visible=True
            )
            logger.info(f"创建信号定义成功: {code} ({name})")
            return signal
        except Exception as e:
            logger.error(f"创建信号定义失败: {e}")
            raise
    
    @staticmethod
    async def get_signal_by_id(signal_id: int) -> Optional["SignalDefinition"]:
        """根据ID获取信号定义"""
        from app.models.platform_upgrade import SignalDefinition
        return await SignalDefinition.get_or_none(id=signal_id)
    
    @staticmethod
    async def get_signal_by_code(category_id: int, code: str) -> Optional["SignalDefinition"]:
        """根据类别ID和编码获取信号定义"""
        from app.models.platform_upgrade import SignalDefinition
        return await SignalDefinition.get_or_none(category_id=category_id, code=code)
    
    @staticmethod
    async def get_signals(
        category_id: Optional[int] = None,
        is_stored: Optional[bool] = None,
        is_realtime: Optional[bool] = None,
        is_feature: Optional[bool] = None,
        is_active: Optional[bool] = None,
        field_group: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List["SignalDefinition"], int]:
        """
        获取信号定义列表（分页）
        
        Args:
            category_id: 按类别ID筛选
            is_stored: 按存储状态筛选
            is_realtime: 按实时监控状态筛选
            is_feature: 按特征工程状态筛选
            is_active: 按激活状态筛选
            field_group: 按字段分组筛选
            search: 搜索关键词
            page: 页码
            page_size: 每页数量
            
        Returns:
            Tuple[List[SignalDefinition], int]: (信号列表, 总数)
        """
        from app.models.platform_upgrade import SignalDefinition
        from tortoise.expressions import Q
        
        query = SignalDefinition.all()
        
        if category_id:
            query = query.filter(category_id=category_id)
        if is_stored is not None:
            query = query.filter(is_stored=is_stored)
        if is_realtime is not None:
            query = query.filter(is_realtime=is_realtime)
        if is_feature is not None:
            query = query.filter(is_feature=is_feature)
        if is_active is not None:
            query = query.filter(is_active=is_active)
        if field_group:
            query = query.filter(field_group=field_group)
        if search:
            query = query.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search)
            )
        
        total = await query.count()
        offset = (page - 1) * page_size
        signals = await query.order_by("category_id", "sort_order").offset(offset).limit(page_size)
        
        return signals, total
    
    @staticmethod
    async def get_signals_by_category(
        category_id: int,
        is_active: bool = True
    ) -> List["SignalDefinition"]:
        """
        获取类别下的所有信号定义
        
        Args:
            category_id: 类别ID
            is_active: 是否只获取激活的信号
            
        Returns:
            List[SignalDefinition]: 信号定义列表
        """
        from app.models.platform_upgrade import SignalDefinition
        
        query = SignalDefinition.filter(category_id=category_id)
        if is_active:
            query = query.filter(is_active=True)
        
        return await query.order_by("sort_order").all()
    
    @staticmethod
    async def update_signal(
        signal_id: int,
        **kwargs
    ) -> Optional["SignalDefinition"]:
        """
        更新信号定义
        
        Args:
            signal_id: 信号ID
            **kwargs: 要更新的字段
            
        Returns:
            SignalDefinition: 更新后的信号对象，如果不存在返回None
        """
        from app.models.platform_upgrade import SignalDefinition
        
        signal = await SignalDefinition.get_or_none(id=signal_id)
        if not signal:
            return None
        
        # 过滤掉None值和不允许更新的字段
        update_data = {k: v for k, v in kwargs.items() if v is not None and k not in ("id", "category_id")}
        
        if update_data:
            await signal.update_from_dict(update_data).save()
            logger.info(f"更新信号定义成功: {signal.code}")
        
        return signal
    
    @staticmethod
    async def delete_signal(signal_id: int, soft_delete: bool = True) -> bool:
        """
        删除信号定义
        
        Args:
            signal_id: 信号ID
            soft_delete: 是否软删除（默认True）
            
        Returns:
            bool: 删除是否成功
        """
        from app.models.platform_upgrade import SignalDefinition
        
        signal = await SignalDefinition.get_or_none(id=signal_id)
        if not signal:
            return False
        
        if soft_delete:
            signal.is_active = False
            await signal.save()
        else:
            await signal.delete()
        
        logger.info(f"删除信号定义成功: {signal.code}")
        return True
    
    @staticmethod
    async def batch_create_signals(
        category_id: int,
        signals_data: List[Dict[str, Any]]
    ) -> List["SignalDefinition"]:
        """
        批量创建信号定义
        
        Args:
            category_id: 类别ID
            signals_data: 信号数据列表
            
        Returns:
            List[SignalDefinition]: 创建的信号定义列表
        """
        from app.models.platform_upgrade import SignalDefinition
        
        created_signals = []
        for data in signals_data:
            data["category_id"] = category_id
            data.setdefault("is_active", True)
            data.setdefault("is_default_visible", True)
            
            signal = await SignalDefinition.create(**data)
            created_signals.append(signal)
        
        logger.info(f"批量创建信号定义成功: {len(created_signals)} 个")
        return created_signals
    
    @staticmethod
    async def get_stored_signals(category_id: int) -> List["SignalDefinition"]:
        """获取需要存储到时序数据库的信号"""
        from app.models.platform_upgrade import SignalDefinition
        return await SignalDefinition.filter(
            category_id=category_id,
            is_stored=True,
            is_active=True
        ).order_by("sort_order").all()
    
    @staticmethod
    async def get_realtime_signals(category_id: int) -> List["SignalDefinition"]:
        """获取需要实时监控的信号"""
        from app.models.platform_upgrade import SignalDefinition
        return await SignalDefinition.filter(
            category_id=category_id,
            is_realtime=True,
            is_active=True
        ).order_by("sort_order").all()
    
    @staticmethod
    async def get_feature_signals(category_id: int) -> List["SignalDefinition"]:
        """获取用于特征工程的信号"""
        from app.models.platform_upgrade import SignalDefinition
        return await SignalDefinition.filter(
            category_id=category_id,
            is_feature=True,
            is_active=True
        ).order_by("sort_order").all()
