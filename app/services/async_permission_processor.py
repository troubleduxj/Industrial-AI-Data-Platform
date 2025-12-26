"""
异步权限验证处理机制
"""
import asyncio
import time
from typing import List, Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import deque
from app.core.unified_logger import get_logger

logger = get_logger(__name__)


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class PermissionTask:
    """权限验证任务"""
    task_id: str
    user_id: int
    permission_code: str
    callback: Optional[Callable[[bool], Awaitable[None]]] = None
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    timeout: float = 5.0
    retries: int = 0
    max_retries: int = 3
    
    def __lt__(self, other):
        """用于优先级队列排序"""
        return self.priority.value > other.priority.value


@dataclass
class BatchPermissionTask:
    """批量权限验证任务"""
    task_id: str
    user_permission_pairs: List[tuple]
    callback: Optional[Callable[[Dict[tuple, bool]], Awaitable[None]]] = None
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    timeout: float = 10.0


class AsyncPermissionProcessor:
    """异步权限验证处理器"""
    
    def __init__(self, max_workers: int = 10, batch_size: int = 50):
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.task_queue = asyncio.PriorityQueue()
        self.batch_queue = deque()
        self.workers = []
        self.running = False
        self.stats = {
            "processed_tasks": 0,
            "failed_tasks": 0,
            "avg_processing_time": 0.0,
            "total_processing_time": 0.0,
            "batch_processed": 0
        }
        
        # 批处理配置
        self.batch_timeout = 0.1  # 100ms
        self.last_batch_time = time.time()
        
    async def start(self):
        """启动异步处理器"""
        if self.running:
            return
        
        self.running = True
        logger.info(f"启动异步权限处理器，工作线程数: {self.max_workers}")
        
        # 启动工作线程
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        
        # 启动批处理器
        batch_processor = asyncio.create_task(self._batch_processor())
        self.workers.append(batch_processor)
    
    async def stop(self):
        """停止异步处理器"""
        if not self.running:
            return
        
        self.running = False
        logger.info("停止异步权限处理器...")
        
        # 等待所有工作线程完成
        for worker in self.workers:
            worker.cancel()
        
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
        logger.info("异步权限处理器已停止")
    
    async def submit_permission_check(
        self,
        task_id: str,
        user_id: int,
        permission_code: str,
        callback: Optional[Callable[[bool], Awaitable[None]]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: float = 5.0
    ) -> str:
        """提交权限检查任务"""
        task = PermissionTask(
            task_id=task_id,
            user_id=user_id,
            permission_code=permission_code,
            callback=callback,
            priority=priority,
            timeout=timeout
        )
        
        await self.task_queue.put(task)
        logger.debug(f"提交权限检查任务: {task_id}")
        
        return task_id
    
    async def submit_batch_permission_check(
        self,
        task_id: str,
        user_permission_pairs: List[tuple],
        callback: Optional[Callable[[Dict[tuple, bool]], Awaitable[None]]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: float = 10.0
    ) -> str:
        """提交批量权限检查任务"""
        task = BatchPermissionTask(
            task_id=task_id,
            user_permission_pairs=user_permission_pairs,
            callback=callback,
            priority=priority,
            timeout=timeout
        )
        
        self.batch_queue.append(task)
        logger.debug(f"提交批量权限检查任务: {task_id}, 数量: {len(user_permission_pairs)}")
        
        return task_id
    
    async def _worker(self, worker_name: str):
        """工作线程"""
        logger.debug(f"启动工作线程: {worker_name}")
        
        while self.running:
            try:
                # 获取任务（带超时）
                try:
                    task = await asyncio.wait_for(
                        self.task_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # 处理任务
                await self._process_task(task, worker_name)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"工作线程{worker_name}处理任务失败: {e}")
        
        logger.debug(f"工作线程{worker_name}已停止")
    
    async def _process_task(self, task: PermissionTask, worker_name: str):
        """处理单个权限检查任务"""
        start_time = time.time()
        
        try:
            # 检查任务是否超时
            if time.time() - task.created_at.timestamp() > task.timeout:
                logger.warning(f"任务{task.task_id}已超时，跳过处理")
                self.stats["failed_tasks"] += 1
                return
            
            # 执行权限检查
            from app.services.permission_service import permission_service
            
            result = await permission_service.check_user_permission(
                task.user_id, task.permission_code
            )
            
            # 调用回调函数
            if task.callback:
                try:
                    await task.callback(result)
                except Exception as e:
                    logger.error(f"任务{task.task_id}回调执行失败: {e}")
            
            # 更新统计信息
            processing_time = time.time() - start_time
            self.stats["processed_tasks"] += 1
            self.stats["total_processing_time"] += processing_time
            self.stats["avg_processing_time"] = (
                self.stats["total_processing_time"] / self.stats["processed_tasks"]
            )
            
            logger.debug(f"任务{task.task_id}处理完成，耗时{processing_time:.3f}s，结果: {result}")
            
        except Exception as e:
            logger.error(f"处理任务{task.task_id}失败: {e}")
            
            # 重试机制
            if task.retries < task.max_retries:
                task.retries += 1
                await self.task_queue.put(task)
                logger.info(f"任务{task.task_id}重试第{task.retries}次")
            else:
                self.stats["failed_tasks"] += 1
                logger.error(f"任务{task.task_id}重试次数已达上限，放弃处理")
    
    async def _batch_processor(self):
        """批处理器"""
        logger.debug("启动批处理器")
        
        while self.running:
            try:
                # 等待批处理时机
                await asyncio.sleep(self.batch_timeout)
                
                if not self.batch_queue:
                    continue
                
                # 收集批处理任务
                batch_tasks = []
                while self.batch_queue and len(batch_tasks) < self.batch_size:
                    batch_tasks.append(self.batch_queue.popleft())
                
                if batch_tasks:
                    await self._process_batch_tasks(batch_tasks)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"批处理器处理失败: {e}")
        
        logger.debug("批处理器已停止")
    
    async def _process_batch_tasks(self, batch_tasks: List[BatchPermissionTask]):
        """处理批量任务"""
        start_time = time.time()
        
        try:
            # 合并所有权限检查请求
            all_pairs = []
            task_mapping = {}
            
            for task in batch_tasks:
                for pair in task.user_permission_pairs:
                    all_pairs.append(pair)
                    if pair not in task_mapping:
                        task_mapping[pair] = []
                    task_mapping[pair].append(task)
            
            # 批量执行权限检查
            from app.services.permission_performance_service import permission_performance_service
            
            batch_results = await permission_performance_service.batch_check_permissions(all_pairs)
            
            # 分发结果给各个任务
            for task in batch_tasks:
                task_results = {}
                for pair in task.user_permission_pairs:
                    task_results[pair] = batch_results.get(pair, False)
                
                # 调用回调函数
                if task.callback:
                    try:
                        await task.callback(task_results)
                    except Exception as e:
                        logger.error(f"批量任务{task.task_id}回调执行失败: {e}")
            
            # 更新统计信息
            processing_time = time.time() - start_time
            self.stats["batch_processed"] += len(batch_tasks)
            
            logger.debug(f"批量处理完成: {len(batch_tasks)}个任务, {len(all_pairs)}个权限检查, 耗时{processing_time:.3f}s")
            
        except Exception as e:
            logger.error(f"批量任务处理失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return {
            "running": self.running,
            "workers": len(self.workers),
            "queue_size": self.task_queue.qsize(),
            "batch_queue_size": len(self.batch_queue),
            "processed_tasks": self.stats["processed_tasks"],
            "failed_tasks": self.stats["failed_tasks"],
            "batch_processed": self.stats["batch_processed"],
            "avg_processing_time": f"{self.stats['avg_processing_time']:.3f}s",
            "total_processing_time": f"{self.stats['total_processing_time']:.3f}s",
            "success_rate": (
                (self.stats["processed_tasks"] / 
                 (self.stats["processed_tasks"] + self.stats["failed_tasks"]) * 100)
                if (self.stats["processed_tasks"] + self.stats["failed_tasks"]) > 0 else 0
            )
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "processed_tasks": 0,
            "failed_tasks": 0,
            "avg_processing_time": 0.0,
            "total_processing_time": 0.0,
            "batch_processed": 0
        }
        logger.info("异步权限处理器统计信息已重置")


class PermissionTaskManager:
    """权限任务管理器"""
    
    def __init__(self):
        self.processor = AsyncPermissionProcessor()
        self.pending_tasks = {}
        self.completed_tasks = {}
        self.task_counter = 0
    
    async def start(self):
        """启动任务管理器"""
        await self.processor.start()
        logger.info("权限任务管理器已启动")
    
    async def stop(self):
        """停止任务管理器"""
        await self.processor.stop()
        logger.info("权限任务管理器已停止")
    
    async def check_permission_async(
        self,
        user_id: int,
        permission_code: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: float = 5.0
    ) -> str:
        """异步权限检查"""
        self.task_counter += 1
        task_id = f"perm_check_{self.task_counter}_{int(time.time())}"
        
        # 创建任务结果存储
        task_future = asyncio.Future()
        self.pending_tasks[task_id] = task_future
        
        # 定义回调函数
        async def callback(result: bool):
            if task_id in self.pending_tasks:
                future = self.pending_tasks.pop(task_id)
                if not future.done():
                    future.set_result(result)
                self.completed_tasks[task_id] = {
                    "result": result,
                    "completed_at": datetime.utcnow()
                }
        
        # 提交任务
        await self.processor.submit_permission_check(
            task_id=task_id,
            user_id=user_id,
            permission_code=permission_code,
            callback=callback,
            priority=priority,
            timeout=timeout
        )
        
        return task_id
    
    async def check_permissions_batch_async(
        self,
        user_permission_pairs: List[tuple],
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: float = 10.0
    ) -> str:
        """异步批量权限检查"""
        self.task_counter += 1
        task_id = f"batch_perm_check_{self.task_counter}_{int(time.time())}"
        
        # 创建任务结果存储
        task_future = asyncio.Future()
        self.pending_tasks[task_id] = task_future
        
        # 定义回调函数
        async def callback(results: Dict[tuple, bool]):
            if task_id in self.pending_tasks:
                future = self.pending_tasks.pop(task_id)
                if not future.done():
                    future.set_result(results)
                self.completed_tasks[task_id] = {
                    "result": results,
                    "completed_at": datetime.utcnow()
                }
        
        # 提交任务
        await self.processor.submit_batch_permission_check(
            task_id=task_id,
            user_permission_pairs=user_permission_pairs,
            callback=callback,
            priority=priority,
            timeout=timeout
        )
        
        return task_id
    
    async def get_task_result(self, task_id: str, timeout: float = 5.0) -> Any:
        """获取任务结果"""
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id]["result"]
        
        if task_id in self.pending_tasks:
            try:
                result = await asyncio.wait_for(
                    self.pending_tasks[task_id],
                    timeout=timeout
                )
                return result
            except asyncio.TimeoutError:
                logger.warning(f"等待任务{task_id}结果超时")
                return None
        
        logger.warning(f"任务{task_id}不存在")
        return None
    
    def get_task_status(self, task_id: str) -> str:
        """获取任务状态"""
        if task_id in self.completed_tasks:
            return "completed"
        elif task_id in self.pending_tasks:
            return "pending"
        else:
            return "not_found"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取管理器统计信息"""
        processor_stats = self.processor.get_stats()
        
        return {
            **processor_stats,
            "pending_tasks": len(self.pending_tasks),
            "completed_tasks": len(self.completed_tasks),
            "total_tasks": self.task_counter
        }
    
    def cleanup_completed_tasks(self, max_age_hours: int = 1):
        """清理已完成的任务"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        to_remove = []
        for task_id, task_info in self.completed_tasks.items():
            if task_info["completed_at"] < cutoff_time:
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.completed_tasks[task_id]
        
        if to_remove:
            logger.info(f"清理了{len(to_remove)}个已完成的任务")


# 全局权限任务管理器实例
permission_task_manager = PermissionTaskManager()