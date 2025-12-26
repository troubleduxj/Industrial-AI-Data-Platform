import asyncio
from datetime import datetime

from tortoise import fields, models

from app.settings import settings


class BaseModel(models.Model):
    id = fields.BigIntField(pk=True, index=True)

    async def to_dict(self, m2m: bool = False, exclude_fields: list[str] | None = None):
        if exclude_fields is None:
            exclude_fields = []

        d = {}
        for field in self._meta.db_fields:
            if field not in exclude_fields:
                value = getattr(self, field)
                if isinstance(value, datetime):
                    value = value.strftime(settings.DATETIME_FORMAT)
                elif hasattr(value, "isoformat"):  # Handle date and other date-like objects
                    value = value.isoformat()
                d[field] = value

        if m2m:
            tasks = [
                self.__fetch_m2m_field(field, exclude_fields)
                for field in self._meta.m2m_fields
                if field not in exclude_fields
            ]
            results = await asyncio.gather(*tasks)
            for field, values in results:
                d[field] = values

        return d

    async def __fetch_m2m_field(self, field, exclude_fields):
        values = await getattr(self, field).all().values()
        formatted_values = []

        for value in values:
            formatted_value = {}
            for k, v in value.items():
                if k not in exclude_fields:
                    if isinstance(v, datetime):
                        formatted_value[k] = v.strftime(settings.DATETIME_FORMAT)
                    else:
                        formatted_value[k] = v
            formatted_values.append(formatted_value)

        return field, formatted_values

    class Meta:
        abstract = True


class UUIDModel:
    uuid = fields.UUIDField(unique=True, pk=False, index=True)


class TimestampMixin:
    """
    时间戳混入类
    
    自动处理创建和更新时间戳
    - created_at: 创建时间，手动设置为naive datetime
    - updated_at: 更新时间，手动更新为naive datetime
    
    注意：不使用auto_now_add=True和auto_now=True，手动设置naive datetime
    以匹配数据库的timestamp without time zone类型
    """
    created_at = fields.DatetimeField(description="创建时间")
    updated_at = fields.DatetimeField(description="更新时间")
    
    async def save(self, *args, **kwargs):
        """重写save方法，手动设置时间字段为naive datetime"""
        from datetime import datetime
        
        now = datetime.now()
        # 确保now是naive datetime
        if now.tzinfo is not None:
            now = now.replace(tzinfo=None)
        
        # 如果created_at为空，设置为当前时间（无论是否为新记录）
        if not self.created_at:
            self.created_at = now
        
        # 总是更新updated_at
        self.updated_at = now
        
        # 确保created_at是naive datetime
        if self.created_at and self.created_at.tzinfo is not None:
            self.created_at = self.created_at.replace(tzinfo=None)
        
        # 如果是User模型，还需要处理login_date字段
        if hasattr(self, 'login_date') and self.login_date and self.login_date.tzinfo is not None:
            self.login_date = self.login_date.replace(tzinfo=None)
            
        return await super().save(*args, **kwargs)
