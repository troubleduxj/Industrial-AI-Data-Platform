# -*- coding: utf-8 -*-
"""
缓存管理模块
提供Redis缓存功能，用于权限验证和其他数据缓存
"""
import json
import logging
from typing import Any, Callable, Optional, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from app.settings import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.default_ttl = 3600  # 1小时默认过期时间
        self.permission_ttl = 1800  # 权限缓存30分钟
        
    async def init_redis(self):
        """初始化Redis连接"""
        try:
            # 从环境变量获取Redis配置
            redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
            redis_port = getattr(settings, 'REDIS_PORT', 6379)
            redis_db = getattr(settings, 'REDIS_DB', 0)
            redis_password = getattr(settings, 'REDIS_PASSWORD', None)
            
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # 测试连接
            await self.redis_client.ping()
            logger.info("Redis连接初始化成功")
            
        except Exception as e:
            logger.warning(f"Redis连接失败，将使用内存缓存: {e}")
            self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            if self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"获取缓存失败 key={key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            if self.redis_client:
                ttl = ttl or self.default_ttl
                serialized_value = json.dumps(value, default=str, ensure_ascii=False)
                await self.redis_client.setex(key, ttl, serialized_value)
                return True
            return False
        except Exception as e:
            logger.error(f"设置缓存失败 key={key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            if self.redis_client:
                await self.redis_client.delete(key)
                return True
            return False
        except Exception as e:
            logger.error(f"删除缓存失败 key={key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """批量删除匹配模式的缓存"""
        try:
            if self.redis_client:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    deleted_count = await self.redis_client.delete(*keys)
                    logger.info(f"批量删除缓存: {deleted_count} 个key")
                    return deleted_count
            return 0
        except Exception as e:
            logger.error(f"批量删除缓存失败 pattern={pattern}: {e}")
            return 0
    
    async def get_or_set(self, key: str, func: Callable, ttl: Optional[int] = None) -> Any:
        """获取缓存或设置缓存"""
        # 先尝试从缓存获取
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # 缓存不存在，执行函数获取值
        try:
            if callable(func):
                value = await func() if hasattr(func, '__call__') and hasattr(func(), '__await__') else func()
            else:
                value = func
            
            # 设置缓存
            await self.set(key, value, ttl)
            return value
        except Exception as e:
            logger.error(f"获取或设置缓存失败 key={key}: {e}")
            raise
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            if self.redis_client:
                return await self.redis_client.exists(key) > 0
            return False
        except Exception as e:
            logger.error(f"检查缓存存在性失败 key={key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """设置缓存过期时间"""
        try:
            if self.redis_client:
                return await self.redis_client.expire(key, ttl)
            return False
        except Exception as e:
            logger.error(f"设置缓存过期时间失败 key={key}: {e}")
            return False
    
    async def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()


class PermissionCache:
    """权限缓存管理器"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.permission_prefix = "perm"
        self.user_roles_prefix = "user_roles"
        self.role_permissions_prefix = "role_perms"
        
    def _get_user_permission_key(self, user_id: int, resource: str, action: str) -> str:
        """获取用户权限缓存key"""
        return f"{self.permission_prefix}:user:{user_id}:{resource}:{action}"
    
    def _get_user_roles_key(self, user_id: int) -> str:
        """获取用户角色缓存key"""
        return f"{self.user_roles_prefix}:user:{user_id}"
    
    def _get_role_permissions_key(self, role_id: int) -> str:
        """获取角色权限缓存key"""
        return f"{self.role_permissions_prefix}:role:{role_id}"
    
    def _get_user_api_permissions_key(self, user_id: int) -> str:
        """获取用户API权限缓存key"""
        return f"{self.permission_prefix}:api:user:{user_id}"
    
    async def get_user_permission(self, user_id: int, resource: str, action: str) -> Optional[bool]:
        """获取用户权限缓存"""
        key = self._get_user_permission_key(user_id, resource, action)
        return await self.cache.get(key)
    
    async def set_user_permission(self, user_id: int, resource: str, action: str, has_permission: bool) -> bool:
        """设置用户权限缓存"""
        key = self._get_user_permission_key(user_id, resource, action)
        return await self.cache.set(key, has_permission, self.cache.permission_ttl)
    
    async def get_user_roles(self, user_id: int) -> Optional[list]:
        """获取用户角色缓存"""
        key = self._get_user_roles_key(user_id)
        return await self.cache.get(key)
    
    async def set_user_roles(self, user_id: int, roles: list) -> bool:
        """设置用户角色缓存"""
        key = self._get_user_roles_key(user_id)
        return await self.cache.set(key, roles, self.cache.permission_ttl)
    
    async def get_user_api_permissions(self, user_id: int) -> Optional[list]:
        """获取用户API权限缓存"""
        key = self._get_user_api_permissions_key(user_id)
        return await self.cache.get(key)
    
    async def set_user_api_permissions(self, user_id: int, permissions: list) -> bool:
        """设置用户API权限缓存"""
        key = self._get_user_api_permissions_key(user_id)
        return await self.cache.set(key, permissions, self.cache.permission_ttl)
    
    async def invalidate_user_permissions(self, user_id: int) -> int:
        """清除用户所有权限缓存"""
        patterns = [
            f"{self.permission_prefix}:user:{user_id}:*",
            f"{self.permission_prefix}:api:user:{user_id}",
            f"{self.user_roles_prefix}:user:{user_id}"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = await self.cache.delete_pattern(pattern)
            total_deleted += deleted
        
        logger.info(f"清除用户 {user_id} 的权限缓存，共删除 {total_deleted} 个缓存项")
        return total_deleted
    
    async def invalidate_role_permissions(self, role_id: int) -> int:
        """清除角色相关的权限缓存"""
        # 这里需要找到所有拥有该角色的用户，然后清除他们的权限缓存
        # 为简化实现，我们清除所有权限缓存
        patterns = [
            f"{self.permission_prefix}:*",
            f"{self.user_roles_prefix}:*",
            f"{self.role_permissions_prefix}:role:{role_id}"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = await self.cache.delete_pattern(pattern)
            total_deleted += deleted
        
        logger.info(f"清除角色 {role_id} 相关的权限缓存，共删除 {total_deleted} 个缓存项")
        return total_deleted
    
    async def clear_all_permissions(self) -> int:
        """清除所有权限缓存"""
        patterns = [
            f"{self.permission_prefix}:*",
            f"{self.user_roles_prefix}:*",
            f"{self.role_permissions_prefix}:*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = await self.cache.delete_pattern(pattern)
            total_deleted += deleted
        
        logger.info(f"清除所有权限缓存，共删除 {total_deleted} 个缓存项")
        return total_deleted


# 全局缓存管理器实例
cache_manager = CacheManager()
permission_cache = PermissionCache(cache_manager)