#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限中间件管理器
统一管理和配置所有权限相关的中间件
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque

from app.middleware.permission_middleware import (
    PermissionMiddleware,
    BatchDeletePermissionMiddleware, 
    DataPermissionMiddleware
)
from app.core.unified_logger import get_logger

logger = get_logger(__name__)


class PermissionMiddlewareManager:
    """权限中间件管理器"""
    
    def __init__(self):
        # 中间件实例
        self.permission_middleware: Optional[PermissionMiddleware] = None
        self.batch_delete_middleware: Optional[BatchDeletePermissionMiddleware] = None
        self.data_permission_middleware: Optional[DataPermissionMiddleware] = None
        
        # 统计信息
        self.global_stats = {
            "total_requests": 0,
            "authenticated_requests": 0,
            "permission_denied": 0,
            "batch_operations": 0,
            "data_permission_checks": 0,
            "avg_response_time": 0.0,
            "start_time": datetime.now()
        }
        
        # 性能监控
        self.performance_history = deque(maxlen=1000)  # 保存最近1000次请求的性能数据
        self.error_history = deque(maxlen=500)  # 保存最近500次错误
        
        # 告警配置
        self.alert_thresholds = {
            "high_error_rate": 0.05,  # 5%错误率
            "slow_response_time": 2000,  # 2秒
            "high_permission_denial_rate": 0.1  # 10%权限拒绝率
        }
        
        # 监控状态
        self.monitoring_enabled = True
        self.last_alert_time = {}
        self.alert_cooldown = 300  # 5分钟告警冷却时间
    
    def register_middleware(
        self,
        permission_middleware: PermissionMiddleware,
        batch_delete_middleware: Optional[BatchDeletePermissionMiddleware] = None,
        data_permission_middleware: Optional[DataPermissionMiddleware] = None
    ):
        """注册中间件实例"""
        self.permission_middleware = permission_middleware
        self.batch_delete_middleware = batch_delete_middleware
        self.data_permission_middleware = data_permission_middleware
        
        logger.info("权限中间件已注册")
    
    def collect_stats(self) -> Dict[str, Any]:
        """收集所有中间件的统计信息"""
        stats = {
            "global": self.global_stats.copy(),
            "permission_middleware": None,
            "batch_delete_middleware": None,
            "data_permission_middleware": None,
            "timestamp": datetime.now().isoformat()
        }
        
        # 收集主权限中间件统计
        if self.permission_middleware:
            stats["permission_middleware"] = self.permission_middleware.get_stats()
        
        # 收集批量删除中间件统计（如果有的话）
        if self.batch_delete_middleware and hasattr(self.batch_delete_middleware, 'get_stats'):
            stats["batch_delete_middleware"] = self.batch_delete_middleware.get_stats()
        
        # 收集数据权限中间件统计（如果有的话）
        if self.data_permission_middleware and hasattr(self.data_permission_middleware, 'get_stats'):
            stats["data_permission_middleware"] = self.data_permission_middleware.get_stats()
        
        return stats
    
    def add_performance_record(
        self,
        request_path: str,
        method: str,
        response_time: float,
        status_code: int,
        user_id: Optional[int] = None,
        permission_granted: bool = True
    ):
        """添加性能记录"""
        if not self.monitoring_enabled:
            return
        
        record = {
            "timestamp": datetime.now(),
            "path": request_path,
            "method": method,
            "response_time": response_time,
            "status_code": status_code,
            "user_id": user_id,
            "permission_granted": permission_granted
        }
        
        self.performance_history.append(record)
        
        # 更新全局统计
        self.global_stats["total_requests"] += 1
        
        if user_id:
            self.global_stats["authenticated_requests"] += 1
        
        if not permission_granted:
            self.global_stats["permission_denied"] += 1
        
        # 更新平均响应时间
        total_time = self.global_stats["avg_response_time"] * (self.global_stats["total_requests"] - 1)
        self.global_stats["avg_response_time"] = (total_time + response_time) / self.global_stats["total_requests"]
        
        # 检查告警条件
        self._check_alerts(record)
    
    def add_error_record(
        self,
        request_path: str,
        method: str,
        error_message: str,
        status_code: int,
        user_id: Optional[int] = None
    ):
        """添加错误记录"""
        if not self.monitoring_enabled:
            return
        
        error_record = {
            "timestamp": datetime.now(),
            "path": request_path,
            "method": method,
            "error_message": error_message,
            "status_code": status_code,
            "user_id": user_id
        }
        
        self.error_history.append(error_record)
        
        logger.warning(f"权限中间件错误: {error_message} - {method} {request_path}")
    
    def _check_alerts(self, record: Dict[str, Any]):
        """检查告警条件"""
        current_time = datetime.now()
        
        # 检查慢响应告警
        if record["response_time"] > self.alert_thresholds["slow_response_time"]:
            alert_key = "slow_response"
            if self._should_send_alert(alert_key, current_time):
                self._send_alert(
                    alert_key,
                    f"检测到慢响应: {record['method']} {record['path']} 耗时 {record['response_time']:.2f}ms",
                    "warning"
                )
        
        # 检查错误率告警（基于最近100个请求）
        if len(self.performance_history) >= 100:
            recent_records = list(self.performance_history)[-100:]
            error_count = sum(1 for r in recent_records if r["status_code"] >= 400)
            error_rate = error_count / len(recent_records)
            
            if error_rate > self.alert_thresholds["high_error_rate"]:
                alert_key = "high_error_rate"
                if self._should_send_alert(alert_key, current_time):
                    self._send_alert(
                        alert_key,
                        f"检测到高错误率: {error_rate:.2%} (最近100个请求)",
                        "error"
                    )
        
        # 检查权限拒绝率告警
        if len(self.performance_history) >= 50:
            recent_records = list(self.performance_history)[-50:]
            denied_count = sum(1 for r in recent_records if not r["permission_granted"])
            denial_rate = denied_count / len(recent_records)
            
            if denial_rate > self.alert_thresholds["high_permission_denial_rate"]:
                alert_key = "high_permission_denial_rate"
                if self._should_send_alert(alert_key, current_time):
                    self._send_alert(
                        alert_key,
                        f"检测到高权限拒绝率: {denial_rate:.2%} (最近50个请求)",
                        "warning"
                    )
    
    def _should_send_alert(self, alert_key: str, current_time: datetime) -> bool:
        """检查是否应该发送告警（考虑冷却时间）"""
        last_alert = self.last_alert_time.get(alert_key)
        if not last_alert:
            return True
        
        time_diff = (current_time - last_alert).total_seconds()
        return time_diff >= self.alert_cooldown
    
    def _send_alert(self, alert_key: str, message: str, level: str):
        """发送告警"""
        self.last_alert_time[alert_key] = datetime.now()
        
        # 根据级别选择日志方法
        if level == "error":
            logger.error(f"权限中间件告警: {message}")
        elif level == "warning":
            logger.warning(f"权限中间件告警: {message}")
        else:
            logger.info(f"权限中间件告警: {message}")
        
        # 这里可以集成其他告警系统，如邮件、短信、Slack等
        # await self._send_external_alert(alert_key, message, level)
    
    def get_performance_report(self, hours: int = 1) -> Dict[str, Any]:
        """获取性能报告"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 过滤指定时间范围的记录
        recent_records = [
            record for record in self.performance_history
            if record["timestamp"] >= cutoff_time
        ]
        
        if not recent_records:
            return {
                "message": f"过去{hours}小时内无性能数据",
                "timestamp": datetime.now().isoformat()
            }
        
        # 计算统计指标
        total_requests = len(recent_records)
        response_times = [r["response_time"] for r in recent_records]
        status_codes = [r["status_code"] for r in recent_records]
        
        # 按状态码分组
        status_groups = defaultdict(int)
        for code in status_codes:
            if code < 300:
                status_groups["success"] += 1
            elif code < 400:
                status_groups["redirect"] += 1
            elif code < 500:
                status_groups["client_error"] += 1
            else:
                status_groups["server_error"] += 1
        
        # 按路径分组统计
        path_stats = defaultdict(lambda: {"count": 0, "avg_time": 0, "errors": 0})
        for record in recent_records:
            path = record["path"]
            path_stats[path]["count"] += 1
            path_stats[path]["avg_time"] += record["response_time"]
            if record["status_code"] >= 400:
                path_stats[path]["errors"] += 1
        
        # 计算平均响应时间
        for path_data in path_stats.values():
            if path_data["count"] > 0:
                path_data["avg_time"] /= path_data["count"]
        
        return {
            "time_range_hours": hours,
            "total_requests": total_requests,
            "avg_response_time": sum(response_times) / len(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "status_distribution": dict(status_groups),
            "error_rate": (status_groups["client_error"] + status_groups["server_error"]) / total_requests,
            "top_paths": dict(sorted(
                path_stats.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )[:10]),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_error_report(self, hours: int = 24) -> Dict[str, Any]:
        """获取错误报告"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 过滤指定时间范围的错误记录
        recent_errors = [
            error for error in self.error_history
            if error["timestamp"] >= cutoff_time
        ]
        
        if not recent_errors:
            return {
                "message": f"过去{hours}小时内无错误记录",
                "timestamp": datetime.now().isoformat()
            }
        
        # 按错误类型分组
        error_groups = defaultdict(int)
        for error in recent_errors:
            status_code = error["status_code"]
            if status_code == 401:
                error_groups["authentication"] += 1
            elif status_code == 403:
                error_groups["authorization"] += 1
            elif status_code == 404:
                error_groups["not_found"] += 1
            elif status_code >= 500:
                error_groups["server_error"] += 1
            else:
                error_groups["other"] += 1
        
        # 按路径分组错误
        path_errors = defaultdict(int)
        for error in recent_errors:
            path_errors[error["path"]] += 1
        
        return {
            "time_range_hours": hours,
            "total_errors": len(recent_errors),
            "error_distribution": dict(error_groups),
            "top_error_paths": dict(sorted(
                path_errors.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),
            "recent_errors": [
                {
                    "timestamp": error["timestamp"].isoformat(),
                    "path": error["path"],
                    "method": error["method"],
                    "status_code": error["status_code"],
                    "error_message": error["error_message"]
                }
                for error in recent_errors[-20:]  # 最近20个错误
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        current_time = datetime.now()
        uptime = current_time - self.global_stats["start_time"]
        
        # 计算最近的错误率
        recent_records = [
            record for record in self.performance_history
            if (current_time - record["timestamp"]).total_seconds() <= 300  # 最近5分钟
        ]
        
        error_rate = 0
        if recent_records:
            error_count = sum(1 for r in recent_records if r["status_code"] >= 400)
            error_rate = error_count / len(recent_records)
        
        # 计算平均响应时间
        avg_response_time = 0
        if recent_records:
            avg_response_time = sum(r["response_time"] for r in recent_records) / len(recent_records)
        
        # 确定健康状态
        status = "healthy"
        if error_rate > 0.1:  # 错误率超过10%
            status = "unhealthy"
        elif error_rate > 0.05 or avg_response_time > 1000:  # 错误率超过5%或响应时间超过1秒
            status = "degraded"
        
        return {
            "status": status,
            "uptime_seconds": uptime.total_seconds(),
            "total_requests": self.global_stats["total_requests"],
            "recent_error_rate": error_rate,
            "recent_avg_response_time": avg_response_time,
            "monitoring_enabled": self.monitoring_enabled,
            "middleware_status": {
                "permission_middleware": self.permission_middleware is not None,
                "batch_delete_middleware": self.batch_delete_middleware is not None,
                "data_permission_middleware": self.data_permission_middleware is not None
            },
            "timestamp": current_time.isoformat()
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.global_stats = {
            "total_requests": 0,
            "authenticated_requests": 0,
            "permission_denied": 0,
            "batch_operations": 0,
            "data_permission_checks": 0,
            "avg_response_time": 0.0,
            "start_time": datetime.now()
        }
        
        self.performance_history.clear()
        self.error_history.clear()
        self.last_alert_time.clear()
        
        logger.info("权限中间件统计信息已重置")
    
    def update_alert_thresholds(self, thresholds: Dict[str, float]):
        """更新告警阈值"""
        self.alert_thresholds.update(thresholds)
        logger.info(f"告警阈值已更新: {thresholds}")
    
    def enable_monitoring(self):
        """启用监控"""
        self.monitoring_enabled = True
        logger.info("权限中间件监控已启用")
    
    def disable_monitoring(self):
        """禁用监控"""
        self.monitoring_enabled = False
        logger.info("权限中间件监控已禁用")


# 全局权限中间件管理器实例
permission_middleware_manager = PermissionMiddlewareManager()


# 便捷函数
def get_middleware_stats() -> Dict[str, Any]:
    """获取中间件统计信息"""
    return permission_middleware_manager.collect_stats()


def get_middleware_performance_report(hours: int = 1) -> Dict[str, Any]:
    """获取中间件性能报告"""
    return permission_middleware_manager.get_performance_report(hours)


def get_middleware_error_report(hours: int = 24) -> Dict[str, Any]:
    """获取中间件错误报告"""
    return permission_middleware_manager.get_error_report(hours)


def get_middleware_health() -> Dict[str, Any]:
    """获取中间件健康状态"""
    return permission_middleware_manager.get_health_status()


if __name__ == "__main__":
    # 测试权限中间件管理器
    async def test_manager():
        manager = PermissionMiddlewareManager()
        
        # 模拟一些性能记录
        import random
        import time
        
        for i in range(100):
            manager.add_performance_record(
                request_path=f"/api/v2/test/{i % 10}",
                method="GET",
                response_time=random.uniform(50, 500),
                status_code=random.choice([200, 200, 200, 403, 404, 500]),
                user_id=random.randint(1, 10),
                permission_granted=random.choice([True, True, True, False])
            )
        
        # 获取报告
        stats = manager.collect_stats()
        print(f"统计信息: {stats}")
        
        performance_report = manager.get_performance_report()
        print(f"性能报告: {performance_report}")
        
        health = manager.get_health_status()
        print(f"健康状态: {health}")
    
    asyncio.run(test_manager())