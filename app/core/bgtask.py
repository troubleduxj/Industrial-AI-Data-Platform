from typing import List, Callable, Any
import asyncio
import logging

logger = logging.getLogger(__name__)


class BgTasks:
    """后台任务管理器"""
    
    _tasks: List[Callable] = []
    _initialized = False
    
    @classmethod
    async def init_bg_tasks_obj(cls):
        """初始化后台任务对象"""
        if not cls._initialized:
            cls._tasks = []
            cls._initialized = True
            logger.debug("Background tasks initialized")
    
    @classmethod
    async def add_task(cls, task: Callable, *args, **kwargs):
        """添加后台任务"""
        if not cls._initialized:
            await cls.init_bg_tasks_obj()
        
        async def wrapped_task():
            try:
                if asyncio.iscoroutinefunction(task):
                    await task(*args, **kwargs)
                else:
                    task(*args, **kwargs)
            except Exception as e:
                logger.error(f"Background task failed: {e}", exc_info=True)
        
        cls._tasks.append(wrapped_task)
    
    @classmethod
    async def execute_tasks(cls):
        """执行所有后台任务"""
        if not cls._tasks:
            return
        
        tasks_to_execute = cls._tasks.copy()
        cls._tasks.clear()
        
        for task in tasks_to_execute:
            try:
                await task()
            except Exception as e:
                logger.error(f"Error executing background task: {e}", exc_info=True)
    
    @classmethod
    def clear_tasks(cls):
        """清空所有任务"""
        cls._tasks.clear()