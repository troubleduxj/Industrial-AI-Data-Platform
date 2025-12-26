# -*- coding: utf-8 -*-
"""
动态模型 API

功能：
1. 生成动态 Pydantic 模型
2. 获取模型字段信息
3. 清除模型缓存
4. 获取缓存统计

作者：AI Assistant
日期：2025-11-03
"""

from typing import Optional
from fastapi import APIRouter, Depends, Request, Query
from app.services.dynamic_model_service import dynamic_model_service
from app.core.dependency import DependAuth
from app.models.admin import User
from app.core.response_formatter_v2 import create_formatter
from app.core.exceptions import APIException
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dynamic-models", tags=["动态模型"])


@router.post("/generate", summary="生成动态Pydantic模型")
async def generate_dynamic_model(
    request: Request,
    model_code: str = Query(..., description="模型代码"),
    version: Optional[str] = Query(None, description="模型版本（不传则使用激活版本）"),
    use_cache: bool = Query(True, description="是否使用缓存"),
    current_user: User = DependAuth
):
    """
    根据模型代码动态生成 Pydantic 模型
    
    **功能说明**:
    - 根据 t_device_data_model 配置动态生成验证模型
    - 支持字段类型映射和验证器
    - 支持模型缓存（提升性能）
    
    **使用场景**:
    - 数据导入前的验证
    - API 请求体验证
    - 数据质量检查
    
    **返回示例**:
    ```json
    {
      "code": 200,
      "message": "动态模型生成成功",
      "data": {
        "model_code": "welding_realtime_v1",
        "model_name": "焊接设备实时监控模型",
        "model_class_name": "DynamicModel_welding_realtime_v1",
        "fields_count": 15,
        "cached": true
      }
    }
    ```
    """
    formatter = create_formatter(request)
    
    try:
        logger.info(f"[动态模型API] 生成模型: model_code={model_code}, version={version}, use_cache={use_cache}")
        
        # 生成动态模型
        dynamic_model = await dynamic_model_service.generate_pydantic_model(
            model_code=model_code,
            version=version,
            use_cache=use_cache
        )
        
        # 获取模型字段数量
        fields_count = len(dynamic_model.__fields__)
        
        return formatter.success(
            data={
                'model_code': model_code,
                'model_class_name': dynamic_model.__name__,
                'fields_count': fields_count,
                'cached': use_cache,
                'fields': list(dynamic_model.__fields__.keys())
            },
            message="动态模型生成成功"
        )
        
    except APIException as e:
        logger.error(f"[动态模型API] 生成模型失败: {e.message}")
        return formatter.error(message=e.message, code=e.code, error_type=e.error_type)
    except Exception as e:
        logger.error(f"[动态模型API] 生成模型异常: {e}", exc_info=True)
        return formatter.internal_error(f"生成动态模型失败: {str(e)}")


@router.get("/fields-info", summary="获取模型字段信息")
async def get_model_fields_info(
    request: Request,
    model_code: str = Query(..., description="模型代码"),
    version: Optional[str] = Query(None, description="模型版本"),
    current_user: User = DependAuth
):
    """
    获取模型的字段信息（不生成模型，仅返回配置）
    
    **功能说明**:
    - 查询模型的所有字段配置
    - 包含字段类型、单位、验证规则等
    - 适用于前端界面展示
    
    **返回示例**:
    ```json
    {
      "code": 200,
      "data": {
        "model_code": "welding_realtime_v1",
        "model_name": "焊接设备实时监控模型",
        "model_type": "realtime",
        "device_type_code": "welding",
        "version": "1.0",
        "total_fields": 15,
        "fields": [
          {
            "field_code": "avg_current",
            "field_name": "平均电流",
            "field_type": "float",
            "unit": "A",
            "is_required": true,
            "data_range": {"min": 0, "max": 500},
            "alarm_threshold": {"warning": 400, "critical": 450}
          }
        ]
      }
    }
    ```
    """
    formatter = create_formatter(request)
    
    try:
        logger.info(f"[动态模型API] 获取字段信息: model_code={model_code}, version={version}")
        
        # 获取字段信息
        fields_info = await dynamic_model_service.get_model_fields_info(
            model_code=model_code,
            version=version
        )
        
        return formatter.success(
            data=fields_info,
            message="获取模型字段信息成功"
        )
        
    except APIException as e:
        logger.error(f"[动态模型API] 获取字段信息失败: {e.message}")
        return formatter.error(message=e.message, code=e.code, error_type=e.error_type)
    except Exception as e:
        logger.error(f"[动态模型API] 获取字段信息异常: {e}", exc_info=True)
        return formatter.internal_error(f"获取模型字段信息失败: {str(e)}")


@router.delete("/cache", summary="清除模型缓存")
async def clear_model_cache(
    request: Request,
    model_code: Optional[str] = Query(None, description="模型代码（不传则清除所有缓存）"),
    current_user: User = DependAuth
):
    """
    清除模型缓存
    
    **功能说明**:
    - 清除指定模型的所有版本缓存
    - 或清除所有模型缓存
    - 适用于模型配置更新后刷新缓存
    
    **使用场景**:
    - 修改模型配置后
    - 修改字段定义后
    - 系统维护时
    
    **返回示例**:
    ```json
    {
      "code": 200,
      "message": "缓存清除成功",
      "data": {
        "cleared": true,
        "model_code": "welding_realtime_v1"
      }
    }
    ```
    """
    formatter = create_formatter(request)
    
    try:
        logger.info(f"[动态模型API] 清除缓存: model_code={model_code}")
        
        # 清除缓存
        dynamic_model_service.clear_cache(model_code=model_code)
        
        return formatter.success(
            data={
                'cleared': True,
                'model_code': model_code or 'all'
            },
            message=f"缓存清除成功"
        )
        
    except Exception as e:
        logger.error(f"[动态模型API] 清除缓存异常: {e}", exc_info=True)
        return formatter.internal_error(f"清除缓存失败: {str(e)}")


@router.get("/cache/stats", summary="获取缓存统计")
async def get_cache_stats(
    request: Request,
    current_user: User = DependAuth
):
    """
    获取缓存统计信息
    
    **功能说明**:
    - 查看当前缓存的模型数量
    - 查看缓存的模型列表
    - 用于监控和调试
    
    **返回示例**:
    ```json
    {
      "code": 200,
      "data": {
        "total_cached_models": 3,
        "cached_keys": [
          "welding_realtime_v1:active",
          "welding_statistics_daily_v1:active",
          "welding_ai_anomaly_v1:active"
        ]
      }
    }
    ```
    """
    formatter = create_formatter(request)
    
    try:
        logger.info("[动态模型API] 获取缓存统计")
        
        # 获取缓存统计
        stats = dynamic_model_service.get_cache_stats()
        
        return formatter.success(
            data=stats,
            message="获取缓存统计成功"
        )
        
    except Exception as e:
        logger.error(f"[动态模型API] 获取缓存统计异常: {e}", exc_info=True)
        return formatter.internal_error(f"获取缓存统计失败: {str(e)}")


@router.post("/validate", summary="验证数据")
async def validate_data(
    request: Request,
    model_code: str = Query(..., description="模型代码"),
    data: dict = ...,
    current_user: User = DependAuth
):
    """
    使用动态模型验证数据
    
    **功能说明**:
    - 根据模型配置验证输入数据
    - 检查必填字段
    - 检查数据类型和范围
    - 返回验证结果和错误信息
    
    **请求体示例**:
    ```json
    {
      "avg_current": 250.5,
      "avg_voltage": 32.0,
      "spec_match_rate": 98.5
    }
    ```
    
    **返回示例**:
    ```json
    {
      "code": 200,
      "data": {
        "valid": true,
        "validated_data": {
          "avg_current": 250.5,
          "avg_voltage": 32.0,
          "spec_match_rate": 98.5
        },
        "warnings": [
          "avg_current 接近警告阈值"
        ]
      }
    }
    ```
    """
    formatter = create_formatter(request)
    
    try:
        logger.info(f"[动态模型API] 验证数据: model_code={model_code}")
        
        # 生成动态模型
        dynamic_model = await dynamic_model_service.generate_pydantic_model(
            model_code=model_code,
            use_cache=True
        )
        
        # 验证数据
        try:
            validated_instance = dynamic_model(**data)
            validated_data = validated_instance.dict()
            
            return formatter.success(
                data={
                    'valid': True,
                    'validated_data': validated_data,
                    'model_code': model_code
                },
                message="数据验证通过"
            )
            
        except Exception as validation_error:
            # 验证失败
            return formatter.error(
                message=f"数据验证失败: {str(validation_error)}",
                code=422,
                error_type="ValidationError"
            )
        
    except APIException as e:
        logger.error(f"[动态模型API] 验证数据失败: {e.message}")
        return formatter.error(message=e.message, code=e.code, error_type=e.error_type)
    except Exception as e:
        logger.error(f"[动态模型API] 验证数据异常: {e}", exc_info=True)
        return formatter.internal_error(f"验证数据失败: {str(e)}")

