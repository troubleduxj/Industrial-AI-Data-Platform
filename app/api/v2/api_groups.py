"""API分组管理 v2接口
提供API分组管理的RESTful接口
"""
from typing import List, Optional
from fastapi import APIRouter, Request, Depends, Query, Body
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.models.admin import SysApiGroup, SysApiEndpoint, User
from app.core.dependency import DependAuth
from app.core.response_formatter_v2 import ResponseFormatterV2, APIv2ErrorDetail
from app.schemas.api_groups import ApiGroupCreate, ApiGroupUpdate, ApiGroupPatch
from app.core.batch_delete_decorators import require_batch_delete_permission
from app.schemas.base import BatchDeleteRequest

router = APIRouter()

@router.get("", summary="获取API分组列表", dependencies=[DependAuth])
async def get_api_groups(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    all: bool = Query(False, description="获取所有分组（不分页）"),
    current_user: User = DependAuth
):
    """获取API分组列表，支持分页和全量获取"""
    formatter = ResponseFormatterV2(request)
    
    try:
        # 构建查询条件
        query = SysApiGroup.all()
        query_params = {}
        
        # 搜索条件
        if search:
            query = query.filter(
                Q(group_name__icontains=search) | 
                Q(group_code__icontains=search) |
                Q(description__icontains=search)
            )
            query_params['search'] = search
        
        # 如果请求所有数据（不分页）
        if all:
            groups = await query.order_by('group_name')
            group_list = []
            for group in groups:
                group_data = {
                    "id": group.id,
                    "group_name": group.group_name,
                    "group_code": group.group_code,
                    "description": group.description or ""
                }
                group_list.append(group_data)
            
            return formatter.success(
                data=group_list,
                message="获取所有API分组成功",
                resource_type="api_groups"
            )
        
        # 分页查询
        total = await query.count()
        offset = (page - 1) * page_size
        groups = await query.offset(offset).limit(page_size).order_by('-id')
        
        # 格式化响应数据
        group_list = []
        for group in groups:
            # 统计该分组下的API数量
            api_count = await SysApiEndpoint.filter(group_id=group.id).count()
            
            group_data = {
                "id": group.id,
                "group_name": group.group_name,
                "group_code": group.group_code,
                "description": group.description or "",
                "api_count": api_count,
                "created_at": group.created_at.isoformat() if hasattr(group, 'created_at') and group.created_at else None,
                "updated_at": group.updated_at.isoformat() if hasattr(group, 'updated_at') and group.updated_at else None
            }
            group_list.append(group_data)
        
        return formatter.paginated_success(
            data=group_list,
            total=total,
            page=page,
            page_size=page_size,
            message="获取API分组列表成功",
            resource_type="api_groups",
            query_params=query_params
        )
        
    except Exception as e:
        return formatter.internal_error(f"获取API分组列表失败: {str(e)}")


@router.get("/all", summary="获取所有API分组", dependencies=[DependAuth])
async def get_all_api_groups(
    request: Request,
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = DependAuth
):
    """获取所有API分组（不分页）"""
    formatter = ResponseFormatterV2(request)
    
    try:
        # 构建查询条件
        query = SysApiGroup.all()
        
        # 搜索条件
        if search:
            query = query.filter(
                Q(group_name__icontains=search) | 
                Q(group_code__icontains=search) |
                Q(description__icontains=search)
            )
        
        groups = await query.order_by('group_name')
        group_list = []
        for group in groups:
            group_data = {
                "id": group.id,
                "group_name": group.group_name,
                "group_code": group.group_code,
                "description": group.description or ""
            }
            group_list.append(group_data)
        
        return formatter.success(
            data=group_list,
            message="获取所有API分组成功",
            resource_type="api_groups"
        )
        
    except Exception as e:
        return formatter.internal_error(f"获取所有API分组失败: {str(e)}")


@router.get("/{group_id}", summary="获取API分组详情", dependencies=[DependAuth])
async def get_api_group(
    group_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """获取API分组详情"""
    formatter = ResponseFormatterV2(request)
    
    try:
        group = await SysApiGroup.get_or_none(id=group_id)
        if not group:
            return formatter.not_found("API分组不存在", "api_group")
        
        # 统计该分组下的API数量
        api_count = await SysApiEndpoint.filter(group_id=group.id).count()
        
        group_data = {
            "id": group.id,
            "group_name": group.group_name,
            "group_code": group.group_code,
            "description": group.description or "",
            "api_count": api_count,
            "created_at": group.created_at.isoformat() if hasattr(group, 'created_at') and group.created_at else None,
            "updated_at": group.updated_at.isoformat() if hasattr(group, 'updated_at') and group.updated_at else None
        }
        
        return formatter.success(
            data=group_data,
            message="获取API分组详情成功",
            resource_id=str(group_id),
            resource_type="api_groups"
        )
        
    except Exception as e:
        return formatter.internal_error(f"获取API分组详情失败: {str(e)}")

@router.post("", summary="创建API分组", dependencies=[DependAuth])
async def create_api_group(
    request: Request,
    group_name: str = Body(..., description="分组名称"),
    group_code: str = Body(..., description="分组代码"),
    description: Optional[str] = Body(None, description="分组描述"),
    current_user: User = DependAuth
):
    """创建API分组"""
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查分组代码是否已存在
        existing_group = await SysApiGroup.get_or_none(group_code=group_code)
        if existing_group:
            return formatter.validation_error(
                message=f"分组代码 {group_code} 已存在",
                details=[APIv2ErrorDetail(
                    field="group_code",
                    code="DUPLICATE_GROUP_CODE",
                    message="分组代码已存在",
                    value=group_code
                )]
            )
        
        # 创建新分组
        group = await SysApiGroup.create(
            group_name=group_name,
            group_code=group_code,
            description=description
        )
        
        group_data = {
            "id": group.id,
            "group_name": group.group_name,
            "group_code": group.group_code,
            "description": group.description or "",
            "api_count": 0,
            "created_at": group.created_at.isoformat() if group.created_at else None,
            "updated_at": group.updated_at.isoformat() if group.updated_at else None
        }
        
        return formatter.success(
            data=group_data,
            message="API分组创建成功",
            code=201,
            resource_id=str(group.id),
            resource_type="api_groups"
        )
        
    except Exception as e:
        return formatter.internal_error(f"创建API分组失败: {str(e)}")

@router.put("/{group_id}", summary="更新API分组", dependencies=[DependAuth])
async def update_api_group(
    request: Request,
    group_id: int,
    group_name: Optional[str] = Body(None, description="分组名称"),
    group_code: Optional[str] = Body(None, description="分组代码"),
    description: Optional[str] = Body(None, description="分组描述"),
    current_user: User = DependAuth
):
    """更新API分组"""
    formatter = ResponseFormatterV2(request)
    
    try:
        # 查找分组
        group = await SysApiGroup.get_or_none(id=group_id)
        if not group:
            return formatter.not_found("API分组不存在", "api_group")
        
        # 如果更新分组代码，检查是否冲突
        if group_code is not None and group_code != group.group_code:
            existing_group = await SysApiGroup.get_or_none(group_code=group_code)
            if existing_group and existing_group.id != group_id:
                return formatter.validation_error(
                    message=f"分组代码 {group_code} 已存在",
                    details=[APIv2ErrorDetail(
                        field="group_code",
                        code="DUPLICATE_GROUP_CODE",
                        message="分组代码已存在",
                        value=group_code
                    )]
                )
        
        # 更新字段
        update_data = {}
        if group_name is not None:
            update_data['group_name'] = group_name
        if group_code is not None:
            update_data['group_code'] = group_code
        if description is not None:
            update_data['description'] = description
        
        if update_data:
            await group.update_from_dict(update_data)
            await group.save()
        
        # 统计该分组下的API数量
        api_count = await SysApiEndpoint.filter(group_id=group.id).count()
        
        group_data = {
            "id": group.id,
            "group_name": group.group_name,
            "group_code": group.group_code,
            "description": group.description or "",
            "api_count": api_count,
            "created_at": group.created_at.isoformat() if group.created_at else None,
            "updated_at": group.updated_at.isoformat() if group.updated_at else None
        }
        
        return formatter.success(
            data=group_data,
            message="API分组更新成功",
            resource_id=str(group_id),
            resource_type="api_groups"
        )
        
    except Exception as e:
        return formatter.internal_error(f"更新API分组失败: {str(e)}")

@router.patch("/{group_id}", summary="部分更新API分组", dependencies=[DependAuth])
async def patch_api_group(
    request: Request,
    group_id: int,
    patch_data: ApiGroupPatch,
    current_user: User = DependAuth
):
    """部分更新API分组（只更新提供的字段）"""
    formatter = ResponseFormatterV2(request)
    
    try:
        # 查找分组
        group = await SysApiGroup.get_or_none(id=group_id)
        if not group:
            return formatter.not_found("API分组不存在", "api_group")
        
        # 检查是否有字段需要更新
        if patch_data.group_name is None and patch_data.group_code is None and patch_data.description is None:
            return formatter.validation_error(
                message="至少需要提供一个要更新的字段",
                details=[APIv2ErrorDetail(
                    field="body",
                    code="NO_UPDATE_FIELDS",
                    message="至少需要提供一个要更新的字段",
                    value=None
                )]
            )
        
        # 如果更新分组代码，检查是否冲突
        if patch_data.group_code is not None and patch_data.group_code != group.group_code:
            existing_group = await SysApiGroup.get_or_none(group_code=patch_data.group_code)
            if existing_group and existing_group.id != group_id:
                return formatter.validation_error(
                    message=f"分组代码 {patch_data.group_code} 已存在",
                    details=[APIv2ErrorDetail(
                        field="group_code",
                        code="DUPLICATE_GROUP_CODE",
                        message="分组代码已存在",
                        value=patch_data.group_code
                    )]
                )
        
        # 更新字段
        if patch_data.group_name is not None:
            group.group_name = patch_data.group_name
        if patch_data.group_code is not None:
            group.group_code = patch_data.group_code
        if patch_data.description is not None:
            group.description = patch_data.description
        
        await group.save()
        
        # 统计该分组下的API数量
        api_count = await SysApiEndpoint.filter(group_id=group.id).count()
        
        group_data = {
            "id": group.id,
            "group_name": group.group_name,
            "group_code": group.group_code,
            "description": group.description or "",
            "api_count": api_count,
            "created_at": group.created_at.isoformat() if group.created_at else None,
            "updated_at": group.updated_at.isoformat() if group.updated_at else None
        }
        
        return formatter.success(
            data=group_data,
            message="API分组部分更新成功",
            resource_id=str(group_id),
            resource_type="api_groups"
        )
        
    except Exception as e:
        return formatter.internal_error(f"部分更新API分组失败: {str(e)}")

@router.delete("/batch", summary="批量删除API分组", dependencies=[DependAuth])
@require_batch_delete_permission("api_group")
async def batch_delete_api_groups(
    request: Request,
    batch_request: BatchDeleteRequest,
    current_user: User = DependAuth
):
    """批量删除API分组 v2版本
    
    使用标准化数据格式：{"ids": [1, 2, 3]}
    返回标准化响应格式，包含用户友好的错误提示
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        from app.services.batch_delete_service import api_group_batch_delete_service
        from tortoise.transactions import in_transaction
        
        group_ids = batch_request.ids
        
        if not group_ids:
            return formatter.validation_error(
                message="API分组ID列表不能为空",
                details=[APIv2ErrorDetail(
                    field="ids",
                    code="EMPTY_LIST",
                    message="API分组ID列表不能为空",
                    value=group_ids
                )]
            )
        
        async with in_transaction():
            # 使用标准化批量删除服务
            result = await api_group_batch_delete_service.batch_delete(ids=group_ids)
            
            # 生成用户友好的响应消息
            if result.failed_count == 0:
                message = f"成功删除 {result.deleted_count} 个API分组"
            elif result.deleted_count == 0:
                failed_reasons = [item.reason for item in result.failed]
                message = f"删除失败：{'; '.join(failed_reasons)}"
            else:
                failed_details = [f"{item.name or item.id}：{item.reason}" for item in result.failed]
                message = f"批量删除完成：成功删除 {result.deleted_count} 个，失败 {result.failed_count} 个API分组。失败原因：{'; '.join(failed_details)}"
            
            return formatter.success(
                data=result.model_dump(),
                message=message,
                resource_type="api_groups"
            )
        
    except Exception as e:
        return formatter.internal_error(f"批量删除API分组失败: {str(e)}")

@router.delete("/{group_id}", summary="删除API分组", dependencies=[DependAuth])
async def delete_api_group(
    group_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """删除API分组"""
    formatter = ResponseFormatterV2(request)
    
    try:
        # 查找分组
        group = await SysApiGroup.get_or_none(id=group_id)
        if not group:
            return formatter.not_found("API分组不存在", "api_group")
        
        # 检查是否有API使用该分组
        api_count = await SysApiEndpoint.filter(group_id=group_id).count()
        if api_count > 0:
            return formatter.validation_error(
                message=f"该分组下还有 {api_count} 个API，无法删除",
                details=[APIv2ErrorDetail(
                    field="group_id",
                    code="GROUP_IN_USE",
                    message="分组下还有API，无法删除",
                    value=str(group_id)
                )]
            )
        
        # 删除分组
        await group.delete()
        
        return formatter.success(
            message="API分组删除成功",
            code=204
        )
        
    except Exception as e:
        return formatter.internal_error(f"删除API分组失败: {str(e)}")

# 子资源操作：分组下的API管理

@router.get("/{group_id}/apis", summary="获取分组下的API列表", dependencies=[DependAuth])
async def get_group_apis(
    request: Request,
    group_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = DependAuth
):
    """获取指定分组下的API列表"""
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查分组是否存在
        group = await SysApiGroup.get_or_none(id=group_id)
        if not group:
            return formatter.not_found("API分组不存在", "api_group")
        
        # 构建查询条件
        query = SysApiEndpoint.filter(group_id=group_id)
        query_params = {"group_id": group_id}
        
        # 搜索条件
        if search:
            query = query.filter(
                Q(api_name__icontains=search) | 
                Q(api_path__icontains=search) |
                Q(description__icontains=search)
            )
            query_params['search'] = search
        
        # 分页查询
        total = await query.count()
        offset = (page - 1) * page_size
        apis = await query.offset(offset).limit(page_size).order_by('-id')
        
        # 格式化响应数据
        api_list = []
        for api in apis:
            api_data = {
                "id": api.id,
                "api_name": api.api_name,
                "api_path": api.api_path,
                "api_method": api.http_method,
                "description": api.description or "",
                "group_id": api.group_id,
                "created_at": api.created_at.isoformat() if hasattr(api, 'created_at') and api.created_at else None,
                "updated_at": api.updated_at.isoformat() if hasattr(api, 'updated_at') and api.updated_at else None
            }
            api_list.append(api_data)
        
        return formatter.paginated_success(
            data=api_list,
            total=total,
            page=page,
            page_size=page_size,
            message=f"获取分组 {group.group_name} 下的API列表成功",
            resource_type="apis",
            query_params=query_params
        )
        
    except Exception as e:
        return formatter.internal_error(f"获取分组API列表失败: {str(e)}")

@router.post("/{group_id}/apis", summary="批量添加API到分组", dependencies=[DependAuth])
async def add_apis_to_group(
    request: Request,
    group_id: int,
    api_ids: List[int] = Body(..., description="API ID列表"),
    current_user: User = DependAuth
):
    """批量添加API到指定分组"""
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查分组是否存在
        group = await SysApiGroup.get_or_none(id=group_id)
        if not group:
            return formatter.not_found("API分组不存在", "api_group")
        
        # 批量更新API的分组
        async with in_transaction():
            updated_count = 0
            not_found_ids = []
            
            for api_id in api_ids:
                api = await SysApiEndpoint.get_or_none(id=api_id)
                if api:
                    api.group_id = group_id
                    await api.save()
                    updated_count += 1
                else:
                    not_found_ids.append(api_id)
        
        result_data = {
            "updated_count": updated_count,
            "total_count": len(api_ids),
            "success_rate": f"{(updated_count/len(api_ids)*100):.1f}%" if api_ids else "0%"
        }
        
        if not_found_ids:
            result_data["not_found_ids"] = not_found_ids
        
        return formatter.success(
            data=result_data,
            message=f"成功添加 {updated_count} 个API到分组 {group.group_name}",
            resource_id=str(group_id),
            resource_type="api_groups"
        )
        
    except Exception as e:
        return formatter.internal_error(f"添加API到分组失败: {str(e)}")

@router.delete("/{group_id}/apis/{api_id}", summary="从分组移除API", dependencies=[DependAuth])
async def remove_api_from_group(
    request: Request,
    group_id: int,
    api_id: int,
    current_user: User = DependAuth
):
    """从指定分组移除单个API"""
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查分组是否存在
        group = await SysApiGroup.get_or_none(id=group_id)
        if not group:
            return formatter.not_found("API分组不存在", "api_group")
        
        # 检查API是否存在且属于该分组
        api = await SysApiEndpoint.get_or_none(id=api_id, group_id=group_id)
        if not api:
            return formatter.not_found("API不存在或不属于该分组", "api")
        
        # 将API的分组设置为None（移除分组关联）
        api.group_id = None
        await api.save()
        
        return formatter.success(
            data={
                "api_id": api_id,
                "api_name": api.api_name,
                "removed_from_group": group.group_name
            },
            message=f"成功从分组 {group.group_name} 移除API {api.api_name}",
            resource_id=str(api_id),
            resource_type="apis"
        )
        
    except Exception as e:
        return formatter.internal_error(f"从分组移除API失败: {str(e)}")