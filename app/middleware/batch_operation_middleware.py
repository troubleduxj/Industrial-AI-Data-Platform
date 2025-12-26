"""
批量操作权限中间件
"""
import json
import re
from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.batch_operation_service import batch_operation_service, BatchOperationType
from app.core.auth_dependencies import get_current_user_optional
from app.core.unified_logger import get_logger

logger = get_logger(__name__)


class BatchOperationMiddleware(BaseHTTPMiddleware):
    """批量操作权限中间件"""
    
    def __init__(self, app, auto_detect: bool = True):
        super().__init__(app)
        self.auto_detect = auto_detect
        
        # 批量操作路径模式
        self.batch_patterns = [
            # 通用批量操作模式
            (r'/api/v[12]/\w+/batch[/-]?(\w+)?', 'auto'),
            (r'/api/v[12]/\w+/bulk[/-]?(\w+)?', 'auto'),
            (r'/api/v[12]/\w+/multiple[/-]?(\w+)?', 'auto'),
            
            # 特定批量操作模式
            (r'/api/v[12]/users/batch[/-]?delete', 'users.DELETE'),
            (r'/api/v[12]/users/batch[/-]?update', 'users.UPDATE'),
            (r'/api/v[12]/users/batch[/-]?deactivate', 'users.DEACTIVATE'),
            (r'/api/v[12]/roles/batch[/-]?delete', 'roles.DELETE'),
            (r'/api/v[12]/devices/batch[/-]?delete', 'devices.DELETE'),
            (r'/api/v[12]/devices/batch[/-]?update', 'devices.UPDATE'),
            (r'/api/v[12]/device/maintenance/batch[/-]?delete', 'repair_records.DELETE'),
            
            # 删除多个项目的模式
            (r'/api/v[12]/users/\d+(,\d+)+', 'users.DELETE'),
            (r'/api/v[12]/roles/\d+(,\d+)+', 'roles.DELETE'),
            (r'/api/v[12]/devices/\d+(,\d+)+', 'devices.DELETE'),
        ]
        
        # 资源类型映射
        self.resource_mapping = {
            'users': 'users',
            'user': 'users',
            'roles': 'roles',
            'role': 'roles',
            'devices': 'devices',
            'device': 'devices',
            'maintenance': 'repair_records',
            'repair-records': 'repair_records',
            'repair_records': 'repair_records'
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        # 检查是否为批量操作
        batch_info = self._detect_batch_operation(request)
        
        if not batch_info:
            return await call_next(request)
        
        # 获取用户信息
        user = await get_current_user_optional(request)
        if not user:
            return await call_next(request)  # 让认证中间件处理
        
        try:
            # 预检查批量操作权限
            await self._pre_check_batch_permission(request, batch_info, user)
            
            # 继续处理请求
            response = await call_next(request)
            
            # 后处理（记录日志等）
            await self._post_process_batch_operation(request, response, batch_info, user)
            
            return response
            
        except HTTPException as e:
            # 返回权限错误
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "success": False,
                    "code": e.status_code,
                    "message": str(e.detail),
                    "data": None
                }
            )
        except Exception as e:
            logger.error(f"批量操作中间件处理失败: {e}")
            return await call_next(request)
    
    def _detect_batch_operation(self, request: Request) -> Optional[Dict[str, Any]]:
        """检测批量操作"""
        if not self.auto_detect:
            return None
        
        path = request.url.path
        method = request.method
        
        # 只处理可能的批量操作方法
        if method not in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return None
        
        # 检查路径模式
        for pattern, operation_info in self.batch_patterns:
            match = re.search(pattern, path, re.IGNORECASE)
            if match:
                return self._parse_batch_info(path, method, operation_info, match)
        
        return None
    
    def _parse_batch_info(self, path: str, method: str, operation_info: str, match) -> Dict[str, Any]:
        """解析批量操作信息"""
        if operation_info == 'auto':
            # 自动检测资源类型和操作类型
            resource_type = self._extract_resource_type(path)
            operation_type = self._map_method_to_operation(method)
        else:
            # 使用预定义的操作信息
            parts = operation_info.split('.')
            resource_type = parts[0]
            operation_type = BatchOperationType(parts[1]) if len(parts) > 1 else self._map_method_to_operation(method)
        
        return {
            'resource_type': resource_type,
            'operation_type': operation_type,
            'path': path,
            'method': method,
            'pattern_match': match
        }
    
    def _extract_resource_type(self, path: str) -> str:
        """从路径中提取资源类型"""
        # 提取路径中的资源名称
        parts = path.strip('/').split('/')
        
        # 查找API版本后的第一个资源名称
        for i, part in enumerate(parts):
            if part.startswith('v') and part[1:].isdigit():
                if i + 1 < len(parts):
                    resource_name = parts[i + 1]
                    return self.resource_mapping.get(resource_name, resource_name)
        
        # 默认返回unknown
        return 'unknown'
    
    def _map_method_to_operation(self, method: str) -> BatchOperationType:
        """将HTTP方法映射到操作类型"""
        mapping = {
            'DELETE': BatchOperationType.DELETE,
            'POST': BatchOperationType.CREATE,
            'PUT': BatchOperationType.UPDATE,
            'PATCH': BatchOperationType.UPDATE
        }
        return mapping.get(method, BatchOperationType.UPDATE)
    
    async def _pre_check_batch_permission(self, request: Request, batch_info: Dict[str, Any], user):
        """预检查批量操作权限"""
        try:
            # 尝试从请求中获取项目ID列表
            item_ids = await self._extract_item_ids(request, batch_info)
            
            if not item_ids:
                return  # 没有找到项目ID，跳过检查
            
            # 如果项目数量较少，跳过中间件检查（让装饰器处理）
            if len(item_ids) < 5:
                return
            
            # 执行快速权限检查
            from app.services.batch_operation_service import BatchOperationRequest
            
            batch_request = BatchOperationRequest(
                user_id=user.id,
                resource_type=batch_info['resource_type'],
                operation_type=batch_info['operation_type'],
                item_ids=item_ids
            )
            
            # 只检查基础权限和数量限制，不进行详细的项目过滤
            rule = batch_operation_service._get_operation_rule(
                batch_info['resource_type'], 
                batch_info['operation_type']
            )
            
            if rule:
                # 检查基础权限
                has_permission = await batch_operation_service._check_basic_permissions(user, rule)
                if not has_permission:
                    raise HTTPException(
                        status_code=403,
                        detail=f"用户缺少执行批量{batch_info['operation_type'].value}操作的权限"
                    )
                
                # 检查数量限制
                if len(item_ids) > rule.max_items:
                    raise HTTPException(
                        status_code=400,
                        detail=f"批量操作数量超出限制，最大允许 {rule.max_items} 项，请求 {len(item_ids)} 项"
                    )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"批量操作预检查失败: {e}")
            # 预检查失败不阻止请求，让后续处理
    
    async def _extract_item_ids(self, request: Request, batch_info: Dict[str, Any]) -> Optional[list]:
        """从请求中提取项目ID列表"""
        try:
            # 从查询参数中获取
            if 'ids' in request.query_params:
                ids_str = request.query_params['ids']
                return [int(id.strip()) for id in ids_str.split(',') if id.strip().isdigit()]
            
            # 从请求体中获取
            if request.method in ['POST', 'PUT', 'PATCH']:
                # 注意：这里需要小心处理，因为请求体只能读取一次
                # 在实际应用中，可能需要在更早的地方缓存请求体
                content_type = request.headers.get('content-type', '')
                if 'application/json' in content_type:
                    # 这里只是示例，实际使用时需要更仔细的处理
                    pass
            
            # 从URL路径中提取（如 /users/1,2,3）
            path_match = re.search(r'/(\d+(?:,\d+)+)/?$', batch_info['path'])
            if path_match:
                ids_str = path_match.group(1)
                return [int(id.strip()) for id in ids_str.split(',') if id.strip().isdigit()]
            
        except Exception as e:
            logger.warning(f"提取项目ID失败: {e}")
        
        return None
    
    async def _post_process_batch_operation(self, request: Request, response: Response, batch_info: Dict[str, Any], user):
        """批量操作后处理"""
        try:
            # 记录批量操作日志
            if response.status_code < 400:
                logger.info(f"批量操作成功: 用户{user.username}, 资源{batch_info['resource_type']}, 操作{batch_info['operation_type'].value}")
            else:
                logger.warning(f"批量操作失败: 用户{user.username}, 资源{batch_info['resource_type']}, 操作{batch_info['operation_type'].value}, 状态码{response.status_code}")
        
        except Exception as e:
            logger.error(f"批量操作后处理失败: {e}")


class BatchOperationConfig:
    """批量操作配置"""
    
    def __init__(self):
        self.enabled = True
        self.auto_detect = True
        self.max_items_global = 1000
        self.require_reason_for_critical = True
        self.audit_all_operations = True
    
    def update_config(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


# 全局批量操作配置
batch_operation_config = BatchOperationConfig()