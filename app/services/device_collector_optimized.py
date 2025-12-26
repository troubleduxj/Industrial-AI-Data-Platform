# -*- coding: utf-8 -*-
"""
优化的设备数据采集服务

使用异步任务系统优化设备数据采集性能
"""

import asyncio
import aiohttp
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from app.core.async_tasks import task_scheduler, async_task, scheduled_task, TaskPriority
from app.models.device import DeviceInfo, DeviceRealTimeData, DeviceType
from app.core.redis_cache import redis_cache_manager
from app.log import logger


@dataclass
class DeviceCollectionResult:
    """设备采集结果"""
    device_id: int
    device_code: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    response_time: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class OptimizedDeviceCollector:
    """优化的设备数据采集器"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.collection_stats = {
            'total_collections': 0,
            'successful_collections': 0,
            'failed_collections': 0,
            'avg_response_time': 0.0,
            'last_collection_time': None
        }
        self.device_cache_ttl = 300  # 5分钟缓存
        self.batch_size = 20
        self.max_concurrent_devices = 50
        self.timeout = 30
        
    async def initialize(self):
        """初始化采集器"""
        # 创建HTTP会话
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=20,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'DeviceMonitor/1.0',
                'Accept': 'application/json',
                'Connection': 'keep-alive'
            }
        )
        
        logger.info("设备采集器已初始化")
    
    async def close(self):
        """关闭采集器"""
        if self.session:
            await self.session.close()
        
        self.executor.shutdown(wait=True)
        logger.info("设备采集器已关闭")
    
    @async_task(
        name="collect_all_devices",
        priority=TaskPriority.HIGH,
        max_retries=2,
        timeout=300,
        tags=["device_collection", "scheduled"]
    )
    async def collect_all_devices_data(self) -> Dict[str, Any]:
        """采集所有设备数据（异步任务）"""
        start_time = time.time()
        
        try:
            # 获取所有活跃设备
            devices = await self._get_active_devices()
            if not devices:
                return {"message": "没有找到活跃设备", "collected": 0}
            
            logger.info(f"开始采集 {len(devices)} 个设备的数据")
            
            # 批量采集
            results = await self._collect_devices_batch(devices)
            
            # 处理采集结果
            await self._process_collection_results(results)
            
            # 更新统计信息
            execution_time = time.time() - start_time
            await self._update_collection_stats(results, execution_time)
            
            successful_count = sum(1 for r in results if r.success)
            failed_count = len(results) - successful_count
            
            logger.info(f"设备数据采集完成: 成功 {successful_count}, 失败 {failed_count}, 耗时 {execution_time:.2f}s")
            
            return {
                "total_devices": len(devices),
                "successful": successful_count,
                "failed": failed_count,
                "execution_time": execution_time,
                "results": [r.__dict__ for r in results]
            }
            
        except Exception as e:
            logger.error(f"设备数据采集失败: {str(e)}")
            raise
    
    async def _get_active_devices(self) -> List[DeviceInfo]:
        """获取活跃设备列表"""
        # 尝试从缓存获取
        cache_key = "active_devices_list"
        cached_devices = await redis_cache_manager.get(cache_key)
        
        if cached_devices:
            logger.debug("从缓存获取活跃设备列表")
            return cached_devices
        
        # 从数据库查询
        devices = await DeviceInfo.filter(
            is_locked=False
        ).prefetch_related('realtime_data').all()
        
        # 过滤有在线地址的设备
        active_devices = [
            device for device in devices 
            if device.online_address and device.online_address.strip()
        ]
        
        # 缓存结果
        await redis_cache_manager.set(cache_key, active_devices, ttl=self.device_cache_ttl)
        
        return active_devices
    
    async def _collect_devices_batch(self, devices: List[DeviceInfo]) -> List[DeviceCollectionResult]:
        """批量采集设备数据"""
        results = []
        
        # 分批处理，避免过多并发连接
        for i in range(0, len(devices), self.batch_size):
            batch = devices[i:i + self.batch_size]
            
            # 创建采集任务
            tasks = []
            semaphore = asyncio.Semaphore(self.max_concurrent_devices)
            
            for device in batch:
                task = self._collect_single_device_with_semaphore(device, semaphore)
                tasks.append(task)
            
            # 并发执行批次任务
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理异常结果
            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    device = batch[i]
                    error_result = DeviceCollectionResult(
                        device_id=device.id,
                        device_code=device.device_code,
                        success=False,
                        error=str(result)
                    )
                    results.append(error_result)
                else:
                    results.append(result)
            
            # 批次间短暂延迟，避免服务器压力过大
            if i + self.batch_size < len(devices):
                await asyncio.sleep(0.1)
        
        return results
    
    async def _collect_single_device_with_semaphore(
        self, 
        device: DeviceInfo, 
        semaphore: asyncio.Semaphore
    ) -> DeviceCollectionResult:
        """使用信号量控制的单设备数据采集"""
        async with semaphore:
            return await self._collect_single_device(device)
    
    async def _collect_single_device(self, device: DeviceInfo) -> DeviceCollectionResult:
        """采集单个设备数据"""
        start_time = time.time()
        
        try:
            # 检查设备缓存
            cache_key = f"device_data_{device.device_code}"
            cached_data = await redis_cache_manager.get(cache_key)
            
            if cached_data:
                # 使用缓存数据，但仍然记录为成功采集
                return DeviceCollectionResult(
                    device_id=device.id,
                    device_code=device.device_code,
                    success=True,
                    data=cached_data,
                    response_time=0.0  # 缓存命中，响应时间为0
                )
            
            # 发起HTTP请求
            url = device.online_address
            if not url.startswith(('http://', 'https://')):
                url = f"http://{url}"
            
            async with self.session.get(url) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    
                    # 缓存采集到的数据
                    await redis_cache_manager.set(cache_key, data, ttl=60)  # 1分钟缓存
                    
                    return DeviceCollectionResult(
                        device_id=device.id,
                        device_code=device.device_code,
                        success=True,
                        data=data,
                        response_time=response_time
                    )
                else:
                    return DeviceCollectionResult(
                        device_id=device.id,
                        device_code=device.device_code,
                        success=False,
                        error=f"HTTP {response.status}: {response.reason}",
                        response_time=response_time
                    )
        
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            return DeviceCollectionResult(
                device_id=device.id,
                device_code=device.device_code,
                success=False,
                error="请求超时",
                response_time=response_time
            )
        
        except Exception as e:
            response_time = time.time() - start_time
            return DeviceCollectionResult(
                device_id=device.id,
                device_code=device.device_code,
                success=False,
                error=str(e),
                response_time=response_time
            )
    
    async def _process_collection_results(self, results: List[DeviceCollectionResult]):
        """处理采集结果"""
        successful_results = [r for r in results if r.success and r.data]
        
        if not successful_results:
            return
        
        # 批量保存到数据库
        await self._batch_save_device_data(successful_results)
        
        # 更新设备状态缓存
        await self._update_device_status_cache(results)
    
    async def _batch_save_device_data(self, results: List[DeviceCollectionResult]):
        """批量保存设备数据到数据库"""
        try:
            # 准备批量插入数据
            realtime_data_list = []
            
            for result in results:
                if not result.data:
                    continue
                
                # 解析设备数据
                device_data = self._parse_device_data(result.data)
                
                realtime_data = DeviceRealTimeData(
                    device_id=result.device_id,
                    metrics=device_data,
                    status=device_data.get('status', 'online'),
                    error_code=device_data.get('error_code'),
                    error_message=device_data.get('error_message'),
                    data_timestamp=result.timestamp
                )
                
                realtime_data_list.append(realtime_data)
            
            # 批量插入
            if realtime_data_list:
                await DeviceRealTimeData.bulk_create(realtime_data_list)
                logger.info(f"批量保存了 {len(realtime_data_list)} 条设备实时数据")
        
        except Exception as e:
            logger.error(f"批量保存设备数据失败: {str(e)}")
    
    def _parse_device_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析设备原始数据"""
        # 这里可以根据不同设备类型进行不同的数据解析
        # 目前使用通用解析逻辑
        
        parsed_data = {}
        
        # 映射常见字段名
        field_mappings = {
            'voltage': ['voltage', 'volt', 'v', 'u'],
            'current': ['current', 'amp', 'i', 'a'],
            'power': ['power', 'watt', 'w', 'p'],
            'temperature': ['temperature', 'temp', 't', 'celsius'],
            'pressure': ['pressure', 'press', 'pa', 'bar'],
            'vibration': ['vibration', 'vib', 'shake'],
            'status': ['status', 'state', 'condition'],
            'error_code': ['error_code', 'err_code', 'error', 'fault'],
            'error_message': ['error_message', 'err_msg', 'message', 'desc']
        }
        
        for standard_field, possible_names in field_mappings.items():
            for name in possible_names:
                if name in raw_data:
                    parsed_data[standard_field] = raw_data[name]
                    break
                # 尝试大小写不敏感匹配
                for key in raw_data.keys():
                    if key.lower() == name.lower():
                        parsed_data[standard_field] = raw_data[key]
                        break
        
        return parsed_data
    
    async def _update_device_status_cache(self, results: List[DeviceCollectionResult]):
        """更新设备状态缓存"""
        for result in results:
            cache_key = f"device_status_{result.device_code}"
            status_data = {
                'device_id': result.device_id,
                'device_code': result.device_code,
                'online': result.success,
                'last_seen': result.timestamp.isoformat(),
                'response_time': result.response_time,
                'error': result.error if not result.success else None
            }
            
            await redis_cache_manager.set(cache_key, status_data, ttl=600)  # 10分钟缓存
    
    async def _update_collection_stats(self, results: List[DeviceCollectionResult], execution_time: float):
        """更新采集统计信息"""
        successful_count = sum(1 for r in results if r.success)
        failed_count = len(results) - successful_count
        
        self.collection_stats['total_collections'] += len(results)
        self.collection_stats['successful_collections'] += successful_count
        self.collection_stats['failed_collections'] += failed_count
        self.collection_stats['last_collection_time'] = datetime.now().isoformat()
        
        # 计算平均响应时间
        response_times = [r.response_time for r in results if r.response_time > 0]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            self.collection_stats['avg_response_time'] = avg_response_time
        
        # 缓存统计信息
        await redis_cache_manager.set(
            "device_collection_stats", 
            self.collection_stats, 
            ttl=3600
        )
    
    @async_task(
        name="collect_device_by_type",
        priority=TaskPriority.NORMAL,
        max_retries=1,
        tags=["device_collection", "by_type"]
    )
    async def collect_devices_by_type(self, device_type: str) -> Dict[str, Any]:
        """按设备类型采集数据"""
        try:
            # 获取指定类型的设备
            devices = await DeviceInfo.filter(
                device_type=device_type,
                is_locked=False
            ).all()
            
            if not devices:
                return {"message": f"没有找到类型为 {device_type} 的活跃设备", "collected": 0}
            
            # 采集数据
            results = await self._collect_devices_batch(devices)
            
            # 处理结果
            await self._process_collection_results(results)
            
            successful_count = sum(1 for r in results if r.success)
            
            return {
                "device_type": device_type,
                "total_devices": len(devices),
                "successful": successful_count,
                "failed": len(results) - successful_count,
                "results": [r.__dict__ for r in results]
            }
        
        except Exception as e:
            logger.error(f"按类型采集设备数据失败 ({device_type}): {str(e)}")
            raise
    
    @async_task(
        name="health_check_devices",
        priority=TaskPriority.LOW,
        max_retries=1,
        tags=["device_health", "monitoring"]
    )
    async def health_check_devices(self) -> Dict[str, Any]:
        """设备健康检查"""
        try:
            devices = await self._get_active_devices()
            health_results = []
            
            for device in devices:
                # 检查设备最后数据时间
                last_data = await DeviceRealTimeData.filter(
                    device_id=device.id
                ).order_by('-data_timestamp').first()
                
                if last_data:
                    time_diff = datetime.now() - last_data.data_timestamp
                    is_healthy = time_diff.total_seconds() < 300  # 5分钟内有数据认为健康
                else:
                    is_healthy = False
                    time_diff = None
                
                health_results.append({
                    'device_id': device.id,
                    'device_code': device.device_code,
                    'device_name': device.device_name,
                    'is_healthy': is_healthy,
                    'last_data_time': last_data.data_timestamp.isoformat() if last_data else None,
                    'offline_duration': time_diff.total_seconds() if time_diff else None
                })
            
            healthy_count = sum(1 for r in health_results if r['is_healthy'])
            unhealthy_count = len(health_results) - healthy_count
            
            # 缓存健康检查结果
            await redis_cache_manager.set(
                "device_health_check",
                {
                    'timestamp': datetime.now().isoformat(),
                    'total_devices': len(health_results),
                    'healthy_devices': healthy_count,
                    'unhealthy_devices': unhealthy_count,
                    'results': health_results
                },
                ttl=600
            )
            
            return {
                'total_devices': len(health_results),
                'healthy_devices': healthy_count,
                'unhealthy_devices': unhealthy_count,
                'health_rate': (healthy_count / len(health_results) * 100) if health_results else 0,
                'results': health_results
            }
        
        except Exception as e:
            logger.error(f"设备健康检查失败: {str(e)}")
            raise
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """获取采集统计信息"""
        # 尝试从缓存获取
        cached_stats = await redis_cache_manager.get("device_collection_stats")
        if cached_stats:
            return cached_stats
        
        return self.collection_stats


# 全局设备采集器实例
device_collector = OptimizedDeviceCollector()


# 定时任务
@scheduled_task(
    schedule=timedelta(minutes=5),  # 每5分钟执行一次
    name="scheduled_device_collection"
)
async def scheduled_device_collection():
    """定时设备数据采集"""
    return await device_collector.collect_all_devices_data()


@scheduled_task(
    schedule=timedelta(minutes=15),  # 每15分钟执行一次
    name="scheduled_device_health_check"
)
async def scheduled_device_health_check():
    """定时设备健康检查"""
    return await device_collector.health_check_devices()


# 初始化和清理函数
async def init_device_collector():
    """初始化设备采集器"""
    await device_collector.initialize()
    logger.info("优化的设备采集器已初始化")


async def shutdown_device_collector():
    """关闭设备采集器"""
    await device_collector.close()
    logger.info("优化的设备采集器已关闭")


if __name__ == "__main__":
    # 测试代码
    async def test_collection():
        await init_device_collector()
        
        try:
            # 测试采集所有设备
            result = await device_collector.collect_all_devices_data()
            print(f"采集结果: {result}")
            
            # 测试健康检查
            health_result = await device_collector.health_check_devices()
            print(f"健康检查结果: {health_result}")
            
        finally:
            await shutdown_device_collector()
    
    asyncio.run(test_collection())