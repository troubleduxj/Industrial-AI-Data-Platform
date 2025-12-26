"""
元数据管理 API V2 接口
提供设备字段定义、数据模型、字段映射的RESTful API
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Request, Query, Path, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.response_formatter_v2 import create_formatter
from app.core.dependency import DependAuth
from app.core.exceptions import APIException
from app.core.tdengine_config import TDengineConfigManager
from app.models.admin import User
from app.services.metadata_service import MetadataService
from app.schemas.metadata import (
    DeviceFieldCreate, DeviceFieldUpdate, DeviceFieldResponse,
    DeviceDataModelCreate, DeviceDataModelUpdate, DeviceDataModelResponse,
    DeviceFieldMappingCreate, DeviceFieldMappingUpdate, DeviceFieldMappingResponse,
    ModelExecutionLogResponse,
    ModelStatistics
)
import logging

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/metadata", tags=["元数据管理"])


# =====================================================
# 设备字段定义 API
# =====================================================

@router.post("/fields", summary="创建设备字段定义", response_model=None)
async def create_field(
    request: Request,
    field_data: DeviceFieldCreate = Body(...),
    current_user: User = DependAuth
):
    """
    创建设备字段定义
    
    - **device_type_code**: 设备类型代码
    - **field_name**: 字段名称（中文）
    - **field_code**: 字段代码（英文，对应TDengine列名）
    - **field_type**: 字段类型
    - **is_monitoring_key**: 是否为实时监控关键字段
    - **is_ai_feature**: 是否为AI分析特征字段
    """
    formatter = create_formatter(request)
    try:
        field = await MetadataService.create_field(field_data)
        return formatter.success(
            data=DeviceFieldResponse.model_validate(field).model_dump(mode='json'),
            message="创建设备字段成功"
        )
    except Exception as e:
        logger.error(f"创建设备字段失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"创建设备字段失败: {str(e)}")


@router.get("/fields", summary="获取设备字段列表", response_model=None)
async def get_fields(
    request: Request,
    device_type_code: Optional[str] = Query(None, description="设备类型代码"),
    field_category: Optional[str] = Query(None, description="字段分类"),
    is_monitoring_key: Optional[bool] = Query(None, description="是否为监控关键字段"),
    is_ai_feature: Optional[bool] = Query(None, description="是否为AI特征"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=1000, description="每页数量"),
    current_user: User = DependAuth
):
    """
    获取设备字段列表（分页）
    
    支持按设备类型、字段分类、监控标记、AI标记筛选
    """
    formatter = create_formatter(request)
    try:
        fields, total = await MetadataService.get_fields(
            device_type_code=device_type_code,
            field_category=field_category,
            is_monitoring_key=is_monitoring_key,
            is_ai_feature=is_ai_feature,
            is_active=is_active,
            search=search,
            page=page,
            page_size=page_size
        )
        
        data = [DeviceFieldResponse.model_validate(f).model_dump(mode='json') for f in fields]
        
        return formatter.paginated_success(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            message="获取设备字段列表成功"
        )
    except Exception as e:
        logger.error(f"获取设备字段列表失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"获取设备字段列表失败: {str(e)}")


@router.get("/fields/{field_id}", summary="获取设备字段详情", response_model=None)
async def get_field(
    request: Request,
    field_id: int = Path(..., description="字段ID"),
    current_user: User = DependAuth
):
    """获取设备字段详情"""
    formatter = create_formatter(request)
    try:
        field = await MetadataService.get_field_by_id(field_id)
        if not field:
            return formatter.error(message="字段不存在", code=404)
        
        return formatter.success(
            data=DeviceFieldResponse.model_validate(field).model_dump(mode='json'),
            message="获取设备字段详情成功"
        )
    except Exception as e:
        logger.error(f"获取设备字段详情失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"获取设备字段详情失败: {str(e)}")


@router.put("/fields/{field_id}", summary="更新设备字段", response_model=None)
async def update_field(
    request: Request,
    field_id: int = Path(..., description="字段ID"),
    field_data: DeviceFieldUpdate = Body(...),
    current_user: User = DependAuth
):
    """更新设备字段"""
    formatter = create_formatter(request)
    try:
        field = await MetadataService.update_field(field_id, field_data)
        if not field:
            return formatter.error(message="字段不存在", code=404)
        
        return formatter.success(
            data=DeviceFieldResponse.model_validate(field).model_dump(mode='json'),
            message="更新设备字段成功"
        )
    except Exception as e:
        logger.error(f"更新设备字段失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"更新设备字段失败: {str(e)}")


@router.delete("/fields/{field_id}", summary="删除设备字段", response_model=None)
async def delete_field(
    request: Request,
    field_id: int = Path(..., description="字段ID"),
    current_user: User = DependAuth
):
    """删除设备字段（软删除）"""
    formatter = create_formatter(request)
    try:
        success = await MetadataService.delete_field(field_id)
        if not success:
            return formatter.error(message="字段不存在", code=404)
        
        return formatter.success(message="删除设备字段成功")
    except Exception as e:
        logger.error(f"删除设备字段失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"删除设备字段失败: {str(e)}")


@router.delete("/fields/batch/{device_type_code}", summary="批量删除设备类型字段")
async def batch_delete_fields(
    request: Request,
    device_type_code: str,
    current_user: User = DependAuth
):
    """
    批量删除指定设备类型下的所有字段
    
    - **device_type_code**: 设备类型代码
    """
    formatter = create_formatter(request)
    try:
        count = await MetadataService.delete_fields_by_device_type(device_type_code)
        return formatter.success(
            data={"deleted_count": count},
            message=f"成功删除 {count} 个字段"
        )
    except APIException as e:
        return formatter.error(message=e.message, code=e.code)
    except Exception as e:
        logger.error(f"批量删除设备字段失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"批量删除设备字段失败: {str(e)}")


class BatchDeleteRequest(BaseModel):
    ids: List[int]

@router.post("/fields/batch-delete", summary="批量删除选中字段")
async def batch_delete_selected_fields(
    request: Request,
    delete_req: BatchDeleteRequest,
    current_user: User = DependAuth
):
    """批量删除选中的字段"""
    formatter = create_formatter(request)
    try:
        count = await MetadataService.delete_fields_by_ids(delete_req.ids)
        return formatter.success(
            data={"deleted_count": count},
            message=f"成功删除 {count} 个字段"
        )
    except APIException as e:
        return formatter.error(message=e.message, code=e.code)
    except Exception as e:
        logger.error(f"批量删除设备字段失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"批量删除设备字段失败: {str(e)}")


# =====================================================
# 数据模型 API
# =====================================================

@router.post("/models", summary="创建数据模型", response_model=None)
async def create_model(
    request: Request,
    model_data: DeviceDataModelCreate = Body(...),
    current_user: User = DependAuth
):
    """
    创建数据模型
    
    支持三种模型类型：
    - **realtime**: 实时监控模型
    - **statistics**: 统计分析模型（需提供aggregation_config）
    - **ai_analysis**: AI分析模型（需提供ai_config）
    """
    formatter = create_formatter(request)
    try:
        # 设置创建人
        if not model_data.created_by:
            model_data.created_by = current_user.id
        
        model = await MetadataService.create_model(model_data)
        return formatter.success(
            data=DeviceDataModelResponse.model_validate(model).model_dump(mode='json'),
            message="创建数据模型成功"
        )
    except APIException as e:
        return formatter.error(message=e.message, code=e.code)
    except Exception as e:
        logger.error(f"创建数据模型失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"创建数据模型失败: {str(e)}")


@router.get("/models", summary="获取数据模型列表", response_model=None)
async def get_models(
    request: Request,
    device_type_code: Optional[str] = Query(None, description="设备类型代码"),
    model_type: Optional[str] = Query(None, description="模型类型：realtime/statistics/ai_analysis"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    current_user: User = DependAuth
):
    """获取数据模型列表（分页）"""
    formatter = create_formatter(request)
    try:
        models, total = await MetadataService.get_models(
            device_type_code=device_type_code,
            model_type=model_type,
            is_active=is_active,
            search=search,
            page=page,
            page_size=page_size
        )
        
        # 使用 mode='json' 确保 datetime 等类型正确序列化
        data = [DeviceDataModelResponse.model_validate(m).model_dump(mode='json') for m in models]
        
        return formatter.paginated_success(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            message="获取数据模型列表成功"
        )
    except Exception as e:
        logger.error(f"获取数据模型列表失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"获取数据模型列表失败: {str(e)}")


@router.get("/models/{model_id}", summary="获取数据模型详情", response_model=None)
async def get_model(
    request: Request,
    model_id: int = Path(..., description="模型ID"),
    current_user: User = DependAuth
):
    """获取数据模型详情"""
    formatter = create_formatter(request)
    try:
        model = await MetadataService.get_model_by_id(model_id)
        if not model:
            return formatter.error(message="数据模型不存在", code=404)
        
        return formatter.success(
            data=DeviceDataModelResponse.model_validate(model).model_dump(mode='json'),
            message="获取数据模型详情成功"
        )
    except Exception as e:
        logger.error(f"获取数据模型详情失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"获取数据模型详情失败: {str(e)}")


@router.get("/models/code/{model_code}", summary="根据编码获取数据模型", response_model=None)
async def get_model_by_code(
    request: Request,
    model_code: str = Path(..., description="模型编码"),
    version: Optional[str] = Query(None, description="模型版本"),
    current_user: User = DependAuth
):
    """根据模型编码获取数据模型（默认获取激活版本）"""
    formatter = create_formatter(request)
    try:
        model = await MetadataService.get_model_by_code(model_code, version)
        if not model:
            return formatter.error(message="数据模型不存在", code=404)
        
        return formatter.success(
            data=DeviceDataModelResponse.model_validate(model).model_dump(mode='json'),
            message="获取数据模型详情成功"
        )
    except Exception as e:
        logger.error(f"获取数据模型详情失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"获取数据模型详情失败: {str(e)}")


@router.put("/models/{model_id}", summary="更新数据模型", response_model=None)
async def update_model(
    request: Request,
    model_id: int = Path(..., description="模型ID"),
    model_data: DeviceDataModelUpdate = Body(...),
    current_user: User = DependAuth
):
    """更新数据模型"""
    formatter = create_formatter(request)
    try:
        # 设置更新人
        if not model_data.updated_by:
            model_data.updated_by = current_user.id
        
        model = await MetadataService.update_model(model_id, model_data)
        if not model:
            return formatter.error(message="数据模型不存在", code=404)
        
        return formatter.success(
            data=DeviceDataModelResponse.model_validate(model).model_dump(mode='json'),
            message="更新数据模型成功"
        )
    except Exception as e:
        logger.error(f"更新数据模型失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"更新数据模型失败: {str(e)}")


@router.delete("/models/{model_id}", summary="删除数据模型", response_model=None)
async def delete_model(
    request: Request,
    model_id: int = Path(..., description="模型ID"),
    current_user: User = DependAuth
):
    """删除数据模型（软删除）"""
    formatter = create_formatter(request)
    try:
        success = await MetadataService.delete_model(model_id)
        if not success:
            return formatter.error(message="数据模型不存在", code=404)
        
        return formatter.success(message="删除数据模型成功")
    except Exception as e:
        logger.error(f"删除数据模型失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"删除数据模型失败: {str(e)}")


@router.post("/models/{model_id}/activate", summary="激活数据模型", response_model=None)
async def activate_model(
    request: Request,
    model_id: int = Path(..., description="模型ID"),
    current_user: User = DependAuth
):
    """
    激活数据模型
    
    激活后，同设备类型、同模型类型的其他模型将被自动停用
    """
    formatter = create_formatter(request)
    try:
        model = await MetadataService.activate_model(model_id)
        if not model:
            return formatter.error(message="数据模型不存在", code=404)
        
        return formatter.success(
            data=DeviceDataModelResponse.model_validate(model).model_dump(mode='json'),
            message="激活数据模型成功"
        )
    except Exception as e:
        logger.error(f"激活数据模型失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"激活数据模型失败: {str(e)}")


# =====================================================
# 字段映射 API
# =====================================================

@router.post("/mappings", summary="创建字段映射", response_model=None)
async def create_mapping(
    request: Request,
    mapping_data: DeviceFieldMappingCreate = Body(...),
    current_user: User = DependAuth
):
    """
    创建字段映射（PostgreSQL ↔ TDengine）
    
    - **device_type_code**: 设备类型代码
    - **tdengine_database**: TDengine数据库名
    - **tdengine_stable**: TDengine超级表名
    - **tdengine_column**: TDengine列名
    - **device_field_id**: 关联的字段定义ID
    - **transform_rule**: 数据转换规则（可选）
    - **is_tag**: 是否为TAG列
    """
    formatter = create_formatter(request)
    try:
        mapping = await MetadataService.create_mapping(mapping_data)
        return formatter.success(
            data=DeviceFieldMappingResponse.model_validate(mapping).model_dump(mode='json'),
            message="创建字段映射成功"
        )
    except Exception as e:
        logger.error(f"创建字段映射失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"创建字段映射失败: {str(e)}")


@router.get("/mappings", summary="获取字段映射列表", response_model=None)
async def get_mappings(
    request: Request,
    device_type_code: Optional[str] = Query(None, description="设备类型代码"),
    tdengine_stable: Optional[str] = Query(None, description="TDengine超级表名"),
    is_tag: Optional[bool] = Query(None, description="是否为TAG列"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    current_user: User = DependAuth
):
    """获取字段映射列表（分页）"""
    formatter = create_formatter(request)
    try:
        mappings, total = await MetadataService.get_mappings(
            device_type_code=device_type_code,
            tdengine_stable=tdengine_stable,
            is_tag=is_tag,
            is_active=is_active,
            page=page,
            page_size=page_size
        )
        
        data = [DeviceFieldMappingResponse.model_validate(m).model_dump(mode='json') for m in mappings]
        
        return formatter.paginated_success(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            message="获取字段映射列表成功"
        )
    except Exception as e:
        logger.error(f"获取字段映射列表失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"获取字段映射列表失败: {str(e)}")


@router.get("/mappings/{mapping_id}", summary="获取字段映射详情", response_model=None)
async def get_mapping(
    request: Request,
    mapping_id: int = Path(..., description="映射ID"),
    current_user: User = DependAuth
):
    """获取字段映射详情"""
    formatter = create_formatter(request)
    try:
        mapping = await MetadataService.get_mapping_by_id(mapping_id)
        if not mapping:
            return formatter.error(message="字段映射不存在", code=404)
        
        return formatter.success(
            data=DeviceFieldMappingResponse.model_validate(mapping).model_dump(mode='json'),
            message="获取字段映射详情成功"
        )
    except Exception as e:
        logger.error(f"获取字段映射详情失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"获取字段映射详情失败: {str(e)}")


@router.put("/mappings/{mapping_id}", summary="更新字段映射", response_model=None)
async def update_mapping(
    request: Request,
    mapping_id: int = Path(..., description="映射ID"),
    mapping_data: DeviceFieldMappingUpdate = Body(...),
    current_user: User = DependAuth
):
    """更新字段映射"""
    formatter = create_formatter(request)
    try:
        mapping = await MetadataService.update_mapping(mapping_id, mapping_data)
        if not mapping:
            return formatter.error(message="字段映射不存在", code=404)
        
        return formatter.success(
            data=DeviceFieldMappingResponse.model_validate(mapping).model_dump(mode='json'),
            message="更新字段映射成功"
        )
    except Exception as e:
        logger.error(f"更新字段映射失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"更新字段映射失败: {str(e)}")


@router.delete("/mappings/{mapping_id}", summary="删除字段映射", response_model=None)
async def delete_mapping(
    request: Request,
    mapping_id: int = Path(..., description="映射ID"),
    current_user: User = DependAuth
):
    """删除字段映射"""
    formatter = create_formatter(request)
    try:
        success = await MetadataService.delete_mapping(mapping_id)
        if not success:
            return formatter.error(message="字段映射不存在", code=404)
        
        return formatter.success(message="删除字段映射成功")
    except Exception as e:
        logger.error(f"删除字段映射失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"删除字段映射失败: {str(e)}")


@router.post("/mappings/batch-delete", summary="批量删除字段映射")
async def batch_delete_mappings(
    request: Request,
    delete_req: BatchDeleteRequest,
    current_user: User = DependAuth
):
    """批量删除选中的字段映射"""
    formatter = create_formatter(request)
    try:
        count = await MetadataService.delete_mappings_by_ids(delete_req.ids)
        return formatter.success(
            data={"deleted_count": count},
            message=f"成功删除 {count} 个字段映射"
        )
    except Exception as e:
        logger.error(f"批量删除字段映射失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"批量删除字段映射失败: {str(e)}")


# =====================================================
# 执行日志 API
# =====================================================

@router.get("/execution-logs", summary="获取模型执行日志列表", response_model=None)
async def get_execution_logs(
    request: Request,
    model_id: Optional[int] = Query(None, description="模型ID"),
    model_code: Optional[str] = Query(None, description="模型编码"),
    execution_type: Optional[str] = Query(None, description="执行类型"),
    status: Optional[str] = Query(None, description="执行状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    current_user: User = DependAuth
):
    """获取模型执行日志列表（分页）"""
    formatter = create_formatter(request)
    try:
        logs, total = await MetadataService.get_execution_logs(
            model_id=model_id,
            model_code=model_code,
            execution_type=execution_type,
            status=status,
            page=page,
            page_size=page_size
        )
        
        data = [ModelExecutionLogResponse.model_validate(log).model_dump(mode='json') for log in logs]
        
        return formatter.paginated_success(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            message="获取执行日志列表成功"
        )
    except Exception as e:
        logger.error(f"获取执行日志列表失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"获取执行日志列表失败: {str(e)}")


# =====================================================
# 统计 API
# =====================================================

@router.get("/statistics", summary="获取模型统计信息", response_model=None)
async def get_statistics(
    request: Request,
    current_user: User = DependAuth
):
    """
    获取模型统计信息
    
    包括：
    - 模型总数、激活数
    - 各类型模型数量
    - 执行总次数、成功率
    - 平均执行时间
    """
    formatter = create_formatter(request)
    try:
        stats = await MetadataService.get_model_statistics()
        return formatter.success(
            data=ModelStatistics(**stats).model_dump(mode='json'),
            message="获取统计信息成功"
        )
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"获取统计信息失败: {str(e)}")


@router.get("/schema/diff", summary="获取TDengine表结构差异", response_model=None)
async def get_schema_diff(
    request: Request,
    device_type_code: str = Query(..., description="设备类型代码"),
    current_user: User = DependAuth
):
    """
    获取TDengine表结构与系统定义的差异
    """
    formatter = create_formatter(request)
    try:
        diff_result = await MetadataService.compare_schema(device_type_code)
        
        if diff_result.get('status') == 'error':
             return formatter.error(message=diff_result.get('message'), code=500)
             
        return formatter.success(
            data=diff_result,
            message="获取结构差异成功"
        )
    except APIException as e:
         return formatter.error(message=e.message, code=e.code)
    except Exception as e:
        logger.error(f"获取结构差异失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"获取结构差异失败: {str(e)}")


# =====================================================
# 配置 API
# =====================================================

@router.get("/config/tdengine-default", summary="获取默认TDengine配置")
async def get_tdengine_default_config(request: Request, current_user: User = DependAuth):
    """
    获取默认TDengine配置
    
    返回当前后端使用的TDengine连接配置，用于前端同步默认值
    """
    formatter = create_formatter(request)
    try:
        manager = TDengineConfigManager()
        config = manager.get_server_config()
        
        return formatter.success(
            data={
                "database": config.database,
                "host": config.host,
                "port": config.port,
                "user": config.user
            },
            message="获取TDengine配置成功"
        )
    except Exception as e:
        logger.error(f"获取TDengine配置失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"获取TDengine配置失败: {str(e)}")


# =====================================================
# 导入导出 API
# =====================================================

@router.get("/export", summary="导出元数据配置")
async def export_metadata(
    request: Request,
    device_type_code: Optional[str] = Query(None, description="设备类型代码"),
    current_user: User = DependAuth
):
    """
    导出元数据配置（JSON格式）
    包括设备类型、字段定义、数据模型和字段映射
    """
    formatter = create_formatter(request)
    try:
        data = await MetadataService.export_metadata(device_type_code)
        return formatter.success(data, "导出成功")
    except Exception as e:
        logger.error(f"导出元数据失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"导出失败: {str(e)}")

@router.post("/import", summary="导入元数据配置")
async def import_metadata(
    request: Request,
    data: Dict[str, Any] = Body(..., description="元数据配置JSON"),
    current_user: User = DependAuth
):
    """
    导入元数据配置
    """
    formatter = create_formatter(request)
    try:
        stats = await MetadataService.import_metadata(data, user_id=current_user.id)
        return formatter.success(stats, "导入成功")
    except Exception as e:
        logger.error(f"导入元数据失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"导入失败: {str(e)}")

