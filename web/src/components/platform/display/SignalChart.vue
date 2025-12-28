<template>
  <n-card class="signal-chart-card" size="small">
    <template #header>
      <div class="chart-header">
        <span class="chart-title">{{ signal.name }}</span>
        <span v-if="signal.unit" class="chart-unit">({{ signal.unit }})</span>
      </div>
    </template>

    <template #header-extra>
      <n-space size="small">
        <n-select
          v-model:value="timeRange"
          :options="timeRangeOptions"
          size="small"
          style="width: 100px"
        />
        <n-button-group size="small">
          <n-button :type="chartType === 'line' ? 'primary' : 'default'" @click="chartType = 'line'">
            折线
          </n-button>
          <n-button :type="chartType === 'area' ? 'primary' : 'default'" @click="chartType = 'area'">
            面积
          </n-button>
        </n-button-group>
      </n-space>
    </template>

    <div class="chart-container" ref="chartRef" :style="{ height: `${height}px` }"></div>

    <!-- 统计信息 -->
    <div v-if="showStats && stats" class="chart-stats">
      <div class="stat-item">
        <span class="stat-label">最小值</span>
        <span class="stat-value">{{ stats.min }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">最大值</span>
        <span class="stat-value">{{ stats.max }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">平均值</span>
        <span class="stat-value">{{ stats.avg }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">当前值</span>
        <span class="stat-value stat-current">{{ stats.current }}</span>
      </div>
    </div>
  </n-card>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { NCard, NSelect, NButton, NButtonGroup, NSpace } from 'naive-ui'
import * as echarts from 'echarts'

// Props
const props = defineProps({
  signal: {
    type: Object,
    required: true
  },
  data: {
    type: Array,
    default: () => []
  },
  height: {
    type: Number,
    default: 200
  },
  showStats: {
    type: Boolean,
    default: true
  }
})

const chartRef = ref(null)
const chartInstance = ref(null)
const chartType = ref('line')
const timeRange = ref('1h')

// 时间范围选项
const timeRangeOptions = [
  { label: '1小时', value: '1h' },
  { label: '6小时', value: '6h' },
  { label: '24小时', value: '24h' },
  { label: '7天', value: '7d' }
]

// 统计信息
const stats = computed(() => {
  if (!props.data || props.data.length === 0) return null

  const values = props.data.map(d => d.value).filter(v => v !== null && v !== undefined)
  if (values.length === 0) return null

  const min = Math.min(...values)
  const max = Math.max(...values)
  const avg = values.reduce((a, b) => a + b, 0) / values.length
  const current = values[values.length - 1]

  return {
    min: min.toFixed(2),
    max: max.toFixed(2),
    avg: avg.toFixed(2),
    current: current.toFixed(2)
  }
})

// 图表配置
const chartOption = computed(() => {
  const xData = props.data.map(d => formatTime(d.timestamp))
  const yData = props.data.map(d => d.value)

  const seriesConfig = {
    name: props.signal.name,
    type: 'line',
    data: yData,
    smooth: true,
    symbol: 'none',
    lineStyle: {
      width: 2,
      color: getSignalColor()
    }
  }

  if (chartType.value === 'area') {
    seriesConfig.areaStyle = {
      color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: getSignalColor(0.4) },
        { offset: 1, color: getSignalColor(0.05) }
      ])
    }
  }

  // 添加阈值线
  const markLines = []
  if (props.signal.value_range) {
    if (props.signal.value_range.min !== undefined) {
      markLines.push({
        yAxis: props.signal.value_range.min,
        lineStyle: { color: '#d03050', type: 'dashed' },
        label: { formatter: '最小值' }
      })
    }
    if (props.signal.value_range.max !== undefined) {
      markLines.push({
        yAxis: props.signal.value_range.max,
        lineStyle: { color: '#d03050', type: 'dashed' },
        label: { formatter: '最大值' }
      })
    }
  }

  if (markLines.length > 0) {
    seriesConfig.markLine = {
      silent: true,
      data: markLines
    }
  }

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const data = params[0]
        return `${data.axisValue}<br/>${props.signal.name}: ${data.value}${props.signal.unit || ''}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xData,
      axisLine: { lineStyle: { color: '#ddd' } },
      axisLabel: { color: '#666', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#eee' } },
      axisLabel: { color: '#666', fontSize: 10 }
    },
    series: [seriesConfig]
  }
})

// 获取信号颜色
function getSignalColor(alpha = 1) {
  const color = props.signal.display_config?.color || '#2080f0'
  if (alpha === 1) return color
  
  // 转换为rgba
  const hex = color.replace('#', '')
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

// 格式化时间
function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 初始化图表
function initChart() {
  if (!chartRef.value) return

  chartInstance.value = echarts.init(chartRef.value)
  chartInstance.value.setOption(chartOption.value)
}

// 更新图表
function updateChart() {
  if (chartInstance.value) {
    chartInstance.value.setOption(chartOption.value)
  }
}

// 调整图表大小
function resizeChart() {
  if (chartInstance.value) {
    chartInstance.value.resize()
  }
}

// 监听数据变化
watch(() => props.data, updateChart, { deep: true })
watch(chartType, updateChart)

// 生命周期
onMounted(() => {
  nextTick(() => {
    initChart()
  })
  window.addEventListener('resize', resizeChart)
})

onUnmounted(() => {
  if (chartInstance.value) {
    chartInstance.value.dispose()
  }
  window.removeEventListener('resize', resizeChart)
})
</script>

<style scoped>
.signal-chart-card {
  height: 100%;
}

.chart-header {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.chart-title {
  font-weight: 600;
  font-size: 14px;
}

.chart-unit {
  font-size: 12px;
  color: var(--n-text-color-3);
}

.chart-container {
  width: 100%;
}

.chart-stats {
  display: flex;
  justify-content: space-around;
  padding-top: 12px;
  border-top: 1px solid var(--n-border-color);
  margin-top: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: 11px;
  color: var(--n-text-color-3);
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--n-text-color);
}

.stat-current {
  color: #2080f0;
}
</style>
