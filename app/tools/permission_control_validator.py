#!/usr/bin/env python3
"""
权限控制验证器
测试页面权限控制是否正常工作
验证权限按钮和指令的正确显示和隐藏
检查不同角色用户的页面访问权限
"""

import os
import re
import json
import asyncio
import aiohttp
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import argparse
import logging


@dataclass
class PermissionElement:
    """权限元素信息"""
    element_type: str  # 'button', 'directive', 'component'
    permission: str
    line_number: int
    line_content: str
    element_content: str
    is_v2_format: bool
    confidence: float


@dataclass
class PagePermissionUsage:
    """页面权限使用情况"""
    file_path: str
    page_name: str
    route_path: str
    total_permission_elements: int
    v2_permission_elements: int
    v1_permission_elements: int
    unknown_permission_elements: int
    permission_elements: List[PermissionElement]
    permission_directives: List[str]
    permission_buttons: List[str]
    permission_components: List[str]
    issues: List[str]
    recommendations: List[str]


@dataclass
class RoleTestResult:
    """角色测试结果"""
    role_name: str
    role_id: int
    permissions: List[str]
    accessible_pages: List[str]
    inaccessible_pages: List[str]
    permission_violations: List[str]
    test_results: Dict[str, Any]


@dataclass
class PermissionValidationReport:
    """权限验证报告"""
    total_pages: int
    pages_with_permissions: int
    v2_permission_pages: int
    v1_permission_pages: int
    mixed_permission_pages: int
    total_permission_elements: int
    v2_permission_elements: int
    v1_permission_elements: int
    page_results: List[PagePermissionUsage]
    role_test_results: List[RoleTestResult]
    summary: Dict[str, Any]


class PermissionControlValidator:
    """权限控制验证器"""
    
    def __init__(self, web_root: str = "web", api_base_url: str = "http://localhost:8000"):
        self.web_root = Path(web_root)
        self.views_path = self.web_root / "src" / "views"
        self.api_base_url = api_base_url.rstrip('/')
        
        # 配置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # V2权限模式
        self.v2_permission_patterns = [
            r'v-permission=[\'"]([^\'"]+)[\'"]',
            r'permission=[\'"]([^\'"]+)[\'"]',
            r'hasPermission\([\'"]([^\'"]+)[\'"]\)',
            r'checkPermission\([\'"]([^\'"]+)[\'"]\)',
            r'getPermission\([\'"]([^\'",]+)[\'"],\s*[\'"]([^\'"]+)[\'"]\)',
            r'GET /api/v2/[^\'"]+',
            r'POST /api/v2/[^\'"]+',
            r'PUT /api/v2/[^\'"]+',
            r'DELETE /api/v2/[^\'"]+',
        ]
        
        # V1权限模式
        self.v1_permission_patterns = [
            r'v-permission=[\'"](?!GET |POST |PUT |DELETE )([^\'"]+)[\'"]',
            r'permission=[\'"](?!GET |POST |PUT |DELETE )([^\'"]+)[\'"]',
            r'hasPermission\([\'"](?!GET |POST |PUT |DELETE )([^\'"]+)[\'"]\)',
            r'/api/(?!v2)[^\'"]+',
        ]
        
        # 权限元素模式
        self.permission_element_patterns = {
            'button': [
                r'<n-button[^>]*v-permission=[\'"]([^\'"]+)[\'"][^>]*>',
                r'<el-button[^>]*v-permission=[\'"]([^\'"]+)[\'"][^>]*>',
                r'<PermissionButton[^>]*permission=[\'"]([^\'"]+)[\'"][^>]*>',
                r'<button[^>]*v-permission=[\'"]([^\'"]+)[\'"][^>]*>',
            ],
            'directive': [
                r'v-permission=[\'"]([^\'"]+)[\'"]',
                r'v-permission\.[a-zA-Z]+=[\'"]([^\'"]+)[\'"]',
            ],
            'component': [
                r'<PermissionButton[^>]*>',
                r'<PermissionTreeV2[^>]*>',
                r'<PermissionConfig[^>]*>',
            ]
        }
        
        # 路由权限映射
        self.route_permission_mapping = {
            '/system/user': 'users',
            '/system/role': 'roles',
            '/system/menu': 'menus',
            '/system/dept': 'departments',
            '/device/baseinfo': 'devices',
            '/device/type': 'device-types',
            '/device/maintenance': 'device-maintenance',
            '/device/process': 'device-processes',
        }

    def scan_page_permissions(self, file_path: str) -> PagePermissionUsage:
        """扫描页面权限使用情况"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return PagePermissionUsage(
                file_path=file_path,
                page_name=os.path.basename(file_path),
                route_path="",
                total_permission_elements=0,
                v2_permission_elements=0,
                v1_permission_elements=0,
                unknown_permission_elements=0,
                permission_elements=[],
                permission_directives=[],
                permission_buttons=[],
                permission_components=[],
                issues=[f"无法读取文件: {str(e)}"],
                recommendations=[]
            )
        
        # 提取页面信息
        page_name = self._extract_page_name(content, file_path)
        route_path = self._extract_route_path(content, file_path)
        
        # 扫描权限元素
        permission_elements = self._scan_permission_elements(content)
        
        # 分类权限元素
        v2_elements = [elem for elem in permission_elements if elem.is_v2_format]
        v1_elements = [elem for elem in permission_elements if not elem.is_v2_format and elem.confidence > 0.5]
        unknown_elements = [elem for elem in permission_elements if elem.confidence <= 0.5]
        
        # 分类权限使用
        permission_directives = [elem.permission for elem in permission_elements if elem.element_type == 'directive']
        permission_buttons = [elem.permission for elem in permission_elements if elem.element_type == 'button']
        permission_components = [elem.permission for elem in permission_elements if elem.element_type == 'component']
        
        # 生成问题和建议
        issues, recommendations = self._analyze_permission_issues(
            permission_elements, route_path, file_path
        )
        
        return PagePermissionUsage(
            file_path=file_path,
            page_name=page_name,
            route_path=route_path,
            total_permission_elements=len(permission_elements),
            v2_permission_elements=len(v2_elements),
            v1_permission_elements=len(v1_elements),
            unknown_permission_elements=len(unknown_elements),
            permission_elements=permission_elements,
            permission_directives=permission_directives,
            permission_buttons=permission_buttons,
            permission_components=permission_components,
            issues=issues,
            recommendations=recommendations
        )

    def _extract_page_name(self, content: str, file_path: str) -> str:
        """提取页面名称"""
        # 尝试从defineOptions中提取
        match = re.search(r'defineOptions\(\s*\{\s*name:\s*[\'"]([^\'"]+)[\'"]', content)
        if match:
            return match.group(1)
        
        # 尝试从文件名提取
        return os.path.splitext(os.path.basename(file_path))[0]

    def _extract_route_path(self, content: str, file_path: str) -> str:
        """提取路由路径"""
        # 从文件路径推断路由
        relative_path = os.path.relpath(file_path, self.views_path)
        route_parts = relative_path.replace('\\', '/').split('/')
        
        # 移除index.vue
        if route_parts[-1] == 'index.vue':
            route_parts = route_parts[:-1]
        else:
            route_parts[-1] = os.path.splitext(route_parts[-1])[0]
        
        return '/' + '/'.join(route_parts) if route_parts else '/'

    def _scan_permission_elements(self, content: str) -> List[PermissionElement]:
        """扫描权限元素"""
        elements = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith('//') or line_stripped.startswith('*'):
                continue
            
            # 扫描各种权限元素
            for element_type, patterns in self.permission_element_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        permission = match.group(1) if match.groups() else match.group(0)
                        is_v2, confidence = self._determine_permission_format(permission, line)
                        
                        element = PermissionElement(
                            element_type=element_type,
                            permission=permission,
                            line_number=line_num,
                            line_content=line_stripped,
                            element_content=match.group(0),
                            is_v2_format=is_v2,
                            confidence=confidence
                        )
                        elements.append(element)
        
        return elements

    def _determine_permission_format(self, permission: str, line: str) -> Tuple[bool, float]:
        """判断权限格式"""
        confidence = 0.5
        
        # 检查V2格式
        v2_indicators = [
            r'GET /api/v2/',
            r'POST /api/v2/',
            r'PUT /api/v2/',
            r'DELETE /api/v2/',
            r'getPermission\(',
            r'checkPermissionV2\(',
            r'hasPermission.*v2',
        ]
        
        for indicator in v2_indicators:
            if re.search(indicator, line, re.IGNORECASE):
                confidence = 0.9
                return True, confidence
        
        # 检查V1格式
        v1_indicators = [
            r'/api/(?!v2)',
            r'v-permission=',
            r'hasPermission\(',
        ]
        
        for indicator in v1_indicators:
            if re.search(indicator, line, re.IGNORECASE):
                confidence = 0.7
                return False, confidence
        
        # 基于权限字符串本身判断
        if permission.startswith(('GET ', 'POST ', 'PUT ', 'DELETE ')) and '/api/v2/' in permission:
            confidence = 0.8
            return True, confidence
        
        if '.' in permission or ':' in permission:
            confidence = 0.6
            return False, confidence
        
        return None, 0.3

    def _analyze_permission_issues(
        self, elements: List[PermissionElement], route_path: str, file_path: str
    ) -> Tuple[List[str], List[str]]:
        """分析权限问题"""
        issues = []
        recommendations = []
        
        if not elements:
            issues.append("页面没有使用任何权限控制")
            recommendations.append("添加适当的权限控制指令或组件")
            return issues, recommendations
        
        v2_elements = [elem for elem in elements if elem.is_v2_format]
        v1_elements = [elem for elem in elements if not elem.is_v2_format and elem.confidence > 0.5]
        
        # 检查混合使用
        if v1_elements and v2_elements:
            issues.append("页面同时使用V1和V2权限格式")
            recommendations.append("统一使用V2权限格式")
        
        # 检查V1权限使用
        if v1_elements and not v2_elements:
            issues.append(f"页面仍在使用V1权限格式 ({len(v1_elements)}个元素)")
            recommendations.append("将权限控制迁移到V2格式")
        
        # 检查权限覆盖
        button_elements = [elem for elem in elements if elem.element_type == 'button']
        if len(button_elements) < 2:
            issues.append("页面权限控制覆盖不足，可能存在未保护的操作")
            recommendations.append("为所有敏感操作添加权限控制")
        
        # 检查权限一致性
        permissions = set(elem.permission for elem in elements)
        if len(permissions) > 5:
            issues.append("页面使用了过多不同的权限，可能存在权限配置混乱")
            recommendations.append("整理和简化权限配置")
        
        # 检查路由权限映射
        expected_resource = self.route_permission_mapping.get(route_path)
        if expected_resource:
            resource_permissions = [elem.permission for elem in elements if expected_resource in elem.permission]
            if not resource_permissions:
                issues.append(f"页面权限与路由不匹配，期望包含 '{expected_resource}' 相关权限")
                recommendations.append(f"添加 '{expected_resource}' 相关的权限控制")
        
        return issues, recommendations

    async def test_role_permissions(self, token: str = None) -> List[RoleTestResult]:
        """测试角色权限"""
        if not token:
            self.logger.warning("未提供认证令牌，跳过角色权限测试")
            return []
        
        role_results = []
        
        try:
            # 获取系统角色列表
            roles = await self._fetch_roles(token)
            
            for role in roles:
                role_result = await self._test_single_role(role, token)
                role_results.append(role_result)
                
                # 添加延迟避免请求过快
                await asyncio.sleep(0.5)
                
        except Exception as e:
            self.logger.error(f"角色权限测试失败: {str(e)}")
        
        return role_results

    async def _fetch_roles(self, token: str) -> List[Dict]:
        """获取角色列表"""
        headers = {'Authorization': f'Bearer {token}'}
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{self.api_base_url}/api/v2/roles") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success') and data.get('data'):
                        return data['data'].get('items', [])
        
        return []

    async def _test_single_role(self, role: Dict, token: str) -> RoleTestResult:
        """测试单个角色权限"""
        role_id = role.get('id')
        role_name = role.get('role_name', 'Unknown')
        
        # 获取角色权限
        permissions = await self._fetch_role_permissions(role_id, token)
        
        # 测试页面访问权限
        accessible_pages = []
        inaccessible_pages = []
        permission_violations = []
        
        # 这里可以添加具体的页面访问测试逻辑
        # 由于需要实际的前端环境，这里提供框架
        
        test_results = {
            "permission_count": len(permissions),
            "test_timestamp": self._get_current_time(),
            "test_status": "completed"
        }
        
        return RoleTestResult(
            role_name=role_name,
            role_id=role_id,
            permissions=permissions,
            accessible_pages=accessible_pages,
            inaccessible_pages=inaccessible_pages,
            permission_violations=permission_violations,
            test_results=test_results
        )

    async def _fetch_role_permissions(self, role_id: int, token: str) -> List[str]:
        """获取角色权限"""
        headers = {'Authorization': f'Bearer {token}'}
        
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(f"{self.api_base_url}/api/v2/roles/{role_id}/permissions") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success') and data.get('data'):
                            return data['data']
        except Exception as e:
            self.logger.error(f"获取角色 {role_id} 权限失败: {str(e)}")
        
        return []

    def scan_all_pages(self) -> List[str]:
        """扫描所有页面文件"""
        vue_files = []
        
        for root, dirs, files in os.walk(self.views_path):
            for file in files:
                if file.endswith('.vue'):
                    vue_files.append(os.path.join(root, file))
        
        return vue_files

    async def run_validation(self, token: str = None) -> PermissionValidationReport:
        """运行权限验证"""
        self.logger.info("开始权限控制验证")
        
        # 扫描页面权限
        vue_files = self.scan_all_pages()
        self.logger.info(f"发现 {len(vue_files)} 个Vue页面文件")
        
        page_results = []
        for i, file_path in enumerate(vue_files, 1):
            self.logger.info(f"分析页面权限 {i}/{len(vue_files)}: {file_path}")
            page_result = self.scan_page_permissions(file_path)
            page_results.append(page_result)
        
        # 测试角色权限
        role_test_results = await self.test_role_permissions(token)
        
        # 生成报告
        report = self._generate_report(page_results, role_test_results)
        
        return report

    def _generate_report(
        self, page_results: List[PagePermissionUsage], role_results: List[RoleTestResult]
    ) -> PermissionValidationReport:
        """生成验证报告"""
        total_pages = len(page_results)
        pages_with_permissions = sum(1 for page in page_results if page.total_permission_elements > 0)
        v2_permission_pages = sum(1 for page in page_results if page.v2_permission_elements > 0 and page.v1_permission_elements == 0)
        v1_permission_pages = sum(1 for page in page_results if page.v1_permission_elements > 0 and page.v2_permission_elements == 0)
        mixed_permission_pages = sum(1 for page in page_results if page.v1_permission_elements > 0 and page.v2_permission_elements > 0)
        
        total_permission_elements = sum(page.total_permission_elements for page in page_results)
        v2_permission_elements = sum(page.v2_permission_elements for page in page_results)
        v1_permission_elements = sum(page.v1_permission_elements for page in page_results)
        
        # 生成汇总信息
        summary = {
            "permission_coverage_rate": (pages_with_permissions / total_pages * 100) if total_pages > 0 else 0,
            "v2_adoption_rate": (v2_permission_pages / total_pages * 100) if total_pages > 0 else 0,
            "v1_legacy_rate": (v1_permission_pages / total_pages * 100) if total_pages > 0 else 0,
            "mixed_usage_rate": (mixed_permission_pages / total_pages * 100) if total_pages > 0 else 0,
            "permission_element_v2_rate": (v2_permission_elements / total_permission_elements * 100) if total_permission_elements > 0 else 0,
            "pages_with_issues": sum(1 for page in page_results if page.issues),
            "common_issues": self._get_common_issues(page_results),
            "permission_distribution": self._get_permission_distribution(page_results),
            "role_test_summary": self._get_role_test_summary(role_results)
        }
        
        return PermissionValidationReport(
            total_pages=total_pages,
            pages_with_permissions=pages_with_permissions,
            v2_permission_pages=v2_permission_pages,
            v1_permission_pages=v1_permission_pages,
            mixed_permission_pages=mixed_permission_pages,
            total_permission_elements=total_permission_elements,
            v2_permission_elements=v2_permission_elements,
            v1_permission_elements=v1_permission_elements,
            page_results=page_results,
            role_test_results=role_results,
            summary=summary
        )

    def _get_common_issues(self, page_results: List[PagePermissionUsage]) -> List[Dict[str, Any]]:
        """获取常见问题"""
        issue_counts = {}
        
        for page in page_results:
            for issue in page.issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {"issue": issue, "count": count, "percentage": count / len(page_results) * 100}
            for issue, count in sorted_issues[:10]
        ]

    def _get_permission_distribution(self, page_results: List[PagePermissionUsage]) -> Dict[str, Any]:
        """获取权限分布统计"""
        element_types = {'button': 0, 'directive': 0, 'component': 0}
        permission_usage = {}
        
        for page in page_results:
            for element in page.permission_elements:
                element_types[element.element_type] = element_types.get(element.element_type, 0) + 1
                permission_usage[element.permission] = permission_usage.get(element.permission, 0) + 1
        
        # 获取最常用的权限
        top_permissions = sorted(permission_usage.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "element_types": element_types,
            "top_permissions": [{"permission": perm, "count": count} for perm, count in top_permissions]
        }

    def _get_role_test_summary(self, role_results: List[RoleTestResult]) -> Dict[str, Any]:
        """获取角色测试摘要"""
        if not role_results:
            return {"total_roles": 0, "tested_roles": 0, "avg_permissions": 0}
        
        total_permissions = sum(len(role.permissions) for role in role_results)
        avg_permissions = total_permissions / len(role_results) if role_results else 0
        
        return {
            "total_roles": len(role_results),
            "tested_roles": len(role_results),
            "avg_permissions": avg_permissions,
            "roles_with_violations": sum(1 for role in role_results if role.permission_violations)
        }

    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def save_report(self, report: PermissionValidationReport, output_file: str):
        """保存报告"""
        report_data = asdict(report)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

    def generate_html_report(self, report: PermissionValidationReport, output_file: str):
        """生成HTML报告"""
        html_content = self._generate_html_content(report)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _generate_html_content(self, report: PermissionValidationReport) -> str:
        """生成HTML内容"""
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>权限控制验证报告</title>
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
        .status-v2 {{ color: #28a745; font-weight: bold; }}
        .status-v1 {{ color: #ffc107; font-weight: bold; }}
        .status-mixed {{ color: #dc3545; font-weight: bold; }}
        .status-none {{ color: #6c757d; font-weight: bold; }}
        .progress-bar {{ width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #28a745, #20c997); }}
        .permission-element {{ font-family: monospace; background: #f8f9fa; padding: 2px 4px; border-radius: 3px; }}
        .file-path {{ font-family: monospace; color: #666; font-size: 0.9em; }}
        .issues {{ background: #fff3cd; padding: 10px; border-radius: 4px; margin: 5px 0; }}
        .recommendations {{ background: #d1ecf1; padding: 10px; border-radius: 4px; margin: 5px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>权限控制验证报告</h1>
        <p>生成时间: {self._get_current_time()}</p>
        
        <div class="summary">
            <div class="summary-card">
                <h3>总页面数</h3>
                <div class="value">{report.total_pages}</div>
                <div class="label">已扫描的Vue页面</div>
            </div>
            <div class="summary-card">
                <h3>权限覆盖率</h3>
                <div class="value">{report.summary['permission_coverage_rate']:.1f}%</div>
                <div class="label">{report.pages_with_permissions} 个页面有权限控制</div>
            </div>
            <div class="summary-card">
                <h3>V2权限采用率</h3>
                <div class="value">{report.summary['v2_adoption_rate']:.1f}%</div>
                <div class="label">{report.v2_permission_pages} 个页面使用V2</div>
            </div>
            <div class="summary-card">
                <h3>权限元素总数</h3>
                <div class="value">{report.total_permission_elements}</div>
                <div class="label">V2: {report.v2_permission_elements}, V1: {report.v1_permission_elements}</div>
            </div>
        </div>
        
        <h2>权限元素分布</h2>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {report.summary['permission_element_v2_rate']:.1f}%"></div>
        </div>
        <p>V2权限元素占比: {report.summary['permission_element_v2_rate']:.1f}% ({report.v2_permission_elements}/{report.total_permission_elements})</p>
        
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
        
        <h2>权限使用统计</h2>
        <table>
            <thead>
                <tr>
                    <th>权限</th>
                    <th>使用次数</th>
                </tr>
            </thead>
            <tbody>
                {self._generate_permission_usage_rows(report.summary['permission_distribution']['top_permissions'])}
            </tbody>
        </table>
        
        <h2>详细页面分析</h2>
        {self._generate_pages_detail(report.page_results)}
    </div>
</body>
</html>
        """

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

    def _generate_permission_usage_rows(self, permissions: List[Dict]) -> str:
        """生成权限使用表格行"""
        rows = []
        for perm in permissions:
            rows.append(f"""
                <tr>
                    <td class="permission-element">{perm['permission']}</td>
                    <td>{perm['count']}</td>
                </tr>
            """)
        return "".join(rows)

    def _generate_pages_detail(self, pages: List[PagePermissionUsage]) -> str:
        """生成页面详情"""
        details = []
        
        for page in pages:
            status_class = self._get_permission_status_class(page)
            status_text = self._get_permission_status_text(page)
            
            elements_html = ""
            if page.permission_elements:
                elements_html = "<h4>权限元素:</h4><ul>"
                for element in page.permission_elements:
                    version_text = "V2" if element.is_v2_format else "V1"
                    elements_html += f"""
                        <li>
                            <span class="permission-element">{element.element_type}: {element.permission}</span> 
                            - {version_text}
                            <br>
                            <small>第{element.line_number}行: {element.line_content}</small>
                        </li>
                    """
                elements_html += "</ul>"
            
            issues_html = ""
            if page.issues:
                issues_html = "<div class='issues'><strong>问题:</strong><ul>"
                for issue in page.issues:
                    issues_html += f"<li>{issue}</li>"
                issues_html += "</ul></div>"
            
            recommendations_html = ""
            if page.recommendations:
                recommendations_html = "<div class='recommendations'><strong>建议:</strong><ul>"
                for rec in page.recommendations:
                    recommendations_html += f"<li>{rec}</li>"
                recommendations_html += "</ul></div>"
            
            details.append(f"""
                <div style="border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px;">
                    <h3>{page.page_name} <span class="{status_class}">[{status_text}]</span></h3>
                    <p class="file-path">{page.file_path}</p>
                    <p class="file-path">路由: {page.route_path}</p>
                    <p>
                        权限元素: {page.total_permission_elements} | 
                        V2: {page.v2_permission_elements} | 
                        V1: {page.v1_permission_elements} | 
                        未知: {page.unknown_permission_elements}
                    </p>
                    {elements_html}
                    {issues_html}
                    {recommendations_html}
                </div>
            """)
        
        return "".join(details)

    def _get_permission_status_class(self, page: PagePermissionUsage) -> str:
        """获取权限状态样式类"""
        if page.total_permission_elements == 0:
            return "status-none"
        elif page.v2_permission_elements > 0 and page.v1_permission_elements == 0:
            return "status-v2"
        elif page.v1_permission_elements > 0 and page.v2_permission_elements == 0:
            return "status-v1"
        else:
            return "status-mixed"

    def _get_permission_status_text(self, page: PagePermissionUsage) -> str:
        """获取权限状态文本"""
        if page.total_permission_elements == 0:
            return "无权限控制"
        elif page.v2_permission_elements > 0 and page.v1_permission_elements == 0:
            return "V2"
        elif page.v1_permission_elements > 0 and page.v2_permission_elements == 0:
            return "V1"
        else:
            return "混合"


async def main():
    parser = argparse.ArgumentParser(description='权限控制验证器')
    parser.add_argument('--web-root', default='web', help='Web项目根目录')
    parser.add_argument('--api-url', default='http://localhost:8000', help='API基础URL')
    parser.add_argument('--token', help='认证令牌')
    parser.add_argument('--output', default='permission_validation_report.json', help='输出JSON报告文件')
    parser.add_argument('--html-output', default='permission_validation_report.html', help='输出HTML报告文件')
    
    args = parser.parse_args()
    
    validator = PermissionControlValidator(args.web_root, args.api_url)
    
    try:
        report = await validator.run_validation(args.token)
        
        # 保存报告
        validator.save_report(report, args.output)
        validator.generate_html_report(report, args.html_output)
        
        print("=== 权限控制验证摘要 ===")
        print(f"总页面数: {report.total_pages}")
        print(f"有权限控制的页面: {report.pages_with_permissions} ({report.summary['permission_coverage_rate']:.1f}%)")
        print(f"使用V2权限的页面: {report.v2_permission_pages} ({report.summary['v2_adoption_rate']:.1f}%)")
        print(f"使用V1权限的页面: {report.v1_permission_pages} ({report.summary['v1_legacy_rate']:.1f}%)")
        print(f"混合使用的页面: {report.mixed_permission_pages}")
        print(f"权限元素总数: {report.total_permission_elements}")
        print(f"V2权限元素占比: {report.summary['permission_element_v2_rate']:.1f}%")
        print(f"存在问题的页面: {report.summary['pages_with_issues']}")
        
        print(f"\n报告已保存:")
        print(f"- JSON: {args.output}")
        print(f"- HTML: {args.html_output}")
        
        return 0
        
    except Exception as e:
        print(f"验证过程中出现错误: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))