"""
设备维修记录服务层

提供维修记录的业务逻辑处理，包括数据验证、创建、更新、删除等操作。
将业务逻辑从API层分离，提高代码的可维护性和可测试性。
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from tortoise.transactions import in_transaction

from app.models.device import DeviceRepairRecord, DeviceInfo
from app.models.admin import User  # 暂时移除AuditLog导入
from app.schemas.devices import DeviceRepairRecordCreate, DeviceRepairRecordUpdate
from app.services.device_maintenance_permission_service import DeviceMaintenanceAuditAction
from app.api.v2.device_repair_records import generate_repair_code

logger = logging.getLogger(__name__)


class DeviceRepairRecordService:
    """设备维修记录服务类"""
    
    @staticmethod
    async def validate_device_exists(device_id: int) -> Optional[DeviceInfo]:
        """
        验证设备是否存在
        
        Args:
            device_id: 设备ID
            
        Returns:
            DeviceInfo: 设备信息，如果不存在返回None
        """
        return await DeviceInfo.get_or_none(id=device_id)
    
    @staticmethod
    def _prepare_create_data(record_data: DeviceRepairRecordCreate, repair_code: str) -> Dict[str, Any]:
        """
        准备创建维修记录的数据
        
        Args:
            record_data: 维修记录创建数据
            repair_code: 维修单号
            
        Returns:
            Dict[str, Any]: 准备好的创建数据
        """
        # 基础必填字段
        create_data = {
            "repair_code": repair_code,
            "device_id": record_data.device_id,
            "device_type": record_data.device_type,
            "repair_date": record_data.repair_date,
            "applicant": record_data.applicant,
            "is_fault": record_data.is_fault,
            "repair_status": record_data.repair_status or "pending",
            "priority": record_data.priority or "normal"
        }
        
        # 可选字段映射
        optional_fields = [
            'fault_content', 'repair_content', 'repairer', 'repair_completion_date',
            'repair_cost', 'remarks', 'applicant_phone', 'applicant_dept',
            'applicant_workshop', 'construction_unit', 'fault_reason',
            'damage_category', 'fault_location', 'parts_name', 'repair_start_time'
        ]
        
        for field in optional_fields:
            if hasattr(record_data, field):
                value = getattr(record_data, field)
                if value is not None and (not isinstance(value, str) or value.strip()):
                    create_data[field] = value
        
        return create_data
    
    @staticmethod
    def _validate_create_data(record_data: DeviceRepairRecordCreate) -> List[str]:
        """
        验证创建数据
        
        Args:
            record_data: 维修记录创建数据
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not record_data.applicant or record_data.applicant.strip() == "":
            errors.append("申请人不能为空")
        
        if record_data.is_fault and (not record_data.fault_content or record_data.fault_content.strip() == ""):
            errors.append("故障维修必须填写故障描述")
        
        if record_data.device_id <= 0:
            errors.append("设备ID必须大于0")
        
        return errors
    
    @staticmethod
    def _validate_update_data(update_data: Dict[str, Any]) -> List[str]:
        """
        验证更新数据
        
        Args:
            update_data: 更新数据字典
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if 'fault_content' in update_data and (not update_data['fault_content'] or update_data['fault_content'].strip() == ""):
            errors.append("故障描述不能为空")
        
        if 'applicant' in update_data and (not update_data['applicant'] or update_data['applicant'].strip() == ""):
            errors.append("申请人不能为空")
        
        return errors
    
    @staticmethod
    async def create_repair_record(
        record_data: DeviceRepairRecordCreate,
        current_user: User
    ) -> Dict[str, Any]:
        """
        创建维修记录
        
        Args:
            record_data: 维修记录创建数据
            current_user: 当前用户
            
        Returns:
            Dict[str, Any]: 包含结果状态和数据的字典
        """
        try:
            # 数据验证
            validation_errors = DeviceRepairRecordService._validate_create_data(record_data)
            if validation_errors:
                return {
                    "success": False,
                    "error_type": "validation",
                    "message": "数据验证失败: " + "; ".join(validation_errors),
                    "details": validation_errors
                }
            
            # 验证设备是否存在
            device = await DeviceRepairRecordService.validate_device_exists(record_data.device_id)
            if not device:
                return {
                    "success": False,
                    "error_type": "not_found",
                    "message": f"设备不存在 (ID: {record_data.device_id})"
                }
            
            # 生成维修单号
            try:
                repair_code = await generate_repair_code(record_data.device_type, record_data.repair_date)
            except Exception as code_error:
                logger.error(f"生成维修单号失败: {str(code_error)}")
                return {
                    "success": False,
                    "error_type": "code_generation",
                    "message": f"生成维修单号失败: {str(code_error)}"
                }
            
            # 准备创建数据
            create_data = DeviceRepairRecordService._prepare_create_data(record_data, repair_code)
            
            # 在事务中创建维修记录
            async with in_transaction():
                repair_record = await DeviceRepairRecord.create(**create_data)
                
                # 获取关联的设备信息以获取device_code
                await repair_record.fetch_related('device')
                device_code = repair_record.device.device_code if repair_record.device else None
                
                logger.info(f"维修记录创建成功: id={repair_record.id}, repair_code={repair_record.repair_code}, device_id={record_data.device_id}, user={current_user.username}")
                
                # 返回完整的数据结构，匹配前端期望
                return {
                    "success": True,
                    "data": {
                        "id": repair_record.id,
                        "device_id": repair_record.device_id,
                        "device_code": device_code,
                        "device_type": repair_record.device_type,
                        "repair_date": repair_record.repair_date.isoformat() if repair_record.repair_date else None,
                        "repair_code": repair_record.repair_code,
                        "repair_status": repair_record.repair_status,
                        "priority": repair_record.priority,
                        
                        # 申请人信息
                        "applicant": repair_record.applicant,
                        "applicant_phone": repair_record.applicant_phone,
                        "applicant_dept": repair_record.applicant_dept,
                        "applicant_workshop": repair_record.applicant_workshop,
                        "construction_unit": repair_record.construction_unit,
                        
                        # 故障信息
                        "is_fault": repair_record.is_fault,
                        "fault_reason": repair_record.fault_reason,
                        "damage_category": repair_record.damage_category,
                        "fault_content": repair_record.fault_content,
                        "fault_location": repair_record.fault_location,
                        
                        # 维修信息
                        "repair_content": repair_record.repair_content,
                        "parts_name": repair_record.parts_name,
                        "repairer": repair_record.repairer,
                        "repair_start_time": repair_record.repair_start_time.isoformat() if repair_record.repair_start_time else None,
                        "repair_completion_date": repair_record.repair_completion_date.isoformat() if repair_record.repair_completion_date else None,
                        "repair_cost": float(repair_record.repair_cost) if repair_record.repair_cost else None,
                        
                        # 扩展数据
                        "device_specific_data": repair_record.device_specific_data or {},
                        
                        # 其他信息
                        "remarks": repair_record.remarks,
                        "attachments": repair_record.attachments or {},
                        "created_by": repair_record.created_by,
                        "updated_by": repair_record.updated_by,
                        "created_at": repair_record.created_at.isoformat(),
                        "updated_at": repair_record.updated_at.isoformat()
                    },
                    "message": "维修记录创建成功"
                }
                
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"创建维修记录失败: {str(e)}")
            logger.error(f"错误堆栈: {error_traceback}")
            return {
                "success": False,
                "error_type": "database",
                "message": f"创建维修记录失败: {type(e).__name__} - {str(e)}",
                "traceback": error_traceback
            }
    
    @staticmethod
    async def update_repair_record(
        record_id: int,
        record_data: DeviceRepairRecordUpdate,
        current_user: User
    ) -> Dict[str, Any]:
        """
        更新维修记录
        
        Args:
            record_id: 维修记录ID
            record_data: 维修记录更新数据
            current_user: 当前用户
            
        Returns:
            Dict[str, Any]: 包含结果状态和数据的字典
        """
        try:
            # 验证记录ID
            if record_id <= 0:
                return {
                    "success": False,
                    "error_type": "validation",
                    "message": f"无效的维修记录ID: {record_id}"
                }
            
            # 获取维修记录
            repair_record = await DeviceRepairRecord.get_or_none(id=record_id)
            if not repair_record:
                return {
                    "success": False,
                    "error_type": "not_found",
                    "message": f"维修记录不存在 (ID: {record_id})"
                }
            
            # 验证更新数据
            update_data = record_data.dict(exclude_unset=True)
            if not update_data:
                return {
                    "success": False,
                    "error_type": "validation",
                    "message": "未提供任何更新数据"
                }
            
            validation_errors = DeviceRepairRecordService._validate_update_data(update_data)
            if validation_errors:
                return {
                    "success": False,
                    "error_type": "validation",
                    "message": "数据验证失败: " + "; ".join(validation_errors),
                    "details": validation_errors
                }
            
            # 记录更新前的状态
            old_status = repair_record.repair_status
            
            # 更新字段
            for field, value in update_data.items():
                setattr(repair_record, field, value)
            
            await repair_record.save()
            
            logger.info(f"维修记录更新成功: record_id={record_id}, old_status={old_status}, new_status={repair_record.repair_status}, user={current_user.username}, updated_fields={list(update_data.keys())}")
            
            return {
                "success": True,
                "message": "维修记录更新成功"
            }
            
        except Exception as e:
            logger.error(f"更新维修记录失败: {str(e)}")
            return {
                "success": False,
                "error_type": "database",
                "message": f"更新维修记录失败: {type(e).__name__} - {str(e)}"
            }
    
    @staticmethod
    async def delete_repair_record(record_id: int, current_user: User) -> Dict[str, Any]:
        """
        删除维修记录
        
        Args:
            record_id: 维修记录ID
            current_user: 当前用户
            
        Returns:
            Dict[str, Any]: 包含结果状态和数据的字典
        """
        try:
            # 验证记录ID
            if record_id <= 0:
                return {
                    "success": False,
                    "error_type": "validation",
                    "message": f"无效的维修记录ID: {record_id}"
                }
            
            # 获取维修记录
            repair_record = await DeviceRepairRecord.get_or_none(id=record_id)
            if not repair_record:
                return {
                    "success": False,
                    "error_type": "not_found",
                    "message": f"维修记录不存在 (ID: {record_id})"
                }
            
            # 删除记录
            await repair_record.delete()
            
            logger.info(f"维修记录删除成功: record_id={record_id}, user={current_user.username}")
            
            return {
                "success": True,
                "message": "维修记录删除成功"
            }
            
        except Exception as e:
            logger.error(f"删除维修记录失败: {str(e)}")
            return {
                "success": False,
                "error_type": "database",
                "message": f"删除维修记录失败: {type(e).__name__} - {str(e)}"
            }
    
    @staticmethod
    async def get_repair_record(record_id: int) -> Dict[str, Any]:
        """
        获取维修记录详情
        
        Args:
            record_id: 维修记录ID
            
        Returns:
            Dict[str, Any]: 包含结果状态和数据的字典
        """
        try:
            # 验证记录ID
            if record_id <= 0:
                return {
                    "success": False,
                    "error_type": "validation",
                    "message": f"无效的维修记录ID: {record_id}"
                }
            
            # 获取维修记录
            repair_record = await DeviceRepairRecord.get_or_none(id=record_id)
            if not repair_record:
                return {
                    "success": False,
                    "error_type": "not_found",
                    "message": f"维修记录不存在 (ID: {record_id})"
                }
            
            return {
                "success": True,
                "data": repair_record,
                "message": "获取维修记录成功"
            }
            
        except Exception as e:
            logger.error(f"获取维修记录失败: {str(e)}")
            return {
                "success": False,
                "error_type": "database",
                "message": f"获取维修记录失败: {type(e).__name__} - {str(e)}"
            }