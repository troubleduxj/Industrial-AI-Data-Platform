#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
菜单权限管理服务
实现菜单权限查询、动态菜单生成、菜单权限缓存等功能
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from tortoise.transactions import in_db_transaction
from tortoise.exceptions import IntegrityError

from app.models.admin import Menu, User, Role
from app.schemas.menus import MenuType
from app.core.unified_logger import get_logger
from app.core.permission_cache import permission_cache_manager

logger = get_logger(__name__)


class MenuPermissionService:
    """菜单权限管理服务"""
    
    def __init__(self):
        self.cache_ttl = 300  # 缓存5分钟
    
    async def get_user_menus(self, user_id: int, include_hidden: bool = False) -> List[Dict[str, Any]]:
        """获取用户可访问的菜单列表"""
        try:
            logger.debug(f"获取用户菜单: user_id={user_id}, include_hidden={include_hidden}")
            
            user = await User.get_or_none(id=user_id).prefetch_related('roles')
            if not user:
                logger.warning(f"用户不存在: user_id={user_id}")
                return []
            
            # 检查缓存
            cache_key = f"user_menus:{user_id}:{include_hidden}"
            cached_menus = await permission_cache_manager.get_cached_data(cache_key)
            if cached_menus:
                logger.debug(f"从缓存获取用户菜单: user_id={user_id}")
                return cached_menus
            
            menus = []
            
            if user.is_superuser:
                # 超级用户获取所有菜单
                query = Menu.filter(del_flag='0', status=True)
                if not include_hidden:
                    query = query.filter(visible=True)
                menus = await query.order_by('order_num', 'id')
            else:
                # 普通用户通过角色获取菜单
                roles = await user.roles.filter(del_flag='0', status='0')
                menu_set = set()
                
                for role in roles:
                    role_menus = await role.menus.filter(del_flag='0', status=True)
                    if not include_hidden:
                        role_menus = role_menus.filter(visible=True)
                    menu_set.update(role_menus)
                
                menus = sorted(list(menu_set), key=lambda x: (x.order_num, x.id))
            
            # 转换为字典格式
            menu_list = []
            for menu in menus:
                menu_dict = await self._menu_to_dict(menu)
                menu_list.append(menu_dict)
            
            # 缓存结果
            await permission_cache_manager.cache_data(cache_key, menu_list, self.cache_ttl)
            
            logger.info(f"获取用户菜单成功: user_id={user_id}, menu_count={len(menu_list)}")
            return menu_list
        
        except Exception as e:
            logger.error(f"获取用户菜单失败: user_id={user_id}, error={e}")
            return []
    
    async def get_user_menu_tree(self, user_id: int, include_hidden: bool = False) -> List[Dict[str, Any]]:
        """获取用户菜单树结构"""
        try:
            logger.debug(f"获取用户菜单树: user_id={user_id}")
            
            # 获取用户所有菜单
            menus = await self.get_user_menus(user_id, include_hidden)
            
            # 构建菜单树
            menu_tree = self._build_menu_tree(menus)
            
            logger.info(f"获取用户菜单树成功: user_id={user_id}, tree_nodes={len(menu_tree)}")
            return menu_tree
        
        except Exception as e:
            logger.error(f"获取用户菜单树失败: user_id={user_id}, error={e}")
            return []
    
    async def get_menu_by_id(self, menu_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取菜单详情"""
        try:
            menu = await Menu.get_or_none(id=menu_id)
            if not menu:
                return None
            
            return await self._menu_to_dict(menu)
        
        except Exception as e:
            logger.error(f"获取菜单详情失败: menu_id={menu_id}, error={e}")
            return None
    
    async def get_all_menus(self, 
                           menu_type: Optional[str] = None,
                           status: Optional[bool] = None,
                           visible: Optional[bool] = None,
                           parent_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取所有菜单列表"""
        try:
            query = Menu.filter(del_flag='0')
            
            # 菜单类型过滤
            if menu_type:
                query = query.filter(menu_type=menu_type)
            
            # 状态过滤
            if status is not None:
                query = query.filter(status=status)
            
            # 可见性过滤
            if visible is not None:
                query = query.filter(visible=visible)
            
            # 父菜单过滤
            if parent_id is not None:
                query = query.filter(parent_id=parent_id)
            
            menus = await query.order_by('order_num', 'id')
            
            menu_list = []
            for menu in menus:
                menu_dict = await self._menu_to_dict(menu)
                menu_list.append(menu_dict)
            
            return menu_list
        
        except Exception as e:
            logger.error(f"获取菜单列表失败: error={e}")
            return []
    
    async def get_menu_tree(self, 
                           menu_type: Optional[str] = None,
                           status: Optional[bool] = None,
                           visible: Optional[bool] = None) -> List[Dict[str, Any]]:
        """获取菜单树结构"""
        try:
            menus = await self.get_all_menus(menu_type=menu_type, status=status, visible=visible)
            return self._build_menu_tree(menus)
        
        except Exception as e:
            logger.error(f"获取菜单树失败: error={e}")
            return []
    
    async def create_menu(self, menu_data: Dict[str, Any]) -> Menu:
        """创建菜单"""
        try:
            logger.info(f"创建菜单: {menu_data.get('name')}")
            
            # 验证父菜单存在性
            if menu_data.get('parent_id'):
                parent_menu = await Menu.get_or_none(id=menu_data['parent_id'])
                if not parent_menu:
                    raise ValueError(f"父菜单不存在: parent_id={menu_data['parent_id']}")
            
            async with in_db_transaction():
                menu = await Menu.create(
                    name=menu_data['name'],
                    path=menu_data.get('path'),
                    component=menu_data.get('component'),
                    menu_type=menu_data.get('menu_type', MenuType.MENU),
                    icon=menu_data.get('icon'),
                    order_num=menu_data.get('order_num', 0),
                    parent_id=menu_data.get('parent_id'),
                    perms=menu_data.get('perms'),
                    visible=menu_data.get('visible', True),
                    status=menu_data.get('status', True),
                    is_frame=menu_data.get('is_frame', False),
                    is_cache=menu_data.get('is_cache', True),
                    query=menu_data.get('query'),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                # 清理菜单缓存
                await self._clear_menu_cache()
                
                logger.info(f"菜单创建成功: {menu.name} (ID: {menu.id})")
                return menu
        
        except Exception as e:
            logger.error(f"创建菜单失败: {e}")
            raise
    
    async def update_menu(self, menu_id: int, menu_data: Dict[str, Any]) -> Optional[Menu]:
        """更新菜单"""
        try:
            menu = await Menu.get_or_none(id=menu_id)
            if not menu:
                logger.warning(f"菜单不存在: id={menu_id}")
                return None
            
            logger.info(f"更新菜单: {menu.name} (ID: {menu_id})")
            
            # 验证父菜单存在性（如果有变更）
            if 'parent_id' in menu_data and menu_data['parent_id']:
                if menu_data['parent_id'] == menu_id:
                    raise ValueError("菜单不能设置自己为父菜单")
                
                parent_menu = await Menu.get_or_none(id=menu_data['parent_id'])
                if not parent_menu:
                    raise ValueError(f"父菜单不存在: parent_id={menu_data['parent_id']}")
            
            async with in_db_transaction():
                # 更新菜单基本信息
                update_fields = ['name', 'path', 'component', 'menu_type', 'icon', 
                               'order_num', 'parent_id', 'perms', 'visible', 'status',
                               'is_frame', 'is_cache', 'query']
                
                updated = False
                for field in update_fields:
                    if field in menu_data:
                        old_value = getattr(menu, field)
                        new_value = menu_data[field]
                        if old_value != new_value:
                            setattr(menu, field, new_value)
                            updated = True
                
                if updated:
                    menu.updated_at = datetime.now()
                    await menu.save()
                
                # 清理菜单缓存
                await self._clear_menu_cache()
                
                logger.info(f"菜单更新成功: {menu.name} (ID: {menu_id})")
                return menu
        
        except Exception as e:
            logger.error(f"更新菜单失败: id={menu_id}, error={e}")
            raise
    
    async def delete_menu(self, menu_id: int) -> bool:
        """删除菜单（软删除）"""
        try:
            menu = await Menu.get_or_none(id=menu_id)
            if not menu:
                logger.warning(f"菜单不存在: id={menu_id}")
                return False
            
            # 检查是否有子菜单
            child_count = await Menu.filter(parent_id=menu_id, del_flag='0').count()
            if child_count > 0:
                raise ValueError(f"菜单 '{menu.name}' 存在子菜单，无法删除")
            
            logger.info(f"删除菜单: {menu.name} (ID: {menu_id})")
            
            async with in_db_transaction():
                # 软删除
                menu.del_flag = '1'
                menu.updated_at = datetime.now()
                await menu.save()
                
                # 清理菜单缓存
                await self._clear_menu_cache()
                
                logger.info(f"菜单删除成功: {menu.name} (ID: {menu_id})")
                return True
        
        except Exception as e:
            logger.error(f"删除菜单失败: id={menu_id}, error={e}")
            raise
    
    async def update_menu_status(self, menu_id: int, status: bool) -> bool:
        """更新菜单状态"""
        try:
            menu = await Menu.get_or_none(id=menu_id)
            if not menu:
                logger.warning(f"菜单不存在: id={menu_id}")
                return False
            
            logger.info(f"更新菜单状态: {menu.name} -> {status}")
            
            menu.status = status
            menu.updated_at = datetime.now()
            await menu.save()
            
            # 清理菜单缓存
            await self._clear_menu_cache()
            
            logger.info(f"菜单状态更新成功: {menu.name} (ID: {menu_id})")
            return True
        
        except Exception as e:
            logger.error(f"更新菜单状态失败: id={menu_id}, error={e}")
            raise
    
    async def update_menu_visibility(self, menu_id: int, visible: bool) -> bool:
        """更新菜单可见性"""
        try:
            menu = await Menu.get_or_none(id=menu_id)
            if not menu:
                logger.warning(f"菜单不存在: id={menu_id}")
                return False
            
            logger.info(f"更新菜单可见性: {menu.name} -> {visible}")
            
            menu.visible = visible
            menu.updated_at = datetime.now()
            await menu.save()
            
            # 清理菜单缓存
            await self._clear_menu_cache()
            
            logger.info(f"菜单可见性更新成功: {menu.name} (ID: {menu_id})")
            return True
        
        except Exception as e:
            logger.error(f"更新菜单可见性失败: id={menu_id}, error={e}")
            raise
    
    async def batch_update_menu_status(self, menu_ids: List[int], status: bool) -> int:
        """批量更新菜单状态"""
        try:
            logger.info(f"批量更新菜单状态: menu_ids={menu_ids}, status={status}")
            
            updated_count = await Menu.filter(id__in=menu_ids, del_flag='0').update(
                status=status,
                updated_at=datetime.now()
            )
            
            # 清理菜单缓存
            await self._clear_menu_cache()
            
            logger.info(f"批量更新菜单状态成功: updated_count={updated_count}")
            return updated_count
        
        except Exception as e:
            logger.error(f"批量更新菜单状态失败: error={e}")
            raise
    
    async def get_menu_permissions(self, user_id: int) -> List[str]:
        """获取用户的菜单权限标识列表"""
        try:
            menus = await self.get_user_menus(user_id)
            permissions = []
            
            for menu in menus:
                if menu.get('perms'):
                    permissions.append(menu['perms'])
            
            return permissions
        
        except Exception as e:
            logger.error(f"获取菜单权限失败: user_id={user_id}, error={e}")
            return []
    
    async def check_menu_permission(self, user_id: int, permission: str) -> bool:
        """检查用户是否有特定菜单权限"""
        try:
            permissions = await self.get_menu_permissions(user_id)
            return permission in permissions
        
        except Exception as e:
            logger.error(f"检查菜单权限失败: user_id={user_id}, permission={permission}, error={e}")
            return False
    
    async def get_menu_statistics(self) -> Dict[str, Any]:
        """获取菜单统计信息"""
        try:
            total_menus = await Menu.filter(del_flag='0').count()
            active_menus = await Menu.filter(del_flag='0', status=True).count()
            visible_menus = await Menu.filter(del_flag='0', visible=True).count()
            
            # 按菜单类型统计
            type_stats = {}
            for menu_type in [MenuType.DIRECTORY, MenuType.MENU, MenuType.BUTTON]:
                count = await Menu.filter(del_flag='0', menu_type=menu_type).count()
                type_stats[menu_type.value] = count
            
            # 按层级统计
            root_menus = await Menu.filter(del_flag='0', parent_id__isnull=True).count()
            child_menus = total_menus - root_menus
            
            return {
                'total_menus': total_menus,
                'active_menus': active_menus,
                'inactive_menus': total_menus - active_menus,
                'visible_menus': visible_menus,
                'hidden_menus': total_menus - visible_menus,
                'type_stats': type_stats,
                'root_menus': root_menus,
                'child_menus': child_menus,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"获取菜单统计信息失败: error={e}")
            return {}
    
    async def refresh_user_menu_cache(self, user_id: int) -> bool:
        """刷新用户菜单缓存"""
        try:
            # 清理用户菜单缓存
            cache_keys = [
                f"user_menus:{user_id}:True",
                f"user_menus:{user_id}:False"
            ]
            
            for cache_key in cache_keys:
                await permission_cache_manager.delete_cached_data(cache_key)
            
            logger.info(f"刷新用户菜单缓存成功: user_id={user_id}")
            return True
        
        except Exception as e:
            logger.error(f"刷新用户菜单缓存失败: user_id={user_id}, error={e}")
            return False
    
    async def _menu_to_dict(self, menu: Menu) -> Dict[str, Any]:
        """将菜单对象转换为字典"""
        return {
            'id': menu.id,
            'name': menu.name,
            'path': menu.path,
            'component': menu.component,
            'menu_type': menu.menu_type.value if menu.menu_type else None,
            'icon': menu.icon,
            'order_num': menu.order_num,
            'parent_id': menu.parent_id,
            'perms': menu.perms,
            'visible': menu.visible,
            'status': menu.status,
            'is_frame': menu.is_frame,
            'is_cache': menu.is_cache,
            'query': menu.query,
            'created_at': menu.created_at.isoformat() if menu.created_at else None,
            'updated_at': menu.updated_at.isoformat() if menu.updated_at else None
        }
    
    def _build_menu_tree(self, menus: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """构建菜单树结构"""
        try:
            # 创建菜单字典，便于查找
            menu_dict = {menu['id']: {**menu, 'children': []} for menu in menus}
            
            # 构建树结构
            tree = []
            for menu in menus:
                menu_node = menu_dict[menu['id']]
                parent_id = menu.get('parent_id')
                
                if parent_id and parent_id in menu_dict:
                    menu_dict[parent_id]['children'].append(menu_node)
                else:
                    tree.append(menu_node)
            
            # 递归排序子菜单
            def sort_children(node):
                if node.get('children'):
                    node['children'].sort(key=lambda x: (x.get('order_num', 0), x.get('id', 0)))
                    for child in node['children']:
                        sort_children(child)
            
            # 排序根菜单和子菜单
            tree.sort(key=lambda x: (x.get('order_num', 0), x.get('id', 0)))
            for node in tree:
                sort_children(node)
            
            return tree
        
        except Exception as e:
            logger.error(f"构建菜单树失败: error={e}")
            return []
    
    async def _clear_menu_cache(self) -> None:
        """清理菜单相关缓存"""
        try:
            # 清理所有用户菜单缓存
            await permission_cache_manager.clear_pattern("user_menus:*")
            logger.debug("清理菜单缓存成功")
        
        except Exception as e:
            logger.error(f"清理菜单缓存失败: error={e}")


# 全局菜单权限服务实例
menu_permission_service = MenuPermissionService()


# 便捷函数
async def get_user_menus(user_id: int, include_hidden: bool = False) -> List[Dict[str, Any]]:
    """获取用户菜单列表"""
    return await menu_permission_service.get_user_menus(user_id, include_hidden)


async def get_user_menu_tree(user_id: int, include_hidden: bool = False) -> List[Dict[str, Any]]:
    """获取用户菜单树"""
    return await menu_permission_service.get_user_menu_tree(user_id, include_hidden)


async def check_menu_permission(user_id: int, permission: str) -> bool:
    """检查菜单权限"""
    return await menu_permission_service.check_menu_permission(user_id, permission)


if __name__ == "__main__":
    # 测试菜单权限服务
    import asyncio
    
    async def test_menu_service():
        service = MenuPermissionService()
        
        print("菜单权限服务测试")
        
        # 测试获取菜单统计
        # stats = await service.get_menu_statistics()
        # print(f"菜单统计: {stats}")
        
        print("菜单权限服务测试完成")
    
    asyncio.run(test_menu_service())