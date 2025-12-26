"""
批量删除服务集成示例

展示如何在现有的API端点中集成统一的批量删除服务层

这个文件展示了如何将现有的批量删除端点迁移到使用新的统一服务层
"""

from typing import List
from fastapi import APIRouter, Request, Body
from app.models.admin import User
from app.core.dependency import DependAuth
from app.schemas.system import SysConfigBatchDelete
from app.services.system_batch_delete_services import batch_delete_system_params

# 示例：系统参数批量删除端点的新实现
async def batch_delete_system_params_new_implementation(
    request: Request,
    batch_data: SysConfigBatchDelete,
    current_user: User = DependAuth
):
    """
    使用统一批量删除服务的系统参数批量删除实现
    
    这个实现展示了如何用几行代码替换原来复杂的批量删除逻辑
    """
    # 使用统一的批量删除服务
    return await batch_delete_system_params(
        request=request,
        item_ids=batch_data.ids,
        current_user=current_user,
        context={
            "operation_type": "batch_delete",
            "source": "api_v2"
        }
    )


# 示例：API管理批量删除端点的新实现
from app.schemas.apis import ApiBatchDelete
from app.services.system_batch_delete_services import batch_delete_apis

async def batch_delete_apis_new_implementation(
    request: Request,
    batch_data: ApiBatchDelete,
    current_user: User = DependAuth
):
    """
    使用统一批量删除服务的API批量删除实现
    """
    return await batch_delete_apis(
        request=request,
        item_ids=batch_data.ids,
        current_user=current_user,
        context={
            "operation_type": "batch_delete",
            "source": "api_v2"
        }
    )


# 示例：字典类型批量删除端点的新实现
from app.schemas.system import SysDictTypeBatchDelete
from app.services.system_batch_delete_services import batch_delete_dict_types

async def batch_delete_dict_types_new_implementation(
    request: Request,
    batch_request: SysDictTypeBatchDelete,
    current_user: User = DependAuth
):
    """
    使用统一批量删除服务的字典类型批量删除实现
    """
    return await batch_delete_dict_types(
        request=request,
        item_ids=batch_request.ids,
        current_user=current_user,
        context={
            "operation_type": "batch_delete",
            "source": "api_v2"
        }
    )


# 示例：字典数据批量删除端点的新实现
from app.services.system_batch_delete_services import batch_delete_dict_data

async def batch_delete_dict_data_new_implementation(
    request: Request,
    batch_data: dict = Body(..., description="批量删除请求数据"),
    current_user: User = DependAuth
):
    """
    使用统一批量删除服务的字典数据批量删除实现
    """
    # 从请求数据中提取ID列表
    item_ids = batch_data.get("ids", [])
    
    return await batch_delete_dict_data(
        request=request,
        item_ids=item_ids,
        current_user=current_user,
        context={
            "operation_type": "batch_delete",
            "source": "api_v2",
            "dict_type_filter": batch_data.get("dict_type_id")  # 可选的字典类型过滤
        }
    )


# 示例：如何创建自定义的批量删除服务
from app.services.batch_delete_service import BaseBatchDeleteService, BatchDeleteValidator
from app.models.admin import Dept

class DeptHierarchyValidator(BatchDeleteValidator):
    """部门层级验证器 - 防止删除有子部门的部门"""
    
    async def validate_item(self, item: Dept, context: dict) -> tuple[bool, str]:
        # 检查是否有子部门
        children_count = await Dept.filter(parent_id=item.id, del_flag="0").count()
        if children_count > 0:
            return False, f"该部门下有 {children_count} 个子部门，无法删除"
        
        # 检查是否有用户
        users_count = await item.users.filter(del_flag="0").count()
        if users_count > 0:
            return False, f"该部门下有 {users_count} 个用户，无法删除"
        
        return True, None


class DeptBatchDeleteService(BaseBatchDeleteService[Dept]):
    """部门批量删除服务"""
    
    def __init__(self):
        super().__init__(
            model_class=Dept,
            resource_name="部门",
            module_name="部门管理",
            validator=DeptHierarchyValidator(),
            max_batch_size=50
        )
    
    async def _delete_item(self, item: Dept, context: dict):
        """重写删除方法，实现软删除"""
        item.del_flag = "2"  # 标记为已删除
        await item.save()


# 创建部门批量删除服务实例
dept_batch_delete_service = DeptBatchDeleteService()

async def batch_delete_departments_new_implementation(
    request: Request,
    dept_ids: List[int],
    current_user: User = DependAuth
):
    """
    使用统一批量删除服务的部门批量删除实现
    """
    return await dept_batch_delete_service.batch_delete(
        request=request,
        item_ids=dept_ids,
        current_user=current_user,
        context={
            "operation_type": "soft_delete",
            "source": "api_v2"
        }
    )


# 使用说明和最佳实践
"""
使用统一批量删除服务的优势：

1. 代码复用：所有批量删除操作使用相同的核心逻辑
2. 一致性：统一的错误处理、响应格式和审计日志
3. 可扩展性：通过验证器和权限检查器轻松扩展业务逻辑
4. 可维护性：集中管理批量删除逻辑，便于维护和更新
5. 测试友好：可以单独测试验证器和权限检查器

最佳实践：

1. 为每种资源类型创建专门的验证器
2. 实现细粒度的权限检查
3. 使用事务确保数据一致性
4. 记录详细的审计日志
5. 提供清晰的错误信息和建议

迁移步骤：

1. 创建资源特定的验证器和权限检查器
2. 创建批量删除服务实例
3. 更新API端点以使用新服务
4. 测试新实现
5. 移除旧的批量删除代码
"""