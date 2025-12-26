#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
响应处理模块
提供统一的API响应格式
"""

from typing import Any, Optional
from app.schemas.base import Success, Fail, SuccessExtra


def success(
    data: Optional[Any] = None,
    msg: Optional[str] = "操作成功",
    code: int = 200,
    **kwargs
) -> Success:
    """
    成功响应
    
    Args:
        data: 响应数据
        msg: 响应消息
        code: 响应状态码
        **kwargs: 其他参数
    
    Returns:
        Success: 成功响应对象
    """
    return Success(code=code, msg=msg, data=data, **kwargs)


def fail(
    msg: Optional[str] = "操作失败",
    data: Optional[Any] = None,
    code: int = 400,
    **kwargs
) -> Fail:
    """
    失败响应
    
    Args:
        msg: 错误消息
        data: 响应数据
        code: 错误状态码
        **kwargs: 其他参数
    
    Returns:
        Fail: 失败响应对象
    """
    return Fail(code=code, msg=msg, data=data, **kwargs)


def success_extra(
    data: Optional[Any] = None,
    msg: Optional[str] = "操作成功",
    total: int = 0,
    page: int = 1,
    page_size: int = 20,
    code: int = 200,
    **kwargs
) -> SuccessExtra:
    """
    带分页信息的成功响应
    
    Args:
        data: 响应数据
        msg: 响应消息
        total: 总记录数
        page: 当前页码
        page_size: 每页大小
        code: 响应状态码
        **kwargs: 其他参数
    
    Returns:
        SuccessExtra: 带分页信息的成功响应对象
    """
    return SuccessExtra(
        code=code,
        msg=msg,
        data=data,
        total=total,
        page=page,
        page_size=page_size,
        **kwargs
    )