#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件模板 API
"""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel

from app.models.email import EmailTemplate
from app.core.response_formatter_v2 import create_formatter
from app.core.pagination import get_pagination_params, create_pagination_response
from app.log import logger

router = APIRouter(tags=["邮件模板"])


class TemplateVariable(BaseModel):
    name: str
    description: str
    example: Optional[str] = None


class EmailTemplateCreate(BaseModel):
    code: str
    name: str
    subject: str
    content: str
    variables: List[TemplateVariable] = []
    template_type: str = "custom"
    is_enabled: bool = True
    remark: Optional[str] = None


class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    variables: Optional[List[TemplateVariable]] = None
    template_type: Optional[str] = None
    is_enabled: Optional[bool] = None
    remark: Optional[str] = None


@router.get("", summary="获取邮件模板列表")
async def get_email_templates(
    search: Optional[str] = Query(None, description="搜索关键词"),
    template_type: Optional[str] = Query(None, description="模板类型"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    pagination: dict = Depends(get_pagination_params)
):
    """获取邮件模板列表"""
    try:
        query = EmailTemplate.all()
        
        if search:
            query = query.filter(name__icontains=search)
        if template_type:
            query = query.filter(template_type=template_type)
        if is_enabled is not None:
            query = query.filter(is_enabled=is_enabled)
        
        total = await query.count()
        templates = await query.order_by("-id").offset(pagination["offset"]).limit(pagination["limit"])
        
        items = []
        for t in templates:
            items.append({
                "id": t.id,
                "code": t.code,
                "name": t.name,
                "subject": t.subject,
                "template_type": t.template_type,
                "is_system": t.is_system,
                "is_enabled": t.is_enabled,
                "variables": t.variables,
                "remark": t.remark,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            })
        
        paginated = create_pagination_response(
            data=items, total=total, page=pagination["page"], page_size=pagination["page_size"]
        )
        
        formatter = create_formatter()
        return formatter.success(data=paginated, message="获取成功")
        
    except Exception as e:
        logger.error(f"获取邮件模板列表失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取失败")


@router.get("/types", summary="获取模板类型列表")
async def get_template_types():
    """获取模板类型列表"""
    types = [
        {"value": "alarm", "label": "报警通知"},
        {"value": "announcement", "label": "系统公告"},
        {"value": "task", "label": "任务提醒"},
        {"value": "custom", "label": "自定义"},
    ]
    formatter = create_formatter()
    return formatter.success(data=types, message="获取成功")


@router.get("/{template_id}", summary="获取邮件模板详情")
async def get_email_template(template_id: int):
    """获取邮件模板详情"""
    try:
        template = await EmailTemplate.get_or_none(id=template_id)
        if not template:
            formatter = create_formatter()
            return formatter.error(message="模板不存在", code=404)
        
        data = {
            "id": template.id,
            "code": template.code,
            "name": template.name,
            "subject": template.subject,
            "content": template.content,
            "variables": template.variables,
            "template_type": template.template_type,
            "is_system": template.is_system,
            "is_enabled": template.is_enabled,
            "remark": template.remark,
        }
        
        formatter = create_formatter()
        return formatter.success(data=data, message="获取成功")
        
    except Exception as e:
        logger.error(f"获取邮件模板详情失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取失败")


@router.post("", summary="创建邮件模板")
async def create_email_template(data: EmailTemplateCreate):
    """创建邮件模板"""
    try:
        # 检查code是否已存在
        existing = await EmailTemplate.get_or_none(code=data.code)
        if existing:
            formatter = create_formatter()
            return formatter.error(message="模板代码已存在")
        
        variables = [v.model_dump() for v in data.variables]
        template = await EmailTemplate.create(
            code=data.code,
            name=data.name,
            subject=data.subject,
            content=data.content,
            variables=variables,
            template_type=data.template_type,
            is_enabled=data.is_enabled,
            remark=data.remark
        )
        
        formatter = create_formatter()
        return formatter.success(data={"id": template.id}, message="创建成功")
        
    except Exception as e:
        logger.error(f"创建邮件模板失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="创建失败")


@router.put("/{template_id}", summary="更新邮件模板")
async def update_email_template(template_id: int, data: EmailTemplateUpdate):
    """更新邮件模板"""
    try:
        template = await EmailTemplate.get_or_none(id=template_id)
        if not template:
            formatter = create_formatter()
            return formatter.error(message="模板不存在", code=404)
        
        update_data = data.model_dump(exclude_unset=True)
        if "variables" in update_data and update_data["variables"]:
            update_data["variables"] = [v.model_dump() if hasattr(v, 'model_dump') else v for v in update_data["variables"]]
        
        await EmailTemplate.filter(id=template_id).update(**update_data, updated_at=datetime.now())
        
        formatter = create_formatter()
        return formatter.success(message="更新成功")
        
    except Exception as e:
        logger.error(f"更新邮件模板失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="更新失败")


@router.delete("/{template_id}", summary="删除邮件模板")
async def delete_email_template(template_id: int):
    """删除邮件模板"""
    try:
        template = await EmailTemplate.get_or_none(id=template_id)
        if not template:
            formatter = create_formatter()
            return formatter.error(message="模板不存在", code=404)
        
        if template.is_system:
            formatter = create_formatter()
            return formatter.error(message="系统预设模板不能删除")
        
        await template.delete()
        
        formatter = create_formatter()
        return formatter.success(message="删除成功")
        
    except Exception as e:
        logger.error(f"删除邮件模板失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="删除失败")


@router.post("/{template_id}/preview", summary="预览邮件模板")
async def preview_email_template(template_id: int, variables: dict = {}):
    """预览邮件模板（替换变量）"""
    try:
        template = await EmailTemplate.get_or_none(id=template_id)
        if not template:
            formatter = create_formatter()
            return formatter.error(message="模板不存在", code=404)
        
        # 替换变量
        subject = template.subject
        content = template.content
        
        for key, value in variables.items():
            subject = subject.replace(f"{{{{{key}}}}}", str(value))
            content = content.replace(f"{{{{{key}}}}}", str(value))
        
        data = {
            "subject": subject,
            "content": content,
        }
        
        formatter = create_formatter()
        return formatter.success(data=data, message="预览成功")
        
    except Exception as e:
        logger.error(f"预览邮件模板失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="预览失败")
