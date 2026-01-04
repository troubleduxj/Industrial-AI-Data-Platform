#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI模型注册中心
实现模型元数据管理和版本控制

需求：2.1, 2.2, 7.1
- 注册新AI模型并存储模型元数据和配置
- 部署模型版本并验证模型文件
- 激活模型版本到推理服务
- 分配唯一标识符并跟踪元数据
"""

import os
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger


class ModelRegistryError(Exception):
    """模型注册中心异常"""
    pass


class ModelRegistry:
    """
    AI模型注册中心
    
    核心功能：
    - 注册和管理AI模型
    - 模型版本控制
    - 模型元数据管理
    - 模型激活和部署
    """
    
    # 支持的算法类型
    SUPPORTED_ALGORITHMS = [
        "isolation_forest",
        "arima", 
        "xgboost",
        "lstm",
        "random_forest",
        "linear_regression"
    ]
    
    # 模型状态
    MODEL_STATUS = {
        "draft": "草稿",
        "training": "训练中",
        "trained": "已训练",
        "deployed": "已部署",
        "archived": "已归档"
    }
    
    # 版本状态
    VERSION_STATUS = {
        "staging": "预发布",
        "prod": "生产",
        "archived": "已归档"
    }
    
    def __init__(self):
        self._predictors_cache: Dict[int, Any] = {}
    
    async def register_model(self, model_data: Dict[str, Any]) -> int:
        """
        注册新AI模型
        
        Args:
            model_data: 模型数据，包含：
                - name: 模型名称 (必填)
                - algorithm: 算法类型 (必填)
                - target_signal: 目标信号 (必填)
                - category_code: 资产类别编码 (必填)
                - description: 模型描述 (可选)
                - hyperparameters: 超参数配置 (可选)
                - feature_config: 特征配置 (可选)
        
        Returns:
            int: 新创建的模型ID
            
        Raises:
            ModelRegistryError: 注册失败时抛出
        """
        from app.models.platform_upgrade import AIModel, AssetCategory
        
        # 1. 验证必填字段
        required_fields = ["name", "algorithm", "target_signal", "category_code"]
        for field in required_fields:
            if field not in model_data or not model_data[field]:
                raise ModelRegistryError(f"缺少必填字段: {field}")
        
        # 2. 验证算法类型
        algorithm = model_data["algorithm"].lower()
        if algorithm not in self.SUPPORTED_ALGORITHMS:
            raise ModelRegistryError(
                f"不支持的算法类型: {algorithm}，"
                f"支持的类型: {', '.join(self.SUPPORTED_ALGORITHMS)}"
            )
        
        # 3. 验证资产类别存在
        try:
            category = await AssetCategory.get_or_none(code=model_data["category_code"])
            if not category:
                raise ModelRegistryError(f"资产类别不存在: {model_data['category_code']}")
        except Exception as e:
            raise ModelRegistryError(f"查询资产类别失败: {str(e)}")
        
        # 4. 生成唯一模型编码
        model_code = self._generate_model_code(
            model_data["name"], 
            algorithm, 
            model_data["category_code"]
        )
        
        # 5. 检查模型编码是否已存在
        existing = await AIModel.get_or_none(code=model_code)
        if existing:
            raise ModelRegistryError(f"模型编码已存在: {model_code}")
        
        # 6. 创建模型记录
        try:
            model = AIModel(
                name=model_data["name"],
                code=model_code,
                algorithm=algorithm,
                target_signal=model_data["target_signal"],
                description=model_data.get("description", ""),
                category=category,
                hyperparameters=model_data.get("hyperparameters", {}),
                feature_config=model_data.get("feature_config", {}),
                training_config=model_data.get("training_config"),
                status="draft",
                is_active=False
            )
            await model.save()
            
            logger.info(f"✅ 模型注册成功: {model.name} (ID: {model.id}, Code: {model_code})")
            return model.id
            
        except Exception as e:
            logger.error(f"❌ 模型注册失败: {str(e)}")
            raise ModelRegistryError(f"模型注册失败: {str(e)}")
    
    async def deploy_model(
        self, 
        model_id: int, 
        version: str, 
        file_path: str,
        metrics: Optional[Dict[str, Any]] = None,
        release_notes: Optional[str] = None
    ) -> bool:
        """
        部署模型版本
        
        Args:
            model_id: 模型ID
            version: 版本号 (如 "1.0.0")
            file_path: 模型文件路径
            metrics: 评估指标 (可选)
            release_notes: 版本说明 (可选)
        
        Returns:
            bool: 部署是否成功
            
        Raises:
            ModelRegistryError: 部署失败时抛出
        """
        from app.models.platform_upgrade import AIModel, AIModelVersion
        
        # 1. 验证模型存在
        model = await AIModel.get_or_none(id=model_id)
        if not model:
            raise ModelRegistryError(f"模型不存在: ID={model_id}")
        
        # 2. 验证版本号格式
        if not self._validate_version_format(version):
            raise ModelRegistryError(f"无效的版本号格式: {version}，应为 X.Y.Z 格式")
        
        # 3. 检查版本是否已存在
        existing_version = await AIModelVersion.get_or_none(
            model_id=model_id, 
            version=version
        )
        if existing_version:
            raise ModelRegistryError(f"版本已存在: {version}")
        
        # 4. 验证模型文件
        file_valid, file_info = self._validate_model_file(file_path)
        if not file_valid:
            raise ModelRegistryError(f"模型文件验证失败: {file_info.get('error', '未知错误')}")
        
        # 5. 创建版本记录
        try:
            version_record = AIModelVersion(
                model=model,
                version=version,
                file_path=file_path,
                file_size=file_info.get("size"),
                file_hash=file_info.get("hash"),
                metrics=metrics or {},
                status="staging",
                release_notes=release_notes
            )
            await version_record.save()
            
            # 6. 更新模型状态
            model.status = "trained"
            await model.save()
            
            logger.info(f"✅ 模型版本部署成功: {model.name} v{version}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 模型版本部署失败: {str(e)}")
            raise ModelRegistryError(f"模型版本部署失败: {str(e)}")
    
    async def activate_version(self, model_id: int, version: str) -> bool:
        """
        激活模型版本到生产环境
        
        Args:
            model_id: 模型ID
            version: 要激活的版本号
        
        Returns:
            bool: 激活是否成功
            
        Raises:
            ModelRegistryError: 激活失败时抛出
        """
        from app.models.platform_upgrade import AIModel, AIModelVersion
        
        # 1. 验证模型存在
        model = await AIModel.get_or_none(id=model_id)
        if not model:
            raise ModelRegistryError(f"模型不存在: ID={model_id}")
        
        # 2. 验证版本存在
        version_record = await AIModelVersion.get_or_none(
            model_id=model_id, 
            version=version
        )
        if not version_record:
            raise ModelRegistryError(f"版本不存在: {version}")
        
        # 3. 验证版本状态
        if version_record.status == "archived":
            raise ModelRegistryError(f"无法激活已归档的版本: {version}")
        
        try:
            # 4. 停用当前生产版本
            await AIModelVersion.filter(
                model_id=model_id, 
                status="prod"
            ).update(status="staging")
            
            # 5. 激活新版本
            version_record.status = "prod"
            version_record.deployed_at = datetime.now()
            await version_record.save()
            
            # 6. 更新模型状态
            model.is_active = True
            model.status = "deployed"
            await model.save()
            
            # 7. 清除预测器缓存
            if model_id in self._predictors_cache:
                del self._predictors_cache[model_id]
            
            logger.info(f"✅ 模型版本激活成功: {model.name} v{version}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 模型版本激活失败: {str(e)}")
            raise ModelRegistryError(f"模型版本激活失败: {str(e)}")
    
    async def deactivate_model(self, model_id: int) -> bool:
        """
        停用模型
        
        Args:
            model_id: 模型ID
        
        Returns:
            bool: 停用是否成功
        """
        from app.models.platform_upgrade import AIModel, AIModelVersion
        
        model = await AIModel.get_or_none(id=model_id)
        if not model:
            raise ModelRegistryError(f"模型不存在: ID={model_id}")
        
        try:
            # 停用所有生产版本
            await AIModelVersion.filter(
                model_id=model_id, 
                status="prod"
            ).update(status="staging")
            
            # 更新模型状态
            model.is_active = False
            await model.save()
            
            # 清除缓存
            if model_id in self._predictors_cache:
                del self._predictors_cache[model_id]
            
            logger.info(f"✅ 模型已停用: {model.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 模型停用失败: {str(e)}")
            raise ModelRegistryError(f"模型停用失败: {str(e)}")
    
    async def get_model(self, model_id: int) -> Optional[Dict[str, Any]]:
        """
        获取模型信息
        
        Args:
            model_id: 模型ID
        
        Returns:
            模型信息字典，不存在返回None
        """
        from app.models.platform_upgrade import AIModel
        
        model = await AIModel.get_or_none(id=model_id).prefetch_related("category")
        if not model:
            return None
        
        return {
            "id": model.id,
            "code": model.code,
            "name": model.name,
            "algorithm": model.algorithm,
            "target_signal": model.target_signal,
            "description": model.description,
            "category_id": model.category_id,
            "category_code": model.category.code if model.category else None,
            "hyperparameters": model.hyperparameters,
            "feature_config": model.feature_config,
            "status": model.status,
            "is_active": model.is_active,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None
        }
    
    async def get_model_versions(self, model_id: int) -> List[Dict[str, Any]]:
        """
        获取模型的所有版本
        
        Args:
            model_id: 模型ID
        
        Returns:
            版本列表
        """
        from app.models.platform_upgrade import AIModelVersion
        
        versions = await AIModelVersion.filter(model_id=model_id).order_by("-created_at")
        
        return [
            {
                "id": v.id,
                "version": v.version,
                "file_path": v.file_path,
                "file_size": v.file_size,
                "metrics": v.metrics,
                "status": v.status,
                "deployed_at": v.deployed_at.isoformat() if v.deployed_at else None,
                "created_at": v.created_at.isoformat() if v.created_at else None
            }
            for v in versions
        ]
    
    async def get_active_version(self, model_id: int) -> Optional[Dict[str, Any]]:
        """
        获取模型的当前生产版本
        
        Args:
            model_id: 模型ID
        
        Returns:
            生产版本信息，不存在返回None
        """
        from app.models.platform_upgrade import AIModelVersion
        
        version = await AIModelVersion.get_or_none(
            model_id=model_id, 
            status="prod"
        )
        
        if not version:
            return None
        
        return {
            "id": version.id,
            "version": version.version,
            "file_path": version.file_path,
            "file_size": version.file_size,
            "metrics": version.metrics,
            "status": version.status,
            "deployed_at": version.deployed_at.isoformat() if version.deployed_at else None,
            "created_at": version.created_at.isoformat() if version.created_at else None
        }
    
    async def list_models(
        self, 
        category_code: Optional[str] = None,
        algorithm: Optional[str] = None,
        is_active: Optional[bool] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        列出模型
        
        Args:
            category_code: 按资产类别过滤
            algorithm: 按算法类型过滤
            is_active: 按激活状态过滤
            status: 按状态过滤
        
        Returns:
            模型列表
        """
        from app.models.platform_upgrade import AIModel, AssetCategory
        
        query = AIModel.all().prefetch_related("category")
        
        if category_code:
            category = await AssetCategory.get_or_none(code=category_code)
            if category:
                query = query.filter(category_id=category.id)
        
        if algorithm:
            query = query.filter(algorithm=algorithm.lower())
        
        if is_active is not None:
            query = query.filter(is_active=is_active)
        
        if status:
            query = query.filter(status=status)
        
        models = await query.order_by("-created_at")
        
        return [
            {
                "id": m.id,
                "code": m.code,
                "name": m.name,
                "algorithm": m.algorithm,
                "target_signal": m.target_signal,
                "category_code": m.category.code if m.category else None,
                "status": m.status,
                "is_active": m.is_active,
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            for m in models
        ]
    
    async def rollback_version(self, model_id: int, target_version: str) -> bool:
        """
        回滚到指定版本
        
        Args:
            model_id: 模型ID
            target_version: 目标版本号
        
        Returns:
            bool: 回滚是否成功
        """
        return await self.activate_version(model_id, target_version)
    
    async def archive_version(self, model_id: int, version: str) -> bool:
        """
        归档模型版本
        
        Args:
            model_id: 模型ID
            version: 版本号
        
        Returns:
            bool: 归档是否成功
        """
        from app.models.platform_upgrade import AIModelVersion
        
        version_record = await AIModelVersion.get_or_none(
            model_id=model_id, 
            version=version
        )
        
        if not version_record:
            raise ModelRegistryError(f"版本不存在: {version}")
        
        if version_record.status == "prod":
            raise ModelRegistryError("无法归档生产版本，请先停用")
        
        version_record.status = "archived"
        await version_record.save()
        
        logger.info(f"✅ 版本已归档: v{version}")
        return True
    
    async def delete_version(self, model_id: int, version: str, cleanup_files: bool = True) -> bool:
        """
        删除模型版本
        
        需求: 2.5 - 删除模型版本时，平台应清理关联的模型文件
        
        Args:
            model_id: 模型ID
            version: 版本号
            cleanup_files: 是否清理关联的模型文件
        
        Returns:
            bool: 删除是否成功
        """
        from app.models.platform_upgrade import AIModelVersion
        
        version_record = await AIModelVersion.get_or_none(
            model_id=model_id, 
            version=version
        )
        
        if not version_record:
            raise ModelRegistryError(f"版本不存在: {version}")
        
        if version_record.status == "prod":
            raise ModelRegistryError("无法删除生产版本，请先停用")
        
        try:
            # 清理模型文件
            if cleanup_files:
                await self._cleanup_model_files(version_record)
            
            # 删除版本记录
            await version_record.delete()
            
            logger.info(f"✅ 版本已删除: v{version}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 删除版本失败: {str(e)}")
            raise ModelRegistryError(f"删除版本失败: {str(e)}")
    
    async def _cleanup_model_files(self, version_record) -> bool:
        """
        清理模型版本关联的文件
        
        需求: 2.5 - 删除模型版本时，平台应清理关联的模型文件
        
        Args:
            version_record: 模型版本记录
        
        Returns:
            bool: 清理是否成功
        """
        files_cleaned = []
        
        try:
            # 1. 清理存储后端文件
            storage_path = getattr(version_record, 'storage_path', None)
            if storage_path:
                try:
                    from ai_engine.model import get_model_storage_service
                    
                    storage_service = get_model_storage_service()
                    if await storage_service.model_exists(storage_path):
                        await storage_service.delete_model(storage_path)
                        files_cleaned.append(f"storage:{storage_path}")
                        logger.info(f"✅ 清理存储后端文件: {storage_path}")
                except ImportError:
                    logger.warning("模型存储模块未安装，跳过存储后端清理")
                except Exception as e:
                    logger.warning(f"清理存储后端文件失败: {e}")
            
            # 2. 清理本地文件
            file_path = version_record.file_path
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    files_cleaned.append(f"local:{file_path}")
                    logger.info(f"✅ 清理本地文件: {file_path}")
                except Exception as e:
                    logger.warning(f"清理本地文件失败: {e}")
            
            if files_cleaned:
                logger.info(f"✅ 模型文件清理完成: {', '.join(files_cleaned)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 模型文件清理失败: {e}")
            return False
    
    def _generate_model_code(self, name: str, algorithm: str, category_code: str) -> str:
        """生成唯一模型编码"""
        import re
        import time
        
        # 清理名称
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', name.lower())[:10]
        timestamp = int(time.time() * 1000) % 100000
        
        return f"{category_code}_{algorithm}_{clean_name}_{timestamp}"
    
    def _validate_version_format(self, version: str) -> bool:
        """验证版本号格式 (X.Y.Z)"""
        import re
        pattern = r'^\d+\.\d+\.\d+$'
        return bool(re.match(pattern, version))
    
    def _validate_model_file(self, file_path: str) -> tuple:
        """
        验证模型文件
        
        Returns:
            (is_valid, file_info)
        """
        if not file_path:
            return False, {"error": "文件路径为空"}
        
        if not os.path.exists(file_path):
            return False, {"error": f"文件不存在: {file_path}"}
        
        if not os.path.isfile(file_path):
            return False, {"error": "路径不是文件"}
        
        try:
            file_size = os.path.getsize(file_path)
            
            # 计算文件哈希
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            return True, {
                "size": file_size,
                "hash": file_hash
            }
            
        except Exception as e:
            return False, {"error": f"读取文件失败: {str(e)}"}


# 全局模型注册中心实例
model_registry = ModelRegistry()
