# -*- coding: utf-8 -*-
"""
异步任务处理系统

提供后台任务队列、任务调度和状态监控功能
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict
from functools import wraps
import traceback

from app.log import logger


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    COMPLETED = "completed"  # 执行完成
    FAILED = "failed"        # 执行失败
    CANCELLED = "cancelled"  # 已取消
    RETRY = "retry"          # 重试中


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class TaskResult:
    """任务执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    memory_usage: Optional[int] = None


@dataclass
class Task:
    """任务定义"""
    id: str
    name: str
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[TaskResult] = None
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    depends_on: List[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.depends_on is None:
            self.depends_on = []
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理不能序列化的字段
        data['func'] = self.func.__name__ if hasattr(self.func, '__name__') else str(self.func)
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data


class TaskQueue:
    """任务队列"""
    
    def __init__(self, maxsize: int = 0):
        self.maxsize = maxsize
        self._queue = asyncio.PriorityQueue(maxsize=maxsize)
        self._tasks = {}  # 任务ID到任务的映射
        self._lock = asyncio.Lock()
    
    async def put(self, task: Task) -> None:
        """添加任务到队列"""
        async with self._lock:
            if self.maxsize > 0 and len(self._tasks) >= self.maxsize:
                raise asyncio.QueueFull("Task queue is full")
            
            # 使用负优先级值，因为PriorityQueue是最小堆
            priority = -task.priority.value
            await self._queue.put((priority, task.created_at, task))
            self._tasks[task.id] = task
            
            logger.debug(f"任务已添加到队列: {task.name} (ID: {task.id})")
    
    async def get(self) -> Task:
        """从队列获取任务"""
        _, _, task = await self._queue.get()
        return task
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务"""
        return self._tasks.get(task_id)
    
    async def remove_task(self, task_id: str) -> bool:
        """移除任务"""
        async with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                return True
            return False
    
    async def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        return list(self._tasks.values())
    
    async def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """根据状态获取任务"""
        return [task for task in self._tasks.values() if task.status == status]
    
    async def get_tasks_by_tag(self, tag: str) -> List[Task]:
        """根据标签获取任务"""
        return [task for task in self._tasks.values() if tag in task.tags]
    
    def qsize(self) -> int:
        """获取队列大小"""
        return self._queue.qsize()
    
    def empty(self) -> bool:
        """检查队列是否为空"""
        return self._queue.empty()


class TaskWorker:
    """任务工作器"""
    
    def __init__(self, worker_id: str, queue: TaskQueue):
        self.worker_id = worker_id
        self.queue = queue
        self.current_task: Optional[Task] = None
        self.is_running = False
        self.processed_count = 0
        self.error_count = 0
        self.start_time: Optional[datetime] = None
    
    async def start(self) -> None:
        """启动工作器"""
        self.is_running = True
        self.start_time = datetime.now()
        logger.info(f"任务工作器 {self.worker_id} 已启动")
        
        while self.is_running:
            try:
                # 获取任务
                task = await self.queue.get()
                self.current_task = task
                
                # 检查依赖
                if not await self._check_dependencies(task):
                    # 重新放回队列
                    await self.queue.put(task)
                    await asyncio.sleep(1)
                    continue
                
                # 执行任务
                await self._execute_task(task)
                
            except asyncio.CancelledError:
                logger.info(f"任务工作器 {self.worker_id} 被取消")
                break
            except Exception as e:
                logger.error(f"任务工作器 {self.worker_id} 发生错误: {str(e)}")
                self.error_count += 1
                await asyncio.sleep(1)
            finally:
                self.current_task = None
    
    async def stop(self) -> None:
        """停止工作器"""
        self.is_running = False
        logger.info(f"任务工作器 {self.worker_id} 已停止")
    
    async def _check_dependencies(self, task: Task) -> bool:
        """检查任务依赖"""
        if not task.depends_on:
            return True
        
        for dep_id in task.depends_on:
            dep_task = await self.queue.get_task(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    async def _execute_task(self, task: Task) -> None:
        """执行任务"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        logger.info(f"开始执行任务: {task.name} (ID: {task.id})")
        
        try:
            # 执行任务函数
            start_time = asyncio.get_event_loop().time()
            
            if asyncio.iscoroutinefunction(task.func):
                if task.timeout:
                    result_data = await asyncio.wait_for(
                        task.func(*task.args, **task.kwargs),
                        timeout=task.timeout
                    )
                else:
                    result_data = await task.func(*task.args, **task.kwargs)
            else:
                # 同步函数在线程池中执行
                if task.timeout:
                    result_data = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, task.func, *task.args
                        ),
                        timeout=task.timeout
                    )
                else:
                    result_data = await asyncio.get_event_loop().run_in_executor(
                        None, task.func, *task.args
                    )
            
            end_time = asyncio.get_event_loop().time()
            execution_time = end_time - start_time
            
            # 记录成功结果
            task.result = TaskResult(
                success=True,
                data=result_data,
                execution_time=execution_time
            )
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
            self.processed_count += 1
            logger.info(f"任务执行成功: {task.name} (耗时: {execution_time:.2f}s)")
            
        except asyncio.TimeoutError:
            await self._handle_task_error(task, "任务执行超时")
        except Exception as e:
            await self._handle_task_error(task, str(e))
    
    async def _handle_task_error(self, task: Task, error_msg: str) -> None:
        """处理任务错误"""
        task.retry_count += 1
        
        if task.retry_count <= task.max_retries:
            # 重试任务
            task.status = TaskStatus.RETRY
            logger.warning(f"任务执行失败，准备重试 ({task.retry_count}/{task.max_retries}): {task.name}, 错误: {error_msg}")
            
            # 延迟后重新加入队列
            await asyncio.sleep(task.retry_delay * task.retry_count)
            await self.queue.put(task)
        else:
            # 任务失败
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.result = TaskResult(
                success=False,
                error=error_msg
            )
            
            self.error_count += 1
            logger.error(f"任务执行失败: {task.name}, 错误: {error_msg}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取工作器统计信息"""
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        return {
            'worker_id': self.worker_id,
            'is_running': self.is_running,
            'current_task': self.current_task.name if self.current_task else None,
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'uptime_seconds': uptime,
            'success_rate': (self.processed_count / max(self.processed_count + self.error_count, 1)) * 100
        }


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, max_workers: int = 4, queue_size: int = 1000):
        self.max_workers = max_workers
        self.queue = TaskQueue(maxsize=queue_size)
        self.workers: List[TaskWorker] = []
        self.worker_tasks: List[asyncio.Task] = []
        self.is_running = False
        self.scheduled_tasks = {}  # 定时任务
        self.scheduler_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """启动调度器"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # 创建工作器
        for i in range(self.max_workers):
            worker = TaskWorker(f"worker-{i}", self.queue)
            self.workers.append(worker)
            
            # 启动工作器任务
            worker_task = asyncio.create_task(worker.start())
            self.worker_tasks.append(worker_task)
        
        # 启动定时任务调度器
        self.scheduler_task = asyncio.create_task(self._run_scheduler())
        
        logger.info(f"任务调度器已启动，工作器数量: {self.max_workers}")
    
    async def stop(self) -> None:
        """停止调度器"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 停止工作器
        for worker in self.workers:
            await worker.stop()
        
        # 取消工作器任务
        for worker_task in self.worker_tasks:
            worker_task.cancel()
        
        # 等待所有任务完成
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        # 停止定时任务调度器
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("任务调度器已停止")
    
    async def submit_task(
        self,
        func: Callable,
        *args,
        name: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None,
        depends_on: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """提交任务"""
        task_id = str(uuid.uuid4())
        task_name = name or func.__name__ if hasattr(func, '__name__') else f"task-{task_id[:8]}"
        
        task = Task(
            id=task_id,
            name=task_name,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            depends_on=depends_on or [],
            tags=tags or []
        )
        
        await self.queue.put(task)
        logger.info(f"任务已提交: {task_name} (ID: {task_id})")
        
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = await self.queue.get_task(task_id)
        if task:
            return task.to_dict()
        return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = await self.queue.get_task(task_id)
        if task and task.status in [TaskStatus.PENDING, TaskStatus.RETRY]:
            task.status = TaskStatus.CANCELLED
            await self.queue.remove_task(task_id)
            logger.info(f"任务已取消: {task.name} (ID: {task_id})")
            return True
        return False
    
    async def schedule_task(
        self,
        func: Callable,
        schedule: Union[str, timedelta],
        *args,
        name: Optional[str] = None,
        **kwargs
    ) -> str:
        """调度定时任务"""
        task_id = str(uuid.uuid4())
        task_name = name or func.__name__ if hasattr(func, '__name__') else f"scheduled-{task_id[:8]}"
        
        self.scheduled_tasks[task_id] = {
            'id': task_id,
            'name': task_name,
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'schedule': schedule,
            'next_run': self._calculate_next_run(schedule),
            'last_run': None,
            'run_count': 0
        }
        
        logger.info(f"定时任务已调度: {task_name} (ID: {task_id})")
        return task_id
    
    def _calculate_next_run(self, schedule: Union[str, timedelta]) -> datetime:
        """计算下次运行时间"""
        now = datetime.now()
        
        if isinstance(schedule, timedelta):
            return now + schedule
        elif isinstance(schedule, str):
            # 简单的cron表达式解析（这里只支持间隔格式）
            if schedule.startswith('every '):
                interval_str = schedule[6:]
                if interval_str.endswith('s'):
                    seconds = int(interval_str[:-1])
                    return now + timedelta(seconds=seconds)
                elif interval_str.endswith('m'):
                    minutes = int(interval_str[:-1])
                    return now + timedelta(minutes=minutes)
                elif interval_str.endswith('h'):
                    hours = int(interval_str[:-1])
                    return now + timedelta(hours=hours)
        
        # 默认1小时后
        return now + timedelta(hours=1)
    
    async def _run_scheduler(self) -> None:
        """运行定时任务调度器"""
        while self.is_running:
            try:
                now = datetime.now()
                
                for task_info in list(self.scheduled_tasks.values()):
                    if now >= task_info['next_run']:
                        # 提交任务
                        await self.submit_task(
                            task_info['func'],
                            *task_info['args'],
                            name=f"{task_info['name']}-{task_info['run_count']}",
                            **task_info['kwargs']
                        )
                        
                        # 更新调度信息
                        task_info['last_run'] = now
                        task_info['run_count'] += 1
                        task_info['next_run'] = self._calculate_next_run(task_info['schedule'])
                
                await asyncio.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                logger.error(f"定时任务调度器错误: {str(e)}")
                await asyncio.sleep(5)
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取调度器统计信息"""
        all_tasks = await self.queue.get_all_tasks()
        
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = len([t for t in all_tasks if t.status == status])
        
        worker_stats = [worker.get_stats() for worker in self.workers]
        
        return {
            'is_running': self.is_running,
            'queue_size': self.queue.qsize(),
            'total_tasks': len(all_tasks),
            'status_counts': status_counts,
            'scheduled_tasks_count': len(self.scheduled_tasks),
            'workers': worker_stats
        }


# 全局任务调度器实例
task_scheduler = TaskScheduler()


# 装饰器
def async_task(
    name: Optional[str] = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    timeout: Optional[float] = None,
    tags: Optional[List[str]] = None
):
    """异步任务装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await task_scheduler.submit_task(
                func,
                *args,
                name=name,
                priority=priority,
                max_retries=max_retries,
                retry_delay=retry_delay,
                timeout=timeout,
                tags=tags,
                **kwargs
            )
        
        # 添加直接执行方法
        wrapper.execute = func
        wrapper.submit = wrapper
        
        return wrapper
    
    return decorator


def scheduled_task(
    schedule: Union[str, timedelta],
    name: Optional[str] = None
):
    """定时任务装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await task_scheduler.schedule_task(
                func,
                schedule,
                *args,
                name=name,
                **kwargs
            )
        
        # 添加直接执行方法
        wrapper.execute = func
        wrapper.schedule = wrapper
        
        return wrapper
    
    return decorator


# 初始化和清理函数
async def init_task_scheduler():
    """初始化任务调度器"""
    await task_scheduler.start()
    logger.info("异步任务调度器已初始化")


async def shutdown_task_scheduler():
    """关闭任务调度器"""
    await task_scheduler.stop()
    logger.info("异步任务调度器已关闭")


if __name__ == "__main__":
    # 测试代码
    async def test_task(name: str, delay: float = 1.0):
        """测试任务"""
        await asyncio.sleep(delay)
        return f"Hello, {name}!"
    
    async def main():
        # 启动调度器
        await init_task_scheduler()
        
        try:
            # 提交任务
            task_id = await task_scheduler.submit_task(
                test_task,
                "World",
                delay=2.0,
                name="test-task",
                priority=TaskPriority.HIGH
            )
            
            print(f"任务已提交: {task_id}")
            
            # 等待任务完成
            while True:
                status = await task_scheduler.get_task_status(task_id)
                if status:
                    print(f"任务状态: {status['status']}")
                    if status['status'] in ['completed', 'failed']:
                        break
                await asyncio.sleep(1)
            
            # 获取统计信息
            stats = await task_scheduler.get_stats()
            print(f"调度器统计: {stats}")
            
        finally:
            # 关闭调度器
            await shutdown_task_scheduler()
    
    asyncio.run(main())