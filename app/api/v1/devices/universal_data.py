from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
import asyncio

from app.core.dependency import DependAuth
from app.models.device import DeviceType, DeviceField, DeviceInfo
from app.schemas import UniversalRealTimeDataQuery, UniversalRealTimeDataResponse

from app.core.response import success, fail
import logging

logger = logging.getLogger(__name__)
from app.core.tdengine_connector import TDengineConnector
from app.settings.config import settings

router = APIRouter()


async def build_dynamic_query(
    type_code: str,
    device_code: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 20,
    offset: int = 0
) -> tuple[str, List[str], List[str]]:
    """
    根据设备类型动态构建TDengine查询语句
    
    Returns:
        tuple: (sql_query, data_fields, tag_fields)
    """
    try:
        # 获取设备类型信息
        device_type = await DeviceType.get(type_code=type_code, is_active=True)
        stable_name = device_type.tdengine_stable_name
        
        # 获取字段定义
        fields = await DeviceField.filter(device_type_code=type_code).order_by('sort_order')
        
        # 分离数据字段和标签字段
        data_fields = []
        tag_fields = []
        
        for field in fields:
            # 由于DeviceField模型中没有is_tag字段，暂时将所有字段都作为数据字段处理
            # TODO: 需要在DeviceField模型中添加is_tag字段或使用其他方式区分标签字段和数据字段
            data_fields.append(field.field_name)
        
        # 构建SELECT子句
        select_fields = []
        # 添加标签字段
        for tag_field in tag_fields:
            select_fields.append(tag_field)
        # 添加数据字段
        for data_field in data_fields:
            select_fields.append(data_field)
        
        select_clause = ", ".join(select_fields) if select_fields else "*"
        
        # 构建WHERE子句
        where_conditions = []
        
        # 设备代码过滤
        if device_code:
            where_conditions.append(f"device_code = '{device_code}'")
        
        # 时间范围过滤
        if start_time:
            where_conditions.append(f"ts >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'")
        if end_time:
            where_conditions.append(f"ts <= '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # 构建完整查询
        sql_query = f"""
        SELECT {select_clause}
        FROM test_db.{stable_name}
        WHERE {where_clause}
        ORDER BY ts DESC
        LIMIT {limit} OFFSET {offset}
        """
        
        return sql_query, data_fields, tag_fields
    
    except Exception as e:
        logger.error(f"构建动态查询失败: {str(e)}")
        raise


async def execute_tdengine_query(sql_query: str) -> List[Dict[str, Any]]:
    """
    执行TDengine查询
    """
    try:
        # 从配置中获取TDengine连接参数
        tdengine_creds = settings.tortoise_orm.connections.tdengine.credentials
        connector = TDengineConnector(
            host=tdengine_creds.host,
            port=tdengine_creds.port,
            user=tdengine_creds.user,
            password=tdengine_creds.password,
            database=tdengine_creds.database
        )
        raw_result = await connector.execute_sql(sql_query)
        logger.info(f"TDengine原始响应: {raw_result}")
        
        # 解析TDengine REST API响应格式
        if isinstance(raw_result, dict):
            if 'data' in raw_result and 'column_meta' in raw_result:
                # TDengine REST API标准响应格式
                columns = [col[0] for col in raw_result['column_meta']]
                rows = raw_result['data']
                
                # 转换为字典列表格式
                result = []
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        if i < len(columns):
                            row_dict[columns[i]] = value
                    result.append(row_dict)
                return result
            else:
                logger.error(f"未知的TDengine响应格式: {raw_result}")
                return []
        else:
            logger.error(f"TDengine返回非字典类型: {type(raw_result)}")
            return []
        
    except Exception as e:
        logger.error(f"执行TDengine查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")


@router.get("/universal/realtime", summary="通用实时数据查询")
async def get_universal_realtime_data(
    query: UniversalRealTimeDataQuery = Depends(),
    user_id: int = DependAuth
):
    """
    通用实时数据查询接口，支持多设备类型
    """
    try:
        # 如果没有指定设备类型，返回所有可用的设备类型
        if not query.type_code:
            device_types = await DeviceType.filter(is_active=True).all()
            available_types = [
                {
                    "type_code": dt.type_code,
                    "type_name": dt.type_name,
                    "description": dt.description
                }
                for dt in device_types
            ]
            return success(data={
                "message": "请指定设备类型代码",
                "available_types": available_types
            })
        
        # 检查设备类型是否存在
        if not await DeviceType.filter(type_code=query.type_code, is_active=True).exists():
            return fail(msg=f"设备类型 {query.type_code} 不存在或未激活")
        
        # 计算分页参数
        offset = (query.page - 1) * query.page_size
        
        # 构建动态查询
        sql_query, data_fields, tag_fields = await build_dynamic_query(
            type_code=query.type_code,
            device_code=query.device_code,
            start_time=query.start_time,
            end_time=query.end_time,
            limit=query.page_size,
            offset=offset
        )
        
        logger.info(f"执行查询: {sql_query}")
        
        # 执行查询
        raw_data = await execute_tdengine_query(sql_query)
        
        # 转换为标准响应格式
        result = []
        for row in raw_data:
            # 分离标签和数据字段
            tags = {}
            data = {}
            
            device_code_val = None
            ts_val = None
            
            for field_name, value in row.items():
                if field_name == 'device_code':
                    device_code_val = value
                elif field_name == 'ts':
                    ts_val = value
                elif field_name in tag_fields:
                    tags[field_name] = value
                elif field_name in data_fields:
                    data[field_name] = value
            
            # 获取设备名称
            device_name = None
            if device_code_val:
                try:
                    device_info = await DeviceInfo.get(device_code=device_code_val)
                    device_name = device_info.device_name
                except:
                    device_name = tags.get('name', device_code_val)
            
            response_item = UniversalRealTimeDataResponse(
                device_code=device_code_val or "unknown",
                device_name=device_name,
                type_code=query.type_code,
                ts=ts_val or datetime.now(),
                data=data,
                tags=tags
            )
            result.append(response_item)
        
        return success(data={
            "items": result,
            "total": len(result),
            "page": query.page,
            "page_size": query.page_size,
            "type_code": query.type_code
        })
    
    except Exception as e:
        logger.error(f"通用实时数据查询失败: {str(e)}")
        return fail(msg=f"查询失败: {str(e)}")


@router.get("/universal/latest/{type_code}", summary="获取指定类型设备的最新数据")
async def get_latest_data_by_type(
    type_code: str,
    device_code: Optional[str] = Query(None, description="设备编号，不指定则获取该类型所有设备"),
    user_id: int = DependAuth
):
    """
    获取指定设备类型的最新数据
    """
    try:
        # 检查设备类型是否存在
        if not await DeviceType.filter(type_code=type_code, is_active=True).exists():
            return fail(msg=f"设备类型 {type_code} 不存在或未激活")
        
        # 构建查询（获取最新数据）
        sql_query, data_fields, tag_fields = await build_dynamic_query(
            type_code=type_code,
            device_code=device_code,
            limit=1 if device_code else 50,  # 单设备获取1条，多设备获取50条
            offset=0
        )
        
        # 如果是查询所有设备，需要按设备分组获取最新数据
        if not device_code:
            device_type = await DeviceType.get(type_code=type_code)
            stable_name = device_type.tdengine_stable_name
            
            # 构建子查询获取每个设备的最新时间戳
            sql_query = f"""
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY device_code ORDER BY ts DESC) as rn
                FROM test_db.{stable_name}
            ) t WHERE rn = 1
            ORDER BY ts DESC
            LIMIT 50
            """
        
        logger.info(f"执行最新数据查询: {sql_query}")
        
        # 执行查询
        raw_data = await execute_tdengine_query(sql_query)
        
        # 转换为标准响应格式
        result = []
        for row in raw_data:
            # 分离标签和数据字段
            tags = {}
            data = {}
            
            device_code_val = None
            ts_val = None
            
            for field_name, value in row.items():
                if field_name == 'device_code':
                    device_code_val = value
                elif field_name == 'ts':
                    ts_val = value
                elif field_name == 'rn':  # 跳过ROW_NUMBER字段
                    continue
                elif field_name in tag_fields:
                    tags[field_name] = value
                elif field_name in data_fields:
                    data[field_name] = value
            
            # 获取设备名称
            device_name = None
            if device_code_val:
                try:
                    device_info = await DeviceInfo.get(device_code=device_code_val)
                    device_name = device_info.device_name
                except:
                    device_name = tags.get('name', device_code_val)
            
            response_item = UniversalRealTimeDataResponse(
                device_code=device_code_val or "unknown",
                device_name=device_name,
                type_code=type_code,
                ts=ts_val or datetime.now(),
                data=data,
                tags=tags
            )
            result.append(response_item)
        
        return success(data={
            "items": result,
            "total": len(result),
            "type_code": type_code,
            "query_time": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"获取最新数据失败: {str(e)}")
        return fail(msg=f"获取最新数据失败: {str(e)}")


@router.get("/universal/statistics/{type_code}", summary="获取设备类型统计信息")
async def get_device_type_statistics(
    type_code: str,
    user_id: int = DependAuth
):
    """
    获取指定设备类型的统计信息
    """
    try:
        # 检查设备类型是否存在
        device_type = await DeviceType.filter(type_code=type_code, is_active=True).first()
        if not device_type:
            return fail(msg=f"设备类型 {type_code} 不存在或未激活")
        
        # 统计设备数量
        total_devices = await DeviceInfo.filter(device_type=type_code).count()
        locked_devices = await DeviceInfo.filter(device_type=type_code, is_locked=True).count()
        
        # 获取字段定义统计
        total_fields = await DeviceField.filter(device_type_code=type_code).count()
        # 由于DeviceField模型中没有is_tag字段，暂时设置tag_fields为0
        # TODO: 需要在DeviceField模型中添加is_tag字段
        tag_fields = 0
        data_fields = total_fields - tag_fields
        
        # 构建统计查询获取在线设备数量
        try:
            stable_name = device_type.tdengine_stable_name
            # 获取最近5分钟有数据的设备数量作为在线设备
            recent_time = datetime.now() - timedelta(minutes=5)
            online_query = f"""
            SELECT COUNT(DISTINCT device_code) as online_count
            FROM test_db.{stable_name}
            WHERE ts >= '{recent_time.strftime('%Y-%m-%d %H:%M:%S')}'
            """
            
            online_result = await execute_tdengine_query(online_query)
            online_devices = online_result[0]['online_count'] if online_result else 0
        except:
            online_devices = 0
        
        result = {
            "type_info": {
                "type_code": device_type.type_code,
                "type_name": device_type.type_name,
                "tdengine_stable_name": device_type.tdengine_stable_name,
                "description": device_type.description
            },
            "device_statistics": {
                "total_devices": total_devices,
                "online_devices": online_devices,
                "offline_devices": total_devices - online_devices,
                "locked_devices": locked_devices,
                "unlocked_devices": total_devices - locked_devices
            },
            "field_statistics": {
                "total_fields": total_fields,
                "tag_fields": tag_fields,
                "data_fields": data_fields
            },
            "query_time": datetime.now().isoformat()
        }
        
        return success(data=result)
    
    except Exception as e:
        logger.error(f"获取设备类型统计失败: {str(e)}")
        return fail(msg=f"获取统计信息失败: {str(e)}")