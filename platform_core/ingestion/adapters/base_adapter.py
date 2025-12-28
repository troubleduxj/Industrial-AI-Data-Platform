#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
协议适配器基类

定义数据采集适配器的抽象接口和通用功能。
支持多种协议（MQTT、HTTP、Modbus等）的统一数据采集。

需求: 5.1 - 支持MQTT、HTTP、Modbus等协议适配器
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, AsyncIterator, Optional, List
import logging
import asyncio

logger = logging.getLogger(__name__)


class AdapterStatus(str, Enum):
    """适配器状态枚举"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    RECONNECTING = "reconnecting"


@dataclass
class DataPoint:
    """
    数据点 - 采集到的单条数据记录
    
    Attributes:
        asset_code: 资产编码
        timestamp: 数据时间戳
        signals: 信号数据字典 {信号编码: 值}
        quality: 数据质量标识 (good/bad/uncertain)
        source: 数据来源标识
        metadata: 附加元数据
    """
    asset_code: str
    timestamp: datetime
    signals: Dict[str, Any]
    quality: str = "good"
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "asset_code": self.asset_code,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "signals": self.signals,
            "quality": self.quality,
            "source": self.source,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataPoint":
        """从字典创建"""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()
        
        return cls(
            asset_code=data.get("asset_code", ""),
            timestamp=timestamp,
            signals=data.get("signals", {}),
            quality=data.get("quality", "good"),
            source=data.get("source", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AdapterStatistics:
    """
    适配器统计信息
    
    Attributes:
        success_count: 成功接收的数据点数量
        error_count: 错误数量
        last_success_time: 最后成功接收时间
        last_error_time: 最后错误时间
        last_error_message: 最后错误信息
        total_bytes_received: 总接收字节数
        connection_count: 连接次数
        reconnection_count: 重连次数
        uptime_seconds: 运行时长（秒）
    """
    success_count: int = 0
    error_count: int = 0
    last_success_time: Optional[datetime] = None
    last_error_time: Optional[datetime] = None
    last_error_message: Optional[str] = None
    total_bytes_received: int = 0
    connection_count: int = 0
    reconnection_count: int = 0
    uptime_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success_count": self.success_count,
            "error_count": self.error_count,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
            "last_error_message": self.last_error_message,
            "total_bytes_received": self.total_bytes_received,
            "connection_count": self.connection_count,
            "reconnection_count": self.reconnection_count,
            "uptime_seconds": self.uptime_seconds,
            "success_rate": self.success_rate,
        }
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        total = self.success_count + self.error_count
        if total == 0:
            return 0.0
        return self.success_count / total
    
    def record_success(self, bytes_received: int = 0):
        """记录成功"""
        self.success_count += 1
        self.last_success_time = datetime.now()
        self.total_bytes_received += bytes_received
    
    def record_error(self, error_message: str):
        """记录错误"""
        self.error_count += 1
        self.last_error_time = datetime.now()
        self.last_error_message = error_message
    
    def record_connection(self):
        """记录连接"""
        self.connection_count += 1
    
    def record_reconnection(self):
        """记录重连"""
        self.reconnection_count += 1
    
    def reset(self):
        """重置统计"""
        self.success_count = 0
        self.error_count = 0
        self.last_success_time = None
        self.last_error_time = None
        self.last_error_message = None
        self.total_bytes_received = 0
        self.connection_count = 0
        self.reconnection_count = 0
        self.uptime_seconds = 0.0


class BaseAdapter(ABC):
    """
    协议适配器基类
    
    定义数据采集适配器的抽象接口，所有协议适配器都应继承此类。
    
    Attributes:
        config: 适配器配置字典
        name: 适配器名称
        protocol: 协议类型
    """
    
    def __init__(self, config: Dict[str, Any], name: Optional[str] = None):
        """
        初始化适配器
        
        Args:
            config: 适配器配置字典
            name: 适配器名称（可选）
        """
        self.config = config
        self.name = name or config.get("name", self.__class__.__name__)
        self.protocol = config.get("protocol", "unknown")
        
        # 状态管理
        self._status = AdapterStatus.STOPPED
        self._statistics = AdapterStatistics()
        self._start_time: Optional[datetime] = None
        
        # 控制标志
        self._running = False
        self._stop_event = asyncio.Event()
        
        # 回调函数
        self._on_data_callbacks: List[callable] = []
        self._on_error_callbacks: List[callable] = []
        self._on_status_change_callbacks: List[callable] = []
    
    @property
    def status(self) -> AdapterStatus:
        """获取适配器状态"""
        return self._status
    
    @status.setter
    def status(self, value: AdapterStatus):
        """设置适配器状态"""
        old_status = self._status
        self._status = value
        if old_status != value:
            self._notify_status_change(old_status, value)
    
    @property
    def statistics(self) -> AdapterStatistics:
        """获取统计信息"""
        # 更新运行时长
        if self._start_time and self._running:
            self._statistics.uptime_seconds = (datetime.now() - self._start_time).total_seconds()
        return self._statistics
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._running and self._status == AdapterStatus.RUNNING
    
    # =====================================================
    # 抽象方法 - 子类必须实现
    # =====================================================
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        建立连接
        
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @abstractmethod
    async def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    async def receive(self) -> AsyncIterator[DataPoint]:
        """
        接收数据
        
        Yields:
            DataPoint: 接收到的数据点
        """
        pass
    
    # =====================================================
    # 生命周期管理
    # =====================================================
    
    async def start(self) -> bool:
        """
        启动适配器
        
        Returns:
            bool: 启动是否成功
        """
        if self._running:
            logger.warning(f"适配器 {self.name} 已在运行中")
            return True
        
        try:
            self.status = AdapterStatus.STARTING
            self._stop_event.clear()
            
            # 建立连接
            connected = await self.connect()
            if not connected:
                self.status = AdapterStatus.ERROR
                self._statistics.record_error("连接失败")
                return False
            
            self._running = True
            self._start_time = datetime.now()
            self._statistics.record_connection()
            self.status = AdapterStatus.RUNNING
            
            logger.info(f"适配器 {self.name} 启动成功")
            return True
            
        except Exception as e:
            self.status = AdapterStatus.ERROR
            self._statistics.record_error(str(e))
            logger.error(f"适配器 {self.name} 启动失败: {e}")
            return False
    
    async def stop(self):
        """停止适配器"""
        if not self._running:
            return
        
        try:
            self.status = AdapterStatus.STOPPING
            self._running = False
            self._stop_event.set()
            
            await self.disconnect()
            
            self.status = AdapterStatus.STOPPED
            logger.info(f"适配器 {self.name} 已停止")
            
        except Exception as e:
            self.status = AdapterStatus.ERROR
            self._statistics.record_error(str(e))
            logger.error(f"适配器 {self.name} 停止失败: {e}")
    
    async def restart(self) -> bool:
        """
        重启适配器
        
        Returns:
            bool: 重启是否成功
        """
        await self.stop()
        await asyncio.sleep(1)  # 等待资源释放
        return await self.start()
    
    # =====================================================
    # 数据处理
    # =====================================================
    
    async def run(self):
        """
        运行数据采集循环
        
        持续接收数据并通知回调函数。
        """
        if not await self.start():
            return
        
        try:
            async for data_point in self.receive():
                if not self._running:
                    break
                
                # 记录成功
                self._statistics.record_success()
                
                # 通知回调
                await self._notify_data(data_point)
                
        except Exception as e:
            self._statistics.record_error(str(e))
            logger.error(f"适配器 {self.name} 运行错误: {e}")
            await self._notify_error(e)
        finally:
            await self.stop()
    
    def process_raw_data(self, raw_data: bytes, topic: Optional[str] = None) -> Optional[DataPoint]:
        """
        处理原始数据
        
        子类可以重写此方法来自定义数据解析逻辑。
        
        Args:
            raw_data: 原始字节数据
            topic: 主题（可选，用于MQTT等协议）
        
        Returns:
            DataPoint: 解析后的数据点，解析失败返回None
        """
        import json
        
        try:
            data = json.loads(raw_data.decode("utf-8"))
            return self._parse_data(data, topic)
        except Exception as e:
            self._statistics.record_error(f"数据解析失败: {e}")
            logger.error(f"适配器 {self.name} 数据解析失败: {e}")
            return None
    
    def _parse_data(self, data: Dict[str, Any], topic: Optional[str] = None) -> Optional[DataPoint]:
        """
        解析数据字典为DataPoint
        
        Args:
            data: 数据字典
            topic: 主题（可选）
        
        Returns:
            DataPoint: 解析后的数据点
        """
        # 从数据或主题中提取资产编码
        asset_code = data.get("asset_code")
        if not asset_code and topic:
            # 尝试从主题中提取（假设主题格式为 prefix/asset_code）
            parts = topic.split("/")
            if parts:
                asset_code = parts[-1]
        
        if not asset_code:
            logger.warning(f"适配器 {self.name} 无法确定资产编码")
            return None
        
        # 解析时间戳
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                timestamp = datetime.now()
        elif timestamp is None:
            timestamp = datetime.now()
        
        # 提取信号数据
        signals = data.get("signals", data.get("data", {}))
        if not isinstance(signals, dict):
            signals = {"value": signals}
        
        return DataPoint(
            asset_code=asset_code,
            timestamp=timestamp,
            signals=signals,
            quality=data.get("quality", "good"),
            source=self.protocol,
            metadata=data.get("metadata", {}),
        )
    
    # =====================================================
    # 回调管理
    # =====================================================
    
    def on_data(self, callback: callable):
        """
        注册数据回调
        
        Args:
            callback: 回调函数，接收DataPoint参数
        """
        self._on_data_callbacks.append(callback)
    
    def on_error(self, callback: callable):
        """
        注册错误回调
        
        Args:
            callback: 回调函数，接收Exception参数
        """
        self._on_error_callbacks.append(callback)
    
    def on_status_change(self, callback: callable):
        """
        注册状态变更回调
        
        Args:
            callback: 回调函数，接收(old_status, new_status)参数
        """
        self._on_status_change_callbacks.append(callback)
    
    async def _notify_data(self, data_point: DataPoint):
        """通知数据回调"""
        for callback in self._on_data_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data_point)
                else:
                    callback(data_point)
            except Exception as e:
                logger.error(f"数据回调执行失败: {e}")
    
    async def _notify_error(self, error: Exception):
        """通知错误回调"""
        for callback in self._on_error_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(error)
                else:
                    callback(error)
            except Exception as e:
                logger.error(f"错误回调执行失败: {e}")
    
    def _notify_status_change(self, old_status: AdapterStatus, new_status: AdapterStatus):
        """通知状态变更回调"""
        for callback in self._on_status_change_callbacks:
            try:
                callback(old_status, new_status)
            except Exception as e:
                logger.error(f"状态变更回调执行失败: {e}")
    
    # =====================================================
    # 工具方法
    # =====================================================
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键
            default: 默认值
        
        Returns:
            配置值
        """
        return self.config.get(key, default)
    
    def validate_config(self) -> tuple[bool, List[str]]:
        """
        验证配置
        
        子类可以重写此方法来添加自定义验证逻辑。
        
        Returns:
            tuple[bool, List[str]]: (是否有效, 错误列表)
        """
        errors = []
        
        # 基础验证
        if not self.config:
            errors.append("配置不能为空")
        
        return len(errors) == 0, errors
    
    def get_status_info(self) -> Dict[str, Any]:
        """
        获取状态信息
        
        Returns:
            Dict: 状态信息字典
        """
        return {
            "name": self.name,
            "protocol": self.protocol,
            "status": self._status.value,
            "is_running": self.is_running,
            "statistics": self.statistics.to_dict(),
            "start_time": self._start_time.isoformat() if self._start_time else None,
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, protocol={self.protocol}, status={self._status.value})>"
