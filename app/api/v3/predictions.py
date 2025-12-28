"""
AI预测API v3
实现预测请求处理、预测历史查询、AI引擎服务集成

需求：2.4
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta

from app.core.auth_dependencies import get_current_active_user
from app.core.unified_logger import get_logger
from app.schemas.base import Success, Fail, SuccessExtra
from app.models.admin import User

from .schemas import PredictionRequest

logger = get_logger(__name__)
router = APIRouter()


# =====================================================
# 辅助函数
# =====================================================

async def get_prediction_model():
    """延迟导入AIPrediction模型"""
    from app.models.platform_upgrade import AIPrediction
    return AIPrediction


async def get_model_registry():
    """延迟导入模型注册中心"""
    try:
        from app.services.ai.model_registry import model_registry
        return model_registry
    except ImportError:
        logger.warning("AI模型注册中心未配置")
        return None


async def get_inference_service():
    """延迟导入推理服务"""
    try:
        from app.services.ai.inference_service import inference_service
        return inference_service
    except ImportError:
        logger.warning("AI推理服务未配置")
        return None


async def prediction_to_dict(prediction) -> dict:
    """将预测结果转换为字典"""
    return {
        "id": prediction.id,
        "model_version_id": prediction.model_version_id,
        "asset_id": prediction.asset_id,
        "input_data": prediction.input_data,
        "predicted_value": prediction.predicted_value,
        "confidence": prediction.confidence,
        "prediction_details": prediction.prediction_details,
        "prediction_time": prediction.prediction_time.isoformat() if prediction.prediction_time else None,
        "target_time": prediction.target_time.isoformat() if prediction.target_time else None,
        "actual_value": prediction.actual_value,
        "actual_recorded_at": prediction.actual_recorded_at.isoformat() if prediction.actual_recorded_at else None,
        "is_anomaly": prediction.is_anomaly,
        "anomaly_score": prediction.anomaly_score,
        "created_at": prediction.created_at.isoformat() if prediction.created_at else None
    }


# =====================================================
# 预测请求API
# =====================================================

@router.post("", summary="执行AI预测")
async def create_prediction(
    prediction_request: PredictionRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    执行AI预测
    
    - 验证模型和资产存在
    - 调用推理服务执行预测
    - 持久化预测结果
    
    需求：2.4
    """
    try:
        inference_service = await get_inference_service()
        if not inference_service:
            return Fail(code=503, msg="AI推理服务不可用")
        
        from app.models.platform_upgrade import AIModel, AIModelVersion, Asset, AIPrediction
        
        # 1. 验证模型存在
        model = await AIModel.get_or_none(id=prediction_request.model_id)
        if not model:
            return Fail(code=404, msg=f"AI模型不存在: {prediction_request.model_id}")
        
        if not model.is_active:
            return Fail(code=400, msg=f"AI模型未激活: {model.name}")
        
        # 2. 获取激活的模型版本
        active_version = await AIModelVersion.filter(
            model_id=model.id,
            status="prod"
        ).first()
        
        if not active_version:
            return Fail(code=400, msg=f"模型没有激活的版本: {model.name}")
        
        # 3. 验证资产存在
        asset = await Asset.get_or_none(id=prediction_request.asset_id)
        if not asset:
            return Fail(code=404, msg=f"资产不存在: {prediction_request.asset_id}")
        
        # 4. 执行预测
        try:
            result = await inference_service.predict(
                model_id=prediction_request.model_id,
                asset_id=prediction_request.asset_id,
                input_data=prediction_request.input_data
            )
        except Exception as e:
            logger.error(f"推理执行失败: {e}")
            return Fail(code=500, msg=f"预测执行失败: {str(e)}")
        
        # 5. 保存预测结果
        prediction = AIPrediction(
            model_version_id=active_version.id,
            asset_id=prediction_request.asset_id,
            input_data=prediction_request.input_data,
            predicted_value=result.get("predicted_value", 0),
            confidence=result.get("confidence"),
            prediction_details=result.get("details"),
            prediction_time=datetime.now(),
            target_time=datetime.now() + timedelta(hours=1),  # 默认预测1小时后
            is_anomaly=result.get("is_anomaly"),
            anomaly_score=result.get("anomaly_score")
        )
        await prediction.save()
        
        logger.info(f"预测执行成功: 模型={model.name}, 资产={asset.code}, 用户={current_user.username}")
        
        return Success(
            code=200,
            msg="预测执行成功",
            data={
                "prediction_id": prediction.id,
                "model_name": model.name,
                "asset_code": asset.code,
                "predicted_value": prediction.predicted_value,
                "confidence": prediction.confidence,
                "is_anomaly": prediction.is_anomaly,
                "anomaly_score": prediction.anomaly_score,
                "prediction_time": prediction.prediction_time.isoformat(),
                "details": prediction.prediction_details
            }
        )
        
    except Exception as e:
        logger.error(f"执行预测失败: {e}")
        return Fail(code=500, msg=f"预测失败: {str(e)}")


@router.post("/batch", summary="批量执行AI预测")
async def batch_prediction(
    model_id: int = Query(..., description="模型ID"),
    asset_ids: List[int] = Query(..., description="资产ID列表"),
    input_data: dict = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    批量执行AI预测
    
    对多个资产执行同一模型的预测
    
    需求：2.4
    """
    try:
        inference_service = await get_inference_service()
        if not inference_service:
            return Fail(code=503, msg="AI推理服务不可用")
        
        from app.models.platform_upgrade import AIModel, AIModelVersion, Asset, AIPrediction
        
        # 1. 验证模型
        model = await AIModel.get_or_none(id=model_id)
        if not model or not model.is_active:
            return Fail(code=404, msg=f"AI模型不存在或未激活: {model_id}")
        
        active_version = await AIModelVersion.filter(model_id=model.id, status="prod").first()
        if not active_version:
            return Fail(code=400, msg=f"模型没有激活的版本")
        
        # 2. 验证资产
        assets = await Asset.filter(id__in=asset_ids).all()
        if len(assets) != len(asset_ids):
            return Fail(code=400, msg="部分资产不存在")
        
        # 3. 批量预测
        results = []
        for asset in assets:
            try:
                result = await inference_service.predict(
                    model_id=model_id,
                    asset_id=asset.id,
                    input_data=input_data or {}
                )
                
                # 保存预测结果
                prediction = AIPrediction(
                    model_version_id=active_version.id,
                    asset_id=asset.id,
                    input_data=input_data or {},
                    predicted_value=result.get("predicted_value", 0),
                    confidence=result.get("confidence"),
                    prediction_details=result.get("details"),
                    prediction_time=datetime.now(),
                    target_time=datetime.now() + timedelta(hours=1),
                    is_anomaly=result.get("is_anomaly"),
                    anomaly_score=result.get("anomaly_score")
                )
                await prediction.save()
                
                results.append({
                    "asset_id": asset.id,
                    "asset_code": asset.code,
                    "success": True,
                    "prediction_id": prediction.id,
                    "predicted_value": prediction.predicted_value
                })
                
            except Exception as e:
                results.append({
                    "asset_id": asset.id,
                    "asset_code": asset.code,
                    "success": False,
                    "error": str(e)
                })
        
        success_count = sum(1 for r in results if r["success"])
        logger.info(f"批量预测完成: {success_count}/{len(assets)}, 用户={current_user.username}")
        
        return Success(
            code=200,
            msg=f"批量预测完成: {success_count}/{len(assets)} 成功",
            data={
                "model_name": model.name,
                "total": len(assets),
                "success_count": success_count,
                "results": results
            }
        )
        
    except Exception as e:
        logger.error(f"批量预测失败: {e}")
        return Fail(code=500, msg=f"批量预测失败: {str(e)}")


# =====================================================
# 预测历史查询API
# =====================================================

@router.get("/history", summary="获取预测历史")
async def get_prediction_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    model_id: Optional[int] = Query(None, description="模型ID"),
    asset_id: Optional[int] = Query(None, description="资产ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    is_anomaly: Optional[bool] = Query(None, description="是否异常"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取预测历史记录
    
    支持按模型、资产、时间范围、异常状态筛选
    
    需求：2.4
    """
    try:
        AIPrediction = await get_prediction_model()
        
        # 1. 构建查询条件
        query = AIPrediction.all()
        
        if model_id:
            from app.models.platform_upgrade import AIModelVersion
            versions = await AIModelVersion.filter(model_id=model_id).values_list("id", flat=True)
            query = query.filter(model_version_id__in=versions)
        if asset_id:
            query = query.filter(asset_id=asset_id)
        if start_time:
            query = query.filter(prediction_time__gte=start_time)
        if end_time:
            query = query.filter(prediction_time__lte=end_time)
        if is_anomaly is not None:
            query = query.filter(is_anomaly=is_anomaly)
        
        # 2. 分页查询
        total = await query.count()
        offset = (page - 1) * page_size
        predictions = await query.order_by("-prediction_time").offset(offset).limit(page_size)
        
        # 3. 转换为字典列表
        prediction_list = [await prediction_to_dict(p) for p in predictions]
        
        return SuccessExtra(
            code=200,
            msg="获取成功",
            data=prediction_list,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"获取预测历史失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")


@router.get("/assets/{asset_id}", summary="获取资产的预测历史")
async def get_asset_predictions(
    asset_id: int,
    model_id: Optional[int] = Query(None, description="模型ID"),
    hours: int = Query(24, ge=1, le=168, description="查询最近N小时"),
    limit: int = Query(100, ge=1, le=1000, description="最大返回条数"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取指定资产的预测历史
    
    需求：2.4
    """
    try:
        AIPrediction = await get_prediction_model()
        from app.models.platform_upgrade import Asset
        
        # 1. 验证资产存在
        asset = await Asset.get_or_none(id=asset_id)
        if not asset:
            return Fail(code=404, msg=f"资产不存在: {asset_id}")
        
        # 2. 构建查询条件
        start_time = datetime.now() - timedelta(hours=hours)
        query = AIPrediction.filter(
            asset_id=asset_id,
            prediction_time__gte=start_time
        )
        
        if model_id:
            from app.models.platform_upgrade import AIModelVersion
            versions = await AIModelVersion.filter(model_id=model_id).values_list("id", flat=True)
            query = query.filter(model_version_id__in=versions)
        
        # 3. 查询
        predictions = await query.order_by("-prediction_time").limit(limit)
        
        # 4. 转换为字典列表
        prediction_list = [await prediction_to_dict(p) for p in predictions]
        
        return Success(
            code=200,
            msg="获取成功",
            data={
                "asset_id": asset_id,
                "asset_code": asset.code,
                "predictions": prediction_list,
                "count": len(prediction_list)
            }
        )
        
    except Exception as e:
        logger.error(f"获取资产预测历史失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")


@router.get("/{prediction_id}", summary="获取预测详情")
async def get_prediction_detail(
    prediction_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    获取单个预测的详细信息
    
    需求：2.4
    """
    try:
        AIPrediction = await get_prediction_model()
        from app.models.platform_upgrade import AIModelVersion, AIModel, Asset
        
        prediction = await AIPrediction.get_or_none(id=prediction_id)
        if not prediction:
            return Fail(code=404, msg=f"预测记录不存在: {prediction_id}")
        
        # 获取关联信息
        model_version = await AIModelVersion.get_or_none(id=prediction.model_version_id)
        model = await AIModel.get_or_none(id=model_version.model_id) if model_version else None
        asset = await Asset.get_or_none(id=prediction.asset_id)
        
        result = await prediction_to_dict(prediction)
        result["model"] = {
            "id": model.id,
            "name": model.name,
            "algorithm": model.algorithm
        } if model else None
        result["model_version"] = {
            "id": model_version.id,
            "version": model_version.version
        } if model_version else None
        result["asset"] = {
            "id": asset.id,
            "code": asset.code,
            "name": asset.name
        } if asset else None
        
        return Success(
            code=200,
            msg="获取成功",
            data=result
        )
        
    except Exception as e:
        logger.error(f"获取预测详情失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")


# =====================================================
# 预测结果更新API
# =====================================================

@router.put("/{prediction_id}/actual", summary="更新预测的实际值")
async def update_prediction_actual(
    prediction_id: int,
    actual_value: float = Query(..., description="实际值"),
    current_user: User = Depends(get_current_active_user)
):
    """
    更新预测记录的实际值（用于模型评估）
    
    需求：2.4
    """
    try:
        AIPrediction = await get_prediction_model()
        
        prediction = await AIPrediction.get_or_none(id=prediction_id)
        if not prediction:
            return Fail(code=404, msg=f"预测记录不存在: {prediction_id}")
        
        prediction.actual_value = actual_value
        prediction.actual_recorded_at = datetime.now()
        await prediction.save()
        
        logger.info(f"预测实际值更新: {prediction_id}, 值={actual_value}, 用户={current_user.username}")
        
        return Success(
            code=200,
            msg="更新成功",
            data=await prediction_to_dict(prediction)
        )
        
    except Exception as e:
        logger.error(f"更新预测实际值失败: {e}")
        return Fail(code=500, msg=f"更新失败: {str(e)}")
