import httpx
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from app.log import logger
from app.core.tdengine_config import tdengine_config_manager, TDengineServerConfig


class TDengineConnector:
    def __init__(self, host: str = None, port: int = None, user: str = None, password: str = None, database: str = None, server_name: str = None):
        """
        初始化TDengine连接器
        
        Args:
            host: TDengine主机地址 (可选，如果提供server_name则忽略)
            port: TDengine端口 (可选)
            user: 用户名 (可选)
            password: 密码 (可选)
            database: 数据库名 (可选)
            server_name: 配置管理器中的服务器名称 (可选，优先使用)
        """
        if server_name:
            # 使用配置管理器中的服务器配置
            config = tdengine_config_manager.get_server_config(server_name)
            self.base_url = f"http://{config.host}:{config.port}"
            self.auth = (config.user, config.password)
            self.database = database or config.database
            self.server_name = server_name
            self.timeout = config.timeout
        else:
            # 使用直接传入的参数
            if not host:
                # 如果没有提供参数，使用默认服务器配置
                config = tdengine_config_manager.get_server_config()
                self.base_url = f"http://{config.host}:{config.port}"
                self.auth = (config.user, config.password)
                self.database = database or config.database
                self.server_name = tdengine_config_manager.default_server
                self.timeout = config.timeout
            else:
                # 使用传入的参数
                self.base_url = f"http://{host}:{port or 6041}"
                self.auth = (user or "root", password or "taosdata")
                self.database = database or "test_db"
                self.server_name = None
                self.timeout = 30
        
        # 显式禁用环境代理以提高初始化速度
        self._connection_pool = httpx.AsyncClient(timeout=self.timeout, trust_env=False)  # Use a single client for connection pooling

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(httpx.RequestError) | retry_if_exception_type(httpx.HTTPStatusError),
        reraise=True,
    )
    async def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        try:
            response = await self._connection_pool.request(method, url, auth=self.auth, **kwargs)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"An error occurred while requesting {e.request.url!r}: {e}")
            raise

    async def execute_sql(self, sql: str, target_db: str = None):
        db_to_use = target_db or self.database

        # 判断是查询语句还是执行语句
        is_query = sql.strip().upper().startswith("SELECT") or sql.strip().upper().startswith("DESCRIBE")

        if is_query:
            # SELECT 和 DESCRIBE 查询使用 /rest/sql/{db} 端点
            if not db_to_use:
                raise ValueError("Database must be specified for query operations")
            path = f"/rest/sql/{db_to_use}"
            # 查询语句不需要 'USE db;' 前缀
            final_sql = sql
        else:
            # 其他语句 (CREATE, INSERT, etc.) 使用 /rest/sql 端点
            path = "/rest/sql"
            # 如果没有在SQL中指定数据库，则添加 'USE db;'
            if db_to_use and not any(db_cmd in sql.upper() for db_cmd in ["USE ", db_to_use.upper() + "."]):
                final_sql = f"USE {db_to_use}; {sql}"
            else:
                final_sql = sql

        logger.info(f"Executing SQL: {final_sql} on path {path}")
        return await self._request("POST", path, data=final_sql)

    async def create_database(self, db_name: str, if_not_exists: bool = True):
        sql = f"CREATE DATABASE {'IF NOT EXISTS ' if if_not_exists else ''}{db_name}"
        logger.info(f"Creating database: {db_name}")
        return await self.execute_sql(sql, target_db=db_name)

    async def create_super_table(
        self, db_name: str, st_name: str, columns: dict, tags: dict, if_not_exists: bool = True
    ):
        cols_str = ", ".join([f"{col_name} {col_type}" for col_name, col_type in columns.items()])
        tags_str = ", ".join([f"{tag_name} {tag_type}" for tag_name, tag_type in tags.items()])
        sql = f"CREATE STABLE {'IF NOT EXISTS ' if if_not_exists else ''}{db_name}.{st_name} ({cols_str}) TAGS ({tags_str})"
        logger.info(f"Creating super table: {st_name} in database {db_name}")
        return await self.execute_sql(sql, target_db=db_name)

    async def create_sub_table(
        self, db_name: str, st_name: str, tb_name: str, tags_value: dict, if_not_exists: bool = True
    ):
        tags_value_str = ", ".join(
            [f"'{value}'" if isinstance(value, str) else str(value) for value in tags_value.values()]
        )
        sql = f"CREATE TABLE {'IF NOT EXISTS ' if if_not_exists else ''}{db_name}.{tb_name} USING {db_name}.{st_name} TAGS ({tags_value_str})"
        logger.info(f"Creating sub table: {tb_name} using super table {st_name} in database {db_name}")
        return await self.execute_sql(sql, target_db=db_name)

    async def insert_data(self, db_name: str, tb_name: str, data: dict):
        columns = ", ".join(data.keys())
        values = ", ".join([f"'{value}'" if isinstance(value, str) else str(value) for value in data.values()])
        sql = f"INSERT INTO {db_name}.{tb_name} ({columns}) VALUES ({values})"
        logger.info(f"Inserting data into table: {tb_name} in database {db_name}")
        return await self.execute_sql(sql, target_db=db_name)

    async def query_data(self, sql: str, db_name: str = None):
        logger.info(f"Querying data: {sql} on database {db_name if db_name else self.database}")
        return await self.execute_sql(sql, target_db=db_name)

    async def health_check(self) -> dict:
        """执行健康检查"""
        try:
            if self.server_name:
                # 使用配置管理器进行健康检查
                health_status = await tdengine_config_manager.test_connection(self.server_name)
                return {
                    "status": "healthy" if health_status.is_healthy else "unhealthy",
                    "response_time_ms": health_status.response_time_ms,
                    "server_version": health_status.server_version,
                    "database_exists": health_status.database_exists,
                    "error_message": health_status.error_message,
                    "last_check": health_status.last_check.isoformat()
                }
            else:
                # 直接测试连接
                result = await self.execute_sql("SHOW DATABASES;")
                return {
                    "status": "healthy",
                    "message": "Connection successful",
                    "databases_count": len(result.get("data", []))
                }
        except Exception as e:
            logger.error(f"TDengine健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def get_server_info(self) -> dict:
        """获取服务器信息"""
        if self.server_name:
            return tdengine_config_manager.get_server_info(self.server_name)
        else:
            return {
                "host": self.base_url,
                "database": self.database,
                "is_external": True,
                "description": "直接连接的TDengine服务器"
            }

    async def close(self):
        await self._connection_pool.aclose()
