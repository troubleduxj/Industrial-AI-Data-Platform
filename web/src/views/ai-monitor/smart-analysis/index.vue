<template>
  <div class="smart-analysis">
    <!-- 页面头部 -->
    <div v-permission="{ action: 'read', resource: 'smart_analysis' }" class="page-header">
      <n-space justify="space-between" align="center">
        <div>
          <h2>智能分析</h2>
          <p class="page-description">基于AI的设备数据智能分析和报告生成</p>
        </div>
        <n-space>
          <PermissionButton
            permission="POST /api/v2/ai-monitor/analysis"
            type="primary"
            @click="startNewAnalysis"
          >
            <template #icon>
              <n-icon><analytics-outline /></n-icon>
            </template>
            新建分析
          </PermissionButton>
          <PermissionButton permission="GET /api/v2/ai-monitor/analysis" @click="refreshData">
            <template #icon>
              <n-icon><refresh-outline /></n-icon>
            </template>
            刷新
          </PermissionButton>
        </n-space>
      </n-space>
    </div>

    <!-- 分析概览 -->
    <n-grid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
      <n-grid-item>
        <n-card>
          <n-statistic label="总分析次数" :value="stats.totalAnalysis">
            <template #prefix>
              <n-icon color="#18a058">
                <bar-chart-outline />
              </n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card>
          <n-statistic label="今日分析" :value="stats.todayAnalysis">
            <template #prefix>
              <n-icon color="#2080f0">
                <today-outline />
              </n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card>
          <n-statistic label="异常发现" :value="stats.anomaliesFound">
            <template #prefix>
              <n-icon color="#f0a020">
                <warning-outline />
              </n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card>
          <n-statistic label="报告生成" :value="stats.reportsGenerated">
            <template #prefix>
              <n-icon color="#d03050">
                <document-text-outline />
              </n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 主要内容区域 -->
    <n-grid :cols="3" :x-gap="16" class="main-content">
      <!-- 左侧：分析配置 -->
      <n-grid-item :span="1">
        <n-card title="分析配置" class="config-card">
          <n-form ref="configFormRef" :model="analysisConfig" label-placement="top" size="small">
            <n-form-item label="分析类型">
              <n-select
                v-model:value="analysisConfig.type"
                :options="analysisTypeOptions"
                placeholder="选择分析类型"
              />
            </n-form-item>

            <n-form-item label="设备选择">
              <n-select
                v-model:value="analysisConfig.devices"
                :options="deviceOptions"
                multiple
                placeholder="选择设备"
                max-tag-count="responsive"
              />
            </n-form-item>

            <n-form-item label="时间范围">
              <n-date-picker
                v-model:value="analysisConfig.dateRange"
                type="datetimerange"
                clearable
                style="width: 100%"
              />
            </n-form-item>

            <n-form-item label="分析维度">
              <n-checkbox-group v-model:value="analysisConfig.dimensions">
                <n-space vertical>
                  <n-checkbox value="performance">性能分析</n-checkbox>
                  <n-checkbox value="efficiency">效率分析</n-checkbox>
                  <n-checkbox value="quality">质量分析</n-checkbox>
                  <n-checkbox value="maintenance">维护分析</n-checkbox>
                </n-space>
              </n-checkbox-group>
            </n-form-item>

            <n-form-item>
              <n-button type="primary" block :loading="analyzing" @click="startAnalysis">
                {{ analyzing ? '分析中...' : '开始分析' }}
              </n-button>
            </n-form-item>
          </n-form>
        </n-card>
      </n-grid-item>

      <!-- 中间：分析结果 -->
      <n-grid-item :span="2">
        <n-card title="分析结果" class="result-card">
          <template #header-extra>
            <n-space>
              <n-button size="small" :disabled="!currentAnalysis" @click="exportReport">
                <template #icon>
                  <n-icon><download-outline /></n-icon>
                </template>
                导出报告
              </n-button>
            </n-space>
          </template>

          <div v-if="!currentAnalysis" class="no-analysis">
            <n-empty description="请配置并开始分析" size="large">
              <template #icon>
                <n-icon size="48">
                  <analytics-outline />
                </n-icon>
              </template>
            </n-empty>
          </div>

          <div v-else class="analysis-result">
            <!-- 分析摘要 -->
            <n-card size="small" title="分析摘要" class="summary-card">
              <n-descriptions :column="2" size="small">
                <n-descriptions-item label="分析类型">
                  {{ getAnalysisTypeText(currentAnalysis.type) }}
                </n-descriptions-item>
                <n-descriptions-item label="设备数量">
                  {{ currentAnalysis.deviceCount }}
                </n-descriptions-item>
                <n-descriptions-item label="数据点数">
                  {{ currentAnalysis.dataPoints.toLocaleString() }}
                </n-descriptions-item>
                <n-descriptions-item label="分析时长">
                  {{ currentAnalysis.duration }}秒
                </n-descriptions-item>
              </n-descriptions>
            </n-card>

            <!-- 关键发现 -->
            <n-card size="small" title="关键发现" class="findings-card">
              <n-list>
                <n-list-item v-for="finding in currentAnalysis.keyFindings" :key="finding.id">
                  <n-space align="center">
                    <n-icon
                      :color="
                        finding.level === 'high'
                          ? '#f56565'
                          : finding.level === 'medium'
                          ? '#ed8936'
                          : '#38a169'
                      "
                    >
                      <alert-circle-outline v-if="finding.level === 'high'" />
                      <warning-outline v-else-if="finding.level === 'medium'" />
                      <checkmark-circle-outline v-else />
                    </n-icon>
                    <div>
                      <n-text strong>{{ finding.title }}</n-text>
                      <br />
                      <n-text depth="3" style="font-size: 12px">{{ finding.description }}</n-text>
                    </div>
                  </n-space>
                </n-list-item>
              </n-list>
            </n-card>

            <!-- 数据可视化 -->
            <n-card size="small" title="数据可视化" class="chart-card">
              <div class="chart-container">
                <n-empty description="图表展示区域" size="small" />
              </div>
            </n-card>

            <!-- AI建议 -->
            <n-card size="small" title="AI建议" class="suggestions-card">
              <n-list>
                <n-list-item v-for="suggestion in currentAnalysis.suggestions" :key="suggestion.id">
                  <n-space align="center">
                    <n-icon color="#2080f0">
                      <bulb-outline />
                    </n-icon>
                    <div>
                      <n-text>{{ suggestion.content }}</n-text>
                      <br />
                      <n-text depth="3" style="font-size: 12px"
                        >优先级: {{ suggestion.priority }}</n-text
                      >
                    </div>
                  </n-space>
                </n-list-item>
              </n-list>
            </n-card>
          </div>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 历史分析记录 -->
    <AnalysisHistory
      :analyses="analysisHistory"
      :loading="loading"
      @view="viewAnalysis"
      @delete="deleteAnalysis"
    />

    <!-- 聊天界面 -->
    <ChatInterface v-model:show="showChat" :analysis="currentAnalysis" />

    <!-- 浮动聊天按钮 -->
    <n-button circle type="primary" size="large" class="chat-fab" @click="showChat = true">
      <template #icon>
        <n-icon><chatbubble-outline /></n-icon>
      </template>
    </n-button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  NSpace,
  NButton,
  NIcon,
  NCard,
  NGrid,
  NGridItem,
  NStatistic,
  NForm,
  NFormItem,
  NSelect,
  NDatePicker,
  NCheckboxGroup,
  NCheckbox,
  NEmpty,
  NDescriptions,
  NDescriptionsItem,
  NList,
  NListItem,
  NText,
  useMessage,
} from 'naive-ui'
import {
  AnalyticsOutline,
  RefreshOutline,
  BarChartOutline,
  TodayOutline,
  WarningOutline,
  DocumentTextOutline,
  DownloadOutline,
  AlertCircleOutline,
  CheckmarkCircleOutline,
  BulbOutline,
  ChatbubbleOutline,
} from '@vicons/ionicons5'
import PermissionButton from '@/components/common/PermissionButton.vue'
import AnalysisHistory from './components/AnalysisHistory.vue'
import ChatInterface from './components/ChatInterface.vue'

// 响应式数据
const loading = ref(false)
const analyzing = ref(false)
const showChat = ref(false)
const configFormRef = ref(null)
const currentAnalysis = ref(null)
const analysisHistory = ref([])

// 统计数据
const stats = ref({
  totalAnalysis: 0,
  todayAnalysis: 0,
  anomaliesFound: 0,
  reportsGenerated: 0,
})

// 分析配置
const analysisConfig = ref({
  type: null,
  devices: [],
  dateRange: null,
  dimensions: ['performance'],
})

// 分析类型选项
const analysisTypeOptions = [
  { label: '综合分析', value: 'comprehensive' },
  { label: '性能分析', value: 'performance' },
  { label: '异常检测', value: 'anomaly' },
  { label: '趋势分析', value: 'trend' },
  { label: '对比分析', value: 'comparison' },
]

// 设备选项
const deviceOptions = ref([])

// 消息提示
const message = useMessage()

// 生成模拟设备选项
const generateDeviceOptions = () => {
  const devices = []
  for (let i = 1; i <= 20; i++) {
    devices.push({
      label: `设备${i.toString().padStart(3, '0')}`,
      value: `device_${i}`,
    })
  }
  return devices
}

// 生成模拟分析历史
const generateAnalysisHistory = () => {
  const history = []
  const types = ['comprehensive', 'performance', 'anomaly', 'trend']

  for (let i = 1; i <= 10; i++) {
    history.push({
      id: i,
      name: `分析任务${i}`,
      type: types[i % types.length],
      deviceCount: Math.floor(Math.random() * 10) + 1,
      status: Math.random() > 0.2 ? 'completed' : 'failed',
      createdAt: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
      duration: Math.floor(Math.random() * 300) + 30,
    })
  }

  return history
}

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

// 生成模拟分析结果
const generateAnalysisResult = () => {
  return {
    id: Date.now(),
    type: analysisConfig.value.type,
    deviceCount: analysisConfig.value.devices.length,
    dataPoints: Math.floor(Math.random() * 100000) + 10000,
    duration: Math.floor(Math.random() * 60) + 10,
    keyFindings: [
      {
        id: 1,
        level: 'high',
        title: '设备001温度异常',
        description: '在过去24小时内，设备001的温度超出正常范围15次',
      },
      {
        id: 2,
        level: 'medium',
        title: '生产效率下降',
        description: '整体生产效率较上周下降8.5%',
      },
      {
        id: 3,
        level: 'low',
        title: '维护计划优化',
        description: '建议调整设备005的维护周期',
      },
    ],
    suggestions: [
      {
        id: 1,
        content: '建议立即检查设备001的冷却系统',
        priority: '高',
      },
      {
        id: 2,
        content: '优化生产流程以提高效率',
        priority: '中',
      },
      {
        id: 3,
        content: '制定预防性维护计划',
        priority: '低',
      },
    ],
  }
}

// 开始新分析
const startNewAnalysis = () => {
  // 重置配置
  analysisConfig.value = {
    type: null,
    devices: [],
    dateRange: null,
    dimensions: ['performance'],
  }
  currentAnalysis.value = null
}

// 开始分析
const startAnalysis = async () => {
  if (!analysisConfig.value.type) {
    message.error('请选择分析类型')
    return
  }

  if (analysisConfig.value.devices.length === 0) {
    message.error('请选择至少一个设备')
    return
  }

  analyzing.value = true

  try {
    // 模拟分析过程
    await new Promise((resolve) => setTimeout(resolve, 3000))

    currentAnalysis.value = generateAnalysisResult()

    // 添加到历史记录
    analysisHistory.value.unshift({
      id: Date.now(),
      name: `${getAnalysisTypeText(analysisConfig.value.type)} - ${new Date().toLocaleString()}`,
      type: analysisConfig.value.type,
      deviceCount: analysisConfig.value.devices.length,
      status: 'completed',
      createdAt: new Date().toISOString(),
      duration: currentAnalysis.value.duration,
    })

    // 更新统计数据
    stats.value.totalAnalysis++
    stats.value.todayAnalysis++
    stats.value.anomaliesFound += currentAnalysis.value.keyFindings.filter(
      (f) => f.level === 'high'
    ).length
    stats.value.reportsGenerated++

    message.success('分析完成')
  } catch (error) {
    message.error('分析失败')
  } finally {
    analyzing.value = false
  }
}

// 导出报告
const exportReport = () => {
  if (currentAnalysis.value) {
    message.info('正在生成报告...')
    // 这里可以实现实际的报告导出逻辑
  }
}

// 查看历史分析
const viewAnalysis = (analysis) => {
  // 这里可以加载历史分析的详细结果
  message.info(`查看分析: ${analysis.name}`)
}

// 删除分析记录
const deleteAnalysis = (analysis) => {
  const index = analysisHistory.value.findIndex((a) => a.id === analysis.id)
  if (index !== -1) {
    analysisHistory.value.splice(index, 1)
    message.success('删除成功')
  }
}

// 刷新数据
const refreshData = () => {
  loading.value = true
  setTimeout(() => {
    analysisHistory.value = generateAnalysisHistory()
    loading.value = false
    message.success('数据刷新成功')
  }, 1000)
}

// 组件挂载时初始化数据
onMounted(() => {
  deviceOptions.value = generateDeviceOptions()
  analysisHistory.value = generateAnalysisHistory()

  // 初始化统计数据
  stats.value = {
    totalAnalysis: 156,
    todayAnalysis: 8,
    anomaliesFound: 23,
    reportsGenerated: 89,
  }
})
</script>

<style scoped>
.smart-analysis {
  padding: 16px;
  position: relative;
}

.page-header {
  margin-bottom: 16px;
}

.page-description {
  color: #666;
  margin: 4px 0 0 0;
  font-size: 14px;
}

.stats-grid {
  margin-bottom: 16px;
}

.main-content {
  margin-bottom: 16px;
}

.config-card,
.result-card {
  height: fit-content;
}

.no-analysis {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.analysis-result {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.summary-card,
.findings-card,
.chart-card,
.suggestions-card {
  margin-bottom: 0;
}

.chart-container {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  background-color: #fafafa;
}

.chat-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>
