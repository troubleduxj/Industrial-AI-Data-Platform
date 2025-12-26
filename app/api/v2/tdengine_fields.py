#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TDengine 字段提取 API
从 TDengine 超级表中自动提取字段信息
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, Request, Depends, HTTPException

from app.core.dependency import DependAuth
from app.core.response_formatter_v2 import create_formatter
from app.models.device import DeviceType
from app.models.admin import User
from app.core.tdengine_connector import TDengineConnector

logger = logging.getLogger(__name__)

router = APIRouter()


def map_tdengine_type_to_field_type(tdengine_type: str) -> str:
    """将 TDengine 类型映射到字段配置类型"""
    type_mapping = {
        'FLOAT': 'float',
        'DOUBLE': 'float',
        'INT': 'int',
        'BIGINT': 'int',
        'SMALLINT': 'int',
        'TINYINT': 'int',
        'BOOL': 'boolean',
        'NCHAR': 'string',
        'VARCHAR': 'string',
        'BINARY': 'string',
        'TIMESTAMP': 'string',
    }
    return type_mapping.get(tdengine_type.upper(), 'string')


@router.get("/tdengine/stable-fields/{device_type_code}", summary="获取TDengine超级表字段列表")
async def get_stable_fields(
    request: Request,
    device_type_code: str,
    current_user: User = DependAuth
):
    """
    从 TDengine 超级表中提取字段列表
    
    - **device_type_code**: 设备类型代码
    
    返回字段列表，包含：
    - field_code: 字段代码（列名）
    - field_type: 字段类型（映射后的类型）
    - tdengine_type: TDengine 原始类型
    - length: 字段长度
    - note: 字段说明（TAG/普通列）
    """
    try:
        formatter = create_formatter(request)
        
        # 1. 获取设备类型信息
        device_type = await DeviceType.get_or_none(type_code=device_type_code)
        if not device_type:
            return formatter.not_found(f"设备类型不存在: {device_type_code}")
        
        if not device_type.tdengine_stable_name:
            return formatter.bad_request(f"设备类型 {device_type.type_name} 未配置 TDengine 超级表")
        
        # 2. 连接 TDengine 并查询超级表结构
        try:
            connector = TDengineConnector()
            
            # 查询超级表结构 - 使用完整的表名（数据库.表名）
            stable_name = device_type.tdengine_stable_name
            # 如果表名不包含数据库前缀，添加数据库名
            if '.' not in stable_name:
                stable_name = f"{connector.database}.{stable_name}"
            
            sql = f"DESCRIBE {stable_name}"
            logger.info(f"查询超级表结构: {sql}")
            result = await connector.execute_sql(sql)
            
            if not result or 'data' not in result:
                logger.error(f"查询 TDengine 超级表结构失败: {result}")
                return formatter.internal_error(f"查询 TDengine 超级表结构失败: {result.get('desc', '未知错误') if result else '无响应'}")
            
            rows = result['data']
            
            # 3. 解析字段信息
            fields = []
            for row in rows:
                field_code = row[0]
                tdengine_type = row[1]
                length = row[2]
                note = row[3] if len(row) > 3 else ''
                
                # 排除时间戳字段和 TAG 字段
                if field_code == 'ts':
                    continue
                
                if note == 'TAG':
                    continue
                
                # 映射字段类型
                field_type = map_tdengine_type_to_field_type(tdengine_type)
                
                fields.append({
                    'field_code': field_code,
                    'field_type': field_type,
                    'tdengine_type': tdengine_type,
                    'length': length,
                    'note': note,
                    'is_tag': note == 'TAG'
                })
            
            await connector.close()
            
            logger.info(f"成功提取 {device_type.type_name} 的 TDengine 字段: {len(fields)} 个")
            
            return formatter.success(
                data={
                    'device_type_code': device_type_code,
                    'device_type_name': device_type.type_name,
                    'stable_name': device_type.tdengine_stable_name,
                    'fields': fields,
                    'total': len(fields)
                },
                message=f"成功获取 {len(fields)} 个字段"
            )
            
        except Exception as e:
            logger.error(f"查询 TDengine 超级表失败: {str(e)}")
            return formatter.internal_error(f"查询 TDengine 超级表失败: {str(e)}")
        
    except Exception as e:
        logger.error(f"获取 TDengine 字段失败: {str(e)}")
        return formatter.internal_error(f"获取字段失败: {str(e)}")


@router.get("/tdengine/field-suggestions/{device_type_code}", summary="获取字段配置建议")
async def get_field_suggestions(
    request: Request,
    device_type_code: str,
    current_user: User = DependAuth
):
    """
    获取字段配置建议
    
    对比已配置的字段和 TDengine 超级表字段，返回：
    - 已配置的字段
    - 未配置的字段（建议配置）
    - 多余的字段（TDengine 中不存在）
    """
    try:
        formatter = create_formatter(request)
        
        from app.models.device import DeviceField
        
        # 1. 获取设备类型信息
        device_type = await DeviceType.get_or_none(type_code=device_type_code)
        if not device_type:
            return formatter.not_found(f"设备类型不存在: {device_type_code}")
        
        if not device_type.tdengine_stable_name:
            return formatter.bad_request(f"设备类型 {device_type.type_name} 未配置 TDengine 超级表")
        
        # 2. 获取已配置的字段
        configured_fields = await DeviceField.filter(
            device_type_code=device_type_code,
            is_active=True
        ).all()
        
        configured_dict = {
            field.field_code: {
                'id': field.id,
                'field_name': field.field_name,
                'field_type': field.field_type,
                'unit': field.unit,
                'is_monitoring_key': field.is_monitoring_key
            }
            for field in configured_fields
        }
        
        # 3. 获取 TDengine 超级表字段
        try:
            connector = TDengineConnector()
            
            # 查询超级表结构 - 使用完整的表名（数据库.表名）
            stable_name = device_type.tdengine_stable_name
            # 如果表名不包含数据库前缀，添加数据库名
            if '.' not in stable_name:
                stable_name = f"{connector.database}.{stable_name}"
            
            sql = f"DESCRIBE {stable_name}"
            logger.info(f"查询超级表结构: {sql}")
            result = await connector.execute_sql(sql)
            
            if not result or 'data' not in result:
                logger.error(f"查询 TDengine 超级表结构失败: {result}")
                return formatter.internal_error(f"查询 TDengine 超级表结构失败: {result.get('desc', '未知错误') if result else '无响应'}")
            
            rows = result['data']
            
            tdengine_fields = {}
            for row in rows:
                field_code = row[0]
                tdengine_type = row[1]
                note = row[3] if len(row) > 3 else ''
                
                # 排除时间戳
                if field_code != 'ts':
                    # -------------------------------------------------
                    # 优化后的字段注释解析逻辑
                    # -------------------------------------------------
                    clean_note = ""
                    is_tag_field = False
                    
                    if note:
                        # 1. 统一转换为字符串
                        if isinstance(note, bytes):
                            try:
                                s_note = note.decode('utf-8', errors='ignore')
                            except:
                                s_note = str(note)
                        else:
                            s_note = str(note)
                        
                        # 2. 清理空白和特殊字符
                        s_note = s_note.strip().replace('\x00', '').replace('\ufeff', '')
                        
                        # 3. 处理 bytes 字符串表示 (例如 "b'TAG'")
                        s_note_upper = s_note.upper()
                        if s_note_upper.startswith("B'") and s_note_upper.endswith("'"):
                             s_note = s_note[2:-1]
                             s_note_upper = s_note.upper()
                        
                        # 4. 判断是否为 TAG
                        if s_note_upper in ['TAG', 'TAGS']:
                             is_tag_field = True
                             clean_note = ""  # 如果仅仅是 TAG 标记，则不作为字段名称
                        else:
                             # 如果包含 TAG 但还有其他内容，也认为是 TAG 字段，但保留注释内容
                             if 'TAG' in s_note_upper:
                                 is_tag_field = True
                             clean_note = s_note

                    # 如果清理后的注释为空，则使用字段代码作为名称
                    field_name = clean_note if clean_note else field_code
                    
                    tdengine_fields[field_code] = {
                        'tdengine_type': tdengine_type,
                        'field_type': map_tdengine_type_to_field_type(tdengine_type),
                        'note': note,
                        'field_name': field_name,
                        'is_tag': is_tag_field
                    }
            
            await connector.close()
            
        except Exception as e:
            logger.error(f"查询 TDengine 超级表失败: {str(e)}")
            return formatter.internal_error(f"查询 TDengine 超级表失败: {str(e)}")
        
        # 4. 对比分析
        configured_set = set(configured_dict.keys())
        tdengine_set = set(tdengine_fields.keys())
        
        # 已配置且匹配的字段
        matched_fields = []
        for field_code in configured_set & tdengine_set:
            matched_fields.append({
                'field_code': field_code,
                **configured_dict[field_code],
                **tdengine_fields[field_code]
            })
        
        # 未配置的字段（建议配置）
        missing_fields = []
        for field_code in tdengine_set - configured_set:
            missing_fields.append({
                'field_code': field_code,
                **tdengine_fields[field_code],
                'suggested': True
            })
        
        # 多余的字段（TDengine 中不存在）
        extra_fields = []
        for field_code in configured_set - tdengine_set:
            extra_fields.append({
                'field_code': field_code,
                **configured_dict[field_code],
                'invalid': True
            })
        
        return formatter.success(
            data={
                'device_type_code': device_type_code,
                'device_type_name': device_type.type_name,
                'stable_name': device_type.tdengine_stable_name,
                'matched_fields': matched_fields,
                'missing_fields': missing_fields,
                'extra_fields': extra_fields,
                'statistics': {
                    'total_tdengine_fields': len(tdengine_fields),
                    'total_configured_fields': len(configured_dict),
                    'matched_count': len(matched_fields),
                    'missing_count': len(missing_fields),
                    'extra_count': len(extra_fields),
                    'match_rate': f"{len(matched_fields)/len(tdengine_fields)*100:.1f}%" if tdengine_fields else "0%"
                }
            },
            message="获取字段配置建议成功"
        )
        
    except Exception as e:
        logger.error(f"获取字段建议失败: {str(e)}")
        return formatter.internal_error(f"获取字段建议失败: {str(e)}")

from pydantic import BaseModel

class SyncFieldsRequest(BaseModel):
    device_type_code: str
    field_codes: List[str]

@router.post("/tdengine/sync-fields", summary="同步TDengine字段到配置")
async def sync_fields(
    request: Request,
    sync_data: SyncFieldsRequest,
    current_user: User = DependAuth
):
    """
    同步 TDengine 字段到设备字段配置
    
    - **device_type_code**: 设备类型代码
    - **field_codes**: 要同步的字段代码列表
    """
    try:
        formatter = create_formatter(request)
        device_type_code = sync_data.device_type_code
        field_codes = sync_data.field_codes
        
        if not field_codes:
            return formatter.bad_request("请选择要同步的字段")
            
        # 1. 获取设备类型
        device_type = await DeviceType.get_or_none(type_code=device_type_code)
        if not device_type:
            return formatter.not_found(f"设备类型不存在: {device_type_code}")
            
        # 2. 获取 TDengine 字段信息
        connector = TDengineConnector()
        try:
            stable_name = device_type.tdengine_stable_name
            if '.' not in stable_name:
                stable_name = f"{connector.database}.{stable_name}"
                
            result = await connector.execute_sql(f"DESCRIBE {stable_name}")
            if not result or 'data' not in result:
                return formatter.internal_error("无法获取TDengine表结构")
                
            # 构建字段映射
            td_fields = {}
            for row in result['data']:
                # row: [field_name, type, length, note]
                name = row[0]
                type_ = row[1]
                note = row[3] if len(row) > 3 else ''
                if name != 'ts' and note != 'TAG':
                    td_fields[name] = {
                        'type': type_,
                        'field_type': map_tdengine_type_to_field_type(type_)
                    }
        finally:
            await connector.close()
            
        # 3. 创建或更新字段
        from app.models.device import DeviceField
        
        created_count = 0
        updated_count = 0
        errors = []
        
        for code in field_codes:
            if code not in td_fields:
                errors.append(f"字段 {code} 在TDengine中不存在")
                continue
                
            td_info = td_fields[code]
            
            # 检查是否存在
            field = await DeviceField.get_or_none(
                device_type_code=device_type_code,
                field_code=code
            )
            
            if field:
                # 更新现有字段 (可选，这里主要用于补全信息)
                # field.field_type = td_info['field_type']
                # await field.save()
                updated_count += 1
            else:
                # 创建新字段
                await DeviceField.create(
                    device_type_code=device_type_code,
                    field_code=code,
                    field_name=code,  # 默认使用代码作为名称
                    field_type=td_info['field_type'],
                    field_category='data_collection',
                    is_active=True,
                    is_monitoring_key=True, # 默认作为监控字段
                    is_alarm_enabled=False,
                    description=f"From TDengine {td_info['type']}"
                )
                created_count += 1
                
        return formatter.success(
            data={
                'created': created_count,
                'updated': updated_count,
                'errors': errors
            },
            message=f"同步完成: 新增 {created_count}, 更新 {updated_count}"
        )
        
    except Exception as e:
        logger.error(f"同步字段失败: {str(e)}")
        return formatter.internal_error(f"同步字段失败: {str(e)}")

