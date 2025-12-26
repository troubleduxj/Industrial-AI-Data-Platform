#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API权限配置管理接口
提供权限配置的CRUD操作、热更新、版本控制等功能
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field

from app.services.api_permission_config import (
    api_permission_config_manager,
    ApiEndpointConfig,
    PermissionRule,
    ConfigVersion
)
from app.core.auth_dependencies import get_current_user
from app.models.admin import User
from app.core.unified_logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/permission-config", tags=["权限配置管理"])


# Pydantic模型定义
class ApiEndpointRequest(BaseModel):
    """API端点请求模型"""
    api_code: str = Field(..., description="API编码")
    api_name: str = Field(..., description="API名称")
    api_path: str = Field(..., description="API路径")
    http_method: str = Field(..., description="HTTP方法")
    description: Optional[str] = Field(None, description="描述")
    version: str = Field("v2", description="版本")
    is_public: bool = Field(False, description="是否公开")
    is_deprecated: bool = Field(False, description="是否废弃")
    rate_limit: Optional[int] = Field(None, description="速率限制")
    permission_code: Optional[str] = Field(None, description="权限编码")
    group_code: Optional[str] = Field(None, description="分组编码")
    tags: Optional[str] = Field(None, description="标签")


class ApiEndpointUpdateRequest(BaseModel):
    """API端点更新请求模型"""
    api_name: Optional[str] = Field(None, description="API名称")
    api_path: Optional[str] = Field(None, description="API路径")
    http_method: Optional[str] = Field(None, description="HTTP方法")
    description: Optional[str] = Field(None, description="描述")
    version: Optional[str] = Field(None, description="版本")
    is_public: Optional[bool] = Field(None, description="是否公开")
    is_deprecated: Optional[bool] = Field(None, description="是否废弃")
    rate_limit: Optional[int] = Field(None, description="速率限制")
    permission_code: Optional[str] = Field(None, description="权限编码")
    group_code: Optional[str] = Field(None, description="分组编码")
    tags: Optional[str] = Field(None, description="标签")


class PermissionRuleRequest(BaseModel):
    """权限规则请求模型"""
    rule_id: str = Field(..., description="规则ID")
    name: str = Field(..., description="规则名称")
    description: str = Field(..., description="规则描述")
    api_patterns: List[str] = Field(..., description="API路径模式列表")
    conditions: Dict[str, Any] = Field(..., description="权限条件")
    priority: int = Field(0, description="优先级")
    enabled: bool = Field(True, description="是否启用")


class PermissionRuleUpdateRequest(BaseModel):
    """权限规则更新请求模型"""
    name: Optional[str] = Field(None, description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    api_patterns: Optional[List[str]] = Field(None, description="API路径模式列表")
    conditions: Optional[Dict[str, Any]] = Field(None, description="权限条件")
    priority: Optional[int] = Field(None, description="优先级")
    enabled: Optional[bool] = Field(None, description="是否启用")


class ConfigVersionRequest(BaseModel):
    """配置版本请求模型"""
    description: str = Field(..., description="版本描述")


class ApiResponse(BaseModel):
    """API响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")
    code: int = Field(200, description="状态码")


# API端点管理接口
@router.get("/endpoints", summary="获取所有API端点配置")
async def get_all_endpoints(
    current_user: User = Depends(get_current_user)
) -> ApiResponse:
    """获取所有API端点配置"""
    try:
        endpoints = api_permission_config_manager.get_all_api_endpoints()
        endpoints_data = [endpoint.to_dict() for endpoint in endpoints.values()]
        
        return ApiResponse(
            success=True,
            message="获取API端点配置成功",
            data={
                "endpoints": endpoints_data,
                "total": len(endpoints_data)
            }
        )
    except Exception as e:
        logger.error(f"获取API端点配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/endpoints/{api_code}", summary="获取指定API端点配置")
async def get_endpoint(
    api_code: str,
    current_user: User = Depends(get_current_user)
) -> ApiResponse:
    """获取指定API端点配置"""
    try:
        endpoint = api_permission_config_manager.get_api_endpoint(api_code)
        if not endpoint:
            raise HTTPException(status_code=404, detail=f"API端点不存在: {api_code}")
        
        return ApiResponse(
            success=True,
            message="获取API端点配置成功",
            data=endpoint.to_dict()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取API端点配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/endpoints", summary="添加API端点配置")
async def add_endpoint(
    request: ApiEndpointRequest,
    current_user: User = Depends(get_current_user)
) -> ApiResponse:
    """添加API端点配置"""
    try:
        # 检查权限（只有超级用户可以添加）
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="需要超级用户权限")
        
        # 创建端点配置
        endpoint_config = ApiEndpointConfig(**request.dict())
        
        # 添加配置
        success = await api_permission_config_manager.add_api_endpoint(endpoint_config)
        
        if success:
            return ApiResponse(
                success=True,
                message="添加API端点配置成功",
                data=endpoint_config.to_dict()
            )
        else:
            raise HTTPException(status_code=400, detail="添加API端点配置失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加API端点配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/endpoints/{api_code}", summary="更新API端点配置")
async def update_endpoint(
    api_code: str,
    request: ApiEndpointUpdateRequest,
    current_user: User = Depends(get_current_user)
) -> ApiResponse:
    """更新API端点配置"""
    try:
        # 检查权限（只有超级用户可以更新）
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="需要超级用户权限")
        
        # 过滤None值
        updates = {k: v for k, v in request.dict().items() if v is not None}
        
        if not updates:
            raise HTTPException(status_code=400, detail="没有提供更新数据")
        
        # 更新配置
        success = await api_permission_config_manager.update_api_endpoint(api_code, updates)
        
        if success:
            updated_endpoint = api_permission_config_manager.get_api_endpoint(api_code)
            return ApiResponse(
                success=True,
                message="更新API端点配置成功",
                data=updated_endpoint.to_dict() if updated_endpoint else None
            )
        else:
            raise HTTPException(status_code=400, detail="更新API端点配置失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新API端点配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/endpoints/{api_code}", summary="删除API端点配置")
async def delete_endpoint(
    api_code: str,
    current_user: User = Depends(get_current_user)
) -> ApiResponse:
    """删除API端点配置"""
    try:
        # 检查权限（只有超级用户可以删除）
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="需要超级用户权限")
        
        # 删除配置
        success = await api_permission_config_manager.remove_api_endpoint(api_code)
        
        if success:
            return ApiResponse(
                success=True,
                message="删除API端点配置成功"
            )
        else:
            raise HTTPException(status_code=400, detail="删除API端点配置失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除API端点配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 权限规则管理接口
@router.get("/rules", summary="获取所有权限规则")
async def get_all_rules(
    current_user: User = Depends(get_current_user)
) -> ApiResponse:
    """获取所有权限规则"""
    try:
        rules = api_permission_config_manager.get_all_permission_rules()
        rules_data = [rule.to_dict() for rule in rules.values()]
        
        return ApiResponse(
            success=True,
            message="获取权限规则成功",
            data={
                "rules": rules_data,
                "total": len(rules_data)
            }
        )
    except Exception as e:
        logger.error(f"获取权限规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/{rule_id}", summary="获取指定权限规则")
async def get_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user)
) -> ApiResponse:
    """获取指定权限规则"""
    try:
        rule = api_permission_config_manager.get_permission_rule(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail=f"权限规则不存在: {rule_id}")
        
        return ApiResponse(
            success=True,
            message="获取权限规则成功",
            data=rule.to_dict()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取权限规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules", summary="添加权限规则")
async def add_rule(
    request: PermissionRuleRequest,
    current_user: User = Depends(get_current_user)
) -> ApiResponse:
    """添加权限规则"""
    try:
        # 检查权限（只有超级用户可以添加）
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="需要超级用户权限")
        
        # 创建权限规则
        rule = PermissionRule(**request.dict())
        
        # 添加规则
        success = await api_permission_config_manager.add_permission_rule(rule)
        
        if success:
            return ApiResponse(
                success=True,
                message="添加权限规则成功",
                data=rule.to_dict()
            )
        else:
            raise HTTPException(status_code=400, detail="添加权限规则失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加权限规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rules/{rule_id}", summary="更新权限规则")
async def update_rule(
    rule_id: str,
    request: PermissionRuleUpdateRequest,
    current_user: User = Depends(get_current_user)
) -> ApiResponse:
    """更新权限规则"""
    try:
        # 检查权限（只有超级用户可以更新）
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="需要超级用户权限")
        
        # 过滤None值
        updates = {k: v for k, v in request.dict().items() if v is not None}
        
        if not updates:
            raise HTTPException(status_code=400, detail="没有提供更新数据")
        
        # 更新规则
        success = await api_permission_config_manager.update_permission_rule(rule_id, updates)
        
        if success:
            updated_rule = api_permission_config_manager.get_permission_rule(rule_id)
            return ApiResponse(
                success=True,
                message="更新权限规则成功",
                data=updated_rule.to_dict() if updated_rule else None
            )
        else:
            raise HTTPException(status_code=400, detail="更新权限规则失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新权限规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}", summary="删除权限规则")
async def delete_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user)
) -> ApiResponse:
    """删除权限规则"""
    try:
        # 检查权限（只有超级用户可以删除）
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="需要超级用户权限")
        
        # 删除规则
        success = await api_permission_config_manager.remove_permission_rule(rule_id)
        
        if success:
            return ApiResponse(
                success=True,
                message="删除权限规则成功"
            )
        else:
            raise HTTPException(status_code=400, detail="删除权限规则失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除权限规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 配置管理接口
@router.post("/discover", summary="自动发现API端点")
async def discover_endpoints(
    current_user: User = Depends(get_current_user)
) -> ApiResponse:
    """自动发现API端点"""
    try:
        # 检查权限（只有超级用户可以执行）
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="需要超级用户权限")
        
        # 执行发现
        result = await api_permission_config_manager.discover_api_endpoints()
        
        return ApiResponse(
            success=True,
            message="API端点发现完成",
            data=result
        )
    except Exception as e:
        logger.error(f"API端点发现失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload", summary="热重载配置")
async def hot_reload_config(
    current_user: User = Depends(get_current_user)
) -> ApiResponse:
    """热重载配置"""
    try:
        # 检查权限（只有超级用户可以执行）
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="需要超级用户权限")
        
        # 执行热重载
        result = await api_permission_config_manager.hot_reload_config()
        
        return ApiResponse(
            success=result.get("status") == "success",
            message=result.get("message", "热重载完成"),
            data=result
        )
    except Exception as e:
        logger.error(f"配置热重载失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", summary="验证配置")
async def validate_config(
    current_user: User = Depends(get_current_user)
) -> ApiResponse:
    """验证配置"""
    try:
        # 执行验证
        result = await api_permission_config_manager.validate_config()
        
        return ApiResponse(
            success=result.get("valid", False),
            message="配置验证完成",
            data=result
        )
    except Exception as e:
        logger.error(f"配置验证失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 版本控制接口
@router.get("/versions", summary="获取配置版本列表")
async def get_versions(
    current_user: User = Depends(get_current_user)
) -> ApiResponse:
    """获取配置版本列表"""
    try:
        versions = api_permission_config_manager.get_config_versions()
        versions_data = [version.to_dict() for version in versions]
        
        return ApiResponse(
            success=True,
            message="获取配置版本成功",
            data={
                "versions": versions_data,
                "current_version": api_permission_config_manager.get_current_version(),
                "total": len(versions_data)
            }
        )
    except Exception as e:
        logger.error(f"获取配置版本失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/versions", summary="创建配置版本")
async def create_version(
    request: ConfigVersionRequest,
    current_user: User = Depends(get_current_user)
) -> ApiResponse:
    """创建配置版本"""
    try:
        # 检查权限（只有超级用户可以创建版本）
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="需要超级用户权限")
        
        # 创建版本
        version = await api_permission_config_manager.create_config_version(
            description=request.description,
            created_by=current_user.username
        )
        
        if version:
            return ApiResponse(
                success=True,
                message="创建配置版本成功",
                data={"version": version}
            )
        else:
            raise HTTPException(status_code=400, detail="创建配置版本失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建配置版本失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/versions/{version}/rollback", summary="回滚到指定版本")
async def rollback_version(
    version: str,
    current_user: User = Depends(get_current_user)
) -> ApiResponse:
    """回滚到指定版本"""
    try:
        # 检查权限（只有超级用户可以回滚）
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="需要超级用户权限")
        
        # 执行回滚
        success = await api_permission_config_manager.rollback_to_version(version)
        
        if success:
            return ApiResponse(
                success=True,
                message=f"回滚到版本 {version} 成功"
            )
        else:
            raise HTTPException(status_code=400, detail="版本回滚失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"版本回滚失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 统计信息接口
@router.get("/stats", summary="获取配置统计信息")
async def get_stats(
    current_user: User = Depends(get_current_user)
) -> ApiResponse:
    """获取配置统计信息"""
    try:
        stats = api_permission_config_manager.get_stats()
        
        return ApiResponse(
            success=True,
            message="获取统计信息成功",
            data=stats
        )
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))