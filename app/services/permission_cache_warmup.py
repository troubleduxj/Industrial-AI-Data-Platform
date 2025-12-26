#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限缓存预热服务
实现权限缓存的预加载和预热机制，提高系统启动后的响应性能
"""

import asyncio
from typing import List, Dict, Set, Optional, Any
from datetime import datetime, timedelta

from app.models.admin import User, Role, Menu, SysApiEndpoint
from app.core.permission_cache import permission_cache_manager
from app.services.permission_service import permission_service
from app.core.unified_logger import get_logger

logger = get_logger(__name__)


class PermissionCacheWarmupService:
    """权限缓存预热服务"""
    
    def __init__(self):
        self.cache_manager = permission_cache_manager
        self.permission_service = permission_service
        
        # 预热配置
        self.warmup_batch_size = 50  # 批量预热大小
        self.warmup_delay = 0.1  # 预热间隔（秒）
        self.max_concurrent_warmup = 10  # 最大并发预热数
        
        # 预热策略
        self.warmup_active_users_only = True  # 只预热活跃用户
        self.warmup_recent_days = 30  # 预热最近N天活跃的用户
        self.warmup_priority_roles = ["admin", "manager"]  # 优先预热的角色
    
    async def warmup_all_permissions(self) -> Dict[str, Any]:
        """预热所有权限缓存"""
        logger.info("开始权限缓存全量预热...")
        start_time = datetime.now()
        
        results = {
            "start_time": start_time.isoformat(),
            "user_permissions": {"total": 0, "success": 0, "failed": 0},
            "user_roles": {"total": 0, "success": 0, "failed": 0},
            "user_menus": {"total": 0, "success": 0, "failed": 0},
            "role_permissions": {"total": 0, "success": 0, "failed": 0},
            "errors": []
        }
        
        try:
            # 1. 预热用户权限
            user_result = await self._warmup_user_permissions()
            results["user_permissions"] = user_result
            
            # 2. 预热用户角色
            role_result = await self._warmup_user_roles()
            results["user_roles"] = role_result
            
            # 3. 预热用户菜单
            menu_result = await self._warmup_user_menus()
            results["user_menus"] = menu_result
            
            # 4. 预热角色权限
            role_perm_result = await self._warmup_role_permissions()
            results["role_permissions"] = role_perm_result
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            results.update({
                "end_time": end_time.isoformat(),
                "duration_seconds": round(duration, 2),
                "status": "completed"
            })
            
            total_success = (
                results["user_permissions"]["success"] +
                results["user_roles"]["success"] +
                results["user_menus"]["success"] +
                results["role_permissions"]["success"]
            )
            
            total_items = (
                results["user_permissions"]["total"] +
                results["user_roles"]["total"] +
                results["user_menus"]["total"] +
                results["role_permissions"]["total"]
            )
            
            logger.info(f"权限缓存预热完成: 总数={total_items}, 成功={total_success}, 耗时={duration:.2f}秒")
            
        except Exception as e:
            logger.error(f"权限缓存预热失败: {e}")
            results["status"] = "failed"
            results["error"] = str(e)
        
        return results
    
    async def _warmup_user_permissions(self) -> Dict[str, int]:
        """预热用户权限缓存"""
        logger.info("开始预热用户权限缓存...")
        
        try:
            # 获取需要预热的用户列表
            users = await self._get_warmup_users()
            user_ids = [user.id for user in users]
            
            if not user_ids:
                logger.warning("没有找到需要预热的用户")
                return {"total": 0, "success": 0, "failed": 0}
            
            # 批量预热用户权限
            results = await self.cache_manager.preload_user_permissions(user_ids)
            
            success_count = sum(1 for success in results.values() if success)
            failed_count = len(results) - success_count
            
            logger.info(f"用户权限缓存预热完成: 总数={len(user_ids)}, 成功={success_count}, 失败={failed_count}")
            
            return {
                "total": len(user_ids),
                "success": success_count,
                "failed": failed_count
            }
            
        except Exception as e:
            logger.error(f"预热用户权限缓存失败: {e}")
            return {"total": 0, "success": 0, "failed": 1}
    
    async def _warmup_user_roles(self) -> Dict[str, int]:
        """预热用户角色缓存"""
        logger.info("开始预热用户角色缓存...")
        
        try:
            users = await self._get_warmup_users()
            
            success_count = 0
            failed_count = 0
            
            # 分批处理
            for i in range(0, len(users), self.warmup_batch_size):
                batch_users = users[i:i + self.warmup_batch_size]
                
                # 并发预热这一批用户的角色
                tasks = []
                for user in batch_users:
                    task = self._warmup_single_user_roles(user.id)
                    tasks.append(task)
                
                # 限制并发数
                semaphore = asyncio.Semaphore(self.max_concurrent_warmup)
                
                async def limited_task(task):
                    async with semaphore:
                        return await task
                
                batch_results = await asyncio.gather(
                    *[limited_task(task) for task in tasks],
                    return_exceptions=True
                )
                
                # 统计结果
                for result in batch_results:
                    if isinstance(result, Exception):
                        failed_count += 1
                    elif result:
                        success_count += 1
                    else:
                        failed_count += 1
                
                # 添加延迟避免过载
                if i + self.warmup_batch_size < len(users):
                    await asyncio.sleep(self.warmup_delay)
            
            logger.info(f"用户角色缓存预热完成: 总数={len(users)}, 成功={success_count}, 失败={failed_count}")
            
            return {
                "total": len(users),
                "success": success_count,
                "failed": failed_count
            }
            
        except Exception as e:
            logger.error(f"预热用户角色缓存失败: {e}")
            return {"total": 0, "success": 0, "failed": 1}
    
    async def _warmup_user_menus(self) -> Dict[str, int]:
        """预热用户菜单缓存"""
        logger.info("开始预热用户菜单缓存...")
        
        try:
            users = await self._get_warmup_users()
            
            success_count = 0
            failed_count = 0
            
            # 分批处理
            for i in range(0, len(users), self.warmup_batch_size):
                batch_users = users[i:i + self.warmup_batch_size]
                
                # 并发预热这一批用户的菜单
                tasks = []
                for user in batch_users:
                    task = self._warmup_single_user_menus(user.id)
                    tasks.append(task)
                
                # 限制并发数
                semaphore = asyncio.Semaphore(self.max_concurrent_warmup)
                
                async def limited_task(task):
                    async with semaphore:
                        return await task
                
                batch_results = await asyncio.gather(
                    *[limited_task(task) for task in tasks],
                    return_exceptions=True
                )
                
                # 统计结果
                for result in batch_results:
                    if isinstance(result, Exception):
                        failed_count += 1
                    elif result:
                        success_count += 1
                    else:
                        failed_count += 1
                
                # 添加延迟避免过载
                if i + self.warmup_batch_size < len(users):
                    await asyncio.sleep(self.warmup_delay)
            
            logger.info(f"用户菜单缓存预热完成: 总数={len(users)}, 成功={success_count}, 失败={failed_count}")
            
            return {
                "total": len(users),
                "success": success_count,
                "failed": failed_count
            }
            
        except Exception as e:
            logger.error(f"预热用户菜单缓存失败: {e}")
            return {"total": 0, "success": 0, "failed": 1}
    
    async def _warmup_role_permissions(self) -> Dict[str, int]:
        """预热角色权限缓存"""
        logger.info("开始预热角色权限缓存...")
        
        try:
            # 获取所有活跃角色
            roles = await Role.filter(status='0', del_flag='0').all()
            
            success_count = 0
            failed_count = 0
            
            # 分批处理
            for i in range(0, len(roles), self.warmup_batch_size):
                batch_roles = roles[i:i + self.warmup_batch_size]
                
                # 并发预热这一批角色的权限
                tasks = []
                for role in batch_roles:
                    task = self._warmup_single_role_permissions(role.id)
                    tasks.append(task)
                
                # 限制并发数
                semaphore = asyncio.Semaphore(self.max_concurrent_warmup)
                
                async def limited_task(task):
                    async with semaphore:
                        return await task
                
                batch_results = await asyncio.gather(
                    *[limited_task(task) for task in tasks],
                    return_exceptions=True
                )
                
                # 统计结果
                for result in batch_results:
                    if isinstance(result, Exception):
                        failed_count += 1
                    elif result:
                        success_count += 1
                    else:
                        failed_count += 1
                
                # 添加延迟避免过载
                if i + self.warmup_batch_size < len(roles):
                    await asyncio.sleep(self.warmup_delay)
            
            logger.info(f"角色权限缓存预热完成: 总数={len(roles)}, 成功={success_count}, 失败={failed_count}")
            
            return {
                "total": len(roles),
                "success": success_count,
                "failed": failed_count
            }
            
        except Exception as e:
            logger.error(f"预热角色权限缓存失败: {e}")
            return {"total": 0, "success": 0, "failed": 1}
    
    async def _get_warmup_users(self) -> List[User]:
        """获取需要预热的用户列表"""
        try:
            query = User.filter(status='0', del_flag='0')  # 只获取活跃用户
            
            if self.warmup_active_users_only and self.warmup_recent_days > 0:
                # 只预热最近活跃的用户
                cutoff_date = datetime.now() - timedelta(days=self.warmup_recent_days)
                query = query.filter(login_date__gte=cutoff_date)
            
            users = await query.prefetch_related('roles').all()
            
            # 按优先级排序（优先角色的用户排在前面）
            priority_users = []
            normal_users = []
            
            for user in users:
                user_roles = [role.role_key for role in user.roles if role.role_key]
                is_priority = any(
                    priority_role in user_roles 
                    for priority_role in self.warmup_priority_roles
                )
                
                if is_priority:
                    priority_users.append(user)
                else:
                    normal_users.append(user)
            
            # 优先用户排在前面
            sorted_users = priority_users + normal_users
            
            logger.info(f"获取预热用户列表: 总数={len(sorted_users)}, 优先用户={len(priority_users)}")
            return sorted_users
            
        except Exception as e:
            logger.error(f"获取预热用户列表失败: {e}")
            return []
    
    async def _warmup_single_user_roles(self, user_id: int) -> bool:
        """预热单个用户的角色缓存"""
        try:
            # 检查是否已缓存
            cached_roles = await self.cache_manager.get_user_roles(user_id)
            if cached_roles is not None:
                return True  # 已缓存，无需预热
            
            # 从权限服务获取角色数据
            roles = await self.permission_service.get_user_roles(user_id)
            
            # 设置缓存
            return await self.cache_manager.set_user_roles(user_id, roles)
            
        except Exception as e:
            logger.error(f"预热用户角色缓存失败: user_id={user_id}, error={e}")
            return False
    
    async def _warmup_single_user_menus(self, user_id: int) -> bool:
        """预热单个用户的菜单缓存"""
        try:
            # 检查是否已缓存
            cached_menus = await self.cache_manager.get_user_menus(user_id)
            if cached_menus is not None:
                return True  # 已缓存，无需预热
            
            # 从权限服务获取菜单数据
            menus = await self.permission_service.get_user_menus(user_id)
            
            # 设置缓存
            return await self.cache_manager.set_user_menus(user_id, menus)
            
        except Exception as e:
            logger.error(f"预热用户菜单缓存失败: user_id={user_id}, error={e}")
            return False
    
    async def _warmup_single_role_permissions(self, role_id: int) -> bool:
        """预热单个角色的权限缓存"""
        try:
            # 检查是否已缓存
            cached_permissions = await self.cache_manager.get_role_permissions(role_id)
            if cached_permissions is not None:
                return True  # 已缓存，无需预热
            
            # 从数据库获取角色权限
            role = await Role.get_or_none(id=role_id).prefetch_related('apis')
            if not role:
                return False
            
            permissions = []
            role_apis = await role.apis.filter(status='active').all()
            for api in role_apis:
                permission = f"{api.http_method} {api.api_path}"
                permissions.append(permission)
            
            # 设置缓存
            return await self.cache_manager.set_role_permissions(role_id, permissions)
            
        except Exception as e:
            logger.error(f"预热角色权限缓存失败: role_id={role_id}, error={e}")
            return False
    
    async def warmup_specific_users(self, user_ids: List[int]) -> Dict[str, Any]:
        """预热指定用户的权限缓存"""
        logger.info(f"开始预热指定用户权限缓存: 用户数量={len(user_ids)}")
        
        results = {
            "user_ids": user_ids,
            "permissions": {"success": 0, "failed": 0},
            "roles": {"success": 0, "failed": 0},
            "menus": {"success": 0, "failed": 0}
        }
        
        try:
            # 预热用户权限
            perm_results = await self.cache_manager.preload_user_permissions(user_ids)
            results["permissions"]["success"] = sum(1 for success in perm_results.values() if success)
            results["permissions"]["failed"] = len(perm_results) - results["permissions"]["success"]
            
            # 预热用户角色
            for user_id in user_ids:
                success = await self._warmup_single_user_roles(user_id)
                if success:
                    results["roles"]["success"] += 1
                else:
                    results["roles"]["failed"] += 1
            
            # 预热用户菜单
            for user_id in user_ids:
                success = await self._warmup_single_user_menus(user_id)
                if success:
                    results["menus"]["success"] += 1
                else:
                    results["menus"]["failed"] += 1
            
            logger.info(f"指定用户权限缓存预热完成: {results}")
            
        except Exception as e:
            logger.error(f"预热指定用户权限缓存失败: {e}")
            results["error"] = str(e)
        
        return results
    
    async def warmup_priority_users(self) -> Dict[str, Any]:
        """预热优先用户的权限缓存"""
        logger.info("开始预热优先用户权限缓存...")
        
        try:
            # 获取优先角色的用户
            priority_users = []
            
            for role_key in self.warmup_priority_roles:
                role = await Role.get_or_none(role_key=role_key, status='0', del_flag='0')
                if role:
                    users = await role.users.filter(status='0', del_flag='0').all()
                    priority_users.extend(users)
            
            # 去重
            unique_users = list({user.id: user for user in priority_users}.values())
            user_ids = [user.id for user in unique_users]
            
            if not user_ids:
                logger.warning("没有找到优先用户")
                return {"message": "没有找到优先用户"}
            
            # 预热这些用户的权限
            results = await self.warmup_specific_users(user_ids)
            results["priority_roles"] = self.warmup_priority_roles
            
            logger.info(f"优先用户权限缓存预热完成: 用户数量={len(user_ids)}")
            return results
            
        except Exception as e:
            logger.error(f"预热优先用户权限缓存失败: {e}")
            return {"error": str(e)}
    
    async def get_warmup_status(self) -> Dict[str, Any]:
        """获取预热状态"""
        try:
            # 获取缓存统计信息
            cache_stats = await self.cache_manager.get_cache_statistics()
            
            # 获取用户和角色总数
            total_users = await User.filter(status='0', del_flag='0').count()
            total_roles = await Role.filter(status='0', del_flag='0').count()
            
            # 计算预热覆盖率
            cached_users = cache_stats.get("cache_keys", {}).get("by_type", {}).get("用户权限", 0)
            cached_roles = cache_stats.get("cache_keys", {}).get("by_type", {}).get("角色权限", 0)
            
            user_coverage = (cached_users / total_users * 100) if total_users > 0 else 0
            role_coverage = (cached_roles / total_roles * 100) if total_roles > 0 else 0
            
            return {
                "total_users": total_users,
                "total_roles": total_roles,
                "cached_users": cached_users,
                "cached_roles": cached_roles,
                "user_coverage_percent": round(user_coverage, 2),
                "role_coverage_percent": round(role_coverage, 2),
                "cache_stats": cache_stats,
                "warmup_config": {
                    "batch_size": self.warmup_batch_size,
                    "delay_seconds": self.warmup_delay,
                    "max_concurrent": self.max_concurrent_warmup,
                    "active_users_only": self.warmup_active_users_only,
                    "recent_days": self.warmup_recent_days,
                    "priority_roles": self.warmup_priority_roles
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取预热状态失败: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}


# 全局权限缓存预热服务实例
permission_cache_warmup_service = PermissionCacheWarmupService()


# 便捷函数
async def warmup_all_permissions() -> Dict[str, Any]:
    """预热所有权限缓存"""
    return await permission_cache_warmup_service.warmup_all_permissions()


async def warmup_priority_users() -> Dict[str, Any]:
    """预热优先用户权限缓存"""
    return await permission_cache_warmup_service.warmup_priority_users()


async def warmup_specific_users(user_ids: List[int]) -> Dict[str, Any]:
    """预热指定用户权限缓存"""
    return await permission_cache_warmup_service.warmup_specific_users(user_ids)


if __name__ == "__main__":
    # 测试权限缓存预热
    async def test_warmup():
        from app.core.permission_cache import init_permission_cache
        
        await init_permission_cache()
        
        print("测试权限缓存预热...")
        
        # 获取预热状态
        status = await permission_cache_warmup_service.get_warmup_status()
        print(f"预热状态: {status}")
        
        # 预热优先用户
        result = await permission_cache_warmup_service.warmup_priority_users()
        print(f"优先用户预热结果: {result}")
        
        print("权限缓存预热测试完成")
    
    asyncio.run(test_warmup())