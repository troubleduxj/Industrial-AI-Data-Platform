#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型注册模块 (Model Registry)

提供AI模型的注册、版本管理和元数据管理功能。

主要组件:
- ModelRegistry: 模型注册服务
- ModelVersionManager: 模型版本管理器

注意: 此模块是 app/services/ai/model_registry.py 的封装，
提供统一的导入接口。
"""

from .registry import (
    ModelRegistry,
    ModelVersionManager,
    ModelInfo,
    VersionInfo,
    ModelRegistryError,
)

__all__ = [
    "ModelRegistry",
    "ModelVersionManager",
    "ModelInfo",
    "VersionInfo",
    "ModelRegistryError",
]
