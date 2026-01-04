"""
TDengine客户端封装

提供TDengine数据库的统一操作接口。

迁移说明:
- 从 platform_v2.timeseries.tdengine_client 迁移到 platform_core.timeseries.tdengine_client
- 保持所有API接口不变
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TDengineClient:
    """
    TDengine客户端封装
    
    提供TDengine数据库的连接管理和操作接口。
    """
    
    def __init__(self, server_name: Optional[str] = None):
        """
        初始化TDengine客户端
        
        Args:
            server_name: 服务器名称，如果为None则使用默认服务器
        """
        self.server_name = server_name
        self._connector = None
    
    async def get_connector(self):
        """获取TDengine连接器"""
        if self._connector is None:
            from app.core.tdengine_connector import TDengineConnector
            self._connector = TDengineConnector(server_name=self.server_name)
        return self._connector
    
    async def execute(self, sql: str, database: Optional[str] = None) -> Dict[str, Any]:
        """
        执行SQL语句
        
        Args:
            sql: SQL语句
            database: 数据库名
            
        Returns:
            Dict: 执行结果
        """
        connector = await self.get_connector()
        return await connector.execute_sql(sql, database)
    
    async def query(self, sql: str, database: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        执行查询
        
        Args:
            sql: SQL查询语句
            database: 数据库名
            
        Returns:
            List[Dict]: 查询结果
        """
        connector = await self.get_connector()
        result = await connector.query_data(sql, database)
        return result.get("data", [])
    
    async def health_check(self) -> Dict[str, Any]:
        """
        执行健康检查
        
        Returns:
            Dict: 健康检查结果
        """
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
    
    async def create_database(
        self,
        database_name: str,
        if_not_exists: bool = True
    ) -> Dict[str, Any]:
        """
        创建数据库
        
        Args:
            database_name: 数据库名
            if_not_exists: 是否使用IF NOT EXISTS
            
        Returns:
            Dict: 执行结果
        """
        connector = await self.get_connector()
        return await connector.create_database(database_name, if_not_exists)
    
    async def create_super_table(
        self,
        database: str,
        stable_name: str,
        columns: Dict[str, str],
        tags: Dict[str, str],
        if_not_exists: bool = True
    ) -> Dict[str, Any]:
        """
        创建超级表
        
        Args:
            database: 数据库名
            stable_name: 超级表名
            columns: 列定义 {列名: 类型}
            tags: TAG定义 {TAG名: 类型}
            if_not_exists: 是否使用IF NOT EXISTS
            
        Returns:
            Dict: 执行结果
        """
        connector = await self.get_connector()
        return await connector.create_super_table(
            database, stable_name, columns, tags, if_not_exists
        )
    
    async def create_sub_table(
        self,
        database: str,
        stable_name: str,
        table_name: str,
        tags_value: Dict[str, Any],
        if_not_exists: bool = True
    ) -> Dict[str, Any]:
        """
        创建子表
        
        Args:
            database: 数据库名
            stable_name: 超级表名
            table_name: 子表名
            tags_value: TAG值
            if_not_exists: 是否使用IF NOT EXISTS
            
        Returns:
            Dict: 执行结果
        """
        connector = await self.get_connector()
        return await connector.create_sub_table(
            database, stable_name, table_name, tags_value, if_not_exists
        )
    
    async def insert_data(
        self,
        database: str,
        table_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        插入数据
        
        Args:
            database: 数据库名
            table_name: 表名
            data: 数据
            
        Returns:
            Dict: 执行结果
        """
        connector = await self.get_connector()
        return await connector.insert_data(database, table_name, data)
    
    async def get_databases(self) -> List[str]:
        """
        获取数据库列表
        
        Returns:
            List[str]: 数据库名列表
        """
        result = await self.query("SHOW DATABASES;")
        return [row[0] for row in result] if result else []
    
    async def get_tables(self, database: str) -> List[str]:
        """
        获取表列表
        
        Args:
            database: 数据库名
            
        Returns:
            List[str]: 表名列表
        """
        result = await self.query("SHOW TABLES;", database)
        return [row[0] for row in result] if result else []
    
    async def get_super_tables(self, database: str) -> List[str]:
        """
        获取超级表列表
        
        Args:
            database: 数据库名
            
        Returns:
            List[str]: 超级表名列表
        """
        result = await self.query("SHOW STABLES;", database)
        return [row[0] for row in result] if result else []
    
    async def describe_table(self, database: str, table_name: str) -> List[Dict[str, Any]]:
        """
        获取表结构
        
        Args:
            database: 数据库名
            table_name: 表名
            
        Returns:
            List[Dict]: 列信息列表
        """
        result = await self.query(f"DESCRIBE `{table_name}`;", database)
        if not result:
            return []
        
        return [
            {
                "name": row[0],
                "type": row[1],
                "length": row[2],
                "note": row[3] if len(row) > 3 else ""
            }
            for row in result
        ]
    
    async def close(self):
        """关闭连接"""
        if self._connector:
            await self._connector.close()
            self._connector = None


# 全局默认客户端
_default_client: Optional[TDengineClient] = None


def get_tdengine_client(server_name: Optional[str] = None) -> TDengineClient:
    """
    获取TDengine客户端实例
    
    Args:
        server_name: 服务器名称
        
    Returns:
        TDengineClient: 客户端实例
    """
    global _default_client
    
    if server_name:
        return TDengineClient(server_name)
    
    if _default_client is None:
        _default_client = TDengineClient()
    
    return _default_client
