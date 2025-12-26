#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流定时调度服务
使用 APScheduler 实现工作流的定时执行
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from app.models.workflow import Workflow, WorkflowSchedule
from app.services.workflow_engine import get_workflow_engine
from app.log import logger


class WorkflowScheduler:
    """工作流调度器"""
    
    _instance: Optional['WorkflowScheduler'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._running = False
    
    def _create_scheduler(self) -> AsyncIOScheduler:
        """创建调度器实例"""
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': AsyncIOExecutor()
        }
        job_defaults = {
            'coalesce': True,  # 合并错过的执行
            'max_instances': 1,  # 同一任务最大并发数
            'misfire_grace_time': 60,  # 错过执行的容忍时间（秒）
        }
        
        return AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='Asia/Shanghai'
        )
    
    async def start(self):
        """启动调度器"""
        if self._running:
            logger.warning("调度器已在运行中")
            return
        
        self._scheduler = self._create_scheduler()
        self._scheduler.start()
        self._running = True
        
        logger.info("工作流调度器已启动")
        
        # 加载已有的调度任务
        await self._load_schedules()
    
    async def stop(self):
        """停止调度器"""
        if not self._running:
            return
        
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
        
        self._running = False
        logger.info("工作流调度器已停止")
    
    async def _load_schedules(self):
        """从数据库加载调度任务"""
        try:
            # 检查表是否存在
            from tortoise import Tortoise
            conn = Tortoise.get_connection("default")
            
            # 尝试查询，如果表不存在则跳过
            try:
                schedules = await WorkflowSchedule.filter(is_active=True).prefetch_related('workflow')
                
                for schedule in schedules:
                    await self.add_schedule(schedule)
                
                logger.info(f"已加载 {len(schedules)} 个调度任务")
            except Exception as table_error:
                # 表可能不存在或字段不匹配，跳过加载
                logger.warning(f"调度任务表可能未创建或字段不匹配，跳过加载: {table_error}")
            
        except Exception as e:
            logger.error(f"加载调度任务失败: {e}")
    
    async def add_schedule(self, schedule: WorkflowSchedule) -> bool:
        """
        添加调度任务
        
        Args:
            schedule: 调度配置
            
        Returns:
            是否添加成功
        """
        if not self._scheduler or not self._running:
            logger.warning("调度器未运行，无法添加任务")
            return False
        
        try:
            job_id = f"workflow_{schedule.workflow_id}_{schedule.id}"
            
            # 移除已存在的任务
            existing_job = self._scheduler.get_job(job_id)
            if existing_job:
                self._scheduler.remove_job(job_id)
            
            # 创建触发器
            trigger = self._create_trigger(schedule)
            if not trigger:
                logger.error(f"无法创建触发器: {schedule.schedule_type}")
                return False
            
            # 添加任务
            self._scheduler.add_job(
                self._execute_workflow,
                trigger=trigger,
                id=job_id,
                name=f"工作流调度: {schedule.workflow.name if schedule.workflow else schedule.workflow_id}",
                args=[schedule.workflow_id, schedule.id],
                replace_existing=True
            )
            
            logger.info(f"已添加调度任务: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"添加调度任务失败: {e}")
            return False
    
    async def remove_schedule(self, schedule_id: int, workflow_id: int) -> bool:
        """
        移除调度任务
        
        Args:
            schedule_id: 调度ID
            workflow_id: 工作流ID
            
        Returns:
            是否移除成功
        """
        if not self._scheduler:
            return False
        
        try:
            job_id = f"workflow_{workflow_id}_{schedule_id}"
            job = self._scheduler.get_job(job_id)
            
            if job:
                self._scheduler.remove_job(job_id)
                logger.info(f"已移除调度任务: {job_id}")
                return True
            else:
                logger.warning(f"调度任务不存在: {job_id}")
                return False
                
        except Exception as e:
            logger.error(f"移除调度任务失败: {e}")
            return False
    
    async def update_schedule(self, schedule: WorkflowSchedule) -> bool:
        """
        更新调度任务
        
        Args:
            schedule: 调度配置
            
        Returns:
            是否更新成功
        """
        # 先移除再添加
        await self.remove_schedule(schedule.id, schedule.workflow_id)
        
        if schedule.is_active:
            return await self.add_schedule(schedule)
        
        return True
    
    def _create_trigger(self, schedule: WorkflowSchedule):
        """
        创建触发器
        
        Args:
            schedule: 调度配置
            
        Returns:
            APScheduler 触发器
        """
        schedule_type = schedule.schedule_type
        config = schedule.schedule_config or {}
        
        if schedule_type == 'cron':
            # Cron 表达式调度
            cron_expr = config.get('cron_expression', '0 0 * * *')
            return self._parse_cron(cron_expr)
        
        elif schedule_type == 'interval':
            # 间隔调度
            interval_value = config.get('interval_value', 1)
            interval_unit = config.get('interval_unit', 'hours')
            
            kwargs = {interval_unit: interval_value}
            return IntervalTrigger(**kwargs)
        
        elif schedule_type == 'once':
            # 一次性调度
            run_at = config.get('run_at')
            if run_at:
                if isinstance(run_at, str):
                    run_at = datetime.fromisoformat(run_at)
                return DateTrigger(run_date=run_at)
        
        elif schedule_type == 'daily':
            # 每日调度
            hour = config.get('hour', 0)
            minute = config.get('minute', 0)
            return CronTrigger(hour=hour, minute=minute)
        
        elif schedule_type == 'weekly':
            # 每周调度
            day_of_week = config.get('day_of_week', 'mon')
            hour = config.get('hour', 0)
            minute = config.get('minute', 0)
            return CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
        
        elif schedule_type == 'monthly':
            # 每月调度
            day = config.get('day', 1)
            hour = config.get('hour', 0)
            minute = config.get('minute', 0)
            return CronTrigger(day=day, hour=hour, minute=minute)
        
        return None
    
    def _parse_cron(self, cron_expr: str) -> CronTrigger:
        """
        解析 Cron 表达式
        
        Args:
            cron_expr: Cron 表达式 (分 时 日 月 周)
            
        Returns:
            CronTrigger
        """
        parts = cron_expr.split()
        
        if len(parts) == 5:
            minute, hour, day, month, day_of_week = parts
        elif len(parts) == 6:
            # 支持秒级 (秒 分 时 日 月 周)
            second, minute, hour, day, month, day_of_week = parts
            return CronTrigger(
                second=second,
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            )
        else:
            # 默认每天0点
            return CronTrigger(hour=0, minute=0)
        
        return CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week
        )
    
    async def _execute_workflow(self, workflow_id: int, schedule_id: int):
        """
        执行工作流（调度任务回调）
        
        Args:
            workflow_id: 工作流ID
            schedule_id: 调度ID
        """
        logger.info(f"调度执行工作流: workflow_id={workflow_id}, schedule_id={schedule_id}")
        
        try:
            # 获取工作流
            workflow = await Workflow.get_or_none(id=workflow_id)
            if not workflow:
                logger.error(f"工作流不存在: {workflow_id}")
                return
            
            if not workflow.is_active:
                logger.warning(f"工作流已禁用: {workflow.code}")
                return
            
            # 获取调度配置
            schedule = await WorkflowSchedule.get_or_none(id=schedule_id)
            if not schedule or not schedule.is_active:
                logger.warning(f"调度已禁用或不存在: {schedule_id}")
                return
            
            # 执行工作流
            engine = get_workflow_engine()
            execution = await engine.execute(
                workflow=workflow,
                context=schedule.schedule_config.get('context', {}),
                trigger_type='scheduled',
                trigger_data={
                    'schedule_id': schedule_id,
                    'schedule_type': schedule.schedule_type,
                },
                triggered_by=None,
                triggered_by_name='系统调度'
            )
            
            # 更新调度统计
            schedule.last_run_at = datetime.now()
            schedule.run_count += 1
            if execution.status == 'success':
                schedule.success_count += 1
            else:
                schedule.failure_count += 1
            schedule.next_run_at = self._get_next_run_time(schedule)
            await schedule.save()
            
            logger.info(f"调度执行完成: workflow={workflow.code}, status={execution.status}")
            
        except Exception as e:
            logger.error(f"调度执行失败: {e}")
            
            # 更新失败统计
            try:
                schedule = await WorkflowSchedule.get_or_none(id=schedule_id)
                if schedule:
                    schedule.last_run_at = datetime.now()
                    schedule.run_count += 1
                    schedule.failure_count += 1
                    await schedule.save()
            except Exception:
                pass
    
    def _get_next_run_time(self, schedule: WorkflowSchedule) -> Optional[datetime]:
        """获取下次执行时间"""
        if not self._scheduler:
            return None
        
        job_id = f"workflow_{schedule.workflow_id}_{schedule.id}"
        job = self._scheduler.get_job(job_id)
        
        if job and job.next_run_time:
            return job.next_run_time
        
        return None
    
    def get_job_info(self, workflow_id: int, schedule_id: int) -> Optional[Dict[str, Any]]:
        """
        获取任务信息
        
        Args:
            workflow_id: 工作流ID
            schedule_id: 调度ID
            
        Returns:
            任务信息
        """
        if not self._scheduler:
            return None
        
        job_id = f"workflow_{workflow_id}_{schedule_id}"
        job = self._scheduler.get_job(job_id)
        
        if not job:
            return None
        
        return {
            'id': job.id,
            'name': job.name,
            'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
            'pending': job.pending,
        }
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """获取所有任务"""
        if not self._scheduler:
            return []
        
        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'pending': job.pending,
            })
        
        return jobs
    
    @property
    def is_running(self) -> bool:
        """调度器是否运行中"""
        return self._running


# 全局调度器实例
_scheduler_instance: Optional[WorkflowScheduler] = None


def get_workflow_scheduler() -> WorkflowScheduler:
    """获取工作流调度器实例"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = WorkflowScheduler()
    return _scheduler_instance


async def start_scheduler():
    """启动调度器"""
    scheduler = get_workflow_scheduler()
    await scheduler.start()


async def stop_scheduler():
    """停止调度器"""
    scheduler = get_workflow_scheduler()
    await scheduler.stop()
