from typing import List

from app.core.crud import CRUDBase
from app.core.optimized_crud import OptimizedCRUDBase
from app.models.admin import Menu, Role, SysApiEndpoint
from app.schemas.roles import RoleCreate, RoleUpdate
from app.core.permission_decorators import role_permission_change_event
from app.core.query_optimizer import monitor_performance, cached_query

# 导入自动包含父菜单的辅助函数
async def get_menu_ids_with_parents(menu_ids: List[int]) -> List[int]:
    """
    获取菜单ID列表及其所有父菜单ID
    
    Args:
        menu_ids: 原始菜单ID列表
        
    Returns:
        包含原始菜单ID和所有父菜单ID的完整列表
    """
    if not menu_ids:
        return []
    
    all_menu_ids = set(menu_ids)
    
    # 获取所有相关菜单信息
    menus = await Menu.filter(id__in=menu_ids).all()
    
    # 递归获取所有父菜单ID
    for menu in menus:
        parent_id = menu.parent_id
        while parent_id and parent_id != 0 and parent_id not in all_menu_ids:
            all_menu_ids.add(parent_id)
            # 获取父菜单信息
            parent_menu = await Menu.get_or_none(id=parent_id)
            if parent_menu:
                parent_id = parent_menu.parent_id
            else:
                break
    
    return list(all_menu_ids)


class RoleController(OptimizedCRUDBase[Role, RoleCreate, RoleUpdate]):
    def __init__(self):
        super().__init__(model=Role, cache_ttl=900)  # 角色数据缓存15分钟

    @monitor_performance
    @cached_query(ttl=600)
    async def is_exist(self, name: str) -> bool:
        return await self.model.filter(name=name).exists()

    @role_permission_change_event
    @monitor_performance
    async def update_roles(self, role: Role, menu_ids: List[int], api_infos: List[dict]) -> None:
        await role.menus.clear()
        
        # 批量获取菜单对象
        if menu_ids:
            # 自动包含父菜单权限
            all_menu_ids = await get_menu_ids_with_parents(menu_ids)
            menus = await Menu.filter(id__in=all_menu_ids).all()
            for menu_obj in menus:
                await role.menus.add(menu_obj)

        await role.apis.clear()
        
        # 批量获取API对象
        if api_infos:
            api_conditions = []
            for item in api_infos:
                api_conditions.append(
                    Q(path=item.get("path")) & Q(method=item.get("method"))
                )
            
            if api_conditions:
                from tortoise.expressions import Q
                combined_q = api_conditions[0]
                for condition in api_conditions[1:]:
                    combined_q |= condition
                
                apis = await Api.filter(combined_q).all()
                for api_obj in apis:
                    await role.apis.add(api_obj)
        
        # 清理角色相关缓存
        self._clear_object_cache(role.id)
    
    @role_permission_change_event
    async def assign_sys_apis_to_role(self, role_id: int, sys_api_ids: List[int]) -> None:
        """为角色分配V2系统API权限"""
        role = await self.get(id=role_id)
        await role.apis.clear()
        for sys_api_id in sys_api_ids:
            sys_api_obj = await SysApiEndpoint.get(id=sys_api_id)
            await role.apis.add(sys_api_obj)
    
    @role_permission_change_event
    async def remove_sys_apis_from_role(self, role_id: int, sys_api_ids: List[int]) -> None:
        """从角色移除V2系统API权限"""
        role = await self.get(id=role_id)
        for sys_api_id in sys_api_ids:
            sys_api_obj = await SysApiEndpoint.get(id=sys_api_id)
            await role.apis.remove(sys_api_obj)


role_controller = RoleController()
