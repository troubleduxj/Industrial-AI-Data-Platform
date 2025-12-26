# -*- coding: utf-8 -*-
"""
权限装饰器模块
提供自动触发权限变更事件的装饰器
"""
import functools
import logging
from typing import Any, Callable, List, Optional

from app.core.permission_events import permission_event_manager
from app.core.ctx import CTX_USER_ID

logger = logging.getLogger(__name__)


def permission_event_trigger(event_type: str = None):
    """
    权限事件触发装饰器
    自动在函数执行后触发相应的权限变更事件
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 执行原函数
            result = await func(*args, **kwargs)
            
            try:
                # 获取当前操作用户ID
                operator_id = None
                try:
                    operator_id = CTX_USER_ID.get()
                except Exception:
                    pass
                
                # 根据函数名和参数自动判断事件类型并触发
                await _auto_trigger_permission_event(
                    func.__name__, 
                    args, 
                    kwargs, 
                    result, 
                    operator_id,
                    event_type
                )
                
            except Exception as e:
                logger.error(f"触发权限事件失败: {e}")
                # 不影响主要业务逻辑
            
            return result
        return wrapper
    return decorator


async def _auto_trigger_permission_event(
    func_name: str, 
    args: tuple, 
    kwargs: dict, 
    result: Any, 
    operator_id: Optional[int],
    event_type: Optional[str] = None
):
    """
    自动触发权限事件
    根据函数名和参数自动判断需要触发的权限事件
    """
    try:
        # 用户角色相关操作
        if "assign_role" in func_name or "add_role" in func_name:
            user_id = _extract_user_id(args, kwargs)
            role_ids = _extract_role_ids(args, kwargs, result)
            if user_id and role_ids:
                await permission_event_manager.emit_user_role_assigned(
                    user_id, role_ids, operator_id
                )
        
        elif "remove_role" in func_name or "delete_role" in func_name:
            user_id = _extract_user_id(args, kwargs)
            role_ids = _extract_role_ids(args, kwargs, result)
            if user_id and role_ids:
                await permission_event_manager.emit_user_role_removed(
                    user_id, role_ids, operator_id
                )
        
        # 角色权限相关操作
        elif "assign_permission" in func_name or "add_api" in func_name:
            role_id = _extract_role_id(args, kwargs)
            api_ids = _extract_api_ids(args, kwargs, result)
            if role_id and api_ids:
                await permission_event_manager.emit_role_permission_assigned(
                    role_id, api_ids, operator_id
                )
        
        elif "remove_permission" in func_name or "remove_api" in func_name:
            role_id = _extract_role_id(args, kwargs)
            api_ids = _extract_api_ids(args, kwargs, result)
            if role_id and api_ids:
                await permission_event_manager.emit_role_permission_removed(
                    role_id, api_ids, operator_id
                )
        
        # 用户状态变更
        elif "update_user" in func_name or "modify_user" in func_name:
            user_id = _extract_user_id(args, kwargs)
            if user_id:
                # 这里可以进一步检查是否是状态变更
                await permission_event_manager.emit_user_status_changed(
                    user_id, True, True, operator_id  # 简化处理
                )
        
        # 角色状态变更
        elif "update_role" in func_name or "modify_role" in func_name:
            role_id = _extract_role_id(args, kwargs)
            if role_id:
                await permission_event_manager.emit_role_status_changed(
                    role_id, True, True, operator_id  # 简化处理
                )
        
        # API权限变更
        elif "update_api" in func_name or "refresh_api" in func_name:
            await permission_event_manager.emit_api_permission_changed(
                0, {"action": func_name}, operator_id
            )
            
    except Exception as e:
        logger.error(f"自动触发权限事件失败: {e}")


def _extract_user_id(args: tuple, kwargs: dict) -> Optional[int]:
    """从参数中提取用户ID"""
    # 检查kwargs中的user_id
    if 'user_id' in kwargs:
        return kwargs['user_id']
    
    # 检查args中的第一个参数是否为用户ID
    if args and isinstance(args[0], int):
        return args[0]
    
    # 检查是否有user对象
    for arg in args:
        if hasattr(arg, 'id') and hasattr(arg, 'username'):
            return arg.id
    
    return None


def _extract_role_id(args: tuple, kwargs: dict) -> Optional[int]:
    """从参数中提取角色ID"""
    # 检查kwargs中的role_id
    if 'role_id' in kwargs:
        return kwargs['role_id']
    
    # 检查是否有role对象
    for arg in args:
        if hasattr(arg, 'id') and hasattr(arg, 'name'):
            return arg.id
    
    return None


def _extract_role_ids(args: tuple, kwargs: dict, result: Any) -> Optional[List[int]]:
    """从参数或结果中提取角色ID列表"""
    # 检查kwargs中的role_ids
    if 'role_ids' in kwargs:
        return kwargs['role_ids']
    
    # 检查args中的角色ID列表
    for arg in args:
        if isinstance(arg, list) and all(isinstance(x, int) for x in arg):
            return arg
    
    # 从结果中提取
    if isinstance(result, list):
        return [item.id if hasattr(item, 'id') else item for item in result]
    
    return None


def _extract_api_ids(args: tuple, kwargs: dict, result: Any) -> Optional[List[int]]:
    """从参数或结果中提取API ID列表"""
    # 检查kwargs中的api_ids
    if 'api_ids' in kwargs:
        return kwargs['api_ids']
    
    # 检查args中的API ID列表
    for arg in args:
        if isinstance(arg, list) and all(isinstance(x, int) for x in arg):
            return arg
    
    # 从结果中提取
    if isinstance(result, list):
        return [item.id if hasattr(item, 'id') else item for item in result]
    
    return None


# 便捷装饰器
def user_role_change_event(func: Callable) -> Callable:
    """用户角色变更事件装饰器"""
    return permission_event_trigger("user_role_change")(func)


def role_permission_change_event(func: Callable) -> Callable:
    """角色权限变更事件装饰器"""
    return permission_event_trigger("role_permission_change")(func)


def user_status_change_event(func: Callable) -> Callable:
    """用户状态变更事件装饰器"""
    return permission_event_trigger("user_status_change")(func)


def api_permission_change_event(func: Callable) -> Callable:
    """API权限变更事件装饰器"""
    return permission_event_trigger("api_permission_change")(func)