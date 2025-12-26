"""
部门管理 API v2
实现完整的部门CRUD操作、树形结构查询和层级权限控制
"""
from typing import List, Optional
from fastapi import APIRouter, Request, Depends, Query, Body
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.core.response_formatter_v2 import ResponseFormatterV2, APIv2ErrorDetail
from app.schemas.base import BatchDeleteRequest
from app.core.dependency import DependAuth
from app.models.admin import User, Dept
from app.core.batch_delete_decorators import require_batch_delete_permission
from app.controllers.dept import dept_controller
from app.schemas.depts import DeptCreate, DeptUpdate, DeptPatch

router = APIRouter()

def build_dept_tree(depts: List[dict], parent_id: int = 0) -> List[dict]:
    """构建部门树结构"""
    tree = []
    for dept in depts:
        if dept.get("parent_id") == parent_id:
            children = build_dept_tree(depts, dept["id"])
            if children:
                dept["children"] = children
            tree.append(dept)
    return tree

@router.get("", summary="获取部门列表", description="获取部门列表 - 支持搜索、过滤和树形视图")
@router.get("/", summary="获取部门列表", description="获取部门列表 - 支持搜索、过滤和树形视图")
async def get_departments(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="部门名称搜索"),
    parent_id: Optional[int] = Query(None, description="父部门ID"),
    include_deleted: bool = Query(False, description="是否包含已删除部门"),
    view: Optional[str] = Query(None, description="视图类型：tree=树形视图，list=列表视图(默认)"),
    include_stats: bool = Query(True, description="是否包含统计信息(仅树形视图)"),
    current_user: User = DependAuth
):
    """
    获取部门列表 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 搜索和过滤
    - HATEOAS链接支持
    - 支持树形视图和列表视图
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 如果请求树形视图，直接返回树形结构
        if view == "tree":
            # 构建查询条件
            q = Q()
            query_params = {}
            if name:
                q &= Q(dept_name__icontains=name)
                query_params['name'] = name
            if parent_id is not None:
                q &= Q(parent_id=parent_id)
                query_params['parent_id'] = parent_id
            if not include_deleted:
                q &= Q(del_flag="0")
            query_params['include_deleted'] = include_deleted
            
            # 获取所有部门
            depts = await Dept.filter(q).order_by("parent_id", "order_num").all()
            
            # 转换为字典格式
            dept_dicts = []
            for dept in depts:
                dept_dict = await dept.to_dict()
                
                if include_stats:
                    # 添加统计信息
                    dept_dict["stats"] = {
                        "children_count": await Dept.filter(parent_id=dept.id, del_flag="0").count(),
                        "users_count": await User.filter(dept_id=dept.id).count(),
                        "total_descendants": await get_descendants_count(dept.id)
                    }
                    dept_dict["level"] = await get_dept_level(dept.id)
                
                dept_dicts.append(dept_dict)
            
            # 构建树形结构
            tree_data = build_dept_tree(dept_dicts)
            
            # 统计信息
            stats = {
                "total_departments": len(dept_dicts),
                "root_departments": len(tree_data),
                "max_depth": calculate_tree_depth(tree_data),
                "active_departments": len([d for d in dept_dicts if not d.get("del_flag", 0)]),
                "deleted_departments": len([d for d in dept_dicts if d.get("del_flag", 0)])
            }
            
            response_data = {
                "tree": tree_data,
                "stats": stats
            }
            
            return formatter.success(
                data=response_data,
                message="Department tree retrieved successfully",
                resource_type="departments"
            )
        else:
            # 构建查询条件
            q = Q()
            query_params = {}
            
            if name:
                q &= Q(dept_name__icontains=name)
                query_params['name'] = name
                
            if parent_id is not None:
                q &= Q(parent_id=parent_id)
                query_params['parent_id'] = parent_id
                
            if not include_deleted:
                q &= Q(del_flag="0")
            query_params['include_deleted'] = include_deleted
            
            # 执行查询
            result = await dept_controller.list(
                page=page,
                page_size=page_size,
                search=q
            )
            total, dept_objs = result
            
            # 转换数据格式
            dept_data = []
            for dept in dept_objs:
                dept_dict = await dept.to_dict()
                
                # 添加v2版本增强字段
                dept_dict["stats"] = {
                    "children_count": await Dept.filter(parent_id=dept.id, del_flag="0").count(),
                    "users_count": await User.filter(dept_id=dept.id).count(),
                    "total_descendants": await get_descendants_count(dept.id)
                }
                
                # 添加层级信息
                dept_dict["level"] = await get_dept_level(dept.id)
                
                dept_data.append(dept_dict)
            
            return formatter.paginated_success(
                data=dept_data,
                total=total,
                page=page,
                page_size=page_size,
                message="Departments retrieved successfully",
                resource_type="departments",
                query_params=query_params
            )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to retrieve departments: {str(e)}")

@router.get("/tree", summary="获取部门树", description="获取完整的部门树结构")
async def get_department_tree(
    request: Request,
    include_deleted: bool = Query(False, description="是否包含已删除部门"),
    include_stats: bool = Query(True, description="是否包含统计信息"),
    current_user: User = DependAuth
):
    """
    获取部门树 v2版本
    
    新功能：
    - 完整的树形结构
    - 可选择包含已删除部门
    - 统计信息
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 构建查询条件
        q = Q()
        if not include_deleted:
            q &= Q(del_flag="0")
        
        # 获取所有部门
        depts = await Dept.filter(q).order_by("parent_id", "order_num").all()
        
        # 转换为字典格式
        dept_dicts = []
        for dept in depts:
            dept_dict = await dept.to_dict()
            
            if include_stats:
                # 添加统计信息
                dept_dict["stats"] = {
                    "children_count": await Dept.filter(parent_id=dept.id, del_flag="0").count(),
                    "users_count": await User.filter(dept_id=dept.id).count(),
                    "total_descendants": await get_descendants_count(dept.id)
                }
                dept_dict["level"] = await get_dept_level(dept.id)
            
            dept_dicts.append(dept_dict)
        
        # 构建树形结构
        tree_data = build_dept_tree(dept_dicts)
        
        # 统计信息
        stats = {
            "total_departments": len(dept_dicts),
            "root_departments": len(tree_data),
            "max_depth": calculate_tree_depth(tree_data),
            "active_departments": len([d for d in dept_dicts if not d.get("del_flag", 0)]),
            "deleted_departments": len([d for d in dept_dicts if d.get("del_flag", 0)])
        }
        
        response_data = {
            "tree": tree_data,
            "stats": stats
        }
        
        return formatter.success(
            data=response_data,
            message="Department tree retrieved successfully",
            resource_type="departments"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to retrieve department tree: {str(e)}")

@router.get("/{dept_id}", summary="获取部门详情", description="根据ID获取部门详细信息")
async def get_department(
    request: Request,
    dept_id: int,
    current_user: User = DependAuth
):
    """
    获取部门详情 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 增强的部门信息
    - 父子关系信息
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        dept = await dept_controller.get(id=dept_id)
        if not dept:
            return formatter.not_found(f"Department with id {dept_id} not found", "department")
        
        # 获取部门详细信息
        dept_dict = await dept.to_dict()
        
        # 添加v2版本增强字段
        dept_dict["stats"] = {
            "children_count": await Dept.filter(parent_id=dept.id, del_flag="0").count(),
            "users_count": await User.filter(dept_id=dept.id).count(),
            "total_descendants": await get_descendants_count(dept.id)
        }
        
        # 添加层级信息
        dept_dict["level"] = await get_dept_level(dept.id)
        
        # 获取父部门信息
        if dept.parent_id and dept.parent_id > 0:
            parent_dept = await Dept.get_or_none(id=dept.parent_id)
            if parent_dept:
                dept_dict["parent"] = {
                    "id": parent_dept.id,
                    "name": parent_dept.dept_name,
                    "desc": parent_dept.desc
                }
        else:
            dept_dict["parent"] = None
        
        # 获取子部门列表
        children = await Dept.filter(parent_id=dept.id, del_flag="0").order_by("order_num").all()
        dept_dict["children"] = [
            {
                "id": child.id,
                "name": child.dept_name,
                "desc": child.desc,
                "order_num": child.order_num,
                "users_count": await User.filter(dept_id=child.id).count()
            }
            for child in children
        ]
        
        # 获取部门用户列表（前10个）
        users = await User.filter(dept_id=dept.id).limit(10).all()
        dept_dict["users_preview"] = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "alias": user.alias,
                "is_active": user.is_active
            }
            for user in users
        ]
        
        # 构建相关资源链接
        related_resources = {
            "children": f"/api/v2/departments?parent_id={dept_id}",
            "users": f"/api/v2/departments/{dept_id}/users"
        }
        
        if dept.parent_id and dept.parent_id > 0:
            related_resources["parent"] = f"/api/v2/departments/{dept.parent_id}"
        
        return formatter.success(
            data=dept_dict,
            message="Department details retrieved successfully",
            resource_id=str(dept_id),
            resource_type="departments",
            related_resources=related_resources
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to retrieve department: {str(e)}")

@router.post("", summary="创建部门", description="创建新部门")
@router.post("/", summary="创建部门", description="创建新部门")
async def create_department(
    request: Request,
    dept_data: DeptCreate,
    current_user: User = DependAuth
):
    """
    创建部门 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 增强的验证和错误处理
    - 层级验证
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 记录接收到的原始数据用于审计
        # print(f"[DEBUG] API接收到的原始数据: {dept_data}")
        
        # 验证部门名是否已存在
        existing_dept = await Dept.filter(dept_name=dept_data.name, del_flag="0").first()
        if existing_dept:
            return formatter.validation_error(
                message="Department with this name already exists",
                details=[APIv2ErrorDetail(
                    field="name",
                    code="DUPLICATE_NAME",
                    message="Department name is already taken",
                    value=dept_data.name
                )]
            )
        
        # 验证父部门是否存在
        if dept_data.parent_id and dept_data.parent_id > 0:
            parent_dept = await Dept.get_or_none(id=dept_data.parent_id, del_flag="0")
            if not parent_dept:
                return formatter.validation_error(
                    message="Parent department not found",
                    details=[APIv2ErrorDetail(
                        field="parent_id",
                        code="PARENT_NOT_FOUND",
                        message="Specified parent department does not exist",
                        value=dept_data.parent_id
                    )]
                )
        
        # 创建部门
        new_dept = await dept_controller.create_dept(obj_in=dept_data)
        
        # 获取创建后的部门信息
        dept_dict = await new_dept.to_dict()
        dept_dict["level"] = await get_dept_level(new_dept.id)
        dept_dict["stats"] = {
            "children_count": 0,
            "users_count": 0,
            "total_descendants": 0
        }
        
        return formatter.success(
            data=dept_dict,
            message="Department created successfully",
            code=201,
            resource_id=str(new_dept.id),
            resource_type="departments"
        )
        
    except Exception as e:
        # DEBUG: 记录详细的异常信息
        import traceback
        print(f"[DEBUG] 创建部门时发生异常: {str(e)}")
        print(f"[DEBUG] 异常类型: {type(e)}")
        print(f"[DEBUG] 异常堆栈: {traceback.format_exc()}")
        return formatter.internal_error(f"Failed to create department: {str(e)}")

@router.post("/batch", summary="批量创建部门", description="批量创建多个部门")
async def batch_create_departments(
    request: Request,
    departments_data: List[DeptCreate],
    current_user: User = DependAuth
):
    """
    批量创建部门 v2版本
    
    新功能：
    - 支持批量创建多个部门
    - 事务性操作（全部成功或全部失败）
    - 详细的验证和错误报告
    - 标准化v2响应格式
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 验证departments_data参数
        if not departments_data:
            return formatter.validation_error(
                message="No departments data provided",
                details=[APIv2ErrorDetail(
                    field="departments_data",
                    code="EMPTY_DATA",
                    message="At least one department must be provided",
                    value=None
                )]
            )
        
        if len(departments_data) > 50:  # 限制批量操作数量
            return formatter.validation_error(
                message="Too many departments in batch operation",
                details=[APIv2ErrorDetail(
                    field="departments_data",
                    code="BATCH_SIZE_EXCEEDED",
                    message="Maximum 50 departments allowed per batch operation",
                    value=len(departments_data)
                )]
            )
        
        # 预验证所有部门数据
        validation_errors = []
        dept_names = [dept.name for dept in departments_data]
        
        # 检查批次内部门名称重复
        name_counts = {}
        for i, dept in enumerate(departments_data):
            if dept.name in name_counts:
                validation_errors.append(APIv2ErrorDetail(
                    field=f"departments_data[{i}].name",
                    code="DUPLICATE_NAME_IN_BATCH",
                    message=f"Department name '{dept.name}' appears multiple times in batch",
                    value=dept.name
                ))
            else:
                name_counts[dept.name] = i
        
        # 检查数据库中是否已存在同名部门
        existing_depts = await Dept.filter(dept_name__in=dept_names, del_flag="0").all()
        existing_names = {dept.dept_name for dept in existing_depts}
        
        for i, dept in enumerate(departments_data):
            if dept.name in existing_names:
                validation_errors.append(APIv2ErrorDetail(
                    field=f"departments_data[{i}].name",
                    code="DUPLICATE_NAME",
                    message=f"Department name '{dept.name}' already exists",
                    value=dept.name
                ))
        
        # 验证父部门ID
        parent_ids = [dept.parent_id for dept in departments_data if dept.parent_id and dept.parent_id > 0]
        if parent_ids:
            existing_parents = await Dept.filter(id__in=parent_ids, del_flag="0").all()
            existing_parent_ids = {dept.id for dept in existing_parents}
            
            for i, dept in enumerate(departments_data):
                if dept.parent_id and dept.parent_id > 0 and dept.parent_id not in existing_parent_ids:
                    validation_errors.append(APIv2ErrorDetail(
                        field=f"departments_data[{i}].parent_id",
                        code="PARENT_NOT_FOUND",
                        message=f"Parent department with id {dept.parent_id} does not exist",
                        value=dept.parent_id
                    ))
        
        if validation_errors:
            return formatter.validation_error(
                message="Validation failed for batch create operation",
                details=validation_errors
            )
        
        # 记录批量创建操作用于审计
        # print(f"[DEBUG] 批量创建部门，共{len(departments_data)}个部门")
        
        # 使用事务批量创建部门
        created_departments = []
        async with in_transaction():
            for i, dept_data in enumerate(departments_data):
                try:
                    # 使用create_dept方法，它会自动处理层级关系
                    new_dept = await dept_controller.create_dept(obj_in=dept_data)
                    created_departments.append(new_dept)
                except Exception as e:
                    # 记录异常信息用于调试
                    import traceback
                    print(f"[ERROR] 第{i+1}个部门创建失败: {str(e)}")
                    print(f"[ERROR] 异常堆栈: {traceback.format_exc()}")
                    raise
        
        # 构建响应数据
        result_data = []
        for dept in created_departments:
            try:
                # 重新获取部门对象以确保是完整的模型实例
                fresh_dept = await dept_controller.get(id=dept.id)
                # to_dict方法是异步的，需要await
                dept_dict = await fresh_dept.to_dict()
                dept_dict["level"] = await get_dept_level(dept.id)
                dept_dict["stats"] = {
                    "children_count": 0,
                    "users_count": 0,
                    "total_descendants": 0
                }
                result_data.append(dept_dict)
            except Exception as e:
                print(f"[ERROR] 处理部门{dept.id}时出错: {str(e)}")
                # 如果获取失败，使用基本信息
                result_data.append({
                    "id": dept.id,
                    "dept_name": getattr(dept, 'dept_name', getattr(dept, 'name', 'Unknown')),
                    "level": await get_dept_level(dept.id),
                    "stats": {
                        "children_count": 0,
                        "users_count": 0,
                        "total_descendants": 0
                    }
                })
        
        return formatter.success(
            data={
                "departments": result_data,
                "summary": {
                    "total_created": len(created_departments),
                    "created_ids": [dept.id for dept in created_departments]
                }
            },
            message=f"Successfully created {len(created_departments)} departments",
            code=201,
            resource_type="departments"
        )
        
    except Exception as e:
        # 记录详细的异常信息用于调试
        import traceback
        print(f"[ERROR] 批量创建部门时发生异常: {str(e)}")
        print(f"[ERROR] 异常堆栈: {traceback.format_exc()}")
        return formatter.internal_error(f"Failed to batch create departments: {str(e)}")

@router.put("/{dept_id}", summary="更新部门", description="更新部门信息")
async def update_department(
    request: Request,
    dept_id: int,
    dept_data: DeptUpdate,
    current_user: User = DependAuth
):
    """
    更新部门 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 增强的验证和错误处理
    - 层级验证
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 验证请求体中的ID与URL中的ID是否匹配
        if hasattr(dept_data, 'id') and dept_data.id != dept_id:
            return formatter.validation_error(
                message="ID mismatch between URL and request body",
                details=[APIv2ErrorDetail(
                    field="id",
                    code="ID_MISMATCH",
                    message=f"ID in request body ({dept_data.id}) does not match URL parameter ({dept_id})",
                    value=dept_data.id
                )]
            )
        
        # 检查部门是否存在
        dept = await dept_controller.get(id=dept_id)
        if not dept:
            return formatter.not_found(f"Department with id {dept_id} not found", "department")
        
        # 验证部门名是否被其他部门使用
        if hasattr(dept_data, 'name') and dept_data.name != dept.dept_name:
            existing_dept = await Dept.filter(dept_name=dept_data.name, del_flag="0").first()
            if existing_dept and existing_dept.id != dept_id:
                return formatter.validation_error(
                    message="Department name is already taken by another department",
                    details=[APIv2ErrorDetail(
                        field="name",
                        code="DUPLICATE_NAME",
                        message="Department name is already taken",
                        value=dept_data.name
                    )]
                )
        
        # 验证父部门设置（防止循环引用）
        if hasattr(dept_data, 'parent_id') and dept_data.parent_id:
            if dept_data.parent_id == dept_id:
                return formatter.validation_error(
                    message="Department cannot be its own parent",
                    details=[APIv2ErrorDetail(
                        field="parent_id",
                        code="CIRCULAR_REFERENCE",
                        message="Department cannot be its own parent",
                        value=dept_data.parent_id
                    )]
                )
            
            # 检查是否会形成循环引用
            if await is_circular_reference(dept_id, dept_data.parent_id):
                return formatter.validation_error(
                    message="This would create a circular reference",
                    details=[APIv2ErrorDetail(
                        field="parent_id",
                        code="CIRCULAR_REFERENCE",
                        message="Setting this parent would create a circular reference",
                        value=dept_data.parent_id
                    )]
                )
        
        # 更新部门
        dept_data.id = dept_id  # 确保ID正确
        updated_dept = await dept_controller.update(id=dept_id, obj_in=dept_data)
        
        # 获取更新后的部门信息
        dept_dict = await updated_dept.to_dict()
        dept_dict["level"] = await get_dept_level(updated_dept.id)
        dept_dict["stats"] = {
            "children_count": await Dept.filter(parent_id=dept_id, del_flag="0").count(),
            "users_count": await User.filter(dept_id=dept_id).count(),
            "total_descendants": await get_descendants_count(dept_id)
        }
        
        return formatter.success(
            data=dept_dict,
            message="Department updated successfully",
            resource_id=str(dept_id),
            resource_type="departments"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to update department: {str(e)}")

@router.patch("/{dept_id}", summary="部分更新部门", description="部分更新部门信息（PATCH方法）")
async def patch_department(
    request: Request,
    dept_id: int,
    dept_data: DeptPatch,
    current_user: User = DependAuth
):
    """
    部分更新部门 v2版本
    
    新功能：
    - 支持PATCH方法进行部分更新
    - 只更新提供的字段
    - 标准化v2响应格式
    - 增强的验证和错误处理
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查部门是否存在
        dept = await dept_controller.get(id=dept_id)
        if not dept:
            return formatter.not_found(f"Department with id {dept_id} not found", "department")
        
        # 将Pydantic模型转换为字典，只包含设置的字段
        dept_data_dict = dept_data.model_dump(exclude_unset=True)
        
        # 验证输入数据
        allowed_fields = {'name', 'desc', 'parent_id', 'order_num', 'is_active'}
        invalid_fields = set(dept_data_dict.keys()) - allowed_fields
        if invalid_fields:
            return formatter.validation_error(
                message="Invalid fields provided",
                details=[APIv2ErrorDetail(
                    field=field,
                    code="INVALID_FIELD",
                    message=f"Field '{field}' is not allowed for update",
                    value=dept_data_dict[field]
                ) for field in invalid_fields]
            )
        
        # 验证部门名是否被其他部门使用
        if 'name' in dept_data_dict and dept_data_dict['name'] != dept.dept_name:
            existing_dept = await Dept.filter(dept_name=dept_data_dict['name'], del_flag="0").first()
            if existing_dept and existing_dept.id != dept_id:
                return formatter.validation_error(
                    message="Department name is already taken by another department",
                    details=[APIv2ErrorDetail(
                        field="name",
                        code="DUPLICATE_NAME",
                        message="Department name is already taken",
                        value=dept_data_dict['name']
                    )]
                )
        
        # 验证父部门设置（防止循环引用）
        if 'parent_id' in dept_data_dict and dept_data_dict['parent_id']:
            if dept_data_dict['parent_id'] == dept_id:
                return formatter.validation_error(
                    message="Department cannot be its own parent",
                    details=[APIv2ErrorDetail(
                        field="parent_id",
                        code="CIRCULAR_REFERENCE",
                        message="Department cannot be its own parent",
                        value=dept_data_dict['parent_id']
                    )]
                )
            
            # 检查父部门是否存在
            parent_dept = await Dept.get_or_none(id=dept_data_dict['parent_id'], del_flag="0")
            if not parent_dept:
                return formatter.validation_error(
                    message="Parent department not found",
                    details=[APIv2ErrorDetail(
                        field="parent_id",
                        code="PARENT_NOT_FOUND",
                        message="Specified parent department does not exist",
                        value=dept_data_dict['parent_id']
                    )]
                )
            
            # 检查是否会形成循环引用
            if await is_circular_reference(dept_id, dept_data_dict['parent_id']):
                return formatter.validation_error(
                    message="This would create a circular reference",
                    details=[APIv2ErrorDetail(
                        field="parent_id",
                        code="CIRCULAR_REFERENCE",
                        message="Setting this parent would create a circular reference",
                        value=dept_data_dict['parent_id']
                    )]
                )
        
        # 部分更新部门 - 处理字段映射
        for field, value in dept_data_dict.items():
            if field == 'name':
                dept.dept_name = value
            elif field == 'desc':
                # desc现在可以通过setter设置到leader字段
                dept.desc = value
            elif field == 'parent_id':
                dept.parent_id = value
            elif field == 'order_num':
                dept.order_num = value
            elif field == 'is_active':
                dept.status = "0" if value else "1"
            elif hasattr(dept, field):
                setattr(dept, field, value)
        
        await dept.save()
        
        # 获取更新后的部门信息
        dept_dict = await dept.to_dict()
        dept_dict["level"] = await get_dept_level(dept.id)
        dept_dict["stats"] = {
            "children_count": await Dept.filter(parent_id=dept_id, del_flag="0").count(),
            "users_count": await User.filter(dept_id=dept_id).count(),
            "total_descendants": await get_descendants_count(dept_id)
        }
        
        return formatter.success(
            data=dept_dict,
            message="Department partially updated successfully",
            resource_id=str(dept_id),
            resource_type="departments"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to partially update department: {str(e)}")

@router.delete("/batch", summary="批量删除部门", description="批量删除多个部门（支持软删除和硬删除）")
@require_batch_delete_permission("department")
async def batch_delete_departments(
    request: Request,
    batch_request: BatchDeleteRequest,
    current_user: User = DependAuth
):
    """
    批量删除部门 v2版本
    
    使用标准化数据格式：{"ids": [1, 2, 3], "force": false}
    返回标准化响应格式，包含用户友好的错误提示
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        from app.services.batch_delete_service import department_batch_delete_service
        from tortoise.transactions import in_transaction
        
        dept_ids = batch_request.ids
        force = batch_request.force
        
        if not dept_ids:
            return formatter.validation_error(
                message="部门ID列表不能为空",
                details=[APIv2ErrorDetail(
                    field="ids",
                    code="EMPTY_LIST",
                    message="部门ID列表不能为空",
                    value=dept_ids
                )]
            )
        
        async with in_transaction():
            # 使用标准化批量删除服务
            result = await department_batch_delete_service.batch_delete(
                ids=dept_ids,
                force=force
            )
            
            # 生成用户友好的响应消息
            if result.failed_count == 0:
                message = f"成功删除 {result.deleted_count} 个部门"
            elif result.deleted_count == 0:
                failed_reasons = [item.reason for item in result.failed]
                message = f"删除失败：{'; '.join(failed_reasons)}"
            else:
                failed_details = [f"{item.name or item.id}：{item.reason}" for item in result.failed]
                message = f"批量删除完成：成功删除 {result.deleted_count} 个，失败 {result.failed_count} 个部门。失败原因：{'; '.join(failed_details)}"
            
            return formatter.success(
                data=result.model_dump(),
                message=message,
                resource_type="departments"
            )
            
    except Exception as e:
        return formatter.internal_error(f"批量删除部门失败: {str(e)}")

@router.delete("/{dept_id}", summary="删除部门", description="删除指定部门（软删除）")
async def delete_department(
    dept_id: int,
    request: Request,
    force: bool = Query(False, description="是否强制删除（硬删除）"),
    current_user: User = DependAuth
):
    """
    删除部门 v2版本
    
    新功能：
    - 标准化v2响应格式
    - 软删除和硬删除选项
    - 层级删除检查
    - 与批量删除一致的验证逻辑和错误处理
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查部门是否存在
        dept = await dept_controller.get(id=dept_id)
        if not dept:
            return formatter.not_found(f"Department with id {dept_id} not found", "department")
        
        # 使用与批量删除相同的验证逻辑
        validation_errors = []
        
        # 检查是否有子部门
        children_count = await Dept.filter(parent_id=dept_id, del_flag="0").count()
        if children_count > 0:
            validation_errors.append(APIv2ErrorDetail(
                field="dept_id",
                code="HAS_CHILDREN",
                message=f"Department '{dept.dept_name}' has {children_count} child departments",
                value=dept_id,
                constraint="no_children_required"
            ))
        
        # 检查是否有用户
        users_count = await User.filter(dept_id=dept_id).count()
        if users_count > 0:
            validation_errors.append(APIv2ErrorDetail(
                field="dept_id",
                code="HAS_USERS",
                message=f"Department '{dept.dept_name}' has {users_count} users assigned",
                value=dept_id,
                constraint="no_users_required"
            ))
        
        # 如果有验证错误且不是强制删除，返回错误
        if validation_errors and not force:
            return formatter.validation_error(
                message="Department cannot be deleted",
                details=validation_errors,
                suggestion="Please move users to other departments or delete child departments first, or use force=true to override"
            )
        
        # 执行删除操作
        deletion_type = "permanent" if force else "soft"
        
        if force:
            # 硬删除
            await dept_controller.remove(id=dept_id)
        else:
            # 软删除
            dept.del_flag = "2"
            await dept.save()
        
        # 构建删除结果数据（与批量删除格式一致）
        deleted_department = {
            "id": dept.id,
            "name": dept.dept_name,
            "deletion_type": deletion_type
        }
        
        return formatter.success(
            data={
                "deleted_department": deleted_department,
                "summary": {
                    "total_deleted": 1,
                    "deletion_type": deletion_type,
                    "successful_ids": [dept_id],
                    "failed_ids": []
                }
            },
            message=f"Department successfully {deletion_type}ly deleted",
            resource_id=str(dept_id),
            resource_type="departments"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to delete department: {str(e)}")
    """
    批量删除部门 v2版本
    
    新功能：
    - 支持批量删除多个部门
    - 事务性操作，全部成功或全部失败
    - 详细的验证和错误报告
    - 软删除和硬删除选项
    - 标准化v2响应格式
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 从请求体中提取参数
        if not isinstance(body, dict):
            return formatter.validation_error(
                message="Request body must be a JSON object",
                details=[APIv2ErrorDetail(
                    field="body",
                    code="INVALID_FORMAT",
                    message="Request body must be a valid JSON object",
                    value=str(body)
                )]
            )
        
        dept_ids = body.get("department_ids")
        force = body.get("force", False)
        
        if dept_ids is None:
            return formatter.validation_error(
                message="Missing required field: department_ids",
                details=[APIv2ErrorDetail(
                    field="department_ids",
                    code="MISSING_FIELD",
                    message="department_ids field is required",
                    value=None
                )]
            )
        
        if not isinstance(dept_ids, list):
            return formatter.validation_error(
                message="department_ids must be a list",
                details=[APIv2ErrorDetail(
                    field="department_ids",
                    code="INVALID_TYPE",
                    message="department_ids must be a list of integers",
                    value=dept_ids
                )]
            )
        
        if not dept_ids:
            return formatter.validation_error(
                message="Department IDs list cannot be empty",
                details=[APIv2ErrorDetail(
                    field="department_ids",
                    code="EMPTY_LIST",
                    message="At least one department ID must be provided",
                    value=dept_ids
                )]
            )
        
        # 限制批量操作数量
        if len(dept_ids) > 50:
            return formatter.validation_error(
                message="Too many departments for batch operation",
                details=[APIv2ErrorDetail(
                    field="department_ids",
                    code="BATCH_SIZE_EXCEEDED",
                    message="Maximum 50 departments allowed per batch operation",
                    value=len(dept_ids)
                )]
            )
        
        # 去重
        dept_ids = list(set(dept_ids))
        
        # 验证所有部门是否存在
        existing_depts = await Dept.filter(id__in=dept_ids, del_flag="0").all()
        existing_ids = {dept.id for dept in existing_depts}
        missing_ids = set(dept_ids) - existing_ids
        
        if missing_ids:
            return formatter.validation_error(
                message="Some departments not found",
                details=[APIv2ErrorDetail(
                    field="department_ids",
                    code="DEPARTMENTS_NOT_FOUND",
                    message=f"Departments with IDs {list(missing_ids)} not found",
                    value=list(missing_ids)
                )]
            )
        
        # 检查每个部门的删除条件
        validation_errors = []
        
        for dept in existing_depts:
            # 检查是否有子部门
            children_count = await Dept.filter(parent_id=dept.id, del_flag="0").count()
            if children_count > 0:
                validation_errors.append(APIv2ErrorDetail(
                    field=f"dept_id_{dept.id}",
                    code="HAS_CHILDREN",
                    message=f"Department '{dept.dept_name}' has {children_count} child departments",
                    value=dept.id
                ))
            
            # 检查是否有用户
            users_count = await User.filter(dept_id=dept.id).count()
            if users_count > 0:
                validation_errors.append(APIv2ErrorDetail(
                    field=f"dept_id_{dept.id}",
                    code="HAS_USERS",
                    message=f"Department '{dept.dept_name}' has {users_count} users",
                    value=dept.id
                ))
        
        if validation_errors:
            return formatter.validation_error(
                message="Some departments cannot be deleted",
                details=validation_errors
            )
        
        # 执行批量删除（事务性操作）
        deleted_departments = []
        
        async with in_transaction():
            for dept in existing_depts:
                if force:
                    # 硬删除
                    await dept.delete()
                else:
                    # 软删除
                    dept.del_flag = "2"
                    await dept.save()
                
                deleted_departments.append({
                    "id": dept.id,
                    "name": dept.dept_name,
                    "deletion_type": "permanent" if force else "soft"
                })
        
        operation_type = "permanently deleted" if force else "marked as deleted"
        
        return formatter.success(
            data={
                "deleted_departments": deleted_departments,
                "total_deleted": len(deleted_departments),
                "deletion_type": "permanent" if force else "soft"
            },
            message=f"Successfully {operation_type} {len(deleted_departments)} departments",
            code=200,
            resource_type="departments"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to batch delete departments: {str(e)}")

@router.get("/{dept_id}/children", summary="获取直接子部门", description="获取指定部门的直接子部门列表")
async def get_department_children(
    request: Request,
    dept_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    include_deleted: bool = Query(False, description="是否包含已删除的子部门"),
    include_stats: bool = Query(True, description="是否包含统计信息"),
    current_user: User = DependAuth
):
    """
    获取直接子部门 v2版本
    
    新功能：
    - 只返回直接子部门，不包含孙子部门
    - 支持分页
    - 可选择包含已删除部门
    - 可选择包含统计信息
    - 标准化v2响应格式
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查父部门是否存在
        parent_dept = await dept_controller.get(id=dept_id)
        if not parent_dept:
            return formatter.not_found(f"Department with id {dept_id} not found", "department")
        
        # 构建查询条件
        q = Q(parent_id=dept_id)
        
        if not include_deleted:
            q &= Q(del_flag="0")
        
        # 获取总数
        total = await Dept.filter(q).count()
        
        # 分页查询
        offset = (page - 1) * page_size
        children = await Dept.filter(q).order_by("order_num", "dept_name").offset(offset).limit(page_size).all()
        
        # 转换数据格式
        children_data = []
        for child in children:
            child_dict = await child.to_dict()
            
            if include_stats:
                # 添加统计信息
                child_dict["stats"] = {
                    "children_count": await Dept.filter(parent_id=child.id, del_flag="0").count(),
                    "users_count": await User.filter(dept_id=child.id).count(),
                    "total_descendants": await get_descendants_count(child.id)
                }
                child_dict["level"] = await get_dept_level(child.id)
            
            children_data.append(child_dict)
        
        # 构建响应数据
        response_data = {
            "parent_department": {
                "id": parent_dept.id,
                "name": parent_dept.dept_name
            },
            "children": children_data,
            "summary": {
                "total_children": total,
                "active_children": len([c for c in children_data if c.get("del_flag", "0") == "0"]),
            "deleted_children": len([c for c in children_data if c.get("del_flag", "0") == "1"])
            }
        }
        
        return formatter.paginated_success(
            data=response_data,
            total=total,
            page=page,
            page_size=page_size,
            message=f"Children of department '{parent_dept.dept_name}' retrieved successfully",
            resource_type="departments"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to retrieve department children: {str(e)}")

@router.get("/{dept_id}/users", summary="获取部门用户", description="获取指定部门的用户列表")
async def get_department_users(
    dept_id: int,
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    include_descendants: bool = Query(False, description="是否包含子部门用户"),
    current_user: User = DependAuth
):
    """
    获取部门用户 v2版本
    
    新功能：
    - 分页支持
    - 可选择包含子部门用户
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查部门是否存在
        dept = await dept_controller.get(id=dept_id)
        if not dept:
            return formatter.not_found(f"Department with id {dept_id} not found", "department")
        
        # 构建查询条件
        if include_descendants:
            # 获取所有子部门ID
            descendant_ids = await get_all_descendant_ids(dept_id)
            dept_ids = [dept_id] + descendant_ids
            q = Q(dept_id__in=dept_ids)
        else:
            q = Q(dept_id=dept_id)
        
        # 获取用户（分页）
        offset = (page - 1) * page_size
        users = await User.filter(q).offset(offset).limit(page_size).all()
        total = await User.filter(q).count()
        
        # 转换用户数据
        user_data = []
        for user in users:
            user_dict = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "alias": user.alias,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            
            # 如果包含子部门用户，添加部门信息
            if include_descendants and user.dept_id != dept_id:
                user_dept = await Dept.get_or_none(id=user.dept_id)
                if user_dept:
                    user_dict["department"] = {
                        "id": user_dept.id,
                        "name": user_dept.dept_name
                    }
            
            user_data.append(user_dict)
        
        return formatter.paginated_success(
            data=user_data,
            total=total,
            page=page,
            page_size=page_size,
            message=f"Users in department '{dept.dept_name}' retrieved successfully",
            resource_type="users"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to retrieve department users: {str(e)}")

@router.put("/{dept_id}/users/{user_id}", summary="用户加入部门", description="将指定用户加入到部门")
async def add_user_to_department(
    request: Request,
    dept_id: int,
    user_id: int,
    current_user: User = DependAuth
):
    """
    用户加入部门 v2版本
    
    新功能：
    - 精细化的用户部门关联管理
    - 详细的验证和错误处理
    - 标准化v2响应格式
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查部门是否存在
        dept = await dept_controller.get(id=dept_id)
        if not dept:
            return formatter.not_found(f"Department with id {dept_id} not found", "department")
        
        # 检查用户是否存在
        user = await User.get_or_none(id=user_id)
        if not user:
            return formatter.not_found(f"User with id {user_id} not found", "user")
        
        # 检查用户是否已经在该部门
        if user.dept_id == dept_id:
            return formatter.validation_error(
                message="User is already in this department",
                details=[APIv2ErrorDetail(
                    field="user_id",
                    code="ALREADY_IN_DEPARTMENT",
                    message=f"User '{user.username}' is already in department '{dept.dept_name}'",
                    value=user_id
                )]
            )
        
        # 记录原部门信息（用于响应）
        old_dept = None
        if user.dept_id:
            old_dept = await Dept.get_or_none(id=user.dept_id)
        
        # 更新用户部门
        user.dept_id = dept_id
        await user.save()
        
        # 构建响应数据
        response_data = {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "alias": user.alias
            },
            "department": {
                "id": dept.id,
                "name": dept.dept_name
            },
            "previous_department": {
                "id": old_dept.id if old_dept else None,
                "name": old_dept.dept_name if old_dept else None
            } if old_dept else None,
            "operation": "user_added_to_department"
        }
        
        return formatter.success(
            data=response_data,
            message=f"User '{user.username}' successfully added to department '{dept.dept_name}'",
            resource_id=f"{dept_id}-{user_id}",
            resource_type="department_user_association"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to add user to department: {str(e)}")

@router.delete("/{dept_id}/users/{user_id}", summary="用户移出部门", description="将指定用户从部门移出")
async def remove_user_from_department(
    request: Request,
    dept_id: int,
    user_id: int,
    target_dept_id: Optional[int] = Query(None, description="目标部门ID（可选，不指定则用户无部门）"),
    current_user: User = DependAuth
):
    """
    用户移出部门 v2版本
    
    新功能：
    - 精细化的用户部门关联管理
    - 可选择移动到其他部门或设为无部门
    - 详细的验证和错误处理
    - 标准化v2响应格式
    """
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查部门是否存在
        dept = await dept_controller.get(id=dept_id)
        if not dept:
            return formatter.not_found(f"Department with id {dept_id} not found", "department")
        
        # 检查用户是否存在
        user = await User.get_or_none(id=user_id)
        if not user:
            return formatter.not_found(f"User with id {user_id} not found", "user")
        
        # 检查用户是否在该部门
        if user.dept_id != dept_id:
            current_dept = await Dept.get_or_none(id=user.dept_id) if user.dept_id else None
            return formatter.validation_error(
                message="User is not in this department",
                details=[APIv2ErrorDetail(
                    field="user_id",
                    code="NOT_IN_DEPARTMENT",
                    message=f"User '{user.username}' is not in department '{dept.dept_name}'. Current department: {current_dept.dept_name if current_dept else 'None'}",
                    value=user_id
                )]
            )
        
        # 如果指定了目标部门，检查目标部门是否存在
        target_dept = None
        if target_dept_id:
            target_dept = await Dept.get_or_none(id=target_dept_id, del_flag="0")
            if not target_dept:
                return formatter.validation_error(
                    message="Target department not found",
                    details=[APIv2ErrorDetail(
                        field="target_dept_id",
                        code="TARGET_DEPARTMENT_NOT_FOUND",
                        message=f"Target department with id {target_dept_id} not found",
                        value=target_dept_id
                    )]
                )
        
        # 更新用户部门
        user.dept_id = target_dept_id
        await user.save()
        
        # 构建响应数据
        response_data = {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "alias": user.alias
            },
            "removed_from_department": {
                "id": dept.id,
                "name": dept.dept_name
            },
            "moved_to_department": {
                "id": target_dept.id if target_dept else None,
                "name": target_dept.dept_name if target_dept else None
            } if target_dept else None,
            "operation": "user_moved_to_department" if target_dept else "user_removed_from_department"
        }
        
        if target_dept:
            message = f"User '{user.username}' successfully moved from '{dept.dept_name}' to '{target_dept.dept_name}'"
        else:
            message = f"User '{user.username}' successfully removed from department '{dept.dept_name}'"
        
        return formatter.success(
            data=response_data,
            message=message,
            resource_id=f"{dept_id}-{user_id}",
            resource_type="department_user_association"
        )
        
    except Exception as e:
        return formatter.internal_error(f"Failed to remove user from department: {str(e)}")

# 辅助函数
async def get_dept_level(dept_id: int) -> int:
    """获取部门层级"""
    level = 0
    current_id = dept_id
    
    while current_id:
        dept = await Dept.get_or_none(id=current_id)
        if not dept or dept.parent_id == 0:
            break
        current_id = dept.parent_id
        level += 1
        
        # 防止无限循环
        if level > 10:
            break
    
    return level

async def get_descendants_count(dept_id: int) -> int:
    """获取所有后代部门数量"""
    count = 0
    children = await Dept.filter(parent_id=dept_id, del_flag="0").all()
    
    for child in children:
        count += 1
        count += await get_descendants_count(child.id)
    
    return count

async def get_all_descendant_ids(dept_id: int) -> List[int]:
    """获取所有后代部门ID"""
    descendant_ids = []
    children = await Dept.filter(parent_id=dept_id, del_flag="0").all()
    
    for child in children:
        descendant_ids.append(child.id)
        descendant_ids.extend(await get_all_descendant_ids(child.id))
    
    return descendant_ids

async def is_circular_reference(dept_id: int, parent_id: int) -> bool:
    """检查是否会形成循环引用"""
    current_id = parent_id
    visited = set()
    
    while current_id and current_id not in visited:
        if current_id == dept_id:
            return True
        
        visited.add(current_id)
        dept = await Dept.get_or_none(id=current_id)
        if not dept:
            break
        
        current_id = dept.parent_id if dept.parent_id != 0 else None
    
    return False

def calculate_tree_depth(tree: List[dict]) -> int:
    """计算树的最大深度"""
    if not tree:
        return 0
    
    max_depth = 0
    for node in tree:
        depth = 1
        if "children" in node:
            depth += calculate_tree_depth(node["children"])
        max_depth = max(max_depth, depth)
    
    return max_depth