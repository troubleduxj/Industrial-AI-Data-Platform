from typing import List, Optional, Type
from tortoise.exceptions import DoesNotExist
from fastapi import HTTPException
from app.core.crud import CRUDBase
from app.models.system import SysDictType, SysDictData, SysConfig
from app.schemas.system import (
    SysDictTypeCreate,
    SysDictTypeUpdate,
    SysDictTypeInDB,
    SysDictDataCreate,
    SysDictDataUpdate,
    SysDictDataInDB,
    SysConfigCreate,
    SysConfigUpdate,
    SysConfigInDB,
)
from app.log import logger

# 全局内存缓存，用于存储系统配置
_system_config_cache = {}


class DictController:
    def __init__(self):
        self.dict_type_crud = CRUDBase[SysDictType, SysDictTypeCreate, SysDictTypeUpdate](model=SysDictType)
        self.dict_data_crud = CRUDBase[SysDictData, SysDictDataCreate, SysDictDataUpdate](model=SysDictData)

    async def create_dict_type(self, obj_in: SysDictTypeCreate) -> SysDictType:
        return await self.dict_type_crud.create(obj_in)

    async def get_dict_type(self, type_id: int) -> Optional[SysDictType]:
        return await self.dict_type_crud.get(type_id)

    async def get_dict_type_by_code(self, type_code: str) -> Optional[SysDictType]:
        return await SysDictType.filter(type_code=type_code).first()

    async def get_all_dict_types(self, page: int = 1, page_size: int = 10) -> List[SysDictType]:
        return await self.dict_type_crud.get_multi(page=page, page_size=page_size)

    async def update_dict_type(self, type_id: int, obj_in: SysDictTypeUpdate) -> SysDictType:
        return await self.dict_type_crud.update(type_id, obj_in)

    async def delete_dict_type(self, type_id: int) -> None:
        await self.dict_type_crud.remove(type_id)

    async def create_dict_data(self, obj_in: SysDictDataCreate) -> SysDictData:
        # 检查 dict_type_id 是否存在
        dict_type = await self.dict_type_crud.get(obj_in.dict_type_id)
        if not dict_type:
            raise HTTPException(status_code=404, detail="字典类型不存在")
        return await self.dict_data_crud.create(obj_in)

    async def get_dict_data(self, data_id: int) -> Optional[SysDictData]:
        return await self.dict_data_crud.get(data_id)

    async def get_dict_data_by_type_code(self, type_code: str, enabled_only: bool = True) -> List[SysDictData]:
        dict_type = await SysDictType.filter(type_code=type_code).first()
        if not dict_type:
            return []  # 或者抛出异常

        query = SysDictData.filter(dict_type=dict_type)
        if enabled_only:
            query = query.filter(is_enabled=True)
        return await query.order_by("sort_order").all()

    async def get_all_dict_data(self, page: int = 1, page_size: int = 10) -> List[SysDictData]:
        # 使用 prefetch_related 预加载关联的字典类型
        offset = (page - 1) * page_size
        return await SysDictData.all().prefetch_related('dict_type').offset(offset).limit(page_size)

    async def update_dict_data(self, data_id: int, obj_in: SysDictDataUpdate) -> SysDictData:
        # 如果更新了 dict_type_id，需要检查是否存在
        if obj_in.dict_type_id:
            dict_type = await self.dict_type_crud.get(obj_in.dict_type_id)
            if not dict_type:
                raise HTTPException(status_code=404, detail="字典类型不存在")
        return await self.dict_data_crud.update(data_id, obj_in)

    async def delete_dict_data(self, data_id: int) -> None:
        await self.dict_data_crud.remove(data_id)


class ConfigController:
    def __init__(self):
        self.config_crud = CRUDBase[SysConfig, SysConfigCreate, SysConfigUpdate](model=SysConfig)

    async def create_config(self, obj_in: SysConfigCreate) -> SysConfig:
        config = await self.config_crud.create(obj_in)
        await self.refresh_config_cache()  # 创建后刷新缓存
        return config

    async def get_config(self, config_id: int) -> Optional[SysConfig]:
        return await self.config_crud.get(config_id)

    async def get_config_by_key(self, param_key: str) -> Optional[SysConfig]:
        return await SysConfig.filter(param_key=param_key).first()

    async def get_all_configs(self, page: int = 1, page_size: int = 10) -> List[SysConfig]:
        return await self.config_crud.get_multi(page=page, page_size=page_size)

    async def update_config(self, config_id: int, obj_in: SysConfigUpdate) -> SysConfig:
        config = await self.config_crud.update(config_id, obj_in)
        await self.refresh_config_cache()  # 更新后刷新缓存
        return config

    async def delete_config(self, config_id: int) -> None:
        await self.config_crud.remove(config_id)
        await self.refresh_config_cache()  # 删除后刷新缓存

    async def refresh_config_cache(self):
        """
        刷新系统配置缓存
        """
        logger.info("Refreshing system config cache...")
        configs = await SysConfig.filter(is_editable=True).all()
        _system_config_cache.clear()
        for config in configs:
            _system_config_cache[config.param_key] = config.param_value
        # 安全地记录系统配置缓存，避免特殊字符导致的格式化错误
        try:
            cache_summary = {k: str(v)[:50] + "..." if len(str(v)) > 50 else str(v) for k, v in _system_config_cache.items()}
            logger.info(f"System config cache refreshed with {len(_system_config_cache)} items")
            logger.debug(f"Cache contents: {cache_summary}")
        except Exception as e:
            logger.warning(f"Failed to log cache contents: {e}")
            logger.info(f"System config cache refreshed with {len(_system_config_cache)} items")

    def get_cached_config(self, param_key: str, default: Optional[str] = None):
        """
        从缓存中获取系统配置
        """
        return _system_config_cache.get(param_key, default)

    async def initialize_default_configs(self):
        """
        初始化默认系统配置
        """
        default_configs = [
            SysConfigCreate(
                param_key="LOG_LEVEL",
                param_value="INFO",
                param_name="日志级别",
                param_type="string",
                description="应用日志输出级别",
                is_editable=True,
            ),
            SysConfigCreate(
                param_key="NODE_RED_API_BASE_URL",
                param_value="http://localhost:1880/api",
                param_name="Node-RED API基础URL",
                param_type="string",
                description="Node-RED服务API的基础URL",
                is_editable=True,
            ),
            SysConfigCreate(
                param_key="FEATURE_TOGGLE_EXAMPLE",
                param_value="true",
                param_name="示例功能开关",
                param_type="boolean",
                description="用于控制某个功能的开关",
                is_editable=True,
            ),
            SysConfigCreate(
                param_key="AI_ASSISTANT_ENABLED",
                param_value="true",
                param_name="AI助手启用状态",
                param_type="boolean",
                description="控制AI助手是否在前端显示",
                is_editable=True,
            ),
            SysConfigCreate(
                param_key="GLOBALIZATION_ENABLED",
                param_value="true",
                param_name="全球化语言按钮显示",
                param_type="boolean",
                description="控制全球化（中英文语言）按钮是否在前端显示",
                is_editable=True,
            ),
            SysConfigCreate(
                param_key="THEME_SWITCHER_ENABLED",
                param_value="true",
                param_name="系统主题颜色按钮显示",
                param_type="boolean",
                description="控制系统主题颜色（白色、黑色）按钮是否在前端显示",
                is_editable=True,
            ),
            SysConfigCreate(
                param_key="HISTORY_DATA_DEFAULT_INTERVAL",
                param_value="3600",
                param_name="历史数据默认查询间隔",
                param_type="int",
                description="历史数据查询页面默认的时间间隔（秒），结束时间为当前时间，开始时间为当前时间减去该间隔",
                is_editable=True,
            ),
        ]

        for config_data in default_configs:
            existing_config = await self.get_config_by_key(config_data.param_key)
            if not existing_config:
                logger.info(f"Creating default config: {config_data.param_key}")
                await self.create_config(config_data)
            else:
                logger.debug(f"Config '{config_data.param_key}' already exists, skipping default creation.")


dict_controller = DictController()
config_controller = ConfigController()
