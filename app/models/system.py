from tortoise import fields
from app.models.base import BaseModel, TimestampMixin


class SysDictType(TimestampMixin, BaseModel):
    """
    系统字典类型表
    """

    type_code = fields.CharField(max_length=64, unique=True, description="字典类型编码")
    type_name = fields.CharField(max_length=128, description="字典类型名称")
    description = fields.TextField(null=True, description="描述")

    class Meta:
        table = "t_sys_dict_type"
        table_description = "系统字典类型表"


class SysDictData(TimestampMixin, BaseModel):
    """
    系统字典数据表
    """

    dict_type: fields.ForeignKeyRelation[SysDictType] = fields.ForeignKeyField(
        "models.SysDictType", related_name="dict_data", on_delete=fields.CASCADE, description="字典类型ID", db_column="dict_type_id"
    )
    data_label = fields.CharField(max_length=128, description="字典数据标签")
    data_value = fields.CharField(max_length=128, description="字典数据值")
    sort_order = fields.IntField(default=0, description="排序")
    description = fields.TextField(null=True, description="描述")
    is_enabled = fields.BooleanField(default=True, description="是否启用")

    class Meta:
        table = "t_sys_dict_data"
        table_description = "系统字典数据表"
        unique_together = (("dict_type", "data_value"),)


class TSysConfig(TimestampMixin, BaseModel):
    """
    系统配置表 (新版本)
    """

    param_key = fields.CharField(max_length=128, unique=True, description="参数键")
    param_value = fields.TextField(null=True, description="参数值")
    param_name = fields.CharField(max_length=128, description="参数名称")
    param_type = fields.CharField(max_length=64, description="参数类型 (string, int, boolean等)")
    description = fields.TextField(null=True, description="描述")
    is_editable = fields.BooleanField(default=True, description="是否允许前端编辑")
    is_system = fields.BooleanField(default=False, description="是否系统内置")
    is_active = fields.BooleanField(default=True, description="是否启用")

    class Meta:
        table = "t_sys_config"
        table_description = "系统配置表 (新版本)"


# 为了向后兼容，创建别名
SysConfig = TSysConfig
