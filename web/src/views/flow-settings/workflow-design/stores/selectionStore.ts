/**
 * 选择状态管理
 * Selection state management store
 */

import { defineStore } from 'pinia'
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import { useWorkflowStore } from './workflowStore.js'

// ========== 类型定义 ==========

/** 选择模式 */
type SelectionMode = 'replace' | 'add' | 'subtract' | 'intersect' | 'toggle'

/** 选择框 */
interface SelectionBox {
  active: boolean
  startX: number
  startY: number
  endX: number
  endY: number
}

/** 选择元素 */
interface SelectedElement {
  id: string
  type: 'node' | 'connection'
}

/** 选择边界 */
interface SelectionBounds {
  x: number
  y: number
  width: number
  height: number
  centerX: number
  centerY: number
}

// ========== Store 定义 ==========

export const useSelectionStore = defineStore('workflowSelection', () => {
  // 选择状态
  const selectedNodes: Ref<string[]> = ref([])
  const selectedConnections: Ref<string[]> = ref([])
  const selectedElements: Ref<SelectedElement[]> = ref([])

  // 高亮状态
  const highlightedNodes: Ref<string[]> = ref([])
  const highlightedConnections: Ref<string[]> = ref([])

  // 悬停状态
  const hoveredNode: Ref<string | null> = ref(null)
  const hoveredConnection: Ref<string | null> = ref(null)

  // 选择框状态
  const selectionBox: Ref<SelectionBox> = ref({
    active: false,
    startX: 0,
    startY: 0,
    endX: 0,
    endY: 0,
  })

  // 选择模式
  const selectionMode: Ref<SelectionMode> = ref('replace')

  // 获取工作流store
  const workflowStore = useWorkflowStore()

  // 计算属性
  const hasSelection: ComputedRef<boolean> = computed(() => {
    return selectedNodes.value.length > 0 || selectedConnections.value.length > 0
  })

  const selectionCount: ComputedRef<number> = computed(() => {
    return selectedNodes.value.length + selectedConnections.value.length
  })

  const selectedNodesData: ComputedRef<any[]> = computed(() => {
    return selectedNodes.value.map((id) => workflowStore.getNodeById(id)).filter(Boolean)
  })

  const selectedConnectionsData: ComputedRef<any[]> = computed(() => {
    return selectedConnections.value
      .map((id) => workflowStore.getConnectionById(id))
      .filter(Boolean)
  })

  const selectionBounds: ComputedRef<SelectionBounds | null> = computed(() => {
    if (selectedNodes.value.length === 0) return null

    const nodes = selectedNodesData.value
    if (nodes.length === 0) return null

    let minX = Infinity
    let minY = Infinity
    let maxX = -Infinity
    let maxY = -Infinity

    nodes.forEach((node: any) => {
      minX = Math.min(minX, node.x)
      minY = Math.min(minY, node.y)
      maxX = Math.max(maxX, node.x + (node.width || 120))
      maxY = Math.max(maxY, node.y + (node.height || 80))
    })

    return {
      x: minX,
      y: minY,
      width: maxX - minX,
      height: maxY - minY,
      centerX: (minX + maxX) / 2,
      centerY: (minY + maxY) / 2,
    }
  })

  // 节点选择操作
  function selectNode(nodeId: string, mode: SelectionMode = selectionMode.value): void {
    if (!nodeId) return

    switch (mode) {
      case 'replace':
        selectedNodes.value = [nodeId]
        selectedConnections.value = []
        break
      case 'add':
        if (!selectedNodes.value.includes(nodeId)) {
          selectedNodes.value.push(nodeId)
        }
        break
      case 'subtract':
        {
          const index = selectedNodes.value.indexOf(nodeId)
          if (index > -1) {
            selectedNodes.value.splice(index, 1)
          }
        }
        break
      case 'toggle':
        {
          const toggleIndex = selectedNodes.value.indexOf(nodeId)
          if (toggleIndex > -1) {
            selectedNodes.value.splice(toggleIndex, 1)
          } else {
            selectedNodes.value.push(nodeId)
          }
        }
        break
    }

    updateSelectedElements()
  }

  function selectNodes(nodeIds: string[], mode: SelectionMode = 'replace'): void {
    switch (mode) {
      case 'replace':
        selectedNodes.value = [...nodeIds]
        selectedConnections.value = []
        break
      case 'add':
        nodeIds.forEach((id) => {
          if (!selectedNodes.value.includes(id)) {
            selectedNodes.value.push(id)
          }
        })
        break
      case 'subtract':
        nodeIds.forEach((id) => {
          const index = selectedNodes.value.indexOf(id)
          if (index > -1) {
            selectedNodes.value.splice(index, 1)
          }
        })
        break
    }

    updateSelectedElements()
  }

  // 连接选择操作
  function selectConnection(connectionId: string, mode: SelectionMode = selectionMode.value): void {
    if (!connectionId) return

    switch (mode) {
      case 'replace':
        selectedConnections.value = [connectionId]
        selectedNodes.value = []
        break
      case 'add':
        if (!selectedConnections.value.includes(connectionId)) {
          selectedConnections.value.push(connectionId)
        }
        break
      case 'subtract':
        {
          const index = selectedConnections.value.indexOf(connectionId)
          if (index > -1) {
            selectedConnections.value.splice(index, 1)
          }
        }
        break
      case 'toggle':
        {
          const toggleIndex = selectedConnections.value.indexOf(connectionId)
          if (toggleIndex > -1) {
            selectedConnections.value.splice(toggleIndex, 1)
          } else {
            selectedConnections.value.push(connectionId)
          }
        }
        break
    }

    updateSelectedElements()
  }

  function selectConnections(connectionIds: string[], mode: SelectionMode = 'replace'): void {
    switch (mode) {
      case 'replace':
        selectedConnections.value = [...connectionIds]
        selectedNodes.value = []
        break
      case 'add':
        connectionIds.forEach((id) => {
          if (!selectedConnections.value.includes(id)) {
            selectedConnections.value.push(id)
          }
        })
        break
      case 'subtract':
        connectionIds.forEach((id) => {
          const index = selectedConnections.value.indexOf(id)
          if (index > -1) {
            selectedConnections.value.splice(index, 1)
          }
        })
        break
    }

    updateSelectedElements()
  }

  // 混合选择操作
  function selectElement(elementId: string, elementType: 'node' | 'connection', mode: SelectionMode = selectionMode.value): void {
    if (elementType === 'node') {
      selectNode(elementId, mode)
    } else if (elementType === 'connection') {
      selectConnection(elementId, mode)
    }
  }

  function selectElements(elements: SelectedElement[], mode: SelectionMode = 'replace'): void {
    const nodeIds = elements.filter((el) => el.type === 'node').map((el) => el.id)
    const connectionIds = elements.filter((el) => el.type === 'connection').map((el) => el.id)

    if (mode === 'replace') {
      selectedNodes.value = nodeIds
      selectedConnections.value = connectionIds
    } else {
      selectNodes(nodeIds, mode)
      selectConnections(connectionIds, mode)
    }

    updateSelectedElements()
  }

  // 清除选择
  function clearSelection(): void {
    selectedNodes.value = []
    selectedConnections.value = []
    selectedElements.value = []
  }

  function clearNodeSelection(): void {
    selectedNodes.value = []
    updateSelectedElements()
  }

  function clearConnectionSelection(): void {
    selectedConnections.value = []
    updateSelectedElements()
  }

  // 全选操作
  function selectAll(): void {
    selectedNodes.value = workflowStore.nodes.map((node: any) => node.id)
    selectedConnections.value = workflowStore.connections.map((conn: any) => conn.id)
    updateSelectedElements()
  }

  function selectAllNodes(): void {
    selectedNodes.value = workflowStore.nodes.map((node: any) => node.id)
    selectedConnections.value = []
    updateSelectedElements()
  }

  function selectAllConnections(): void {
    selectedConnections.value = workflowStore.connections.map((conn: any) => conn.id)
    selectedNodes.value = []
    updateSelectedElements()
  }

  // 反选操作
  function invertSelection(): void {
    const allNodeIds = workflowStore.nodes.map((node: any) => node.id)
    const allConnectionIds = workflowStore.connections.map((conn: any) => conn.id)

    const newSelectedNodes = allNodeIds.filter((id: string) => !selectedNodes.value.includes(id))
    const newSelectedConnections = allConnectionIds.filter(
      (id: string) => !selectedConnections.value.includes(id)
    )

    selectedNodes.value = newSelectedNodes
    selectedConnections.value = newSelectedConnections
    updateSelectedElements()
  }

  // 选择框操作
  function startSelectionBox(x: number, y: number): void {
    selectionBox.value = {
      active: true,
      startX: x,
      startY: y,
      endX: x,
      endY: y,
    }
  }

  function updateSelectionBox(x: number, y: number): void {
    if (selectionBox.value.active) {
      selectionBox.value.endX = x
      selectionBox.value.endY = y
    }
  }

  function endSelectionBox(mode: SelectionMode = 'replace'): void {
    if (!selectionBox.value.active) return

    const box = selectionBox.value
    const minX = Math.min(box.startX, box.endX)
    const maxX = Math.max(box.startX, box.endX)
    const minY = Math.min(box.startY, box.endY)
    const maxY = Math.max(box.startY, box.endY)

    // 查找在选择框内的节点
    const nodesInBox = workflowStore.nodes
      .filter((node: any) => {
        const nodeRight = node.x + (node.width || 120)
        const nodeBottom = node.y + (node.height || 80)

        return node.x >= minX && nodeRight <= maxX && node.y >= minY && nodeBottom <= maxY
      })
      .map((node: any) => node.id)

    selectNodes(nodesInBox, mode)

    selectionBox.value.active = false
  }

  function cancelSelectionBox(): void {
    selectionBox.value.active = false
  }

  // 高亮操作
  function highlightNodes(nodeIds: string[]): void {
    highlightedNodes.value = [...nodeIds]
  }

  function highlightConnections(connectionIds: string[]): void {
    highlightedConnections.value = [...connectionIds]
  }

  function clearHighlight(): void {
    highlightedNodes.value = []
    highlightedConnections.value = []
  }

  // 悬停操作
  function setHoveredNode(nodeId: string | null): void {
    hoveredNode.value = nodeId
  }

  function setHoveredConnection(connectionId: string | null): void {
    hoveredConnection.value = connectionId
  }

  function clearHover(): void {
    hoveredNode.value = null
    hoveredConnection.value = null
  }

  // 选择模式设置
  function setSelectionMode(mode: SelectionMode): void {
    selectionMode.value = mode
  }

  // 辅助函数
  function updateSelectedElements(): void {
    selectedElements.value = [
      ...selectedNodes.value.map((id) => ({ id, type: 'node' as const })),
      ...selectedConnections.value.map((id) => ({ id, type: 'connection' as const })),
    ]
  }

  function isNodeSelected(nodeId: string): boolean {
    return selectedNodes.value.includes(nodeId)
  }

  function isConnectionSelected(connectionId: string): boolean {
    return selectedConnections.value.includes(connectionId)
  }

  function isNodeHighlighted(nodeId: string): boolean {
    return highlightedNodes.value.includes(nodeId)
  }

  function isConnectionHighlighted(connectionId: string): boolean {
    return highlightedConnections.value.includes(connectionId)
  }

  // 选择相关的节点和连接
  function selectConnectedElements(nodeId: string): void {
    const connectedConnections = workflowStore.connections
      .filter((conn: any) => conn.fromNodeId === nodeId || conn.toNodeId === nodeId)
      .map((conn: any) => conn.id)

    selectNode(nodeId, 'add')
    selectConnections(connectedConnections, 'add')
  }

  function selectNodePath(startNodeId: string, endNodeId: string): void {
    // 实现路径选择逻辑
    // 这里可以添加图算法来找到两个节点之间的路径
    // 暂时简化实现
    selectNode(startNodeId, 'add')
    selectNode(endNodeId, 'add')
  }

  return {
    // 状态
    selectedNodes: computed(() => selectedNodes.value),
    selectedConnections: computed(() => selectedConnections.value),
    selectedElements: computed(() => selectedElements.value),
    highlightedNodes: computed(() => highlightedNodes.value),
    highlightedConnections: computed(() => highlightedConnections.value),
    hoveredNode: computed(() => hoveredNode.value),
    hoveredConnection: computed(() => hoveredConnection.value),
    selectionBox: computed(() => selectionBox.value),
    selectionMode: computed(() => selectionMode.value),

    // 计算属性
    hasSelection,
    selectionCount,
    selectedNodesData,
    selectedConnectionsData,
    selectionBounds,

    // 方法
    selectNode,
    selectNodes,
    selectConnection,
    selectConnections,
    selectElement,
    selectElements,
    clearSelection,
    clearNodeSelection,
    clearConnectionSelection,
    selectAll,
    selectAllNodes,
    selectAllConnections,
    invertSelection,
    startSelectionBox,
    updateSelectionBox,
    endSelectionBox,
    cancelSelectionBox,
    highlightNodes,
    highlightConnections,
    clearHighlight,
    setHoveredNode,
    setHoveredConnection,
    clearHover,
    setSelectionMode,
    isNodeSelected,
    isConnectionSelected,
    isNodeHighlighted,
    isConnectionHighlighted,
    selectConnectedElements,
    selectNodePath,
  }
})

// ========== 导出类型 ==========

export type { SelectionMode, SelectionBox, SelectedElement, SelectionBounds }

