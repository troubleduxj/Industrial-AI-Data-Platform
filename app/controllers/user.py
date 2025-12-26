from datetime import datetime, timezone
from typing import List, Optional

from fastapi.exceptions import HTTPException

from app.core.crud import CRUDBase
from app.core.optimized_crud import OptimizedCRUDBase
from app.models.admin import User
from app.schemas.login import CredentialsSchema
from app.schemas.users import UserCreate, UserUpdate
from app.utils.password import get_password_hash, verify_password
from app.core.permission_decorators import user_role_change_event, user_status_change_event
from app.core.query_optimizer import monitor_performance, cached_query

from .role import role_controller


class UserController(OptimizedCRUDBase[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(model=User, cache_ttl=600)  # 用户数据缓存10分钟

    @monitor_performance
    @cached_query(ttl=300)
    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.model.filter(email=email).first()

    @monitor_performance
    @cached_query(ttl=300)
    async def get_by_username(self, username: str) -> Optional[User]:
        return await self.model.filter(username=username).first()

    async def create_user(self, obj_in: UserCreate) -> User:
        from app.log import logger

        try:
            logger.info(f"Creating user: {obj_in.username}")
            obj_in.password = get_password_hash(password=obj_in.password)
            # 使用UserCreate的create_dict()方法来排除role_ids字段
            obj_dict = obj_in.create_dict()
            obj = await self.create(obj_dict)
            logger.info(f"User created successfully: {obj.username}")
            return obj
        except Exception as e:
            logger.error(f"Failed to create user {obj_in.username}: {str(e)}")
            raise

    async def update_last_login(self, id: int) -> None:
        user = await self.model.get(id=id)
        # 使用naive datetime以匹配数据库字段类型(timestamp without time zone)
        # 确保datetime对象没有时区信息
        now = datetime.now()
        if now.tzinfo is not None:
            now = now.replace(tzinfo=None)
        
        # 确保所有时间字段都没有时区信息
        if user.created_at and user.created_at.tzinfo is not None:
            user.created_at = user.created_at.replace(tzinfo=None)
        if user.updated_at and user.updated_at.tzinfo is not None:
            user.updated_at = user.updated_at.replace(tzinfo=None)
        if user.login_date and user.login_date.tzinfo is not None:
            user.login_date = user.login_date.replace(tzinfo=None)
            
        user.last_login = now
        await user.save()
    
    @user_status_change_event
    async def update_user_status(self, user_id: int, is_active: bool) -> User:
        """更新用户状态"""
        user = await self.get(id=user_id)
        old_status = user.is_active
        user.is_active = is_active
        await user.save()
        return user

    async def authenticate(self, credentials: CredentialsSchema) -> Optional["User"]:
        user = await self.model.filter(username=credentials.username).first()
        if not user:
            raise HTTPException(status_code=400, detail="无效的用户名")
        verified = verify_password(credentials.password, user.password)
        if not verified:
            raise HTTPException(status_code=400, detail="密码错误!")
        if not user.is_active:
            raise HTTPException(status_code=400, detail="用户已被禁用")
        return user

    @user_role_change_event
    @monitor_performance
    async def update_roles(self, user: User, role_ids: List[int]) -> None:
        await user.roles.clear()
        
        # 批量获取角色对象以提高性能
        if role_ids:
            roles = await role_controller.model.filter(id__in=role_ids).all()
            for role_obj in roles:
                await user.roles.add(role_obj)
        
        # 清理用户相关缓存
        self._clear_object_cache(user.id)

    async def reset_password(self, user_id: int):
        user_obj = await self.get(id=user_id)
        if user_obj.is_superuser:
            raise HTTPException(status_code=403, detail="不允许重置超级管理员密码")
        user_obj.password = get_password_hash(password="123456")
        await user_obj.save()

    @monitor_performance
    @cached_query(ttl=300)
    async def get_user_menu(self, user_id: int):
        """获取用户可访问的菜单列表"""
        from app.models.admin import Menu, Role
        
        user_obj = await self.get(id=user_id)
        if not user_obj:
            return []
        
        menus = []
        if user_obj.is_superuser:
            # 超级用户获取所有菜单，按order_num排序
            menus = await Menu.all().order_by('order_num', 'id')
        else:
            # 普通用户通过角色获取菜单
            role_objs = await user_obj.roles.all()
            menu_set = set()
            for role_obj in role_objs:
                role_menus = await role_obj.menus.all()
                menu_set.update(role_menus)
            # 将set转换为list并按order_num排序
            menus = sorted(list(menu_set), key=lambda x: (x.order_num, x.id))
        
        return menus


user_controller = UserController()
