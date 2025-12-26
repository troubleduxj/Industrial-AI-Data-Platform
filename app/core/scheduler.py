# -*- coding: utf-8 -*-
"""
任务调度管理器 (基于 APScheduler)
用于处理定时任务，如每日检查、定时报表等
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from app.log import logger
from typing import Callable, Any

class SchedulerManager:
    """调度器管理器单例"""
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SchedulerManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.scheduler = AsyncIOScheduler(
            jobstores={
                'default': MemoryJobStore()
            },
            job_defaults={
                'coalesce': False,
                'max_instances': 3
            },
            timezone='Asia/Shanghai'
        )
        self._is_running = False
        self._initialized = True

    def start(self):
        """启动调度器"""
        if not self._is_running:
            self.scheduler.start()
            self._is_running = True
            logger.info("✅ 任务调度器 (APScheduler) 已启动")

    def shutdown(self):
        """停止调度器"""
        if self._is_running:
            self.scheduler.shutdown()
            self._is_running = False
            logger.info("🛑 任务调度器 (APScheduler) 已停止")

    def add_job(self, func: Callable, trigger: Any, id: str = None, name: str = None, replace_existing: bool = True, **kwargs):
        """添加任务"""
        try:
            job = self.scheduler.add_job(
                func, 
                trigger, 
                id=id, 
                name=name, 
                replace_existing=replace_existing,
                **kwargs
            )
            logger.info(f"➕ 添加定时任务: {name or func.__name__} (ID: {job.id})")
            return job
        except Exception as e:
            logger.error(f"❌ 添加定时任务失败: {e}")
            raise

    def get_job(self, job_id: str):
        """获取任务"""
        return self.scheduler.get_job(job_id)

    def remove_job(self, job_id: str):
        """移除任务"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"➖ 移除定时任务: {job_id}")
        except Exception as e:
            logger.error(f"❌ 移除定时任务失败: {e}")

# 全局实例
scheduler_manager = SchedulerManager()
