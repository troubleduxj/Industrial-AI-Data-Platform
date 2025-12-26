# Redis 核心连接模块
import redis.asyncio as redis
import json
import logging
from typing import Optional, Any, Dict
from app.settings.config import settings

class RedisClient:
    """Redis 异步客户端封装类"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.logger = logging.getLogger(__name__)
    
    async def connect(self) -> bool:
        """连接到 Redis 服务器"""
        try:
            # 从配置中获取 Redis 连接信息
            redis_url = settings.REDIS_URL
            
            self.redis = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # 测试连接
            await self.redis.ping()
            self.logger.info("Redis 连接成功")
            return True
            
        except Exception as e:
            self.logger.error(f"Redis 连接失败: {e}")
            return False
    
    async def disconnect(self):
        """断开 Redis 连接"""
        if self.redis:
            await self.redis.close()
            self.logger.info("Redis 连接已断开")
    



# 全局 Redis 客户端实例
redis_client = RedisClient()

async def get_redis_client() -> RedisClient:
    """获取 Redis 客户端实例"""
    if not redis_client.redis:
        await redis_client.connect()
    return redis_client

async def close_redis_client():
    """关闭 Redis 客户端连接"""
    await redis_client.disconnect()