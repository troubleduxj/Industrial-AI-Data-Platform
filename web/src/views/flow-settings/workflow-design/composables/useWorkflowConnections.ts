/**
 * 工作流连接管理组合式函数
 * 提供连接的创建、编辑、删除、验证等功能
 */

import { ref, computed, reactive, watch, type Ref, type ComputedRef } from 'vue'
import { useWorkflowStore } from '../stores/workflowStore'

// ========== 类型定义 ==========

interface Point { x: number; y: number }

interface ConnectionPoint { id: string; type: string; position: Point }

interface CreatingState {
  active: boolean
  sourceNodeId: string | null
  sourcePoint: ConnectionPoint | null
  currentPosition: Point
  validTargets: any[]
  hoveredTarget: any | null
}

interface EditingState {
  active: boolean
  connectionId: string | null
  field: string | null
}

interface HoveringState {
  connectionId: string | null
  position: Point
}

interface SelectionState {
  connectionIds: string[]
  lastSelected: string | null
}

interface ValidationState {
  errors: any[]
  warnings: any[]
}

interface ConnectionState {
  creating: CreatingState
  editing: EditingState
  hovering: HoveringState
  selection: SelectionState
  validation: ValidationState
}

interface ConnectionTypeConfig {
  label: string
  color: string
  style: string
  allowMultiple: boolean
}

type ConnectionTypes = Record<string, ConnectionTypeConfig>

// ========== Composable ==========

export function useWorkflowConnections() {
  const workflowStore = useWorkflowStore()

  const connectionState = reactive<ConnectionState>({
    creating: {
      active: false,
      sourceNodeId: null,
      sourcePoint: null,
      currentPosition: { x: 0, y: 0 },
      validTargets: [],
      hoveredTarget: null,
    },
    editing: {
      active: false,
      connectionId: null,
      field: null,
    },
    hovering: {
      connectionId: null,
      position: { x: 0, y: 0 },
    },
    selection: {
      connectionIds: [],
      lastSelected: null,
    },
    validation: {
      errors: [],
      warnings: [],
    },
  })

  const connectionTypes: ConnectionTypes = {
    data: { label: '数据流', color: '#1890ff', style: 'solid', allowMultiple: true },
    control: { label: '控制流', color: '#52c41a', style: 'solid', allowMultiple: false },
    error: { label: '错误处理', color: '#ff4d4f', style: 'dashed', allowMultiple: false },
    condition: { label: '条件分支', color: '#faad14', style: 'solid', allowMultiple: false },
  }

  const selectedConnections: ComputedRef<any[]> = computed(() =>
    workflowStore.connections.filter((conn: any) =>
      connectionState.selection.connectionIds.includes(conn.id)
    )
  )

  const validConnections: ComputedRef<any[]> = computed(() =>
    workflowStore.connections.filter((conn: any) => validateConnection(conn).isValid)
  )

  const invalidConnections: ComputedRef<any[]> = computed(() =>
    workflowStore.connections.filter((conn: any) => !validateConnection(conn).isValid)
  )

  function startConnectionCreation(
    sourceNodeId: string,
    sourcePoint: ConnectionPoint,
    mousePosition: Point
  ): boolean {
    const sourceNode = workflowStore.getNodeById(sourceNodeId)
    if (!sourceNode) return false

    connectionState.creating = {
      active: true,
      sourceNodeId,
      sourcePoint,
      currentPosition: { ...mousePosition },
      validTargets: findValidTargets(sourceNodeId, sourcePoint),
      hoveredTarget: null,
    }

    return true
  }

  function updateConnectionCreation(
    mousePosition: Point,
    hoveredNodeId: string | null = null,
    hoveredPoint: ConnectionPoint | null = null
  ): void {
    if (!connectionState.creating.active) return

    connectionState.creating.currentPosition = { ...mousePosition }

    if (hoveredNodeId && hoveredPoint) {
      const isValidTarget = connectionState.creating.validTargets.some(
        (target: any) => target.nodeId === hoveredNodeId && target.point.id === hoveredPoint.id
      )

      connectionState.creating.hoveredTarget = isValidTarget
        ? { nodeId: hoveredNodeId, point: hoveredPoint }
        : null
    } else {
      connectionState.creating.hoveredTarget = null
    }
  }

  function completeConnectionCreation(
    targetNodeId: string | null = null,
    targetPoint: ConnectionPoint | null = null
  ): any | null {
    if (!connectionState.creating.active) return null

    const { sourceNodeId, sourcePoint } = connectionState.creating

    const finalTargetNodeId = targetNodeId || connectionState.creating.hoveredTarget?.nodeId
    const finalTargetPoint = targetPoint || connectionState.creating.hoveredTarget?.point

    let newConnection: any | null = null

    if (
      finalTargetNodeId &&
      finalTargetPoint &&
      sourceNodeId &&
      sourcePoint &&
      canCreateConnection(sourceNodeId, sourcePoint, finalTargetNodeId, finalTargetPoint)
    ) {
      newConnection = {
        id: `conn_${Date.now()}`,
        sourceNodeId,
        sourcePoint: sourcePoint.id,
        targetNodeId: finalTargetNodeId,
        targetPoint: finalTargetPoint.id,
        type: 'data',
        style: connectionTypes.data.style,
      }

      workflowStore.addConnection(newConnection)
    }

    cancelConnectionCreation()
    return newConnection
  }

  function cancelConnectionCreation(): void {
    connectionState.creating = {
      active: false,
      sourceNodeId: null,
      sourcePoint: null,
      currentPosition: { x: 0, y: 0 },
      validTargets: [],
      hoveredTarget: null,
    }
  }

  function deleteConnection(connectionId: string): boolean {
    return workflowStore.removeConnection(connectionId)
  }

  function deleteConnections(connectionIds: string[]): number {
    let deletedCount = 0
    connectionIds.forEach((id) => {
      if (workflowStore.removeConnection(id)) {
        deletedCount++
      }
    })
    return deletedCount
  }

  function validateConnection(connection: any): { isValid: boolean; errors: string[] } {
    const errors: string[] = []

    if (!connection.sourceNodeId || !connection.targetNodeId) {
      errors.push('缺少源节点或目标节点')
    }

    if (connection.sourceNodeId === connection.targetNodeId) {
      errors.push('不能连接到自身')
    }

    return { isValid: errors.length === 0, errors }
  }

  function findValidTargets(sourceNodeId: string, sourcePoint: ConnectionPoint): any[] {
    return workflowStore.nodes
      .filter((node: any) => node.id !== sourceNodeId)
      .map((node: any) => ({
        nodeId: node.id,
        points: node.connectionPoints || [],
      }))
  }

  function canCreateConnection(
    sourceNodeId: string,
    sourcePoint: ConnectionPoint,
    targetNodeId: string,
    targetPoint: ConnectionPoint
  ): boolean {
    if (sourceNodeId === targetNodeId) return false

    const existingConnection = workflowStore.connections.find(
      (conn: any) =>
        conn.sourceNodeId === sourceNodeId &&
        conn.targetNodeId === targetNodeId &&
        conn.sourcePoint === sourcePoint.id &&
        conn.targetPoint === targetPoint.id
    )

    return !existingConnection
  }

  return {
    connectionState,
    connectionTypes,
    selectedConnections,
    validConnections,
    invalidConnections,
    startConnectionCreation,
    updateConnectionCreation,
    completeConnectionCreation,
    cancelConnectionCreation,
    deleteConnection,
    deleteConnections,
    validateConnection,
  }
}

export type {
  Point,
  ConnectionPoint,
  CreatingState,
  EditingState,
  HoveringState,
  SelectionState,
  ValidationState,
  ConnectionState,
  ConnectionTypeConfig,
  ConnectionTypes,
}

