from tortoise.models import Model
from tortoise import fields
from .base import BaseModel, TimestampMixin


class DeviceInfo(TimestampMixin, BaseModel):
    """设备信息模型"""
    
    device_code = fields.CharField(max_length=50, unique=True, description="设备编号，唯一标识", index=True)
    device_name = fields.CharField(max_length=100, description="设备名称", index=True)
    device_model = fields.CharField(max_length=50, null=True, description="设备型号")
    device_type = fields.CharField(max_length=50, null=True, description="设备类型", index=True)
    manufacturer = fields.CharField(max_length=100, null=True, description="制造商", index=True)
    production_date = fields.DateField(null=True, description="出厂日期")
    install_date = fields.DateField(null=True, description="安装日期")
    install_location = fields.CharField(max_length=255, null=True, description="安装位置", index=True)
    online_address = fields.CharField(max_length=255, null=True, description="设备在线地址")
    team_name = fields.CharField(max_length=100, null=True, description="所属班组")
    is_locked = fields.BooleanField(default=False, description="是否锁定状态")
    description = fields.TextField(null=True, description="备注信息")
    attributes = fields.JSONField(null=True, description="扩展属性")
    
    class Meta:
        table = "t_device_info"
        table_description = "设备基础信息表"
        app = "models"


class DeviceRealTimeData(TimestampMixin, BaseModel):
    """设备实时数据模型"""
    
    device = fields.ForeignKeyField("models.DeviceInfo", related_name="realtime_data", description="关联设备")
    metrics = fields.JSONField(null=True, description="实时指标快照")
    status = fields.CharField(max_length=20, default="offline", description="设备状态: online/offline/error/maintenance")
    error_code = fields.CharField(max_length=50, null=True, description="错误代码")
    error_message = fields.TextField(null=True, description="错误信息")
    data_timestamp = fields.DatetimeField(description="数据时间戳")
    
    class Meta:
        table = "t_device_realtime_data"
        table_description = "设备实时数据表"
        indexes = [("device_id", "data_timestamp"), ("status",)]
        app = "models"


class DeviceHistoryData(TimestampMixin, BaseModel):
    """设备历史数据模型"""
    
    device = fields.ForeignKeyField("models.DeviceInfo", related_name="history_data", description="关联设备")
    voltage = fields.FloatField(null=True, description="电压值(V)")
    current = fields.FloatField(null=True, description="电流值(A)")
    power = fields.FloatField(null=True, description="功率值(W)")
    temperature = fields.FloatField(null=True, description="温度值(°C)")
    pressure = fields.FloatField(null=True, description="压力值(Pa)")
    vibration = fields.FloatField(null=True, description="振动值")
    status = fields.CharField(max_length=20, description="设备状态")
    error_code = fields.CharField(max_length=50, null=True, description="错误代码")
    error_message = fields.TextField(null=True, description="错误信息")
    data_timestamp = fields.DatetimeField(description="数据时间戳")
    
    class Meta:
        table = "t_device_history_data"
        table_description = "设备历史数据表"
        indexes = [("device_id", "data_timestamp"), ("status",)]
        app = "models"


class DeviceType(TimestampMixin, BaseModel):
    """设备类型模型"""
    type_name = fields.CharField(max_length=100, description="设备类型名称", index=True)
    type_code = fields.CharField(max_length=50, unique=True, description="设备类型代码", index=True)
    tdengine_stable_name = fields.CharField(max_length=100, description="TDengine超级表名")
    description = fields.TextField(null=True, description="设备类型描述")
    icon = fields.CharField(max_length=100, null=True, description="设备类型图标（Iconify图标名称）")
    is_active = fields.BooleanField(default=True, description="是否激活", index=True)
    device_count = fields.IntField(default=0, description="该类型下的设备数量")
    
    class Meta:
        table = "t_device_type"
        table_description = "设备类型表"
        indexes = [("is_active", "type_name"), ("is_active", "type_code")]
        app = "models"


class DeviceField(TimestampMixin, BaseModel):
    """设备字段模型（扩展支持元数据驱动）"""
    field_name = fields.CharField(max_length=100, description="字段名称")
    field_code = fields.CharField(max_length=50, description="字段代码")
    device_type_code = fields.CharField(max_length=50, description="设备类型代码")
    field_type = fields.CharField(max_length=20, description="字段类型: string/integer/float/boolean/json")
    field_category = fields.CharField(max_length=50, default="data_collection", description="字段分类")
    unit = fields.CharField(max_length=20, null=True, description="单位")
    description = fields.TextField(null=True, description="字段描述")
    is_required = fields.BooleanField(default=False, description="是否必填")
    default_value = fields.CharField(max_length=255, null=True, description="默认值")
    validation_rule = fields.TextField(null=True, description="验证规则")
    sort_order = fields.IntField(default=0, description="排序顺序")
    is_active = fields.BooleanField(default=True, description="是否激活")
    
    # ⭐ 新增字段：元数据驱动支持
    is_monitoring_key = fields.BooleanField(default=False, description="是否为实时监控关键字段")
    is_alarm_enabled = fields.BooleanField(default=False, description="是否允许配置报警规则")
    is_ai_feature = fields.BooleanField(default=False, description="是否为AI分析特征字段")
    aggregation_method = fields.CharField(max_length=20, null=True, description="聚合方法: avg/sum/max/min/count/first/last")
    data_range = fields.JSONField(null=True, description='正常数据范围: {"min": 0, "max": 100}')
    alarm_threshold = fields.JSONField(null=True, description='报警阈值配置: {"warning": 80, "critical": 90}')
    display_config = fields.JSONField(null=True, description='前端显示配置: {"chart_type": "line", "color": "#1890ff"}')
    
    # ⭐ 字段分组功能
    field_group = fields.CharField(max_length=50, default="default", description="字段分组: core/temperature/power/speed/dimension/pressure/other/default")
    is_default_visible = fields.BooleanField(default=True, description="是否默认显示（卡片上直接可见）")
    group_order = fields.IntField(default=0, description="分组内排序顺序")
    
    class Meta:
        table = "t_device_field"
        table_description = "设备字段定义表"
        indexes = [
            ("device_type_code",), 
            ("device_type_code", "sort_order"), 
            ("device_type_code", "field_category"),
            ("is_monitoring_key",),  # 新增索引
            ("is_ai_feature",)        # 新增索引
        ]
        unique_together = [("device_type_code", "field_name")]
        app = "models"


class DeviceAlarmHistory(TimestampMixin, BaseModel):
    """设备报警历史表 (通用)"""
    
    device = fields.ForeignKeyField("models.DeviceInfo", related_name="alarm_history", description="关联设备")
    alarm_code = fields.CharField(max_length=50, description="报警代码", index=True)
    severity = fields.CharField(max_length=20, default="Error", description="报警等级: Info/Warning/Error/Fatal")
    category = fields.CharField(max_length=50, default="Device", description="报警分类: System/Hardware/Process")
    content = fields.TextField(description="报警内容")
    start_time = fields.DatetimeField(description="开始时间", index=True)
    end_time = fields.DatetimeField(null=True, description="结束时间")
    context = fields.JSONField(null=True, description="报警上下文数据")
    
    class Meta:
        table = "t_device_alarm_history"
        table_description = "设备报警历史表"
        indexes = [("device_id", "start_time"), ("severity",), ("alarm_code",)]
        app = "models"


class WeldingAlarmHistory(TimestampMixin, BaseModel):
    """焊接报警历史模型 (已弃用，请使用 DeviceAlarmHistory)"""
    prod_code = fields.CharField(max_length=64, description="设备制造编码", index=True)
    alarm_time = fields.DatetimeField(description="报警时刻（开始时间）", index=True)
    alarm_end_time = fields.DatetimeField(null=True, description="报警结束时刻")
    alarm_duration_sec = fields.IntField(null=True, description="报警持续秒数（可解析得出）")
    alarm_code = fields.CharField(max_length=16, null=True, description="报警代码")
    alarm_message = fields.TextField(null=True, description="报警内容")
    alarm_solution = fields.TextField(null=True, description="解决方法（目前为空，但字段预留）")
    
    class Meta:
        table = "t_welding_alarm_his"
        table_description = "焊接报警历史表"
        indexes = [("prod_code",), ("alarm_time",), ("prod_code", "alarm_time")]
        app = "models"

class DeviceMaintenanceRecord(TimestampMixin, BaseModel):
    """设备维护记录模型"""
    
    device = fields.ForeignKeyField("models.DeviceInfo", related_name="maintenance_records", description="关联设备")
    maintenance_type = fields.CharField(max_length=50, description="维护类型: preventive/corrective/emergency/inspection")
    maintenance_title = fields.CharField(max_length=200, description="维护标题")
    maintenance_description = fields.TextField(null=True, description="维护描述")
    maintenance_status = fields.CharField(max_length=20, default="planned", description="维护状态: planned/in_progress/completed/cancelled")
    priority = fields.CharField(max_length=20, default="medium", description="优先级: low/medium/high/urgent")
    
    # 时间相关字段
    planned_start_time = fields.DatetimeField(description="计划开始时间")
    planned_end_time = fields.DatetimeField(description="计划结束时间")
    actual_start_time = fields.DatetimeField(null=True, description="实际开始时间")
    actual_end_time = fields.DatetimeField(null=True, description="实际结束时间")
    
    # 人员相关字段
    assigned_to = fields.CharField(max_length=100, null=True, description="负责人")
    maintenance_team = fields.CharField(max_length=100, null=True, description="维护团队")
    
    # 成本相关字段
    estimated_cost = fields.DecimalField(max_digits=10, decimal_places=2, null=True, description="预估成本")
    actual_cost = fields.DecimalField(max_digits=10, decimal_places=2, null=True, description="实际成本")
    
    # 结果相关字段
    maintenance_result = fields.TextField(null=True, description="维护结果")
    parts_replaced = fields.TextField(null=True, description="更换的零件")
    next_maintenance_date = fields.DatetimeField(null=True, description="下次维护日期")
    
    # 附件和备注
    attachments = fields.TextField(null=True, description="附件路径，JSON格式")
    notes = fields.TextField(null=True, description="备注信息")
    
    class Meta:
        table = "t_device_maintenance_record"
        table_description = "设备维护记录表"
        indexes = [("device_id", "planned_start_time"), ("maintenance_status",), ("maintenance_type",)]
        app = "models"


class DeviceMaintenancePlan(TimestampMixin, BaseModel):
    """设备维护计划模型"""
    
    device = fields.ForeignKeyField("models.DeviceInfo", related_name="maintenance_plans", description="关联设备")
    plan_name = fields.CharField(max_length=200, description="计划名称")
    plan_description = fields.TextField(null=True, description="计划描述")
    maintenance_type = fields.CharField(max_length=50, description="维护类型: preventive/inspection")
    
    # 频率相关字段
    frequency_type = fields.CharField(max_length=20, description="频率类型: daily/weekly/monthly/quarterly/yearly/custom")
    frequency_value = fields.IntField(description="频率值")
    frequency_unit = fields.CharField(max_length=20, null=True, description="频率单位: days/weeks/months/years")
    
    # 时间相关字段
    start_date = fields.DateField(description="开始日期")
    end_date = fields.DateField(null=True, description="结束日期")
    last_execution_date = fields.DateField(null=True, description="上次执行日期")
    next_execution_date = fields.DateField(description="下次执行日期")
    
    # 执行相关字段
    estimated_duration = fields.IntField(null=True, description="预估持续时间（分钟）")
    assigned_team = fields.CharField(max_length=100, null=True, description="指定团队")
    
    # 状态字段
    is_active = fields.BooleanField(default=True, description="是否激活")
    
    # 配置相关字段
    maintenance_checklist = fields.TextField(null=True, description="维护检查清单，JSON格式")
    required_tools = fields.TextField(null=True, description="所需工具，JSON格式")
    required_parts = fields.TextField(null=True, description="所需零件，JSON格式")
    
    class Meta:
        table = "t_device_maintenance_plan"
        table_description = "设备维护计划表"
        indexes = [("device_id", "next_execution_date"), ("is_active",), ("maintenance_type",)]
        app = "models"


class DeviceMaintenanceReminder(TimestampMixin, BaseModel):
    """设备维护提醒模型"""
    
    device = fields.ForeignKeyField("models.DeviceInfo", related_name="maintenance_reminders", description="关联设备")
    maintenance_plan = fields.ForeignKeyField("models.DeviceMaintenancePlan", related_name="reminders", null=True, description="关联维护计划")
    
    reminder_type = fields.CharField(max_length=20, description="提醒类型: plan/overdue/urgent")
    reminder_title = fields.CharField(max_length=200, description="提醒标题")
    reminder_message = fields.TextField(description="提醒消息")
    
    # 时间相关字段
    reminder_time = fields.DatetimeField(description="提醒时间")
    due_date = fields.DatetimeField(description="到期时间")
    
    # 状态字段
    is_sent = fields.BooleanField(default=False, description="是否已发送")
    is_read = fields.BooleanField(default=False, description="是否已读")
    is_dismissed = fields.BooleanField(default=False, description="是否已忽略")
    
    # 接收人相关字段
    recipient_users = fields.TextField(null=True, description="接收用户，JSON格式")
    recipient_teams = fields.TextField(null=True, description="接收团队，JSON格式")
    
    class Meta:
        table = "t_device_maintenance_reminder"
        table_description = "设备维护提醒表"
        indexes = [("device_id", "reminder_time"), ("is_sent",), ("reminder_type",)]
        app = "models"


class DeviceProcess(TimestampMixin, BaseModel):
    """设备工艺模型"""
    
    device = fields.ForeignKeyField("models.DeviceInfo", related_name="processes", description="关联设备")
    process_name = fields.CharField(max_length=200, description="工艺名称")
    process_code = fields.CharField(max_length=50, unique=True, description="工艺编码", index=True)
    process_version = fields.CharField(max_length=20, default="1.0", description="工艺版本")
    process_description = fields.TextField(null=True, description="工艺描述")
    
    # 工艺状态
    process_status = fields.CharField(max_length=20, default="draft", description="工艺状态: draft/active/inactive/archived")
    
    # 工艺类型和分类
    process_type = fields.CharField(max_length=50, description="工艺类型: welding/cutting/assembly/inspection")
    process_category = fields.CharField(max_length=50, null=True, description="工艺分类")
    
    # 工艺参数（JSON格式存储）
    process_parameters = fields.TextField(null=True, description="工艺参数，JSON格式")
    quality_standards = fields.TextField(null=True, description="质量标准，JSON格式")
    safety_requirements = fields.TextField(null=True, description="安全要求，JSON格式")
    
    # 工艺执行相关
    estimated_duration = fields.IntField(null=True, description="预估执行时间（分钟）")
    difficulty_level = fields.CharField(max_length=20, default="medium", description="难度等级: easy/medium/hard/expert")
    required_skills = fields.TextField(null=True, description="所需技能，JSON格式")
    
    # 人员和团队
    created_by = fields.CharField(max_length=100, null=True, description="创建人")
    approved_by = fields.CharField(max_length=100, null=True, description="审批人")
    assigned_team = fields.CharField(max_length=100, null=True, description="指定团队")
    
    # 版本控制
    parent_process_id = fields.IntField(null=True, description="父工艺ID（用于版本控制）")
    is_template = fields.BooleanField(default=False, description="是否为模板")
    is_active = fields.BooleanField(default=True, description="是否激活")
    
    # 审批相关
    approval_status = fields.CharField(max_length=20, default="pending", description="审批状态: pending/approved/rejected")
    approval_date = fields.DatetimeField(null=True, description="审批日期")
    approval_notes = fields.TextField(null=True, description="审批备注")
    
    class Meta:
        table = "t_device_process"
        table_description = "设备工艺表"
        indexes = [("device_id", "process_status"), ("process_code",), ("process_type",), ("is_active",)]


class DeviceProcessExecution(TimestampMixin, BaseModel):
    """设备工艺执行记录模型"""
    
    device = fields.ForeignKeyField("models.DeviceInfo", related_name="process_executions", description="关联设备")
    process = fields.ForeignKeyField("models.DeviceProcess", related_name="executions", description="关联工艺")
    
    # 执行基本信息
    execution_code = fields.CharField(max_length=50, unique=True, description="执行编号", index=True)
    execution_name = fields.CharField(max_length=200, description="执行名称")
    execution_description = fields.TextField(null=True, description="执行描述")
    
    # 执行状态
    execution_status = fields.CharField(max_length=20, default="planned", description="执行状态: planned/in_progress/paused/completed/failed/cancelled")
    
    # 时间相关
    planned_start_time = fields.DatetimeField(null=True, description="计划开始时间")
    planned_end_time = fields.DatetimeField(null=True, description="计划结束时间")
    actual_start_time = fields.DatetimeField(null=True, description="实际开始时间")
    actual_end_time = fields.DatetimeField(null=True, description="实际结束时间")
    
    # 人员相关
    operator = fields.CharField(max_length=100, null=True, description="操作员")
    supervisor = fields.CharField(max_length=100, null=True, description="监督员")
    execution_team = fields.CharField(max_length=100, null=True, description="执行团队")
    
    # 执行结果
    execution_result = fields.TextField(null=True, description="执行结果")
    quality_result = fields.CharField(max_length=20, null=True, description="质量结果: pass/fail/pending")
    quality_score = fields.FloatField(null=True, description="质量评分")
    quality_notes = fields.TextField(null=True, description="质量备注")
    
    # 异常和问题
    issues_encountered = fields.TextField(null=True, description="遇到的问题，JSON格式")
    solutions_applied = fields.TextField(null=True, description="应用的解决方案，JSON格式")
    
    # 资源消耗
    materials_used = fields.TextField(null=True, description="使用的材料，JSON格式")
    tools_used = fields.TextField(null=True, description="使用的工具，JSON格式")
    energy_consumption = fields.FloatField(null=True, description="能耗")
    
    # 成本相关
    estimated_cost = fields.FloatField(null=True, description="预估成本")
    actual_cost = fields.FloatField(null=True, description="实际成本")
    
    # 备注和附件
    notes = fields.TextField(null=True, description="备注信息")
    attachments = fields.TextField(null=True, description="附件信息，JSON格式")
    
    class Meta:
        table = "t_device_process_execution"
        table_description = "设备工艺执行记录表"
        indexes = [("device_id", "execution_status"), ("process_id", "execution_status"), ("execution_code",)]


class DeviceProcessTemplate(TimestampMixin, BaseModel):
    """设备工艺模板模型"""
    
    # 基本信息
    template_name = fields.CharField(max_length=200, description="模板名称")
    template_code = fields.CharField(max_length=50, unique=True, description="模板编码", index=True)
    template_description = fields.TextField(null=True, description="模板描述")
    
    # 分类相关字段
    template_category = fields.CharField(max_length=50, description="模板分类")
    device_type = fields.CharField(max_length=50, null=True, description="适用设备类型")
    process_type = fields.CharField(max_length=50, description="工艺类型")
    
    # 内容相关字段
    template_content = fields.TextField(description="模板内容，JSON格式")
    default_parameters = fields.TextField(null=True, description="默认参数，JSON格式")
    parameter_constraints = fields.TextField(null=True, description="参数约束，JSON格式")
    
    # 状态相关字段
    is_active = fields.BooleanField(default=True, description="是否激活")
    is_public = fields.BooleanField(default=False, description="是否公开")
    
    # 人员相关字段
    created_by = fields.CharField(max_length=100, null=True, description="创建人")
    maintained_by = fields.CharField(max_length=100, null=True, description="维护人")
    
    # 使用统计字段
    usage_count = fields.IntField(default=0, description="使用次数")
    last_used_date = fields.DatetimeField(null=True, description="最后使用日期")
    
    class Meta:
        table = "t_device_process_template"
        table_description = "设备工艺模板表"
        indexes = [("template_code",), ("template_category",), ("device_type",), ("is_active",)]


class DeviceRepairRecord(TimestampMixin, BaseModel):
    """设备维修记录模型"""
    
    # 关联设备
    device = fields.ForeignKeyField("models.DeviceInfo", related_name="repair_records", description="关联设备")
    device_type = fields.CharField(max_length=50, description="设备类型", index=True)
    
    # 基础信息
    repair_date = fields.DateField(description="报修日期", index=True)
    repair_code = fields.CharField(max_length=50, unique=True, null=True, description="维修单号")
    repair_status = fields.CharField(max_length=20, default="pending", description="维修状态：pending/in_progress/completed/cancelled", index=True)
    priority = fields.CharField(max_length=20, default="medium", description="优先级：low/medium/high/urgent")
    
    # 申请人信息
    applicant = fields.CharField(max_length=100, description="申请人", index=True)
    applicant_phone = fields.CharField(max_length=20, null=True, description="申请人电话")
    applicant_dept = fields.CharField(max_length=100, null=True, description="申请部门")
    applicant_workshop = fields.CharField(max_length=100, null=True, description="申请车间")
    construction_unit = fields.CharField(max_length=100, null=True, description="施工单位")
    
    # 故障信息
    is_fault = fields.BooleanField(default=True, description="是否故障")
    fault_reason = fields.CharField(max_length=100, null=True, description="故障原因")
    damage_category = fields.CharField(max_length=50, null=True, description="损坏类别")
    fault_content = fields.TextField(null=True, description="故障内容描述")
    fault_location = fields.CharField(max_length=200, null=True, description="故障部位")
    
    # 维修信息
    repair_content = fields.TextField(null=True, description="维修内容")
    parts_name = fields.CharField(max_length=500, null=True, description="更换配件名称")
    repairer = fields.CharField(max_length=100, null=True, description="维修人员")
    repair_start_time = fields.DatetimeField(null=True, description="维修开始时间")
    repair_completion_date = fields.DateField(null=True, description="维修完成日期")
    repair_cost = fields.DecimalField(max_digits=10, decimal_places=2, null=True, description="维修成本")
    
    # 设备特定数据
    device_specific_data = fields.JSONField(null=True, description="设备特定字段数据")
    
    # 附加信息
    remarks = fields.TextField(null=True, description="备注")
    attachments = fields.JSONField(null=True, description="附件信息")
    
    # 创建和更新人员
    created_by = fields.BigIntField(null=True, description="创建人ID")
    updated_by = fields.BigIntField(null=True, description="更新人ID")
    
    class Meta:
        table = "t_device_repair_record"
        table_description = "设备维修记录表"
        indexes = [
            ("device_id", "repair_date"), 
            ("repair_status",), 
            ("device_type",), 
            ("applicant",),
            ("repair_date",)
        ]
        app = "models"


class DeviceProcessMonitoring(TimestampMixin, BaseModel):
    """设备工艺监控数据模型"""
    
    # 关联字段
    execution = fields.ForeignKeyField("models.DeviceProcessExecution", related_name="monitoring_data", description="关联执行记录")
    device = fields.ForeignKeyField("models.DeviceInfo", related_name="process_monitoring", description="关联设备")
    
    # 时间字段
    monitoring_time = fields.DatetimeField(description="监控时间")
    
    # 工艺参数相关字段
    process_parameters = fields.TextField(null=True, description="工艺参数值，JSON格式")
    parameter_status = fields.CharField(max_length=20, default="normal", description="参数状态: normal/warning/alarm")
    
    # 质量相关字段
    quality_metrics = fields.TextField(null=True, description="质量指标，JSON格式")
    quality_status = fields.CharField(max_length=20, default="normal", description="质量状态: normal/warning/alarm")
    
    # 设备状态相关字段
    device_status = fields.CharField(max_length=20, description="设备状态")
    device_parameters = fields.TextField(null=True, description="设备参数，JSON格式")
    
    # 环境数据
    environmental_data = fields.TextField(null=True, description="环境数据，JSON格式")
    
    # 报警和警告
    alarms = fields.TextField(null=True, description="报警信息，JSON格式")
    warnings = fields.TextField(null=True, description="警告信息，JSON格式")
    
    # 操作员相关字段
    operator_notes = fields.TextField(null=True, description="操作员备注")
    operator_rating = fields.IntField(null=True, description="操作员评分（1-5）")
    
    class Meta:
        table = "t_device_process_monitoring"
        table_description = "设备工艺监控数据表"
        indexes = [("execution_id", "monitoring_time"), ("device_id", "monitoring_time"), ("parameter_status",)]
        app = "models"


# =====================================================
# ⭐ 元数据驱动模型 - 新增
# =====================================================

class DeviceDataModel(TimestampMixin, BaseModel):
    """设备数据模型定义（元数据驱动核心表）"""
    
    # 基础字段
    model_name = fields.CharField(max_length=100, description="模型名称")
    model_code = fields.CharField(max_length=50, description="模型编码（唯一标识）", index=True)
    device_type_code = fields.CharField(max_length=50, description="设备类型代码", index=True)
    model_type = fields.CharField(
        max_length=30, 
        description="模型类型：realtime/statistics/ai_analysis",
        index=True
    )
    
    # 字段选择配置（JSONB格式）
    selected_fields = fields.JSONField(description='选中的字段列表，格式：[{"field_code": "avg_current", "alias": "电流", "weight": 1.0, "is_required": true}]')
    
    # 聚合配置（用于statistics类型）
    aggregation_config = fields.JSONField(
        null=True, 
        description='聚合配置，格式：{"time_window": "1h", "interval": "5m", "methods": ["avg", "max"], "group_by": ["device_code"]}'
    )
    
    # AI配置（用于ai_analysis类型）
    ai_config = fields.JSONField(
        null=True,
        description='AI配置，格式：{"algorithm": "isolation_forest", "features": [...], "normalization": "min-max", "window_size": 100}'
    )
    
    # 版本管理
    version = fields.CharField(max_length=20, default="1.0", description="模型版本")
    is_active = fields.BooleanField(default=True, description="是否激活", index=True)
    is_default = fields.BooleanField(default=False, description="是否为默认模型")
    description = fields.TextField(null=True, description="模型说明")
    
    # 审计字段
    created_by = fields.IntField(null=True, description="创建人ID")
    updated_by = fields.IntField(null=True, description="更新人ID")
    
    class Meta:
        table = "t_device_data_model"
        table_description = "设备数据模型定义表"
        indexes = [
            ("device_type_code",),
            ("model_type",),
            ("model_code",),
            ("device_type_code", "model_type", "is_active"),
            ("created_at",)
        ]
        unique_together = [("model_code", "version")]
        app = "models"


class DeviceFieldMapping(TimestampMixin, BaseModel):
    """设备字段映射（PostgreSQL ↔ TDengine）"""
    
    # 基础字段
    device_type_code = fields.CharField(max_length=50, description="设备类型代码", index=True)
    
    # TDengine信息
    tdengine_database = fields.CharField(max_length=100, description="TDengine数据库名")
    tdengine_stable = fields.CharField(max_length=100, description="TDengine超级表名", index=True)
    tdengine_column = fields.CharField(max_length=100, description="TDengine列名")
    
    # 关联字段定义
    device_field = fields.ForeignKeyField(
        "models.DeviceField",
        related_name="mappings",
        description="关联的字段定义",
        on_delete=fields.CASCADE
    )
    
    # 数据转换规则（JSONB格式）
    transform_rule = fields.JSONField(
        null=True,
        description='数据转换规则，格式：{"type": "expression", "expression": "value * 0.001", "conditions": [...]}'
    )
    
    # 标记字段
    is_tag = fields.BooleanField(default=False, description="是否为TDengine TAG列", index=True)
    is_active = fields.BooleanField(default=True, description="是否激活", index=True)
    
    class Meta:
        table = "t_device_field_mapping"
        table_description = "设备字段映射表（PostgreSQL ↔ TDengine）"
        indexes = [
            ("device_type_code",),
            ("device_field_id",),
            ("tdengine_stable",),
            ("tdengine_database", "tdengine_stable"),
            ("is_tag",),
            ("device_type_code", "is_active")
        ]
        unique_together = [("tdengine_stable", "tdengine_column")]
        app = "models"


class ModelExecutionLog(BaseModel):
    """模型执行日志"""
    
    # 基础字段
    model = fields.ForeignKeyField(
        "models.DeviceDataModel",
        related_name="execution_logs",
        description="关联的数据模型",
        on_delete=fields.CASCADE
    )
    execution_type = fields.CharField(
        max_length=30,
        description="执行类型：query/feature_extract/training/validation",
        index=True
    )
    
    # 执行参数（JSONB格式）
    input_params = fields.JSONField(
        null=True,
        description='输入参数，格式：{"device_code": "...", "start_time": "...", "filters": {...}}'
    )
    
    # 执行结果
    status = fields.CharField(
        max_length=20,
        description="执行状态：success/failed/timeout/cancelled",
        index=True
    )
    result_summary = fields.JSONField(
        null=True,
        description='结果摘要，格式：{"total_rows": 1523, "returned_rows": 100, "data_quality_score": 0.95}'
    )
    error_message = fields.TextField(null=True, description="错误信息")
    
    # 性能指标
    execution_time_ms = fields.IntField(null=True, description="执行时间（毫秒）")
    data_volume = fields.IntField(null=True, description="数据量（行数）")
    memory_usage_mb = fields.IntField(null=True, description="内存使用（MB）")
    
    # 生成的SQL（用于审计和调试）
    generated_sql = fields.TextField(null=True, description="生成的SQL语句")
    
    # 审计字段
    executed_by = fields.IntField(null=True, description="执行人ID", index=True)
    executed_at = fields.DatetimeField(auto_now_add=True, description="执行时间", index=True)
    
    class Meta:
        table = "t_model_execution_log"
        table_description = "模型执行日志表"
        indexes = [
            ("model_id",),
            ("executed_at",),
            ("status",),
            ("execution_type",),
            ("executed_by",),
            ("model_id", "executed_at"),
            ("execution_type", "status", "executed_at")
        ]
        app = "models"


class DeviceDataModelHistory(BaseModel):
    """设备数据模型变更历史"""
    
    # 关联模型
    model = fields.ForeignKeyField(
        "models.DeviceDataModel",
        related_name="history",
        description="关联的数据模型",
        on_delete=fields.CASCADE
    )
    
    # 历史版本信息
    version = fields.CharField(max_length=20, description="版本号")
    
    # 快照内容 (完整保存修改前的状态)
    content = fields.JSONField(description="模型配置快照")
    
    # 变更说明
    change_type = fields.CharField(max_length=20, description="变更类型: create/update/delete")
    change_reason = fields.CharField(max_length=200, null=True, description="变更原因")
    
    # 审计字段
    created_by = fields.IntField(null=True, description="创建人ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    
    class Meta:
        table = "t_device_model_history"
        table_description = "设备数据模型变更历史表"
        indexes = [("model_id", "version"), ("created_at",)]
        app = "models"
