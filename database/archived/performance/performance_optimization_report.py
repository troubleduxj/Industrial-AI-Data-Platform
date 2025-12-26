#!/usr/bin/env python3
"""
数据库性能优化报告生成器
API权限重构项目 - 任务3.5
创建时间: 2025-01-10
"""

import asyncio
import asyncpg
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class OptimizationRecommendation:
    """优化建议"""
    category: str
    priority: str  # 'high', 'medium', 'low'
    title: str
    description: str
    impact: str
    implementation_effort: str
    sql_commands: List[str]

class DatabasePerformanceReportGenerator:
    """数据库性能优化报告生成器"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn: Optional[asyncpg.Connection] = None
        self.report_data = {}
        self.recommendations = []
        
        # 权限相关表列表
        self.permission_tables = [
            't_sys_api_endpoints',
            't_sys_user_permissions', 
            't_sys_role_permissions',
            't_sys_user_roles'
        ]
    
    async def connect(self):
        """连接数据库"""
        try:
            self.conn = await asyncpg.connect(self.database_url)
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    async def disconnect(self):
        """断开数据库连接"""
        if self.conn:
            await self.conn.close()
            logger.info("数据库连接已断开")
    
    async def generate_comprehensive_report(self, output_dir: str = "reports") -> str:
        """生成综合性能优化报告"""
        logger.info("开始生成数据库性能优化报告")
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 收集各种性能数据
        await self._collect_table_statistics()
        await self._collect_index_analysis()
        await self._collect_query_performance()
        await self._collect_cache_statistics()
        await self._collect_connection_analysis()
        await self._analyze_optimization_opportunities()
        
        # 生成报告文件
        report_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 生成Markdown报告
        md_report_path = output_path / f"performance_optimization_report_{report_timestamp}.md"
        await self._generate_markdown_report(md_report_path)
        
        # 生成JSON报告
        json_report_path = output_path / f"performance_data_{report_timestamp}.json"
        await self._generate_json_report(json_report_path)
        
        # 生成图表
        charts_dir = output_path / f"charts_{report_timestamp}"
        await self._generate_performance_charts(charts_dir)
        
        logger.info(f"性能优化报告生成完成: {md_report_path}")
        return str(md_report_path)
    
    async def _collect_table_statistics(self):
        """收集表统计信息"""
        logger.info("收集表统计信息...")
        
        query = """
            SELECT 
                schemaname,
                tablename,
                seq_scan,
                seq_tup_read,
                idx_scan,
                idx_tup_fetch,
                n_tup_ins,
                n_tup_upd,
                n_tup_del,
                n_tup_hot_upd,
                n_live_tup,
                n_dead_tup,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size
            FROM pg_stat_user_tables 
            WHERE tablename = ANY($1)
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """
        
        rows = await self.conn.fetch(query, self.permission_tables)
        
        table_stats = []
        for row in rows:
            total_scans = (row['seq_scan'] or 0) + (row['idx_scan'] or 0)
            seq_scan_ratio = (row['seq_scan'] or 0) / max(total_scans, 1) if total_scans > 0 else 0
            
            # 计算死元组比例
            total_tuples = (row['n_live_tup'] or 0) + (row['n_dead_tup'] or 0)
            dead_tuple_ratio = (row['n_dead_tup'] or 0) / max(total_tuples, 1) if total_tuples > 0 else 0
            
            stats = dict(row)
            stats.update({
                'total_scans': total_scans,
                'seq_scan_ratio': seq_scan_ratio,
                'dead_tuple_ratio': dead_tuple_ratio,
                'needs_vacuum': dead_tuple_ratio > 0.1,
                'high_seq_scan': seq_scan_ratio > 0.5 and total_scans > 100
            })
            table_stats.append(stats)
            
            # 生成优化建议
            if stats['high_seq_scan']:
                self.recommendations.append(OptimizationRecommendation(
                    category='索引优化',
                    priority='high',
                    title=f'表 {row["tablename"]} 顺序扫描过多',
                    description=f'该表的顺序扫描比例为 {seq_scan_ratio:.1%}，建议添加适当的索引',
                    impact='显著提升查询性能',
                    implementation_effort='中等',
                    sql_commands=[
                        f"-- 分析表 {row['tablename']} 的查询模式",
                        f"ANALYZE {row['tablename']};",
                        f"-- 根据查询模式添加适当的索引"
                    ]
                ))
            
            if stats['needs_vacuum']:
                self.recommendations.append(OptimizationRecommendation(
                    category='维护优化',
                    priority='medium',
                    title=f'表 {row["tablename"]} 需要清理',
                    description=f'该表的死元组比例为 {dead_tuple_ratio:.1%}，建议执行VACUUM',
                    impact='释放存储空间，提升查询性能',
                    implementation_effort='低',
                    sql_commands=[
                        f"VACUUM ANALYZE {row['tablename']};",
                        f"-- 考虑调整autovacuum参数"
                    ]
                ))
        
        self.report_data['table_statistics'] = table_stats
    
    async def _collect_index_analysis(self):
        """收集索引分析信息"""
        logger.info("收集索引分析信息...")
        
        # 索引使用统计
        index_usage_query = """
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch,
                pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size,
                pg_relation_size(indexname::regclass) as index_size_bytes
            FROM pg_stat_user_indexes 
            WHERE tablename = ANY($1)
            ORDER BY idx_scan DESC
        """
        
        index_rows = await self.conn.fetch(index_usage_query, self.permission_tables)
        
        # 索引定义查询
        index_def_query = """
            SELECT 
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE tablename = ANY($1)
            ORDER BY tablename, indexname
        """
        
        index_def_rows = await self.conn.fetch(index_def_query, self.permission_tables)
        
        # 合并索引信息
        index_analysis = []
        for usage_row in index_rows:
            # 查找对应的索引定义
            index_def = next(
                (def_row['indexdef'] for def_row in index_def_rows 
                 if def_row['indexname'] == usage_row['indexname']),
                'Unknown'
            )
            
            analysis = dict(usage_row)
            analysis['indexdef'] = index_def
            analysis['is_unused'] = (usage_row['idx_scan'] or 0) < 10
            analysis['efficiency'] = (usage_row['idx_tup_fetch'] or 0) / max(usage_row['idx_tup_read'] or 1, 1)
            
            index_analysis.append(analysis)
            
            # 生成优化建议
            if analysis['is_unused'] and not usage_row['indexname'].endswith('_pkey'):
                self.recommendations.append(OptimizationRecommendation(
                    category='索引优化',
                    priority='low',
                    title=f'索引 {usage_row["indexname"]} 使用率低',
                    description=f'该索引扫描次数仅为 {usage_row["idx_scan"]}，考虑是否需要删除',
                    impact='节省存储空间，提升写入性能',
                    implementation_effort='低',
                    sql_commands=[
                        f"-- 确认索引不再需要后删除",
                        f"DROP INDEX IF EXISTS {usage_row['indexname']};"
                    ]
                ))
        
        self.report_data['index_analysis'] = index_analysis
        
        # 缺失索引分析
        await self._analyze_missing_indexes()
    
    async def _analyze_missing_indexes(self):
        """分析可能缺失的索引"""
        logger.info("分析可能缺失的索引...")
        
        missing_indexes = []
        
        # 检查权限验证相关的常用查询模式
        common_patterns = [
            {
                'table': 't_sys_user_permissions',
                'columns': ['user_id', 'permission_code', 'is_active'],
                'reason': '用户权限验证查询'
            },
            {
                'table': 't_sys_role_permissions', 
                'columns': ['role_id', 'permission_code', 'is_active'],
                'reason': '角色权限验证查询'
            },
            {
                'table': 't_sys_api_endpoints',
                'columns': ['api_path', 'http_method', 'status'],
                'reason': 'API权限验证查询'
            }
        ]
        
        for pattern in common_patterns:
            # 检查是否存在对应的复合索引
            index_check_query = """
                SELECT COUNT(*) as index_count
                FROM pg_indexes 
                WHERE tablename = $1 
                  AND indexdef ILIKE $2
            """
            
            index_pattern = f"%{', '.join(pattern['columns'])}%"
            count = await self.conn.fetchval(index_check_query, pattern['table'], index_pattern)
            
            if count == 0:
                missing_indexes.append({
                    'table': pattern['table'],
                    'columns': pattern['columns'],
                    'reason': pattern['reason'],
                    'suggested_name': f"idx_{pattern['table'].replace('t_sys_', '')}_{('_'.join(pattern['columns']))}"
                })
                
                # 生成优化建议
                self.recommendations.append(OptimizationRecommendation(
                    category='索引优化',
                    priority='high',
                    title=f'建议为 {pattern["table"]} 添加复合索引',
                    description=f'为 {pattern["reason"]} 添加复合索引可显著提升性能',
                    impact='显著提升查询性能',
                    implementation_effort='低',
                    sql_commands=[
                        f"CREATE INDEX CONCURRENTLY {missing_indexes[-1]['suggested_name']}",
                        f"ON {pattern['table']}({', '.join(pattern['columns'])});",
                        f"-- 用于优化: {pattern['reason']}"
                    ]
                ))
        
        self.report_data['missing_indexes'] = missing_indexes
    
    async def _collect_query_performance(self):
        """收集查询性能信息"""
        logger.info("收集查询性能信息...")
        
        # 检查pg_stat_statements扩展
        extension_check = await self.conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
            )
        """)
        
        if not extension_check:
            logger.warning("pg_stat_statements扩展未安装，跳过查询性能分析")
            self.report_data['query_performance'] = {
                'available': False,
                'message': 'pg_stat_statements扩展未安装'
            }
            return
        
        # 查询慢查询统计
        slow_queries_query = """
            SELECT 
                query,
                calls,
                total_time,
                mean_time,
                max_time,
                min_time,
                rows,
                shared_blks_hit,
                shared_blks_read,
                shared_blks_dirtied,
                shared_blks_written,
                100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
            FROM pg_stat_statements 
            WHERE query ILIKE ANY(ARRAY['%t_sys_%', '%permission%', '%api%'])
            ORDER BY mean_time DESC
            LIMIT 20
        """
        
        slow_queries = await self.conn.fetch(slow_queries_query)
        
        query_stats = []
        for row in slow_queries:
            stats = dict(row)
            stats['is_slow'] = row['mean_time'] > 100  # 100ms阈值
            stats['cache_efficiency'] = row['hit_percent'] or 0
            query_stats.append(stats)
            
            # 生成优化建议
            if stats['is_slow']:
                self.recommendations.append(OptimizationRecommendation(
                    category='查询优化',
                    priority='high',
                    title=f'慢查询优化 (平均 {row["mean_time"]:.1f}ms)',
                    description=f'该查询平均执行时间过长，需要优化',
                    impact='显著提升响应时间',
                    implementation_effort='中等到高',
                    sql_commands=[
                        "-- 使用EXPLAIN ANALYZE分析查询计划",
                        f"EXPLAIN (ANALYZE, BUFFERS) {row['query'][:100]}...;",
                        "-- 根据执行计划优化索引和查询结构"
                    ]
                ))
        
        self.report_data['query_performance'] = {
            'available': True,
            'slow_queries': query_stats,
            'total_queries_analyzed': len(query_stats)
        }
    
    async def _collect_cache_statistics(self):
        """收集缓存统计信息"""
        logger.info("收集缓存统计信息...")
        
        # 数据库级别缓存统计
        db_cache_query = """
            SELECT 
                sum(heap_blks_read) as heap_read,
                sum(heap_blks_hit) as heap_hit,
                sum(idx_blks_read) as idx_read,
                sum(idx_blks_hit) as idx_hit,
                sum(toast_blks_read) as toast_read,
                sum(toast_blks_hit) as toast_hit
            FROM pg_statio_user_tables 
            WHERE relname = ANY($1)
        """
        
        cache_row = await self.conn.fetchrow(db_cache_query, self.permission_tables)
        
        # 计算缓存命中率
        total_heap = (cache_row['heap_read'] or 0) + (cache_row['heap_hit'] or 0)
        total_idx = (cache_row['idx_read'] or 0) + (cache_row['idx_hit'] or 0)
        
        heap_hit_ratio = (cache_row['heap_hit'] or 0) / max(total_heap, 1) if total_heap > 0 else 0
        idx_hit_ratio = (cache_row['idx_hit'] or 0) / max(total_idx, 1) if total_idx > 0 else 0
        
        # 系统级别缓存统计
        system_cache_query = """
            SELECT 
                setting as shared_buffers
            FROM pg_settings 
            WHERE name = 'shared_buffers'
        """
        
        shared_buffers = await self.conn.fetchval(system_cache_query)
        
        cache_stats = {
            'heap_hit_ratio': heap_hit_ratio,
            'index_hit_ratio': idx_hit_ratio,
            'shared_buffers': shared_buffers,
            'total_heap_blocks': total_heap,
            'total_index_blocks': total_idx,
            'cache_efficiency': 'good' if heap_hit_ratio > 0.95 else 'needs_improvement'
        }
        
        # 生成优化建议
        if heap_hit_ratio < 0.95 and total_heap > 1000:
            self.recommendations.append(OptimizationRecommendation(
                category='缓存优化',
                priority='medium',
                title='数据库缓存命中率偏低',
                description=f'堆缓存命中率为 {heap_hit_ratio:.1%}，建议调整shared_buffers参数',
                impact='提升整体查询性能',
                implementation_effort='中等',
                sql_commands=[
                    "-- 在postgresql.conf中调整shared_buffers",
                    "# shared_buffers = 256MB  # 建议设置为内存的25%",
                    "-- 重启数据库服务使配置生效"
                ]
            ))
        
        self.report_data['cache_statistics'] = cache_stats
    
    async def _collect_connection_analysis(self):
        """收集连接分析信息"""
        logger.info("收集连接分析信息...")
        
        connection_query = """
            SELECT 
                count(*) as total_connections,
                count(*) FILTER (WHERE state = 'active') as active_connections,
                count(*) FILTER (WHERE state = 'idle') as idle_connections,
                count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction,
                max(setting::int) as max_connections,
                avg(EXTRACT(EPOCH FROM (now() - query_start))) as avg_query_duration
            FROM pg_stat_activity, pg_settings 
            WHERE pg_settings.name = 'max_connections'
              AND pid != pg_backend_pid()
        """
        
        conn_row = await self.conn.fetchrow(connection_query)
        
        connection_usage = conn_row['total_connections'] / max(conn_row['max_connections'], 1)
        
        connection_stats = dict(conn_row)
        connection_stats.update({
            'connection_usage_ratio': connection_usage,
            'connection_efficiency': 'good' if connection_usage < 0.8 else 'high_usage'
        })
        
        # 生成优化建议
        if connection_usage > 0.8:
            self.recommendations.append(OptimizationRecommendation(
                category='连接优化',
                priority='high',
                title='数据库连接使用率过高',
                description=f'连接使用率为 {connection_usage:.1%}，建议使用连接池或增加最大连接数',
                impact='避免连接耗尽，提升系统稳定性',
                implementation_effort='中等',
                sql_commands=[
                    "-- 在postgresql.conf中调整max_connections",
                    "# max_connections = 200",
                    "-- 或者使用连接池如PgBouncer"
                ]
            ))
        
        if conn_row['idle_in_transaction'] > 5:
            self.recommendations.append(OptimizationRecommendation(
                category='连接优化',
                priority='medium',
                title='存在过多空闲事务连接',
                description=f'有 {conn_row["idle_in_transaction"]} 个空闲事务连接，可能导致锁等待',
                impact='减少锁等待，提升并发性能',
                implementation_effort='低',
                sql_commands=[
                    "-- 设置空闲事务超时",
                    "# idle_in_transaction_session_timeout = 60s"
                ]
            ))
        
        self.report_data['connection_analysis'] = connection_stats
    
    async def _analyze_optimization_opportunities(self):
        """分析优化机会"""
        logger.info("分析优化机会...")
        
        # 按优先级排序建议
        self.recommendations.sort(key=lambda x: {'high': 3, 'medium': 2, 'low': 1}[x.priority], reverse=True)
        
        # 统计建议分类
        recommendation_summary = {
            'total_recommendations': len(self.recommendations),
            'by_priority': {
                'high': len([r for r in self.recommendations if r.priority == 'high']),
                'medium': len([r for r in self.recommendations if r.priority == 'medium']),
                'low': len([r for r in self.recommendations if r.priority == 'low'])
            },
            'by_category': {}
        }
        
        for rec in self.recommendations:
            if rec.category not in recommendation_summary['by_category']:
                recommendation_summary['by_category'][rec.category] = 0
            recommendation_summary['by_category'][rec.category] += 1
        
        self.report_data['optimization_summary'] = recommendation_summary
    
    async def _generate_markdown_report(self, output_path: Path):
        """生成Markdown格式报告"""
        logger.info(f"生成Markdown报告: {output_path}")
        
        report_content = f"""# 数据库性能优化报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**数据库**: PostgreSQL  
**分析范围**: API权限系统相关表  

## 执行摘要

本报告分析了API权限系统相关数据库表的性能状况，识别了 **{self.report_data['optimization_summary']['total_recommendations']}** 个优化机会，其中：

- 🔴 高优先级: {self.report_data['optimization_summary']['by_priority']['high']} 个
- 🟡 中优先级: {self.report_data['optimization_summary']['by_priority']['medium']} 个  
- 🟢 低优先级: {self.report_data['optimization_summary']['by_priority']['low']} 个

## 1. 表统计分析

### 1.1 表大小和访问模式

| 表名 | 大小 | 活跃元组 | 死元组 | 顺序扫描比例 | 状态 |
|------|------|----------|--------|--------------|------|
"""
        
        for table in self.report_data['table_statistics']:
            status = "⚠️ 需要优化" if table['high_seq_scan'] or table['needs_vacuum'] else "✅ 正常"
            report_content += f"| {table['tablename']} | {table['table_size']} | {table['n_live_tup']:,} | {table['n_dead_tup']:,} | {table['seq_scan_ratio']:.1%} | {status} |\n"
        
        report_content += f"""

### 1.2 表维护状态

"""
        
        for table in self.report_data['table_statistics']:
            if table['needs_vacuum'] or table['high_seq_scan']:
                report_content += f"""
**{table['tablename']}**:
- 死元组比例: {table['dead_tuple_ratio']:.1%}
- 顺序扫描比例: {table['seq_scan_ratio']:.1%}
- 最后VACUUM: {table['last_vacuum'] or '未知'}
- 最后ANALYZE: {table['last_analyze'] or '未知'}
"""

        report_content += f"""

## 2. 索引分析

### 2.1 现有索引使用情况

| 索引名 | 表名 | 扫描次数 | 大小 | 效率 | 状态 |
|--------|------|----------|------|------|------|
"""
        
        for index in self.report_data['index_analysis']:
            status = "⚠️ 低使用率" if index['is_unused'] else "✅ 正常使用"
            report_content += f"| {index['indexname']} | {index['tablename']} | {index['idx_scan']:,} | {index['index_size']} | {index['efficiency']:.2f} | {status} |\n"
        
        if self.report_data.get('missing_indexes'):
            report_content += f"""

### 2.2 建议添加的索引

"""
            for missing in self.report_data['missing_indexes']:
                report_content += f"""
**{missing['suggested_name']}**:
- 表: {missing['table']}
- 列: {', '.join(missing['columns'])}
- 用途: {missing['reason']}
"""

        # 查询性能分析
        if self.report_data['query_performance']['available']:
            report_content += f"""

## 3. 查询性能分析

### 3.1 慢查询统计

| 平均时间(ms) | 调用次数 | 缓存命中率 | 查询片段 |
|--------------|----------|------------|----------|
"""
            
            for query in self.report_data['query_performance']['slow_queries'][:10]:
                query_snippet = query['query'][:80].replace('\n', ' ') + '...'
                report_content += f"| {query['mean_time']:.1f} | {query['calls']:,} | {query['cache_efficiency']:.1f}% | `{query_snippet}` |\n"
        
        # 缓存统计
        cache_stats = self.report_data['cache_statistics']
        report_content += f"""

## 4. 缓存性能分析

### 4.1 缓存命中率

- **堆缓存命中率**: {cache_stats['heap_hit_ratio']:.1%}
- **索引缓存命中率**: {cache_stats['index_hit_ratio']:.1%}
- **共享缓冲区大小**: {cache_stats['shared_buffers']}
- **整体评估**: {cache_stats['cache_efficiency']}

"""
        
        # 连接分析
        conn_stats = self.report_data['connection_analysis']
        report_content += f"""

## 5. 连接分析

### 5.1 连接使用情况

- **总连接数**: {conn_stats['total_connections']}
- **活跃连接**: {conn_stats['active_connections']}
- **空闲连接**: {conn_stats['idle_connections']}
- **空闲事务连接**: {conn_stats['idle_in_transaction']}
- **最大连接数**: {conn_stats['max_connections']}
- **连接使用率**: {conn_stats['connection_usage_ratio']:.1%}

"""
        
        # 优化建议
        report_content += f"""

## 6. 优化建议

### 6.1 高优先级建议

"""
        
        high_priority_recs = [r for r in self.recommendations if r.priority == 'high']
        for i, rec in enumerate(high_priority_recs, 1):
            report_content += f"""
#### {i}. {rec.title}

**分类**: {rec.category}  
**影响**: {rec.impact}  
**实施难度**: {rec.implementation_effort}

**描述**: {rec.description}

**实施步骤**:
```sql
{chr(10).join(rec.sql_commands)}
```

"""
        
        # 中优先级建议
        medium_priority_recs = [r for r in self.recommendations if r.priority == 'medium']
        if medium_priority_recs:
            report_content += f"""

### 6.2 中优先级建议

"""
            for i, rec in enumerate(medium_priority_recs, 1):
                report_content += f"""
#### {i}. {rec.title}

**描述**: {rec.description}  
**影响**: {rec.impact}

```sql
{chr(10).join(rec.sql_commands)}
```

"""
        
        # 低优先级建议
        low_priority_recs = [r for r in self.recommendations if r.priority == 'low']
        if low_priority_recs:
            report_content += f"""

### 6.3 低优先级建议

"""
            for i, rec in enumerate(low_priority_recs, 1):
                report_content += f"- **{rec.title}**: {rec.description}\n"
        
        # 实施计划
        report_content += f"""

## 7. 实施计划建议

### 7.1 第一阶段 (立即执行)
- 执行所有高优先级的索引优化
- 清理需要VACUUM的表
- 修复慢查询问题

### 7.2 第二阶段 (1-2周内)
- 实施缓存优化配置
- 优化连接池配置
- 执行中优先级建议

### 7.3 第三阶段 (持续优化)
- 监控性能指标变化
- 根据业务增长调整配置
- 定期执行性能分析

## 8. 监控建议

建议建立以下监控指标：

1. **查询性能监控**
   - 平均查询响应时间
   - 慢查询数量和频率
   - 查询吞吐量

2. **资源使用监控**
   - 缓存命中率
   - 连接使用率
   - 磁盘I/O性能

3. **表维护监控**
   - 死元组比例
   - 表膨胀率
   - VACUUM/ANALYZE执行频率

---

**报告生成工具**: 数据库性能优化分析器  
**版本**: 1.0  
**联系**: 数据库管理团队
"""
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
    
    async def _generate_json_report(self, output_path: Path):
        """生成JSON格式报告"""
        logger.info(f"生成JSON报告: {output_path}")
        
        # 转换recommendations为可序列化格式
        recommendations_data = []
        for rec in self.recommendations:
            recommendations_data.append({
                'category': rec.category,
                'priority': rec.priority,
                'title': rec.title,
                'description': rec.description,
                'impact': rec.impact,
                'implementation_effort': rec.implementation_effort,
                'sql_commands': rec.sql_commands
            })
        
        json_data = {
            'generated_at': datetime.now().isoformat(),
            'database_type': 'PostgreSQL',
            'analysis_scope': 'API Permission System Tables',
            'summary': self.report_data['optimization_summary'],
            'table_statistics': self.report_data['table_statistics'],
            'index_analysis': self.report_data['index_analysis'],
            'missing_indexes': self.report_data.get('missing_indexes', []),
            'query_performance': self.report_data['query_performance'],
            'cache_statistics': self.report_data['cache_statistics'],
            'connection_analysis': self.report_data['connection_analysis'],
            'recommendations': recommendations_data
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)
    
    async def _generate_performance_charts(self, charts_dir: Path):
        """生成性能图表"""
        logger.info(f"生成性能图表: {charts_dir}")
        
        charts_dir.mkdir(exist_ok=True)
        
        try:
            # 1. 表大小分布图
            table_names = [t['tablename'] for t in self.report_data['table_statistics']]
            table_sizes = [t['n_live_tup'] for t in self.report_data['table_statistics']]
            
            plt.figure(figsize=(12, 6))
            plt.bar(table_names, table_sizes)
            plt.title('表记录数分布')
            plt.xlabel('表名')
            plt.ylabel('记录数')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(charts_dir / 'table_sizes.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            # 2. 顺序扫描比例图
            seq_scan_ratios = [t['seq_scan_ratio'] for t in self.report_data['table_statistics']]
            
            plt.figure(figsize=(12, 6))
            bars = plt.bar(table_names, seq_scan_ratios)
            # 标记高顺序扫描的表
            for i, (bar, ratio) in enumerate(zip(bars, seq_scan_ratios)):
                if ratio > 0.5:
                    bar.set_color('red')
                elif ratio > 0.3:
                    bar.set_color('orange')
                else:
                    bar.set_color('green')
            
            plt.title('表顺序扫描比例')
            plt.xlabel('表名')
            plt.ylabel('顺序扫描比例')
            plt.xticks(rotation=45)
            plt.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='警告线(50%)')
            plt.legend()
            plt.tight_layout()
            plt.savefig(charts_dir / 'seq_scan_ratios.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            # 3. 索引使用情况图
            if self.report_data['index_analysis']:
                index_names = [idx['indexname'][:20] + '...' if len(idx['indexname']) > 20 
                              else idx['indexname'] for idx in self.report_data['index_analysis']]
                index_scans = [idx['idx_scan'] for idx in self.report_data['index_analysis']]
                
                plt.figure(figsize=(15, 8))
                bars = plt.bar(range(len(index_names)), index_scans)
                
                # 标记未使用的索引
                for i, (bar, scans) in enumerate(zip(bars, index_scans)):
                    if scans < 10:
                        bar.set_color('red')
                    elif scans < 100:
                        bar.set_color('orange')
                    else:
                        bar.set_color('green')
                
                plt.title('索引使用频率')
                plt.xlabel('索引名')
                plt.ylabel('扫描次数')
                plt.xticks(range(len(index_names)), index_names, rotation=45, ha='right')
                plt.yscale('log')  # 使用对数刻度
                plt.tight_layout()
                plt.savefig(charts_dir / 'index_usage.png', dpi=300, bbox_inches='tight')
                plt.close()
            
            # 4. 优化建议分布图
            categories = list(self.report_data['optimization_summary']['by_category'].keys())
            counts = list(self.report_data['optimization_summary']['by_category'].values())
            
            plt.figure(figsize=(10, 8))
            plt.pie(counts, labels=categories, autopct='%1.1f%%', startangle=90)
            plt.title('优化建议分类分布')
            plt.axis('equal')
            plt.tight_layout()
            plt.savefig(charts_dir / 'recommendations_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info("性能图表生成完成")
            
        except ImportError:
            logger.warning("matplotlib未安装，跳过图表生成")
        except Exception as e:
            logger.error(f"生成图表时发生错误: {e}")

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库性能优化报告生成器')
    parser.add_argument('--db-url', required=True, help='数据库连接URL')
    parser.add_argument('--output-dir', default='reports', help='报告输出目录')
    
    args = parser.parse_args()
    
    generator = DatabasePerformanceReportGenerator(args.db_url)
    
    try:
        await generator.connect()
        report_path = await generator.generate_comprehensive_report(args.output_dir)
        print(f"✅ 性能优化报告生成完成: {report_path}")
        
    except Exception as e:
        logger.error(f"生成报告失败: {e}")
    finally:
        await generator.disconnect()

if __name__ == '__main__':
    asyncio.run(main())