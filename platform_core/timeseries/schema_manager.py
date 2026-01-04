"""
TDengine Schema管理器

提供TDengine表结构的动态管理功能。

迁移说明:
- 从 platform_v2.timeseries.schema_manager 迁移到 platform_core.timeseries.schema_manager
- 保持所有API接口不变
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SchemaManager:
    """
    TDengine Schema动态管理器
    
    提供超级表的创建、更新和管理功能。
    """
    
    # 数据类型映射
    TYPE_MAPPING = {
        "float": "FLOAT",
        "int": "INT",
        "bool": "BOOL",
        "string": "NCHAR(64)",
        "double": "DOUBLE",
        "bigint": "BIGINT",
        "timestamp": "TIMESTAMP"
    }
    
    def __init__(self):
        self._client = None
    
    @property
    def client(self):
        """延迟加载TDengine客户端"""
        if self._client is None:
            from .tdengine_client import get_tdengine_client
            self._client = get_tdengine_client()
        return self._client
    
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
            
            # 1. 获取类别和信号定义
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
                await self._create_stable(stable_name, signals, category)
            else:
                await self._update_stable(stable_name, signals, category.tdengine_database)
            
            # 4. 记录Schema变更
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
            result = await self.client.describe_table(database, stable_name)
            return len(result) > 0
        except Exception:
            return False
    
    async def _create_stable(self, stable_name: str, signals: List, category) -> None:
        """创建新的超级表"""
        logger.info(f"创建超级表: {stable_name}")
        
        # 构建列定义
        columns = {"ts": "TIMESTAMP"}
        for signal in signals:
            col_type = self._map_data_type(signal.data_type)
            columns[signal.code] = col_type
        
        # 构建TAG定义
        tags = {
            "asset_id": "BIGINT",
            "asset_code": "NCHAR(100)"
        }
        
        # 执行创建
        await self.client.create_super_table(
            category.tdengine_database,
            stable_name,
            columns,
            tags
        )
        logger.info(f"✅ 超级表 {stable_name} 创建成功")
    
    async def _update_stable(self, stable_name: str, signals: List, database: str) -> None:
        """更新现有超级表结构"""
        logger.info(f"更新超级表: {stable_name}")
        
        # 获取现有列信息
        existing_columns = await self.client.describe_table(database, stable_name)
        existing_col_names = {col['name'].lower() for col in existing_columns}
        
        # 计算需要添加的列
        new_signals = [s for s in signals if s.code.lower() not in existing_col_names]
        
        # 添加新列
        for signal in new_signals:
            col_type = self._map_data_type(signal.data_type)
            alter_sql = f"ALTER STABLE {database}.{stable_name} ADD COLUMN {signal.code} {col_type}"
            
            try:
                await self.client.execute(alter_sql)
                logger.info(f"✅ 添加列: {signal.code} {col_type}")
            except Exception as e:
                logger.error(f"❌ 添加列失败: {signal.code}, {e}")
    
    def _map_data_type(self, signal_type: str) -> str:
        """映射信号类型到TDengine类型"""
        return self.TYPE_MAPPING.get(signal_type.lower(), "NCHAR(64)")
    
    async def create_child_table(
        self,
        stable_name: str,
        asset_code: str,
        asset_id: int,
        database: str
    ) -> bool:
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
            
            await self.client.create_sub_table(
                database,
                stable_name,
                child_table,
                {"asset_id": asset_id, "asset_code": asset_code}
            )
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
        
        return [
            {
                "version": v.version,
                "change_type": v.change_type,
                "change_details": v.change_details,
                "execution_status": v.execution_status,
                "execution_time": v.execution_time.isoformat() if v.execution_time else None
            }
            for v in versions
        ]


class SchemaVersionManager:
    """Schema版本管理器"""
    
    def __init__(self):
        self.schema_manager = SchemaManager()
    
    async def rollback_to_version(self, category_code: str, target_version: str) -> bool:
        """
        回滚到指定版本
        
        注意：TDengine不支持删除列，回滚只能通过重建表实现
        """
        logger.warning("Schema回滚功能暂不支持，TDengine不支持删除列")
        return False
    
    async def compare_versions(
        self,
        category_code: str,
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
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


# 全局实例
schema_manager = SchemaManager()
schema_version_manager = SchemaVersionManager()
