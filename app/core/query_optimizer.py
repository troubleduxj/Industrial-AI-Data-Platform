# -*- coding: utf-8 -*-
"""
数据库查询优化模块

提供查询优化、缓存机制和性能监控功能
"""

import asyncio
import json
import time
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
from functools import wraps
from datetime import datetime, timedelta

from tortoise.expressions import Q
from tortoise.models import Model
from tortoise.queryset import QuerySet

from app.log import logger

ModelType = TypeVar("ModelType", bound=Model)


class QueryOptimizer:
    """查询优化器"""
    
    def __init__(self):
        self.query_stats = {}
        self.slow_query_threshold = 1.0  # 慢查询阈值（秒）
    
    def monitor_query(self, func: Callable) -> Callable:
        """查询监控装饰器"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            query_name = f"{func.__module__}.{func.__name__}"
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # 记录查询统计
                self._record_query_stats(query_name, execution_time, True)
                
                # 记录慢查询
                if execution_time > self.slow_query_threshold:
                    logger.warning(
                        f"慢查询检测: {query_name} 执行时间: {execution_time:.3f}s, "
                        f"参数: args={args[1:] if len(args) > 1 else []}, kwargs={kwargs}"
                    )
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                self._record_query_stats(query_name, execution_time, False)
                logger.error(f"查询执行失败: {query_name}, 错误: {str(e)}")
                raise
        
        return wrapper
    
    def _record_query_stats(self, query_name: str, execution_time: float, success: bool):
        """记录查询统计信息"""
        if query_name not in self.query_stats:
            self.query_stats[query_name] = {
                'total_calls': 0,
                'success_calls': 0,
                'failed_calls': 0,
                'total_time': 0.0,
                'avg_time': 0.0,
                'max_time': 0.0,
                'min_time': float('inf')
            }
        
        stats = self.query_stats[query_name]
        stats['total_calls'] += 1
        stats['total_time'] += execution_time
        stats['avg_time'] = stats['total_time'] / stats['total_calls']
        stats['max_time'] = max(stats['max_time'], execution_time)
        stats['min_time'] = min(stats['min_time'], execution_time)
        
        if success:
            stats['success_calls'] += 1
        else:
            stats['failed_calls'] += 1
    
    def get_query_stats(self) -> Dict[str, Any]:
        """获取查询统计信息"""
        return self.query_stats.copy()


class OptimizedQueryMixin:
    """优化查询混入类"""
    
    @classmethod
    async def get_with_relations(cls, prefetch_fields: List[str] = None, select_fields: List[str] = None, **filters):
        """优化的关联查询"""
        query = cls.filter(**filters)
        
        if prefetch_fields:
            query = query.prefetch_related(*prefetch_fields)
        
        if select_fields:
            query = query.select_related(*select_fields)
        
        return await query.first()
    
    @classmethod
    async def get_paginated(
        cls, 
        page: int, 
        page_size: int, 
        search: Q = None,
        order_by: List[str] = None,
        prefetch_fields: List[str] = None,
        select_fields: List[str] = None
    ):
        """优化的分页查询"""
        offset = (page - 1) * page_size
        
        # 构建基础查询
        if search:
            queryset = cls.filter(search)
        else:
            queryset = cls.all()
        
        # 添加关联查询
        if prefetch_fields:
            queryset = queryset.prefetch_related(*prefetch_fields)
        
        if select_fields:
            queryset = queryset.select_related(*select_fields)
        
        # 添加排序
        if order_by:
            queryset = queryset.order_by(*order_by)
        
        # 并行执行计数和数据查询
        count_query = cls.filter(search) if search else cls.all()
        total_task = count_query.count()
        data_task = queryset.offset(offset).limit(page_size)
        
        total, data = await asyncio.gather(total_task, data_task)
        return total, data
    
    @classmethod
    async def bulk_create_optimized(cls, objects: List[Dict[str, Any]], batch_size: int = 100):
        """优化的批量创建"""
        results = []
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            batch_objects = [cls(**obj_data) for obj_data in batch]
            await cls.bulk_create(batch_objects)
            results.extend(batch_objects)
        return results
    
    @classmethod
    async def bulk_update_optimized(
        cls, 
        objects: List[Dict[str, Any]], 
        fields: List[str], 
        batch_size: int = 100
    ):
        """优化的批量更新"""
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            await cls.bulk_update(batch, fields=fields)


class QueryCache:
    """查询缓存管理器"""
    
    def __init__(self):
        self._cache = {}
        self._cache_ttl = {}
        self.default_ttl = 300  # 5分钟默认TTL
    
    def _generate_cache_key(self, model_name: str, method: str, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        # 将参数序列化为字符串
        args_str = str(args) if args else ""
        kwargs_str = json.dumps(kwargs, sort_keys=True, default=str) if kwargs else ""
        return f"{model_name}:{method}:{hash(args_str + kwargs_str)}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._cache_ttl:
            return False
        return datetime.now() < self._cache_ttl[cache_key]
    
    def get(self, cache_key: str) -> Optional[Any]:
        """获取缓存"""
        if cache_key in self._cache and self._is_cache_valid(cache_key):
            logger.debug(f"缓存命中: {cache_key}")
            return self._cache[cache_key]
        
        # 清理过期缓存
        if cache_key in self._cache:
            del self._cache[cache_key]
            del self._cache_ttl[cache_key]
        
        return None
    
    def set(self, cache_key: str, value: Any, ttl: int = None) -> None:
        """设置缓存"""
        ttl = ttl or self.default_ttl
        self._cache[cache_key] = value
        self._cache_ttl[cache_key] = datetime.now() + timedelta(seconds=ttl)
        logger.debug(f"缓存设置: {cache_key}, TTL: {ttl}s")
    
    def delete(self, cache_key: str) -> None:
        """删除缓存"""
        if cache_key in self._cache:
            del self._cache[cache_key]
            del self._cache_ttl[cache_key]
            logger.debug(f"缓存删除: {cache_key}")
    
    def clear_pattern(self, pattern: str) -> None:
        """清理匹配模式的缓存"""
        keys_to_delete = [key for key in self._cache.keys() if pattern in key]
        for key in keys_to_delete:
            self.delete(key)
        logger.debug(f"批量清理缓存: {pattern}, 清理数量: {len(keys_to_delete)}")
    
    def clear_all(self) -> None:
        """清理所有缓存"""
        count = len(self._cache)
        self._cache.clear()
        self._cache_ttl.clear()
        logger.debug(f"清理所有缓存, 清理数量: {count}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        now = datetime.now()
        valid_count = sum(1 for ttl in self._cache_ttl.values() if now < ttl)
        expired_count = len(self._cache) - valid_count
        
        return {
            'total_keys': len(self._cache),
            'valid_keys': valid_count,
            'expired_keys': expired_count,
            'memory_usage_mb': sum(len(str(v)) for v in self._cache.values()) / 1024 / 1024
        }


def cached_query(ttl: int = 300, cache_key_prefix: str = ""):
    """查询缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # 生成缓存键
            model_name = self.__class__.__name__
            method_name = func.__name__
            cache_key = query_cache._generate_cache_key(
                f"{cache_key_prefix}{model_name}", method_name, args, kwargs
            )
            
            # 尝试从缓存获取
            cached_result = query_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行查询
            result = await func(self, *args, **kwargs)
            
            # 缓存结果
            query_cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# 全局实例
query_optimizer = QueryOptimizer()
query_cache = QueryCache()


class DatabaseIndexAnalyzer:
    """数据库索引分析器"""
    
    @staticmethod
    async def analyze_missing_indexes(model_class: Type[Model]) -> List[Dict[str, Any]]:
        """分析缺失的索引"""
        suggestions = []
        
        # 分析外键字段
        for field_name, field in model_class._meta.fields_map.items():
            if hasattr(field, 'related_model') and not field.index:
                suggestions.append({
                    'table': model_class._meta.db_table,
                    'field': field_name,
                    'type': 'foreign_key',
                    'reason': '外键字段建议添加索引以提高关联查询性能'
                })
        
        # 分析频繁查询字段（基于字段名推测）
        frequent_query_fields = ['status', 'type', 'category', 'is_active', 'created_at', 'updated_at']
        for field_name, field in model_class._meta.fields_map.items():
            if any(keyword in field_name.lower() for keyword in frequent_query_fields):
                if not field.index and not field.pk:
                    suggestions.append({
                        'table': model_class._meta.db_table,
                        'field': field_name,
                        'type': 'frequent_query',
                        'reason': f'字段 {field_name} 可能是频繁查询字段，建议添加索引'
                    })
        
        return suggestions
    
    @staticmethod
    async def generate_index_sql(suggestions: List[Dict[str, Any]]) -> List[str]:
        """生成索引创建SQL"""
        sql_statements = []
        
        for suggestion in suggestions:
            table = suggestion['table']
            field = suggestion['field']
            index_name = f"idx_{table}_{field}"
            
            sql = f"CREATE INDEX {index_name} ON {table} ({field});"
            sql_statements.append(sql)
        
        return sql_statements


# 性能监控装饰器
def monitor_performance(func: Callable) -> Callable:
    """性能监控装饰器"""
    return query_optimizer.monitor_query(func)