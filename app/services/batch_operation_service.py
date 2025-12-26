"""
批量操作权限控制服务
"""
import asyncio
from typing import List, Dict, Any, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass
from app.core.unified_logger import get_logger

logger = get_logger(__name__)
from app.models.admin import User
from app.services.audit_service import audit_service


class BatchOperationType(Enum):
    """批量操作类型"""
    DELETE = "DELETE"
    UPDATE = "UPDATE"
    CREATE = "CREATE"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    ACTIVATE = "ACTIVATE"
    DEACTIVATE = "DEACTIVATE"


class ProtectionLevel(Enum):
    """保护级别"""
    NONE = "NONE"           # 无保护
    LOW = "LOW"             # 低保护
    MEDIUM = "MEDIUM"       # 中保护
    HIGH = "HIGH"           # 高保护
    CRITICAL = "CRITICAL"   # 关键保护


@dataclass
class BatchOperationRule:
    """批量操作规则"""
    resource_type: str
    operation_type: BatchOperationType
    max_items: int
    protection_level: ProtectionLevel
    required_permissions: List[str]
    protected_conditions: List[Dict[str, Any]]
    approval_required: bool = False
    audit_required: bool = True


@dataclass
class BatchOperationRequest:
    """批量操作请求"""
    user_id: int
    resource_type: str
    operation_type: BatchOperationType
    item_ids: List[Any]
    additional_data: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None


@dataclass
class BatchOperationResult:
    """批量操作结果"""
    success: bool
    allowed_items: List[Any]
    denied_items: List[Any]
    protected_items: List[Any]
    total_requested: int
    total_allowed: int
    total_denied: int
    error_message: Optional[str] = None
    warnings: List[str] = None


class BatchOperationService:
    """批量操作权限控制服务"""
    
    def __init__(self):
        # 默认批量操作规则
        self.default_rules = {
            # 用户管理
            "users": {
                BatchOperationType.DELETE: BatchOperationRule(
                    resource_type="users",
                    operation_type=BatchOperationType.DELETE,
                    max_items=50,
                    protection_level=ProtectionLevel.HIGH,
                    required_permissions=["DELETE /api/v2/users", "batch_delete_users"],
                    protected_conditions=[
                        {"field": "is_superuser", "value": True},
                        {"field": "is_active", "value": True, "role": "admin"}
                    ],
                    approval_required=True,
                    audit_required=True
                ),
                BatchOperationType.UPDATE: BatchOperationRule(
                    resource_type="users",
                    operation_type=BatchOperationType.UPDATE,
                    max_items=100,
                    protection_level=ProtectionLevel.MEDIUM,
                    required_permissions=["PUT /api/v2/users", "batch_update_users"],
                    protected_conditions=[
                        {"field": "is_superuser", "value": True}
                    ]
                ),
                BatchOperationType.DEACTIVATE: BatchOperationRule(
                    resource_type="users",
                    operation_type=BatchOperationType.DEACTIVATE,
                    max_items=30,
                    protection_level=ProtectionLevel.HIGH,
                    required_permissions=["PUT /api/v2/users", "batch_deactivate_users"],
                    protected_conditions=[
                        {"field": "is_superuser", "value": True},
                        {"field": "id", "operator": "current_user"}
                    ],
                    approval_required=True
                )
            },
            
            # 角色管理
            "roles": {
                BatchOperationType.DELETE: BatchOperationRule(
                    resource_type="roles",
                    operation_type=BatchOperationType.DELETE,
                    max_items=20,
                    protection_level=ProtectionLevel.CRITICAL,
                    required_permissions=["DELETE /api/v2/roles", "batch_delete_roles"],
                    protected_conditions=[
                        {"field": "is_system_role", "value": True},
                        {"field": "user_count", "operator": ">", "value": 0}
                    ],
                    approval_required=True
                )
            },
            
            # 设备管理
            "devices": {
                BatchOperationType.DELETE: BatchOperationRule(
                    resource_type="devices",
                    operation_type=BatchOperationType.DELETE,
                    max_items=200,
                    protection_level=ProtectionLevel.MEDIUM,
                    required_permissions=["DELETE /api/v2/devices", "batch_delete_devices"],
                    protected_conditions=[
                        {"field": "status", "value": "online"},
                        {"field": "is_critical", "value": True}
                    ]
                ),
                BatchOperationType.UPDATE: BatchOperationRule(
                    resource_type="devices",
                    operation_type=BatchOperationType.UPDATE,
                    max_items=500,
                    protection_level=ProtectionLevel.LOW,
                    required_permissions=["PUT /api/v2/devices", "batch_update_devices"],
                    protected_conditions=[]
                )
            },
            
            # 维修记录
            "repair_records": {
                BatchOperationType.DELETE: BatchOperationRule(
                    resource_type="repair_records",
                    operation_type=BatchOperationType.DELETE,
                    max_items=100,
                    protection_level=ProtectionLevel.MEDIUM,
                    required_permissions=["DELETE /api/v2/device/maintenance", "batch_delete_repair_records"],
                    protected_conditions=[
                        {"field": "status", "value": "completed"},
                        {"field": "created_days_ago", "operator": "<", "value": 30}
                    ]
                )
            }
        }
        
        # 系统关键数据保护列表
        self.critical_resources = {
            "users": ["admin", "system"],
            "roles": ["超级管理员", "系统管理员"],
            "devices": [],  # 通过条件判断
            "repair_records": []
        }
    
    async def check_batch_operation_permission(
        self,
        request: BatchOperationRequest,
        user: Admin,
        db: Session = None
    ) -> BatchOperationResult:
        """检查批量操作权限"""
        try:
            if not db:
                db = next(get_db())
            
            logger.info(f"检查批量操作权限: 用户{user.username}, 资源{request.resource_type}, 操作{request.operation_type.value}")
            
            # 获取操作规则
            rule = self._get_operation_rule(request.resource_type, request.operation_type)
            if not rule:
                return BatchOperationResult(
                    success=False,
                    allowed_items=[],
                    denied_items=request.item_ids,
                    protected_items=[],
                    total_requested=len(request.item_ids),
                    total_allowed=0,
                    total_denied=len(request.item_ids),
                    error_message=f"未找到资源类型 {request.resource_type} 的 {request.operation_type.value} 操作规则"
                )
            
            # 检查基础权限
            permission_check = await self._check_basic_permissions(user, rule)
            if not permission_check:
                return BatchOperationResult(
                    success=False,
                    allowed_items=[],
                    denied_items=request.item_ids,
                    protected_items=[],
                    total_requested=len(request.item_ids),
                    total_allowed=0,
                    total_denied=len(request.item_ids),
                    error_message="用户缺少执行此批量操作的基础权限"
                )
            
            # 检查数量限制
            if len(request.item_ids) > rule.max_items:
                return BatchOperationResult(
                    success=False,
                    allowed_items=[],
                    denied_items=request.item_ids,
                    protected_items=[],
                    total_requested=len(request.item_ids),
                    total_allowed=0,
                    total_denied=len(request.item_ids),
                    error_message=f"批量操作数量超出限制，最大允许 {rule.max_items} 项，请求 {len(request.item_ids)} 项"
                )
            
            # 检查受保护项目
            allowed_items, denied_items, protected_items = await self._filter_protected_items(
                request, rule, user, db
            )
            
            # 记录审计日志
            if rule.audit_required:
                await self._log_batch_operation_attempt(request, user, rule, allowed_items, denied_items, protected_items)
            
            result = BatchOperationResult(
                success=len(allowed_items) > 0,
                allowed_items=allowed_items,
                denied_items=denied_items,
                protected_items=protected_items,
                total_requested=len(request.item_ids),
                total_allowed=len(allowed_items),
                total_denied=len(denied_items) + len(protected_items)
            )
            
            # 添加警告信息
            warnings = []
            if protected_items:
                warnings.append(f"有 {len(protected_items)} 项受保护项目被排除")
            if denied_items:
                warnings.append(f"有 {len(denied_items)} 项因权限不足被拒绝")
            result.warnings = warnings
            
            return result
            
        except Exception as e:
            logger.error(f"批量操作权限检查失败: {e}")
            return BatchOperationResult(
                success=False,
                allowed_items=[],
                denied_items=request.item_ids,
                protected_items=[],
                total_requested=len(request.item_ids),
                total_allowed=0,
                total_denied=len(request.item_ids),
                error_message=f"权限检查过程中发生错误: {str(e)}"
            )
        finally:
            if db:
                db.close()
    
    def _get_operation_rule(self, resource_type: str, operation_type: BatchOperationType) -> Optional[BatchOperationRule]:
        """获取操作规则"""
        resource_rules = self.default_rules.get(resource_type)
        if not resource_rules:
            return None
        return resource_rules.get(operation_type)
    
    async def _check_basic_permissions(self, user: Admin, rule: BatchOperationRule) -> bool:
        """检查基础权限"""
        # 超级用户拥有所有权限
        if user.is_superuser:
            return True
        
        # 检查用户是否具有所需权限
        from app.services.permission_service import permission_service
        
        for permission in rule.required_permissions:
            has_permission = await permission_service.check_user_permission(
                user_id=user.id,
                permission_code=permission
            )
            if not has_permission:
                logger.warning(f"用户 {user.username} 缺少权限: {permission}")
                return False
        
        return True
    
    async def _filter_protected_items(
        self,
        request: BatchOperationRequest,
        rule: BatchOperationRule,
        user: Admin,
        db: Session
    ) -> Tuple[List[Any], List[Any], List[Any]]:
        """过滤受保护的项目"""
        allowed_items = []
        denied_items = []
        protected_items = []
        
        # 获取资源数据
        resource_data = await self._get_resource_data(request.resource_type, request.item_ids, db)
        
        for item_id in request.item_ids:
            item_data = resource_data.get(item_id)
            if not item_data:
                denied_items.append(item_id)
                continue
            
            # 检查是否为受保护项目
            is_protected = await self._is_protected_item(
                request.resource_type, item_data, rule.protected_conditions, user
            )
            
            if is_protected:
                protected_items.append(item_id)
            else:
                allowed_items.append(item_id)
        
        return allowed_items, denied_items, protected_items
    
    async def _get_resource_data(self, resource_type: str, item_ids: List[Any], db: Session) -> Dict[Any, Dict[str, Any]]:
        """获取资源数据"""
        resource_data = {}
        
        try:
            if resource_type == "users":
                from app.models.admin import Admin
                users = db.query(Admin).filter(Admin.id.in_(item_ids)).all()
                for user in users:
                    resource_data[user.id] = {
                        "id": user.id,
                        "username": user.username,
                        "is_superuser": user.is_superuser,
                        "is_active": user.is_active,
                        "email": user.email
                    }
            
            elif resource_type == "roles":
                from app.models.admin import Role
                roles = db.query(Role).filter(Role.id.in_(item_ids)).all()
                for role in roles:
                    # 计算使用此角色的用户数量
                    user_count = db.query(Admin).filter(Admin.role_id == role.id).count()
                    resource_data[role.id] = {
                        "id": role.id,
                        "name": role.name,
                        "is_system_role": role.name in ["超级管理员", "系统管理员"],
                        "user_count": user_count
                    }
            
            elif resource_type == "devices":
                # 这里需要根据实际的设备模型来实现
                # 暂时使用模拟数据
                for item_id in item_ids:
                    resource_data[item_id] = {
                        "id": item_id,
                        "status": "offline",  # 模拟状态
                        "is_critical": False  # 模拟关键设备标识
                    }
            
            elif resource_type == "repair_records":
                # 这里需要根据实际的维修记录模型来实现
                # 暂时使用模拟数据
                from datetime import datetime, timedelta
                for item_id in item_ids:
                    resource_data[item_id] = {
                        "id": item_id,
                        "status": "pending",  # 模拟状态
                        "created_days_ago": 10  # 模拟创建天数
                    }
            
        except Exception as e:
            logger.error(f"获取资源数据失败: {e}")
        
        return resource_data
    
    async def _is_protected_item(
        self,
        resource_type: str,
        item_data: Dict[str, Any],
        protected_conditions: List[Dict[str, Any]],
        user: Admin
    ) -> bool:
        """检查是否为受保护项目"""
        # 检查系统关键数据
        critical_items = self.critical_resources.get(resource_type, [])
        if resource_type == "users" and item_data.get("username") in critical_items:
            return True
        elif resource_type == "roles" and item_data.get("name") in critical_items:
            return True
        
        # 检查保护条件
        for condition in protected_conditions:
            if await self._check_protection_condition(condition, item_data, user):
                return True
        
        return False
    
    async def _check_protection_condition(
        self,
        condition: Dict[str, Any],
        item_data: Dict[str, Any],
        user: Admin
    ) -> bool:
        """检查保护条件"""
        field = condition.get("field")
        operator = condition.get("operator", "=")
        value = condition.get("value")
        
        if not field:
            return False
        
        # 特殊操作符处理
        if operator == "current_user":
            return item_data.get("id") == user.id
        
        item_value = item_data.get(field)
        
        if operator == "=":
            return item_value == value
        elif operator == "!=":
            return item_value != value
        elif operator == ">":
            return item_value > value
        elif operator == "<":
            return item_value < value
        elif operator == ">=":
            return item_value >= value
        elif operator == "<=":
            return item_value <= value
        elif operator == "in":
            return item_value in value if isinstance(value, (list, tuple)) else False
        elif operator == "not_in":
            return item_value not in value if isinstance(value, (list, tuple)) else True
        
        return False
    
    async def _log_batch_operation_attempt(
        self,
        request: BatchOperationRequest,
        user: Admin,
        rule: BatchOperationRule,
        allowed_items: List[Any],
        denied_items: List[Any],
        protected_items: List[Any]
    ):
        """记录批量操作尝试日志"""
        try:
            # 创建模拟请求对象用于审计
            class MockRequest:
                def __init__(self):
                    self.method = request.operation_type.value
                    self.url = MockURL(f"/api/v2/{request.resource_type}/batch")
                    self.client = MockClient("127.0.0.1")
                    self.headers = {"user-agent": "batch-operation-service"}
                    self.query_params = {}
                
                class MockURL:
                    def __init__(self, path):
                        self.path = path
                
                class MockClient:
                    def __init__(self, host):
                        self.host = host
            
            mock_request = MockRequest()
            
            # 记录批量操作日志
            await audit_service.log_batch_operation(
                user_id=user.id,
                username=user.username,
                operation_type=request.operation_type.value,
                affected_count=len(allowed_items),
                resource_type=request.resource_type.upper(),
                request=mock_request,
                success=len(allowed_items) > 0,
                extra_data={
                    "total_requested": len(request.item_ids),
                    "allowed_count": len(allowed_items),
                    "denied_count": len(denied_items),
                    "protected_count": len(protected_items),
                    "protection_level": rule.protection_level.value,
                    "reason": request.reason
                }
            )
            
            # 如果有受保护项目，创建安全事件
            if protected_items:
                await audit_service.create_security_event(
                    event_type="PROTECTED_ITEM_ACCESS",
                    event_level="MEDIUM",
                    event_title="尝试操作受保护项目",
                    event_description=f"用户 {user.username} 尝试对 {len(protected_items)} 个受保护的{request.resource_type}执行{request.operation_type.value}操作",
                    user_id=user.id,
                    username=user.username,
                    request=mock_request,
                    detection_rule="PROTECTED_ITEM_FILTER",
                    threat_score=30,
                    extra_data={
                        "resource_type": request.resource_type,
                        "operation_type": request.operation_type.value,
                        "protected_items": protected_items
                    }
                )
            
        except Exception as e:
            logger.error(f"记录批量操作日志失败: {e}")
    
    def add_custom_rule(self, rule: BatchOperationRule):
        """添加自定义规则"""
        if rule.resource_type not in self.default_rules:
            self.default_rules[rule.resource_type] = {}
        
        self.default_rules[rule.resource_type][rule.operation_type] = rule
        logger.info(f"添加自定义批量操作规则: {rule.resource_type}.{rule.operation_type.value}")
    
    def get_operation_limits(self, resource_type: str) -> Dict[str, Any]:
        """获取操作限制信息"""
        limits = {}
        resource_rules = self.default_rules.get(resource_type, {})
        
        for operation_type, rule in resource_rules.items():
            limits[operation_type.value] = {
                "max_items": rule.max_items,
                "protection_level": rule.protection_level.value,
                "required_permissions": rule.required_permissions,
                "approval_required": rule.approval_required,
                "audit_required": rule.audit_required
            }
        
        return limits


# 全局批量操作服务实例
batch_operation_service = BatchOperationService()