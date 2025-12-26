from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.controllers.alarm import alarm_controller
from app.schemas.devices import WeldingAlarmHistoryQuery, WeldingAlarmHistoryResponse
from app.schemas.response import ResponseModel, ListResponseModel, ListData
from app.log import logger

router = APIRouter()


@router.get(
    "/list",
    response_model=ListResponseModel[WeldingAlarmHistoryResponse],
    summary="获取设备报警历史列表",
    description="根据设备类型、设备编号和时间范围查询设备报警历史数据"
)
async def get_device_alarm_list(
    device_type: Optional[str] = Query(None, description="设备类型，当前支持：welding"),
    device_code: Optional[str] = Query(None, description="设备编号"),
    start_time: Optional[str] = Query(None, description="开始时间，格式：YYYY-MM-DD HH:MM:SS"),
    end_time: Optional[str] = Query(None, description="结束时间，格式：YYYY-MM-DD HH:MM:SS"),
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(20, description="每页数量", ge=1, le=100)
):
    """获取设备报警历史列表
    
    支持的查询参数：
    - device_type: 设备类型，当前只支持 'welding'
    - device_code: 设备编号，对应数据库中的 prod_code 字段
    - start_time: 开始时间，筛选 alarm_time >= start_time 的记录
    - end_time: 结束时间，筛选 alarm_time <= end_time 的记录
    - page: 页码，从1开始
    - page_size: 每页数量，范围1-100
    
    返回数据包含：
    - items: 报警历史记录列表
    - total: 总记录数
    - page: 当前页码
    - page_size: 每页数量
    - total_pages: 总页数
    """
    try:
        logger.info("查询设备报警历史，参数: device_type={}, device_code={}, start_time={}, end_time={}, page={}, page_size={}", device_type, device_code, start_time, end_time, page, page_size)
        
        # 时间字符串解析 - 直接创建naive datetime以匹配数据库格式
        parsed_start_time = None
        parsed_end_time = None
        
        if start_time:
            try:
                # 解析时间字符串为naive datetime（无时区信息）
                parsed_start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    # 尝试解析日期格式
                    parsed_start_time = datetime.strptime(start_time, "%Y-%m-%d")
                except ValueError:
                    raise HTTPException(status_code=400, detail="开始时间格式错误，请使用 YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DD 格式")
        
        if end_time:
            try:
                # 解析时间字符串为naive datetime（无时区信息）
                parsed_end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    # 尝试解析日期格式
                    parsed_end_time = datetime.strptime(end_time, "%Y-%m-%d")
                except ValueError:
                    raise HTTPException(status_code=400, detail="结束时间格式错误，请使用 YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DD 格式")
        
        # 参数验证
        if parsed_start_time and parsed_end_time and parsed_start_time > parsed_end_time:
            raise HTTPException(status_code=400, detail="开始时间不能大于结束时间")
        
        # 调用控制器获取数据
        result = await alarm_controller.get_welding_alarm_history(
            device_type=device_type,
            device_code=device_code,
            start_time=parsed_start_time,
            end_time=parsed_end_time,
            page=page,
            page_size=page_size
        )
        
        # 转换为响应模型
        items = [WeldingAlarmHistoryResponse.from_orm(item) for item in result["items"]]
        
        response_data = ListData(
            items=items,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"]
        )
        
        logger.info("查询设备报警历史成功，返回{}条记录", len(items))
        
        return ListResponseModel(
            code=200,
            message="查询成功",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("查询设备报警历史失败: {}", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="查询报警历史数据失败")


@router.get(
    "/statistics",
    response_model=ResponseModel[Dict[str, Any]],
    summary="获取设备报警统计信息",
    description="获取设备报警的统计信息，包括总数、活跃报警、已解决报警等"
)
async def get_device_alarm_statistics(
    device_type: Optional[str] = Query(None, description="设备类型，当前支持：welding"),
    start_time: Optional[datetime] = Query(None, description="开始时间，格式：YYYY-MM-DD HH:MM:SS"),
    end_time: Optional[datetime] = Query(None, description="结束时间，格式：YYYY-MM-DD HH:MM:SS")
):
    """获取设备报警统计信息
    
    返回数据包含：
    - total_alarms: 总报警数
    - active_alarms: 活跃报警数（未结束的报警）
    - resolved_alarms: 已解决报警数（已结束的报警）
    - avg_duration: 平均持续时间（秒）
    """
    try:
        logger.info("查询设备报警统计信息，参数: device_type={}, start_time={}, end_time={}", device_type, start_time, end_time)
        
        # 参数验证
        if start_time and end_time and start_time > end_time:
            raise HTTPException(status_code=400, detail="开始时间不能大于结束时间")
        
        # 调用控制器获取统计数据
        statistics = await alarm_controller.get_alarm_statistics(
            device_type=device_type,
            start_time=start_time,
            end_time=end_time
        )
        
        logger.info("查询设备报警统计信息成功")
        
        return ResponseModel(
            code=200,
            message="查询成功",
            data=statistics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("查询设备报警统计信息失败: {}", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="查询报警统计信息失败")