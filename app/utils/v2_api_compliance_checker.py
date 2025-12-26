#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V2 API响应格式合规性验证器
检查所有系统管理V2 API的响应格式是否符合标准规范
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import httpx
from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.core.response_formatter_v2 import APIv2Response, APIv2ErrorResponse
from app.models.admin import User, Role, SysApiEndpoint, Menu, Dept, SysApiGroup, HttpAuditLog
from app.models.system import SysDictType, SysDictData


class ComplianceStatus(Enum):
    """合规性状态"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class ComplianceIssue:
    """合规性问题"""
    field: str
    expected: Any
    actual: Any
    severity: str  # "critical", "major", "minor"
    description: str


@dataclass
class EndpointComplianceResult:
    """端点合规性检查结果"""
    endpoint: str
    method: str
    status: ComplianceStatus
    http_status_code: Optional[int] = None
    response_format_compliant: bool = False
    status_code_compliant: bool = False
    required_fields_present: bool = False
    issues: List[ComplianceIssue] = None
    response_sample: Optional[Dict] = None
    execution_time_ms: Optional[float] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []


@dataclass
class ComplianceReport:
    """完整的合规性报告"""
    timestamp: str
    total_endpoints: int
    compliant_count: int
    non_compliant_count: int
    error_count: int
    skipped_count: int
    compliance_rate: float
    endpoints: List[EndpointComplianceResult]
    summary: Dict[str, Any]
    
    def __post_init__(self):
        if self.compliance_rate == 0 and self.total_endpoints > 0:
            self.compliance_rate = (self.compliant_count / self.total_endpoints) * 100


class V2APIComplianceChecker:
    """V2 API合规性检查器"""
    
    # 系统管理模块的V2 API端点
    SYSTEM_MANAGEMENT_ENDPOINTS = {
        # 用户管理
        "users": [
            ("GET", "/api/v2/users", "获取用户列表"),
            ("POST", "/api/v2/users", "创建用户"),
            ("GET", "/api/v2/users/{user_id}", "获取用户详情"),
            ("PUT", "/api/v2/users/{user_id}", "更新用户"),
            ("DELETE", "/api/v2/users/{user_id}", "删除用户"),
            ("DELETE", "/api/v2/users/batch", "批量删除用户"),
            ("GET", "/api/v2/users/{user_id}/roles", "获取用户角色"),
            ("GET", "/api/v2/users/{user_id}/permissions", "获取用户权限"),
        ],
        # 角色管理
        "roles": [
            ("GET", "/api/v2/roles", "获取角色列表"),
            ("POST", "/api/v2/roles", "创建角色"),
            ("GET", "/api/v2/roles/{role_id}", "获取角色详情"),
            ("PUT", "/api/v2/roles/{role_id}", "更新角色"),
            ("DELETE", "/api/v2/roles/{role_id}", "删除角色"),
            ("DELETE", "/api/v2/roles/batch", "批量删除角色"),
            ("GET", "/api/v2/roles/{role_id}/permissions", "获取角色权限"),
            ("PUT", "/api/v2/roles/{role_id}/permissions", "设置角色权限"),
        ],
        # 菜单管理
        "menus": [
            ("GET", "/api/v2/menus", "获取菜单列表"),
            ("POST", "/api/v2/menus", "创建菜单"),
            ("GET", "/api/v2/menus/{menu_id}", "获取菜单详情"),
            ("PUT", "/api/v2/menus/{menu_id}", "更新菜单"),
            ("DELETE", "/api/v2/menus/{menu_id}", "删除菜单"),
            ("DELETE", "/api/v2/menus/batch", "批量删除菜单"),
            ("GET", "/api/v2/menus/tree", "获取菜单树"),
        ],
        # 部门管理
        "departments": [
            ("GET", "/api/v2/departments", "获取部门列表"),
            ("POST", "/api/v2/departments", "创建部门"),
            ("GET", "/api/v2/departments/{dept_id}", "获取部门详情"),
            ("PUT", "/api/v2/departments/{dept_id}", "更新部门"),
            ("DELETE", "/api/v2/departments/{dept_id}", "删除部门"),
            ("DELETE", "/api/v2/departments/batch", "批量删除部门"),
        ],
        # API管理
        "apis": [
            ("GET", "/api/v2/apis", "获取API列表"),
            ("POST", "/api/v2/apis", "创建API"),
            ("GET", "/api/v2/apis/{api_id}", "获取API详情"),
            ("PUT", "/api/v2/apis/{api_id}", "更新API"),
            ("DELETE", "/api/v2/apis/{api_id}", "删除API"),
            ("DELETE", "/api/v2/apis/batch", "批量删除API"),
        ],
        # API分组管理
        "api-groups": [
            ("GET", "/api/v2/api-groups", "获取API分组列表"),
            ("POST", "/api/v2/api-groups", "创建API分组"),
            ("GET", "/api/v2/api-groups/{group_id}", "获取API分组详情"),
            ("PUT", "/api/v2/api-groups/{group_id}", "更新API分组"),
            ("DELETE", "/api/v2/api-groups/{group_id}", "删除API分组"),
            ("DELETE", "/api/v2/api-groups/batch", "批量删除API分组"),
        ],
        # 字典类型管理
        "dict-types": [
            ("GET", "/api/v2/dict-types", "获取字典类型列表"),
            ("POST", "/api/v2/dict-types", "创建字典类型"),
            ("GET", "/api/v2/dict-types/{type_id}", "获取字典类型详情"),
            ("PUT", "/api/v2/dict-types/{type_id}", "更新字典类型"),
            ("DELETE", "/api/v2/dict-types/{type_id}", "删除字典类型"),
            ("DELETE", "/api/v2/dict-types/batch", "批量删除字典类型"),
        ],
        # 字典数据管理
        "dict-data": [
            ("GET", "/api/v2/dict-data", "获取字典数据列表"),
            ("POST", "/api/v2/dict-data", "创建字典数据"),
            ("GET", "/api/v2/dict-data/{data_id}", "获取字典数据详情"),
            ("PUT", "/api/v2/dict-data/{data_id}", "更新字典数据"),
            ("DELETE", "/api/v2/dict-data/{data_id}", "删除字典数据"),
            ("DELETE", "/api/v2/dict-data/batch", "批量删除字典数据"),
        ],
        # 系统参数管理 (暂时注释，模型不存在)
        # "system-params": [
        #     ("GET", "/api/v2/system-params", "获取系统参数列表"),
        #     ("POST", "/api/v2/system-params", "创建系统参数"),
        #     ("GET", "/api/v2/system-params/{param_id}", "获取系统参数详情"),
        #     ("PUT", "/api/v2/system-params/{param_id}", "更新系统参数"),
        #     ("DELETE", "/api/v2/system-params/{param_id}", "删除系统参数"),
        # ],
        # 审计日志管理
        "audit-logs": [
            ("GET", "/api/v2/audit-logs", "获取审计日志列表"),
            ("GET", "/api/v2/audit-logs/{log_id}", "获取审计日志详情"),
        ]
    }
    
    # 标准HTTP状态码
    VALID_STATUS_CODES = {200, 201, 400, 401, 403, 404, 422, 500}
    
    # V2响应格式必需字段
    REQUIRED_SUCCESS_FIELDS = {"success", "code", "message", "data", "meta"}
    REQUIRED_ERROR_FIELDS = {"success", "code", "message", "error_type", "error", "meta"}
    REQUIRED_META_FIELDS = {"version", "timestamp", "request_id"}
    
    def __init__(self, base_url: str = "http://localhost:8001", auth_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.logger = logging.getLogger(__name__)
        
        # HTTP客户端配置
        self.client_config = {
            "timeout": 30.0,
            "follow_redirects": True
        }
        
        if auth_token:
            self.client_config["headers"] = {
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            }
    
    async def check_endpoint_compliance(
        self, 
        method: str, 
        endpoint: str, 
        description: str,
        test_data: Optional[Dict] = None
    ) -> EndpointComplianceResult:
        """检查单个端点的合规性"""
        start_time = datetime.now()
        
        try:
            # 构建完整URL
            url = f"{self.base_url}{endpoint}"
            
            # 替换路径参数为测试值
            if "{user_id}" in url:
                url = url.replace("{user_id}", "1")
            if "{role_id}" in url:
                url = url.replace("{role_id}", "1")
            if "{menu_id}" in url:
                url = url.replace("{menu_id}", "1")
            if "{dept_id}" in url:
                url = url.replace("{dept_id}", "1")
            if "{api_id}" in url:
                url = url.replace("{api_id}", "1")
            if "{group_id}" in url:
                url = url.replace("{group_id}", "1")
            if "{type_id}" in url:
                url = url.replace("{type_id}", "1")
            if "{data_id}" in url:
                url = url.replace("{data_id}", "1")
            if "{param_id}" in url:
                url = url.replace("{param_id}", "1")
            if "{log_id}" in url:
                url = url.replace("{log_id}", "1")
            
            # 发送HTTP请求
            async with httpx.AsyncClient(**self.client_config) as client:
                if method == "GET":
                    response = await client.get(url)
                elif method == "POST":
                    response = await client.post(url, json=test_data or {})
                elif method == "PUT":
                    response = await client.put(url, json=test_data or {})
                elif method == "DELETE":
                    if "batch" in endpoint:
                        # 对于批量删除，使用POST方法发送DELETE请求体
                        response = await client.request(
                            method="DELETE",
                            url=url,
                            json={"ids": [1]},
                            headers={"Content-Type": "application/json"}
                        )
                    else:
                        response = await client.delete(url)
                else:
                    return EndpointComplianceResult(
                        endpoint=endpoint,
                        method=method,
                        status=ComplianceStatus.SKIPPED,
                        issues=[ComplianceIssue(
                            field="method",
                            expected="GET/POST/PUT/DELETE",
                            actual=method,
                            severity="critical",
                            description=f"Unsupported HTTP method: {method}"
                        )]
                    )
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # 解析响应
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                return EndpointComplianceResult(
                    endpoint=endpoint,
                    method=method,
                    status=ComplianceStatus.ERROR,
                    http_status_code=response.status_code,
                    execution_time_ms=execution_time,
                    issues=[ComplianceIssue(
                        field="response_body",
                        expected="Valid JSON",
                        actual="Invalid JSON",
                        severity="critical",
                        description="Response body is not valid JSON"
                    )]
                )
            
            # 检查合规性
            issues = []
            
            # 1. 检查HTTP状态码
            status_code_compliant = response.status_code in self.VALID_STATUS_CODES
            if not status_code_compliant:
                issues.append(ComplianceIssue(
                    field="http_status_code",
                    expected=f"One of {self.VALID_STATUS_CODES}",
                    actual=response.status_code,
                    severity="major",
                    description=f"HTTP status code {response.status_code} is not in valid range"
                ))
            
            # 2. 检查响应格式
            response_format_compliant = True
            required_fields_present = True
            
            # 确定是成功还是错误响应
            is_success_response = response.status_code < 400
            
            if is_success_response:
                # 检查成功响应格式
                missing_fields = self.REQUIRED_SUCCESS_FIELDS - set(response_data.keys())
                if missing_fields:
                    required_fields_present = False
                    response_format_compliant = False
                    issues.append(ComplianceIssue(
                        field="required_fields",
                        expected=list(self.REQUIRED_SUCCESS_FIELDS),
                        actual=list(response_data.keys()),
                        severity="critical",
                        description=f"Missing required success response fields: {missing_fields}"
                    ))
                
                # 检查success字段值
                if response_data.get("success") is not True:
                    response_format_compliant = False
                    issues.append(ComplianceIssue(
                        field="success",
                        expected=True,
                        actual=response_data.get("success"),
                        severity="major",
                        description="Success field should be true for successful responses"
                    ))
                
                # 检查code字段值
                if response_data.get("code") != response.status_code:
                    response_format_compliant = False
                    issues.append(ComplianceIssue(
                        field="code",
                        expected=response.status_code,
                        actual=response_data.get("code"),
                        severity="major",
                        description="Code field should match HTTP status code"
                    ))
            
            else:
                # 检查错误响应格式
                missing_fields = self.REQUIRED_ERROR_FIELDS - set(response_data.keys())
                if missing_fields:
                    required_fields_present = False
                    response_format_compliant = False
                    issues.append(ComplianceIssue(
                        field="required_fields",
                        expected=list(self.REQUIRED_ERROR_FIELDS),
                        actual=list(response_data.keys()),
                        severity="critical",
                        description=f"Missing required error response fields: {missing_fields}"
                    ))
                
                # 检查success字段值
                if response_data.get("success") is not False:
                    response_format_compliant = False
                    issues.append(ComplianceIssue(
                        field="success",
                        expected=False,
                        actual=response_data.get("success"),
                        severity="major",
                        description="Success field should be false for error responses"
                    ))
            
            # 3. 检查meta字段
            meta = response_data.get("meta", {})
            if isinstance(meta, dict):
                missing_meta_fields = self.REQUIRED_META_FIELDS - set(meta.keys())
                if missing_meta_fields:
                    response_format_compliant = False
                    issues.append(ComplianceIssue(
                        field="meta",
                        expected=list(self.REQUIRED_META_FIELDS),
                        actual=list(meta.keys()),
                        severity="major",
                        description=f"Missing required meta fields: {missing_meta_fields}"
                    ))
                
                # 检查version字段
                if meta.get("version") != "v2":
                    response_format_compliant = False
                    issues.append(ComplianceIssue(
                        field="meta.version",
                        expected="v2",
                        actual=meta.get("version"),
                        severity="major",
                        description="Meta version should be 'v2'"
                    ))
            else:
                response_format_compliant = False
                issues.append(ComplianceIssue(
                    field="meta",
                    expected="object",
                    actual=type(meta).__name__,
                    severity="critical",
                    description="Meta field should be an object"
                ))
            
            # 确定整体合规性状态
            if not issues:
                status = ComplianceStatus.COMPLIANT
            else:
                critical_issues = [i for i in issues if i.severity == "critical"]
                if critical_issues:
                    status = ComplianceStatus.NON_COMPLIANT
                else:
                    status = ComplianceStatus.NON_COMPLIANT
            
            return EndpointComplianceResult(
                endpoint=endpoint,
                method=method,
                status=status,
                http_status_code=response.status_code,
                response_format_compliant=response_format_compliant,
                status_code_compliant=status_code_compliant,
                required_fields_present=required_fields_present,
                issues=issues,
                response_sample=response_data,
                execution_time_ms=execution_time
            )
        
        except httpx.TimeoutException:
            return EndpointComplianceResult(
                endpoint=endpoint,
                method=method,
                status=ComplianceStatus.ERROR,
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                issues=[ComplianceIssue(
                    field="network",
                    expected="Response within timeout",
                    actual="Timeout",
                    severity="critical",
                    description="Request timed out"
                )]
            )
        
        except httpx.ConnectError:
            return EndpointComplianceResult(
                endpoint=endpoint,
                method=method,
                status=ComplianceStatus.ERROR,
                issues=[ComplianceIssue(
                    field="network",
                    expected="Successful connection",
                    actual="Connection failed",
                    severity="critical",
                    description="Failed to connect to server"
                )]
            )
        
        except Exception as e:
            return EndpointComplianceResult(
                endpoint=endpoint,
                method=method,
                status=ComplianceStatus.ERROR,
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                issues=[ComplianceIssue(
                    field="unknown",
                    expected="Successful execution",
                    actual=str(e),
                    severity="critical",
                    description=f"Unexpected error: {str(e)}"
                )]
            )
    
    async def check_all_endpoints(self) -> ComplianceReport:
        """检查所有系统管理端点的合规性"""
        self.logger.info("开始V2 API合规性检查...")
        
        all_results = []
        
        # 遍历所有模块和端点
        for module_name, endpoints in self.SYSTEM_MANAGEMENT_ENDPOINTS.items():
            self.logger.info(f"检查模块: {module_name}")
            
            for method, endpoint, description in endpoints:
                self.logger.info(f"  检查端点: {method} {endpoint}")
                
                result = await self.check_endpoint_compliance(method, endpoint, description)
                all_results.append(result)
                
                # 记录结果
                if result.status == ComplianceStatus.COMPLIANT:
                    self.logger.info(f"    ✅ 合规")
                elif result.status == ComplianceStatus.NON_COMPLIANT:
                    self.logger.warning(f"    ❌ 不合规 ({len(result.issues)} 个问题)")
                elif result.status == ComplianceStatus.ERROR:
                    self.logger.error(f"    🔥 错误")
                else:
                    self.logger.info(f"    ⏭️ 跳过")
        
        # 生成报告
        compliant_count = len([r for r in all_results if r.status == ComplianceStatus.COMPLIANT])
        non_compliant_count = len([r for r in all_results if r.status == ComplianceStatus.NON_COMPLIANT])
        error_count = len([r for r in all_results if r.status == ComplianceStatus.ERROR])
        skipped_count = len([r for r in all_results if r.status == ComplianceStatus.SKIPPED])
        
        total_endpoints = len(all_results)
        compliance_rate = (compliant_count / total_endpoints * 100) if total_endpoints > 0 else 0
        
        # 生成摘要
        summary = {
            "modules_checked": len(self.SYSTEM_MANAGEMENT_ENDPOINTS),
            "endpoints_by_module": {
                module: len(endpoints) 
                for module, endpoints in self.SYSTEM_MANAGEMENT_ENDPOINTS.items()
            },
            "issues_by_severity": {
                "critical": sum(len([i for i in r.issues if i.severity == "critical"]) for r in all_results),
                "major": sum(len([i for i in r.issues if i.severity == "major"]) for r in all_results),
                "minor": sum(len([i for i in r.issues if i.severity == "minor"]) for r in all_results)
            },
            "common_issues": self._analyze_common_issues(all_results),
            "performance_stats": {
                "avg_response_time_ms": sum(r.execution_time_ms or 0 for r in all_results) / len(all_results) if all_results else 0,
                "slowest_endpoint": max(all_results, key=lambda r: r.execution_time_ms or 0, default=None),
                "fastest_endpoint": min(all_results, key=lambda r: r.execution_time_ms or float('inf'), default=None)
            }
        }
        
        report = ComplianceReport(
            timestamp=datetime.now().isoformat(),
            total_endpoints=total_endpoints,
            compliant_count=compliant_count,
            non_compliant_count=non_compliant_count,
            error_count=error_count,
            skipped_count=skipped_count,
            compliance_rate=compliance_rate,
            endpoints=all_results,
            summary=summary
        )
        
        self.logger.info(f"合规性检查完成: {compliance_rate:.1f}% 合规率 ({compliant_count}/{total_endpoints})")
        
        return report
    
    def _analyze_common_issues(self, results: List[EndpointComplianceResult]) -> Dict[str, int]:
        """分析常见问题"""
        issue_counts = {}
        
        for result in results:
            for issue in result.issues:
                key = f"{issue.field}: {issue.description}"
                issue_counts[key] = issue_counts.get(key, 0) + 1
        
        # 返回前10个最常见的问题
        return dict(sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10])
    
    def generate_html_report(self, report: ComplianceReport) -> str:
        """生成HTML格式的报告"""
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>V2 API合规性检查报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; }}
        .summary-card h3 {{ margin: 0 0 10px 0; color: #333; }}
        .summary-card .number {{ font-size: 2em; font-weight: bold; }}
        .compliant {{ color: #28a745; }}
        .non-compliant {{ color: #dc3545; }}
        .error {{ color: #fd7e14; }}
        .skipped {{ color: #6c757d; }}
        .endpoints {{ margin-top: 30px; }}
        .endpoint {{ margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 6px; }}
        .endpoint-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
        .method {{ padding: 4px 8px; border-radius: 4px; color: white; font-weight: bold; }}
        .method.GET {{ background-color: #28a745; }}
        .method.POST {{ background-color: #007bff; }}
        .method.PUT {{ background-color: #ffc107; color: #212529; }}
        .method.DELETE {{ background-color: #dc3545; }}
        .status {{ padding: 4px 8px; border-radius: 4px; color: white; font-weight: bold; }}
        .status.compliant {{ background-color: #28a745; }}
        .status.non_compliant {{ background-color: #dc3545; }}
        .status.error {{ background-color: #fd7e14; }}
        .status.skipped {{ background-color: #6c757d; }}
        .issues {{ margin-top: 10px; }}
        .issue {{ margin: 5px 0; padding: 8px; border-left: 4px solid #dc3545; background: #f8d7da; }}
        .issue.major {{ border-left-color: #fd7e14; background: #fff3cd; }}
        .issue.minor {{ border-left-color: #ffc107; background: #fff3cd; }}
        .performance {{ margin-top: 20px; font-size: 0.9em; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>V2 API合规性检查报告</h1>
            <p>生成时间: {report.timestamp}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>总端点数</h3>
                <div class="number">{report.total_endpoints}</div>
            </div>
            <div class="summary-card">
                <h3>合规端点</h3>
                <div class="number compliant">{report.compliant_count}</div>
            </div>
            <div class="summary-card">
                <h3>不合规端点</h3>
                <div class="number non-compliant">{report.non_compliant_count}</div>
            </div>
            <div class="summary-card">
                <h3>错误端点</h3>
                <div class="number error">{report.error_count}</div>
            </div>
            <div class="summary-card">
                <h3>合规率</h3>
                <div class="number">{report.compliance_rate:.1f}%</div>
            </div>
        </div>
        
        <div class="endpoints">
            <h2>端点详情</h2>
        """
        
        for endpoint in report.endpoints:
            status_class = endpoint.status.value
            html += f"""
            <div class="endpoint">
                <div class="endpoint-header">
                    <div>
                        <span class="method {endpoint.method}">{endpoint.method}</span>
                        <strong>{endpoint.endpoint}</strong>
                    </div>
                    <span class="status {status_class}">{endpoint.status.value.upper()}</span>
                </div>
                
                <div class="performance">
                    HTTP状态码: {endpoint.http_status_code or 'N/A'} | 
                    响应时间: {(endpoint.execution_time_ms or 0):.1f}ms
                </div>
                
                {f'<div class="issues"><h4>问题 ({len(endpoint.issues)}):</h4>' if endpoint.issues else ''}
            """
            
            for issue in endpoint.issues:
                html += f"""
                <div class="issue {issue.severity}">
                    <strong>{issue.field}:</strong> {issue.description}<br>
                    <small>期望: {issue.expected} | 实际: {issue.actual}</small>
                </div>
                """
            
            if endpoint.issues:
                html += "</div>"
            
            html += "</div>"
        
        html += """
        </div>
    </div>
</body>
</html>
        """
        
        return html
    
    def save_report(self, report: ComplianceReport, output_dir: str = "reports") -> Tuple[str, str]:
        """保存报告到文件"""
        import os
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存JSON报告
        json_file = os.path.join(output_dir, f"v2_api_compliance_report_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, ensure_ascii=False, indent=2, default=str)
        
        # 保存HTML报告
        html_file = os.path.join(output_dir, f"v2_api_compliance_report_{timestamp}.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(self.generate_html_report(report))
        
        return json_file, html_file


async def main():
    """主函数 - 运行合规性检查"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建检查器
    checker = V2APIComplianceChecker(
        base_url="http://localhost:8888",
        # auth_token="your_token_here"  # 如果需要认证
    )
    
    # 运行检查
    report = await checker.check_all_endpoints()
    
    # 保存报告
    json_file, html_file = checker.save_report(report)
    
    print(f"\n📊 合规性检查完成!")
    print(f"📈 合规率: {report.compliance_rate:.1f}%")
    print(f"✅ 合规端点: {report.compliant_count}")
    print(f"❌ 不合规端点: {report.non_compliant_count}")
    print(f"🔥 错误端点: {report.error_count}")
    print(f"\n📄 报告已保存:")
    print(f"  JSON: {json_file}")
    print(f"  HTML: {html_file}")


if __name__ == "__main__":
    asyncio.run(main())