#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
双写配置管理

管理新旧数据结构的双写模式配置，支持全局和按类别粒度的配置。

需求: 8.5 - 双写模式应支持按资产类别粒度启用或禁用
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Set, Optional, Any, List
import logging
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class CategoryDualWriteConfig:
    """
    类别双写配置
    
    Attributes:
        category_id: 资产类别ID
        category_code: 资产类别编码
        enabled: 是否启用双写
        write_to_new: 是否写入新结构
        write_to_old: 是否写入旧结构
        fail_on_old_error: 旧结构写入失败是否影响主流程
        verify_enabled: 是否启用一致性验证
        verify_interval_hours: 验证间隔（小时）
        last_verify_time: 最后验证时间
        last_verify_result: 最后验证结果
    """
    category_id: Optional[int] = None
    category_code: str = ""
    enabled: bool = False
    write_to_new: bool = True
    write_to_old: bool = True
    fail_on_old_error: bool = False
    verify_enabled: bool = False
    verify_interval_hours: int = 24
    last_verify_time: Optional[datetime] = None
    last_verify_result: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "category_id": self.category_id,
            "category_code": self.category_code,
            "enabled": self.enabled,
            "write_to_new": self.write_to_new,
            "write_to_old": self.write_to_old,
            "fail_on_old_error": self.fail_on_old_error,
            "verify_enabled": self.verify_enabled,
            "verify_interval_hours": self.verify_interval_hours,
            "last_verify_time": self.last_verify_time.isoformat() if self.last_verify_time else None,
            "last_verify_result": self.last_verify_result,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CategoryDualWriteConfig":
        """从字典创建"""
        last_verify_time = data.get("last_verify_time")
        if isinstance(last_verify_time, str):
            last_verify_time = datetime.fromisoformat(last_verify_time)
        
        return cls(
            category_id=data.get("category_id"),
            category_code=data.get("category_code", ""),
            enabled=data.get("enabled", False),
            write_to_new=data.get("write_to_new", True),
            write_to_old=data.get("write_to_old", True),
            fail_on_old_error=data.get("fail_on_old_error", False),
            verify_enabled=data.get("verify_enabled", False),
            verify_interval_hours=data.get("verify_interval_hours", 24),
            last_verify_time=last_verify_time,
            last_verify_result=data.get("last_verify_result"),
        )


class DualWriteConfigManager:
    """
    双写配置管理器
    
    管理全局和按类别的双写配置，支持从数据库加载和持久化配置。
    
    Attributes:
        _global_enabled: 全局双写开关
        _category_configs: 按类别的配置字典
        _enabled_categories: 启用双写的类别编码集合
    """
    
    def __init__(self):
        """初始化配置管理器"""
        self._global_enabled: bool = False
        self._global_write_to_new: bool = True
        self._global_write_to_old: bool = True
        self._global_fail_on_old_error: bool = False
        
        # 按类别配置
        self._category_configs: Dict[str, CategoryDualWriteConfig] = {}
        self._enabled_categories: Set[str] = set()
        
        # 配置加载状态
        self._loaded: bool = False
        self._load_lock = asyncio.Lock()
    
    # =====================================================
    # 全局配置管理
    # =====================================================
    
    @property
    def global_enabled(self) -> bool:
        """获取全局启用状态"""
        return self._global_enabled
    
    def enable_global(self):
        """全局启用双写"""
        self._global_enabled = True
        logger.info("双写模式已全局启用")
    
    def disable_global(self):
        """全局禁用双写"""
        self._global_enabled = False
        logger.info("双写模式已全局禁用")
    
    def set_global_config(
        self,
        enabled: Optional[bool] = None,
        write_to_new: Optional[bool] = None,
        write_to_old: Optional[bool] = None,
        fail_on_old_error: Optional[bool] = None
    ):
        """
        设置全局配置
        
        Args:
            enabled: 是否启用
            write_to_new: 是否写入新结构
            write_to_old: 是否写入旧结构
            fail_on_old_error: 旧结构写入失败是否影响主流程
        """
        if enabled is not None:
            self._global_enabled = enabled
        if write_to_new is not None:
            self._global_write_to_new = write_to_new
        if write_to_old is not None:
            self._global_write_to_old = write_to_old
        if fail_on_old_error is not None:
            self._global_fail_on_old_error = fail_on_old_error
        
        logger.info(f"全局双写配置已更新: enabled={self._global_enabled}")
    
    def get_global_config(self) -> Dict[str, Any]:
        """获取全局配置"""
        return {
            "enabled": self._global_enabled,
            "write_to_new": self._global_write_to_new,
            "write_to_old": self._global_write_to_old,
            "fail_on_old_error": self._global_fail_on_old_error,
        }
    
    # =====================================================
    # 类别配置管理
    # =====================================================
    
    def enable_category(self, category_code: str, category_id: Optional[int] = None):
        """
        启用特定类别的双写
        
        Args:
            category_code: 资产类别编码
            category_id: 资产类别ID（可选）
        """
        if category_code not in self._category_configs:
            self._category_configs[category_code] = CategoryDualWriteConfig(
                category_id=category_id,
                category_code=category_code,
                enabled=True,
            )
        else:
            self._category_configs[category_code].enabled = True
            if category_id:
                self._category_configs[category_code].category_id = category_id
        
        self._enabled_categories.add(category_code)
        logger.info(f"类别 {category_code} 双写已启用")
    
    def disable_category(self, category_code: str):
        """
        禁用特定类别的双写
        
        Args:
            category_code: 资产类别编码
        """
        if category_code in self._category_configs:
            self._category_configs[category_code].enabled = False
        
        self._enabled_categories.discard(category_code)
        logger.info(f"类别 {category_code} 双写已禁用")
    
    def set_category_config(
        self,
        category_code: str,
        config: CategoryDualWriteConfig
    ):
        """
        设置类别配置
        
        Args:
            category_code: 资产类别编码
            config: 类别配置
        """
        self._category_configs[category_code] = config
        if config.enabled:
            self._enabled_categories.add(category_code)
        else:
            self._enabled_categories.discard(category_code)
        
        logger.info(f"类别 {category_code} 双写配置已更新")
    
    def get_category_config(self, category_code: str) -> Optional[CategoryDualWriteConfig]:
        """
        获取类别配置
        
        Args:
            category_code: 资产类别编码
        
        Returns:
            CategoryDualWriteConfig: 类别配置，不存在返回None
        """
        return self._category_configs.get(category_code)
    
    def get_all_category_configs(self) -> Dict[str, CategoryDualWriteConfig]:
        """获取所有类别配置"""
        return self._category_configs.copy()
    
    def get_enabled_categories(self) -> Set[str]:
        """获取所有启用双写的类别"""
        return self._enabled_categories.copy()
    
    # =====================================================
    # 双写状态检查
    # =====================================================
    
    def is_enabled(self, category_code: str) -> bool:
        """
        检查是否启用双写
        
        全局启用或类别启用都会返回True
        
        Args:
            category_code: 资产类别编码
        
        Returns:
            bool: 是否启用双写
        """
        # 全局启用
        if self._global_enabled:
            return True
        
        # 类别启用
        return category_code in self._enabled_categories
    
    def should_write_to_new(self, category_code: str) -> bool:
        """
        检查是否应写入新结构
        
        Args:
            category_code: 资产类别编码
        
        Returns:
            bool: 是否写入新结构
        """
        # 检查类别配置
        config = self._category_configs.get(category_code)
        if config and config.enabled:
            return config.write_to_new
        
        # 使用全局配置
        return self._global_write_to_new
    
    def should_write_to_old(self, category_code: str) -> bool:
        """
        检查是否应写入旧结构
        
        Args:
            category_code: 资产类别编码
        
        Returns:
            bool: 是否写入旧结构
        """
        if not self.is_enabled(category_code):
            return False
        
        # 检查类别配置
        config = self._category_configs.get(category_code)
        if config and config.enabled:
            return config.write_to_old
        
        # 使用全局配置
        return self._global_write_to_old
    
    def should_fail_on_old_error(self, category_code: str) -> bool:
        """
        检查旧结构写入失败是否应影响主流程
        
        Args:
            category_code: 资产类别编码
        
        Returns:
            bool: 是否影响主流程
        """
        # 检查类别配置
        config = self._category_configs.get(category_code)
        if config and config.enabled:
            return config.fail_on_old_error
        
        # 使用全局配置
        return self._global_fail_on_old_error
    
    # =====================================================
    # 配置持久化
    # =====================================================
    
    async def load_from_database(self):
        """从数据库加载配置"""
        async with self._load_lock:
            if self._loaded:
                return
            
            try:
                # 尝试从数据库加载配置
                # 这里使用原始SQL查询，因为可能没有ORM模型
                from app.core.database import get_db_connection
                
                try:
                    conn = await get_db_connection()
                    
                    # 加载全局配置（category_id为NULL的记录）
                    global_config = await conn.fetchrow(
                        "SELECT * FROM t_dual_write_config WHERE category_id IS NULL"
                    )
                    
                    if global_config:
                        self._global_enabled = global_config.get("enabled", False)
                        self._global_write_to_new = global_config.get("write_to_new", True)
                        self._global_write_to_old = global_config.get("write_to_old", True)
                        self._global_fail_on_old_error = global_config.get("fail_on_old_error", False)
                    
                    # 加载类别配置
                    category_configs = await conn.fetch("""
                        SELECT dwc.*, ac.code as category_code
                        FROM t_dual_write_config dwc
                        LEFT JOIN t_asset_category ac ON dwc.category_id = ac.id
                        WHERE dwc.category_id IS NOT NULL
                    """)
                    
                    for row in category_configs:
                        category_code = row.get("category_code")
                        if category_code:
                            config = CategoryDualWriteConfig(
                                category_id=row.get("category_id"),
                                category_code=category_code,
                                enabled=row.get("enabled", False),
                                write_to_new=row.get("write_to_new", True),
                                write_to_old=row.get("write_to_old", True),
                                fail_on_old_error=row.get("fail_on_old_error", False),
                                verify_enabled=row.get("verify_enabled", False),
                                verify_interval_hours=row.get("verify_interval_hours", 24),
                                last_verify_time=row.get("last_verify_time"),
                                last_verify_result=row.get("last_verify_result"),
                            )
                            self._category_configs[category_code] = config
                            if config.enabled:
                                self._enabled_categories.add(category_code)
                    
                    self._loaded = True
                    logger.info(f"双写配置已从数据库加载: 全局={self._global_enabled}, 类别数={len(self._category_configs)}")
                    
                except Exception as db_error:
                    logger.warning(f"从数据库加载双写配置失败，使用默认配置: {db_error}")
                    self._loaded = True
                    
            except ImportError:
                logger.warning("数据库模块不可用，使用默认配置")
                self._loaded = True
    
    async def save_to_database(self):
        """保存配置到数据库"""
        try:
            from app.core.database import get_db_connection
            
            conn = await get_db_connection()
            
            # 保存全局配置
            await conn.execute("""
                INSERT INTO t_dual_write_config (category_id, enabled, write_to_new, write_to_old, fail_on_old_error)
                VALUES (NULL, $1, $2, $3, $4)
                ON CONFLICT (category_id) WHERE category_id IS NULL
                DO UPDATE SET enabled = $1, write_to_new = $2, write_to_old = $3, fail_on_old_error = $4, updated_at = NOW()
            """, self._global_enabled, self._global_write_to_new, self._global_write_to_old, self._global_fail_on_old_error)
            
            # 保存类别配置
            for category_code, config in self._category_configs.items():
                if config.category_id:
                    await conn.execute("""
                        INSERT INTO t_dual_write_config (category_id, enabled, write_to_new, write_to_old, fail_on_old_error, verify_enabled, verify_interval_hours)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (category_id)
                        DO UPDATE SET enabled = $2, write_to_new = $3, write_to_old = $4, fail_on_old_error = $5, verify_enabled = $6, verify_interval_hours = $7, updated_at = NOW()
                    """, config.category_id, config.enabled, config.write_to_new, config.write_to_old, 
                        config.fail_on_old_error, config.verify_enabled, config.verify_interval_hours)
            
            logger.info("双写配置已保存到数据库")
            
        except Exception as e:
            logger.error(f"保存双写配置到数据库失败: {e}")
            raise
    
    # =====================================================
    # 配置导出/导入
    # =====================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """导出配置为字典"""
        return {
            "global": self.get_global_config(),
            "categories": {
                code: config.to_dict()
                for code, config in self._category_configs.items()
            },
            "enabled_categories": list(self._enabled_categories),
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """从字典导入配置"""
        # 导入全局配置
        global_config = data.get("global", {})
        self._global_enabled = global_config.get("enabled", False)
        self._global_write_to_new = global_config.get("write_to_new", True)
        self._global_write_to_old = global_config.get("write_to_old", True)
        self._global_fail_on_old_error = global_config.get("fail_on_old_error", False)
        
        # 导入类别配置
        categories = data.get("categories", {})
        for code, config_data in categories.items():
            config = CategoryDualWriteConfig.from_dict(config_data)
            self._category_configs[code] = config
            if config.enabled:
                self._enabled_categories.add(code)
            else:
                self._enabled_categories.discard(code)
    
    def reset(self):
        """重置所有配置"""
        self._global_enabled = False
        self._global_write_to_new = True
        self._global_write_to_old = True
        self._global_fail_on_old_error = False
        self._category_configs.clear()
        self._enabled_categories.clear()
        self._loaded = False
        logger.info("双写配置已重置")


# =====================================================
# 全局实例
# =====================================================

_dual_write_config_manager: Optional[DualWriteConfigManager] = None


def get_dual_write_config_manager() -> DualWriteConfigManager:
    """
    获取双写配置管理器单例
    
    Returns:
        DualWriteConfigManager: 配置管理器实例
    """
    global _dual_write_config_manager
    if _dual_write_config_manager is None:
        _dual_write_config_manager = DualWriteConfigManager()
    return _dual_write_config_manager


async def init_dual_write_config():
    """初始化双写配置（从数据库加载）"""
    manager = get_dual_write_config_manager()
    await manager.load_from_database()
    return manager
