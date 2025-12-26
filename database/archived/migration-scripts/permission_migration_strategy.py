#!/usr/bin/env python3
"""
权限数据迁移策略分析器
分析现有权限数据结构，创建权限迁移映射表，编写数据迁移脚本和验证程序
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import asyncpg
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PermissionMapping:
    """权限映射数据结构"""
    old_permission: str
    new_permission: str
    api_path: str
    http_method: str
    api_group: str
    migration_type: str
    confidence_score: float
    notes: str = ""

@dataclass
class MigrationStats:
    """迁移统计信息"""
    total_apis: int = 0
    total_roles: int = 0
    total_permissions: int = 0
    mapped_permissions: int = 0
    unmapped_permissions: int = 0
    confidence_high: int = 0
    confidence_medium: int = 0
    confidence_low: int = 0

class PermissionMigrationAnalyzer:
    """权限迁移分析器"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.connection: Optional[asyncpg.Connection] = None
        self.mappings: List[PermissionMapping] = []
        self.stats = MigrationStats()
        
        # API路径标准化规则 (v1 -> v2)
        self.path_normalization_rules = {
            # 用户管理
            '/user/list': '/api/v2/users',
            '/user/create': '/api/v2/users',
            '/user/update': '/api/v2/users/{id}',
            '/user/delete': '/api/v2/users/{id}',
            '/user/reset_password': '/api/v2/users/{id}/reset-password',
            '/user/info': '/api/v2/users/{id}',
            
            # 角色管理
            '/role/list': '/api/v2/roles',
            '/role/create': '/api/v2/roles',
            '/role/update': '/api/v2/roles/{id}',
            '/role/delete': '/api/v2/roles/{id}',
            '/role/info': '/api/v2/roles/{id}',
            '/role/permissions': '/api/v2/roles/{id}/permissions',
            
            # 菜单管理
            '/menu/list': '/api/v2/menus',
            '/menu/create': '/api/v2/menus',
            '/menu/update': '/api/v2/menus/{id}',
            '/menu/delete': '/api/v2/menus/{id}',
            '/menu/tree': '/api/v2/menus/tree',
            
            # 部门管理
            '/dept/list': '/api/v2/departments',
            '/dept/create': '/api/v2/departments',
            '/dept/update': '/api/v2/departments/{id}',
            '/dept/delete': '/api/v2/departments/{id}',
            '/dept/tree': '/api/v2/departments/tree',
            
            # 设备管理
            '/device/list': '/api/v2/devices',
            '/device/create': '/api/v2/devices',
            '/device/update': '/api/v2/devices/{id}',
            '/device/delete': '/api/v2/devices/{id}',
            '/device/info': '/api/v2/devices/{id}',
            '/device/search': '/api/v2/devices/search',
            
            # 设备类型
            '/device/type/list': '/api/v2/devices/types',
            '/device/type/create': '/api/v2/devices/types',
            '/device/type/update': '/api/v2/devices/types/{id}',
            '/device/type/delete': '/api/v2/devices/types/{id}',
            
            # 设备监控
            '/device/monitor/data': '/api/v2/devices/{id}/data',
            '/device/monitor/status': '/api/v2/devices/{id}/status',
            '/device/monitor/statistics': '/api/v2/devices/statistics',
            
            # 统计分析
            '/statistics/online-rate': '/api/v2/statistics/online-rate',
            '/statistics/weld-records': '/api/v2/statistics/weld-records',
            '/statistics/weld-time': '/api/v2/statistics/weld-time',
            '/statistics/welding-reports': '/api/v2/statistics/welding-reports',
            '/statistics/dashboard': '/api/v2/statistics/dashboard',
            
            # 仪表板
            '/dashboard/overview': '/api/v2/dashboard/overview',
            '/dashboard/device-stats': '/api/v2/dashboard/device-stats',
            '/dashboard/alarm-stats': '/api/v2/dashboard/alarm-stats',
        }
        
        # API分组映射
        self.api_groups = {
            'users': '系统管理',
            'roles': '系统管理', 
            'menus': '系统管理',
            'departments': '系统管理',
            'devices': '设备管理',
            'statistics': '统计分析',
            'dashboard': '仪表板',
            'ai': 'AI监控'
        }

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

    async def analyze_current_permissions(self) -> Dict:
        """分析现有权限数据结构"""
        logger.info("开始分析现有权限数据结构...")
        
        # 查询现有API数据
        apis_query = """
        SELECT id, path, method, summary, tags, created_at, updated_at
        FROM api
        ORDER BY path, method
        """
        apis = await self.connection.fetch(apis_query)
        self.stats.total_apis = len(apis)
        
        # 查询现有角色数据
        roles_query = """
        SELECT id, name, desc, created_at, updated_at
        FROM role
        ORDER BY name
        """
        roles = await self.connection.fetch(roles_query)
        self.stats.total_roles = len(roles)
        
        # 查询角色-API权限关联
        permissions_query = """
        SELECT r.name as role_name, a.path, a.method, a.summary, a.tags
        FROM role_api ra
        JOIN role r ON ra.role_id = r.id
        JOIN api a ON ra.api_id = a.id
        ORDER BY r.name, a.path, a.method
        """
        permissions = await self.connection.fetch(permissions_query)
        self.stats.total_permissions = len(permissions)
        
        # 查询菜单数据
        menus_query = """
        SELECT id, name, path, menu_type, parent_id, component
        FROM menu
        ORDER BY parent_id, "order"
        """
        menus = await self.connection.fetch(menus_query)
        
        analysis_result = {
            'apis': [dict(api) for api in apis],
            'roles': [dict(role) for role in roles],
            'permissions': [dict(perm) for perm in permissions],
            'menus': [dict(menu) for menu in menus],
            'stats': asdict(self.stats)
        }
        
        logger.info(f"分析完成: {self.stats.total_apis}个API, {self.stats.total_roles}个角色, {self.stats.total_permissions}个权限关联")
        return analysis_result

    def normalize_api_path(self, old_path: str, method: str) -> Tuple[str, float]:
        """标准化API路径"""
        # 直接映射
        if old_path in self.path_normalization_rules:
            return self.path_normalization_rules[old_path], 1.0
        
        # 模式匹配
        confidence = 0.0
        new_path = old_path
        
        # 处理带参数的路径
        if '/{id}' in old_path or '/{' in old_path:
            confidence = 0.9
        elif old_path.startswith('/'):
            # 尝试推断新路径
            parts = old_path.strip('/').split('/')
            if len(parts) >= 2:
                resource = parts[0]
                action = parts[1] if len(parts) > 1 else 'list'
                
                # 根据动作推断RESTful路径
                if action in ['list', 'get']:
                    new_path = f'/api/v2/{resource}s'
                    confidence = 0.8
                elif action == 'create':
                    new_path = f'/api/v2/{resource}s'
                    confidence = 0.8
                elif action in ['update', 'delete', 'info']:
                    new_path = f'/api/v2/{resource}s/{{id}}'
                    confidence = 0.8
                else:
                    new_path = f'/api/v2/{resource}s/{action}'
                    confidence = 0.6
            else:
                confidence = 0.3
        
        return new_path, confidence

    def get_api_group(self, api_path: str) -> str:
        """获取API分组"""
        if api_path.startswith('/api/v2/'):
            parts = api_path.split('/')
            if len(parts) >= 4:
                resource = parts[3]
                return self.api_groups.get(resource, '其他')
        return '未分类'

    async def create_permission_mappings(self, analysis_data: Dict):
        """创建权限映射"""
        logger.info("开始创建权限映射...")
        
        for api in analysis_data['apis']:
            old_path = api['path']
            method = api['method']
            
            # 标准化路径
            new_path, confidence = self.normalize_api_path(old_path, method)
            
            # 创建权限标识
            old_permission = f"{method} {old_path}"
            new_permission = f"{method} {new_path}"
            
            # 确定迁移类型
            migration_type = "direct" if confidence == 1.0 else "inferred" if confidence >= 0.8 else "manual"
            
            # 获取API分组
            api_group = self.get_api_group(new_path)
            
            mapping = PermissionMapping(
                old_permission=old_permission,
                new_permission=new_permission,
                api_path=new_path,
                http_method=method,
                api_group=api_group,
                migration_type=migration_type,
                confidence_score=confidence,
                notes=api.get('summary', '')
            )
            
            self.mappings.append(mapping)
            
            # 更新统计
            if confidence >= 0.9:
                self.stats.confidence_high += 1
            elif confidence >= 0.7:
                self.stats.confidence_medium += 1
            else:
                self.stats.confidence_low += 1
        
        self.stats.mapped_permissions = len(self.mappings)
        logger.info(f"权限映射创建完成: {len(self.mappings)}个映射")

    async def generate_migration_sql(self) -> str:
        """生成迁移SQL脚本"""
        logger.info("生成迁移SQL脚本...")
        
        sql_parts = []
        
        # 1. 创建权限迁移映射表
        sql_parts.append("""
-- =====================================================
-- 权限数据迁移脚本
-- 生成时间: {timestamp}
-- 描述: 将现有权限数据迁移到v2格式
-- =====================================================

-- 1. 创建权限迁移映射表
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_old_permission (old_permission),
    INDEX idx_new_permission (new_permission),
    INDEX idx_migration_batch (migration_batch),
    INDEX idx_migration_type (migration_type),
    INDEX idx_confidence_score (confidence_score)
);

COMMENT ON TABLE t_sys_permission_migrations IS '权限迁移映射表';
COMMENT ON COLUMN t_sys_permission_migrations.old_permission IS '旧权限标识';
COMMENT ON COLUMN t_sys_permission_migrations.new_permission IS '新权限标识';
COMMENT ON COLUMN t_sys_permission_migrations.api_path IS 'API路径';
COMMENT ON COLUMN t_sys_permission_migrations.http_method IS 'HTTP方法';
COMMENT ON COLUMN t_sys_permission_migrations.api_group IS 'API分组';
COMMENT ON COLUMN t_sys_permission_migrations.migration_type IS '迁移类型';
COMMENT ON COLUMN t_sys_permission_migrations.confidence_score IS '置信度分数';
COMMENT ON COLUMN t_sys_permission_migrations.migration_batch IS '迁移批次';
""".format(timestamp=datetime.now().isoformat()))
        
        # 2. 插入权限映射数据
        batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        sql_parts.append(f"\n-- 2. 插入权限映射数据 (批次: {batch_id})")
        
        for mapping in self.mappings:
            sql_parts.append(f"""
INSERT INTO t_sys_permission_migrations 
(old_permission, new_permission, api_path, http_method, api_group, migration_type, confidence_score, migration_batch, notes)
VALUES 
('{mapping.old_permission}', '{mapping.new_permission}', '{mapping.api_path}', 
 '{mapping.http_method}', '{mapping.api_group}', '{mapping.migration_type}', 
 {mapping.confidence_score}, '{batch_id}', '{mapping.notes}');""")
        
        # 3. 创建数据迁移记录表
        sql_parts.append("""
-- 3. 创建数据迁移记录表
CREATE TABLE IF NOT EXISTS t_sys_migration_logs (
    id BIGSERIAL PRIMARY KEY,
    migration_name VARCHAR(200) NOT NULL,
    migration_type VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    description TEXT,
    sql_content LONGTEXT,
    rollback_sql LONGTEXT,
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    execution_time_ms INT,
    executed_at TIMESTAMP NULL,
    rolled_back_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    
    INDEX idx_migration_type (migration_type),
    INDEX idx_version (version),
    INDEX idx_status (status),
    INDEX idx_executed_at (executed_at)
);

COMMENT ON TABLE t_sys_migration_logs IS '数据迁移记录表';
""")
        
        # 4. 创建权限验证函数
        sql_parts.append("""
-- 4. 创建权限验证函数
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
    new_mapping_count BIGINT;
    old_permission_count BIGINT;
BEGIN
    -- 验证API数量
    SELECT COUNT(*) INTO old_api_count FROM api;
    SELECT COUNT(*) INTO new_mapping_count FROM t_sys_permission_migrations;
    
    RETURN QUERY SELECT 
        'api_count'::VARCHAR,
        old_api_count,
        new_mapping_count,
        CASE WHEN old_api_count = new_mapping_count THEN 'PASS' ELSE 'FAIL' END::VARCHAR,
        CASE WHEN old_api_count = new_mapping_count 
             THEN 'API数量匹配' 
             ELSE 'API数量不匹配，需要检查' END::TEXT;
    
    -- 验证权限关联数量
    SELECT COUNT(*) INTO old_permission_count FROM role_api;
    
    RETURN QUERY SELECT 
        'permission_count'::VARCHAR,
        old_permission_count,
        0::BIGINT,
        'INFO'::VARCHAR,
        ('原有权限关联数量: ' || old_permission_count)::TEXT;
        
    -- 验证置信度分布
    RETURN QUERY SELECT 
        'confidence_high'::VARCHAR,
        (SELECT COUNT(*) FROM t_sys_permission_migrations WHERE confidence_score >= 0.9)::BIGINT,
        0::BIGINT,
        'INFO'::VARCHAR,
        '高置信度映射数量'::TEXT;
        
    RETURN QUERY SELECT 
        'confidence_medium'::VARCHAR,
        (SELECT COUNT(*) FROM t_sys_permission_migrations WHERE confidence_score >= 0.7 AND confidence_score < 0.9)::BIGINT,
        0::BIGINT,
        'INFO'::VARCHAR,
        '中等置信度映射数量'::TEXT;
        
    RETURN QUERY SELECT 
        'confidence_low'::VARCHAR,
        (SELECT COUNT(*) FROM t_sys_permission_migrations WHERE confidence_score < 0.7)::BIGINT,
        0::BIGINT,
        'WARN'::VARCHAR,
        '低置信度映射数量，需要人工检查'::TEXT;
END;
$ LANGUAGE plpgsql;
""")
        
        return '\n'.join(sql_parts)

    async def generate_rollback_sql(self) -> str:
        """生成回滚SQL脚本"""
        logger.info("生成回滚SQL脚本...")
        
        rollback_sql = f"""
-- =====================================================
-- 权限数据迁移回滚脚本
-- 生成时间: {datetime.now().isoformat()}
-- 描述: 回滚权限数据迁移操作
-- =====================================================

-- 1. 删除权限迁移映射表
DROP TABLE IF EXISTS t_sys_permission_migrations;

-- 2. 删除数据迁移记录表
DROP TABLE IF EXISTS t_sys_migration_logs;

-- 3. 删除验证函数
DROP FUNCTION IF EXISTS validate_permission_migration();

-- 4. 记录回滚操作
INSERT INTO auditlog (user_id, username, module, summary, method, path, status, response_time)
VALUES (0, 'system', 'migration', '权限迁移回滚', 'ROLLBACK', '/migration/permission', 200, 0);
"""
        return rollback_sql

    async def save_analysis_report(self, analysis_data: Dict, output_dir: str = "database"):
        """保存分析报告"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存详细分析数据
        analysis_file = output_path / f"permission_analysis_{timestamp}.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2, default=str)
        
        # 保存权限映射数据
        mappings_file = output_path / f"permission_mappings_{timestamp}.json"
        mappings_data = [asdict(mapping) for mapping in self.mappings]
        with open(mappings_file, 'w', encoding='utf-8') as f:
            json.dump(mappings_data, f, ensure_ascii=False, indent=2)
        
        # 保存迁移SQL
        migration_sql = await self.generate_migration_sql()
        sql_file = output_path / f"permission_migration_{timestamp}.sql"
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write(migration_sql)
        
        # 保存回滚SQL
        rollback_sql = await self.generate_rollback_sql()
        rollback_file = output_path / f"permission_rollback_{timestamp}.sql"
        with open(rollback_file, 'w', encoding='utf-8') as f:
            f.write(rollback_sql)
        
        # 生成迁移报告
        report = self.generate_migration_report(analysis_data)
        report_file = output_path / f"permission_migration_report_{timestamp}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"分析报告已保存到 {output_path}")
        return {
            'analysis_file': str(analysis_file),
            'mappings_file': str(mappings_file),
            'sql_file': str(sql_file),
            'rollback_file': str(rollback_file),
            'report_file': str(report_file)
        }

    def generate_migration_report(self, analysis_data: Dict) -> str:
        """生成迁移报告"""
        report = f"""# 权限数据迁移分析报告

## 生成时间
{datetime.now().isoformat()}

## 迁移概览

### 数据统计
- **API总数**: {self.stats.total_apis}
- **角色总数**: {self.stats.total_roles}  
- **权限关联总数**: {self.stats.total_permissions}
- **映射权限数**: {self.stats.mapped_permissions}

### 置信度分布
- **高置信度 (≥0.9)**: {self.stats.confidence_high} ({self.stats.confidence_high/len(self.mappings)*100:.1f}%)
- **中等置信度 (0.7-0.9)**: {self.stats.confidence_medium} ({self.stats.confidence_medium/len(self.mappings)*100:.1f}%)
- **低置信度 (<0.7)**: {self.stats.confidence_low} ({self.stats.confidence_low/len(self.mappings)*100:.1f}%)

## 权限映射示例

### 高置信度映射
"""
        
        # 添加高置信度映射示例
        high_confidence = [m for m in self.mappings if m.confidence_score >= 0.9][:10]
        for mapping in high_confidence:
            report += f"- `{mapping.old_permission}` → `{mapping.new_permission}` (置信度: {mapping.confidence_score})\n"
        
        report += "\n### 需要人工检查的映射\n"
        
        # 添加低置信度映射
        low_confidence = [m for m in self.mappings if m.confidence_score < 0.7][:10]
        for mapping in low_confidence:
            report += f"- `{mapping.old_permission}` → `{mapping.new_permission}` (置信度: {mapping.confidence_score})\n"
        
        report += f"""

## API分组统计
"""
        
        # 统计API分组
        group_stats = {}
        for mapping in self.mappings:
            group = mapping.api_group
            if group not in group_stats:
                group_stats[group] = 0
            group_stats[group] += 1
        
        for group, count in sorted(group_stats.items()):
            report += f"- **{group}**: {count}个API\n"
        
        report += f"""

## 迁移建议

### 自动迁移
- 高置信度映射 ({self.stats.confidence_high}个) 可以自动迁移
- 建议先执行高置信度映射的迁移

### 人工检查
- 低置信度映射 ({self.stats.confidence_low}个) 需要人工检查和确认
- 建议在迁移前仔细审查这些映射

### 风险评估
- **低风险**: 高置信度直接映射
- **中风险**: 中等置信度推断映射
- **高风险**: 低置信度映射，需要人工干预

## 执行步骤

1. **备份现有数据**
   ```sql
   -- 备份现有权限数据
   CREATE TABLE api_backup AS SELECT * FROM api;
   CREATE TABLE role_api_backup AS SELECT * FROM role_api;
   ```

2. **执行迁移脚本**
   ```bash
   psql -d database_name -f permission_migration_{{timestamp}}.sql
   ```

3. **验证迁移结果**
   ```sql
   SELECT * FROM validate_permission_migration();
   ```

4. **如需回滚**
   ```bash
   psql -d database_name -f permission_rollback_{{timestamp}}.sql
   ```

## 注意事项

1. 迁移前请务必备份数据库
2. 建议在测试环境先执行迁移
3. 低置信度映射需要人工确认
4. 迁移后需要更新前端权限配置
5. 建议分批次执行迁移，先迁移高置信度映射

## 联系信息

如有问题，请联系开发团队进行支持。
"""
        
        return report

async def main():
    """主函数"""
    # 数据库连接配置 (需要根据实际环境调整)
    db_url = "postgresql://user:password@localhost:5432/database"
    
    analyzer = PermissionMigrationAnalyzer(db_url)
    
    try:
        await analyzer.connect()
        
        # 分析现有权限数据
        analysis_data = await analyzer.analyze_current_permissions()
        
        # 创建权限映射
        await analyzer.create_permission_mappings(analysis_data)
        
        # 保存分析报告和迁移脚本
        files = await analyzer.save_analysis_report(analysis_data)
        
        print("权限迁移策略分析完成!")
        print("生成的文件:")
        for file_type, file_path in files.items():
            print(f"  {file_type}: {file_path}")
            
    except Exception as e:
        logger.error(f"分析过程中发生错误: {e}")
        raise
    finally:
        await analyzer.disconnect()

if __name__ == "__main__":
    asyncio.run(main())