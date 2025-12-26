#!/usr/bin/env python3
"""
CRUD操作测试器
测试用户管理、角色管理、设备管理等页面的CRUD功能
验证创建、读取、更新、删除操作的正确性
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import argparse
import logging


@dataclass
class CrudTestCase:
    """CRUD测试用例"""
    name: str
    module: str
    api_base_url: str
    test_data: Dict[str, Any]
    expected_fields: List[str]
    required_fields: List[str]
    update_data: Dict[str, Any]
    search_params: Dict[str, Any]
    is_v2_api: bool = True


@dataclass
class CrudTestResult:
    """CRUD测试结果"""
    test_case: str
    module: str
    operation: str
    success: bool
    response_time: float
    status_code: int
    response_data: Optional[Dict]
    error_message: Optional[str]
    api_version: str
    compliance_issues: List[str]


@dataclass
class PageTestResult:
    """页面测试结果"""
    page_name: str
    module: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    test_results: List[CrudTestResult]
    issues: List[str]
    recommendations: List[str]
    api_version_compliance: str  # "v2", "v1", "mixed", "unknown"


@dataclass
class CrudTestReport:
    """CRUD测试报告"""
    total_pages: int
    total_tests: int
    passed_tests: int
    failed_tests: int
    v2_compliant_pages: int
    v1_legacy_pages: int
    mixed_pages: int
    page_results: List[PageTestResult]
    summary: Dict[str, Any]


class CrudOperationsTester:
    """CRUD操作测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000", token: str = None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = None
        
        # 配置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 定义测试用例
        self.test_cases = self._define_test_cases()
        
        # V2 API响应格式验证
        self.v2_required_fields = ['success', 'code', 'message', 'data']
        self.v2_pagination_fields = ['total', 'page', 'pageSize']

    def _define_test_cases(self) -> List[CrudTestCase]:
        """定义测试用例"""
        return [
            # 用户管理测试
            CrudTestCase(
                name="用户管理",
                module="system",
                api_base_url="/api/v2/users",
                test_data={
                    "username": f"test_user_{int(time.time())}",
                    "password": "Test123456",
                    "email": "test@example.com",
                    "phone": "13800138000",
                    "real_name": "测试用户",
                    "status": True,
                    "dept_id": 1,
                    "role_ids": [1]
                },
                expected_fields=["id", "username", "email", "real_name", "status"],
                required_fields=["username", "password", "email"],
                update_data={
                    "real_name": "更新测试用户",
                    "phone": "13900139000"
                },
                search_params={
                    "page": 1,
                    "pageSize": 10,
                    "username": "test"
                }
            ),
            
            # 角色管理测试
            CrudTestCase(
                name="角色管理",
                module="system",
                api_base_url="/api/v2/roles",
                test_data={
                    "role_name": f"test_role_{int(time.time())}",
                    "role_code": f"TEST_ROLE_{int(time.time())}",
                    "description": "测试角色",
                    "status": True,
                    "sort": 1
                },
                expected_fields=["id", "role_name", "role_code", "description", "status"],
                required_fields=["role_name", "role_code"],
                update_data={
                    "description": "更新测试角色",
                    "sort": 2
                },
                search_params={
                    "page": 1,
                    "pageSize": 10,
                    "role_name": "test"
                }
            ),
            
            # 菜单管理测试
            CrudTestCase(
                name="菜单管理",
                module="system",
                api_base_url="/api/v2/menus",
                test_data={
                    "menu_name": f"测试菜单_{int(time.time())}",
                    "menu_type": "M",
                    "path": f"/test-menu-{int(time.time())}",
                    "component": "TestMenu",
                    "visible": True,
                    "status": True,
                    "sort": 1,
                    "parent_id": 0
                },
                expected_fields=["id", "menu_name", "menu_type", "path", "visible", "status"],
                required_fields=["menu_name", "menu_type"],
                update_data={
                    "menu_name": "更新测试菜单",
                    "sort": 2
                },
                search_params={
                    "page": 1,
                    "pageSize": 10,
                    "menu_name": "测试"
                }
            ),
            
            # 部门管理测试
            CrudTestCase(
                name="部门管理",
                module="system",
                api_base_url="/api/v2/departments",
                test_data={
                    "dept_name": f"测试部门_{int(time.time())}",
                    "dept_code": f"TEST_DEPT_{int(time.time())}",
                    "description": "测试部门",
                    "status": True,
                    "sort": 1,
                    "parent_id": 0
                },
                expected_fields=["id", "dept_name", "dept_code", "description", "status"],
                required_fields=["dept_name", "dept_code"],
                update_data={
                    "description": "更新测试部门",
                    "sort": 2
                },
                search_params={
                    "page": 1,
                    "pageSize": 10,
                    "dept_name": "测试"
                }
            ),
            
            # 设备类型管理测试
            CrudTestCase(
                name="设备类型管理",
                module="device",
                api_base_url="/api/v2/device-types",
                test_data={
                    "type_code": f"TEST_TYPE_{int(time.time())}",
                    "type_name": f"测试设备类型_{int(time.time())}",
                    "description": "测试设备类型",
                    "status": True,
                    "sort": 1
                },
                expected_fields=["type_code", "type_name", "description", "status"],
                required_fields=["type_code", "type_name"],
                update_data={
                    "description": "更新测试设备类型",
                    "sort": 2
                },
                search_params={
                    "page": 1,
                    "pageSize": 10,
                    "type_name": "测试"
                }
            ),
            
            # 设备管理测试
            CrudTestCase(
                name="设备管理",
                module="device",
                api_base_url="/api/v2/devices",
                test_data={
                    "device_name": f"测试设备_{int(time.time())}",
                    "device_code": f"TEST_DEVICE_{int(time.time())}",
                    "device_type": "welding",
                    "manufacturer": "测试厂商",
                    "device_model": "TEST-001",
                    "online_address": "192.168.1.100",
                    "status": True
                },
                expected_fields=["id", "device_name", "device_code", "device_type", "status"],
                required_fields=["device_name", "device_code", "device_type"],
                update_data={
                    "manufacturer": "更新测试厂商",
                    "device_model": "TEST-002"
                },
                search_params={
                    "page": 1,
                    "pageSize": 10,
                    "device_name": "测试"
                }
            )
        ]

    async def create_session(self):
        """创建HTTP会话"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30)
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            connector=connector,
            timeout=timeout
        )

    async def close_session(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()

    async def test_create_operation(self, test_case: CrudTestCase) -> CrudTestResult:
        """测试创建操作"""
        start_time = time.time()
        
        try:
            url = f"{self.base_url}{test_case.api_base_url}"
            
            async with self.session.post(url, json=test_case.test_data) as response:
                response_time = time.time() - start_time
                response_data = await response.json()
                
                # 验证响应格式
                compliance_issues = self._check_v2_compliance(response_data, "create")
                
                # 验证必需字段
                if response.status == 200 or response.status == 201:
                    if 'data' in response_data and response_data['data']:
                        data = response_data['data']
                        for field in test_case.expected_fields:
                            if field not in data:
                                compliance_issues.append(f"响应数据缺少字段: {field}")
                
                return CrudTestResult(
                    test_case=test_case.name,
                    module=test_case.module,
                    operation="create",
                    success=response.status in [200, 201],
                    response_time=response_time,
                    status_code=response.status,
                    response_data=response_data,
                    error_message=None if response.status in [200, 201] else response_data.get('message', 'Unknown error'),
                    api_version="v2" if test_case.is_v2_api else "v1",
                    compliance_issues=compliance_issues
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            return CrudTestResult(
                test_case=test_case.name,
                module=test_case.module,
                operation="create",
                success=False,
                response_time=response_time,
                status_code=0,
                response_data=None,
                error_message=str(e),
                api_version="v2" if test_case.is_v2_api else "v1",
                compliance_issues=["请求异常"]
            )

    async def test_read_operation(self, test_case: CrudTestCase, created_id: Any = None) -> CrudTestResult:
        """测试读取操作"""
        start_time = time.time()
        
        try:
            # 测试列表查询
            url = f"{self.base_url}{test_case.api_base_url}"
            params = test_case.search_params
            
            async with self.session.get(url, params=params) as response:
                response_time = time.time() - start_time
                response_data = await response.json()
                
                # 验证响应格式
                compliance_issues = self._check_v2_compliance(response_data, "list")
                
                # 验证分页字段
                if response.status == 200 and 'data' in response_data:
                    data = response_data['data']
                    if isinstance(data, dict) and 'items' in data:
                        # 分页格式
                        for field in self.v2_pagination_fields:
                            if field not in data:
                                compliance_issues.append(f"分页数据缺少字段: {field}")
                
                return CrudTestResult(
                    test_case=test_case.name,
                    module=test_case.module,
                    operation="read",
                    success=response.status == 200,
                    response_time=response_time,
                    status_code=response.status,
                    response_data=response_data,
                    error_message=None if response.status == 200 else response_data.get('message', 'Unknown error'),
                    api_version="v2" if test_case.is_v2_api else "v1",
                    compliance_issues=compliance_issues
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            return CrudTestResult(
                test_case=test_case.name,
                module=test_case.module,
                operation="read",
                success=False,
                response_time=response_time,
                status_code=0,
                response_data=None,
                error_message=str(e),
                api_version="v2" if test_case.is_v2_api else "v1",
                compliance_issues=["请求异常"]
            )

    async def test_update_operation(self, test_case: CrudTestCase, created_id: Any) -> CrudTestResult:
        """测试更新操作"""
        if not created_id:
            return CrudTestResult(
                test_case=test_case.name,
                module=test_case.module,
                operation="update",
                success=False,
                response_time=0,
                status_code=0,
                response_data=None,
                error_message="没有可更新的记录ID",
                api_version="v2" if test_case.is_v2_api else "v1",
                compliance_issues=["缺少记录ID"]
            )
        
        start_time = time.time()
        
        try:
            url = f"{self.base_url}{test_case.api_base_url}/{created_id}"
            
            async with self.session.put(url, json=test_case.update_data) as response:
                response_time = time.time() - start_time
                response_data = await response.json()
                
                # 验证响应格式
                compliance_issues = self._check_v2_compliance(response_data, "update")
                
                return CrudTestResult(
                    test_case=test_case.name,
                    module=test_case.module,
                    operation="update",
                    success=response.status == 200,
                    response_time=response_time,
                    status_code=response.status,
                    response_data=response_data,
                    error_message=None if response.status == 200 else response_data.get('message', 'Unknown error'),
                    api_version="v2" if test_case.is_v2_api else "v1",
                    compliance_issues=compliance_issues
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            return CrudTestResult(
                test_case=test_case.name,
                module=test_case.module,
                operation="update",
                success=False,
                response_time=response_time,
                status_code=0,
                response_data=None,
                error_message=str(e),
                api_version="v2" if test_case.is_v2_api else "v1",
                compliance_issues=["请求异常"]
            )

    async def test_delete_operation(self, test_case: CrudTestCase, created_id: Any) -> CrudTestResult:
        """测试删除操作"""
        if not created_id:
            return CrudTestResult(
                test_case=test_case.name,
                module=test_case.module,
                operation="delete",
                success=False,
                response_time=0,
                status_code=0,
                response_data=None,
                error_message="没有可删除的记录ID",
                api_version="v2" if test_case.is_v2_api else "v1",
                compliance_issues=["缺少记录ID"]
            )
        
        start_time = time.time()
        
        try:
            url = f"{self.base_url}{test_case.api_base_url}/{created_id}"
            
            async with self.session.delete(url) as response:
                response_time = time.time() - start_time
                response_data = await response.json()
                
                # 验证响应格式
                compliance_issues = self._check_v2_compliance(response_data, "delete")
                
                return CrudTestResult(
                    test_case=test_case.name,
                    module=test_case.module,
                    operation="delete",
                    success=response.status == 200,
                    response_time=response_time,
                    status_code=response.status,
                    response_data=response_data,
                    error_message=None if response.status == 200 else response_data.get('message', 'Unknown error'),
                    api_version="v2" if test_case.is_v2_api else "v1",
                    compliance_issues=compliance_issues
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            return CrudTestResult(
                test_case=test_case.name,
                module=test_case.module,
                operation="delete",
                success=False,
                response_time=response_time,
                status_code=0,
                response_data=None,
                error_message=str(e),
                api_version="v2" if test_case.is_v2_api else "v1",
                compliance_issues=["请求异常"]
            )

    def _check_v2_compliance(self, response_data: Dict, operation: str) -> List[str]:
        """检查V2 API合规性"""
        issues = []
        
        if not isinstance(response_data, dict):
            issues.append("响应数据不是JSON对象")
            return issues
        
        # 检查必需字段
        for field in self.v2_required_fields:
            if field not in response_data:
                issues.append(f"缺少必需字段: {field}")
        
        # 检查success字段类型
        if 'success' in response_data and not isinstance(response_data['success'], bool):
            issues.append("success字段应该是布尔类型")
        
        # 检查code字段类型
        if 'code' in response_data and not isinstance(response_data['code'], int):
            issues.append("code字段应该是整数类型")
        
        # 检查message字段类型
        if 'message' in response_data and not isinstance(response_data['message'], str):
            issues.append("message字段应该是字符串类型")
        
        return issues

    async def test_page_crud_operations(self, test_case: CrudTestCase) -> PageTestResult:
        """测试页面的CRUD操作"""
        self.logger.info(f"开始测试 {test_case.name} 的CRUD操作")
        
        test_results = []
        created_id = None
        
        # 1. 测试创建操作
        create_result = await self.test_create_operation(test_case)
        test_results.append(create_result)
        
        # 提取创建的记录ID
        if create_result.success and create_result.response_data:
            data = create_result.response_data.get('data')
            if isinstance(data, dict):
                created_id = data.get('id') or data.get(test_case.expected_fields[0])
        
        # 2. 测试读取操作
        read_result = await self.test_read_operation(test_case, created_id)
        test_results.append(read_result)
        
        # 3. 测试更新操作
        if created_id:
            update_result = await self.test_update_operation(test_case, created_id)
            test_results.append(update_result)
        
        # 4. 测试删除操作
        if created_id:
            delete_result = await self.test_delete_operation(test_case, created_id)
            test_results.append(delete_result)
        
        # 统计结果
        passed_tests = sum(1 for result in test_results if result.success)
        failed_tests = len(test_results) - passed_tests
        
        # 收集问题和建议
        issues = []
        recommendations = []
        
        # 检查API版本一致性
        api_versions = set(result.api_version for result in test_results)
        if len(api_versions) > 1:
            issues.append("CRUD操作使用了不同版本的API")
            recommendations.append("统一使用V2 API")
        
        # 检查合规性问题
        all_compliance_issues = []
        for result in test_results:
            all_compliance_issues.extend(result.compliance_issues)
        
        if all_compliance_issues:
            issues.extend(set(all_compliance_issues))
            recommendations.append("修复API响应格式合规性问题")
        
        # 检查失败的操作
        failed_operations = [result.operation for result in test_results if not result.success]
        if failed_operations:
            issues.append(f"以下操作失败: {', '.join(failed_operations)}")
            recommendations.append("检查API实现和数据库配置")
        
        # 确定API版本合规性
        api_version_compliance = "unknown"
        if api_versions:
            if api_versions == {"v2"}:
                api_version_compliance = "v2"
            elif api_versions == {"v1"}:
                api_version_compliance = "v1"
            else:
                api_version_compliance = "mixed"
        
        return PageTestResult(
            page_name=test_case.name,
            module=test_case.module,
            total_tests=len(test_results),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            test_results=test_results,
            issues=issues,
            recommendations=recommendations,
            api_version_compliance=api_version_compliance
        )

    async def run_all_tests(self) -> CrudTestReport:
        """运行所有测试"""
        self.logger.info("开始运行CRUD操作测试")
        
        await self.create_session()
        
        try:
            page_results = []
            
            for test_case in self.test_cases:
                try:
                    page_result = await self.test_page_crud_operations(test_case)
                    page_results.append(page_result)
                    
                    # 添加延迟避免请求过快
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"测试 {test_case.name} 时出现异常: {str(e)}")
                    # 创建失败的测试结果
                    page_result = PageTestResult(
                        page_name=test_case.name,
                        module=test_case.module,
                        total_tests=0,
                        passed_tests=0,
                        failed_tests=1,
                        test_results=[],
                        issues=[f"测试异常: {str(e)}"],
                        recommendations=["检查API服务是否正常运行"],
                        api_version_compliance="unknown"
                    )
                    page_results.append(page_result)
            
            # 生成报告
            report = self._generate_report(page_results)
            
            return report
            
        finally:
            await self.close_session()

    def _generate_report(self, page_results: List[PageTestResult]) -> CrudTestReport:
        """生成测试报告"""
        total_pages = len(page_results)
        total_tests = sum(result.total_tests for result in page_results)
        passed_tests = sum(result.passed_tests for result in page_results)
        failed_tests = sum(result.failed_tests for result in page_results)
        
        v2_compliant_pages = sum(1 for result in page_results if result.api_version_compliance == "v2")
        v1_legacy_pages = sum(1 for result in page_results if result.api_version_compliance == "v1")
        mixed_pages = sum(1 for result in page_results if result.api_version_compliance == "mixed")
        
        # 生成汇总信息
        summary = {
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "v2_compliance_rate": (v2_compliant_pages / total_pages * 100) if total_pages > 0 else 0,
            "avg_response_time": self._calculate_avg_response_time(page_results),
            "common_issues": self._get_common_issues(page_results),
            "module_performance": self._get_module_performance(page_results)
        }
        
        return CrudTestReport(
            total_pages=total_pages,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            v2_compliant_pages=v2_compliant_pages,
            v1_legacy_pages=v1_legacy_pages,
            mixed_pages=mixed_pages,
            page_results=page_results,
            summary=summary
        )

    def _calculate_avg_response_time(self, page_results: List[PageTestResult]) -> float:
        """计算平均响应时间"""
        all_times = []
        for page_result in page_results:
            for test_result in page_result.test_results:
                all_times.append(test_result.response_time)
        
        return sum(all_times) / len(all_times) if all_times else 0

    def _get_common_issues(self, page_results: List[PageTestResult]) -> List[Dict[str, Any]]:
        """获取常见问题"""
        issue_counts = {}
        
        for page_result in page_results:
            for issue in page_result.issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        # 按出现频率排序
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {"issue": issue, "count": count, "percentage": count / len(page_results) * 100}
            for issue, count in sorted_issues[:10]
        ]

    def _get_module_performance(self, page_results: List[PageTestResult]) -> Dict[str, Dict[str, Any]]:
        """获取模块性能统计"""
        module_stats = {}
        
        for page_result in page_results:
            module = page_result.module
            if module not in module_stats:
                module_stats[module] = {
                    "total_tests": 0,
                    "passed_tests": 0,
                    "failed_tests": 0,
                    "avg_response_time": 0,
                    "pages": []
                }
            
            stats = module_stats[module]
            stats["total_tests"] += page_result.total_tests
            stats["passed_tests"] += page_result.passed_tests
            stats["failed_tests"] += page_result.failed_tests
            stats["pages"].append(page_result.page_name)
            
            # 计算平均响应时间
            response_times = [result.response_time for result in page_result.test_results]
            if response_times:
                stats["avg_response_time"] = sum(response_times) / len(response_times)
        
        return module_stats

    def save_report(self, report: CrudTestReport, output_file: str):
        """保存报告"""
        report_data = asdict(report)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

    def generate_html_report(self, report: CrudTestReport, output_file: str):
        """生成HTML报告"""
        html_content = self._generate_html_content(report)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _generate_html_content(self, report: CrudTestReport) -> str:
        """生成HTML内容"""
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CRUD操作测试报告</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1, h2, h3 {{ color: #333; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
        .summary-card {{ background: #f8f9fa; padding: 20px; border-radius: 6px; border-left: 4px solid #007bff; }}
        .summary-card h3 {{ margin: 0 0 10px 0; color: #007bff; }}
        .summary-card .value {{ font-size: 2em; font-weight: bold; color: #333; }}
        .summary-card .label {{ color: #666; font-size: 0.9em; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; font-weight: 600; }}
        .status-success {{ color: #28a745; font-weight: bold; }}
        .status-failed {{ color: #dc3545; font-weight: bold; }}
        .status-v2 {{ color: #28a745; font-weight: bold; }}
        .status-v1 {{ color: #ffc107; font-weight: bold; }}
        .status-mixed {{ color: #dc3545; font-weight: bold; }}
        .progress-bar {{ width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #28a745, #20c997); }}
        .test-detail {{ margin: 10px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .operation-result {{ display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.8em; margin: 2px; }}
        .operation-success {{ background: #d4edda; color: #155724; }}
        .operation-failed {{ background: #f8d7da; color: #721c24; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>CRUD操作测试报告</h1>
        <p>生成时间: {self._get_current_time()}</p>
        
        <div class="summary">
            <div class="summary-card">
                <h3>总测试数</h3>
                <div class="value">{report.total_tests}</div>
                <div class="label">{report.total_pages} 个页面</div>
            </div>
            <div class="summary-card">
                <h3>成功率</h3>
                <div class="value">{report.summary['success_rate']:.1f}%</div>
                <div class="label">{report.passed_tests}/{report.total_tests} 通过</div>
            </div>
            <div class="summary-card">
                <h3>V2合规率</h3>
                <div class="value">{report.summary['v2_compliance_rate']:.1f}%</div>
                <div class="label">{report.v2_compliant_pages} 个页面使用V2</div>
            </div>
            <div class="summary-card">
                <h3>平均响应时间</h3>
                <div class="value">{report.summary['avg_response_time']:.2f}s</div>
                <div class="label">所有操作平均</div>
            </div>
        </div>
        
        <h2>测试结果概览</h2>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {report.summary['success_rate']:.1f}%"></div>
        </div>
        <p>测试通过率: {report.summary['success_rate']:.1f}% ({report.passed_tests}/{report.total_tests})</p>
        
        <h2>模块性能统计</h2>
        <table>
            <thead>
                <tr>
                    <th>模块</th>
                    <th>页面数</th>
                    <th>测试数</th>
                    <th>通过率</th>
                    <th>平均响应时间</th>
                </tr>
            </thead>
            <tbody>
                {self._generate_module_table_rows(report.summary['module_performance'])}
            </tbody>
        </table>
        
        <h2>常见问题</h2>
        <table>
            <thead>
                <tr>
                    <th>问题描述</th>
                    <th>影响页面数</th>
                    <th>占比</th>
                </tr>
            </thead>
            <tbody>
                {self._generate_issues_table_rows(report.summary['common_issues'])}
            </tbody>
        </table>
        
        <h2>详细测试结果</h2>
        {self._generate_detailed_results(report.page_results)}
    </div>
</body>
</html>
        """

    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _generate_module_table_rows(self, module_performance: Dict) -> str:
        """生成模块表格行"""
        rows = []
        for module, stats in module_performance.items():
            success_rate = (stats['passed_tests'] / stats['total_tests'] * 100) if stats['total_tests'] > 0 else 0
            rows.append(f"""
                <tr>
                    <td>{module}</td>
                    <td>{len(stats['pages'])}</td>
                    <td>{stats['total_tests']}</td>
                    <td>{success_rate:.1f}%</td>
                    <td>{stats['avg_response_time']:.2f}s</td>
                </tr>
            """)
        return "".join(rows)

    def _generate_issues_table_rows(self, issues: List[Dict]) -> str:
        """生成问题表格行"""
        rows = []
        for issue in issues:
            rows.append(f"""
                <tr>
                    <td>{issue['issue']}</td>
                    <td>{issue['count']}</td>
                    <td>{issue['percentage']:.1f}%</td>
                </tr>
            """)
        return "".join(rows)

    def _generate_detailed_results(self, page_results: List[PageTestResult]) -> str:
        """生成详细结果"""
        details = []
        
        for page_result in page_results:
            success_rate = (page_result.passed_tests / page_result.total_tests * 100) if page_result.total_tests > 0 else 0
            
            # 操作结果
            operations_html = ""
            for test_result in page_result.test_results:
                status_class = "operation-success" if test_result.success else "operation-failed"
                operations_html += f'<span class="{status_class}">{test_result.operation}</span>'
            
            # API版本状态
            version_class = f"status-{page_result.api_version_compliance}"
            
            details.append(f"""
                <div class="test-detail">
                    <h3>{page_result.page_name} ({page_result.module}) 
                        <span class="{version_class}">[{page_result.api_version_compliance.upper()}]</span>
                    </h3>
                    <p>测试通过率: {success_rate:.1f}% ({page_result.passed_tests}/{page_result.total_tests})</p>
                    <p>操作结果: {operations_html}</p>
                    
                    {self._generate_issues_section(page_result.issues)}
                    {self._generate_recommendations_section(page_result.recommendations)}
                </div>
            """)
        
        return "".join(details)

    def _generate_issues_section(self, issues: List[str]) -> str:
        """生成问题部分"""
        if not issues:
            return ""
        
        issues_html = "<div style='background: #fff3cd; padding: 10px; border-radius: 4px; margin: 5px 0;'>"
        issues_html += "<strong>问题:</strong><ul>"
        for issue in issues:
            issues_html += f"<li>{issue}</li>"
        issues_html += "</ul></div>"
        return issues_html

    def _generate_recommendations_section(self, recommendations: List[str]) -> str:
        """生成建议部分"""
        if not recommendations:
            return ""
        
        rec_html = "<div style='background: #d1ecf1; padding: 10px; border-radius: 4px; margin: 5px 0;'>"
        rec_html += "<strong>建议:</strong><ul>"
        for rec in recommendations:
            rec_html += f"<li>{rec}</li>"
        rec_html += "</ul></div>"
        return rec_html


async def main():
    parser = argparse.ArgumentParser(description='CRUD操作测试器')
    parser.add_argument('--base-url', default='http://localhost:8000', help='API基础URL')
    parser.add_argument('--token', help='认证令牌')
    parser.add_argument('--output', default='crud_test_report.json', help='输出JSON报告文件')
    parser.add_argument('--html-output', default='crud_test_report.html', help='输出HTML报告文件')
    
    args = parser.parse_args()
    
    tester = CrudOperationsTester(args.base_url, args.token)
    
    try:
        report = await tester.run_all_tests()
        
        # 保存报告
        tester.save_report(report, args.output)
        tester.generate_html_report(report, args.html_output)
        
        print(f"测试完成！")
        print(f"总测试数: {report.total_tests}")
        print(f"通过: {report.passed_tests}")
        print(f"失败: {report.failed_tests}")
        print(f"成功率: {report.summary['success_rate']:.1f}%")
        print(f"V2合规页面: {report.v2_compliant_pages}/{report.total_pages}")
        print(f"报告已保存到: {args.output} 和 {args.html_output}")
        
        return 0
        
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))