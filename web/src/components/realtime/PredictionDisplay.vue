<template>
  <n-card class="prediction-display-card" size="small">
    <template #header>
      <div class="prediction-header">
        <span class="prediction-title">{{ title || 'AI预测结果' }}</span>
        <n-tag v-if="isRealtime" type="success" size="small">实时</n-tag>
      </div>
    </template>

    <template #header-extra>
      <n-space size="small">
        <n-select
          v-model:value="selectedModel"
          :options="modelOptions"
          placeholder="选择模型"
          size="small"
          clearable
          style="width: 150px"
        />
        <n-button size="small" @click="$emit('refresh')">
          <template #icon>
            <n-icon :component="RefreshOutline" />
          </template>
        </n-button>
      </n-space>
    </template>

    <!-- 无数据状态 -->
    <div v-if="!prediction" class="empty-prediction">
      <n-empty description="暂无预测数据" />
    </div>

    <!-- 预测结果展示 -->
    <div v-else class="prediction-content">
      <!-- 主要预测值 -->
      <div class="prediction-main">
        <div class="prediction-value-container">
          <div class="prediction-label">预测值</div>
          <div class="prediction-value" :style="{ color: getPredictionColor() }">
            {{ formatValue(prediction.predicted_value) }}
            <span v-if="prediction.unit" class="prediction-unit">{{ prediction.unit }}</span>
          </div>
          <div v-if="prediction.target_time" class="prediction-target">
            预测时间: {{ formatTime(prediction.target_time) }}
          </div>
        </div>

        <!-- 置信度指示器 -->
        <div class="confidence-container">
          <div class="confidence-label">置信度</div>
          <n-progress
            type="circle"
            :percentage="confidencePercentage"
            :color="getConfidenceColor()"
            :stroke-width="8"
            :show-indicator="true"
          >
            <span class="confidence-value">{{ confidencePercentage }}%</span>
          </n-progress>
        </div>
      </div>

      <!-- 异常检测 -->
      <div v-if="prediction.is_anomaly !== undefined" class="anomaly-section">
        <n-alert 
          :type="prediction.is_anomaly ? 'error' : 'success'" 
          :title="prediction.is_anomaly ? '检测到异常' : '状态正常'"
          :show-icon="true"
        >
          <template v-if="prediction.is_anomaly && prediction.anomaly_score">
            异常分数: {{ formatValue(prediction.anomaly_score) }}
          </template>
        </n-alert>
      </div>

      <!-- 预测详情 -->
      <div v-if="showDetails && prediction.prediction_details" class="prediction-details">
        <n-collapse>
          <n-collapse-item title="预测详情" name="details">
            <n-descriptions :column="2" label-placement="left" size="small">
              <n-descriptions-item label="模型ID">
                {{ prediction.model_id || '-' }}
              </n-descriptions-item>
              <n-descriptions-item label="模型版本">
                {{ prediction.model_version || '-' }}
              </n-descriptions-item>
              <n-descriptions-item label="预测时间">
                {{ formatTime(prediction.prediction_time) }}
              </n-descriptions-item>
              <n-descriptions-item label="目标时间">
                {{ formatTime(prediction.target_time) }}
              </n-descriptions-item>
              <n-descriptions-item v-if="prediction.actual_value !== undefined" label="实际值">
                <span :class="{ 'value-match': isValueMatch, 'value-mismatch': !isValueMatch }">
                  {{ formatValue(prediction.actual_value) }}
                </span>
              </n-descriptions-item>
              <n-descriptions-item v-if="prediction.actual_value !== undefined" label="偏差">
                {{ formatValue(predictionError) }} ({{ formatValue(predictionErrorPercent) }}%)
              </n-descriptions-item>
            </n-descriptions>

            <!-- 输入特征 -->
            <div v-if="prediction.input_data" class="input-features">
              <div class="section-title">输入特征</div>
              <n-data-table
                :columns="inputColumns"
                :data="inputFeatures"
                :bordered="false"
                size="small"
                :max-height="200"
              />
            </div>
          </n-collapse-item>
        </n-collapse>
      </div>

      <!-- 历史趋势 -->
      <div v-if="showTrend && predictionHistory.length > 0" class="prediction-trend">
        <div class="section-title">预测趋势</div>
        <div ref="trendChartRef" style="height: 150px;"></div>
      </div>

      <!-- 更新时间 -->
      <div class="prediction-footer">
        <span>更新时间: {{ formatTime(prediction.timestamp || prediction.prediction_time) }}</span>
      </div>
    </div>
  </n-card>
</template>

<script setup>
/**
 * 预测结果显示组件
 * 
 * 需求: 7.3 - 当预测结果产生时，前端应在监控面板中显示预测值和置信度
 */
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { 
  NCard, NTag, NSpace, NSelect, NButton, NIcon, NEmpty, NProgress, 
  NAlert, NCollapse, NCollapseItem, NDescriptions, NDescriptionsItem, NDataTable 
} from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'
import * as echarts from 'echarts'

// Props
const props = defineProps({
  title: {
    type: String,
    default: ''
  },
  prediction: {
    type: Object,
    default: null
  },
  models: {
    type: Array,
    default: () => []
  },
  predictionHistory: {
    type: Array,
    default: () => []
  },
  isRealtime: {
    type: Boolean,
    default: false
  },
  showDetails: {
    type: Boolean,
    default: true
  },
  showTrend: {
    type: Boolean,
    default: true
  },
  displayPrecision: {
    type: Number,
    default: 2
  }
})

// Emits
const emit = defineEmits(['refresh', 'model-change'])

const selectedModel = ref(null)
const trendChartRef = ref(null)
let trendChart = null

// 模型选项
const modelOptions = computed(() => {
  return props.models.map(m => ({
    label: m.name,
    value: m.id
  }))
})

// 置信度百分比
const confidencePercentage = computed(() => {
  if (!props.prediction?.confidence) return 0
  return Math.round(props.prediction.confidence * 100)
})

// 预测误差
const predictionError = computed(() => {
  if (!props.prediction?.actual_value || props.prediction.actual_value === null) return null
  return props.prediction.predicted_value - props.prediction.actual_value
})

// 预测误差百分比
const predictionErrorPercent = computed(() => {
  if (predictionError.value === null || !props.prediction?.actual_value) return null
  if (props.prediction.actual_value === 0) return 0
  return (predictionError.value / props.prediction.actual_value) * 100
})

// 值是否匹配（误差在5%以内）
const isValueMatch = computed(() => {
  if (predictionErrorPercent.value === null) return true
  return Math.abs(predictionErrorPercent.value) <= 5
})

// 输入特征列
const inputColumns = [
  { title: '特征名', key: 'name', width: 120 },
  { title: '值', key: 'value' }
]

// 输入特征数据
const inputFeatures = computed(() => {
  if (!props.prediction?.input_data) return []
  return Object.entries(props.prediction.input_data).map(([name, value]) => ({
    name,
    value: formatValue(value)
  }))
})

// 格式化值
function formatValue(value) {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'number') {
    return value.toFixed(props.displayPrecision)
  }
  return String(value)
}

// 格式化时间
function formatTime(timestamp) {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 获取预测值颜色
function getPredictionColor() {
  if (!props.prediction) return '#333'
  if (props.prediction.is_anomaly) return '#d03050'
  if (confidencePercentage.value >= 80) return '#18a058'
  if (confidencePercentage.value >= 60) return '#f0a020'
  return '#d03050'
}

// 获取置信度颜色
function getConfidenceColor() {
  if (confidencePercentage.value >= 80) return '#18a058'
  if (confidencePercentage.value >= 60) return '#f0a020'
  return '#d03050'
}

// 初始化趋势图
function initTrendChart() {
  if (!trendChartRef.value || props.predictionHistory.length === 0) return

  trendChart = echarts.init(trendChartRef.value)
  updateTrendChart()
}

// 更新趋势图
function updateTrendChart() {
  if (!trendChart) return

  const xData = props.predictionHistory.map(p => {
    const date = new Date(p.timestamp || p.prediction_time)
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  })

  const predictedData = props.predictionHistory.map(p => p.predicted_value)
  const actualData = props.predictionHistory.map(p => p.actual_value)
  const confidenceData = props.predictionHistory.map(p => (p.confidence || 0) * 100)

  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['预测值', '实际值', '置信度'],
      bottom: 0,
      textStyle: { fontSize: 10 }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '20%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xData,
      axisLabel: { fontSize: 10 }
    },
    yAxis: [
      {
        type: 'value',
        name: '值',
        axisLabel: { fontSize: 10 }
      },
      {
        type: 'value',
        name: '置信度%',
        min: 0,
        max: 100,
        axisLabel: { fontSize: 10 }
      }
    ],
    series: [
      {
        name: '预测值',
        type: 'line',
        data: predictedData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { color: '#5470c6' },
        itemStyle: { color: '#5470c6' }
      },
      {
        name: '实际值',
        type: 'line',
        data: actualData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { color: '#91cc75', type: 'dashed' },
        itemStyle: { color: '#91cc75' }
      },
      {
        name: '置信度',
        type: 'line',
        yAxisIndex: 1,
        data: confidenceData,
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#fac858', width: 1 },
        areaStyle: { color: 'rgba(250, 200, 88, 0.1)' }
      }
    ]
  }

  trendChart.setOption(option)
}

// 调整图表大小
function resizeChart() {
  if (trendChart) {
    trendChart.resize()
  }
}

// 监听模型选择变化
watch(selectedModel, (newVal) => {
  emit('model-change', newVal)
})

// 监听历史数据变化
watch(() => props.predictionHistory, () => {
  nextTick(() => {
    if (trendChart) {
      updateTrendChart()
    } else {
      initTrendChart()
    }
  })
}, { deep: true })

// 生命周期
onMounted(() => {
  nextTick(() => {
    initTrendChart()
  })
  window.addEventListener('resize', resizeChart)
})

onUnmounted(() => {
  if (trendChart) {
    trendChart.dispose()
  }
  window.removeEventListener('resize', resizeChart)
})

// 暴露方法
defineExpose({
  updateTrendChart,
  resizeChart
})
</script>

<style scoped>
.prediction-display-card {
  height: 100%;
}

.prediction-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.prediction-title {
  font-weight: 600;
  font-size: 14px;
}

.empty-prediction {
  padding: 40px 0;
}

.prediction-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.prediction-main {
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 16px;
  background: var(--n-color-hover);
  border-radius: 8px;
}

.prediction-value-container {
  text-align: center;
}

.prediction-label {
  font-size: 12px;
  color: var(--n-text-color-3);
  margin-bottom: 8px;
}

.prediction-value {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
}

.prediction-unit {
  font-size: 14px;
  font-weight: normal;
  color: var(--n-text-color-3);
  margin-left: 4px;
}

.prediction-target {
  font-size: 11px;
  color: var(--n-text-color-3);
  margin-top: 8px;
}

.confidence-container {
  text-align: center;
}

.confidence-label {
  font-size: 12px;
  color: var(--n-text-color-3);
  margin-bottom: 8px;
}

.confidence-value {
  font-size: 14px;
  font-weight: 600;
}

.anomaly-section {
  margin-top: 8px;
}

.prediction-details {
  margin-top: 8px;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--n-text-color-2);
  margin: 12px 0 8px;
}

.input-features {
  margin-top: 12px;
}

.prediction-trend {
  margin-top: 8px;
}

.prediction-footer {
  font-size: 11px;
  color: var(--n-text-color-3);
  text-align: right;
  padding-top: 8px;
  border-top: 1px solid var(--n-border-color);
}

.value-match {
  color: #18a058;
}

.value-mismatch {
  color: #d03050;
}
</style>
