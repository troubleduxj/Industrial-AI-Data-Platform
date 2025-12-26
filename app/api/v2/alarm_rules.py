#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报警规则管理 API v2
提供报警规则的CRUD操作
"""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel, Field

from app.models.alarm import AlarmRule, AlarmRecord
from app.models.device import DeviceField, DeviceType
from app.core.response_formatter_v2 import create_formatter
from app.core.pagination import get_pagination_params, create_pagination_response
from app.log import logger

router = APIRouter(tags=["报警规则管理"])


# =====================================================
# Pydantic 模型
# =====================================================

class ThresholdConfig(BaseModel):
    """阈值配置"""
    type: str = Field("range", description="阈值类型: range/upper/lower/change_rate")
    warning: Optional[dict] = Field(None, description="警告阈值")
    critical: Optional[dict] = Field(None, description="严重阈值")
    emergency: Optional[dict] = Field(None, description="紧急阈值")


class TriggerCondition(BaseModel):
    """触发条件"""
    consecutive_count: int = Field(1, description="连续触发次数")
    duration_seconds: Optional[int] = Field(None, description="持续时间(秒)")
    check_interval: Optional[int] = Field(10, description="检测间隔(秒)")


class AlarmRuleCreate(BaseModel):
    """创建报警规则"""
    rule_name: str = Field(..., description="规则名称")
    rule_code: str = Field(..., description="规则代码")
    description: Optional[str] = Field(None, description="规则描述")
    device_type_code: str = Field(..., description="设备类型代码")
    device_code: Optional[str] = Field(None, description="关联设备编码，为空则为通用规则")
    field_code: str = Field(..., description="监测字段代码")
    field_name: Optional[str] = Field(None, description="字段名称")
    threshold_config: dict = Field(..., description="阈值配置")
    trigger_condition: Optional[dict] = Field(None, description="触发条件")
    trigger_config: Optional[dict] = Field(None, description="高级触发配置")
    alarm_level: str = Field("warning", description="默认报警级别")
    notification_config: Optional[dict] = Field(None, description="通知配置")
    is_enabled: bool = Field(True, description="是否启用")
    priority: int = Field(0, description="优先级")


class AlarmRuleUpdate(BaseModel):
    """更新报警规则"""
    rule_name: Optional[str] = None
    description: Optional[str] = None
    device_code: Optional[str] = None
    field_code: Optional[str] = None
    field_name: Optional[str] = None
    threshold_config: Optional[dict] = None
    trigger_condition: Optional[dict] = None
    trigger_config: Optional[dict] = None
    alarm_level: Optional[str] = None
    notification_config: Optional[dict] = None
    is_enabled: Optional[bool] = None
    priority: Optional[int] = None


# =====================================================
# API 路由
# =====================================================

@router.get("", summary="获取报警规则列表")
async def get_alarm_rules(
    device_type_code: Optional[str] = Query(None, description="设备类型代码"),
    device_code: Optional[str] = Query(None, description="设备编码"),
    field_code: Optional[str] = Query(None, description="字段代码"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    pagination: dict = Depends(get_pagination_params)
):
    """获取报警规则列表"""
    try:
        query = AlarmRule.all()
        
        if device_type_code:
            query = query.filter(device_type_code=device_type_code)
        if device_code:
            query = query.filter(device_code=device_code)
        if field_code:
            query = query.filter(field_code=field_code)
        if is_enabled is not None:
            query = query.filter(is_enabled=is_enabled)
        if search:
            query = query.filter(rule_name__icontains=search)
        
        total = await query.count()
        rules = await query.offset(pagination["offset"]).limit(pagination["limit"]).order_by("-priority", "-created_at")
        
        # 转换为字典列表
        items = []
        for rule in rules:
            items.append({
                "id": rule.id,
                "rule_name": rule.rule_name,
                "rule_code": rule.rule_code,
                "description": rule.description,
                "device_type_code": rule.device_type_code,
                "device_code": rule.device_code,
                "field_code": rule.field_code,
                "field_name": rule.field_name,
                "threshold_config": rule.threshold_config,
                "trigger_condition": rule.trigger_condition,
                "trigger_config": rule.trigger_config,
                "alarm_level": rule.alarm_level,
                "notification_config": rule.notification_config,
                "is_enabled": rule.is_enabled,
                "priority": rule.priority,
                "created_at": rule.created_at.isoformat() if rule.created_at else None,
                "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
            })
        
        paginated = create_pagination_response(
            data=items,
            total=total,
            page=pagination["page"],
            page_size=pagination["page_size"]
        )
        
        formatter = create_formatter()
        return formatter.success(data=paginated, message=f"获取报警规则列表成功，共{total}条")
        
    except Exception as e:
        logger.error(f"获取报警规则列表失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message=f"获取报警规则列表失败: {str(e)}")


@router.get("/device-types", summary="获取可配置的设备类型列表")
async def get_device_types_for_rules():
    """获取可配置报警规则的设备类型列表"""
    try:
        # 从设备类型表获取
        device_types = await DeviceType.filter(is_active=True).all()
        
        items = [
            {
                "type_code": dt.type_code,
                "type_name": dt.type_name,
                "description": dt.description
            }
            for dt in device_types
        ]
        
        formatter = create_formatter()
        return formatter.success(data=items, message="获取设备类型列表成功")
        
    except Exception as e:
        logger.error(f"获取设备类型列表失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取设备类型列表失败")


@router.get("/fields/{device_type_code}", summary="获取设备类型的可监测字段")
async def get_fields_for_device_type(device_type_code: str):
    """获取指定设备类型的可监测字段列表"""
    try:
        fields = await DeviceField.filter(
            device_type_code=device_type_code,
            is_active=True,
            # is_monitoring_key=True, # 旧逻辑：仅监控字段
            # is_alarm_enabled=True     # 新逻辑：仅允许报警的字段 -> 暂时移除此限制，防止列表为空
        ).order_by("sort_order")
        
        items = [
            {
                "id": f.id,
                "field_code": f.field_code,
                "field_name": f.field_name,
                "field_type": f.field_type,
                "unit": f.unit,
                "data_range": f.data_range,
                "alarm_threshold": f.alarm_threshold,
                "is_monitoring_key": f.is_monitoring_key, # 返回此标志供前端参考
            }
            for f in fields
        ]
        
        formatter = create_formatter()
        return formatter.success(data=items, message="获取字段列表成功")
        
    except Exception as e:
        logger.error(f"获取字段列表失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取字段列表失败")


@router.get("/{rule_id}", summary="获取报警规则详情")
async def get_alarm_rule(rule_id: int):
    """获取报警规则详情"""
    try:
        rule = await AlarmRule.get_or_none(id=rule_id)
        if not rule:
            formatter = create_formatter()
            return formatter.error(message="报警规则不存在", code=404)
        
        data = {
            "id": rule.id,
            "rule_name": rule.rule_name,
            "rule_code": rule.rule_code,
            "description": rule.description,
            "device_type_code": rule.device_type_code,
            "device_code": rule.device_code,
            "field_code": rule.field_code,
            "field_name": rule.field_name,
            "threshold_config": rule.threshold_config,
            "trigger_condition": rule.trigger_condition,
            "trigger_config": rule.trigger_config,
            "alarm_level": rule.alarm_level,
            "notification_config": rule.notification_config,
            "is_enabled": rule.is_enabled,
            "priority": rule.priority,
            "created_at": rule.created_at.isoformat() if rule.created_at else None,
            "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
        }
        
        formatter = create_formatter()
        return formatter.success(data=data, message="获取报警规则详情成功")
        
    except Exception as e:
        logger.error(f"获取报警规则详情失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取报警规则详情失败")


@router.post("", summary="创建报警规则")
async def create_alarm_rule(rule_data: AlarmRuleCreate):
    """创建报警规则"""
    try:
        # 检查规则代码是否已存在
        existing = await AlarmRule.get_or_none(rule_code=rule_data.rule_code)
        if existing:
            formatter = create_formatter()
            return formatter.error(message=f"规则代码 {rule_data.rule_code} 已存在", code=400)
        
        # 创建规则
        rule = await AlarmRule.create(
            rule_name=rule_data.rule_name,
            rule_code=rule_data.rule_code,
            description=rule_data.description,
            device_type_code=rule_data.device_type_code,
            device_code=rule_data.device_code,
            field_code=rule_data.field_code,
            field_name=rule_data.field_name,
            threshold_config=rule_data.threshold_config,
            trigger_condition=rule_data.trigger_condition or {"consecutive_count": 1},
            trigger_config=rule_data.trigger_config,
            alarm_level=rule_data.alarm_level,
            notification_config=rule_data.notification_config or {"channels": ["websocket"]},
            is_enabled=rule_data.is_enabled,
            priority=rule_data.priority,
        )
        
        logger.info(f"创建报警规则成功: {rule.rule_code}")
        
        formatter = create_formatter()
        return formatter.success(
            data={"id": rule.id, "rule_code": rule.rule_code},
            message="创建报警规则成功"
        )
        
    except Exception as e:
        logger.error(f"创建报警规则失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="创建报警规则失败")


@router.put("/{rule_id}", summary="更新报警规则")
async def update_alarm_rule(rule_id: int, rule_data: AlarmRuleUpdate):
    """更新报警规则"""
    try:
        rule = await AlarmRule.get_or_none(id=rule_id)
        if not rule:
            formatter = create_formatter()
            return formatter.error(message="报警规则不存在", code=404)
        
        # 更新字段
        update_data = rule_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(rule, key, value)
        
        rule.updated_at = datetime.now()
        await rule.save()
        
        logger.info(f"更新报警规则成功: {rule.rule_code}")
        
        formatter = create_formatter()
        return formatter.success(data={"id": rule.id}, message="更新报警规则成功")
        
    except Exception as e:
        logger.error(f"更新报警规则失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="更新报警规则失败")


@router.delete("/{rule_id}", summary="删除报警规则")
async def delete_alarm_rule(rule_id: int):
    """删除报警规则"""
    try:
        rule = await AlarmRule.get_or_none(id=rule_id)
        if not rule:
            formatter = create_formatter()
            return formatter.error(message="报警规则不存在", code=404)
        
        rule_code = rule.rule_code
        await rule.delete()
        
        logger.info(f"删除报警规则成功: {rule_code}")
        
        formatter = create_formatter()
        return formatter.success(message="删除报警规则成功")
        
    except Exception as e:
        logger.error(f"删除报警规则失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="删除报警规则失败")


@router.put("/{rule_id}/toggle", summary="启用/禁用报警规则")
async def toggle_alarm_rule(rule_id: int):
    """切换报警规则的启用状态"""
    try:
        rule = await AlarmRule.get_or_none(id=rule_id)
        if not rule:
            formatter = create_formatter()
            return formatter.error(message="报警规则不存在", code=404)
        
        rule.is_enabled = not rule.is_enabled
        rule.updated_at = datetime.now()
        await rule.save()
        
        status = "启用" if rule.is_enabled else "禁用"
        logger.info(f"报警规则 {rule.rule_code} 已{status}")
        
        formatter = create_formatter()
        return formatter.success(
            data={"id": rule.id, "is_enabled": rule.is_enabled},
            message=f"报警规则已{status}"
        )
        
    except Exception as e:
        logger.error(f"切换报警规则状态失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="切换报警规则状态失败")


@router.post("/{rule_id}/test", summary="测试报警规则")
async def test_alarm_rule(rule_id: int, test_value: float = Query(..., description="测试值")):
    """测试报警规则是否会触发"""
    try:
        rule = await AlarmRule.get_or_none(id=rule_id)
        if not rule:
            formatter = create_formatter()
            return formatter.error(message="报警规则不存在", code=404)
        
        # 检测阈值
        result = check_threshold(rule.threshold_config, test_value)
        
        formatter = create_formatter()
        return formatter.success(
            data={
                "rule_code": rule.rule_code,
                "test_value": test_value,
                "threshold_config": rule.threshold_config,
                "triggered": result["triggered"],
                "level": result["level"],
                "message": result["message"]
            },
            message="测试完成"
        )
        
    except Exception as e:
        logger.error(f"测试报警规则失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="测试报警规则失败")


def check_threshold(config: dict, value: float) -> dict:
    """检测阈值"""
    threshold_type = config.get("type", "range")
    
    # 按严重程度从高到低检查
    for level in ["emergency", "critical", "warning"]:
        if level not in config:
            continue
            
        threshold = config[level]
        triggered = False
        message = ""
        
        if threshold_type == "range":
            min_val = threshold.get("min")
            max_val = threshold.get("max")
            if min_val is not None and value < min_val:
                triggered = True
                message = f"低于下限 {min_val}"
            elif max_val is not None and value > max_val:
                triggered = True
                message = f"超过上限 {max_val}"
                
        elif threshold_type == "upper":
            max_val = threshold.get("max")
            if max_val is not None and value > max_val:
                triggered = True
                message = f"超过上限 {max_val}"
                
        elif threshold_type == "lower":
            min_val = threshold.get("min")
            if min_val is not None and value < min_val:
                triggered = True
                message = f"低于下限 {min_val}"
        
        if triggered:
            return {"triggered": True, "level": level, "message": message}
    
    return {"triggered": False, "level": None, "message": "正常"}
