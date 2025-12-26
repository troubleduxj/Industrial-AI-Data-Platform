#!/usr/bin/env python3
"""
页面功能自动化测试框架
统一的页面测试工具，整合API调用检查、CRUD操作测试和权限控制验证
"""

import asyncio
import json
import argparse
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from page_api_checker import PageApiChecker
from crud_operations_tester import CrudOperationsTester
from permission_control_validator import PermissionControlValidator


@dataclass
class UnifiedTestReport:
    """统一测试报告"""
    test_timestamp: str
    api_usage_report: Dict[str, Any]
    crud_test_report: Dict[str, Any]
    permission_validation_report: Dict[str, Any]
    summary: Dict[str, Any]


class PageFunctionTestFramework:
    """页面功能自动化测试框架"""
    
    def __init__(self, web_root: str = "web", api_base_url: str = "http://localhost:8000", token: str = None):
        self.web_root = web_root
        self.api_base_url = api_base_url
        self.token = token
        
        # 初始化各个测试工具
        self.api_checker = PageApiChecker(web_root)
        self.crud_tester = CrudOperationsTester(api_base_url, token)
        self.permission_validator = PermissionControlValidator(web_root, api_base_url)

    async def run_comprehensive_test(self) -> UnifiedTestReport:
        """运行综合测试"""
        print("=== 开始页面功能综合测试 ===")
        
        # 1. API使用情况检查
        print("\n1. 执行API使用情况检查...")
        api_report = self.api_checker.run_check()
        
        # 2. CRUD操作测试
        print("\n2. 执行CRUD操作测试...")
        try:
            crud_report = await self.crud_tester.run_all_tests()
        except Exception as e:
            print(f"CRUD测试失败: {str(e)}")
            crud_report = None
        
        # 3. 权限控制验证
        print("\n3. 执行权限控制验证...")
        permission_report = await self.permission_validator.run_validation(self.token)
        
        # 生成统一报告
        unified_report = self._generate_unified_report(api_report, crud_report, permission_report)
        
        return unified_report

    def _generate_unified_report(
        self, api_report, crud_report, permission_report
    ) -> UnifiedTestReport:
        """生成统一报告"""
        from datetime import datetime
        
        # 转换报告为字典格式
        api_report_dict = asdict(api_report) if api_report else {}
        crud_report_dict = asdict(crud_report) if crud_report else {}
        permission_report_dict = asdict(permission_report) if permission_report else {}
        
        # 生成综合摘要
        summary = self._generate_comprehensive_summary(
            api_report, crud_report, permission_report
        )
        
        return UnifiedTestReport(
            test_timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            api_usage_report=api_report_dict,
            crud_test_report=crud_report_dict,
            permission_validation_report=permission_report_dict,
            summary=summary
        )

    def _generate_comprehensive_summary(
        self, api_report, crud_report, permission_report
    ) -> Dict[str, Any]:
        """生成综合摘要"""
        summary = {
            "overall_status": "completed",
            "test_modules": {
                "api_usage_check": api_report is not None,
                "crud_operations_test": crud_report is not None,
                "permission_validation": permission_report is not None
            }
        }
        
        # API使用情况摘要
        if api_report:
            summary["api_usage"] = {
                "total_pages": api_report.total_pages,
                "v2_adoption_rate": api_report.summary['v2_adoption_rate'],
                "v1_legacy_rate": api_report.summary['v1_legacy_rate'],
                "mixed_usage_rate": api_report.summary['mixed_usage_rate'],
                "pages_with_issues": api_report.summary['pages_with_issues']
            }
        
        # CRUD测试摘要
        if crud_report:
            summary["crud_testing"] = {
                "total_tests": crud_report.total_tests,
                "success_rate": crud_report.summary['success_rate'],
                "v2_compliance_rate": crud_report.summary['v2_compliance_rate'],
                "avg_response_time": crud_report.summary['avg_response_time']
            }
        
        # 权限验证摘要
        if permission_report:
            summary["permission_validation"] = {
                "total_pages": permission_report.total_pages,
                "permission_coverage_rate": permission_report.summary['permission_coverage_rate'],
                "v2_adoption_rate": permission_report.summary['v2_adoption_rate'],
                "pages_with_issues": permission_report.summary['pages_with_issues']
            }
        
        # 综合评分
        summary["overall_score"] = self._calculate_overall_score(
            api_report, crud_report, permission_report
        )
        
        # 主要建议
        summary["key_recommendations"] = self._generate_key_recommendations(
            api_report, crud_report, permission_report
        )
        
        return summary

    def _calculate_overall_score(self, api_report, crud_report, permission_report) -> float:
        """计算综合评分"""
        scores = []
        
        # API使用评分 (0-100)
        if api_report:
            api_score = api_report.summary['v2_adoption_rate']
            scores.append(api_score)
        
        # CRUD测试评分 (0-100)
        if crud_report:
            crud_score = crud_report.summary['success_rate']
            scores.append(crud_score)
        
        # 权限验证评分 (0-100)
        if permission_report:
            permission_score = (
                permission_report.summary['permission_coverage_rate'] * 0.6 +
                permission_report.summary['v2_adoption_rate'] * 0.4
            )
            scores.append(permission_score)
        
        return sum(scores) / len(scores) if scores else 0

    def _generate_key_recommendations(
        self, api_report, crud_report, permission_report
    ) -> List[str]:
        """生成关键建议"""
        recommendations = []
        
        # API使用建议
        if api_report:
            if api_report.summary['v2_adoption_rate'] < 80:
                recommendations.append("加快API v2迁移，当前采用率较低")
            if api_report.summary['pages_with_issues'] > 0:
                recommendations.append("修复API使用中的问题和不一致性")
        
        # CRUD测试建议
        if crud_report:
            if crud_report.summary['success_rate'] < 90:
                recommendations.append("修复CRUD操作中的失败测试")
            if crud_report.summary['v2_compliance_rate'] < 80:
                recommendations.append("提高API v2合规性")
        
        # 权限验证建议
        if permission_report:
            if permission_report.summary['permission_coverage_rate'] < 50:
                recommendations.append("增加页面权限控制覆盖率")
            if permission_report.summary['v2_adoption_rate'] < 80:
                recommendations.append("将权限控制迁移到v2格式")
        
        return recommendations

    def save_unified_report(self, report: UnifiedTestReport, output_file: str):
        """保存统一报告"""
        report_data = asdict(report)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

    def generate_unified_html_report(self, report: UnifiedTestReport, output_file: str):
        """生成统一HTML报告"""
        html_content = self._generate_unified_html_content(report)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _generate_unified_html_content(self, report: UnifiedTestReport) -> str:
        """生成统一HTML内容"""
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>页面功能综合测试报告</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1, h2, h3 {{ color: #333; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
        .summary-card {{ background: #f8f9fa; padding: 20px; border-radius: 6px; border-left: 4px solid #007bff; }}
        .summary-card h3 {{ margin: 0 0 10px 0; color: #007bff; }}
        .summary-card .value {{ font-size: 2em; font-weight: bold; color: #333; }}
        .summary-card .label {{ color: #666; font-size: 0.9em; }}
        .score-circle {{ width: 120px; height: 120px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto; }}
        .score-excellent {{ background: linear-gradient(135deg, #28a745, #20c997); }}
        .score-good {{ background: linear-gradient(135deg, #ffc107, #fd7e14); }}
        .score-poor {{ background: linear-gradient(135deg, #dc3545, #e83e8c); }}
        .score-text {{ color: white; font-size: 1.5em; font-weight: bold; }}
        .test-module {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
        .test-module h3 {{ margin-top: 0; }}
        .status-success {{ color: #28a745; }}
        .status-warning {{ color: #ffc107; }}
        .status-danger {{ color: #dc3545; }}
        .recommendations {{ background: #d1ecf1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .recommendations h3 {{ margin-top: 0; color: #0c5460; }}
        .recommendations ul {{ margin: 0; }}
        .progress-bar {{ width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; margin: 10px 0; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #28a745, #20c997); }}
    </style>
</head>
<body>
    <div class="container">
        <h1>页面功能综合测试报告</h1>
        <p>测试时间: {report.test_timestamp}</p>
        
        <div class="summary">
            <div class="summary-card">
                <h3>综合评分</h3>
                <div class="{self._get_score_class(report.summary['overall_score'])}">
                    <div class="score-text">{report.summary['overall_score']:.0f}</div>
                </div>
                <div class="label">综合质量评分</div>
            </div>
            
            {self._generate_test_module_cards(report)}
        </div>
        
        <div class="recommendations">
            <h3>关键建议</h3>
            <ul>
                {self._generate_recommendations_list(report.summary['key_recommendations'])}
            </ul>
        </div>
        
        <h2>测试模块详情</h2>
        
        {self._generate_api_usage_section(report)}
        {self._generate_crud_test_section(report)}
        {self._generate_permission_validation_section(report)}
        
        <h2>详细报告链接</h2>
        <p>
            <a href="page_api_usage_report.html" target="_blank">API使用情况详细报告</a> |
            <a href="crud_test_report.html" target="_blank">CRUD测试详细报告</a> |
            <a href="permission_validation_report.html" target="_blank">权限验证详细报告</a>
        </p>
    </div>
</body>
</html>
        """

    def _get_score_class(self, score: float) -> str:
        """获取评分样式类"""
        if score >= 80:
            return "score-circle score-excellent"
        elif score >= 60:
            return "score-circle score-good"
        else:
            return "score-circle score-poor"

    def _generate_test_module_cards(self, report: UnifiedTestReport) -> str:
        """生成测试模块卡片"""
        cards = []
        
        # API使用情况卡片
        if report.summary.get('api_usage'):
            api_data = report.summary['api_usage']
            cards.append(f"""
                <div class="summary-card">
                    <h3>API使用情况</h3>
                    <div class="value">{api_data['v2_adoption_rate']:.1f}%</div>
                    <div class="label">V2 API采用率</div>
                </div>
            """)
        
        # CRUD测试卡片
        if report.summary.get('crud_testing'):
            crud_data = report.summary['crud_testing']
            cards.append(f"""
                <div class="summary-card">
                    <h3>CRUD测试</h3>
                    <div class="value">{crud_data['success_rate']:.1f}%</div>
                    <div class="label">测试通过率</div>
                </div>
            """)
        
        # 权限验证卡片
        if report.summary.get('permission_validation'):
            perm_data = report.summary['permission_validation']
            cards.append(f"""
                <div class="summary-card">
                    <h3>权限验证</h3>
                    <div class="value">{perm_data['permission_coverage_rate']:.1f}%</div>
                    <div class="label">权限覆盖率</div>
                </div>
            """)
        
        return "".join(cards)

    def _generate_recommendations_list(self, recommendations: List[str]) -> str:
        """生成建议列表"""
        return "".join(f"<li>{rec}</li>" for rec in recommendations)

    def _generate_api_usage_section(self, report: UnifiedTestReport) -> str:
        """生成API使用情况部分"""
        if not report.summary.get('api_usage'):
            return ""
        
        api_data = report.summary['api_usage']
        return f"""
            <div class="test-module">
                <h3>API使用情况检查</h3>
                <p>总页面数: {api_data['total_pages']}</p>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {api_data['v2_adoption_rate']:.1f}%"></div>
                </div>
                <p>V2 API采用率: {api_data['v2_adoption_rate']:.1f}%</p>
                <p>V1遗留页面: {api_data['v1_legacy_rate']:.1f}%</p>
                <p>存在问题的页面: {api_data['pages_with_issues']}</p>
            </div>
        """

    def _generate_crud_test_section(self, report: UnifiedTestReport) -> str:
        """生成CRUD测试部分"""
        if not report.summary.get('crud_testing'):
            return ""
        
        crud_data = report.summary['crud_testing']
        return f"""
            <div class="test-module">
                <h3>CRUD操作测试</h3>
                <p>总测试数: {crud_data['total_tests']}</p>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {crud_data['success_rate']:.1f}%"></div>
                </div>
                <p>测试通过率: {crud_data['success_rate']:.1f}%</p>
                <p>V2合规率: {crud_data['v2_compliance_rate']:.1f}%</p>
                <p>平均响应时间: {crud_data['avg_response_time']:.2f}s</p>
            </div>
        """

    def _generate_permission_validation_section(self, report: UnifiedTestReport) -> str:
        """生成权限验证部分"""
        if not report.summary.get('permission_validation'):
            return ""
        
        perm_data = report.summary['permission_validation']
        return f"""
            <div class="test-module">
                <h3>权限控制验证</h3>
                <p>总页面数: {perm_data['total_pages']}</p>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {perm_data['permission_coverage_rate']:.1f}%"></div>
                </div>
                <p>权限覆盖率: {perm_data['permission_coverage_rate']:.1f}%</p>
                <p>V2权限采用率: {perm_data['v2_adoption_rate']:.1f}%</p>
                <p>存在问题的页面: {perm_data['pages_with_issues']}</p>
            </div>
        """


async def main():
    parser = argparse.ArgumentParser(description='页面功能自动化测试框架')
    parser.add_argument('--web-root', default='web', help='Web项目根目录')
    parser.add_argument('--api-url', default='http://localhost:8000', help='API基础URL')
    parser.add_argument('--token', help='认证令牌')
    parser.add_argument('--output', default='unified_test_report.json', help='输出JSON报告文件')
    parser.add_argument('--html-output', default='unified_test_report.html', help='输出HTML报告文件')
    parser.add_argument('--skip-crud', action='store_true', help='跳过CRUD测试')
    
    args = parser.parse_args()
    
    framework = PageFunctionTestFramework(args.web_root, args.api_url, args.token)
    
    try:
        # 如果跳过CRUD测试，设置为None
        if args.skip_crud:
            framework.crud_tester = None
        
        report = await framework.run_comprehensive_test()
        
        # 保存报告
        framework.save_unified_report(report, args.output)
        framework.generate_unified_html_report(report, args.html_output)
        
        # 保存各个子报告
        if report.api_usage_report:
            framework.api_checker.save_report(
                framework.api_checker.generate_report([]), 
                "page_api_usage_report.json"
            )
            framework.api_checker.generate_html_report(
                framework.api_checker.generate_report([]), 
                "page_api_usage_report.html"
            )
        
        print("\n=== 综合测试完成 ===")
        print(f"综合评分: {report.summary['overall_score']:.1f}")
        print(f"测试模块: {sum(report.summary['test_modules'].values())}/3 完成")
        
        if report.summary.get('api_usage'):
            print(f"API v2采用率: {report.summary['api_usage']['v2_adoption_rate']:.1f}%")
        
        if report.summary.get('crud_testing'):
            print(f"CRUD测试通过率: {report.summary['crud_testing']['success_rate']:.1f}%")
        
        if report.summary.get('permission_validation'):
            print(f"权限覆盖率: {report.summary['permission_validation']['permission_coverage_rate']:.1f}%")
        
        print(f"\n关键建议:")
        for rec in report.summary['key_recommendations']:
            print(f"- {rec}")
        
        print(f"\n报告已保存:")
        print(f"- 综合报告: {args.output} 和 {args.html_output}")
        
        return 0
        
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))