"""
权限系统性能优化服务
"""
import asyncio
import time
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from app.core.unified_logger import get_logger

logger = get_logger(__name__)
from app.core.permission_cache import permission_cache
from app.services.permission_service import permission_service


@dataclass
class PermissionQueryBatch:
    """权限查询批次"""
    user_ids: List[int]
    permission_codes: List[str]
    query_id: str
    created_at: datetime
    
    
@dataclass
class PerformanceMetrics:
    """性能指标"""
    query_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_response_time: float = 0.0
    batch_queries: int = 0
    total_time: float = 0.0
    
    @property
    def cache_hit_rate(self) -> float:
        """缓存命中率"""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0


class PermissionPerformanceService:
    """权限系统性能优化服务"""
    
    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.batch_queue = []
        self.batch_processing = False
        self.batch_size = 50
        self.batch_timeout = 0.1  # 100ms
        self.preload_cache = {}
        self.query_patterns = defaultdict(int)
        
        # 性能监控配置
        self.enable_metrics = True
        self.enable_batch_optimization = True
        self.enable_preload = True
        self.enable_query_pattern_analysis = True
    
    async def batch_check_permissions(
        self,
        user_permission_pairs: List[Tuple[int, str]]
    ) -> Dict[Tuple[int, str], bool]:
        """批量权限检查优化"""
        start_time = time.time()
        
        try:
            # 分组处理
            results = {}
            cache_results = {}
            db_queries = []
            
            # 第一步：检查缓存
            for user_id, permission_code in user_permission_pairs:
                cache_key = f"perm:{user_id}:{permission_code}"
                cached_result = await permission_cache.get(cache_key)
                
                if cached_result is not None:
                    cache_results[(user_id, permission_code)] = cached_result
                    self.metrics.cache_hits += 1
                else:
                    db_queries.append((user_id, permission_code))
                    self.metrics.cache_misses += 1
            
            # 第二步：批量数据库查询
            if db_queries:
                db_results = await self._batch_db_permission_check(db_queries)
                
                # 缓存结果
                for (user_id, permission_code), result in db_results.items():
                    cache_key = f"perm:{user_id}:{permission_code}"
                    await permission_cache.set(cache_key, result, expire=300)  # 5分钟缓存
                
                results.update(db_results)
            
            # 合并结果
            results.update(cache_results)
            
            # 更新性能指标
            query_time = time.time() - start_time
            self.metrics.query_count += len(user_permission_pairs)
            self.metrics.batch_queries += 1
            self.metrics.total_time += query_time
            self.metrics.avg_response_time = self.metrics.total_time / self.metrics.batch_queries
            
            logger.debug(f"批量权限检查完成: {len(user_permission_pairs)}项, 耗时{query_time:.3f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"批量权限检查失败: {e}")
            # 降级处理：逐个检查
            return await self._fallback_individual_check(user_permission_pairs)
    
    async def _batch_db_permission_check(
        self,
        user_permission_pairs: List[Tuple[int, str]]
    ) -> Dict[Tuple[int, str], bool]:
        """批量数据库权限检查"""
        results = {}
        
        # 按用户分组
        user_groups = defaultdict(list)
        for user_id, permission_code in user_permission_pairs:
            user_groups[user_id].append(permission_code)
        
        # 并发查询每个用户的权限
        tasks = []
        for user_id, permissions in user_groups.items():
            task = self._check_user_permissions_batch(user_id, permissions)
            tasks.append(task)
        
        # 等待所有查询完成
        user_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并结果
        for i, (user_id, permissions) in enumerate(user_groups.items()):
            user_result = user_results[i]
            if isinstance(user_result, Exception):
                logger.error(f"用户{user_id}权限查询失败: {user_result}")
                # 设置默认值
                for permission_code in permissions:
                    results[(user_id, permission_code)] = False
            else:
                for permission_code in permissions:
                    results[(user_id, permission_code)] = user_result.get(permission_code, False)
        
        return results
    
    async def _check_user_permissions_batch(
        self,
        user_id: int,
        permission_codes: List[str]
    ) -> Dict[str, bool]:
        """检查单个用户的多个权限"""
        try:
            # 使用现有的权限服务，但优化查询
            results = {}
            
            # 获取用户的所有权限（一次查询）
            user_permissions = await permission_service.get_user_permissions(user_id)
            user_permission_set = set(user_permissions)
            
            # 批量检查
            for permission_code in permission_codes:
                results[permission_code] = permission_code in user_permission_set
            
            return results
            
        except Exception as e:
            logger.error(f"用户{user_id}权限批量检查失败: {e}")
            return {code: False for code in permission_codes}
    
    async def _fallback_individual_check(
        self,
        user_permission_pairs: List[Tuple[int, str]]
    ) -> Dict[Tuple[int, str], bool]:
        """降级处理：逐个检查权限"""
        results = {}
        
        for user_id, permission_code in user_permission_pairs:
            try:
                has_permission = await permission_service.check_user_permission(
                    user_id, permission_code
                )
                results[(user_id, permission_code)] = has_permission
            except Exception as e:
                logger.error(f"权限检查失败 用户{user_id} 权限{permission_code}: {e}")
                results[(user_id, permission_code)] = False
        
        return results
    
    async def preload_user_permissions(self, user_ids: List[int]):
        """预加载用户权限"""
        if not self.enable_preload:
            return
        
        start_time = time.time()
        
        try:
            # 并发预加载
            tasks = []
            for user_id in user_ids:
                task = self._preload_single_user_permissions(user_id)
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            preload_time = time.time() - start_time
            logger.info(f"预加载{len(user_ids)}个用户权限完成, 耗时{preload_time:.3f}s")
            
        except Exception as e:
            logger.error(f"预加载用户权限失败: {e}")
    
    async def _preload_single_user_permissions(self, user_id: int):
        """预加载单个用户权限"""
        try:
            # 检查是否已经缓存
            cache_key = f"user_perms:{user_id}"
            cached_permissions = await permission_cache.get(cache_key)
            
            if cached_permissions is None:
                # 获取用户权限并缓存
                permissions = await permission_service.get_user_permissions(user_id)
                await permission_cache.set(cache_key, permissions, expire=600)  # 10分钟缓存
                
                # 同时缓存每个具体权限
                for permission in permissions:
                    perm_cache_key = f"perm:{user_id}:{permission}"
                    await permission_cache.set(perm_cache_key, True, expire=300)
                
                logger.debug(f"预加载用户{user_id}权限: {len(permissions)}项")
            
        except Exception as e:
            logger.error(f"预加载用户{user_id}权限失败: {e}")
    
    async def warm_up_cache(self):
        """缓存预热"""
        logger.info("开始权限缓存预热...")
        start_time = time.time()
        
        try:
            # 获取活跃用户列表
            active_users = await self._get_active_users()
            
            # 预加载活跃用户权限
            await self.preload_user_permissions(active_users)
            
            # 预加载常用权限组合
            await self._preload_common_permissions()
            
            warm_up_time = time.time() - start_time
            logger.info(f"权限缓存预热完成, 耗时{warm_up_time:.3f}s")
            
        except Exception as e:
            logger.error(f"权限缓存预热失败: {e}")
    
    async def _get_active_users(self) -> List[int]:
        """获取活跃用户列表"""
        try:
            # 这里应该从数据库获取最近活跃的用户
            # 暂时返回模拟数据
            return list(range(1, 101))  # 前100个用户
            
        except Exception as e:
            logger.error(f"获取活跃用户失败: {e}")
            return []
    
    async def _preload_common_permissions(self):
        """预加载常用权限"""
        try:
            # 常用权限列表
            common_permissions = [
                "GET /api/v2/users",
                "GET /api/v2/roles",
                "GET /api/v2/menus",
                "GET /api/v2/devices",
                "POST /api/v2/auth/login",
                "POST /api/v2/auth/logout"
            ]
            
            # 为活跃用户预加载这些权限
            active_users = await self._get_active_users()
            
            user_permission_pairs = []
            for user_id in active_users[:20]:  # 只处理前20个用户
                for permission in common_permissions:
                    user_permission_pairs.append((user_id, permission))
            
            # 批量检查并缓存
            await self.batch_check_permissions(user_permission_pairs)
            
            logger.info(f"预加载常用权限完成: {len(user_permission_pairs)}项")
            
        except Exception as e:
            logger.error(f"预加载常用权限失败: {e}")
    
    async def optimize_query_patterns(self):
        """优化查询模式"""
        if not self.enable_query_pattern_analysis:
            return
        
        try:
            # 分析查询模式
            top_patterns = sorted(
                self.query_patterns.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            logger.info("权限查询热点模式:")
            for pattern, count in top_patterns:
                logger.info(f"  {pattern}: {count}次")
            
            # 为热点模式预加载缓存
            await self._preload_hot_patterns(top_patterns)
            
        except Exception as e:
            logger.error(f"查询模式优化失败: {e}")
    
    async def _preload_hot_patterns(self, patterns: List[Tuple[str, int]]):
        """预加载热点模式"""
        try:
            for pattern, count in patterns:
                if count > 10:  # 只处理查询次数超过10次的模式
                    # 解析模式并预加载
                    await self._preload_pattern(pattern)
            
        except Exception as e:
            logger.error(f"预加载热点模式失败: {e}")
    
    async def _preload_pattern(self, pattern: str):
        """预加载特定模式"""
        try:
            # 这里可以根据模式类型进行不同的预加载策略
            # 暂时简单处理
            logger.debug(f"预加载模式: {pattern}")
            
        except Exception as e:
            logger.error(f"预加载模式{pattern}失败: {e}")
    
    def record_query_pattern(self, user_id: int, permission_code: str):
        """记录查询模式"""
        if not self.enable_query_pattern_analysis:
            return
        
        pattern = f"user_type:{self._get_user_type(user_id)}:perm:{permission_code}"
        self.query_patterns[pattern] += 1
    
    def _get_user_type(self, user_id: int) -> str:
        """获取用户类型（用于模式分析）"""
        # 简单的用户类型分类
        if user_id == 1:
            return "admin"
        elif user_id <= 10:
            return "manager"
        else:
            return "user"
    
    async def clear_user_cache(self, user_id: int):
        """清除用户相关缓存"""
        try:
            # 清除用户权限缓存
            cache_key = f"user_perms:{user_id}"
            await permission_cache.delete(cache_key)
            
            # 清除用户具体权限缓存（需要知道所有可能的权限）
            # 这里可以优化为使用缓存标签或前缀删除
            common_permissions = [
                "GET /api/v2/users",
                "POST /api/v2/users",
                "PUT /api/v2/users",
                "DELETE /api/v2/users",
                "GET /api/v2/roles",
                "POST /api/v2/roles",
                "PUT /api/v2/roles",
                "DELETE /api/v2/roles"
            ]
            
            for permission in common_permissions:
                perm_cache_key = f"perm:{user_id}:{permission}"
                await permission_cache.delete(perm_cache_key)
            
            logger.info(f"清除用户{user_id}权限缓存完成")
            
        except Exception as e:
            logger.error(f"清除用户{user_id}权限缓存失败: {e}")
    
    async def clear_permission_cache(self, permission_code: str):
        """清除特定权限的所有缓存"""
        try:
            # 这里需要实现前缀删除功能
            # 暂时记录日志
            logger.info(f"需要清除权限{permission_code}的所有缓存")
            
        except Exception as e:
            logger.error(f"清除权限{permission_code}缓存失败: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            "query_count": self.metrics.query_count,
            "cache_hits": self.metrics.cache_hits,
            "cache_misses": self.metrics.cache_misses,
            "cache_hit_rate": f"{self.metrics.cache_hit_rate:.2f}%",
            "avg_response_time": f"{self.metrics.avg_response_time:.3f}s",
            "batch_queries": self.metrics.batch_queries,
            "total_time": f"{self.metrics.total_time:.3f}s",
            "top_query_patterns": dict(
                sorted(self.query_patterns.items(), key=lambda x: x[1], reverse=True)[:5]
            )
        }
    
    def reset_metrics(self):
        """重置性能指标"""
        self.metrics = PerformanceMetrics()
        self.query_patterns.clear()
        logger.info("权限系统性能指标已重置")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            start_time = time.time()
            
            # 测试缓存连接
            test_key = "health_check_test"
            await permission_cache.set(test_key, "ok", expire=10)
            cache_result = await permission_cache.get(test_key)
            await permission_cache.delete(test_key)
            
            cache_ok = cache_result == "ok"
            response_time = time.time() - start_time
            
            return {
                "status": "healthy" if cache_ok else "unhealthy",
                "cache_connection": "ok" if cache_ok else "failed",
                "response_time": f"{response_time:.3f}s",
                "metrics": self.get_performance_metrics()
            }
            
        except Exception as e:
            logger.error(f"权限系统健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "cache_connection": "failed"
            }


# 全局权限性能优化服务实例
permission_performance_service = PermissionPerformanceService()