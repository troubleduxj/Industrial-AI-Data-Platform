"""
数据权限过滤中间件
实现基于部门的数据权限过滤和SQL查询增强
"""

import logging
from typing import Optional, Dict, Any, List, Union
from fastapi import Request, HTTPException, status

from app.services.department_permission_service import department_permission_service
from app.models.admin import User, Department

logger = logging.getLogger(__name__)


class DataPermissionMiddleware:
    """数据权限过滤中间件"""
    
    def __init__(self):
        self.department_service = department_permission_service
    
    async def apply_department_filter(
        self, 
        query: Query, 
        user: User, 
        department_field: str = "department_id",
        table_alias: Optional[str] = None
    ) -> Query:
        """
        应用部门数据权限过滤
        
        Args:
            query: SQLAlchemy查询对象
            user: 当前用户
            department_field: 部门字段名
            table_alias: 表别名
            
        Returns:
            Query: 过滤后的查询对象
        """
        try:
            # 超级用户不需要过滤
            if user.is_superuser:
                return query
            
            # 获取用户可访问的部门列表
            accessible_departments = await self.department_service.get_accessible_departments(user.id)
            
            if not accessible_departments:
                # 如果用户没有任何部门权限，返回空结果
                return query.filter(text("1=0"))
            
            # 提取部门ID列表
            department_ids = [dept.get('id') for dept in accessible_departments if dept.get('id')]
            
            if not department_ids:
                return query.filter(text("1=0"))
            
            # 构建字段名
            field_name = f"{table_alias}.{department_field}" if table_alias else department_field
            
            # 应用部门过滤
            return query.filter(text(f"{field_name} IN :department_ids")).params(
                department_ids=tuple(department_ids)
            )
            
        except Exception as e:
            logger.error(f"应用部门数据权限过滤失败: error={str(e)}")
            # 出错时返回空结果，确保数据安全
            return query.filter(text("1=0"))
    
    async def check_data_access_permission(
        self, 
        user: User, 
        data_department_id: int,
        operation: str = "read"
    ) -> Dict[str, Any]:
        """
        检查数据访问权限
        
        Args:
            user: 当前用户
            data_department_id: 数据所属部门ID
            operation: 操作类型 (read, write, delete)
            
        Returns:
            Dict: 权限检查结果
        """
        try:
            # 超级用户拥有所有权限
            if user.is_superuser:
                return {
                    "allowed": True,
                    "reason": "super_user",
                    "message": "超级用户拥有所有数据访问权限"
                }
            
            # 检查用户是否有权限访问该部门的数据
            has_access = await self.department_service.check_department_access_permission(
                user.id, data_department_id
            )
            
            if not has_access:
                return {
                    "allowed": False,
                    "reason": "department_access_denied",
                    "message": f"用户无权限访问部门ID为{data_department_id}的数据"
                }
            
            # 根据操作类型检查具体权限
            scope_info = await self.department_service.get_user_department_scope(user.id)
            
            if operation == "write" and not scope_info.get("can_modify", False):
                return {
                    "allowed": False,
                    "reason": "write_permission_denied",
                    "message": "用户没有数据修改权限"
                }
            
            if operation == "delete" and not scope_info.get("can_delete", False):
                return {
                    "allowed": False,
                    "reason": "delete_permission_denied",
                    "message": "用户没有数据删除权限"
                }
            
            return {
                "allowed": True,
                "reason": "data_access_granted",
                "message": f"用户有权限对部门ID为{data_department_id}的数据执行{operation}操作"
            }
            
        except Exception as e:
            logger.error(f"检查数据访问权限失败: error={str(e)}")
            return {
                "allowed": False,
                "reason": "permission_check_error",
                "message": f"权限检查过程中发生错误: {str(e)}"
            }
    
    async def filter_data_by_department(
        self, 
        data_list: List[Dict[str, Any]], 
        user: User,
        department_field: str = "department_id"
    ) -> List[Dict[str, Any]]:
        """
        根据部门权限过滤数据列表
        
        Args:
            data_list: 数据列表
            user: 当前用户
            department_field: 部门字段名
            
        Returns:
            List: 过滤后的数据列表
        """
        try:
            # 超级用户不需要过滤
            if user.is_superuser:
                return data_list
            
            # 获取用户可访问的部门列表
            accessible_departments = await self.department_service.get_accessible_departments(user.id)
            department_ids = {dept.get('id') for dept in accessible_departments if dept.get('id')}
            
            if not department_ids:
                return []
            
            # 过滤数据
            filtered_data = []
            for item in data_list:
                item_dept_id = item.get(department_field)
                if item_dept_id in department_ids:
                    filtered_data.append(item)
            
            return filtered_data
            
        except Exception as e:
            logger.error(f"根据部门权限过滤数据失败: error={str(e)}")
            return []
    
    async def validate_batch_operation_permission(
        self, 
        user: User, 
        target_ids: List[int],
        get_department_func,
        operation: str = "delete"
    ) -> Dict[str, Any]:
        """
        验证批量操作权限
        
        Args:
            user: 当前用户
            target_ids: 目标数据ID列表
            get_department_func: 获取数据部门ID的函数
            operation: 操作类型
            
        Returns:
            Dict: 验证结果
        """
        try:
            # 超级用户拥有所有权限
            if user.is_superuser:
                return {
                    "allowed": True,
                    "reason": "super_user",
                    "message": "超级用户拥有批量操作权限",
                    "allowed_ids": target_ids,
                    "denied_ids": []
                }
            
            allowed_ids = []
            denied_ids = []
            
            # 逐个检查每个目标数据的权限
            for target_id in target_ids:
                try:
                    # 获取数据所属部门
                    department_id = await get_department_func(target_id)
                    
                    if department_id is None:
                        denied_ids.append(target_id)
                        continue
                    
                    # 检查权限
                    permission_result = await self.check_data_access_permission(
                        user, department_id, operation
                    )
                    
                    if permission_result.get("allowed", False):
                        allowed_ids.append(target_id)
                    else:
                        denied_ids.append(target_id)
                        
                except Exception as e:
                    logger.error(f"检查目标ID {target_id} 权限失败: error={str(e)}")
                    denied_ids.append(target_id)
            
            # 判断整体结果
            if not allowed_ids:
                return {
                    "allowed": False,
                    "reason": "no_permission_for_any_target",
                    "message": "用户对所有目标数据都没有操作权限",
                    "allowed_ids": [],
                    "denied_ids": denied_ids
                }
            
            if denied_ids:
                return {
                    "allowed": True,
                    "reason": "partial_permission",
                    "message": f"用户对部分数据有操作权限，允许操作{len(allowed_ids)}个，拒绝{len(denied_ids)}个",
                    "allowed_ids": allowed_ids,
                    "denied_ids": denied_ids
                }
            
            return {
                "allowed": True,
                "reason": "full_permission",
                "message": "用户对所有目标数据都有操作权限",
                "allowed_ids": allowed_ids,
                "denied_ids": []
            }
            
        except Exception as e:
            logger.error(f"验证批量操作权限失败: error={str(e)}")
            return {
                "allowed": False,
                "reason": "validation_error",
                "message": f"权限验证过程中发生错误: {str(e)}",
                "allowed_ids": [],
                "denied_ids": target_ids
            }
    
    async def get_department_data_statistics(
        self, 
        user: User
    ) -> Dict[str, Any]:
        """
        获取用户可访问的部门数据统计
        
        Args:
            user: 当前用户
            
        Returns:
            Dict: 数据统计结果
        """
        try:
            # 获取用户可访问的部门列表
            accessible_departments = await self.tenant_service.get_accessible_departments(user.id)
            
            # 获取用户权限范围信息
            scope_info = await self.tenant_service.get_user_department_scope(user.id)
            
            return {
                "success": True,
                "message": "获取部门数据统计成功",
                "data": {
                    "accessible_departments": accessible_departments,
                    "department_count": len(accessible_departments),
                    "scope_info": scope_info,
                    "permissions": {
                        "can_read": True,  # 基本读取权限
                        "can_modify": scope_info.get("can_modify", False),
                        "can_delete": scope_info.get("can_delete", False),
                        "can_cross_department": scope_info.get("can_cross_department", False)
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"获取部门数据统计失败: error={str(e)}")
            return {
                "success": False,
                "message": f"获取数据统计失败: {str(e)}",
                "data": {}
            }
    
    def create_department_filter_condition(
        self, 
        department_ids: List[int], 
        department_field: str = "department_id",
        table_alias: Optional[str] = None
    ) -> str:
        """
        创建部门过滤条件的SQL片段
        
        Args:
            department_ids: 部门ID列表
            department_field: 部门字段名
            table_alias: 表别名
            
        Returns:
            str: SQL条件片段
        """
        if not department_ids:
            return "1=0"  # 没有权限时返回false条件
        
        field_name = f"{table_alias}.{department_field}" if table_alias else department_field
        ids_str = ",".join(str(id) for id in department_ids)
        
        return f"{field_name} IN ({ids_str})"


# 创建全局实例
data_permission_middleware = DataPermissionMiddleware()


# 装饰器函数
def require_data_permission(
    department_field: str = "department_id",
    operation: str = "read"
):
    """
    数据权限装饰器
    
    Args:
        department_field: 部门字段名
        operation: 操作类型
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 这里需要根据具体的函数签名来获取user和数据
            # 简化实现，实际使用时需要根据具体情况调整
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def apply_department_data_filter(
    department_field: str = "department_id",
    table_alias: Optional[str] = None
):
    """
    应用部门数据过滤装饰器
    
    Args:
        department_field: 部门字段名
        table_alias: 表别名
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 获取查询对象和用户信息
            # 这里需要根据具体的函数实现来调整
            result = await func(*args, **kwargs)
            
            # 如果结果是Query对象，应用过滤
            if hasattr(result, 'filter'):
                # 需要获取当前用户信息
                # user = await get_current_user()
                # result = await data_permission_middleware.apply_department_filter(
                #     result, user, department_field, table_alias
                # )
                pass
            
            return result
        return wrapper
    return decorator