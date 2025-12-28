#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型存储服务

提供统一的模型文件存储管理接口，支持多种存储后端切换。

需求: 2.1, 2.4, 2.5
- 上传模型文件时，平台应将文件存储到配置的存储后端
- 激活模型版本时，推理服务应从存储后端加载实际模型文件
- 删除模型版本时，平台应清理关联的模型文件
"""

import os
import io
import tempfile
from typing import BinaryIO, Optional, Dict, Any
from pathlib import Path
from loguru import logger

from .storage_backend import StorageBackend, StorageResult, StorageBackendException
from .local_storage import LocalStorage
from .minio_storage import MinIOStorage


class ModelStorageService:
    """
    模型存储服务
    
    提供统一的模型文件存储管理接口，支持：
    - 多种存储后端（MinIO、本地文件系统）
    - 模型文件上传、下载、删除
    - 模型版本关联管理
    - 模型文件加载到内存
    
    需求: 2.1, 2.4, 2.5
    """
    
    def __init__(self, backend: Optional[StorageBackend] = None):
        """
        初始化模型存储服务
        
        Args:
            backend: 存储后端实例，如果为None则使用默认本地存储
        """
        self._backend = backend or self._create_default_backend()
        self._temp_dir = tempfile.mkdtemp(prefix="model_storage_")
        logger.info(f"✅ 模型存储服务初始化: {self._backend}")
    
    def _create_default_backend(self) -> StorageBackend:
        """
        创建默认存储后端
        
        根据环境变量配置选择存储后端：
        - MODEL_STORAGE_TYPE=minio: 使用MinIO
        - MODEL_STORAGE_TYPE=local: 使用本地存储（默认）
        """
        storage_type = os.getenv("MODEL_STORAGE_TYPE", "local").lower()
        
        if storage_type == "minio":
            return MinIOStorage(
                endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
                access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
                secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
                bucket=os.getenv("MINIO_BUCKET", "ai-models"),
                secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
            )
        else:
            return LocalStorage(
                base_path=os.getenv("MODEL_STORAGE_PATH", "data/ai_models")
            )
    
    @property
    def backend(self) -> StorageBackend:
        """获取当前存储后端"""
        return self._backend
    
    async def upload_model(
        self,
        file: BinaryIO,
        filename: str,
        model_id: Optional[int] = None,
        version: Optional[str] = None,
    ) -> StorageResult:
        """
        上传模型文件
        
        Args:
            file: 文件对象（二进制模式）
            filename: 文件名
            model_id: 模型ID（可选，用于组织存储路径）
            version: 模型版本（可选）
        
        Returns:
            StorageResult: 上传结果
        """
        # 如果提供了model_id和version，修改文件名以包含这些信息
        if model_id and version:
            ext = self._backend.get_file_extension(filename)
            if ext:
                base_name = filename[:-len(ext)]
                filename = f"{base_name}_m{model_id}_v{version}{ext}"
        
        result = await self._backend.upload(file, filename)
        
        if result.success:
            logger.info(f"✅ 模型文件上传成功: {result.file_path}")
        else:
            logger.error(f"❌ 模型文件上传失败: {result.error}")
        
        return result
    
    async def download_model(self, file_path: str) -> BinaryIO:
        """
        下载模型文件
        
        Args:
            file_path: 存储路径
        
        Returns:
            BinaryIO: 文件对象
        """
        return await self._backend.download(file_path)
    
    async def delete_model(self, file_path: str) -> bool:
        """
        删除模型文件
        
        需求: 2.5 - 删除模型版本时，平台应清理关联的模型文件
        
        Args:
            file_path: 存储路径
        
        Returns:
            bool: 删除是否成功
        """
        result = await self._backend.delete(file_path)
        
        if result:
            logger.info(f"✅ 模型文件删除成功: {file_path}")
        else:
            logger.warning(f"⚠️ 模型文件删除失败或不存在: {file_path}")
        
        return result
    
    async def model_exists(self, file_path: str) -> bool:
        """
        检查模型文件是否存在
        
        Args:
            file_path: 存储路径
        
        Returns:
            bool: 文件是否存在
        """
        return await self._backend.exists(file_path)
    
    async def get_model_checksum(self, file_path: str) -> Optional[str]:
        """
        获取模型文件校验和
        
        Args:
            file_path: 存储路径
        
        Returns:
            Optional[str]: 校验和，如果文件不存在则返回None
        """
        try:
            file = await self._backend.download(file_path)
            return self._backend.calculate_checksum(file)
        except Exception:
            return None
    
    async def verify_model_checksum(self, file_path: str, expected_checksum: str) -> bool:
        """
        验证模型文件校验和
        
        Args:
            file_path: 存储路径
            expected_checksum: 期望的校验和
        
        Returns:
            bool: 校验和是否匹配
        """
        return await self._backend.verify_checksum(file_path, expected_checksum)
    
    async def load_model_to_temp(self, file_path: str) -> str:
        """
        将模型文件加载到临时目录
        
        需求: 2.4 - 激活模型版本时，推理服务应从存储后端加载实际模型文件
        
        用于推理服务加载模型时，先将模型文件从存储后端下载到本地临时目录。
        
        Args:
            file_path: 存储路径
        
        Returns:
            str: 临时文件的本地路径
        """
        try:
            # 下载文件
            file_content = await self._backend.download(file_path)
            
            # 提取文件名
            filename = Path(file_path).name
            
            # 保存到临时目录
            temp_path = Path(self._temp_dir) / filename
            with open(temp_path, "wb") as f:
                f.write(file_content.read())
            
            logger.info(f"✅ 模型文件加载到临时目录: {temp_path}")
            return str(temp_path)
            
        except Exception as e:
            logger.error(f"❌ 模型文件加载失败: {e}")
            raise StorageBackendException(f"模型文件加载失败: {e}")
    
    async def cleanup_temp_file(self, temp_path: str) -> bool:
        """
        清理临时文件
        
        Args:
            temp_path: 临时文件路径
        
        Returns:
            bool: 清理是否成功
        """
        try:
            path = Path(temp_path)
            if path.exists() and path.is_file():
                path.unlink()
                logger.debug(f"清理临时文件: {temp_path}")
                return True
            return False
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")
            return False
    
    def cleanup_all_temp_files(self):
        """清理所有临时文件"""
        try:
            import shutil
            if Path(self._temp_dir).exists():
                shutil.rmtree(self._temp_dir)
                self._temp_dir = tempfile.mkdtemp(prefix="model_storage_")
                logger.info("✅ 清理所有临时文件完成")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")
    
    def __del__(self):
        """析构时清理临时目录"""
        try:
            import shutil
            if hasattr(self, '_temp_dir') and Path(self._temp_dir).exists():
                shutil.rmtree(self._temp_dir)
        except Exception:
            pass


# 全局模型存储服务实例
_model_storage_service: Optional[ModelStorageService] = None


def get_model_storage_service() -> ModelStorageService:
    """
    获取全局模型存储服务实例
    
    Returns:
        ModelStorageService: 模型存储服务实例
    """
    global _model_storage_service
    if _model_storage_service is None:
        _model_storage_service = ModelStorageService()
    return _model_storage_service


def set_model_storage_service(service: ModelStorageService):
    """
    设置全局模型存储服务实例
    
    用于测试或自定义配置。
    
    Args:
        service: 模型存储服务实例
    """
    global _model_storage_service
    _model_storage_service = service
