#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流版本历史表迁移脚本
"""

import os
import sys
import asyncio
import asyncpg

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'app', '.env.dev'))


async def get_db_connection():
    """获取数据库连接"""
    # 从环境变量获取数据库配置
    db_host = os.getenv('POSTGRES_HOST', '127.0.0.1')
    db_port = int(os.getenv('POSTGRES_PORT', 5432))
    db_user = os.getenv('POSTGRES_USER', 'postgres')
    db_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
    db_name = os.getenv('POSTGRES_DATABASE', 'devicemonitor')
    
    print(f"连接数据库: {db_host}:{db_port}/{db_name}")
    
    conn = await asyncpg.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name
    )
    return conn


async def execute_migration():
    """执行迁移"""
    conn = await get_db_connection()
    
    try:
        # 读取SQL文件
        sql_file = os.path.join(os.path.dirname(__file__), '005_create_workflow_version_table.sql')
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print("=" * 60)
        print("开始执行工作流版本历史表迁移...")
        print("=" * 60)
        
        # 定义要执行的SQL语句
        sql_statements = [
            # 1. 创建表
            ("""
            CREATE TABLE IF NOT EXISTS t_sys_workflow_version (
                id BIGSERIAL PRIMARY KEY,
                workflow_id BIGINT NOT NULL REFERENCES t_sys_workflow(id) ON DELETE CASCADE,
                version VARCHAR(20) NOT NULL,
                version_name VARCHAR(100),
                description TEXT,
                snapshot JSONB NOT NULL,
                change_type VARCHAR(20) DEFAULT 'update',
                change_summary TEXT,
                is_published BOOLEAN DEFAULT FALSE,
                is_current BOOLEAN DEFAULT FALSE,
                created_by BIGINT,
                created_by_name VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """, "创建表 t_sys_workflow_version"),
            
            # 2. 创建索引
            ("CREATE INDEX IF NOT EXISTS idx_workflow_version_workflow_id ON t_sys_workflow_version(workflow_id)", "创建索引 workflow_id"),
            ("CREATE INDEX IF NOT EXISTS idx_workflow_version_version ON t_sys_workflow_version(version)", "创建索引 version"),
            ("CREATE INDEX IF NOT EXISTS idx_workflow_version_is_current ON t_sys_workflow_version(is_current)", "创建索引 is_current"),
            ("CREATE INDEX IF NOT EXISTS idx_workflow_version_created_at ON t_sys_workflow_version(created_at)", "创建索引 created_at"),
            
            # 3. 添加注释
            ("COMMENT ON TABLE t_sys_workflow_version IS '工作流版本历史表'", "添加表注释"),
            ("COMMENT ON COLUMN t_sys_workflow_version.workflow_id IS '关联工作流ID'", "添加列注释 workflow_id"),
            ("COMMENT ON COLUMN t_sys_workflow_version.version IS '版本号'", "添加列注释 version"),
            ("COMMENT ON COLUMN t_sys_workflow_version.snapshot IS '工作流快照'", "添加列注释 snapshot"),
        ]
        
        for i, (stmt, desc) in enumerate(sql_statements, 1):
            try:
                await conn.execute(stmt)
                print(f"  [{i}/{len(sql_statements)}] {desc} ✓")
            except Exception as e:
                if 'already exists' in str(e).lower():
                    print(f"  [{i}/{len(sql_statements)}] {desc} (已存在)")
                else:
                    print(f"  [{i}/{len(sql_statements)}] {desc} 错误: {e}")
        
        print("=" * 60)
        print("迁移完成！")
        print("=" * 60)
        
        # 验证表是否创建成功
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 't_sys_workflow_version'
            )
        """)
        
        if result:
            print("✓ 表 t_sys_workflow_version 创建成功")
            
            # 查询表结构
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 't_sys_workflow_version'
                ORDER BY ordinal_position
            """)
            
            print("\n表结构:")
            print("-" * 50)
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                print(f"  {col['column_name']}: {col['data_type']} {nullable}")
        else:
            print("✗ 表创建失败")
            
    except Exception as e:
        print(f"迁移失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()


if __name__ == '__main__':
    asyncio.run(execute_migration())
