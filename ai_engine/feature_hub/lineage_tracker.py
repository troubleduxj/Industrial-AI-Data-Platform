#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
特征血缘追踪器 (Lineage Tracker)

实现需求6.5: 平台应提供特征血缘追踪，记录特征的来源信号和计算逻辑

核心功能:
- record_lineage(): 记录特征血缘信息
- get_lineage(): 获取特征血缘信息
- get_downstream_features(): 获取依赖某信号的所有特征
- get_upstream_signals(): 获取特征依赖的所有源信号
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from loguru import logger


# =====================================================
# 数据类定义
# =====================================================

@dataclass
class FeatureLineage:
    """
    特征血缘信息
    
    记录特征的来源信号、计算逻辑和依赖关系
    """
    feature_name: str
    source_signals: List[str]
    calculation_logic: str
    created_at: datetime
    updated_at: datetime
    category_code: str = ""
    view_name: str = ""
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result["created_at"] = self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        result["updated_at"] = self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureLineage":
        """从字典创建"""
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")
        
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
            
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        elif updated_at is None:
            updated_at = datetime.now()
        
        return cls(
            feature_name=data.get("feature_name", ""),
            source_signals=data.get("source_signals", []),
            calculation_logic=data.get("calculation_logic", ""),
            created_at=created_at,
            updated_at=updated_at,
            category_code=data.get("category_code", ""),
            view_name=data.get("view_name", ""),
            dependencies=data.get("dependencies", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class LineageGraph:
    """
    血缘关系图
    
    表示信号到特征的依赖关系
    """
    # 信号 -> 依赖该信号的特征列表
    signal_to_features: Dict[str, List[str]] = field(default_factory=dict)
    # 特征 -> 该特征依赖的信号列表
    feature_to_signals: Dict[str, List[str]] = field(default_factory=dict)
    # 特征 -> 血缘信息
    feature_lineages: Dict[str, FeatureLineage] = field(default_factory=dict)
    
    def add_lineage(self, lineage: FeatureLineage):
        """添加血缘信息"""
        feature_key = f"{lineage.category_code}:{lineage.view_name}:{lineage.feature_name}"
        
        # 存储血缘信息
        self.feature_lineages[feature_key] = lineage
        
        # 更新特征到信号的映射
        self.feature_to_signals[feature_key] = lineage.source_signals.copy()
        
        # 更新信号到特征的映射
        for signal in lineage.source_signals:
            if signal not in self.signal_to_features:
                self.signal_to_features[signal] = []
            if feature_key not in self.signal_to_features[signal]:
                self.signal_to_features[signal].append(feature_key)
    
    def get_downstream_features(self, signal_code: str) -> List[str]:
        """获取依赖某信号的所有特征"""
        return self.signal_to_features.get(signal_code, [])
    
    def get_upstream_signals(self, feature_key: str) -> List[str]:
        """获取特征依赖的所有源信号"""
        return self.feature_to_signals.get(feature_key, [])


# =====================================================
# 血缘追踪器
# =====================================================

class LineageTracker:
    """
    特征血缘追踪器
    
    负责记录和查询特征的血缘信息，包括来源信号和计算逻辑。
    
    核心功能:
    - record_lineage(): 记录特征血缘
    - get_lineage(): 获取特征血缘
    - get_downstream_features(): 获取依赖某信号的所有特征
    - get_upstream_signals(): 获取特征依赖的所有源信号
    """
    
    def __init__(self):
        """初始化血缘追踪器"""
        self._lineage_graph = LineageGraph()
        self._initialized = False
    
    async def record_lineage(
        self,
        category_code: str,
        view_name: str,
        feature_config: Dict[str, Any]
    ) -> bool:
        """
        记录特征血缘
        
        实现需求6.5: 记录特征的来源信号和计算逻辑
        
        Args:
            category_code: 资产类别编码
            view_name: 特征视图名称
            feature_config: 特征配置，包含:
                - name: 特征名称
                - source_signal: 源信号
                - function: 聚合函数
                - window: 时间窗口 (可选)
                - filters: 过滤条件 (可选)
        
        Returns:
            bool: 记录是否成功
            
        Example:
            >>> tracker = LineageTracker()
            >>> config = {
            ...     "name": "avg_current",
            ...     "source_signal": "current",
            ...     "function": "avg",
            ...     "window": "1h"
            ... }
            >>> await tracker.record_lineage("motor", "realtime", config)
            True
        """
        try:
            feature_name = feature_config.get("name", "")
            source_signal = feature_config.get("source_signal", "")
            function = feature_config.get("function", "")
            window = feature_config.get("window", "")
            filters = feature_config.get("filters", {})
            
            if not feature_name or not source_signal:
                logger.error("特征名称和源信号不能为空")
                return False
            
            # 构建计算逻辑描述
            calculation_logic = self._build_calculation_logic(
                function, source_signal, window, filters
            )
            
            # 创建血缘信息
            now = datetime.now()
            lineage = FeatureLineage(
                feature_name=feature_name,
                source_signals=[source_signal],
                calculation_logic=calculation_logic,
                created_at=now,
                updated_at=now,
                category_code=category_code,
                view_name=view_name,
                metadata={
                    "function": function,
                    "window": window,
                    "filters": filters,
                    "original_config": feature_config
                }
            )
            
            # 添加到内存图
            self._lineage_graph.add_lineage(lineage)
            
            # 保存到数据库
            await self._save_lineage_to_db(category_code, view_name, lineage)
            
            logger.info(f"✅ 特征血缘记录成功: {category_code}/{view_name}/{feature_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 记录特征血缘失败: {e}")
            return False
    
    async def record_lineages_batch(
        self,
        category_code: str,
        view_name: str,
        feature_configs: List[Dict[str, Any]]
    ) -> int:
        """
        批量记录特征血缘
        
        Args:
            category_code: 资产类别编码
            view_name: 特征视图名称
            feature_configs: 特征配置列表
        
        Returns:
            int: 成功记录的数量
        """
        success_count = 0
        for config in feature_configs:
            if await self.record_lineage(category_code, view_name, config):
                success_count += 1
        return success_count
    
    async def get_lineage(
        self,
        category_code: str,
        view_name: str,
        feature_name: str
    ) -> Optional[FeatureLineage]:
        """
        获取特征血缘信息
        
        实现需求6.5: 查询特征的来源信号和计算逻辑
        
        Args:
            category_code: 资产类别编码
            view_name: 特征视图名称
            feature_name: 特征名称
        
        Returns:
            Optional[FeatureLineage]: 血缘信息，如果不存在则返回None
            
        Example:
            >>> tracker = LineageTracker()
            >>> lineage = await tracker.get_lineage("motor", "realtime", "avg_current")
            >>> print(lineage.source_signals)
            ['current']
        """
        try:
            feature_key = f"{category_code}:{view_name}:{feature_name}"
            
            # 先从内存图查找
            if feature_key in self._lineage_graph.feature_lineages:
                return self._lineage_graph.feature_lineages[feature_key]
            
            # 从数据库加载
            lineage = await self._load_lineage_from_db(
                category_code, view_name, feature_name
            )
            
            if lineage:
                # 缓存到内存图
                self._lineage_graph.add_lineage(lineage)
            
            return lineage
            
        except Exception as e:
            logger.error(f"❌ 获取特征血缘失败: {e}")
            return None
    
    async def get_downstream_features(
        self,
        signal_code: str,
        category_code: Optional[str] = None
    ) -> List[str]:
        """
        获取依赖某信号的所有特征
        
        Args:
            signal_code: 信号编码
            category_code: 资产类别编码 (可选，用于过滤)
        
        Returns:
            List[str]: 依赖该信号的特征列表
            
        Example:
            >>> tracker = LineageTracker()
            >>> features = await tracker.get_downstream_features("current")
            >>> print(features)
            ['motor:realtime:avg_current', 'motor:realtime:max_current']
        """
        try:
            # 从内存图获取
            features = self._lineage_graph.get_downstream_features(signal_code)
            
            # 如果内存图为空，从数据库加载
            if not features:
                features = await self._load_downstream_from_db(signal_code)
            
            # 按类别过滤
            if category_code:
                features = [f for f in features if f.startswith(f"{category_code}:")]
            
            return features
            
        except Exception as e:
            logger.error(f"❌ 获取下游特征失败: {e}")
            return []
    
    async def get_upstream_signals(
        self,
        category_code: str,
        view_name: str,
        feature_name: str
    ) -> List[str]:
        """
        获取特征依赖的所有源信号
        
        Args:
            category_code: 资产类别编码
            view_name: 特征视图名称
            feature_name: 特征名称
        
        Returns:
            List[str]: 源信号列表
        """
        try:
            feature_key = f"{category_code}:{view_name}:{feature_name}"
            
            # 从内存图获取
            signals = self._lineage_graph.get_upstream_signals(feature_key)
            
            if not signals:
                # 从数据库加载血缘信息
                lineage = await self.get_lineage(category_code, view_name, feature_name)
                if lineage:
                    signals = lineage.source_signals
            
            return signals
            
        except Exception as e:
            logger.error(f"❌ 获取上游信号失败: {e}")
            return []
    
    async def get_all_lineages(
        self,
        category_code: str,
        view_name: Optional[str] = None
    ) -> List[FeatureLineage]:
        """
        获取所有特征血缘信息
        
        Args:
            category_code: 资产类别编码
            view_name: 特征视图名称 (可选)
        
        Returns:
            List[FeatureLineage]: 血缘信息列表
        """
        try:
            lineages = await self._load_all_lineages_from_db(category_code, view_name)
            
            # 更新内存图
            for lineage in lineages:
                self._lineage_graph.add_lineage(lineage)
            
            return lineages
            
        except Exception as e:
            logger.error(f"❌ 获取所有血缘信息失败: {e}")
            return []
    
    async def delete_lineage(
        self,
        category_code: str,
        view_name: str,
        feature_name: str
    ) -> bool:
        """
        删除特征血缘信息
        
        Args:
            category_code: 资产类别编码
            view_name: 特征视图名称
            feature_name: 特征名称
        
        Returns:
            bool: 删除是否成功
        """
        try:
            feature_key = f"{category_code}:{view_name}:{feature_name}"
            
            # 从内存图删除
            if feature_key in self._lineage_graph.feature_lineages:
                lineage = self._lineage_graph.feature_lineages[feature_key]
                
                # 清理信号到特征的映射
                for signal in lineage.source_signals:
                    if signal in self._lineage_graph.signal_to_features:
                        if feature_key in self._lineage_graph.signal_to_features[signal]:
                            self._lineage_graph.signal_to_features[signal].remove(feature_key)
                
                # 清理特征到信号的映射
                if feature_key in self._lineage_graph.feature_to_signals:
                    del self._lineage_graph.feature_to_signals[feature_key]
                
                # 删除血缘信息
                del self._lineage_graph.feature_lineages[feature_key]
            
            # 从数据库删除
            await self._delete_lineage_from_db(category_code, view_name, feature_name)
            
            logger.info(f"✅ 特征血缘删除成功: {feature_key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 删除特征血缘失败: {e}")
            return False
    
    def _build_calculation_logic(
        self,
        function: str,
        source_signal: str,
        window: str,
        filters: Dict[str, Any]
    ) -> str:
        """
        构建计算逻辑描述
        
        Args:
            function: 聚合函数
            source_signal: 源信号
            window: 时间窗口
            filters: 过滤条件
        
        Returns:
            str: 计算逻辑描述
        """
        logic_parts = [f"{function.upper()}({source_signal})"]
        
        if window:
            logic_parts.append(f"WINDOW({window})")
        
        if filters:
            filter_strs = [f"{k}={v}" for k, v in filters.items()]
            logic_parts.append(f"FILTER({', '.join(filter_strs)})")
        
        return " ".join(logic_parts)
    
    async def _save_lineage_to_db(
        self,
        category_code: str,
        view_name: str,
        lineage: FeatureLineage
    ):
        """保存血缘信息到数据库"""
        try:
            from app.models.platform_upgrade import FeatureDefinition, AssetCategory
            
            # 获取资产类别
            category = await AssetCategory.get_or_none(code=category_code)
            if not category:
                logger.warning(f"资产类别不存在: {category_code}")
                return
            
            # 更新或创建特征定义
            feature_code = f"{view_name}_{lineage.feature_name}"
            
            await FeatureDefinition.update_or_create(
                category=category,
                code=feature_code,
                defaults={
                    "name": lineage.feature_name,
                    "calculation_config": lineage.metadata.get("original_config", {}),
                    "is_active": True
                }
            )
            
            logger.debug(f"血缘信息已保存到数据库: {feature_code}")
            
        except ImportError:
            logger.debug("数据库模型未配置，跳过保存")
        except Exception as e:
            logger.error(f"保存血缘信息到数据库失败: {e}")
    
    async def _load_lineage_from_db(
        self,
        category_code: str,
        view_name: str,
        feature_name: str
    ) -> Optional[FeatureLineage]:
        """从数据库加载血缘信息"""
        try:
            from app.models.platform_upgrade import FeatureDefinition
            
            feature_code = f"{view_name}_{feature_name}"
            
            definition = await FeatureDefinition.filter(
                code=feature_code,
                category__code=category_code
            ).first()
            
            if definition and definition.calculation_config:
                config = definition.calculation_config
                return FeatureLineage(
                    feature_name=feature_name,
                    source_signals=[config.get("source_signal", "")],
                    calculation_logic=self._build_calculation_logic(
                        config.get("function", ""),
                        config.get("source_signal", ""),
                        config.get("window", ""),
                        config.get("filters", {})
                    ),
                    created_at=definition.created_at or datetime.now(),
                    updated_at=definition.updated_at or datetime.now(),
                    category_code=category_code,
                    view_name=view_name,
                    metadata={"original_config": config}
                )
            
            return None
            
        except ImportError:
            logger.debug("数据库模型未配置")
            return None
        except Exception as e:
            logger.error(f"从数据库加载血缘信息失败: {e}")
            return None
    
    async def _load_downstream_from_db(self, signal_code: str) -> List[str]:
        """从数据库加载依赖某信号的特征"""
        try:
            from app.models.platform_upgrade import FeatureDefinition
            
            definitions = await FeatureDefinition.filter(
                calculation_config__source_signal=signal_code,
                is_active=True
            ).prefetch_related("category").all()
            
            features = []
            for d in definitions:
                category_code = d.category.code if d.category else ""
                # 从code中提取view_name和feature_name
                parts = d.code.split("_", 1)
                if len(parts) == 2:
                    view_name, feature_name = parts
                    features.append(f"{category_code}:{view_name}:{feature_name}")
            
            return features
            
        except ImportError:
            logger.debug("数据库模型未配置")
            return []
        except Exception as e:
            logger.error(f"从数据库加载下游特征失败: {e}")
            return []
    
    async def _load_all_lineages_from_db(
        self,
        category_code: str,
        view_name: Optional[str] = None
    ) -> List[FeatureLineage]:
        """从数据库加载所有血缘信息"""
        try:
            from app.models.platform_upgrade import FeatureDefinition
            
            query = FeatureDefinition.filter(
                category__code=category_code,
                is_active=True
            )
            
            if view_name:
                query = query.filter(code__startswith=f"{view_name}_")
            
            definitions = await query.all()
            
            lineages = []
            for d in definitions:
                if d.calculation_config:
                    config = d.calculation_config
                    # 从code中提取view_name和feature_name
                    parts = d.code.split("_", 1)
                    if len(parts) == 2:
                        v_name, f_name = parts
                        lineages.append(FeatureLineage(
                            feature_name=f_name,
                            source_signals=[config.get("source_signal", "")],
                            calculation_logic=self._build_calculation_logic(
                                config.get("function", ""),
                                config.get("source_signal", ""),
                                config.get("window", ""),
                                config.get("filters", {})
                            ),
                            created_at=d.created_at or datetime.now(),
                            updated_at=d.updated_at or datetime.now(),
                            category_code=category_code,
                            view_name=v_name,
                            metadata={"original_config": config}
                        ))
            
            return lineages
            
        except ImportError:
            logger.debug("数据库模型未配置")
            return []
        except Exception as e:
            logger.error(f"从数据库加载所有血缘信息失败: {e}")
            return []
    
    async def _delete_lineage_from_db(
        self,
        category_code: str,
        view_name: str,
        feature_name: str
    ):
        """从数据库删除血缘信息"""
        try:
            from app.models.platform_upgrade import FeatureDefinition
            
            feature_code = f"{view_name}_{feature_name}"
            
            await FeatureDefinition.filter(
                code=feature_code,
                category__code=category_code
            ).update(is_active=False)
            
            logger.debug(f"血缘信息已从数据库删除: {feature_code}")
            
        except ImportError:
            logger.debug("数据库模型未配置，跳过删除")
        except Exception as e:
            logger.error(f"从数据库删除血缘信息失败: {e}")


# =====================================================
# 全局实例
# =====================================================

lineage_tracker = LineageTracker()
