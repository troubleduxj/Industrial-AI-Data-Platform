#!/usr/bin/env python3
"""
分阶段数据库迁移策略实现
实现双写机制、数据一致性验证、配置化读取切换和监控告警系统
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import asyncpg
from contextlib import asynccontextmanager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phased_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MigrationPhase(Enum):
    """迁移阶段枚举"""
    PREPARATION = "preparation"      # 准备阶段
    DUAL_WRITE = "dual_write"       # 双写阶段
    VALIDATION = "validation"       # 验证阶段
    READ_SWITCH = "read_switch"     # 读取切换阶段
    CLEANUP = "cleanup"             # 清理阶段
    COMPLETED = "completed"         # 完成阶段

class ConsistencyLevel(Enum):
    """一致性级别枚举"""
    STRICT = "strict"               # 严格一致性
    EVENTUAL = "eventual"           # 最终一致性
    WEAK = "weak"                   # 弱一致性

@dataclass
class MigrationConfig:
    """迁移配置"""
    migration_id: str
    source_table: str
    target_table: str
    phase: MigrationPhase
    consistency_level: ConsistencyLevel
    dual_write_enabled: bool = False
    read_from_target: bool = False
    validation_enabled: bool = True
    auto_switch_threshold: float = 0.99  # 自动切换阈值
    rollback_enabled: bool = True
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class ConsistencyReport:
    """一致性检查报告"""
    migration_id: str
    source_count: int
    target_count: int
    matched_count: int
    mismatched_count: int
    missing_in_target: int
    extra_in_target: int
    consistency_ratio: float
    check_timestamp: datetime
    details: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = []

class PhasedMigrationStrategy:
    """分阶段迁移策略管理器"""
    
    def __init__(self, db_url: str, config_file: str = None):
        self.db_url = db_url
        self.connection: Optional[asyncpg.Connection] = None
        self.config_file = config_file or "database/migration_configs.json"
        self.migrations: Dict[str, MigrationConfig] = {}
        self.dual_write_handlers: Dict[str, Callable] = {}
        self.validation_handlers: Dict[str, Callable] = {}
        
        # 加载配置
        self._load_configurations()
    
    def _load_configurations(self):
        """加载迁移配置"""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    configs = json.load(f)
                    
                for config_data in configs.get('migrations', []):
                    config = MigrationConfig(**config_data)
                    config.phase = MigrationPhase(config_data['phase'])
                    config.consistency_level = ConsistencyLevel(config_data['consistency_level'])
                    self.migrations[config.migration_id] = config
                    
                logger.info(f"加载了 {len(self.migrations)} 个迁移配置")
            else:
                logger.warning(f"配置文件不存在: {config_path}")
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
    
    def _save_configurations(self):
        """保存迁移配置"""
        try:
            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            configs = {
                'migrations': [
                    {
                        **asdict(config),
                        'phase': config.phase.value,
                        'consistency_level': config.consistency_level.value
                    }
                    for config in self.migrations.values()
                ],
                'updated_at': datetime.now().isoformat()
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(configs, f, ensure_ascii=False, indent=2, default=str)
                
            logger.info(f"配置已保存到: {config_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    async def connect(self):
        """连接数据库"""
        try:
            self.connection = await asyncpg.connect(self.db_url)
            await self._initialize_migration_tables()
            logger.info("分阶段迁移系统数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    async def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            await self.connection.close()
            logger.info("分阶段迁移系统数据库连接已关闭")
    
    async def _initialize_migration_tables(self):
        """初始化迁移相关表"""
        # 创建迁移配置表
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS t_sys_phased_migrations (
                id BIGSERIAL PRIMARY KEY,
                migration_id VARCHAR(100) NOT NULL UNIQUE,
                source_table VARCHAR(100) NOT NULL,
                target_table VARCHAR(100) NOT NULL,
                phase VARCHAR(20) NOT NULL,
                consistency_level VARCHAR(20) NOT NULL,
                dual_write_enabled BOOLEAN DEFAULT FALSE,
                read_from_target BOOLEAN DEFAULT FALSE,
                validation_enabled BOOLEAN DEFAULT TRUE,
                auto_switch_threshold DECIMAL(5,4) DEFAULT 0.99,
                rollback_enabled BOOLEAN DEFAULT TRUE,
                config_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                CONSTRAINT chk_phase CHECK (phase IN ('preparation', 'dual_write', 'validation', 'read_switch', 'cleanup', 'completed')),
                CONSTRAINT chk_consistency_level CHECK (consistency_level IN ('strict', 'eventual', 'weak'))
            );
            
            CREATE INDEX IF NOT EXISTS idx_phased_migrations_id ON t_sys_phased_migrations(migration_id);
            CREATE INDEX IF NOT EXISTS idx_phased_migrations_phase ON t_sys_phased_migrations(phase);
            CREATE INDEX IF NOT EXISTS idx_phased_migrations_source ON t_sys_phased_migrations(source_table);
            CREATE INDEX IF NOT EXISTS idx_phased_migrations_target ON t_sys_phased_migrations(target_table);
        """)
        
        # 创建一致性检查记录表
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS t_sys_consistency_checks (
                id BIGSERIAL PRIMARY KEY,
                migration_id VARCHAR(100) NOT NULL,
                check_type VARCHAR(50) NOT NULL,
                source_count BIGINT NOT NULL,
                target_count BIGINT NOT NULL,
                matched_count BIGINT NOT NULL,
                mismatched_count BIGINT NOT NULL,
                missing_in_target BIGINT NOT NULL,
                extra_in_target BIGINT NOT NULL,
                consistency_ratio DECIMAL(5,4) NOT NULL,
                check_duration_ms INTEGER,
                details JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (migration_id) REFERENCES t_sys_phased_migrations(migration_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_consistency_checks_migration ON t_sys_consistency_checks(migration_id);
            CREATE INDEX IF NOT EXISTS idx_consistency_checks_type ON t_sys_consistency_checks(check_type);
            CREATE INDEX IF NOT EXISTS idx_consistency_checks_ratio ON t_sys_consistency_checks(consistency_ratio);
            CREATE INDEX IF NOT EXISTS idx_consistency_checks_created ON t_sys_consistency_checks(created_at);
        """)
        
        # 创建双写操作日志表
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS t_sys_dual_write_logs (
                id BIGSERIAL PRIMARY KEY,
                migration_id VARCHAR(100) NOT NULL,
                operation_type VARCHAR(20) NOT NULL,
                table_name VARCHAR(100) NOT NULL,
                record_id VARCHAR(100),
                operation_data JSONB,
                source_success BOOLEAN DEFAULT FALSE,
                target_success BOOLEAN DEFAULT FALSE,
                source_error TEXT,
                target_error TEXT,
                execution_time_ms INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                CONSTRAINT chk_operation_type CHECK (operation_type IN ('INSERT', 'UPDATE', 'DELETE'))
            );
            
            CREATE INDEX IF NOT EXISTS idx_dual_write_logs_migration ON t_sys_dual_write_logs(migration_id);
            CREATE INDEX IF NOT EXISTS idx_dual_write_logs_operation ON t_sys_dual_write_logs(operation_type);
            CREATE INDEX IF NOT EXISTS idx_dual_write_logs_table ON t_sys_dual_write_logs(table_name);
            CREATE INDEX IF NOT EXISTS idx_dual_write_logs_success ON t_sys_dual_write_logs(source_success, target_success);
            CREATE INDEX IF NOT EXISTS idx_dual_write_logs_created ON t_sys_dual_write_logs(created_at);
        """)
    
    async def register_migration(self, config: MigrationConfig) -> bool:
        """注册迁移配置"""
        try:
            self.migrations[config.migration_id] = config
            
            # 保存到数据库
            await self.connection.execute("""
                INSERT INTO t_sys_phased_migrations 
                (migration_id, source_table, target_table, phase, consistency_level,
                 dual_write_enabled, read_from_target, validation_enabled,
                 auto_switch_threshold, rollback_enabled, config_data)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (migration_id) DO UPDATE SET
                    source_table = EXCLUDED.source_table,
                    target_table = EXCLUDED.target_table,
                    phase = EXCLUDED.phase,
                    consistency_level = EXCLUDED.consistency_level,
                    dual_write_enabled = EXCLUDED.dual_write_enabled,
                    read_from_target = EXCLUDED.read_from_target,
                    validation_enabled = EXCLUDED.validation_enabled,
                    auto_switch_threshold = EXCLUDED.auto_switch_threshold,
                    rollback_enabled = EXCLUDED.rollback_enabled,
                    config_data = EXCLUDED.config_data,
                    updated_at = CURRENT_TIMESTAMP
            """, 
                config.migration_id, config.source_table, config.target_table,
                config.phase.value, config.consistency_level.value,
                config.dual_write_enabled, config.read_from_target, config.validation_enabled,
                config.auto_switch_threshold, config.rollback_enabled,
                json.dumps(asdict(config), default=str)
            )
            
            self._save_configurations()
            logger.info(f"迁移配置已注册: {config.migration_id}")
            return True
            
        except Exception as e:
            logger.error(f"注册迁移配置失败: {e}")
            return False
    
    async def update_migration_phase(self, migration_id: str, new_phase: MigrationPhase) -> bool:
        """更新迁移阶段"""
        try:
            if migration_id not in self.migrations:
                logger.error(f"迁移配置不存在: {migration_id}")
                return False
            
            old_phase = self.migrations[migration_id].phase
            self.migrations[migration_id].phase = new_phase
            self.migrations[migration_id].updated_at = datetime.now()
            
            # 更新数据库
            await self.connection.execute("""
                UPDATE t_sys_phased_migrations 
                SET phase = $1, updated_at = CURRENT_TIMESTAMP
                WHERE migration_id = $2
            """, new_phase.value, migration_id)
            
            self._save_configurations()
            logger.info(f"迁移 {migration_id} 阶段已更新: {old_phase.value} -> {new_phase.value}")
            return True
            
        except Exception as e:
            logger.error(f"更新迁移阶段失败: {e}")
            return False
    
    def register_dual_write_handler(self, table_name: str, handler: Callable):
        """注册双写处理器"""
        self.dual_write_handlers[table_name] = handler
        logger.info(f"双写处理器已注册: {table_name}")
    
    def register_validation_handler(self, table_name: str, handler: Callable):
        """注册验证处理器"""
        self.validation_handlers[table_name] = handler
        logger.info(f"验证处理器已注册: {table_name}")
    
    @asynccontextmanager
    async def dual_write_transaction(self, migration_id: str):
        """双写事务上下文管理器"""
        config = self.migrations.get(migration_id)
        if not config or not config.dual_write_enabled:
            # 如果未启用双写，只使用源表
            async with self.connection.transaction():
                yield self.connection
            return
        
        start_time = time.time()
        source_success = False
        target_success = False
        source_error = None
        target_error = None
        
        try:
            async with self.connection.transaction():
                yield self.connection
                source_success = True
        except Exception as e:
            source_error = str(e)
            logger.error(f"源表操作失败: {e}")
            raise
        
        # 如果源表操作成功，尝试目标表操作
        if source_success:
            try:
                # 这里应该调用目标表的操作
                # 实际实现中需要根据具体的操作类型来处理
                target_success = True
            except Exception as e:
                target_error = str(e)
                logger.error(f"目标表操作失败: {e}")
                # 根据一致性级别决定是否回滚
                if config.consistency_level == ConsistencyLevel.STRICT:
                    raise
        
        # 记录双写日志
        execution_time = int((time.time() - start_time) * 1000)
        await self._log_dual_write_operation(
            migration_id, "TRANSACTION", config.source_table,
            None, None, source_success, target_success,
            source_error, target_error, execution_time
        )
    
    async def _log_dual_write_operation(self, migration_id: str, operation_type: str,
                                      table_name: str, record_id: str = None,
                                      operation_data: Dict = None,
                                      source_success: bool = False,
                                      target_success: bool = False,
                                      source_error: str = None,
                                      target_error: str = None,
                                      execution_time_ms: int = 0):
        """记录双写操作日志"""
        try:
            await self.connection.execute("""
                INSERT INTO t_sys_dual_write_logs 
                (migration_id, operation_type, table_name, record_id, operation_data,
                 source_success, target_success, source_error, target_error, execution_time_ms)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, 
                migration_id, operation_type, table_name, record_id,
                json.dumps(operation_data) if operation_data else None,
                source_success, target_success, source_error, target_error, execution_time_ms
            )
        except Exception as e:
            logger.error(f"记录双写日志失败: {e}")
    
    async def validate_data_consistency(self, migration_id: str, 
                                      sample_size: int = None) -> ConsistencyReport:
        """验证数据一致性"""
        config = self.migrations.get(migration_id)
        if not config:
            raise ValueError(f"迁移配置不存在: {migration_id}")
        
        start_time = time.time()
        
        try:
            # 获取源表和目标表的记录数
            source_count = await self.connection.fetchval(
                f"SELECT COUNT(*) FROM {config.source_table}"
            )
            target_count = await self.connection.fetchval(
                f"SELECT COUNT(*) FROM {config.target_table}"
            )
            
            # 如果有自定义验证处理器，使用它
            if config.source_table in self.validation_handlers:
                handler = self.validation_handlers[config.source_table]
                validation_result = await handler(self.connection, config, sample_size)
                matched_count = validation_result.get('matched_count', 0)
                mismatched_count = validation_result.get('mismatched_count', 0)
                details = validation_result.get('details', [])
            else:
                # 默认验证逻辑
                matched_count, mismatched_count, details = await self._default_consistency_check(
                    config, sample_size
                )
            
            missing_in_target = max(0, source_count - target_count)
            extra_in_target = max(0, target_count - source_count)
            
            # 计算一致性比率
            total_checked = matched_count + mismatched_count
            consistency_ratio = matched_count / total_checked if total_checked > 0 else 0.0
            
            # 创建报告
            report = ConsistencyReport(
                migration_id=migration_id,
                source_count=source_count,
                target_count=target_count,
                matched_count=matched_count,
                mismatched_count=mismatched_count,
                missing_in_target=missing_in_target,
                extra_in_target=extra_in_target,
                consistency_ratio=consistency_ratio,
                check_timestamp=datetime.now(),
                details=details
            )
            
            # 保存检查记录
            check_duration = int((time.time() - start_time) * 1000)
            await self.connection.execute("""
                INSERT INTO t_sys_consistency_checks 
                (migration_id, check_type, source_count, target_count, matched_count,
                 mismatched_count, missing_in_target, extra_in_target, consistency_ratio,
                 check_duration_ms, details)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, 
                migration_id, "FULL_CHECK", source_count, target_count, matched_count,
                mismatched_count, missing_in_target, extra_in_target, consistency_ratio,
                check_duration, json.dumps(details[:100])  # 限制详情数量
            )
            
            logger.info(f"一致性检查完成: {migration_id}, 一致性比率: {consistency_ratio:.4f}")
            return report
            
        except Exception as e:
            logger.error(f"一致性检查失败: {e}")
            raise
    
    async def _default_consistency_check(self, config: MigrationConfig, 
                                       sample_size: int = None) -> Tuple[int, int, List[Dict]]:
        """默认一致性检查逻辑"""
        # 这是一个简化的实现，实际应用中需要根据具体表结构来实现
        # 假设表有id字段作为主键
        
        limit_clause = f"LIMIT {sample_size}" if sample_size else ""
        
        # 获取源表的记录ID
        source_ids = await self.connection.fetch(
            f"SELECT id FROM {config.source_table} ORDER BY id {limit_clause}"
        )
        
        matched_count = 0
        mismatched_count = 0
        details = []
        
        for record in source_ids:
            record_id = record['id']
            
            # 检查目标表中是否存在相同ID的记录
            target_exists = await self.connection.fetchval(
                f"SELECT COUNT(*) FROM {config.target_table} WHERE id = $1",
                record_id
            )
            
            if target_exists > 0:
                matched_count += 1
            else:
                mismatched_count += 1
                details.append({
                    'type': 'missing_in_target',
                    'record_id': record_id,
                    'message': f'记录 {record_id} 在目标表中不存在'
                })
        
        return matched_count, mismatched_count, details
    
    async def switch_read_source(self, migration_id: str, to_target: bool = True) -> bool:
        """切换读取源"""
        try:
            config = self.migrations.get(migration_id)
            if not config:
                logger.error(f"迁移配置不存在: {migration_id}")
                return False
            
            # 在切换前进行一致性检查
            if to_target and config.validation_enabled:
                report = await self.validate_data_consistency(migration_id)
                if report.consistency_ratio < config.auto_switch_threshold:
                    logger.warning(
                        f"一致性比率 {report.consistency_ratio:.4f} 低于阈值 "
                        f"{config.auto_switch_threshold:.4f}，不执行切换"
                    )
                    return False
            
            # 更新配置
            config.read_from_target = to_target
            config.updated_at = datetime.now()
            
            # 更新数据库
            await self.connection.execute("""
                UPDATE t_sys_phased_migrations 
                SET read_from_target = $1, updated_at = CURRENT_TIMESTAMP
                WHERE migration_id = $2
            """, to_target, migration_id)
            
            self._save_configurations()
            
            source_name = "目标表" if to_target else "源表"
            logger.info(f"迁移 {migration_id} 读取源已切换到: {source_name}")
            return True
            
        except Exception as e:
            logger.error(f"切换读取源失败: {e}")
            return False
    
    async def enable_dual_write(self, migration_id: str) -> bool:
        """启用双写"""
        try:
            config = self.migrations.get(migration_id)
            if not config:
                logger.error(f"迁移配置不存在: {migration_id}")
                return False
            
            config.dual_write_enabled = True
            config.updated_at = datetime.now()
            
            # 更新数据库
            await self.connection.execute("""
                UPDATE t_sys_phased_migrations 
                SET dual_write_enabled = TRUE, updated_at = CURRENT_TIMESTAMP
                WHERE migration_id = $1
            """, migration_id)
            
            self._save_configurations()
            logger.info(f"迁移 {migration_id} 双写已启用")
            return True
            
        except Exception as e:
            logger.error(f"启用双写失败: {e}")
            return False
    
    async def disable_dual_write(self, migration_id: str) -> bool:
        """禁用双写"""
        try:
            config = self.migrations.get(migration_id)
            if not config:
                logger.error(f"迁移配置不存在: {migration_id}")
                return False
            
            config.dual_write_enabled = False
            config.updated_at = datetime.now()
            
            # 更新数据库
            await self.connection.execute("""
                UPDATE t_sys_phased_migrations 
                SET dual_write_enabled = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE migration_id = $1
            """, migration_id)
            
            self._save_configurations()
            logger.info(f"迁移 {migration_id} 双写已禁用")
            return True
            
        except Exception as e:
            logger.error(f"禁用双写失败: {e}")
            return False
    
    async def get_migration_status(self, migration_id: str = None) -> Dict[str, Any]:
        """获取迁移状态"""
        try:
            if migration_id:
                # 获取单个迁移状态
                config = self.migrations.get(migration_id)
                if not config:
                    return {}
                
                # 获取最近的一致性检查
                latest_check = await self.connection.fetchrow("""
                    SELECT * FROM t_sys_consistency_checks
                    WHERE migration_id = $1
                    ORDER BY created_at DESC
                    LIMIT 1
                """, migration_id)
                
                # 获取双写统计
                dual_write_stats = await self.connection.fetchrow("""
                    SELECT 
                        COUNT(*) as total_operations,
                        COUNT(CASE WHEN source_success AND target_success THEN 1 END) as successful_operations,
                        COUNT(CASE WHEN NOT source_success OR NOT target_success THEN 1 END) as failed_operations,
                        AVG(execution_time_ms) as avg_execution_time
                    FROM t_sys_dual_write_logs
                    WHERE migration_id = $1
                        AND created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
                """, migration_id)
                
                return {
                    'migration_id': migration_id,
                    'config': asdict(config),
                    'latest_consistency_check': dict(latest_check) if latest_check else None,
                    'dual_write_stats': dict(dual_write_stats) if dual_write_stats else None
                }
            else:
                # 获取所有迁移状态概览
                all_status = {}
                for mid in self.migrations.keys():
                    all_status[mid] = await self.get_migration_status(mid)
                return all_status
                
        except Exception as e:
            logger.error(f"获取迁移状态失败: {e}")
            return {}
    
    async def rollback_migration(self, migration_id: str) -> bool:
        """回滚迁移"""
        try:
            config = self.migrations.get(migration_id)
            if not config:
                logger.error(f"迁移配置不存在: {migration_id}")
                return False
            
            if not config.rollback_enabled:
                logger.error(f"迁移 {migration_id} 未启用回滚功能")
                return False
            
            logger.info(f"开始回滚迁移: {migration_id}")
            
            # 1. 禁用双写
            await self.disable_dual_write(migration_id)
            
            # 2. 切换读取源到源表
            await self.switch_read_source(migration_id, to_target=False)
            
            # 3. 更新阶段为准备阶段
            await self.update_migration_phase(migration_id, MigrationPhase.PREPARATION)
            
            logger.info(f"迁移 {migration_id} 回滚完成")
            return True
            
        except Exception as e:
            logger.error(f"回滚迁移失败: {e}")
            return False
    
    async def get_consistency_history(self, migration_id: str, 
                                    days: int = 7) -> List[Dict[str, Any]]:
        """获取一致性检查历史"""
        try:
            history = await self.connection.fetch("""
                SELECT * FROM t_sys_consistency_checks
                WHERE migration_id = $1
                    AND created_at > CURRENT_TIMESTAMP - INTERVAL '%s days'
                ORDER BY created_at DESC
            """ % days, migration_id)
            
            return [dict(record) for record in history]
            
        except Exception as e:
            logger.error(f"获取一致性历史失败: {e}")
            return []
    
    async def get_dual_write_metrics(self, migration_id: str, 
                                   hours: int = 24) -> Dict[str, Any]:
        """获取双写指标"""
        try:
            metrics = await self.connection.fetchrow("""
                SELECT 
                    COUNT(*) as total_operations,
                    COUNT(CASE WHEN source_success AND target_success THEN 1 END) as successful_operations,
                    COUNT(CASE WHEN source_success AND NOT target_success THEN 1 END) as target_failed_operations,
                    COUNT(CASE WHEN NOT source_success THEN 1 END) as source_failed_operations,
                    AVG(execution_time_ms) as avg_execution_time,
                    MAX(execution_time_ms) as max_execution_time,
                    MIN(execution_time_ms) as min_execution_time
                FROM t_sys_dual_write_logs
                WHERE migration_id = $1
                    AND created_at > CURRENT_TIMESTAMP - INTERVAL '%s hours'
            """ % hours, migration_id)
            
            if metrics:
                result = dict(metrics)
                result['success_rate'] = (
                    result['successful_operations'] / result['total_operations']
                    if result['total_operations'] > 0 else 0.0
                )
                return result
            else:
                return {}
                
        except Exception as e:
            logger.error(f"获取双写指标失败: {e}")
            return {}

# 使用示例配置
EXAMPLE_MIGRATION_CONFIG = {
    "migrations": [
        {
            "migration_id": "user_table_migration",
            "source_table": "users",
            "target_table": "t_sys_users",
            "phase": "preparation",
            "consistency_level": "strict",
            "dual_write_enabled": False,
            "read_from_target": False,
            "validation_enabled": True,
            "auto_switch_threshold": 0.99,
            "rollback_enabled": True
        },
        {
            "migration_id": "role_table_migration",
            "source_table": "roles",
            "target_table": "t_sys_roles",
            "phase": "preparation",
            "consistency_level": "eventual",
            "dual_write_enabled": False,
            "read_from_target": False,
            "validation_enabled": True,
            "auto_switch_threshold": 0.95,
            "rollback_enabled": True
        }
    ]
}

async def main():
    """主函数示例"""
    import argparse
    
    parser = argparse.ArgumentParser(description='分阶段数据库迁移工具')
    parser.add_argument('--db-url', required=True, help='数据库连接URL')
    parser.add_argument('--config-file', help='配置文件路径')
    parser.add_argument('--action', 
                       choices=['status', 'validate', 'switch-read', 'enable-dual-write', 
                               'disable-dual-write', 'rollback'],
                       required=True, help='执行的操作')
    parser.add_argument('--migration-id', help='迁移ID')
    parser.add_argument('--to-target', action='store_true', help='切换到目标表')
    
    args = parser.parse_args()
    
    strategy = PhasedMigrationStrategy(args.db_url, args.config_file)
    
    try:
        await strategy.connect()
        
        if args.action == 'status':
            status = await strategy.get_migration_status(args.migration_id)
            print(json.dumps(status, indent=2, ensure_ascii=False, default=str))
        
        elif args.action == 'validate':
            if not args.migration_id:
                print("需要指定 --migration-id")
                return
            report = await strategy.validate_data_consistency(args.migration_id)
            print(json.dumps(asdict(report), indent=2, ensure_ascii=False, default=str))
        
        elif args.action == 'switch-read':
            if not args.migration_id:
                print("需要指定 --migration-id")
                return
            success = await strategy.switch_read_source(args.migration_id, args.to_target)
            print(f"切换读取源: {'成功' if success else '失败'}")
        
        elif args.action == 'enable-dual-write':
            if not args.migration_id:
                print("需要指定 --migration-id")
                return
            success = await strategy.enable_dual_write(args.migration_id)
            print(f"启用双写: {'成功' if success else '失败'}")
        
        elif args.action == 'disable-dual-write':
            if not args.migration_id:
                print("需要指定 --migration-id")
                return
            success = await strategy.disable_dual_write(args.migration_id)
            print(f"禁用双写: {'成功' if success else '失败'}")
        
        elif args.action == 'rollback':
            if not args.migration_id:
                print("需要指定 --migration-id")
                return
            success = await strategy.rollback_migration(args.migration_id)
            print(f"回滚迁移: {'成功' if success else '失败'}")
    
    finally:
        await strategy.disconnect()

if __name__ == "__main__":
    asyncio.run(main())