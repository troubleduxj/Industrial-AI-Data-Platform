from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class BaseRole(BaseModel):
    id: int
    role_name: str
    remark: str = ""
    users: Optional[list] = []
    menus: Optional[list] = []
    apis: Optional[list] = []
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class RoleCreate(BaseModel):
    role_name: str = Field(example="管理员")
    remark: str = Field("", example="管理员角色")
    role_key: Optional[str] = Field(None, example="admin")
    role_sort: Optional[int] = Field(1, example=1)
    status: Optional[str] = Field("0", example="0")
    data_scope: Optional[str] = Field("1", example="1")
    menu_check_strictly: Optional[bool] = Field(True, example=True)
    dept_check_strictly: Optional[bool] = Field(True, example=True)
    parent_id: Optional[int] = Field(None, description="父角色ID，用于创建子角色")
    # V2 API权限字段
    sys_api_ids: Optional[List[int]] = Field(None, description="系统API权限ID列表")
    menu_ids: Optional[List[int]] = Field(None, description="菜单权限ID列表")
    # 保留V1 API兼容性
    api_ids: Optional[List[int]] = Field(None, description="V1 API权限ID列表（已弃用）")


class RoleUpdate(BaseModel):
    id: int = Field(example=1)
    role_name: str = Field(example="管理员")
    remark: str = Field("", example="管理员角色")
    role_key: Optional[str] = Field(None, example="admin")
    role_sort: Optional[int] = Field(None, example=1)
    status: Optional[str] = Field(None, example="0")
    data_scope: Optional[str] = Field(None, example="1")
    menu_check_strictly: Optional[bool] = Field(None, example=True)
    dept_check_strictly: Optional[bool] = Field(None, example=True)
    # V2 API权限字段
    sys_api_ids: Optional[List[int]] = Field(None, description="系统API权限ID列表")
    menu_ids: Optional[List[int]] = Field(None, description="菜单权限ID列表")
    # 保留V1 API兼容性
    api_ids: Optional[List[int]] = Field(None, description="V1 API权限ID列表（已弃用）")


class RolePatch(BaseModel):
    """角色部分更新模型 - 所有字段都是可选的"""
    role_name: Optional[str] = Field(None, example="管理员")
    remark: Optional[str] = Field(None, example="管理员角色")
    role_key: Optional[str] = Field(None, example="admin")
    role_sort: Optional[int] = Field(None, example=1)
    status: Optional[str] = Field(None, example="0")
    data_scope: Optional[str] = Field(None, example="1")
    menu_check_strictly: Optional[bool] = Field(None, example=True)
    dept_check_strictly: Optional[bool] = Field(None, example=True)


class RoleUpdateMenusApis(BaseModel):
    id: int
    menu_ids: list[int] = []
    api_infos: list[dict] = []


class RoleUsersUpdate(BaseModel):
    """角色用户更新模型"""
    user_ids: list[int] = Field([], description="用户ID列表")
    action: str = Field("replace", description="操作类型：replace(替换), add(添加), remove(移除)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_ids": [1, 2, 3],
                "action": "replace"
            }
        }


class RolePermissionsUpdate(BaseModel):
    """角色权限更新模型"""
    # V2 系统API权限字段（推荐使用）
    sys_api_ids: list[int] = Field([], description="V2系统API权限ID列表")
    menu_ids: list[int] = Field([], description="菜单权限ID列表")
    # V1 API权限字段（兼容性支持，已弃用）
    api_ids: list[int] = Field([], description="V1 API权限ID列表（已弃用）")
    action: str = Field("replace", description="操作类型：replace(替换), add(添加), remove(移除)")
    
    class Config:
        schema_extra = {
            "example": {
                "sys_api_ids": [1, 2, 3],
                "menu_ids": [4, 5, 6],
                "api_ids": [7, 8, 9],
                "action": "replace"
            }
        }
