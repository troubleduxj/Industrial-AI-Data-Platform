#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
特征存储服务 (Feature Store)

实现需求6.1: 当激活特征视图时，平台应自动创建feat_{category}超级表
实现需求6.3: 当查询特征数据时，平台应支持按资产、时间范围和特征名筛选
实现需求6.4: 当特征定义变更时，平台应支持特征表的Schema演进

核心功能:
- 特征表自动创建 (create_feature_table)
- Schema演进 (evolve_schema)
- 特征数据查询 (query_features)
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger


# =====================================================
# 异常定义
# =====================================================

class TableNameError(Exception):
    """表名相关错误"""
    pass


class SchemaEvolutionError(Exception):
    """Schema演进错误"""
    pass


class FeatureQueryError(Exception):
    """特征查询错误"""
    pass


# =====================================================
# 常量和枚举
# =====================================================

class FeatureOutputType(str, Enum):
    """特征输出类型"""
    DOUBLE = "DOUBLE"
    BIGINT = "BIGINT"
    FLOAT = "FLOAT"
    INT = "INT"
    BOOL = "BOOL"
    NCHAR = "NCHAR"


# 聚合函数到输出类型的映射
FUNCTION_OUTPUT_TYPES = {
    "count": FeatureOutputType.BIGINT,
    "avg": FeatureOutputType.DOUBLE,
    "sum": FeatureOutputType.DOUBLE,
    "max": FeatureOutputType.DOUBLE,
    "min": FeatureOutputType.DOUBLE,
    "stddev": FeatureOutputType.DOUBLE,
    "first": FeatureOutputType.DOUBLE,
    "last": FeatureOutputType.DOUBLE,
    "diff": FeatureOutputType.DOUBLE,
    "derivative": FeatureOutputType.DOUBLE,
    "spread": FeatureOutputType.DOUBLE,
    "percentile": FeatureOutputType.DOUBLE,
}

# 验证正则表达式
CATEGORY_CODE_PATTERN = re.compile(r'^[a-z][a-z0-9_]{0,49}$')
# 视图名称不允许下划线，以保证解析时的往返一致性
VIEW_NAME_PATTERN = re.compile(r'^[a-z][a-z0-9]{0,49}$')
FEATURE_NAME_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]{0,63}$')


# =====================================================
# 数据类定义
# =====================================================

@dataclass
class FeatureConfig:
    """特征配置"""
    name: str
    function: str
    source_signal: str
    output_type: Optional[str] = None
    
    def get_output_type(self) -> str:
        """获取输出类型"""
        if self.output_type:
            return self.output_type.upper()
        return FUNCTION_OUTPUT_TYPES.get(
            self.function.lower(), 
            FeatureOutputType.DOUBLE
        ).value


@dataclass
class FeatureTableConfig:
    """特征表配置"""
    category_code: str
    view_name: str
    feature_configs: List[FeatureConfig]
    database: str = "devicemonitor"
    
    @property
    def stable_name(self) -> str:
        """获取超级表名"""
        return FeatureTableNaming.get_stable_name(self.category_code, self.view_name)
    
    @property
    def full_stable_name(self) -> str:
        """获取完整超级表名（包含数据库）"""
        return f"{self.database}.{self.stable_name}"


@dataclass
class FeatureRecord:
    """特征记录"""
    asset_id: int
    asset_code: str
    timestamp: datetime
    features: Dict[str, Any]
    category_code: str
    view_name: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "asset_id": self.asset_id,
            "asset_code": self.asset_code,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            "category_code": self.category_code,
            "view_name": self.view_name,
        }
        result.update(self.features)
        return result


# =====================================================
# 特征表命名服务
# =====================================================

class FeatureTableNaming:
    """
    特征表命名服务
    
    负责生成和验证特征表名称，确保遵循feat_{category}_{view}模式
    """
    
    PREFIX = "feat"
    
    @classmethod
    def get_stable_name(cls, category_code: str, view_name: str) -> str:
        """
        获取超级表名
        
        Args:
            category_code: 资产类别编码
            view_name: 特征视图名称
            
        Returns:
            str: 超级表名，格式为 feat_{category}_{view}
            
        Raises:
            TableNameError: 如果类别编码或视图名称无效
        """
        # 验证类别编码
        is_valid, error = cls.validate_category_code(category_code)
        if not is_valid:
            raise TableNameError(f"无效的类别编码: {error}")
        
        # 验证视图名称
        is_valid, error = cls.validate_view_name(view_name)
        if not is_valid:
            raise TableNameError(f"无效的视图名称: {error}")
        
        return f"{cls.PREFIX}_{category_code.lower()}_{view_name.lower()}"
    
    @classmethod
    def get_child_table_name(
        cls, 
        category_code: str, 
        view_name: str, 
        asset_code: str
    ) -> str:
        """
        获取子表名
        
        Args:
            category_code: 资产类别编码
            view_name: 特征视图名称
            asset_code: 资产编码
            
        Returns:
            str: 子表名，格式为 feat_{category}_{view}_{asset}
        """
        stable_name = cls.get_stable_name(category_code, view_name)
        return f"{stable_name}_{asset_code}"
    
    @classmethod
    def validate_category_code(cls, category_code: str) -> Tuple[bool, Optional[str]]:
        """
        验证类别编码
        
        Args:
            category_code: 类别编码
            
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误信息)
        """
        if not category_code:
            return False, "类别编码不能为空"
        
        if not isinstance(category_code, str):
            return False, "类别编码必须是字符串"
        
        if len(category_code) > 50:
            return False, f"类别编码过长: {len(category_code)}字符，最大50字符"
        
        if not CATEGORY_CODE_PATTERN.match(category_code.lower()):
            return False, "类别编码必须以小写字母开头，只能包含小写字母、数字和下划线"
        
        return True, None
    
    @classmethod
    def validate_view_name(cls, view_name: str) -> Tuple[bool, Optional[str]]:
        """
        验证视图名称
        
        注意：视图名称不允许包含下划线，以保证表名解析时的往返一致性。
        
        Args:
            view_name: 视图名称
            
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误信息)
        """
        if not view_name:
            return False, "视图名称不能为空"
        
        if not isinstance(view_name, str):
            return False, "视图名称必须是字符串"
        
        if len(view_name) > 50:
            return False, f"视图名称过长: {len(view_name)}字符，最大50字符"
        
        if not VIEW_NAME_PATTERN.match(view_name.lower()):
            return False, "视图名称必须以小写字母开头，只能包含小写字母和数字（不允许下划线）"
        
        return True, None
    
    @classmethod
    def validate_feature_name(cls, feature_name: str) -> Tuple[bool, Optional[str]]:
        """
        验证特征名称
        
        Args:
            feature_name: 特征名称
            
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误信息)
        """
        if not feature_name:
            return False, "特征名称不能为空"
        
        if not isinstance(feature_name, str):
            return False, "特征名称必须是字符串"
        
        if len(feature_name) > 64:
            return False, f"特征名称过长: {len(feature_name)}字符，最大64字符"
        
        if not FEATURE_NAME_PATTERN.match(feature_name):
            return False, "特征名称必须以字母或下划线开头，只能包含字母、数字和下划线"
        
        return True, None
    
    @classmethod
    def is_valid_stable_name(cls, stable_name: str) -> bool:
        """
        检查是否是有效的超级表名
        
        Args:
            stable_name: 超级表名
            
        Returns:
            bool: 是否有效
        """
        if not stable_name or not isinstance(stable_name, str):
            return False
        
        if not stable_name.startswith(f"{cls.PREFIX}_"):
            return False
        
        # 尝试解析
        parts = stable_name.split("_")
        if len(parts) < 3:
            return False
        
        return True
    
    @classmethod
    def parse_stable_name(cls, stable_name: str) -> Tuple[str, str]:
        """
        解析超级表名
        
        注意：由于类别编码和视图名称都可能包含下划线，解析时采用最后一个下划线作为分隔符。
        这意味着类别编码可以包含下划线，但视图名称不能包含下划线（或者需要其他方式区分）。
        
        为了保持往返一致性，我们采用从右向左查找第一个下划线的方式来分割。
        
        Args:
            stable_name: 超级表名
            
        Returns:
            Tuple[str, str]: (类别编码, 视图名称)
            
        Raises:
            TableNameError: 如果表名格式无效
        """
        if not cls.is_valid_stable_name(stable_name):
            raise TableNameError(f"无效的超级表名格式: {stable_name}")
        
        # 移除前缀 "feat_"
        name_without_prefix = stable_name[len(cls.PREFIX) + 1:]
        
        # 从右向左查找最后一个下划线来分割类别编码和视图名称
        # 这样可以支持类别编码包含下划线的情况
        last_underscore_idx = name_without_prefix.rfind("_")
        
        if last_underscore_idx <= 0:
            raise TableNameError(f"无法解析超级表名: {stable_name}")
        
        category_code = name_without_prefix[:last_underscore_idx]
        view_name = name_without_prefix[last_underscore_idx + 1:]
        
        if not category_code or not view_name:
            raise TableNameError(f"无法解析超级表名: {stable_name}")
        
        return category_code, view_name
    
    @classmethod
    def get_create_stable_sql(
        cls,
        category_code: str,
        view_name: str,
        feature_configs: List[Dict[str, Any]],
        database: str = "devicemonitor"
    ) -> str:
        """
        生成创建超级表的SQL
        
        Args:
            category_code: 资产类别编码
            view_name: 特征视图名称
            feature_configs: 特征配置列表
            database: 数据库名称
            
        Returns:
            str: CREATE STABLE SQL语句
        """
        stable_name = cls.get_stable_name(category_code, view_name)
        
        # 构建列定义
        columns = ["ts TIMESTAMP"]
        for config in feature_configs:
            feature = FeatureConfig(
                name=config.get("name", ""),
                function=config.get("function", "avg"),
                source_signal=config.get("source_signal", ""),
                output_type=config.get("output_type")
            )
            
            # 验证特征名称
            is_valid, error = cls.validate_feature_name(feature.name)
            if not is_valid:
                raise TableNameError(f"特征配置无效: {error}")
            
            output_type = feature.get_output_type()
            columns.append(f"{feature.name} {output_type}")
        
        # 构建TAG定义
        tags = ["asset_id BIGINT", "asset_code NCHAR(64)"]
        
        columns_str = ",\n    ".join(columns)
        tags_str = ",\n    ".join(tags)
        
        sql = f"""CREATE STABLE IF NOT EXISTS {database}.{stable_name} (
    {columns_str}
) TAGS (
    {tags_str}
)"""
        
        return sql
    
    @classmethod
    def get_create_child_table_sql(
        cls,
        category_code: str,
        view_name: str,
        asset_code: str,
        asset_id: int,
        database: str = "devicemonitor"
    ) -> str:
        """
        生成创建子表的SQL
        
        Args:
            category_code: 资产类别编码
            view_name: 特征视图名称
            asset_code: 资产编码
            asset_id: 资产ID
            database: 数据库名称
            
        Returns:
            str: CREATE TABLE SQL语句
        """
        stable_name = cls.get_stable_name(category_code, view_name)
        child_table_name = cls.get_child_table_name(category_code, view_name, asset_code)
        
        sql = f"""CREATE TABLE IF NOT EXISTS {database}.{child_table_name}
USING {database}.{stable_name}
TAGS ({asset_id}, '{asset_code}')"""
        
        return sql



# =====================================================
# 特征存储服务
# =====================================================

class FeatureStore:
    """
    特征存储服务
    
    负责特征表的创建、Schema演进和数据查询。
    
    核心功能:
    - create_feature_table(): 自动创建特征超级表
    - evolve_schema(): Schema演进，添加新特征列
    - query_features(): 特征数据查询
    """
    
    def __init__(self, database: str = "devicemonitor"):
        """
        初始化特征存储服务
        
        Args:
            database: TDengine数据库名称
        """
        self.database = database
        self._td_client = None
    
    @property
    def td_client(self):
        """延迟加载TDengine客户端"""
        if self._td_client is None:
            try:
                from app.core.tdengine_connector import td_client
                self._td_client = td_client
            except ImportError:
                logger.warning("TDengine客户端未配置，使用模拟模式")
                self._td_client = None
        return self._td_client
    
    async def create_feature_table(
        self,
        category_code: str,
        view_name: str,
        feature_configs: List[Dict[str, Any]]
    ) -> bool:
        """
        创建特征超级表
        
        实现需求6.1: 当激活特征视图时，平台应自动创建feat_{category}_{view}超级表
        
        Args:
            category_code: 资产类别编码
            view_name: 特征视图名称
            feature_configs: 特征配置列表，每个配置包含:
                - name: 特征名称
                - function: 聚合函数 (avg, sum, max, min, count, stddev等)
                - source_signal: 源信号
                - output_type: 输出类型 (可选)
        
        Returns:
            bool: 创建是否成功
            
        Example:
            >>> store = FeatureStore()
            >>> configs = [
            ...     {"name": "avg_current", "function": "avg", "source_signal": "current"},
            ...     {"name": "max_voltage", "function": "max", "source_signal": "voltage"}
            ... ]
            >>> await store.create_feature_table("motor", "realtime_stats", configs)
            True
        """
        try:
            # 验证输入
            if not feature_configs:
                logger.error("特征配置列表不能为空")
                return False
            
            # 生成表名
            table_name = FeatureTableNaming.get_stable_name(category_code, view_name)
            
            # 生成创建SQL
            create_sql = FeatureTableNaming.get_create_stable_sql(
                category_code, view_name, feature_configs, self.database
            )
            
            logger.debug(f"创建特征表SQL:\n{create_sql}")
            
            # 执行创建
            if self.td_client:
                await self.td_client.execute(create_sql)
                logger.info(f"✅ 特征表创建成功: {table_name}")
            else:
                logger.warning(f"TDengine客户端未配置，跳过表创建: {table_name}")
            
            return True
            
        except TableNameError as e:
            logger.error(f"❌ 特征表创建失败 - 命名错误: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 特征表创建失败: {e}")
            return False
    
    async def evolve_schema(
        self,
        category_code: str,
        view_name: str,
        new_features: List[Dict[str, Any]]
    ) -> bool:
        """
        Schema演进 - 添加新特征列
        
        实现需求6.4: 当特征定义变更时，平台应支持特征表的Schema演进
        
        Args:
            category_code: 资产类别编码
            view_name: 特征视图名称
            new_features: 新增特征配置列表
        
        Returns:
            bool: 演进是否成功
            
        Example:
            >>> store = FeatureStore()
            >>> new_features = [
            ...     {"name": "min_current", "function": "min", "source_signal": "current"}
            ... ]
            >>> await store.evolve_schema("motor", "realtime_stats", new_features)
            True
        """
        try:
            if not new_features:
                logger.warning("没有新特征需要添加")
                return True
            
            table_name = FeatureTableNaming.get_stable_name(category_code, view_name)
            full_table_name = f"{self.database}.{table_name}"
            
            success_count = 0
            for feature_config in new_features:
                feature = FeatureConfig(
                    name=feature_config.get("name", ""),
                    function=feature_config.get("function", "avg"),
                    source_signal=feature_config.get("source_signal", ""),
                    output_type=feature_config.get("output_type")
                )
                
                # 验证特征名称
                is_valid, error = FeatureTableNaming.validate_feature_name(feature.name)
                if not is_valid:
                    logger.error(f"特征名称无效: {error}")
                    continue
                
                output_type = feature.get_output_type()
                
                # 生成ALTER SQL
                alter_sql = f"ALTER STABLE {full_table_name} ADD COLUMN {feature.name} {output_type}"
                
                try:
                    if self.td_client:
                        await self.td_client.execute(alter_sql)
                        logger.info(f"✅ 添加特征列成功: {feature.name}")
                        success_count += 1
                    else:
                        logger.warning(f"TDengine客户端未配置，跳过添加列: {feature.name}")
                        success_count += 1
                except Exception as e:
                    error_msg = str(e).lower()
                    if "duplicated column" in error_msg or "column already exists" in error_msg:
                        logger.debug(f"特征列已存在，跳过: {feature.name}")
                        success_count += 1
                    else:
                        logger.error(f"❌ 添加特征列失败 {feature.name}: {e}")
            
            return success_count == len(new_features)
            
        except TableNameError as e:
            logger.error(f"❌ Schema演进失败 - 命名错误: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Schema演进失败: {e}")
            return False
    
    async def query_features(
        self,
        category_code: str,
        view_name: str,
        asset_id: Optional[int] = None,
        asset_code: Optional[str] = None,
        feature_names: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        查询特征数据
        
        实现需求6.3: 当查询特征数据时，平台应支持按资产、时间范围和特征名筛选
        
        Args:
            category_code: 资产类别编码
            view_name: 特征视图名称
            asset_id: 资产ID (可选)
            asset_code: 资产编码 (可选)
            feature_names: 特征名称列表 (可选，为空则查询所有特征)
            start_time: 开始时间 (可选)
            end_time: 结束时间 (可选)
            limit: 返回记录数限制
        
        Returns:
            List[Dict]: 特征数据列表
            
        Example:
            >>> store = FeatureStore()
            >>> data = await store.query_features(
            ...     "motor", "realtime_stats",
            ...     asset_id=1,
            ...     feature_names=["avg_current", "max_voltage"],
            ...     start_time=datetime(2024, 1, 1),
            ...     end_time=datetime(2024, 1, 2)
            ... )
        """
        try:
            table_name = FeatureTableNaming.get_stable_name(category_code, view_name)
            full_table_name = f"{self.database}.{table_name}"
            
            # 构建SELECT子句
            if feature_names:
                # 验证特征名称
                for name in feature_names:
                    is_valid, error = FeatureTableNaming.validate_feature_name(name)
                    if not is_valid:
                        raise FeatureQueryError(f"无效的特征名称 {name}: {error}")
                
                select_columns = ["ts", "asset_id", "asset_code"] + feature_names
                select_clause = ", ".join(select_columns)
            else:
                select_clause = "*"
            
            # 构建WHERE子句
            conditions = []
            
            if asset_id is not None:
                conditions.append(f"asset_id = {asset_id}")
            
            if asset_code is not None:
                conditions.append(f"asset_code = '{asset_code}'")
            
            if start_time is not None:
                conditions.append(f"ts >= '{start_time.isoformat()}'")
            
            if end_time is not None:
                conditions.append(f"ts <= '{end_time.isoformat()}'")
            
            where_clause = " AND ".join(conditions) if conditions else ""
            
            # 构建完整SQL
            sql = f"SELECT {select_clause} FROM {full_table_name}"
            if where_clause:
                sql += f" WHERE {where_clause}"
            sql += f" ORDER BY ts DESC LIMIT {limit}"
            
            logger.debug(f"查询特征数据SQL: {sql}")
            
            # 执行查询
            if self.td_client:
                result = await self.td_client.query(sql)
                return result if result else []
            else:
                logger.warning("TDengine客户端未配置，返回空结果")
                return []
            
        except TableNameError as e:
            logger.error(f"❌ 特征查询失败 - 命名错误: {e}")
            raise FeatureQueryError(f"表名错误: {e}")
        except FeatureQueryError:
            raise
        except Exception as e:
            logger.error(f"❌ 特征查询失败: {e}")
            raise FeatureQueryError(f"查询失败: {e}")
    
    async def ensure_child_table(
        self,
        category_code: str,
        view_name: str,
        asset_code: str,
        asset_id: int
    ) -> bool:
        """
        确保子表存在
        
        Args:
            category_code: 资产类别编码
            view_name: 特征视图名称
            asset_code: 资产编码
            asset_id: 资产ID
        
        Returns:
            bool: 是否成功
        """
        try:
            create_sql = FeatureTableNaming.get_create_child_table_sql(
                category_code, view_name, asset_code, asset_id, self.database
            )
            
            if self.td_client:
                await self.td_client.execute(create_sql)
                logger.debug(f"子表已确保存在: {category_code}_{view_name}_{asset_code}")
            
            return True
        except Exception as e:
            logger.error(f"确保子表存在失败: {e}")
            return False
    
    async def write_feature(
        self,
        category_code: str,
        view_name: str,
        record: FeatureRecord
    ) -> bool:
        """
        写入特征数据
        
        Args:
            category_code: 资产类别编码
            view_name: 特征视图名称
            record: 特征记录
        
        Returns:
            bool: 写入是否成功
        """
        try:
            # 确保子表存在
            await self.ensure_child_table(
                category_code, view_name, 
                record.asset_code, record.asset_id
            )
            
            child_table_name = FeatureTableNaming.get_child_table_name(
                category_code, view_name, record.asset_code
            )
            full_table_name = f"{self.database}.{child_table_name}"
            
            # 构建INSERT SQL
            columns = ["ts"] + list(record.features.keys())
            values = [f"'{record.timestamp.isoformat()}'"]
            
            for value in record.features.values():
                if isinstance(value, str):
                    values.append(f"'{value}'")
                elif value is None:
                    values.append("NULL")
                else:
                    values.append(str(value))
            
            columns_str = ", ".join(columns)
            values_str = ", ".join(values)
            
            sql = f"INSERT INTO {full_table_name} ({columns_str}) VALUES ({values_str})"
            
            if self.td_client:
                await self.td_client.execute(sql)
                logger.debug(f"特征数据写入成功: {child_table_name}")
            
            return True
        except Exception as e:
            logger.error(f"特征数据写入失败: {e}")
            return False
    
    async def table_exists(
        self,
        category_code: str,
        view_name: str
    ) -> bool:
        """
        检查特征表是否存在
        
        Args:
            category_code: 资产类别编码
            view_name: 特征视图名称
        
        Returns:
            bool: 表是否存在
        """
        try:
            table_name = FeatureTableNaming.get_stable_name(category_code, view_name)
            
            if self.td_client:
                sql = f"DESCRIBE {self.database}.{table_name}"
                try:
                    await self.td_client.query(sql)
                    return True
                except Exception:
                    return False
            
            return False
        except TableNameError:
            return False
    
    async def get_table_schema(
        self,
        category_code: str,
        view_name: str
    ) -> List[Dict[str, Any]]:
        """
        获取特征表Schema
        
        Args:
            category_code: 资产类别编码
            view_name: 特征视图名称
        
        Returns:
            List[Dict]: 列信息列表
        """
        try:
            table_name = FeatureTableNaming.get_stable_name(category_code, view_name)
            
            if self.td_client:
                sql = f"DESCRIBE {self.database}.{table_name}"
                result = await self.td_client.query(sql)
                return result if result else []
            
            return []
        except Exception as e:
            logger.error(f"获取表Schema失败: {e}")
            return []
    
    def _get_output_type(self, function: str) -> str:
        """
        获取聚合函数的输出类型
        
        Args:
            function: 聚合函数名称
        
        Returns:
            str: TDengine数据类型
        """
        return FUNCTION_OUTPUT_TYPES.get(
            function.lower(), 
            FeatureOutputType.DOUBLE
        ).value


# =====================================================
# 全局实例
# =====================================================

feature_store = FeatureStore()
