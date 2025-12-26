"""
字典类型管理 v2接口 - 修复路由顺序
提供字典类型管理的RESTful接口
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Request, Depends, Query, Body, Path
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.models.system import SysDictType as DictType
from app.models.admin import User
from app.core.dependency import DependAuth
from app.core.response_formatter_v2 import ResponseFormatterV2, APIv2ErrorDetail
from app.core.batch_delete_decorators import require_batch_delete_permission
from app.schemas.system import (
    SysDictTypeCreate,
    SysDictTypeUpdate,
    SysDictTypePatch,
    SysDictTypeBatchCreate,
    SysDictTypeBatchUpdate,
    SysDictTypeBatchDelete,
    SysDictTypeBatchResponse,
    SysDictTypeInDB,
    BatchDeleteResult,
    BatchDeleteFailedItem,
    BatchDeleteSkippedItem
)

router = APIRouter()

# ============================================================================
# 集合操作路由 (Collection Routes) - 必须在单个资源路由之前定义
# ============================================================================

@router.get("", summary="获取字典类型列表")
async def get_dict_types(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    type_name: Optional[str] = Query(None, description="字典类型名称"),
    type_code: Optional[str] = Query(None, description="字典类型编码"),
    current_user: User = DependAuth
):
    """获取字典类型列表"""
    formatter = ResponseFormatterV2(request)
    
    try:
        # 构建查询条件
        query = DictType.all()
        query_params = {}
        
        if search:
            query = query.filter(
                Q(type_name__icontains=search) | 
                Q(type_code__icontains=search) |
                Q(description__icontains=search)
            )
            query_params['search'] = search
        
        if type_name:
            query = query.filter(type_name__icontains=type_name)
            query_params['type_name'] = type_name
            
        if type_code:
            query = query.filter(type_code__icontains=type_code)
            query_params['type_code'] = type_code
        
        # 分页查询
        total = await query.count()
        offset = (page - 1) * page_size
        dict_types = await query.offset(offset).limit(page_size).order_by('-created_at')
        
        # 格式化响应数据
        dict_type_list = []
        for dt in dict_types:
            dict_type_list.append({
                "id": dt.id,
                "type_name": dt.type_name,
                "type_code": dt.type_code,
                "description": dt.description,
                "created_at": dt.created_at.isoformat() if dt.created_at else None,
                "updated_at": dt.updated_at.isoformat() if dt.updated_at else None
            })
        
        return formatter.paginated_success(
            data=dict_type_list,
            total=total,
            page=page,
            page_size=page_size,
            message="获取字典类型列表成功",
            resource_type="dict_types",
            query_params=query_params
        )
        
    except Exception as e:
        return formatter.internal_error(f"获取字典类型列表失败: {str(e)}")

@router.post("", summary="创建字典类型")
async def create_dict_type(
    request: Request,
    dict_type_data: SysDictTypeCreate,
    current_user: User = DependAuth
):
    """创建字典类型"""
    formatter = ResponseFormatterV2(request)
    
    try:
        async with in_transaction("default"):
            # 检查字典类型编码是否已存在
            existing_dict_type = await DictType.get_or_none(type_code=dict_type_data.type_code)
            if existing_dict_type:
                return formatter.validation_error(
                    message="字典类型编码已存在",
                    details=[APIv2ErrorDetail(
                        field="type_code",
                        code="DUPLICATE_CODE",
                        message="字典类型编码已存在",
                        value=dict_type_data.type_code
                    )]
                )
            
            # 创建字典类型
            new_dict_type = await DictType.create(
                type_name=dict_type_data.type_name,
                type_code=dict_type_data.type_code,
                description=dict_type_data.description
            )
            
            dict_type_data = {
                "id": new_dict_type.id,
                "type_name": new_dict_type.type_name,
                "type_code": new_dict_type.type_code,
                "description": new_dict_type.description,
                "created_at": new_dict_type.created_at.isoformat() if new_dict_type.created_at else None,
                "updated_at": new_dict_type.updated_at.isoformat() if new_dict_type.updated_at else None
            }
            
            return formatter.success(
                data=dict_type_data,
                message="字典类型创建成功",
                code=201,
                resource_id=str(new_dict_type.id),
                resource_type="dict_types"
            )
            
    except Exception as e:
        return formatter.internal_error(f"创建字典类型失败: {str(e)}")

# ============================================================================
# 批量操作路由 (Batch Routes) - 必须在单个资源路由之前定义
# ============================================================================

@router.post("/batch", summary="批量创建字典类型")
async def batch_create_dict_types(
    request: Request,
    batch_data: SysDictTypeBatchCreate,
    current_user: User = DependAuth
):
    """批量创建字典类型
    
    支持一次性创建多个字典类型。
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        async with in_transaction("default"):
            created_data = []
            errors = []
            
            for index, dict_type_info in enumerate(batch_data.dict_types):
                try:
                    # 将Pydantic模型转换为字典
                    dict_type_dict = dict_type_info.model_dump()
                    
                    # 验证必需字段
                    required_fields = ['type_name', 'type_code']
                    current_errors = []
                    for field in required_fields:
                        if field not in dict_type_dict or dict_type_dict[field] is None:
                            current_errors.append({
                                "index": index,
                                "field": field,
                                "code": "REQUIRED_FIELD_MISSING",
                                "message": f"缺少必需字段: {field}"
                            })
                    
                    if current_errors:
                        errors.extend(current_errors)
                        continue
                    
                    # 检查字典类型编码是否重复
                    existing_dict_type = await DictType.get_or_none(type_code=dict_type_dict['type_code'])
                    if existing_dict_type:
                        errors.append({
                            "index": index,
                            "field": "type_code",
                            "code": "DUPLICATE_CODE",
                            "message": "字典类型编码已存在",
                            "value": dict_type_dict['type_code']
                        })
                        continue
                    
                    # 创建字典类型
                    current_time = datetime.now()
                    dict_type = await DictType.create(
                        type_name=dict_type_dict['type_name'],
                        type_code=dict_type_dict['type_code'],
                        description=dict_type_dict.get('description', ''),
                        created_at=current_time,
                        updated_at=current_time
                    )
                    
                    created_data.append({
                        "index": index,
                        "id": dict_type.id,
                        "type_name": dict_type.type_name,
                        "type_code": dict_type.type_code,
                        "description": dict_type.description
                    })
                    
                except Exception as e:
                    errors.append({
                        "index": index,
                        "field": "general",
                        "code": "CREATION_ERROR",
                        "message": f"创建失败: {str(e)}"
                    })
            
            result = {
                "created_count": len(created_data),
                "error_count": len(errors),
                "created_data": created_data,
                "errors": errors
            }
            
            if errors:
                return formatter.validation_error(
                    message=f"批量创建完成，成功: {len(created_data)}，失败: {len(errors)}",
                    details=result
                )
            else:
                return formatter.success(
                    data=result,
                    message=f"批量创建成功，共创建 {len(created_data)} 个字典类型"
                )
                
    except Exception as e:
        return formatter.internal_error(f"批量创建字典类型失败: {str(e)}")

@router.put("/batch", summary="批量更新字典类型")
async def batch_update_dict_types(
    request: Request,
    updates: List[Dict[str, Any]] = Body(..., description="更新数据列表，每项必须包含id字段"),
    current_user: User = DependAuth
):
    """批量更新字典类型
    
    支持一次性更新多个字典类型。
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        async with in_transaction("default"):
            updated_data = []
            errors = []
            
            for index, update_info in enumerate(updates):
                try:
                    # 验证必需的id字段
                    if 'id' not in update_info or update_info['id'] is None:
                        errors.append({
                            "index": index,
                            "field": "id",
                            "code": "REQUIRED_FIELD_MISSING",
                            "message": "缺少必需字段: id"
                        })
                        continue
                    
                    dict_type_id = update_info['id']
                    dict_type = await DictType.get_or_none(id=dict_type_id)
                    if not dict_type:
                        errors.append({
                            "index": index,
                            "field": "id",
                            "code": "NOT_FOUND",
                            "message": "字典类型不存在",
                            "value": dict_type_id
                        })
                        continue
                    
                    # 如果更新字典类型编码，检查是否与其他类型冲突
                    if 'type_code' in update_info and update_info['type_code'] != dict_type.type_code:
                        existing_dict_type = await DictType.get_or_none(type_code=update_info['type_code'])
                        if existing_dict_type and existing_dict_type.id != dict_type_id:
                            errors.append({
                                "index": index,
                                "field": "type_code",
                                "code": "DUPLICATE_CODE",
                                "message": "字典类型编码已存在",
                                "value": update_info['type_code']
                            })
                            continue
                    
                    # 构建更新数据
                    update_data = {}
                    if 'type_name' in update_info:
                        update_data['type_name'] = update_info['type_name']
                    if 'type_code' in update_info:
                        update_data['type_code'] = update_info['type_code']
                    if 'description' in update_info:
                        update_data['description'] = update_info['description']
                    
                    # 执行更新
                    if update_data:
                        await dict_type.update_from_dict(update_data)
                        await dict_type.save()
                    
                    updated_data.append({
                        "index": index,
                        "id": dict_type.id,
                        "type_name": dict_type.type_name,
                        "type_code": dict_type.type_code,
                        "description": dict_type.description
                    })
                    
                except Exception as e:
                    errors.append({
                        "index": index,
                        "field": "general",
                        "code": "UPDATE_ERROR",
                        "message": f"更新失败: {str(e)}"
                    })
            
            result = {
                "updated_count": len(updated_data),
                "error_count": len(errors),
                "updated_data": updated_data,
                "errors": errors
            }
            
            if errors:
                return formatter.validation_error(
                    message=f"批量更新完成，成功: {len(updated_data)}，失败: {len(errors)}",
                    details=result
                )
            else:
                return formatter.success(
                    data=result,
                    message=f"批量更新成功，共更新 {len(updated_data)} 个字典类型"
                )
                
    except Exception as e:
        return formatter.internal_error(f"批量更新字典类型失败: {str(e)}")

@router.delete("/batch", summary="批量删除字典类型")
@require_batch_delete_permission("dict_type")
async def batch_delete_dict_types(
    request: Request,
    batch_request: SysDictTypeBatchDelete,
    current_user: User = DependAuth
):
    """批量删除字典类型
    
    支持一次性删除多个字典类型，会检查关联的字典数据。
    
    请求格式:
    {
        "ids": [1, 2, 3, 4, 5]
    }
    
    响应格式符合V2 API规范，包含详细的删除结果和失败信息。
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # Pydantic已经处理了基本验证，直接获取ID列表
        ids = batch_request.ids
        
        # 额外的业务验证
        if len(ids) == 0:
            return formatter.validation_error(
                message="ID列表不能为空",
                details=[APIv2ErrorDetail(
                    field="ids",
                    code="EMPTY_ID_LIST",
                    message="ID列表不能为空",
                    value=ids
                )]
            )
        
        async with in_transaction("default"):
            deleted_count = 0
            failed_items = []
            skipped_items = []
            
            for dict_type_id in ids:
                try:
                    dict_type = await DictType.get_or_none(id=dict_type_id)
                    if not dict_type:
                        failed_items.append({
                            "id": dict_type_id,
                            "reason": "字典类型不存在"
                        })
                        continue
                    
                    # 检查是否有关联的字典数据
                    from app.models.system import SysDictData as DictData
                    data_count = await DictData.filter(dict_type_id=dict_type_id).count()
                    if data_count > 0:
                        skipped_items.append({
                            "id": dict_type_id,
                            "reason": f"该字典类型下有 {data_count} 条字典数据，无法删除"
                        })
                        continue
                    
                    # 执行删除
                    await dict_type.delete()
                    deleted_count += 1
                    
                except Exception as e:
                    failed_items.append({
                        "id": dict_type_id,
                        "reason": f"删除失败: {str(e)}"
                    })
            
            # 构建响应数据，符合V2 API规范
            failed_item_objects = [
                BatchDeleteFailedItem(id=item["id"], reason=item["reason"])
                for item in failed_items
            ]
            skipped_item_objects = [
                BatchDeleteSkippedItem(id=item["id"], reason=item["reason"])
                for item in skipped_items
            ]
            
            result_data = BatchDeleteResult(
                deleted_count=deleted_count,
                failed_items=failed_item_objects,
                skipped_items=skipped_item_objects
            )
            
            # 根据结果确定响应类型
            total_requested = len(ids)
            total_processed = deleted_count + len(failed_items) + len(skipped_items)
            
            if deleted_count == total_requested:
                # 全部成功
                return formatter.success(
                    data=result_data.model_dump(),
                    message=f"批量删除成功，共删除 {deleted_count} 个字典类型",
                    resource_type="dict_types"
                )
            elif deleted_count > 0:
                # 部分成功
                return formatter.success(
                    data=result_data.model_dump(),
                    message=f"批量删除部分成功，成功删除 {deleted_count} 个，失败 {len(failed_items)} 个，跳过 {len(skipped_items)} 个",
                    code=207,  # Multi-Status
                    resource_type="dict_types"
                )
            else:
                # 全部失败
                return formatter.validation_error(
                    message="批量删除失败，没有字典类型被删除",
                    details=[APIv2ErrorDetail(
                        field="batch_operation",
                        code="BATCH_DELETE_FAILED",
                        message=f"删除失败 {len(failed_items)} 个，跳过 {len(skipped_items)} 个",
                        value=result_data.model_dump()
                    )]
                )
                
    except Exception as e:
        return formatter.internal_error(f"批量删除字典类型失败: {str(e)}")

# ============================================================================
# 单个资源操作路由 (Individual Resource Routes) - 必须在批量操作路由之后定义
# ============================================================================

@router.get("/{dict_type_id}", summary="获取字典类型详情", dependencies=[DependAuth])
async def get_dict_type(
    dict_type_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """获取字典类型详情"""
    formatter = ResponseFormatterV2(request)
    
    try:
        dict_type = await DictType.get_or_none(id=dict_type_id)
        if not dict_type:
            return formatter.not_found("字典类型不存在", "dict_type")
        
        dict_type_data = {
            "id": dict_type.id,
            "type_name": dict_type.type_name,
            "type_code": dict_type.type_code,
            "description": dict_type.description,
            "created_at": dict_type.created_at.isoformat() if dict_type.created_at else None,
            "updated_at": dict_type.updated_at.isoformat() if dict_type.updated_at else None
        }
        
        return formatter.success(
            data=dict_type_data,
            message="获取字典类型详情成功",
            resource_id=str(dict_type_id),
            resource_type="dict_types"
        )
        
    except Exception as e:
        return formatter.internal_error(f"获取字典类型详情失败: {str(e)}")

@router.put("/{dict_type_id}", summary="更新字典类型")
async def update_dict_type(
    request: Request,
    dict_type_id: int,
    dict_type_data: SysDictTypeUpdate,
    current_user: User = DependAuth
):
    """更新字典类型"""
    formatter = ResponseFormatterV2(request)
    
    try:
        async with in_transaction("default"):
            existing_dict_type = await DictType.get_or_none(id=dict_type_id)
            if not existing_dict_type:
                return formatter.not_found("字典类型不存在", "dict_type")
            
            # 如果更新字典类型代码，检查是否与其他字典类型冲突
            if dict_type_data.type_code and dict_type_data.type_code != existing_dict_type.type_code:
                conflicting_dict_type = await DictType.get_or_none(type_code=dict_type_data.type_code)
                if conflicting_dict_type and conflicting_dict_type.id != dict_type_id:
                    return formatter.validation_error(
                        message="字典类型编码已存在",
                        details=[APIv2ErrorDetail(
                            field="type_code",
                            code="DUPLICATE_CODE",
                            message="字典类型编码已存在",
                            value=dict_type_data.type_code
                        )]
                    )
            
            # 更新字典类型
            update_data = {}
            if dict_type_data.type_name is not None:
                update_data['type_name'] = dict_type_data.type_name
            if dict_type_data.type_code is not None:
                update_data['type_code'] = dict_type_data.type_code
            if dict_type_data.description is not None:
                update_data['description'] = dict_type_data.description
            
            if update_data:
                await existing_dict_type.update_from_dict(update_data)
                await existing_dict_type.save()
            
            dict_type_data = {
                "id": existing_dict_type.id,
                "type_name": existing_dict_type.type_name,
                "type_code": existing_dict_type.type_code,
                "description": existing_dict_type.description,
                "created_at": existing_dict_type.created_at.isoformat() if existing_dict_type.created_at else None,
                "updated_at": existing_dict_type.updated_at.isoformat() if existing_dict_type.updated_at else None
            }
            
            return formatter.success(
                data=dict_type_data,
                message="字典类型更新成功",
                resource_id=str(dict_type_id),
                resource_type="dict_types"
            )
            
    except Exception as e:
        return formatter.internal_error(f"更新字典类型失败: {str(e)}")

@router.patch("/{dict_type_id}", summary="部分更新字典类型")
async def patch_dict_type(
    request: Request,
    dict_type_id: int,
    dict_type_data: SysDictTypePatch,
    current_user: User = DependAuth
):
    """部分更新字典类型（PATCH方法）
    
    只更新提供的字段，未提供的字段保持不变。
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        async with in_transaction("default"):
            existing_dict_type = await DictType.get_or_none(id=dict_type_id)
            if not existing_dict_type:
                return formatter.not_found("字典类型不存在", "dict_type")
            
            # 如果更新字典类型代码，检查是否与其他字典类型冲突
            if dict_type_data.type_code and dict_type_data.type_code != existing_dict_type.type_code:
                conflicting_dict_type = await DictType.get_or_none(type_code=dict_type_data.type_code)
                if conflicting_dict_type and conflicting_dict_type.id != dict_type_id:
                    return formatter.validation_error(
                        message="字典类型编码已存在",
                        details=[APIv2ErrorDetail(
                            field="type_code",
                            code="DUPLICATE_CODE",
                            message="字典类型编码已存在",
                            value=dict_type_data.type_code
                        )]
                    )
            
            # 构建更新数据（只包含提供的字段）
            update_data = {}
            if dict_type_data.type_name is not None:
                update_data['type_name'] = dict_type_data.type_name
            if dict_type_data.type_code is not None:
                update_data['type_code'] = dict_type_data.type_code
            if dict_type_data.description is not None:
                update_data['description'] = dict_type_data.description
            
            # 如果没有提供任何更新字段，返回错误
            if not update_data:
                return formatter.validation_error(
                    message="至少需要提供一个要更新的字段",
                    details=[APIv2ErrorDetail(
                        field="body",
                        code="NO_UPDATE_FIELDS",
                        message="请提供至少一个要更新的字段",
                        value=None
                    )]
                )
            
            # 执行更新
            await existing_dict_type.update_from_dict(update_data)
            await existing_dict_type.save()
            
            dict_type_data = {
                "id": existing_dict_type.id,
                "type_name": existing_dict_type.type_name,
                "type_code": existing_dict_type.type_code,
                "description": existing_dict_type.description,
                "created_at": existing_dict_type.created_at.isoformat() if existing_dict_type.created_at else None,
                "updated_at": existing_dict_type.updated_at.isoformat() if existing_dict_type.updated_at else None
            }
            
            return formatter.success(
                data=dict_type_data,
                message="字典类型部分更新成功",
                resource_id=str(dict_type_id),
                resource_type="dict_types"
            )
            
    except Exception as e:
        return formatter.internal_error(f"部分更新字典类型失败: {str(e)}")

@router.delete("/{dict_type_id}", summary="删除字典类型", dependencies=[DependAuth])
async def delete_dict_type(
    dict_type_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """删除字典类型"""
    formatter = ResponseFormatterV2(request)
    
    try:
        async with in_transaction("default"):
            dict_type = await DictType.get_or_none(id=dict_type_id)
            if not dict_type:
                return formatter.not_found("字典类型不存在", "dict_type")
            
            # 检查是否有关联的字典数据
            from app.models.system import SysDictData as DictData
            data_count = await DictData.filter(dict_type_id=dict_type_id).count()
            if data_count > 0:
                return formatter.validation_error(
                    message="无法删除字典类型，存在关联的字典数据",
                    details=[APIv2ErrorDetail(
                        field="dict_type_id",
                        code="HAS_RELATED_DATA",
                        message=f"该字典类型下有 {data_count} 条字典数据",
                        value=dict_type_id
                    )]
                )
            
            await dict_type.delete()
            
            return formatter.success(
                message="字典类型删除成功",
                code=204
            )
            
    except Exception as e:
        return formatter.internal_error(f"删除字典类型失败: {str(e)}")