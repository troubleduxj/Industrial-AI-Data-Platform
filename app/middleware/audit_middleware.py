"""
权限审计中间件
"""
import time
import json
from typing import Callable, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.audit_service import audit_service
from app.core.unified_logger import get_logger

logger = get_logger(__name__)
from app.core.auth_dependencies import get_current_user_optional


class AuditMiddleware(BaseHTTPMiddleware):
    """权限审计中间件"""
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        # 排除不需要审计的路径
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/health",
            "/metrics"
        ]
        
        # 需要特别关注的敏感路径
        self.sensitive_paths = [
            "/api/v2/users",
            "/api/v2/roles",
            "/api/v2/permissions",
            "/api/v2/admin",
            "/api/v2/system"
        ]
        
        # 批量操作路径
        self.batch_operation_paths = [
            "/batch",
            "/bulk",
            "/delete-multiple"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        start_time = time.time()
        
        # 检查是否需要审计
        if self._should_exclude_path(request.url.path):
            return await call_next(request)
        
        # 获取用户信息
        user_info = await self._get_user_info(request)
        
        # 处理请求
        try:
            response = await call_next(request)
            duration_ms = int((time.time() - start_time) * 1000)
            
            # 记录审计日志
            await self._log_request(request, response, user_info, duration_ms)
            
            return response
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            # 记录异常审计日志
            await self._log_exception(request, e, user_info, duration_ms)
            
            # 重新抛出异常
            raise e
    
    def _should_exclude_path(self, path: str) -> bool:
        """检查路径是否应该排除审计"""
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        return False
    
    async def _get_user_info(self, request: Request) -> dict:
        """获取用户信息"""
        try:
            # 尝试从请求中获取用户信息
            user = await get_current_user_optional(request)
            if user:
                return {
                    "user_id": user.id,
                    "username": user.username,
                    "is_superuser": user.is_superuser
                }
        except Exception:
            pass
        
        return {
            "user_id": None,
            "username": "anonymous",
            "is_superuser": False
        }
    
    async def _log_request(self, request: Request, response: Response, user_info: dict, duration_ms: int):
        """记录请求审计日志"""
        try:
            path = request.url.path
            method = request.method
            status_code = response.status_code
            
            # 确定操作类型
            action_type = self._determine_action_type(path, method)
            
            # 检查是否是敏感操作
            is_sensitive = self._is_sensitive_operation(path, method)
            
            # 检查是否是批量操作
            is_batch = self._is_batch_operation(path, method)
            
            # 根据不同类型记录不同的日志
            if is_batch:
                # 批量操作日志
                await self._log_batch_operation(request, user_info, duration_ms, status_code == 200)
            elif is_sensitive:
                # 敏感操作日志
                await self._log_sensitive_operation(request, user_info, duration_ms, status_code == 200)
            elif action_type == "API_ACCESS":
                # API访问日志
                await self._log_api_access(request, user_info, duration_ms, status_code)
            
            # 检查异常状态码
            if status_code >= 400:
                await self._log_error_response(request, response, user_info, duration_ms)
                
        except Exception as e:
            logger.error(f"记录请求审计日志失败: {e}")
    
    async def _log_exception(self, request: Request, exception: Exception, user_info: dict, duration_ms: int):
        """记录异常审计日志"""
        try:
            await audit_service.log_sensitive_operation(
                user_id=user_info["user_id"],
                username=user_info["username"],
                operation_name=f"异常请求: {type(exception).__name__}",
                resource_type="ERROR",
                resource_id=str(exception),
                request=request,
                success=False,
                extra_data={
                    "exception_type": type(exception).__name__,
                    "exception_message": str(exception)
                },
                duration_ms=duration_ms
            )
        except Exception as e:
            logger.error(f"记录异常审计日志失败: {e}")
    
    async def _log_api_access(self, request: Request, user_info: dict, duration_ms: int, status_code: int):
        """记录API访问日志"""
        try:
            # 只记录需要认证的API访问
            if user_info["user_id"]:
                # 这里可以根据需要决定是否记录所有API访问
                # 目前只记录失败的访问
                if status_code >= 400:
                    permission_code = f"{request.method} {request.url.path}"
                    await audit_service.log_permission_check(
                        user_id=user_info["user_id"],
                        username=user_info["username"],
                        permission_code=permission_code,
                        result=status_code < 400,
                        request=request,
                        resource_type="API",
                        resource_id=request.url.path,
                        duration_ms=duration_ms
                    )
        except Exception as e:
            logger.error(f"记录API访问日志失败: {e}")
    
    async def _log_sensitive_operation(self, request: Request, user_info: dict, duration_ms: int, success: bool):
        """记录敏感操作日志"""
        try:
            if user_info["user_id"]:
                operation_name = f"{request.method} {request.url.path}"
                resource_type = self._extract_resource_type(request.url.path)
                resource_id = self._extract_resource_id(request.url.path)
                
                await audit_service.log_sensitive_operation(
                    user_id=user_info["user_id"],
                    username=user_info["username"],
                    operation_name=operation_name,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    request=request,
                    success=success,
                    extra_data=await self._get_request_data(request),
                    duration_ms=duration_ms
                )
        except Exception as e:
            logger.error(f"记录敏感操作日志失败: {e}")
    
    async def _log_batch_operation(self, request: Request, user_info: dict, duration_ms: int, success: bool):
        """记录批量操作日志"""
        try:
            if user_info["user_id"]:
                # 尝试从请求体中获取影响的记录数量
                request_data = await self._get_request_data(request)
                affected_count = self._estimate_affected_count(request_data)
                
                operation_type = "删除" if "delete" in request.url.path.lower() else "操作"
                resource_type = self._extract_resource_type(request.url.path)
                
                await audit_service.log_batch_operation(
                    user_id=user_info["user_id"],
                    username=user_info["username"],
                    operation_type=operation_type,
                    affected_count=affected_count,
                    resource_type=resource_type,
                    request=request,
                    success=success,
                    extra_data=request_data,
                    duration_ms=duration_ms
                )
        except Exception as e:
            logger.error(f"记录批量操作日志失败: {e}")
    
    async def _log_error_response(self, request: Request, response: Response, user_info: dict, duration_ms: int):
        """记录错误响应日志"""
        try:
            if response.status_code == 403:
                # 权限拒绝
                permission_code = f"{request.method} {request.url.path}"
                await audit_service.log_permission_check(
                    user_id=user_info["user_id"],
                    username=user_info["username"],
                    permission_code=permission_code,
                    result=False,
                    request=request,
                    resource_type="API",
                    resource_id=request.url.path,
                    duration_ms=duration_ms
                )
            elif response.status_code == 401:
                # 认证失败
                await audit_service.log_authentication(
                    user_id=user_info["user_id"],
                    username=user_info["username"],
                    action_type=audit_service.ACTION_API_ACCESS,
                    success=False,
                    request=request,
                    extra_data={"error": "认证失败"},
                    duration_ms=duration_ms
                )
        except Exception as e:
            logger.error(f"记录错误响应日志失败: {e}")
    
    def _determine_action_type(self, path: str, method: str) -> str:
        """确定操作类型"""
        if "/login" in path:
            return audit_service.ACTION_LOGIN
        elif "/logout" in path:
            return audit_service.ACTION_LOGOUT
        elif any(sensitive in path for sensitive in self.sensitive_paths):
            return audit_service.ACTION_SENSITIVE_OPERATION
        elif any(batch in path for batch in self.batch_operation_paths):
            return audit_service.ACTION_BATCH_OPERATION
        else:
            return audit_service.ACTION_API_ACCESS
    
    def _is_sensitive_operation(self, path: str, method: str) -> bool:
        """检查是否是敏感操作"""
        # 管理员相关操作
        if any(sensitive in path for sensitive in self.sensitive_paths):
            return True
        
        # 删除操作
        if method == "DELETE":
            return True
        
        # 权限相关操作
        if "permission" in path.lower() or "role" in path.lower():
            return True
        
        return False
    
    def _is_batch_operation(self, path: str, method: str) -> bool:
        """检查是否是批量操作"""
        return any(batch in path for batch in self.batch_operation_paths)
    
    def _extract_resource_type(self, path: str) -> str:
        """从路径中提取资源类型"""
        path_parts = path.strip("/").split("/")
        if len(path_parts) >= 3:
            return path_parts[2].upper()  # /api/v2/users -> USERS
        return "UNKNOWN"
    
    def _extract_resource_id(self, path: str) -> str:
        """从路径中提取资源ID"""
        path_parts = path.strip("/").split("/")
        if len(path_parts) >= 4 and path_parts[3].isdigit():
            return path_parts[3]
        return "unknown"
    
    async def _get_request_data(self, request: Request) -> dict:
        """获取请求数据"""
        try:
            # 获取查询参数
            query_params = dict(request.query_params)
            
            # 尝试获取请求体（如果是POST/PUT/PATCH）
            body_data = {}
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    # 注意：这里需要小心处理，因为请求体只能读取一次
                    # 在实际应用中，可能需要在更早的地方缓存请求体
                    content_type = request.headers.get("content-type", "")
                    if "application/json" in content_type:
                        # 这里只是示例，实际使用时需要更仔细的处理
                        pass
                except Exception:
                    pass
            
            return {
                "query_params": query_params,
                "body_data": body_data,
                "content_type": request.headers.get("content-type", ""),
                "content_length": request.headers.get("content-length", "0")
            }
        except Exception as e:
            logger.error(f"获取请求数据失败: {e}")
            return {}
    
    def _estimate_affected_count(self, request_data: dict) -> int:
        """估算影响的记录数量"""
        try:
            # 从查询参数中查找批量操作的标识
            query_params = request_data.get("query_params", {})
            
            # 检查常见的批量操作参数
            if "ids" in query_params:
                ids_str = query_params["ids"]
                if isinstance(ids_str, str):
                    return len(ids_str.split(","))
            
            if "count" in query_params:
                try:
                    return int(query_params["count"])
                except ValueError:
                    pass
            
            # 默认返回1
            return 1
        except Exception:
            return 1