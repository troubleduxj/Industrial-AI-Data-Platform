from fastapi import APIRouter, Query, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.core.dependency import DependAuth
from app.models.device import DeviceInfo

from app.schemas.base import Success
from tortoise.functions import Count
from tortoise.expressions import Q

router = APIRouter()


@router.get("/", summary="获取仪表板数据", dependencies=[DependAuth])
async def get_dashboard(
    current_user=DependAuth
) -> Dict[str, Any]:
    """获取仪表板概览数据"""
    try:
        # 获取设备统计
        total_devices = await DeviceInfo.all().count()
        online_devices = await DeviceInfo.filter(is_locked=False).count()
        offline_devices = total_devices - online_devices
        

        
        recent_data_points = 0 # 暂时设置为0，因为DeviceRealTimeData已被移除
        
        # 获取设备类型分布
        device_types = await DeviceInfo.all().group_by('device_type').annotate(
            count=Count('id')
        ).values('device_type', 'count')
        
        dashboard_data = {
            "overview": {
                "total_devices": total_devices,
                "online_devices": online_devices,
                "offline_devices": offline_devices,

                "recent_data_points": recent_data_points
            },
            "device_types": device_types,
            "last_updated": datetime.now().isoformat()
        }
        
        return Success(data=dashboard_data, msg="获取仪表板数据成功")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表板数据失败: {str(e)}")


@router.get("/charts", summary="获取图表数据", dependencies=[DependAuth])
async def get_chart_data(
    chart_type: Optional[str] = Query(None, description="图表类型"),
    time_range: Optional[str] = Query("24h", description="时间范围: 1h, 24h, 7d, 30d"),
    current_user=DependAuth
) -> Dict[str, Any]:
    """获取图表数据"""
    try:
        # 根据时间范围计算起始时间
        time_ranges = {
            "1h": timedelta(hours=1),
            "24h": timedelta(days=1),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }
        
        start_time = datetime.now() - time_ranges.get(time_range, timedelta(days=1))
        
        # 获取设备状态趋势数据
        device_trend = []
        if chart_type in [None, "device_trend"]:
            # 这里可以根据实际需求实现更复杂的趋势分析
            total_devices = await DeviceInfo.all().count()
            online_devices = await DeviceInfo.filter(is_locked=False).count()
            
            device_trend = {
                "labels": ["在线设备", "离线设备"],
                "data": [online_devices, total_devices - online_devices],
                "colors": ["#52c41a", "#ff4d4f"]
            }
        
        # 获取数据采集趋势 (此功能已移除，因为DeviceRealTimeData已被移除)
        collection_trend = {"labels": [], "data": []}
        
        chart_data = {
            "device_trend": device_trend,
            "collection_trend": collection_trend,
            "generated_at": datetime.now().isoformat()
        }
        
        return Success(data=chart_data, msg="获取图表数据成功")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图表数据失败: {str(e)}")