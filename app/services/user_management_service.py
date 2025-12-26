#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户管理服务
实现用户的CRUD操作、角色分配、状态管理等功能
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from tortoise.transactions import in_db_transaction
from tortoise.exceptions import IntegrityError

from app.models.admin import User, Role, Dept
from app.utils.password import get_password_hash, verify_password
from app.core.unified_logger import get_logger
from app.core.permission_cache import permission_cache_manager

logger = get_logger(__name__)


class UserManagementService:
    """用户管理服务"""
    
    def __init__(self):
        self.cache_ttl = 300  # 缓存5分钟
        self.default_password = "123456"  # 默认密码
    
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """创建用户"""
        try:
            logger.info(f"创建用户: {user_data.get('username')}")
            
            # 检查用户名是否已存在
            existing_user = await User.get_or_none(username=user_data['username'])
            if existing_user:
                raise ValueError(f"用户名 '{user_data['username']}' 已存在")
            
            # 检查邮箱是否已存在
            if user_data.get('email'):
                existing_email = await User.get_or_none(email=user_data['email'])
                if existing_email:
                    raise ValueError(f"邮箱 '{user_data['email']}' 已存在")
            
            async with in_db_transaction():
                # 处理密码
                password = user_data.get('password', self.default_password)
                hashed_password = get_password_hash(password)
                
                # 创建用户
                user = await User.create(
                    username=user_data['username'],
                    nick_name=user_data.get('nick_name'),
                    email=user_data.get('email'),
                    phone_number=user_data.get('phone_number'),
                    sex=user_data.get('sex'),
                    avatar=user_data.get('avatar'),
                    password=hashed_password,
                    user_type=user_data.get('user_type', '00'),
                    status=user_data.get('status', '0'),
                    remark=user_data.get('remark'),
                    dept_id=user_data.get('dept_id'),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                # 分配角色
                role_ids = user_data.get('role_ids', [])
                if role_ids:
                    await self._assign_roles_to_user(user, role_ids)
                
                logger.info(f"用户创建成功: {user.username} (ID: {user.id})")
                return user
        
        except IntegrityError as e:
            logger.error(f"创建用户失败，数据完整性错误: {e}")
            raise ValueError("用户数据违反唯一性约束")
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            raise
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """获取用户详情"""
        try:
            user = await User.get_or_none(id=user_id).prefetch_related('roles', 'dept')
            if not user:
                logger.warning(f"用户不存在: id={user_id}")
                return None
            
            return user
        
        except Exception as e:
            logger.error(f"获取用户失败: id={user_id}, error={e}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        try:
            user = await User.get_or_none(username=username).prefetch_related('roles', 'dept')
            return user
        
        except Exception as e:
            logger.error(f"根据用户名获取用户失败: username={username}, error={e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        try:
            user = await User.get_or_none(email=email).prefetch_related('roles', 'dept')
            return user
        
        except Exception as e:
            logger.error(f"根据邮箱获取用户失败: email={email}, error={e}")
            return None
    
    async def get_users(self, 
                       status: Optional[str] = None,
                       user_type: Optional[str] = None,
                       dept_id: Optional[int] = None,
                       keyword: Optional[str] = None,
                       page: int = 1,
                       page_size: int = 20) -> Dict[str, Any]:
        """获取用户列表"""
        try:
            query = User.filter(del_flag='0')
            
            # 状态过滤
            if status is not None:
                query = query.filter(status=status)
            
            # 用户类型过滤
            if user_type is not None:
                query = query.filter(user_type=user_type)
            
            # 部门过滤
            if dept_id is not None:
                query = query.filter(dept_id=dept_id)
            
            # 关键词搜索
            if keyword:
                query = query.filter(
                    username__icontains=keyword
                ).union(
                    User.filter(nick_name__icontains=keyword, del_flag='0')
                ).union(
                    User.filter(email__icontains=keyword, del_flag='0')
                )
            
            # 总数统计
            total = await query.count()
            
            # 分页查询
            offset = (page - 1) * page_size
            users = await query.offset(offset).limit(page_size).order_by('-created_at').prefetch_related('roles', 'dept')
            
            # 转换为字典格式
            user_list = []
            for user in users:
                # 获取用户角色
                roles = await user.roles.all()
                role_list = [{'id': role.id, 'role_name': role.role_name} for role in roles]
                
                # 获取部门信息
                dept_info = None
                if user.dept:
                    dept_info = {
                        'id': user.dept.id,
                        'dept_name': user.dept.dept_name
                    }
                
                user_dict = {
                    'id': user.id,
                    'username': user.username,
                    'nick_name': user.nick_name,
                    'email': user.email,
                    'phone_number': user.phone_number,
                    'sex': user.sex,
                    'avatar': user.avatar,
                    'user_type': user.user_type,
                    'status': user.status,
                    'remark': user.remark,
                    'login_ip': user.login_ip,
                    'login_date': user.login_date.isoformat() if user.login_date else None,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'updated_at': user.updated_at.isoformat() if user.updated_at else None,
                    'roles': role_list,
                    'dept': dept_info,
                    'is_superuser': user.is_superuser,
                    'is_active': user.is_active
                }
                user_list.append(user_dict)
            
            return {
                'items': user_list,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
        
        except Exception as e:
            logger.error(f"获取用户列表失败: error={e}")
            return {'items': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}
    
    async def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Optional[User]:
        """更新用户"""
        try:
            user = await User.get_or_none(id=user_id)
            if not user:
                logger.warning(f"用户不存在: id={user_id}")
                return None
            
            logger.info(f"更新用户: {user.username} (ID: {user_id})")
            
            async with in_db_transaction():
                # 检查用户名唯一性
                if 'username' in user_data and user_data['username'] != user.username:
                    existing_user = await User.get_or_none(username=user_data['username'])
                    if existing_user:
                        raise ValueError(f"用户名 '{user_data['username']}' 已存在")
                
                # 检查邮箱唯一性
                if 'email' in user_data and user_data['email'] != user.email:
                    existing_email = await User.get_or_none(email=user_data['email'])
                    if existing_email:
                        raise ValueError(f"邮箱 '{user_data['email']}' 已存在")
                
                # 更新用户基本信息
                update_fields = ['username', 'nick_name', 'email', 'phone_number', 'sex', 
                               'avatar', 'user_type', 'status', 'remark', 'dept_id']
                
                updated = False
                for field in update_fields:
                    if field in user_data:
                        old_value = getattr(user, field)
                        new_value = user_data[field]
                        if old_value != new_value:
                            setattr(user, field, new_value)
                            updated = True
                
                # 处理密码更新
                if 'password' in user_data and user_data['password']:
                    user.password = get_password_hash(user_data['password'])
                    updated = True
                
                if updated:
                    user.updated_at = datetime.now()
                    await user.save()
                
                # 更新角色分配
                if 'role_ids' in user_data:
                    await self._assign_roles_to_user(user, user_data['role_ids'])
                
                # 清理用户权限缓存
                await permission_cache_manager.clear_user_permissions(user_id)
                
                logger.info(f"用户更新成功: {user.username} (ID: {user_id})")
                return user
        
        except IntegrityError as e:
            logger.error(f"更新用户失败，数据完整性错误: {e}")
            raise ValueError("用户数据违反唯一性约束")
        except Exception as e:
            logger.error(f"更新用户失败: id={user_id}, error={e}")
            raise
    
    async def delete_user(self, user_id: int) -> bool:
        """删除用户（软删除）"""
        try:
            user = await User.get_or_none(id=user_id)
            if not user:
                logger.warning(f"用户不存在: id={user_id}")
                return False
            
            # 防止删除超级用户
            if user.is_superuser:
                raise ValueError("不允许删除超级用户")
            
            logger.info(f"删除用户: {user.username} (ID: {user_id})")
            
            async with in_db_transaction():
                # 软删除
                user.del_flag = '1'
                user.updated_at = datetime.now()
                await user.save()
                
                # 清理角色关联
                await user.roles.clear()
                
                # 清理权限缓存
                await permission_cache_manager.clear_user_permissions(user_id)
                
                logger.info(f"用户删除成功: {user.username} (ID: {user_id})")
                return True
        
        except Exception as e:
            logger.error(f"删除用户失败: id={user_id}, error={e}")
            raise
    
    async def update_user_status(self, user_id: int, status: str) -> bool:
        """更新用户状态"""
        try:
            user = await User.get_or_none(id=user_id)
            if not user:
                logger.warning(f"用户不存在: id={user_id}")
                return False
            
            if status not in ['0', '1']:
                raise ValueError("状态值必须为 '0'（启用）或 '1'（禁用）")
            
            # 防止禁用超级用户
            if user.is_superuser and status == '1':
                raise ValueError("不允许禁用超级用户")
            
            logger.info(f"更新用户状态: {user.username} -> {status}")
            
            user.status = status
            user.updated_at = datetime.now()
            await user.save()
            
            # 清理权限缓存
            await permission_cache_manager.clear_user_permissions(user_id)
            
            logger.info(f"用户状态更新成功: {user.username} (ID: {user_id})")
            return True
        
        except Exception as e:
            logger.error(f"更新用户状态失败: id={user_id}, error={e}")
            raise
    
    async def reset_user_password(self, user_id: int, new_password: Optional[str] = None) -> bool:
        """重置用户密码"""
        try:
            user = await User.get_or_none(id=user_id)
            if not user:
                logger.warning(f"用户不存在: id={user_id}")
                return False
            
            # 防止重置超级用户密码
            if user.is_superuser:
                raise ValueError("不允许重置超级用户密码")
            
            password = new_password or self.default_password
            logger.info(f"重置用户密码: {user.username}")
            
            user.password = get_password_hash(password)
            user.updated_at = datetime.now()
            await user.save()
            
            logger.info(f"用户密码重置成功: {user.username} (ID: {user_id})")
            return True
        
        except Exception as e:
            logger.error(f"重置用户密码失败: id={user_id}, error={e}")
            raise
    
    async def change_user_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改用户密码"""
        try:
            user = await User.get_or_none(id=user_id)
            if not user:
                logger.warning(f"用户不存在: id={user_id}")
                return False
            
            # 验证旧密码
            if not verify_password(old_password, user.password):
                raise ValueError("旧密码不正确")
            
            logger.info(f"修改用户密码: {user.username}")
            
            user.password = get_password_hash(new_password)
            user.updated_at = datetime.now()
            await user.save()
            
            logger.info(f"用户密码修改成功: {user.username} (ID: {user_id})")
            return True
        
        except Exception as e:
            logger.error(f"修改用户密码失败: id={user_id}, error={e}")
            raise
    
    async def get_user_roles(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的角色列表"""
        try:
            user = await User.get_or_none(id=user_id).prefetch_related('roles')
            if not user:
                return []
            
            roles = await user.roles.filter(del_flag='0', status='0').order_by('role_sort', 'id')
            
            role_list = []
            for role in roles:
                role_dict = {
                    'id': role.id,
                    'role_name': role.role_name,
                    'role_key': role.role_key,
                    'role_sort': role.role_sort,
                    'data_scope': role.data_scope,
                    'status': role.status,
                    'remark': role.remark
                }
                role_list.append(role_dict)
            
            return role_list
        
        except Exception as e:
            logger.error(f"获取用户角色失败: user_id={user_id}, error={e}")
            return []
    
    async def assign_roles_to_user(self, user_id: int, role_ids: List[int]) -> bool:
        """为用户分配角色"""
        try:
            user = await User.get_or_none(id=user_id)
            if not user:
                logger.warning(f"用户不存在: id={user_id}")
                return False
            
            logger.info(f"为用户分配角色: {user.username}, role_ids={role_ids}")
            
            await self._assign_roles_to_user(user, role_ids)
            
            # 清理权限缓存
            await permission_cache_manager.clear_user_permissions(user_id)
            
            logger.info(f"角色分配成功: user_id={user_id}, role_count={len(role_ids)}")
            return True
        
        except Exception as e:
            logger.error(f"分配角色失败: user_id={user_id}, error={e}")
            raise
    
    async def update_user_login_info(self, user_id: int, login_ip: str) -> bool:
        """更新用户登录信息"""
        try:
            user = await User.get_or_none(id=user_id)
            if not user:
                return False
            
            user.login_ip = login_ip
            user.login_date = datetime.now()
            await user.save()
            
            logger.debug(f"更新用户登录信息: user_id={user_id}, ip={login_ip}")
            return True
        
        except Exception as e:
            logger.error(f"更新用户登录信息失败: user_id={user_id}, error={e}")
            return False
    
    async def batch_update_user_status(self, user_ids: List[int], status: str) -> int:
        """批量更新用户状态"""
        try:
            if status not in ['0', '1']:
                raise ValueError("状态值必须为 '0'（启用）或 '1'（禁用）")
            
            # 过滤掉超级用户
            if status == '1':  # 禁用操作
                superusers = await User.filter(id__in=user_ids, user_type='01').values_list('id', flat=True)
                if superusers:
                    user_ids = [uid for uid in user_ids if uid not in superusers]
                    logger.warning(f"跳过超级用户: {superusers}")
            
            logger.info(f"批量更新用户状态: user_ids={user_ids}, status={status}")
            
            updated_count = await User.filter(id__in=user_ids, del_flag='0').update(
                status=status,
                updated_at=datetime.now()
            )
            
            # 清理权限缓存
            for user_id in user_ids:
                await permission_cache_manager.clear_user_permissions(user_id)
            
            logger.info(f"批量更新用户状态成功: updated_count={updated_count}")
            return updated_count
        
        except Exception as e:
            logger.error(f"批量更新用户状态失败: error={e}")
            raise
    
    async def batch_reset_user_password(self, user_ids: List[int]) -> int:
        """批量重置用户密码"""
        try:
            # 过滤掉超级用户
            superusers = await User.filter(id__in=user_ids, user_type='01').values_list('id', flat=True)
            if superusers:
                user_ids = [uid for uid in user_ids if uid not in superusers]
                logger.warning(f"跳过超级用户: {superusers}")
            
            logger.info(f"批量重置用户密码: user_ids={user_ids}")
            
            hashed_password = get_password_hash(self.default_password)
            updated_count = await User.filter(id__in=user_ids, del_flag='0').update(
                password=hashed_password,
                updated_at=datetime.now()
            )
            
            logger.info(f"批量重置用户密码成功: updated_count={updated_count}")
            return updated_count
        
        except Exception as e:
            logger.error(f"批量重置用户密码失败: error={e}")
            raise
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """获取用户统计信息"""
        try:
            total_users = await User.filter(del_flag='0').count()
            active_users = await User.filter(del_flag='0', status='0').count()
            inactive_users = await User.filter(del_flag='0', status='1').count()
            superusers = await User.filter(del_flag='0', user_type='01').count()
            
            # 按用户类型统计
            user_type_stats = {}
            user_types = ['00', '01']  # 普通用户、超级用户
            for user_type in user_types:
                count = await User.filter(del_flag='0', user_type=user_type).count()
                user_type_stats[user_type] = count
            
            # 最近登录统计
            from datetime import timedelta
            recent_date = datetime.now() - timedelta(days=7)
            recent_login_users = await User.filter(
                del_flag='0', 
                login_date__gte=recent_date
            ).count()
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'inactive_users': inactive_users,
                'superusers': superusers,
                'user_type_stats': user_type_stats,
                'recent_login_users': recent_login_users,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"获取用户统计信息失败: error={e}")
            return {}
    
    async def _assign_roles_to_user(self, user: User, role_ids: List[int]) -> None:
        """内部方法：为用户分配角色"""
        try:
            # 清除现有角色关联
            await user.roles.clear()
            
            if role_ids:
                # 验证角色存在性和状态
                roles = await Role.filter(id__in=role_ids, del_flag='0', status='0')
                valid_role_ids = {role.id for role in roles}
                invalid_role_ids = set(role_ids) - valid_role_ids
                
                if invalid_role_ids:
                    logger.warning(f"无效的角色ID: {invalid_role_ids}")
                
                # 添加新的角色关联
                for role in roles:
                    await user.roles.add(role)
                
                logger.debug(f"为用户分配角色: user_id={user.id}, valid_roles={len(roles)}")
        
        except Exception as e:
            logger.error(f"分配角色失败: user_id={user.id}, error={e}")
            raise


# 全局用户管理服务实例
user_management_service = UserManagementService()


# 便捷函数
async def create_user(user_data: Dict[str, Any]) -> User:
    """创建用户"""
    return await user_management_service.create_user(user_data)


async def get_user(user_id: int) -> Optional[User]:
    """获取用户详情"""
    return await user_management_service.get_user(user_id)


async def get_users(**filters) -> Dict[str, Any]:
    """获取用户列表"""
    return await user_management_service.get_users(**filters)


async def update_user(user_id: int, user_data: Dict[str, Any]) -> Optional[User]:
    """更新用户"""
    return await user_management_service.update_user(user_id, user_data)


async def delete_user(user_id: int) -> bool:
    """删除用户"""
    return await user_management_service.delete_user(user_id)


if __name__ == "__main__":
    # 测试用户管理服务
    import asyncio
    
    async def test_user_service():
        service = UserManagementService()
        
        # 模拟用户数据
        user_data = {
            'username': 'test_user',
            'nick_name': '测试用户',
            'email': 'test@example.com',
            'phone_number': '13800138000',
            'password': 'test123456',
            'role_ids': [1, 2]
        }
        
        print("用户管理服务测试")
        print(f"模拟用户数据: {user_data}")
        
        # 测试获取用户统计
        # stats = await service.get_user_statistics()
        # print(f"用户统计: {stats}")
        
        print("用户管理服务测试完成")
    
    asyncio.run(test_user_service())