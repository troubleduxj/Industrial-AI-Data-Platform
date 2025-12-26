<template>
  <div class="ai-chart">
    <div v-if="title || $slots.header" class="chart-header">
      <slot name="header">
        <h3 class="chart-title">{{ title }}</h3>
      </slot>
      <div v-if="$slots.actions" class="chart-actions">
        <slot name="actions"></slot>
      </div>
    </div>

    <div class="chart-container">
      <div
        ref="chartRef"
        :style="{ height: height + 'px', width: '100%' }"
        class="chart-content"
      ></div>

      <!-- 加载状态 -->
      <div v-if="loading" class="chart-loading">
        <n-spin size="large">
          <template #description>加载中...</template>
        </n-spin>
      </div>

      <!-- 空数据状态 -->
      <div v-else-if="!hasData" class="chart-empty">
        <n-empty description="暂无数据" />
      </div>
    </div>

    <!-- AI洞察 -->
    <div v-if="showInsight && insight" class="chart-insight">
      <n-alert type="info" :show-icon="false">
        <template #icon>
          <n-icon><BulbOutline /></n-icon>
        </template>
        <strong>AI洞察：</strong>{{ insight }}
      </n-alert>
    </div>

    <!-- 自定义底部内容 -->
    <div v-if="$slots.footer" class="chart-footer">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, onBeforeUnmount, computed } from 'vue'
import * as echarts from 'echarts'
import { BulbOutline } from '@vicons/ionicons5'

// Props
const props = defineProps({
  // 图表标题
  title: {
    type: String,
    default: '',
  },
  // 图表高度
  height: {
    type: Number,
    default: 300,
  },
  // 图表配置
  option: {
    type: Object,
    required: true,
  },
  // 数据
  data: {
    type: [Array, Object],
    default: () => [],
  },
  // 加载状态
  loading: {
    type: Boolean,
    default: false,
  },
  // 是否显示AI洞察
  showInsight: {
    type: Boolean,
    default: false,
  },
  // AI洞察内容
  insight: {
    type: String,
    default: '',
  },
  // 主题
  theme: {
    type: String,
    default: 'default',
  },
  // 是否自适应
  responsive: {
    type: Boolean,
    default: true,
  },
})

// Emits
const emit = defineEmits(['chart-ready', 'chart-click', 'chart-hover'])

// 响应式数据
const chartRef = ref(null)
let chartInstance = null
let resizeObserver = null

// 计算属性
const hasData = computed(() => {
  if (Array.isArray(props.data)) {
    return props.data.length > 0
  }
  return props.data && Object.keys(props.data).length > 0
})

// 初始化图表
const initChart = async () => {
  if (!chartRef.value || props.loading || !hasData.value) return

  await nextTick()

  // 销毁已存在的实例
  if (chartInstance) {
    chartInstance.dispose()
  }

  // 创建新实例
  chartInstance = echarts.init(chartRef.value, props.theme)

  // 设置配置
  chartInstance.setOption(props.option, true)

  // 绑定事件
  chartInstance.on('click', (params) => {
    emit('chart-click', params)
  })

  chartInstance.on('mouseover', (params) => {
    emit('chart-hover', params)
  })

  // 发出就绪事件
  emit('chart-ready', chartInstance)

  // 设置响应式
  if (props.responsive) {
    setupResize()
  }
}

// 设置响应式调整
const setupResize = () => {
  if (!chartInstance || !chartRef.value) return

  // 使用 ResizeObserver 监听容器大小变化
  if (window.ResizeObserver) {
    resizeObserver = new ResizeObserver(() => {
      chartInstance?.resize()
    })
    resizeObserver.observe(chartRef.value)
  } else {
    // 降级到 window resize 事件
    window.addEventListener('resize', handleResize)
  }
}

// 处理窗口大小变化
const handleResize = () => {
  chartInstance?.resize()
}

// 更新图表
const updateChart = () => {
  if (chartInstance && props.option) {
    chartInstance.setOption(props.option, true)
  }
}

// 获取图表实例
const getChartInstance = () => {
  return chartInstance
}

// 导出图片
const exportImage = (type = 'png') => {
  if (chartInstance) {
    return chartInstance.getDataURL({
      type: type,
      backgroundColor: '#fff',
    })
  }
  return null
}

// 监听配置变化
watch(() => props.option, updateChart, { deep: true })
watch(() => props.data, initChart, { deep: true })
watch(() => props.loading, initChart)

// 生命周期
onMounted(() => {
  initChart()
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }

  if (resizeObserver) {
    resizeObserver.disconnect()
  } else {
    window.removeEventListener('resize', handleResize)
  }
})

// 暴露方法
defineExpose({
  getChartInstance,
  updateChart,
  exportImage,
})
</script>

<style scoped>
.ai-chart {
  width: 100%;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px 0;
}

.chart-title {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.chart-actions {
  display: flex;
  gap: 8px;
}

.chart-container {
  position: relative;
  padding: 16px;
}

.chart-content {
  position: relative;
}

.chart-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.8);
  z-index: 10;
}

.chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.chart-insight {
  margin: 0 16px 16px;
}

.chart-footer {
  padding: 0 16px 16px;
}

/* 响应式 */
@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .chart-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
