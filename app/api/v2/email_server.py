#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件服务器配置 API
"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel, EmailStr

from app.models.email import EmailServer
from app.core.response_formatter_v2 import create_formatter
from app.core.pagination import get_pagination_params, create_pagination_response
from app.log import logger

router = APIRouter(tags=["邮件服务器配置"])


class EmailServerCreate(BaseModel):
    name: str
    host: str
    port: int = 587
    username: Optional[str] = None
    password: Optional[str] = None
    encryption: str = "tls"
    from_email: str
    from_name: Optional[str] = None
    is_default: bool = False
    is_enabled: bool = True
    remark: Optional[str] = None


class EmailServerUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    encryption: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    is_default: Optional[bool] = None
    is_enabled: Optional[bool] = None
    remark: Optional[str] = None


@router.get("", summary="获取邮件服务器列表")
async def get_email_servers(
    search: Optional[str] = Query(None, description="搜索关键词"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    pagination: dict = Depends(get_pagination_params)
):
    """获取邮件服务器配置列表"""
    try:
        query = EmailServer.all()
        
        if search:
            query = query.filter(name__icontains=search)
        if is_enabled is not None:
            query = query.filter(is_enabled=is_enabled)
        
        total = await query.count()
        servers = await query.order_by("-is_default", "-id").offset(pagination["offset"]).limit(pagination["limit"])
        
        items = []
        for s in servers:
            items.append({
                "id": s.id,
                "name": s.name,
                "host": s.host,
                "port": s.port,
                "username": s.username,
                "encryption": s.encryption,
                "from_email": s.from_email,
                "from_name": s.from_name,
                "is_default": s.is_default,
                "is_enabled": s.is_enabled,
                "test_status": s.test_status,
                "last_test_time": s.last_test_time.isoformat() if s.last_test_time else None,
                "remark": s.remark,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            })
        
        paginated = create_pagination_response(
            data=items, total=total, page=pagination["page"], page_size=pagination["page_size"]
        )
        
        formatter = create_formatter()
        return formatter.success(data=paginated, message="获取成功")
        
    except Exception as e:
        logger.error(f"获取邮件服务器列表失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取失败")


@router.get("/{server_id}", summary="获取邮件服务器详情")
async def get_email_server(server_id: int):
    """获取邮件服务器配置详情"""
    try:
        server = await EmailServer.get_or_none(id=server_id)
        if not server:
            formatter = create_formatter()
            return formatter.error(message="服务器配置不存在", code=404)
        
        data = {
            "id": server.id,
            "name": server.name,
            "host": server.host,
            "port": server.port,
            "username": server.username,
            "encryption": server.encryption,
            "from_email": server.from_email,
            "from_name": server.from_name,
            "is_default": server.is_default,
            "is_enabled": server.is_enabled,
            "test_status": server.test_status,
            "last_test_time": server.last_test_time.isoformat() if server.last_test_time else None,
            "last_test_result": server.last_test_result,
            "remark": server.remark,
        }
        
        formatter = create_formatter()
        return formatter.success(data=data, message="获取成功")
        
    except Exception as e:
        logger.error(f"获取邮件服务器详情失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取失败")


@router.post("", summary="创建邮件服务器配置")
async def create_email_server(data: EmailServerCreate):
    """创建邮件服务器配置"""
    try:
        # 如果设为默认，取消其他默认
        if data.is_default:
            await EmailServer.filter(is_default=True).update(is_default=False)
        
        server = await EmailServer.create(**data.model_dump())
        
        formatter = create_formatter()
        return formatter.success(data={"id": server.id}, message="创建成功")
        
    except Exception as e:
        logger.error(f"创建邮件服务器失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="创建失败")


@router.put("/{server_id}", summary="更新邮件服务器配置")
async def update_email_server(server_id: int, data: EmailServerUpdate):
    """更新邮件服务器配置"""
    try:
        server = await EmailServer.get_or_none(id=server_id)
        if not server:
            formatter = create_formatter()
            return formatter.error(message="服务器配置不存在", code=404)
        
        update_data = data.model_dump(exclude_unset=True)
        
        # 如果设为默认，取消其他默认
        if update_data.get("is_default"):
            await EmailServer.filter(is_default=True).exclude(id=server_id).update(is_default=False)
        
        await EmailServer.filter(id=server_id).update(**update_data, updated_at=datetime.now())
        
        formatter = create_formatter()
        return formatter.success(message="更新成功")
        
    except Exception as e:
        logger.error(f"更新邮件服务器失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="更新失败")


@router.delete("/{server_id}", summary="删除邮件服务器配置")
async def delete_email_server(server_id: int):
    """删除邮件服务器配置"""
    try:
        server = await EmailServer.get_or_none(id=server_id)
        if not server:
            formatter = create_formatter()
            return formatter.error(message="服务器配置不存在", code=404)
        
        await server.delete()
        
        formatter = create_formatter()
        return formatter.success(message="删除成功")
        
    except Exception as e:
        logger.error(f"删除邮件服务器失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="删除失败")


@router.post("/{server_id}/test", summary="测试邮件服务器连接")
async def test_email_server(server_id: int, test_email: str = Query(..., description="测试收件邮箱")):
    """测试邮件服务器连接"""
    try:
        server = await EmailServer.get_or_none(id=server_id)
        if not server:
            formatter = create_formatter()
            return formatter.error(message="服务器配置不存在", code=404)
        
        # 尝试发送测试邮件
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        try:
            # 创建SMTP连接
            if server.encryption == "ssl":
                smtp = smtplib.SMTP_SSL(server.host, server.port, timeout=10)
            else:
                smtp = smtplib.SMTP(server.host, server.port, timeout=10)
                if server.encryption == "tls":
                    smtp.starttls()
            
            # 登录
            if server.username and server.password:
                smtp.login(server.username, server.password)
            
            # 发送测试邮件
            msg = MIMEMultipart()
            msg["From"] = f"{server.from_name} <{server.from_email}>" if server.from_name else server.from_email
            msg["To"] = test_email
            msg["Subject"] = "邮件服务器测试"
            msg.attach(MIMEText("这是一封测试邮件，如果您收到此邮件，说明邮件服务器配置正确。", "plain", "utf-8"))
            
            smtp.sendmail(server.from_email, [test_email], msg.as_string())
            smtp.quit()
            
            # 更新测试状态
            await EmailServer.filter(id=server_id).update(
                test_status="success",
                last_test_time=datetime.now(),
                last_test_result="测试成功"
            )
            
            formatter = create_formatter()
            return formatter.success(message="测试成功，邮件已发送")
            
        except Exception as smtp_error:
            error_msg = str(smtp_error)
            await EmailServer.filter(id=server_id).update(
                test_status="failed",
                last_test_time=datetime.now(),
                last_test_result=error_msg
            )
            
            formatter = create_formatter()
            return formatter.error(message=f"测试失败: {error_msg}")
        
    except Exception as e:
        logger.error(f"测试邮件服务器失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="测试失败")
