#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流执行引擎
实现工作流的真正执行逻辑
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import uuid
import traceback

from app.models.workflow import Workflow, WorkflowExecution, WorkflowNodeExecution
from app.log import logger


class WorkflowError(Exception):
    """工作流执行错误"""
    pass


class NodeExecutionResult:
    """节点执行结果"""
    
    def __init__(
        self, 
        success: bool = True, 
        output: Dict[str, Any] = None,
        error: str = None,
        branch: str = None
    ):
        self.success = success
        self.output = output or {}
        self.error = error
        self.branch = branch  # 用于条件节点指定分支


class NodeExecutor:
    """节点执行器基类"""
    
    async def execute(self, node: Dict, context: Dict[str, Any]) -> NodeExecutionResult:
        """
        执行节点
        
        Args:
            node: 节点定义
            context: 执行上下文（包含变量等）
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        raise NotImplementedError("子类必须实现execute方法")
    
    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        渲染模板字符串，替换 ${变量名} 为实际值
        
        Args:
            template: 模板字符串
            context: 上下文变量
            
        Returns:
            渲染后的字符串
        """
        if not template:
            return template
            
        import re
        
        def replace_var(match):
            var_path = match.group(1)
            try:
                # 支持嵌套访问，如 ${data.user.name}
                value = context
                for key in var_path.split('.'):
                    if isinstance(value, dict):
                        value = value.get(key, '')
                    else:
                        value = getattr(value, key, '')
                return str(value)
            except Exception:
                return match.group(0)
        
        return re.sub(r'\$\{([^}]+)\}', replace_var, template)


class StartNodeExecutor(NodeExecutor):
    """开始节点执行器"""
    
    async def execute(self, node: Dict, context: Dict[str, Any]) -> NodeExecutionResult:
        logger.info(f"执行开始节点: {node.get('name', 'start')}")
        
        # 初始化输入变量
        properties = node.get('properties', {})
        input_variables = properties.get('inputVariables', {})
        
        # 将输入变量合并到上下文
        output = {'_start_time': datetime.now().isoformat()}
        output.update(input_variables)
        
        return NodeExecutionResult(success=True, output=output)


class EndNodeExecutor(NodeExecutor):
    """结束节点执行器"""
    
    async def execute(self, node: Dict, context: Dict[str, Any]) -> NodeExecutionResult:
        logger.info(f"执行结束节点: {node.get('name', 'end')}")
        
        properties = node.get('properties', {})
        end_type = properties.get('endType', 'success')
        output_variables = properties.get('outputVariables', {})
        
        # 收集输出变量
        output = {
            '_end_time': datetime.now().isoformat(),
            '_end_type': end_type,
        }
        
        # 从上下文中提取指定的输出变量
        for key, var_name in output_variables.items():
            if var_name in context:
                output[key] = context[var_name]
        
        return NodeExecutionResult(
            success=(end_type == 'success'),
            output=output
        )


class ConditionNodeExecutor(NodeExecutor):
    """条件节点执行器"""
    
    async def execute(self, node: Dict, context: Dict[str, Any]) -> NodeExecutionResult:
        logger.info(f"执行条件节点: {node.get('name', 'condition')}")
        
        properties = node.get('properties', {})
        
        # 优先使用高级表达式
        expression = properties.get('expression', '')
        if expression:
            result = self._evaluate_expression(expression, context)
        else:
            # 使用简单条件
            left = self._render_template(properties.get('leftOperand', ''), context)
            operator = properties.get('operator', 'eq')
            right = self._render_template(properties.get('rightOperand', ''), context)
            result = self._compare(left, operator, right)
        
        branch = 'true' if result else 'false'
        logger.info(f"条件判断结果: {result}, 分支: {branch}")
        
        return NodeExecutionResult(
            success=True,
            output={'_condition_result': result},
            branch=branch
        )
    
    def _evaluate_expression(self, expression: str, context: Dict[str, Any]) -> bool:
        """安全执行表达式"""
        try:
            # 创建安全的执行环境
            safe_globals = {
                '__builtins__': {},
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'abs': abs,
                'min': min,
                'max': max,
                'sum': sum,
                'any': any,
                'all': all,
            }
            safe_locals = dict(context)
            
            result = eval(expression, safe_globals, safe_locals)
            return bool(result)
        except Exception as e:
            logger.warning(f"表达式执行失败: {expression}, 错误: {e}")
            return False
    
    def _compare(self, left: str, operator: str, right: str) -> bool:
        """执行比较操作"""
        try:
            # 尝试转换为数字进行比较
            try:
                left_num = float(left)
                right_num = float(right)
                left, right = left_num, right_num
            except (ValueError, TypeError):
                pass
            
            if operator == 'eq':
                return left == right
            elif operator == 'ne':
                return left != right
            elif operator == 'gt':
                return left > right
            elif operator == 'gte':
                return left >= right
            elif operator == 'lt':
                return left < right
            elif operator == 'lte':
                return left <= right
            elif operator == 'contains':
                return str(right) in str(left)
            elif operator == 'not_contains':
                return str(right) not in str(left)
            elif operator == 'is_null':
                return left is None or left == '' or left == 'None'
            elif operator == 'is_not_null':
                return left is not None and left != '' and left != 'None'
            else:
                return False
        except Exception as e:
            logger.warning(f"比较操作失败: {left} {operator} {right}, 错误: {e}")
            return False


class ApiNodeExecutor(NodeExecutor):
    """API调用节点执行器"""
    
    async def execute(self, node: Dict, context: Dict[str, Any]) -> NodeExecutionResult:
        logger.info(f"执行API节点: {node.get('name', 'api')}")
        
        properties = node.get('properties', {})
        
        url = self._render_template(properties.get('url', ''), context)
        method = properties.get('method', 'GET').upper()
        headers = properties.get('headers', {})
        params = properties.get('params', {})
        body = properties.get('body', {})
        timeout = properties.get('timeout', 30)
        output_variable = properties.get('outputVariable', 'apiResult')
        
        if not url:
            return NodeExecutionResult(
                success=False,
                error="API地址不能为空"
            )
        
        try:
            import httpx
            
            # 渲染模板变量
            rendered_headers = {}
            for k, v in headers.items():
                rendered_headers[k] = self._render_template(str(v), context)
            
            rendered_params = {}
            for k, v in params.items():
                rendered_params[k] = self._render_template(str(v), context)
            
            # 渲染body中的模板变量
            rendered_body = self._render_body(body, context)
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method == 'GET':
                    response = await client.get(url, headers=rendered_headers, params=rendered_params)
                elif method == 'POST':
                    response = await client.post(url, headers=rendered_headers, json=rendered_body)
                elif method == 'PUT':
                    response = await client.put(url, headers=rendered_headers, json=rendered_body)
                elif method == 'DELETE':
                    response = await client.delete(url, headers=rendered_headers)
                elif method == 'PATCH':
                    response = await client.patch(url, headers=rendered_headers, json=rendered_body)
                else:
                    return NodeExecutionResult(
                        success=False,
                        error=f"不支持的HTTP方法: {method}"
                    )
            
            # 解析响应
            try:
                response_data = response.json()
            except Exception:
                response_data = response.text
            
            output = {
                output_variable: {
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'data': response_data,
                }
            }
            
            success = 200 <= response.status_code < 300
            
            return NodeExecutionResult(
                success=success,
                output=output,
                error=None if success else f"HTTP {response.status_code}"
            )
            
        except Exception as e:
            logger.error(f"API调用失败: {e}")
            return NodeExecutionResult(
                success=False,
                error=str(e)
            )
    
    def _render_body(self, body: Any, context: Dict[str, Any]) -> Any:
        """递归渲染body中的模板变量"""
        if isinstance(body, str):
            return self._render_template(body, context)
        elif isinstance(body, dict):
            return {k: self._render_body(v, context) for k, v in body.items()}
        elif isinstance(body, list):
            return [self._render_body(item, context) for item in body]
        else:
            return body


class DelayNodeExecutor(NodeExecutor):
    """延时节点执行器"""
    
    async def execute(self, node: Dict, context: Dict[str, Any]) -> NodeExecutionResult:
        logger.info(f"执行延时节点: {node.get('name', 'delay')}")
        
        properties = node.get('properties', {})
        duration = properties.get('duration', 1)
        unit = properties.get('unit', 'seconds')
        
        # 转换为秒
        multipliers = {
            'seconds': 1,
            'minutes': 60,
            'hours': 3600,
            'days': 86400,
        }
        
        seconds = duration * multipliers.get(unit, 1)
        
        logger.info(f"延时等待 {seconds} 秒")
        await asyncio.sleep(seconds)
        
        return NodeExecutionResult(
            success=True,
            output={'_delay_seconds': seconds}
        )


class ScriptNodeExecutor(NodeExecutor):
    """脚本节点执行器"""
    
    async def execute(self, node: Dict, context: Dict[str, Any]) -> NodeExecutionResult:
        logger.info(f"执行脚本节点: {node.get('name', 'script')}")
        
        properties = node.get('properties', {})
        language = properties.get('language', 'javascript')
        script = properties.get('script', '')
        output_variable = properties.get('outputVariable', 'scriptResult')
        
        if not script:
            return NodeExecutionResult(
                success=False,
                error="脚本内容不能为空"
            )
        
        try:
            if language == 'python':
                result = self._execute_python(script, context)
            else:
                # JavaScript暂不支持，返回模拟结果
                result = {'message': 'JavaScript执行暂不支持，请使用Python'}
            
            return NodeExecutionResult(
                success=True,
                output={output_variable: result}
            )
            
        except Exception as e:
            logger.error(f"脚本执行失败: {e}")
            return NodeExecutionResult(
                success=False,
                error=str(e)
            )
    
    def _execute_python(self, script: str, context: Dict[str, Any]) -> Any:
        """执行Python脚本"""
        # 创建安全的执行环境
        safe_globals = {
            '__builtins__': {
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'abs': abs,
                'min': min,
                'max': max,
                'sum': sum,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'sorted': sorted,
                'print': print,
            }
        }
        safe_locals = {'context': context, 'result': None}
        
        exec(script, safe_globals, safe_locals)
        
        return safe_locals.get('result')


class NotificationNodeExecutor(NodeExecutor):
    """通知节点执行器"""
    
    async def execute(self, node: Dict, context: Dict[str, Any]) -> NodeExecutionResult:
        logger.info(f"执行通知节点: {node.get('name', 'notification')}")
        
        properties = node.get('properties', {})
        channels = properties.get('channels', ['internal'])
        title = self._render_template(properties.get('title', ''), context)
        content = self._render_template(properties.get('content', ''), context)
        recipients = properties.get('recipients', '')
        
        # 这里可以集成实际的通知服务
        logger.info(f"发送通知: 渠道={channels}, 标题={title}, 接收人={recipients}")
        
        # 模拟发送通知
        sent_count = len(channels)
        
        return NodeExecutionResult(
            success=True,
            output={
                '_notification_sent': True,
                '_notification_channels': channels,
                '_notification_count': sent_count,
            }
        )


# ============== 设备节点执行器 ==============

class DeviceQueryNodeExecutor(NodeExecutor):
    """设备查询节点执行器"""
    
    async def execute(self, node: Dict, context: Dict[str, Any]) -> NodeExecutionResult:
        logger.info(f"执行设备查询节点: {node.get('name', 'device_query')}")
        
        properties = node.get('properties', {})
        device_type = properties.get('deviceType', '')
        device_id = properties.get('deviceId', '')
        query_fields = properties.get('queryFields', [])
        output_variable = properties.get('outputVariable', 'deviceData')
        
        # TODO: 集成实际的设备查询服务
        logger.info(f"查询设备: type={device_type}, id={device_id}")
        
        # 模拟查询结果
        result = {
            'device_id': device_id,
            'device_type': device_type,
            'status': 'online',
            'data': {}
        }
        
        return NodeExecutionResult(
            success=True,
            output={output_variable: result}
        )


class DeviceControlNodeExecutor(NodeExecutor):
    """设备控制节点执行器"""
    
    async def execute(self, node: Dict, context: Dict[str, Any]) -> NodeExecutionResult:
        logger.info(f"执行设备控制节点: {node.get('name', 'device_control')}")
        
        properties = node.get('properties', {})
        device_id = self._render_template(properties.get('deviceId', ''), context)
        command = properties.get('command', '')
        parameters = properties.get('parameters', {})
        
        # TODO: 集成实际的设备控制服务
        logger.info(f"控制设备: id={device_id}, command={command}")
        
        return NodeExecutionResult(
            success=True,
            output={
                '_control_sent': True,
                '_device_id': device_id,
                '_command': command
            }
        )


class DeviceDataNodeExecutor(NodeExecutor):
    """数据采集节点执行器"""
    
    async def execute(self, node: Dict, context: Dict[str, Any]) -> NodeExecutionResult:
        logger.info(f"执行数据采集节点: {node.get('name', 'device_data')}")
        
        properties = node.get('properties', {})
        device_id = self._render_template(properties.get('deviceId', ''), context)
        data_points = properties.get('dataPoints', [])
        output_variable = properties.get('outputVariable', 'collectedData')
        
        # TODO: 集成实际的数据采集服务
        logger.info(f"采集数据: device={device_id}, points={data_points}")
        
        # 模拟采集结果
        result = {
            'device_id': device_id,
            'timestamp': datetime.now().isoformat(),
            'data': {}
        }
        
        return NodeExecutionResult(
            success=True,
            output={output_variable: result}
        )


class DeviceStatusNodeExecutor(NodeExecutor):
    """状态检测节点执行器"""
    
    async def execute(self, node: Dict, context: Dict[str, Any]) -> NodeExecutionResult:
        logger.info(f"执行状态检测节点: {node.get('name', 'device_status')}")
        
        properties = node.get('properties', {})
        device_id = self._render_template(properties.get('deviceId', ''), context)
        expected_status = properties.get('expectedStatus', 'online')
        
        # TODO: 集成实际的状态检测服务
        current_status = 'online'  # 模拟当前状态
        
        is_match = current_status == expected_status
        branch = 'true' if is_match else 'false'
        
        return NodeExecutionResult(
            success=True,
            output={
                '_device_status': current_status,
                '_status_match': is_match
            },
            branch=branch
        )


# ============== 报警节点执行器 ==============

class AlarmTriggerNodeExecutor(NodeExecutor):
    """触发报警节点执行器"""
    
    async def execute(self, node: Dict, context: Dict[str, Any]) -> NodeExecutionResult:
        logger.info(f"执行触发报警节点: {node.get('name', 'alarm_trigger')}")
        
        properties = node.get('properties', {})
        alarm_type = properties.get('alarmType', 'warning')
        alarm_level = properties.get('alarmLevel', 'medium')
        title = self._render_template(properties.get('title', ''), context)
        content = self._render_template(properties.get('content', ''), context)
        device_id = self._render_template(properties.get('deviceId', ''), context)
        
        # TODO: 集成实际的报警服务
        logger.info(f"触发报警: type={alarm_type}, level={alarm_level}, title={title}")
        
        return NodeExecutionResult(
            success=True,
            output={
                '_alarm_triggered': True,
                '_alarm_type': alarm_type,
                '_alarm_level': alarm_level
            }
        )


class AlarmCheckNodeExecutor(NodeExecutor):
    """报警检测节点执行器"""
    
    async def execute(self, node: Dict, context: Dict[str, Any]) -> NodeExecutionResult:
        logger.info(f"执行报警检测节点: {node.get('name', 'alarm_check')}")
        
        properties = node.get('properties', {})
        check_type = properties.get('checkType', 'threshold')
        threshold = properties.get('threshold', 0)
        value_path = properties.get('valuePath', '')
        
        # 从上下文获取要检测的值
        value = context.get(value_path, 0)
        
        # 执行检测
        is_alarm = False
        if check_type == 'threshold':
            is_alarm = float(value) > float(threshold)
        elif check_type == 'range':
            min_val = properties.get('minValue', 0)
            max_val = properties.get('maxValue', 100)
            is_alarm = not (float(min_val) <= float(value) <= float(max_val))
        
        branch = 'true' if is_alarm else 'false'
        
        return NodeExecutionResult(
            success=True,
            output={
                '_alarm_detected': is_alarm,
                '_checked_value': value
            },
            branch=branch
        )


class AlarmClearNodeExecutor(NodeExecutor):
    """清除报警节点执行器"""
    
    async def execute(self, node: Dict, context: Dict[str, Any]) -> NodeExecutionResult:
        logger.info(f"执行清除报警节点: {node.get('name', 'alarm_clear')}")
        
        properties = node.get('properties', {})
        alarm_id = self._render_template(properties.get('alarmId', ''), context)
        device_id = self._render_template(properties.get('deviceId', ''), context)
        
        # TODO: 集成实际的报警清除服务
        logger.info(f"清除报警: alarm_id={alarm_id}, device_id={device_id}")
        
        return NodeExecutionResult(
            success=True,
            output={
                '_alarm_cleared': True,
                '_alarm_id': alarm_id
            }
        )


# ============== 扩展动作节点执行器 ==============

class DatabaseNodeExecutor(NodeExecutor):
    """数据库操作节点执行器"""
    
    async def execute(self, node: Dict, context: Dict[str, Any]) -> NodeExecutionResult:
        logger.info(f"执行数据库节点: {node.get('name', 'database')}")
        
        properties = node.get('properties', {})
        operation = properties.get('operation', 'query')
        sql = self._render_template(properties.get('sql', ''), context)
        output_variable = properties.get('outputVariable', 'dbResult')
        
        # TODO: 集成实际的数据库服务
        logger.info(f"数据库操作: operation={operation}, sql={sql[:100]}...")
        
        # 模拟结果
        result = {
            'operation': operation,
            'affected_rows': 0,
            'data': []
        }
        
        return NodeExecutionResult(
            success=True,
            output={output_variable: result}
        )


class TransformNodeExecutor(NodeExecutor):
    """数据转换节点执行器"""
    
    async def execute(self, node: Dict, context: Dict[str, Any]) -> NodeExecutionResult:
        logger.info(f"执行数据转换节点: {node.get('name', 'transform')}")
        
        properties = node.get('properties', {})
        input_variable = properties.get('inputVariable', '')
        output_variable = properties.get('outputVariable', 'transformedData')
        transform_type = properties.get('transformType', 'json')
        mapping = properties.get('mapping', {})
        
        # 获取输入数据
        input_data = context.get(input_variable, {})
        
        # 执行转换
        if transform_type == 'mapping':
            result = {}
            for target_key, source_path in mapping.items():
                value = input_data
                for key in source_path.split('.'):
                    if isinstance(value, dict):
                        value = value.get(key, '')
                result[target_key] = value
        else:
            result = input_data
        
        return NodeExecutionResult(
            success=True,
            output={output_variable: result}
        )


# ============== 扩展通知节点执行器 ==============

class EmailNodeExecutor(NodeExecutor):
    """邮件发送节点执行器"""
    
    async def execute(self, node: Dict, context: Dict[str, Any]) -> NodeExecutionResult:
        logger.info(f"执行邮件节点: {node.get('name', 'email')}")
        
        properties = node.get('properties', {})
        to = self._render_template(properties.get('to', ''), context)
        cc = self._render_template(properties.get('cc', ''), context)
        subject = self._render_template(properties.get('subject', ''), context)
        body = self._render_template(properties.get('body', ''), context)
        template_id = properties.get('templateId', '')
        
        # TODO: 集成实际的邮件服务
        logger.info(f"发送邮件: to={to}, subject={subject}")
        
        return NodeExecutionResult(
            success=True,
            output={
                '_email_sent': True,
                '_email_to': to,
                '_email_subject': subject
            }
        )


class SmsNodeExecutor(NodeExecutor):
    """短信发送节点执行器"""
    
    async def execute(self, node: Dict, context: Dict[str, Any]) -> NodeExecutionResult:
        logger.info(f"执行短信节点: {node.get('name', 'sms')}")
        
        properties = node.get('properties', {})
        phone = self._render_template(properties.get('phone', ''), context)
        content = self._render_template(properties.get('content', ''), context)
        template_id = properties.get('templateId', '')
        
        # TODO: 集成实际的短信服务
        logger.info(f"发送短信: phone={phone}, content={content[:50]}...")
        
        return NodeExecutionResult(
            success=True,
            output={
                '_sms_sent': True,
                '_sms_phone': phone
            }
        )


class WebhookNodeExecutor(NodeExecutor):
    """Webhook调用节点执行器"""
    
    async def execute(self, node: Dict, context: Dict[str, Any]) -> NodeExecutionResult:
        logger.info(f"执行Webhook节点: {node.get('name', 'webhook')}")
        
        properties = node.get('properties', {})
        url = self._render_template(properties.get('url', ''), context)
        method = properties.get('method', 'POST')
        headers = properties.get('headers', {})
        payload = properties.get('payload', {})
        
        if not url:
            return NodeExecutionResult(
                success=False,
                error="Webhook URL不能为空"
            )
        
        try:
            import httpx
            
            # 渲染payload中的模板变量
            rendered_payload = self._render_body(payload, context)
            
            async with httpx.AsyncClient(timeout=30) as client:
                if method.upper() == 'GET':
                    response = await client.get(url, headers=headers)
                else:
                    response = await client.post(url, headers=headers, json=rendered_payload)
            
            return NodeExecutionResult(
                success=response.status_code < 400,
                output={
                    '_webhook_status': response.status_code,
                    '_webhook_response': response.text[:500] if response.text else ''
                }
            )
            
        except Exception as e:
            logger.error(f"Webhook调用失败: {e}")
            return NodeExecutionResult(
                success=False,
                error=str(e)
            )
    
    def _render_body(self, body: Any, context: Dict[str, Any]) -> Any:
        """递归渲染body中的模板变量"""
        if isinstance(body, str):
            return self._render_template(body, context)
        elif isinstance(body, dict):
            return {k: self._render_body(v, context) for k, v in body.items()}
        elif isinstance(body, list):
            return [self._render_body(item, context) for item in body]
        else:
            return body



class MetadataAnalysisNodeExecutor(NodeExecutor):
    """元数据分析节点执行器"""
    
    async def execute(self, node: Dict, context: Dict[str, Any]) -> NodeExecutionResult:
        logger.info(f"执行元数据分析节点: {node.get('name', 'metadata_analysis')}")
        
        properties = node.get('properties', {})
        model_code = properties.get('model_code')
        
        if not model_code:
            return NodeExecutionResult(success=False, error="未配置模型代码")
            
        # 提取数据 (假设上游节点输出了 data 或 payload)
        data = context.get('data') or context.get('payload') or {}
        
        try:
            from app.services.metadata_service import MetadataService
            result = await MetadataService.execute_model(model_code, data)
            
            return NodeExecutionResult(
                success=True, 
                output={'result': result}
            )
        except Exception as e:
            logger.error(f"元数据模型执行失败: {e}")
            return NodeExecutionResult(success=False, error=str(e))


class WorkflowEngine:
    """工作流执行引擎"""
    
    def __init__(self):
        self.node_executors: Dict[str, NodeExecutor] = {}
        self._register_default_executors()
    
    def _register_default_executors(self):
        """注册默认节点执行器"""
        self.node_executors = {
            # 基础节点
            'start': StartNodeExecutor(),
            'end': EndNodeExecutor(),
            # 逻辑控制节点
            'condition': ConditionNodeExecutor(),
            'loop': StartNodeExecutor(),  # 循环节点待实现
            'parallel': StartNodeExecutor(),  # 并行节点待实现
            'switch': ConditionNodeExecutor(),  # 多路分支使用条件节点逻辑
            # 设备节点
            'device_query': DeviceQueryNodeExecutor(),
            'device_control': DeviceControlNodeExecutor(),
            'device_data': DeviceDataNodeExecutor(),
            'device_status': DeviceStatusNodeExecutor(),
            # 报警节点
            'alarm_trigger': AlarmTriggerNodeExecutor(),
            'alarm_check': AlarmCheckNodeExecutor(),
            'alarm_clear': AlarmClearNodeExecutor(),
            # 动作节点
            'api': ApiNodeExecutor(),
            'http': ApiNodeExecutor(),  # HTTP请求使用API节点逻辑
            'database': DatabaseNodeExecutor(),
            'script': ScriptNodeExecutor(),
            'delay': DelayNodeExecutor(),
            'transform': TransformNodeExecutor(),
            # 通知节点
            'notification': NotificationNodeExecutor(),
            'email': EmailNodeExecutor(),
            'sms': SmsNodeExecutor(),
            'webhook': WebhookNodeExecutor(),
            # 元数据节点
            'metadata_analysis': MetadataAnalysisNodeExecutor(),
            # 兼容旧节点
            'process': StartNodeExecutor(),
        }
    
    def register_executor(self, node_type: str, executor: NodeExecutor):
        """注册自定义节点执行器"""
        self.node_executors[node_type] = executor
    
    async def execute(
        self, 
        workflow: Workflow, 
        context: Dict[str, Any] = None,
        trigger_type: str = 'manual',
        trigger_data: Dict[str, Any] = None,
        triggered_by: int = None,
        triggered_by_name: str = None,
    ) -> WorkflowExecution:
        """
        执行工作流
        
        Args:
            workflow: 工作流定义
            context: 初始上下文
            trigger_type: 触发类型
            trigger_data: 触发数据
            triggered_by: 触发人ID
            triggered_by_name: 触发人姓名
            
        Returns:
            WorkflowExecution: 执行记录
        """
        # 创建执行记录
        execution_id = f"exec_{uuid.uuid4().hex[:16]}"
        execution = await WorkflowExecution.create(
            workflow=workflow,
            execution_id=execution_id,
            status='running',
            trigger_type=trigger_type,
            trigger_data=trigger_data or {},
            triggered_by=triggered_by,
            triggered_by_name=triggered_by_name,
            context=context or {},
            variables=context or {},
            started_at=datetime.now(),
        )
        
        logger.info(f"开始执行工作流: {workflow.code}, 执行ID: {execution_id}")
        
        try:
            # 初始化执行上下文
            exec_context = dict(context or {})
            exec_context['_workflow_id'] = workflow.id
            exec_context['_execution_id'] = execution_id
            exec_context['_trigger_type'] = trigger_type
            exec_context['_trigger_data'] = trigger_data or {}
            
            # 找到开始节点
            start_node = self._find_start_node(workflow.nodes)
            if not start_node:
                raise WorkflowError("工作流缺少开始节点")
            
            # 执行节点链
            await self._execute_node_chain(execution, start_node, workflow, exec_context)
            
            # 更新执行状态为成功
            execution.status = 'success'
            execution.completed_at = datetime.now()
            execution.duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)
            execution.result = {'context': exec_context}
            await execution.save()
            
            # 更新工作流统计
            workflow.execution_count += 1
            workflow.success_count += 1
            workflow.last_executed_at = datetime.now()
            await workflow.save()
            
            logger.info(f"工作流执行成功: {workflow.code}, 执行ID: {execution_id}")
            
        except Exception as e:
            # 更新执行状态为失败
            execution.status = 'failed'
            execution.completed_at = datetime.now()
            execution.duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)
            execution.error_message = str(e)
            execution.error_stack = traceback.format_exc()
            await execution.save()
            
            # 更新工作流统计
            workflow.execution_count += 1
            workflow.failure_count += 1
            workflow.last_executed_at = datetime.now()
            await workflow.save()
            
            logger.error(f"工作流执行失败: {workflow.code}, 错误: {e}")
        
        return execution
    
    def _find_start_node(self, nodes: List[Dict]) -> Optional[Dict]:
        """找到开始节点"""
        for node in nodes:
            if node.get('type') == 'start':
                return node
        return None
    
    def _find_node_by_id(self, nodes: List[Dict], node_id: str) -> Optional[Dict]:
        """根据ID查找节点"""
        for node in nodes:
            if node.get('id') == node_id:
                return node
        return None
    
    def _find_next_nodes(
        self, 
        workflow: Workflow, 
        current_node: Dict, 
        result: NodeExecutionResult
    ) -> List[Dict]:
        """
        找到下一个要执行的节点
        
        Args:
            workflow: 工作流定义
            current_node: 当前节点
            result: 当前节点执行结果
            
        Returns:
            下一个节点列表
        """
        next_nodes = []
        current_id = current_node.get('id')
        
        for conn in workflow.connections:
            from_id = conn.get('fromNodeId') or conn.get('from_node_id')
            to_id = conn.get('toNodeId') or conn.get('to_node_id')
            
            if from_id == current_id:
                # 检查条件分支
                conn_condition = conn.get('condition') or conn.get('label', '')
                
                # 如果是条件节点，根据分支选择
                if result.branch:
                    if conn_condition.lower() == result.branch or not conn_condition:
                        next_node = self._find_node_by_id(workflow.nodes, to_id)
                        if next_node:
                            next_nodes.append(next_node)
                else:
                    # 非条件节点，执行所有连接
                    next_node = self._find_node_by_id(workflow.nodes, to_id)
                    if next_node:
                        next_nodes.append(next_node)
        
        return next_nodes
    
    async def _execute_node_chain(
        self, 
        execution: WorkflowExecution, 
        node: Dict, 
        workflow: Workflow, 
        context: Dict[str, Any]
    ):
        """
        执行节点链
        
        Args:
            execution: 执行记录
            node: 当前节点
            workflow: 工作流定义
            context: 执行上下文
        """
        # 执行当前节点
        result = await self._execute_single_node(execution, node, context)
        
        # 更新上下文
        context.update(result.output)
        
        # 如果是结束节点，停止执行
        if node.get('type') == 'end':
            return
        
        # 如果执行失败且不是条件节点，停止执行
        if not result.success and node.get('type') != 'condition':
            raise WorkflowError(f"节点 {node.get('name', node.get('id'))} 执行失败: {result.error}")
        
        # 找到下一个节点
        next_nodes = self._find_next_nodes(workflow, node, result)
        
        if not next_nodes and node.get('type') != 'end':
            logger.warning(f"节点 {node.get('name', node.get('id'))} 没有后续节点")
            return
        
        # 执行下一个节点（目前只支持顺序执行，不支持并行）
        for next_node in next_nodes:
            await self._execute_node_chain(execution, next_node, workflow, context)
    
    async def _execute_single_node(
        self, 
        execution: WorkflowExecution, 
        node: Dict, 
        context: Dict[str, Any]
    ) -> NodeExecutionResult:
        """
        执行单个节点
        
        Args:
            execution: 执行记录
            node: 节点定义
            context: 执行上下文
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        node_id = node.get('id')
        node_type = node.get('type')
        node_name = node.get('name', node_id)
        
        # 创建节点执行记录
        node_execution = await WorkflowNodeExecution.create(
            execution=execution,
            node_id=node_id,
            node_type=node_type,
            node_name=node_name,
            status='running',
            started_at=datetime.now(),
            input_data=dict(context),
        )
        
        logger.info(f"执行节点: {node_name} (类型: {node_type})")
        
        try:
            # 获取节点执行器
            executor = self.node_executors.get(node_type)
            if not executor:
                # 使用默认执行器
                executor = StartNodeExecutor()
                logger.warning(f"未找到节点类型 {node_type} 的执行器，使用默认执行器")
            
            # 执行节点
            result = await executor.execute(node, context)
            
            # 更新节点执行记录
            node_execution.status = 'success' if result.success else 'failed'
            node_execution.completed_at = datetime.now()
            node_execution.duration_ms = int((node_execution.completed_at - node_execution.started_at).total_seconds() * 1000)
            node_execution.output_data = result.output
            if result.error:
                node_execution.error_message = result.error
            await node_execution.save()
            
            # 更新执行记录的当前节点
            execution.current_node_id = node_id
            execution.node_states[node_id] = {
                'status': node_execution.status,
                'output': result.output,
            }
            await execution.save()
            
            return result
            
        except Exception as e:
            # 更新节点执行记录为失败
            node_execution.status = 'failed'
            node_execution.completed_at = datetime.now()
            node_execution.duration_ms = int((node_execution.completed_at - node_execution.started_at).total_seconds() * 1000)
            node_execution.error_message = str(e)
            node_execution.error_details = {'traceback': traceback.format_exc()}
            await node_execution.save()
            
            raise


# 全局引擎实例
_engine_instance: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """获取工作流引擎实例"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = WorkflowEngine()
    return _engine_instance
