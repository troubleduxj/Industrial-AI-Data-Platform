<template>
  <div class="prediction-report">
    <n-card title="预测报告" class="report-card">
      <template #header-extra>
        <n-space>
          <n-button size="small" @click="refreshReport">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
            刷新
          </n-button>
          <n-button size="small" @click="exportReport">
            <template #icon>
              <n-icon><DownloadOutline /></n-icon>
            </template>
            导出
          </n-button>
        </n-space>
      </template>

      <n-spin :show="loading">
        <div class="report-content">
          <!-- 报告摘要 -->
          <n-card title="报告摘要" class="summary-section">
            <n-descriptions :column="2" label-placement="left">
              <n-descriptions-item label="生成时间">
                {{ reportData.generateTime }}
              </n-descriptions-item>
              <n-descriptions-item label="预测周期">
                {{ reportData.predictionPeriod }}
              </n-descriptions-item>
              <n-descriptions-item label="设备数量">
                {{ reportData.deviceCount }}
              </n-descriptions-item>
              <n-descriptions-item label="预测准确率">
                <n-tag :type="getAccuracyType(reportData.accuracy)">
                  {{ reportData.accuracy }}%
                </n-tag>
              </n-descriptions-item>
            </n-descriptions>
          </n-card>

          <!-- 趋势分析 -->
          <n-card title="趋势分析" class="trend-section">
            <div class="trend-charts">
              <div ref="trendChartRef" class="chart-container"></div>
            </div>
          </n-card>

          <!-- 风险评估 -->
          <n-card title="风险评估" class="risk-section">
            <n-data-table
              :columns="riskColumns"
              :data="reportData.riskAssessment"
              :pagination="false"
              size="small"
            />
          </n-card>

          <!-- 建议措施 -->
          <n-card title="建议措施" class="recommendations-section">
            <n-list>
              <n-list-item
                v-for="(recommendation, index) in reportData.recommendations"
                :key="index"
              >
                <n-thing>
                  <template #avatar>
                    <n-icon size="20" :color="getRecommendationColor(recommendation.priority)">
                      <BulbOutline />
                    </n-icon>
                  </template>
                  <template #header>
                    {{ recommendation.title }}
                  </template>
                  <template #description>
                    {{ recommendation.description }}
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </n-card>
        </div>
      </n-spin>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, h } from 'vue'
import {
  NCard,
  NButton,
  NIcon,
  NSpace,
  NSpin,
  NDescriptions,
  NDescriptionsItem,
  NTag,
  NDataTable,
  NList,
  NListItem,
  NThing,
  useMessage,
} from 'naive-ui'
import { RefreshOutline, DownloadOutline, BulbOutline } from '@vicons/ionicons5'
import * as echarts from 'echarts'

// Props
const props = defineProps({
  deviceId: {
    type: String,
    default: '',
  },
})

// Reactive data
const loading = ref(false)
const trendChartRef = ref(null)
const message = useMessage()

const reportData = ref({
  generateTime: '2024-01-15 14:30:00',
  predictionPeriod: '未来7天',
  deviceCount: 156,
  accuracy: 92.5,
  riskAssessment: [
    {
      deviceId: 'DEV001',
      deviceName: '设备A',
      riskLevel: '高',
      probability: '85%',
      predictedIssue: '温度异常',
      estimatedTime: '2天内',
    },
    {
      deviceId: 'DEV002',
      deviceName: '设备B',
      riskLevel: '中',
      probability: '65%',
      predictedIssue: '性能下降',
      estimatedTime: '5天内',
    },
  ],
  recommendations: [
    {
      title: '立即检查设备A温度传感器',
      description: '建议在2天内对设备A进行温度传感器检查和校准',
      priority: 'high',
    },
    {
      title: '优化设备B运行参数',
      description: '调整设备B的运行参数以提高性能表现',
      priority: 'medium',
    },
  ],
})

const riskColumns = [
  {
    title: '设备ID',
    key: 'deviceId',
    width: 100,
  },
  {
    title: '设备名称',
    key: 'deviceName',
    width: 120,
  },
  {
    title: '风险等级',
    key: 'riskLevel',
    width: 100,
    render: (row) => {
      const type = row.riskLevel === '高' ? 'error' : row.riskLevel === '中' ? 'warning' : 'success'
      return h(NTag, { type }, { default: () => row.riskLevel })
    },
  },
  {
    title: '发生概率',
    key: 'probability',
    width: 100,
  },
  {
    title: '预测问题',
    key: 'predictedIssue',
    width: 120,
  },
  {
    title: '预计时间',
    key: 'estimatedTime',
    width: 100,
  },
]

// Methods
const getAccuracyType = (accuracy) => {
  if (accuracy >= 90) return 'success'
  if (accuracy >= 80) return 'warning'
  return 'error'
}

const getRecommendationColor = (priority) => {
  switch (priority) {
    case 'high':
      return '#f56565'
    case 'medium':
      return '#ed8936'
    case 'low':
      return '#38a169'
    default:
      return '#4299e1'
  }
}

const initTrendChart = () => {
  if (!trendChartRef.value) return

  const chart = echarts.init(trendChartRef.value)

  const option = {
    title: {
      text: '预测趋势图',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
    },
    legend: {
      data: ['历史数据', '预测数据'],
      top: 30,
    },
    xAxis: {
      type: 'category',
      data: ['Day1', 'Day2', 'Day3', 'Day4', 'Day5', 'Day6', 'Day7'],
    },
    yAxis: {
      type: 'value',
      name: '设备状态评分',
    },
    series: [
      {
        name: '历史数据',
        type: 'line',
        data: [85, 87, 84, 86, 88, 85, 87],
        itemStyle: { color: '#5470c6' },
      },
      {
        name: '预测数据',
        type: 'line',
        data: [87, 85, 82, 80, 78, 75, 73],
        itemStyle: { color: '#fc8452' },
        lineStyle: { type: 'dashed' },
      },
    ],
  }

  chart.setOption(option)

  // 响应式调整
  window.addEventListener('resize', () => {
    chart.resize()
  })
}

const refreshReport = async () => {
  loading.value = true
  try {
    // 模拟API调用
    await new Promise((resolve) => setTimeout(resolve, 1000))
    message.success('报告已刷新')
  } catch (error) {
    message.error('刷新失败')
  } finally {
    loading.value = false
  }
}

const exportReport = () => {
  // 模拟导出功能
  message.success('报告导出成功')
}

// Lifecycle
onMounted(async () => {
  await nextTick()
  initTrendChart()
})
</script>

<style scoped>
.prediction-report {
  padding: 16px;
}

.report-card {
  margin-bottom: 16px;
}

.report-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.summary-section,
.trend-section,
.risk-section,
.recommendations-section {
  margin-bottom: 16px;
}

.chart-container {
  width: 100%;
  height: 300px;
}

.trend-charts {
  padding: 16px 0;
}
</style>
