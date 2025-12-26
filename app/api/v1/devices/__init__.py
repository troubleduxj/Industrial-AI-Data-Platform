from fastapi import APIRouter
from .devices import router as devices_router_base
from .device_data import router as device_data_router
from .device_types import router as device_types_router
from .universal_data import router as universal_data_router
from .welding_daily_report import router as welding_daily_report_router
from .alarm import router as alarm_router

# websocket_router 已在 v1/__init__.py 中单独注册，避免权限依赖冲突

devices_router = APIRouter()
devices_router.include_router(devices_router_base, tags=["设备模块"])
devices_router.include_router(device_data_router, prefix="/data", tags=["设备数据"])
devices_router.include_router(device_types_router, tags=["设备类型管理"])
devices_router.include_router(universal_data_router, prefix="/data", tags=["通用设备数据"])
devices_router.include_router(welding_daily_report_router, tags=["焊机日报统计"])
devices_router.include_router(alarm_router, prefix="/alarm", tags=["设备报警"])
# websocket_router 不在此处注册，避免重复和权限依赖问题

__all__ = ["devices_router"]
