# -*- coding: utf-8 -*-
"""
数据迁移管理API
提供迁移状态查询、执行和回滚功能
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from loguru import logger

router = APIRouter(prefix="/migration", tags=["数据迁移"])


# =====================================================
# 请求/响应模型
# =====================================================

class MigrationStatusResponse(BaseModel):
    """迁移状态响应"""
    success: bool
    message: str
    data: Dict[str, Any]
    timestamp: str


class MigrationExecuteRequest(BaseModel):
    """迁移执行请求"""
    migration_type: str  # full/device_types/device_fields/devices
    dry_run: bool = False


class MigrationExecuteResponse(BaseModel):
    """迁移执行响应"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str


class RollbackRequest(BaseModel):
    """回滚请求"""
    migration_type: str  # device_type/device_field/device_info


class ArchitectureSwitchRequest(BaseModel):
    """架构切换请求"""
    enable_new_architecture: bool
    enable_dual_write: bool = True


# =====================================================
# API端点
# =====================================================

@router.get("/status", response_model=MigrationStatusResponse)
async def get_migration_status():
    """
    获取迁移状态
    
    返回当前迁移状态、数据统计和架构配置
    """
    try:
        from app.services.migration_engine import architecture_manager
        
        status = await architecture_manager.get_migration_status()
        
        return MigrationStatusResponse(
            success=True,
            message="获取迁移状态成功",
            data=status,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"获取迁移状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/records")
async def get_migration_records(
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None
):
    """
    获取迁移记录列表
    
    Args:
        limit: 返回数量限制
        offset: 偏移量
        status: 状态过滤
    """
    try:
        from app.models.platform_upgrade import MigrationRecord
        
        query = MigrationRecord.all()
        
        if status:
            query = query.filter(status=status)
        
        total = await query.count()
        records = await query.order_by("-started_at").offset(offset).limit(limit)
        
        return {
            "success": True,
            "message": "获取迁移记录成功",
            "data": {
                "total": total,
                "records": [
                    {
                        "id": r.id,
                        "migration_name": r.migration_name,
                        "migration_type": r.migration_type,
                        "source_table": r.source_table,
                        "target_table": r.target_table,
                        "total_records": r.total_records,
                        "migrated_records": r.migrated_records,
                        "failed_records": r.failed_records,
                        "skipped_records": r.skipped_records,
                        "status": r.status,
                        "started_at": r.started_at.isoformat() if r.started_at else None,
                        "completed_at": r.completed_at.isoformat() if r.completed_at else None
                    }
                    for r in records
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取迁移记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=MigrationExecuteResponse)
async def execute_migration(
    request: MigrationExecuteRequest,
    background_tasks: BackgroundTasks
):
    """
    执行数据迁移
    
    支持完整迁移或单独迁移某个类型
    """
    try:
        from app.services.migration_engine import (
            migration_engine, 
            run_full_migration
        )
        
        if request.dry_run:
            # 模拟运行，返回预估信息
            from app.models.device import DeviceType, DeviceInfo, DeviceField
            
            type_count = await DeviceType.all().count()
            device_count = await DeviceInfo.all().count()
            field_count = await DeviceField.all().count()
            
            return MigrationExecuteResponse(
                success=True,
                message="模拟运行完成",
                data={
                    "dry_run": True,
                    "estimated": {
                        "device_types": type_count,
                        "devices": device_count,
                        "fields": field_count
                    }
                },
                timestamp=datetime.now().isoformat()
            )
        
        # 实际执行迁移
        if request.migration_type == "full":
            result = await run_full_migration()
        elif request.migration_type == "device_types":
            result = await migration_engine.migrate_device_types()
        elif request.migration_type == "device_fields":
            result = await migration_engine.migrate_device_fields()
        elif request.migration_type == "devices":
            result = await migration_engine.migrate_devices()
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"未知的迁移类型: {request.migration_type}"
            )
        
        return MigrationExecuteResponse(
            success=True,
            message="迁移执行完成",
            data=result,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行迁移失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_migration():
    """
    验证迁移结果
    
    检查数据完整性和一致性
    """
    try:
        from app.services.migration_engine import migration_validator
        
        result = await migration_validator.validate_migration()
        
        return {
            "success": True,
            "message": "验证完成",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"验证迁移失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rollback")
async def rollback_migration(request: RollbackRequest):
    """
    回滚迁移
    
    警告：此操作将删除新表中的数据
    """
    try:
        from app.services.migration_engine import migration_rollback
        
        result = await migration_rollback.rollback_migration(request.migration_type)
        
        if result["status"] == "failed":
            raise HTTPException(status_code=400, detail=result.get("error", "回滚失败"))
        
        return {
            "success": True,
            "message": "回滚完成",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"回滚迁移失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/switch-architecture")
async def switch_architecture(request: ArchitectureSwitchRequest):
    """
    切换系统架构
    
    启用或禁用新架构，配置双写模式
    """
    try:
        from app.services.migration_engine import architecture_manager
        
        if request.enable_new_architecture:
            architecture_manager.enable_new_architecture()
        else:
            architecture_manager.disable_new_architecture()
        
        if request.enable_dual_write:
            architecture_manager.enable_dual_write()
        else:
            architecture_manager.disable_dual_write()
        
        status = await architecture_manager.get_migration_status()
        
        return {
            "success": True,
            "message": "架构切换完成",
            "data": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"切换架构失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data-comparison")
async def get_data_comparison():
    """
    获取新旧数据对比
    
    比较旧表和新表的数据统计
    """
    try:
        from app.models.device import DeviceType, DeviceInfo, DeviceField
        from app.models.platform_upgrade import AssetCategory, Asset, SignalDefinition
        
        comparison = {
            "device_types": {
                "old_count": await DeviceType.all().count(),
                "new_count": await AssetCategory.all().count()
            },
            "devices": {
                "old_count": await DeviceInfo.all().count(),
                "new_count": await Asset.all().count()
            },
            "fields": {
                "old_count": await DeviceField.all().count(),
                "new_count": await SignalDefinition.all().count()
            }
        }
        
        # 计算迁移进度
        for key in comparison:
            old = comparison[key]["old_count"]
            new = comparison[key]["new_count"]
            comparison[key]["progress"] = (new / old * 100) if old > 0 else 100
            comparison[key]["match"] = new >= old
        
        return {
            "success": True,
            "message": "获取数据对比成功",
            "data": comparison,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取数据对比失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-tdengine-schema")
async def sync_tdengine_schema(category_code: Optional[str] = None):
    """
    同步TDengine Schema
    
    Args:
        category_code: 指定类别编码，为空则同步所有
    """
    try:
        from app.services.schema_engine import schema_manager
        
        if category_code:
            success = await schema_manager.sync_category_schema(category_code)
            result = {category_code: success}
        else:
            result = await schema_manager.sync_all_categories()
        
        return {
            "success": True,
            "message": "Schema同步完成",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"同步Schema失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
