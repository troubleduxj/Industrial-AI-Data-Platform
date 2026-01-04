"""
TDengine查询构建器

提供类型安全的SQL查询构建功能。

迁移说明:
- 从 platform_v2.timeseries.query_builder 迁移到 platform_core.timeseries.query_builder
- 保持所有API接口不变
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum


class AggregateFunction(str, Enum):
    """聚合函数"""
    AVG = "AVG"
    SUM = "SUM"
    COUNT = "COUNT"
    MIN = "MIN"
    MAX = "MAX"
    FIRST = "FIRST"
    LAST = "LAST"
    SPREAD = "SPREAD"
    STDDEV = "STDDEV"
    PERCENTILE = "PERCENTILE"


class TimeInterval(str, Enum):
    """时间间隔"""
    SECOND = "s"
    MINUTE = "m"
    HOUR = "h"
    DAY = "d"
    WEEK = "w"
    MONTH = "n"
    YEAR = "y"


class QueryBuilder:
    """
    TDengine查询构建器
    
    提供链式API构建SQL查询。
    """
    
    def __init__(self, database: str, table: str):
        """
        初始化查询构建器
        
        Args:
            database: 数据库名
            table: 表名或超级表名
        """
        self._database = database
        self._table = table
        self._select_columns: List[str] = []
        self._where_conditions: List[str] = []
        self._group_by: List[str] = []
        self._order_by: List[str] = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._interval: Optional[str] = None
        self._fill: Optional[str] = None
        self._slimit: Optional[int] = None
        self._soffset: Optional[int] = None
    
    def select(self, *columns: str) -> "QueryBuilder":
        """
        选择列
        
        Args:
            *columns: 列名列表
            
        Returns:
            QueryBuilder: 自身实例
        """
        self._select_columns.extend(columns)
        return self
    
    def select_all(self) -> "QueryBuilder":
        """选择所有列"""
        self._select_columns.append("*")
        return self
    
    def aggregate(
        self,
        func: AggregateFunction,
        column: str,
        alias: Optional[str] = None
    ) -> "QueryBuilder":
        """
        添加聚合函数
        
        Args:
            func: 聚合函数
            column: 列名
            alias: 别名
            
        Returns:
            QueryBuilder: 自身实例
        """
        expr = f"{func.value}({column})"
        if alias:
            expr = f"{expr} AS {alias}"
        self._select_columns.append(expr)
        return self
    
    def where(self, condition: str) -> "QueryBuilder":
        """
        添加WHERE条件
        
        Args:
            condition: 条件表达式
            
        Returns:
            QueryBuilder: 自身实例
        """
        self._where_conditions.append(condition)
        return self
    
    def where_time_range(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        column: str = "ts"
    ) -> "QueryBuilder":
        """
        添加时间范围条件
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            column: 时间列名
            
        Returns:
            QueryBuilder: 自身实例
        """
        if start_time:
            self._where_conditions.append(
                f"{column} >= '{start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}'"
            )
        if end_time:
            self._where_conditions.append(
                f"{column} <= '{end_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}'"
            )
        return self
    
    def where_tag(self, tag_name: str, value: Any) -> "QueryBuilder":
        """
        添加TAG条件
        
        Args:
            tag_name: TAG名
            value: TAG值
            
        Returns:
            QueryBuilder: 自身实例
        """
        if isinstance(value, str):
            self._where_conditions.append(f"{tag_name} = '{value}'")
        else:
            self._where_conditions.append(f"{tag_name} = {value}")
        return self
    
    def group_by(self, *columns: str) -> "QueryBuilder":
        """
        添加GROUP BY
        
        Args:
            *columns: 列名列表
            
        Returns:
            QueryBuilder: 自身实例
        """
        self._group_by.extend(columns)
        return self
    
    def order_by(self, column: str, desc: bool = False) -> "QueryBuilder":
        """
        添加ORDER BY
        
        Args:
            column: 列名
            desc: 是否降序
            
        Returns:
            QueryBuilder: 自身实例
        """
        direction = "DESC" if desc else "ASC"
        self._order_by.append(f"{column} {direction}")
        return self
    
    def limit(self, count: int) -> "QueryBuilder":
        """
        设置LIMIT
        
        Args:
            count: 限制数量
            
        Returns:
            QueryBuilder: 自身实例
        """
        self._limit = count
        return self
    
    def offset(self, count: int) -> "QueryBuilder":
        """
        设置OFFSET
        
        Args:
            count: 偏移量
            
        Returns:
            QueryBuilder: 自身实例
        """
        self._offset = count
        return self
    
    def interval(self, value: int, unit: TimeInterval) -> "QueryBuilder":
        """
        设置时间窗口间隔
        
        Args:
            value: 间隔值
            unit: 时间单位
            
        Returns:
            QueryBuilder: 自身实例
        """
        self._interval = f"{value}{unit.value}"
        return self
    
    def fill(self, method: str = "NULL") -> "QueryBuilder":
        """
        设置填充方法
        
        Args:
            method: 填充方法 (NULL, PREV, NEXT, LINEAR, VALUE)
            
        Returns:
            QueryBuilder: 自身实例
        """
        self._fill = method
        return self
    
    def slimit(self, count: int) -> "QueryBuilder":
        """
        设置SLIMIT（超级表分组限制）
        
        Args:
            count: 限制数量
            
        Returns:
            QueryBuilder: 自身实例
        """
        self._slimit = count
        return self
    
    def soffset(self, count: int) -> "QueryBuilder":
        """
        设置SOFFSET（超级表分组偏移）
        
        Args:
            count: 偏移量
            
        Returns:
            QueryBuilder: 自身实例
        """
        self._soffset = count
        return self
    
    def build(self) -> str:
        """
        构建SQL查询
        
        Returns:
            str: SQL查询语句
        """
        # SELECT
        if not self._select_columns:
            select_clause = "*"
        else:
            select_clause = ", ".join(self._select_columns)
        
        sql = f"SELECT {select_clause} FROM {self._database}.{self._table}"
        
        # WHERE
        if self._where_conditions:
            sql += " WHERE " + " AND ".join(self._where_conditions)
        
        # INTERVAL
        if self._interval:
            sql += f" INTERVAL({self._interval})"
        
        # FILL
        if self._fill:
            sql += f" FILL({self._fill})"
        
        # GROUP BY
        if self._group_by:
            sql += " GROUP BY " + ", ".join(self._group_by)
        
        # ORDER BY
        if self._order_by:
            sql += " ORDER BY " + ", ".join(self._order_by)
        
        # SLIMIT/SOFFSET
        if self._slimit is not None:
            sql += f" SLIMIT {self._slimit}"
            if self._soffset is not None:
                sql += f" SOFFSET {self._soffset}"
        
        # LIMIT/OFFSET
        if self._limit is not None:
            sql += f" LIMIT {self._limit}"
            if self._offset is not None:
                sql += f" OFFSET {self._offset}"
        
        return sql
    
    def __str__(self) -> str:
        return self.build()


def query(database: str, table: str) -> QueryBuilder:
    """
    创建查询构建器
    
    Args:
        database: 数据库名
        table: 表名
        
    Returns:
        QueryBuilder: 查询构建器实例
    """
    return QueryBuilder(database, table)
