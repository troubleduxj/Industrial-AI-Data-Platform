#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地文件存储后端实现

提供基于本地文件系统的模型文件存储功能。

需求: 2.1
- 上传模型文件时，平台应将文件存储到配置的存储后端（本地存储）
"""

import io
import os
import shutil
from pathlib import Path
from typing import BinaryIO, Optional
from datetime import datetime
from loguru import logger

from .storage_backend import (
    StorageBackend,
    StorageResult,
    StorageBackendException,
)


class LocalStorage(StorageBackend):
    """
    本地文件系统存储实现
    
    使用本地文件系统作为模型文件的存储后端，适用于开发环境或单机部署。
    
    需求: 2.1
    """
    
    def __init__(self, base_path: str = "data/ai_models"):
        """
        初始化本地存储后端
        
        Args:
            base_path: 基础存储路径（相对于项目根目录或绝对路径）
        """
        super().__init__()
        self.base_path = Path(base_path)
        self._ensure_base_path()
        self._initialized = True
    
    def _ensure_base_path(self):
        """确保基础存储路径存在"""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ 本地存储初始化成功: {self.base_path.absolute()}")
        except Exception as e:
            raise StorageBackendException(f"创建存储目录失败: {e}")
    
    def _get_full_path(self, file_path: str) -> Path:
        """
        获取完整的文件路径
        
        Args:
            file_path: 相对存储路径
        
        Returns:
            Path: 完整的文件路径
        """
        return self.base_path / file_path
    
    async def upload(self, file: BinaryIO, filename: str) -> StorageResult:
        """
        上传文件到本地存储
        
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
            # 计算校验和
            checksum = self.calculate_checksum(file)
            
            # 获取文件大小
            size = self.get_file_size(file)
            
            # 生成存储路径
            file_path = self.generate_storage_path(filename, checksum)
            full_path = self._get_full_path(file_path)
            
            # 确保目录存在
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 确保文件指针在开头
            file.seek(0)
            
            # 写入文件
            with open(full_path, "wb") as f:
                shutil.copyfileobj(file, f)
            
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
        从本地存储下载文件
        
        Args:
            file_path: 存储路径
        
        Returns:
            BinaryIO: 文件对象
        
        Raises:
            StorageBackendException: 文件不存在或下载失败
        """
        try:
            full_path = self._get_full_path(file_path)
            
            if not full_path.exists():
                raise StorageBackendException(f"文件不存在: {file_path}")
            
            with open(full_path, "rb") as f:
                content = f.read()
            
            logger.debug(f"✅ 文件下载成功: {file_path}")
            return io.BytesIO(content)
            
        except StorageBackendException:
            raise
        except Exception as e:
            logger.error(f"❌ 文件下载失败: {file_path}, {e}")
            raise StorageBackendException(f"文件下载失败: {e}")
    
    async def delete(self, file_path: str) -> bool:
        """
        从本地存储删除文件
        
        Args:
            file_path: 存储路径
        
        Returns:
            bool: 删除是否成功
        """
        try:
            full_path = self._get_full_path(file_path)
            
            if not full_path.exists():
                logger.warning(f"文件不存在，无需删除: {file_path}")
                return False
            
            full_path.unlink()
            
            # 尝试清理空目录
            self._cleanup_empty_dirs(full_path.parent)
            
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
        full_path = self._get_full_path(file_path)
        return full_path.exists() and full_path.is_file()
    
    async def get_file_info(self, file_path: str) -> Optional[dict]:
        """
        获取文件信息
        
        Args:
            file_path: 存储路径
        
        Returns:
            Optional[dict]: 文件信息，包含大小、修改时间等
        """
        try:
            full_path = self._get_full_path(file_path)
            
            if not full_path.exists():
                return None
            
            stat = full_path.stat()
            
            return {
                "file_path": file_path,
                "full_path": str(full_path.absolute()),
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
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
            prefix_path = self._get_full_path(prefix)
            
            if not prefix_path.exists():
                return []
            
            files = []
            for file_path in prefix_path.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.base_path)
                    stat = file_path.stat()
                    files.append({
                        "file_path": str(relative_path),
                        "size_bytes": stat.st_size,
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })
            
            return files
            
        except Exception as e:
            logger.error(f"❌ 列出文件失败: {e}")
            return []
    
    def _cleanup_empty_dirs(self, dir_path: Path):
        """
        清理空目录
        
        递归删除空目录，直到遇到非空目录或基础路径。
        
        Args:
            dir_path: 目录路径
        """
        try:
            # 不删除基础路径
            if dir_path == self.base_path or not dir_path.is_relative_to(self.base_path):
                return
            
            # 如果目录为空，删除它
            if dir_path.exists() and dir_path.is_dir() and not any(dir_path.iterdir()):
                dir_path.rmdir()
                logger.debug(f"清理空目录: {dir_path}")
                
                # 递归清理父目录
                self._cleanup_empty_dirs(dir_path.parent)
                
        except Exception as e:
            logger.debug(f"清理目录失败（可忽略）: {e}")
    
    def get_storage_stats(self) -> dict:
        """
        获取存储统计信息
        
        Returns:
            dict: 存储统计信息
        """
        try:
            total_size = 0
            file_count = 0
            
            for file_path in self.base_path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            return {
                "base_path": str(self.base_path.absolute()),
                "total_files": file_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
            }
        except Exception as e:
            logger.error(f"获取存储统计失败: {e}")
            return {}
    
    def __repr__(self) -> str:
        return f"LocalStorage(base_path={self.base_path})"
