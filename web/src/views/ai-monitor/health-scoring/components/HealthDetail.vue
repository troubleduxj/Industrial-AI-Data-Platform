<template>
  <div class="health-detail">
    <n-card title="设备健康详情" size="small">
      <template #header-extra>
        <n-space>
          <n-button size="small" @click="refreshDetail">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
            刷新
          </n-button>
          <n-button size="small" type="primary" @click="exportDetail">
            <template #icon>
              <n-icon><DownloadOutline /></n-icon>
            </template>
            导出报告
          </n-button>
        </n-space>
      </template>

      <n-spin :show="loading">
        <div v-if="deviceDetail" class="detail-content">
          <!-- 基本信息 -->
          <n-card title="基本信息" size="small" class="mb-4">
            <n-descriptions :column="2" bordered>
              <n-descriptions-item label="设备名称">{{ deviceDetail.name }}</n-descriptions-item>
              <n-descriptions-item label="设备编号">{{ deviceDetail.code }}</n-descriptions-item>
              <n-descriptions-item label="所属车间">{{
                deviceDetail.workshop
              }}</n-descriptions-item>
              <n-descriptions-item label="设备类型">{{ deviceDetail.type }}</n-descriptions-item>
              <n-descriptions-item label="健康评分">
                <n-tag :type="getScoreType(deviceDetail.healthScore)" size="small">
                  {{ deviceDetail.healthScore }}
                </n-tag>
              </n-descriptions-item>
              <n-descriptions-item label="健康等级">
                <n-tag :type="getLevelType(deviceDetail.healthLevel)" size="small">
                  {{ deviceDetail.healthLevel }}
                </n-tag>
              </n-descriptions-item>
            </n-descriptions>
          </n-card>

          <!-- 健康指标 -->
          <n-card title="健康指标" size="small" class="mb-4">
            <n-grid :cols="2" :x-gap="16" :y-gap="16">
              <n-grid-item v-for="metric in deviceDetail.metrics" :key="metric.name">
                <n-statistic :label="metric.name" :value="metric.value">
                  <template #suffix>
                    <span class="text-gray-500">{{ metric.unit }}</span>
                  </template>
                </n-statistic>
                <n-progress
                  type="line"
                  :percentage="metric.percentage"
                  :status="getProgressStatus(metric.percentage)"
                  :show-indicator="false"
                  class="mt-2"
                />
              </n-grid-item>
            </n-grid>
          </n-card>

          <!-- 历史趋势 -->
          <n-card title="健康趋势" size="small" class="mb-4">
            <div ref="trendChart" style="height: 300px"></div>
          </n-card>

          <!-- 异常记录 -->
          <n-card title="异常记录" size="small">
            <n-data-table
              :columns="anomalyColumns"
              :data="deviceDetail.anomalies"
              :pagination="false"
              size="small"
              max-height="300"
            />
          </n-card>
        </div>

        <n-empty v-else description="暂无设备详情数据" />
      </n-spin>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch, onUnmounted, h } from 'vue'
import { useMessage } from 'naive-ui'
import * as echarts from 'echarts'
import { RefreshOutline, DownloadOutline } from '@vicons/ionicons5'

const props = defineProps({
  deviceId: {
    type: String,
    default: '',
  },
})

const message = useMessage()
const loading = ref(false)
const deviceDetail = ref(null)
const trendChart = ref(null)
let chartInstance = null

// 异常记录表格列
const anomalyColumns = [
  {
    title: '时间',
    key: 'time',
    width: 150,
  },
  {
    title: '异常类型',
    key: 'type',
    width: 120,
  },
  {
    title: '严重程度',
    key: 'severity',
    width: 100,
    render: (row) => {
      const typeMap = {
        高: 'error',
        中: 'warning',
        低: 'info',
      }
      return h('n-tag', { type: typeMap[row.severity], size: 'small' }, row.severity)
    },
  },
  {
    title: '描述',
    key: 'description',
  },
]

// 获取评分类型
const getScoreType = (score) => {
  if (score >= 90) return 'success'
  if (score >= 70) return 'warning'
  return 'error'
}

// 获取等级类型
const getLevelType = (level) => {
  const typeMap = {
    优秀: 'success',
    良好: 'info',
    一般: 'warning',
    较差: 'error',
  }
  return typeMap[level] || 'default'
}

// 获取进度条状态
const getProgressStatus = (percentage) => {
  if (percentage >= 80) return 'success'
  if (percentage >= 60) return 'warning'
  return 'error'
}

// 加载设备详情
const loadDeviceDetail = async () => {
  if (!props.deviceId) return

  loading.value = true
  try {
    // 模拟API调用
    await new Promise((resolve) => setTimeout(resolve, 1000))

    deviceDetail.value = {
      name: '焊接机器人-001',
      code: 'WR001',
      workshop: '车间A',
      type: '焊接设备',
      healthScore: 85,
      healthLevel: '良好',
      metrics: [
        { name: '温度', value: 45, unit: '°C', percentage: 75 },
        { name: '振动', value: 2.3, unit: 'mm/s', percentage: 60 },
        { name: '电流', value: 12.5, unit: 'A', percentage: 85 },
        { name: '压力', value: 0.8, unit: 'MPa', percentage: 90 },
      ],
      anomalies: [
        {
          time: '2024-01-15 14:30',
          type: '温度异常',
          severity: '中',
          description: '设备温度超过正常范围',
        },
        {
          time: '2024-01-14 09:15',
          type: '振动异常',
          severity: '低',
          description: '设备振动频率异常',
        },
      ],
    }

    // 渲染图表
    await nextTick()
    renderTrendChart()
  } catch (error) {
    message.error('加载设备详情失败')
  } finally {
    loading.value = false
  }
}

// 渲染趋势图表
const renderTrendChart = () => {
  if (!trendChart.value) return

  chartInstance = echarts.init(trendChart.value)

  const option = {
    tooltip: {
      trigger: 'axis',
    },
    legend: {
      data: ['健康评分'],
    },
    xAxis: {
      type: 'category',
      data: ['1月', '2月', '3月', '4月', '5月', '6月'],
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
    },
    series: [
      {
        name: '健康评分',
        type: 'line',
        data: [88, 85, 90, 82, 85, 87],
        smooth: true,
        lineStyle: {
          color: '#18a058',
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
              { offset: 1, color: 'rgba(24, 160, 88, 0.1)' },
            ],
          },
        },
      },
    ],
  }

  chartInstance.setOption(option)
}

// 刷新详情
const refreshDetail = () => {
  loadDeviceDetail()
}

// 导出详情
const exportDetail = () => {
  message.info('导出功能开发中')
}

// 监听设备ID变化
watch(
  () => props.deviceId,
  () => {
    loadDeviceDetail()
  },
  { immediate: true }
)

// 组件卸载时销毁图表
onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
})
</script>

<style scoped>
.health-detail {
  height: 100%;
}

.detail-content {
  min-height: 400px;
}

.mb-4 {
  margin-bottom: 16px;
}
</style>
