from datetime import date
from fastapi import APIRouter, HTTPException, Query
from app.controllers.welding_daily_report import WeldingDailyReportController
from app.schemas.welding_daily_report import (
    WeldingDailyReportSummary,
    WeldingDailyReportDetailList
)
from app.core.response import success, fail
from app.core.unified_logger import get_logger

logger = get_logger(__name__)

# 创建路由器
router = APIRouter(prefix="/statistics/daily-report", tags=["焊机日报统计"])

# 创建控制器实例
welding_daily_report_controller = WeldingDailyReportController()


@router.get(
    "/summary",
    response_model=dict,
    summary="获取焊机日报汇总数据",
    description="获取指定日期的焊机日报汇总统计数据，包括总焊接时长、总焊丝消耗、总气体消耗和总能耗"
)
async def get_daily_report_summary(
    report_date: date = Query(..., description="报告日期，格式：YYYY-MM-DD", example="2025-01-24"),
    device_type: str = Query("welding", description="设备类型，固定为welding"),
    prod_code: str = Query(None, description="设备编码，可选")
):
    """
    获取焊机日报汇总数据
    
    参数:
    - report_date: 报告日期
    - device_type: 设备类型（固定为welding）
    
    返回:
    - total_duration: 总焊接时长(秒)
    - total_wire: 总焊丝消耗(kg)
    - total_gas: 总气体消耗(升)
    - total_energy: 总能耗(kWh)
    """
    try:
        # 验证设备类型
        if device_type != "welding":
            return fail(msg="设备类型必须为welding", code=400)
        
        # 获取汇总数据
        summary_data = await welding_daily_report_controller.get_daily_report_summary(report_date, prod_code)
        
        return success(
            data=summary_data.model_dump(),
            msg=f"成功获取{report_date}的焊机日报汇总数据"
        )
        
    except Exception as e:
        logger.error(f"获取焊机日报汇总数据失败: {str(e)}")
        return fail(msg=f"获取焊机日报汇总数据失败: {str(e)}", code=500)


@router.get(
    "/detail",
    response_model=dict,
    summary="获取焊机日报详情数据",
    description="获取指定日期的焊机日报详细数据，包括所有设备的详细统计信息，按产品编码排序"
)
async def get_daily_report_detail(
    report_date: date = Query(..., description="报告日期，格式：YYYY-MM-DD", example="2025-01-24"),
    device_type: str = Query("welding", description="设备类型，固定为welding"),
    page: int = Query(None, description="页码，从1开始，不提供则返回所有数据", ge=1),
    page_size: int = Query(None, description="每页记录数，不提供则返回所有数据", ge=1, le=1000),
    prod_code: str = Query(None, description="设备编码，可选")
):
    """
    获取焊机日报详情数据
    
    参数:
    - report_date: 报告日期
    - device_type: 设备类型（固定为welding）
    
    返回:
    - data: 日报详情列表
    - total: 总记录数
    """
    try:
        # 验证设备类型
        if device_type != "welding":
            return fail(msg="设备类型必须为welding", code=400)
        
        # 获取详情数据
        # 如果page和page_size都为None，则获取所有数据
        if page is None and page_size is None:
            detail_data = await welding_daily_report_controller.get_daily_report_detail_all(report_date, prod_code)
        else:
            # 设置默认值
            page = page or 1
            page_size = page_size or 10
            detail_data = await welding_daily_report_controller.get_daily_report_detail(report_date, page, page_size, prod_code)
        
        return success(
            data=detail_data.model_dump(),
            msg=f"成功获取{report_date}的焊机日报详情数据，共{detail_data.total}条记录"
        )
        
    except Exception as e:
        logger.error(f"获取焊机日报详情数据失败: {str(e)}")
        return fail(msg=f"获取焊机日报详情数据失败: {str(e)}", code=500)