"""
权限审计日志数据模型
"""
from datetime import datetime
from typing import Optional, Dict, Any
from tortoise import fields
from .base import BaseModel, TimestampMixin


class AuditLog(TimestampMixin, BaseModel):
    """权限审计日志模型"""
    
    # 用户信息
    user_id = fields.IntField(null=True, description="用户ID", index=True)
    username = fields.CharField(max_length=50, null=True, description="用户名", index=True)
    user_ip = fields.CharField(max_length=45, null=True, description="用户IP地址")
    user_agent = fields.CharField(max_length=500, null=True, description="用户代理")
    
    # 操作信息
    action_type = fields.CharField(max_length=50, description="操作类型", index=True)
    action_name = fields.CharField(max_length=100, null=True, description="操作名称")
    resource_type = fields.CharField(max_length=50, null=True, description="资源类型")
    resource_id = fields.CharField(max_length=100, null=True, description="资源ID")
    
    # 权限信息
    permission_code = fields.CharField(max_length=100, null=True, description="权限代码")
    permission_result = fields.BooleanField(null=True, description="权限验证结果")
    
    # 请求信息
    request_method = fields.CharField(max_length=10, null=True, description="请求方法")
    request_path = fields.CharField(max_length=500, null=True, description="请求路径")
    request_params = fields.JSONField(null=True, description="请求参数")
    
    # 响应信息
    response_status = fields.IntField(null=True, description="响应状态码")
    response_message = fields.TextField(null=True, description="响应消息")
    
    # 额外信息
    extra_data = fields.JSONField(null=True, description="额外数据")
    risk_level = fields.CharField(max_length=20, default="LOW", description="风险等级")
    
    # 时间信息
    duration_ms = fields.IntField(null=True, description="处理时长(毫秒)")
    
    class Meta:
        table = "audit_logs"
        table_description = "权限审计日志表"
    
    def __str__(self):
        return f"<AuditLog(id={self.id}, user={self.username}, action={self.action_type})>"


class SecurityEvent(TimestampMixin, BaseModel):
    """安全事件模型"""
    
    # 事件信息
    event_type = fields.CharField(max_length=50, description="事件类型", index=True)
    event_level = fields.CharField(max_length=20, description="事件级别", index=True)
    event_title = fields.CharField(max_length=200, description="事件标题")
    event_description = fields.TextField(null=True, description="事件描述")
    
    # 用户信息
    user_id = fields.IntField(null=True, description="用户ID", index=True)
    username = fields.CharField(max_length=50, null=True, description="用户名")
    user_ip = fields.CharField(max_length=45, null=True, description="用户IP地址")
    
    # 请求信息
    request_path = fields.CharField(max_length=500, null=True, description="请求路径")
    request_method = fields.CharField(max_length=10, null=True, description="请求方法")
    
    # 检测信息
    detection_rule = fields.CharField(max_length=100, null=True, description="检测规则")
    threat_score = fields.IntField(default=0, description="威胁评分")
    
    # 处理状态
    status = fields.CharField(max_length=20, default="PENDING", description="处理状态")
    handled_by = fields.IntField(null=True, description="处理人ID")
    handled_at = fields.DatetimeField(null=True, description="处理时间")
    handle_note = fields.TextField(null=True, description="处理备注")
    
    # 额外信息
    extra_data = fields.JSONField(null=True, description="额外数据")
    
    class Meta:
        table = "security_events"
        table_description = "安全事件表"
    
    def __str__(self):
        return f"<SecurityEvent(id={self.id}, type={self.event_type}, level={self.event_level})>"