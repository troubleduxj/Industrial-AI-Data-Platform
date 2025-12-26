"""
系统管理模块的批量删除服务实现

为各个系统管理资源提供具体的批量删除服务实现：
- API管理批量删除服务
- 字典类型批量删除服务
- 字典数据批量删除服务
- 系统参数批量删除服务

需求映射：
- 需求1.3, 需求1.4: API管理批量删除
- 需求2.2, 需求2.3: 字典类型批量删除
- 需求3.3, 需求3.5: 字典数据批量删除
- 需求4.2, 需求4.3: 系统参数批量删除
"""

from typing import List, Dict, Any, Optional
from tortoise.expressions import Q

from app.models.admin import SysApiEndpoint, User
from app.models.system import SysDictType, SysDictData, TSysConfig
from app.services.batch_delete_service import (
    BaseBatchDeleteService,
    BatchDeleteValidator,
    BatchDeletePermissionChecker,
    SystemProtectedValidator,
    ReferenceCheckValidator,
    DefaultPermissionChecker
)


class ApiReferenceValidator(BatchDeleteValidator):
    """API引用检查验证器"""
    
    async def validate_item(self, item: SysApiEndpoint, context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        # 检查API是否被角色引用
        from app.models.admin import Role
        
        # 通过多对多关系检查是否有角色使用此API
        roles_count = await Role.filter(apis=item.id).count()
        if roles_count > 0:
            return False, f"该API被 {roles_count} 个角色引用，无法删除"
        
        return True, None


class DictTypeReferenceValidator(BatchDeleteValidator):
    """字典类型引用检查验证器"""
    
    async def validate_item(self, item: SysDictType, context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        # 检查字典类型是否有关联的字典数据
        dict_data_count = await SysDictData.filter(dict_type=item).count()
        if dict_data_count > 0:
            return False, f"该字典类型下有 {dict_data_count} 条字典数据，无法删除"
        
        return True, None


class DictDataReferenceValidator(BatchDeleteValidator):
    """字典数据引用检查验证器"""
    
    async def validate_item(self, item: SysDictData, context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        # 这里可以添加检查字典数据是否被其他系统组件引用的逻辑
        # 例如检查用户状态、系统配置等是否使用了该字典值
        
        # 示例：检查是否为关键字典数据
        critical_dict_values = ['active', 'inactive', 'enabled', 'disabled', 'admin', 'user']
        if item.data_value.lower() in critical_dict_values:
            return False, "关键字典数据不允许删除"
        
        return True, None


class SystemParamCriticalValidator(BatchDeleteValidator):
    """系统参数关键项验证器"""
    
    def __init__(self):
        # 定义关键系统参数键
        self.critical_param_keys = [
            'system.version', 'system.name', 'system.logo',
            'auth.jwt_secret', 'auth.token_expire',
            'database.host', 'database.port', 'redis.host',
            'security.encryption_key', 'system.admin_email'
        ]
    
    async def validate_item(self, item: TSysConfig, context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        # 检查是否为系统内置参数
        if item.is_system:
            return False, "系统内置参数不允许删除"
        
        # 检查是否为关键系统参数
        if item.param_key in self.critical_param_keys:
            return False, "关键系统参数不允许删除"
        
        return True, None


class SystemBatchDeletePermissionChecker(BatchDeletePermissionChecker):
    """系统管理权限检查器"""
    
    async def check_permission(self, user: User, resource_type: str, context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        # 检查用户是否为超级管理员
        if user.is_superuser:
            return True, None
        
        # 检查用户角色权限
        # 这里可以集成实际的权限系统
        # 目前简化处理，检查用户是否有管理员角色
        
        user_roles = await user.roles.all()
        admin_roles = ['admin', 'system_admin', 'super_admin']
        
        for role in user_roles:
            if role.role_key in admin_roles:
                return True, None
        
        return False, f"用户权限不足，无法执行{resource_type}的批量删除操作"
    
    async def check_item_permission(self, user: User, item, context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        # 对于系统管理资源，如果有批量删除权限，则有删除单个项目的权限
        return await self.check_permission(user, item.__class__.__name__.lower(), context)


# 具体的批量删除服务实现

class ApiBatchDeleteService(BaseBatchDeleteService[SysApiEndpoint]):
    """API管理批量删除服务"""
    
    def __init__(self):
        super().__init__(
            model_class=SysApiEndpoint,
            resource_name="API",
            module_name="API管理",
            validator=ApiReferenceValidator(),
            permission_checker=SystemBatchDeletePermissionChecker(),
            max_batch_size=100
        )


class DictTypeBatchDeleteService(BaseBatchDeleteService[SysDictType]):
    """字典类型批量删除服务"""
    
    def __init__(self):
        super().__init__(
            model_class=SysDictType,
            resource_name="字典类型",
            module_name="字典类型管理",
            validator=DictTypeReferenceValidator(),
            permission_checker=SystemBatchDeletePermissionChecker(),
            max_batch_size=50
        )


class DictDataBatchDeleteService(BaseBatchDeleteService[SysDictData]):
    """字典数据批量删除服务"""
    
    def __init__(self):
        super().__init__(
            model_class=SysDictData,
            resource_name="字典数据",
            module_name="字典数据管理",
            validator=DictDataReferenceValidator(),
            permission_checker=SystemBatchDeletePermissionChecker(),
            max_batch_size=200
        )


class SystemParamBatchDeleteService(BaseBatchDeleteService[TSysConfig]):
    """系统参数批量删除服务"""
    
    def __init__(self):
        super().__init__(
            model_class=TSysConfig,
            resource_name="系统参数",
            module_name="系统参数管理",
            validator=SystemParamCriticalValidator(),
            permission_checker=SystemBatchDeletePermissionChecker(),
            max_batch_size=100
        )


# 服务实例 - 单例模式
api_batch_delete_service = ApiBatchDeleteService()
dict_type_batch_delete_service = DictTypeBatchDeleteService()
dict_data_batch_delete_service = DictDataBatchDeleteService()
system_param_batch_delete_service = SystemParamBatchDeleteService()


# 便捷函数，用于在API端点中直接调用

async def batch_delete_apis(request, item_ids: List[int], current_user: User, context: Optional[Dict[str, Any]] = None):
    """批量删除API的便捷函数"""
    return await api_batch_delete_service.batch_delete(request, item_ids, current_user, context)


async def batch_delete_dict_types(request, item_ids: List[int], current_user: User, context: Optional[Dict[str, Any]] = None):
    """批量删除字典类型的便捷函数"""
    return await dict_type_batch_delete_service.batch_delete(request, item_ids, current_user, context)


async def batch_delete_dict_data(request, item_ids: List[int], current_user: User, context: Optional[Dict[str, Any]] = None):
    """批量删除字典数据的便捷函数"""
    return await dict_data_batch_delete_service.batch_delete(request, item_ids, current_user, context)


async def batch_delete_system_params(request, item_ids: List[int], current_user: User, context: Optional[Dict[str, Any]] = None):
    """批量删除系统参数的便捷函数"""
    return await system_param_batch_delete_service.batch_delete(request, item_ids, current_user, context)