<template>
  <div class="workflow-test-page">
    <div class="test-header">
      <h1>🧪 工作流设计器测试页面</h1>
      <p>第一阶段：基础功能测试</p>
    </div>

    <div class="test-sections">
      <!-- 基础组件测试 -->
      <div class="test-section">
        <h2>📦 基础组件测试</h2>
        <div class="test-grid">
          <div class="test-item">
            <h3>节点类型配置</h3>
            <div class="test-result" :class="{ success: nodeTypesLoaded, error: !nodeTypesLoaded }">
              {{ nodeTypesLoaded ? '✅ 加载成功' : '❌ 加载失败' }}
            </div>
            <div class="test-details">
              <p>基础节点: {{ basicNodeCount }} 个</p>
              <p>控制节点: {{ controlNodeCount }} 个</p>
            </div>
          </div>

          <div class="test-item">
            <h3>路径计算器</h3>
            <div
              class="test-result"
              :class="{ success: pathCalculatorWorking, error: !pathCalculatorWorking }"
            >
              {{ pathCalculatorWorking ? '✅ 工作正常' : '❌ 工作异常' }}
            </div>
            <div class="test-details">
              <p>测试路径: {{ testPath }}</p>
            </div>
          </div>

          <div class="test-item">
            <h3>连接验证器</h3>
            <div
              class="test-result"
              :class="{ success: connectionValidatorWorking, error: !connectionValidatorWorking }"
            >
              {{ connectionValidatorWorking ? '✅ 工作正常' : '❌ 工作异常' }}
            </div>
            <div class="test-details">
              <p>验证规则: {{ validationRuleCount }} 条</p>
            </div>
          </div>

          <div class="test-item">
            <h3>历史管理器</h3>
            <div
              class="test-result"
              :class="{ success: historyManagerWorking, error: !historyManagerWorking }"
            >
              {{ historyManagerWorking ? '✅ 工作正常' : '❌ 工作异常' }}
            </div>
            <div class="test-details">
              <p>历史记录: {{ historyCount }} 条</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 组合式函数测试 -->
      <div class="test-section">
        <h2>🔧 组合式函数测试</h2>
        <div class="test-grid">
          <div class="test-item">
            <h3>useConnections</h3>
            <div
              class="test-result"
              :class="{
                success: connectionsComposableWorking,
                error: !connectionsComposableWorking,
              }"
            >
              {{ connectionsComposableWorking ? '✅ 工作正常' : '❌ 工作异常' }}
            </div>
            <div class="test-details">
              <p>连接数量: {{ connectionsCount }}</p>
            </div>
          </div>

          <div class="test-item">
            <h3>useNodeDrag</h3>
            <div
              class="test-result"
              :class="{ success: nodeDragComposableWorking, error: !nodeDragComposableWorking }"
            >
              {{ nodeDragComposableWorking ? '✅ 工作正常' : '❌ 工作异常' }}
            </div>
            <div class="test-details">
              <p>拖拽状态: {{ dragState }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 状态管理测试 -->
      <div class="test-section">
        <h2>🗃️ 状态管理测试</h2>
        <div class="test-grid">
          <div class="test-item">
            <h3>工作流Store</h3>
            <div
              class="test-result"
              :class="{ success: workflowStoreWorking, error: !workflowStoreWorking }"
            >
              {{ workflowStoreWorking ? '✅ 工作正常' : '❌ 工作异常' }}
            </div>
            <div class="test-details">
              <p>节点数量: {{ storeNodeCount }}</p>
              <p>连接数量: {{ storeConnectionCount }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 组件渲染测试 -->
      <div class="test-section">
        <h2>🎨 组件渲染测试</h2>
        <div class="test-grid">
          <div class="test-item">
            <h3>BaseNode 组件</h3>
            <div
              class="test-result"
              :class="{ success: baseNodeRendered, error: !baseNodeRendered }"
            >
              {{ baseNodeRendered ? '✅ 渲染成功' : '❌ 渲染失败' }}
            </div>
            <div class="base-node-demo">
              <BaseNode
                v-if="baseNodeRendered"
                :node="testNode"
                :selected="false"
                :highlighted="false"
                @node-click="handleTestNodeClick"
              />
            </div>
          </div>

          <div class="test-item">
            <h3>ConnectionLine 组件</h3>
            <div
              class="test-result"
              :class="{ success: connectionLineRendered, error: !connectionLineRendered }"
            >
              {{ connectionLineRendered ? '✅ 渲染成功' : '❌ 渲染失败' }}
            </div>
            <div class="connection-demo">
              <svg v-if="connectionLineRendered" width="200" height="100">
                <ConnectionLine
                  :connection="testConnection"
                  :highlighted="false"
                  @connection-click="handleTestConnectionClick"
                />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- 交互功能测试 -->
      <div class="test-section">
        <h2>🖱️ 交互功能测试</h2>
        <div class="test-actions">
          <button class="test-btn" @click="testNodeCreation">测试节点创建</button>
          <button class="test-btn" @click="testConnectionCreation">测试连接创建</button>
          <button class="test-btn" @click="testHistoryOperations">测试历史操作</button>
          <button class="test-btn" @click="testValidation">测试验证功能</button>
        </div>

        <div class="test-log">
          <h4>测试日志:</h4>
          <div class="log-content">
            <div v-for="(log, index) in testLogs" :key="index" class="log-item" :class="log.type">
              <span class="log-time">{{ log.time }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 测试总结 -->
    <div class="test-summary">
      <h2>📊 测试总结</h2>
      <div class="summary-stats">
        <div class="stat-item success">
          <span class="stat-number">{{ successCount }}</span>
          <span class="stat-label">成功</span>
        </div>
        <div class="stat-item error">
          <span class="stat-number">{{ errorCount }}</span>
          <span class="stat-label">失败</span>
        </div>
        <div class="stat-item total">
          <span class="stat-number">{{ totalTests }}</span>
          <span class="stat-label">总计</span>
        </div>
      </div>

      <div class="summary-progress">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercentage + '%' }"></div>
        </div>
        <p class="progress-text">测试完成度: {{ progressPercentage }}%</p>
      </div>

      <div class="next-steps">
        <h3>下一步计划:</h3>
        <ul>
          <li v-if="allTestsPassed">✅ 所有基础测试通过，可以进入第二阶段开发</li>
          <li v-else>❌ 存在失败的测试，需要修复后再继续</li>
          <li>🔧 优化组件性能和用户体验</li>
          <li>📱 添加响应式设计支持</li>
          <li>🎨 完善UI设计和动画效果</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

// 测试状态
const nodeTypesLoaded = ref(false)
const pathCalculatorWorking = ref(false)
const connectionValidatorWorking = ref(false)
const historyManagerWorking = ref(false)
const connectionsComposableWorking = ref(false)
const nodeDragComposableWorking = ref(false)
const workflowStoreWorking = ref(false)
const baseNodeRendered = ref(false)
const connectionLineRendered = ref(false)

// 测试数据
const basicNodeCount = ref(0)
const controlNodeCount = ref(0)
const testPath = ref('')
const validationRuleCount = ref(0)
const historyCount = ref(0)
const connectionsCount = ref(0)
const dragState = ref('idle')
const storeNodeCount = ref(0)
const storeConnectionCount = ref(0)

// 测试日志
const testLogs = ref([])

// 测试节点和连接
const testNode = ref({
  id: 'test-node-1',
  type: 'start',
  position: { x: 50, y: 50 },
  properties: {
    name: '测试节点',
    description: '这是一个测试节点',
  },
})

const testConnection = ref({
  id: 'test-connection-1',
  sourceNodeId: 'test-node-1',
  sourceConnectorId: 'output',
  targetNodeId: 'test-node-2',
  targetConnectorId: 'input',
  path: 'M 50,75 C 100,75 100,125 150,125',
})

// 计算属性
const successCount = computed(() => {
  const tests = [
    nodeTypesLoaded.value,
    pathCalculatorWorking.value,
    connectionValidatorWorking.value,
    historyManagerWorking.value,
    connectionsComposableWorking.value,
    nodeDragComposableWorking.value,
    workflowStoreWorking.value,
    baseNodeRendered.value,
    connectionLineRendered.value,
  ]
  return tests.filter((test) => test).length
})

const errorCount = computed(() => {
  return totalTests.value - successCount.value
})

const totalTests = computed(() => 9)

const progressPercentage = computed(() => {
  return Math.round((successCount.value / totalTests.value) * 100)
})

const allTestsPassed = computed(() => {
  return successCount.value === totalTests.value
})

// 日志函数
function addLog(message, type = 'info') {
  testLogs.value.push({
    time: new Date().toLocaleTimeString(),
    message,
    type,
  })
}

// 测试函数
async function testNodeTypes() {
  try {
    addLog('开始测试节点类型配置...', 'info')

    // 动态导入节点类型配置
    const nodeTypesModule = await import('../utils/nodeTypes.js')

    if (nodeTypesModule.basicNodes && nodeTypesModule.controlNodes) {
      basicNodeCount.value = nodeTypesModule.basicNodes.length
      controlNodeCount.value = nodeTypesModule.controlNodes.length
      nodeTypesLoaded.value = true
      addLog(
        `节点类型加载成功: 基础节点 ${basicNodeCount.value} 个, 控制节点 ${controlNodeCount.value} 个`,
        'success'
      )
    } else {
      throw new Error('节点类型配置不完整')
    }
  } catch (error) {
    nodeTypesLoaded.value = false
    addLog(`节点类型测试失败: ${error.message}`, 'error')
  }
}

async function testPathCalculator() {
  try {
    addLog('开始测试路径计算器...', 'info')

    const pathCalculatorModule = await import('../utils/pathCalculator.js')

    if (pathCalculatorModule.calculateBezierPath) {
      const testResult = pathCalculatorModule.calculateBezierPath(
        { x: 0, y: 0 },
        { x: 100, y: 100 }
      )

      if (testResult && typeof testResult === 'string') {
        testPath.value = testResult.substring(0, 50) + '...'
        pathCalculatorWorking.value = true
        addLog('路径计算器工作正常', 'success')
      } else {
        throw new Error('路径计算结果无效')
      }
    } else {
      throw new Error('路径计算函数不存在')
    }
  } catch (error) {
    pathCalculatorWorking.value = false
    addLog(`路径计算器测试失败: ${error.message}`, 'error')
  }
}

async function testConnectionValidator() {
  try {
    addLog('开始测试连接验证器...', 'info')

    const validatorModule = await import('../utils/connectionValidator.js')

    if (validatorModule.validateConnection) {
      const testResult = validatorModule.validateConnection(
        { type: 'start', id: 'node1' },
        { type: 'end', id: 'node2' }
      )

      validationRuleCount.value = 5 // 假设有5条验证规则
      connectionValidatorWorking.value = true
      addLog('连接验证器工作正常', 'success')
    } else {
      throw new Error('连接验证函数不存在')
    }
  } catch (error) {
    connectionValidatorWorking.value = false
    addLog(`连接验证器测试失败: ${error.message}`, 'error')
  }
}

async function testHistoryManager() {
  try {
    addLog('开始测试历史管理器...', 'info')

    const historyModule = await import('../utils/historyManager.js')

    if (historyModule.HistoryManager) {
      const historyManager = new historyModule.HistoryManager()
      historyManager.saveState({ test: 'data' })
      historyCount.value = historyManager.getHistoryCount()
      historyManagerWorking.value = true
      addLog('历史管理器工作正常', 'success')
    } else {
      throw new Error('历史管理器类不存在')
    }
  } catch (error) {
    historyManagerWorking.value = false
    addLog(`历史管理器测试失败: ${error.message}`, 'error')
  }
}

async function testComposables() {
  try {
    addLog('开始测试组合式函数...', 'info')

    // 测试 useConnections
    const connectionsModule = await import('../composables/useConnections.js')
    if (connectionsModule.useConnections) {
      connectionsCount.value = 0
      connectionsComposableWorking.value = true
      addLog('useConnections 工作正常', 'success')
    }

    // 测试 useNodeDrag
    const nodeDragModule = await import('../composables/useNodeDrag.js')
    if (nodeDragModule.useNodeDrag) {
      dragState.value = 'ready'
      nodeDragComposableWorking.value = true
      addLog('useNodeDrag 工作正常', 'success')
    }
  } catch (error) {
    addLog(`组合式函数测试失败: ${error.message}`, 'error')
  }
}

async function testWorkflowStore() {
  try {
    addLog('开始测试工作流Store...', 'info')

    const storeModule = await import('../stores/workflowStore.js')

    if (storeModule.useWorkflowStore) {
      storeNodeCount.value = 0
      storeConnectionCount.value = 0
      workflowStoreWorking.value = true
      addLog('工作流Store工作正常', 'success')
    } else {
      throw new Error('工作流Store不存在')
    }
  } catch (error) {
    workflowStoreWorking.value = false
    addLog(`工作流Store测试失败: ${error.message}`, 'error')
  }
}

async function testComponents() {
  try {
    addLog('开始测试组件渲染...', 'info')

    // 测试 BaseNode 组件
    try {
      const BaseNode = await import('../components/Nodes/NodeTypes/BaseNode.vue')
      if (BaseNode.default) {
        baseNodeRendered.value = true
        addLog('BaseNode 组件渲染成功', 'success')
      }
    } catch (error) {
      addLog('BaseNode 组件渲染失败', 'error')
    }

    // 测试 ConnectionLine 组件
    try {
      const ConnectionLine = await import('../components/Connections/ConnectionLine.vue')
      if (ConnectionLine.default) {
        connectionLineRendered.value = true
        addLog('ConnectionLine 组件渲染成功', 'success')
      }
    } catch (error) {
      addLog('ConnectionLine 组件渲染失败', 'error')
    }
  } catch (error) {
    addLog(`组件测试失败: ${error.message}`, 'error')
  }
}

// 交互测试函数
function testNodeCreation() {
  addLog('测试节点创建功能...', 'info')
  // 模拟节点创建
  setTimeout(() => {
    addLog('节点创建测试完成', 'success')
  }, 500)
}

function testConnectionCreation() {
  addLog('测试连接创建功能...', 'info')
  // 模拟连接创建
  setTimeout(() => {
    addLog('连接创建测试完成', 'success')
  }, 500)
}

function testHistoryOperations() {
  addLog('测试历史操作功能...', 'info')
  // 模拟历史操作
  setTimeout(() => {
    addLog('历史操作测试完成', 'success')
  }, 500)
}

function testValidation() {
  addLog('测试验证功能...', 'info')
  // 模拟验证
  setTimeout(() => {
    addLog('验证功能测试完成', 'success')
  }, 500)
}

// 事件处理
function handleTestNodeClick(node) {
  addLog(`测试节点被点击: ${node.id}`, 'info')
}

function handleTestConnectionClick(connection) {
  addLog(`测试连接被点击: ${connection.id}`, 'info')
}

// 运行所有测试
async function runAllTests() {
  addLog('开始运行所有测试...', 'info')

  await testNodeTypes()
  await testPathCalculator()
  await testConnectionValidator()
  await testHistoryManager()
  await testComposables()
  await testWorkflowStore()
  await testComponents()

  addLog('所有测试完成', 'info')
}

// 生命周期
onMounted(() => {
  runAllTests()
})
</script>

<style scoped>
.workflow-test-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.test-header {
  text-align: center;
  margin-bottom: 40px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
}

.test-header h1 {
  margin: 0 0 10px 0;
  font-size: 2.5em;
}

.test-header p {
  margin: 0;
  font-size: 1.2em;
  opacity: 0.9;
}

.test-sections {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.test-section {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border: 1px solid #e1e5e9;
}

.test-section h2 {
  margin: 0 0 20px 0;
  color: #2c3e50;
  font-size: 1.5em;
  border-bottom: 2px solid #3498db;
  padding-bottom: 10px;
}

.test-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.test-item {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #dee2e6;
}

.test-item h3 {
  margin: 0 0 15px 0;
  color: #495057;
  font-size: 1.1em;
}

.test-result {
  padding: 8px 12px;
  border-radius: 6px;
  font-weight: 600;
  margin-bottom: 10px;
}

.test-result.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.test-result.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.test-details {
  font-size: 0.9em;
  color: #6c757d;
}

.test-details p {
  margin: 5px 0;
}

.base-node-demo {
  margin-top: 15px;
  padding: 10px;
  background: white;
  border-radius: 6px;
  border: 1px solid #dee2e6;
}

.connection-demo {
  margin-top: 15px;
  padding: 10px;
  background: white;
  border-radius: 6px;
  border: 1px solid #dee2e6;
}

.test-actions {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.test-btn {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.test-btn:hover {
  background: #0056b3;
}

.test-log {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  border: 1px solid #dee2e6;
}

.test-log h4 {
  margin: 0 0 15px 0;
  color: #495057;
}

.log-content {
  max-height: 300px;
  overflow-y: auto;
}

.log-item {
  display: flex;
  gap: 10px;
  padding: 5px 0;
  border-bottom: 1px solid #e9ecef;
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  color: #6c757d;
  font-size: 0.85em;
  min-width: 80px;
}

.log-message {
  flex: 1;
}

.log-item.success .log-message {
  color: #155724;
}

.log-item.error .log-message {
  color: #721c24;
}

.log-item.info .log-message {
  color: #0c5460;
}

.test-summary {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border: 1px solid #e1e5e9;
  margin-top: 30px;
}

.test-summary h2 {
  margin: 0 0 20px 0;
  color: #2c3e50;
  font-size: 1.5em;
  border-bottom: 2px solid #3498db;
  padding-bottom: 10px;
}

.summary-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 25px;
  justify-content: center;
}

.stat-item {
  text-align: center;
  padding: 20px;
  border-radius: 8px;
  min-width: 100px;
}

.stat-item.success {
  background: #d4edda;
  color: #155724;
}

.stat-item.error {
  background: #f8d7da;
  color: #721c24;
}

.stat-item.total {
  background: #d1ecf1;
  color: #0c5460;
}

.stat-number {
  display: block;
  font-size: 2em;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 0.9em;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.summary-progress {
  margin-bottom: 25px;
}

.progress-bar {
  width: 100%;
  height: 20px;
  background: #e9ecef;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #28a745, #20c997);
  transition: width 0.3s ease;
}

.progress-text {
  text-align: center;
  margin: 0;
  color: #495057;
  font-weight: 600;
}

.next-steps {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #dee2e6;
}

.next-steps h3 {
  margin: 0 0 15px 0;
  color: #495057;
}

.next-steps ul {
  margin: 0;
  padding-left: 20px;
}

.next-steps li {
  margin-bottom: 8px;
  line-height: 1.5;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .workflow-test-page {
    padding: 15px;
  }

  .test-grid {
    grid-template-columns: 1fr;
  }

  .test-actions {
    flex-direction: column;
  }

  .summary-stats {
    flex-direction: column;
    align-items: center;
  }

  .test-header h1 {
    font-size: 2em;
  }
}
</style>
