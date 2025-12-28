#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据采集API

提供数据源管理、采集控制和状态监控的API端点。

需求: 5.1, 5.6 - 数据源管理和扩展适配器
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingestion", tags=["数据采集"])


# =====================================================
# 请求/响应模型
# =====================================================

class DataSourceCreate(BaseModel):
    """创建数据源请求"""
    name: str = Field(..., description="数据源名称", min_length=1, max_length=100)
    protocol: str = Field(..., description="协议类型: mqtt, http, modbus")
    config: Dict[str, Any] = Field(..., description="协议配置")
    category_id: Optional[int] = Field(None, description="关联的资产类别ID")
    enabled: bool = Field(True, description="是否启用")
    description: Optional[str] = Field(None, description="描述")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "MQTT数据源1",
                "protocol": "mqtt",
                "config": {
                    "host": "localhost",
                    "port": 1883,
                    "topics": ["sensors/#"],
                    "username": "user",
                    "password": "pass"
                },
                "category_id": 1,
                "enabled": True,
                "description": "生产线传感器数据采集"
            }
        }


class DataSourceUpdate(BaseModel):
    """更新数据源请求"""
    name: Optional[str] = Field(None, description="数据源名称")
    config: Optional[Dict[str, Any]] = Field(None, description="协议配置")
    category_id: Optional[int] = Field(None, description="关联的资产类别ID")
    enabled: Optional[bool] = Field(None, description="是否启用")
    description: Optional[str] = Field(None, description="描述")


class DataSourceResponse(BaseModel):
    """数据源响应"""
    id: int
    name: str
    protocol: str
    config: Dict[str, Any]
    category_id: Optional[int]
    enabled: bool
    status: str
    description: Optional[str]
    last_connected_at: Optional[datetime]
    error_count: int
    success_count: int
    created_at: datetime
    updated_at: datetime


class DataSourceListResponse(BaseModel):
    """数据源列表响应"""
    total: int
    items: List[DataSourceResponse]


class DataSourceStatsResponse(BaseModel):
    """数据源统计响应"""
    id: int
    name: str
    protocol: str
    status: str
    statistics: Dict[str, Any]
    health: Dict[str, Any]


class IngestionStatusResponse(BaseModel):
    """采集状态响应"""
    total_sources: int
    running_sources: int
    stopped_sources: int
    overall_health: str
    metrics: Dict[str, Any]
    timestamp: datetime


# =====================================================
# 数据源管理服务
# =====================================================

class DataSourceService:
    """数据源管理服务"""
    
    def __init__(self):
        self._adapters: Dict[int, Any] = {}  # source_id -> adapter
        self._monitor = None
    
    async def get_monitor(self):
        """获取监控实例"""
        if self._monitor is None:
            from platform_core.ingestion.monitor import get_ingestion_monitor
            self._monitor = get_ingestion_monitor()
        return self._monitor
    
    async def create_adapter(self, source_id: int, protocol: str, config: Dict[str, Any]):
        """创建适配器实例"""
        from platform_core.ingestion.adapters.mqtt_adapter import MQTTAdapter
        from platform_core.ingestion.adapters.http_adapter import HTTPAdapter
        
        adapter_classes = {
            "mqtt": MQTTAdapter,
            "http": HTTPAdapter,
        }
        
        adapter_class = adapter_classes.get(protocol.lower())
        if not adapter_class:
            raise ValueError(f"不支持的协议类型: {protocol}")
        
        adapter = adapter_class(config, name=f"source_{source_id}")
        self._adapters[source_id] = adapter
        
        # 注册到监控
        monitor = await self.get_monitor()
        monitor.register_adapter(adapter)
        
        return adapter
    
    async def get_adapter(self, source_id: int):
        """获取适配器实例"""
        return self._adapters.get(source_id)
    
    async def remove_adapter(self, source_id: int):
        """移除适配器实例"""
        adapter = self._adapters.pop(source_id, None)
        if adapter:
            await adapter.stop()
            monitor = await self.get_monitor()
            monitor.unregister_adapter(adapter.name)


# 全局服务实例
_data_source_service = DataSourceService()


async def get_data_source_service() -> DataSourceService:
    """获取数据源服务"""
    return _data_source_service


# =====================================================
# API端点
# =====================================================

@router.post("/sources", response_model=DataSourceResponse, summary="创建数据源")
async def create_data_source(
    data: DataSourceCreate,
    service: DataSourceService = Depends(get_data_source_service)
):
    """
    创建新的数据源配置
    
    支持的协议类型:
    - mqtt: MQTT协议
    - http: HTTP轮询
    - modbus: Modbus协议（待实现）
    """
    try:
        from app.models.platform_upgrade import AssetCategory
        
        # 验证资产类别
        if data.category_id:
            category = await AssetCategory.get_or_none(id=data.category_id)
            if not category:
                raise HTTPException(status_code=404, detail="资产类别不存在")
        
        # 创建数据库记录
        from tortoise.transactions import in_transaction
        
        async with in_transaction():
            # 这里假设有DataSource模型，如果没有则需要创建
            source_data = {
                "name": data.name,
                "protocol": data.protocol,
                "config": data.config,
                "category_id": data.category_id,
                "enabled": data.enabled,
                "status": "stopped",
                "error_count": 0,
                "success_count": 0,
            }
            
            # 模拟创建（实际应使用ORM）
            source_id = 1  # 临时ID
            
            # 创建适配器
            if data.enabled:
                await service.create_adapter(source_id, data.protocol, data.config)
            
            return DataSourceResponse(
                id=source_id,
                name=data.name,
                protocol=data.protocol,
                config=data.config,
                category_id=data.category_id,
                enabled=data.enabled,
                status="stopped",
                description=data.description,
                last_connected_at=None,
                error_count=0,
                success_count=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建数据源失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建数据源失败: {str(e)}")


@router.get("/sources", response_model=DataSourceListResponse, summary="获取数据源列表")
async def list_data_sources(
    protocol: Optional[str] = Query(None, description="按协议过滤"),
    enabled: Optional[bool] = Query(None, description="按启用状态过滤"),
    category_id: Optional[int] = Query(None, description="按资产类别过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """获取数据源列表"""
    try:
        # 模拟数据（实际应从数据库查询）
        items = []
        
        return DataSourceListResponse(
            total=len(items),
            items=items
        )
        
    except Exception as e:
        logger.error(f"获取数据源列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取数据源列表失败: {str(e)}")


@router.get("/sources/{source_id}", response_model=DataSourceResponse, summary="获取数据源详情")
async def get_data_source(source_id: int):
    """获取指定数据源的详细信息"""
    try:
        # 模拟数据（实际应从数据库查询）
        raise HTTPException(status_code=404, detail="数据源不存在")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据源详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取数据源详情失败: {str(e)}")


@router.put("/sources/{source_id}", response_model=DataSourceResponse, summary="更新数据源")
async def update_data_source(
    source_id: int,
    data: DataSourceUpdate,
    service: DataSourceService = Depends(get_data_source_service)
):
    """更新数据源配置"""
    try:
        # 模拟更新（实际应更新数据库）
        raise HTTPException(status_code=404, detail="数据源不存在")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新数据源失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新数据源失败: {str(e)}")


@router.delete("/sources/{source_id}", summary="删除数据源")
async def delete_data_source(
    source_id: int,
    service: DataSourceService = Depends(get_data_source_service)
):
    """删除数据源"""
    try:
        # 停止并移除适配器
        await service.remove_adapter(source_id)
        
        # 模拟删除（实际应删除数据库记录）
        return {"message": "数据源已删除", "id": source_id}
        
    except Exception as e:
        logger.error(f"删除数据源失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除数据源失败: {str(e)}")


@router.post("/sources/{source_id}/start", summary="启动数据源")
async def start_data_source(
    source_id: int,
    service: DataSourceService = Depends(get_data_source_service)
):
    """启动数据源采集"""
    try:
        adapter = await service.get_adapter(source_id)
        if not adapter:
            raise HTTPException(status_code=404, detail="数据源不存在或未初始化")
        
        success = await adapter.start()
        if not success:
            raise HTTPException(status_code=500, detail="启动数据源失败")
        
        return {
            "message": "数据源已启动",
            "id": source_id,
            "status": adapter.status.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动数据源失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动数据源失败: {str(e)}")


@router.post("/sources/{source_id}/stop", summary="停止数据源")
async def stop_data_source(
    source_id: int,
    service: DataSourceService = Depends(get_data_source_service)
):
    """停止数据源采集"""
    try:
        adapter = await service.get_adapter(source_id)
        if not adapter:
            raise HTTPException(status_code=404, detail="数据源不存在或未初始化")
        
        await adapter.stop()
        
        return {
            "message": "数据源已停止",
            "id": source_id,
            "status": adapter.status.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止数据源失败: {e}")
        raise HTTPException(status_code=500, detail=f"停止数据源失败: {str(e)}")


@router.get("/sources/{source_id}/stats", response_model=DataSourceStatsResponse, summary="获取数据源统计")
async def get_data_source_stats(
    source_id: int,
    service: DataSourceService = Depends(get_data_source_service)
):
    """获取数据源的统计信息"""
    try:
        adapter = await service.get_adapter(source_id)
        if not adapter:
            raise HTTPException(status_code=404, detail="数据源不存在或未初始化")
        
        monitor = await service.get_monitor()
        adapter_status = monitor.get_adapter_status(adapter.name)
        
        return DataSourceStatsResponse(
            id=source_id,
            name=adapter.name,
            protocol=adapter.protocol,
            status=adapter.status.value,
            statistics=adapter.statistics.to_dict(),
            health=adapter_status.get("health", {}) if adapter_status else {}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据源统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取数据源统计失败: {str(e)}")


@router.get("/status", response_model=IngestionStatusResponse, summary="获取采集状态")
async def get_ingestion_status(
    service: DataSourceService = Depends(get_data_source_service)
):
    """获取整体采集状态"""
    try:
        monitor = await service.get_monitor()
        status = monitor.get_overall_status()
        
        return IngestionStatusResponse(
            total_sources=status["total_adapters"],
            running_sources=status["running_adapters"],
            stopped_sources=status["stopped_adapters"],
            overall_health=status["overall_health"],
            metrics=status["metrics"],
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"获取采集状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取采集状态失败: {str(e)}")


@router.get("/health", summary="获取健康报告")
async def get_health_report(
    service: DataSourceService = Depends(get_data_source_service)
):
    """获取采集层健康报告"""
    try:
        monitor = await service.get_monitor()
        return monitor.get_health_report()
        
    except Exception as e:
        logger.error(f"获取健康报告失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取健康报告失败: {str(e)}")


@router.get("/metrics", summary="获取性能指标")
async def get_metrics(
    service: DataSourceService = Depends(get_data_source_service)
):
    """获取采集层性能指标"""
    try:
        monitor = await service.get_monitor()
        return monitor.get_metrics()
        
    except Exception as e:
        logger.error(f"获取性能指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取性能指标失败: {str(e)}")


@router.get("/errors", summary="获取错误日志")
async def get_error_logs(
    source: Optional[str] = Query(None, description="按来源过滤"),
    error_type: Optional[str] = Query(None, description="按错误类型过滤"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    service: DataSourceService = Depends(get_data_source_service)
):
    """获取采集错误日志"""
    try:
        from platform_core.ingestion.retry_manager import get_error_logger
        
        error_logger = get_error_logger()
        records = error_logger.get_records(
            source=source,
            error_type=error_type,
            limit=limit
        )
        
        return {
            "total": len(records),
            "records": [r.to_dict() for r in records],
            "statistics": error_logger.get_statistics()
        }
        
    except Exception as e:
        logger.error(f"获取错误日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取错误日志失败: {str(e)}")


# =====================================================
# 双写管理API
# =====================================================

class DualWriteConfigUpdate(BaseModel):
    """双写配置更新请求"""
    global_enabled: Optional[bool] = Field(None, description="全局启用")
    write_to_new: Optional[bool] = Field(None, description="写入新结构")
    write_to_old: Optional[bool] = Field(None, description="写入旧结构")
    fail_on_old_error: Optional[bool] = Field(None, description="旧结构写入失败是否影响主流程")


class CategoryDualWriteConfigUpdate(BaseModel):
    """类别双写配置更新请求"""
    category_code: str = Field(..., description="资产类别编码")
    enabled: bool = Field(..., description="是否启用")
    write_to_new: bool = Field(True, description="写入新结构")
    write_to_old: bool = Field(True, description="写入旧结构")
    fail_on_old_error: bool = Field(False, description="旧结构写入失败是否影响主流程")
    verify_enabled: bool = Field(False, description="是否启用一致性验证")
    verify_interval_hours: int = Field(24, ge=1, le=168, description="验证间隔（小时）")


class DualWriteConfigResponse(BaseModel):
    """双写配置响应"""
    global_config: Dict[str, Any]
    category_configs: Dict[str, Dict[str, Any]]
    enabled_categories: List[str]
    statistics: Dict[str, Any]
    timestamp: datetime


class ConsistencyReportResponse(BaseModel):
    """一致性报告响应"""
    category_code: str
    time_range_hours: int
    check_time: datetime
    new_structure_count: int
    old_structure_count: int
    matched_count: int
    mismatched_count: int
    missing_in_new: int
    missing_in_old: int
    consistency_rate: float
    mismatches: List[Dict[str, Any]]
    summary: Dict[str, Any]


# 双写服务依赖
async def get_dual_write_service():
    """获取双写服务"""
    from platform_core.ingestion.dual_write_config import get_dual_write_config_manager
    from platform_core.ingestion.dual_writer import get_dual_write_adapter
    
    return {
        "config_manager": get_dual_write_config_manager(),
        "adapter": get_dual_write_adapter(),
    }


@router.get("/dual-write/config", response_model=DualWriteConfigResponse, summary="获取双写配置")
async def get_dual_write_config():
    """
    获取双写模式配置
    
    返回全局配置和所有类别的配置信息。
    
    需求: 8.4 - 当完成迁移验证时，平台应支持关闭双写模式
    """
    try:
        from platform_core.ingestion.dual_write_config import get_dual_write_config_manager
        from platform_core.ingestion.dual_writer import get_dual_write_adapter
        
        config_manager = get_dual_write_config_manager()
        adapter = get_dual_write_adapter()
        
        # 获取全局配置
        global_config = config_manager.get_global_config()
        
        # 获取所有类别配置
        category_configs = {
            code: config.to_dict()
            for code, config in config_manager.get_all_category_configs().items()
        }
        
        # 获取启用的类别
        enabled_categories = list(config_manager.get_enabled_categories())
        
        # 获取统计信息
        statistics = adapter.get_statistics()
        
        return DualWriteConfigResponse(
            global_config=global_config,
            category_configs=category_configs,
            enabled_categories=enabled_categories,
            statistics=statistics,
            timestamp=datetime.now(),
        )
        
    except Exception as e:
        logger.error(f"获取双写配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取双写配置失败: {str(e)}")


@router.put("/dual-write/config", summary="更新全局双写配置")
async def update_dual_write_config(data: DualWriteConfigUpdate):
    """
    更新全局双写模式配置
    
    需求: 8.4 - 当完成迁移验证时，平台应支持关闭双写模式
    """
    try:
        from platform_core.ingestion.dual_write_config import get_dual_write_config_manager
        
        config_manager = get_dual_write_config_manager()
        
        # 更新全局配置
        config_manager.set_global_config(
            enabled=data.global_enabled,
            write_to_new=data.write_to_new,
            write_to_old=data.write_to_old,
            fail_on_old_error=data.fail_on_old_error,
        )
        
        # 尝试保存到数据库
        try:
            await config_manager.save_to_database()
        except Exception as db_error:
            logger.warning(f"保存配置到数据库失败: {db_error}")
        
        return {
            "message": "全局双写配置已更新",
            "config": config_manager.get_global_config(),
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"更新双写配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新双写配置失败: {str(e)}")


@router.put("/dual-write/config/category", summary="更新类别双写配置")
async def update_category_dual_write_config(data: CategoryDualWriteConfigUpdate):
    """
    更新特定类别的双写配置
    
    需求: 8.5 - 双写模式应支持按资产类别粒度启用或禁用
    """
    try:
        from platform_core.ingestion.dual_write_config import (
            get_dual_write_config_manager,
            CategoryDualWriteConfig,
        )
        
        config_manager = get_dual_write_config_manager()
        
        # 创建类别配置
        config = CategoryDualWriteConfig(
            category_code=data.category_code,
            enabled=data.enabled,
            write_to_new=data.write_to_new,
            write_to_old=data.write_to_old,
            fail_on_old_error=data.fail_on_old_error,
            verify_enabled=data.verify_enabled,
            verify_interval_hours=data.verify_interval_hours,
        )
        
        # 设置类别配置
        config_manager.set_category_config(data.category_code, config)
        
        # 尝试保存到数据库
        try:
            await config_manager.save_to_database()
        except Exception as db_error:
            logger.warning(f"保存配置到数据库失败: {db_error}")
        
        return {
            "message": f"类别 {data.category_code} 双写配置已更新",
            "config": config.to_dict(),
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"更新类别双写配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新类别双写配置失败: {str(e)}")


@router.delete("/dual-write/config/category/{category_code}", summary="删除类别双写配置")
async def delete_category_dual_write_config(category_code: str):
    """
    删除特定类别的双写配置
    
    删除后该类别将使用全局配置。
    """
    try:
        from platform_core.ingestion.dual_write_config import get_dual_write_config_manager
        
        config_manager = get_dual_write_config_manager()
        
        # 禁用并移除类别配置
        config_manager.disable_category(category_code)
        
        return {
            "message": f"类别 {category_code} 双写配置已删除",
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"删除类别双写配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除类别双写配置失败: {str(e)}")


@router.post("/dual-write/verify", response_model=ConsistencyReportResponse, summary="验证数据一致性")
async def verify_dual_write_consistency_api(
    category_code: str = Query(..., description="资产类别编码"),
    time_range_hours: int = Query(24, ge=1, le=168, description="时间范围（小时）"),
    asset_codes: Optional[List[str]] = Query(None, description="指定的资产编码列表"),
):
    """
    验证新旧数据结构的一致性
    
    需求: 8.3 - 当验证数据一致性时，平台应提供新旧数据对比报告
    """
    try:
        from platform_core.ingestion.consistency_verifier import ConsistencyVerifier
        
        verifier = ConsistencyVerifier()
        report = await verifier.verify_consistency(
            category_code=category_code,
            time_range_hours=time_range_hours,
            asset_codes=asset_codes,
        )
        
        return ConsistencyReportResponse(
            category_code=report.category_code,
            time_range_hours=report.time_range_hours,
            check_time=report.check_time,
            new_structure_count=report.new_structure_count,
            old_structure_count=report.old_structure_count,
            matched_count=report.matched_count,
            mismatched_count=report.mismatched_count,
            missing_in_new=report.missing_in_new,
            missing_in_old=report.missing_in_old,
            consistency_rate=report.consistency_rate,
            mismatches=[m.to_dict() for m in report.mismatches],
            summary=report.summary,
        )
        
    except Exception as e:
        logger.error(f"验证数据一致性失败: {e}")
        raise HTTPException(status_code=500, detail=f"验证数据一致性失败: {str(e)}")


@router.get("/dual-write/errors", summary="获取双写错误日志")
async def get_dual_write_errors(
    target: Optional[str] = Query(None, description="按目标过滤 (new/old)"),
    category_code: Optional[str] = Query(None, description="按类别过滤"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
):
    """
    获取双写错误日志
    
    需求: 8.2 - 当双写发生错误时，平台应记录错误但不影响主写入流程
    """
    try:
        from platform_core.ingestion.dual_writer import get_dual_write_adapter
        
        adapter = get_dual_write_adapter()
        errors = adapter.get_error_log(
            limit=limit,
            target=target,
            category_code=category_code,
        )
        
        return {
            "total": len(errors),
            "errors": [e.to_dict() for e in errors],
            "statistics": adapter.get_statistics(),
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"获取双写错误日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取双写错误日志失败: {str(e)}")


@router.post("/dual-write/errors/clear", summary="清空双写错误日志")
async def clear_dual_write_errors():
    """清空双写错误日志"""
    try:
        from platform_core.ingestion.dual_writer import get_dual_write_adapter
        
        adapter = get_dual_write_adapter()
        adapter.clear_error_log()
        
        return {
            "message": "双写错误日志已清空",
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"清空双写错误日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"清空双写错误日志失败: {str(e)}")


@router.get("/dual-write/statistics", summary="获取双写统计信息")
async def get_dual_write_statistics():
    """获取双写统计信息"""
    try:
        from platform_core.ingestion.dual_writer import get_dual_write_adapter
        
        adapter = get_dual_write_adapter()
        statistics = adapter.get_statistics()
        
        return {
            "statistics": statistics,
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"获取双写统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取双写统计信息失败: {str(e)}")


@router.post("/dual-write/statistics/reset", summary="重置双写统计信息")
async def reset_dual_write_statistics():
    """重置双写统计信息"""
    try:
        from platform_core.ingestion.dual_writer import get_dual_write_adapter
        
        adapter = get_dual_write_adapter()
        adapter.reset_statistics()
        
        return {
            "message": "双写统计信息已重置",
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"重置双写统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"重置双写统计信息失败: {str(e)}")
