<template>
  <div class="health-trend">
    <n-card title="健康趋势分析" size="small">
      <template #header-extra>
        <n-space>
          <n-select
            v-model:value="timeRange"
            :options="timeRangeOptions"
            size="small"
            style="width: 100px"
            @update:value="handleTimeRangeChange"
          />
          <n-select
            v-model:value="trendType"
            :options="trendTypeOptions"
            size="small"
            style="width: 120px"
            @update:value="handleTrendTypeChange"
          />
          <n-button size="small" @click="refreshData">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
          </n-button>
        </n-space>
      </template>

      <div class="trend-content">
        <!-- 图表区域 -->
        <div ref="chartRef" :style="{ height: chartHeight + 'px' }"></div>

        <!-- 趋势统计 -->
        <div class="trend-stats">
          <n-grid :cols="4" :x-gap="16">
            <n-grid-item>
              <n-statistic label="当前平均分" :value="currentAverage" tabular-nums>
                <template #suffix>/100</template>
                <template #prefix>
                  <n-icon :color="getScoreColor(currentAverage)">
                    <HeartOutline />
                  </n-icon>
                </template>
              </n-statistic>
            </n-grid-item>
            <n-grid-item>
              <n-statistic label="趋势方向" :value="trendDirection" tabular-nums>
                <template #prefix>
                  <n-icon :color="trendColor">
                    <component :is="trendIcon" />
                  </n-icon>
                </template>
              </n-statistic>
            </n-grid-item>
            <n-grid-item>
              <n-statistic label="变化幅度" :value="changeAmount" tabular-nums>
                <template #suffix>分</template>
                <template #prefix>
                  <n-icon :color="changeAmount >= 0 ? '#18a058' : '#d03050'">
                    <component :is="changeAmount >= 0 ? TrendingUpOutline : TrendingDownOutline" />
                  </n-icon>
                </template>
              </n-statistic>
            </n-grid-item>
            <n-grid-item>
              <n-statistic label="预测评分" :value="predictedScore" tabular-nums>
                <template #suffix>/100</template>
                <template #prefix>
                  <n-icon color="#722ed1">
                    <EyeOutline />
                  </n-icon>
                </template>
              </n-statistic>
            </n-grid-item>
          </n-grid>
        </div>

        <!-- 图表控制 -->
        <div class="chart-controls">
          <n-space>
            <n-checkbox-group v-model:value="visibleSeries" @update:value="handleSeriesToggle">
              <n-space>
                <n-checkbox value="historical" label="历史数据" />
                <n-checkbox value="prediction" label="预测数据" />
                <n-checkbox value="average" label="平均线" />
                <n-checkbox value="threshold" label="阈值线" />
              </n-space>
            </n-checkbox-group>

            <n-divider vertical />

            <n-space>
              <span class="control-label">显示模式:</span>
              <n-radio-group
                v-model:value="displayMode"
                size="small"
                @update:value="handleDisplayModeChange"
              >
                <n-radio-button value="line">折线</n-radio-button>
                <n-radio-button value="area">面积</n-radio-button>
                <n-radio-button value="smooth">平滑</n-radio-button>
              </n-radio-group>
            </n-space>
          </n-space>
        </div>

        <!-- 趋势分析 -->
        <div class="trend-analysis">
          <n-alert type="info" :show-icon="false">
            <template #icon>
              <n-icon color="#2080f0">
                <AnalyticsOutline />
              </n-icon>
            </template>
            <template #header>趋势分析</template>
            <div class="analysis-content">
              <div class="analysis-item">
                <span class="analysis-label">整体趋势:</span>
                <span class="analysis-value" :style="{ color: trendColor }">{{
                  trendDescription
                }}</span>
              </div>
              <div class="analysis-item">
                <span class="analysis-label">波动程度:</span>
                <span class="analysis-value" :style="{ color: getVolatilityColor(volatility) }">{{
                  getVolatilityText(volatility)
                }}</span>
              </div>
              <div class="analysis-item">
                <span class="analysis-label">预测置信度:</span>
                <span class="analysis-value" style="color: #722ed1"
                  >{{ predictionConfidence }}%</span
                >
              </div>
              <div class="analysis-item">
                <span class="analysis-label">建议措施:</span>
                <span class="analysis-value" style="color: #f0a020">{{ recommendation }}</span>
              </div>
            </div>
          </n-alert>
        </div>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useMessage } from 'naive-ui'
import * as echarts from 'echarts'
import {
  RefreshOutline,
  AnalyticsOutline,
  HeartOutline,
  TrendingUpOutline,
  TrendingDownOutline,
  RemoveOutline,
  EyeOutline,
} from '@vicons/ionicons5'

const props = defineProps({
  data: {
    type: Object,
    default: () => ({
      dates: [],
      scores: [],
      predictions: [],
    }),
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
const timeRange = ref('30d')
const trendType = ref('overall')
const displayMode = ref('line')
const visibleSeries = ref(['historical', 'prediction', 'average'])
let chartInstance = null

// 选项数据
const timeRangeOptions = [
  { label: '7天', value: '7d' },
  { label: '30天', value: '30d' },
  { label: '90天', value: '90d' },
  { label: '180天', value: '180d' },
]

const trendTypeOptions = [
  { label: '整体趋势', value: 'overall' },
  { label: '设备类型', value: 'device_type' },
  { label: '车间分布', value: 'workshop' },
  { label: '关键指标', value: 'key_metrics' },
]

// 生成图表数据
const generateChartData = () => {
  const now = new Date()
  const dates = []
  const scores = []
  const predictions = []

  // 历史数据天数
  let historicalDays
  switch (timeRange.value) {
    case '7d':
      historicalDays = 7
      break
    case '30d':
      historicalDays = 30
      break
    case '90d':
      historicalDays = 90
      break
    case '180d':
      historicalDays = 180
      break
    default:
      historicalDays = 30
  }

  // 生成历史数据
  for (let i = historicalDays - 1; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
    dates.push(date.toISOString().split('T')[0])

    // 模拟健康评分数据，带有一定的趋势和波动
    const baseScore = 75
    const trendFactor = (historicalDays - i) * 0.1 // 轻微上升趋势
    const randomFactor = (Math.random() - 0.5) * 10
    const score = Math.max(0, Math.min(100, baseScore + trendFactor + randomFactor))
    scores.push(score)
  }

  // 生成预测数据（未来7天）
  const lastScore = scores[scores.length - 1]
  for (let i = 1; i <= 7; i++) {
    const date = new Date(now.getTime() + i * 24 * 60 * 60 * 1000)
    dates.push(date.toISOString().split('T')[0])

    // 预测数据基于最后的评分，加上轻微的改善趋势
    const predictedScore = Math.max(
      0,
      Math.min(100, lastScore + i * 0.5 + (Math.random() - 0.5) * 3)
    )
    predictions.push(predictedScore)
  }

  return { dates, scores, predictions }
}

// 计算属性
const chartData = computed(() => {
  if (props.data && props.data.dates && props.data.dates.length > 0) {
    return props.data
  }
  return generateChartData()
})

const currentAverage = computed(() => {
  const scores = chartData.value.scores
  if (scores.length === 0) return 0
  const sum = scores.reduce((acc, score) => acc + score, 0)
  return Math.round((sum / scores.length) * 10) / 10
})

const trendDirection = computed(() => {
  const scores = chartData.value.scores
  if (scores.length < 2) return '无数据'

  const firstHalf = scores.slice(0, Math.floor(scores.length / 2))
  const secondHalf = scores.slice(Math.floor(scores.length / 2))

  const firstAvg = firstHalf.reduce((acc, score) => acc + score, 0) / firstHalf.length
  const secondAvg = secondHalf.reduce((acc, score) => acc + score, 0) / secondHalf.length

  const change = secondAvg - firstAvg
  if (change > 2) return '上升'
  if (change < -2) return '下降'
  return '稳定'
})

const trendColor = computed(() => {
  switch (trendDirection.value) {
    case '上升':
      return '#18a058'
    case '下降':
      return '#d03050'
    case '稳定':
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
    case '稳定':
      return RemoveOutline
    default:
      return RemoveOutline
  }
})

const changeAmount = computed(() => {
  const scores = chartData.value.scores
  if (scores.length < 2) return 0

  const recent = scores.slice(-7) // 最近7天
  const previous = scores.slice(-14, -7) // 前7天

  if (previous.length === 0) return 0

  const recentAvg = recent.reduce((acc, score) => acc + score, 0) / recent.length
  const previousAvg = previous.reduce((acc, score) => acc + score, 0) / previous.length

  return Math.round((recentAvg - previousAvg) * 10) / 10
})

const predictedScore = computed(() => {
  const predictions = chartData.value.predictions
  if (predictions.length === 0) return 0
  return Math.round(predictions[predictions.length - 1] * 10) / 10
})

const volatility = computed(() => {
  const scores = chartData.value.scores
  if (scores.length < 2) return 0

  const mean = scores.reduce((acc, score) => acc + score, 0) / scores.length
  const variance = scores.reduce((acc, score) => acc + Math.pow(score - mean, 2), 0) / scores.length
  const stdDev = Math.sqrt(variance)

  // 将标准差转换为波动程度等级
  if (stdDev < 3) return 'low'
  if (stdDev < 6) return 'medium'
  return 'high'
})

const predictionConfidence = ref(85.2)

const trendDescription = computed(() => {
  switch (trendDirection.value) {
    case '上升':
      return '设备健康状态持续改善'
    case '下降':
      return '设备健康状态有所下降'
    case '稳定':
      return '设备健康状态保持稳定'
    default:
      return '数据不足'
  }
})

const recommendation = computed(() => {
  if (trendDirection.value === '下降') {
    return '建议加强设备维护和监控'
  } else if (trendDirection.value === '上升') {
    return '继续保持当前维护策略'
  } else {
    return '保持定期监控和维护'
  }
})

// 方法
const getScoreColor = (score) => {
  if (score >= 80) return '#18a058'
  if (score >= 60) return '#f0a020'
  return '#d03050'
}

const getVolatilityColor = (volatility) => {
  switch (volatility) {
    case 'low':
      return '#18a058'
    case 'medium':
      return '#f0a020'
    case 'high':
      return '#d03050'
    default:
      return '#999'
  }
}

const getVolatilityText = (volatility) => {
  switch (volatility) {
    case 'low':
      return '低波动'
    case 'medium':
      return '中等波动'
    case 'high':
      return '高波动'
    default:
      return '未知'
  }
}

const initChart = () => {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)
  updateChart()

  // 响应式调整
  window.addEventListener('resize', handleResize)
}

const updateChart = () => {
  if (!chartInstance) return

  const data = chartData.value
  const series = []

  // 历史数据系列
  if (visibleSeries.value.includes('historical')) {
    series.push({
      name: '历史评分',
      type: 'line',
      data: data.dates
        .slice(0, data.scores.length)
        .map((date, index) => [date, data.scores[index]]),
      smooth: displayMode.value === 'smooth',
      areaStyle: displayMode.value === 'area' ? { opacity: 0.3 } : null,
      itemStyle: {
        color: '#2080f0',
      },
      lineStyle: {
        width: 2,
      },
      symbol: 'circle',
      symbolSize: 4,
    })
  }

  // 预测数据系列
  if (visibleSeries.value.includes('prediction') && data.predictions.length > 0) {
    const predictionStartIndex = data.scores.length
    series.push({
      name: '预测评分',
      type: 'line',
      data: data.dates
        .slice(predictionStartIndex)
        .map((date, index) => [date, data.predictions[index]]),
      smooth: displayMode.value === 'smooth',
      areaStyle: displayMode.value === 'area' ? { opacity: 0.2 } : null,
      itemStyle: {
        color: '#722ed1',
      },
      lineStyle: {
        type: 'dashed',
        width: 2,
      },
      symbol: 'diamond',
      symbolSize: 4,
    })
  }

  // 平均线
  if (visibleSeries.value.includes('average')) {
    const avgValue = currentAverage.value
    series.push({
      name: '平均线',
      type: 'line',
      data: data.dates.map((date) => [date, avgValue]),
      lineStyle: {
        type: 'dotted',
        color: '#18a058',
        width: 2,
      },
      itemStyle: {
        color: '#18a058',
      },
      symbol: 'none',
    })
  }

  // 阈值线
  if (visibleSeries.value.includes('threshold')) {
    series.push({
      name: '健康阈值',
      type: 'line',
      data: data.dates.map((date) => [date, 80]),
      lineStyle: {
        type: 'dotted',
        color: '#f0a020',
        width: 2,
      },
      itemStyle: {
        color: '#f0a020',
      },
      symbol: 'none',
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
            <span style="display: inline-block; width: 10px; height: 10px; background-color: ${
              param.color
            }; border-radius: 50%; margin-right: 8px;"></span>
            <span>${param.seriesName}: ${param.value[1].toFixed(1)}分</span>
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
      boundaryGap: false,
      axisLabel: {
        fontSize: 11,
        formatter: function (value) {
          return value.split('-').slice(1).join('-') // 显示 MM-DD
        },
      },
    },
    yAxis: {
      type: 'value',
      name: '健康评分',
      nameTextStyle: {
        fontSize: 11,
      },
      axisLabel: {
        fontSize: 11,
        formatter: '{value}分',
      },
      splitLine: {
        lineStyle: {
          type: 'dashed',
          opacity: 0.5,
        },
      },
      min: 0,
      max: 100,
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

const handleTrendTypeChange = () => {
  updateChart()
  message.info(
    `趋势类型已切换到${trendTypeOptions.find((opt) => opt.value === trendType.value)?.label}`
  )
}

const handleDisplayModeChange = () => {
  updateChart()
}

const handleSeriesToggle = () => {
  updateChart()
}

const refreshData = () => {
  updateChart()
  predictionConfidence.value = Math.floor(Math.random() * 20) + 75
  message.success('趋势数据已刷新')
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
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
  }
})
</script>

<style scoped>
.health-trend {
  width: 100%;
}

.trend-content {
  padding: 0;
}

.trend-stats {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
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

.trend-analysis {
  margin-top: 16px;
}

.analysis-content {
  margin-top: 8px;
}

.analysis-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 12px;
}

.analysis-label {
  color: #666;
  min-width: 80px;
}

.analysis-value {
  font-weight: 500;
}
</style>
