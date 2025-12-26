# -*- coding: utf-8 -*-
"""
SQL 动态构建器

功能：
1. 根据数据模型配置动态生成 TDengine SQL
2. 支持基础查询、聚合查询、条件筛选
3. 支持分页、排序
4. SQL 防注入处理

作者：AI Assistant
日期：2025-11-03
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from app.core.exceptions import APIException
from app.models.device import DeviceDataModel, DeviceField, DeviceType, DeviceFieldMapping
from app.settings.config import settings
import logging

logger = logging.getLogger(__name__)
import re


class SQLBuilder:
    """
    SQL 动态构建器 (Refactored)
    
    核心功能：
    - 根据 DeviceType 和 DeviceField 配置动态生成 TDengine SQL
    - 移除对 DeviceFieldMapping 的依赖
    - 仅支持 SELECT 查询 (只读模式)
    """
    
    # 允许的聚合函数
    ALLOWED_AGG_FUNCTIONS = {'avg', 'sum', 'max', 'min', 'count', 'first', 'last'}
    
    # 允许的比较运算符
    ALLOWED_OPERATORS = {'=', '>', '<', '>=', '<=', '!=', '<>', 'like', 'in', 'between'}
    
    # 允许的排序方向
    ALLOWED_ORDER_DIRECTIONS = {'asc', 'desc'}
    
    async def build_query_sql(
        self,
        model_config: DeviceDataModel,
        device_code: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        order_by: Optional[str] = None,
        order_direction: str = 'desc',
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        构建基础查询 SQL
        """
        logger.info(f"[SQL构建器] 构建查询SQL: model={model_config.model_code}, device={device_code}")
        
        # 1. 获取字段映射
        field_mappings = await self._get_field_mappings(
            model_config.device_type_code,
            model_config.selected_fields
        )
        
        if not field_mappings:
            raise APIException(
                code=400,
                message=f"数据模型 '{model_config.model_code}' 没有有效的字段映射"
            )
        
        # 2. 确定 TDengine 数据库和超级表
        tdengine_database = field_mappings[0]['tdengine_database']
        tdengine_stable = field_mappings[0]['tdengine_stable']
        
        # 3. 构建 SELECT 子句
        select_columns = []
        for mapping in field_mappings:
            column = mapping['tdengine_column']
            if not re.match(r'^[a-zA-Z0-9_]+$', column):
                continue
            select_columns.append(column)
        
        if 'ts' not in select_columns:
            select_columns.insert(0, 'ts')
        
        # 动态获取设备标识字段
        identifier_mapping = await self._get_identifier_mapping(model_config.device_type_code)
        if identifier_mapping:
             device_id_col = identifier_mapping['tdengine_column']
        else:
             # Fallback to previous logic (check selected fields or default to prod_code)
             device_id_col = self._get_device_identifier_column(field_mappings)

        if device_id_col not in select_columns:
            select_columns.insert(1, device_id_col)
        
        select_clause = f"SELECT {', '.join(select_columns)}"
        
        # 4. 构建 FROM 子句
        from_clause = f"FROM {tdengine_database}.{tdengine_stable}"
        
        # 5. 构建 WHERE 子句
        where_conditions = []
        
        if device_code:
            where_conditions.append(f"{device_id_col} = '{self._escape_sql_string(device_code)}'")
        
        if start_time:
            start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            where_conditions.append(f"ts >= '{start_time_str}'")
        
        if end_time:
            end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            where_conditions.append(f"ts <= '{end_time_str}'")
        
        # 额外筛选条件
        if filters:
            for field, value in filters.items():
                if not re.match(r'^[a-zA-Z0-9_]+$', field):
                    continue
                
                if isinstance(value, (int, float)):
                    where_conditions.append(f"{field} = {value}")
                elif isinstance(value, str):
                    where_conditions.append(f"{field} = '{self._escape_sql_string(value)}'")
                elif isinstance(value, dict):
                    if 'min' in value:
                        where_conditions.append(f"{field} >= {value['min']}")
                    if 'max' in value:
                        where_conditions.append(f"{field} <= {value['max']}")
                elif isinstance(value, list):
                    escaped_values = [f"'{self._escape_sql_string(str(v))}'" for v in value]
                    where_conditions.append(f"{field} IN ({', '.join(escaped_values)})")
        
        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        
        # 6. 构建 ORDER BY 子句
        order_clause = ""
        if order_by:
            if re.match(r'^[a-zA-Z0-9_]+$', order_by):
                direction = order_direction.lower()
                if direction not in self.ALLOWED_ORDER_DIRECTIONS:
                    direction = 'desc'
                order_clause = f"ORDER BY {order_by} {direction.upper()}"
        else:
            order_clause = "ORDER BY ts DESC"
        
        # 7. 构建 LIMIT 和 OFFSET
        limit = max(1, min(limit, 10000))
        offset = max(0, offset)
        limit_clause = f"LIMIT {limit} OFFSET {offset}"
        
        sql_parts = [select_clause, from_clause, where_clause, order_clause, limit_clause]
        sql = ' '.join(part for part in sql_parts if part)
        
        logger.info(f"[SQL构建器] SQL生成成功: {sql}")
        
        return {
            'sql': sql,
            'database': tdengine_database,
            'stable': tdengine_stable,
            'select_columns': select_columns,
            'row_count_sql': self._build_count_sql(tdengine_database, tdengine_stable, where_clause)
        }

    async def build_aggregation_sql(
        self,
        model_config: DeviceDataModel,
        device_code: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        group_by: Optional[List[str]] = None,
        interval: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        构建聚合查询 SQL
        """
        logger.info(f"[SQL构建器] 构建聚合SQL: model={model_config.model_code}")
        
        if model_config.model_type not in ['statistics', 'ai_analysis']:
            raise APIException(code=400, message=f"不支持聚合查询的模型类型: {model_config.model_type}")
        
        field_mappings = await self._get_field_mappings(
            model_config.device_type_code,
            model_config.selected_fields
        )
        
        if not field_mappings:
            raise APIException(code=400, message=f"无有效字段映射: {model_config.model_code}")
        
        tdengine_database = field_mappings[0]['tdengine_database']
        tdengine_stable = field_mappings[0]['tdengine_stable']
        
        aggregation_config = model_config.aggregation_config or {}
        default_methods = aggregation_config.get('methods', ['avg'])
        
        select_items = []
        
        if interval:
            if re.match(r'^\d+[smhd]$', interval):
                select_items.append(f"_wstart as window_start")
                select_items.append(f"_wend as window_end")
            else:
                interval = None
        
        if group_by:
            for field in group_by:
                if re.match(r'^[a-zA-Z0-9_]+$', field):
                    select_items.append(field)
        else:
            # 动态获取设备标识字段
            identifier_mapping = await self._get_identifier_mapping(model_config.device_type_code)
            if identifier_mapping:
                 device_id_col = identifier_mapping['tdengine_column']
            else:
                 device_id_col = self._get_device_identifier_column(field_mappings)
            
            select_items.append(device_id_col)
        
        for mapping in field_mappings:
            column = mapping['tdengine_column']
            field_code = mapping['field_code']
            agg_method = mapping.get('aggregation_method', 'avg')
            if agg_method not in self.ALLOWED_AGG_FUNCTIONS:
                agg_method = 'avg'
            
            if not re.match(r'^[a-zA-Z0-9_]+$', column):
                continue
            
            select_items.append(f"{agg_method.upper()}({column}) as {field_code}_{agg_method}")
        
        select_clause = f"SELECT {', '.join(select_items)}"
        from_clause = f"FROM {tdengine_database}.{tdengine_stable}"
        
        where_conditions = []
        if device_code:
            # 动态获取设备标识字段
            identifier_mapping = await self._get_identifier_mapping(model_config.device_type_code)
            if identifier_mapping:
                 device_id_col = identifier_mapping['tdengine_column']
            else:
                 device_id_col = self._get_device_identifier_column(field_mappings)
            
            where_conditions.append(f"{device_id_col} = '{self._escape_sql_string(device_code)}'")
        if start_time:
            start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            where_conditions.append(f"ts >= '{start_time_str}'")
        if end_time:
            end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            where_conditions.append(f"ts <= '{end_time_str}'")
        
        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        
        interval_clause = f"INTERVAL({interval})" if interval else ""
        
        group_by_clause = ""
        if group_by:
            valid_fields = [f for f in group_by if re.match(r'^[a-zA-Z0-9_]+$', f)]
            if valid_fields:
                group_by_clause = f"GROUP BY {', '.join(valid_fields)}"
        
        sql_parts = [
            select_clause, from_clause, where_clause, 
            interval_clause, group_by_clause, 
            "ORDER BY window_start DESC" if interval else "ORDER BY prod_code"
        ]
        
        sql = ' '.join(part for part in sql_parts if part)
        logger.info(f"[SQL构建器] 聚合SQL生成成功: {sql}")
        
        return {
            'sql': sql,
            'database': tdengine_database,
            'stable': tdengine_stable,
            'aggregation_methods': default_methods,
            'interval': interval
        }
    
    async def _get_table_info(self, device_type_code: str) -> Dict[str, str]:
        """
        获取设备类型对应的 TDengine 表信息
        """
        device_type = await DeviceType.filter(type_code=device_type_code).first()
        if not device_type:
            raise APIException(code=400, message=f"设备类型不存在: {device_type_code}")
            
        if not device_type.tdengine_stable_name:
            raise APIException(code=400, message=f"设备类型未配置超级表: {device_type_code}")
            
        return {
            "database": settings.TDENGINE_DATABASE, # 从配置获取数据库名
            "stable": device_type.tdengine_stable_name
        }

    async def _get_identifier_mapping(self, device_type_code: str) -> Dict[str, Any]:
        """
        获取设备标识字段的映射信息
        """
        # 1. 查找可能的标识字段
        candidates = ['device_code', 'device_id', 'prod_code']
        
        # 优先查找 mapping 中 is_tag=True 的字段? 
        # 或者是直接查找 field_code 匹配的字段
        
        best_mapping = None
        best_prio = 999
        
        priority_map = {
            'device_code': 1,
            'prod_code': 2,
            'device_id': 3
        }

        for code in candidates:
            field = await DeviceField.filter(
                device_type_code=device_type_code, 
                field_code=code
            ).first()
            
            if field:
                mapping = await DeviceFieldMapping.filter(
                    device_type_code=device_type_code,
                    device_field_id=field.id
                ).first()
                
                col_name = mapping.tdengine_column if mapping else code
                
                prio = priority_map.get(code, 999)
                if prio < best_prio:
                    best_prio = prio
                    best_mapping = {
                        'field_code': code,
                        'tdengine_column': col_name
                    }
        
        return best_mapping

    async def _get_field_mappings(
        self,
        device_type_code: str,
        selected_fields: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        获取字段映射信息
        优先使用 DeviceFieldMapping 配置，如果不存在则默认使用 field_code 作为列名
        """
        field_mappings = []
        table_info = await self._get_table_info(device_type_code)
        
        for field_config in selected_fields:
            field_code = field_config.get('field_code')
            if not field_code:
                continue
            
            # 验证字段是否存在且启用
            field = await DeviceField.filter(
                device_type_code=device_type_code,
                field_code=field_code,
                is_active=True
            ).first()
            
            if not field:
                logger.warning(f"[SQL构建器] 字段未定义或未启用: {field_code}，跳过")
                continue
            
            # 尝试查找自定义映射
            # 注意：通过外键关联查询字段映射
            mapping = await DeviceFieldMapping.filter(
                device_type_code=device_type_code,
                device_field_id=field.id
            ).first()
            
            # 默认值
            tdengine_database = table_info['database']
            tdengine_stable = table_info['stable']
            tdengine_column = field_code
            
            # 如果有映射配置，覆盖默认值
            if mapping:
                if mapping.tdengine_database:
                    tdengine_database = mapping.tdengine_database
                if mapping.tdengine_stable:
                    tdengine_stable = mapping.tdengine_stable
                if mapping.tdengine_column:
                    tdengine_column = mapping.tdengine_column
            
            field_mappings.append({
                'field_code': field_code,
                'tdengine_database': tdengine_database,
                'tdengine_stable': tdengine_stable,
                'tdengine_column': tdengine_column,
                'aggregation_method': field.aggregation_method or 'avg'
            })
        
        return field_mappings
    
    def _build_count_sql(
        self,
        database: str,
        stable: str,
        where_clause: str
    ) -> str:
        """
        构建 COUNT 查询 SQL（用于获取总记录数）
        
        Args:
            database: 数据库名
            stable: 超级表名
            where_clause: WHERE 子句
        
        Returns:
            COUNT SQL
        """
        sql_parts = [
            f"SELECT COUNT(*) as total",
            f"FROM {database}.{stable}",
            where_clause
        ]
        
        return ' '.join(part for part in sql_parts if part)
    
    def _get_device_identifier_column(self, field_mappings: List[Dict[str, Any]]) -> str:
        """
        获取设备标识字段的 TDengine 列名
        优先级：
        1. field_code 为 'device_code'
        2. field_code 为 'prod_code'
        3. field_code 为 'device_id'
        4. field_code 为 'tag' (忽略大小写)
        5. 默认 'prod_code'
        """
        priority_map = {
            'device_code': 1,
            'prod_code': 2,
            'device_id': 3,
            'tag': 4
        }
        
        best_col = 'prod_code'
        best_prio = 999
        
        for mapping in field_mappings:
            code = mapping['field_code'].lower()
            col = mapping['tdengine_column']
            
            # 检查优先级
            prio = priority_map.get(code, 999)
            if prio < best_prio:
                best_prio = prio
                best_col = col
                
            # 如果找不到匹配的field_code，尝试检查是否是TAG (通常TAG用于标识设备)
            # 这里简单假设包含 device, id, code, tag 的列名可能是标识符
            if best_prio == 999:
                 if any(k in col.lower() for k in ['device', 'code', 'id', 'tag']) and mapping.get('is_tag', False):
                     # 这是一个启发式规则，作为备选
                     pass 

        return best_col
    
    def _escape_sql_string(self, value: str) -> str:
        """
        SQL 字符串转义（防注入）
        
        Args:
            value: 原始字符串
        
        Returns:
            转义后的字符串
        """
        # 转义单引号
        return value.replace("'", "''").replace("\\", "\\\\")
    
    def validate_sql(self, sql: str) -> bool:
        """
        验证 SQL 安全性（防注入）
        
        Args:
            sql: SQL 语句
        
        Returns:
            是否安全
        """
        # 检查危险关键词
        dangerous_keywords = [
            'drop', 'delete', 'truncate', 'update', 'insert',
            'create', 'alter', 'exec', 'execute', 'script'
        ]
        
        sql_lower = sql.lower()
        for keyword in dangerous_keywords:
            if keyword in sql_lower:
                logger.warning(f"[SQL构建器] SQL包含危险关键词: {keyword}")
                return False
        
        return True


# 创建全局实例
sql_builder = SQLBuilder()

