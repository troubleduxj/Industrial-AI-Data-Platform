from fastapi import APIRouter, Query, Depends
from app.core.tdengine_connector import TDengineConnector
from app.core.dependency import get_tdengine_connector
import logging
from fastapi import APIRouter, Query, Depends, HTTPException
from app.schemas.base import Success, SuccessExtra, Fail
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/statistics/use-record/list", summary="获取焊接记录列表")
async def get_welding_record_list(
    device_code: Optional[str] = Query(None, alias="deviceCode"),
    device_type: Optional[str] = Query("welding", description="设备类型"),
    start_time: str = Query(..., description="开始时间 (YYYY-MM-DD HH:MM:SS)"),
    end_time: str = Query(..., description="结束时间 (YYYY-MM-DD HH:MM:SS)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    td_connector: TDengineConnector = Depends(get_tdengine_connector),
):
    # 添加调试日志
    logger.info(f"接收到的查询参数: device_code={device_code}, start_time={start_time}, end_time={end_time}, page={page}, page_size={page_size}")
    # 构建子表名
    if device_code:
        sub_table_name = f"record_{device_code}"
    else:
        sub_table_name = "welding_record_his"

    # 构建查询SQL
    # 注意：TDengine的时间戳通常是毫秒或纳秒，这里假设是毫秒，并进行转换
    # 如果实际时间戳单位不同，需要调整FROM_UNIXTIME的参数或时间格式
    start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')

    if start_dt > end_dt:
        raise HTTPException(status_code=422, detail="开始时间不能晚于结束时间")

    start_time_str = start_dt.strftime('%Y-%m-%d %H:%M:%S.000')
    end_time_str = end_dt.strftime('%Y-%m-%d %H:%M:%S.000')

    sql = f"SELECT device_code,ts, weld_end_time, team_name, shift_name, spec_match_rate, avg_current, avg_voltage, operator_name, workpiece_code, wire_consumption, duration_sec, operator_card_id, operator_code FROM hlzg_db.{sub_table_name} WHERE ts >= '{start_time_str}' AND ts <= '{end_time_str}'"
    if device_code:
        sql += f" AND device_code = '{device_code}'"
    sql += " ORDER BY ts DESC"

    # 执行查询
    try:
        result = await td_connector.query_data(sql, db_name="hlzg_db")
    except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Error querying TDengine: {e}\n{error_traceback}")
            return Fail(code=500, message=f"Error querying TDengine: {e}. Details: {error_traceback}")

    # 提取数据
    data = []
    logger.info(f"TDengine query result type: {type(result)}")
    logger.info(f"TDengine query result content: {result}")
    if result and isinstance(result, dict):
        logger.info(f"TDengine query result keys: {result.keys()}")
    if result and isinstance(result, dict):
        logger.info(f"TDengine query result keys: {result.keys()}")
        # 确保 result 是字典，并且包含 'data' 键
        if "data" in result and isinstance(result["data"], list):
            # 获取列名
            columns = [col[0] for col in result.get("column_meta", [])] if isinstance(result.get("column_meta"), list) else []
            for row in result["data"]:
                row_dict = dict(zip(columns, row))
                # 格式化时间戳
                if 'ts' in row_dict and isinstance(row_dict['ts'], int):
                    row_dict['ts'] = datetime.fromtimestamp(row_dict['ts'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                if 'weld_end_time' in row_dict and isinstance(row_dict['weld_end_time'], int):
                    row_dict['weld_end_time'] = datetime.fromtimestamp(row_dict['weld_end_time'] / 1000).strftime('%Y-%m-%d %H:%M:%S')

                data.append(row_dict)
        else:
            logger.warning("TDengine query result does not contain 'data' key or 'data' is not a list.")
    else:
        logger.warning("TDengine query result is not a dictionary or is empty.")

    # 手动分页
    total = len(data)
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_data = data[start_index:end_index]

    return SuccessExtra(total=total, data=paginated_data)