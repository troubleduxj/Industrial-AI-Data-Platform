#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工业AI数据平台数据库查询优化服务
提供查询优化、索引建议和慢查询分析

需求映射：
- 需求9.1: API响应时间亚秒级保证
- 需求9.4: 历史数据查询10秒内返回
"""

import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

from app.core.unified_logger import get_logger

logger = get_logger(__name__)


class QueryType(Enum):
    """查询类型"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    AGGREGATE = "AGGREGATE"
    JOIN = "JOIN"


@dataclass
class QueryPlan:
    """查询计划"""
    query_hash: str
    query_type: QueryType
    tables: List[str]
    estimated_rows: int
    estimated_cost: float
    uses_index: bool
    index_suggestions: List[str] = field(default_factory=list)


@dataclass
class SlowQueryRecord:
    """慢查询记录"""
    query_hash: str
    query_type: str
    table_name: str
    duration_ms: float
    rows_examined: int
    rows_returned: int
    timestamp: datetime
    query_pattern: str
    optimization_suggestions: List[str] = field(default_factory=list)


class QueryOptimizationStrategy(Enum):
    """查询优化策略"""
    ADD_INDEX = "add_index"
    REWRITE_QUERY = "rewrite_query"
    ADD_CACHE = "add_cache"
    PARTITION_TABLE = "partition_table"
    LIMIT_RESULTS = "limit_results"
    USE_COVERING_INDEX = "use_covering_index"


class PlatformQueryOptimizer:
    """平台查询优化器"""
    
    def __init__(self):
        # 慢查询阈值（毫秒）
        self.slow_query_threshold_ms = 100
        
        # 慢查询记录
        self.slow_queries: List[SlowQueryRecord] = []
        self.max_slow_queries = 1000
        
        # 查询统计
        self.query_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'total_duration': 0.0,
            'avg_duration': 0.0,
            'max_duration': 0.0,
            'slow_count': 0,
            'last_executed': None
        })
        
        # 索引建议缓存
        self.index_suggestions: Dict[str, List[str]] = {}
        
        # 查询模式缓存
        self.query_patterns: Dict[str, str] = {}
        
        # 优化建议
        self.optimization_rules = self._init_optimization_rules()
    
    def _init_optimization_rules(self) -> Dict[str, Dict[str, Any]]:
        """初始化优化规则"""
        return {
            'asset_category_list': {
                'pattern': 'SELECT * FROM asset_categories',
                'suggestions': [
                    '添加缓存，TTL=300秒',
                    '使用分页查询限制返回数量'
                ],
                'cache_ttl': 300
            },
            'asset_list_by_category': {
                'pattern': 'SELECT * FROM assets WHERE category_id',
                'suggestions': [
                    '确保category_id字段有索引',
                    '使用分页查询',
                    '考虑添加复合索引 (category_id, status)'
                ],
                'index': ['category_id', 'category_id_status']
            },
            'signal_definition_list': {
                'pattern': 'SELECT * FROM signal_definitions WHERE category_id',
                'suggestions': [
                    '添加缓存，TTL=300秒',
                    '确保category_id字段有索引'
                ],
                'cache_ttl': 300,
                'index': ['category_id']
            },
            'ai_model_list': {
                'pattern': 'SELECT * FROM ai_models',
                'suggestions': [
                    '添加缓存，TTL=120秒',
                    '使用分页查询'
                ],
                'cache_ttl': 120
            },
            'prediction_history': {
                'pattern': 'SELECT * FROM ai_predictions WHERE asset_id',
                'suggestions': [
                    '确保asset_id和prediction_time字段有复合索引',
                    '使用时间范围限制查询',
                    '考虑数据分区'
                ],
                'index': ['asset_id_prediction_time']
            },
            'feature_data_query': {
                'pattern': 'SELECT * FROM feat_',
                'suggestions': [
                    '使用TDengine的时间范围查询优化',
                    '限制返回的数据点数量',
                    '使用降采样查询'
                ]
            },
            'realtime_data_query': {
                'pattern': 'SELECT LAST(*) FROM raw_',
                'suggestions': [
                    '使用TDengine的LAST函数优化',
                    '添加短期缓存，TTL=5秒'
                ],
                'cache_ttl': 5
            },
            'historical_data_query': {
                'pattern': 'SELECT * FROM raw_ WHERE ts',
                'suggestions': [
                    '使用时间范围索引',
                    '限制返回数据量',
                    '使用降采样或聚合查询'
                ]
            }
        }
    
    def record_query(
        self,
        query_type: str,
        table_name: str,
        duration_ms: float,
        rows_examined: int = 0,
        rows_returned: int = 0,
        query_pattern: Optional[str] = None
    ) -> Optional[SlowQueryRecord]:
        """
        记录查询执行
        
        Args:
            query_type: 查询类型
            table_name: 表名
            duration_ms: 执行时间（毫秒）
            rows_examined: 扫描行数
            rows_returned: 返回行数
            query_pattern: 查询模式
            
        Returns:
            SlowQueryRecord: 如果是慢查询，返回记录
        """
        # 生成查询哈希
        query_hash = self._generate_query_hash(query_type, table_name, query_pattern)
        
        # 更新统计
        stats = self.query_stats[query_hash]
        stats['count'] += 1
        stats['total_duration'] += duration_ms
        stats['avg_duration'] = stats['total_duration'] / stats['count']
        stats['max_duration'] = max(stats['max_duration'], duration_ms)
        stats['last_executed'] = datetime.now()
        
        # 检查是否为慢查询
        if duration_ms > self.slow_query_threshold_ms:
            stats['slow_count'] += 1
            
            # 生成优化建议
            suggestions = self._generate_optimization_suggestions(
                query_type, table_name, duration_ms, rows_examined, rows_returned
            )
            
            record = SlowQueryRecord(
                query_hash=query_hash,
                query_type=query_type,
                table_name=table_name,
                duration_ms=duration_ms,
                rows_examined=rows_examined,
                rows_returned=rows_returned,
                timestamp=datetime.now(),
                query_pattern=query_pattern or f"{query_type} {table_name}",
                optimization_suggestions=suggestions
            )
            
            # 添加到慢查询列表
            self.slow_queries.append(record)
            if len(self.slow_queries) > self.max_slow_queries:
                self.slow_queries.pop(0)
            
            logger.warning(
                f"慢查询检测: {query_type} {table_name}, "
                f"duration={duration_ms}ms, rows={rows_returned}"
            )
            
            return record
        
        return None
    
    def _generate_query_hash(
        self,
        query_type: str,
        table_name: str,
        query_pattern: Optional[str]
    ) -> str:
        """生成查询哈希"""
        content = f"{query_type}:{table_name}:{query_pattern or ''}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _generate_optimization_suggestions(
        self,
        query_type: str,
        table_name: str,
        duration_ms: float,
        rows_examined: int,
        rows_returned: int
    ) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        # 检查是否匹配已知模式
        for rule_name, rule in self.optimization_rules.items():
            if table_name.lower() in rule['pattern'].lower():
                suggestions.extend(rule['suggestions'])
        
        # 基于执行情况的通用建议
        if rows_examined > 0 and rows_returned > 0:
            scan_ratio = rows_examined / rows_returned
            if scan_ratio > 10:
                suggestions.append(f"扫描效率低（扫描{rows_examined}行返回{rows_returned}行），考虑添加索引")
        
        if duration_ms > 500:
            suggestions.append("查询时间过长，考虑添加缓存或优化查询")
        
        if duration_ms > 1000:
            suggestions.append("严重慢查询，需要立即优化")
        
        # 根据查询类型的特定建议
        if query_type == "SELECT" and rows_returned > 1000:
            suggestions.append("返回数据量大，考虑使用分页查询")
        
        if query_type == "SELECT" and "JOIN" in table_name.upper():
            suggestions.append("JOIN查询，确保关联字段有索引")
        
        return list(set(suggestions))  # 去重
    
    def get_slow_queries(
        self,
        limit: int = 50,
        min_duration_ms: Optional[float] = None,
        table_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取慢查询列表
        
        Args:
            limit: 返回数量限制
            min_duration_ms: 最小执行时间过滤
            table_name: 表名过滤
            
        Returns:
            List[Dict]: 慢查询列表
        """
        queries = self.slow_queries.copy()
        
        # 过滤
        if min_duration_ms:
            queries = [q for q in queries if q.duration_ms >= min_duration_ms]
        
        if table_name:
            queries = [q for q in queries if table_name.lower() in q.table_name.lower()]
        
        # 按执行时间排序
        queries.sort(key=lambda x: x.duration_ms, reverse=True)
        
        # 转换为字典
        return [
            {
                'query_hash': q.query_hash,
                'query_type': q.query_type,
                'table_name': q.table_name,
                'duration_ms': q.duration_ms,
                'rows_examined': q.rows_examined,
                'rows_returned': q.rows_returned,
                'timestamp': q.timestamp.isoformat(),
                'query_pattern': q.query_pattern,
                'optimization_suggestions': q.optimization_suggestions
            }
            for q in queries[:limit]
        ]
    
    def get_query_stats(self, table_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取查询统计
        
        Args:
            table_name: 表名过滤
            
        Returns:
            Dict: 查询统计
        """
        stats = {}
        
        for query_hash, query_stats in self.query_stats.items():
            if table_name and table_name.lower() not in query_hash.lower():
                continue
            
            stats[query_hash] = {
                'count': query_stats['count'],
                'avg_duration_ms': query_stats['avg_duration'],
                'max_duration_ms': query_stats['max_duration'],
                'slow_count': query_stats['slow_count'],
                'slow_rate': query_stats['slow_count'] / query_stats['count'] if query_stats['count'] > 0 else 0,
                'last_executed': query_stats['last_executed'].isoformat() if query_stats['last_executed'] else None
            }
        
        return stats
    
    def get_index_suggestions(self, table_name: str) -> List[str]:
        """
        获取索引建议
        
        Args:
            table_name: 表名
            
        Returns:
            List[str]: 索引建议列表
        """
        suggestions = []
        
        # 从优化规则中获取
        for rule_name, rule in self.optimization_rules.items():
            if table_name.lower() in rule['pattern'].lower():
                if 'index' in rule:
                    suggestions.extend(rule['index'])
        
        # 从慢查询分析中获取
        table_slow_queries = [
            q for q in self.slow_queries
            if table_name.lower() in q.table_name.lower()
        ]
        
        if len(table_slow_queries) > 5:
            suggestions.append(f"表 {table_name} 有 {len(table_slow_queries)} 个慢查询，建议分析查询模式")
        
        return list(set(suggestions))
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """
        获取优化报告
        
        Returns:
            Dict: 优化报告
        """
        # 统计慢查询
        slow_query_count = len(self.slow_queries)
        
        # 按表分组统计
        table_stats = defaultdict(lambda: {'count': 0, 'total_duration': 0, 'slow_count': 0})
        
        for query_hash, stats in self.query_stats.items():
            # 从哈希中提取表名（简化处理）
            table_stats['all']['count'] += stats['count']
            table_stats['all']['total_duration'] += stats['total_duration']
            table_stats['all']['slow_count'] += stats['slow_count']
        
        # 生成报告
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_queries': table_stats['all']['count'],
                'total_slow_queries': slow_query_count,
                'slow_query_rate': slow_query_count / table_stats['all']['count'] if table_stats['all']['count'] > 0 else 0,
                'avg_query_time_ms': table_stats['all']['total_duration'] / table_stats['all']['count'] if table_stats['all']['count'] > 0 else 0
            },
            'top_slow_queries': self.get_slow_queries(limit=10),
            'recommendations': self._generate_global_recommendations()
        }
        
        return report
    
    def _generate_global_recommendations(self) -> List[str]:
        """生成全局优化建议"""
        recommendations = []
        
        # 分析慢查询模式
        if len(self.slow_queries) > 100:
            recommendations.append("慢查询数量较多，建议进行全面的查询优化")
        
        # 检查高频慢查询
        high_freq_slow = [
            (hash, stats) for hash, stats in self.query_stats.items()
            if stats['slow_count'] > 10
        ]
        
        if high_freq_slow:
            recommendations.append(f"发现 {len(high_freq_slow)} 个高频慢查询，优先优化这些查询")
        
        # 通用建议
        recommendations.extend([
            "定期检查并更新数据库统计信息",
            "考虑使用连接池优化数据库连接",
            "对热点数据使用Redis缓存",
            "对时序数据使用TDengine的时间分区"
        ])
        
        return recommendations
    
    def analyze_query_pattern(self, query: str) -> Dict[str, Any]:
        """
        分析查询模式
        
        Args:
            query: SQL查询语句
            
        Returns:
            Dict: 分析结果
        """
        query_upper = query.upper().strip()
        
        # 识别查询类型
        if query_upper.startswith('SELECT'):
            query_type = QueryType.SELECT
        elif query_upper.startswith('INSERT'):
            query_type = QueryType.INSERT
        elif query_upper.startswith('UPDATE'):
            query_type = QueryType.UPDATE
        elif query_upper.startswith('DELETE'):
            query_type = QueryType.DELETE
        else:
            query_type = QueryType.SELECT
        
        # 检查是否有聚合
        has_aggregate = any(
            agg in query_upper
            for agg in ['COUNT(', 'SUM(', 'AVG(', 'MAX(', 'MIN(', 'GROUP BY']
        )
        
        # 检查是否有JOIN
        has_join = 'JOIN' in query_upper
        
        # 检查是否有子查询
        has_subquery = query_upper.count('SELECT') > 1
        
        # 生成建议
        suggestions = []
        
        if has_aggregate and 'INDEX' not in query_upper:
            suggestions.append("聚合查询建议使用覆盖索引")
        
        if has_join:
            suggestions.append("JOIN查询确保关联字段有索引")
        
        if has_subquery:
            suggestions.append("考虑将子查询改写为JOIN")
        
        if 'SELECT *' in query_upper:
            suggestions.append("避免使用SELECT *，只查询需要的字段")
        
        if 'LIKE' in query_upper and '%' in query:
            suggestions.append("LIKE查询以%开头无法使用索引")
        
        return {
            'query_type': query_type.value,
            'has_aggregate': has_aggregate,
            'has_join': has_join,
            'has_subquery': has_subquery,
            'suggestions': suggestions
        }


# 全局查询优化器实例
platform_query_optimizer = PlatformQueryOptimizer()
