#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件相关模型
"""

from tortoise import fields
from tortoise.models import Model


class EmailServer(Model):
    """邮件服务器配置"""
    
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, description="配置名称")
    host = fields.CharField(max_length=255, description="SMTP服务器地址")
    port = fields.IntField(default=587, description="端口号")
    username = fields.CharField(max_length=255, null=True, description="用户名")
    password = fields.CharField(max_length=255, null=True, description="密码")
    encryption = fields.CharField(max_length=20, default="tls", description="加密方式")
    from_email = fields.CharField(max_length=255, description="发件人邮箱")
    from_name = fields.CharField(max_length=100, null=True, description="发件人名称")
    is_default = fields.BooleanField(default=False, description="是否默认")
    is_enabled = fields.BooleanField(default=True, description="是否启用")
    test_status = fields.CharField(max_length=20, default="untested", description="测试状态")
    last_test_time = fields.DatetimeField(null=True, description="最后测试时间")
    last_test_result = fields.TextField(null=True, description="测试结果")
    remark = fields.TextField(null=True, description="备注")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    created_by = fields.IntField(null=True)
    updated_by = fields.IntField(null=True)
    
    class Meta:
        table = "t_sys_email_server"
        table_description = "邮件服务器配置表"


class EmailTemplate(Model):
    """邮件模板"""
    
    id = fields.IntField(pk=True)
    code = fields.CharField(max_length=50, unique=True, description="模板代码")
    name = fields.CharField(max_length=100, description="模板名称")
    subject = fields.CharField(max_length=255, description="邮件主题")
    content = fields.TextField(description="邮件内容")
    variables = fields.JSONField(default=list, description="可用变量")
    template_type = fields.CharField(max_length=50, default="custom", description="模板类型")
    is_system = fields.BooleanField(default=False, description="是否系统预设")
    is_enabled = fields.BooleanField(default=True, description="是否启用")
    remark = fields.TextField(null=True, description="备注")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    created_by = fields.IntField(null=True)
    updated_by = fields.IntField(null=True)
    
    class Meta:
        table = "t_sys_email_template"
        table_description = "邮件模板表"


class NotificationConfig(Model):
    """通知发送配置"""
    
    id = fields.IntField(pk=True)
    notification_type = fields.CharField(max_length=50, unique=True, description="通知类型")
    type_name = fields.CharField(max_length=100, description="类型名称")
    channels = fields.JSONField(default=dict, description="发送渠道")
    email_template_id = fields.IntField(null=True, description="邮件模板ID")
    retry_config = fields.JSONField(default=dict, description="重试配置")
    rate_limit = fields.JSONField(default=dict, description="频率限制")
    silent_period = fields.JSONField(default=dict, description="静默时段")
    is_enabled = fields.BooleanField(default=True, description="是否启用")
    remark = fields.TextField(null=True, description="备注")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "t_sys_notification_config"
        table_description = "通知发送配置表"


class EmailLog(Model):
    """邮件发送记录"""
    
    id = fields.IntField(pk=True)
    notification_id = fields.IntField(null=True, description="通知ID")
    template_id = fields.IntField(null=True, description="模板ID")
    server_id = fields.IntField(null=True, description="服务器ID")
    to_email = fields.CharField(max_length=255, description="收件人邮箱")
    to_name = fields.CharField(max_length=100, null=True, description="收件人名称")
    subject = fields.CharField(max_length=255, description="邮件主题")
    content = fields.TextField(null=True, description="邮件内容")
    status = fields.CharField(max_length=20, default="pending", description="发送状态")
    retry_count = fields.IntField(default=0, description="重试次数")
    error_message = fields.TextField(null=True, description="错误信息")
    sent_at = fields.DatetimeField(null=True, description="发送时间")
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "t_sys_email_log"
        table_description = "邮件发送记录表"
