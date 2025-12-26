# -*- coding: utf-8 -*-
"""
TDengine管理API
提供TDengine服务器配置、健康检查和管理接口
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.core.tdengine_config import tdengine_config_manager, TDengineServerConfig
from app.services.tdengine_service import tdengine_service_manager
from app.log import logger

router = APIRouter(prefix="/api/tdengine", tags=["TDengine管理"])


class TDengineServerConfigRequest(BaseModel):
    """TDengine服务器配置请求模型"""
    host: str = Field(..., description="服务器地址")
    port: int = Field(default=6041, description="端口号")
    user: str = Field(default="root", description="用户名")
    password: str = Field(..., description="密码")
    database: str = Field(default="test_db", description="数据库名")
    timeout: int = Field(default=30, description="超时时间（秒）")
    is_external: bool = Field(default=True, description="是否为外部服务器")
    description: str = Field(default="", description="描述")


class TDengineQueryRequest(BaseModel):
    """TDengine查询请求模型"""
    sql: str = Field(..., description="SQL语句")
    database: Optional[str] = Field(None, description="数据库名")
    server_name: Optional[str] = Field(None, description="服务器名称")


@router.get("/servers", summary="获取所有TDengine服务器配置")
async def get_servers():
    """获取所有TDengine服务器配置"""
    try:
        servers = []
        for server_name in tdengine_config_manager.list_servers():
            server_info = tdengine_config_manager.get_server_info(server_name)
            servers.append(server_info)
        
        return {
            "success": True,
            "data": {
                "servers": servers,
                "default_server": tdengine_config_manager.default_server,
                "total": len(servers)
            }
        }
    except Exception as e:
        logger.error(f"获取TDengine服务器配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers/{server_name}", summary="获取指定TDengine服务器配置")
async def get_server(server_name: str):
    """获取指定TDengine服务器配置"""
    try:
        server_info = tdengine_config_manager.get_server_info(server_name)
        return {
            "success": True,
            "data": server_info
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取TDengine服务器配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/servers/{server_name}", summary="添加或更新TDengine服务器配置")
async def add_or_update_server(server_name: str, config: TDengineServerConfigRequest):
    """添加或更新TDengine服务器配置"""
    try:
        server_config = TDengineServerConfig(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=config.database,
            timeout=config.timeout,
            is_external=config.is_external,
            description=config.description
        )
        
        tdengine_config_manager.add_server(server_name, server_config)
        
        return {
            "success": True,
            "message": f"TDengine服务器配置 '{server_name}' 已保存",
            "data": tdengine_config_manager.get_server_info(server_name)
        }
    except Exception as e:
        logger.error(f"保存TDengine服务器配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/servers/{server_name}", summary="删除TDengine服务器配置")
async def delete_server(server_name: str):
    """删除TDengine服务器配置"""
    try:
        if server_name not in tdengine_config_manager.servers:
            raise HTTPException(status_code=404, detail=f"服务器 '{server_name}' 不存在")
        
        tdengine_config_manager.remove_server(server_name)
        
        return {
            "success": True,
            "message": f"TDengine服务器配置 '{server_name}' 已删除"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除TDengine服务器配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/servers/{server_name}/set-default", summary="设置默认TDengine服务器")
async def set_default_server(server_name: str):
    """设置默认TDengine服务器"""
    try:
        tdengine_config_manager.set_default_server(server_name)
        
        return {
            "success": True,
            "message": f"默认TDengine服务器已设置为 '{server_name}'"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"设置默认TDengine服务器失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="检查所有TDengine服务器健康状态")
async def health_check_all():
    """检查所有TDengine服务器健康状态"""
    try:
        health_results = await tdengine_service_manager.health_check_all()
        
        healthy_count = sum(1 for result in health_results.values() if result.get("status") == "healthy")
        total_count = len(health_results)
        
        return {
            "success": True,
            "data": {
                "servers": health_results,
                "summary": {
                    "total": total_count,
                    "healthy": healthy_count,
                    "unhealthy": total_count - healthy_count,
                    "overall_status": "healthy" if healthy_count == total_count else "partial" if healthy_count > 0 else "unhealthy"
                }
            }
        }
    except Exception as e:
        logger.error(f"TDengine健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/{server_name}", summary="检查指定TDengine服务器健康状态")
async def health_check_server(server_name: str):
    """检查指定TDengine服务器健康状态"""
    try:
        service = tdengine_service_manager.get_service(server_name)
        health_result = await service.health_check()
        
        return {
            "success": True,
            "data": health_result
        }
    except Exception as e:
        logger.error(f"TDengine服务器 {server_name} 健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-connection/{server_name}", summary="测试TDengine服务器连接")
async def test_connection(server_name: str):
    """测试TDengine服务器连接"""
    try:
        health_status = await tdengine_config_manager.test_connection(server_name)
        
        return {
            "success": True,
            "data": {
                "server_name": server_name,
                "is_healthy": health_status.is_healthy,
                "response_time_ms": health_status.response_time_ms,
                "server_version": health_status.server_version,
                "database_exists": health_status.database_exists,
                "error_message": health_status.error_message,
                "last_check": health_status.last_check.isoformat()
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"测试TDengine连接失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", summary="获取TDengine统计信息")
async def get_statistics(
    server_name: Optional[str] = Query(None, description="服务器名称"),
    database: Optional[str] = Query(None, description="数据库名称")
):
    """获取TDengine统计信息"""
    try:
        service = tdengine_service_manager.get_service(server_name)
        stats = await service.get_statistics(database)
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"获取TDengine统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/databases", summary="获取数据库列表")
async def get_databases(server_name: Optional[str] = Query(None, description="服务器名称")):
    """获取数据库列表"""
    try:
        service = tdengine_service_manager.get_service(server_name)
        databases = await service.get_databases()
        
        return {
            "success": True,
            "data": {
                "databases": databases,
                "count": len(databases)
            }
        }
    except Exception as e:
        logger.error(f"获取TDengine数据库列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/databases/{database}/tables", summary="获取表列表")
async def get_tables(
    database: str,
    server_name: Optional[str] = Query(None, description="服务器名称")
):
    """获取表列表"""
    try:
        service = tdengine_service_manager.get_service(server_name)
        tables = await service.get_tables(database)
        super_tables = await service.get_super_tables(database)
        
        return {
            "success": True,
            "data": {
                "database": database,
                "tables": tables,
                "super_tables": super_tables,
                "tables_count": len(tables),
                "super_tables_count": len(super_tables)
            }
        }
    except Exception as e:
        logger.error(f"获取TDengine表列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/databases/{database}/tables/{table_name}/schema", summary="获取表结构")
async def get_table_schema(
    database: str,
    table_name: str,
    server_name: Optional[str] = Query(None, description="服务器名称")
):
    """获取表结构"""
    try:
        service = tdengine_service_manager.get_service(server_name)
        schema = await service.get_table_schema(database, table_name)
        
        return {
            "success": True,
            "data": schema
        }
    except Exception as e:
        logger.error(f"获取TDengine表结构失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", summary="执行TDengine查询")
async def execute_query(query: TDengineQueryRequest):
    """执行TDengine查询"""
    try:
        service = tdengine_service_manager.get_service(query.server_name)
        result = await service.execute_query(query.sql, query.database)
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"执行TDengine查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/export", summary="导出TDengine配置")
async def export_config():
    """导出TDengine配置"""
    try:
        config_data = tdengine_config_manager.export_config()
        
        return {
            "success": True,
            "data": config_data
        }
    except Exception as e:
        logger.error(f"导出TDengine配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/import", summary="导入TDengine配置")
async def import_config(config_data: Dict[str, Any]):
    """导入TDengine配置"""
    try:
        tdengine_config_manager.import_config(config_data)
        
        return {
            "success": True,
            "message": "TDengine配置导入成功"
        }
    except Exception as e:
        logger.error(f"导入TDengine配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))