#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的认证依赖模块
提供基于JWT的认证和权限验证依赖
"""

from typing import Optional
from fastapi import Depends, Header, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.auth_service import auth_service
from app.models.admin import User
from app.core.unified_logger import get_logger

logger = get_logger(__name__)

# HTTP Bearer 认证方案
security = HTTPBearer(auto_error=False)


class AuthenticationError(HTTPException):
    """认证错误异常"""
    
    def __init__(self, detail: str = "认证失败", status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(status_code=status_code, detail=detail)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Header(None, alias="X-Token")
) -> User:
    """
    获取当前认证用户
    
    支持多种令牌传递方式：
    1. Authorization: Bearer <token>
    2. X-Token: <token>
    3. token: <token> (Header)
    
    Args:
        request: FastAPI请求对象
        credentials: HTTP Bearer认证凭据
        authorization: Authorization头
        token: X-Token头或token头
        
    Returns:
        User: 当前认证用户
        
    Raises:
        AuthenticationError: 认证失败时抛出
    """
    # 提取令牌
    auth_token = None
    
    # 优先级：Bearer token > X-Token > token header > Authorization header
    if credentials and credentials.credentials:
        auth_token = credentials.credentials
    elif token:
        auth_token = token
    elif authorization:
        if authorization.startswith("Bearer "):
            auth_token = authorization[7:]
        else:
            auth_token = authorization
    
    # 开发模式支持
    if auth_token == "dev":
        logger.warning("使用开发模式令牌")
        user = await User.filter().first()
        if user:
            return user
    
    if not auth_token:
        logger.warning(f"缺少认证令牌: {request.url.path}")
        raise AuthenticationError("缺少访问令牌")
    
    # 使用认证服务验证令牌
    user = await auth_service.get_user_from_token(auth_token)
    if not user:
        logger.warning(f"令牌验证失败: {request.url.path}")
        raise AuthenticationError("无效或已过期的访问令牌")
    
    # 将用户信息添加到请求状态中
    request.state.user = user
    request.state.user_id = user.id
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    获取当前活跃用户
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 当前活跃用户
        
    Raises:
        AuthenticationError: 用户未激活时抛出
    """
    if not current_user.is_active:
        logger.warning(f"用户账户已被禁用: {current_user.username}")
        raise AuthenticationError("用户账户已被禁用")
    
    return current_user


async def get_current_superuser(current_user: User = Depends(get_current_active_user)) -> User:
    """
    获取当前超级用户
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 当前超级用户
        
    Raises:
        AuthenticationError: 用户不是超级用户时抛出
    """
    if not current_user.is_superuser:
        logger.warning(f"用户不是超级管理员: {current_user.username}")
        raise AuthenticationError("需要超级管理员权限", status.HTTP_403_FORBIDDEN)
    
    return current_user


class OptionalAuth:
    """可选认证依赖"""
    
    async def __call__(
        self,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        authorization: Optional[str] = Header(None),
        token: Optional[str] = Header(None, alias="X-Token")
    ) -> Optional[User]:
        """
        可选的用户认证
        
        如果提供了令牌则进行认证，否则返回None
        """
        try:
            return await get_current_user(request, credentials, authorization, token)
        except AuthenticationError:
            return None


# 依赖实例
optional_auth = OptionalAuth()

# 兼容性别名
DependAuth = Depends(get_current_active_user)
DependSuperUser = Depends(get_current_superuser)
DependOptionalAuth = Depends(optional_auth)


async def get_current_user_optional(request: Request) -> Optional[User]:
    """
    可选的用户认证函数
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        Optional[User]: 当前用户或None
    """
    return await optional_auth(request)


def create_permission_dependency(required_permissions: list):
    """
    创建权限验证依赖
    
    Args:
        required_permissions: 需要的权限列表
        
    Returns:
        依赖函数
    """
    async def permission_checker(
        request: Request,
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        # 超级用户直接通过
        if current_user.is_superuser:
            return current_user
        
        # TODO: 实现具体的权限检查逻辑
        # 这里可以集成权限服务进行权限验证
        
        return current_user
    
    return Depends(permission_checker)


def require_permissions(*permissions):
    """
    权限验证装饰器
    
    Args:
        *permissions: 需要的权限列表
        
    Returns:
        权限验证依赖
    """
    return create_permission_dependency(list(permissions))