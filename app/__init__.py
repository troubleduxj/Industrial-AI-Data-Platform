import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from tortoise import Tortoise

from app.core.exceptions import SettingNotFound
from app.core.init_app import (
    init_data,
    make_middlewares,
    register_exceptions,
    register_routers,
)


try:
    from app.settings.config import settings
except ImportError:
    raise SettingNotFound("Can not import settings")

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)




@asynccontextmanager
async def lifespan(app: FastAPI):

    
    logger.info("应用启动中...")
    
    try:
        # 初始化数据库和数据
        logger.info("初始化数据库...")
        await init_data()
        logger.info("✅ 数据库初始化完成")
        
        # 初始化外部API服务
        logger.info("初始化外部API服务...")
        from app.services.external_api import external_api_service
        await external_api_service._get_http_client()
        logger.info("✅ 外部API服务初始化完成")
        
        # 初始化文档服务
        logger.info("初始化Swagger文档服务...")
        from app.services.swagger_documentation_service import init_swagger_service
        from app.services.documentation_sync_service import init_sync_service
        
        swagger_service = init_swagger_service(app)
        sync_service = init_sync_service(app, swagger_service)
        
        # 启动时同步文档（如果配置启用）
        sync_config = sync_service.load_sync_config()
        if sync_config.get("sync_on_startup", True):
            try:
                await sync_service.sync_documentation(force=False)
                logger.info("✅ 启动时文档同步完成")
            except Exception as e:
                logger.warning(f"⚠️ 启动时文档同步失败: {e}")
        
        logger.info("✅ Swagger文档服务初始化完成")
        
        # 启动权限系统性能优化
        logger.info("启动权限系统性能优化...")
        try:
            from app.services.permission_startup_optimizer import permission_startup_optimizer
            optimization_result = await permission_startup_optimizer.optimize_on_startup()
            if optimization_result["success"]:
                logger.info("✅ 权限系统性能优化完成")
            else:
                logger.warning(f"⚠️ 权限系统性能优化部分失败: {optimization_result}")
        except Exception as e:
            logger.warning(f"⚠️ 权限系统性能优化失败: {e}")
        
        # 初始化工作流调度器 (可选)
        logger.info("检查工作流调度器配置...")
        try:
            from app.services.workflow_scheduler import start_scheduler
            await start_scheduler()
            logger.info("✅ 工作流调度器启动完成")
        except Exception as e:
            logger.warning(f"⚠️ 工作流调度器启动失败: {e}")
        
        # 初始化AI模块 (可选)
        logger.info("检查AI模块配置...")
        try:
            from app.settings.ai_settings import ai_settings
            from app.ai_module.loader import ai_loader
            
            if ai_settings.ai_module_enabled:
                logger.info("🚀 开始初始化AI模块...")
                success = ai_loader.load_module()
                
                if success:
                    # 注册AI路由到FastAPI
                    for router in ai_loader.get_routers():
                        app.include_router(
                            router,
                            prefix="/api/v2/ai",
                            tags=["AI监测 v2"]
                        )
                    logger.info("✅ AI模块初始化完成")
                else:
                    logger.warning("⚠️ AI模块初始化失败，核心功能不受影响")
            else:
                logger.info("⏸️ AI模块未启用，跳过初始化")
        except Exception as e:
            logger.warning(f"⚠️ AI模块初始化异常: {e}")
        
        logger.info("🚀 应用启动完成")
        
    except Exception as e:
        logger.error(f"❌ 应用启动失败: {e}")
        raise

    yield

    # 应用关闭阶段
    logger.info("应用关闭中...")
    
    try:
        # 停止工作流调度器
        try:
            from app.services.workflow_scheduler import stop_scheduler
            await stop_scheduler()
            logger.info("✅ 工作流调度器已停止")
        except Exception as e:
            logger.warning(f"⚠️ 工作流调度器停止失败: {e}")
        
        # 卸载AI模块
        try:
            from app.ai_module.loader import ai_loader
            ai_loader.unload_module()
        except Exception as e:
            logger.warning(f"⚠️ AI模块卸载失败: {e}")
        
        # 关闭外部API服务
        logger.info("关闭外部API服务...")
        from app.services.external_api import shutdown_external_api_service
        await shutdown_external_api_service()
        logger.info("✅ 外部API服务已关闭")
        
        # 关闭Tortoise ORM连接
        logger.info("关闭数据库连接...")
        await Tortoise.close_connections()
        logger.info("✅ 数据库连接已关闭")
        
        logger.info("🔚 应用关闭完成")
        
    except Exception as e:
        logger.error(f"❌ 应用关闭过程中发生错误: {e}")


def create_app() -> FastAPI:
    # 导入自定义JSON编码器
    from app.schemas.base import CustomJsonEncoder
    import json
    
    # 增强的API文档配置
    app = FastAPI(
        title=settings.APP_TITLE,
        description=f"""{settings.APP_DESCRIPTION}

## API版本控制

本API支持多版本控制，当前支持的版本：
• v1: 传统响应格式，保持向后兼容
• v2: 标准化响应格式，增强错误处理

### 版本指定方式

1. URL路径方式 (推荐):
   - GET /api/v1/users - 使用v1版本
   - GET /api/v2/users - 使用v2版本

2. 请求头方式:
   - 添加请求头 API-Version: v2

## 响应格式

### v1版本响应格式
{{
  "code": 200,
  "msg": "OK",
  "data": {{...}}
}}

### v2版本响应格式
{{
  "success": true,
  "code": 200,
  "message": "OK",
  "data": {{...}},
  "timestamp": "2025-01-06T00:00:00"
}}

## 错误处理

v2版本提供了增强的错误处理，包含详细的错误码和错误信息。

## 认证

大部分API需要在请求头中包含有效的访问令牌:
Authorization: Bearer <your-token>

或者使用token参数:
token: <your-token>""",
        version=settings.VERSION,
        openapi_url="/openapi.json",
        docs_url="/docs",  # 启用在线Swagger UI
        redoc_url="/redoc",  # 启用在线ReDoc
        lifespan=lifespan,
        # 添加联系信息和许可证信息
        contact={
            "name": "DeviceMonitor API Support",
            "email": "support@devicemonitor.com",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        # 添加服务器信息
        servers=[
            {
                "url": "http://localhost:8000",
                "description": "开发环境"
            },
            {
                "url": "https://api.devicemonitor.com",
                "description": "生产环境"
            }
        ],
        # 添加标签元数据
        openapi_tags=[
            {
                "name": "认证",
                "description": "用户认证相关接口"
            },
            {
                "name": "用户管理",
                "description": "用户信息管理接口"
            },
            {
                "name": "用户管理 v2",
                "description": "用户信息管理接口 - v2版本，使用标准化响应格式"
            },
            {
                "name": "角色管理",
                "description": "角色和权限管理接口"
            },
            {
                "name": "设备管理",
                "description": "设备信息管理接口"
            },
            {
                "name": "系统管理",
                "description": "系统配置和管理接口"
            },
            {
                "name": "健康检查",
                "description": "系统健康状态检查接口"
            },
            {
                "name": "健康检查 v2",
                "description": "系统健康状态检查接口 - v2版本"
            }
        ]
    )
    
    # 配置自定义JSON编码器
    app.json_encoder = CustomJsonEncoder
    
    # 添加中间件
    from app.core.middlewares import BackGroundTaskMiddleware, HttpAuditLogMiddleware
    from app.core.versioning import APIVersionMiddleware
    from app.core.security_middleware import SecurityMiddleware, SecurityConfig
    from app.middleware.audit_middleware import AuditMiddleware
    from fastapi.middleware.cors import CORSMiddleware
    
    # 添加CORS中间件（必须在最前面）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001", "http://localhost:4000", "http://127.0.0.1:4000", "http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174", "http://localhost:5175", "http://127.0.0.1:5175"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 创建安全配置
    security_config = SecurityConfig()
    
    # 添加中间件（注意顺序：安全中间件应该在最前面）
    app.add_middleware(
        SecurityMiddleware,
        **security_config.get_middleware_config()
    )
    app.add_middleware(APIVersionMiddleware, default_version="v1")
    app.add_middleware(BackGroundTaskMiddleware)
    
    # 添加权限审计中间件
    app.add_middleware(
        AuditMiddleware,
        exclude_paths=[
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/favicon.ico",
            "/health",
            "/metrics",
            "/api/v1/base/access_token",
            "/api/v2/base/access_token"
        ]
    )
    
    app.add_middleware(
        HttpAuditLogMiddleware,
        methods=["GET", "POST", "PUT", "DELETE"],
        exclude_paths=[
            "/api/v1/base/access_token",
            "/api/v2/base/access_token",
            "/docs",
            "/openapi.json",
        ],
    )
    
    register_exceptions(app)
    register_routers(app, prefix="/api")

    # 使用FastAPI默认的在线文档
    # 如需离线文档，可以取消注释下面的代码：
    # from app.core.swagger_config import setup_offline_docs
    # setup_offline_docs(app)

    # 添加根路径处理
    @app.get("/")
    async def root():
        return {"message": "Device Monitor API", "version": settings.VERSION, "docs": "/docs", "api_base": "/api/v1"}

    return app


app = create_app()
