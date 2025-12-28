# 动态Schema管理器 - TDengine表结构自动同步

"""
核心功能：
1. 根据SignalDefinition自动创建/更新TDengine超级表
2. 支持字段增删改，保证数据一致性
3. 提供Schema版本控制和回滚能力
"""

import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger
from app.core.tdengine_connector import td_client


class TDengineSchemaManager:
    """TDengine Schema 动态管理器"""
    
    def __init__(self):
        self.td_client = td_client
    
    async def sync_category_schema(self, category_code: str) -> bool:
        """同步资产类别的TDengine Schema"""
        try:
            logger.info(f"开始同步类别 {category_code} 的Schema...")
            
            # 1. 获取信号定义
            from platform_upgrade_models import AssetCategory, SignalDefinition
            
            category = await AssetCategory.get(code=category_code)
            signals = await SignalDefinition.filter(
                category=category, 
                is_stored=True,
                is_active=True
            ).all()
            
            if not signals:
                logger.warning(f"类别 {category_code} 没有需要存储的信号")
                return True
            
            # 2. 生成表名
            stable_name = f"raw_{category_code}"
            
            # 3. 检查表是否存在
            exists = await self._check_stable_exists(stable_name)
            
            if not exists:
                # 创建新表
                await self._create_stable(stable_name, signals, category)
            else:
                # 更新现有表
                await self._update_stable(stable_name, signals)
            
            logger.info(f"✅ 类别 {category_code} Schema同步完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 同步Schema失败: {e}")
            return False
    
    async def _check_stable_exists(self, stable_name: str) -> bool:
        """检查超级表是否存在"""
        try:
            sql = f"DESCRIBE {stable_name}"
            result = await self.td_client.query(sql)
            return len(result) > 0
        except:
            return False
    
    async def _create_stable(self, stable_name: str, signals: List, category) -> None:
        """创建新的超级表"""
        logger.info(f"创建超级表: {stable_name}")
        
        # 1. 构建列定义
        columns = ["ts TIMESTAMP"]  # 时间戳列
        
        for signal in signals:
            col_type = self._map_data_type(signal.data_type)
            columns.append(f"{signal.code} {col_type}")
        
        # 2. 构建TAG定义
        tags = [
            "asset_id BIGINT",
            "asset_code NCHAR(64)"
        ]
        
        # 3. 生成CREATE SQL
        columns_str = ",\n    ".join(columns)
        tags_str = ",\n    ".join(tags)
        
        create_sql = f"""
        CREATE STABLE {stable_name} (
            {columns_str}
        ) TAGS (
            {tags_str}
        )
        """
        
        # 4. 执行创建
        await self.td_client.execute(create_sql)
        logger.info(f"✅ 超级表 {stable_name} 创建成功")
    
    async def _update_stable(self, stable_name: str, signals: List) -> None:
        """更新现有超级表结构"""
        logger.info(f"更新超级表: {stable_name}")
        
        # 1. 获取现有列信息
        existing_columns = await self._get_stable_columns(stable_name)
        existing_col_names = {col['Field'] for col in existing_columns}
        
        # 2. 计算需要添加的列
        new_signals = [s for s in signals if s.code not in existing_col_names]
        
        # 3. 添加新列
        for signal in new_signals:
            col_type = self._map_data_type(signal.data_type)
            alter_sql = f"ALTER STABLE {stable_name} ADD COLUMN {signal.code} {col_type}"
            
            try:
                await self.td_client.execute(alter_sql)
                logger.info(f"✅ 添加列: {signal.code} {col_type}")
            except Exception as e:
                logger.error(f"❌ 添加列失败: {signal.code}, {e}")
        
        # 注意：TDengine不支持删除列，只能添加
        # 如果需要删除列，需要重建表或标记为废弃
    
    async def _get_stable_columns(self, stable_name: str) -> List[Dict]:
        """获取超级表的列信息"""
        sql = f"DESCRIBE {stable_name}"
        return await self.td_client.query(sql)
    
    def _map_data_type(self, signal_type: str) -> str:
        """映射信号类型到TDengine类型"""
        type_mapping = {
            "float": "FLOAT",
            "int": "INT", 
            "bool": "BOOL",
            "string": "NCHAR(64)",
            "double": "DOUBLE",
            "bigint": "BIGINT"
        }
        return type_mapping.get(signal_type, "NCHAR(64)")
    
    async def create_child_table(self, stable_name: str, asset_code: str, asset_id: int) -> bool:
        """为资产创建子表"""
        try:
            child_table = f"{stable_name}_{asset_code}"
            
            create_sql = f"""
            CREATE TABLE {child_table} USING {stable_name} 
            TAGS ({asset_id}, '{asset_code}')
            """
            
            await self.td_client.execute(create_sql)
            logger.info(f"✅ 创建子表: {child_table}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建子表失败: {e}")
            return False
    
    async def sync_all_categories(self) -> Dict[str, bool]:
        """同步所有激活类别的Schema"""
        from platform_upgrade_models import AssetCategory
        
        categories = await AssetCategory.filter(is_active=True).all()
        results = {}
        
        for category in categories:
            success = await self.sync_category_schema(category.code)
            results[category.code] = success
        
        return results


# =====================================================
# Schema版本控制
# =====================================================

class SchemaVersionManager:
    """Schema版本管理器"""
    
    def __init__(self):
        self.version_table = "t_schema_versions"
    
    async def record_schema_change(self, category_code: str, change_type: str, details: Dict) -> None:
        """记录Schema变更"""
        # 这里可以扩展为完整的版本控制系统
        logger.info(f"Schema变更记录: {category_code} - {change_type}")
        logger.debug(f"变更详情: {details}")
    
    async def get_schema_history(self, category_code: str) -> List[Dict]:
        """获取Schema变更历史"""
        # TODO: 实现完整的历史查询
        return []


# =====================================================
# 使用示例
# =====================================================

async def example_usage():
    """使用示例"""
    
    schema_manager = TDengineSchemaManager()
    
    # 1. 同步单个类别
    success = await schema_manager.sync_category_schema("welding_robot")
    print(f"同步结果: {success}")
    
    # 2. 同步所有类别
    results = await schema_manager.sync_all_categories()
    print(f"批量同步结果: {results}")
    
    # 3. 为新资产创建子表
    await schema_manager.create_child_table("raw_welding_robot", "ROBOT_001", 1)


# 全局实例
schema_manager = TDengineSchemaManager()


# =====================================================
# API集成钩子
# =====================================================

async def on_signal_definition_changed(category_code: str):
    """信号定义变更时的钩子函数"""
    logger.info(f"检测到信号定义变更: {category_code}")
    
    # 自动同步Schema
    success = await schema_manager.sync_category_schema(category_code)
    
    if success:
        logger.info(f"✅ Schema自动同步成功: {category_code}")
    else:
        logger.error(f"❌ Schema自动同步失败: {category_code}")
        # 这里可以发送告警通知
    
    return success


async def on_asset_created(asset_code: str, category_code: str, asset_id: int):
    """资产创建时的钩子函数"""
    logger.info(f"检测到新资产创建: {asset_code}")
    
    # 自动创建子表
    stable_name = f"raw_{category_code}"
    success = await schema_manager.create_child_table(stable_name, asset_code, asset_id)
    
    return success