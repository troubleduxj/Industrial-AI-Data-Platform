"""
安全验证依赖
使用FastAPI的依赖注入系统进行输入验证
"""

import json
import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SecurityValidator:
    """安全验证器"""
    
    def __init__(self):
        # XSS攻击模式
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'<style[^>]*>.*?</style>',
        ]
        
        # SQL注入模式
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
    
    def _detect_xss(self, text: str) -> bool:
        """检测XSS攻击"""
        if not isinstance(text, str):
            return False
        
        text_lower = text.lower()
        for pattern in self.xss_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                return True
        return False
    
    def _detect_sql_injection(self, text: str) -> bool:
        """检测SQL注入攻击"""
        if not isinstance(text, str):
            return False
        
        text_upper = text.upper()
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, text_upper, re.IGNORECASE):
                return True
        return False
    
    def validate_data(self, data: Any) -> Dict[str, Any]:
        """验证数据"""
        if isinstance(data, str):
            if self._detect_xss(data):
                return {
                    'is_valid': False,
                    'attack_type': 'xss',
                    'malicious_content': data[:500]
                }
            if self._detect_sql_injection(data):
                return {
                    'is_valid': False,
                    'attack_type': 'sql_injection',
                    'malicious_content': data[:500]
                }
        elif isinstance(data, dict):
            for key, value in data.items():
                key_result = self.validate_data(key)
                if not key_result['is_valid']:
                    return key_result
                
                value_result = self.validate_data(value)
                if not value_result['is_valid']:
                    return value_result
        elif isinstance(data, list):
            for item in data:
                item_result = self.validate_data(item)
                if not item_result['is_valid']:
                    return item_result
        elif isinstance(data, BaseModel):
            # 验证Pydantic模型
            return self.validate_data(data.dict())
        
        return {'is_valid': True}


# 全局验证器实例
security_validator = SecurityValidator()


async def validate_request_body(request: Request) -> None:
    """
    验证请求体的依赖函数
    可以在需要验证的API端点中使用
    """
    if request.method in ['POST', 'PUT', 'PATCH']:
        content_type = request.headers.get('content-type', '')
        if 'application/json' in content_type:
            try:
                body = await request.body()
                if body:
                    body_str = body.decode('utf-8')
                    data = json.loads(body_str)
                    
                    validation_result = security_validator.validate_data(data)
                    if not validation_result['is_valid']:
                        logger.warning(f"Malicious input detected from IP {request.client.host}")
                        
                        # 记录安全事件
                        try:
                            from app.core.security_monitor import security_event_logger
                            if validation_result['attack_type'] == 'xss':
                                security_event_logger.log_xss_attack(
                                    request, 
                                    validation_result['malicious_content']
                                )
                            elif validation_result['attack_type'] == 'sql_injection':
                                security_event_logger.log_sql_injection(
                                    request, 
                                    validation_result['malicious_content']
                                )
                        except Exception as e:
                            logger.error(f"Failed to log security event: {e}")
                        
                        raise HTTPException(
                            status_code=400,
                            detail={
                                "success": False,
                                "message": "输入包含非法内容",
                                "code": 400,
                                "timestamp": datetime.now().isoformat()
                            }
                        )
            
            except json.JSONDecodeError:
                # 非JSON数据，跳过验证
                pass
            except Exception as e:
                logger.error(f"Error in request body validation: {e}")


def create_input_validator(enable_validation: bool = True):
    """
    创建输入验证依赖
    """
    async def input_validator(request: Request) -> None:
        if enable_validation:
            await validate_request_body(request)
    
    return input_validator


# 默认的输入验证依赖
ValidateInput = Depends(create_input_validator(True))


def validate_pydantic_model(model_data: BaseModel) -> BaseModel:
    """
    验证Pydantic模型的装饰器
    """
    validation_result = security_validator.validate_data(model_data)
    if not validation_result['is_valid']:
        logger.warning(f"Malicious input detected in model data")
        
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": "模型数据包含非法内容",
                "code": 400,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    return model_data


# 安全的Pydantic模型验证依赖
def SecureModel(model_class):
    """
    安全模型验证装饰器
    使用方式: @SecureModel
    """
    def wrapper(model_data: model_class) -> model_class:
        return validate_pydantic_model(model_data)
    
    return Depends(wrapper)