"""
部门权限服务
实现部门数据权限范围控制和跨部门访问权限验证
"""

import logging
from typing import List, Optional, Dict, Any, Set
from tortoise.expressions import Q
from tortoise.queryset import QuerySet

from app.models.admin import User, Role, Dept
from app.core.permission_cache import permission_cache_manager
from app.services.permission_service import PermissionService

logger = logging.getLogger(__name__)


class DepartmentPermissionService:
    """部门权限服务"""
    
    def __init__(self):
        self.permission_service = PermissionService()
    
    async def get_user_department_scope(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户的部门权限范围
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 部门权限范围信息
        """
        try:
            # 从缓存获取
            cache_key = f"user_department_scope:{user_id}"
            cached_scope = await permission_cache_manager.get(cache_key)
            if cached_scope:
                return cached_scope
            
            user = await User.get_or_none(id=user_id).prefetch_related('dept', 'roles')
            if not user:
                return {
                    "departments": [], 
                    "scope_type": "none", 
                    "can_cross_department": False,
                    "can_modify": False,
                    "can_delete": False
                }
            
            # 获取用户所属部门
            user_department = user.dept
            department_ids = []
            department_names = []
            
            if user_department:
                department_ids.append(user_department.id)
                department_names.append(user_department.dept_name)
            
            # 获取用户角色的数据范围权限
            role_departments = await self._get_role_department_scope(user)
            department_ids.extend(role_departments.get("department_ids", []))
            department_names.extend(role_departments.get("department_names", []))
            
            # 去重
            department_ids = list(set(department_ids))
            department_names = list(set(department_names))
            
            # 确定权限范围类型
            scope_type = self._determine_scope_type(user, department_ids)
            
            # 检查是否可以跨部门访问
            can_cross_department = await self._check_cross_department_permission(user)
            
            # 检查操作权限
            can_modify = await self._check_operation_permission(user, "modify")
            can_delete = await self._check_operation_permission(user, "delete")
            
            scope_info = {
                "departments": department_ids,
                "department_names": department_names,
                "scope_type": scope_type,
                "can_cross_department": can_cross_department,
                "can_modify": can_modify,
                "can_delete": can_delete,
                "is_super_user": user.is_superuser,
                "user_id": user_id
            }
            
            # 缓存结果
            await permission_cache_manager.set(cache_key, scope_info, ttl=300)  # 5分钟缓存
            
            logger.info(f"获取用户部门权限范围成功: user_id={user_id}, scope={scope_info}")
            return scope_info
            
        except Exception as e:
            logger.error(f"获取用户部门权限范围失败: user_id={user_id}, error={str(e)}")
            return {
                "departments": [], 
                "scope_type": "none", 
                "can_cross_department": False,
                "can_modify": False,
                "can_delete": False
            }
    
    async def _get_role_department_scope(self, user: User) -> Dict[str, Any]:
        """
        获取用户角色的部门权限范围
        
        Args:
            user: 用户对象
            
        Returns:
            Dict: 角色部门权限信息
        """
        department_ids = []
        department_names = []
        
        try:
            for role in await user.roles.all():
                # 根据角色的数据范围(data_scope)确定可访问的部门
                data_scope = role.data_scope
                
                if data_scope == "1":  # 全部数据权限
                    all_depts = await Dept.all()
                    department_ids.extend([dept.id for dept in all_depts])
                    department_names.extend([dept.dept_name for dept in all_depts])
                elif data_scope == "2":  # 自定义部门数据权限
                    # 这里需要查询角色关联的部门，暂时简化处理
                    pass
                elif data_scope == "3":  # 本部门数据权限
                    if user.dept:
                        department_ids.append(user.dept.id)
                        department_names.append(user.dept.dept_name)
                elif data_scope == "4":  # 本部门及以下数据权限
                    if user.dept:
                        # 获取本部门及其子部门
                        child_depts = await self._get_department_children(user.dept.id)
                        department_ids.extend([dept.id for dept in child_depts])
                        department_names.extend([dept.dept_name for dept in child_depts])
                elif data_scope == "5":  # 仅本人数据权限
                    # 这种情况下不添加部门权限，只能访问自己的数据
                    pass
                    
        except Exception as e:
            logger.error(f"获取角色部门权限范围失败: user_id={user.id}, error={str(e)}")
        
        return {
            "department_ids": list(set(department_ids)),
            "department_names": list(set(department_names))
        }
    
    async def _get_department_children(self, department_id: int) -> List[Dept]:
        """
        获取部门及其所有子部门
        
        Args:
            department_id: 部门ID
            
        Returns:
            List[Dept]: 部门及子部门列表
        """
        try:
            # 获取当前部门
            current_dept = await Dept.get_or_none(id=department_id)
            if not current_dept:
                return []
            
            departments = [current_dept]
            
            # 递归获取子部门
            child_depts = await Dept.filter(parent_id=department_id)
            for child in child_depts:
                child_departments = await self._get_department_children(child.id)
                departments.extend(child_departments)
            
            return departments
            
        except Exception as e:
            logger.error(f"获取部门子部门失败: department_id={department_id}, error={str(e)}")
            return []
    
    def _determine_scope_type(self, user: User, department_ids: List[int]) -> str:
        """
        确定权限范围类型
        
        Args:
            user: 用户对象
            department_ids: 部门ID列表
            
        Returns:
            str: 权限范围类型
        """
        if user.is_superuser:
            return "global"  # 全局权限
        
        if not department_ids:
            return "none"  # 无部门权限
        
        if len(department_ids) == 1:
            return "single"  # 单部门权限
        
        return "multiple"  # 多部门权限
    
    async def _check_cross_department_permission(self, user: User) -> bool:
        """
        检查用户是否有跨部门访问权限
        
        Args:
            user: 用户对象
            
        Returns:
            bool: 是否可以跨部门访问
        """
        if user.is_superuser:
            return True
        
        # 检查用户角色的数据范围
        for role in await user.roles.all():
            data_scope = role.data_scope
            # 全部数据权限或自定义部门权限允许跨部门访问
            if data_scope in ["1", "2"]:
                return True
        
        return False
    
    async def _check_operation_permission(self, user: User, operation: str) -> bool:
        """
        检查用户的操作权限
        
        Args:
            user: 用户对象
            operation: 操作类型 (modify, delete)
            
        Returns:
            bool: 是否有操作权限
        """
        if user.is_superuser:
            return True
        
        try:
            # 获取用户权限
            user_permissions = await self.permission_service.get_user_permissions(user.id)
            
            # 检查是否有相应的操作权限
            operation_permissions = {
                "modify": ["data:write", "data:edit", "data:update"],
                "delete": ["data:delete", "data:remove"]
            }
            
            required_permissions = operation_permissions.get(operation, [])
            user_permission_keys = [perm.get("permission_key", "") for perm in user_permissions]
            
            return any(perm in user_permission_keys for perm in required_permissions)
            
        except Exception as e:
            logger.error(f"检查操作权限失败: user_id={user.id}, operation={operation}, error={str(e)}")
            return False
    
    async def filter_data_by_department_scope(
        self, 
        queryset: QuerySet, 
        user_id: int, 
        department_field: str = "department_id"
    ) -> QuerySet:
        """
        根据部门权限范围过滤数据
        
        Args:
            queryset: 查询集
            user_id: 用户ID
            department_field: 部门字段名
            
        Returns:
            QuerySet: 过滤后的查询集
        """
        try:
            scope_info = await self.get_user_department_scope(user_id)
            
            # 超级用户可以访问所有数据
            if scope_info.get("is_super_user"):
                return queryset
            
            # 无部门权限，返回空结果
            if scope_info.get("scope_type") == "none":
                return queryset.filter(id__in=[])  # 返回空查询集
            
            # 根据部门范围过滤
            department_ids = scope_info.get("departments", [])
            if department_ids:
                return queryset.filter(**{f"{department_field}__in": department_ids})
            
            return queryset.filter(id__in=[])  # 返回空查询集
            
        except Exception as e:
            logger.error(f"部门权限数据过滤失败: user_id={user_id}, error={str(e)}")
            return queryset.filter(id__in=[])  # 出错时返回空查询集，确保安全
    
    async def check_department_access_permission(
        self, 
        user_id: int, 
        target_department_id: int
    ) -> bool:
        """
        检查用户是否有权限访问指定部门的数据
        
        Args:
            user_id: 用户ID
            target_department_id: 目标部门ID
            
        Returns:
            bool: 是否有权限访问
        """
        try:
            scope_info = await self.get_user_department_scope(user_id)
            
            # 超级用户可以访问所有部门
            if scope_info.get("is_super_user"):
                return True
            
            # 检查目标部门是否在用户权限范围内
            user_departments = scope_info.get("departments", [])
            if target_department_id in user_departments:
                return True
            
            # 检查是否有跨部门访问权限
            if scope_info.get("can_cross_department"):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"检查部门访问权限失败: user_id={user_id}, dept_id={target_department_id}, error={str(e)}")
            return False
    
    async def get_accessible_departments(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户可访问的部门列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[Dict]: 可访问的部门列表
        """
        try:
            scope_info = await self.get_user_department_scope(user_id)
            
            # 超级用户可以访问所有部门
            if scope_info.get("is_super_user"):
                departments = await Dept.all()
                return [
                    {
                        "id": dept.id,
                        "name": dept.dept_name,
                        "parent_id": dept.parent_id,
                        "order_num": dept.order_num,
                        "leader": dept.leader,
                        "status": dept.status
                    }
                    for dept in departments
                ]
            
            # 获取用户权限范围内的部门
            department_ids = scope_info.get("departments", [])
            if not department_ids:
                return []
            
            departments = await Dept.filter(id__in=department_ids)
            
            return [
                {
                    "id": dept.id,
                    "name": dept.dept_name,
                    "parent_id": dept.parent_id,
                    "order_num": dept.order_num,
                    "leader": dept.leader,
                    "status": dept.status
                }
                for dept in departments
            ]
            
        except Exception as e:
            logger.error(f"获取可访问部门列表失败: user_id={user_id}, error={str(e)}")
            return []
    
    async def validate_data_access_permission(
        self, 
        user_id: int, 
        data_department_id: int, 
        operation: str = "read"
    ) -> Dict[str, Any]:
        """
        验证数据访问权限
        
        Args:
            user_id: 用户ID
            data_department_id: 数据所属部门ID
            operation: 操作类型 (read, write, delete)
            
        Returns:
            Dict: 权限验证结果
        """
        try:
            # 检查部门访问权限
            has_access = await self.check_department_access_permission(user_id, data_department_id)
            
            if not has_access:
                return {
                    "allowed": False,
                    "reason": "department_access_denied",
                    "message": f"用户无权限访问部门ID为{data_department_id}的数据"
                }
            
            # 检查操作权限
            scope_info = await self.get_user_department_scope(user_id)
            
            # 超级用户拥有所有操作权限
            if scope_info.get("is_super_user"):
                return {
                    "allowed": True,
                    "reason": "super_user",
                    "message": "超级用户拥有所有权限"
                }
            
            # 根据操作类型检查权限
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
            logger.error(f"验证数据访问权限失败: user_id={user_id}, dept_id={data_department_id}, error={str(e)}")
            return {
                "allowed": False,
                "reason": "validation_error",
                "message": f"权限验证过程中发生错误: {str(e)}"
            }
    
    async def clear_user_department_cache(self, user_id: int):
        """
        清除用户部门权限缓存
        
        Args:
            user_id: 用户ID
        """
        try:
            cache_key = f"user_department_scope:{user_id}"
            await permission_cache_manager.delete(cache_key)
            logger.info(f"清除用户部门权限缓存成功: user_id={user_id}")
        except Exception as e:
            logger.error(f"清除用户部门权限缓存失败: user_id={user_id}, error={str(e)}")
    
    async def refresh_department_permissions(self, department_id: int):
        """
        刷新部门相关的权限缓存
        
        Args:
            department_id: 部门ID
        """
        try:
            # 获取该部门的所有用户
            users = await User.filter(dept_id=department_id)
            
            # 清除所有相关用户的部门权限缓存
            for user in users:
                await self.clear_user_department_cache(user.id)
            
            logger.info(f"刷新部门权限缓存成功: department_id={department_id}, affected_users={len(users)}")
            
        except Exception as e:
            logger.error(f"刷新部门权限缓存失败: department_id={department_id}, error={str(e)}")


# 创建全局实例
department_permission_service = DepartmentPermissionService()