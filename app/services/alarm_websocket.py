#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报警WebSocket推送服务
负责实时推送报警通知到前端
"""

import asyncio
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect, Query
import jwt

from app.models import User
from app.settings import settings
from app.log import logger


class AlarmWebSocketManager:
    """报警WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, Dict] = {}  # {websocket: {device_types: [], user_id: int}}
    
    async def connect(
        self, 
        websocket: WebSocket, 
        user_id: int,
        device_types: Optional[List[str]] = None
    ):
        """建立WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = {
            "user_id": user_id,
            "device_types": device_types or [],  # 空列表表示订阅所有类型
            "connected_at": datetime.now().isoformat()
        }
        logger.info(f"报警WebSocket连接已建立，用户ID: {user_id}, 订阅类型: {device_types or '全部'}")
    
    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            sub = self.subscriptions[websocket]
            logger.info(f"报警WebSocket连接已断开，用户ID: {sub.get('user_id')}")
            del self.subscriptions[websocket]
    
    async def send_alarm(self, websocket: WebSocket, alarm: Dict):
        """发送报警消息到单个连接"""
        try:
            message = json.dumps({
                "type": "alarm",
                "timestamp": datetime.now().isoformat(),
                "data": alarm
            }, ensure_ascii=False, default=str)
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"发送报警消息失败: {str(e)}")
            self.disconnect(websocket)
    
    async def broadcast_alarm(self, alarm: Dict):
        """广播报警消息到所有相关订阅者"""
        device_type = alarm.get("device_type_code")
        disconnected = []
        
        for websocket, subscription in self.subscriptions.items():
            try:
                subscribed_types = subscription.get("device_types", [])
                
                # 检查是否订阅了该设备类型
                if not subscribed_types or device_type in subscribed_types:
                    await self.send_alarm(websocket, alarm)
                    
            except Exception as e:
                logger.error(f"广播报警失败: {str(e)}")
                disconnected.append(websocket)
        
        # 清理断开的连接
        for ws in disconnected:
            self.disconnect(ws)
    
    async def broadcast_alarms(self, alarms: List[Dict]):
        """批量广播报警消息"""
        for alarm in alarms:
            await self.broadcast_alarm(alarm)
    
    async def send_statistics_update(self):
        """发送统计更新通知"""
        message = json.dumps({
            "type": "statistics_update",
            "timestamp": datetime.now().isoformat(),
        }, ensure_ascii=False)
        
        disconnected = []
        for websocket in self.active_connections:
            try:
                await websocket.send_text(message)
            except Exception:
                disconnected.append(websocket)
        
        for ws in disconnected:
            self.disconnect(ws)
    
    def get_connection_count(self) -> int:
        """获取当前连接数"""
        return len(self.active_connections)
    
    def get_connection_info(self) -> List[Dict]:
        """获取所有连接信息"""
        return [
            {
                "user_id": sub.get("user_id"),
                "device_types": sub.get("device_types"),
                "connected_at": sub.get("connected_at")
            }
            for sub in self.subscriptions.values()
        ]


# 全局单例
alarm_ws_manager = AlarmWebSocketManager()


async def websocket_auth(token: Optional[str]) -> tuple[Optional[User], Optional[str]]:
    """WebSocket认证函数"""
    if not token:
        return None, "Missing authentication token"
    
    try:
        if token == "dev":
            user = await User.filter().first()
        else:
            decode_data = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = decode_data.get("user_id")
            user = await User.filter(id=user_id).first()
        
        if not user:
            return None, "Authentication failed"
        
        return user, None
    except jwt.DecodeError:
        return None, "无效的Token"
    except jwt.ExpiredSignatureError:
        return None, "登录已过期"
    except Exception as e:
        return None, f"认证异常: {repr(e)}"


async def broadcast_new_alarms(alarms: List[Dict]):
    """
    广播新报警（供其他模块调用）
    
    Args:
        alarms: 报警列表
    """
    if alarms:
        await alarm_ws_manager.broadcast_alarms(alarms)
        await alarm_ws_manager.send_statistics_update()
