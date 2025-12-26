"""
菜单管理 API v2
实现完整的菜单CRUD操作、树形结构查询和层级权限控制
"""
from typing import List, Optional
from fastapi import APIRouter, Request, Depends, Query
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.core.response_formatter_v2 import ResponseFormatterV2, APIv2ErrorDetail
from app.schemas.base import BatchDeleteRequest
from app.core.dependency import DependAuth
from app.models.admin import User, Menu
from app.core.batch_delete_decorators import require_batch_delete_permission
from app.controllers.menu import menu_controller
from app.schemas.menus import MenuCreate, MenuUpdate

router = APIRouter()

def build_menu_tree(menus: List[dict], parent_id: int = 0) -> List[dict]:
    """构建菜单树结构"""
    tree = []
    for menu in menus:
        if menu.get("parent_id") == parent_id:
            children = build_menu_tree(menus, menu["id"])
            if children:
                menu["children"] = children
            tree.append(menu)
    return tree

@router.get("/", summary="获取菜单列表", description="获取菜单列表 - 支持搜索、过滤和树形视图")
async def get_menus(
    request: Request,
    view: Optional[str] = Query(None, description="视图类型：tree=树形视图，默认为列表视图"),
    page: int = Query(1, ge=1, description="页码（树形视图时忽略）"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量（树形视图时忽略）"),
    name: Optional[str] = Query(None, description="菜单名称搜索"),
    menu_type: Optional[str] = Query(None, description="菜单类型过滤"),
    parent_id: Optional[int] = Query(None, description="父菜单ID"),
    include_hidden: bool = Query(False, description="是否包含隐藏菜单（仅树形视图）"),
    current_user: User = DependAuth
):
    """
    获取菜单列表 v2版本
    
    新功能：
    - 支持树形视图（view=tree）和列表视图
    - 标准化v2响应格式
    - 搜索和过滤
    - HATEOAS链接支持
    - 统一的查询入口
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 构建查询条件
        q = Q()
        query_params = {}
        
        if name:
            q &= Q(name__icontains=name)
            query_params['name'] = name
            
        if menu_type:
            q &= Q(menu_type=menu_type)
            query_params['menu_type'] = menu_type
            
        if parent_id is not None:
            q &= Q(parent_id=parent_id)
            query_params['parent_id'] = parent_id
            
        # 树形视图处理
        if view == "tree":
            # 获取所有菜单（不分页）
            all_menus = await Menu.filter(q).order_by('order_num', 'id')
            
            # 转换为字典格式并添加增强字段
            menu_data = []
            for menu in all_menus:
                menu_dict = await menu.to_dict()
                
                # 添加v2版本增强字段
                children_count = await Menu.filter(parent_id=menu.id).count()
                roles_count = await menu.roles.all().count() if hasattr(menu, 'roles') else 0
                
                menu_dict["stats"] = {
                    "children_count": children_count,
                    "roles_count": roles_count
                }
                
                # 添加层级信息
                menu_dict["level"] = await get_menu_level(menu.id)
                
                menu_data.append(menu_dict)
            
            # 构建树形结构
            tree_data = build_menu_tree(menu_data)
            
            return formatter.success(
                data={
                    "tree": tree_data,
                    "total": len(menu_data),
                    "tree_depth": calculate_tree_depth(tree_data)
                },
                message="Menu tree retrieved successfully",
                resource_type="menus",
                related_resources={
                    "list_view": str(request.url).replace("view=tree", "view=list")
                }
            )
        
        # 列表视图处理（默认）
        total, menu_objs = await menu_controller.list(
            page=page,
            page_size=page_size,
            search=q,
            order=['order_num', 'id']  # 添加默认排序：按order_num和id升序
        )
        
        # 转换数据格式
        menu_data = []
        for menu in menu_objs:
            menu_dict = await menu.to_dict()
            
            # 添加v2版本增强字段
            children_count = await Menu.filter(parent_id=menu.id).count()
            roles_count = await menu.roles.all().count() if hasattr(menu, 'roles') else 0
            
            menu_dict["stats"] = {
                "children_count": children_count,
                "roles_count": roles_count
            }
            
            # 添加层级信息
            menu_dict["level"] = await get_menu_level(menu.id)
            
            menu_data.append(menu_dict)
        
        return formatter.paginated_success(
            data=menu_data,
            total=total,
            page=page,
            page_size=page_size,
            message="Menus retrieved successfully",
            resource_type="menus",
            query_params=query_params
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to retrieve menus: {str(e)}")


@router.get("/{menu_id}/children", summary="获取子菜单", description="获取指定菜单的直接子菜单列表", dependencies=[DependAuth])
async def get_menu_children(
    menu_id: int,
    request: Request,
    include_hidden: bool = Query(False, description="是否包含隐藏菜单"),
    current_user: User = DependAuth
):
    """
    获取子菜单 v2版本
    
    新功能：
    - 按需加载子菜单
    - 标准化v2响应格式
    - 支持隐藏菜单过滤
    - 性能优化的子菜单查询
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查父菜单是否存在
        parent_menu = await Menu.get_or_none(id=menu_id)
        if not parent_menu:
            return formatter.not_found(
                message=f"Parent menu with id {menu_id} not found",
                details=[APIv2ErrorDetail(
                    field="menu_id",
                    message=f"Menu with id {menu_id} does not exist",
                    code="MENU_NOT_FOUND"
                )]
            )
        
        # 构建查询条件
        q = Q(parent_id=menu_id)
        if not include_hidden:
            q &= Q(is_hidden=False)
        
        # 获取子菜单
        children = await Menu.filter(q).order_by('order_num', 'id')
        
        # 转换数据格式
        children_data = []
        for child in children:
            child_dict = await child.to_dict()
            
            # 添加v2版本增强字段
            child_dict["stats"] = {
                "children_count": await Menu.filter(parent_id=child.id).count(),
                "roles_count": await child.role_menus.all().count()
            }
            
            # 添加层级信息
            child_dict["level"] = await get_menu_level(child.id)
            
            children_data.append(child_dict)
        
        return formatter.success(
            data={
                "parent": {
                    "id": parent_menu.id,
                    "name": parent_menu.name,
                    "path": parent_menu.path
                },
                "children": children_data,
                "total": len(children_data)
            },
            message=f"Children of menu '{parent_menu.name}' retrieved successfully",
            resource_type="menus",
            related_resources={
                "parent": f"/api/v2/menus/{menu_id}",
                "tree_view": f"/api/v2/menus?view=tree&parent_id={menu_id}"
            }
        )
        
    except Exception as e:
         return formatter.internal_error(f"Failed to retrieve menu children: {str(e)}")


@router.post("/batch", summary="批量创建菜单", description="批量创建多个菜单", dependencies=[DependAuth])
async def batch_create_menus(
    request: Request,
    menus_data: List[MenuCreate],
    current_user: User = DependAuth
):
    """
    批量创建菜单 v2版本
    
    新功能：
    - 支持批量创建多个菜单
    - 事务性操作保证数据一致性
    - 详细的验证和错误报告
    - 标准化v2响应格式
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        if not menus_data:
            return formatter.bad_request(
                message="No menu data provided",
                details=[APIv2ErrorDetail(
                    field="menus_data",
                    message="At least one menu is required for batch creation",
                    code="EMPTY_BATCH_DATA"
                )]
            )
        
        if len(menus_data) > 50:  # 限制批量操作数量
            return formatter.bad_request(
                message="Too many menus in batch operation",
                details=[APIv2ErrorDetail(
                    field="menus_data",
                    message="Maximum 50 menus allowed per batch operation",
                    code="BATCH_SIZE_EXCEEDED"
                )]
            )
        
        created_menus = []
        failed_menus = []
        
        async with in_transaction("default"):
            for index, menu_data in enumerate(menus_data):
                try:
                    # 检查菜单名是否已存在
                    existing_menu = await Menu.get_or_none(name=menu_data.name)
                    if existing_menu:
                        failed_menus.append({
                            "index": index,
                            "data": menu_data.dict(),
                            "error": f"Menu with name '{menu_data.name}' already exists"
                        })
                        continue
                    
                    # 检查路径是否已存在
                    if menu_data.path:
                        existing_path = await Menu.get_or_none(path=menu_data.path)
                        if existing_path:
                            failed_menus.append({
                                "index": index,
                                "data": menu_data.dict(),
                                "error": f"Menu with path '{menu_data.path}' already exists"
                            })
                            continue
                    
                    # 验证父菜单
                    if menu_data.parent_id:
                        parent_menu = await Menu.get_or_none(id=menu_data.parent_id)
                        if not parent_menu:
                            failed_menus.append({
                                "index": index,
                                "data": menu_data.dict(),
                                "error": f"Parent menu with id {menu_data.parent_id} not found"
                            })
                            continue
                    
                    # 创建菜单
                    menu_obj = await menu_controller.create(menu_data)
                    menu_dict = await menu_obj.to_dict()
                    
                    # 添加增强字段
                    menu_dict["stats"] = {
                        "children_count": 0,
                        "roles_count": 0
                    }
                    menu_dict["level"] = await get_menu_level(menu_obj.id)
                    
                    created_menus.append(menu_dict)
                    
                except Exception as e:
                    failed_menus.append({
                        "index": index,
                        "data": menu_data.dict(),
                        "error": str(e)
                    })
        
        # 构建响应
        response_data = {
            "successful": created_menus,
            "failed": failed_menus,
            "summary": {
                "total_requested": len(menus_data),
                "created_count": len(created_menus),
                "failed_count": len(failed_menus),
                "success_rate": len(created_menus) / len(menus_data) * 100
            }
        }
        
        if failed_menus:
            return formatter.partial_success(
                data=response_data,
                message=f"Batch creation completed with {len(failed_menus)} failures",
                success_count=len(created_menus),
                failure_count=len(failed_menus),
                errors=failed_menus,
                resource_type="menus"
            )
        else:
            return formatter.success(
                data=response_data,
                message=f"Successfully created {len(created_menus)} menus",
                code=201
            )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to batch create menus: {str(e)}")


@router.patch("/batch", summary="批量更新菜单", description="批量更新多个菜单", dependencies=[DependAuth])
async def batch_update_menus(
    request: Request,
    updates: List[dict],
    current_user: User = DependAuth
):
    """
    批量更新菜单 v2版本
    
    新功能：
    - 支持批量更新多个菜单
    - 事务性操作保证数据一致性
    - 支持部分字段更新
    - 详细的验证和错误报告
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        if not updates:
            return formatter.bad_request(
                message="No update data provided",
                details=[APIv2ErrorDetail(
                    field="updates",
                    message="At least one update is required for batch operation",
                    code="EMPTY_BATCH_DATA"
                )]
            )
        
        if len(updates) > 50:
            return formatter.bad_request(
                message="Too many updates in batch operation",
                details=[APIv2ErrorDetail(
                    field="updates",
                    message="Maximum 50 updates allowed per batch operation",
                    code="BATCH_SIZE_EXCEEDED"
                )]
            )
        
        updated_menus = []
        failed_updates = []
        
        async with in_transaction("default"):
            for index, update_data in enumerate(updates):
                try:
                    menu_id = update_data.get('id')
                    if not menu_id:
                        failed_updates.append({
                            "index": index,
                            "data": update_data,
                            "error": "Menu ID is required for update"
                        })
                        continue
                    
                    # 检查菜单是否存在
                    menu_obj = await Menu.get_or_none(id=menu_id)
                    if not menu_obj:
                        failed_updates.append({
                            "index": index,
                            "data": update_data,
                            "error": f"Menu with id {menu_id} not found"
                        })
                        continue
                    
                    # 验证更新数据
                    update_fields = {k: v for k, v in update_data.items() if k != 'id'}
                    
                    # 检查名称唯一性
                    if 'name' in update_fields:
                        existing_name = await Menu.get_or_none(name=update_fields['name'])
                        if existing_name and existing_name.id != menu_id:
                            failed_updates.append({
                                "index": index,
                                "data": update_data,
                                "error": f"Menu name '{update_fields['name']}' already exists"
                            })
                            continue
                    
                    # 检查路径唯一性
                    if 'path' in update_fields and update_fields['path']:
                        existing_path = await Menu.get_or_none(path=update_fields['path'])
                        if existing_path and existing_path.id != menu_id:
                            failed_updates.append({
                                "index": index,
                                "data": update_data,
                                "error": f"Menu path '{update_fields['path']}' already exists"
                            })
                            continue
                    
                    # 验证父菜单和循环引用
                    if 'parent_id' in update_fields:
                        parent_id = update_fields['parent_id']
                        if parent_id:
                            parent_menu = await Menu.get_or_none(id=parent_id)
                            if not parent_menu:
                                failed_updates.append({
                                    "index": index,
                                    "data": update_data,
                                    "error": f"Parent menu with id {parent_id} not found"
                                })
                                continue
                            
                            # 检查循环引用
                            if await is_circular_reference(menu_id, parent_id):
                                failed_updates.append({
                                    "index": index,
                                    "data": update_data,
                                    "error": "Circular reference detected"
                                })
                                continue
                    
                    # 更新菜单
                    for field, value in update_fields.items():
                        setattr(menu_obj, field, value)
                    
                    await menu_obj.save()
                    
                    # 构建响应数据
                    menu_dict = await menu_obj.to_dict()
                    menu_dict["stats"] = {
                        "children_count": await Menu.filter(parent_id=menu_obj.id).count(),
                        "roles_count": await menu_obj.role_menus.all().count()
                    }
                    menu_dict["level"] = await get_menu_level(menu_obj.id)
                    
                    updated_menus.append(menu_dict)
                    
                except Exception as e:
                    failed_updates.append({
                        "index": index,
                        "data": update_data,
                        "error": str(e)
                    })
        
        # 构建响应
        response_data = {
            "successful": updated_menus,
            "failed": failed_updates,
            "summary": {
                "total_requested": len(updates),
                "updated_count": len(updated_menus),
                "failed_count": len(failed_updates),
                "success_rate": len(updated_menus) / len(updates) * 100
            }
        }
        
        if failed_updates:
            return formatter.partial_success(
                data=response_data,
                message=f"Batch update completed with {len(failed_updates)} failures",
                success_count=len(updated_menus),
                failure_count=len(failed_updates),
                errors=failed_updates,
                resource_type="menus"
            )
        else:
            return formatter.success(
                data=response_data,
                message=f"Successfully updated {len(updated_menus)} menus"
            )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to batch update menus: {str(e)}")


@router.delete("/batch", summary="批量删除菜单", description="批量删除多个菜单", dependencies=[DependAuth])
@require_batch_delete_permission("menu")
async def batch_delete_menus(
    request: Request,
    batch_request: BatchDeleteRequest,
    current_user: User = DependAuth
):
    """
    批量删除菜单 v2版本
    
    使用标准化数据格式：{"ids": [1, 2, 3], "force": false}
    返回标准化响应格式，包含用户友好的错误提示
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        from app.services.batch_delete_service import menu_batch_delete_service
        from tortoise.transactions import in_transaction
        
        menu_ids = batch_request.ids
        force = batch_request.force
        
        if not menu_ids:
            return formatter.validation_error(
                message="菜单ID列表不能为空",
                details=[APIv2ErrorDetail(
                    field="ids",
                    code="EMPTY_LIST",
                    message="菜单ID列表不能为空",
                    value=menu_ids
                )]
            )
        
        async with in_transaction("default"):
            # 使用标准化批量删除服务
            result = await menu_batch_delete_service.batch_delete(
                ids=menu_ids,
                force=force
            )
            
            # 生成用户友好的响应消息
            if result.failed_count == 0:
                message = f"成功删除 {result.deleted_count} 个菜单"
            elif result.deleted_count == 0:
                failed_reasons = [item.reason for item in result.failed]
                message = f"删除失败：{'; '.join(failed_reasons)}"
            else:
                failed_details = [f"{item.name or item.id}：{item.reason}" for item in result.failed]
                message = f"批量删除完成：成功删除 {result.deleted_count} 个，失败 {result.failed_count} 个菜单。失败原因：{'; '.join(failed_details)}"
            
            return formatter.success(
                data=result.model_dump(),
                message=message,
                resource_type="menus"
            )
        
    except Exception as e:
        return formatter.internal_error(f"批量删除菜单失败: {str(e)}")

@router.get("/tree", summary="获取菜单树", description="获取完整的菜单树结构")
async def get_menu_tree(
    request: Request,
    include_hidden: bool = Query(False, description="是否包含隐藏菜单"),
    current_user: User = DependAuth
):
    """
    获取菜单树 v2版本
    
    新功能：
    - 完整的树形结构
    - 可选择包含隐藏菜单
    - 层级权限信息
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 构建查询条件
        q = Q()
        if not include_hidden:
            q &= Q(visible=True)  # 使用visible字段而不是is_hidden
        
        # 获取所有菜单
        menus = await Menu.filter(q).order_by("parent_id", "order_num").all()
        
        # 转换为字典格式
        menu_dicts = []
        for menu in menus:
            menu_dict = await menu.to_dict()
            
            # 添加增强信息
            children_count = await Menu.filter(parent_id=menu.id).count()
            # 统计关联的角色数量
            roles_count = await menu.roles.all().count() if hasattr(menu, 'roles') else 0
            
            menu_dict["stats"] = {
                "children_count": children_count,
                "roles_count": roles_count
            }
            menu_dict["level"] = await get_menu_level(menu.id)
            
            menu_dicts.append(menu_dict)
        
        # 构建树形结构
        tree_data = build_menu_tree(menu_dicts)
        
        # 统计信息
        stats = {
            "total_menus": len(menu_dicts),
            "root_menus": len(tree_data),
            "max_depth": calculate_tree_depth(tree_data),
            "menu_types": {}
        }
        
        # 统计菜单类型
        for menu in menu_dicts:
            menu_type = menu.get("menu_type", "unknown")
            stats["menu_types"][menu_type] = stats["menu_types"].get(menu_type, 0) + 1
        
        response_data = {
            "tree": tree_data,
            "stats": stats
        }
        
        return formatter.success(
            data=response_data,
            message="Menu tree retrieved successfully",
            resource_type="menus"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to retrieve menu tree: {str(e)}")

@router.get("/{menu_id}", summary="获取菜单详情", description="根据ID获取菜单详细信息", dependencies=[DependAuth])
async def get_menu(
    menu_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """
    获取菜单详情 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 增强的菜单信息
    - 父子关系信息
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        from tortoise.exceptions import DoesNotExist
        try:
            menu = await menu_controller.get(id=menu_id)
        except DoesNotExist:
            return formatter.not_found(
                message=f"Menu with id {menu_id} not found",
                resource_type="menu",
                resource_id=str(menu_id)
            )
        
        if not menu:
            return formatter.not_found(
                message=f"Menu with id {menu_id} not found",
                resource_type="menu",
                resource_id=str(menu_id)
            )
        
        # 获取菜单详细信息
        menu_dict = await menu.to_dict()
        
        # 添加v2版本增强字段
        children_count = await Menu.filter(parent_id=menu.id).count()
        roles_count = await menu.role_menus.all().count()
        menu_dict["stats"] = {
            "children_count": children_count,
            "roles_count": roles_count
        }
        
        # 添加层级信息
        level = await get_menu_level(menu.id)
        menu_dict["level"] = level
        
        # 获取父菜单信息
        if menu.parent_id and menu.parent_id > 0:
            parent_menu = await Menu.get_or_none(id=menu.parent_id)
            if parent_menu:
                menu_dict["parent"] = {
                    "id": parent_menu.id,
                    "name": parent_menu.name,
                    "path": parent_menu.path
                }
        else:
            menu_dict["parent"] = None
        
        # 获取子菜单列表
        children = await Menu.filter(parent_id=menu.id).order_by("order_num").all()
        menu_dict["children"] = [
            {
                "id": child.id,
                "name": child.name,
                "path": child.path,
                "menu_type": child.menu_type,
                "order": child.order,
                "is_hidden": child.is_hidden
            }
            for child in children
        ]
        
        # 构建相关资源链接
        related_resources = {
            "children": f"/api/v2/menus?parent_id={menu_id}",
            "roles": f"/api/v2/menus/{menu_id}/roles"
        }
        
        if menu.parent_id and menu.parent_id > 0:
            related_resources["parent"] = f"/api/v2/menus/{menu.parent_id}"
        
        return formatter.success(
            data=menu_dict,
            message="Menu details retrieved successfully",
            resource_id=str(menu_id),
            resource_type="menus",
            related_resources=related_resources
        )
        
    except Exception as e:
        return formatter.internal_error(
            message="Failed to retrieve menu",
            component="menu_service",
            error_detail=str(e)
        )

@router.post("/", summary="创建菜单", description="创建新菜单", dependencies=[DependAuth])
async def create_menu(
    request: Request,
    menu_in: MenuCreate,
    current_user: User = DependAuth
):
    """
    创建菜单 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 增强的验证和错误处理
    - 层级验证
    """
    from loguru import logger
    from pydantic import ValidationError
    
    formatter = ResponseFormatterV2(request)
    
    # 记录接收到的原始数据
    logger.info(f"Creating menu with data: {menu_in.dict()}")
    
    # 验证菜单名是否已存在
    existing_menu = await Menu.filter(name=menu_in.name).first()
    if existing_menu:
        return formatter.validation_error(
            message="Menu with this name already exists",
            details=[APIv2ErrorDetail(
                field="name",
                code="DUPLICATE_NAME",
                message="Menu name is already taken",
                value=menu_in.name
            )]
        )
    
    # 验证路径是否已存在
    if menu_in.path:
        existing_path = await Menu.filter(path=menu_in.path).first()
        if existing_path:
            return formatter.validation_error(
                message="Menu with this path already exists",
                details=[APIv2ErrorDetail(
                    field="path",
                    code="DUPLICATE_PATH",
                    message="Menu path is already taken",
                    value=menu_in.path
                )]
            )
    
    # 验证父菜单是否存在
    if menu_in.parent_id and menu_in.parent_id > 0:
        parent_menu = await Menu.get_or_none(id=menu_in.parent_id)
        if not parent_menu:
            return formatter.validation_error(
                message="Parent menu not found",
                details=[APIv2ErrorDetail(
                    field="parent_id",
                    code="PARENT_NOT_FOUND",
                    message="Specified parent menu does not exist",
                    value=menu_in.parent_id
                )]
            )
    
    try:
        # 创建菜单
        new_menu = await menu_controller.create(obj_in=menu_in)
        
        # 获取创建后的菜单信息
        menu_dict = await new_menu.to_dict()
        menu_dict["level"] = await get_menu_level(new_menu.id)
        
        return formatter.success(
            data=menu_dict,
            message="Menu created successfully",
            code=201,
            resource_id=str(new_menu.id),
            resource_type="menus"
        )
        
    except ValidationError as ve:
        # 记录详细的验证错误
        logger.error(f"Menu validation error: {ve.errors()}")
        error_details = []
        for error in ve.errors():
            error_details.append(APIv2ErrorDetail(
                field=".".join(str(loc) for loc in error['loc']),
                code="VALIDATION_ERROR",
                message=error['msg'],
                value=error.get('input', 'N/A')
            ))
        return formatter.validation_error(
            message="Menu validation failed",
            details=error_details
        )
    except Exception as e:
        logger.error(f"Failed to create menu: {str(e)}")
        return formatter.internal_error(f"Failed to create menu: {str(e)}")

@router.patch("/{menu_id}", summary="部分更新菜单", description="部分更新菜单信息", dependencies=[DependAuth])
async def update_menu(
    menu_id: int,
    request: Request,
    menu_in: MenuUpdate,
    current_user: User = DependAuth
):
    """
    部分更新菜单 v2版本
    
    新功能：
    - 支持部分字段更新（PATCH语义）
    - 标准化v2响应格式
    - 增强的验证和错误处理
    - 层级验证和循环引用检测
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查菜单是否存在
        from tortoise.exceptions import DoesNotExist
        try:
            menu = await menu_controller.get(id=menu_id)
        except DoesNotExist:
            return formatter.not_found(f"Menu with id {menu_id} not found", "menu")
        
        if not menu:
            return formatter.not_found(f"Menu with id {menu_id} not found", "menu")
        
        # 验证菜单名是否被其他菜单使用
        if menu_in.name is not None and menu_in.name != menu.name:
            existing_menu = await Menu.filter(name=menu_in.name).first()
            if existing_menu and existing_menu.id != menu_id:
                return formatter.validation_error(
                    message="Menu name is already taken by another menu",
                    details=[APIv2ErrorDetail(
                        field="name",
                        code="DUPLICATE_NAME",
                        message="Menu name is already taken",
                        value=menu_in.name
                    )]
                )
        
        # 验证路径是否被其他菜单使用
        if menu_in.path is not None and menu_in.path and menu_in.path != menu.path:
            existing_path = await Menu.filter(path=menu_in.path).first()
            if existing_path and existing_path.id != menu_id:
                return formatter.validation_error(
                    message="Menu path is already taken by another menu",
                    details=[APIv2ErrorDetail(
                        field="path",
                        code="DUPLICATE_PATH",
                        message="Menu path is already taken",
                        value=menu_in.path
                    )]
                )
        
        # 验证父菜单设置（防止循环引用）
        if menu_in.parent_id is not None and menu_in.parent_id:
            if menu_in.parent_id == menu_id:
                return formatter.validation_error(
                    message="Menu cannot be its own parent",
                    details=[APIv2ErrorDetail(
                        field="parent_id",
                        code="CIRCULAR_REFERENCE",
                        message="Menu cannot be its own parent",
                        value=menu_in.parent_id
                    )]
                )
            
            # 检查是否会形成循环引用
            if await is_circular_reference(menu_id, menu_in.parent_id):
                return formatter.validation_error(
                    message="This would create a circular reference",
                    details=[APIv2ErrorDetail(
                        field="parent_id",
                        code="CIRCULAR_REFERENCE",
                        message="Setting this parent would create a circular reference",
                        value=menu_in.parent_id
                    )]
                )
        
        # 更新菜单
        updated_menu = await menu_controller.update(id=menu_id, obj_in=menu_in)
        
        # 获取更新后的菜单信息
        menu_dict = await updated_menu.to_dict()
        menu_dict["level"] = await get_menu_level(updated_menu.id)
        
        return formatter.success(
            data=menu_dict,
            message="Menu updated successfully",
            resource_id=str(menu_id),
            resource_type="menus"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to update menu: {str(e)}")


@router.put("/{menu_id}", summary="完整更新菜单", description="完整更新菜单信息", dependencies=[DependAuth])
async def put_update_menu(
    menu_id: int,
    request: Request,
    menu_in: MenuUpdate,
    current_user: User = DependAuth
):
    """
    完整更新菜单 v2版本 (PUT方法)
    
    这是 PATCH 方法的别名，提供 PUT 语义支持以保持前端兼容性
    """
    # 直接调用 PATCH 方法的实现
    return await update_menu(menu_id, request, menu_in, current_user)


@router.get("/{menu_id}/usage", summary="检查菜单使用情况", description="检查菜单是否被角色使用或有子菜单", dependencies=[DependAuth])
async def check_menu_usage(
    menu_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """
    检查菜单使用情况
    
    Args:
        menu_id: 菜单ID
        request: 请求对象
        current_user: 当前用户
    
    Returns:
        菜单使用情况信息
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查菜单是否存在
        menu = await Menu.get_or_none(id=menu_id)
        if not menu:
            return formatter.not_found("Menu not found")
        
        # 检查是否有子菜单
        children_count = await Menu.filter(parent_id=menu_id).count()
        
        # 检查是否有角色使用此菜单
        roles_count = await menu.role_menus.all().count()
        
        # 获取使用此菜单的角色信息
        roles = []
        if roles_count > 0:
            role_menus = await menu.role_menus.all()
            roles = [{
                "id": rm.id,
                "name": rm.role_name
            } for rm in role_menus]
        
        usage_info = {
            "can_delete": children_count == 0 and roles_count == 0,
            "children_count": children_count,
            "roles_count": roles_count,
            "assigned_roles": roles,
            "blocking_reasons": []
        }
        
        # 添加阻止删除的原因
        if children_count > 0:
            usage_info["blocking_reasons"].append({
                "type": "HAS_CHILDREN",
                "message": f"菜单有 {children_count} 个子菜单",
                "count": children_count
            })
        
        if roles_count > 0:
            usage_info["blocking_reasons"].append({
                "type": "ASSIGNED_TO_ROLES",
                "message": f"菜单已分配给 {roles_count} 个角色",
                "count": roles_count
            })
        
        return formatter.success(
            data=usage_info,
            message="Menu usage information retrieved successfully"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to check menu usage: {str(e)}")


@router.delete("/{menu_id}", summary="删除菜单", description="删除指定菜单", dependencies=[DependAuth])
async def delete_menu(
    menu_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """
    删除菜单 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 层级删除检查
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查菜单是否存在
        from tortoise.exceptions import DoesNotExist
        try:
            menu = await menu_controller.get(id=menu_id)
        except DoesNotExist:
            return formatter.not_found(f"Menu with id {menu_id} not found", "menu")
        
        if not menu:
            return formatter.not_found(f"Menu with id {menu_id} not found", "menu")
        
        # 检查是否有子菜单
        children_count = await Menu.filter(parent_id=menu_id).count()
        if children_count > 0:
            return formatter.validation_error(
                message="Cannot delete menu that has child menus",
                details=[APIv2ErrorDetail(
                    field="menu_id",
                    code="HAS_CHILDREN",
                    message=f"Menu has {children_count} child menus",
                    value=menu_id
                )]
            )
        
        # 检查是否有角色使用此菜单
        roles_count = await menu.role_menus.all().count()
        if roles_count > 0:
            return formatter.validation_error(
                message="Cannot delete menu that is assigned to roles",
                details=[APIv2ErrorDetail(
                    field="menu_id",
                    code="MENU_IN_USE",
                    message=f"Menu is assigned to {roles_count} roles",
                    value=menu_id
                )]
            )
        
        # 删除菜单
        await menu_controller.remove(id=menu_id)
        
        return formatter.success(
            message="Menu deleted successfully",
            code=204
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to delete menu: {str(e)}")

# 辅助函数
async def get_menu_level(menu_id: int) -> int:
    """获取菜单层级"""
    level = 0
    current_id = menu_id
    
    while current_id:
        menu = await Menu.get_or_none(id=current_id)
        if not menu or menu.parent_id == 0:
            break
        current_id = menu.parent_id
        level += 1
        
        # 防止无限循环
        if level > 10:
            break
    
    return level

async def is_circular_reference(menu_id: int, parent_id: int) -> bool:
    """检查是否会形成循环引用"""
    current_id = parent_id
    visited = set()
    
    while current_id and current_id not in visited:
        if current_id == menu_id:
            return True
        
        visited.add(current_id)
        menu = await Menu.get_or_none(id=current_id)
        if not menu:
            break
        
        current_id = menu.parent_id if menu.parent_id != 0 else None
    
    return False

def calculate_tree_depth(tree: List[dict]) -> int:
    """计算树的最大深度"""
    if not tree:
        return 0
    
    max_depth = 0
    for node in tree:
        depth = 1
        if "children" in node:
            depth += calculate_tree_depth(node["children"])
        max_depth = max(max_depth, depth)
    
    return max_depth