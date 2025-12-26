"""
用户管理 API v2
演示标准化响应格式和版本控制
"""
from fastapi import APIRouter, Request, Depends, Body
from app.schemas.base import APIResponse, success_response, paginated_response, error_response, BatchDeleteRequest
from app.core.response_formatter_v2 import ResponseFormatterV2, create_formatter, APIv2ErrorDetail
from tortoise.transactions import in_transaction
from app.core.versioning import version_required
from app.core.dependency import DependAuth
from app.core.batch_delete_decorators import require_batch_delete_permission
from app.models import User
from app.controllers.user import user_controller
from typing import Optional, List, Dict, Any
import logging
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# 请求体模型定义
class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
    nick_name: Optional[str] = None
    alias: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    role_ids: Optional[List[int]] = []
    dept_id: Optional[int] = None

class SetUserRolesRequest(BaseModel):
    role_ids: List[int]

class ResetPasswordRequest(BaseModel):
    new_password: Optional[str] = "123456"

class BatchUserRequest(BaseModel):
    action: str  # "activate", "deactivate", "delete"
    user_ids: List[int]

class UserPatchRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    role_ids: Optional[List[int]] = None
    dept_id: Optional[int] = None

class UserStatusRequest(BaseModel):
    is_active: bool

class BatchCreateUserRequest(BaseModel):
    users: List[CreateUserRequest]

class BatchUpdateUserRequest(BaseModel):
    updates: List[dict]  # 格式: [{"user_id": 1, "data": {...}}]

class UserSearchRequest(BaseModel):
    """用户复杂查询请求模型"""
    username: Optional[str] = None
    email: Optional[str] = None
    dept_id: Optional[int] = None
    role_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    created_after: Optional[str] = None  # ISO格式日期
    created_before: Optional[str] = None  # ISO格式日期
    page: int = 1
    page_size: int = 20
    sort_by: Optional[str] = "created_at"  # 排序字段
    sort_order: Optional[str] = "desc"  # asc 或 desc

@router.get("/", summary="获取用户列表 v2", description="获取用户列表 - v2版本使用标准化响应", dependencies=[DependAuth])
async def get_users_v2(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    username: Optional[str] = None,
    email: Optional[str] = None,
    dept_id: Optional[int] = None,
    current_user: User = DependAuth
):
    # 添加调试日志
    logger = logging.getLogger(__name__)
    logger.info(f"获取用户列表 - 参数: page={page}, page_size={page_size}, username={username}, email={email}, dept_id={dept_id}")
    """
    获取用户列表 v2版本
    
    新功能：
    - 标准化响应格式
    - 改进的分页信息
    - 版本控制支持
    """
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 构建查询条件
    query = User.all()
    
    # 添加筛选条件
    if username:
        query = query.filter(username__icontains=username)
    if email:
        query = query.filter(email__icontains=email)
    if dept_id:
        query = query.filter(dept_id=dept_id)
    
    # 获取总数
    total = await query.count()
    
    # 获取用户列表（不使用prefetch_related避免字段名称问题）
    users = await query.offset(offset).limit(page_size)
    
    # 转换为字典格式
    user_data = []
    for user in users:
        # 获取用户角色信息
        roles = []
        try:
            user_roles = await user.roles.all()
            roles = [{'id': role.id, 'name': role.role_name} for role in user_roles]
        except Exception as e:
            logger.warning(f"获取用户 {user.id} 角色信息失败: {e}")
            roles = []
        
        # 获取用户部门信息
        dept = None
        try:
            if user.dept_id:
                dept_obj = await user.dept
                if dept_obj:
                    dept = {'id': dept_obj.id, 'name': dept_obj.dept_name}
        except Exception as e:
            logger.warning(f"获取用户 {user.id} 部门信息失败: {e}")
            dept = None
        
        user_data.append({
            "id": user.id,
            "username": user.username,
            "alias": getattr(user, 'alias', None),
            "email": user.email,
            "phone": getattr(user, 'phone', None),
            "isActive": user.is_active,
            "isSuperuser": user.is_superuser,
            "dept_id": user.dept_id,
            "last_login": user.last_login.isoformat() if getattr(user, 'last_login', None) else None,
            "roles": roles,
            "dept": dept,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        })
    
    # 使用ResponseFormatterV2创建符合项目规范的响应
    formatter = create_formatter(request)
    return formatter.paginated_success(
        data=user_data,
        total=total,
        page=page,
        page_size=page_size,
        message="Users retrieved successfully",
        resource_type="users",
        query_params={
            "username": username,
            "email": email,
            "dept_id": dept_id
        }
    )

@router.get("/export", summary="导出用户数据 v2")
async def export_users_v2(
    request: Request,
    format: str = "csv",
    username: Optional[str] = None,
    email: Optional[str] = None,
    dept_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    current_user: User = DependAuth
):
    """
    导出用户数据 v2版本
    
    新功能：
    - 支持多种导出格式（csv, json）
    - 筛选条件支持
    - 标准化响应格式
    """
    try:
        # 构建查询条件
        query = User.all().prefetch_related('roles', 'dept')
        
        # 添加筛选条件
        if username:
            query = query.filter(username__icontains=username)
        if email:
            query = query.filter(email__icontains=email)
        if dept_id:
            query = query.filter(dept_id=dept_id)
        if is_active is not None:
            query = query.filter(is_active=is_active)
        
        # 获取所有用户
        users = await query
        
        # 转换为导出格式
        export_data = []
        for user in users:
            # 获取用户角色信息
            roles = []
            if hasattr(user, 'roles'):
                user_roles = await user.roles.all()
                roles = [role.role_name for role in user_roles]
            
            # 获取用户部门信息
            dept_name = None
            if hasattr(user, 'dept') and user.dept:
                dept_name = user.dept.name
            
            export_data.append({
                "id": user.id,
                "username": user.username,
                "alias": getattr(user, 'alias', None),
                "email": user.email,
                "phone": getattr(user, 'phone', None),
                "isActive": user.is_active,
                "isSuperuser": user.is_superuser,
                "dept_name": dept_name,
                "roles": ", ".join(roles),
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            })
        
        if format.lower() == "csv":
            # 生成CSV格式
            import csv
            import io
            
            output = io.StringIO()
            if export_data:
                writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
                writer.writeheader()
                writer.writerows(export_data)
            
            from fastapi.responses import Response
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=users_export.csv"}
            )
        else:
            # 返回JSON格式
            formatter = create_formatter(request)
            return formatter.success(
                data={
                    "users": export_data,
                    "total_count": len(export_data),
                    "export_format": format,
                    "exported_at": datetime.now().isoformat()
                },
                message=f"Users exported successfully in {format} format",
                resource_type="users",
                resource_id=None
            )
        
    except Exception as e:
        formatter = create_formatter(request)
        return formatter.internal_error(
            message=f"Failed to export users: {str(e)}"
        )

@router.delete("/batch", summary="批量删除用户 v2")
@require_batch_delete_permission("user")
async def batch_delete_users_v2(
    request: Request,
    batch_request: BatchDeleteRequest,
    current_user: User = DependAuth
):
    """
    批量删除用户 v2版本
    
    使用标准化数据格式：{"ids": [1, 2, 3]}
    返回标准化响应格式，包含用户友好的错误提示
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        from app.services.batch_delete_service import user_batch_delete_service
        from tortoise.transactions import in_transaction
        
        user_ids = batch_request.ids
        
        if not user_ids:
            return formatter.validation_error(
                message="用户ID列表不能为空",
                details=[APIv2ErrorDetail(
                    field="ids",
                    code="EMPTY_LIST",
                    message="用户ID列表不能为空",
                    value=user_ids
                )]
            )
        
        async with in_transaction("default"):
            # 使用标准化批量删除服务
            result = await user_batch_delete_service.batch_delete(
                ids=user_ids,
                current_user=current_user
            )
            
            # 生成用户友好的响应消息 - 增强版本，支持错误分类
            if result.failed_count == 0:
                message = f"✅ 成功删除 {result.deleted_count} 个用户"
            elif result.deleted_count == 0:
                # 按错误类型分组显示
                error_categories = {}
                for item in result.failed:
                    reason = item.reason
                    if reason not in error_categories:
                        error_categories[reason] = []
                    error_categories[reason].append(item.name or f"ID:{item.id}")
                
                error_summaries = []
                for reason, items in error_categories.items():
                    if len(items) == 1:
                        error_summaries.append(f"{items[0]}：{reason}")
                    else:
                        error_summaries.append(f"{len(items)}个用户：{reason}")
                
                message = f"❌ 删除失败：{'; '.join(error_summaries)}"
            else:
                # 部分成功的情况 - 提供详细的分类信息
                error_categories = {}
                for item in result.failed:
                    reason = item.reason
                    if reason not in error_categories:
                        error_categories[reason] = []
                    error_categories[reason].append(item.name or f"ID:{item.id}")
                
                error_summaries = []
                for reason, items in error_categories.items():
                    if '当前登录用户' in reason:
                        error_summaries.append(f"⚠️ 当前用户保护：{len(items)}个")
                    elif 'admin管理员' in reason:
                        error_summaries.append(f"🚫 admin用户保护：{len(items)}个")
                    elif '超级管理员' in reason:
                        error_summaries.append(f"🔒 超级管理员保护：{len(items)}个")
                    else:
                        error_summaries.append(f"❌ 其他原因：{len(items)}个")
                
                message = f"⚡ 批量删除完成：成功删除 {result.deleted_count} 个，失败 {result.failed_count} 个用户\n失败详情：{'; '.join(error_summaries)}"
            
            return formatter.success(
                data=result.model_dump(),
                message=message,
                resource_type="users"
            )
            
    except Exception as e:
        return formatter.internal_error(f"批量删除用户失败: {str(e)}")

@router.get("/{user_id}", summary="获取用户详情 v2")
async def get_user_v2(
    user_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """
    获取用户详情 v2版本
    
    新功能：
    - 标准化响应格式
    - 增强的用户信息
    """
    user = await User.get_or_none(id=user_id)
    
    formatter = create_formatter(request)
    
    if not user:
        return formatter.not_found(
            message=f"User with id {user_id} not found",
            resource_type="user"
        )
    
    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "isActive": user.is_active,
        "isSuperuser": user.is_superuser,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        # v2版本新增字段
        "profile": {
            "last_login": None,  # 可以从其他地方获取
            "permissions_count": len(await user.roles.all()) if hasattr(user, 'roles') else 0
        }
    }
    
    return formatter.success(
        data=user_data,
        message="User details retrieved successfully",
        resource_id=str(user_id),
        resource_type="user",
        related_resources={
            "roles": f"/api/v2/users/{user_id}/roles",
            "permissions": f"/api/v2/users/{user_id}/permissions"
        }
    )

@router.put("/{user_id}", summary="更新用户 v2")
async def update_user_v2(
    user_id: int,
    request: Request,
    username: Optional[str] = Body(None, description="用户名"),
    email: Optional[str] = Body(None, description="邮箱"),
    is_active: Optional[bool] = Body(None, description="是否激活"),
    is_superuser: Optional[bool] = Body(None, description="是否超级用户"),
    role_ids: Optional[List[int]] = Body(None, description="角色ID列表"),
    dept_id: Optional[int] = Body(None, description="部门ID"),
    current_user: User = DependAuth
):
    """
    更新用户 v2版本
    
    新功能：
    - 标准化响应格式
    - 支持部分字段更新
    - 角色关联更新
    """
    try:
        formatter = create_formatter(request)
        user = await User.get_or_none(id=user_id)
        
        if not user:
            return formatter.not_found(
                message=f"User with id {user_id} not found",
                resource_type="user",
                resource_id=str(user_id)
            )
        
        # 添加调试日志
        logger = logging.getLogger(__name__)
        logger.info(f"🔄 更新用户 {user_id} ({user.username}) - 原始状态: is_active={user.is_active}")
        logger.info(f"📝 接收到的参数: username={username}, email={email}, is_active={is_active}, is_superuser={is_superuser}, role_ids={role_ids}, dept_id={dept_id}")
        
        # 构建更新数据
        update_data = {}
        if username is not None:
            update_data['username'] = username
        if email is not None:
            update_data['email'] = email
        if is_active is not None:
            # 直接设置 status 字段而不是使用 is_active 属性
            update_data['status'] = "0" if is_active else "1"
            logger.info(f"🔄 将更新 is_active 从 {user.is_active} 到 {is_active} (status: {user.status} -> {'0' if is_active else '1'})")
        if is_superuser is not None:
            # 直接设置 user_type 字段而不是使用 is_superuser 属性
            update_data['user_type'] = "01" if is_superuser else "00"
            logger.info(f"🔄 将更新 is_superuser 从 {user.is_superuser} 到 {is_superuser} (user_type: {user.user_type} -> {'01' if is_superuser else '00'})")
        
        logger.info(f"📊 更新数据: {update_data}")
        
        # 更新用户基本信息
        if update_data:
            from tortoise.transactions import in_transaction
            async with in_transaction("default"):
                await user.update_from_dict(update_data)
                await user.save()
                logger.info(f"✅ 用户基本信息已保存")
        
        # 更新部门关联
        if dept_id is not None:
            if dept_id:
                # 验证部门是否存在
                from app.models.admin import Dept
                dept = await Dept.get_or_none(id=dept_id)
                if dept:
                    user.dept = dept
                    await user.save()
                else:
                    return formatter.not_found(
                        message=f"Department with id {dept_id} not found",
                        resource_type="department",
                        resource_id=str(dept_id)
                    )
            else:
                user.dept = None
                await user.save()
        
        # 更新角色关联
        if role_ids is not None:
            try:
                await user_controller.update_roles(user, role_ids)
                logger.info(f"✅ 角色更新成功")
            except Exception as role_error:
                logger.error(f"❌ 角色更新失败: {role_error}")
                # 角色更新失败不应该影响基本信息更新，继续执行
        
        # 重新获取更新后的完整用户信息
        updated_user = await User.filter(id=user_id).prefetch_related('dept').first()
        
        logger.info(f"🔍 更新后验证: 用户 {updated_user.username} 的 is_active = {updated_user.is_active}")
        
        # 返回更新后的用户数据
        user_data = {
            "id": updated_user.id,
            "username": updated_user.username,
            "email": updated_user.email,
            "isActive": updated_user.is_active,
            "isSuperuser": updated_user.is_superuser,
            "dept_id": updated_user.dept.id if updated_user.dept else None,
            "dept": {
                "id": updated_user.dept.id,
                "name": updated_user.dept.name
            } if updated_user.dept else None,
            "created_at": updated_user.created_at.isoformat() if updated_user.created_at else None,
            "updated_at": updated_user.updated_at.isoformat() if updated_user.updated_at else None
        }
        
        logger.info(f"📤 返回的用户数据: isActive = {user_data['isActive']}")
        
        return formatter.success(
            data=user_data,
            message="User updated successfully",
            resource_id=str(user_id),
            resource_type="user",
            related_resources={
                "department": f"/api/v2/departments/{updated_user.dept.id}" if updated_user.dept else None,
                "roles": f"/api/v2/users/{user_id}/roles"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 更新用户失败: {str(e)}")
        import traceback
        logger.error(f"❌ 错误堆栈: {traceback.format_exc()}")
        formatter = create_formatter(request)
        return formatter.internal_error(
            message=f"Failed to update user: {str(e)}"
        )

@router.post("/", summary="创建用户 v2")
async def create_user_v2(
    request: Request,
    user_data: CreateUserRequest,
    current_user: User = DependAuth
):
    """
    创建用户 v2版本
    
    新功能：
    - 标准化响应格式
    - 支持角色关联
    - 部门关联
    """
    try:
        formatter = create_formatter(request)
        
        # 检查用户名是否已存在
        existing_user = await User.get_or_none(username=user_data.username)
        if existing_user:
            return formatter.error(
                message=f"Username '{user_data.username}' already exists",
                code=400,
                error_type="ValidationError"
            )
        
        # 检查邮箱是否已存在
        existing_email = await User.get_or_none(email=user_data.email)
        if existing_email:
            return formatter.error(
                message=f"Email '{user_data.email}' already exists",
                code=400,
                error_type="ValidationError"
            )
        
        # 验证部门是否存在
        if user_data.dept_id:
            from app.models.admin import Dept
            dept = await Dept.get_or_none(id=user_data.dept_id)
            if not dept:
                return formatter.not_found(
                    message=f"Department with id {user_data.dept_id} not found",
                    resource_type="department",
                    resource_id=str(user_data.dept_id)
                )
        
        # 创建用户数据（不包含dept_id，避免冲突）
        from app.schemas.users import UserCreate
        user_create_data = UserCreate(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            nick_name=user_data.nick_name,
            is_active=user_data.is_active,
            is_superuser=user_data.is_superuser,
            role_ids=user_data.role_ids,
            dept_id=0  # 先设置为0，避免外键约束问题
        )
        
        # 使用控制器创建用户
        new_user = await user_controller.create_user(user_create_data)
        
        # 设置部门关联
        if user_data.dept_id:
            from app.models.admin import Dept
            dept = await Dept.get_or_none(id=user_data.dept_id)
            if dept:
                new_user.dept = dept
                await new_user.save()
            else:
                return formatter.not_found(
                    message=f"Department with id {user_data.dept_id} not found",
                    resource_type="department",
                    resource_id=str(user_data.dept_id)
                )
        
        # 设置其他字段
        if user_data.alias:
            new_user.alias = user_data.alias
        if user_data.phone:
            new_user.phone = user_data.phone
        await new_user.save()
        
        # 设置角色关联
        if user_data.role_ids:
            await user_controller.update_roles(new_user, user_data.role_ids)
        
        # 返回创建的用户数据
        # 重新获取用户以确保dept关系正确加载
        new_user = await User.filter(id=new_user.id).select_related('dept').first()
        
        user_response_data = {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "alias": new_user.alias,
            "phone": new_user.phone,
            "is_active": new_user.is_active,
            "is_superuser": new_user.is_superuser,
            "dept_id": new_user.dept.id if new_user.dept else None,
            "created_at": new_user.created_at.isoformat() if new_user.created_at else None,
            "updated_at": new_user.updated_at.isoformat() if new_user.updated_at else None
        }
        
        return formatter.success(
            data=user_response_data,
            message="User created successfully",
            code=201,
            resource_id=str(new_user.id),
            resource_type="users",
            related_resources={
                "department": f"/api/v2/departments/{new_user.dept.id}" if new_user.dept else None,
                "roles": f"/api/v2/users/{new_user.id}/roles"
            }
        )
        
    except Exception as e:
        formatter = create_formatter(request)
        return formatter.internal_error(
            message=f"Failed to create user: {str(e)}"
        )

@router.delete("/{user_id}", summary="删除用户 v2")
async def delete_user_v2(
    user_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """
    删除用户 v2版本
    
    新功能：
    - 标准化响应格式
    - 完整的admin用户保护机制
    - 与批量删除一致的保护逻辑
    
    Requirements: 需求5.1, 需求5.2, 需求4.1, 需求4.2, 需求4.3
    """
    try:
        formatter = create_formatter(request)
        user = await User.get_or_none(id=user_id)
        
        if not user:
            return formatter.not_found(
                message=f"User with id {user_id} not found",
                resource_type="user",
                resource_id=str(user_id)
            )
        
        # 使用与批量删除相同的业务规则检查
        from app.services.batch_delete_service import BatchDeleteBusinessRules
        
        error_message = await BatchDeleteBusinessRules.check_user_deletion_rules(user, current_user)
        if error_message:
            return formatter.forbidden(
                message=error_message,
                resource_type="user",
                resource_id=str(user_id)
            )
        
        # 清除用户的角色关联
        await user.roles.clear()
        
        # 删除用户
        await user.delete()
        
        return formatter.success(
            data={"deleted_user_id": user_id},
            message="用户删除成功",
            resource_type="user",
            resource_id=str(user_id)
        )
        
    except Exception as e:
        formatter = create_formatter(request)
        return formatter.internal_error(
            message=f"删除用户失败: {str(e)}"
        )

@router.get("/{user_id}/roles", summary="获取用户角色 v2")
async def get_user_roles_v2(
    user_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """
    获取用户角色 v2版本
    
    新功能：
    - 标准化响应格式
    - 详细的角色信息
    """
    try:
        formatter = create_formatter(request)
        user = await User.filter(id=user_id).prefetch_related('roles').first()
        
        if not user:
            return formatter.not_found(
                message=f"User with id {user_id} not found",
                resource_type="user",
                resource_id=str(user_id)
            )
        
        # 获取用户角色信息
        roles_data = []
        user_roles = await user.roles.all()
        for role in user_roles:
            roles_data.append({
                "id": role.id,
                "name": role.role_name,
                "desc": role.desc,
                "created_at": role.created_at.isoformat() if role.created_at else None
            })
        
        return formatter.success(
            data={
                "user_id": user_id,
                "username": user.username,
                "roles": roles_data,
                "roles_count": len(roles_data)
            },
            message="User roles retrieved successfully",
            resource_id=str(user_id),
            resource_type="user",
            related_resources={
                "user_details": f"/api/v2/users/{user_id}",
                "user_permissions": f"/api/v2/users/{user_id}/permissions"
            }
        )
        
    except Exception as e:
        formatter = create_formatter(request)
        return formatter.internal_error(
            message=f"Failed to get user roles: {str(e)}"
        )

@router.get("/{user_id}/permissions", summary="获取用户权限 v2")
async def get_user_permissions_v2(
    user_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """
    获取用户权限 v2版本
    
    新功能：
    - 通过角色计算用户权限
    - 包含API权限和菜单权限
    - 标准化响应格式
    """
    try:
        formatter = create_formatter(request)
        user = await User.filter(id=user_id).prefetch_related('roles').first()
        
        if not user:
            return formatter.not_found(
                message=f"User with id {user_id} not found",
                resource_type="user",
                resource_id=str(user_id)
            )
        
        # 获取用户所有角色
        user_roles = await user.roles.all().prefetch_related('apis', 'menus')
        
        # 收集所有API权限
        api_permissions = set()
        menu_permissions = set()
        role_info = []
        
        for role in user_roles:
            role_info.append({
                "id": role.id,
                "name": role.role_name,
                "desc": role.desc
            })
            
            # 获取角色的API权限
            role_apis = await role.apis.all()
            for api in role_apis:
                api_permissions.add((api.id, api.api_path, api.http_method, api.description or api.api_name))
            
            # 获取角色的菜单权限
            role_menus = await role.menus.all()
            for menu in role_menus:
                menu_permissions.add((menu.id, menu.name, menu.path, menu.component))
        
        # 格式化API权限
        api_permissions_list = []
        for api_id, api_path, http_method, description in api_permissions:
            api_permissions_list.append({
                "id": api_id,
                "path": api_path,
                "method": http_method,
                "summary": description
            })
        
        # 格式化菜单权限
        menu_permissions_list = []
        for menu_id, name, path, component in menu_permissions:
            menu_permissions_list.append({
                "id": menu_id,
                "name": name,
                "path": path,
                "component": component
            })
        
        return formatter.success(
            data={
                "user_id": user_id,
                "username": user.username,
                "roles": role_info,
                "permissions": {
                    "apis": {
                        "count": len(api_permissions_list),
                        "items": api_permissions_list
                    },
                    "menus": {
                        "count": len(menu_permissions_list),
                        "items": menu_permissions_list
                    }
                },
                "total_permissions": len(api_permissions_list) + len(menu_permissions_list)
            },
            message="User permissions retrieved successfully",
            resource_id=str(user_id),
            resource_type="user",
            related_resources={
                "user_details": f"/api/v2/users/{user_id}",
                "user_roles": f"/api/v2/users/{user_id}/roles"
            }
        )
        
    except Exception as e:
        formatter = create_formatter(request)
        return formatter.internal_error(
            message=f"Failed to get user permissions: {str(e)}"
        )

@router.put("/{user_id}/roles", summary="设置用户角色 v2")
async def set_user_roles_v2(
    user_id: int,
    request: Request,
    roles_data: SetUserRolesRequest,
    current_user: User = DependAuth
):
    """
    设置用户角色 v2版本
    
    新功能：
    - 标准化响应格式
    - 角色验证
    - 批量角色设置
    """
    try:
        formatter = create_formatter(request)
        user = await User.get_or_none(id=user_id)
        
        if not user:
            return formatter.not_found(
                message=f"User with id {user_id} not found",
                resource_type="user",
                resource_id=str(user_id)
            )
        
        # 验证角色是否存在
        if roles_data.role_ids:
            from app.models.admin import Role
            existing_roles = await Role.filter(id__in=roles_data.role_ids).all()
            existing_role_ids = [role.id for role in existing_roles]
            
            invalid_role_ids = set(roles_data.role_ids) - set(existing_role_ids)
            if invalid_role_ids:
                return formatter.not_found(
                    message=f"Roles with ids {list(invalid_role_ids)} not found",
                    resource_type="role",
                    resource_id=str(list(invalid_role_ids))
                )
        
        # 使用控制器更新角色
        await user_controller.update_roles(user, roles_data.role_ids)
        
        # 获取更新后的角色信息
        updated_roles = await user.roles.all()
        roles_response = []
        for role in updated_roles:
            roles_response.append({
                "id": role.id,
                "name": role.role_name,
                "desc": role.desc
            })
        
        return formatter.success(
            data={
                "user_id": user_id,
                "username": user.username,
                "roles": roles_response,
                "roles_count": len(roles_response)
            },
            message="User roles updated successfully",
            resource_id=str(user_id),
            resource_type="user",
            related_resources={
                "user_details": f"/api/v2/users/{user_id}",
                "user_permissions": f"/api/v2/users/{user_id}/permissions"
            }
        )
        
    except Exception as e:
        formatter = create_formatter(request)
        return formatter.internal_error(
            message=f"Failed to update user roles: {str(e)}"
        )

# 重复的批量更新路由定义已删除

@router.patch("/_batch-update", summary="批量更新用户 v2")
async def batch_update_users_v2(
    request: Request,
    batch_data: BatchUpdateUserRequest,
    current_user: User = DependAuth
):
    """
    批量更新用户 v2版本
    
    新功能：
    - 批量更新多个用户
    - 支持不同用户的不同更新字段
    - 详细的成功/失败统计
    - 标准化响应格式
    """
    try:
        if not batch_data.updates:
            formatter = create_formatter(request)
            return formatter.bad_request(
                message="Updates list cannot be empty",
                resource_type="users",
                resource_id=None
            )
        
        success_count = 0
        failed_count = 0
        updated_users = []
        failed_updates = []
        
        for update_item in batch_data.updates:
            try:
                # 支持两种数据格式：
                # 1. {"user_id": 1, "data": {...}} - 标准格式
                # 2. {"id": 1, "phone": ..., "real_name": ...} - 简化格式
                user_id = update_item.get('user_id') or update_item.get('id')
                
                if 'data' in update_item:
                    # 标准格式
                    update_data = update_item.get('data', {})
                else:
                    # 简化格式，除了id/user_id之外的所有字段都是更新数据
                    update_data = {k: v for k, v in update_item.items() if k not in ['id', 'user_id']}
                
                if not user_id:
                    failed_count += 1
                    failed_updates.append({
                        "user_id": user_id,
                        "reason": "Missing user_id or id"
                    })
                    continue
                
                if not update_data:
                    failed_count += 1
                    failed_updates.append({
                        "user_id": user_id,
                        "reason": "Missing update data"
                    })
                    continue
                
                # 获取用户
                user = await User.get_or_none(id=user_id)
                if not user:
                    failed_count += 1
                    failed_updates.append({
                        "user_id": user_id,
                        "reason": "User not found"
                    })
                    continue
                
                # 安全检查：不能修改超级管理员（除非是自己）
                if user.is_superuser and user.id != current_user.id:
                    failed_count += 1
                    failed_updates.append({
                        "user_id": user_id,
                        "username": user.username,
                        "reason": "Cannot modify superuser"
                    })
                    continue
                
                # 检查用户名和邮箱唯一性
                if 'username' in update_data and update_data['username'] != user.username:
                    existing_user = await User.get_or_none(username=update_data['username'])
                    if existing_user:
                        failed_count += 1
                        failed_updates.append({
                            "user_id": user_id,
                            "username": user.username,
                            "reason": "Username already exists"
                        })
                        continue
                
                if 'email' in update_data and update_data['email'] != user.email:
                    existing_user = await User.get_or_none(email=update_data['email'])
                    if existing_user:
                        failed_count += 1
                        failed_updates.append({
                            "user_id": user_id,
                            "username": user.username,
                            "reason": "Email already exists"
                        })
                        continue
                
                # 验证部门是否存在
                if 'dept_id' in update_data and update_data['dept_id']:
                    from app.models.admin import Dept
                    dept = await Dept.get_or_none(id=update_data['dept_id'])
                    if not dept:
                        failed_count += 1
                        failed_updates.append({
                            "user_id": user_id,
                            "username": user.username,
                            "reason": f"Department with id {update_data['dept_id']} not found"
                        })
                        continue
                
                # 验证角色是否存在
                if 'role_ids' in update_data and update_data['role_ids']:
                    from app.models.admin import Role
                    existing_roles = await Role.filter(id__in=update_data['role_ids']).all()
                    existing_role_ids = [role.id for role in existing_roles]
                    
                    invalid_role_ids = set(update_data['role_ids']) - set(existing_role_ids)
                    if invalid_role_ids:
                        failed_count += 1
                        failed_updates.append({
                            "user_id": user_id,
                            "username": user.username,
                            "reason": f"Roles with ids {list(invalid_role_ids)} not found"
                        })
                        continue
                
                # 更新用户基本信息
                update_fields = {}
                for field in ['username', 'email', 'is_active', 'is_superuser', 'dept_id']:
                    if field in update_data:
                        update_fields[field] = update_data[field]
                
                if update_fields:
                    await User.filter(id=user_id).update(**update_fields)
                
                # 更新角色（如果提供）
                if 'role_ids' in update_data:
                    await user_controller.update_roles(user, update_data['role_ids'])
                
                # 重新获取更新后的用户
                updated_user = await User.get_or_none(id=user_id)
                
                success_count += 1
                updated_users.append({
                    "id": updated_user.id,
                    "username": updated_user.username,
                    "email": updated_user.email,
                    "is_active": updated_user.is_active,
                    "updated_fields": list(update_data.keys())
                })
                
            except Exception as e:
                failed_count += 1
                failed_updates.append({
                    "user_id": update_item.get('user_id'),
                    "reason": str(e)
                })
        
        formatter = create_formatter(request)
        return formatter.success(
            data={
                "total_requested": len(batch_data.updates),
                "success_count": success_count,
                "failed_count": failed_count,
                "updated_users": updated_users,
                "failed_updates": failed_updates
            },
            message=f"Batch update completed. {success_count} succeeded, {failed_count} failed.",
            resource_type="users",
            resource_id=None
        )
        
    except Exception as e:
        formatter = create_formatter(request)
        return formatter.internal_error(
            message=f"Failed to execute batch update: {str(e)}"
        )


@router.patch("/{user_id}", summary="更新用户 v2")
async def patch_user_v2(
    user_id: int,
    request: Request,
    patch_data: UserPatchRequest,
    current_user: User = DependAuth
):
    """
    部分更新用户 v2版本
    
    新功能：
    - 只更新提供的字段
    - 支持角色和部门更新
    - 标准化响应格式
    """
    formatter = create_formatter(request)
    try:
        user = await User.get_or_none(id=user_id)
        
        if not user:
            return formatter.not_found(
                message=f"User with id {user_id} not found",
                resource_type="users",
                resource_id=str(user_id)
            )
        
        # 安全检查：不能修改超级管理员（除非是自己）
        if user.is_superuser and user.id != current_user.id:
            return formatter.forbidden(
                message="Cannot modify superuser",
                resource_type="user",
                resource_id=str(user_id)
            )
        
        # 检查用户名和邮箱唯一性
        if patch_data.username and patch_data.username != user.username:
            existing_user = await User.get_or_none(username=patch_data.username)
            if existing_user:
                return formatter.error(
                    message="Username already exists",
                    code=400,
                    error_type="ValidationError"
                )
        
        if patch_data.email and patch_data.email != user.email:
            existing_user = await User.get_or_none(email=patch_data.email)
            if existing_user:
                return formatter.error(
                    message="Email already exists",
                    code=400,
                    error_type="ValidationError"
                )
        
        # 更新提供的字段
        update_fields = {}
        if patch_data.username is not None:
            update_fields['username'] = patch_data.username
        if patch_data.email is not None:
            update_fields['email'] = patch_data.email
        if patch_data.is_active is not None:
            update_fields['is_active'] = patch_data.is_active
        if patch_data.is_superuser is not None:
            update_fields['is_superuser'] = patch_data.is_superuser
        if patch_data.dept_id is not None:
            # 验证部门是否存在
            from app.models.admin import Dept
            if patch_data.dept_id:
                dept = await Dept.get_or_none(id=patch_data.dept_id)
                if not dept:
                    formatter = create_formatter(request)
                    return formatter.not_found(
                        message=f"Department with id {patch_data.dept_id} not found",
                        resource_type="users",
                        resource_id=str(patch_data.dept_id)
                    )
                # 直接设置部门对象
                user.dept = dept
                await user.save()
            else:
                # 清除部门关联
                user.dept = None
                await user.save()
        
        # 更新用户基本信息
        if update_fields:
            await User.filter(id=user_id).update(**update_fields)
            # 重新获取更新后的用户
            user = await User.get_or_none(id=user_id)
        
        # 更新角色（如果提供）
        if patch_data.role_ids is not None:
            # 验证角色是否存在
            from app.models.admin import Role
            if patch_data.role_ids:
                existing_roles = await Role.filter(id__in=patch_data.role_ids).all()
                existing_role_ids = [role.id for role in existing_roles]
                
                invalid_role_ids = set(patch_data.role_ids) - set(existing_role_ids)
                if invalid_role_ids:
                    formatter = create_formatter(request)
                    return formatter.not_found(
                        message=f"Roles with ids {list(invalid_role_ids)} not found",
                        resource_type="users",
                        resource_id=str(list(invalid_role_ids))
                    )
            
            # 更新角色
            await user_controller.update_roles(user, patch_data.role_ids)
        
        # 获取更新后的完整用户信息
        updated_user = await User.filter(id=user_id).prefetch_related('roles', 'dept').first()
        
        # 构建响应数据
        user_data = {
            "id": updated_user.id,
            "username": updated_user.username,
            "email": updated_user.email,
            "is_active": updated_user.is_active,
            "is_superuser": updated_user.is_superuser,
            "last_login": updated_user.last_login.isoformat() if updated_user.last_login else None,
            "created_at": updated_user.created_at.isoformat() if updated_user.created_at else None,
            "dept": {
                "id": updated_user.dept.id,
                "name": updated_user.dept.name
            } if updated_user.dept else None,
            "roles": []
        }
        
        # 添加角色信息
        user_roles = await updated_user.roles.all()
        for role in user_roles:
            user_data["roles"].append({
                "id": role.id,
                "name": role.role_name,
                "desc": role.desc
            })
        
        return formatter.success(
            data=user_data,
            message="User updated successfully",
            resource_id=str(user_id),
            resource_type="users",
            related_resources={
                "dept": str(updated_user.dept.id) if updated_user.dept else None,
                "roles": [str(role.id) for role in user_roles]
            }
        )
        
    except Exception as e:
        return formatter.internal_error(
            message=f"Failed to update user: {str(e)}"
        )

@router.post("/{user_id}/actions/reset-password", summary="重置用户密码 v2")
async def reset_user_password_v2(
    user_id: int,
    request: Request,
    password_data: ResetPasswordRequest,
    current_user: User = DependAuth
):
    """
    重置用户密码 v2版本
    
    新功能：
    - 标准化响应格式
    - 自定义密码支持
    - 安全检查
    """
    try:
        user = await User.get_or_none(id=user_id)
        
        if not user:
            formatter = create_formatter(request)
            return formatter.not_found(
                message=f"User with id {user_id} not found",
                resource_type="users",
                resource_id=str(user_id)
            )
        
        # 安全检查：不能重置超级管理员密码（除非是自己）
        if user.is_superuser and user.id != current_user.id:
            formatter = create_formatter(request)
            return formatter.forbidden(
                message="Cannot reset superuser password",
                resource_type="users",
                resource_id=str(user_id)
            )
        
        # 使用控制器重置密码
        from app.utils.password import get_password_hash
        user.password = get_password_hash(password_data.new_password)
        await user.save()
        
        formatter = create_formatter(request)
        return formatter.success(
            data={
                "user_id": user_id,
                "username": user.username,
                "password_reset": True
            },
            message="Password reset successfully",
            resource_id=str(user_id),
            resource_type="users"
        )
        
    except Exception as e:
        formatter = create_formatter(request)
        return formatter.internal_error(
            message=f"Failed to reset password: {str(e)}"
        )

@router.post("/{user_id}/actions/activate", summary="激活用户 v2")
async def activate_user_v2(
    user_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """
    激活用户 v2版本
    
    新功能：
    - 动作型操作，语义更清晰
    - 标准化响应格式
    - 安全检查
    """
    try:
        user = await User.get_or_none(id=user_id)
        
        if not user:
            formatter = create_formatter(request)
            return formatter.not_found(
                message=f"User with id {user_id} not found",
                resource_type="users",
                resource_id=str(user_id)
            )
        
        # 激活用户
        user.is_active = True
        await user.save()
        
        formatter = create_formatter(request)
        return formatter.success(
            data={
                "user_id": user_id,
                "username": user.username,
                "is_active": user.is_active,
                "action": "activated"
            },
            message="User activated successfully",
            resource_id=str(user_id),
            resource_type="users"
        )
        
    except Exception as e:
        formatter = create_formatter(request)
        return formatter.internal_error(
            message=f"Failed to activate user: {str(e)}"
        )

@router.post("/{user_id}/actions/deactivate", summary="禁用用户 v2")
async def deactivate_user_v2(
    user_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """
    禁用用户 v2版本
    
    新功能：
    - 动作型操作，语义更清晰
    - 标准化响应格式
    - 安全检查
    """
    try:
        user = await User.get_or_none(id=user_id)
        
        if not user:
            formatter = create_formatter(request)
            return formatter.not_found(
                message=f"User with id {user_id} not found",
                resource_type="users",
                resource_id=str(user_id)
            )
        
        # 安全检查：不能停用超级管理员（除非是自己）
        if user.is_superuser and user.id != current_user.id:
            formatter = create_formatter(request)
            return formatter.forbidden(
                message="Cannot deactivate superuser",
                resource_type="users",
                resource_id=str(user_id)
            )
        
        # 不能停用自己
        if user.id == current_user.id:
            formatter = create_formatter(request)
            return formatter.forbidden(
                message="Cannot deactivate yourself",
                resource_type="users",
                resource_id=str(user_id)
            )
        
        # 禁用用户
        user.is_active = False
        await user.save()
        
        formatter = create_formatter(request)
        return formatter.success(
            data={
                "user_id": user_id,
                "username": user.username,
                "is_active": user.is_active,
                "action": "deactivated"
            },
            message="User deactivated successfully",
            resource_id=str(user_id),
            resource_type="users"
        )
        
    except Exception as e:
        formatter = create_formatter(request)
        return formatter.internal_error(
            message=f"Failed to deactivate user: {str(e)}"
        )

@router.patch("/{user_id}/status", summary="更新用户状态 v2")
async def update_user_status_v2(
    user_id: int,
    request: Request,
    status_data: UserStatusRequest,
    current_user: User = DependAuth
):
    """
    更新用户状态 v2版本
    
    新功能：
    - 专门用于状态更新的端点
    - 标准化响应格式
    - 安全检查
    """
    try:
        user = await User.get_or_none(id=user_id)
        
        if not user:
            formatter = create_formatter(request)
            return formatter.not_found(
                message=f"User with id {user_id} not found",
                resource_type="users",
                resource_id=str(user_id)
            )
        
        # 安全检查：不能修改超级管理员状态（除非是自己）
        if user.is_superuser and user.id != current_user.id:
            formatter = create_formatter(request)
            return formatter.forbidden(
                message="Cannot modify superuser status",
                resource_type="users",
                resource_id=str(user_id)
            )
        
        # 如果要禁用用户，不能禁用自己
        if not status_data.is_active and user.id == current_user.id:
            formatter = create_formatter(request)
            return formatter.forbidden(
                message="Cannot deactivate yourself",
                resource_type="users",
                resource_id=str(user_id)
            )
        
        # 更新用户状态
        user.is_active = status_data.is_active
        await user.save()
        
        formatter = create_formatter(request)
        return formatter.success(
            data={
                "user_id": user_id,
                "username": user.username,
                "is_active": user.is_active,
                "action": "activated" if status_data.is_active else "deactivated"
            },
            message=f"User {'activated' if status_data.is_active else 'deactivated'} successfully",
            resource_id=str(user_id),
            resource_type="users"
        )
        
    except Exception as e:
        formatter = create_formatter(request)
        return formatter.internal_error(
            message=f"Failed to update user status: {str(e)}"
        )



@router.post("/_batch-activate", summary="批量激活用户 v2")
async def batch_activate_users_v2(
    request: Request,
    batch_data: BatchUserRequest,
    current_user: User = DependAuth
):
    """
    批量激活用户 v2版本
    
    新功能：
    - 专门用于批量激活操作
    - 标准化响应格式
    - 批量操作结果统计
    - 安全检查
    """
    try:
        if not batch_data.user_ids:
            formatter = create_formatter(request)
            return formatter.bad_request(
                message="User IDs list cannot be empty",
                resource_type="users",
                resource_id=None
            )
        
        # 获取要激活的用户
        users = await User.filter(id__in=batch_data.user_ids).all()
        
        if not users:
            formatter = create_formatter(request)
            return formatter.not_found(
                message="No users found with provided IDs",
                resource_type="users",
                resource_id=batch_data.user_ids
            )
        
        success_count = 0
        failed_count = 0
        failed_users = []
        
        for user in users:
            try:
                # 激活用户
                user.is_active = True
                await user.save()
                
                success_count += 1
                
            except Exception as e:
                failed_count += 1
                failed_users.append({
                    "user_id": user.id,
                    "username": user.username,
                    "reason": str(e)
                })
        
        formatter = create_formatter(request)
        return formatter.success(
            data={
                "action": "activate",
                "total_requested": len(batch_data.user_ids),
                "success_count": success_count,
                "failed_count": failed_count,
                "failed_users": failed_users
            },
            message=f"Batch activate completed. {success_count} succeeded, {failed_count} failed.",
            resource_type="users",
            resource_id=batch_data.user_ids
        )
        
    except Exception as e:
        formatter = create_formatter(request)
        return formatter.internal_error(
            message=f"Failed to execute batch activate: {str(e)}"
        )

@router.post("/_batch-deactivate", summary="批量禁用用户 v2")
async def batch_deactivate_users_v2(
    request: Request,
    batch_data: BatchUserRequest,
    current_user: User = DependAuth
):
    """
    批量禁用用户 v2版本
    
    新功能：
    - 专门用于批量禁用操作
    - 标准化响应格式
    - 批量操作结果统计
    - 安全检查
    """
    try:
        if not batch_data.user_ids:
            formatter = create_formatter(request)
            return formatter.bad_request(
                message="User IDs list cannot be empty",
                resource_type="users",
                resource_id=None
            )
        
        # 获取要禁用的用户
        users = await User.filter(id__in=batch_data.user_ids).all()
        
        if not users:
            formatter = create_formatter(request)
            return formatter.not_found(
                message="No users found with provided IDs",
                resource_type="users",
                resource_id=batch_data.user_ids
            )
        
        success_count = 0
        failed_count = 0
        failed_users = []
        
        for user in users:
            try:
                # 安全检查：不能禁用超级管理员（除非是自己）
                if user.is_superuser and user.id != current_user.id:
                    failed_count += 1
                    failed_users.append({
                        "user_id": user.id,
                        "username": user.username,
                        "reason": "Cannot deactivate superuser"
                    })
                    continue
                
                # 不能禁用自己
                if user.id == current_user.id:
                    failed_count += 1
                    failed_users.append({
                        "user_id": user.id,
                        "username": user.username,
                        "reason": "Cannot deactivate yourself"
                    })
                    continue
                
                # 禁用用户
                user.is_active = False
                await user.save()
                
                success_count += 1
                
            except Exception as e:
                failed_count += 1
                failed_users.append({
                    "user_id": user.id,
                    "username": user.username,
                    "reason": str(e)
                })
        
        formatter = create_formatter(request)
        return formatter.success(
            data={
                "action": "deactivate",
                "total_requested": len(batch_data.user_ids),
                "success_count": success_count,
                "failed_count": failed_count,
                "failed_users": failed_users
            },
            message=f"Batch deactivate completed. {success_count} succeeded, {failed_count} failed.",
            resource_type="users",
            resource_id=batch_data.user_ids
        )
        
    except Exception as e:
        formatter = create_formatter(request)
        return formatter.internal_error(
            message=f"Failed to execute batch deactivate: {str(e)}"
        )

@router.post("/_batch-create", summary="批量创建用户 v2")
async def batch_create_users_v2(
    request: Request,
    batch_data: BatchCreateUserRequest,
    current_user: User = DependAuth
):
    """
    批量创建用户 v2版本
    
    新功能：
    - 批量创建多个用户
    - 详细的成功/失败统计
    - 标准化响应格式
    """
    try:
        if not batch_data.users:
            formatter = create_formatter(request)
            return formatter.bad_request(
                message="Users list cannot be empty",
                resource_type="users",
                resource_id=None
            )
        
        success_count = 0
        failed_count = 0
        created_users = []
        failed_users = []
        
        for user_data in batch_data.users:
            try:
                # 检查用户名和邮箱唯一性
                existing_user = await User.get_or_none(username=user_data.username)
                if existing_user:
                    failed_count += 1
                    failed_users.append({
                        "username": user_data.username,
                        "email": user_data.email,
                        "reason": "Username already exists"
                    })
                    continue
                
                existing_user = await User.get_or_none(email=user_data.email)
                if existing_user:
                    failed_count += 1
                    failed_users.append({
                        "username": user_data.username,
                        "email": user_data.email,
                        "reason": "Email already exists"
                    })
                    continue
                
                # 验证部门是否存在
                if user_data.dept_id:
                    from app.models.admin import Dept
                    dept = await Dept.get_or_none(id=user_data.dept_id)
                    if not dept:
                        failed_count += 1
                        failed_users.append({
                            "username": user_data.username,
                            "email": user_data.email,
                            "reason": f"Department with id {user_data.dept_id} not found"
                        })
                        continue
                
                # 验证角色是否存在
                if user_data.role_ids:
                    from app.models.admin import Role
                    existing_roles = await Role.filter(id__in=user_data.role_ids).all()
                    existing_role_ids = [role.id for role in existing_roles]
                    
                    invalid_role_ids = set(user_data.role_ids) - set(existing_role_ids)
                    if invalid_role_ids:
                        failed_count += 1
                        failed_users.append({
                            "username": user_data.username,
                            "email": user_data.email,
                            "reason": f"Roles with ids {list(invalid_role_ids)} not found"
                        })
                        continue
                
                # 创建用户数据对象
                from app.schemas.users import UserCreate
                user_create_data = UserCreate(
                    username=user_data.username,
                    email=user_data.email,
                    password=user_data.password,
                    is_active=user_data.is_active,
                    is_superuser=user_data.is_superuser,
                    dept_id=user_data.dept_id
                )
                
                # 创建用户
                new_user = await user_controller.create_user(user_create_data)
                
                # 设置角色
                if user_data.role_ids:
                    await user_controller.update_roles(new_user, user_data.role_ids)
                
                success_count += 1
                created_users.append({
                    "id": new_user.id,
                    "username": new_user.username,
                    "email": new_user.email,
                    "is_active": new_user.is_active
                })
                
            except Exception as e:
                failed_count += 1
                failed_users.append({
                    "username": user_data.username,
                    "email": user_data.email,
                    "reason": str(e)
                })
        
        formatter = create_formatter(request)
        return formatter.created(
            data={
                "total_requested": len(batch_data.users),
                "success_count": success_count,
                "failed_count": failed_count,
                "created_users": created_users,
                "failed_users": failed_users
            },
            message=f"Batch create completed. {success_count} succeeded, {failed_count} failed.",
            resource_type="users",
            resource_id=[user["id"] for user in created_users]
        )
        
    except Exception as e:
        formatter = create_formatter(request)
        return formatter.internal_error(
            message=f"Failed to execute batch create: {str(e)}"
        )

# 批量更新路由已移动到正确位置



@router.post("/search", summary="复杂查询用户 v2")
async def search_users_v2(
    request: Request,
    search_data: UserSearchRequest,
    current_user: User = DependAuth
):
    """
    复杂查询用户 v2版本
    
    新功能：
    - 支持复杂查询条件
    - 多字段筛选
    - 日期范围查询
    - 角色筛选
    - 自定义排序
    - 标准化响应格式
    """
    try:
        # 计算偏移量
        offset = (search_data.page - 1) * search_data.page_size
        
        # 构建查询条件
        query = User.all().prefetch_related('roles', 'dept')
        
        # 添加筛选条件
        if search_data.username:
            query = query.filter(username__icontains=search_data.username)
        if search_data.email:
            query = query.filter(email__icontains=search_data.email)
        if search_data.dept_id:
            query = query.filter(dept_id=search_data.dept_id)
        if search_data.is_active is not None:
            query = query.filter(is_active=search_data.is_active)
        if search_data.is_superuser is not None:
            query = query.filter(is_superuser=search_data.is_superuser)
        
        # 日期范围查询
        if search_data.created_after:
            from datetime import datetime
            # 转换为naive datetime以匹配数据库格式
            created_after = datetime.fromisoformat(search_data.created_after.replace('Z', '').replace('+00:00', ''))
            query = query.filter(created_at__gte=created_after)
        if search_data.created_before:
            from datetime import datetime
            # 转换为naive datetime以匹配数据库格式
            created_before = datetime.fromisoformat(search_data.created_before.replace('Z', '').replace('+00:00', ''))
            query = query.filter(created_at__lte=created_before)
        
        # 角色筛选
        if search_data.role_ids:
            query = query.filter(roles__id__in=search_data.role_ids)
        
        # 排序
        sort_field = search_data.sort_by or "created_at"
        if search_data.sort_order == "asc":
            query = query.order_by(sort_field)
        else:
            query = query.order_by(f"-{sort_field}")
        
        # 获取总数（在分页之前）
        total = await query.count()
        
        # 应用分页
        users = await query.offset(offset).limit(search_data.page_size).all()
        
        # 转换为字典格式
        user_data = []
        for user in users:
            # 获取用户角色信息
            roles = []
            if hasattr(user, 'roles'):
                user_roles = await user.roles.all()
                roles = [{'id': role.id, 'name': role.role_name, 'desc': role.desc} for role in user_roles]
            
            # 获取用户部门信息
            dept = None
            if hasattr(user, 'dept') and user.dept:
                dept = {'id': user.dept.id, 'name': user.dept.name}
            
            user_data.append({
                "id": user.id,
                "username": user.username,
                "alias": getattr(user, 'alias', None),
                "email": user.email,
                "phone": getattr(user, 'phone', None),
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "dept_id": user.dept_id,
                "last_login": user.last_login.isoformat() if getattr(user, 'last_login', None) else None,
                "roles": roles,
                "dept": dept,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            })
        
        formatter = create_formatter(request)
        return formatter.paginated_success(
            data=user_data,
            total=total,
            page=search_data.page,
            page_size=search_data.page_size,
            message="Users search completed successfully"
        )
        
    except Exception as e:
        formatter = create_formatter(request)
        return formatter.internal_error(
            message=f"Failed to search users: {str(e)}"
        )