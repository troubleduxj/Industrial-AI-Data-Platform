#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型管理模块 (Model)

整合model_registry和model_storage的功能，提供统一的模型管理接口。

主要组件:
- ModelRegistry: 模型注册服务
- ModelVersionManager: 模型版本管理器
- ModelStorage: 统一的模型存储接口
- StorageBackend: 存储后端抽象基类

存储后端:
- LocalStorage: 本地文件系统存储
- MinIOStorage: MinIO对象存储

注意: 此模块整合了 ai_engine/model_registry 和 ai_engine/model_storage，
保持API兼容性。
"""

# 从registry导出模型注册相关
from .registry import (
    ModelRegistry,
    ModelVersionManager,
    ModelInfo,
    VersionInfo,
    ModelRegistryError,
)

# 从storage导出存储服务相关
from .storage import (
    ModelStorage,
    ModelStorageService,
    get_model_storage_service,
    set_model_storage_service,
)

# 从backends导出存储后端
from .backends import (
    StorageBackend,
    StorageResult,
    ModelStorageException,
    UnsupportedFormatException,
    StorageBackendException,
    LocalStorage,
    MinIOStorage,
)

__all__ = [
    # Model Registry
    "ModelRegistry",
    "ModelVersionManager",
    "ModelInfo",
    "VersionInfo",
    "ModelRegistryError",
    # Model Storage
    "ModelStorage",
    "ModelStorageService",
    "get_model_storage_service",
    "set_model_storage_service",
    # Storage Backends
    "StorageBackend",
    "StorageResult",
    "ModelStorageException",
    "UnsupportedFormatException",
    "StorageBackendException",
    "LocalStorage",
    "MinIOStorage",
]
