# -*- coding: utf-8 -*-
"""
TDengine服务类 - 薄封装层
此模块已简化为platform_core的薄封装层
核心逻辑已迁移到 platform_core/timeseries/

Requirements: 7.1, 7.4 - 服务调用路径统一
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


class TDengineService:
    """TDengine服务类 - 委托给platform_core"""
    
    def __init__(self, server_name: Optional[str] = None):
        self.server_name = server_name
        self._client = None
    
    @property
    def client(self):
        """延迟加载platform_core TDengine客户端"""
        if self._client is None:
            from platform_core.timeseries import get_tdengine_client
            self._client = get_tdengine_client(self.server_name)
        return self._client
    
    async def health_check(self) -> Dict[str, Any]:
        """执行健康检查"""
        try:
            return await self.client.health_check()
        except Exception as e:
            logger.error(f"TDengine健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_connection(self) -> bool:
        """测试连接"""
        try:
            health = await self.health_check()
            return health.get("status") == "healthy"
        except Exception:
            return False

    async def execute_query(self, sql: str, database: Optional[str] = None) -> Dict[str, Any]:
        """执行查询"""
        try:
            return await self.client.query(sql, database)
        except Exception as e:
            logger.error(f"TDengine查询执行失败: {sql}, 错误: {e}")
            raise
    
    async def execute_sql(self, sql: str, database: Optional[str] = None) -> Dict[str, Any]:
        """执行SQL语句"""
        try:
            return await self.client.execute(sql, database)
        except Exception as e:
            logger.error(f"TDengine SQL执行失败: {sql}, 错误: {e}")
            raise
    
    async def get_databases(self) -> List[str]:
        """获取数据库列表"""
        try:
            return await self.client.get_databases()
        except Exception as e:
            logger.error(f"获取TDengine数据库列表失败: {e}")
            return []
    
    async def get_tables(self, database: str) -> List[str]:
        """获取表列表"""
        try:
            return await self.client.get_tables(database)
        except Exception as e:
            logger.error(f"获取TDengine表列表失败: {e}")
            return []
    
    async def get_super_tables(self, database: str) -> List[str]:
        """获取超级表列表"""
        try:
            return await self.client.get_super_tables(database)
        except Exception as e:
            logger.error(f"获取TDengine超级表列表失败: {e}")
            return []
    
    async def close(self):
        """关闭连接"""
        if self._client:
            await self._client.close()
            self._client = None


class TDengineServiceManager:
    """TDengine服务管理器"""
    
    def __init__(self):
        self._services: Dict[str, TDengineService] = {}
    
    def get_service(self, server_name: Optional[str] = None) -> TDengineService:
        """获取TDengine服务实例"""
        key = server_name or "default"
        if key not in self._services:
            self._services[key] = TDengineService(server_name)
        return self._services[key]
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """对所有服务器进行健康检查"""
        from app.core.tdengine_config import tdengine_config_manager
        results = {}
        server_names = tdengine_config_manager.list_servers()
        
        for server_name in server_names:
            service = self.get_service(server_name)
            try:
                results[server_name] = await service.health_check()
            except Exception as e:
                results[server_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        return results
    
    async def close_all(self):
        """关闭所有服务连接"""
        for service in self._services.values():
            await service.close()
        self._services.clear()


# 全局服务管理器实例
tdengine_service_manager = TDengineServiceManager()
