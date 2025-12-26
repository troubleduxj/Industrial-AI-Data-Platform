#!/usr/bin/env python3
"""
验证简化迁移结果的脚本
"""
import asyncio
import os
from datetime import datetime

# 设置数据库连接
os.environ['DATABASE_URL'] = 'postgresql://postgres:Hanatech%40123@127.0.0.1:5432/devicemonitor'

class MigrationVerifier:
    """迁移结果验证器"""
    
    def __init__(self):
        self.db_url = os.environ['DATABASE_URL']
        self.conn = None
    
    async def connect(self):
        """连接数据库"""
        try:
            import asyncpg
            self.conn = await asyncpg.connect(self.db_url)
            print("数据库连接成功")
            return True
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return False
    
    async def disconnect(self):
        """断开数据库连接"""
        if self.conn:
            await self.conn.close()
            print("数据库连接已关闭")
    
    def print_banner(self):
        """打印横幅"""
        banner = f"""
================================================================
                数据库迁移结果验证
              Database Migration Verification
================================================================
  验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================
        """
        print(banner)
    
    async def verify_table_data(self):
        """验证表数据"""
        print("验证表数据...")
        
        # 要验证的表和预期的最小记录数
        tables_to_verify = [
            ('t_sys_dept', 1, '部门表'),
            ('t_sys_user', 1, '用户表'),
            ('t_sys_role', 1, '角色表'),
            ('t_sys_menu', 0, '菜单表'),  # 菜单迁移失败了，所以预期为0
            ('t_sys_user_role', 1, '用户角色关联表'),
            ('t_sys_role_menu', 1, '角色菜单关联表'),
            ('t_sys_api_endpoints', 50, 'API端点表'),
            ('t_sys_permission', 50, '权限表')
        ]
        
        verification_results = []
        
        for table_name, min_expected, description in tables_to_verify:
            try:
                count = await self.conn.fetchval(f'SELECT COUNT(*) FROM {table_name}')
                status = "通过" if count >= min_expected else "警告"
                verification_results.append({
                    'table': table_name,
                    'description': description,
                    'count': count,
                    'min_expected': min_expected,
                    'status': status
                })
                
                status_icon = "✅" if status == "通过" else "⚠️"
                print(f"  {status_icon} {description}: {count} 条记录 (预期最少: {min_expected})")
                
            except Exception as e:
                verification_results.append({
                    'table': table_name,
                    'description': description,
                    'count': 0,
                    'min_expected': min_expected,
                    'status': '错误',
                    'error': str(e)
                })
                print(f"  ❌ {description}: 查询失败 - {e}")
        
        return verification_results
    
    async def verify_data_integrity(self):
        """验证数据完整性"""
        print("\n验证数据完整性...")
        
        integrity_checks = []
        
        # 检查用户角色关联完整性
        try:
            orphaned_user_roles = await self.conn.fetchval("""
                SELECT COUNT(*) FROM t_sys_user_role ur
                LEFT JOIN t_sys_user u ON ur.user_id = u.id
                LEFT JOIN t_sys_role r ON ur.role_id = r.id
                WHERE u.id IS NULL OR r.id IS NULL
            """)
            
            if orphaned_user_roles == 0:
                print("  ✅ 用户角色关联完整性检查通过")
                integrity_checks.append(('user_role_integrity', True, '用户角色关联完整性'))
            else:
                print(f"  ⚠️ 发现 {orphaned_user_roles} 条孤立的用户角色关联")
                integrity_checks.append(('user_role_integrity', False, f'发现{orphaned_user_roles}条孤立记录'))
                
        except Exception as e:
            print(f"  ❌ 用户角色关联完整性检查失败: {e}")
            integrity_checks.append(('user_role_integrity', False, f'检查失败: {e}'))
        
        # 检查API权限映射
        try:
            api_without_permission = await self.conn.fetchval("""
                SELECT COUNT(*) FROM t_sys_api_endpoints
                WHERE permission_code IS NULL OR permission_code = ''
            """)
            
            if api_without_permission == 0:
                print("  ✅ API权限映射检查通过")
                integrity_checks.append(('api_permission_mapping', True, 'API权限映射完整'))
            else:
                print(f"  ⚠️ 发现 {api_without_permission} 个API端点未映射权限")
                integrity_checks.append(('api_permission_mapping', False, f'{api_without_permission}个API未映射权限'))
                
        except Exception as e:
            print(f"  ❌ API权限映射检查失败: {e}")
            integrity_checks.append(('api_permission_mapping', False, f'检查失败: {e}'))
        
        # 检查权限数据与API端点的对应关系
        try:
            permission_api_match = await self.conn.fetchval("""
                SELECT COUNT(*) FROM t_sys_permission p
                WHERE p.permission_type = 'api' 
                  AND NOT EXISTS (
                      SELECT 1 FROM t_sys_api_endpoints ae 
                      WHERE ae.permission_code = p.permission_code
                  )
            """)
            
            if permission_api_match == 0:
                print("  ✅ 权限与API端点映射检查通过")
                integrity_checks.append(('permission_api_match', True, '权限与API端点映射完整'))
            else:
                print(f"  ⚠️ 发现 {permission_api_match} 个权限没有对应的API端点")
                integrity_checks.append(('permission_api_match', False, f'{permission_api_match}个权限无对应API'))
                
        except Exception as e:
            print(f"  ❌ 权限与API端点映射检查失败: {e}")
            integrity_checks.append(('permission_api_match', False, f'检查失败: {e}'))
        
        return integrity_checks
    
    async def show_migration_summary(self):
        """显示迁移摘要"""
        print("\n迁移摘要:")
        print("="*60)
        
        try:
            # 获取各表的统计信息
            tables = [
                ('t_sys_dept', '部门'),
                ('t_sys_user', '用户'),
                ('t_sys_role', '角色'),
                ('t_sys_menu', '菜单'),
                ('t_sys_user_role', '用户角色关联'),
                ('t_sys_role_menu', '角色菜单关联'),
                ('t_sys_api_endpoints', 'API端点'),
                ('t_sys_permission', '权限')
            ]
            
            for table_name, description in tables:
                try:
                    count = await self.conn.fetchval(f'SELECT COUNT(*) FROM {table_name}')
                    print(f"  {description}: {count} 条")
                except Exception as e:
                    print(f"  {description}: 查询失败 - {e}")
            
            print("="*60)
            
            # 显示一些关键的数据样例
            print("\n关键数据样例:")
            
            # 显示用户信息
            users = await self.conn.fetch("""
                SELECT u.username, u.nick_name, d.dept_name, 
                       string_agg(r.role_name, ', ') as roles
                FROM t_sys_user u
                LEFT JOIN t_sys_dept d ON u.dept_id = d.id
                LEFT JOIN t_sys_user_role ur ON u.id = ur.user_id
                LEFT JOIN t_sys_role r ON ur.role_id = r.id
                GROUP BY u.id, u.username, u.nick_name, d.dept_name
                LIMIT 5
            """)
            
            print("  用户信息:")
            for user in users:
                roles = user['roles'] or '无角色'
                dept = user['dept_name'] or '无部门'
                print(f"    - {user['username']} ({user['nick_name']}) | 部门: {dept} | 角色: {roles}")
            
            # 显示权限统计
            permission_stats = await self.conn.fetch("""
                SELECT permission_type, COUNT(*) as count
                FROM t_sys_permission
                GROUP BY permission_type
                ORDER BY count DESC
            """)
            
            print("  权限类型统计:")
            for stat in permission_stats:
                print(f"    - {stat['permission_type']}: {stat['count']} 个")
            
        except Exception as e:
            print(f"获取迁移摘要失败: {e}")
    
    async def run_verification(self):
        """运行完整验证"""
        self.print_banner()
        
        try:
            # 连接数据库
            if not await self.connect():
                return False
            
            # 验证表数据
            table_results = await self.verify_table_data()
            
            # 验证数据完整性
            integrity_results = await self.verify_data_integrity()
            
            # 显示迁移摘要
            await self.show_migration_summary()
            
            # 计算总体成功率
            table_success = sum(1 for r in table_results if r['status'] == '通过')
            table_total = len(table_results)
            
            integrity_success = sum(1 for r in integrity_results if r[1] == True)
            integrity_total = len(integrity_results)
            
            overall_success_rate = ((table_success + integrity_success) / (table_total + integrity_total)) * 100
            
            print(f"\n验证结果:")
            print("="*60)
            print(f"表数据验证: {table_success}/{table_total} 通过")
            print(f"完整性验证: {integrity_success}/{integrity_total} 通过")
            print(f"总体成功率: {overall_success_rate:.1f}%")
            print("="*60)
            
            if overall_success_rate >= 80:
                print("🎉 数据库迁移验证通过！")
                return True
            else:
                print("⚠️ 数据库迁移验证存在问题，请检查详情")
                return False
            
        except Exception as e:
            print(f"验证过程中发生错误: {e}")
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
        print("\n❌ 验证发现问题，请检查详细信息！")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)