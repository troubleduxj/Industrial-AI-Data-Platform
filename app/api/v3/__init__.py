"""
API v3 路由模块
工业AI数据平台 - 平台化API接口

设计原则：
1. 资产驱动：以Asset为核心，而非Device
2. 元数据驱动：动态Schema，支持任意设备类型
3. 统一响应格式：标准化错误处理和数据格式
4. RESTful设计：遵循REST规范
"""
from fastapi import APIRouter

# 创建v3版本的路由器
v3_router = APIRouter()

# 导入v3版本的子路由
from .asset_categories import router as asset_categories_router
from .assets import router as assets_router
from .predictions import router as predictions_router
from .feature_views import router as feature_views_router
from .security import router as security_router
from .performance import router as performance_router
from .audit import router as audit_router
from .migration import router as migration_router
from .model_storage import router as model_storage_router
from .websocket import router as websocket_router
from .ingestion import router as ingestion_router
from .identity import router as identity_router
from .decision import router as decision_router

# 注册资产类别管理路由
v3_router.include_router(
    asset_categories_router, 
    prefix="/asset-categories", 
    tags=["资产类别管理 v3"]
)

# 注册资产管理路由
v3_router.include_router(
    assets_router, 
    prefix="/assets", 
    tags=["资产管理 v3"]
)

# 注册AI预测路由
v3_router.include_router(
    predictions_router, 
    prefix="/predictions", 
    tags=["AI预测 v3"]
)

# 注册特征工程路由
v3_router.include_router(
    feature_views_router, 
    prefix="/feature-views", 
    tags=["特征工程 v3"]
)

# 注册安全管理路由
v3_router.include_router(
    security_router,
    tags=["安全管理 v3"]
)

# 注册性能监控路由
v3_router.include_router(
    performance_router,
    tags=["性能监控 v3"]
)

# 注册审计日志路由
v3_router.include_router(
    audit_router,
    tags=["审计日志 v3"]
)

# 注册数据迁移路由
v3_router.include_router(
    migration_router,
    tags=["数据迁移 v3"]
)

# 注册模型存储路由
v3_router.include_router(
    model_storage_router,
    tags=["模型存储 v3"]
)

# 注册WebSocket实时推送路由
v3_router.include_router(
    websocket_router,
    tags=["实时推送 v3"]
)

# 注册数据采集路由
v3_router.include_router(
    ingestion_router,
    tags=["数据采集 v3"]
)

# 注册身份集成路由
v3_router.include_router(
    identity_router,
    tags=["身份集成 v3"]
)

# 注册决策引擎路由
v3_router.include_router(
    decision_router,
    tags=["决策引擎 v3"]
)

__all__ = ["v3_router"]
