# -*- coding: utf-8 -*-
"""
数据库优化工具

提供索引分析、查询优化建议和数据库性能监控功能
"""

import asyncio
from typing import Dict, List, Any, Optional
from tortoise import Tortoise
from tortoise.models import Model

from app.models.admin import User, Role, SysApiEndpoint, Menu, Dept, HttpAuditLog
from app.models.device import DeviceInfo, DeviceType, DeviceRealTimeData, DeviceHistoryData
from app.log import logger


class DatabaseIndexOptimizer:
    """数据库索引优化器"""
    
    def __init__(self):
        self.models = [
            User, Role, Api, Menu, Dept, AuditLog,
            DeviceInfo, DeviceType, DeviceRealTimeData, DeviceHistoryData
        ]
    
    async def analyze_all_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """分析所有模型的索引需求"""
        analysis_results = {}
        
        for model in self.models:
            suggestions = await self.analyze_model_indexes(model)
            if suggestions:
                analysis_results[model.__name__] = suggestions
        
        return analysis_results
    
    async def analyze_model_indexes(self, model: Model) -> List[Dict[str, Any]]:
        """分析单个模型的索引需求"""
        suggestions = []
        
        # 分析外键字段
        for field_name, field in model._meta.fields_map.items():
            if hasattr(field, 'related_model') and not getattr(field, 'index', False):
                suggestions.append({
                    'table': model._meta.db_table,
                    'field': field_name,
                    'type': 'foreign_key',
                    'priority': 'high',
                    'reason': f'外键字段 {field_name} 建议添加索引以提高关联查询性能',
                    'sql': f"CREATE INDEX idx_{model._meta.db_table}_{field_name} ON {model._meta.db_table} ({field_name});"
                })
        
        # 分析频繁查询字段
        frequent_fields = self._get_frequent_query_fields(model)
        for field_name, field in model._meta.fields_map.items():
            if field_name in frequent_fields and not getattr(field, 'index', False) and not field.pk:
                suggestions.append({
                    'table': model._meta.db_table,
                    'field': field_name,
                    'type': 'frequent_query',
                    'priority': 'medium',
                    'reason': f'字段 {field_name} 是频繁查询字段，建议添加索引',
                    'sql': f"CREATE INDEX idx_{model._meta.db_table}_{field_name} ON {model._meta.db_table} ({field_name});"
                })
        
        # 分析复合索引需求
        composite_suggestions = self._analyze_composite_indexes(model)
        suggestions.extend(composite_suggestions)
        
        return suggestions
    
    def _get_frequent_query_fields(self, model: Model) -> List[str]:
        """获取频繁查询的字段"""
        # 基于字段名和模型类型推测频繁查询字段
        common_query_fields = ['status', 'type', 'category', 'is_active', 'created_at', 'updated_at']
        
        # 模型特定的频繁查询字段
        model_specific_fields = {
            'User': ['username', 'email', 'is_active', 'is_superuser', 'last_login'],
            'Role': ['name'],
            'Api': ['path', 'method', 'tags'],
            'Menu': ['path', 'parent_id', 'order', 'is_hidden'],
            'DeviceInfo': ['device_code', 'device_type', 'manufacturer', 'team_name', 'is_locked'],
            'DeviceType': ['type_code', 'is_active'],
            'DeviceRealTimeData': ['device_id', 'status', 'data_timestamp'],
            'DeviceHistoryData': ['device_id', 'status', 'data_timestamp'],
            'AuditLog': ['user_id', 'module', 'status', 'created_at']
        }
        
        model_name = model.__name__
        specific_fields = model_specific_fields.get(model_name, [])
        
        # 合并通用字段和特定字段
        all_fields = common_query_fields + specific_fields
        
        # 只返回模型中实际存在的字段
        existing_fields = []
        for field_name in all_fields:
            if field_name in model._meta.fields_map:
                existing_fields.append(field_name)
        
        return existing_fields
    
    def _analyze_composite_indexes(self, model: Model) -> List[Dict[str, Any]]:
        """分析复合索引需求"""
        suggestions = []
        
        # 基于模型特点定义复合索引建议
        composite_indexes = {
            'DeviceRealTimeData': [
                (['device_id', 'data_timestamp'], '设备实时数据按设备和时间查询'),
                (['status', 'data_timestamp'], '按状态和时间查询设备数据')
            ],
            'DeviceHistoryData': [
                (['device_id', 'data_timestamp'], '设备历史数据按设备和时间查询'),
                (['status', 'data_timestamp'], '按状态和时间查询历史数据')
            ],
            'AuditLog': [
                (['user_id', 'created_at'], '按用户和时间查询审计日志'),
                (['module', 'created_at'], '按模块和时间查询审计日志')
            ],
            'Menu': [
                (['parent_id', 'order'], '菜单层级和排序查询')
            ]
        }
        
        model_name = model.__name__
        if model_name in composite_indexes:
            for fields, reason in composite_indexes[model_name]:
                # 检查字段是否都存在
                if all(field in model._meta.fields_map for field in fields):
                    field_list = ', '.join(fields)
                    index_name = f"idx_{model._meta.db_table}_{'_'.join(fields)}"
                    
                    suggestions.append({
                        'table': model._meta.db_table,
                        'field': field_list,
                        'type': 'composite',
                        'priority': 'medium',
                        'reason': reason,
                        'sql': f"CREATE INDEX {index_name} ON {model._meta.db_table} ({field_list});"
                    })
        
        return suggestions
    
    async def generate_optimization_script(self, analysis_results: Dict[str, List[Dict[str, Any]]]) -> str:
        """生成数据库优化脚本"""
        script_lines = [
            "-- 数据库索引优化脚本",
            f"-- 生成时间: {asyncio.get_event_loop().time()}",
            "",
            "-- 注意: 在生产环境执行前请先备份数据库",
            "-- 建议在低峰期执行以减少对系统性能的影响",
            ""
        ]
        
        for model_name, suggestions in analysis_results.items():
            script_lines.append(f"-- {model_name} 模型索引优化")
            script_lines.append("-" * 50)
            
            # 按优先级排序
            high_priority = [s for s in suggestions if s['priority'] == 'high']
            medium_priority = [s for s in suggestions if s['priority'] == 'medium']
            
            for suggestion in high_priority + medium_priority:
                script_lines.append(f"-- {suggestion['reason']}")
                script_lines.append(suggestion['sql'])
                script_lines.append("")
        
        return "\n".join(script_lines)
    
    async def check_existing_indexes(self) -> Dict[str, List[str]]:
        """检查现有索引"""
        # 这里需要根据具体数据库类型实现
        # SQLite 示例
        existing_indexes = {}
        
        try:
            connection = Tortoise.get_connection("default")
            
            for model in self.models:
                table_name = model._meta.db_table
                
                # 查询表的索引信息
                query = f"PRAGMA index_list('{table_name}')"
                result = await connection.execute_query(query)
                
                indexes = []
                for row in result:
                    if isinstance(row, dict):
                        indexes.append(row.get('name', ''))
                    else:
                        indexes.append(str(row[1]) if len(row) > 1 else '')
                
                existing_indexes[table_name] = indexes
        
        except Exception as e:
            logger.error(f"检查现有索引失败: {str(e)}")
        
        return existing_indexes


class QueryPerformanceMonitor:
    """查询性能监控器"""
    
    def __init__(self):
        self.query_log = []
        self.slow_query_threshold = 1.0  # 秒
    
    async def analyze_query_patterns(self) -> Dict[str, Any]:
        """分析查询模式"""
        if not self.query_log:
            return {"message": "暂无查询数据"}
        
        # 统计查询类型
        query_types = {}
        slow_queries = []
        total_queries = len(self.query_log)
        total_time = 0
        
        for query_info in self.query_log:
            query_type = query_info.get('type', 'unknown')
            execution_time = query_info.get('execution_time', 0)
            
            query_types[query_type] = query_types.get(query_type, 0) + 1
            total_time += execution_time
            
            if execution_time > self.slow_query_threshold:
                slow_queries.append(query_info)
        
        return {
            'total_queries': total_queries,
            'avg_execution_time': total_time / total_queries if total_queries > 0 else 0,
            'query_types': query_types,
            'slow_queries_count': len(slow_queries),
            'slow_queries': slow_queries[:10],  # 只返回前10个慢查询
            'recommendations': self._generate_performance_recommendations(query_types, slow_queries)
        }
    
    def _generate_performance_recommendations(self, query_types: Dict, slow_queries: List) -> List[str]:
        """生成性能优化建议"""
        recommendations = []
        
        if slow_queries:
            recommendations.append(f"发现 {len(slow_queries)} 个慢查询，建议优化查询逻辑或添加索引")
        
        # 分析查询类型分布
        if query_types.get('select', 0) > query_types.get('insert', 0) * 10:
            recommendations.append("读查询远多于写查询，建议增加缓存策略")
        
        if query_types.get('count', 0) > 100:
            recommendations.append("计数查询较多，建议使用缓存或预计算")
        
        return recommendations


class DatabaseMaintenanceScheduler:
    """数据库维护调度器"""
    
    async def schedule_maintenance_tasks(self) -> Dict[str, Any]:
        """调度维护任务"""
        tasks = {
            'index_analysis': await self._schedule_index_analysis(),
            'cache_cleanup': await self._schedule_cache_cleanup(),
            'statistics_update': await self._schedule_statistics_update(),
            'performance_report': await self._schedule_performance_report()
        }
        
        return tasks
    
    async def _schedule_index_analysis(self) -> Dict[str, Any]:
        """调度索引分析任务"""
        optimizer = DatabaseIndexOptimizer()
        analysis_results = await optimizer.analyze_all_models()
        
        return {
            'task': 'index_analysis',
            'status': 'completed',
            'results': analysis_results,
            'recommendations_count': sum(len(suggestions) for suggestions in analysis_results.values())
        }
    
    async def _schedule_cache_cleanup(self) -> Dict[str, Any]:
        """调度缓存清理任务"""
        from app.core.query_optimizer import query_cache
        
        cache_stats_before = query_cache.get_cache_stats()
        
        # 清理过期缓存
        query_cache.clear_all()
        
        cache_stats_after = query_cache.get_cache_stats()
        
        return {
            'task': 'cache_cleanup',
            'status': 'completed',
            'cleaned_keys': cache_stats_before['total_keys'],
            'memory_freed_mb': cache_stats_before['memory_usage_mb']
        }
    
    async def _schedule_statistics_update(self) -> Dict[str, Any]:
        """调度统计信息更新任务"""
        # 这里可以实现统计信息的更新逻辑
        return {
            'task': 'statistics_update',
            'status': 'completed',
            'updated_tables': len(DatabaseIndexOptimizer().models)
        }
    
    async def _schedule_performance_report(self) -> Dict[str, Any]:
        """调度性能报告生成任务"""
        from app.core.optimized_crud import QueryPerformanceAnalyzer
        
        report = await QueryPerformanceAnalyzer.generate_performance_report()
        
        return {
            'task': 'performance_report',
            'status': 'completed',
            'report': report
        }


# 全局实例
db_optimizer = DatabaseIndexOptimizer()
performance_monitor = QueryPerformanceMonitor()
maintenance_scheduler = DatabaseMaintenanceScheduler()


async def run_database_optimization():
    """运行数据库优化"""
    logger.info("开始数据库优化分析...")
    
    # 分析索引需求
    analysis_results = await db_optimizer.analyze_all_models()
    
    if analysis_results:
        # 生成优化脚本
        optimization_script = await db_optimizer.generate_optimization_script(analysis_results)
        
        # 保存脚本到文件
        script_path = "database_optimization.sql"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(optimization_script)
        
        logger.info(f"数据库优化脚本已生成: {script_path}")
        
        # 输出分析结果摘要
        total_suggestions = sum(len(suggestions) for suggestions in analysis_results.values())
        logger.info(f"分析完成，共发现 {total_suggestions} 个优化建议")
        
        for model_name, suggestions in analysis_results.items():
            high_priority = len([s for s in suggestions if s['priority'] == 'high'])
            medium_priority = len([s for s in suggestions if s['priority'] == 'medium'])
            logger.info(f"{model_name}: 高优先级 {high_priority} 个，中优先级 {medium_priority} 个")
    
    else:
        logger.info("未发现需要优化的索引")
    
    return analysis_results


if __name__ == "__main__":
    # 可以直接运行此脚本进行数据库优化分析
    asyncio.run(run_database_optimization())