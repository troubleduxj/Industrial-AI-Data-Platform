#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报警集成服务
将报警检测集成到设备数据流中
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.services.alarm_detection import check_and_trigger_alarms, alarm_engine
from app.services.alarm_websocket import broadcast_new_alarms
from app.log import logger


async def process_device_data_for_alarms(
    devices_data: List[Dict[str, Any]],
    device_type_code: str
) -> List[Dict]:
    """
    处理设备数据并检测报警
    
    Args:
        devices_data: 设备数据列表，每个元素包含设备信息和监测数据
        device_type_code: 设备类型代码
        
    Returns:
        触发的报警列表
    """
    all_alarms = []
    
    for device_data in devices_data:
        try:
            # 提取设备信息
            device_code = device_data.get("device_code") or device_data.get("prod_code")
            device_name = device_data.get("device_name") or device_data.get("prod_name")
            
            if not device_code:
                continue
            
            # 提取监测数据（排除非数值字段）
            monitoring_data = {}
            exclude_keys = {
                "device_code", "prod_code", "device_name", "prod_name",
                "device_id", "id", "device_type", "type_code",
                "status", "device_status", "online_status",
                "created_at", "updated_at", "ts", "timestamp",
                "install_location", "workshop", "line"
            }
            
            for key, value in device_data.items():
                if key.lower() not in exclude_keys and value is not None:
                    # 尝试转换为数值
                    try:
                        if isinstance(value, (int, float)):
                            monitoring_data[key] = value
                        elif isinstance(value, str) and value.replace(".", "").replace("-", "").isdigit():
                            monitoring_data[key] = float(value)
                    except (ValueError, TypeError):
                        pass
            
            if not monitoring_data:
                continue
            
            # 检测报警
            alarms = await check_and_trigger_alarms(
                device_code=device_code,
                device_name=device_name,
                device_type_code=device_type_code,
                data=monitoring_data
            )
            
            if alarms:
                all_alarms.extend(alarms)
                
        except Exception as e:
            logger.error(f"处理设备 {device_data.get('device_code')} 报警检测失败: {str(e)}")
    
    # 广播报警
    if all_alarms:
        await broadcast_new_alarms(all_alarms)
        logger.info(f"触发 {len(all_alarms)} 条报警")
    
    return all_alarms


async def check_single_device_alarms(
    device_code: str,
    device_name: Optional[str],
    device_type_code: str,
    data: Dict[str, Any]
) -> List[Dict]:
    """
    检测单个设备的报警
    
    Args:
        device_code: 设备编码
        device_name: 设备名称
        device_type_code: 设备类型代码
        data: 设备监测数据
        
    Returns:
        触发的报警列表
    """
    alarms = await check_and_trigger_alarms(
        device_code=device_code,
        device_name=device_name,
        device_type_code=device_type_code,
        data=data
    )
    
    if alarms:
        await broadcast_new_alarms(alarms)
    
    return alarms


class AlarmBackgroundTask:
    """报警后台任务"""
    
    def __init__(self):
        self._running = False
        self._task = None
    
    async def start(self):
        """启动后台任务"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("报警后台任务已启动")
    
    async def stop(self):
        """停止后台任务"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("报警后台任务已停止")
    
    async def _run(self):
        """后台任务主循环"""
        while self._running:
            try:
                # 定期刷新规则缓存
                await alarm_engine.load_rules()
                
                # 等待一段时间
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"报警后台任务错误: {str(e)}")
                await asyncio.sleep(10)


# 全局后台任务实例
alarm_background_task = AlarmBackgroundTask()
