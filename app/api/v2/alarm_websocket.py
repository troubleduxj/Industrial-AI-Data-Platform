#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报警WebSocket API端点
提供实时报警推送功能
"""

import asyncio
import json
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.services.alarm_websocket import alarm_ws_manager, websocket_auth
from app.services.alarm_detection import alarm_engine
from app.core.response_formatter_v2 import create_formatter
from app.log import logger

router = APIRouter(tags=["报警WebSocket"])


@router.websocket("/ws")
async def alarm_websocket_endpoint(
    websocket: WebSocket,
    device_types: Optional[str] = Query(None, description="订阅的设备类型，逗号分隔"),
    token: Optional[str] = Query(None, description="JWT认证token"),
):
    """
    报警WebSocket端点
    
    连接后会实时接收报警通知：
    - type: "alarm" - 新报警触发
    - type: "statistics_update" - 统计数据更新
    - type: "ping" - 心跳
    """
    # 认证
    user, auth_error = await websocket_auth(token)
    if auth_error:
        logger.error(f"报警WebSocket认证失败: {auth_error}")
        await websocket.close(code=1008, reason=f"Authentication failed: {auth_error}")
        return
    
    # 解析设备类型
    device_type_list = None
    if device_types:
        device_type_list = [t.strip() for t in device_types.split(",") if t.strip()]
    
    # 建立连接
    await alarm_ws_manager.connect(websocket, user.id, device_type_list)
    
    try:
        # 发送连接成功消息
        welcome_msg = json.dumps({
            "type": "connected",
            "timestamp": datetime.now().isoformat(),
            "message": "报警WebSocket连接成功",
            "subscribed_types": device_type_list or "all"
        }, ensure_ascii=False)
        await websocket.send_text(welcome_msg)
        
        # 保持连接
        while True:
            try:
                # 等待客户端消息（心跳或订阅更新）
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                
                try:
                    msg = json.loads(data)
                    msg_type = msg.get("type")
                    
                    if msg_type == "ping":
                        # 响应心跳
                        pong_msg = json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        })
                        await websocket.send_text(pong_msg)
                        
                    elif msg_type == "subscribe":
                        # 更新订阅
                        new_types = msg.get("device_types", [])
                        alarm_ws_manager.subscriptions[websocket]["device_types"] = new_types
                        ack_msg = json.dumps({
                            "type": "subscribed",
                            "timestamp": datetime.now().isoformat(),
                            "device_types": new_types or "all"
                        })
                        await websocket.send_text(ack_msg)
                        
                except json.JSONDecodeError:
                    pass
                    
            except asyncio.TimeoutError:
                # 发送心跳
                ping_msg = json.dumps({
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                })
                await websocket.send_text(ping_msg)
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"报警WebSocket错误: {str(e)}")
    finally:
        alarm_ws_manager.disconnect(websocket)


@router.get("/connections", summary="获取报警WebSocket连接信息")
async def get_alarm_connections():
    """获取当前报警WebSocket连接信息"""
    formatter = create_formatter()
    return formatter.success(
        data={
            "connection_count": alarm_ws_manager.get_connection_count(),
            "connections": alarm_ws_manager.get_connection_info()
        },
        message="获取连接信息成功"
    )


@router.get("/engine/status", summary="获取报警引擎状态")
async def get_alarm_engine_status():
    """获取报警检测引擎状态"""
    formatter = create_formatter()
    return formatter.success(
        data=alarm_engine.get_cache_info(),
        message="获取引擎状态成功"
    )


@router.post("/engine/refresh", summary="刷新报警规则缓存")
async def refresh_alarm_rules():
    """强制刷新报警规则缓存"""
    await alarm_engine.refresh_rules()
    formatter = create_formatter()
    return formatter.success(
        data=alarm_engine.get_cache_info(),
        message="规则缓存已刷新"
    )
