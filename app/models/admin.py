from tortoise import fields

from app.schemas.menus import MenuType

from .base import BaseModel, TimestampMixin
from .enums import MethodType


class User(TimestampMixin, BaseModel):
    username = fields.CharField(max_length=20, unique=True, description="用户名称", index=True)
    nick_name = fields.CharField(max_length=30, null=True, description="昵称", index=True)
    user_type = fields.CharField(max_length=20, null=True, description="用户类型", index=True)
    email = fields.CharField(max_length=255, unique=True, description="邮箱", index=True)
    phone_number = fields.CharField(max_length=20, null=True, description="电话", index=True)
    sex = fields.CharField(max_length=10, null=True, description="性别", index=True)
    avatar = fields.CharField(max_length=255, null=True, description="头像", index=True)
    password = fields.CharField(max_length=128, null=True, description="密码")
    status = fields.CharField(max_length=20, default="0", description="状态", index=True)
    del_flag = fields.CharField(max_length=10, default="0", description="删除标志", index=True)
    login_ip = fields.CharField(max_length=50, null=True, description="最后登录IP", index=True)
    login_date = fields.DatetimeField(null=True, description="最后登录时间", index=True)
    remark = fields.TextField(null=True, description="备注")
    roles = fields.ManyToManyField("models.Role", related_name="users", through="t_sys_user_role", forward_key="role_id", backward_key="user_id")
    dept = fields.ForeignKeyField("models.Dept", related_name="users", null=True, description="所属部门")
    
    # 为了兼容性，添加属性映射
    @property
    def alias(self):
        return self.nick_name
    
    @alias.setter
    def alias(self, value):
        self.nick_name = value
    
    @property
    def phone(self):
        return self.phone_number
    
    @phone.setter
    def phone(self, value):
        self.phone_number = value
    
    @property
    def is_active(self):
        return self.status == "0"
    
    @is_active.setter
    def is_active(self, value):
        self.status = "0" if value else "1"
    
    @property
    def is_superuser(self):
        return self.user_type == "01"
    
    @is_superuser.setter
    def is_superuser(self, value):
        self.user_type = "01" if value else "00"
    
    @property
    def last_login(self):
        return self.login_date
    
    @last_login.setter
    def last_login(self, value):
        self.login_date = value

    class Meta:
        table = "t_sys_user"


class UserRole(BaseModel):
    """用户角色关联表模型 - 对应t_sys_user_role表"""
    user = fields.ForeignKeyField("models.User", related_name="user_roles", description="用户", source_field="user_id")
    role = fields.ForeignKeyField("models.Role", related_name="role_users", description="角色", source_field="role_id")
    
    class Meta:
        table = "t_sys_user_role"
        unique_together = (("user", "role"),)


class Role(TimestampMixin, BaseModel):
    role_name = fields.CharField(max_length=20, unique=True, description="角色名称", index=True)
    role_key = fields.CharField(max_length=100, null=True, description="角色权限字符串", index=True)
    role_sort = fields.IntField(null=True, description="显示顺序", index=True)
    data_scope = fields.CharField(max_length=20, null=True, description="数据范围", index=True)
    menu_check_strictly = fields.BooleanField(default=True, description="菜单树选择项是否关联显示")
    dept_check_strictly = fields.BooleanField(default=True, description="部门树选择项是否关联显示")
    status = fields.CharField(max_length=20, default="0", description="角色状态", index=True)
    del_flag = fields.CharField(max_length=10, default="0", description="删除标志", index=True)
    remark = fields.TextField(null=True, description="备注")
    parent_id = fields.BigIntField(null=True, description="父角色ID", index=True)
    
    # 为了兼容性，添加description属性映射
    @property
    def description(self):
        return self.remark
    
    @description.setter
    def description(self, value):
        self.remark = value
    menus = fields.ManyToManyField(
        "models.Menu", 
        related_name="role_menus", 
        through="t_sys_role_menu",
        forward_key="role_id",
        backward_key="menu_id"
    )
    # V2 API关联，使用现有的t_sys_role_api表
    # 必须明确指定字段映射，因为实际表字段名与ORM推断的不同
    # 实际表字段：role_id, api_id
    # ORM推断字段：role_id, sysapiendpoint_id
    # 注意：Tortoise ORM的forward_key和backward_key含义特殊
    # forward_key: 指向目标模型(SysApiEndpoint)在关联表中的字段名
    # backward_key: 指向当前模型(Role)在关联表中的字段名
    apis = fields.ManyToManyField(
        "models.SysApiEndpoint", 
        related_name="roles", 
        through="t_sys_role_api",
        forward_key="api_id",
        backward_key="role_id"
    )
    # users字段通过User.roles的反向关系自动创建，无需重复定义
    
    # 为了兼容性，添加属性映射
    @property
    def name(self):
        return self.role_name
    
    @name.setter
    def name(self, value):
        self.role_name = value
    
    @property
    def desc(self):
        return self.remark
    
    @desc.setter
    def desc(self, value):
        self.remark = value

    class Meta:
        table = "t_sys_role"


# 旧的 Api 模型已移除，请使用 SysApiEndpoint 模型


class Menu(TimestampMixin, BaseModel):
    # 基本信息
    name = fields.CharField(max_length=20, description="菜单名称", index=True)
    path = fields.CharField(max_length=200, null=True, description="路由路径", index=True)
    component = fields.CharField(max_length=255, null=True, description="组件路径")
    
    # 菜单属性
    menu_type = fields.CharEnumField(MenuType, null=True, description="菜单类型")
    icon = fields.CharField(max_length=100, null=True, description="菜单图标")
    order_num = fields.IntField(default=0, description="显示顺序", index=True)
    parent_id = fields.BigIntField(null=True, description="父菜单ID", index=True)
    
    # 权限控制
    perms = fields.CharField(max_length=100, null=True, description="权限标识", index=True)
    visible = fields.BooleanField(default=True, description="显示状态", index=True)
    status = fields.BooleanField(default=True, description="菜单状态", index=True)
    
    # 路由配置
    is_frame = fields.BooleanField(default=False, description="是否外链")
    is_cache = fields.BooleanField(default=True, description="是否缓存")
    query = fields.CharField(max_length=255, null=True, description="路由参数")
    
    # 保留字段（兼容性）
    remark = fields.JSONField(null=True, description="保留字段")
    
    # 兼容性属性映射
    @property
    def order(self):
        return self.order_num
    
    @order.setter
    def order(self, value):
        self.order_num = value if value is not None else 0
    
    @property
    def is_hidden(self):
        return not self.visible
    
    @is_hidden.setter
    def is_hidden(self, value):
        self.visible = not value if value is not None else True
    
    @property
    def keepalive(self):
        return self.is_cache
    
    @keepalive.setter
    def keepalive(self, value):
        self.is_cache = value if value is not None else True
    
    @property
    def redirect(self):
        return self.query
    
    @redirect.setter
    def redirect(self, value):
        self.query = value

    async def to_dict(self, m2m: bool = False, exclude_fields: list[str] | None = None):
        """
        将Menu模型转换为字典格式（异步版本）
        
        Args:
            m2m: 是否包含多对多关系
            exclude_fields: 要排除的字段列表
            
        Returns:
            dict: 包含菜单信息的字典
        """
        # 首先调用父类的to_dict方法获取基础字段
        base_dict = await super().to_dict(m2m=m2m, exclude_fields=exclude_fields)
        
        # 添加Menu特有的字段映射，确保前端兼容性
        menu_dict = {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "component": self.component,
            "menu_type": self.menu_type,
            "icon": self.icon,
            "order": self.order_num,  # 映射order_num到order字段
            "order_num": self.order_num,  # 保留原字段名
            "parent_id": self.parent_id,
            "perms": self.perms,
            "visible": self.visible,
            "status": self.status,
            "is_frame": self.is_frame,
            "is_cache": self.is_cache,
            "is_hidden": self.is_hidden,  # 使用属性
            "keepalive": self.keepalive,  # 使用属性
            "redirect": self.redirect,    # 使用属性
            "query": self.query,
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        return menu_dict

    class Meta:
        table = "t_sys_menu"


class Dept(TimestampMixin, BaseModel):
    dept_name = fields.CharField(max_length=50, default="", description="部门名称")
    ancestors = fields.CharField(max_length=500, null=True, description="祖级列表")
    order_num = fields.IntField(default=0, description="显示顺序")
    leader = fields.CharField(max_length=20, null=True, description="负责人")
    phone = fields.CharField(max_length=11, null=True, description="联系电话")
    email = fields.CharField(max_length=50, null=True, description="邮箱")
    status = fields.CharField(max_length=1, default="0", description="部门状态（0正常 1停用）")
    del_flag = fields.CharField(max_length=1, default="0", description="删除标志（0代表存在 2代表删除）")
    parent_id = fields.BigIntField(null=True, description="父部门ID")

    # 为了兼容v2 API，添加属性映射
    @property
    def name(self):
        return self.dept_name
    
    @name.setter
    def name(self, value):
        # dept_name字段不能为None，如果value为None则设置为空字符串
        self.dept_name = value if value is not None else ""
    
    @property
    def desc(self):
        return f"{self.leader or ''} - {self.email or ''}".strip(' - ')
    
    @desc.setter
    def desc(self, value):
        # desc是一个计算属性，由leader和email组合而成
        # 设置时我们将值存储到leader字段中
        if value:
            self.leader = str(value)
        else:
            self.leader = None
    
    # order属性已移除，直接使用order_num字段
    
    # is_deleted属性已移除，直接使用del_flag字段
    
    @property
    def is_active(self):
        return self.status == "0"
    
    @is_active.setter
    def is_active(self, value):
        self.status = "0" if value else "1"
    
    async def to_dict(self, m2m: bool = False, exclude_fields: list[str] | None = None):
        """
        将Dept模型转换为字典格式（异步版本）
        
        Args:
            m2m: 是否包含多对多关系
            exclude_fields: 要排除的字段列表
            
        Returns:
            dict: 包含部门信息的字典
        """
        # 首先调用父类的to_dict方法获取基础字段
        base_dict = await super().to_dict(m2m=m2m, exclude_fields=exclude_fields)
        
        # 添加Dept特有的字段映射
        dept_dict = {
            "id": self.id,
            "name": self.dept_name,
            "dept_name": self.dept_name,
            "desc": self.desc,
            "parent_id": self.parent_id,
            "order_num": self.order_num,
            "leader": self.leader,
            "phone": self.phone,
            "email": self.email,
            "status": self.status,
            "del_flag": self.del_flag,
            "is_active": self.is_active,
            "ancestors": self.ancestors,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        return dept_dict

    class Meta:
        table = "t_sys_dept"


class DeptClosure(BaseModel):
    ancestor = fields.ForeignKeyField("models.Dept", related_name="ancestor_closures", on_delete=fields.CASCADE, description="祖先ID")
    descendant = fields.ForeignKeyField("models.Dept", related_name="descendant_closures", on_delete=fields.CASCADE, description="后代ID")
    level = fields.IntField(default=0, description="深度")

    class Meta:
        table = "t_sys_dept_closure"
        unique_together = (("ancestor", "descendant"),)


class SysApiGroup(TimestampMixin, BaseModel):
    """系统API分组模型 - 对应t_sys_api_groups表"""
    group_code = fields.CharField(max_length=100, unique=True, description="分组编码", index=True)
    group_name = fields.CharField(max_length=200, description="分组名称")
    parent_id = fields.BigIntField(null=True, description="父分组ID", index=True)
    description = fields.TextField(null=True, description="描述")
    sort_order = fields.IntField(null=True, description="排序")
    status = fields.CharField(max_length=20, default="active", description="状态", index=True)
    
    class Meta:
        table = "t_sys_api_groups"


class SysApiEndpoint(BaseModel):
    """系统API端点模型 - 对应t_sys_api_endpoints表"""
    api_code = fields.CharField(max_length=100, unique=True, description="API编码", index=True)
    api_name = fields.CharField(max_length=200, description="API名称")
    api_path = fields.CharField(max_length=500, description="API路径", index=True)
    http_method = fields.CharField(max_length=10, description="HTTP方法", index=True)
    description = fields.TextField(null=True, description="描述")
    version = fields.CharField(max_length=20, default="v2", description="版本", index=True)
    is_public = fields.BooleanField(default=False, description="是否公开", index=True)
    is_deprecated = fields.BooleanField(default=False, description="是否废弃", index=True)
    rate_limit = fields.IntField(null=True, description="速率限制")
    status = fields.CharField(max_length=20, default="active", description="状态", index=True)
    permission_code = fields.CharField(max_length=100, null=True, description="权限编码", index=True)
    created_at = fields.DatetimeField(null=True, description="创建时间")
    updated_at = fields.DatetimeField(null=True, description="更新时间")
    
    # 关联分组 - 使用ForeignKeyField会自动创建group_id字段
    group: fields.ForeignKeyRelation[SysApiGroup] = fields.ForeignKeyField(
        "models.SysApiGroup", related_name="endpoints", null=True, description="所属分组"
    )
    
    class Meta:
        table = "t_sys_api_endpoints"


# 注意：t_sys_role_api表由Role.apis的ManyToManyField自动管理
# 不需要单独的RoleApiThrough模型定义


class HttpAuditLog(TimestampMixin, BaseModel):
    """HTTP请求审计日志模型（用于记录API请求）"""
    user_id = fields.IntField(description="用户ID", index=True)
    username = fields.CharField(max_length=64, default="", description="用户名称", index=True)
    module = fields.CharField(max_length=64, default="", description="功能模块", index=True)
    summary = fields.CharField(max_length=128, default="", description="请求描述", index=True)
    method = fields.CharField(max_length=10, default="", description="请求方法", index=True)
    path = fields.CharField(max_length=255, default="", description="请求路径", index=True)
    status = fields.IntField(default=-1, description="状态码", index=True)
    response_time = fields.IntField(default=0, description="响应时间(单位ms)", index=True)
    request_args = fields.JSONField(null=True, description="请求参数")
    response_body = fields.JSONField(null=True, description="返回数据")

    class Meta:
        table = "t_sys_auditlog"


class MockData(TimestampMixin, BaseModel):
    """Mock数据模型 - 用于模拟API响应"""
    
    # 基本信息
    name = fields.CharField(max_length=100, description="Mock规则名称", index=True)
    description = fields.CharField(max_length=500, null=True, description="规则描述")
    
    # 匹配规则
    method = fields.CharField(max_length=10, description="HTTP方法", index=True)
    url_pattern = fields.CharField(max_length=500, description="URL匹配模式", index=True)
    
    # Mock响应
    response_data = fields.JSONField(description="响应数据")
    response_code = fields.IntField(default=200, description="响应状态码")
    delay = fields.IntField(default=0, description="延迟时间(ms)")
    
    # 控制字段
    enabled = fields.BooleanField(default=True, description="是否启用", index=True)
    priority = fields.IntField(default=0, description="优先级(数字越大越优先)", index=True)
    
    # 统计字段
    hit_count = fields.IntField(default=0, description="命中次数")
    last_hit_time = fields.DatetimeField(null=True, description="最后命中时间")
    
    # 创建者信息
    creator_id = fields.IntField(null=True, description="创建者ID", index=True)
    creator_name = fields.CharField(max_length=64, null=True, description="创建者名称")
    
    class Meta:
        table = "t_sys_mock_data"
        indexes = [("enabled", "priority")]
