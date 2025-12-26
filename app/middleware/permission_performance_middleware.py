#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限验证性能监控中间件
提供权限验证的性能监控和优化
"""

import time
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.permission_performance_optimizer import permission_performance_optimizer
from app.log import logger


class PermissionPerformanceMiddleware(BaseHTTPMiddleware):
    """权限验证性能监控中间件"""
    
    def __init__(self, app, enable_monitoring: bool = True):
        super().__init__(app)
        self.enable_monitoring = enable_monitoring
        self.optimizer = permission_performance_optimizer
        
        # 性能阈值配置
        self.slow_request_threshold = 100  # 100ms
        self.error_rate_threshold = 5  # 5%
        
        # 监控统计
        self.request_stats = {
            "total_requests": 0,
            "slow_requests": 0,
            "error_requests": 0,
            "total_time": 0.0
        }
        
        # 最近请求记录（用于分析）
        self.recent_requests = []
        self.max_recent_requests = 1000
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        if not self.enable_monitoring:
            return await call_next(request)
        
        start_time = time.time()
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "user_id": None,
            "start_time": start_time,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 获取用户ID（如果存在）
            user_id = await self._extract_user_id(request)
            request_info["user_id"] = user_id
            
            # 执行请求
            response = await call_next(request)
            
            # 计算响应时间
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # 转换为毫秒
            
            # 更新请求信息
            request_info.update({
                "response_time": response_time,
                "status_code": response.status_code,
                "success": 200 <= response.status_code < 400
            })
            
            # 记录性能数据
            await self._record_performance_data(request_info)
            
            # 添加性能头信息
            if hasattr(response, 'headers'):
                response.headers["X-Permission-Response-Time"] = f"{response_time:.2f}ms"
                response.headers["X-Permission-Cache-Status"] = await self._get_cache_status()
            
            return response
            
        except Exception as e:
            # 记录错误
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            request_info.update({
                "response_time": response_time,
                "status_code": 500,
                "success": False,
                "error": str(e)
            })
            
            await self._record_performance_data(request_info)
            
            logger.error(f"权限中间件处理请求失败: {str(e)}")
            
            # 返回错误响应
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "request_id": id(request)}
            )
    
    async def _extract_user_id(self, request: Request) -> Optional[int]:
        """提取用户ID"""
        try:
            # 从JWT token中提取
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # 这里应该解析JWT token获取user_id
                # 暂时返回None，实际实现需要根据具体的认证方式
                pass
            
            # 从session中提取
            if hasattr(request, 'session') and 'user_id' in request.session:
                return request.session['user_id']
            
            # 从请求参数中提取（仅用于测试）
            if 'user_id' in request.query_params:
                return int(request.query_params['user_id'])
            
            return None
            
        except Exception as e:
            logger.error(f"提取用户ID失败: {str(e)}")
            return None
    
    async def _record_performance_data(self, request_info: Dict[str, Any]):
        """记录性能数据"""
        try:
            # 更新统计信息
            self.request_stats["total_requests"] += 1
            self.request_stats["total_time"] += request_info["response_time"]
            
            if request_info["response_time"] > self.slow_request_threshold:
                self.request_stats["slow_requests"] += 1
            
            if not request_info["success"]:
                self.request_stats["error_requests"] += 1
            
            # 记录最近请求
            self.recent_requests.append(request_info)
            if len(self.recent_requests) > self.max_recent_requests:
                self.recent_requests = self.recent_requests[-self.max_recent_requests:]
            
            # 性能告警检查
            await self._check_performance_alerts(request_info)
            
        except Exception as e:
            logger.error(f"记录性能数据失败: {str(e)}")
    
    async def _check_performance_alerts(self, request_info: Dict[str, Any]):
        """检查性能告警"""
        try:
            # 慢请求告警
            if request_info["response_time"] > self.slow_request_threshold:
                logger.warning(
                    f"慢权限请求: {request_info['method']} {request_info['url']}, "
                    f"响应时间: {request_info['response_time']:.2f}ms, "
                    f"用户ID: {request_info['user_id']}"
                )
            
            # 错误率告警
            if self.request_stats["total_requests"] > 100:
                error_rate = (self.request_stats["error_requests"] / self.request_stats["total_requests"]) * 100
                if error_rate > self.error_rate_threshold:
                    logger.warning(f"权限验证错误率过高: {error_rate:.1f}%")
            
            # 平均响应时间告警
            if self.request_stats["total_requests"] > 10:
                avg_response_time = self.request_stats["total_time"] / self.request_stats["total_requests"]
                if avg_response_time > self.slow_request_threshold:
                    logger.warning(f"权限验证平均响应时间过高: {avg_response_time:.2f}ms")
                    
        except Exception as e:
            logger.error(f"性能告警检查失败: {str(e)}")
    
    async def _get_cache_status(self) -> str:
        """获取缓存状态"""
        try:
            metrics = self.optimizer.metrics
            if metrics.total_requests > 0:
                hit_rate = metrics.hit_rate
                if hit_rate > 90:
                    return "excellent"
                elif hit_rate > 70:
                    return "good"
                elif hit_rate > 50:
                    return "fair"
                else:
                    return "poor"
            return "unknown"
        except Exception:
            return "error"
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        try:
            total_requests = self.request_stats["total_requests"]
            
            if total_requests == 0:
                return {
                    "total_requests": 0,
                    "avg_response_time": 0,
                    "slow_request_rate": 0,
                    "error_rate": 0,
                    "status": "no_data"
                }
            
            avg_response_time = self.request_stats["total_time"] / total_requests
            slow_request_rate = (self.request_stats["slow_requests"] / total_requests) * 100
            error_rate = (self.request_stats["error_requests"] / total_requests) * 100
            
            # 性能状态评估
            status = "excellent"
            if avg_response_time > self.slow_request_threshold or error_rate > self.error_rate_threshold:
                status = "poor"
            elif avg_response_time > self.slow_request_threshold * 0.7 or error_rate > self.error_rate_threshold * 0.7:
                status = "fair"
            elif avg_response_time > self.slow_request_threshold * 0.5 or error_rate > self.error_rate_threshold * 0.5:
                status = "good"
            
            return {
                "total_requests": total_requests,
                "avg_response_time": f"{avg_response_time:.2f}ms",
                "slow_request_rate": f"{slow_request_rate:.1f}%",
                "error_rate": f"{error_rate:.1f}%",
                "status": status,
                "optimizer_metrics": self.optimizer.get_performance_report()["current_metrics"]
            }
            
        except Exception as e:
            logger.error(f"获取性能摘要失败: {str(e)}")
            return {"error": str(e)}
    
    def get_recent_slow_requests(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的慢请求"""
        try:
            slow_requests = [
                req for req in self.recent_requests
                if req["response_time"] > self.slow_request_threshold
            ]
            
            # 按响应时间降序排序
            slow_requests.sort(key=lambda x: x["response_time"], reverse=True)
            
            return slow_requests[:limit]
            
        except Exception as e:
            logger.error(f"获取慢请求失败: {str(e)}")
            return []
    
    def get_error_requests(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取错误请求"""
        try:
            error_requests = [
                req for req in self.recent_requests
                if not req["success"]
            ]
            
            # 按时间降序排序
            error_requests.sort(key=lambda x: x["start_time"], reverse=True)
            
            return error_requests[:limit]
            
        except Exception as e:
            logger.error(f"获取错误请求失败: {str(e)}")
            return []
    
    def reset_stats(self):
        """重置统计信息"""
        self.request_stats = {
            "total_requests": 0,
            "slow_requests": 0,
            "error_requests": 0,
            "total_time": 0.0
        }
        self.recent_requests.clear()
        logger.info("权限性能中间件统计信息已重置")


# 创建中间件实例的工厂函数
def create_permission_performance_middleware(enable_monitoring: bool = True):
    """创建权限性能监控中间件"""
    def middleware_factory(app):
        return PermissionPerformanceMiddleware(app, enable_monitoring)
    return middleware_factory