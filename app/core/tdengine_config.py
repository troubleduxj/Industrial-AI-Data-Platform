# -*- coding: utf-8 -*-
"""
TDengine配置管理类
支持外部TDengine服务器连接、健康检查和配置管理
"""

import asyncio
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import httpx
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from app.log import logger


@dataclass
class TDengineServerConfig:
    """TDengine服务器配置"""
    host: str
    port: int = 6041
    user: str = "root"
    password: str = "taosdata"
    database: str = "test_db"
    timeout: int = 30
    max_retries: int = 3
    connection_pool_size: int = 10
    is_external: bool = True
    description: str = ""
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class TDengineHealthStatus:
    """TDengine健康状态"""
    is_healthy: bool
    response_time_ms: float
    last_check: datetime
    error_message: Optional[str] = None
    server_version: Optional[str] = None
    database_exists: bool = False
    connection_count: int = 0


class TDengineConfigManager:
    """TDengine配置管理器"""
    
    def __init__(self):
        self.servers: Dict[str, TDengineServerConfig] = {}
        self.health_status: Dict[str, TDengineHealthStatus] = {}
        self.default_server: Optional[str] = None
        self._load_from_env()
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        # 主TDengine服务器配置
        main_config = TDengineServerConfig(
            host=os.getenv("TDENGINE_HOST", "localhost"),
            port=int(os.getenv("TDENGINE_PORT", "6041")),
            user=os.getenv("TDENGINE_USER", "root"),
            password=os.getenv("TDENGINE_PASSWORD", "taosdata"),
            database=os.getenv("TDENGINE_DATABASE", "test_db"),
            timeout=int(os.getenv("TDENGINE_TIMEOUT", "30")),
            max_retries=int(os.getenv("TDENGINE_MAX_RETRIES", "3")),
            is_external=os.getenv("TDENGINE_EXTERNAL", "false").lower() == "true",
            description="主TDengine服务器"
        )
        
        self.add_server("main", main_config)
        self.set_default_server("main")
        
        # 支持多个TDengine服务器配置
        # 格式: TDENGINE_SERVERS_<NAME>_HOST, TDENGINE_SERVERS_<NAME>_PORT, etc.
        server_names = set()
        for key in os.environ:
            if key.startswith("TDENGINE_SERVERS_") and key.endswith("_HOST"):
                server_name = key.replace("TDENGINE_SERVERS_", "").replace("_HOST", "").lower()
                server_names.add(server_name)
        
        for server_name in server_names:
            prefix = f"TDENGINE_SERVERS_{server_name.upper()}_"
            server_config = TDengineServerConfig(
                host=os.getenv(f"{prefix}HOST"),
                port=int(os.getenv(f"{prefix}PORT", "6041")),
                user=os.getenv(f"{prefix}USER", "root"),
                password=os.getenv(f"{prefix}PASSWORD", "taosdata"),
                database=os.getenv(f"{prefix}DATABASE", "test_db"),
                timeout=int(os.getenv(f"{prefix}TIMEOUT", "30")),
                is_external=os.getenv(f"{prefix}EXTERNAL", "true").lower() == "true",
                description=os.getenv(f"{prefix}DESCRIPTION", f"TDengine服务器 - {server_name}")
            )
            self.add_server(server_name, server_config)
    
    def add_server(self, name: str, config: TDengineServerConfig):
        """添加TDengine服务器配置"""
        self.servers[name] = config
        logger.info(f"添加TDengine服务器配置: {name} -> {config.host}:{config.port}")
    
    def remove_server(self, name: str):
        """移除TDengine服务器配置"""
        if name in self.servers:
            del self.servers[name]
            if name in self.health_status:
                del self.health_status[name]
            if self.default_server == name:
                self.default_server = next(iter(self.servers.keys()), None)
            logger.info(f"移除TDengine服务器配置: {name}")
    
    def set_default_server(self, name: str):
        """设置默认服务器"""
        if name in self.servers:
            self.default_server = name
            logger.info(f"设置默认TDengine服务器: {name}")
        else:
            raise ValueError(f"服务器 '{name}' 不存在")
    
    def get_server_config(self, name: Optional[str] = None) -> TDengineServerConfig:
        """获取服务器配置"""
        server_name = name or self.default_server
        if not server_name or server_name not in self.servers:
            raise ValueError(f"服务器 '{server_name}' 不存在")
        return self.servers[server_name]
    
    def list_servers(self) -> List[str]:
        """列出所有服务器名称"""
        return list(self.servers.keys())
    
    def get_server_info(self, name: Optional[str] = None) -> Dict[str, Any]:
        """获取服务器详细信息"""
        server_name = name or self.default_server
        config = self.get_server_config(server_name)
        health = self.health_status.get(server_name)
        
        return {
            "name": server_name,
            "host": config.host,
            "port": config.port,
            "database": config.database,
            "is_external": config.is_external,
            "description": config.description,
            "is_default": server_name == self.default_server,
            "health_status": {
                "is_healthy": health.is_healthy if health else None,
                "response_time_ms": health.response_time_ms if health else None,
                "last_check": health.last_check.isoformat() if health and health.last_check else None,
                "error_message": health.error_message if health else None,
                "server_version": health.server_version if health else None,
                "database_exists": health.database_exists if health else None,
            } if health else None
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(httpx.RequestError),
        reraise=True,
    )
    async def test_connection(self, name: Optional[str] = None) -> TDengineHealthStatus:
        """测试TDengine连接"""
        server_name = name or self.default_server
        config = self.get_server_config(server_name)
        
        start_time = datetime.now()
        
        try:
            base_url = f"http://{config.host}:{config.port}"
            auth = (config.user, config.password)
            
            async with httpx.AsyncClient(timeout=config.timeout) as client:
                # 测试基本连接
                response = await client.post(
                    f"{base_url}/rest/sql",
                    data="SHOW DATABASES;",
                    auth=auth
                )
                response.raise_for_status()
                
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                result = response.json()
                
                # 检查服务器版本
                server_version = None
                try:
                    version_response = await client.post(
                        f"{base_url}/rest/sql",
                        data="SELECT SERVER_VERSION();",
                        auth=auth
                    )
                    if version_response.status_code == 200:
                        version_data = version_response.json()
                        if version_data.get("data") and len(version_data["data"]) > 0:
                            server_version = version_data["data"][0][0]
                except Exception as e:
                    logger.warning(f"无法获取TDengine服务器版本: {e}")
                
                # 检查数据库是否存在
                database_exists = False
                if result.get("data"):
                    databases = [row[0] for row in result["data"]]
                    database_exists = config.database in databases
                
                # 如果数据库不存在，尝试创建
                if not database_exists:
                    try:
                        create_response = await client.post(
                            f"{base_url}/rest/sql",
                            data=f"CREATE DATABASE IF NOT EXISTS {config.database};",
                            auth=auth
                        )
                        if create_response.status_code == 200:
                            database_exists = True
                            logger.info(f"成功创建数据库: {config.database}")
                    except Exception as e:
                        logger.warning(f"无法创建数据库 {config.database}: {e}")
                
                health_status = TDengineHealthStatus(
                    is_healthy=True,
                    response_time_ms=response_time,
                    last_check=datetime.now(),
                    server_version=server_version,
                    database_exists=database_exists,
                    connection_count=1
                )
                
                self.health_status[server_name] = health_status
                logger.info(f"TDengine服务器 {server_name} 连接测试成功: {response_time:.2f}ms")
                
                return health_status
                
        except Exception as e:
            error_message = str(e)
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            health_status = TDengineHealthStatus(
                is_healthy=False,
                response_time_ms=response_time,
                last_check=datetime.now(),
                error_message=error_message
            )
            
            self.health_status[server_name] = health_status
            logger.error(f"TDengine服务器 {server_name} 连接测试失败: {error_message}")
            
            return health_status
    
    async def health_check_all(self) -> Dict[str, TDengineHealthStatus]:
        """对所有服务器进行健康检查"""
        tasks = []
        for server_name in self.servers.keys():
            task = asyncio.create_task(self.test_connection(server_name))
            tasks.append((server_name, task))
        
        results = {}
        for server_name, task in tasks:
            try:
                results[server_name] = await task
            except Exception as e:
                logger.error(f"健康检查失败 {server_name}: {e}")
                results[server_name] = TDengineHealthStatus(
                    is_healthy=False,
                    response_time_ms=0,
                    last_check=datetime.now(),
                    error_message=str(e)
                )
        
        return results
    
    async def get_server_stats(self, name: Optional[str] = None) -> Dict[str, Any]:
        """获取服务器统计信息"""
        server_name = name or self.default_server
        config = self.get_server_config(server_name)
        
        try:
            base_url = f"http://{config.host}:{config.port}"
            auth = (config.user, config.password)
            
            async with httpx.AsyncClient(timeout=config.timeout) as client:
                # 获取数据库信息
                db_response = await client.post(
                    f"{base_url}/rest/sql",
                    data="SHOW DATABASES;",
                    auth=auth
                )
                db_response.raise_for_status()
                db_result = db_response.json()
                
                # 获取表信息
                tables_response = await client.post(
                    f"{base_url}/rest/sql/{config.database}",
                    data="SHOW TABLES;",
                    auth=auth
                )
                tables_count = 0
                if tables_response.status_code == 200:
                    tables_result = tables_response.json()
                    tables_count = len(tables_result.get("data", []))
                
                # 获取超级表信息
                stables_response = await client.post(
                    f"{base_url}/rest/sql/{config.database}",
                    data="SHOW STABLES;",
                    auth=auth
                )
                stables_count = 0
                if stables_response.status_code == 200:
                    stables_result = stables_response.json()
                    stables_count = len(stables_result.get("data", []))
                
                return {
                    "server_name": server_name,
                    "databases_count": len(db_result.get("data", [])),
                    "tables_count": tables_count,
                    "stables_count": stables_count,
                    "current_database": config.database,
                    "last_updated": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"获取服务器统计信息失败 {server_name}: {e}")
            return {
                "server_name": server_name,
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }
    
    def export_config(self) -> Dict[str, Any]:
        """导出配置"""
        return {
            "servers": {
                name: {
                    "host": config.host,
                    "port": config.port,
                    "user": config.user,
                    "database": config.database,
                    "timeout": config.timeout,
                    "is_external": config.is_external,
                    "description": config.description,
                    "tags": config.tags
                }
                for name, config in self.servers.items()
            },
            "default_server": self.default_server,
            "export_time": datetime.now().isoformat()
        }
    
    def import_config(self, config_data: Dict[str, Any]):
        """导入配置"""
        if "servers" in config_data:
            for name, server_data in config_data["servers"].items():
                server_config = TDengineServerConfig(
                    host=server_data["host"],
                    port=server_data.get("port", 6041),
                    user=server_data.get("user", "root"),
                    password=server_data.get("password", "taosdata"),
                    database=server_data.get("database", "test_db"),
                    timeout=server_data.get("timeout", 30),
                    is_external=server_data.get("is_external", True),
                    description=server_data.get("description", ""),
                    tags=server_data.get("tags", {})
                )
                self.add_server(name, server_config)
        
        if "default_server" in config_data:
            self.set_default_server(config_data["default_server"])


# 全局配置管理器实例
tdengine_config_manager = TDengineConfigManager()