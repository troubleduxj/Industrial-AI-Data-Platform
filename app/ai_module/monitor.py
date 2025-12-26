#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI模块资源监控"""

import psutil
from typing import Dict, Any
from loguru import logger

from app.settings.ai_settings import ai_settings


class AIResourceMonitor:
    """AI资源监控器"""
    
    @staticmethod
    def check_memory_usage() -> float:
        """
        检查当前进程内存使用(MB)
        
        Returns:
            float: 内存使用量(MB)
        """
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024  # 转换为MB
            
            # 检查是否超限
            if memory_mb > ai_settings.ai_max_memory_mb:
                logger.warning(
                    f"⚠️ AI模块内存使用超限: "
                    f"{memory_mb:.2f}MB > {ai_settings.ai_max_memory_mb}MB"
                )
            
            return memory_mb
        except Exception as e:
            logger.error(f"检查内存使用失败: {e}")
            return 0.0
    
    @staticmethod
    def check_cpu_usage() -> float:
        """
        检查CPU使用率(%)
        
        Returns:
            float: CPU使用率(%)
        """
        try:
            # interval=1表示测量1秒内的CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 检查是否超限
            if cpu_percent > ai_settings.ai_max_cpu_percent:
                logger.warning(
                    f"⚠️ AI模块CPU使用超限: "
                    f"{cpu_percent:.2f}% > {ai_settings.ai_max_cpu_percent}%"
                )
            
            return cpu_percent
        except Exception as e:
            logger.error(f"检查CPU使用失败: {e}")
            return 0.0
    
    @staticmethod
    def get_system_memory_info() -> Dict[str, Any]:
        """
        获取系统内存信息
        
        Returns:
            dict: 包含总内存、可用内存、使用率等信息
        """
        try:
            mem = psutil.virtual_memory()
            return {
                "total_mb": mem.total / 1024 / 1024,
                "available_mb": mem.available / 1024 / 1024,
                "used_mb": mem.used / 1024 / 1024,
                "percent": mem.percent
            }
        except Exception as e:
            logger.error(f"获取系统内存信息失败: {e}")
            return {}
    
    @staticmethod
    def get_resource_stats() -> Dict[str, Any]:
        """
        获取完整的资源统计信息
        
        Returns:
            dict: 包含内存、CPU、限制等信息
        """
        try:
            # 进程级别的资源使用
            process_memory_mb = AIResourceMonitor.check_memory_usage()
            process_cpu_percent = AIResourceMonitor.check_cpu_usage()
            
            # 系统级别的内存信息
            system_memory = AIResourceMonitor.get_system_memory_info()
            
            # 配置的资源限制
            limits = {
                "max_memory_mb": ai_settings.ai_max_memory_mb,
                "max_cpu_percent": ai_settings.ai_max_cpu_percent,
                "worker_threads": ai_settings.ai_worker_threads
            }
            
            # 资源使用情况
            usage = {
                "memory_mb": process_memory_mb,
                "cpu_percent": process_cpu_percent,
                "memory_usage_ratio": process_memory_mb / ai_settings.ai_max_memory_mb,
                "cpu_usage_ratio": process_cpu_percent / ai_settings.ai_max_cpu_percent
            }
            
            # 健康状态评估
            is_healthy = (
                usage["memory_usage_ratio"] < 0.9 and
                usage["cpu_usage_ratio"] < 0.9
            )
            
            status = "healthy" if is_healthy else "warning"
            if usage["memory_usage_ratio"] >= 1.0 or usage["cpu_usage_ratio"] >= 1.0:
                status = "critical"
            
            return {
                "status": status,
                "usage": usage,
                "limits": limits,
                "system_memory": system_memory,
                "timestamp": None  # 由调用方添加
            }
        
        except Exception as e:
            logger.error(f"获取资源统计失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "usage": {},
                "limits": {},
                "system_memory": {}
            }
    
    @staticmethod
    def is_resource_available() -> bool:
        """
        检查资源是否可用
        
        Returns:
            bool: 资源是否充足
        """
        try:
            stats = AIResourceMonitor.get_resource_stats()
            return stats.get("status") in ["healthy", "warning"]
        except Exception:
            return False
    
    @staticmethod
    def log_resource_usage():
        """记录当前资源使用情况（用于调试）"""
        try:
            stats = AIResourceMonitor.get_resource_stats()
            logger.info(
                f"AI模块资源使用: "
                f"内存 {stats['usage']['memory_mb']:.2f}MB/"
                f"{stats['limits']['max_memory_mb']}MB "
                f"({stats['usage']['memory_usage_ratio']*100:.1f}%), "
                f"CPU {stats['usage']['cpu_percent']:.2f}%/"
                f"{stats['limits']['max_cpu_percent']}% "
                f"({stats['usage']['cpu_usage_ratio']*100:.1f}%)"
            )
        except Exception as e:
            logger.error(f"记录资源使用失败: {e}")


# 全局监控器实例
ai_resource_monitor = AIResourceMonitor()

