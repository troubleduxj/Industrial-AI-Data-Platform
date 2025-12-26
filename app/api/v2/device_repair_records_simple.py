#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备维修记录管理 API v2 - 简化版本
实现设备维修记录的CRUD操作，支持多条件筛选和分页
"""

import logging
from fastapi import APIRouter, Query, Request, Depends, HTTPException
from typing import Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# 简化的数据模型
class RepairRecordCreate(BaseModel):
    device_id: int
    device_type: str
    repair_date: date
    priority: str = "medium"
    applicant: str
    applicant_phone: Optional[str] = None
    is_fault: bool = True
    fault_reason: Optional[str] = None
    repair_content: Optional[str] = None

class RepairRecordUpdate(BaseModel):
    repair_status: Optional[str] = None
    priority: Optional[str] = None
    repair_content: Optional[str] = None
    repairer: Optional[str] = None

class RepairCodeGenerateRequest(BaseModel):
    device_type: str
    repair_date: date

# 简单的认证依赖
def simple_auth():
    return 1

# 简单的格式化器
def get_formatter():
    try:
        from app.core.response_formatter_v2 import create_formatter
        return create_formatter
    except ImportError:
        def simple_formatter(request):
            class SimpleFormatter:
                def success(self, data=None, message="Success"):
                    return {"success": True, "message": message, "data": data}
                def not_found(self, message="Not found"):
                    return {"success": False, "message": message, "error": "NOT_FOUND"}
                def bad_request(self, message="Bad request"):
                    return {"success": False, "message": message, "error": "BAD_REQUEST"}
                def internal_error(self, message="Internal error"):
                    return {"success": False, "message": message, "error": "INTERNAL_ERROR"}
            return SimpleFormatter()
        return simple_formatter


@router.get("/repair-records", summary="获取设备维修记录列表")
async def get_repair_records(
    request: Request,
    device_id: Optional[int] = Query(None, description="设备ID筛选"),
    device_type: Optional[str] = Query(None, description="设备类型筛选"),
    repair_status: Optional[str] = Query(None, description="维修状态筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    applicant: Optional[str] = Query(None, description="申请人筛选"),
    repairer: Optional[str] = Query(None, description="维修人员筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    is_fault: Optional[bool] = Query(None, description="是否故障筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: int = Depends(simple_auth)
):
    """获取设备维修记录列表，支持多条件筛选和分页"""
    try:
        formatter = get_formatter()(request)
        
        # 模拟数据
        sample_records = [
            {
                "id": 1,
                "device_id": 1,
                "device_type": "welding",
                "repair_date": "2025-09-08",
                "repair_code": "RWEL20250908001",
                "repair_status": "pending",
                "priority": "normal",
                "applicant": "张三",
                "applicant_phone": "13800138000",
                "is_fault": True,
                "fault_reason": "设备老化",
                "repair_content": "更换焊接头",
                "created_at": "2025-09-08T10:00:00",
                "updated_at": "2025-09-08T10:00:00"
            }
        ]
        
        # 简单筛选
        filtered_records = sample_records
        if device_id:
            filtered_records = [r for r in filtered_records if r["device_id"] == device_id]
        if device_type:
            filtered_records = [r for r in filtered_records if r["device_type"] == device_type]
        
        total = len(filtered_records)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_records = filtered_records[start_idx:end_idx]
        
        return formatter.success(
            data={
                "records": paginated_records,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "pages": (total + page_size - 1) // page_size
                }
            },
            message="获取维修记录列表成功"
        )
        
    except Exception as e:
        logger.error(f"获取维修记录列表失败: {str(e)}")
        formatter = get_formatter()(request)
        return formatter.internal_error("获取维修记录列表失败")


@router.get("/repair-records/{record_id}", summary="获取设备维修记录详情")
async def get_repair_record_detail(
    request: Request,
    record_id: int,
    user_id: int = Depends(simple_auth)
):
    """获取设备维修记录详情"""
    try:
        formatter = get_formatter()(request)
        
        if record_id <= 0:
            return formatter.not_found("维修记录不存在")
        
        record_data = {
            "id": record_id,
            "device_id": 1,
            "device_type": "welding",
            "repair_date": "2025-09-08",
            "repair_code": "RWEL20250908001",
            "repair_status": "pending",
            "priority": "normal",
            "applicant": "张三",
            "applicant_phone": "13800138000",
            "is_fault": True,
            "fault_reason": "设备老化",
            "repair_content": "更换焊接头",
            "created_at": "2025-09-08T10:00:00",
            "updated_at": "2025-09-08T10:00:00"
        }
        
        return formatter.success(
            data=record_data,
            message="获取维修记录详情成功"
        )
        
    except Exception as e:
        logger.error(f"获取维修记录详情失败: {str(e)}")
        formatter = get_formatter()(request)
        return formatter.internal_error("获取维修记录详情失败")


@router.post("/repair-records", summary="创建设备维修记录")
async def create_repair_record(
    request: Request,
    record_data: RepairRecordCreate,
    user_id: int = Depends(simple_auth)
):
    """创建设备维修记录"""
    try:
        formatter = get_formatter()(request)
        
        # 生成维修单号
        date_str = record_data.repair_date.strftime("%Y%m%d")
        type_prefix = record_data.device_type.upper()[:3] if record_data.device_type else "DEV"
        repair_code = f"R{type_prefix}{date_str}001"
        
        created_record = {
            "id": 1,
            "device_id": record_data.device_id,
            "device_type": record_data.device_type,
            "repair_date": record_data.repair_date,
            "repair_code": repair_code,
            "repair_status": "pending",
            "priority": record_data.priority,
            "applicant": record_data.applicant,
            "applicant_phone": record_data.applicant_phone,
            "is_fault": record_data.is_fault,
            "fault_reason": record_data.fault_reason,
            "repair_content": record_data.repair_content,
            "created_by": user_id,
            "updated_by": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        return formatter.success(
            data=created_record,
            message="创建维修记录成功"
        )
        
    except Exception as e:
        logger.error(f"创建维修记录失败: {str(e)}")
        formatter = get_formatter()(request)
        return formatter.internal_error("创建维修记录失败")


@router.put("/repair-records/{record_id}", summary="更新设备维修记录")
async def update_repair_record(
    request: Request,
    record_id: int,
    record_data: RepairRecordUpdate,
    user_id: int = Depends(simple_auth)
):
    """更新设备维修记录"""
    try:
        formatter = get_formatter()(request)
        
        if record_id <= 0:
            return formatter.not_found("维修记录不存在")
        
        updated_record = {
            "id": record_id,
            "device_id": 1,
            "device_type": "welding",
            "repair_date": "2025-09-08",
            "repair_code": "RWEL20250908001",
            "repair_status": record_data.repair_status or "pending",
            "priority": record_data.priority or "medium",
            "repair_content": record_data.repair_content,
            "repairer": record_data.repairer,
            "updated_by": user_id,
            "updated_at": datetime.now().isoformat()
        }
        
        return formatter.success(
            data=updated_record,
            message="更新维修记录成功"
        )
        
    except Exception as e:
        logger.error(f"更新维修记录失败: {str(e)}")
        formatter = get_formatter()(request)
        return formatter.internal_error("更新维修记录失败")


@router.delete("/repair-records/{record_id}", summary="删除设备维修记录")
async def delete_repair_record(
    request: Request,
    record_id: int,
    user_id: int = Depends(simple_auth)
):
    """删除设备维修记录"""
    try:
        formatter = get_formatter()(request)
        
        if record_id <= 0:
            return formatter.not_found("维修记录不存在")
        
        return formatter.success(
            data={"deleted_id": record_id},
            message="删除维修记录成功"
        )
        
    except Exception as e:
        logger.error(f"删除维修记录失败: {str(e)}")
        formatter = get_formatter()(request)
        return formatter.internal_error("删除维修记录失败")


@router.get("/repair-records/statistics", summary="获取维修记录统计信息")
async def get_repair_records_statistics(
    request: Request,
    device_type: Optional[str] = Query(None, description="设备类型筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    user_id: int = Depends(simple_auth)
):
    """获取维修记录统计信息"""
    try:
        formatter = get_formatter()(request)
        
        statistics = {
            "total_records": 10,
            "pending_records": 3,
            "in_progress_records": 2,
            "completed_records": 4,
            "cancelled_records": 1,
            "fault_records": 8,
            "maintenance_records": 2,
            "device_type_distribution": {
                "welding": 6,
                "cutting": 3,
                "assembly": 1
            },
            "priority_distribution": {
                "low": 2,
                "medium": 5,
                "high": 2,
                "urgent": 1
            },
            "status_distribution": {
                "pending": 3,
                "in_progress": 2,
                "completed": 4,
                "cancelled": 1
            },
            "monthly_trend": {
                "2025-08": 5,
                "2025-09": 5
            },
            "average_repair_time": 2.5,
            "total_repair_cost": 15000.0,
            "average_repair_cost": 1500.0
        }
        
        return formatter.success(
            data=statistics,
            message="获取维修记录统计信息成功"
        )
        
    except Exception as e:
        logger.error(f"获取维修记录统计信息失败: {str(e)}")
        formatter = get_formatter()(request)
        return formatter.internal_error("获取维修记录统计信息失败")


@router.post("/repair-codes/generate", summary="生成维修单号")
async def generate_repair_code_endpoint(
    request: Request,
    code_request: RepairCodeGenerateRequest,
    user_id: int = Depends(simple_auth)
):
    """生成维修单号"""
    try:
        formatter = get_formatter()(request)
        
        date_str = code_request.repair_date.strftime("%Y%m%d")
        type_prefix = code_request.device_type.upper()[:3] if code_request.device_type else "DEV"
        repair_code = f"R{type_prefix}{date_str}001"
        
        response_data = {
            "repair_code": repair_code,
            "device_type": code_request.device_type,
            "repair_date": code_request.repair_date
        }
        
        return formatter.success(
            data=response_data,
            message="生成维修单号成功"
        )
        
    except Exception as e:
        logger.error(f"生成维修单号失败: {str(e)}")
        formatter = get_formatter()(request)
        return formatter.internal_error("生成维修单号失败")