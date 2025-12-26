"""
API文档相关接口
提供API变更日志和文档信息，支持Swagger文档自动生成和同步
"""
import os
from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from typing import Optional, Dict, Any
from app.schemas.base import success_response
from app.core.api_changelog import changelog_manager, ChangeType
from app.services.swagger_documentation_service import get_swagger_service
from app.services.documentation_sync_service import get_sync_service

router = APIRouter()

@router.get("/changelog", summary="获取API变更日志", description="获取API变更历史记录")
async def get_api_changelog(
    version: str = Query(None, description="指定版本，不指定则返回所有版本"),
    format: str = Query("json", description="返回格式：json, markdown, html")
):
    """
    获取API变更日志
    
    支持的格式：
    - json: JSON格式的变更记录
    - markdown: Markdown格式的变更日志
    - html: HTML格式的变更日志
    """
    if format == "markdown":
        content = changelog_manager.generate_markdown_changelog()
        return PlainTextResponse(content=content, media_type="text/markdown")
    
    elif format == "html":
        content = changelog_manager.generate_html_changelog()
        return HTMLResponse(content=content)
    
    else:  # json格式
        if version:
            changes = changelog_manager.get_changes_by_version(version)
        else:
            changes = changelog_manager.load_changelog()
        
        return success_response(
            data={
                "changes": changes,
                "total": len(changes),
                "available_formats": ["json", "markdown", "html"]
            },
            message="API变更日志获取成功"
        )

@router.get("/changelog/breaking", summary="获取破坏性变更", description="获取破坏性变更记录")
async def get_breaking_changes(
    from_version: str = Query(None, description="从指定版本开始的破坏性变更")
):
    """
    获取破坏性变更记录
    
    这些变更可能需要客户端代码修改才能正常工作
    """
    breaking_changes = changelog_manager.get_breaking_changes(from_version)
    
    return success_response(
        data={
            "breaking_changes": breaking_changes,
            "total": len(breaking_changes),
            "migration_required": len(breaking_changes) > 0
        },
        message="破坏性变更记录获取成功"
    )

@router.get("/versions", summary="获取API版本信息", description="获取支持的API版本列表")
async def get_api_versions():
    """
    获取API版本信息
    
    返回当前支持的所有API版本及其特性
    """
    versions_info = {
        "v1": {
            "status": "deprecated",
            "description": "传统API版本，保持向后兼容",
            "features": [
                "基础功能",
                "传统响应格式",
                "兼容旧客户端"
            ],
            "deprecation_date": "2025-01-06",
            "sunset_date": "2025-12-31"
        },
        "v2": {
            "status": "current",
            "description": "当前推荐使用的API版本",
            "features": [
                "标准化响应格式",
                "增强错误处理",
                "版本控制支持",
                "详细的API文档",
                "变更日志跟踪"
            ],
            "release_date": "2025-01-06"
        }
    }
    
    return success_response(
        data={
            "current_version": "v2",
            "default_version": "v1",
            "supported_versions": list(versions_info.keys()),
            "versions": versions_info,
            "version_selection": {
                "url_path": "在URL路径中指定版本，如 /api/v2/users",
                "header": "在请求头中添加 API-Version: v2"
            }
        },
        message="API版本信息获取成功"
    )

@router.get("/schema", summary="获取API Schema", description="获取OpenAPI规范文档")
async def get_api_schema():
    """
    获取API Schema信息
    
    提供OpenAPI规范文档的访问链接和基本信息
    """
    return success_response(
        data={
            "openapi_url": "/openapi.json",
            "docs_url": "/docs",
            "redoc_url": "/redoc",
            "postman_collection": "/api/v2/docs/postman",
            "insomnia_collection": "/api/v2/docs/insomnia",
            "schema_format": "OpenAPI 3.0",
            "last_updated": "2025-01-06T00:00:00"
        },
        message="API Schema信息获取成功"
    )

@router.get("/examples", summary="获取API使用示例", description="获取常用API的使用示例")
async def get_api_examples():
    """
    获取API使用示例
    
    提供常用API接口的请求和响应示例
    """
    examples = {
        "authentication": {
            "description": "用户认证示例",
            "request": {
                "method": "POST",
                "url": "/api/v2/auth/login",
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": {
                    "username": "admin",
                    "password": "password123"
                }
            },
            "response": {
                "success": True,
                "code": 200,
                "message": "登录成功",
                "data": {
                    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "user": {
                        "id": 1,
                        "username": "admin",
                        "email": "admin@example.com"
                    }
                },
                "timestamp": "2025-01-06T00:00:00"
            }
        },
        "user_list": {
            "description": "获取用户列表示例",
            "request": {
                "method": "GET",
                "url": "/api/v2/users?page=1&page_size=20",
                "headers": {
                    "Authorization": "Bearer <token>",
                    "API-Version": "v2"
                }
            },
            "response": {
                "success": True,
                "code": 200,
                "message": "Users retrieved successfully",
                "data": [
                    {
                        "id": 1,
                        "username": "admin",
                        "email": "admin@example.com",
                        "is_active": True
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 20,
                "total_pages": 1,
                "timestamp": "2025-01-06T00:00:00"
            }
        },
        "error_handling": {
            "description": "错误处理示例",
            "request": {
                "method": "GET",
                "url": "/api/v2/users/999",
                "headers": {
                    "Authorization": "Bearer <token>"
                }
            },
            "response": {
                "success": False,
                "code": 404,
                "message": "User with id 999 not found",
                "details": {
                    "error_code": "RESOURCE_NOT_FOUND",
                    "path": "/api/v2/users/999",
                    "method": "GET"
                },
                "timestamp": "2025-01-06T00:00:00"
            }
        }
    }
    
    return success_response(
        data={
            "examples": examples,
            "total_examples": len(examples),
            "categories": ["authentication", "user_management", "error_handling"]
        },
        message="API使用示例获取成功"
    )


# ============================================================================
# Swagger文档自动生成和同步相关接口
# ============================================================================

@router.get("/swagger/generate", summary="生成Swagger文档", description="手动触发Swagger文档生成")
async def generate_swagger_docs(
    background_tasks: BackgroundTasks,
    module: Optional[str] = Query(None, description="指定模块名称，不指定则生成全部文档")
):
    """
    生成Swagger文档
    
    支持生成完整文档或指定模块文档
    """
    swagger_service = get_swagger_service()
    if not swagger_service:
        raise HTTPException(status_code=503, detail="Swagger文档服务未初始化")
    
    try:
        if module:
            # 生成指定模块文档
            module_docs = await swagger_service.generate_module_documentation(module)
            return success_response(
                data={
                    "module": module,
                    "paths_count": len(module_docs.get("paths", {})),
                    "generated_at": module_docs.get("info", {}).get("generated_at"),
                    "download_url": f"/api/v2/docs/swagger/download?module={module}"
                },
                message=f"{module}模块文档生成成功"
            )
        else:
            # 生成完整文档
            full_docs = await swagger_service.generate_v2_documentation()
            
            # 后台保存文档文件
            background_tasks.add_task(swagger_service.save_documentation_files)
            
            return success_response(
                data={
                    "paths_count": len(full_docs.get("paths", {})),
                    "tags_count": len(full_docs.get("tags", [])),
                    "components_count": len(full_docs.get("components", {}).get("schemas", {})),
                    "download_url": "/api/v2/docs/swagger/download"
                },
                message="完整API文档生成成功"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档生成失败: {str(e)}")


@router.get("/swagger/download", summary="下载Swagger文档", description="下载生成的Swagger文档文件")
async def download_swagger_docs(
    module: Optional[str] = Query(None, description="指定模块名称")
):
    """
    下载Swagger文档
    
    返回JSON格式的OpenAPI文档
    """
    swagger_service = get_swagger_service()
    if not swagger_service:
        raise HTTPException(status_code=503, detail="Swagger文档服务未初始化")
    
    try:
        if module:
            docs = await swagger_service.generate_module_documentation(module)
            filename = f"api-v2-{module.lower().replace(' ', '-')}.json"
        else:
            docs = await swagger_service.generate_v2_documentation()
            filename = "api-v2-complete.json"
        
        return JSONResponse(
            content=docs,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/json"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档下载失败: {str(e)}")


@router.get("/swagger/modules", summary="获取可用模块列表", description="获取支持文档生成的模块列表")
async def get_swagger_modules():
    """
    获取可用模块列表
    
    返回所有支持独立文档生成的模块
    """
    modules = [
        {
            "name": "用户管理",
            "description": "用户信息管理相关接口",
            "tag": "用户管理 v2",
            "base_path": "/api/v2/users"
        },
        {
            "name": "角色管理",
            "description": "角色和权限管理相关接口",
            "tag": "角色管理 v2",
            "base_path": "/api/v2/roles"
        },
        {
            "name": "菜单管理",
            "description": "系统菜单管理相关接口",
            "tag": "菜单管理 v2",
            "base_path": "/api/v2/menus"
        },
        {
            "name": "部门管理",
            "description": "组织架构管理相关接口",
            "tag": "部门管理 v2",
            "base_path": "/api/v2/departments"
        },
        {
            "name": "API管理",
            "description": "API接口管理相关接口",
            "tag": "API管理 v2",
            "base_path": "/api/v2/apis"
        },
        {
            "name": "API分组管理",
            "description": "API分组管理相关接口",
            "tag": "API分组管理 v2",
            "base_path": "/api/v2/api-groups"
        },
        {
            "name": "字典类型管理",
            "description": "数据字典类型管理相关接口",
            "tag": "字典类型管理 v2",
            "base_path": "/api/v2/dict-types"
        },
        {
            "name": "字典数据管理",
            "description": "数据字典管理相关接口",
            "tag": "字典数据管理 v2",
            "base_path": "/api/v2/dict-data"
        },
        {
            "name": "系统参数管理",
            "description": "系统配置参数管理相关接口",
            "tag": "系统参数管理 v2",
            "base_path": "/api/v2/system-params"
        },
        {
            "name": "审计日志",
            "description": "系统操作审计日志相关接口",
            "tag": "审计日志 v2",
            "base_path": "/api/v2/audit-logs"
        }
    ]
    
    return success_response(
        data={
            "modules": modules,
            "total_modules": len(modules)
        },
        message="模块列表获取成功"
    )


@router.post("/sync", summary="同步文档", description="手动触发文档同步")
async def sync_documentation(
    background_tasks: BackgroundTasks,
    force: bool = Query(False, description="强制同步，即使没有变更")
):
    """
    同步文档
    
    检测API变更并更新文档版本
    """
    sync_service = get_sync_service()
    if not sync_service:
        raise HTTPException(status_code=503, detail="文档同步服务未初始化")
    
    try:
        # 后台执行同步
        background_tasks.add_task(sync_service.sync_documentation, force)
        
        return success_response(
            data={
                "sync_started": True,
                "force": force,
                "status_url": "/api/v2/docs/sync/status"
            },
            message="文档同步已启动"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档同步失败: {str(e)}")


@router.get("/sync/status", summary="获取同步状态", description="获取文档同步状态和历史")
async def get_sync_status():
    """
    获取同步状态
    
    返回最近的同步记录和当前状态
    """
    sync_service = get_sync_service()
    if not sync_service:
        raise HTTPException(status_code=503, detail="文档同步服务未初始化")
    
    try:
        config = sync_service.load_sync_config()
        versions_data = sync_service.load_versions()
        
        current_version_info = None
        if versions_data["versions"]:
            current_version_info = versions_data["versions"][-1]
        
        return success_response(
            data={
                "auto_sync_enabled": config.get("auto_sync", True),
                "last_sync": config.get("last_sync"),
                "current_version": versions_data.get("current_version"),
                "current_version_info": current_version_info,
                "total_versions": len(versions_data["versions"]),
                "sync_config": {
                    "sync_interval_minutes": config.get("sync_interval_minutes", 60),
                    "track_changes": config.get("track_changes", True),
                    "generate_changelog": config.get("generate_changelog", True),
                    "backup_versions": config.get("backup_versions", 10)
                }
            },
            message="同步状态获取成功"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取同步状态失败: {str(e)}")


@router.get("/versions", summary="获取文档版本列表", description="获取所有文档版本历史")
async def get_documentation_versions(
    limit: int = Query(10, ge=1, le=50, description="返回版本数量限制")
):
    """
    获取文档版本列表
    
    返回文档版本历史记录
    """
    sync_service = get_sync_service()
    if not sync_service:
        raise HTTPException(status_code=503, detail="文档同步服务未初始化")
    
    try:
        versions_data = sync_service.load_versions()
        recent_versions = versions_data["versions"][-limit:] if versions_data["versions"] else []
        
        return success_response(
            data={
                "versions": list(reversed(recent_versions)),  # 最新版本在前
                "current_version": versions_data.get("current_version"),
                "total_versions": len(versions_data["versions"]),
                "showing": len(recent_versions)
            },
            message="版本列表获取成功"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取版本列表失败: {str(e)}")


@router.get("/versions/{version}", summary="获取指定版本信息", description="获取指定版本的详细信息")
async def get_version_info(version: str):
    """
    获取指定版本信息
    
    返回版本的详细信息和变更记录
    """
    sync_service = get_sync_service()
    if not sync_service:
        raise HTTPException(status_code=503, detail="文档同步服务未初始化")
    
    try:
        version_info = await sync_service.get_version_info(version)
        
        if "error" in version_info:
            raise HTTPException(status_code=404, detail=version_info["error"])
        
        return success_response(
            data=version_info,
            message=f"版本 {version} 信息获取成功"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取版本信息失败: {str(e)}")


@router.get("/changes", summary="获取变更记录", description="获取API变更历史记录")
async def get_documentation_changes(
    since_version: Optional[str] = Query(None, description="获取指定版本以来的变更"),
    limit: int = Query(50, ge=1, le=200, description="返回变更数量限制")
):
    """
    获取变更记录
    
    返回API变更历史，支持按版本过滤
    """
    sync_service = get_sync_service()
    if not sync_service:
        raise HTTPException(status_code=503, detail="文档同步服务未初始化")
    
    try:
        if since_version:
            changes = await sync_service.get_changes_since_version(since_version)
        else:
            changes_data = sync_service.load_changes()
            changes = changes_data.get("changes", [])
        
        # 限制返回数量
        recent_changes = changes[-limit:] if changes else []
        
        # 按变更类型统计
        stats = {
            "added": len([c for c in recent_changes if c.get("change_type") == "added"]),
            "modified": len([c for c in recent_changes if c.get("change_type") == "modified"]),
            "removed": len([c for c in recent_changes if c.get("change_type") == "removed"])
        }
        
        return success_response(
            data={
                "changes": list(reversed(recent_changes)),  # 最新变更在前
                "total_changes": len(changes),
                "showing": len(recent_changes),
                "since_version": since_version,
                "statistics": stats
            },
            message="变更记录获取成功"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取变更记录失败: {str(e)}")


@router.get("/changelog", summary="获取变更日志", description="获取Markdown格式的变更日志")
async def get_changelog_markdown():
    """
    获取变更日志
    
    返回Markdown格式的完整变更日志
    """
    try:
        changelog_path = "docs/api-v2/CHANGELOG.md"
        
        if not os.path.exists(changelog_path):
            # 如果变更日志不存在，尝试生成
            sync_service = get_sync_service()
            if sync_service:
                await sync_service._generate_changelog()
        
        if os.path.exists(changelog_path):
            with open(changelog_path, "r", encoding="utf-8") as f:
                changelog_content = f.read()
            
            return PlainTextResponse(
                content=changelog_content,
                media_type="text/markdown",
                headers={
                    "Content-Disposition": "inline; filename=CHANGELOG.md"
                }
            )
        else:
            return PlainTextResponse(
                content="# API变更日志\n\n暂无变更记录。",
                media_type="text/markdown"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取变更日志失败: {str(e)}")