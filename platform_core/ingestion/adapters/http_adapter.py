#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HTTP协议适配器

实现基于HTTP协议的数据采集适配器。
支持轮询模式从HTTP端点获取数据。

需求: 5.1 - 支持HTTP协议适配器
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


class HTTPAdapter(BaseAdapter):
    """
    HTTP协议适配器
    
    支持通过HTTP轮询方式采集数据。
    
    配置示例:
    {
        "name": "http_adapter_1",
        "protocol": "http",
        "url": "http://localhost:8080/api/data",
        "method": "GET",
        "headers": {"Authorization": "Bearer token"},
        "params": {"device_id": "device_001"},
        "body": null,
        "poll_interval": 5,
        "timeout": 30,
        "retry_count": 3,
        "retry_delay": 1,
        "verify_ssl": true,
        "auth": {
            "type": "basic",
            "username": "user",
            "password": "pass"
        },
        "response_format": "json",
        "data_path": "data.items"
    }
    """
    
    def __init__(self, config: Dict[str, Any], name: Optional[str] = None):
        """
        初始化HTTP适配器
        
        Args:
            config: HTTP配置字典
            name: 适配器名称
        """
        config["protocol"] = "http"
        super().__init__(config, name)
        
        # HTTP配置
        self._url = config.get("url", "")
        self._method = config.get("method", "GET").upper()
        self._headers = config.get("headers", {})
        self._params = config.get("params", {})
        self._body = config.get("body")
        
        # 轮询配置
        self._poll_interval = config.get("poll_interval", 5)  # 秒
        
        # 请求配置
        self._timeout = config.get("timeout", 30)
        self._retry_count = config.get("retry_count", 3)
        self._retry_delay = config.get("retry_delay", 1)
        self._verify_ssl = config.get("verify_ssl", True)
        
        # 认证配置
        self._auth_config = config.get("auth", {})
        
        # 响应解析配置
        self._response_format = config.get("response_format", "json")
        self._data_path = config.get("data_path", "")  # 数据在响应中的路径，如 "data.items"
        
        # HTTP客户端
        self._client = None
        self._session = None
    
    def validate_config(self) -> tuple[bool, List[str]]:
        """验证HTTP配置"""
        is_valid, errors = super().validate_config()
        
        if not self._url:
            errors.append("HTTP url 不能为空")
        
        if self._method not in ["GET", "POST", "PUT", "PATCH"]:
            errors.append("HTTP method 必须是 GET, POST, PUT 或 PATCH")
        
        if self._poll_interval <= 0:
            errors.append("poll_interval 必须大于0")
        
        if self._timeout <= 0:
            errors.append("timeout 必须大于0")
        
        return len(errors) == 0, errors
    
    async def connect(self) -> bool:
        """
        建立HTTP连接（创建会话）
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 尝试导入httpx（推荐）或aiohttp
            try:
                import httpx
                return await self._connect_with_httpx()
            except ImportError:
                try:
                    import aiohttp
                    return await self._connect_with_aiohttp()
                except ImportError:
                    logger.error("未安装HTTP客户端库，请安装 httpx 或 aiohttp")
                    return False
                    
        except Exception as e:
            self._statistics.record_error(f"HTTP连接失败: {e}")
            logger.error(f"HTTP适配器 {self.name} 连接失败: {e}")
            return False
    
    async def _connect_with_httpx(self) -> bool:
        """使用httpx创建会话"""
        import httpx
        
        # 配置认证
        auth = None
        if self._auth_config:
            auth_type = self._auth_config.get("type", "").lower()
            if auth_type == "basic":
                auth = httpx.BasicAuth(
                    self._auth_config.get("username", ""),
                    self._auth_config.get("password", "")
                )
        
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout),
            verify=self._verify_ssl,
            auth=auth,
            headers=self._headers,
        )
        
        # 测试连接
        try:
            response = await self._client.request(
                self._method,
                self._url,
                params=self._params if self._method == "GET" else None,
                json=self._body if self._method != "GET" and self._body else None,
            )
            response.raise_for_status()
            logger.info(f"HTTP适配器 {self.name} 连接测试成功: {self._url}")
            return True
        except Exception as e:
            logger.warning(f"HTTP连接测试失败（将继续尝试）: {e}")
            return True  # 即使测试失败也返回True，让轮询继续
    
    async def _connect_with_aiohttp(self) -> bool:
        """使用aiohttp创建会话"""
        import aiohttp
        
        # 配置认证
        auth = None
        if self._auth_config:
            auth_type = self._auth_config.get("type", "").lower()
            if auth_type == "basic":
                auth = aiohttp.BasicAuth(
                    self._auth_config.get("username", ""),
                    self._auth_config.get("password", "")
                )
        
        connector = aiohttp.TCPConnector(ssl=self._verify_ssl)
        timeout = aiohttp.ClientTimeout(total=self._timeout)
        
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            auth=auth,
            headers=self._headers,
        )
        
        logger.info(f"HTTP适配器 {self.name} 会话创建成功")
        return True
    
    async def disconnect(self):
        """关闭HTTP会话"""
        try:
            if self._client:
                await self._client.aclose()
                self._client = None
            
            if self._session:
                await self._session.close()
                self._session = None
            
            logger.info(f"HTTP适配器 {self.name} 会话已关闭")
            
        except Exception as e:
            logger.error(f"HTTP关闭会话失败: {e}")
    
    async def receive(self) -> AsyncIterator[DataPoint]:
        """
        轮询接收HTTP数据
        
        Yields:
            DataPoint: 解析后的数据点
        """
        while self._running:
            try:
                # 发送请求
                data_points = await self._fetch_data()
                
                # 产出数据点
                for data_point in data_points:
                    if not self._running:
                        break
                    yield data_point
                
                # 等待下一次轮询
                await asyncio.sleep(self._poll_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._statistics.record_error(str(e))
                logger.error(f"HTTP轮询失败: {e}")
                await asyncio.sleep(self._poll_interval)
    
    async def _fetch_data(self) -> List[DataPoint]:
        """
        获取数据
        
        Returns:
            List[DataPoint]: 数据点列表
        """
        for attempt in range(self._retry_count):
            try:
                response_data = await self._make_request()
                
                if response_data is None:
                    continue
                
                # 解析响应
                data_points = self._parse_response(response_data)
                return data_points
                
            except Exception as e:
                self._statistics.record_error(str(e))
                logger.warning(f"HTTP请求失败 (尝试 {attempt + 1}/{self._retry_count}): {e}")
                
                if attempt < self._retry_count - 1:
                    await asyncio.sleep(self._retry_delay)
        
        return []
    
    async def _make_request(self) -> Optional[Dict[str, Any]]:
        """
        发送HTTP请求
        
        Returns:
            响应数据
        """
        if self._client:
            return await self._request_with_httpx()
        elif self._session:
            return await self._request_with_aiohttp()
        else:
            raise RuntimeError("HTTP客户端未初始化")
    
    async def _request_with_httpx(self) -> Optional[Dict[str, Any]]:
        """使用httpx发送请求"""
        response = await self._client.request(
            self._method,
            self._url,
            params=self._params if self._method == "GET" else None,
            json=self._body if self._method != "GET" and self._body else None,
        )
        
        response.raise_for_status()
        
        # 记录统计
        self._statistics.total_bytes_received += len(response.content)
        
        if self._response_format == "json":
            return response.json()
        else:
            return {"raw": response.text}
    
    async def _request_with_aiohttp(self) -> Optional[Dict[str, Any]]:
        """使用aiohttp发送请求"""
        async with self._session.request(
            self._method,
            self._url,
            params=self._params if self._method == "GET" else None,
            json=self._body if self._method != "GET" and self._body else None,
        ) as response:
            response.raise_for_status()
            
            content = await response.read()
            self._statistics.total_bytes_received += len(content)
            
            if self._response_format == "json":
                return await response.json()
            else:
                return {"raw": await response.text()}
    
    def _parse_response(self, response_data: Dict[str, Any]) -> List[DataPoint]:
        """
        解析HTTP响应
        
        Args:
            response_data: 响应数据
        
        Returns:
            List[DataPoint]: 数据点列表
        """
        data_points = []
        
        # 根据data_path提取数据
        data = self._extract_data(response_data)
        
        if data is None:
            return data_points
        
        # 处理数据（可能是单个对象或列表）
        if isinstance(data, list):
            for item in data:
                data_point = self._parse_item(item)
                if data_point:
                    data_points.append(data_point)
                    self._statistics.record_success()
        elif isinstance(data, dict):
            data_point = self._parse_item(data)
            if data_point:
                data_points.append(data_point)
                self._statistics.record_success()
        
        return data_points
    
    def _extract_data(self, response_data: Dict[str, Any]) -> Any:
        """
        根据data_path从响应中提取数据
        
        Args:
            response_data: 响应数据
        
        Returns:
            提取的数据
        """
        if not self._data_path:
            return response_data
        
        data = response_data
        for key in self._data_path.split("."):
            if isinstance(data, dict) and key in data:
                data = data[key]
            elif isinstance(data, list) and key.isdigit():
                index = int(key)
                if 0 <= index < len(data):
                    data = data[index]
                else:
                    return None
            else:
                return None
        
        return data
    
    def _parse_item(self, item: Dict[str, Any]) -> Optional[DataPoint]:
        """
        解析单个数据项为DataPoint
        
        Args:
            item: 数据项
        
        Returns:
            DataPoint: 数据点
        """
        # 提取资产编码
        asset_code = (
            item.get("asset_code") or
            item.get("device_id") or
            item.get("id") or
            item.get("code")
        )
        
        if not asset_code:
            logger.warning("HTTP响应中缺少资产编码")
            return None
        
        # 解析时间戳
        timestamp = item.get("timestamp") or item.get("ts") or item.get("time")
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                timestamp = datetime.now()
        elif isinstance(timestamp, (int, float)):
            if timestamp > 1e12:
                timestamp = datetime.fromtimestamp(timestamp / 1000)
            else:
                timestamp = datetime.fromtimestamp(timestamp)
        else:
            timestamp = datetime.now()
        
        # 提取信号数据
        signals = item.get("signals") or item.get("data") or item.get("values")
        if signals is None:
            exclude_keys = {"asset_code", "device_id", "id", "code", "timestamp", "ts", "time", "quality", "metadata"}
            signals = {k: v for k, v in item.items() if k not in exclude_keys}
        
        if not isinstance(signals, dict):
            signals = {"value": signals}
        
        return DataPoint(
            asset_code=str(asset_code),
            timestamp=timestamp,
            signals=signals,
            quality=item.get("quality", "good"),
            source="http",
            metadata={
                "url": self._url,
                **item.get("metadata", {})
            },
        )
    
    async def fetch_once(self) -> List[DataPoint]:
        """
        单次获取数据（不进入轮询循环）
        
        Returns:
            List[DataPoint]: 数据点列表
        """
        if not self._client and not self._session:
            await self.connect()
        
        return await self._fetch_data()
    
    def get_status_info(self) -> Dict[str, Any]:
        """获取状态信息"""
        info = super().get_status_info()
        info.update({
            "url": self._url,
            "method": self._method,
            "poll_interval": self._poll_interval,
            "timeout": self._timeout,
            "retry_count": self._retry_count,
            "data_path": self._data_path,
        })
        return info
