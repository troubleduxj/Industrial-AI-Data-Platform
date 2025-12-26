from pydantic import BaseModel, Field
from typing import Optional


class BaseDept(BaseModel):
    name: Optional[str] = Field(None, description="部门名称", example="研发中心")
    desc: str = Field("", description="备注", example="研发中心")
    order_num: int = Field(0, description="排序")
    parent_id: Optional[int] = Field(0, description="父部门ID")


class DeptCreate(BaseDept): ...


class DeptUpdate(BaseDept):
    id: int

    def update_dict(self):
        return self.model_dump(exclude_unset=True, exclude={"id"})


class DeptPatch(BaseModel):
    """部门部分更新模型 - 所有字段都是可选的"""
    name: Optional[str] = Field(None, description="部门名称", example="研发中心")
    desc: Optional[str] = Field(None, description="备注", example="研发中心")
    order_num: Optional[int] = Field(None, description="排序")
    parent_id: Optional[int] = Field(None, description="父部门ID")
    is_active: Optional[bool] = Field(None, description="是否激活")

    def update_dict(self):
        return self.model_dump(exclude_unset=True)
