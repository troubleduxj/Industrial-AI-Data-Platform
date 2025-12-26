from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from app.controllers.user import user_controller
from app.core.ctx import CTX_USER_ID
from app.core.dependency import DependAuth
from app.models.admin import SysApiEndpoint, Menu, Role, User
from app.schemas.base import Fail, Success
from app.schemas.login import *
from app.schemas.menus import BaseMenu
from app.schemas.users import BaseUser, UpdatePassword
from app.settings import settings
from app.utils.jwt_utils import create_access_token
from app.utils.password import get_password_hash, verify_password

router = APIRouter()


@router.post("/access_token", summary="获取token")
async def login_access_token(credentials: CredentialsSchema):
    user: User = await user_controller.authenticate(credentials)
    await user_controller.update_last_login(user.id)
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    # 确保使用naive datetime以避免时区问题
    now = datetime.now()
    if now.tzinfo is not None:
        now = now.replace(tzinfo=None)
    expire = now + access_token_expires

    data = JWTOut(
        access_token=create_access_token(
            data=JWTPayload(
                user_id=user.id,
                username=user.username,
                is_superuser=user.is_superuser,
                exp=expire,
            )
        ),
        username=user.username,
    )
    return Success(data=data.model_dump())


@router.get("/userinfo", summary="查看用户信息", dependencies=[DependAuth])
async def get_userinfo():
    user_id = CTX_USER_ID.get()
    user_obj = await User.filter(id=user_id).prefetch_related('roles').first()
    
    # 手动构建用户数据，避免ManyToManyRelation序列化问题
    user_data = {
        "id": user_obj.id,
        "email": user_obj.email,
        "username": user_obj.username,
        "is_active": user_obj.is_active,
        "is_superuser": user_obj.is_superuser,
        "created_at": user_obj.created_at.isoformat() if user_obj.created_at else None,
        "updated_at": user_obj.updated_at.isoformat() if user_obj.updated_at else None,
        "last_login": user_obj.last_login.isoformat() if user_obj.last_login else None,
        "roles": [role.role_name for role in await user_obj.roles.all()],
        "avatar": f"/api/v1/avatar/generate/{user_obj.username}?size=100"
    }
    
    return Success(data=user_data)


@router.get("/usermenu", summary="查看用户菜单", dependencies=[DependAuth])
async def get_user_menu():
    user_id = CTX_USER_ID.get()
    user_obj = await User.filter(id=user_id).first()
    menus: list[Menu] = []
    if user_obj.is_superuser:
        menus = await Menu.all()
    else:
        role_objs: list[Role] = await user_obj.roles
        for role_obj in role_objs:
            menu = await role_obj.menus
            menus.extend(menu)
        menus = list(set(menus))
    parent_menus: list[Menu] = []
    for menu in menus:
        if menu.parent_id == 0:
            parent_menus.append(menu)

    # 使用 Pydantic 模型进行序列化
    serialized_menus = []
    for parent_menu in parent_menus:
        # 将 Tortoise ORM Menu 对象转换为 BaseMenu Pydantic 对象
        parent_menu_pydantic = BaseMenu.model_validate(parent_menu)

        # 递归处理子菜单
        children_pydantic = []
        for menu_child in menus:
            if menu_child.parent_id == parent_menu.id:
                children_pydantic.append(BaseMenu.model_validate(menu_child))

        # 将子菜单添加到父菜单的 children 字段中
        parent_menu_pydantic.children = children_pydantic

        # 将 Pydantic 对象转换为字典以便 JSON 序列化
        serialized_menus.append(parent_menu_pydantic.model_dump())

    return Success(data=serialized_menus)


@router.get("/userapi", summary="查看用户API", dependencies=[DependAuth])
async def get_user_api():
    user_id = CTX_USER_ID.get()
    user_obj = await User.filter(id=user_id).first()
    if user_obj.is_superuser:
        api_objs: list[Api] = await Api.all()
        apis = [api.http_method.lower() + api.api_path for api in api_objs]
        return Success(data=apis)
    role_objs: list[Role] = await user_obj.roles
    apis = []
    for role_obj in role_objs:
        api_objs: list[Api] = await role_obj.apis
        apis.extend([api.http_method.lower() + api.api_path for api in api_objs])
    apis = list(set(apis))
    return Success(data=apis)


@router.post("/update_password", summary="修改密码", dependencies=[DependAuth])
async def update_user_password(req_in: UpdatePassword):
    user_id = CTX_USER_ID.get()
    user = await user_controller.get(user_id)
    verified = verify_password(req_in.old_password, user.password)
    if not verified:
        return Fail(msg="旧密码验证错误！")
    user.password = get_password_hash(req_in.new_password)
    await user.save()
    return Success(msg="修改成功")
