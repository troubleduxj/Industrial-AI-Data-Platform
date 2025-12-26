"""
审计日志 v2接口
提供审计日志查询的RESTful接口（只读）
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Request, Depends, Query
from tortoise.expressions import Q

from app.models.admin import HttpAuditLog, User
from app.core.auth_dependencies import get_current_active_user
from app.core.response_formatter_v2 import ResponseFormatterV2

router = APIRouter()

@router.get("", summary="获取审计日志列表")
async def get_audit_logs(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    username: Optional[str] = Query(None, description="用户名筛选"),
    module: Optional[str] = Query(None, description="模块筛选"),
    method: Optional[str] = Query(None, description="请求方法筛选"),
    current_user: User = Depends(get_current_active_user)
):
    """获取审计日志列表"""
    formatter = ResponseFormatterV2(request)
    
    try:
        # 构建查询条件
        q = Q()
        query_params = {}
        
        if username:
            q &= Q(username__icontains=username)
            query_params['username'] = username
            
        if module:
            q &= Q(module__icontains=module)
            query_params['module'] = module
            
        if method:
            q &= Q(method=method)
            query_params['method'] = method
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 查询总数
        total = await HttpAuditLog.filter(q).count()
        
        # 查询数据
        audit_logs = await HttpAuditLog.filter(q).order_by("-created_at").offset(offset).limit(page_size).all()
        
        # 转换数据格式
        log_list = []
        for log in audit_logs:
            # 解析请求参数
            request_data = {}
            if log.request_args:
                try:
                    request_data = log.request_args if isinstance(log.request_args, dict) else {}
                except:
                    request_data = {"raw": str(log.request_args)}
            
            # 解析响应数据
            response_data = {}
            if log.response_body:
                try:
                    response_data = log.response_body if isinstance(log.response_body, dict) else {}
                except:
                    response_data = {"raw": str(log.response_body)}
            
            log_data = {
                "id": log.id,
                "username": log.username,
                "module": log.module or "unknown",  # 修复字段名映射
                "summary": log.summary,
                "path": log.path,
                "method": log.method,
                "status": log.status,
                "response_time": log.response_time,
                "request_data": request_data,
                "response_data": response_data,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            log_list.append(log_data)
        
        return formatter.paginated_success(
            data=log_list,
            total=total,
            page=page,
            page_size=page_size,
            message="Audit logs retrieved successfully",
            resource_type="audit_logs",
            query_params=query_params
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to retrieve audit logs: {str(e)}")

@router.get("/{log_id}", summary="获取审计日志详情")
async def get_audit_log(
    log_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """获取审计日志详情"""
    formatter = ResponseFormatterV2(request)
    
    try:
        log = await HttpAuditLog.get_or_none(id=log_id)
        if not log:
            return formatter.not_found("审计日志不存在", "audit_log")
        
        # 解析请求参数
        request_data = {}
        if log.request_args:
            try:
                import json
                request_data = json.loads(log.request_args) if isinstance(log.request_args, str) else log.request_args
            except:
                request_data = {"raw": str(log.request_args)}
        
        # 解析响应数据
        response_data = {}
        if log.response_body:
            try:
                import json
                response_data = json.loads(log.response_body) if isinstance(log.response_body, str) else log.response_body
            except:
                response_data = {"raw": str(log.response_body)}
        
        log_data = {
            "id": log.id,
            "username": log.username,
            "action_type": log.method,
            "resource_type": log.module or "unknown",
            "resource_id": None,  # 可以从路径中提取
            "summary": log.summary,
            "path": log.path,
            "method": log.method,
            "status": log.status,
            "success": 200 <= log.status < 400 if log.status else False,
            "response_time": log.response_time,
            "ip_address": getattr(log, 'ip_address', None),
            "user_agent": getattr(log, 'user_agent', None),
            "request_data": request_data,
            "response_data": response_data,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
        
        return formatter.success(
            data=log_data,
            message="获取审计日志详情成功",
            resource_id=str(log_id),
            resource_type="audit_logs"
        )
        
    except Exception as e:
        return formatter.internal_error(f"获取审计日志详情失败: {str(e)}")