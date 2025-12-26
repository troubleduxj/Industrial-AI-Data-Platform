# -*- coding: utf-8 -*-
"""
TDengine服务类
提供高级TDengine操作接口，支持外部服务器和健康检查
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio

from app.core.tdengine_connector import TDengineConnector
from app.core.tdengine_config import tdengine_config_manager, TDengineServerConfig
from app.log import logger


class TDengineService:
    """TDengine服务类"""
    
    def __init__(self, server_name: Optional[str] = None):
        """
        初始化TDengine服务
        
        Args:
            server_name: 服务器名称，如果为None则使用默认服务器
        """
        self.server_name = server_name
        self._connector: Optional[TDengineConnector] = None
    
    async def get_connector(self) -> TDengineConnector:
        """获取TDengine连接器"""
        if not self._connector:
            self._connector = TDengineConnector(server_name=self.server_name)
        return self._connector
    
    async def health_check(self) -> Dict[str, Any]:
        """执行健康检查"""
        try:
            connector = await self.get_connector()
            return await connector.health_check()
        except Exception as e:
            logger.error(f"TDengine健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_server_info(self) -> Dict[str, Any]:
        """获取服务器信息"""
        try:
            connector = await self.get_connector()
            return await connector.get_server_info()
        except Exception as e:
            logger.error(f"获取TDengine服务器信息失败: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_connection(self) -> bool:
        """测试连接"""
        try:
            health = await self.health_check()
            return health.get("status") == "healthy"
        except Exception as e:
            logger.error(f"TDengine连接测试失败: {e}")
            return False
    
    async def execute_query(self, sql: str, database: Optional[str] = None) -> Dict[str, Any]:
        """执行查询"""
        try:
            connector = await self.get_connector()
            return await connector.query_data(sql, database)
        except Exception as e:
            logger.error(f"TDengine查询执行失败: {sql}, 错误: {e}")
            raise
    
    async def execute_sql(self, sql: str, database: Optional[str] = None) -> Dict[str, Any]:
        """执行SQL语句"""
        try:
            connector = await self.get_connector()
            return await connector.execute_sql(sql, database)
        except Exception as e:
            logger.error(f"TDengine SQL执行失败: {sql}, 错误: {e}")
            raise
    
    async def create_database(self, database_name: str, if_not_exists: bool = True) -> Dict[str, Any]:
        """创建数据库"""
        try:
            connector = await self.get_connector()
            return await connector.create_database(database_name, if_not_exists)
        except Exception as e:
            logger.error(f"创建TDengine数据库失败: {database_name}, 错误: {e}")
            raise
    
    async def create_super_table(
        self, 
        database: str, 
        stable_name: str, 
        columns: Dict[str, str], 
        tags: Dict[str, str], 
        if_not_exists: bool = True
    ) -> Dict[str, Any]:
        """创建超级表"""
        try:
            connector = await self.get_connector()
            return await connector.create_super_table(database, stable_name, columns, tags, if_not_exists)
        except Exception as e:
            logger.error(f"创建TDengine超级表失败: {stable_name}, 错误: {e}")
            raise
    
    async def create_sub_table(
        self, 
        database: str, 
        stable_name: str, 
        table_name: str, 
        tags_value: Dict[str, Any], 
        if_not_exists: bool = True
    ) -> Dict[str, Any]:
        """创建子表"""
        try:
            connector = await self.get_connector()
            return await connector.create_sub_table(database, stable_name, table_name, tags_value, if_not_exists)
        except Exception as e:
            logger.error(f"创建TDengine子表失败: {table_name}, 错误: {e}")
            raise
    
    async def insert_data(self, database: str, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """插入数据"""
        try:
            connector = await self.get_connector()
            return await connector.insert_data(database, table_name, data)
        except Exception as e:
            logger.error(f"TDengine数据插入失败: {table_name}, 错误: {e}")
            raise
    
    async def get_databases(self) -> List[str]:
        """获取数据库列表"""
        try:
            result = await self.execute_query("SHOW DATABASES;")
            if result.get("data"):
                return [row[0] for row in result["data"]]
            return []
        except Exception as e:
            logger.error(f"获取TDengine数据库列表失败: {e}")
            return []
    
    async def get_tables(self, database: str) -> List[str]:
        """获取表列表"""
        try:
            result = await self.execute_query("SHOW TABLES;", database)
            if result.get("data"):
                return [row[0] for row in result["data"]]
            return []
        except Exception as e:
            logger.error(f"获取TDengine表列表失败: {e}")
            return []
    
    async def get_super_tables(self, database: str) -> List[str]:
        """获取超级表列表"""
        try:
            result = await self.execute_query("SHOW STABLES;", database)
            if result.get("data"):
                return [row[0] for row in result["data"]]
            return []
        except Exception as e:
            logger.error(f"获取TDengine超级表列表失败: {e}")
            return []
    
    async def get_table_schema(self, database: str, table_name: str) -> Dict[str, Any]:
        """获取表结构"""
        try:
            # 使用反引号包裹表名以支持特殊字符和区分大小写
            result = await self.execute_query(f"DESCRIBE `{table_name}`;", database)
            if result.get("data"):
                columns = []
                for row in result["data"]:
                    columns.append({
                        "name": row[0],
                        "type": row[1],
                        "length": row[2],
                        "note": row[3] if len(row) > 3 else ""
                    })
                return {
                    "table_name": table_name,
                    "database": database,
                    "columns": columns
                }
            return {}
        except Exception as e:
            logger.error(f"获取TDengine表结构失败: {table_name}, 错误: {e}")
            return {}
    
    async def get_statistics(self, database: Optional[str] = None) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            stats = {}
            
            # 数据库统计
            databases = await self.get_databases()
            stats["databases_count"] = len(databases)
            stats["databases"] = databases
            
            if database:
                # 表统计
                tables = await self.get_tables(database)
                super_tables = await self.get_super_tables(database)
                
                stats["current_database"] = database
                stats["tables_count"] = len(tables)
                stats["super_tables_count"] = len(super_tables)
                stats["tables"] = tables
                stats["super_tables"] = super_tables
            
            stats["timestamp"] = datetime.now().isoformat()
            return stats
            
        except Exception as e:
            logger.error(f"获取TDengine统计信息失败: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def close(self):
        """关闭连接"""
        if self._connector:
            await self._connector.close()
            self._connector = None


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
        results = {}
        
        # 获取所有配置的服务器
        server_names = tdengine_config_manager.list_servers()
        
        tasks = []
        for server_name in server_names:
            service = self.get_service(server_name)
            task = asyncio.create_task(service.health_check())
            tasks.append((server_name, task))
        
        for server_name, task in tasks:
            try:
                results[server_name] = await task
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