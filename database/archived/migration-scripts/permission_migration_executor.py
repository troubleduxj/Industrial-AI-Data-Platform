#!/usr/bin/env python3
"""
权限数据迁移执行器
执行权限数据迁移，包含完整的日志记录和错误处理
"""

import asyncio
import json
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import asyncpg
from pathlib import Path
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MigrationStep:
    """迁移步骤数据结构"""
    step_name: str
    sql_content: str
    rollback_sql: str = ""
    is_critical: bool = True
    timeout_seconds: int = 300

@dataclass
class MigrationResult:
    """迁移结果数据结构"""
    step_name: str
    status: str  # SUCCESS, FAILED, SKIPPED
    execution_time_ms: int
    error_message: str = ""
    affected_rows: int = 0

class PermissionMigrationExecutor:
    """权限迁移执行器"""
    
    def __init__(self, db_url: str, dry_run: bool = False):
        self.db_url = db_url
        self.dry_run = dry_run
        self.connection: Optional[asyncpg.Connection] = None
        self.transaction: Optional[asyncpg.Transaction] = None
        self.migration_results: List[MigrationResult] = []
        self.migration_id: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    async def connect(self):
        """连接数据库"""
        try:
            self.connection = await asyncpg.connect(self.db_url)
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    async def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            await self.connection.close()
            logger.info("数据库连接已关闭")

    async def create_backup_tables(self) -> MigrationResult:
        """创建备份表"""
        logger.info("创建备份表...")
        start_time = time.time()
        
        backup_sql = f"""
        -- 创建备份表 (迁移ID: {self.migration_id})
        CREATE TABLE IF NOT EXISTS api_backup_{self.migration_id} AS SELECT * FROM api;
        CREATE TABLE IF NOT EXISTS role_api_backup_{self.migration_id} AS SELECT * FROM role_api;
        CREATE TABLE IF NOT EXISTS role_backup_{self.migration_id} AS SELECT * FROM role;
        CREATE TABLE IF NOT EXISTS user_role_backup_{self.migration_id} AS SELECT * FROM user_role;
        
        -- 记录备份信息
        INSERT INTO t_sys_migration_logs 
        (migration_name, migration_type, version, description, status, created_at, created_by)
        VALUES 
        ('backup_creation', 'backup', 'v2', '权限迁移前数据备份', 'success', CURRENT_TIMESTAMP, 'migration_executor');
        """
        
        rollback_sql = f"""
        -- 删除备份表
        DROP TABLE IF EXISTS api_backup_{self.migration_id};
        DROP TABLE IF EXISTS role_api_backup_{self.migration_id};
        DROP TABLE IF EXISTS role_backup_{self.migration_id};
        DROP TABLE IF EXISTS user_role_backup_{self.migration_id};
        """
        
        try:
            if not self.dry_run:
                await self.connection.execute(backup_sql)
            
            execution_time = int((time.time() - start_time) * 1000)
            result = MigrationResult(
                step_name="create_backup_tables",
                status="SUCCESS",
                execution_time_ms=execution_time
            )
            logger.info(f"备份表创建成功 (耗时: {execution_time}ms)")
            return result
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            error_msg = f"备份表创建失败: {str(e)}"
            logger.error(error_msg)
            return MigrationResult(
                step_name="create_backup_tables",
                status="FAILED",
                execution_time_ms=execution_time,
                error_message=error_msg
            )

    async def create_migration_tables(self) -> MigrationResult:
        """创建迁移相关表"""
        logger.info("创建迁移相关表...")
        start_time = time.time()
        
        migration_tables_sql = """
        -- 创建权限迁移映射表
        CREATE TABLE IF NOT EXISTS t_sys_permission_migrations (
            id BIGSERIAL PRIMARY KEY,
            old_permission VARCHAR(255) NOT NULL UNIQUE,
            new_permission VARCHAR(255) NOT NULL,
            api_path VARCHAR(500) NOT NULL,
            http_method VARCHAR(10) NOT NULL,
            api_group VARCHAR(100) NOT NULL,
            migration_type VARCHAR(20) NOT NULL,
            confidence_score DECIMAL(3,2) NOT NULL,
            migration_batch VARCHAR(50) NOT NULL,
            notes TEXT,
            is_active BOOLEAN DEFAULT true,
            migrated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_permission_migrations_old ON t_sys_permission_migrations(old_permission);
        CREATE INDEX IF NOT EXISTS idx_permission_migrations_new ON t_sys_permission_migrations(new_permission);
        CREATE INDEX IF NOT EXISTS idx_permission_migrations_batch ON t_sys_permission_migrations(migration_batch);
        
        -- 创建数据迁移记录表
        CREATE TABLE IF NOT EXISTS t_sys_migration_logs (
            id BIGSERIAL PRIMARY KEY,
            migration_name VARCHAR(200) NOT NULL,
            migration_type VARCHAR(50) NOT NULL,
            version VARCHAR(20) NOT NULL,
            description TEXT,
            sql_content TEXT,
            rollback_sql TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            error_message TEXT,
            execution_time_ms INT,
            executed_at TIMESTAMP NULL,
            rolled_back_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(100)
        );
        
        CREATE INDEX IF NOT EXISTS idx_migration_logs_type ON t_sys_migration_logs(migration_type);
        CREATE INDEX IF NOT EXISTS idx_migration_logs_status ON t_sys_migration_logs(status);
        CREATE INDEX IF NOT EXISTS idx_migration_logs_executed ON t_sys_migration_logs(executed_at);
        
        -- 添加表注释
        COMMENT ON TABLE t_sys_permission_migrations IS '权限迁移映射表';
        COMMENT ON TABLE t_sys_migration_logs IS '数据迁移记录表';
        """
        
        try:
            if not self.dry_run:
                await self.connection.execute(migration_tables_sql)
            
            execution_time = int((time.time() - start_time) * 1000)
            result = MigrationResult(
                step_name="create_migration_tables",
                status="SUCCESS",
                execution_time_ms=execution_time
            )
            logger.info(f"迁移表创建成功 (耗时: {execution_time}ms)")
            return result
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            error_msg = f"迁移表创建失败: {str(e)}"
            logger.error(error_msg)
            return MigrationResult(
                step_name="create_migration_tables",
                status="FAILED",
                execution_time_ms=execution_time,
                error_message=error_msg
            )

    async def load_permission_mappings(self, mappings_file: str) -> MigrationResult:
        """加载权限映射数据"""
        logger.info(f"加载权限映射数据: {mappings_file}")
        start_time = time.time()
        
        try:
            # 读取映射文件
            with open(mappings_file, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
            
            if not mappings:
                return MigrationResult(
                    step_name="load_permission_mappings",
                    status="FAILED",
                    execution_time_ms=0,
                    error_message="映射文件为空"
                )
            
            # 批量插入映射数据
            insert_sql = """
            INSERT INTO t_sys_permission_migrations 
            (old_permission, new_permission, api_path, http_method, api_group, 
             migration_type, confidence_score, migration_batch, notes)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (old_permission) DO UPDATE SET
                new_permission = EXCLUDED.new_permission,
                api_path = EXCLUDED.api_path,
                http_method = EXCLUDED.http_method,
                api_group = EXCLUDED.api_group,
                migration_type = EXCLUDED.migration_type,
                confidence_score = EXCLUDED.confidence_score,
                notes = EXCLUDED.notes
            """
            
            if not self.dry_run:
                async with self.connection.transaction():
                    for mapping in mappings:
                        await self.connection.execute(
                            insert_sql,
                            mapping['old_permission'],
                            mapping['new_permission'],
                            mapping['api_path'],
                            mapping['http_method'],
                            mapping['api_group'],
                            mapping['migration_type'],
                            mapping['confidence_score'],
                            self.migration_id,
                            mapping.get('notes', '')
                        )
            
            execution_time = int((time.time() - start_time) * 1000)
            result = MigrationResult(
                step_name="load_permission_mappings",
                status="SUCCESS",
                execution_time_ms=execution_time,
                affected_rows=len(mappings)
            )
            logger.info(f"权限映射数据加载成功: {len(mappings)}条记录 (耗时: {execution_time}ms)")
            return result
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            error_msg = f"权限映射数据加载失败: {str(e)}"
            logger.error(error_msg)
            return MigrationResult(
                step_name="load_permission_mappings",
                status="FAILED",
                execution_time_ms=execution_time,
                error_message=error_msg
            )

    async def create_new_api_structure(self) -> MigrationResult:
        """创建新的API结构表"""
        logger.info("创建新的API结构表...")
        start_time = time.time()
        
        new_api_structure_sql = """
        -- 创建API分组表
        CREATE TABLE IF NOT EXISTS t_sys_api_groups (
            id BIGSERIAL PRIMARY KEY,
            group_code VARCHAR(50) NOT NULL UNIQUE,
            group_name VARCHAR(100) NOT NULL,
            parent_id BIGINT DEFAULT 0,
            description TEXT,
            sort_order INT DEFAULT 0,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_api_groups_code ON t_sys_api_groups(group_code);
        CREATE INDEX IF NOT EXISTS idx_api_groups_parent ON t_sys_api_groups(parent_id);
        
        -- 创建新的API接口表
        CREATE TABLE IF NOT EXISTS t_sys_api_endpoints (
            id BIGSERIAL PRIMARY KEY,
            api_code VARCHAR(100) NOT NULL UNIQUE,
            api_name VARCHAR(200) NOT NULL,
            api_path VARCHAR(500) NOT NULL,
            http_method VARCHAR(10) NOT NULL,
            group_id BIGINT NOT NULL,
            description TEXT,
            version VARCHAR(10) DEFAULT 'v2',
            is_public BOOLEAN DEFAULT FALSE,
            is_deprecated BOOLEAN DEFAULT FALSE,
            rate_limit INT DEFAULT 0,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            CONSTRAINT fk_api_endpoints_group FOREIGN KEY (group_id) REFERENCES t_sys_api_groups(id)
        );
        
        CREATE UNIQUE INDEX IF NOT EXISTS idx_api_endpoints_method_path ON t_sys_api_endpoints(http_method, api_path);
        CREATE INDEX IF NOT EXISTS idx_api_endpoints_code ON t_sys_api_endpoints(api_code);
        CREATE INDEX IF NOT EXISTS idx_api_endpoints_group ON t_sys_api_endpoints(group_id);
        
        -- 插入默认API分组
        INSERT INTO t_sys_api_groups (group_code, group_name, description, sort_order) VALUES
        ('system', '系统管理', '用户、角色、菜单、部门管理', 1),
        ('device', '设备管理', '设备信息、类型、监控管理', 2),
        ('ai', 'AI监控', 'AI预测、模型、数据标注', 3),
        ('statistics', '统计分析', '数据统计和分析报告', 4),
        ('dashboard', '仪表板', '概览和仪表板数据', 5)
        ON CONFLICT (group_code) DO NOTHING;
        
        -- 添加表注释
        COMMENT ON TABLE t_sys_api_groups IS 'API分组表';
        COMMENT ON TABLE t_sys_api_endpoints IS 'API接口表';
        """
        
        try:
            if not self.dry_run:
                await self.connection.execute(new_api_structure_sql)
            
            execution_time = int((time.time() - start_time) * 1000)
            result = MigrationResult(
                step_name="create_new_api_structure",
                status="SUCCESS",
                execution_time_ms=execution_time
            )
            logger.info(f"新API结构表创建成功 (耗时: {execution_time}ms)")
            return result
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            error_msg = f"新API结构表创建失败: {str(e)}"
            logger.error(error_msg)
            return MigrationResult(
                step_name="create_new_api_structure",
                status="FAILED",
                execution_time_ms=execution_time,
                error_message=error_msg
            )

    async def migrate_api_data(self) -> MigrationResult:
        """迁移API数据到新结构"""
        logger.info("迁移API数据到新结构...")
        start_time = time.time()
        
        migrate_api_sql = """
        -- 迁移API数据到新结构
        INSERT INTO t_sys_api_endpoints (
            api_code, api_name, api_path, http_method, group_id, description, version
        )
        SELECT 
            LOWER(REPLACE(pm.new_permission, ' ', '_')) as api_code,
            COALESCE(a.summary, pm.new_permission) as api_name,
            pm.api_path,
            pm.http_method,
            CASE pm.api_group
                WHEN '系统管理' THEN (SELECT id FROM t_sys_api_groups WHERE group_code = 'system')
                WHEN '设备管理' THEN (SELECT id FROM t_sys_api_groups WHERE group_code = 'device')
                WHEN 'AI监控' THEN (SELECT id FROM t_sys_api_groups WHERE group_code = 'ai')
                WHEN '统计分析' THEN (SELECT id FROM t_sys_api_groups WHERE group_code = 'statistics')
                WHEN '仪表板' THEN (SELECT id FROM t_sys_api_groups WHERE group_code = 'dashboard')
                ELSE (SELECT id FROM t_sys_api_groups WHERE group_code = 'system')
            END as group_id,
            pm.notes as description,
            'v2' as version
        FROM t_sys_permission_migrations pm
        LEFT JOIN api a ON CONCAT(a.method, ' ', a.path) = pm.old_permission
        WHERE pm.is_active = true
        ON CONFLICT (api_code) DO UPDATE SET
            api_name = EXCLUDED.api_name,
            api_path = EXCLUDED.api_path,
            description = EXCLUDED.description;
        """
        
        try:
            if not self.dry_run:
                result_proxy = await self.connection.execute(migrate_api_sql)
                # 从结果中提取受影响的行数
                affected_rows = int(result_proxy.split()[-1]) if result_proxy.startswith('INSERT') else 0
            else:
                affected_rows = 0
            
            execution_time = int((time.time() - start_time) * 1000)
            result = MigrationResult(
                step_name="migrate_api_data",
                status="SUCCESS",
                execution_time_ms=execution_time,
                affected_rows=affected_rows
            )
            logger.info(f"API数据迁移成功: {affected_rows}条记录 (耗时: {execution_time}ms)")
            return result
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            error_msg = f"API数据迁移失败: {str(e)}"
            logger.error(error_msg)
            return MigrationResult(
                step_name="migrate_api_data",
                status="FAILED",
                execution_time_ms=execution_time,
                error_message=error_msg
            )

    async def create_validation_functions(self) -> MigrationResult:
        """创建验证函数"""
        logger.info("创建验证函数...")
        start_time = time.time()
        
        validation_functions_sql = """
        -- 创建权限迁移验证函数
        CREATE OR REPLACE FUNCTION validate_permission_migration()
        RETURNS TABLE(
            validation_type VARCHAR,
            old_count BIGINT,
            new_count BIGINT,
            status VARCHAR,
            message TEXT
        ) AS $
        DECLARE
            old_api_count BIGINT;
            new_api_count BIGINT;
            mapping_count BIGINT;
            high_confidence_count BIGINT;
            low_confidence_count BIGINT;
        BEGIN
            -- 统计原有API数量
            SELECT COUNT(*) INTO old_api_count FROM api;
            
            -- 统计新API数量
            SELECT COUNT(*) INTO new_api_count FROM t_sys_api_endpoints;
            
            -- 统计映射数量
            SELECT COUNT(*) INTO mapping_count FROM t_sys_permission_migrations;
            
            -- 统计置信度
            SELECT COUNT(*) INTO high_confidence_count 
            FROM t_sys_permission_migrations WHERE confidence_score >= 0.9;
            
            SELECT COUNT(*) INTO low_confidence_count 
            FROM t_sys_permission_migrations WHERE confidence_score < 0.7;
            
            -- 返回验证结果
            RETURN QUERY SELECT 
                'api_migration'::VARCHAR,
                old_api_count,
                new_api_count,
                CASE WHEN old_api_count = mapping_count THEN 'PASS' ELSE 'WARN' END::VARCHAR,
                ('原有API: ' || old_api_count || ', 新API: ' || new_api_count || ', 映射: ' || mapping_count)::TEXT;
            
            RETURN QUERY SELECT 
                'high_confidence'::VARCHAR,
                high_confidence_count,
                0::BIGINT,
                'INFO'::VARCHAR,
                ('高置信度映射: ' || high_confidence_count)::TEXT;
            
            RETURN QUERY SELECT 
                'low_confidence'::VARCHAR,
                low_confidence_count,
                0::BIGINT,
                CASE WHEN low_confidence_count > 0 THEN 'WARN' ELSE 'PASS' END::VARCHAR,
                ('低置信度映射: ' || low_confidence_count || ' (需要人工检查)')::TEXT;
        END;
        $ LANGUAGE plpgsql;
        
        -- 创建权限查询优化函数
        CREATE OR REPLACE FUNCTION get_user_permissions_v2(user_id_param BIGINT)
        RETURNS TABLE(
            permission_code VARCHAR,
            api_path VARCHAR,
            http_method VARCHAR,
            api_group VARCHAR
        ) AS $
        BEGIN
            RETURN QUERY
            SELECT 
                ae.api_code,
                ae.api_path,
                ae.http_method,
                ag.group_name
            FROM user_role ur
            JOIN role_api ra ON ur.role_id = ra.role_id
            JOIN api a ON ra.api_id = a.id
            JOIN t_sys_permission_migrations pm ON CONCAT(a.method, ' ', a.path) = pm.old_permission
            JOIN t_sys_api_endpoints ae ON pm.new_permission = CONCAT(ae.http_method, ' ', ae.api_path)
            JOIN t_sys_api_groups ag ON ae.group_id = ag.id
            WHERE ur.user_id = user_id_param
              AND pm.is_active = true
              AND ae.status = 'active';
        END;
        $ LANGUAGE plpgsql;
        """
        
        try:
            if not self.dry_run:
                await self.connection.execute(validation_functions_sql)
            
            execution_time = int((time.time() - start_time) * 1000)
            result = MigrationResult(
                step_name="create_validation_functions",
                status="SUCCESS",
                execution_time_ms=execution_time
            )
            logger.info(f"验证函数创建成功 (耗时: {execution_time}ms)")
            return result
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            error_msg = f"验证函数创建失败: {str(e)}"
            logger.error(error_msg)
            return MigrationResult(
                step_name="create_validation_functions",
                status="FAILED",
                execution_time_ms=execution_time,
                error_message=error_msg
            )

    async def log_migration_step(self, step_name: str, status: str, execution_time_ms: int, 
                               error_message: str = "", sql_content: str = ""):
        """记录迁移步骤"""
        if self.dry_run:
            return
            
        try:
            log_sql = """
            INSERT INTO t_sys_migration_logs 
            (migration_name, migration_type, version, description, status, 
             execution_time_ms, error_message, sql_content, executed_at, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CURRENT_TIMESTAMP, $9)
            """
            
            await self.connection.execute(
                log_sql,
                step_name,
                'permission_migration',
                'v2',
                f'权限迁移步骤: {step_name}',
                status.lower(),
                execution_time_ms,
                error_message,
                sql_content[:1000] if sql_content else "",  # 限制SQL内容长度
                'migration_executor'
            )
        except Exception as e:
            logger.error(f"记录迁移日志失败: {e}")

    async def execute_migration(self, mappings_file: str) -> Dict:
        """执行完整的迁移流程"""
        logger.info(f"开始执行权限迁移 (迁移ID: {self.migration_id})")
        logger.info(f"干运行模式: {self.dry_run}")
        
        migration_steps = [
            ("创建备份表", self.create_backup_tables),
            ("创建迁移表", self.create_migration_tables),
            ("加载权限映射", lambda: self.load_permission_mappings(mappings_file)),
            ("创建新API结构", self.create_new_api_structure),
            ("迁移API数据", self.migrate_api_data),
            ("创建验证函数", self.create_validation_functions)
        ]
        
        success_count = 0
        failed_count = 0
        
        for step_name, step_func in migration_steps:
            logger.info(f"执行步骤: {step_name}")
            
            try:
                result = await step_func()
                self.migration_results.append(result)
                
                # 记录迁移日志
                await self.log_migration_step(
                    result.step_name,
                    result.status,
                    result.execution_time_ms,
                    result.error_message
                )
                
                if result.status == "SUCCESS":
                    success_count += 1
                    logger.info(f"✅ {step_name} 完成")
                else:
                    failed_count += 1
                    logger.error(f"❌ {step_name} 失败: {result.error_message}")
                    
                    # 如果是关键步骤失败，停止迁移
                    if result.step_name in ["create_backup_tables", "create_migration_tables"]:
                        logger.error("关键步骤失败，停止迁移")
                        break
                        
            except Exception as e:
                error_msg = f"步骤执行异常: {str(e)}\n{traceback.format_exc()}"
                logger.error(error_msg)
                
                result = MigrationResult(
                    step_name=step_name.replace(" ", "_").lower(),
                    status="FAILED",
                    execution_time_ms=0,
                    error_message=error_msg
                )
                self.migration_results.append(result)
                failed_count += 1
                break
        
        # 生成迁移摘要
        total_time = sum(r.execution_time_ms for r in self.migration_results)
        summary = {
            'migration_id': self.migration_id,
            'dry_run': self.dry_run,
            'total_steps': len(migration_steps),
            'success_count': success_count,
            'failed_count': failed_count,
            'total_execution_time_ms': total_time,
            'results': [asdict(r) for r in self.migration_results]
        }
        
        logger.info(f"迁移完成: {success_count}个成功, {failed_count}个失败, 总耗时: {total_time}ms")
        return summary

    async def rollback_migration(self) -> Dict:
        """回滚迁移"""
        logger.info(f"开始回滚迁移 (迁移ID: {self.migration_id})")
        
        if self.dry_run:
            logger.info("干运行模式，跳过实际回滚")
            return {'status': 'skipped', 'message': '干运行模式'}
        
        rollback_sql = f"""
        -- 回滚权限迁移
        DROP TABLE IF EXISTS t_sys_api_endpoints;
        DROP TABLE IF EXISTS t_sys_api_groups;
        DROP TABLE IF EXISTS t_sys_permission_migrations;
        DROP FUNCTION IF EXISTS validate_permission_migration();
        DROP FUNCTION IF EXISTS get_user_permissions_v2(BIGINT);
        
        -- 删除备份表
        DROP TABLE IF EXISTS api_backup_{self.migration_id};
        DROP TABLE IF EXISTS role_api_backup_{self.migration_id};
        DROP TABLE IF EXISTS role_backup_{self.migration_id};
        DROP TABLE IF EXISTS user_role_backup_{self.migration_id};
        
        -- 记录回滚操作
        UPDATE t_sys_migration_logs 
        SET status = 'rolled_back', rolled_back_at = CURRENT_TIMESTAMP
        WHERE migration_type = 'permission_migration' 
          AND created_by = 'migration_executor'
          AND executed_at >= CURRENT_DATE;
        """
        
        try:
            await self.connection.execute(rollback_sql)
            logger.info("迁移回滚成功")
            return {'status': 'success', 'message': '迁移回滚成功'}
        except Exception as e:
            error_msg = f"迁移回滚失败: {str(e)}"
            logger.error(error_msg)
            return {'status': 'failed', 'message': error_msg}

    async def save_migration_report(self, summary: Dict, output_dir: str = "database"):
        """保存迁移报告"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 保存迁移结果JSON
        results_file = output_path / f"migration_results_{self.migration_id}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
        
        # 生成迁移报告
        report = self.generate_migration_report(summary)
        report_file = output_path / f"migration_report_{self.migration_id}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"迁移报告已保存到 {output_path}")
        return {
            'results_file': str(results_file),
            'report_file': str(report_file)
        }

    def generate_migration_report(self, summary: Dict) -> str:
        """生成迁移报告"""
        report = f"""# 权限数据迁移执行报告

## 迁移信息
- **迁移ID**: {summary['migration_id']}
- **执行时间**: {datetime.now().isoformat()}
- **模式**: {'干运行' if summary['dry_run'] else '实际执行'}
- **总步骤数**: {summary['total_steps']}
- **成功步骤**: {summary['success_count']}
- **失败步骤**: {summary['failed_count']}
- **总执行时间**: {summary['total_execution_time_ms']}ms

## 执行结果

"""
        
        for result in summary['results']:
            status_emoji = "✅" if result['status'] == "SUCCESS" else "❌"
            report += f"### {status_emoji} {result['step_name']}\n"
            report += f"- **状态**: {result['status']}\n"
            report += f"- **执行时间**: {result['execution_time_ms']}ms\n"
            
            if result.get('affected_rows'):
                report += f"- **影响行数**: {result['affected_rows']}\n"
            
            if result.get('error_message'):
                report += f"- **错误信息**: {result['error_message']}\n"
            
            report += "\n"
        
        # 添加后续步骤建议
        if summary['failed_count'] > 0:
            report += """## ⚠️ 迁移失败处理

### 立即行动
1. 检查失败步骤的错误信息
2. 修复问题后重新执行迁移
3. 如需回滚，执行回滚命令

### 回滚命令
```bash
python database/permission_migration_executor.py --rollback --migration-id {migration_id}
```
""".format(migration_id=summary['migration_id'])
        else:
            report += """## ✅ 迁移成功

### 后续步骤
1. 运行验证程序确认迁移结果
2. 更新前端权限配置
3. 测试权限功能
4. 部署到生产环境

### 验证命令
```bash
python database/permission_migration_validator.py
```

### 验证SQL
```sql
SELECT * FROM validate_permission_migration();
```
"""
        
        return report

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='权限数据迁移执行器')
    parser.add_argument('--db-url', default='postgresql://user:password@localhost:5432/database',
                       help='数据库连接URL')
    parser.add_argument('--mappings-file', required=True,
                       help='权限映射文件路径')
    parser.add_argument('--dry-run', action='store_true',
                       help='干运行模式，不实际执行SQL')
    parser.add_argument('--rollback', action='store_true',
                       help='回滚迁移')
    parser.add_argument('--migration-id',
                       help='指定迁移ID（用于回滚）')
    
    args = parser.parse_args()
    
    # 如果指定了迁移ID，使用指定的ID
    executor = PermissionMigrationExecutor(args.db_url, args.dry_run)
    if args.migration_id:
        executor.migration_id = args.migration_id
    
    try:
        await executor.connect()
        
        if args.rollback:
            # 执行回滚
            result = await executor.rollback_migration()
            print(f"回滚结果: {result['status']} - {result['message']}")
            return 0 if result['status'] == 'success' else 1
        else:
            # 执行迁移
            summary = await executor.execute_migration(args.mappings_file)
            
            # 保存迁移报告
            files = await executor.save_migration_report(summary)
            
            print(f"\n权限迁移执行完成!")
            print(f"迁移ID: {summary['migration_id']}")
            print(f"成功步骤: {summary['success_count']}/{summary['total_steps']}")
            print("生成的文件:")
            for file_type, file_path in files.items():
                print(f"  {file_type}: {file_path}")
            
            return 0 if summary['failed_count'] == 0 else 1
            
    except Exception as e:
        logger.error(f"迁移执行过程中发生错误: {e}")
        return 1
    finally:
        await executor.disconnect()

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)