"""数据库连接管理模块

提供统一的数据库连接接口，支持PostgreSQL和其他数据库类型。
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

import asyncpg
from tortoise import Tortoise
from tortoise.connection import connections

from app.settings.config import settings
from app.core.unified_logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """数据库连接管理器"""
    
    def __init__(self):
        self._connection_pool: Optional[asyncpg.Pool] = None
        self._initialized = False
    
    async def initialize(self):
        """初始化数据库连接池"""
        if self._initialized:
            return
        
        try:
            # 初始化Tortoise ORM
            if not Tortoise._inited:
                await Tortoise.init(config=settings.tortoise_orm.model_dump())
                logger.info("Tortoise ORM 初始化成功")
            
            # 创建原生asyncpg连接池（用于高性能查询）
            postgres_creds = settings.tortoise_orm.connections.postgres.credentials
            self._connection_pool = await asyncpg.create_pool(
                host=postgres_creds.host,
                port=postgres_creds.port,
                user=postgres_creds.user,
                password=postgres_creds.password,
                database=postgres_creds.database,
                min_size=postgres_creds.minsize,
                max_size=postgres_creds.maxsize,
                command_timeout=postgres_creds.timeout,
                ssl='disable',
                server_settings={'client_encoding': 'utf8'}
            )
            
            self._initialized = True
            logger.info("数据库连接池初始化成功")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    async def close(self):
        """关闭数据库连接"""
        if self._connection_pool:
            await self._connection_pool.close()
            self._connection_pool = None
        
        if Tortoise._inited:
            await Tortoise.close_connections()
        
        self._initialized = False
        logger.info("数据库连接已关闭")
    
    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接（上下文管理器）
        
        Returns:
            asyncpg.Connection: 数据库连接对象
        """
        if not self._initialized:
            await self.initialize()
        
        if not self._connection_pool:
            raise RuntimeError("数据库连接池未初始化")
        
        async with self._connection_pool.acquire() as connection:
            try:
                yield connection
            except Exception as e:
                logger.error(f"数据库操作错误: {e}")
                raise
    
    async def get_tortoise_connection(self, connection_name: str = "default"):
        """获取Tortoise ORM连接
        
        Args:
            connection_name: 连接名称，默认为"default"
            
        Returns:
            Tortoise连接对象
        """
        if not self._initialized:
            await self.initialize()
        
        return connections.get(connection_name)
    
    async def execute_query(self, query: str, *args) -> list:
        """执行查询语句
        
        Args:
            query: SQL查询语句
            *args: 查询参数
            
        Returns:
            list: 查询结果
        """
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_command(self, command: str, *args) -> str:
        """执行命令语句（INSERT, UPDATE, DELETE等）
        
        Args:
            command: SQL命令语句
            *args: 命令参数
            
        Returns:
            str: 执行结果状态
        """
        async with self.get_connection() as conn:
            return await conn.execute(command, *args)
    
    async def execute_many(self, command: str, args_list: list) -> None:
        """批量执行命令
        
        Args:
            command: SQL命令语句
            args_list: 参数列表
        """
        async with self.get_connection() as conn:
            await conn.executemany(command, args_list)
    
    async def health_check(self) -> Dict[str, Any]:
        """数据库健康检查
        
        Returns:
            Dict[str, Any]: 健康检查结果
        """
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchval("SELECT version()")
                
                return {
                    "status": "healthy",
                    "database_version": result,
                    "connection_pool_size": self._connection_pool.get_size() if self._connection_pool else 0,
                    "connection_pool_free": self._connection_pool.get_idle_size() if self._connection_pool else 0
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# 全局数据库管理器实例
_db_manager = DatabaseManager()


async def get_database() -> DatabaseManager:
    """获取数据库管理器实例
    
    Returns:
        DatabaseManager: 数据库管理器
    """
    if not _db_manager._initialized:
        await _db_manager.initialize()
    return _db_manager


@asynccontextmanager
async def get_db_connection():
    """获取数据库连接（兼容性函数）
    
    这是为了兼容现有代码中使用的get_db_connection函数。
    
    Returns:
        asyncpg.Connection: 数据库连接对象
    """
    db_manager = await get_database()
    async with db_manager.get_connection() as conn:
        yield conn


async def initialize_database():
    """初始化数据库（应用启动时调用）"""
    await _db_manager.initialize()


async def close_database():
    """关闭数据库连接（应用关闭时调用）"""
    await _db_manager.close()


# 便捷函数
async def execute_query(query: str, *args) -> list:
    """执行查询语句的便捷函数"""
    db_manager = await get_database()
    return await db_manager.execute_query(query, *args)


async def execute_command(command: str, *args) -> str:
    """执行命令语句的便捷函数"""
    db_manager = await get_database()
    return await db_manager.execute_command(command, *args)


async def execute_many(command: str, args_list: list) -> None:
    """批量执行命令的便捷函数"""
    db_manager = await get_database()
    return await db_manager.execute_many(command, args_list)


__all__ = [
    'DatabaseManager',
    'get_database',
    'get_db_connection',
    'initialize_database',
    'close_database',
    'execute_query',
    'execute_command',
    'execute_many'
]