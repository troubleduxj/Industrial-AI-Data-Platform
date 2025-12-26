<template>
  <div class="execution-monitor" :class="{ expanded: isExpanded, collapsed: !isExpanded }">
    <!-- 悬浮展开/收起按钮 -->
    <button class="edge-collapse-btn bottom" @click="toggleExpand">
      {{ isExpanded ? '▼' : '▲' }}
    </button>

    <!-- 面板头部 -->
    <div v-show="isExpanded" class="monitor-header">
      <div class="header-left">
        <span class="monitor-icon">📊</span>
        <span class="monitor-title">执行监控</span>
        <span v-if="currentExecution" class="execution-status" :class="currentExecution.status">
          {{ getStatusText(currentExecution.status) }}
        </span>
      </div>
    </div>

    <!-- 面板内容 -->
    <div v-show="isExpanded" class="monitor-content">
      <!-- 执行控制 -->
      <div class="execution-controls">
        <button 
          class="control-btn execute" 
          :disabled="isExecuting || !canExecute"
          @click="startExecution"
        >
          <span class="btn-icon">▶</span>
          <span>执行</span>
        </button>
        <button 
          class="control-btn stop" 
          :disabled="!isExecuting"
          @click="stopExecution"
        >
          <span class="btn-icon">⏹</span>
          <span>停止</span>
        </button>
        <button 
          class="control-btn clear" 
          :disabled="isExecuting"
          @click="clearLogs"
        >
          <span class="btn-icon">🗑</span>
          <span>清除</span>
        </button>
      </div>

      <!-- 执行进度 -->
      <div v-if="currentExecution" class="execution-progress">
        <div class="progress-header">
          <span class="progress-label">执行进度</span>
          <span class="progress-value">{{ executionProgress }}%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: executionProgress + '%' }"></div>
        </div>
        <div class="progress-info">
          <span>已执行: {{ executedNodes }}/{{ totalNodes }} 节点</span>
          <span>耗时: {{ executionDuration }}</span>
        </div>
      </div>

      <!-- 节点执行状态 -->
      <div class="node-status-list">
        <div class="status-header">节点执行状态</div>
        <div class="status-items">
          <div 
            v-for="node in nodeStatuses" 
            :key="node.id" 
            class="status-item"
            :class="node.status"
            @click="highlightNode(node.id)"
          >
            <span class="node-icon">{{ getNodeIcon(node.type) }}</span>
            <span class="node-name">{{ node.name }}</span>
            <span class="node-status-icon">{{ getStatusIcon(node.status) }}</span>
          </div>
        </div>
      </div>

      <!-- 执行日志 -->
      <div class="execution-logs">
        <div class="logs-header">
          <span>执行日志</span>
          <button class="logs-toggle" @click="autoScroll = !autoScroll">
            {{ autoScroll ? '🔒 自动滚动' : '🔓 手动滚动' }}
          </button>
        </div>
        <div ref="logsContainer" class="logs-container">
          <div 
            v-for="(log, index) in executionLogs" 
            :key="index" 
            class="log-item"
            :class="log.level"
          >
            <span class="log-time">{{ formatTime(log.timestamp) }}</span>
            <span class="log-level">{{ log.level.toUpperCase() }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
          <div v-if="executionLogs.length === 0" class="logs-empty">
            暂无执行日志
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onUnmounted } from 'vue'

import { executeWorkflow, cancelExecution, getExecutionDetail } from '@/api/workflow'

// Props
const props = defineProps<{
  workflowId: string | null
  nodes: any[]
  connections: any[]
}>()

// Emits
const emit = defineEmits<{
  (e: 'highlight-node', nodeId: string): void
  (e: 'execution-complete', result: any): void
}>()

// 状态
const isExpanded = ref(true)
const isExecuting = ref(false)
const autoScroll = ref(true)
const logsContainer = ref<HTMLElement | null>(null)

// 执行数据
const currentExecution = ref<any>(null)
const nodeStatuses = ref<any[]>([])
const executionLogs = ref<any[]>([])
const pollingTimer = ref<number | null>(null)

// 计算属性
const canExecute = computed(() => {
  return props.workflowId && props.nodes.length > 0
})

const totalNodes = computed(() => props.nodes.length)

const executedNodes = computed(() => {
  return nodeStatuses.value.filter(n => 
    n.status === 'completed' || n.status === 'failed' || n.status === 'skipped'
  ).length
})

const executionProgress = computed(() => {
  if (totalNodes.value === 0) return 0
  return Math.round((executedNodes.value / totalNodes.value) * 100)
})

const executionDuration = computed(() => {
  if (!currentExecution.value) return '0s'
  const start = new Date(currentExecution.value.started_at).getTime()
  const end = currentExecution.value.completed_at 
    ? new Date(currentExecution.value.completed_at).getTime()
    : Date.now()
  const duration = Math.round((end - start) / 1000)
  if (duration < 60) return `${duration}s`
  const minutes = Math.floor(duration / 60)
  const seconds = duration % 60
  return `${minutes}m ${seconds}s`
})

// 方法
function toggleExpand() {
  isExpanded.value = !isExpanded.value
}

async function startExecution() {
  if (!props.workflowId || isExecuting.value) return
  
  isExecuting.value = true
  executionLogs.value = []
  
  // 初始化节点状态
  nodeStatuses.value = props.nodes.map(node => ({
    id: node.id,
    name: node.name,
    type: node.type,
    status: 'pending'
  }))
  
  addLog('info', '开始执行工作流...')
  
  try {
    const response: any = await executeWorkflow(props.workflowId, {})
    const data = response.data || response
    if (data.code === 200 || data.id) {
      const execData = data.data || data
      currentExecution.value = execData
      addLog('info', `执行ID: ${execData.id}`)
      startPolling(execData.id)
    } else {
      addLog('error', `执行失败: ${data.message || '未知错误'}`)
      isExecuting.value = false
    }
  } catch (error: any) {
    addLog('error', `执行出错: ${error.message}`)
    isExecuting.value = false
  }
}

async function stopExecution() {
  if (!currentExecution.value) return
  
  try {
    await cancelExecution(currentExecution.value.id)
    addLog('warn', '执行已取消')
    stopPolling()
    isExecuting.value = false
  } catch (error: any) {
    addLog('error', `取消失败: ${error.message}`)
  }
}

function clearLogs() {
  executionLogs.value = []
  nodeStatuses.value = []
  currentExecution.value = null
}

function startPolling(executionId: string) {
  pollingTimer.value = window.setInterval(async () => {
    try {
      const response: any = await getExecutionDetail(executionId)
      const data = response.data || response
      if (data.code === 200 || data.id) {
        updateExecutionStatus(data.data || data)
      }
    } catch (error) {
      console.error('轮询执行状态失败:', error)
    }
  }, 1000)
}

function stopPolling() {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
}

function updateExecutionStatus(execution: any) {
  currentExecution.value = execution
  
  // 更新节点状态
  if (execution.node_results) {
    for (const [nodeId, result] of Object.entries(execution.node_results as Record<string, any>)) {
      const nodeStatus = nodeStatuses.value.find(n => n.id === nodeId)
      if (nodeStatus) {
        nodeStatus.status = result.status
        if (result.status === 'running') {
          addLog('info', `正在执行节点: ${nodeStatus.name}`)
        } else if (result.status === 'completed') {
          addLog('info', `节点完成: ${nodeStatus.name}`)
        } else if (result.status === 'failed') {
          addLog('error', `节点失败: ${nodeStatus.name} - ${result.error || '未知错误'}`)
        }
      }
    }
  }
  
  // 检查执行是否完成
  if (['completed', 'failed', 'cancelled'].includes(execution.status)) {
    stopPolling()
    isExecuting.value = false
    
    if (execution.status === 'completed') {
      addLog('info', '✅ 工作流执行完成')
    } else if (execution.status === 'failed') {
      addLog('error', `❌ 工作流执行失败: ${execution.error || '未知错误'}`)
    } else {
      addLog('warn', '⚠️ 工作流执行已取消')
    }
    
    emit('execution-complete', execution)
  }
}

function addLog(level: string, message: string) {
  executionLogs.value.push({
    timestamp: new Date(),
    level,
    message
  })
  
  if (autoScroll.value) {
    nextTick(() => {
      if (logsContainer.value) {
        logsContainer.value.scrollTop = logsContainer.value.scrollHeight
      }
    })
  }
}

function highlightNode(nodeId: string) {
  emit('highlight-node', nodeId)
}

function formatTime(date: Date) {
  return date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit' 
  })
}

function getStatusText(status: string) {
  const statusMap: Record<string, string> = {
    pending: '等待中',
    running: '执行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return statusMap[status] || status
}

function getStatusIcon(status: string) {
  const iconMap: Record<string, string> = {
    pending: '⏳',
    running: '🔄',
    completed: '✅',
    failed: '❌',
    skipped: '⏭️'
  }
  return iconMap[status] || '❓'
}

function getNodeIcon(type: string) {
  const iconMap: Record<string, string> = {
    start: '▶',
    end: '⏹',
    condition: '❓',
    loop: '🔄',
    parallel: '⫘',
    api: '🌐',
    database: '🗄',
    script: '📜',
    delay: '⏱',
    notification: '🔔',
    email: '📧'
  }
  return iconMap[type] || '📦'
}

// 清理
onUnmounted(() => {
  stopPolling()
})
</script>


<style scoped>
.execution-monitor {
  position: absolute;
  bottom: 32px;
  left: 300px;
  right: 320px;
  background: #fff;
  z-index: 15;
  transition: all 0.3s;
}

.execution-monitor.expanded {
  height: 280px;
  border-top: 1px solid #e8e8e8;
  box-shadow: 0 -2px 8px rgba(0,0,0,0.06);
}

.execution-monitor.collapsed {
  height: 20px;  /* 保留按钮高度 */
  background: transparent;
  border-top: none;
  overflow: hidden;
}

/* 悬浮展开/收起按钮 - 与左右面板一致的样式 */
.edge-collapse-btn {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  width: 48px;
  height: 20px;
  border: none;
  background: #fff;
  cursor: pointer;
  font-size: 10px;
  color: #8c8c8c;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  box-shadow: 0 -2px 8px rgba(0,0,0,0.1);
  border-radius: 4px 4px 0 0;
}

.edge-collapse-btn:hover {
  background: #1890ff;
  color: #fff;
}

/* 展开状态：按钮在面板顶部外面 */
.execution-monitor.expanded .edge-collapse-btn.bottom {
  top: -20px;
}

/* 收起状态：按钮在面板内部顶部 */
.execution-monitor.collapsed .edge-collapse-btn.bottom {
  top: 0;
}

.monitor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
  user-select: none;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.monitor-icon {
  font-size: 16px;
}

.monitor-title {
  font-weight: 500;
  color: #262626;
}

.execution-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.execution-status.pending { background: #f5f5f5; color: #8c8c8c; }
.execution-status.running { background: #e6f7ff; color: #1890ff; }
.execution-status.completed { background: #f6ffed; color: #52c41a; }
.execution-status.failed { background: #fff2f0; color: #ff4d4f; }
.execution-status.cancelled { background: #fffbe6; color: #faad14; }

.monitor-content {
  display: flex;
  height: calc(100% - 40px);
  overflow: hidden;
}

.execution-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  border-right: 1px solid #f0f0f0;
  width: 100px;
}

.control-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.control-btn.execute {
  background: #52c41a;
  color: #fff;
}
.control-btn.execute:hover:not(:disabled) {
  background: #73d13d;
}

.control-btn.stop {
  background: #ff4d4f;
  color: #fff;
}
.control-btn.stop:hover:not(:disabled) {
  background: #ff7875;
}

.control-btn.clear {
  background: #f5f5f5;
  color: #595959;
}
.control-btn.clear:hover:not(:disabled) {
  background: #e8e8e8;
}

.btn-icon {
  font-size: 12px;
}

.execution-progress {
  padding: 12px;
  border-right: 1px solid #f0f0f0;
  width: 180px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
}

.progress-label {
  color: #595959;
}

.progress-value {
  font-weight: 600;
  color: #1890ff;
}

.progress-bar {
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #1890ff, #52c41a);
  border-radius: 4px;
  transition: width 0.3s;
}

.progress-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #8c8c8c;
}

.node-status-list {
  width: 200px;
  border-right: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
}

.status-header {
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 500;
  color: #595959;
  border-bottom: 1px solid #f0f0f0;
}

.status-items {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.status-item:hover {
  background: #f5f5f5;
}

.status-item.pending { opacity: 0.6; }
.status-item.running { background: #e6f7ff; }
.status-item.completed { background: #f6ffed; }
.status-item.failed { background: #fff2f0; }

.node-icon {
  font-size: 14px;
}

.node-name {
  flex: 1;
  font-size: 12px;
  color: #262626;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.node-status-icon {
  font-size: 12px;
}

.execution-logs {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 500;
  color: #595959;
  border-bottom: 1px solid #f0f0f0;
}

.logs-toggle {
  padding: 2px 8px;
  border: none;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
}

.logs-container {
  flex: 1;
  overflow-y: auto;
  padding: 8px 12px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  background: #fafafa;
}

.log-item {
  display: flex;
  gap: 8px;
  padding: 4px 0;
  border-bottom: 1px solid #f0f0f0;
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  color: #8c8c8c;
  flex-shrink: 0;
}

.log-level {
  width: 50px;
  flex-shrink: 0;
  font-weight: 600;
}

.log-item.info .log-level { color: #1890ff; }
.log-item.warn .log-level { color: #faad14; }
.log-item.error .log-level { color: #ff4d4f; }

.log-message {
  flex: 1;
  color: #262626;
  word-break: break-all;
}

.logs-empty {
  text-align: center;
  color: #8c8c8c;
  padding: 20px;
}

/* 滚动条样式 */
.status-items::-webkit-scrollbar,
.logs-container::-webkit-scrollbar {
  width: 6px;
}

.status-items::-webkit-scrollbar-track,
.logs-container::-webkit-scrollbar-track {
  background: #f5f5f5;
}

.status-items::-webkit-scrollbar-thumb,
.logs-container::-webkit-scrollbar-thumb {
  background: #d9d9d9;
  border-radius: 3px;
}
</style>
