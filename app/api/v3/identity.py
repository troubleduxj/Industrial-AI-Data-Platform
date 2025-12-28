"""
身份集成API

提供身份提供商管理和外部认证端点。

API端点:
- POST   /api/v3/identity/providers          # 创建提供商
- GET    /api/v3/identity/providers          # 获取提供商列表
- GET    /api/v3/identity/providers/{id}     # 获取提供商详情
- PUT    /api/v3/identity/providers/{id}     # 更新提供商
- DELETE /api/v3/identity/providers/{id}     # 删除提供商
- POST   /api/v3/auth/external/{provider}    # 外部认证
- GET    /api/v3/auth/oauth2/callback        # OAuth2回调
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# =====================================================
# 请求/响应模型
# =====================================================

class IdentityProviderCreate(BaseModel):
    """创建身份提供商请求"""
    name: str = Field(..., min_length=1, max_length=50, description="提供商名称")
    type: str = Field(..., description="提供商类型: ldap, oauth2")
    config: Dict[str, Any] = Field(default_factory=dict, description="提供商配置")
    enabled: bool = Field(default=True, description="是否启用")
    priority: int = Field(default=0, description="优先级")
    role_mapping: Dict[str, int] = Field(default_factory=dict, description="组到角色映射")


class IdentityProviderUpdate(BaseModel):
    """更新身份提供商请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="提供商名称")
    config: Optional[Dict[str, Any]] = Field(None, description="提供商配置")
    enabled: Optional[bool] = Field(None, description="是否启用")
    priority: Optional[int] = Field(None, description="优先级")
    role_mapping: Optional[Dict[str, int]] = Field(None, description="组到角色映射")


class IdentityProviderResponse(BaseModel):
    """身份提供商响应"""
    id: int
    name: str
    type: str
    enabled: bool
    priority: int
    role_mapping: Dict[str, int]
    created_at: datetime
    updated_at: datetime


class ExternalAuthRequest(BaseModel):
    """外部认证请求"""
    username: Optional[str] = Field(None, description="用户名（LDAP认证）")
    password: Optional[str] = Field(None, description="密码（LDAP认证）")
    code: Optional[str] = Field(None, description="授权码（OAuth2认证）")
    redirect_uri: Optional[str] = Field(None, description="重定向URI（OAuth2认证）")


class AuthResponse(BaseModel):
    """认证响应"""
    success: bool
    message: str
    user: Optional[Dict[str, Any]] = None
    token: Optional[str] = None
    provider: Optional[str] = None


class OAuth2CallbackResponse(BaseModel):
    """OAuth2回调响应"""
    success: bool
    message: str
    user: Optional[Dict[str, Any]] = None
    token: Optional[str] = None


# =====================================================
# 身份提供商管理端点
# =====================================================

@router.post(
    "/identity/providers",
    response_model=IdentityProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建身份提供商",
    description="创建新的身份提供商配置"
)
async def create_identity_provider(
    request: IdentityProviderCreate,
):
    """
    创建身份提供商
    
    支持的提供商类型:
    - ldap: LDAP/Active Directory
    - oauth2: OAuth2/OpenID Connect
    """
    try:
        from app.models.platform_upgrade import IdentityProvider
        
        # 检查名称是否已存在
        existing = await IdentityProvider.filter(name=request.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"身份提供商名称已存在: {request.name}"
            )
        
        # 验证提供商类型
        valid_types = ["ldap", "oauth2"]
        if request.type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的提供商类型: {request.type}，支持的类型: {valid_types}"
            )
        
        # 创建提供商
        provider = await IdentityProvider.create(
            name=request.name,
            type=request.type,
            config=request.config,
            enabled=request.enabled,
            priority=request.priority,
            role_mapping=request.role_mapping,
        )
        
        logger.info(f"创建身份提供商: {request.name} ({request.type})")
        
        return IdentityProviderResponse(
            id=provider.id,
            name=provider.name,
            type=provider.type,
            enabled=provider.enabled,
            priority=provider.priority,
            role_mapping=provider.role_mapping or {},
            created_at=provider.created_at,
            updated_at=provider.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建身份提供商失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建身份提供商失败: {str(e)}"
        )


@router.get(
    "/identity/providers",
    response_model=List[IdentityProviderResponse],
    summary="获取身份提供商列表",
    description="获取所有身份提供商配置"
)
async def list_identity_providers(
    enabled: Optional[bool] = Query(None, description="按启用状态筛选"),
    type: Optional[str] = Query(None, description="按类型筛选"),
):
    """获取身份提供商列表"""
    try:
        from app.models.platform_upgrade import IdentityProvider
        
        query = IdentityProvider.all()
        
        if enabled is not None:
            query = query.filter(enabled=enabled)
        
        if type:
            query = query.filter(type=type)
        
        providers = await query.order_by("priority", "name")
        
        return [
            IdentityProviderResponse(
                id=p.id,
                name=p.name,
                type=p.type,
                enabled=p.enabled,
                priority=p.priority,
                role_mapping=p.role_mapping or {},
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in providers
        ]
        
    except Exception as e:
        logger.error(f"获取身份提供商列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取身份提供商列表失败: {str(e)}"
        )


@router.get(
    "/identity/providers/{provider_id}",
    response_model=IdentityProviderResponse,
    summary="获取身份提供商详情",
    description="获取指定身份提供商的详细配置"
)
async def get_identity_provider(provider_id: int):
    """获取身份提供商详情"""
    try:
        from app.models.platform_upgrade import IdentityProvider
        
        provider = await IdentityProvider.filter(id=provider_id).first()
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"身份提供商不存在: {provider_id}"
            )
        
        return IdentityProviderResponse(
            id=provider.id,
            name=provider.name,
            type=provider.type,
            enabled=provider.enabled,
            priority=provider.priority,
            role_mapping=provider.role_mapping or {},
            created_at=provider.created_at,
            updated_at=provider.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取身份提供商详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取身份提供商详情失败: {str(e)}"
        )


@router.put(
    "/identity/providers/{provider_id}",
    response_model=IdentityProviderResponse,
    summary="更新身份提供商",
    description="更新身份提供商配置"
)
async def update_identity_provider(
    provider_id: int,
    request: IdentityProviderUpdate,
):
    """更新身份提供商"""
    try:
        from app.models.platform_upgrade import IdentityProvider
        
        provider = await IdentityProvider.filter(id=provider_id).first()
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"身份提供商不存在: {provider_id}"
            )
        
        # 更新字段
        update_data = request.model_dump(exclude_unset=True)
        
        if "name" in update_data:
            # 检查名称是否与其他提供商冲突
            existing = await IdentityProvider.filter(
                name=update_data["name"]
            ).exclude(id=provider_id).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"身份提供商名称已存在: {update_data['name']}"
                )
        
        for field, value in update_data.items():
            setattr(provider, field, value)
        
        await provider.save()
        
        logger.info(f"更新身份提供商: {provider.name}")
        
        return IdentityProviderResponse(
            id=provider.id,
            name=provider.name,
            type=provider.type,
            enabled=provider.enabled,
            priority=provider.priority,
            role_mapping=provider.role_mapping or {},
            created_at=provider.created_at,
            updated_at=provider.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新身份提供商失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新身份提供商失败: {str(e)}"
        )


@router.delete(
    "/identity/providers/{provider_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除身份提供商",
    description="删除身份提供商配置"
)
async def delete_identity_provider(provider_id: int):
    """删除身份提供商"""
    try:
        from app.models.platform_upgrade import IdentityProvider
        
        provider = await IdentityProvider.filter(id=provider_id).first()
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"身份提供商不存在: {provider_id}"
            )
        
        provider_name = provider.name
        await provider.delete()
        
        logger.info(f"删除身份提供商: {provider_name}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除身份提供商失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除身份提供商失败: {str(e)}"
        )



# =====================================================
# 外部认证端点
# =====================================================

@router.post(
    "/auth/external/{provider_name}",
    response_model=AuthResponse,
    summary="外部认证",
    description="通过外部身份提供商进行认证"
)
async def external_authenticate(
    provider_name: str,
    request: ExternalAuthRequest,
):
    """
    通过外部身份提供商进行认证
    
    LDAP认证需要提供:
    - username: 用户名
    - password: 密码
    
    OAuth2认证需要提供:
    - code: 授权码
    - redirect_uri: 重定向URI
    """
    try:
        from app.services.auth.identity_manager import identity_manager
        
        # 构建凭据
        credentials = {}
        if request.username:
            credentials["username"] = request.username
        if request.password:
            credentials["password"] = request.password
        if request.code:
            credentials["code"] = request.code
        if request.redirect_uri:
            credentials["redirect_uri"] = request.redirect_uri
        
        # 执行认证
        result = await identity_manager.authenticate(provider_name, credentials)
        
        if not result:
            return AuthResponse(
                success=False,
                message="认证失败，请检查凭据",
            )
        
        # 生成JWT令牌
        token = await _generate_jwt_token(result["local_user"])
        
        return AuthResponse(
            success=True,
            message="认证成功",
            user={
                "id": result["local_user"].id if result["local_user"] else None,
                "username": result["user_info"].username,
                "email": result["user_info"].email,
                "display_name": result["user_info"].display_name,
                "groups": result["user_info"].groups,
                "synced_roles": result["synced_roles"],
            },
            token=token,
            provider=result["provider"],
        )
        
    except Exception as e:
        logger.error(f"外部认证失败: {e}")
        return AuthResponse(
            success=False,
            message=f"认证失败: {str(e)}",
        )


@router.get(
    "/auth/oauth2/callback",
    response_model=OAuth2CallbackResponse,
    summary="OAuth2回调",
    description="处理OAuth2授权回调"
)
async def oauth2_callback(
    code: str = Query(..., description="授权码"),
    state: Optional[str] = Query(None, description="状态参数"),
    provider: str = Query(..., description="提供商名称"),
    redirect_uri: str = Query(..., description="重定向URI"),
):
    """
    处理OAuth2授权回调
    
    当用户在OAuth2提供商完成授权后，会重定向到此端点。
    """
    try:
        from app.services.auth.identity_manager import identity_manager
        
        # 构建凭据
        credentials = {
            "code": code,
            "redirect_uri": redirect_uri,
        }
        
        # 执行认证
        result = await identity_manager.authenticate(provider, credentials)
        
        if not result:
            return OAuth2CallbackResponse(
                success=False,
                message="OAuth2认证失败",
            )
        
        # 生成JWT令牌
        token = await _generate_jwt_token(result["local_user"])
        
        return OAuth2CallbackResponse(
            success=True,
            message="OAuth2认证成功",
            user={
                "id": result["local_user"].id if result["local_user"] else None,
                "username": result["user_info"].username,
                "email": result["user_info"].email,
                "display_name": result["user_info"].display_name,
            },
            token=token,
        )
        
    except Exception as e:
        logger.error(f"OAuth2回调处理失败: {e}")
        return OAuth2CallbackResponse(
            success=False,
            message=f"OAuth2认证失败: {str(e)}",
        )


@router.get(
    "/auth/oauth2/authorize/{provider_name}",
    summary="获取OAuth2授权URL",
    description="获取OAuth2提供商的授权URL"
)
async def get_oauth2_authorize_url(
    provider_name: str,
    redirect_uri: str = Query(..., description="回调重定向URI"),
    state: Optional[str] = Query(None, description="状态参数"),
):
    """
    获取OAuth2授权URL
    
    返回用于重定向用户到OAuth2提供商的授权URL。
    """
    try:
        from app.services.auth.identity_manager import identity_manager
        
        provider = identity_manager.get_provider(provider_name)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"身份提供商不存在: {provider_name}"
            )
        
        # 检查是否为OAuth2提供商
        from app.services.auth.identity_provider import IdentityProviderType
        if provider.provider_type != IdentityProviderType.OAUTH2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"提供商 {provider_name} 不是OAuth2类型"
            )
        
        # 获取授权URL
        from app.services.auth.oauth2_provider import OAuth2Provider
        if isinstance(provider, OAuth2Provider):
            authorize_url = provider.get_authorization_url(redirect_uri, state)
            return {
                "authorize_url": authorize_url,
                "provider": provider_name,
            }
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法获取授权URL"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取OAuth2授权URL失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取授权URL失败: {str(e)}"
        )


# =====================================================
# 辅助函数
# =====================================================

async def _generate_jwt_token(user) -> Optional[str]:
    """
    生成JWT令牌
    
    Args:
        user: 用户对象
        
    Returns:
        str: JWT令牌
    """
    if not user:
        return None
    
    try:
        from app.core.security import create_access_token
        
        token_data = {
            "sub": str(user.id),
            "username": user.username,
        }
        
        return create_access_token(token_data)
        
    except ImportError:
        # 如果安全模块不可用，返回简单令牌
        import hashlib
        import time
        
        token_str = f"{user.id}:{user.username}:{time.time()}"
        return hashlib.sha256(token_str.encode()).hexdigest()
    except Exception as e:
        logger.error(f"生成JWT令牌失败: {e}")
        return None
