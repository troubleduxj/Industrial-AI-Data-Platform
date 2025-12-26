#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流 Pydantic 模型定义
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# =====================================================
# 节点相关模型
# =====================================================

class WorkflowNodeBase(BaseModel):
    """工作流节点基础模型"""
    id: str = Field(..., description="节点ID")
    type: str = Field(..., description="节点类型")
    name: str = Field(..., description="节点名称")
    x: float = Field(0, description="X坐标")
    y: float = Field(0, description="Y坐标")
    description: Optional[str] = Field(None, description="节点描述")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="节点属性")


class WorkflowConnectionBase(BaseModel):
    """工作流连接基础模型"""
    id: str = Field(..., description="连接ID")
    from_node_id: str = Field(..., alias="fromNodeId", description="源节点ID")
    to_node_id: str = Field(..., alias="toNodeId", description="目标节点ID")
    from_connector_id: Optional[str] = Field(None, alias="fromConnectorId", description="源连接点ID")
    to_connector_id: Optional[str] = Field(None, alias="toConnectorId", description="目标连接点ID")
    label: Optional[str] = Field(None, description="连接标签")
    condition: Optional[str] = Field(None, description="条件表达式")
    
    class Config:
        populate_by_name = True


# =====================================================
# 触发配置模型
# =====================================================

class TriggerConfig(BaseModel):
    """触发配置"""
    # 事件触发
    event_type: Optional[str] = Field(None, description="事件类型")
    event_source: Optional[str] = Field(None, description="事件来源")
    event_filter: Optional[Dict[str, Any]] = Field(None, description="事件过滤条件")
    
    # 定时触发
    cron_expression: Optional[str] = Field(None, description="Cron表达式")
    interval_seconds: Optional[int] = Field(None, description="间隔秒数")
    
    # Webhook触发
    webhook_path: Optional[str] = Field(None, description="Webhook路径")
    webhook_secret: Optional[str] = Field(None, description="Webhook密钥")


class ExecutionConfig(BaseModel):
    """执行配置"""
    timeout_seconds: int = Field(3600, description="超时时间(秒)")
    retry_count: int = Field(0, description="重试次数")
    retry_interval: int = Field(60, description="重试间隔(秒)")
    parallel_limit: int = Field(1, description="并行执行限制")
    error_handling: str = Field("stop", description="错误处理方式: stop/continue/retry")


class NotificationConfig(BaseModel):
    """通知配置"""
    on_start: bool = Field(False, description="开始时通知")
    on_success: bool = Field(True, description="成功时通知")
    on_failure: bool = Field(True, description="失败时通知")
    channels: List[str] = Field(default_factory=lambda: ["websocket"], description="通知渠道")
    recipients: Optional[List[int]] = Field(None, description="接收人ID列表")


# =====================================================
# 工作流CRUD模型
# =====================================================

class WorkflowCreate(BaseModel):
    """创建工作流"""
    name: str = Field(..., min_length=1, max_length=100, description="工作流名称")
    code: Optional[str] = Field(None, max_length=50, description="工作流代码(自动生成)")
    description: Optional[str] = Field(None, description="工作流描述")
    type: str = Field("custom", description="工作流类型")
    category: Optional[str] = Field(None, description="工作流分类")
    priority: str = Field("medium", description="优先级")
    
    nodes: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="节点定义")
    connections: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="连接定义")
    
    trigger_type: str = Field("manual", description="触发类型")
    trigger_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="触发配置")
    execution_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="执行配置")
    notification_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="通知配置")
    
    related_device_types: Optional[List[str]] = Field(default_factory=list, description="关联设备类型")
    related_alarm_rules: Optional[List[int]] = Field(default_factory=list, description="关联报警规则ID")
    
    is_active: bool = Field(True, description="是否启用")
    accent_color: Optional[str] = Field(None, description="卡片强调色(HEX)")


class WorkflowUpdate(BaseModel):
    """更新工作流"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    type: Optional[str] = Field(None, description="工作流类型")
    category: Optional[str] = Field(None, description="工作流分类")
    priority: Optional[str] = Field(None, description="优先级")
    
    nodes: Optional[List[Dict[str, Any]]] = Field(None, description="节点定义")
    connections: Optional[List[Dict[str, Any]]] = Field(None, description="连接定义")
    
    trigger_type: Optional[str] = Field(None, description="触发类型")
    trigger_config: Optional[Dict[str, Any]] = Field(None, description="触发配置")
    execution_config: Optional[Dict[str, Any]] = Field(None, description="执行配置")
    notification_config: Optional[Dict[str, Any]] = Field(None, description="通知配置")
    
    related_device_types: Optional[List[str]] = Field(None, description="关联设备类型")
    related_alarm_rules: Optional[List[int]] = Field(None, description="关联报警规则ID")
    
    is_active: Optional[bool] = Field(None, description="是否启用")
    accent_color: Optional[str] = Field(None, description="卡片强调色(HEX)")


class WorkflowDesignSave(BaseModel):
    """保存工作流设计"""
    nodes: List[Dict[str, Any]] = Field(..., description="节点定义")
    connections: List[Dict[str, Any]] = Field(..., description="连接定义")
    canvas_state: Optional[Dict[str, Any]] = Field(None, description="画布状态")


class WorkflowResponse(BaseModel):
    """工作流响应模型"""
    id: int
    name: str
    code: str
    description: Optional[str]
    type: str
    category: Optional[str]
    priority: str
    
    nodes: List[Dict[str, Any]]
    connections: List[Dict[str, Any]]
    
    trigger_type: str
    trigger_config: Dict[str, Any]
    execution_config: Dict[str, Any]
    notification_config: Dict[str, Any]
    
    related_device_types: List[str]
    related_alarm_rules: List[int]
    
    is_active: bool
    is_published: bool
    version: str
    accent_color: Optional[str]
    
    execution_count: int
    success_count: int
    failure_count: int
    last_executed_at: Optional[datetime]
    
    created_by: Optional[int]
    created_by_name: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# =====================================================
# 执行相关模型
# =====================================================

class WorkflowExecuteRequest(BaseModel):
    """执行工作流请求"""
    trigger_data: Optional[Dict[str, Any]] = Field(None, description="触发数据")
    variables: Optional[Dict[str, Any]] = Field(None, description="初始变量")
    async_mode: bool = Field(True, description="是否异步执行")


class WorkflowExecutionResponse(BaseModel):
    """工作流执行响应"""
    execution_id: str
    workflow_id: int
    workflow_name: str
    status: str
    trigger_type: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True


class NodeExecutionResponse(BaseModel):
    """节点执行响应"""
    node_id: str
    node_type: str
    node_name: Optional[str]
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True


# =====================================================
# 模板相关模型
# =====================================================

class WorkflowTemplateCreate(BaseModel):
    """创建工作流模板"""
    name: str = Field(..., description="模板名称")
    code: Optional[str] = Field(None, description="模板代码")
    description: Optional[str] = Field(None, description="模板描述")
    type: str = Field(..., description="模板类型")
    category: Optional[str] = Field(None, description="模板分类")
    nodes: List[Dict[str, Any]] = Field(default_factory=list, description="节点定义")
    connections: List[Dict[str, Any]] = Field(default_factory=list, description="连接定义")
    default_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="默认配置")


class WorkflowTemplateResponse(BaseModel):
    """工作流模板响应"""
    id: int
    name: str
    code: str
    description: Optional[str]
    type: str
    category: Optional[str]
    nodes: List[Dict[str, Any]]
    connections: List[Dict[str, Any]]
    default_config: Dict[str, Any]
    is_active: bool
    is_system: bool
    usage_count: int
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# =====================================================
# 调度相关模型
# =====================================================

class WorkflowScheduleCreate(BaseModel):
    """创建工作流调度"""
    workflow_id: int = Field(..., description="工作流ID")
    schedule_type: str = Field(..., description="调度类型: cron/interval/once")
    cron_expression: Optional[str] = Field(None, description="Cron表达式")
    interval_seconds: Optional[int] = Field(None, description="间隔秒数")
    execute_at: Optional[datetime] = Field(None, description="执行时间(单次)")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    is_active: bool = Field(True, description="是否启用")


class WorkflowScheduleResponse(BaseModel):
    """工作流调度响应"""
    id: int
    workflow_id: int
    schedule_type: str
    cron_expression: Optional[str]
    interval_seconds: Optional[int]
    execute_at: Optional[datetime]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    is_active: bool
    last_executed_at: Optional[datetime]
    next_execute_at: Optional[datetime]
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# =====================================================
# 统计相关模型
# =====================================================

class WorkflowStats(BaseModel):
    """工作流统计"""
    total_workflows: int = Field(0, description="工作流总数")
    active_workflows: int = Field(0, description="启用的工作流数")
    published_workflows: int = Field(0, description="已发布的工作流数")
    total_executions: int = Field(0, description="总执行次数")
    success_executions: int = Field(0, description="成功执行次数")
    failed_executions: int = Field(0, description="失败执行次数")
    running_executions: int = Field(0, description="正在执行数")
    by_type: Dict[str, int] = Field(default_factory=dict, description="按类型统计")
    by_priority: Dict[str, int] = Field(default_factory=dict, description="按优先级统计")


class WorkflowValidationResult(BaseModel):
    """工作流验证结果"""
    is_valid: bool = Field(..., description="是否有效")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")
    node_count: int = Field(0, description="节点数量")
    connection_count: int = Field(0, description="连接数量")
    has_start_node: bool = Field(False, description="是否有开始节点")
    has_end_node: bool = Field(False, description="是否有结束节点")
