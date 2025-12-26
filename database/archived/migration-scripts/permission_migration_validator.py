#!/usr/bin/env python3
"""
权限数据迁移验证程序
验证迁移过程的数据完整性和正确性
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
        logging.FileHandler('migration_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """验证结果数据结构"""
    check_name: str
    status: str  # PASS, FAIL, WARN, INFO
    expected: Optional[int] = None
    actual: Optional[int] = None
    message: str = ""
    details: Dict = None

class PermissionMigrationValidator:
    """权限迁移验证器"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.connection: Optional[asyncpg.Connection] = None
        self.validation_results: List[ValidationResult] = []
        
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

    async def validate_table_existence(self) -> ValidationResult:
        """验证迁移表是否存在"""
        logger.info("验证迁移表存在性...")
        
        tables_to_check = [
            't_sys_permission_migrations',
            't_sys_migration_logs'
        ]
        
        missing_tables = []
        for table in tables_to_check:
            query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = $1
            )
            """
            exists = await self.connection.fetchval(query, table)
            if not exists:
                missing_tables.append(table)
        
        if missing_tables:
            return ValidationResult(
                check_name="table_existence",
                status="FAIL",
                message=f"缺少迁移表: {', '.join(missing_tables)}"
            )
        else:
            return ValidationResult(
                check_name="table_existence",
                status="PASS",
                message="所有迁移表都存在"
            )

    async def validate_data_integrity(self) -> List[ValidationResult]:
        """验证数据完整性"""
        logger.info("验证数据完整性...")
        results = []
        
        # 1. 验证API数量匹配
        old_api_count = await self.connection.fetchval("SELECT COUNT(*) FROM api")
        new_mapping_count = await self.connection.fetchval(
            "SELECT COUNT(*) FROM t_sys_permission_migrations"
        )
        
        results.append(ValidationResult(
            check_name="api_count_match",
            status="PASS" if old_api_count == new_mapping_count else "FAIL",
            expected=old_api_count,
            actual=new_mapping_count,
            message=f"API数量匹配检查: 原有{old_api_count}个，映射{new_mapping_count}个"
        ))
        
        # 2. 验证权限映射唯一性
        duplicate_old = await self.connection.fetchval("""
            SELECT COUNT(*) FROM (
                SELECT old_permission, COUNT(*) 
                FROM t_sys_permission_migrations 
                GROUP BY old_permission 
                HAVING COUNT(*) > 1
            ) duplicates
        """)
        
        results.append(ValidationResult(
            check_name="old_permission_uniqueness",
            status="PASS" if duplicate_old == 0 else "FAIL",
            actual=duplicate_old,
            message=f"旧权限标识唯一性检查: {duplicate_old}个重复"
        ))
        
        # 3. 验证新权限格式
        invalid_format_count = await self.connection.fetchval("""
            SELECT COUNT(*) FROM t_sys_permission_migrations 
            WHERE new_permission NOT LIKE '%% /api/v2/%%'
        """)
        
        results.append(ValidationResult(
            check_name="new_permission_format",
            status="PASS" if invalid_format_count == 0 else "WARN",
            actual=invalid_format_count,
            message=f"新权限格式检查: {invalid_format_count}个不符合v2格式"
        ))
        
        # 4. 验证置信度分布
        confidence_stats = await self.connection.fetch("""
            SELECT 
                CASE 
                    WHEN confidence_score >= 0.9 THEN 'high'
                    WHEN confidence_score >= 0.7 THEN 'medium'
                    ELSE 'low'
                END as confidence_level,
                COUNT(*) as count
            FROM t_sys_permission_migrations
            GROUP BY 
                CASE 
                    WHEN confidence_score >= 0.9 THEN 'high'
                    WHEN confidence_score >= 0.7 THEN 'medium'
                    ELSE 'low'
                END
        """)
        
        confidence_dict = {row['confidence_level']: row['count'] for row in confidence_stats}
        low_confidence_count = confidence_dict.get('low', 0)
        
        results.append(ValidationResult(
            check_name="confidence_distribution",
            status="WARN" if low_confidence_count > 0 else "PASS",
            details=confidence_dict,
            message=f"置信度分布: 高{confidence_dict.get('high', 0)}个, "
                   f"中{confidence_dict.get('medium', 0)}个, "
                   f"低{confidence_dict.get('low', 0)}个"
        ))
        
        return results

    async def validate_permission_coverage(self) -> List[ValidationResult]:
        """验证权限覆盖度"""
        logger.info("验证权限覆盖度...")
        results = []
        
        # 1. 检查是否有未映射的API
        unmapped_apis = await self.connection.fetch("""
            SELECT a.path, a.method, a.summary
            FROM api a
            LEFT JOIN t_sys_permission_migrations pm 
                ON CONCAT(a.method, ' ', a.path) = pm.old_permission
            WHERE pm.old_permission IS NULL
        """)
        
        results.append(ValidationResult(
            check_name="api_coverage",
            status="PASS" if len(unmapped_apis) == 0 else "WARN",
            actual=len(unmapped_apis),
            message=f"API覆盖度检查: {len(unmapped_apis)}个API未映射",
            details=[dict(api) for api in unmapped_apis] if unmapped_apis else None
        ))
        
        # 2. 检查角色权限覆盖
        role_permission_stats = await self.connection.fetch("""
            SELECT 
                r.name as role_name,
                COUNT(ra.api_id) as old_permission_count,
                COUNT(pm.new_permission) as mapped_permission_count
            FROM role r
            LEFT JOIN role_api ra ON r.id = ra.role_id
            LEFT JOIN api a ON ra.api_id = a.id
            LEFT JOIN t_sys_permission_migrations pm 
                ON CONCAT(a.method, ' ', a.path) = pm.old_permission
            GROUP BY r.id, r.name
            ORDER BY r.name
        """)
        
        coverage_issues = []
        for row in role_permission_stats:
            if row['old_permission_count'] != row['mapped_permission_count']:
                coverage_issues.append({
                    'role': row['role_name'],
                    'old_count': row['old_permission_count'],
                    'mapped_count': row['mapped_permission_count']
                })
        
        results.append(ValidationResult(
            check_name="role_permission_coverage",
            status="PASS" if len(coverage_issues) == 0 else "WARN",
            actual=len(coverage_issues),
            message=f"角色权限覆盖度检查: {len(coverage_issues)}个角色有覆盖问题",
            details=coverage_issues if coverage_issues else None
        ))
        
        return results

    async def validate_api_groups(self) -> ValidationResult:
        """验证API分组"""
        logger.info("验证API分组...")
        
        # 检查API分组分布
        group_stats = await self.connection.fetch("""
            SELECT api_group, COUNT(*) as count
            FROM t_sys_permission_migrations
            GROUP BY api_group
            ORDER BY count DESC
        """)
        
        unclassified_count = 0
        for row in group_stats:
            if row['api_group'] in ['未分类', '其他']:
                unclassified_count += row['count']
        
        return ValidationResult(
            check_name="api_groups",
            status="WARN" if unclassified_count > 0 else "PASS",
            actual=unclassified_count,
            message=f"API分组检查: {unclassified_count}个API未正确分组",
            details={row['api_group']: row['count'] for row in group_stats}
        )

    async def validate_migration_logs(self) -> ValidationResult:
        """验证迁移日志"""
        logger.info("验证迁移日志...")
        
        # 检查迁移日志表结构
        log_count = await self.connection.fetchval(
            "SELECT COUNT(*) FROM t_sys_migration_logs"
        )
        
        return ValidationResult(
            check_name="migration_logs",
            status="INFO",
            actual=log_count,
            message=f"迁移日志表包含{log_count}条记录"
        )

    async def validate_rollback_capability(self) -> ValidationResult:
        """验证回滚能力"""
        logger.info("验证回滚能力...")
        
        # 检查是否有备份表
        backup_tables = await self.connection.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name LIKE '%_backup'
        """)
        
        return ValidationResult(
            check_name="rollback_capability",
            status="PASS" if len(backup_tables) > 0 else "WARN",
            actual=len(backup_tables),
            message=f"回滚能力检查: 发现{len(backup_tables)}个备份表",
            details=[row['table_name'] for row in backup_tables] if backup_tables else None
        )

    async def run_all_validations(self) -> List[ValidationResult]:
        """运行所有验证"""
        logger.info("开始运行所有验证...")
        
        all_results = []
        
        # 1. 表存在性验证
        table_result = await self.validate_table_existence()
        all_results.append(table_result)
        
        if table_result.status == "FAIL":
            logger.error("迁移表不存在，跳过其他验证")
            return all_results
        
        # 2. 数据完整性验证
        integrity_results = await self.validate_data_integrity()
        all_results.extend(integrity_results)
        
        # 3. 权限覆盖度验证
        coverage_results = await self.validate_permission_coverage()
        all_results.extend(coverage_results)
        
        # 4. API分组验证
        group_result = await self.validate_api_groups()
        all_results.append(group_result)
        
        # 5. 迁移日志验证
        log_result = await self.validate_migration_logs()
        all_results.append(log_result)
        
        # 6. 回滚能力验证
        rollback_result = await self.validate_rollback_capability()
        all_results.append(rollback_result)
        
        self.validation_results = all_results
        return all_results

    def generate_validation_report(self) -> str:
        """生成验证报告"""
        logger.info("生成验证报告...")
        
        # 统计验证结果
        pass_count = sum(1 for r in self.validation_results if r.status == "PASS")
        fail_count = sum(1 for r in self.validation_results if r.status == "FAIL")
        warn_count = sum(1 for r in self.validation_results if r.status == "WARN")
        info_count = sum(1 for r in self.validation_results if r.status == "INFO")
        
        report = f"""# 权限数据迁移验证报告

## 验证时间
{datetime.now().isoformat()}

## 验证概览
- **总验证项**: {len(self.validation_results)}
- **通过**: {pass_count} ✅
- **失败**: {fail_count} ❌
- **警告**: {warn_count} ⚠️
- **信息**: {info_count} ℹ️

## 验证结果详情

"""
        
        # 按状态分组显示结果
        for status in ["FAIL", "WARN", "PASS", "INFO"]:
            status_results = [r for r in self.validation_results if r.status == status]
            if not status_results:
                continue
                
            status_emoji = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️"}
            report += f"### {status} {status_emoji[status]}\n\n"
            
            for result in status_results:
                report += f"#### {result.check_name}\n"
                report += f"- **状态**: {result.status}\n"
                report += f"- **消息**: {result.message}\n"
                
                if result.expected is not None:
                    report += f"- **期望值**: {result.expected}\n"
                if result.actual is not None:
                    report += f"- **实际值**: {result.actual}\n"
                
                if result.details:
                    report += f"- **详细信息**:\n"
                    if isinstance(result.details, dict):
                        for key, value in result.details.items():
                            report += f"  - {key}: {value}\n"
                    elif isinstance(result.details, list):
                        for item in result.details[:5]:  # 只显示前5个
                            report += f"  - {item}\n"
                        if len(result.details) > 5:
                            report += f"  - ... 还有{len(result.details) - 5}项\n"
                
                report += "\n"
        
        # 添加建议
        report += "## 建议和后续步骤\n\n"
        
        if fail_count > 0:
            report += "### 🚨 紧急处理\n"
            report += "- 发现严重问题，建议暂停迁移\n"
            report += "- 检查失败项并修复后重新验证\n\n"
        
        if warn_count > 0:
            report += "### ⚠️ 需要关注\n"
            report += "- 发现警告项，建议人工检查\n"
            report += "- 可以继续迁移，但需要额外注意\n\n"
        
        if pass_count == len(self.validation_results):
            report += "### ✅ 验证通过\n"
            report += "- 所有验证项都通过\n"
            report += "- 可以安全进行迁移\n\n"
        
        report += """## 验证命令

### 重新运行验证
```bash
python database/permission_migration_validator.py
```

### 查看详细日志
```bash
tail -f migration_validation.log
```

### 数据库验证查询
```sql
-- 验证权限映射
SELECT * FROM validate_permission_migration();

-- 检查置信度分布
SELECT 
    CASE 
        WHEN confidence_score >= 0.9 THEN 'High'
        WHEN confidence_score >= 0.7 THEN 'Medium'
        ELSE 'Low'
    END as confidence_level,
    COUNT(*) as count,
    ROUND(AVG(confidence_score), 2) as avg_score
FROM t_sys_permission_migrations
GROUP BY 1
ORDER BY avg_score DESC;

-- 检查API分组
SELECT api_group, COUNT(*) as count
FROM t_sys_permission_migrations
GROUP BY api_group
ORDER BY count DESC;
```
"""
        
        return report

    async def save_validation_report(self, output_dir: str = "database"):
        """保存验证报告"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存验证结果JSON
        results_file = output_path / f"validation_results_{timestamp}.json"
        results_data = [asdict(result) for result in self.validation_results]
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2, default=str)
        
        # 保存验证报告
        report = self.generate_validation_report()
        report_file = output_path / f"validation_report_{timestamp}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"验证报告已保存到 {output_path}")
        return {
            'results_file': str(results_file),
            'report_file': str(report_file)
        }

async def main():
    """主函数"""
    # 数据库连接配置 (需要根据实际环境调整)
    db_url = "postgresql://user:password@localhost:5432/database"
    
    validator = PermissionMigrationValidator(db_url)
    
    try:
        await validator.connect()
        
        # 运行所有验证
        results = await validator.run_all_validations()
        
        # 保存验证报告
        files = await validator.save_validation_report()
        
        # 输出验证摘要
        pass_count = sum(1 for r in results if r.status == "PASS")
        fail_count = sum(1 for r in results if r.status == "FAIL")
        warn_count = sum(1 for r in results if r.status == "WARN")
        
        print(f"\n权限迁移验证完成!")
        print(f"验证结果: {pass_count}个通过, {fail_count}个失败, {warn_count}个警告")
        print("生成的文件:")
        for file_type, file_path in files.items():
            print(f"  {file_type}: {file_path}")
        
        if fail_count > 0:
            print("\n⚠️  发现严重问题，建议检查失败项后重新验证")
            return 1
        elif warn_count > 0:
            print("\n⚠️  发现警告项，建议人工检查")
            return 0
        else:
            print("\n✅ 所有验证通过，可以安全进行迁移")
            return 0
            
    except Exception as e:
        logger.error(f"验证过程中发生错误: {e}")
        return 1
    finally:
        await validator.disconnect()

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)