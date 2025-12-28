# 数据迁移引擎 - 从DeviceMonitorV4到工业AI数据平台
# 实现渐进式升级，保证业务连续性

"""
迁移策略：
1. 保留旧表只读，新数据写入新表
2. 双写期间保证数据一致性  
3. 分阶段切换，降低风险
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger


# =====================================================
# 表结构映射关系
# =====================================================

MIGRATION_MAPPING = {
    # 设备类型 -> 资产类别
    "t_device_type": {
        "target": "t_asset_category",
        "field_mapping": {
            "type_code": "code",
            "type_name": "name", 
            "description": "description",
            "tdengine_stable_name": "tdengine_stable_prefix",
            "is_active": "is_active",
            "icon": "icon",
            "device_count": "asset_count"
        },
        "new_fields": {
            "industry": "manufacturing",  # 默认值
            "tdengine_database": "devicemonitor"
        }
    },
    
    # 设备信息 -> 资产
    "t_device_info": {
        "target": "t_asset", 
        "field_mapping": {
            "device_code": "code",
            "device_name": "name",
            "device_type": "category_id",  # 需要关联查询
            "install_location": "location",
            "manufacturer": "manufacturer",
            "device_model": "model",
            "install_date": "install_date",
            "attributes": "attributes",
            "team_name": "team",
            "is_locked": "is_locked"
        },
        "status_mapping": {
            "default": "offline"
        }
    },
    
    # 设备字段 -> 信号定义
    "t_device_field": {
        "target": "t_signal_definition",
        "field_mapping": {
            "field_code": "code",
            "field_name": "name",
            "device_type_code": "category_id",  # 需要关联查询
            "field_type": "data_type",
            "unit": "unit",
            "is_monitoring_key": "is_realtime",
            "is_ai_feature": "is_feature",
            "is_alarm_enabled": "is_alarm_enabled",
            "data_range": "value_range",
            "alarm_threshold": "alarm_threshold",
            "display_config": "display_config",
            "sort_order": "sort_order",
            "field_group": "field_group",
            "is_default_visible": "is_default_visible",
            "aggregation_method": "aggregation_method",
            "is_active": "is_active"
        },
        "new_fields": {
            "is_stored": True
        }
    }
}


class MigrationEngine:
    """数据迁移引擎"""
    
    def __init__(self):
        self.mapping = MIGRATION_MAPPING
    
    async def migrate_device_types(self) -> Dict[str, Any]:
        """
        迁移设备类型到资产类别
        
        Returns:
            迁移结果统计
        """
        from app.models.device import DeviceType
        from app.models.platform_upgrade import AssetCategory, MigrationRecord
        
        logger.info("开始迁移设备类型...")
        
        # 创建迁移记录
        migration_record = MigrationRecord(
            migration_name="migrate_device_types",
            migration_type="device_type",
            source_table="t_device_type",
            target_table="t_asset_category",
            status="running",
            started_at=datetime.now()
        )
        await migration_record.save()
        
        try:
            # 1. 读取旧数据
            old_types = await DeviceType.all()
            migration_record.total_records = len(old_types)
            await migration_record.save()
            
            migrated = 0
            failed = 0
            skipped = 0
            errors = []
            
            # 2. 转换并插入新表
            for old_type in old_types:
                try:
                    # 检查是否已存在
                    existing = await AssetCategory.get_or_none(code=old_type.type_code)
                    if existing:
                        logger.info(f"跳过已存在的类别: {old_type.type_code}")
                        skipped += 1
                        continue
                    
                    new_category = AssetCategory(
                        code=old_type.type_code,
                        name=old_type.type_name,
                        description=old_type.description,
                        industry="manufacturing",  # 默认行业
                        icon=old_type.icon,
                        tdengine_database="devicemonitor",
                        tdengine_stable_prefix=old_type.tdengine_stable_name or f"raw_{old_type.type_code}",
                        is_active=old_type.is_active,
                        asset_count=old_type.device_count
                    )
                    await new_category.save()
                    migrated += 1
                    
                except Exception as e:
                    logger.error(f"迁移设备类型失败 {old_type.type_code}: {e}")
                    failed += 1
                    errors.append({
                        "type_code": old_type.type_code,
                        "error": str(e)
                    })
            
            # 更新迁移记录
            migration_record.migrated_records = migrated
            migration_record.failed_records = failed
            migration_record.skipped_records = skipped
            migration_record.status = "completed" if failed == 0 else "completed_with_errors"
            migration_record.completed_at = datetime.now()
            migration_record.error_details = {"errors": errors} if errors else None
            await migration_record.save()
            
            logger.info(f"✅ 设备类型迁移完成: 成功{migrated}, 失败{failed}, 跳过{skipped}")
            
            return {
                "total": len(old_types),
                "migrated": migrated,
                "failed": failed,
                "skipped": skipped,
                "errors": errors
            }
            
        except Exception as e:
            migration_record.status = "failed"
            migration_record.error_details = {"error": str(e)}
            migration_record.completed_at = datetime.now()
            await migration_record.save()
            
            logger.error(f"❌ 设备类型迁移失败: {e}")
            raise
    
    async def migrate_device_fields(self) -> Dict[str, Any]:
        """
        迁移设备字段到信号定义
        
        Returns:
            迁移结果统计
        """
        from app.models.device import DeviceField
        from app.models.platform_upgrade import SignalDefinition, AssetCategory, MigrationRecord
        
        logger.info("开始迁移设备字段...")
        
        # 创建迁移记录
        migration_record = MigrationRecord(
            migration_name="migrate_device_fields",
            migration_type="device_field",
            source_table="t_device_field",
            target_table="t_signal_definition",
            status="running",
            started_at=datetime.now()
        )
        await migration_record.save()
        
        try:
            # 1. 建立类别映射
            categories = await AssetCategory.all()
            category_map = {cat.code: cat for cat in categories}
            
            # 2. 读取旧字段
            old_fields = await DeviceField.all()
            migration_record.total_records = len(old_fields)
            await migration_record.save()
            
            migrated = 0
            failed = 0
            skipped = 0
            errors = []
            
            # 3. 转换并插入
            for old_field in old_fields:
                try:
                    category = category_map.get(old_field.device_type_code)
                    if not category:
                        logger.warning(f"跳过字段 {old_field.field_code}，找不到对应类别 {old_field.device_type_code}")
                        skipped += 1
                        continue
                    
                    # 检查是否已存在
                    existing = await SignalDefinition.get_or_none(
                        category=category,
                        code=old_field.field_code
                    )
                    if existing:
                        logger.info(f"跳过已存在的信号: {old_field.field_code}")
                        skipped += 1
                        continue
                    
                    new_signal = SignalDefinition(
                        category=category,
                        code=old_field.field_code,
                        name=old_field.field_name,
                        data_type=self._map_field_type(old_field.field_type),
                        unit=old_field.unit,
                        is_stored=True,
                        is_realtime=old_field.is_monitoring_key,
                        is_feature=old_field.is_ai_feature,
                        is_alarm_enabled=old_field.is_alarm_enabled,
                        value_range=old_field.data_range,
                        alarm_threshold=old_field.alarm_threshold,
                        aggregation_method=old_field.aggregation_method,
                        display_config=old_field.display_config,
                        sort_order=old_field.sort_order,
                        field_group=old_field.field_group or "default",
                        is_default_visible=old_field.is_default_visible,
                        is_active=old_field.is_active
                    )
                    await new_signal.save()
                    migrated += 1
                    
                except Exception as e:
                    logger.error(f"迁移字段失败 {old_field.field_code}: {e}")
                    failed += 1
                    errors.append({
                        "field_code": old_field.field_code,
                        "error": str(e)
                    })
            
            # 更新迁移记录
            migration_record.migrated_records = migrated
            migration_record.failed_records = failed
            migration_record.skipped_records = skipped
            migration_record.status = "completed" if failed == 0 else "completed_with_errors"
            migration_record.completed_at = datetime.now()
            migration_record.error_details = {"errors": errors} if errors else None
            await migration_record.save()
            
            logger.info(f"✅ 设备字段迁移完成: 成功{migrated}, 失败{failed}, 跳过{skipped}")
            
            return {
                "total": len(old_fields),
                "migrated": migrated,
                "failed": failed,
                "skipped": skipped,
                "errors": errors
            }
            
        except Exception as e:
            migration_record.status = "failed"
            migration_record.error_details = {"error": str(e)}
            migration_record.completed_at = datetime.now()
            await migration_record.save()
            
            logger.error(f"❌ 设备字段迁移失败: {e}")
            raise
    
    async def migrate_devices(self) -> Dict[str, Any]:
        """
        迁移设备信息到资产
        
        Returns:
            迁移结果统计
        """
        from app.models.device import DeviceInfo
        from app.models.platform_upgrade import Asset, AssetCategory, MigrationRecord
        
        logger.info("开始迁移设备信息...")
        
        # 创建迁移记录
        migration_record = MigrationRecord(
            migration_name="migrate_devices",
            migration_type="device_info",
            source_table="t_device_info",
            target_table="t_asset",
            status="running",
            started_at=datetime.now()
        )
        await migration_record.save()
        
        try:
            # 1. 建立类别映射
            categories = await AssetCategory.all()
            category_map = {cat.code: cat for cat in categories}
            
            # 2. 读取旧设备
            old_devices = await DeviceInfo.all()
            migration_record.total_records = len(old_devices)
            await migration_record.save()
            
            migrated = 0
            failed = 0
            skipped = 0
            errors = []
            
            # 3. 转换并插入
            for old_device in old_devices:
                try:
                    category = category_map.get(old_device.device_type)
                    if not category:
                        logger.warning(f"跳过设备 {old_device.device_code}，找不到对应类别 {old_device.device_type}")
                        skipped += 1
                        continue
                    
                    # 检查是否已存在
                    existing = await Asset.get_or_none(code=old_device.device_code)
                    if existing:
                        logger.info(f"跳过已存在的资产: {old_device.device_code}")
                        skipped += 1
                        continue
                    
                    new_asset = Asset(
                        category=category,
                        code=old_device.device_code,
                        name=old_device.device_name,
                        attributes=old_device.attributes or {},
                        location=old_device.install_location,
                        status="offline",  # 默认离线状态
                        manufacturer=old_device.manufacturer,
                        model=old_device.device_model,
                        install_date=old_device.install_date,
                        team=old_device.team_name,
                        is_locked=old_device.is_locked,
                        is_active=True
                    )
                    await new_asset.save()
                    migrated += 1
                    
                except Exception as e:
                    logger.error(f"迁移设备失败 {old_device.device_code}: {e}")
                    failed += 1
                    errors.append({
                        "device_code": old_device.device_code,
                        "error": str(e)
                    })
            
            # 更新迁移记录
            migration_record.migrated_records = migrated
            migration_record.failed_records = failed
            migration_record.skipped_records = skipped
            migration_record.status = "completed" if failed == 0 else "completed_with_errors"
            migration_record.completed_at = datetime.now()
            migration_record.error_details = {"errors": errors} if errors else None
            await migration_record.save()
            
            logger.info(f"✅ 设备信息迁移完成: 成功{migrated}, 失败{failed}, 跳过{skipped}")
            
            return {
                "total": len(old_devices),
                "migrated": migrated,
                "failed": failed,
                "skipped": skipped,
                "errors": errors
            }
            
        except Exception as e:
            migration_record.status = "failed"
            migration_record.error_details = {"error": str(e)}
            migration_record.completed_at = datetime.now()
            await migration_record.save()
            
            logger.error(f"❌ 设备信息迁移失败: {e}")
            raise
    
    def _map_field_type(self, old_type: str) -> str:
        """映射旧字段类型到新类型"""
        type_mapping = {
            "string": "string",
            "integer": "int",
            "float": "float",
            "boolean": "bool",
            "json": "string",
            "double": "double"
        }
        return type_mapping.get(old_type.lower(), "string")


# =====================================================
# 双写适配器
# =====================================================

class DualWriteAdapter:
    """双写适配器 - 过渡期间同时写入新旧表"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
    
    async def create_asset(self, asset_data: dict) -> Any:
        """
        创建资产时同时写入新旧表
        
        Args:
            asset_data: 资产数据
            
        Returns:
            新创建的资产对象
        """
        from app.models.device import DeviceInfo
        from app.models.platform_upgrade import Asset, AssetCategory
        
        # 1. 写入新表
        category = await AssetCategory.get(code=asset_data["category_code"])
        new_asset = Asset(
            category=category,
            code=asset_data["code"],
            name=asset_data["name"],
            attributes=asset_data.get("attributes", {}),
            location=asset_data.get("location"),
            status=asset_data.get("status", "offline"),
            manufacturer=asset_data.get("manufacturer"),
            model=asset_data.get("model"),
            install_date=asset_data.get("install_date"),
            team=asset_data.get("team"),
            is_active=True
        )
        await new_asset.save()
        
        # 2. 写入旧表 (兼容性)
        if self.enabled:
            try:
                old_device = DeviceInfo(
                    device_code=asset_data["code"],
                    device_name=asset_data["name"],
                    device_type=asset_data["category_code"],
                    install_location=asset_data.get("location"),
                    manufacturer=asset_data.get("manufacturer"),
                    device_model=asset_data.get("model"),
                    install_date=asset_data.get("install_date"),
                    team_name=asset_data.get("team"),
                    attributes=asset_data.get("attributes", {})
                )
                await old_device.save()
                logger.debug(f"双写成功: {asset_data['code']}")
            except Exception as e:
                logger.warning(f"双写旧表失败: {e}")
        
        return new_asset
    
    async def update_asset_status(self, asset_code: str, status: str) -> bool:
        """
        更新资产状态时同步新旧表
        
        Args:
            asset_code: 资产编码
            status: 新状态
            
        Returns:
            更新是否成功
        """
        from app.models.device import DeviceInfo
        from app.models.platform_upgrade import Asset
        
        try:
            # 更新新表
            await Asset.filter(code=asset_code).update(status=status)
            
            # 更新旧表 (如果存在)
            if self.enabled:
                # DeviceInfo没有status字段，可以更新attributes
                device = await DeviceInfo.get_or_none(device_code=asset_code)
                if device:
                    attrs = device.attributes or {}
                    attrs["status"] = status
                    device.attributes = attrs
                    await device.save()
            
            return True
            
        except Exception as e:
            logger.error(f"更新资产状态失败: {e}")
            return False


# =====================================================
# 迁移验证器
# =====================================================

class MigrationValidator:
    """迁移验证器"""
    
    async def validate_migration(self) -> Dict[str, Any]:
        """
        验证迁移结果
        
        Returns:
            验证结果
        """
        from app.models.device import DeviceType, DeviceInfo, DeviceField
        from app.models.platform_upgrade import AssetCategory, Asset, SignalDefinition
        
        logger.info("开始验证迁移结果...")
        
        results = {
            "categories": {},
            "signals": {},
            "assets": {},
            "overall": "success"
        }
        
        try:
            # 1. 验证类别数量
            old_type_count = await DeviceType.all().count()
            new_category_count = await AssetCategory.all().count()
            
            results["categories"] = {
                "old_count": old_type_count,
                "new_count": new_category_count,
                "match": old_type_count <= new_category_count,
                "message": "类别数量一致" if old_type_count <= new_category_count else f"类别数量不匹配: {old_type_count} vs {new_category_count}"
            }
            
            # 2. 验证字段数量
            old_field_count = await DeviceField.all().count()
            new_signal_count = await SignalDefinition.all().count()
            
            results["signals"] = {
                "old_count": old_field_count,
                "new_count": new_signal_count,
                "match": old_field_count <= new_signal_count,
                "message": "信号数量一致" if old_field_count <= new_signal_count else f"信号数量不匹配: {old_field_count} vs {new_signal_count}"
            }
            
            # 3. 验证设备数量
            old_device_count = await DeviceInfo.all().count()
            new_asset_count = await Asset.all().count()
            
            results["assets"] = {
                "old_count": old_device_count,
                "new_count": new_asset_count,
                "match": old_device_count <= new_asset_count,
                "message": "资产数量一致" if old_device_count <= new_asset_count else f"资产数量不匹配: {old_device_count} vs {new_asset_count}"
            }
            
            # 4. 验证关联关系
            categories = await AssetCategory.all().prefetch_related("signals")
            for category in categories:
                signals = await category.signals.all()
                logger.info(f"类别 {category.name} 有 {len(signals)} 个信号")
            
            # 5. 综合判断
            if not all([
                results["categories"]["match"],
                results["signals"]["match"],
                results["assets"]["match"]
            ]):
                results["overall"] = "warning"
            
            logger.info(f"✅ 迁移验证完成: {results['overall']}")
            
        except Exception as e:
            results["overall"] = "error"
            results["error"] = str(e)
            logger.error(f"❌ 迁移验证失败: {e}")
        
        return results


# =====================================================
# 全局实例
# =====================================================

migration_engine = MigrationEngine()
dual_write_adapter = DualWriteAdapter(enabled=True)
migration_validator = MigrationValidator()


# =====================================================
# 主迁移流程
# =====================================================

async def run_full_migration() -> Dict[str, Any]:
    """
    执行完整迁移流程
    
    Returns:
        迁移结果汇总
    """
    results = {
        "device_types": None,
        "device_fields": None,
        "devices": None,
        "validation": None,
        "overall_status": "success"
    }
    
    try:
        logger.info("🚀 开始数据迁移...")
        
        # 阶段1：迁移设备类型
        results["device_types"] = await migration_engine.migrate_device_types()
        
        # 阶段2：迁移设备字段
        results["device_fields"] = await migration_engine.migrate_device_fields()
        
        # 阶段3：迁移设备信息
        results["devices"] = await migration_engine.migrate_devices()
        
        # 阶段4：验证迁移结果
        results["validation"] = await migration_validator.validate_migration()
        
        # 判断整体状态
        if results["validation"]["overall"] != "success":
            results["overall_status"] = results["validation"]["overall"]
        
        logger.info("✅ 数据迁移完成！")
        logger.info("📝 后续步骤：")
        logger.info("1. 更新API接口使用新模型")
        logger.info("2. 更新前端使用新接口")
        logger.info("3. 测试完成后停用旧表")
        
    except Exception as e:
        results["overall_status"] = "failed"
        results["error"] = str(e)
        logger.error(f"❌ 迁移失败: {e}")
    
    return results


# =====================================================
# 架构切换管理
# =====================================================

class ArchitectureManager:
    """系统架构管理器"""
    
    def __init__(self):
        self._use_new_architecture = False
        self._dual_write_enabled = True
    
    @property
    def use_new_architecture(self) -> bool:
        """是否使用新架构"""
        return self._use_new_architecture
    
    @property
    def dual_write_enabled(self) -> bool:
        """是否启用双写"""
        return self._dual_write_enabled
    
    def enable_new_architecture(self):
        """启用新架构"""
        self._use_new_architecture = True
        logger.info("✅ 已切换到新系统架构")
    
    def disable_new_architecture(self):
        """禁用新架构（回滚）"""
        self._use_new_architecture = False
        logger.info("⚠️ 已回滚到旧系统架构")
    
    def enable_dual_write(self):
        """启用双写模式"""
        self._dual_write_enabled = True
        dual_write_adapter.enabled = True
        logger.info("✅ 双写模式已启用")
    
    def disable_dual_write(self):
        """禁用双写模式"""
        self._dual_write_enabled = False
        dual_write_adapter.enabled = False
        logger.info("⚠️ 双写模式已禁用")
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """获取迁移状态"""
        from app.models.platform_upgrade import MigrationRecord, AssetCategory, Asset, SignalDefinition
        
        # 获取最新迁移记录
        latest_migration = await MigrationRecord.all().order_by("-started_at").first()
        
        # 获取数据统计
        category_count = await AssetCategory.all().count()
        asset_count = await Asset.all().count()
        signal_count = await SignalDefinition.all().count()
        
        return {
            "use_new_architecture": self._use_new_architecture,
            "dual_write_enabled": self._dual_write_enabled,
            "latest_migration": {
                "name": latest_migration.migration_name if latest_migration else None,
                "status": latest_migration.status if latest_migration else None,
                "completed_at": latest_migration.completed_at.isoformat() if latest_migration and latest_migration.completed_at else None
            },
            "data_counts": {
                "categories": category_count,
                "assets": asset_count,
                "signals": signal_count
            }
        }


# 全局架构管理器实例
architecture_manager = ArchitectureManager()


# =====================================================
# 迁移回滚支持
# =====================================================

class MigrationRollback:
    """迁移回滚管理器"""
    
    async def rollback_migration(self, migration_type: str) -> Dict[str, Any]:
        """
        回滚指定类型的迁移
        
        Args:
            migration_type: 迁移类型 (device_type/device_field/device_info)
            
        Returns:
            回滚结果
        """
        from app.models.platform_upgrade import MigrationRecord
        
        logger.warning(f"⚠️ 开始回滚迁移: {migration_type}")
        
        result = {
            "migration_type": migration_type,
            "status": "success",
            "rolled_back_count": 0
        }
        
        try:
            if migration_type == "device_type":
                result["rolled_back_count"] = await self._rollback_categories()
            elif migration_type == "device_field":
                result["rolled_back_count"] = await self._rollback_signals()
            elif migration_type == "device_info":
                result["rolled_back_count"] = await self._rollback_assets()
            else:
                result["status"] = "failed"
                result["error"] = f"未知的迁移类型: {migration_type}"
                return result
            
            # 记录回滚
            rollback_record = MigrationRecord(
                migration_name=f"rollback_{migration_type}",
                migration_type=f"rollback_{migration_type}",
                source_table="new_tables",
                target_table="rollback",
                total_records=result["rolled_back_count"],
                migrated_records=result["rolled_back_count"],
                status="completed",
                started_at=datetime.now(),
                completed_at=datetime.now()
            )
            await rollback_record.save()
            
            logger.info(f"✅ 回滚完成: {result['rolled_back_count']} 条记录")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            logger.error(f"❌ 回滚失败: {e}")
        
        return result
    
    async def _rollback_categories(self) -> int:
        """回滚资产类别"""
        from app.models.platform_upgrade import AssetCategory
        
        count = await AssetCategory.all().count()
        await AssetCategory.all().delete()
        return count
    
    async def _rollback_signals(self) -> int:
        """回滚信号定义"""
        from app.models.platform_upgrade import SignalDefinition
        
        count = await SignalDefinition.all().count()
        await SignalDefinition.all().delete()
        return count
    
    async def _rollback_assets(self) -> int:
        """回滚资产"""
        from app.models.platform_upgrade import Asset
        
        count = await Asset.all().count()
        await Asset.all().delete()
        return count


# 全局回滚管理器实例
migration_rollback = MigrationRollback()
