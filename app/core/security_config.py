"""
安全配置管理模块
"""

import os
from typing import Dict, List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class SecuritySettings(BaseSettings):
    """安全设置配置"""
    
    # 安全头配置
    ENABLE_SECURITY_HEADERS: bool = Field(True, description="启用安全头")
    ENABLE_HSTS: bool = Field(True, description="启用HSTS")
    HSTS_MAX_AGE: int = Field(31536000, description="HSTS最大年龄（秒）")
    ENABLE_CSP: bool = Field(True, description="启用内容安全策略")
    CSP_POLICY: str = Field(
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https:; "
        "font-src 'self' data: https://cdn.jsdelivr.net; "
        "connect-src 'self'; "
        "frame-ancestors 'none'",
        description="CSP策略（支持API文档CDN）"
    )
    
    # 频率限制配置
    ENABLE_RATE_LIMITING: bool = Field(True, description="启用频率限制")
    DEFAULT_RATE_LIMIT: int = Field(100, description="默认频率限制（每分钟请求数）")
    RATE_LIMIT_WINDOW: int = Field(60, description="频率限制时间窗口（秒）")
    RATE_LIMIT_WHITELIST_IPS: List[str] = Field(
        ['127.0.0.1', '::1'], 
        description="频率限制白名单IP"
    )
    
    # 登录接口特殊限制
    LOGIN_RATE_LIMIT: int = Field(5, description="登录接口频率限制")
    LOGIN_RATE_LIMIT_WINDOW: int = Field(300, description="登录接口限制时间窗口（秒）")
    
    # 用户接口限制
    USER_API_RATE_LIMIT: int = Field(50, description="用户API频率限制")
    USER_API_RATE_LIMIT_WINDOW: int = Field(60, description="用户API限制时间窗口（秒）")
    
    # 输入验证配置
    ENABLE_INPUT_VALIDATION: bool = Field(True, description="启用输入验证")
    ENABLE_XSS_PROTECTION: bool = Field(True, description="启用XSS防护")
    ENABLE_SQL_INJECTION_PROTECTION: bool = Field(True, description="启用SQL注入防护")
    ENABLE_INPUT_SANITIZATION: bool = Field(False, description="启用输入清理")
    
    # 允许的HTML标签
    ALLOWED_HTML_TAGS: List[str] = Field(
        ['p', 'br', 'strong', 'em', 'u', 'i', 'b', 'ul', 'ol', 'li', 
         'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre'],
        description="允许的HTML标签"
    )
    
    # 日志配置
    ENABLE_SECURITY_LOGGING: bool = Field(True, description="启用安全日志")
    SECURITY_LOG_LEVEL: str = Field("WARNING", description="安全日志级别")
    
    class Config:
        env_file = ".env"
        env_prefix = "SECURITY_"
        extra = 'ignore'  # 忽略额外的环境变量字段


class SecurityConfigManager:
    """安全配置管理器"""
    
    def __init__(self):
        self.settings = SecuritySettings()
    
    def get_security_headers_config(self) -> Dict:
        """获取安全头配置"""
        headers = {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
        
        if self.settings.ENABLE_HSTS:
            headers["Strict-Transport-Security"] = f"max-age={self.settings.HSTS_MAX_AGE}; includeSubDomains"
        
        if self.settings.ENABLE_CSP:
            headers["Content-Security-Policy"] = self.settings.CSP_POLICY
        
        return headers
    
    def get_rate_limit_config(self) -> Dict:
        """获取频率限制配置"""
        return {
            'default_limit': self.settings.DEFAULT_RATE_LIMIT,
            'window_size': self.settings.RATE_LIMIT_WINDOW,
            'whitelist_ips': self.settings.RATE_LIMIT_WHITELIST_IPS,
            'path_limits': {
                '/api/v1/auth/login': {
                    'limit': self.settings.LOGIN_RATE_LIMIT,
                    'window': self.settings.LOGIN_RATE_LIMIT_WINDOW
                },
                '/api/v2/auth/login': {
                    'limit': self.settings.LOGIN_RATE_LIMIT,
                    'window': self.settings.LOGIN_RATE_LIMIT_WINDOW
                },
                '/api/v1/users': {
                    'limit': self.settings.USER_API_RATE_LIMIT,
                    'window': self.settings.USER_API_RATE_LIMIT_WINDOW
                },
                '/api/v2/users': {
                    'limit': self.settings.USER_API_RATE_LIMIT,
                    'window': self.settings.USER_API_RATE_LIMIT_WINDOW
                },
            }
        }
    
    def get_input_validation_config(self) -> Dict:
        """获取输入验证配置"""
        return {
            'enable_xss_protection': self.settings.ENABLE_XSS_PROTECTION,
            'enable_sql_injection_protection': self.settings.ENABLE_SQL_INJECTION_PROTECTION,
            'enable_input_sanitization': self.settings.ENABLE_INPUT_SANITIZATION,
            'allowed_html_tags': self.settings.ALLOWED_HTML_TAGS
        }
    
    def get_middleware_config(self) -> Dict:
        """获取完整的中间件配置"""
        return {
            'enable_security_headers': self.settings.ENABLE_SECURITY_HEADERS,
            'enable_rate_limiting': self.settings.ENABLE_RATE_LIMITING,
            'enable_input_validation': self.settings.ENABLE_INPUT_VALIDATION,
            **self.get_rate_limit_config(),
            **self.get_input_validation_config()
        }
    
    def is_development_mode(self) -> bool:
        """检查是否为开发模式"""
        return os.getenv('ENVIRONMENT', 'development').lower() == 'development'
    
    def get_production_security_config(self) -> Dict:
        """获取生产环境安全配置"""
        config = self.get_middleware_config()
        
        if not self.is_development_mode():
            # 生产环境更严格的配置
            config.update({
                'default_limit': 50,  # 更严格的默认限制
                'login_rate_limit': 3,  # 更严格的登录限制
                'enable_input_sanitization': True,  # 启用输入清理
            })
        
        return config


# 全局安全配置实例
security_config_manager = SecurityConfigManager()