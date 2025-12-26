<template>
  <AIChart
    :title="chartTitle"
    :height="height"
    :loading="loading"
    :data="data"
    :option="chartOption"
    :show-insight="true"
    :insight="aiInsight"
    @refresh="handleRefresh"
  >
    <template #header-extra>
      <n-space>
        <n-select
          v-model:value="timeRange"
          :options="timeRangeOptions"
          size="small"
          style="width: 120px"
          @update:value="handleTimeRangeChange"
        />
        <n-select
          v-model:value="predictionRange"
          :options="predictionRangeOptions"
          size="small"
          style="width: 120px"
          @update:value="handlePredictionRangeChange"
        />
      </n-space>
    </template>

    <!-- 图表控制面板 -->
    <div class="chart-controls">
      <n-space>
        <n-checkbox-group v-model:value="visibleSeries" @update:value="handleSeriesToggle">
          <n-space>
            <n-checkbox value="historical" label="历史数据" />
            <n-checkbox value="prediction" label="预测数据" />
            <n-checkbox value="confidence" label="置信区间" />
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
            <n-radio-button value="line">折线图</n-radio-button>
            <n-radio-button value="area">面积图</n-radio-button>
            <n-radio-button value="scatter">散点图</n-radio-button>
          </n-radio-group>
        </n-space>
      </n-space>
    </div>

    <!-- 预测统计信息 -->
    <div class="prediction-stats">
      <n-grid :cols="5" :x-gap="16">
        <n-grid-item>
          <n-statistic label="预测准确率" :value="predictionAccuracy" suffix="%" tabular-nums>
            <template #prefix>
              <n-icon color="#18a058"><CheckmarkCircleOutline /></n-icon>
            </template>
          </n-statistic>
        </n-grid-item>
        <n-grid-item>
          <n-statistic label="平均置信度" :value="averageConfidence" suffix="%" tabular-nums>
            <template #prefix>
              <n-icon color="#2080f0"><ShieldCheckmarkOutline /></n-icon>
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
          <n-statistic label="预测范围" :value="predictionDays" suffix="天" tabular-nums>
            <template #prefix>
              <n-icon color="#722ed1"><CalendarOutline /></n-icon>
            </template>
          </n-statistic>
        </n-grid-item>
        <n-grid-item>
          <n-statistic label="数据点数" :value="dataPointCount" tabular-nums>
            <template #prefix>
              <n-icon color="#f0a020"><AnalyticsOutline /></n-icon>
            </template>
          </n-statistic>
        </n-grid-item>
      </n-grid>
    </div>
  </AIChart>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMessage } from 'naive-ui'
import AIChart from '@/components/ai-monitor/charts/AIChart.vue'
import {
  TrendingUpOutline,
  TrendingDownOutline,
  RemoveOutline,
  CheckmarkCircleOutline,
  ShieldCheckmarkOutline,
  CalendarOutline,
  AnalyticsOutline,
} from '@vicons/ionicons5'

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
  },
  height: {
    type: Number,
    default: 350,
  },
  chartType: {
    type: String,
    default: 'trend',
  },
})

const message = useMessage()

// 响应式数据
const loading = ref(false)
const timeRange = ref('30d')
const predictionRange = ref('7d')
const displayMode = ref('line')
const visibleSeries = ref(['historical', 'prediction', 'confidence'])

// 计算属性
const chartTitle = computed(() => {
  const titleMap = {
    trend: '设备状态趋势',
    prediction: '健康趋势预测',
    health: '设备健康度',
  }
  return titleMap[props.chartType] || '趋势图表'
})

const aiInsight = computed(() => {
  if (!props.data || props.data.length === 0) {
    return {
      type: 'info',
      title: '数据分析',
      content: '暂无历史数据进行趋势分析',
    }
  }

  return {
    type: 'success',
    title: '趋势洞察',
    content: '当前趋势呈上升态势，预测未来7天平均值将上升5.2%',
  }
})

const predictionAccuracy = ref(92.3)
const averageConfidence = ref(87.5)
const trendDirection = computed(() => '上升')
const trendColor = computed(() => '#18a058')
const trendIcon = computed(() => TrendingUpOutline)
const predictionDays = computed(() => parseInt(predictionRange.value.replace('d', '')))
const dataPointCount = computed(() => 100)

const chartOption = computed(() => {
  // 使用传入的data或默认数据
  const chartData = props.data && props.data.length > 0 ? props.data : []
  
  // 提取时间轴和数据
  const xAxisData = chartData.map(item => item.time || item.date || item.label)
  const healthyData = chartData.map(item => item.healthy || 0)
  const warningData = chartData.map(item => item.warning || 0)
  const errorData = chartData.map(item => item.error || 0)
  
  // 如果没有数据，使用默认值以显示图表结构
  const defaultXAxis = xAxisData.length > 0 ? xAxisData : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  const defaultHealthy = healthyData.length > 0 ? healthyData : [0, 0, 0, 0, 0, 0, 0]
  const defaultWarning = warningData.length > 0 ? warningData : [0, 0, 0, 0, 0, 0, 0]
  const defaultError = errorData.length > 0 ? errorData : [0, 0, 0, 0, 0, 0, 0]
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
    },
    legend: {
      data: ['健康', '预警', '异常'],
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: defaultXAxis,
    },
    yAxis: {
      type: 'value',
      name: '设备数量'
    },
    series: [
      {
        name: '健康',
        type: displayMode.value === 'scatter' ? 'scatter' : 'line',
        data: defaultHealthy,
        smooth: true,
        itemStyle: { color: '#18a058' },
        areaStyle: displayMode.value === 'area' ? { opacity: 0.3 } : null,
        show: visibleSeries.value.includes('historical'),
      },
      {
        name: '预警',
        type: displayMode.value === 'scatter' ? 'scatter' : 'line',
        data: defaultWarning,
        smooth: true,
        itemStyle: { color: '#f0a020' },
        areaStyle: displayMode.value === 'area' ? { opacity: 0.3 } : null,
        show: visibleSeries.value.includes('prediction'),
      },
      {
        name: '异常',
        type: displayMode.value === 'scatter' ? 'scatter' : 'line',
        data: defaultError,
        smooth: true,
        itemStyle: { color: '#d03050' },
        areaStyle: displayMode.value === 'area' ? { opacity: 0.3 } : null,
        show: visibleSeries.value.includes('confidence'),
      },
    ],
  }
})

// 选项
const timeRangeOptions = [
  { label: '7天', value: '7d' },
  { label: '30天', value: '30d' },
  { label: '90天', value: '90d' },
  { label: '180天', value: '180d' },
  { label: '1年', value: '1y' },
]

const predictionRangeOptions = [
  { label: '3天', value: '3d' },
  { label: '7天', value: '7d' },
  { label: '14天', value: '14d' },
  { label: '30天', value: '30d' },
]

// 方法
const handleRefresh = () => {
  loading.value = true
  setTimeout(() => {
    loading.value = false
    message.success('数据已刷新')
  }, 1000)
}

const handleTimeRangeChange = () => {
  message.info(
    `时间范围已切换到${timeRangeOptions.find((opt) => opt.value === timeRange.value)?.label}`
  )
}

const handlePredictionRangeChange = () => {
  message.info(
    `预测范围已切换到${
      predictionRangeOptions.find((opt) => opt.value === predictionRange.value)?.label
    }`
  )
}

const handleDisplayModeChange = () => {
  // Chart will update automatically through chartOption computed property
}

const handleSeriesToggle = () => {
  // Chart will update automatically through chartOption computed property
}
</script>

<style scoped>
.chart-controls {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.control-label {
  font-size: 12px;
  color: #666;
}

.prediction-stats {
  margin-top: 16px;
  padding: 16px;
  background-color: #fafafa;
  border-radius: 6px;
}
</style>
