#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据一致性验证器

验证新旧数据结构的一致性，生成一致性报告。

需求: 8.3 - 当验证数据一致性时，平台应提供新旧数据对比报告
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class DataMismatch:
    """
    数据不匹配记录
    
    Attributes:
        key: 数据键（通常是时间戳+资产编码）
        field: 不匹配的字段名
        new_value: 新结构中的值
        old_value: 旧结构中的值
        timestamp: 数据时间戳
        asset_code: 资产编码
    """
    key: str
    field: str
    new_value: Any
    old_value: Any
    timestamp: Optional[datetime] = None
    asset_code: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "key": self.key,
            "field": self.field,
            "new_value": self._serialize_value(self.new_value),
            "old_value": self._serialize_value(self.old_value),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "asset_code": self.asset_code,
        }
    
    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """序列化值（处理不可JSON序列化的类型）"""
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, (set, frozenset)):
            return list(value)
        elif hasattr(value, '__dict__'):
            return str(value)
        return value


@dataclass
class ConsistencyReport:
    """
    一致性报告
    
    Attributes:
        category_code: 资产类别编码
        time_range_hours: 验证的时间范围（小时）
        check_time: 验证时间
        new_structure_count: 新结构记录数
        old_structure_count: 旧结构记录数
        matched_count: 匹配记录数
        mismatched_count: 不匹配记录数
        missing_in_new: 新结构中缺失的记录数
        missing_in_old: 旧结构中缺失的记录数
        consistency_rate: 一致性率
        mismatches: 不匹配详情列表
        summary: 摘要信息
    """
    category_code: str
    time_range_hours: int
    check_time: datetime
    new_structure_count: int = 0
    old_structure_count: int = 0
    matched_count: int = 0
    mismatched_count: int = 0
    missing_in_new: int = 0
    missing_in_old: int = 0
    consistency_rate: float = 0.0
    mismatches: List[DataMismatch] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "category_code": self.category_code,
            "time_range_hours": self.time_range_hours,
            "check_time": self.check_time.isoformat(),
            "new_structure_count": self.new_structure_count,
            "old_structure_count": self.old_structure_count,
            "matched_count": self.matched_count,
            "mismatched_count": self.mismatched_count,
            "missing_in_new": self.missing_in_new,
            "missing_in_old": self.missing_in_old,
            "consistency_rate": self.consistency_rate,
            "mismatches": [m.to_dict() for m in self.mismatches],
            "summary": self.summary,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConsistencyReport":
        """从字典创建"""
        check_time = data.get("check_time")
        if isinstance(check_time, str):
            check_time = datetime.fromisoformat(check_time)
        elif check_time is None:
            check_time = datetime.now()
        
        mismatches = []
        for m in data.get("mismatches", []):
            timestamp = m.get("timestamp")
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            mismatches.append(DataMismatch(
                key=m.get("key", ""),
                field=m.get("field", ""),
                new_value=m.get("new_value"),
                old_value=m.get("old_value"),
                timestamp=timestamp,
                asset_code=m.get("asset_code"),
            ))
        
        return cls(
            category_code=data.get("category_code", ""),
            time_range_hours=data.get("time_range_hours", 24),
            check_time=check_time,
            new_structure_count=data.get("new_structure_count", 0),
            old_structure_count=data.get("old_structure_count", 0),
            matched_count=data.get("matched_count", 0),
            mismatched_count=data.get("mismatched_count", 0),
            missing_in_new=data.get("missing_in_new", 0),
            missing_in_old=data.get("missing_in_old", 0),
            consistency_rate=data.get("consistency_rate", 0.0),
            mismatches=mismatches,
            summary=data.get("summary", {}),
        )
    
    def calculate_consistency_rate(self):
        """计算一致性率"""
        total = self.new_structure_count
        if total > 0:
            self.consistency_rate = self.matched_count / total
        else:
            self.consistency_rate = 1.0 if self.old_structure_count == 0 else 0.0
    
    def generate_summary(self):
        """生成摘要信息"""
        self.summary = {
            "status": "healthy" if self.consistency_rate >= 0.99 else (
                "warning" if self.consistency_rate >= 0.95 else "critical"
            ),
            "total_records": self.new_structure_count,
            "consistency_percentage": round(self.consistency_rate * 100, 2),
            "issues_found": self.mismatched_count + self.missing_in_new + self.missing_in_old,
            "recommendation": self._get_recommendation(),
        }
    
    def _get_recommendation(self) -> str:
        """获取建议"""
        if self.consistency_rate >= 0.99:
            return "数据一致性良好，可以考虑关闭双写模式"
        elif self.consistency_rate >= 0.95:
            return "存在少量不一致，建议检查不匹配记录"
        else:
            return "数据一致性较差，建议暂缓关闭双写模式并排查问题"


class ConsistencyVerifier:
    """
    一致性验证器
    
    验证新旧数据结构的一致性，支持多种比较策略。
    """
    
    def __init__(self):
        """初始化验证器"""
        self._td_client = None
        self._pg_conn = None
        
        # 比较配置
        self._float_tolerance = 0.0001  # 浮点数比较容差
        self._ignore_fields = {"created_at", "updated_at", "id"}  # 忽略的字段
        self._max_mismatches = 1000  # 最大记录的不匹配数
    
    async def verify_consistency(
        self,
        category_code: str,
        time_range_hours: int = 24,
        asset_codes: Optional[List[str]] = None,
        sample_rate: float = 1.0
    ) -> ConsistencyReport:
        """
        验证数据一致性
        
        Args:
            category_code: 资产类别编码
            time_range_hours: 时间范围（小时）
            asset_codes: 指定的资产编码列表（可选）
            sample_rate: 采样率（0-1，用于大数据量时的抽样验证）
        
        Returns:
            ConsistencyReport: 一致性报告
        """
        report = ConsistencyReport(
            category_code=category_code,
            time_range_hours=time_range_hours,
            check_time=datetime.now(),
        )
        
        try:
            # 计算时间范围
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=time_range_hours)
            
            # 查询新结构数据
            new_data = await self._query_new_structure(
                category_code, start_time, end_time, asset_codes
            )
            report.new_structure_count = len(new_data)
            
            # 查询旧结构数据
            old_data = await self._query_old_structure(
                category_code, start_time, end_time, asset_codes
            )
            report.old_structure_count = len(old_data)
            
            # 对比数据
            self._compare_data(new_data, old_data, report, sample_rate)
            
            # 计算一致性率
            report.calculate_consistency_rate()
            
            # 生成摘要
            report.generate_summary()
            
            logger.info(
                f"一致性验证完成: {category_code}, "
                f"一致性率={report.consistency_rate:.2%}, "
                f"匹配={report.matched_count}, 不匹配={report.mismatched_count}"
            )
            
        except Exception as e:
            logger.error(f"一致性验证失败: {e}")
            report.summary = {
                "status": "error",
                "error": str(e),
            }
        
        return report
    
    async def _query_new_structure(
        self,
        category_code: str,
        start_time: datetime,
        end_time: datetime,
        asset_codes: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        查询新结构数据
        
        Returns:
            Dict[str, Dict]: 以key为索引的数据字典
        """
        data = {}
        
        try:
            td_client = await self._get_td_client()
            if td_client is None:
                logger.debug("TDengine客户端不可用，返回空数据")
                return data
            
            # 构建查询SQL
            table_pattern = f"raw_{category_code}_%"
            
            # 查询超级表
            sql = f"""
                SELECT * FROM raw_{category_code}
                WHERE ts >= '{start_time.isoformat()}' 
                AND ts <= '{end_time.isoformat()}'
            """
            
            if asset_codes:
                asset_filter = ", ".join([f"'{code}'" for code in asset_codes])
                sql += f" AND asset_code IN ({asset_filter})"
            
            sql += " ORDER BY ts"
            
            result = await td_client.query(sql)
            
            for row in result:
                # 生成唯一键
                ts = row.get("ts")
                asset_code = row.get("asset_code", "")
                key = f"{ts}_{asset_code}"
                
                data[key] = {
                    "timestamp": ts,
                    "asset_code": asset_code,
                    "signals": {k: v for k, v in row.items() if k not in ("ts", "asset_code")},
                }
                
        except Exception as e:
            logger.debug(f"查询新结构数据失败: {e}")
        
        return data
    
    async def _query_old_structure(
        self,
        category_code: str,
        start_time: datetime,
        end_time: datetime,
        asset_codes: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        查询旧结构数据
        
        Returns:
            Dict[str, Dict]: 以key为索引的数据字典
        """
        data = {}
        
        try:
            # 尝试从PostgreSQL查询旧数据
            conn = await self._get_pg_connection()
            if conn is None:
                logger.debug("PostgreSQL连接不可用，返回空数据")
                return data
            
            # 查询旧的device_data表
            sql = """
                SELECT dd.*, a.code as asset_code
                FROM device_data dd
                JOIN t_assets a ON dd.device_id = a.id
                JOIN t_asset_category ac ON a.category_id = ac.id
                WHERE ac.code = $1
                AND dd.created_at >= $2
                AND dd.created_at <= $3
            """
            
            params = [category_code, start_time, end_time]
            
            if asset_codes:
                sql += " AND a.code = ANY($4)"
                params.append(asset_codes)
            
            sql += " ORDER BY dd.created_at"
            
            rows = await conn.fetch(sql, *params)
            
            for row in rows:
                ts = row.get("created_at")
                asset_code = row.get("asset_code", "")
                key = f"{ts}_{asset_code}"
                
                # 解析JSON数据
                raw_data = row.get("data", {})
                if isinstance(raw_data, str):
                    raw_data = json.loads(raw_data)
                
                data[key] = {
                    "timestamp": ts,
                    "asset_code": asset_code,
                    "signals": raw_data,
                }
                
        except Exception as e:
            logger.debug(f"查询旧结构数据失败: {e}")
        
        return data
    
    def _compare_data(
        self,
        new_data: Dict[str, Dict[str, Any]],
        old_data: Dict[str, Dict[str, Any]],
        report: ConsistencyReport,
        sample_rate: float = 1.0
    ):
        """
        对比新旧数据
        
        Args:
            new_data: 新结构数据
            old_data: 旧结构数据
            report: 一致性报告
            sample_rate: 采样率
        """
        import random
        
        # 获取所有键
        all_keys = set(new_data.keys()) | set(old_data.keys())
        
        # 采样
        if sample_rate < 1.0:
            sample_size = int(len(all_keys) * sample_rate)
            all_keys = set(random.sample(list(all_keys), sample_size))
        
        for key in all_keys:
            new_record = new_data.get(key)
            old_record = old_data.get(key)
            
            if new_record is None:
                # 新结构中缺失
                report.missing_in_new += 1
                if len(report.mismatches) < self._max_mismatches:
                    report.mismatches.append(DataMismatch(
                        key=key,
                        field="__record__",
                        new_value=None,
                        old_value="exists",
                        timestamp=old_record.get("timestamp") if old_record else None,
                        asset_code=old_record.get("asset_code") if old_record else None,
                    ))
            elif old_record is None:
                # 旧结构中缺失
                report.missing_in_old += 1
                if len(report.mismatches) < self._max_mismatches:
                    report.mismatches.append(DataMismatch(
                        key=key,
                        field="__record__",
                        new_value="exists",
                        old_value=None,
                        timestamp=new_record.get("timestamp"),
                        asset_code=new_record.get("asset_code"),
                    ))
            else:
                # 两边都有，比较内容
                is_match, field_mismatches = self._compare_records(new_record, old_record)
                
                if is_match:
                    report.matched_count += 1
                else:
                    report.mismatched_count += 1
                    
                    # 记录不匹配详情
                    for field, (new_val, old_val) in field_mismatches.items():
                        if len(report.mismatches) < self._max_mismatches:
                            report.mismatches.append(DataMismatch(
                                key=key,
                                field=field,
                                new_value=new_val,
                                old_value=old_val,
                                timestamp=new_record.get("timestamp"),
                                asset_code=new_record.get("asset_code"),
                            ))
    
    def _compare_records(
        self,
        new_record: Dict[str, Any],
        old_record: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Tuple[Any, Any]]]:
        """
        比较两条记录
        
        Returns:
            Tuple[bool, Dict]: (是否匹配, 不匹配字段字典)
        """
        mismatches = {}
        
        new_signals = new_record.get("signals", {})
        old_signals = old_record.get("signals", {})
        
        # 获取所有信号字段
        all_fields = set(new_signals.keys()) | set(old_signals.keys())
        all_fields -= self._ignore_fields
        
        for field in all_fields:
            new_val = new_signals.get(field)
            old_val = old_signals.get(field)
            
            if not self._values_equal(new_val, old_val):
                mismatches[field] = (new_val, old_val)
        
        return len(mismatches) == 0, mismatches
    
    def _values_equal(self, val1: Any, val2: Any) -> bool:
        """
        比较两个值是否相等
        
        支持浮点数容差比较。
        """
        if val1 is None and val2 is None:
            return True
        
        if val1 is None or val2 is None:
            return False
        
        # 浮点数比较
        if isinstance(val1, float) and isinstance(val2, float):
            return abs(val1 - val2) < self._float_tolerance
        
        # 数值类型转换比较
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            return abs(float(val1) - float(val2)) < self._float_tolerance
        
        # 字符串比较（忽略空白）
        if isinstance(val1, str) and isinstance(val2, str):
            return val1.strip() == val2.strip()
        
        # 其他类型直接比较
        return val1 == val2
    
    async def _get_td_client(self):
        """获取TDengine客户端"""
        if self._td_client is not None:
            return self._td_client
        
        try:
            from app.core.tdengine_connector import get_tdengine_client
            self._td_client = await get_tdengine_client()
            return self._td_client
        except Exception as e:
            logger.debug(f"获取TDengine客户端失败: {e}")
            return None
    
    async def _get_pg_connection(self):
        """获取PostgreSQL连接"""
        if self._pg_conn is not None:
            return self._pg_conn
        
        try:
            from app.core.database import get_db_connection
            self._pg_conn = await get_db_connection()
            return self._pg_conn
        except Exception as e:
            logger.debug(f"获取PostgreSQL连接失败: {e}")
            return None
    
    def set_float_tolerance(self, tolerance: float):
        """设置浮点数比较容差"""
        self._float_tolerance = tolerance
    
    def set_ignore_fields(self, fields: set):
        """设置忽略的字段"""
        self._ignore_fields = fields
    
    def set_max_mismatches(self, max_count: int):
        """设置最大记录的不匹配数"""
        self._max_mismatches = max_count


# =====================================================
# 便捷函数
# =====================================================

async def verify_dual_write_consistency(
    category_code: str,
    time_range_hours: int = 24,
    asset_codes: Optional[List[str]] = None
) -> ConsistencyReport:
    """
    验证双写数据一致性
    
    Args:
        category_code: 资产类别编码
        time_range_hours: 时间范围（小时）
        asset_codes: 指定的资产编码列表（可选）
    
    Returns:
        ConsistencyReport: 一致性报告
    """
    verifier = ConsistencyVerifier()
    return await verifier.verify_consistency(
        category_code=category_code,
        time_range_hours=time_range_hours,
        asset_codes=asset_codes,
    )


def create_mock_consistency_report(
    category_code: str,
    matched_count: int,
    mismatched_count: int,
    time_range_hours: int = 24
) -> ConsistencyReport:
    """
    创建模拟的一致性报告（用于测试）
    
    Args:
        category_code: 资产类别编码
        matched_count: 匹配数
        mismatched_count: 不匹配数
        time_range_hours: 时间范围
    
    Returns:
        ConsistencyReport: 一致性报告
    """
    total = matched_count + mismatched_count
    
    report = ConsistencyReport(
        category_code=category_code,
        time_range_hours=time_range_hours,
        check_time=datetime.now(),
        new_structure_count=total,
        old_structure_count=total,
        matched_count=matched_count,
        mismatched_count=mismatched_count,
    )
    
    report.calculate_consistency_rate()
    report.generate_summary()
    
    return report
