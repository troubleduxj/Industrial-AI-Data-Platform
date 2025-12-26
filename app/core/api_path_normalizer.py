#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API路径标准化器
将旧API路径转换为新的RESTful v2格式，支持路径标准化和验证功能
"""

import re
from typing import Dict, List, Optional, Tuple, Set
from urllib.parse import urlparse, parse_qs

from app.log import logger


class APIPathNormalizer:
    """API路径标准化器"""
    
    def __init__(self):
        # API v2标准化规则
        self.normalization_rules = {
            # 用户管理 - 升级到v2
            '/user/list': '/api/v2/users',
            '/user/create': '/api/v2/users',
            '/user/update': '/api/v2/users/{id}',
            '/user/delete': '/api/v2/users/{id}',
            '/user/reset_password': '/api/v2/users/{id}/reset-password',
            '/user/info': '/api/v2/users/{id}',
            '/user/profile': '/api/v2/users/{id}',
            
            # 角色管理 - 升级到v2
            '/role/list': '/api/v2/roles',
            '/role/create': '/api/v2/roles',
            '/role/update': '/api/v2/roles/{id}',
            '/role/delete': '/api/v2/roles/{id}',
            '/role/permissions': '/api/v2/roles/{id}/permissions',
            '/role/users': '/api/v2/roles/{id}/users',
            
            # 菜单管理 - 升级到v2
            '/menu/list': '/api/v2/menus',
            '/menu/create': '/api/v2/menus',
            '/menu/update': '/api/v2/menus/{id}',
            '/menu/delete': '/api/v2/menus/{id}',
            '/menu/tree': '/api/v2/menus/tree',
            
            # 部门管理 - 升级到v2
            '/dept/list': '/api/v2/departments',
            '/dept/create': '/api/v2/departments',
            '/dept/update': '/api/v2/departments/{id}',
            '/dept/delete': '/api/v2/departments/{id}',
            '/dept/tree': '/api/v2/departments/tree',
            
            # 设备管理 - 升级到v2
            '/device/list': '/api/v2/devices',
            '/device/create': '/api/v2/devices',
            '/device/update': '/api/v2/devices/{id}',
            '/device/delete': '/api/v2/devices/{id}',
            '/device/info': '/api/v2/devices/{id}',
            '/device/status': '/api/v2/devices/{id}/status',
            '/device/statistics': '/api/v2/devices/statistics',
            
            # 设备类型归并到设备模块 - v2
            '/device/types': '/api/v2/devices/types',
            '/device/type/list': '/api/v2/devices/types',
            '/device/type/create': '/api/v2/devices/types',
            '/device/type/update': '/api/v2/devices/types/{id}',
            '/device/type/delete': '/api/v2/devices/types/{id}',
            
            # 设备维护 - v2
            '/device/maintenance': '/api/v2/devices/{id}/maintenance',
            '/device/maintenance/list': '/api/v2/devices/{id}/maintenance',
            '/device/maintenance/create': '/api/v2/devices/{id}/maintenance',
            '/device/maintenance/update': '/api/v2/devices/maintenance/{id}',
            '/device/maintenance/delete': '/api/v2/devices/maintenance/{id}',
            '/device/maintenance/schedule': '/api/v2/devices/maintenance/schedule',
            
            # AI监控模块 - v2
            '/ai/predictions': '/api/v2/ai/predictions',
            '/ai/prediction/list': '/api/v2/ai/predictions',
            '/ai/prediction/create': '/api/v2/ai/predictions',
            '/ai/prediction/update': '/api/v2/ai/predictions/{id}',
            '/ai/prediction/delete': '/api/v2/ai/predictions/{id}',
            '/ai/prediction/export': '/api/v2/ai/predictions/{id}/export',
            
            '/ai/models': '/api/v2/ai/models',
            '/ai/model/list': '/api/v2/ai/models',
            '/ai/model/create': '/api/v2/ai/models',
            '/ai/model/update': '/api/v2/ai/models/{id}',
            '/ai/model/delete': '/api/v2/ai/models/{id}',
            '/ai/model/train': '/api/v2/ai/models/{id}/train',
            
            '/ai/annotations': '/api/v2/ai/annotations',
            '/ai/annotation/list': '/api/v2/ai/annotations',
            '/ai/annotation/create': '/api/v2/ai/annotations',
            '/ai/annotation/update': '/api/v2/ai/annotations/{id}',
            '/ai/annotation/delete': '/api/v2/ai/annotations/{id}',
            
            '/ai/health-scores': '/api/v2/ai/health-scores',
            '/ai/health/list': '/api/v2/ai/health-scores',
            '/ai/health/create': '/api/v2/ai/health-scores',
            '/ai/health/update': '/api/v2/ai/health-scores/{id}',
            '/ai/health/delete': '/api/v2/ai/health-scores/{id}',
            
            # 统计分析 - v2
            '/statistics/online-rate': '/api/v2/statistics/online-rate',
            '/statistics/weld-records': '/api/v2/statistics/weld-records',
            '/statistics/weld-time': '/api/v2/statistics/weld-time',
            '/statistics/welding-reports': '/api/v2/statistics/welding-reports',
            '/statistics/dashboard': '/api/v2/statistics/dashboard',
            
            # 仪表板 - v2
            '/dashboard/overview': '/api/v2/dashboard/overview',
            '/dashboard/device-stats': '/api/v2/dashboard/device-stats',
            '/dashboard/alarm-stats': '/api/v2/dashboard/alarm-stats',
            '/dashboard/widgets': '/api/v2/dashboard/widgets',
            
            # 报警管理 - v2
            '/alarms': '/api/v2/alarms',
            '/alarm/list': '/api/v2/alarms',
            '/alarm/handle': '/api/v2/alarms/{id}/handle',
            '/alarm/batch-handle': '/api/v2/alarms/batch-handle',
            '/alarm/acknowledge': '/api/v2/alarms/{id}/acknowledge',
            '/alarm/statistics': '/api/v2/alarms/statistics',
            
            # 保持v1兼容性映射
            '/api/v1/users': '/api/v2/users',
            '/api/v1/roles': '/api/v2/roles',
            '/api/v1/menus': '/api/v2/menus',
            '/api/v1/departments': '/api/v2/departments',
            '/api/v1/devices': '/api/v2/devices',
        }
        
        # HTTP方法映射规则
        self.method_mapping = {
            'GET': {
                'list': '',  # GET /resource/list -> GET /api/v2/resources
                'info': '/{id}',  # GET /resource/info -> GET /api/v2/resources/{id}
                'detail': '/{id}',
                'show': '/{id}',
            },
            'POST': {
                'create': '',  # POST /resource/create -> POST /api/v2/resources
                'add': '',
                'new': '',
            },
            'PUT': {
                'update': '/{id}',  # PUT /resource/update -> PUT /api/v2/resources/{id}
                'edit': '/{id}',
                'modify': '/{id}',
            },
            'DELETE': {
                'delete': '/{id}',  # DELETE /resource/delete -> DELETE /api/v2/resources/{id}
                'remove': '/{id}',
                'destroy': '/{id}',
            }
        }
        
        # 资源名称复数化规则
        self.pluralization_rules = {
            'user': 'users',
            'role': 'roles',
            'menu': 'menus',
            'dept': 'departments',
            'department': 'departments',
            'device': 'devices',
            'api': 'apis',
            'permission': 'permissions',
            'alarm': 'alarms',
            'statistic': 'statistics',
            'prediction': 'predictions',
            'model': 'models',
            'annotation': 'annotations',
            'analysis': 'analysis',  # 不变
            'data': 'data',  # 不变
        }
        
        # 路径验证正则表达式
        self.path_patterns = {
            'v2_api': re.compile(r'^/api/v2/[a-z0-9\-]+(/[a-z0-9\-{}]+)*$'),
            'resource_id': re.compile(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}'),
            'valid_segment': re.compile(r'^[a-z0-9\-]+$'),
        }
    
    def normalize_path(self, old_path: str, method: str = 'GET') -> str:
        """
        标准化API路径
        
        Args:
            old_path: 旧API路径
            method: HTTP方法
            
        Returns:
            标准化后的v2 API路径
        """
        try:
            # 移除查询参数
            clean_path = old_path.split('?')[0].rstrip('/')
            
            # 直接映射查找
            if clean_path in self.normalization_rules:
                return self.normalization_rules[clean_path]
            
            # 如果已经是v2格式，验证并返回
            if self.is_v2_format(clean_path):
                if self.validate_path_format(clean_path):
                    return clean_path
                else:
                    logger.warning(f"v2路径格式不正确: {clean_path}")
                    return clean_path  # 返回原路径，让调用者处理
            
            # 模式匹配转换
            normalized_path = self._pattern_normalize(clean_path, method)
            if normalized_path:
                return normalized_path
            
            # 智能转换
            smart_normalized = self._smart_normalize(clean_path, method)
            if smart_normalized:
                return smart_normalized
            
            logger.warning(f"无法标准化路径: {old_path}")
            return old_path
            
        except Exception as e:
            logger.error(f"路径标准化失败: {old_path}, 错误: {str(e)}")
            return old_path
    
    def _pattern_normalize(self, path: str, method: str) -> Optional[str]:
        """
        模式匹配标准化
        
        Args:
            path: 路径
            method: HTTP方法
            
        Returns:
            标准化路径或None
        """
        try:
            # 解析路径段
            segments = [s for s in path.split('/') if s]
            if not segments:
                return None
            
            # 识别资源和操作
            resource = segments[0]
            action = segments[1] if len(segments) > 1 else None
            
            # 获取复数形式的资源名
            plural_resource = self.pluralization_rules.get(resource, resource + 's')
            
            # 构建基础路径
            base_path = f"/api/v2/{plural_resource}"
            
            # 根据方法和操作确定完整路径
            if method in self.method_mapping and action in self.method_mapping[method]:
                suffix = self.method_mapping[method][action]
                return base_path + suffix
            
            # 特殊操作处理
            if action:
                return self._handle_special_action(base_path, action, method)
            
            return base_path
            
        except Exception as e:
            logger.error(f"模式匹配标准化失败: {path}, 错误: {str(e)}")
            return None
    
    def _smart_normalize(self, path: str, method: str) -> Optional[str]:
        """
        智能标准化转换
        
        Args:
            path: 路径
            method: HTTP方法
            
        Returns:
            标准化路径或None
        """
        try:
            # 移除常见前缀
            clean_path = path
            prefixes_to_remove = ['/api/v1', '/api', '/v1']
            for prefix in prefixes_to_remove:
                if clean_path.startswith(prefix):
                    clean_path = clean_path[len(prefix):]
                    break
            
            # 确保以/开头
            if not clean_path.startswith('/'):
                clean_path = '/' + clean_path
            
            # 递归尝试模式匹配
            return self._pattern_normalize(clean_path, method)
            
        except Exception as e:
            logger.error(f"智能标准化失败: {path}, 错误: {str(e)}")
            return None
    
    def _handle_special_action(self, base_path: str, action: str, method: str) -> str:
        """
        处理特殊操作
        
        Args:
            base_path: 基础路径
            action: 操作名称
            method: HTTP方法
            
        Returns:
            完整路径
        """
        # 特殊操作映射
        special_actions = {
            'reset_password': '/reset-password',
            'reset-password': '/reset-password',
            'change_password': '/change-password',
            'permissions': '/permissions',
            'roles': '/roles',
            'users': '/users',
            'tree': '/tree',
            'statistics': '/statistics',
            'status': '/status',
            'export': '/export',
            'import': '/import',
            'batch': '/batch',
            'search': '/search',
            'schedule': '/schedule',
            'train': '/train',
            'predict': '/predict',
            'analyze': '/analyze',
            'handle': '/handle',
            'acknowledge': '/acknowledge',
        }
        
        if action in special_actions:
            if method in ['PUT', 'DELETE', 'PATCH'] and action not in ['tree', 'statistics', 'batch', 'search']:
                return base_path + '/{id}' + special_actions[action]
            else:
                return base_path + special_actions[action]
        
        # 默认处理
        if method in ['PUT', 'DELETE', 'PATCH']:
            return base_path + '/{id}'
        else:
            return base_path + f'/{action}'
    
    def is_v2_format(self, path: str) -> bool:
        """
        检查路径是否为v2格式
        
        Args:
            path: API路径
            
        Returns:
            是否为v2格式
        """
        return path.startswith('/api/v2/')
    
    def validate_path_format(self, path: str) -> bool:
        """
        验证路径格式是否符合v2标准
        
        Args:
            path: API路径
            
        Returns:
            格式是否正确
        """
        try:
            # 检查基本v2格式
            if not self.is_v2_format(path):
                return False
            
            # 使用正则表达式验证
            if not self.path_patterns['v2_api'].match(path):
                return False
            
            # 检查路径段
            segments = [s for s in path.split('/') if s]
            if len(segments) < 3:  # 至少包含 api, v2, resource
                return False
            
            # 验证各段格式
            for i, segment in enumerate(segments):
                if i < 2:  # api, v2
                    continue
                
                # 检查是否为参数占位符
                if segment.startswith('{') and segment.endswith('}'):
                    if not self.path_patterns['resource_id'].match(segment):
                        return False
                else:
                    # 检查普通段格式
                    if not self.path_patterns['valid_segment'].match(segment):
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"路径格式验证失败: {path}, 错误: {str(e)}")
            return False
    
    def normalize_full_api(self, method: str, path: str) -> str:
        """
        标准化完整的API标识
        
        Args:
            method: HTTP方法
            path: API路径
            
        Returns:
            标准化的API标识 (METHOD /path)
        """
        try:
            normalized_path = self.normalize_path(path, method)
            return f"{method.upper()} {normalized_path}"
        except Exception as e:
            logger.error(f"完整API标准化失败: {method} {path}, 错误: {str(e)}")
            return f"{method.upper()} {path}"
    
    def batch_normalize_paths(self, paths: List[Tuple[str, str]]) -> Dict[str, str]:
        """
        批量标准化路径
        
        Args:
            paths: (method, path) 元组列表
            
        Returns:
            标准化结果字典
        """
        try:
            results = {}
            for method, path in paths:
                original = f"{method} {path}"
                normalized = self.normalize_full_api(method, path)
                results[original] = normalized
            
            return results
        except Exception as e:
            logger.error(f"批量标准化失败: 错误: {str(e)}")
            return {}
    
    def get_normalization_rules(self) -> Dict[str, str]:
        """
        获取标准化规则
        
        Returns:
            标准化规则字典
        """
        return self.normalization_rules.copy()
    
    def add_normalization_rule(self, old_path: str, new_path: str) -> bool:
        """
        添加标准化规则
        
        Args:
            old_path: 旧路径
            new_path: 新路径
            
        Returns:
            是否添加成功
        """
        try:
            if not self.validate_path_format(new_path):
                logger.error(f"新路径格式不正确: {new_path}")
                return False
            
            self.normalization_rules[old_path] = new_path
            logger.info(f"添加标准化规则: {old_path} -> {new_path}")
            return True
        except Exception as e:
            logger.error(f"添加标准化规则失败: {old_path} -> {new_path}, 错误: {str(e)}")
            return False
    
    def remove_normalization_rule(self, old_path: str) -> bool:
        """
        移除标准化规则
        
        Args:
            old_path: 旧路径
            
        Returns:
            是否移除成功
        """
        try:
            if old_path in self.normalization_rules:
                del self.normalization_rules[old_path]
                logger.info(f"移除标准化规则: {old_path}")
                return True
            else:
                logger.warning(f"标准化规则不存在: {old_path}")
                return False
        except Exception as e:
            logger.error(f"移除标准化规则失败: {old_path}, 错误: {str(e)}")
            return False
    
    def get_path_suggestions(self, path: str) -> List[str]:
        """
        获取路径标准化建议
        
        Args:
            path: 原始路径
            
        Returns:
            建议的标准化路径列表
        """
        try:
            suggestions = []
            
            # 尝试不同HTTP方法的标准化
            for method in ['GET', 'POST', 'PUT', 'DELETE']:
                normalized = self.normalize_path(path, method)
                if normalized != path and normalized not in suggestions:
                    suggestions.append(f"{method} {normalized}")
            
            return suggestions
        except Exception as e:
            logger.error(f"获取路径建议失败: {path}, 错误: {str(e)}")
            return []


# 全局API路径标准化器实例
api_path_normalizer = APIPathNormalizer()