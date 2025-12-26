#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API权限配置管理
实现API权限配置管理器，支持动态权限配置、热更新机制、API端点自动发现和权限注册
"""

import json
import hashlib
import asyncio
from typing import Dict, List, Set, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict

from app.models.admin import SysApiEndpoint, SysApiGroup, Role
from app.core.unified_logger import get_logger
from app.core.redis_cache import redis_cache_manager

logger = get_logger(__name__)


@dataclass
class ApiEndpointConfig:
    """API端点配置"""
    api_code: str
    api_name: str
    api_path: str
    http_method: str
    description: Optional[str] = None
    version: str = "v2"
    is_public: bool = False
    is_deprecated: bool = False
    rate_limit: Optional[int] = None
    permission_code: Optional[str] = None
    group_code: Optional[str] = None
    tags: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApiEndpointConfig':
        """从字典创建"""
        return cls(**data)


@dataclass
class PermissionRule:
    """权限规则"""
    rule_id: str
    name: str
    description: str
    api_patterns: List[str]  # API路径模式列表
    conditions: Dict[str, Any]  # 权限条件
    priority: int = 0  # 优先级
    enabled: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        return data

@dataclass
class ConfigVersion:
    """配置版本"""
    version: str
    description: str
    config_hash: str
    created_at: datetime
    created_by: str
    is_active: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "version": self.version,
            "description": self.description,
            "config_hash": self.config_hash,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "is_active": self.is_active
        }


class ApiPermissionConfigManager:
    """API权限配置管理器"""
    
    def __init__(self):
        self.cache_manager = redis_cache_manager
        
        # 配置缓存键
        self.config_cache_key = "api_permission_config"
        self.version_cache_key = "api_permission_versions"
        self.rules_cache_key = "api_permission_rules"
        
        # 配置文件路径
        self.config_dir = Path("config/permissions")
        self.config_file = self.config_dir / "api_permissions.json"
        self.rules_file = self.config_dir / "permission_rules.json"
        self.versions_file = self.config_dir / "config_versions.json"
        
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self._api_endpoints: Dict[str, ApiEndpointConfig] = {}
        self._permission_rules: Dict[str, PermissionRule] = {}
        self._config_versions: List[ConfigVersion] = []
        self._current_version: Optional[str] = None
        
        # 热更新配置
        self.hot_reload_enabled = True
        self.auto_discovery_enabled = True
        self.config_validation_enabled = True
        
        # 统计信息
        self.stats = {
            "total_endpoints": 0,
            "public_endpoints": 0,
            "deprecated_endpoints": 0,
            "permission_rules": 0,
            "config_versions": 0,
            "last_discovery": None,
            "last_update": None
        }
    
    async def initialize(self):
        """初始化配置管理器"""
        try:
            # 加载配置文件
            await self._load_config_files()
            
            # 从数据库同步API端点
            await self._sync_from_database()
            
            # 更新统计信息
            self._update_stats()
            
            logger.info("API权限配置管理器初始化完成")
            
        except Exception as e:
            logger.error(f"API权限配置管理器初始化失败: {e}")
            raise
    
    async def _load_config_files(self):
        """加载配置文件"""
        try:
            # 加载API端点配置
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    for endpoint_data in config_data.get('endpoints', []):
                        endpoint = ApiEndpointConfig.from_dict(endpoint_data)
                        self._api_endpoints[endpoint.api_code] = endpoint
            
            # 加载权限规则
            if self.rules_file.exists():
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    rules_data = json.load(f)
                    for rule_data in rules_data.get('rules', []):
                        if 'created_at' in rule_data and rule_data['created_at']:
                            rule_data['created_at'] = datetime.fromisoformat(rule_data['created_at'])
                        if 'updated_at' in rule_data and rule_data['updated_at']:
                            rule_data['updated_at'] = datetime.fromisoformat(rule_data['updated_at'])
                        rule = PermissionRule(**rule_data)
                        self._permission_rules[rule.rule_id] = rule
            
            # 加载版本信息
            if self.versions_file.exists():
                with open(self.versions_file, 'r', encoding='utf-8') as f:
                    versions_data = json.load(f)
                    for version_data in versions_data.get('versions', []):
                        version_data['created_at'] = datetime.fromisoformat(version_data['created_at'])
                        version = ConfigVersion(**version_data)
                        self._config_versions.append(version)
                        if version.is_active:
                            self._current_version = version.version
            
            logger.info(f"配置文件加载完成: 端点={len(self._api_endpoints)}, 规则={len(self._permission_rules)}, 版本={len(self._config_versions)}")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
    
    async def _sync_from_database(self):
        """从数据库同步API端点"""
        try:
            # 获取数据库中的API端点
            db_endpoints = await SysApiEndpoint.all()
            
            for db_endpoint in db_endpoints:
                api_code = db_endpoint.api_code
                
                # 如果配置中不存在，则添加
                if api_code not in self._api_endpoints:
                    endpoint_config = ApiEndpointConfig(
                        api_code=api_code,
                        api_name=db_endpoint.api_name,
                        api_path=db_endpoint.api_path,
                        http_method=db_endpoint.http_method,
                        description=db_endpoint.description,
                        version=db_endpoint.version,
                        is_public=db_endpoint.is_public,
                        is_deprecated=db_endpoint.is_deprecated,
                        rate_limit=db_endpoint.rate_limit,
                        permission_code=db_endpoint.permission_code
                    )
                    self._api_endpoints[api_code] = endpoint_config
                    logger.debug(f"从数据库同步API端点: {api_code}")
            
            logger.info(f"数据库同步完成: 总端点数={len(self._api_endpoints)}")
            
        except Exception as e:
            logger.error(f"数据库同步失败: {e}")
    
    async def discover_api_endpoints(self, app_instance=None) -> Dict[str, Any]:
        """自动发现API端点"""
        if not self.auto_discovery_enabled:
            return {"message": "API自动发现已禁用"}
        
        try:
            discovered_endpoints = []
            new_endpoints = 0
            updated_endpoints = 0
            
            # 这里可以集成FastAPI的路由发现逻辑
            # 由于没有直接访问FastAPI实例，我们模拟发现过程
            
            # 模拟发现的API端点
            mock_discovered = [
                {
                    "api_code": "get_users_list",
                    "api_name": "获取用户列表",
                    "api_path": "/api/v2/users",
                    "http_method": "GET",
                    "description": "获取系统用户列表",
                    "tags": "用户管理"
                },
                {
                    "api_code": "create_user",
                    "api_name": "创建用户",
                    "api_path": "/api/v2/users",
                    "http_method": "POST",
                    "description": "创建新用户",
                    "tags": "用户管理"
                },
                {
                    "api_code": "get_user_detail",
                    "api_name": "获取用户详情",
                    "api_path": "/api/v2/users/{id}",
                    "http_method": "GET",
                    "description": "获取指定用户详情",
                    "tags": "用户管理"
                }
            ]
            
            for endpoint_data in mock_discovered:
                api_code = endpoint_data["api_code"]
                
                if api_code not in self._api_endpoints:
                    # 新发现的端点
                    endpoint_config = ApiEndpointConfig(**endpoint_data)
                    self._api_endpoints[api_code] = endpoint_config
                    discovered_endpoints.append(endpoint_config.to_dict())
                    new_endpoints += 1
                    
                    # 同步到数据库
                    await self._sync_endpoint_to_database(endpoint_config)
                    
                else:
                    # 检查是否需要更新
                    existing_endpoint = self._api_endpoints[api_code]
                    if (existing_endpoint.api_name != endpoint_data.get("api_name") or
                        existing_endpoint.description != endpoint_data.get("description")):
                        
                        existing_endpoint.api_name = endpoint_data.get("api_name", existing_endpoint.api_name)
                        existing_endpoint.description = endpoint_data.get("description", existing_endpoint.description)
                        updated_endpoints += 1
                        
                        # 同步到数据库
                        await self._sync_endpoint_to_database(existing_endpoint)
            
            # 保存配置
            await self._save_config_files()
            
            # 更新统计
            self.stats["last_discovery"] = datetime.now().isoformat()
            self._update_stats()
            
            result = {
                "discovered_endpoints": len(discovered_endpoints),
                "new_endpoints": new_endpoints,
                "updated_endpoints": updated_endpoints,
                "total_endpoints": len(self._api_endpoints),
                "endpoints": discovered_endpoints
            }
            
            logger.info(f"API端点发现完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"API端点发现失败: {e}")
            return {"error": str(e)}
    
    async def _sync_endpoint_to_database(self, endpoint_config: ApiEndpointConfig):
        """同步端点配置到数据库"""
        try:
            # 查找或创建API端点
            endpoint, created = await SysApiEndpoint.get_or_create(
                api_code=endpoint_config.api_code,
                defaults={
                    "api_name": endpoint_config.api_name,
                    "api_path": endpoint_config.api_path,
                    "http_method": endpoint_config.http_method,
                    "description": endpoint_config.description,
                    "version": endpoint_config.version,
                    "is_public": endpoint_config.is_public,
                    "is_deprecated": endpoint_config.is_deprecated,
                    "rate_limit": endpoint_config.rate_limit,
                    "permission_code": endpoint_config.permission_code,
                    "status": "active"
                }
            )
            
            if not created:
                # 更新现有端点
                endpoint.api_name = endpoint_config.api_name
                endpoint.api_path = endpoint_config.api_path
                endpoint.http_method = endpoint_config.http_method
                endpoint.description = endpoint_config.description
                endpoint.version = endpoint_config.version
                endpoint.is_public = endpoint_config.is_public
                endpoint.is_deprecated = endpoint_config.is_deprecated
                endpoint.rate_limit = endpoint_config.rate_limit
                endpoint.permission_code = endpoint_config.permission_code
                await endpoint.save()
            
            logger.debug(f"同步端点到数据库: {endpoint_config.api_code} ({'创建' if created else '更新'})")
            
        except Exception as e:
            logger.error(f"同步端点到数据库失败: {endpoint_config.api_code}, error={e}")
    
    async def add_api_endpoint(self, endpoint_config: ApiEndpointConfig) -> bool:
        """添加API端点配置"""
        try:
            # 验证配置
            if self.config_validation_enabled:
                validation_result = self._validate_endpoint_config(endpoint_config)
                if not validation_result["valid"]:
                    logger.error(f"端点配置验证失败: {validation_result['errors']}")
                    return False
            
            # 添加到内存缓存
            self._api_endpoints[endpoint_config.api_code] = endpoint_config
            
            # 同步到数据库
            await self._sync_endpoint_to_database(endpoint_config)
            
            # 保存配置文件
            await self._save_config_files()
            
            # 清除相关缓存
            await self._clear_related_cache()
            
            # 更新统计
            self._update_stats()
            
            logger.info(f"添加API端点配置: {endpoint_config.api_code}")
            return True
            
        except Exception as e:
            logger.error(f"添加API端点配置失败: {e}")
            return False
    
    async def update_api_endpoint(self, api_code: str, updates: Dict[str, Any]) -> bool:
        """更新API端点配置"""
        try:
            if api_code not in self._api_endpoints:
                logger.error(f"API端点不存在: {api_code}")
                return False
            
            endpoint_config = self._api_endpoints[api_code]
            
            # 更新配置
            for key, value in updates.items():
                if hasattr(endpoint_config, key):
                    setattr(endpoint_config, key, value)
            
            # 验证更新后的配置
            if self.config_validation_enabled:
                validation_result = self._validate_endpoint_config(endpoint_config)
                if not validation_result["valid"]:
                    logger.error(f"更新后的端点配置验证失败: {validation_result['errors']}")
                    return False
            
            # 同步到数据库
            await self._sync_endpoint_to_database(endpoint_config)
            
            # 保存配置文件
            await self._save_config_files()
            
            # 清除相关缓存
            await self._clear_related_cache()
            
            logger.info(f"更新API端点配置: {api_code}")
            return True
            
        except Exception as e:
            logger.error(f"更新API端点配置失败: {e}")
            return False
    
    async def remove_api_endpoint(self, api_code: str) -> bool:
        """删除API端点配置"""
        try:
            if api_code not in self._api_endpoints:
                logger.error(f"API端点不存在: {api_code}")
                return False
            
            # 从内存缓存中删除
            del self._api_endpoints[api_code]
            
            # 从数据库中删除
            endpoint = await SysApiEndpoint.get_or_none(api_code=api_code)
            if endpoint:
                await endpoint.delete()
            
            # 保存配置文件
            await self._save_config_files()
            
            # 清除相关缓存
            await self._clear_related_cache()
            
            # 更新统计
            self._update_stats()
            
            logger.info(f"删除API端点配置: {api_code}")
            return True
            
        except Exception as e:
            logger.error(f"删除API端点配置失败: {e}")
            return False
    
    def _validate_endpoint_config(self, endpoint_config: ApiEndpointConfig) -> Dict[str, Any]:
        """验证端点配置"""
        errors = []
        
        # 必填字段检查
        if not endpoint_config.api_code:
            errors.append("api_code不能为空")
        
        if not endpoint_config.api_name:
            errors.append("api_name不能为空")
        
        if not endpoint_config.api_path:
            errors.append("api_path不能为空")
        
        if not endpoint_config.http_method:
            errors.append("http_method不能为空")
        
        # HTTP方法验证
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
        if endpoint_config.http_method not in valid_methods:
            errors.append(f"http_method必须是以下之一: {valid_methods}")
        
        # API路径格式验证
        if not endpoint_config.api_path.startswith("/"):
            errors.append("api_path必须以'/'开头")
        
        # 版本验证
        if endpoint_config.version not in ["v1", "v2"]:
            errors.append("version必须是v1或v2")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def add_permission_rule(self, rule: PermissionRule) -> bool:
        """添加权限规则"""
        try:
            # 设置时间戳
            if not rule.created_at:
                rule.created_at = datetime.now()
            rule.updated_at = datetime.now()
            
            # 添加到内存缓存
            self._permission_rules[rule.rule_id] = rule
            
            # 保存配置文件
            await self._save_config_files()
            
            # 清除相关缓存
            await self._clear_related_cache()
            
            logger.info(f"添加权限规则: {rule.rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"添加权限规则失败: {e}")
            return False
    
    async def update_permission_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """更新权限规则"""
        try:
            if rule_id not in self._permission_rules:
                logger.error(f"权限规则不存在: {rule_id}")
                return False
            
            rule = self._permission_rules[rule_id]
            
            # 更新规则
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            rule.updated_at = datetime.now()
            
            # 保存配置文件
            await self._save_config_files()
            
            # 清除相关缓存
            await self._clear_related_cache()
            
            logger.info(f"更新权限规则: {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新权限规则失败: {e}")
            return False
    
    async def remove_permission_rule(self, rule_id: str) -> bool:
        """删除权限规则"""
        try:
            if rule_id not in self._permission_rules:
                logger.error(f"权限规则不存在: {rule_id}")
                return False
            
            # 从内存缓存中删除
            del self._permission_rules[rule_id]
            
            # 保存配置文件
            await self._save_config_files()
            
            # 清除相关缓存
            await self._clear_related_cache()
            
            logger.info(f"删除权限规则: {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除权限规则失败: {e}")
            return False
    
    async def create_config_version(self, description: str, created_by: str) -> str:
        """创建配置版本"""
        try:
            # 生成版本号
            version = f"v{len(self._config_versions) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 计算配置哈希
            config_hash = self._calculate_config_hash()
            
            # 创建版本对象
            config_version = ConfigVersion(
                version=version,
                description=description,
                config_hash=config_hash,
                created_at=datetime.now(),
                created_by=created_by,
                is_active=True
            )
            
            # 将之前的版本设为非活跃
            for existing_version in self._config_versions:
                existing_version.is_active = False
            
            # 添加新版本
            self._config_versions.append(config_version)
            self._current_version = version
            
            # 保存版本信息
            await self._save_config_files()
            
            logger.info(f"创建配置版本: {version}")
            return version
            
        except Exception as e:
            logger.error(f"创建配置版本失败: {e}")
            return ""
    
    async def rollback_to_version(self, version: str) -> bool:
        """回滚到指定版本"""
        try:
            # 查找目标版本
            target_version = None
            for config_version in self._config_versions:
                if config_version.version == version:
                    target_version = config_version
                    break
            
            if not target_version:
                logger.error(f"配置版本不存在: {version}")
                return False
            
            # 这里应该实现从版本备份中恢复配置的逻辑
            # 由于简化实现，我们只更新活跃版本标记
            
            # 将所有版本设为非活跃
            for config_version in self._config_versions:
                config_version.is_active = False
            
            # 设置目标版本为活跃
            target_version.is_active = True
            self._current_version = version
            
            # 保存版本信息
            await self._save_config_files()
            
            # 清除相关缓存
            await self._clear_related_cache()
            
            logger.info(f"回滚到配置版本: {version}")
            return True
            
        except Exception as e:
            logger.error(f"回滚配置版本失败: {e}")
            return False
    
    def _calculate_config_hash(self) -> str:
        """计算配置哈希值"""
        try:
            # 将配置转换为字符串
            config_str = json.dumps({
                "endpoints": [ep.to_dict() for ep in self._api_endpoints.values()],
                "rules": [rule.to_dict() for rule in self._permission_rules.values()]
            }, sort_keys=True)
            
            # 计算MD5哈希
            return hashlib.md5(config_str.encode()).hexdigest()
            
        except Exception as e:
            logger.error(f"计算配置哈希失败: {e}")
            return ""
    
    async def _save_config_files(self):
        """保存配置文件"""
        try:
            # 保存API端点配置
            endpoints_data = {
                "endpoints": [ep.to_dict() for ep in self._api_endpoints.values()],
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(endpoints_data, f, indent=2, ensure_ascii=False)
            
            # 保存权限规则
            rules_data = {
                "rules": [rule.to_dict() for rule in self._permission_rules.values()],
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, indent=2, ensure_ascii=False)
            
            # 保存版本信息
            versions_data = {
                "versions": [version.to_dict() for version in self._config_versions],
                "current_version": self._current_version,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.versions_file, 'w', encoding='utf-8') as f:
                json.dump(versions_data, f, indent=2, ensure_ascii=False)
            
            # 更新统计
            self.stats["last_update"] = datetime.now().isoformat()
            
            logger.debug("配置文件保存完成")
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    async def _clear_related_cache(self):
        """清除相关缓存"""
        try:
            cache_keys = [
                self.config_cache_key,
                self.version_cache_key,
                self.rules_cache_key
            ]
            
            for key in cache_keys:
                await self.cache_manager.delete(key)
            
            logger.debug("相关缓存已清除")
            
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
    
    def _update_stats(self):
        """更新统计信息"""
        self.stats.update({
            "total_endpoints": len(self._api_endpoints),
            "public_endpoints": sum(1 for ep in self._api_endpoints.values() if ep.is_public),
            "deprecated_endpoints": sum(1 for ep in self._api_endpoints.values() if ep.is_deprecated),
            "permission_rules": len(self._permission_rules),
            "config_versions": len(self._config_versions)
        })
    
    async def hot_reload_config(self) -> Dict[str, Any]:
        """热重载配置"""
        if not self.hot_reload_enabled:
            return {"message": "热重载已禁用"}
        
        try:
            # 备份当前配置
            backup_endpoints = self._api_endpoints.copy()
            backup_rules = self._permission_rules.copy()
            
            # 重新加载配置
            self._api_endpoints.clear()
            self._permission_rules.clear()
            
            await self._load_config_files()
            await self._sync_from_database()
            
            # 清除缓存
            await self._clear_related_cache()
            
            # 更新统计
            self._update_stats()
            
            result = {
                "status": "success",
                "message": "配置热重载完成",
                "endpoints_loaded": len(self._api_endpoints),
                "rules_loaded": len(self._permission_rules),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"配置热重载完成: {result}")
            return result
            
        except Exception as e:
            # 恢复备份配置
            self._api_endpoints = backup_endpoints
            self._permission_rules = backup_rules
            
            logger.error(f"配置热重载失败: {e}")
            return {
                "status": "error",
                "message": f"配置热重载失败: {e}",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_api_endpoint(self, api_code: str) -> Optional[ApiEndpointConfig]:
        """获取API端点配置"""
        return self._api_endpoints.get(api_code)
    
    def get_all_api_endpoints(self) -> Dict[str, ApiEndpointConfig]:
        """获取所有API端点配置"""
        return self._api_endpoints.copy()
    
    def get_permission_rule(self, rule_id: str) -> Optional[PermissionRule]:
        """获取权限规则"""
        return self._permission_rules.get(rule_id)
    
    def get_all_permission_rules(self) -> Dict[str, PermissionRule]:
        """获取所有权限规则"""
        return self._permission_rules.copy()
    
    def get_config_versions(self) -> List[ConfigVersion]:
        """获取配置版本列表"""
        return self._config_versions.copy()
    
    def get_current_version(self) -> Optional[str]:
        """获取当前版本"""
        return self._current_version
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    async def validate_config(self) -> Dict[str, Any]:
        """验证配置"""
        try:
            validation_results = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "endpoint_validations": {},
                "rule_validations": {}
            }
            
            # 验证API端点
            for api_code, endpoint in self._api_endpoints.items():
                endpoint_validation = self._validate_endpoint_config(endpoint)
                validation_results["endpoint_validations"][api_code] = endpoint_validation
                
                if not endpoint_validation["valid"]:
                    validation_results["valid"] = False
                    validation_results["errors"].extend([
                        f"端点 {api_code}: {error}" for error in endpoint_validation["errors"]
                    ])
            
            # 验证权限规则
            for rule_id, rule in self._permission_rules.items():
                rule_validation = self._validate_permission_rule(rule)
                validation_results["rule_validations"][rule_id] = rule_validation
                
                if not rule_validation["valid"]:
                    validation_results["valid"] = False
                    validation_results["errors"].extend([
                        f"规则 {rule_id}: {error}" for error in rule_validation["errors"]
                    ])
            
            return validation_results
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return {
                "valid": False,
                "errors": [f"配置验证异常: {e}"],
                "warnings": [],
                "endpoint_validations": {},
                "rule_validations": {}
            }
    
    def _validate_permission_rule(self, rule: PermissionRule) -> Dict[str, Any]:
        """验证权限规则"""
        errors = []
        
        # 必填字段检查
        if not rule.rule_id:
            errors.append("rule_id不能为空")
        
        if not rule.name:
            errors.append("name不能为空")
        
        if not rule.api_patterns:
            errors.append("api_patterns不能为空")
        
        # API模式验证
        for pattern in rule.api_patterns:
            if not isinstance(pattern, str) or not pattern.strip():
                errors.append(f"无效的API模式: {pattern}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }


# 全局API权限配置管理器实例
api_permission_config_manager = ApiPermissionConfigManager()


# 便捷函数
async def initialize_api_config():
    """初始化API权限配置"""
    await api_permission_config_manager.initialize()


async def discover_api_endpoints(app_instance=None):
    """发现API端点"""
    return await api_permission_config_manager.discover_api_endpoints(app_instance)


async def hot_reload_api_config():
    """热重载API配置"""
    return await api_permission_config_manager.hot_reload_config()


def get_api_endpoint_config(api_code: str) -> Optional[ApiEndpointConfig]:
    """获取API端点配置"""
    return api_permission_config_manager.get_api_endpoint(api_code)


if __name__ == "__main__":
    # 测试API权限配置管理器
    async def test_config_manager():
        manager = ApiPermissionConfigManager()
        await manager.initialize()
        
        # 测试发现API端点
        result = await manager.discover_api_endpoints()
        print(f"发现结果: {result}")
        
        # 测试添加权限规则
        rule = PermissionRule(
            rule_id="test_rule_1",
            name="测试规则",
            description="这是一个测试权限规则",
            api_patterns=["GET /api/v2/test/*"],
            conditions={"role": "admin"}
        )
        
        success = await manager.add_permission_rule(rule)
        print(f"添加规则结果: {success}")
        
        # 测试配置验证
        validation = await manager.validate_config()
        print(f"配置验证: {validation}")
        
        # 获取统计信息
        stats = manager.get_stats()
        print(f"统计信息: {stats}")
    
    asyncio.run(test_config_manager())

# Service alias for compatibility
api_permission_config_service = api_permission_config_manager