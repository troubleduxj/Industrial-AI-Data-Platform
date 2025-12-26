<template>
  <div v-permission="{ action: 'read', resource: 'ai_monitor_dashboard' }" class="ai-dashboard">
    <!-- 页面标题 -->
    <n-page-header title="AI监测总览" subtitle="设备智能监测与分析平台">
      <template #extra>
        <n-space>
          <n-button
            type="info"
            @click="router.push({ path: '/data-model/config', query: { model_type: 'ai_analysis' } })"
          >
            <template #icon>
              <n-icon><SettingsOutline /></n-icon>
            </template>
            管理特征模型
          </n-button>
          <n-button type="primary" @click="refreshData">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
            刷新数据
          </n-button>
          <n-button
            v-permission="{ action: 'export', resource: 'ai_monitor_dashboard' }"
            @click="exportReport"
          >
            <template #icon>
              <n-icon><DownloadOutline /></n-icon>
            </template>
            导出报告
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <!-- 设备健康状态总览 -->
    <n-card title="设备健康状态" class="mb-4" hoverable>
      <HealthOverview :data="healthData" @device-click="handleDeviceClick" />
    </n-card>

    <!-- 数据统计卡片 -->
    <n-grid :cols="4" :x-gap="16" class="mb-4">
      <n-grid-item>
        <n-card hoverable :loading="loading">
          <n-statistic label="总设备数" :value="dashboardStats.totalDevices" tabular-nums>
            <template #prefix>
              <n-icon color="#18a058"><HardwareChipOutline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card hoverable :loading="loading">
          <n-statistic label="在线率" :value="dashboardStats.onlineRate" suffix="%" tabular-nums>
            <template #prefix>
              <n-icon color="#2080f0"><WifiOutline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card hoverable :loading="loading">
          <n-statistic label="异常检测" :value="dashboardStats.anomalyCount" tabular-nums>
            <template #prefix>
              <n-icon color="#f0a020"><WarningOutline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card hoverable :loading="loading">
          <n-statistic label="AI模型" :value="dashboardStats.activeModels" tabular-nums>
            <template #prefix>
              <n-icon color="#d03050"><BulbOutline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 图表区域 -->
    <n-grid :cols="2" :x-gap="16" class="mb-4">
      <n-grid-item>
        <n-card title="异常趋势分析" hoverable :loading="loading">
          <AnomalyChart :data="anomalyTrendData" height="300" />
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card title="设备健康趋势" hoverable :loading="loading">
          <TrendChart :data="healthTrendData" height="300" />
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- AI洞察报告 -->
    <n-card title="AI智能洞察" hoverable>
      <template #header-extra>
        <n-tag type="info">
          <template #icon>
            <n-icon><BulbOutline /></n-icon>
          </template>
          实时分析
        </n-tag>
      </template>
      <n-space vertical>
        <n-alert
          v-for="insight in aiInsights"
          :key="insight.id"
          :type="insight.type"
          :title="insight.title"
          :show-icon="false"
        >
          <template #icon>
            <n-icon><BulbOutline /></n-icon>
          </template>
          {{ insight.content }}
        </n-alert>
      </n-space>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { useRouter } from 'vue-router'
import {
  RefreshOutline,
  DownloadOutline,
  HardwareChipOutline,
  WifiOutline,
  WarningOutline,
  BulbOutline,
} from '@vicons/ionicons5'
import { SettingsOutline } from '@vicons/ionicons5'
import HealthOverview from './components/HealthOverview.vue'
import AnomalyChart from './components/AnomalyChart.vue'
import TrendChart from './components/TrendChart.vue'
import aiMonitorV2Api from '@/api/ai-monitor-v2'
// 导入新的AI API客户端
import { anomalyDetectionApi, healthScoringApi } from '@/api/v2/ai-module'

const router = useRouter()

// ==================== 类型定义 ====================

interface DashboardStats {
  totalDevices: number
  onlineRate: number
  anomalyCount: number
  activeModels: number
}

interface HealthData {
  healthy: number
  warning: number
  error: number
}

interface AnomalyTrendItem {
  time: string
  value: number
}

interface HealthTrendItem {
  time: string
  healthy: number
  warning: number
  error: number
}

interface AIInsight {
  id: number
  type: 'success' | 'info' | 'warning' | 'error'
  title: string
  content: string
}

const message = useMessage()

// 加载状态
const loading = ref(false)

// 响应式数据
const dashboardStats = ref<DashboardStats>({
  totalDevices: 0,
  onlineRate: 0,
  anomalyCount: 0,
  activeModels: 0,
})

const healthData = ref<HealthData>({
  healthy: 0,
  warning: 0,
  error: 0,
})

const anomalyTrendData = ref<AnomalyTrendItem[]>([
  { time: '00:00', value: 2 },
  { time: '04:00', value: 1 },
  { time: '08:00', value: 5 },
  { time: '12:00', value: 3 },
  { time: '16:00', value: 8 },
  { time: '20:00', value: 4 },
])

const healthTrendData = ref<HealthTrendItem[]>([
  { time: '00:00', healthy: 140, warning: 8, error: 8 },
  { time: '04:00', healthy: 142, warning: 6, error: 8 },
  { time: '08:00', healthy: 138, warning: 10, error: 8 },
  { time: '12:00', healthy: 141, warning: 7, error: 8 },
  { time: '16:00', healthy: 142, warning: 6, error: 8 },
  { time: '20:00', healthy: 144, warning: 4, error: 8 },
])

const aiInsights = ref<AIInsight[]>([
  {
    id: 1,
    type: 'warning',
    title: '设备异常预警',
    content: '检测到设备 WLD-001 温度持续上升，建议立即检查冷却系统。',
  },
  {
    id: 2,
    type: 'info',
    title: '性能优化建议',
    content: '基于历史数据分析，建议在14:00-16:00期间调整设备运行参数以提高效率。',
  },
  {
    id: 3,
    type: 'success',
    title: '维护提醒',
    content: '设备 WLD-005 运行状态良好，预计下次维护时间为2024年2月15日。',
  },
])

// 方法
const refreshData = async () => {
  if (loading.value) return
  
  loading.value = true
  try {
    console.log('🔄 开始刷新AI仪表盘数据...')

    // 并行获取多个数据源
    const [anomalyRecordsRes, healthScoresRes] = await Promise.allSettled([
      // 获取最近的异常记录
      anomalyDetectionApi.getRecords({
        page: 1,
        page_size: 100,
        is_handled: false,
      }),
      // 获取最近的健康评分记录
      healthScoringApi.getHistory({
        page: 1,
        page_size: 50,
      }),
    ])

    // 处理异常记录数据
    if (anomalyRecordsRes.status === 'fulfilled' && anomalyRecordsRes.value?.data) {
      const anomalyData = anomalyRecordsRes.value.data
      console.log('✅ 异常记录数据:', anomalyData)

      // 更新异常统计
      dashboardStats.value.anomalyCount = anomalyData.total || 0

      // 构建异常趋势数据（按时间聚合）
      const records = anomalyData.records || []
      const trendMap = new Map<string, number>()
      
      records.forEach((record: any) => {
        if (record.detection_time) {
          const hour = new Date(record.detection_time).getHours()
          const timeKey = `${String(hour).padStart(2, '0')}:00`
          trendMap.set(timeKey, (trendMap.get(timeKey) || 0) + 1)
        }
      })

      // 转换为图表数据（最近6个时间点）
      const now = new Date()
      anomalyTrendData.value = []
      for (let i = 5; i >= 0; i--) {
        const hour = (now.getHours() - i * 4 + 24) % 24
        const timeKey = `${String(hour).padStart(2, '0')}:00`
        anomalyTrendData.value.push({
          time: timeKey,
          value: trendMap.get(timeKey) || 0,
        })
      }
    } else {
      console.warn('⚠️ 获取异常记录失败:', anomalyRecordsRes)
    }

    // 处理健康评分数据
    if (healthScoresRes.status === 'fulfilled' && healthScoresRes.value?.data) {
      const healthData = healthScoresRes.value.data
      console.log('✅ 健康评分数据:', healthData)

      const records = healthData.records || []

      // 统计不同健康等级的设备数量
      const gradeCount = { A: 0, B: 0, C: 0, D: 0, F: 0 }
      const deviceGrades = new Map<string, string>()

      records.forEach((record: any) => {
        // 只统计每个设备的最新评分
        if (!deviceGrades.has(record.device_code)) {
          deviceGrades.set(record.device_code, record.health_grade)
          if (gradeCount[record.health_grade] !== undefined) {
            gradeCount[record.health_grade]++
          }
        }
      })

      // 更新健康状态统计
      healthData.value = {
        healthy: gradeCount.A + gradeCount.B, // A和B等级为健康
        warning: gradeCount.C, // C等级为警告
        error: gradeCount.D + gradeCount.F, // D和F等级为错误
      }

      // 更新总设备数和在线率
      const totalDevices = deviceGrades.size
      dashboardStats.value.totalDevices = totalDevices
      dashboardStats.value.onlineRate = totalDevices > 0
        ? Math.round(((gradeCount.A + gradeCount.B + gradeCount.C) / totalDevices) * 100 * 10) / 10
        : 0

      // 构建健康趋势数据（按时间聚合）
      const trendMap = new Map<string, { healthy: number; warning: number; error: number }>()
      
      records.slice(0, 30).forEach((record: any) => {
        if (record.score_time) {
          const hour = new Date(record.score_time).getHours()
          const timeKey = `${String(hour).padStart(2, '0')}:00`
          
          if (!trendMap.has(timeKey)) {
            trendMap.set(timeKey, { healthy: 0, warning: 0, error: 0 })
          }
          
          const trend = trendMap.get(timeKey)!
          const grade = record.health_grade
          
          if (grade === 'A' || grade === 'B') {
            trend.healthy++
          } else if (grade === 'C') {
            trend.warning++
          } else {
            trend.error++
          }
        }
      })

      // 转换为图表数据
      const now = new Date()
      healthTrendData.value = []
      for (let i = 5; i >= 0; i--) {
        const hour = (now.getHours() - i * 4 + 24) % 24
        const timeKey = `${String(hour).padStart(2, '0')}:00`
        const trend = trendMap.get(timeKey) || { healthy: 0, warning: 0, error: 0 }
        healthTrendData.value.push({
          time: timeKey,
          ...trend,
        })
      }
    } else {
      console.warn('⚠️ 获取健康评分失败:', healthScoresRes)
    }

    // 生成AI洞察（基于实际数据）
    generateAIInsights()

    // 模拟活跃模型数（可以后续从API获取）
    dashboardStats.value.activeModels = 4 // 特征提取、异常检测、趋势预测、健康评分

    console.log('✅ 仪表盘数据刷新完成')
    message.success('数据刷新完成')
  } catch (error) {
    console.error('❌ 刷新数据失败:', error)
    message.error(`数据刷新失败: ${error.message || '未知错误'}`)
  } finally {
    loading.value = false
  }
}

// 生成AI洞察
const generateAIInsights = () => {
  const insights: AIInsight[] = []

  // 基于异常数量生成洞察
  if (dashboardStats.value.anomalyCount > 10) {
    insights.push({
      id: 1,
      type: 'warning',
      title: '异常数量较多',
      content: `当前检测到 ${dashboardStats.value.anomalyCount} 个异常，建议优先处理严重程度较高的异常。`,
    })
  } else if (dashboardStats.value.anomalyCount > 5) {
    insights.push({
      id: 1,
      type: 'info',
      title: '异常检测正常',
      content: `系统运行正常，当前有 ${dashboardStats.value.anomalyCount} 个异常需要关注。`,
    })
  } else {
    insights.push({
      id: 1,
      type: 'success',
      title: '系统运行健康',
      content: '设备运行状态良好，异常数量较少，请继续保持。',
    })
  }

  // 基于在线率生成洞察
  if (dashboardStats.value.onlineRate < 80) {
    insights.push({
      id: 2,
      type: 'error',
      title: '设备在线率偏低',
      content: `当前在线率为 ${dashboardStats.value.onlineRate}%，建议检查离线设备的连接状态。`,
    })
  } else if (dashboardStats.value.onlineRate < 90) {
    insights.push({
      id: 2,
      type: 'warning',
      title: '部分设备离线',
      content: `当前在线率为 ${dashboardStats.value.onlineRate}%，有部分设备离线，请注意检查。`,
    })
  }

  // 基于健康状态生成洞察
  const { healthy, warning, error } = healthData.value
  const total = healthy + warning + error

  if (total > 0) {
    const healthyRate = Math.round((healthy / total) * 100)
    
    if (healthyRate >= 90) {
      insights.push({
        id: 3,
        type: 'success',
        title: '设备健康状况优秀',
        content: `${healthyRate}% 的设备处于健康状态（A/B等级），继续保持良好的维护习惯。`,
      })
    } else if (healthyRate >= 70) {
      insights.push({
        id: 3,
        type: 'info',
        title: '设备健康状况良好',
        content: `${healthyRate}% 的设备处于健康状态，建议关注 ${warning + error} 个需要维护的设备。`,
      })
    } else {
      insights.push({
        id: 3,
        type: 'warning',
        title: '需要加强设备维护',
        content: `只有 ${healthyRate}% 的设备处于健康状态，有 ${error} 个设备健康状况较差，建议尽快维护。`,
      })
    }
  }

  aiInsights.value = insights
}

const exportReport = () => {
  message.info('正在生成报告...')
  // 模拟报告导出
  setTimeout(() => {
    message.success('报告导出完成')
  }, 2000)
}

const handleDeviceClick = (deviceInfo) => {
  message.info(`查看设备详情: ${deviceInfo.name}`)
}

// 生命周期
onMounted(() => {
  // 初始化数据加载
  refreshData()
})
</script>

<style scoped>
.ai-dashboard {
  padding: 16px;
}

.mb-4 {
  margin-bottom: 16px;
}
</style>
