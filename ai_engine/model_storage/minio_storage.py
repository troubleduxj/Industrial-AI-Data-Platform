#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MinIO对象存储后端实现

提供基于MinIO的模型文件存储功能。

需求: 2.1
- 上传模型文件时，平台应将文件存储到配置的存储后端（MinIO）
"""

import io
from typing import BinaryIO, Optional
from loguru import logger

from .storage_backend import (
    StorageBackend,
    StorageResult,
    StorageBackendException,
)


class MinIOStorage(StorageBackend):
    """
    MinIO对象存储实现
    
    使用MinIO作为模型文件的存储后端，支持文件上传、下载、删除等操作。
    
    需求: 2.1
    """
    
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
        region: Optional[str] = None,
    ):
        """
        初始化MinIO存储后端
        
        Args:
            endpoint: MinIO服务器地址（如 "localhost:9000"）
            access_key: 访问密钥
            secret_key: 秘密密钥
            bucket: 存储桶名称
            secure: 是否使用HTTPS
            region: 区域（可选）
        """
        super().__init__()
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.secure = secure
        self.region = region
        self._client = None
    
    def _get_client(self):
        """获取或创建MinIO客户端"""
        if self._client is None:
            try:
                from minio import Minio
                
                self._client = Minio(
                    self.endpoint,
                    access_key=self.access_key,
                    secret_key=self.secret_key,
                    secure=self.secure,
                    region=self.region,
                )
                self._ensure_bucket()
                self._initialized = True
                logger.info(f"✅ MinIO客户端初始化成功: {self.endpoint}")
            except ImportError:
                raise StorageBackendException(
                    "minio库未安装，请运行: pip install minio"
                )
            except Exception as e:
                raise StorageBackendException(f"MinIO客户端初始化失败: {e}")
        
        return self._client
    
    def _ensure_bucket(self):
        """确保存储桶存在"""
        try:
            if not self._client.bucket_exists(self.bucket):
                self._client.make_bucket(self.bucket)
                logger.info(f"✅ 创建存储桶: {self.bucket}")
        except Exception as e:
            raise StorageBackendException(f"创建存储桶失败: {e}")
    
    async def upload(self, file: BinaryIO, filename: str) -> StorageResult:
        """
        上传文件到MinIO
        
        Args:
            file: 文件对象（二进制模式）
            filename: 文件名（包含扩展名）
        
        Returns:
            StorageResult: 上传结果
        """
        # 验证文件格式
        is_valid, ext = self.validate_format(filename)
        if not is_valid:
            return StorageResult.failure(f"不支持的文件格式: {filename}")
        
        try:
            client = self._get_client()
            
            # 计算校验和
            checksum = self.calculate_checksum(file)
            
            # 获取文件大小
            size = self.get_file_size(file)
            
            # 生成存储路径
            file_path = self.generate_storage_path(filename, checksum)
            
            # 确保文件指针在开头
            file.seek(0)
            
            # 上传文件
            client.put_object(
                self.bucket,
                file_path,
                file,
                size,
                content_type=self._get_content_type(ext),
            )
            
            logger.info(f"✅ 文件上传成功: {file_path} ({size} bytes)")
            
            return StorageResult(
                success=True,
                file_path=file_path,
                checksum=checksum,
                size_bytes=size,
            )
            
        except Exception as e:
            logger.error(f"❌ 文件上传失败: {e}")
            return StorageResult.failure(str(e))
    
    async def download(self, file_path: str) -> BinaryIO:
        """
        从MinIO下载文件
        
        Args:
            file_path: 存储路径
        
        Returns:
            BinaryIO: 文件对象
        
        Raises:
            StorageBackendException: 文件不存在或下载失败
        """
        try:
            client = self._get_client()
            
            response = client.get_object(self.bucket, file_path)
            content = response.read()
            response.close()
            response.release_conn()
            
            logger.debug(f"✅ 文件下载成功: {file_path}")
            return io.BytesIO(content)
            
        except Exception as e:
            logger.error(f"❌ 文件下载失败: {file_path}, {e}")
            raise StorageBackendException(f"文件下载失败: {e}")
    
    async def delete(self, file_path: str) -> bool:
        """
        从MinIO删除文件
        
        Args:
            file_path: 存储路径
        
        Returns:
            bool: 删除是否成功
        """
        try:
            client = self._get_client()
            
            # 检查文件是否存在
            if not await self.exists(file_path):
                logger.warning(f"文件不存在，无需删除: {file_path}")
                return False
            
            client.remove_object(self.bucket, file_path)
            logger.info(f"✅ 文件删除成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 文件删除失败: {file_path}, {e}")
            return False
    
    async def exists(self, file_path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path: 存储路径
        
        Returns:
            bool: 文件是否存在
        """
        try:
            client = self._get_client()
            client.stat_object(self.bucket, file_path)
            return True
        except Exception:
            return False
    
    async def get_file_info(self, file_path: str) -> Optional[dict]:
        """
        获取文件信息
        
        Args:
            file_path: 存储路径
        
        Returns:
            Optional[dict]: 文件信息，包含大小、修改时间等
        """
        try:
            client = self._get_client()
            stat = client.stat_object(self.bucket, file_path)
            
            return {
                "file_path": file_path,
                "size_bytes": stat.size,
                "content_type": stat.content_type,
                "last_modified": stat.last_modified.isoformat() if stat.last_modified else None,
                "etag": stat.etag,
            }
        except Exception:
            return None
    
    async def list_files(self, prefix: str = "models/") -> list:
        """
        列出指定前缀下的所有文件
        
        Args:
            prefix: 路径前缀
        
        Returns:
            list: 文件列表
        """
        try:
            client = self._get_client()
            objects = client.list_objects(self.bucket, prefix=prefix, recursive=True)
            
            return [
                {
                    "file_path": obj.object_name,
                    "size_bytes": obj.size,
                    "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                }
                for obj in objects
            ]
        except Exception as e:
            logger.error(f"❌ 列出文件失败: {e}")
            return []
    
    def _get_content_type(self, extension: str) -> str:
        """
        根据扩展名获取Content-Type
        
        Args:
            extension: 文件扩展名
        
        Returns:
            str: Content-Type
        """
        content_types = {
            ".pkl": "application/octet-stream",
            ".onnx": "application/octet-stream",
            ".h5": "application/x-hdf5",
            ".joblib": "application/octet-stream",
        }
        return content_types.get(extension, "application/octet-stream")
    
    def __repr__(self) -> str:
        return f"MinIOStorage(endpoint={self.endpoint}, bucket={self.bucket})"
