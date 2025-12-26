#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康评分服务
基于多维度指标综合评估设备健康状况
"""

from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime, timedelta
import numpy as np
from loguru import logger


class HealthGrade(str, Enum):
    """健康等级枚举"""
    A_EXCELLENT = "A-优秀"
    B_GOOD = "B-良好"
    C_NORMAL = "C-一般"
    D_POOR = "D-较差"
    F_CRITICAL = "F-危险"


class HealthDimension(str, Enum):
    """健康维度枚举"""
    PERFORMANCE = "performance"  # 性能指标
    ANOMALY = "anomaly"  # 异常频率
    TREND = "trend"  # 趋势健康
    UPTIME = "uptime"  # 运行时长


class PerformanceScorer:
    """性能指标评分器"""
    
    def __init__(self, target_ranges: Optional[Dict[str, tuple]] = None):
        """
        初始化性能评分器
        
        Args:
            target_ranges: 目标范围字典 {指标名: (min, max)}
        """
        self.target_ranges = target_ranges or {}
    
    def score(
        self,
        metrics: Dict[str, float],
        target_ranges: Optional[Dict[str, tuple]] = None
    ) -> float:
        """
        基于性能指标计算评分
        
        Args:
            metrics: 当前性能指标 {指标名: 值}
            target_ranges: 目标范围 {指标名: (min, max)}
        
        Returns:
            性能评分 (0-100)
        """
        if not metrics:
            logger.warning("性能指标为空")
            return 0.0
        
        ranges = target_ranges or self.target_ranges
        
        if not ranges:
            # 如果没有目标范围，假设当前值就是良好的
            return 80.0
        
        try:
            scores = []
            
            for metric_name, value in metrics.items():
                if metric_name in ranges:
                    min_val, max_val = ranges[metric_name]
                    
                    # 在范围内得满分，超出范围线性衰减
                    if min_val <= value <= max_val:
                        scores.append(100.0)
                    else:
                        # 计算偏离程度
                        if value < min_val:
                            deviation = min_val - value
                            range_size = max_val - min_val
                        else:
                            deviation = value - max_val
                            range_size = max_val - min_val
                        
                        # 偏离越大，分数越低（最低0分）
                        penalty = min(100, (deviation / range_size) * 50)
                        scores.append(max(0, 100 - penalty))
            
            if scores:
                return float(np.mean(scores))
            else:
                return 80.0  # 默认分数
                
        except Exception as e:
            logger.error(f"计算性能评分失败: {e}")
            return 0.0


class AnomalyScorer:
    """异常频率评分器"""
    
    def score(
        self,
        anomaly_count: int,
        total_count: int,
        time_window_hours: float = 24.0
    ) -> float:
        """
        基于异常频率计算评分
        
        Args:
            anomaly_count: 异常数量
            total_count: 总数据点数
            time_window_hours: 时间窗口（小时）
        
        Returns:
            异常评分 (0-100)
        """
        if total_count <= 0:
            return 100.0  # 无数据，假设正常
        
        try:
            # 计算异常率
            anomaly_rate = anomaly_count / total_count
            
            # 根据异常率计算分数
            # 0% 异常 -> 100分
            # 1% 异常 -> 95分
            # 5% 异常 -> 80分
            # 10% 异常 -> 60分
            # 20% 异常 -> 30分
            # >30% 异常 -> 0分
            
            if anomaly_rate <= 0.01:
                score = 100 - anomaly_rate * 500
            elif anomaly_rate <= 0.05:
                score = 95 - (anomaly_rate - 0.01) * 375
            elif anomaly_rate <= 0.10:
                score = 80 - (anomaly_rate - 0.05) * 400
            elif anomaly_rate <= 0.20:
                score = 60 - (anomaly_rate - 0.10) * 300
            else:
                score = max(0, 30 - (anomaly_rate - 0.20) * 100)
            
            return float(max(0, min(100, score)))
            
        except Exception as e:
            logger.error(f"计算异常评分失败: {e}")
            return 0.0


class TrendScorer:
    """趋势健康评分器"""
    
    def score(
        self,
        trend_direction: str,
        trend_stability: float = 0.5,
        is_increasing_good: bool = True
    ) -> float:
        """
        基于趋势方向和稳定性计算评分
        
        Args:
            trend_direction: 趋势方向 ("上升", "下降", "平稳")
            trend_stability: 趋势稳定性 (0-1, 1表示非常稳定)
            is_increasing_good: 上升趋势是否为好（如温度上升可能不好）
        
        Returns:
            趋势评分 (0-100)
        """
        try:
            # 基础分数
            base_score = 0.0
            
            if trend_direction == "平稳":
                # 平稳趋势通常是好的
                base_score = 90.0
            elif trend_direction == "上升":
                base_score = 80.0 if is_increasing_good else 40.0
            elif trend_direction == "下降":
                base_score = 40.0 if is_increasing_good else 80.0
            else:
                base_score = 60.0  # 未知趋势
            
            # 根据稳定性调整分数
            # 稳定性越高，分数越接近基础分数
            # 稳定性低，分数会有较大波动
            stability_factor = 0.5 + 0.5 * trend_stability
            final_score = base_score * stability_factor
            
            return float(max(0, min(100, final_score)))
            
        except Exception as e:
            logger.error(f"计算趋势评分失败: {e}")
            return 0.0


class UptimeScorer:
    """运行时长评分器"""
    
    def score(
        self,
        uptime_hours: float,
        expected_uptime_hours: float = 720.0  # 30天
    ) -> float:
        """
        基于运行时长计算评分
        
        Args:
            uptime_hours: 实际运行时长（小时）
            expected_uptime_hours: 期望运行时长（小时）
        
        Returns:
            运行时长评分 (0-100)
        """
        try:
            if uptime_hours <= 0:
                return 0.0
            
            # 计算运行率
            uptime_ratio = uptime_hours / expected_uptime_hours
            
            # 运行时长评分规则：
            # 100% -> 100分
            # 95% -> 95分
            # 90% -> 85分
            # 80% -> 70分
            # 70% -> 50分
            # <50% -> 线性降至0分
            
            if uptime_ratio >= 1.0:
                score = 100.0
            elif uptime_ratio >= 0.95:
                score = 95 + (uptime_ratio - 0.95) * 100
            elif uptime_ratio >= 0.90:
                score = 85 + (uptime_ratio - 0.90) * 200
            elif uptime_ratio >= 0.80:
                score = 70 + (uptime_ratio - 0.80) * 150
            elif uptime_ratio >= 0.70:
                score = 50 + (uptime_ratio - 0.70) * 200
            elif uptime_ratio >= 0.50:
                score = (uptime_ratio - 0.50) * 250
            else:
                score = uptime_ratio * 100
            
            return float(max(0, min(100, score)))
            
        except Exception as e:
            logger.error(f"计算运行时长评分失败: {e}")
            return 0.0


class HealthScoreCalculator:
    """健康评分计算器"""
    
    # 默认权重配置
    DEFAULT_WEIGHTS = {
        HealthDimension.PERFORMANCE: 0.30,  # 性能指标 30%
        HealthDimension.ANOMALY: 0.25,      # 异常频率 25%
        HealthDimension.TREND: 0.25,        # 趋势健康 25%
        HealthDimension.UPTIME: 0.20,       # 运行时长 20%
    }
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        初始化健康评分计算器
        
        Args:
            weights: 自定义权重配置
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
        self.performance_scorer = PerformanceScorer()
        self.anomaly_scorer = AnomalyScorer()
        self.trend_scorer = TrendScorer()
        self.uptime_scorer = UptimeScorer()
    
    def calculate(
        self,
        performance_metrics: Optional[Dict[str, float]] = None,
        anomaly_count: int = 0,
        total_count: int = 100,
        trend_direction: str = "平稳",
        trend_stability: float = 0.8,
        uptime_hours: float = 720.0,
        target_ranges: Optional[Dict[str, tuple]] = None,
        is_increasing_good: bool = True
    ) -> Dict[str, Any]:
        """
        计算综合健康评分
        
        Args:
            performance_metrics: 性能指标
            anomaly_count: 异常数量
            total_count: 总数据点数
            trend_direction: 趋势方向
            trend_stability: 趋势稳定性
            uptime_hours: 运行时长
            target_ranges: 性能目标范围
            is_increasing_good: 上升是否为好
        
        Returns:
            评分结果字典
        """
        try:
            # 计算各维度分数
            scores = {}
            
            # 性能评分
            if performance_metrics:
                scores[HealthDimension.PERFORMANCE.value] = self.performance_scorer.score(
                    performance_metrics, target_ranges
                )
            else:
                scores[HealthDimension.PERFORMANCE.value] = 80.0  # 默认分数
            
            # 异常评分
            scores[HealthDimension.ANOMALY.value] = self.anomaly_scorer.score(
                anomaly_count, total_count
            )
            
            # 趋势评分
            scores[HealthDimension.TREND.value] = self.trend_scorer.score(
                trend_direction, trend_stability, is_increasing_good
            )
            
            # 运行时长评分
            scores[HealthDimension.UPTIME.value] = self.uptime_scorer.score(uptime_hours)
            
            # 计算加权总分
            total_score = 0.0
            for dimension, weight in self.weights.items():
                dimension_key = dimension.value if isinstance(dimension, HealthDimension) else dimension
                total_score += scores.get(dimension_key, 0) * weight
            
            # 确定健康等级
            grade = self._get_grade(total_score)
            
            result = {
                'total_score': round(total_score, 2),
                'grade': grade.value,
                'grade_code': grade.name,
                'dimension_scores': {
                    'performance': round(scores.get(HealthDimension.PERFORMANCE.value, 0), 2),
                    'anomaly': round(scores.get(HealthDimension.ANOMALY.value, 0), 2),
                    'trend': round(scores.get(HealthDimension.TREND.value, 0), 2),
                    'uptime': round(scores.get(HealthDimension.UPTIME.value, 0), 2),
                },
                'weights': {k.value if isinstance(k, HealthDimension) else k: v for k, v in self.weights.items()}
            }
            
            logger.info(f"健康评分计算完成: {total_score:.2f} ({grade.value})")
            return result
            
        except Exception as e:
            logger.error(f"健康评分计算失败: {e}")
            return {
                'total_score': 0.0,
                'grade': HealthGrade.F_CRITICAL.value,
                'grade_code': HealthGrade.F_CRITICAL.name,
                'dimension_scores': {},
                'weights': {}
            }
    
    def _get_grade(self, score: float) -> HealthGrade:
        """
        根据分数确定健康等级
        
        Args:
            score: 总分 (0-100)
        
        Returns:
            健康等级
        """
        if score >= 90:
            return HealthGrade.A_EXCELLENT
        elif score >= 80:
            return HealthGrade.B_GOOD
        elif score >= 70:
            return HealthGrade.C_NORMAL
        elif score >= 60:
            return HealthGrade.D_POOR
        else:
            return HealthGrade.F_CRITICAL
    
    def batch_calculate(
        self,
        devices_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        批量计算多个设备的健康评分
        
        Args:
            devices_data: {设备ID: 设备数据} 的字典
        
        Returns:
            {设备ID: 评分结果} 的字典
        """
        results = {}
        for device_id, data in devices_data.items():
            try:
                score = self.calculate(**data)
                results[device_id] = score
                logger.debug(f"设备 {device_id} 健康评分: {score['total_score']}")
            except Exception as e:
                logger.error(f"计算设备 {device_id} 健康评分失败: {e}")
                results[device_id] = {
                    'total_score': 0.0,
                    'grade': HealthGrade.F_CRITICAL.value,
                    'error': str(e)
                }
        
        return results


# 创建全局实例
health_score_calculator = HealthScoreCalculator()

