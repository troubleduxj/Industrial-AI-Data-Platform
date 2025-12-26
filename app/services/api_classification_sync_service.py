"""
API分类管理系统优化服务
提供API分类与V2端点的审计、同步和自动映射功能
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from fastapi import FastAPI
from tortoise.transactions import in_transaction

from app.models.admin import SysApiGroup, SysApiEndpoint
from app.core.response_formatter_v2 import ResponseFormatterV2

logger = logging.getLogger(__name__)


class APIClassificationSyncService:
    """API分类同步服务"""
    
    def __init__(self):
        self.system_management_groups = {
            'user_management': {
                'group_name': '用户管理',
                'group_code': 'user_management',
                'description': '用户账户管理相关API',
                'patterns': ['/api/v2/users']
            },
            'role_management': {
                'group_name': '角色管理',
                'group_code': 'role_management',
                'description': '角色权限管理相关API',
                'patterns': ['/api/v2/roles']
            },
            'menu_management': {
                'group_name': '菜单管理',
                'group_code': 'menu_management',
                'description': '系统菜单管理相关API',
                'patterns': ['/api/v2/menus']
            },
            'dept_management': {
                'group_name': '部门管理',
                'group_code': 'dept_management',
                'description': '组织部门管理相关API',
                'patterns': ['/api/v2/departments']
            },
            'api_management': {
                'group_name': 'API管理',
                'group_code': 'api_management',
                'description': 'API接口管理相关API',
                'patterns': ['/api/v2/apis']
            },
            'api_group_management': {
                'group_name': 'API分组管理',
                'group_code': 'api_group_management',
                'description': 'API分组管理相关API',
                'patterns': ['/api/v2/api-groups']
            },
            'dict_management': {
                'group_name': '字典管理',
                'group_code': 'dict_management',
                'description': '数据字典管理相关API',
                'patterns': ['/api/v2/dict-types', '/api/v2/dict-data']
            },
            'system_management': {
                'group_name': '系统管理',
                'group_code': 'system_management',
                'description': '系统参数和配置管理相关API',
                'patterns': ['/api/v2/system-params', '/api/v2/system/config']
            },
            'audit_management': {
                'group_name': '审计管理',
                'group_code': 'audit_management',
                'description': '系统审计日志管理相关API',
                'patterns': ['/api/v2/audit-logs']
            },
            'device_management': {
                'group_name': '设备管理',
                'group_code': 'device_management',
                'description': '设备信息管理相关API',
                'patterns': ['/api/v2/devices']
            },
            'alarm_management': {
                'group_name': '报警管理',
                'group_code': 'alarm_management',
                'description': '设备报警管理相关API',
                'patterns': ['/api/v2/alarms']
            },
            'auth_management': {
                'group_name': '认证管理',
                'group_code': 'auth_management',
                'description': '用户认证和授权相关API',
                'patterns': ['/api/v2/auth']
            },
            'base_services': {
                'group_name': '基础服务',
                'group_code': 'base_services',
                'description': '基础功能服务API',
                'patterns': ['/api/v2/base', '/api/v2/avatar', '/api/v2/health']
            },
            'documentation': {
                'group_name': '文档管理',
                'group_code': 'documentation',
                'description': 'API文档和变更日志相关API',
                'patterns': ['/api/v2/docs']
            }
        }
    
    async def audit_current_classification(self) -> Dict:
        """审计当前API分类与实际V2端点的匹配情况"""
        logger.info("开始审计API分类与V2端点匹配情况")
        
        try:
            # 获取所有现有分组
            existing_groups = await SysApiGroup.all()
            existing_groups_dict = {group.group_code: group for group in existing_groups}
            
            # 获取所有API端点
            all_endpoints = await SysApiEndpoint.all()
            
            # 分析结果
            audit_result = {
                'total_groups': len(existing_groups),
                'total_endpoints': len(all_endpoints),
                'matched_endpoints': 0,
                'unmatched_endpoints': 0,
                'missing_groups': [],
                'orphaned_endpoints': [],
                'group_endpoint_mapping': {},
                'recommendations': []
            }
            
            # 检查每个推荐分组是否存在
            for group_code, group_config in self.system_management_groups.items():
                if group_code not in existing_groups_dict:
                    audit_result['missing_groups'].append({
                        'group_code': group_code,
                        'group_name': group_config['group_name'],
                        'description': group_config['description'],
                        'patterns': group_config['patterns']
                    })
            
            # 检查端点分组情况
            for endpoint in all_endpoints:
                if endpoint.group_id:
                    audit_result['matched_endpoints'] += 1
                    group = existing_groups_dict.get(endpoint.group_id)
                    if group:
                        group_code = group.group_code
                        if group_code not in audit_result['group_endpoint_mapping']:
                            audit_result['group_endpoint_mapping'][group_code] = []
                        audit_result['group_endpoint_mapping'][group_code].append({
                            'id': endpoint.id,
                            'api_name': endpoint.api_name,
                            'api_path': endpoint.api_path,
                            'http_method': endpoint.http_method
                        })
                else:
                    audit_result['unmatched_endpoints'] += 1
                    audit_result['orphaned_endpoints'].append({
                        'id': endpoint.id,
                        'api_name': endpoint.api_name,
                        'api_path': endpoint.api_path,
                        'http_method': endpoint.http_method,
                        'suggested_group': self._suggest_group_for_endpoint(endpoint.api_path)
                    })
            
            # 生成建议
            if audit_result['missing_groups']:
                audit_result['recommendations'].append(
                    f"建议创建 {len(audit_result['missing_groups'])} 个缺失的API分组"
                )
            
            if audit_result['orphaned_endpoints']:
                audit_result['recommendations'].append(
                    f"建议为 {len(audit_result['orphaned_endpoints'])} 个未分组的API端点分配分组"
                )
            
            # 计算匹配率
            if audit_result['total_endpoints'] > 0:
                match_rate = (audit_result['matched_endpoints'] / audit_result['total_endpoints']) * 100
                audit_result['match_rate'] = f"{match_rate:.1f}%"
            else:
                audit_result['match_rate'] = "0%"
            
            logger.info(f"审计完成：{audit_result['match_rate']} 的端点已分组")
            return audit_result
            
        except Exception as e:
            logger.error(f"审计API分类失败: {str(e)}")
            raise
    
    def _suggest_group_for_endpoint(self, api_path: str) -> Optional[str]:
        """根据API路径建议分组"""
        for group_code, group_config in self.system_management_groups.items():
            for pattern in group_config['patterns']:
                if api_path.startswith(pattern):
                    return group_code
        return None
    
    async def reorganize_api_groups(self) -> Dict:
        """重新组织API分类结构，确保逻辑分组与系统管理模块对应"""
        logger.info("开始重新组织API分类结构")
        
        try:
            async with in_transaction():
                reorganize_result = {
                    'created_groups': [],
                    'updated_groups': [],
                    'skipped_groups': [],
                    'total_processed': 0
                }
                
                # 获取现有分组
                existing_groups = await SysApiGroup.all()
                existing_groups_dict = {group.group_code: group for group in existing_groups}
                
                # 处理每个推荐分组
                for group_code, group_config in self.system_management_groups.items():
                    reorganize_result['total_processed'] += 1
                    
                    if group_code in existing_groups_dict:
                        # 更新现有分组
                        existing_group = existing_groups_dict[group_code]
                        updated = False
                        
                        if existing_group.group_name != group_config['group_name']:
                            existing_group.group_name = group_config['group_name']
                            updated = True
                        
                        if existing_group.description != group_config['description']:
                            existing_group.description = group_config['description']
                            updated = True
                        
                        if updated:
                            existing_group.updated_at = datetime.now()
                            await existing_group.save()
                            reorganize_result['updated_groups'].append({
                                'group_code': group_code,
                                'group_name': group_config['group_name'],
                                'action': 'updated'
                            })
                        else:
                            reorganize_result['skipped_groups'].append({
                                'group_code': group_code,
                                'group_name': group_config['group_name'],
                                'reason': 'no_changes_needed'
                            })
                    else:
                        # 创建新分组
                        new_group = await SysApiGroup.create(
                            group_code=group_code,
                            group_name=group_config['group_name'],
                            description=group_config['description'],
                            status='active',
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        reorganize_result['created_groups'].append({
                            'id': new_group.id,
                            'group_code': group_code,
                            'group_name': group_config['group_name'],
                            'action': 'created'
                        })
                
                logger.info(f"重新组织完成：创建 {len(reorganize_result['created_groups'])} 个，更新 {len(reorganize_result['updated_groups'])} 个分组")
                return reorganize_result
                
        except Exception as e:
            logger.error(f"重新组织API分类失败: {str(e)}")
            raise
    
    async def auto_map_endpoints_to_groups(self) -> Dict:
        """实现API到分类的自动映射和同步机制"""
        logger.info("开始自动映射API端点到分组")
        
        try:
            async with in_transaction():
                mapping_result = {
                    'mapped_endpoints': [],
                    'unmapped_endpoints': [],
                    'updated_endpoints': [],
                    'total_processed': 0,
                    'success_count': 0,
                    'failed_count': 0
                }
                
                # 获取所有分组
                all_groups = await SysApiGroup.all()
                groups_dict = {group.group_code: group for group in all_groups}
                
                # 获取所有未分组的端点
                unassigned_endpoints = await SysApiEndpoint.filter(group_id__isnull=True)
                
                for endpoint in unassigned_endpoints:
                    mapping_result['total_processed'] += 1
                    
                    # 根据路径建议分组
                    suggested_group_code = self._suggest_group_for_endpoint(endpoint.api_path)
                    
                    if suggested_group_code and suggested_group_code in groups_dict:
                        # 分配到建议的分组
                        target_group = groups_dict[suggested_group_code]
                        endpoint.group_id = target_group.id
                        await endpoint.save()
                        
                        mapping_result['mapped_endpoints'].append({
                            'endpoint_id': endpoint.id,
                            'api_name': endpoint.api_name,
                            'api_path': endpoint.api_path,
                            'assigned_group': suggested_group_code,
                            'group_name': target_group.group_name
                        })
                        mapping_result['success_count'] += 1
                    else:
                        # 无法自动分组
                        mapping_result['unmapped_endpoints'].append({
                            'endpoint_id': endpoint.id,
                            'api_name': endpoint.api_name,
                            'api_path': endpoint.api_path,
                            'reason': 'no_matching_group_found'
                        })
                        mapping_result['failed_count'] += 1
                
                # 检查已分组端点是否需要重新分组
                assigned_endpoints = await SysApiEndpoint.filter(group_id__isnull=False)
                
                for endpoint in assigned_endpoints:
                    mapping_result['total_processed'] += 1
                    
                    # 获取当前分组
                    current_group = await SysApiGroup.get_or_none(id=endpoint.group_id)
                    if not current_group:
                        continue
                    
                    # 检查是否应该重新分组
                    suggested_group_code = self._suggest_group_for_endpoint(endpoint.api_path)
                    
                    if (suggested_group_code and 
                        suggested_group_code in groups_dict and 
                        current_group.group_code != suggested_group_code):
                        
                        # 重新分组
                        new_group = groups_dict[suggested_group_code]
                        old_group_name = current_group.group_name
                        
                        endpoint.group_id = new_group.id
                        await endpoint.save()
                        
                        mapping_result['updated_endpoints'].append({
                            'endpoint_id': endpoint.id,
                            'api_name': endpoint.api_name,
                            'api_path': endpoint.api_path,
                            'old_group': current_group.group_code,
                            'old_group_name': old_group_name,
                            'new_group': suggested_group_code,
                            'new_group_name': new_group.group_name
                        })
                        mapping_result['success_count'] += 1
                
                # 计算成功率
                if mapping_result['total_processed'] > 0:
                    success_rate = (mapping_result['success_count'] / mapping_result['total_processed']) * 100
                    mapping_result['success_rate'] = f"{success_rate:.1f}%"
                else:
                    mapping_result['success_rate'] = "0%"
                
                logger.info(f"自动映射完成：成功率 {mapping_result['success_rate']}")
                return mapping_result
                
        except Exception as e:
            logger.error(f"自动映射API端点失败: {str(e)}")
            raise
    
    async def sync_v2_endpoints_from_fastapi_app(self, app: FastAPI) -> Dict:
        """从FastAPI应用同步V2端点到数据库"""
        logger.info("开始从FastAPI应用同步V2端点")
        
        try:
            sync_result = {
                'discovered_endpoints': [],
                'created_endpoints': [],
                'updated_endpoints': [],
                'skipped_endpoints': [],
                'total_discovered': 0,
                'total_created': 0,
                'total_updated': 0
            }
            
            # 获取现有端点
            existing_endpoints = await SysApiEndpoint.all()
            existing_dict = {f"{ep.api_path}:{ep.http_method}": ep for ep in existing_endpoints}
            
            # 遍历FastAPI路由
            for route in app.routes:
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    # 只处理V2 API
                    if route.path.startswith('/api/v2/'):
                        for method in route.methods:
                            if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                                sync_result['total_discovered'] += 1
                                
                                endpoint_key = f"{route.path}:{method}"
                                
                                # 生成API名称和描述
                                api_name = self._generate_api_name(route.path, method)
                                description = self._generate_api_description(route.path, method)
                                api_code = self._generate_api_code(route.path, method)
                                
                                sync_result['discovered_endpoints'].append({
                                    'path': route.path,
                                    'method': method,
                                    'api_name': api_name,
                                    'api_code': api_code
                                })
                                
                                if endpoint_key in existing_dict:
                                    # 更新现有端点
                                    existing_endpoint = existing_dict[endpoint_key]
                                    updated = False
                                    
                                    if existing_endpoint.api_name != api_name:
                                        existing_endpoint.api_name = api_name
                                        updated = True
                                    
                                    if existing_endpoint.description != description:
                                        existing_endpoint.description = description
                                        updated = True
                                    
                                    if updated:
                                        existing_endpoint.updated_at = datetime.now()
                                        await existing_endpoint.save()
                                        sync_result['updated_endpoints'].append({
                                            'id': existing_endpoint.id,
                                            'api_path': route.path,
                                            'http_method': method,
                                            'action': 'updated'
                                        })
                                        sync_result['total_updated'] += 1
                                    else:
                                        sync_result['skipped_endpoints'].append({
                                            'api_path': route.path,
                                            'http_method': method,
                                            'reason': 'no_changes_needed'
                                        })
                                else:
                                    # 创建新端点
                                    new_endpoint = await SysApiEndpoint.create(
                                        api_code=api_code,
                                        api_name=api_name,
                                        api_path=route.path,
                                        http_method=method,
                                        description=description,
                                        version='v2',
                                        status='active',
                                        created_at=datetime.now(),
                                        updated_at=datetime.now()
                                    )
                                    sync_result['created_endpoints'].append({
                                        'id': new_endpoint.id,
                                        'api_path': route.path,
                                        'http_method': method,
                                        'action': 'created'
                                    })
                                    sync_result['total_created'] += 1
            
            logger.info(f"同步完成：发现 {sync_result['total_discovered']} 个端点，创建 {sync_result['total_created']} 个，更新 {sync_result['total_updated']} 个")
            return sync_result
            
        except Exception as e:
            logger.error(f"同步V2端点失败: {str(e)}")
            raise
    
    def _generate_api_name(self, path: str, method: str) -> str:
        """根据路径和方法生成API名称"""
        # 移除/api/v2/前缀
        clean_path = path.replace('/api/v2/', '')
        
        # 处理路径参数
        clean_path = clean_path.replace('{', '').replace('}', '')
        
        # 根据HTTP方法生成动作
        action_map = {
            'GET': '获取',
            'POST': '创建',
            'PUT': '更新',
            'DELETE': '删除',
            'PATCH': '部分更新'
        }
        
        action = action_map.get(method, method)
        
        # 生成名称
        if clean_path.endswith('/'):
            clean_path = clean_path[:-1]
        
        path_parts = clean_path.split('/')
        resource_name = path_parts[-1] if path_parts else 'resource'
        
        return f"{action}{resource_name}"
    
    def _generate_api_description(self, path: str, method: str) -> str:
        """根据路径和方法生成API描述"""
        return f"{method} {path} - 自动生成的API描述"
    
    def _generate_api_code(self, path: str, method: str) -> str:
        """根据路径和方法生成API编码"""
        # 移除/api/v2/前缀并替换特殊字符
        clean_path = path.replace('/api/v2/', '').replace('/', '_').replace('{', '').replace('}', '')
        return f"{method.lower()}_{clean_path}".replace('__', '_').strip('_')
    
    async def generate_classification_report(self) -> Dict:
        """生成API分类管理报告"""
        logger.info("生成API分类管理报告")
        
        try:
            # 执行审计
            audit_result = await self.audit_current_classification()
            
            # 获取统计信息
            total_groups = await SysApiGroup.all().count()
            total_endpoints = await SysApiEndpoint.all().count()
            active_groups = await SysApiGroup.filter(status='active').count()
            
            report = {
                'generated_at': datetime.now().isoformat(),
                'summary': {
                    'total_groups': total_groups,
                    'active_groups': active_groups,
                    'total_endpoints': total_endpoints,
                    'match_rate': audit_result['match_rate'],
                    'recommendations_count': len(audit_result['recommendations'])
                },
                'audit_details': audit_result,
                'system_health': {
                    'classification_coverage': audit_result['match_rate'],
                    'missing_groups_count': len(audit_result['missing_groups']),
                    'orphaned_endpoints_count': len(audit_result['orphaned_endpoints'])
                },
                'next_steps': [
                    "运行重新组织API分类结构",
                    "执行自动映射端点到分组",
                    "验证分类结果",
                    "更新权限系统关联"
                ]
            }
            
            logger.info("API分类管理报告生成完成")
            return report
            
        except Exception as e:
            logger.error(f"生成分类报告失败: {str(e)}")
            raise


# 创建全局服务实例
api_classification_sync_service = APIClassificationSyncService()