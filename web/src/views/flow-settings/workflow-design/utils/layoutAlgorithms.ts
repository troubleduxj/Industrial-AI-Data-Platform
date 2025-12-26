/**
 * 布局算法工具
 * Layout algorithms utilities
 */

// ========== 类型定义 ==========

/** 布局算法类型 */
export type LayoutType = 'hierarchical' | 'forceDirected' | 'circular' | 'grid' | 'tree' | 'layered' | 'organic'

/** 布局方向 */
export type LayoutDirection = 'TB' | 'BT' | 'LR' | 'RL'

/** 对齐方式 */
type AlignmentType = 'start' | 'center' | 'end'

/** 节点（临时类型） */
interface WorkflowNode {
  id: string
  x?: number
  y?: number
  [key: string]: any
}

/** 连接（临时类型） */
interface Connection {
  fromNodeId: string
  toNodeId: string
  [key: string]: any
}

/** 布局配置 */
interface LayoutConfig {
  nodeSpacing?: number
  levelSpacing?: number
  padding?: number
  direction?: LayoutDirection
  alignment?: AlignmentType
  iterations?: number
  springLength?: number
  springStrength?: number
  repulsionStrength?: number
  damping?: number
  centerX?: number
  centerY?: number
}

/** 力导向节点（扩展） */
interface ForceNode extends WorkflowNode {
  vx: number
  vy: number
  fx: number
  fy: number
}

/** 图结构 */
interface Graph {
  nodes: Map<string, WorkflowNode>
  edges: Map<string, string[]>
  inDegree: Map<string, number>
  outDegree: Map<string, number>
}

/** 树结构 */
interface Tree {
  root: string | undefined
  children: Map<string, string[]>
  parents: Map<string, string>
}

/** 自动布局结果 */
interface AutoLayoutResult {
  nodes: WorkflowNode[]
  algorithm: LayoutType
  reason: string
  stats: {
    nodeCount: number
    connectionCount: number
    density: number
  }
}

// ========== 常量定义 ==========

/**
 * 布局算法类型
 */
export const LAYOUT_TYPES = {
  HIERARCHICAL: 'hierarchical' as const,
  FORCE_DIRECTED: 'forceDirected' as const,
  CIRCULAR: 'circular' as const,
  GRID: 'grid' as const,
  TREE: 'tree' as const,
  LAYERED: 'layered' as const,
  ORGANIC: 'organic' as const,
}

/**
 * 布局方向
 */
export const LAYOUT_DIRECTIONS = {
  TOP_TO_BOTTOM: 'TB' as const,
  BOTTOM_TO_TOP: 'BT' as const,
  LEFT_TO_RIGHT: 'LR' as const,
  RIGHT_TO_LEFT: 'RL' as const,
}

/**
 * 默认布局配置
 */
const DEFAULT_LAYOUT_CONFIG: Required<Omit<LayoutConfig, 'centerX' | 'centerY' | 'repulsionStrength'>> = {
  nodeSpacing: 100,
  levelSpacing: 150,
  padding: 50,
  direction: LAYOUT_DIRECTIONS.TOP_TO_BOTTOM,
  alignment: 'center',
  iterations: 100,
  springLength: 100,
  springStrength: 0.1,
  damping: 0.9,
}

// ========== 主要布局算法 ==========

/**
 * 层次布局算法
 * @param nodes - 节点数组
 * @param connections - 连接数组
 * @param config - 布局配置
 * @returns 更新位置后的节点数组
 */
export function hierarchicalLayout(
  nodes: WorkflowNode[],
  connections: Connection[],
  config: LayoutConfig = {}
): WorkflowNode[] {
  const cfg = { ...DEFAULT_LAYOUT_CONFIG, ...config }
  const nodeMap = new Map(nodes.map((node) => [node.id, { ...node }]))

  // 构建图结构
  const graph = buildGraph(nodes, connections)

  // 查找根节点（入度为0的节点）
  const rootNodes = findRootNodes(graph)

  if (rootNodes.length === 0 && nodes.length > 0) {
    // 如果没有根节点，选择第一个节点作为根
    rootNodes.push(nodes[0]?.id)
  }

  // 计算层级
  const levels = calculateLevels(graph, rootNodes)

  // 布局节点
  layoutNodesByLevels(levels, nodeMap, cfg)

  return Array.from(nodeMap.values())
}

/**
 * 力导向布局算法
 * @param nodes - 节点数组
 * @param connections - 连接数组
 * @param config - 布局配置
 * @returns 更新位置后的节点数组
 */
export function forceDirectedLayout(
  nodes: WorkflowNode[],
  connections: Connection[],
  config: LayoutConfig = {}
): WorkflowNode[] {
  const cfg = { ...DEFAULT_LAYOUT_CONFIG, ...config }
  const nodeMap = new Map<string, ForceNode>(
    nodes.map((node) => [
      node.id,
      {
        ...node,
        vx: 0,
        vy: 0,
        fx: node.x || Math.random() * 800,
        fy: node.y || Math.random() * 600,
      },
    ])
  )

  // 力导向模拟
  for (let i = 0; i < cfg.iterations; i++) {
    // 计算斥力
    calculateRepulsiveForces(nodeMap, cfg)

    // 计算引力
    calculateAttractiveForces(nodeMap, connections, cfg)

    // 更新位置
    updateNodePositions(nodeMap, cfg)
  }

  // 移除临时属性
  const result = Array.from(nodeMap.values()).map((node) => {
    const { vx, vy, fx, fy, ...cleanNode } = node
    return {
      ...cleanNode,
      x: fx,
      y: fy,
    }
  })

  return result
}

/**
 * 圆形布局算法
 * @param nodes - 节点数组
 * @param connections - 连接数组
 * @param config - 布局配置
 * @returns 更新位置后的节点数组
 */
export function circularLayout(
  nodes: WorkflowNode[],
  connections: Connection[],
  config: LayoutConfig = {}
): WorkflowNode[] {
  const cfg = { ...DEFAULT_LAYOUT_CONFIG, ...config }
  const nodeCount = nodes.length

  if (nodeCount === 0) return nodes

  const radius = Math.max(200, nodeCount * 30)
  const centerX = config.centerX || 400
  const centerY = config.centerY || 300
  const angleStep = (2 * Math.PI) / nodeCount

  return nodes.map((node, index) => {
    const angle = index * angleStep
    return {
      ...node,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    }
  })
}

/**
 * 网格布局算法
 * @param nodes - 节点数组
 * @param connections - 连接数组
 * @param config - 布局配置
 * @returns 更新位置后的节点数组
 */
export function gridLayout(
  nodes: WorkflowNode[],
  connections: Connection[],
  config: LayoutConfig = {}
): WorkflowNode[] {
  const cfg = { ...DEFAULT_LAYOUT_CONFIG, ...config }
  const nodeCount = nodes.length

  if (nodeCount === 0) return nodes

  const cols = Math.ceil(Math.sqrt(nodeCount))
  const rows = Math.ceil(nodeCount / cols)

  const cellWidth = cfg.nodeSpacing + 120 // 节点宽度 + 间距
  const cellHeight = cfg.levelSpacing + 80 // 节点高度 + 间距

  const startX = cfg.padding
  const startY = cfg.padding

  return nodes.map((node, index) => {
    const row = Math.floor(index / cols)
    const col = index % cols

    return {
      ...node,
      x: startX + col * cellWidth,
      y: startY + row * cellHeight,
    }
  })
}

/**
 * 树形布局算法
 * @param nodes - 节点数组
 * @param connections - 连接数组
 * @param config - 布局配置
 * @returns 更新位置后的节点数组
 */
export function treeLayout(
  nodes: WorkflowNode[],
  connections: Connection[],
  config: LayoutConfig = {}
): WorkflowNode[] {
  const cfg = { ...DEFAULT_LAYOUT_CONFIG, ...config }
  const nodeMap = new Map(nodes.map((node) => [node.id, { ...node }]))

  // 构建树结构
  const tree = buildTree(nodes, connections)

  if (!tree.root) {
    return gridLayout(nodes, connections, config)
  }

  // 计算子树大小
  calculateSubtreeSizes(tree.root, tree.children)

  // 布局树节点
  layoutTreeNodes(tree.root, tree.children, nodeMap, cfg)

  return Array.from(nodeMap.values())
}

/**
 * 分层布局算法
 * @param nodes - 节点数组
 * @param connections - 连接数组
 * @param config - 布局配置
 * @returns 更新位置后的节点数组
 */
export function layeredLayout(
  nodes: WorkflowNode[],
  connections: Connection[],
  config: LayoutConfig = {}
): WorkflowNode[] {
  const cfg = { ...DEFAULT_LAYOUT_CONFIG, ...config }
  const nodeMap = new Map(nodes.map((node) => [node.id, { ...node }]))

  // 构建图并进行拓扑排序
  const graph = buildGraph(nodes, connections)
  const layers = topologicalSort(graph)

  // 减少交叉
  reduceCrossings(layers, connections)

  // 分配坐标
  assignLayerCoordinates(layers, nodeMap, cfg)

  return Array.from(nodeMap.values())
}

/**
 * 有机布局算法（基于力导向的改进版本）
 * @param nodes - 节点数组
 * @param connections - 连接数组
 * @param config - 布局配置
 * @returns 更新位置后的节点数组
 */
export function organicLayout(
  nodes: WorkflowNode[],
  connections: Connection[],
  config: LayoutConfig = {}
): WorkflowNode[] {
  const cfg: LayoutConfig = {
    ...DEFAULT_LAYOUT_CONFIG,
    ...config,
    springStrength: 0.05,
    repulsionStrength: 1000,
    iterations: 200,
  }

  let result = forceDirectedLayout(nodes, connections, cfg)

  // 应用额外的有机化处理
  result = applyOrganicAdjustments(result, connections, cfg)

  return result
}

// ========== 辅助函数 ==========

/**
 * 构建图结构
 */
function buildGraph(nodes: WorkflowNode[], connections: Connection[]): Graph {
  const graph: Graph = {
    nodes: new Map(),
    edges: new Map(),
    inDegree: new Map(),
    outDegree: new Map(),
  }

  // 初始化节点
  nodes.forEach((node) => {
    graph.nodes.set(node.id, node)
    graph.edges.set(node.id, [])
    graph.inDegree.set(node.id, 0)
    graph.outDegree.set(node.id, 0)
  })

  // 添加边
  connections.forEach((conn) => {
    if (graph.edges.has(conn.fromNodeId)) {
      graph.edges.get(conn.fromNodeId)!.push(conn.toNodeId)
      graph.outDegree.set(conn.fromNodeId, graph.outDegree.get(conn.fromNodeId)! + 1)
      graph.inDegree.set(conn.toNodeId, graph.inDegree.get(conn.toNodeId)! + 1)
    }
  })

  return graph
}

/**
 * 查找根节点
 */
function findRootNodes(graph: Graph): string[] {
  const roots: string[] = []
  graph.inDegree.forEach((degree, nodeId) => {
    if (degree === 0) {
      roots.push(nodeId)
    }
  })
  return roots
}

/**
 * 计算节点层级
 */
function calculateLevels(graph: Graph, rootNodes: string[]): string[][] {
  const levels: string[][] = []
  const visited = new Set<string>()
  const queue: Array<{ id: string; level: number }> = rootNodes.map((id) => ({ id, level: 0 }))

  while (queue.length > 0) {
    const item = queue.shift()!
    const { id, level } = item

    if (visited.has(id)) continue
    visited.add(id)

    if (!levels[level]) {
      levels[level] = []
    }
    levels[level].push(id)

    const neighbors = graph.edges.get(id) || []
    neighbors.forEach((neighborId) => {
      if (!visited.has(neighborId)) {
        queue.push({ id: neighborId, level: level + 1 })
      }
    })
  }

  return levels
}

/**
 * 按层级布局节点
 */
function layoutNodesByLevels(
  levels: string[][],
  nodeMap: Map<string, WorkflowNode>,
  config: Required<Omit<LayoutConfig, 'centerX' | 'centerY' | 'repulsionStrength'>>
): void {
  const { nodeSpacing, levelSpacing, padding, direction, alignment } = config

  levels.forEach((level, levelIndex) => {
    const levelY = padding + levelIndex * levelSpacing
    const totalWidth = (level.length - 1) * nodeSpacing
    let startX = padding

    if (alignment === 'center') {
      startX = padding + Math.max(0, (800 - totalWidth) / 2) // 假设画布宽度800
    }

    level.forEach((nodeId, nodeIndex) => {
      const node = nodeMap.get(nodeId)
      if (node) {
        if (direction === LAYOUT_DIRECTIONS.TOP_TO_BOTTOM) {
          node.x = startX + nodeIndex * nodeSpacing
          node.y = levelY
        } else if (direction === LAYOUT_DIRECTIONS.LEFT_TO_RIGHT) {
          node.x = levelY
          node.y = startX + nodeIndex * nodeSpacing
        }
        // 可以添加其他方向的支持
      }
    })
  })
}

/**
 * 计算斥力
 */
function calculateRepulsiveForces(nodeMap: Map<string, ForceNode>, config: LayoutConfig): void {
  const nodes = Array.from(nodeMap.values())
  const repulsionStrength = config.repulsionStrength || 1000

  nodes.forEach((node1) => {
    node1.vx = 0
    node1.vy = 0

    nodes.forEach((node2) => {
      if (node1.id !== node2.id) {
        const dx = node1.fx - node2.fx
        const dy = node1.fy - node2.fy
        const distance = Math.sqrt(dx * dx + dy * dy) || 1
        const force = repulsionStrength / (distance * distance)

        node1.vx += (dx / distance) * force
        node1.vy += (dy / distance) * force
      }
    })
  })
}

/**
 * 计算引力
 */
function calculateAttractiveForces(
  nodeMap: Map<string, ForceNode>,
  connections: Connection[],
  config: Required<Omit<LayoutConfig, 'centerX' | 'centerY' | 'repulsionStrength'>>
): void {
  const { springLength, springStrength } = config

  connections.forEach((conn) => {
    const node1 = nodeMap.get(conn.fromNodeId)
    const node2 = nodeMap.get(conn.toNodeId)

    if (node1 && node2) {
      const dx = node2.fx - node1.fx
      const dy = node2.fy - node1.fy
      const distance = Math.sqrt(dx * dx + dy * dy) || 1
      const force = springStrength * (distance - springLength)

      const fx = (dx / distance) * force
      const fy = (dy / distance) * force

      node1.vx += fx
      node1.vy += fy
      node2.vx -= fx
      node2.vy -= fy
    }
  })
}

/**
 * 更新节点位置
 */
function updateNodePositions(
  nodeMap: Map<string, ForceNode>,
  config: Required<Omit<LayoutConfig, 'centerX' | 'centerY' | 'repulsionStrength'>>
): void {
  const { damping } = config

  nodeMap.forEach((node) => {
    node.vx *= damping
    node.vy *= damping

    node.fx += node.vx
    node.fy += node.vy

    // 边界约束
    node.fx = Math.max(50, Math.min(1200, node.fx))
    node.fy = Math.max(50, Math.min(800, node.fy))
  })
}

/**
 * 构建树结构
 */
function buildTree(nodes: WorkflowNode[], connections: Connection[]): Tree {
  const nodeMap = new Map(nodes.map((node) => [node.id, node]))
  const children = new Map<string, string[]>()
  const parents = new Map<string, string>()

  // 初始化
  nodes.forEach((node) => {
    children.set(node.id, [])
  })

  // 构建父子关系
  connections.forEach((conn) => {
    if (nodeMap.has(conn.fromNodeId) && nodeMap.has(conn.toNodeId)) {
      children.get(conn.fromNodeId)!.push(conn.toNodeId)
      parents.set(conn.toNodeId, conn.fromNodeId)
    }
  })

  // 查找根节点
  const root = nodes.find((node) => !parents.has(node.id))?.id

  return { root, children, parents }
}

/**
 * 计算子树大小
 */
function calculateSubtreeSizes(nodeId: string, children: Map<string, string[]>): number {
  const childNodes = children.get(nodeId) || []
  let size = 1

  childNodes.forEach((childId) => {
    size += calculateSubtreeSizes(childId, children)
  })

  return size
}

/**
 * 布局树节点
 */
function layoutTreeNodes(
  rootId: string,
  children: Map<string, string[]>,
  nodeMap: Map<string, WorkflowNode>,
  config: Required<Omit<LayoutConfig, 'centerX' | 'centerY' | 'repulsionStrength'>>,
  x: number = 0,
  y: number = 0,
  level: number = 0
): number {
  const node = nodeMap.get(rootId)
  if (!node) return 0

  node.x = x
  node.y = y

  const childNodes = children.get(rootId) || []
  if (childNodes.length === 0) return 1

  let currentX = x
  const nextY = y + config.levelSpacing

  childNodes.forEach((childId) => {
    const width = layoutTreeNodes(childId, children, nodeMap, config, currentX, nextY, level + 1)
    currentX += width * config.nodeSpacing
  })

  // 居中父节点
  if (childNodes.length > 0) {
    const firstChild = nodeMap.get(childNodes[0])
    const lastChild = nodeMap.get(childNodes[childNodes.length - 1])
    if (firstChild && lastChild) {
      node.x = (firstChild.x! + lastChild.x!) / 2
    }
  }

  return childNodes.length || 1
}

/**
 * 拓扑排序
 */
function topologicalSort(graph: Graph): string[][] {
  const layers: string[][] = []
  const inDegree = new Map(graph.inDegree)
  const queue: string[] = []

  // 找到所有入度为0的节点
  inDegree.forEach((degree, nodeId) => {
    if (degree === 0) {
      queue.push(nodeId)
    }
  })

  let currentLayer = 0

  while (queue.length > 0) {
    const layerSize = queue.length
    layers[currentLayer] = []

    for (let i = 0; i < layerSize; i++) {
      const nodeId = queue.shift()!
      layers[currentLayer].push(nodeId)

      const neighbors = graph.edges.get(nodeId) || []
      neighbors.forEach((neighborId) => {
        const newDegree = inDegree.get(neighborId)! - 1
        inDegree.set(neighborId, newDegree)

        if (newDegree === 0) {
          queue.push(neighborId)
        }
      })
    }

    currentLayer++
  }

  return layers
}

/**
 * 减少交叉
 */
function reduceCrossings(layers: string[][], connections: Connection[]): void {
  // 简化的交叉减少算法
  for (let i = 0; i < layers.length - 1; i++) {
    const currentLayer = layers[i]
    const nextLayer = layers[i + 1]

    // 计算每个节点的重心
    const barycenters = new Map<string, number>()

    nextLayer.forEach((nodeId) => {
      const incomingConnections = connections.filter((conn) => conn.toNodeId === nodeId)
      if (incomingConnections.length > 0) {
        const sum = incomingConnections.reduce((acc, conn) => {
          const index = currentLayer.indexOf(conn.fromNodeId)
          return acc + (index >= 0 ? index : 0)
        }, 0)
        barycenters.set(nodeId, sum / incomingConnections.length)
      } else {
        barycenters.set(nodeId, 0)
      }
    })

    // 按重心排序
    nextLayer.sort((a, b) => {
      const aBarycenter = barycenters.get(a) || 0
      const bBarycenter = barycenters.get(b) || 0
      return aBarycenter - bBarycenter
    })
  }
}

/**
 * 分配层级坐标
 */
function assignLayerCoordinates(
  layers: string[][],
  nodeMap: Map<string, WorkflowNode>,
  config: Required<Omit<LayoutConfig, 'centerX' | 'centerY' | 'repulsionStrength'>>
): void {
  const { nodeSpacing, levelSpacing, padding } = config

  layers.forEach((layer, layerIndex) => {
    const y = padding + layerIndex * levelSpacing
    const totalWidth = (layer.length - 1) * nodeSpacing
    const startX = padding + Math.max(0, (1000 - totalWidth) / 2)

    layer.forEach((nodeId, nodeIndex) => {
      const node = nodeMap.get(nodeId)
      if (node) {
        node.x = startX + nodeIndex * nodeSpacing
        node.y = y
      }
    })
  })
}

/**
 * 应用有机化调整
 */
function applyOrganicAdjustments(
  nodes: WorkflowNode[],
  connections: Connection[],
  config: LayoutConfig
): WorkflowNode[] {
  // 添加一些随机性和自然感
  return nodes.map((node) => ({
    ...node,
    x: (node.x || 0) + (Math.random() - 0.5) * 20,
    y: (node.y || 0) + (Math.random() - 0.5) * 20,
  }))
}

// ========== 高级功能 ==========

/**
 * 自动选择最佳布局算法
 * @param nodes - 节点数组
 * @param connections - 连接数组
 * @param config - 布局配置
 * @returns 布局结果和推荐的算法
 */
export function autoLayout(
  nodes: WorkflowNode[],
  connections: Connection[],
  config: LayoutConfig = {}
): AutoLayoutResult {
  const nodeCount = nodes.length
  const connectionCount = connections.length
  const density = nodeCount > 0 ? connectionCount / (nodeCount * (nodeCount - 1)) : 0

  let recommendedAlgorithm: LayoutType = LAYOUT_TYPES.HIERARCHICAL
  let reason = '默认选择'

  // 根据图的特征选择算法
  if (nodeCount <= 10) {
    recommendedAlgorithm = LAYOUT_TYPES.CIRCULAR
    reason = '节点数量较少，适合圆形布局'
  } else if (density < 0.1) {
    recommendedAlgorithm = LAYOUT_TYPES.HIERARCHICAL
    reason = '连接密度较低，适合层次布局'
  } else if (density > 0.3) {
    recommendedAlgorithm = LAYOUT_TYPES.FORCE_DIRECTED
    reason = '连接密度较高，适合力导向布局'
  } else {
    // 检查是否为树结构
    const graph = buildGraph(nodes, connections)
    const rootNodes = findRootNodes(graph)

    if (rootNodes.length === 1 && connectionCount === nodeCount - 1) {
      recommendedAlgorithm = LAYOUT_TYPES.TREE
      reason = '检测到树结构，适合树形布局'
    }
  }

  // 执行推荐的布局算法
  let layoutedNodes: WorkflowNode[]
  switch (recommendedAlgorithm) {
    case LAYOUT_TYPES.HIERARCHICAL:
      layoutedNodes = hierarchicalLayout(nodes, connections, config)
      break
    case LAYOUT_TYPES.FORCE_DIRECTED:
      layoutedNodes = forceDirectedLayout(nodes, connections, config)
      break
    case LAYOUT_TYPES.CIRCULAR:
      layoutedNodes = circularLayout(nodes, connections, config)
      break
    case LAYOUT_TYPES.GRID:
      layoutedNodes = gridLayout(nodes, connections, config)
      break
    case LAYOUT_TYPES.TREE:
      layoutedNodes = treeLayout(nodes, connections, config)
      break
    case LAYOUT_TYPES.LAYERED:
      layoutedNodes = layeredLayout(nodes, connections, config)
      break
    case LAYOUT_TYPES.ORGANIC:
      layoutedNodes = organicLayout(nodes, connections, config)
      break
    default:
      layoutedNodes = hierarchicalLayout(nodes, connections, config)
  }

  return {
    nodes: layoutedNodes,
    algorithm: recommendedAlgorithm,
    reason,
    stats: {
      nodeCount,
      connectionCount,
      density: Math.round(density * 1000) / 1000,
    },
  }
}

/**
 * 优化现有布局
 * @param nodes - 节点数组
 * @param connections - 连接数组
 * @param config - 优化配置
 * @returns 优化后的节点数组
 */
export function optimizeLayout(
  nodes: WorkflowNode[],
  connections: Connection[],
  config: LayoutConfig = {}
): WorkflowNode[] {
  const cfg: LayoutConfig = {
    iterations: 50,
    springStrength: 0.01,
    repulsionStrength: 500,
    ...config,
  }

  // 使用轻量级的力导向算法进行微调
  return forceDirectedLayout(nodes, connections, cfg)
}

// ========== 导出类型 ==========

export type {
  LayoutType,
  LayoutDirection,
  LayoutConfig,
  WorkflowNode,
  Connection,
  ForceNode,
  Graph,
  Tree,
  AutoLayoutResult,
  AlignmentType,
}

