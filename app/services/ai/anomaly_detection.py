#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常检测服务
支持基于统计和机器学习的异常检测方法
"""

from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from datetime import datetime
import numpy as np
from loguru import logger


class AnomalySeverity(str, Enum):
    """异常严重程度枚举"""
    NORMAL = "正常"
    SLIGHT = "轻微"
    MODERATE = "中等"
    SEVERE = "严重"
    CRITICAL = "危险"


class DetectionMethod(str, Enum):
    """检测方法枚举"""
    STATISTICAL = "statistical"  # 统计方法（3-sigma）
    ISOLATION_FOREST = "isolation_forest"  # 孤立森林
    COMBINED = "combined"  # 组合方法


class StatisticalAnomalyDetector:
    """基于统计的异常检测器（3-sigma规则）"""
    
    def __init__(
        self,
        threshold_sigma: float = 3.0,
        use_mad: bool = False
    ):
        """
        初始化统计异常检测器
        
        Args:
            threshold_sigma: 异常判定阈值（几倍标准差）
            use_mad: 是否使用MAD（中位数绝对偏差）代替标准差（更鲁棒）
        """
        self.threshold_sigma = threshold_sigma
        self.use_mad = use_mad
    
    def detect(
        self,
        data: List[float],
        return_scores: bool = False
    ) -> List[Dict[str, Any]]:
        """
        检测异常点
        
        Args:
            data: 数值数据列表
            return_scores: 是否返回异常分数
        
        Returns:
            异常点列表，每个异常点包含索引、值、严重程度等信息
        """
        if not data or len(data) < 3:
            logger.warning("数据点太少，无法进行异常检测")
            return []
        
        try:
            arr = np.array(data, dtype=float)
            
            # 移除NaN
            valid_mask = ~np.isnan(arr)
            valid_indices = np.where(valid_mask)[0]
            valid_arr = arr[valid_mask]
            
            if len(valid_arr) < 3:
                logger.warning("有效数据点太少")
                return []
            
            # 计算中心和离散度
            if self.use_mad:
                # 使用中位数和MAD（更鲁棒）
                center = np.median(valid_arr)
                mad = np.median(np.abs(valid_arr - center))
                scale = mad * 1.4826  # MAD到标准差的转换因子
            else:
                # 使用均值和标准差
                center = np.mean(valid_arr)
                scale = np.std(valid_arr)
            
            if scale == 0:
                logger.warning("数据无变化，无法检测异常")
                return []
            
            # 计算偏离程度（标准分数）
            z_scores = np.abs((valid_arr - center) / scale)
            
            # 找出异常点
            anomalies = []
            for i, (idx, value, z_score) in enumerate(zip(valid_indices, valid_arr, z_scores)):
                if z_score > self.threshold_sigma:
                    severity = self._calculate_severity(z_score)
                    anomaly = {
                        'index': int(idx),
                        'value': float(value),
                        'expected_value': float(center),
                        'deviation': float(value - center),
                        'z_score': float(z_score),
                        'severity': severity.value,
                        'severity_code': severity.name,
                    }
                    
                    if return_scores:
                        anomaly['anomaly_score'] = float(z_score / self.threshold_sigma)
                    
                    anomalies.append(anomaly)
            
            logger.info(f"统计方法检测到 {len(anomalies)} 个异常点（共{len(data)}个数据点）")
            return anomalies
            
        except Exception as e:
            logger.error(f"统计异常检测失败: {e}")
            return []
    
    def _calculate_severity(self, z_score: float) -> AnomalySeverity:
        """
        根据Z分数计算异常严重程度
        
        Args:
            z_score: 标准分数
        
        Returns:
            异常严重程度
        """
        abs_z = abs(z_score)
        
        if abs_z < 3:
            return AnomalySeverity.NORMAL
        elif abs_z < 4:
            return AnomalySeverity.SLIGHT
        elif abs_z < 5:
            return AnomalySeverity.MODERATE
        elif abs_z < 6:
            return AnomalySeverity.SEVERE
        else:
            return AnomalySeverity.CRITICAL
    
    def detect_with_context(
        self,
        data: List[float],
        window_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        使用滑动窗口进行上下文感知的异常检测
        
        Args:
            data: 数值数据列表
            window_size: 滑动窗口大小
        
        Returns:
            异常点列表
        """
        if len(data) < window_size:
            logger.warning("数据点少于窗口大小，使用全局检测")
            return self.detect(data)
        
        anomalies = []
        
        for i in range(len(data)):
            # 定义窗口范围
            start = max(0, i - window_size // 2)
            end = min(len(data), i + window_size // 2 + 1)
            window_data = data[start:end]
            
            # 在窗口内检测
            window_anomalies = self.detect(window_data)
            
            # 调整索引到全局
            for anomaly in window_anomalies:
                if anomaly['index'] == i - start:
                    anomaly['index'] = i
                    anomaly['detection_window'] = (start, end)
                    anomalies.append(anomaly)
                    break
        
        # 去重（同一点可能被多个窗口检测到）
        seen = set()
        unique_anomalies = []
        for anomaly in anomalies:
            idx = anomaly['index']
            if idx not in seen:
                seen.add(idx)
                unique_anomalies.append(anomaly)
        
        return unique_anomalies


class IsolationForestDetector:
    """基于孤立森林的异常检测器"""
    
    def __init__(
        self,
        contamination: float = 0.1,
        n_estimators: int = 100,
        random_state: int = 42
    ):
        """
        初始化孤立森林检测器
        
        Args:
            contamination: 预期异常比例
            n_estimators: 决策树数量
            random_state: 随机种子
        """
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self._model = None
    
    def detect(
        self,
        data: List[float],
        return_scores: bool = False
    ) -> List[Dict[str, Any]]:
        """
        使用孤立森林检测异常
        
        Args:
            data: 数值数据列表
            return_scores: 是否返回异常分数
        
        Returns:
            异常点列表
        """
        if not data or len(data) < 10:
            logger.warning("数据点太少（<10），无法使用孤立森林")
            return []
        
        try:
            from sklearn.ensemble import IsolationForest
            
            arr = np.array(data, dtype=float)
            
            # 移除NaN
            valid_mask = ~np.isnan(arr)
            valid_indices = np.where(valid_mask)[0]
            valid_arr = arr[valid_mask]
            
            if len(valid_arr) < 10:
                return []
            
            # 转换为二维数组（sklearn要求）
            X = valid_arr.reshape(-1, 1)
            
            # 训练模型
            self._model = IsolationForest(
                contamination=self.contamination,
                n_estimators=self.n_estimators,
                random_state=self.random_state,
                n_jobs=-1  # 使用所有CPU核心
            )
            
            predictions = self._model.fit_predict(X)
            scores = -self._model.score_samples(X)  # 负分数转为正（分数越高越异常）
            
            # 提取异常点（prediction == -1）
            anomalies = []
            for idx, pred, score in zip(valid_indices, predictions, scores):
                if pred == -1:
                    severity = self._calculate_severity(score, scores)
                    anomaly = {
                        'index': int(idx),
                        'value': float(data[idx]),
                        'severity': severity.value,
                        'severity_code': severity.name,
                    }
                    
                    if return_scores:
                        anomaly['anomaly_score'] = float(score)
                    
                    anomalies.append(anomaly)
            
            logger.info(f"孤立森林检测到 {len(anomalies)} 个异常点（共{len(data)}个数据点）")
            return anomalies
            
        except ImportError:
            logger.error("scikit-learn未安装，无法使用孤立森林")
            return []
        except Exception as e:
            logger.error(f"孤立森林异常检测失败: {e}")
            return []
    
    def _calculate_severity(
        self,
        score: float,
        all_scores: np.ndarray
    ) -> AnomalySeverity:
        """
        根据异常分数计算严重程度
        
        Args:
            score: 当前异常分数
            all_scores: 所有分数（用于归一化）
        
        Returns:
            异常严重程度
        """
        # 计算分数的百分位数
        percentile = (all_scores < score).sum() / len(all_scores) * 100
        
        if percentile < 90:
            return AnomalySeverity.NORMAL
        elif percentile < 95:
            return AnomalySeverity.SLIGHT
        elif percentile < 98:
            return AnomalySeverity.MODERATE
        elif percentile < 99:
            return AnomalySeverity.SEVERE
        else:
            return AnomalySeverity.CRITICAL


class AnomalyDetector:
    """异常检测服务主类"""
    
    def __init__(self, threshold: float = 3.0):
        self.statistical_detector = StatisticalAnomalyDetector(threshold_sigma=threshold)
        self.isolation_forest_detector = IsolationForestDetector()
    
    def detect(
        self,
        data: List[float],
        method: str = "statistical",  # Changed type hint to str to match usage
        **kwargs
    ) -> Dict[str, Any]:
        """
        检测异常
        
        Args:
            data: 数值数据列表
            method: 检测方法 (statistical, isolation_forest, combined)
            **kwargs: 传递给具体检测器的参数
        
        Returns:
            检测结果字典
        """
        if not data:
            return {"is_anomaly": False, "anomalies": []}
            
        anomalies = []
        
        # Convert string method to enum or handle string directly
        method_str = str(method).lower()
        
        if method_str == "statistical":
            anomalies = self.statistical_detector.detect(data, **kwargs)
        elif method_str == "isolation_forest":
            anomalies = self.isolation_forest_detector.detect(data, **kwargs)
        elif method_str == "combined":
            anomalies = self._combined_detect(data, **kwargs)
        else:
            logger.warning(f"未知的检测方法: {method}，使用统计方法")
            anomalies = self.statistical_detector.detect(data, **kwargs)
            
        # Add required fields for AnomalyPoint model if missing
        for anomaly in anomalies:
            if 'score' not in anomaly:
                anomaly['score'] = anomaly.get('anomaly_score', 0.0)
            if 'method' not in anomaly:
                anomaly['method'] = method_str
                
        return {
            "is_anomaly": len(anomalies) > 0,
            "anomalies": anomalies
        }
    
    def _combined_detect(
        self,
        data: List[float],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        组合多种方法进行异常检测
        
        Args:
            data: 数值数据列表
        
        Returns:
            异常点列表（投票机制：至少被一种方法检测为异常）
        """
        # 分别使用两种方法
        stat_anomalies = self.statistical_detector.detect(data, return_scores=True)
        if_anomalies = self.isolation_forest_detector.detect(data, return_scores=True)
        
        # 合并结果
        anomaly_map = {}
        
        # 添加统计方法的结果
        for anomaly in stat_anomalies:
            idx = anomaly['index']
            anomaly_map[idx] = {
                'index': idx,
                'value': anomaly['value'],
                'methods': ['statistical'],
                'stat_severity': anomaly['severity'],
                'stat_score': anomaly.get('anomaly_score', 0),
            }
        
        # 添加孤立森林的结果
        for anomaly in if_anomalies:
            idx = anomaly['index']
            if idx in anomaly_map:
                anomaly_map[idx]['methods'].append('isolation_forest')
                anomaly_map[idx]['if_severity'] = anomaly['severity']
                anomaly_map[idx]['if_score'] = anomaly.get('anomaly_score', 0)
            else:
                anomaly_map[idx] = {
                    'index': idx,
                    'value': anomaly['value'],
                    'methods': ['isolation_forest'],
                    'if_severity': anomaly['severity'],
                    'if_score': anomaly.get('anomaly_score', 0),
                }
        
        # 组合评分
        combined_anomalies = []
        for idx, info in anomaly_map.items():
            # 计算综合严重程度
            severity = self._combine_severity(info)
            
            combined_anomalies.append({
                'index': info['index'],
                'value': info['value'],
                'severity': severity.value,
                'severity_code': severity.name,
                'detected_by': info['methods'],
                'detection_count': len(info['methods']),
                'details': info
            })
        
        # 按索引排序
        combined_anomalies.sort(key=lambda x: x['index'])
        
        logger.info(f"组合方法检测到 {len(combined_anomalies)} 个异常点")
        return combined_anomalies
    
    def _combine_severity(self, info: Dict) -> AnomalySeverity:
        """
        组合多个方法的严重程度
        
        Args:
            info: 包含多个方法结果的信息
        
        Returns:
            综合严重程度
        """
        # 如果两种方法都检测到，取更严重的
        if len(info['methods']) == 2:
            stat_sev = info.get('stat_severity', AnomalySeverity.NORMAL.value)
            if_sev = info.get('if_severity', AnomalySeverity.NORMAL.value)
            
            severity_order = [
                AnomalySeverity.NORMAL.value,
                AnomalySeverity.SLIGHT.value,
                AnomalySeverity.MODERATE.value,
                AnomalySeverity.SEVERE.value,
                AnomalySeverity.CRITICAL.value,
            ]
            
            stat_idx = severity_order.index(stat_sev) if stat_sev in severity_order else 0
            if_idx = severity_order.index(if_sev) if if_sev in severity_order else 0
            
            combined_idx = max(stat_idx, if_idx)
            return AnomalySeverity(severity_order[combined_idx])
        
        # 只有一种方法检测到
        if 'stat_severity' in info:
            return AnomalySeverity(info['stat_severity'])
        elif 'if_severity' in info:
            return AnomalySeverity(info['if_severity'])
        
        return AnomalySeverity.NORMAL
    
    def batch_detect(
        self,
        data_dict: Dict[str, List[float]],
        method: DetectionMethod = DetectionMethod.STATISTICAL,
        **kwargs
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        批量检测多个时间序列的异常
        
        Args:
            data_dict: {指标名: 数据列表} 的字典
            method: 检测方法
            **kwargs: 传递给检测器的参数
        
        Returns:
            {指标名: 异常列表} 的字典
        """
        results = {}
        for metric_name, data in data_dict.items():
            try:
                anomalies = self.detect(data, method=method, **kwargs)
                results[metric_name] = anomalies
                logger.debug(f"指标 {metric_name} 检测到 {len(anomalies)} 个异常")
            except Exception as e:
                logger.error(f"检测指标 {metric_name} 的异常时出错: {e}")
                results[metric_name] = []
        
        return results


# 创建全局实例
anomaly_detector = AnomalyDetector()

