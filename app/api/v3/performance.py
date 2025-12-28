#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工业AI数据平台性能监控API
提供API响应时间监控、性能统计和健康检查接口

需求映射：
- 需求9.1: API响应时间亚秒级保证
- 需求9.2: 水平扩展支持
- 需求9.5: 99.9%正常运行时间
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from app.services.platform_performance_service import (
    platform_performance_service,
    PerformanceThresholds
)
from app.core.auth_dependencies import get_current_user, get_current_active_user
from app.models.admin import User
from app.core.unified_logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/performance", tags=["性能监控"])


# ==================== 响应模型 ====================

class PerformanceSummaryResponse(BaseModel):
    """性能摘要响应"""
    time_range_minutes: int = Field(..., description="统计时间范围（分钟）")
    timestamp: str = Field(..., description="统计时间戳")
    api: dict = Field(..., description="API性能统计")
    database: dict = Field(..., description="数据库性能统计")
    cache: dict = Field(..., description="缓存统计")
    concurrent_requests: dict = Field(..., description="并发请求统计")


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="健康状态")
    timestamp: str = Field(..., description="检查时间戳")
    issues: list = Field(..., description="问题列表")
    summary: dict = Field(..., description="性能摘要")


class EndpointStatsResponse(BaseModel):
    """端点统计响应"""
    endpoint: str = Field(..., description="端点")
    count: int = Field(..., description="调用次数")
    avg_duration: float = Field(..., description="平均响应时间")
    min_duration: float = Field(..., description="最小响应时间")
    max_duration: float = Field(..., description="最大响应时间")
    error_count: int = Field(..., description="错误次数")
    error_rate: float = Field(..., description="错误率")


# ==================== 性能监控接口 ====================

@router.get("/summary", summary="获取性能摘要")
async def get_performance_summary(
    minutes: int = Query(60, ge=1, le=1440, description="统计时间范围（分钟）"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取系统性能摘要
    
    - API响应时间统计
    - 数据库查询统计
    - 缓存命中率统计
    - 并发请求统计
    """
    summary = platform_performance_service.get_performance_summary(minutes=minutes)
    
    return {
        "success": True,
        "message": "获取性能摘要成功",
        "data": summary,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/health", summary="健康检查")
async def health_check():
    """
    系统健康检查
    
    - 检查API响应时间是否达标
    - 检查错误率是否正常
    - 检查缓存命中率
    - 返回健康状态和问题列表
    """
    health = platform_performance_service.check_health()
    
    return {
        "success": True,
        "message": "健康检查完成",
        "data": health,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/slow-endpoints", summary="获取慢端点列表")
async def get_slow_endpoints(
    threshold_ms: float = Query(500, ge=0, description="响应时间阈值（毫秒）"),
    limit: int = Query(10, ge=1, le=100, description="返回数量限制"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取响应时间超过阈值的端点列表
    
    - 按平均响应时间排序
    - 包含调用次数和错误率
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    slow_endpoints = platform_performance_service.get_slow_endpoints(
        threshold_ms=threshold_ms,
        limit=limit
    )
    
    return {
        "success": True,
        "message": "获取慢端点列表成功",
        "data": slow_endpoints,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/endpoint-stats", summary="获取端点统计")
async def get_endpoint_stats(
    endpoint: Optional[str] = Query(None, description="端点名称"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取端点性能统计
    
    - 如果指定端点，返回该端点的详细统计
    - 如果不指定，返回所有端点的统计
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    stats = platform_performance_service.get_endpoint_stats(endpoint=endpoint)
    
    return {
        "success": True,
        "message": "获取端点统计成功",
        "data": stats,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/concurrent-requests", summary="获取并发请求统计")
async def get_concurrent_requests(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前并发请求统计
    
    - 当前并发请求数
    - 历史最大并发请求数
    """
    current = platform_performance_service.get_concurrent_requests()
    
    return {
        "success": True,
        "message": "获取并发请求统计成功",
        "data": {
            "current": current,
            "max": platform_performance_service._max_concurrent_requests
        },
        "timestamp": datetime.now().isoformat()
    }


@router.get("/thresholds", summary="获取性能阈值配置")
async def get_performance_thresholds(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取性能阈值配置
    
    - API响应时间阈值
    - 数据库查询阈值
    - 缓存命中率阈值
    - 错误率阈值
    """
    thresholds = {
        "api_response": {
            "warning_ms": PerformanceThresholds.API_RESPONSE_WARNING_MS,
            "critical_ms": PerformanceThresholds.API_RESPONSE_CRITICAL_MS
        },
        "db_query": {
            "warning_ms": PerformanceThresholds.DB_QUERY_WARNING_MS,
            "critical_ms": PerformanceThresholds.DB_QUERY_CRITICAL_MS
        },
        "cache_hit_rate": {
            "warning": PerformanceThresholds.CACHE_HIT_RATE_WARNING
        },
        "error_rate": {
            "warning": PerformanceThresholds.ERROR_RATE_WARNING,
            "critical": PerformanceThresholds.ERROR_RATE_CRITICAL
        }
    }
    
    return {
        "success": True,
        "message": "获取性能阈值成功",
        "data": thresholds,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/cache/invalidate", summary="使缓存失效")
async def invalidate_cache(
    resource_type: str = Query(..., description="资源类型"),
    resource_id: Optional[str] = Query(None, description="资源ID"),
    current_user: User = Depends(get_current_active_user)
):
    """
    使指定缓存失效
    
    - 如果指定resource_id，使单个缓存失效
    - 如果不指定，使该类型所有缓存失效
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    if resource_id:
        await platform_performance_service.invalidate_cache(resource_type, resource_id)
        message = f"缓存已失效: {resource_type}/{resource_id}"
    else:
        await platform_performance_service.invalidate_cache_pattern(resource_type)
        message = f"缓存已批量失效: {resource_type}/*"
    
    return {
        "success": True,
        "message": message,
        "data": None,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/cache/stats", summary="获取缓存统计")
async def get_cache_stats(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取缓存统计信息
    
    - 总操作数
    - 命中次数
    - 未命中次数
    - 命中率
    """
    stats = dict(platform_performance_service.cache_stats)
    
    return {
        "success": True,
        "message": "获取缓存统计成功",
        "data": stats,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/cache/config", summary="获取缓存配置")
async def get_cache_config(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取缓存配置
    
    - 各资源类型的TTL配置
    - 缓存键前缀配置
    """
    config = dict(platform_performance_service.cache_config)
    
    return {
        "success": True,
        "message": "获取缓存配置成功",
        "data": config,
        "timestamp": datetime.now().isoformat()
    }


# ==================== SLA监控接口 ====================

@router.get("/sla", summary="获取SLA指标")
async def get_sla_metrics(
    minutes: int = Query(60, ge=1, le=1440, description="统计时间范围（分钟）"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取SLA相关指标
    
    - 亚秒级响应率（目标：>95%）
    - 错误率（目标：<1%）
    - 可用性（目标：99.9%）
    """
    summary = platform_performance_service.get_performance_summary(minutes=minutes)
    
    api_stats = summary.get('api', {})
    
    sla_metrics = {
        "time_range_minutes": minutes,
        "response_time": {
            "avg_ms": api_stats.get('avg_response_time_ms', 0),
            "max_ms": api_stats.get('max_response_time_ms', 0),
            "under_1s_rate": api_stats.get('requests_under_1s_rate', 1.0),
            "target": 0.95,
            "status": "pass" if api_stats.get('requests_under_1s_rate', 1.0) >= 0.95 else "fail"
        },
        "error_rate": {
            "current": api_stats.get('error_rate', 0),
            "target": 0.01,
            "status": "pass" if api_stats.get('error_rate', 0) <= 0.01 else "fail"
        },
        "availability": {
            "total_requests": api_stats.get('total_requests', 0),
            "successful_requests": api_stats.get('total_requests', 0) - api_stats.get('error_count', 0),
            "rate": 1 - api_stats.get('error_rate', 0),
            "target": 0.999,
            "status": "pass" if (1 - api_stats.get('error_rate', 0)) >= 0.999 else "fail"
        },
        "overall_status": "healthy"
    }
    
    # 计算整体状态
    if sla_metrics["response_time"]["status"] == "fail" or \
       sla_metrics["error_rate"]["status"] == "fail" or \
       sla_metrics["availability"]["status"] == "fail":
        sla_metrics["overall_status"] = "degraded"
    
    return {
        "success": True,
        "message": "获取SLA指标成功",
        "data": sla_metrics,
        "timestamp": datetime.now().isoformat()
    }
