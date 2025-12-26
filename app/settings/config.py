import os
import typing
from dotenv import load_dotenv

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

# 环境配置
DEFAULT_ENV = "dev"  # 修改此处来切换默认环境: "dev" 或 "prod"


def get_env_file():
    """根据配置选择环境文件"""
    env = os.getenv("APP_ENV", DEFAULT_ENV)
    base_dir = os.path.dirname(os.path.dirname(__file__))

    if env == "dev":
        env_file = os.path.join(base_dir, ".env.dev")
    else:
        env_file = os.path.join(base_dir, ".env.prod")

    # 如果指定的环境文件不存在，回退到默认的.env文件
    if not os.path.exists(env_file):
        env_file = os.path.join(base_dir, ".env")

    # 打印配置加载信息
    print(f"[配置加载] APP_ENV={env}, 配置文件={env_file}, 文件存在={os.path.exists(env_file)}")
    
    # 使用 python-dotenv 显式加载环境变量
    if os.path.exists(env_file):
        load_dotenv(env_file, override=True)
        print(f"[配置加载] 已加载环境变量文件: {env_file}")
        print(f"[配置加载] TDENGINE_HOST={os.getenv('TDENGINE_HOST')}")
    else:
        print(f"[配置加载] 警告: 环境变量文件不存在: {env_file}")
    
    return env_file

# 在模块加载时就执行配置加载
get_env_file()


class PostgresCredentials(BaseSettings):
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    user: str = Field(default="postgres")
    password: str = Field(default="123456")
    database: str = Field(default="device_monitor")
    minsize: int = Field(default=1)  # 减少最小连接数
    maxsize: int = Field(default=10)  # 减少最大连接数
    max_queries: int = Field(default=1000)  # 减少最大查询数
    timeout: int = Field(default=30)  # 增加超时时间

    class Config:
        env_prefix = "POSTGRES_"
        env_file = get_env_file()
        extra = "ignore"


class TDengineCredentials(BaseSettings):
    host: str = Field(default="localhost")
    port: int = Field(default=6041)  # REST API端口
    user: str = Field(default="root")
    password: str = Field(default="taosdata")
    database: str = Field(default="test_db")
    external: bool = Field(default=False, description="是否为外部TDengine服务器")
    timeout: int = Field(default=30, description="连接超时时间（秒）")
    max_retries: int = Field(default=3, description="最大重试次数")
    connection_pool_size: int = Field(default=10, description="连接池大小")

    class Config:
        env_prefix = "TDENGINE_"
        env_file = get_env_file()
        extra = "ignore"
    
    def __init__(self, **data):
        super().__init__(**data)
        print(f"[TDengine配置] host={self.host}, port={self.port}, database={self.database}")


class PostgresConnection(BaseSettings):
    engine: str = "tortoise.backends.asyncpg"
    credentials: PostgresCredentials = Field(default_factory=PostgresCredentials)


class TDengineConnection(BaseSettings):
    engine: str = "tortoise.backends.mysql"  # TDengine uses MySQL protocol
    credentials: TDengineCredentials = Field(default_factory=TDengineCredentials)


class Connections(BaseSettings):
    postgres: PostgresConnection = Field(default_factory=PostgresConnection)
    tdengine: TDengineConnection = Field(default_factory=TDengineConnection)


class AppsModels(BaseSettings):
    models: typing.List[str] = ["app.models.admin", "app.models.system", "app.models.device", "app.models.ai_monitoring", "app.models.audit_log", "app.models.alarm", "app.models.notification", "app.models.email", "app.models.workflow", "aerich.models"]
    default_connection: str = "default"  # 使用"default"作为默认连接，与aerich_config.py保持一致


class Apps(BaseSettings):
    models: AppsModels = Field(default_factory=AppsModels)


class TortoiseORMConfig(BaseSettings):
    connections: Connections = Field(default_factory=Connections)
    apps: Apps = Field(default_factory=Apps)
    use_tz: bool = True  # 启用时区支持
    timezone: str = Field(default="Asia/Shanghai")

    def model_dump(self):
        """Generate Tortoise ORM configuration dictionary"""
        config = super().model_dump()

        # Build connections configuration
        postgres_creds = self.connections.postgres.credentials
        # tdengine_creds = self.connections.tdengine.credentials

        postgres_connection = {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": postgres_creds.host,
                "port": postgres_creds.port,
                "user": postgres_creds.user,
                "password": postgres_creds.password,
                "database": postgres_creds.database,
                "minsize": postgres_creds.minsize,
                "maxsize": postgres_creds.maxsize,
                "max_queries": postgres_creds.max_queries,
                "timeout": postgres_creds.timeout,
                "ssl": "disable",
            },
        }
        
        config["connections"] = {
            "default": postgres_connection,  # 使用"default"作为连接名称，与aerich_config.py保持一致
            "postgres": postgres_connection,  # 保留"postgres"别名以兼容现有代码
            # 暂时禁用TDengine连接
            # 'tdengine': {
            #     'engine': 'tortoise.backends.mysql',
            #     'credentials': {
            #         'host': tdengine_creds.host,
            #         'port': tdengine_creds.port,
            #         'user': tdengine_creds.user,
            #         'password': tdengine_creds.password,
            #         'database': tdengine_creds.database,
            #     }
            # }
        }
        
        # 添加apps配置
        config["apps"] = {
            "models": {
                "models": self.apps.models.models,
                "default_connection": "default"  # 使用"default"作为默认连接
            }
        }
        
        # 添加时区配置
        config["use_tz"] = self.use_tz
        config["timezone"] = self.timezone

        return config


class RedisCredentials(BaseSettings):
    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    db: int = Field(default=0)
    password: str = Field(default="")
    max_connections: int = Field(default=20)
    socket_timeout: int = Field(default=5)
    socket_connect_timeout: int = Field(default=5)

    class Config:
        env_prefix = "REDIS_"
        env_file = get_env_file()
        extra = "ignore"


class CelerySettings(BaseSettings):
    broker_url: str = Field(default="redis://localhost:6379/0")
    result_backend: str = Field(default="redis://localhost:6379/1")
    task_serializer: str = Field(default="json")
    result_serializer: str = Field(default="json")
    accept_content: typing.List[str] = Field(default=["json"])
    timezone: str = Field(default="Asia/Shanghai")
    enable_utc: bool = Field(default=True)

    class Config:
        env_prefix = "CELERY_"
        env_file = get_env_file()
        extra = "ignore"


class Settings(BaseSettings):
    class Config:
        env_file = get_env_file()
        extra = "ignore"

    VERSION: str = "0.1.0"
    APP_TITLE: str = "DeviceMonitor"
    PROJECT_NAME: str = "DeviceMonitor"
    APP_DESCRIPTION: str = "Description"

    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")
    PORT: int = Field(default=8001)
    
    # Redis配置
    redis: RedisCredentials = Field(default_factory=RedisCredentials)
    
    # Celery配置
    celery: CelerySettings = Field(default_factory=CelerySettings)
    
    # TDengine配置 (添加此配置)
    tdengine: TDengineConnection = Field(default_factory=TDengineConnection)

    @property
    def LOGGING_CONFIG(self):
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": self.LOG_LEVEL,
                },
            },
            "loggers": {
                "tortoise": {
                    "handlers": ["console"],
                    "level": self.LOG_LEVEL,
                    "propagate": False,
                },
            },
        }

    PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    BASE_DIR: str = os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))
    LOGS_ROOT: str = os.path.join(BASE_DIR, "app/logs")
    tortoise_orm: TortoiseORMConfig = Field(default_factory=TortoiseORMConfig)
    SECRET_KEY: str
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 7)  # 7 day default
    DATETIME_FORMAT: str = Field(default="%Y-%m-%d %H:%M:%S")
    

    
    @property
    def TORTOISE_ORM(self) -> dict:
        """获取Tortoise ORM配置（向后兼容）"""
        return self.tortoise_orm.model_dump()
    
    @property
    def TDENGINE_DATABASE(self) -> str:
        return self.tortoise_orm.connections.tdengine.credentials.database

    # 数据库配置属性（向后兼容）
    @property
    def DATABASE_HOST(self) -> str:
        return self.tortoise_orm.connections.postgres.credentials.host
    
    @property
    def DATABASE_PORT(self) -> int:
        return self.tortoise_orm.connections.postgres.credentials.port
    
    @property
    def DATABASE_USER(self) -> str:
        return self.tortoise_orm.connections.postgres.credentials.user
    
    @property
    def DATABASE_PASSWORD(self) -> str:
        return self.tortoise_orm.connections.postgres.credentials.password
    
    @property
    def DATABASE_NAME(self) -> str:
        return self.tortoise_orm.connections.postgres.credentials.database
    
    @property
    def DATABASE_URL(self) -> str:
        """获取数据库连接URL"""
        creds = self.tortoise_orm.connections.postgres.credentials
        return f"postgresql://{creds.user}:{creds.password}@{creds.host}:{creds.port}/{creds.database}"



settings = Settings()
