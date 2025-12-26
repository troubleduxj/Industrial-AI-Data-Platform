from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from tortoise.exceptions import DoesNotExist
from tortoise.transactions import in_transaction
from tortoise.functions import Count

from app.core.ctx import CTX_USER_ID
from app.core.dependency import DependAuth
from app.models.device import DeviceType, DeviceField, DeviceInfo
from app.schemas.devices import (
    DeviceTypeResponse,
    DeviceTypeCreate,
    DeviceTypeUpdate,
    DeviceTypeDetailResponse,
    DeviceFieldResponse,
    DeviceFieldCreate,
    DeviceFieldUpdate
)
from app.core.response import success, fail
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/types", summary="获取设备类型列表", response_model=List[DeviceTypeResponse])
async def get_device_types(
    is_active: Optional[bool] = Query(None, description="是否激活状态筛选"),
    type_name: Optional[str] = Query(None, description="类型名称搜索"),
    type_code: Optional[str] = Query(None, description="类型编码搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    include_counts: bool = Query(False, description="是否包含统计数据"),
    user_id: int = DependAuth
):
    """
    获取设备类型列表
    """
    try:
        # 构建查询条件
        query = DeviceType.all()
        if is_active is not None:
            query = query.filter(is_active=is_active)
        if type_name:
            query = query.filter(type_name__icontains=type_name)
        if type_code:
            query = query.filter(type_code__icontains=type_code)
        
        # 分页查询
        offset = (page - 1) * page_size
        device_types = await query.offset(offset).limit(page_size).order_by('created_at')
        
        result = []
        
        if include_counts:
            # 构建结果
            for device_type in device_types:
                type_data = {
                    "id": device_type.id,
                    "type_name": device_type.type_name,
                    "type_code": device_type.type_code,
                    "tdengine_stable_name": device_type.tdengine_stable_name,
                    "description": device_type.description,
                    "is_active": device_type.is_active,
                    "device_count": device_type.device_count,  # 直接读取缓存的计数值
                    "field_count": 0, #  TODO: 后面再优化
                    "created_at": device_type.created_at.isoformat() if device_type.created_at else None,
                    "updated_at": device_type.updated_at.isoformat() if device_type.updated_at else None
                }
                result.append(type_data)
        else:
            # 不包含统计数据，快速返回
            for device_type in device_types:
                type_data = {
                    "id": device_type.id,
                    "type_name": device_type.type_name,
                    "type_code": device_type.type_code,
                    "tdengine_stable_name": device_type.tdengine_stable_name,
                    "description": device_type.description,
                    "is_active": device_type.is_active,
                    "device_count": 0,  # 默认值
                    "field_count": 0,   # 默认值
                    "created_at": device_type.created_at.isoformat() if device_type.created_at else None,
                    "updated_at": device_type.updated_at.isoformat() if device_type.updated_at else None
                }
                result.append(type_data)
        
        return success(data=result)
    
    except Exception as e:
        logger.error(f"获取设备类型列表失败: {str(e)}")
        return fail(msg=f"获取设备类型列表失败: {str(e)}")


@router.get("/types/{type_code}", summary="获取设备类型详情", response_model=DeviceTypeDetailResponse)
async def get_device_type_detail(
    type_code: str,
    user_id: int = DependAuth
):
    """
    获取设备类型详情，包含字段定义
    """
    try:
        # 获取设备类型
        device_type = await DeviceType.get(type_code=type_code)
        
        # 获取字段定义
        fields = await DeviceField.filter(device_type_code=type_code).order_by('sort_order', 'field_name')
        
        # 使用缓存的设备数量，提高查询性能
        device_count = device_type.device_count
        
        # 构建响应数据
        field_list = [
            DeviceFieldResponse(
                id=field.id,
                device_type_code=field.device_type_code,
                field_name=field.field_name,
                field_type=field.field_type,
                field_description=field.field_description,
                is_required=field.is_required,
                is_tag=field.is_tag,
                sort_order=field.sort_order,
                created_at=field.created_at,
                updated_at=field.updated_at
            )
            for field in fields
        ]
        
        result = DeviceTypeDetailResponse(
            id=device_type.id,
            type_name=device_type.type_name,
            type_code=device_type.type_code,
            tdengine_stable_name=device_type.tdengine_stable_name,
            description=device_type.description,
            is_active=device_type.is_active,
            device_count=device_count,
            field_count=len(field_list),
            created_at=device_type.created_at,
            updated_at=device_type.updated_at,
            fields=field_list
        )
        
        return success(data=result)
    
    except DoesNotExist:
        return fail(msg=f"设备类型 {type_code} 不存在")
    except Exception as e:
        logger.error(f"获取设备类型详情失败: {str(e)}")
        return fail(msg=f"获取设备类型详情失败: {str(e)}")


@router.post("/types", summary="创建设备类型")
async def create_device_type(
    device_type_data: DeviceTypeCreate,
    user_id: int = DependAuth
):
    """
    创建新的设备类型
    """
    try:
        async with in_transaction():
            # 检查类型代码是否已存在
            if await DeviceType.filter(type_code=device_type_data.type_code).exists():
                return fail(msg=f"设备类型代码 {device_type_data.type_code} 已存在")
            
            # 创建设备类型
            device_type = await DeviceType.create(**device_type_data.model_dump())
            
            return success(data={"id": device_type.id, "type_code": device_type.type_code}, msg="设备类型创建成功")
    
    except Exception as e:
        logger.error(f"创建设备类型失败: {str(e)}")
        return fail(msg=f"创建设备类型失败: {str(e)}")


@router.put("/types/{type_code}", summary="更新设备类型")
async def update_device_type(
    type_code: str,
    device_type_data: DeviceTypeUpdate,
    user_id: int = DependAuth
):
    """
    更新设备类型信息
    """
    try:
        async with in_transaction():
            # 获取设备类型
            device_type = await DeviceType.get(type_code=type_code)
            
            # 更新字段
            update_data = device_type_data.model_dump(exclude_unset=True)
            if update_data:
                await device_type.update_from_dict(update_data)
                await device_type.save()
            
            return success(msg="设备类型更新成功")
    
    except DoesNotExist:
        return fail(msg=f"设备类型 {type_code} 不存在")
    except Exception as e:
        logger.error(f"更新设备类型失败: {str(e)}")
        return fail(msg=f"更新设备类型失败: {str(e)}")


@router.delete("/types/{type_code}", summary="删除设备类型")
async def delete_device_type(
    type_code: str,
    user_id: int = DependAuth
):
    """
    删除设备类型（软删除，设置为非激活状态）
    """
    try:
        async with in_transaction():
            # 检查是否有关联的设备
            device_count = await DeviceInfo.filter(device_type=type_code).count()
            if device_count > 0:
                return fail(msg=f"该设备类型下还有 {device_count} 个设备，无法删除")
            
            # 获取设备类型
            device_type = await DeviceType.get(type_code=type_code)
            
            # 软删除（设置为非激活状态）
            device_type.is_active = False
            await device_type.save()
            
            return success(msg="设备类型删除成功")
    
    except DoesNotExist:
        return fail(msg=f"设备类型 {type_code} 不存在")
    except Exception as e:
        logger.error(f"删除设备类型失败: {str(e)}")
        return fail(msg=f"删除设备类型失败: {str(e)}")


# =====================================================
# 设备字段相关接口
# =====================================================

@router.get("/types/{type_code}/fields", summary="获取设备类型字段列表", response_model=List[DeviceFieldResponse])
async def get_device_type_fields(
    type_code: str,
    user_id: int = DependAuth
):
    """
    获取指定设备类型的字段定义列表
    """
    try:
        # 检查设备类型是否存在
        if not await DeviceType.filter(type_code=type_code).exists():
            return fail(msg=f"设备类型 {type_code} 不存在")
        
        # 获取字段列表
        fields = await DeviceField.filter(device_type_code=type_code).order_by('sort_order', 'field_name')
        
        result = [
            DeviceFieldResponse(
                id=field.id,
                device_type_code=field.device_type_code,
                field_name=field.field_name,
                field_type=field.field_type,
                field_description=field.field_description,
                is_required=field.is_required,
                is_tag=field.is_tag,
                sort_order=field.sort_order,
                created_at=field.created_at,
                updated_at=field.updated_at
            )
            for field in fields
        ]
        
        return success(data=result)
    
    except Exception as e:
        logger.error(f"获取设备字段列表失败: {str(e)}")
        return fail(msg=f"获取设备字段列表失败: {str(e)}")


@router.post("/types/{type_code}/fields", summary="添加设备字段")
async def create_device_field(
    type_code: str,
    field_data: DeviceFieldCreate,
    user_id: int = DependAuth
):
    """
    为指定设备类型添加字段定义
    """
    try:
        async with in_transaction():
            # 检查设备类型是否存在
            if not await DeviceType.filter(type_code=type_code).exists():
                return fail(msg=f"设备类型 {type_code} 不存在")
            
            # 检查字段是否已存在
            if await DeviceField.filter(device_type_code=type_code, field_name=field_data.field_name).exists():
                return fail(msg=f"字段 {field_data.field_name} 已存在")
            
            # 确保device_type_code与路径参数一致
            field_data.device_type_code = type_code
            
            # 创建字段
            field = await DeviceField.create(**field_data.model_dump())
            
            return success(data={"id": field.id, "field_name": field.field_name}, msg="设备字段创建成功")
    
    except Exception as e:
        logger.error(f"创建设备字段失败: {str(e)}")
        return fail(msg=f"创建设备字段失败: {str(e)}")


@router.put("/types/{type_code}/fields/{field_id}", summary="更新设备字段")
async def update_device_field(
    type_code: str,
    field_id: int,
    field_data: DeviceFieldUpdate,
    user_id: int = DependAuth
):
    """
    更新设备字段定义
    """
    try:
        async with in_transaction():
            # 获取字段
            field = await DeviceField.get(id=field_id, device_type_code=type_code)
            
            # 更新字段
            update_data = field_data.model_dump(exclude_unset=True)
            if update_data:
                await field.update_from_dict(update_data)
                await field.save()
            
            return success(msg="设备字段更新成功")
    
    except DoesNotExist:
        return fail(msg=f"字段不存在")
    except Exception as e:
        logger.error(f"更新设备字段失败: {str(e)}")
        return fail(msg=f"更新设备字段失败: {str(e)}")


@router.delete("/types/{type_code}/fields/{field_id}", summary="删除设备字段")
async def delete_device_field(
    type_code: str,
    field_id: int,
    user_id: int = DependAuth
):
    """
    删除设备字段定义
    """
    try:
        async with in_transaction():
            # 获取字段
            field = await DeviceField.get(id=field_id, device_type_code=type_code)
            
            # 删除字段
            await field.delete()
            
            return success(msg="设备字段删除成功")
    
    except DoesNotExist:
        return fail(msg=f"字段不存在")
    except Exception as e:
        logger.error(f"删除设备字段失败: {str(e)}")
        return fail(msg=f"删除设备字段失败: {str(e)}")