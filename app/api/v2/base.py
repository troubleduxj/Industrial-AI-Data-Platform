"""
API v2 Base endpoints
提供认证、用户信息等基础功能的v2版本
"""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, status, Request
from app.controllers.user import user_controller
from app.schemas.base import Fail, Success
from app.schemas.login import CredentialsSchema, JWTOut, JWTPayload
from app.settings import settings
from app.utils.jwt_utils import create_access_token
from app.core.dependency import DependAuth
from app.core.response_formatter_v2 import ResponseFormatterV2
from app.models.admin import SysApiEndpoint, Role, User

router = APIRouter()


@router.post("/access_token", summary="用户登录获取访问令牌")
async def login_access_token(credentials: CredentialsSchema):
    """
    用户登录接口 - API v2版本
    
    提供与v1相同的登录功能，但返回v2格式的响应
    """
    try:
        # 验证用户凭据
        user = await user_controller.authenticate(credentials)
        
        # 更新最后登录时间
        await user_controller.update_last_login(user.id)
        
        # 创建访问令牌
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        # 确保使用naive datetime以避免时区问题
        now = datetime.now()
        if now.tzinfo is not None:
            now = now.replace(tzinfo=None)
        expire = now + access_token_expires
        
        # 生成JWT令牌
        access_token = create_access_token(
            data=JWTPayload(
                user_id=user.id,
                username=user.username,
                is_superuser=user.is_superuser,
                exp=expire
            )
        )
        
        # 构建v2格式响应
        response_data = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # 秒
            "expires_at": expire.isoformat(),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        }
        
        return Success(
            data=response_data,
            message="登录成功",
            code=200
        )
        
    except HTTPException as e:
        return Fail(
            message=e.detail,
            code=e.status_code
        )
    except Exception as e:
        return Fail(
            message=f"登录失败: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/userinfo", summary="获取当前用户信息", dependencies=[DependAuth])
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
        dept = None
        if user_obj.dept_id:
            from app.controllers.dept import dept_controller
            dept = await dept_controller.get(id=user_obj.dept_id)
        
        user_data = {
            "id": user_obj.id,
            "username": user_obj.username,
            "email": user_obj.email,
            "is_active": user_obj.is_active,
            "is_superuser": user_obj.is_superuser,
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


@router.get("/usermenu", summary="获取当前用户菜单", dependencies=[DependAuth])
async def get_user_menu(request: Request, current_user=DependAuth):
    """
    获取当前用户可访问的菜单 - API v2版本
    """
    # 强制将 current_user 设置到 request.state 中
    if hasattr(current_user, "id"):
        request.state.user = current_user
        request.state.user_id = current_user.id
        
    formatter = ResponseFormatterV2(request)
    
    try:
        # 如果 current_user 是依赖项返回的，它可能已经是一个 User 对象
        # 但如果是 None 或者不是预期的类型，我们需要处理
        if not current_user:
            # 尝试从 request.state 获取
            if hasattr(request.state, "user") and request.state.user:
                current_user = request.state.user
            else:
                return formatter.error(
                    message="未认证用户",
                    code=401
                )
        
        user_id = current_user.id
        user_obj = await user_controller.get(id=user_id)
        if not user_obj:
            return formatter.not_found("用户不存在", "user")
        
        # 获取用户菜单权限
        menus = await user_controller.get_user_menu(user_obj.id)
        
        # 构建菜单树结构
        menu_tree = []
        menu_dict = {}
        
        # 先创建所有菜单项的字典
        for menu in menus:
            menu_item = {
                "id": menu.id,
                "name": menu.name,
                "path": menu.path,
                "component": menu.component,
                "redirect": menu.redirect,
                "icon": menu.icon,
                "order": menu.order,
                "is_hidden": menu.is_hidden,
                "keepalive": menu.keepalive,
                "menuType": menu.menu_type,  # 使用驼峰命名，与前端一致
                "type": menu.menu_type,      # 兼容字段
                "parent_id": menu.parent_id,
                "children": []
            }
            menu_dict[menu.id] = menu_item
        
        # 构建树形结构
        for menu_item in menu_dict.values():
            # 根菜单：parent_id为NULL或0
            if menu_item["parent_id"] is None or menu_item["parent_id"] == 0:
                menu_tree.append(menu_item)
            else:
                parent = menu_dict.get(menu_item["parent_id"])
                if parent:
                    parent["children"].append(menu_item)
        
        # 按order排序
        def sort_menus(menu_list):
            menu_list.sort(key=lambda x: x["order"])
            for menu in menu_list:
                if menu["children"]:
                    sort_menus(menu["children"])
        
        sort_menus(menu_tree)
        
        return formatter.success(
            data=menu_tree,
            message="获取用户菜单成功",
            code=200,
            resource_type="menu"
        )
        
    except Exception as e:
        return formatter.internal_error(
            message=f"获取用户菜单失败: {str(e)}"
        )


@router.post("/logout", summary="用户登出", dependencies=[DependAuth])
async def logout(current_user=DependAuth):
    """
    用户登出接口 - API v2版本
    
    注意：JWT令牌是无状态的，实际的令牌失效需要在客户端处理
    这里主要是提供一个标准的登出端点
    """
    try:
        return Success(
            data={"message": "登出成功"},
            message="登出成功",
            code=200
        )
    except Exception as e:
        return Fail(
            message=f"登出失败: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/refresh", summary="刷新访问令牌", dependencies=[DependAuth])
async def refresh_token(current_user=DependAuth):
    """
    刷新访问令牌 - API v2版本
    """
    try:
        user_obj = await user_controller.get(id=current_user.user_id)
        if not user_obj:
            return Fail(message="用户不存在", code=404)
        
        # 创建新的访问令牌
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        # 确保使用naive datetime以避免时区问题
        now = datetime.now()
        if now.tzinfo is not None:
            now = now.replace(tzinfo=None)
        expire = now + access_token_expires
        
        access_token = create_access_token(
            data=JWTPayload(
                user_id=user_obj.id,
                username=user_obj.username,
                is_superuser=user_obj.is_superuser,
                exp=expire
            )
        )
        
        response_data = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "expires_at": expire.isoformat()
        }
        
        return Success(
            data=response_data,
            message="令牌刷新成功",
            code=200
        )
        
    except Exception as e:
        return Fail(
            message=f"令牌刷新失败: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/userapi", summary="获取用户可访问的API列表", dependencies=[DependAuth])
async def get_user_api(request: Request, current_user=DependAuth):
    """
    获取当前用户可访问的API列表 - API v2版本
    
    根据用户角色权限返回可访问的V2 API接口列表
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        user_obj = await User.get(id=current_user.id)
        
        if user_obj.is_superuser:
            # 超级用户可以访问所有V2 API
            from app.models.admin import SysApiEndpoint
            v2_api_objs = await SysApiEndpoint.all()
            apis = [api.http_method.lower() + api.api_path for api in v2_api_objs]
        else:
            # 普通用户根据角色权限获取V2 API
            role_objs = await user_obj.roles.all()
            apis = []
            
            for role_obj in role_objs:
                # 获取V2 API权限
                v2_api_objs = await role_obj.apis.all()
                apis.extend([api.http_method.lower() + api.api_path for api in v2_api_objs])
            
            apis = list(set(apis))  # 去重
        
        return formatter.success(
            data=apis,
            message="获取用户API列表成功",
            resource_type="apis"
        )
        
    except Exception as e:
        return formatter.internal_error(f"获取用户API列表失败: {str(e)}")