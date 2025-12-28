#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一推理服务
实现AI模型推理和预测结果持久化

需求：2.3, 2.4
- 激活模型版本后加载到推理服务
- 执行推理并持久化结果
- 从存储后端加载模型文件
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger


class InferenceError(Exception):
    """推理服务异常"""
    pass


class ModelLoadError(InferenceError):
    """模型加载异常"""
    pass


class BasePredictor(ABC):
    """
    预测器基类 - 统一推理接口
    
    所有具体预测器必须继承此类并实现抽象方法
    """
    
    def __init__(self, model_id: int, version_id: int):
        self.model_id = model_id
        self.version_id = version_id
        self.model = None
        self.is_loaded = False
        self.model_info: Dict[str, Any] = {}
    
    @abstractmethod
    async def load_model(self, file_path: str) -> bool:
        """
        加载模型到内存
        
        Args:
            file_path: 模型文件路径
        
        Returns:
            bool: 加载是否成功
        """
        pass
    
    @abstractmethod
    async def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单次预测
        
        Args:
            input_data: 输入数据
        
        Returns:
            预测结果字典
        """
        pass
    
    async def batch_predict(self, input_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量预测
        
        Args:
            input_batch: 输入数据列表
        
        Returns:
            预测结果列表
        """
        results = []
        for input_data in input_batch:
            try:
                result = await self.predict(input_data)
                results.append(result)
            except Exception as e:
                results.append({
                    "success": False,
                    "error": str(e)
                })
        return results
    
    def unload_model(self):
        """卸载模型释放内存"""
        self.model = None
        self.is_loaded = False
        logger.info(f"模型已卸载: model_id={self.model_id}")


class IsolationForestPredictor(BasePredictor):
    """
    孤立森林异常检测预测器
    
    用于检测设备数据中的异常模式
    """
    
    async def load_model(self, file_path: str) -> bool:
        """加载孤立森林模型"""
        try:
            import joblib
            
            if not os.path.exists(file_path):
                logger.error(f"模型文件不存在: {file_path}")
                return False
            
            self.model = joblib.load(file_path)
            self.is_loaded = True
            
            logger.info(f"✅ 孤立森林模型加载成功: {file_path}")
            return True
            
        except ImportError:
            logger.error("joblib未安装，无法加载模型")
            return False
        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            return False
    
    async def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行异常检测预测"""
        if not self.is_loaded or self.model is None:
            raise InferenceError("模型未加载")
        
        try:
            # 1. 提取特征
            features = self._extract_features(input_data)
            
            if not features:
                raise InferenceError("无法从输入数据提取特征")
            
            # 2. 执行预测
            import numpy as np
            features_array = np.array([features])
            
            anomaly_score = float(self.model.decision_function(features_array)[0])
            prediction = int(self.model.predict(features_array)[0])
            is_anomaly = prediction == -1
            
            # 3. 计算置信度 (基于异常分数的绝对值)
            confidence = min(abs(anomaly_score), 1.0)
            
            return {
                "success": True,
                "predicted_value": anomaly_score,
                "is_anomaly": is_anomaly,
                "anomaly_score": anomaly_score,
                "confidence": confidence,
                "prediction_time": datetime.now().isoformat(),
                "algorithm": "isolation_forest"
            }
            
        except Exception as e:
            logger.error(f"❌ 预测失败: {e}")
            raise InferenceError(f"预测失败: {str(e)}")
    
    def _extract_features(self, input_data: Dict[str, Any]) -> List[float]:
        """从输入数据提取特征向量"""
        features = []
        
        # 提取所有数值字段作为特征
        for key, value in input_data.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                features.append(float(value))
        
        return features


class ARIMAPredictor(BasePredictor):
    """
    ARIMA时间序列预测器
    
    用于预测设备指标的未来趋势
    """
    
    async def load_model(self, file_path: str) -> bool:
        """加载ARIMA模型"""
        try:
            import joblib
            
            if not os.path.exists(file_path):
                logger.error(f"模型文件不存在: {file_path}")
                return False
            
            self.model = joblib.load(file_path)
            self.is_loaded = True
            
            logger.info(f"✅ ARIMA模型加载成功: {file_path}")
            return True
            
        except ImportError:
            logger.error("joblib未安装，无法加载模型")
            return False
        except Exception as e:
            logger.error(f"❌ ARIMA模型加载失败: {e}")
            return False
    
    async def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行时间序列预测"""
        if not self.is_loaded or self.model is None:
            raise InferenceError("模型未加载")
        
        try:
            # 获取预测步数
            forecast_steps = input_data.get("forecast_steps", 24)
            
            # 执行预测
            forecast = self.model.forecast(steps=forecast_steps)
            
            # 获取置信区间
            confidence_intervals = None
            try:
                forecast_result = self.model.get_forecast(steps=forecast_steps)
                conf_int = forecast_result.conf_int()
                confidence_intervals = {
                    "lower": conf_int.iloc[:, 0].tolist(),
                    "upper": conf_int.iloc[:, 1].tolist()
                }
            except Exception:
                pass
            
            # 取第一个预测值作为主要预测值
            predicted_value = float(forecast[0]) if len(forecast) > 0 else 0.0
            
            result = {
                "success": True,
                "predicted_value": predicted_value,
                "forecast_values": forecast.tolist() if hasattr(forecast, 'tolist') else list(forecast),
                "forecast_steps": forecast_steps,
                "confidence": 0.95,  # ARIMA默认置信度
                "prediction_time": datetime.now().isoformat(),
                "algorithm": "arima"
            }
            
            if confidence_intervals:
                result["confidence_intervals"] = confidence_intervals
            
            return result
            
        except Exception as e:
            logger.error(f"❌ ARIMA预测失败: {e}")
            raise InferenceError(f"ARIMA预测失败: {str(e)}")


class XGBoostPredictor(BasePredictor):
    """
    XGBoost预测器
    
    用于回归和分类预测任务
    """
    
    async def load_model(self, file_path: str) -> bool:
        """加载XGBoost模型"""
        try:
            import joblib
            
            if not os.path.exists(file_path):
                logger.error(f"模型文件不存在: {file_path}")
                return False
            
            self.model = joblib.load(file_path)
            self.is_loaded = True
            
            logger.info(f"✅ XGBoost模型加载成功: {file_path}")
            return True
            
        except ImportError:
            logger.error("joblib未安装，无法加载模型")
            return False
        except Exception as e:
            logger.error(f"❌ XGBoost模型加载失败: {e}")
            return False
    
    async def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行XGBoost预测"""
        if not self.is_loaded or self.model is None:
            raise InferenceError("模型未加载")
        
        try:
            import numpy as np
            
            # 提取特征
            features = self._extract_features(input_data)
            
            if not features:
                raise InferenceError("无法从输入数据提取特征")
            
            features_array = np.array([features])
            
            # 执行预测
            prediction = self.model.predict(features_array)
            predicted_value = float(prediction[0])
            
            # 尝试获取预测概率（分类任务）
            confidence = 0.0
            try:
                if hasattr(self.model, 'predict_proba'):
                    proba = self.model.predict_proba(features_array)
                    confidence = float(np.max(proba))
            except Exception:
                confidence = 0.8  # 默认置信度
            
            return {
                "success": True,
                "predicted_value": predicted_value,
                "confidence": confidence,
                "prediction_time": datetime.now().isoformat(),
                "algorithm": "xgboost"
            }
            
        except Exception as e:
            logger.error(f"❌ XGBoost预测失败: {e}")
            raise InferenceError(f"XGBoost预测失败: {str(e)}")
    
    def _extract_features(self, input_data: Dict[str, Any]) -> List[float]:
        """从输入数据提取特征向量"""
        features = []
        
        for key, value in input_data.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                features.append(float(value))
        
        return features


class InferenceService:
    """
    统一推理服务
    
    核心功能：
    - 管理预测器实例
    - 执行预测并持久化结果
    - 支持批量预测
    """
    
    # 算法类型到预测器类的映射
    PREDICTOR_CLASSES = {
        "isolation_forest": IsolationForestPredictor,
        "arima": ARIMAPredictor,
        "xgboost": XGBoostPredictor
    }
    
    def __init__(self):
        self._predictors: Dict[int, BasePredictor] = {}
    
    async def predict(
        self, 
        model_id: int, 
        asset_id: int, 
        input_data: Dict[str, Any],
        persist: bool = True
    ) -> Dict[str, Any]:
        """
        执行预测并持久化结果
        
        Args:
            model_id: 模型ID
            asset_id: 资产ID
            input_data: 输入数据
            persist: 是否持久化结果
        
        Returns:
            预测结果字典
        """
        try:
            # 1. 获取预测器
            predictor = await self._get_predictor(model_id)
            if not predictor:
                return {
                    "success": False,
                    "error": f"无法获取模型 {model_id} 的预测器"
                }
            
            # 2. 执行预测
            prediction_result = await predictor.predict(input_data)
            
            # 3. 持久化预测结果
            if persist and prediction_result.get("success"):
                await self._save_prediction(
                    model_id=model_id,
                    version_id=predictor.version_id,
                    asset_id=asset_id,
                    input_data=input_data,
                    result=prediction_result
                )
            
            # 4. 返回结果
            return {
                "success": True,
                "model_id": model_id,
                "asset_id": asset_id,
                "prediction": prediction_result
            }
            
        except InferenceError as e:
            logger.error(f"❌ 推理错误: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"❌ 预测失败: {e}")
            return {
                "success": False,
                "error": f"预测失败: {str(e)}"
            }
    
    async def batch_predict(
        self,
        model_id: int,
        predictions: List[Dict[str, Any]],
        persist: bool = True
    ) -> List[Dict[str, Any]]:
        """
        批量预测
        
        Args:
            model_id: 模型ID
            predictions: 预测请求列表，每个包含 asset_id 和 input_data
            persist: 是否持久化结果
        
        Returns:
            预测结果列表
        """
        results = []
        
        for pred_request in predictions:
            asset_id = pred_request.get("asset_id")
            input_data = pred_request.get("input_data", {})
            
            if not asset_id:
                results.append({
                    "success": False,
                    "error": "缺少 asset_id"
                })
                continue
            
            result = await self.predict(
                model_id=model_id,
                asset_id=asset_id,
                input_data=input_data,
                persist=persist
            )
            results.append(result)
        
        return results
    
    async def get_prediction_history(
        self,
        asset_id: int,
        model_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取预测历史
        
        Args:
            asset_id: 资产ID
            model_id: 模型ID (可选)
            start_time: 开始时间 (可选)
            end_time: 结束时间 (可选)
            limit: 返回数量限制
        
        Returns:
            预测历史列表
        """
        from app.models.platform_upgrade import AIPrediction
        
        query = AIPrediction.filter(asset_id=asset_id)
        
        if model_id:
            query = query.filter(model_version__model_id=model_id)
        
        if start_time:
            query = query.filter(prediction_time__gte=start_time)
        
        if end_time:
            query = query.filter(prediction_time__lte=end_time)
        
        predictions = await query.order_by("-prediction_time").limit(limit).prefetch_related("model_version")
        
        return [
            {
                "id": p.id,
                "model_version_id": p.model_version_id,
                "version": p.model_version.version if p.model_version else None,
                "input_data": p.input_data,
                "predicted_value": p.predicted_value,
                "confidence": p.confidence,
                "is_anomaly": p.is_anomaly,
                "anomaly_score": p.anomaly_score,
                "prediction_time": p.prediction_time.isoformat() if p.prediction_time else None,
                "target_time": p.target_time.isoformat() if p.target_time else None,
                "actual_value": p.actual_value
            }
            for p in predictions
        ]
    
    async def _get_predictor(self, model_id: int) -> Optional[BasePredictor]:
        """获取或创建预测器实例"""
        
        # 检查缓存
        if model_id in self._predictors:
            predictor = self._predictors[model_id]
            if predictor.is_loaded:
                return predictor
        
        # 创建新的预测器
        from app.models.platform_upgrade import AIModel, AIModelVersion
        
        try:
            # 获取模型信息
            model = await AIModel.get_or_none(id=model_id)
            if not model:
                logger.error(f"模型不存在: {model_id}")
                return None
            
            if not model.is_active:
                logger.error(f"模型未激活: {model_id}")
                return None
            
            # 获取生产版本
            version = await AIModelVersion.get_or_none(
                model_id=model_id,
                status="prod"
            )
            if not version:
                logger.error(f"模型没有生产版本: {model_id}")
                return None
            
            # 创建预测器
            predictor_class = self.PREDICTOR_CLASSES.get(model.algorithm)
            if not predictor_class:
                logger.error(f"不支持的算法类型: {model.algorithm}")
                return None
            
            predictor = predictor_class(model_id, version.id)
            
            # 加载模型 - 优先从存储后端加载
            file_path = await self._resolve_model_path(version)
            if not file_path:
                logger.error(f"无法解析模型文件路径: {model_id}")
                return None
            
            success = await predictor.load_model(file_path)
            if not success:
                logger.error(f"模型加载失败: {model_id}")
                return None
            
            # 缓存预测器
            self._predictors[model_id] = predictor
            
            return predictor
            
        except Exception as e:
            logger.error(f"❌ 获取预测器失败: {e}")
            return None
    
    async def _resolve_model_path(self, version) -> Optional[str]:
        """
        解析模型文件路径
        
        需求: 2.4 - 激活模型版本时，推理服务应从存储后端加载实际模型文件
        
        优先从存储后端加载，如果存储后端有文件则下载到临时目录。
        如果存储后端没有文件，则使用本地文件路径。
        
        Args:
            version: 模型版本对象
        
        Returns:
            Optional[str]: 模型文件的本地路径
        """
        try:
            # 检查是否有存储后端路径
            storage_path = getattr(version, 'storage_path', None)
            
            if storage_path:
                # 从存储后端加载
                try:
                    from ai_engine.model_storage.model_storage_service import get_model_storage_service
                    
                    storage_service = get_model_storage_service()
                    
                    # 检查文件是否存在于存储后端
                    if await storage_service.model_exists(storage_path):
                        # 下载到临时目录
                        local_path = await storage_service.load_model_to_temp(storage_path)
                        logger.info(f"✅ 从存储后端加载模型: {storage_path} -> {local_path}")
                        return local_path
                    else:
                        logger.warning(f"存储后端文件不存在: {storage_path}")
                except ImportError:
                    logger.warning("模型存储模块未安装，使用本地文件路径")
                except Exception as e:
                    logger.warning(f"从存储后端加载失败: {e}，尝试使用本地路径")
            
            # 使用本地文件路径
            file_path = version.file_path
            if file_path and os.path.exists(file_path):
                logger.info(f"✅ 使用本地模型文件: {file_path}")
                return file_path
            
            logger.error(f"模型文件不存在: {file_path}")
            return None
            
        except Exception as e:
            logger.error(f"解析模型路径失败: {e}")
            return None
    
    async def _save_prediction(
        self,
        model_id: int,
        version_id: int,
        asset_id: int,
        input_data: Dict[str, Any],
        result: Dict[str, Any]
    ):
        """
        保存预测结果到数据库
        
        需求 4.1: AI模型产生预测结果时，平台应同时写入PostgreSQL和TDengine
        
        使用PredictionStore实现双写，确保预测结果同时存储到PostgreSQL和TDengine。
        """
        try:
            # 获取资产和模型信息用于双写
            from app.models.platform_upgrade import Asset, AIModelVersion
            
            # 获取资产信息
            asset = await Asset.get_or_none(id=asset_id).prefetch_related("category")
            if not asset:
                logger.warning(f"资产不存在: {asset_id}，仅保存到PostgreSQL")
                await self._save_prediction_postgresql_only(
                    version_id, asset_id, input_data, result
                )
                return
            
            # 获取模型版本信息
            version = await AIModelVersion.get_or_none(id=version_id)
            if not version:
                logger.warning(f"模型版本不存在: {version_id}，仅保存到PostgreSQL")
                await self._save_prediction_postgresql_only(
                    version_id, asset_id, input_data, result
                )
                return
            
            # 使用PredictionStore进行双写
            try:
                from ai_engine.inference.prediction_store import get_prediction_store
                
                prediction_store = get_prediction_store()
                
                pg_success, td_success = await prediction_store.save_prediction(
                    model_id=model_id,
                    model_version=version.version,
                    asset_id=asset_id,
                    asset_code=asset.code,
                    category_code=asset.category.code if asset.category else "default",
                    prediction_result={
                        "predicted_value": result.get("predicted_value", 0.0),
                        "confidence": result.get("confidence", 0.0),
                        "is_anomaly": result.get("is_anomaly"),
                        "anomaly_score": result.get("anomaly_score"),
                        "prediction_details": result,
                        "input_data": input_data,
                    }
                )
                
                if pg_success:
                    logger.debug(f"✅ 预测结果已保存到PostgreSQL: model={model_id}, asset={asset_id}")
                else:
                    logger.warning(f"⚠️ PostgreSQL写入失败: model={model_id}, asset={asset_id}")
                
                if td_success:
                    logger.debug(f"✅ 预测结果已保存到TDengine: model={model_id}, asset={asset_id}")
                else:
                    logger.warning(f"⚠️ TDengine写入失败（不影响主流程）: model={model_id}, asset={asset_id}")
                    
            except ImportError:
                logger.warning("PredictionStore模块未安装，使用传统方式保存")
                await self._save_prediction_postgresql_only(
                    version_id, asset_id, input_data, result
                )
            
        except Exception as e:
            logger.error(f"❌ 保存预测结果失败: {e}")
            # 不抛出异常，预测结果保存失败不影响预测本身
    
    async def _save_prediction_postgresql_only(
        self,
        version_id: int,
        asset_id: int,
        input_data: Dict[str, Any],
        result: Dict[str, Any]
    ):
        """仅保存到PostgreSQL（回退方案）"""
        from app.models.platform_upgrade import AIPrediction
        
        try:
            predicted_value = result.get("predicted_value", 0.0)
            confidence = result.get("confidence", 0.0)
            is_anomaly = result.get("is_anomaly")
            anomaly_score = result.get("anomaly_score")
            target_time = datetime.now() + timedelta(hours=1)
            
            prediction = AIPrediction(
                model_version_id=version_id,
                asset_id=asset_id,
                input_data=input_data,
                predicted_value=predicted_value,
                confidence=confidence,
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score,
                prediction_time=datetime.now(),
                target_time=target_time,
                prediction_details=result
            )
            await prediction.save()
            
            logger.debug(f"✅ 预测结果已保存到PostgreSQL: asset={asset_id}")
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL保存失败: {e}")
    
    def clear_predictor_cache(self, model_id: Optional[int] = None):
        """
        清除预测器缓存
        
        Args:
            model_id: 指定模型ID，为None时清除所有缓存
        """
        if model_id:
            if model_id in self._predictors:
                self._predictors[model_id].unload_model()
                del self._predictors[model_id]
                logger.info(f"已清除模型 {model_id} 的预测器缓存")
        else:
            for predictor in self._predictors.values():
                predictor.unload_model()
            self._predictors.clear()
            logger.info("已清除所有预测器缓存")


# 全局推理服务实例
inference_service = InferenceService()
