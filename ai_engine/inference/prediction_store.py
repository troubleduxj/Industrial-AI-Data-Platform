#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预测结果存储服务

实现预测结果的双写存储（PostgreSQL和TDengine），
支持预测历史查询和统计计算。

需求:
- 4.1: AI模型产生预测结果时，平台应同时写入PostgreSQL和TDengine
- 4.2: TDengine应使用pred_{category}超级表结构
- 4.3: 支持按时间范围、资产和模型筛选
- 4.4: 支持计算准确率、偏差等统计指标
- 4.5: 支持预测结果与实际值的对比分析查询
- 8.1: 双写模式支持
"""

import re
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger


class PredictionStoreError(Exception):
    """预测存储异常"""
    pass


class TableNameError(PredictionStoreError):
    """表名错误"""
    pass


@dataclass
class PredictionRecord:
    """预测记录数据类"""
    model_id: int
    model_version: str
    asset_id: int
    asset_code: str
    category_code: str
    predicted_value: float
    confidence: float
    is_anomaly: Optional[bool] = None
    anomaly_score: Optional[float] = None
    target_time: Optional[datetime] = None
    actual_value: Optional[float] = None
    prediction_details: Optional[Dict[str, Any]] = None
    prediction_time: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        # 处理datetime序列化
        if self.prediction_time:
            result["prediction_time"] = self.prediction_time.isoformat()
        if self.target_time:
            result["target_time"] = self.target_time.isoformat()
        return result


@dataclass
class PredictionQueryResult:
    """预测查询结果"""
    records: List[Dict[str, Any]]
    total_count: int
    page: int = 1
    page_size: int = 100


@dataclass
class PredictionStatistics:
    """预测统计结果"""
    model_id: int
    category_code: str
    time_range_hours: int
    total_predictions: int
    predictions_with_actual: int
    accuracy_rate: Optional[float] = None
    mean_absolute_error: Optional[float] = None
    mean_squared_error: Optional[float] = None
    root_mean_squared_error: Optional[float] = None
    mean_bias: Optional[float] = None
    anomaly_count: int = 0
    anomaly_rate: Optional[float] = None


class PredictionTableNaming:
    """
    预测表命名工具类
    
    属性12: 预测表命名规范
    对于任何资产类别的预测结果，TDengine表名应遵循pred_{category}模式
    """
    
    # 有效的类别编码正则表达式
    CATEGORY_CODE_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')
    
    # 有效的资产编码正则表达式
    ASSET_CODE_PATTERN = re.compile(r'^[A-Za-z][A-Za-z0-9_]*$')
    
    # 超级表名前缀
    STABLE_PREFIX = "pred_"
    
    @classmethod
    def validate_category_code(cls, category_code: str) -> Tuple[bool, Optional[str]]:
        """
        验证类别编码是否有效
        
        Args:
            category_code: 类别编码
        
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误信息)
        """
        if not category_code:
            return False, "类别编码不能为空"
        
        if not isinstance(category_code, str):
            return False, "类别编码必须是字符串"
        
        # 转换为小写进行验证
        code_lower = category_code.lower()
        
        if not cls.CATEGORY_CODE_PATTERN.match(code_lower):
            return False, f"类别编码格式无效: {category_code}，必须以字母开头，只能包含小写字母、数字和下划线"
        
        if len(code_lower) > 50:
            return False, f"类别编码过长: {len(code_lower)}，最大长度50"
        
        return True, None
    
    @classmethod
    def validate_asset_code(cls, asset_code: str) -> Tuple[bool, Optional[str]]:
        """
        验证资产编码是否有效
        
        Args:
            asset_code: 资产编码
        
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误信息)
        """
        if not asset_code:
            return False, "资产编码不能为空"
        
        if not isinstance(asset_code, str):
            return False, "资产编码必须是字符串"
        
        if not cls.ASSET_CODE_PATTERN.match(asset_code):
            return False, f"资产编码格式无效: {asset_code}，必须以字母开头，只能包含字母、数字和下划线"
        
        if len(asset_code) > 64:
            return False, f"资产编码过长: {len(asset_code)}，最大长度64"
        
        return True, None
    
    @classmethod
    def get_stable_name(cls, category_code: str) -> str:
        """
        获取超级表名
        
        属性12: 预测表命名规范
        对于任何资产类别的预测结果，TDengine表名应遵循pred_{category}模式
        
        Args:
            category_code: 类别编码
        
        Returns:
            str: 超级表名 (pred_{category_code})
        
        Raises:
            TableNameError: 类别编码无效
        """
        is_valid, error = cls.validate_category_code(category_code)
        if not is_valid:
            raise TableNameError(error)
        
        return f"{cls.STABLE_PREFIX}{category_code.lower()}"
    
    @classmethod
    def get_child_table_name(cls, category_code: str, asset_code: str) -> str:
        """
        获取子表名
        
        Args:
            category_code: 类别编码
            asset_code: 资产编码
        
        Returns:
            str: 子表名 (pred_{category_code}_{asset_code})
        
        Raises:
            TableNameError: 编码无效
        """
        is_valid, error = cls.validate_category_code(category_code)
        if not is_valid:
            raise TableNameError(f"类别编码错误: {error}")
        
        is_valid, error = cls.validate_asset_code(asset_code)
        if not is_valid:
            raise TableNameError(f"资产编码错误: {error}")
        
        return f"{cls.STABLE_PREFIX}{category_code.lower()}_{asset_code}"
    
    @classmethod
    def parse_stable_name(cls, table_name: str) -> Optional[str]:
        """
        从超级表名解析类别编码
        
        Args:
            table_name: 表名
        
        Returns:
            Optional[str]: 类别编码，如果不是有效的超级表名则返回None
        """
        if not table_name or not table_name.startswith(cls.STABLE_PREFIX):
            return None
        
        category_code = table_name[len(cls.STABLE_PREFIX):]
        
        # 直接验证整个类别编码（超级表名不包含资产编码）
        # 超级表名格式: pred_{category_code}
        # 子表名格式: pred_{category_code}_{asset_code}
        # 这里只处理超级表名，直接返回去掉前缀后的部分
        
        is_valid, _ = cls.validate_category_code(category_code)
        if is_valid:
            return category_code
        
        return None
    
    @classmethod
    def is_valid_stable_name(cls, table_name: str) -> bool:
        """
        检查是否是有效的超级表名
        
        Args:
            table_name: 表名
        
        Returns:
            bool: 是否有效
        """
        if not table_name or not table_name.startswith(cls.STABLE_PREFIX):
            return False
        
        category_code = table_name[len(cls.STABLE_PREFIX):]
        is_valid, _ = cls.validate_category_code(category_code)
        return is_valid
    
    @classmethod
    def get_create_stable_sql(cls, category_code: str, database: str = "") -> str:
        """
        获取创建超级表的SQL语句
        
        Args:
            category_code: 类别编码
            database: 数据库名（可选）
        
        Returns:
            str: CREATE STABLE SQL语句
        """
        stable_name = cls.get_stable_name(category_code)
        
        if database:
            full_name = f"{database}.{stable_name}"
        else:
            full_name = stable_name
        
        return f"""CREATE STABLE IF NOT EXISTS {full_name} (
    ts TIMESTAMP,
    model_id INT,
    model_version NCHAR(32),
    predicted_value DOUBLE,
    confidence DOUBLE,
    is_anomaly BOOL,
    anomaly_score DOUBLE,
    target_time TIMESTAMP,
    actual_value DOUBLE,
    prediction_details NCHAR(2048)
) TAGS (
    asset_id BIGINT,
    asset_code NCHAR(64)
)"""
    
    @classmethod
    def get_create_child_table_sql(
        cls,
        category_code: str,
        asset_code: str,
        asset_id: int,
        database: str = ""
    ) -> str:
        """
        获取创建子表的SQL语句
        
        Args:
            category_code: 类别编码
            asset_code: 资产编码
            asset_id: 资产ID
            database: 数据库名（可选）
        
        Returns:
            str: CREATE TABLE SQL语句
        """
        stable_name = cls.get_stable_name(category_code)
        child_table_name = cls.get_child_table_name(category_code, asset_code)
        
        if database:
            stable_full = f"{database}.{stable_name}"
            child_full = f"{database}.{child_table_name}"
        else:
            stable_full = stable_name
            child_full = child_table_name
        
        return f"CREATE TABLE IF NOT EXISTS {child_full} USING {stable_full} TAGS ({asset_id}, '{asset_code}')"



class PredictionStore:
    """
    预测结果存储服务 - 双写PostgreSQL和TDengine
    
    需求:
    - 4.1: 同时写入PostgreSQL和TDengine
    - 4.2: TDengine使用pred_{category}超级表结构
    - 4.3: 支持按时间范围、资产和模型筛选
    - 4.4: 支持计算准确率、偏差等统计指标
    - 8.1: 双写模式支持
    """
    
    def __init__(self):
        self._pg_enabled = True
        self._td_enabled = True
        self._td_client = None
        self._database = os.getenv("TDENGINE_DATABASE", "test_db")
        self._created_tables: set = set()  # 缓存已创建的表
    
    def enable_postgresql(self, enabled: bool = True):
        """启用/禁用PostgreSQL写入"""
        self._pg_enabled = enabled
    
    def enable_tdengine(self, enabled: bool = True):
        """启用/禁用TDengine写入"""
        self._td_enabled = enabled
    
    async def save_prediction(
        self,
        model_id: int,
        model_version: str,
        asset_id: int,
        asset_code: str,
        category_code: str,
        prediction_result: Dict[str, Any]
    ) -> Tuple[bool, bool]:
        """
        保存预测结果到双存储
        
        属性11: 预测结果双写一致性
        对于任何AI预测结果，应同时存在于PostgreSQL和TDengine中，且核心字段值一致
        
        Args:
            model_id: 模型ID
            model_version: 模型版本
            asset_id: 资产ID
            asset_code: 资产编码
            category_code: 资产类别编码
            prediction_result: 预测结果字典
        
        Returns:
            Tuple[bool, bool]: (PostgreSQL写入成功, TDengine写入成功)
        """
        pg_success = True
        td_success = True
        
        # 创建预测记录
        record = PredictionRecord(
            model_id=model_id,
            model_version=model_version,
            asset_id=asset_id,
            asset_code=asset_code,
            category_code=category_code,
            predicted_value=prediction_result.get("predicted_value", 0.0),
            confidence=prediction_result.get("confidence", 0.0),
            is_anomaly=prediction_result.get("is_anomaly"),
            anomaly_score=prediction_result.get("anomaly_score"),
            target_time=prediction_result.get("target_time"),
            prediction_details=prediction_result.get("prediction_details", prediction_result),
            prediction_time=datetime.now()
        )
        
        # 1. 写入PostgreSQL
        if self._pg_enabled:
            try:
                await self._save_to_postgresql(record)
                logger.debug(f"✅ PostgreSQL写入成功: model={model_id}, asset={asset_id}")
            except Exception as e:
                logger.error(f"❌ PostgreSQL写入失败: {e}")
                pg_success = False
        
        # 2. 写入TDengine
        if self._td_enabled:
            try:
                await self._save_to_tdengine(record)
                logger.debug(f"✅ TDengine写入成功: model={model_id}, asset={asset_id}")
            except Exception as e:
                logger.error(f"❌ TDengine写入失败: {e}")
                td_success = False
                # TDengine写入失败不影响主流程（属性15: 双写错误隔离）
        
        return pg_success, td_success
    
    async def _save_to_postgresql(self, record: PredictionRecord):
        """保存到PostgreSQL"""
        from app.models.platform_upgrade import AIPrediction, AIModelVersion
        
        # 获取模型版本ID
        version = await AIModelVersion.get_or_none(
            model_id=record.model_id,
            version=record.model_version
        )
        
        prediction = AIPrediction(
            model_version_id=version.id if version else None,
            asset_id=record.asset_id,
            input_data=record.prediction_details or {},
            predicted_value=record.predicted_value,
            confidence=record.confidence,
            is_anomaly=record.is_anomaly,
            anomaly_score=record.anomaly_score,
            prediction_time=record.prediction_time,
            target_time=record.target_time or (record.prediction_time + timedelta(hours=1)),
            prediction_details=record.prediction_details
        )
        await prediction.save()
    
    async def _save_to_tdengine(self, record: PredictionRecord):
        """
        保存到TDengine
        
        属性12: 预测表命名规范
        对于任何资产类别的预测结果，TDengine表名应遵循pred_{category}模式
        """
        # 获取表名
        child_table_name = PredictionTableNaming.get_child_table_name(
            record.category_code,
            record.asset_code
        )
        stable_name = PredictionTableNaming.get_stable_name(record.category_code)
        
        # 确保子表存在
        await self._ensure_child_table(
            stable_name,
            child_table_name,
            record.asset_id,
            record.asset_code,
            record.category_code
        )
        
        # 构建INSERT语句
        target_time_str = f"'{record.target_time.isoformat()}'" if record.target_time else "NULL"
        details_str = json.dumps(record.prediction_details or {})
        
        sql = f"""INSERT INTO {self._database}.{child_table_name} VALUES (
            NOW(),
            {record.model_id},
            '{record.model_version}',
            {record.predicted_value},
            {record.confidence},
            {str(record.is_anomaly).lower() if record.is_anomaly is not None else 'NULL'},
            {record.anomaly_score if record.anomaly_score is not None else 'NULL'},
            {target_time_str},
            NULL,
            '{details_str}'
        )"""
        
        await self._execute_tdengine(sql)
    
    async def _ensure_child_table(
        self,
        stable_name: str,
        child_table_name: str,
        asset_id: int,
        asset_code: str,
        category_code: str
    ):
        """确保子表存在"""
        cache_key = f"{self._database}.{child_table_name}"
        
        if cache_key in self._created_tables:
            return
        
        # 先确保超级表存在
        await self._ensure_stable(category_code)
        
        # 创建子表
        sql = PredictionTableNaming.get_create_child_table_sql(
            category_code,
            asset_code,
            asset_id,
            self._database
        )
        
        try:
            await self._execute_tdengine(sql)
            self._created_tables.add(cache_key)
        except Exception as e:
            # 表可能已存在
            if "table already exists" not in str(e).lower():
                raise
            self._created_tables.add(cache_key)
    
    async def _ensure_stable(self, category_code: str):
        """确保超级表存在"""
        stable_name = PredictionTableNaming.get_stable_name(category_code)
        cache_key = f"{self._database}.{stable_name}"
        
        if cache_key in self._created_tables:
            return
        
        sql = PredictionTableNaming.get_create_stable_sql(category_code, self._database)
        
        try:
            await self._execute_tdengine(sql)
            self._created_tables.add(cache_key)
        except Exception as e:
            if "table already exists" not in str(e).lower():
                raise
            self._created_tables.add(cache_key)
    
    async def _execute_tdengine(self, sql: str):
        """执行TDengine SQL"""
        import httpx
        
        host = os.getenv("TDENGINE_HOST", "localhost")
        port = int(os.getenv("TDENGINE_PORT", "6041"))
        user = os.getenv("TDENGINE_USER", "root")
        password = os.getenv("TDENGINE_PASSWORD", "taosdata")
        
        url = f"http://{host}:{port}/rest/sql/{self._database}"
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                data=sql,
                auth=(user, password)
            )
            
            if response.status_code != 200:
                raise PredictionStoreError(f"TDengine执行失败: {response.text}")
            
            result = response.json()
            if result.get("code") != 0:
                raise PredictionStoreError(f"TDengine错误: {result.get('desc', 'Unknown error')}")
            
            return result
    
    async def query_predictions(
        self,
        category_code: str,
        asset_id: Optional[int] = None,
        asset_code: Optional[str] = None,
        model_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        source: str = "postgresql"
    ) -> PredictionQueryResult:
        """
        查询预测历史
        
        属性13: 预测查询过滤正确性
        对于任何带有时间范围、资产或模型过滤条件的查询，
        返回结果应只包含满足所有条件的记录
        
        Args:
            category_code: 资产类别编码
            asset_id: 资产ID（可选）
            asset_code: 资产编码（可选）
            model_id: 模型ID（可选）
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            limit: 返回数量限制
            offset: 偏移量
            source: 数据源 ("postgresql" 或 "tdengine")
        
        Returns:
            PredictionQueryResult: 查询结果
        """
        if source == "tdengine":
            return await self._query_from_tdengine(
                category_code, asset_id, asset_code, model_id,
                start_time, end_time, limit, offset
            )
        else:
            return await self._query_from_postgresql(
                asset_id, model_id, start_time, end_time, limit, offset
            )
    
    async def _query_from_postgresql(
        self,
        asset_id: Optional[int],
        model_id: Optional[int],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        limit: int,
        offset: int
    ) -> PredictionQueryResult:
        """从PostgreSQL查询"""
        from app.models.platform_upgrade import AIPrediction
        
        query = AIPrediction.all()
        
        if asset_id:
            query = query.filter(asset_id=asset_id)
        
        if model_id:
            query = query.filter(model_version__model_id=model_id)
        
        if start_time:
            query = query.filter(prediction_time__gte=start_time)
        
        if end_time:
            query = query.filter(prediction_time__lte=end_time)
        
        total_count = await query.count()
        
        predictions = await query.order_by("-prediction_time").offset(offset).limit(limit).prefetch_related("model_version")
        
        records = [
            {
                "id": p.id,
                "model_version_id": p.model_version_id,
                "model_version": p.model_version.version if p.model_version else None,
                "model_id": p.model_version.model_id if p.model_version else None,
                "asset_id": p.asset_id,
                "predicted_value": p.predicted_value,
                "confidence": p.confidence,
                "is_anomaly": p.is_anomaly,
                "anomaly_score": p.anomaly_score,
                "prediction_time": p.prediction_time.isoformat() if p.prediction_time else None,
                "target_time": p.target_time.isoformat() if p.target_time else None,
                "actual_value": p.actual_value,
            }
            for p in predictions
        ]
        
        return PredictionQueryResult(
            records=records,
            total_count=total_count,
            page=(offset // limit) + 1 if limit > 0 else 1,
            page_size=limit
        )
    
    async def _query_from_tdengine(
        self,
        category_code: str,
        asset_id: Optional[int],
        asset_code: Optional[str],
        model_id: Optional[int],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        limit: int,
        offset: int
    ) -> PredictionQueryResult:
        """从TDengine查询"""
        stable_name = PredictionTableNaming.get_stable_name(category_code)
        
        # 构建WHERE条件
        conditions = []
        
        if asset_id:
            conditions.append(f"asset_id = {asset_id}")
        
        if asset_code:
            conditions.append(f"asset_code = '{asset_code}'")
        
        if model_id:
            conditions.append(f"model_id = {model_id}")
        
        if start_time:
            conditions.append(f"ts >= '{start_time.isoformat()}'")
        
        if end_time:
            conditions.append(f"ts <= '{end_time.isoformat()}'")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 查询总数
        count_sql = f"SELECT COUNT(*) FROM {self._database}.{stable_name} WHERE {where_clause}"
        count_result = await self._execute_tdengine(count_sql)
        total_count = count_result.get("data", [[0]])[0][0] if count_result.get("data") else 0
        
        # 查询数据
        query_sql = f"""
        SELECT ts, model_id, model_version, predicted_value, confidence, 
               is_anomaly, anomaly_score, target_time, actual_value, 
               asset_id, asset_code
        FROM {self._database}.{stable_name}
        WHERE {where_clause}
        ORDER BY ts DESC
        LIMIT {limit} OFFSET {offset}
        """
        
        result = await self._execute_tdengine(query_sql)
        
        records = []
        if result.get("data"):
            for row in result["data"]:
                records.append({
                    "ts": row[0],
                    "model_id": row[1],
                    "model_version": row[2],
                    "predicted_value": row[3],
                    "confidence": row[4],
                    "is_anomaly": row[5],
                    "anomaly_score": row[6],
                    "target_time": row[7],
                    "actual_value": row[8],
                    "asset_id": row[9],
                    "asset_code": row[10],
                })
        
        return PredictionQueryResult(
            records=records,
            total_count=total_count,
            page=(offset // limit) + 1 if limit > 0 else 1,
            page_size=limit
        )
    
    async def calculate_statistics(
        self,
        category_code: str,
        model_id: int,
        time_range_hours: int = 24,
        asset_id: Optional[int] = None
    ) -> PredictionStatistics:
        """
        计算预测统计指标
        
        需求 4.4: 支持计算准确率、偏差等统计指标
        需求 4.5: 支持预测结果与实际值的对比分析
        
        Args:
            category_code: 资产类别编码
            model_id: 模型ID
            time_range_hours: 时间范围（小时）
            asset_id: 资产ID（可选）
        
        Returns:
            PredictionStatistics: 统计结果
        """
        stable_name = PredictionTableNaming.get_stable_name(category_code)
        
        # 构建WHERE条件
        conditions = [
            f"model_id = {model_id}",
            f"ts >= NOW() - {time_range_hours}h"
        ]
        
        if asset_id:
            conditions.append(f"asset_id = {asset_id}")
        
        where_clause = " AND ".join(conditions)
        
        # 查询总预测数
        total_sql = f"SELECT COUNT(*) FROM {self._database}.{stable_name} WHERE {where_clause}"
        total_result = await self._execute_tdengine(total_sql)
        total_predictions = total_result.get("data", [[0]])[0][0] if total_result.get("data") else 0
        
        # 查询有实际值的预测数
        with_actual_sql = f"""
        SELECT COUNT(*) FROM {self._database}.{stable_name} 
        WHERE {where_clause} AND actual_value IS NOT NULL
        """
        with_actual_result = await self._execute_tdengine(with_actual_sql)
        predictions_with_actual = with_actual_result.get("data", [[0]])[0][0] if with_actual_result.get("data") else 0
        
        # 查询异常数
        anomaly_sql = f"""
        SELECT COUNT(*) FROM {self._database}.{stable_name} 
        WHERE {where_clause} AND is_anomaly = true
        """
        anomaly_result = await self._execute_tdengine(anomaly_sql)
        anomaly_count = anomaly_result.get("data", [[0]])[0][0] if anomaly_result.get("data") else 0
        
        stats = PredictionStatistics(
            model_id=model_id,
            category_code=category_code,
            time_range_hours=time_range_hours,
            total_predictions=total_predictions,
            predictions_with_actual=predictions_with_actual,
            anomaly_count=anomaly_count,
            anomaly_rate=anomaly_count / total_predictions if total_predictions > 0 else None
        )
        
        # 如果有实际值，计算误差指标
        if predictions_with_actual > 0:
            error_sql = f"""
            SELECT 
                AVG(ABS(predicted_value - actual_value)) as mae,
                AVG(POW(predicted_value - actual_value, 2)) as mse,
                AVG(predicted_value - actual_value) as bias
            FROM {self._database}.{stable_name}
            WHERE {where_clause} AND actual_value IS NOT NULL
            """
            
            try:
                error_result = await self._execute_tdengine(error_sql)
                if error_result.get("data") and error_result["data"][0]:
                    row = error_result["data"][0]
                    stats.mean_absolute_error = row[0]
                    stats.mean_squared_error = row[1]
                    stats.root_mean_squared_error = (row[1] ** 0.5) if row[1] else None
                    stats.mean_bias = row[2]
            except Exception as e:
                logger.warning(f"计算误差指标失败: {e}")
        
        return stats
    
    async def update_actual_value(
        self,
        category_code: str,
        asset_code: str,
        prediction_time: datetime,
        actual_value: float
    ) -> bool:
        """
        更新预测的实际值（用于后续评估）
        
        Args:
            category_code: 资产类别编码
            asset_code: 资产编码
            prediction_time: 预测时间
            actual_value: 实际值
        
        Returns:
            bool: 更新是否成功
        """
        child_table_name = PredictionTableNaming.get_child_table_name(
            category_code, asset_code
        )
        
        # TDengine不支持UPDATE，需要使用其他方式
        # 这里我们记录到PostgreSQL
        try:
            from app.models.platform_upgrade import AIPrediction
            
            # 查找最接近的预测记录
            prediction = await AIPrediction.filter(
                asset__code=asset_code,
                prediction_time__lte=prediction_time,
                prediction_time__gte=prediction_time - timedelta(minutes=5)
            ).order_by("-prediction_time").first()
            
            if prediction:
                prediction.actual_value = actual_value
                prediction.actual_recorded_at = datetime.now()
                await prediction.save()
                return True
            
            return False
        except Exception as e:
            logger.error(f"更新实际值失败: {e}")
            return False


# 全局预测存储服务实例
_prediction_store: Optional[PredictionStore] = None


def get_prediction_store() -> PredictionStore:
    """获取预测存储服务实例"""
    global _prediction_store
    if _prediction_store is None:
        _prediction_store = PredictionStore()
    return _prediction_store
