<template>
  <n-modal
    v-model:show="showModal"
    preset="card"
    title="AI 智能助手"
    size="huge"
    :mask-closable="false"
    class="chat-modal"
  >
    <template #header-extra>
      <n-space>
        <n-button size="small" @click="clearChat">
          <template #icon>
            <n-icon><trash-outline /></n-icon>
          </template>
          清空对话
        </n-button>
        <n-button size="small" @click="showModal = false">
          <template #icon>
            <n-icon><close-outline /></n-icon>
          </template>
        </n-button>
      </n-space>
    </template>

    <div class="chat-container">
      <!-- 聊天消息区域 -->
      <div ref="messagesContainer" class="messages-container">
        <div v-if="messages.length === 0" class="welcome-message">
          <n-icon size="48" color="#2080f0">
            <chatbubble-ellipses-outline />
          </n-icon>
          <h3>AI 智能助手</h3>
          <p>我可以帮您分析数据、解答问题、提供建议。请告诉我您需要什么帮助？</p>

          <!-- 快捷问题 -->
          <div class="quick-questions">
            <n-space vertical>
              <n-text strong>常见问题：</n-text>
              <n-space wrap>
                <n-button
                  v-for="question in quickQuestions"
                  :key="question"
                  size="small"
                  ghost
                  @click="sendQuickQuestion(question)"
                >
                  {{ question }}
                </n-button>
              </n-space>
            </n-space>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-for="message in messages" :key="message.id" class="message-item">
          <div :class="['message', message.type]">
            <div class="message-avatar">
              <n-avatar
                :size="32"
                :style="{
                  backgroundColor: message.type === 'user' ? '#2080f0' : '#18a058',
                }"
              >
                <n-icon>
                  <person-outline v-if="message.type === 'user'" />
                  <hardware-chip-outline v-else />
                </n-icon>
              </n-avatar>
            </div>

            <div class="message-content">
              <div class="message-header">
                <n-text strong>
                  {{ message.type === 'user' ? '您' : 'AI助手' }}
                </n-text>
                <n-time :time="message.timestamp" format="HH:mm" />
              </div>

              <div class="message-body">
                <div v-if="message.type === 'ai' && message.typing" class="typing-indicator">
                  <n-spin size="small" />
                  <span>AI正在思考...</span>
                </div>
                <div v-else class="message-text">
                  {{ message.content }}
                </div>

                <!-- AI消息的附加信息 -->
                <div
                  v-if="message.type === 'ai' && message.suggestions"
                  class="message-suggestions"
                >
                  <n-divider style="margin: 12px 0" />
                  <n-text depth="3" style="font-size: 12px">相关建议：</n-text>
                  <n-space vertical size="small" style="margin-top: 8px">
                    <n-button
                      v-for="suggestion in message.suggestions"
                      :key="suggestion"
                      size="tiny"
                      text
                      type="primary"
                      @click="sendQuickQuestion(suggestion)"
                    >
                      {{ suggestion }}
                    </n-button>
                  </n-space>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-container">
        <n-input
          ref="inputRef"
          v-model:value="inputMessage"
          type="textarea"
          placeholder="输入您的问题..."
          :autosize="{ minRows: 1, maxRows: 4 }"
          :disabled="sending"
          @keydown="handleKeydown"
        />
        <n-button
          type="primary"
          :loading="sending"
          :disabled="!inputMessage.trim()"
          @click="sendMessage"
        >
          <template #icon>
            <n-icon><send-outline /></n-icon>
          </template>
          发送
        </n-button>
      </div>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import {
  NModal,
  NSpace,
  NButton,
  NIcon,
  NAvatar,
  NText,
  NTime,
  NInput,
  NDivider,
  NSpin,
  useMessage,
} from 'naive-ui'
import {
  ChatbubbleEllipsesOutline,
  PersonOutline,
  HardwareChipOutline,
  SendOutline,
  TrashOutline,
  CloseOutline,
} from '@vicons/ionicons5'

// Props
const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  analysis: {
    type: Object,
    default: null,
  },
})

// Emits
const emit = defineEmits(['update:show'])

// 响应式数据
const inputMessage = ref('')
const sending = ref(false)
const messages = ref([])
const messagesContainer = ref(null)
const inputRef = ref(null)
const message = useMessage()

// 计算属性
const showModal = computed({
  get: () => props.show,
  set: (value) => emit('update:show', value),
})

// 快捷问题
const quickQuestions = [
  '分析结果如何解读？',
  '发现的异常如何处理？',
  '如何优化设备性能？',
  '预防性维护建议',
  '数据趋势分析',
  '成本效益分析',
]

// 模拟AI回复
const aiResponses = {
  '分析结果如何解读？': {
    content:
      '根据当前分析结果，我为您总结以下几个关键点：\n\n1. **性能指标**：整体设备运行状态良好，但设备001存在温度异常\n2. **效率分析**：生产效率较上周下降8.5%，建议关注生产流程\n3. **异常检测**：发现23个异常点，其中15个为高优先级\n\n建议您重点关注温度异常设备的维护。',
    suggestions: ['设备001具体问题是什么？', '如何提高生产效率？', '异常点详细信息'],
  },
  '发现的异常如何处理？': {
    content:
      '针对发现的异常，我建议按以下优先级处理：\n\n**高优先级异常**：\n- 设备001温度超标：立即检查冷却系统\n- 设备005振动异常：安排紧急维护\n\n**中优先级异常**：\n- 生产效率下降：分析工艺流程\n- 能耗增加：检查设备老化情况\n\n建议建立异常处理标准流程。',
    suggestions: ['如何建立异常处理流程？', '预防性维护计划', '设备更换建议'],
  },
  '如何优化设备性能？': {
    content:
      '基于分析数据，我为您提供以下优化建议：\n\n**短期优化**：\n- 调整设备运行参数\n- 优化维护周期\n- 改进操作流程\n\n**长期优化**：\n- 设备升级改造\n- 引入智能监控\n- 建立预测性维护\n\n预计可提升15-20%的整体效率。',
    suggestions: ['具体参数如何调整？', '维护周期建议', '设备升级方案'],
  },
  预防性维护建议: {
    content:
      '根据设备运行数据分析，我为您制定预防性维护计划：\n\n**日常维护**：\n- 每日检查关键参数\n- 定期清洁和润滑\n\n**周期性维护**：\n- 每周深度检查\n- 每月专业保养\n- 每季度全面检修\n\n**预测性维护**：\n- 基于数据预测故障\n- 提前安排维护计划',
    suggestions: ['维护成本分析', '维护人员培训', '备件管理建议'],
  },
  数据趋势分析: {
    content:
      '通过历史数据分析，我发现以下趋势：\n\n**性能趋势**：\n- 整体性能呈下降趋势（-3.2%/月）\n- 设备老化影响明显\n\n**效率趋势**：\n- 生产效率波动较大\n- 季节性影响显著\n\n**故障趋势**：\n- 故障频率逐月增加\n- 主要集中在关键设备\n\n建议制定针对性改进措施。',
    suggestions: ['如何逆转下降趋势？', '季节性影响应对', '关键设备重点监控'],
  },
  成本效益分析: {
    content:
      '基于当前数据进行成本效益分析：\n\n**当前成本**：\n- 维护成本：¥50,000/月\n- 停机损失：¥120,000/月\n- 能耗成本：¥80,000/月\n\n**优化收益**：\n- 预计减少维护成本20%\n- 降低停机时间30%\n- 节约能耗15%\n\n**投资回报期**：约8-12个月',
    suggestions: ['详细成本分解', '投资方案对比', '风险评估分析'],
  },
}

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || sending.value) return

  const userMessage = {
    id: Date.now(),
    type: 'user',
    content: inputMessage.value.trim(),
    timestamp: new Date(),
  }

  messages.value.push(userMessage)

  const userInput = inputMessage.value.trim()
  inputMessage.value = ''
  sending.value = true

  // 添加AI思考状态
  const aiMessage = {
    id: Date.now() + 1,
    type: 'ai',
    content: '',
    typing: true,
    timestamp: new Date(),
  }

  messages.value.push(aiMessage)

  await nextTick()
  scrollToBottom()

  // 模拟AI回复延迟
  setTimeout(() => {
    const response = getAIResponse(userInput)

    // 更新AI消息
    const messageIndex = messages.value.findIndex((m) => m.id === aiMessage.id)
    if (messageIndex !== -1) {
      messages.value[messageIndex] = {
        ...aiMessage,
        content: response.content,
        suggestions: response.suggestions,
        typing: false,
      }
    }

    sending.value = false
    nextTick(() => scrollToBottom())
  }, 1500 + Math.random() * 1000)
}

// 发送快捷问题
const sendQuickQuestion = (question) => {
  inputMessage.value = question
  sendMessage()
}

// 获取AI回复
const getAIResponse = (input) => {
  // 检查是否有预设回复
  for (const [key, response] of Object.entries(aiResponses)) {
    if (input.includes(key) || key.includes(input)) {
      return response
    }
  }

  // 默认回复
  return {
    content: `感谢您的问题："${input}"。我正在分析相关数据，请稍等...\n\n基于当前分析结果，我建议您：\n1. 查看详细的数据报告\n2. 关注关键性能指标\n3. 制定相应的优化方案\n\n如需更详细的分析，请告诉我具体关注的方面。`,
    suggestions: ['查看详细报告', '性能优化建议', '异常处理方案'],
  }
}

// 处理键盘事件
const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// 清空对话
const clearChat = () => {
  messages.value = []
  message.success('对话已清空')
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 监听模态框显示状态
watch(showModal, (newVal) => {
  if (newVal) {
    nextTick(() => {
      if (inputRef.value) {
        inputRef.value.focus()
      }
    })
  }
})

// 监听分析数据变化
watch(
  () => props.analysis,
  (newAnalysis) => {
    if (newAnalysis && messages.value.length === 0) {
      // 自动添加分析结果介绍消息
      const introMessage = {
        id: Date.now(),
        type: 'ai',
        content: `您好！我已经分析了您的${getAnalysisTypeText(
          newAnalysis.type
        )}结果。\n\n本次分析涵盖了${
          newAnalysis.deviceCount
        }台设备，处理了${newAnalysis.dataPoints.toLocaleString()}个数据点。\n\n我发现了${
          newAnalysis.keyFindings.length
        }个关键问题，并为您准备了${
          newAnalysis.suggestions.length
        }条优化建议。\n\n请告诉我您想了解哪个方面的详细信息？`,
        suggestions: ['关键问题详情', '优化建议说明', '数据趋势分析'],
        timestamp: new Date(),
      }
      messages.value.push(introMessage)
    }
  },
  { immediate: true }
)

// 获取分析类型文本
const getAnalysisTypeText = (type) => {
  const typeMap = {
    comprehensive: '综合分析',
    performance: '性能分析',
    anomaly: '异常检测',
    trend: '趋势分析',
    comparison: '对比分析',
  }
  return typeMap[type] || type
}
</script>

<style scoped>
.chat-modal {
  width: 800px;
  height: 600px;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 500px;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
}

.welcome-message {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.welcome-message h3 {
  margin: 16px 0 8px 0;
  color: #333;
}

.welcome-message p {
  margin-bottom: 24px;
  line-height: 1.6;
}

.quick-questions {
  text-align: left;
  max-width: 400px;
  margin: 0 auto;
}

.message-item {
  margin-bottom: 16px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.message.user {
  margin-left: auto;
  flex-direction: row-reverse;
}

.message.ai {
  margin-right: auto;
}

.message-avatar {
  flex-shrink: 0;
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  font-size: 12px;
}

.message.user .message-header {
  flex-direction: row-reverse;
}

.message-body {
  background: #f8f9fa;
  padding: 12px 16px;
  border-radius: 12px;
  position: relative;
}

.message.user .message-body {
  background: #2080f0;
  color: white;
}

.message-text {
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
  font-style: italic;
}

.message-suggestions {
  margin-top: 8px;
}

.input-container {
  display: flex;
  gap: 12px;
  padding: 16px 0 0 0;
  align-items: flex-end;
}

.input-container .n-input {
  flex: 1;
}
</style>
