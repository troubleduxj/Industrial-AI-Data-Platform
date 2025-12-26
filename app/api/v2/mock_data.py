"""
Mock数据管理API
用于模拟API响应，方便系统演示和测试
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query
from tortoise.expressions import Q

from app.core.dependency import DependAuth
from app.core.response_formatter_v2 import ResponseFormatterV2
from app.models.admin import MockData, User
from app.schemas.mock_data import (
    MockDataCreate,
    MockDataUpdate,
    MockDataResponse,
    MockDataListResponse,
    MockDataToggleRequest,
    MockDataBatchDeleteRequest
)
from app.log import logger


router = APIRouter(prefix="/mock-data", tags=["Mock数据管理"])
formatter = ResponseFormatterV2()


@router.get("", summary="获取Mock数据列表", response_model=dict)
async def get_mock_data_list(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词(名称/URL)"),
    method: Optional[str] = Query(None, description="HTTP方法筛选"),
    enabled: Optional[bool] = Query(None, description="启用状态筛选"),
    current_user: User = DependAuth
):
    """
    获取Mock数据列表，支持分页和筛选
    """
    try:
        # 构建查询条件
        query = MockData.all()
        
        if keyword:
            query = query.filter(
                Q(name__icontains=keyword) | Q(url_pattern__icontains=keyword)
            )
        
        if method:
            query = query.filter(method=method.upper())
        
        if enabled is not None:
            query = query.filter(enabled=enabled)
        
        # 按优先级和创建时间排序
        query = query.order_by('-priority', '-created_at')
        
        # 分页
        total = await query.count()
        offset = (page - 1) * page_size
        items = await query.offset(offset).limit(page_size)
        
        # 转换为响应模型
        items_data = [MockDataResponse.model_validate(item) for item in items]
        
        return formatter.success(
            data={
                "items": [item.model_dump() for item in items_data],
                "total": total,
                "page": page,
                "page_size": page_size
            },
            message="获取Mock数据列表成功"
        )
        
    except Exception as e:
        logger.error(f"获取Mock数据列表失败: {str(e)}")
        return formatter.error(message=f"获取Mock数据列表失败: {str(e)}")


@router.get("/{mock_id}", summary="获取Mock数据详情", response_model=dict)
async def get_mock_data_detail(
    mock_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """
    获取指定Mock数据的详细信息
    """
    try:
        mock_data = await MockData.get_or_none(id=mock_id)
        
        if not mock_data:
            return formatter.error(message="Mock数据不存在", code=404)
        
        data = MockDataResponse.model_validate(mock_data)
        
        return formatter.success(
            data=data.model_dump(),
            message="获取Mock数据详情成功"
        )
        
    except Exception as e:
        logger.error(f"获取Mock数据详情失败: {str(e)}")
        return formatter.error(message=f"获取Mock数据详情失败: {str(e)}")


@router.post("", summary="创建Mock数据", response_model=dict)
async def create_mock_data(
    mock_create: MockDataCreate,
    request: Request,
    current_user: User = DependAuth
):
    """
    创建新的Mock数据规则
    """
    try:
        # 检查是否已存在相同的Mock规则
        existing = await MockData.filter(
            method=mock_create.method,
            url_pattern=mock_create.url_pattern
        ).first()
        
        if existing:
            return formatter.error(
                message=f"已存在相同的Mock规则: {mock_create.method} {mock_create.url_pattern}"
            )
        
        # 创建Mock数据
        mock_data = await MockData.create(
            **mock_create.model_dump(),
            creator_id=current_user.id,
            creator_name=current_user.username
        )
        
        data = MockDataResponse.model_validate(mock_data)
        
        logger.info(f"用户 {current_user.username} 创建Mock规则: {mock_create.name}")
        
        return formatter.success(
            data=data.model_dump(),
            message="创建Mock数据成功"
        )
        
    except Exception as e:
        logger.error(f"创建Mock数据失败: {str(e)}")
        return formatter.error(message=f"创建Mock数据失败: {str(e)}")


@router.put("/{mock_id}", summary="更新Mock数据", response_model=dict)
async def update_mock_data(
    mock_id: int,
    mock_update: MockDataUpdate,
    request: Request,
    current_user: User = DependAuth
):
    """
    更新指定的Mock数据规则
    """
    try:
        mock_data = await MockData.get_or_none(id=mock_id)
        
        if not mock_data:
            return formatter.error(message="Mock数据不存在", code=404)
        
        # 如果更新了method或url_pattern，检查是否与其他规则冲突
        if mock_update.method or mock_update.url_pattern:
            check_method = mock_update.method or mock_data.method
            check_url = mock_update.url_pattern or mock_data.url_pattern
            
            existing = await MockData.filter(
                method=check_method,
                url_pattern=check_url
            ).exclude(id=mock_id).first()
            
            if existing:
                return formatter.error(
                    message=f"已存在相同的Mock规则: {check_method} {check_url}"
                )
        
        # 更新字段
        update_data = mock_update.model_dump(exclude_unset=True)
        await mock_data.update_from_dict(update_data)
        await mock_data.save()
        
        data = MockDataResponse.model_validate(mock_data)
        
        logger.info(f"用户 {current_user.username} 更新Mock规则: {mock_data.name}")
        
        return formatter.success(
            data=data.model_dump(),
            message="更新Mock数据成功"
        )
        
    except Exception as e:
        logger.error(f"更新Mock数据失败: {str(e)}")
        return formatter.error(message=f"更新Mock数据失败: {str(e)}")


@router.delete("/{mock_id}", summary="删除Mock数据", response_model=dict)
async def delete_mock_data(
    mock_id: int,
    request: Request,
    current_user: User = DependAuth
):
    """
    删除指定的Mock数据规则
    """
    try:
        mock_data = await MockData.get_or_none(id=mock_id)
        
        if not mock_data:
            return formatter.error(message="Mock数据不存在", code=404)
        
        mock_name = mock_data.name
        await mock_data.delete()
        
        logger.info(f"用户 {current_user.username} 删除Mock规则: {mock_name}")
        
        return formatter.success(message=f"删除Mock数据成功: {mock_name}")
        
    except Exception as e:
        logger.error(f"删除Mock数据失败: {str(e)}")
        return formatter.error(message=f"删除Mock数据失败: {str(e)}")


@router.post("/batch-delete", summary="批量删除Mock数据", response_model=dict)
async def batch_delete_mock_data(
    delete_request: MockDataBatchDeleteRequest,
    request: Request,
    current_user: User = DependAuth
):
    """
    批量删除Mock数据规则
    """
    try:
        deleted_count = await MockData.filter(id__in=delete_request.ids).delete()
        
        logger.info(f"用户 {current_user.username} 批量删除 {deleted_count} 条Mock规则")
        
        return formatter.success(
            data={"deleted_count": deleted_count},
            message=f"成功删除 {deleted_count} 条Mock数据"
        )
        
    except Exception as e:
        logger.error(f"批量删除Mock数据失败: {str(e)}")
        return formatter.error(message=f"批量删除Mock数据失败: {str(e)}")


@router.post("/{mock_id}/toggle", summary="切换Mock启用状态", response_model=dict)
async def toggle_mock_data(
    mock_id: int,
    toggle_request: MockDataToggleRequest,
    request: Request,
    current_user: User = DependAuth
):
    """
    切换Mock数据的启用/禁用状态
    """
    try:
        mock_data = await MockData.get_or_none(id=mock_id)
        
        if not mock_data:
            return formatter.error(message="Mock数据不存在", code=404)
        
        mock_data.enabled = toggle_request.enabled
        await mock_data.save()
        
        status = "启用" if toggle_request.enabled else "禁用"
        logger.info(f"用户 {current_user.username} {status}Mock规则: {mock_data.name}")
        
        return formatter.success(
            data={"enabled": mock_data.enabled},
            message=f"Mock数据已{status}"
        )
        
    except Exception as e:
        logger.error(f"切换Mock状态失败: {str(e)}")
        return formatter.error(message=f"切换Mock状态失败: {str(e)}")


@router.get("/active/list", summary="获取所有启用的Mock规则", response_model=dict)
async def get_active_mock_rules(request: Request):
    """
    获取所有启用的Mock规则（不需要认证，供前端Mock拦截器使用）
    """
    try:
        # 获取所有启用的Mock规则，按优先级排序
        mocks = await MockData.filter(enabled=True).order_by('-priority', '-created_at')
        
        rules = []
        for mock in mocks:
            rules.append({
                "id": mock.id,
                "method": mock.method,
                "url_pattern": mock.url_pattern,
                "response_data": mock.response_data,
                "response_code": mock.response_code,
                "delay": mock.delay
            })
        
        return formatter.success(
            data=rules,
            message=f"获取到 {len(rules)} 条启用的Mock规则"
        )
        
    except Exception as e:
        logger.error(f"获取启用的Mock规则失败: {str(e)}")
        return formatter.error(message=f"获取启用的Mock规则失败: {str(e)}")


@router.post("/{mock_id}/hit", summary="记录Mock命中", response_model=dict)
async def record_mock_hit(
    mock_id: int,
    request: Request
):
    """
    记录Mock规则被命中（供前端Mock拦截器调用）
    """
    try:
        mock_data = await MockData.get_or_none(id=mock_id)
        
        if mock_data:
            mock_data.hit_count += 1
            mock_data.last_hit_time = datetime.now()
            await mock_data.save()
        
        return formatter.success(message="记录成功")
        
    except Exception as e:
        logger.error(f"记录Mock命中失败: {str(e)}")
        return formatter.success(message="记录失败（不影响Mock功能）")

