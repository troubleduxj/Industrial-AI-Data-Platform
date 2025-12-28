#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型文件存储模块

提供AI模型文件的存储、下载、删除等功能。
支持多种存储后端：MinIO对象存储、本地文件系统。

需求: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
"""

from .storage_backend import (
    StorageBackend,
    StorageResult,
    ModelStorageException,
    UnsupportedFormatException,
    StorageBackendException,
)
from .local_storage import LocalStorage
from .minio_storage import MinIOStorage
from .model_storage_service import (
    ModelStorageService,
    get_model_storage_service,
    set_model_storage_service,
)

__all__ = [
    "StorageBackend",
    "StorageResult",
    "ModelStorageException",
    "UnsupportedFormatException",
    "StorageBackendException",
    "LocalStorage",
    "MinIOStorage",
    "ModelStorageService",
    "get_model_storage_service",
    "set_model_storage_service",
]
