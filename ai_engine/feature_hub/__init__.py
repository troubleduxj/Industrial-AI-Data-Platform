#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
特征工厂模块 (Feature Hub)

提供特征存储、血缘追踪和特征管理功能。

模块组成:
- feature_store: 特征存储服务，管理TDengine特征表的创建和数据存储
- lineage_tracker: 特征血缘追踪器，记录特征的来源信号和计算逻辑
"""

from .feature_store import (
    FeatureStore,
    FeatureTableNaming,
    FeatureRecord,
    FeatureTableConfig,
    TableNameError,
)

from .lineage_tracker import (
    LineageTracker,
    FeatureLineage,
    LineageGraph,
)

__all__ = [
    # Feature Store
    "FeatureStore",
    "FeatureTableNaming",
    "FeatureRecord",
    "FeatureTableConfig",
    "TableNameError",
    # Lineage Tracker
    "LineageTracker",
    "FeatureLineage",
    "LineageGraph",
]
