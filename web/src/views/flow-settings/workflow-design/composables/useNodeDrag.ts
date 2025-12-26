/**
 * 节点拖拽处理器
 * Node drag handler composable
 */

import { ref, computed, onMounted, onUnmounted, type Ref, type ComputedRef } from 'vue'
import {
  snapPointWithMagnetism,
  getAlignmentGuides,
  applyAlignmentSnap,
} from '../utils/gridUtils.js'
import { ACTION_TYPES, getActionDescription } from '../utils/historyManager.js'

// ========== 类型定义 ==========

/** 节点拖拽配置 */
interface UseNodeDragOptions {
  nodes: Ref<any[]>
  selectedNodes: Ref<string[]>
  scale: Ref<number>
  translateX: Ref<number>
  translateY: Ref<number>
  snapToGrid?: boolean
  showAlignmentGuides?: boolean
  onNodeMove?: (nodes: any[]) => void
  onSaveHistory?: (description: string) => void
}

/** 位置坐标 */
interface Position {
  x: number
  y: number
}

/** 拖拽偏移 */
interface DragOffset {
  x: number
  y: number
}

/** 对齐辅助线 */
interface AlignmentGuide {
  type: 'horizontal' | 'vertical'
  position: number
}

// ========== Composable ==========

export function useNodeDrag({
  nodes,
  selectedNodes,
  scale,
  translateX,
  translateY,
  snapToGrid = true,
  showAlignmentGuides = true,
  onNodeMove,
  onSaveHistory,
}: UseNodeDragOptions) {
  // 拖拽状态
  const isDragging: Ref<boolean> = ref(false)
  const draggedNodes: Ref<any[]> = ref([])
  const dragStartPos: Ref<Position> = ref({ x: 0, y: 0 })
  const dragOffset: Ref<DragOffset> = ref({ x: 0, y: 0 })
  const alignmentGuides: Ref<AlignmentGuide[]> = ref([])

  // 拖拽相关的计算属性
  const draggedNodeIds: ComputedRef<string[]> = computed(() => draggedNodes.value.map((node: any) => node.id))

  /**
   * 开始拖拽节点
   * @param node - 被拖拽的节点
   * @param event - 鼠标事件
   */
  function startDrag(node: any, event: MouseEvent): void {
    if (isDragging.value) return

    isDragging.value = true

    // 确定要拖拽的节点列表
    if (selectedNodes.value.includes(node.id)) {
      // 如果点击的节点在选中列表中，拖拽所有选中的节点
      draggedNodes.value = nodes.value.filter((n: any) => selectedNodes.value.includes(n.id))
    } else {
      // 否则只拖拽当前节点
      draggedNodes.value = [node]
    }

    // 记录拖拽起始位置
    const canvasElement = (event.target as Element).closest('.workflow-canvas')
    if (!canvasElement) return
    
    const rect = canvasElement.getBoundingClientRect()
    dragStartPos.value = {
      x: event.clientX,
      y: event.clientY,
    }

    // 计算鼠标相对于节点的偏移
    const canvasX = (event.clientX - rect.left - translateX.value) / scale.value
    const canvasY = (event.clientY - rect.top - translateY.value) / scale.value

    dragOffset.value = {
      x: canvasX - node.x,
      y: canvasY - node.y,
    }

    // 添加全局事件监听
    document.addEventListener('mousemove', handleDragMove)
    document.addEventListener('mouseup', handleDragEnd)

    // 阻止默认行为
    event.preventDefault()
  }

  /**
   * 处理拖拽移动
   * @param event - 鼠标事件
   */
  function handleDragMove(event: MouseEvent): void {
    if (!isDragging.value || draggedNodes.value.length === 0) return

    const canvasElement = document.querySelector('.workflow-canvas')
    if (!canvasElement) return

    const rect = canvasElement.getBoundingClientRect()
    const canvasX = (event.clientX - rect.left - translateX.value) / scale.value
    const canvasY = (event.clientY - rect.top - translateY.value) / scale.value

    // 计算新位置
    const newX = canvasX - dragOffset.value.x
    const newY = canvasY - dragOffset.value.y

    // 计算位置偏移量
    const primaryNode = draggedNodes.value[0]
    const deltaX = newX - primaryNode.x
    const deltaY = newY - primaryNode.y

    // 应用网格吸附和对齐吸附
    let adjustedDelta: DragOffset = { x: deltaX, y: deltaY }

    if (snapToGrid) {
      const snappedPosition = snapPointWithMagnetism(
        { x: newX, y: newY },
        20, // 网格大小
        10 // 吸附阈值
      )
      adjustedDelta = {
        x: snappedPosition.x - primaryNode.x,
        y: snappedPosition.y - primaryNode.y,
      }
    }

    // 检查对齐辅助线
    if (showAlignmentGuides) {
      const otherNodes = nodes.value.filter((node: any) => !draggedNodeIds.value.includes(node.id))

      const testPosition: Position = {
        x: primaryNode.x + adjustedDelta.x,
        y: primaryNode.y + adjustedDelta.y,
      }

      const alignedPosition = applyAlignmentSnap(testPosition, otherNodes, 5)
      adjustedDelta = {
        x: alignedPosition.x - primaryNode.x,
        y: alignedPosition.y - primaryNode.y,
      }

      // 更新对齐辅助线
      const testNode = { ...primaryNode, x: alignedPosition.x, y: alignedPosition.y }
      alignmentGuides.value = getAlignmentGuides(testNode, otherNodes, 5)
    }

    // 更新所有被拖拽节点的位置
    const updatedNodes = draggedNodes.value.map((node: any) => ({
      ...node,
      x: node.x + adjustedDelta.x,
      y: node.y + adjustedDelta.y,
    }))

    // 触发节点移动事件
    onNodeMove?.(updatedNodes)
  }

  /**
   * 结束拖拽
   * @param event - 鼠标事件
   */
  function handleDragEnd(event: MouseEvent): void {
    if (!isDragging.value) return

    // 检查是否实际移动了节点
    const moved =
      Math.abs(event.clientX - dragStartPos.value.x) > 3 ||
      Math.abs(event.clientY - dragStartPos.value.y) > 3

    if (moved && draggedNodes.value.length > 0) {
      // 保存到历史记录
      const actionDescription =
        draggedNodes.value.length === 1
          ? getActionDescription(ACTION_TYPES.MOVE_NODE, { nodeName: draggedNodes.value[0].name })
          : `移动 ${draggedNodes.value.length} 个节点`

      onSaveHistory?.(actionDescription)
    }

    // 重置拖拽状态
    isDragging.value = false
    draggedNodes.value = []
    alignmentGuides.value = []

    // 移除全局事件监听
    document.removeEventListener('mousemove', handleDragMove)
    document.removeEventListener('mouseup', handleDragEnd)
  }

  /**
   * 取消拖拽
   */
  function cancelDrag(): void {
    if (!isDragging.value) return

    isDragging.value = false
    draggedNodes.value = []
    alignmentGuides.value = []

    document.removeEventListener('mousemove', handleDragMove)
    document.removeEventListener('mouseup', handleDragEnd)
  }

  /**
   * 检查节点是否正在被拖拽
   * @param nodeId - 节点ID
   * @returns 是否正在拖拽
   */
  function isNodeDragging(nodeId: string): boolean {
    return isDragging.value && draggedNodeIds.value.includes(nodeId)
  }

  /**
   * 获取拖拽预览位置
   * @param node - 节点
   * @returns 预览位置 {x, y}
   */
  function getDragPreviewPosition(node: any): Position {
    if (!isDragging.value || !draggedNodeIds.value.includes(node.id)) {
      return { x: node.x, y: node.y }
    }

    const draggedNode = draggedNodes.value.find((n: any) => n.id === node.id)
    return draggedNode ? { x: draggedNode.x, y: draggedNode.y } : { x: node.x, y: node.y }
  }

  /**
   * 批量移动节点
   * @param nodeIds - 节点ID列表
   * @param delta - 移动偏移量 {x, y}
   */
  function moveNodes(nodeIds: string[], delta: DragOffset): void {
    const nodesToMove = nodes.value.filter((node: any) => nodeIds.includes(node.id))

    const updatedNodes = nodesToMove.map((node: any) => ({
      ...node,
      x: node.x + delta.x,
      y: node.y + delta.y,
    }))

    onNodeMove?.(updatedNodes)

    // 保存到历史记录
    const actionDescription =
      nodesToMove.length === 1
        ? getActionDescription(ACTION_TYPES.MOVE_NODE, { nodeName: nodesToMove[0].name })
        : `移动 ${nodesToMove.length} 个节点`

    onSaveHistory?.(actionDescription)
  }

  /**
   * 将节点移动到指定位置
   * @param nodeId - 节点ID
   * @param position - 目标位置 {x, y}
   */
  function moveNodeToPosition(nodeId: string, position: Position): void {
    const node = nodes.value.find((n: any) => n.id === nodeId)
    if (!node) return

    let finalPosition: Position = { ...position }

    // 应用网格吸附
    if (snapToGrid) {
      finalPosition = snapPointWithMagnetism(position, 20, 10)
    }

    // 应用对齐吸附
    if (showAlignmentGuides) {
      const otherNodes = nodes.value.filter((n: any) => n.id !== nodeId)
      finalPosition = applyAlignmentSnap(finalPosition, otherNodes, 5)
    }

    const updatedNode = {
      ...node,
      x: finalPosition.x,
      y: finalPosition.y,
    }

    onNodeMove?.([updatedNode])
    onSaveHistory?.(getActionDescription(ACTION_TYPES.MOVE_NODE, { nodeName: node.name }))
  }

  /**
   * 自动排列节点
   * @param type - 排列类型 'horizontal' | 'vertical' | 'grid'
   */
  function autoArrangeNodes(type: 'horizontal' | 'vertical' | 'grid' = 'grid'): void {
    if (nodes.value.length === 0) return

    const nodeWidth = 150
    const nodeHeight = 80
    const spacing = 50

    let updatedNodes: any[] = []

    switch (type) {
      case 'horizontal':
        updatedNodes = nodes.value.map((node: any, index: number) => ({
          ...node,
          x: index * (nodeWidth + spacing),
          y: 100,
        }))
        break

      case 'vertical':
        updatedNodes = nodes.value.map((node: any, index: number) => ({
          ...node,
          x: 100,
          y: index * (nodeHeight + spacing),
        }))
        break

      case 'grid':
        const cols = Math.ceil(Math.sqrt(nodes.value.length))
        updatedNodes = nodes.value.map((node: any, index: number) => {
          const row = Math.floor(index / cols)
          const col = index % cols
          return {
            ...node,
            x: col * (nodeWidth + spacing) + 100,
            y: row * (nodeHeight + spacing) + 100,
          }
        })
        break
    }

    onNodeMove?.(updatedNodes)
    onSaveHistory?.(`自动排列节点 (${type})`)
  }

  /**
   * 处理键盘事件
   * @param event - 键盘事件
   */
  function handleKeyDown(event: KeyboardEvent): void {
    if (selectedNodes.value.length === 0) return

    const step = event.shiftKey ? 10 : 1
    let delta: DragOffset = { x: 0, y: 0 }

    switch (event.key) {
      case 'ArrowLeft':
        delta.x = -step
        break
      case 'ArrowRight':
        delta.x = step
        break
      case 'ArrowUp':
        delta.y = -step
        break
      case 'ArrowDown':
        delta.y = step
        break
      default:
        return
    }

    event.preventDefault()
    moveNodes(selectedNodes.value, delta)
  }

  // 生命周期管理
  onMounted(() => {
    // 添加键盘事件监听
    document.addEventListener('keydown', handleKeyDown)
  })

  onUnmounted(() => {
    // 清理事件监听
    document.removeEventListener('keydown', handleKeyDown)
    cancelDrag()
  })

  return {
    // 状态
    isDragging: computed(() => isDragging.value),
    draggedNodeIds,
    alignmentGuides: computed(() => alignmentGuides.value),

    // 方法
    startDrag,
    cancelDrag,
    isNodeDragging,
    getDragPreviewPosition,
    moveNodes,
    moveNodeToPosition,
    autoArrangeNodes,
  }
}

// ========== 导出类型 ==========

export type { UseNodeDragOptions, Position, DragOffset, AlignmentGuide }

