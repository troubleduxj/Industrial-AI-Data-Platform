<template>
  <n-card class="realtime-chart-card" size="small">
    <template #header>
      <div class="chart-header">
        <span class="chart-title">{{ title || '实时数据趋势' }}</span>
        <n-tag v-if="isConnected" type="success" size="small">实时</n-tag>
        <n-tag v-else type="warning" size="small">离线</n-tag>
      </div>
    </template>

    <template #header-extra>
      <n-space size="small">
        <n-select
          v-model:value="selectedSignals"
          :options="signalOptions"
          multiple
          max-tag-count="responsive"
          placeholder="选择信号"
          size="small"
          style="min-width: 150px"
        />
        <n-button-group size="small">
          <n-button :type="chartType === 'line' ? 'primary' : 'default'" @click="chartType = 'line'">
            折线
          </n-button>
          <n-button :type="chartType === 'area' ? 'primary' : 'default'" @click="chartType = 'area'">
            面积
          </n-button>
        </n-button-group>
        <n-button size="small" :disabled="isPaused" @click="togglePause">
          <template #icon>
            <n-icon :component="isPaused ? PlayOutline : PauseOutline" />
          </template>
        </n-button>
      </n-space>
    </template>

    <div class="chart-container" ref="chartRef" :style="{ height: `${height}px` }"></div>

    <!-- 实时统计 -->
    <div v-if="showStats && currentStats" class="chart-stats">
      <div v-for="(stat, key) in currentStats" :key="key" class="stat-item">
        <span class="stat-label">{{ stat.label }}</span>
        <span class="stat-value" :style="{ color: stat.color }">
          {{ formatValue(stat.value) }}
          <span v-if="stat.unit" class="stat-unit">{{ stat.unit }}</span>
        </span>
      </div>
    </div>
  </n-card>
</template>

<script setup>
/**
 * 实时图表组件
 * 
 * 需求: 7.2 - 当收到实时数据时，前端应更新图表和数值显示而无需刷新页面
 */
import { ref, computed, watch, onMounted, onUnmounted, nextTick, toRefs } from 'vue'
import { NCard, NSelect, NButton, NButtonGroup, NSpace, NTag, NIcon } from 'naive-ui'
import { PlayOutline, PauseOutline } from '@vicons/ionicons5'
import * as echarts from 'echarts'

// Props
const props = defineProps({
  title: {
    type: String,
    default: ''
  },
  signals: {
    type: Array,
    default: () => []
  },
  data: {
    type: Array,
    default: () => []
  },
  height: {
    type: Number,
    default: 300
  },
  showStats: {
    type: Boolean,
    default: true
  },
  isConnected: {
    type: Boolean,
    default: false
  },
  maxDataPoints: {
    type: Number,
    default: 60
  },
  displayPrecision: {
    type: Number,
    default: 2
  }
})

const chartRef = ref(null)
const chartInstance = ref(null)
const chartType = ref('line')
const isPaused = ref(false)
const selectedSignals = ref([])

// 内部数据缓存
const dataBuffer = ref([])

// 信号选项
const signalOptions = computed(() => {
  return props.signals.map(s => ({
    label: s.name,
    value: s.code
  }))
})

// 当前统计信息
const currentStats = computed(() => {
  if (!props.data || props.data.length === 0) return null
  
  const stats = {}
  const latestData = props.data[props.data.length - 1]
  
  props.signals.forEach((signal, index) => {
    const values = props.data
      .map(d => d.signals?.[signal.code] ?? d[signal.code])
      .filter(v => v !== null && v !== undefined)
    
    if (values.length > 0) {
      const current = values[values.length - 1]
      const min = Math.min(...values)
      const max = Math.max(...values)
      const avg = values.reduce((a, b) => a + b, 0) / values.length
      
      stats[signal.code] = {
        label: signal.name,
        value: current,
        min,
        max,
        avg,
        unit: signal.unit,
        color: getSignalColor(index)
      }
    }
  })
  
  return Object.keys(stats).length > 0 ? stats : null
})

// 颜色配置
const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4']

function getSignalColor(index) {
  return colors[index % colors.length]
}

// 格式化值
function formatValue(value) {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'number') {
    return value.toFixed(props.displayPrecision)
  }
  return String(value)
}

// 图表配置
function getChartOption() {
  const displaySignals = selectedSignals.value.length > 0 
    ? props.signals.filter(s => selectedSignals.value.includes(s.code))
    : props.signals

  const xData = props.data.map((d, i) => {
    if (d.timestamp) {
      const date = new Date(d.timestamp)
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    }
    return String(i + 1)
  })

  const series = displaySignals.map((signal, index) => {
    const yData = props.data.map(d => d.signals?.[signal.code] ?? d[signal.code] ?? null)
    
    const seriesConfig = {
      name: signal.name,
      type: 'line',
      data: yData,
      smooth: true,
      symbol: 'none',
      lineStyle: {
        width: 2,
        color: getSignalColor(index)
      },
      itemStyle: {
        color: getSignalColor(index)
      }
    }

    if (chartType.value === 'area') {
      seriesConfig.areaStyle = {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: getSignalColor(index) + '80' },
          { offset: 1, color: getSignalColor(index) + '10' }
        ])
      }
    }

    return seriesConfig
  })

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: displaySignals.map(s => s.name),
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
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
    series
  }
}

// 初始化图表
function initChart() {
  if (!chartRef.value) return

  chartInstance.value = echarts.init(chartRef.value)
  updateChart()
}

// 更新图表
function updateChart() {
  if (!chartInstance.value || isPaused.value) return
  chartInstance.value.setOption(getChartOption(), { notMerge: false })
}

// 调整图表大小
function resizeChart() {
  if (chartInstance.value) {
    chartInstance.value.resize()
  }
}

// 切换暂停
function togglePause() {
  isPaused.value = !isPaused.value
  if (!isPaused.value) {
    updateChart()
  }
}

// 监听数据变化
watch(() => props.data, () => {
  if (!isPaused.value) {
    updateChart()
  }
}, { deep: true })

watch(chartType, updateChart)
watch(selectedSignals, updateChart)

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

// 暴露方法
defineExpose({
  updateChart,
  resizeChart,
  togglePause
})
</script>

<style scoped>
.realtime-chart-card {
  height: 100%;
}

.chart-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chart-title {
  font-weight: 600;
  font-size: 14px;
}

.chart-container {
  width: 100%;
}

.chart-stats {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-around;
  padding-top: 12px;
  border-top: 1px solid var(--n-border-color);
  margin-top: 12px;
  gap: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 80px;
}

.stat-label {
  font-size: 11px;
  color: var(--n-text-color-3);
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
}

.stat-unit {
  font-size: 11px;
  font-weight: normal;
  color: var(--n-text-color-3);
}
</style>
