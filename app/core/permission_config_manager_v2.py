#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限配置管理器
提供统一的权限配置管理接口，支持权限获取、验证和迁移功能
"""

import asyncio
from typing import Dict, List, Optional, Set, Any, Union
from datetime import datetime

from app.models.admin import User, Role, SysApiEndpoint, Menu
from app.core.permission_cache import permission_cache_manager
from app.log import logger


class PermissionConfigManager:
    """权限配置管理器"""
    
    def __init__(self):
        # API v2权限配置映射
        self.v2_permission_config = {
            # 用户管理
            "users": {
                "read": "GET /api/v2/users",
                "create": "POST /api/v2/users", 
                "update": "PUT /api/v2/users/{id}",
                "delete": "DELETE /api/v2/users/{id}",
                "reset-password": "POST /api/v2/users/{id}/reset-password",
                "permissions": "GET /api/v2/users/{id}/permissions",
                "batch": "POST /api/v2/users/batch"
            },
            # 角色管理
            "roles": {
                "read": "GET /api/v2/roles",
                "create": "POST /api/v2/roles",
                "update": "PUT /api/v2/roles/{id}",
                "delete": "DELETE /api/v2/roles/{id}",
                "permissions": "GET /api/v2/roles/{id}/permissions",
                "assign-permissions": "PUT /api/v2/roles/{id}/permissions",
                "users": "GET /api/v2/roles/{id}/users"
            },
            # 菜单管理
            "menus": {
                "read": "GET /api/v2/menus",
                "create": "POST /api/v2/menus",
                "update": "PATCH /api/v2/menus/{id}",
                "delete": "DELETE /api/v2/menus/{id}",
                "tree": "GET /api/v2/menus/tree",
                "batch-create": "POST /api/v2/menus/batch",
                "batch-update": "PATCH /api/v2/menus/batch",
                "batch-delete": "DELETE /api/v2/menus/batch",
                "children": "GET /api/v2/menus/{id}/children"
            },
            # 部门管理
            "departments": {
                "read": "GET /api/v2/departments",
                "create": "POST /api/v2/departments",
                "update": "PUT /api/v2/departments/{id}",
                "delete": "DELETE /api/v2/departments/{id}",
                "tree": "GET /api/v2/departments/tree"
            },
            # 设备管理
            "devices": {
                "read": "GET /api/v2/devices",
                "create": "POST /api/v2/devices",
                "update": "PUT /api/v2/devices/{id}",
                "delete": "DELETE /api/v2/devices/{id}",
                "batch": "POST /api/v2/devices/batch",
                "search": "GET /api/v2/devices/search",
                "status": "GET /api/v2/devices/{id}/status",
                "statistics": "GET /api/v2/devices/statistics"
            },
            # 设备类型
            "device-types": {
                "read": "GET /api/v2/devices/types",
                "create": "POST /api/v2/devices/types",
                "update": "PUT /api/v2/devices/types/{id}",
                "delete": "DELETE /api/v2/devices/types/{id}"
            },
            # 设备维护
            "device-maintenance": {
                "read": "GET /api/v2/devices/{id}/maintenance",
                "create": "POST /api/v2/devices/{id}/maintenance",
                "update": "PUT /api/v2/devices/maintenance/{id}",
                "delete": "DELETE /api/v2/devices/maintenance/{id}",
                "schedule": "GET /api/v2/devices/maintenance/schedule"
            },
            # AI监控
            "ai-predictions": {
                "read": "GET /api/v2/ai/predictions",
                "create": "POST /api/v2/ai/predictions",
                "update": "PUT /api/v2/ai/predictions/{id}",
                "delete": "DELETE /api/v2/ai/predictions/{id}",
                "export": "GET /api/v2/ai/predictions/{id}/export"
            },
            # AI模型管理
            "ai-models": {
                "read": "GET /api/v2/ai/models",
                "create": "POST /api/v2/ai/models",
                "update": "PUT /api/v2/ai/models/{id}",
                "delete": "DELETE /api/v2/ai/models/{id}",
                "train": "POST /api/v2/ai/models/{id}/train"
            }
        }
        
        # 旧版本权限迁移映射
        self.legacy_permission_map = {
            # v1到v2的映射
            "GET /api/v1/users": "GET /api/v2/users",
            "POST /api/v1/users": "POST /api/v2/users",
            "PUT /api/v1/users/{id}": "PUT /api/v2/users/{id}",
            "DELETE /api/v1/users/{id}": "DELETE /api/v2/users/{id}",
            
            "GET /api/v1/roles": "GET /api/v2/roles",
            "POST /api/v1/roles": "POST /api/v2/roles",
            "PUT /api/v1/roles/{id}": "PUT /api/v2/roles/{id}",
            "DELETE /api/v1/roles/{id}": "DELETE /api/v2/roles/{id}",
            
            # 旧路径格式到v2的映射
            "GET /user/list": "GET /api/v2/users",
            "POST /user/create": "POST /api/v2/users",
            "PUT /user/update": "PUT /api/v2/users/{id}",
            "DELETE /user/delete": "DELETE /api/v2/users/{id}",
            
            "GET /role/list": "GET /api/v2/roles",
            "POST /role/create": "POST /api/v2/roles",
            "PUT /role/update": "PUT /api/v2/roles/{id}",
            "DELETE /role/delete": "DELETE /api/v2/roles/{id}",
            
            "GET /device/list": "GET /api/v2/devices",
            "POST /device/create": "POST /api/v2/devices",
            "PUT /device/update": "PUT /api/v2/devices/{id}",
            "DELETE /device/delete": "DELETE /api/v2/devices/{id}",
        }
        
        # 页面路径到权限资源的映射
        self.page_permission_map = {
            "/system/user": "users",
            "/system/role": "roles", 
            "/system/menu": "menus",
            "/system/dept": "departments",
            "/device/baseinfo": "devices",
            "/device/type": "device-types",
            "/device/maintenance-records": "device-maintenance",
            "/ai-monitor/trend-prediction": "ai-predictions",
            "/ai-monitor/model-management": "ai-models",
            "/ai-monitor/data-annotation": "ai-annotations",
            "/ai-monitor/health-scoring": "ai-health-scores"
        }
    
    def get_permission(self, resource: str, action: str) -> Optional[str]:
        """
        获取权限标识
        
        Args:
            resource: 资源名称 (如 'users', 'roles')
            action: 操作类型 (如 'read', 'create', 'update', 'delete')
            
        Returns:
            权限标识字符串，如 'GET /api/v2/users'
        """
        try:
            resource_config = self.v2_permission_config.get(resource)
            if not resource_config:
                logger.warning(f"未找到资源配置: {resource}")
                return None
            
            permission = resource_config.get(action)
            if not permission:
                logger.warning(f"未找到操作权限: {resource}.{action}")
                return None
            
            return permission
        except Exception as e:
            logger.error(f"获取权限失败: {resource}.{action}, 错误: {str(e)}")
            return None
    
    def get_resource_permissions(self, resource: str) -> Dict[str, str]:
        """
        批量获取资源的所有权限
        
        Args:
            resource: 资源名称
            
        Returns:
            权限字典，键为操作类型，值为权限标识
        """
        try:
            return self.v2_permission_config.get(resource, {})
        except Exception as e:
            logger.error(f"获取资源权限失败: {resource}, 错误: {str(e)}")
            return {}
    
    def get_permission_by_page(self, page_path: str, action: str) -> Optional[str]:
        """
        根据页面路径获取权限标识
        
        Args:
            page_path: 页面路径 (如 '/system/user')
            action: 操作类型
            
        Returns:
            权限标识字符串
        """
        try:
            resource = self.page_permission_map.get(page_path)
            if not resource:
                logger.warning(f"未找到页面权限映射: {page_path}")
                return None
            
            return self.get_permission(resource, action)
        except Exception as e:
            logger.error(f"根据页面获取权限失败: {page_path}.{action}, 错误: {str(e)}")
            return None
    
    def migrate_permission(self, old_permission: str) -> str:
        """
        权限迁移：将旧权限标识转换为新格式
        
        Args:
            old_permission: 旧权限标识
            
        Returns:
            新权限标识
        """
        try:
            # 直接映射查找
            new_permission = self.legacy_permission_map.get(old_permission)
            if new_permission:
                return new_permission
            
            # 如果已经是v2格式，直接返回
            if old_permission.startswith("GET /api/v2/") or \
               old_permission.startswith("POST /api/v2/") or \
               old_permission.startswith("PUT /api/v2/") or \
               old_permission.startswith("DELETE /api/v2/"):
                return old_permission
            
            # 尝试模式匹配转换
            new_permission = self._pattern_migrate(old_permission)
            if new_permission:
                return new_permission
            
            logger.warning(f"无法迁移权限: {old_permission}")
            return old_permission
        except Exception as e:
            logger.error(f"权限迁移失败: {old_permission}, 错误: {str(e)}")
            return old_permission
    
    def _pattern_migrate(self, old_permission: str) -> Optional[str]:
        """
        模式匹配权限迁移
        
        Args:
            old_permission: 旧权限标识
            
        Returns:
            新权限标识或None
        """
        try:
            # 解析HTTP方法和路径
            parts = old_permission.split(" ", 1)
            if len(parts) != 2:
                return None
            
            method, path = parts
            
            # 处理 V1 API 路径转换为 V2
            if path.startswith("/api/v1/"):
                # 移除 /api/v1/ 前缀
                v1_path = path[8:]  # 去掉 "/api/v1/"
                
                # 根据 V1 路径模式转换为 V2
                if v1_path.startswith("user/"):
                    new_path = "/api/v2/users/" + v1_path[5:]
                elif v1_path.startswith("role/"):
                    new_path = "/api/v2/roles/" + v1_path[5:]
                elif v1_path.startswith("device/"):
                    new_path = "/api/v2/devices/" + v1_path[7:]
                elif v1_path.startswith("menu/"):
                    new_path = "/api/v2/menus/" + v1_path[5:]
                elif v1_path.startswith("dept/"):
                    new_path = "/api/v2/departments/" + v1_path[5:]
                elif v1_path.startswith("base/"):
                    new_path = "/api/v2/" + v1_path[5:]
                elif v1_path.startswith("api/"):
                    new_path = "/api/v2/apis/" + v1_path[4:]
                else:
                    new_path = "/api/v2/" + v1_path
            # 处理旧格式路径（不带 /api/v1/ 前缀）
            elif path.startswith("/user/"):
                new_path = path.replace("/user/", "/api/v2/users/")
            elif path.startswith("/role/"):
                new_path = path.replace("/role/", "/api/v2/roles/")
            elif path.startswith("/device/"):
                new_path = path.replace("/device/", "/api/v2/devices/")
            elif path.startswith("/menu/"):
                new_path = path.replace("/menu/", "/api/v2/menus/")
            elif path.startswith("/dept/"):
                new_path = path.replace("/dept/", "/api/v2/departments/")
            else:
                return None
            
            # 处理特殊路径
            new_path = new_path.replace("/list", "")
            new_path = new_path.replace("/create", "")
            new_path = new_path.replace("/update", "/{id}")
            new_path = new_path.replace("/delete", "/{id}")
            new_path = new_path.replace("/authorized", "/{id}/permissions")
            
            # 清理多余的斜杠
            new_path = new_path.rstrip("/")
            if new_path.endswith("/api/v2"):
                new_path += "/"
            
            return f"{method} {new_path}"
        except Exception as e:
            logger.error(f"模式匹配迁移失败: {old_permission}, 错误: {str(e)}")
            return None
    
    async def has_permission(self, user_permissions: List[str], required_permission: str) -> bool:
        """
        权限验证
        
        Args:
            user_permissions: 用户权限列表
            required_permission: 需要的权限
            
        Returns:
            是否有权限
        """
        try:
            # 直接匹配
            if required_permission in user_permissions:
                return True
            
            # 尝试迁移后匹配
            migrated_permission = self.migrate_permission(required_permission)
            if migrated_permission in user_permissions:
                return True
            
            # 检查是否有超级管理员权限
            if "ADMIN" in user_permissions or "*" in user_permissions:
                return True
            
            return False
        except Exception as e:
            logger.error(f"权限验证失败: {required_permission}, 错误: {str(e)}")
            return False
    
    async def get_user_permissions(self, user_id: int) -> Set[str]:
        """
        获取用户的所有权限
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户权限集合
        """
        try:
            # 先尝试从缓存获取
            cached_permissions = await permission_cache_manager.get_user_apis(user_id)
            if cached_permissions:
                return cached_permissions
            
            # 从数据库获取
            user = await User.get(id=user_id).prefetch_related("roles__apis")
            permissions = set()
            
            for role in user.roles:
                for api in role.apis:
                    permission = f"{api.http_method} {api.api_path}"
                    permissions.add(permission)
                    
                    # 同时添加迁移后的权限
                    migrated = self.migrate_permission(permission)
                    if migrated != permission:
                        permissions.add(migrated)
            
            # 缓存权限
            await permission_cache_manager.set_user_apis(user_id, permissions)
            
            return permissions
        except Exception as e:
            logger.error(f"获取用户权限失败: user_id={user_id}, 错误: {str(e)}")
            return set()
    
    async def get_role_permissions(self, role_id: int) -> Set[str]:
        """
        获取角色的所有权限
        
        Args:
            role_id: 角色ID
            
        Returns:
            角色权限集合
        """
        try:
            # 先尝试从缓存获取
            cached_permissions = await permission_cache_manager.get_role_permissions(role_id)
            if cached_permissions and "apis" in cached_permissions:
                return set(cached_permissions["apis"])
            
            # 从数据库获取
            role = await Role.get(id=role_id).prefetch_related("apis")
            permissions = set()
            
            for api in role.apis:
                permission = f"{api.http_method} {api.api_path}"
                permissions.add(permission)
                
                # 同时添加迁移后的权限
                migrated = self.migrate_permission(permission)
                if migrated != permission:
                    permissions.add(migrated)
            
            # 缓存权限
            cache_data = {"apis": list(permissions)}
            await permission_cache_manager.set_role_permissions(role_id, cache_data)
            
            return permissions
        except Exception as e:
            logger.error(f"获取角色权限失败: role_id={role_id}, 错误: {str(e)}")
            return set()
    
    async def validate_user_permission(self, user_id: int, required_permission: str) -> bool:
        """
        验证用户是否有指定权限
        
        Args:
            user_id: 用户ID
            required_permission: 需要的权限
            
        Returns:
            是否有权限
        """
        try:
            user_permissions = await self.get_user_permissions(user_id)
            return await self.has_permission(list(user_permissions), required_permission)
        except Exception as e:
            logger.error(f"验证用户权限失败: user_id={user_id}, permission={required_permission}, 错误: {str(e)}")
            return False
    
    def get_all_v2_permissions(self) -> Dict[str, Dict[str, str]]:
        """
        获取所有v2权限配置
        
        Returns:
            完整的v2权限配置字典
        """
        return self.v2_permission_config.copy()
    
    def get_permission_migration_map(self) -> Dict[str, str]:
        """
        获取权限迁移映射表
        
        Returns:
            权限迁移映射字典
        """
        return self.legacy_permission_map.copy()
    
    def get_page_permission_map(self) -> Dict[str, str]:
        """
        获取页面权限映射表
        
        Returns:
            页面权限映射字典
        """
        return self.page_permission_map.copy()
    
    async def batch_migrate_permissions(self, old_permissions: List[str]) -> Dict[str, str]:
        """
        批量迁移权限
        
        Args:
            old_permissions: 旧权限列表
            
        Returns:
            迁移结果字典，键为旧权限，值为新权限
        """
        try:
            migration_results = {}
            for old_permission in old_permissions:
                new_permission = self.migrate_permission(old_permission)
                migration_results[old_permission] = new_permission
            
            return migration_results
        except Exception as e:
            logger.error(f"批量迁移权限失败: 错误: {str(e)}")
            return {}
    
    def validate_permission_format(self, permission: str) -> bool:
        """
        验证权限格式是否正确
        
        Args:
            permission: 权限标识
            
        Returns:
            格式是否正确
        """
        try:
            # 检查基本格式: METHOD /path
            parts = permission.split(" ", 1)
            if len(parts) != 2:
                return False
            
            method, path = parts
            
            # 检查HTTP方法
            valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]
            if method not in valid_methods:
                return False
            
            # 检查路径格式
            if not path.startswith("/"):
                return False
            
            return True
        except Exception as e:
            logger.error(f"验证权限格式失败: {permission}, 错误: {str(e)}")
            return False


# 全局权限配置管理器实例
permission_config_manager = PermissionConfigManager()