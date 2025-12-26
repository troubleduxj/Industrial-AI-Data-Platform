/**
 * 节点属性配置Schema定义
 * 定义各类型节点的属性配置表单
 */

// ========== 类型定义 ==========

/** 表单字段类型 */
export type PropertyFieldType = 
  | 'input' 
  | 'textarea' 
  | 'select' 
  | 'switch' 
  | 'number' 
  | 'json' 
  | 'code' 
  | 'color'
  | 'multiselect'
  | 'slider'
  | 'datepicker'

/** 选项配置 */
export interface SelectOption {
  label: string
  value: string | number | boolean
  disabled?: boolean
  description?: string
}

/** 表单字段验证规则 */
export interface ValidationRule {
  required?: boolean
  message?: string
  min?: number
  max?: number
  pattern?: string
  validator?: (value: any) => boolean | string
}

/** 节点属性字段定义 */
export interface NodePropertyField {
  /** 字段类型 */
  type: PropertyFieldType
  /** 字段名（对应节点properties中的key） */
  field: string
  /** 显示标签 */
  label: string
  /** 是否必填 */
  required?: boolean
  /** 占位符 */
  placeholder?: string
  /** 选项列表（select/multiselect类型使用） */
  options?: SelectOption[]
  /** 默认值 */
  defaultValue?: any
  /** 验证规则 */
  rules?: ValidationRule[]
  /** 字段描述/帮助文本 */
  description?: string
  /** 是否禁用 */
  disabled?: boolean
  /** 是否隐藏 */
  hidden?: boolean
  /** 分组名称 */
  group?: string
  /** 显示条件（依赖其他字段的值） */
  showWhen?: {
    field: string
    value: any
  }
  /** 额外配置 */
  props?: Record<string, any>
}

/** 节点属性分组 */
export interface PropertyGroup {
  name: string
  label: string
  collapsed?: boolean
  fields: string[]
}

/** 节点属性Schema */
export interface NodePropertySchema {
  /** 节点类型 */
  nodeType: string
  /** 属性字段列表 */
  fields: NodePropertyField[]
  /** 字段分组 */
  groups?: PropertyGroup[]
}

// ========== 通用选项定义 ==========

/** HTTP请求方法选项 */
export const HTTP_METHOD_OPTIONS: SelectOption[] = [
  { label: 'GET', value: 'GET' },
  { label: 'POST', value: 'POST' },
  { label: 'PUT', value: 'PUT' },
  { label: 'DELETE', value: 'DELETE' },
  { label: 'PATCH', value: 'PATCH' },
]

/** 比较操作符选项 */
export const COMPARE_OPERATOR_OPTIONS: SelectOption[] = [
  { label: '等于 (==)', value: 'eq' },
  { label: '不等于 (!=)', value: 'ne' },
  { label: '大于 (>)', value: 'gt' },
  { label: '大于等于 (>=)', value: 'gte' },
  { label: '小于 (<)', value: 'lt' },
  { label: '小于等于 (<=)', value: 'lte' },
  { label: '包含', value: 'contains' },
  { label: '不包含', value: 'not_contains' },
  { label: '为空', value: 'is_null' },
  { label: '不为空', value: 'is_not_null' },
]

/** 逻辑操作符选项 */
export const LOGIC_OPERATOR_OPTIONS: SelectOption[] = [
  { label: '与 (AND)', value: 'and' },
  { label: '或 (OR)', value: 'or' },
]

/** 结束类型选项 */
export const END_TYPE_OPTIONS: SelectOption[] = [
  { label: '正常结束', value: 'success' },
  { label: '异常结束', value: 'error' },
  { label: '取消结束', value: 'cancel' },
]

/** 时间单位选项 */
export const TIME_UNIT_OPTIONS: SelectOption[] = [
  { label: '秒', value: 'seconds' },
  { label: '分钟', value: 'minutes' },
  { label: '小时', value: 'hours' },
  { label: '天', value: 'days' },
]

/** 报警级别选项 */
export const ALARM_LEVEL_OPTIONS: SelectOption[] = [
  { label: '信息', value: 'info' },
  { label: '警告', value: 'warning' },
  { label: '错误', value: 'error' },
  { label: '严重', value: 'critical' },
]

/** 通知渠道选项 */
export const NOTIFY_CHANNEL_OPTIONS: SelectOption[] = [
  { label: '站内消息', value: 'internal' },
  { label: '邮件', value: 'email' },
  { label: '短信', value: 'sms' },
  { label: '钉钉', value: 'dingtalk' },
  { label: '企业微信', value: 'wechat_work' },
]

// ========== 节点属性Schema定义 ==========

/** 开始节点属性 */
const START_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'start',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '开始',
    },
    {
      type: 'textarea',
      field: 'description',
      label: '描述',
      placeholder: '请输入节点描述',
      props: { rows: 3 },
    },
    {
      type: 'json',
      field: 'inputVariables',
      label: '输入变量',
      description: '定义工作流的输入参数',
      defaultValue: {},
    },
  ],
}

/** 结束节点属性 */
const END_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'end',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '结束',
    },
    {
      type: 'select',
      field: 'endType',
      label: '结束类型',
      options: END_TYPE_OPTIONS,
      defaultValue: 'success',
    },
    {
      type: 'textarea',
      field: 'description',
      label: '描述',
      placeholder: '请输入节点描述',
      props: { rows: 3 },
    },
    {
      type: 'json',
      field: 'outputVariables',
      label: '输出变量',
      description: '定义工作流的输出结果',
      defaultValue: {},
    },
  ],
}

/** 条件节点属性 */
const CONDITION_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'condition',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '条件判断',
    },
    {
      type: 'textarea',
      field: 'description',
      label: '描述',
      placeholder: '请输入节点描述',
      props: { rows: 2 },
    },
    {
      type: 'input',
      field: 'leftOperand',
      label: '左操作数',
      required: true,
      placeholder: '变量名或值，如: ${data.value}',
      description: '支持使用 ${变量名} 引用上下文变量',
    },
    {
      type: 'select',
      field: 'operator',
      label: '比较操作符',
      required: true,
      options: COMPARE_OPERATOR_OPTIONS,
      defaultValue: 'eq',
    },
    {
      type: 'input',
      field: 'rightOperand',
      label: '右操作数',
      placeholder: '比较值',
      description: '当操作符为"为空"或"不为空"时可不填',
      showWhen: {
        field: 'operator',
        value: ['eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'contains', 'not_contains'],
      },
    },
    {
      type: 'code',
      field: 'expression',
      label: '高级表达式',
      placeholder: 'data.value > 100 && data.status === "active"',
      description: '使用JavaScript表达式进行复杂条件判断',
      props: { language: 'javascript', height: 100 },
    },
  ],
  groups: [
    { name: 'basic', label: '基本信息', fields: ['name', 'description'] },
    { name: 'condition', label: '条件配置', fields: ['leftOperand', 'operator', 'rightOperand'] },
    { name: 'advanced', label: '高级配置', collapsed: true, fields: ['expression'] },
  ],
}

/** API调用节点属性 */
const API_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'api',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: 'API调用',
    },
    {
      type: 'textarea',
      field: 'description',
      label: '描述',
      placeholder: '请输入节点描述',
      props: { rows: 2 },
    },
    {
      type: 'input',
      field: 'url',
      label: 'API地址',
      required: true,
      placeholder: 'https://api.example.com/endpoint',
      description: '支持使用 ${变量名} 动态替换',
    },
    {
      type: 'select',
      field: 'method',
      label: '请求方法',
      required: true,
      options: HTTP_METHOD_OPTIONS,
      defaultValue: 'GET',
    },
    {
      type: 'json',
      field: 'headers',
      label: '请求头',
      placeholder: '{"Content-Type": "application/json"}',
      defaultValue: { 'Content-Type': 'application/json' },
    },
    {
      type: 'json',
      field: 'params',
      label: '查询参数',
      placeholder: '{"key": "value"}',
      defaultValue: {},
      showWhen: { field: 'method', value: 'GET' },
    },
    {
      type: 'json',
      field: 'body',
      label: '请求体',
      placeholder: '{"data": "value"}',
      defaultValue: {},
      showWhen: { field: 'method', value: ['POST', 'PUT', 'PATCH'] },
    },
    {
      type: 'number',
      field: 'timeout',
      label: '超时时间(秒)',
      defaultValue: 30,
      props: { min: 1, max: 300 },
    },
    {
      type: 'number',
      field: 'retryCount',
      label: '重试次数',
      defaultValue: 0,
      props: { min: 0, max: 5 },
    },
    {
      type: 'input',
      field: 'outputVariable',
      label: '输出变量名',
      placeholder: 'apiResult',
      description: '将API响应保存到指定变量',
      defaultValue: 'apiResult',
    },
  ],
  groups: [
    { name: 'basic', label: '基本信息', fields: ['name', 'description'] },
    { name: 'request', label: '请求配置', fields: ['url', 'method', 'headers', 'params', 'body'] },
    { name: 'advanced', label: '高级配置', collapsed: true, fields: ['timeout', 'retryCount', 'outputVariable'] },
  ],
}

/** 数据库节点属性 */
const DATABASE_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'database',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '数据库操作',
    },
    {
      type: 'textarea',
      field: 'description',
      label: '描述',
      placeholder: '请输入节点描述',
      props: { rows: 2 },
    },
    {
      type: 'select',
      field: 'operation',
      label: '操作类型',
      required: true,
      options: [
        { label: '查询 (SELECT)', value: 'select' },
        { label: '插入 (INSERT)', value: 'insert' },
        { label: '更新 (UPDATE)', value: 'update' },
        { label: '删除 (DELETE)', value: 'delete' },
        { label: '执行SQL', value: 'execute' },
      ],
      defaultValue: 'select',
    },
    {
      type: 'input',
      field: 'table',
      label: '表名',
      placeholder: '数据库表名',
      showWhen: { field: 'operation', value: ['select', 'insert', 'update', 'delete'] },
    },
    {
      type: 'code',
      field: 'sql',
      label: 'SQL语句',
      placeholder: 'SELECT * FROM table WHERE id = ${id}',
      description: '支持使用 ${变量名} 参数化查询',
      props: { language: 'sql', height: 150 },
      showWhen: { field: 'operation', value: 'execute' },
    },
    {
      type: 'json',
      field: 'conditions',
      label: '查询条件',
      placeholder: '{"field": "value"}',
      defaultValue: {},
      showWhen: { field: 'operation', value: ['select', 'update', 'delete'] },
    },
    {
      type: 'json',
      field: 'data',
      label: '数据',
      placeholder: '{"field": "value"}',
      defaultValue: {},
      showWhen: { field: 'operation', value: ['insert', 'update'] },
    },
    {
      type: 'input',
      field: 'outputVariable',
      label: '输出变量名',
      placeholder: 'dbResult',
      defaultValue: 'dbResult',
    },
  ],
}

/** 延时节点属性 */
const DELAY_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'delay',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '延时等待',
    },
    {
      type: 'textarea',
      field: 'description',
      label: '描述',
      placeholder: '请输入节点描述',
      props: { rows: 2 },
    },
    {
      type: 'number',
      field: 'duration',
      label: '等待时长',
      required: true,
      defaultValue: 5,
      props: { min: 1 },
    },
    {
      type: 'select',
      field: 'unit',
      label: '时间单位',
      options: TIME_UNIT_OPTIONS,
      defaultValue: 'seconds',
    },
  ],
}

/** 脚本节点属性 */
const SCRIPT_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'script',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '脚本执行',
    },
    {
      type: 'textarea',
      field: 'description',
      label: '描述',
      placeholder: '请输入节点描述',
      props: { rows: 2 },
    },
    {
      type: 'select',
      field: 'language',
      label: '脚本语言',
      options: [
        { label: 'JavaScript', value: 'javascript' },
        { label: 'Python', value: 'python' },
      ],
      defaultValue: 'javascript',
    },
    {
      type: 'code',
      field: 'script',
      label: '脚本代码',
      required: true,
      placeholder: '// 在此编写脚本\nreturn { result: "success" }',
      props: { height: 200 },
    },
    {
      type: 'input',
      field: 'outputVariable',
      label: '输出变量名',
      placeholder: 'scriptResult',
      defaultValue: 'scriptResult',
    },
  ],
}

/** 通知节点属性 */
const NOTIFICATION_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'notification',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '发送通知',
    },
    {
      type: 'textarea',
      field: 'description',
      label: '描述',
      placeholder: '请输入节点描述',
      props: { rows: 2 },
    },
    {
      type: 'multiselect',
      field: 'channels',
      label: '通知渠道',
      required: true,
      options: NOTIFY_CHANNEL_OPTIONS,
      defaultValue: ['internal'],
    },
    {
      type: 'input',
      field: 'title',
      label: '通知标题',
      required: true,
      placeholder: '通知标题，支持 ${变量}',
    },
    {
      type: 'textarea',
      field: 'content',
      label: '通知内容',
      required: true,
      placeholder: '通知内容，支持 ${变量}',
      props: { rows: 4 },
    },
    {
      type: 'input',
      field: 'recipients',
      label: '接收人',
      placeholder: '用户ID或邮箱，多个用逗号分隔',
      description: '留空则发送给工作流触发人',
    },
  ],
}

/** 报警节点属性 */
const ALARM_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'alarm',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '触发报警',
    },
    {
      type: 'textarea',
      field: 'description',
      label: '描述',
      placeholder: '请输入节点描述',
      props: { rows: 2 },
    },
    {
      type: 'select',
      field: 'alarmLevel',
      label: '报警级别',
      required: true,
      options: ALARM_LEVEL_OPTIONS,
      defaultValue: 'warning',
    },
    {
      type: 'input',
      field: 'alarmTitle',
      label: '报警标题',
      required: true,
      placeholder: '报警标题',
    },
    {
      type: 'textarea',
      field: 'alarmContent',
      label: '报警内容',
      required: true,
      placeholder: '报警详细内容，支持 ${变量}',
      props: { rows: 3 },
    },
    {
      type: 'input',
      field: 'deviceId',
      label: '关联设备ID',
      placeholder: '可选，关联的设备ID',
    },
    {
      type: 'multiselect',
      field: 'notifyChannels',
      label: '通知渠道',
      options: NOTIFY_CHANNEL_OPTIONS,
      defaultValue: ['internal'],
    },
  ],
}

/** 循环节点属性 */
const LOOP_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'loop',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '循环',
    },
    {
      type: 'textarea',
      field: 'description',
      label: '描述',
      placeholder: '请输入节点描述',
      props: { rows: 2 },
    },
    {
      type: 'select',
      field: 'loopType',
      label: '循环类型',
      required: true,
      options: [
        { label: '遍历数组', value: 'foreach' },
        { label: '固定次数', value: 'count' },
        { label: '条件循环', value: 'while' },
      ],
      defaultValue: 'foreach',
    },
    {
      type: 'input',
      field: 'arrayVariable',
      label: '数组变量',
      placeholder: '${data.items}',
      showWhen: { field: 'loopType', value: 'foreach' },
    },
    {
      type: 'number',
      field: 'count',
      label: '循环次数',
      defaultValue: 10,
      props: { min: 1, max: 1000 },
      showWhen: { field: 'loopType', value: 'count' },
    },
    {
      type: 'input',
      field: 'condition',
      label: '循环条件',
      placeholder: '${index} < 10',
      showWhen: { field: 'loopType', value: 'while' },
    },
    {
      type: 'input',
      field: 'itemVariable',
      label: '当前项变量名',
      placeholder: 'item',
      defaultValue: 'item',
    },
    {
      type: 'input',
      field: 'indexVariable',
      label: '索引变量名',
      placeholder: 'index',
      defaultValue: 'index',
    },
  ],
}

/** 并行节点属性 */
const PARALLEL_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'parallel',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '并行执行',
    },
    {
      type: 'textarea',
      field: 'description',
      label: '描述',
      placeholder: '请输入节点描述',
      props: { rows: 2 },
    },
    {
      type: 'select',
      field: 'waitMode',
      label: '等待模式',
      options: [
        { label: '等待全部完成', value: 'all' },
        { label: '任一完成即可', value: 'any' },
      ],
      defaultValue: 'all',
    },
    {
      type: 'number',
      field: 'maxConcurrency',
      label: '最大并发数',
      defaultValue: 5,
      props: { min: 1, max: 20 },
    },
  ],
}

// ========== Schema注册表 ==========

// ========== 设备节点属性Schema ==========

/** 设备查询节点属性 */
const DEVICE_QUERY_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'device_query',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '设备查询',
    },
    {
      type: 'textarea',
      field: 'description',
      label: '描述',
      placeholder: '请输入节点描述',
      props: { rows: 2 },
    },
    {
      type: 'input',
      field: 'deviceType',
      label: '设备类型',
      placeholder: '设备类型编码',
      description: '留空则查询所有类型',
    },
    {
      type: 'input',
      field: 'deviceId',
      label: '设备ID',
      placeholder: '设备ID，支持 ${变量}',
      description: '留空则查询所有设备',
    },
    {
      type: 'json',
      field: 'queryFields',
      label: '查询字段',
      placeholder: '["field1", "field2"]',
      description: '要查询的字段列表',
      defaultValue: [],
    },
    {
      type: 'input',
      field: 'outputVariable',
      label: '输出变量名',
      placeholder: 'deviceData',
      defaultValue: 'deviceData',
    },
  ],
}

/** 设备控制节点属性 */
const DEVICE_CONTROL_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'device_control',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '设备控制',
    },
    {
      type: 'textarea',
      field: 'description',
      label: '描述',
      placeholder: '请输入节点描述',
      props: { rows: 2 },
    },
    {
      type: 'input',
      field: 'deviceId',
      label: '设备ID',
      required: true,
      placeholder: '设备ID，支持 ${变量}',
    },
    {
      type: 'input',
      field: 'command',
      label: '控制指令',
      required: true,
      placeholder: '如: start, stop, restart',
    },
    {
      type: 'json',
      field: 'parameters',
      label: '指令参数',
      placeholder: '{"param1": "value1"}',
      defaultValue: {},
    },
  ],
}

/** 数据采集节点属性 */
const DEVICE_DATA_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'device_data',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '数据采集',
    },
    {
      type: 'textarea',
      field: 'description',
      label: '描述',
      placeholder: '请输入节点描述',
      props: { rows: 2 },
    },
    {
      type: 'input',
      field: 'deviceId',
      label: '设备ID',
      required: true,
      placeholder: '设备ID，支持 ${变量}',
    },
    {
      type: 'json',
      field: 'dataPoints',
      label: '数据点',
      placeholder: '["temperature", "humidity"]',
      description: '要采集的数据点列表',
      defaultValue: [],
    },
    {
      type: 'input',
      field: 'outputVariable',
      label: '输出变量名',
      placeholder: 'collectedData',
      defaultValue: 'collectedData',
    },
  ],
}

/** 状态检测节点属性 */
const DEVICE_STATUS_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'device_status',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '状态检测',
    },
    {
      type: 'textarea',
      field: 'description',
      label: '描述',
      placeholder: '请输入节点描述',
      props: { rows: 2 },
    },
    {
      type: 'input',
      field: 'deviceId',
      label: '设备ID',
      required: true,
      placeholder: '设备ID，支持 ${变量}',
    },
    {
      type: 'select',
      field: 'expectedStatus',
      label: '期望状态',
      required: true,
      options: [
        { label: '在线', value: 'online' },
        { label: '离线', value: 'offline' },
        { label: '运行中', value: 'running' },
        { label: '停止', value: 'stopped' },
        { label: '故障', value: 'fault' },
      ],
      defaultValue: 'online',
    },
  ],
}

// ========== 报警节点属性Schema ==========

/** 触发报警节点属性 */
const ALARM_TRIGGER_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'alarm_trigger',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '触发报警',
    },
    {
      type: 'textarea',
      field: 'description',
      label: '描述',
      placeholder: '请输入节点描述',
      props: { rows: 2 },
    },
    {
      type: 'select',
      field: 'alarmType',
      label: '报警类型',
      required: true,
      options: [
        { label: '设备报警', value: 'device' },
        { label: '系统报警', value: 'system' },
        { label: '业务报警', value: 'business' },
      ],
      defaultValue: 'device',
    },
    {
      type: 'select',
      field: 'alarmLevel',
      label: '报警级别',
      required: true,
      options: ALARM_LEVEL_OPTIONS,
      defaultValue: 'warning',
    },
    {
      type: 'input',
      field: 'title',
      label: '报警标题',
      required: true,
      placeholder: '报警标题，支持 ${变量}',
    },
    {
      type: 'textarea',
      field: 'content',
      label: '报警内容',
      required: true,
      placeholder: '报警详细内容，支持 ${变量}',
      props: { rows: 3 },
    },
    {
      type: 'input',
      field: 'deviceId',
      label: '关联设备ID',
      placeholder: '可选，关联的设备ID',
    },
  ],
}

/** 报警检测节点属性 */
const ALARM_CHECK_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'alarm_check',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '报警检测',
    },
    {
      type: 'textarea',
      field: 'description',
      label: '描述',
      placeholder: '请输入节点描述',
      props: { rows: 2 },
    },
    {
      type: 'select',
      field: 'checkType',
      label: '检测类型',
      required: true,
      options: [
        { label: '阈值检测', value: 'threshold' },
        { label: '范围检测', value: 'range' },
        { label: '变化率检测', value: 'rate' },
      ],
      defaultValue: 'threshold',
    },
    {
      type: 'input',
      field: 'valuePath',
      label: '值路径',
      required: true,
      placeholder: '如: deviceData.temperature',
      description: '要检测的值在上下文中的路径',
    },
    {
      type: 'number',
      field: 'threshold',
      label: '阈值',
      placeholder: '报警阈值',
      showWhen: { field: 'checkType', value: 'threshold' },
    },
    {
      type: 'number',
      field: 'minValue',
      label: '最小值',
      placeholder: '范围最小值',
      showWhen: { field: 'checkType', value: 'range' },
    },
    {
      type: 'number',
      field: 'maxValue',
      label: '最大值',
      placeholder: '范围最大值',
      showWhen: { field: 'checkType', value: 'range' },
    },
  ],
}

/** 清除报警节点属性 */
const ALARM_CLEAR_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'alarm_clear',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '清除报警',
    },
    {
      type: 'textarea',
      field: 'description',
      label: '描述',
      placeholder: '请输入节点描述',
      props: { rows: 2 },
    },
    {
      type: 'input',
      field: 'alarmId',
      label: '报警ID',
      placeholder: '报警ID，支持 ${变量}',
      description: '留空则按设备ID清除',
    },
    {
      type: 'input',
      field: 'deviceId',
      label: '设备ID',
      placeholder: '设备ID，支持 ${变量}',
      description: '清除该设备的所有报警',
    },
  ],
}

// ========== 通知节点属性Schema ==========

/** 邮件发送节点属性 */
const EMAIL_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'email',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '邮件发送',
    },
    {
      type: 'textarea',
      field: 'description',
      label: '描述',
      placeholder: '请输入节点描述',
      props: { rows: 2 },
    },
    {
      type: 'input',
      field: 'to',
      label: '收件人',
      required: true,
      placeholder: '邮箱地址，多个用逗号分隔',
    },
    {
      type: 'input',
      field: 'cc',
      label: '抄送',
      placeholder: '抄送邮箱，多个用逗号分隔',
    },
    {
      type: 'input',
      field: 'subject',
      label: '邮件主题',
      required: true,
      placeholder: '邮件主题，支持 ${变量}',
    },
    {
      type: 'textarea',
      field: 'body',
      label: '邮件内容',
      required: true,
      placeholder: '邮件正文，支持 ${变量}',
      props: { rows: 5 },
    },
    {
      type: 'input',
      field: 'templateId',
      label: '邮件模板ID',
      placeholder: '可选，使用预定义模板',
    },
  ],
}

/** 短信发送节点属性 */
const SMS_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'sms',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '短信发送',
    },
    {
      type: 'textarea',
      field: 'description',
      label: '描述',
      placeholder: '请输入节点描述',
      props: { rows: 2 },
    },
    {
      type: 'input',
      field: 'phone',
      label: '手机号',
      required: true,
      placeholder: '手机号，多个用逗号分隔',
    },
    {
      type: 'textarea',
      field: 'content',
      label: '短信内容',
      required: true,
      placeholder: '短信内容，支持 ${变量}',
      props: { rows: 3 },
    },
    {
      type: 'input',
      field: 'templateId',
      label: '短信模板ID',
      placeholder: '可选，使用预定义模板',
    },
  ],
}

/** Webhook节点属性 */
const WEBHOOK_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'webhook',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: 'Webhook调用',
    },
    {
      type: 'textarea',
      field: 'description',
      label: '描述',
      placeholder: '请输入节点描述',
      props: { rows: 2 },
    },
    {
      type: 'input',
      field: 'url',
      label: 'Webhook URL',
      required: true,
      placeholder: 'https://example.com/webhook',
    },
    {
      type: 'select',
      field: 'method',
      label: '请求方法',
      options: [
        { label: 'POST', value: 'POST' },
        { label: 'GET', value: 'GET' },
      ],
      defaultValue: 'POST',
    },
    {
      type: 'json',
      field: 'headers',
      label: '请求头',
      placeholder: '{"Authorization": "Bearer xxx"}',
      defaultValue: {},
    },
    {
      type: 'json',
      field: 'payload',
      label: '请求数据',
      placeholder: '{"key": "${value}"}',
      defaultValue: {},
    },
  ],
}

// ========== 补充缺失节点属性Schema ==========

/** 定时器节点属性 */
const TIMER_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'timer',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '定时器',
    },
    {
      type: 'select',
      field: 'timerType',
      label: '定时类型',
      required: true,
      options: [
        { label: 'Cron表达式', value: 'cron' },
        { label: '时间间隔', value: 'interval' },
        { label: '一次性', value: 'once' },
      ],
      defaultValue: 'cron',
    },
    {
      type: 'input',
      field: 'cronExpression',
      label: 'Cron表达式',
      placeholder: '* * * * *',
      description: '分 时 日 月 周',
      showWhen: { field: 'timerType', value: 'cron' },
    },
    {
      type: 'number',
      field: 'interval',
      label: '间隔时间',
      defaultValue: 60,
      props: { min: 1 },
      showWhen: { field: 'timerType', value: 'interval' },
    },
    {
      type: 'select',
      field: 'unit',
      label: '时间单位',
      options: TIME_UNIT_OPTIONS,
      defaultValue: 'seconds',
      showWhen: { field: 'timerType', value: 'interval' },
    },
    {
      type: 'datepicker',
      field: 'executeTime',
      label: '执行时间',
      placeholder: '选择执行时间',
      showWhen: { field: 'timerType', value: 'once' },
    },
  ],
}

/** 转换节点属性 */
const TRANSFORM_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'transform',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '数据转换',
    },
    {
      type: 'select',
      field: 'transformType',
      label: '转换类型',
      required: true,
      options: [
        { label: 'JavaScript脚本', value: 'script' },
        { label: '字段映射', value: 'mapping' },
        { label: '模板渲染', value: 'template' },
      ],
      defaultValue: 'script',
    },
    {
      type: 'code',
      field: 'script',
      label: '转换脚本',
      placeholder: 'return data.map(item => item.value)',
      props: { language: 'javascript', height: 200 },
      showWhen: { field: 'transformType', value: 'script' },
    },
    {
      type: 'json',
      field: 'mapping',
      label: '字段映射',
      placeholder: '{"targetField": "sourceField"}',
      showWhen: { field: 'transformType', value: 'mapping' },
    },
    {
      type: 'textarea',
      field: 'template',
      label: '模板内容',
      placeholder: 'Hello ${name}!',
      props: { rows: 5 },
      showWhen: { field: 'transformType', value: 'template' },
    },
    {
      type: 'input',
      field: 'outputVariable',
      label: '输出变量名',
      defaultValue: 'transformResult',
    },
  ],
}

/** 过滤节点属性 */
const FILTER_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'filter',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '数据过滤',
    },
    {
      type: 'select',
      field: 'filterMode',
      label: '过滤模式',
      required: true,
      options: [
        { label: '简单条件', value: 'condition' },
        { label: '脚本过滤', value: 'script' },
      ],
      defaultValue: 'condition',
    },
    {
      type: 'input',
      field: 'field',
      label: '过滤字段',
      placeholder: 'data.value',
      showWhen: { field: 'filterMode', value: 'condition' },
    },
    {
      type: 'select',
      field: 'operator',
      label: '操作符',
      options: COMPARE_OPERATOR_OPTIONS,
      defaultValue: 'eq',
      showWhen: { field: 'filterMode', value: 'condition' },
    },
    {
      type: 'input',
      field: 'value',
      label: '比较值',
      placeholder: '比较值',
      showWhen: { field: 'filterMode', value: 'condition' },
    },
    {
      type: 'code',
      field: 'expression',
      label: '过滤表达式',
      placeholder: 'return item.value > 10',
      props: { language: 'javascript', height: 100 },
      showWhen: { field: 'filterMode', value: 'script' },
    },
    {
      type: 'select',
      field: 'action',
      label: '不匹配动作',
      options: [
        { label: '丢弃', value: 'drop' },
        { label: '保留但标记', value: 'mark' },
      ],
      defaultValue: 'drop',
    },
  ],
}

/** 流程调用节点属性 (Process) */
const PROCESS_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'process',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '子流程',
    },
    {
      type: 'input',
      field: 'processId',
      label: '流程ID',
      required: true,
      placeholder: '请输入子流程ID',
    },
    {
      type: 'switch',
      field: 'sync',
      label: '同步等待',
      defaultValue: true,
    },
    {
      type: 'json',
      field: 'inputParams',
      label: '输入参数',
      placeholder: '{"param1": "value1"}',
      defaultValue: {},
    },
    {
      type: 'input',
      field: 'outputVariable',
      label: '输出变量名',
      defaultValue: 'processResult',
      showWhen: { field: 'sync', value: true },
    },
  ],
}

/** 合并节点属性 */
const MERGE_NODE_SCHEMA: NodePropertySchema = {
  nodeType: 'merge',
  fields: [
    {
      type: 'input',
      field: 'name',
      label: '节点名称',
      required: true,
      placeholder: '请输入节点名称',
      defaultValue: '合并分支',
    },
    {
      type: 'select',
      field: 'mergeStrategy',
      label: '合并策略',
      required: true,
      options: [
        { label: '等待所有 (And)', value: 'all' },
        { label: '任一到达 (Or)', value: 'any' },
      ],
      defaultValue: 'all',
    },
    {
      type: 'number',
      field: 'timeout',
      label: '超时时间(秒)',
      defaultValue: 60,
      props: { min: 0 },
    },
  ],
}

// ========== Schema注册表 ==========

/** 所有节点属性Schema */
export const NODE_PROPERTY_SCHEMAS: Record<string, NodePropertySchema> = {
  // 基础节点
  start: START_NODE_SCHEMA,
  end: END_NODE_SCHEMA,
  // 控制节点
  condition: CONDITION_NODE_SCHEMA,
  loop: LOOP_NODE_SCHEMA,
  parallel: PARALLEL_NODE_SCHEMA,
  delay: DELAY_NODE_SCHEMA,
  timer: TIMER_NODE_SCHEMA,
  process: PROCESS_NODE_SCHEMA,
  merge: MERGE_NODE_SCHEMA,
  // 数据处理
  transform: TRANSFORM_NODE_SCHEMA,
  filter: FILTER_NODE_SCHEMA,
  // 集成节点
  api: API_NODE_SCHEMA,
  database: DATABASE_NODE_SCHEMA,
  script: SCRIPT_NODE_SCHEMA,
  // 设备节点
  device_query: DEVICE_QUERY_NODE_SCHEMA,
  device_control: DEVICE_CONTROL_NODE_SCHEMA,
  device_data: DEVICE_DATA_NODE_SCHEMA,
  device_status: DEVICE_STATUS_NODE_SCHEMA,
  // 报警节点
  alarm: ALARM_NODE_SCHEMA,
  alarm_trigger: ALARM_TRIGGER_NODE_SCHEMA,
  alarm_check: ALARM_CHECK_NODE_SCHEMA,
  alarm_clear: ALARM_CLEAR_NODE_SCHEMA,
  // 通知节点
  notification: NOTIFICATION_NODE_SCHEMA,
  email: EMAIL_NODE_SCHEMA,
  sms: SMS_NODE_SCHEMA,
  webhook: WEBHOOK_NODE_SCHEMA,
}

// ========== 工具函数 ==========

/**
 * 获取节点属性Schema
 * @param nodeType 节点类型
 * @returns 属性Schema，如果不存在则返回默认Schema
 */
export function getNodePropertySchema(nodeType: string): NodePropertySchema {
  return NODE_PROPERTY_SCHEMAS[nodeType] || {
    nodeType,
    fields: [
      {
        type: 'input',
        field: 'name',
        label: '节点名称',
        required: true,
        placeholder: '请输入节点名称',
      },
      {
        type: 'textarea',
        field: 'description',
        label: '描述',
        placeholder: '请输入节点描述',
        props: { rows: 3 },
      },
    ],
  }
}

/**
 * 获取节点属性默认值
 * @param nodeType 节点类型
 * @returns 默认属性值对象
 */
export function getNodeDefaultProperties(nodeType: string): Record<string, any> {
  const schema = getNodePropertySchema(nodeType)
  const defaults: Record<string, any> = {}
  
  schema.fields.forEach(field => {
    if (field.defaultValue !== undefined) {
      defaults[field.field] = field.defaultValue
    }
  })
  
  return defaults
}

/**
 * 验证节点属性
 * @param nodeType 节点类型
 * @param properties 属性值
 * @returns 验证结果
 */
export function validateNodeProperties(
  nodeType: string, 
  properties: Record<string, any>
): { valid: boolean; errors: string[] } {
  const schema = getNodePropertySchema(nodeType)
  const errors: string[] = []
  
  schema.fields.forEach(field => {
    const value = properties[field.field]
    
    // 检查必填
    if (field.required && (value === undefined || value === null || value === '')) {
      errors.push(`${field.label} 不能为空`)
    }
    
    // 检查自定义规则
    if (field.rules) {
      field.rules.forEach(rule => {
        if (rule.required && !value) {
          errors.push(rule.message || `${field.label} 不能为空`)
        }
        if (rule.min !== undefined && typeof value === 'number' && value < rule.min) {
          errors.push(rule.message || `${field.label} 不能小于 ${rule.min}`)
        }
        if (rule.max !== undefined && typeof value === 'number' && value > rule.max) {
          errors.push(rule.message || `${field.label} 不能大于 ${rule.max}`)
        }
        if (rule.pattern && typeof value === 'string' && !new RegExp(rule.pattern).test(value)) {
          errors.push(rule.message || `${field.label} 格式不正确`)
        }
        if (rule.validator && typeof rule.validator === 'function') {
          const result = rule.validator(value)
          if (result !== true) {
            errors.push(typeof result === 'string' ? result : `${field.label} 验证失败`)
          }
        }
      })
    }
  })
  
  return {
    valid: errors.length === 0,
    errors,
  }
}

/**
 * 检查字段是否应该显示
 * @param field 字段定义
 * @param properties 当前属性值
 * @returns 是否显示
 */
export function shouldShowField(
  field: NodePropertyField, 
  properties: Record<string, any>
): boolean {
  if (field.hidden) return false
  
  if (field.showWhen) {
    const { field: dependField, value: dependValue } = field.showWhen
    const currentValue = properties[dependField]
    
    if (Array.isArray(dependValue)) {
      return dependValue.includes(currentValue)
    }
    return currentValue === dependValue
  }
  
  return true
}

export default NODE_PROPERTY_SCHEMAS
