#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型存储API端点

提供模型文件的上传、下载、删除等REST API接口。

需求: 2.6
- 平台应支持模型文件的版本回溯和下载
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from loguru import logger
import io

router = APIRouter(prefix="/model-storage", tags=["模型存储"])


# =====================================================
# 响应模型
# =====================================================

class UploadResponse(BaseModel):
    """上传响应"""
    success: bool
    file_path: Optional[str] = None
    checksum: Optional[str] = None
    size_bytes: Optional[int] = None
    error: Optional[str] = None
    created_at: Optional[str] = None


class FileInfoResponse(BaseModel):
    """文件信息响应"""
    file_path: str
    size_bytes: int
    checksum: Optional[str] = None
    exists: bool
    created_at: Optional[str] = None
    modified_at: Optional[str] = None


class DeleteResponse(BaseModel):
    """删除响应"""
    success: bool
    file_path: str
    message: str


class ChecksumResponse(BaseModel):
    """校验和响应"""
    file_path: str
    checksum: str
    valid: bool


class StorageStatsResponse(BaseModel):
    """存储统计响应"""
    total_files: int
    total_size_bytes: int
    total_size_mb: float
    backend_type: str


# =====================================================
# 辅助函数
# =====================================================

def get_storage_service():
    """获取模型存储服务实例"""
    try:
        from ai_engine.model_storage.model_storage_service import get_model_storage_service
        return get_model_storage_service()
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="模型存储模块未安装"
        )


# =====================================================
# API端点
# =====================================================

@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="上传模型文件",
    description="上传AI模型文件到存储后端。支持.pkl、.onnx、.h5、.joblib格式。"
)
async def upload_model_file(
    file: UploadFile = File(..., description="模型文件"),
    model_id: Optional[int] = Query(None, description="模型ID（可选）"),
    version: Optional[str] = Query(None, description="模型版本（可选）"),
):
    """
    上传模型文件
    
    需求: 2.1 - 上传模型文件时，平台应将文件存储到配置的存储后端
    """
    storage_service = get_storage_service()
    
    # 验证文件名
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    # 验证文件格式
    is_valid, ext = storage_service.backend.validate_format(file.filename)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file.filename}。支持的格式: .pkl, .onnx, .h5, .joblib"
        )
    
    try:
        # 读取文件内容
        content = await file.read()
        file_obj = io.BytesIO(content)
        
        # 上传文件
        result = await storage_service.upload_model(
            file=file_obj,
            filename=file.filename,
            model_id=model_id,
            version=version,
        )
        
        if result.success:
            return UploadResponse(
                success=True,
                file_path=result.file_path,
                checksum=result.checksum,
                size_bytes=result.size_bytes,
                created_at=result.created_at.isoformat() if result.created_at else None,
            )
        else:
            return UploadResponse(
                success=False,
                error=result.error,
            )
            
    except Exception as e:
        logger.error(f"上传模型文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get(
    "/download",
    summary="下载模型文件",
    description="从存储后端下载模型文件。"
)
async def download_model_file(
    file_path: str = Query(..., description="文件存储路径"),
):
    """
    下载模型文件
    
    需求: 2.6 - 平台应支持模型文件的版本回溯和下载
    """
    storage_service = get_storage_service()
    
    try:
        # 检查文件是否存在
        if not await storage_service.model_exists(file_path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
        
        # 下载文件
        file_obj = await storage_service.download_model(file_path)
        content = file_obj.read()
        
        # 提取文件名
        filename = file_path.split("/")[-1]
        
        # 返回文件流
        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(content)),
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载模型文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")


@router.delete(
    "/delete",
    response_model=DeleteResponse,
    summary="删除模型文件",
    description="从存储后端删除模型文件。"
)
async def delete_model_file(
    file_path: str = Query(..., description="文件存储路径"),
):
    """
    删除模型文件
    
    需求: 2.5 - 删除模型版本时，平台应清理关联的模型文件
    """
    storage_service = get_storage_service()
    
    try:
        # 检查文件是否存在
        if not await storage_service.model_exists(file_path):
            return DeleteResponse(
                success=False,
                file_path=file_path,
                message="文件不存在",
            )
        
        # 删除文件
        result = await storage_service.delete_model(file_path)
        
        if result:
            return DeleteResponse(
                success=True,
                file_path=file_path,
                message="文件删除成功",
            )
        else:
            return DeleteResponse(
                success=False,
                file_path=file_path,
                message="文件删除失败",
            )
            
    except Exception as e:
        logger.error(f"删除模型文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get(
    "/info",
    response_model=FileInfoResponse,
    summary="获取文件信息",
    description="获取模型文件的详细信息。"
)
async def get_file_info(
    file_path: str = Query(..., description="文件存储路径"),
):
    """获取模型文件信息"""
    storage_service = get_storage_service()
    
    try:
        # 检查文件是否存在
        exists = await storage_service.model_exists(file_path)
        
        if not exists:
            return FileInfoResponse(
                file_path=file_path,
                size_bytes=0,
                exists=False,
            )
        
        # 获取校验和
        checksum = await storage_service.get_model_checksum(file_path)
        
        # 下载文件获取大小
        file_obj = await storage_service.download_model(file_path)
        size = len(file_obj.read())
        
        return FileInfoResponse(
            file_path=file_path,
            size_bytes=size,
            checksum=checksum,
            exists=True,
        )
        
    except Exception as e:
        logger.error(f"获取文件信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取信息失败: {str(e)}")


@router.get(
    "/checksum",
    response_model=ChecksumResponse,
    summary="获取文件校验和",
    description="获取模型文件的SHA256校验和。"
)
async def get_file_checksum(
    file_path: str = Query(..., description="文件存储路径"),
):
    """
    获取文件校验和
    
    需求: 2.3 - 创建模型版本时，平台应关联模型文件路径和校验和
    """
    storage_service = get_storage_service()
    
    try:
        # 检查文件是否存在
        if not await storage_service.model_exists(file_path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
        
        # 获取校验和
        checksum = await storage_service.get_model_checksum(file_path)
        
        if not checksum:
            raise HTTPException(status_code=500, detail="无法计算校验和")
        
        return ChecksumResponse(
            file_path=file_path,
            checksum=checksum,
            valid=True,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取校验和失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取校验和失败: {str(e)}")


@router.post(
    "/verify",
    response_model=ChecksumResponse,
    summary="验证文件校验和",
    description="验证模型文件的校验和是否匹配。"
)
async def verify_file_checksum(
    file_path: str = Query(..., description="文件存储路径"),
    expected_checksum: str = Query(..., description="期望的校验和"),
):
    """验证文件校验和"""
    storage_service = get_storage_service()
    
    try:
        # 检查文件是否存在
        if not await storage_service.model_exists(file_path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
        
        # 验证校验和
        is_valid = await storage_service.verify_model_checksum(file_path, expected_checksum)
        
        # 获取实际校验和
        actual_checksum = await storage_service.get_model_checksum(file_path)
        
        return ChecksumResponse(
            file_path=file_path,
            checksum=actual_checksum or "",
            valid=is_valid,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证校验和失败: {e}")
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")


@router.get(
    "/list",
    summary="列出模型文件",
    description="列出存储后端中的所有模型文件。"
)
async def list_model_files(
    prefix: str = Query("models/", description="路径前缀"),
):
    """列出模型文件"""
    storage_service = get_storage_service()
    
    try:
        # 获取文件列表
        files = await storage_service.backend.list_files(prefix=prefix)
        
        return {
            "success": True,
            "prefix": prefix,
            "count": len(files),
            "files": files,
        }
        
    except Exception as e:
        logger.error(f"列出文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"列出文件失败: {str(e)}")


@router.get(
    "/stats",
    response_model=StorageStatsResponse,
    summary="获取存储统计",
    description="获取模型存储的统计信息。"
)
async def get_storage_stats():
    """获取存储统计信息"""
    storage_service = get_storage_service()
    
    try:
        # 获取文件列表
        files = await storage_service.backend.list_files(prefix="models/")
        
        total_size = sum(f.get("size_bytes", 0) for f in files)
        
        return StorageStatsResponse(
            total_files=len(files),
            total_size_bytes=total_size,
            total_size_mb=round(total_size / (1024 * 1024), 2),
            backend_type=storage_service.backend.__class__.__name__,
        )
        
    except Exception as e:
        logger.error(f"获取存储统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.get(
    "/supported-formats",
    summary="获取支持的文件格式",
    description="获取存储后端支持的模型文件格式列表。"
)
async def get_supported_formats():
    """获取支持的文件格式"""
    storage_service = get_storage_service()
    
    return {
        "formats": storage_service.backend.supported_formats,
        "description": {
            ".pkl": "Python Pickle序列化文件",
            ".onnx": "ONNX模型格式",
            ".h5": "HDF5/Keras模型格式",
            ".joblib": "Joblib序列化文件",
        }
    }
