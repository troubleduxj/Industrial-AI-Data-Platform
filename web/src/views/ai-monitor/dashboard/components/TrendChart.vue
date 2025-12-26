<template>
  <div class="trend-chart">
    <div ref="chartRef" :style="{ height: height + 'px' }"></div>
    <div v-if="showControls" class="chart-controls">
      <n-space>
        <n-button-group size="small">
          <n-button
            v-for="period in timePeriods"
            :key="period.value"
            :type="selectedPeriod === period.value ? 'primary' : 'default'"
            @click="changePeriod(period.value)"
          >
            {{ period.label }}
          </n-button>
        </n-button-group>
        <n-button size="small" @click="toggleLegend">
          <template #icon>
            <n-icon><EyeOutline /></n-icon>
          </template>
          {{ showLegend ? '隐藏' : '显示' }}图例
        </n-button>
      </n-space>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { EyeOutline } from '@vicons/ionicons5'

// Props
const props = defineProps({
  data: {
    type: Array,
    required: true,
    default: () => [],
  },
  height: {
    type: Number,
    default: 300,
  },
  showControls: {
    type: Boolean,
    default: true,
  },
})

// 响应式数据
const chartRef = ref(null)
let chartInstance = null
const selectedPeriod = ref('24h')
const showLegend = ref(true)

// 时间周期选项
const timePeriods = [
  { label: '24小时', value: '24h' },
  { label: '7天', value: '7d' },
  { label: '30天', value: '30d' },
]

// 图表配置
const getChartOption = () => {
  return {
    title: {
      text: '设备健康状态趋势',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal',
        color: '#333',
      },
      left: 0,
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e0e0e0',
      borderWidth: 1,
      textStyle: {
        color: '#333',
      },
      formatter: function (params) {
        let result = `<div style="padding: 8px;"><div style="margin-bottom: 8px; font-weight: bold;">${params[0].name}</div>`
        params.forEach((param) => {
          result += `
            <div style="display: flex; align-items: center; margin-bottom: 4px;">
              <span style="display: inline-block; width: 10px; height: 10px; background: ${param.color}; border-radius: 50%; margin-right: 8px;"></span>
              ${param.seriesName}：<strong>${param.value}</strong>
            </div>
          `
        })
        result += '</div>'
        return result
      },
    },
    legend: {
      show: showLegend.value,
      data: ['健康设备', '预警设备', '异常设备'],
      top: 30,
      textStyle: {
        color: '#666',
        fontSize: 12,
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: showLegend.value ? '20%' : '15%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: props.data.map((item) => item.time),
      axisLine: {
        lineStyle: {
          color: '#e0e0e0',
        },
      },
      axisLabel: {
        color: '#666',
        fontSize: 12,
      },
    },
    yAxis: {
      type: 'value',
      name: '设备数量',
      nameTextStyle: {
        color: '#666',
        fontSize: 12,
      },
      axisLine: {
        show: false,
      },
      axisTick: {
        show: false,
      },
      axisLabel: {
        color: '#666',
        fontSize: 12,
      },
      splitLine: {
        lineStyle: {
          color: '#f0f0f0',
          type: 'dashed',
        },
      },
    },
    series: [
      {
        name: '健康设备',
        type: 'line',
        data: props.data.map((item) => item.healthy),
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          width: 3,
          color: '#18a058',
        },
        itemStyle: {
          color: '#18a058',
          borderColor: '#fff',
          borderWidth: 2,
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(24, 160, 88, 0.3)' },
              { offset: 1, color: 'rgba(24, 160, 88, 0.05)' },
            ],
          },
        },
      },
      {
        name: '预警设备',
        type: 'line',
        data: props.data.map((item) => item.warning),
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          width: 3,
          color: '#f0a020',
        },
        itemStyle: {
          color: '#f0a020',
          borderColor: '#fff',
          borderWidth: 2,
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(240, 160, 32, 0.3)' },
              { offset: 1, color: 'rgba(240, 160, 32, 0.05)' },
            ],
          },
        },
      },
      {
        name: '异常设备',
        type: 'line',
        data: props.data.map((item) => item.error),
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          width: 3,
          color: '#d03050',
        },
        itemStyle: {
          color: '#d03050',
          borderColor: '#fff',
          borderWidth: 2,
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(208, 48, 80, 0.3)' },
              { offset: 1, color: 'rgba(208, 48, 80, 0.05)' },
            ],
          },
        },
      },
    ],
    animation: true,
    animationDuration: 1000,
    animationEasing: 'cubicOut',
  }
}

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)
  chartInstance.setOption(getChartOption())

  // 添加点击事件
  chartInstance.on('click', (params) => {
    if (params.componentType === 'series') {
      console.log('点击了数据点:', params)
    }
  })
}

// 更新图表
const updateChart = () => {
  if (chartInstance) {
    chartInstance.setOption(getChartOption(), true)
  }
}

// 切换时间周期
const changePeriod = (period) => {
  selectedPeriod.value = period
  // 这里可以根据时间周期重新获取数据
  console.log('切换时间周期:', period)
}

// 切换图例显示
const toggleLegend = () => {
  showLegend.value = !showLegend.value
  updateChart()
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

// 监听高度变化
watch(
  () => props.height,
  () => {
    nextTick(() => {
      if (chartInstance) {
        chartInstance.resize()
      }
    })
  }
)

// 生命周期
onMounted(() => {
  nextTick(() => {
    initChart()
  })

  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    if (chartInstance) {
      chartInstance.resize()
    }
  })
})

// 组件卸载时销毁图表
onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  window.removeEventListener('resize', () => {
    if (chartInstance) {
      chartInstance.resize()
    }
  })
})
</script>

<style scoped>
.trend-chart {
  width: 100%;
}

.chart-controls {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}
</style>
