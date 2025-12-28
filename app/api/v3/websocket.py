"""
WebSocket API端点

实现WebSocket连接和实时数据推送功能。

需求: 3.1 - 当客户端连接WebSocket时，平台应建立持久连接并进行身份验证
需求: 3.4 - 当连接断开时，平台应支持自动重连和状态恢复
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from app.services.auth_service import auth_service
from app.models.admin import User

# 导入实时推送模块
from platform_core.realtime.websocket_server import connection_manager
from platform_core.realtime.subscription_manager import subscription_manager, SubscriptionType
from platform_core.realtime.push_service import push_service

logger = logging.getLogger(__name__)

router = APIRouter()


async def verify_websocket_token(token: str) -> Optional[User]:
    """
    验证WebSocket连接的JWT令牌
    
    Args:
        token: JWT令牌
        
    Returns:
        Optional[User]: 验证成功返回用户，否则返回None
    """
    if not token:
        return None
    
    # 开发模式支持
    if token == "dev":
        logger.warning("WebSocket使用开发模式令牌")
        user = await User.filter().first()
        return user
    
    try:
        user = await auth_service.get_user_from_token(token)
        return user
    except Exception as e:
        logger.error(f"WebSocket令牌验证失败: {e}")
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT认证令牌")
):
    """
    WebSocket连接端点
    
    连接URL: ws://host/api/v3/ws?token={jwt_token}
    
    支持的消息类型：
    - subscribe: 订阅资产数据
    - unsubscribe: 取消订阅
    - ping: 心跳检测
    
    推送的消息类型：
    - connection: 连接状态
    - asset_data: 资产数据更新
    - alert: 告警通知
    - prediction: 预测结果
    - pong: 心跳响应
    """
    # 验证令牌
    user = await verify_websocket_token(token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="认证失败")
        return
    
    user_id = user.id
    
    # 建立连接
    connected = await connection_manager.connect(websocket, user_id)
    if not connected:
        return
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_client_message(user_id, message, websocket)
            except json.JSONDecodeError:
                await send_error(websocket, "无效的JSON格式")
            except Exception as e:
                logger.error(f"处理消息失败: {e}")
                await send_error(websocket, f"处理消息失败: {str(e)}")
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket断开连接: user_id={user_id}")
    except Exception as e:
        logger.error(f"WebSocket错误: user_id={user_id}, error={e}")
    finally:
        # 清理连接和订阅
        await connection_manager.disconnect(user_id)
        await subscription_manager.unsubscribe_all(user_id)


async def handle_client_message(
    user_id: int,
    message: Dict[str, Any],
    websocket: WebSocket
):
    """
    处理客户端消息
    
    Args:
        user_id: 用户ID
        message: 消息内容
        websocket: WebSocket连接
    """
    action = message.get("action")
    
    if action == "subscribe":
        await handle_subscribe(user_id, message, websocket)
    
    elif action == "unsubscribe":
        await handle_unsubscribe(user_id, message, websocket)
    
    elif action == "ping":
        await handle_ping(websocket)
    
    elif action == "get_subscriptions":
        await handle_get_subscriptions(user_id, websocket)
    
    else:
        await send_error(websocket, f"未知的操作: {action}")


async def handle_subscribe(
    user_id: int,
    message: Dict[str, Any],
    websocket: WebSocket
):
    """
    处理订阅请求
    
    消息格式:
    {
        "action": "subscribe",
        "asset_ids": [1, 2, 3],
        "type": "asset_data"  // 可选: asset_data, alert, prediction, all
    }
    """
    asset_ids = message.get("asset_ids", [])
    sub_type_str = message.get("type", "asset_data")
    
    if not asset_ids:
        await send_error(websocket, "asset_ids不能为空")
        return
    
    if not isinstance(asset_ids, list):
        asset_ids = [asset_ids]
    
    # 转换订阅类型
    try:
        sub_type = SubscriptionType(sub_type_str)
    except ValueError:
        sub_type = SubscriptionType.ASSET_DATA
    
    # 批量订阅
    subscriptions = await subscription_manager.subscribe_batch(
        user_id=user_id,
        asset_ids=asset_ids,
        subscription_type=sub_type
    )
    
    # 同时更新连接管理器的订阅（用于快速查找）
    await connection_manager.subscribe(user_id, asset_ids)
    
    # 发送确认
    await websocket.send_text(json.dumps({
        "type": "subscribe_response",
        "success": True,
        "subscribed_assets": asset_ids,
        "subscription_type": sub_type.value,
        "timestamp": datetime.now().isoformat()
    }, ensure_ascii=False))
    
    logger.info(f"订阅成功: user_id={user_id}, assets={asset_ids}, type={sub_type.value}")


async def handle_unsubscribe(
    user_id: int,
    message: Dict[str, Any],
    websocket: WebSocket
):
    """
    处理取消订阅请求
    
    消息格式:
    {
        "action": "unsubscribe",
        "asset_ids": [1, 2, 3]
    }
    """
    asset_ids = message.get("asset_ids", [])
    
    if not asset_ids:
        await send_error(websocket, "asset_ids不能为空")
        return
    
    if not isinstance(asset_ids, list):
        asset_ids = [asset_ids]
    
    # 批量取消订阅
    count = await subscription_manager.unsubscribe_batch(user_id, asset_ids)
    
    # 同时更新连接管理器
    await connection_manager.unsubscribe(user_id, asset_ids)
    
    # 发送确认
    await websocket.send_text(json.dumps({
        "type": "unsubscribe_response",
        "success": True,
        "unsubscribed_count": count,
        "asset_ids": asset_ids,
        "timestamp": datetime.now().isoformat()
    }, ensure_ascii=False))
    
    logger.info(f"取消订阅: user_id={user_id}, assets={asset_ids}")


async def handle_ping(websocket: WebSocket):
    """
    处理心跳请求
    
    消息格式:
    {
        "action": "ping"
    }
    """
    await websocket.send_text(json.dumps({
        "type": "pong",
        "timestamp": datetime.now().isoformat()
    }))


async def handle_get_subscriptions(user_id: int, websocket: WebSocket):
    """
    获取当前订阅列表
    
    消息格式:
    {
        "action": "get_subscriptions"
    }
    """
    subscriptions = subscription_manager.get_user_subscriptions(user_id)
    
    await websocket.send_text(json.dumps({
        "type": "subscriptions_response",
        "subscriptions": [
            {
                "asset_id": sub.asset_id,
                "type": sub.subscription_type.value,
                "created_at": sub.created_at.isoformat()
            }
            for sub in subscriptions
        ],
        "timestamp": datetime.now().isoformat()
    }, ensure_ascii=False))


async def send_error(websocket: WebSocket, error_message: str):
    """
    发送错误消息
    
    Args:
        websocket: WebSocket连接
        error_message: 错误信息
    """
    await websocket.send_text(json.dumps({
        "type": "error",
        "message": error_message,
        "timestamp": datetime.now().isoformat()
    }, ensure_ascii=False))


# ============================================================================
# HTTP API端点 - 用于管理和监控
# ============================================================================

@router.get("/ws/stats", summary="获取WebSocket连接统计")
async def get_websocket_stats():
    """
    获取WebSocket连接和订阅统计信息
    """
    return {
        "connection_stats": connection_manager.get_connection_stats(),
        "subscription_stats": subscription_manager.get_stats(),
        "push_stats": push_service.get_stats()
    }


@router.post("/ws/broadcast", summary="广播消息")
async def broadcast_message(message: Dict[str, Any]):
    """
    向所有连接的客户端广播消息
    
    仅供管理员使用
    """
    count = await push_service.broadcast(message)
    return {
        "success": True,
        "recipients": count
    }


@router.post("/ws/push/asset/{asset_id}", summary="推送资产数据")
async def push_asset_data(
    asset_id: int,
    data: Dict[str, Any],
    quality: str = "good"
):
    """
    向资产订阅者推送数据
    
    用于测试和手动推送
    """
    await push_service.publish_asset_data(asset_id, data, quality)
    return {
        "success": True,
        "asset_id": asset_id
    }


@router.post("/ws/push/alert", summary="推送告警")
async def push_alert(alert: Dict[str, Any]):
    """
    推送告警通知
    """
    await push_service.publish_alert(alert)
    return {
        "success": True
    }
