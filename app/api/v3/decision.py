"""
决策引擎API v3
实现决策规则的CRUD操作、启用/禁用、审计日志查询

需求：1.4, 1.5, 1.6
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, Body
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.auth_dependencies import get_current_active_user
from app.core.unified_logger import get_logger
from app.schemas.base import Success, Fail, SuccessExtra
from app.models.admin import User

logger = get_logger(__name__)
router = APIRouter(prefix="/decision")


# =====================================================
# Pydantic模型定义
# =====================================================

class ConditionSchema(BaseModel):
    """条件配置模型"""
    field: str = Field(..., description="字段名")
    operator: str = Field(..., description="运算符: eq/ne/gt/gte/lt/lte/in/not_in/between/contains")
    value: Any = Field(..., description="比较值")


class ConditionGroupSchema(BaseModel):
    """条件组配置模型"""
    type: str = Field(..., description="逻辑运算符: AND/OR")
    rules: List[Any] = Field(..., description="条件列表（可嵌套）")


class ActionSchema(BaseModel):
    """动作配置模型"""
    type: str = Field(..., description="动作类型: alert/notification/webhook/workorder")
    level: Optional[str] = Field(None, description="告警级别（alert类型）")
    message: Optional[str] = Field(None, description="消息内容")
    channels: Optional[List[str]] = Field(None, description="通知渠道（notification类型）")
    recipients: Optional[List[str]] = Field(None, description="接收人")
    url: Optional[str] = Field(None, description="Webhook URL")


class RuleCreateSchema(BaseModel):
    """规则创建模型"""
    rule_id: str = Field(..., min_length=1, max_length=64, description="规则ID")
    name: str = Field(..., min_length=1, max_length=100, description="规则名称")
    description: Optional[str] = Field(None, max_length=500, description="规则描述")
    category_id: Optional[int] = Field(None, description="关联资产类别ID")
    model_id: Optional[int] = Field(None, description="关联AI模型ID")
    conditions: Dict[str, Any] = Field(..., description="条件配置")
    actions: List[Dict[str, Any]] = Field(..., description="动作配置列表")
    priority: int = Field(0, ge=0, description="优先级（数字越小优先级越高）")
    enabled: bool = Field(True, description="是否启用")
    cooldown_seconds: int = Field(0, ge=0, description="冷却时间（秒）")


class RuleUpdateSchema(BaseModel):
    """规则更新模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="规则名称")
    description: Optional[str] = Field(None, max_length=500, description="规则描述")
    category_id: Optional[int] = Field(None, description="关联资产类别ID")
    model_id: Optional[int] = Field(None, description="关联AI模型ID")
    conditions: Optional[Dict[str, Any]] = Field(None, description="条件配置")
    actions: Optional[List[Dict[str, Any]]] = Field(None, description="动作配置列表")
    priority: Optional[int] = Field(None, ge=0, description="优先级")
    enabled: Optional[bool] = Field(None, description="是否启用")
    cooldown_seconds: Optional[int] = Field(None, ge=0, description="冷却时间（秒）")


# =====================================================
# 辅助函数
# =====================================================

async def get_decision_rule_model():
    """延迟导入DecisionRule模型"""
    from app.models.platform_upgrade import DecisionRule
    return DecisionRule


async def get_audit_log_model():
    """延迟导入DecisionAuditLog模型"""
    from app.models.platform_upgrade import DecisionAuditLog
    return DecisionAuditLog


async def get_rule_parser():
    """延迟导入规则解析器"""
    from ai_engine.decision_engine import RuleParser
    return RuleParser


async def get_rule_runtime():
    """延迟导入规则运行时"""
    from ai_engine.decision_engine import rule_runtime
    return rule_runtime


async def rule_to_dict(rule) -> dict:
    """将规则转换为字典"""
    return {
        "id": rule.id,
        "rule_id": rule.rule_id,
        "name": rule.name,
        "description": rule.description,
        "category_id": rule.category_id,
        "model_id": rule.model_id,
        "conditions": rule.conditions,
        "actions": rule.actions,
        "priority": rule.priority,
        "enabled": rule.enabled,
        "cooldown_seconds": rule.cooldown_seconds,
        "created_by": rule.created_by,
        "updated_by": rule.updated_by,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None
    }


async def audit_log_to_dict(log) -> dict:
    """将审计日志转换为字典"""
    return {
        "id": log.id,
        "rule_id": log.rule_id,
        "rule_name": log.rule_name,
        "asset_id": log.asset_id,
        "prediction_id": log.prediction_id,
        "trigger_time": log.trigger_time.isoformat() if log.trigger_time else None,
        "trigger_data": log.trigger_data,
        "conditions_snapshot": log.conditions_snapshot,
        "actions_executed": log.actions_executed,
        "result": log.result,
        "error_message": log.error_message,
        "execution_duration_ms": log.execution_duration_ms,
        "created_at": log.created_at.isoformat() if log.created_at else None
    }


# =====================================================
# 规则CRUD API
# =====================================================

@router.post("/rules", summary="创建决策规则")
async def create_rule(
    rule_data: RuleCreateSchema,
    current_user: User = Depends(get_current_active_user)
):
    """
    创建新的决策规则
    
    - 验证规则DSL格式
    - 保存到数据库
    - 加载到运行时引擎
    
    需求：1.4
    """
    try:
        DecisionRule = await get_decision_rule_model()
        RuleParser = await get_rule_parser()
        
        # 1. 检查规则ID是否已存在
        existing = await DecisionRule.get_or_none(rule_id=rule_data.rule_id)
        if existing:
            return Fail(code=400, msg=f"规则ID已存在: {rule_data.rule_id}")
        
        # 2. 验证规则DSL格式
        rule_dict = {
            "rule_id": rule_data.rule_id,
            "name": rule_data.name,
            "description": rule_data.description,
            "conditions": rule_data.conditions,
            "actions": rule_data.actions,
            "priority": rule_data.priority,
            "enabled": rule_data.enabled,
            "cooldown_seconds": rule_data.cooldown_seconds,
            "category_id": rule_data.category_id,
            "model_id": rule_data.model_id
        }
        
        is_valid, errors = RuleParser.validate(rule_dict)
        if not is_valid:
            return Fail(code=400, msg=f"规则格式验证失败: {'; '.join(errors)}")
        
        # 3. 验证关联的资产类别和模型（如果指定）
        if rule_data.category_id:
            from app.models.platform_upgrade import AssetCategory
            category = await AssetCategory.get_or_none(id=rule_data.category_id)
            if not category:
                return Fail(code=404, msg=f"资产类别不存在: {rule_data.category_id}")
        
        if rule_data.model_id:
            from app.models.platform_upgrade import AIModel
            model = await AIModel.get_or_none(id=rule_data.model_id)
            if not model:
                return Fail(code=404, msg=f"AI模型不存在: {rule_data.model_id}")
        
        # 4. 创建规则
        rule = DecisionRule(
            rule_id=rule_data.rule_id,
            name=rule_data.name,
            description=rule_data.description,
            category_id=rule_data.category_id,
            model_id=rule_data.model_id,
            conditions=rule_data.conditions,
            actions=rule_data.actions,
            priority=rule_data.priority,
            enabled=rule_data.enabled,
            cooldown_seconds=rule_data.cooldown_seconds,
            created_by=current_user.id,
            updated_by=current_user.id
        )
        await rule.save()
        
        # 5. 如果规则启用，加载到运行时
        if rule.enabled:
            try:
                rule_runtime = await get_rule_runtime()
                parsed_rule = RuleParser.parse(rule_dict)
                rule_runtime.add_rule(parsed_rule)
            except Exception as e:
                logger.warning(f"加载规则到运行时失败: {e}")
        
        logger.info(f"创建决策规则: {rule.rule_id}, 用户={current_user.username}")
        
        return Success(
            code=200,
            msg="规则创建成功",
            data=await rule_to_dict(rule)
        )
        
    except Exception as e:
        logger.error(f"创建决策规则失败: {e}")
        return Fail(code=500, msg=f"创建失败: {str(e)}")


@router.get("/rules", summary="获取决策规则列表")
async def list_rules(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category_id: Optional[int] = Query(None, description="资产类别ID"),
    model_id: Optional[int] = Query(None, description="AI模型ID"),
    enabled: Optional[bool] = Query(None, description="是否启用"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取决策规则列表
    
    支持按类别、模型、启用状态筛选
    
    需求：1.4, 1.6
    """
    try:
        DecisionRule = await get_decision_rule_model()
        
        # 1. 构建查询条件
        query = DecisionRule.all()
        
        if category_id is not None:
            query = query.filter(category_id=category_id)
        if model_id is not None:
            query = query.filter(model_id=model_id)
        if enabled is not None:
            query = query.filter(enabled=enabled)
        if keyword:
            query = query.filter(name__icontains=keyword)
        
        # 2. 分页查询
        total = await query.count()
        offset = (page - 1) * page_size
        rules = await query.order_by("priority", "-created_at").offset(offset).limit(page_size)
        
        # 3. 转换为字典列表
        rule_list = [await rule_to_dict(r) for r in rules]
        
        return SuccessExtra(
            code=200,
            msg="获取成功",
            data=rule_list,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"获取决策规则列表失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")


@router.get("/rules/{rule_id}", summary="获取决策规则详情")
async def get_rule(
    rule_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    获取单个决策规则的详细信息
    
    需求：1.4
    """
    try:
        DecisionRule = await get_decision_rule_model()
        
        rule = await DecisionRule.get_or_none(rule_id=rule_id)
        if not rule:
            return Fail(code=404, msg=f"规则不存在: {rule_id}")
        
        result = await rule_to_dict(rule)
        
        # 获取关联信息
        if rule.category_id:
            from app.models.platform_upgrade import AssetCategory
            category = await AssetCategory.get_or_none(id=rule.category_id)
            if category:
                result["category"] = {"id": category.id, "name": category.name, "code": category.code}
        
        if rule.model_id:
            from app.models.platform_upgrade import AIModel
            model = await AIModel.get_or_none(id=rule.model_id)
            if model:
                result["model"] = {"id": model.id, "name": model.name, "code": model.code}
        
        # 获取运行时状态
        try:
            rule_runtime = await get_rule_runtime()
            runtime_rule = rule_runtime.get_rule(rule_id)
            cooldown_remaining = rule_runtime.get_cooldown_remaining(rule_id)
            result["runtime_status"] = {
                "loaded": runtime_rule is not None,
                "cooldown_remaining": cooldown_remaining
            }
        except Exception:
            result["runtime_status"] = {"loaded": False, "cooldown_remaining": None}
        
        return Success(
            code=200,
            msg="获取成功",
            data=result
        )
        
    except Exception as e:
        logger.error(f"获取决策规则详情失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")


@router.put("/rules/{rule_id}", summary="更新决策规则")
async def update_rule(
    rule_id: str,
    rule_data: RuleUpdateSchema,
    current_user: User = Depends(get_current_active_user)
):
    """
    更新决策规则
    
    - 验证规则DSL格式
    - 更新数据库
    - 重新加载到运行时引擎
    
    需求：1.4
    """
    try:
        DecisionRule = await get_decision_rule_model()
        RuleParser = await get_rule_parser()
        
        # 1. 获取现有规则
        rule = await DecisionRule.get_or_none(rule_id=rule_id)
        if not rule:
            return Fail(code=404, msg=f"规则不存在: {rule_id}")
        
        # 2. 更新字段
        update_data = rule_data.model_dump(exclude_unset=True)
        
        # 3. 如果更新了条件或动作，验证格式
        if "conditions" in update_data or "actions" in update_data:
            rule_dict = {
                "rule_id": rule.rule_id,
                "name": update_data.get("name", rule.name),
                "conditions": update_data.get("conditions", rule.conditions),
                "actions": update_data.get("actions", rule.actions),
                "priority": update_data.get("priority", rule.priority),
                "enabled": update_data.get("enabled", rule.enabled),
                "cooldown_seconds": update_data.get("cooldown_seconds", rule.cooldown_seconds)
            }
            
            is_valid, errors = RuleParser.validate(rule_dict)
            if not is_valid:
                return Fail(code=400, msg=f"规则格式验证失败: {'; '.join(errors)}")
        
        # 4. 验证关联的资产类别和模型（如果更新）
        if "category_id" in update_data and update_data["category_id"]:
            from app.models.platform_upgrade import AssetCategory
            category = await AssetCategory.get_or_none(id=update_data["category_id"])
            if not category:
                return Fail(code=404, msg=f"资产类别不存在: {update_data['category_id']}")
        
        if "model_id" in update_data and update_data["model_id"]:
            from app.models.platform_upgrade import AIModel
            model = await AIModel.get_or_none(id=update_data["model_id"])
            if not model:
                return Fail(code=404, msg=f"AI模型不存在: {update_data['model_id']}")
        
        # 5. 更新规则
        for key, value in update_data.items():
            setattr(rule, key, value)
        rule.updated_by = current_user.id
        await rule.save()
        
        # 6. 更新运行时
        try:
            rule_runtime = await get_rule_runtime()
            # 先移除旧规则
            rule_runtime.remove_rule(rule_id)
            # 如果启用，重新加载
            if rule.enabled:
                rule_dict = {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "description": rule.description,
                    "conditions": rule.conditions,
                    "actions": rule.actions,
                    "priority": rule.priority,
                    "enabled": rule.enabled,
                    "cooldown_seconds": rule.cooldown_seconds,
                    "category_id": rule.category_id,
                    "model_id": rule.model_id
                }
                parsed_rule = RuleParser.parse(rule_dict)
                rule_runtime.add_rule(parsed_rule)
        except Exception as e:
            logger.warning(f"更新运行时规则失败: {e}")
        
        logger.info(f"更新决策规则: {rule_id}, 用户={current_user.username}")
        
        return Success(
            code=200,
            msg="规则更新成功",
            data=await rule_to_dict(rule)
        )
        
    except Exception as e:
        logger.error(f"更新决策规则失败: {e}")
        return Fail(code=500, msg=f"更新失败: {str(e)}")


@router.delete("/rules/{rule_id}", summary="删除决策规则")
async def delete_rule(
    rule_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    删除决策规则
    
    需求：1.4
    """
    try:
        DecisionRule = await get_decision_rule_model()
        
        rule = await DecisionRule.get_or_none(rule_id=rule_id)
        if not rule:
            return Fail(code=404, msg=f"规则不存在: {rule_id}")
        
        # 从运行时移除
        try:
            rule_runtime = await get_rule_runtime()
            rule_runtime.remove_rule(rule_id)
        except Exception as e:
            logger.warning(f"从运行时移除规则失败: {e}")
        
        # 删除数据库记录
        await rule.delete()
        
        logger.info(f"删除决策规则: {rule_id}, 用户={current_user.username}")
        
        return Success(
            code=200,
            msg="规则删除成功",
            data={"rule_id": rule_id}
        )
        
    except Exception as e:
        logger.error(f"删除决策规则失败: {e}")
        return Fail(code=500, msg=f"删除失败: {str(e)}")


# =====================================================
# 规则启用/禁用API
# =====================================================

@router.post("/rules/{rule_id}/enable", summary="启用决策规则")
async def enable_rule(
    rule_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    启用决策规则
    
    需求：1.6
    """
    try:
        DecisionRule = await get_decision_rule_model()
        RuleParser = await get_rule_parser()
        
        rule = await DecisionRule.get_or_none(rule_id=rule_id)
        if not rule:
            return Fail(code=404, msg=f"规则不存在: {rule_id}")
        
        if rule.enabled:
            return Success(code=200, msg="规则已经是启用状态", data=await rule_to_dict(rule))
        
        # 更新数据库
        rule.enabled = True
        rule.updated_by = current_user.id
        await rule.save()
        
        # 加载到运行时
        try:
            rule_runtime = await get_rule_runtime()
            rule_dict = {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "description": rule.description,
                "conditions": rule.conditions,
                "actions": rule.actions,
                "priority": rule.priority,
                "enabled": rule.enabled,
                "cooldown_seconds": rule.cooldown_seconds,
                "category_id": rule.category_id,
                "model_id": rule.model_id
            }
            parsed_rule = RuleParser.parse(rule_dict)
            rule_runtime.add_rule(parsed_rule)
        except Exception as e:
            logger.warning(f"加载规则到运行时失败: {e}")
        
        logger.info(f"启用决策规则: {rule_id}, 用户={current_user.username}")
        
        return Success(
            code=200,
            msg="规则已启用",
            data=await rule_to_dict(rule)
        )
        
    except Exception as e:
        logger.error(f"启用决策规则失败: {e}")
        return Fail(code=500, msg=f"启用失败: {str(e)}")


@router.post("/rules/{rule_id}/disable", summary="禁用决策规则")
async def disable_rule(
    rule_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    禁用决策规则
    
    需求：1.6
    """
    try:
        DecisionRule = await get_decision_rule_model()
        
        rule = await DecisionRule.get_or_none(rule_id=rule_id)
        if not rule:
            return Fail(code=404, msg=f"规则不存在: {rule_id}")
        
        if not rule.enabled:
            return Success(code=200, msg="规则已经是禁用状态", data=await rule_to_dict(rule))
        
        # 更新数据库
        rule.enabled = False
        rule.updated_by = current_user.id
        await rule.save()
        
        # 从运行时移除
        try:
            rule_runtime = await get_rule_runtime()
            rule_runtime.remove_rule(rule_id)
        except Exception as e:
            logger.warning(f"从运行时移除规则失败: {e}")
        
        logger.info(f"禁用决策规则: {rule_id}, 用户={current_user.username}")
        
        return Success(
            code=200,
            msg="规则已禁用",
            data=await rule_to_dict(rule)
        )
        
    except Exception as e:
        logger.error(f"禁用决策规则失败: {e}")
        return Fail(code=500, msg=f"禁用失败: {str(e)}")


@router.post("/rules/{rule_id}/clear-cooldown", summary="清除规则冷却时间")
async def clear_rule_cooldown(
    rule_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    清除规则的冷却时间，使其可以立即触发
    
    需求：1.6
    """
    try:
        DecisionRule = await get_decision_rule_model()
        
        rule = await DecisionRule.get_or_none(rule_id=rule_id)
        if not rule:
            return Fail(code=404, msg=f"规则不存在: {rule_id}")
        
        # 清除运行时冷却
        try:
            rule_runtime = await get_rule_runtime()
            rule_runtime.clear_cooldown(rule_id)
        except Exception as e:
            logger.warning(f"清除冷却时间失败: {e}")
        
        logger.info(f"清除规则冷却时间: {rule_id}, 用户={current_user.username}")
        
        return Success(
            code=200,
            msg="冷却时间已清除",
            data={"rule_id": rule_id}
        )
        
    except Exception as e:
        logger.error(f"清除规则冷却时间失败: {e}")
        return Fail(code=500, msg=f"操作失败: {str(e)}")


# =====================================================
# 规则运行时状态API
# =====================================================

@router.get("/runtime/status", summary="获取运行时状态")
async def get_runtime_status(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取决策引擎运行时状态
    
    需求：1.6
    """
    try:
        rule_runtime = await get_rule_runtime()
        
        rules = rule_runtime.rules
        rule_status = []
        
        for rule_id, rule in rules.items():
            cooldown_remaining = rule_runtime.get_cooldown_remaining(rule_id)
            rule_status.append({
                "rule_id": rule_id,
                "name": rule.name,
                "enabled": rule.enabled,
                "priority": rule.priority,
                "in_cooldown": cooldown_remaining is not None,
                "cooldown_remaining": cooldown_remaining
            })
        
        return Success(
            code=200,
            msg="获取成功",
            data={
                "total_rules": len(rules),
                "enabled_rules": sum(1 for r in rules.values() if r.enabled),
                "rules": rule_status
            }
        )
        
    except Exception as e:
        logger.error(f"获取运行时状态失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")


@router.post("/runtime/reload", summary="重新加载所有规则")
async def reload_rules(
    current_user: User = Depends(get_current_active_user)
):
    """
    从数据库重新加载所有规则到运行时
    
    需求：1.6
    """
    try:
        rule_runtime = await get_rule_runtime()
        
        # 清除现有规则
        rule_runtime._rules.clear()
        rule_runtime.clear_all_cooldowns()
        
        # 重新加载
        loaded_count = await rule_runtime.load_rules_from_db()
        
        logger.info(f"重新加载规则: {loaded_count}条, 用户={current_user.username}")
        
        return Success(
            code=200,
            msg=f"已重新加载 {loaded_count} 条规则",
            data={"loaded_count": loaded_count}
        )
        
    except Exception as e:
        logger.error(f"重新加载规则失败: {e}")
        return Fail(code=500, msg=f"重新加载失败: {str(e)}")



# =====================================================
# 审计日志API
# =====================================================

@router.get("/audit-logs", summary="获取审计日志列表")
async def list_audit_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    rule_id: Optional[str] = Query(None, description="规则ID"),
    asset_id: Optional[int] = Query(None, description="资产ID"),
    result: Optional[str] = Query(None, description="执行结果: success/partial/failed"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取决策审计日志列表
    
    支持按规则、资产、结果、时间范围筛选
    
    需求：1.5
    """
    try:
        DecisionAuditLog = await get_audit_log_model()
        
        # 1. 构建查询条件
        query = DecisionAuditLog.all()
        
        if rule_id:
            query = query.filter(rule_id=rule_id)
        if asset_id:
            query = query.filter(asset_id=asset_id)
        if result:
            query = query.filter(result=result)
        if start_time:
            query = query.filter(trigger_time__gte=start_time)
        if end_time:
            query = query.filter(trigger_time__lte=end_time)
        
        # 2. 分页查询
        total = await query.count()
        offset = (page - 1) * page_size
        logs = await query.order_by("-trigger_time").offset(offset).limit(page_size)
        
        # 3. 转换为字典列表
        log_list = [await audit_log_to_dict(log) for log in logs]
        
        return SuccessExtra(
            code=200,
            msg="获取成功",
            data=log_list,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"获取审计日志列表失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")


@router.get("/audit-logs/statistics", summary="获取审计日志统计")
async def get_audit_statistics(
    rule_id: Optional[str] = Query(None, description="规则ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取审计日志统计信息
    
    需求：1.5
    """
    try:
        from ai_engine.decision_engine import audit_logger
        
        stats = await audit_logger.get_statistics(
            rule_id=rule_id,
            start_time=start_time,
            end_time=end_time
        )
        
        return Success(
            code=200,
            msg="获取成功",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"获取审计日志统计失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")


@router.get("/audit-logs/rules/{rule_id}", summary="获取规则的审计日志")
async def get_rule_audit_logs(
    rule_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取指定规则的审计日志
    
    需求：1.5
    """
    try:
        DecisionAuditLog = await get_audit_log_model()
        DecisionRule = await get_decision_rule_model()
        
        # 验证规则存在
        rule = await DecisionRule.get_or_none(rule_id=rule_id)
        if not rule:
            return Fail(code=404, msg=f"规则不存在: {rule_id}")
        
        # 构建查询
        query = DecisionAuditLog.filter(rule_id=rule_id)
        
        if start_time:
            query = query.filter(trigger_time__gte=start_time)
        if end_time:
            query = query.filter(trigger_time__lte=end_time)
        
        # 分页查询
        total = await query.count()
        offset = (page - 1) * page_size
        logs = await query.order_by("-trigger_time").offset(offset).limit(page_size)
        
        # 转换为字典列表
        log_list = [await audit_log_to_dict(log) for log in logs]
        
        return SuccessExtra(
            code=200,
            msg="获取成功",
            data=log_list,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"获取规则审计日志失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")


@router.get("/audit-logs/{log_id}", summary="获取审计日志详情")
async def get_audit_log_detail(
    log_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    获取单个审计日志的详细信息
    
    需求：1.5
    """
    try:
        DecisionAuditLog = await get_audit_log_model()
        
        log = await DecisionAuditLog.get_or_none(id=log_id)
        if not log:
            return Fail(code=404, msg=f"审计日志不存在: {log_id}")
        
        result = await audit_log_to_dict(log)
        
        # 获取关联的规则信息
        DecisionRule = await get_decision_rule_model()
        rule = await DecisionRule.get_or_none(rule_id=log.rule_id)
        if rule:
            result["rule"] = {
                "id": rule.id,
                "rule_id": rule.rule_id,
                "name": rule.name,
                "enabled": rule.enabled
            }
        
        # 获取关联的资产信息
        if log.asset_id:
            from app.models.platform_upgrade import Asset
            asset = await Asset.get_or_none(id=log.asset_id)
            if asset:
                result["asset"] = {
                    "id": asset.id,
                    "code": asset.code,
                    "name": asset.name
                }
        
        return Success(
            code=200,
            msg="获取成功",
            data=result
        )
        
    except Exception as e:
        logger.error(f"获取审计日志详情失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")


# =====================================================
# 规则测试API
# =====================================================

@router.post("/rules/{rule_id}/test", summary="测试决策规则")
async def test_rule(
    rule_id: str,
    test_data: Dict[str, Any] = Body(..., description="测试数据"),
    current_user: User = Depends(get_current_active_user)
):
    """
    使用测试数据测试决策规则
    
    不会触发实际动作，仅返回评估结果
    
    需求：1.4
    """
    try:
        DecisionRule = await get_decision_rule_model()
        RuleParser = await get_rule_parser()
        from ai_engine.decision_engine import RuleRuntime
        
        # 获取规则
        rule = await DecisionRule.get_or_none(rule_id=rule_id)
        if not rule:
            return Fail(code=404, msg=f"规则不存在: {rule_id}")
        
        # 解析规则
        rule_dict = {
            "rule_id": rule.rule_id,
            "name": rule.name,
            "description": rule.description,
            "conditions": rule.conditions,
            "actions": rule.actions,
            "priority": rule.priority,
            "enabled": True,  # 测试时强制启用
            "cooldown_seconds": 0,  # 测试时忽略冷却
            "category_id": rule.category_id,
            "model_id": rule.model_id
        }
        
        parsed_rule = RuleParser.parse(rule_dict)
        
        # 创建临时运行时进行测试
        test_runtime = RuleRuntime()
        test_runtime.add_rule(parsed_rule)
        
        # 评估
        triggered_actions = test_runtime.evaluate_sync(test_data)
        
        return Success(
            code=200,
            msg="测试完成",
            data={
                "rule_id": rule_id,
                "test_data": test_data,
                "triggered": len(triggered_actions) > 0,
                "actions_count": len(triggered_actions),
                "actions": [
                    {
                        "type": a["action"].type,
                        "config": a["action"].config
                    }
                    for a in triggered_actions
                ]
            }
        )
        
    except Exception as e:
        logger.error(f"测试决策规则失败: {e}")
        return Fail(code=500, msg=f"测试失败: {str(e)}")


@router.post("/rules/validate", summary="验证规则DSL")
async def validate_rule_dsl(
    rule_data: Dict[str, Any] = Body(..., description="规则DSL"),
    current_user: User = Depends(get_current_active_user)
):
    """
    验证规则DSL格式是否正确
    
    需求：1.4
    """
    try:
        RuleParser = await get_rule_parser()
        
        is_valid, errors = RuleParser.validate(rule_data)
        
        return Success(
            code=200,
            msg="验证完成",
            data={
                "valid": is_valid,
                "errors": errors if not is_valid else []
            }
        )
        
    except Exception as e:
        logger.error(f"验证规则DSL失败: {e}")
        return Fail(code=500, msg=f"验证失败: {str(e)}")
