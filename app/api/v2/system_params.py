"""
系统参数管理 v2接口
提供系统参数管理的RESTful接口
"""
from typing import List, Optional
from fastapi import APIRouter, Request, Depends, Query, Body, Path
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.models.system import TSysConfig as SystemParam
from app.models.admin import User
from app.schemas.system import SysConfigCreate, SysConfigBatchDelete
from app.core.dependency import DependAuth
from app.core.response_formatter_v2 import ResponseFormatterV2, APIv2ErrorDetail
from app.core.batch_delete_decorators import require_batch_delete_permission
from app.core.pagination import create_pagination_response
from app.controllers.system import config_controller

router = APIRouter()

@router.get("", summary="获取系统参数列表")
async def get_system_params(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    param_name: Optional[str] = Query(None, description="参数名称"),
    param_key: Optional[str] = Query(None, description="参数键"),
    param_type: Optional[str] = Query(None, description="参数类型"),
    is_system: Optional[bool] = Query(None, description="是否系统内置"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = DependAuth
):
    """获取系统参数列表"""
    formatter = ResponseFormatterV2(request)
    
    try:
        # 构建查询条件
        query = SystemParam.all()
        query_params = {}
        
        if search:
            query = query.filter(
                Q(param_name__icontains=search) | 
                Q(param_key__icontains=search) |
                Q(description__icontains=search)
            )
            query_params['search'] = search
        
        if param_name:
            query = query.filter(param_name__icontains=param_name)
            query_params['param_name'] = param_name
            
        if param_key:
            query = query.filter(param_key__icontains=param_key)
            query_params['param_key'] = param_key
            
        if param_type:
            query = query.filter(param_type=param_type)
            query_params['param_type'] = param_type
            
        if is_system is not None:
            query = query.filter(is_system=is_system)
            query_params['is_system'] = is_system
            
        if is_active is not None:
            query = query.filter(is_active=is_active)
            query_params['is_active'] = is_active
        
        # 分页查询
        total = await query.count()
        offset = (page - 1) * page_size
        system_params = await query.offset(offset).limit(page_size).order_by('-created_at')
        
        # 格式化响应数据
        param_list = []
        for sp in system_params:
            param_list.append({
                "id": sp.id,
                "param_name": sp.param_name,
                "param_key": sp.param_key,
                "param_value": sp.param_value,
                "param_type": sp.param_type,
                "description": sp.description,
                "is_editable": sp.is_editable,
                "is_system": sp.is_system,
                "is_active": sp.is_active,
                "created_at": sp.created_at.isoformat() if sp.created_at else None,
                "updated_at": sp.updated_at.isoformat() if sp.updated_at else None
            })
        
        # 创建分页响应
        paginated_response = create_pagination_response(
            data=param_list,
            total=total,
            page=page,
            page_size=page_size
        )
        
        return formatter.success(
            data=paginated_response,
            message="获取系统参数列表成功",
            resource_type="system_params"
        )
        
    except Exception as e:
        return formatter.internal_error(f"获取系统参数列表失败: {str(e)}")

@router.get("/{param_id}", summary="获取系统参数详情")
async def get_system_param(
    request: Request,
    param_id: int = Path(..., description="参数ID"),
    current_user: User = DependAuth
):
    """获取系统参数详情"""
    formatter = ResponseFormatterV2(request)
    
    try:
        system_param = await SystemParam.get_or_none(id=param_id)
        if not system_param:
            return formatter.not_found("系统参数不存在", "system_param")
        
        param_data = {
            "id": system_param.id,
            "param_name": system_param.param_name,
            "param_key": system_param.param_key,
            "param_value": system_param.param_value,
            "param_type": system_param.param_type,
            "description": system_param.description,
            "is_editable": system_param.is_editable,
            "is_system": system_param.is_system,
            "is_active": system_param.is_active,
            "created_at": system_param.created_at.isoformat() if system_param.created_at else None,
            "updated_at": system_param.updated_at.isoformat() if system_param.updated_at else None
        }
        
        return formatter.success(
            data=param_data,
            message="获取系统参数详情成功",
            resource_id=str(param_id),
            resource_type="system_params"
        )
        
    except Exception as e:
        return formatter.internal_error(f"获取系统参数详情失败: {str(e)}")

@router.post("", summary="创建系统参数")
async def create_system_param(
    request: Request,
    config_data: SysConfigCreate,
    current_user: User = DependAuth
):
    """创建系统参数"""
    formatter = ResponseFormatterV2(request)
    
    try:
        async with in_transaction("default"):
            # 检查参数键是否已存在
            existing_param = await SystemParam.get_or_none(param_key=config_data.param_key)
            if existing_param:
                return formatter.validation_error(
                    message="参数键已存在",
                    details=[APIv2ErrorDetail(
                        field="param_key",
                        code="DUPLICATE_KEY",
                        message="参数键已存在",
                        value=config_data.param_key
                    )]
                )
            
            # 记录创建参数的详细信息
            print(f"Creating system param with data: {config_data.dict()}")
            
            # 创建系统参数实例并保存（确保TimestampMixin的save方法被调用）
            new_param = SystemParam(
                param_name=config_data.param_name,
                param_key=config_data.param_key,
                param_value=config_data.param_value,
                param_type=config_data.param_type,
                description=config_data.description,
                is_editable=config_data.is_editable,
                is_system=config_data.is_system,
                is_active=config_data.is_active
            )
            await new_param.save()
            
            print(f"System param created successfully with id: {new_param.id}")
            
            param_data = {
                "id": new_param.id,
                "param_name": new_param.param_name,
                "param_key": new_param.param_key,
                "param_value": new_param.param_value,
                "param_type": new_param.param_type,
                "description": new_param.description,
                "is_editable": new_param.is_editable,
                "is_system": new_param.is_system,
                "is_active": new_param.is_active,
                "created_at": new_param.created_at.isoformat() if new_param.created_at else None,
                "updated_at": new_param.updated_at.isoformat() if new_param.updated_at else None
            }
            
            return formatter.success(
                data=param_data,
                message="系统参数创建成功",
                code=201,
                resource_id=str(new_param.id),
                resource_type="system_params"
            )
            
    except Exception as e:
        print(f"Error creating system param: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return formatter.internal_error(f"创建系统参数失败: {str(e)}")

@router.put("/{param_id}", summary="更新系统参数")
async def update_system_param(
    request: Request,
    param_id: int,
    param_name: Optional[str] = Body(None, description="参数名称"),
    param_key: Optional[str] = Body(None, description="参数键"),
    param_value: Optional[str] = Body(None, description="参数值"),
    param_type: Optional[str] = Body(None, description="参数类型"),
    description: Optional[str] = Body(None, description="描述"),
    is_editable: Optional[bool] = Body(None, description="是否允许前端编辑"),
    is_system: Optional[bool] = Body(None, description="是否系统内置"),
    is_active: Optional[bool] = Body(None, description="是否启用"),
    current_user: User = DependAuth
):
    """更新系统参数"""
    formatter = ResponseFormatterV2(request)
    
    try:
        async with in_transaction("default"):
            system_param = await SystemParam.get_or_none(id=param_id)
            if not system_param:
                return formatter.not_found("系统参数不存在", "system_param")
            
            # 如果更新参数键，检查是否与其他参数冲突
            if param_key and param_key != system_param.param_key:
                existing_param = await SystemParam.get_or_none(param_key=param_key)
                if existing_param and existing_param.id != param_id:
                    return formatter.validation_error(
                        message="参数键已存在",
                        details=[APIv2ErrorDetail(
                            field="param_key",
                            code="DUPLICATE_KEY",
                            message="参数键已存在",
                            value=param_key
                        )]
                    )
            
            # 更新系统参数
            update_data = {}
            if param_name is not None:
                update_data['param_name'] = param_name
            if param_key is not None:
                update_data['param_key'] = param_key
            if param_value is not None:
                update_data['param_value'] = param_value
            if param_type is not None:
                update_data['param_type'] = param_type
            if description is not None:
                update_data['description'] = description
            if is_editable is not None:
                update_data['is_editable'] = is_editable
            if is_system is not None:
                update_data['is_system'] = is_system
            if is_active is not None:
                update_data['is_active'] = is_active
            
            if update_data:
                await system_param.update_from_dict(update_data)
                await system_param.save()
            
            param_data = {
                "id": system_param.id,
                "param_name": system_param.param_name,
                "param_key": system_param.param_key,
                "param_value": system_param.param_value,
                "param_type": system_param.param_type,
                "description": system_param.description,
                "is_editable": system_param.is_editable,
                "is_system": system_param.is_system,
                "is_active": system_param.is_active,
                "created_at": system_param.created_at.isoformat() if system_param.created_at else None,
                "updated_at": system_param.updated_at.isoformat() if system_param.updated_at else None
            }
            
            return formatter.success(
                data=param_data,
                message="系统参数更新成功",
                resource_id=str(param_id),
                resource_type="system_params"
            )
            
    except Exception as e:
        return formatter.internal_error(f"更新系统参数失败: {str(e)}")

@router.delete("/batch", summary="批量删除系统参数", dependencies=[DependAuth])
@require_batch_delete_permission("system_param")
async def batch_delete_system_params(
    request: Request,
    batch_data: SysConfigBatchDelete,
    current_user: User = DependAuth
):
    """
    批量删除系统参数 v2版本
    
    使用标准化数据格式：{"ids": [1, 2, 3]}
    返回标准化响应格式，包含用户友好的错误提示
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        from app.services.batch_delete_service import system_param_batch_delete_service
        from tortoise.transactions import in_transaction
        
        # 获取要删除的系统参数ID列表
        param_ids = batch_data.ids
        
        if not param_ids:
            return formatter.validation_error(
                message="系统参数ID列表不能为空",
                details=[APIv2ErrorDetail(
                    field="ids",
                    code="EMPTY_LIST",
                    message="系统参数ID列表不能为空",
                    value=param_ids
                )]
            )
        
        async with in_transaction("default"):
            # 使用标准化批量删除服务
            result = await system_param_batch_delete_service.batch_delete(ids=param_ids)
            
            # 生成用户友好的响应消息
            if result.failed_count == 0:
                message = f"成功删除 {result.deleted_count} 个系统参数"
            elif result.deleted_count == 0:
                failed_reasons = [item.reason for item in result.failed]
                message = f"删除失败：{'; '.join(failed_reasons)}"
            else:
                failed_details = [f"{item.name or item.id}：{item.reason}" for item in result.failed]
                message = f"批量删除完成：成功删除 {result.deleted_count} 个，失败 {result.failed_count} 个系统参数。失败原因：{'; '.join(failed_details)}"
            
            return formatter.success(
                data=result.model_dump(),
                message=message,
                resource_type="system_params"
            )
                
    except Exception as e:
        return formatter.internal_error(
            message="批量删除系统参数时发生系统错误",
            error_detail=str(e),
            component="batch_delete_system_params"
        )


@router.delete("/{param_id}", summary="删除系统参数", dependencies=[DependAuth])
async def delete_system_param(
    request: Request,
    param_id: int = Path(..., description="参数ID"),
    current_user: User = DependAuth
):
    """删除系统参数"""
    formatter = ResponseFormatterV2(request)
    
    try:
        async with in_transaction("default"):
            system_param = await SystemParam.get_or_none(id=param_id)
            if not system_param:
                return formatter.not_found("系统参数不存在", "system_param")
            
            # 检查是否为系统内置参数
            if system_param.is_system:
                return formatter.validation_error(
                    message="系统内置参数不允许删除",
                    details=[APIv2ErrorDetail(
                        field="is_system",
                        code="SYSTEM_PARAM",
                        message="系统内置参数不允许删除",
                        value=True
                    )]
                )
            
            await system_param.delete()
            
            return formatter.success(
                message="系统参数删除成功",
                code=204
            )
            
    except Exception as e:
        return formatter.internal_error(f"删除系统参数失败: {str(e)}")


@router.get("/cached/{param_key}", summary="从缓存获取系统配置")
async def get_cached_config_value(
    request: Request,
    param_key: str = Path(..., description="参数键")
):
    """从缓存获取系统配置（无需认证）"""
    formatter = ResponseFormatterV2(request)
    
    try:
        value = config_controller.get_cached_config(param_key)
        if value is None:
            return formatter.not_found("缓存中未找到该配置", "config")
        
        return formatter.success(
            data={"param_key": param_key, "param_value": value},
            message="获取缓存配置成功",
            resource_id=param_key,
            resource_type="system_params"
        )
    except Exception as e:
        return formatter.internal_error(f"获取缓存配置失败: {str(e)}")