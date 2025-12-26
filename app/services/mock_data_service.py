# -*- coding: utf-8 -*-
"""
模拟数据服务
当TDengine服务不可用时提供模拟数据
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.log import logger


class MockDataService:
    """模拟数据服务类"""
    
    def __init__(self):
        """初始化模拟数据服务"""
        self.device_types = [
            {"id": 1, "name": "温度传感器", "code": "TEMP_SENSOR", "description": "温度监测设备"},
            {"id": 2, "name": "湿度传感器", "code": "HUMIDITY_SENSOR", "description": "湿度监测设备"},
            {"id": 3, "name": "压力传感器", "code": "PRESSURE_SENSOR", "description": "压力监测设备"},
            {"id": 4, "name": "流量计", "code": "FLOW_METER", "description": "流量监测设备"},
            {"id": 5, "name": "液位计", "code": "LEVEL_METER", "description": "液位监测设备"}
        ]
        
        self.devices = []
        self._generate_mock_devices()
        
        logger.info("模拟数据服务已初始化")
    
    def _generate_mock_devices(self):
        """生成模拟设备数据"""
        device_id = 1
        for device_type in self.device_types:
            for i in range(3):  # 每种类型生成3个设备
                device = {
                    "id": device_id,
                    "name": f"{device_type['name']}-{i+1:02d}",
                    "device_id": f"{device_type['code']}_{device_id:03d}",
                    "type_id": device_type["id"],
                    "type_name": device_type["name"],
                    "status": random.choice(["online", "offline", "warning"]),
                    "location": f"区域{random.randint(1, 5)}-{random.randint(1, 10)}号位置",
                    "last_update": datetime.now() - timedelta(minutes=random.randint(1, 30))
                }
                self.devices.append(device)
                device_id += 1
    
    async def get_device_types(self) -> List[Dict[str, Any]]:
        """获取设备类型列表"""
        logger.info("返回模拟设备类型数据")
        return self.device_types
    
    async def get_devices(self, page: int = 1, page_size: int = 20, device_type: Optional[str] = None) -> Dict[str, Any]:
        """获取设备列表（分页）"""
        devices = self.devices.copy()
        
        # 过滤设备类型
        if device_type and device_type != "全部":
            devices = [d for d in devices if d["type_name"] == device_type]
        
        # 分页
        total = len(devices)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_devices = devices[start_idx:end_idx]
        
        # 更新设备状态和数据
        for device in page_devices:
            device["last_update"] = datetime.now() - timedelta(minutes=random.randint(1, 30))
            device["status"] = random.choice(["online", "offline", "warning"])
            device["value"] = round(random.uniform(10, 100), 2)
            device["unit"] = self._get_unit_by_type(device["type_name"])
        
        logger.info(f"返回模拟设备数据: 第{page}页，共{total}条记录")
        
        return {
            "devices": page_devices,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    async def get_device_realtime_data(self, device_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """获取设备实时数据"""
        devices = self.devices.copy()
        
        if device_ids:
            devices = [d for d in devices if d["device_id"] in device_ids]
        
        realtime_data = []
        for device in devices:
            data = {
                "device_id": device["device_id"],
                "device_name": device["name"],
                "type_name": device["type_name"],
                "status": random.choice(["online", "offline", "warning"]),
                "value": round(random.uniform(10, 100), 2),
                "unit": self._get_unit_by_type(device["type_name"]),
                "timestamp": datetime.now().isoformat(),
                "location": device["location"]
            }
            realtime_data.append(data)
        
        logger.info(f"返回{len(realtime_data)}个设备的模拟实时数据")
        return realtime_data
    
    def _get_unit_by_type(self, type_name: str) -> str:
        """根据设备类型获取单位"""
        unit_map = {
            "温度传感器": "°C",
            "湿度传感器": "%RH",
            "压力传感器": "Pa",
            "流量计": "L/min",
            "液位计": "m"
        }
        return unit_map.get(type_name, "")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy",
            "service": "mock_data_service",
            "timestamp": datetime.now().isoformat(),
            "device_count": len(self.devices),
            "device_type_count": len(self.device_types)
        }


# 全局模拟数据服务实例
mock_data_service = MockDataService()