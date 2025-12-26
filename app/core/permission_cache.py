#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限缓存系统
实现Redis权限缓存管理器，支持自动过期、批量查询优化、缓存命中率监控和性能统计
"""

import json
import time
import asyncio
from typing import List, Dict, Set, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict
from contextlib import asynccontextmanager

from app.core.redis_cache import redis_cache_manager
from app.core.unified_logger import get_logger

logger = get_logger(__name__)


@dataclass
class CacheStats:
    """缓存统计信息"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    total_requests: int = 0
    avg_response_time: float = 0.0
    hit_rate: float = 0.0
    
    def update_hit_rate(self):
        """更新命中率"""
        if self.total_requests > 0:
            self.hit_rate = self.hits / self.total_requests
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class CacheMetrics:
    """缓存性能指标"""
    operation: str
    start_time: float
    end_time: float
    success: bool
    cache_key: str
    hit: bool = False
    
    @property
    def duration(self) -> float:
        """操作耗时（毫秒）"""
        return (self.end_time - self.start_time) * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "operation": self.operation,
            "duration_ms": round(self.duration, 3),
            "success": self.success,
            "cache_key": self.cache_key,
            "hit": self.hit,
            "timestamp": datetime.fromtimestamp(self.end_time).isoformat()
        }


class PermissionCacheManager:
    """权限缓存管理器"""
    
    def __init__(self):
        self.cache_manager = redis_cache_manager
        
        # 缓存配置
        self.default_ttl = 300  # 5分钟默认TTL
        self.user_permissions_ttl = 600  # 用户权限缓存10分钟
        self.user_roles_ttl = 900  # 用户角色缓存15分钟
        self.user_menus_ttl = 1200  # 用户菜单缓存20分钟
        self.role_permissions_ttl = 1800  # 角色权限缓存30分钟
        
        # 缓存键前缀
        self.user_permissions_prefix = "perm:user_permissions:"
        self.user_roles_prefix = "perm:user_roles:"
        self.user_menus_prefix = "perm:user_menus:"
        self.role_permissions_prefix = "perm:role_permissions:"
        self.api_permissions_prefix = "perm:api_permissions:"
        self.batch_permissions_prefix = "perm:batch_permissions:"
        
        # 统计信息
        self.stats = CacheStats()
        self.metrics_history: List[CacheMetrics] = []
        self.max_metrics_history = 1000  # 最多保存1000条历史记录
        
        # 性能监控
        self.slow_query_threshold = 100  # 慢查询阈值（毫秒）
        self.enable_metrics = True
        
        # 批量操作优化
        self.batch_size = 100  # 批量操作大小
        self.pipeline_enabled = True
    
    @asynccontextmanager
    async def _track_operation(self, operation: str, cache_key: str):
        """跟踪缓存操作性能"""
        start_time = time.time()
        success = False
        hit = False
        
        try:
            yield lambda h: setattr(self, '_current_hit', h)  # 用于设置命中状态
            success = True
        except Exception as e:
            logger.error(f"缓存操作失败 {operation} {cache_key}: {e}")
            self.stats.errors += 1
            raise
        finally:
            end_time = time.time()
            hit = getattr(self, '_current_hit', False)
            
            # 更新统计
            self.stats.total_requests += 1
            if hit:
                self.stats.hits += 1
            else:
                self.stats.misses += 1
            
            # 记录性能指标
            if self.enable_metrics:
                metric = CacheMetrics(
                    operation=operation,
                    start_time=start_time,
                    end_time=end_time,
                    success=success,
                    cache_key=cache_key,
                    hit=hit
                )
                
                self._add_metric(metric)
                
                # 慢查询警告
                if metric.duration > self.slow_query_threshold:
                    logger.warning(f"慢缓存查询: {operation} {cache_key} 耗时 {metric.duration:.2f}ms")
            
            # 更新平均响应时间
            total_time = self.stats.avg_response_time * (self.stats.total_requests - 1)
            self.stats.avg_response_time = (total_time + (end_time - start_time) * 1000) / self.stats.total_requests
            
            # 更新命中率
            self.stats.update_hit_rate()
    
    def _add_metric(self, metric: CacheMetrics):
        """添加性能指标"""
        self.metrics_history.append(metric)
        
        # 保持历史记录在限制范围内
        if len(self.metrics_history) > self.max_metrics_history:
            self.metrics_history = self.metrics_history[-self.max_metrics_history:]
    
    async def get_user_permissions(self, user_id: int) -> Optional[List[str]]:
        """获取用户权限缓存"""
        cache_key = f"{self.user_permissions_prefix}{user_id}"
        
        async with self._track_operation("get_user_permissions", cache_key) as set_hit:
            try:
                cached_permissions = await self.cache_manager.get(cache_key)
                if cached_permissions is not None:
                    set_hit(True)
                    logger.debug(f"用户权限缓存命中: user_id={user_id}")
                    return cached_permissions
                else:
                    set_hit(False)
                    return None
            except Exception as e:
                logger.error(f"获取用户权限缓存失败: user_id={user_id}, error={e}")
                set_hit(False)
                return None
    
    async def set_user_permissions(self, user_id: int, permissions: List[str]) -> bool:
        """设置用户权限缓存"""
        cache_key = f"{self.user_permissions_prefix}{user_id}"
        
        async with self._track_operation("set_user_permissions", cache_key) as set_hit:
            try:
                result = await self.cache_manager.set(
                    cache_key.replace(f"{self.cache_manager.key_prefix}", ""),
                    permissions,
                    ttl=self.user_permissions_ttl
                )
                if result:
                    self.stats.sets += 1
                    logger.debug(f"用户权限缓存设置成功: user_id={user_id}, 权限数量={len(permissions)}")
                set_hit(False)  # set操作不算命中
                return result
            except Exception as e:
                logger.error(f"设置用户权限缓存失败: user_id={user_id}, error={e}")
                set_hit(False)
                return False
    
    async def get_user_roles(self, user_id: int) -> Optional[List[Dict]]:
        """获取用户角色缓存"""
        cache_key = f"{self.user_roles_prefix}{user_id}"
        
        async with self._track_operation("get_user_roles", cache_key) as set_hit:
            try:
                cached_roles = await self.cache_manager.get(cache_key)
                if cached_roles is not None:
                    set_hit(True)
                    logger.debug(f"用户角色缓存命中: user_id={user_id}")
                    return cached_roles
                else:
                    set_hit(False)
                    return None
            except Exception as e:
                logger.error(f"获取用户角色缓存失败: user_id={user_id}, error={e}")
                set_hit(False)
                return None
    
    async def set_user_roles(self, user_id: int, roles: List[Dict]) -> bool:
        """设置用户角色缓存"""
        cache_key = f"{self.user_roles_prefix}{user_id}"
        
        async with self._track_operation("set_user_roles", cache_key) as set_hit:
            try:
                result = await self.cache_manager.set(
                    cache_key.replace(f"{self.cache_manager.key_prefix}", ""),
                    roles,
                    ttl=self.user_roles_ttl
                )
                if result:
                    self.stats.sets += 1
                    logger.debug(f"用户角色缓存设置成功: user_id={user_id}, 角色数量={len(roles)}")
                set_hit(False)
                return result
            except Exception as e:
                logger.error(f"设置用户角色缓存失败: user_id={user_id}, error={e}")
                set_hit(False)
                return False
    
    async def get_user_menus(self, user_id: int) -> Optional[List[Dict]]:
        """获取用户菜单缓存"""
        cache_key = f"{self.user_menus_prefix}{user_id}"
        
        async with self._track_operation("get_user_menus", cache_key) as set_hit:
            try:
                cached_menus = await self.cache_manager.get(cache_key)
                if cached_menus is not None:
                    set_hit(True)
                    logger.debug(f"用户菜单缓存命中: user_id={user_id}")
                    return cached_menus
                else:
                    set_hit(False)
                    return None
            except Exception as e:
                logger.error(f"获取用户菜单缓存失败: user_id={user_id}, error={e}")
                set_hit(False)
                return None
    
    async def set_user_menus(self, user_id: int, menus: List[Dict]) -> bool:
        """设置用户菜单缓存"""
        cache_key = f"{self.user_menus_prefix}{user_id}"
        
        async with self._track_operation("set_user_menus", cache_key) as set_hit:
            try:
                result = await self.cache_manager.set(
                    cache_key.replace(f"{self.cache_manager.key_prefix}", ""),
                    menus,
                    ttl=self.user_menus_ttl
                )
                if result:
                    self.stats.sets += 1
                    logger.debug(f"用户菜单缓存设置成功: user_id={user_id}, 菜单数量={len(menus)}")
                set_hit(False)
                return result
            except Exception as e:
                logger.error(f"设置用户菜单缓存失败: user_id={user_id}, error={e}")
                set_hit(False)
                return False
    
    async def get_role_permissions(self, role_id: int) -> Optional[List[str]]:
        """获取角色权限缓存"""
        cache_key = f"{self.role_permissions_prefix}{role_id}"
        
        async with self._track_operation("get_role_permissions", cache_key) as set_hit:
            try:
                cached_permissions = await self.cache_manager.get(cache_key)
                if cached_permissions is not None:
                    set_hit(True)
                    logger.debug(f"角色权限缓存命中: role_id={role_id}")
                    return cached_permissions
                else:
                    set_hit(False)
                    return None
            except Exception as e:
                logger.error(f"获取角色权限缓存失败: role_id={role_id}, error={e}")
                set_hit(False)
                return None
    
    async def set_role_permissions(self, role_id: int, permissions: List[str]) -> bool:
        """设置角色权限缓存"""
        cache_key = f"{self.role_permissions_prefix}{role_id}"
        
        async with self._track_operation("set_role_permissions", cache_key) as set_hit:
            try:
                result = await self.cache_manager.set(
                    cache_key.replace(f"{self.cache_manager.key_prefix}", ""),
                    permissions,
                    ttl=self.role_permissions_ttl
                )
                if result:
                    self.stats.sets += 1
                    logger.debug(f"角色权限缓存设置成功: role_id={role_id}, 权限数量={len(permissions)}")
                set_hit(False)
                return result
            except Exception as e:
                logger.error(f"设置角色权限缓存失败: role_id={role_id}, error={e}")
                set_hit(False)
                return False
    
    async def batch_get_user_permissions(self, user_ids: List[int]) -> Dict[int, Optional[List[str]]]:
        """批量获取用户权限"""
        if not user_ids:
            return {}
        
        results = {}
        
        # 分批处理
        for i in range(0, len(user_ids), self.batch_size):
            batch_user_ids = user_ids[i:i + self.batch_size]
            
            # 并发获取这一批的权限
            tasks = [self.get_user_permissions(user_id) for user_id in batch_user_ids]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for user_id, result in zip(batch_user_ids, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"批量获取用户权限失败: user_id={user_id}, error={result}")
                    results[user_id] = None
                else:
                    results[user_id] = result
        
        logger.debug(f"批量获取用户权限完成: 请求数量={len(user_ids)}, 命中数量={sum(1 for v in results.values() if v is not None)}")
        return results
    
    async def batch_set_user_permissions(self, permissions_data: Dict[int, List[str]]) -> Dict[int, bool]:
        """批量设置用户权限"""
        if not permissions_data:
            return {}
        
        results = {}
        
        # 分批处理
        items = list(permissions_data.items())
        for i in range(0, len(items), self.batch_size):
            batch_items = items[i:i + self.batch_size]
            
            # 并发设置这一批的权限
            tasks = [self.set_user_permissions(user_id, permissions) for user_id, permissions in batch_items]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for (user_id, _), result in zip(batch_items, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"批量设置用户权限失败: user_id={user_id}, error={result}")
                    results[user_id] = False
                else:
                    results[user_id] = result
        
        success_count = sum(1 for v in results.values() if v)
        logger.debug(f"批量设置用户权限完成: 请求数量={len(permissions_data)}, 成功数量={success_count}")
        return results
    
    async def clear_user_cache(self, user_id: int) -> bool:
        """清除用户相关缓存"""
        cache_keys = [
            f"{self.user_permissions_prefix}{user_id}",
            f"{self.user_roles_prefix}{user_id}",
            f"{self.user_menus_prefix}{user_id}"
        ]
        
        success = True
        deleted_count = 0
        
        for cache_key in cache_keys:
            try:
                result = await self.cache_manager.delete(cache_key.replace(f"{self.cache_manager.key_prefix}", ""))
                if result:
                    deleted_count += 1
                    self.stats.deletes += 1
                else:
                    success = False
            except Exception as e:
                logger.error(f"清除用户缓存失败: cache_key={cache_key}, error={e}")
                success = False
        
        logger.debug(f"清除用户缓存: user_id={user_id}, 删除数量={deleted_count}")
        return success
    
    async def clear_role_cache(self, role_id: int) -> bool:
        """清除角色相关缓存"""
        try:
            # 清除角色权限缓存
            role_cache_key = f"{self.role_permissions_prefix}{role_id}"
            await self.cache_manager.delete(role_cache_key.replace(f"{self.cache_manager.key_prefix}", ""))
            
            # 清除所有用户权限缓存（因为角色权限变更会影响所有拥有该角色的用户）
            patterns = [
                f"{self.user_permissions_prefix}*",
                f"{self.user_roles_prefix}*",
                f"{self.user_menus_prefix}*"
            ]
            
            total_deleted = 0
            for pattern in patterns:
                deleted_count = await self.cache_manager.clear_pattern(pattern.replace(f"{self.cache_manager.key_prefix}", ""))
                total_deleted += deleted_count
                self.stats.deletes += deleted_count
            
            logger.info(f"清除角色缓存: role_id={role_id}, 删除数量={total_deleted}")
            return True
            
        except Exception as e:
            logger.error(f"清除角色缓存失败: role_id={role_id}, error={e}")
            return False
    
    async def clear_all_permission_cache(self) -> bool:
        """清除所有权限相关缓存"""
        try:
            patterns = [
                f"{self.user_permissions_prefix}*",
                f"{self.user_roles_prefix}*",
                f"{self.user_menus_prefix}*",
                f"{self.role_permissions_prefix}*",
                f"{self.api_permissions_prefix}*",
                f"{self.batch_permissions_prefix}*"
            ]
            
            total_deleted = 0
            for pattern in patterns:
                deleted_count = await self.cache_manager.clear_pattern(pattern.replace(f"{self.cache_manager.key_prefix}", ""))
                total_deleted += deleted_count
                self.stats.deletes += deleted_count
            
            logger.info(f"清除所有权限缓存完成, 删除数量={total_deleted}")
            return True
            
        except Exception as e:
            logger.error(f"清除所有权限缓存失败: error={e}")
            return False
    
    async def preload_user_permissions(self, user_ids: List[int]) -> Dict[int, bool]:
        """预加载用户权限（缓存预热）"""
        logger.info(f"开始预加载用户权限: 用户数量={len(user_ids)}")
        
        # 检查哪些用户的权限还没有缓存
        uncached_user_ids = []
        for user_id in user_ids:
            cached_permissions = await self.get_user_permissions(user_id)
            if cached_permissions is None:
                uncached_user_ids.append(user_id)
        
        if not uncached_user_ids:
            logger.info("所有用户权限都已缓存，无需预加载")
            return {user_id: True for user_id in user_ids}
        
        # 从数据库加载未缓存的用户权限
        try:
            from app.services.permission_service import permission_service
            
            results = {}
            for user_id in uncached_user_ids:
                try:
                    permissions = await permission_service.get_user_permissions(user_id)
                    success = await self.set_user_permissions(user_id, permissions)
                    results[user_id] = success
                except Exception as e:
                    logger.error(f"预加载用户权限失败: user_id={user_id}, error={e}")
                    results[user_id] = False
            
            # 已缓存的用户标记为成功
            for user_id in user_ids:
                if user_id not in results:
                    results[user_id] = True
            
            success_count = sum(1 for v in results.values() if v)
            logger.info(f"用户权限预加载完成: 总数量={len(user_ids)}, 新加载={len(uncached_user_ids)}, 成功={success_count}")
            
            return results
            
        except Exception as e:
            logger.error(f"预加载用户权限失败: error={e}")
            return {user_id: False for user_id in user_ids}
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            # 基础统计
            stats_dict = self.stats.to_dict()
            
            # 缓存键统计
            patterns = [
                (self.user_permissions_prefix, "用户权限"),
                (self.user_roles_prefix, "用户角色"),
                (self.user_menus_prefix, "用户菜单"),
                (self.role_permissions_prefix, "角色权限"),
                (self.api_permissions_prefix, "API权限"),
                (self.batch_permissions_prefix, "批量权限")
            ]
            
            cache_key_stats = {}
            total_keys = 0
            
            for prefix, name in patterns:
                try:
                    # 获取匹配的键数量
                    pattern = f"{prefix}*"
                    keys = await self.cache_manager.redis_manager.redis.keys(
                        f"{self.cache_manager.key_prefix}{pattern}"
                    )
                    key_count = len(keys)
                    cache_key_stats[name] = key_count
                    total_keys += key_count
                except Exception as e:
                    logger.error(f"获取缓存键统计失败: {name}, error={e}")
                    cache_key_stats[name] = 0
            
            # 性能统计
            recent_metrics = self.metrics_history[-100:] if self.metrics_history else []
            
            if recent_metrics:
                avg_duration = sum(m.duration for m in recent_metrics) / len(recent_metrics)
                slow_queries = sum(1 for m in recent_metrics if m.duration > self.slow_query_threshold)
                error_rate = sum(1 for m in recent_metrics if not m.success) / len(recent_metrics)
            else:
                avg_duration = 0
                slow_queries = 0
                error_rate = 0
            
            return {
                "basic_stats": stats_dict,
                "cache_keys": {
                    "total": total_keys,
                    "by_type": cache_key_stats
                },
                "performance": {
                    "avg_duration_ms": round(avg_duration, 3),
                    "slow_queries": slow_queries,
                    "error_rate": round(error_rate * 100, 2),
                    "slow_query_threshold_ms": self.slow_query_threshold
                },
                "configuration": {
                    "user_permissions_ttl": self.user_permissions_ttl,
                    "user_roles_ttl": self.user_roles_ttl,
                    "user_menus_ttl": self.user_menus_ttl,
                    "role_permissions_ttl": self.role_permissions_ttl,
                    "batch_size": self.batch_size,
                    "enable_metrics": self.enable_metrics
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取缓存统计信息失败: error={e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    async def get_performance_report(self, hours: int = 1) -> Dict[str, Any]:
        """获取性能报告"""
        try:
            # 过滤指定时间范围内的指标
            cutoff_time = time.time() - (hours * 3600)
            recent_metrics = [
                m for m in self.metrics_history 
                if m.end_time >= cutoff_time
            ]
            
            if not recent_metrics:
                return {
                    "message": f"过去{hours}小时内无性能数据",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 按操作类型分组统计
            operation_stats = defaultdict(lambda: {
                "count": 0,
                "total_duration": 0,
                "success_count": 0,
                "hit_count": 0
            })
            
            for metric in recent_metrics:
                stats = operation_stats[metric.operation]
                stats["count"] += 1
                stats["total_duration"] += metric.duration
                if metric.success:
                    stats["success_count"] += 1
                if metric.hit:
                    stats["hit_count"] += 1
            
            # 计算各项指标
            operation_report = {}
            for operation, stats in operation_stats.items():
                operation_report[operation] = {
                    "total_requests": stats["count"],
                    "avg_duration_ms": round(stats["total_duration"] / stats["count"], 3),
                    "success_rate": round(stats["success_count"] / stats["count"] * 100, 2),
                    "hit_rate": round(stats["hit_count"] / stats["count"] * 100, 2) if stats["count"] > 0 else 0
                }
            
            # 整体统计
            total_requests = len(recent_metrics)
            total_duration = sum(m.duration for m in recent_metrics)
            successful_requests = sum(1 for m in recent_metrics if m.success)
            cache_hits = sum(1 for m in recent_metrics if m.hit)
            slow_queries = sum(1 for m in recent_metrics if m.duration > self.slow_query_threshold)
            
            return {
                "time_range_hours": hours,
                "overall": {
                    "total_requests": total_requests,
                    "avg_duration_ms": round(total_duration / total_requests, 3),
                    "success_rate": round(successful_requests / total_requests * 100, 2),
                    "hit_rate": round(cache_hits / total_requests * 100, 2),
                    "slow_queries": slow_queries,
                    "slow_query_rate": round(slow_queries / total_requests * 100, 2)
                },
                "by_operation": operation_report,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取性能报告失败: error={e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def reset_statistics(self):
        """重置统计信息"""
        self.stats = CacheStats()
        self.metrics_history.clear()
        logger.info("缓存统计信息已重置")
    
    async def health_check(self) -> Dict[str, Any]:
        """权限缓存健康检查"""
        try:
            start_time = time.time()
            
            # 测试基本缓存操作
            test_user_id = 999999
            test_permissions = ["GET /api/v2/test", "POST /api/v2/test"]
            
            # 测试设置
            set_result = await self.set_user_permissions(test_user_id, test_permissions)
            
            # 测试获取
            get_result = await self.get_user_permissions(test_user_id)
            
            # 测试删除
            delete_result = await self.clear_user_cache(test_user_id)
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            # 检查结果
            operations_ok = (
                set_result and 
                get_result == test_permissions and 
                delete_result
            )
            
            return {
                "status": "healthy" if operations_ok else "degraded",
                "response_time_ms": round(response_time, 2),
                "operations": {
                    "set": set_result,
                    "get": get_result == test_permissions,
                    "delete": delete_result
                },
                "cache_stats": self.stats.to_dict(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# 全局权限缓存管理器实例
permission_cache_manager = PermissionCacheManager()


# 缓存装饰器
def permission_cache(
    ttl: Optional[int] = None,
    key_prefix: str = "perm:custom:",
    enable_stats: bool = True
):
    """权限缓存装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key_parts = [key_prefix, func.__name__]
            
            # 添加参数到缓存键
            if args:
                cache_key_parts.append(str(hash(str(args))))
            if kwargs:
                cache_key_parts.append(str(hash(str(sorted(kwargs.items())))))
            
            cache_key = "_".join(filter(None, cache_key_parts))
            
            # 尝试从缓存获取
            if enable_stats:
                async with permission_cache_manager._track_operation("decorator_get", cache_key) as set_hit:
                    cached_result = await permission_cache_manager.cache_manager.get(cache_key)
                    if cached_result is not None:
                        set_hit(True)
                        logger.debug(f"装饰器缓存命中: {cache_key}")
                        return cached_result
                    set_hit(False)
            else:
                cached_result = await permission_cache_manager.cache_manager.get(cache_key)
                if cached_result is not None:
                    return cached_result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            cache_ttl = ttl or permission_cache_manager.default_ttl
            await permission_cache_manager.cache_manager.set(
                cache_key.replace(f"{permission_cache_manager.cache_manager.key_prefix}", ""),
                result,
                ttl=cache_ttl
            )
            
            if enable_stats:
                permission_cache_manager.stats.sets += 1
            
            return result
        
        return wrapper
    return decorator


# 初始化函数
async def init_permission_cache():
    """初始化权限缓存系统"""
    try:
        # 确保Redis缓存管理器已初始化
        if not await permission_cache_manager.cache_manager.redis_manager.is_connected():
            await permission_cache_manager.cache_manager.initialize()
        
        logger.info("权限缓存系统初始化成功")
        
        # 输出配置信息
        logger.info(f"权限缓存配置: "
                   f"用户权限TTL={permission_cache_manager.user_permissions_ttl}s, "
                   f"用户角色TTL={permission_cache_manager.user_roles_ttl}s, "
                   f"用户菜单TTL={permission_cache_manager.user_menus_ttl}s, "
                   f"角色权限TTL={permission_cache_manager.role_permissions_ttl}s")
        
    except Exception as e:
        logger.error(f"权限缓存系统初始化失败: {e}")
        raise


if __name__ == "__main__":
    # 测试权限缓存系统
    async def test_permission_cache():
        await init_permission_cache()
        
        # 测试基本操作
        test_user_id = 1
        test_permissions = ["GET /api/v2/users", "POST /api/v2/users"]
        
        print("测试权限缓存系统...")
        
        # 设置权限
        result = await permission_cache_manager.set_user_permissions(test_user_id, test_permissions)
        print(f"设置权限: {result}")
        
        # 获取权限
        cached_permissions = await permission_cache_manager.get_user_permissions(test_user_id)
        print(f"获取权限: {cached_permissions}")
        
        # 批量操作测试
        batch_data = {
            2: ["GET /api/v2/roles"],
            3: ["GET /api/v2/devices"]
        }
        batch_result = await permission_cache_manager.batch_set_user_permissions(batch_data)
        print(f"批量设置权限: {batch_result}")
        
        batch_get_result = await permission_cache_manager.batch_get_user_permissions([1, 2, 3])
        print(f"批量获取权限: {batch_get_result}")
        
        # 统计信息
        stats = await permission_cache_manager.get_cache_statistics()
        print(f"缓存统计: {stats}")
        
        # 健康检查
        health = await permission_cache_manager.health_check()
        print(f"健康检查: {health}")
        
        # 清理测试数据
        await permission_cache_manager.clear_user_cache(test_user_id)
        await permission_cache_manager.clear_user_cache(2)
        await permission_cache_manager.clear_user_cache(3)
        
        print("权限缓存系统测试完成")
    
    asyncio.run(test_permission_cache())