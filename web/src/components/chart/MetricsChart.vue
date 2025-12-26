<template>
  <n-card :title="title" class="metrics-chart">
    <template #header-extra>
      <n-space>
        <!-- 时间范围选择 -->
        <n-select
          v-model:value="timeRange"
          :options="timeRangeOptions"
          size="small"
          style="width: 120px"
          @update:value="handleTimeRangeChange"
        />

        <!-- 刷新按钮 -->
        <n-button size="small" :loading="loading" @click="handleRefresh">
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
          </template>
        </n-button>

        <!-- 全屏按钮 -->
        <n-button size="small" @click="toggleFullscreen">
          <template #icon>
            <n-icon><ExpandOutline /></n-icon>
          </template>
        </n-button>
      </n-space>
    </template>

    <!-- 图表容器 -->
    <div ref="chartContainer" class="chart-container" :style="{ height: chartHeight + 'px' }">
      <!-- 加载状态 -->
      <div v-if="loading" class="chart-loading">
        <n-spin size="large">
          <template #description>加载中...</template>
        </n-spin>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="error" class="chart-error">
        <n-result status="error" title="图表加载失败" :description="error">
          <template #footer>
            <n-button @click="handleRefresh">重试</n-button>
          </template>
        </n-result>
      </div>

      <!-- 空数据状态 -->
      <div v-else-if="!chartData || chartData.length === 0" class="chart-empty">
        <n-empty description="暂无数据">
          <template #icon>
            <n-icon size="48"><BarChartOutline /></n-icon>
          </template>
        </n-empty>
      </div>

      <!-- 图表 -->
      <div v-else ref="chartElement" class="chart-element"></div>
    </div>

    <!-- 图表说明 -->
    <div v-if="showLegend && legendData.length > 0" class="chart-legend">
      <n-space>
        <div
          v-for="item in legendData"
          :key="item.name"
          class="legend-item"
          @click="toggleSeries(item.name)"
        >
          <div class="legend-color" :style="{ backgroundColor: item.color }"></div>
          <span class="legend-name">{{ item.name }}</span>
          <span v-if="item.value !== undefined" class="legend-value">
            {{ formatValue(item.value, item.unit) }}
          </span>
        </div>
      </n-space>
    </div>
  </n-card>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useMessage } from 'naive-ui'
import * as echarts from 'echarts'
import { RefreshOutline, ExpandOutline, BarChartOutline } from '@vicons/ionicons5'

const props = defineProps({
  // 图表标题
  title: {
    type: String,
    default: '指标图表',
  },
  // 图表类型
  type: {
    type: String,
    default: 'line', // line, bar, pie, gauge, scatter
    validator: (value) => ['line', 'bar', 'pie', 'gauge', 'scatter'].includes(value),
  },
  // 图表数据
  data: {
    type: Array,
    default: () => [],
  },
  // 图表配置
  options: {
    type: Object,
    default: () => ({}),
  },
  // 图表高度
  height: {
    type: Number,
    default: 300,
  },
  // 是否显示图例
  showLegend: {
    type: Boolean,
    default: true,
  },
  // 是否自动刷新
  autoRefresh: {
    type: Boolean,
    default: false,
  },
  // 自动刷新间隔（秒）
  refreshInterval: {
    type: Number,
    default: 30,
  },
  // 加载状态
  loading: {
    type: Boolean,
    default: false,
  },
  // 错误信息
  error: {
    type: String,
    default: '',
  },
  // 时间范围选项
  timeRanges: {
    type: Array,
    default: () => [
      { label: '最近1小时', value: '1h' },
      { label: '最近6小时', value: '6h' },
      { label: '最近24小时', value: '24h' },
      { label: '最近7天', value: '7d' },
      { label: '最近30天', value: '30d' },
    ],
  },
  // 默认时间范围
  defaultTimeRange: {
    type: String,
    default: '1h',
  },
})

const emit = defineEmits([
  'refresh',
  'time-range-change',
  'series-toggle',
  'chart-click',
  'chart-brush',
])

const message = useMessage()
const chartContainer = ref()
const chartElement = ref()
const chart = ref(null)
const timeRange = ref(props.defaultTimeRange)
const refreshTimer = ref(null)
const isFullscreen = ref(false)

// 图表数据
const chartData = computed(() => props.data)

// 图表高度
const chartHeight = computed(() => {
  return isFullscreen.value ? window.innerHeight - 200 : props.height
})

// 时间范围选项
const timeRangeOptions = computed(() => props.timeRanges)

// 图例数据
const legendData = computed(() => {
  if (!chart.value) return []

  const option = chart.value.getOption()
  const series = option.series || []

  return series.map((s, index) => ({
    name: s.name,
    color: s.itemStyle?.color || getDefaultColor(index),
    value: getLatestValue(s.data),
    unit: s.unit || '',
  }))
})

// 监听数据变化
watch(
  () => props.data,
  (newData) => {
    if (chart.value && newData) {
      updateChart()
    }
  },
  { deep: true }
)

// 监听配置变化
watch(
  () => props.options,
  () => {
    if (chart.value) {
      updateChart()
    }
  },
  { deep: true }
)

// 监听高度变化
watch(chartHeight, () => {
  nextTick(() => {
    if (chart.value) {
      chart.value.resize()
    }
  })
})

// 组件挂载
onMounted(() => {
  initChart()
  startAutoRefresh()
  window.addEventListener('resize', handleResize)
})

// 组件卸载
onUnmounted(() => {
  stopAutoRefresh()
  if (chart.value) {
    chart.value.dispose()
  }
  window.removeEventListener('resize', handleResize)
})

// 初始化图表
const initChart = () => {
  if (!chartElement.value) return

  chart.value = echarts.init(chartElement.value)

  // 绑定事件
  chart.value.on('click', (params) => {
    emit('chart-click', params)
  })

  chart.value.on('brush', (params) => {
    emit('chart-brush', params)
  })

  updateChart()
}

// 更新图表
const updateChart = () => {
  if (!chart.value || !chartData.value) return

  const option = generateChartOption()
  chart.value.setOption(option, true)
}

// 生成图表配置
const generateChartOption = () => {
  const baseOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
      formatter: (params) => {
        return formatTooltip(params)
      },
    },
    legend: {
      show: props.showLegend,
      top: 'bottom',
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: props.showLegend ? '15%' : '3%',
      containLabel: true,
    },
    toolbox: {
      feature: {
        saveAsImage: { show: true },
        dataZoom: { show: true },
        brush: { show: true },
        restore: { show: true },
      },
    },
  }

  // 根据图表类型生成特定配置
  let typeSpecificOption = {}

  switch (props.type) {
    case 'line':
      typeSpecificOption = generateLineChartOption()
      break
    case 'bar':
      typeSpecificOption = generateBarChartOption()
      break
    case 'pie':
      typeSpecificOption = generatePieChartOption()
      break
    case 'gauge':
      typeSpecificOption = generateGaugeChartOption()
      break
    case 'scatter':
      typeSpecificOption = generateScatterChartOption()
      break
  }

  // 合并配置
  return {
    ...baseOption,
    ...typeSpecificOption,
    ...props.options,
  }
}

// 生成折线图配置
const generateLineChartOption = () => {
  return {
    xAxis: {
      type: 'category',
      data: chartData.value.map((item) => item.time || item.x),
      boundaryGap: false,
    },
    yAxis: {
      type: 'value',
    },
    series: generateLineSeries(),
  }
}

// 生成柱状图配置
const generateBarChartOption = () => {
  return {
    xAxis: {
      type: 'category',
      data: chartData.value.map((item) => item.name || item.x),
    },
    yAxis: {
      type: 'value',
    },
    series: generateBarSeries(),
  }
}

// 生成饼图配置
const generatePieChartOption = () => {
  return {
    series: [
      {
        type: 'pie',
        radius: '50%',
        data: chartData.value.map((item) => ({
          name: item.name,
          value: item.value,
        })),
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
}

// 生成仪表盘配置
const generateGaugeChartOption = () => {
  const data = chartData.value[0] || {}
  return {
    series: [
      {
        type: 'gauge',
        data: [
          {
            value: data.value || 0,
            name: data.name || '指标',
          },
        ],
        detail: {
          formatter: '{value}%',
        },
      },
    ],
  }
}

// 生成散点图配置
const generateScatterChartOption = () => {
  return {
    xAxis: {
      type: 'value',
    },
    yAxis: {
      type: 'value',
    },
    series: [
      {
        type: 'scatter',
        data: chartData.value.map((item) => [item.x, item.y]),
      },
    ],
  }
}

// 生成折线图系列
const generateLineSeries = () => {
  const seriesMap = new Map()

  chartData.value.forEach((item) => {
    Object.keys(item).forEach((key) => {
      if (key !== 'time' && key !== 'x') {
        if (!seriesMap.has(key)) {
          seriesMap.set(key, {
            name: key,
            type: 'line',
            data: [],
            smooth: true,
            symbol: 'circle',
            symbolSize: 4,
          })
        }
        seriesMap.get(key).data.push(item[key])
      }
    })
  })

  return Array.from(seriesMap.values())
}

// 生成柱状图系列
const generateBarSeries = () => {
  return [
    {
      type: 'bar',
      data: chartData.value.map((item) => item.value || item.y),
    },
  ]
}

// 格式化工具提示
const formatTooltip = (params) => {
  if (!Array.isArray(params)) {
    params = [params]
  }

  let tooltip = `<div>${params[0].axisValueLabel}</div>`

  params.forEach((param) => {
    tooltip += `
      <div style="margin-top: 4px;">
        <span style="display: inline-block; width: 10px; height: 10px; background-color: ${
          param.color
        }; border-radius: 50%; margin-right: 8px;"></span>
        <span>${param.seriesName}: </span>
        <strong>${formatValue(param.value, param.series.unit)}</strong>
      </div>
    `
  })

  return tooltip
}

// 格式化数值
const formatValue = (value, unit = '') => {
  if (typeof value !== 'number') return value

  let formattedValue = value

  if (value >= 1000000) {
    formattedValue = (value / 1000000).toFixed(1) + 'M'
  } else if (value >= 1000) {
    formattedValue = (value / 1000).toFixed(1) + 'K'
  } else {
    formattedValue = value.toFixed(2)
  }

  return formattedValue + (unit ? ' ' + unit : '')
}

// 获取默认颜色
const getDefaultColor = (index) => {
  const colors = [
    '#5470c6',
    '#91cc75',
    '#fac858',
    '#ee6666',
    '#73c0de',
    '#3ba272',
    '#fc8452',
    '#9a60b4',
    '#ea7ccc',
    '#5470c6',
  ]
  return colors[index % colors.length]
}

// 获取最新值
const getLatestValue = (data) => {
  if (!Array.isArray(data) || data.length === 0) return undefined
  return data[data.length - 1]
}

// 处理时间范围变化
const handleTimeRangeChange = (value) => {
  emit('time-range-change', value)
}

// 处理刷新
const handleRefresh = () => {
  emit('refresh')
}

// 切换全屏
const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
}

// 切换系列显示
const toggleSeries = (seriesName) => {
  if (chart.value) {
    chart.value.dispatchAction({
      type: 'legendToggleSelect',
      name: seriesName,
    })
  }
  emit('series-toggle', seriesName)
}

// 处理窗口大小变化
const handleResize = () => {
  if (chart.value) {
    chart.value.resize()
  }
}

// 开始自动刷新
const startAutoRefresh = () => {
  if (props.autoRefresh && props.refreshInterval > 0) {
    refreshTimer.value = setInterval(() => {
      handleRefresh()
    }, props.refreshInterval * 1000)
  }
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

// 暴露方法
defineExpose({
  refresh: handleRefresh,
  toggleFullscreen,
  getChart: () => chart.value,
})
</script>

<style scoped>
.metrics-chart {
  width: 100%;
}

.chart-container {
  position: relative;
  width: 100%;
}

.chart-element {
  width: 100%;
  height: 100%;
}

.chart-loading,
.chart-error,
.chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
}

.chart-legend {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--n-border-color);
}

.legend-item {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.legend-item:hover {
  background-color: var(--n-hover-color);
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 8px;
}

.legend-name {
  margin-right: 8px;
  font-weight: 500;
}

.legend-value {
  color: var(--n-text-color-2);
  font-size: 12px;
}
</style>
