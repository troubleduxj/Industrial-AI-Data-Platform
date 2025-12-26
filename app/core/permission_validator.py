#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限验证核心逻辑
提供权限验证、角色权限合并、权限继承等核心功能
"""

import asyncio
from typing import Dict, List, Optional, Set, Any, Union, Tuple
from datetime import datetime
from dataclasses import dataclass

from app.models.admin import User, Role, SysApiEndpoint, Menu
from app.core.permission_config_manager_v2 import permission_config_manager
from app.core.permission_cache import permission_cache_manager
from app.log import logger


@dataclass
class PermissionResult:
    """权限验证结果"""
    has_permission: bool
    reason: str
    matched_permissions: List[str]
    user_permissions: Set[str]
    required_permission: str


@dataclass
class UserPermissionInfo:
    """用户权限信息"""
    user_id: int
    username: str
    roles: List[Dict[str, Any]]
    permissions: Set[str]
    is_superuser: bool
    is_active: bool


class PermissionValidator:
    """权限验证器"""
    
    def __init__(self):
        self.config_manager = permission_config_manager
        self.cache_manager = permission_cache_manager
        
        # 超级管理员权限标识
        self.super_permissions = {"ADMIN", "*", "SUPERUSER"}
        
        # 权限继承规则
        self.permission_inheritance = {
            # 读权限可以继承到详情查看
            "read": ["detail", "view", "info"],
            # 创建权限可以继承到批量创建
            "create": ["batch-create", "import"],
            # 更新权限可以继承到批量更新
            "update": ["batch-update", "edit"],
            # 删除权限可以继承到批量删除
            "delete": ["batch-delete", "remove"],
            # 管理权限可以继承到所有操作
            "manage": ["read", "create", "update", "delete", "detail", "batch"]
        }
    
    async def has_permission(
        self, 
        user_permissions: List[str], 
        required_permission: str,
        check_inheritance: bool = True
    ) -> bool:
        """
        基础权限验证
        
        Args:
            user_permissions: 用户权限列表
            required_permission: 需要的权限
            check_inheritance: 是否检查权限继承
            
        Returns:
            是否有权限
        """
        try:
            user_permission_set = set(user_permissions)
            
            # 1. 直接匹配
            if required_permission in user_permission_set:
                return True
            
            # 2. 检查超级管理员权限
            if self.super_permissions.intersection(user_permission_set):
                return True
            
            # 3. 检查迁移后的权限
            migrated_permission = self.config_manager.migrate_permission(required_permission)
            if migrated_permission != required_permission and migrated_permission in user_permission_set:
                return True
            
            # 4. 检查权限继承
            if check_inheritance and await self._check_permission_inheritance(
                user_permission_set, required_permission
            ):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"权限验证失败: {required_permission}, 错误: {str(e)}")
            return False
    
    async def validate_user_permissions(
        self, 
        user_id: int, 
        required_permissions: Union[str, List[str]],
        require_all: bool = False
    ) -> PermissionResult:
        """
        验证用户权限（增强版）
        
        Args:
            user_id: 用户ID
            required_permissions: 需要的权限（单个或列表）
            require_all: 是否需要所有权限（True）还是任一权限（False）
            
        Returns:
            权限验证结果
        """
        try:
            # 标准化权限列表
            if isinstance(required_permissions, str):
                required_permissions = [required_permissions]
            
            # 获取用户权限信息
            user_permission_info = await self.get_user_permission_info(user_id)
            if not user_permission_info:
                return PermissionResult(
                    has_permission=False,
                    reason="用户不存在或未激活",
                    matched_permissions=[],
                    user_permissions=set(),
                    required_permission=str(required_permissions)
                )
            
            # 检查用户是否激活
            if not user_permission_info.is_active:
                return PermissionResult(
                    has_permission=False,
                    reason="用户未激活",
                    matched_permissions=[],
                    user_permissions=user_permission_info.permissions,
                    required_permission=str(required_permissions)
                )
            
            # 超级管理员直接通过
            if user_permission_info.is_superuser:
                return PermissionResult(
                    has_permission=True,
                    reason="超级管理员权限",
                    matched_permissions=required_permissions,
                    user_permissions=user_permission_info.permissions,
                    required_permission=str(required_permissions)
                )
            
            # 验证权限
            matched_permissions = []
            for permission in required_permissions:
                if await self.has_permission(
                    list(user_permission_info.permissions), 
                    permission
                ):
                    matched_permissions.append(permission)
            
            # 判断结果
            if require_all:
                has_permission = len(matched_permissions) == len(required_permissions)
                reason = "所有权限验证通过" if has_permission else f"缺少权限: {set(required_permissions) - set(matched_permissions)}"
            else:
                has_permission = len(matched_permissions) > 0
                reason = "权限验证通过" if has_permission else "无任何匹配权限"
            
            return PermissionResult(
                has_permission=has_permission,
                reason=reason,
                matched_permissions=matched_permissions,
                user_permissions=user_permission_info.permissions,
                required_permission=str(required_permissions)
            )
            
        except Exception as e:
            logger.error(f"验证用户权限失败: user_id={user_id}, permissions={required_permissions}, 错误: {str(e)}")
            return PermissionResult(
                has_permission=False,
                reason=f"权限验证异常: {str(e)}",
                matched_permissions=[],
                user_permissions=set(),
                required_permission=str(required_permissions)
            )
    
    async def get_user_permission_info(self, user_id: int) -> Optional[UserPermissionInfo]:
        """
        获取用户权限信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户权限信息
        """
        try:
            # 先尝试从缓存获取
            cached_info = await self.cache_manager.get_user_permissions(user_id)
            if cached_info and self._is_cache_valid(cached_info):
                return self._build_user_permission_info_from_cache(cached_info)
            
            # 从数据库获取
            user = await User.get_or_none(id=user_id).prefetch_related("roles__apis", "roles__menus")
            if not user:
                return None
            
            # 获取角色信息
            roles_info = []
            all_permissions = set()
            
            for role in user.roles:
                role_info = {
                    "id": role.id,
                    "name": role.role_name,
                    "desc": role.desc
                }
                roles_info.append(role_info)
                
                # 收集角色权限
                role_permissions = await self._get_role_permissions(role)
                all_permissions.update(role_permissions)
            
            # 构建用户权限信息
            user_permission_info = UserPermissionInfo(
                user_id=user.id,
                username=user.username,
                roles=roles_info,
                permissions=all_permissions,
                is_superuser=user.is_superuser,
                is_active=user.is_active
            )
            
            # 缓存权限信息
            await self._cache_user_permission_info(user_permission_info)
            
            return user_permission_info
            
        except Exception as e:
            logger.error(f"获取用户权限信息失败: user_id={user_id}, 错误: {str(e)}")
            return None
    
    async def merge_role_permissions(self, role_ids: List[int]) -> Set[str]:
        """
        合并多个角色的权限
        
        Args:
            role_ids: 角色ID列表
            
        Returns:
            合并后的权限集合
        """
        try:
            merged_permissions = set()
            
            for role_id in role_ids:
                role_permissions = await self.config_manager.get_role_permissions(role_id)
                merged_permissions.update(role_permissions)
            
            return merged_permissions
            
        except Exception as e:
            logger.error(f"合并角色权限失败: role_ids={role_ids}, 错误: {str(e)}")
            return set()
    
    async def check_api_permission(
        self, 
        user_id: int, 
        method: str, 
        path: str
    ) -> PermissionResult:
        """
        检查API权限
        
        Args:
            user_id: 用户ID
            method: HTTP方法
            path: API路径
            
        Returns:
            权限验证结果
        """
        try:
            # 构建权限标识
            required_permission = f"{method.upper()} {path}"
            
            # 验证权限
            return await self.validate_user_permissions(user_id, required_permission)
            
        except Exception as e:
            logger.error(f"检查API权限失败: user_id={user_id}, method={method}, path={path}, 错误: {str(e)}")
            return PermissionResult(
                has_permission=False,
                reason=f"API权限检查异常: {str(e)}",
                matched_permissions=[],
                user_permissions=set(),
                required_permission=f"{method.upper()} {path}"
            )
    
    async def check_menu_permission(self, user_id: int, menu_path: str) -> bool:
        """
        检查菜单权限
        
        Args:
            user_id: 用户ID
            menu_path: 菜单路径
            
        Returns:
            是否有权限
        """
        try:
            user_permission_info = await self.get_user_permission_info(user_id)
            if not user_permission_info:
                return False
            
            # 超级管理员直接通过
            if user_permission_info.is_superuser:
                return True
            
            # 检查用户角色是否包含该菜单
            user = await User.get(id=user_id).prefetch_related("roles__menus")
            
            for role in user.roles:
                for menu in role.menus:
                    if menu.path == menu_path:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"检查菜单权限失败: user_id={user_id}, menu_path={menu_path}, 错误: {str(e)}")
            return False
    
    async def get_user_accessible_menus(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户可访问的菜单列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            菜单列表
        """
        try:
            # 先尝试从缓存获取
            cached_menus = await self.cache_manager.get_user_menus(user_id)
            if cached_menus:
                return cached_menus
            
            user = await User.get_or_none(id=user_id).prefetch_related("roles__menus")
            if not user:
                return []
            
            # 超级管理员获取所有菜单
            if user.is_superuser:
                all_menus = await Menu.all().order_by("order_num", "id")
                menus = [await self._menu_to_dict(menu) for menu in all_menus]
            else:
                # 收集用户角色的所有菜单
                menu_ids = set()
                for role in user.roles:
                    for menu in role.menus:
                        menu_ids.add(menu.id)
                
                if menu_ids:
                    user_menus = await Menu.filter(id__in=menu_ids).order_by("order_num", "id")
                    menus = [await self._menu_to_dict(menu) for menu in user_menus]
                else:
                    menus = []
            
            # 缓存菜单
            await self.cache_manager.set_user_menus(user_id, menus)
            
            return menus
            
        except Exception as e:
            logger.error(f"获取用户菜单失败: user_id={user_id}, 错误: {str(e)}")
            return []
    
    async def batch_check_permissions(
        self, 
        user_id: int, 
        permissions: List[str]
    ) -> Dict[str, bool]:
        """
        批量检查权限
        
        Args:
            user_id: 用户ID
            permissions: 权限列表
            
        Returns:
            权限检查结果字典
        """
        try:
            user_permission_info = await self.get_user_permission_info(user_id)
            if not user_permission_info:
                return {permission: False for permission in permissions}
            
            results = {}
            for permission in permissions:
                results[permission] = await self.has_permission(
                    list(user_permission_info.permissions), 
                    permission
                )
            
            return results
            
        except Exception as e:
            logger.error(f"批量检查权限失败: user_id={user_id}, 错误: {str(e)}")
            return {permission: False for permission in permissions}
    
    async def _check_permission_inheritance(
        self, 
        user_permissions: Set[str], 
        required_permission: str
    ) -> bool:
        """
        检查权限继承
        
        Args:
            user_permissions: 用户权限集合
            required_permission: 需要的权限
            
        Returns:
            是否通过继承获得权限
        """
        try:
            # 解析权限格式: METHOD /api/v2/resource/action
            parts = required_permission.split(" ")
            if len(parts) != 2:
                return False
            
            method, path = parts
            path_parts = path.split("/")
            
            if len(path_parts) < 4:  # /api/v2/resource
                return False
            
            resource = path_parts[3]  # 资源名
            
            # 检查是否有管理权限
            manage_permission = f"{method} /api/v2/{resource}/manage"
            if manage_permission in user_permissions:
                return True
            
            # 检查具体的继承规则
            for parent_action, child_actions in self.permission_inheritance.items():
                parent_permission = f"{method} /api/v2/{resource}/{parent_action}"
                if parent_permission in user_permissions:
                    # 检查当前权限是否在继承列表中
                    for child_action in child_actions:
                        child_permission = f"{method} /api/v2/{resource}/{child_action}"
                        if child_permission == required_permission:
                            return True
            
            return False
            
        except Exception as e:
            logger.error(f"检查权限继承失败: {required_permission}, 错误: {str(e)}")
            return False
    
    async def _get_role_permissions(self, role: Role) -> Set[str]:
        """
        获取角色权限
        
        Args:
            role: 角色对象
            
        Returns:
            权限集合
        """
        try:
            permissions = set()
            
            for api in role.apis:
                permission = f"{api.http_method} {api.api_path}"
                permissions.add(permission)
                
                # 添加迁移后的权限
                migrated = self.config_manager.migrate_permission(permission)
                if migrated != permission:
                    permissions.add(migrated)
            
            return permissions
            
        except Exception as e:
            logger.error(f"获取角色权限失败: role_id={role.id}, 错误: {str(e)}")
            return set()
    
    async def _cache_user_permission_info(self, user_info: UserPermissionInfo) -> None:
        """
        缓存用户权限信息
        
        Args:
            user_info: 用户权限信息
        """
        try:
            cache_data = {
                "user_id": user_info.user_id,
                "username": user_info.username,
                "roles": user_info.roles,
                "permissions": list(user_info.permissions),
                "is_superuser": user_info.is_superuser,
                "is_active": user_info.is_active,
                "cached_at": datetime.now().isoformat()
            }
            
            await self.cache_manager.set_user_permissions(user_info.user_id, cache_data)
            
        except Exception as e:
            logger.error(f"缓存用户权限信息失败: user_id={user_info.user_id}, 错误: {str(e)}")
    
    def _build_user_permission_info_from_cache(self, cached_data: Dict[str, Any]) -> UserPermissionInfo:
        """
        从缓存数据构建用户权限信息
        
        Args:
            cached_data: 缓存数据
            
        Returns:
            用户权限信息
        """
        return UserPermissionInfo(
            user_id=cached_data["user_id"],
            username=cached_data["username"],
            roles=cached_data["roles"],
            permissions=set(cached_data["permissions"]),
            is_superuser=cached_data["is_superuser"],
            is_active=cached_data["is_active"]
        )
    
    def _is_cache_valid(self, cached_data: Dict[str, Any]) -> bool:
        """
        检查缓存是否有效
        
        Args:
            cached_data: 缓存数据
            
        Returns:
            是否有效
        """
        try:
            if "expires_at" not in cached_data:
                return False
            
            expires_at = datetime.fromisoformat(cached_data["expires_at"])
            return datetime.now() < expires_at
            
        except Exception:
            return False
    
    async def _menu_to_dict(self, menu: Menu) -> Dict[str, Any]:
        """
        将菜单对象转换为字典
        
        Args:
            menu: 菜单对象
            
        Returns:
            菜单字典
        """
        return {
            "id": menu.id,
            "name": menu.name,
            "path": menu.path,
            "component": menu.component,
            "icon": menu.icon,
            "order": menu.order,
            "parent_id": menu.parent_id,
            "is_hidden": menu.is_hidden,
            "menu_type": menu.menu_type,
            "keepalive": menu.keepalive,
            "redirect": menu.redirect,
            "remark": menu.remark
        }


# 全局权限验证器实例
permission_validator = PermissionValidator()