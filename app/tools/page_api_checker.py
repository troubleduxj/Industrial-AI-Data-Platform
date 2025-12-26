#!/usr/bin/env python3
"""
页面API调用检查器
分析web/src/views/下的所有页面组件，检查API调用是否使用v2版本
"""

import os
import re
import json
import glob
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import argparse


@dataclass
class ApiCall:
    """API调用信息"""
    api_name: str
    method_name: str
    line_number: int
    line_content: str
    is_v2: bool
    confidence: float  # 置信度 0-1


@dataclass
class PageApiUsage:
    """页面API使用情况"""
    file_path: str
    page_name: str
    total_api_calls: int
    v2_api_calls: int
    v1_api_calls: int
    unknown_api_calls: int
    api_calls: List[ApiCall]
    imports: List[str]
    issues: List[str]
    recommendations: List[str]


@dataclass
class ApiUsageReport:
    """API使用情况报告"""
    total_pages: int
    pages_using_v2: int
    pages_using_v1: int
    pages_mixed_usage: int
    total_api_calls: int
    v2_api_calls: int
    v1_api_calls: int
    unknown_api_calls: int
    pages: List[PageApiUsage]
    summary: Dict[str, any]


class PageApiChecker:
    """页面API调用检查器"""
    
    def __init__(self, web_root: str = "web"):
        self.web_root = Path(web_root)
        self.views_path = self.web_root / "src" / "views"
        self.api_path = self.web_root / "src" / "api"
        
        # V2 API模式
        self.v2_patterns = [
            r'systemV2Api\.',
            r'deviceV2Api\.',
            r'from\s+[\'"]@/api/system-v2[\'"]',
            r'from\s+[\'"]@/api/device-v2[\'"]',
            r'import.*system-v2',
            r'import.*device-v2',
            r'\.v2\.',
            r'api/v2/',
            r'systemApis\.',
            r'deviceApis\.',
            r'createSystemApis',
            r'createDeviceApis',
        ]
        
        # V1 API模式
        self.v1_patterns = [
            r'api\.[a-zA-Z]+(?!V2)',
            r'from\s+[\'"]@/api[\'"](?!\s*\/)',
            r'import\s+api\s+from',
            r'\.v1\.',
            r'api/v1/',
            r'/api/(?!v2)',
        ]
        
        # 常见API方法模式
        self.api_method_patterns = [
            r'(\w+Api)\.(\w+)\(',
            r'api\.(\w+)\(',
            r'(\w+)\.list\(',
            r'(\w+)\.get\(',
            r'(\w+)\.create\(',
            r'(\w+)\.update\(',
            r'(\w+)\.delete\(',
            r'(\w+)\.search\(',
        ]
        
        # 已知的V2 API模块
        self.v2_api_modules = {
            'systemV2Api', 'deviceV2Api', 'userApi', 'roleApi', 
            'menuApi', 'departmentApi', 'deviceApi', 'deviceTypeApi',
            'maintenanceApi', 'processApi', 'compatibilityApi'
        }
        
        # 已知的V1 API模式
        self.v1_api_patterns = {
            'getUserList', 'createUser', 'updateUser', 'deleteUser',
            'getRoleList', 'createRole', 'updateRole', 'deleteRole',
            'getMenus', 'createMenu', 'updateMenu', 'deleteMenu',
            'getDepts', 'createDept', 'updateDept', 'deleteDept',
            'getDeviceList', 'createDevice', 'updateDevice', 'deleteDevice',
        }

    def scan_all_pages(self) -> List[str]:
        """扫描所有页面文件"""
        vue_files = []
        
        # 递归查找所有.vue文件
        for root, dirs, files in os.walk(self.views_path):
            for file in files:
                if file.endswith('.vue'):
                    vue_files.append(os.path.join(root, file))
        
        return vue_files

    def extract_imports(self, content: str) -> List[str]:
        """提取import语句"""
        imports = []
        
        # 匹配import语句
        import_patterns = [
            r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',
            r'import\s+[\'"]([^\'"]+)[\'"]',
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            imports.extend(matches)
        
        return imports

    def analyze_api_calls(self, content: str, file_path: str) -> List[ApiCall]:
        """分析API调用"""
        api_calls = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith('//') or line_stripped.startswith('*'):
                continue
            
            # 检查API方法调用
            for pattern in self.api_method_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    api_name = match.group(1) if match.lastindex >= 1 else 'unknown'
                    method_name = match.group(2) if match.lastindex >= 2 else match.group(1)
                    
                    # 判断是否为V2 API
                    is_v2, confidence = self._determine_api_version(line, api_name, method_name)
                    
                    api_call = ApiCall(
                        api_name=api_name,
                        method_name=method_name,
                        line_number=line_num,
                        line_content=line_stripped,
                        is_v2=is_v2,
                        confidence=confidence
                    )
                    api_calls.append(api_call)
        
        return api_calls

    def _determine_api_version(self, line: str, api_name: str, method_name: str) -> Tuple[bool, float]:
        """判断API版本"""
        confidence = 0.5  # 默认置信度
        
        # 检查V2模式
        for pattern in self.v2_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                confidence = 0.9
                return True, confidence
        
        # 检查V1模式
        for pattern in self.v1_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                confidence = 0.8
                return False, confidence
        
        # 基于API名称判断
        if api_name in self.v2_api_modules:
            confidence = 0.8
            return True, confidence
        
        if method_name in self.v1_api_patterns:
            confidence = 0.7
            return False, confidence
        
        # 基于命名约定判断
        if 'v2' in api_name.lower() or 'V2' in api_name:
            confidence = 0.8
            return True, confidence
        
        if api_name == 'api' and method_name not in self.v2_api_modules:
            confidence = 0.6
            return False, confidence
        
        # 无法确定，返回未知
        confidence = 0.3
        return None, confidence

    def analyze_page(self, file_path: str) -> PageApiUsage:
        """分析单个页面"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return PageApiUsage(
                file_path=file_path,
                page_name=os.path.basename(file_path),
                total_api_calls=0,
                v2_api_calls=0,
                v1_api_calls=0,
                unknown_api_calls=0,
                api_calls=[],
                imports=[],
                issues=[f"无法读取文件: {str(e)}"],
                recommendations=[]
            )
        
        # 提取页面名称
        page_name = self._extract_page_name(content, file_path)
        
        # 提取imports
        imports = self.extract_imports(content)
        
        # 分析API调用
        api_calls = self.analyze_api_calls(content, file_path)
        
        # 统计API调用
        v2_calls = sum(1 for call in api_calls if call.is_v2 is True)
        v1_calls = sum(1 for call in api_calls if call.is_v2 is False)
        unknown_calls = sum(1 for call in api_calls if call.is_v2 is None)
        
        # 生成问题和建议
        issues, recommendations = self._generate_issues_and_recommendations(
            api_calls, imports, file_path
        )
        
        return PageApiUsage(
            file_path=file_path,
            page_name=page_name,
            total_api_calls=len(api_calls),
            v2_api_calls=v2_calls,
            v1_api_calls=v1_calls,
            unknown_api_calls=unknown_calls,
            api_calls=api_calls,
            imports=imports,
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

    def _generate_issues_and_recommendations(
        self, api_calls: List[ApiCall], imports: List[str], file_path: str
    ) -> Tuple[List[str], List[str]]:
        """生成问题和建议"""
        issues = []
        recommendations = []
        
        v2_calls = [call for call in api_calls if call.is_v2 is True]
        v1_calls = [call for call in api_calls if call.is_v2 is False]
        unknown_calls = [call for call in api_calls if call.is_v2 is None]
        
        # 检查混合使用
        if v1_calls and v2_calls:
            issues.append(f"页面同时使用V1和V2 API，存在不一致性")
            recommendations.append("统一使用V2 API，移除V1 API调用")
        
        # 检查V1 API使用
        if v1_calls and not v2_calls:
            issues.append(f"页面仍在使用V1 API ({len(v1_calls)}个调用)")
            recommendations.append("将所有API调用迁移到V2版本")
        
        # 检查未知API调用
        if unknown_calls:
            issues.append(f"发现{len(unknown_calls)}个无法确定版本的API调用")
            recommendations.append("检查并明确标识API版本")
        
        # 检查import语句
        v1_imports = [imp for imp in imports if any(pattern in imp for pattern in ['@/api"', 'api"']) and 'v2' not in imp]
        if v1_imports:
            issues.append(f"发现V1 API import语句: {', '.join(v1_imports)}")
            recommendations.append("更新import语句使用V2 API模块")
        
        # 检查低置信度调用
        low_confidence_calls = [call for call in api_calls if call.confidence < 0.5]
        if low_confidence_calls:
            issues.append(f"发现{len(low_confidence_calls)}个低置信度的API调用")
            recommendations.append("手动检查这些API调用的版本")
        
        return issues, recommendations

    def generate_report(self, pages: List[PageApiUsage]) -> ApiUsageReport:
        """生成报告"""
        total_pages = len(pages)
        pages_using_v2 = sum(1 for page in pages if page.v2_api_calls > 0 and page.v1_api_calls == 0)
        pages_using_v1 = sum(1 for page in pages if page.v1_api_calls > 0 and page.v2_api_calls == 0)
        pages_mixed_usage = sum(1 for page in pages if page.v1_api_calls > 0 and page.v2_api_calls > 0)
        
        total_api_calls = sum(page.total_api_calls for page in pages)
        v2_api_calls = sum(page.v2_api_calls for page in pages)
        v1_api_calls = sum(page.v1_api_calls for page in pages)
        unknown_api_calls = sum(page.unknown_api_calls for page in pages)
        
        # 生成汇总信息
        summary = {
            "v2_adoption_rate": (pages_using_v2 / total_pages * 100) if total_pages > 0 else 0,
            "v1_legacy_rate": (pages_using_v1 / total_pages * 100) if total_pages > 0 else 0,
            "mixed_usage_rate": (pages_mixed_usage / total_pages * 100) if total_pages > 0 else 0,
            "api_v2_usage_rate": (v2_api_calls / total_api_calls * 100) if total_api_calls > 0 else 0,
            "pages_with_issues": sum(1 for page in pages if page.issues),
            "top_issues": self._get_top_issues(pages),
            "migration_priority": self._get_migration_priority(pages)
        }
        
        return ApiUsageReport(
            total_pages=total_pages,
            pages_using_v2=pages_using_v2,
            pages_using_v1=pages_using_v1,
            pages_mixed_usage=pages_mixed_usage,
            total_api_calls=total_api_calls,
            v2_api_calls=v2_api_calls,
            v1_api_calls=v1_api_calls,
            unknown_api_calls=unknown_api_calls,
            pages=pages,
            summary=summary
        )

    def _get_top_issues(self, pages: List[PageApiUsage]) -> List[Dict[str, any]]:
        """获取主要问题"""
        issue_counts = {}
        
        for page in pages:
            for issue in page.issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        # 按出现频率排序
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {"issue": issue, "count": count, "percentage": count / len(pages) * 100}
            for issue, count in sorted_issues[:10]
        ]

    def _get_migration_priority(self, pages: List[PageApiUsage]) -> List[Dict[str, any]]:
        """获取迁移优先级"""
        priority_pages = []
        
        for page in pages:
            if page.v1_api_calls > 0:
                priority_score = page.v1_api_calls * 2 + len(page.issues)
                priority_pages.append({
                    "file_path": page.file_path,
                    "page_name": page.page_name,
                    "v1_calls": page.v1_api_calls,
                    "issues_count": len(page.issues),
                    "priority_score": priority_score
                })
        
        # 按优先级分数排序
        priority_pages.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return priority_pages[:20]  # 返回前20个高优先级页面

    def save_report(self, report: ApiUsageReport, output_file: str):
        """保存报告"""
        report_data = asdict(report)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

    def generate_html_report(self, report: ApiUsageReport, output_file: str):
        """生成HTML报告"""
        html_content = self._generate_html_content(report)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _generate_html_content(self, report: ApiUsageReport) -> str:
        """生成HTML内容"""
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>页面API使用情况报告</title>
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
        .status-v1 {{ color: #dc3545; font-weight: bold; }}
        .status-mixed {{ color: #ffc107; font-weight: bold; }}
        .status-unknown {{ color: #6c757d; font-weight: bold; }}
        .issues {{ background: #fff3cd; padding: 10px; border-radius: 4px; margin: 5px 0; }}
        .recommendations {{ background: #d1ecf1; padding: 10px; border-radius: 4px; margin: 5px 0; }}
        .progress-bar {{ width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #28a745, #20c997); }}
        .api-call {{ font-family: monospace; background: #f8f9fa; padding: 2px 4px; border-radius: 3px; }}
        .confidence {{ font-size: 0.8em; color: #666; }}
        .file-path {{ font-family: monospace; color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>页面API使用情况报告</h1>
        <p>生成时间: {self._get_current_time()}</p>
        
        <div class="summary">
            <div class="summary-card">
                <h3>总页面数</h3>
                <div class="value">{report.total_pages}</div>
                <div class="label">已扫描的Vue页面</div>
            </div>
            <div class="summary-card">
                <h3>V2 API采用率</h3>
                <div class="value">{report.summary['v2_adoption_rate']:.1f}%</div>
                <div class="label">{report.pages_using_v2} 个页面使用V2</div>
            </div>
            <div class="summary-card">
                <h3>V1 API遗留率</h3>
                <div class="value">{report.summary['v1_legacy_rate']:.1f}%</div>
                <div class="label">{report.pages_using_v1} 个页面使用V1</div>
            </div>
            <div class="summary-card">
                <h3>混合使用</h3>
                <div class="value">{report.pages_mixed_usage}</div>
                <div class="label">同时使用V1和V2的页面</div>
            </div>
        </div>
        
        <h2>API调用统计</h2>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {report.summary['api_v2_usage_rate']:.1f}%"></div>
        </div>
        <p>V2 API调用占比: {report.summary['api_v2_usage_rate']:.1f}% ({report.v2_api_calls}/{report.total_api_calls})</p>
        
        <h2>主要问题</h2>
        <table>
            <thead>
                <tr>
                    <th>问题描述</th>
                    <th>影响页面数</th>
                    <th>占比</th>
                </tr>
            </thead>
            <tbody>
                {self._generate_issues_table_rows(report.summary['top_issues'])}
            </tbody>
        </table>
        
        <h2>迁移优先级</h2>
        <table>
            <thead>
                <tr>
                    <th>页面</th>
                    <th>文件路径</th>
                    <th>V1调用数</th>
                    <th>问题数</th>
                    <th>优先级分数</th>
                </tr>
            </thead>
            <tbody>
                {self._generate_priority_table_rows(report.summary['migration_priority'])}
            </tbody>
        </table>
        
        <h2>详细页面分析</h2>
        {self._generate_pages_detail(report.pages)}
    </div>
</body>
</html>
        """

    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

    def _generate_priority_table_rows(self, priorities: List[Dict]) -> str:
        """生成优先级表格行"""
        rows = []
        for priority in priorities:
            rows.append(f"""
                <tr>
                    <td>{priority['page_name']}</td>
                    <td class="file-path">{priority['file_path']}</td>
                    <td>{priority['v1_calls']}</td>
                    <td>{priority['issues_count']}</td>
                    <td><strong>{priority['priority_score']}</strong></td>
                </tr>
            """)
        return "".join(rows)

    def _generate_pages_detail(self, pages: List[PageApiUsage]) -> str:
        """生成页面详情"""
        details = []
        
        for page in pages:
            status_class = self._get_status_class(page)
            status_text = self._get_status_text(page)
            
            api_calls_html = ""
            if page.api_calls:
                api_calls_html = "<h4>API调用详情:</h4><ul>"
                for call in page.api_calls:
                    confidence_text = f"(置信度: {call.confidence:.1f})" if call.confidence < 1.0 else ""
                    version_text = "V2" if call.is_v2 is True else "V1" if call.is_v2 is False else "未知"
                    api_calls_html += f"""
                        <li>
                            <span class="api-call">{call.api_name}.{call.method_name}()</span> 
                            - {version_text} 
                            <span class="confidence">{confidence_text}</span>
                            <br>
                            <small>第{call.line_number}行: {call.line_content}</small>
                        </li>
                    """
                api_calls_html += "</ul>"
            
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
                    <p>
                        总API调用: {page.total_api_calls} | 
                        V2: {page.v2_api_calls} | 
                        V1: {page.v1_api_calls} | 
                        未知: {page.unknown_api_calls}
                    </p>
                    {api_calls_html}
                    {issues_html}
                    {recommendations_html}
                </div>
            """)
        
        return "".join(details)

    def _get_status_class(self, page: PageApiUsage) -> str:
        """获取状态样式类"""
        if page.v2_api_calls > 0 and page.v1_api_calls == 0:
            return "status-v2"
        elif page.v1_api_calls > 0 and page.v2_api_calls == 0:
            return "status-v1"
        elif page.v1_api_calls > 0 and page.v2_api_calls > 0:
            return "status-mixed"
        else:
            return "status-unknown"

    def _get_status_text(self, page: PageApiUsage) -> str:
        """获取状态文本"""
        if page.v2_api_calls > 0 and page.v1_api_calls == 0:
            return "V2"
        elif page.v1_api_calls > 0 and page.v2_api_calls == 0:
            return "V1"
        elif page.v1_api_calls > 0 and page.v2_api_calls > 0:
            return "混合"
        else:
            return "未知"

    def run_check(self) -> ApiUsageReport:
        """运行检查"""
        print("开始扫描页面文件...")
        vue_files = self.scan_all_pages()
        print(f"发现 {len(vue_files)} 个Vue页面文件")
        
        pages = []
        for i, file_path in enumerate(vue_files, 1):
            print(f"分析页面 {i}/{len(vue_files)}: {file_path}")
            page_usage = self.analyze_page(file_path)
            pages.append(page_usage)
        
        print("生成报告...")
        report = self.generate_report(pages)
        
        return report


def main():
    parser = argparse.ArgumentParser(description='页面API调用检查器')
    parser.add_argument('--web-root', default='web', help='Web项目根目录')
    parser.add_argument('--output', default='page_api_usage_report.json', help='输出JSON报告文件')
    parser.add_argument('--html-output', default='page_api_usage_report.html', help='输出HTML报告文件')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    checker = PageApiChecker(args.web_root)
    
    try:
        report = checker.run_check()
        
        # 保存JSON报告
        checker.save_report(report, args.output)
        print(f"JSON报告已保存到: {args.output}")
        
        # 生成HTML报告
        checker.generate_html_report(report, args.html_output)
        print(f"HTML报告已保存到: {args.html_output}")
        
        # 打印摘要
        print("\n=== 检查摘要 ===")
        print(f"总页面数: {report.total_pages}")
        print(f"使用V2 API的页面: {report.pages_using_v2} ({report.summary['v2_adoption_rate']:.1f}%)")
        print(f"使用V1 API的页面: {report.pages_using_v1} ({report.summary['v1_legacy_rate']:.1f}%)")
        print(f"混合使用的页面: {report.pages_mixed_usage}")
        print(f"V2 API调用占比: {report.summary['api_v2_usage_rate']:.1f}%")
        print(f"存在问题的页面: {report.summary['pages_with_issues']}")
        
        if args.verbose:
            print("\n=== 主要问题 ===")
            for issue in report.summary['top_issues'][:5]:
                print(f"- {issue['issue']} (影响{issue['count']}个页面)")
        
    except Exception as e:
        print(f"检查过程中出现错误: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())