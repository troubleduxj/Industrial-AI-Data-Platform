#!/usr/bin/env python3
"""
数据库查询性能监控系统
API权限重构项目 - 任务3.5
创建时间: 2025-01-10
"""

import asyncio
import asyncpg
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import statistics

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class QueryPerformanceMetric:
    """查询性能指标"""
    query_type: str
    query_text: str
    execution_time_ms: float
    rows_returned: int
    rows_examined: int
    index_used: bool
    timestamp: datetime
    user_id: Optional[int] = None
    api_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class PerformanceAlert:
    """性能告警"""
    alert_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    metric_value: float
    threshold: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

class DatabasePerformanceMonitor:
    """数据库性能监控器"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn: Optional[asyncpg.Connection] = None
        self.monitoring_active = False
        self.metrics_buffer: List[QueryPerformanceMetric] = []
        self.alerts_buffer: List[PerformanceAlert] = []
        
        # 性能阈值配置
        self.thresholds = {
            'slow_query_ms': 100,           # 慢查询阈值(毫秒)
            'very_slow_query_ms': 500,      # 非常慢查询阈值(毫秒)
            'high_rows_examined': 10000,    # 高扫描行数阈值
            'seq_scan_ratio': 0.8,          # 顺序扫描比例阈值
            'cache_hit_ratio': 0.95,        # 缓存命中率阈值
            'connection_usage': 0.8,        # 连接使用率阈值
        }
        
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
            
            # 创建监控相关表
            await self._create_monitoring_tables()
            
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    async def disconnect(self):
        """断开数据库连接"""
        if self.conn:
            await self.conn.close()
            logger.info("数据库连接已断开")
    
    async def _create_monitoring_tables(self):
        """创建监控相关表"""
        
        # 创建性能指标表
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS t_sys_performance_metrics (
                id BIGSERIAL PRIMARY KEY,
                query_type VARCHAR(50) NOT NULL,
                query_text TEXT,
                execution_time_ms NUMERIC(10,3) NOT NULL,
                rows_returned INTEGER DEFAULT 0,
                rows_examined INTEGER DEFAULT 0,
                index_used BOOLEAN DEFAULT FALSE,
                user_id BIGINT,
                api_path VARCHAR(500),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # 创建性能告警表
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS t_sys_performance_alerts (
                id BIGSERIAL PRIMARY KEY,
                alert_type VARCHAR(50) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                message TEXT NOT NULL,
                metric_value NUMERIC(15,3),
                threshold NUMERIC(15,3),
                is_resolved BOOLEAN DEFAULT FALSE,
                resolved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # 创建索引
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_performance_metrics_type_time 
            ON t_sys_performance_metrics(query_type, created_at DESC)
        """)
        
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_performance_alerts_severity_time 
            ON t_sys_performance_alerts(severity, created_at DESC) 
            WHERE is_resolved = FALSE
        """)
        
        logger.info("监控表创建完成")
    
    async def start_monitoring(self, interval_seconds: int = 60):
        """开始性能监控"""
        self.monitoring_active = True
        logger.info(f"开始性能监控，监控间隔: {interval_seconds}秒")
        
        while self.monitoring_active:
            try:
                # 收集性能指标
                await self._collect_performance_metrics()
                
                # 检查性能告警
                await self._check_performance_alerts()
                
                # 保存缓冲区数据
                await self._flush_buffers()
                
                # 等待下一个监控周期
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"监控过程中发生错误: {e}")
                await asyncio.sleep(interval_seconds)
    
    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring_active = False
        logger.info("性能监控已停止")
    
    async def _collect_performance_metrics(self):
        """收集性能指标"""
        
        # 1. 收集表统计信息
        await self._collect_table_stats()
        
        # 2. 收集索引使用统计
        await self._collect_index_stats()
        
        # 3. 收集慢查询信息
        await self._collect_slow_queries()
        
        # 4. 收集缓存命中率
        await self._collect_cache_stats()
        
        # 5. 收集连接统计
        await self._collect_connection_stats()
    
    async def _collect_table_stats(self):
        """收集表统计信息"""
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
                n_live_tup,
                n_dead_tup
            FROM pg_stat_user_tables 
            WHERE tablename = ANY($1)
        """
        
        rows = await self.conn.fetch(query, self.permission_tables)
        
        for row in rows:
            # 计算顺序扫描比例
            total_scans = (row['seq_scan'] or 0) + (row['idx_scan'] or 0)
            seq_scan_ratio = (row['seq_scan'] or 0) / max(total_scans, 1)
            
            # 记录指标
            metric = QueryPerformanceMetric(
                query_type='table_stats',
                query_text=f"Table: {row['tablename']}",
                execution_time_ms=0,
                rows_returned=row['n_live_tup'] or 0,
                rows_examined=row['seq_tup_read'] or 0,
                index_used=seq_scan_ratio < 0.5,
                timestamp=datetime.now()
            )
            self.metrics_buffer.append(metric)
            
            # 检查顺序扫描比例告警
            if seq_scan_ratio > self.thresholds['seq_scan_ratio'] and total_scans > 100:
                alert = PerformanceAlert(
                    alert_type='high_seq_scan_ratio',
                    severity='medium',
                    message=f"表 {row['tablename']} 顺序扫描比例过高: {seq_scan_ratio:.2%}",
                    metric_value=seq_scan_ratio,
                    threshold=self.thresholds['seq_scan_ratio'],
                    timestamp=datetime.now()
                )
                self.alerts_buffer.append(alert)
    
    async def _collect_index_stats(self):
        """收集索引使用统计"""
        query = """
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes 
            WHERE tablename = ANY($1)
            ORDER BY idx_scan DESC
        """
        
        rows = await self.conn.fetch(query, self.permission_tables)
        
        for row in rows:
            metric = QueryPerformanceMetric(
                query_type='index_stats',
                query_text=f"Index: {row['indexname']} on {row['tablename']}",
                execution_time_ms=0,
                rows_returned=row['idx_tup_fetch'] or 0,
                rows_examined=row['idx_tup_read'] or 0,
                index_used=True,
                timestamp=datetime.now()
            )
            self.metrics_buffer.append(metric)
    
    async def _collect_slow_queries(self):
        """收集慢查询信息（需要pg_stat_statements扩展）"""
        try:
            # 检查pg_stat_statements扩展是否可用
            extension_check = await self.conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
                )
            """)
            
            if not extension_check:
                logger.warning("pg_stat_statements扩展未安装，跳过慢查询收集")
                return
            
            query = """
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows,
                    shared_blks_hit,
                    shared_blks_read
                FROM pg_stat_statements 
                WHERE query ILIKE ANY(ARRAY['%t_sys_%', '%permission%', '%api%'])
                  AND mean_time > $1
                ORDER BY mean_time DESC
                LIMIT 20
            """
            
            rows = await self.conn.fetch(query, self.thresholds['slow_query_ms'])
            
            for row in rows:
                # 计算缓存命中率
                total_blocks = (row['shared_blks_hit'] or 0) + (row['shared_blks_read'] or 0)
                cache_hit_ratio = (row['shared_blks_hit'] or 0) / max(total_blocks, 1)
                
                metric = QueryPerformanceMetric(
                    query_type='slow_query',
                    query_text=row['query'][:500],  # 截断长查询
                    execution_time_ms=row['mean_time'],
                    rows_returned=row['rows'] or 0,
                    rows_examined=0,
                    index_used=cache_hit_ratio > 0.8,
                    timestamp=datetime.now()
                )
                self.metrics_buffer.append(metric)
                
                # 检查慢查询告警
                if row['mean_time'] > self.thresholds['very_slow_query_ms']:
                    alert = PerformanceAlert(
                        alert_type='very_slow_query',
                        severity='high',
                        message=f"发现非常慢的查询，平均执行时间: {row['mean_time']:.2f}ms",
                        metric_value=row['mean_time'],
                        threshold=self.thresholds['very_slow_query_ms'],
                        timestamp=datetime.now()
                    )
                    self.alerts_buffer.append(alert)
                    
        except Exception as e:
            logger.warning(f"收集慢查询信息失败: {e}")
    
    async def _collect_cache_stats(self):
        """收集缓存统计信息"""
        query = """
            SELECT 
                sum(heap_blks_read) as heap_read,
                sum(heap_blks_hit) as heap_hit,
                sum(idx_blks_read) as idx_read,
                sum(idx_blks_hit) as idx_hit
            FROM pg_statio_user_tables 
            WHERE relname = ANY($1)
        """
        
        row = await self.conn.fetchrow(query, self.permission_tables)
        
        if row:
            total_heap = (row['heap_read'] or 0) + (row['heap_hit'] or 0)
            total_idx = (row['idx_read'] or 0) + (row['idx_hit'] or 0)
            
            heap_hit_ratio = (row['heap_hit'] or 0) / max(total_heap, 1)
            idx_hit_ratio = (row['idx_hit'] or 0) / max(total_idx, 1)
            
            # 记录堆缓存命中率
            metric = QueryPerformanceMetric(
                query_type='cache_stats',
                query_text='Heap cache hit ratio',
                execution_time_ms=0,
                rows_returned=0,
                rows_examined=0,
                index_used=True,
                timestamp=datetime.now()
            )
            self.metrics_buffer.append(metric)
            
            # 检查缓存命中率告警
            if heap_hit_ratio < self.thresholds['cache_hit_ratio'] and total_heap > 1000:
                alert = PerformanceAlert(
                    alert_type='low_cache_hit_ratio',
                    severity='medium',
                    message=f"堆缓存命中率过低: {heap_hit_ratio:.2%}",
                    metric_value=heap_hit_ratio,
                    threshold=self.thresholds['cache_hit_ratio'],
                    timestamp=datetime.now()
                )
                self.alerts_buffer.append(alert)
    
    async def _collect_connection_stats(self):
        """收集连接统计信息"""
        query = """
            SELECT 
                count(*) as total_connections,
                count(*) FILTER (WHERE state = 'active') as active_connections,
                count(*) FILTER (WHERE state = 'idle') as idle_connections,
                max(setting::int) as max_connections
            FROM pg_stat_activity, pg_settings 
            WHERE pg_settings.name = 'max_connections'
        """
        
        row = await self.conn.fetchrow(query)
        
        if row:
            connection_usage = row['total_connections'] / max(row['max_connections'], 1)
            
            metric = QueryPerformanceMetric(
                query_type='connection_stats',
                query_text=f"Connections: {row['total_connections']}/{row['max_connections']}",
                execution_time_ms=0,
                rows_returned=row['total_connections'],
                rows_examined=0,
                index_used=True,
                timestamp=datetime.now()
            )
            self.metrics_buffer.append(metric)
            
            # 检查连接使用率告警
            if connection_usage > self.thresholds['connection_usage']:
                alert = PerformanceAlert(
                    alert_type='high_connection_usage',
                    severity='high',
                    message=f"数据库连接使用率过高: {connection_usage:.2%}",
                    metric_value=connection_usage,
                    threshold=self.thresholds['connection_usage'],
                    timestamp=datetime.now()
                )
                self.alerts_buffer.append(alert)
    
    async def _check_performance_alerts(self):
        """检查性能告警"""
        # 这里可以添加更多自定义的性能检查逻辑
        pass
    
    async def _flush_buffers(self):
        """保存缓冲区数据到数据库"""
        
        # 保存性能指标
        if self.metrics_buffer:
            metrics_data = [
                (
                    m.query_type, m.query_text, m.execution_time_ms,
                    m.rows_returned, m.rows_examined, m.index_used,
                    m.user_id, m.api_path, m.timestamp
                )
                for m in self.metrics_buffer
            ]
            
            await self.conn.executemany("""
                INSERT INTO t_sys_performance_metrics 
                (query_type, query_text, execution_time_ms, rows_returned, 
                 rows_examined, index_used, user_id, api_path, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, metrics_data)
            
            logger.info(f"保存了 {len(self.metrics_buffer)} 条性能指标")
            self.metrics_buffer.clear()
        
        # 保存性能告警
        if self.alerts_buffer:
            alerts_data = [
                (
                    a.alert_type, a.severity, a.message,
                    a.metric_value, a.threshold, a.timestamp
                )
                for a in self.alerts_buffer
            ]
            
            await self.conn.executemany("""
                INSERT INTO t_sys_performance_alerts 
                (alert_type, severity, message, metric_value, threshold, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, alerts_data)
            
            logger.warning(f"生成了 {len(self.alerts_buffer)} 条性能告警")
            self.alerts_buffer.clear()
    
    async def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """获取性能报告"""
        since = datetime.now() - timedelta(hours=hours)
        
        # 查询性能指标统计
        metrics_query = """
            SELECT 
                query_type,
                COUNT(*) as count,
                AVG(execution_time_ms) as avg_time,
                MIN(execution_time_ms) as min_time,
                MAX(execution_time_ms) as max_time,
                AVG(rows_returned) as avg_rows_returned,
                AVG(rows_examined) as avg_rows_examined
            FROM t_sys_performance_metrics 
            WHERE created_at >= $1
            GROUP BY query_type
            ORDER BY avg_time DESC
        """
        
        metrics = await self.conn.fetch(metrics_query, since)
        
        # 查询告警统计
        alerts_query = """
            SELECT 
                alert_type,
                severity,
                COUNT(*) as count,
                MAX(created_at) as last_occurrence
            FROM t_sys_performance_alerts 
            WHERE created_at >= $1
            GROUP BY alert_type, severity
            ORDER BY count DESC
        """
        
        alerts = await self.conn.fetch(alerts_query, since)
        
        # 查询最慢的查询
        slow_queries_query = """
            SELECT 
                query_text,
                execution_time_ms,
                rows_returned,
                rows_examined,
                created_at
            FROM t_sys_performance_metrics 
            WHERE created_at >= $1 
              AND query_type = 'slow_query'
            ORDER BY execution_time_ms DESC
            LIMIT 10
        """
        
        slow_queries = await self.conn.fetch(slow_queries_query, since)
        
        return {
            'report_period_hours': hours,
            'generated_at': datetime.now().isoformat(),
            'metrics_summary': [dict(row) for row in metrics],
            'alerts_summary': [dict(row) for row in alerts],
            'slowest_queries': [dict(row) for row in slow_queries],
            'total_metrics': sum(row['count'] for row in metrics),
            'total_alerts': sum(row['count'] for row in alerts)
        }
    
    async def test_permission_query_performance(self, test_user_id: int = 1, iterations: int = 100):
        """测试权限查询性能"""
        logger.info(f"开始权限查询性能测试，用户ID: {test_user_id}, 迭代次数: {iterations}")
        
        test_results = {}
        
        # 测试1: 单个权限检查
        times = []
        for _ in range(iterations):
            start_time = time.time()
            result = await self.conn.fetchval(
                "SELECT check_user_permission($1, $2)",
                test_user_id, 'GET /api/v2/users'
            )
            end_time = time.time()
            times.append((end_time - start_time) * 1000)
        
        test_results['single_permission_check'] = {
            'avg_time_ms': statistics.mean(times),
            'min_time_ms': min(times),
            'max_time_ms': max(times),
            'median_time_ms': statistics.median(times),
            'std_dev_ms': statistics.stdev(times) if len(times) > 1 else 0
        }
        
        # 测试2: API权限检查
        times = []
        for _ in range(iterations):
            start_time = time.time()
            result = await self.conn.fetchval(
                "SELECT check_api_permission($1, $2, $3)",
                test_user_id, '/api/v2/users', 'GET'
            )
            end_time = time.time()
            times.append((end_time - start_time) * 1000)
        
        test_results['api_permission_check'] = {
            'avg_time_ms': statistics.mean(times),
            'min_time_ms': min(times),
            'max_time_ms': max(times),
            'median_time_ms': statistics.median(times),
            'std_dev_ms': statistics.stdev(times) if len(times) > 1 else 0
        }
        
        # 测试3: 批量权限检查
        times = []
        permission_codes = ['GET /api/v2/users', 'POST /api/v2/users', 'PUT /api/v2/users/{id}']
        for _ in range(iterations):
            start_time = time.time()
            result = await self.conn.fetch(
                "SELECT * FROM check_user_permissions_batch($1, $2)",
                test_user_id, permission_codes
            )
            end_time = time.time()
            times.append((end_time - start_time) * 1000)
        
        test_results['batch_permission_check'] = {
            'avg_time_ms': statistics.mean(times),
            'min_time_ms': min(times),
            'max_time_ms': max(times),
            'median_time_ms': statistics.median(times),
            'std_dev_ms': statistics.stdev(times) if len(times) > 1 else 0
        }
        
        logger.info("权限查询性能测试完成")
        return test_results

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库性能监控')
    parser.add_argument('--db-url', required=True, help='数据库连接URL')
    parser.add_argument('--action', choices=['monitor', 'report', 'test'], 
                       default='monitor', help='执行的操作')
    parser.add_argument('--interval', type=int, default=60, help='监控间隔(秒)')
    parser.add_argument('--hours', type=int, default=24, help='报告时间范围(小时)')
    parser.add_argument('--test-user', type=int, default=1, help='测试用户ID')
    parser.add_argument('--iterations', type=int, default=100, help='测试迭代次数')
    
    args = parser.parse_args()
    
    monitor = DatabasePerformanceMonitor(args.db_url)
    
    try:
        await monitor.connect()
        
        if args.action == 'monitor':
            print(f"开始性能监控，间隔: {args.interval}秒")
            print("按 Ctrl+C 停止监控")
            await monitor.start_monitoring(args.interval)
            
        elif args.action == 'report':
            report = await monitor.get_performance_report(args.hours)
            print(json.dumps(report, indent=2, ensure_ascii=False))
            
        elif args.action == 'test':
            results = await monitor.test_permission_query_performance(
                args.test_user, args.iterations
            )
            print(json.dumps(results, indent=2, ensure_ascii=False))
            
    except KeyboardInterrupt:
        print("\n监控已停止")
    except Exception as e:
        logger.error(f"执行失败: {e}")
    finally:
        await monitor.disconnect()

if __name__ == '__main__':
    asyncio.run(main())