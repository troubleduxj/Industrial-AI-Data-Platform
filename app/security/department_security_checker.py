"""
部门权限隔离安全检查器
实现部门环境下的安全检查和数据隔离验证
"""

import logging
from typing import Optional, Dict, Any, List, Set
from datetime import datetime, timedelta
from collections import defaultdict

from app.services.department_permission_service import department_permission_service
from app.models.admin import User, Dept
from app.core.database import get_db

logger = logging.getLogger(__name__)


class DepartmentSecurityChecker:
    """部门权限隔离安全检查器"""
    
    def __init__(self):
        self.department_service = department_permission_service
        self.security_violations = defaultdict(list)
        self.access_patterns = defaultdict(dict)
    
    async def validate_department_isolation(
        self, 
        user: User, 
        requested_department_ids: List[int],
        operation: str = "read"
    ) -> Dict[str, Any]:
        """
        验证部门隔离完整性
        
        Args:
            user: 当前用户
            requested_department_ids: 请求访问的部门ID列表
            operation: 操作类型
            
        Returns:
            Dict: 验证结果
        """
        try:
            # 超级用户跳过隔离检查
            if user.is_superuser:
                return {
                    "valid": True,
                    "reason": "super_user_bypass",
                    "message": "超级用户跳过部门隔离检查",
                    "violations": []
                }
            
            violations = []
            
            # 获取用户可访问的部门
            accessible_departments = await self.department_service.get_accessible_departments(user.id)
            accessible_dept_ids = {dept.get('id') for dept in accessible_departments if dept.get('id')}
            
            # 检查是否有越权访问
            unauthorized_depts = set(requested_department_ids) - accessible_dept_ids
            if unauthorized_depts:
                violations.append({
                    "type": "unauthorized_department_access",
                    "message": f"用户尝试访问未授权的部门: {list(unauthorized_depts)}",
                    "severity": "high",
                    "department_ids": list(unauthorized_depts)
                })
            
            # 检查跨部门访问权限
            if len(set(requested_department_ids)) > 1:
                scope_info = await self.department_service.get_user_department_scope(user.id)
                if not scope_info.get("can_cross_department", False):
                    violations.append({
                        "type": "unauthorized_cross_department_access",
                        "message": "用户没有跨部门访问权限但尝试访问多个部门",
                        "severity": "high",
                        "department_ids": requested_department_ids
                    })
            
            # 检查操作权限
            scope_info = await self.department_service.get_user_department_scope(user.id)
            if operation == "write" and not scope_info.get("can_modify", False):
                violations.append({
                    "type": "unauthorized_write_operation",
                    "message": "用户没有写入权限但尝试执行写入操作",
                    "severity": "medium",
                    "operation": operation
                })
            
            if operation == "delete" and not scope_info.get("can_delete", False):
                violations.append({
                    "type": "unauthorized_delete_operation",
                    "message": "用户没有删除权限但尝试执行删除操作",
                    "severity": "high",
                    "operation": operation
                })
            
            # 记录安全违规
            if violations:
                await self._record_security_violation(user.id, violations)
            
            return {
                "valid": len(violations) == 0,
                "reason": "department_isolation_check",
                "message": "部门隔离检查完成" if not violations else f"发现{len(violations)}个安全违规",
                "violations": violations
            }
            
        except Exception as e:
            logger.error(f"部门隔离验证失败: error={str(e)}")
            return {
                "valid": False,
                "reason": "validation_error",
                "message": f"隔离验证过程中发生错误: {str(e)}",
                "violations": [{
                    "type": "system_error",
                    "message": str(e),
                    "severity": "critical"
                }]
            }
    
    async def check_data_leakage_risk(
        self, 
        user: User, 
        query_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        检查数据泄露风险
        
        Args:
            user: 当前用户
            query_conditions: 查询条件
            
        Returns:
            Dict: 风险评估结果
        """
        try:
            risks = []
            risk_level = "low"
            
            # 检查是否包含敏感字段查询
            sensitive_fields = ["password", "token", "secret", "key", "private"]
            for field in query_conditions.keys():
                if any(sensitive in field.lower() for sensitive in sensitive_fields):
                    risks.append({
                        "type": "sensitive_field_query",
                        "message": f"查询包含敏感字段: {field}",
                        "severity": "high",
                        "field": field
                    })
                    risk_level = "high"
            
            # 检查是否有大范围数据查询
            if not query_conditions.get("department_id") and not user.is_superuser:
                risks.append({
                    "type": "unrestricted_department_query",
                    "message": "查询未限制部门范围，可能导致数据泄露",
                    "severity": "medium"
                })
                if risk_level == "low":
                    risk_level = "medium"
            
            # 检查查询频率
            access_pattern = await self._check_access_pattern(user.id)
            if access_pattern.get("suspicious", False):
                risks.append({
                    "type": "suspicious_access_pattern",
                    "message": "检测到异常访问模式",
                    "severity": "medium",
                    "pattern": access_pattern
                })
                if risk_level == "low":
                    risk_level = "medium"
            
            return {
                "safe": len(risks) == 0,
                "risk_level": risk_level,
                "message": "数据泄露风险检查完成",
                "risks": risks,
                "recommendations": self._get_security_recommendations(risks)
            }
            
        except Exception as e:
            logger.error(f"数据泄露风险检查失败: error={str(e)}")
            return {
                "safe": False,
                "risk_level": "critical",
                "message": f"风险检查过程中发生错误: {str(e)}",
                "risks": [{
                    "type": "system_error",
                    "message": str(e),
                    "severity": "critical"
                }]
            }
    
    async def validate_department_hierarchy(
        self, 
        user: User, 
        parent_department_id: int, 
        child_department_id: int
    ) -> Dict[str, Any]:
        """
        验证部门层级关系的访问权限
        
        Args:
            user: 当前用户
            parent_department_id: 父部门ID
            child_department_id: 子部门ID
            
        Returns:
            Dict: 验证结果
        """
        try:
            # 超级用户拥有所有权限
            if user.is_superuser:
                return {
                    "valid": True,
                    "reason": "super_user",
                    "message": "超级用户拥有部门层级访问权限"
                }
            
            # 检查用户是否有权限访问父部门
            parent_access = await self.department_service.check_department_access_permission(
                user.id, parent_department_id
            )
            
            # 检查用户是否有权限访问子部门
            child_access = await self.department_service.check_department_access_permission(
                user.id, child_department_id
            )
            
            if not parent_access:
                return {
                    "valid": False,
                    "reason": "parent_department_access_denied",
                    "message": f"用户无权限访问父部门ID为{parent_department_id}的数据"
                }
            
            if not child_access:
                return {
                    "valid": False,
                    "reason": "child_department_access_denied",
                    "message": f"用户无权限访问子部门ID为{child_department_id}的数据"
                }
            
            # 验证部门层级关系
            is_valid_hierarchy = await self._validate_department_relationship(
                parent_department_id, child_department_id
            )
            
            if not is_valid_hierarchy:
                return {
                    "valid": False,
                    "reason": "invalid_department_hierarchy",
                    "message": "部门层级关系无效"
                }
            
            return {
                "valid": True,
                "reason": "hierarchy_access_granted",
                "message": "部门层级访问权限验证通过"
            }
            
        except Exception as e:
            logger.error(f"部门层级关系验证失败: error={str(e)}")
            return {
                "valid": False,
                "reason": "validation_error",
                "message": f"层级关系验证过程中发生错误: {str(e)}"
            }
    
    async def audit_department_access(
        self, 
        user: User, 
        operation: str, 
        resource_type: str,
        resource_ids: List[int],
        department_ids: List[int]
    ) -> Dict[str, Any]:
        """
        审计部门访问操作
        
        Args:
            user: 当前用户
            operation: 操作类型
            resource_type: 资源类型
            resource_ids: 资源ID列表
            department_ids: 涉及的部门ID列表
            
        Returns:
            Dict: 审计结果
        """
        try:
            audit_record = {
                "user_id": user.id,
                "username": user.username,
                "operation": operation,
                "resource_type": resource_type,
                "resource_ids": resource_ids,
                "department_ids": department_ids,
                "timestamp": datetime.now(),
                "ip_address": None,  # 需要从请求中获取
                "user_agent": None   # 需要从请求中获取
            }
            
            # 执行安全检查
            security_result = await self.validate_department_isolation(
                user, department_ids, operation
            )
            
            audit_record["security_check"] = security_result
            audit_record["violations"] = security_result.get("violations", [])
            
            # 记录审计日志
            await self._record_audit_log(audit_record)
            
            # 更新访问模式
            await self._update_access_pattern(user.id, operation, resource_type)
            
            return {
                "success": True,
                "message": "部门访问审计完成",
                "audit_id": audit_record.get("id"),
                "security_status": "safe" if security_result.get("valid", False) else "violation"
            }
            
        except Exception as e:
            logger.error(f"部门访问审计失败: error={str(e)}")
            return {
                "success": False,
                "message": f"审计过程中发生错误: {str(e)}"
            }
    
    async def _record_security_violation(
        self, 
        user_id: int, 
        violations: List[Dict[str, Any]]
    ):
        """记录安全违规"""
        try:
            for violation in violations:
                violation_record = {
                    "user_id": user_id,
                    "violation_type": violation.get("type"),
                    "message": violation.get("message"),
                    "severity": violation.get("severity"),
                    "timestamp": datetime.now(),
                    "details": violation
                }
                
                # 存储到违规记录中
                self.security_violations[user_id].append(violation_record)
                
                # 如果是高危违规，立即记录日志
                if violation.get("severity") == "high":
                    logger.warning(f"高危安全违规: user_id={user_id}, type={violation.get('type')}, message={violation.get('message')}")
                
        except Exception as e:
            logger.error(f"记录安全违规失败: error={str(e)}")
    
    async def _check_access_pattern(self, user_id: int) -> Dict[str, Any]:
        """检查用户访问模式"""
        try:
            pattern = self.access_patterns.get(user_id, {})
            current_time = datetime.now()
            
            # 检查访问频率
            recent_accesses = pattern.get("recent_accesses", [])
            recent_accesses = [
                access for access in recent_accesses 
                if current_time - access < timedelta(minutes=10)
            ]
            
            suspicious = False
            if len(recent_accesses) > 100:  # 10分钟内超过100次访问
                suspicious = True
            
            return {
                "recent_access_count": len(recent_accesses),
                "suspicious": suspicious,
                "last_access": pattern.get("last_access"),
                "total_accesses": pattern.get("total_accesses", 0)
            }
            
        except Exception as e:
            logger.error(f"检查访问模式失败: error={str(e)}")
            return {"suspicious": False}
    
    async def _update_access_pattern(
        self, 
        user_id: int, 
        operation: str, 
        resource_type: str
    ):
        """更新用户访问模式"""
        try:
            current_time = datetime.now()
            
            if user_id not in self.access_patterns:
                self.access_patterns[user_id] = {
                    "recent_accesses": [],
                    "total_accesses": 0,
                    "operations": defaultdict(int),
                    "resource_types": defaultdict(int)
                }
            
            pattern = self.access_patterns[user_id]
            pattern["recent_accesses"].append(current_time)
            pattern["total_accesses"] += 1
            pattern["operations"][operation] += 1
            pattern["resource_types"][resource_type] += 1
            pattern["last_access"] = current_time
            
            # 清理过期的访问记录
            pattern["recent_accesses"] = [
                access for access in pattern["recent_accesses"]
                if current_time - access < timedelta(hours=1)
            ]
            
        except Exception as e:
            logger.error(f"更新访问模式失败: error={str(e)}")
    
    async def _validate_department_relationship(
        self, 
        parent_id: int, 
        child_id: int
    ) -> bool:
        """验证部门层级关系"""
        try:
            # 查询子部门是否真的是父部门的子部门
            child_dept = await Dept.get_or_none(id=child_id)
            if not child_dept:
                return False
            
            # 检查直接父子关系
            if child_dept.parent_id == parent_id:
                return True
            
            # 检查间接父子关系（递归查找）
            current_parent_id = child_dept.parent_id
            while current_parent_id:
                if current_parent_id == parent_id:
                    return True
                parent_dept = await Dept.get_or_none(id=current_parent_id)
                if not parent_dept:
                    break
                current_parent_id = parent_dept.parent_id
            
            return False
            
        except Exception as e:
            logger.error(f"验证部门层级关系失败: error={str(e)}")
            return False
    
    async def _record_audit_log(self, audit_record: Dict[str, Any]):
        """记录审计日志"""
        try:
            # 这里应该将审计记录存储到数据库或日志系统
            logger.info(f"部门访问审计: {audit_record}")
            
        except Exception as e:
            logger.error(f"记录审计日志失败: error={str(e)}")
    
    def _get_security_recommendations(
        self, 
        risks: List[Dict[str, Any]]
    ) -> List[str]:
        """获取安全建议"""
        recommendations = []
        
        for risk in risks:
            risk_type = risk.get("type")
            
            if risk_type == "sensitive_field_query":
                recommendations.append("避免在查询中包含敏感字段，使用字段映射或视图")
            elif risk_type == "unrestricted_department_query":
                recommendations.append("在查询中明确指定部门范围，避免全局查询")
            elif risk_type == "suspicious_access_pattern":
                recommendations.append("检查访问频率，考虑实施访问限流")
        
        return list(set(recommendations))  # 去重
    
    async def get_security_summary(self, user_id: int) -> Dict[str, Any]:
        """获取用户安全摘要"""
        try:
            violations = self.security_violations.get(user_id, [])
            pattern = self.access_patterns.get(user_id, {})
            
            # 统计违规类型
            violation_types = defaultdict(int)
            for violation in violations:
                violation_types[violation.get("violation_type")] += 1
            
            return {
                "user_id": user_id,
                "total_violations": len(violations),
                "violation_types": dict(violation_types),
                "access_pattern": pattern,
                "last_violation": violations[-1] if violations else None,
                "security_score": self._calculate_security_score(violations, pattern)
            }
            
        except Exception as e:
            logger.error(f"获取安全摘要失败: error={str(e)}")
            return {"error": str(e)}
    
    def _calculate_security_score(
        self, 
        violations: List[Dict[str, Any]], 
        pattern: Dict[str, Any]
    ) -> int:
        """计算安全评分 (0-100)"""
        score = 100
        
        # 根据违规数量扣分
        score -= len(violations) * 5
        
        # 根据违规严重程度扣分
        for violation in violations:
            severity = violation.get("severity", "low")
            if severity == "critical":
                score -= 20
            elif severity == "high":
                score -= 10
            elif severity == "medium":
                score -= 5
        
        # 根据访问模式扣分
        if pattern.get("suspicious", False):
            score -= 15
        
        return max(0, score)


# 创建全局实例
department_security_checker = DepartmentSecurityChecker()