from enum import Enum
from typing import Optional
import re

from pydantic import BaseModel, Field, validator, model_validator


class MenuType(str, Enum):
    CATALOG = "catalog"  # 目录
    MENU = "menu"  # 菜单
    BUTTON = "button"  # 按钮权限


class BaseMenu(BaseModel):
    id: int
    name: str
    path: str
    remark: Optional[dict]
    menu_type: Optional[MenuType]
    icon: Optional[str]
    order: Optional[int] = 0  # 修改为Optional，并设置默认值
    parent_id: Optional[int] = 0  # 修改为Optional，并设置默认值
    is_hidden: bool
    component: str
    keepalive: bool
    redirect: Optional[str]
    children: Optional[list["BaseMenu"]] = None

    class Config:
        from_attributes = True


class MenuCreate(BaseModel):
    menu_type: MenuType = Field(default=MenuType.CATALOG.value)
    name: str = Field(min_length=1, max_length=100, example="用户管理")
    icon: Optional[str] = "ph:user-list-bold"
    path: str = Field(example="/system/user")
    order: Optional[int] = Field(default=0, ge=0, le=9999, example=1)
    parent_id: Optional[int] = Field(example=0, default=0, ge=0)
    is_hidden: Optional[bool] = False
    component: str = Field(default="Layout", example="/system/user")
    keepalive: Optional[bool] = True
    redirect: Optional[str] = ""
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('菜单名称不能为空')
        return v.strip()
    
    @model_validator(mode='after')
    def validate_path_with_parent(self):
        path = self.path
        parent_id = self.parent_id
        
        if not path:
            return self
            
        if parent_id == 0 or parent_id is None:
            # 根菜单必须以/开头
            if not path.startswith('/'):
                raise ValueError('根菜单路径必须以/开头')
            if not re.match(r'^/[a-zA-Z0-9/_-]*$', path):
                raise ValueError('根菜单路径格式不正确，只能包含字母、数字、/、_、-')
        else:
            # 子菜单可以是相对路径或绝对路径
            if path.startswith('/'):
                # 绝对路径验证
                if not re.match(r'^/[a-zA-Z0-9/_-]*$', path):
                    raise ValueError('绝对路径格式不正确，只能包含字母、数字、/、_、-')
            else:
                # 相对路径验证 - 允许斜杠用于多级路径
                if not re.match(r'^[a-zA-Z0-9/_-]+$', path):
                    raise ValueError('相对路径格式不正确，只能包含字母、数字、/、_、-')
        
        return self


class MenuUpdate(BaseModel):
    menu_type: Optional[MenuType] = Field(None, example=MenuType.CATALOG.value)
    name: Optional[str] = Field(None, max_length=20, example="用户管理")
    icon: Optional[str] = Field(None, example="ph:user-list-bold")
    path: Optional[str] = Field(None, example="/system/user")
    order: Optional[int] = Field(None, example=1)
    parent_id: Optional[int] = Field(None, example=0)
    is_hidden: Optional[bool] = Field(None, example=False)
    component: Optional[str] = Field(None, example="/system/user")
    keepalive: Optional[bool] = Field(None, example=True)
    redirect: Optional[str] = Field(None, example="")
