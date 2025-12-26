"""
数据库审计工具
用于分析数据库表使用情况，识别未使用的表和孤立数据
"""

import os
import re
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from tortoise import Tortoise
from tortoise.connection import connections
from tortoise.exceptions import OperationalError

logger = logging.getLogger(__name__)


class DatabaseAuditor:
    """数据库审计器"""
    
    def __init__(self):
        self.unused_tables = []
        self.orphaned_data = []
        self.table_usage_info = {}
        self.code_references = {}
        self.project_root = Path(__file__).parent.parent
        
    async def analyze_table_usage(self) -> Dict[str, Any]:
        """分析数据库表使用情况"""
        logger.info("开始分析数据库表使用情况...")
        
        try:
            # 获取所有表
            tables = await self.get_all_tables()
            logger.info(f"发现 {len(tables)} 个数据库表")
            
            # 分析每个表的使用情况
            for table in tables:
                logger.info(f"分析表: {table}")
                usage_info = await self.check_table_usage(table)
                self.table_usage_info[table] = usage_info
                
                if not usage_info['is_used']:
                    self.unused_tables.append({
                        'table_name': table,
                        'last_modified': usage_info['last_modified'],
                        'record_count': usage_info['record_count'],
                        'references': usage_info['references'],
                        'code_references': usage_info['code_references']
                    })
            
            # 检查孤立数据
            await self.check_orphaned_data()
            
            return {
                'total_tables': len(tables),
                'unused_tables': len(self.unused_tables),
                'orphaned_data_issues': len(self.orphaned_data),
                'table_usage_info': self.table_usage_info,
                'unused_tables_detail': self.unused_tables,
                'orphaned_data_detail': self.orphaned_data
            }
            
        except Exception as e:
            logger.error(f"分析数据库表使用情况时出错: {e}")
            raise
    
    async def get_all_tables(self) -> List[str]:
        """获取数据库中所有表"""
        try:
            conn = connections.get("postgres")
            
            # PostgreSQL查询所有表
            query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
            
            result = await conn.execute_query(query)
            return [row[0] for row in result[1]]
            
        except Exception as e:
            logger.error(f"获取数据库表列表时出错: {e}")
            # 如果是SQLite，尝试SQLite语法
            try:
                query = """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
                result = await conn.execute_query(query)
                return [row[0] for row in result[1]]
            except Exception as sqlite_e:
                logger.error(f"SQLite查询也失败: {sqlite_e}")
                raise e
    
    async def check_table_usage(self, table_name: str) -> Dict[str, Any]:
        """检查表的使用情况"""
        try:
            # 检查代码中是否引用该表
            code_references = self.scan_code_references(table_name)
            
            # 检查表的记录数量
            record_count = await self.get_table_record_count(table_name)
            
            # 检查表的最后修改时间（如果有时间戳字段）
            last_modified = await self.get_table_last_modified(table_name)
            
            # 检查外键关系
            foreign_key_refs = await self.get_foreign_key_references(table_name)
            
            # 判断表是否被使用
            is_used = (
                len(code_references) > 0 or  # 代码中有引用
                record_count > 0 or          # 有数据记录
                len(foreign_key_refs) > 0    # 有外键关系
            )
            
            return {
                'is_used': is_used,
                'code_references': code_references,
                'last_modified': last_modified,
                'record_count': record_count,
                'references': foreign_key_refs,
                'analysis_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"检查表 {table_name} 使用情况时出错: {e}")
            return {
                'is_used': True,  # 出错时保守处理，认为表被使用
                'code_references': [],
                'last_modified': None,
                'record_count': 0,
                'references': [],
                'error': str(e),
                'analysis_time': datetime.now().isoformat()
            }
    
    def scan_code_references(self, table_name: str) -> List[str]:
        """扫描代码中对表的引用"""
        references = []
        
        try:
            # 扫描的目录列表
            scan_dirs = ['app', 'scripts', 'database']
            
            for scan_dir in scan_dirs:
                scan_path = self.project_root / scan_dir
                if not scan_path.exists():
                    continue
                    
                # 递归扫描Python文件
                for file_path in scan_path.rglob('*.py'):
                    if self._check_file_references_table(file_path, table_name):
                        references.append(str(file_path.relative_to(self.project_root)))
            
            # 扫描SQL文件
            for sql_file in self.project_root.rglob('*.sql'):
                if self._check_file_references_table(sql_file, table_name):
                    references.append(str(sql_file.relative_to(self.project_root)))
                    
        except Exception as e:
            logger.error(f"扫描代码引用时出错: {e}")
        
        return references
    
    def _check_file_references_table(self, file_path: Path, table_name: str) -> bool:
        """检查文件是否引用了指定的表"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # 查找表名引用的模式
                patterns = [
                    # 直接表名引用
                    rf'\b{re.escape(table_name)}\b',
                    # 字符串中的表名
                    rf'["\'{table_name}["\']',
                    # Meta类中的table定义
                    rf'table\s*=\s*["\'{table_name}["\']',
                    # SQL查询中的表名
                    rf'FROM\s+{re.escape(table_name)}\b',
                    rf'JOIN\s+{re.escape(table_name)}\b',
                    rf'UPDATE\s+{re.escape(table_name)}\b',
                    rf'INSERT\s+INTO\s+{re.escape(table_name)}\b',
                    rf'DELETE\s+FROM\s+{re.escape(table_name)}\b',
                ]
                
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        return True
                        
                return False
                
        except Exception as e:
            logger.warning(f"读取文件 {file_path} 时出错: {e}")
            return False
    
    async def get_table_record_count(self, table_name: str) -> int:
        """获取表的记录数量"""
        try:
            conn = connections.get("postgres")
            query = f"SELECT COUNT(*) FROM {table_name}"
            result = await conn.execute_query(query)
            return result[1][0][0] if result[1] else 0
        except Exception as e:
            logger.warning(f"获取表 {table_name} 记录数量时出错: {e}")
            return 0
    
    async def get_table_last_modified(self, table_name: str) -> Optional[str]:
        """获取表的最后修改时间"""
        try:
            conn = connections.get("postgres")
            
            # 尝试查找常见的时间戳字段
            timestamp_fields = ['updated_at', 'modified_at', 'last_modified', 'created_at']
            
            for field in timestamp_fields:
                try:
                    query = f"SELECT MAX({field}) FROM {table_name}"
                    result = await conn.execute_query(query)
                    if result[1] and result[1][0][0]:
                        return result[1][0][0].isoformat() if hasattr(result[1][0][0], 'isoformat') else str(result[1][0][0])
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"获取表 {table_name} 最后修改时间时出错: {e}")
            return None
    
    async def get_foreign_key_references(self, table_name: str) -> List[Dict[str, str]]:
        """获取表的外键关系"""
        try:
            conn = connections.get("postgres")
            
            # PostgreSQL查询外键关系
            query = """
            SELECT 
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND (tc.table_name = %s OR ccu.table_name = %s)
            """
            
            result = await conn.execute_query(query, [table_name, table_name])
            
            references = []
            for row in result[1]:
                references.append({
                    'constraint_name': row[0],
                    'table_name': row[1],
                    'column_name': row[2],
                    'foreign_table_name': row[3],
                    'foreign_column_name': row[4]
                })
            
            return references
            
        except Exception as e:
            logger.warning(f"获取表 {table_name} 外键关系时出错: {e}")
            return []
    
    async def check_orphaned_data(self):
        """检查孤立数据"""
        logger.info("检查孤立数据...")
        
        # 定义需要检查的外键关系
        foreign_key_checks = [
            {
                'name': '用户角色关联检查',
                'child_table': 'user_role',
                'child_column': 'user_id',
                'parent_table': 'user',
                'parent_column': 'id'
            },
            {
                'name': '角色菜单关联检查',
                'child_table': 'role_menu',
                'child_column': 'role_id',
                'parent_table': 'role',
                'parent_column': 'id'
            },
            {
                'name': '角色API关联检查',
                'child_table': 'role_api',
                'child_column': 'role_id',
                'parent_table': 'role',
                'parent_column': 'id'
            },
            {
                'name': '设备实时数据关联检查',
                'child_table': 't_device_realtime_data',
                'child_column': 'device_id',
                'parent_table': 't_device_info',
                'parent_column': 'id'
            },
            {
                'name': '设备历史数据关联检查',
                'child_table': 't_device_history_data',
                'child_column': 'device_id',
                'parent_table': 't_device_info',
                'parent_column': 'id'
            }
        ]
        
        for check in foreign_key_checks:
            try:
                orphaned_count = await self._check_orphaned_records(check)
                if orphaned_count > 0:
                    self.orphaned_data.append({
                        'check_name': check['name'],
                        'child_table': check['child_table'],
                        'orphaned_count': orphaned_count,
                        'description': f"表 {check['child_table']} 中有 {orphaned_count} 条记录的 {check['child_column']} 在父表 {check['parent_table']} 中不存在"
                    })
            except Exception as e:
                logger.warning(f"检查 {check['name']} 时出错: {e}")
    
    async def _check_orphaned_records(self, check: Dict[str, str]) -> int:
        """检查孤立记录数量"""
        try:
            conn = connections.get("postgres")
            
            query = f"""
            SELECT COUNT(*) 
            FROM {check['child_table']} 
            WHERE {check['child_column']} NOT IN (
                SELECT {check['parent_column']} 
                FROM {check['parent_table']} 
                WHERE {check['parent_column']} IS NOT NULL
            )
            """
            
            result = await conn.execute_query(query)
            return result[1][0][0] if result[1] else 0
            
        except Exception as e:
            logger.warning(f"检查孤立记录时出错: {e}")
            return 0
    
    def generate_audit_report(self, output_file: str = None) -> str:
        """生成审计报告"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"database_audit_report_{timestamp}.md"
        
        report_content = self._build_report_content()
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"审计报告已生成: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"生成审计报告时出错: {e}")
            raise
    
    def _build_report_content(self) -> str:
        """构建报告内容"""
        report = []
        report.append("# 数据库审计报告")
        report.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"\n## 概览")
        report.append(f"- 总表数: {len(self.table_usage_info)}")
        report.append(f"- 未使用表数: {len(self.unused_tables)}")
        report.append(f"- 孤立数据问题: {len(self.orphaned_data)}")
        
        # 未使用的表
        if self.unused_tables:
            report.append(f"\n## 未使用的表 ({len(self.unused_tables)})")
            for table in self.unused_tables:
                report.append(f"\n### {table['table_name']}")
                report.append(f"- 记录数: {table['record_count']}")
                report.append(f"- 最后修改: {table['last_modified'] or '未知'}")
                report.append(f"- 代码引用: {len(table['code_references'])} 个文件")
                if table['code_references']:
                    for ref in table['code_references']:
                        report.append(f"  - {ref}")
        
        # 孤立数据
        if self.orphaned_data:
            report.append(f"\n## 孤立数据问题 ({len(self.orphaned_data)})")
            for issue in self.orphaned_data:
                report.append(f"\n### {issue['check_name']}")
                report.append(f"- 表: {issue['child_table']}")
                report.append(f"- 孤立记录数: {issue['orphaned_count']}")
                report.append(f"- 描述: {issue['description']}")
        
        # 表使用情况详情
        report.append(f"\n## 所有表使用情况")
        for table_name, info in self.table_usage_info.items():
            status = "✅ 使用中" if info['is_used'] else "❌ 未使用"
            report.append(f"\n### {table_name} {status}")
            report.append(f"- 记录数: {info['record_count']}")
            report.append(f"- 代码引用: {len(info['code_references'])} 个文件")
            report.append(f"- 外键关系: {len(info['references'])} 个")
            if info.get('error'):
                report.append(f"- ⚠️ 分析错误: {info['error']}")
        
        return "\n".join(report)


class CodeReferenceScanner:
    """代码引用扫描器"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.scan_patterns = {
            'model_class': r'class\s+(\w+)\s*\([^)]*Model[^)]*\)',
            'table_meta': r'table\s*=\s*["\']([^"\']+)["\']',
            'sql_table': r'(?:FROM|JOIN|UPDATE|INSERT\s+INTO|DELETE\s+FROM)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            'string_reference': r'["\']([a-zA-Z_][a-zA-Z0-9_]*)["\']'
        }
    
    def scan_all_references(self) -> Dict[str, List[str]]:
        """扫描所有代码引用"""
        references = {}
        
        # 扫描Python文件
        for py_file in self.project_root.rglob('*.py'):
            file_refs = self.scan_file_references(py_file)
            if file_refs:
                references[str(py_file.relative_to(self.project_root))] = file_refs
        
        # 扫描SQL文件
        for sql_file in self.project_root.rglob('*.sql'):
            file_refs = self.scan_file_references(sql_file)
            if file_refs:
                references[str(sql_file.relative_to(self.project_root))] = file_refs
        
        return references
    
    def scan_file_references(self, file_path: Path) -> List[str]:
        """扫描单个文件的引用"""
        references = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                for pattern_name, pattern in self.scan_patterns.items():
                    matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        if isinstance(match, tuple):
                            references.extend(match)
                        else:
                            references.append(match)
                            
        except Exception as e:
            logger.warning(f"扫描文件 {file_path} 时出错: {e}")
        
        return list(set(references))  # 去重


# 使用示例和测试函数
async def run_database_audit():
    """运行数据库审计"""
    from app.settings.config import settings
    
    # 初始化Tortoise ORM
    await Tortoise.init(config=settings.TORTOISE_ORM)
    
    try:
        auditor = DatabaseAuditor()
        
        # 执行审计
        audit_results = await auditor.analyze_table_usage()
        
        # 生成报告
        report_file = auditor.generate_audit_report()
        
        print(f"数据库审计完成!")
        print(f"总表数: {audit_results['total_tables']}")
        print(f"未使用表数: {audit_results['unused_tables']}")
        print(f"孤立数据问题: {audit_results['orphaned_data_issues']}")
        print(f"详细报告: {report_file}")
        
        return audit_results
        
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(run_database_audit())