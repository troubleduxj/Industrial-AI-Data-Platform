#!/usr/bin/env python3
"""
权限迁移配置文件
包含数据库连接、迁移参数等配置
"""

import os
from typing import Dict, Any

class MigrationConfig:
    """迁移配置类"""
    
    def __init__(self):
        # 数据库配置
        self.DATABASE_URL = os.getenv(
            'DATABASE_URL', 
            'postgresql://user:password@localhost:5432/database'
        )
        
        # 迁移配置
        self.MIGRATION_BATCH_SIZE = int(os.getenv('MIGRATION_BATCH_SIZE', '1000'))
        self.MIGRATION_TIMEOUT = int(os.getenv('MIGRATION_TIMEOUT', '300'))  # 秒
        self.BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))
        
        # 置信度阈值
        self.HIGH_CONFIDENCE_THRESHOLD = float(os.getenv('HIGH_CONFIDENCE_THRESHOLD', '0.9'))
        self.MEDIUM_CONFIDENCE_THRESHOLD = float(os.getenv('MEDIUM_CONFIDENCE_THRESHOLD', '0.7'))
        
        # 日志配置
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE_MAX_SIZE = int(os.getenv('LOG_FILE_MAX_SIZE', '10485760'))  # 10MB
        self.LOG_FILE_BACKUP_COUNT = int(os.getenv('LOG_FILE_BACKUP_COUNT', '5'))
        
        # 输出目录
        self.OUTPUT_DIR = os.getenv('MIGRATION_OUTPUT_DIR', 'database/migration_output')
        
        # API路径标准化规则
        self.API_PATH_RULES = {
            # 系统管理模块
            'system': {
                '/user/list': '/api/v2/users',
                '/user/create': '/api/v2/users',
                '/user/update': '/api/v2/users/{id}',
                '/user/delete': '/api/v2/users/{id}',
                '/user/reset_password': '/api/v2/users/{id}/reset-password',
                '/user/info': '/api/v2/users/{id}',
                '/user/permissions': '/api/v2/users/{id}/permissions',
                
                '/role/list': '/api/v2/roles',
                '/role/create': '/api/v2/roles',
                '/role/update': '/api/v2/roles/{id}',
                '/role/delete': '/api/v2/roles/{id}',
                '/role/info': '/api/v2/roles/{id}',
                '/role/permissions': '/api/v2/roles/{id}/permissions',
                '/role/users': '/api/v2/roles/{id}/users',
                
                '/menu/list': '/api/v2/menus',
                '/menu/create': '/api/v2/menus',
                '/menu/update': '/api/v2/menus/{id}',
                '/menu/delete': '/api/v2/menus/{id}',
                '/menu/tree': '/api/v2/menus/tree',
                
                '/dept/list': '/api/v2/departments',
                '/dept/create': '/api/v2/departments',
                '/dept/update': '/api/v2/departments/{id}',
                '/dept/delete': '/api/v2/departments/{id}',
                '/dept/tree': '/api/v2/departments/tree',
            },
            
            # 设备管理模块
            'device': {
                '/device/list': '/api/v2/devices',
                '/device/create': '/api/v2/devices',
                '/device/update': '/api/v2/devices/{id}',
                '/device/delete': '/api/v2/devices/{id}',
                '/device/info': '/api/v2/devices/{id}',
                '/device/search': '/api/v2/devices/search',
                '/device/batch': '/api/v2/devices/batch',
                
                '/device/type/list': '/api/v2/devices/types',
                '/device/type/create': '/api/v2/devices/types',
                '/device/type/update': '/api/v2/devices/types/{id}',
                '/device/type/delete': '/api/v2/devices/types/{id}',
                '/device/type/info': '/api/v2/devices/types/{id}',
                
                '/device/monitor/data': '/api/v2/devices/{id}/data',
                '/device/monitor/status': '/api/v2/devices/{id}/status',
                '/device/monitor/statistics': '/api/v2/devices/statistics',
                
                '/device/maintenance/list': '/api/v2/devices/{id}/maintenance',
                '/device/maintenance/create': '/api/v2/devices/{id}/maintenance',
                '/device/maintenance/update': '/api/v2/devices/maintenance/{id}',
                '/device/maintenance/delete': '/api/v2/devices/maintenance/{id}',
                '/device/maintenance/schedule': '/api/v2/devices/maintenance/schedule',
                
                '/device/process/list': '/api/v2/devices/{id}/processes',
                '/device/process/create': '/api/v2/devices/{id}/processes',
                '/device/process/update': '/api/v2/devices/processes/{id}',
                '/device/process/delete': '/api/v2/devices/processes/{id}',
                '/device/process/execute': '/api/v2/devices/processes/{id}/execute',
            },
            
            # AI监控模块
            'ai': {
                '/ai/prediction/list': '/api/v2/ai/predictions',
                '/ai/prediction/create': '/api/v2/ai/predictions',
                '/ai/prediction/update': '/api/v2/ai/predictions/{id}',
                '/ai/prediction/delete': '/api/v2/ai/predictions/{id}',
                '/ai/prediction/export': '/api/v2/ai/predictions/{id}/export',
                '/ai/prediction/share': '/api/v2/ai/predictions/{id}/share',
                
                '/ai/model/list': '/api/v2/ai/models',
                '/ai/model/create': '/api/v2/ai/models',
                '/ai/model/update': '/api/v2/ai/models/{id}',
                '/ai/model/delete': '/api/v2/ai/models/{id}',
                '/ai/model/train': '/api/v2/ai/models/{id}/train',
                '/ai/model/metrics': '/api/v2/ai/models/{id}/metrics',
                
                '/ai/annotation/list': '/api/v2/ai/annotations',
                '/ai/annotation/create': '/api/v2/ai/annotations',
                '/ai/annotation/update': '/api/v2/ai/annotations/{id}',
                '/ai/annotation/delete': '/api/v2/ai/annotations/{id}',
                '/ai/annotation/import': '/api/v2/ai/annotations/{id}/import',
                '/ai/annotation/export': '/api/v2/ai/annotations/{id}/export',
                
                '/ai/health/list': '/api/v2/ai/health-scores',
                '/ai/health/create': '/api/v2/ai/health-scores',
                '/ai/health/update': '/api/v2/ai/health-scores/{id}',
                '/ai/health/delete': '/api/v2/ai/health-scores/{id}',
                '/ai/health/export': '/api/v2/ai/health-scores/export',
                '/ai/health/config': '/api/v2/ai/health-scores/config',
                '/ai/health/trends': '/api/v2/ai/health-scores/trends',
                
                '/ai/analysis/list': '/api/v2/ai/analysis',
                '/ai/analysis/create': '/api/v2/ai/analysis',
                '/ai/analysis/update': '/api/v2/ai/analysis/{id}',
                '/ai/analysis/delete': '/api/v2/ai/analysis/{id}',
                '/ai/analysis/results': '/api/v2/ai/analysis/{id}/results',
                '/ai/analysis/schedule': '/api/v2/ai/analysis/{id}/schedule',
            },
            
            # 统计分析模块
            'statistics': {
                '/statistics/online-rate': '/api/v2/statistics/online-rate',
                '/statistics/weld-records': '/api/v2/statistics/weld-records',
                '/statistics/weld-time': '/api/v2/statistics/weld-time',
                '/statistics/welding-reports': '/api/v2/statistics/welding-reports',
                '/statistics/dashboard': '/api/v2/statistics/dashboard',
                '/statistics/custom-report': '/api/v2/statistics/custom-report',
            },
            
            # 仪表板模块
            'dashboard': {
                '/dashboard/overview': '/api/v2/dashboard/overview',
                '/dashboard/device-stats': '/api/v2/dashboard/device-stats',
                '/dashboard/alarm-stats': '/api/v2/dashboard/alarm-stats',
                '/dashboard/widgets': '/api/v2/dashboard/widgets',
                '/dashboard/widget/create': '/api/v2/dashboard/widgets',
                '/dashboard/widget/update': '/api/v2/dashboard/widgets/{id}',
                '/dashboard/widget/delete': '/api/v2/dashboard/widgets/{id}',
            },
            
            # 报警管理模块
            'alarm': {
                '/alarm/list': '/api/v2/alarms',
                '/alarm/info': '/api/v2/alarms/{id}',
                '/alarm/handle': '/api/v2/alarms/{id}/handle',
                '/alarm/batch-handle': '/api/v2/alarms/batch-handle',
                '/alarm/acknowledge': '/api/v2/alarms/{id}/acknowledge',
                '/alarm/statistics': '/api/v2/alarms/statistics',
            }
        }
        
        # API分组映射
        self.API_GROUPS = {
            'users': '系统管理',
            'roles': '系统管理',
            'menus': '系统管理',
            'departments': '系统管理',
            'devices': '设备管理',
            'ai': 'AI监控',
            'statistics': '统计分析',
            'dashboard': '仪表板',
            'alarms': '报警管理'
        }
        
        # 验证规则
        self.VALIDATION_RULES = {
            'required_tables': [
                't_sys_permission_migrations',
                't_sys_migration_logs',
                't_sys_api_groups',
                't_sys_api_endpoints'
            ],
            'required_functions': [
                'validate_permission_migration',
                'get_user_permissions_v2'
            ],
            'max_low_confidence_ratio': 0.2,  # 低置信度映射不超过20%
            'min_api_coverage_ratio': 0.95,   # API覆盖率不低于95%
        }
        
        # 性能配置
        self.PERFORMANCE_CONFIG = {
            'connection_pool_size': 10,
            'connection_timeout': 30,
            'query_timeout': 60,
            'batch_insert_size': 1000,
            'max_concurrent_operations': 5
        }

    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return {
            'url': self.DATABASE_URL,
            'pool_size': self.PERFORMANCE_CONFIG['connection_pool_size'],
            'timeout': self.PERFORMANCE_CONFIG['connection_timeout']
        }
    
    def get_migration_config(self) -> Dict[str, Any]:
        """获取迁移配置"""
        return {
            'batch_size': self.MIGRATION_BATCH_SIZE,
            'timeout': self.MIGRATION_TIMEOUT,
            'backup_retention_days': self.BACKUP_RETENTION_DAYS,
            'high_confidence_threshold': self.HIGH_CONFIDENCE_THRESHOLD,
            'medium_confidence_threshold': self.MEDIUM_CONFIDENCE_THRESHOLD
        }
    
    def get_validation_config(self) -> Dict[str, Any]:
        """获取验证配置"""
        return self.VALIDATION_RULES
    
    def get_all_api_path_rules(self) -> Dict[str, str]:
        """获取所有API路径规则"""
        all_rules = {}
        for module_rules in self.API_PATH_RULES.values():
            all_rules.update(module_rules)
        return all_rules
    
    def get_api_group_by_path(self, api_path: str) -> str:
        """根据API路径获取分组"""
        if api_path.startswith('/api/v2/'):
            parts = api_path.split('/')
            if len(parts) >= 4:
                resource = parts[3]
                return self.API_GROUPS.get(resource, '其他')
        return '未分类'

# 全局配置实例
config = MigrationConfig()

# 便捷函数
def get_database_url() -> str:
    """获取数据库连接URL"""
    return config.DATABASE_URL

def get_api_path_rules() -> Dict[str, str]:
    """获取API路径规则"""
    return config.get_all_api_path_rules()

def get_api_groups() -> Dict[str, str]:
    """获取API分组映射"""
    return config.API_GROUPS

def get_confidence_thresholds() -> tuple:
    """获取置信度阈值"""
    return (config.HIGH_CONFIDENCE_THRESHOLD, config.MEDIUM_CONFIDENCE_THRESHOLD)

if __name__ == "__main__":
    # 配置测试
    print("权限迁移配置:")
    print(f"  数据库URL: {config.DATABASE_URL}")
    print(f"  批处理大小: {config.MIGRATION_BATCH_SIZE}")
    print(f"  高置信度阈值: {config.HIGH_CONFIDENCE_THRESHOLD}")
    print(f"  API路径规则数量: {len(config.get_all_api_path_rules())}")
    print(f"  API分组数量: {len(config.API_GROUPS)}")
    print(f"  输出目录: {config.OUTPUT_DIR}")