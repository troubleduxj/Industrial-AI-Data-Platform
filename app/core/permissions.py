"""
批量删除权限控制系统

实现细粒度的批量删除权限控制，包括：
- 权限装饰器和中间件
- 批量删除特定权限检查
- 权限缓存和优化
- 与现有权限系统的集成

需求映射：
- 需求6.1: 前端权限控制
- 需求6.2: 后端权限验证
- 需求6.3: 细粒度权限检查
- 需求6.5: 权限一致性
"""

from typing import List, Dict, Any, Optional, Callable, Union
from functools import wraps
from enum import Enum
import logging

from fastapi import Request, HTTPException, Depends
from tortoise.models import Model

from app.models.admin import User, Role, SysApiEndpoint
from app.core.dependency import AuthControl
from app.core.cache import permission_cache

logger = logging.getLogger(__name__)


class BatchDeletePermission(Enum):
    """批量删除权限枚举"""
    
    # API管理批量删除权限
    API_BATCH_DELETE = "api:batch_delete"
    
    # 字典类型批量删除权限
    DICT_TYPE_BATCH_DELETE = "dict_type:batch_delete"
    
    # 字典数据批量删除权限
    DICT_DATA_BATCH_DELETE = "dict_data:batch_delete"
    
    # 系统参数批量删除权限
    SYSTEM_PARAM_BATCH_DELETE = "system_param:batch_delete"
    
    # 部门批量删除权限
    DEPT_BATCH_DELETE = "dept:batch_delete"
    
    # 用户批量删除权限
    USER_BATCH_DELETE = "user:batch_delete"
    
    # 角色批量删除权限
    ROLE_BATCH_DELETE = "role:batch_delete"
    
    # 菜单批量删除权限
    MENU_BATCH_DELETE = "menu:batch_delete"


class PermissionCondition(Enum):
    """权限条件枚举"""
    
    # 排除系统内置项
    EXCLUDE_SYSTEM_ITEMS = "exclude_system_items"
    
    # 排除被引用项
    EXCLUDE_REFERENCED_ITEMS = "exclude_referenced_items"
    
    # 仅限自己创建的项
    ONLY_OWN_ITEMS = "only_own_items"
    
    # 仅限部门内项目
    ONLY_DEPT_ITEMS = "only_dept_items"


class BatchDeletePermissionChecker:
    """批量删除权限检查器"""
    
    def __init__(self):
        self.cache_ttl = 300  # 5分钟缓存
    
    async def check_batch_delete_permission(
        self,
        user: User,
        resource_type: str,
        action: str = "batch_delete",
        conditions: Optional[List[PermissionCondition]] = None
    ) -> tuple[bool, Optional[str]]:
        """
        检查用户是否有批量删除权限
        
        Args:
            user: 当前用户
            resource_type: 资源类型 (api, dict_type, dict_data, system_param等)
            action: 操作类型，默认为batch_delete
            conditions: 权限条件列表
            
        Returns:
            tuple: (是否有权限, 权限不足的原因)
        """
        try:
            # 1. 超级管理员直接通过
            if user.is_superuser:
                return True, None
            
            # 2. 构建权限标识
            permission_key = f"{resource_type}:{action}"
            
            # 3. 尝试从缓存获取权限结果
            cached_result = await self._get_cached_permission(user.id, permission_key)
            if cached_result is not None:
                return cached_result, None if cached_result else f"缺少权限: {permission_key}"
            
            # 4. 从数据库检查权限
            has_permission = await self._check_permission_from_db(user, permission_key)
            
            # 5. 检查权限条件
            if has_permission and conditions:
                condition_result = await self._check_permission_conditions(user, resource_type, conditions)
                if not condition_result:
                    has_permission = False
            
            # 6. 缓存结果
            await self._cache_permission_result(user.id, permission_key, has_permission)
            
            return has_permission, None if has_permission else f"缺少权限: {permission_key}"
            
        except Exception as e:
            logger.error(f"权限检查失败 user_id={user.id}, resource={resource_type}: {e}")
            return False, f"权限检查失败: {str(e)}"
    
    async def check_item_delete_permission(
        self,
        user: User,
        item: Model,
        resource_type: str,
        conditions: Optional[List[PermissionCondition]] = None
    ) -> tuple[bool, Optional[str]]:
        """
        检查用户是否有删除特定项目的权限
        
        Args:
            user: 当前用户
            item: 要删除的项目
            resource_type: 资源类型
            conditions: 权限条件列表
            
        Returns:
            tuple: (是否有权限, 权限不足的原因)
        """
        try:
            # 1. 首先检查基本的批量删除权限
            has_basic_permission, reason = await self.check_batch_delete_permission(
                user, resource_type, "batch_delete", conditions
            )
            
            if not has_basic_permission:
                return False, reason
            
            # 2. 检查项目级别的权限条件
            if conditions:
                for condition in conditions:
                    condition_result, condition_reason = await self._check_item_condition(
                        user, item, condition
                    )
                    if not condition_result:
                        return False, condition_reason
            
            return True, None
            
        except Exception as e:
            logger.error(f"项目权限检查失败 user_id={user.id}, item_id={item.id}: {e}")
            return False, f"项目权限检查失败: {str(e)}"
    
    async def _check_permission_from_db(self, user: User, permission_key: str) -> bool:
        """从数据库检查权限"""
        try:
            # 获取用户角色
            roles = await user.roles.all()
            if not roles:
                return False
            
            # 检查角色是否有对应的API权限
            # 这里需要根据实际的权限系统实现
            # 目前简化为检查是否有相关的API端点权限
            
            # 构建对应的API路径模式
            api_patterns = self._get_api_patterns_for_permission(permission_key)
            
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
    
    def _get_api_patterns_for_permission(self, permission_key: str) -> List[str]:
        """获取权限对应的API路径模式"""
        permission_api_mapping = {
            "api:batch_delete": ["DELETE /api/v2/apis/batch"],
            "dict_type:batch_delete": ["DELETE /api/v2/dict-types/batch"],
            "dict_data:batch_delete": ["DELETE /api/v2/dict-data/batch"],
            "system_param:batch_delete": ["DELETE /api/v2/system-params/batch"],
            "dept:batch_delete": ["DELETE /api/v2/departments/batch"],
            "user:batch_delete": ["DELETE /api/v2/users/batch"],
            "role:batch_delete": ["DELETE /api/v2/roles/batch"],
            "menu:batch_delete": ["DELETE /api/v2/menus/batch"],
        }
        
        return permission_api_mapping.get(permission_key, [])
    
    async def _check_permission_conditions(
        self,
        user: User,
        resource_type: str,
        conditions: List[PermissionCondition]
    ) -> bool:
        """检查权限条件"""
        for condition in conditions:
            if condition == PermissionCondition.EXCLUDE_SYSTEM_ITEMS:
                # 检查是否有删除系统项的权限
                if not user.is_superuser:
                    continue  # 非超级管理员不能删除系统项，这是正常的
            
            elif condition == PermissionCondition.EXCLUDE_REFERENCED_ITEMS:
                # 检查是否有删除被引用项的权限
                # 这通常需要更高级的权限
                continue
            
            elif condition == PermissionCondition.ONLY_OWN_ITEMS:
                # 检查是否只能删除自己创建的项目
                # 这需要在项目级别检查
                continue
            
            elif condition == PermissionCondition.ONLY_DEPT_ITEMS:
                # 检查是否只能删除部门内的项目
                if not user.dept:
                    return False
        
        return True
    
    async def _check_item_condition(
        self,
        user: User,
        item: Model,
        condition: PermissionCondition
    ) -> tuple[bool, Optional[str]]:
        """检查单个项目的权限条件"""
        if condition == PermissionCondition.EXCLUDE_SYSTEM_ITEMS:
            # 检查是否为系统内置项
            if hasattr(item, 'is_system') and getattr(item, 'is_system'):
                if not user.is_superuser:
                    return False, "系统内置项不允许删除"
        
        elif condition == PermissionCondition.EXCLUDE_REFERENCED_ITEMS:
            # 检查是否被其他项目引用
            # 这需要根据具体的业务逻辑实现
            pass
        
        elif condition == PermissionCondition.ONLY_OWN_ITEMS:
            # 检查是否为用户自己创建的项目
            if hasattr(item, 'created_by') and getattr(item, 'created_by') != user.id:
                return False, "只能删除自己创建的项目"
        
        elif condition == PermissionCondition.ONLY_DEPT_ITEMS:
            # 检查是否为同部门的项目
            if hasattr(item, 'dept_id') and user.dept:
                if getattr(item, 'dept_id') != user.dept.id:
                    return False, "只能删除本部门的项目"
        
        return True, None
    
    async def _get_cached_permission(self, user_id: int, permission_key: str) -> Optional[bool]:
        """从缓存获取权限结果"""
        try:
            cache_key = f"batch_delete_permission:{user_id}:{permission_key}"
            return await permission_cache.get(cache_key)
        except Exception as e:
            logger.error(f"获取权限缓存失败: {e}")
            return None
    
    async def _cache_permission_result(self, user_id: int, permission_key: str, result: bool):
        """缓存权限结果"""
        try:
            cache_key = f"batch_delete_permission:{user_id}:{permission_key}"
            await permission_cache.set(cache_key, result, ttl=self.cache_ttl)
        except Exception as e:
            logger.error(f"缓存权限结果失败: {e}")
    
    async def invalidate_user_permissions(self, user_id: int):
        """清除用户的权限缓存"""
        try:
            pattern = f"batch_delete_permission:{user_id}:*"
            await permission_cache.delete_pattern(pattern)
        except Exception as e:
            logger.error(f"清除用户权限缓存失败: {e}")


# 全局权限检查器实例
batch_delete_permission_checker = BatchDeletePermissionChecker()


def require_batch_delete_permission(
    resource_type: str,
    conditions: Optional[List[PermissionCondition]] = None
):
    """
    批量删除权限装饰器
    
    Args:
        resource_type: 资源类型
        conditions: 权限条件列表
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中获取request和current_user
            request = None
            current_user = None
            
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                elif isinstance(arg, User):
                    current_user = arg
            
            # 从kwargs中获取
            if not request:
                request = kwargs.get('request')
            if not current_user:
                current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(status_code=401, detail="未认证用户")
            
            # 检查权限
            has_permission, reason = await batch_delete_permission_checker.check_batch_delete_permission(
                current_user, resource_type, "batch_delete", conditions
            )
            
            if not has_permission:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": f"批量删除{resource_type}权限不足",
                        "reason": reason,
                        "error_code": "BATCH_DELETE_PERMISSION_DENIED"
                    }
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


async def check_batch_delete_permission_dependency(
    resource_type: str,
    conditions: Optional[List[PermissionCondition]] = None
):
    """
    批量删除权限依赖函数
    
    Args:
        resource_type: 资源类型
        conditions: 权限条件列表
    """
    async def permission_checker(current_user: User = Depends(AuthControl.is_authed)):
        has_permission, reason = await batch_delete_permission_checker.check_batch_delete_permission(
            current_user, resource_type, "batch_delete", conditions
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=403,
                detail={
                    "message": f"批量删除{resource_type}权限不足",
                    "reason": reason,
                    "error_code": "BATCH_DELETE_PERMISSION_DENIED"
                }
            )
        
        return True
    
    return permission_checker


class BatchDeletePermissionMiddleware:
    """批量删除权限中间件"""
    
    def __init__(self):
        self.permission_checker = batch_delete_permission_checker
        
        # 定义需要权限检查的路径模式
        self.protected_paths = {
            "/api/v2/apis/batch": ("api", "batch_delete"),
            "/api/v2/dict-types/batch": ("dict_type", "batch_delete"),
            "/api/v2/dict-data/batch": ("dict_data", "batch_delete"),
            "/api/v2/system-params/batch": ("system_param", "batch_delete"),
            "/api/v2/departments/batch": ("dept", "batch_delete"),
            "/api/v2/users/batch": ("user", "batch_delete"),
            "/api/v2/roles/batch": ("role", "batch_delete"),
            "/api/v2/menus/batch": ("menu", "batch_delete"),
        }
    
    async def check_request_permission(self, request: Request, current_user: User) -> tuple[bool, Optional[str]]:
        """检查请求权限"""
        path = request.url.path
        method = request.method
        
        # 只检查DELETE方法的批量操作
        if method != "DELETE":
            return True, None
        
        # 检查是否为受保护的路径
        if path in self.protected_paths:
            resource_type, action = self.protected_paths[path]
            return await self.permission_checker.check_batch_delete_permission(
                current_user, resource_type, action
            )
        
        return True, None


# 权限工具函数

async def has_batch_delete_permission(
    user: User,
    resource_type: str,
    conditions: Optional[List[PermissionCondition]] = None
) -> bool:
    """
    检查用户是否有批量删除权限的便捷函数
    
    Args:
        user: 用户对象
        resource_type: 资源类型
        conditions: 权限条件列表
        
    Returns:
        bool: 是否有权限
    """
    has_permission, _ = await batch_delete_permission_checker.check_batch_delete_permission(
        user, resource_type, "batch_delete", conditions
    )
    return has_permission


async def get_user_batch_delete_permissions(user: User) -> Dict[str, bool]:
    """
    获取用户的所有批量删除权限
    
    Args:
        user: 用户对象
        
    Returns:
        dict: 权限映射字典
    """
    permissions = {}
    
    resource_types = [
        "api", "dict_type", "dict_data", "system_param",
        "dept", "user", "role", "menu"
    ]
    
    for resource_type in resource_types:
        has_permission = await has_batch_delete_permission(user, resource_type)
        permissions[f"{resource_type}:batch_delete"] = has_permission
    
    return permissions


async def invalidate_user_batch_delete_permissions(user_id: int):
    """
    清除用户的批量删除权限缓存
    
    Args:
        user_id: 用户ID
    """
    await batch_delete_permission_checker.invalidate_user_permissions(user_id)


# 预定义的权限条件组合

STANDARD_CONDITIONS = [
    PermissionCondition.EXCLUDE_SYSTEM_ITEMS,
    PermissionCondition.EXCLUDE_REFERENCED_ITEMS
]

STRICT_CONDITIONS = [
    PermissionCondition.EXCLUDE_SYSTEM_ITEMS,
    PermissionCondition.EXCLUDE_REFERENCED_ITEMS,
    PermissionCondition.ONLY_OWN_ITEMS
]

DEPT_CONDITIONS = [
    PermissionCondition.EXCLUDE_SYSTEM_ITEMS,
    PermissionCondition.EXCLUDE_REFERENCED_ITEMS,
    PermissionCondition.ONLY_DEPT_ITEMS
]