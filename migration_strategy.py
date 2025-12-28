# 数据迁移策略 - 从DeviceMonitorV4到工业AI数据平台

"""
迁移策略：渐进式升级，保证业务连续性

原则：
1. 保留旧表只读，新数据写入新表
2. 双写期间保证数据一致性  
3. 分阶段切换，降低风险
"""

# =====================================================
# 阶段1：表结构映射关系
# =====================================================

MIGRATION_MAPPING = {
    # 设备相关表迁移
    "t_device_type": {
        "target": "t_asset_category",
        "field_mapping": {
            "type_code": "code",
            "type_name": "name", 
            "description": "description",
            "tdengine_stable_name": "tdengine_stable_prefix",
            "is_active": "is_active"
        },
        "new_fields": {
            "industry": "manufacturing",  # 默认值
            "tdengine_database": "devicemonitor"
        }
    },
    
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
            "attributes": "attributes"
        }
    },
    
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
            "data_range": "value_range",
            "display_config": "display_config",
            "sort_order": "sort_order"
        }
    }
}

# =====================================================
# 阶段2：迁移脚本模板
# =====================================================

async def migrate_device_types():
    """迁移设备类型到资产类别"""
    from app.models.device import DeviceType
    from platform_upgrade_models import AssetCategory
    
    print("开始迁移设备类型...")
    
    # 1. 读取旧数据
    old_types = await DeviceType.all()
    
    # 2. 转换并插入新表
    for old_type in old_types:
        new_category = AssetCategory(
            code=old_type.type_code,
            name=old_type.type_name,
            description=old_type.description,
            industry="manufacturing",  # 默认行业
            tdengine_database="devicemonitor",
            tdengine_stable_prefix=old_type.tdengine_stable_name,
            is_active=old_type.is_active,
            asset_count=old_type.device_count,
            created_at=old_type.created_at,
            updated_at=old_type.updated_at
        )
        await new_category.save()
    
    print(f"✅ 迁移完成，共迁移 {len(old_types)} 个设备类型")


async def migrate_device_fields():
    """迁移设备字段到信号定义"""
    from app.models.device import DeviceField
    from platform_upgrade_models import SignalDefinition, AssetCategory
    
    print("开始迁移设备字段...")
    
    # 1. 建立类别映射
    categories = await AssetCategory.all()
    category_map = {cat.code: cat for cat in categories}
    
    # 2. 读取旧字段
    old_fields = await DeviceField.all()
    
    # 3. 转换并插入
    for old_field in old_fields:
        category = category_map.get(old_field.device_type_code)
        if not category:
            print(f"⚠️ 跳过字段 {old_field.field_code}，找不到对应类别")
            continue
            
        new_signal = SignalDefinition(
            category=category,
            code=old_field.field_code,
            name=old_field.field_name,
            data_type=old_field.field_type,
            unit=old_field.unit,
            is_stored=True,  # 默认存储
            is_realtime=old_field.is_monitoring_key,
            is_feature=old_field.is_ai_feature,
            value_range=old_field.data_range,
            display_config=old_field.display_config,
            sort_order=old_field.sort_order,
            created_at=old_field.created_at,
            updated_at=old_field.updated_at
        )
        await new_signal.save()
    
    print(f"✅ 迁移完成，共迁移 {len(old_fields)} 个字段定义")


# =====================================================
# 阶段3：双写适配器
# =====================================================

class DualWriteAdapter:
    """双写适配器 - 过渡期间同时写入新旧表"""
    
    @staticmethod
    async def create_asset(asset_data: dict):
        """创建资产时同时写入新旧表"""
        from app.models.device import DeviceInfo
        from platform_upgrade_models import Asset, AssetCategory
        
        # 1. 写入新表
        category = await AssetCategory.get(code=asset_data["category_code"])
        new_asset = Asset(
            category=category,
            code=asset_data["code"],
            name=asset_data["name"],
            attributes=asset_data.get("attributes", {}),
            location=asset_data.get("location"),
            status=asset_data.get("status", "offline")
        )
        await new_asset.save()
        
        # 2. 写入旧表 (兼容性)
        old_device = DeviceInfo(
            device_code=asset_data["code"],
            device_name=asset_data["name"],
            device_type=asset_data["category_code"],
            install_location=asset_data.get("location"),
            attributes=asset_data.get("attributes", {})
        )
        await old_device.save()
        
        return new_asset
    
    @staticmethod
    async def update_asset_status(asset_code: str, status: str):
        """更新资产状态时同步新旧表"""
        from app.models.device import DeviceInfo
        from platform_upgrade_models import Asset
        
        # 更新新表
        await Asset.filter(code=asset_code).update(status=status)
        
        # 更新旧表 (如果存在)
        await DeviceInfo.filter(device_code=asset_code).update(
            # DeviceInfo没有status字段，可以更新attributes
            attributes={"status": status}
        )


# =====================================================
# 阶段4：验证脚本
# =====================================================

async def validate_migration():
    """验证迁移结果"""
    from app.models.device import DeviceType, DeviceInfo, DeviceField
    from platform_upgrade_models import AssetCategory, Asset, SignalDefinition
    
    print("开始验证迁移结果...")
    
    # 1. 验证数量一致性
    old_type_count = await DeviceType.all().count()
    new_category_count = await AssetCategory.all().count()
    assert old_type_count == new_category_count, f"类别数量不匹配: {old_type_count} vs {new_category_count}"
    
    old_field_count = await DeviceField.all().count()
    new_signal_count = await SignalDefinition.all().count()
    assert old_field_count == new_signal_count, f"字段数量不匹配: {old_field_count} vs {new_signal_count}"
    
    # 2. 验证关联关系
    categories = await AssetCategory.all().prefetch_related("signals")
    for category in categories:
        signals = await category.signals.all()
        print(f"类别 {category.name} 有 {len(signals)} 个信号")
    
    print("✅ 迁移验证通过")


# =====================================================
# 主迁移流程
# =====================================================

async def run_migration():
    """执行完整迁移流程"""
    try:
        print("🚀 开始数据迁移...")
        
        # 阶段1：迁移基础数据
        await migrate_device_types()
        await migrate_device_fields()
        
        # 阶段2：验证迁移结果
        await validate_migration()
        
        print("✅ 数据迁移完成！")
        print("📝 后续步骤：")
        print("1. 更新API接口使用新模型")
        print("2. 更新前端使用新接口")
        print("3. 测试完成后停用旧表")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        raise


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_migration())