#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限验证性能优化器
实现多级缓存策略、权限预加载、批量检查等性能优化功能
"""

import asyncio
import time
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from collections import defaultdict
import weakref

from app.core.permission_validator import permission_validator
from app.core.permission_cache import permission_cache_manager
from app.core.redis_cache import redis_cache_manager
from app.log import logger


@dataclass
class PerformanceMetrics:
    """性能指标"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_response_time: float = 0.0
    max_response_time: float = 0.0
    min_response_time: float = float('inf')
    error_count: int = 0
    
    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100


class PermissionPerformanceOptimizer:
    """权限验证性能优化器"""
    
    def __init__(self):
        self.validator = permission_validator
        self.cache_manager = permission_cache_manager
        
        # 多级缓存配置
        self.l1_cache = {}  # 内存缓存（最快）
        self.l1_cache_size = 500
        self.l1_cache_ttl = 30  # 30秒
        
        # 预加载配置
        self.preload_enabled = True
        self.preload_batch_size = 50
        self.preload_interval = 300  # 5分钟
        
        # 批量处理配置
        self.batch_size = 20
        self.batch_timeout = 0.1  # 100ms
        
        # 性能监控
        self.metrics = PerformanceMetrics()
        self.performance_history = []
        self.monitoring_enabled = True
        
        # 权限预测缓存
        self.permission_patterns = defaultdict(list)
        self.pattern_cache = {}
        
        # 弱引用缓存（避免内存泄漏）
        self.weak_cache = weakref.WeakValueDictionary()
        
        # 启动后台任务
        self._background_tasks = []
        self._tasks_started = False
    
    async def _ensure_background_tasks(self):
        """确保后台任务已启动"""
        if self._tasks_started:
            return
        
        try:
            if self.preload_enabled:
                task = asyncio.create_task(self._preload_permissions_loop())
                self._background_tasks.append(task)
            
            if self.monitoring_enabled:
                task = asyncio.create_task(self._performance_monitoring_loop())
                self._background_tasks.append(task)
            
            # 缓存清理任务
            task = asyncio.create_task(self._cache_cleanup_loop())
            self._background_tasks.append(task)
            
            self._tasks_started = True
        except RuntimeError:
            # 没有运行的事件循环，跳过后台任务
            pass
    
    async def optimize_permission_check(
        self, 
        user_id: int, 
        permission: str,
        use_prediction: bool = True
    ) -> Tuple[bool, float]:
        """
        优化的权限检查
        
        Args:
            user_id: 用户ID
            permission: 权限标识
            use_prediction: 是否使用权限预测
            
        Returns:
            (是否有权限, 响应时间)
        """
        start_time = time.time()
        
        # 确保后台任务已启动
        await self._ensure_background_tasks()
        
        try:
            # 1. L1缓存检查（内存）
            cache_key = f"perm_{user_id}_{hash(permission)}"
            l1_result = self._get_from_l1_cache(cache_key)
            if l1_result is not None:
                response_time = (time.time() - start_time) * 1000
                self._update_metrics(True, response_time)
                return l1_result, response_time
            
            # 2. 权限预测检查
            if use_prediction:
                predicted_result = await self._predict_permission(user_id, permission)
                if predicted_result is not None:
                    self._set_to_l1_cache(cache_key, predicted_result)
                    response_time = (time.time() - start_time) * 1000
                    self._update_metrics(True, response_time)
                    return predicted_result, response_time
            
            # 3. 标准权限验证
            result = await self.validator.validate_user_permissions(user_id, permission)
            has_permission = result.has_permission
            
            # 4. 缓存结果
            self._set_to_l1_cache(cache_key, has_permission)
            await self.cache_manager.set_permission_validation_cache(
                user_id, permission, has_permission
            )
            
            # 5. 更新权限模式
            self._update_permission_patterns(user_id, permission, has_permission)
            
            response_time = (time.time() - start_time) * 1000
            self._update_metrics(False, response_time)
            
            return has_permission, response_time
            
        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"优化权限检查失败: user_id={user_id}, permission={permission}, 错误: {str(e)}")
            response_time = (time.time() - start_time) * 1000
            return False, response_time
    
    async def batch_permission_check(
        self, 
        requests: List[Tuple[int, str]]
    ) -> Dict[Tuple[int, str], bool]:
        """
        批量权限检查优化（增强版）
        
        Args:
            requests: [(user_id, permission), ...]
            
        Returns:
            {(user_id, permission): has_permission, ...}
        """
        start_time = time.time()
        results = {}
        
        try:
            # 1. 批量L1缓存检查
            cache_hits = {}
            cache_misses = []
            
            for user_id, permission in requests:
                cache_key = f"perm_{user_id}_{hash(permission)}"
                l1_result = self._get_from_l1_cache(cache_key)
                if l1_result is not None:
                    cache_hits[(user_id, permission)] = l1_result
                else:
                    cache_misses.append((user_id, permission))
            
            results.update(cache_hits)
            
            # 2. 批量Redis缓存检查
            if cache_misses:
                redis_hits = {}
                redis_misses = []
                
                # 并发检查Redis缓存
                redis_tasks = []
                for user_id, permission in cache_misses:
                    task = self.cache_manager.get_permission_validation_cache(user_id, permission)
                    redis_tasks.append(((user_id, permission), task))
                
                redis_results = await asyncio.gather(*[task for _, task in redis_tasks], return_exceptions=True)
                
                for i, ((user_id, permission), result) in enumerate(zip([req for req, _ in redis_tasks], redis_results)):
                    if isinstance(result, Exception) or result is None:
                        redis_misses.append((user_id, permission))
                    else:
                        redis_hits[(user_id, permission)] = result
                        # 更新L1缓存
                        cache_key = f"perm_{user_id}_{hash(permission)}"
                        self._set_to_l1_cache(cache_key, result)
                
                results.update(redis_hits)
                cache_misses = redis_misses
            
            # 3. 批量处理缓存未命中的请求
            if cache_misses:
                # 按用户分组以优化数据库查询
                user_groups = defaultdict(list)
                for user_id, permission in cache_misses:
                    user_groups[user_id].append(permission)
                
                # 并发处理每个用户的权限检查
                tasks = []
                for user_id, permissions in user_groups.items():
                    task = self._batch_check_user_permissions(user_id, permissions)
                    tasks.append(task)
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 合并结果
                for batch_result in batch_results:
                    if isinstance(batch_result, dict):
                        results.update(batch_result)
                    else:
                        logger.error(f"批量权限检查异常: {batch_result}")
            
            # 4. 更新性能指标
            total_time = (time.time() - start_time) * 1000
            avg_time = total_time / len(requests) if requests else 0
            
            for _ in cache_hits:
                self._update_metrics(True, avg_time)
            for _ in results:
                if (_, _) not in cache_hits:
                    self._update_metrics(False, avg_time)
            
            return results
            
        except Exception as e:
            logger.error(f"批量权限检查失败: 错误: {str(e)}")
            return {req: False for req in requests}
    
    async def _batch_check_user_permissions(
        self, 
        user_id: int, 
        permissions: List[str]
    ) -> Dict[Tuple[int, str], bool]:
        """批量检查单个用户的多个权限（优化版）"""
        results = {}
        
        try:
            # 获取用户权限信息（一次数据库查询）
            user_permission_info = await self.validator.get_user_permission_info(user_id)
            if not user_permission_info:
                return {(user_id, perm): False for perm in permissions}
            
            # 批量验证权限（优化：减少循环调用）
            user_permissions_list = list(user_permission_info.permissions)
            
            for permission in permissions:
                has_permission = await self.validator.has_permission(
                    user_permissions_list, 
                    permission
                )
                results[(user_id, permission)] = has_permission
                
                # 缓存结果到L1
                cache_key = f"perm_{user_id}_{hash(permission)}"
                self._set_to_l1_cache(cache_key, has_permission)
            
            # 批量异步缓存到Redis（减少Redis连接数）
            asyncio.create_task(
                self._batch_cache_to_redis(user_id, permissions, results)
            )
            
            return results
            
        except Exception as e:
            logger.error(f"批量检查用户权限失败: user_id={user_id}, 错误: {str(e)}")
            return {(user_id, perm): False for perm in permissions}
    
    async def _batch_cache_to_redis(
        self, 
        user_id: int, 
        permissions: List[str], 
        results: Dict[Tuple[int, str], bool]
    ):
        """批量缓存权限验证结果到Redis"""
        try:
            cache_tasks = []
            for permission in permissions:
                has_permission = results.get((user_id, permission), False)
                task = self.cache_manager.set_permission_validation_cache(
                    user_id, permission, has_permission
                )
                cache_tasks.append(task)
            
            # 并发执行所有缓存操作
            await asyncio.gather(*cache_tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"批量缓存到Redis失败: user_id={user_id}, 错误: {str(e)}")
    
    async def optimize_database_queries(self) -> Dict[str, Any]:
        """
        优化权限验证的数据库查询
        
        Returns:
            优化结果统计
        """
        try:
            optimization_results = {
                "user_permission_queries": 0,
                "role_permission_queries": 0,
                "api_definition_queries": 0,
                "optimized_queries": 0,
                "cache_preloaded": 0
            }
            
            # 1. 预加载常用权限定义
            await self._preload_api_definitions()
            optimization_results["api_definition_queries"] += 1
            
            # 2. 预加载活跃用户权限
            from app.models.admin import User
            active_users = await User.filter(
                is_active=True,
                login_date__gte=datetime.now() - timedelta(days=7)
            ).limit(50).all()
            
            user_ids = [user.id for user in active_users]
            preload_result = await self.preload_user_permissions(user_ids)
            optimization_results["cache_preloaded"] = preload_result["success"]
            
            # 3. 优化角色权限查询
            await self._optimize_role_permission_queries()
            optimization_results["role_permission_queries"] += 1
            
            # 4. 建立权限查询索引建议
            index_suggestions = await self._analyze_permission_query_patterns()
            optimization_results["index_suggestions"] = index_suggestions
            
            logger.info(f"数据库查询优化完成: {optimization_results}")
            return optimization_results
            
        except Exception as e:
            logger.error(f"数据库查询优化失败: {str(e)}")
            return {"error": str(e)}
    
    async def _preload_api_definitions(self):
        """预加载API定义"""
        try:
            from app.models.admin import SysApiEndpoint as Api
            
            # 获取所有API定义并缓存
            apis = await Api.all()
            api_cache = {}
            
            for api in apis:
                permission_key = f"{api.http_method} {api.api_path}"
                api_cache[permission_key] = {
                    "id": api.id,
                    "summary": getattr(api, 'description', '') or getattr(api, 'api_name', ''),
                    "method": api.http_method,
                    "path": api.api_path,
                    "group": getattr(api, 'group', 'default')
                }
            
            # 缓存API定义
            await redis_cache_manager.set("api_definitions", api_cache, ttl=3600)
            logger.info(f"预加载了{len(apis)}个API定义")
            
        except Exception as e:
            logger.error(f"预加载API定义失败: {str(e)}")
    
    async def _optimize_role_permission_queries(self):
        """优化角色权限查询"""
        try:
            from app.models.admin import Role
            
            # 预加载所有角色的权限
            roles = await Role.all().prefetch_related("apis")
            
            for role in roles:
                role_permissions = set()
                for api in role.apis:
                    permission = f"{api.http_method} {api.api_path}"
                    role_permissions.add(permission)
                
                # 缓存角色权限
                await self.cache_manager.set_role_permissions(
                    role.id, 
                    {
                        "role_id": role.id,
                        "role_name": role.role_name,
                        "permissions": list(role_permissions)
                    }
                )
            
            logger.info(f"优化了{len(roles)}个角色的权限查询")
            
        except Exception as e:
            logger.error(f"优化角色权限查询失败: {str(e)}")
    
    async def _analyze_permission_query_patterns(self) -> List[str]:
        """分析权限查询模式并提供索引建议"""
        try:
            suggestions = []
            
            # 基于常见查询模式的索引建议
            suggestions.extend([
                "CREATE INDEX idx_user_roles_user_id ON user_roles(user_id)",
                "CREATE INDEX idx_role_apis_role_id ON role_apis(role_id)", 
                "CREATE INDEX idx_apis_method_path ON apis(method, path)",
                "CREATE INDEX idx_users_active_login ON users(is_active, last_login)",
                "CREATE INDEX idx_roles_active ON roles(is_active)",
                "CREATE UNIQUE INDEX idx_permission_cache ON permission_cache(user_id, permission_hash)"
            ])
            
            return suggestions
            
        except Exception as e:
            logger.error(f"分析权限查询模式失败: {str(e)}")
            return []
    
    async def preload_user_permissions(self, user_ids: List[int]) -> Dict[str, int]:
        """
        预加载用户权限
        
        Args:
            user_ids: 用户ID列表
            
        Returns:
            预加载结果统计
        """
        start_time = time.time()
        success_count = 0
        error_count = 0
        
        try:
            # 分批处理
            for i in range(0, len(user_ids), self.preload_batch_size):
                batch_user_ids = user_ids[i:i + self.preload_batch_size]
                
                # 并发预加载
                tasks = []
                for user_id in batch_user_ids:
                    task = self._preload_single_user(user_id)
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        error_count += 1
                        logger.error(f"预加载用户权限失败: {result}")
                    else:
                        success_count += 1
                
                # 避免过度负载
                await asyncio.sleep(0.01)
            
            total_time = time.time() - start_time
            logger.info(f"权限预加载完成: 成功={success_count}, 失败={error_count}, 耗时={total_time:.2f}秒")
            
            return {
                "success": success_count,
                "error": error_count,
                "total_time": total_time
            }
            
        except Exception as e:
            logger.error(f"批量预加载权限失败: {str(e)}")
            return {"success": 0, "error": len(user_ids), "total_time": 0}
    
    async def _preload_single_user(self, user_id: int) -> bool:
        """预加载单个用户的权限"""
        try:
            # 检查是否已缓存
            cached_permissions = await self.cache_manager.get_user_permissions(user_id)
            if cached_permissions:
                return True
            
            # 获取用户权限信息
            user_permission_info = await self.validator.get_user_permission_info(user_id)
            if not user_permission_info:
                return False
            
            # 预加载常用权限
            common_permissions = [
                "GET /api/v2/users",
                "GET /api/v2/roles", 
                "GET /api/v2/menus",
                "GET /api/v2/devices",
                "GET /api/v2/dashboard/overview"
            ]
            
            for permission in common_permissions:
                has_permission = await self.validator.has_permission(
                    list(user_permission_info.permissions), 
                    permission
                )
                
                # 缓存到L1
                cache_key = f"perm_{user_id}_{hash(permission)}"
                self._set_to_l1_cache(cache_key, has_permission)
                
                # 异步缓存到Redis
                asyncio.create_task(
                    self.cache_manager.set_permission_validation_cache(
                        user_id, permission, has_permission
                    )
                )
            
            return True
            
        except Exception as e:
            logger.error(f"预加载用户权限失败: user_id={user_id}, 错误: {str(e)}")
            return False
    
    async def _predict_permission(self, user_id: int, permission: str) -> Optional[bool]:
        """权限预测"""
        try:
            # 基于历史模式预测
            pattern_key = f"pattern_{user_id}"
            if pattern_key in self.permission_patterns:
                patterns = self.permission_patterns[pattern_key]
                
                # 查找相似权限
                for past_permission, result in patterns[-10:]:  # 最近10个权限
                    if self._is_similar_permission(permission, past_permission):
                        return result
            
            return None
            
        except Exception as e:
            logger.error(f"权限预测失败: user_id={user_id}, permission={permission}, 错误: {str(e)}")
            return None
    
    def _is_similar_permission(self, perm1: str, perm2: str) -> bool:
        """判断权限是否相似"""
        try:
            # 简单的相似性判断
            parts1 = perm1.split()
            parts2 = perm2.split()
            
            if len(parts1) != 2 or len(parts2) != 2:
                return False
            
            method1, path1 = parts1
            method2, path2 = parts2
            
            # 相同方法和相似路径
            if method1 == method2:
                path1_parts = path1.split('/')
                path2_parts = path2.split('/')
                
                if len(path1_parts) >= 4 and len(path2_parts) >= 4:
                    # 比较资源类型
                    return path1_parts[3] == path2_parts[3]
            
            return False
            
        except Exception:
            return False
    
    def _update_permission_patterns(self, user_id: int, permission: str, result: bool):
        """更新权限模式"""
        try:
            pattern_key = f"pattern_{user_id}"
            self.permission_patterns[pattern_key].append((permission, result))
            
            # 保持最近100个记录
            if len(self.permission_patterns[pattern_key]) > 100:
                self.permission_patterns[pattern_key] = self.permission_patterns[pattern_key][-100:]
                
        except Exception as e:
            logger.error(f"更新权限模式失败: {str(e)}")
    
    def _get_from_l1_cache(self, key: str) -> Optional[bool]:
        """从L1缓存获取"""
        try:
            if key in self.l1_cache:
                item = self.l1_cache[key]
                expires_at = item['expires_at']
                # 如果expires_at是字符串，转换为datetime对象
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                
                if datetime.now() < expires_at:
                    return item['value']
                else:
                    del self.l1_cache[key]
            return None
        except Exception:
            return None
    
    def _set_to_l1_cache(self, key: str, value: bool):
        """设置L1缓存"""
        try:
            # 清理过期项
            if len(self.l1_cache) >= self.l1_cache_size:
                self._cleanup_l1_cache()
            
            self.l1_cache[key] = {
                'value': value,
                'expires_at': datetime.now() + timedelta(seconds=self.l1_cache_ttl)
            }
        except Exception as e:
            logger.error(f"设置L1缓存失败: {str(e)}")
    
    def _cleanup_l1_cache(self):
        """清理L1缓存"""
        try:
            current_time = datetime.now()
            expired_keys = [
                key for key, item in self.l1_cache.items()
                if current_time >= item['expires_at']
            ]
            
            for key in expired_keys:
                del self.l1_cache[key]
            
            # 如果还是太满，删除最旧的
            if len(self.l1_cache) >= self.l1_cache_size:
                sorted_items = sorted(
                    self.l1_cache.items(),
                    key=lambda x: x[1]['expires_at']
                )
                
                items_to_delete = len(sorted_items) // 4
                for i in range(items_to_delete):
                    key = sorted_items[i][0]
                    del self.l1_cache[key]
                    
        except Exception as e:
            logger.error(f"清理L1缓存失败: {str(e)}")
    
    def _update_metrics(self, cache_hit: bool, response_time: float):
        """更新性能指标"""
        try:
            self.metrics.total_requests += 1
            
            if cache_hit:
                self.metrics.cache_hits += 1
            else:
                self.metrics.cache_misses += 1
            
            # 更新响应时间统计
            if response_time > self.metrics.max_response_time:
                self.metrics.max_response_time = response_time
            
            if response_time < self.metrics.min_response_time:
                self.metrics.min_response_time = response_time
            
            # 计算平均响应时间
            total_time = self.metrics.avg_response_time * (self.metrics.total_requests - 1) + response_time
            self.metrics.avg_response_time = total_time / self.metrics.total_requests
            
        except Exception as e:
            logger.error(f"更新性能指标失败: {str(e)}")
    
    async def _preload_permissions_loop(self):
        """权限预加载循环任务"""
        while True:
            try:
                await asyncio.sleep(self.preload_interval)
                
                # 获取活跃用户
                from app.models.admin import User
                active_users = await User.filter(
                    is_active=True,
                    login_date__gte=datetime.now() - timedelta(days=7)
                ).limit(100).all()
                
                user_ids = [user.id for user in active_users]
                if user_ids:
                    await self.preload_user_permissions(user_ids)
                    
            except Exception as e:
                logger.error(f"权限预加载循环任务失败: {str(e)}")
                await asyncio.sleep(60)  # 出错后等待1分钟再重试
    
    async def _performance_monitoring_loop(self):
        """性能监控循环任务（增强版）"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟记录一次
                
                # 记录性能历史
                snapshot = {
                    'timestamp': datetime.now().isoformat(),
                    'total_requests': self.metrics.total_requests,
                    'hit_rate': self.metrics.hit_rate,
                    'avg_response_time': self.metrics.avg_response_time,
                    'max_response_time': self.metrics.max_response_time,
                    'min_response_time': self.metrics.min_response_time,
                    'error_count': self.metrics.error_count,
                    'l1_cache_size': len(self.l1_cache),
                    'l1_cache_usage': f"{len(self.l1_cache) / self.l1_cache_size * 100:.1f}%",
                    'pattern_cache_size': len(self.permission_patterns)
                }
                
                self.performance_history.append(snapshot)
                
                # 保持最近24小时的记录
                if len(self.performance_history) > 1440:  # 24 * 60
                    self.performance_history = self.performance_history[-1440:]
                
                # 增强的性能告警
                await self._check_performance_alerts(snapshot)
                
                # 自动优化触发
                await self._auto_optimization_check(snapshot)
                
            except Exception as e:
                logger.error(f"性能监控循环任务失败: {str(e)}")
    
    async def _check_performance_alerts(self, snapshot: Dict[str, Any]):
        """检查性能告警（增强版）"""
        try:
            # 缓存命中率告警
            if self.metrics.hit_rate < 80 and self.metrics.total_requests > 100:
                logger.warning(f"权限缓存命中率过低: {self.metrics.hit_rate:.1f}%")
                await self._trigger_cache_optimization()
            
            # 响应时间告警
            if self.metrics.avg_response_time > 100:  # 100ms
                logger.warning(f"权限验证平均响应时间过高: {self.metrics.avg_response_time:.1f}ms")
                await self._trigger_performance_optimization()
            
            # 错误率告警
            if self.metrics.total_requests > 0:
                error_rate = (self.metrics.error_count / self.metrics.total_requests) * 100
                if error_rate > 5:  # 5%
                    logger.warning(f"权限验证错误率过高: {error_rate:.1f}%")
            
            # 内存使用告警
            l1_usage = len(self.l1_cache) / self.l1_cache_size
            if l1_usage > 0.9:
                logger.warning(f"L1缓存使用率过高: {l1_usage * 100:.1f}%")
                self._cleanup_l1_cache()
            
            # 性能趋势分析
            if len(self.performance_history) >= 5:
                await self._analyze_performance_trends()
                
        except Exception as e:
            logger.error(f"性能告警检查失败: {str(e)}")
    
    async def _auto_optimization_check(self, snapshot: Dict[str, Any]):
        """自动优化检查"""
        try:
            # 如果命中率持续低于阈值，触发预加载
            if (self.metrics.hit_rate < 70 and 
                self.metrics.total_requests > 200 and 
                len(self.performance_history) >= 3):
                
                recent_hit_rates = [
                    float(h['hit_rate']) for h in self.performance_history[-3:]
                ]
                
                if all(rate < 70 for rate in recent_hit_rates):
                    logger.info("触发自动权限预加载优化")
                    await self._auto_preload_optimization()
            
            # 如果响应时间持续过高，触发缓存清理
            if (self.metrics.avg_response_time > 50 and 
                len(self.performance_history) >= 3):
                
                recent_response_times = [
                    h['avg_response_time'] for h in self.performance_history[-3:]
                ]
                
                if all(time > 50 for time in recent_response_times):
                    logger.info("触发自动缓存清理优化")
                    self._cleanup_l1_cache()
                    
        except Exception as e:
            logger.error(f"自动优化检查失败: {str(e)}")
    
    async def _analyze_performance_trends(self):
        """分析性能趋势"""
        try:
            if len(self.performance_history) < 5:
                return
            
            recent_data = self.performance_history[-5:]
            
            # 分析命中率趋势
            hit_rates = [float(d['hit_rate']) for d in recent_data]
            hit_rate_trend = hit_rates[-1] - hit_rates[0]
            
            # 分析响应时间趋势
            response_times = [d['avg_response_time'] for d in recent_data]
            response_time_trend = response_times[-1] - response_times[0]
            
            # 记录趋势分析结果
            if hit_rate_trend < -10:  # 命中率下降超过10%
                logger.info(f"权限缓存命中率呈下降趋势: {hit_rate_trend:.1f}%")
            
            if response_time_trend > 20:  # 响应时间增加超过20ms
                logger.info(f"权限验证响应时间呈上升趋势: +{response_time_trend:.1f}ms")
                
        except Exception as e:
            logger.error(f"性能趋势分析失败: {str(e)}")
    
    async def _trigger_cache_optimization(self):
        """触发缓存优化"""
        try:
            # 清理过期缓存
            self._cleanup_l1_cache()
            
            # 预加载热点权限
            await self._preload_hot_permissions()
            
            logger.info("缓存优化已触发")
            
        except Exception as e:
            logger.error(f"缓存优化失败: {str(e)}")
    
    async def _trigger_performance_optimization(self):
        """触发性能优化"""
        try:
            # 数据库查询优化
            await self.optimize_database_queries()
            
            # 调整缓存策略
            if self.l1_cache_ttl < 60:
                self.l1_cache_ttl = min(self.l1_cache_ttl * 1.5, 60)
                logger.info(f"调整L1缓存TTL为: {self.l1_cache_ttl}秒")
            
            logger.info("性能优化已触发")
            
        except Exception as e:
            logger.error(f"性能优化失败: {str(e)}")
    
    async def _auto_preload_optimization(self):
        """自动预加载优化"""
        try:
            # 获取最近活跃的用户
            from app.models.admin import User
            active_users = await User.filter(
                is_active=True,
                login_date__gte=datetime.now() - timedelta(hours=1)
            ).limit(20).all()
            
            user_ids = [user.id for user in active_users]
            if user_ids:
                await self.preload_user_permissions(user_ids)
                logger.info(f"自动预加载了{len(user_ids)}个活跃用户的权限")
                
        except Exception as e:
            logger.error(f"自动预加载优化失败: {str(e)}")
    
    async def _preload_hot_permissions(self):
        """预加载热点权限"""
        try:
            # 分析权限访问模式，找出热点权限
            hot_permissions = [
                "GET /api/v2/users",
                "GET /api/v2/dashboard/overview",
                "GET /api/v2/menus",
                "GET /api/v2/roles",
                "GET /api/v2/devices"
            ]
            
            # 为最近活跃用户预加载热点权限
            from app.models.admin import User
            active_users = await User.filter(
                is_active=True,
                login_date__gte=datetime.now() - timedelta(hours=2)
            ).limit(10).all()
            
            for user in active_users:
                for permission in hot_permissions:
                    # 检查是否已缓存
                    cache_key = f"perm_{user.id}_{hash(permission)}"
                    if self._get_from_l1_cache(cache_key) is None:
                        # 异步预加载
                        asyncio.create_task(
                            self.optimize_permission_check(user.id, permission, use_prediction=False)
                        )
            
            logger.info(f"预加载了{len(hot_permissions)}个热点权限")
            
        except Exception as e:
            logger.error(f"预加载热点权限失败: {str(e)}")
    
    async def _cache_cleanup_loop(self):
        """缓存清理循环任务"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次
                
                # 清理L1缓存
                self._cleanup_l1_cache()
                
                # 清理权限模式（保持最近的记录）
                for pattern_key in list(self.permission_patterns.keys()):
                    patterns = self.permission_patterns[pattern_key]
                    if len(patterns) > 100:
                        self.permission_patterns[pattern_key] = patterns[-100:]
                
            except Exception as e:
                logger.error(f"缓存清理循环任务失败: {str(e)}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告（增强版）"""
        try:
            return {
                "current_metrics": {
                    "total_requests": self.metrics.total_requests,
                    "cache_hits": self.metrics.cache_hits,
                    "cache_misses": self.metrics.cache_misses,
                    "hit_rate": f"{self.metrics.hit_rate:.1f}%",
                    "avg_response_time": f"{self.metrics.avg_response_time:.2f}ms",
                    "max_response_time": f"{self.metrics.max_response_time:.2f}ms",
                    "min_response_time": f"{self.metrics.min_response_time:.2f}ms",
                    "error_count": self.metrics.error_count,
                    "error_rate": f"{(self.metrics.error_count / max(self.metrics.total_requests, 1)) * 100:.2f}%"
                },
                "cache_status": {
                    "l1_cache_size": len(self.l1_cache),
                    "l1_cache_max_size": self.l1_cache_size,
                    "l1_cache_usage": f"{len(self.l1_cache) / self.l1_cache_size * 100:.1f}%",
                    "pattern_cache_size": len(self.permission_patterns),
                    "weak_cache_size": len(self.weak_cache)
                },
                "configuration": {
                    "preload_enabled": self.preload_enabled,
                    "preload_batch_size": self.preload_batch_size,
                    "preload_interval": self.preload_interval,
                    "batch_size": self.batch_size,
                    "l1_cache_ttl": self.l1_cache_ttl,
                    "monitoring_enabled": self.monitoring_enabled
                },
                "performance_trends": self._analyze_performance_trends_sync(),
                "recent_performance": self.performance_history[-10:] if self.performance_history else [],
                "optimization_suggestions": self._get_optimization_suggestions()
            }
        except Exception as e:
            logger.error(f"获取性能报告失败: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_performance_trends_sync(self) -> Dict[str, Any]:
        """同步分析性能趋势"""
        try:
            if len(self.performance_history) < 5:
                return {"status": "insufficient_data"}
            
            recent_data = self.performance_history[-5:]
            
            # 分析各项指标趋势
            hit_rates = [float(d['hit_rate']) for d in recent_data]
            response_times = [d['avg_response_time'] for d in recent_data]
            
            trends = {
                "hit_rate_trend": {
                    "direction": "stable",
                    "change": 0.0,
                    "status": "good"
                },
                "response_time_trend": {
                    "direction": "stable", 
                    "change": 0.0,
                    "status": "good"
                }
            }
            
            # 命中率趋势
            hit_rate_change = hit_rates[-1] - hit_rates[0]
            if abs(hit_rate_change) > 5:
                trends["hit_rate_trend"]["direction"] = "improving" if hit_rate_change > 0 else "declining"
                trends["hit_rate_trend"]["change"] = hit_rate_change
                trends["hit_rate_trend"]["status"] = "good" if hit_rate_change > 0 else "warning"
            
            # 响应时间趋势
            response_time_change = response_times[-1] - response_times[0]
            if abs(response_time_change) > 10:
                trends["response_time_trend"]["direction"] = "improving" if response_time_change < 0 else "declining"
                trends["response_time_trend"]["change"] = response_time_change
                trends["response_time_trend"]["status"] = "good" if response_time_change < 0 else "warning"
            
            return trends
            
        except Exception as e:
            logger.error(f"同步性能趋势分析失败: {str(e)}")
            return {"error": str(e)}
    
    def _get_optimization_suggestions(self) -> List[Dict[str, str]]:
        """获取优化建议"""
        suggestions = []
        
        try:
            # 基于当前性能指标提供建议
            if self.metrics.hit_rate < 80 and self.metrics.total_requests > 100:
                suggestions.append({
                    "type": "cache_optimization",
                    "priority": "high",
                    "suggestion": "缓存命中率过低，建议增加预加载或调整缓存策略",
                    "action": "enable_preload"
                })
            
            if self.metrics.avg_response_time > 100:
                suggestions.append({
                    "type": "performance_optimization",
                    "priority": "high", 
                    "suggestion": "平均响应时间过高，建议优化数据库查询或增加缓存层级",
                    "action": "optimize_queries"
                })
            
            if len(self.l1_cache) / self.l1_cache_size > 0.9:
                suggestions.append({
                    "type": "memory_optimization",
                    "priority": "medium",
                    "suggestion": "L1缓存使用率过高，建议增加缓存大小或调整清理策略",
                    "action": "increase_cache_size"
                })
            
            if self.metrics.error_count > 0:
                error_rate = (self.metrics.error_count / max(self.metrics.total_requests, 1)) * 100
                if error_rate > 1:
                    suggestions.append({
                        "type": "error_handling",
                        "priority": "high",
                        "suggestion": f"错误率过高({error_rate:.1f}%)，建议检查权限配置和数据库连接",
                        "action": "check_errors"
                    })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"获取优化建议失败: {str(e)}")
            return []
    
    async def get_detailed_performance_analysis(self) -> Dict[str, Any]:
        """获取详细性能分析"""
        try:
            # 获取缓存管理器统计
            cache_stats = await self.cache_manager.get_cache_statistics()
            
            # 计算性能指标
            analysis = {
                "summary": {
                    "overall_status": self._calculate_overall_status(),
                    "performance_score": self._calculate_performance_score(),
                    "recommendations": self._get_optimization_suggestions()
                },
                "detailed_metrics": {
                    "optimizer_metrics": {
                        "total_requests": self.metrics.total_requests,
                        "hit_rate": self.metrics.hit_rate,
                        "avg_response_time": self.metrics.avg_response_time,
                        "error_count": self.metrics.error_count
                    },
                    "cache_metrics": cache_stats,
                    "memory_usage": {
                        "l1_cache_items": len(self.l1_cache),
                        "pattern_cache_items": len(self.permission_patterns),
                        "weak_cache_items": len(self.weak_cache)
                    }
                },
                "performance_history": {
                    "recent_snapshots": self.performance_history[-20:],
                    "trends": self._analyze_performance_trends_sync()
                },
                "optimization_opportunities": await self._identify_optimization_opportunities()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"获取详细性能分析失败: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_overall_status(self) -> str:
        """计算整体状态"""
        try:
            if self.metrics.total_requests == 0:
                return "no_data"
            
            score = 0
            
            # 命中率评分 (40%)
            if self.metrics.hit_rate >= 90:
                score += 40
            elif self.metrics.hit_rate >= 80:
                score += 32
            elif self.metrics.hit_rate >= 70:
                score += 24
            elif self.metrics.hit_rate >= 60:
                score += 16
            else:
                score += 8
            
            # 响应时间评分 (40%)
            if self.metrics.avg_response_time <= 10:
                score += 40
            elif self.metrics.avg_response_time <= 50:
                score += 32
            elif self.metrics.avg_response_time <= 100:
                score += 24
            elif self.metrics.avg_response_time <= 200:
                score += 16
            else:
                score += 8
            
            # 错误率评分 (20%)
            error_rate = (self.metrics.error_count / self.metrics.total_requests) * 100
            if error_rate == 0:
                score += 20
            elif error_rate <= 1:
                score += 16
            elif error_rate <= 5:
                score += 12
            elif error_rate <= 10:
                score += 8
            else:
                score += 4
            
            # 根据总分确定状态
            if score >= 90:
                return "excellent"
            elif score >= 80:
                return "good"
            elif score >= 70:
                return "fair"
            elif score >= 60:
                return "poor"
            else:
                return "critical"
                
        except Exception:
            return "unknown"
    
    def _calculate_performance_score(self) -> int:
        """计算性能评分 (0-100)"""
        try:
            if self.metrics.total_requests == 0:
                return 0
            
            # 命中率权重 40%
            hit_rate_score = min(self.metrics.hit_rate, 100) * 0.4
            
            # 响应时间权重 40% (响应时间越低分数越高)
            response_time_score = max(0, 100 - self.metrics.avg_response_time) * 0.4
            
            # 错误率权重 20%
            error_rate = (self.metrics.error_count / self.metrics.total_requests) * 100
            error_score = max(0, 100 - error_rate * 10) * 0.2
            
            total_score = hit_rate_score + response_time_score + error_score
            return int(min(100, max(0, total_score)))
            
        except Exception:
            return 0
    
    async def _identify_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """识别优化机会"""
        opportunities = []
        
        try:
            # 分析缓存效率
            if self.metrics.hit_rate < 85:
                opportunities.append({
                    "area": "cache_efficiency",
                    "current_value": f"{self.metrics.hit_rate:.1f}%",
                    "target_value": "85%+",
                    "impact": "high",
                    "effort": "medium",
                    "actions": [
                        "启用权限预加载",
                        "调整缓存TTL",
                        "优化缓存键策略"
                    ]
                })
            
            # 分析响应时间
            if self.metrics.avg_response_time > 50:
                opportunities.append({
                    "area": "response_time",
                    "current_value": f"{self.metrics.avg_response_time:.1f}ms",
                    "target_value": "50ms以下",
                    "impact": "high",
                    "effort": "high",
                    "actions": [
                        "优化数据库查询",
                        "增加索引",
                        "实现查询结果缓存"
                    ]
                })
            
            # 分析内存使用
            l1_usage = len(self.l1_cache) / self.l1_cache_size
            if l1_usage > 0.8:
                opportunities.append({
                    "area": "memory_usage",
                    "current_value": f"{l1_usage * 100:.1f}%",
                    "target_value": "80%以下",
                    "impact": "medium",
                    "effort": "low",
                    "actions": [
                        "增加L1缓存大小",
                        "优化缓存清理策略",
                        "实现LRU淘汰算法"
                    ]
                })
            
            return opportunities
            
        except Exception as e:
            logger.error(f"识别优化机会失败: {str(e)}")
            return []
    
    def reset_metrics(self):
        """重置性能指标"""
        self.metrics = PerformanceMetrics()
        self.performance_history.clear()
        logger.info("权限性能指标已重置")
    
    async def shutdown(self):
        """关闭优化器"""
        try:
            # 取消后台任务
            for task in self._background_tasks:
                task.cancel()
            
            # 等待任务完成
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
            
            logger.info("权限性能优化器已关闭")
        except Exception as e:
            logger.error(f"关闭权限性能优化器失败: {str(e)}")


# 全局权限性能优化器实例（延迟初始化）
permission_performance_optimizer = None

def get_permission_performance_optimizer() -> PermissionPerformanceOptimizer:
    """获取权限性能优化器实例"""
    global permission_performance_optimizer
    if permission_performance_optimizer is None:
        permission_performance_optimizer = PermissionPerformanceOptimizer()
    return permission_performance_optimizer