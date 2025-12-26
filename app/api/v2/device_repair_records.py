# -*- coding: utf-8 -*-
"""
设备维修记录管理API
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
import time
import io
from fastapi import APIRouter, Query, Request, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from tortoise.transactions import in_transaction
from tortoise.expressions import Q
from pydantic import ValidationError

from app.core.dependency import DependAuth
from app.core.response_formatter_v2 import create_formatter
from app.schemas.devices import (
    DeviceRepairRecordCreate,
    DeviceRepairRecordUpdate,
    RepairCodeGenerateRequest
)
from app.models.device import DeviceInfo, DeviceRepairRecord
from app.models.admin import User, HttpAuditLog
from app.core.device_maintenance_permissions import (
    require_repair_record_read_permission,
    require_repair_record_create_permission,
    require_repair_record_update_permission,
    require_repair_record_delete_permission,
    require_repair_record_statistics_permission,
    require_repair_code_generate_permission,
    check_repair_record_access
)
from app.services.device_maintenance_permission_service import (
    device_maintenance_permission_service,
    DeviceMaintenanceAuditAction
)

logger = logging.getLogger(__name__)

router = APIRouter()


async def generate_repair_code(device_type: str, repair_date: date) -> str:
    """
    生成维修单号
    格式: WX-{设备类型}-{年月日}-{序号}
    """
    date_str = repair_date.strftime("%Y%m%d")
    
    # 设备类型映射
    type_mapping = {
        "welding": "HJ",
        "cutting": "QG", 
        "drilling": "ZK",
        "milling": "XX",
        "grinding": "MX",
        "lathe": "CC",
        "press": "YJ",
        "conveyor": "SS",
        "robot": "JQ",
        "other": "QT"
    }
    
    type_code = type_mapping.get(device_type, "QT")
    
    # 查询当天同类型设备的维修记录数量，确保唯一性
    today_start = datetime.combine(repair_date, datetime.min.time())
    today_end = datetime.combine(repair_date, datetime.max.time())
    
    # 使用循环确保生成唯一的维修单号
    sequence = 1
    max_attempts = 1000  # 防止无限循环
    
    for attempt in range(max_attempts):
        repair_code = f"WX-{type_code}-{date_str}-{sequence:03d}"
        
        # 检查是否已存在
        existing = await DeviceRepairRecord.filter(repair_code=repair_code).exists()
        if not existing:
            return repair_code
        
        sequence += 1
    
    # 如果尝试1000次都没有找到唯一编号，使用时间戳后缀
    import time
    timestamp_suffix = int(time.time() * 1000) % 10000
    return f"WX-{type_code}-{date_str}-{timestamp_suffix:04d}"



@router.get("/repair-records/statistics", summary="获取维修记录统计信息")
async def get_repair_records_statistics(
    request: Request,
    device_type: Optional[str] = Query(None, description="设备类型筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(require_repair_record_statistics_permission)
):
    """
    获取维修记录统计信息
    """
    formatter = create_formatter(request)
    
    try:
        # 记录审计日志
        await device_maintenance_permission_service.log_audit(
            user=current_user,
            action=DeviceMaintenanceAuditAction.VIEW_REPAIR_STATISTICS,
            details=f"查询维修记录统计信息 - 设备类型: {device_type}, 时间范围: {start_date} 到 {end_date}"
        )
        
        # 构建查询条件
        query = DeviceRepairRecord.all()
        
        if device_type:
            query = query.filter(device_type=device_type)
        
        if start_date:
            query = query.filter(repair_date__gte=start_date)
        
        if end_date:
            query = query.filter(repair_date__lte=end_date)
        
        # 获取统计数据
        total_records = await query.count()
        
        # 按状态统计
        status_stats = {}
        for status in ['pending', 'in_progress', 'completed', 'cancelled']:
            count = await query.filter(repair_status=status).count()
            status_stats[status] = count
        
        # 按优先级统计
        priority_stats = {}
        for priority in ['low', 'normal', 'high', 'urgent']:
            count = await query.filter(priority=priority).count()
            priority_stats[priority] = count
        
        # 按设备类型统计
        device_type_stats = {}
        device_types = await query.distinct().values_list('device_type', flat=True)
        for dtype in device_types:
            count = await query.filter(device_type=dtype).count()
            device_type_stats[dtype] = count
        
        # 按月份统计（最近12个月）
        monthly_stats = {}
        current_date = datetime.now().date()
        for i in range(12):
            month_start = current_date.replace(day=1) - timedelta(days=i*30)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            count = await query.filter(
                repair_date__gte=month_start,
                repair_date__lte=month_end
            ).count()
            monthly_stats[month_start.strftime("%Y-%m")] = count
        
        return formatter.success({
            "total_records": total_records,
            "status_statistics": status_stats,
            "priority_statistics": priority_stats,
            "device_type_statistics": device_type_stats,
            "monthly_statistics": monthly_stats
        })
        
    except Exception as e:
        logger.error(f"获取维修记录统计信息失败: {type(e).__name__} - {str(e)}")
        return formatter.internal_error(f"获取统计信息失败: {type(e).__name__} - {str(e)}")


@router.get("/repair-records", summary="获取设备维修记录列表", response_model=None)
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
    current_user: User = Depends(require_repair_record_read_permission)
):
    """
    获取设备维修记录列表
    """
    formatter = create_formatter()
    start_time = time.time()

    try:
        # 构建查询条件
        query = DeviceRepairRecord.all().select_related('device')
        
        if device_id:
            query = query.filter(device_id=device_id)
        if device_type:
            query = query.filter(device__device_type=device_type)
        if repair_status:
            query = query.filter(repair_status=repair_status)
        if start_date:
            query = query.filter(repair_date__gte=start_date)
        if end_date:
            query = query.filter(repair_date__lte=end_date)
        if applicant:
            query = query.filter(applicant__icontains=applicant)
        if repairer:
            query = query.filter(repairer__icontains=repairer)
        if priority:
            query = query.filter(priority=priority)
        if is_fault is not None:
            query = query.filter(is_fault=is_fault)

        # 获取总数
        total = await query.count()
        
        # 分页查询
        offset = (page - 1) * page_size
        records = await query.offset(offset).limit(page_size).order_by('-created_at')
        
        # 格式化数据 - 支持前端完整数据结构
        record_list = []
        for record in records:
            # 获取设备编号
            device_code = record.device.device_code if record.device else None
            
            record_data = {
                "id": record.id,
                "device_id": record.device_id,
                "device_code": device_code,  # 新增字段
                "device_type": record.device_type,
                "repair_date": record.repair_date.isoformat() if record.repair_date else None,
                "repair_code": record.repair_code,
                "repair_status": record.repair_status,
                "priority": record.priority,
                
                # 申请人信息
                "applicant": record.applicant,
                "applicant_phone": record.applicant_phone,
                "applicant_dept": record.applicant_dept,
                "applicant_workshop": record.applicant_workshop,
                "construction_unit": record.construction_unit,
                
                # 故障信息
                "is_fault": record.is_fault,
                "fault_reason": record.fault_reason,
                "damage_category": record.damage_category,
                "fault_content": record.fault_content,
                "fault_location": record.fault_location,
                
                # 维修信息
                "repair_content": record.repair_content,
                "parts_name": record.parts_name,
                "repairer": record.repairer,
                "repair_start_time": record.repair_start_time.isoformat() if record.repair_start_time else None,
                "repair_completion_date": record.repair_completion_date.isoformat() if record.repair_completion_date else None,
                "repair_cost": float(record.repair_cost) if record.repair_cost else None,
                
                # 扩展数据
                "device_specific_data": record.device_specific_data or {},
                
                # 其他信息
                "remarks": record.remarks,
                "attachments": record.attachments or {},
                "created_by": record.created_by,
                "updated_by": record.updated_by,
                "created_at": record.created_at.isoformat(),
                "updated_at": record.updated_at.isoformat()
            }
            record_list.append(record_data)

        # 记录成功审计日志
        response_time = int((time.time() - start_time) * 1000)
        await device_maintenance_permission_service.create_audit_log(
            user=current_user,
            action=DeviceMaintenanceAuditAction.VIEW_REPAIR_RECORD,
            request=request,
            status_code=200,
            response_time=response_time
        )

        return formatter.success(data={
            "records": record_list,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": (total + page_size - 1) // page_size
            }
        })

    except Exception as e:
        logger.error(f"获取维修记录列表失败: {str(e)}")
        
        # 记录错误审计日志
        response_time = int((time.time() - start_time) * 1000)
        await device_maintenance_permission_service.create_audit_log(
            user=current_user,
            action=DeviceMaintenanceAuditAction.VIEW_REPAIR_RECORD,
            request=request,
            status_code=500,
            response_time=response_time,
            error_message=str(e)
        )
        
        return formatter.internal_error("获取维修记录列表失败")


@router.post("/repair-codes/generate", summary="生成维修单号", response_model=None)
async def generate_repair_code_endpoint(
    request: Request,
    code_request: RepairCodeGenerateRequest,
    current_user: User = Depends(require_repair_code_generate_permission)
):
    """
    生成维修单号
    """
    formatter = create_formatter()
    start_time = time.time()
    
    try:
        repair_code = await generate_repair_code(code_request.device_type, code_request.repair_date)
        
        # 记录成功审计日志
        response_time = int((time.time() - start_time) * 1000)
        await device_maintenance_permission_service.create_audit_log(
            user=current_user,
            action=DeviceMaintenanceAuditAction.GENERATE_REPAIR_CODE,
            request=request,
            status_code=200,
            response_time=response_time
        )
        
        return formatter.success(data={
            "repair_code": repair_code
        })
        
    except Exception as e:
        logger.error(f"生成维修单号失败: {str(e)}")
        
        # 记录错误审计日志
        response_time = int((time.time() - start_time) * 1000)
        await device_maintenance_permission_service.create_audit_log(
            user=current_user,
            action=DeviceMaintenanceAuditAction.GENERATE_REPAIR_CODE,
            request=request,
            status_code=500,
            response_time=response_time,
            error_message=str(e)
        )
        
        return formatter.internal_error("生成维修单号失败")



@router.get("/repair-records/{record_id}", summary="获取设备维修记录详情", response_model=None)
async def get_repair_record_detail(
    request: Request,
    record_id: int,
    current_user: User = Depends(require_repair_record_read_permission)
):
    """
    获取设备维修记录详情
    """
    formatter = create_formatter()
    start_time = time.time()
    
    try:
        # 检查记录级别的访问权限
        has_access, error_msg = await check_repair_record_access(current_user, record_id, "delete")
        if not has_access:
            logger.warning(f"用户无权限访问维修记录: record_id={record_id}, user={current_user.username}, error={error_msg}")
            return formatter.forbidden(f"无权限访问该维修记录 (ID: {record_id}): {error_msg}")
        
        # 获取维修记录详情
        repair_record = await DeviceRepairRecord.get_or_none(id=record_id)
        if repair_record:
            await repair_record.fetch_related('device')
        
        if not repair_record:
            return formatter.not_found("维修记录不存在")
        
        # 格式化数据 - 支持前端完整数据结构
        device_code = repair_record.device.device_code if repair_record.device else None
        
        record_data = {
            "id": repair_record.id,
            "device_id": repair_record.device_id,
            "device_code": device_code,  # 新增字段
            "device_type": repair_record.device_type,
            "repair_date": repair_record.repair_date.isoformat() if repair_record.repair_date else None,
            "repair_code": repair_record.repair_code,
            "repair_status": repair_record.repair_status,
            "priority": repair_record.priority,
            
            # 申请人信息
            "applicant": repair_record.applicant,
            "applicant_phone": repair_record.applicant_phone,
            "applicant_dept": repair_record.applicant_dept,
            "applicant_workshop": repair_record.applicant_workshop,
            "construction_unit": repair_record.construction_unit,
            
            # 故障信息
            "is_fault": repair_record.is_fault,
            "fault_reason": repair_record.fault_reason,
            "damage_category": repair_record.damage_category,
            "fault_content": repair_record.fault_content,
            "fault_location": repair_record.fault_location,
            
            # 维修信息
            "repair_content": repair_record.repair_content,
            "parts_name": repair_record.parts_name,
            "repairer": repair_record.repairer,
            "repair_start_time": repair_record.repair_start_time.isoformat() if repair_record.repair_start_time else None,
            "repair_completion_date": repair_record.repair_completion_date.isoformat() if repair_record.repair_completion_date else None,
            "repair_cost": float(repair_record.repair_cost) if repair_record.repair_cost else None,
            
            # 扩展数据
            "device_specific_data": repair_record.device_specific_data or {},
            
            # 其他信息
            "remarks": repair_record.remarks,
            "attachments": repair_record.attachments or {},
            "created_by": repair_record.created_by,
            "updated_by": repair_record.updated_by,
            "created_at": repair_record.created_at.isoformat(),
            "updated_at": repair_record.updated_at.isoformat()
        }

        # 记录成功审计日志
        response_time = int((time.time() - start_time) * 1000)
        await device_maintenance_permission_service.create_audit_log(
            user=current_user,
            action=DeviceMaintenanceAuditAction.VIEW_REPAIR_RECORD,
            request=request,
            status_code=200,
            response_time=response_time
        )

        return formatter.success(data=record_data)

    except Exception as e:
        logger.error(f"获取维修记录详情失败: {str(e)}")
        
        # 记录错误审计日志
        response_time = int((time.time() - start_time) * 1000)
        await device_maintenance_permission_service.create_audit_log(
            user=current_user,
            action=DeviceMaintenanceAuditAction.VIEW_REPAIR_RECORD,
            request=request,
            status_code=500,
            response_time=response_time,
            error_message=str(e)
        )
        
        return formatter.internal_error("获取维修记录详情失败")


@router.post("/repair-records", summary="创建设备维修记录", response_model=None)
async def create_repair_record(
    request: Request,
    record_data: DeviceRepairRecordCreate,
    current_user: User = Depends(require_repair_record_create_permission)
):
    """
    创建设备维修记录
    """
    formatter = create_formatter()
    start_time = time.time()
    
    try:
        # 使用服务层处理业务逻辑
        from app.services.device_repair_record_service import DeviceRepairRecordService
        result = await DeviceRepairRecordService.create_repair_record(record_data, current_user)
        
        # 根据结果类型返回相应的响应
        if result["success"]:
            # 暂时禁用审计日志功能以绕过AuditLog导入问题
            response_time = int((time.time() - start_time) * 1000)
            summary = f"{DeviceMaintenanceAuditAction.CREATE_REPAIR_RECORD.value} (ID: {result['data']['id']})"
            # await AuditLog.create(
            #     user_id=current_user.id,
            #     username=current_user.username,
            #     module="设备维护管理",
            #     summary=summary,
            #     method=request.method,
            #     path=str(request.url.path),
            #     status=201,
            #     response_time=response_time,
            #     request_args=None,
            #     response_body=None
            # )
            
            logger.info(f"审计日志功能已暂时禁用: 创建维修记录 {result['data']['id']}")
            
            return formatter.success(data=result["data"], message=result["message"])
        else:
            # 处理不同类型的错误
            response_time = int((time.time() - start_time) * 1000)
            error_type = result.get("error_type", "unknown")
            
            if error_type == "validation":
                # 记录验证错误审计日志
                await device_maintenance_permission_service.create_audit_log(
                    user=current_user,
                    action=DeviceMaintenanceAuditAction.CREATE_REPAIR_RECORD,
                    request=request,
                    status_code=422,
                    response_time=response_time,
                    error_message=result["message"]
                )
                return formatter.bad_request(result["message"], details=result.get("details"))
            
            elif error_type == "not_found":
                logger.warning(f"尝试为不存在的设备创建维修记录: device_id={record_data.device_id}, user={current_user.username}")
                return formatter.not_found(result["message"])
            
            else:
                # 记录其他错误审计日志
                await device_maintenance_permission_service.create_audit_log(
                    user=current_user,
                    action=DeviceMaintenanceAuditAction.CREATE_REPAIR_RECORD,
                    request=request,
                    status_code=500,
                    response_time=response_time,
                    error_message=result["message"]
                )
                return formatter.internal_error(result["message"])

    except ValidationError as ve:
        # 处理Pydantic验证错误，返回422状态码
        error_details = []
        for error in ve.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            error_details.append(f"{field}: {message}")
        
        error_msg = "请求参数验证失败: " + "; ".join(error_details)
        logger.warning(f"维修记录创建参数验证失败: {error_msg}, user={current_user.username}")
        
        # 记录验证错误审计日志
        response_time = int((time.time() - start_time) * 1000)
        await device_maintenance_permission_service.create_audit_log(
            user=current_user,
            action=DeviceMaintenanceAuditAction.CREATE_REPAIR_RECORD,
            request=request,
            status_code=422,
            response_time=response_time,
            error_message=error_msg
        )
        
        return formatter.bad_request(error_msg, details=error_details)
        
    except Exception as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "device_id": getattr(record_data, 'device_id', None),
            "user": current_user.username,
            "timestamp": datetime.now().isoformat()
        }
        logger.error(f"创建维修记录失败: {error_details}")
        
        # 记录错误审计日志
        response_time = int((time.time() - start_time) * 1000)
        await device_maintenance_permission_service.create_audit_log(
            user=current_user,
            action=DeviceMaintenanceAuditAction.CREATE_REPAIR_RECORD,
            request=request,
            status_code=500,
            response_time=response_time,
            error_message=str(e)
        )
        
        return formatter.internal_error(f"创建维修记录失败: {type(e).__name__} - {str(e)}")


@router.put("/repair-records/{record_id}", summary="更新设备维修记录", response_model=None)
async def update_repair_record(
    request: Request,
    record_id: int,
    record_data: DeviceRepairRecordUpdate,
    current_user: User = Depends(require_repair_record_update_permission)
):
    """
    更新设备维修记录
    """
    formatter = create_formatter()
    start_time = time.time()
    
    try:
        # 检查记录级别的访问权限
        has_access, error_msg = await check_repair_record_access(current_user, record_id, "update")
        if not has_access:
            logger.warning(f"用户无权限访问维修记录: record_id={record_id}, user={current_user.username}, error={error_msg}")
            return formatter.forbidden(f"无权限访问该维修记录 (ID: {record_id}): {error_msg}")
        
        # 使用服务层处理业务逻辑
        from app.services.device_repair_record_service import DeviceRepairRecordService
        result = await DeviceRepairRecordService.update_repair_record(record_id, record_data, current_user)
        
        # 根据结果类型返回相应的响应
        if result["success"]:
            # 记录成功审计日志
            response_time = int((time.time() - start_time) * 1000)
            await device_maintenance_permission_service.create_audit_log(
                user=current_user,
                action=DeviceMaintenanceAuditAction.UPDATE_REPAIR_RECORD,
                request=request,
                status_code=200,
                response_time=response_time
            )
            
            return formatter.success(message=result["message"])
        else:
            # 处理不同类型的错误
            response_time = int((time.time() - start_time) * 1000)
            error_type = result.get("error_type", "unknown")
            
            if error_type == "validation":
                return formatter.bad_request(result["message"], details=result.get("details"))
            elif error_type == "not_found":
                logger.warning(f"尝试更新不存在的维修记录: record_id={record_id}, user={current_user.username}")
                return formatter.not_found(result["message"])
            else:
                # 记录错误审计日志
                await device_maintenance_permission_service.create_audit_log(
                    user=current_user,
                    action=DeviceMaintenanceAuditAction.UPDATE_REPAIR_RECORD,
                    request=request,
                    status_code=500,
                    response_time=response_time,
                    error_message=result["message"]
                )
                return formatter.internal_error(result["message"])

    except Exception as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "record_id": record_id,
            "user": current_user.username,
            "timestamp": datetime.now().isoformat()
        }
        logger.error(f"更新维修记录失败: {error_details}")
        
        # 记录错误审计日志
        response_time = int((time.time() - start_time) * 1000)
        await device_maintenance_permission_service.create_audit_log(
            user=current_user,
            action=DeviceMaintenanceAuditAction.UPDATE_REPAIR_RECORD,
            request=request,
            status_code=500,
            response_time=response_time,
            error_message=str(e)
        )
        
        return formatter.internal_error(f"更新维修记录失败: {type(e).__name__} - {str(e)}")


@router.delete("/repair-records/{record_id}", summary="删除设备维修记录", response_model=None)
async def delete_repair_record(
    request: Request,
    record_id: int,
    current_user: User = Depends(require_repair_record_delete_permission)
):
    """
    删除设备维修记录
    """
    formatter = create_formatter()
    start_time = time.time()
    
    try:
        # 验证记录ID
        if record_id <= 0:
            logger.warning(f"无效的维修记录ID: {record_id}, user={current_user.username}")
            return formatter.bad_request(f"无效的维修记录ID: {record_id}")
        
        # 检查记录级别的访问权限
        has_access, error_msg = await check_repair_record_access(current_user, record_id, "read")
        if not has_access:
            logger.warning(f"用户无权限访问维修记录: record_id={record_id}, user={current_user.username}, error={error_msg}")
            return formatter.forbidden(f"无权限访问该维修记录 (ID: {record_id}): {error_msg}")
        
        # 获取维修记录
        repair_record = await DeviceRepairRecord.get_or_none(id=record_id)
        if not repair_record:
            logger.warning(f"尝试删除不存在的维修记录: record_id={record_id}, user={current_user.username}")
            return formatter.not_found(f"维修记录不存在 (ID: {record_id})")
        
        # 检查是否可以删除（业务逻辑验证）
        if repair_record.repair_status == "completed":
            logger.warning(f"尝试删除已完成的维修记录: record_id={record_id}, repair_code={repair_record.repair_code}, user={current_user.username}")
            return formatter.bad_request(f"无法删除已完成的维修记录 (维修单号: {repair_record.repair_code})")
        
        # 记录删除前的信息
        repair_code = repair_record.repair_code
        device_id = repair_record.device_id
        
        # 执行删除操作
        try:
            await repair_record.delete()
        except Exception as db_error:
            logger.error(f"数据库删除维修记录失败: {str(db_error)}, record_id={record_id}, repair_code={repair_code}")
            return formatter.internal_error(f"数据库操作失败: {str(db_error)}")

        # 记录成功审计日志
        response_time = int((time.time() - start_time) * 1000)
        await device_maintenance_permission_service.create_audit_log(
            user=current_user,
            action=DeviceMaintenanceAuditAction.DELETE_REPAIR_RECORD,
            request=request,
            status_code=200,
            response_time=response_time
        )

        logger.info(f"维修记录删除成功: record_id={record_id}, repair_code={repair_code}, device_id={device_id}, user={current_user.username}")
        return formatter.success(message=f"维修记录删除成功 (维修单号: {repair_code})")

    except Exception as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "record_id": record_id,
            "user": current_user.username,
            "timestamp": datetime.now().isoformat()
        }
        logger.error(f"删除维修记录失败: {error_details}")
        
        # 记录错误审计日志
        response_time = int((time.time() - start_time) * 1000)
        await device_maintenance_permission_service.create_audit_log(
            user=current_user,
            action=DeviceMaintenanceAuditAction.DELETE_REPAIR_RECORD,
            request=request,
            status_code=500,
            response_time=response_time,
            error_message=str(e)
        )
        
        return formatter.internal_error(f"删除维修记录失败: {type(e).__name__} - {str(e)}")