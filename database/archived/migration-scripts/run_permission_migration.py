#!/usr/bin/env python3
"""
权限数据迁移主控脚本
统一执行权限迁移的完整流程：分析 -> 验证 -> 执行 -> 验证
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# 导入迁移相关模块
from permission_migration_strategy import PermissionMigrationAnalyzer
from permission_migration_validator import PermissionMigrationValidator
from permission_migration_executor import PermissionMigrationExecutor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('permission_migration_main.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PermissionMigrationController:
    """权限迁移控制器"""
    
    def __init__(self, db_url: str, dry_run: bool = False):
        self.db_url = db_url
        self.dry_run = dry_run
        self.migration_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path("database/migration_output")
        self.output_dir.mkdir(exist_ok=True)
        
    async def run_analysis_phase(self) -> dict:
        """运行分析阶段"""
        logger.info("=" * 60)
        logger.info("阶段 1: 权限数据分析")
        logger.info("=" * 60)
        
        analyzer = PermissionMigrationAnalyzer(self.db_url)
        
        try:
            await analyzer.connect()
            
            # 分析现有权限数据
            analysis_data = await analyzer.analyze_current_permissions()
            
            # 创建权限映射
            await analyzer.create_permission_mappings(analysis_data)
            
            # 保存分析报告
            files = await analyzer.save_analysis_report(analysis_data, str(self.output_dir))
            
            logger.info("✅ 权限数据分析完成")
            logger.info(f"   - API总数: {analyzer.stats.total_apis}")
            logger.info(f"   - 权限映射: {analyzer.stats.mapped_permissions}")
            logger.info(f"   - 高置信度: {analyzer.stats.confidence_high}")
            logger.info(f"   - 低置信度: {analyzer.stats.confidence_low}")
            
            return {
                'status': 'success',
                'files': files,
                'stats': {
                    'total_apis': analyzer.stats.total_apis,
                    'mapped_permissions': analyzer.stats.mapped_permissions,
                    'confidence_high': analyzer.stats.confidence_high,
                    'confidence_low': analyzer.stats.confidence_low
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 权限数据分析失败: {e}")
            return {'status': 'failed', 'error': str(e)}
        finally:
            await analyzer.disconnect()
    
    async def run_pre_migration_validation(self) -> dict:
        """运行迁移前验证"""
        logger.info("=" * 60)
        logger.info("阶段 2: 迁移前验证")
        logger.info("=" * 60)
        
        validator = PermissionMigrationValidator(self.db_url)
        
        try:
            await validator.connect()
            
            # 运行基础验证（检查数据完整性等）
            results = await validator.run_all_validations()
            
            # 保存验证报告
            files = await validator.save_validation_report(str(self.output_dir))
            
            # 统计验证结果
            pass_count = sum(1 for r in results if r.status == "PASS")
            fail_count = sum(1 for r in results if r.status == "FAIL")
            warn_count = sum(1 for r in results if r.status == "WARN")
            
            logger.info("✅ 迁移前验证完成")
            logger.info(f"   - 通过: {pass_count}")
            logger.info(f"   - 失败: {fail_count}")
            logger.info(f"   - 警告: {warn_count}")
            
            return {
                'status': 'success' if fail_count == 0 else 'warning' if warn_count > 0 else 'failed',
                'files': files,
                'stats': {
                    'pass_count': pass_count,
                    'fail_count': fail_count,
                    'warn_count': warn_count
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 迁移前验证失败: {e}")
            return {'status': 'failed', 'error': str(e)}
        finally:
            await validator.disconnect()
    
    async def run_migration_execution(self, mappings_file: str) -> dict:
        """运行迁移执行"""
        logger.info("=" * 60)
        logger.info("阶段 3: 迁移执行")
        logger.info("=" * 60)
        
        executor = PermissionMigrationExecutor(self.db_url, self.dry_run)
        executor.migration_id = self.migration_id
        
        try:
            await executor.connect()
            
            # 执行迁移
            summary = await executor.execute_migration(mappings_file)
            
            # 保存迁移报告
            files = await executor.save_migration_report(summary, str(self.output_dir))
            
            logger.info("✅ 迁移执行完成")
            logger.info(f"   - 成功步骤: {summary['success_count']}")
            logger.info(f"   - 失败步骤: {summary['failed_count']}")
            logger.info(f"   - 总耗时: {summary['total_execution_time_ms']}ms")
            
            return {
                'status': 'success' if summary['failed_count'] == 0 else 'failed',
                'files': files,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"❌ 迁移执行失败: {e}")
            return {'status': 'failed', 'error': str(e)}
        finally:
            await executor.disconnect()
    
    async def run_post_migration_validation(self) -> dict:
        """运行迁移后验证"""
        logger.info("=" * 60)
        logger.info("阶段 4: 迁移后验证")
        logger.info("=" * 60)
        
        validator = PermissionMigrationValidator(self.db_url)
        
        try:
            await validator.connect()
            
            # 运行完整验证
            results = await validator.run_all_validations()
            
            # 保存验证报告
            files = await validator.save_validation_report(str(self.output_dir))
            
            # 统计验证结果
            pass_count = sum(1 for r in results if r.status == "PASS")
            fail_count = sum(1 for r in results if r.status == "FAIL")
            warn_count = sum(1 for r in results if r.status == "WARN")
            
            logger.info("✅ 迁移后验证完成")
            logger.info(f"   - 通过: {pass_count}")
            logger.info(f"   - 失败: {fail_count}")
            logger.info(f"   - 警告: {warn_count}")
            
            return {
                'status': 'success' if fail_count == 0 else 'warning' if warn_count > 0 else 'failed',
                'files': files,
                'stats': {
                    'pass_count': pass_count,
                    'fail_count': fail_count,
                    'warn_count': warn_count
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 迁移后验证失败: {e}")
            return {'status': 'failed', 'error': str(e)}
        finally:
            await validator.disconnect()
    
    async def run_full_migration(self) -> dict:
        """运行完整的迁移流程"""
        logger.info("🚀 开始权限数据迁移流程")
        logger.info(f"   - 迁移ID: {self.migration_id}")
        logger.info(f"   - 模式: {'干运行' if self.dry_run else '实际执行'}")
        logger.info(f"   - 输出目录: {self.output_dir}")
        
        results = {}
        
        # 阶段1: 分析
        analysis_result = await self.run_analysis_phase()
        results['analysis'] = analysis_result
        
        if analysis_result['status'] != 'success':
            logger.error("❌ 分析阶段失败，停止迁移")
            return results
        
        # 获取映射文件路径
        mappings_file = analysis_result['files']['mappings_file']
        
        # 阶段2: 迁移前验证
        pre_validation_result = await self.run_pre_migration_validation()
        results['pre_validation'] = pre_validation_result
        
        if pre_validation_result['status'] == 'failed':
            logger.error("❌ 迁移前验证失败，停止迁移")
            return results
        elif pre_validation_result['status'] == 'warning':
            logger.warning("⚠️ 迁移前验证有警告，请检查后决定是否继续")
            if not self.dry_run:
                response = input("是否继续迁移? (y/N): ")
                if response.lower() != 'y':
                    logger.info("用户取消迁移")
                    return results
        
        # 阶段3: 迁移执行
        migration_result = await self.run_migration_execution(mappings_file)
        results['migration'] = migration_result
        
        if migration_result['status'] != 'success':
            logger.error("❌ 迁移执行失败")
            return results
        
        # 阶段4: 迁移后验证
        post_validation_result = await self.run_post_migration_validation()
        results['post_validation'] = post_validation_result
        
        # 生成最终报告
        await self.generate_final_report(results)
        
        logger.info("🎉 权限数据迁移流程完成")
        return results
    
    async def generate_final_report(self, results: dict):
        """生成最终迁移报告"""
        report = f"""# 权限数据迁移最终报告

## 迁移信息
- **迁移ID**: {self.migration_id}
- **执行时间**: {datetime.now().isoformat()}
- **模式**: {'干运行' if self.dry_run else '实际执行'}

## 执行摘要

### 阶段1: 数据分析
- **状态**: {results.get('analysis', {}).get('status', 'unknown')}
"""
        
        if 'analysis' in results and 'stats' in results['analysis']:
            stats = results['analysis']['stats']
            report += f"""- **API总数**: {stats.get('total_apis', 0)}
- **权限映射**: {stats.get('mapped_permissions', 0)}
- **高置信度**: {stats.get('confidence_high', 0)}
- **低置信度**: {stats.get('confidence_low', 0)}
"""
        
        report += f"""
### 阶段2: 迁移前验证
- **状态**: {results.get('pre_validation', {}).get('status', 'unknown')}
"""
        
        if 'pre_validation' in results and 'stats' in results['pre_validation']:
            stats = results['pre_validation']['stats']
            report += f"""- **通过**: {stats.get('pass_count', 0)}
- **失败**: {stats.get('fail_count', 0)}
- **警告**: {stats.get('warn_count', 0)}
"""
        
        report += f"""
### 阶段3: 迁移执行
- **状态**: {results.get('migration', {}).get('status', 'unknown')}
"""
        
        if 'migration' in results and 'summary' in results['migration']:
            summary = results['migration']['summary']
            report += f"""- **成功步骤**: {summary.get('success_count', 0)}
- **失败步骤**: {summary.get('failed_count', 0)}
- **总耗时**: {summary.get('total_execution_time_ms', 0)}ms
"""
        
        report += f"""
### 阶段4: 迁移后验证
- **状态**: {results.get('post_validation', {}).get('status', 'unknown')}
"""
        
        if 'post_validation' in results and 'stats' in results['post_validation']:
            stats = results['post_validation']['stats']
            report += f"""- **通过**: {stats.get('pass_count', 0)}
- **失败**: {stats.get('fail_count', 0)}
- **警告**: {stats.get('warn_count', 0)}
"""
        
        # 添加后续步骤建议
        overall_success = all(
            results.get(phase, {}).get('status') in ['success', 'warning']
            for phase in ['analysis', 'pre_validation', 'migration', 'post_validation']
        )
        
        if overall_success:
            report += """
## ✅ 迁移成功

### 后续步骤
1. 更新前端权限配置文件
2. 测试所有权限功能
3. 部署到生产环境
4. 监控系统运行状态

### 清理建议
- 备份表可在确认无问题后删除
- 迁移日志建议保留用于审计
"""
        else:
            report += """
## ❌ 迁移存在问题

### 立即行动
1. 检查失败阶段的详细日志
2. 修复问题后重新执行
3. 如需回滚，使用回滚命令

### 回滚命令
```bash
python database/permission_migration_executor.py --rollback --migration-id {migration_id}
```
""".format(migration_id=self.migration_id)
        
        # 保存最终报告
        final_report_file = self.output_dir / f"final_migration_report_{self.migration_id}.md"
        with open(final_report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"最终迁移报告已保存: {final_report_file}")

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='权限数据迁移主控脚本')
    parser.add_argument('--db-url', 
                       default='postgresql://user:password@localhost:5432/database',
                       help='数据库连接URL')
    parser.add_argument('--dry-run', action='store_true',
                       help='干运行模式，不实际执行SQL')
    parser.add_argument('--phase', 
                       choices=['analysis', 'pre-validation', 'migration', 'post-validation', 'full'],
                       default='full',
                       help='执行特定阶段')
    
    args = parser.parse_args()
    
    controller = PermissionMigrationController(args.db_url, args.dry_run)
    
    try:
        if args.phase == 'analysis':
            result = await controller.run_analysis_phase()
        elif args.phase == 'pre-validation':
            result = await controller.run_pre_migration_validation()
        elif args.phase == 'migration':
            # 需要先有映射文件
            mappings_file = input("请输入权限映射文件路径: ")
            result = await controller.run_migration_execution(mappings_file)
        elif args.phase == 'post-validation':
            result = await controller.run_post_migration_validation()
        else:  # full
            result = await controller.run_full_migration()
        
        # 判断整体结果
        if isinstance(result, dict):
            if args.phase == 'full':
                # 检查所有阶段的状态
                all_success = all(
                    phase_result.get('status') in ['success', 'warning']
                    for phase_result in result.values()
                    if isinstance(phase_result, dict)
                )
                return 0 if all_success else 1
            else:
                return 0 if result.get('status') in ['success', 'warning'] else 1
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("用户中断迁移")
        return 1
    except Exception as e:
        logger.error(f"迁移过程中发生未预期错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)