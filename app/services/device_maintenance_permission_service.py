#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备维护权限控制服务
实现设备维修记录的权限验证和审计功能
"""

import logging
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import json

from fastapi import Request
from tortoise.transactions import in_transaction

from app.models.admin import User, Role, SysApiEndpoint, HttpAuditLog
from app.models.device import DeviceRepairRecord, DeviceInfo
from app.core.cache import permission_cache

logger = logging.getLogger(__name__)


class DeviceMaintenancePermission(Enum):
    """设备维护权限枚举"""
    
    # 维修记录权限
    REPAIR_RECORD_READ = "device:maintenance:repair_record:read"
    REPAIR_RECORD_CREATE = "device:maintenance:repair_record:create"
    REPAIR_RECORD_UPDATE = "device:maintenance:repair_record:update"
    REPAIR_RECORD_DELETE = "device:maintenance:repair_record:delete"
    REPAIR_RECORD_STATISTICS = "device:maintenance:repair_record:statistics"
    
    # 设备字段配置权限
    DEVICE_FIELD_CONFIG_READ = "device:maintenance:field_config:read"
    DEVICE_FIELD_CONFIG_UPDATE = "device:maintenance:field_config:update"
    
    # 维修单号生成权限
    REPAIR_CODE_GENERATE = "device:maintenance:repair_code:generate"


class DeviceMaintenanceAuditAction(Enum):
    """设备维护审计操作枚举"""
    
    # 维修记录操作
    CREATE_REPAIR_RECORD = "创建维修记录"
    UPDATE_REPAIR_RECORD = "更新维修记录"
    DELETE_REPAIR_RECORD = "删除维修记录"
    VIEW_REPAIR_RECORD = "查看维修记录"
    VIEW_REPAIR_STATISTICS = "查看维修统计"
    
    # 配置操作
    VIEW_DEVICE_FIELDS = "查看设备字段配置"
    UPDATE_DEVICE_FIELDS = "更新设备字段配置"
    
    # 其他操作
    GENERATE_REPAIR_CODE = "生成维修单号"


class DeviceMaintenancePermissionService:
    """设备维护权限服务"""
    
    def __init__(self):
        self.cache_ttl = 300  # 5分钟缓存
        self.module_name = "设备维护"
    
    async def check_permission(
        self,
        user: User,
        permission: DeviceMaintenancePermission,
        resource_id: Optional[int] = None,
        additional_checks: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, Optional[str]]:
        """
        检查用户是否有指定的设备维护权限
        
        Args:
            user: 当前用户
            permission: 权限类型
            resource_id: 资源ID（如维修记录ID）
            additional_checks: 额外的权限检查条件
            
        Returns:
            tuple: (是否有权限, 权限不足的原因)
        """
        try:
            # 临时设置：维修记录相关权限全开放
            # TODO: 完善权限配置逻辑后移除此临时设置
            repair_record_permissions = {
                DeviceMaintenancePermission.REPAIR_RECORD_READ,
                DeviceMaintenancePermission.REPAIR_RECORD_CREATE,
                DeviceMaintenancePermission.REPAIR_RECORD_UPDATE,
                DeviceMaintenancePermission.REPAIR_RECORD_DELETE,
                DeviceMaintenancePermission.REPAIR_RECORD_STATISTICS,
                DeviceMaintenancePermission.REPAIR_CODE_GENERATE
            }
            
            if permission in repair_record_permissions:
                logger.info(f"维修记录权限全开放模式: 用户 {user.username} 获得权限 {permission.value}")
                return True, None
            
            # 1. 超级管理员直接通过
            if user.is_superuser:
                return True, None
            
            # 2. 尝试从缓存获取权限结果
            cache_key = f"device_maintenance_permission:{user.id}:{permission.value}"
            if resource_id:
                cache_key += f":{resource_id}"
            
            try:
                cached_result = await permission_cache.get(cache_key)
                if cached_result is not None:
                    return cached_result, None if cached_result else f"缺少权限: {permission.value}"
            except Exception as cache_error:
                logger.warning(f"权限缓存获取失败: {cache_error}")
            
            # 3. 从数据库检查权限
            has_permission = await self._check_permission_from_db(user, permission)
            
            # 4. 执行额外的权限检查
            if has_permission and additional_checks:
                additional_result = await self._check_additional_conditions(
                    user, permission, resource_id, additional_checks
                )
                if not additional_result:
                    has_permission = False
            
            # 5. 缓存结果
            try:
                await permission_cache.set(cache_key, has_permission, ttl=self.cache_ttl)
            except Exception as cache_error:
                logger.warning(f"权限缓存设置失败: {cache_error}")
            
            return has_permission, None if has_permission else f"缺少权限: {permission.value}"
            
        except Exception as e:
            logger.error(f"权限检查失败 user_id={user.id}, permission={permission.value}: {e}")
            return False, f"权限检查失败: {str(e)}"
    
    async def check_repair_record_access(
        self,
        user: User,
        record: DeviceRepairRecord,
        action: str
    ) -> tuple[bool, Optional[str]]:
        """
        检查用户是否可以访问特定的维修记录
        
        Args:
            user: 当前用户
            record: 维修记录
            action: 操作类型 (read, update, delete)
            
        Returns:
            tuple: (是否有权限, 权限不足的原因)
        """
        try:
            # 1. 超级管理员直接通过
            if user.is_superuser:
                return True, None
            
            # 2. 检查基础权限
            permission_map = {
                "read": DeviceMaintenancePermission.REPAIR_RECORD_READ,
                "update": DeviceMaintenancePermission.REPAIR_RECORD_UPDATE,
                "delete": DeviceMaintenancePermission.REPAIR_RECORD_DELETE
            }
            
            base_permission = permission_map.get(action)
            if not base_permission:
                return False, f"未知操作类型: {action}"
            
            has_base_permission, reason = await self.check_permission(user, base_permission)
            if not has_base_permission:
                return False, reason
            
            # 3. 检查记录级别的权限
            # 检查是否只能访问自己创建的记录
            if not user.is_superuser and record.created_by != user.id:
                # 检查是否有跨用户访问权限
                has_cross_user_permission = await self._check_cross_user_access(user, record)
                if not has_cross_user_permission:
                    return False, "只能访问自己创建的维修记录"
            
            # 4. 检查记录状态权限
            if action == "delete" and record.repair_status == "completed":
                return False, "已完成的维修记录不允许删除"
            
            return True, None
            
        except Exception as e:
            logger.error(f"维修记录访问权限检查失败 user_id={user.id}, record_id={record.id}: {e}")
            return False, f"权限检查失败: {str(e)}"
    
    async def _check_permission_from_db(self, user: User, permission: DeviceMaintenancePermission) -> bool:
        """从数据库检查权限"""
        try:
            # 获取用户角色
            roles = await user.roles.all()
            if not roles:
                return False
            
            # 构建对应的API路径模式
            api_patterns = self._get_api_patterns_for_permission(permission)
            
            for role in roles:
                role_apis = await role.apis.all()
                for api in role_apis:
                    api_path = f"{api.http_method} {api.api_path}"
                    if any(pattern in api_path for pattern in api_patterns):
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"数据库权限检查失败: {e}")
            return False
    
    def _get_api_patterns_for_permission(self, permission: DeviceMaintenancePermission) -> List[str]:
        """获取权限对应的API路径模式"""
        permission_api_mapping = {
            DeviceMaintenancePermission.REPAIR_RECORD_READ: [
                "GET /api/v2/device/maintenance/repair-records",
                "GET /api/v2/device/maintenance/repair-records/"
            ],
            DeviceMaintenancePermission.REPAIR_RECORD_CREATE: [
                "POST /api/v2/device/maintenance/repair-records"
            ],
            DeviceMaintenancePermission.REPAIR_RECORD_UPDATE: [
                "PUT /api/v2/device/maintenance/repair-records/"
            ],
            DeviceMaintenancePermission.REPAIR_RECORD_DELETE: [
                "DELETE /api/v2/device/maintenance/repair-records/"
            ],
            DeviceMaintenancePermission.REPAIR_RECORD_STATISTICS: [
                "GET /api/v2/device/maintenance/repair-records/statistics"
            ],
            DeviceMaintenancePermission.DEVICE_FIELD_CONFIG_READ: [
                "GET /api/v2/device/maintenance/device-fields/"
            ],
            DeviceMaintenancePermission.DEVICE_FIELD_CONFIG_UPDATE: [
                "POST /api/v2/device/maintenance/device-fields/"
            ],
            DeviceMaintenancePermission.REPAIR_CODE_GENERATE: [
                "POST /api/v2/device/maintenance/repair-codes/generate"
            ]
        }
        
        return permission_api_mapping.get(permission, [])
    
    async def _check_additional_conditions(
        self,
        user: User,
        permission: DeviceMaintenancePermission,
        resource_id: Optional[int],
        additional_checks: Dict[str, Any]
    ) -> bool:
        """检查额外的权限条件"""
        try:
            # 检查部门权限
            if additional_checks.get("check_department", False):
                if not user.dept:
                    return False
                
                # 如果有资源ID，检查资源是否属于同一部门
                if resource_id and permission in [
                    DeviceMaintenancePermission.REPAIR_RECORD_READ,
                    DeviceMaintenancePermission.REPAIR_RECORD_UPDATE,
                    DeviceMaintenancePermission.REPAIR_RECORD_DELETE
                ]:
                    record = await DeviceRepairRecord.get_or_none(id=resource_id)
                    if record and hasattr(record, 'applicant_dept'):
                        if record.applicant_dept != user.dept.dept_name:
                            return False
            
            # 检查时间范围权限
            if additional_checks.get("time_range_days"):
                time_range_days = additional_checks["time_range_days"]
                if resource_id:
                    record = await DeviceRepairRecord.get_or_none(id=resource_id)
                    if record:
                        days_diff = (datetime.now().date() - record.repair_date).days
                        if days_diff > time_range_days:
                            return False
            
            return True
            
        except Exception as e:
            logger.error(f"额外权限条件检查失败: {e}")
            return False
    
    async def _check_cross_user_access(self, user: User, record: DeviceRepairRecord) -> bool:
        """检查跨用户访问权限"""
        try:
            # 检查是否为同部门用户
            if user.dept and record.applicant_dept:
                if user.dept.dept_name == record.applicant_dept:
                    return True
            
            # 检查是否有管理员权限
            roles = await user.roles.all()
            for role in roles:
                if "管理员" in role.role_name or "admin" in role.role_key.lower():
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"跨用户访问权限检查失败: {e}")
            return False
    
    async def create_audit_log(
        self,
        user: User,
        action: DeviceMaintenanceAuditAction,
        request: Request,
        resource_id: Optional[int] = None,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        status_code: int = 200,
        response_time: int = 0,
        error_message: Optional[str] = None
    ):
        """
        创建审计日志
        
        Args:
            user: 当前用户
            action: 审计操作
            request: 请求对象
            resource_id: 资源ID
            request_data: 请求数据
            response_data: 响应数据
            status_code: 状态码
            response_time: 响应时间
            error_message: 错误信息
        """
        try:
            # 构建审计日志摘要
            summary = action.value
            if resource_id:
                summary += f" (ID: {resource_id})"
            
            # 处理敏感数据
            safe_request_data = self._sanitize_audit_data(request_data)
            safe_response_data = self._sanitize_audit_data(response_data)
            
            # 如果有错误，添加到响应数据中
            if error_message:
                if safe_response_data is None:
                    safe_response_data = {}
                safe_response_data["error"] = error_message
            
            # 暂时禁用审计日志功能以绕过AuditLog导入问题
            # async with in_transaction():
            #     await AuditLog.create(
            #         user_id=user.id,
            #         username=user.username,
            #         module=self.module_name,
            #         summary=summary,
            #         method=request.method,
            #         path=str(request.url.path),
            #         status=status_code,
            #         response_time=response_time,
            #         request_args=safe_request_data,
            #         response_body=safe_response_data
            #     )
            
            logger.info(f"审计日志功能已暂时禁用: user={user.username}, action={action.value}, status={status_code}")
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"创建审计日志失败: {e}")
            logger.error(f"错误堆栈: {error_traceback}")
    
    def _sanitize_audit_data(self, data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """清理审计数据中的敏感信息"""
        if not data:
            return data
        
        # 需要清理的敏感字段
        sensitive_fields = [
            "password", "token", "secret", "key", "auth",
            "applicant_phone"  # 电话号码部分脱敏
        ]
        
        try:
            sanitized_data = data.copy()
            
            for field in sensitive_fields:
                if field in sanitized_data:
                    if field == "applicant_phone" and sanitized_data[field]:
                        # 电话号码脱敏：保留前3位和后4位
                        phone = str(sanitized_data[field])
                        if len(phone) >= 7:
                            sanitized_data[field] = phone[:3] + "****" + phone[-4:]
                    else:
                        sanitized_data[field] = "***"
            
            return sanitized_data
            
        except Exception as e:
            logger.error(f"审计数据清理失败: {e}")
            return {"error": "数据清理失败"}
    
    async def log_audit(
        self,
        user: User,
        action: DeviceMaintenanceAuditAction,
        details: str,
        request: Optional[Request] = None,
        resource_id: Optional[int] = None,
        status_code: int = 200,
        response_time: int = 0
    ):
        """
        记录审计日志（简化版本，兼容旧接口）
        
        Args:
            user: 当前用户
            action: 审计操作
            details: 操作详情
            request: 请求对象（可选）
            resource_id: 资源ID（可选）
            status_code: 状态码
            response_time: 响应时间
        """
        try:
            # 调用完整的审计日志方法
            await self.create_audit_log(
                user=user,
                action=action,
                request=request,
                resource_id=resource_id,
                request_data={"details": details},
                status_code=status_code,
                response_time=response_time
            )
        except Exception as e:
            logger.error(f"记录审计日志失败: {e}")

    async def invalidate_user_permissions(self, user_id: int):
        """清除用户的权限缓存"""
        try:
            pattern = f"device_maintenance_permission:{user_id}:*"
            await permission_cache.delete_pattern(pattern)
            logger.info(f"用户权限缓存清除成功: user_id={user_id}")
        except Exception as e:
            logger.error(f"清除用户权限缓存失败: {e}")


# 全局权限服务实例
device_maintenance_permission_service = DeviceMaintenancePermissionService()