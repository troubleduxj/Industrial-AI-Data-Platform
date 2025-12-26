"""
文档同步服务
建立文档版本管理和自动更新流程，确保文档与代码同步
"""
import os
import json
import hashlib
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.services.swagger_documentation_service import SwaggerDocumentationService


@dataclass
class DocumentationVersion:
    """文档版本信息"""
    version: str
    timestamp: str
    api_hash: str
    changes: List[str]
    endpoints_count: int
    modules_count: int


@dataclass
class EndpointChange:
    """端点变更信息"""
    path: str
    method: str
    change_type: str  # "added", "modified", "removed"
    description: str
    timestamp: str


class DocumentationSyncService:
    """文档同步服务"""
    
    def __init__(self, app: FastAPI, swagger_service: SwaggerDocumentationService):
        self.app = app
        self.swagger_service = swagger_service
        self.versions_file = "docs/api-v2/versions.json"
        self.changes_file = "docs/api-v2/changes.json"
        self.sync_config_file = "docs/api-v2/sync-config.json"
        self.ensure_sync_files()
    
    def ensure_sync_files(self):
        """确保同步文件存在"""
        os.makedirs("docs/api-v2", exist_ok=True)
        
        # 初始化版本文件
        if not os.path.exists(self.versions_file):
            with open(self.versions_file, "w", encoding="utf-8") as f:
                json.dump({"versions": [], "current_version": None}, f, ensure_ascii=False, indent=2)
        
        # 初始化变更文件
        if not os.path.exists(self.changes_file):
            with open(self.changes_file, "w", encoding="utf-8") as f:
                json.dump({"changes": []}, f, ensure_ascii=False, indent=2)
        
        # 初始化同步配置文件
        if not os.path.exists(self.sync_config_file):
            default_config = {
                "auto_sync": True,
                "sync_on_startup": True,
                "sync_interval_minutes": 60,
                "track_changes": True,
                "generate_changelog": True,
                "backup_versions": 10,
                "excluded_paths": [
                    "/docs",
                    "/redoc", 
                    "/openapi.json",
                    "/health"
                ],
                "notification_webhook": None,
                "last_sync": None
            }
            with open(self.sync_config_file, "w", encoding="utf-8") as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
    
    def load_sync_config(self) -> Dict[str, Any]:
        """加载同步配置"""
        try:
            with open(self.sync_config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"auto_sync": True, "track_changes": True}
    
    def save_sync_config(self, config: Dict[str, Any]):
        """保存同步配置"""
        with open(self.sync_config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def load_versions(self) -> Dict[str, Any]:
        """加载版本信息"""
        try:
            with open(self.versions_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"versions": [], "current_version": None}
    
    def save_versions(self, versions_data: Dict[str, Any]):
        """保存版本信息"""
        with open(self.versions_file, "w", encoding="utf-8") as f:
            json.dump(versions_data, f, ensure_ascii=False, indent=2)
    
    def load_changes(self) -> Dict[str, Any]:
        """加载变更记录"""
        try:
            with open(self.changes_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"changes": []}
    
    def save_changes(self, changes_data: Dict[str, Any]):
        """保存变更记录"""
        with open(self.changes_file, "w", encoding="utf-8") as f:
            json.dump(changes_data, f, ensure_ascii=False, indent=2)
    
    def calculate_api_hash(self) -> str:
        """计算API结构哈希值"""
        api_structure = []
        
        for route in self.app.routes:
            if isinstance(route, APIRoute):
                # 只关注v2 API
                if route.path.startswith("/api/v2/"):
                    api_structure.append({
                        "path": route.path,
                        "methods": list(route.methods),
                        "name": route.name,
                        "summary": getattr(route, "summary", ""),
                        "description": getattr(route, "description", "")
                    })
        
        # 排序确保一致性
        api_structure.sort(key=lambda x: (x["path"], str(x["methods"])))
        
        # 计算哈希
        api_json = json.dumps(api_structure, sort_keys=True)
        return hashlib.md5(api_json.encode()).hexdigest()
    
    async def detect_changes(self) -> List[EndpointChange]:
        """检测API变更"""
        current_endpoints = self._get_current_endpoints()
        versions_data = self.load_versions()
        
        if not versions_data["versions"]:
            # 首次运行，所有端点都是新增的
            changes = []
            for endpoint in current_endpoints:
                changes.append(EndpointChange(
                    path=endpoint["path"],
                    method=endpoint["method"],
                    change_type="added",
                    description=f"新增端点: {endpoint['method']} {endpoint['path']}",
                    timestamp=datetime.now().isoformat()
                ))
            return changes
        
        # 获取最新版本的端点
        latest_version = versions_data["versions"][-1]
        previous_endpoints = self._load_version_endpoints(latest_version["version"])
        
        changes = []
        current_set = {(ep["path"], ep["method"]) for ep in current_endpoints}
        previous_set = {(ep["path"], ep["method"]) for ep in previous_endpoints}
        
        # 检测新增端点
        for endpoint in current_endpoints:
            key = (endpoint["path"], endpoint["method"])
            if key not in previous_set:
                changes.append(EndpointChange(
                    path=endpoint["path"],
                    method=endpoint["method"],
                    change_type="added",
                    description=f"新增端点: {endpoint['method']} {endpoint['path']}",
                    timestamp=datetime.now().isoformat()
                ))
        
        # 检测删除的端点
        for endpoint in previous_endpoints:
            key = (endpoint["path"], endpoint["method"])
            if key not in current_set:
                changes.append(EndpointChange(
                    path=endpoint["path"],
                    method=endpoint["method"],
                    change_type="removed",
                    description=f"删除端点: {endpoint['method']} {endpoint['path']}",
                    timestamp=datetime.now().isoformat()
                ))
        
        # 检测修改的端点（基于摘要或描述变化）
        for current_ep in current_endpoints:
            key = (current_ep["path"], current_ep["method"])
            if key in previous_set:
                previous_ep = next(ep for ep in previous_endpoints if (ep["path"], ep["method"]) == key)
                if (current_ep.get("summary") != previous_ep.get("summary") or 
                    current_ep.get("description") != previous_ep.get("description")):
                    changes.append(EndpointChange(
                        path=current_ep["path"],
                        method=current_ep["method"],
                        change_type="modified",
                        description=f"修改端点: {current_ep['method']} {current_ep['path']}",
                        timestamp=datetime.now().isoformat()
                    ))
        
        return changes
    
    def _get_current_endpoints(self) -> List[Dict[str, Any]]:
        """获取当前端点列表"""
        endpoints = []
        
        for route in self.app.routes:
            if isinstance(route, APIRoute) and route.path.startswith("/api/v2/"):
                for method in route.methods:
                    if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                        endpoints.append({
                            "path": route.path,
                            "method": method.upper(),
                            "name": route.name,
                            "summary": getattr(route, "summary", ""),
                            "description": getattr(route, "description", ""),
                            "tags": getattr(route, "tags", [])
                        })
        
        return endpoints
    
    def _load_version_endpoints(self, version: str) -> List[Dict[str, Any]]:
        """加载指定版本的端点信息"""
        version_file = f"docs/api-v2/versions/{version}/endpoints.json"
        try:
            with open(version_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    
    def _save_version_endpoints(self, version: str, endpoints: List[Dict[str, Any]]):
        """保存版本端点信息"""
        version_dir = f"docs/api-v2/versions/{version}"
        os.makedirs(version_dir, exist_ok=True)
        
        with open(f"{version_dir}/endpoints.json", "w", encoding="utf-8") as f:
            json.dump(endpoints, f, ensure_ascii=False, indent=2)
    
    async def sync_documentation(self, force: bool = False) -> Dict[str, Any]:
        """同步文档"""
        config = self.load_sync_config()
        
        if not force and not config.get("auto_sync", True):
            return {"status": "skipped", "reason": "auto_sync disabled"}
        
        # 计算当前API哈希
        current_hash = self.calculate_api_hash()
        versions_data = self.load_versions()
        
        # 检查是否有变更
        if versions_data["versions"] and versions_data["versions"][-1]["api_hash"] == current_hash:
            if not force:
                return {"status": "no_changes", "hash": current_hash}
        
        # 检测变更
        changes = await self.detect_changes()
        
        # 生成新版本
        new_version = self._generate_version_number()
        current_endpoints = self._get_current_endpoints()
        
        # 保存版本端点信息
        self._save_version_endpoints(new_version, current_endpoints)
        
        # 创建版本记录
        version_record = DocumentationVersion(
            version=new_version,
            timestamp=datetime.now().isoformat(),
            api_hash=current_hash,
            changes=[asdict(change) for change in changes],
            endpoints_count=len(current_endpoints),
            modules_count=len(set(ep.get("tags", [""])[0] for ep in current_endpoints if ep.get("tags")))
        )
        
        # 更新版本记录
        versions_data["versions"].append(asdict(version_record))
        versions_data["current_version"] = new_version
        
        # 保持版本数量限制
        max_versions = config.get("backup_versions", 10)
        if len(versions_data["versions"]) > max_versions:
            # 删除旧版本文件
            old_version = versions_data["versions"][0]["version"]
            old_version_dir = f"docs/api-v2/versions/{old_version}"
            if os.path.exists(old_version_dir):
                import shutil
                shutil.rmtree(old_version_dir)
            
            versions_data["versions"] = versions_data["versions"][-max_versions:]
        
        self.save_versions(versions_data)
        
        # 记录变更
        if config.get("track_changes", True) and changes:
            changes_data = self.load_changes()
            changes_data["changes"].extend([asdict(change) for change in changes])
            # 保持最近1000条变更记录
            changes_data["changes"] = changes_data["changes"][-1000:]
            self.save_changes(changes_data)
        
        # 生成文档文件
        await self.swagger_service.save_documentation_files()
        
        # 生成变更日志
        if config.get("generate_changelog", True):
            await self._generate_changelog()
        
        # 更新同步配置
        config["last_sync"] = datetime.now().isoformat()
        self.save_sync_config(config)
        
        # 发送通知（如果配置了webhook）
        if config.get("notification_webhook") and changes:
            await self._send_change_notification(config["notification_webhook"], changes)
        
        return {
            "status": "success",
            "version": new_version,
            "changes_count": len(changes),
            "endpoints_count": len(current_endpoints),
            "hash": current_hash
        }
    
    def _generate_version_number(self) -> str:
        """生成版本号"""
        versions_data = self.load_versions()
        
        if not versions_data["versions"]:
            return "2.0.0"
        
        # 简单的版本递增策略
        latest_version = versions_data["versions"][-1]["version"]
        try:
            major, minor, patch = map(int, latest_version.split("."))
            return f"{major}.{minor}.{patch + 1}"
        except:
            return f"2.0.{len(versions_data['versions']) + 1}"
    
    async def _generate_changelog(self):
        """生成变更日志"""
        versions_data = self.load_versions()
        changes_data = self.load_changes()
        
        changelog_md = "# API变更日志\n\n"
        changelog_md += "本文档记录了系统管理API v2的所有变更历史。\n\n"
        
        # 按版本组织变更
        for version_info in reversed(versions_data["versions"][-10:]):  # 最近10个版本
            version = version_info["version"]
            timestamp = version_info["timestamp"]
            version_changes = version_info.get("changes", [])
            
            if version_changes:
                changelog_md += f"## 版本 {version}\n\n"
                changelog_md += f"**发布时间**: {timestamp}\n\n"
                changelog_md += f"**端点数量**: {version_info.get('endpoints_count', 0)}\n\n"
                
                # 按变更类型分组
                added = [c for c in version_changes if c.get("change_type") == "added"]
                modified = [c for c in version_changes if c.get("change_type") == "modified"]
                removed = [c for c in version_changes if c.get("change_type") == "removed"]
                
                if added:
                    changelog_md += "### 新增\n\n"
                    for change in added:
                        changelog_md += f"- `{change['method']} {change['path']}` - {change['description']}\n"
                    changelog_md += "\n"
                
                if modified:
                    changelog_md += "### 修改\n\n"
                    for change in modified:
                        changelog_md += f"- `{change['method']} {change['path']}` - {change['description']}\n"
                    changelog_md += "\n"
                
                if removed:
                    changelog_md += "### 删除\n\n"
                    for change in removed:
                        changelog_md += f"- `{change['method']} {change['path']}` - {change['description']}\n"
                    changelog_md += "\n"
                
                changelog_md += "---\n\n"
        
        # 保存变更日志
        with open("docs/api-v2/CHANGELOG.md", "w", encoding="utf-8") as f:
            f.write(changelog_md)
    
    async def _send_change_notification(self, webhook_url: str, changes: List[EndpointChange]):
        """发送变更通知"""
        try:
            import aiohttp
            
            notification_data = {
                "title": "API文档变更通知",
                "timestamp": datetime.now().isoformat(),
                "changes_count": len(changes),
                "changes": [asdict(change) for change in changes[:10]]  # 最多发送10条变更
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=notification_data) as response:
                    if response.status == 200:
                        print(f"变更通知发送成功: {len(changes)}条变更")
                    else:
                        print(f"变更通知发送失败: {response.status}")
        except Exception as e:
            print(f"发送变更通知时出错: {e}")
    
    async def get_version_info(self, version: Optional[str] = None) -> Dict[str, Any]:
        """获取版本信息"""
        versions_data = self.load_versions()
        
        if not version:
            # 返回当前版本信息
            if versions_data["versions"]:
                return versions_data["versions"][-1]
            else:
                return {"error": "No versions found"}
        
        # 查找指定版本
        for version_info in versions_data["versions"]:
            if version_info["version"] == version:
                return version_info
        
        return {"error": f"Version {version} not found"}
    
    async def get_changes_since_version(self, since_version: str) -> List[Dict[str, Any]]:
        """获取指定版本以来的所有变更"""
        versions_data = self.load_versions()
        
        # 找到指定版本的索引
        since_index = -1
        for i, version_info in enumerate(versions_data["versions"]):
            if version_info["version"] == since_version:
                since_index = i
                break
        
        if since_index == -1:
            return []
        
        # 收集后续版本的所有变更
        all_changes = []
        for version_info in versions_data["versions"][since_index + 1:]:
            all_changes.extend(version_info.get("changes", []))
        
        return all_changes
    
    async def rollback_to_version(self, target_version: str) -> Dict[str, Any]:
        """回滚到指定版本（仅文档，不影响代码）"""
        versions_data = self.load_versions()
        
        # 查找目标版本
        target_version_info = None
        for version_info in versions_data["versions"]:
            if version_info["version"] == target_version:
                target_version_info = version_info
                break
        
        if not target_version_info:
            return {"error": f"Version {target_version} not found"}
        
        # 加载目标版本的端点信息
        target_endpoints = self._load_version_endpoints(target_version)
        
        if not target_endpoints:
            return {"error": f"Endpoints data for version {target_version} not found"}
        
        # 这里只是文档回滚，实际的API端点由代码控制
        # 可以生成一个回滚报告，显示需要的代码变更
        current_endpoints = self._get_current_endpoints()
        
        rollback_report = {
            "target_version": target_version,
            "current_endpoints": len(current_endpoints),
            "target_endpoints": len(target_endpoints),
            "rollback_timestamp": datetime.now().isoformat(),
            "note": "This is a documentation rollback report. Actual API changes require code modifications."
        }
        
        # 保存回滚报告
        rollback_dir = "docs/api-v2/rollbacks"
        os.makedirs(rollback_dir, exist_ok=True)
        
        rollback_file = f"{rollback_dir}/rollback-to-{target_version}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(rollback_file, "w", encoding="utf-8") as f:
            json.dump(rollback_report, f, ensure_ascii=False, indent=2)
        
        return rollback_report


# 全局同步服务实例
sync_service: Optional[DocumentationSyncService] = None


def get_sync_service() -> Optional[DocumentationSyncService]:
    """获取文档同步服务实例"""
    return sync_service


def init_sync_service(app: FastAPI, swagger_service: SwaggerDocumentationService):
    """初始化文档同步服务"""
    global sync_service
    sync_service = DocumentationSyncService(app, swagger_service)
    return sync_service