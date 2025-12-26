from fastapi import APIRouter

from app.core.dependency import DependPermission

# System management V1 APIs removed - migrated to V2
# from .apis import apis_router
# from .auditlog import auditlog_router
# from .depts import depts_router
# from .menus import menus_router
# from .roles import roles_router
# from .users import users_router

from .base import base_router
from .devices import devices_router
from .devices.websocket import router as websocket_router
from .devices.weld_record import router as weld_record_router
from .devices.welding_daily_report import router as welding_daily_report_router
from .health import router as health_router
# V1 system management router removed - migrated to V2
# from .system import router as system_router  # 导入system模块的router
from .dashboard import dashboard_router
from .avatar import router as avatar_router
from app.api.security import router as security_router

# from .mock_api import router as mock_api_router


v1_router = APIRouter()

v1_router.include_router(base_router, prefix="/base")
v1_router.include_router(health_router, prefix="/health")  # 健康检查路由，无需权限验证
v1_router.include_router(avatar_router, prefix="/avatar")  # 头像生成路由，无需权限验证
# v1_router.include_router(mock_api_router)  # 模拟API路由，无需权限验证
# System management V1 routes removed - use V2 versions instead
# v1_router.include_router(users_router, prefix="/user", dependencies=[DependPermission])
# v1_router.include_router(roles_router, prefix="/role", dependencies=[DependPermission])
# v1_router.include_router(menus_router, prefix="/menu", dependencies=[DependPermission])
# v1_router.include_router(apis_router, prefix="/api", dependencies=[DependPermission])
# v1_router.include_router(depts_router, prefix="/dept", dependencies=[DependPermission])
v1_router.include_router(websocket_router, prefix="/device")  # WebSocket路由不使用权限依赖
v1_router.include_router(devices_router, prefix="/device", dependencies=[DependPermission])
v1_router.include_router(weld_record_router, prefix="/device", dependencies=[DependPermission])
v1_router.include_router(welding_daily_report_router, dependencies=[DependPermission])
# Audit log V1 route removed - use V2 version instead
# v1_router.include_router(auditlog_router, prefix="/auditlog", dependencies=[DependPermission])
# V1 system management routes completely removed - all functionality migrated to V2
# V1 system management routes removed - migrated to V2
# v1_router.include_router(system_router, prefix="/system", dependencies=[DependPermission])  # 包含system模块的路由



v1_router.include_router(dashboard_router, prefix="/dashboard")  # 仪表板路由
v1_router.include_router(security_router, dependencies=[DependPermission])  # 安全管理路由
