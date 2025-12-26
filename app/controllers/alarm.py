from typing import List, Optional, Dict, Any
from datetime import datetime
from tortoise.expressions import Q
from tortoise.queryset import QuerySet
from fastapi import HTTPException
from tortoise.functions import Sum

from app.core.crud import CRUDBase
from app.models.device import DeviceAlarmHistory, DeviceInfo
from app.schemas.devices import WeldingAlarmHistoryQuery
from app.log import logger


class AlarmController:
    """报警控制器
    
    提供报警历史数据的查询和业务逻辑处理 (已升级为通用版)
    """
    
    def __init__(self):
        self.model = DeviceAlarmHistory
    
    async def get_welding_alarm_history(
        self,
        device_type: Optional[str] = None,
        device_code: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取设备报警历史数据 (API兼容适配器)
        
        Args:
            device_type: 设备类型
            device_code: 设备编号
            start_time: 开始时间
            end_time: 结束时间
            page: 页码
            page_size: 每页数量
            
        Returns:
            包含报警历史数据和分页信息的字典
        """
        try:
            # 验证设备类型参数
            if not device_type:
                logger.warning("设备类型参数为空")
                raise HTTPException(status_code=400, detail="请选择设备类型")
            
            # 1. 构建查询条件 (基于新模型 DeviceAlarmHistory)
            query = self.model.all()
            
            # 关联查询 device 以获取 device_code
            query = query.prefetch_related('device')
            
            # 2. 过滤条件适配
            
            # 设备类型过滤
            # 兼容旧逻辑：如果传的是 'welding'，实际对应 type_code='welding_robot' 或类似的
            # DeviceInfo 中有 device_type 字段 (字符串)
            if device_type:
                query = query.filter(device__device_type=device_type)

            # 设备编号过滤 (prod_code -> device.device_code)
            if device_code:
                query = query.filter(device__device_code=device_code)
            
            # 时间范围过滤 (alarm_time -> start_time)
            if start_time:
                query = query.filter(start_time__gte=start_time)
            
            if end_time:
                query = query.filter(start_time__lte=end_time)
            
            # 3. 获取总数
            total = await query.count()
            
            # 4. 分页查询
            offset = (page - 1) * page_size
            items = await query.offset(offset).limit(page_size).order_by("-start_time")
            
            # 5. 响应数据适配 (New Model -> Old API Response)
            mapped_items = []
            for item in items:
                # 获取上下文数据
                context = item.context or {}
                
                mapped_item = {
                    "id": item.id,
                    "prod_code": item.device.device_code if item.device else "UNKNOWN",
                    "alarm_time": item.start_time,
                    "alarm_end_time": item.end_time,
                    "alarm_duration_sec": context.get("duration_sec"),
                    "alarm_code": item.alarm_code,
                    "alarm_message": item.content,
                    "alarm_solution": context.get("solution"),
                    "created_at": item.created_at,
                    "updated_at": item.updated_at
                }
                mapped_items.append(mapped_item)
            
            # 计算总页数
            total_pages = (total + page_size - 1) // page_size
            
            logger.info(f"查询设备报警历史数据成功(通用适配)，共{total}条记录")
            
            return {
                "items": mapped_items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
            
        except Exception as e:
            logger.error(f"查询设备报警历史数据失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="查询报警历史数据失败")
    
    async def get_alarm_statistics(
        self,
        device_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取报警统计信息 (通用适配)
        
        Args:
            device_type: 设备类型
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            报警统计信息字典
        """
        try:
            # 构建查询条件
            query = self.model.all()
            
            # 设备类型过滤
            if device_type:
                query = query.filter(device__device_type=device_type)
            
            # 时间范围过滤
            if start_time:
                query = query.filter(start_time__gte=start_time)
            
            if end_time:
                query = query.filter(start_time__lte=end_time)
            
            # 获取统计数据
            total_alarms = await query.count()
            active_alarms = await query.filter(end_time__isnull=True).count()
            resolved_alarms = await query.filter(end_time__isnull=False).count()
            
            # 计算平均持续时间
            # 注意：JSONB 中的字段无法直接用于数据库级聚合，需要在内存中计算或使用原生SQL
            # 这里为了兼容性，我们获取最近 1000 条已解决的报警来估算平均值，避免全表扫描
            resolved_items = await query.filter(
                end_time__isnull=False
            ).limit(1000).values_list("context", flat=True)
            
            total_duration = 0
            count = 0
            
            for context in resolved_items:
                if context and isinstance(context, dict):
                    duration = context.get("duration_sec")
                    if duration is not None:
                        total_duration += float(duration)
                        count += 1
            
            avg_duration = 0
            if count > 0:
                avg_duration = total_duration / count
            
            logger.info(f"获取报警统计信息成功，总报警数: {total_alarms}")
            
            return {
                "total_alarms": total_alarms,
                "active_alarms": active_alarms,
                "resolved_alarms": resolved_alarms,
                "avg_duration": round(avg_duration, 2)
            }
            
        except Exception as e:
            logger.error(f"获取报警统计信息失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="获取报警统计信息失败")


# 创建全局实例
alarm_controller = AlarmController()