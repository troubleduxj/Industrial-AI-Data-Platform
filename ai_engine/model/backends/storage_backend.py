#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
存储后端抽象基类

定义模型文件存储的统一接口，支持多种存储后端实现。

需求: 2.2, 2.3
- 支持.pkl、.onnx、.h5、.joblib格式
- 创建模型版本时关联模型文件路径和校验和
"""

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import BinaryIO, Optional, List, Tuple
from datetime import datetime
from loguru import logger


# =====================================================
# 异常定义
# =====================================================

class ModelStorageException(Exception):
    """模型存储基础异常"""
    pass


class UnsupportedFormatException(ModelStorageException):
    """不支持的文件格式异常"""
    def __init__(self, filename: str, supported_formats: List[str]):
        self.filename = filename
        self.supported_formats = supported_formats
        super().__init__(
            f"不支持的文件格式: {filename}。支持的格式: {', '.join(supported_formats)}"
        )


class StorageBackendException(ModelStorageException):
    """存储后端异常"""
    pass


# =====================================================
# 数据类定义
# =====================================================

@dataclass
class StorageResult:
    """
    存储操作结果
    
    Attributes:
        success: 操作是否成功
        file_path: 存储路径
        checksum: 文件SHA256校验和
        size_bytes: 文件大小（字节）
        error: 错误信息（如果失败）
        created_at: 创建时间
    """
    success: bool
    file_path: str
    checksum: str
    size_bytes: int
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "success": self.success,
            "file_path": self.file_path,
            "checksum": self.checksum,
            "size_bytes": self.size_bytes,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def failure(cls, error: str) -> "StorageResult":
        """创建失败结果"""
        return cls(
            success=False,
            file_path="",
            checksum="",
            size_bytes=0,
            error=error,
        )


# =====================================================
# 存储后端抽象基类
# =====================================================

class StorageBackend(ABC):
    """
    存储后端抽象基类
    
    定义模型文件存储的统一接口，所有具体存储后端必须实现此接口。
    
    支持的文件格式:
    - .pkl: Python pickle序列化文件
    - .onnx: ONNX模型格式
    - .h5: HDF5/Keras模型格式
    - .joblib: Joblib序列化文件
    
    需求: 2.2, 2.3
    """
    
    # 支持的模型文件格式
    SUPPORTED_FORMATS: List[str] = [".pkl", ".onnx", ".h5", ".joblib"]
    
    def __init__(self):
        """初始化存储后端"""
        self._initialized = False
    
    @abstractmethod
    async def upload(self, file: BinaryIO, filename: str) -> StorageResult:
        """
        上传文件到存储后端
        
        Args:
            file: 文件对象（二进制模式）
            filename: 文件名（包含扩展名）
        
        Returns:
            StorageResult: 上传结果，包含存储路径和校验和
        
        Raises:
            UnsupportedFormatException: 文件格式不支持
            StorageBackendException: 存储后端错误
        """
        pass
    
    @abstractmethod
    async def download(self, file_path: str) -> BinaryIO:
        """
        从存储后端下载文件
        
        Args:
            file_path: 存储路径
        
        Returns:
            BinaryIO: 文件对象
        
        Raises:
            StorageBackendException: 文件不存在或下载失败
        """
        pass
    
    @abstractmethod
    async def delete(self, file_path: str) -> bool:
        """
        从存储后端删除文件
        
        Args:
            file_path: 存储路径
        
        Returns:
            bool: 删除是否成功
        """
        pass
    
    @abstractmethod
    async def exists(self, file_path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path: 存储路径
        
        Returns:
            bool: 文件是否存在
        """
        pass
    
    def validate_format(self, filename: str) -> Tuple[bool, Optional[str]]:
        """
        验证文件格式是否支持
        
        Args:
            filename: 文件名
        
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 文件扩展名)
        """
        if not filename:
            return False, None
        
        filename_lower = filename.lower()
        for fmt in self.SUPPORTED_FORMATS:
            if filename_lower.endswith(fmt):
                return True, fmt
        
        return False, None
    
    def get_file_extension(self, filename: str) -> Optional[str]:
        """
        获取文件扩展名
        
        Args:
            filename: 文件名
        
        Returns:
            Optional[str]: 文件扩展名（小写），如果无效则返回None
        """
        is_valid, ext = self.validate_format(filename)
        return ext if is_valid else None
    
    @staticmethod
    def calculate_checksum(file: BinaryIO) -> str:
        """
        计算文件SHA256校验和
        
        Args:
            file: 文件对象（二进制模式）
        
        Returns:
            str: SHA256校验和（十六进制字符串）
        """
        sha256 = hashlib.sha256()
        
        # 保存当前位置
        original_position = file.tell()
        file.seek(0)
        
        # 分块读取计算校验和
        for chunk in iter(lambda: file.read(8192), b""):
            sha256.update(chunk)
        
        # 恢复文件位置
        file.seek(original_position)
        
        return sha256.hexdigest()
    
    @staticmethod
    def get_file_size(file: BinaryIO) -> int:
        """
        获取文件大小
        
        Args:
            file: 文件对象（二进制模式）
        
        Returns:
            int: 文件大小（字节）
        """
        # 保存当前位置
        original_position = file.tell()
        
        # 移动到文件末尾获取大小
        file.seek(0, 2)
        size = file.tell()
        
        # 恢复文件位置
        file.seek(original_position)
        
        return size
    
    def generate_storage_path(self, filename: str, checksum: str) -> str:
        """
        生成存储路径
        
        使用校验和前缀组织文件，避免单目录文件过多。
        
        Args:
            filename: 原始文件名
            checksum: 文件校验和
        
        Returns:
            str: 存储路径
        """
        # 使用校验和前8位作为目录前缀
        prefix = checksum[:8] if checksum else "unknown"
        return f"models/{prefix}/{filename}"
    
    async def verify_checksum(self, file_path: str, expected_checksum: str) -> bool:
        """
        验证文件校验和
        
        Args:
            file_path: 存储路径
            expected_checksum: 期望的校验和
        
        Returns:
            bool: 校验和是否匹配
        """
        try:
            file = await self.download(file_path)
            actual_checksum = self.calculate_checksum(file)
            return actual_checksum == expected_checksum
        except Exception as e:
            logger.error(f"校验和验证失败: {e}")
            return False
    
    @property
    def supported_formats(self) -> List[str]:
        """获取支持的文件格式列表"""
        return self.SUPPORTED_FORMATS.copy()
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
