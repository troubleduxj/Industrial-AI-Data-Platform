"""
安全中间件模块
实现安全头设置、请求频率限制、输入验证和XSS防护
"""

import re
import time
import json
from datetime import datetime
from typing import Dict, Optional, Any, List
import logging

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全头设置中间件
    添加各种安全相关的HTTP头
    """
    
    def __init__(self, app, **kwargs):
        super().__init__(app)
        self.security_headers = {
            # 防止点击劫持
            "X-Frame-Options": "DENY",
            # 防止MIME类型嗅探
            "X-Content-Type-Options": "nosniff",
            # XSS保护
            "X-XSS-Protection": "1; mode=block",
            # 强制HTTPS（在生产环境中启用）
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            # 内容安全策略 - 现在从配置文件读取
            # "Content-Security-Policy" 将由 SecurityConfig 设置
            # 推荐人策略
            "Referrer-Policy": "strict-origin-when-cross-origin",
            # 权限策略
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """处理请求并添加安全头"""
        response = await call_next(request)
        
        # 添加安全头
        for header_name, header_value in self.security_headers.items():
            response.headers[header_name] = header_value
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    请求频率限制中间件
    防止API滥用和DDoS攻击
    """
    
    def __init__(self, app, **kwargs):
        super().__init__(app)
        # 默认限制配置：每分钟最多100个请求
        self.default_limit = kwargs.get('default_limit', 100)
        self.window_size = kwargs.get('window_size', 60)  # 时间窗口（秒）
        
        # 不同路径的特殊限制
        self.path_limits = {
            '/api/v1/auth/login': {'limit': 5, 'window': 300},  # 登录接口：5分钟内最多5次
            '/api/v2/auth/login': {'limit': 5, 'window': 300},
            '/api/v1/users': {'limit': 50, 'window': 60},       # 用户接口：每分钟50次
            '/api/v2/users': {'limit': 50, 'window': 60},
        }
        
        # 白名单IP（不受限制）
        self.whitelist_ips = kwargs.get('whitelist_ips', ['127.0.0.1', '::1'])
        
        # 内存存储请求记录（生产环境建议使用Redis）
        self.request_records: Dict[str, List[float]] = {}
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 优先从X-Forwarded-For头获取真实IP
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        # 从X-Real-IP头获取
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # 最后使用客户端IP
        return request.client.host if request.client else '127.0.0.1'
    
    def _get_rate_limit_config(self, path: str) -> Dict[str, int]:
        """获取路径对应的限制配置"""
        for pattern, config in self.path_limits.items():
            if path.startswith(pattern):
                return config
        return {'limit': self.default_limit, 'window': self.window_size}
    
    def _is_rate_limited(self, client_ip: str, path: str) -> bool:
        """检查是否超过频率限制"""
        if client_ip in self.whitelist_ips:
            return False
        
        config = self._get_rate_limit_config(path)
        limit = config['limit']
        window = config['window']
        
        key = f"{client_ip}:{path}"
        current_time = time.time()
        
        # 获取或初始化请求记录
        if key not in self.request_records:
            self.request_records[key] = []
        
        # 清理过期记录
        self.request_records[key] = [
            timestamp for timestamp in self.request_records[key]
            if current_time - timestamp < window
        ]
        
        # 检查是否超过限制
        if len(self.request_records[key]) >= limit:
            return True
        
        # 记录当前请求
        self.request_records[key].append(current_time)
        return False
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """处理请求并检查频率限制"""
        client_ip = self._get_client_ip(request)
        path = request.url.path
        
        # 检查频率限制
        if self._is_rate_limited(client_ip, path):
            config = self._get_rate_limit_config(path)
            logger.warning(f"Rate limit exceeded for IP {client_ip} on path {path}")
            
            # 记录安全事件
            try:
                security_event_logger = get_security_event_logger()
                security_event_logger.log_rate_limit_exceeded(
                    request, 
                    config['limit'], 
                    config['window']
                )
            except Exception as e:
                logger.error(f"Failed to log security event: {e}")
            
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "请求过于频繁，请稍后再试",
                    "code": 429,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        response = await call_next(request)
        return response





class SecurityMiddleware(BaseHTTPMiddleware):
    """
    综合安全中间件
    整合所有安全功能
    """
    
    def __init__(self, app, **kwargs):
        super().__init__(app)
        self.enable_security_headers = kwargs.get('enable_security_headers', True)
        self.enable_rate_limiting = kwargs.get('enable_rate_limiting', True)
        self.enable_input_validation = kwargs.get('enable_input_validation', True)
        
        # 初始化子中间件
        if self.enable_security_headers:
            self.security_headers_middleware = SecurityHeadersMiddleware(app, **kwargs)
        
        if self.enable_rate_limiting:
            self.rate_limit_middleware = RateLimitMiddleware(app, **kwargs)
        
        if self.enable_input_validation:
            # 直接在主中间件中处理输入验证
            self._init_validation_patterns()
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """处理请求并应用所有安全措施"""
        
        # 应用输入验证（URL参数和请求头）
        if self.enable_input_validation:
            # 直接在这里进行验证，不调用子中间件的dispatch
            validation_result = self._validate_request_inputs(request)
            if not validation_result['is_valid']:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "message": validation_result.get('message', '请求包含非法内容'),
                        "code": 400,
                        "timestamp": datetime.now().isoformat()
                    }
                )
        
        # 应用频率限制
        if self.enable_rate_limiting:
            client_ip = self.rate_limit_middleware._get_client_ip(request)
            path = request.url.path
            
            # 检查频率限制
            if self.rate_limit_middleware._is_rate_limited(client_ip, path):
                config = self.rate_limit_middleware._get_rate_limit_config(path)
                logger.warning(f"Rate limit exceeded for IP {client_ip} on path {path}")
                
                # 记录安全事件
                try:
                    security_event_logger = get_security_event_logger()
                    security_event_logger.log_rate_limit_exceeded(
                        request, 
                        config['limit'], 
                        config['window']
                    )
                except Exception as e:
                    logger.error(f"Failed to log security event: {e}")
                
                return JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "message": "请求过于频繁，请稍后再试",
                        "code": 429,
                        "timestamp": datetime.now().isoformat()
                    }
                )
        
        # 执行实际请求
        response = await call_next(request)
        
        # 应用安全头
        if self.enable_security_headers:
            for header_name, header_value in self.security_headers_middleware.security_headers.items():
                response.headers[header_name] = header_value
        
        return response
    
    def _init_validation_patterns(self):
        """初始化验证模式"""
        # XSS攻击模式（简化版）
        self.xss_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
        ]
        
        # SQL注入模式（简化版）
        self.sql_injection_patterns = [
            r'(\bSELECT\b.*\bFROM\b)',
            r'(\bINSERT\b.*\bINTO\b)',
            r'(\bUPDATE\b.*\bSET\b)',
            r'(\bDELETE\b.*\bFROM\b)',
            r'(\bUNION\b.*\bSELECT\b)',
            r'(--|#)',
            r'(\bOR\b.*=.*)',
            r'(\bAND\b.*=.*)',
        ]
    
    def _detect_attack(self, text: str) -> Dict[str, Any]:
        """检测攻击模式"""
        if not isinstance(text, str):
            return {'is_valid': True}
        
        text_lower = text.lower()
        
        # 检测XSS
        for pattern in self.xss_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return {
                    'is_valid': False,
                    'attack_type': 'xss',
                    'malicious_content': text[:500]
                }
        
        # 检测SQL注入
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return {
                    'is_valid': False,
                    'attack_type': 'sql_injection',
                    'malicious_content': text[:500]
                }
        
        return {'is_valid': True}
    
    def _validate_request_inputs(self, request: Request) -> Dict[str, Any]:
        """验证请求输入（URL参数和请求头）"""
        try:
            # 验证查询参数
            query_params = str(request.url.query)
            if query_params:
                validation_result = self._detect_attack(query_params)
                if not validation_result['is_valid']:
                    logger.warning(f"Malicious query params detected from IP {request.client.host}")
                    
                    # 记录安全事件
                    try:
                        security_event_logger = get_security_event_logger()
                        if validation_result['attack_type'] == 'xss':
                            security_event_logger.log_xss_attack(request, validation_result['malicious_content'])
                        elif validation_result['attack_type'] == 'sql_injection':
                            security_event_logger.log_sql_injection(request, validation_result['malicious_content'])
                    except Exception as e:
                        logger.error(f"Failed to log security event: {e}")
                    
                    return {
                        'is_valid': False,
                        'message': '请求参数包含非法内容'
                    }
            
            # 验证关键请求头
            dangerous_headers = ['user-agent', 'referer', 'x-forwarded-for']
            for header_name in dangerous_headers:
                header_value = request.headers.get(header_name, '')
                if header_value:
                    validation_result = self._detect_attack(header_value)
                    if not validation_result['is_valid']:
                        logger.warning(f"Malicious header detected from IP {request.client.host}")
                        
                        try:
                            security_event_logger = get_security_event_logger()
                            security_event_logger.log_malicious_input(
                                request,
                                f"{header_name}: {validation_result['malicious_content']}",
                                validation_result['attack_type']
                            )
                        except Exception as e:
                            logger.error(f"Failed to log security event: {e}")
                        
                        return {
                            'is_valid': False,
                            'message': '请求头包含非法内容'
                        }
            
            return {'is_valid': True}
            
        except Exception as e:
            logger.error(f"Error in input validation: {e}")
            return {'is_valid': True}  # 验证失败时允许通过，避免阻塞正常请求


# 延迟导入，避免循环导入
def get_security_config_manager():
    from app.core.security_config import security_config_manager
    return security_config_manager

def get_security_event_logger():
    from app.core.security_monitor import security_event_logger
    return security_event_logger

# 保持向后兼容的SecurityConfig类
class SecurityConfig:
    """安全配置管理（向后兼容）"""
    
    def __init__(self):
        self.config_manager = get_security_config_manager()
    
    def get_middleware_config(self) -> dict:
        """获取中间件配置"""
        return self.config_manager.get_middleware_config()


# 工具函数
def create_security_middleware(app, config: Optional[SecurityConfig] = None):
    """创建安全中间件实例"""
    if config is None:
        config = SecurityConfig()
    
    return SecurityMiddleware(app, **config.get_middleware_config())


def log_security_event(event_type: str, details: dict, request: Request = None):
    """记录安全事件"""
    log_data = {
        'event_type': event_type,
        'timestamp': datetime.now().isoformat(),
        'details': details
    }
    
    if request:
        log_data.update({
            'client_ip': request.client.host if request.client else 'unknown',
            'user_agent': request.headers.get('User-Agent', 'unknown'),
            'path': request.url.path,
            'method': request.method
        })
    
    logger.warning(f"Security Event: {json.dumps(log_data)}")


# 安全检查装饰器
def security_check(check_xss: bool = True, check_sql_injection: bool = True):
    """安全检查装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 这里可以添加额外的安全检查逻辑
            return await func(*args, **kwargs)
        return wrapper
    return decorator