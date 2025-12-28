#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生产环境配置管理
配置生产环境参数、监控和告警设置
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class Environment(Enum):
    """环境类型"""
    DEVELOPMENT = "dev"
    STAGING = "staging"
    PRODUCTION = "prod"


@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str = "localhost"
    port: int = 5432
    database: str = "industrial_ai_platform"
    username: str = "postgres"
    password: str = ""
    pool_size: int = 20
    max_overflow: int = 10
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class TDengineConfig:
    """TDengine配置"""
    host: str = "localhost"
    port: int = 6041
    database: str = "devicemonitor"
    username: str = "root"
    password: str = "taosdata"
    
    @property
    def url(self) -> str:
        return f"taos://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class RedisConfig:
    """Redis配置"""
    host: str = "localhost"
    port: int = 6379
    password: str = ""
    db: int = 0
    
    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


@dataclass
class MonitoringConfig:
    """监控配置"""
    enabled: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 30  # 秒
    alert_email: str = ""
    alert_webhook: str = ""
    
    # 性能阈值
    api_response_time_warning: float = 0.5  # 秒
    api_response_time_critical: float = 1.0  # 秒
    cpu_usage_warning: float = 70.0  # 百分比
    cpu_usage_critical: float = 90.0  # 百分比
    memory_usage_warning: float = 70.0  # 百分比
    memory_usage_critical: float = 90.0  # 百分比
    disk_usage_warning: float = 80.0  # 百分比
    disk_usage_critical: float = 95.0  # 百分比


@dataclass
class SecurityConfig:
    """安全配置"""
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24小时
    cors_origins: list = field(default_factory=lambda: ["*"])
    rate_limit_per_minute: int = 100
    enable_audit_log: bool = True


@dataclass
class ProductionConfig:
    """生产环境完整配置"""
    environment: Environment = Environment.PRODUCTION
    debug: bool = False
    
    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # 数据库配置
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    tdengine: TDengineConfig = field(default_factory=TDengineConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    
    # 监控配置
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # 安全配置
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # 迁移配置
    enable_dual_write: bool = True
    use_new_architecture: bool = False
    
    @classmethod
    def from_env(cls) -> "ProductionConfig":
        """从环境变量加载配置"""
        config = cls()
        
        # 环境
        env_str = os.getenv("APP_ENV", "prod")
        config.environment = Environment(env_str)
        config.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # 服务
        config.host = os.getenv("HOST", "0.0.0.0")
        config.port = int(os.getenv("PORT", "8000"))
        config.workers = int(os.getenv("WORKERS", "4"))
        
        # 数据库
        config.database.host = os.getenv("DB_HOST", "localhost")
        config.database.port = int(os.getenv("DB_PORT", "5432"))
        config.database.database = os.getenv("DB_NAME", "industrial_ai_platform")
        config.database.username = os.getenv("DB_USER", "postgres")
        config.database.password = os.getenv("DB_PASSWORD", "")
        
        # TDengine
        config.tdengine.host = os.getenv("TDENGINE_HOST", "localhost")
        config.tdengine.port = int(os.getenv("TDENGINE_PORT", "6041"))
        config.tdengine.database = os.getenv("TDENGINE_DB", "devicemonitor")
        
        # Redis
        config.redis.host = os.getenv("REDIS_HOST", "localhost")
        config.redis.port = int(os.getenv("REDIS_PORT", "6379"))
        config.redis.password = os.getenv("REDIS_PASSWORD", "")
        
        # 监控
        config.monitoring.enabled = os.getenv("MONITORING_ENABLED", "true").lower() == "true"
        config.monitoring.alert_email = os.getenv("ALERT_EMAIL", "")
        config.monitoring.alert_webhook = os.getenv("ALERT_WEBHOOK", "")
        
        # 安全
        config.security.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "")
        
        # 迁移
        config.enable_dual_write = os.getenv("ENABLE_DUAL_WRITE", "true").lower() == "true"
        config.use_new_architecture = os.getenv("USE_NEW_ARCHITECTURE", "false").lower() == "true"
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "environment": self.environment.value,
            "debug": self.debug,
            "host": self.host,
            "port": self.port,
            "workers": self.workers,
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database
            },
            "tdengine": {
                "host": self.tdengine.host,
                "port": self.tdengine.port,
                "database": self.tdengine.database
            },
            "redis": {
                "host": self.redis.host,
                "port": self.redis.port
            },
            "monitoring": {
                "enabled": self.monitoring.enabled,
                "metrics_port": self.monitoring.metrics_port
            },
            "migration": {
                "enable_dual_write": self.enable_dual_write,
                "use_new_architecture": self.use_new_architecture
            }
        }


# 全局配置实例
production_config = ProductionConfig.from_env()


def get_config() -> ProductionConfig:
    """获取配置实例"""
    return production_config


def print_config():
    """打印当前配置（隐藏敏感信息）"""
    config = get_config()
    print("=" * 60)
    print("生产环境配置")
    print("=" * 60)
    print(f"环境: {config.environment.value}")
    print(f"调试模式: {config.debug}")
    print(f"服务地址: {config.host}:{config.port}")
    print(f"工作进程: {config.workers}")
    print(f"数据库: {config.database.host}:{config.database.port}/{config.database.database}")
    print(f"TDengine: {config.tdengine.host}:{config.tdengine.port}/{config.tdengine.database}")
    print(f"Redis: {config.redis.host}:{config.redis.port}")
    print(f"监控: {'启用' if config.monitoring.enabled else '禁用'}")
    print(f"双写模式: {'启用' if config.enable_dual_write else '禁用'}")
    print(f"新架构: {'启用' if config.use_new_architecture else '禁用'}")
    print("=" * 60)


if __name__ == "__main__":
    print_config()
