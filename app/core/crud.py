from typing import Any, Dict, Generic, List, NewType, Tuple, Type, TypeVar, Union

from pydantic import BaseModel
from tortoise.expressions import Q
from tortoise.models import Model

Total = NewType("Total", int)
ModelType = TypeVar("ModelType", bound=Model)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, id: int) -> ModelType:
        return await self.model.get(id=id)

    async def get_multi_with_total(
        self, page: int, page_size: int, search: Union[Q, Dict[str, Any]] = None, order: list = []
    ) -> Tuple[Total, List[ModelType]]:
        if search is None:
            query = self.model.all()
        elif isinstance(search, Q):
            query = self.model.filter(search)
        else:
            query = self.model.filter(**search)
        return await query.count(), await query.offset((page - 1) * page_size).limit(page_size).order_by(*order)

    async def create(self, obj_in: Union[CreateSchemaType, Dict[str, Any]]) -> ModelType:
        """创建新对象"""
        # 将Pydantic模型转换为字典，排除None值
        if hasattr(obj_in, 'model_dump'):
            obj_dict = obj_in.model_dump(exclude_none=True)
        else:
            obj_dict = dict(obj_in)
        
        # 排除时间戳字段，让Tortoise ORM自动处理
        filtered_dict = {k: v for k, v in obj_dict.items() if k not in ['created_at', 'updated_at']}
        
        # 创建模型实例并使用setattr设置属性，这样会调用property setter
        obj = self.model()
        
        # 使用setattr设置属性，确保调用property setter（如Dept模型的name setter）
        for key, value in filtered_dict.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        
        # 保存到数据库
        await obj.save()
        
        return obj

    async def update(self, id: int, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        if isinstance(obj_in, dict):
            obj_dict = obj_in
        else:
            obj_dict = obj_in.model_dump(exclude_unset=True, exclude={"id"})
        obj = await self.get(id=id)
        for field, value in obj_dict.items():
            setattr(obj, field, value)
        await obj.save()
        return obj

    async def remove(self, id: int) -> None:
        from tortoise.exceptions import DoesNotExist
        try:
            obj = await self.get(id=id)
            await obj.delete()
        except DoesNotExist:
            # 如果对象不存在，静默处理
            pass

    async def list(self, page: int, page_size: int, search: Union[Q, Dict[str, Any]] = None, order: list = []) -> Tuple[Total, List[ModelType]]:
        """Alias for get_multi_with_total method for backward compatibility"""
        return await self.get_multi_with_total(page=page, page_size=page_size, search=search, order=order)
