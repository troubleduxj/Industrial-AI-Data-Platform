#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
趋势预测服务
支持ARIMA、移动平均等时间序列预测方法
"""

from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from datetime import datetime, timedelta
import numpy as np
from loguru import logger


class PredictionMethod(str, Enum):
    """预测方法枚举"""
    ARIMA = "arima"  # ARIMA时间序列模型
    MOVING_AVERAGE = "moving_average"  # 简单移动平均
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"  # 指数平滑
    LINEAR_REGRESSION = "linear_regression"  # 线性回归


class ARIMAPredictor:
    """ARIMA时间序列预测器"""
    
    def __init__(
        self,
        order: Tuple[int, int, int] = (1, 1, 1),
        seasonal_order: Optional[Tuple[int, int, int, int]] = None
    ):
        """
        初始化ARIMA预测器
        
        Args:
            order: ARIMA模型参数 (p, d, q)
                p: 自回归项数
                d: 差分阶数
                q: 移动平均项数
            seasonal_order: 季节性ARIMA参数 (P, D, Q, s)
        """
        self.order = order
        self.seasonal_order = seasonal_order
        self._model = None
        self._fitted = False
    
    def fit(self, data: List[float]) -> bool:
        """
        训练ARIMA模型
        
        Args:
            data: 历史数据
        
        Returns:
            是否训练成功
        """
        if not data or len(data) < 10:
            logger.warning("数据点太少（<10），无法训练ARIMA模型")
            return False
        
        try:
            from statsmodels.tsa.arima.model import ARIMA
            
            arr = np.array(data, dtype=float)
            
            # 移除NaN
            valid_arr = arr[~np.isnan(arr)]
            
            if len(valid_arr) < 10:
                logger.warning("有效数据点太少")
                return False
            
            # 训练模型
            self._model = ARIMA(
                valid_arr,
                order=self.order,
                seasonal_order=self.seasonal_order
            )
            
            self._model = self._model.fit()
            self._fitted = True
            
            logger.info(f"ARIMA模型训练成功，参数: {self.order}")
            return True
            
        except ImportError:
            logger.error("statsmodels未安装，无法使用ARIMA")
            return False
        except Exception as e:
            logger.error(f"ARIMA模型训练失败: {e}")
            return False
    
    def predict(
        self,
        data: List[float],
        steps: int = 10,
        return_confidence: bool = False
    ) -> Dict[str, Any]:
        """
        使用ARIMA模型预测未来值
        
        Args:
            data: 历史数据
            steps: 预测步数
            return_confidence: 是否返回置信区间
        
        Returns:
            预测结果字典
        """
        if not data or steps <= 0:
            return {'predictions': [], 'success': False}
        
        # 如果模型未训练或数据变化，重新训练
        if not self._fitted or self._model is None:
            if not self.fit(data):
                return {'predictions': [], 'success': False}
        
        try:
            # 预测
            forecast_result = self._model.forecast(steps=steps)
            
            if isinstance(forecast_result, tuple):
                predictions = forecast_result[0]
            else:
                predictions = forecast_result
            
            result = {
                'predictions': predictions.tolist() if hasattr(predictions, 'tolist') else list(predictions),
                'success': True,
                'method': 'arima',
                'steps': steps
            }
            
            # 置信区间（如果可用）
            if return_confidence:
                try:
                    forecast_df = self._model.get_forecast(steps=steps)
                    conf_int = forecast_df.conf_int()
                    result['confidence_interval'] = {
                        'lower': conf_int.iloc[:, 0].tolist(),
                        'upper': conf_int.iloc[:, 1].tolist()
                    }
                except Exception as e:
                    logger.debug(f"无法获取置信区间: {e}")
            
            logger.info(f"ARIMA预测成功，预测了{steps}步")
            return result
            
        except Exception as e:
            logger.error(f"ARIMA预测失败: {e}")
            return {'predictions': [], 'success': False}


class MovingAveragePredictor:
    """移动平均预测器"""
    
    def __init__(self, window: int = 5):
        """
        初始化移动平均预测器
        
        Args:
            window: 窗口大小（使用最近N个点计算平均）
        """
        self.window = window
    
    def predict(
        self,
        data: List[float],
        steps: int = 10
    ) -> Dict[str, Any]:
        """
        使用简单移动平均预测
        
        Args:
            data: 历史数据
            steps: 预测步数
        
        Returns:
            预测结果字典
        """
        if not data or steps <= 0:
            return {'predictions': [], 'success': False}
        
        try:
            arr = np.array(data, dtype=float)
            valid_arr = arr[~np.isnan(arr)]
            
            if len(valid_arr) < self.window:
                logger.warning(f"数据点少于窗口大小({self.window})，使用所有数据计算平均")
                window = len(valid_arr)
            else:
                window = self.window
            
            predictions = []
            current_data = valid_arr.tolist()
            
            # 迭代预测每一步
            for _ in range(steps):
                # 使用最近window个点的平均值作为下一步预测
                next_value = np.mean(current_data[-window:])
                predictions.append(float(next_value))
                # 将预测值加入数据中，用于下一步预测
                current_data.append(next_value)
            
            logger.info(f"移动平均预测成功，窗口={window}，预测了{steps}步")
            
            return {
                'predictions': predictions,
                'success': True,
                'method': 'moving_average',
                'window': window,
                'steps': steps
            }
            
        except Exception as e:
            logger.error(f"移动平均预测失败: {e}")
            return {'predictions': [], 'success': False}


class ExponentialSmoothingPredictor:
    """指数平滑预测器"""
    
    def __init__(self, alpha: float = 0.3):
        """
        初始化指数平滑预测器
        
        Args:
            alpha: 平滑系数（0-1），越大对最新数据权重越大
        """
        self.alpha = max(0.0, min(1.0, alpha))  # 限制在0-1之间
    
    def predict(
        self,
        data: List[float],
        steps: int = 10
    ) -> Dict[str, Any]:
        """
        使用指数平滑预测
        
        Args:
            data: 历史数据
            steps: 预测步数
        
        Returns:
            预测结果字典
        """
        if not data or steps <= 0:
            return {'predictions': [], 'success': False}
        
        try:
            arr = np.array(data, dtype=float)
            valid_arr = arr[~np.isnan(arr)]
            
            if len(valid_arr) < 2:
                logger.warning("数据点太少")
                return {'predictions': [], 'success': False}
            
            # 计算指数平滑
            smoothed = [valid_arr[0]]  # 第一个值作为初始值
            
            for i in range(1, len(valid_arr)):
                smoothed_value = self.alpha * valid_arr[i] + (1 - self.alpha) * smoothed[-1]
                smoothed.append(smoothed_value)
            
            # 使用最后的平滑值作为预测（简单方法）
            last_smoothed = smoothed[-1]
            predictions = [float(last_smoothed)] * steps
            
            logger.info(f"指数平滑预测成功，alpha={self.alpha}，预测了{steps}步")
            
            return {
                'predictions': predictions,
                'success': True,
                'method': 'exponential_smoothing',
                'alpha': self.alpha,
                'steps': steps
            }
            
        except Exception as e:
            logger.error(f"指数平滑预测失败: {e}")
            return {'predictions': [], 'success': False}


class LinearRegressionPredictor:
    """线性回归预测器"""
    
    def predict(
        self,
        data: List[float],
        steps: int = 10
    ) -> Dict[str, Any]:
        """
        使用线性回归预测趋势
        
        Args:
            data: 历史数据
            steps: 预测步数
        
        Returns:
            预测结果字典
        """
        if not data or steps <= 0:
            return {'predictions': [], 'success': False}
        
        try:
            arr = np.array(data, dtype=float)
            valid_arr = arr[~np.isnan(arr)]
            
            if len(valid_arr) < 2:
                logger.warning("数据点太少")
                return {'predictions': [], 'success': False}
            
            # 线性回归拟合
            x = np.arange(len(valid_arr))
            coefficients = np.polyfit(x, valid_arr, 1)
            slope, intercept = coefficients
            
            # 预测未来值
            future_x = np.arange(len(valid_arr), len(valid_arr) + steps)
            predictions = slope * future_x + intercept
            
            logger.info(f"线性回归预测成功，斜率={slope:.4f}，预测了{steps}步")
            
            return {
                'predictions': predictions.tolist(),
                'success': True,
                'method': 'linear_regression',
                'slope': float(slope),
                'intercept': float(intercept),
                'steps': steps
            }
            
        except Exception as e:
            logger.error(f"线性回归预测失败: {e}")
            return {'predictions': [], 'success': False}


class PredictionEvaluator:
    """预测准确度评估器"""
    
    @staticmethod
    def calculate_mae(actual: List[float], predicted: List[float]) -> float:
        """
        计算平均绝对误差 (Mean Absolute Error)
        
        Args:
            actual: 实际值
            predicted: 预测值
        
        Returns:
            MAE值
        """
        if not actual or not predicted or len(actual) != len(predicted):
            return float('inf')
        
        try:
            actual_arr = np.array(actual, dtype=float)
            predicted_arr = np.array(predicted, dtype=float)
            
            mae = np.mean(np.abs(actual_arr - predicted_arr))
            return float(mae)
        except Exception as e:
            logger.error(f"计算MAE失败: {e}")
            return float('inf')
    
    @staticmethod
    def calculate_rmse(actual: List[float], predicted: List[float]) -> float:
        """
        计算均方根误差 (Root Mean Squared Error)
        
        Args:
            actual: 实际值
            predicted: 预测值
        
        Returns:
            RMSE值
        """
        if not actual or not predicted or len(actual) != len(predicted):
            return float('inf')
        
        try:
            actual_arr = np.array(actual, dtype=float)
            predicted_arr = np.array(predicted, dtype=float)
            
            rmse = np.sqrt(np.mean((actual_arr - predicted_arr) ** 2))
            return float(rmse)
        except Exception as e:
            logger.error(f"计算RMSE失败: {e}")
            return float('inf')
    
    @staticmethod
    def calculate_mape(actual: List[float], predicted: List[float]) -> float:
        """
        计算平均绝对百分比误差 (Mean Absolute Percentage Error)
        
        Args:
            actual: 实际值
            predicted: 预测值
        
        Returns:
            MAPE值（百分比）
        """
        if not actual or not predicted or len(actual) != len(predicted):
            return float('inf')
        
        try:
            actual_arr = np.array(actual, dtype=float)
            predicted_arr = np.array(predicted, dtype=float)
            
            # 避免除零，过滤掉实际值为0的点
            mask = actual_arr != 0
            if not mask.any():
                return float('inf')
            
            mape = np.mean(np.abs((actual_arr[mask] - predicted_arr[mask]) / actual_arr[mask])) * 100
            return float(mape)
        except Exception as e:
            logger.error(f"计算MAPE失败: {e}")
            return float('inf')
    
    @staticmethod
    def evaluate(
        actual: List[float],
        predicted: List[float]
    ) -> Dict[str, float]:
        """
        综合评估预测准确度
        
        Args:
            actual: 实际值
            predicted: 预测值
        
        Returns:
            包含MAE、RMSE、MAPE的字典
        """
        return {
            'mae': PredictionEvaluator.calculate_mae(actual, predicted),
            'rmse': PredictionEvaluator.calculate_rmse(actual, predicted),
            'mape': PredictionEvaluator.calculate_mape(actual, predicted)
        }


class TrendPredictor:
    """趋势预测服务主类"""
    
    def __init__(self):
        self.arima_predictor = ARIMAPredictor()
        self.ma_predictor = MovingAveragePredictor()
        self.es_predictor = ExponentialSmoothingPredictor()
        self.lr_predictor = LinearRegressionPredictor()
        self.evaluator = PredictionEvaluator()
    
    def predict(
        self,
        data: List[float],
        steps: int = 10,
        method: PredictionMethod = PredictionMethod.MOVING_AVERAGE,
        **kwargs
    ) -> Dict[str, Any]:
        """
        预测未来趋势
        
        Args:
            data: 历史数据
            steps: 预测步数
            method: 预测方法
            **kwargs: 传递给具体预测器的参数
        
        Returns:
            预测结果字典
        """
        if not data or steps <= 0:
            return {'predictions': [], 'success': False}
        
        if method == PredictionMethod.ARIMA:
            return self.arima_predictor.predict(data, steps, **kwargs)
        elif method == PredictionMethod.MOVING_AVERAGE:
            return self.ma_predictor.predict(data, steps)
        elif method == PredictionMethod.EXPONENTIAL_SMOOTHING:
            return self.es_predictor.predict(data, steps)
        elif method == PredictionMethod.LINEAR_REGRESSION:
            return self.lr_predictor.predict(data, steps)
        else:
            logger.warning(f"未知的预测方法: {method}，使用移动平均")
            return self.ma_predictor.predict(data, steps)
    
    def evaluate_prediction(
        self,
        actual: List[float],
        predicted: List[float]
    ) -> Dict[str, float]:
        """
        评估预测准确度
        
        Args:
            actual: 实际值
            predicted: 预测值
        
        Returns:
            评估指标
        """
        return self.evaluator.evaluate(actual, predicted)
    
    def batch_predict(
        self,
        data_dict: Dict[str, List[float]],
        steps: int = 10,
        method: PredictionMethod = PredictionMethod.MOVING_AVERAGE,
        **kwargs
    ) -> Dict[str, Dict[str, Any]]:
        """
        批量预测多个时间序列
        
        Args:
            data_dict: {指标名: 历史数据} 的字典
            steps: 预测步数
            method: 预测方法
            **kwargs: 传递给预测器的参数
        
        Returns:
            {指标名: 预测结果} 的字典
        """
        results = {}
        for metric_name, data in data_dict.items():
            try:
                prediction = self.predict(data, steps, method, **kwargs)
                results[metric_name] = prediction
                logger.debug(f"指标 {metric_name} 预测完成")
            except Exception as e:
                logger.error(f"预测指标 {metric_name} 失败: {e}")
                results[metric_name] = {'predictions': [], 'success': False}
        
        return results


# 创建全局实例
trend_predictor = TrendPredictor()

