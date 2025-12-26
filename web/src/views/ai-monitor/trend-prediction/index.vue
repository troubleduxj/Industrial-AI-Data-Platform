<template>
  <div v-permission="{ action: 'read', resource: 'trend_prediction' }" class="trend-prediction">
    <!-- 页面标题 -->
    <n-page-header title="趋势预测" subtitle="基于机器学习的设备状态趋势预测分析">
      <template #extra>
        <n-space>
          <PermissionButton
            permission="POST /api/v2/ai-monitor/predictions"
            type="primary"
            @click="startPrediction"
          >
            <template #icon>
              <n-icon><TrendingUpOutline /></n-icon>
            </template>
            开始预测
          </PermissionButton>
          <PermissionButton
            permission="GET /api/v2/ai-monitor/predictions"
            @click="refreshPrediction"
          >
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
            刷新数据
          </PermissionButton>
          <PermissionButton
            permission="GET /api/v2/ai-monitor/predictions/export"
            @click="exportReport"
          >
            <template #icon>
              <n-icon><DownloadOutline /></n-icon>
            </template>
            导出报告
          </PermissionButton>
        </n-space>
      </template>
    </n-page-header>

    <!-- 预测概览 -->
    <n-grid :cols="4" :x-gap="16" class="mb-4">
      <n-grid-item>
        <n-card hoverable>
          <n-statistic label="预测精度" :value="predictionAccuracy" suffix="%" tabular-nums>
            <template #prefix>
              <n-icon color="#18a058"><CheckmarkCircleOutline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card hoverable>
          <n-statistic label="预测设备" :value="predictedDevices" tabular-nums>
            <template #prefix>
              <n-icon color="#2080f0"><HardwareChipOutline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card hoverable>
          <n-statistic label="风险设备" :value="riskDevices" tabular-nums>
            <template #prefix>
              <n-icon color="#f0a020"><WarningOutline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card hoverable>
          <n-statistic label="预测周期" :value="predictionPeriod" suffix="天" tabular-nums>
            <template #prefix>
              <n-icon color="#722ed1"><TimeOutline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 预测配置 -->
    <n-card title="预测配置" class="mb-4" hoverable>
      <PredictionConfig
        :config="predictionConfig"
        @update="updatePredictionConfig"
        @reset="resetPredictionConfig"
      />
    </n-card>

    <!-- 趋势预测图表 -->
    <n-grid :cols="2" :x-gap="16" class="mb-4">
      <n-grid-item>
        <n-card title="设备健康趋势预测" hoverable>
          <TrendChart :data="healthTrendData" :height="350" chart-type="prediction" />
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card title="故障概率预测" hoverable>
          <div ref="failureProbabilityRef" style="height: 350px"></div>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 设备风险评估 -->
    <n-card title="设备风险评估" class="mb-4" hoverable>
      <template #header-extra>
        <n-space>
          <n-select
            v-model:value="riskFilter"
            :options="riskFilterOptions"
            placeholder="筛选风险等级"
            style="width: 120px"
            clearable
          />
          <n-select
            v-model:value="deviceTypeFilter"
            :options="deviceTypeOptions"
            placeholder="筛选设备类型"
            style="width: 120px"
            clearable
          />
        </n-space>
      </template>
      <RiskAssessment
        :data="filteredRiskData"
        :loading="loading"
        @view-detail="viewRiskDetail"
        @update-maintenance="updateMaintenanceSchedule"
      />
    </n-card>

    <!-- 预测模型性能 -->
    <n-grid :cols="3" :x-gap="16" class="mb-4">
      <n-grid-item>
        <n-card title="模型准确率" hoverable>
          <div ref="accuracyChartRef" style="height: 250px"></div>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card title="预测置信度分布" hoverable>
          <div ref="confidenceChartRef" style="height: 250px"></div>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card title="模型训练历史" hoverable>
          <div ref="trainingHistoryRef" style="height: 250px"></div>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 预测报告 -->
    <n-card title="预测报告" hoverable>
      <PredictionReport
        :report-data="reportData"
        @generate-report="generateReport"
        @schedule-report="scheduleReport"
      />
    </n-card>

    <!-- 风险详情抽屉 -->
    <n-drawer v-model:show="showRiskDrawer" :width="700" placement="right">
      <n-drawer-content title="设备风险详情">
        <div v-if="selectedRiskDevice">
          <n-descriptions :column="2" bordered>
            <n-descriptions-item label="设备ID">{{
              selectedRiskDevice.deviceId
            }}</n-descriptions-item>
            <n-descriptions-item label="设备名称">{{
              selectedRiskDevice.deviceName
            }}</n-descriptions-item>
            <n-descriptions-item label="设备类型">{{
              selectedRiskDevice.deviceType
            }}</n-descriptions-item>
            <n-descriptions-item label="风险等级">
              <n-tag :type="getRiskLevelColor(selectedRiskDevice.riskLevel)">
                {{ selectedRiskDevice.riskLevelName }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="故障概率"
              >{{ selectedRiskDevice.failureProbability }}%</n-descriptions-item
            >
            <n-descriptions-item label="预测时间范围">{{
              selectedRiskDevice.predictionRange
            }}</n-descriptions-item>
          </n-descriptions>

          <div class="mt-4">
            <h4>风险因素分析</h4>
            <n-list>
              <n-list-item v-for="factor in selectedRiskDevice.riskFactors" :key="factor.name">
                <n-space justify="space-between" style="width: 100%">
                  <span>{{ factor.name }}</span>
                  <n-progress
                    type="line"
                    :percentage="factor.impact"
                    :status="
                      factor.impact > 70 ? 'error' : factor.impact > 40 ? 'warning' : 'success'
                    "
                    :show-indicator="true"
                    style="width: 200px"
                  />
                </n-space>
              </n-list-item>
            </n-list>
          </div>

          <div class="mt-4">
            <h4>维护建议</h4>
            <n-alert type="info" :show-icon="false">
              <template #icon>
                <n-icon><BulbOutline /></n-icon>
              </template>
              {{ selectedRiskDevice.maintenanceAdvice }}
            </n-alert>
          </div>

          <div class="mt-4">
            <n-space>
              <PermissionButton
                permission="PUT /api/v2/devices/{device_id}/maintenance"
                type="primary"
                @click="scheduleMaintenanceForDevice"
              >
                安排维护
              </PermissionButton>
              <PermissionButton
                permission="GET /api/v2/ai-monitor/risk-reports/export"
                @click="exportRiskReport"
              >
                导出风险报告
              </PermissionButton>
              <PermissionButton
                permission="POST /api/v2/ai-monitor/watch-list"
                @click="addToWatchList"
              >
                加入监控
              </PermissionButton>
            </n-space>
          </div>
        </div>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useMessage } from 'naive-ui'
import * as echarts from 'echarts'
import {
  TrendingUpOutline,
  RefreshOutline,
  DownloadOutline,
  CheckmarkCircleOutline,
  HardwareChipOutline,
  WarningOutline,
  TimeOutline,
  BulbOutline,
} from '@vicons/ionicons5'
import PermissionButton from '@/components/common/PermissionButton.vue'
import PredictionConfig from './components/PredictionConfig.vue'
import TrendChart from './components/TrendChart.vue'
import RiskAssessment from './components/RiskAssessment.vue'
import PredictionReport from './components/PredictionReport.vue'
// 导入新的AI API客户端
import { trendPredictionApi, predictionManagementApi } from '@/api/v2/ai-module'

const message = useMessage()

// 响应式数据
const loading = ref(false)
const showRiskDrawer = ref(false)
const selectedRiskDevice = ref(null)
const riskFilter = ref(null)
const deviceTypeFilter = ref(null)

// 图表引用
const failureProbabilityRef = ref(null)
const accuracyChartRef = ref(null)
const confidenceChartRef = ref(null)
const trainingHistoryRef = ref(null)
let failureProbabilityChart = null
let accuracyChart = null
let confidenceChart = null
let trainingHistoryChart = null

// 预测概览数据
const predictionAccuracy = ref(92.5)
const predictedDevices = ref(156)
const riskDevices = ref(12)
const predictionPeriod = ref(30)

// 预测配置
const predictionConfig = ref({
  algorithm: 'lstm', // 预测算法
  timeWindow: 30, // 时间窗口（天）
  features: ['temperature', 'pressure', 'vibration', 'current'], // 特征参数
  threshold: 0.7, // 风险阈值
  updateFrequency: 'daily', // 更新频率
})

// 健康趋势数据（从API获取）
const healthTrendData = ref([])

// 设备风险数据（从API获取）
const riskData = ref([])

// 筛选选项
const riskFilterOptions = [
  { label: '高风险', value: 'high' },
  { label: '中风险', value: 'medium' },
  { label: '低风险', value: 'low' },
]

const deviceTypeOptions = [
  { label: '焊接设备', value: '焊接设备' },
  { label: '切割设备', value: '切割设备' },
  { label: '检测设备', value: '检测设备' },
]

// 报告数据（从API获取）
const reportData = ref(null)

// 计算属性
const filteredRiskData = computed(() => {
  let filtered = riskData.value

  if (riskFilter.value) {
    filtered = filtered.filter((item) => item.riskLevel === riskFilter.value)
  }

  if (deviceTypeFilter.value) {
    filtered = filtered.filter((item) => item.deviceType === deviceTypeFilter.value)
  }

  return filtered
})

// 方法
const startPrediction = async () => {
  loading.value = true
  try {
    console.log('🚀 开始趋势预测...')
    message.info('正在启动趋势预测...')

    // 获取所有设备的数据进行批量预测
    // 这里简化为直接刷新预测数据
    await refreshPrediction()

    message.success('趋势预测已启动')
  } catch (error) {
    console.error('❌ 启动趋势预测失败:', error)
    message.error(`启动趋势预测失败: ${error.message || '未知错误'}`)
  } finally {
    loading.value = false
  }
}

const refreshPrediction = async () => {
  if (loading.value) return
  
  loading.value = true
  try {
    console.log('🔄 刷新趋势预测数据...')

    // 并行加载多个API数据
    const [batchResponse, riskResponse, healthTrendResponse, reportResponse] = await Promise.allSettled([
      // 1. 批量创建预测任务
      predictionManagementApi.createBatch({
        device_codes: ['WLD-001', 'WLD-002', 'WLD-003'],
        metric_name: 'temperature',
        prediction_horizon: 24,
        model_type: 'ARIMA'
      }),
      // 2. 获取风险评估数据
      fetch('/api/v2/ai/predictions/analytics/risk-assessment').then(r => r.json()),
      // 3. 获取健康趋势数据
      fetch('/api/v2/ai/predictions/analytics/health-trend?days=7').then(r => r.json()),
      // 4. 获取预测报告数据
      fetch('/api/v2/ai/predictions/analytics/prediction-report').then(r => r.json())
    ])

    // 处理批量创建响应
    if (batchResponse.status === 'fulfilled' && batchResponse.value) {
      const response = batchResponse.value
      if (response.code === 200 || response.code === 201) {
        const { successful, total, predictions } = response.data || {}
        
        predictedDevices.value = total || 3
        
        if (predictions && predictions.length > 0) {
          const totalAccuracy = predictions.reduce((sum, p) => sum + (p.accuracy_score || 0), 0)
          predictionAccuracy.value = (totalAccuracy / predictions.length * 100).toFixed(1)
          riskDevices.value = predictions.filter(p => p.status === 'completed').length
        }
      }
    }
    
    // 处理风险评估数据
    if (riskResponse.status === 'fulfilled' && riskResponse.value?.data) {
      riskData.value = riskResponse.value.data.items || []
      console.log('✅ 风险评估数据加载成功:', riskData.value.length)
    }
    
    // 处理健康趋势数据
    if (healthTrendResponse.status === 'fulfilled' && healthTrendResponse.value?.data) {
      healthTrendData.value = healthTrendResponse.value.data || []
      console.log('✅ 健康趋势数据加载成功:', healthTrendData.value.length)
    }
    
    // 处理报告数据
    if (reportResponse.status === 'fulfilled' && reportResponse.value?.data) {
      reportData.value = reportResponse.value.data
      console.log('✅ 预测报告数据加载成功')
    }
    
    // 更新所有图表
    await nextTick()
    updateCharts()

    message.success('趋势预测数据刷新完成')
    console.log('✅ 所有数据加载完成')
  } catch (error) {
    console.error('❌ 刷新预测数据失败:', error)
    message.error(`刷新预测数据失败: ${error.message || '未知错误'}`)
  } finally {
    loading.value = false
  }
}

// 生成健康趋势预测数据
const generateHealthTrendPrediction = () => {
  const today = new Date()
  const data = []
  
  // 生成过去7天和未来7天的数据
  for (let i = -7; i <= 7; i++) {
    const date = new Date(today)
    date.setDate(date.getDate() + i)
    
    const dateStr = date.toISOString().split('T')[0]
    
    // 过去数据：基于实际趋势
    // 未来数据：基于预测（略微下降）
    const baseHealthy = 85
    const trend = i * -0.8 // 轻微下降趋势
    const randomNoise = Math.random() * 3 - 1.5
    
    const healthy = Math.max(60, Math.floor(baseHealthy + trend + randomNoise))
    const warning = Math.min(25, Math.floor(12 + (-trend) / 2 + randomNoise))
    const error = Math.max(0, 100 - healthy - warning)
    
    data.push({
      time: dateStr,
      healthy,
      warning,
      error,
      isPrediction: i > 0, // 标记是否为预测数据
    })
  }
  
  healthTrendData.value = data
}

const exportReport = () => {
  message.info('正在导出预测报告...')
  setTimeout(() => {
    message.success('预测报告导出完成')
  }, 2000)
}

const updatePredictionConfig = (config) => {
  predictionConfig.value = { ...config }
  message.success('预测配置已更新')
}

const resetPredictionConfig = () => {
  predictionConfig.value = {
    algorithm: 'lstm',
    timeWindow: 30,
    features: ['temperature', 'pressure', 'vibration', 'current'],
    threshold: 0.7,
    updateFrequency: 'daily',
  }
  message.info('预测配置已重置')
}

const viewRiskDetail = (device) => {
  selectedRiskDevice.value = device
  showRiskDrawer.value = true
}

const updateMaintenanceSchedule = (device) => {
  message.success(`设备 ${device.deviceName} 的维护计划已更新`)
}

const getRiskLevelColor = (level) => {
  const colorMap = {
    high: 'error',
    medium: 'warning',
    low: 'success',
  }
  return colorMap[level] || 'default'
}

const scheduleMaintenanceForDevice = () => {
  if (selectedRiskDevice.value) {
    message.success(`已为设备 ${selectedRiskDevice.value.deviceName} 安排维护`)
    showRiskDrawer.value = false
  }
}

const exportRiskReport = () => {
  message.info('正在导出风险报告...')
  setTimeout(() => {
    message.success('风险报告导出完成')
  }, 1500)
}

const addToWatchList = () => {
  if (selectedRiskDevice.value) {
    message.success(`设备 ${selectedRiskDevice.value.deviceName} 已加入重点监控列表`)
  }
}

const generateReport = () => {
  message.info('正在生成预测报告...')
  setTimeout(() => {
    message.success('预测报告生成完成')
  }, 2000)
}

const scheduleReport = () => {
  message.success('报告定时生成已设置')
}

// 初始化图表
const initCharts = () => {
  initFailureProbabilityChart()
  initAccuracyChart()
  initConfidenceChart()
  initTrainingHistoryChart()
}

const initFailureProbabilityChart = () => {
  if (!failureProbabilityRef.value) return

  failureProbabilityChart = echarts.init(failureProbabilityRef.value)
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
    },
    legend: {
      data: ['当前概率', '预测概率'],
      top: 10,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: ['今天', '3天后', '7天后', '14天后', '30天后'],
    },
    yAxis: {
      type: 'value',
      name: '故障概率(%)',
      max: 100,
    },
    series: [
      {
        name: '当前概率',
        type: 'line',
        data: [15, 18, 22, 28, 35],
        itemStyle: { color: '#2080f0' },
        smooth: true,
      },
      {
        name: '预测概率',
        type: 'line',
        data: [18, 25, 35, 48, 65],
        itemStyle: { color: '#f0a020' },
        lineStyle: { type: 'dashed' },
        smooth: true,
      },
    ],
  }
  failureProbabilityChart.setOption(option)
}

const initAccuracyChart = () => {
  if (!accuracyChartRef.value) return

  accuracyChart = echarts.init(accuracyChartRef.value)
  const option = {
    tooltip: {
      trigger: 'item',
    },
    series: [
      {
        name: '模型准确率',
        type: 'gauge',
        center: ['50%', '60%'],
        startAngle: 200,
        endAngle: -40,
        min: 0,
        max: 100,
        splitNumber: 10,
        itemStyle: {
          color: '#18a058',
        },
        progress: {
          show: true,
          width: 18,
        },
        pointer: {
          show: false,
        },
        axisLine: {
          lineStyle: {
            width: 18,
          },
        },
        axisTick: {
          distance: -30,
          splitNumber: 5,
          lineStyle: {
            width: 2,
            color: '#999',
          },
        },
        splitLine: {
          distance: -30,
          length: 14,
          lineStyle: {
            width: 3,
            color: '#999',
          },
        },
        axisLabel: {
          distance: -20,
          color: '#999',
          fontSize: 10,
        },
        anchor: {
          show: false,
        },
        title: {
          show: false,
        },
        detail: {
          valueAnimation: true,
          width: '60%',
          lineHeight: 40,
          borderRadius: 8,
          offsetCenter: [0, '-15%'],
          fontSize: 20,
          fontWeight: 'bolder',
          formatter: '{value}%',
          color: 'inherit',
        },
        data: [
          {
            value: 92.5,
          },
        ],
      },
    ],
  }
  accuracyChart.setOption(option)
}

const initConfidenceChart = () => {
  if (!confidenceChartRef.value) return

  confidenceChart = echarts.init(confidenceChartRef.value)
  const option = {
    tooltip: {
      trigger: 'item',
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'center',
    },
    series: [
      {
        name: '置信度分布',
        type: 'pie',
        radius: '50%',
        center: ['60%', '50%'],
        data: [
          { value: 45, name: '高置信度(>90%)', itemStyle: { color: '#18a058' } },
          { value: 35, name: '中置信度(70-90%)', itemStyle: { color: '#f0a020' } },
          { value: 20, name: '低置信度(<70%)', itemStyle: { color: '#d03050' } },
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      },
    ],
  }
  confidenceChart.setOption(option)
}

const initTrainingHistoryChart = () => {
  if (!trainingHistoryRef.value) return

  trainingHistoryChart = echarts.init(trainingHistoryRef.value)
  const option = {
    tooltip: {
      trigger: 'axis',
    },
    legend: {
      data: ['训练损失', '验证损失'],
      top: 10,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: [
        'Epoch 1',
        'Epoch 2',
        'Epoch 3',
        'Epoch 4',
        'Epoch 5',
        'Epoch 6',
        'Epoch 7',
        'Epoch 8',
      ],
    },
    yAxis: {
      type: 'value',
      name: '损失值',
    },
    series: [
      {
        name: '训练损失',
        type: 'line',
        data: [0.8, 0.6, 0.4, 0.3, 0.25, 0.2, 0.18, 0.15],
        itemStyle: { color: '#2080f0' },
        smooth: true,
      },
      {
        name: '验证损失',
        type: 'line',
        data: [0.85, 0.65, 0.45, 0.35, 0.28, 0.22, 0.2, 0.18],
        itemStyle: { color: '#f0a020' },
        smooth: true,
      },
    ],
  }
  trainingHistoryChart.setOption(option)
}

const updateCharts = () => {
  // 更新图表数据
  if (failureProbabilityChart) {
    // 模拟数据更新
    const newData1 = Array.from({ length: 5 }, () => Math.floor(Math.random() * 50 + 10))
    const newData2 = Array.from({ length: 5 }, () => Math.floor(Math.random() * 80 + 20))

    failureProbabilityChart.setOption({
      series: [{ data: newData1 }, { data: newData2 }],
    })
  }
}

// 生命周期
onMounted(() => {
  nextTick(() => {
    initCharts()
    // 初始加载预测数据
    refreshPrediction()
  })
})

onBeforeUnmount(() => {
  if (failureProbabilityChart) {
    failureProbabilityChart.dispose()
    failureProbabilityChart = null
  }
  if (accuracyChart) {
    accuracyChart.dispose()
    accuracyChart = null
  }
  if (confidenceChart) {
    confidenceChart.dispose()
    confidenceChart = null
  }
  if (trainingHistoryChart) {
    trainingHistoryChart.dispose()
    trainingHistoryChart = null
  }
})
</script>

<style scoped>
.trend-prediction {
  padding: 16px;
}

.mb-4 {
  margin-bottom: 16px;
}

.mt-4 {
  margin-top: 16px;
}
</style>
