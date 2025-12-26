#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色管理服务
实现角色的CRUD操作、权限分配、状态管理等功能
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from tortoise.transactions import in_db_transaction
from tortoise.exceptions import IntegrityError

from app.models.admin import Role, User, Menu, SysApiEndpoint
from app.core.unified_logger import get_logger
from app.core.permission_cache import permission_cache_manager

logger = get_logger(__name__)


class RoleManagementService:
    """角色管理服务"""
    
    def __init__(self):
        self.cache_ttl = 300  # 缓存5分钟
    
    async def create_role(self, role_data: Dict[str, Any]) -> Role:
        """创建角色"""
        try:
            logger.info(f"创建角色: {role_data.get('role_name')}")
            
            # 检查角色名是否已存在
            existing_role = await Role.get_or_none(role_name=role_data['role_name'])
            if existing_role:
                raise ValueError(f"角色名 '{role_data['role_name']}' 已存在")
            
            # 检查角色键是否已存在
            if role_data.get('role_key'):
                existing_key = await Role.get_or_none(role_key=role_data['role_key'])
                if existing_key:
                    raise ValueError(f"角色键 '{role_data['role_key']}' 已存在")
            
            async with in_db_transaction():
                # 创建角色
                role = await Role.create(
                    role_name=role_data['role_name'],
                    role_key=role_data.get('role_key'),
                    role_sort=role_data.get('role_sort', 0),
                    data_scope=role_data.get('data_scope', '1'),
                    menu_check_strictly=role_data.get('menu_check_strictly', True),
                    dept_check_strictly=role_data.get('dept_check_strictly', True),
                    status=role_data.get('status', '0'),
                    remark=role_data.get('remark'),
                    parent_id=role_data.get('parent_id'),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                # 分配菜单权限
                menu_ids = role_data.get('menu_ids', [])
                if menu_ids:
                    await self._assign_menus_to_role(role, menu_ids)
                
                # 分配API权限
                api_ids = role_data.get('api_ids', [])
                if api_ids:
                    await self._assign_apis_to_role(role, api_ids)
                
                logger.info(f"角色创建成功: {role.role_name} (ID: {role.id})")
                return role
        
        except IntegrityError as e:
            logger.error(f"创建角色失败，数据完整性错误: {e}")
            raise ValueError("角色数据违反唯一性约束")
        except Exception as e:
            logger.error(f"创建角色失败: {e}")
            raise
    
    async def get_role(self, role_id: int) -> Optional[Role]:
        """获取角色详情"""
        try:
            role = await Role.get_or_none(id=role_id).prefetch_related('menus', 'apis')
            if not role:
                logger.warning(f"角色不存在: id={role_id}")
                return None
            
            return role
        
        except Exception as e:
            logger.error(f"获取角色失败: id={role_id}, error={e}")
            return None
    
    async def get_roles(self, 
                       status: Optional[str] = None,
                       parent_id: Optional[int] = None,
                       page: int = 1,
                       page_size: int = 20) -> Dict[str, Any]:
        """获取角色列表"""
        try:
            query = Role.filter(del_flag='0')
            
            # 状态过滤
            if status is not None:
                query = query.filter(status=status)
            
            # 父角色过滤
            if parent_id is not None:
                query = query.filter(parent_id=parent_id)
            
            # 总数统计
            total = await query.count()
            
            # 分页查询
            offset = (page - 1) * page_size
            roles = await query.offset(offset).limit(page_size).order_by('role_sort', 'id')
            
            # 转换为字典格式
            role_list = []
            for role in roles:
                role_dict = {
                    'id': role.id,
                    'role_name': role.role_name,
                    'role_key': role.role_key,
                    'role_sort': role.role_sort,
                    'data_scope': role.data_scope,
                    'menu_check_strictly': role.menu_check_strictly,
                    'dept_check_strictly': role.dept_check_strictly,
                    'status': role.status,
                    'remark': role.remark,
                    'parent_id': role.parent_id,
                    'created_at': role.created_at.isoformat() if role.created_at else None,
                    'updated_at': role.updated_at.isoformat() if role.updated_at else None
                }
                role_list.append(role_dict)
            
            return {
                'items': role_list,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
        
        except Exception as e:
            logger.error(f"获取角色列表失败: error={e}")
            return {'items': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}
    
    async def update_role(self, role_id: int, role_data: Dict[str, Any]) -> Optional[Role]:
        """更新角色"""
        try:
            role = await Role.get_or_none(id=role_id)
            if not role:
                logger.warning(f"角色不存在: id={role_id}")
                return None
            
            logger.info(f"更新角色: {role.role_name} (ID: {role_id})")
            
            async with in_db_transaction():
                # 检查角色名唯一性
                if 'role_name' in role_data and role_data['role_name'] != role.role_name:
                    existing_role = await Role.get_or_none(role_name=role_data['role_name'])
                    if existing_role:
                        raise ValueError(f"角色名 '{role_data['role_name']}' 已存在")
                
                # 检查角色键唯一性
                if 'role_key' in role_data and role_data['role_key'] != role.role_key:
                    existing_key = await Role.get_or_none(role_key=role_data['role_key'])
                    if existing_key:
                        raise ValueError(f"角色键 '{role_data['role_key']}' 已存在")
                
                # 更新角色基本信息
                update_fields = ['role_name', 'role_key', 'role_sort', 'data_scope', 
                               'menu_check_strictly', 'dept_check_strictly', 'status', 'remark', 'parent_id']
                
                updated = False
                for field in update_fields:
                    if field in role_data:
                        old_value = getattr(role, field)
                        new_value = role_data[field]
                        if old_value != new_value:
                            setattr(role, field, new_value)
                            updated = True
                
                if updated:
                    role.updated_at = datetime.now()
                    await role.save()
                
                # 更新菜单权限
                if 'menu_ids' in role_data:
                    await self._assign_menus_to_role(role, role_data['menu_ids'])
                
                # 更新API权限
                if 'api_ids' in role_data:
                    await self._assign_apis_to_role(role, role_data['api_ids'])
                
                # 清理相关用户的权限缓存
                await self._clear_role_users_cache(role_id)
                
                logger.info(f"角色更新成功: {role.role_name} (ID: {role_id})")
                return role
        
        except IntegrityError as e:
            logger.error(f"更新角色失败，数据完整性错误: {e}")
            raise ValueError("角色数据违反唯一性约束")
        except Exception as e:
            logger.error(f"更新角色失败: id={role_id}, error={e}")
            raise
    
    async def delete_role(self, role_id: int) -> bool:
        """删除角色（软删除）"""
        try:
            role = await Role.get_or_none(id=role_id)
            if not role:
                logger.warning(f"角色不存在: id={role_id}")
                return False
            
            # 检查是否有用户使用该角色
            user_count = await role.users.all().count()
            if user_count > 0:
                raise ValueError(f"角色 '{role.role_name}' 正在被 {user_count} 个用户使用，无法删除")
            
            # 检查是否有子角色
            child_count = await Role.filter(parent_id=role_id, del_flag='0').count()
            if child_count > 0:
                raise ValueError(f"角色 '{role.role_name}' 存在子角色，无法删除")
            
            logger.info(f"删除角色: {role.role_name} (ID: {role_id})")
            
            async with in_db_transaction():
                # 软删除
                role.del_flag = '1'
                role.updated_at = datetime.now()
                await role.save()
                
                # 清理权限关联
                await role.menus.clear()
                await role.apis.clear()
                
                logger.info(f"角色删除成功: {role.role_name} (ID: {role_id})")
                return True
        
        except Exception as e:
            logger.error(f"删除角色失败: id={role_id}, error={e}")
            raise
    
    async def update_role_status(self, role_id: int, status: str) -> bool:
        """更新角色状态"""
        try:
            role = await Role.get_or_none(id=role_id)
            if not role:
                logger.warning(f"角色不存在: id={role_id}")
                return False
            
            if status not in ['0', '1']:
                raise ValueError("状态值必须为 '0'（启用）或 '1'（禁用）")
            
            logger.info(f"更新角色状态: {role.role_name} -> {status}")
            
            role.status = status
            role.updated_at = datetime.now()
            await role.save()
            
            # 清理相关用户的权限缓存
            await self._clear_role_users_cache(role_id)
            
            logger.info(f"角色状态更新成功: {role.role_name} (ID: {role_id})")
            return True
        
        except Exception as e:
            logger.error(f"更新角色状态失败: id={role_id}, error={e}")
            raise
    
    async def get_role_menus(self, role_id: int) -> List[Dict[str, Any]]:
        """获取角色的菜单权限"""
        try:
            role = await Role.get_or_none(id=role_id).prefetch_related('menus')
            if not role:
                return []
            
            menus = await role.menus.filter(del_flag='0').order_by('order_num', 'id')
            
            menu_list = []
            for menu in menus:
                menu_dict = {
                    'id': menu.id,
                    'name': menu.name,
                    'path': menu.path,
                    'component': menu.component,
                    'menu_type': menu.menu_type,
                    'icon': menu.icon,
                    'order_num': menu.order_num,
                    'parent_id': menu.parent_id,
                    'perms': menu.perms,
                    'visible': menu.visible,
                    'status': menu.status
                }
                menu_list.append(menu_dict)
            
            return menu_list
        
        except Exception as e:
            logger.error(f"获取角色菜单权限失败: role_id={role_id}, error={e}")
            return []
    
    async def get_role_apis(self, role_id: int) -> List[Dict[str, Any]]:
        """获取角色的API权限"""
        try:
            role = await Role.get_or_none(id=role_id).prefetch_related('apis')
            if not role:
                return []
            
            apis = await role.apis.filter(status='active').order_by('api_path', 'http_method')
            
            api_list = []
            for api in apis:
                api_dict = {
                    'id': api.id,
                    'api_name': api.api_name,
                    'api_path': api.api_path,
                    'http_method': api.http_method,
                    'api_description': api.api_description,
                    'permission_level': api.permission_level,
                    'is_public': api.is_public
                }
                api_list.append(api_dict)
            
            return api_list
        
        except Exception as e:
            logger.error(f"获取角色API权限失败: role_id={role_id}, error={e}")
            return []
    
    async def assign_menus_to_role(self, role_id: int, menu_ids: List[int]) -> bool:
        """为角色分配菜单权限"""
        try:
            role = await Role.get_or_none(id=role_id)
            if not role:
                logger.warning(f"角色不存在: id={role_id}")
                return False
            
            logger.info(f"为角色分配菜单权限: {role.role_name}, menu_ids={menu_ids}")
            
            await self._assign_menus_to_role(role, menu_ids)
            
            # 清理相关用户的权限缓存
            await self._clear_role_users_cache(role_id)
            
            logger.info(f"菜单权限分配成功: role_id={role_id}, menu_count={len(menu_ids)}")
            return True
        
        except Exception as e:
            logger.error(f"分配菜单权限失败: role_id={role_id}, error={e}")
            raise
    
    async def assign_apis_to_role(self, role_id: int, api_ids: List[int]) -> bool:
        """为角色分配API权限"""
        try:
            role = await Role.get_or_none(id=role_id)
            if not role:
                logger.warning(f"角色不存在: id={role_id}")
                return False
            
            logger.info(f"为角色分配API权限: {role.role_name}, api_ids={api_ids}")
            
            await self._assign_apis_to_role(role, api_ids)
            
            # 清理相关用户的权限缓存
            await self._clear_role_users_cache(role_id)
            
            logger.info(f"API权限分配成功: role_id={role_id}, api_count={len(api_ids)}")
            return True
        
        except Exception as e:
            logger.error(f"分配API权限失败: role_id={role_id}, error={e}")
            raise
    
    async def get_role_users(self, role_id: int) -> List[Dict[str, Any]]:
        """获取角色下的用户列表"""
        try:
            role = await Role.get_or_none(id=role_id).prefetch_related('users')
            if not role:
                return []
            
            users = await role.users.filter(del_flag='0').order_by('username')
            
            user_list = []
            for user in users:
                user_dict = {
                    'id': user.id,
                    'username': user.username,
                    'nick_name': user.nick_name,
                    'email': user.email,
                    'phone_number': user.phone_number,
                    'status': user.status,
                    'user_type': user.user_type,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                }
                user_list.append(user_dict)
            
            return user_list
        
        except Exception as e:
            logger.error(f"获取角色用户列表失败: role_id={role_id}, error={e}")
            return []
    
    async def batch_update_role_status(self, role_ids: List[int], status: str) -> int:
        """批量更新角色状态"""
        try:
            if status not in ['0', '1']:
                raise ValueError("状态值必须为 '0'（启用）或 '1'（禁用）")
            
            logger.info(f"批量更新角色状态: role_ids={role_ids}, status={status}")
            
            updated_count = await Role.filter(id__in=role_ids, del_flag='0').update(
                status=status,
                updated_at=datetime.now()
            )
            
            # 清理相关用户的权限缓存
            for role_id in role_ids:
                await self._clear_role_users_cache(role_id)
            
            logger.info(f"批量更新角色状态成功: updated_count={updated_count}")
            return updated_count
        
        except Exception as e:
            logger.error(f"批量更新角色状态失败: error={e}")
            raise
    
    async def get_role_tree(self) -> List[Dict[str, Any]]:
        """获取角色树结构"""
        try:
            # 获取所有有效角色
            roles = await Role.filter(del_flag='0').order_by('role_sort', 'id')
            
            # 构建角色字典
            role_dict = {}
            for role in roles:
                role_dict[role.id] = {
                    'id': role.id,
                    'role_name': role.role_name,
                    'role_key': role.role_key,
                    'role_sort': role.role_sort,
                    'status': role.status,
                    'parent_id': role.parent_id,
                    'children': []
                }
            
            # 构建树结构
            tree = []
            for role in roles:
                role_node = role_dict[role.id]
                if role.parent_id and role.parent_id in role_dict:
                    role_dict[role.parent_id]['children'].append(role_node)
                else:
                    tree.append(role_node)
            
            return tree
        
        except Exception as e:
            logger.error(f"获取角色树失败: error={e}")
            return []
    
    async def get_role_statistics(self) -> Dict[str, Any]:
        """获取角色统计信息"""
        try:
            total_roles = await Role.filter(del_flag='0').count()
            active_roles = await Role.filter(del_flag='0', status='0').count()
            inactive_roles = await Role.filter(del_flag='0', status='1').count()
            
            # 按数据权限范围统计
            data_scope_stats = {}
            data_scopes = ['1', '2', '3', '4', '5']  # 全部、自定义、本部门、本部门及以下、仅本人
            for scope in data_scopes:
                count = await Role.filter(del_flag='0', data_scope=scope).count()
                data_scope_stats[scope] = count
            
            return {
                'total_roles': total_roles,
                'active_roles': active_roles,
                'inactive_roles': inactive_roles,
                'data_scope_stats': data_scope_stats,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"获取角色统计信息失败: error={e}")
            return {}
    
    async def _assign_menus_to_role(self, role: Role, menu_ids: List[int]) -> None:
        """内部方法：为角色分配菜单权限"""
        try:
            # 清除现有菜单关联
            await role.menus.clear()
            
            if menu_ids:
                # 验证菜单存在性
                menus = await Menu.filter(id__in=menu_ids, del_flag='0')
                valid_menu_ids = {menu.id for menu in menus}
                invalid_menu_ids = set(menu_ids) - valid_menu_ids
                
                if invalid_menu_ids:
                    logger.warning(f"无效的菜单ID: {invalid_menu_ids}")
                
                # 添加新的菜单关联
                for menu in menus:
                    await role.menus.add(menu)
                
                logger.debug(f"为角色分配菜单: role_id={role.id}, valid_menus={len(menus)}")
        
        except Exception as e:
            logger.error(f"分配菜单权限失败: role_id={role.id}, error={e}")
            raise
    
    async def _assign_apis_to_role(self, role: Role, api_ids: List[int]) -> None:
        """内部方法：为角色分配API权限"""
        try:
            # 清除现有API关联
            await role.apis.clear()
            
            if api_ids:
                # 验证API存在性
                apis = await SysApiEndpoint.filter(id__in=api_ids, status='active')
                valid_api_ids = {api.id for api in apis}
                invalid_api_ids = set(api_ids) - valid_api_ids
                
                if invalid_api_ids:
                    logger.warning(f"无效的API ID: {invalid_api_ids}")
                
                # 添加新的API关联
                for api in apis:
                    await role.apis.add(api)
                
                logger.debug(f"为角色分配API: role_id={role.id}, valid_apis={len(apis)}")
        
        except Exception as e:
            logger.error(f"分配API权限失败: role_id={role.id}, error={e}")
            raise
    
    async def _clear_role_users_cache(self, role_id: int) -> None:
        """清理角色相关用户的权限缓存"""
        try:
            role = await Role.get_or_none(id=role_id).prefetch_related('users')
            if role:
                for user in await role.users.all():
                    await permission_cache_manager.clear_user_permissions(user.id)
                    logger.debug(f"清理用户权限缓存: user_id={user.id}")
        
        except Exception as e:
            logger.error(f"清理角色用户缓存失败: role_id={role_id}, error={e}")


# 全局角色管理服务实例
role_management_service = RoleManagementService()


# 便捷函数
async def create_role(role_data: Dict[str, Any]) -> Role:
    """创建角色"""
    return await role_management_service.create_role(role_data)


async def get_role(role_id: int) -> Optional[Role]:
    """获取角色详情"""
    return await role_management_service.get_role(role_id)


async def get_roles(**filters) -> Dict[str, Any]:
    """获取角色列表"""
    return await role_management_service.get_roles(**filters)


async def update_role(role_id: int, role_data: Dict[str, Any]) -> Optional[Role]:
    """更新角色"""
    return await role_management_service.update_role(role_id, role_data)


async def delete_role(role_id: int) -> bool:
    """删除角色"""
    return await role_management_service.delete_role(role_id)


if __name__ == "__main__":
    # 测试角色管理服务
    import asyncio
    
    async def test_role_service():
        service = RoleManagementService()
        
        # 模拟角色数据
        role_data = {
            'role_name': '测试角色',
            'role_key': 'test_role',
            'role_sort': 1,
            'data_scope': '1',
            'remark': '这是一个测试角色',
            'menu_ids': [1, 2, 3],
            'api_ids': [1, 2, 3]
        }
        
        print("角色管理服务测试")
        print(f"模拟角色数据: {role_data}")
        
        # 测试获取角色统计
        # stats = await service.get_role_statistics()
        # print(f"角色统计: {stats}")
        
        print("角色管理服务测试完成")
    
    asyncio.run(test_role_service())