"""
字典数据管理 v2接口
提供字典数据管理的RESTful接口
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from fastapi import APIRouter, Request, Depends, Query, Body, Path
from fastapi.responses import JSONResponse
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.models.system import SysDictData as DictData, SysDictType as DictType
from app.models.admin import User
from app.core.dependency import DependAuth
from app.core.response_formatter_v2 import ResponseFormatterV2, APIv2ErrorDetail
from app.core.batch_delete_decorators import require_batch_delete_permission
from app.schemas.base import BatchDeleteRequest
from app.schemas.system import (
    SysDictDataCreate,
    SysDictDataUpdate,
    SysDictDataPatch,
    SysDictDataBatchCreate,
    SysDictDataBatchUpdate,
    SysDictDataBatchDelete,
    SysDictDataBatchToggleStatus,
    SysDictDataBatchResponse,
    SysDictDataByTypeQuery,
    SysDictDataInDB,
    SysDictDataWithType
)

router = APIRouter()

@router.get("", summary="获取字典数据列表")
async def get_dict_data(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    dict_type_id: Optional[int] = Query(None, description="字典类型ID"),
    data_label: Optional[str] = Query(None, description="字典标签"),
    data_value: Optional[str] = Query(None, description="字典值"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = DependAuth
):
    """获取字典数据列表"""
    formatter = ResponseFormatterV2(request)
    
    try:
        # 构建查询条件
        query = DictData.all().select_related('dict_type')
        query_params = {}
        
        if search:
            query = query.filter(
                Q(data_label__icontains=search) | 
                Q(data_value__icontains=search) |
                Q(description__icontains=search)
            )
            query_params['search'] = search
        
        if dict_type_id:
            query = query.filter(dict_type_id=dict_type_id)
            query_params['dict_type_id'] = dict_type_id
            
        if data_label:
            query = query.filter(data_label__icontains=data_label)
            query_params['data_label'] = data_label
            
        if data_value:
            query = query.filter(data_value__icontains=data_value)
            query_params['data_value'] = data_value
            
        if is_enabled is not None:
            query = query.filter(is_enabled=is_enabled)
            query_params['is_enabled'] = is_enabled
        
        # 分页查询
        total = await query.count()
        offset = (page - 1) * page_size
        # 修复排序问题：处理created_at为null的情况，使用id作为备用排序字段
        dict_data_list = await query.offset(offset).limit(page_size).order_by('sort_order', '-created_at', '-id')
        
        # 格式化响应数据
        data_list = []
        for dd in dict_data_list:
            data_list.append({
                "id": dd.id,
                "dict_type_id": dd.dict_type_id,
                "dict_type": dd.dict_type.type_code if dd.dict_type else None,
                "dict_type_name": dd.dict_type.type_name if dd.dict_type else None,
                "data_label": dd.data_label,
                "data_value": dd.data_value,
                "sort_order": dd.sort_order,
                "description": getattr(dd, 'description', ''),
                "is_enabled": dd.is_enabled,
                "created_at": dd.created_at.isoformat() if dd.created_at else None,
                "updated_at": dd.updated_at.isoformat() if dd.updated_at else None
            })
        
        return formatter.paginated_success(
            data=data_list,
            total=total,
            page=page,
            page_size=page_size,
            message="获取字典数据列表成功",
            resource_type="dict_data",
            query_params=query_params
        )
        
    except Exception as e:
        return formatter.internal_error(f"获取字典数据列表失败: {str(e)}")

# 批量操作路由必须在参数化路由之前定义
@router.post("/batch", summary="批量创建字典数据")
async def batch_create_dict_data(
    request: Request,
    dict_data_list: List[Dict[str, Any]] = Body(..., description="字典数据列表"),
    current_user: User = DependAuth
):
    """批量创建字典数据
    
    支持一次性创建多个字典数据。
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        async with in_transaction("default"):
            created_data = []
            errors = []
            
            for index, dict_data_info in enumerate(dict_data_list):
                try:
                    # 验证必需字段
                    required_fields = ['dict_type_id', 'data_label', 'data_value']
                    for field in required_fields:
                        if field not in dict_data_info or dict_data_info[field] is None:
                            errors.append({
                                "index": index,
                                "field": field,
                                "code": "REQUIRED_FIELD_MISSING",
                                "message": f"缺少必需字段: {field}"
                            })
                            continue
                    
                    if errors:
                        continue
                    
                    # 检查字典类型是否存在
                    dict_type = await DictType.get_or_none(id=dict_data_info['dict_type_id'])
                    if not dict_type:
                        errors.append({
                            "index": index,
                            "field": "dict_type_id",
                            "code": "NOT_FOUND",
                            "message": "字典类型不存在",
                            "value": dict_data_info['dict_type_id']
                        })
                        continue
                    
                    # 检查同一字典类型下的数据值是否重复
                    existing_data = await DictData.get_or_none(
                        dict_type_id=dict_data_info['dict_type_id'],
                        data_value=dict_data_info['data_value']
                    )
                    if existing_data:
                        errors.append({
                            "index": index,
                            "field": "data_value",
                            "code": "DUPLICATE_VALUE",
                            "message": "同一字典类型下的数据值不能重复",
                            "value": dict_data_info['data_value']
                        })
                        continue
                    
                    # 创建字典数据
                    new_dict_data = await DictData.create(
                        dict_type_id=dict_data_info['dict_type_id'],
                        data_label=dict_data_info['data_label'],
                        data_value=dict_data_info['data_value'],
                        sort_order=dict_data_info.get('sort_order', 0),
                        description=dict_data_info.get('description', ''),
                        is_enabled=dict_data_info.get('is_enabled', True)
                    )
                    
                    created_data.append({
                        "id": new_dict_data.id,
                        "dict_type_id": new_dict_data.dict_type_id,
                        "data_label": new_dict_data.data_label,
                        "data_value": new_dict_data.data_value,
                        "sort_order": new_dict_data.sort_order,
                        "description": new_dict_data.description,
                        "is_enabled": new_dict_data.is_enabled
                    })
                    
                except Exception as e:
                    errors.append({
                        "index": index,
                        "code": "CREATE_ERROR",
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
                    message=f"批量创建成功，共创建 {len(created_data)} 条字典数据"
                )
                
    except Exception as e:
        return formatter.internal_error(f"批量创建字典数据失败: {str(e)}")

@router.put("/batch", summary="批量更新字典数据")
async def batch_update_dict_data(
    request: Request,
    updates: List[Dict[str, Any]] = Body(..., description="更新数据列表，每项必须包含id字段"),
    current_user: User = DependAuth
):
    """批量更新字典数据
    
    支持一次性更新多个字典数据。
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
                    
                    dict_data_id = update_info['id']
                    dict_data = await DictData.get_or_none(id=dict_data_id)
                    if not dict_data:
                        errors.append({
                            "index": index,
                            "field": "id",
                            "code": "NOT_FOUND",
                            "message": "字典数据不存在",
                            "value": dict_data_id
                        })
                        continue
                    
                    # 如果更新字典类型，检查新的字典类型是否存在
                    if 'dict_type_id' in update_info and update_info['dict_type_id'] != dict_data.dict_type_id:
                        dict_type = await DictType.get_or_none(id=update_info['dict_type_id'])
                        if not dict_type:
                            errors.append({
                                "index": index,
                                "field": "dict_type_id",
                                "code": "NOT_FOUND",
                                "message": "字典类型不存在",
                                "value": update_info['dict_type_id']
                            })
                            continue
                    
                    # 如果更新数据值，检查是否与同一字典类型下的其他数据冲突
                    if 'data_value' in update_info and update_info['data_value'] != dict_data.data_value:
                        target_dict_type_id = update_info.get('dict_type_id', dict_data.dict_type_id)
                        existing_data = await DictData.get_or_none(
                            dict_type_id=target_dict_type_id,
                            data_value=update_info['data_value']
                        )
                        if existing_data and existing_data.id != dict_data_id:
                            errors.append({
                                "index": index,
                                "field": "data_value",
                                "code": "DUPLICATE_VALUE",
                                "message": "同一字典类型下的数据值不能重复",
                                "value": update_info['data_value']
                            })
                            continue
                    
                    # 更新字段
                    update_fields = {}
                    for field in ['dict_type_id', 'data_label', 'data_value', 'sort_order', 'description', 'is_enabled']:
                        if field in update_info:
                            update_fields[field] = update_info[field]
                    
                    if update_fields:
                        await DictData.filter(id=dict_data_id).update(**update_fields)
                        
                        # 重新获取更新后的数据
                        updated_dict_data = await DictData.get(id=dict_data_id)
                        updated_data.append({
                            "id": updated_dict_data.id,
                            "dict_type_id": updated_dict_data.dict_type_id,
                            "data_label": updated_dict_data.data_label,
                            "data_value": updated_dict_data.data_value,
                            "sort_order": updated_dict_data.sort_order,
                            "description": updated_dict_data.description,
                            "is_enabled": updated_dict_data.is_enabled
                        })
                    
                except Exception as e:
                    errors.append({
                        "index": index,
                        "id": update_info.get('id'),
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
                    message=f"批量更新成功，共更新 {len(updated_data)} 条字典数据"
                )
                
    except Exception as e:
        return formatter.internal_error(f"批量更新字典数据失败: {str(e)}")

# 重复的批量删除API已删除，使用前面的实现

@router.patch("/batch/status", summary="批量切换字典数据状态")
async def batch_toggle_dict_data_status(
    request: Request,
    ids: List[int] = Body(..., description="要切换状态的字典数据ID列表"),
    is_enabled: bool = Body(..., description="目标状态"),
    current_user: User = DependAuth
):
    """批量切换字典数据状态
    
    支持一次性启用或禁用多个字典数据。
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        async with in_transaction("default"):
            updated_ids = []
            errors = []
            
            for index, dict_data_id in enumerate(ids):
                try:
                    dict_data = await DictData.get_or_none(id=dict_data_id)
                    if not dict_data:
                        errors.append({
                            "index": index,
                            "id": dict_data_id,
                            "code": "NOT_FOUND",
                            "message": "字典数据不存在"
                        })
                        continue
                    
                    # 更新状态
                    dict_data.is_enabled = is_enabled
                    await dict_data.save()
                    updated_ids.append(dict_data_id)
                    
                except Exception as e:
                    errors.append({
                        "index": index,
                        "id": dict_data_id,
                        "code": "UPDATE_ERROR",
                        "message": f"状态切换失败: {str(e)}"
                    })
            
            result = {
                "updated_count": len(updated_ids),
                "error_count": len(errors),
                "updated_ids": updated_ids,
                "target_status": is_enabled,
                "errors": errors
            }
            
            status_text = "启用" if is_enabled else "禁用"
            
            if errors:
                return formatter.validation_error(
                    message=f"批量{status_text}完成，成功: {len(updated_ids)}，失败: {len(errors)}",
                    details=result
                )
            else:
                return formatter.success(
                    data=result,
                    message=f"批量{status_text}成功，共{status_text} {len(updated_ids)} 条字典数据"
                )
                
    except Exception as e:
        return formatter.internal_error(f"批量切换字典数据状态失败: {str(e)}")

# 重复的批量删除API已删除，使用前面的实现

# 参数化路由必须在所有批量操作路由之后定义
@router.get("/{dict_data_id}", summary="获取字典数据详情", dependencies=[DependAuth])
async def get_dict_data_detail(
    dict_data_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """获取字典数据详情"""
    formatter = ResponseFormatterV2(request)
    
    try:
        dict_data = await DictData.get_or_none(id=dict_data_id).select_related('dict_type')
        if not dict_data:
            return formatter.not_found("字典数据不存在", "dict_data")
        
        dict_data_detail = {
            "id": dict_data.id,
            "dict_type_id": dict_data.dict_type_id,
            "dict_type": dict_data.dict_type.type_code if dict_data.dict_type else None,
            "dict_type_name": dict_data.dict_type.type_name if dict_data.dict_type else None,
            "data_label": dict_data.data_label,
            "data_value": dict_data.data_value,
            "sort_order": dict_data.sort_order,
            "description": getattr(dict_data, 'description', ''),
            "is_enabled": dict_data.is_enabled,
            "created_at": dict_data.created_at.isoformat() if dict_data.created_at else None,
            "updated_at": dict_data.updated_at.isoformat() if dict_data.updated_at else None
        }
        
        return formatter.success(
            data=dict_data_detail,
            message="获取字典数据详情成功",
            resource_id=str(dict_data_id),
            resource_type="dict_data"
        )
        
    except Exception as e:
        return formatter.internal_error(f"获取字典数据详情失败: {str(e)}")

@router.post("", summary="创建字典数据")
async def create_dict_data(
    request: Request,
    dict_data: SysDictDataCreate,
    current_user: User = DependAuth
):
    """创建字典数据"""
    formatter = ResponseFormatterV2(request)
    
    try:
        async with in_transaction("default"):
            # 检查字典类型是否存在
            dict_type = await DictType.get_or_none(id=dict_data.dict_type_id)
            if not dict_type:
                return formatter.validation_error(
                    message="字典类型不存在",
                    details=[APIv2ErrorDetail(
                        field="dict_type_id",
                        code="NOT_FOUND",
                        message="指定的字典类型不存在",
                        value=dict_data.dict_type_id
                    )]
                )
            
            # 检查同一字典类型下的值是否已存在
            existing_dict_data = await DictData.get_or_none(
                dict_type_id=dict_data.dict_type_id,
                data_value=dict_data.data_value
            )
            if existing_dict_data:
                return formatter.validation_error(
                    message="字典值已存在",
                    details=[APIv2ErrorDetail(
                        field="data_value",
                        code="DUPLICATE_VALUE",
                        message="同一字典类型下的值已存在",
                        value=dict_data.data_value
                    )]
                )
            
            # 创建字典数据
            new_dict_data = await DictData.create(
                dict_type_id=dict_data.dict_type_id,
                data_label=dict_data.data_label,
                data_value=dict_data.data_value,
                sort_order=dict_data.sort_order,
                description=dict_data.description,
                is_enabled=dict_data.is_enabled
            )
            
            # 重新查询以获取关联的字典类型信息
            dict_data_with_type = await DictData.filter(id=new_dict_data.id).select_related('dict_type').first()
            
            dict_data_detail = {
                "id": dict_data_with_type.id,
                "dict_type_id": dict_data_with_type.dict_type_id,
                "dict_type": dict_data_with_type.dict_type.type_code if dict_data_with_type.dict_type else None,
                "dict_type_name": dict_data_with_type.dict_type.type_name if dict_data_with_type.dict_type else None,
                "data_label": dict_data_with_type.data_label,
                "data_value": dict_data_with_type.data_value,
                "sort_order": dict_data_with_type.sort_order,
                "description": getattr(dict_data_with_type, 'description', ''),
                "is_enabled": dict_data_with_type.is_enabled,
                "created_at": dict_data_with_type.created_at.isoformat() if dict_data_with_type.created_at else None,
                "updated_at": dict_data_with_type.updated_at.isoformat() if dict_data_with_type.updated_at else None
            }
            
            return formatter.success(
                data=dict_data_detail,
                message="字典数据创建成功",
                code=201,
                resource_id=str(new_dict_data.id),
                resource_type="dict_data"
            )
            
    except Exception as e:
        return formatter.internal_error(f"创建字典数据失败: {str(e)}")

@router.put("/{dict_data_id}", summary="更新字典数据")
async def update_dict_data(
    request: Request,
    dict_data_id: int,
    dict_data: SysDictDataUpdate,
    current_user: User = DependAuth
):
    """更新字典数据"""
    formatter = ResponseFormatterV2(request)
    
    try:
        async with in_transaction("default"):
            existing_dict_data = await DictData.get_or_none(id=dict_data_id)
            if not existing_dict_data:
                return formatter.not_found("字典数据不存在", "dict_data")
            
            # 如果更新字典类型，检查新的字典类型是否存在
            if dict_data.dict_type_id and dict_data.dict_type_id != existing_dict_data.dict_type_id:
                dict_type = await DictType.get_or_none(id=dict_data.dict_type_id)
                if not dict_type:
                    return formatter.validation_error(
                        message="字典类型不存在",
                        details=[APIv2ErrorDetail(
                            field="dict_type_id",
                            code="NOT_FOUND",
                            message="指定的字典类型不存在",
                            value=dict_data.dict_type_id
                        )]
                    )
            
            # 如果更新字典值，检查是否与同类型下的其他值冲突
            if dict_data.data_value and dict_data.data_value != existing_dict_data.data_value:
                check_type_id = dict_data.dict_type_id if dict_data.dict_type_id else existing_dict_data.dict_type_id
                conflict_dict_data = await DictData.get_or_none(
                    dict_type_id=check_type_id,
                    data_value=dict_data.data_value
                )
                if conflict_dict_data and conflict_dict_data.id != dict_data_id:
                    return formatter.validation_error(
                        message="字典值已存在",
                        details=[APIv2ErrorDetail(
                            field="data_value",
                            code="DUPLICATE_VALUE",
                            message="同一字典类型下的值已存在",
                            value=dict_data.data_value
                        )]
                    )
            
            # 更新字典数据
            update_data = {}
            if dict_data.dict_type_id is not None:
                update_data['dict_type_id'] = dict_data.dict_type_id
            if dict_data.data_label is not None:
                update_data['data_label'] = dict_data.data_label
            if dict_data.data_value is not None:
                update_data['data_value'] = dict_data.data_value
            if dict_data.sort_order is not None:
                update_data['sort_order'] = dict_data.sort_order
            if dict_data.description is not None:
                update_data['description'] = dict_data.description
            if dict_data.is_enabled is not None:
                update_data['is_enabled'] = dict_data.is_enabled
            
            if update_data:
                await existing_dict_data.update_from_dict(update_data)
                await existing_dict_data.save()
            
            # 重新查询以获取关联的字典类型信息
            updated_dict_data = await DictData.filter(id=dict_data_id).select_related('dict_type').first()
            
            dict_data_detail = {
                "id": updated_dict_data.id,
                "dict_type_id": updated_dict_data.dict_type_id,
                "dict_type": updated_dict_data.dict_type.type_code if updated_dict_data.dict_type else None,
                "dict_type_name": updated_dict_data.dict_type.type_name if updated_dict_data.dict_type else None,
                "data_label": updated_dict_data.data_label,
                "data_value": updated_dict_data.data_value,
                "sort_order": updated_dict_data.sort_order,
                "description": getattr(updated_dict_data, 'description', ''),
                "is_enabled": updated_dict_data.is_enabled,
                "created_at": updated_dict_data.created_at.isoformat() if updated_dict_data.created_at else None,
                "updated_at": updated_dict_data.updated_at.isoformat() if updated_dict_data.updated_at else None
            }
            
            return formatter.success(
                data=dict_data_detail,
                message="字典数据更新成功",
                resource_id=str(dict_data_id),
                resource_type="dict_data"
            )
            
    except Exception as e:
        return formatter.internal_error(f"更新字典数据失败: {str(e)}")

@router.patch("/{dict_data_id}", summary="部分更新字典数据")
async def patch_dict_data(
    request: Request,
    dict_data_id: int,
    dict_data: SysDictDataPatch,
    current_user: User = DependAuth
):
    """部分更新字典数据（PATCH方法）
    
    只更新提供的字段，未提供的字段保持不变。
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        async with in_transaction("default"):
            existing_dict_data = await DictData.get_or_none(id=dict_data_id)
            if not existing_dict_data:
                return formatter.not_found("字典数据不存在", "dict_data")
            
            # 如果更新字典类型，检查新的字典类型是否存在
            if dict_data.dict_type_id and dict_data.dict_type_id != existing_dict_data.dict_type_id:
                dict_type = await DictType.get_or_none(id=dict_data.dict_type_id)
                if not dict_type:
                    return formatter.validation_error(
                        message="字典类型不存在",
                        details=[APIv2ErrorDetail(
                            field="dict_type_id",
                            code="NOT_FOUND",
                            message="指定的字典类型不存在",
                            value=dict_data.dict_type_id
                        )]
                    )
            
            # 如果更新字典值，检查是否与同类型下的其他值冲突
            if dict_data.data_value and dict_data.data_value != existing_dict_data.data_value:
                check_type_id = dict_data.dict_type_id if dict_data.dict_type_id else existing_dict_data.dict_type_id
                conflict_dict_data = await DictData.get_or_none(
                    dict_type_id=check_type_id,
                    data_value=dict_data.data_value
                )
                if conflict_dict_data and conflict_dict_data.id != dict_data_id:
                    return formatter.validation_error(
                        message="字典值已存在",
                        details=[APIv2ErrorDetail(
                            field="data_value",
                            code="DUPLICATE_VALUE",
                            message="同一字典类型下的值已存在",
                            value=dict_data.data_value
                        )]
                    )
            
            # 构建更新数据（只包含提供的字段）
            update_data = {}
            if dict_data.dict_type_id is not None:
                update_data['dict_type_id'] = dict_data.dict_type_id
            if dict_data.data_label is not None:
                update_data['data_label'] = dict_data.data_label
            if dict_data.data_value is not None:
                update_data['data_value'] = dict_data.data_value
            if dict_data.sort_order is not None:
                update_data['sort_order'] = dict_data.sort_order
            if dict_data.description is not None:
                update_data['description'] = dict_data.description
            if dict_data.is_enabled is not None:
                update_data['is_enabled'] = dict_data.is_enabled
            
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
            await existing_dict_data.update_from_dict(update_data)
            await existing_dict_data.save()
            
            # 重新查询以获取关联的字典类型信息
            updated_dict_data = await DictData.filter(id=dict_data_id).select_related('dict_type').first()
            
            dict_data_detail = {
                "id": updated_dict_data.id,
                "dict_type_id": updated_dict_data.dict_type_id,
                "dict_type": updated_dict_data.dict_type.type_code if updated_dict_data.dict_type else None,
                "dict_type_name": updated_dict_data.dict_type.type_name if updated_dict_data.dict_type else None,
                "data_label": updated_dict_data.data_label,
                "data_value": updated_dict_data.data_value,
                "sort_order": updated_dict_data.sort_order,
                "description": getattr(updated_dict_data, 'description', ''),
                "is_enabled": updated_dict_data.is_enabled,
                "created_at": updated_dict_data.created_at.isoformat() if updated_dict_data.created_at else None,
                "updated_at": updated_dict_data.updated_at.isoformat() if updated_dict_data.updated_at else None
            }
            
            return formatter.success(
                data=dict_data_detail,
                message="字典数据部分更新成功",
                resource_id=str(dict_data_id),
                resource_type="dict_data"
            )
            
    except Exception as e:
        return formatter.internal_error(f"部分更新字典数据失败: {str(e)}")

# 重复的批量创建API已删除，使用前面的实现

@router.get("/{data_id}/children", summary="获取字典数据子节点")
async def get_dict_data_children(
    request: Request,
    data_id: int = Path(..., description="字典数据ID"),
    current_user: User = DependAuth
):
    """获取字典数据的子节点
    
    注意：当前字典数据模型不支持树形结构，此接口返回空列表。
    如需树形结构支持，需要在SysDictData模型中添加parent_id字段。
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查字典数据是否存在
        dict_data = await DictData.get_or_none(id=data_id)
        if not dict_data:
            return formatter.not_found("字典数据不存在")
        
        # 当前模型不支持树形结构，返回空列表
        # 如果将来需要支持树形结构，可以在这里实现查询逻辑
        children = []
        
        return formatter.success(
            data={
                "parent_id": data_id,
                "parent_label": dict_data.data_label,
                "parent_value": dict_data.data_value,
                "children_count": len(children),
                "children": children,
                "note": "当前字典数据模型不支持树形结构，如需此功能请联系管理员"
            },
            message="获取字典数据子节点成功"
        )
        
    except Exception as e:
        return formatter.internal_error(f"获取字典数据子节点失败: {str(e)}")

@router.delete("/batch", summary="批量删除字典数据")
@require_batch_delete_permission("dict_data")
async def batch_delete_dict_data(
    request: Request,
    batch_request: BatchDeleteRequest,
    current_user: User = DependAuth
):
    """
    批量删除字典数据 v2版本
    
    使用标准化数据格式：{"ids": [1, 2, 3]}
    返回标准化响应格式，包含用户友好的错误提示
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        from app.services.batch_delete_service import dict_data_batch_delete_service
        from tortoise.transactions import in_transaction
        
        ids = batch_request.ids
        if not ids:
            return formatter.validation_error(
                message="字典数据ID列表不能为空",
                details=[APIv2ErrorDetail(
                    field="ids",
                    code="EMPTY_LIST",
                    message="字典数据ID列表不能为空",
                    value=ids
                )]
            )
        
        async with in_transaction("default"):
            # 使用标准化批量删除服务
            result = await dict_data_batch_delete_service.batch_delete(ids=ids)
            
            # 生成用户友好的响应消息
            if result.failed_count == 0:
                message = f"成功删除 {result.deleted_count} 条字典数据"
            elif result.deleted_count == 0:
                failed_reasons = [item.reason for item in result.failed]
                message = f"删除失败：{'; '.join(failed_reasons)}"
            else:
                failed_details = [f"{item.name or item.id}：{item.reason}" for item in result.failed]
                message = f"批量删除完成：成功删除 {result.deleted_count} 个，失败 {result.failed_count} 个字典数据。失败原因：{'; '.join(failed_details)}"
            
            return formatter.success(
                data=result.model_dump(),
                message=message,
                resource_type="dict_data"
            )
                
    except Exception as e:
        return formatter.internal_error(f"批量删除字典数据失败: {str(e)}")

@router.delete("/{dict_data_id}", summary="删除字典数据", dependencies=[DependAuth])
async def delete_dict_data(
    dict_data_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """删除字典数据"""
    formatter = ResponseFormatterV2(request)
    
    try:
        async with in_transaction("default"):
            dict_data = await DictData.get_or_none(id=dict_data_id)
            if not dict_data:
                return formatter.not_found("字典数据不存在", "dict_data")
            
            await dict_data.delete()
            
            return formatter.success(
                message="字典数据删除成功",
                code=204
            )
            
    except Exception as e:
        return formatter.internal_error(f"删除字典数据失败: {str(e)}")

@router.get("/by-type/{type_code}", summary="按字典类型编码获取字典数据")
async def get_dict_data_by_type(
    request: Request,
    type_code: str,
    is_enabled: Optional[bool] = Query(None, description="是否启用过滤"),
    sort_by: Optional[str] = Query("sort_order", description="排序字段"),
    sort_order: Optional[str] = Query("asc", description="排序方向"),
    current_user: User = DependAuth
):
    """按字典类型编码获取字典数据
    
    根据字典类型编码获取该类型下的所有字典数据。
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 首先检查字典类型是否存在
        dict_type = await DictType.get_or_none(type_code=type_code)
        if not dict_type:
            return formatter.not_found(f"字典类型 '{type_code}' 不存在", "dict_type")
        
        # 构建查询条件
        query = DictData.filter(dict_type_id=dict_type.id)
        
        # 添加启用状态过滤
        if is_enabled is not None:
            query = query.filter(is_enabled=is_enabled)
        
        # 添加排序
        valid_sort_fields = ['sort_order', 'data_label', 'data_value', 'created_at', 'updated_at']
        if sort_by not in valid_sort_fields:
            sort_by = 'sort_order'
        
        if sort_order.lower() == 'desc':
            query = query.order_by(f'-{sort_by}')
        else:
            query = query.order_by(sort_by)
        
        # 执行查询
        dict_data_list = await query.select_related('dict_type')
        
        # 构建响应数据
        data_list = []
        for dict_data in dict_data_list:
            data_list.append({
                "id": dict_data.id,
                "dict_type_id": dict_data.dict_type_id,
                "dict_type": dict_data.dict_type.type_code if dict_data.dict_type else None,
                "dict_type_name": dict_data.dict_type.type_name if dict_data.dict_type else None,
                "data_label": dict_data.data_label,
                "data_value": dict_data.data_value,
                "sort_order": dict_data.sort_order,
                "description": getattr(dict_data, 'description', ''),
                "is_enabled": dict_data.is_enabled,
                "created_at": dict_data.created_at.isoformat() if dict_data.created_at else None,
                "updated_at": dict_data.updated_at.isoformat() if dict_data.updated_at else None
            })
        
        result = {
            "dict_type": {
                "id": dict_type.id,
                "type_code": dict_type.type_code,
                "type_name": dict_type.type_name,
                "description": getattr(dict_type, 'description', '')
            },
            "total_count": len(data_list),
            "data": data_list
        }
        
        return formatter.success(
            data=result,
            message=f"成功获取字典类型 '{type_code}' 下的字典数据",
            resource_type="dict_data"
        )
        
    except Exception as e:
        return formatter.internal_error(f"获取字典数据失败: {str(e)}")

# 重复的批量状态切换API已删除，使用前面的实现