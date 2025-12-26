#!/usr/bin/env python3
"""
API兼容性适配器
提供v1到v2 API的兼容性支持，确保现有客户端可以无缝迁移
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class APIMapping:
    """API映射配置"""
    v1_path: str
    v2_path: str
    method: str
    request_mapper: Optional[str] = None
    response_mapper: Optional[str] = None
    deprecated: bool = False
    removal_date: Optional[str] = None

class APICompatibilityAdapter:
    """API兼容性适配器"""
    
    def __init__(self):
        self.mappings = self._load_api_mappings()
        self.request_mappers = self._init_request_mappers()
        self.response_mappers = self._init_response_mappers()
    
    def _load_api_mappings(self) -> Dict[str, APIMapping]:
        """加载API映射配置"""
        mappings = {
            # 用户管理API映射
            "GET:/user/list": APIMapping(
                v1_path="/user/list",
                v2_path="/api/v2/users",
                method="GET",
                request_mapper="map_user_list_request",
                response_mapper="map_user_list_response"
            ),
            "POST:/user/create": APIMapping(
                v1_path="/user/create",
                v2_path="/api/v2/users",
                method="POST",
                request_mapper="map_user_create_request",
                response_mapper="map_user_create_response"
            ),
            "PUT:/user/update": APIMapping(
                v1_path="/user/update",
                v2_path="/api/v2/users/{id}",
                method="PUT",
                request_mapper="map_user_update_request",
                response_mapper="map_user_update_response"
            ),
            "DELETE:/user/delete": APIMapping(
                v1_path="/user/delete",
                v2_path="/api/v2/users/{id}",
                method="DELETE",
                request_mapper="map_user_delete_request",
                response_mapper="map_user_delete_response"
            ),
            "GET:/user/info": APIMapping(
                v1_path="/user/info",
                v2_path="/api/v2/users/{id}",
                method="GET",
                request_mapper="map_user_info_request",
                response_mapper="map_user_info_response"
            ),
            
            # 角色管理API映射
            "GET:/role/list": APIMapping(
                v1_path="/role/list",
                v2_path="/api/v2/roles",
                method="GET",
                request_mapper="map_role_list_request",
                response_mapper="map_role_list_response"
            ),
            "POST:/role/create": APIMapping(
                v1_path="/role/create",
                v2_path="/api/v2/roles",
                method="POST",
                request_mapper="map_role_create_request",
                response_mapper="map_role_create_response"
            ),
            
            # 设备管理API映射
            "GET:/device/list": APIMapping(
                v1_path="/device/list",
                v2_path="/api/v2/devices",
                method="GET",
                request_mapper="map_device_list_request",
                response_mapper="map_device_list_response"
            ),
            "POST:/device/create": APIMapping(
                v1_path="/device/create",
                v2_path="/api/v2/devices",
                method="POST",
                request_mapper="map_device_create_request",
                response_mapper="map_device_create_response"
            ),
            
            # 菜单管理API映射
            "GET:/menu/list": APIMapping(
                v1_path="/menu/list",
                v2_path="/api/v2/menus",
                method="GET",
                request_mapper="map_menu_list_request",
                response_mapper="map_menu_list_response"
            ),
            "GET:/menu/tree": APIMapping(
                v1_path="/menu/tree",
                v2_path="/api/v2/menus/tree",
                method="GET",
                request_mapper="map_menu_tree_request",
                response_mapper="map_menu_tree_response"
            ),
            
            # 部门管理API映射
            "GET:/dept/list": APIMapping(
                v1_path="/dept/list",
                v2_path="/api/v2/departments",
                method="GET",
                request_mapper="map_dept_list_request",
                response_mapper="map_dept_list_response"
            ),
            "GET:/dept/tree": APIMapping(
                v1_path="/dept/tree",
                v2_path="/api/v2/departments/tree",
                method="GET",
                request_mapper="map_dept_tree_request",
                response_mapper="map_dept_tree_response"
            ),
        }
        
        return mappings
    
    def _init_request_mappers(self) -> Dict[str, callable]:
        """初始化请求映射器"""
        return {
            "map_user_list_request": self._map_user_list_request,
            "map_user_create_request": self._map_user_create_request,
            "map_user_update_request": self._map_user_update_request,
            "map_user_delete_request": self._map_user_delete_request,
            "map_user_info_request": self._map_user_info_request,
            "map_role_list_request": self._map_role_list_request,
            "map_role_create_request": self._map_role_create_request,
            "map_device_list_request": self._map_device_list_request,
            "map_device_create_request": self._map_device_create_request,
            "map_menu_list_request": self._map_menu_list_request,
            "map_menu_tree_request": self._map_menu_tree_request,
            "map_dept_list_request": self._map_dept_list_request,
            "map_dept_tree_request": self._map_dept_tree_request,
        }
    
    def _init_response_mappers(self) -> Dict[str, callable]:
        """初始化响应映射器"""
        return {
            "map_user_list_response": self._map_user_list_response,
            "map_user_create_response": self._map_user_create_response,
            "map_user_update_response": self._map_user_update_response,
            "map_user_delete_response": self._map_user_delete_response,
            "map_user_info_response": self._map_user_info_response,
            "map_role_list_response": self._map_role_list_response,
            "map_role_create_response": self._map_role_create_response,
            "map_device_list_response": self._map_device_list_response,
            "map_device_create_response": self._map_device_create_response,
            "map_menu_list_response": self._map_menu_list_response,
            "map_menu_tree_response": self._map_menu_tree_response,
            "map_dept_list_response": self._map_dept_list_response,
            "map_dept_tree_response": self._map_dept_tree_response,
        }
    
    def get_v2_mapping(self, v1_method: str, v1_path: str) -> Optional[APIMapping]:
        """获取v1到v2的API映射"""
        key = f"{v1_method}:{v1_path}"
        return self.mappings.get(key)
    
    def map_request(self, mapping: APIMapping, v1_request: Dict[str, Any]) -> Dict[str, Any]:
        """映射v1请求到v2格式"""
        if mapping.request_mapper and mapping.request_mapper in self.request_mappers:
            mapper = self.request_mappers[mapping.request_mapper]
            return mapper(v1_request)
        return v1_request
    
    def map_response(self, mapping: APIMapping, v2_response: Dict[str, Any]) -> Dict[str, Any]:
        """映射v2响应到v1格式"""
        if mapping.response_mapper and mapping.response_mapper in self.response_mappers:
            mapper = self.response_mappers[mapping.response_mapper]
            return mapper(v2_response)
        return v2_response
    
    # 用户管理请求映射器
    def _map_user_list_request(self, v1_request: Dict[str, Any]) -> Dict[str, Any]:
        """映射用户列表请求"""
        v2_request = {}
        
        # 分页参数映射
        if 'page' in v1_request:
            v2_request['page'] = v1_request['page']
        if 'limit' in v1_request:
            v2_request['size'] = v1_request['limit']
        elif 'page_size' in v1_request:
            v2_request['size'] = v1_request['page_size']
        
        # 搜索参数映射
        if 'search' in v1_request:
            v2_request['search'] = v1_request['search']
        if 'username' in v1_request:
            v2_request['filter[username]'] = v1_request['username']
        if 'status' in v1_request:
            v2_request['filter[status]'] = v1_request['status']
        if 'dept_id' in v1_request:
            v2_request['filter[department_id]'] = v1_request['dept_id']
        
        # 排序参数映射
        if 'order_by' in v1_request:
            order = v1_request.get('order', 'asc')
            v2_request['sort'] = f"{v1_request['order_by']}:{order}"
        
        return v2_request
    
    def _map_user_create_request(self, v1_request: Dict[str, Any]) -> Dict[str, Any]:
        """映射用户创建请求"""
        v2_request = {}
        
        # 基本字段映射
        field_mapping = {
            'username': 'username',
            'alias': 'displayName',
            'email': 'email',
            'phone': 'phone',
            'password': 'password',
            'is_active': 'status',
            'dept_id': 'departmentId'
        }
        
        for v1_field, v2_field in field_mapping.items():
            if v1_field in v1_request:
                if v1_field == 'is_active':
                    v2_request[v2_field] = 'active' if v1_request[v1_field] else 'inactive'
                else:
                    v2_request[v2_field] = v1_request[v1_field]
        
        # 角色映射
        if 'role_ids' in v1_request:
            v2_request['roleIds'] = v1_request['role_ids']
        
        return v2_request
    
    def _map_user_update_request(self, v1_request: Dict[str, Any]) -> Dict[str, Any]:
        """映射用户更新请求"""
        return self._map_user_create_request(v1_request)
    
    def _map_user_delete_request(self, v1_request: Dict[str, Any]) -> Dict[str, Any]:
        """映射用户删除请求"""
        # v1通常通过查询参数传递ID，v2通过路径参数
        return {}
    
    def _map_user_info_request(self, v1_request: Dict[str, Any]) -> Dict[str, Any]:
        """映射用户信息请求"""
        return {}
    
    # 用户管理响应映射器
    def _map_user_list_response(self, v2_response: Dict[str, Any]) -> Dict[str, Any]:
        """映射用户列表响应"""
        if not v2_response.get('success', True):
            return self._map_error_response(v2_response)
        
        v1_response = {
            'code': 200,
            'message': 'success',
            'data': []
        }
        
        # 映射用户数据
        if 'data' in v2_response and isinstance(v2_response['data'], list):
            v1_response['data'] = []
            for user in v2_response['data']:
                v1_user = {
                    'id': user.get('id'),
                    'username': user.get('username'),
                    'alias': user.get('displayName'),
                    'email': user.get('email'),
                    'phone': user.get('phone'),
                    'is_active': user.get('status') == 'active',
                    'dept_id': user.get('departmentId'),
                    'created_at': user.get('createdAt'),
                    'updated_at': user.get('updatedAt')
                }
                v1_response['data'].append(v1_user)
        
        # 映射分页信息
        if 'meta' in v2_response and 'pagination' in v2_response['meta']:
            pagination = v2_response['meta']['pagination']
            v1_response['total'] = pagination.get('total', 0)
            v1_response['page'] = pagination.get('page', 1)
            v1_response['page_size'] = pagination.get('size', 20)
            v1_response['total_pages'] = pagination.get('pages', 1)
        
        return v1_response
    
    def _map_user_create_response(self, v2_response: Dict[str, Any]) -> Dict[str, Any]:
        """映射用户创建响应"""
        if not v2_response.get('success', True):
            return self._map_error_response(v2_response)
        
        v1_response = {
            'code': 200,
            'message': v2_response.get('message', '用户创建成功'),
            'data': {}
        }
        
        if 'data' in v2_response:
            user = v2_response['data']
            v1_response['data'] = {
                'id': user.get('id'),
                'username': user.get('username'),
                'alias': user.get('displayName'),
                'email': user.get('email'),
                'phone': user.get('phone'),
                'is_active': user.get('status') == 'active',
                'dept_id': user.get('departmentId'),
                'created_at': user.get('createdAt')
            }
        
        return v1_response
    
    def _map_user_update_response(self, v2_response: Dict[str, Any]) -> Dict[str, Any]:
        """映射用户更新响应"""
        return self._map_user_create_response(v2_response)
    
    def _map_user_delete_response(self, v2_response: Dict[str, Any]) -> Dict[str, Any]:
        """映射用户删除响应"""
        if not v2_response.get('success', True):
            return self._map_error_response(v2_response)
        
        return {
            'code': 200,
            'message': v2_response.get('message', '用户删除成功'),
            'data': None
        }
    
    def _map_user_info_response(self, v2_response: Dict[str, Any]) -> Dict[str, Any]:
        """映射用户信息响应"""
        return self._map_user_create_response(v2_response)
    
    # 角色管理映射器（简化实现）
    def _map_role_list_request(self, v1_request: Dict[str, Any]) -> Dict[str, Any]:
        """映射角色列表请求"""
        return self._map_user_list_request(v1_request)
    
    def _map_role_create_request(self, v1_request: Dict[str, Any]) -> Dict[str, Any]:
        """映射角色创建请求"""
        v2_request = {}
        field_mapping = {
            'name': 'name',
            'desc': 'description',
            'menu_ids': 'menuIds',
            'api_ids': 'permissionIds'
        }
        
        for v1_field, v2_field in field_mapping.items():
            if v1_field in v1_request:
                v2_request[v2_field] = v1_request[v1_field]
        
        return v2_request
    
    def _map_role_list_response(self, v2_response: Dict[str, Any]) -> Dict[str, Any]:
        """映射角色列表响应"""
        if not v2_response.get('success', True):
            return self._map_error_response(v2_response)
        
        v1_response = {
            'code': 200,
            'message': 'success',
            'data': []
        }
        
        if 'data' in v2_response and isinstance(v2_response['data'], list):
            v1_response['data'] = []
            for role in v2_response['data']:
                v1_role = {
                    'id': role.get('id'),
                    'name': role.get('name'),
                    'desc': role.get('description'),
                    'created_at': role.get('createdAt'),
                    'updated_at': role.get('updatedAt')
                }
                v1_response['data'].append(v1_role)
        
        return v1_response
    
    def _map_role_create_response(self, v2_response: Dict[str, Any]) -> Dict[str, Any]:
        """映射角色创建响应"""
        if not v2_response.get('success', True):
            return self._map_error_response(v2_response)
        
        v1_response = {
            'code': 200,
            'message': v2_response.get('message', '角色创建成功'),
            'data': {}
        }
        
        if 'data' in v2_response:
            role = v2_response['data']
            v1_response['data'] = {
                'id': role.get('id'),
                'name': role.get('name'),
                'desc': role.get('description'),
                'created_at': role.get('createdAt')
            }
        
        return v1_response
    
    # 设备管理映射器（简化实现）
    def _map_device_list_request(self, v1_request: Dict[str, Any]) -> Dict[str, Any]:
        """映射设备列表请求"""
        v2_request = {}
        
        # 分页参数
        if 'page' in v1_request:
            v2_request['page'] = v1_request['page']
        if 'limit' in v1_request:
            v2_request['size'] = v1_request['limit']
        
        # 过滤参数
        if 'device_name' in v1_request:
            v2_request['filter[name]'] = v1_request['device_name']
        if 'device_type' in v1_request:
            v2_request['filter[type]'] = v1_request['device_type']
        if 'status' in v1_request:
            v2_request['filter[status]'] = v1_request['status']
        
        return v2_request
    
    def _map_device_create_request(self, v1_request: Dict[str, Any]) -> Dict[str, Any]:
        """映射设备创建请求"""
        v2_request = {}
        field_mapping = {
            'device_name': 'name',
            'device_code': 'code',
            'device_type': 'typeId',
            'device_model': 'model',
            'manufacturer': 'manufacturer',
            'install_location': 'location',
            'description': 'description'
        }
        
        for v1_field, v2_field in field_mapping.items():
            if v1_field in v1_request:
                v2_request[v2_field] = v1_request[v1_field]
        
        return v2_request
    
    def _map_device_list_response(self, v2_response: Dict[str, Any]) -> Dict[str, Any]:
        """映射设备列表响应"""
        if not v2_response.get('success', True):
            return self._map_error_response(v2_response)
        
        v1_response = {
            'code': 200,
            'message': 'success',
            'data': []
        }
        
        if 'data' in v2_response and isinstance(v2_response['data'], list):
            v1_response['data'] = []
            for device in v2_response['data']:
                v1_device = {
                    'id': device.get('id'),
                    'device_name': device.get('name'),
                    'device_code': device.get('code'),
                    'device_type': device.get('type'),
                    'device_model': device.get('model'),
                    'manufacturer': device.get('manufacturer'),
                    'install_location': device.get('location'),
                    'status': device.get('status'),
                    'created_at': device.get('createdAt'),
                    'updated_at': device.get('updatedAt')
                }
                v1_response['data'].append(v1_device)
        
        return v1_response
    
    def _map_device_create_response(self, v2_response: Dict[str, Any]) -> Dict[str, Any]:
        """映射设备创建响应"""
        if not v2_response.get('success', True):
            return self._map_error_response(v2_response)
        
        v1_response = {
            'code': 200,
            'message': v2_response.get('message', '设备创建成功'),
            'data': {}
        }
        
        if 'data' in v2_response:
            device = v2_response['data']
            v1_response['data'] = {
                'id': device.get('id'),
                'device_name': device.get('name'),
                'device_code': device.get('code'),
                'device_type': device.get('type'),
                'created_at': device.get('createdAt')
            }
        
        return v1_response
    
    # 菜单和部门管理映射器（简化实现）
    def _map_menu_list_request(self, v1_request: Dict[str, Any]) -> Dict[str, Any]:
        """映射菜单列表请求"""
        return {}
    
    def _map_menu_tree_request(self, v1_request: Dict[str, Any]) -> Dict[str, Any]:
        """映射菜单树请求"""
        return {}
    
    def _map_dept_list_request(self, v1_request: Dict[str, Any]) -> Dict[str, Any]:
        """映射部门列表请求"""
        return {}
    
    def _map_dept_tree_request(self, v1_request: Dict[str, Any]) -> Dict[str, Any]:
        """映射部门树请求"""
        return {}
    
    def _map_menu_list_response(self, v2_response: Dict[str, Any]) -> Dict[str, Any]:
        """映射菜单列表响应"""
        return self._map_generic_list_response(v2_response, 'menu')
    
    def _map_menu_tree_response(self, v2_response: Dict[str, Any]) -> Dict[str, Any]:
        """映射菜单树响应"""
        return self._map_generic_response(v2_response)
    
    def _map_dept_list_response(self, v2_response: Dict[str, Any]) -> Dict[str, Any]:
        """映射部门列表响应"""
        return self._map_generic_list_response(v2_response, 'dept')
    
    def _map_dept_tree_response(self, v2_response: Dict[str, Any]) -> Dict[str, Any]:
        """映射部门树响应"""
        return self._map_generic_response(v2_response)
    
    # 通用映射器
    def _map_generic_response(self, v2_response: Dict[str, Any]) -> Dict[str, Any]:
        """通用响应映射"""
        if not v2_response.get('success', True):
            return self._map_error_response(v2_response)
        
        return {
            'code': 200,
            'message': v2_response.get('message', 'success'),
            'data': v2_response.get('data', {})
        }
    
    def _map_generic_list_response(self, v2_response: Dict[str, Any], resource_type: str) -> Dict[str, Any]:
        """通用列表响应映射"""
        if not v2_response.get('success', True):
            return self._map_error_response(v2_response)
        
        v1_response = {
            'code': 200,
            'message': 'success',
            'data': v2_response.get('data', [])
        }
        
        # 添加分页信息
        if 'meta' in v2_response and 'pagination' in v2_response['meta']:
            pagination = v2_response['meta']['pagination']
            v1_response['total'] = pagination.get('total', 0)
            v1_response['page'] = pagination.get('page', 1)
            v1_response['page_size'] = pagination.get('size', 20)
        
        return v1_response
    
    def _map_error_response(self, v2_response: Dict[str, Any]) -> Dict[str, Any]:
        """映射错误响应"""
        error = v2_response.get('error', {})
        
        # 映射错误码
        error_code_mapping = {
            'VALIDATION_ERROR': 400,
            'AUTHENTICATION_FAILED': 401,
            'PERMISSION_DENIED': 403,
            'RESOURCE_NOT_FOUND': 404,
            'RESOURCE_CONFLICT': 409,
            'INTERNAL_SERVER_ERROR': 500
        }
        
        code = error_code_mapping.get(error.get('code'), 500)
        
        v1_response = {
            'code': code,
            'message': error.get('message', '操作失败'),
            'data': None
        }
        
        # 添加详细错误信息
        if 'details' in error:
            v1_response['errors'] = error['details']
        
        return v1_response
    
    def is_deprecated(self, v1_method: str, v1_path: str) -> bool:
        """检查API是否已废弃"""
        mapping = self.get_v2_mapping(v1_method, v1_path)
        return mapping.deprecated if mapping else False
    
    def get_deprecation_info(self, v1_method: str, v1_path: str) -> Optional[Dict[str, Any]]:
        """获取废弃信息"""
        mapping = self.get_v2_mapping(v1_method, v1_path)
        if mapping and mapping.deprecated:
            return {
                'deprecated': True,
                'removal_date': mapping.removal_date,
                'replacement': mapping.v2_path,
                'message': f'API {v1_path} 已废弃，请使用 {mapping.v2_path} 替代'
            }
        return None

# 全局适配器实例
compatibility_adapter = APICompatibilityAdapter()