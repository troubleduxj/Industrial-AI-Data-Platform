#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
特征提取服务
从设备数据中提取统计、时序和频域特征
"""

from typing import List, Dict, Optional, Any
import numpy as np
from loguru import logger


class StatisticalFeatureExtractor:
    """统计特征提取器"""
    
    @staticmethod
    def extract(data: List[float], prefix: str = "") -> Dict[str, float]:
        """
        提取统计特征
        
        Args:
            data: 数值数据列表
            prefix: 特征名称前缀
        
        Returns:
            统计特征字典
        """
        if not data or len(data) == 0:
            logger.warning("数据为空，无法提取特征")
            return {}
        
        try:
            arr = np.array(data, dtype=float)
            
            # 移除NaN值
            arr = arr[~np.isnan(arr)]
            
            if len(arr) == 0:
                logger.warning("移除NaN后数据为空")
                return {}
            
            features = {
                f'{prefix}mean': float(np.mean(arr)),
                f'{prefix}std': float(np.std(arr)),
                f'{prefix}var': float(np.var(arr)),
                f'{prefix}max': float(np.max(arr)),
                f'{prefix}min': float(np.min(arr)),
                f'{prefix}range': float(np.ptp(arr)),  # peak to peak
                f'{prefix}median': float(np.median(arr)),
                f'{prefix}q25': float(np.percentile(arr, 25)),
                f'{prefix}q75': float(np.percentile(arr, 75)),
                f'{prefix}iqr': float(np.percentile(arr, 75) - np.percentile(arr, 25)),
            }
            
            # 计算偏度和峰度（需要scipy）
            try:
                from scipy import stats
                features[f'{prefix}skewness'] = float(stats.skew(arr))
                features[f'{prefix}kurtosis'] = float(stats.kurtosis(arr))
            except ImportError:
                logger.debug("scipy未安装，跳过偏度和峰度计算")
            except Exception as e:
                logger.warning(f"计算偏度和峰度时出错: {e}")
            
            return features
            
        except Exception as e:
            logger.error(f"提取统计特征时出错: {e}")
            return {}


class TimeSeriesFeatureExtractor:
    """时间序列特征提取器"""
    
    @staticmethod
    def extract_trend(data: List[float]) -> str:
        """
        提取趋势方向
        
        Args:
            data: 时间序列数据
        
        Returns:
            趋势描述: "上升"、"下降"、"平稳"
        """
        if not data or len(data) < 2:
            return "未知"
        
        try:
            arr = np.array(data, dtype=float)
            arr = arr[~np.isnan(arr)]
            
            if len(arr) < 2:
                return "未知"
            
            # 线性回归计算斜率
            x = np.arange(len(arr))
            coefficients = np.polyfit(x, arr, 1)
            slope = coefficients[0]
            
            # 归一化斜率（相对于数据范围）
            data_range = np.ptp(arr)
            if data_range > 0:
                normalized_slope = slope / data_range * len(arr)
            else:
                return "平稳"
            
            # 根据斜率判断趋势
            if normalized_slope > 0.1:
                return "上升"
            elif normalized_slope < -0.1:
                return "下降"
            else:
                return "平稳"
                
        except Exception as e:
            logger.error(f"提取趋势时出错: {e}")
            return "未知"
    
    @staticmethod
    def extract_change_rate(data: List[float]) -> Dict[str, float]:
        """
        提取变化率特征
        
        Args:
            data: 时间序列数据
        
        Returns:
            变化率特征
        """
        if not data or len(data) < 2:
            return {}
        
        try:
            arr = np.array(data, dtype=float)
            arr = arr[~np.isnan(arr)]
            
            if len(arr) < 2:
                return {}
            
            # 计算相邻数据点的变化率
            changes = np.diff(arr)
            change_rates = changes / (arr[:-1] + 1e-10)  # 避免除零
            
            return {
                'avg_change': float(np.mean(changes)),
                'max_change': float(np.max(changes)),
                'min_change': float(np.min(changes)),
                'avg_change_rate': float(np.mean(change_rates)),
                'max_change_rate': float(np.max(change_rates)),
                'volatility': float(np.std(changes)),
            }
            
        except Exception as e:
            logger.error(f"提取变化率时出错: {e}")
            return {}
    
    @staticmethod
    def extract_autocorrelation(data: List[float], max_lag: int = 5) -> Dict[str, float]:
        """
        提取自相关系数
        
        Args:
            data: 时间序列数据
            max_lag: 最大滞后阶数
        
        Returns:
            自相关系数
        """
        if not data or len(data) < max_lag + 1:
            return {}
        
        try:
            arr = np.array(data, dtype=float)
            arr = arr[~np.isnan(arr)]
            
            if len(arr) < max_lag + 1:
                return {}
            
            # 计算自相关
            mean = np.mean(arr)
            var = np.var(arr)
            
            if var == 0:
                return {f'acf_lag_{lag}': 0.0 for lag in range(1, max_lag + 1)}
            
            autocorr = {}
            for lag in range(1, max_lag + 1):
                if len(arr) > lag:
                    covariance = np.mean((arr[:-lag] - mean) * (arr[lag:] - mean))
                    autocorr[f'acf_lag_{lag}'] = float(covariance / var)
            
            return autocorr
            
        except Exception as e:
            logger.error(f"提取自相关时出错: {e}")
            return {}
    
    @staticmethod
    def extract(data: List[float], prefix: str = "") -> Dict[str, Any]:
        """
        提取所有时间序列特征
        
        Args:
            data: 时间序列数据
            prefix: 特征名称前缀
        
        Returns:
            时间序列特征字典
        """
        features = {}
        
        # 趋势
        features[f'{prefix}trend'] = TimeSeriesFeatureExtractor.extract_trend(data)
        
        # 变化率
        change_features = TimeSeriesFeatureExtractor.extract_change_rate(data)
        for key, value in change_features.items():
            features[f'{prefix}{key}'] = value
        
        # 自相关（前3个滞后）
        autocorr_features = TimeSeriesFeatureExtractor.extract_autocorrelation(data, max_lag=3)
        for key, value in autocorr_features.items():
            features[f'{prefix}{key}'] = value
        
        return features


class FrequencyFeatureExtractor:
    """频域特征提取器"""
    
    @staticmethod
    def extract(data: List[float], sampling_rate: float = 1.0, prefix: str = "") -> Dict[str, float]:
        """
        提取频域特征
        
        Args:
            data: 时间序列数据
            sampling_rate: 采样率（Hz）
            prefix: 特征名称前缀
        
        Returns:
            频域特征字典
        """
        if not data or len(data) < 4:
            logger.warning("数据点太少，无法进行FFT分析")
            return {}
        
        try:
            arr = np.array(data, dtype=float)
            arr = arr[~np.isnan(arr)]
            
            if len(arr) < 4:
                return {}
            
            # 去均值
            arr = arr - np.mean(arr)
            
            # FFT变换
            fft_result = np.fft.fft(arr)
            frequencies = np.fft.fftfreq(len(arr), d=1/sampling_rate)
            
            # 只取正频率部分
            positive_freq_idx = frequencies > 0
            frequencies = frequencies[positive_freq_idx]
            fft_magnitudes = np.abs(fft_result[positive_freq_idx])
            
            if len(fft_magnitudes) == 0:
                return {}
            
            # 计算特征
            features = {}
            
            # 主频率（最大幅值对应的频率）
            dominant_freq_idx = np.argmax(fft_magnitudes)
            features[f'{prefix}dominant_frequency'] = float(frequencies[dominant_freq_idx])
            features[f'{prefix}dominant_magnitude'] = float(fft_magnitudes[dominant_freq_idx])
            
            # 总能量
            total_energy = float(np.sum(fft_magnitudes ** 2))
            features[f'{prefix}total_energy'] = total_energy
            
            # 频谱熵（频率分布的均匀程度）
            if total_energy > 0:
                power = (fft_magnitudes ** 2) / total_energy
                # 避免log(0)
                power = power[power > 0]
                spectral_entropy = -float(np.sum(power * np.log2(power)))
                features[f'{prefix}spectral_entropy'] = spectral_entropy
            
            # 频率带能量分布（低、中、高频）
            n_freq = len(frequencies)
            low_freq_energy = float(np.sum(fft_magnitudes[:n_freq//3] ** 2))
            mid_freq_energy = float(np.sum(fft_magnitudes[n_freq//3:2*n_freq//3] ** 2))
            high_freq_energy = float(np.sum(fft_magnitudes[2*n_freq//3:] ** 2))
            
            features[f'{prefix}low_freq_energy'] = low_freq_energy
            features[f'{prefix}mid_freq_energy'] = mid_freq_energy
            features[f'{prefix}high_freq_energy'] = high_freq_energy
            
            # 能量比例
            if total_energy > 0:
                features[f'{prefix}low_freq_ratio'] = low_freq_energy / total_energy
                features[f'{prefix}mid_freq_ratio'] = mid_freq_energy / total_energy
                features[f'{prefix}high_freq_ratio'] = high_freq_energy / total_energy
            
            return features
            
        except Exception as e:
            logger.error(f"提取频域特征时出错: {e}")
            return {}


class FeatureExtractor:
    """特征提取服务主类"""
    
    def __init__(self):
        self.statistical_extractor = StatisticalFeatureExtractor()
        self.timeseries_extractor = TimeSeriesFeatureExtractor()
        self.frequency_extractor = FrequencyFeatureExtractor()
    
    def extract_all_features(
        self,
        data: List[float],
        include_statistical: bool = True,
        include_timeseries: bool = True,
        include_frequency: bool = False,
        sampling_rate: float = 1.0,
    ) -> Dict[str, Any]:
        """
        提取所有特征
        
        Args:
            data: 数值数据列表
            include_statistical: 是否包含统计特征
            include_timeseries: 是否包含时间序列特征
            include_frequency: 是否包含频域特征
            sampling_rate: 采样率（用于频域分析）
        
        Returns:
            特征字典
        """
        if not data or len(data) == 0:
            logger.warning("数据为空，无法提取特征")
            return {}
        
        features = {}
        
        # 统计特征
        if include_statistical:
            stat_features = self.statistical_extractor.extract(data, prefix='stat_')
            features.update(stat_features)
            logger.debug(f"提取统计特征: {len(stat_features)}个")
        
        # 时间序列特征
        if include_timeseries:
            ts_features = self.timeseries_extractor.extract(data, prefix='ts_')
            features.update(ts_features)
            logger.debug(f"提取时序特征: {len(ts_features)}个")
        
        # 频域特征
        if include_frequency:
            freq_features = self.frequency_extractor.extract(data, sampling_rate, prefix='freq_')
            features.update(freq_features)
            logger.debug(f"提取频域特征: {len(freq_features)}个")
        
        logger.info(f"共提取 {len(features)} 个特征")
        return features
    
    def extract_features_batch(
        self,
        data_dict: Dict[str, List[float]],
        **kwargs
    ) -> Dict[str, Dict[str, Any]]:
        """
        批量提取特征
        
        Args:
            data_dict: {指标名: 数据列表} 的字典
            **kwargs: 传递给extract_all_features的参数
        
        Returns:
            {指标名: 特征字典} 的字典
        """
        results = {}
        for metric_name, data in data_dict.items():
            try:
                features = self.extract_all_features(data, **kwargs)
                results[metric_name] = features
                logger.debug(f"指标 {metric_name} 提取了 {len(features)} 个特征")
            except Exception as e:
                logger.error(f"提取指标 {metric_name} 的特征时出错: {e}")
                results[metric_name] = {}
        
        return results


# 创建全局实例
feature_extractor = FeatureExtractor()

