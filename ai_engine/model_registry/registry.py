#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型注册服务

提供AI模型的注册、版本管理和元数据管理功能。
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ModelRegistryError(Exception):
    """模型注册错误"""
    pass


@dataclass
class ModelInfo:
    """模型信息"""
    id: int
    code: str
    name: str
    algorithm: str
    target_signal: str
    category_id: int
    status: str
    is_active: bool
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    feature_config: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class VersionInfo:
    """版本信息"""
    id: int
    model_id: int
    version: str
    file_path: str
    status: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    training_start_time: Optional[datetime] = None
    training_end_time: Optional[datetime] = None
    deployed_at: Optional[datetime] = None
    release_notes: Optional[str] = None


class ModelRegistry:
    """
    模型注册服务
    
    提供模型的注册、查询和管理功能。
    """
    
    @staticmethod
    async def register_model(
        code: str,
        name: str,
        algorithm: str,
        target_signal: str,
        category_id: int,
        hyperparameters: Optional[Dict[str, Any]] = None,
        feature_config: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None
    ) -> ModelInfo:
        """
        注册新模型
        
        Args:
            code: 模型编码
            name: 模型名称
            algorithm: 算法类型
            target_signal: 目标信号
            category_id: 资产类别ID
            hyperparameters: 超参数配置
            feature_config: 特征配置
            description: 模型描述
            
        Returns:
            ModelInfo: 注册的模型信息
        """
        from app.models.platform_upgrade import AIModel
        
        try:
            model = await AIModel.create(
                code=code,
                name=name,
                algorithm=algorithm,
                target_signal=target_signal,
                category_id=category_id,
                hyperparameters=hyperparameters or {},
                feature_config=feature_config or {},
                description=description,
                status="draft",
                is_active=False
            )
            
            logger.info(f"注册模型成功: {code} ({name})")
            
            return ModelInfo(
                id=model.id,
                code=model.code,
                name=model.name,
                algorithm=model.algorithm,
                target_signal=model.target_signal,
                category_id=model.category_id,
                status=model.status,
                is_active=model.is_active,
                hyperparameters=model.hyperparameters,
                feature_config=model.feature_config,
                description=model.description,
                created_at=model.created_at,
                updated_at=model.updated_at
            )
        except Exception as e:
            logger.error(f"注册模型失败: {e}")
            raise ModelRegistryError(f"注册模型失败: {e}")
    
    @staticmethod
    async def get_model_by_code(code: str) -> Optional[ModelInfo]:
        """根据编码获取模型"""
        from app.models.platform_upgrade import AIModel
        
        model = await AIModel.get_or_none(code=code)
        if not model:
            return None
        
        return ModelInfo(
            id=model.id,
            code=model.code,
            name=model.name,
            algorithm=model.algorithm,
            target_signal=model.target_signal,
            category_id=model.category_id,
            status=model.status,
            is_active=model.is_active,
            hyperparameters=model.hyperparameters,
            feature_config=model.feature_config,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    @staticmethod
    async def get_model_by_id(model_id: int) -> Optional[ModelInfo]:
        """根据ID获取模型"""
        from app.models.platform_upgrade import AIModel
        
        model = await AIModel.get_or_none(id=model_id)
        if not model:
            return None
        
        return ModelInfo(
            id=model.id,
            code=model.code,
            name=model.name,
            algorithm=model.algorithm,
            target_signal=model.target_signal,
            category_id=model.category_id,
            status=model.status,
            is_active=model.is_active,
            hyperparameters=model.hyperparameters,
            feature_config=model.feature_config,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    @staticmethod
    async def list_models(
        category_id: Optional[int] = None,
        algorithm: Optional[str] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[ModelInfo]:
        """
        列出模型
        
        Args:
            category_id: 按类别筛选
            algorithm: 按算法筛选
            status: 按状态筛选
            is_active: 按激活状态筛选
            
        Returns:
            List[ModelInfo]: 模型列表
        """
        from app.models.platform_upgrade import AIModel
        
        query = AIModel.all()
        
        if category_id:
            query = query.filter(category_id=category_id)
        if algorithm:
            query = query.filter(algorithm=algorithm)
        if status:
            query = query.filter(status=status)
        if is_active is not None:
            query = query.filter(is_active=is_active)
        
        models = await query.order_by("-created_at").all()
        
        return [
            ModelInfo(
                id=m.id,
                code=m.code,
                name=m.name,
                algorithm=m.algorithm,
                target_signal=m.target_signal,
                category_id=m.category_id,
                status=m.status,
                is_active=m.is_active,
                hyperparameters=m.hyperparameters,
                feature_config=m.feature_config,
                description=m.description,
                created_at=m.created_at,
                updated_at=m.updated_at
            )
            for m in models
        ]
    
    @staticmethod
    async def update_model_status(model_id: int, status: str) -> bool:
        """更新模型状态"""
        from app.models.platform_upgrade import AIModel
        
        model = await AIModel.get_or_none(id=model_id)
        if not model:
            return False
        
        model.status = status
        await model.save()
        logger.info(f"更新模型状态: {model.code} -> {status}")
        return True
    
    @staticmethod
    async def activate_model(model_id: int) -> bool:
        """激活模型"""
        from app.models.platform_upgrade import AIModel
        
        model = await AIModel.get_or_none(id=model_id)
        if not model:
            return False
        
        model.is_active = True
        model.status = "deployed"
        await model.save()
        logger.info(f"激活模型: {model.code}")
        return True
    
    @staticmethod
    async def deactivate_model(model_id: int) -> bool:
        """停用模型"""
        from app.models.platform_upgrade import AIModel
        
        model = await AIModel.get_or_none(id=model_id)
        if not model:
            return False
        
        model.is_active = False
        await model.save()
        logger.info(f"停用模型: {model.code}")
        return True


class ModelVersionManager:
    """
    模型版本管理器
    
    提供模型版本的创建、查询和管理功能。
    """
    
    @staticmethod
    async def create_version(
        model_id: int,
        version: str,
        file_path: str,
        file_size: Optional[int] = None,
        file_hash: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
        release_notes: Optional[str] = None
    ) -> VersionInfo:
        """
        创建模型版本
        
        Args:
            model_id: 模型ID
            version: 版本号
            file_path: 模型文件路径
            file_size: 文件大小
            file_hash: 文件哈希
            metrics: 评估指标
            release_notes: 版本说明
            
        Returns:
            VersionInfo: 创建的版本信息
        """
        from app.models.platform_upgrade import AIModelVersion
        
        try:
            model_version = await AIModelVersion.create(
                model_id=model_id,
                version=version,
                file_path=file_path,
                file_size=file_size,
                file_hash=file_hash,
                metrics=metrics or {},
                release_notes=release_notes,
                status="staging"
            )
            
            logger.info(f"创建模型版本成功: model_id={model_id}, version={version}")
            
            return VersionInfo(
                id=model_version.id,
                model_id=model_version.model_id,
                version=model_version.version,
                file_path=model_version.file_path,
                status=model_version.status,
                metrics=model_version.metrics,
                file_size=model_version.file_size,
                file_hash=model_version.file_hash,
                training_start_time=model_version.training_start_time,
                training_end_time=model_version.training_end_time,
                deployed_at=model_version.deployed_at,
                release_notes=model_version.release_notes
            )
        except Exception as e:
            logger.error(f"创建模型版本失败: {e}")
            raise ModelRegistryError(f"创建模型版本失败: {e}")
    
    @staticmethod
    async def get_version(model_id: int, version: str) -> Optional[VersionInfo]:
        """获取指定版本"""
        from app.models.platform_upgrade import AIModelVersion
        
        model_version = await AIModelVersion.get_or_none(
            model_id=model_id,
            version=version
        )
        if not model_version:
            return None
        
        return VersionInfo(
            id=model_version.id,
            model_id=model_version.model_id,
            version=model_version.version,
            file_path=model_version.file_path,
            status=model_version.status,
            metrics=model_version.metrics,
            file_size=model_version.file_size,
            file_hash=model_version.file_hash,
            training_start_time=model_version.training_start_time,
            training_end_time=model_version.training_end_time,
            deployed_at=model_version.deployed_at,
            release_notes=model_version.release_notes
        )
    
    @staticmethod
    async def list_versions(model_id: int) -> List[VersionInfo]:
        """列出模型的所有版本"""
        from app.models.platform_upgrade import AIModelVersion
        
        versions = await AIModelVersion.filter(model_id=model_id).order_by("-version").all()
        
        return [
            VersionInfo(
                id=v.id,
                model_id=v.model_id,
                version=v.version,
                file_path=v.file_path,
                status=v.status,
                metrics=v.metrics,
                file_size=v.file_size,
                file_hash=v.file_hash,
                training_start_time=v.training_start_time,
                training_end_time=v.training_end_time,
                deployed_at=v.deployed_at,
                release_notes=v.release_notes
            )
            for v in versions
        ]
    
    @staticmethod
    async def get_active_version(model_id: int) -> Optional[VersionInfo]:
        """获取模型的激活版本"""
        from app.models.platform_upgrade import AIModelVersion
        
        model_version = await AIModelVersion.get_or_none(
            model_id=model_id,
            status="prod"
        )
        if not model_version:
            return None
        
        return VersionInfo(
            id=model_version.id,
            model_id=model_version.model_id,
            version=model_version.version,
            file_path=model_version.file_path,
            status=model_version.status,
            metrics=model_version.metrics,
            file_size=model_version.file_size,
            file_hash=model_version.file_hash,
            training_start_time=model_version.training_start_time,
            training_end_time=model_version.training_end_time,
            deployed_at=model_version.deployed_at,
            release_notes=model_version.release_notes
        )
    
    @staticmethod
    async def activate_version(model_id: int, version: str) -> bool:
        """
        激活指定版本
        
        将指定版本设为prod状态，其他版本设为staging或archived
        """
        from app.models.platform_upgrade import AIModelVersion
        from datetime import datetime
        
        # 获取目标版本
        target_version = await AIModelVersion.get_or_none(
            model_id=model_id,
            version=version
        )
        if not target_version:
            return False
        
        # 将当前prod版本设为archived
        await AIModelVersion.filter(
            model_id=model_id,
            status="prod"
        ).update(status="archived")
        
        # 激活目标版本
        target_version.status = "prod"
        target_version.deployed_at = datetime.now()
        await target_version.save()
        
        logger.info(f"激活模型版本: model_id={model_id}, version={version}")
        return True
    
    @staticmethod
    async def update_metrics(model_id: int, version: str, metrics: Dict[str, Any]) -> bool:
        """更新版本评估指标"""
        from app.models.platform_upgrade import AIModelVersion
        
        model_version = await AIModelVersion.get_or_none(
            model_id=model_id,
            version=version
        )
        if not model_version:
            return False
        
        model_version.metrics = metrics
        await model_version.save()
        logger.info(f"更新模型版本指标: model_id={model_id}, version={version}")
        return True
