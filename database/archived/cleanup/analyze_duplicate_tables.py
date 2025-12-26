#!/usr/bin/env python3
"""
分析本次迁移造成的重复表，特别是t开头的权限相关表
"""

import asyncio
import asyncpg

async def analyze_duplicate_tables():
    conn = await asyncpg.connect('postgresql://postgres:Hanatech%40123@127.0.0.1:5432/devicemonitor')
    
    print('本次迁移造成的重复表分析')
    print('=' * 60)
    
    # 重点分析的重复表组
    duplicate_groups = [
        {
            'category': '角色权限表',
            'tables': ['t_sys_role_permission', 't_sys_role_permissions'],
            'description': '单数vs复数形式，功能相似但结构不同'
        },
        {
            'category': '用户权限表', 
            'tables': ['t_sys_user_permission', 't_sys_user_permissions'],
            'description': '单数vs复数形式，功能相似但结构不同'
        },
        {
            'category': '系统配置表',
            'tables': ['sys_config', 't_sys_config'],
            'description': '旧表vs新表，可能存在数据重复'
        },
        {
            'category': '字典数据表',
            'tables': ['sys_dict_data', 't_sys_dict_data'],
            'description': '旧表vs新表，可能存在数据重复'
        },
        {
            'category': '字典类型表',
            'tables': ['sys_dict_type', 't_sys_dict_type'], 
            'description': '旧表vs新表，可能存在数据重复'
        },
        {
            'category': '焊接日报表',
            'tables': ['welding_daily_report', 't_welding_daily_report'],
            'description': '旧表vs新表，可能存在数据重复'
        }
    ]
    
    for group in duplicate_groups:
        print(f'\n📊 {group["category"]}')
        print(f'描述: {group["description"]}')
        print('-' * 50)
        
        for table_name in group['tables']:
            # 检查表是否存在
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = $1
                )
            """, table_name)
            
            if not exists:
                print(f'❌ {table_name}: 表不存在')
                continue
                
            print(f'\n✅ {table_name}:')
            
            # 获取表结构
            columns = await conn.fetch("""
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_name = $1
                ORDER BY ordinal_position
            """, table_name)
            
            print(f'   列数: {len(columns)}')
            print('   主要列:')
            for col in columns[:5]:  # 只显示前5列
                nullable = 'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'
                print(f'     - {col["column_name"]}: {col["data_type"]} {nullable}')
            
            if len(columns) > 5:
                print(f'     ... 还有 {len(columns) - 5} 列')
            
            # 获取记录数
            try:
                count = await conn.fetchval(f'SELECT COUNT(*) FROM {table_name}')
                print(f'   记录数: {count:,}')
            except Exception as e:
                print(f'   记录数: 查询失败 - {e}')
            
            # 获取索引数量
            index_count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM pg_indexes 
                WHERE tablename = $1 AND schemaname = 'public'
            """, table_name)
            print(f'   索引数: {index_count}')
            
            # 获取表大小
            try:
                size = await conn.fetchval(f"""
                    SELECT pg_size_pretty(pg_total_relation_size('{table_name}'))
                """)
                print(f'   表大小: {size}')
            except Exception as e:
                print(f'   表大小: 查询失败')
    
    # 生成清理建议
    print('\n\n🔧 清理建议')
    print('=' * 60)
    
    recommendations = [
        {
            'action': '保留',
            'tables': ['t_sys_role_permissions', 't_sys_user_permissions'],
            'reason': '新的权限系统表，结构更完善，支持权限码和资源ID',
            'next_step': '确认数据迁移完成后，可以考虑删除旧表'
        },
        {
            'action': '考虑删除',
            'tables': ['t_sys_role_permission', 't_sys_user_permission'],
            'reason': '旧的权限系统表，使用permission_id关联，结构相对简单',
            'next_step': '确认新表功能正常后删除'
        },
        {
            'action': '数据对比',
            'tables': ['sys_config vs t_sys_config', 'sys_dict_data vs t_sys_dict_data', 'sys_dict_type vs t_sys_dict_type'],
            'reason': '需要对比数据是否一致，确定哪个是主表',
            'next_step': '数据同步后删除冗余表'
        }
    ]
    
    for rec in recommendations:
        print(f'\n📋 {rec["action"]}:')
        print(f'   表: {", ".join(rec["tables"]) if isinstance(rec["tables"], list) else rec["tables"]}')
        print(f'   原因: {rec["reason"]}')
        print(f'   下一步: {rec["next_step"]}')
    
    await conn.close()

if __name__ == '__main__':
    asyncio.run(analyze_duplicate_tables())