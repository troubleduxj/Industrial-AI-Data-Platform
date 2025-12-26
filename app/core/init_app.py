import shutil

from aerich import Command
from fastapi import FastAPI
from fastapi.middleware import Middleware
from tortoise.expressions import Q

from app.api import api_router
from app.controllers.api import api_controller
from app.controllers.user import UserCreate, user_controller
from app.core.exceptions import (
    DoesNotExist,
    DoesNotExistHandle,
    HTTPException,
    HttpExcHandle,
    IntegrityError,
    IntegrityHandle,
    RequestValidationError,
    RequestValidationHandle,
    ResponseValidationError,
    ResponseValidationHandle,
    APIException,
    api_exception_handler,
    general_exception_handler,
    ValidationErrorHandle,
)
from pydantic import ValidationError
from app.log import logger
from app.models.admin import SysApiEndpoint, Menu, Role
from app.schemas.menus import MenuType
from app.settings.config import settings

from .middlewares import BackGroundTaskMiddleware, HttpAuditLogMiddleware
from .api_version_middleware import APIVersionMiddleware
from app.middleware.permission_middleware import PermissionMiddleware


def make_middlewares():
    middleware = [
        # API版本检测中间件（最先执行）
        Middleware(APIVersionMiddleware),
        # 权限验证中间件
        Middleware(PermissionMiddleware, enable_cache=True),
        Middleware(BackGroundTaskMiddleware),
        Middleware(
            HttpAuditLogMiddleware,
            methods=["GET", "POST", "PUT", "DELETE"],
            exclude_paths=[
                "/api/v1/base/access_token",
                "/docs",
                "/openapi.json",
            ],
        ),
    ]
    return middleware


def register_exceptions(app: FastAPI):
    # 注册自定义异常处理器（按优先级顺序）
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(DoesNotExist, DoesNotExistHandle)
    app.add_exception_handler(HTTPException, HttpExcHandle)
    app.add_exception_handler(IntegrityError, IntegrityHandle)
    app.add_exception_handler(ValidationError, ValidationErrorHandle)
    app.add_exception_handler(RequestValidationError, RequestValidationHandle)
    app.add_exception_handler(ResponseValidationError, ResponseValidationHandle)
    # 通用异常处理器应该最后注册
    app.add_exception_handler(Exception, general_exception_handler)


def register_routers(app: FastAPI, prefix: str = "/api"):
    app.include_router(api_router, prefix=prefix)


async def init_superuser():
    from app.models.admin import User

    logger.info("Checking superuser existence")
    user = await User.exists()
    if not user:
        logger.info("Creating superuser")
        try:
            await user_controller.create_user(
                UserCreate(
                    username="admin",
                    email="admin@admin.com",
                    password="123456",
                    is_active=True,
                    is_superuser=True,
                )
            )
            logger.info("Superuser created successfully")
        except Exception as e:
            logger.error(f"Failed to create superuser: {str(e)}")
            raise
    else:
        logger.info("Superuser already exists")


async def init_menus():
    menus = await Menu.exists()
    if not menus:
        parent_menu = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="系统管理",
            path="/system",
            order=1,
            parent_id=0,
            icon="carbon:gui-management",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/system/user",
        )
        children_menu = [
            Menu(
                menu_type=MenuType.MENU,
                name="用户管理",
                path="user",
                order=1,
                parent_id=parent_menu.id,
                icon="material-symbols:person-outline-rounded",
                is_hidden=False,
                component="/system/user",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="角色管理",
                path="role",
                order=2,
                parent_id=parent_menu.id,
                icon="carbon:user-role",
                is_hidden=False,
                component="/system/role",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="菜单管理",
                path="menu",
                order=3,
                parent_id=parent_menu.id,
                icon="material-symbols:list-alt-outline",
                is_hidden=False,
                component="/system/menu",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="API管理",
                path="api",
                order=4,
                parent_id=parent_menu.id,
                icon="ant-design:api-outlined",
                is_hidden=False,
                component="/system/api",
                keepalive=False,
            ),
            # 字典管理
            # 系统参数管理
            Menu(
                menu_type=MenuType.MENU,
                name="系统参数",
                path="config",
                order=7,  # 订单号
                parent_id=parent_menu.id,
                icon="ant-design:setting-outlined",
                is_hidden=False,
                component="/system/config/SystemConfig",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="部门管理",
                path="dept",
                order=5,
                parent_id=parent_menu.id,
                icon="mingcute:department-line",
                is_hidden=False,
                component="/system/dept",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="审计日志",
                path="auditlog",
                order=6,
                parent_id=parent_menu.id,
                icon="ph:clipboard-text-bold",
                is_hidden=False,
                component="/system/auditlog",
                keepalive=False,
            ),
        ]
        await Menu.bulk_create(children_menu)
        # 手动创建字典管理下的子菜单
        dict_menu = await Menu.filter(path="dict", parent_id=parent_menu.id).first()
        if dict_menu:
            dict_children_menu = [
                Menu(
                    menu_type=MenuType.MENU,
                    name="字典类型",
                    path="dict/types",
                    order=1,
                    parent_id=dict_menu.id,
                    icon="ant-design:tag-outlined",
                    is_hidden=False,
                    component="/system/dict/DictType",
                    keepalive=False,
                ),
                Menu(
                    menu_type=MenuType.MENU,
                    name="字典数据",
                    path="dict/data",
                    order=2,
                    parent_id=dict_menu.id,
                    icon="ant-design:tags-outlined",
                    is_hidden=False,
                    component="/system/dict/DictData",
                    keepalive=False,
                ),
            ]
            await Menu.bulk_create(dict_children_menu)

        # 创建设备管理菜单
        device_parent_menu = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="设备管理",
            path="/device",
            order=2,
            parent_id=0,
            icon="carbon:devices",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/device/baseinfo",
        )
        device_children_menu = [
            Menu(
                menu_type=MenuType.MENU,
                name="设备信息管理",
                path="baseinfo",
                order=1,
                parent_id=device_parent_menu.id,
                icon="carbon:information",
                is_hidden=False,
                component="/device/baseinfo",
                keepalive=False,
            ),

        ]
        await Menu.bulk_create(device_children_menu)

        # 创建报警管理菜单
        alarm_parent_menu = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="报警管理",
            path="/alarm",
            order=3,
            parent_id=0,
            icon="material-symbols:warning",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/alarm/alarm-info",
        )
        alarm_children_menu = [
            Menu(
                menu_type=MenuType.MENU,
                name="报警信息",
                path="alarm-info",
                order=1,
                parent_id=alarm_parent_menu.id,
                icon="material-symbols:error",
                is_hidden=False,
                component="/alarm/alarm-info",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="报警分析",
                path="alarm-analysis",
                order=2,
                parent_id=alarm_parent_menu.id,
                icon="material-symbols:analytics",
                is_hidden=False,
                component="/alarm/alarm-analysis",
                keepalive=False,
            ),
        ]
        await Menu.bulk_create(alarm_children_menu)

        # 创建流程设置菜单
        flow_parent_menu = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="流程设置",
            path="/flow-settings",
            order=4,
            parent_id=0,
            icon="ant-design:node-index-outlined",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/flow-settings/workflow-manage",
        )
        flow_children_menu = [
            Menu(
                menu_type=MenuType.MENU,
                name="工作流管理",
                path="workflow-manage",
                order=1,
                parent_id=flow_parent_menu.id,
                icon="material-symbols:workflow-outline",
                is_hidden=False,
                component="/flow-settings/workflow-manage",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="工作流设计",
                path="workflow-design",
                order=2,
                parent_id=flow_parent_menu.id,
                icon="material-symbols:design-services-outline",
                is_hidden=False,
                component="/flow-settings/workflow-design",
                keepalive=False,
            ),
        ]
        await Menu.bulk_create(flow_children_menu)

        # 创建采集器管理菜单
        collector_parent_menu = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="采集器管理",
            path="/collector",
            order=5,
            parent_id=0,
            icon="mdi:database-sync",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/collector/dashboard",
        )
        collector_children_menu = [
            Menu(
                menu_type=MenuType.MENU,
                name="采集器总览",
                path="dashboard",
                order=1,
                parent_id=collector_parent_menu.id,
                icon="mdi:view-dashboard",
                is_hidden=False,
                component="/collector/dashboard",
                keepalive=True,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="配置管理",
                path="config",
                order=2,
                parent_id=collector_parent_menu.id,
                icon="mdi:cog",
                is_hidden=False,
                component="/collector/config",
                keepalive=True,
            ),

            Menu(
                menu_type=MenuType.MENU,
                name="数据质量",
                path="quality",
                order=4,
                parent_id=collector_parent_menu.id,
                icon="mdi:chart-line",
                is_hidden=False,
                component="/collector/quality",
                keepalive=True,
            ),
        ]
        await Menu.bulk_create(collector_children_menu)

        await Menu.create(
            menu_type=MenuType.MENU,
            name="一级菜单",
            path="/top-menu",
            order=6,
            parent_id=0,
            icon="material-symbols:featured-play-list-outline",
            is_hidden=False,
            component="/top-menu",
            keepalive=False,
            redirect="",
        )


async def init_apis():
    apis = await api_controller.model.exists()
    if not apis:
        await api_controller.refresh_api()


async def init_db():
    """
    初始化数据库连接和迁移
    
    Returns:
        None
    """
    from app.settings.config import settings
    from tortoise import Tortoise
    import logging
    import asyncio

    # 配置Tortoise ORM日志
    logging.getLogger("tortoise").setLevel(logging.INFO)  # 减少日志输出

    try:
        # 初始化Tortoise ORM，增加超时时间
        if not Tortoise._inited:
            # 修改配置，增加连接超时时间
            config = settings.tortoise_orm.model_dump()
            # 更新default和postgres连接的超时设置
            for conn_name in ['default', 'postgres']:
                if conn_name in config['connections']:
                    config['connections'][conn_name]['credentials']['timeout'] = 60  # 增加到60秒
                    config['connections'][conn_name]['credentials']['command_timeout'] = 60  # 命令超时
                    config['connections'][conn_name]['credentials']['server_settings'] = {
                        'application_name': 'DeviceMonitor',
                        'jit': 'off'  # 禁用JIT以提高连接速度
                    }
            
            logger.info("正在初始化Tortoise ORM...")
            logger.info(f"配置的连接: {list(config['connections'].keys())}")
            logger.info(f"默认连接: {config['apps']['models']['default_connection']}")
            await asyncio.wait_for(Tortoise.init(config=config), timeout=60)
            
            # 临时跳过schema生成，避免字段映射冲突
            # logger.info("正在生成数据库模式...")
            # await asyncio.wait_for(Tortoise.generate_schemas(), timeout=60)
            
            logger.info("Tortoise ORM initialized successfully")

        # 使用aerich进行数据库迁移
        logger.info("正在初始化数据库迁移...")
        command = Command(tortoise_config=settings.tortoise_orm.model_dump())
        
        try:
            await asyncio.wait_for(command.init_db(safe=True), timeout=30)
        except FileExistsError:
            logger.info("迁移目录已存在，跳过初始化")
        except asyncio.TimeoutError:
            logger.warning("数据库迁移初始化超时，但继续执行")

        try:
            await asyncio.wait_for(command.init(), timeout=30)
        except asyncio.TimeoutError:
            logger.warning("迁移初始化超时，但继续执行")
        
        # 执行数据库升级
        logger.info("正在执行数据库升级...")
        try:
            await asyncio.wait_for(command.upgrade(run_in_transaction=True), timeout=60)
            logger.info("数据库迁移完成")
        except asyncio.TimeoutError:
            logger.error("数据库升级超时")
            raise
        except Exception as e:
            logger.warning(f"数据库升级失败，但继续启动: {e}")
            
    except asyncio.TimeoutError:
        logger.error("数据库初始化超时")
        raise
    except Exception as e:
        logger.error(f"PostgreSQL数据库初始化失败，请检查数据库连接设置或服务是否启动: {e}")
        raise e


async def init_configs():
    """
    初始化系统配置
    """
    from app.controllers.system import config_controller  # 导入config_controller

    await config_controller.initialize_default_configs()
    await config_controller.refresh_config_cache()  # 确保在应用启动时加载配置到缓存


async def init_roles():
    roles = await Role.exists()
    if not roles:
        admin_role = await Role.create(
            name="管理员",
            desc="管理员角色",
        )
        user_role = await Role.create(
            name="普通用户",
            desc="普通用户角色",
        )

        # 分配所有API给管理员角色
        all_apis = await Api.all()
        await admin_role.apis.add(*all_apis)
        # 分配所有菜单给管理员和普通用户
        all_menus = await Menu.all()
        await admin_role.menus.add(*all_menus)
        await user_role.menus.add(*all_menus)

        # 为普通用户分配基本API
        basic_apis = await Api.filter(Q(method__in=["GET"]) | Q(tags="基础模块"))
        await user_role.apis.add(*basic_apis)


async def init_cache():
    """
    初始化缓存系统
    """
    from app.core.cache import cache_manager
    
    logger.info("Initializing cache system")
    try:
        await cache_manager.init_redis()
        logger.info("Cache system initialized successfully")
    except Exception as e:
        logger.warning(f"Cache initialization failed, will use fallback: {str(e)}")


async def init_data():
    from tortoise import Tortoise

    logger.info("Starting database initialization")
    try:
        await init_db()
        await init_cache()  # 初始化缓存系统
        await init_superuser()
        await init_menus()
        await init_apis()
        await init_configs()  # 初始化系统配置
        # await init_roles()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"PostgreSQL Database initialization failed: {str(e)}")
        raise e
