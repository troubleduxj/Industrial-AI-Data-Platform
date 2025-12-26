#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI异常检测API

提供设备数据异常检测功能，支持多种检测算法和严重程度划分。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
import logging

from app.core.response_formatter_v2 import create_formatter
from app.core.dependency import DependAuth
from app.services.ai.anomaly_detection import AnomalyDetector
from app.models.ai_monitoring import AIAnomalyRecord, AIAnomalyConfig
from app.core.exceptions import APIException
from app.schemas.base import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/anomalies", tags=["AI异常检测"])
formatter = create_formatter()


# ==================== 请求/响应模型 ====================

class AnomalyDetectionRequest(BaseModel):
    """异常检测请求"""
    data: List[float] = Field(..., description="设备数据时间序列", min_items=3)
    device_code: Optional[str] = Field(None, description="设备编码（用于记录）")
    device_name: Optional[str] = Field(None, description="设备名称")
    method: str = Field(
        default="combined",
        description="检测方法：statistical（统计）、isolation_forest（孤立森林）、combined（组合）"
    )
    threshold: float = Field(
        default=3.0,
        description="统计方法的阈值（sigma倍数），默认3.0",
        gt=0
    )
    save_to_db: bool = Field(
        default=False,
        description="是否保存异常记录到数据库"
    )


class AnomalyPoint(BaseModel):
    """异常点信息"""
    index: int = Field(..., description="异常点索引")
    value: float = Field(..., description="异常值")
    score: float = Field(..., description="异常分数（越高越异常）")
    severity: str = Field(..., description="严重程度：极低、低、中等、高、极高")
    method: str = Field(..., description="检测方法")


class AnomalyDetectionResponse(BaseModel):
    """异常检测响应"""
    is_anomaly: bool = Field(..., description="是否检测到异常")
    anomaly_count: int = Field(..., description="异常点数量")
    anomaly_rate: float = Field(..., description="异常率（百分比）")
    anomalies: List[AnomalyPoint] = Field(..., description="异常点详细信息")
    data_points: int = Field(..., description="输入数据点数")
    method_used: str = Field(..., description="使用的检测方法")


class BatchAnomalyDetectionRequest(BaseModel):
    """批量异常检测请求"""
    dataset: Dict[str, List[float]] = Field(..., description="设备数据集")
    method: str = Field(default="combined", description="检测方法")
    threshold: float = Field(default=3.0, description="统计阈值")


class BatchAnomalyDetectionResponse(BaseModel):
    """批量异常检测响应"""
    results: Dict[str, dict] = Field(..., description="批量检测结果")
    total_devices: int = Field(..., description="处理的设备总数")
    anomaly_devices: List[str] = Field(..., description="检测到异常的设备列表")
    anomaly_device_count: int = Field(..., description="异常设备数量")


# ==================== API端点 ====================

@router.post(
    "/detect",
    summary="检测数据异常",
    description="使用AI算法检测设备数据中的异常点，支持统计、孤立森林和组合方法",
    response_model=APIResponse[AnomalyDetectionResponse],
    dependencies=[DependAuth]
)
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    current_user=DependAuth
):
    """
    检测数据异常
    
    **检测方法**:
    - `statistical`: 基于3-sigma规则的统计异常检测
    - `isolation_forest`: 基于孤立森林的机器学习异常检测
    - `combined`: 组合多种方法，提高检测准确性
    
    **严重程度划分**:
    - 极低：异常分数 < 0.3
    - 低：0.3 ≤ 分数 < 0.5
    - 中等：0.5 ≤ 分数 < 0.7
    - 高：0.7 ≤ 分数 < 0.9
    - 极高：分数 ≥ 0.9
    
    **使用场景**:
    - 实时设备监控
    - 故障预警
    - 数据质量检查
    
    **示例**:
    ```json
    {
      "data": [100, 102, 98, 150, 99],
      "device_code": "WD001",
      "method": "combined",
      "save_to_db": true
    }
    ```
    """
    try:
        logger.info(
            f"用户 {current_user.username} 请求异常检测，"
            f"设备: {request.device_code or 'N/A'}，数据点数: {len(request.data)}"
        )
        
        # 验证数据
        if len(request.data) < 3:
            raise APIException(
                status_code=400,
                code="INSUFFICIENT_DATA",
                message="数据点数至少需要3个才能进行异常检测"
            )
        
        # 验证检测方法
        valid_methods = {"statistical", "isolation_forest", "combined"}
        if request.method not in valid_methods:
            raise APIException(
                status_code=400,
                code="INVALID_METHOD",
                message=f"无效的检测方法。有效方法: {', '.join(valid_methods)}"
            )
        
        # 创建异常检测器
        detector = AnomalyDetector(threshold=request.threshold)
        
        # 执行检测
        result = detector.detect(request.data, method=request.method)
        
        # 构建响应
        anomalies = []
        for anomaly in result["anomalies"]:
            anomalies.append(AnomalyPoint(
                index=anomaly["index"],
                value=anomaly["value"],
                score=anomaly["score"],
                severity=anomaly["severity"],
                method=anomaly["method"]
            ))
        
        anomaly_count = len(anomalies)
        anomaly_rate = (anomaly_count / len(request.data)) * 100 if request.data else 0.0
        
        response = AnomalyDetectionResponse(
            is_anomaly=result["is_anomaly"],
            anomaly_count=anomaly_count,
            anomaly_rate=round(anomaly_rate, 2),
            anomalies=anomalies,
            data_points=len(request.data),
            method_used=request.method
        )
        
        # 保存到数据库
        if request.save_to_db and result["is_anomaly"]:
            try:
                await AIAnomalyRecord.create(
                    device_code=request.device_code or "UNKNOWN",
                    device_name=request.device_name or "未知设备",
                    anomaly_type=request.method,
                    severity=anomalies[0].severity if anomalies else "低",  # 使用第一个异常的严重程度
                    anomaly_score=anomalies[0].score if anomalies else 0.0,
                    detection_time=datetime.now(),
                    anomaly_data={
                        "anomalies": [a.dict() for a in anomalies],
                        "data_points": len(request.data),
                        "anomaly_rate": anomaly_rate
                    },
                    is_handled=False
                )
                logger.info(f"异常记录已保存到数据库，设备: {request.device_code}")
            except Exception as e:
                logger.error(f"保存异常记录失败: {str(e)}", exc_info=True)
                # 不阻止响应，只记录错误
        
        logger.info(
            f"异常检测完成，检测到 {anomaly_count} 个异常点，"
            f"异常率: {anomaly_rate:.2f}%"
        )
        
        return formatter.success(
            data=response,
            message=f"检测完成，发现 {anomaly_count} 个异常点"
        )
    
    except APIException:
        raise
    except Exception as e:
        logger.error(f"异常检测失败: {str(e)}", exc_info=True)
        # Print for debugging
        import traceback
        traceback.print_exc()
        raise APIException(
            status_code=500,
            code="ANOMALY_DETECTION_ERROR",
            message=f"异常检测失败: {str(e)}"
        )


@router.post(
    "/detect/batch",
    summary="批量异常检测",
    description="批量检测多个设备的数据异常",
    response_model=APIResponse[BatchAnomalyDetectionResponse],
    dependencies=[DependAuth]
)
async def batch_detect_anomalies(
    request: BatchAnomalyDetectionRequest,
    current_user=DependAuth
):
    """
    批量异常检测
    
    **功能**:
    - 同时处理多个设备的数据
    - 自动跳过异常数据
    - 返回异常设备列表
    
    **使用场景**:
    - 设备群组监控
    - 批量故障诊断
    - 定期巡检
    """
    try:
        logger.info(f"用户 {current_user.username} 请求批量异常检测，设备数: {len(request.dataset)}")
        
        if not request.dataset:
            raise APIException(
                status_code=400,
                code="EMPTY_DATASET",
                message="数据集不能为空"
            )
        
        # 创建异常检测器
        detector = AnomalyDetector(threshold=request.threshold)
        
        # 批量检测
        results = {}
        anomaly_devices = []
        
        for device_id, data in request.dataset.items():
            try:
                if len(data) < 3:
                    logger.warning(f"设备 {device_id} 数据点数不足，跳过")
                    continue
                
                # 检测异常
                result = detector.detect(data, method=request.method)
                
                results[device_id] = {
                    "is_anomaly": result["is_anomaly"],
                    "anomaly_count": len(result["anomalies"]),
                    "anomaly_rate": (len(result["anomalies"]) / len(data)) * 100,
                    "anomalies": result["anomalies"]
                }
                
                if result["is_anomaly"]:
                    anomaly_devices.append(device_id)
                
            except Exception as e:
                logger.error(f"设备 {device_id} 异常检测失败: {str(e)}")
                continue
        
        response = BatchAnomalyDetectionResponse(
            results=results,
            total_devices=len(request.dataset),
            anomaly_devices=anomaly_devices,
            anomaly_device_count=len(anomaly_devices)
        )
        
        logger.info(f"批量异常检测完成，异常设备: {len(anomaly_devices)}/{len(request.dataset)}")
        
        return formatter.success(
            data=response,
            message=f"批量检测完成，发现 {len(anomaly_devices)} 个异常设备"
        )
    
    except APIException:
        raise
    except Exception as e:
        logger.error(f"批量异常检测失败: {str(e)}", exc_info=True)
        raise APIException(
            status_code=500,
            code="BATCH_ANOMALY_DETECTION_ERROR",
            message=f"批量异常检测失败: {str(e)}"
        )


@router.get(
    "/records",
    summary="获取异常记录",
    description="查询历史异常记录",
    dependencies=[DependAuth]
)
async def get_anomaly_records(
    device_code: Optional[str] = Query(None, description="设备编码"),
    severity: Optional[str] = Query(None, description="严重程度"),
    is_handled: Optional[bool] = Query(None, description="是否已处理"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user=DependAuth
):
    """
    获取异常记录
    
    **查询条件**:
    - device_code: 按设备编码筛选
    - severity: 按严重程度筛选（极低/低/中等/高/极高）
    - is_handled: 按处理状态筛选
    
    **返回**: 分页的异常记录列表
    """
    try:
        # 构建查询
        query = AIAnomalyRecord.all()
        
        if device_code:
            query = query.filter(device_code=device_code)
        
        if severity:
            query = query.filter(severity=severity)
        
        if is_handled is not None:
            query = query.filter(is_handled=is_handled)
        
        # 总数
        total = await query.count()
        
        # 分页
        offset = (page - 1) * page_size
        records = await query.offset(offset).limit(page_size).order_by("-detection_time")
        
        # 转换为字典
        records_data = []
        for record in records:
            records_data.append({
                "id": record.id,
                "device_code": record.device_code,
                "device_name": record.device_name,
                "anomaly_type": record.anomaly_type,
                "severity": record.severity,
                "anomaly_score": record.anomaly_score,
                "detection_time": record.detection_time.isoformat() if record.detection_time else None,
                "anomaly_data": record.anomaly_data,
                "is_handled": record.is_handled,
                "handle_time": record.handle_time.isoformat() if record.handle_time else None,
                "handle_by": record.handle_by,
                "handle_note": record.handle_note
            })
        
        return formatter.success(
            data={
                "records": records_data,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            },
            message=f"成功获取 {len(records_data)} 条异常记录"
        )
    
    except Exception as e:
        logger.error(f"获取异常记录失败: {str(e)}", exc_info=True)
        raise APIException(
            status_code=500,
            code="GET_ANOMALY_RECORDS_ERROR",
            message=f"获取异常记录失败: {str(e)}"
        )


@router.put(
    "/records/{record_id}/handle",
    summary="处理异常记录",
    description="标记异常记录为已处理",
    dependencies=[DependAuth]
)
async def handle_anomaly_record(
    record_id: int,
    handle_note: Optional[str] = None,
    current_user=DependAuth
):
    """处理异常记录"""
    try:
        record = await AIAnomalyRecord.get_or_none(id=record_id)
        if not record:
            raise APIException(
                status_code=404,
                code="RECORD_NOT_FOUND",
                message=f"异常记录 {record_id} 不存在"
            )
        
        # 更新记录
        record.is_handled = True
        record.handle_time = datetime.now()
        record.handle_by = current_user.username
        record.handle_note = handle_note
        await record.save()
        
        logger.info(f"异常记录 {record_id} 已被 {current_user.username} 处理")
        
        return formatter.success(
            data={"record_id": record_id},
            message="异常记录已处理"
        )
    
    except APIException:
        raise
    except Exception as e:
        logger.error(f"处理异常记录失败: {str(e)}", exc_info=True)
        raise APIException(
            status_code=500,
            code="HANDLE_ANOMALY_RECORD_ERROR",
            message=f"处理异常记录失败: {str(e)}"
        )


class AnomalyConfigResponse(BaseModel):
    """异常检测配置响应"""
    device_code: str
    config_data: Dict[str, Any]
    is_active: bool
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None


class UpdateAnomalyConfigRequest(BaseModel):
    """更新异常检测配置请求"""
    config_data: Dict[str, Any]
    is_active: bool = True


class MonitoredDeviceItem(BaseModel):
    """监控设备项"""
    device_code: str
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    is_active: bool = True
    anomaly_count: int = 0
    anomaly_score: float = 0.0
    severity: str = "low"
    last_check_time: Optional[str] = None
    config_data: Dict[str, Any] = {}


class MonitoredDevicesResponse(BaseModel):
    """监控设备列表响应"""
    items: List[MonitoredDeviceItem]
    total: int


@router.get(
    "/monitored-devices",
    summary="获取已配置异常检测的设备列表",
    description="获取所有已配置异常检测的设备及其状态",
    response_model=APIResponse[MonitoredDevicesResponse],
    dependencies=[DependAuth]
)
async def get_monitored_devices(
    is_active: Optional[bool] = Query(None, description="是否只返回启用的设备"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=500, description="每页数量"),
    current_user=DependAuth
):
    """
    获取已配置异常检测的设备列表
    
    返回所有在 t_ai_anomaly_configs 表中配置的设备，
    并关联其异常记录统计信息。
    """
    try:
        from app.models.device import DeviceInfo
        from datetime import timedelta
        
        # 构建查询
        query = AIAnomalyConfig.all()
        
        if is_active is not None:
            query = query.filter(is_active=is_active)
        
        # 总数
        total = await query.count()
        
        # 分页
        offset = (page - 1) * page_size
        configs = await query.offset(offset).limit(page_size).order_by("-updated_at")
        
        # 获取设备信息和异常统计
        items = []
        for config in configs:
            # 获取设备基本信息
            device = await DeviceInfo.get_or_none(device_code=config.device_code)
            
            # 获取最近24小时的异常统计
            now = datetime.now()
            yesterday = now - timedelta(hours=24)
            
            anomaly_records = await AIAnomalyRecord.filter(
                device_code=config.device_code,
                detection_time__gte=yesterday
            ).order_by("-detection_time")
            
            anomaly_count = len(anomaly_records)
            
            # 计算异常分数和严重程度
            if anomaly_count > 0:
                avg_score = sum(r.anomaly_score for r in anomaly_records) / anomaly_count
                # 根据异常数量和平均分数计算综合风险分数
                risk_score = min(100, avg_score * 100 + anomaly_count * 2)
                
                # 确定严重程度
                if risk_score >= 70:
                    severity = "high"
                elif risk_score >= 40:
                    severity = "medium"
                else:
                    severity = "low"
                
                last_check_time = anomaly_records[0].detection_time.isoformat() if anomaly_records else None
            else:
                risk_score = 0
                severity = "low"
                last_check_time = config.updated_at.isoformat() if config.updated_at else None
            
            items.append(MonitoredDeviceItem(
                device_code=config.device_code,
                device_name=device.device_name if device else None,
                device_type=device.device_type if device else None,
                is_active=config.is_active,
                anomaly_count=anomaly_count,
                anomaly_score=round(risk_score, 1),
                severity=severity,
                last_check_time=last_check_time,
                config_data=config.config_data or {}
            ))
        
        return formatter.success(
            data=MonitoredDevicesResponse(items=items, total=total),
            message=f"获取到 {len(items)} 个监控设备"
        )
    
    except Exception as e:
        logger.error(f"获取监控设备列表失败: {str(e)}", exc_info=True)
        raise APIException(
            status_code=500,
            code="GET_MONITORED_DEVICES_ERROR",
            message=f"获取监控设备列表失败: {str(e)}"
        )


@router.get(
    "/config/{device_code}",
    summary="获取设备异常检测配置",
    description="获取指定设备的异常检测配置",
    response_model=APIResponse[AnomalyConfigResponse],
    dependencies=[DependAuth]
)
async def get_anomaly_config(
    device_code: str,
    current_user=DependAuth
):
    try:
        config = await AIAnomalyConfig.get_or_none(device_code=device_code)
        
        if not config:
            # Return empty config if not found
            return formatter.success(
                data={
                    "device_code": device_code,
                    "config_data": {},
                    "is_active": True,
                    "updated_at": None,
                    "updated_by": None
                },
                message="未找到配置，返回默认值"
            )
            
        return formatter.success(
            data={
                "device_code": config.device_code,
                "config_data": config.config_data,
                "is_active": config.is_active,
                "updated_at": config.updated_at.isoformat() if config.updated_at else None,
                "updated_by": config.updated_by
            },
            message="获取配置成功"
        )
    except Exception as e:
        logger.error(f"获取异常检测配置失败: {str(e)}", exc_info=True)
        raise APIException(
            status_code=500,
            code="GET_CONFIG_ERROR",
            message=f"获取配置失败: {str(e)}"
        )


@router.put(
    "/config/{device_code}",
    summary="更新设备异常检测配置",
    description="更新指定设备的异常检测配置",
    response_model=APIResponse[AnomalyConfigResponse],
    dependencies=[DependAuth]
)
async def update_anomaly_config(
    device_code: str,
    request: UpdateAnomalyConfigRequest,
    current_user=DependAuth
):
    try:
        logger.info(f"Updating anomaly config for device {device_code}, user: {current_user.username}")
        config = await AIAnomalyConfig.get_or_none(device_code=device_code)
        logger.info(f"Config found: {config is not None}")
        
        if config:
            config.config_data = request.config_data
            config.is_active = request.is_active
            config.updated_by = current_user.username
            await config.save()
            logger.info("Config updated successfully")
        else:
            logger.info("Creating new config")
            config = await AIAnomalyConfig.create(
                device_code=device_code,
                config_data=request.config_data,
                is_active=request.is_active,
                updated_by=current_user.username
            )
            logger.info("Config created successfully")
            
        return formatter.success(
            data={
                "device_code": config.device_code,
                "config_data": config.config_data,
                "is_active": config.is_active,
                "updated_at": config.updated_at.isoformat() if config.updated_at else None,
                "updated_by": config.updated_by
            },
            message="配置已保存"
        )
    except Exception as e:
        logger.error(f"更新异常检测配置失败: {str(e)}", exc_info=True)
        raise APIException(
            status_code=500,
            code="UPDATE_CONFIG_ERROR",
            message=f"更新配置失败: {str(e)}"
        )

