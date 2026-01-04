"""
统一API v4

整合v2和v3的所有功能，提供统一的API接口。

设计原则：
1. 统一响应格式：所有端点使用ApiResponse格式
2. 统一错误处理：标准化错误码和错误消息
3. 统一分页规范：使用PageMeta元数据
4. RESTful设计：遵循REST规范
5. 向后兼容：提供v2/v3兼容层

Requirements: 6.1, 6.5
"""
from fastapi import APIRouter

# 创建v4版本的主路由器
v4_router = APIRouter()

# 导入v4版本的子路由
from .assets import router as assets_router
from .categories import router as categories_router
from .signals import router as signals_router
from .models import router as models_router
from .system import router as system_router
from .compatibility import router as compatibility_router

# 注册资产管理路由
v4_router.include_router(
    assets_router,
    prefix="/assets",
    tags=["资产管理 v4"]
)

# 注册资产类别管理路由
v4_router.include_router(
    categories_router,
    prefix="/categories",
    tags=["资产类别 v4"]
)

# 注册信号定义路由
v4_router.include_router(
    signals_router,
    prefix="/signals",
    tags=["信号定义 v4"]
)

# 注册AI模型路由
v4_router.include_router(
    models_router,
    prefix="/models",
    tags=["AI模型 v4"]
)

# 注册系统管理路由
v4_router.include_router(
    system_router,
    prefix="/system",
    tags=["系统管理 v4"]
)

# 注册兼容层路由
v4_router.include_router(
    compatibility_router,
    prefix="/compat",
    tags=["兼容层 v4"]
)

# 导出兼容层中间件
from .compatibility import DeprecationMiddleware, ResponseConverter, RequestConverter

__all__ = [
    "v4_router",
    "DeprecationMiddleware",
    "ResponseConverter",
    "RequestConverter"
]
