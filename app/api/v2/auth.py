"""
API v2 认证模块
提供用户认证相关的API接口，支持JWT令牌管理、刷新和黑名单机制
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Request, Header
from app.controllers.user import user_controller
from app.services.auth_service import auth_service
from app.schemas.login import CredentialsSchema, JWTOut, JWTPayload, RefreshTokenSchema, TokenResponse
from app.schemas.users import UpdatePassword
from app.utils.password import verify_password, get_password_hash
from app.settings import settings
from app.core.dependency import DependAuth
from app.core.response_formatter_v2 import ResponseFormatterV2
from app.models.admin import SysApiEndpoint, Role, User
from app.core.unified_logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/login", summary="用户登录")
async def login(request: Request, credentials: CredentialsSchema):
    """
    用户登录接口 - API v2版本
    
    支持JWT令牌生成、验证、刷新功能和令牌黑名单机制
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 使用认证服务进行用户认证
        user = await auth_service.authenticate(credentials)
        
        # 更新最后登录时间
        await auth_service.update_last_login(user)
        
        # 生成访问令牌和刷新令牌
        tokens = await auth_service.generate_tokens(user)
        
        # 构建v2格式响应
        response_data = {
            **tokens,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "isActive": user.is_active,
                "isSuperuser": user.is_superuser,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        }
        
        logger.info(f"用户登录成功: {user.username}")
        
        return formatter.success(
            data=response_data,
            message="登录成功",
            code=200,
            resource_type="auth"
        )
        
    except HTTPException as e:
        logger.warning(f"用户登录失败: {e.detail}")
        return formatter.error(
            message=e.detail,
            code=e.status_code,
            error_type="AUTHENTICATION_ERROR"
        )
    except Exception as e:
        logger.error(f"登录过程中发生错误: {str(e)}")
        return formatter.internal_error(
            message=f"登录失败: {str(e)}"
        )


@router.get("/user", summary="获取当前用户信息", dependencies=[DependAuth])
@router.get("/userinfo", summary="获取当前用户信息 (兼容路径)", dependencies=[DependAuth])
async def get_user_info(request: Request, current_user=DependAuth):
    """
    获取当前登录用户信息 - API v2版本
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        user_obj = await user_controller.get(id=current_user.id)
        if not user_obj:
            return formatter.not_found("用户不存在", "user")
        
        # 获取用户角色和部门信息
        roles = await user_obj.roles.all()
        dept = await user_obj.dept.get() if user_obj.dept_id else None
        
        user_data = {
            "id": user_obj.id,
            "username": user_obj.username,
            "email": user_obj.email,
            "isActive": user_obj.is_active,
            "isSuperuser": user_obj.is_superuser,
            "created_at": user_obj.created_at.isoformat() if user_obj.created_at else None,
            "updated_at": user_obj.updated_at.isoformat() if user_obj.updated_at else None,
            "last_login": user_obj.last_login.isoformat() if user_obj.last_login else None,
            "roles": [{"id": role.id, "name": role.role_name} for role in roles],
            "dept": {
                "id": dept.id,
                "name": dept.name
            } if dept else None,
            "avatar": f"/api/v2/avatar/generate/{user_obj.username}?size=100",
            # v2增强字段
            "profile": {
                "roles_count": len(roles),
                "dept_name": dept.name if dept else None,
                "permissions_count": 0  # 可以后续添加权限统计
            }
        }
        
        return formatter.success(
            data=user_data,
            message="获取用户信息成功",
            code=200,
            resource_type="user"
        )
        
    except Exception as e:
        return formatter.internal_error(
            message=f"获取用户信息失败: {str(e)}"
        )


@router.get("/user/apis", summary="获取当前用户API权限", dependencies=[DependAuth])
@router.get("/user-apis", summary="获取当前用户API权限 (兼容路径)", dependencies=[DependAuth])
async def get_user_apis(request: Request, current_user=DependAuth):
    """
    获取当前用户的API权限列表 - API v2版本
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        user_obj = await user_controller.get(id=current_user.id)
        if not user_obj:
            return formatter.not_found("用户不存在", "user")
        
        # 如果是超级管理员，返回所有API权限
        if user_obj.is_superuser:
            all_apis = await SysApiEndpoint.all()
            api_permissions = [f"{api.http_method} {api.api_path}" for api in all_apis]
        else:
            # 获取用户角色的API权限
            roles = await user_obj.roles.all()
            api_permissions = []
            
            for role in roles:
                # 1. 获取角色的API权限（通过t_sys_role_api表）
                role_apis = await role.apis.all()
                for api in role_apis:
                    permission = f"{api.http_method} {api.api_path}"
                    if permission not in api_permissions:
                        api_permissions.append(permission)
                
                # 2. 获取角色的按钮权限（通过t_sys_role_menu表）
                # 按钮权限的perms字段包含API权限标识
                role_menus = await role.menus.filter(menu_type='button').all()
                for menu in role_menus:
                    if menu.perms and menu.perms not in api_permissions:
                        api_permissions.append(menu.perms)
        
        return formatter.success(
            data=api_permissions,
            message="获取用户API权限成功",
            code=200,
            resource_type="permissions"
        )
        
    except Exception as e:
        return formatter.internal_error(
            message=f"获取用户API权限失败: {str(e)}"
        )


def build_menu_tree(menus_data):
    """
    构建菜单树形结构（包含按钮权限）
    
    Args:
        menus_data: 平铺的菜单列表
        
    Returns:
        树形结构的菜单列表
    """
    if not menus_data:
        return []
    
    # 创建ID到菜单的映射
    menu_map = {menu["id"]: {**menu, "children": []} for menu in menus_data}
    
    # 构建树形结构
    tree = []
    for menu in menus_data:
        menu_id = menu["id"]
        parent_id = menu.get("parentId")
        
        if parent_id and parent_id in menu_map:
            # 有父节点，添加到父节点的children中
            menu_map[parent_id]["children"].append(menu_map[menu_id])
        else:
            # 根节点
            tree.append(menu_map[menu_id])
    
    return tree


@router.get("/user/menus", summary="获取当前用户菜单权限", dependencies=[DependAuth])
async def get_user_menus(request: Request, current_user=DependAuth):
    """
    获取当前用户的菜单权限列表 - API v2版本（包含按钮权限）
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        user_obj = await user_controller.get(id=current_user.id)
        if not user_obj:
            return formatter.not_found("用户不存在", "user")
        
        # 获取用户菜单权限（包含按钮类型）
        if user_obj.is_superuser:
            # 超级管理员获取所有菜单（包括按钮）
            from app.models.admin import Menu
            all_menus = await Menu.all().order_by("order_num", "id")
            menus = [{
                "id": menu.id,
                "name": menu.name,
                "path": menu.path or "",
                "component": menu.component or "",
                "redirect": menu.redirect,
                "icon": menu.icon,
                "order": menu.order,
                "isHidden": menu.is_hidden,
                "keepalive": menu.keepalive,
                "menuType": menu.menu_type,  # 包含 'button' 类型
                "parentId": menu.parent_id,
                "perms": menu.perms,  # 按钮权限标识
                "type": menu.menu_type  # 前端兼容字段
            } for menu in all_menus]
        else:
            # 普通用户通过角色获取菜单（包括按钮）
            roles = await user_obj.roles.all()
            menu_ids = set()
            
            for role in roles:
                role_menus = await role.menus.all()
                for menu in role_menus:
                    menu_ids.add(menu.id)
            
            if menu_ids:
                from app.models.admin import Menu
                user_menus = await Menu.filter(id__in=menu_ids).order_by("order_num", "id")
                menus = [{
                    "id": menu.id,
                    "name": menu.name,
                    "path": menu.path or "",
                    "component": menu.component or "",
                    "redirect": menu.redirect,
                    "icon": menu.icon,
                    "order": menu.order,
                    "isHidden": menu.is_hidden,
                    "keepalive": menu.keepalive,
                    "menuType": menu.menu_type,  # 包含 'button' 类型
                    "parentId": menu.parent_id,
                    "perms": menu.perms,  # 按钮权限标识
                    "type": menu.menu_type  # 前端兼容字段
                } for menu in user_menus]
            else:
                menus = []
        
        # 构建树形结构
        menu_tree = build_menu_tree(menus)
        
        return formatter.success(
            data=menu_tree,
            message="获取用户菜单权限成功",
            code=200,
            resource_type="menus"
        )
        
    except Exception as e:
        logger.error(f"获取用户菜单权限失败: {str(e)}")
        return formatter.internal_error(
            message=f"获取用户菜单权限失败: {str(e)}"
        )





@router.post("/change-password", summary="修改密码", dependencies=[DependAuth])
async def change_password(request: Request, password_data: UpdatePassword, current_user=DependAuth):
    """
    用户修改密码接口 - API v2版本
    
    允许用户修改自己的密码
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 获取当前用户信息
        user = await user_controller.get(current_user.user_id)
        if not user:
            return formatter.not_found("用户不存在", "user")
        
        # 验证旧密码
        if not verify_password(password_data.old_password, user.password):
            return formatter.validation_error(
                message="旧密码验证错误",
                details=[{
                    "field": "old_password",
                    "code": "INVALID_PASSWORD",
                    "message": "旧密码不正确"
                }]
            )
        
        # 更新密码
        user.password = get_password_hash(password_data.new_password)
        await user.save()
        
        return formatter.success(
            data={"message": "密码修改成功"},
            message="密码修改成功",
            resource_id=str(user.id),
            resource_type="user"
        )
        
    except Exception as e:
        return formatter.internal_error(f"修改密码失败: {str(e)}")


@router.post("/refresh", summary="刷新访问令牌", response_model=TokenResponse)
async def refresh_token(request: Request, token_data: RefreshTokenSchema):
    """
    刷新访问令牌接口
    
    使用刷新令牌获取新的访问令牌和刷新令牌
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 使用认证服务刷新令牌
        new_tokens = await auth_service.refresh_token(token_data.refresh_token)
        
        if not new_tokens:
            return formatter.error(
                message="刷新令牌无效或已过期",
                code=401,
                error_type="TOKEN_REFRESH_ERROR"
            )
        
        logger.info("令牌刷新成功")
        
        return formatter.success(
            data=new_tokens,
            message="令牌刷新成功",
            code=200,
            resource_type="auth"
        )
        
    except Exception as e:
        logger.error(f"令牌刷新过程中发生错误: {str(e)}")
        return formatter.internal_error(
            message=f"令牌刷新失败: {str(e)}"
        )


@router.post("/logout", summary="用户登出", dependencies=[DependAuth])
async def logout(
    request: Request, 
    current_user=DependAuth,
    authorization: Optional[str] = Header(None)
):
    """
    用户登出接口 - API v2版本
    
    支持JWT令牌黑名单机制，确保令牌失效
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 提取访问令牌
        token = None
        if authorization and authorization.startswith("Bearer "):
            token = authorization[7:]
        
        if token:
            # 使用认证服务进行登出
            success = await auth_service.logout(token, current_user.id)
            if not success:
                logger.warning(f"用户登出失败: user_id={current_user.id}")
        
        logger.info(f"用户登出成功: {current_user.username}")
        
        return formatter.success(
            data={"message": "登出成功"},
            message="登出成功",
            code=200,
            resource_type="auth"
        )
        
    except Exception as e:
        logger.error(f"登出过程中发生错误: {str(e)}")
        return formatter.internal_error(
            message=f"登出失败: {str(e)}"
        )


@router.post("/logout-all", summary="从所有设备登出", dependencies=[DependAuth])
async def logout_all_devices(request: Request, current_user=DependAuth):
    """
    从所有设备登出接口
    
    使所有设备上的令牌失效
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 使用认证服务从所有设备登出
        success = await auth_service.logout_all_devices(current_user.id)
        
        if success:
            logger.info(f"用户从所有设备登出成功: {current_user.username}")
            return formatter.success(
                data={"message": "已从所有设备登出"},
                message="已从所有设备登出",
                code=200,
                resource_type="auth"
            )
        else:
            return formatter.error(
                message="登出失败",
                code=500,
                error_type="LOGOUT_ERROR"
            )
        
    except Exception as e:
        logger.error(f"从所有设备登出过程中发生错误: {str(e)}")
        return formatter.internal_error(
            message=f"登出失败: {str(e)}"
        )