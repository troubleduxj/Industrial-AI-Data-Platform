#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI推理模块

包含预测存储服务和相关功能。
"""

from .prediction_store import (
    PredictionStore,
    PredictionStoreError,
    get_prediction_store,
)

__all__ = [
    "PredictionStore",
    "PredictionStoreError",
    "get_prediction_store",
]
