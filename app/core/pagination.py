#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分页工具模块
提供统一的分页参数处理和响应格式化功能
"""

from typing import Dict, Any, Optional
from fastapi import Query


def get_pagination_params(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
) -> Dict[str, int]:
    """
    获取分页参数
    
    Args:
        page: 页码，从1开始
        page_size: 每页数量，最大100
        
    Returns:
        包含分页参数的字典
    """
    return {
        "page": page,
        "page_size": page_size,
        "offset": (page - 1) * page_size,
        "limit": page_size
    }


def create_pagination_response(
    data: list,
    total: int,
    page: int,
    page_size: int,
    **kwargs
) -> Dict[str, Any]:
    """
    创建分页响应数据
    
    Args:
        data: 数据列表
        total: 总记录数
        page: 当前页码
        page_size: 每页数量
        **kwargs: 其他参数
        
    Returns:
        分页响应数据
    """
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    
    return {
        "items": data,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
        **kwargs
    }


def calculate_pagination_info(total: int, page: int, page_size: int) -> Dict[str, Any]:
    """
    计算分页信息
    
    Args:
        total: 总记录数
        page: 当前页码
        page_size: 每页数量
        
    Returns:
        分页信息字典
    """
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    offset = (page - 1) * page_size
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "offset": offset,
        "limit": page_size,
        "has_next": page < total_pages,
        "has_prev": page > 1,
        "start_index": offset + 1 if total > 0 else 0,
        "end_index": min(offset + page_size, total)
    }