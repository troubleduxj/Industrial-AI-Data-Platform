#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限服务核心逻辑
实现用户权限查询、权限检查、角色权限继承等核心功能
"""

import re
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime, timedelta

from app.models.admin import User, Role, Menu, SysApiEndpoint
from app.core.unified_logger import get_logger
from app.core.permission_cache import permission_cache_manager

logger = get_logger(__name__)


# 权限缓存管理器已移至 app.core.permission_cache 模块


class PermissionService:
    """权限服务核心类"""
    
    def __init__(self):
        self.cache = permission_cache_manager
        self.superuser_types = ["01"]  # 超级用户类型
        self.api_permission_pattern = re.compile(r'^(GET|POST|PUT|DELETE|PATCH)\s+(.+)$')
    
    async def get_user_permissions(self, user_id: int) -> List[str]:
        """
        获取用户权限列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[str]: 用户权限列表，格式为 "METHOD /path"
        """
        try:
            # 尝试从缓存获取
            cached_permissions = await self.cache.get_user_permissions(user_id)
            if cached_permissions is not None:
                logger.debug(f"从缓存获取用户权限: user_id={user_id}")
                return cached_permissions
            
            # 从数据库获取用户信息
            user = await User.get_or_none(id=user_id).prefetch_related('roles')
            if not user:
                logger.warning(f"用户不存在: user_id={user_id}")
                return []
            
            # 超级用户拥有所有权限
            if user.is_superuser:
                all_apis = await SysApiEndpoint.filter(status='active').all()
                permissions = [f"{api.http_method} {api.api_path}" for api in all_apis]
                
                # 缓存权限
                await self.cache.set_user_permissions(user_id, permissions)
                logger.info(f"超级用户权限加载完成: user_id={user_id}, 权限数量={len(permissions)}")
                return permissions
            
            # 获取用户角色权限（支持角色继承）
            permissions = set()
            roles = await user.roles.filter(status='0', del_flag='0').all()
            
            # 获取所有角色权限（包括继承的权限）
            all_role_permissions = await self._get_inherited_role_permissions(roles)
            permissions.update(all_role_permissions)
            
            permissions_list = list(permissions)
            
            # 缓存权限
            await self.cache.set_user_permissions(user_id, permissions_list)
            
            logger.info(f"用户权限加载完成: user_id={user_id}, 角色数量={len(roles)}, 权限数量={len(permissions_list)}")
            return permissions_list
            
        except Exception as e:
            logger.error(f"获取用户权限失败: user_id={user_id}, error={e}")
            return []
    
    async def has_permission(self, user_id: int, permission: str) -> bool:
        """
        检查用户是否有特定权限
        
        Args:
            user_id: 用户ID
            permission: 权限字符串，格式为 "METHOD /path"
            
        Returns:
            bool: 是否有权限
        """
        try:
            # 首先检查用户是否为超级用户
            if await self.is_superuser(user_id):
                logger.debug(f"超级用户权限检查通过: user_id={user_id}, permission={permission}")
                return True
            
            # 获取用户权限列表
            user_permissions = await self.get_user_permissions(user_id)
            
            # 直接匹配
            if permission in user_permissions:
                return True
            
            # 模糊匹配（支持路径参数）
            return await self._match_permission_pattern(permission, user_permissions)
            
        except Exception as e:
            logger.error(f"权限检查失败: user_id={user_id}, permission={permission}, error={e}")
            return False
    
    async def _match_permission_pattern(self, target_permission: str, user_permissions: List[str]) -> bool:
        """
        权限模式匹配
        
        支持路径参数匹配，例如：
        - 用户权限: "GET /api/v2/users/{id}"
        - 请求权限: "GET /api/v2/users/123"
        """
        try:
            # 解析目标权限
            match = self.api_permission_pattern.match(target_permission)
            if not match:
                return False
            
            target_method, target_path = match.groups()
            
            # 遍历用户权限进行模式匹配
            for user_perm in user_permissions:
                perm_match = self.api_permission_pattern.match(user_perm)
                if not perm_match:
                    continue
                
                perm_method, perm_path = perm_match.groups()
                
                # 方法必须匹配
                if target_method != perm_method:
                    continue
                
                # 路径匹配（支持参数占位符）
                if self._match_path_pattern(target_path, perm_path):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"权限模式匹配失败: {e}")
            return False
    
    async def _get_inherited_role_permissions(self, roles: List[Role]) -> Set[str]:
        """
        获取角色继承权限
        
        Args:
            roles: 角色列表
            
        Returns:
            Set[str]: 继承的权限集合
        """
        permissions = set()
        processed_roles = set()
        
        async def collect_role_permissions(role: Role):
            """递归收集角色权限"""
            if role.id in processed_roles:
                return
            
            processed_roles.add(role.id)
            
            # 获取当前角色的API权限
            role_apis = await role.apis.filter(status='active').all()
            for api in role_apis:
                permission = f"{api.http_method} {api.api_path}"
                permissions.add(permission)
            
            # 如果有父角色，递归获取父角色权限
            if role.parent_id:
                parent_role = await Role.get_or_none(id=role.parent_id, status='0', del_flag='0')
                if parent_role:
                    await collect_role_permissions(parent_role)
        
        # 收集所有角色的权限
        for role in roles:
            await collect_role_permissions(role)
        
        return permissions
    
    def _match_path_pattern(self, target_path: str, pattern_path: str) -> bool:
        """
        路径模式匹配
        
        支持以下模式：
        - 精确匹配: /api/v2/users == /api/v2/users
        - 参数匹配: /api/v2/users/123 匹配 /api/v2/users/{id}
        - 通配符匹配: /api/v2/users/123/posts 匹配 /api/v2/users/*
        """
        # 精确匹配
        if target_path == pattern_path:
            return True
        
        # 参数占位符匹配
        pattern_parts = pattern_path.split('/')
        target_parts = target_path.split('/')
        
        if len(pattern_parts) != len(target_parts):
            # 检查通配符匹配
            if pattern_path.endswith('/*'):
                pattern_prefix = pattern_path[:-2]  # 移除 /*
                return target_path.startswith(pattern_prefix)
            return False
        
        # 逐段匹配
        for pattern_part, target_part in zip(pattern_parts, target_parts):
            # 参数占位符（{id}, {name} 等）
            if pattern_part.startswith('{') and pattern_part.endswith('}'):
                continue
            # 通配符
            elif pattern_part == '*':
                continue
            # 精确匹配
            elif pattern_part != target_part:
                return False
        
        return True
    
    async def get_user_roles(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户角色列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[Dict]: 用户角色列表
        """
        try:
            # 尝试从缓存获取
            cached_roles = await self.cache.get_user_roles(user_id)
            if cached_roles is not None:
                logger.debug(f"从缓存获取用户角色: user_id={user_id}")
                return cached_roles
            
            # 从数据库获取
            user = await User.get_or_none(id=user_id).prefetch_related('roles')
            if not user:
                return []
            
            roles = await user.roles.filter(status='0', del_flag='0').all()
            roles_data = []
            
            for role in roles:
                roles_data.append({
                    'id': role.id,
                    'role_name': role.role_name,
                    'role_key': role.role_key,
                    'description': role.description,
                    'status': role.status
                })
            
            # 缓存角色信息
            await self.cache.set_user_roles(user_id, roles_data)
            
            logger.debug(f"用户角色加载完成: user_id={user_id}, 角色数量={len(roles_data)}")
            return roles_data
            
        except Exception as e:
            logger.error(f"获取用户角色失败: user_id={user_id}, error={e}")
            return []
    
    async def get_user_menus(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户菜单权限
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[Dict]: 用户菜单列表
        """
        try:
            # 尝试从缓存获取
            cached_menus = await self.cache.get_user_menus(user_id)
            if cached_menus is not None:
                logger.debug(f"从缓存获取用户菜单: user_id={user_id}")
                return cached_menus
            
            # 从数据库获取用户信息
            user = await User.get_or_none(id=user_id).prefetch_related('roles')
            if not user:
                return []
            
            # 超级用户获取所有菜单
            if user.is_superuser:
                all_menus = await Menu.filter(status=True, visible=True).order_by('order_num', 'id').all()
                menus_data = []
                
                for menu in all_menus:
                    menus_data.append({
                        'id': menu.id,
                        'name': menu.name,
                        'path': menu.path,
                        'component': menu.component,
                        'icon': menu.icon,
                        'order_num': menu.order_num,
                        'parent_id': menu.parent_id,
                        'menu_type': menu.menu_type,
                        'visible': menu.visible,
                        'perms': menu.perms,
                        'query': menu.query,
                        'is_frame': menu.is_frame,
                        'is_cache': menu.is_cache
                    })
                
                # 缓存菜单信息
                await self.cache.set_user_menus(user_id, menus_data)
                logger.info(f"超级用户菜单加载完成: user_id={user_id}, 菜单数量={len(menus_data)}")
                return menus_data
            
            # 获取用户角色菜单权限
            menu_ids = set()
            roles = await user.roles.filter(status='0', del_flag='0').all()
            
            for role in roles:
                role_menus = await role.menus.filter(status=True, visible=True).all()
                for menu in role_menus:
                    menu_ids.add(menu.id)
            
            if not menu_ids:
                return []
            
            # 获取菜单详细信息
            user_menus = await Menu.filter(id__in=menu_ids).order_by('order_num', 'id').all()
            menus_data = []
            
            for menu in user_menus:
                menus_data.append({
                    'id': menu.id,
                    'name': menu.name,
                    'path': menu.path,
                    'component': menu.component,
                    'icon': menu.icon,
                    'order_num': menu.order_num,
                    'parent_id': menu.parent_id,
                    'menu_type': menu.menu_type,
                    'visible': menu.visible,
                    'perms': menu.perms,
                    'query': menu.query,
                    'is_frame': menu.is_frame,
                    'is_cache': menu.is_cache
                })
            
            # 缓存菜单信息
            await self.cache.set_user_menus(user_id, menus_data)
            
            logger.info(f"用户菜单加载完成: user_id={user_id}, 角色数量={len(roles)}, 菜单数量={len(menus_data)}")
            return menus_data
            
        except Exception as e:
            logger.error(f"获取用户菜单失败: user_id={user_id}, error={e}")
            return []
    
    async def check_batch_permission(self, user_id: int, resource: str, action: str) -> Tuple[bool, str]:
        """
        检查批量操作权限
        
        Args:
            user_id: 用户ID
            resource: 资源类型
            action: 操作类型
            
        Returns:
            Tuple[bool, str]: (是否有权限, 原因)
        """
        try:
            # 获取用户信息
            user = await User.get_or_none(id=user_id)
            if not user:
                return False, "用户不存在"
            
            if not user.is_active:
                return False, "用户账户已被禁用"
            
            # 超级用户拥有所有批量操作权限
            if user.is_superuser:
                return True, "超级用户权限"
            
            # 检查批量操作权限
            batch_permission = f"POST /api/v2/{resource}/batch-{action}"
            has_perm = await self.has_permission(user_id, batch_permission)
            
            if has_perm:
                return True, "拥有批量操作权限"
            else:
                return False, f"缺少批量{action}权限"
                
        except Exception as e:
            logger.error(f"批量操作权限检查失败: user_id={user_id}, resource={resource}, action={action}, error={e}")
            return False, "权限检查失败"
    
    async def is_superuser(self, user_id: int) -> bool:
        """
        检查用户是否为超级用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否为超级用户
        """
        try:
            user = await User.get_or_none(id=user_id)
            return user and user.is_superuser
        except Exception as e:
            logger.error(f"超级用户检查失败: user_id={user_id}, error={e}")
            return False
    
    async def refresh_user_permissions(self, user_id: int) -> bool:
        """
        刷新用户权限缓存
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否成功
        """
        try:
            # 清除缓存
            await self.cache.clear_user_cache(user_id)
            
            # 重新加载权限
            await self.get_user_permissions(user_id)
            await self.get_user_roles(user_id)
            await self.get_user_menus(user_id)
            
            logger.info(f"用户权限缓存刷新成功: user_id={user_id}")
            return True
            
        except Exception as e:
            logger.error(f"刷新用户权限缓存失败: user_id={user_id}, error={e}")
            return False
    
    async def refresh_role_permissions(self, role_id: int) -> bool:
        """
        刷新角色权限缓存
        
        Args:
            role_id: 角色ID
            
        Returns:
            bool: 是否成功
        """
        try:
            # 清除所有用户的权限缓存（因为角色权限变更会影响所有拥有该角色的用户）
            await self.cache.clear_role_cache(role_id)
            
            logger.info(f"角色权限缓存刷新成功: role_id={role_id}")
            return True
            
        except Exception as e:
            logger.error(f"刷新角色权限缓存失败: role_id={role_id}, error={e}")
            return False
    
    async def get_user_data_scope(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户数据权限范围
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 数据权限范围信息
        """
        try:
            user = await User.get_or_none(id=user_id).prefetch_related('roles', 'dept')
            if not user:
                return {'scope': 'none', 'dept_ids': [], 'user_ids': []}
            
            # 超级用户拥有全部数据权限
            if user.is_superuser:
                return {'scope': 'all', 'dept_ids': [], 'user_ids': []}
            
            # 获取用户角色的数据权限范围
            roles = await user.roles.filter(status='0', del_flag='0').all()
            data_scopes = []
            
            for role in roles:
                if role.data_scope:
                    data_scopes.append(role.data_scope)
            
            # 确定最高权限范围
            if '1' in data_scopes:  # 全部数据权限
                return {'scope': 'all', 'dept_ids': [], 'user_ids': []}
            elif '2' in data_scopes:  # 自定义数据权限
                # 这里需要根据具体业务逻辑实现
                return {'scope': 'custom', 'dept_ids': [], 'user_ids': []}
            elif '3' in data_scopes:  # 本部门数据权限
                dept_ids = [user.dept.id] if user.dept else []
                return {'scope': 'dept', 'dept_ids': dept_ids, 'user_ids': []}
            elif '4' in data_scopes:  # 本部门及以下数据权限
                dept_ids = await self._get_dept_and_children_ids(user.dept.id if user.dept else None)
                return {'scope': 'dept_and_children', 'dept_ids': dept_ids, 'user_ids': []}
            elif '5' in data_scopes:  # 仅本人数据权限
                return {'scope': 'self', 'dept_ids': [], 'user_ids': [user_id]}
            else:
                return {'scope': 'none', 'dept_ids': [], 'user_ids': []}
                
        except Exception as e:
            logger.error(f"获取用户数据权限范围失败: user_id={user_id}, error={e}")
            return {'scope': 'none', 'dept_ids': [], 'user_ids': []}
    
    async def _get_dept_and_children_ids(self, dept_id: Optional[int]) -> List[int]:
        """
        获取部门及其子部门ID列表
        
        Args:
            dept_id: 部门ID
            
        Returns:
            List[int]: 部门ID列表
        """
        if not dept_id:
            return []
        
        try:
            from app.models.admin import Dept
            
            # 使用递归查询获取所有子部门
            dept_ids = [dept_id]
            
            async def collect_children(parent_id: int):
                children = await Dept.filter(parent_id=parent_id, del_flag='0').all()
                for child in children:
                    dept_ids.append(child.id)
                    await collect_children(child.id)
            
            await collect_children(dept_id)
            return dept_ids
            
        except Exception as e:
            logger.error(f"获取部门子部门失败: dept_id={dept_id}, error={e}")
            return [dept_id] if dept_id else []
    
    async def check_data_permission(self, user_id: int, resource_dept_id: Optional[int], resource_user_id: Optional[int] = None) -> bool:
        """
        检查数据权限
        
        Args:
            user_id: 当前用户ID
            resource_dept_id: 资源所属部门ID
            resource_user_id: 资源所属用户ID
            
        Returns:
            bool: 是否有权限访问
        """
        try:
            data_scope = await self.get_user_data_scope(user_id)
            
            if data_scope['scope'] == 'all':
                return True
            elif data_scope['scope'] == 'none':
                return False
            elif data_scope['scope'] == 'self':
                return resource_user_id == user_id
            elif data_scope['scope'] in ['dept', 'dept_and_children']:
                return resource_dept_id in data_scope['dept_ids']
            elif data_scope['scope'] == 'custom':
                # 自定义权限逻辑，需要根据具体业务实现
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"数据权限检查失败: user_id={user_id}, error={e}")
            return False
    
    async def get_user_apis(self, user_id: int) -> List[str]:
        """
        获取用户API权限列表（用于前端权限控制）
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[str]: 用户API权限列表
        """
        try:
            return await self.get_user_permissions(user_id)
        except Exception as e:
            logger.error(f"获取用户API权限失败: user_id={user_id}, error={e}")
            return []
    
    async def batch_check_permissions(self, user_id: int, permissions: List[str]) -> Dict[str, bool]:
        """
        批量检查权限
        
        Args:
            user_id: 用户ID
            permissions: 权限列表
            
        Returns:
            Dict[str, bool]: 权限检查结果
        """
        try:
            # 首先检查用户是否为超级用户
            if await self.is_superuser(user_id):
                return {perm: True for perm in permissions}
            
            # 获取用户权限列表
            user_permissions = await self.get_user_permissions(user_id)
            
            results = {}
            for permission in permissions:
                if permission in user_permissions:
                    results[permission] = True
                else:
                    results[permission] = await self._match_permission_pattern(permission, user_permissions)
            
            return results
            
        except Exception as e:
            logger.error(f"批量权限检查失败: user_id={user_id}, error={e}")
            return {perm: False for perm in permissions}


# 全局权限服务实例
permission_service = PermissionService()