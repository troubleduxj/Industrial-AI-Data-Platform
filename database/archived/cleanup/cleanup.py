"""
数据库清理脚本
提供安全的数据库清理功能，包括表删除、孤立数据清理和备份机制
"""

import os
import asyncio
import logging
import shutil
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from tortoise import Tortoise
from tortoise.connection import connections
from tortoise.exceptions import OperationalError

from .audit import DatabaseAuditor

logger = logging.getLogger(__name__)


class DatabaseCleaner:
    """数据库清理器"""
    
    def __init__(self, backup_dir: str = None):
        self.backup_dir = Path(backup_dir) if backup_dir else Path("backup") / f"database_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.cleanup_log = []
        
    async def create_full_backup(self) -> str:
        """创建完整数据库备份"""
        logger.info("创建完整数据库备份...")
        
        try:
            backup_file = self.backup_dir / f"full_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
            
            # 使用pg_dump创建备份（如果是PostgreSQL）
            conn = connections.get("postgres")
            
            # 获取数据库连接信息
            from app.settings.config import settings
            db_config = settings.tortoise_orm.connections.postgres.credentials
            
            # 构建pg_dump命令
            dump_command = [
                "pg_dump",
                f"--host={db_config.host}",
                f"--port={db_config.port}",
                f"--username={db_config.user}",
                f"--dbname={db_config.database}",
                "--no-password",
                "--verbose",
                "--clean",
                "--no-acl",
                "--no-owner",
                f"--file={backup_file}"
            ]
            
            # 设置密码环境变量
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config.password
            
            import subprocess
            result = subprocess.run(dump_command, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"数据库备份成功: {backup_file}")
                self.cleanup_log.append({
                    'action': 'full_backup',
                    'status': 'success',
                    'file': str(backup_file),
                    'timestamp': datetime.now().isoformat()
                })
                return str(backup_file)
            else:
                logger.error(f"数据库备份失败: {result.stderr}")
                raise Exception(f"备份失败: {result.stderr}")
                
        except Exception as e:
            logger.error(f"创建数据库备份时出错: {e}")
            # 如果pg_dump失败，尝试使用SQL导出
            return await self._create_sql_backup()
    
    async def _create_sql_backup(self) -> str:
        """使用SQL语句创建备份"""
        logger.info("使用SQL语句创建备份...")
        
        backup_file = self.backup_dir / f"sql_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        try:
            conn = connections.get("postgres")
            
            # 获取所有表
            auditor = DatabaseAuditor()
            tables = await auditor.get_all_tables()
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(f"-- 数据库备份文件\n")
                f.write(f"-- 生成时间: {datetime.now().isoformat()}\n\n")
                
                for table in tables:
                    try:
                        # 导出表结构
                        f.write(f"-- 表结构: {table}\n")
                        
                        # 导出数据
                        query = f"SELECT * FROM {table}"
                        result = await conn.execute_query(query)
                        
                        if result[1]:  # 如果有数据
                            # 获取列名
                            columns_query = f"""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = '{table}' 
                            ORDER BY ordinal_position
                            """
                            columns_result = await conn.execute_query(columns_query)
                            columns = [row[0] for row in columns_result[1]]
                            
                            f.write(f"-- 数据: {table}\n")
                            for row in result[1]:
                                values = []
                                for value in row:
                                    if value is None:
                                        values.append('NULL')
                                    elif isinstance(value, str):
                                        escaped_value = value.replace("'", "''")
                                        values.append(f"'{escaped_value}'")
                                    else:
                                        values.append(str(value))
                                
                                f.write(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)});\n")
                        
                        f.write(f"\n")
                        
                    except Exception as table_error:
                        logger.warning(f"备份表 {table} 时出错: {table_error}")
                        f.write(f"-- 备份表 {table} 时出错: {table_error}\n\n")
            
            logger.info(f"SQL备份创建成功: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            logger.error(f"创建SQL备份时出错: {e}")
            raise
    
    async def create_table_backup(self, table_name: str) -> str:
        """创建单个表的备份"""
        logger.info(f"创建表 {table_name} 的备份...")
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"{table_name}_{timestamp}.sql"
            
            conn = connections.get("postgres")
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(f"-- 表备份: {table_name}\n")
                f.write(f"-- 生成时间: {datetime.now().isoformat()}\n\n")
                
                # 获取表结构
                try:
                    structure_query = f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    ORDER BY ordinal_position
                    """
                    structure_result = await conn.execute_query(structure_query)
                    
                    f.write(f"-- 表结构信息\n")
                    for row in structure_result[1]:
                        f.write(f"-- {row[0]}: {row[1]} {'NULL' if row[2] == 'YES' else 'NOT NULL'} {row[3] or ''}\n")
                    f.write(f"\n")
                    
                except Exception as e:
                    f.write(f"-- 获取表结构失败: {e}\n\n")
                
                # 导出数据
                try:
                    data_query = f"SELECT * FROM {table_name}"
                    data_result = await conn.execute_query(data_query)
                    
                    if data_result[1]:
                        # 获取列名
                        columns_query = f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = '{table_name}' 
                        ORDER BY ordinal_position
                        """
                        columns_result = await conn.execute_query(columns_query)
                        columns = [row[0] for row in columns_result[1]]
                        
                        f.write(f"-- 数据记录 ({len(data_result[1])} 条)\n")
                        for row in data_result[1]:
                            values = []
                            for value in row:
                                if value is None:
                                    values.append('NULL')
                                elif isinstance(value, str):
                                    escaped_value = value.replace("'", "''")
                                    values.append(f"'{escaped_value}'")
                                elif isinstance(value, datetime):
                                    values.append(f"'{value.isoformat()}'")
                                else:
                                    values.append(str(value))
                            
                            f.write(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});\n")
                    else:
                        f.write(f"-- 表 {table_name} 无数据\n")
                        
                except Exception as e:
                    f.write(f"-- 导出数据失败: {e}\n")
            
            logger.info(f"表 {table_name} 备份完成: {backup_file}")
            self.cleanup_log.append({
                'action': 'table_backup',
                'table': table_name,
                'status': 'success',
                'file': str(backup_file),
                'timestamp': datetime.now().isoformat()
            })
            
            return str(backup_file)
            
        except Exception as e:
            logger.error(f"备份表 {table_name} 时出错: {e}")
            self.cleanup_log.append({
                'action': 'table_backup',
                'table': table_name,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            raise
    
    async def safe_drop_table(self, table_name: str, force: bool = False) -> bool:
        """安全删除表"""
        logger.info(f"准备删除表: {table_name}")
        
        try:
            if not force:
                # 创建备份
                backup_file = await self.create_table_backup(table_name)
                logger.info(f"表 {table_name} 已备份到 {backup_file}")
                
                # 检查外键约束
                foreign_keys = await self._get_foreign_key_constraints(table_name)
                if foreign_keys:
                    logger.warning(f"表 {table_name} 存在外键约束: {foreign_keys}")
                    if not force:
                        raise Exception(f"表 {table_name} 存在外键约束，无法安全删除: {foreign_keys}")
            
            # 删除表
            conn = connections.get("postgres")
            await conn.execute_query(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            
            logger.info(f"表 {table_name} 已删除")
            self.cleanup_log.append({
                'action': 'drop_table',
                'table': table_name,
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"删除表 {table_name} 时出错: {e}")
            self.cleanup_log.append({
                'action': 'drop_table',
                'table': table_name,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            return False
    
    async def _get_foreign_key_constraints(self, table_name: str) -> List[Dict[str, str]]:
        """获取表的外键约束"""
        try:
            conn = connections.get("postgres")
            
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
            AND tc.table_name = %s
            """
            
            result = await conn.execute_query(query, [table_name])
            
            constraints = []
            for row in result[1]:
                constraints.append({
                    'constraint_name': row[0],
                    'table_name': row[1],
                    'column_name': row[2],
                    'foreign_table_name': row[3],
                    'foreign_column_name': row[4]
                })
            
            return constraints
            
        except Exception as e:
            logger.warning(f"获取表 {table_name} 外键约束时出错: {e}")
            return []
    
    async def cleanup_orphaned_data(self) -> Dict[str, int]:
        """清理孤立数据"""
        logger.info("开始清理孤立数据...")
        
        cleanup_results = {}
        
        # 定义需要清理的孤立数据检查
        orphaned_data_checks = [
            {
                'name': '用户角色关联',
                'query': """
                DELETE FROM user_role 
                WHERE user_id NOT IN (SELECT id FROM "user" WHERE id IS NOT NULL)
                """,
                'description': '删除不存在用户的角色关联'
            },
            {
                'name': '角色菜单关联',
                'query': """
                DELETE FROM role_menu 
                WHERE role_id NOT IN (SELECT id FROM role WHERE id IS NOT NULL)
                """,
                'description': '删除不存在角色的菜单关联'
            },
            {
                'name': '角色API关联',
                'query': """
                DELETE FROM role_api 
                WHERE role_id NOT IN (SELECT id FROM role WHERE id IS NOT NULL)
                """,
                'description': '删除不存在角色的API关联'
            },
            {
                'name': '设备实时数据',
                'query': """
                DELETE FROM t_device_realtime_data 
                WHERE device_id NOT IN (SELECT id FROM t_device_info WHERE id IS NOT NULL)
                """,
                'description': '删除不存在设备的实时数据'
            },
            {
                'name': '设备历史数据',
                'query': """
                DELETE FROM t_device_history_data 
                WHERE device_id NOT IN (SELECT id FROM t_device_info WHERE id IS NOT NULL)
                """,
                'description': '删除不存在设备的历史数据'
            },
            {
                'name': '部门闭包表',
                'query': """
                DELETE FROM dept_closure 
                WHERE ancestor_id NOT IN (SELECT id FROM dept WHERE id IS NOT NULL)
                OR descendant_id NOT IN (SELECT id FROM dept WHERE id IS NOT NULL)
                """,
                'description': '删除不存在部门的闭包关系'
            }
        ]
        
        conn = connections.get("postgres")
        
        for check in orphaned_data_checks:
            try:
                logger.info(f"清理 {check['name']}...")
                
                # 先检查有多少孤立数据
                count_query = check['query'].replace('DELETE FROM', 'SELECT COUNT(*) FROM')
                count_result = await conn.execute_query(count_query)
                orphaned_count = count_result[1][0][0] if count_result[1] else 0
                
                if orphaned_count > 0:
                    # 执行清理
                    await conn.execute_query(check['query'])
                    logger.info(f"{check['name']} 清理完成: 删除了 {orphaned_count} 条孤立记录")
                    
                    cleanup_results[check['name']] = orphaned_count
                    self.cleanup_log.append({
                        'action': 'cleanup_orphaned_data',
                        'check_name': check['name'],
                        'deleted_count': orphaned_count,
                        'status': 'success',
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    logger.info(f"{check['name']}: 没有发现孤立数据")
                    cleanup_results[check['name']] = 0
                    
            except Exception as e:
                logger.error(f"清理 {check['name']} 时出错: {e}")
                cleanup_results[check['name']] = -1
                self.cleanup_log.append({
                    'action': 'cleanup_orphaned_data',
                    'check_name': check['name'],
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return cleanup_results
    
    async def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """清理旧数据"""
        logger.info(f"清理 {days_to_keep} 天前的旧数据...")
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleanup_results = {}
        
        # 定义需要清理旧数据的表
        old_data_checks = [
            {
                'name': '审计日志',
                'table': 'auditlog',
                'date_column': 'created_at',
                'description': f'删除 {days_to_keep} 天前的审计日志'
            },
            {
                'name': '设备历史数据',
                'table': 't_device_history_data',
                'date_column': 'created_at',
                'description': f'删除 {days_to_keep} 天前的设备历史数据'
            },
            {
                'name': '焊接报警历史',
                'table': 't_welding_alarm_his',
                'date_column': 'created_at',
                'description': f'删除 {days_to_keep} 天前的焊接报警历史'
            }
        ]
        
        conn = connections.get("postgres")
        
        for check in old_data_checks:
            try:
                logger.info(f"清理 {check['name']}...")
                
                # 先检查有多少旧数据
                count_query = f"""
                SELECT COUNT(*) FROM {check['table']} 
                WHERE {check['date_column']} < %s
                """
                count_result = await conn.execute_query(count_query, [cutoff_date])
                old_count = count_result[1][0][0] if count_result[1] else 0
                
                if old_count > 0:
                    # 执行清理
                    delete_query = f"""
                    DELETE FROM {check['table']} 
                    WHERE {check['date_column']} < %s
                    """
                    await conn.execute_query(delete_query, [cutoff_date])
                    
                    logger.info(f"{check['name']} 清理完成: 删除了 {old_count} 条旧记录")
                    cleanup_results[check['name']] = old_count
                    
                    self.cleanup_log.append({
                        'action': 'cleanup_old_data',
                        'table': check['table'],
                        'deleted_count': old_count,
                        'cutoff_date': cutoff_date.isoformat(),
                        'status': 'success',
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    logger.info(f"{check['name']}: 没有发现需要清理的旧数据")
                    cleanup_results[check['name']] = 0
                    
            except Exception as e:
                logger.error(f"清理 {check['name']} 时出错: {e}")
                cleanup_results[check['name']] = -1
                self.cleanup_log.append({
                    'action': 'cleanup_old_data',
                    'table': check['table'],
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return cleanup_results
    
    def save_cleanup_log(self) -> str:
        """保存清理日志"""
        log_file = self.backup_dir / f"cleanup_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'cleanup_time': datetime.now().isoformat(),
                    'backup_dir': str(self.backup_dir),
                    'operations': self.cleanup_log
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"清理日志已保存: {log_file}")
            return str(log_file)
            
        except Exception as e:
            logger.error(f"保存清理日志时出错: {e}")
            raise


class DatabaseMigrationCleaner:
    """数据库迁移清理器"""
    
    def __init__(self):
        self.auditor = DatabaseAuditor()
        self.cleaner = DatabaseCleaner()
        
    async def generate_cleanup_migration(self, migration_name: str = None) -> str:
        """生成清理迁移脚本"""
        if not migration_name:
            migration_name = f"cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info("生成数据库清理迁移脚本...")
        
        # 分析未使用的表
        audit_results = await self.auditor.analyze_table_usage()
        
        # 生成迁移脚本内容
        migration_content = self._generate_migration_content(audit_results, migration_name)
        
        # 创建迁移文件
        migrations_dir = Path("migrations")
        migrations_dir.mkdir(exist_ok=True)
        
        migration_file = migrations_dir / f"{migration_name}.py"
        
        with open(migration_file, 'w', encoding='utf-8') as f:
            f.write(migration_content)
        
        logger.info(f"清理迁移文件已生成: {migration_file}")
        return str(migration_file)
    
    def _generate_migration_content(self, audit_results: Dict[str, Any], migration_name: str) -> str:
        """生成迁移内容"""
        unused_tables = audit_results.get('unused_tables_detail', [])
        orphaned_data = audit_results.get('orphaned_data_detail', [])
        
        content = f'''"""
数据库清理迁移: {migration_name}
生成时间: {datetime.now().isoformat()}

此迁移将执行以下操作:
- 删除未使用的表: {len(unused_tables)} 个
- 清理孤立数据: {len(orphaned_data)} 个问题

警告: 执行前请确保已创建数据库备份!
"""

from tortoise import BaseDBAsyncClient
import logging

logger = logging.getLogger(__name__)


async def upgrade(db: BaseDBAsyncClient) -> str:
    """数据库清理升级脚本"""
    operations = []
    
    try:
        # 清理孤立数据
        logger.info("开始清理孤立数据...")
'''
        
        # 添加孤立数据清理
        for issue in orphaned_data:
            content += f'''
        # 清理 {issue['check_name']}
        try:
            result = await db.execute_query("""
                DELETE FROM {issue['child_table']} 
                WHERE {issue['child_table'].split('_')[-1]}_id NOT IN (
                    SELECT id FROM {issue['child_table'].replace('_' + issue['child_table'].split('_')[-1], '')} 
                    WHERE id IS NOT NULL
                )
            """)
            operations.append(f"清理 {issue['check_name']}: 删除了孤立记录")
            logger.info(f"清理 {issue['check_name']} 完成")
        except Exception as e:
            logger.error(f"清理 {issue['check_name']} 失败: {{e}}")
            operations.append(f"清理 {issue['check_name']} 失败: {{e}}")
'''
        
        # 添加未使用表删除
        content += f'''
        
        # 删除未使用的表
        logger.info("开始删除未使用的表...")
'''
        
        for table in unused_tables:
            content += f'''
        # 删除未使用的表: {table['table_name']}
        # 记录数: {table['record_count']}, 代码引用: {len(table['code_references'])}
        try:
            await db.execute_query("DROP TABLE IF EXISTS {table['table_name']} CASCADE")
            operations.append("删除表: {table['table_name']}")
            logger.info("删除表 {table['table_name']} 完成")
        except Exception as e:
            logger.error(f"删除表 {table['table_name']} 失败: {{e}}")
            operations.append(f"删除表 {table['table_name']} 失败: {{e}}")
'''
        
        content += f'''
        
        return "数据库清理完成: " + "; ".join(operations)
        
    except Exception as e:
        logger.error(f"数据库清理过程中出错: {{e}}")
        return f"数据库清理失败: {{e}}"


async def downgrade(db: BaseDBAsyncClient) -> str:
    """回滚脚本"""
    # 注意: 数据删除操作无法自动回滚
    # 如需恢复，请从备份文件手动恢复
    
    logger.warning("数据库清理操作无法自动回滚")
    logger.warning("如需恢复数据，请从备份文件手动恢复")
    
    return "清理操作无法自动回滚，请从备份手动恢复"
'''
        
        return content


# 使用示例和测试函数
async def run_database_cleanup(
    create_backup: bool = True,
    cleanup_orphaned: bool = True,
    cleanup_old_data: bool = False,
    old_data_days: int = 90,
    drop_unused_tables: bool = False
):
    """运行数据库清理"""
    from app.settings.config import settings
    
    # 初始化Tortoise ORM
    await Tortoise.init(config=settings.TORTOISE_ORM)
    
    try:
        cleaner = DatabaseCleaner()
        results = {}
        
        # 创建备份
        if create_backup:
            logger.info("创建数据库备份...")
            backup_file = await cleaner.create_full_backup()
            results['backup_file'] = backup_file
        
        # 清理孤立数据
        if cleanup_orphaned:
            logger.info("清理孤立数据...")
            orphaned_results = await cleaner.cleanup_orphaned_data()
            results['orphaned_cleanup'] = orphaned_results
        
        # 清理旧数据
        if cleanup_old_data:
            logger.info(f"清理 {old_data_days} 天前的旧数据...")
            old_data_results = await cleaner.cleanup_old_data(old_data_days)
            results['old_data_cleanup'] = old_data_results
        
        # 删除未使用的表（需要先进行审计）
        if drop_unused_tables:
            logger.info("分析并删除未使用的表...")
            auditor = DatabaseAuditor()
            audit_results = await auditor.analyze_table_usage()
            
            dropped_tables = []
            for table_info in audit_results['unused_tables_detail']:
                table_name = table_info['table_name']
                if table_info['record_count'] == 0 and len(table_info['code_references']) == 0:
                    success = await cleaner.safe_drop_table(table_name)
                    if success:
                        dropped_tables.append(table_name)
            
            results['dropped_tables'] = dropped_tables
        
        # 保存清理日志
        log_file = cleaner.save_cleanup_log()
        results['log_file'] = log_file
        
        logger.info("数据库清理完成!")
        return results
        
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    # 示例用法
    asyncio.run(run_database_cleanup(
        create_backup=True,
        cleanup_orphaned=True,
        cleanup_old_data=False,
        drop_unused_tables=False
    ))