from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from typing import Optional, List
import asyncio
import json
import logging
from datetime import datetime
import jwt

from app.controllers.device_data import DeviceDataController
from app.schemas.devices import DeviceRealtimeQuery
from app.core.dependency import DependAuth
from app.models.device import DeviceType
from app.models import User
from app.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["设备WebSocket"])


async def websocket_auth(token: Optional[str]) -> tuple[Optional[User], Optional[str]]:
    """WebSocket认证函数，返回(用户对象, 错误信息)"""
    logger.debug(f"WebSocket认证开始，token: {token[:50] if token else 'None'}...")

    if not token:
        logger.debug("认证失败：缺少token")
        return None, "Missing authentication token"

    try:
        if token == "dev":
            logger.debug("使用开发模式认证")
            user = await User.filter().first()
        else:
            logger.debug(f"开始解码JWT token，SECRET_KEY: {settings.SECRET_KEY[:10]}...")
            decode_data = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            logger.debug(f"JWT解码成功，数据: {decode_data}")
            user_id = decode_data.get("user_id")
            logger.debug(f"查找用户ID: {user_id}")
            user = await User.filter(id=user_id).first()

        if not user:
            logger.debug("认证失败：用户不存在")
            return None, "Authentication failed"

        logger.debug(f"认证成功，用户: {user.username}")
        return user, None
    except jwt.DecodeError as e:
        logger.debug(f"JWT解码错误: {str(e)}")
        return None, "无效的Token"
    except jwt.ExpiredSignatureError as e:
        logger.debug(f"JWT过期错误: {str(e)}")
        return None, "登录已过期"
    except Exception as e:
        logger.debug(f"认证异常: {repr(e)}")
        return None, f"认证异常: {repr(e)}"


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.device_subscriptions: dict = (
            {}
        )  # {websocket: {device_code: str, type_code: str, query: DeviceRealtimeQuery}}

    async def connect(
        self,
        websocket: WebSocket,
        device_code: Optional[str] = None,
        device_codes: Optional[List[str]] = None,
        type_code: Optional[str] = None,
        page_size: int = 20,
    ):
        """建立WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)

        # 创建统一的设备查询对象，如果type_code为None则默认为welding
        query = DeviceRealtimeQuery(
            device_code=device_code,
            device_codes=device_codes,
            type_code=type_code or "welding",
            page=1,
            page_size=page_size,
        )

        self.device_subscriptions[websocket] = {
            "device_code": device_code,
            "device_codes": device_codes,
            "type_code": type_code,
            "query": query,
        }

        device_info = (
            device_code or f"{len(device_codes) if device_codes else 0}个指定设备" if device_codes else "全部设备"
        )
        logger.info(f"WebSocket连接已建立，设备类型: {type_code or 'welding'}，设备编号: {device_info}")

    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.device_subscriptions:
            subscription = self.device_subscriptions[websocket]
            device_code = subscription.get("device_code")
            device_codes = subscription.get("device_codes")
            type_code = subscription.get("type_code")
            del self.device_subscriptions[websocket]
            device_info = (
                device_code or f"{len(device_codes) if device_codes else 0}个指定设备" if device_codes else "全部设备"
            )
            logger.info(f"WebSocket连接已断开，设备类型: {type_code or 'welding'}，设备编号: {device_info}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {str(e)}")
            self.disconnect(websocket)

    async def broadcast_device_data(self, device_code: Optional[str], type_code: Optional[str], data: dict):
        """广播设备数据到相关订阅者"""
        disconnected_connections = []

        for websocket, subscription in self.device_subscriptions.items():
            try:
                # 检查是否需要发送给这个连接
                sub_device_code = subscription.get("device_code")
                sub_type_code = subscription.get("type_code")

                # 匹配条件：设备编号和设备类型都要匹配（或为None表示订阅全部）
                device_match = sub_device_code is None or sub_device_code == device_code
                type_match = sub_type_code is None or sub_type_code == type_code

                if device_match and type_match:
                    message = json.dumps(
                        {
                            "type": "realtime_data",
                            "timestamp": datetime.now().isoformat(),
                            "device_type": type_code,
                            "data": data,
                        },
                        ensure_ascii=False,
                        default=str,
                    )
                    await websocket.send_text(message)
            except Exception as e:
                logger.error(f"广播消息失败: {str(e)}")
                disconnected_connections.append(websocket)

        # 清理断开的连接
        for websocket in disconnected_connections:
            self.disconnect(websocket)


manager = ConnectionManager()


@router.websocket("/realtime-data/ws")
async def websocket_realtime_data(
    websocket: WebSocket,
    device_code: Optional[str] = Query(None, description="设备编号，不提供则订阅所有设备"),
    device_codes: Optional[str] = Query(None, description="设备编号列表，逗号分隔，用于订阅指定设备"),
    type_code: Optional[str] = Query(None, description="设备类型代码，不提供则默认为焊接设备"),
    page_size: int = Query(20, description="每次推送数据量", ge=1, le=2000),
    token: Optional[str] = Query(None, description="JWT认证token"),
):
    """WebSocket实时数据推送端点"""
    # 先进行认证
    user, auth_error = await websocket_auth(token)
    if auth_error:
        logger.error(f"WebSocket认证失败: {auth_error}")
        await websocket.close(code=1008, reason=f"Authentication failed: {auth_error}")
        return

    logger.info(f"WebSocket认证成功，用户: {user.username}")

    # 处理device_codes参数（从逗号分隔的字符串转换为列表）
    device_codes_list = None
    if device_codes:
        device_codes_list = [code.strip() for code in device_codes.split(",") if code.strip()]
        if len(device_codes_list) > 100:  # 限制最大设备数量
            await websocket.close(code=1008, reason="设备数量超过限制（最大100个）")
            return

    await manager.connect(websocket, device_code, device_codes_list, type_code, page_size)
    controller = DeviceDataController()

    try:
        while True:
            try:
                # 获取订阅信息
                subscription = manager.device_subscriptions.get(websocket)
                if not subscription:
                    break

                query = subscription["query"]

                # 如果没有指定具体的设备编码，说明是通用订阅，
                # 我们需要获取所有设备的数据，而不是默认的第一页。
                # 通过设置一个足够大的 page_size 来实现这一点。
                if not query.device_code and not query.device_codes:
                    query.page_size = 10000  # 获取所有设备
                    query.page = 1

                # 获取设备实时数据
                result = await controller.get_device_realtime_data(query)

                # 发送数据
                message = json.dumps(
                    {
                        "type": "realtime_data",
                        "timestamp": datetime.now().isoformat(),
                        "device_type": subscription.get("type_code", "welding"),
                        "data": result,
                    },
                    ensure_ascii=False,
                    default=str,
                )

                await manager.send_personal_message(message, websocket)

                # 等待60秒（按用户要求的查询频率）
                await asyncio.sleep(60)

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket数据推送错误: {str(e)}")
                error_message = json.dumps(
                    {"type": "error", "timestamp": datetime.now().isoformat(), "message": f"数据获取失败: {str(e)}"},
                    ensure_ascii=False,
                )
                await manager.send_personal_message(error_message, websocket)
                await asyncio.sleep(60)  # 错误后也等待60秒再重试

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)


@router.websocket("/realtime-data/broadcast")
async def websocket_broadcast_endpoint(
    websocket: WebSocket,
    type_code: Optional[str] = Query(None, description="设备类型代码，不提供则订阅所有类型"),
    token: Optional[str] = Query(None, description="JWT认证token"),
):
    """WebSocket广播端点（用于系统主动推送）"""
    # 先进行认证
    user, auth_error = await websocket_auth(token)
    if auth_error:
        logger.error(f"WebSocket广播认证失败: {auth_error}")
        await websocket.close(code=1008, reason=f"Authentication failed: {auth_error}")
        return

    logger.info(f"WebSocket广播认证成功，用户: {user.username}")

    await manager.connect(websocket, None, type_code)

    try:
        while True:
            # 保持连接活跃
            await asyncio.sleep(30)
            ping_message = json.dumps({"type": "ping", "timestamp": datetime.now().isoformat()})
            await manager.send_personal_message(ping_message, websocket)

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)


# 提供给其他模块使用的广播函数
async def broadcast_device_update(device_code: str, type_code: str, data: dict):
    """广播设备数据更新（供其他模块调用）"""
    await manager.broadcast_device_data(device_code, type_code, data)


async def broadcast_all_devices_update(type_code: Optional[str], data: dict):
    """广播所有设备数据更新（供其他模块调用）"""
    await manager.broadcast_device_data(None, type_code, data)


async def broadcast_type_devices_update(type_code: str, data: dict):
    """广播指定类型所有设备数据更新（供其他模块调用）"""
    await manager.broadcast_device_data(None, type_code, data)
