# Schema引擎 - TDengine表结构动态管理
# 实现元数据驱动的Schema自动同步

"""
核心功能：
1. 根据SignalDefinition自动创建/更新TDengine超级表
2. 支持字段增删改，保证数据一致性
3. 提供Schema版本控制和回滚能力
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger


class TDengineSchemaManager:
    """TDengine Schema 动态管理器"""
    
    def __init__(self):
        self._td_client = None
    
    @property
    def td_client(self):
        """延迟加载TDengine客户端"""
        if self._td_client is None:
            from app.core.tdengine_connector import td_client
            self._td_client = td_client
        return self._td_client
    
    async def sync_category_schema(self, category_code: str) -> bool:
        """
        同步资产类别的TDengine Schema
        
        Args:
            category_code: 资产类别编码
            
        Returns:
            bool: 同步是否成功
        """
        try:
            logger.info(f"开始同步类别 {category_code} 的Schema...")
            
            # 1. 获取信号定义
            from app.models.platform_upgrade import AssetCategory, SignalDefinition
            
            category = await AssetCategory.get_or_none(code=category_code)
            if not category:
                logger.error(f"类别 {category_code} 不存在")
                return False
            
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
            exists = await self._check_stable_exists(stable_name, category.tdengine_database)
            
            if not exists:
                # 创建新表
                await self._create_stable(stable_name, signals, category)
            else:
                # 更新现有表
                await self._update_stable(stable_name, signals, category.tdengine_database)
            
            # 4. 记录Schema版本
            await self._record_schema_change(
                category=category,
                change_type="create" if not exists else "update",
                signals=signals,
                stable_name=stable_name
            )
            
            logger.info(f"✅ 类别 {category_code} Schema同步完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 同步Schema失败: {e}")
            return False
    
    async def _check_stable_exists(self, stable_name: str, database: str) -> bool:
        """检查超级表是否存在"""
        try:
            sql = f"DESCRIBE {database}.{stable_name}"
            result = await self.td_client.query(sql)
            return len(result) > 0
        except Exception:
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
            "asset_code NCHAR(100)"
        ]
        
        # 3. 生成CREATE SQL
        columns_str = ",\n    ".join(columns)
        tags_str = ",\n    ".join(tags)
        
        create_sql = f"""
        CREATE STABLE IF NOT EXISTS {category.tdengine_database}.{stable_name} (
            {columns_str}
        ) TAGS (
            {tags_str}
        )
        """
        
        # 4. 执行创建
        await self.td_client.execute(create_sql)
        logger.info(f"✅ 超级表 {stable_name} 创建成功")
    
    async def _update_stable(self, stable_name: str, signals: List, database: str) -> None:
        """更新现有超级表结构"""
        logger.info(f"更新超级表: {stable_name}")
        
        # 1. 获取现有列信息
        existing_columns = await self._get_stable_columns(stable_name, database)
        existing_col_names = {col['Field'].lower() for col in existing_columns}
        
        # 2. 计算需要添加的列
        new_signals = [s for s in signals if s.code.lower() not in existing_col_names]
        
        # 3. 添加新列
        for signal in new_signals:
            col_type = self._map_data_type(signal.data_type)
            alter_sql = f"ALTER STABLE {database}.{stable_name} ADD COLUMN {signal.code} {col_type}"
            
            try:
                await self.td_client.execute(alter_sql)
                logger.info(f"✅ 添加列: {signal.code} {col_type}")
            except Exception as e:
                logger.error(f"❌ 添加列失败: {signal.code}, {e}")
        
        # 注意：TDengine不支持删除列，只能添加
        # 如果需要删除列，需要重建表或标记为废弃
    
    async def _get_stable_columns(self, stable_name: str, database: str) -> List[Dict]:
        """获取超级表的列信息"""
        sql = f"DESCRIBE {database}.{stable_name}"
        return await self.td_client.query(sql)
    
    def _map_data_type(self, signal_type: str) -> str:
        """映射信号类型到TDengine类型"""
        type_mapping = {
            "float": "FLOAT",
            "int": "INT", 
            "bool": "BOOL",
            "string": "NCHAR(64)",
            "double": "DOUBLE",
            "bigint": "BIGINT",
            "timestamp": "TIMESTAMP"
        }
        return type_mapping.get(signal_type.lower(), "NCHAR(64)")
    
    async def create_child_table(self, stable_name: str, asset_code: str, asset_id: int, database: str = "devicemonitor") -> bool:
        """
        为资产创建子表
        
        Args:
            stable_name: 超级表名
            asset_code: 资产编码
            asset_id: 资产ID
            database: 数据库名
            
        Returns:
            bool: 创建是否成功
        """
        try:
            # 清理资产编码中的特殊字符
            safe_asset_code = asset_code.replace("-", "_").replace(" ", "_")
            child_table = f"{stable_name}_{safe_asset_code}"
            
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {database}.{child_table} USING {database}.{stable_name} 
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
        from app.models.platform_upgrade import AssetCategory
        
        categories = await AssetCategory.filter(is_active=True).all()
        results = {}
        
        for category in categories:
            success = await self.sync_category_schema(category.code)
            results[category.code] = success
        
        return results
    
    async def _record_schema_change(
        self, 
        category, 
        change_type: str, 
        signals: List,
        stable_name: str
    ) -> None:
        """记录Schema变更"""
        from app.models.platform_upgrade import SchemaVersion
        
        try:
            # 获取当前版本号
            latest_version = await SchemaVersion.filter(
                category=category
            ).order_by("-version").first()
            
            if latest_version:
                # 解析版本号并递增
                parts = latest_version.version.split(".")
                new_version = f"{parts[0]}.{int(parts[1]) + 1}"
            else:
                new_version = "1.0"
            
            # 构建变更详情
            change_details = {
                "stable_name": stable_name,
                "signals": [
                    {
                        "code": s.code,
                        "name": s.name,
                        "data_type": s.data_type
                    } for s in signals
                ],
                "change_type": change_type
            }
            
            # 创建版本记录
            schema_version = SchemaVersion(
                category=category,
                version=new_version,
                change_type=change_type,
                change_details=change_details,
                execution_status="success",
                execution_time=datetime.now()
            )
            await schema_version.save()
            
            logger.info(f"✅ Schema变更记录: {category.code} v{new_version}")
            
        except Exception as e:
            logger.error(f"❌ 记录Schema变更失败: {e}")
    
    async def get_schema_history(self, category_code: str) -> List[Dict]:
        """获取Schema变更历史"""
        from app.models.platform_upgrade import AssetCategory, SchemaVersion
        
        category = await AssetCategory.get_or_none(code=category_code)
        if not category:
            return []
        
        versions = await SchemaVersion.filter(
            category=category
        ).order_by("-execution_time").all()
        
        return [await v.to_dict() for v in versions]


class SchemaVersionManager:
    """Schema版本管理器"""
    
    def __init__(self):
        self.schema_manager = TDengineSchemaManager()
    
    async def rollback_to_version(self, category_code: str, target_version: str) -> bool:
        """
        回滚到指定版本
        
        注意：TDengine不支持删除列，回滚只能通过重建表实现
        """
        logger.warning(f"Schema回滚功能暂不支持，TDengine不支持删除列")
        return False
    
    async def compare_versions(self, category_code: str, version1: str, version2: str) -> Dict:
        """比较两个版本的差异"""
        from app.models.platform_upgrade import AssetCategory, SchemaVersion
        
        category = await AssetCategory.get_or_none(code=category_code)
        if not category:
            return {"error": "类别不存在"}
        
        v1 = await SchemaVersion.get_or_none(category=category, version=version1)
        v2 = await SchemaVersion.get_or_none(category=category, version=version2)
        
        if not v1 or not v2:
            return {"error": "版本不存在"}
        
        # 比较信号列表
        v1_signals = {s["code"] for s in v1.change_details.get("signals", [])}
        v2_signals = {s["code"] for s in v2.change_details.get("signals", [])}
        
        return {
            "added": list(v2_signals - v1_signals),
            "removed": list(v1_signals - v2_signals),
            "unchanged": list(v1_signals & v2_signals)
        }


# =====================================================
# 全局实例
# =====================================================

schema_manager = TDengineSchemaManager()
schema_version_manager = SchemaVersionManager()


# =====================================================
# API集成钩子
# =====================================================

async def on_signal_definition_changed(category_code: str) -> bool:
    """
    信号定义变更时的钩子函数
    
    当信号定义被创建、更新或删除时调用此函数，
    自动同步TDengine Schema
    """
    logger.info(f"检测到信号定义变更: {category_code}")
    
    # 自动同步Schema
    success = await schema_manager.sync_category_schema(category_code)
    
    if success:
        logger.info(f"✅ Schema自动同步成功: {category_code}")
    else:
        logger.error(f"❌ Schema自动同步失败: {category_code}")
        # 这里可以发送告警通知
    
    return success


async def on_asset_created(asset_code: str, category_code: str, asset_id: int) -> bool:
    """
    资产创建时的钩子函数
    
    当新资产被创建时调用此函数，
    自动创建TDengine子表
    """
    logger.info(f"检测到新资产创建: {asset_code}")
    
    from app.models.platform_upgrade import AssetCategory
    
    category = await AssetCategory.get_or_none(code=category_code)
    if not category:
        logger.error(f"类别 {category_code} 不存在")
        return False
    
    # 自动创建子表
    stable_name = f"raw_{category_code}"
    success = await schema_manager.create_child_table(
        stable_name, 
        asset_code, 
        asset_id,
        category.tdengine_database
    )
    
    return success


async def on_category_created(category_code: str) -> bool:
    """
    资产类别创建时的钩子函数
    
    当新资产类别被创建时调用此函数，
    初始化TDengine Schema
    """
    logger.info(f"检测到新资产类别创建: {category_code}")
    
    # 同步Schema（如果有信号定义的话）
    success = await schema_manager.sync_category_schema(category_code)
    
    return success
