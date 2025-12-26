#!/usr/bin/env python3
"""
数据库性能优化执行脚本
API权限重构项目 - 任务3.5
创建时间: 2025-01-10
"""

import asyncio
import asyncpg
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceOptimizationExecutor:
    """性能优化执行器"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn: Optional[asyncpg.Connection] = None
        self.execution_log = []
        
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
    
    async def execute_full_optimization(self):
        """执行完整的性能优化"""
        logger.info("🚀 开始执行数据库性能优化")
        
        try:
            # 1. 创建核心索引
            await self._execute_core_indexes()
            
            # 2. 执行查询优化
            await self._execute_query_optimization()
            
            # 3. 设置监控
            await self._setup_monitoring()
            
            # 4. 执行性能测试
            await self._run_performance_tests()
            
            # 5. 生成优化报告
            await self._generate_optimization_report()
            
            logger.info("✅ 数据库性能优化完成")
            
        except Exception as e:
            logger.error(f"❌ 性能优化执行失败: {e}")
            raise
    
    async def _execute_core_indexes(self):
        """执行核心索引创建"""
        logger.info("📊 创建权限查询核心索引...")
        
        # 读取索引创建脚本
        index_script_path = Path(__file__).parent / "performance_optimization_indexes_simple.sql"
        
        if not index_script_path.exists():
            logger.error(f"索引脚本文件不存在: {index_script_path}")
            return
        
        try:
            with open(index_script_path, 'r', encoding='utf-8') as f:
                index_sql = f.read()
            
            # 执行索引创建脚本
            await self.conn.execute(index_sql)
            
            self.execution_log.append({
                'step': 'create_indexes',
                'status': 'success',
                'message': '核心索引创建完成',
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info("✅ 核心索引创建完成")
            
        except Exception as e:
            error_msg = f"索引创建失败: {e}"
            logger.error(error_msg)
            self.execution_log.append({
                'step': 'create_indexes',
                'status': 'error',
                'message': error_msg,
                'timestamp': datetime.now().isoformat()
            })
            raise
    
    async def _execute_query_optimization(self):
        """执行查询优化"""
        logger.info("🔍 执行查询优化...")
        
        # 读取查询优化脚本
        query_script_path = Path(__file__).parent / "performance_optimization_queries_minimal.sql"
        
        if not query_script_path.exists():
            logger.error(f"查询优化脚本文件不存在: {query_script_path}")
            return
        
        try:
            with open(query_script_path, 'r', encoding='utf-8') as f:
                query_sql = f.read()
            
            # 执行查询优化脚本
            await self.conn.execute(query_sql)
            
            self.execution_log.append({
                'step': 'optimize_queries',
                'status': 'success',
                'message': '查询优化完成',
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info("✅ 查询优化完成")
            
        except Exception as e:
            error_msg = f"查询优化失败: {e}"
            logger.error(error_msg)
            self.execution_log.append({
                'step': 'optimize_queries',
                'status': 'error',
                'message': error_msg,
                'timestamp': datetime.now().isoformat()
            })
            raise
    
    async def _setup_monitoring(self):
        """设置性能监控"""
        logger.info("📈 设置性能监控...")
        
        try:
            # 创建监控表
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
            
            # 创建监控索引
            await self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_performance_metrics_type_time 
                ON t_sys_performance_metrics(query_type, created_at DESC)
            """)
            
            await self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_performance_alerts_severity_time 
                ON t_sys_performance_alerts(severity, created_at DESC) 
                WHERE is_resolved = FALSE
            """)
            
            self.execution_log.append({
                'step': 'setup_monitoring',
                'status': 'success',
                'message': '性能监控设置完成',
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info("✅ 性能监控设置完成")
            
        except Exception as e:
            error_msg = f"监控设置失败: {e}"
            logger.error(error_msg)
            self.execution_log.append({
                'step': 'setup_monitoring',
                'status': 'error',
                'message': error_msg,
                'timestamp': datetime.now().isoformat()
            })
            raise
    
    async def _run_performance_tests(self):
        """运行性能测试"""
        logger.info("🧪 运行性能测试...")
        
        try:
            # 检查权限验证函数是否存在
            function_exists = await self.conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_proc 
                    WHERE proname = 'check_user_permission'
                )
            """)
            
            if not function_exists:
                logger.warning("权限验证函数不存在，跳过性能测试")
                return
            
            # 运行性能测试
            test_results = await self.conn.fetch("""
                SELECT * FROM test_permission_query_performance(1, 100)
            """)
            
            # 记录测试结果
            test_summary = {}
            for result in test_results:
                test_summary[result['test_name']] = {
                    'avg_time_ms': float(result['avg_time_ms']),
                    'min_time_ms': float(result['min_time_ms']),
                    'max_time_ms': float(result['max_time_ms']),
                    'total_time_ms': float(result['total_time_ms'])
                }
            
            self.execution_log.append({
                'step': 'performance_tests',
                'status': 'success',
                'message': '性能测试完成',
                'test_results': test_summary,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info("✅ 性能测试完成")
            
            # 输出测试结果
            print("\n📊 性能测试结果:")
            for test_name, metrics in test_summary.items():
                print(f"  {test_name}:")
                print(f"    平均时间: {metrics['avg_time_ms']:.2f}ms")
                print(f"    最小时间: {metrics['min_time_ms']:.2f}ms")
                print(f"    最大时间: {metrics['max_time_ms']:.2f}ms")
            
        except Exception as e:
            error_msg = f"性能测试失败: {e}"
            logger.error(error_msg)
            self.execution_log.append({
                'step': 'performance_tests',
                'status': 'error',
                'message': error_msg,
                'timestamp': datetime.now().isoformat()
            })
            # 性能测试失败不应该阻止整个优化过程
            logger.warning("性能测试失败，但继续执行其他优化步骤")
    
    async def _generate_optimization_report(self):
        """生成优化报告"""
        logger.info("📋 生成优化报告...")
        
        try:
            # 收集优化后的统计信息
            table_stats = await self.conn.fetch("""
                SELECT 
                    tablename,
                    seq_scan,
                    seq_tup_read,
                    idx_scan,
                    idx_tup_fetch,
                    n_live_tup,
                    n_dead_tup,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size
                FROM pg_stat_user_tables 
                WHERE tablename IN ('t_sys_api_endpoints', 't_sys_user_permissions', 't_sys_role_permissions')
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """)
            
            index_stats = await self.conn.fetch("""
                SELECT 
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch,
                    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
                FROM pg_stat_user_indexes 
                WHERE tablename IN ('t_sys_api_endpoints', 't_sys_user_permissions', 't_sys_role_permissions')
                ORDER BY idx_scan DESC
            """)
            
            # 生成报告
            report = {
                'optimization_completed_at': datetime.now().isoformat(),
                'execution_log': self.execution_log,
                'post_optimization_stats': {
                    'table_statistics': [dict(row) for row in table_stats],
                    'index_statistics': [dict(row) for row in index_stats]
                },
                'summary': {
                    'total_steps': len(self.execution_log),
                    'successful_steps': len([log for log in self.execution_log if log['status'] == 'success']),
                    'failed_steps': len([log for log in self.execution_log if log['status'] == 'error'])
                }
            }
            
            # 保存报告到文件
            report_dir = Path("reports")
            report_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = report_dir / f"performance_optimization_execution_{timestamp}.json"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"✅ 优化报告已保存: {report_path}")
            
            # 输出执行摘要
            print(f"\n📋 优化执行摘要:")
            print(f"  总步骤数: {report['summary']['total_steps']}")
            print(f"  成功步骤: {report['summary']['successful_steps']}")
            print(f"  失败步骤: {report['summary']['failed_steps']}")
            print(f"  报告文件: {report_path}")
            
        except Exception as e:
            error_msg = f"报告生成失败: {e}"
            logger.error(error_msg)
            self.execution_log.append({
                'step': 'generate_report',
                'status': 'error',
                'message': error_msg,
                'timestamp': datetime.now().isoformat()
            })
    
    async def verify_optimization_results(self):
        """验证优化结果"""
        logger.info("🔍 验证优化结果...")
        
        try:
            # 检查索引是否创建成功
            indexes = await self.conn.fetch("""
                SELECT 
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE tablename IN ('t_sys_api_endpoints', 't_sys_user_permissions', 't_sys_role_permissions')
                  AND indexname LIKE 'idx_%'
                ORDER BY tablename, indexname
            """)
            
            print(f"\n📊 优化结果验证:")
            print(f"  创建的索引数量: {len(indexes)}")
            
            # 按表分组显示索引
            table_indexes = {}
            for index in indexes:
                table_name = index['tablename']
                if table_name not in table_indexes:
                    table_indexes[table_name] = []
                table_indexes[table_name].append(index['indexname'])
            
            for table_name, index_list in table_indexes.items():
                print(f"  {table_name}: {len(index_list)} 个索引")
                for index_name in index_list:
                    print(f"    - {index_name}")
            
            # 检查函数是否创建成功
            functions = await self.conn.fetch("""
                SELECT 
                    proname,
                    prosrc
                FROM pg_proc 
                WHERE proname LIKE '%permission%'
                  AND proname IN ('check_user_permission', 'check_role_permission', 'check_api_permission')
            """)
            
            print(f"  创建的函数数量: {len(functions)}")
            for func in functions:
                print(f"    - {func['proname']}")
            
            # 检查监控表是否创建成功
            monitoring_tables = await self.conn.fetch("""
                SELECT 
                    tablename
                FROM pg_tables 
                WHERE tablename IN ('t_sys_performance_metrics', 't_sys_performance_alerts')
            """)
            
            print(f"  创建的监控表数量: {len(monitoring_tables)}")
            for table in monitoring_tables:
                print(f"    - {table['tablename']}")
            
            return True
            
        except Exception as e:
            logger.error(f"验证优化结果失败: {e}")
            return False

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库性能优化执行器')
    parser.add_argument('--db-url', required=True, help='数据库连接URL')
    parser.add_argument('--action', choices=['optimize', 'verify', 'both'], 
                       default='both', help='执行的操作')
    parser.add_argument('--skip-tests', action='store_true', help='跳过性能测试')
    
    args = parser.parse_args()
    
    executor = PerformanceOptimizationExecutor(args.db_url)
    
    try:
        await executor.connect()
        
        if args.action in ['optimize', 'both']:
            print("🚀 开始执行数据库性能优化...")
            await executor.execute_full_optimization()
            print("✅ 性能优化执行完成")
        
        if args.action in ['verify', 'both']:
            print("\n🔍 验证优化结果...")
            success = await executor.verify_optimization_results()
            if success:
                print("✅ 优化结果验证通过")
            else:
                print("❌ 优化结果验证失败")
                sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n⏹️ 操作被用户中断")
    except Exception as e:
        logger.error(f"❌ 执行失败: {e}")
        sys.exit(1)
    finally:
        await executor.disconnect()

if __name__ == '__main__':
    asyncio.run(main())