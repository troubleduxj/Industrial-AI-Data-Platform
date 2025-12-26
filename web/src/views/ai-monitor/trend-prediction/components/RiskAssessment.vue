<template>
  <div class="risk-assessment">
    <div class="assessment-header">
      <n-space justify="space-between" align="center">
        <div class="header-title">
          <n-space align="center">
            <n-icon size="16" color="#d03050">
              <WarningOutline />
            </n-icon>
            <span>风险评估</span>
          </n-space>
        </div>
        <n-space>
          <n-select
            v-model:value="assessmentType"
            :options="assessmentTypeOptions"
            size="small"
            style="width: 120px"
            @update:value="handleAssessmentTypeChange"
          />
          <n-button size="small" @click="refreshAssessment">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
          </n-button>
        </n-space>
      </n-space>
    </div>

    <!-- 总体风险等级 -->
    <div class="overall-risk">
      <n-card size="small">
        <div class="risk-level-display">
          <div class="risk-indicator">
            <n-progress
              type="circle"
              :percentage="overallRiskScore"
              :color="getRiskColor(overallRiskLevel)"
              :stroke-width="8"
              :show-indicator="false"
              style="width: 80px; height: 80px"
            />
            <div class="risk-score">{{ overallRiskScore }}</div>
          </div>
          <div class="risk-info">
            <div class="risk-level">
              <n-tag :type="getRiskTagType(overallRiskLevel)" size="large">
                {{ overallRiskLevel }}
              </n-tag>
            </div>
            <div class="risk-description">{{ getRiskDescription(overallRiskLevel) }}</div>
            <div class="risk-trend">
              <n-space align="center">
                <n-icon :color="trendColor" size="14">
                  <component :is="trendIcon" />
                </n-icon>
                <span class="trend-text">{{ trendText }}</span>
              </n-space>
            </div>
          </div>
        </div>
      </n-card>
    </div>

    <!-- 风险分类详情 -->
    <div class="risk-categories">
      <n-grid :cols="2" :x-gap="16" :y-gap="16">
        <n-grid-item v-for="category in riskCategories" :key="category.id">
          <n-card size="small" hoverable>
            <template #header>
              <n-space align="center">
                <n-icon :color="category.color" size="16">
                  <component :is="category.icon" />
                </n-icon>
                <span>{{ category.name }}</span>
                <n-tag :type="getRiskTagType(category.level)" size="small">
                  {{ category.level }}
                </n-tag>
              </n-space>
            </template>

            <div class="category-content">
              <div class="category-score">
                <n-progress
                  :percentage="category.score"
                  :color="getRiskColor(category.level)"
                  :height="6"
                  :show-indicator="false"
                />
                <span class="score-text">{{ category.score }}/100</span>
              </div>

              <div class="category-details">
                <div v-for="detail in category.details" :key="detail.name" class="detail-item">
                  <span class="detail-name">{{ detail.name }}:</span>
                  <span class="detail-value" :style="{ color: detail.color }">{{
                    detail.value
                  }}</span>
                </div>
              </div>

              <div class="category-actions">
                <n-space>
                  <n-button size="tiny" @click="viewCategoryDetail(category)"> 查看详情 </n-button>
                  <n-button size="tiny" type="primary" @click="handleCategoryRisk(category)">
                    处理风险
                  </n-button>
                </n-space>
              </div>
            </div>
          </n-card>
        </n-grid-item>
      </n-grid>
    </div>

    <!-- 风险时间线 -->
    <div class="risk-timeline">
      <n-card title="风险变化趋势" size="small">
        <div ref="timelineChartRef" style="height: 200px"></div>
      </n-card>
    </div>

    <!-- 风险建议 -->
    <div class="risk-recommendations">
      <n-card title="风险处理建议" size="small">
        <n-list>
          <n-list-item v-for="recommendation in recommendations" :key="recommendation.id">
            <template #prefix>
              <n-icon
                :color="
                  recommendation.priority === 'high'
                    ? '#d03050'
                    : recommendation.priority === 'medium'
                    ? '#f0a020'
                    : '#18a058'
                "
                size="16"
              >
                <component :is="recommendation.icon" />
              </n-icon>
            </template>
            <n-thing>
              <template #header>
                <n-space align="center">
                  <span>{{ recommendation.title }}</span>
                  <n-tag
                    :type="
                      recommendation.priority === 'high'
                        ? 'error'
                        : recommendation.priority === 'medium'
                        ? 'warning'
                        : 'success'
                    "
                    size="small"
                  >
                    {{ getPriorityText(recommendation.priority) }}
                  </n-tag>
                </n-space>
              </template>
              <template #description>
                {{ recommendation.description }}
              </template>
              <template #action>
                <n-space>
                  <n-button size="small" @click="executeRecommendation(recommendation)">
                    执行建议
                  </n-button>
                  <n-button size="small" @click="ignoreRecommendation(recommendation)">
                    忽略
                  </n-button>
                </n-space>
              </template>
            </n-thing>
          </n-list-item>
        </n-list>
      </n-card>
    </div>

    <!-- 风险详情抽屉 -->
    <n-drawer v-model:show="showRiskDetail" :width="600" placement="right">
      <n-drawer-content :title="selectedCategory?.name + ' 风险详情'">
        <div v-if="selectedCategory" class="risk-detail-content">
          <!-- 详细信息 -->
          <n-descriptions :column="2" bordered>
            <n-descriptions-item label="风险等级">
              <n-tag :type="getRiskTagType(selectedCategory.level)">
                {{ selectedCategory.level }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="风险评分">
              {{ selectedCategory.score }}/100
            </n-descriptions-item>
            <n-descriptions-item label="影响设备">
              {{ selectedCategory.affectedDevices }}台
            </n-descriptions-item>
            <n-descriptions-item label="预计损失">
              ¥{{ selectedCategory.estimatedLoss }}
            </n-descriptions-item>
            <n-descriptions-item label="发生概率">
              {{ selectedCategory.probability }}%
            </n-descriptions-item>
            <n-descriptions-item label="检测时间">
              {{ selectedCategory.detectionTime }}
            </n-descriptions-item>
          </n-descriptions>

          <!-- 风险因子 -->
          <div class="risk-factors">
            <h4>主要风险因子</h4>
            <n-list>
              <n-list-item v-for="factor in selectedCategory.riskFactors" :key="factor.name">
                <n-thing>
                  <template #header>{{ factor.name }}</template>
                  <template #description>{{ factor.description }}</template>
                  <template #action>
                    <n-progress
                      :percentage="factor.contribution"
                      :color="
                        factor.contribution > 70
                          ? '#d03050'
                          : factor.contribution > 40
                          ? '#f0a020'
                          : '#18a058'
                      "
                      :height="4"
                      style="width: 100px"
                    />
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </div>

          <!-- 处理历史 -->
          <div class="risk-history">
            <h4>处理历史</h4>
            <n-timeline>
              <n-timeline-item
                v-for="history in selectedCategory.history"
                :key="history.id"
                :type="history.type"
                :title="history.action"
                :content="history.description"
                :time="history.time"
              />
            </n-timeline>
          </div>
        </div>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useMessage } from 'naive-ui'
import * as echarts from 'echarts'
import {
  WarningOutline,
  RefreshOutline,
  TrendingUpOutline,
  TrendingDownOutline,
  RemoveOutline,
  ThermometerOutline,
  FlashOutline,
  HardwareChipOutline,
  SpeedometerOutline,
  AlertCircleOutline,
  CheckmarkCircleOutline,
  TimeOutline,
} from '@vicons/ionicons5'

const message = useMessage()

// 响应式数据
const assessmentType = ref('comprehensive')
const showRiskDetail = ref(false)
const selectedCategory = ref(null)
const timelineChartRef = ref(null)
let timelineChart = null

// 评估类型选项
const assessmentTypeOptions = [
  { label: '综合评估', value: 'comprehensive' },
  { label: '设备风险', value: 'device' },
  { label: '运行风险', value: 'operation' },
  { label: '维护风险', value: 'maintenance' },
]

// 总体风险数据
const overallRiskScore = ref(73)
const overallRiskLevel = computed(() => {
  const score = overallRiskScore.value
  if (score >= 80) return '高风险'
  if (score >= 60) return '中风险'
  if (score >= 40) return '低风险'
  return '安全'
})

// 趋势数据
const riskTrend = ref('rising') // 'rising' | 'falling' | 'stable'
const trendColor = computed(() => {
  switch (riskTrend.value) {
    case 'rising':
      return '#d03050'
    case 'falling':
      return '#18a058'
    case 'stable':
      return '#2080f0'
    default:
      return '#999'
  }
})

const trendIcon = computed(() => {
  switch (riskTrend.value) {
    case 'rising':
      return TrendingUpOutline
    case 'falling':
      return TrendingDownOutline
    case 'stable':
      return RemoveOutline
    default:
      return RemoveOutline
  }
})

const trendText = computed(() => {
  switch (riskTrend.value) {
    case 'rising':
      return '风险上升'
    case 'falling':
      return '风险下降'
    case 'stable':
      return '风险稳定'
    default:
      return '无数据'
  }
})

// 风险分类数据
const riskCategories = ref([
  {
    id: 1,
    name: '温度风险',
    level: '高风险',
    score: 85,
    color: '#d03050',
    icon: ThermometerOutline,
    affectedDevices: 12,
    estimatedLoss: '50,000',
    probability: 78,
    detectionTime: '2024-01-15 14:30',
    details: [
      { name: '超温设备', value: '12台', color: '#d03050' },
      { name: '平均温度', value: '85°C', color: '#f0a020' },
      { name: '预警次数', value: '23次', color: '#d03050' },
    ],
    riskFactors: [
      { name: '环境温度过高', description: '车间环境温度超过正常范围', contribution: 85 },
      { name: '散热系统故障', description: '部分设备散热系统效率下降', contribution: 72 },
      { name: '负载过重', description: '设备长时间高负载运行', contribution: 65 },
    ],
    history: [
      {
        id: 1,
        type: 'error',
        action: '发现温度异常',
        description: '设备温度超过阈值',
        time: '2024-01-15 14:30',
      },
      {
        id: 2,
        type: 'warning',
        action: '启动应急措施',
        description: '降低设备负载',
        time: '2024-01-15 14:35',
      },
      {
        id: 3,
        type: 'info',
        action: '维护人员到场',
        description: '开始检查散热系统',
        time: '2024-01-15 15:00',
      },
    ],
  },
  {
    id: 2,
    name: '电力风险',
    level: '中风险',
    score: 65,
    color: '#f0a020',
    icon: FlashOutline,
    affectedDevices: 8,
    estimatedLoss: '30,000',
    probability: 45,
    detectionTime: '2024-01-15 13:45',
    details: [
      { name: '电压波动', value: '±8%', color: '#f0a020' },
      { name: '功率因数', value: '0.82', color: '#f0a020' },
      { name: '谐波含量', value: '12%', color: '#d03050' },
    ],
    riskFactors: [
      { name: '电网不稳定', description: '供电质量波动较大', contribution: 68 },
      { name: '负载不平衡', description: '三相负载分配不均', contribution: 55 },
      { name: '老化线路', description: '部分电力线路老化', contribution: 42 },
    ],
    history: [
      {
        id: 1,
        type: 'warning',
        action: '检测到电压波动',
        description: '电压超出正常范围',
        time: '2024-01-15 13:45',
      },
      {
        id: 2,
        type: 'info',
        action: '调整负载分配',
        description: '重新分配设备负载',
        time: '2024-01-15 14:00',
      },
    ],
  },
  {
    id: 3,
    name: '机械风险',
    level: '中风险',
    score: 58,
    color: '#f0a020',
    icon: HardwareChipOutline,
    affectedDevices: 5,
    estimatedLoss: '25,000',
    probability: 38,
    detectionTime: '2024-01-15 12:20',
    details: [
      { name: '振动异常', value: '3台', color: '#f0a020' },
      { name: '磨损程度', value: '中等', color: '#f0a020' },
      { name: '润滑状态', value: '良好', color: '#18a058' },
    ],
    riskFactors: [
      { name: '轴承磨损', description: '部分轴承出现磨损迹象', contribution: 62 },
      { name: '振动增大', description: '设备振动超过正常范围', contribution: 48 },
      { name: '润滑不足', description: '润滑油更换周期延长', contribution: 35 },
    ],
    history: [
      {
        id: 1,
        type: 'info',
        action: '定期检查',
        description: '进行设备例行检查',
        time: '2024-01-15 12:20',
      },
      {
        id: 2,
        type: 'warning',
        action: '发现振动异常',
        description: '设备振动值超标',
        time: '2024-01-15 12:25',
      },
    ],
  },
  {
    id: 4,
    name: '性能风险',
    level: '低风险',
    score: 35,
    color: '#18a058',
    icon: SpeedometerOutline,
    affectedDevices: 3,
    estimatedLoss: '10,000',
    probability: 25,
    detectionTime: '2024-01-15 11:30',
    details: [
      { name: '效率下降', value: '5%', color: '#f0a020' },
      { name: '产能影响', value: '轻微', color: '#18a058' },
      { name: '质量指标', value: '正常', color: '#18a058' },
    ],
    riskFactors: [
      { name: '设备老化', description: '设备使用年限较长', contribution: 45 },
      { name: '工艺参数偏移', description: '部分工艺参数偏离最优值', contribution: 32 },
      { name: '操作不当', description: '操作人员技能有待提升', contribution: 28 },
    ],
    history: [
      {
        id: 1,
        type: 'info',
        action: '性能监控',
        description: '监控设备性能指标',
        time: '2024-01-15 11:30',
      },
      {
        id: 2,
        type: 'info',
        action: '参数优化',
        description: '调整工艺参数',
        time: '2024-01-15 12:00',
      },
    ],
  },
])

// 风险建议数据
const recommendations = ref([
  {
    id: 1,
    title: '立即检查高温设备散热系统',
    description: '12台设备温度超标，建议立即检查散热系统并降低负载',
    priority: 'high',
    icon: AlertCircleOutline,
  },
  {
    id: 2,
    title: '优化电力负载分配',
    description: '调整三相负载分配，减少电压波动对设备的影响',
    priority: 'medium',
    icon: FlashOutline,
  },
  {
    id: 3,
    title: '安排设备维护计划',
    description: '对振动异常的设备进行深度检查和维护',
    priority: 'medium',
    icon: HardwareChipOutline,
  },
  {
    id: 4,
    title: '优化工艺参数',
    description: '调整设备工艺参数，提升运行效率',
    priority: 'low',
    icon: SpeedometerOutline,
  },
])

// 方法
const getRiskColor = (level) => {
  switch (level) {
    case '高风险':
      return '#d03050'
    case '中风险':
      return '#f0a020'
    case '低风险':
      return '#18a058'
    case '安全':
      return '#2080f0'
    default:
      return '#999'
  }
}

const getRiskTagType = (level) => {
  switch (level) {
    case '高风险':
      return 'error'
    case '中风险':
      return 'warning'
    case '低风险':
      return 'success'
    case '安全':
      return 'info'
    default:
      return 'default'
  }
}

const getRiskDescription = (level) => {
  switch (level) {
    case '高风险':
      return '需要立即采取措施'
    case '中风险':
      return '需要密切关注'
    case '低风险':
      return '保持正常监控'
    case '安全':
      return '运行状态良好'
    default:
      return '状态未知'
  }
}

const getPriorityText = (priority) => {
  switch (priority) {
    case 'high':
      return '高优先级'
    case 'medium':
      return '中优先级'
    case 'low':
      return '低优先级'
    default:
      return '普通'
  }
}

const handleAssessmentTypeChange = () => {
  // 根据评估类型更新数据
  message.info(
    `已切换到${assessmentTypeOptions.find((opt) => opt.value === assessmentType.value)?.label}模式`
  )
}

const refreshAssessment = () => {
  // 刷新风险评估数据
  overallRiskScore.value = Math.floor(Math.random() * 40) + 50
  message.success('风险评估数据已刷新')
}

const viewCategoryDetail = (category) => {
  selectedCategory.value = category
  showRiskDetail.value = true
}

const handleCategoryRisk = (category) => {
  message.info(`正在处理${category.name}...`)
}

const executeRecommendation = (recommendation) => {
  message.success(`正在执行建议: ${recommendation.title}`)
}

const ignoreRecommendation = (recommendation) => {
  message.info(`已忽略建议: ${recommendation.title}`)
}

// 初始化时间线图表
const initTimelineChart = () => {
  if (!timelineChartRef.value) return

  timelineChart = echarts.init(timelineChartRef.value)

  // 生成时间线数据
  const dates = []
  const riskScores = []
  const now = new Date()

  for (let i = 29; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
    dates.push(date.toISOString().split('T')[0])
    riskScores.push(Math.floor(Math.random() * 30) + 50)
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: function (params) {
        return `${params[0].axisValue}<br/>风险评分: ${params[0].value}`
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
      data: dates,
      axisLabel: {
        fontSize: 10,
        formatter: function (value) {
          return value.split('-').slice(1).join('-')
        },
      },
    },
    yAxis: {
      type: 'value',
      name: '风险评分',
      nameTextStyle: {
        fontSize: 10,
      },
      axisLabel: {
        fontSize: 10,
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
        name: '风险评分',
        type: 'line',
        data: riskScores,
        smooth: true,
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(208, 48, 80, 0.3)' },
              { offset: 1, color: 'rgba(208, 48, 80, 0.1)' },
            ],
          },
        },
        lineStyle: {
          color: '#d03050',
          width: 2,
        },
        itemStyle: {
          color: '#d03050',
        },
        symbol: 'circle',
        symbolSize: 4,
      },
    ],
  }

  timelineChart.setOption(option)

  // 响应式调整
  window.addEventListener('resize', () => {
    if (timelineChart) {
      timelineChart.resize()
    }
  })
}

// 生命周期
onMounted(() => {
  nextTick(() => {
    initTimelineChart()
  })
})

onBeforeUnmount(() => {
  if (timelineChart) {
    timelineChart.dispose()
  }
})
</script>

<style scoped>
.risk-assessment {
  width: 100%;
}

.assessment-header {
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.header-title {
  font-weight: 500;
  font-size: 14px;
}

.overall-risk {
  margin-bottom: 24px;
}

.risk-level-display {
  display: flex;
  align-items: center;
  gap: 24px;
}

.risk-indicator {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.risk-score {
  position: absolute;
  font-size: 18px;
  font-weight: bold;
  color: #333;
}

.risk-info {
  flex: 1;
}

.risk-level {
  margin-bottom: 8px;
}

.risk-description {
  color: #666;
  font-size: 13px;
  margin-bottom: 8px;
}

.trend-text {
  font-size: 12px;
  color: #666;
}

.risk-categories {
  margin-bottom: 24px;
}

.category-content {
  padding: 0;
}

.category-score {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.score-text {
  font-size: 12px;
  color: #666;
  min-width: 50px;
}

.category-details {
  margin-bottom: 12px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  font-size: 12px;
}

.detail-name {
  color: #666;
}

.detail-value {
  font-weight: 500;
}

.category-actions {
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

.risk-timeline {
  margin-bottom: 24px;
}

.risk-recommendations {
  margin-bottom: 24px;
}

.risk-detail-content {
  padding: 0;
}

.risk-factors {
  margin-top: 24px;
}

.risk-factors h4 {
  margin-bottom: 12px;
  font-size: 14px;
  color: #333;
}

.risk-history {
  margin-top: 24px;
}

.risk-history h4 {
  margin-bottom: 12px;
  font-size: 14px;
  color: #333;
}
</style>
