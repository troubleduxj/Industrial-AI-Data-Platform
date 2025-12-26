/**
 * 节点类型导出文件
 * Node types export file
 */

// 导入所有节点类型组件
import StartNode from './StartNode.vue'
import EndNode from './EndNode.vue'
import ProcessNode from './ProcessNode.vue'
import DecisionNode from './DecisionNode.vue'
import ActionNode from './ActionNode.vue'
import BaseNode from './BaseNode.vue'

// 节点类型映射
export const NODE_TYPE_COMPONENTS = {
  start: StartNode,
  end: EndNode,
  process: ProcessNode,
  decision: DecisionNode,
  action: ActionNode,
  base: BaseNode,
  api: ApiNode,
  database: DatabaseNode,
  timer: TimerNode,
  email: EmailNode,
  file: FileNode,
  condition: ConditionNode,
  loop: LoopNode,
}

// 节点类型配置
export const NODE_TYPE_CONFIGS = {
  start: {
    name: '开始节点',
    description: '工作流的起始点',
    category: 'control',
    icon: 'play-circle',
    color: '#52c41a',
    maxInputs: 0,
    maxOutputs: 1,
    defaultSize: { width: 120, height: 60 },
    connectionPoints: {
      outputs: [{ id: 'output', label: '输出', position: 'right' }],
    },
  },
  end: {
    name: '结束节点',
    description: '工作流的终点',
    category: 'control',
    icon: 'stop-circle',
    color: '#ff4d4f',
    maxInputs: 1,
    maxOutputs: 0,
    defaultSize: { width: 120, height: 60 },
    connectionPoints: {
      inputs: [{ id: 'input', label: '输入', position: 'left' }],
    },
  },
  process: {
    name: '处理节点',
    description: '执行数据处理操作',
    category: 'processing',
    icon: 'cog',
    color: '#1890ff',
    maxInputs: 1,
    maxOutputs: 2,
    defaultSize: { width: 140, height: 80 },
    connectionPoints: {
      inputs: [{ id: 'input', label: '输入', position: 'left' }],
      outputs: [
        { id: 'success', label: '成功', position: 'right' },
        { id: 'error', label: '错误', position: 'bottom' },
      ],
    },
  },
  decision: {
    name: '决策节点',
    description: '根据条件进行分支判断',
    category: 'logic',
    icon: 'question-circle',
    color: '#fa8c16',
    maxInputs: 1,
    maxOutputs: 2,
    defaultSize: { width: 120, height: 80 },
    connectionPoints: {
      inputs: [{ id: 'input', label: '输入', position: 'left' }],
      outputs: [
        { id: 'true', label: '是', position: 'right' },
        { id: 'false', label: '否', position: 'bottom' },
      ],
    },
  },
  action: {
    name: '动作节点',
    description: '执行具体的操作动作',
    category: 'action',
    icon: 'thunderbolt',
    color: '#722ed1',
    maxInputs: 1,
    maxOutputs: 2,
    defaultSize: { width: 140, height: 80 },
    connectionPoints: {
      inputs: [{ id: 'input', label: '输入', position: 'left' }],
      outputs: [
        { id: 'success', label: '成功', position: 'right' },
        { id: 'error', label: '错误', position: 'bottom' },
      ],
    },
  },
  base: {
    name: '基础节点',
    description: '通用基础节点',
    category: 'basic',
    icon: 'node-index',
    color: '#8c8c8c',
    maxInputs: 1,
    maxOutputs: 1,
    defaultSize: { width: 120, height: 60 },
    connectionPoints: {
      inputs: [{ id: 'input', label: '输入', position: 'left' }],
      outputs: [{ id: 'output', label: '输出', position: 'right' }],
    },
  },
  api: {
    name: 'API节点',
    description: 'API接口调用节点',
    category: 'integration',
    icon: 'api',
    color: '#13c2c2',
    maxInputs: 2,
    maxOutputs: 2,
    defaultSize: { width: 180, height: 140 },
    connectionPoints: {
      inputs: [
        { id: 'input', label: '输入', position: 'left' },
        { id: 'config', label: '配置', position: 'top' },
      ],
      outputs: [
        { id: 'success', label: '成功', position: 'right' },
        { id: 'error', label: '错误', position: 'bottom' },
      ],
    },
  },
  database: {
    name: '数据库节点',
    description: '数据库操作节点',
    category: 'integration',
    icon: 'database',
    color: '#2f54eb',
    maxInputs: 2,
    maxOutputs: 2,
    defaultSize: { width: 180, height: 140 },
    connectionPoints: {
      inputs: [
        { id: 'input', label: '输入', position: 'left' },
        { id: 'query', label: '查询', position: 'top' },
      ],
      outputs: [
        { id: 'success', label: '成功', position: 'right' },
        { id: 'error', label: '错误', position: 'bottom' },
      ],
    },
  },
  timer: {
    name: '定时器节点',
    description: '定时触发节点',
    category: 'basic',
    icon: 'clock-circle',
    color: '#fa541c',
    maxInputs: 1,
    maxOutputs: 2,
    defaultSize: { width: 160, height: 130 },
    connectionPoints: {
      inputs: [{ id: 'input', label: '输入', position: 'left' }],
      outputs: [
        { id: 'trigger', label: '触发', position: 'right' },
        { id: 'timeout', label: '超时', position: 'bottom' },
      ],
    },
  },
  email: {
    name: '邮件节点',
    description: '邮件发送节点',
    category: 'integration',
    icon: 'mail',
    color: '#f759ab',
    maxInputs: 2,
    maxOutputs: 2,
    defaultSize: { width: 170, height: 130 },
    connectionPoints: {
      inputs: [
        { id: 'input', label: '输入', position: 'left' },
        { id: 'content', label: '内容', position: 'top' },
      ],
      outputs: [
        { id: 'success', label: '成功', position: 'right' },
        { id: 'error', label: '错误', position: 'bottom' },
      ],
    },
  },
  file: {
    name: '文件节点',
    description: '文件处理节点',
    category: 'basic',
    icon: 'file',
    color: '#eb2f96',
    maxInputs: 2,
    maxOutputs: 2,
    defaultSize: { width: 180, height: 140 },
    connectionPoints: {
      inputs: [
        { id: 'input', label: '输入', position: 'left' },
        { id: 'path', label: '路径', position: 'top' },
      ],
      outputs: [
        { id: 'success', label: '成功', position: 'right' },
        { id: 'error', label: '错误', position: 'bottom' },
      ],
    },
  },
  condition: {
    name: '条件节点',
    description: '条件判断节点',
    category: 'logic',
    icon: 'branches',
    color: '#fa8c16',
    maxInputs: 2,
    maxOutputs: 2,
    defaultSize: { width: 200, height: 160 },
    connectionPoints: {
      inputs: [
        { id: 'input', label: '输入', position: 'left' },
        { id: 'condition', label: '条件', position: 'top' },
      ],
      outputs: [
        { id: 'true', label: '真', position: 'right' },
        { id: 'false', label: '假', position: 'bottom' },
      ],
    },
  },
  loop: {
    name: '循环节点',
    description: '循环控制节点',
    category: 'logic',
    icon: 'reload',
    color: '#722ed1',
    maxInputs: 2,
    maxOutputs: 3,
    defaultSize: { width: 220, height: 180 },
    connectionPoints: {
      inputs: [
        { id: 'input', label: '输入', position: 'left' },
        { id: 'condition', label: '条件', position: 'top' },
      ],
      outputs: [
        { id: 'loop', label: '循环', position: 'right' },
        { id: 'exit', label: '退出', position: 'bottom' },
        { id: 'error', label: '错误', position: 'bottom-right' },
      ],
    },
  },
}

// 节点类别配置
export const NODE_CATEGORIES = {
  control: {
    name: '控制节点',
    description: '控制工作流执行流程',
    icon: 'control',
    color: '#52c41a',
  },
  processing: {
    name: '处理节点',
    description: '数据处理和转换',
    icon: 'processor',
    color: '#1890ff',
  },
  logic: {
    name: '逻辑节点',
    description: '条件判断和逻辑控制',
    icon: 'branches',
    color: '#fa8c16',
  },
  action: {
    name: '动作节点',
    description: '执行具体操作',
    icon: 'rocket',
    color: '#722ed1',
  },
  integration: {
    name: '集成节点',
    description: '外部系统集成',
    icon: 'api',
    color: '#13c2c2',
  },
  basic: {
    name: '基础节点',
    description: '基础通用节点',
    icon: 'appstore',
    color: '#8c8c8c',
  },
}

// 获取节点类型配置
export function getNodeTypeConfig(type) {
  return NODE_TYPE_CONFIGS[type] || NODE_TYPE_CONFIGS.base
}

// 获取节点类型组件
export function getNodeTypeComponent(type) {
  return NODE_TYPE_COMPONENTS[type] || NODE_TYPE_COMPONENTS.base
}

// 获取节点类别配置
export function getNodeCategoryConfig(category) {
  return NODE_CATEGORIES[category] || NODE_CATEGORIES.basic
}

// 获取所有节点类型
export function getAllNodeTypes() {
  return Object.keys(NODE_TYPE_CONFIGS)
}

// 获取所有节点类别
export function getAllNodeCategories() {
  return Object.keys(NODE_CATEGORIES)
}

// 根据类别获取节点类型
export function getNodeTypesByCategory(category) {
  return Object.entries(NODE_TYPE_CONFIGS)
    .filter(([, config]) => config.category === category)
    .map(([type]) => type)
}

// 验证节点类型
export function isValidNodeType(type) {
  return type in NODE_TYPE_CONFIGS
}

// 创建默认节点数据
export function createDefaultNodeData(type, position = { x: 0, y: 0 }) {
  const config = getNodeTypeConfig(type)

  return {
    id: `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    type,
    position,
    size: config.defaultSize,
    data: {
      label: config.name,
      description: config.description,
      properties: {},
    },
    style: {
      backgroundColor: config.color,
      borderColor: config.color,
      color: '#ffffff',
    },
    connectionPoints: config.connectionPoints,
  }
}

// 导出所有组件
export { StartNode, EndNode, ProcessNode, DecisionNode, ActionNode, BaseNode }

// 默认导出
export default {
  components: NODE_TYPE_COMPONENTS,
  configs: NODE_TYPE_CONFIGS,
  categories: NODE_CATEGORIES,
  getNodeTypeConfig,
  getNodeTypeComponent,
  getNodeCategoryConfig,
  getAllNodeTypes,
  getAllNodeCategories,
  getNodeTypesByCategory,
  isValidNodeType,
  createDefaultNodeData,
}
