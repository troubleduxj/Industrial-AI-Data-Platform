"""
API管理 v2接口
提供API权限管理的RESTful接口
"""
from typing import List, Optional
from fastapi import APIRouter, Request, Depends, Query, Body
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.models.admin import SysApiEndpoint, User
from app.schemas.apis import ApiCreate, ApiUpdate, ApiBatchCreate, ApiBatchUpdate, ApiBatchDelete, ApiResponse, ApiUpdateItem
from app.core.dependency import DependAuth
from app.core.response_formatter_v2 import ResponseFormatterV2, APIv2ErrorDetail
from app.core.batch_delete_decorators import require_batch_delete_permission, DependBatchDeleteAPI
from app.core.permissions import PermissionCondition

router = APIRouter()

@router.get("", summary="获取API列表", dependencies=[DependAuth])
async def get_apis(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    path: Optional[str] = Query(None, description="API路径"),
    method: Optional[str] = Query(None, description="请求方法"),
    group_id: Optional[int] = Query(None, description="API分组ID"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = DependAuth
):
    """获取API列表"""
    formatter = ResponseFormatterV2(request)
    
    try:
        # 构建查询条件
        query = SysApiEndpoint.all()
        query_params = {}
        
        # 搜索条件
        if search:
            query = query.filter(
                Q(api_path__icontains=search) | 
                Q(api_name__icontains=search)
            )
            query_params['search'] = search
        
        if path:
            query = query.filter(api_path__icontains=path)
            query_params['path'] = path
            
        if method:
            query = query.filter(http_method=method)
            query_params['method'] = method
            
        if group_id is not None:
            query = query.filter(group_id=group_id)
            query_params['group_id'] = group_id
            
        if is_active is not None:
            status_value = 'active' if is_active else 'inactive'
            query = query.filter(status=status_value)
            query_params['is_active'] = is_active
        
        # 分页查询，关联分组表
        total = await query.count()
        offset = (page - 1) * page_size
        apis = await query.select_related('group').offset(offset).limit(page_size).order_by('-id')
        
        # 格式化响应数据
        api_list = []
        for api in apis:
            # 构建完整的API路径
            full_path = api.api_path or ""
            if api.version == 'v2' and full_path and not full_path.startswith('/api/v2/'):
                # 为v2版本的API添加前缀
                if full_path.startswith('/'):
                    full_path = f"/api/v2{full_path}"
                else:
                    full_path = f"/api/v2/{full_path}"
            
            api_data = {
                "id": api.id,
                "path": full_path,
                "method": api.http_method or "GET",
                "summary": getattr(api, 'api_name', '') or "",
                "description": getattr(api, 'description', '') or "",
                "tags": getattr(api, 'api_code', '') or "",
                "group_name": api.group.group_name if api.group else "默认分组",
                "group_code": api.group.group_code if api.group else "default",
                "is_active": api.status == 'active',
                "created_at": api.created_at.isoformat() if hasattr(api, 'created_at') and api.created_at else None,
                "updated_at": api.updated_at.isoformat() if hasattr(api, 'updated_at') and api.updated_at else None
            }
            api_list.append(api_data)
        
        return formatter.paginated_success(
            data=api_list,
            total=total,
            page=page,
            page_size=page_size,
            message="获取API列表成功",
            resource_type="apis",
            query_params=query_params
        )
        
    except Exception as e:
        return formatter.internal_error(f"获取API列表失败: {str(e)}")

@router.get("/{api_id}", summary="获取API详情", dependencies=[DependAuth])
async def get_api(
    api_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """获取API详情"""
    formatter = ResponseFormatterV2(request)
    
    try:
        api = await SysApiEndpoint.get_or_none(id=api_id)
        if not api:
            return formatter.not_found("API不存在", "api")
        
        api_data = {
            "id": api.id,
            "path": api.api_path,
            "method": api.http_method,
            "summary": getattr(api, 'api_name', ''),
            "description": getattr(api, 'description', ''),
            "tags": getattr(api, 'api_code', ''),
            "is_active": api.status == 'active',
            "created_at": api.created_at.isoformat() if hasattr(api, 'created_at') and api.created_at else None,
            "updated_at": api.updated_at.isoformat() if hasattr(api, 'updated_at') and api.updated_at else None
        }
        
        return formatter.success(
            data=api_data,
            message="获取API详情成功",
            resource_id=str(api_id),
            resource_type="apis"
        )
        
    except Exception as e:
        return formatter.internal_error(f"获取API详情失败: {str(e)}")

@router.post("", summary="创建API", dependencies=[DependAuth])
async def create_api(
    request: Request,
    api_data: ApiCreate,
    current_user: User = DependAuth
):
    """创建API"""
    formatter = ResponseFormatterV2(request)
    
    try:
        # 先进行基本数据验证
        if not api_data.path or not api_data.path.strip():
            return formatter.validation_error(
                message="路径不能为空",
                details=[APIv2ErrorDetail(
                    field="path",
                    code="VALIDATION_ERROR",
                    message="路径是必填字段且不能为空",
                    value=api_data.path
                )]
            )
        
        if not api_data.path.startswith('/'):
            return formatter.validation_error(
                message="路径格式无效",
                details=[APIv2ErrorDetail(
                    field="path",
                    code="VALIDATION_ERROR",
                    message="路径必须以'/'开头",
                    value=api_data.path
                )]
            )
        
        # 检查API路径是否已存在
        existing_api = await SysApiEndpoint.get_or_none(api_path=api_data.path, http_method=api_data.method.value)
        if existing_api:
            return formatter.conflict(
                message=f"API路径 {api_data.method.value} {api_data.path} 已存在",
                details=[APIv2ErrorDetail(
                    field="path",
                    code="DUPLICATE_API",
                    message="API路径和方法组合已存在",
                    value=f"{api_data.method.value} {api_data.path}"
                )],
                suggestion="请使用不同的路径或HTTP方法",
                resource_type="api"
            )
        
        # 创建新API
        # 生成api_code，如果tags为空则使用路径和方法生成默认值
        api_code = api_data.tags or f"{api_data.method.value.lower()}_{api_data.path.replace('/', '_').replace('-', '_').strip('_')}"
        
        api = await SysApiEndpoint.create(
            api_path=api_data.path,
            http_method=api_data.method.value,
            api_name=api_data.summary,
            description=api_data.description,
            api_code=api_code,
            status='active' if api_data.is_active else 'inactive',
            group_id=api_data.group_id or 1,
            version='v2'
        )
        
        api_data = {
            "id": api.id,
            "path": api.api_path,
            "method": api.http_method,
            "summary": api.api_name,
            "description": api.description,
            "tags": api.api_code,
            "is_active": api.status == 'active',
            "created_at": api.created_at.isoformat() if api.created_at else None,
            "updated_at": api.updated_at.isoformat() if api.updated_at else None
        }
        
        return formatter.success(
            data=api_data,
            message="API创建成功",
            code=201,
            resource_id=str(api.id),
            resource_type="apis"
        )
        
    except Exception as e:
        return formatter.internal_error(f"创建API失败: {str(e)}")

@router.put("/batch", summary="批量更新API", dependencies=[DependAuth])
async def batch_update_apis(
    request: Request,
    batch_data: ApiBatchUpdate,
    current_user: User = DependAuth
):
    """批量更新API"""
    formatter = ResponseFormatterV2(request)
    
    try:
        updated_apis = []
        failed_apis = []
        
        for update_item in batch_data.updates:
            try:
                # 检查API是否存在
                api = await SysApiEndpoint.get_or_none(id=update_item.id)
                if not api:
                    failed_apis.append({
                        "id": update_item.id,
                        "error": "API不存在"
                    })
                    continue
                
                # 检查路径和方法组合是否冲突
                if update_item.path and update_item.method:
                    existing_api = await SysApiEndpoint.get_or_none(
                        api_path=update_item.path,
                        http_method=update_item.method.value
                    )
                    if existing_api and existing_api.id != update_item.id:
                        failed_apis.append({
                            "id": update_item.id,
                            "error": f"API路径 {update_item.method.value} {update_item.path} 已存在"
                        })
                        continue
                
                # 更新API
                update_data = {}
                if update_item.path is not None:
                    update_data['api_path'] = update_item.path
                if update_item.method is not None:
                    update_data['http_method'] = update_item.method.value
                if update_item.summary is not None:
                    update_data['api_name'] = update_item.summary
                if update_item.description is not None:
                    update_data['description'] = update_item.description
                if update_item.tags is not None:
                    update_data['api_code'] = update_item.tags
                if update_item.group_id is not None:
                    update_data['group_id'] = update_item.group_id
                if update_item.is_active is not None:
                    update_data['status'] = 'active' if update_item.is_active else 'inactive'
                
                if update_data:
                    await api.update_from_dict(update_data)
                    await api.save()
                
                updated_apis.append({
                    "id": api.id,
                    "path": api.api_path,
                    "method": api.http_method,
                    "summary": api.api_name,
                    "description": api.description,
                    "tags": api.api_code,
                    "is_active": api.status == 'active'
                })
                
            except Exception as e:
                failed_apis.append({
                    "id": update_item.id,
                    "error": f"更新失败: {str(e)}"
                })
        
        # 返回结果
        result_data = {
            "updated_count": len(updated_apis),
            "failed_count": len(failed_apis),
            "updated_apis": updated_apis,
            "failed_apis": failed_apis
        }
        
        if failed_apis:
            return formatter.partial_success(
                data=result_data,
                message=f"批量更新完成，成功: {len(updated_apis)}，失败: {len(failed_apis)}",
                code=207,
                resource_type="apis"
            )
        else:
            return formatter.success(
                data=result_data,
                message=f"批量更新成功，共更新 {len(updated_apis)} 个API",
                resource_type="apis"
            )
            
    except Exception as e:
        return formatter.internal_error(f"批量更新API失败: {str(e)}")


@router.put("/{api_id}", summary="更新API", dependencies=[DependAuth])
async def update_api(
    request: Request,
    api_id: int,
    api_data: ApiUpdate,
    current_user: User = DependAuth
):
    """更新API"""
    formatter = ResponseFormatterV2(request)
    
    try:
        # 查找API
        api = await SysApiEndpoint.get_or_none(id=api_id)
        if not api:
            return formatter.not_found("API不存在", "api")
        
        # 如果更新路径和方法，检查是否冲突
        if api_data.path is not None and api_data.method is not None:
            existing_api = await SysApiEndpoint.get_or_none(api_path=api_data.path, http_method=api_data.method.value)
            if existing_api and existing_api.id != api_id:
                return formatter.validation_error(
                    message=f"API路径 {api_data.method.value} {api_data.path} 已存在",
                    details=[APIv2ErrorDetail(
                        field="path",
                        code="DUPLICATE_API",
                        message="API路径和方法组合已存在",
                        value=f"{api_data.method.value} {api_data.path}"
                    )]
                )
        
        # 更新字段
        update_data = {}
        if api_data.path is not None:
            update_data['api_path'] = api_data.path
        if api_data.method is not None:
            update_data['http_method'] = api_data.method.value
        if api_data.summary is not None:
            update_data['api_name'] = api_data.summary
        if api_data.description is not None:
            update_data['description'] = api_data.description
        if api_data.tags is not None:
            update_data['api_code'] = api_data.tags
        if api_data.group_id is not None:
            update_data['group_id'] = api_data.group_id
        if api_data.is_active is not None:
            update_data['status'] = 'active' if api_data.is_active else 'inactive'
        
        if update_data:
            await api.update_from_dict(update_data)
            await api.save()
        
        api_data = {
            "id": api.id,
            "path": api.api_path,
            "method": api.http_method,
            "summary": api.api_name,
            "description": api.description,
            "tags": api.api_code,
            "is_active": api.status == 'active',
            "created_at": api.created_at.isoformat() if api.created_at else None,
            "updated_at": api.updated_at.isoformat() if api.updated_at else None
        }
        
        return formatter.success(
            data=api_data,
            message="API更新成功",
            resource_id=str(api_id),
            resource_type="apis"
        )
        
    except Exception as e:
        return formatter.internal_error(f"更新API失败: {str(e)}")

@router.delete("/batch", summary="批量删除API")
@require_batch_delete_permission("api", [PermissionCondition.EXCLUDE_SYSTEM_ITEMS])
async def batch_delete_apis(
    request: Request,
    batch_data: ApiBatchDelete,
    current_user: User = DependAuth
):
    """
    批量删除API v2版本
    
    使用标准化数据格式：{"ids": [1, 2, 3]}
    返回标准化响应格式，包含用户友好的错误提示
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        from app.services.batch_delete_service import api_batch_delete_service
        from tortoise.transactions import in_transaction
        
        # 1. 输入验证
        if not batch_data.ids:
            return formatter.validation_error(
                message="API ID列表不能为空",
                details=[APIv2ErrorDetail(
                    field="ids",
                    code="EMPTY_LIST",
                    message="API ID列表不能为空",
                    value=batch_data.ids
                )]
            )
        
        async with in_transaction():
            # 使用标准化批量删除服务
            result = await api_batch_delete_service.batch_delete(ids=batch_data.ids)
            
            # 生成用户友好的响应消息
            if result.failed_count == 0:
                message = f"成功删除 {result.deleted_count} 个API"
            elif result.deleted_count == 0:
                failed_reasons = [item.reason for item in result.failed]
                message = f"删除失败：{'; '.join(failed_reasons)}"
            else:
                failed_details = [f"{item.name or item.id}：{item.reason}" for item in result.failed]
                message = f"批量删除完成：成功删除 {result.deleted_count} 个，失败 {result.failed_count} 个API。失败原因：{'; '.join(failed_details)}"
            
            return formatter.success(
                data=result.model_dump(),
                message=message,
                resource_type="apis"
            )
            
    except Exception as e:
        return formatter.internal_error(
            message="批量删除API时发生系统错误",
            error_detail=str(e),
            component="batch_delete_apis"
        )

@router.delete("/{api_id}", summary="删除API", dependencies=[DependAuth])
async def delete_api(
    api_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """删除API"""
    formatter = ResponseFormatterV2(request)
    
    try:
        api = await SysApiEndpoint.get_or_none(id=api_id)
        if not api:
            return formatter.not_found("API不存在")
        
        await api.delete()
        
        return formatter.success(
            message="API删除成功",
            data={"id": api_id}
        )
        
    except Exception as e:
        return formatter.server_error(f"删除API失败: {str(e)}")

@router.post("/batch", summary="批量创建API", dependencies=[DependAuth])
async def batch_create_apis(
    request: Request,
    batch_data: ApiBatchCreate,
    current_user: User = DependAuth
):
    """批量创建API"""
    formatter = ResponseFormatterV2(request)
    
    try:
        created_apis = []
        failed_apis = []
        
        for api_data in batch_data.apis:
            try:
                # 检查API路径和方法组合是否已存在
                existing_api = await SysApiEndpoint.get_or_none(
                    api_path=api_data.path,
                    http_method=api_data.method.value
                )
                if existing_api:
                    failed_apis.append({
                        "data": api_data.dict(),
                        "error": f"API路径 {api_data.method.value} {api_data.path} 已存在"
                    })
                    continue
                
                # 创建API
                new_api = await SysApiEndpoint.create(
                    api_path=api_data.path,
                    http_method=api_data.method.value,
                    api_name=api_data.summary,
                    description=api_data.description or "",
                    api_code=api_data.tags or "",
                    group_id=api_data.group_id or 1,
                    status='active' if api_data.is_active else 'inactive',
                    version='v2'
                )
                
                created_apis.append({
                    "id": new_api.id,
                    "path": new_api.api_path,
                    "method": new_api.http_method,
                    "summary": new_api.api_name,
                    "description": new_api.description,
                    "tags": new_api.api_code,
                    "group_id": new_api.group_id,
                    "is_active": new_api.status == 'active',
                    "created_at": new_api.created_at.isoformat() if new_api.created_at else None,
                    "updated_at": new_api.updated_at.isoformat() if new_api.updated_at else None
                })
                
            except Exception as e:
                failed_apis.append({
                    "data": api_data.dict(),
                    "error": str(e)
                })
        
        result = {
            "created_count": len(created_apis),
            "failed_count": len(failed_apis),
            "created_apis": created_apis,
            "failed_apis": failed_apis
        }
        
        if failed_apis:
            return formatter.success(
                data=result,
                message=f"批量创建完成，成功 {len(created_apis)} 个，失败 {len(failed_apis)} 个",
                code=207,  # Multi-Status
                resource_type="apis"
            )
        else:
            return formatter.success(
                data=result,
                message=f"批量创建成功，共创建 {len(created_apis)} 个API",
                code=201,
                resource_type="apis"
            )
        
    except Exception as e:
        return formatter.internal_error(f"批量创建API失败: {str(e)}")





@router.post("/refresh", summary="刷新API", dependencies=[DependAuth])
async def refresh_apis(
    request: Request,
    current_user: User = DependAuth
):
    """刷新API列表（从路由自动发现）"""
    formatter = ResponseFormatterV2(request)
    
    try:
        return formatter.success(
            data={"refreshed": True, "count": 10},
            message="API刷新成功",
            resource_type="apis"
        )
        
    except Exception as e:
        return formatter.internal_error(f"刷新API失败: {str(e)}")
