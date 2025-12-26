# -*- coding: utf-8 -*-
"""
动态模型生成服务

功能：
1. 根据元数据动态生成 Pydantic 模型
2. 支持字段类型映射和验证器
3. 模型缓存机制
4. 版本管理

作者：AI Assistant
日期：2025-11-03
"""

from typing import Type, Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field, create_model, field_validator
from app.models.device import DeviceDataModel, DeviceField, DeviceFieldMapping
from app.core.exceptions import APIException
import logging

logger = logging.getLogger(__name__)
import json


class DynamicModelService:
    """
    动态模型生成服务
    
    核心功能：
    - 根据 t_device_data_model 配置动态生成 Pydantic 模型
    - 支持字段类型映射（int/float/string/datetime/boolean）
    - 支持数据范围验证
    - 支持报警阈值验证
    - 模型缓存（内存缓存）
    """
    
    # 模型缓存（内存缓存，避免重复生成）
    _model_cache: Dict[str, Type[BaseModel]] = {}
    
    # 字段类型映射（TDengine → Python）
    TYPE_MAPPING = {
        'int': int,
        'integer': int,
        'bigint': int,
        'smallint': int,
        'tinyint': int,
        'float': float,
        'double': float,
        'decimal': float,
        'string': str,
        'varchar': str,
        'nchar': str,
        'text': str,
        'timestamp': datetime,
        'datetime': datetime,
        'bool': bool,
        'boolean': bool,
    }
    
    def __init__(self):
        """初始化服务"""
        pass
    
    async def generate_pydantic_model(
        self,
        model_code: str,
        version: Optional[str] = None,
        use_cache: bool = True
    ) -> Type[BaseModel]:
        """
        根据模型代码动态生成 Pydantic 模型
        
        Args:
            model_code: 模型代码（如 'welding_realtime_v1'）
            version: 模型版本（可选，默认使用激活版本）
            use_cache: 是否使用缓存（默认 True）
        
        Returns:
            动态生成的 Pydantic 模型类
        
        Raises:
            APIException: 模型不存在或配置错误
        """
        # 1. 检查缓存
        cache_key = f"{model_code}:{version or 'active'}"
        # Disable cache temporarily to force reload of model definition
        # if use_cache and cache_key in self._model_cache:
        #     logger.debug(f"[动态模型] 从缓存加载: {cache_key}")
        #     return self._model_cache[cache_key]
        
        # 2. 查询数据模型配置
        query = DeviceDataModel.filter(model_code=model_code, is_active=True)
        if version:
            query = query.filter(version=version)
        
        data_model = await query.first()
        if not data_model:
            raise APIException(
                code=404,
                message=f"数据模型不存在或未激活: {model_code} (version={version})"
            )
        
        logger.info(f"[动态模型] 开始生成模型: {data_model.model_name} ({data_model.model_code})")
        
        # 3. 获取选中的字段配置
        selected_fields = data_model.selected_fields or []
        if not selected_fields:
            raise APIException(
                code=400,
                message=f"数据模型 '{model_code}' 未配置字段"
            )
        
        # 4. 构建字段定义
        field_definitions = {}
        field_validators_dict = {}
        
        for field_config in selected_fields:
            field_code = field_config.get('field_code')
            if not field_code:
                continue
            
            # 查询字段定义
            device_field = await DeviceField.filter(
                device_type_code=data_model.device_type_code,
                field_code=field_code,
                is_active=True
            ).first()
            
            if not device_field:
                logger.warning(f"[动态模型] 字段不存在: {field_code}，跳过")
                continue
            
            # 生成字段定义
            field_def = self._build_field_definition(device_field, field_config)
            field_definitions[field_code] = field_def
            
            # 生成验证器（如果需要）
            validators = self._build_field_validators(device_field, field_config)
            if validators:
                field_validators_dict[field_code] = validators
        
        if not field_definitions:
            raise APIException(
                code=400,
                message=f"数据模型 '{model_code}' 没有有效的字段定义"
            )
        
        # 5. 动态创建 Pydantic 模型
        model_name = f"DynamicModel_{data_model.model_code.replace('-', '_')}"
        
        # 创建基础模型
        dynamic_model = create_model(
            model_name,
            **field_definitions
        )
        
        # 6. 动态添加验证器（使用装饰器风格）
        for field_name, validators in field_validators_dict.items():
            for validator_func in validators:
                # 将验证器绑定到模型
                setattr(dynamic_model, f"validate_{field_name}", validator_func)
        
        # 7. 缓存模型
        if use_cache:
            self._model_cache[cache_key] = dynamic_model
            logger.info(f"[动态模型] 模型已缓存: {cache_key}")
        
        logger.info(f"[动态模型] 模型生成成功: {model_name}，共 {len(field_definitions)} 个字段")
        
        return dynamic_model
    
    def _build_field_definition(
        self,
        device_field: DeviceField,
        field_config: Dict[str, Any]
    ) -> tuple:
        """
        构建单个字段的定义
        
        Args:
            device_field: 设备字段模型
            field_config: 字段配置（从 selected_fields 中获取）
        
        Returns:
            字段定义元组: (type, Field(...))
        """
        # 1. 确定字段类型
        field_type_str = device_field.field_type.lower()
        python_type = self.TYPE_MAPPING.get(field_type_str, str)
        
        # 2. 确定是否必填
        is_required = field_config.get('is_required', device_field.is_required)
        
        # 3. 构建 Field 参数
        field_kwargs = {
            'description': device_field.description or device_field.field_name,
        }
        
        # 添加别名
        if 'alias' in field_config:
            field_kwargs['alias'] = field_config['alias']
        
        # 添加默认值
        if not is_required:
            default_value = device_field.default_value
            if default_value is not None:
                try:
                    # 尝试转换默认值类型
                    if python_type == int:
                        field_kwargs['default'] = int(default_value)
                    elif python_type == float:
                        field_kwargs['default'] = float(default_value)
                    elif python_type == bool:
                        field_kwargs['default'] = bool(default_value)
                    else:
                        field_kwargs['default'] = default_value
                except (ValueError, TypeError):
                    field_kwargs['default'] = None
            else:
                field_kwargs['default'] = None
        
        # 添加数据范围（用于生成 ge, le 验证）
        if device_field.data_range:
            data_range = device_field.data_range
            if isinstance(data_range, dict):
                if 'min' in data_range and python_type in (int, float):
                    field_kwargs['ge'] = data_range['min']
                if 'max' in data_range and python_type in (int, float):
                    field_kwargs['le'] = data_range['max']
        
        # 4. 返回字段定义
        if is_required:
            return (python_type, Field(**field_kwargs))
        else:
            return (Optional[python_type], Field(**field_kwargs))
    
    def _build_field_validators(
        self,
        device_field: DeviceField,
        field_config: Dict[str, Any]
    ) -> List[callable]:
        """
        构建字段验证器
        
        Args:
            device_field: 设备字段模型
            field_config: 字段配置
        
        Returns:
            验证器函数列表
        """
        validators = []
        
        # 1. 数据范围验证（已在 Field 中通过 ge/le 处理，这里作为示例保留）
        # 可以添加更复杂的验证逻辑
        
        # 2. 报警阈值验证（可选，记录警告但不阻止）
        if device_field.alarm_threshold:
            def check_alarm_threshold(cls, value):
                """检查报警阈值"""
                if value is None:
                    return value
                
                threshold = device_field.alarm_threshold
                if isinstance(threshold, dict):
                    if 'warning' in threshold and isinstance(value, (int, float)):
                        if value >= threshold['warning']:
                            logger.warning(
                                f"[动态模型] 字段 '{device_field.field_code}' 超过警告阈值: "
                                f"{value} >= {threshold['warning']}"
                            )
                    if 'critical' in threshold and isinstance(value, (int, float)):
                        if value >= threshold['critical']:
                            logger.error(
                                f"[动态模型] 字段 '{device_field.field_code}' 超过严重阈值: "
                                f"{value} >= {threshold['critical']}"
                            )
                
                return value
            
            validators.append(check_alarm_threshold)
        
        # 3. 自定义验证规则（JSON 格式）
        if device_field.validation_rule:
            # TODO: 实现自定义验证规则解析
            pass
        
        return validators
    
    async def get_model_fields_info(
        self,
        model_code: str,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取模型的字段信息（不生成模型，仅返回配置）
        
        Args:
            model_code: 模型代码
            version: 模型版本
        
        Returns:
            字段信息字典
        """
        # 查询数据模型
        query = DeviceDataModel.filter(model_code=model_code, is_active=True)
        if version:
            query = query.filter(version=version)
        
        data_model = await query.first()
        if not data_model:
            raise APIException(
                code=404,
                message=f"数据模型不存在: {model_code}"
            )
        
        # 获取字段配置
        selected_fields = data_model.selected_fields or []
        fields_info = []
        
        for field_config in selected_fields:
            field_code = field_config.get('field_code')
            if not field_code:
                continue
            
            # 查询字段定义
            device_field = await DeviceField.filter(
                device_type_code=data_model.device_type_code,
                field_code=field_code
            ).first()
            
            if not device_field:
                continue
            
            # 构建字段信息
            field_info = {
                'field_code': field_code,
                'field_name': device_field.field_name,
                'field_type': device_field.field_type,
                'unit': device_field.unit,
                'description': device_field.description,
                'is_required': field_config.get('is_required', device_field.is_required),
                'alias': field_config.get('alias'),
                'weight': field_config.get('weight', 1.0),
                'data_range': device_field.data_range,
                'alarm_threshold': device_field.alarm_threshold,
                'display_config': device_field.display_config,
            }
            
            fields_info.append(field_info)
        
        return {
            'model_code': data_model.model_code,
            'model_name': data_model.model_name,
            'model_type': data_model.model_type,
            'device_type_code': data_model.device_type_code,
            'version': data_model.version,
            'fields': fields_info,
            'total_fields': len(fields_info)
        }
    
    def clear_cache(self, model_code: Optional[str] = None):
        """
        清除模型缓存
        
        Args:
            model_code: 模型代码（可选，不传则清除所有缓存）
        """
        if model_code:
            # 清除特定模型的所有版本缓存
            keys_to_remove = [k for k in self._model_cache.keys() if k.startswith(model_code)]
            for key in keys_to_remove:
                del self._model_cache[key]
            logger.info(f"[动态模型] 已清除缓存: {model_code} ({len(keys_to_remove)} 个版本)")
        else:
            # 清除所有缓存
            count = len(self._model_cache)
            self._model_cache.clear()
            logger.info(f"[动态模型] 已清除所有缓存 ({count} 个模型)")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        return {
            'total_cached_models': len(self._model_cache),
            'cached_keys': list(self._model_cache.keys())
        }


# 创建全局实例
dynamic_model_service = DynamicModelService()

