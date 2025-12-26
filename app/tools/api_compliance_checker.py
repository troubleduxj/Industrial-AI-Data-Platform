#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API v2合规性检查工具
基于现有的response_formatter_v2.py创建自动化检查脚本
"""

import os
import ast
import json
import logging
import asyncio
import inspect
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

import aiohttp
from fastapi import APIRouter
from fastapi.routing import APIRoute

from app.core.response_formatter_v2 import ResponseFormatterV2, APIv2Response, APIv2ErrorResponse

logger = logging.getLogger(__name__)


@dataclass
class ApiEndpoint:
    """API端点信息"""
    path: str
    method: str
    function_name: str
    module_path: str
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = None
    parameters: List[Dict[str, Any]] = None
    response_model: Optional[str] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.parameters is None:
            self.parameters = []
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class ComplianceIssue:
    """合规性问题"""
    severity: str  # high, medium, low
    category: str  # response_format, error_handling, pagination, etc.
    code: str
    message: str
    field: Optional[str] = None
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    suggestion: Optional[str] = None


@dataclass
class ComplianceResult:
    """合规性检查结果"""
    endpoint: ApiEndpoint
    is_compliant: bool
    score: int  # 0-100
    issues: List[ComplianceIssue]
    response_sample: Optional[Dict[str, Any]] = None
    error_sample: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []


@dataclass
class ComplianceReport:
    """合规性报告"""
    total_endpoints: int
    compliant_endpoints: int
    non_compliant_endpoints: int
    overall_score: float
    results: List[ComplianceResult]
    summary: Dict[str, Any]
    generated_at: str
    
    def __post_init__(self):
        if self.results is None:
            self.results = []


class ApiEndpointDiscovery:
    """API端点自动发现器"""
    
    def __init__(self, api_v2_path: str = "app/api/v2"):
        self.api_v2_path = Path(api_v2_path)
        self.endpoints: List[ApiEndpoint] = []
        
    async def discover_endpoints(self) -> List[ApiEndpoint]:
        """扫描所有v2 API端点"""
        logger.info(f"开始扫描API端点: {self.api_v2_path}")
        
        if not self.api_v2_path.exists():
            logger.error(f"API目录不存在: {self.api_v2_path}")
            return []
        
        # 扫描所有Python文件
        for py_file in self.api_v2_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
                
            try:
                await self._parse_api_file(py_file)
            except Exception as e:
                logger.error(f"解析API文件失败 {py_file}: {str(e)}")
                continue
        
        logger.info(f"发现 {len(self.endpoints)} 个API端点")
        return self.endpoints
    
    async def _parse_api_file(self, file_path: Path):
        """解析单个API文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析AST
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                logger.warning(f"文件 {file_path} 存在语法错误，跳过: {str(e)}")
                return
            
            # 检查是否包含路由定义
            has_router = False
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "router":
                            has_router = True
                            break
                # 检查是否有使用router的装饰器
                elif isinstance(node, ast.FunctionDef):
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                            if (isinstance(decorator.func.value, ast.Name) and 
                                decorator.func.value.id == "router"):
                                has_router = True
                                break
                        elif isinstance(decorator, ast.Attribute):
                            if (isinstance(decorator.value, ast.Name) and 
                                decorator.value.id == "router"):
                                has_router = True
                                break
                if has_router:
                    break
            
            if not has_router:
                logger.debug(f"文件 {file_path} 不包含路由定义，跳过")
                return
            
            logger.debug(f"文件 {file_path} 包含路由定义，开始解析端点")
            
            # 查找路由装饰器
            function_count = 0
            async_function_count = 0
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    function_count += 1
                    logger.debug(f"检查函数: {node.name}")
                    await self._extract_endpoint_from_function(node, file_path)
                elif isinstance(node, ast.AsyncFunctionDef):
                    async_function_count += 1
                    logger.debug(f"检查异步函数: {node.name}")
                    await self._extract_endpoint_from_function(node, file_path)
            
            logger.debug(f"文件 {file_path} 共检查了 {function_count} 个同步函数和 {async_function_count} 个异步函数")
                    
        except Exception as e:
            logger.warning(f"解析文件 {file_path} 失败: {str(e)}")
    
    async def _extract_endpoint_from_function(self, func_node, file_path: Path):
        """从函数节点提取端点信息"""
        try:
            # 查找路由装饰器
            for decorator in func_node.decorator_list:
                method = None
                path = None
                summary = None
                description = None
                
                if isinstance(decorator, ast.Call):
                    # 检查是否是路由装饰器 @router.get(), @router.post() 等
                    if isinstance(decorator.func, ast.Attribute):
                        if (isinstance(decorator.func.value, ast.Name) and 
                            decorator.func.value.id == "router"):
                            
                            method = decorator.func.attr.upper()
                            
                            # 提取路径和其他参数
                            if decorator.args:
                                if isinstance(decorator.args[0], ast.Constant):
                                    path = decorator.args[0].value
                                elif isinstance(decorator.args[0], ast.Str):  # Python < 3.8 兼容
                                    path = decorator.args[0].s
                            
                            # 提取关键字参数
                            for keyword in decorator.keywords:
                                if keyword.arg == "summary":
                                    if isinstance(keyword.value, ast.Constant):
                                        summary = keyword.value.value
                                    elif isinstance(keyword.value, ast.Str):
                                        summary = keyword.value.s
                                elif keyword.arg == "description":
                                    if isinstance(keyword.value, ast.Constant):
                                        description = keyword.value.value
                                    elif isinstance(keyword.value, ast.Str):
                                        description = keyword.value.s
                
                elif isinstance(decorator, ast.Attribute):
                    # 检查是否是简单的路由装饰器 @router.get
                    if (isinstance(decorator.value, ast.Name) and 
                        decorator.value.id == "router"):
                        method = decorator.attr.upper()
                        path = "/"  # 默认路径
                
                # 如果找到了路由装饰器
                if method and path is not None:
                    # 提取函数参数
                    parameters = await self._extract_function_parameters(func_node)
                    
                    endpoint = ApiEndpoint(
                        path=path,
                        method=method,
                        function_name=func_node.name,
                        module_path=str(file_path.name),
                        summary=summary,
                        description=description,
                        parameters=parameters
                    )
                    
                    self.endpoints.append(endpoint)
                    logger.debug(f"发现端点: {method} {path} -> {func_node.name}")
                    break  # 找到一个路由装饰器就够了
                                
        except Exception as e:
            logger.error(f"提取端点信息失败 {func_node.name}: {str(e)}")
    
    async def _extract_function_parameters(self, func_node) -> List[Dict[str, Any]]:
        """提取函数参数信息"""
        parameters = []
        
        try:
            for arg in func_node.args.args:
                param_info = {
                    "name": arg.arg,
                    "type": None,
                    "default": None,
                    "annotation": None
                }
                
                # 提取类型注解
                if arg.annotation:
                    if isinstance(arg.annotation, ast.Name):
                        param_info["annotation"] = arg.annotation.id
                    elif isinstance(arg.annotation, ast.Constant):
                        param_info["annotation"] = str(arg.annotation.value)
                
                parameters.append(param_info)
                
        except Exception as e:
            logger.error(f"提取参数信息失败: {str(e)}")
        
        return parameters
    
    def get_endpoints_by_module(self) -> Dict[str, List[ApiEndpoint]]:
        """按模块分组端点"""
        grouped = {}
        for endpoint in self.endpoints:
            module = endpoint.module_path
            if module not in grouped:
                grouped[module] = []
            grouped[module].append(endpoint)
        return grouped
    
    def get_endpoints_by_method(self) -> Dict[str, List[ApiEndpoint]]:
        """按HTTP方法分组端点"""
        grouped = {}
        for endpoint in self.endpoints:
            method = endpoint.method
            if method not in grouped:
                grouped[method] = []
            grouped[method].append(endpoint)
        return grouped
    
    def export_endpoints_catalog(self, output_path: str = "api_endpoints_catalog.json"):
        """导出API端点清单"""
        catalog = {
            "total_endpoints": len(self.endpoints),
            "discovery_time": datetime.now().isoformat(),
            "endpoints": [asdict(endpoint) for endpoint in self.endpoints],
            "summary": {
                "by_module": {k: len(v) for k, v in self.get_endpoints_by_module().items()},
                "by_method": {k: len(v) for k, v in self.get_endpoints_by_method().items()}
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)
        
        logger.info(f"API端点清单已导出到: {output_path}")
        return catalog


class ResponseFormatValidator:
    """响应格式验证器"""
    
    def __init__(self):
        self.required_success_fields = {"success", "code", "message", "data", "meta"}
        self.required_error_fields = {"success", "code", "message", "error_type", "meta"}
        self.required_meta_fields = {"version", "timestamp", "request_id"}
        self.required_pagination_meta_fields = {"total", "page", "page_size", "has_next", "has_prev"}
        self.valid_http_codes = {200, 201, 204, 400, 401, 403, 404, 422, 500}
        self.valid_error_types = {
            "ValidationError", "AuthenticationError", "AuthorizationError", 
            "NotFoundError", "InternalServerError", "BusinessError"
        }
    
    async def validate_response_format(self, response_data: Dict[str, Any], 
                                     endpoint: ApiEndpoint) -> List[ComplianceIssue]:
        """验证响应格式合规性"""
        issues = []
        
        # 检查基本字段
        if response_data.get("success") is True:
            issues.extend(await self._validate_success_response(response_data, endpoint))
        else:
            issues.extend(await self._validate_error_response(response_data, endpoint))
        
        # 检查meta字段
        issues.extend(await self._validate_meta_fields(response_data, endpoint))
        
        # 检查分页字段（如果适用）
        if self._is_pagination_endpoint(endpoint):
            issues.extend(await self._validate_pagination_fields(response_data, endpoint))
        
        return issues
    
    async def _validate_success_response(self, response_data: Dict[str, Any], 
                                       endpoint: ApiEndpoint) -> List[ComplianceIssue]:
        """验证成功响应格式"""
        issues = []
        
        # 检查必需字段
        for field in self.required_success_fields:
            if field not in response_data:
                issues.append(ComplianceIssue(
                    severity="high",
                    category="response_format",
                    code="MISSING_REQUIRED_FIELD",
                    message=f"缺少必需字段: {field}",
                    field=field,
                    expected="present",
                    actual="missing",
                    suggestion=f"在响应中添加 {field} 字段"
                ))
        
        # 检查字段类型
        if "success" in response_data and not isinstance(response_data["success"], bool):
            issues.append(ComplianceIssue(
                severity="high",
                category="response_format",
                code="INVALID_FIELD_TYPE",
                message="success字段必须是布尔类型",
                field="success",
                expected="boolean",
                actual=type(response_data["success"]).__name__,
                suggestion="将success字段设置为true或false"
            ))
        
        if "code" in response_data and not isinstance(response_data["code"], int):
            issues.append(ComplianceIssue(
                severity="high",
                category="response_format",
                code="INVALID_FIELD_TYPE",
                message="code字段必须是整数类型",
                field="code",
                expected="integer",
                actual=type(response_data["code"]).__name__,
                suggestion="将code字段设置为HTTP状态码（如200, 201等）"
            ))
        
        if "message" in response_data and not isinstance(response_data["message"], str):
            issues.append(ComplianceIssue(
                severity="medium",
                category="response_format",
                code="INVALID_FIELD_TYPE",
                message="message字段必须是字符串类型",
                field="message",
                expected="string",
                actual=type(response_data["message"]).__name__,
                suggestion="将message字段设置为描述性文本"
            ))
        
        return issues
    
    async def _validate_error_response(self, response_data: Dict[str, Any], 
                                     endpoint: ApiEndpoint) -> List[ComplianceIssue]:
        """验证错误响应格式"""
        issues = []
        
        # 检查必需字段
        for field in self.required_error_fields:
            if field not in response_data:
                issues.append(ComplianceIssue(
                    severity="high",
                    category="error_handling",
                    code="MISSING_ERROR_FIELD",
                    message=f"错误响应缺少必需字段: {field}",
                    field=field,
                    expected="present",
                    actual="missing",
                    suggestion=f"在错误响应中添加 {field} 字段"
                ))
        
        # 检查success字段应为false
        if response_data.get("success") is not False:
            issues.append(ComplianceIssue(
                severity="high",
                category="error_handling",
                code="INVALID_ERROR_SUCCESS_FIELD",
                message="错误响应的success字段必须为false",
                field="success",
                expected=False,
                actual=response_data.get("success"),
                suggestion="将错误响应的success字段设置为false"
            ))
        
        # 检查details字段（如果存在）
        if "details" in response_data:
            if not isinstance(response_data["details"], list):
                issues.append(ComplianceIssue(
                    severity="medium",
                    category="error_handling",
                    code="INVALID_DETAILS_TYPE",
                    message="details字段必须是数组类型",
                    field="details",
                    expected="array",
                    actual=type(response_data["details"]).__name__,
                    suggestion="将details字段设置为错误详情数组"
                ))
        
        return issues
    
    async def _validate_meta_fields(self, response_data: Dict[str, Any], 
                                  endpoint: ApiEndpoint) -> List[ComplianceIssue]:
        """验证meta字段"""
        issues = []
        
        if "meta" not in response_data:
            issues.append(ComplianceIssue(
                severity="high",
                category="response_format",
                code="MISSING_META_FIELD",
                message="缺少meta字段",
                field="meta",
                expected="object",
                actual="missing",
                suggestion="添加包含版本、时间戳等信息的meta字段"
            ))
            return issues
        
        meta = response_data["meta"]
        if not isinstance(meta, dict):
            issues.append(ComplianceIssue(
                severity="high",
                category="response_format",
                code="INVALID_META_TYPE",
                message="meta字段必须是对象类型",
                field="meta",
                expected="object",
                actual=type(meta).__name__,
                suggestion="将meta字段设置为包含元数据的对象"
            ))
            return issues
        
        # 检查必需的meta字段
        for field in self.required_meta_fields:
            if field not in meta:
                issues.append(ComplianceIssue(
                    severity="medium",
                    category="response_format",
                    code="MISSING_META_SUBFIELD",
                    message=f"meta字段缺少必需子字段: {field}",
                    field=f"meta.{field}",
                    expected="present",
                    actual="missing",
                    suggestion=f"在meta字段中添加 {field} 子字段"
                ))
        
        return issues
    
    async def _validate_pagination_fields(self, response_data: Dict[str, Any], 
                                        endpoint: ApiEndpoint) -> List[ComplianceIssue]:
        """验证分页字段"""
        issues = []
        
        if "meta" not in response_data:
            return issues
        
        meta = response_data["meta"]
        
        # 检查分页相关字段
        for field in self.required_pagination_meta_fields:
            if field not in meta:
                issues.append(ComplianceIssue(
                    severity="medium",
                    category="pagination",
                    code="MISSING_PAGINATION_FIELD",
                    message=f"分页API缺少必需字段: meta.{field}",
                    field=f"meta.{field}",
                    expected="present",
                    actual="missing",
                    suggestion=f"在meta字段中添加分页信息 {field}"
                ))
        
        # 检查分页字段类型
        if "total" in meta and not isinstance(meta["total"], int):
            issues.append(ComplianceIssue(
                severity="medium",
                category="pagination",
                code="INVALID_PAGINATION_TYPE",
                message="meta.total必须是整数类型",
                field="meta.total",
                expected="integer",
                actual=type(meta["total"]).__name__,
                suggestion="将meta.total设置为记录总数"
            ))
        
        return issues
    
    def _is_pagination_endpoint(self, endpoint: ApiEndpoint) -> bool:
        """判断是否为分页端点"""
        # 检查路径和参数
        pagination_indicators = ["page", "page_size", "limit", "offset"]
        
        # 检查参数名
        for param in endpoint.parameters:
            if param.get("name") in pagination_indicators:
                return True
        
        # 检查函数名
        if any(word in endpoint.function_name.lower() for word in ["list", "search", "get_all"]):
            return True
        
        return False
    
    async def validate_error_details(self, details: List[Dict[str, Any]]) -> List[ComplianceIssue]:
        """验证错误详情格式"""
        issues = []
        
        if not isinstance(details, list):
            issues.append(ComplianceIssue(
                severity="high",
                category="error_handling",
                code="INVALID_DETAILS_FORMAT",
                message="details必须是数组格式",
                field="details",
                expected="array",
                actual=type(details).__name__,
                suggestion="将details设置为错误详情数组"
            ))
            return issues
        
        for i, detail in enumerate(details):
            if not isinstance(detail, dict):
                issues.append(ComplianceIssue(
                    severity="medium",
                    category="error_handling",
                    code="INVALID_DETAIL_ITEM",
                    message=f"details[{i}]必须是对象格式",
                    field=f"details[{i}]",
                    expected="object",
                    actual=type(detail).__name__,
                    suggestion="将错误详情项设置为包含field、code、message的对象"
                ))
                continue
            
            # 检查错误详情必需字段
            required_detail_fields = {"code", "message"}
            for field in required_detail_fields:
                if field not in detail:
                    issues.append(ComplianceIssue(
                        severity="medium",
                        category="error_handling",
                        code="MISSING_DETAIL_FIELD",
                        message=f"错误详情缺少必需字段: {field}",
                        field=f"details[{i}].{field}",
                        expected="present",
                        actual="missing",
                        suggestion=f"在错误详情中添加 {field} 字段"
                    ))
        
        return issues
    
    async def validate_hateoas_links(self, response_data: Dict[str, Any]) -> List[ComplianceIssue]:
        """验证HATEOAS链接格式"""
        issues = []
        
        if "links" not in response_data:
            # HATEOAS链接是可选的，不强制要求
            return issues
        
        links = response_data["links"]
        if not isinstance(links, dict):
            issues.append(ComplianceIssue(
                severity="low",
                category="hateoas",
                code="INVALID_LINKS_FORMAT",
                message="links字段必须是对象格式",
                field="links",
                expected="object",
                actual=type(links).__name__,
                suggestion="将links字段设置为包含相关链接的对象"
            ))
            return issues
        
        # 检查链接URL格式
        for link_name, link_url in links.items():
            if link_url is not None and not isinstance(link_url, str):
                issues.append(ComplianceIssue(
                    severity="low",
                    category="hateoas",
                    code="INVALID_LINK_URL",
                    message=f"链接URL必须是字符串格式: {link_name}",
                    field=f"links.{link_name}",
                    expected="string",
                    actual=type(link_url).__name__,
                    suggestion="将链接URL设置为有效的URL字符串"
                ))
        
        return issues
    
    async def validate_response_consistency(self, response_data: Dict[str, Any], 
                                          endpoint: ApiEndpoint) -> List[ComplianceIssue]:
        """验证响应一致性"""
        issues = []
        
        # 检查HTTP状态码与success字段的一致性
        success = response_data.get("success")
        code = response_data.get("code")
        
        if success is True and code and code >= 400:
            issues.append(ComplianceIssue(
                severity="high",
                category="response_consistency",
                code="INCONSISTENT_SUCCESS_CODE",
                message="success为true但HTTP状态码表示错误",
                field="success/code",
                expected="success=true时code应为2xx或3xx",
                actual=f"success={success}, code={code}",
                suggestion="确保success字段与HTTP状态码保持一致"
            ))
        
        if success is False and code and code < 400:
            issues.append(ComplianceIssue(
                severity="high",
                category="response_consistency",
                code="INCONSISTENT_ERROR_CODE",
                message="success为false但HTTP状态码表示成功",
                field="success/code",
                expected="success=false时code应为4xx或5xx",
                actual=f"success={success}, code={code}",
                suggestion="确保success字段与HTTP状态码保持一致"
            ))
        
        return issues


class ApiComplianceChecker:
    """API合规性检查器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.discovery = ApiEndpointDiscovery()
        self.validator = ResponseFormatValidator()
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_all_endpoints(self) -> ComplianceReport:
        """检查所有API端点的合规性"""
        logger.info("开始API合规性检查")
        
        # 发现所有端点
        endpoints = await self.discovery.discover_endpoints()
        
        if not endpoints:
            logger.warning("未发现任何API端点")
            return ComplianceReport(
                total_endpoints=0,
                compliant_endpoints=0,
                non_compliant_endpoints=0,
                overall_score=0.0,
                results=[],
                summary={},
                generated_at=datetime.now().isoformat()
            )
        
        # 检查每个端点
        results = []
        for endpoint in endpoints:
            try:
                result = await self.check_endpoint_compliance(endpoint)
                results.append(result)
                logger.info(f"检查端点 {endpoint.method} {endpoint.path}: "
                          f"{'合规' if result.is_compliant else '不合规'} (评分: {result.score})")
            except Exception as e:
                logger.error(f"检查端点失败 {endpoint.method} {endpoint.path}: {str(e)}")
                # 创建失败结果
                result = ComplianceResult(
                    endpoint=endpoint,
                    is_compliant=False,
                    score=0,
                    issues=[ComplianceIssue(
                        severity="high",
                        category="system_error",
                        code="CHECK_FAILED",
                        message=f"检查失败: {str(e)}",
                        suggestion="检查API端点是否可访问"
                    )]
                )
                results.append(result)
        
        # 生成报告
        return await self._generate_report(results)
    
    async def check_endpoint_compliance(self, endpoint: ApiEndpoint) -> ComplianceResult:
        """检查单个端点的合规性"""
        issues = []
        response_sample = None
        error_sample = None
        
        try:
            # 测试成功响应
            success_response = await self._test_endpoint_success(endpoint)
            if success_response:
                response_sample = success_response
                success_issues = await self.validator.validate_response_format(success_response, endpoint)
                issues.extend(success_issues)
                
                # 验证HATEOAS链接
                hateoas_issues = await self.validator.validate_hateoas_links(success_response)
                issues.extend(hateoas_issues)
                
                # 验证响应一致性
                consistency_issues = await self.validator.validate_response_consistency(success_response, endpoint)
                issues.extend(consistency_issues)
            
            # 测试错误响应
            error_response = await self._test_endpoint_error(endpoint)
            if error_response:
                error_sample = error_response
                error_issues = await self.validator.validate_response_format(error_response, endpoint)
                issues.extend(error_issues)
                
                # 验证错误详情
                if "details" in error_response:
                    detail_issues = await self.validator.validate_error_details(error_response["details"])
                    issues.extend(detail_issues)
        
        except Exception as e:
            logger.error(f"测试端点失败 {endpoint.method} {endpoint.path}: {str(e)}")
            issues.append(ComplianceIssue(
                severity="high",
                category="system_error",
                code="ENDPOINT_TEST_FAILED",
                message=f"端点测试失败: {str(e)}",
                suggestion="检查端点是否正常工作"
            ))
        
        # 计算合规性评分
        score = self._calculate_compliance_score(issues)
        is_compliant = score >= 80  # 80分以上认为合规
        
        return ComplianceResult(
            endpoint=endpoint,
            is_compliant=is_compliant,
            score=score,
            issues=issues,
            response_sample=response_sample,
            error_sample=error_sample
        )
    
    async def _test_endpoint_success(self, endpoint: ApiEndpoint) -> Optional[Dict[str, Any]]:
        """测试端点成功响应"""
        if not self.session:
            return None
        
        try:
            url = f"{self.base_url}/api/v2{endpoint.path}"
            
            # 根据端点类型构造测试参数
            params = {}
            if self.validator._is_pagination_endpoint(endpoint):
                params = {"page": 1, "page_size": 10}
            
            # 发送请求
            method = endpoint.method.lower()
            if method == "get":
                async with self.session.get(url, params=params) as response:
                    if response.status < 400:
                        return await response.json()
            elif method == "post":
                # 对于POST请求，尝试发送空数据或最小数据
                test_data = {}
                async with self.session.post(url, json=test_data) as response:
                    if response.status < 400:
                        return await response.json()
            
        except Exception as e:
            logger.debug(f"测试成功响应失败 {endpoint.method} {endpoint.path}: {str(e)}")
        
        return None
    
    async def _test_endpoint_error(self, endpoint: ApiEndpoint) -> Optional[Dict[str, Any]]:
        """测试端点错误响应"""
        if not self.session:
            return None
        
        try:
            url = f"{self.base_url}/api/v2{endpoint.path}"
            
            # 构造会导致错误的请求
            method = endpoint.method.lower()
            if method == "get":
                # 尝试访问不存在的资源
                if "{" in endpoint.path:
                    test_url = url.replace("{", "999999").replace("}", "")
                    async with self.session.get(test_url) as response:
                        if response.status >= 400:
                            return await response.json()
            elif method == "post":
                # 发送无效数据
                invalid_data = {"invalid": "data"}
                async with self.session.post(url, json=invalid_data) as response:
                    if response.status >= 400:
                        return await response.json()
            
        except Exception as e:
            logger.debug(f"测试错误响应失败 {endpoint.method} {endpoint.path}: {str(e)}")
        
        return None
    
    def _calculate_compliance_score(self, issues: List[ComplianceIssue]) -> int:
        """计算合规性评分"""
        if not issues:
            return 100
        
        # 根据问题严重程度扣分
        score = 100
        for issue in issues:
            if issue.severity == "high":
                score -= 20
            elif issue.severity == "medium":
                score -= 10
            elif issue.severity == "low":
                score -= 5
        
        return max(0, score)
    
    async def _generate_report(self, results: List[ComplianceResult]) -> ComplianceReport:
        """生成合规性报告"""
        total_endpoints = len(results)
        compliant_endpoints = sum(1 for r in results if r.is_compliant)
        non_compliant_endpoints = total_endpoints - compliant_endpoints
        
        # 计算总体评分
        if total_endpoints > 0:
            overall_score = sum(r.score for r in results) / total_endpoints
        else:
            overall_score = 0.0
        
        # 生成摘要统计
        summary = {
            "compliance_rate": f"{(compliant_endpoints / total_endpoints * 100):.1f}%" if total_endpoints > 0 else "0%",
            "average_score": f"{overall_score:.1f}",
            "issues_by_severity": self._count_issues_by_severity(results),
            "issues_by_category": self._count_issues_by_category(results),
            "top_issues": self._get_top_issues(results),
            "endpoints_by_module": self._group_results_by_module(results)
        }
        
        return ComplianceReport(
            total_endpoints=total_endpoints,
            compliant_endpoints=compliant_endpoints,
            non_compliant_endpoints=non_compliant_endpoints,
            overall_score=overall_score,
            results=results,
            summary=summary,
            generated_at=datetime.now().isoformat()
        )
    
    def _count_issues_by_severity(self, results: List[ComplianceResult]) -> Dict[str, int]:
        """按严重程度统计问题"""
        counts = {"high": 0, "medium": 0, "low": 0}
        for result in results:
            for issue in result.issues:
                counts[issue.severity] = counts.get(issue.severity, 0) + 1
        return counts
    
    def _count_issues_by_category(self, results: List[ComplianceResult]) -> Dict[str, int]:
        """按类别统计问题"""
        counts = {}
        for result in results:
            for issue in result.issues:
                counts[issue.category] = counts.get(issue.category, 0) + 1
        return counts
    
    def _get_top_issues(self, results: List[ComplianceResult], limit: int = 10) -> List[Dict[str, Any]]:
        """获取最常见的问题"""
        issue_counts = {}
        for result in results:
            for issue in result.issues:
                key = f"{issue.code}: {issue.message}"
                if key not in issue_counts:
                    issue_counts[key] = {
                        "code": issue.code,
                        "message": issue.message,
                        "severity": issue.severity,
                        "category": issue.category,
                        "count": 0,
                        "suggestion": issue.suggestion
                    }
                issue_counts[key]["count"] += 1
        
        # 按出现次数排序
        sorted_issues = sorted(issue_counts.values(), key=lambda x: x["count"], reverse=True)
        return sorted_issues[:limit]
    
    def _group_results_by_module(self, results: List[ComplianceResult]) -> Dict[str, Dict[str, Any]]:
        """按模块分组结果"""
        grouped = {}
        for result in results:
            module = result.endpoint.module_path
            if module not in grouped:
                grouped[module] = {
                    "total": 0,
                    "compliant": 0,
                    "average_score": 0.0,
                    "endpoints": []
                }
            
            grouped[module]["total"] += 1
            if result.is_compliant:
                grouped[module]["compliant"] += 1
            grouped[module]["endpoints"].append({
                "path": result.endpoint.path,
                "method": result.endpoint.method,
                "score": result.score,
                "is_compliant": result.is_compliant
            })
        
        # 计算平均分
        for module_data in grouped.values():
            if module_data["total"] > 0:
                total_score = sum(ep["score"] for ep in module_data["endpoints"])
                module_data["average_score"] = total_score / module_data["total"]
        
        return grouped


class ComplianceReportGenerator:
    """合规性报告生成器"""
    
    def __init__(self):
        self.template_dir = Path("app/tools/templates")
        self.output_dir = Path("reports")
        self.output_dir.mkdir(exist_ok=True)
    
    async def generate_html_report(self, report: ComplianceReport, 
                                 output_path: Optional[str] = None) -> str:
        """生成HTML格式的可视化报告"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"reports/api_compliance_report_{timestamp}.html"
        
        # 生成HTML内容
        html_content = self._generate_html_content(report)
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML报告已生成: {output_path}")
        return output_path
    
    def _generate_html_content(self, report: ComplianceReport) -> str:
        """生成HTML报告内容"""
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API v2 合规性检查报告</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .summary-card .value {{
            font-size: 2em;
            font-weight: bold;
            margin: 0;
        }}
        .value.good {{ color: #28a745; }}
        .value.warning {{ color: #ffc107; }}
        .value.danger {{ color: #dc3545; }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        .table th, .table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        .table th {{
            background-color: #f8f9fa;
            font-weight: 600;
            color: #333;
        }}
        .table tr:hover {{
            background-color: #f8f9fa;
        }}
        .badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .badge.compliant {{
            background-color: #d4edda;
            color: #155724;
        }}
        .badge.non-compliant {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .badge.high {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .badge.medium {{
            background-color: #fff3cd;
            color: #856404;
        }}
        .badge.low {{
            background-color: #d1ecf1;
            color: #0c5460;
        }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background-color: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
            transition: width 0.3s ease;
        }}
        .issue-details {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 10px 0;
            border-radius: 0 4px 4px 0;
        }}
        .issue-details h4 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .issue-details p {{
            margin: 5px 0;
            color: #666;
        }}
        .collapsible {{
            cursor: pointer;
            padding: 10px;
            background-color: #f1f1f1;
            border: none;
            text-align: left;
            outline: none;
            font-size: 15px;
            width: 100%;
            border-radius: 4px;
            margin-bottom: 5px;
        }}
        .collapsible:hover {{
            background-color: #ddd;
        }}
        .collapsible-content {{
            padding: 0 18px;
            display: none;
            overflow: hidden;
            background-color: #f9f9f9;
            border-radius: 0 0 4px 4px;
        }}
        .chart-container {{
            width: 100%;
            height: 300px;
            margin: 20px 0;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>API v2 合规性检查报告</h1>
            <p>生成时间: {report.generated_at}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>总端点数</h3>
                <p class="value">{report.total_endpoints}</p>
            </div>
            <div class="summary-card">
                <h3>合规端点</h3>
                <p class="value good">{report.compliant_endpoints}</p>
            </div>
            <div class="summary-card">
                <h3>不合规端点</h3>
                <p class="value danger">{report.non_compliant_endpoints}</p>
            </div>
            <div class="summary-card">
                <h3>总体评分</h3>
                <p class="value {'good' if report.overall_score >= 80 else 'warning' if report.overall_score >= 60 else 'danger'}">{report.overall_score:.1f}</p>
            </div>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>合规性概览</h2>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {(report.compliant_endpoints / report.total_endpoints * 100) if report.total_endpoints > 0 else 0:.1f}%"></div>
                </div>
                <p>合规率: {report.summary.get('compliance_rate', '0%')}</p>
            </div>
            
            <div class="section">
                <h2>问题统计</h2>
                <div class="chart-container">
                    <canvas id="issuesChart"></canvas>
                </div>
                <table class="table">
                    <thead>
                        <tr>
                            <th>严重程度</th>
                            <th>问题数量</th>
                            <th>占比</th>
                        </tr>
                    </thead>
                    <tbody>
                        {self._generate_issues_table_rows(report.summary.get('issues_by_severity', {}))}
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>常见问题</h2>
                {self._generate_top_issues_html(report.summary.get('top_issues', []))}
            </div>
            
            <div class="section">
                <h2>端点详情</h2>
                {self._generate_endpoints_details_html(report.results)}
            </div>
            
            <div class="section">
                <h2>按模块统计</h2>
                {self._generate_modules_summary_html(report.summary.get('endpoints_by_module', {}))}
            </div>
        </div>
    </div>
    
    <script>
        // 初始化图表
        const ctx = document.getElementById('issuesChart').getContext('2d');
        const issuesData = {json.dumps(report.summary.get('issues_by_severity', {}))};
        
        new Chart(ctx, {{
            type: 'doughnut',
            data: {{
                labels: ['高', '中', '低'],
                datasets: [{{
                    data: [issuesData.high || 0, issuesData.medium || 0, issuesData.low || 0],
                    backgroundColor: ['#dc3545', '#ffc107', '#17a2b8'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});
        
        // 折叠功能
        document.querySelectorAll('.collapsible').forEach(button => {{
            button.addEventListener('click', function() {{
                this.classList.toggle('active');
                const content = this.nextElementSibling;
                if (content.style.display === 'block') {{
                    content.style.display = 'none';
                }} else {{
                    content.style.display = 'block';
                }}
            }});
        }});
    </script>
</body>
</html>
        """
        return html
    
    def _generate_issues_table_rows(self, issues_by_severity: Dict[str, int]) -> str:
        """生成问题统计表格行"""
        total_issues = sum(issues_by_severity.values())
        rows = []
        
        severity_labels = {"high": "高", "medium": "中", "low": "低"}
        severity_classes = {"high": "danger", "medium": "warning", "low": "info"}
        
        for severity, count in issues_by_severity.items():
            percentage = (count / total_issues * 100) if total_issues > 0 else 0
            label = severity_labels.get(severity, severity)
            css_class = severity_classes.get(severity, "")
            
            rows.append(f"""
                <tr>
                    <td><span class="badge {severity}">{label}</span></td>
                    <td>{count}</td>
                    <td>{percentage:.1f}%</td>
                </tr>
            """)
        
        return "".join(rows)
    
    def _generate_top_issues_html(self, top_issues: List[Dict[str, Any]]) -> str:
        """生成常见问题HTML"""
        if not top_issues:
            return "<p>暂无问题记录</p>"
        
        html_parts = []
        for issue in top_issues[:10]:  # 只显示前10个
            html_parts.append(f"""
                <div class="issue-details">
                    <h4>
                        <span class="badge {issue['severity']}">{issue['severity'].upper()}</span>
                        {issue['message']} 
                        <small>(出现 {issue['count']} 次)</small>
                    </h4>
                    <p><strong>类别:</strong> {issue['category']}</p>
                    <p><strong>错误代码:</strong> {issue['code']}</p>
                    {f"<p><strong>建议:</strong> {issue['suggestion']}</p>" if issue.get('suggestion') else ""}
                </div>
            """)
        
        return "".join(html_parts)
    
    def _generate_endpoints_details_html(self, results: List[ComplianceResult]) -> str:
        """生成端点详情HTML"""
        html_parts = []
        
        for result in results:
            endpoint = result.endpoint
            status_class = "compliant" if result.is_compliant else "non-compliant"
            status_text = "合规" if result.is_compliant else "不合规"
            
            issues_html = ""
            if result.issues:
                issues_html = "<ul>"
                for issue in result.issues:
                    issues_html += f"""
                        <li>
                            <span class="badge {issue.severity}">{issue.severity}</span>
                            {issue.message}
                            {f" - {issue.suggestion}" if issue.suggestion else ""}
                        </li>
                    """
                issues_html += "</ul>"
            
            html_parts.append(f"""
                <button class="collapsible">
                    <strong>{endpoint.method}</strong> {endpoint.path} 
                    <span class="badge {status_class}">{status_text}</span>
                    <span style="float: right;">评分: {result.score}</span>
                </button>
                <div class="collapsible-content">
                    <p><strong>模块:</strong> {endpoint.module_path}</p>
                    <p><strong>函数:</strong> {endpoint.function_name}</p>
                    {f"<p><strong>描述:</strong> {endpoint.summary}</p>" if endpoint.summary else ""}
                    <p><strong>问题数量:</strong> {len(result.issues)}</p>
                    {issues_html if issues_html else "<p>无问题</p>"}
                </div>
            """)
        
        return "".join(html_parts)
    
    def _generate_modules_summary_html(self, modules_data: Dict[str, Dict[str, Any]]) -> str:
        """生成模块摘要HTML"""
        if not modules_data:
            return "<p>暂无模块数据</p>"
        
        html_parts = ["<table class='table'><thead><tr><th>模块</th><th>总端点</th><th>合规端点</th><th>合规率</th><th>平均分</th></tr></thead><tbody>"]
        
        for module, data in modules_data.items():
            compliance_rate = (data['compliant'] / data['total'] * 100) if data['total'] > 0 else 0
            rate_class = "good" if compliance_rate >= 80 else "warning" if compliance_rate >= 60 else "danger"
            
            html_parts.append(f"""
                <tr>
                    <td>{module}</td>
                    <td>{data['total']}</td>
                    <td>{data['compliant']}</td>
                    <td><span class="value {rate_class}">{compliance_rate:.1f}%</span></td>
                    <td>{data['average_score']:.1f}</td>
                </tr>
            """)
        
        html_parts.append("</tbody></table>")
        return "".join(html_parts)
    
    async def generate_json_report(self, report: ComplianceReport, 
                                 output_path: Optional[str] = None) -> str:
        """生成JSON格式报告"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"reports/api_compliance_report_{timestamp}.json"
        
        # 转换为可序列化的字典
        report_dict = {
            "total_endpoints": report.total_endpoints,
            "compliant_endpoints": report.compliant_endpoints,
            "non_compliant_endpoints": report.non_compliant_endpoints,
            "overall_score": report.overall_score,
            "generated_at": report.generated_at,
            "summary": report.summary,
            "results": []
        }
        
        for result in report.results:
            result_dict = {
                "endpoint": asdict(result.endpoint),
                "is_compliant": result.is_compliant,
                "score": result.score,
                "issues": [asdict(issue) for issue in result.issues],
                "response_sample": result.response_sample,
                "error_sample": result.error_sample
            }
            report_dict["results"].append(result_dict)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSON报告已生成: {output_path}")
        return output_path
    
    async def generate_markdown_report(self, report: ComplianceReport, 
                                     output_path: Optional[str] = None) -> str:
        """生成Markdown格式报告"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"reports/api_compliance_report_{timestamp}.md"
        
        md_content = f"""# API v2 合规性检查报告

**生成时间:** {report.generated_at}

## 概览

| 指标 | 数值 |
|------|------|
| 总端点数 | {report.total_endpoints} |
| 合规端点 | {report.compliant_endpoints} |
| 不合规端点 | {report.non_compliant_endpoints} |
| 合规率 | {report.summary.get('compliance_rate', '0%')} |
| 总体评分 | {report.overall_score:.1f} |

## 问题统计

### 按严重程度

| 严重程度 | 数量 |
|----------|------|
"""
        
        issues_by_severity = report.summary.get('issues_by_severity', {})
        for severity, count in issues_by_severity.items():
            md_content += f"| {severity.upper()} | {count} |\n"
        
        md_content += "\n### 按类别\n\n| 类别 | 数量 |\n|------|------|\n"
        
        issues_by_category = report.summary.get('issues_by_category', {})
        for category, count in issues_by_category.items():
            md_content += f"| {category} | {count} |\n"
        
        md_content += "\n## 常见问题\n\n"
        
        top_issues = report.summary.get('top_issues', [])
        for i, issue in enumerate(top_issues[:10], 1):
            md_content += f"""### {i}. {issue['message']}

- **严重程度:** {issue['severity'].upper()}
- **类别:** {issue['category']}
- **错误代码:** {issue['code']}
- **出现次数:** {issue['count']}
- **建议:** {issue.get('suggestion', '无')}

"""
        
        md_content += "\n## 端点详情\n\n"
        
        for result in report.results:
            endpoint = result.endpoint
            status = "✅ 合规" if result.is_compliant else "❌ 不合规"
            
            md_content += f"""### {endpoint.method} {endpoint.path}

- **状态:** {status}
- **评分:** {result.score}
- **模块:** {endpoint.module_path}
- **函数:** {endpoint.function_name}
"""
            
            if endpoint.summary:
                md_content += f"- **描述:** {endpoint.summary}\n"
            
            if result.issues:
                md_content += "\n**问题列表:**\n\n"
                for issue in result.issues:
                    md_content += f"- [{issue.severity.upper()}] {issue.message}\n"
                    if issue.suggestion:
                        md_content += f"  - 建议: {issue.suggestion}\n"
            
            md_content += "\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"Markdown报告已生成: {output_path}")
        return output_path


async def main():
    """主函数 - 演示完整的API合规性检查流程"""
    print("🚀 开始API v2合规性检查...")
    
    try:
        # 使用异步上下文管理器
        async with ApiComplianceChecker() as checker:
            # 执行合规性检查
            report = await checker.check_all_endpoints()
            
            # 生成报告
            report_generator = ComplianceReportGenerator()
            
            # 生成HTML报告
            html_path = await report_generator.generate_html_report(report)
            print(f"📊 HTML报告已生成: {html_path}")
            
            # 生成JSON报告
            json_path = await report_generator.generate_json_report(report)
            print(f"📄 JSON报告已生成: {json_path}")
            
            # 生成Markdown报告
            md_path = await report_generator.generate_markdown_report(report)
            print(f"📝 Markdown报告已生成: {md_path}")
            
            # 打印摘要
            print(f"\n📈 检查摘要:")
            print(f"   总端点数: {report.total_endpoints}")
            print(f"   合规端点: {report.compliant_endpoints}")
            print(f"   不合规端点: {report.non_compliant_endpoints}")
            print(f"   合规率: {report.summary.get('compliance_rate', '0%')}")
            print(f"   总体评分: {report.overall_score:.1f}")
            
            if report.non_compliant_endpoints > 0:
                print(f"\n⚠️  发现 {report.non_compliant_endpoints} 个不合规端点，请查看详细报告")
            else:
                print(f"\n✅ 所有API端点都符合v2格式标准！")
    
    except Exception as e:
        logger.error(f"合规性检查失败: {str(e)}")
        print(f"❌ 合规性检查失败: {str(e)}")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())