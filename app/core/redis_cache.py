# -*- coding: utf-8 -*-
"""
Redis缓存管理器

提供Redis缓存的统一接口和管理功能
"""

import json
import pickle
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from functools import wraps

import redis.asyncio as redis
from redis.asyncio import Redis

from app.log import logger


class RedisConfig:
    """Redis配置类"""
    
    def __init__(self):
        import os
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", "6379"))
        self.db = int(os.getenv("REDIS_DB", "0"))
        self.password = os.getenv("REDIS_PASSWORD", "")
        self.max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS", "20"))
        self.socket_timeout = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
        self.socket_connect_timeout = int(os.getenv("REDIS_CONNECT_TIMEOUT", "5"))
        self.retry_on_timeout = True
        self.health_check_interval = 30
    
    def get_connection_kwargs(self) -> Dict[str, Any]:
        """获取Redis连接参数"""
        kwargs = {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "socket_timeout": self.socket_timeout,
            "socket_connect_timeout": self.socket_connect_timeout,
            "retry_on_timeout": self.retry_on_timeout,
            "health_check_interval": self.health_check_interval,
            "max_connections": self.max_connections,
        }
        
        if self.password:
            kwargs["password"] = self.password
        
        return kwargs


class RedisManager:
    """Redis管理器"""
    
    def __init__(self, config: RedisConfig = None):
        self.config = config or RedisConfig()
        self._redis: Optional[Redis] = None
        self._connection_pool = None
        self._is_connected = False
    
    async def connect(self) -> None:
        """连接Redis"""
        try:
            connection_kwargs = self.config.get_connection_kwargs()
            
            # 创建连接池
            self._connection_pool = redis.ConnectionPool(**connection_kwargs)
            
            # 创建Redis客户端
            self._redis = Redis(connection_pool=self._connection_pool)
            
            # 测试连接
            await self._redis.ping()
            self._is_connected = True
            
            logger.info(f"Redis连接成功: {self.config.host}:{self.config.port}")
            
        except Exception as e:
            logger.error(f"Redis连接失败: {str(e)}")
            self._is_connected = False
            raise
    
    async def disconnect(self) -> None:
        """断开Redis连接"""
        if self._redis:
            await self._redis.close()
            self._is_connected = False
            logger.info("Redis连接已关闭")
    
    async def is_connected(self) -> bool:
        """检查连接状态"""
        if not self._redis or not self._is_connected:
            return False
        
        try:
            await self._redis.ping()
            return True
        except Exception:
            self._is_connected = False
            return False
    
    async def ensure_connection(self) -> None:
        """确保连接可用"""
        if not await self.is_connected():
            await self.connect()
    
    @property
    def redis(self) -> Redis:
        """获取Redis客户端"""
        if not self._redis:
            raise RuntimeError("Redis未连接，请先调用connect()方法")
        return self._redis


class RedisCacheManager:
    """Redis缓存管理器"""
    
    def __init__(self, redis_manager: RedisManager = None):
        self.redis_manager = redis_manager or RedisManager()
        self.default_ttl = 300  # 5分钟默认TTL
        self.key_prefix = "device_monitor:"
    
    async def initialize(self) -> None:
        """初始化缓存管理器"""
        await self.redis_manager.connect()
    
    async def close(self) -> None:
        """关闭缓存管理器"""
        await self.redis_manager.disconnect()
    
    def _build_key(self, key: str) -> str:
        """构建缓存键"""
        return f"{self.key_prefix}{key}"
    
    async def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        try:
            await self.redis_manager.ensure_connection()
            redis_client = self.redis_manager.redis
            
            full_key = self._build_key(key)
            value = await redis_client.get(full_key)
            
            if value is None:
                return default
            
            # 尝试JSON反序列化
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # 如果JSON反序列化失败，尝试pickle
                try:
                    return pickle.loads(value)
                except (pickle.PickleError, TypeError):
                    # 如果都失败，返回原始字符串
                    return value.decode('utf-8') if isinstance(value, bytes) else value
        
        except Exception as e:
            logger.error(f"获取缓存失败 {key}: {str(e)}")
            return default
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        serialize_method: str = "json"
    ) -> bool:
        """设置缓存值"""
        try:
            await self.redis_manager.ensure_connection()
            redis_client = self.redis_manager.redis
            
            full_key = self._build_key(key)
            ttl = ttl or self.default_ttl
            
            # 序列化值
            if serialize_method == "json":
                try:
                    serialized_value = json.dumps(value, default=str, ensure_ascii=False)
                except (TypeError, ValueError):
                    # JSON序列化失败，使用pickle
                    serialized_value = pickle.dumps(value)
            elif serialize_method == "pickle":
                serialized_value = pickle.dumps(value)
            else:
                serialized_value = str(value)
            
            # 设置缓存
            result = await redis_client.setex(full_key, ttl, serialized_value)
            
            if result:
                logger.debug(f"缓存设置成功 {key}, TTL: {ttl}s")
            
            return bool(result)
        
        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            await self.redis_manager.ensure_connection()
            redis_client = self.redis_manager.redis
            
            full_key = self._build_key(key)
            result = await redis_client.delete(full_key)
            
            if result:
                logger.debug(f"缓存删除成功 {key}")
            
            return bool(result)
        
        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            await self.redis_manager.ensure_connection()
            redis_client = self.redis_manager.redis
            
            full_key = self._build_key(key)
            result = await redis_client.exists(full_key)
            
            return bool(result)
        
        except Exception as e:
            logger.error(f"检查缓存存在性失败 {key}: {str(e)}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """设置缓存过期时间"""
        try:
            await self.redis_manager.ensure_connection()
            redis_client = self.redis_manager.redis
            
            full_key = self._build_key(key)
            result = await redis_client.expire(full_key, ttl)
            
            return bool(result)
        
        except Exception as e:
            logger.error(f"设置缓存过期时间失败 {key}: {str(e)}")
            return False
    
    async def get_ttl(self, key: str) -> int:
        """获取缓存剩余过期时间"""
        try:
            await self.redis_manager.ensure_connection()
            redis_client = self.redis_manager.redis
            
            full_key = self._build_key(key)
            ttl = await redis_client.ttl(full_key)
            
            return ttl
        
        except Exception as e:
            logger.error(f"获取缓存TTL失败 {key}: {str(e)}")
            return -1
    
    async def clear_pattern(self, pattern: str) -> int:
        """清理匹配模式的缓存"""
        try:
            await self.redis_manager.ensure_connection()
            redis_client = self.redis_manager.redis
            
            full_pattern = self._build_key(pattern)
            keys = await redis_client.keys(full_pattern)
            
            if keys:
                deleted_count = await redis_client.delete(*keys)
                logger.debug(f"批量清理缓存: {pattern}, 清理数量: {deleted_count}")
                return deleted_count
            
            return 0
        
        except Exception as e:
            logger.error(f"批量清理缓存失败 {pattern}: {str(e)}")
            return 0
    
    async def clear_all(self) -> bool:
        """清理所有缓存"""
        try:
            await self.redis_manager.ensure_connection()
            redis_client = self.redis_manager.redis
            
            # 只清理带有前缀的键
            pattern = f"{self.key_prefix}*"
            keys = await redis_client.keys(pattern)
            
            if keys:
                deleted_count = await redis_client.delete(*keys)
                logger.info(f"清理所有缓存完成, 清理数量: {deleted_count}")
            
            return True
        
        except Exception as e:
            logger.error(f"清理所有缓存失败: {str(e)}")
            return False
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        try:
            await self.redis_manager.ensure_connection()
            redis_client = self.redis_manager.redis
            
            # 获取Redis信息
            info = await redis_client.info()
            
            # 获取我们的键数量
            pattern = f"{self.key_prefix}*"
            keys = await redis_client.keys(pattern)
            
            return {
                "redis_version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "total_keys": len(keys),
                "key_prefix": self.key_prefix,
                "default_ttl": self.default_ttl
            }
        
        except Exception as e:
            logger.error(f"获取缓存信息失败: {str(e)}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            start_time = datetime.now()
            
            # 测试连接
            await self.redis_manager.ensure_connection()
            redis_client = self.redis_manager.redis
            
            # 测试ping
            await redis_client.ping()
            
            # 测试读写
            test_key = "health_check_test"
            test_value = {"timestamp": start_time.isoformat(), "test": True}
            
            await self.set(test_key, test_value, ttl=10)
            retrieved_value = await self.get(test_key)
            await self.delete(test_key)
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "connection": "ok",
                "read_write": "ok" if retrieved_value else "failed",
                "timestamp": end_time.isoformat()
            }
        
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# 缓存装饰器
def redis_cache(
    ttl: int = 300,
    key_prefix: str = "",
    serialize_method: str = "json"
):
    """Redis缓存装饰器"""
    def decorator(func):
        @wraps(func)
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
            cached_result = await redis_cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            await redis_cache_manager.set(
                cache_key, 
                result, 
                ttl=ttl, 
                serialize_method=serialize_method
            )
            
            return result
        
        return wrapper
    return decorator


# 全局Redis缓存管理器实例
redis_cache_manager = RedisCacheManager()


# 缓存失效管理器
class CacheInvalidationManager:
    """缓存失效管理器"""
    
    def __init__(self, cache_manager: RedisCacheManager):
        self.cache_manager = cache_manager
        self.invalidation_patterns = {
            # 用户相关缓存失效模式
            "user": ["user_*", "auth_*", "permission_*"],
            # 角色相关缓存失效模式
            "role": ["role_*", "permission_*", "menu_*"],
            # 设备相关缓存失效模式
            "device": ["device_*", "device_type_*", "device_stats_*"],
            # 权限相关缓存失效模式
            "permission": ["permission_*", "user_*", "role_*"],
        }
    
    async def invalidate_by_type(self, cache_type: str) -> int:
        """根据类型失效缓存"""
        patterns = self.invalidation_patterns.get(cache_type, [])
        total_deleted = 0
        
        for pattern in patterns:
            deleted_count = await self.cache_manager.clear_pattern(pattern)
            total_deleted += deleted_count
        
        logger.info(f"失效 {cache_type} 相关缓存，共删除 {total_deleted} 个键")
        return total_deleted
    
    async def invalidate_user_cache(self, user_id: int) -> None:
        """失效特定用户的缓存"""
        patterns = [
            f"user_{user_id}_*",
            f"auth_{user_id}_*",
            f"permission_{user_id}_*"
        ]
        
        for pattern in patterns:
            await self.cache_manager.clear_pattern(pattern)
    
    async def invalidate_role_cache(self, role_id: int) -> None:
        """失效特定角色的缓存"""
        patterns = [
            f"role_{role_id}_*",
            "permission_*",  # 角色变更影响所有权限缓存
            "user_*"  # 角色变更可能影响用户权限
        ]
        
        for pattern in patterns:
            await self.cache_manager.clear_pattern(pattern)


# 全局缓存失效管理器
cache_invalidation_manager = CacheInvalidationManager(redis_cache_manager)


# 初始化和清理函数
async def init_redis_cache():
    """初始化Redis缓存"""
    try:
        await redis_cache_manager.initialize()
        logger.info("Redis缓存初始化成功")
    except Exception as e:
        logger.error(f"Redis缓存初始化失败: {str(e)}")
        raise


async def close_redis_cache():
    """关闭Redis缓存"""
    try:
        await redis_cache_manager.close()
        logger.info("Redis缓存已关闭")
    except Exception as e:
        logger.error(f"关闭Redis缓存失败: {str(e)}")


# 缓存预热函数
async def warm_up_cache():
    """缓存预热"""
    logger.info("开始缓存预热...")
    
    try:
        # 预热用户权限缓存
        from app.controllers.user import user_controller
        from app.controllers.role import role_controller
        
        # 预热前几页的用户数据
        for page in range(1, 4):
            await user_controller.get_multi_with_total_optimized(
                page=page, page_size=20, use_cache=True
            )
        
        # 预热角色数据
        for page in range(1, 3):
            await role_controller.get_multi_with_total_optimized(
                page=page, page_size=20, use_cache=True
            )
        
        logger.info("缓存预热完成")
    
    except Exception as e:
        logger.error(f"缓存预热失败: {str(e)}")


if __name__ == "__main__":
    # 测试Redis缓存
    async def test_redis_cache():
        await init_redis_cache()
        
        # 测试基本操作
        await redis_cache_manager.set("test_key", {"message": "Hello Redis!"}, ttl=60)
        value = await redis_cache_manager.get("test_key")
        print(f"缓存值: {value}")
        
        # 健康检查
        health = await redis_cache_manager.health_check()
        print(f"健康检查: {health}")
        
        # 缓存信息
        info = await redis_cache_manager.get_cache_info()
        print(f"缓存信息: {info}")
        
        await close_redis_cache()
    
    asyncio.run(test_redis_cache())