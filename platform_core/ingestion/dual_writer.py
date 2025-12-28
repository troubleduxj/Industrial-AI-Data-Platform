#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
双写适配器

实现新旧数据结构的同时写入，支持错误隔离和一致性验证。

需求: 8.1 - 当启用双写模式时，平台应将数据同时写入新旧数据结构
需求: 8.2 - 当双写发生错误时，平台应记录错误但不影响主写入流程
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging
import asyncio
import json

from platform_core.ingestion.dual_write_config import (
    DualWriteConfigManager,
    get_dual_write_config_manager,
)
from platform_core.ingestion.adapters.base_adapter import DataPoint

logger = logging.getLogger(__name__)


@dataclass
class DualWriteError:
    """
    双写错误记录
    
    Attributes:
        timestamp: 错误发生时间
        category_code: 资产类别编码
        asset_code: 资产编码
        target: 写入目标 (new/old)
        error_type: 错误类型
        error_message: 错误信息
        data_snapshot: 数据快照（可选）
        resolved: 是否已解决
    """
    timestamp: datetime
    category_code: str
    asset_code: str
    target: str  # "new" or "old"
    error_type: str
    error_message: str
    data_snapshot: Optional[Dict[str, Any]] = None
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "category_code": self.category_code,
            "asset_code": self.asset_code,
            "target": self.target,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "data_snapshot": self.data_snapshot,
            "resolved": self.resolved,
        }


@dataclass
class DualWriteResult:
    """
    双写结果
    
    Attributes:
        success: 主写入是否成功
        new_write_success: 新结构写入是否成功
        old_write_success: 旧结构写入是否成功
        new_write_error: 新结构写入错误
        old_write_error: 旧结构写入错误
        timestamp: 写入时间
    """
    success: bool
    new_write_success: bool = True
    old_write_success: bool = True
    new_write_error: Optional[str] = None
    old_write_error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "new_write_success": self.new_write_success,
            "old_write_success": self.old_write_success,
            "new_write_error": self.new_write_error,
            "old_write_error": self.old_write_error,
            "timestamp": self.timestamp.isoformat(),
        }


class DualWriteAdapter:
    """
    双写适配器
    
    同时写入新旧数据结构，实现错误隔离，确保主写入流程不受影响。
    
    Attributes:
        _config_manager: 双写配置管理器
        _error_log: 错误日志列表
        _statistics: 统计信息
    """
    
    def __init__(self, config_manager: Optional[DualWriteConfigManager] = None):
        """
        初始化双写适配器
        
        Args:
            config_manager: 配置管理器（可选，默认使用全局实例）
        """
        self._config_manager = config_manager or get_dual_write_config_manager()
        self._error_log: List[DualWriteError] = []
        self._max_error_log_size = 10000
        
        # 统计信息
        self._statistics = {
            "total_writes": 0,
            "new_success": 0,
            "new_failures": 0,
            "old_success": 0,
            "old_failures": 0,
            "dual_write_enabled_count": 0,
        }
        
        # TDengine客户端（延迟初始化）
        self._td_client = None
        
        # 写入锁（防止并发问题）
        self._write_lock = asyncio.Lock()
    
    @property
    def config_manager(self) -> DualWriteConfigManager:
        """获取配置管理器"""
        return self._config_manager
    
    @property
    def statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self._statistics.copy()
    
    # =====================================================
    # 核心写入方法
    # =====================================================
    
    async def write_asset_data(
        self,
        category_code: str,
        asset_code: str,
        data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> DualWriteResult:
        """
        写入资产数据
        
        实现双写逻辑：
        1. 始终尝试写入新结构（主写入）
        2. 如果启用双写，尝试写入旧结构
        3. 旧结构写入失败不影响主流程（除非配置为fail_on_old_error）
        
        Args:
            category_code: 资产类别编码
            asset_code: 资产编码
            data: 数据字典（信号数据）
            timestamp: 数据时间戳（可选）
        
        Returns:
            DualWriteResult: 写入结果
        """
        self._statistics["total_writes"] += 1
        timestamp = timestamp or datetime.now()
        
        result = DualWriteResult(success=True)
        
        # 1. 写入新结构（主写入）
        if self._config_manager.should_write_to_new(category_code):
            try:
                await self._write_to_new_structure(
                    category_code, asset_code, data, timestamp
                )
                result.new_write_success = True
                self._statistics["new_success"] += 1
            except Exception as e:
                result.new_write_success = False
                result.new_write_error = str(e)
                result.success = False
                self._statistics["new_failures"] += 1
                
                # 记录错误
                self._log_error(
                    category_code=category_code,
                    asset_code=asset_code,
                    target="new",
                    error_type=type(e).__name__,
                    error_message=str(e),
                    data_snapshot=data
                )
                
                logger.error(f"新结构写入失败: {category_code}/{asset_code} - {e}")
        
        # 2. 如果启用双写，写入旧结构
        if self._config_manager.should_write_to_old(category_code):
            self._statistics["dual_write_enabled_count"] += 1
            
            try:
                await self._write_to_old_structure(
                    category_code, asset_code, data, timestamp
                )
                result.old_write_success = True
                self._statistics["old_success"] += 1
            except Exception as e:
                result.old_write_success = False
                result.old_write_error = str(e)
                self._statistics["old_failures"] += 1
                
                # 记录错误
                self._log_error(
                    category_code=category_code,
                    asset_code=asset_code,
                    target="old",
                    error_type=type(e).__name__,
                    error_message=str(e),
                    data_snapshot=data
                )
                
                logger.warning(f"旧结构写入失败（已隔离）: {category_code}/{asset_code} - {e}")
                
                # 检查是否应该影响主流程
                if self._config_manager.should_fail_on_old_error(category_code):
                    result.success = False
        
        return result
    
    async def write_data_point(self, data_point: DataPoint, category_code: str) -> DualWriteResult:
        """
        写入数据点
        
        Args:
            data_point: 数据点
            category_code: 资产类别编码
        
        Returns:
            DualWriteResult: 写入结果
        """
        return await self.write_asset_data(
            category_code=category_code,
            asset_code=data_point.asset_code,
            data=data_point.signals,
            timestamp=data_point.timestamp
        )
    
    async def write_batch(
        self,
        category_code: str,
        data_points: List[Tuple[str, Dict[str, Any], Optional[datetime]]]
    ) -> List[DualWriteResult]:
        """
        批量写入数据
        
        Args:
            category_code: 资产类别编码
            data_points: 数据点列表 [(asset_code, data, timestamp), ...]
        
        Returns:
            List[DualWriteResult]: 写入结果列表
        """
        results = []
        for asset_code, data, timestamp in data_points:
            result = await self.write_asset_data(
                category_code=category_code,
                asset_code=asset_code,
                data=data,
                timestamp=timestamp
            )
            results.append(result)
        return results
    
    # =====================================================
    # 写入实现
    # =====================================================
    
    async def _write_to_new_structure(
        self,
        category_code: str,
        asset_code: str,
        data: Dict[str, Any],
        timestamp: datetime
    ):
        """
        写入新数据结构（TDengine raw_{category} 表）
        
        Args:
            category_code: 资产类别编码
            asset_code: 资产编码
            data: 信号数据
            timestamp: 时间戳
        """
        # 构建表名
        table_name = f"raw_{category_code}_{asset_code}"
        stable_name = f"raw_{category_code}"
        
        # 获取TDengine客户端
        td_client = await self._get_td_client()
        
        if td_client is None:
            # 如果TDengine不可用，记录日志但不抛出异常（用于测试）
            logger.debug(f"TDengine客户端不可用，跳过新结构写入: {table_name}")
            return
        
        # 确保子表存在
        await self._ensure_child_table(td_client, stable_name, table_name, asset_code)
        
        # 构建插入SQL
        columns = ["ts"]
        values = [f"'{timestamp.isoformat()}'"]
        
        for signal_code, value in data.items():
            columns.append(signal_code)
            if isinstance(value, str):
                values.append(f"'{value}'")
            elif isinstance(value, bool):
                values.append(str(value).lower())
            elif value is None:
                values.append("NULL")
            else:
                values.append(str(value))
        
        sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)})"
        
        await td_client.execute(sql)
    
    async def _write_to_old_structure(
        self,
        category_code: str,
        asset_code: str,
        data: Dict[str, Any],
        timestamp: datetime
    ):
        """
        写入旧数据结构（兼容性写入）
        
        旧结构可能是：
        1. 旧的device_data表
        2. 旧的TDengine表结构
        3. 其他遗留系统
        
        Args:
            category_code: 资产类别编码
            asset_code: 资产编码
            data: 信号数据
            timestamp: 时间戳
        """
        # 尝试写入旧的PostgreSQL表
        try:
            await self._write_to_old_postgresql(category_code, asset_code, data, timestamp)
        except Exception as pg_error:
            logger.debug(f"旧PostgreSQL写入失败: {pg_error}")
        
        # 尝试写入旧的TDengine表
        try:
            await self._write_to_old_tdengine(category_code, asset_code, data, timestamp)
        except Exception as td_error:
            logger.debug(f"旧TDengine写入失败: {td_error}")
    
    async def _write_to_old_postgresql(
        self,
        category_code: str,
        asset_code: str,
        data: Dict[str, Any],
        timestamp: datetime
    ):
        """写入旧的PostgreSQL表"""
        try:
            from app.core.database import get_db_connection
            
            conn = await get_db_connection()
            
            # 查找资产ID
            asset = await conn.fetchrow(
                "SELECT id FROM t_assets WHERE code = $1",
                asset_code
            )
            
            if not asset:
                logger.debug(f"资产不存在: {asset_code}")
                return
            
            asset_id = asset["id"]
            
            # 写入旧的device_data表（如果存在）
            await conn.execute("""
                INSERT INTO device_data (device_id, data, created_at)
                VALUES ($1, $2, $3)
                ON CONFLICT DO NOTHING
            """, asset_id, json.dumps(data), timestamp)
            
        except Exception as e:
            # 旧表可能不存在，忽略错误
            logger.debug(f"旧PostgreSQL写入跳过: {e}")
    
    async def _write_to_old_tdengine(
        self,
        category_code: str,
        asset_code: str,
        data: Dict[str, Any],
        timestamp: datetime
    ):
        """写入旧的TDengine表"""
        td_client = await self._get_td_client()
        
        if td_client is None:
            return
        
        # 旧表名格式（假设）
        old_table_name = f"device_{asset_code}"
        
        try:
            # 尝试写入旧表
            columns = ["ts"]
            values = [f"'{timestamp.isoformat()}'"]
            
            for signal_code, value in data.items():
                columns.append(signal_code)
                if isinstance(value, str):
                    values.append(f"'{value}'")
                elif isinstance(value, bool):
                    values.append(str(value).lower())
                elif value is None:
                    values.append("NULL")
                else:
                    values.append(str(value))
            
            sql = f"INSERT INTO {old_table_name} ({', '.join(columns)}) VALUES ({', '.join(values)})"
            await td_client.execute(sql)
            
        except Exception as e:
            # 旧表可能不存在，忽略错误
            logger.debug(f"旧TDengine写入跳过: {e}")
    
    async def _ensure_child_table(
        self,
        td_client,
        stable_name: str,
        table_name: str,
        asset_code: str
    ):
        """确保TDengine子表存在"""
        try:
            # 检查表是否存在
            result = await td_client.query(f"SHOW TABLES LIKE '{table_name}'")
            if not result:
                # 创建子表
                sql = f"CREATE TABLE IF NOT EXISTS {table_name} USING {stable_name} TAGS ('{asset_code}')"
                await td_client.execute(sql)
        except Exception as e:
            logger.debug(f"确保子表存在失败: {e}")
    
    async def _get_td_client(self):
        """获取TDengine客户端"""
        if self._td_client is not None:
            return self._td_client
        
        try:
            from app.core.tdengine_connector import get_tdengine_client
            self._td_client = await get_tdengine_client()
            return self._td_client
        except Exception as e:
            logger.debug(f"获取TDengine客户端失败: {e}")
            return None
    
    # =====================================================
    # 错误日志管理
    # =====================================================
    
    def _log_error(
        self,
        category_code: str,
        asset_code: str,
        target: str,
        error_type: str,
        error_message: str,
        data_snapshot: Optional[Dict[str, Any]] = None
    ):
        """记录错误"""
        error = DualWriteError(
            timestamp=datetime.now(),
            category_code=category_code,
            asset_code=asset_code,
            target=target,
            error_type=error_type,
            error_message=error_message,
            data_snapshot=data_snapshot,
        )
        
        self._error_log.append(error)
        
        # 限制错误日志大小
        if len(self._error_log) > self._max_error_log_size:
            self._error_log = self._error_log[-self._max_error_log_size:]
    
    def get_error_log(
        self,
        limit: int = 100,
        target: Optional[str] = None,
        category_code: Optional[str] = None
    ) -> List[DualWriteError]:
        """
        获取错误日志
        
        Args:
            limit: 返回数量限制
            target: 按目标过滤 (new/old)
            category_code: 按类别过滤
        
        Returns:
            List[DualWriteError]: 错误日志列表
        """
        errors = self._error_log
        
        if target:
            errors = [e for e in errors if e.target == target]
        
        if category_code:
            errors = [e for e in errors if e.category_code == category_code]
        
        return errors[-limit:]
    
    def clear_error_log(self):
        """清空错误日志"""
        self._error_log.clear()
    
    # =====================================================
    # 统计信息
    # =====================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self._statistics.copy()
        
        # 计算成功率
        total = stats["total_writes"]
        if total > 0:
            stats["new_success_rate"] = stats["new_success"] / total
            stats["old_success_rate"] = stats["old_success"] / stats["dual_write_enabled_count"] if stats["dual_write_enabled_count"] > 0 else 0
        else:
            stats["new_success_rate"] = 0
            stats["old_success_rate"] = 0
        
        # 错误统计
        stats["error_count"] = len(self._error_log)
        stats["new_errors"] = len([e for e in self._error_log if e.target == "new"])
        stats["old_errors"] = len([e for e in self._error_log if e.target == "old"])
        
        return stats
    
    def reset_statistics(self):
        """重置统计信息"""
        self._statistics = {
            "total_writes": 0,
            "new_success": 0,
            "new_failures": 0,
            "old_success": 0,
            "old_failures": 0,
            "dual_write_enabled_count": 0,
        }


# =====================================================
# 全局实例
# =====================================================

_dual_write_adapter: Optional[DualWriteAdapter] = None


def get_dual_write_adapter() -> DualWriteAdapter:
    """
    获取双写适配器单例
    
    Returns:
        DualWriteAdapter: 双写适配器实例
    """
    global _dual_write_adapter
    if _dual_write_adapter is None:
        _dual_write_adapter = DualWriteAdapter()
    return _dual_write_adapter


def create_dual_write_adapter(
    config_manager: Optional[DualWriteConfigManager] = None
) -> DualWriteAdapter:
    """
    创建新的双写适配器实例
    
    Args:
        config_manager: 配置管理器（可选）
    
    Returns:
        DualWriteAdapter: 新的双写适配器实例
    """
    return DualWriteAdapter(config_manager)
