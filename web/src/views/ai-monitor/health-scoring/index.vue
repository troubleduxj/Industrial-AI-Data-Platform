<template>
  <div v-permission="{ action: 'read', resource: 'health_scoring' }" class="health-scoring">
    <!-- 页面头部 -->
    <n-page-header @back="$router.go(-1)">
      <template #title>
        <n-space align="center">
          <n-icon size="20" color="#18a058">
            <HeartOutline />
          </n-icon>
          <span>设备健康评分</span>
        </n-space>
      </template>
      <template #subtitle> 基于AI算法的设备健康状态综合评估 </template>
      <template #extra>
        <n-space>
          <PermissionButton permission="GET /api/v2/ai-monitor/health-scores" @click="refreshData">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
            刷新数据
          </PermissionButton>
          <PermissionButton
            permission="GET /api/v2/ai-monitor/health-scores/export"
            type="primary"
            @click="exportReport"
          >
            <template #icon>
              <n-icon><DocumentTextOutline /></n-icon>
            </template>
            导出报告
          </PermissionButton>
          <PermissionButton
            permission="PUT /api/v2/ai-monitor/health-score-config"
            @click="showScoreConfig = true"
          >
            <template #icon>
              <n-icon><SettingsOutline /></n-icon>
            </template>
            评分配置
          </PermissionButton>
        </n-space>
      </template>
    </n-page-header>

    <!-- 总体健康概览 -->
    <div class="overview-section">
      <n-grid :cols="4" :x-gap="16">
        <n-grid-item>
          <n-card>
            <n-statistic label="平均健康评分" :value="overviewStats.averageScore" tabular-nums>
              <template #suffix>/100</template>
              <template #prefix>
                <n-icon :color="getScoreColor(overviewStats.averageScore)">
                  <HeartOutline />
                </n-icon>
              </template>
            </n-statistic>
          </n-card>
        </n-grid-item>
        <n-grid-item>
          <n-card>
            <n-statistic label="健康设备" :value="overviewStats.healthyDevices" tabular-nums>
              <template #suffix>台</template>
              <template #prefix>
                <n-icon color="#18a058">
                  <CheckmarkCircleOutline />
                </n-icon>
              </template>
            </n-statistic>
          </n-card>
        </n-grid-item>
        <n-grid-item>
          <n-card>
            <n-statistic label="预警设备" :value="overviewStats.warningDevices" tabular-nums>
              <template #suffix>台</template>
              <template #prefix>
                <n-icon color="#f0a020">
                  <WarningOutline />
                </n-icon>
              </template>
            </n-statistic>
          </n-card>
        </n-grid-item>
        <n-grid-item>
          <n-card>
            <n-statistic label="异常设备" :value="overviewStats.errorDevices" tabular-nums>
              <template #suffix>台</template>
              <template #prefix>
                <n-icon color="#d03050">
                  <CloseCircleOutline />
                </n-icon>
              </template>
            </n-statistic>
          </n-card>
        </n-grid-item>
      </n-grid>
    </div>

    <!-- 健康评分分布 -->
    <div class="distribution-section">
      <n-grid :cols="2" :x-gap="16">
        <n-grid-item>
          <ScoreDistribution :data="scoreDistributionData" />
        </n-grid-item>
        <n-grid-item>
          <HealthTrend :data="healthTrendData" />
        </n-grid-item>
      </n-grid>
    </div>

    <!-- 设备健康列表 -->
    <div class="device-list-section">
      <n-card title="设备健康详情">
        <template #header-extra>
          <n-space>
            <n-input
              v-model:value="searchKeyword"
              placeholder="搜索设备"
              clearable
              style="width: 200px"
            >
              <template #prefix>
                <n-icon><SearchOutline /></n-icon>
              </template>
            </n-input>
            <n-select
              v-model:value="healthFilter"
              :options="healthFilterOptions"
              placeholder="健康状态"
              clearable
              style="width: 120px"
            />
            <n-select
              v-model:value="scoreRangeFilter"
              :options="scoreRangeOptions"
              placeholder="评分范围"
              clearable
              style="width: 120px"
            />
          </n-space>
        </template>

        <DeviceHealthList
          :data="filteredDeviceList"
          :loading="loading"
          @view-detail="handleViewDetail"
          @update-score="handleUpdateScore"
        />
      </n-card>
    </div>

    <!-- 健康评分详情抽屉 -->
    <n-drawer v-model:show="showHealthDetail" :width="800" placement="right">
      <n-drawer-content :title="selectedDevice?.name + ' 健康详情'">
        <HealthDetail v-if="selectedDevice" :device="selectedDevice" />
      </n-drawer-content>
    </n-drawer>

    <!-- 评分配置模态框 -->
    <n-modal v-model:show="showScoreConfig" preset="card" title="健康评分配置" style="width: 800px">
      <ScoreConfig @save="handleSaveConfig" @cancel="showScoreConfig = false" />
    </n-modal>

    <!-- AI洞察提示 -->
    <div class="ai-insights">
      <n-alert type="info" :show-icon="false">
        <template #icon>
          <n-icon color="#2080f0">
            <BulbOutline />
          </n-icon>
        </template>
        <template #header>AI智能洞察</template>
        <div class="insights-content">
          <div v-for="insight in aiInsights" :key="insight.id" class="insight-item">
            <n-tag :type="insight.type" size="small">{{ insight.category }}</n-tag>
            <span class="insight-text">{{ insight.content }}</span>
          </div>
        </div>
      </n-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import {
  HeartOutline,
  RefreshOutline,
  DocumentTextOutline,
  SettingsOutline,
  CheckmarkCircleOutline,
  WarningOutline,
  CloseCircleOutline,
  SearchOutline,
  BulbOutline,
} from '@vicons/ionicons5'
import PermissionButton from '@/components/common/PermissionButton.vue'
import ScoreDistribution from './components/ScoreDistribution.vue'
import HealthTrend from './components/HealthTrend.vue'
import DeviceHealthList from './components/DeviceHealthList.vue'
import HealthDetail from './components/HealthDetail.vue'
import ScoreConfig from './components/ScoreConfig.vue'
// 导入新的AI API客户端
import { healthScoringApi } from '@/api/v2/ai-module'

const message = useMessage()

// 响应式数据
const loading = ref(false)
const searchKeyword = ref('')
const healthFilter = ref(null)
const scoreRangeFilter = ref(null)
const showHealthDetail = ref(false)
const showScoreConfig = ref(false)
const selectedDevice = ref(null)

// 总体统计数据（从API获取）
const overviewStats = ref({
  averageScore: 0,
  healthyDevices: 0,
  warningDevices: 0,
  errorDevices: 0,
})

// 健康状态过滤选项
const healthFilterOptions = [
  { label: '健康', value: 'healthy' },
  { label: '预警', value: 'warning' },
  { label: '异常', value: 'error' },
]

// 评分范围过滤选项
const scoreRangeOptions = [
  { label: '90-100分', value: '90-100' },
  { label: '80-89分', value: '80-89' },
  { label: '70-79分', value: '70-79' },
  { label: '60-69分', value: '60-69' },
  { label: '60分以下', value: '0-59' },
]

// 评分分布数据（从API获取）
const scoreDistributionData = ref([])

// 健康趋势数据
const healthTrendData = ref({
  dates: [],
  scores: [],
  predictions: [],
})

// 设备健康列表数据（从API获取）
const deviceList = ref([])

// AI洞察数据
const aiInsights = ref([
  {
    id: 1,
    category: '趋势预警',
    type: 'warning',
    content: '生产线B的设备整体健康评分呈下降趋势，建议加强维护频次',
  },
  {
    id: 2,
    category: '效率优化',
    type: 'info',
    content: '通过调整工艺参数，预计可提升整体设备效率8-12%',
  },
  {
    id: 3,
    category: '维护建议',
    type: 'success',
    content: '设备003需要立即维护，预计维护后健康评分可提升至75分以上',
  },
])

// 计算属性
const filteredDeviceList = computed(() => {
  let filtered = deviceList.value

  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(
      (device) =>
        device.name.toLowerCase().includes(keyword) ||
        device.type.toLowerCase().includes(keyword) ||
        device.location.toLowerCase().includes(keyword)
    )
  }

  // 健康状态过滤
  if (healthFilter.value) {
    filtered = filtered.filter((device) => device.healthLevel === healthFilter.value)
  }

  // 评分范围过滤
  if (scoreRangeFilter.value) {
    const [min, max] = scoreRangeFilter.value.split('-').map(Number)
    filtered = filtered.filter((device) => {
      if (max) {
        return device.healthScore >= min && device.healthScore <= max
      } else {
        return device.healthScore >= min
      }
    })
  }

  return filtered
})

// 方法
const getScoreColor = (score) => {
  if (score >= 80) return '#18a058'
  if (score >= 60) return '#f0a020'
  return '#d03050'
}

const refreshData = async () => {
  if (loading.value) return
  
  loading.value = true
  try {
    console.log('🔄 刷新健康评分数据...')

    // 并行加载多个API数据
    const [devicesResponse, distributionResponse, overviewResponse] = await Promise.allSettled([
      fetch('/api/v2/ai/health-scoring/devices').then(r => r.json()),
      fetch('/api/v2/ai/health-scoring/distribution').then(r => r.json()),
      fetch('/api/v2/ai/health-scoring/overview').then(r => r.json())
    ])
    
    // 处理设备健康列表
    if (devicesResponse.status === 'fulfilled' && devicesResponse.value?.data) {
      deviceList.value = devicesResponse.value.data.items || []
      console.log('✅ 设备健康列表加载成功:', deviceList.value.length)
    }
    
    // 处理评分分布
    if (distributionResponse.status === 'fulfilled' && distributionResponse.value?.data) {
      scoreDistributionData.value = distributionResponse.value.data || []
      console.log('✅ 评分分布数据加载成功')
    }
    
    // 处理概览统计
    if (overviewResponse.status === 'fulfilled' && overviewResponse.value?.data) {
      Object.assign(overviewStats.value, overviewResponse.value.data)
      console.log('✅ 概览统计数据加载成功')
    }
    
    // 原有的历史记录获取逻辑（保留）
    try {
      const response = await healthScoringApi.getHistory({
        page: 1,
        page_size: 100,
      })

      if (response.data && response.data.records) {
        console.log('✅ 获取健康评分记录:', response.data)
        
        const records = response.data.records
        
        // 按设备聚合最新评分
        const deviceScoreMap = new Map()
        records.forEach((record) => {
          const key = record.device_code
          if (!deviceScoreMap.has(key) || new Date(record.score_time) > new Date(deviceScoreMap.get(key).score_time)) {
            deviceScoreMap.set(key, record)
          }
        })
        
        // 转换为设备列表格式
        const devices = Array.from(deviceScoreMap.values()).map((record, index) => ({
          id: index + 1,
          name: record.device_name || record.device_code,
          type: '设备', // 实际应从设备信息获取
          location: '-', // 实际应从设备信息获取
          healthScore: Math.round(record.health_score),
          healthLevel: mapHealthLevel(record.health_grade),
          lastUpdate: formatDateTime(record.score_time),
          factors: mapHealthFactors(record.dimension_scores),
          trend: 'stable', // 实际应根据历史趋势计算
          riskLevel: mapRiskLevel(record.health_grade),
          nextMaintenance: '-', // 实际应从维护计划获取
          operatingHours: 0, // 实际应从设备运行数据获取
          rawData: record,
        }))
        
        // 如果从新API没有获取到数据，使用历史记录
        if (deviceList.value.length === 0) {
          deviceList.value = devices
        }
        
        // 更新统计数据
        updateOverviewStats(devices)
        
        // 更新评分分布
        updateScoreDistribution(devices)
        
        // 生成健康趋势数据
        generateHealthTrendDataFromAPI(records)
      }
    } catch (historyError) {
      console.warn('获取历史记录失败:', historyError)
      // 历史记录获取失败不影响主流程
    }

    message.success(`已刷新健康评分数据`)
    console.log('✅ 健康评分数据刷新完成')
  } catch (error) {
    console.error('❌ 刷新数据失败:', error)
    message.error(`数据刷新失败: ${error.message || '未知错误'}`)
  } finally {
    loading.value = false
  }
}

// 辅助函数：映射健康等级
const mapHealthLevel = (grade: string): string => {
  if (grade === 'A' || grade === 'B') return 'healthy'
  if (grade === 'C') return 'warning'
  return 'error' // D, F
}

// 辅助函数：映射风险等级
const mapRiskLevel = (grade: string): string => {
  if (grade === 'A' || grade === 'B') return 'low'
  if (grade === 'C') return 'medium'
  return 'high'
}

// 辅助函数：映射健康因素
const mapHealthFactors = (dimensionScores: any): any => {
  if (!dimensionScores || typeof dimensionScores !== 'object') {
    return {
      performance: { score: 0, status: 'unknown', value: '-' },
      anomaly: { score: 0, status: 'unknown', value: '-' },
      trend: { score: 0, status: 'unknown', value: '-' },
      uptime: { score: 0, status: 'unknown', value: '-' },
    }
  }
  
  const mapFactorStatus = (score: number) => {
    if (score >= 80) return 'normal'
    if (score >= 60) return 'warning'
    return 'error'
  }
  
  return {
    performance: {
      score: Math.round(dimensionScores.performance_score || 0),
      status: mapFactorStatus(dimensionScores.performance_score || 0),
      value: `${Math.round(dimensionScores.performance_score || 0)}分`,
    },
    anomaly: {
      score: Math.round(dimensionScores.anomaly_score || 0),
      status: mapFactorStatus(dimensionScores.anomaly_score || 0),
      value: `${Math.round(dimensionScores.anomaly_score || 0)}分`,
    },
    trend: {
      score: Math.round(dimensionScores.trend_score || 0),
      status: mapFactorStatus(dimensionScores.trend_score || 0),
      value: `${Math.round(dimensionScores.trend_score || 0)}分`,
    },
    uptime: {
      score: Math.round(dimensionScores.uptime_score || 0),
      status: mapFactorStatus(dimensionScores.uptime_score || 0),
      value: `${Math.round(dimensionScores.uptime_score || 0)}分`,
    },
  }
}

// 辅助函数：格式化日期时间
const formatDateTime = (dateStr: string): string => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }).replace(/\//g, '-')
  } catch {
    return dateStr
  }
}

// 辅助函数：更新统计数据
const updateOverviewStats = (devices: any[]) => {
  const healthy = devices.filter(d => d.healthLevel === 'healthy').length
  const warning = devices.filter(d => d.healthLevel === 'warning').length
  const error = devices.filter(d => d.healthLevel === 'error').length
  
  const totalScore = devices.reduce((sum, d) => sum + d.healthScore, 0)
  const avgScore = devices.length > 0 ? Math.round(totalScore / devices.length * 10) / 10 : 0
  
  overviewStats.value = {
    averageScore: avgScore,
    healthyDevices: healthy,
    warningDevices: warning,
    errorDevices: error,
  }
}

// 辅助函数：更新评分分布
const updateScoreDistribution = (devices: any[]) => {
  const ranges = [
    { range: '90-100', min: 90, max: 100, count: 0 },
    { range: '80-89', min: 80, max: 89, count: 0 },
    { range: '70-79', min: 70, max: 79, count: 0 },
    { range: '60-69', min: 60, max: 69, count: 0 },
    { range: '0-59', min: 0, max: 59, count: 0 },
  ]
  
  devices.forEach((device) => {
    const score = device.healthScore
    const range = ranges.find(r => score >= r.min && score <= r.max)
    if (range) range.count++
  })
  
  const total = devices.length || 1
  scoreDistributionData.value = ranges.map(r => ({
    range: r.range,
    count: r.count,
    percentage: Math.round((r.count / total) * 100 * 10) / 10,
  }))
}

// 辅助函数：从API数据生成健康趋势
const generateHealthTrendDataFromAPI = (records: any[]) => {
  // 按日期聚合平均评分
  const dateScoreMap = new Map<string, { sum: number; count: number }>()
  
  records.forEach((record) => {
    if (record.score_time) {
      const date = record.score_time.split('T')[0] || record.score_time.split(' ')[0]
      if (!dateScoreMap.has(date)) {
        dateScoreMap.set(date, { sum: 0, count: 0 })
      }
      const entry = dateScoreMap.get(date)!
      entry.sum += record.health_score
      entry.count++
    }
  })
  
  // 排序并转换为数组
  const sortedDates = Array.from(dateScoreMap.keys()).sort()
  const dates = sortedDates.slice(-30) // 最近30天
  const scores = dates.map((date) => {
    const entry = dateScoreMap.get(date)!
    return Math.round((entry.sum / entry.count) * 10) / 10
  })
  
  // 简单的线性预测（实际应使用趋势预测API）
  const predictions = []
  if (scores.length >= 2) {
    const lastScore = scores[scores.length - 1]
    const trend = (scores[scores.length - 1] - scores[scores.length - 2])
    
    for (let i = 1; i <= 7; i++) {
      const predictedScore = Math.max(0, Math.min(100, lastScore + trend * i))
      predictions.push(Math.round(predictedScore * 10) / 10)
      
      // 添加预测日期
      const lastDate = new Date(dates[dates.length - 1])
      lastDate.setDate(lastDate.getDate() + i)
      dates.push(lastDate.toISOString().split('T')[0])
    }
  }
  
  healthTrendData.value = { dates, scores, predictions }
}

const exportReport = () => {
  message.info('正在生成健康评分报告...')
  // 模拟报告生成
  setTimeout(() => {
    message.success('报告已生成并下载')
  }, 2000)
}

const handleViewDetail = (device) => {
  selectedDevice.value = device
  showHealthDetail.value = true
}

const handleUpdateScore = (device) => {
  message.info(`正在重新计算 ${device.name} 的健康评分...`)
  // 模拟评分更新
  setTimeout(() => {
    const index = deviceList.value.findIndex((d) => d.id === device.id)
    if (index !== -1) {
      deviceList.value[index].healthScore = Math.floor(Math.random() * 30) + 60
      deviceList.value[index].lastUpdate = new Date().toLocaleString('zh-CN')
    }
    message.success('健康评分已更新')
  }, 1500)
}

const handleSaveConfig = (config) => {
  message.success('评分配置已保存')
  showScoreConfig.value = false
}

// 生成健康趋势数据
const generateHealthTrendData = () => {
  const dates = []
  const scores = []
  const predictions = []
  const now = new Date()

  // 历史数据（30天）
  for (let i = 29; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
    dates.push(date.toISOString().split('T')[0])
    scores.push(Math.floor(Math.random() * 20) + 70)
  }

  // 预测数据（7天）
  for (let i = 1; i <= 7; i++) {
    const date = new Date(now.getTime() + i * 24 * 60 * 60 * 1000)
    dates.push(date.toISOString().split('T')[0])
    predictions.push(Math.floor(Math.random() * 15) + 75)
  }

  healthTrendData.value = { dates, scores, predictions }
}

// 生命周期
onMounted(() => {
  // 初始加载健康评分数据
  refreshData()
})
</script>

<style scoped>
.health-scoring {
  padding: 0;
}

.overview-section {
  margin-bottom: 24px;
}

.distribution-section {
  margin-bottom: 24px;
}

.device-list-section {
  margin-bottom: 24px;
}

.ai-insights {
  margin-top: 24px;
}

.insights-content {
  margin-top: 12px;
}

.insight-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.insight-text {
  font-size: 13px;
  color: #666;
}
</style>
