from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from app.core.dependency import DependAuth
from app.controllers.device_data import DeviceDataController

from app.core.response import Success, SuccessExtra
from app.log import logger

router = APIRouter()
device_data_controller = DeviceDataController()



@router.get("/realtime/latest/{device_id}", summary="获取设备最新实时数据", dependencies=[DependAuth])
async def get_device_latest_data(
    device_id: int,
):
    """获取指定设备的最新实时数据"""
    try:
        latest_data = await device_data_controller.get_device_latest_data(device_id=device_id)
        if not latest_data:
            return Success(data=None, msg="暂无实时数据")

        # 获取设备信息
        device = await latest_data.device

        response_data = {
            "id": latest_data.id,
            "device_id": latest_data.device_id,
            "device_code": device.device_code,
            "device_name": device.device_name,
            "voltage": latest_data.voltage,
            "current": latest_data.current,
            "power": latest_data.power,
            "temperature": latest_data.temperature,
            "pressure": latest_data.pressure,
            "vibration": latest_data.vibration,
            "status": latest_data.status,
            "error_code": latest_data.error_code,
            "error_message": latest_data.error_message,
            "data_timestamp": latest_data.data_timestamp,
            "created_at": latest_data.created_at,
            "updated_at": latest_data.updated_at,
        }

        return Success(data=response_data, msg="获取成功")
    except Exception as e:
        logger.error(f"获取设备最新数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取设备最新数据失败")


@router.get("/realtime/latest_by_code/{device_code}", summary="根据设备编号获取最新实时数据", dependencies=[DependAuth])
async def get_device_latest_data_by_code(
    device_code: str,
):
    """根据设备编号获取最新实时数据"""
    try:
        latest_data = await device_data_controller.get_device_latest_data_by_code(device_code=device_code)
        if not latest_data:
            return Success(data=None, msg="暂无实时数据")

        # 获取设备信息
        device = await latest_data.device

        response_data = {
            "id": latest_data.id,
            "device_id": latest_data.device_id,
            "device_code": device.device_code,
            "device_name": device.device_name,
            "voltage": latest_data.voltage,
            "current": latest_data.current,
            "power": latest_data.power,
            "temperature": latest_data.temperature,
            "pressure": latest_data.pressure,
            "vibration": latest_data.vibration,
            "status": latest_data.status,
            "error_code": latest_data.error_code,
            "error_message": latest_data.error_message,
            "data_timestamp": latest_data.data_timestamp,
            "created_at": latest_data.created_at,
            "updated_at": latest_data.updated_at,
        }

        return Success(data=response_data, msg="获取成功")
    except Exception as e:
        logger.error(f"获取设备最新数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取设备最新数据失败")


@router.get("/status/summary", summary="获取所有设备状态汇总", dependencies=[DependAuth])
async def get_devices_status_summary(
    type_code: Optional[str] = Query(None, description="设备类型代码，不提供则查询所有类型")
):
    """获取所有设备的状态汇总信息"""
    try:
        summary = await device_data_controller.get_devices_status_summary(type_code=type_code)
        return Success(data=summary, msg="获取成功")
    except Exception as e:
        logger.error(f"获取设备状态汇总失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取设备状态汇总失败")


@router.get("/status/online_count", summary="获取在线设备数量", dependencies=[DependAuth])
async def get_online_devices_count(
    type_code: Optional[str] = Query(None, description="设备类型代码，不提供则查询所有类型")
):
    """获取当前在线设备数量"""
    try:
        online_count = await device_data_controller.get_online_devices_count(type_code=type_code)
        return Success(data={"online_count": online_count}, msg="获取成功")
    except Exception as e:
        logger.error(f"获取在线设备数量失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取在线设备数量失败")


@router.get("/status/realtime", summary="获取设备实时状态统计", dependencies=[DependAuth])
async def get_realtime_device_status(device_type: str = Query(..., description="设备类型代码 (e.g., welding)")):
    """获取指定类型设备的实时状态统计信息"""
    try:
        statistics = await device_data_controller.get_realtime_device_status(device_type=device_type)
        return Success(data=statistics, msg="获取成功")
    except HTTPException as http_exc:
        # 直接重新抛出控制器中定义的HTTPException
        raise http_exc
    except Exception as e:
        logger.error(f"获取设备实时状态统计失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取设备实时状态统计失败")


@router.get("/status/statistics", summary="获取设备状态统计", dependencies=[DependAuth])
async def get_device_status_statistics(
    type_code: Optional[str] = Query(None, description="设备类型代码，不提供则查询所有类型")
):
    """获取设备状态统计信息，包括各状态设备数量和占比"""
    try:
        statistics = await device_data_controller.get_device_status_statistics(type_code=type_code)
        return Success(data=statistics, msg="获取成功")
    except Exception as e:
        logger.error(f"获取设备状态统计失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取设备状态统计失败")


@router.get("/status/online_rate_history", summary="获取设备在线率历史数据", dependencies=[DependAuth])
async def get_device_online_rate_history(
    type_code: Optional[str] = Query(None, description="设备类型代码，不提供则查询所有类型"),
    days: int = Query(7, description="查询天数，默认7天", ge=1, le=30),
):
    """获取设备在线率历史数据，用于趋势图表"""
    try:
        history_data = await device_data_controller.get_device_online_rate_history(type_code=type_code, days=days)
        return Success(data=history_data, msg="获取成功")
    except Exception as e:
        logger.error(f"获取设备在线率历史数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取设备在线率历史数据失败")


@router.get("/history", summary="查询设备历史数据", dependencies=[DependAuth])
async def get_device_history_data(
    device_id: Optional[int] = Query(None, description="设备ID"),
    device_code: Optional[str] = Query(None, description="设备编号"),
    start_time: Optional[int] = Query(None, description="开始时间，毫秒时间戳"),
    end_time: Optional[int] = Query(None, description="结束时间，毫秒时间戳"),
    status: Optional[str] = Query(None, description="设备状态"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
):
    """查询设备历史数据"""
    logger.info(
        f"API: Received history data query: device_code={device_code}, start_time={start_time}, end_time={end_time}, page={page}, page_size={page_size}"
    )
    try:
        # 将毫秒时间戳转换为 datetime 对象
        start_dt = datetime.fromtimestamp(start_time / 1000) if start_time else None
        end_dt = datetime.fromtimestamp(end_time / 1000) if end_time else None

        logger.info(f"API: Converted timestamps - start_dt={start_dt}, end_dt={end_dt}")

        total, history_data = await device_data_controller.get_device_history_data(
            device_id=device_id,
            device_code=device_code,
            start_time=start_dt,
            end_time=end_dt,
            status=status,
            page=page,
            page_size=page_size,
        )

        logger.info(f"API: Query successful - total={total}, returned_items={len(history_data)}")
        return SuccessExtra(data=history_data, total=total, page=page, page_size=page_size, msg="查询成功")

    except Exception as e:
        logger.error(f"API: 查询设备历史数据失败 - Error: {str(e)}", exc_info=True)
        logger.error(f"API: Query parameters - device_code={device_code}, start_time={start_time}, end_time={end_time}")
        raise HTTPException(status_code=500, detail=f"查询设备历史数据失败: {str(e)}")



    try:
        realtime_data = await device_data_controller.update_device_realtime_data(device_id=device_id, data=data)
        return Success(data={"id": realtime_data.id}, msg="实时数据更新成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新设备实时数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="更新设备实时数据失败")


# 批量更新功能暂时移除，等待DeviceRealTimeDataUpdate schema定义


@router.get("/realtime/{type_code}", summary="获取指定类型设备实时数据", response_model=dict, dependencies=[DependAuth])
async def get_device_realtime_data_by_type(
    type_code: str,
    device_code: Optional[str] = Query(None, description="设备编号，不提供则查询所有设备（单个设备）"),
    device_codes: Optional[List[str]] = Query(None, description="设备编号列表，支持批量查询（多个设备）"),
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(20, description="每页数量", ge=1, le=100),
    use_dynamic_fields: bool = Query(False, description="是否使用动态字段支持，默认为静态字段支持"),
    paged: bool = Query(True, description="是否启用分页"),
):
    """根据设备类型获取实时数据 - 从TDengine对应超级表获取

    支持两种查询模式：
    1. 单设备查询：使用device_code参数
    2. 批量查询：使用device_codes参数（数组形式）

    注意：device_code和device_codes不能同时使用
    """
    try:
        query = DeviceRealtimeQuery(
            type_code=type_code,
            device_code=device_code,
            device_codes=device_codes,
            page=page,
            page_size=page_size,
            use_dynamic_fields=use_dynamic_fields,
            paged=paged,
        )
        controller = DeviceDataController()
        result = await controller.get_device_realtime_data(query)
        return Success(data=result, msg="获取成功")
    except Exception as e:
        logger.error(f"获取设备实时数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取设备实时数据失败")


@router.get("/statistics/dashboard/alarm_record_top", summary="获取报警时长Top排名统计数据", dependencies=[DependAuth])
async def get_alarm_record_top(
    start_time: str = Query(..., description="开始时间，格式：YYYY-MM-DD"),
    end_time: str = Query(..., description="结束时间，格式：YYYY-MM-DD"),
    top: int = Query(10, description="Top数量，默认10", ge=1, le=100),
):
    """获取报警时长Top排名统计数据
    
    根据指定时间范围，查询设备报警时长排名前N的数据
    """
    try:
        controller = DeviceDataController()
        result = await controller.get_alarm_record_top(start_time, end_time, top)
        return Success(data=result, msg="获取报警记录Top数据成功")
    except Exception as e:
        logger.error(f"获取报警记录Top数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取报警记录Top数据失败")


@router.get("/statistics/dashboard/online-welding-rate", summary="获取在线率和焊接率统计数据", dependencies=[DependAuth])
async def get_online_welding_rate_statistics(
    start_time: str = Query(..., description="开始时间 (YYYY-MM-DD)"),
    end_time: str = Query(..., description="结束时间 (YYYY-MM-DD)")
):
    """
    获取在线率和焊接率统计数据
    
    Args:
        start_time: 开始时间 (YYYY-MM-DD)
        end_time: 结束时间 (YYYY-MM-DD)
        
    Returns:
        包含设备总数、焊接设备数、开机设备数、关机设备数、在线率、焊接率的数据
    """
    try:
        controller = DeviceDataController()
        result = await controller.get_online_welding_rate_statistics(start_time, end_time)
        return Success(data=result, msg="获取在线率和焊接率统计数据成功")
    except Exception as e:
        logger.error("获取在线率和焊接率统计数据失败: " + str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="获取在线率和焊接率统计数据失败")


@router.get("/statistics/dashboard/alarm-category-summary", summary="获取报警类型分布统计数据", dependencies=[DependAuth])
async def get_alarm_category_summary(
    start_time: str = Query(..., description="开始时间 (YYYY-MM-DD)"),
    end_time: str = Query(..., description="结束时间 (YYYY-MM-DD)")
):
    """
    获取报警类型分布统计数据
    
    Args:
        start_time: 开始时间 (YYYY-MM-DD)
        end_time: 结束时间 (YYYY-MM-DD)
        
    Returns:
        包含各报警类型的记录数和持续时间统计
    """
    try:
        controller = DeviceDataController()
        result = await controller.get_alarm_category_summary(start_time, end_time)
        return Success(data=result, msg="获取报警类型分布统计数据成功")
    except Exception as e:
        logger.error("获取报警类型分布统计数据失败: " + str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="获取报警类型分布统计数据失败")


@router.get("/statistics/dashboard/alarm_record_top", summary="获取报警时长Top排名统计数据", dependencies=[DependAuth])
async def get_alarm_record_top(
    start_time: str = Query(..., description="开始时间 (YYYY-MM-DD)"),
    end_time: str = Query(..., description="结束时间 (YYYY-MM-DD)"),
    top: int = Query(10, description="返回Top数量，默认10", ge=1, le=100)
):
    """
    获取报警时长Top排名统计数据
    
    Args:
        start_time: 开始时间 (YYYY-MM-DD)
        end_time: 结束时间 (YYYY-MM-DD)
        top: 返回Top数量，默认10
        
    Returns:
        包含设备编码、设备名称、报警时长的Top排名数据
    """
    try:
        controller = DeviceDataController()
        result = await controller.get_alarm_record_top(start_time, end_time, top)
        return Success(data=result, msg="获取报警时长Top排名统计数据成功")
    except Exception as e:
        logger.error("获取报警时长Top排名统计数据失败: " + str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="获取报警时长Top排名统计数据失败")


@router.get("/statistics/online-rate", summary="获取在线率统计数据", dependencies=[DependAuth])
async def get_online_rate_statistics(
    device_type: Optional[str] = Query(None, description="设备类型代码"),
    device_group: Optional[str] = Query(None, description="设备组"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
):
    """获取在线率统计数据
    
    从TDengine超级表获取在线率统计数据，超级表名从PostgreSQL数据字典获取
    """
    try:
        statistics = await device_data_controller.get_online_rate_statistics(
            device_type=device_type,
            device_group=device_group,
            start_date=start_date,
            end_date=end_date
        )
        return Success(data=statistics, msg="获取成功")
    except Exception as e:
        logger.error(f"获取在线率统计数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取在线率统计数据失败")


@router.get("/statistics/weld-time", summary="获取焊接时长统计数据", dependencies=[DependAuth])
async def get_weld_time_statistics(
    device_type: Optional[str] = Query(None, description="设备类型代码"),
    device_group: Optional[str] = Query(None, description="设备组"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
):
    """获取焊接时长统计数据
    
    从TDengine查询焊接时长统计数据
    """
    try:
        statistics = await device_data_controller.get_weld_time_statistics(
            device_type=device_type,
            device_group=device_group,
            start_date=start_date,
            end_date=end_date
        )
        return Success(data=statistics, msg="获取成功")
    except Exception as e:
        logger.error(f"获取焊接时长统计数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取焊接时长统计数据失败")


@router.get("/realtime-data", summary="获取设备实时数据（兼容旧接口）", response_model=dict, dependencies=[DependAuth])
async def get_welding_realtime_data_compatible(
    type_code: str = Query(..., description="设备类型编码"),
    device_code: Optional[str] = Query(None, description="设备编号，不提供则查询所有设备（单个设备）"),
    device_codes: Optional[List[str]] = Query(None, description="设备编号列表，支持批量查询（多个设备）"),
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(20, description="每页数量", ge=1, le=100),
    use_dynamic_fields: bool = Query(False, description="是否使用动态字段支持，默认为静态字段支持"),
):
    """兼容旧接口的设备实时数据获取

    支持两种查询模式：
    1. 单设备查询：使用device_code参数
    2. 批量查询：使用device_codes参数（数组形式）

    注意：device_code和device_codes不能同时使用
    """
    try:
        query = DeviceRealtimeQuery(
            type_code=type_code,
            device_code=device_code,
            device_codes=device_codes,
            page=page,
            page_size=page_size,
            use_dynamic_fields=use_dynamic_fields,
        )
        controller = DeviceDataController()
        result = await controller.get_device_realtime_data(query)
        return Success(data=result, msg="获取成功")
    except Exception as e:
        logger.error(f"获取设备实时数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取设备实时数据失败")
