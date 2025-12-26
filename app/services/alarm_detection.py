#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报警检测引擎服务
负责检测设备数据是否触发报警规则
"""

import asyncio
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from decimal import Decimal
from tortoise.expressions import F
from tortoise.functions import Avg, Max, Min, Sum, Count

from app.models.alarm import AlarmRule, AlarmRecord
from app.models.device import DeviceField, DeviceMaintenanceRecord, DeviceHistoryData
from app.log import logger


class AlarmDetectionEngine:
    """报警检测引擎"""
    
    def __init__(self):
        self._rules_cache: Dict[str, List[AlarmRule]] = {}  # {device_type_code: [rules]}
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = 300  # 缓存5分钟
        self._trigger_counts: Dict[str, Dict[str, int]] = {}  # {device_code: {rule_code: count}}
        self._last_alarm_time: Dict[str, Dict[str, datetime]] = {}  # 静默期控制
        # Phase 3: ROC检测缓存 {device_code: {field_code: {"value": val, "time": dt}}}
        self._last_values: Dict[str, Dict[str, Dict[str, Any]]] = {} 
        
        # Phase 4: 报警自动恢复状态
        self._active_alarms: Dict[str, Dict[str, int]] = {}  # {device_code: {rule_code: alarm_id}}
        self._recovery_counts: Dict[str, Dict[str, int]] = {}  # {device_code: {rule_code: consecutive_normal_count}}
        
        # Phase 3: 维护模式缓存 {device_code: True}
        self._maintenance_cache: Dict[str, bool] = {}
        self._maintenance_cache_time: Optional[datetime] = None
    
    async def load_rules(self, force: bool = False) -> None:
        """加载报警规则到缓存"""
        now = datetime.now()
        
        # 检查缓存是否有效
        if not force and self._cache_time:
            elapsed = (now - self._cache_time).total_seconds()
            if elapsed < self._cache_ttl:
                return
        
        try:
            # 1. 获取允许报警的字段
            enabled_fields = await DeviceField.filter(is_alarm_enabled=True).values("device_type_code", "field_code")
            # 构建快速查找集合 {(device_type_code, field_code)}
            valid_field_set = {(f["device_type_code"], f["field_code"]) for f in enabled_fields}
            
            rules = await AlarmRule.filter(is_enabled=True).all()
            
            # 按设备类型分组
            self._rules_cache = {}
            for rule in rules:
                # 检查字段是否允许报警
                if (rule.device_type_code, rule.field_code) not in valid_field_set:
                    continue
                    
                type_code = rule.device_type_code
                if type_code not in self._rules_cache:
                    self._rules_cache[type_code] = []
                self._rules_cache[type_code].append(rule)
            
            # 加载当前活跃的报警
            await self._load_active_alarms_from_db()
            
            # 加载维护状态
            await self._load_maintenance_status()
            
            self._cache_time = now
            logger.info(f"报警规则缓存已更新，共 {len(rules)} 条规则 (已过滤未启用报警字段)")
            
        except Exception as e:
            logger.error(f"加载报警规则失败: {str(e)}")
            
    async def _load_maintenance_status(self) -> None:
        """加载设备维护状态"""
        try:
            # 查询所有处于"进行中"的维护记录
            records = await DeviceMaintenanceRecord.filter(
                maintenance_status="in_progress"
            ).select_related("device").all()
            
            self._maintenance_cache = {}
            for record in records:
                if record.device:
                    self._maintenance_cache[record.device.device_code] = True
            
            self._maintenance_cache_time = datetime.now()
            logger.info(f"维护状态缓存已更新，共 {len(self._maintenance_cache)} 个设备处于维护中")
        except Exception as e:
            logger.error(f"加载维护状态失败: {str(e)}")
    
    async def check_device_data(
        self, 
        device_code: str,
        device_name: Optional[str],
        device_type_code: str,
        data: Dict[str, Any]
    ) -> List[Dict]:
        """
        检测设备数据是否触发报警
        
        Args:
            device_code: 设备编码
            device_name: 设备名称
            device_type_code: 设备类型代码
            data: 设备数据字典 {field_code: value}
            
        Returns:
            触发的报警列表
        """
        await self.load_rules()
        
        rules = self._rules_cache.get(device_type_code, [])
        if not rules:
            return []
        
        # 1. 筛选当前设备生效的规则 (Phase 2: 规则覆盖)
        effective_rules_map = {} # {field_code: rule}
        
        for rule in rules:
            # Check if rule applies to this device
            if rule.device_code and rule.device_code != device_code:
                continue
            
            # Override logic: Specific rule overrides general rule
            existing = effective_rules_map.get(rule.field_code)
            if existing:
                if rule.device_code == device_code: # This is specific
                    effective_rules_map[rule.field_code] = rule
            else:
                effective_rules_map[rule.field_code] = rule
        
        triggered_alarms = []
        
        for rule in effective_rules_map.values():
            # 0. 检查高级生效条件 (Phase 3: 状态/时间过滤/维护模式)
            if not self._check_effective_condition(rule, data, device_code):
                continue

            field_code = rule.field_code
            # ...
            rule_code = rule.rule_code
            
            # 检查数据中是否有该字段
            if field_code not in data:
                continue
            
            value = data[field_code]
            if value is None:
                continue
            
            # 转换为数值
            try:
                if isinstance(value, (int, float, Decimal)):
                    numeric_value = float(value)
                else:
                    numeric_value = float(str(value))
            except (ValueError, TypeError):
                continue
            
            # Phase 3: 检查是否为变化率(ROC)检测 或 统计报警
            check_value = numeric_value
            threshold_config = rule.threshold_config or {}
            statistics_config = threshold_config.get("statistics")
            
            if statistics_config and statistics_config.get("enabled"):
                # 统计报警
                stat_value = await self._get_statistical_value(device_code, field_code, statistics_config)
                if stat_value is None:
                    continue
                check_value = stat_value
                
            elif threshold_config.get("type") == "change_rate":
                # 计算变化率 (单位: /分钟)
                roc_value = self._calculate_roc(device_code, field_code, numeric_value, data)
                if roc_value is None:
                    # 第一次数据，无法计算ROC，跳过并记录
                    self._update_last_value(device_code, field_code, numeric_value, data)
                    continue
                check_value = roc_value
            
            # 检测阈值
            result = self._check_threshold(threshold_config, check_value)
            
            # 无论是否触发，对于ROC都需要更新上一次的值(但要在计算后)
            if threshold_config.get("type") == "change_rate":
                self._update_last_value(device_code, field_code, numeric_value, data)

            # 检查该规则是否有活跃报警
            is_active = False
            active_alarm_id = None
            if device_code in self._active_alarms and rule_code in self._active_alarms[device_code]:
                is_active = True
                active_alarm_id = self._active_alarms[device_code][rule_code]

            if result["triggered"]:
                # 重置恢复计数
                if device_code in self._recovery_counts and rule_code in self._recovery_counts[device_code]:
                    self._recovery_counts[device_code][rule_code] = 0
                
                # 如果已经是活跃状态，则不需要重复创建报警
                if is_active:
                    # 报警合并: 更新活跃报警的状态
                    await self._merge_active_alarm(active_alarm_id, check_value)
                    continue

                # 检查触发条件（连续次数）
                if self._check_trigger_condition(device_code, rule, result["triggered"]):
                    # 检查静默期
                    if self._check_silent_period(device_code, rule):
                        # 创建报警记录
                        alarm = await self._create_alarm_record(
                            rule=rule,
                            device_code=device_code,
                            device_name=device_name,
                            device_type_code=device_type_code,
                            field_code=field_code,
                            trigger_value=check_value,
                            level=result["level"],
                            message=result["message"]
                        )
                        if alarm:
                            triggered_alarms.append(alarm)
                            # 记录活跃状态
                            if device_code not in self._active_alarms:
                                self._active_alarms[device_code] = {}
                            self._active_alarms[device_code][rule_code] = alarm["id"]
            else:
                # 重置触发计数
                self._reset_trigger_count(device_code, rule.rule_code)
                
                # Phase 4: 自动恢复逻辑
                if is_active:
                    # 获取恢复配置
                    trigger_config = rule.trigger_config or {}
                    auto_recover = trigger_config.get("auto_recover", True)
                    
                    if auto_recover:
                        recovery_threshold = trigger_config.get("auto_recovery_count", 3)
                        
                        if device_code not in self._recovery_counts:
                            self._recovery_counts[device_code] = {}
                        
                        current_recovery = self._recovery_counts[device_code].get(rule_code, 0) + 1
                        self._recovery_counts[device_code][rule_code] = current_recovery
                        
                        if current_recovery >= recovery_threshold:
                            # 触发恢复
                            await self._resolve_alarm(active_alarm_id, device_code, rule_code)
        
        return triggered_alarms
    
    def _check_effective_condition(self, rule: AlarmRule, data: Dict[str, Any], device_code: str = None) -> bool:
        """
        检查规则是否满足生效条件 (Phase 3)
        支持：状态白名单、时间段、周末排除、维护模式抑制
        """
        # 0. 维护模式抑制
        # 如果设备处于维护模式，且规则未显式允许维护期间报警（默认不允许），则抑制
        if device_code and self._maintenance_cache.get(device_code):
            # TODO: 可以在规则中配置 allow_maintenance_alarm，目前默认全部抑制
            return False

        # 兼容 trigger_config 或 effective_condition (如果模型中有的话)
        # 目前模型中使用 trigger_config 存储高级配置
        config = rule.trigger_config
        if not config:
            return True
            
        now = datetime.now()
        
        # 1. 状态白名单检查 (status_whitelist)
        # 仅在设备处于指定状态时生效
        status_whitelist = config.get("status_whitelist")
        if status_whitelist and isinstance(status_whitelist, list):
            # 尝试从数据中获取设备状态，常见字段名：device_status, status, state
            current_status = data.get("device_status") or data.get("status") or data.get("state")
            if current_status:
                # 统一转大写比较
                current_status = str(current_status).upper()
                whitelist = [str(s).upper() for s in status_whitelist]
                if current_status not in whitelist:
                    return False
        
        # 2. 周末排除 (exclude_weekend)
        if config.get("exclude_weekend") is True:
            # weekday(): 0=Mon, 6=Sun
            if now.weekday() >= 5:
                return False
                
        # 3. 时间段检查 (time_ranges)
        # 格式: [{"start": "08:00", "end": "20:00"}]
        time_ranges = config.get("time_ranges")
        if time_ranges and isinstance(time_ranges, list):
            current_time_str = now.strftime("%H:%M")
            in_range = False
            for tr in time_ranges:
                start = tr.get("start")
                end = tr.get("end")
                if start and end:
                    if start <= current_time_str <= end:
                        in_range = True
                        break
            # 如果定义了时间段，必须在至少一个时间段内
            if not in_range:
                return False
                
        return True

    async def _get_statistical_value(
        self, 
        device_code: str, 
        field_code: str, 
        config: Dict[str, Any]
    ) -> Optional[float]:
        """
        获取统计值
        Config: {
            "window": "5m", // 5 minutes
            "function": "avg" // avg, max, min, sum, count
        }
        """
        try:
            window_str = config.get("window", "5m")
            func_type = config.get("function", "avg")
            
            # 解析时间窗口
            window_minutes = 5
            if window_str.endswith("m"):
                window_minutes = int(window_str[:-1])
            elif window_str.endswith("h"):
                window_minutes = int(window_str[:-1]) * 60
            
            start_time = datetime.now() - timedelta(minutes=window_minutes)
            
            # 查询历史数据
            # 注意：这里假设DeviceHistoryData有对应的字段
            # 如果field_code是动态的，可能需要使用RawSQL或者更复杂的查询
            # 简单起见，我们假设field_code对应模型的一个属性
            
            # 首先找到设备ID
            # 优化：应该缓存 device_code -> device_id 的映射
            from app.models.device import DeviceInfo
            device = await DeviceInfo.get_or_none(device_code=device_code)
            if not device:
                return None
                
            # 构建查询
            query = DeviceHistoryData.filter(
                device_id=device.id,
                data_timestamp__gte=start_time
            )
            
            if func_type == "avg":
                result = await query.annotate(val=Avg(field_code)).first()
            elif func_type == "max":
                result = await query.annotate(val=Max(field_code)).first()
            elif func_type == "min":
                result = await query.annotate(val=Min(field_code)).first()
            elif func_type == "sum":
                result = await query.annotate(val=Sum(field_code)).first()
            elif func_type == "count":
                # Count is a bit different, it returns int
                count = await query.count()
                return float(count)
            else:
                return None
                
            if result and result.val is not None:
                return float(result.val)
                
            return None
            
        except Exception as e:
            logger.warning(f"获取统计值失败 {device_code} {field_code}: {str(e)}")
            return None

    def _calculate_roc(self, device_code: str, field_code: str, current_value: float, data: Dict[str, Any]) -> Optional[float]:
        """
        计算变化率 (Rate of Change)
        返回单位: 值变化量/分钟
        """
        if device_code not in self._last_values:
            return None
            
        last_data = self._last_values[device_code].get(field_code)
        if not last_data:
            return None
            
        last_value = last_data["value"]
        last_time = last_data["time"]
        
        # 获取当前时间
        current_time = self._get_data_time(data)
        
        # 计算时间差 (秒)
        time_diff = (current_time - last_time).total_seconds()
        
        # 如果时间差太小（例如小于1秒），或者是负数（乱序），则不计算
        if time_diff < 1.0:
            return None
            
        # 计算变化率
        delta_value = current_value - last_value
        # 转换为每分钟变化率: delta / (seconds / 60) = delta * 60 / seconds
        roc_per_minute = (delta_value * 60.0) / time_diff
        
        return roc_per_minute

    def _update_last_value(self, device_code: str, field_code: str, value: float, data: Dict[str, Any]) -> None:
        """更新上一次的值缓存"""
        if device_code not in self._last_values:
            self._last_values[device_code] = {}
            
        self._last_values[device_code][field_code] = {
            "value": value,
            "time": self._get_data_time(data)
        }
        
    def _get_data_time(self, data: Dict[str, Any]) -> datetime:
        """从数据中获取时间，如果没有则使用当前时间"""
        # 尝试常见的时间字段
        ts = data.get("timestamp") or data.get("ts") or data.get("time")
        
        if ts:
            if isinstance(ts, datetime):
                return ts
            elif isinstance(ts, (int, float)):
                # 假设是毫秒或秒
                try:
                    # 简单的判断：如果是13位是毫秒，10位是秒
                    if ts > 1e11: 
                        return datetime.fromtimestamp(ts / 1000.0)
                    else:
                        return datetime.fromtimestamp(ts)
                except:
                    pass
            elif isinstance(ts, str):
                try:
                    return datetime.fromisoformat(ts)
                except:
                    pass
                    
        return datetime.now()
 
    def _check_threshold(self, config: Dict, value: float) -> Dict:
        """检测阈值"""
        threshold_type = config.get("type", "range")
        
        # 按严重程度从高到低检查
        for level in ["emergency", "critical", "warning"]:
            if level not in config:
                continue
            
            threshold = config[level]
            triggered = False
            message = ""
            
            if threshold_type == "range":
                min_val = threshold.get("min")
                max_val = threshold.get("max")
                if min_val is not None and value < min_val:
                    triggered = True
                    message = f"低于下限 {min_val}，当前值 {value}"
                elif max_val is not None and value > max_val:
                    triggered = True
                    message = f"超过上限 {max_val}，当前值 {value}"
                    
            elif threshold_type == "upper":
                max_val = threshold.get("max")
                if max_val is not None and value > max_val:
                    triggered = True
                    message = f"超过上限 {max_val}，当前值 {value}"
                    
            elif threshold_type == "lower":
                min_val = threshold.get("min")
                if min_val is not None and value < min_val:
                    triggered = True
                    message = f"低于下限 {min_val}，当前值 {value}"
            
            elif threshold_type == "change_rate":
                # 变化率检测
                # 变化率可以是正(上升)或负(下降)
                # 规则配置通常为绝对值或范围
                # 示例: warning: {min: -10, max: 10} 表示允许的变化率范围是 -10 到 10
                # 如果超出这个范围（例如 -15 或 15），则触发报警
                
                min_val = threshold.get("min")
                max_val = threshold.get("max")
                
                # 如果设置了max，表示正向变化率不能超过此值 (上升过快)
                if max_val is not None and value > max_val:
                    triggered = True
                    message = f"上升速率过快 {value:.2f}/min (上限 {max_val})"
                
                # 如果设置了min，表示负向变化率不能低于此值 (下降过快)
                # 注意：min通常是负数，例如 -10
                elif min_val is not None and value < min_val:
                    triggered = True
                    message = f"下降速率过快 {value:.2f}/min (下限 {min_val})"
            
            if triggered:
                return {"triggered": True, "level": level, "message": message}
        
        return {"triggered": False, "level": None, "message": "正常"}
    
    def _check_trigger_condition(self, device_code: str, rule: AlarmRule, triggered: bool) -> bool:
        """检查触发条件（连续次数）"""
        rule_code = rule.rule_code
        condition = rule.trigger_condition or {}
        consecutive_count = condition.get("consecutive_count", 1)
        
        if device_code not in self._trigger_counts:
            self._trigger_counts[device_code] = {}
        
        if triggered:
            current_count = self._trigger_counts[device_code].get(rule_code, 0) + 1
            self._trigger_counts[device_code][rule_code] = current_count
            
            if current_count >= consecutive_count:
                return True
        else:
            self._trigger_counts[device_code][rule_code] = 0
        
        return False
    
    def _reset_trigger_count(self, device_code: str, rule_code: str) -> None:
        """重置触发计数"""
        if device_code in self._trigger_counts:
            self._trigger_counts[device_code][rule_code] = 0
    
    def _check_silent_period(self, device_code: str, rule: AlarmRule) -> bool:
        """检查静默期（避免重复报警）"""
        rule_code = rule.rule_code
        notification_config = rule.notification_config or {}
        silent_period = notification_config.get("silent_period", 300)  # 默认5分钟
        
        if device_code not in self._last_alarm_time:
            self._last_alarm_time[device_code] = {}
        
        last_time = self._last_alarm_time[device_code].get(rule_code)
        now = datetime.now()
        
        if last_time:
            elapsed = (now - last_time).total_seconds()
            if elapsed < silent_period:
                return False
        
        # 更新最后报警时间
        self._last_alarm_time[device_code][rule_code] = now
        return True
    
    async def _create_alarm_record(
        self,
        rule: AlarmRule,
        device_code: str,
        device_name: Optional[str],
        device_type_code: str,
        field_code: str,
        trigger_value: float,
        level: str,
        message: str
    ) -> Optional[Dict]:
        """创建报警记录"""
        try:
            # 生成报警代码
            alarm_code = f"{rule.rule_code}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            record = await AlarmRecord.create(
                rule_id=rule.id,
                device_code=device_code,
                device_name=device_name,
                device_type_code=device_type_code,
                alarm_code=alarm_code,
                alarm_level=level,
                alarm_title=f"{rule.rule_name} - {device_code}",
                alarm_content=message,
                field_code=field_code,
                field_name=rule.field_name,
                trigger_value=Decimal(str(trigger_value)),
                threshold_value=rule.threshold_config,
                triggered_at=datetime.now(),
                last_triggered_at=datetime.now(),
                trigger_count=1,
                status="active",
            )
            
            logger.warning(f"报警触发: {rule.rule_name}, 设备: {device_code}, 级别: {level}, {message}")
            
            alarm_data = {
                "id": record.id,
                "rule_id": rule.id,
                "rule_name": rule.rule_name,
                "device_code": device_code,
                "device_name": device_name,
                "alarm_level": level,
                "alarm_title": record.alarm_title,
                "alarm_content": message,
                "field_code": field_code,
                "field_name": rule.field_name,
                "trigger_value": trigger_value,
                "triggered_at": record.triggered_at.isoformat(),
            }
            
            # 创建报警通知
            try:
                from app.services.notification_service import create_alarm_notification
                await create_alarm_notification(alarm_data)
            except Exception as notify_error:
                logger.error(f"创建报警通知失败: {str(notify_error)}")
            
            return alarm_data
            
        except Exception as e:
            logger.error(f"创建报警记录失败: {str(e)}")
            return None
            
    async def _merge_active_alarm(self, alarm_id: int, current_value: float) -> None:
        """
        合并活跃报警：更新最后触发时间和计数
        Phase 4: 报警合并特性
        """
        try:
            # 使用 update 避免加载整个对象，提高性能
            await AlarmRecord.filter(id=alarm_id).update(
                last_triggered_at=datetime.now(),
                trigger_value=Decimal(str(current_value)),
                trigger_count=F("trigger_count") + 1
            )
        except Exception as e:
            logger.error(f"合并报警失败: {str(e)}")

    async def _load_active_alarms_from_db(self) -> None:
        """从数据库加载当前活跃的报警"""
        try:
            # 获取所有状态为active的报警
            active_records = await AlarmRecord.filter(status="active").prefetch_related("rule").all()
            
            self._active_alarms = {}
            count = 0
            
            for record in active_records:
                if not record.device_code or not record.rule:
                    continue
                    
                device_code = record.device_code
                rule_code = record.rule.rule_code
                
                if device_code not in self._active_alarms:
                    self._active_alarms[device_code] = {}
                    
                self._active_alarms[device_code][rule_code] = record.id
                count += 1
                
            if count > 0:
                logger.info(f"已加载 {count} 条活跃报警记录")
                
        except Exception as e:
            logger.error(f"加载活跃报警失败: {str(e)}")

    async def _resolve_alarm(self, alarm_id: int, device_code: str, rule_code: str) -> None:
        """
        自动解决报警
        """
        try:
            record = await AlarmRecord.get_or_none(id=alarm_id)
            if record and record.status == "active":
                now = datetime.now()
                duration = (now - record.triggered_at).total_seconds()
                
                record.status = "resolved"
                record.resolved_at = now
                record.duration_seconds = int(duration) if duration > 0 else 0
                record.resolution_notes = "系统自动恢复 (Auto-resolved)"
                await record.save()
                
                logger.info(f"报警自动恢复: ID={alarm_id}, 设备={device_code}, 规则={rule_code}")
                
            # 清理缓存
            if device_code in self._active_alarms:
                self._active_alarms[device_code].pop(rule_code, None)
                if not self._active_alarms[device_code]:
                    del self._active_alarms[device_code]
                    
            if device_code in self._recovery_counts:
                self._recovery_counts[device_code].pop(rule_code, None)
                
        except Exception as e:
            logger.error(f"自动解决报警失败: {str(e)}")

    async def check_timeout_alarms(self) -> None:
        """检查超时未处理的报警并自动升级"""
        try:
            # 获取所有活跃报警
            active_records = await AlarmRecord.filter(status="active").prefetch_related("rule").all()
            
            now = datetime.now()
            count = 0
            
            for record in active_records:
                if not record.rule:
                    continue
                    
                # 检查升级配置
                notification_config = record.rule.notification_config or {}
                escalation_config = notification_config.get("escalation_config")
                
                if not escalation_config or not escalation_config.get("enabled"):
                    continue
                    
                timeout_minutes = escalation_config.get("timeout_minutes", 30)
                target_level = escalation_config.get("target_level", "critical")
                
                # 检查是否超时
                duration_minutes = (now - record.triggered_at).total_seconds() / 60
                
                if duration_minutes > timeout_minutes:
                    # 检查是否需要升级（级别不同）
                    if record.alarm_level != target_level:
                        old_level = record.alarm_level
                        record.alarm_level = target_level
                        
                        # 添加备注
                        note = f"\\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] 自动升级: 超时{int(duration_minutes)}分钟未处理，级别由 {old_level} 升级为 {target_level}"
                        if record.resolution_notes:
                            record.resolution_notes += note
                        else:
                            record.resolution_notes = note.strip()
                            
                        await record.save()
                        
                        logger.warning(f"报警自动升级: ID={record.id}, 设备={record.device_code}, {old_level} -> {target_level}")
                        
                        # 发送通知
                        try:
                            from app.services.alarm_integration import create_alarm_notification
                            
                            # 构造通知数据
                            alarm_data = {
                                "id": record.id,
                                "rule_id": record.rule.id,
                                "rule_name": record.rule.rule_name,
                                "device_code": record.device_code,
                                "device_name": record.device_name,
                                "alarm_level": target_level,
                                "alarm_title": f"{record.alarm_title} (已升级)",
                                "alarm_content": f"{record.alarm_content} [超时自动升级]",
                                "field_code": record.field_code,
                                "field_name": record.field_name,
                                "trigger_value": float(record.trigger_value) if record.trigger_value is not None else 0,
                                "triggered_at": record.triggered_at.isoformat(),
                                "escalated": True
                            }
                            await create_alarm_notification(alarm_data)
                            count += 1
                        except Exception as e:
                            logger.error(f"报警升级通知发送失败: {str(e)}")
                            
            if count > 0:
                logger.info(f"已自动升级 {count} 条超时报警")
                
        except Exception as e:
            logger.error(f"检查报警超时失败: {str(e)}")
    
    async def refresh_rules(self) -> None:
        """强制刷新规则缓存"""
        await self.load_rules(force=True)
    
    def get_cache_info(self) -> Dict:
        """获取缓存信息"""
        total_rules = sum(len(rules) for rules in self._rules_cache.values())
        return {
            "total_rules": total_rules,
            "device_types": list(self._rules_cache.keys()),
            "cache_time": self._cache_time.isoformat() if self._cache_time else None,
            "trigger_counts": len(self._trigger_counts),
        }


# 全局单例
alarm_engine = AlarmDetectionEngine()


async def check_and_trigger_alarms(
    device_code: str,
    device_name: Optional[str],
    device_type_code: str,
    data: Dict[str, Any]
) -> List[Dict]:
    """
    检测设备数据并触发报警（供其他模块调用）
    
    Args:
        device_code: 设备编码
        device_name: 设备名称
        device_type_code: 设备类型代码
        data: 设备数据字典
        
    Returns:
        触发的报警列表
    """
    return await alarm_engine.check_device_data(
        device_code=device_code,
        device_name=device_name,
        device_type_code=device_type_code,
        data=data
    )
