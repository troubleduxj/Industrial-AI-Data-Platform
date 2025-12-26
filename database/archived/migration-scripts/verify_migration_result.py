#!/usr/bin/env python3
"""
验证数据库迁移结果的脚本
"""
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List

# 设置数据库连接
os.environ['DATABASE_URL'] = 'postgresql://postgres:Hanatech%40123@127.0.0.1:5432/devicemonitor'

class MigrationVerifier:
    """迁移结果验证器"""
    
    def __init__(self):
        self.db_url = os.environ['DATABASE_URL']
        self.conn = None
        self.verification_results = {}
    
    async def connect(self):
        """连接数据库"""
        try:
            import asyncpg
            self.conn = await asyncpg.connect(self.db_url)
            print("✅ 数据库连接成功")
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
    
    async def disconnect(self):
        """断开数据库连接"""
        if self.conn:
            await self.conn.close()
            print("✅ 数据库连接已关闭")
    
    def print_banner(self):
        """打印横幅"""
        banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                 🔍 数据库迁移结果验证                        ║
║              Database Migration Verification               ║
╠══════════════════════════════════════════════════════════════╣
║  验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                           ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    async def verify_table_structure(self):
        """验证表结构"""
        print("🏗️ 验证表结构...")
        
        expected_tables = [
            't_sys_config', 't_sys_dict_type', 't_sys_dict_data',
            't_sys_dept', 't_sys_user', 't_sys_role', 't_sys_user_role',
            't_sys_menu', 't_sys_role_menu', 't_sys_api_groups',
            't_sys_api_endpoints', 't_sys_permission', 't_sys_role_permission',
            't_sys_user_permission', 't_sys_migration_logs'
        ]
        
        existing_tables = []
        missing_tables = []
        
        for table in expected_tables:
            exists = await self.conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = $1
                )
            """, table)
            
            if exists:
                existing_tables.append(table)
                print(f"  ✅ {table}")
            else:
                missing_tables.append(table)
                print(f"  ❌ {table} (缺失)")
        
        self.verification_results['table_structure'] = {
            'expected_count': len(expected_tables),
            'existing_count': len(existing_tables),
            'missing_count': len(missing_tables),
            'existing_tables': existing_tables,
            'missing_tables': missing_tables,
            'success': len(missing_tables) == 0
        }
        
        print(f"📊 表结构验证: {len(existing_tables)}/{len(expected_tables)} 成功")
        return len(missing_tables) == 0
    
    async def verify_data_migration(self):
        """验证数据迁移"""
        print("📦 验证数据迁移...")
        
        data_checks = []
        
        # 检查各表的数据量
        tables_to_check = [
            't_sys_dept', 't_sys_user', 't_sys_role', 't_sys_user_role',
            't_sys_menu', 't_sys_role_menu', 't_sys_api_groups',
            't_sys_api_endpoints', 't_sys_permission'
        ]
        
        for table in tables_to_check:
            try:
                count = await self.conn.fetchval(f'SELECT COUNT(*) FROM {table}')
                data_checks.append({
                    'table': table,
                    'count': count,
                    'status': 'success'
                })
                print(f"  ✅ {table}: {count} 条记录")
            except Exception as e:
                data_checks.append({
                    'table': table,
                    'count': 0,
                    'status': 'error',
                    'error': str(e)
                })
                print(f"  ❌ {table}: 查询失败 - {e}")
        
        # 检查关键数据完整性
        integrity_checks = []
        
        # 检查用户角色关联完整性
        try:
            orphaned_user_roles = await self.conn.fetchval("""
                SELECT COUNT(*) FROM t_sys_user_role ur
                LEFT JOIN t_sys_user u ON ur.user_id = u.id
                LEFT JOIN t_sys_role r ON ur.role_id = r.id
                WHERE u.id IS NULL OR r.id IS NULL
            """)
            
            integrity_checks.append({
                'check': 'user_role_integrity',
                'orphaned_count': orphaned_user_roles,
                'status': 'success' if orphaned_user_roles == 0 else 'warning'
            })
            
            if orphaned_user_roles == 0:
                print("  ✅ 用户角色关联完整性检查通过")
            else:
                print(f"  ⚠️ 发现 {orphaned_user_roles} 条孤立的用户角色关联")
                
        except Exception as e:
            integrity_checks.append({
                'check': 'user_role_integrity',
                'status': 'error',
                'error': str(e)
            })
            print(f"  ❌ 用户角色关联完整性检查失败: {e}")
        
        # 检查API端点权限映射
        try:
            api_without_permission = await self.conn.fetchval("""
                SELECT COUNT(*) FROM t_sys_api_endpoints
                WHERE permission_code IS NULL OR permission_code = ''
            """)
            
            integrity_checks.append({
                'check': 'api_permission_mapping',
                'unmapped_count': api_without_permission,
                'status': 'success' if api_without_permission == 0 else 'warning'
            })
            
            if api_without_permission == 0:
                print("  ✅ API权限映射检查通过")
            else:
                print(f"  ⚠️ 发现 {api_without_permission} 个API端点未映射权限")
                
        except Exception as e:
            integrity_checks.append({
                'check': 'api_permission_mapping',
                'status': 'error',
                'error': str(e)
            })
            print(f"  ❌ API权限映射检查失败: {e}")
        
        self.verification_results['data_migration'] = {
            'table_data': data_checks,
            'integrity_checks': integrity_checks,
            'success': all(check['status'] != 'error' for check in data_checks + integrity_checks)
        }
        
        success_count = sum(1 for check in data_checks if check['status'] == 'success')
        print(f"📊 数据迁移验证: {success_count}/{len(data_checks)} 表成功")
        
        return self.verification_results['data_migration']['success']
    
    async def verify_indexes_and_constraints(self):
        """验证索引和约束"""
        print("🔍 验证索引和约束...")
        
        # 检查重要索引
        important_indexes = [
            'idx_api_endpoints_code', 'idx_api_endpoints_path', 'idx_api_endpoints_method',
            'idx_permission_code', 'idx_user_username', 'idx_role_key'
        ]
        
        existing_indexes = []
        missing_indexes = []
        
        for index in important_indexes:
            exists = await self.conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM pg_indexes 
                    WHERE schemaname = 'public' AND indexname = $1
                )
            """, index)
            
            if exists:
                existing_indexes.append(index)
                print(f"  ✅ {index}")
            else:
                missing_indexes.append(index)
                print(f"  ❌ {index} (缺失)")
        
        # 检查外键约束
        foreign_keys = await self.conn.fetch("""
            SELECT 
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
                AND tc.table_name LIKE 't_sys_%'
            ORDER BY tc.table_name, tc.constraint_name
        """)
        
        print(f"  📋 发现 {len(foreign_keys)} 个外键约束")
        for fk in foreign_keys:
            print(f"    🔗 {fk['table_name']}.{fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}")
        
        self.verification_results['indexes_constraints'] = {
            'expected_indexes': len(important_indexes),
            'existing_indexes': len(existing_indexes),
            'missing_indexes': missing_indexes,
            'foreign_keys_count': len(foreign_keys),
            'foreign_keys': [dict(fk) for fk in foreign_keys],
            'success': len(missing_indexes) == 0
        }
        
        print(f"📊 索引验证: {len(existing_indexes)}/{len(important_indexes)} 成功")
        return len(missing_indexes) == 0
    
    async def verify_migration_logs(self):
        """验证迁移日志"""
        print("📝 验证迁移日志...")
        
        try:
            # 获取迁移日志统计
            log_stats = await self.conn.fetch("""
                SELECT 
                    migration_type,
                    status,
                    COUNT(*) as count,
                    AVG(execution_time_ms) as avg_execution_time
                FROM t_sys_migration_logs
                WHERE created_at >= CURRENT_DATE
                GROUP BY migration_type, status
                ORDER BY migration_type, status
            """)
            
            # 获取最近的迁移记录
            recent_migrations = await self.conn.fetch("""
                SELECT migration_name, migration_type, status, execution_time_ms, executed_at
                FROM t_sys_migration_logs
                WHERE created_at >= CURRENT_DATE
                ORDER BY executed_at DESC
                LIMIT 10
            """)
            
            print("  📊 迁移日志统计:")
            for stat in log_stats:
                print(f"    {stat['migration_type']}.{stat['status']}: {stat['count']} 条 "
                      f"(平均耗时: {stat['avg_execution_time']:.0f}ms)")
            
            print("  📋 最近迁移记录:")
            for migration in recent_migrations:
                status_icon = "✅" if migration['status'] == 'success' else "❌"
                print(f"    {status_icon} {migration['migration_name']} "
                      f"({migration['execution_time_ms']}ms)")
            
            self.verification_results['migration_logs'] = {
                'log_statistics': [dict(stat) for stat in log_stats],
                'recent_migrations': [dict(migration) for migration in recent_migrations],
                'success': True
            }
            
            return True
            
        except Exception as e:
            print(f"  ❌ 迁移日志验证失败: {e}")
            self.verification_results['migration_logs'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    async def generate_verification_report(self):
        """生成验证报告"""
        print("📊 生成验证报告...")
        
        # 计算总体成功率
        all_checks = [
            self.verification_results.get('table_structure', {}).get('success', False),
            self.verification_results.get('data_migration', {}).get('success', False),
            self.verification_results.get('indexes_constraints', {}).get('success', False),
            self.verification_results.get('migration_logs', {}).get('success', False)
        ]
        
        success_rate = sum(all_checks) / len(all_checks) * 100
        
        report = {
            'verification_time': datetime.now().isoformat(),
            'overall_success_rate': success_rate,
            'verification_results': self.verification_results,
            'summary': {
                'table_structure': self.verification_results.get('table_structure', {}).get('success', False),
                'data_migration': self.verification_results.get('data_migration', {}).get('success', False),
                'indexes_constraints': self.verification_results.get('indexes_constraints', {}).get('success', False),
                'migration_logs': self.verification_results.get('migration_logs', {}).get('success', False)
            }
        }
        
        # 保存报告
        report_file = f"migration_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📋 验证报告已生成: {report_file}")
        
        # 打印摘要
        print("\n" + "="*60)
        print("📊 验证摘要报告")
        print("="*60)
        print(f"总体成功率: {success_rate:.1f}%")
        print(f"表结构验证: {'✅ 通过' if report['summary']['table_structure'] else '❌ 失败'}")
        print(f"数据迁移验证: {'✅ 通过' if report['summary']['data_migration'] else '❌ 失败'}")
        print(f"索引约束验证: {'✅ 通过' if report['summary']['indexes_constraints'] else '❌ 失败'}")
        print(f"迁移日志验证: {'✅ 通过' if report['summary']['migration_logs'] else '❌ 失败'}")
        print("="*60)
        
        return success_rate >= 75  # 75%以上认为验证通过
    
    async def run_verification(self):
        """运行完整验证"""
        self.print_banner()
        
        try:
            # 连接数据库
            if not await self.connect():
                return False
            
            # 执行各项验证
            verification_tasks = [
                self.verify_table_structure(),
                self.verify_data_migration(),
                self.verify_indexes_and_constraints(),
                self.verify_migration_logs()
            ]
            
            results = []
            for task in verification_tasks:
                try:
                    result = await task
                    results.append(result)
                except Exception as e:
                    print(f"❌ 验证任务失败: {e}")
                    results.append(False)
            
            # 生成验证报告
            overall_success = await self.generate_verification_report()
            
            if overall_success:
                print("\n🎉 数据库迁移验证通过！")
                return True
            else:
                print("\n⚠️ 数据库迁移验证存在问题，请检查报告详情")
                return False
            
        except Exception as e:
            print(f"❌ 验证过程中发生错误: {e}")
            return False
        
        finally:
            await self.disconnect()

async def main():
    """主函数"""
    verifier = MigrationVerifier()
    success = await verifier.run_verification()
    
    if success:
        print("\n✅ 验证完成，迁移结果良好！")
        return 0
    else:
        print("\n❌ 验证发现问题，请检查详细报告！")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)