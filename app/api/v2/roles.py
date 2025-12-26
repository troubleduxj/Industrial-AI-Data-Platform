"""
角色管理 API v2
实现完整的角色CRUD操作、权限配置和用户关联功能
"""
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Request, Depends, Query, Body
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.core.response_formatter_v2 import ResponseFormatterV2, APIv2ErrorDetail
from app.schemas.base import BatchDeleteRequest
from app.core.dependency import DependAuth
from app.models.admin import User, Role, Menu, SysApiEndpoint
from app.core.batch_delete_decorators import require_batch_delete_permission
from app.controllers.role import role_controller
from app.schemas.roles import RoleCreate, RoleUpdate, RolePatch, RoleUsersUpdate, RolePermissionsUpdate
from app.log import logger

router = APIRouter()


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


@router.get("/", summary="获取角色列表", description="获取角色列表，支持搜索、过滤、分页、排序", dependencies=[DependAuth])
async def get_roles(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词（支持角色名称、描述搜索）"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    created_after: Optional[str] = Query(None, description="创建时间起始（YYYY-MM-DD格式）"),
    created_before: Optional[str] = Query(None, description="创建时间结束（YYYY-MM-DD格式）"),
    sort_by: Optional[str] = Query("created_at", description="排序字段（name, created_at, updated_at）"),
    sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$", description="排序方向（asc升序, desc降序）"),
    current_user: User = DependAuth
):
    """
    获取角色列表 v2版本 - 简化版本
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 简化查询，先获取基本数据
        roles_query = Role.all()
        
        # 基本搜索
        if search:
            from tortoise.expressions import Q
            search_q = Q(role_name__icontains=search) | Q(remark__icontains=search)
            roles_query = roles_query.filter(search_q)
        
        # 基本状态过滤
        if is_active is not None:
            status_value = "0" if is_active else "1"
            roles_query = roles_query.filter(status=status_value)
        
        # 排序
        order_field = f"-{sort_by}" if sort_order == "desc" else sort_by
        roles_query = roles_query.order_by(order_field)
        
        # 分页
        total = await roles_query.count()
        offset = (page - 1) * size
        roles = await roles_query.offset(offset).limit(size)
        
        # 转换数据格式 - 修复字段名映射问题
        role_data = []
        for role in roles:
            role_dict = {
                "id": role.id,
                "name": role.role_name,  # 使用数据库字段名
                "desc": role.desc,  # 使用属性映射，而不是remark
                "role_key": role.role_key,
                "role_sort": role.role_sort,
                "data_scope": role.data_scope,
                "status": role.status,
                "del_flag": role.del_flag,
                "parent_id": role.parent_id,
                "created_at": role.created_at.strftime("%Y-%m-%d %H:%M:%S") if role.created_at else None,
                "updated_at": role.updated_at.strftime("%Y-%m-%d %H:%M:%S") if role.updated_at else None
            }
            role_data.append(role_dict)
        
        # 构建分页信息
        pagination = {
            "page": page,
            "page_size": size,
            "total": total,
            "total_pages": (total + size - 1) // size if total > 0 else 0,
            "has_next": page * size < total,
            "has_prev": page > 1
        }
        
        return formatter.success(
            data={
                "items": role_data,
                "pagination": pagination
            },
            message="Roles retrieved successfully",
            resource_type="roles"
        )
        
    except Exception as e:
        import traceback
        logger.error(f"Failed to retrieve roles: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return formatter.internal_error(f"Failed to retrieve roles: {str(e)}")

# 注意：/{role_id} GET路由已移动到文件末尾，以避免与/batch等更具体的路由冲突

@router.post("/", summary="创建角色", description="创建新角色")
async def create_role(
    request: Request,
    role_in: RoleCreate,
    current_user: User = DependAuth
):
    """
    创建角色 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 增强的验证和错误处理
    - 事务支持
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 验证角色名是否已存在
        existing_role = await Role.filter(role_name=role_in.role_name).first()
        if existing_role:
            return formatter.validation_error(
                message="Role with this name already exists",
                details=[APIv2ErrorDetail(
                    field="role_name",
                    code="DUPLICATE_NAME",
                    message="Role name is already taken",
                    value=role_in.role_name
                )]
            )
        
        # 验证父角色是否存在（如果指定了parent_id）
        if role_in.parent_id is not None:
            parent_role = await Role.filter(id=role_in.parent_id).first()
            if not parent_role:
                return formatter.validation_error(
                    message="Parent role not found",
                    details=[APIv2ErrorDetail(
                        field="parent_id",
                        code="PARENT_NOT_FOUND",
                        message="Specified parent role does not exist",
                        value=role_in.parent_id
                    )]
                )
            
            # 防止循环引用（不能将角色设为自己的子角色）
            if role_in.parent_id == getattr(role_in, 'id', None):
                return formatter.validation_error(
                    message="Cannot set role as its own parent",
                    details=[APIv2ErrorDetail(
                        field="parent_id",
                        code="CIRCULAR_REFERENCE",
                        message="Role cannot be its own parent",
                        value=role_in.parent_id
                    )]
                )
        
        # 创建角色
        async with in_transaction("default"):
            # 如果role_key为空，自动生成
            if not role_in.role_key:
                role_in.role_key = role_in.role_name.lower().replace(" ", "_").replace("-", "_")
            
            new_role = await role_controller.create(obj_in=role_in)
            
            # 分配V2系统API权限（推荐使用）
            if hasattr(role_in, 'sys_api_ids') and role_in.sys_api_ids:
                sys_apis = await SysApiEndpoint.filter(id__in=role_in.sys_api_ids).all()
                for sys_api in sys_apis:
                    await new_role.apis.add(sys_api)
            
            # V1 API权限已弃用，不再支持
            
            # 分配菜单权限
            if hasattr(role_in, 'menu_ids') and role_in.menu_ids:
                menus = await Menu.filter(id__in=role_in.menu_ids).all()
                for menu in menus:
                    await new_role.menus.add(menu)
        
        # 获取创建后的角色信息
        role_dict = await new_role.to_dict(m2m=True)
        
        return formatter.success(
            data=role_dict,
            message="Role created successfully",
            code=201,
            resource_id=str(new_role.id),
            resource_type="roles"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to create role: {str(e)}")

# PUT /{role_id} 路由已移动到文件末尾以避免与 /batch 路由冲突


# ==================== 权限管理接口 ====================

# GET /{role_id}/permissions 路由已移动到文件末尾以避免与 /batch 路由冲突


# POST /{role_id}/permissions 路由已移动到文件末尾以避免与 /batch 路由冲突


@router.delete("/batch", summary="批量删除角色", description="批量删除多个角色", dependencies=[DependAuth])
@require_batch_delete_permission("role")
async def batch_delete_roles(
    request: Request,
    batch_request: BatchDeleteRequest,
    current_user: User = DependAuth
):
    """
    批量删除角色 v2版本
    
    使用标准化数据格式：{"ids": [1, 2, 3]}
    返回标准化响应格式，包含用户友好的错误提示
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        from app.services.batch_delete_service import role_batch_delete_service
        from tortoise.transactions import in_transaction
        
        role_ids = batch_request.ids
        
        logger.info(f"Batch delete role_ids: {role_ids}")
        
        if not role_ids:
            return formatter.validation_error(
                message="角色ID列表不能为空",
                details=[APIv2ErrorDetail(
                    field="ids",
                    code="EMPTY_LIST",
                    message="角色ID列表不能为空",
                    value=role_ids
                )]
            )
        
        async with in_transaction("default"):
            # 使用标准化批量删除服务
            result = await role_batch_delete_service.batch_delete(ids=role_ids)
            
            # 生成用户友好的响应消息
            if result.failed_count == 0:
                message = f"成功删除 {result.deleted_count} 个角色"
            elif result.deleted_count == 0:
                failed_reasons = [item.reason for item in result.failed]
                message = f"删除失败：{'; '.join(failed_reasons)}"
            else:
                failed_details = [f"{item.name or item.id}：{item.reason}" for item in result.failed]
                message = f"批量删除完成：成功删除 {result.deleted_count} 个，失败 {result.failed_count} 个角色。失败原因：{'; '.join(failed_details)}"
            
            return formatter.success(
                data=result.model_dump(),
                message=message,
                resource_type="roles"
            )
        
    except Exception as e:
        return formatter.internal_error(f"批量删除角色失败: {str(e)}")


# DELETE /{role_id}/permissions 路由已移动到文件末尾以避免与 /batch 路由冲突


# /tree 路由已移动到文件末尾以避免与 /{role_id} 路由冲突

# ==================== 角色层级管理接口 ====================

# GET /tree 路由已移动到文件末尾以避免与 /{role_id} 路由冲突


# /{role_id}/tree 路由已移动到文件末尾以避免与 /tree 路由冲突


# 删除角色路由已移动到文件末尾以避免路由冲突

# GET /{role_id}/permissions 路由已移动到文件末尾以避免与 /batch 路由冲突

# PUT /{role_id}/permissions 路由已移动到文件末尾以避免与 /batch 路由冲突

# GET /{role_id}/users 路由已移动到文件末尾以避免与 /batch 路由冲突

# POST /{role_id}/users 路由已移动到文件末尾以避免与 /batch 路由冲突

# DELETE /{role_id}/users/{user_id} 路由已移动到文件末尾以避免与 /batch 路由冲突

# PATCH /{role_id} 路由已移动到文件末尾以避免与 /batch 路由冲突

# GET /{role_id}/children 路由已移动到文件末尾以避免与 /batch 路由冲突

# POST /{role_id}/children 路由已移动到文件末尾以避免与 /batch 路由冲突

@router.post("/batch", summary="批量创建角色", description="批量创建多个角色", dependencies=[DependAuth])
async def batch_create_roles(
    request: Request,
    batch_data: dict = Body(..., description="批量角色数据"),
    current_user: User = DependAuth
):
    """
    批量创建角色 v2版本
    
    新功能：
    - 批量创建多个角色
    - 标准化响应格式
    - 批量操作结果统计
    - 错误处理和回滚
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        if "roles" not in batch_data or not batch_data["roles"]:
            return formatter.validation_error(
                message="Roles list cannot be empty",
                details=[APIv2ErrorDetail(
                    field="roles",
                    code="EMPTY_LIST",
                    message="Roles list is required and cannot be empty",
                    value=batch_data.get("roles", [])
                )]
            )
        
        roles_data = batch_data["roles"]
        success_count = 0
        failed_count = 0
        created_roles = []
        failed_roles = []
        
        async with in_transaction("default"):
            for i, role_data in enumerate(roles_data):
                try:
                    # 验证必需字段
                    if "name" not in role_data:
                        failed_count += 1
                        failed_roles.append({
                            "index": i,
                            "data": role_data,
                            "reason": "Missing required field: name"
                        })
                        continue
                    
                    # 检查角色名是否已存在
                    existing_role = await Role.filter(name=role_data["name"]).first()
                    if existing_role:
                        failed_count += 1
                        failed_roles.append({
                            "index": i,
                            "data": role_data,
                            "reason": f"Role name '{role_data['name']}' already exists"
                        })
                        continue
                    
                    # 创建角色
                    new_role = await role_controller.create(obj_in=role_data)
                    role_dict = await new_role.to_dict()
                    role_dict["stats"] = {
                        "users_count": 0,
                        "apis_count": 0,
                        "menus_count": 0
                    }
                    
                    created_roles.append(role_dict)
                    success_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    failed_roles.append({
                        "index": i,
                        "data": role_data,
                        "reason": str(e)
                    })
        
        return formatter.success(
            data={
                "action": "create",
                "total_requested": len(roles_data),
                "success_count": success_count,
                "failed_count": failed_count,
                "created": created_roles,
                "failed": failed_roles
            },
            message=f"Batch create completed. {success_count} succeeded, {failed_count} failed.",
            code=201,
            resource_type="roles"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to execute batch create: {str(e)}")

@router.put("/batch", summary="批量更新角色", description="批量更新多个角色", dependencies=[DependAuth])
async def batch_update_roles(
    request: Request,
    batch_data: dict = Body(..., description="批量更新数据"),
    current_user: User = DependAuth
):
    """
    批量更新角色 v2版本
    
    新功能：
    - 批量更新多个角色
    - 标准化响应格式
    - 批量操作结果统计
    - 字段验证
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        if "updates" not in batch_data or not batch_data["updates"]:
            return formatter.validation_error(
                message="Updates list cannot be empty",
                details=[APIv2ErrorDetail(
                    field="updates",
                    code="EMPTY_LIST",
                    message="Updates list is required and cannot be empty",
                    value=batch_data.get("updates", [])
                )]
            )
        
        updates_data = batch_data["updates"]
        success_count = 0
        failed_count = 0
        updated_roles = []
        failed_roles = []
        
        allowed_fields = {'name', 'desc', 'is_active'}
        
        async with in_transaction("default"):
            for i, update_data in enumerate(updates_data):
                try:
                    # 验证必需字段
                    if "id" not in update_data:
                        failed_count += 1
                        failed_roles.append({
                            "index": i,
                            "data": update_data,
                            "reason": "Missing required field: id"
                        })
                        continue
                    
                    role_id = update_data["id"]
                    
                    # 获取角色
                    role = await Role.filter(id=role_id).first()
                    if not role:
                        failed_count += 1
                        failed_roles.append({
                            "index": i,
                            "data": update_data,
                            "reason": f"Role with id {role_id} not found"
                        })
                        continue
                    
                    # 验证更新字段
                    update_fields = {k: v for k, v in update_data.items() if k != "id"}
                    invalid_fields = set(update_fields.keys()) - allowed_fields
                    
                    if invalid_fields:
                        failed_count += 1
                        failed_roles.append({
                            "index": i,
                            "data": update_data,
                            "reason": f"Invalid fields: {list(invalid_fields)}"
                        })
                        continue
                    
                    # 检查角色名重复
                    if 'name' in update_fields and update_fields['name'] != role.role_name:
                        existing_role = await Role.filter(name=update_fields['name']).first()
                        if existing_role and existing_role.id != role_id:
                            failed_count += 1
                            failed_roles.append({
                                "index": i,
                                "data": update_data,
                                "reason": f"Role name '{update_fields['name']}' already exists"
                            })
                            continue
                    
                    # 更新角色
                    for field, value in update_fields.items():
                        setattr(role, field, value)
                    
                    await role.save()
                    
                    # 获取更新后的角色信息
                    role_dict = await role.to_dict()
                    role_dict["stats"] = {
                        "users_count": await role.users.all().count(),
                        "apis_count": await role.apis.all().count(),
                        "menus_count": await role.menus.all().count()
                    }
                    
                    updated_roles.append(role_dict)
                    success_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    failed_roles.append({
                        "index": i,
                        "data": update_data,
                        "reason": str(e)
                    })
        
        return formatter.success(
            data={
                "action": "update",
                "total_requested": len(updates_data),
                "success_count": success_count,
                "failed_count": failed_count,
                "updated": updated_roles,
                "failed": failed_roles
            },
            message=f"Batch update completed. {success_count} succeeded, {failed_count} failed.",
            resource_type="roles"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to execute batch update: {str(e)}")


# 注意：以下 /{role_id} 路由必须放在文件末尾，以避免与其他更具体的路由（如 /batch）冲突

# GET /{role_id} 路由已移动到文件末尾以避免与 /batch 和 /tree 路由冲突


# PUT /{role_id} 路由已移动到文件末尾以避免与 /batch 和 /tree 路由冲突


# DELETE /{role_id} 路由已移动到文件末尾以避免与 /batch 和 /tree 路由冲突


# 用户管理相关路由
@router.get("/{role_id}/users", summary="获取角色用户", description="获取指定角色的用户列表", dependencies=[DependAuth])
async def get_role_users(
    role_id: int,
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    current_user: User = DependAuth
):
    """
    获取角色用户 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 分页支持
    - 用户详细信息
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查角色是否存在
        role = await role_controller.get(id=role_id)
        if not role:
            return formatter.not_found(f"Role with id {role_id} not found", "role")
        
        # 计算分页参数
        offset = (page - 1) * size
        
        # 获取用户总数
        total_count = await role.users.all().count()
        
        # 获取分页用户数据
        users = await role.users.all().offset(offset).limit(size)
        
        users_data = []
        for user in users:
            user_dict = await user.to_dict()
            # 注意：由于这是ManyToMany关系，我们无法直接获取关联时间
            # 如果需要关联时间，需要通过UserRole中间表查询
            user_dict["assigned_at"] = None  # 暂时设为None，后续可通过UserRole表查询
            users_data.append(user_dict)
        
        # 计算分页信息
        total_pages = (total_count + size - 1) // size
        
        pagination_data = {
            "users": users_data,
            "pagination": {
                "page": page,
                "size": size,
                "total": total_count,
                "pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "role_info": {
                "id": role_id,
                "name": role.role_name,
                "description": role.description
            }
        }
        
        return formatter.success(
            data=pagination_data,
            message="Role users retrieved successfully",
            resource_id=str(role_id),
            resource_type="role_users"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to retrieve role users: {str(e)}")


@router.post("/{role_id}/users", summary="添加角色用户", description="为角色添加用户", dependencies=[DependAuth])
async def add_role_users(
    role_id: int,
    request: Request,
    users_in: RoleUsersUpdate,
    current_user: User = DependAuth
):
    """
    添加角色用户 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 批量用户添加
    - 事务支持
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查角色是否存在
        role = await role_controller.get(id=role_id)
        if not role:
            return formatter.not_found(f"Role with id {role_id} not found", "role")
        
        # 检查用户是否存在
        users = await User.filter(id__in=users_in.user_ids).all()
        if len(users) != len(users_in.user_ids):
            found_ids = [user.id for user in users]
            missing_ids = [uid for uid in users_in.user_ids if uid not in found_ids]
            return formatter.validation_error(
                message="Some users not found",
                details=[APIv2ErrorDetail(
                    field="user_ids",
                    code="USERS_NOT_FOUND",
                    message=f"Users not found: {missing_ids}",
                    value=missing_ids
                )]
            )
        
        # 添加用户到角色
        async with in_transaction("default"):
            added_users = []
            for user in users:
                # 检查用户是否已经有此角色
                existing_role = await UserRole.filter(user=user.id, role=role.id).first()
                if not existing_role:
                    await UserRole.create(user=user.id, role=role.id)
                    added_users.append(await user.to_dict())
        
        return formatter.success(
            data={
                "role_id": role_id,
                "added_users": added_users,
                "total_added": len(added_users)
            },
            message=f"Successfully added {len(added_users)} users to role",
            resource_id=str(role_id),
            resource_type="role_users"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to add users to role: {str(e)}")


@router.delete("/{role_id}/users/{user_id}", summary="移除角色用户", description="从角色中移除指定用户", dependencies=[DependAuth])
async def remove_role_user(
    role_id: int,
    user_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """
    移除角色用户 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 安全检查
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查角色是否存在
        role = await role_controller.get(id=role_id)
        if not role:
            return formatter.not_found(f"Role with id {role_id} not found", "role")
        
        # 检查用户是否存在
        user = await User.get_or_none(id=user_id)
        if not user:
            return formatter.not_found(f"User with id {user_id} not found", "user")
        
        # 检查用户角色关系是否存在
        user_role = await UserRole.filter(user=user.id, role=role.id).first()
        if not user_role:
            return formatter.not_found(
                f"User {user_id} is not assigned to role {role_id}",
                "user_role"
            )
        
        # 删除用户角色关系
        await user_role.delete()
        
        return formatter.success(
            data={
                "role_id": role_id,
                "user_id": user_id,
                "removed_user": await user.to_dict()
            },
            message="User removed from role successfully",
            resource_id=f"{role_id}_{user_id}",
            resource_type="role_users"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to remove user from role: {str(e)}")


# 子角色管理相关路由
@router.get("/{role_id}/children", summary="获取子角色", description="获取指定角色的子角色列表", dependencies=[DependAuth])
async def get_role_children(
    role_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """
    获取子角色 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 递归子角色信息
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查角色是否存在
        role = await role_controller.get(id=role_id)
        if not role:
            return formatter.not_found(f"Role with id {role_id} not found", "role")
        
        # 获取直接子角色
        children = await Role.filter(parent_id=role_id).all()
        children_data = []
        
        for child in children:
            child_dict = await child.to_dict()
            # 获取子角色的用户数量
            child_dict["users_count"] = await child.users.all().count()
            # 获取子角色的子角色数量
            child_dict["children_count"] = await Role.filter(parent_id=child.id).count()
            children_data.append(child_dict)
        
        return formatter.success(
            data={
                "parent_role": {
                    "id": role_id,
                    "name": role.role_name,
                    "description": role.description
                },
                "children": children_data,
                "total_children": len(children_data)
            },
            message="Role children retrieved successfully",
            resource_id=str(role_id),
            resource_type="role_children"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to retrieve role children: {str(e)}")


@router.post("/{role_id}/children", summary="创建子角色", description="为指定角色创建子角色", dependencies=[DependAuth])
async def create_role_child(
    role_id: int,
    request: Request,
    role_in: RoleCreate,
    current_user: User = DependAuth
):
    """
    创建子角色 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 自动设置父角色关系
    - 层级验证
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查父角色是否存在
        parent_role = await role_controller.get(id=role_id)
        if not parent_role:
            return formatter.not_found(f"Parent role with id {role_id} not found", "role")
        
        # 检查角色名是否已存在
        existing_role = await Role.filter(role_name=role_in.role_name).first()
        if existing_role:
            return formatter.validation_error(
                message="Role name already exists",
                details=[APIv2ErrorDetail(
                    field="role_name",
                    code="DUPLICATE_NAME",
                    message="Role name is already taken",
                    value=role_in.role_name
                )]
            )
        
        # 设置父角色ID
        role_in.parent_id = role_id
        
        # 创建子角色
        async with in_transaction("default"):
            new_role = await role_controller.create(obj_in=role_in)
            
            # V1 API权限已完全弃用，不再支持
            # 注意：V1 Api模型已被移除，只支持V2 SysApiEndpoint
            
            if hasattr(role_in, 'menu_ids') and role_in.menu_ids:
                menus = await Menu.filter(id__in=role_in.menu_ids).all()
                for menu in menus:
                    await new_role.menus.add(menu)
        
        # 获取创建的角色信息
        role_dict = await new_role.to_dict(m2m=True)
        
        return formatter.success(
            data=role_dict,
            message="Child role created successfully",
            resource_id=str(new_role.id),
            resource_type="roles",
            code=201
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to create child role: {str(e)}")


# 注释：/tree 路由已移动到文件末尾，确保在 /{role_id} 路由之后


# 注释：GET /{role_id} 路由已移动到文件最末尾，确保在 /tree 路由之后


# 注释：PUT /{role_id} 路由已移动到文件最末尾，确保在 /tree 路由之后


# 注释：DELETE /{role_id} 路由已移动到文件最末尾，确保在 /tree 路由之后


# 注释：/tree 路由已移动到文件最末尾，确保在所有 /{role_id} 路由之后


# PUT /{role_id} 路由 - 必须放在文件最末尾，确保在 /tree 路由之后
@router.put("/{role_id}", summary="更新角色", description="更新角色信息", dependencies=[DependAuth])
async def update_role(
    role_id: int,
    request: Request,
    role_in: RoleUpdate,
    current_user: User = DependAuth
):
    """
    更新角色 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 增强的验证和错误处理
    - 事务支持
    
    注意：此路由定义在文件末尾，确保更具体的路由（如 /batch）优先匹配
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查角色是否存在
        role = await role_controller.get(id=role_id)
        if not role:
            return formatter.not_found(f"Role with id {role_id} not found", "role")
        
        # 验证角色名是否被其他角色使用
        if hasattr(role_in, 'role_name') and role_in.role_name != role.role_name:
            existing_role = await Role.filter(role_name=role_in.role_name).first()
            if existing_role and existing_role.id != role_id:
                return formatter.validation_error(
                    message="Role name is already taken by another role",
                    details=[APIv2ErrorDetail(
                        field="role_name",
                        code="DUPLICATE_NAME",
                        message="Role name is already taken",
                        value=role_in.role_name
                    )]
                )
        
        # 更新角色
        async with in_transaction("default"):
            role_in.id = role_id  # 确保ID正确
            updated_role = await role_controller.update(id=role_id, obj_in=role_in)
            
            # 更新V2系统API权限（推荐使用）
            if hasattr(role_in, 'sys_api_ids') and role_in.sys_api_ids is not None:
                await updated_role.apis.clear()
                if role_in.sys_api_ids:
                    sys_apis = await SysApiEndpoint.filter(id__in=role_in.sys_api_ids).all()
                    for sys_api in sys_apis:
                        await updated_role.apis.add(sys_api)
            
            # V1 API权限已完全弃用，不再支持
            # 注意：V1 Api模型已被移除，只支持V2 SysApiEndpoint
            
            # 更新菜单权限
            if hasattr(role_in, 'menu_ids') and role_in.menu_ids is not None:
                await updated_role.menus.clear()
                if role_in.menu_ids:
                    # 自动包含父菜单权限
                    all_menu_ids = await get_menu_ids_with_parents(role_in.menu_ids)
                    menus = await Menu.filter(id__in=all_menu_ids).all()
                    for menu in menus:
                        await updated_role.menus.add(menu)
        
        # 获取更新后的角色信息
        role_dict = await updated_role.to_dict(m2m=True)
        
        return formatter.success(
            data=role_dict,
            message="Role updated successfully",
            resource_id=str(role_id),
            resource_type="roles"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to update role: {str(e)}")


@router.delete("/{role_id}", summary="删除角色", description="删除指定角色", dependencies=[DependAuth])
async def delete_role(
    role_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """
    删除角色 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 增强的安全检查
    - 用户关联检查
    
    注意：此路由定义在文件末尾，确保更具体的路由（如 /batch）优先匹配
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查角色是否存在
        role = await role_controller.get(id=role_id)
        if not role:
            return formatter.not_found(f"Role with id {role_id} not found", "role")
        
        # 检查是否有用户关联到此角色
        user_count = await User.filter(roles=role).count()
        if user_count > 0:
            return formatter.validation_error(
                message="Cannot delete role with associated users",
                details=[APIv2ErrorDetail(
                    field="role_id",
                    code="HAS_USERS",
                    message=f"Role has {user_count} associated users",
                    value=role_id
                )]
            )
        
        # 删除角色
        await role_controller.remove(id=role_id)
        
        return formatter.success(
            data=None,
            message="Role deleted successfully",
            resource_id=str(role_id),
            resource_type="roles"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to delete role: {str(e)}")


# GET /{role_id} 路由已移动到文件最末尾，在 /tree 路由之后


# /{role_id} 相关路由 - 重新定义在文件末尾，确保在 /tree 路由之前

# 权限管理相关路由
@router.get("/{role_id}/permissions", summary="获取角色权限", description="获取指定角色的权限配置", dependencies=[DependAuth])
async def get_role_permissions(
    role_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """
    获取角色权限 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 详细权限信息
    - 权限分类展示
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查角色是否存在
        role = await role_controller.get(id=role_id)
        if not role:
            return formatter.not_found(f"Role with id {role_id} not found", "role")
        
        # 获取角色权限
        apis = await role.apis.all()
        menus = await role.menus.all()
        
        permissions_data = {
            "role_id": role_id,
            "role_name": role.role_name,
            "api_permissions": await asyncio.gather(*[api.to_dict() for api in apis]) if apis else [],
            "menu_permissions": await asyncio.gather(*[menu.to_dict() for menu in menus]) if menus else [],
            "permissions_count": {
                "apis": len(apis),
                "menus": len(menus),
                "total": len(apis) + len(menus)
            }
        }
        
        return formatter.success(
            data=permissions_data,
            message="Role permissions retrieved successfully",
            resource_id=str(role_id),
            resource_type="role_permissions"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to retrieve role permissions: {str(e)}")


@router.post("/{role_id}/permissions", summary="添加角色权限", description="为角色添加权限", dependencies=[DependAuth])
async def add_role_permissions(
    role_id: int,
    request: Request,
    permissions_in: RolePermissionsUpdate,
    current_user: User = DependAuth
):
    """
    添加角色权限 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 批量权限添加
    - 事务支持
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查角色是否存在
        role = await role_controller.get(id=role_id)
        if not role:
            return formatter.not_found(f"Role with id {role_id} not found", "role")
        
        async with in_transaction("default"):
            # 优先处理V2系统API权限（推荐使用）
            if hasattr(permissions_in, 'sys_api_ids') and permissions_in.sys_api_ids:
                # 验证API是否存在
                sys_apis = await SysApiEndpoint.filter(id__in=permissions_in.sys_api_ids).all()
                valid_api_ids = [api.id for api in sys_apis]
                
                # 直接使用ORM方法添加权限关系
                for api in sys_apis:
                    try:
                        logger.info(f"准备添加权限关系 - role_id: {role_id}, api_id: {api.id}")
                        await role.apis.add(api)
                        logger.info(f"成功添加权限关系 - role_id: {role_id}, api_id: {api.id}")
                    except Exception as e:
                        logger.error(f"添加权限关系失败 - role_id: {role_id}, api_id: {api.id}, 错误: {str(e)}")
                        raise
            # V1 API权限已弃用，不再支持
            
            # 添加菜单权限
            if hasattr(permissions_in, 'menu_ids') and permissions_in.menu_ids:
                # 自动包含父菜单权限
                all_menu_ids = await get_menu_ids_with_parents(permissions_in.menu_ids)
                menus = await Menu.filter(id__in=all_menu_ids).all()
                for menu in menus:
                    await role.menus.add(menu)
        
        # 获取更新后的权限信息
        apis = await role.apis.all()
        menus = await role.menus.all()
        
        permissions_data = {
            "role_id": role_id,
            "api_permissions": await asyncio.gather(*[api.to_dict() for api in apis]) if apis else [],
            "menu_permissions": await asyncio.gather(*[menu.to_dict() for menu in menus]) if menus else []
        }
        
        return formatter.success(
            data=permissions_data,
            message="Role permissions added successfully",
            resource_id=str(role_id),
            resource_type="role_permissions"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to add role permissions: {str(e)}")


@router.put("/{role_id}/permissions", summary="更新角色权限", description="更新角色的权限配置", dependencies=[DependAuth])
async def update_role_permissions(
    role_id: int,
    request: Request,
    permissions_in: RolePermissionsUpdate,
    current_user: User = DependAuth
):
    """
    更新角色权限 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 完整权限替换
    - 事务支持
    """
    formatter = ResponseFormatterV2(request)
    
    # 添加详细的请求日志
    logger.info(f"更新角色权限请求 - role_id: {role_id}")
    logger.info(f"请求数据: {permissions_in.dict()}")
    
    try:
        # 检查角色是否存在
        role = await role_controller.get(id=role_id)
        if not role:
            return formatter.not_found(f"Role with id {role_id} not found", "role")
        
        async with in_transaction("default"):
            # 清除现有权限
            await role.apis.clear()
            await role.menus.clear()
            
            # 优先处理V2系统API权限（推荐使用）
            if hasattr(permissions_in, 'sys_api_ids') and permissions_in.sys_api_ids:
                # 验证API是否存在
                sys_apis = await SysApiEndpoint.filter(id__in=permissions_in.sys_api_ids).all()
                valid_api_ids = [api.id for api in sys_apis]
                
                # 直接使用ORM方法添加权限关系
                for api in sys_apis:
                    try:
                        logger.info(f"准备添加权限关系 - role_id: {role_id}, api_id: {api.id}")
                        await role.apis.add(api)
                        logger.info(f"成功添加权限关系 - role_id: {role_id}, api_id: {api.id}")
                    except Exception as e:
                        logger.error(f"添加权限关系失败 - role_id: {role_id}, api_id: {api.id}, 错误: {str(e)}")
                        raise
            # V1 API权限已完全弃用，不再支持
            # 注意：V1 Api模型已被移除，只支持V2 SysApiEndpoint
            
            # 添加新的菜单权限
            if hasattr(permissions_in, 'menu_ids') and permissions_in.menu_ids:
                # 自动包含父菜单权限
                all_menu_ids = await get_menu_ids_with_parents(permissions_in.menu_ids)
                menus = await Menu.filter(id__in=all_menu_ids).all()
                for menu in menus:
                    await role.menus.add(menu)
        
        # 获取更新后的权限信息
        apis = await role.apis.all()
        menus = await role.menus.all()
        
        permissions_data = {
            "role_id": role_id,
            "api_permissions": await asyncio.gather(*[api.to_dict() for api in apis]) if apis else [],
            "menu_permissions": await asyncio.gather(*[menu.to_dict() for menu in menus]) if menus else []
        }
        
        return formatter.success(
            data=permissions_data,
            message="Role permissions updated successfully",
            resource_id=str(role_id),
            resource_type="role_permissions"
        )
        
    except Exception as e:
        logger.error(f"更新角色权限失败 - role_id: {role_id}, 错误: {str(e)}")
        logger.error(f"错误类型: {type(e).__name__}")
        if hasattr(e, 'errors'):
            logger.error(f"验证错误详情: {e.errors()}")
        return formatter.internal_error(f"Failed to update role permissions: {str(e)}")


@router.delete("/{role_id}/permissions", summary="删除角色权限", description="删除角色的指定权限", dependencies=[DependAuth])
async def delete_role_permissions(
    role_id: int,
    request: Request,
    permissions_in: RolePermissionsUpdate = None,
    api_ids: str = Query(None, description="要删除的API权限ID列表，逗号分隔"),
    menu_ids: str = Query(None, description="要删除的菜单权限ID列表，逗号分隔"),
    current_user: User = DependAuth
):
    """
    删除角色权限 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 批量权限删除
    - 事务支持
    - 支持查询参数和请求体两种方式
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查角色是否存在
        role = await role_controller.get(id=role_id)
        if not role:
            return formatter.not_found(f"Role with id {role_id} not found", "role")
        
        # 处理权限ID - 优先使用请求体，其次使用查询参数
        api_id_list = []
        menu_id_list = []
        
        if permissions_in and (permissions_in.sys_api_ids or permissions_in.api_ids or permissions_in.menu_ids):
            # 使用请求体中的数据 - 优先处理sys_api_ids（V2 SysApiEndpoint）
            if permissions_in.sys_api_ids:
                # 处理V2系统API权限
                sys_apis = await SysApiEndpoint.filter(id__in=permissions_in.sys_api_ids).all()
                for sys_api in sys_apis:
                    await role.apis.remove(sys_api)
            elif permissions_in.api_ids:
                # 兼容性支持：处理V1 API权限（已弃用）
                api_id_list = permissions_in.api_ids or []
            menu_id_list = permissions_in.menu_ids or []
        else:
            # 使用查询参数
            if api_ids:
                try:
                    api_id_list = [int(id.strip()) for id in api_ids.split(',') if id.strip()]
                except ValueError:
                    return formatter.bad_request("Invalid api_ids format. Should be comma-separated integers.")
            
            if menu_ids:
                try:
                    menu_id_list = [int(id.strip()) for id in menu_ids.split(',') if id.strip()]
                except ValueError:
                    return formatter.bad_request("Invalid menu_ids format. Should be comma-separated integers.")
        
        # 检查是否有权限ID需要删除
        if not api_id_list and not menu_id_list:
            return formatter.bad_request("No permission IDs provided for deletion")
        
        async with in_transaction("default"):
            # V1 API权限删除已弃用，不再支持
            if api_id_list:
                logger.warning(f"尝试删除V1 API权限，已弃用: {api_id_list}")
            
            # 删除菜单权限
            if menu_id_list:
                menus = await Menu.filter(id__in=menu_id_list).all()
                for menu in menus:
                    await role.menus.remove(menu)
        
        # 获取删除的权限信息用于响应
        deleted_menus = await Menu.filter(id__in=menu_id_list).all() if menu_id_list else []
        
        permissions_data = {
            "apis": await asyncio.gather(*[api.to_dict() for api in deleted_apis]) if deleted_apis else [],
            "menus": await asyncio.gather(*[menu.to_dict() for menu in deleted_menus]) if deleted_menus else []
        }
        
        return formatter.success(
            data=permissions_data,
            message="Permissions removed from role successfully",
            resource_id=str(role_id),
            resource_type="role_permissions"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to delete role permissions: {str(e)}")


@router.patch("/{role_id}", summary="部分更新角色", description="部分更新角色信息", dependencies=[DependAuth])
async def patch_role(
    role_id: int,
    request: Request,
    role_in: RolePatch,
    current_user: User = DependAuth
):
    """
    部分更新角色 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 部分字段更新
    - 数据验证
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查角色是否存在
        role = await role_controller.get(id=role_id)
        if not role:
            return formatter.not_found(f"Role with id {role_id} not found", "role")
        
        # 更新角色信息
        update_data = role_in.dict(exclude_unset=True)
        if update_data:
            updated_role = await role_controller.update(id=role_id, obj_in=update_data)
            role_data = await updated_role.to_dict(m2m=True)
        else:
            role_data = await role.to_dict(m2m=True)
        
        return formatter.success(
            data=role_data,
            message="Role updated successfully",
            resource_id=str(role_id),
            resource_type="role"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to update role: {str(e)}")


# 角色树形结构路由 - 必须放在文件最末尾，确保在所有 /{role_id} 路由之后
@router.get("/tree", summary="获取角色树形结构", description="获取完整的角色层级树形结构", dependencies=[DependAuth])
async def get_roles_tree(
    request: Request,
    include_inactive: bool = Query(False, description="是否包含非激活角色"),
    current_user: User = DependAuth
):
    """
    获取角色树形结构
    
    功能：
    - 返回完整的角色层级树
    - 支持过滤非激活角色
    - 优化查询性能
    
    注意：此路由定义在文件最末尾，确保在所有 /{role_id} 路由之后
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 构建查询条件
        query_filter = Q()
        if not include_inactive:
            query_filter &= Q(status="0")  # 使用status字段而不是is_active
        
        # 获取所有角色
        roles = await Role.filter(query_filter).prefetch_related("apis", "menus").all()
        
        # 构建角色映射
        role_map = {}
        for role in roles:
            role_dict = await role.to_dict(m2m=True)
            role_dict["children"] = []
            role_dict["stats"] = {
                "users_count": await role.users.all().count(),
                "apis_count": len(role_dict.get("apis", [])),
                "menus_count": len(role_dict.get("menus", [])),
                "children_count": 0  # 将在后面计算
            }
            role_map[role.id] = role_dict
        
        # 构建树形结构
        root_roles = []
        for role_dict in role_map.values():
            parent_id = role_dict.get("parent_id")
            if parent_id and parent_id in role_map:
                # 添加到父角色的children中
                role_map[parent_id]["children"].append(role_dict)
                role_map[parent_id]["stats"]["children_count"] += 1
            else:
                # 根角色
                root_roles.append(role_dict)
        
        # 递归计算子角色统计
        def calculate_tree_stats(role_dict):
            total_children = len(role_dict["children"])
            total_users = role_dict["stats"]["users_count"]
            
            for child in role_dict["children"]:
                child_stats = calculate_tree_stats(child)
                total_children += child_stats["total_children"]
                total_users += child_stats["total_users"]
            
            role_dict["stats"]["total_children_count"] = total_children
            role_dict["stats"]["total_users_count"] = total_users
            
            return {
                "total_children": total_children,
                "total_users": total_users
            }
        
        # 计算每个根角色的统计信息
        for root_role in root_roles:
            calculate_tree_stats(root_role)
        
        # 计算最大深度的辅助函数
        def calculate_max_depth(roles_list, current_depth=1):
            if not roles_list:
                return current_depth - 1
            
            max_depth = current_depth
            for role in roles_list:
                if role.get("children"):
                    child_depth = calculate_max_depth(role["children"], current_depth + 1)
                    max_depth = max(max_depth, child_depth)
            
            return max_depth
        
        # 构建响应数据
        tree_data = {
            "tree": root_roles,
            "summary": {
                "total_roles": len(roles),
                "root_roles_count": len(root_roles),
                "max_depth": calculate_max_depth(root_roles),
                "include_inactive": include_inactive
            }
        }
        
        return formatter.success(
            data=tree_data,
            message="Role tree retrieved successfully",
            resource_type="role_tree"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to retrieve role tree: {str(e)}")


# GET /{role_id} 路由 - 放在文件最末尾，确保在 /tree 路由之后
@router.get("/{role_id}", summary="获取角色详情", description="获取指定角色的详细信息", dependencies=[DependAuth])
async def get_role(
    role_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """
    获取角色详情 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 增强的角色统计信息
    - 关联用户列表
    - 相关资源链接
    
    注意：此路由定义在文件最末尾，确保 /tree 等具体路由优先匹配
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 获取角色信息
        role = await role_controller.get(id=role_id)
        if not role:
            return formatter.not_found(f"Role with id {role_id} not found", "role")
        
        # 转换为字典格式
        role_dict = await role.to_dict(m2m=True)
        
        # 添加统计信息
        role_dict["stats"] = {
            "users_count": await role.users.all().count(),
            "apis_count": await role.apis.all().count(),
            "menus_count": await role.menus.all().count()
        }
        
        # 获取关联用户列表（限制数量以避免性能问题）
        users = await role.users.all().limit(10)
        role_dict["users"] = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active
            }
            for user in users
        ]
        
        # 构建相关资源链接
        related_resources = {
            "permissions": f"/api/v2/roles/{role_id}/permissions",
            "users": f"/api/v2/roles/{role_id}/users",
            "update": f"/api/v2/roles/{role_id}",
            "delete": f"/api/v2/roles/{role_id}"
        }
        
        return formatter.success(
            data=role_dict,
            message="Role retrieved successfully",
            resource_id=str(role_id),
            resource_type="roles",
            related_resources=related_resources
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to retrieve role: {str(e)}")