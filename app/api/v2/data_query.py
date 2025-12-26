# -*- coding: utf-8 -*-
"""
数据查询 API

功能：
1. 实时数据查询
2. 统计聚合数据查询
3. 数据导出

作者：AI Assistant
日期：2025-11-03
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Query, Body
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from app.services.data_query_service import data_query_service
from app.core.dependency import DependAuth
from app.models.admin import User
from app.core.response_formatter_v2 import create_formatter
from app.core.exceptions import APIException
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data", tags=["数据查询"])


# =====================================================================
# Pydantic Schema 定义
# =====================================================================

class RealtimeQueryRequest(BaseModel):
    """实时数据查询请求"""
    model_code: str = Field(..., description="模型代码")
    device_code: Optional[str] = Field(None, description="设备编码")
    filters: Optional[dict] = Field(None, description="额外筛选条件")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    order_by: Optional[str] = Field(None, description="排序字段")
    order_direction: str = Field('desc', description="排序方向 (asc/desc)")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(100, ge=1, le=1000, description="每页记录数")
    apply_transform: bool = Field(True, description="是否应用数据转换")


class StatisticsQueryRequest(BaseModel):
    """统计数据查询请求"""
    model_code: str = Field(..., description="模型代码")
    device_code: Optional[str] = Field(None, description="设备编码")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    group_by: Optional[List[str]] = Field(None, description="分组字段")
    interval: Optional[str] = Field(None, description="时间间隔 (如 '1h', '5m', '1d')")
    apply_transform: bool = Field(True, description="是否应用数据转换")


# =====================================================================
# API 接口
# =====================================================================

@router.post("/query/realtime", summary="查询实时数据")
async def query_realtime_data(
    request: Request,
    query_request: RealtimeQueryRequest,
    current_user: User = DependAuth
):
    """
    查询实时数据
    
    **功能说明**:
    - 根据数据模型配置查询 TDengine 实时数据
    - 支持设备筛选、时间范围、条件筛选
    - 支持分页、排序
    - 自动应用数据转换规则
    
    **使用场景**:
    - 实时监控大屏
    - 设备数据查看
    - 历史数据回溯
    
    **请求体示例**:
    ```json
    {
      "model_code": "welding_realtime_v1",
      "device_code": "14323A0032",
      "start_time": "2025-11-01T00:00:00",
      "end_time": "2025-11-01T23:59:59",
      "page": 1,
      "page_size": 100,
      "apply_transform": true
    }
    ```
    
    **返回示例**:
    ```json
    {
      "code": 200,
      "data": {
        "data": [
          {
            "ts": "2025-11-01T10:00:00",
            "prod_code": "14323A0032",
            "avg_current": 250.5,
            "avg_voltage": 32.0
          }
        ],
        "total": 1523,
        "page": 1,
        "page_size": 100,
        "total_pages": 16,
        "execution_time_ms": 235
      }
    }
    ```
    """
    formatter = create_formatter(request)
    
    try:
        # Extract start_time and end_time from filters if not provided in top-level
        # Frontend sends time range in filters, but backend expects them as top-level fields
        start_time = query_request.start_time
        end_time = query_request.end_time
        filters = query_request.filters or {}
        
        if not start_time and 'start_time' in filters:
            try:
                time_str = str(filters.pop('start_time')).replace('Z', '+00:00')
                # Convert UTC to local time (naive) for TDengine
                start_time = datetime.fromisoformat(time_str).astimezone().replace(tzinfo=None)
            except Exception as e:
                logger.warning(f"Failed to parse start_time from filters: {e}")
                
        if not end_time and 'end_time' in filters:
            try:
                time_str = str(filters.pop('end_time')).replace('Z', '+00:00')
                # Convert UTC to local time (naive) for TDengine
                end_time = datetime.fromisoformat(time_str).astimezone().replace(tzinfo=None)
            except Exception as e:
                logger.warning(f"Failed to parse end_time from filters: {e}")

        logger.info(
            f"[数据查询API] 实时数据查询: model={query_request.model_code}, "
            f"device={query_request.device_code}, "
            f"start_time={start_time}, end_time={end_time}"
        )
        
        # 调用数据查询服务
        result = await data_query_service.query_realtime_data(
            model_code=query_request.model_code,
            device_code=query_request.device_code,
            filters=filters,
            start_time=start_time,
            end_time=end_time,
            order_by=query_request.order_by,
            order_direction=query_request.order_direction,
            page=query_request.page,
            page_size=query_request.page_size,
            apply_transform=query_request.apply_transform,
            log_execution=True
        )
        
        logger.info(f"[API] Realtime Query Result: total={result['total']}, rows={len(result['data'])}")

        # Custom response format to match frontend expectations (Flattened Structure)
        # Frontend expects response.data to be an array and response.total to be at top level
        # We also add 'meta' for compatibility with different frontend versions
        return JSONResponse(content=jsonable_encoder({
            "code": 200,
            "success": True,
            "data": result['data'],
            "total": result['total'],
            "meta": {
                "total": result['total'],
                "page": result['page'],
                "page_size": result['page_size']
            },
            "page": result['page'],
            "page_size": result['page_size'],
            "message": f"查询成功，共 {result['total']} 条记录，耗时 {result['execution_time_ms']} ms",
            "generated_sql": result.get('generated_sql')
        }))
        
        # return formatter.paginated_success(
        #     data=result['data'],
        #     total=result['total'],
        #     page=result['page'],
        #     page_size=result['page_size'],
        #     message=f"查询成功，共 {result['total']} 条记录，耗时 {result['execution_time_ms']} ms",
        #     generated_sql=result.get('generated_sql')
        # )
        
    except APIException as e:
        logger.error(f"[数据查询API] 实时数据查询失败: {e.message}")
        # Fix: APIException has error_code, not error_type
        error_code = getattr(e, 'error_code', getattr(e, 'error_type', 'API_ERROR'))
        return formatter.error(message=e.message, code=e.code, error_type=error_code)
    except Exception as e:
        logger.error(f"[数据查询API] 实时数据查询异常: {e}", exc_info=True)
        return formatter.internal_error(f"查询实时数据失败: {str(e)}")


@router.post("/query/statistics", summary="查询统计数据")
async def query_statistics_data(
    request: Request,
    query_request: StatisticsQueryRequest,
    current_user: User = DependAuth
):
    """
    查询统计聚合数据
    
    **功能说明**:
    - 根据数据模型配置查询 TDengine 统计聚合数据
    - 支持时间窗口聚合 (INTERVAL)
    - 支持分组聚合 (GROUP BY)
    - 支持多种聚合函数 (AVG, SUM, MAX, MIN, COUNT)
    
    **使用场景**:
    - 设备运行趋势分析
    - 性能指标统计
    - 报表生成
    
    **请求体示例**:
    ```json
    {
      "model_code": "welding_statistics_daily_v1",
      "device_code": "14323A0032",
      "start_time": "2025-11-01T00:00:00",
      "end_time": "2025-11-01T23:59:59",
      "interval": "1h",
      "group_by": ["prod_code"],
      "apply_transform": true
    }
    ```
    
    **返回示例**:
    ```json
    {
      "code": 200,
      "data": {
        "data": [
          {
            "window_start": "2025-11-01T00:00:00",
            "window_end": "2025-11-01T01:00:00",
            "prod_code": "14323A0032",
            "avg_current_avg": 245.3,
            "avg_voltage_avg": 31.8
          }
        ],
        "total": 24,
        "execution_time_ms": 189,
        "aggregation_info": {
          "interval": "1h",
          "group_by": ["prod_code"],
          "methods": ["avg"]
        }
      }
    }
    ```
    """
    formatter = create_formatter(request)
    
    try:
        logger.info(
            f"[数据查询API] 统计数据查询: model={query_request.model_code}, "
            f"interval={query_request.interval}"
        )
        
        # 调用数据查询服务
        result = await data_query_service.query_statistics_data(
            model_code=query_request.model_code,
            device_code=query_request.device_code,
            start_time=query_request.start_time,
            end_time=query_request.end_time,
            group_by=query_request.group_by,
            interval=query_request.interval,
            apply_transform=query_request.apply_transform,
            log_execution=True
        )
        
        return formatter.success(
            data=result,
            message=f"统计查询成功，共 {result['total']} 条记录，耗时 {result['execution_time_ms']} ms",
            generated_sql=result.get('generated_sql')
        )
        
    except APIException as e:
        logger.error(f"[数据查询API] 统计数据查询失败: {e.message}")
        return formatter.error(message=e.message, code=e.code, error_type=e.error_type)
    except Exception as e:
        logger.error(f"[数据查询API] 统计数据查询异常: {e}", exc_info=True)
        return formatter.internal_error(f"查询统计数据失败: {str(e)}")


@router.get("/models/{model_code}/preview", summary="预览数据模型")
async def preview_model_data(
    request: Request,
    model_code: str,
    device_code: Optional[str] = Query(None, description="设备编码"),
    limit: int = Query(10, ge=1, le=100, description="预览记录数"),
    current_user: User = DependAuth
):
    """
    预览数据模型的最新数据
    
    **功能说明**:
    - 快速预览模型的最新数据（前N条）
    - 用于模型配置测试和验证
    - 不记录执行日志
    
    **使用场景**:
    - 模型配置后的测试
    - 数据模型预览
    
    **返回示例**:
    ```json
    {
      "code": 200,
      "data": {
        "data": [...],
        "total": 10,
        "model_info": {
          "model_code": "welding_realtime_v1",
          "model_name": "焊接设备实时监控模型"
        }
      }
    }
    ```
    """
    formatter = create_formatter(request)
    
    try:
        logger.info(f"[数据查询API] 预览模型数据: model={model_code}, limit={limit}")
        
        # 调用数据查询服务（不记录日志）
        result = await data_query_service.query_realtime_data(
            model_code=model_code,
            device_code=device_code,
            page=1,
            page_size=limit,
            order_direction='desc',
            apply_transform=True,
            log_execution=False  # 预览不记录日志
        )
        
        return formatter.success(
            data={
                'data': result['data'],
                'total': len(result['data']),
                'model_info': result['model_info']
            },
            message=f"预览成功，返回 {len(result['data'])} 条记录",
            generated_sql=result.get('generated_sql')
        )
        
    except APIException as e:
        logger.error(f"[数据查询API] 预览模型数据失败: {e.message}")
        return formatter.error(message=e.message, code=e.code, error_type=e.error_type)
    except Exception as e:
        logger.error(f"[数据查询API] 预览模型数据异常: {e}", exc_info=True)
        return formatter.internal_error(f"预览数据失败: {str(e)}")


@router.get("/models/list", summary="获取可用数据模型列表")
async def list_available_models(
    request: Request,
    device_type_code: Optional[str] = Query(None, description="设备类型代码"),
    model_type: Optional[str] = Query(None, description="模型类型"),
    current_user: User = DependAuth
):
    """
    获取可用的数据模型列表
    
    **功能说明**:
    - 查询激活状态的数据模型
    - 支持按设备类型和模型类型筛选
    - 返回模型基本信息
    
    **返回示例**:
    ```json
    {
      "code": 200,
      "data": [
        {
          "model_code": "welding_realtime_v1",
          "model_name": "焊接设备实时监控模型",
          "model_type": "realtime",
          "device_type_code": "welding",
          "is_default": true,
          "version": "1.0"
        }
      ]
    }
    ```
    """
    formatter = create_formatter(request)
    
    try:
        from app.models.device import DeviceDataModel
        
        logger.info(
            f"[数据查询API] 获取模型列表: device_type={device_type_code}, "
            f"model_type={model_type}"
        )
        
        # 查询数据模型
        query = DeviceDataModel.filter(is_active=True)
        
        if device_type_code:
            query = query.filter(device_type_code=device_type_code)
        
        if model_type:
            query = query.filter(model_type=model_type)
        
        models = await query.order_by('-is_default', 'model_code')
        
        # 构建返回数据
        model_list = [
            {
                'id': model.id,
                'model_code': model.model_code,
                'model_name': model.model_name,
                'model_type': model.model_type,
                'device_type_code': model.device_type_code,
                'is_default': model.is_default,
                'version': model.version,
                'description': model.description,
                'fields_count': len(model.selected_fields) if model.selected_fields else 0,
                'selected_fields': model.selected_fields  # Fix: Return selected_fields for frontend
            }
            for model in models
        ]
        
        return formatter.success(
            data=model_list,
            message=f"获取模型列表成功，共 {len(model_list)} 个模型"
        )
        
    except Exception as e:
        logger.error(f"[数据查询API] 获取模型列表异常: {e}", exc_info=True)
        return formatter.internal_error(f"获取模型列表失败: {str(e)}")

