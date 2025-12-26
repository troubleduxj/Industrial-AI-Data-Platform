<template>
  <div class="data-chart-container">
    <!-- 图表头部 -->
    <div v-if="showHeader" class="chart-header">
      <div class="chart-title">
        <h3>{{ title }}</h3>
        <p v-if="subtitle" class="chart-subtitle">{{ subtitle }}</p>
      </div>

      <div class="chart-actions">
        <n-space>
          <!-- 刷新按钮 -->
          <n-button
            v-if="showRefresh"
            circle
            quaternary
            :loading="refreshing"
            @click="handleRefresh"
          >
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
          </n-button>

          <!-- 全屏按钮 -->
          <n-button v-if="showFullscreen" circle quaternary @click="toggleFullscreen">
            <template #icon>
              <n-icon>
                <ExpandOutline v-if="!isFullscreen" />
                <ContractOutline v-else />
              </n-icon>
            </template>
          </n-button>

          <!-- 下载按钮 -->
          <n-button v-if="showDownload" circle quaternary @click="handleDownload">
            <template #icon>
              <n-icon><DownloadOutline /></n-icon>
            </template>
          </n-button>

          <!-- 设置按钮 -->
          <n-button v-if="showSettings" circle quaternary @click="showSettingsModal = true">
            <template #icon>
              <n-icon><SettingsOutline /></n-icon>
            </template>
          </n-button>
        </n-space>
      </div>
    </div>

    <!-- 图表内容 -->
    <div class="chart-content" :class="{ fullscreen: isFullscreen }">
      <!-- 加载状态 -->
      <div v-if="loading" class="chart-loading">
        <n-spin size="large">
          <template #description>加载中...</template>
        </n-spin>
      </div>

      <!-- 空数据状态 -->
      <div v-else-if="isEmpty" class="chart-empty">
        <n-empty description="暂无数据">
          <template #icon>
            <n-icon size="48"><BarChartOutline /></n-icon>
          </template>
        </n-empty>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="error" class="chart-error">
        <n-result status="error" title="图表加载失败" :description="error">
          <template #footer>
            <n-button @click="handleRefresh">重试</n-button>
          </template>
        </n-result>
      </div>

      <!-- ECharts图表 -->
      <div v-else ref="chartRef" class="chart-instance" :style="chartStyle"></div>
    </div>

    <!-- 设置弹窗 -->
    <n-modal v-model:show="showSettingsModal" preset="card" title="图表设置" style="width: 500px">
      <n-form :model="chartSettings" label-placement="left" label-width="100px">
        <n-form-item label="图表类型">
          <n-select
            v-model:value="chartSettings.type"
            :options="chartTypeOptions"
            @update:value="updateChartType"
          />
        </n-form-item>

        <n-form-item label="主题">
          <n-select
            v-model:value="chartSettings.theme"
            :options="themeOptions"
            @update:value="updateTheme"
          />
        </n-form-item>

        <n-form-item label="动画">
          <n-switch v-model:value="chartSettings.animation" @update:value="updateAnimation" />
        </n-form-item>

        <n-form-item label="网格线">
          <n-switch v-model:value="chartSettings.showGrid" @update:value="updateGrid" />
        </n-form-item>

        <n-form-item label="图例">
          <n-switch v-model:value="chartSettings.showLegend" @update:value="updateLegend" />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button @click="resetSettings">重置</n-button>
          <n-button type="primary" @click="showSettingsModal = false">确定</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import {
  NButton,
  NIcon,
  NSpace,
  NSpin,
  NEmpty,
  NResult,
  NModal,
  NForm,
  NFormItem,
  NSelect,
  NSwitch,
  useMessage,
} from 'naive-ui'
import {
  RefreshOutline,
  ExpandOutline,
  ContractOutline,
  DownloadOutline,
  SettingsOutline,
  BarChartOutline,
} from '@vicons/ionicons5'
import * as echarts from 'echarts'

/**
 * 通用数据图表组件
 * 基于ECharts实现，支持多种图表类型和配置
 */
const props = defineProps({
  // 图表标题
  title: {
    type: String,
    default: '',
  },
  // 图表副标题
  subtitle: {
    type: String,
    default: '',
  },
  // 图表配置
  option: {
    type: Object,
    required: true,
  },
  // 图表类型
  type: {
    type: String,
    default: 'line',
    validator: (value) => ['line', 'bar', 'pie', 'scatter', 'radar', 'gauge'].includes(value),
  },
  // 图表高度
  height: {
    type: [String, Number],
    default: '400px',
  },
  // 图表宽度
  width: {
    type: [String, Number],
    default: '100%',
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
  // 是否显示头部
  showHeader: {
    type: Boolean,
    default: true,
  },
  // 是否显示刷新按钮
  showRefresh: {
    type: Boolean,
    default: true,
  },
  // 是否显示全屏按钮
  showFullscreen: {
    type: Boolean,
    default: true,
  },
  // 是否显示下载按钮
  showDownload: {
    type: Boolean,
    default: true,
  },
  // 是否显示设置按钮
  showSettings: {
    type: Boolean,
    default: true,
  },
  // 主题
  theme: {
    type: String,
    default: 'default',
  },
  // 自动刷新间隔（秒）
  autoRefresh: {
    type: Number,
    default: 0,
  },
})

const emit = defineEmits(['refresh', 'download', 'fullscreen-change'])
const message = useMessage()

// 图表实例
const chartRef = ref(null)
let chartInstance = null

// 状态
const refreshing = ref(false)
const isFullscreen = ref(false)
const showSettingsModal = ref(false)
let autoRefreshTimer = null

// 图表设置
const chartSettings = reactive({
  type: props.type,
  theme: props.theme,
  animation: true,
  showGrid: true,
  showLegend: true,
})

// 计算属性
const isEmpty = computed(() => {
  if (!props.option || !props.option.series) return true
  return props.option.series.every((series) => !series.data || series.data.length === 0)
})

const chartStyle = computed(() => {
  return {
    width: typeof props.width === 'number' ? `${props.width}px` : props.width,
    height: typeof props.height === 'number' ? `${props.height}px` : props.height,
  }
})

// 选项配置
const chartTypeOptions = [
  { label: '折线图', value: 'line' },
  { label: '柱状图', value: 'bar' },
  { label: '饼图', value: 'pie' },
  { label: '散点图', value: 'scatter' },
  { label: '雷达图', value: 'radar' },
  { label: '仪表盘', value: 'gauge' },
]

const themeOptions = [
  { label: '默认', value: 'default' },
  { label: '暗色', value: 'dark' },
  { label: '蓝色', value: 'blue' },
  { label: '绿色', value: 'green' },
]

// 初始化图表
const initChart = async () => {
  if (!chartRef.value) return

  try {
    // 销毁旧实例
    if (chartInstance) {
      chartInstance.dispose()
    }

    // 创建新实例
    chartInstance = echarts.init(chartRef.value, chartSettings.theme)

    // 设置配置
    const option = {
      ...props.option,
      animation: chartSettings.animation,
      grid: {
        ...props.option.grid,
        show: chartSettings.showGrid,
      },
      legend: {
        ...props.option.legend,
        show: chartSettings.showLegend,
      },
    }

    chartInstance.setOption(option, true)

    // 监听窗口大小变化
    window.addEventListener('resize', handleResize)

    // 监听图表事件
    chartInstance.on('click', handleChartClick)
    chartInstance.on('legendselectchanged', handleLegendChange)
  } catch (error) {
    console.error('图表初始化失败:', error)
    message.error('图表初始化失败')
  }
}

// 更新图表
const updateChart = () => {
  if (!chartInstance || props.loading || props.error || isEmpty.value) return

  const option = {
    ...props.option,
    animation: chartSettings.animation,
    grid: {
      ...props.option.grid,
      show: chartSettings.showGrid,
    },
    legend: {
      ...props.option.legend,
      show: chartSettings.showLegend,
    },
  }

  chartInstance.setOption(option, true)
}

// 处理窗口大小变化
const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 处理图表点击
const handleChartClick = (params) => {
  console.log('图表点击:', params)
}

// 处理图例变化
const handleLegendChange = (params) => {
  console.log('图例变化:', params)
}

// 刷新图表
const handleRefresh = async () => {
  refreshing.value = true
  try {
    emit('refresh')
    await nextTick()
    updateChart()
  } finally {
    refreshing.value = false
  }
}

// 切换全屏
const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
  emit('fullscreen-change', isFullscreen.value)

  nextTick(() => {
    handleResize()
  })
}

// 下载图表
const handleDownload = () => {
  if (!chartInstance) return

  try {
    const url = chartInstance.getDataURL({
      type: 'png',
      pixelRatio: 2,
      backgroundColor: '#fff',
    })

    const link = document.createElement('a')
    link.download = `${props.title || 'chart'}_${new Date().getTime()}.png`
    link.href = url
    link.click()

    emit('download', url)
    message.success('图表下载成功')
  } catch (error) {
    console.error('图表下载失败:', error)
    message.error('图表下载失败')
  }
}

// 更新图表类型
const updateChartType = (type) => {
  chartSettings.type = type
  updateChart()
}

// 更新主题
const updateTheme = (theme) => {
  chartSettings.theme = theme
  initChart()
}

// 更新动画
const updateAnimation = (animation) => {
  chartSettings.animation = animation
  updateChart()
}

// 更新网格
const updateGrid = (showGrid) => {
  chartSettings.showGrid = showGrid
  updateChart()
}

// 更新图例
const updateLegend = (showLegend) => {
  chartSettings.showLegend = showLegend
  updateChart()
}

// 重置设置
const resetSettings = () => {
  Object.assign(chartSettings, {
    type: props.type,
    theme: props.theme,
    animation: true,
    showGrid: true,
    showLegend: true,
  })
  initChart()
}

// 启动自动刷新
const startAutoRefresh = () => {
  if (props.autoRefresh > 0) {
    autoRefreshTimer = setInterval(() => {
      handleRefresh()
    }, props.autoRefresh * 1000)
  }
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
}

// 监听配置变化
watch(() => props.option, updateChart, { deep: true })
watch(
  () => props.loading,
  (loading) => {
    if (!loading) {
      nextTick(updateChart)
    }
  }
)
watch(
  () => props.autoRefresh,
  (newVal, oldVal) => {
    if (oldVal > 0) stopAutoRefresh()
    if (newVal > 0) startAutoRefresh()
  }
)

// 生命周期
onMounted(async () => {
  await nextTick()
  initChart()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
  }
})

// 暴露方法
defineExpose({
  refresh: handleRefresh,
  download: handleDownload,
  toggleFullscreen,
  getChartInstance: () => chartInstance,
})
</script>

<style scoped>
.data-chart-container {
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.chart-title h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

.chart-subtitle {
  margin: 4px 0 0 0;
  font-size: 12px;
  color: #8c8c8c;
}

.chart-content {
  position: relative;
  flex: 1;
  padding: 20px;
}

.chart-content.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  background: #fff;
  padding: 40px;
}

.chart-loading,
.chart-empty,
.chart-error {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}

.chart-instance {
  width: 100%;
  height: 100%;
  min-height: 300px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .chart-content {
    padding: 12px;
  }

  .chart-content.fullscreen {
    padding: 20px;
  }
}
</style>
