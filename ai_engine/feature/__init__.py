#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
特征工程模块 (Feature)

提供特征存储、血缘追踪和特征管理功能。

模块组成:
- feature_store: 特征存储服务，管理TDengine特征表的创建和数据存储
- lineage_tracker: 特征血缘追踪器，记录特征的来源信号和计算逻辑

注意: 此模块从 ai_engine/feature_hub 重命名而来，保持API兼容性。
"""

from .feature_store import (
    FeatureStore,
    FeatureTableNaming,
    FeatureRecord,
    FeatureTableConfig,
    TableNameError,
    feature_store,
)

from .lineage_tracker import (
    LineageTracker,
    FeatureLineage,
    LineageGraph,
    lineage_tracker,
)

__all__ = [
    # Feature Store
    "FeatureStore",
    "FeatureTableNaming",
    "FeatureRecord",
    "FeatureTableConfig",
    "TableNameError",
    "feature_store",
    # Lineage Tracker
    "LineageTracker",
    "FeatureLineage",
    "LineageGraph",
    "lineage_tracker",
]
