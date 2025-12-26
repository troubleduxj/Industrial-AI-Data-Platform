# -*- coding: utf-8 -*-
"""
数据查询服务

功能：
1. 根据数据模型查询 TDengine 数据
2. 整合动态模型、SQL构建器、数据转换引擎
3. 支持实时数据查询、统计聚合查询
4. 记录执行日志

作者：AI Assistant
日期：2025-11-03
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import time
import json
from tortoise import Tortoise
from app.models.device import DeviceDataModel, ModelExecutionLog
from app.services.dynamic_model_service import dynamic_model_service
from app.services.sql_builder import sql_builder
from app.services.transform_engine import transform_engine
from app.core.tdengine_connector import TDengineConnector
from app.core.dependency import get_tdengine_connector
from app.core.exceptions import APIException
from app.settings.config import settings
import logging

logger = logging.getLogger(__name__)


class DataQueryService:
    """
    数据查询服务
    
    核心功能：
    - 根据数据模型配置查询 TDengine 数据
    - 支持实时数据查询（realtime）
    - 支持统计聚合查询（statistics）
    - 应用数据转换规则
    - 记录执行日志
    """
    
    def __init__(self):
        """初始化服务"""
        self.tdengine_connector: Optional[TDengineConnector] = None
    
    async def query_realtime_data(
        self,
        model_code: str,
        device_code: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        order_by: Optional[str] = None,
        order_direction: str = 'desc',
        page: int = 1,
        page_size: int = 100,
        apply_transform: bool = True,
        log_execution: bool = True
    ) -> Dict[str, Any]:
        """
        查询实时数据
        
        Args:
            model_code: 模型代码
            device_code: 设备编码（可选）
            filters: 额外筛选条件
            start_time: 开始时间
            end_time: 结束时间
            order_by: 排序字段
            order_direction: 排序方向 (asc/desc)
            page: 页码
            page_size: 每页记录数
            apply_transform: 是否应用数据转换
            log_execution: 是否记录执行日志
        
        Returns:
            查询结果字典
        """
        start_exec_time = time.time()
        
        # Fix: Strip whitespace from input parameters to prevent copy-paste errors
        if model_code:
            model_code = model_code.strip()
        if device_code:
            device_code = device_code.strip()
        
        # Debug Log: Capture incoming request parameters
        logger.info(
            f"[DEBUG_REQUEST] query_realtime_data params: "
            f"model={model_code}, device={device_code}, "
            f"start={start_time}, end={end_time}, "
            f"page={page}, size={page_size}"
        )
        
        try:
            # 1. 查询数据模型配置
            data_model = await DeviceDataModel.filter(
                model_code=model_code,
                is_active=True
            ).first()
            
            if not data_model:
                raise APIException(
                    code=404,
                    message=f"数据模型不存在或未激活: {model_code}"
                )
            
            if data_model.model_type != 'realtime':
                raise APIException(
                    code=400,
                    message=f"模型类型错误，期望 'realtime'，实际 '{data_model.model_type}'"
                )
            
            # 2. 构建查询 SQL
            offset = (page - 1) * page_size
            sql_result = await sql_builder.build_query_sql(
                model_config=data_model,
                device_code=device_code,
                filters=filters,
                start_time=start_time,
                end_time=end_time,
                order_by=order_by,
                order_direction=order_direction,
                limit=page_size,
                offset=offset
            )
            
            query_sql = sql_result['sql']
            count_sql = sql_result['row_count_sql']
            
            # 3. 执行查询
            # 获取 TDengine 连接器
            if not self.tdengine_connector:
                self.tdengine_connector = await get_tdengine_connector()
            
            # Fix: Use query_data with explicit database name to ensure correct context
            db_name = settings.TDENGINE_DATABASE
            
            # 查询总记录数
            # Fix: Use query_data instead of execute_query and parse response
            count_res = await self.tdengine_connector.query_data(count_sql, db_name=db_name)
            count_result = self._parse_tdengine_response(count_res)
            total_count = count_result[0]['total'] if count_result else 0
            
            # 查询数据
            raw_res = await self.tdengine_connector.query_data(query_sql, db_name=db_name)
            raw_data = self._parse_tdengine_response(raw_res)
            
            # 4. 应用数据转换
            transformed_data = []
            if apply_transform and raw_data:
                # 获取字段映射
                field_mappings = await self._get_field_mappings(
                    data_model.device_type_code,
                    data_model.selected_fields
                )
                
                for row in raw_data:
                    transformed_row = transform_engine.batch_transform(
                        data=row,
                        field_mappings=field_mappings
                    )
                    # 保留原始的时间戳和设备编码
                    transformed_row['ts'] = row.get('ts')
                    # Fix: Support dynamic device identifier (device_id, device_code, or prod_code)
                    transformed_row['prod_code'] = row.get('prod_code') or row.get('device_id') or row.get('device_code')
                    # Also ensure explicit keys are present if available
                    if 'device_id' in row:
                        transformed_row['device_id'] = row['device_id']
                    if 'device_code' in row:
                        transformed_row['device_code'] = row['device_code']
                    
                    transformed_data.append(transformed_row)
            else:
                transformed_data = raw_data
            
            # 5. 计算执行时间
            exec_time_ms = int((time.time() - start_exec_time) * 1000)
            
            # 7. 记录执行日志
            await self._log_execution(
                model_id=data_model.id,
                execution_type='query',
                input_params={
                    'model_code': model_code,
                    'device_code': device_code,
                    'filters': filters,
                    'start_time': start_time.isoformat() if start_time else None,
                    'end_time': end_time.isoformat() if end_time else None,
                    'page': page,
                    'page_size': page_size
                },
                status='success',
                result_summary={
                    'total_rows': total_count,
                    'returned_rows': len(transformed_data),
                    'transformed': apply_transform
                },
                execution_time_ms=exec_time_ms,
                data_volume=len(transformed_data),
                generated_sql=query_sql
            )
            
            logger.info(
                f"[数据查询] 查询成功: {len(transformed_data)} 行数据，"
                f"共 {total_count} 条记录，耗时 {exec_time_ms} ms"
            )
            
            # 7. 返回结果
            return {
                'data': transformed_data,
                'total': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size,
                'execution_time_ms': exec_time_ms,
                'generated_sql': query_sql,
                'model_info': {
                    'model_code': data_model.model_code,
                    'model_name': data_model.model_name,
                    'version': data_model.version
                }
            }
            
        except APIException as e:
            # 记录失败日志
            if log_execution:
                await self._log_execution(
                    model_id=data_model.id if 'data_model' in locals() else None,
                    execution_type='query',
                    input_params={
                        'model_code': model_code,
                        'device_code': device_code
                    },
                    status='failed',
                    error_message=e.message,
                    execution_time_ms=int((time.time() - start_exec_time) * 1000)
                )
            raise e
            
        except Exception as e:
            logger.error(f"[数据查询] 查询失败: {e}", exc_info=True)
            # 记录失败日志
            if log_execution:
                await self._log_execution(
                    model_id=data_model.id if 'data_model' in locals() else None,
                    execution_type='query',
                    input_params={
                        'model_code': model_code,
                        'device_code': device_code
                    },
                    status='failed',
                    error_message=str(e),
                    execution_time_ms=int((time.time() - start_exec_time) * 1000)
                )
            raise APIException(
                code=500,
                message=f"数据查询失败: {str(e)}"
            )
    
    async def query_statistics_data(
        self,
        model_code: str,
        device_code: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        group_by: Optional[List[str]] = None,
        interval: Optional[str] = None,
        apply_transform: bool = True,
        log_execution: bool = True
    ) -> Dict[str, Any]:
        """
        查询统计聚合数据
        
        Args:
            model_code: 模型代码
            device_code: 设备编码（可选）
            start_time: 开始时间
            end_time: 结束时间
            group_by: 分组字段
            interval: 时间间隔 (如 '1h', '5m', '1d')
            apply_transform: 是否应用数据转换
            log_execution: 是否记录执行日志
        
        Returns:
            统计结果字典
        """
        start_exec_time = time.time()
        
        logger.info(
            f"[数据查询] 统计数据查询: model={model_code}, device={device_code}, "
            f"interval={interval}"
        )
        
        try:
            # 1. 查询数据模型配置
            data_model = await DeviceDataModel.filter(
                model_code=model_code,
                is_active=True
            ).first()
            
            if not data_model:
                raise APIException(
                    code=404,
                    message=f"数据模型不存在或未激活: {model_code}"
                )
            
            if data_model.model_type not in ['statistics', 'ai_analysis']:
                raise APIException(
                    code=400,
                    message=f"模型类型错误，期望 'statistics' 或 'ai_analysis'，实际 '{data_model.model_type}'"
                )
            
            # 2. 构建聚合查询 SQL
            sql_result = await sql_builder.build_aggregation_sql(
                model_config=data_model,
                device_code=device_code,
                start_time=start_time,
                end_time=end_time,
                group_by=group_by,
                interval=interval
            )
            
            query_sql = sql_result['sql']
            
            # 3. 执行查询
            if not self.tdengine_connector:
                self.tdengine_connector = await get_tdengine_connector()
            
            # Fix: Use query_data with explicit database name
            db_name = settings.TDENGINE_DATABASE

            # Fix: Use query_data instead of execute_query and parse response
            raw_res = await self.tdengine_connector.query_data(query_sql, db_name=db_name)
            raw_data = self._parse_tdengine_response(raw_res)
            
            # 4. 应用数据转换（如果需要）
            transformed_data = []
            if apply_transform and raw_data:
                # 获取字段映射
                field_mappings = await self._get_field_mappings(
                    data_model.device_type_code,
                    data_model.selected_fields
                )
                
                for row in raw_data:
                    transformed_row = transform_engine.batch_transform(
                        data=row,
                        field_mappings=field_mappings
                    )
                    # 保留时间窗口和分组字段
                    if 'window_start' in row:
                        transformed_row['window_start'] = row['window_start']
                    if 'window_end' in row:
                        transformed_row['window_end'] = row['window_end']
                    
                    # Fix: Support dynamic device identifier
                    transformed_row['prod_code'] = row.get('prod_code') or row.get('device_id') or row.get('device_code')
                    
                    transformed_data.append(transformed_row)
            else:
                transformed_data = raw_data
            
            # 5. 计算执行时间
            exec_time_ms = int((time.time() - start_exec_time) * 1000)
            
            # 6. 记录执行日志
            if log_execution:
                await self._log_execution(
                    model_id=data_model.id,
                    execution_type='query',
                    input_params={
                        'model_code': model_code,
                        'device_code': device_code,
                        'start_time': start_time.isoformat() if start_time else None,
                        'end_time': end_time.isoformat() if end_time else None,
                        'interval': interval,
                        'group_by': group_by
                    },
                    status='success',
                    result_summary={
                        'total_rows': len(transformed_data),
                        'aggregation_type': 'statistics',
                        'interval': interval,
                        'transformed': apply_transform
                    },
                    execution_time_ms=exec_time_ms,
                    data_volume=len(transformed_data),
                    generated_sql=query_sql
                )
            
            logger.info(
                f"[数据查询] 统计查询成功: {len(transformed_data)} 行数据，"
                f"耗时 {exec_time_ms} ms"
            )
            
            # 7. 返回结果
            return {
                'data': transformed_data,
                'total': len(transformed_data),
                'execution_time_ms': exec_time_ms,
                'generated_sql': query_sql,
                'aggregation_info': {
                    'interval': interval,
                    'group_by': group_by,
                    'methods': sql_result.get('aggregation_methods', [])
                },
                'model_info': {
                    'model_code': data_model.model_code,
                    'model_name': data_model.model_name,
                    'version': data_model.version
                }
            }
            
        except APIException as e:
            # 记录失败日志
            if log_execution:
                await self._log_execution(
                    model_id=data_model.id if 'data_model' in locals() else None,
                    execution_type='query',
                    input_params={
                        'model_code': model_code,
                        'device_code': device_code
                    },
                    status='failed',
                    error_message=e.message,
                    execution_time_ms=int((time.time() - start_exec_time) * 1000)
                )
            raise e
            
        except Exception as e:
            logger.error(f"[数据查询] 统计查询失败: {e}", exc_info=True)
            # 记录失败日志
            if log_execution:
                await self._log_execution(
                    model_id=data_model.id if 'data_model' in locals() else None,
                    execution_type='query',
                    input_params={
                        'model_code': model_code,
                        'device_code': device_code
                    },
                    status='failed',
                    error_message=str(e),
                    execution_time_ms=int((time.time() - start_exec_time) * 1000)
                )
            raise APIException(
                code=500,
                message=f"统计查询失败: {str(e)}"
            )
    
    async def _get_field_mappings(
        self,
        device_type_code: str,
        selected_fields: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        获取字段映射信息（复用 SQL Builder 的逻辑）
        
        Args:
            device_type_code: 设备类型代码
            selected_fields: 选中的字段配置
        
        Returns:
            字段映射信息列表
        """
        return await sql_builder._get_field_mappings(device_type_code, selected_fields)
    
    def _parse_tdengine_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析 TDengine 响应格式为字典列表
        """
        # TDengine response success code is 0
        if not response:
            return []
            
        # Check 'code' (0 is success) OR 'status' ('succ') for compatibility
        is_success = (response.get('code') == 0) or (response.get('status') == 'succ')
        if not is_success:
            return []
        
        head = response.get('column_meta', []) # New format uses column_meta? Or head?
        # Check which key is used for columns
        columns = []
        if 'column_meta' in response:
             columns = [col[0] for col in response['column_meta']]
        elif 'head' in response:
             columns = response['head']
        else:
             return []

        data = response.get('data', [])
        
        result = []
        for row in data:
            item = {}
            for i, field in enumerate(columns):
                if i < len(row):
                    item[field] = row[i]
            result.append(item)
        return result

    async def _log_execution(
        self,
        model_id: Optional[int],
        execution_type: str,
        input_params: Dict[str, Any],
        status: str,
        result_summary: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        data_volume: Optional[int] = None,
        generated_sql: Optional[str] = None
    ):
        """
        记录执行日志
        
        Args:
            model_id: 模型ID
            execution_type: 执行类型
            input_params: 输入参数
            status: 执行状态
            result_summary: 结果摘要
            error_message: 错误信息
            execution_time_ms: 执行时间（毫秒）
            data_volume: 数据量
            generated_sql: 生成的SQL
        """
        if not model_id:
            return
        
        try:
            conn = Tortoise.get_connection("default")
            
            # Use raw SQL to bypass Tortoise timezone handling issues
            sql = """
                INSERT INTO "t_model_execution_log" 
                ("model_id", "execution_type", "input_params", "status", "result_summary", 
                 "error_message", "execution_time_ms", "data_volume", "generated_sql", 
                 "executed_at")
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """
            
            # Use naive local time which works with asyncpg when passed directly
            executed_at = datetime.now().replace(microsecond=0)
            
            await conn.execute_query(
                sql,
                [
                    model_id,
                    execution_type,
                    json.dumps(input_params, default=str) if input_params else None,
                    status,
                    json.dumps(result_summary, default=str) if result_summary else None,
                    error_message,
                    execution_time_ms,
                    data_volume,
                    generated_sql,
                    executed_at
                ]
            )
            
        except Exception as e:
            logger.error(f"[数据查询] 记录执行日志失败: {e}", exc_info=True)


# 创建全局实例
data_query_service = DataQueryService()

