<template>
  <div class="score-distribution">
    <n-card title="健康评分分布" size="small">
      <template #header-extra>
        <n-space>
          <n-select
            v-model:value="chartType"
            :options="chartTypeOptions"
            size="small"
            style="width: 100px"
            @update:value="handleChartTypeChange"
          />
          <n-button size="small" @click="refreshData">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
          </n-button>
        </n-space>
      </template>

      <div class="distribution-content">
        <!-- 图表区域 -->
        <div ref="chartRef" :style="{ height: chartHeight + 'px' }"></div>

        <!-- 统计信息 -->
        <div class="distribution-stats">
          <n-grid :cols="5" :x-gap="12">
            <n-grid-item v-for="item in distributionData" :key="item.range">
              <div class="stat-item">
                <div class="stat-header">
                  <span class="score-range">{{ item.range }}分</span>
                  <n-tag :color="getScoreRangeColor(item.range)" size="small">
                    {{ item.percentage }}%
                  </n-tag>
                </div>
                <div class="stat-content">
                  <div class="device-count">{{ item.count }}台设备</div>
                  <n-progress
                    :percentage="item.percentage"
                    :color="getScoreRangeColor(item.range)"
                    :height="4"
                    :show-indicator="false"
                  />
                </div>
                <div class="stat-trend">
                  <n-space align="center" size="small">
                    <n-icon
                      :color="
                        item.trend === 'up' ? '#18a058' : item.trend === 'down' ? '#d03050' : '#666'
                      "
                      size="12"
                    >
                      <component :is="getTrendIcon(item.trend)" />
                    </n-icon>
                    <span class="trend-text">{{ getTrendText(item.trend) }}</span>
                  </n-space>
                </div>
              </div>
            </n-grid-item>
          </n-grid>
        </div>

        <!-- 详细分析 -->
        <div class="distribution-analysis">
          <n-alert type="info" :show-icon="false">
            <template #icon>
              <n-icon color="#2080f0">
                <AnalyticsOutline />
              </n-icon>
            </template>
            <template #header>分布分析</template>
            <div class="analysis-content">
              <div class="analysis-item">
                <span class="analysis-label">健康设备占比:</span>
                <span class="analysis-value" style="color: #18a058">{{ healthyPercentage }}%</span>
                <span class="analysis-desc">(评分≥80分)</span>
              </div>
              <div class="analysis-item">
                <span class="analysis-label">需关注设备:</span>
                <span class="analysis-value" style="color: #f0a020">{{ warningPercentage }}%</span>
                <span class="analysis-desc">(评分60-79分)</span>
              </div>
              <div class="analysis-item">
                <span class="analysis-label">异常设备:</span>
                <span class="analysis-value" style="color: #d03050">{{ errorPercentage }}%</span>
                <span class="analysis-desc">(评分<60分)</span>
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
  TrendingUpOutline,
  TrendingDownOutline,
  RemoveOutline,
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
const chartType = ref('pie')
let chartInstance = null

// 图表类型选项
const chartTypeOptions = [
  { label: '饼图', value: 'pie' },
  { label: '柱状图', value: 'bar' },
  { label: '环形图', value: 'doughnut' },
]

// 分布数据（包含趋势信息）
const distributionData = ref([
  { range: '90-100', count: 15, percentage: 25, trend: 'up', change: '+2' },
  { range: '80-89', count: 20, percentage: 33.3, trend: 'stable', change: '0' },
  { range: '70-79', count: 15, percentage: 25, trend: 'down', change: '-1' },
  { range: '60-69', count: 7, percentage: 11.7, trend: 'down', change: '-3' },
  { range: '0-59', count: 3, percentage: 5, trend: 'up', change: '+1' },
])

// 计算属性
const healthyPercentage = computed(() => {
  const healthy = distributionData.value
    .filter((item) => item.range === '90-100' || item.range === '80-89')
    .reduce((sum, item) => sum + item.percentage, 0)
  return healthy.toFixed(1)
})

const warningPercentage = computed(() => {
  const warning = distributionData.value
    .filter((item) => item.range === '70-79' || item.range === '60-69')
    .reduce((sum, item) => sum + item.percentage, 0)
  return warning.toFixed(1)
})

const errorPercentage = computed(() => {
  const error = distributionData.value
    .filter((item) => item.range === '0-59')
    .reduce((sum, item) => sum + item.percentage, 0)
  return error.toFixed(1)
})

// 方法
const getScoreRangeColor = (range) => {
  switch (range) {
    case '90-100':
      return '#18a058'
    case '80-89':
      return '#36ad6a'
    case '70-79':
      return '#f0a020'
    case '60-69':
      return '#d03050'
    case '0-59':
      return '#722ed1'
    default:
      return '#999'
  }
}

const getTrendIcon = (trend) => {
  switch (trend) {
    case 'up':
      return TrendingUpOutline
    case 'down':
      return TrendingDownOutline
    case 'stable':
      return RemoveOutline
    default:
      return RemoveOutline
  }
}

const getTrendText = (trend) => {
  switch (trend) {
    case 'up':
      return '上升'
    case 'down':
      return '下降'
    case 'stable':
      return '稳定'
    default:
      return '无变化'
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

  const data = distributionData.value.map((item) => ({
    name: `${item.range}分`,
    value: item.count,
    percentage: item.percentage,
    itemStyle: {
      color: getScoreRangeColor(item.range),
    },
  }))

  let option = {}

  if (chartType.value === 'pie' || chartType.value === 'doughnut') {
    option = {
      tooltip: {
        trigger: 'item',
        formatter: function (params) {
          return `${params.name}<br/>设备数量: ${params.value}台<br/>占比: ${params.data.percentage}%`
        },
      },
      legend: {
        orient: 'horizontal',
        bottom: '5%',
        textStyle: {
          fontSize: 12,
        },
      },
      series: [
        {
          name: '健康评分分布',
          type: 'pie',
          radius: chartType.value === 'doughnut' ? ['40%', '70%'] : '65%',
          center: ['50%', '45%'],
          data: data,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
          label: {
            show: true,
            formatter: function (params) {
              return `${params.data.percentage}%`
            },
            fontSize: 11,
          },
          labelLine: {
            show: true,
          },
        },
      ],
    }
  } else if (chartType.value === 'bar') {
    option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
        formatter: function (params) {
          const param = params[0]
          return `${param.name}<br/>设备数量: ${param.value}台<br/>占比: ${param.data.percentage}%`
        },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '10%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: data.map((item) => item.name),
        axisLabel: {
          fontSize: 11,
          interval: 0,
          rotate: 0,
        },
      },
      yAxis: {
        type: 'value',
        name: '设备数量(台)',
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
      series: [
        {
          name: '设备数量',
          type: 'bar',
          data: data.map((item) => ({
            value: item.value,
            percentage: item.percentage,
            itemStyle: {
              color: item.itemStyle.color,
            },
          })),
          barWidth: '60%',
          label: {
            show: true,
            position: 'top',
            formatter: function (params) {
              return `${params.data.percentage}%`
            },
            fontSize: 10,
          },
        },
      ],
    }
  }

  chartInstance.setOption(option, true)
}

const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

const handleChartTypeChange = () => {
  updateChart()
  message.info(
    `已切换到${chartTypeOptions.find((opt) => opt.value === chartType.value)?.label}模式`
  )
}

const refreshData = () => {
  // 模拟数据刷新
  distributionData.value = distributionData.value.map((item) => ({
    ...item,
    count: Math.floor(Math.random() * 20) + 5,
    percentage: Math.floor(Math.random() * 30) + 10,
    trend: ['up', 'down', 'stable'][Math.floor(Math.random() * 3)],
  }))

  // 重新计算百分比
  const total = distributionData.value.reduce((sum, item) => sum + item.count, 0)
  distributionData.value = distributionData.value.map((item) => ({
    ...item,
    percentage: parseFloat(((item.count / total) * 100).toFixed(1)),
  }))

  updateChart()
  message.success('分布数据已刷新')
}

// 监听数据变化
watch(
  () => props.data,
  () => {
    if (props.data && props.data.length > 0) {
      distributionData.value = props.data
    }
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
.score-distribution {
  width: 100%;
}

.distribution-content {
  padding: 0;
}

.distribution-stats {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.stat-item {
  text-align: center;
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.score-range {
  font-size: 12px;
  font-weight: 500;
  color: #333;
}

.stat-content {
  margin-bottom: 8px;
}

.device-count {
  font-size: 11px;
  color: #666;
  margin-bottom: 4px;
}

.stat-trend {
  display: flex;
  justify-content: center;
}

.trend-text {
  font-size: 10px;
  color: #666;
}

.distribution-analysis {
  margin-top: 20px;
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
  min-width: 40px;
}

.analysis-desc {
  color: #999;
  font-size: 11px;
}
</style>
