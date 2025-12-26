from typing import List, Optional
from tortoise.expressions import Q
from tortoise.functions import Count
from fastapi.exceptions import HTTPException

from app.core.crud import CRUDBase
from app.core.optimized_crud import OptimizedCRUDBase
from tortoise.transactions import in_transaction
from app.models.device import (
    DeviceInfo, DeviceType,
    DeviceRealTimeData, DeviceHistoryData, DeviceAlarmHistory,
    DeviceMaintenanceRecord, DeviceRepairRecord,
    DeviceMaintenancePlan, DeviceMaintenanceReminder,
    DeviceProcess, DeviceProcessExecution, DeviceProcessMonitoring
)
from app.schemas.devices import DeviceCreate, DeviceUpdate
from app.core.query_optimizer import monitor_performance, cached_query


class DeviceController(OptimizedCRUDBase[DeviceInfo, DeviceCreate, DeviceUpdate]):
    """设备信息控制器

    提供设备信息的CRUD操作和业务逻辑处理
    """

    def __init__(self):
        super().__init__(model=DeviceInfo, cache_ttl=300)  # 设备数据缓存5分钟

    @monitor_performance
    @cached_query(ttl=300)
    async def get_by_device_code(self, device_code: str) -> Optional[DeviceInfo]:
        """根据设备编号获取设备信息

        Args:
            device_code: 设备编号

        Returns:
            设备信息对象或None
        """
        return await self.model.filter(device_code=device_code).first()

    async def create_device(self, obj_in: DeviceCreate) -> DeviceInfo:
        """创建设备信息, 并更新设备类型的计数值

        Args:
            obj_in: 设备创建数据

        Returns:
            创建的设备信息对象

        Raises:
            HTTPException: 当设备编号或设备类型不存在时
        """
        async with in_transaction("default"):
            # 1. 检查设备编号是否已存在
            if await self.model.filter(device_code=obj_in.device_code).exists():
                raise HTTPException(status_code=400, detail=f"设备编号 {obj_in.device_code} 已存在")

            # 2. 检查并获取设备类型
            device_type_obj = await DeviceType.get_or_none(type_code=obj_in.device_type)
            if not device_type_obj:
                raise HTTPException(status_code=404, detail=f"设备类型 {obj_in.device_type} 不存在")

            # 3. 创建设备
            device = await self.model.create(**obj_in.model_dump())

            # 4. 更新设备类型的计数值
            device_type_obj.device_count += 1
            await device_type_obj.save()

            return device

    async def get_related_counts(self, id: int) -> dict:
        """获取设备关联数据的数量"""
        return {
            "repair_records": await DeviceRepairRecord.filter(device_id=id).count(),
            "maintenance_records": await DeviceMaintenanceRecord.filter(device_id=id).count(),
            "maintenance_plans": await DeviceMaintenancePlan.filter(device_id=id).count(),
            "process_executions": await DeviceProcessExecution.filter(device_id=id).count(),
            "processes": await DeviceProcess.filter(device_id=id).count(),
            "alarm_history": await DeviceAlarmHistory.filter(device_id=id).count(),
        }

    async def delete_device(self, id: int) -> None:
        """删除设备信息, 并更新设备类型的计数值

        Args:
            id: 设备ID

        Raises:
            HTTPException: 当设备不存在时
        """
        async with in_transaction("default"):
            # 1. 获取设备信息
            device = await self.get(id)
            if not device:
                raise HTTPException(status_code=404, detail="设备不存在")

            # 2. 级联删除关联数据 (按依赖顺序反向删除)
            # 工艺相关
            await DeviceProcessMonitoring.filter(device_id=id).delete()
            await DeviceProcessExecution.filter(device_id=id).delete()
            await DeviceProcess.filter(device_id=id).delete()
            
            # 维护相关
            await DeviceMaintenanceReminder.filter(device_id=id).delete()
            await DeviceMaintenancePlan.filter(device_id=id).delete()
            await DeviceRepairRecord.filter(device_id=id).delete()
            await DeviceMaintenanceRecord.filter(device_id=id).delete()
            
            # 监控数据相关
            await DeviceAlarmHistory.filter(device_id=id).delete()
            await DeviceHistoryData.filter(device_id=id).delete()
            await DeviceRealTimeData.filter(device_id=id).delete()

            # 3. 更新设备类型的计数值
            if device.device_type:
                device_type_obj = await DeviceType.get_or_none(type_code=device.device_type)
                if device_type_obj:
                    device_type_obj.device_count -= 1
                    await device_type_obj.save()

            # 3. 删除设备
            await self.remove(id)

    async def update_device(self, id: int, obj_in: DeviceUpdate) -> DeviceInfo:
        """更新设备信息，并处理设备类型变更时的计数值维护

        Args:
            id: 设备ID
            obj_in: 设备更新数据

        Returns:
            更新后的设备信息对象

        Raises:
            HTTPException: 当设备不存在或设备编号冲突时
        """
        from datetime import datetime, timezone

        try:
            async with in_transaction("default"):
                # 检查设备是否存在
                device = await self.model.filter(id=id).first()
                if not device:
                    raise HTTPException(status_code=404, detail="设备不存在")

                # 如果更新设备编号，检查是否与其他设备冲突
                if obj_in.device_code and obj_in.device_code != device.device_code:
                    existing_device = await self.get_by_device_code(obj_in.device_code)
                    if existing_device:
                        raise HTTPException(status_code=400, detail=f"设备编号 {obj_in.device_code} 已存在")

                # 检查是否更新了设备类型
                old_device_type = device.device_type
                new_device_type = obj_in.device_type if obj_in.device_type else old_device_type
                
                # 如果设备类型发生变更，需要更新相关类型的计数值
                if new_device_type and old_device_type != new_device_type:
                    # 原设备类型计数减1
                    if old_device_type:
                        old_type_obj = await DeviceType.get_or_none(type_code=old_device_type)
                        if old_type_obj:
                            old_type_obj.device_count -= 1
                            await old_type_obj.save()
                    
                    # 新设备类型计数加1
                    new_type_obj = await DeviceType.get_or_none(type_code=new_device_type)
                    if new_type_obj:
                        new_type_obj.device_count += 1
                        await new_type_obj.save()
                    else:
                        raise HTTPException(status_code=404, detail=f"设备类型 {new_device_type} 不存在")

                # 转换输入数据为字典并添加更新时间
                update_data = obj_in.dict(exclude_unset=True)
                update_data["updated_at"] = datetime.now()

                # 更新记录
                await self.model.filter(id=id).update(**update_data)
                return await self.model.filter(id=id).first()
        except HTTPException:
            raise
        except Exception as e:
            import traceback

            traceback.print_exc()
            raise HTTPException(
                status_code=500, detail={"message": "更新设备失败", "error": str(e), "error_type": type(e).__name__}
            )

    async def get_devices_by_type(self, device_type: str, page: int = 1, page_size: int = 10) -> tuple[int, List[DeviceInfo]]:
        """根据设备类型获取设备列表

        Args:
            device_type: 设备类型
            page: 页码
            page_size: 每页数量

        Returns:
            元组(总数量, 设备列表)
        """
        q = Q(device_type=device_type)
        return await self.get_multi_with_total(page=page, page_size=page_size, search=q)

    async def get_devices_by_location(self, location: str) -> List[DeviceInfo]:
        """根据安装位置获取设备列表

        Args:
            location: 安装位置

        Returns:
            设备信息列表
        """
        return await self.model.filter(install_location__icontains=location).all()

    async def get_devices_by_team(self, team_name: str) -> List[DeviceInfo]:
        """根据所属班组获取设备列表

        Args:
            team_name: 班组名称

        Returns:
            设备信息列表
        """
        return await self.model.filter(team_name=team_name).all()

    async def get_locked_devices(self) -> List[DeviceInfo]:
        """获取所有锁定状态的设备

        Returns:
            锁定设备列表
        """
        return await self.model.filter(is_locked=True).all()

    async def toggle_device_lock(self, id: int) -> DeviceInfo:
        """切换设备锁定状态

        Args:
            id: 设备ID

        Returns:
            更新后的设备信息对象

        Raises:
            HTTPException: 当设备不存在或更新失败时
        """
        try:
            device = await self.model.filter(id=id).first()
            if not device:
                raise HTTPException(status_code=404, detail="设备不存在")

            device.is_locked = not device.is_locked
            await device.save()
            return device
        except HTTPException:
            raise
        except Exception as e:
            import traceback

            traceback.print_exc()
            raise HTTPException(
                status_code=500, detail={"message": "切换锁定状态失败", "error": str(e), "error_type": type(e).__name__}
            )

    @monitor_performance
    @cached_query(ttl=600)  # 统计数据缓存时间更长
    async def get_type_statistics(self) -> List[dict]:
        """获取按设备类型的统计信息

        Returns:
            设备类型统计列表

        Raises:
            HTTPException: 当查询失败时
        """
        try:
            # 使用优化的统计查询
            return await self.get_statistics(group_by="device_type")
        except Exception as e:
            import traceback
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"获取设备类型统计失败: {str(e)}")
            logger.error(f"完整错误堆栈: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "获取设备类型统计失败",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "stack_trace": traceback.format_exc(),
                },
            )

    @monitor_performance
    @cached_query(ttl=600)  # 统计数据缓存时间更长
    async def get_team_statistics(self) -> List[dict]:
        """获取按班组的统计信息

        Returns:
            班组统计列表

        Raises:
            HTTPException: 当查询失败时
        """
        try:
            import logging

            logger = logging.getLogger(__name__)
            logger.info("开始执行班组统计查询")

            # 使用优化的统计查询，过滤掉空的team_name
            from tortoise.expressions import Q
            stats = await self.get_statistics(
                group_by="team_name", 
                search=Q(team_name__not_isnull=True)
            )

            logger.info(f"查询结果: {stats}")
            return [{"team": item["team_name"], "count": item["count"]} for item in stats]
        except Exception as e:
            import traceback
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"获取班组统计失败: {str(e)}")
            logger.error(f"完整错误堆栈: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "获取班组统计失败",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "stack_trace": traceback.format_exc(),
                },
            )

    async def count(self, search: Q = None) -> int:
        """统计设备数量

        Args:
            search: 查询条件

        Returns:
            设备数量
        """
        if search:
            return await self.model.filter(search).count()
        return await self.model.all().count()

    @monitor_performance
    async def search_devices(
        self,
        keyword: str = None,
        device_type: str = None,
        manufacturer: str = None,
        team_name: str = None,
        is_locked: bool = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[int, List[DeviceInfo]]:
        """搜索设备信息并分页

        Args:
            keyword: 关键词（搜索设备名称、编号、型号）
            device_type: 设备类型
            manufacturer: 制造商
            team_name: 所属班组
            is_locked: 锁定状态
            page: 页码
            page_size: 每页数量

        Returns:
            元组(总数量, 设备列表)
        """
        # 使用优化的搜索功能
        filters = {}
        if device_type:
            filters['device_type'] = device_type
        if manufacturer:
            filters['manufacturer__icontains'] = manufacturer
        if team_name:
            filters['team_name'] = team_name
        if is_locked is not None:
            filters['is_locked'] = is_locked
        
        search_fields = ['device_name', 'device_code', 'device_model']
        
        return await self.search_optimized(
            keyword=keyword,
            filters=filters,
            page=page,
            page_size=page_size,
            search_fields=search_fields,
            order=['-created_at']
        )


# 创建控制器实例
device_controller = DeviceController()
