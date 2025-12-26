# -*- coding: utf-8 -*-
"""
优化的CRUD基类

提供带有缓存、性能监控和查询优化的CRUD操作
"""

import asyncio
from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar, Union

from pydantic import BaseModel
from tortoise.expressions import Q
from tortoise.models import Model

from app.core.crud import CRUDBase
from app.core.query_optimizer import (
    cached_query, 
    monitor_performance, 
    query_cache, 
    OptimizedQueryMixin
)
from app.log import logger

ModelType = TypeVar("ModelType", bound=Model)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class OptimizedCRUDBase(CRUDBase[ModelType, CreateSchemaType, UpdateSchemaType]):
    """优化的CRUD基类"""
    
    def __init__(self, model: Type[ModelType], cache_ttl: int = 300):
        super().__init__(model)
        self.cache_ttl = cache_ttl
        self.cache_prefix = f"{model.__name__.lower()}_"
    
    @monitor_performance
    @cached_query(ttl=300)
    async def get(self, id: int, prefetch_fields: List[str] = None) -> ModelType:
        """获取单个对象（带缓存）"""
        query = self.model.filter(id=id)
        
        if prefetch_fields:
            query = query.prefetch_related(*prefetch_fields)
        
        return await query.first()
    
    @monitor_performance
    async def get_multi_with_total_optimized(
        self,
        page: int,
        page_size: int,
        search: Union[Q, Dict[str, Any]] = None,
        order: List[str] = None,
        prefetch_fields: List[str] = None,
        select_fields: List[str] = None,
        use_cache: bool = True
    ) -> Tuple[int, List[ModelType]]:
        """优化的分页查询"""
        
        # 生成缓存键
        cache_key = None
        if use_cache:
            cache_params = {
                'page': page,
                'page_size': page_size,
                'search': str(search) if search else None,
                'order': order,
                'prefetch': prefetch_fields,
                'select': select_fields
            }
            cache_key = f"{self.cache_prefix}paginated_{hash(str(cache_params))}"
            
            # 尝试从缓存获取
            cached_result = query_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
        
        # 构建查询
        if search is None:
            query = self.model.all()
        elif isinstance(search, Q):
            query = self.model.filter(search)
        else:
            query = self.model.filter(**search)
        
        # 添加关联查询
        if prefetch_fields:
            query = query.prefetch_related(*prefetch_fields)
        
        if select_fields:
            query = query.select_related(*select_fields)
        
        # 添加排序
        if order:
            query = query.order_by(*order)
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 并行执行计数和数据查询
        count_query = self.model.all()
        if isinstance(search, Q):
            count_query = self.model.filter(search)
        elif search:
            count_query = self.model.filter(**search)
        
        total_task = count_query.count()
        data_task = query.offset(offset).limit(page_size)
        
        total, data = await asyncio.gather(total_task, data_task)
        
        result = (total, data)
        
        # 缓存结果
        if use_cache and cache_key:
            query_cache.set(cache_key, result, self.cache_ttl)
        
        return result
    
    @monitor_performance
    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """创建对象（清理相关缓存）"""
        result = await super().create(obj_in)
        
        # 清理相关缓存
        self._clear_related_cache()
        
        return result
    
    @monitor_performance
    async def update(self, id: int, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        """更新对象（清理相关缓存）"""
        result = await super().update(id, obj_in)
        
        # 清理相关缓存
        self._clear_related_cache()
        self._clear_object_cache(id)
        
        return result
    
    @monitor_performance
    async def remove(self, id: int) -> None:
        """删除对象（清理相关缓存）"""
        await super().remove(id)
        
        # 清理相关缓存
        self._clear_related_cache()
        self._clear_object_cache(id)
    
    @monitor_performance
    async def bulk_create_optimized(
        self, 
        objects: List[CreateSchemaType], 
        batch_size: int = 100
    ) -> List[ModelType]:
        """优化的批量创建"""
        results = []
        
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            batch_data = []
            
            for obj in batch:
                if isinstance(obj, dict):
                    batch_data.append(obj)
                else:
                    batch_data.append(obj.model_dump())
            
            # 批量创建
            batch_objects = [self.model(**data) for data in batch_data]
            await self.model.bulk_create(batch_objects)
            results.extend(batch_objects)
        
        # 清理相关缓存
        self._clear_related_cache()
        
        return results
    
    @monitor_performance
    async def bulk_update_optimized(
        self, 
        updates: List[Dict[str, Any]], 
        batch_size: int = 100
    ) -> None:
        """优化的批量更新"""
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            
            # 批量更新
            for update_data in batch:
                obj_id = update_data.pop('id')
                await self.model.filter(id=obj_id).update(**update_data)
        
        # 清理相关缓存
        self._clear_related_cache()
    
    @cached_query(ttl=600)  # 统计数据缓存时间更长
    async def get_count(self, search: Union[Q, Dict[str, Any]] = None) -> int:
        """获取计数（带缓存）"""
        if search is None:
            return await self.model.all().count()
        elif isinstance(search, Q):
            return await self.model.filter(search).count()
        else:
            return await self.model.filter(**search).count()
    
    @cached_query(ttl=600)
    async def get_statistics(self, group_by: str, search: Union[Q, Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """获取统计信息（带缓存）"""
        from tortoise.functions import Count
        
        query = self.model.all()
        if isinstance(search, Q):
            query = self.model.filter(search)
        elif search:
            query = self.model.filter(**search)
        
        return await query.annotate(count=Count("id")).group_by(group_by).values(group_by, "count")
    
    async def search_optimized(
        self,
        keyword: str = None,
        filters: Dict[str, Any] = None,
        page: int = 1,
        page_size: int = 10,
        order: List[str] = None,
        search_fields: List[str] = None
    ) -> Tuple[int, List[ModelType]]:
        """优化的搜索功能"""
        q = Q()
        
        # 关键词搜索
        if keyword and search_fields:
            keyword_q = Q()
            for field in search_fields:
                keyword_q |= Q(**{f"{field}__icontains": keyword})
            q &= keyword_q
        
        # 过滤条件
        if filters:
            for key, value in filters.items():
                if value is not None:
                    q &= Q(**{key: value})
        
        return await self.get_multi_with_total_optimized(
            page=page,
            page_size=page_size,
            search=q,
            order=order or ['-created_at']
        )
    
    def _clear_related_cache(self) -> None:
        """清理相关缓存"""
        query_cache.clear_pattern(self.cache_prefix)
    
    def _clear_object_cache(self, obj_id: int) -> None:
        """清理特定对象的缓存"""
        query_cache.clear_pattern(f"{self.cache_prefix}get_{obj_id}")
    
    async def warm_cache(self, page_range: Tuple[int, int] = (1, 5)) -> None:
        """预热缓存"""
        logger.info(f"开始预热 {self.model.__name__} 缓存")
        
        start_page, end_page = page_range
        for page in range(start_page, end_page + 1):
            try:
                await self.get_multi_with_total_optimized(
                    page=page,
                    page_size=20,
                    use_cache=True
                )
                logger.debug(f"预热缓存页面 {page} 完成")
            except Exception as e:
                logger.error(f"预热缓存页面 {page} 失败: {str(e)}")
        
        logger.info(f"{self.model.__name__} 缓存预热完成")


class CacheInvalidationMixin:
    """缓存失效混入类"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.related_cache_patterns = []
    
    def add_cache_dependency(self, pattern: str) -> None:
        """添加缓存依赖"""
        if pattern not in self.related_cache_patterns:
            self.related_cache_patterns.append(pattern)
    
    def invalidate_related_caches(self) -> None:
        """失效相关缓存"""
        for pattern in self.related_cache_patterns:
            query_cache.clear_pattern(pattern)
            logger.debug(f"失效缓存模式: {pattern}")


# 查询性能分析器
class QueryPerformanceAnalyzer:
    """查询性能分析器"""
    
    @staticmethod
    async def analyze_slow_queries(threshold: float = 1.0) -> List[Dict[str, Any]]:
        """分析慢查询"""
        from app.core.query_optimizer import query_optimizer
        
        stats = query_optimizer.get_query_stats()
        slow_queries = []
        
        for query_name, stat in stats.items():
            if stat['avg_time'] > threshold:
                slow_queries.append({
                    'query': query_name,
                    'avg_time': stat['avg_time'],
                    'max_time': stat['max_time'],
                    'total_calls': stat['total_calls'],
                    'success_rate': stat['success_calls'] / stat['total_calls'] * 100
                })
        
        return sorted(slow_queries, key=lambda x: x['avg_time'], reverse=True)
    
    @staticmethod
    async def get_cache_hit_rate() -> Dict[str, Any]:
        """获取缓存命中率"""
        cache_stats = query_cache.get_cache_stats()
        
        return {
            'total_keys': cache_stats['total_keys'],
            'valid_keys': cache_stats['valid_keys'],
            'hit_rate': cache_stats['valid_keys'] / max(cache_stats['total_keys'], 1) * 100,
            'memory_usage_mb': cache_stats['memory_usage_mb']
        }
    
    @staticmethod
    async def generate_performance_report() -> Dict[str, Any]:
        """生成性能报告"""
        slow_queries = await QueryPerformanceAnalyzer.analyze_slow_queries()
        cache_stats = await QueryPerformanceAnalyzer.get_cache_hit_rate()
        
        return {
            'timestamp': str(asyncio.get_event_loop().time()),
            'slow_queries': slow_queries[:10],  # 前10个慢查询
            'cache_performance': cache_stats,
            'recommendations': QueryPerformanceAnalyzer._generate_recommendations(slow_queries, cache_stats)
        }
    
    @staticmethod
    def _generate_recommendations(slow_queries: List[Dict], cache_stats: Dict) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if slow_queries:
            recommendations.append(f"发现 {len(slow_queries)} 个慢查询，建议优化查询逻辑或添加索引")
        
        if cache_stats['hit_rate'] < 50:
            recommendations.append("缓存命中率较低，建议调整缓存策略或增加缓存时间")
        
        if cache_stats['memory_usage_mb'] > 100:
            recommendations.append("缓存内存使用过高，建议清理过期缓存或减少缓存数据")
        
        if not recommendations:
            recommendations.append("系统性能良好，无需特别优化")
        
        return recommendations