#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报警规则和报警记录模型
"""

from tortoise import fields
from app.models.base import BaseModel, TimestampMixin


class AlarmRule(TimestampMixin, BaseModel):
    """报警规则模型"""
    
    # 基本信息
    rule_name = fields.CharField(max_length=100, description="规则名称")
    rule_code = fields.CharField(max_length=50, unique=True, description="规则代码")
    description = fields.TextField(null=True, description="规则描述")
    
    # 关联信息
    device_type_code = fields.CharField(max_length=50, description="设备类型代码")
    device_code = fields.CharField(max_length=64, null=True, description="关联设备编码，为空则为通用规则")
    device_field_id = fields.BigIntField(null=True, description="关联的设备字段ID")
    field_code = fields.CharField(max_length=50, description="监测字段代码")
    field_name = fields.CharField(max_length=100, null=True, description="字段名称")
    
    # 阈值配置
    threshold_config = fields.JSONField(default=dict, description="阈值配置")
    
    # 触发条件
    trigger_condition = fields.JSONField(default=dict, description="触发条件配置")
    trigger_config = fields.JSONField(null=True, description="高级触发配置")
    
    # 报警级别
    alarm_level = fields.CharField(max_length=20, default="warning", description="默认报警级别")
    
    # 通知配置
    notification_config = fields.JSONField(default=dict, description="通知配置")
    
    # 状态
    is_enabled = fields.BooleanField(default=True, description="是否启用")
    priority = fields.IntField(default=0, description="优先级")
    
    # 创建/更新人
    created_by = fields.BigIntField(null=True, description="创建人ID")
    updated_by = fields.BigIntField(null=True, description="更新人ID")
    
    class Meta:
        table = "t_alarm_rule"
        table_description = "报警规则配置表"
        ordering = ["-priority", "-created_at"]


class AlarmRecord(TimestampMixin, BaseModel):
    """报警记录模型"""
    
    # 关联信息
    rule = fields.ForeignKeyField(
        "models.AlarmRule", 
        related_name="records", 
        null=True,
        on_delete=fields.SET_NULL,
        description="关联规则"
    )
    device_id = fields.BigIntField(null=True, description="设备ID")
    device_code = fields.CharField(max_length=64, description="设备编码")
    device_name = fields.CharField(max_length=100, null=True, description="设备名称")
    device_type_code = fields.CharField(max_length=50, null=True, description="设备类型")
    
    # 报警信息
    alarm_code = fields.CharField(max_length=50, description="报警代码")
    alarm_level = fields.CharField(max_length=20, description="报警级别")
    alarm_title = fields.CharField(max_length=200, description="报警标题")
    alarm_content = fields.TextField(null=True, description="报警内容")
    
    # 触发数据
    field_code = fields.CharField(max_length=50, null=True, description="触发字段")
    field_name = fields.CharField(max_length=100, null=True, description="字段名称")
    trigger_value = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="触发值")
    threshold_value = fields.JSONField(null=True, description="阈值配置")
    
    # 时间信息
    triggered_at = fields.DatetimeField(description="触发时间")
    last_triggered_at = fields.DatetimeField(null=True, description="最近一次触发时间")
    recovered_at = fields.DatetimeField(null=True, description="恢复时间")
    duration_seconds = fields.IntField(null=True, description="持续时间(秒)")
    trigger_count = fields.IntField(default=1, description="触发次数")
    
    # 处理信息
    status = fields.CharField(max_length=20, default="active", description="状态")
    acknowledged_at = fields.DatetimeField(null=True, description="确认时间")
    acknowledged_by = fields.BigIntField(null=True, description="确认人ID")
    acknowledged_by_name = fields.CharField(max_length=50, null=True, description="确认人姓名")
    resolved_at = fields.DatetimeField(null=True, description="解决时间")
    resolved_by = fields.BigIntField(null=True, description="解决人ID")
    resolved_by_name = fields.CharField(max_length=50, null=True, description="解决人姓名")
    resolution_notes = fields.TextField(null=True, description="解决备注")
    
    # 通知状态
    notification_sent = fields.BooleanField(default=False, description="是否已发送通知")
    notification_channels = fields.JSONField(null=True, description="已通知渠道")
    
    class Meta:
        table = "t_alarm_record"
        table_description = "报警记录表"
        ordering = ["-triggered_at"]
