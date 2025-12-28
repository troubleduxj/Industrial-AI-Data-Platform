#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MQTT协议适配器

实现基于MQTT协议的数据采集适配器。
支持连接MQTT Broker、订阅主题、接收和解析消息。

需求: 5.1 - 支持MQTT协议适配器
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, AsyncIterator, Optional, List

from platform_core.ingestion.adapters.base_adapter import (
    BaseAdapter,
    DataPoint,
    AdapterStatus,
)

logger = logging.getLogger(__name__)


class MQTTAdapter(BaseAdapter):
    """
    MQTT协议适配器
    
    支持连接MQTT Broker，订阅主题并接收数据。
    
    配置示例:
    {
        "name": "mqtt_adapter_1",
        "protocol": "mqtt",
        "host": "localhost",
        "port": 1883,
        "username": "user",
        "password": "pass",
        "topics": ["sensors/#", "devices/+/data"],
        "client_id": "ingestion_client_1",
        "qos": 1,
        "keepalive": 60,
        "clean_session": True,
        "reconnect_interval": 5,
        "max_reconnect_attempts": 10
    }
    """
    
    def __init__(self, config: Dict[str, Any], name: Optional[str] = None):
        """
        初始化MQTT适配器
        
        Args:
            config: MQTT配置字典
            name: 适配器名称
        """
        config["protocol"] = "mqtt"
        super().__init__(config, name)
        
        # MQTT配置
        self._host = config.get("host", "localhost")
        self._port = config.get("port", 1883)
        self._username = config.get("username")
        self._password = config.get("password")
        self._topics = config.get("topics", ["#"])
        self._client_id = config.get("client_id", f"ingestion_{id(self)}")
        self._qos = config.get("qos", 1)
        self._keepalive = config.get("keepalive", 60)
        self._clean_session = config.get("clean_session", True)
        
        # 重连配置
        self._reconnect_interval = config.get("reconnect_interval", 5)
        self._max_reconnect_attempts = config.get("max_reconnect_attempts", 10)
        self._reconnect_attempts = 0
        
        # MQTT客户端
        self._client = None
        self._message_queue: asyncio.Queue = asyncio.Queue()
    
    def validate_config(self) -> tuple[bool, List[str]]:
        """验证MQTT配置"""
        is_valid, errors = super().validate_config()
        
        if not self._host:
            errors.append("MQTT host 不能为空")
        
        if not isinstance(self._port, int) or self._port <= 0:
            errors.append("MQTT port 必须是正整数")
        
        if not self._topics:
            errors.append("MQTT topics 不能为空")
        
        if self._qos not in [0, 1, 2]:
            errors.append("MQTT qos 必须是 0, 1 或 2")
        
        return len(errors) == 0, errors
    
    async def connect(self) -> bool:
        """
        连接MQTT Broker
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 尝试导入 aiomqtt (paho-mqtt的异步包装)
            try:
                import aiomqtt
                return await self._connect_with_aiomqtt()
            except ImportError:
                # 如果没有aiomqtt，使用paho-mqtt的同步客户端
                try:
                    import paho.mqtt.client as mqtt
                    return await self._connect_with_paho()
                except ImportError:
                    logger.error("未安装MQTT客户端库，请安装 aiomqtt 或 paho-mqtt")
                    return False
                    
        except Exception as e:
            self._statistics.record_error(f"MQTT连接失败: {e}")
            logger.error(f"MQTT适配器 {self.name} 连接失败: {e}")
            return False
    
    async def _connect_with_aiomqtt(self) -> bool:
        """使用aiomqtt连接"""
        import aiomqtt
        
        try:
            self._client = aiomqtt.Client(
                hostname=self._host,
                port=self._port,
                username=self._username,
                password=self._password,
                identifier=self._client_id,
                clean_session=self._clean_session,
            )
            
            await self._client.__aenter__()
            
            # 订阅主题
            for topic in self._topics:
                await self._client.subscribe(topic, qos=self._qos)
                logger.info(f"MQTT适配器 {self.name} 订阅主题: {topic}")
            
            self._reconnect_attempts = 0
            logger.info(f"MQTT适配器 {self.name} 连接成功: {self._host}:{self._port}")
            return True
            
        except Exception as e:
            logger.error(f"aiomqtt连接失败: {e}")
            raise
    
    async def _connect_with_paho(self) -> bool:
        """使用paho-mqtt连接（同步客户端的异步包装）"""
        import paho.mqtt.client as mqtt
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logger.info(f"MQTT适配器 {self.name} 连接成功")
                # 订阅主题
                for topic in self._topics:
                    client.subscribe(topic, qos=self._qos)
                    logger.info(f"MQTT适配器 {self.name} 订阅主题: {topic}")
            else:
                logger.error(f"MQTT连接失败，返回码: {rc}")
        
        def on_message(client, userdata, msg):
            # 将消息放入队列
            try:
                asyncio.get_event_loop().call_soon_threadsafe(
                    self._message_queue.put_nowait,
                    (msg.topic, msg.payload)
                )
            except Exception as e:
                logger.error(f"消息入队失败: {e}")
        
        def on_disconnect(client, userdata, rc):
            if rc != 0:
                logger.warning(f"MQTT意外断开连接，返回码: {rc}")
        
        self._client = mqtt.Client(
            client_id=self._client_id,
            clean_session=self._clean_session
        )
        
        if self._username:
            self._client.username_pw_set(self._username, self._password)
        
        self._client.on_connect = on_connect
        self._client.on_message = on_message
        self._client.on_disconnect = on_disconnect
        
        # 连接（在线程中运行）
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self._client.connect(self._host, self._port, self._keepalive)
        )
        
        # 启动网络循环
        self._client.loop_start()
        
        # 等待连接完成
        await asyncio.sleep(1)
        
        self._reconnect_attempts = 0
        return self._client.is_connected()
    
    async def disconnect(self):
        """断开MQTT连接"""
        if self._client is None:
            return
        
        try:
            # 检查是否是aiomqtt客户端
            if hasattr(self._client, '__aexit__'):
                await self._client.__aexit__(None, None, None)
            else:
                # paho-mqtt客户端
                self._client.loop_stop()
                self._client.disconnect()
            
            logger.info(f"MQTT适配器 {self.name} 已断开连接")
            
        except Exception as e:
            logger.error(f"MQTT断开连接失败: {e}")
        finally:
            self._client = None
    
    async def receive(self) -> AsyncIterator[DataPoint]:
        """
        接收MQTT消息
        
        Yields:
            DataPoint: 解析后的数据点
        """
        if self._client is None:
            logger.error(f"MQTT适配器 {self.name} 未连接")
            return
        
        try:
            # 检查是否是aiomqtt客户端
            if hasattr(self._client, 'messages'):
                # aiomqtt方式
                async for message in self._client.messages:
                    if not self._running:
                        break
                    
                    data_point = await self._process_message(
                        str(message.topic),
                        message.payload
                    )
                    if data_point:
                        yield data_point
            else:
                # paho-mqtt方式 - 从队列读取
                while self._running:
                    try:
                        topic, payload = await asyncio.wait_for(
                            self._message_queue.get(),
                            timeout=1.0
                        )
                        data_point = await self._process_message(topic, payload)
                        if data_point:
                            yield data_point
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        self._statistics.record_error(str(e))
                        logger.error(f"处理MQTT消息失败: {e}")
                        
        except Exception as e:
            self._statistics.record_error(str(e))
            logger.error(f"MQTT接收消息失败: {e}")
            
            # 尝试重连
            if self._running:
                await self._handle_reconnect()
    
    async def _process_message(self, topic: str, payload: bytes) -> Optional[DataPoint]:
        """
        处理MQTT消息
        
        Args:
            topic: 消息主题
            payload: 消息负载
        
        Returns:
            DataPoint: 解析后的数据点
        """
        try:
            # 记录接收字节数
            self._statistics.total_bytes_received += len(payload)
            
            # 解析JSON
            data = json.loads(payload.decode("utf-8"))
            
            # 解析为DataPoint
            data_point = self._parse_mqtt_message(topic, data)
            
            if data_point:
                self._statistics.record_success(len(payload))
                return data_point
            else:
                self._statistics.record_error("消息解析失败")
                return None
                
        except json.JSONDecodeError as e:
            self._statistics.record_error(f"JSON解析失败: {e}")
            logger.warning(f"MQTT消息JSON解析失败: {e}, topic={topic}")
            return None
        except Exception as e:
            self._statistics.record_error(str(e))
            logger.error(f"处理MQTT消息失败: {e}")
            return None
    
    def _parse_mqtt_message(self, topic: str, data: Dict[str, Any]) -> Optional[DataPoint]:
        """
        解析MQTT消息为DataPoint
        
        Args:
            topic: 消息主题
            data: 解析后的JSON数据
        
        Returns:
            DataPoint: 数据点
        """
        # 从数据或主题中提取资产编码
        asset_code = data.get("asset_code") or data.get("device_id")
        
        if not asset_code:
            # 尝试从主题中提取
            # 支持格式: prefix/asset_code, prefix/asset_code/data, devices/asset_code/telemetry
            parts = topic.split("/")
            if len(parts) >= 2:
                # 尝试找到资产编码（通常是第二个或最后一个非data/telemetry的部分）
                for part in reversed(parts):
                    if part not in ["data", "telemetry", "status", "events", "#", "+"]:
                        asset_code = part
                        break
        
        if not asset_code:
            logger.warning(f"无法从MQTT消息中提取资产编码, topic={topic}")
            return None
        
        # 解析时间戳
        timestamp = data.get("timestamp") or data.get("ts") or data.get("time")
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                timestamp = datetime.now()
        elif isinstance(timestamp, (int, float)):
            # Unix时间戳
            if timestamp > 1e12:  # 毫秒
                timestamp = datetime.fromtimestamp(timestamp / 1000)
            else:
                timestamp = datetime.fromtimestamp(timestamp)
        else:
            timestamp = datetime.now()
        
        # 提取信号数据
        signals = data.get("signals") or data.get("data") or data.get("values")
        if signals is None:
            # 如果没有专门的signals字段，将整个数据作为信号（排除元数据字段）
            exclude_keys = {"asset_code", "device_id", "timestamp", "ts", "time", "quality", "metadata"}
            signals = {k: v for k, v in data.items() if k not in exclude_keys}
        
        if not isinstance(signals, dict):
            signals = {"value": signals}
        
        return DataPoint(
            asset_code=asset_code,
            timestamp=timestamp,
            signals=signals,
            quality=data.get("quality", "good"),
            source="mqtt",
            metadata={
                "topic": topic,
                **data.get("metadata", {})
            },
        )
    
    async def _handle_reconnect(self):
        """处理重连"""
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            logger.error(f"MQTT适配器 {self.name} 达到最大重连次数，停止重连")
            self.status = AdapterStatus.ERROR
            return
        
        self._reconnect_attempts += 1
        self._statistics.record_reconnection()
        self.status = AdapterStatus.RECONNECTING
        
        logger.info(f"MQTT适配器 {self.name} 尝试重连 ({self._reconnect_attempts}/{self._max_reconnect_attempts})")
        
        await asyncio.sleep(self._reconnect_interval)
        
        try:
            await self.disconnect()
            if await self.connect():
                self.status = AdapterStatus.RUNNING
                logger.info(f"MQTT适配器 {self.name} 重连成功")
            else:
                await self._handle_reconnect()
        except Exception as e:
            logger.error(f"MQTT重连失败: {e}")
            await self._handle_reconnect()
    
    async def publish(self, topic: str, payload: Dict[str, Any], qos: int = None) -> bool:
        """
        发布MQTT消息
        
        Args:
            topic: 目标主题
            payload: 消息负载
            qos: QoS级别（可选，默认使用配置值）
        
        Returns:
            bool: 发布是否成功
        """
        if self._client is None:
            logger.error(f"MQTT适配器 {self.name} 未连接，无法发布消息")
            return False
        
        try:
            message = json.dumps(payload)
            qos = qos if qos is not None else self._qos
            
            if hasattr(self._client, 'publish'):
                # aiomqtt或paho-mqtt
                if asyncio.iscoroutinefunction(self._client.publish):
                    await self._client.publish(topic, message, qos=qos)
                else:
                    self._client.publish(topic, message, qos=qos)
            
            logger.debug(f"MQTT消息已发布: topic={topic}")
            return True
            
        except Exception as e:
            logger.error(f"MQTT发布消息失败: {e}")
            return False
    
    def get_status_info(self) -> Dict[str, Any]:
        """获取状态信息"""
        info = super().get_status_info()
        info.update({
            "host": self._host,
            "port": self._port,
            "topics": self._topics,
            "client_id": self._client_id,
            "qos": self._qos,
            "reconnect_attempts": self._reconnect_attempts,
            "connected": self._client is not None and self.is_running,
        })
        return info
