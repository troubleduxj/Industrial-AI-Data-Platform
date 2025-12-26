# -*- coding: utf-8 -*-
"""
应用启动初始化模块

处理应用启动时的初始化工作，包括Redis缓存、数据库连接等
"""

import asyncio
from typing import Optional

from app.log import logger
from app.core.redis_cache import init_redis_cache, close_redis_cache, warm_up_cache
from app.core.permission_cache import permission_cache_manager
from app.core.async_tasks import init_task_scheduler, shutdown_task_scheduler
from app.core.scheduler import scheduler_manager
from app.services.device_collector_optimized import init_device_collector, shutdown_device_collector
from app.services.metadata_service import MetadataService
from app.services.alarm_detection import alarm_engine
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger


class ApplicationStartup:
    """应用启动管理器"""
    
    def __init__(self):
        self.redis_initialized = False
        self.cache_warmed_up = False
    
    async def initialize(self) -> None:
        """初始化应用"""
        logger.info("开始初始化应用...")
        
        try:
            # 初始化Redis缓存
            await self._initialize_redis()
            
            # 初始化异步任务调度器
            await self._initialize_task_scheduler()
            
            # 初始化设备采集器
            await self._initialize_device_collector()
            
            # 预热缓存（可选，在后台执行）
            asyncio.create_task(self._warm_up_caches())
            
            logger.info("应用初始化完成")
            
        except Exception as e:
            logger.error(f"应用初始化失败: {str(e)}")
            raise
    
    async def shutdown(self) -> None:
        """关闭应用"""
        logger.info("开始关闭应用...")
        
        try:
            # 关闭设备采集器
            if hasattr(self, 'device_collector_initialized') and self.device_collector_initialized:
                await shutdown_device_collector()
                self.device_collector_initialized = False
            
            # 关闭异步任务调度器
            if hasattr(self, 'task_scheduler_initialized') and self.task_scheduler_initialized:
                await shutdown_task_scheduler()
                scheduler_manager.shutdown()
                self.task_scheduler_initialized = False
            
            # 关闭Redis连接
            if self.redis_initialized:
                await close_redis_cache()
                self.redis_initialized = False
            
            logger.info("应用关闭完成")
            
        except Exception as e:
            logger.error(f"应用关闭失败: {str(e)}")
    
    async def _initialize_redis(self) -> None:
        """初始化Redis缓存"""
        try:
            await init_redis_cache()
            self.redis_initialized = True
            logger.info("Redis缓存初始化成功")
        except Exception as e:
            logger.warning(f"Redis缓存初始化失败，将使用内存缓存: {str(e)}")
            # Redis初始化失败不应该阻止应用启动
            # 可以降级到内存缓存
    
    async def _initialize_task_scheduler(self) -> None:
        """初始化异步任务调度器"""
        try:
            # 初始化原有任务调度器 (Task Queue)
            await init_task_scheduler()
            
            # 初始化 APScheduler
            scheduler_manager.start()
            
            # 添加每日表结构差异检查任务 (每天凌晨 02:00)
            scheduler_manager.add_job(
                MetadataService.check_schema_diff_daily,
                CronTrigger(hour=2, minute=0),
                id='daily_schema_check',
                name='每日表结构差异检查',
                replace_existing=True
            )
            
            # 添加报警超时升级检查任务 (每1分钟)
            scheduler_manager.add_job(
                alarm_engine.check_timeout_alarms,
                IntervalTrigger(minutes=1),
                id='alarm_timeout_check',
                name='报警超时升级检查',
                replace_existing=True
            )
            
            self.task_scheduler_initialized = True
            logger.info("异步任务调度器初始化成功")
        except Exception as e:
            logger.error(f"异步任务调度器初始化失败: {str(e)}")
            # 任务调度器初始化失败不应该阻止应用启动
            self.task_scheduler_initialized = False
    
    async def _initialize_device_collector(self) -> None:
        """初始化设备采集器"""
        try:
            await init_device_collector()
            self.device_collector_initialized = True
            logger.info("设备采集器初始化成功")
        except Exception as e:
            logger.error(f"设备采集器初始化失败: {str(e)}")
            # 设备采集器初始化失败不应该阻止应用启动
            self.device_collector_initialized = False
    
    async def _warm_up_caches(self) -> None:
        """预热缓存"""
        if not self.redis_initialized:
            return
        
        try:
            logger.info("开始预热缓存...")
            
            # 预热基础缓存
            await warm_up_cache()
            
            # 预热权限缓存
            await permission_cache_manager.warm_up_permissions()
            
            self.cache_warmed_up = True
            logger.info("缓存预热完成")
            
        except Exception as e:
            logger.error(f"缓存预热失败: {str(e)}")
    
    async def health_check(self) -> dict:
        """健康检查"""
        health_status = {
            "status": "healthy",
            "redis_initialized": self.redis_initialized,
            "cache_warmed_up": self.cache_warmed_up,
            "checks": {}
        }
        
        # Redis健康检查
        if self.redis_initialized:
            try:
                from app.core.redis_cache import redis_cache_manager
                redis_health = await redis_cache_manager.health_check()
                health_status["checks"]["redis"] = redis_health
                
                if redis_health["status"] != "healthy":
                    health_status["status"] = "degraded"
                    
            except Exception as e:
                health_status["checks"]["redis"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["status"] = "degraded"
        else:
            health_status["checks"]["redis"] = {
                "status": "not_initialized",
                "message": "Redis未初始化，使用内存缓存"
            }
        
        return health_status


# 全局应用启动管理器实例
app_startup = ApplicationStartup()


# FastAPI事件处理器
async def startup_event():
    """FastAPI启动事件处理器"""
    await app_startup.initialize()


async def shutdown_event():
    """FastAPI关闭事件处理器"""
    await app_startup.shutdown()


# 健康检查端点处理器
async def health_check_handler():
    """健康检查处理器"""
    return await app_startup.health_check()


# 缓存管理端点处理器
class CacheManagementHandler:
    """缓存管理处理器"""
    
    @staticmethod
    async def get_cache_info():
        """获取缓存信息"""
        try:
            from app.core.redis_cache import redis_cache_manager
            from app.core.permission_cache import permission_cache_manager
            
            cache_info = await redis_cache_manager.get_cache_info()
            permission_stats = await permission_cache_manager.get_cache_statistics()
            
            return {
                "redis_cache": cache_info,
                "permission_cache": permission_stats,
                "status": "ok"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    @staticmethod
    async def clear_cache(cache_type: Optional[str] = None):
        """清理缓存"""
        try:
            from app.core.redis_cache import cache_invalidation_manager
            
            if cache_type:
                deleted_count = await cache_invalidation_manager.invalidate_by_type(cache_type)
                return {
                    "message": f"已清理 {cache_type} 类型缓存",
                    "deleted_count": deleted_count,
                    "status": "ok"
                }
            else:
                from app.core.redis_cache import redis_cache_manager
                success = await redis_cache_manager.clear_all()
                return {
                    "message": "已清理所有缓存",
                    "success": success,
                    "status": "ok"
                }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    @staticmethod
    async def warm_up_cache():
        """预热缓存"""
        try:
            await app_startup._warm_up_caches()
            return {
                "message": "缓存预热完成",
                "status": "ok"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }


# 全局缓存管理处理器实例
cache_management_handler = CacheManagementHandler()


if __name__ == "__main__":
    # 测试启动流程
    async def test_startup():
        await startup_event()
        
        # 健康检查
        health = await health_check_handler()
        print(f"健康检查结果: {health}")
        
        # 缓存信息
        cache_info = await cache_management_handler.get_cache_info()
        print(f"缓存信息: {cache_info}")
        
        await shutdown_event()
    
    asyncio.run(test_startup())