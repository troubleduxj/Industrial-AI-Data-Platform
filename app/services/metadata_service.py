"""
元数据管理服务
提供设备字段定义、数据模型、字段映射的业务逻辑
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from tortoise.exceptions import DoesNotExist, IntegrityError
from tortoise.expressions import Q
from tortoise.queryset import QuerySet

from app.models.device import DeviceField, DeviceDataModel, DeviceFieldMapping, ModelExecutionLog, DeviceType, DeviceDataModelHistory
from app.models.notification import Notification
from app.schemas.metadata import (
    DeviceFieldCreate, DeviceFieldUpdate,
    DeviceDataModelCreate, DeviceDataModelUpdate,
    DeviceFieldMappingCreate, DeviceFieldMappingUpdate,
    ModelExecutionLogCreate
)
from app.core.exceptions import APIException
from app.core.tdengine_connector import TDengineConnector
import logging
import httpx

logger = logging.getLogger(__name__)


class MetadataService:
    """元数据管理服务"""
    
    # =====================================================
    # 设备字段定义管理
    # =====================================================
    
    @staticmethod
    async def create_field(field_data: DeviceFieldCreate) -> DeviceField:
        """创建设备字段定义"""
        try:
            field = await DeviceField.create(**field_data.model_dump())
            logger.info(f"创建设备字段成功: {field.field_name} ({field.field_code})")
            return field
        except Exception as e:
            logger.error(f"创建设备字段失败: {str(e)}")
            raise
    
    @staticmethod
    async def get_field_by_id(field_id: int) -> Optional[DeviceField]:
        """根据ID获取字段定义"""
        try:
            return await DeviceField.get(id=field_id)
        except DoesNotExist:
            return None
    
    @staticmethod
    async def get_fields(
        device_type_code: Optional[str] = None,
        field_category: Optional[str] = None,
        is_monitoring_key: Optional[bool] = None,
        is_ai_feature: Optional[bool] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[DeviceField], int]:
        """获取字段定义列表（分页）"""
        query = DeviceField.all()
        
        # 构建查询条件
        if device_type_code:
            query = query.filter(device_type_code=device_type_code)
        if field_category:
            query = query.filter(field_category=field_category)
        if is_monitoring_key is not None:
            query = query.filter(is_monitoring_key=is_monitoring_key)
        if is_ai_feature is not None:
            query = query.filter(is_ai_feature=is_ai_feature)
        if is_active is not None:
            query = query.filter(is_active=is_active)
        if search:
            query = query.filter(
                Q(field_name__icontains=search) | 
                Q(field_code__icontains=search) |
                Q(description__icontains=search)
            )
        
        # 统计总数
        total = await query.count()
        
        # 分页查询
        offset = (page - 1) * page_size
        fields = await query.order_by('device_type_code', 'sort_order').offset(offset).limit(page_size)
        
        return fields, total
    
    @staticmethod
    async def update_field(field_id: int, field_data: DeviceFieldUpdate) -> Optional[DeviceField]:
        """更新字段定义"""
        try:
            field = await DeviceField.get(id=field_id)
            update_data = field_data.model_dump(exclude_unset=True)
            await field.update_from_dict(update_data).save()
            logger.info(f"更新设备字段成功: {field.field_name}")
            return field
        except DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"更新设备字段失败: {str(e)}")
            raise
    
    @staticmethod
    async def delete_field(field_id: int) -> bool:
        """删除字段定义（软删除）"""
        try:
            field = await DeviceField.get(id=field_id)
            
            # 检查字段是否被激活的模型引用
            active_models = await DeviceDataModel.filter(
                device_type_code=field.device_type_code,
                is_active=True
            ).all()
            
            for model in active_models:
                # selected_fields 是 List[Dict] (JSONField)
                # 格式: [{"field_code": "voltage", ...}, ...]
                selected_fields = model.selected_fields or []
                for sf in selected_fields:
                    if isinstance(sf, dict) and sf.get("field_code") == field.field_code:
                        raise APIException(
                            message=f"字段 '{field.field_name}' 正被模型 '{model.model_name}' 使用，无法删除。请先从模型中移除该字段。",
                            code=400
                        )
            
            field.is_active = False
            await field.save()
            
            # 同时删除（禁用）关联的字段映射
            await DeviceFieldMapping.filter(device_field_id=field.id).update(is_active=False)
            
            logger.info(f"删除设备字段成功: {field.field_name}")
            return True
        except DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"删除设备字段失败: {str(e)}")
            raise
    
    @staticmethod
    async def delete_fields_by_device_type(device_type_code: str) -> int:
        """批量删除设备类型下的所有字段"""
        try:
            # 1. 获取该类型下的所有激活字段
            fields = await DeviceField.filter(device_type_code=device_type_code, is_active=True).all()
            if not fields:
                return 0

            # 2. 检查是否被模型引用
            active_models = await DeviceDataModel.filter(
                device_type_code=device_type_code,
                is_active=True
            ).all()
            
            used_fields = set()
            for model in active_models:
                selected_fields = model.selected_fields or []
                for sf in selected_fields:
                    if isinstance(sf, dict):
                        used_fields.add(sf.get("field_code"))
            
            # 3. 检查冲突
            conflicts = []
            for f in fields:
                if f.field_code in used_fields:
                    conflicts.append(f.field_name)
            
            if conflicts:
                raise APIException(
                    message=f"以下字段正被模型引用，无法批量删除: {', '.join(conflicts[:5])}{' 等' if len(conflicts)>5 else ''}。请先从模型中移除这些字段。",
                    code=400
                )
                
            # 4. 执行删除
            count = await DeviceField.filter(device_type_code=device_type_code, is_active=True).update(is_active=False)
            
            # 同时删除关联的字段映射
            await DeviceFieldMapping.filter(device_type_code=device_type_code, is_active=True).update(is_active=False)
            
            logger.info(f"批量删除设备字段成功: {device_type_code}, 数量: {count}")
            return count
        except Exception as e:
            logger.error(f"批量删除设备字段失败: {str(e)}")
            raise

    @staticmethod
    async def delete_fields_by_ids(field_ids: List[int]) -> int:
        """批量删除指定ID的字段"""
        try:
            # 1. 获取字段
            fields = await DeviceField.filter(id__in=field_ids, is_active=True).all()
            if not fields:
                return 0
            
            device_types = set(f.device_type_code for f in fields)
            field_codes = set(f.field_code for f in fields)
            
            # 2. 检查引用
            active_models = await DeviceDataModel.filter(
                device_type_code__in=device_types,
                is_active=True
            ).all()
            
            conflicts = []
            for model in active_models:
                selected = model.selected_fields or []
                for sf in selected:
                    if isinstance(sf, dict) and sf.get("field_code") in field_codes:
                         # Find which field
                         fname = next((f.field_name for f in fields if f.field_code == sf.get("field_code")), "?")
                         if fname not in conflicts:
                             conflicts.append(fname)
            
            if conflicts:
                 raise APIException(
                    message=f"以下字段正被模型引用，无法删除: {', '.join(conflicts[:5])}{' 等' if len(conflicts)>5 else ''}。请先从模型中移除这些字段。",
                    code=400
                )
            
            # 3. 执行删除
            count = await DeviceField.filter(id__in=field_ids).update(is_active=False)
            
            # 同时删除关联的字段映射
            await DeviceFieldMapping.filter(device_field_id__in=field_ids).update(is_active=False)
            
            logger.info(f"批量删除设备字段成功: {field_ids}, 数量: {count}")
            return count
        except Exception as e:
            logger.error(f"批量删除设备字段失败: {str(e)}")
            raise

    # =====================================================
    # 数据模型管理
    # =====================================================
    
    @staticmethod
    async def create_model(model_data: DeviceDataModelCreate) -> DeviceDataModel:
        """创建数据模型"""
        try:
            # 1. 验证设备类型是否存在
            device_type = await DeviceType.get_or_none(type_code=model_data.device_type_code)
            if not device_type:
                raise APIException(message=f"设备类型 {model_data.device_type_code} 不存在", code=400)

            # 转换 Pydantic 模型为字典
            model_dict = model_data.model_dump()
            
            # 处理嵌套的 Pydantic 模型
            model_dict['selected_fields'] = [f.model_dump() for f in model_data.selected_fields]
            if model_data.aggregation_config:
                model_dict['aggregation_config'] = model_data.aggregation_config.model_dump()
            if model_data.ai_config:
                model_dict['ai_config'] = model_data.ai_config.model_dump()
            
            logger.info(f"Creating model with data: {model_dict}")
            model = DeviceDataModel(**model_dict)
            await model.save()

            logger.info(f"创建数据模型成功: {model.model_name} ({model.model_code})")
            return model
        except IntegrityError as e:
            error_msg = str(e)
            logger.error(f"数据库完整性错误: {error_msg}")
            if "fk_data_model_device_type" in error_msg:
                 raise APIException(message=f"设备类型 {model_data.device_type_code} 不存在", code=400)
            elif "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
                 # 解析冲突的具体键值
                 if "uk_model_code_version" in error_msg or "(model_code, version)" in error_msg:
                     # 检查是否存在被软删除的同名模型
                     deleted_model = await DeviceDataModel.filter(
                         model_code=model_data.model_code, 
                         version=model_data.version, 
                         is_active=False
                     ).first()
                     
                     if deleted_model:
                         raise APIException(
                             message=f"模型编码 {model_data.model_code} (版本 {model_data.version}) 已存在但被标记为删除。请使用其他版本号或联系管理员恢复。",
                             code=400
                         )
                     else:
                         raise APIException(message=f"模型编码 {model_data.model_code} (版本 {model_data.version}) 已存在", code=400)
                 else:
                     raise APIException(message=f"数据库唯一约束冲突: {error_msg}", code=400)
            else:
                 raise APIException(message=f"数据库操作失败: {error_msg}", code=400)
        except APIException:
            raise
        except Exception as e:
            logger.error(f"创建数据模型失败: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def get_model_by_id(model_id: int) -> Optional[DeviceDataModel]:
        """根据ID获取数据模型"""
        try:
            return await DeviceDataModel.get(id=model_id)
        except DoesNotExist:
            return None
    
    @staticmethod
    async def get_model_by_code(model_code: str, version: Optional[str] = None) -> Optional[DeviceDataModel]:
        """根据编码获取数据模型"""
        try:
            query = DeviceDataModel.filter(model_code=model_code)
            if version:
                query = query.filter(version=version)
            else:
                # 获取最新版本
                query = query.filter(is_active=True)
            return await query.first()
        except Exception:
            return None
    
    @staticmethod
    async def get_models(
        device_type_code: Optional[str] = None,
        model_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[DeviceDataModel], int]:
        """获取数据模型列表（分页）"""
        try:
            logger.info(f"get_models params: device_type_code={device_type_code}, search='{search}'")
            query = DeviceDataModel.all()
            
            # 构建查询条件
            if device_type_code:
                query = query.filter(device_type_code=device_type_code)
            if model_type:
                query = query.filter(model_type=model_type)
            if is_active is not None:
                query = query.filter(is_active=is_active)
            if search:
                logger.info(f"Applying search filter: {search}")
                q_obj = Q(model_name__icontains=search) | Q(model_code__icontains=search)
                logger.info(f"Search Q object type: {type(q_obj)}")
                query = query.filter(q_obj)
            
            # 统计总数
            total = await query.count()
            
            # 分页查询
            offset = (page - 1) * page_size
            models = await query.order_by('-created_at').offset(offset).limit(page_size)
            
            return models, total
        except Exception as e:
            logger.error(f"get_models failed: {str(e)}", exc_info=True)
            raise

    @staticmethod
    async def execute_model(model_code: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行数据模型分析
        TODO: 实现真实的模型执行逻辑 (统计/AI)
        """
        model = await DeviceDataModel.get_or_none(model_code=model_code)
        if not model:
            raise Exception(f"模型 {model_code} 不存在")
            
        # 模拟执行结果
        return {
            "model": model_code,
            "timestamp": datetime.now().isoformat(),
            "result": "success",
            "score": 0.95,
            "anomalies": []
        }
    
    @staticmethod
    async def create_snapshot(model: DeviceDataModel, change_type: str, change_reason: str = None, user_id: int = None):
        """创建模型快照"""
        try:
            content = {
                "model_name": model.model_name,
                "model_code": model.model_code,
                "model_type": model.model_type,
                "selected_fields": model.selected_fields,
                "aggregation_config": model.aggregation_config,
                "ai_config": model.ai_config,
                "is_active": model.is_active,
                "version": model.version
            }
            
            await DeviceDataModelHistory.create(
                model=model,
                version=model.version,
                content=content,
                change_type=change_type,
                change_reason=change_reason,
                created_by=user_id
            )
            logger.info(f"创建模型快照成功: {model.model_code} v{model.version}")
        except Exception as e:
            logger.error(f"创建模型快照失败: {str(e)}")
            # 快照失败不应阻断主流程

    @staticmethod
    async def update_model(model_id: int, model_data: DeviceDataModelUpdate, user_id: int = None) -> Optional[DeviceDataModel]:
        """更新数据模型"""
        try:
            model = await DeviceDataModel.get(id=model_id)
            
            # 创建更新前的快照
            await MetadataService.create_snapshot(
                model=model, 
                change_type="update", 
                change_reason="Update via API",
                user_id=user_id
            )
            
            update_dict = model_data.model_dump(exclude_unset=True)
            
            # 处理嵌套的 Pydantic 模型
            if 'selected_fields' in update_dict and update_dict['selected_fields']:
                update_dict['selected_fields'] = [f.model_dump() if hasattr(f, 'model_dump') else f for f in update_dict['selected_fields']]
            if 'aggregation_config' in update_dict and update_dict['aggregation_config']:
                if hasattr(update_dict['aggregation_config'], 'model_dump'):
                    update_dict['aggregation_config'] = update_dict['aggregation_config'].model_dump()
            if 'ai_config' in update_dict and update_dict['ai_config']:
                if hasattr(update_dict['ai_config'], 'model_dump'):
                    update_dict['ai_config'] = update_dict['ai_config'].model_dump()
            
            await model.update_from_dict(update_dict).save()
            logger.info(f"更新数据模型成功: {model.model_name}")
            return model
        except DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"更新数据模型失败: {str(e)}")
            raise
    
    @staticmethod
    async def delete_model(model_id: int) -> bool:
        """删除数据模型（软删除）"""
        try:
            model = await DeviceDataModel.get(id=model_id)
            model.is_active = False
            await model.save()
            logger.info(f"删除数据模型成功: {model.model_name}")
            return True
        except DoesNotExist:
            return False
    
    @staticmethod
    async def activate_model(model_id: int) -> Optional[DeviceDataModel]:
        """激活数据模型（同时停用同类型的其他模型）"""
        try:
            model = await DeviceDataModel.get(id=model_id)
            
            # 停用同设备类型、同模型类型的其他激活模型
            await DeviceDataModel.filter(
                device_type_code=model.device_type_code,
                model_type=model.model_type,
                is_active=True
            ).exclude(id=model_id).update(is_active=False)
            
            # 激活当前模型
            model.is_active = True
            await model.save()
            
            logger.info(f"激活数据模型成功: {model.model_name}")
            return model
        except DoesNotExist:
            return None
    
    # =====================================================
    # 字段映射管理
    # =====================================================
    
    @staticmethod
    async def create_mapping(mapping_data: DeviceFieldMappingCreate) -> DeviceFieldMapping:
        """创建字段映射"""
        try:
            mapping_dict = mapping_data.model_dump()
            if mapping_data.transform_rule:
                mapping_dict['transform_rule'] = mapping_data.transform_rule.model_dump()
            
            mapping = await DeviceFieldMapping.create(**mapping_dict)
            logger.info(f"创建字段映射成功: {mapping.tdengine_stable}.{mapping.tdengine_column}")
            return mapping
        except Exception as e:
            logger.error(f"创建字段映射失败: {str(e)}")
            raise
    
    @staticmethod
    async def get_mapping_by_id(mapping_id: int) -> Optional[DeviceFieldMapping]:
        """根据ID获取字段映射"""
        try:
            return await DeviceFieldMapping.get(id=mapping_id).prefetch_related('device_field')
        except DoesNotExist:
            return None
    
    @staticmethod
    async def get_mappings(
        device_type_code: Optional[str] = None,
        tdengine_stable: Optional[str] = None,
        is_tag: Optional[bool] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[DeviceFieldMapping], int]:
        """获取字段映射列表（分页）"""
        query = DeviceFieldMapping.all().prefetch_related('device_field')
        
        # 构建查询条件
        if device_type_code:
            query = query.filter(device_type_code=device_type_code)
        if tdengine_stable:
            query = query.filter(tdengine_stable=tdengine_stable)
        if is_tag is not None:
            query = query.filter(is_tag=is_tag)
        if is_active is not None:
            query = query.filter(is_active=is_active)
        
        # 统计总数
        total = await query.count()
        
        # 分页查询
        offset = (page - 1) * page_size
        mappings = await query.order_by('device_type_code', 'tdengine_stable', 'tdengine_column').offset(offset).limit(page_size)
        
        return mappings, total

    # =====================================================
    # 导入导出管理
    # =====================================================
    
    @staticmethod
    async def export_metadata(device_type_code: Optional[str] = None) -> Dict[str, Any]:
        """导出元数据配置"""
        
        # 1. 获取设备类型
        type_query = DeviceType.all()
        if device_type_code:
            type_query = type_query.filter(type_code=device_type_code)
        device_types = await type_query.values()
        
        # 2. 获取字段定义
        field_query = DeviceField.all()
        if device_type_code:
            field_query = field_query.filter(device_type_code=device_type_code)
        fields = await field_query.values()
        
        # 3. 获取数据模型
        model_query = DeviceDataModel.all()
        if device_type_code:
            model_query = model_query.filter(device_type_code=device_type_code)
        models = await model_query.values()
        
        # 4. 获取字段映射
        mapping_query = DeviceFieldMapping.all()
        if device_type_code:
            mapping_query = mapping_query.filter(device_type_code=device_type_code)
        mappings = await mapping_query.values()
        
        return {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "device_types": device_types,
            "fields": fields,
            "models": models,
            "mappings": mappings
        }

    @staticmethod
    async def import_metadata(data: Dict[str, Any], user_id: int = None) -> Dict[str, Any]:
        """导入元数据配置"""
        stats = {"created": 0, "updated": 0, "errors": 0, "details": []}
        
        try:
            # 1. 导入设备类型
            for item in data.get("device_types", []):
                try:
                    type_code = item.get("type_code")
                    if not type_code: continue
                    
                    # 移除 id
                    item.pop("id", None)
                    
                    obj, created = await DeviceType.update_or_create(
                        type_code=type_code,
                        defaults=item
                    )
                    stats["created" if created else "updated"] += 1
                except Exception as e:
                    stats["errors"] += 1
                    stats["details"].append(f"Type {type_code}: {str(e)}")

            # 2. 导入字段定义
            for item in data.get("fields", []):
                try:
                    device_type = item.get("device_type_code")
                    field_name = item.get("field_name")
                    if not device_type or not field_name: continue
                    
                    item.pop("id", None)
                    
                    obj, created = await DeviceField.update_or_create(
                        device_type_code=device_type,
                        field_name=field_name,
                        defaults=item
                    )
                    stats["created" if created else "updated"] += 1
                except Exception as e:
                    stats["errors"] += 1
                    stats["details"].append(f"Field {field_name}: {str(e)}")

            # 3. 导入数据模型
            for item in data.get("models", []):
                try:
                    model_code = item.get("model_code")
                    version = item.get("version", "1.0")
                    if not model_code: continue
                    
                    item.pop("id", None)
                    
                    # 查找是否存在
                    model = await DeviceDataModel.filter(model_code=model_code, version=version).first()
                    if model:
                        # 创建快照
                        await MetadataService.create_snapshot(model, "import", "Import via API", user_id)
                        await model.update_from_dict(item).save()
                        stats["updated"] += 1
                    else:
                        await DeviceDataModel.create(**item)
                        stats["created"] += 1
                except Exception as e:
                    stats["errors"] += 1
                    stats["details"].append(f"Model {model_code}: {str(e)}")
            
            return stats
            
        except Exception as e:
            logger.error(f"导入元数据失败: {str(e)}")
            raise APIException(f"导入失败: {str(e)}")
    
    @staticmethod
    async def update_mapping(mapping_id: int, mapping_data: DeviceFieldMappingUpdate) -> Optional[DeviceFieldMapping]:
        """更新字段映射"""
        try:
            mapping = await DeviceFieldMapping.get(id=mapping_id)
            update_dict = mapping_data.model_dump(exclude_unset=True)
            
            if 'transform_rule' in update_dict and update_dict['transform_rule']:
                if hasattr(update_dict['transform_rule'], 'model_dump'):
                    update_dict['transform_rule'] = update_dict['transform_rule'].model_dump()
            
            await mapping.update_from_dict(update_dict).save()
            logger.info(f"更新字段映射成功: {mapping.tdengine_stable}.{mapping.tdengine_column}")
            return mapping
        except DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"更新字段映射失败: {str(e)}")
            raise
    
    @staticmethod
    async def delete_mapping(mapping_id: int) -> bool:
        """删除字段映射（软删除）"""
        try:
            mapping = await DeviceFieldMapping.get(id=mapping_id).prefetch_related('device_field')
            
            # 检查是否被模型引用
            if mapping.device_field:
                active_models = await DeviceDataModel.filter(
                    device_type_code=mapping.device_type_code,
                    is_active=True
                ).all()
                
                for model in active_models:
                    selected = model.selected_fields or []
                    for sf in selected:
                        if isinstance(sf, dict) and sf.get("field_code") == mapping.device_field.field_code:
                            raise APIException(
                                message=f"字段 '{mapping.device_field.field_name}' 的映射正被模型 '{model.model_name}' 使用，无法删除。",
                                code=400
                            )

            mapping.is_active = False
            await mapping.save()
            logger.info(f"删除字段映射成功: {mapping.tdengine_stable}.{mapping.tdengine_column}")
            return True
        except DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"删除字段映射失败: {str(e)}")
            raise

    @staticmethod
    async def delete_mappings_by_ids(mapping_ids: List[int]) -> int:
        """批量删除字段映射"""
        try:
            # 1. 获取映射
            mappings = await DeviceFieldMapping.filter(id__in=mapping_ids, is_active=True).prefetch_related('device_field').all()
            if not mappings:
                return 0
            
            # 2. 检查引用
            fields = [m.device_field for m in mappings if m.device_field]
            if not fields:
                # No fields associated (shouldn't happen), safe to delete?
                pass
            
            field_codes = set(f.field_code for f in fields)
            device_types = set(f.device_type_code for f in fields)
            
            active_models = await DeviceDataModel.filter(
                device_type_code__in=device_types,
                is_active=True
            ).all()
            
            conflicts = []
            for model in active_models:
                selected = model.selected_fields or []
                for sf in selected:
                    if isinstance(sf, dict) and sf.get("field_code") in field_codes:
                         fname = next((f.field_name for f in fields if f.field_code == sf.get("field_code")), "?")
                         conflict_msg = f"{fname} (模型: {model.model_name})"
                         if conflict_msg not in conflicts:
                             conflicts.append(conflict_msg)
            
            if conflicts:
                 raise APIException(
                    message=f"以下字段映射关联的字段正被模型引用，无法删除: {', '.join(conflicts[:3])}{'...' if len(conflicts)>3 else ''}。请先从模型中移除这些字段。",
                    code=400
                )

            count = await DeviceFieldMapping.filter(id__in=mapping_ids).update(is_active=False)
            logger.info(f"批量删除字段映射成功: {mapping_ids}, 数量: {count}")
            return count
        except Exception as e:
            logger.error(f"批量删除字段映射失败: {str(e)}")
            raise
    
    # =====================================================
    # 模型执行日志
    # =====================================================
    
    @staticmethod
    async def create_execution_log(log_data: ModelExecutionLogCreate) -> ModelExecutionLog:
        """创建执行日志"""
        try:
            log = await ModelExecutionLog.create(**log_data.model_dump())
            return log
        except Exception as e:
            logger.error(f"创建执行日志失败: {str(e)}")
            raise
    
    @staticmethod
    async def get_execution_logs(
        model_id: Optional[int] = None,
        model_code: Optional[str] = None,
        execution_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[ModelExecutionLog], int]:
        """获取执行日志列表（分页）"""
        query = ModelExecutionLog.all().prefetch_related('model')
        
        # 构建查询条件
        if model_id:
            query = query.filter(model_id=model_id)
        if model_code:
            query = query.filter(model__model_code=model_code)
        if execution_type:
            query = query.filter(execution_type=execution_type)
        if status:
            query = query.filter(status=status)
        
        # 统计总数
        total = await query.count()
        
        # 分页查询
        offset = (page - 1) * page_size
        logs = await query.order_by('-executed_at').offset(offset).limit(page_size)
        
        return logs, total
    
    # =====================================================
    # 统计功能
    # =====================================================
    
    @staticmethod
    async def get_model_statistics() -> Dict[str, Any]:
        """获取模型统计信息"""
        total_models = await DeviceDataModel.all().count()
        active_models = await DeviceDataModel.filter(is_active=True).count()
        realtime_models = await DeviceDataModel.filter(model_type='realtime').count()
        statistics_models = await DeviceDataModel.filter(model_type='statistics').count()
        ai_models = await DeviceDataModel.filter(model_type='ai_analysis').count()
        
        total_executions = await ModelExecutionLog.all().count()
        success_executions = await ModelExecutionLog.filter(status='success').count()
        success_rate = (success_executions / total_executions * 100) if total_executions > 0 else 0
        
        # 计算平均执行时间
        avg_time_result = await ModelExecutionLog.filter(
            status='success',
            execution_time_ms__isnull=False
        ).values_list('execution_time_ms')
        
        avg_execution_time_ms = 0
        if avg_time_result:
            times = [t[0] for t in avg_time_result if t[0] is not None]
            avg_execution_time_ms = sum(times) / len(times) if times else 0
        
        return {
            'total_models': total_models,
            'active_models': active_models,
            'realtime_models': realtime_models,
            'statistics_models': statistics_models,
            'ai_models': ai_models,
            'total_executions': total_executions,
            'success_rate': round(success_rate, 2),
            'avg_execution_time_ms': round(avg_execution_time_ms, 2)
        }

    @staticmethod
    async def compare_schema(device_type_code: str, dry_run: bool = True) -> Dict[str, Any]:
        """比较TDengine表结构与系统定义的差异
        
        Args:
            device_type_code: 设备类型代码
            dry_run: 是否为试运行模式（只检查不执行，当前版本强制为True）
            
        Returns:
            包含差异信息的字典
        """
        # 强制 dry_run 模式，符合文档规划
        dry_run = True
        
        # 1. 获取设备类型和关联字段
        device_type = await DeviceType.get_or_none(type_code=device_type_code)
        if not device_type:
            raise APIException(message=f"Device type {device_type_code} not found", code=404)
        
        if not device_type.tdengine_stable_name:
            raise APIException(message=f"Device type {device_type_code} has no TDengine stable name", code=400)

        fields = await DeviceField.filter(
            device_type_code=device_type_code, 
            is_active=True
        ).all()
        
        # 2. 获取TDengine表结构
        connector = TDengineConnector()
        td_columns = {}
        table_exists = False
        
        try:
            # Use backticks for stable name
            sql = f"DESCRIBE `{device_type.tdengine_stable_name}`"
            result = await connector.execute_sql(sql)
            
            # Handle TDengine raw response (code/desc)
            if 'code' in result:
                if result['code'] == 0:
                    table_exists = True
                    for row in result.get('data', []):
                        # row format: [field_name, type, length, note]
                        col_name = row[0]
                        col_type = row[1]
                        col_note = row[3] if len(row) > 3 else ""
                        
                        # Handle bytes note
                        note_str = ""
                        if col_note:
                             if isinstance(col_note, bytes):
                                 try:
                                     note_str = col_note.decode('utf-8', errors='ignore')
                                 except:
                                     note_str = str(col_note)
                             else:
                                 note_str = str(col_note)

                        td_columns[col_name] = {
                            'type': col_type,
                            'is_tag': 'TAG' in note_str.upper()
                        }
                else:
                    # Check for "Table does not exist" (code 9731 or error message)
                    error_desc = str(result.get('desc', '')).lower()
                    if result['code'] == 9731 or "not exist" in error_desc or "not found" in error_desc:
                        table_exists = False
                    else:
                        raise APIException(message=f"TDengine Error {result['code']}: {result.get('desc')}", code=500)
            elif 'status' in result and result.get('status') == 'succ':
                 # Legacy format
                 table_exists = True
                 for row in result.get('data', []):
                     col_name = row[0]
                     col_type = row[1]
                     col_note = row[3] if len(row) > 3 else ""
                     td_columns[col_name] = {'type': col_type, 'is_tag': 'TAG' in str(col_note).upper()}
            else:
                 # Legacy format error or unexpected
                 raise APIException(message=f"Failed to describe table: {result.get('desc')}", code=500)
                
        except Exception as e:
            # Table might not exist
            logger.error(f"Error describing table: {e}")
            
            error_msg = str(e)
            if isinstance(e, httpx.HTTPStatusError):
                try:
                    error_msg += f" {e.response.text}"
                except:
                    pass
            
            error_msg_lower = error_msg.lower()
            if "not exist" in error_msg_lower or "not found" in error_msg_lower:
                 table_exists = False
            else:
                 raise APIException(message=f"Error connecting to TDengine: {error_msg}", code=500)

        # 3. 比较差异
        diff = {
            "missing_in_tdengine": [],
            "missing_in_system": [],
            "type_mismatch": [],
            "suggested_actions": [] # 新增：建议执行的 SQL (仅展示)
        }
        
        # System definition
        system_fields = {f.field_code: f for f in fields}
        
        if not table_exists:
            # 整个表缺失
            create_sql = f"CREATE STABLE `{device_type.tdengine_stable_name}` (ts TIMESTAMP, "
            cols = []
            tags = [f"prod_code BINARY(64)"] # 默认 Tag
            
            for code, field in system_fields.items():
                # 简单映射类型
                data_type = "FLOAT" # 默认
                if field.field_type == 'string': data_type = "BINARY(64)"
                elif field.field_type == 'integer': data_type = "INT"
                elif field.field_type == 'boolean': data_type = "BOOL"
                
                cols.append(f"{code} {data_type}")
                
            create_sql += ", ".join(cols)
            create_sql += f") TAGS ({', '.join(tags)})"
            
            diff['suggested_actions'].append({
                "action": "CREATE_STABLE",
                "sql": create_sql,
                "reason": "Super table does not exist"
            })
            
            # 标记所有字段为缺失
            for code, field in system_fields.items():
                diff['missing_in_tdengine'].append({
                    "field_code": code,
                    "field_name": field.field_name,
                    "field_type": field.field_type
                })
        else:
            # 表存在，检查列差异
            
            # Check for missing fields in TDengine
            for code, field in system_fields.items():
                if code not in td_columns:
                    diff['missing_in_tdengine'].append({
                        "field_code": code,
                        "field_name": field.field_name,
                        "field_type": field.field_type
                    })
                    
                    # 生成建议 SQL
                    data_type = "FLOAT"
                    if field.field_type == 'string': data_type = "BINARY(64)"
                    elif field.field_type == 'integer': data_type = "INT"
                    elif field.field_type == 'boolean': data_type = "BOOL"
                    
                    alter_sql = f"ALTER STABLE `{device_type.tdengine_stable_name}` ADD COLUMN {code} {data_type}"
                    diff['suggested_actions'].append({
                        "action": "ADD_COLUMN",
                        "sql": alter_sql,
                        "reason": f"Column {code} missing in TDengine"
                    })
                else:
                    # Type comparison (Basic)
                    pass
                    
            # Check for extra fields in TDengine
            for col_name, col_info in td_columns.items():
                if col_name not in system_fields and col_name not in ['ts', 'prod_code']:
                    diff['missing_in_system'].append({
                        "field_code": col_name,
                        "td_type": col_info['type'],
                        "is_tag": col_info['is_tag']
                    })

        return {
            "status": "success",
            "device_type": device_type_code,
            "stable_name": device_type.tdengine_stable_name,
            "table_exists": table_exists,
            "dry_run": dry_run,
            "diff": diff
        }

    @staticmethod
    async def check_schema_diff_daily():
        """每日检查表结构差异并通知"""
        logger.info("⏰ 开始执行每日表结构差异检查...")
        try:
            # 获取所有配置了超级表的设备类型
            device_types = await DeviceType.filter(tdengine_stable_name__isnull=False).all()
            
            diff_count = 0
            for dt in device_types:
                if not dt.tdengine_stable_name:
                    continue
                    
                try:
                    result = await MetadataService.compare_schema(dt.type_code)
                    if result.get('status') == 'success':
                        diff = result.get('diff')
                        if diff and (diff['missing_in_tdengine'] or diff['missing_in_system']):
                            diff_count += 1
                            # 创建通知
                            missing_td = len(diff['missing_in_tdengine'])
                            missing_sys = len(diff['missing_in_system'])
                            
                            content = f"设备类型 [{dt.type_name}] ({dt.type_code}) 发现表结构差异。\n"
                            if missing_td > 0:
                                content += f"- TDengine缺失字段: {missing_td} 个\n"
                            if missing_sys > 0:
                                content += f"- 系统缺失字段: {missing_sys} 个\n"
                            content += "请前往[数据模型管理]查看并处理。"
                            
                            await Notification.create(
                                title=f"⚠️ 表结构差异告警: {dt.type_name}",
                                content=content,
                                notification_type="system",
                                level="warning",
                                scope="all"
                            )
                            logger.warning(f"发现差异并发送通知: {dt.type_name}")
                except Exception as e:
                    logger.error(f"检查设备类型 {dt.type_code} 差异失败: {e}")
            
            logger.info(f"✅ 表结构差异检查完成，发现 {diff_count} 个设备类型存在差异")
            
        except Exception as e:
            logger.error(f"❌ 每日表结构差异检查任务失败: {e}")

