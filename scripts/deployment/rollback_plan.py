#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
回滚方案
提供系统回滚能力，确保升级失败时可以快速恢复

使用方法:
    python scripts/deployment/rollback_plan.py [--check] [--execute] [--restore-backup]

参数:
    --check: 检查回滚条件
    --execute: 执行回滚
    --restore-backup: 从备份恢复数据
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from loguru import logger


class RollbackType(Enum):
    """回滚类型"""
    ARCHITECTURE = "architecture"  # 架构回滚
    DATA = "data"  # 数据回滚
    FULL = "full"  # 完整回滚


@dataclass
class RollbackCheckpoint:
    """回滚检查点"""
    name: str
    timestamp: datetime
    description: str
    data_snapshot: Optional[Dict[str, Any]] = None


class RollbackManager:
    """回滚管理器"""
    
    def __init__(self):
        self.checkpoints: List[RollbackCheckpoint] = []
        self.rollback_history: List[Dict[str, Any]] = []
    
    async def create_checkpoint(self, name: str, description: str) -> RollbackCheckpoint:
        """
        创建回滚检查点
        
        Args:
            name: 检查点名称
            description: 描述
            
        Returns:
            创建的检查点
        """
        logger.info(f"创建回滚检查点: {name}")
        
        # 收集当前状态快照
        snapshot = await self._collect_state_snapshot()
        
        checkpoint = RollbackCheckpoint(
            name=name,
            timestamp=datetime.now(),
            description=description,
            data_snapshot=snapshot
        )
        
        self.checkpoints.append(checkpoint)
        
        # 保存检查点到数据库
        await self._save_checkpoint(checkpoint)
        
        logger.info(f"✅ 检查点创建成功: {name}")
        return checkpoint
    
    async def _collect_state_snapshot(self) -> Dict[str, Any]:
        """收集状态快照"""
        try:
            from app.models.platform_upgrade import AssetCategory, Asset, SignalDefinition
            from app.services.migration_engine import architecture_manager
            
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "architecture": {
                    "use_new_architecture": architecture_manager.use_new_architecture,
                    "dual_write_enabled": architecture_manager.dual_write_enabled
                },
                "data_counts": {
                    "categories": await AssetCategory.all().count(),
                    "assets": await Asset.all().count(),
                    "signals": await SignalDefinition.all().count()
                }
            }
            
            return snapshot
            
        except Exception as e:
            logger.error(f"收集状态快照失败: {e}")
            return {"error": str(e)}
    
    async def _save_checkpoint(self, checkpoint: RollbackCheckpoint):
        """保存检查点到数据库"""
        try:
            from app.models.platform_upgrade import MigrationRecord
            
            record = MigrationRecord(
                migration_name=f"checkpoint_{checkpoint.name}",
                migration_type="checkpoint",
                source_table="system_state",
                target_table="checkpoint_storage",
                status="completed",
                started_at=checkpoint.timestamp,
                completed_at=checkpoint.timestamp,
                error_details=checkpoint.data_snapshot
            )
            await record.save()
            
        except Exception as e:
            logger.warning(f"保存检查点到数据库失败: {e}")
    
    async def check_rollback_conditions(self) -> Dict[str, Any]:
        """
        检查回滚条件
        
        Returns:
            检查结果
        """
        logger.info("检查回滚条件...")
        
        result = {
            "can_rollback": True,
            "checks": [],
            "warnings": []
        }
        
        try:
            from app.models.device import DeviceType, DeviceInfo
            from app.models.platform_upgrade import AssetCategory, Asset
            
            # 检查1: 旧数据是否存在
            old_type_count = await DeviceType.all().count()
            old_device_count = await DeviceInfo.all().count()
            
            if old_type_count == 0 and old_device_count == 0:
                result["warnings"].append("旧系统数据为空，回滚后可能没有数据")
            
            result["checks"].append({
                "name": "旧数据检查",
                "passed": True,
                "details": {
                    "old_types": old_type_count,
                    "old_devices": old_device_count
                }
            })
            
            # 检查2: 新数据状态
            new_category_count = await AssetCategory.all().count()
            new_asset_count = await Asset.all().count()
            
            result["checks"].append({
                "name": "新数据检查",
                "passed": True,
                "details": {
                    "new_categories": new_category_count,
                    "new_assets": new_asset_count
                }
            })
            
            # 检查3: 是否有进行中的迁移
            from app.models.platform_upgrade import MigrationRecord
            
            running_migrations = await MigrationRecord.filter(status="running").count()
            
            if running_migrations > 0:
                result["can_rollback"] = False
                result["checks"].append({
                    "name": "迁移状态检查",
                    "passed": False,
                    "details": {"running_migrations": running_migrations}
                })
            else:
                result["checks"].append({
                    "name": "迁移状态检查",
                    "passed": True,
                    "details": {"running_migrations": 0}
                })
            
            logger.info(f"回滚条件检查完成: {'可以回滚' if result['can_rollback'] else '不能回滚'}")
            
        except Exception as e:
            result["can_rollback"] = False
            result["error"] = str(e)
            logger.error(f"检查回滚条件失败: {e}")
        
        return result
    
    async def execute_rollback(self, rollback_type: RollbackType) -> Dict[str, Any]:
        """
        执行回滚
        
        Args:
            rollback_type: 回滚类型
            
        Returns:
            回滚结果
        """
        logger.warning(f"⚠️ 开始执行回滚: {rollback_type.value}")
        
        result = {
            "rollback_type": rollback_type.value,
            "status": "success",
            "steps": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 检查回滚条件
            check_result = await self.check_rollback_conditions()
            if not check_result["can_rollback"]:
                result["status"] = "failed"
                result["error"] = "回滚条件不满足"
                return result
            
            if rollback_type == RollbackType.ARCHITECTURE:
                # 仅回滚架构配置
                step_result = await self._rollback_architecture()
                result["steps"].append(step_result)
                
            elif rollback_type == RollbackType.DATA:
                # 回滚数据
                step_result = await self._rollback_data()
                result["steps"].append(step_result)
                
            elif rollback_type == RollbackType.FULL:
                # 完整回滚
                arch_result = await self._rollback_architecture()
                result["steps"].append(arch_result)
                
                data_result = await self._rollback_data()
                result["steps"].append(data_result)
            
            # 记录回滚历史
            self.rollback_history.append(result)
            
            # 保存回滚记录
            await self._save_rollback_record(result)
            
            logger.info("✅ 回滚执行完成")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            logger.error(f"❌ 回滚执行失败: {e}")
        
        return result
    
    async def _rollback_architecture(self) -> Dict[str, Any]:
        """回滚架构配置"""
        logger.info("回滚架构配置...")
        
        try:
            from app.services.migration_engine import architecture_manager
            
            # 禁用新架构
            architecture_manager.disable_new_architecture()
            
            # 启用双写模式（保险起见）
            architecture_manager.enable_dual_write()
            
            return {
                "step": "architecture_rollback",
                "status": "success",
                "details": {
                    "use_new_architecture": False,
                    "dual_write_enabled": True
                }
            }
            
        except Exception as e:
            return {
                "step": "architecture_rollback",
                "status": "failed",
                "error": str(e)
            }
    
    async def _rollback_data(self) -> Dict[str, Any]:
        """回滚数据"""
        logger.info("回滚数据...")
        
        try:
            from app.services.migration_engine import migration_rollback
            
            # 回滚资产
            asset_result = await migration_rollback.rollback_migration("device_info")
            
            # 回滚信号定义
            signal_result = await migration_rollback.rollback_migration("device_field")
            
            # 回滚资产类别
            category_result = await migration_rollback.rollback_migration("device_type")
            
            return {
                "step": "data_rollback",
                "status": "success",
                "details": {
                    "assets_rolled_back": asset_result.get("rolled_back_count", 0),
                    "signals_rolled_back": signal_result.get("rolled_back_count", 0),
                    "categories_rolled_back": category_result.get("rolled_back_count", 0)
                }
            }
            
        except Exception as e:
            return {
                "step": "data_rollback",
                "status": "failed",
                "error": str(e)
            }
    
    async def _save_rollback_record(self, result: Dict[str, Any]):
        """保存回滚记录"""
        try:
            from app.models.platform_upgrade import MigrationRecord
            
            record = MigrationRecord(
                migration_name=f"rollback_{result['rollback_type']}",
                migration_type="rollback",
                source_table="new_tables",
                target_table="rollback",
                status=result["status"],
                started_at=datetime.now(),
                completed_at=datetime.now(),
                error_details=result
            )
            await record.save()
            
        except Exception as e:
            logger.warning(f"保存回滚记录失败: {e}")
    
    def get_rollback_history(self) -> List[Dict[str, Any]]:
        """获取回滚历史"""
        return self.rollback_history


# 全局回滚管理器
rollback_manager = RollbackManager()


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="回滚方案")
    parser.add_argument("--check", action="store_true", help="检查回滚条件")
    parser.add_argument("--execute", choices=["architecture", "data", "full"], help="执行回滚")
    parser.add_argument("--create-checkpoint", type=str, help="创建检查点")
    
    args = parser.parse_args()
    
    # 配置日志
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO"
    )
    
    # 初始化数据库
    from tortoise import Tortoise
    from app.settings.config import settings
    
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgres://", 1)
    
    await Tortoise.init(
        db_url=db_url,
        modules={"models": ["app.models.device", "app.models.platform_upgrade"]}
    )
    
    try:
        if args.check:
            result = await rollback_manager.check_rollback_conditions()
            print("\n回滚条件检查结果:")
            print(f"  可以回滚: {'是' if result['can_rollback'] else '否'}")
            for check in result.get("checks", []):
                status = "✅" if check["passed"] else "❌"
                print(f"  {status} {check['name']}: {check.get('details', {})}")
            for warning in result.get("warnings", []):
                print(f"  ⚠️ {warning}")
        
        elif args.execute:
            rollback_type = RollbackType(args.execute)
            result = await rollback_manager.execute_rollback(rollback_type)
            print(f"\n回滚结果: {result['status']}")
            for step in result.get("steps", []):
                status = "✅" if step["status"] == "success" else "❌"
                print(f"  {status} {step['step']}")
        
        elif args.create_checkpoint:
            checkpoint = await rollback_manager.create_checkpoint(
                args.create_checkpoint,
                f"手动创建的检查点: {args.create_checkpoint}"
            )
            print(f"\n✅ 检查点已创建: {checkpoint.name}")
        
        else:
            parser.print_help()
    
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
