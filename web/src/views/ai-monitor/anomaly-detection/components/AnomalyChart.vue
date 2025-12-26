<template>
  <div class="anomaly-chart">
    <div class="chart-header">
      <n-space justify="space-between" align="center">
        <div class="chart-title">
          <n-space align="center">
            <n-icon size="16" color="#f0a020">
              <TrendingUpOutline />
            </n-icon>
            <span>实时异常趋势</span>
          </n-space>
        </div>
        <n-space>
          <n-select
            v-model:value="timeRange"
            :options="timeRangeOptions"
            size="small"
            style="width: 120px"
            @update:value="handleTimeRangeChange"
          />
          <n-button size="small" @click="refreshData">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
          </n-button>
          <n-button size="small" @click="toggleAutoRefresh">
            <template #icon>
              <n-icon><PlayOutline v-if="!autoRefresh" /><PauseOutline v-else /></n-icon>
            </template>
            {{ autoRefresh ? '暂停' : '自动' }}
          </n-button>
        </n-space>
      </n-space>
    </div>

    <div ref="chartRef" :style="{ height: chartHeight + 'px' }"></div>

    <!-- 图表控制面板 -->
    <div class="chart-controls">
      <n-space>
        <n-checkbox-group v-model:value="visibleSeries" @update:value="handleSeriesToggle">
          <n-space>
            <n-checkbox value="anomaly" label="异常数量" />
            <n-checkbox value="threshold" label="阈值线" />
            <n-checkbox value="prediction" label="预测趋势" />
          </n-space>
        </n-checkbox-group>

        <n-divider vertical />

        <n-space>
          <span class="control-label">图表类型:</span>
          <n-radio-group
            v-model:value="chartType"
            size="small"
            @update:value="handleChartTypeChange"
          >
            <n-radio-button value="line">折线图</n-radio-button>
            <n-radio-button value="bar">柱状图</n-radio-button>
            <n-radio-button value="area">面积图</n-radio-button>
          </n-radio-group>
        </n-space>
      </n-space>
    </div>

    <!-- 统计信息 -->
    <div class="chart-stats">
      <n-grid :cols="4" :x-gap="16">
        <n-grid-item>
          <n-statistic label="总异常数" :value="totalAnomalies" tabular-nums>
            <template #prefix>
              <n-icon color="#f0a020"><WarningOutline /></n-icon>
            </template>
          </n-statistic>
        </n-grid-item>
        <n-grid-item>
          <n-statistic label="平均值" :value="averageAnomalies" :precision="1" tabular-nums>
            <template #prefix>
              <n-icon color="#2080f0"><BarChartOutline /></n-icon>
            </template>
          </n-statistic>
        </n-grid-item>
        <n-grid-item>
          <n-statistic label="峰值" :value="maxAnomalies" tabular-nums>
            <template #prefix>
              <n-icon color="#d03050"><TrendingUpOutline /></n-icon>
            </template>
          </n-statistic>
        </n-grid-item>
        <n-grid-item>
          <n-statistic label="趋势" :value="trendDirection" tabular-nums>
            <template #prefix>
              <n-icon :color="trendColor">
                <component :is="trendIcon" />
              </n-icon>
            </template>
          </n-statistic>
        </n-grid-item>
      </n-grid>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useMessage } from 'naive-ui'
import * as echarts from 'echarts'
import {
  TrendingUpOutline,
  TrendingDownOutline,
  RemoveOutline,
  RefreshOutline,
  PlayOutline,
  PauseOutline,
  WarningOutline,
  BarChartOutline,
} from '@vicons/ionicons5'

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
  },
  height: {
    type: Number,
    default: 300,
  },
})

const message = useMessage()

// 响应式数据
const chartRef = ref(null)
const chartHeight = ref(props.height)
const timeRange = ref('1h')
const autoRefresh = ref(true)
const chartType = ref('line')
const visibleSeries = ref(['anomaly', 'threshold'])
let chartInstance = null
let refreshTimer = null

// 时间范围选项
const timeRangeOptions = [
  { label: '1小时', value: '1h' },
  { label: '6小时', value: '6h' },
  { label: '12小时', value: '12h' },
  { label: '24小时', value: '24h' },
  { label: '7天', value: '7d' },
]

// 模拟数据生成
const generateChartData = () => {
  const now = new Date()
  const data = []
  const thresholdData = []
  const predictionData = []

  let timeUnit, dataPoints
  switch (timeRange.value) {
    case '1h':
      timeUnit = 5 * 60 * 1000 // 5分钟
      dataPoints = 12
      break
    case '6h':
      timeUnit = 30 * 60 * 1000 // 30分钟
      dataPoints = 12
      break
    case '12h':
      timeUnit = 60 * 60 * 1000 // 1小时
      dataPoints = 12
      break
    case '24h':
      timeUnit = 2 * 60 * 60 * 1000 // 2小时
      dataPoints = 12
      break
    case '7d':
      timeUnit = 24 * 60 * 60 * 1000 // 1天
      dataPoints = 7
      break
    default:
      timeUnit = 5 * 60 * 1000
      dataPoints = 12
  }

  for (let i = dataPoints - 1; i >= 0; i--) {
    const time = new Date(now.getTime() - i * timeUnit)
    const timeStr = time.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      ...(timeRange.value === '7d' ? { month: '2-digit', day: '2-digit' } : {}),
    })

    // 生成异常数据（模拟真实波动）
    const baseValue = 3
    const variation = Math.sin(i * 0.5) * 2 + Math.random() * 3
    const anomalyCount = Math.max(0, Math.round(baseValue + variation))

    data.push([timeStr, anomalyCount])
    thresholdData.push([timeStr, 8]) // 阈值线

    // 预测数据（未来3个点）
    if (i < 3) {
      const futureTime = new Date(now.getTime() + (3 - i) * timeUnit)
      const futureTimeStr = futureTime.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
      })
      const predictedValue = anomalyCount + Math.random() * 2 - 1
      predictionData.push([futureTimeStr, Math.max(0, Math.round(predictedValue))])
    }
  }

  return { data, thresholdData, predictionData }
}

// 计算统计数据
const chartData = computed(() => generateChartData())

const totalAnomalies = computed(() => {
  return chartData.value.data.reduce((sum, item) => sum + item[1], 0)
})

const averageAnomalies = computed(() => {
  const data = chartData.value.data
  return data.length > 0 ? totalAnomalies.value / data.length : 0
})

const maxAnomalies = computed(() => {
  return Math.max(...chartData.value.data.map((item) => item[1]))
})

const trendDirection = computed(() => {
  const data = chartData.value.data
  if (data.length < 2) return '无数据'

  const recent = data.slice(-3).map((item) => item[1])
  const earlier = data.slice(-6, -3).map((item) => item[1])

  const recentAvg = recent.reduce((a, b) => a + b, 0) / recent.length
  const earlierAvg = earlier.reduce((a, b) => a + b, 0) / earlier.length

  if (recentAvg > earlierAvg * 1.1) return '上升'
  if (recentAvg < earlierAvg * 0.9) return '下降'
  return '平稳'
})

const trendColor = computed(() => {
  switch (trendDirection.value) {
    case '上升':
      return '#d03050'
    case '下降':
      return '#18a058'
    case '平稳':
      return '#2080f0'
    default:
      return '#999'
  }
})

const trendIcon = computed(() => {
  switch (trendDirection.value) {
    case '上升':
      return TrendingUpOutline
    case '下降':
      return TrendingDownOutline
    case '平稳':
      return RemoveOutline
    default:
      return RemoveOutline
  }
})

// 方法
const initChart = () => {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)
  updateChart()

  // 响应式调整
  window.addEventListener('resize', handleResize)
}

const updateChart = () => {
  if (!chartInstance) return

  const { data, thresholdData, predictionData } = chartData.value

  const series = []

  // 异常数量系列
  if (visibleSeries.value.includes('anomaly')) {
    series.push({
      name: '异常数量',
      type: chartType.value,
      data: data,
      smooth: chartType.value === 'line',
      areaStyle: chartType.value === 'area' ? { opacity: 0.3 } : null,
      itemStyle: {
        color: '#f0a020',
      },
      emphasis: {
        focus: 'series',
      },
    })
  }

  // 阈值线
  if (visibleSeries.value.includes('threshold')) {
    series.push({
      name: '阈值线',
      type: 'line',
      data: thresholdData,
      lineStyle: {
        type: 'dashed',
        color: '#d03050',
        width: 2,
      },
      itemStyle: {
        color: '#d03050',
      },
      symbol: 'none',
      emphasis: {
        focus: 'series',
      },
    })
  }

  // 预测趋势
  if (visibleSeries.value.includes('prediction')) {
    series.push({
      name: '预测趋势',
      type: 'line',
      data: predictionData,
      lineStyle: {
        type: 'dotted',
        color: '#722ed1',
        width: 2,
      },
      itemStyle: {
        color: '#722ed1',
      },
      emphasis: {
        focus: 'series',
      },
    })
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985',
        },
      },
      formatter: function (params) {
        let result = `<div style="margin-bottom: 4px;">${params[0].axisValue}</div>`
        params.forEach((param) => {
          result += `<div style="display: flex; align-items: center; margin-bottom: 2px;">
            <span style="display: inline-block; width: 10px; height: 10px; background-color: ${param.color}; border-radius: 50%; margin-right: 8px;"></span>
            <span>${param.seriesName}: ${param.value[1]}</span>
          </div>`
        })
        return result
      },
    },
    legend: {
      data: series.map((s) => s.name),
      top: 10,
      textStyle: {
        fontSize: 12,
      },
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
      boundaryGap: chartType.value === 'bar',
      axisLabel: {
        fontSize: 11,
        rotate: timeRange.value === '7d' ? 45 : 0,
      },
    },
    yAxis: {
      type: 'value',
      name: '异常数量',
      nameTextStyle: {
        fontSize: 11,
      },
      axisLabel: {
        fontSize: 11,
      },
      splitLine: {
        lineStyle: {
          type: 'dashed',
          opacity: 0.5,
        },
      },
    },
    series: series,
    animation: true,
    animationDuration: 1000,
  }

  chartInstance.setOption(option, true)
}

const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

const handleTimeRangeChange = () => {
  updateChart()
  message.info(
    `时间范围已切换到${timeRangeOptions.find((opt) => opt.value === timeRange.value)?.label}`
  )
}

const handleChartTypeChange = () => {
  updateChart()
}

const handleSeriesToggle = () => {
  updateChart()
}

const refreshData = () => {
  updateChart()
  message.success('数据已刷新')
}

const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value

  if (autoRefresh.value) {
    startAutoRefresh()
    message.success('已开启自动刷新')
  } else {
    stopAutoRefresh()
    message.info('已关闭自动刷新')
  }
}

const startAutoRefresh = () => {
  if (refreshTimer) clearInterval(refreshTimer)

  refreshTimer = setInterval(() => {
    if (autoRefresh.value) {
      updateChart()
    }
  }, 30000) // 30秒刷新一次
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 监听数据变化
watch(
  () => props.data,
  () => {
    nextTick(() => {
      updateChart()
    })
  },
  { deep: true }
)

watch(
  () => props.height,
  (newHeight) => {
    chartHeight.value = newHeight
    nextTick(() => {
      handleResize()
    })
  }
)

// 生命周期
onMounted(() => {
  nextTick(() => {
    initChart()
    if (autoRefresh.value) {
      startAutoRefresh()
    }
  })
})

onBeforeUnmount(() => {
  stopAutoRefresh()
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
  }
})
</script>

<style scoped>
.anomaly-chart {
  width: 100%;
}

.chart-header {
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.chart-title {
  font-weight: 500;
  font-size: 14px;
}

.chart-controls {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.control-label {
  font-size: 12px;
  color: #666;
}

.chart-stats {
  margin-top: 16px;
  padding: 16px;
  background-color: #fafafa;
  border-radius: 6px;
}
</style>
