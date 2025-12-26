from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


# =====================================================
# 焊机日报相关模型
# =====================================================


class WeldingDailyReportQuery(BaseModel):
    """焊机日报查询模型"""
    
    report_date: date = Field(..., description="报告日期", example="2025-01-24")
    device_type: str = Field("welding", description="设备类型，固定为welding")
    
    class Config:
        from_attributes = True
        json_encoders = {date: lambda v: v.isoformat()}


class WeldingDailyReportSummary(BaseModel):
    """焊机日报汇总响应模型"""
    
    total_duration: Optional[int] = Field(None, description="总焊接时长(秒)")
    total_wire: Optional[float] = Field(None, description="总焊丝消耗(kg)")
    total_gas: Optional[float] = Field(None, description="总气体消耗(升)")
    total_energy: Optional[float] = Field(None, description="总能耗(kWh)")
    
    class Config:
        from_attributes = True
        json_encoders = {date: lambda v: v.isoformat()}


class WeldingDailyReportDetail(BaseModel):
    """焊机日报详情响应模型"""
    
    id: int = Field(..., description="记录ID")
    prod_code: str = Field(..., description="产品编码")
    report_date: str = Field(..., description="报告日期")
    shift: Optional[str] = Field(None, description="班次")
    operator: Optional[str] = Field(None, description="操作员")
    welding_duration_sec: Optional[int] = Field(None, description="焊接时长(秒)")
    wire_consumed_kg: Optional[float] = Field(None, description="焊丝消耗(kg)")
    gas_consumed_liter: Optional[float] = Field(None, description="气体消耗(升)")
    energy_consumed_kwh: Optional[float] = Field(None, description="能耗(kWh)")
    weld_length_m: Optional[float] = Field(None, description="焊缝长度(米)")
    defect_count: Optional[int] = Field(None, description="缺陷数量")
    rework_count: Optional[int] = Field(None, description="返工次数")
    quality_score: Optional[float] = Field(None, description="质量评分")
    notes: Optional[str] = Field(None, description="备注")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")
    
    class Config:
        from_attributes = True
        json_encoders = {date: lambda v: v.isoformat()}


class WeldingDailyReportDetailList(BaseModel):
    """焊机日报详情列表响应模型"""
    
    data: List[WeldingDailyReportDetail] = Field(..., description="日报详情列表")
    total: int = Field(..., description="总记录数")
    
    class Config:
        from_attributes = True
        json_encoders = {date: lambda v: v.isoformat()}