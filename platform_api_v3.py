# 工业AI数据平台 - API v3 接口设计

"""
API v3 设计原则：
1. 资产驱动：以Asset为核心，而非Device
2. 元数据驱动：动态Schema，支持任意设备类型
3. 统一响应格式：标准化错误处理和数据格式
4. RESTful设计：遵循REST规范
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from app.core.response import success_response, error_response
from app.core.auth_dependencies import get_current_user
from platform_upgrade_models import AssetCategory, Asset, SignalDefinition
from ai_engine_architecture import inference_service, model_registry
from feature_engine import feature_manager
from schema_manager import schema_manager


# =====================================================
# Pydantic模型定义
# =====================================================

class AssetCategoryCreate(BaseModel):
    """资产类别创建模型"""
    code: str = Field(..., description="类别编码")
    name: str = Field(..., description="类别名称")
    description: Optional[str] = Field(None, description="描述")
    industry: Optional[str] = Field(None, description="所属行业")
    icon: Optional[str] = Field(None, description="图标")


class AssetCategoryResponse(BaseModel):
    """资产类别响应模型"""
    id: int
    code: str
    name: str
    description: Optional[str]
    industry: Optional[str]
    icon: Optional[str]
    is_active: bool
    asset_count: int
    created_at: datetime
    updated_at: datetime


class SignalDefinitionCreate(BaseModel):
    """信号定义创建模型"""
    code: str = Field(..., description="信号编码")
    name: str = Field(..., description="信号名称")
    data_type: str = Field(..., description="数据类型")
    unit: Optional[str] = Field(None, description="单位")
    is_stored: bool = Field(True, description="是否存储")
    is_realtime: bool = Field(True, description="是否实时监控")
    is_feature: bool = Field(False, description="是否用于特征工程")
    value_range: Optional[Dict] = Field(None, description="值范围")
    display_config: Optional[Dict] = Field(None, description="显示配置")


class AssetCreate(BaseModel):
    """资产创建模型"""
    code: str = Field(..., description="资产编号")
    name: str = Field(..., description="资产名称")
    category_code: str = Field(..., description="资产类别编码")
    location: Optional[str] = Field(None, description="位置")
    attributes: Optional[Dict] = Field(default_factory=dict, description="静态属性")
    manufacturer: Optional[str] = Field(None, description="制造商")
    model: Optional[str] = Field(None, description="型号")


class AssetResponse(BaseModel):
    """资产响应模型"""
    id: int
    code: str
    name: str
    category: AssetCategoryResponse
    location: Optional[str]
    status: str
    attributes: Dict
    manufacturer: Optional[str]
    model: Optional[str]
    created_at: datetime
    updated_at: datetime


class PredictionRequest(BaseModel):
    """预测请求模型"""
    model_id: int = Field(..., description="模型ID")
    asset_id: int = Field(..., description="资产ID")
    input_data: Dict[str, Any] = Field(..., description="输入数据")


class FeatureViewCreate(BaseModel):
    """特征视图创建模型"""
    view_name: str = Field(..., description="视图名称")
    category_code: str = Field(..., description="资产类别编码")
    feature_configs: List[Dict] = Field(..., description="特征配置列表")


# =====================================================
# 资产类别管理API
# =====================================================

router = APIRouter(prefix="/api/v3", tags=["Platform API v3"])

@router.post("/asset-categories", response_model=Dict)
async def create_asset_category(
    category_data: AssetCategoryCreate,
    current_user = Depends(get_current_user)
):
    """创建资产类别"""
    try:
        # 1. 检查编码唯一性
        existing = await AssetCategory.filter(code=category_data.code).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"类别编码 {category_data.code} 已存在")
        
        # 2. 创建类别
        category = AssetCategory(
            code=category_data.code,
            name=category_data.name,
            description=category_data.description,
            industry=category_data.industry,
            icon=category_data.icon,
            tdengine_database="devicemonitor",
            tdengine_stable_prefix=f"raw_{category_data.code}"
        )
        await category.save()
        
        # 3. 初始化TDengine Schema
        await schema_manager.sync_category_schema(category_data.code)
        
        return success_response(
            data=await category.to_dict(),
            message="资产类别创建成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return error_response(message=f"创建失败: {str(e)}")


@router.get("/asset-categories", response_model=Dict)
async def list_asset_categories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    current_user = Depends(get_current_user)
):
    """获取资产类别列表"""
    try:
        # 1. 构建查询条件
        query = AssetCategory.all()
        if is_active is not None:
            query = query.filter(is_active=is_active)
        
        # 2. 分页查询
        total = await query.count()
        offset = (page - 1) * page_size
        categories = await query.offset(offset).limit(page_size)
        
        # 3. 转换为字典
        category_list = []
        for category in categories:
            category_dict = await category.to_dict()
            category_list.append(category_dict)
        
        return success_response(
            data={
                "items": category_list,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        )
        
    except Exception as e:
        return error_response(message=f"查询失败: {str(e)}")


@router.get("/asset-categories/{category_id}/signals", response_model=Dict)
async def get_category_signals(
    category_id: int,
    current_user = Depends(get_current_user)
):
    """获取资产类别的信号定义"""
    try:
        # 1. 获取类别
        category = await AssetCategory.get(id=category_id)
        
        # 2. 获取信号定义
        signals = await SignalDefinition.filter(
            category=category,
            is_active=True
        ).order_by("sort_order")
        
        # 3. 转换为字典
        signal_list = []
        for signal in signals:
            signal_dict = await signal.to_dict()
            signal_list.append(signal_dict)
        
        return success_response(
            data={
                "category": await category.to_dict(),
                "signals": signal_list
            }
        )
        
    except Exception as e:
        return error_response(message=f"查询失败: {str(e)}")


@router.post("/asset-categories/{category_id}/signals", response_model=Dict)
async def create_signal_definition(
    category_id: int,
    signal_data: SignalDefinitionCreate,
    current_user = Depends(get_current_user)
):
    """为资产类别创建信号定义"""
    try:
        # 1. 获取类别
        category = await AssetCategory.get(id=category_id)
        
        # 2. 检查信号编码唯一性
        existing = await SignalDefinition.filter(
            category=category,
            code=signal_data.code
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"信号编码 {signal_data.code} 已存在")
        
        # 3. 创建信号定义
        signal = SignalDefinition(
            category=category,
            code=signal_data.code,
            name=signal_data.name,
            data_type=signal_data.data_type,
            unit=signal_data.unit,
            is_stored=signal_data.is_stored,
            is_realtime=signal_data.is_realtime,
            is_feature=signal_data.is_feature,
            value_range=signal_data.value_range,
            display_config=signal_data.display_config
        )
        await signal.save()
        
        # 4. 同步TDengine Schema
        await schema_manager.sync_category_schema(category.code)
        
        return success_response(
            data=await signal.to_dict(),
            message="信号定义创建成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return error_response(message=f"创建失败: {str(e)}")


# =====================================================
# 资产管理API
# =====================================================

@router.post("/assets", response_model=Dict)
async def create_asset(
    asset_data: AssetCreate,
    current_user = Depends(get_current_user)
):
    """创建资产"""
    try:
        # 1. 获取资产类别
        category = await AssetCategory.get(code=asset_data.category_code)
        
        # 2. 检查资产编号唯一性
        existing = await Asset.filter(code=asset_data.code).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"资产编号 {asset_data.code} 已存在")
        
        # 3. 创建资产
        asset = Asset(
            category=category,
            code=asset_data.code,
            name=asset_data.name,
            location=asset_data.location,
            attributes=asset_data.attributes,
            manufacturer=asset_data.manufacturer,
            model=asset_data.model
        )
        await asset.save()
        
        # 4. 创建TDengine子表
        stable_name = f"raw_{category.code}"
        await schema_manager.create_child_table(stable_name, asset_data.code, asset.id)
        
        # 5. 返回完整资产信息
        asset_with_category = await Asset.get(id=asset.id).prefetch_related("category")
        
        return success_response(
            data=await asset_with_category.to_dict(),
            message="资产创建成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return error_response(message=f"创建失败: {str(e)}")


@router.get("/assets", response_model=Dict)
async def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_code: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user = Depends(get_current_user)
):
    """获取资产列表"""
    try:
        # 1. 构建查询条件
        query = Asset.all().prefetch_related("category")
        
        if category_code:
            query = query.filter(category__code=category_code)
        if status:
            query = query.filter(status=status)
        
        # 2. 分页查询
        total = await query.count()
        offset = (page - 1) * page_size
        assets = await query.offset(offset).limit(page_size)
        
        # 3. 转换为字典
        asset_list = []
        for asset in assets:
            asset_dict = await asset.to_dict()
            asset_list.append(asset_dict)
        
        return success_response(
            data={
                "items": asset_list,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        )
        
    except Exception as e:
        return error_response(message=f"查询失败: {str(e)}")


@router.get("/assets/{asset_id}/realtime-data", response_model=Dict)
async def get_asset_realtime_data(
    asset_id: int,
    current_user = Depends(get_current_user)
):
    """获取资产实时数据"""
    try:
        # 1. 获取资产信息
        asset = await Asset.get(id=asset_id).prefetch_related("category")
        
        # 2. 查询最新数据
        table_name = f"raw_{asset.category.code}_{asset.code}"
        
        sql = f"""
        SELECT * FROM {table_name}
        ORDER BY ts DESC
        LIMIT 1
        """
        
        from app.core.tdengine_connector import td_client
        result = await td_client.query(sql)
        
        return success_response(
            data={
                "asset": await asset.to_dict(),
                "realtime_data": result[0] if result else None,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        return error_response(message=f"查询失败: {str(e)}")


# =====================================================
# AI预测API
# =====================================================

@router.post("/predictions", response_model=Dict)
async def create_prediction(
    prediction_request: PredictionRequest,
    current_user = Depends(get_current_user)
):
    """执行AI预测"""
    try:
        # 执行预测
        result = await inference_service.predict(
            model_id=prediction_request.model_id,
            asset_id=prediction_request.asset_id,
            input_data=prediction_request.input_data
        )
        
        return success_response(
            data=result,
            message="预测执行成功" if result["success"] else "预测执行失败"
        )
        
    except Exception as e:
        return error_response(message=f"预测失败: {str(e)}")


@router.get("/assets/{asset_id}/predictions", response_model=Dict)
async def get_asset_predictions(
    asset_id: int,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    model_id: Optional[int] = Query(None),
    current_user = Depends(get_current_user)
):
    """获取资产的预测历史"""
    try:
        from platform_upgrade_models import AIPrediction
        
        # 1. 构建查询条件
        query = AIPrediction.filter(asset_id=asset_id).prefetch_related("model_version__model")
        
        if start_time:
            query = query.filter(prediction_time__gte=start_time)
        if end_time:
            query = query.filter(prediction_time__lte=end_time)
        if model_id:
            query = query.filter(model_version__model_id=model_id)
        
        # 2. 查询预测记录
        predictions = await query.order_by("-prediction_time").limit(100)
        
        # 3. 转换为字典
        prediction_list = []
        for prediction in predictions:
            prediction_dict = await prediction.to_dict()
            prediction_list.append(prediction_dict)
        
        return success_response(
            data={
                "asset_id": asset_id,
                "predictions": prediction_list,
                "count": len(prediction_list)
            }
        )
        
    except Exception as e:
        return error_response(message=f"查询失败: {str(e)}")


# =====================================================
# 特征工程API
# =====================================================

@router.post("/feature-views", response_model=Dict)
async def create_feature_view(
    feature_view_data: FeatureViewCreate,
    current_user = Depends(get_current_user)
):
    """创建特征视图"""
    try:
        # 创建特征视图
        success = await feature_manager.create_feature_view(
            category_code=feature_view_data.category_code,
            view_name=feature_view_data.view_name,
            feature_configs=feature_view_data.feature_configs
        )
        
        if success:
            return success_response(
                data={
                    "view_name": feature_view_data.view_name,
                    "category_code": feature_view_data.category_code,
                    "feature_count": len(feature_view_data.feature_configs)
                },
                message="特征视图创建成功"
            )
        else:
            return error_response(message="特征视图创建失败")
        
    except Exception as e:
        return error_response(message=f"创建失败: {str(e)}")


@router.get("/asset-categories/{category_code}/feature-views", response_model=Dict)
async def list_feature_views(
    category_code: str,
    current_user = Depends(get_current_user)
):
    """获取资产类别的特征视图列表"""
    try:
        views = await feature_manager.list_feature_views(category_code)
        
        return success_response(
            data={
                "category_code": category_code,
                "feature_views": views
            }
        )
        
    except Exception as e:
        return error_response(message=f"查询失败: {str(e)}")


@router.get("/feature-data/{category_code}/{view_name}", response_model=Dict)
async def get_feature_data(
    category_code: str,
    view_name: str,
    asset_id: int = Query(...),
    hours: int = Query(24, ge=1, le=168),  # 最多7天
    current_user = Depends(get_current_user)
):
    """获取特征数据"""
    try:
        # 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # 获取特征数据
        feature_data = await feature_manager.get_feature_data(
            category_code=category_code,
            view_name=view_name,
            asset_id=asset_id,
            start_time=start_time,
            end_time=end_time
        )
        
        return success_response(
            data={
                "category_code": category_code,
                "view_name": view_name,
                "asset_id": asset_id,
                "time_range": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                },
                "data": feature_data,
                "count": len(feature_data)
            }
        )
        
    except Exception as e:
        return error_response(message=f"查询失败: {str(e)}")


# =====================================================
# 系统状态API
# =====================================================

@router.get("/system/status", response_model=Dict)
async def get_system_status(current_user = Depends(get_current_user)):
    """获取系统状态"""
    try:
        # 1. 统计资产类别数量
        category_count = await AssetCategory.filter(is_active=True).count()
        
        # 2. 统计资产数量
        asset_count = await Asset.all().count()
        
        # 3. 统计在线资产数量
        online_asset_count = await Asset.filter(status="online").count()
        
        # 4. 统计AI模型数量
        from platform_upgrade_models import AIModel
        model_count = await AIModel.filter(is_active=True).count()
        
        return success_response(
            data={
                "category_count": category_count,
                "asset_count": asset_count,
                "online_asset_count": online_asset_count,
                "model_count": model_count,
                "system_time": datetime.now().isoformat(),
                "version": "3.0.0"
            }
        )
        
    except Exception as e:
        return error_response(message=f"查询失败: {str(e)}")


# 导出路由
platform_router = router