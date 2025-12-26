<template>
  <AIChart
    title="异常检测趋势"
    :height="height"
    :loading="loading"
    :data="data"
    :option="chartOption"
    :show-insight="showInsight"
    :insight="aiInsight"
    @refresh="handleRefresh"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AIChart from '@/components/ai-monitor/charts/AIChart.vue'

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
  showInsight: {
    type: Boolean,
    default: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

// Emits
const emit = defineEmits(['refresh'])

// AI洞察内容
const aiInsight = computed(() => {
  if (!props.data || props.data.length === 0) {
    return '暂无数据进行异常分析'
  }

  // 简单的异常检测逻辑
  const values = props.data.map((item) => item.value)
  const maxValue = Math.max(...values)
  const avgValue = values.reduce((sum, val) => sum + val, 0) / values.length

  if (maxValue > avgValue * 2) {
    const maxIndex = values.indexOf(maxValue)
    const timePoint = props.data[maxIndex]?.time || '未知时间'
    return `检测到${timePoint}时段异常峰值，建议检查该时段设备运行参数和环境因素。`
  }

  return '设备运行状态正常，未检测到明显异常。'
})

// 图表配置
const chartOption = computed(() => {
  if (!props.data || props.data.length === 0) {
    return {}
  }

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985',
        },
      },
      formatter: function (params) {
        const point = params[0]
        return `
          <div style="padding: 8px;">
            <div style="margin-bottom: 4px; font-weight: bold;">${point.name}</div>
            <div style="display: flex; align-items: center;">
              <span style="display: inline-block; width: 10px; height: 10px; background-color: ${point.color}; border-radius: 50%; margin-right: 8px;"></span>
              <span>异常分数: ${point.value}</span>
            </div>
          </div>
        `
      },
    },
    xAxis: {
      type: 'category',
      data: props.data.map((item) => item.time || item.name),
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
      name: '异常分数',
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
        name: '异常分数',
        type: 'line',
        data: props.data.map((item) => item.value),
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          width: 3,
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 1,
            y2: 0,
            colorStops: [
              { offset: 0, color: '#ff6b6b' },
              { offset: 1, color: '#ffa726' },
            ],
          },
        },
        itemStyle: {
          color: '#ff6b6b',
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
              { offset: 0, color: 'rgba(255, 107, 107, 0.3)' },
              { offset: 1, color: 'rgba(255, 107, 107, 0.05)' },
            ],
          },
        },
        emphasis: {
          focus: 'series',
          itemStyle: {
            color: '#ff4757',
            borderColor: '#fff',
            borderWidth: 3,
            shadowBlur: 10,
            shadowColor: 'rgba(255, 71, 87, 0.3)',
          },
        },
        markPoint: {
          data: [
            {
              type: 'max',
              name: '最大值',
              itemStyle: {
                color: '#ff4757',
              },
              label: {
                color: '#fff',
                fontSize: 12,
              },
            },
          ],
        },
      },
    ],
    animation: true,
    animationDuration: 1000,
    animationEasing: 'cubicOut',
  }
})

// 处理刷新事件
const handleRefresh = () => {
  emit('refresh')
}
</script>

<style scoped>
/* 组件样式由AIChart基础组件提供 */
</style>
