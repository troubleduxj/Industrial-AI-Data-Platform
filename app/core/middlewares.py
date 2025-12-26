import json
import re
from datetime import datetime
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send
from loguru import logger

from app.core.dependency import AuthControl
from app.models.admin import HttpAuditLog, User

from .bgtask import BgTasks


def serialize_datetime(obj):
    """递归处理对象中的datetime类型，转换为字符串"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_datetime(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(serialize_datetime(item) for item in obj)
    else:
        return obj


class SimpleBaseMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)

        response = await self.before_request(request) or self.app
        await response(request.scope, request.receive, send)
        await self.after_request(request)

    async def before_request(self, request: Request):
        return self.app

    async def after_request(self, request: Request):
        return None


class BackGroundTaskMiddleware(SimpleBaseMiddleware):
    async def before_request(self, request):
        await BgTasks.init_bg_tasks_obj()

    async def after_request(self, request):
        await BgTasks.execute_tasks()


class HttpAuditLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, methods: list[str], exclude_paths: list[str]):
        super().__init__(app)
        self.methods = methods
        self.exclude_paths = exclude_paths
        # 更新：添加V2审计日志路径
        self.audit_log_paths = ["/api/v1/auditlog/list", "/api/v2/audit-logs"]
        # 更新：增加响应体大小限制到5MB
        self.max_body_size = 5 * 1024 * 1024  # 5MB 响应体大小限制

    async def get_request_args(self, request: Request) -> dict:
        args = {}
        # 获取查询参数
        for key, value in request.query_params.items():
            args[key] = value

        # 获取请求体
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
                if isinstance(body, dict):
                    args.update(body)
                elif isinstance(body, list):
                    # 处理批量导入等列表类型请求体
                    if request.url.path.endswith("/batch_import"):
                        args = {"devices": body}  # 确保整个请求体作为devices数组传递
                    else:
                        args["batch_data"] = body
                elif body is not None:
                    # 处理简单类型请求体(如切换锁定状态的ID)
                    args["body"] = body
            except json.JSONDecodeError:
                try:
                    body = await request.form()
                    for k, v in body.items():
                        if hasattr(v, "filename"):  # 文件上传行为
                            args[k] = v.filename
                        elif isinstance(v, list) and v and hasattr(v[0], "filename"):
                            args[k] = [file.filename for file in v]
                        else:
                            args[k] = v
                except Exception:
                    pass

        return args

    async def get_response_body(self, request: Request, response: Response) -> Any:
        # 检查Content-Length
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > self.max_body_size:
            return {"code": 0, "msg": "Response too large to log", "data": None}

        if hasattr(response, "body"):
            body = response.body
        else:
            body_chunks = []
            async for chunk in response.body_iterator:
                if not isinstance(chunk, bytes):
                    chunk = chunk.encode(response.charset)
                body_chunks.append(chunk)

            response.body_iterator = self._async_iter(body_chunks)
            body = b"".join(body_chunks)

        # 检查实际body大小，而不仅仅是Content-Length
        if len(body) > self.max_body_size:
            return {"code": 0, "msg": "Response too large to log", "data": None}

        # 对审计日志接口进行特殊处理（包括V1和V2）
        if any(request.url.path.startswith(path) for path in self.audit_log_paths):
            try:
                data = self.lenient_json(body)
                # 只保留基本信息，去除详细的响应内容
                if isinstance(data, dict):
                    data.pop("response_body", None)
                    if "data" in data and isinstance(data["data"], list):
                        for item in data["data"]:
                            item.pop("response_body", None)
                return data
            except Exception:
                return None

        return self.lenient_json(body)

    def lenient_json(self, v: Any) -> Any:
        if isinstance(v, (str, bytes)):
            try:
                return json.loads(v)
            except (ValueError, TypeError):
                pass
        return v

    async def _async_iter(self, items: list[bytes]) -> AsyncGenerator[bytes, None]:
        for item in items:
            yield item

    async def get_request_log(self, request: Request, response: Response) -> dict:
        """
        根据request和response对象获取对应的日志记录数据
        """
        data: dict = {"path": request.url.path, "status": response.status_code, "method": request.method, "summary": ""}
        # 路由信息
        app: FastAPI = request.app
        for route in app.routes:
            if (
                isinstance(route, APIRoute)
                and route.path_regex.match(request.url.path)
                and request.method in route.methods
            ):
                data["module"] = ",".join(route.tags)
                data["summary"] = route.summary or ""
        # 获取用户信息
        try:
            # 优先从Authorization头部获取Bearer token
            token = None
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]  # 移除"Bearer "前缀
            else:
                # 兼容旧的token头部方式
                token = request.headers.get("token")
            
            user_obj = None
            if token:
                user_obj: User = await AuthControl.is_authed(token)
            data["user_id"] = user_obj.id if user_obj else 0
            data["username"] = user_obj.username if user_obj else ""
        except Exception:
            data["user_id"] = 0
            data["username"] = ""
        return data

    async def before_request(self, request: Request):
        request_args = await self.get_request_args(request)
        request.state.request_args = request_args

    async def after_request(self, request: Request, response: Response, process_time: int):
        if request.method in self.methods:
            for path in self.exclude_paths:
                if re.search(path, request.url.path, re.I) is not None:
                    return
            data: dict = await self.get_request_log(request=request, response=response)
            data["response_time"] = process_time

            # 确保所有JSON字段都有有效值
            data["request_args"] = serialize_datetime(request.state.request_args or {})
            response_body = await self.get_response_body(request, response)
            
            # 处理response_body，确保它是有效的JSON数据
            if response_body is None or response_body == b'' or response_body == '':
                data["response_body"] = {}
            elif isinstance(response_body, bytes):
                try:
                    parsed_body = json.loads(response_body.decode('utf-8'))
                    data["response_body"] = serialize_datetime(parsed_body)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    data["response_body"] = {"raw_data": response_body.decode('utf-8', errors='ignore')}
            else:
                data["response_body"] = serialize_datetime(response_body)
            
            # 确保所有字符串字段不为None
            for key in ["module", "summary", "method", "path", "username"]:
                if data.get(key) is None:
                    data[key] = ""
            
            # 对整个data字典进行datetime序列化处理，确保没有datetime对象
            data = serialize_datetime(data)
            
            # 不要手动设置created_at和updated_at字段，让TimestampMixin自动处理
            # 移除可能存在的时间戳字段，避免与TimestampMixin冲突
            data.pop("created_at", None)
            data.pop("updated_at", None)
            
            # 创建AuditLog对象
            try:
                # 检查数据库连接是否可用
                from tortoise import Tortoise
                from tortoise.connection import connections
                
                if not Tortoise._inited:
                    logger.warning("Tortoise ORM未初始化，跳过审计日志记录")
                    return response
                
                # 检查default连接是否存在
                try:
                    conn = connections.get("default")
                    if conn is None:
                        logger.warning("数据库连接不可用，跳过审计日志记录")
                        return response
                except KeyError:
                    logger.warning("default连接未配置，跳过审计日志记录")
                    return response
                
                audit_log = HttpAuditLog(**data)
                # 手动设置初始时间戳，确保字段不为None
                now = datetime.now()
                if now.tzinfo is not None:
                    now = now.replace(tzinfo=None)
                audit_log.created_at = now
                audit_log.updated_at = now
                
                # 保存到数据库
                await audit_log.save()
                logger.debug(f"审计日志已记录: {data.get('summary', 'N/A')}")
            except Exception as e:
                logger.error(f"记录审计日志失败: {e}")
                import traceback
                logger.debug(f"详细错误信息: {traceback.format_exc()}")
                # 不抛出异常，避免影响正常请求

        return response

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time: datetime = datetime.now()
        await self.before_request(request)
        response = await call_next(request)
        end_time: datetime = datetime.now()
        process_time = int((end_time.timestamp() - start_time.timestamp()) * 1000)
        await self.after_request(request, response, process_time)
        return response
