#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V2 API输入验证系统
提供统一的输入验证和错误详情返回机制
"""

import re
from typing import Any, Dict, List, Optional, Union, Type
from datetime import datetime, date
from pydantic import BaseModel, ValidationError, Field
from fastapi import Request
from app.core.response_formatter_v2 import APIv2ErrorDetail
from app.core.error_logger import ErrorLogger


class ValidationRule:
    """验证规则基类"""
    
    def __init__(self, field_name: str, message: str = None):
        self.field_name = field_name
        self.message = message or f"字段 {field_name} 验证失败"
    
    def validate(self, value: Any) -> bool:
        """验证值是否符合规则"""
        raise NotImplementedError
    
    def get_error_detail(self, value: Any) -> APIv2ErrorDetail:
        """获取错误详情"""
        # 将值转换为字符串，避免序列化问题
        safe_value = str(value) if value is not None else None
        
        return APIv2ErrorDetail(
            field=self.field_name,
            code=self.__class__.__name__.upper(),
            message=self.message,
            value=safe_value
        )


class RequiredRule(ValidationRule):
    """必填字段验证规则"""
    
    def __init__(self, field_name: str, message: str = None):
        super().__init__(field_name, message or f"字段 {field_name} 是必填的")
    
    def validate(self, value: Any) -> bool:
        return value is not None and value != "" and value != []


class LengthRule(ValidationRule):
    """长度验证规则"""
    
    def __init__(self, field_name: str, min_length: int = None, max_length: int = None, message: str = None):
        self.min_length = min_length
        self.max_length = max_length
        
        if not message:
            if min_length and max_length:
                message = f"字段 {field_name} 长度必须在 {min_length} 到 {max_length} 之间"
            elif min_length:
                message = f"字段 {field_name} 长度不能少于 {min_length}"
            elif max_length:
                message = f"字段 {field_name} 长度不能超过 {max_length}"
        
        super().__init__(field_name, message)
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return True  # 长度验证不检查None值，由RequiredRule处理
        
        length = len(str(value))
        
        if self.min_length and length < self.min_length:
            return False
        if self.max_length and length > self.max_length:
            return False
        
        return True


class PatternRule(ValidationRule):
    """正则表达式验证规则"""
    
    def __init__(self, field_name: str, pattern: str, message: str = None):
        self.pattern = re.compile(pattern)
        super().__init__(field_name, message or f"字段 {field_name} 格式不正确")
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return True  # 格式验证不检查None值
        
        return bool(self.pattern.match(str(value)))


class EmailRule(PatternRule):
    """邮箱验证规则"""
    
    def __init__(self, field_name: str, message: str = None):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        super().__init__(field_name, email_pattern, message or f"字段 {field_name} 必须是有效的邮箱地址")


class PhoneRule(PatternRule):
    """手机号验证规则"""
    
    def __init__(self, field_name: str, message: str = None):
        phone_pattern = r'^1[3-9]\d{9}$'
        super().__init__(field_name, phone_pattern, message or f"字段 {field_name} 必须是有效的手机号")


class RangeRule(ValidationRule):
    """数值范围验证规则"""
    
    def __init__(self, field_name: str, min_value: Union[int, float] = None, max_value: Union[int, float] = None, message: str = None):
        self.min_value = min_value
        self.max_value = max_value
        
        if not message:
            if min_value is not None and max_value is not None:
                message = f"字段 {field_name} 必须在 {min_value} 到 {max_value} 之间"
            elif min_value is not None:
                message = f"字段 {field_name} 不能小于 {min_value}"
            elif max_value is not None:
                message = f"字段 {field_name} 不能大于 {max_value}"
        
        super().__init__(field_name, message)
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        
        try:
            num_value = float(value)
            
            if self.min_value is not None and num_value < self.min_value:
                return False
            if self.max_value is not None and num_value > self.max_value:
                return False
            
            return True
        except (ValueError, TypeError):
            return False


class DateRule(ValidationRule):
    """日期验证规则"""
    
    def __init__(self, field_name: str, date_format: str = "%Y-%m-%d", message: str = None):
        self.date_format = date_format
        super().__init__(field_name, message or f"字段 {field_name} 必须是有效的日期格式 ({date_format})")
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        
        if isinstance(value, (datetime, date)):
            return True
        
        try:
            datetime.strptime(str(value), self.date_format)
            return True
        except ValueError:
            return False


class ChoiceRule(ValidationRule):
    """选择项验证规则"""
    
    def __init__(self, field_name: str, choices: List[Any], message: str = None):
        self.choices = choices
        super().__init__(field_name, message or f"字段 {field_name} 必须是以下值之一: {', '.join(map(str, choices))}")
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return True
        
        return value in self.choices


class CustomRule(ValidationRule):
    """自定义验证规则"""
    
    def __init__(self, field_name: str, validator_func: callable, message: str = None):
        self.validator_func = validator_func
        super().__init__(field_name, message or f"字段 {field_name} 验证失败")
    
    def validate(self, value: Any) -> bool:
        try:
            return self.validator_func(value)
        except Exception:
            return False


class InputValidator:
    """输入验证器"""
    
    def __init__(self, request: Optional[Request] = None):
        self.request = request
        self.rules: Dict[str, List[ValidationRule]] = {}
        self.errors: List[APIv2ErrorDetail] = []
    
    def add_rule(self, field_name: str, rule: ValidationRule) -> 'InputValidator':
        """添加验证规则"""
        if field_name not in self.rules:
            self.rules[field_name] = []
        self.rules[field_name].append(rule)
        return self
    
    def required(self, field_name: str, message: str = None) -> 'InputValidator':
        """添加必填验证"""
        return self.add_rule(field_name, RequiredRule(field_name, message))
    
    def length(self, field_name: str, min_length: int = None, max_length: int = None, message: str = None) -> 'InputValidator':
        """添加长度验证"""
        return self.add_rule(field_name, LengthRule(field_name, min_length, max_length, message))
    
    def pattern(self, field_name: str, pattern: str, message: str = None) -> 'InputValidator':
        """添加正则表达式验证"""
        return self.add_rule(field_name, PatternRule(field_name, pattern, message))
    
    def email(self, field_name: str, message: str = None) -> 'InputValidator':
        """添加邮箱验证"""
        return self.add_rule(field_name, EmailRule(field_name, message))
    
    def phone(self, field_name: str, message: str = None) -> 'InputValidator':
        """添加手机号验证"""
        return self.add_rule(field_name, PhoneRule(field_name, message))
    
    def range(self, field_name: str, min_value: Union[int, float] = None, max_value: Union[int, float] = None, message: str = None) -> 'InputValidator':
        """添加数值范围验证"""
        return self.add_rule(field_name, RangeRule(field_name, min_value, max_value, message))
    
    def date(self, field_name: str, date_format: str = "%Y-%m-%d", message: str = None) -> 'InputValidator':
        """添加日期验证"""
        return self.add_rule(field_name, DateRule(field_name, date_format, message))
    
    def choice(self, field_name: str, choices: List[Any], message: str = None) -> 'InputValidator':
        """添加选择项验证"""
        return self.add_rule(field_name, ChoiceRule(field_name, choices, message))
    
    def custom(self, field_name: str, validator_func: callable, message: str = None) -> 'InputValidator':
        """添加自定义验证"""
        return self.add_rule(field_name, CustomRule(field_name, validator_func, message))
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """执行验证"""
        self.errors.clear()
        
        for field_name, rules in self.rules.items():
            field_value = data.get(field_name)
            
            for rule in rules:
                if not rule.validate(field_value):
                    self.errors.append(rule.get_error_detail(field_value))
        
        # 记录验证错误日志
        if self.errors and self.request:
            user_id = getattr(self.request.state, 'user_id', None)
            ErrorLogger.log_validation_error(
                request=self.request,
                validation_errors=[error.model_dump() for error in self.errors],
                user_id=user_id
            )
        
        return len(self.errors) == 0
    
    def get_errors(self) -> List[APIv2ErrorDetail]:
        """获取验证错误列表"""
        return self.errors
    
    def get_first_error(self) -> Optional[APIv2ErrorDetail]:
        """获取第一个验证错误"""
        return self.errors[0] if self.errors else None
    
    def get_errors_by_field(self, field_name: str) -> List[APIv2ErrorDetail]:
        """获取指定字段的验证错误"""
        return [error for error in self.errors if error.field == field_name]


class BatchValidator:
    """批量操作验证器"""
    
    def __init__(self, request: Optional[Request] = None):
        self.request = request
    
    def validate_batch_delete(self, data: Dict[str, Any]) -> List[APIv2ErrorDetail]:
        """验证批量删除请求"""
        validator = InputValidator(self.request)
        
        validator.required("ids", "请提供要删除的ID列表") \
                .custom("ids", lambda x: isinstance(x, list), "ids必须是数组") \
                .custom("ids", lambda x: len(x) > 0 if isinstance(x, list) else False, "至少需要提供一个ID") \
                .custom("ids", lambda x: len(x) <= 100 if isinstance(x, list) else False, "一次最多只能删除100个项目") \
                .custom("ids", lambda x: all(isinstance(id, int) and id > 0 for id in x) if isinstance(x, list) else False, "所有ID必须是正整数")
        
        # 验证force参数（可选）
        if "force" in data:
            validator.custom("force", lambda x: isinstance(x, bool), "force参数必须是布尔值")
        
        validator.validate(data)
        return validator.get_errors()
    
    def validate_batch_update(self, data: Dict[str, Any]) -> List[APIv2ErrorDetail]:
        """验证批量更新请求"""
        validator = InputValidator(self.request)
        
        validator.required("ids", "请提供要更新的ID列表") \
                .custom("ids", lambda x: isinstance(x, list), "ids必须是数组") \
                .custom("ids", lambda x: len(x) > 0 if isinstance(x, list) else False, "至少需要提供一个ID") \
                .custom("ids", lambda x: len(x) <= 100 if isinstance(x, list) else False, "一次最多只能更新100个项目") \
                .required("update_data", "请提供更新数据") \
                .custom("update_data", lambda x: isinstance(x, dict), "update_data必须是对象")
        
        validator.validate(data)
        return validator.get_errors()


def create_validator(request: Optional[Request] = None) -> InputValidator:
    """创建输入验证器实例"""
    return InputValidator(request)


def create_batch_validator(request: Optional[Request] = None) -> BatchValidator:
    """创建批量操作验证器实例"""
    return BatchValidator(request)


# 常用验证规则预设
class CommonValidators:
    """常用验证规则预设"""
    
    @staticmethod
    def username_validator(request: Optional[Request] = None) -> InputValidator:
        """用户名验证器"""
        return (InputValidator(request)
                .required("username", "用户名不能为空")
                .length("username", 3, 50, "用户名长度必须在3-50个字符之间")
                .pattern("username", r'^[a-zA-Z0-9_]+$', "用户名只能包含字母、数字和下划线"))
    
    @staticmethod
    def password_validator(request: Optional[Request] = None) -> InputValidator:
        """密码验证器"""
        return (InputValidator(request)
                .required("password", "密码不能为空")
                .length("password", 6, 128, "密码长度必须在6-128个字符之间")
                .custom("password", 
                       lambda x: bool(re.search(r'[A-Za-z]', str(x))) and bool(re.search(r'\d', str(x))),
                       "密码必须包含至少一个字母和一个数字"))
    
    @staticmethod
    def email_validator(request: Optional[Request] = None) -> InputValidator:
        """邮箱验证器"""
        return (InputValidator(request)
                .required("email", "邮箱不能为空")
                .email("email", "请输入有效的邮箱地址"))
    
    @staticmethod
    def phone_validator(request: Optional[Request] = None) -> InputValidator:
        """手机号验证器"""
        return (InputValidator(request)
                .required("phone", "手机号不能为空")
                .phone("phone", "请输入有效的手机号"))
    
    @staticmethod
    def pagination_validator(request: Optional[Request] = None) -> InputValidator:
        """分页参数验证器"""
        return (InputValidator(request)
                .range("page", 1, None, "页码必须大于0")
                .range("page_size", 1, 100, "每页数量必须在1-100之间"))