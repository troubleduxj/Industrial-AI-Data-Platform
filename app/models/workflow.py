#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流模型定义
支持设备监控、报警处理、数据采集、维护保养等业务流程
"""

from tortoise import fields
from app.models.base import BaseModel, TimestampMixin


class Workflow(TimestampMixin, BaseModel):
    """工作流定义模型"""
    
    # 基本信息
    name = fields.CharField(max_length=100, description="工作流名称")
    code = fields.CharField(max_length=50, unique=True, description="工作流代码")
    description = fields.TextField(null=True, description="工作流描述")
    
    # 分类信息
    type = fields.CharField(max_length=30, default="custom", description="工作流类型")
    # 类型: device_monitor(设备监控), alarm_process(报警处理), 
    #       data_collection(数据采集), maintenance(维护保养), custom(自定义)
    
    category = fields.CharField(max_length=50, null=True, description="工作流分类")
    priority = fields.CharField(max_length=20, default="medium", description="优先级")
    # 优先级: low, medium, high, urgent
    
    # 工作流定义（JSON格式存储节点和连接）
    nodes = fields.JSONField(default=list, description="节点定义")
    connections = fields.JSONField(default=list, description="连接定义")
    
    # 触发配置
    trigger_type = fields.CharField(max_length=30, default="manual", description="触发类型")
    # 触发类型: manual(手动), schedule(定时), event(事件), webhook(Webhook)
    trigger_config = fields.JSONField(default=dict, description="触发配置")
    
    # 执行配置
    execution_config = fields.JSONField(default=dict, description="执行配置")
    timeout_seconds = fields.IntField(default=3600, description="超时时间(秒)")
    retry_count = fields.IntField(default=0, description="重试次数")
    retry_interval = fields.IntField(default=60, description="重试间隔(秒)")
    
    # 通知配置
    notification_config = fields.JSONField(default=dict, description="通知配置")
    
    # 关联配置（可关联设备类型、报警规则等）
    related_device_types = fields.JSONField(default=list, description="关联设备类型")
    related_alarm_rules = fields.JSONField(default=list, description="关联报警规则")
    
    # 状态
    is_active = fields.BooleanField(default=True, description="是否启用")
    is_published = fields.BooleanField(default=False, description="是否已发布")
    version = fields.CharField(max_length=20, default="1.0.0", description="版本号")
    accent_color = fields.CharField(max_length=20, null=True, description="卡片强调色")
    
    # 统计信息
    execution_count = fields.IntField(default=0, description="执行次数")
    success_count = fields.IntField(default=0, description="成功次数")
    failure_count = fields.IntField(default=0, description="失败次数")
    last_executed_at = fields.DatetimeField(null=True, description="最后执行时间")
    
    # 创建/更新人
    created_by = fields.BigIntField(null=True, description="创建人ID")
    created_by_name = fields.CharField(max_length=50, null=True, description="创建人姓名")
    updated_by = fields.BigIntField(null=True, description="更新人ID")
    updated_by_name = fields.CharField(max_length=50, null=True, description="更新人姓名")
    published_by = fields.BigIntField(null=True, description="发布人ID")
    published_at = fields.DatetimeField(null=True, description="发布时间")
    
    class Meta:
        table = "t_sys_workflow"
        table_description = "工作流定义表"
        ordering = ["-created_at"]


class WorkflowExecution(TimestampMixin, BaseModel):
    """工作流执行记录模型"""
    
    # 关联工作流
    workflow = fields.ForeignKeyField(
        "models.Workflow",
        related_name="executions",
        on_delete=fields.CASCADE,
        description="关联工作流"
    )
    
    # 执行信息
    execution_id = fields.CharField(max_length=64, unique=True, description="执行ID")
    status = fields.CharField(max_length=20, default="pending", description="执行状态")
    # 状态: pending(待执行), running(执行中), success(成功), failed(失败), 
    #       cancelled(已取消), timeout(超时)
    
    # 触发信息
    trigger_type = fields.CharField(max_length=30, description="触发类型")
    trigger_data = fields.JSONField(null=True, description="触发数据")
    triggered_by = fields.BigIntField(null=True, description="触发人ID")
    triggered_by_name = fields.CharField(max_length=50, null=True, description="触发人姓名")
    
    # 执行时间
    started_at = fields.DatetimeField(null=True, description="开始时间")
    completed_at = fields.DatetimeField(null=True, description="完成时间")
    duration_ms = fields.IntField(null=True, description="执行时长(毫秒)")
    
    # 执行结果
    result = fields.JSONField(null=True, description="执行结果")
    error_message = fields.TextField(null=True, description="错误信息")
    error_stack = fields.TextField(null=True, description="错误堆栈")
    
    # 节点执行状态
    node_states = fields.JSONField(default=dict, description="节点执行状态")
    current_node_id = fields.CharField(max_length=64, null=True, description="当前节点ID")
    
    # 上下文数据
    context = fields.JSONField(default=dict, description="执行上下文")
    variables = fields.JSONField(default=dict, description="变量数据")
    
    # 重试信息
    retry_count = fields.IntField(default=0, description="已重试次数")
    parent_execution_id = fields.CharField(max_length=64, null=True, description="父执行ID(重试时)")
    
    class Meta:
        table = "t_sys_workflow_execution"
        table_description = "工作流执行记录表"
        ordering = ["-created_at"]


class WorkflowNodeExecution(TimestampMixin, BaseModel):
    """工作流节点执行记录模型"""
    
    # 关联执行记录
    execution = fields.ForeignKeyField(
        "models.WorkflowExecution",
        related_name="node_executions",
        on_delete=fields.CASCADE,
        description="关联执行记录"
    )
    
    # 节点信息
    node_id = fields.CharField(max_length=64, description="节点ID")
    node_type = fields.CharField(max_length=30, description="节点类型")
    node_name = fields.CharField(max_length=100, null=True, description="节点名称")
    
    # 执行状态
    status = fields.CharField(max_length=20, default="pending", description="执行状态")
    # 状态: pending, running, success, failed, skipped
    
    # 执行时间
    started_at = fields.DatetimeField(null=True, description="开始时间")
    completed_at = fields.DatetimeField(null=True, description="完成时间")
    duration_ms = fields.IntField(null=True, description="执行时长(毫秒)")
    
    # 输入输出
    input_data = fields.JSONField(null=True, description="输入数据")
    output_data = fields.JSONField(null=True, description="输出数据")
    
    # 错误信息
    error_message = fields.TextField(null=True, description="错误信息")
    error_details = fields.JSONField(null=True, description="错误详情")
    
    # 重试信息
    retry_count = fields.IntField(default=0, description="重试次数")
    
    class Meta:
        table = "t_sys_workflow_node_execution"
        table_description = "工作流节点执行记录表"
        ordering = ["created_at"]


class WorkflowTemplate(TimestampMixin, BaseModel):
    """工作流模板模型"""
    
    # 基本信息
    name = fields.CharField(max_length=100, description="模板名称")
    code = fields.CharField(max_length=50, unique=True, description="模板代码")
    description = fields.TextField(null=True, description="模板描述")
    
    # 分类
    type = fields.CharField(max_length=30, description="模板类型")
    category = fields.CharField(max_length=50, null=True, description="模板分类")
    
    # 模板定义
    nodes = fields.JSONField(default=list, description="节点定义")
    connections = fields.JSONField(default=list, description="连接定义")
    default_config = fields.JSONField(default=dict, description="默认配置")
    
    # 状态
    is_active = fields.BooleanField(default=True, description="是否启用")
    is_system = fields.BooleanField(default=False, description="是否系统模板")
    
    # 使用统计
    usage_count = fields.IntField(default=0, description="使用次数")
    
    class Meta:
        table = "t_sys_workflow_template"
        table_description = "工作流模板表"
        ordering = ["-created_at"]


class WorkflowVersion(TimestampMixin, BaseModel):
    """工作流版本历史模型"""
    
    # 关联工作流
    workflow = fields.ForeignKeyField(
        "models.Workflow",
        related_name="versions",
        on_delete=fields.CASCADE,
        description="关联工作流"
    )
    
    # 版本信息
    version = fields.CharField(max_length=20, description="版本号")
    version_name = fields.CharField(max_length=100, null=True, description="版本名称")
    description = fields.TextField(null=True, description="版本描述")
    
    # 工作流快照
    snapshot = fields.JSONField(description="工作流快照")
    # 快照包含: name, description, nodes, connections, trigger_config, execution_config等
    
    # 变更信息
    change_type = fields.CharField(max_length=20, default="update", description="变更类型")
    # 类型: create(创建), update(更新), publish(发布), rollback(回滚)
    change_summary = fields.TextField(null=True, description="变更摘要")
    
    # 状态
    is_published = fields.BooleanField(default=False, description="是否为发布版本")
    is_current = fields.BooleanField(default=False, description="是否为当前版本")
    
    # 创建人
    created_by = fields.BigIntField(null=True, description="创建人ID")
    created_by_name = fields.CharField(max_length=50, null=True, description="创建人姓名")
    
    class Meta:
        table = "t_sys_workflow_version"
        table_description = "工作流版本历史表"
        ordering = ["-created_at"]


class WorkflowSchedule(TimestampMixin, BaseModel):
    """工作流调度配置模型"""
    
    # 关联工作流
    workflow = fields.ForeignKeyField(
        "models.Workflow",
        related_name="schedules",
        on_delete=fields.CASCADE,
        description="关联工作流"
    )
    
    # 基本信息
    name = fields.CharField(max_length=100, null=True, description="调度名称")
    description = fields.TextField(null=True, description="调度描述")
    
    # 调度配置
    schedule_type = fields.CharField(max_length=20, description="调度类型")
    # 类型: cron(Cron表达式), interval(固定间隔), once(单次执行), 
    #       daily(每日), weekly(每周), monthly(每月)
    
    schedule_config = fields.JSONField(default=dict, description="调度配置")
    # 配置示例:
    # cron: {"cron_expression": "0 0 * * *"}
    # interval: {"interval_value": 1, "interval_unit": "hours"}
    # once: {"run_at": "2024-01-01T00:00:00"}
    # daily: {"hour": 8, "minute": 0}
    # weekly: {"day_of_week": "mon", "hour": 8, "minute": 0}
    # monthly: {"day": 1, "hour": 8, "minute": 0}
    
    # 时间范围
    start_time = fields.DatetimeField(null=True, description="开始时间")
    end_time = fields.DatetimeField(null=True, description="结束时间")
    
    # 状态
    is_active = fields.BooleanField(default=True, description="是否启用")
    
    # 执行统计
    run_count = fields.IntField(default=0, description="执行次数")
    success_count = fields.IntField(default=0, description="成功次数")
    failure_count = fields.IntField(default=0, description="失败次数")
    last_run_at = fields.DatetimeField(null=True, description="最后执行时间")
    next_run_at = fields.DatetimeField(null=True, description="下次执行时间")
    
    # 创建人
    created_by = fields.BigIntField(null=True, description="创建人ID")
    created_by_name = fields.CharField(max_length=50, null=True, description="创建人姓名")
    
    class Meta:
        table = "t_sys_workflow_schedule"
        table_description = "工作流调度配置表"
        ordering = ["-created_at"]
