"""
API变更日志记录机制
用于跟踪API版本变更和文档更新
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class ChangeType(str, Enum):
    """变更类型枚举"""
    ADDED = "added"           # 新增功能
    CHANGED = "changed"       # 修改功能
    DEPRECATED = "deprecated" # 弃用功能
    REMOVED = "removed"       # 删除功能
    FIXED = "fixed"          # 修复问题
    SECURITY = "security"     # 安全相关


@dataclass
class APIChange:
    """API变更记录"""
    version: str
    change_type: ChangeType
    endpoint: str
    method: str
    description: str
    date: str
    breaking_change: bool = False
    migration_guide: Optional[str] = None
    
    def to_dict(self) -> dict:
        return asdict(self)


class APIChangelogManager:
    """API变更日志管理器"""
    
    def __init__(self, changelog_file: str = "docs/api_changelog.json"):
        self.changelog_file = changelog_file
        self.ensure_changelog_file()
    
    def ensure_changelog_file(self):
        """确保变更日志文件存在"""
        os.makedirs(os.path.dirname(self.changelog_file), exist_ok=True)
        if not os.path.exists(self.changelog_file):
            self.save_changelog([])
    
    def load_changelog(self) -> List[Dict]:
        """加载变更日志"""
        try:
            with open(self.changelog_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_changelog(self, changelog: List[Dict]):
        """保存变更日志"""
        with open(self.changelog_file, 'w', encoding='utf-8') as f:
            json.dump(changelog, f, ensure_ascii=False, indent=2)
    
    def add_change(self, change: APIChange):
        """添加变更记录"""
        changelog = self.load_changelog()
        changelog.append(change.to_dict())
        # 按日期倒序排列
        changelog.sort(key=lambda x: x['date'], reverse=True)
        self.save_changelog(changelog)
    
    def get_changes_by_version(self, version: str) -> List[Dict]:
        """获取指定版本的变更记录"""
        changelog = self.load_changelog()
        return [change for change in changelog if change['version'] == version]
    
    def get_breaking_changes(self, from_version: str = None) -> List[Dict]:
        """获取破坏性变更"""
        changelog = self.load_changelog()
        breaking_changes = [change for change in changelog if change.get('breaking_change', False)]
        
        if from_version:
            # 过滤指定版本之后的破坏性变更
            breaking_changes = [
                change for change in breaking_changes 
                if self._version_compare(change['version'], from_version) > 0
            ]
        
        return breaking_changes
    
    def _version_compare(self, version1: str, version2: str) -> int:
        """简单的版本比较（假设版本格式为v1, v2等）"""
        v1_num = int(version1.lstrip('v'))
        v2_num = int(version2.lstrip('v'))
        return v1_num - v2_num
    
    def generate_markdown_changelog(self) -> str:
        """生成Markdown格式的变更日志"""
        changelog = self.load_changelog()
        
        if not changelog:
            return "# API变更日志\n\n暂无变更记录。\n"
        
        markdown = "# API变更日志\n\n"
        markdown += "本文档记录了API的所有变更历史。\n\n"
        
        # 按版本分组
        versions = {}
        for change in changelog:
            version = change['version']
            if version not in versions:
                versions[version] = []
            versions[version].append(change)
        
        # 生成每个版本的变更记录
        for version in sorted(versions.keys(), key=lambda x: int(x.lstrip('v')), reverse=True):
            changes = versions[version]
            markdown += f"## {version}\n\n"
            
            # 按变更类型分组
            change_types = {}
            for change in changes:
                change_type = change['change_type']
                if change_type not in change_types:
                    change_types[change_type] = []
                change_types[change_type].append(change)
            
            # 按优先级顺序显示变更类型
            type_order = [ChangeType.SECURITY, ChangeType.REMOVED, ChangeType.DEPRECATED, 
                         ChangeType.CHANGED, ChangeType.ADDED, ChangeType.FIXED]
            
            for change_type in type_order:
                if change_type.value in change_types:
                    type_changes = change_types[change_type.value]
                    markdown += f"### {change_type.value.title()}\n\n"
                    
                    for change in type_changes:
                        breaking_indicator = " 🚨" if change.get('breaking_change') else ""
                        markdown += f"- **{change['method']} {change['endpoint']}**{breaking_indicator}: {change['description']}\n"
                        
                        if change.get('migration_guide'):
                            markdown += f"  - 迁移指南: {change['migration_guide']}\n"
                    
                    markdown += "\n"
        
        return markdown
    
    def generate_html_changelog(self) -> str:
        """生成HTML格式的变更日志"""
        changelog = self.load_changelog()
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>API变更日志</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .version { margin-bottom: 30px; }
                .change-type { margin-bottom: 15px; }
                .change-item { margin-bottom: 10px; padding: 10px; border-left: 3px solid #ccc; }
                .breaking { border-left-color: #ff4444; background-color: #fff5f5; }
                .added { border-left-color: #00aa00; }
                .changed { border-left-color: #0066cc; }
                .deprecated { border-left-color: #ff8800; }
                .removed { border-left-color: #cc0000; }
                .fixed { border-left-color: #8800cc; }
                .security { border-left-color: #ff0000; background-color: #fff0f0; }
            </style>
        </head>
        <body>
            <h1>API变更日志</h1>
        """
        
        # 按版本分组并生成HTML
        versions = {}
        for change in changelog:
            version = change['version']
            if version not in versions:
                versions[version] = []
            versions[version].append(change)
        
        for version in sorted(versions.keys(), key=lambda x: int(x.lstrip('v')), reverse=True):
            changes = versions[version]
            html += f"<div class='version'><h2>{version}</h2>"
            
            for change in changes:
                css_class = change['change_type']
                if change.get('breaking_change'):
                    css_class += " breaking"
                
                breaking_indicator = " 🚨 破坏性变更" if change.get('breaking_change') else ""
                
                html += f"""
                <div class='change-item {css_class}'>
                    <strong>{change['method']} {change['endpoint']}</strong>{breaking_indicator}
                    <br>{change['description']}
                    <br><small>日期: {change['date']}</small>
                """
                
                if change.get('migration_guide'):
                    html += f"<br><em>迁移指南: {change['migration_guide']}</em>"
                
                html += "</div>"
            
            html += "</div>"
        
        html += "</body></html>"
        return html


# 全局变更日志管理器实例
changelog_manager = APIChangelogManager()

# 便捷函数
def log_api_change(
    version: str,
    change_type: ChangeType,
    endpoint: str,
    method: str,
    description: str,
    breaking_change: bool = False,
    migration_guide: Optional[str] = None
):
    """记录API变更"""
    change = APIChange(
        version=version,
        change_type=change_type,
        endpoint=endpoint,
        method=method,
        description=description,
        date=datetime.now().isoformat(),
        breaking_change=breaking_change,
        migration_guide=migration_guide
    )
    changelog_manager.add_change(change)

# 初始化一些示例变更记录
def initialize_sample_changelog():
    """初始化示例变更记录"""
    sample_changes = [
        APIChange(
            version="v2",
            change_type=ChangeType.ADDED,
            endpoint="/api/v2/users",
            method="GET",
            description="新增v2版本用户列表接口，使用标准化响应格式",
            date="2025-01-06T00:00:00",
            breaking_change=False
        ),
        APIChange(
            version="v2",
            change_type=ChangeType.ADDED,
            endpoint="/api/v2/health",
            method="GET",
            description="新增v2版本健康检查接口，包含API版本信息",
            date="2025-01-06T00:00:00",
            breaking_change=False
        ),
        APIChange(
            version="v2",
            change_type=ChangeType.CHANGED,
            endpoint="/api/v2/*",
            method="ALL",
            description="所有v2接口使用标准化响应格式，包含success、code、message、data、timestamp字段",
            date="2025-01-06T00:00:00",
            breaking_change=True,
            migration_guide="更新客户端代码以处理新的响应格式，检查success字段而不是code字段来判断请求是否成功"
        ),
        APIChange(
            version="v1",
            change_type=ChangeType.DEPRECATED,
            endpoint="/api/v1/*",
            method="ALL",
            description="v1版本接口已弃用，建议迁移到v2版本",
            date="2025-01-06T00:00:00",
            breaking_change=False,
            migration_guide="逐步迁移到v2版本接口，v1版本将在下个主要版本中移除"
        )
    ]
    
    for change in sample_changes:
        changelog_manager.add_change(change)

# 如果是首次运行，初始化示例数据
if not os.path.exists("docs/api_changelog.json"):
    initialize_sample_changelog()