from datetime import date, datetime
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


# =====================================================
# 维修记录状态枚举
# =====================================================

class RepairStatus(str, Enum):
    """维修状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RepairPriority(str, Enum):
    """维修优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# =====================================================
# 基础设备管理模型
# =====================================================


class BaseDevice(BaseModel):
    """设备基础模型"""
    pass


# =====================================================
# 设备类型管理模型
# =====================================================


class DeviceType(BaseModel):
    """设备类型模型"""

    id: Optional[int] = None
    type_name: str = Field(..., description="设备类型名称", example="焊接设备")
    type_code: str = Field(..., description="设备类型代码", example="welding")

    description: Optional[str] = Field(None, description="类型描述")
    is_active: bool = Field(True, description="是否激活")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DeviceTypeCreate(BaseModel):
    """创建设备类型模型"""

    type_name: str = Field(..., description="设备类型名称")
    type_code: str = Field(..., description="设备类型代码")

    description: Optional[str] = Field(None, description="类型描述")
    is_active: bool = Field(True, description="是否激活")


class DeviceTypeUpdate(BaseModel):
    """更新设备类型模型"""

    type_name: Optional[str] = Field(None, description="设备类型名称")
    type_code: Optional[str] = Field(None, description="设备类型代码")

    description: Optional[str] = Field(None, description="类型描述")
    is_active: Optional[bool] = Field(None, description="是否激活")


class DeviceTypeResponse(BaseModel):
    """设备类型响应模型"""

    id: int = Field(..., description="设备类型ID")
    type_name: str = Field(..., description="设备类型名称")
    type_code: str = Field(..., description="设备类型代码")

    description: Optional[str] = Field(None, description="类型描述")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# =====================================================
# 设备响应模型
# =====================================================


class DeviceResponse(BaseModel):
    """设备响应模型"""
    
    id: int
    device_code: str
    device_name: str
    device_model: Optional[str] = None
    device_type: Optional[str] = None
    manufacturer: Optional[str] = None
    production_date: Optional[date] = None
    install_date: Optional[date] = None
    install_location: Optional[str] = None
    online_address: Optional[str] = None
    team_name: Optional[str] = None
    is_locked: bool = False
    description: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DeviceCreate(BaseModel):
    """创建设备模型"""

    device_code: str = Field(..., description="设备编号，唯一标识", example="DEV001")
    device_name: str = Field(..., description="设备名称", example="焊接设备01")
    device_model: Optional[str] = Field(None, description="设备型号", example="WLD-2000")
    device_type: Optional[str] = Field(None, description="设备类型", example="welding")
    manufacturer: Optional[str] = Field(None, description="制造商", example="华为技术")
    production_date: Optional[date] = Field(None, description="出厂日期")
    install_date: Optional[date] = Field(None, description="安装日期")
    install_location: Optional[str] = Field(None, description="安装位置", example="车间A-01")
    online_address: Optional[str] = Field(None, description="设备在线地址", example="192.168.1.100")
    team_name: Optional[str] = Field(None, description="所属班组", example="生产一班")
    is_locked: bool = Field(False, description="是否锁定状态")
    description: Optional[str] = Field(None, description="备注信息")
    attributes: Optional[Dict[str, Any]] = Field(None, description="扩展属性")

    def create_dict(self):
        return self.model_dump(exclude_unset=True)


class DeviceUpdate(BaseModel):
    """更新设备模型"""

    device_code: Optional[str] = Field(None, description="设备编号，唯一标识")
    device_name: Optional[str] = Field(None, description="设备名称")
    device_model: Optional[str] = Field(None, description="设备型号")
    device_type: Optional[str] = Field(None, description="设备类型")
    manufacturer: Optional[str] = Field(None, description="制造商")
    production_date: Optional[date] = Field(None, description="出厂日期")
    install_date: Optional[date] = Field(None, description="安装日期")
    install_location: Optional[str] = Field(None, description="安装位置")
    online_address: Optional[str] = Field(None, description="设备在线地址")
    team_name: Optional[str] = Field(None, description="所属班组")
    is_locked: Optional[bool] = Field(None, description="是否锁定状态")
    description: Optional[str] = Field(None, description="备注信息")
    attributes: Optional[Dict[str, Any]] = Field(None, description="扩展属性")

    def update_dict(self):
        return self.model_dump(exclude_unset=True, exclude={"id"})


class DeviceQuery(BaseModel):
    """设备查询模型"""

    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(10, description="每页数量", ge=1, le=100)
    device_code: Optional[str] = Field(None, description="设备编号搜索")
    device_name: Optional[str] = Field(None, description="设备名称搜索")
    device_type: Optional[str] = Field(None, description="设备类型搜索")
    manufacturer: Optional[str] = Field(None, description="制造商搜索")
    team_name: Optional[str] = Field(None, description="所属班组搜索")
    is_locked: Optional[bool] = Field(None, description="锁定状态搜索")
    install_location: Optional[str] = Field(None, description="安装位置搜索")


class DeviceBatchImport(BaseModel):
    """批量导入设备模型"""

    devices: List[DeviceCreate] = Field(..., description="设备列表")


class BatchImportResult(BaseModel):
    """批量导入结果模型"""

    success_count: int = Field(..., description="成功导入数量")
    failed_count: int = Field(..., description="失败数量")
    failed_items: List[dict] = Field(..., description="失败项目详情")





# =====================================================
# 历史数据和统计模型
# =====================================================


class DeviceHistoryDataQuery(BaseModel):
    """设备历史数据查询模型"""

    device_id: Optional[int] = Field(None, description="设备ID")
    device_code: Optional[str] = Field(None, description="设备编号")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    status: Optional[str] = Field(None, description="设备状态")
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(10, description="每页数量", ge=1, le=100)


class DeviceStatusSummary(BaseModel):
    """设备状态汇总模型"""

    device_id: int
    device_code: str
    device_name: str
    device_type: Optional[str] = None
    install_location: Optional[str] = None
    current_status: str
    last_update: Optional[datetime] = None
    voltage: Optional[float] = None
    current: Optional[float] = None
    power: Optional[float] = None
    temperature: Optional[float] = None


class DeviceStatistics(BaseModel):
    """设备统计模型"""

    total_devices: int = Field(..., description="设备总数")
    locked_devices: int = Field(..., description="锁定设备数")
    unlocked_devices: int = Field(..., description="未锁定设备数")
    device_types: Dict[str, int] = Field(..., description="设备类型分布")
    manufacturers: Dict[str, int] = Field(..., description="制造商分布")
    teams: Dict[str, int] = Field(..., description="班组分布")


# =====================================================
# 设备类型管理模型
# =====================================================


class DeviceType(BaseModel):
    """设备类型模型"""

    id: Optional[int] = None
    type_name: str = Field(..., description="设备类型名称", example="焊接设备")
    type_code: str = Field(..., description="设备类型代码", example="welding")
    tdengine_stable_name: str = Field(..., description="TDengine超级表名", example="welding_real_data")
    description: Optional[str] = Field(None, description="类型描述")
    icon: Optional[str] = Field(None, description="设备类型图标（Iconify图标名称）", example="material-symbols:precision-manufacturing")
    is_active: bool = Field(True, description="是否激活")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DeviceTypeCreate(BaseModel):
    """创建设备类型模型"""

    type_name: str = Field(..., description="设备类型名称")
    type_code: str = Field(..., description="设备类型代码")
    tdengine_stable_name: str = Field(..., description="TDengine超级表名")
    description: Optional[str] = Field(None, description="类型描述")
    icon: Optional[str] = Field(None, description="设备类型图标（Iconify图标名称）", example="material-symbols:precision-manufacturing")
    is_active: bool = Field(True, description="是否激活")


class DeviceTypeUpdate(BaseModel):
    """更新设备类型模型"""

    type_name: Optional[str] = Field(None, description="设备类型名称")
    type_code: Optional[str] = Field(None, description="设备类型代码")
    tdengine_stable_name: Optional[str] = Field(None, description="TDengine超级表名")
    description: Optional[str] = Field(None, description="类型描述")
    icon: Optional[str] = Field(None, description="设备类型图标（Iconify图标名称）")
    is_active: Optional[bool] = Field(None, description="是否激活")


class DeviceTypeResponse(BaseModel):
    """设备类型响应模型"""

    id: int = Field(..., description="设备类型ID")
    type_name: str = Field(..., description="设备类型名称")
    type_code: str = Field(..., description="设备类型代码")
    tdengine_stable_name: str = Field(..., description="TDengine超级表名")
    description: Optional[str] = Field(None, description="类型描述")
    icon: Optional[str] = Field(None, description="设备类型图标（Iconify图标名称）")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# =====================================================
# 设备实时数据相关模型
# =====================================================


class DeviceRealtimeQuery(BaseModel):
    """设备实时数据查询模型"""
    
    device_id: Optional[int] = Field(None, description="设备ID")
    device_code: Optional[str] = Field(None, description="设备编号")
    device_codes: Optional[List[str]] = Field(None, description="设备编号列表，支持批量查询")
    type_code: Optional[str] = Field(None, description="设备类型代码")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    status: Optional[str] = Field(None, description="设备状态")
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(20, description="每页数量", ge=1, le=2000)
    use_dynamic_fields: bool = Field(False, description="是否使用动态字段支持")
    paged: bool = Field(True, description="是否启用分页")


class DeviceRealtimeResponse(BaseModel):
    """设备实时数据响应模型"""
    
    device_id: int = Field(..., description="设备ID")
    device_code: str = Field(..., description="设备编号")
    voltage: Optional[float] = Field(None, description="电压值(V)")
    current: Optional[float] = Field(None, description="电流值(A)")
    power: Optional[float] = Field(None, description="功率值(W)")
    temperature: Optional[float] = Field(None, description="温度值(°C)")
    pressure: Optional[float] = Field(None, description="压力值(Pa)")
    vibration: Optional[float] = Field(None, description="振动值")
    metrics: Optional[Dict[str, Any]] = Field(None, description="实时指标快照")
    status: str = Field(..., description="设备状态")
    error_code: Optional[str] = Field(None, description="错误代码")
    error_message: Optional[str] = Field(None, description="错误信息")
    data_timestamp: datetime = Field(..., description="数据时间戳")
    
    class Config:
        from_attributes = True


class DeviceRealTimeDataCreate(BaseModel):
    """创建设备实时数据模型"""

    device_id: int = Field(..., description="设备ID")
    voltage: Optional[float] = Field(None, description="电压值(V)")
    current: Optional[float] = Field(None, description="电流值(A)")
    power: Optional[float] = Field(None, description="功率值(W)")
    temperature: Optional[float] = Field(None, description="温度值(°C)")
    pressure: Optional[float] = Field(None, description="压力值(Pa)")
    vibration: Optional[float] = Field(None, description="振动值")
    metrics: Optional[Dict[str, Any]] = Field(None, description="实时指标快照")
    status: str = Field("offline", description="设备状态: online/offline/error/maintenance")
    error_code: Optional[str] = Field(None, description="错误代码")
    error_message: Optional[str] = Field(None, description="错误信息")
    data_timestamp: datetime = Field(..., description="数据时间戳")


class DeviceRealTimeDataResponse(BaseModel):
    """设备实时数据响应模型"""

    id: int = Field(..., description="数据ID")
    device_id: int = Field(..., description="设备ID")
    voltage: Optional[float] = Field(None, description="电压值(V)")
    current: Optional[float] = Field(None, description="电流值(A)")
    power: Optional[float] = Field(None, description="功率值(W)")
    temperature: Optional[float] = Field(None, description="温度值(°C)")
    pressure: Optional[float] = Field(None, description="压力值(Pa)")
    vibration: Optional[float] = Field(None, description="振动值")
    metrics: Optional[Dict[str, Any]] = Field(None, description="实时指标快照")
    status: str = Field(..., description="设备状态")
    error_code: Optional[str] = Field(None, description="错误代码")
    error_message: Optional[str] = Field(None, description="错误信息")
    data_timestamp: datetime = Field(..., description="数据时间戳")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# =====================================================
# 设备字段管理模型
# =====================================================


class DeviceFieldResponse(BaseModel):
    """设备字段响应模型"""

    id: int = Field(..., description="字段ID")
    device_type_code: str = Field(..., description="设备类型代码")
    field_name: str = Field(..., description="字段名称")
    field_type: str = Field(..., description="字段类型")
    field_description: Optional[str] = Field(None, description="字段描述")
    is_required: bool = Field(False, description="是否必填")
    is_tag: bool = Field(False, description="是否为标签字段")
    sort_order: int = Field(0, description="排序顺序")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class DeviceFieldCreate(BaseModel):
    """创建设备字段模型"""

    field_name: str = Field(..., description="字段名称")
    field_type: str = Field(..., description="字段类型")
    field_description: Optional[str] = Field(None, description="字段描述")
    is_required: bool = Field(False, description="是否必填")
    is_tag: bool = Field(False, description="是否为标签字段")
    sort_order: int = Field(0, description="排序顺序")


class DeviceFieldUpdate(BaseModel):
    """更新设备字段模型"""

    field_name: Optional[str] = Field(None, description="字段名称")
    field_type: Optional[str] = Field(None, description="字段类型")
    field_description: Optional[str] = Field(None, description="字段描述")
    is_required: Optional[bool] = Field(None, description="是否必填")
    is_tag: Optional[bool] = Field(None, description="是否为标签字段")
    sort_order: Optional[int] = Field(None, description="排序顺序")


class DeviceTypeDetailResponse(BaseModel):
    """设备类型详情响应模型"""

    id: int = Field(..., description="设备类型ID")
    type_name: str = Field(..., description="设备类型名称")
    type_code: str = Field(..., description="设备类型代码")
    tdengine_stable_name: str = Field(..., description="TDengine超级表名")
    description: Optional[str] = Field(None, description="类型描述")
    is_active: bool = Field(..., description="是否激活")
    device_count: int = Field(0, description="设备数量")
    field_count: int = Field(0, description="字段数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    fields: List[DeviceFieldResponse] = Field(default_factory=list, description="字段列表")

    class Config:
        from_attributes = True


# =====================================================
# 通用设备数据查询模型
# =====================================================


class UniversalRealTimeDataQuery(BaseModel):
    """通用实时数据查询模型"""
    
    type_code: Optional[str] = Field(None, description="设备类型代码")
    device_code: Optional[str] = Field(None, description="设备编号")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(20, description="每页数量", ge=1, le=100)


class UniversalRealTimeDataResponse(BaseModel):
    """通用实时数据响应模型"""
    
    device_code: str = Field(..., description="设备编号")
    device_name: Optional[str] = Field(None, description="设备名称")
    type_code: str = Field(..., description="设备类型代码")
    ts: datetime = Field(..., description="时间戳")
    data: Dict[str, Any] = Field(default_factory=dict, description="数据字段")
    tags: Dict[str, Any] = Field(default_factory=dict, description="标签字段")
    
    class Config:
        from_attributes = True


# =====================================================
# 报警历史数据模型
# =====================================================

class WeldingAlarmHistoryQuery(BaseModel):
    """焊接报警历史查询模型"""
    device_type: Optional[str] = Field(None, description="设备类型")
    device_code: Optional[str] = Field(None, description="设备编号")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(20, description="每页数量", ge=1, le=100)


class WeldingAlarmHistoryResponse(BaseModel):
    """焊接报警历史响应模型"""
    id: int = Field(..., description="报警记录ID")
    prod_code: str = Field(..., description="设备制造编码")
    alarm_time: datetime = Field(..., description="报警时刻（开始时间）")
    alarm_end_time: Optional[datetime] = Field(None, description="报警结束时刻")
    alarm_duration_sec: Optional[int] = Field(None, description="报警持续秒数")
    alarm_code: Optional[str] = Field(None, description="报警代码")
    alarm_message: Optional[str] = Field(None, description="报警内容")
    alarm_solution: Optional[str] = Field(None, description="解决方法")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class DeviceAlarmHistoryResponse(BaseModel):
    """设备报警历史响应模型"""
    id: int = Field(..., description="报警记录ID")
    device_id: int = Field(..., description="设备ID")
    alarm_code: str = Field(..., description="报警代码")
    severity: str = Field(..., description="报警等级")
    category: str = Field(..., description="报警分类")
    content: str = Field(..., description="报警内容")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    context: Optional[Dict[str, Any]] = Field(None, description="报警上下文数据")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


# =====================================================
# 设备维修记录管理模型
# =====================================================

class DeviceRepairRecordCreate(BaseModel):
    """创建设备维修记录模型"""
    
    device_id: int = Field(..., description="设备ID")
    device_type: str = Field(..., description="设备类型")
    repair_date: date = Field(..., description="报修日期")
    priority: str = Field("normal", description="优先级：low/normal/high/urgent")
    
    # 申请人信息
    applicant: str = Field(..., description="申请人")
    applicant_phone: Optional[str] = Field(None, description="申请人电话")
    applicant_dept: Optional[str] = Field(None, description="申请部门")
    applicant_workshop: Optional[str] = Field(None, description="申请车间")
    construction_unit: Optional[str] = Field(None, description="施工单位")
    
    # 故障信息
    is_fault: bool = Field(True, description="是否故障")
    fault_reason: Optional[str] = Field(None, description="故障原因")
    damage_category: Optional[str] = Field(None, description="损坏类别")
    fault_content: Optional[str] = Field(None, description="故障内容描述")
    fault_location: Optional[str] = Field(None, description="故障部位")
    
    # 维修信息
    repair_content: Optional[str] = Field(None, description="维修内容")
    parts_name: Optional[str] = Field(None, description="更换配件名称")
    repairer: Optional[str] = Field(None, description="维修人员")
    repair_start_time: Optional[datetime] = Field(None, description="维修开始时间")
    repair_completion_date: Optional[date] = Field(None, description="维修完成日期")
    repair_cost: Optional[float] = Field(None, description="维修成本")
    
    # 设备特定信息
    device_specific_data: Optional[Dict[str, Any]] = Field(None, description="设备特定字段数据")
    
    # 附加信息
    remarks: Optional[str] = Field(None, description="备注")
    attachments: Optional[Dict[str, Any]] = Field(None, description="附件信息")


class DeviceRepairRecordUpdate(BaseModel):
    """更新设备维修记录模型"""
    
    device_type: Optional[str] = Field(None, description="设备类型")
    repair_date: Optional[date] = Field(None, description="报修日期")
    repair_status: Optional[str] = Field(None, description="维修状态")
    priority: Optional[str] = Field(None, description="优先级")
    
    # 申请人信息
    applicant: Optional[str] = Field(None, description="申请人")
    applicant_phone: Optional[str] = Field(None, description="申请人电话")
    applicant_dept: Optional[str] = Field(None, description="申请部门")
    applicant_workshop: Optional[str] = Field(None, description="申请车间")
    construction_unit: Optional[str] = Field(None, description="施工单位")
    
    # 故障信息
    is_fault: Optional[bool] = Field(None, description="是否故障")
    fault_reason: Optional[str] = Field(None, description="故障原因")
    damage_category: Optional[str] = Field(None, description="损坏类别")
    fault_content: Optional[str] = Field(None, description="故障内容描述")
    fault_location: Optional[str] = Field(None, description="故障部位")
    
    # 维修信息
    repair_content: Optional[str] = Field(None, description="维修内容")
    parts_name: Optional[str] = Field(None, description="更换配件名称")
    repairer: Optional[str] = Field(None, description="维修人员")
    repair_start_time: Optional[datetime] = Field(None, description="维修开始时间")
    repair_completion_date: Optional[date] = Field(None, description="维修完成日期")
    repair_cost: Optional[float] = Field(None, description="维修成本")
    
    # 设备特定信息
    device_specific_data: Optional[Dict[str, Any]] = Field(None, description="设备特定字段数据")
    
    # 附加信息
    remarks: Optional[str] = Field(None, description="备注")
    attachments: Optional[Dict[str, Any]] = Field(None, description="附件信息")


class DeviceRepairRecordResponse(BaseModel):
    """设备维修记录响应模型"""
    
    id: int = Field(..., description="维修记录ID")
    device_id: int = Field(..., description="设备ID")
    device_type: str = Field(..., description="设备类型")
    repair_date: date = Field(..., description="报修日期")
    repair_code: Optional[str] = Field(None, description="维修单号")
    repair_status: str = Field(..., description="维修状态")
    priority: str = Field(..., description="优先级")
    
    # 申请人信息
    applicant: str = Field(..., description="申请人")
    applicant_phone: Optional[str] = Field(None, description="申请人电话")
    applicant_dept: Optional[str] = Field(None, description="申请部门")
    applicant_workshop: Optional[str] = Field(None, description="申请车间")
    construction_unit: Optional[str] = Field(None, description="施工单位")
    
    # 故障信息
    is_fault: bool = Field(..., description="是否故障")
    fault_reason: Optional[str] = Field(None, description="故障原因")
    damage_category: Optional[str] = Field(None, description="损坏类别")
    fault_content: Optional[str] = Field(None, description="故障内容描述")
    fault_location: Optional[str] = Field(None, description="故障部位")
    
    # 维修信息
    repair_content: Optional[str] = Field(None, description="维修内容")
    parts_name: Optional[str] = Field(None, description="更换配件名称")
    repairer: Optional[str] = Field(None, description="维修人员")
    repair_start_time: Optional[datetime] = Field(None, description="维修开始时间")
    repair_completion_date: Optional[date] = Field(None, description="维修完成日期")
    repair_cost: Optional[float] = Field(None, description="维修成本")
    
    # 设备特定信息
    device_specific_data: Optional[Dict[str, Any]] = Field(None, description="设备特定字段数据")
    
    # 附加信息
    remarks: Optional[str] = Field(None, description="备注")
    attachments: Optional[Dict[str, Any]] = Field(None, description="附件信息")
    
    # 审计字段
    created_by: Optional[int] = Field(None, description="创建人ID")
    updated_by: Optional[int] = Field(None, description="更新人ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 关联设备信息
    device: Optional[Dict[str, Any]] = Field(None, description="关联设备信息")
    
    class Config:
        from_attributes = True


class RepairCodeGenerateRequest(BaseModel):
    """维修单号生成请求模型"""
    
    device_type: str = Field(..., description="设备类型")
    repair_date: date = Field(..., description="报修日期")


# =====================================================
# 设备字段配置管理模型
# =====================================================

class DeviceFieldConfigResponse(BaseModel):
    """设备字段配置响应模型"""
    
    field_code: str = Field(..., description="字段代码")
    field_name: str = Field(..., description="字段名称")
    field_type: str = Field(..., description="字段类型")
    field_category: str = Field(..., description="字段分类")
    is_required: bool = Field(False, description="是否必填")
    sort_order: int = Field(0, description="排序顺序")
    default_value: Optional[str] = Field(None, description="默认值")
    validation_rule: Optional[Dict[str, Any]] = Field(None, description="验证规则")
    options: Optional[List[Dict[str, str]]] = Field(None, description="选项值（用于字典类型字段）")
    unit: Optional[str] = Field(None, description="单位")
    description: Optional[str] = Field(None, description="字段描述")
    is_alarm_enabled: bool = Field(False, description="是否允许配置报警规则")
    
    class Config:
        from_attributes = True


class DeviceFieldConfigQuery(BaseModel):
    """设备字段配置查询模型"""
    
    device_type_code: str = Field(..., description="设备类型代码")
    field_category: Optional[str] = Field(None, description="字段分类筛选")
    include_options: bool = Field(True, description="是否包含选项值")


class DeviceFieldConfigCreate(BaseModel):
    """创建设备字段配置模型"""
    
    device_type_code: str = Field(..., description="设备类型代码")
    field_name: str = Field(..., description="字段名称")
    field_code: str = Field(..., description="字段代码")
    field_type: str = Field(..., description="字段类型")
    field_category: str = Field("maintenance_record", description="字段分类")
    field_group: Optional[str] = Field("default", description="字段分组")  # ✅ 添加字段分组
    is_default_visible: Optional[bool] = Field(True, description="是否默认显示")  # ✅ 添加默认显示
    group_order: Optional[int] = Field(0, description="分组内排序")  # ✅ 添加分组排序
    is_required: bool = Field(False, description="是否必填")
    sort_order: int = Field(0, description="排序顺序")
    default_value: Optional[str] = Field(None, description="默认值")
    validation_rule: Optional[Dict[str, Any]] = Field(None, description="验证规则")
    unit: Optional[str] = Field(None, description="单位")
    description: Optional[str] = Field(None, description="字段描述")
    is_monitoring_key: bool = Field(False, description="是否为实时监控关键字段")
    is_alarm_enabled: bool = Field(False, description="是否允许配置报警规则")
    is_ai_feature: bool = Field(False, description="是否为AI分析特征字段")
    aggregation_method: Optional[str] = Field(None, description="聚合方法")
    data_range: Optional[Dict[str, Any]] = Field(None, description="正常数据范围")
    alarm_threshold: Optional[Dict[str, Any]] = Field(None, description="报警阈值配置")
    display_config: Optional[Dict[str, Any]] = Field(None, description="前端显示配置")


class DeviceFieldConfigUpdate(BaseModel):
    """更新设备字段配置模型"""
    
    field_name: Optional[str] = Field(None, description="字段名称")
    field_type: Optional[str] = Field(None, description="字段类型")
    field_category: Optional[str] = Field(None, description="字段分类")
    field_group: Optional[str] = Field(None, description="字段分组")  # ✅ 添加字段分组
    is_default_visible: Optional[bool] = Field(None, description="是否默认显示")  # ✅ 添加默认显示
    group_order: Optional[int] = Field(None, description="分组内排序")  # ✅ 添加分组排序
    is_required: Optional[bool] = Field(None, description="是否必填")
    sort_order: Optional[int] = Field(None, description="排序顺序")
    default_value: Optional[str] = Field(None, description="默认值")
    validation_rule: Optional[Dict[str, Any]] = Field(None, description="验证规则")
    unit: Optional[str] = Field(None, description="单位")
    description: Optional[str] = Field(None, description="字段描述")
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_monitoring_key: Optional[bool] = Field(None, description="是否为实时监控关键字段")
    is_alarm_enabled: Optional[bool] = Field(None, description="是否允许配置报警规则")
    is_ai_feature: Optional[bool] = Field(None, description="是否为AI分析特征字段")
    aggregation_method: Optional[str] = Field(None, description="聚合方法")
    data_range: Optional[Dict[str, Any]] = Field(None, description="正常数据范围")
    alarm_threshold: Optional[Dict[str, Any]] = Field(None, description="报警阈值配置")
    display_config: Optional[Dict[str, Any]] = Field(None, description="前端显示配置")


# =====================================================
# 兼容性别名 - 保持向后兼容
# =====================================================

# 焊接设备兼容性别名
WeldingRealtimeQuery = DeviceRealtimeQuery
WeldingRealTimeDataResponse = DeviceRealtimeResponse

# =====================================================
# 设备维护管理模型
# =====================================================

class DeviceMaintenanceRecordCreate(BaseModel):
    """创建设备维护记录模型"""
    
    device_id: int = Field(..., description="设备ID")
    maintenance_type: str = Field(..., description="维护类型: preventive/corrective/emergency/inspection")
    maintenance_title: str = Field(..., description="维护标题")
    maintenance_description: Optional[str] = Field(None, description="维护描述")
    priority: str = Field("normal", description="优先级: low/normal/high/urgent")
    
    planned_start_time: datetime = Field(..., description="计划开始时间")
    planned_end_time: datetime = Field(..., description="计划结束时间")
    
    assigned_to: Optional[str] = Field(None, description="负责人")
    maintenance_team: Optional[str] = Field(None, description="维护团队")
    estimated_cost: Optional[float] = Field(None, description="预估成本")
    notes: Optional[str] = Field(None, description="备注信息")


class DeviceMaintenanceRecordUpdate(BaseModel):
    """更新设备维护记录模型"""
    
    maintenance_type: Optional[str] = Field(None, description="维护类型")
    maintenance_title: Optional[str] = Field(None, description="维护标题")
    maintenance_description: Optional[str] = Field(None, description="维护描述")
    maintenance_status: Optional[str] = Field(None, description="维护状态: planned/in_progress/completed/cancelled")
    priority: Optional[str] = Field(None, description="优先级")
    
    planned_start_time: Optional[datetime] = Field(None, description="计划开始时间")
    planned_end_time: Optional[datetime] = Field(None, description="计划结束时间")
    actual_start_time: Optional[datetime] = Field(None, description="实际开始时间")
    actual_end_time: Optional[datetime] = Field(None, description="实际结束时间")
    
    assigned_to: Optional[str] = Field(None, description="负责人")
    maintenance_team: Optional[str] = Field(None, description="维护团队")
    estimated_cost: Optional[float] = Field(None, description="预估成本")
    actual_cost: Optional[float] = Field(None, description="实际成本")
    
    maintenance_result: Optional[str] = Field(None, description="维护结果")
    parts_replaced: Optional[str] = Field(None, description="更换的零件")
    next_maintenance_date: Optional[datetime] = Field(None, description="下次维护日期")
    notes: Optional[str] = Field(None, description="备注信息")


class DeviceMaintenanceRecordResponse(BaseModel):
    """设备维护记录响应模型"""
    
    id: int = Field(..., description="维护记录ID")
    device_id: int = Field(..., description="设备ID")
    maintenance_type: str = Field(..., description="维护类型")
    maintenance_title: str = Field(..., description="维护标题")
    maintenance_description: Optional[str] = Field(None, description="维护描述")
    maintenance_status: str = Field(..., description="维护状态")
    priority: str = Field(..., description="优先级")
    
    planned_start_time: datetime = Field(..., description="计划开始时间")
    planned_end_time: datetime = Field(..., description="计划结束时间")
    actual_start_time: Optional[datetime] = Field(None, description="实际开始时间")
    actual_end_time: Optional[datetime] = Field(None, description="实际结束时间")
    
    assigned_to: Optional[str] = Field(None, description="负责人")
    maintenance_team: Optional[str] = Field(None, description="维护团队")
    estimated_cost: Optional[float] = Field(None, description="预估成本")
    actual_cost: Optional[float] = Field(None, description="实际成本")
    
    maintenance_result: Optional[str] = Field(None, description="维护结果")
    parts_replaced: Optional[str] = Field(None, description="更换的零件")
    next_maintenance_date: Optional[datetime] = Field(None, description="下次维护日期")
    notes: Optional[str] = Field(None, description="备注信息")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class DeviceMaintenancePlanCreate(BaseModel):
    """创建设备维护计划模型"""
    
    device_id: int = Field(..., description="设备ID")
    plan_name: str = Field(..., description="计划名称")
    plan_description: Optional[str] = Field(None, description="计划描述")
    maintenance_type: str = Field(..., description="维护类型: preventive/inspection")
    
    frequency_type: str = Field(..., description="频率类型: daily/weekly/monthly/quarterly/yearly/custom")
    frequency_value: int = Field(..., description="频率值")
    frequency_unit: Optional[str] = Field(None, description="频率单位: days/weeks/months/years")
    
    start_date: date = Field(..., description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    next_execution_date: date = Field(..., description="下次执行日期")
    
    estimated_duration: Optional[int] = Field(None, description="预估持续时间（分钟）")
    assigned_team: Optional[str] = Field(None, description="指定团队")
    
    maintenance_checklist: Optional[str] = Field(None, description="维护检查清单，JSON格式")
    required_tools: Optional[str] = Field(None, description="所需工具，JSON格式")
    required_parts: Optional[str] = Field(None, description="所需零件，JSON格式")


class DeviceMaintenancePlanUpdate(BaseModel):
    """更新设备维护计划模型"""
    
    plan_name: Optional[str] = Field(None, description="计划名称")
    plan_description: Optional[str] = Field(None, description="计划描述")
    maintenance_type: Optional[str] = Field(None, description="维护类型")
    
    frequency_type: Optional[str] = Field(None, description="频率类型")
    frequency_value: Optional[int] = Field(None, description="频率值")
    frequency_unit: Optional[str] = Field(None, description="频率单位")
    
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    next_execution_date: Optional[date] = Field(None, description="下次执行日期")
    
    estimated_duration: Optional[int] = Field(None, description="预估持续时间（分钟）")
    assigned_team: Optional[str] = Field(None, description="指定团队")
    is_active: Optional[bool] = Field(None, description="是否激活")
    
    maintenance_checklist: Optional[str] = Field(None, description="维护检查清单，JSON格式")
    required_tools: Optional[str] = Field(None, description="所需工具，JSON格式")
    required_parts: Optional[str] = Field(None, description="所需零件，JSON格式")


class DeviceMaintenancePlanResponse(BaseModel):
    """设备维护计划响应模型"""
    
    id: int = Field(..., description="维护计划ID")
    device_id: int = Field(..., description="设备ID")
    plan_name: str = Field(..., description="计划名称")
    plan_description: Optional[str] = Field(None, description="计划描述")
    maintenance_type: str = Field(..., description="维护类型")
    
    frequency_type: str = Field(..., description="频率类型")
    frequency_value: int = Field(..., description="频率值")
    frequency_unit: Optional[str] = Field(None, description="频率单位")
    
    start_date: date = Field(..., description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    last_execution_date: Optional[date] = Field(None, description="上次执行日期")
    next_execution_date: date = Field(..., description="下次执行日期")
    
    estimated_duration: Optional[int] = Field(None, description="预估持续时间（分钟）")
    assigned_team: Optional[str] = Field(None, description="指定团队")
    is_active: bool = Field(..., description="是否激活")
    
    maintenance_checklist: Optional[str] = Field(None, description="维护检查清单，JSON格式")
    required_tools: Optional[str] = Field(None, description="所需工具，JSON格式")
    required_parts: Optional[str] = Field(None, description="所需零件，JSON格式")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class DeviceMaintenanceReminderResponse(BaseModel):
    """设备维护提醒响应模型"""
    
    id: int = Field(..., description="提醒ID")
    device_id: int = Field(..., description="设备ID")
    maintenance_plan_id: Optional[int] = Field(None, description="维护计划ID")
    
    reminder_type: str = Field(..., description="提醒类型")
    reminder_title: str = Field(..., description="提醒标题")
    reminder_message: str = Field(..., description="提醒消息")
    
    reminder_time: datetime = Field(..., description="提醒时间")
    due_date: datetime = Field(..., description="到期时间")
    
    is_sent: bool = Field(..., description="是否已发送")
    is_read: bool = Field(..., description="是否已读")
    is_dismissed: bool = Field(..., description="是否已忽略")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class DeviceMaintenanceQuery(BaseModel):
    """设备维护查询模型"""
    
    device_id: Optional[int] = Field(None, description="设备ID")
    device_code: Optional[str] = Field(None, description="设备编号")
    maintenance_type: Optional[str] = Field(None, description="维护类型")
    maintenance_status: Optional[str] = Field(None, description="维护状态")
    priority: Optional[str] = Field(None, description="优先级")
    assigned_to: Optional[str] = Field(None, description="负责人")
    maintenance_team: Optional[str] = Field(None, description="维护团队")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(20, description="每页数量", ge=1, le=100)


class DeviceMaintenanceStatistics(BaseModel):
    """设备维护统计模型"""
    
    total_records: int = Field(..., description="总维护记录数")
    planned_records: int = Field(..., description="计划中的记录数")
    in_progress_records: int = Field(..., description="进行中的记录数")
    completed_records: int = Field(..., description="已完成的记录数")
    cancelled_records: int = Field(..., description="已取消的记录数")
    
    overdue_records: int = Field(..., description="逾期记录数")
    upcoming_records: int = Field(..., description="即将到期记录数")
    
    maintenance_types: Dict[str, int] = Field(..., description="维护类型分布")
    priority_distribution: Dict[str, int] = Field(..., description="优先级分布")
    team_workload: Dict[str, int] = Field(..., description="团队工作量分布")
    
    average_completion_time: Optional[float] = Field(None, description="平均完成时间（小时）")
    total_maintenance_cost: Optional[float] = Field(None, description="总维护成本")
    average_maintenance_cost: Optional[float] = Field(None, description="平均维护成本")

# =====================================================
# 设备工艺管理模型
# =====================================================

class DeviceProcessCreate(BaseModel):
    """创建设备工艺模型"""
    
    device_id: int = Field(..., description="设备ID")
    process_name: str = Field(..., description="工艺名称")
    process_code: str = Field(..., description="工艺编码")
    process_version: str = Field("1.0", description="工艺版本")
    process_description: Optional[str] = Field(None, description="工艺描述")
    process_type: str = Field(..., description="工艺类型: welding/cutting/assembly/inspection")
    process_category: Optional[str] = Field(None, description="工艺分类")
    process_parameters: Optional[str] = Field(None, description="工艺参数，JSON格式")
    quality_standards: Optional[str] = Field(None, description="质量标准，JSON格式")
    safety_requirements: Optional[str] = Field(None, description="安全要求，JSON格式")
    estimated_duration: Optional[int] = Field(None, description="预估执行时间（分钟）")
    difficulty_level: str = Field("medium", description="难度等级: easy/medium/hard/expert")
    required_skills: Optional[str] = Field(None, description="所需技能，JSON格式")
    created_by: Optional[str] = Field(None, description="创建人")
    assigned_team: Optional[str] = Field(None, description="指定团队")
    is_template: bool = Field(False, description="是否为模板")


class DeviceProcessUpdate(BaseModel):
    """更新设备工艺模型"""
    
    process_name: Optional[str] = Field(None, description="工艺名称")
    process_version: Optional[str] = Field(None, description="工艺版本")
    process_description: Optional[str] = Field(None, description="工艺描述")
    process_status: Optional[str] = Field(None, description="工艺状态")
    process_type: Optional[str] = Field(None, description="工艺类型")
    process_category: Optional[str] = Field(None, description="工艺分类")
    process_parameters: Optional[str] = Field(None, description="工艺参数，JSON格式")
    quality_standards: Optional[str] = Field(None, description="质量标准，JSON格式")
    safety_requirements: Optional[str] = Field(None, description="安全要求，JSON格式")
    estimated_duration: Optional[int] = Field(None, description="预估执行时间（分钟）")
    difficulty_level: Optional[str] = Field(None, description="难度等级")
    required_skills: Optional[str] = Field(None, description="所需技能，JSON格式")
    assigned_team: Optional[str] = Field(None, description="指定团队")
    is_active: Optional[bool] = Field(None, description="是否激活")
    approval_status: Optional[str] = Field(None, description="审批状态")
    approval_notes: Optional[str] = Field(None, description="审批备注")


class DeviceProcessResponse(BaseModel):
    """设备工艺响应模型"""
    
    id: int = Field(..., description="工艺ID")
    device_id: int = Field(..., description="设备ID")
    device_code: Optional[str] = Field(None, description="设备编号")
    device_name: Optional[str] = Field(None, description="设备名称")
    process_name: str = Field(..., description="工艺名称")
    process_code: str = Field(..., description="工艺编码")
    process_version: str = Field(..., description="工艺版本")
    process_description: Optional[str] = Field(None, description="工艺描述")
    process_status: str = Field(..., description="工艺状态")
    process_type: str = Field(..., description="工艺类型")
    process_category: Optional[str] = Field(None, description="工艺分类")
    process_parameters: Optional[str] = Field(None, description="工艺参数，JSON格式")
    quality_standards: Optional[str] = Field(None, description="质量标准，JSON格式")
    safety_requirements: Optional[str] = Field(None, description="安全要求，JSON格式")
    estimated_duration: Optional[int] = Field(None, description="预估执行时间（分钟）")
    difficulty_level: str = Field(..., description="难度等级")
    required_skills: Optional[str] = Field(None, description="所需技能，JSON格式")
    created_by: Optional[str] = Field(None, description="创建人")
    approved_by: Optional[str] = Field(None, description="审批人")
    assigned_team: Optional[str] = Field(None, description="指定团队")
    parent_process_id: Optional[int] = Field(None, description="父工艺ID")
    is_template: bool = Field(..., description="是否为模板")
    is_active: bool = Field(..., description="是否激活")
    approval_status: str = Field(..., description="审批状态")
    approval_date: Optional[datetime] = Field(None, description="审批日期")
    approval_notes: Optional[str] = Field(None, description="审批备注")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class DeviceProcessExecutionCreate(BaseModel):
    """创建设备工艺执行记录模型"""
    
    device_id: int = Field(..., description="设备ID")
    process_id: int = Field(..., description="工艺ID")
    execution_code: str = Field(..., description="执行编号")
    execution_name: str = Field(..., description="执行名称")
    execution_description: Optional[str] = Field(None, description="执行描述")
    planned_start_time: Optional[datetime] = Field(None, description="计划开始时间")
    planned_end_time: Optional[datetime] = Field(None, description="计划结束时间")
    operator: Optional[str] = Field(None, description="操作员")
    supervisor: Optional[str] = Field(None, description="监督员")
    execution_team: Optional[str] = Field(None, description="执行团队")
    estimated_cost: Optional[float] = Field(None, description="预估成本")
    notes: Optional[str] = Field(None, description="备注信息")


class DeviceProcessExecutionUpdate(BaseModel):
    """更新设备工艺执行记录模型"""
    
    execution_name: Optional[str] = Field(None, description="执行名称")
    execution_description: Optional[str] = Field(None, description="执行描述")
    execution_status: Optional[str] = Field(None, description="执行状态")
    actual_start_time: Optional[datetime] = Field(None, description="实际开始时间")
    actual_end_time: Optional[datetime] = Field(None, description="实际结束时间")
    operator: Optional[str] = Field(None, description="操作员")
    supervisor: Optional[str] = Field(None, description="监督员")
    execution_team: Optional[str] = Field(None, description="执行团队")
    execution_result: Optional[str] = Field(None, description="执行结果")
    quality_result: Optional[str] = Field(None, description="质量结果")
    quality_score: Optional[float] = Field(None, description="质量评分")
    quality_notes: Optional[str] = Field(None, description="质量备注")
    issues_encountered: Optional[str] = Field(None, description="遇到的问题，JSON格式")
    solutions_applied: Optional[str] = Field(None, description="应用的解决方案，JSON格式")
    materials_used: Optional[str] = Field(None, description="使用的材料，JSON格式")
    tools_used: Optional[str] = Field(None, description="使用的工具，JSON格式")
    energy_consumption: Optional[float] = Field(None, description="能耗")
    actual_cost: Optional[float] = Field(None, description="实际成本")
    notes: Optional[str] = Field(None, description="备注信息")


class DeviceProcessExecutionResponse(BaseModel):
    """设备工艺执行记录响应模型"""
    
    id: int = Field(..., description="执行记录ID")
    device_id: int = Field(..., description="设备ID")
    process_id: int = Field(..., description="工艺ID")
    device_code: Optional[str] = Field(None, description="设备编号")
    device_name: Optional[str] = Field(None, description="设备名称")
    process_name: Optional[str] = Field(None, description="工艺名称")
    process_code: Optional[str] = Field(None, description="工艺编码")
    execution_code: str = Field(..., description="执行编号")
    execution_name: str = Field(..., description="执行名称")
    execution_description: Optional[str] = Field(None, description="执行描述")
    execution_status: str = Field(..., description="执行状态")
    planned_start_time: Optional[datetime] = Field(None, description="计划开始时间")
    planned_end_time: Optional[datetime] = Field(None, description="计划结束时间")
    actual_start_time: Optional[datetime] = Field(None, description="实际开始时间")
    actual_end_time: Optional[datetime] = Field(None, description="实际结束时间")
    operator: Optional[str] = Field(None, description="操作员")
    supervisor: Optional[str] = Field(None, description="监督员")
    execution_team: Optional[str] = Field(None, description="执行团队")
    execution_result: Optional[str] = Field(None, description="执行结果")
    quality_result: Optional[str] = Field(None, description="质量结果")
    quality_score: Optional[float] = Field(None, description="质量评分")
    quality_notes: Optional[str] = Field(None, description="质量备注")
    issues_encountered: Optional[str] = Field(None, description="遇到的问题，JSON格式")
    solutions_applied: Optional[str] = Field(None, description="应用的解决方案，JSON格式")
    materials_used: Optional[str] = Field(None, description="使用的材料，JSON格式")
    tools_used: Optional[str] = Field(None, description="使用的工具，JSON格式")
    energy_consumption: Optional[float] = Field(None, description="能耗")
    estimated_cost: Optional[float] = Field(None, description="预估成本")
    actual_cost: Optional[float] = Field(None, description="实际成本")
    notes: Optional[str] = Field(None, description="备注信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class DeviceProcessTemplateCreate(BaseModel):
    """创建设备工艺模板模型"""
    
    template_name: str = Field(..., description="模板名称")
    template_code: str = Field(..., description="模板编码")
    template_description: Optional[str] = Field(None, description="模板描述")
    template_category: str = Field(..., description="模板分类")
    device_type: Optional[str] = Field(None, description="适用设备类型")
    process_type: str = Field(..., description="工艺类型")
    template_content: str = Field(..., description="模板内容，JSON格式")
    default_parameters: Optional[str] = Field(None, description="默认参数，JSON格式")
    parameter_constraints: Optional[str] = Field(None, description="参数约束，JSON格式")
    is_public: bool = Field(False, description="是否公开")
    created_by: Optional[str] = Field(None, description="创建人")


class DeviceProcessTemplateUpdate(BaseModel):
    """更新设备工艺模板模型"""
    
    template_name: Optional[str] = Field(None, description="模板名称")
    template_description: Optional[str] = Field(None, description="模板描述")
    template_category: Optional[str] = Field(None, description="模板分类")
    device_type: Optional[str] = Field(None, description="适用设备类型")
    process_type: Optional[str] = Field(None, description="工艺类型")
    template_content: Optional[str] = Field(None, description="模板内容，JSON格式")
    default_parameters: Optional[str] = Field(None, description="默认参数，JSON格式")
    parameter_constraints: Optional[str] = Field(None, description="参数约束，JSON格式")
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_public: Optional[bool] = Field(None, description="是否公开")
    maintained_by: Optional[str] = Field(None, description="维护人")


class DeviceProcessTemplateResponse(BaseModel):
    """设备工艺模板响应模型"""
    
    id: int = Field(..., description="模板ID")
    template_name: str = Field(..., description="模板名称")
    template_code: str = Field(..., description="模板编码")
    template_description: Optional[str] = Field(None, description="模板描述")
    template_category: str = Field(..., description="模板分类")
    device_type: Optional[str] = Field(None, description="适用设备类型")
    process_type: str = Field(..., description="工艺类型")
    template_content: str = Field(..., description="模板内容，JSON格式")
    default_parameters: Optional[str] = Field(None, description="默认参数，JSON格式")
    parameter_constraints: Optional[str] = Field(None, description="参数约束，JSON格式")
    is_active: bool = Field(..., description="是否激活")
    is_public: bool = Field(..., description="是否公开")
    created_by: Optional[str] = Field(None, description="创建人")
    maintained_by: Optional[str] = Field(None, description="维护人")
    usage_count: int = Field(..., description="使用次数")
    last_used_date: Optional[datetime] = Field(None, description="最后使用日期")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class DeviceProcessQuery(BaseModel):
    """设备工艺查询模型"""
    
    device_id: Optional[int] = Field(None, description="设备ID")
    device_code: Optional[str] = Field(None, description="设备编号")
    process_type: Optional[str] = Field(None, description="工艺类型")
    process_status: Optional[str] = Field(None, description="工艺状态")
    approval_status: Optional[str] = Field(None, description="审批状态")
    difficulty_level: Optional[str] = Field(None, description="难度等级")
    created_by: Optional[str] = Field(None, description="创建人")
    assigned_team: Optional[str] = Field(None, description="指定团队")
    is_template: Optional[bool] = Field(None, description="是否为模板")
    is_active: Optional[bool] = Field(None, description="是否激活")
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(20, description="每页数量", ge=1, le=100)


class DeviceProcessStatistics(BaseModel):
    """设备工艺统计模型"""
    
    total_processes: int = Field(..., description="工艺总数")
    active_processes: int = Field(..., description="激活工艺数")
    template_processes: int = Field(..., description="模板工艺数")
    draft_processes: int = Field(..., description="草稿工艺数")
    approved_processes: int = Field(..., description="已审批工艺数")
    
    process_types: Dict[str, int] = Field(..., description="工艺类型分布")
    difficulty_distribution: Dict[str, int] = Field(..., description="难度等级分布")
    approval_status_distribution: Dict[str, int] = Field(..., description="审批状态分布")
    team_workload: Dict[str, int] = Field(..., description="团队工作量分布")
    
    total_executions: int = Field(..., description="总执行次数")
    completed_executions: int = Field(..., description="已完成执行次数")
    success_rate: Optional[float] = Field(None, description="成功率")
    average_execution_time: Optional[float] = Field(None, description="平均执行时间（小时）")
    average_quality_score: Optional[float] = Field(None, description="平均质量评分")


# =====================================================
# 设备维修记录管理模型
# =====================================================

class DeviceRepairRecordCreate(BaseModel):
    """创建设备维修记录模型"""
    
    device_id: int = Field(..., description="设备ID")
    device_type: str = Field(..., description="设备类型")
    repair_date: date = Field(..., description="报修日期")
    priority: str = Field("normal", description="优先级：low/normal/high/urgent")
    
    # 申请人信息
    applicant: str = Field(..., description="申请人")
    applicant_phone: Optional[str] = Field(None, description="申请人电话")
    applicant_dept: Optional[str] = Field(None, description="申请部门")
    applicant_workshop: Optional[str] = Field(None, description="申请车间")
    construction_unit: Optional[str] = Field(None, description="施工单位")
    
    # 故障信息
    is_fault: bool = Field(True, description="是否故障")
    fault_reason: Optional[str] = Field(None, description="故障原因")
    damage_category: Optional[str] = Field(None, description="损坏类别")
    fault_content: Optional[str] = Field(None, description="故障内容描述")
    fault_location: Optional[str] = Field(None, description="故障部位")
    
    # 维修信息
    repair_content: Optional[str] = Field(None, description="维修内容")
    parts_name: Optional[str] = Field(None, description="更换配件名称")
    repairer: Optional[str] = Field(None, description="维修人员")
    repair_start_time: Optional[datetime] = Field(None, description="维修开始时间")
    repair_completion_date: Optional[date] = Field(None, description="维修完成日期")
    repair_cost: Optional[float] = Field(None, description="维修成本")
    
    # 设备特定信息
    device_specific_data: Optional[Dict[str, Any]] = Field(None, description="设备特定字段数据")
    
    # 附加信息
    remarks: Optional[str] = Field(None, description="备注")
    attachments: Optional[Dict[str, Any]] = Field(None, description="附件信息")
    
    @validator('applicant_phone')
    def validate_phone(cls, v):
        if v and not v.isdigit():
            raise ValueError('电话号码只能包含数字')
        return v
    
    @validator('repair_completion_date')
    def validate_completion_date(cls, v, values):
        if v and 'repair_date' in values and v < values['repair_date']:
            raise ValueError('维修完成日期不能早于报修日期')
        return v


class DeviceRepairRecordUpdate(BaseModel):
    """更新设备维修记录模型"""
    
    repair_status: Optional[str] = Field(None, description="维修状态：pending/in_progress/completed/cancelled")
    priority: Optional[str] = Field(None, description="优先级")
    
    # 申请人信息
    applicant: Optional[str] = Field(None, description="申请人")
    applicant_phone: Optional[str] = Field(None, description="申请人电话")
    applicant_dept: Optional[str] = Field(None, description="申请部门")
    applicant_workshop: Optional[str] = Field(None, description="申请车间")
    construction_unit: Optional[str] = Field(None, description="施工单位")
    
    # 故障信息
    is_fault: Optional[bool] = Field(None, description="是否故障")
    fault_reason: Optional[str] = Field(None, description="故障原因")
    damage_category: Optional[str] = Field(None, description="损坏类别")
    fault_content: Optional[str] = Field(None, description="故障内容描述")
    fault_location: Optional[str] = Field(None, description="故障部位")
    
    # 维修信息
    repair_content: Optional[str] = Field(None, description="维修内容")
    parts_name: Optional[str] = Field(None, description="更换配件名称")
    repairer: Optional[str] = Field(None, description="维修人员")
    repair_start_time: Optional[datetime] = Field(None, description="维修开始时间")
    repair_completion_date: Optional[date] = Field(None, description="维修完成日期")
    repair_cost: Optional[float] = Field(None, description="维修成本")
    
    # 设备特定信息
    device_specific_data: Optional[Dict[str, Any]] = Field(None, description="设备特定字段数据")
    
    # 附加信息
    remarks: Optional[str] = Field(None, description="备注")
    attachments: Optional[Dict[str, Any]] = Field(None, description="附件信息")
    
    @validator('applicant_phone')
    def validate_phone(cls, v):
        if v and not v.isdigit():
            raise ValueError('电话号码只能包含数字')
        return v


class DeviceRepairRecordResponse(BaseModel):
    """设备维修记录响应模型"""
    
    id: int = Field(..., description="维修记录ID")
    device_id: int = Field(..., description="设备ID")
    device_type: str = Field(..., description="设备类型")
    repair_date: date = Field(..., description="报修日期")
    repair_code: Optional[str] = Field(None, description="维修单号")
    repair_status: str = Field(..., description="维修状态")
    priority: str = Field(..., description="优先级")
    
    # 申请人信息
    applicant: str = Field(..., description="申请人")
    applicant_phone: Optional[str] = Field(None, description="申请人电话")
    applicant_dept: Optional[str] = Field(None, description="申请部门")
    applicant_workshop: Optional[str] = Field(None, description="申请车间")
    construction_unit: Optional[str] = Field(None, description="施工单位")
    
    # 故障信息
    is_fault: bool = Field(..., description="是否故障")
    fault_reason: Optional[str] = Field(None, description="故障原因")
    damage_category: Optional[str] = Field(None, description="损坏类别")
    fault_content: Optional[str] = Field(None, description="故障内容描述")
    fault_location: Optional[str] = Field(None, description="故障部位")
    
    # 维修信息
    repair_content: Optional[str] = Field(None, description="维修内容")
    parts_name: Optional[str] = Field(None, description="更换配件名称")
    repairer: Optional[str] = Field(None, description="维修人员")
    repair_start_time: Optional[datetime] = Field(None, description="维修开始时间")
    repair_completion_date: Optional[date] = Field(None, description="维修完成日期")
    repair_cost: Optional[float] = Field(None, description="维修成本")
    
    # 设备特定信息
    device_specific_data: Optional[Dict[str, Any]] = Field(None, description="设备特定字段数据")
    
    # 附加信息
    remarks: Optional[str] = Field(None, description="备注")
    attachments: Optional[Dict[str, Any]] = Field(None, description="附件信息")
    
    # 审计字段
    created_by: Optional[int] = Field(None, description="创建人ID")
    updated_by: Optional[int] = Field(None, description="更新人ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class DeviceRepairRecordQuery(BaseModel):
    """设备维修记录查询模型"""
    
    device_id: Optional[int] = Field(None, description="设备ID筛选")
    device_type: Optional[str] = Field(None, description="设备类型筛选")
    repair_status: Optional[str] = Field(None, description="维修状态筛选")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    applicant: Optional[str] = Field(None, description="申请人筛选")
    repairer: Optional[str] = Field(None, description="维修人员筛选")
    priority: Optional[str] = Field(None, description="优先级筛选")
    is_fault: Optional[bool] = Field(None, description="是否故障筛选")
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(20, description="每页数量", ge=1, le=100)


class DeviceRepairRecordStatistics(BaseModel):
    """设备维修记录统计模型"""
    
    total_records: int = Field(..., description="总维修记录数")
    pending_records: int = Field(..., description="待处理记录数")
    in_progress_records: int = Field(..., description="进行中记录数")
    completed_records: int = Field(..., description="已完成记录数")
    cancelled_records: int = Field(..., description="已取消记录数")
    
    fault_records: int = Field(..., description="故障记录数")
    maintenance_records: int = Field(..., description="维护记录数")
    
    device_type_distribution: Dict[str, int] = Field(..., description="设备类型分布")
    priority_distribution: Dict[str, int] = Field(..., description="优先级分布")
    fault_reason_distribution: Dict[str, int] = Field(..., description="故障原因分布")
    
    average_repair_time: Optional[float] = Field(None, description="平均维修时间（天）")
    total_repair_cost: Optional[float] = Field(None, description="总维修成本")
    average_repair_cost: Optional[float] = Field(None, description="平均维修成本")


# =====================================================
# 设备字段配置扩展模型
# =====================================================

class DeviceFieldConfigResponse(BaseModel):
    """设备字段配置响应模型"""
    
    field_code: str = Field(..., description="字段代码")
    field_name: str = Field(..., description="字段名称")
    field_type: str = Field(..., description="字段类型")
    field_category: str = Field(..., description="字段分类")
    is_required: bool = Field(..., description="是否必填")
    sort_order: int = Field(..., description="排序顺序")
    options: Optional[List[Dict[str, str]]] = Field(None, description="字段选项（用于下拉选择）")
    validation_rule: Optional[Dict[str, Any]] = Field(None, description="验证规则")
    
    class Config:
        from_attributes = True


class DeviceFieldOption(BaseModel):
    """设备字段选项模型"""
    
    label: str = Field(..., description="选项标签")
    value: str = Field(..., description="选项值")


class RepairCodeGenerateRequest(BaseModel):
    """维修单号生成请求模型"""
    
    device_type: str = Field(..., description="设备类型")
    repair_date: date = Field(..., description="报修日期")


class RepairCodeGenerateResponse(BaseModel):
    """维修单号生成响应模型"""
    
    repair_code: str = Field(..., description="生成的维修单号")
    format_pattern: str = Field(..., description="单号格式模式")
    
    class Config:
        from_attributes = True


# =====================================================
# 设备维修记录管理模型
# =====================================================

class DeviceRepairRecordCreate(BaseModel):
    """创建设备维修记录模型"""
    
    device_id: int = Field(..., description="设备ID")
    device_type: str = Field(..., description="设备类型")
    
    # 基础信息
    repair_date: date = Field(..., description="报修日期")
    repair_status: RepairStatus = Field("pending", description="维修状态")
    priority: RepairPriority = Field("medium", description="优先级")
    
    # 申请人信息
    applicant: str = Field(..., description="申请人")
    applicant_phone: Optional[str] = Field(None, description="申请人电话")
    applicant_dept: Optional[str] = Field(None, description="申请部门")
    applicant_workshop: Optional[str] = Field(None, description="申请车间")
    construction_unit: Optional[str] = Field(None, description="施工单位")
    
    # 故障信息
    is_fault: bool = Field(True, description="是否故障")
    fault_reason: Optional[str] = Field(None, description="故障原因")
    damage_category: Optional[str] = Field(None, description="损坏类别")
    fault_content: Optional[str] = Field(None, description="故障内容描述")
    fault_location: Optional[str] = Field(None, description="故障部位")
    
    # 维修信息
    repair_content: Optional[str] = Field(None, description="维修内容")
    parts_name: Optional[str] = Field(None, description="更换配件名称")
    repairer: Optional[str] = Field(None, description="维修人员")
    repair_start_time: Optional[datetime] = Field(None, description="维修开始时间")
    repair_completion_date: Optional[date] = Field(None, description="维修完成日期")
    repair_cost: Optional[float] = Field(None, description="维修成本")
    
    # 设备特定信息
    device_specific_data: Optional[Dict[str, Any]] = Field(None, description="设备特定字段数据")
    
    # 附加信息
    remarks: Optional[str] = Field(None, description="备注")
    attachments: Optional[Dict[str, Any]] = Field(None, description="附件信息")

    @validator('device_id')
    def validate_device_id(cls, v):
        if v is None or v <= 0:
            raise ValueError('设备ID必须为正整数')
        return v

    @validator('device_type', pre=True)
    def validate_device_type(cls, v):
        """验证设备类型字段"""
        from pydantic import ValidationError
        
        if v is None:
            # None值不应该作为设备类型
            raise ValidationError([{"loc": ("device_type",), "msg": "设备类型不能为空", "type": "value_error"}], cls)
        elif isinstance(v, bool):
            # 布尔值不应该作为设备类型
            raise ValidationError([{"loc": ("device_type",), "msg": "设备类型必须为字符串", "type": "type_error"}], cls)
        elif isinstance(v, (list, dict)):
            # 列表和字典类型不应该作为设备类型
            raise ValidationError([{"loc": ("device_type",), "msg": "设备类型必须为字符串", "type": "type_error"}], cls)
        elif isinstance(v, (int, float)):
            # 数字类型转换为字符串
            v_str = str(v)
        else:
            # 其他类型（包括字符串）转换为字符串
            v_str = str(v)
        
        # 检查是否为空或只包含空格
        if not v_str or not v_str.strip():
            raise ValidationError([{"loc": ("device_type",), "msg": "设备类型不能为空或只包含空格", "type": "value_error"}], cls)
        
        # 检查长度限制
        trimmed_value = v_str.strip()
        if len(trimmed_value) > 50:
            raise ValidationError([{"loc": ("device_type",), "msg": "设备类型长度不能超过50个字符", "type": "value_error"}], cls)
        
        return trimmed_value

    @validator('applicant')
    def validate_applicant(cls, v):
        if not v or not v.strip():
            raise ValueError('申请人不能为空')
        if len(v.strip()) > 50:
            raise ValueError('申请人姓名长度不能超过50个字符')
        return v.strip()

    @validator('applicant_phone')
    def validate_phone(cls, v):
        if v and (len(v) != 11 or not v.isdigit()):
            raise ValueError('手机号码必须为11位数字')
        return v

    @validator('fault_content')
    def validate_fault_content(cls, v):
        if v and len(v) > 1000:
            raise ValueError('故障内容描述长度不能超过1000个字符')
        return v

    @validator('repair_content')
    def validate_repair_content(cls, v):
        if v and len(v) > 1000:
            raise ValueError('维修内容描述长度不能超过1000个字符')
        return v

    @validator('repair_status')
    def validate_repair_status(cls, v):
        valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        if v not in valid_statuses:
            raise ValueError(f'维修状态必须为以下值之一: {", ".join(valid_statuses)}')
        return v

    @validator('priority')
    def validate_priority(cls, v):
        valid_priorities = [priority.value for priority in RepairPriority]
        if v not in valid_priorities:
            raise ValueError(f'优先级必须为以下值之一: {", ".join(valid_priorities)}')
        return v

    @validator('repair_cost')
    def validate_repair_cost(cls, v):
        if v is not None and v < 0:
            raise ValueError('维修成本不能为负数')
        return v

    @validator('repair_completion_date')
    def validate_completion_date(cls, v, values):
        if v and 'repair_date' in values and v < values['repair_date']:
            raise ValueError('维修完成日期不能早于报修日期')
        return v


class DeviceRepairRecordUpdate(BaseModel):
    """更新设备维修记录模型"""
    
    # 基础信息
    repair_date: Optional[date] = Field(None, description="报修日期")
    repair_status: Optional[RepairStatus] = Field(None, description="维修状态")
    priority: Optional[RepairPriority] = Field(None, description="优先级")
    
    # 申请人信息
    applicant: Optional[str] = Field(None, description="申请人")
    applicant_phone: Optional[str] = Field(None, description="申请人电话")
    applicant_dept: Optional[str] = Field(None, description="申请部门")
    applicant_workshop: Optional[str] = Field(None, description="申请车间")
    construction_unit: Optional[str] = Field(None, description="施工单位")
    
    # 故障信息
    is_fault: Optional[bool] = Field(None, description="是否故障")
    fault_reason: Optional[str] = Field(None, description="故障原因")
    damage_category: Optional[str] = Field(None, description="损坏类别")
    fault_content: Optional[str] = Field(None, description="故障内容描述")
    fault_location: Optional[str] = Field(None, description="故障部位")
    
    # 维修信息
    repair_content: Optional[str] = Field(None, description="维修内容")
    parts_name: Optional[str] = Field(None, description="更换配件名称")
    repairer: Optional[str] = Field(None, description="维修人员")
    repair_start_time: Optional[datetime] = Field(None, description="维修开始时间")
    repair_completion_date: Optional[date] = Field(None, description="维修完成日期")
    repair_cost: Optional[float] = Field(None, description="维修成本")
    
    # 设备特定信息
    device_specific_data: Optional[Dict[str, Any]] = Field(None, description="设备特定字段数据")
    
    # 附加信息
    remarks: Optional[str] = Field(None, description="备注")
    attachments: Optional[Dict[str, Any]] = Field(None, description="附件信息")

    @validator('applicant')
    def validate_applicant(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('申请人不能为空')
            if len(v.strip()) > 50:
                raise ValueError('申请人姓名长度不能超过50个字符')
        return v.strip() if v else v

    @validator('applicant_phone')
    def validate_phone(cls, v):
        if v and (not v.isdigit() or len(v) != 11):
            raise ValueError('申请人电话必须为11位数字')
        return v

    @validator('fault_content')
    def validate_fault_content(cls, v):
        if v is not None and len(v) > 1000:
            raise ValueError('故障内容描述长度不能超过1000个字符')
        return v

    @validator('repair_content')
    def validate_repair_content(cls, v):
        if v is not None and len(v) > 1000:
            raise ValueError('维修内容描述长度不能超过1000个字符')
        return v

    @validator('repair_status')
    def validate_repair_status(cls, v):
        if v is not None:
            valid_statuses = [status.value for status in RepairStatus]
            if v not in valid_statuses:
                raise ValueError(f'维修状态必须为以下值之一: {", ".join(valid_statuses)}')
        return v

    @validator('priority')
    def validate_priority(cls, v):
        if v is not None:
            valid_priorities = [priority.value for priority in RepairPriority]
            if v not in valid_priorities:
                raise ValueError(f'优先级必须为以下值之一: {", ".join(valid_priorities)}')
        return v

    @validator('repair_cost')
    def validate_repair_cost(cls, v):
        if v is not None and v < 0:
            raise ValueError('维修成本不能为负数')
        return v

    @validator('repair_completion_date')
    def validate_completion_date(cls, v, values):
        if v and 'repair_date' in values and values['repair_date'] and v < values['repair_date']:
            raise ValueError('维修完成日期不能早于报修日期')
        return v


class DeviceRepairRecordResponse(BaseModel):
    """设备维修记录响应模型"""
    
    id: int = Field(..., description="维修记录ID")
    device_id: int = Field(..., description="设备ID")
    device_code: Optional[str] = Field(None, description="设备编号")  # 新增字段
    device_type: str = Field(..., description="设备类型")
    
    # 基础信息
    repair_date: date = Field(..., description="报修日期")
    repair_code: Optional[str] = Field(None, description="维修单号")
    repair_status: RepairStatus = Field(..., description="维修状态")
    priority: RepairPriority = Field(..., description="优先级")
    
    # 申请人信息
    applicant: str = Field(..., description="申请人")
    applicant_phone: Optional[str] = Field(None, description="申请人电话")
    applicant_dept: Optional[str] = Field(None, description="申请部门")
    applicant_workshop: Optional[str] = Field(None, description="申请车间")
    construction_unit: Optional[str] = Field(None, description="施工单位")
    
    # 故障信息
    is_fault: bool = Field(..., description="是否故障")
    fault_reason: Optional[str] = Field(None, description="故障原因")
    damage_category: Optional[str] = Field(None, description="损坏类别")
    fault_content: Optional[str] = Field(None, description="故障内容描述")
    fault_location: Optional[str] = Field(None, description="故障部位")
    
    # 维修信息
    repair_content: Optional[str] = Field(None, description="维修内容")
    parts_name: Optional[str] = Field(None, description="更换配件名称")
    repairer: Optional[str] = Field(None, description="维修人员")
    repair_start_time: Optional[datetime] = Field(None, description="维修开始时间")
    repair_completion_date: Optional[date] = Field(None, description="维修完成日期")
    repair_cost: Optional[float] = Field(None, description="维修成本")
    
    # 设备特定信息
    device_specific_data: Optional[Dict[str, Any]] = Field(None, description="设备特定字段数据")
    
    # 附加信息
    remarks: Optional[str] = Field(None, description="备注")
    attachments: Optional[Dict[str, Any]] = Field(None, description="附件信息")
    
    # 审计字段
    created_by: Optional[int] = Field(None, description="创建人ID")
    updated_by: Optional[int] = Field(None, description="更新人ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 关联设备信息
    device: Optional[Dict[str, Any]] = Field(None, description="设备信息")
    
    class Config:
        from_attributes = True


class DeviceRepairRecordQuery(BaseModel):
    """设备维修记录查询模型"""
    
    device_id: Optional[int] = Field(None, description="设备ID筛选")
    device_type: Optional[str] = Field(None, description="设备类型筛选")
    repair_status: Optional[str] = Field(None, description="维修状态筛选")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    applicant: Optional[str] = Field(None, description="申请人筛选")
    repairer: Optional[str] = Field(None, description="维修人员筛选")
    priority: Optional[str] = Field(None, description="优先级筛选")
    is_fault: Optional[bool] = Field(None, description="是否故障筛选")
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(20, description="每页数量", ge=1, le=100)


class DeviceRepairRecordStatistics(BaseModel):
    """设备维修记录统计模型"""
    
    total_records: int = Field(..., description="总维修记录数")
    pending_records: int = Field(..., description="待处理记录数")
    in_progress_records: int = Field(..., description="进行中记录数")
    completed_records: int = Field(..., description="已完成记录数")
    cancelled_records: int = Field(..., description="已取消记录数")
    
    fault_records: int = Field(..., description="故障记录数")
    maintenance_records: int = Field(..., description="维护记录数")
    
    device_type_distribution: Dict[str, int] = Field(..., description="设备类型分布")
    priority_distribution: Dict[str, int] = Field(..., description="优先级分布")
    status_distribution: Dict[str, int] = Field(..., description="状态分布")
    monthly_trend: Dict[str, int] = Field(..., description="月度趋势")
    
    average_repair_time: Optional[float] = Field(None, description="平均维修时间（天）")
    total_repair_cost: Optional[float] = Field(None, description="总维修成本")
    average_repair_cost: Optional[float] = Field(None, description="平均维修成本")


class RepairCodeGenerateRequest(BaseModel):
    """维修单号生成请求模型"""
    
    device_type: str = Field(..., description="设备类型")
    repair_date: date = Field(..., description="报修日期")


class RepairCodeGenerateResponse(BaseModel):
    """维修单号生成响应模型"""
    
    repair_code: str = Field(..., description="生成的维修单号")
    device_type: str = Field(..., description="设备类型")
    repair_date: date = Field(..., description="报修日期")