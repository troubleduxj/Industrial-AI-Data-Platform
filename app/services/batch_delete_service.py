"""
批量删除服务 - 提供统一的批量删除逻辑和用户友好的错误提示
"""
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
import logging

from app.schemas.base import BatchDeleteResponse, BatchDeleteFailedItem, BatchDeleteSuccessItem

logger = logging.getLogger(__name__)


class UserFriendlyErrorMessages:
    """用户友好的错误提示消息模板 - 增强版本，支持错误分类和用户体验优化"""
    
    # 通用错误消息
    ITEM_NOT_FOUND = "项目不存在"
    SYSTEM_PROTECTED = "系统内置项目，不允许删除"
    
    # 用户保护错误消息 - 按严重程度和类型分类
    CURRENT_USER_PROTECTION = "不能删除当前登录用户"  # 警告级别
    ADMIN_USER_PROTECTION = "不能删除admin管理员账户"  # 错误级别
    SUPERUSER_PROTECTION = "不能删除超级管理员"  # 错误级别
    
    # 错误消息分类
    ERROR_CATEGORIES = {
        'CURRENT_USER': {
            'message': CURRENT_USER_PROTECTION,
            'severity': 'warning',
            'icon': '⚠️',
            'description': '为了安全考虑，不能删除当前登录的用户账户'
        },
        'ADMIN_USER': {
            'message': ADMIN_USER_PROTECTION,
            'severity': 'error',
            'icon': '🚫',
            'description': 'admin账户是系统核心管理员，删除后可能导致系统无法管理'
        },
        'SUPER_USER': {
            'message': SUPERUSER_PROTECTION,
            'severity': 'error',
            'icon': '🔒',
            'description': '超级管理员拥有最高权限，删除后可能影响系统正常运行'
        }
    }
    
    # 关联数据错误消息模板
    API_GROUP_HAS_APIS = "API分组'{name}'不能删除，因为当前有{count}个API引用该分组"
    DEPARTMENT_HAS_CHILDREN_AND_USERS = "部门'{name}'不能删除，因为当前有{sub_count}个子部门和{user_count}个用户"
    DEPARTMENT_HAS_CHILDREN = "部门'{name}'不能删除，因为当前有{count}个子部门"
    DEPARTMENT_HAS_USERS = "部门'{name}'不能删除，因为当前有{count}个用户"
    ROLE_HAS_USERS = "角色'{name}'不能删除，因为当前有{count}个用户使用该角色"
    DICT_TYPE_HAS_DATA = "字典类型'{name}'不能删除，因为当前有{count}个字典数据项"
    MENU_HAS_CHILDREN = "菜单'{name}'不能删除，因为当前有{count}个子菜单"
    
    # 特定资源错误消息
    USER_IS_CURRENT = "用户'{name}'不能删除，因为是当前登录用户"
    USER_IS_SUPERUSER = "用户'{name}'不能删除，因为是超级管理员"
    ROLE_IS_SYSTEM = "角色'{name}'不能删除，因为是系统内置角色"
    MENU_IS_SYSTEM = "菜单'{name}'不能删除，因为是系统内置菜单"
    API_IS_SYSTEM = "API'{name}'不能删除，因为是系统内置接口"
    DICT_TYPE_IS_SYSTEM = "字典类型'{name}'不能删除，因为是系统内置类型"
    DICT_DATA_IS_SYSTEM = "字典数据'{name}'不能删除，因为是系统内置数据"
    SYSTEM_PARAM_IS_CRITICAL = "系统参数'{name}'不能删除，因为是系统关键配置"
    
    @classmethod
    def format_message(cls, template: str, **kwargs) -> str:
        """格式化错误消息模板"""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Error formatting message template '{template}': missing key {e}")
            return template


class BatchDeleteBusinessRules:
    """批量删除业务规则检查器"""
    
    @staticmethod
    async def check_user_deletion_rules(user, current_user) -> Optional[str]:
        """
        检查用户删除业务规则
        
        检查顺序：当前用户 -> admin用户 -> 超级管理员
        
        Args:
            user: 要删除的用户对象
            current_user: 当前登录用户对象
            
        Returns:
            Optional[str]: 如果不能删除返回错误消息，否则返回None
            
        Requirements: 需求3.1, 需求3.2, 需求3.3, 需求4.1, 需求4.2, 需求4.3
        """
        # 1. 检查当前用户保护 - 不能删除当前登录用户
        if user.id == current_user.id:
            return UserFriendlyErrorMessages.CURRENT_USER_PROTECTION
        
        # 2. 检查admin用户保护 - 严格的admin用户名检查（大小写不敏感）
        if user.username and user.username.lower() == 'admin':
            return UserFriendlyErrorMessages.ADMIN_USER_PROTECTION
        
        # 3. 检查超级管理员保护 - 不能删除超级管理员
        if user.is_superuser:
            return UserFriendlyErrorMessages.SUPERUSER_PROTECTION
        
        return None
    
    @staticmethod
    async def check_role_deletion_rules(role) -> Optional[str]:
        """检查角色删除业务规则"""
        # 检查是否为系统内置角色
        if getattr(role, 'is_system', False):
            return UserFriendlyErrorMessages.format_message(
                UserFriendlyErrorMessages.ROLE_IS_SYSTEM,
                name=role.role_name
            )
        
        # 检查是否有关联用户
        user_count = await role.users.all().count()
        if user_count > 0:
            return UserFriendlyErrorMessages.format_message(
                UserFriendlyErrorMessages.ROLE_HAS_USERS,
                name=role.role_name,
                count=user_count
            )
        
        return None
    
    @staticmethod
    async def check_department_deletion_rules(department) -> Optional[str]:
        """检查部门删除业务规则"""
        from app.models.admin import User, Dept
        
        # 检查子部门
        sub_dept_count = await Dept.filter(parent_id=department.id, del_flag="0").count()
        
        # 检查关联用户
        user_count = await User.filter(dept_id=department.id).count()
        
        if sub_dept_count > 0 and user_count > 0:
            return UserFriendlyErrorMessages.format_message(
                UserFriendlyErrorMessages.DEPARTMENT_HAS_CHILDREN_AND_USERS,
                name=department.dept_name,
                sub_count=sub_dept_count,
                user_count=user_count
            )
        elif sub_dept_count > 0:
            return UserFriendlyErrorMessages.format_message(
                UserFriendlyErrorMessages.DEPARTMENT_HAS_CHILDREN,
                name=department.dept_name,
                count=sub_dept_count
            )
        elif user_count > 0:
            return UserFriendlyErrorMessages.format_message(
                UserFriendlyErrorMessages.DEPARTMENT_HAS_USERS,
                name=department.dept_name,
                count=user_count
            )
        
        return None
    
    @staticmethod
    async def check_api_group_deletion_rules(api_group) -> Optional[str]:
        """检查API分组删除业务规则"""
        from app.models.admin import SysApiEndpoint
        
        # 检查是否为系统内置
        if getattr(api_group, 'is_system', False):
            return UserFriendlyErrorMessages.format_message(
                UserFriendlyErrorMessages.API_IS_SYSTEM,
                name=api_group.group_name
            )
        
        # 检查关联API
        api_count = await SysApiEndpoint.filter(group_id=api_group.id).count()
        if api_count > 0:
            return UserFriendlyErrorMessages.format_message(
                UserFriendlyErrorMessages.API_GROUP_HAS_APIS,
                name=api_group.group_name,
                count=api_count
            )
        
        return None
    
    @staticmethod
    async def check_menu_deletion_rules(menu) -> Optional[str]:
        """检查菜单删除业务规则"""
        from app.models.admin import Menu
        
        # 检查是否为系统内置
        if getattr(menu, 'is_system', False):
            return UserFriendlyErrorMessages.format_message(
                UserFriendlyErrorMessages.MENU_IS_SYSTEM,
                name=menu.name
            )
        
        # 检查子菜单
        child_count = await Menu.filter(parent_id=menu.id).count()
        if child_count > 0:
            return UserFriendlyErrorMessages.format_message(
                UserFriendlyErrorMessages.MENU_HAS_CHILDREN,
                name=menu.name,
                count=child_count
            )
        
        return None
    
    @staticmethod
    async def check_dict_type_deletion_rules(dict_type) -> Optional[str]:
        """检查字典类型删除业务规则"""
        # 检查是否为系统内置
        if getattr(dict_type, 'is_system', False):
            return UserFriendlyErrorMessages.format_message(
                UserFriendlyErrorMessages.DICT_TYPE_IS_SYSTEM,
                name=dict_type.type_name
            )
        
        # 检查关联字典数据
        from app.models.system import SysDictData as DictData
        data_count = await DictData.filter(dict_type_id=dict_type.id).count()
        if data_count > 0:
            return UserFriendlyErrorMessages.format_message(
                UserFriendlyErrorMessages.DICT_TYPE_HAS_DATA,
                name=dict_type.type_name,
                count=data_count
            )
        
        return None
    
    @staticmethod
    async def check_dict_data_deletion_rules(dict_data) -> Optional[str]:
        """检查字典数据删除业务规则"""
        if getattr(dict_data, 'is_system', False):
            return UserFriendlyErrorMessages.format_message(
                UserFriendlyErrorMessages.DICT_DATA_IS_SYSTEM,
                name=dict_data.data_label
            )
        
        return None
    
    @staticmethod
    async def check_system_param_deletion_rules(system_param) -> Optional[str]:
        """检查系统参数删除业务规则"""
        if getattr(system_param, 'is_system', False) or not getattr(system_param, 'is_editable', True):
            return UserFriendlyErrorMessages.format_message(
                UserFriendlyErrorMessages.SYSTEM_PARAM_IS_CRITICAL,
                name=system_param.param_name
            )
        
        return None
    
    @staticmethod
    async def check_api_deletion_rules(api) -> Optional[str]:
        """检查API删除业务规则"""
        if getattr(api, 'is_system', False):
            return UserFriendlyErrorMessages.format_message(
                UserFriendlyErrorMessages.API_IS_SYSTEM,
                name=api.api_name
            )
        
        return None


class BaseBatchDeleteService(ABC):
    """批量删除服务基类"""
    
    def __init__(self, resource_name: str):
        self.resource_name = resource_name
    
    @abstractmethod
    async def get_item_by_id(self, item_id: int):
        """根据ID获取项目"""
        pass
    
    @abstractmethod
    async def get_item_name(self, item) -> str:
        """获取项目名称"""
        pass
    
    @abstractmethod
    async def check_business_rules(self, item, **kwargs) -> Optional[str]:
        """检查业务规则，返回错误消息或None"""
        pass
    
    @abstractmethod
    async def delete_item(self, item):
        """删除项目"""
        pass
    
    async def batch_delete(self, ids: List[int], **kwargs) -> BatchDeleteResponse:
        """执行批量删除操作"""
        deleted_items = []
        failed_items = []
        
        for item_id in ids:
            try:
                # 获取项目
                item = await self.get_item_by_id(item_id)
                if not item:
                    failed_items.append(BatchDeleteFailedItem(
                        id=item_id,
                        name=None,
                        reason=UserFriendlyErrorMessages.ITEM_NOT_FOUND
                    ))
                    continue
                
                # 获取项目名称
                item_name = await self.get_item_name(item)
                
                # 检查业务规则
                error_message = await self.check_business_rules(item, **kwargs)
                if error_message:
                    failed_items.append(BatchDeleteFailedItem(
                        id=item_id,
                        name=item_name,
                        reason=error_message
                    ))
                    continue
                
                # 执行删除
                await self.delete_item(item)
                deleted_items.append(BatchDeleteSuccessItem(
                    id=item_id,
                    name=item_name
                ))
                
            except Exception as e:
                logger.error(f"Error deleting {self.resource_name} {item_id}: {str(e)}")
                failed_items.append(BatchDeleteFailedItem(
                    id=item_id,
                    name=None,
                    reason=f"删除失败: {str(e)}"
                ))
        
        return BatchDeleteResponse(
            deleted_count=len(deleted_items),
            failed_count=len(failed_items),
            deleted=deleted_items,
            failed=failed_items
        )


class UserBatchDeleteService(BaseBatchDeleteService):
    """用户批量删除服务"""
    
    def __init__(self):
        super().__init__("用户")
    
    async def get_item_by_id(self, item_id: int):
        from app.models.admin import User
        return await User.get_or_none(id=item_id)
    
    async def get_item_name(self, item) -> str:
        return item.username
    
    async def check_business_rules(self, item, current_user=None, **kwargs) -> Optional[str]:
        return await BatchDeleteBusinessRules.check_user_deletion_rules(item, current_user)
    
    async def delete_item(self, item):
        await item.delete()


class RoleBatchDeleteService(BaseBatchDeleteService):
    """角色批量删除服务"""
    
    def __init__(self):
        super().__init__("角色")
    
    async def get_item_by_id(self, item_id: int):
        from app.models.admin import Role
        return await Role.get_or_none(id=item_id)
    
    async def get_item_name(self, item) -> str:
        return item.role_name
    
    async def check_business_rules(self, item, **kwargs) -> Optional[str]:
        return await BatchDeleteBusinessRules.check_role_deletion_rules(item)
    
    async def delete_item(self, item):
        # 清理关联关系
        await item.apis.clear()
        await item.menus.clear()
        await item.delete()


class DepartmentBatchDeleteService(BaseBatchDeleteService):
    """部门批量删除服务"""
    
    def __init__(self):
        super().__init__("部门")
    
    async def get_item_by_id(self, item_id: int):
        from app.models.admin import Dept
        return await Dept.get_or_none(id=item_id)
    
    async def get_item_name(self, item) -> str:
        return item.dept_name
    
    async def check_business_rules(self, item, force=False, **kwargs) -> Optional[str]:
        if force:
            return None  # 强制删除时跳过业务规则检查
        return await BatchDeleteBusinessRules.check_department_deletion_rules(item)
    
    async def delete_item(self, item):
        # 软删除
        item.del_flag = "2"
        await item.save()


class ApiGroupBatchDeleteService(BaseBatchDeleteService):
    """API分组批量删除服务"""
    
    def __init__(self):
        super().__init__("API分组")
    
    async def get_item_by_id(self, item_id: int):
        from app.models.admin import SysApiGroup
        return await SysApiGroup.get_or_none(id=item_id)
    
    async def get_item_name(self, item) -> str:
        return item.group_name
    
    async def check_business_rules(self, item, **kwargs) -> Optional[str]:
        return await BatchDeleteBusinessRules.check_api_group_deletion_rules(item)
    
    async def delete_item(self, item):
        await item.delete()


class MenuBatchDeleteService(BaseBatchDeleteService):
    """菜单批量删除服务"""
    
    def __init__(self):
        super().__init__("菜单")
    
    async def get_item_by_id(self, item_id: int):
        from app.models.admin import Menu
        return await Menu.get_or_none(id=item_id)
    
    async def get_item_name(self, item) -> str:
        return item.name
    
    async def check_business_rules(self, item, force=False, **kwargs) -> Optional[str]:
        if force:
            # 强制删除时先删除子菜单
            from app.models.admin import Menu
            children = await Menu.filter(parent_id=item.id).all()
            for child in children:
                await child.delete()
            return None
        return await BatchDeleteBusinessRules.check_menu_deletion_rules(item)
    
    async def delete_item(self, item):
        await item.delete()


class DictTypeBatchDeleteService(BaseBatchDeleteService):
    """字典类型批量删除服务"""
    
    def __init__(self):
        super().__init__("字典类型")
    
    async def get_item_by_id(self, item_id: int):
        from app.models.system import SysDictType as DictType
        return await DictType.get_or_none(id=item_id)
    
    async def get_item_name(self, item) -> str:
        return item.type_name
    
    async def check_business_rules(self, item, **kwargs) -> Optional[str]:
        return await BatchDeleteBusinessRules.check_dict_type_deletion_rules(item)
    
    async def delete_item(self, item):
        await item.delete()


class DictDataBatchDeleteService(BaseBatchDeleteService):
    """字典数据批量删除服务"""
    
    def __init__(self):
        super().__init__("字典数据")
    
    async def get_item_by_id(self, item_id: int):
        from app.models.system import SysDictData as DictData
        return await DictData.get_or_none(id=item_id)
    
    async def get_item_name(self, item) -> str:
        return item.data_label
    
    async def check_business_rules(self, item, **kwargs) -> Optional[str]:
        return await BatchDeleteBusinessRules.check_dict_data_deletion_rules(item)
    
    async def delete_item(self, item):
        await item.delete()


class SystemParamBatchDeleteService(BaseBatchDeleteService):
    """系统参数批量删除服务"""
    
    def __init__(self):
        super().__init__("系统参数")
    
    async def get_item_by_id(self, item_id: int):
        from app.models.system import TSysConfig as SystemParam
        return await SystemParam.get_or_none(id=item_id)
    
    async def get_item_name(self, item) -> str:
        return item.param_name
    
    async def check_business_rules(self, item, **kwargs) -> Optional[str]:
        return await BatchDeleteBusinessRules.check_system_param_deletion_rules(item)
    
    async def delete_item(self, item):
        await item.delete()


class ApiBatchDeleteService(BaseBatchDeleteService):
    """API批量删除服务"""
    
    def __init__(self):
        super().__init__("API")
    
    async def get_item_by_id(self, item_id: int):
        from app.models.admin import SysApiEndpoint
        return await SysApiEndpoint.get_or_none(id=item_id)
    
    async def get_item_name(self, item) -> str:
        return item.api_name
    
    async def check_business_rules(self, item, **kwargs) -> Optional[str]:
        return await BatchDeleteBusinessRules.check_api_deletion_rules(item)
    
    async def delete_item(self, item):
        await item.delete()


# 服务实例
user_batch_delete_service = UserBatchDeleteService()
role_batch_delete_service = RoleBatchDeleteService()
department_batch_delete_service = DepartmentBatchDeleteService()
api_group_batch_delete_service = ApiGroupBatchDeleteService()
menu_batch_delete_service = MenuBatchDeleteService()
dict_type_batch_delete_service = DictTypeBatchDeleteService()
dict_data_batch_delete_service = DictDataBatchDeleteService()
system_param_batch_delete_service = SystemParamBatchDeleteService()
api_batch_delete_service = ApiBatchDeleteService()