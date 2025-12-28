<!-- 动态数据展示组件 - 基于元数据的数据可视化 -->

<template>
  <div class="dynamic-data-display">
    <!-- 数据卡片视图 -->
    <div v-if="displayMode === 'cards'" class="cards-container">
      <template v-for="group in signalGroups" :key="group.name">
        <!-- 分组标题 -->
        <div class="group-header" v-if="group.signals.length > 0">
          <n-icon :component="getGroupIcon(group.name)" />
          <span>{{ getGroupTitle(group.name) }}</span>
        </div>

        <!-- 信号卡片 -->
        <div class="signal-cards">
          <n-card
            v-for="signal in group.signals"
            :key="signal.code"
            class="signal-card"
            :class="getSignalCardClass(signal)"
            size="small"
            hoverable
          >
            <template #header>
              <div class="signal-header">
                <span class="signal-name">{{ signal.name }}</span>
                <n-tag
                  v-if="getSignalStatus(signal)"
                  :type="getSignalStatus(signal).type"
                  size="small"
                >
                  {{ getSignalStatus(signal).text }}
                </n-tag>
              </div>
            </template>

            <div class="signal-content">
              <!-- 数值显示 -->
              <div class="signal-value">
                <span class="value">{{ formatSignalValue(signal) }}</span>
                <span class="unit" v-if="signal.unit">{{ signal.unit }}</span>
              </div>

              <!-- 趋势图标 -->
              <div class="signal-trend" v-if="showTrend">
                <n-icon
                  :component="getTrendIcon(signal)"
                  :color="getTrendColor(signal)"
                  size="16"
                />
              </div>
            </div>

            <!-- 进度条 (用于显示范围内的值) -->
            <n-progress
              v-if="signal.value_range && isNumericType(signal.data_type)"
              :percentage="getProgressPercentage(signal)"
              :color="getProgressColor(signal)"
              :show-indicator="false"
              :height="4"
              style="margin-top: 8px"
            />

            <!-- 迷你图表 -->
            <div class="mini-chart" v-if="showMiniChart && signal.history_data">
              <mini-line-chart
                :data="signal.history_data"
                :height="40"
                :color="getSignalColor(signal)"
              />
            </div>
          </n-card>
        </div>
      </template>
    </div>

    <!-- 表格视图 -->
    <div v-else-if="displayMode === 'table'" class="table-container">
      <n-data-table
        :columns="tableColumns"
        :data="tableData"
        :pagination="false"
        :bordered="false"
        size="small"
      />
    </div>

    <!-- 图表视图 -->
    <div v-else-if="displayMode === 'charts'" class="charts-container">
      <div class="chart-grid">
        <n-card
          v-for="signal in chartSignals"
          :key="signal.code"
          class="chart-card"
          size="small"
        >
          <template #header>
            {{ signal.name }}
            <span v-if="signal.unit" class="chart-unit">({{ signal.unit }})</span>
          </template>

          <signal-chart
            :signal="signal"
            :data="signal.history_data || []"
            :height="200"
            :type="getChartType(signal)"
          />
        </n-card>
      </div>
    </div>

    <!-- 实时监控视图 -->
    <div v-else-if="displayMode === 'monitor'" class="monitor-container">
      <div class="monitor-grid">
        <div
          v-for="signal in monitorSignals"
          :key="signal.code"
          class="monitor-item"
          :class="getMonitorItemClass(signal)"
        >
          <div class="monitor-label">{{ signal.name }}</div>
          <div class="monitor-value">
            {{ formatSignalValue(signal) }}
            <span v-if="signal.unit" class="monitor-unit">{{ signal.unit }}</span>
          </div>
          <div class="monitor-status">
            <n-icon
              :component="getStatusIcon(signal)"
              :color="getStatusColor(signal)"
              size="20"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { NCard, NIcon, NTag, NProgress, NDataTable } from 'naive-ui'
import {
  TrendingUpOutline,
  TrendingDownOutline,
  RemoveOutline,
  CheckmarkCircleOutline,
  WarningOutline,
  CloseCircleOutline,
  SettingsOutline,
  ThermometerOutline,
  FlashOutline,
  SpeedometerOutline
} from '@vicons/ionicons5'
import MiniLineChart from './MiniLineChart.vue'
import SignalChart from './SignalChart.vue'

// 类型定义
interface SignalDefinition {
  code: string
  name: string
  data_type: string
  unit?: string
  value_range?: {
    min?: number
    max?: number
  }
  display_config?: {
    group?: string
    chart_type?: string
    color?: string
    show_in_monitor?: boolean
  }
}

interface SignalData extends SignalDefinition {
  value: any
  previous_value?: any
  history_data?: Array<{ timestamp: string; value: number }>
  status?: 'normal' | 'warning' | 'error'
  last_update?: string
}

interface SignalGroup {
  name: string
  title: string
  icon: any
  signals: SignalData[]
}

// Props
interface Props {
  // 信号定义和数据
  signals: SignalData[]
  // 显示模式
  displayMode: 'cards' | 'table' | 'charts' | 'monitor'
  // 显示选项
  showTrend?: boolean
  showMiniChart?: boolean
  showStatus?: boolean
  // 布局选项
  cardsPerRow?: number
  chartHeight?: number
}

const props = withDefaults(defineProps<Props>(), {
  displayMode: 'cards',
  showTrend: true,
  showMiniChart: false,
  showStatus: true,
  cardsPerRow: 4,
  chartHeight: 300
})

// 计算属性 - 信号分组
const signalGroups = computed<SignalGroup[]>(() => {
  const groups: Record<string, SignalData[]> = {
    core: [],
    temperature: [],
    power: [],
    speed: [],
    other: []
  }

  props.signals.forEach(signal => {
    const groupName = signal.display_config?.group || 'other'
    if (groups[groupName]) {
      groups[groupName].push(signal)
    } else {
      groups.other.push(signal)
    }
  })

  return Object.entries(groups)
    .filter(([_, signals]) => signals.length > 0)
    .map(([name, signals]) => ({
      name,
      title: getGroupTitle(name),
      icon: getGroupIcon(name),
      signals
    }))
})

// 计算属性 - 表格数据
const tableData = computed(() => {
  return props.signals.map(signal => ({
    name: signal.name,
    value: formatSignalValue(signal),
    unit: signal.unit || '-',
    status: getSignalStatus(signal)?.text || '正常',
    lastUpdate: signal.last_update || '-'
  }))
})

// 计算属性 - 表格列定义
const tableColumns = computed(() => [
  {
    title: '信号名称',
    key: 'name',
    width: 150
  },
  {
    title: '当前值',
    key: 'value',
    width: 120,
    render: (row: any) => {
      return h('span', {
        style: {
          fontWeight: 'bold',
          color: getValueColor(row.value)
        }
      }, row.value)
    }
  },
  {
    title: '单位',
    key: 'unit',
    width: 80
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row: any) => {
      const status = getSignalStatusByText(row.status)
      return h(NTag, {
        type: status?.type || 'default',
        size: 'small'
      }, () => row.status)
    }
  },
  {
    title: '更新时间',
    key: 'lastUpdate',
    width: 150
  }
])

// 计算属性 - 图表信号
const chartSignals = computed(() => {
  return props.signals.filter(signal => 
    isNumericType(signal.data_type) && signal.history_data && signal.history_data.length > 0
  )
})

// 计算属性 - 监控信号
const monitorSignals = computed(() => {
  return props.signals.filter(signal => 
    signal.display_config?.show_in_monitor !== false
  )
})

// 方法 - 获取分组标题
function getGroupTitle(groupName: string): string {
  const titles: Record<string, string> = {
    core: '核心参数',
    temperature: '温度监控',
    power: '功率参数',
    speed: '速度参数',
    other: '其他参数'
  }
  return titles[groupName] || groupName
}

// 方法 - 获取分组图标
function getGroupIcon(groupName: string) {
  const icons: Record<string, any> = {
    core: SettingsOutline,
    temperature: ThermometerOutline,
    power: FlashOutline,
    speed: SpeedometerOutline,
    other: SettingsOutline
  }
  return icons[groupName] || SettingsOutline
}

// 方法 - 格式化信号值
function formatSignalValue(signal: SignalData): string {
  if (signal.value === null || signal.value === undefined) {
    return '-'
  }

  switch (signal.data_type) {
    case 'float':
      return typeof signal.value === 'number' ? signal.value.toFixed(2) : String(signal.value)
    case 'int':
      return String(Math.round(Number(signal.value)))
    case 'bool':
      return signal.value ? '开启' : '关闭'
    case 'string':
      return String(signal.value)
    default:
      return String(signal.value)
  }
}

// 方法 - 获取信号状态
function getSignalStatus(signal: SignalData) {
  if (!signal.value_range || !isNumericType(signal.data_type)) {
    return signal.status ? {
      type: signal.status === 'normal' ? 'success' : signal.status === 'warning' ? 'warning' : 'error',
      text: signal.status === 'normal' ? '正常' : signal.status === 'warning' ? '警告' : '异常'
    } : null
  }

  const value = Number(signal.value)
  const { min, max } = signal.value_range

  if (min !== undefined && value < min) {
    return { type: 'error', text: '过低' }
  }
  if (max !== undefined && value > max) {
    return { type: 'error', text: '过高' }
  }

  // 警告范围 (90% - 100% 或 0% - 10%)
  if (min !== undefined && max !== undefined) {
    const range = max - min
    const warningLow = min + range * 0.1
    const warningHigh = max - range * 0.1

    if (value <= warningLow || value >= warningHigh) {
      return { type: 'warning', text: '警告' }
    }
  }

  return { type: 'success', text: '正常' }
}

// 方法 - 根据文本获取状态
function getSignalStatusByText(statusText: string) {
  const statusMap: Record<string, any> = {
    '正常': { type: 'success' },
    '警告': { type: 'warning' },
    '异常': { type: 'error' },
    '过低': { type: 'error' },
    '过高': { type: 'error' }
  }
  return statusMap[statusText]
}

// 方法 - 获取信号卡片样式类
function getSignalCardClass(signal: SignalData): string {
  const status = getSignalStatus(signal)
  if (!status) return ''
  
  return `signal-card--${status.type}`
}

// 方法 - 获取趋势图标
function getTrendIcon(signal: SignalData) {
  if (!signal.previous_value || !isNumericType(signal.data_type)) {
    return RemoveOutline
  }

  const current = Number(signal.value)
  const previous = Number(signal.previous_value)

  if (current > previous) return TrendingUpOutline
  if (current < previous) return TrendingDownOutline
  return RemoveOutline
}

// 方法 - 获取趋势颜色
function getTrendColor(signal: SignalData): string {
  if (!signal.previous_value || !isNumericType(signal.data_type)) {
    return '#999'
  }

  const current = Number(signal.value)
  const previous = Number(signal.previous_value)

  if (current > previous) return '#18a058'
  if (current < previous) return '#d03050'
  return '#999'
}

// 方法 - 获取进度百分比
function getProgressPercentage(signal: SignalData): number {
  if (!signal.value_range || !isNumericType(signal.data_type)) {
    return 0
  }

  const { min = 0, max = 100 } = signal.value_range
  const value = Number(signal.value)
  
  return Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100))
}

// 方法 - 获取进度条颜色
function getProgressColor(signal: SignalData): string {
  const status = getSignalStatus(signal)
  
  switch (status?.type) {
    case 'success': return '#18a058'
    case 'warning': return '#f0a020'
    case 'error': return '#d03050'
    default: return '#2080f0'
  }
}

// 方法 - 获取信号颜色
function getSignalColor(signal: SignalData): string {
  return signal.display_config?.color || '#2080f0'
}

// 方法 - 获取图表类型
function getChartType(signal: SignalData): string {
  return signal.display_config?.chart_type || 'line'
}

// 方法 - 获取状态图标
function getStatusIcon(signal: SignalData) {
  const status = getSignalStatus(signal)
  
  switch (status?.type) {
    case 'success': return CheckmarkCircleOutline
    case 'warning': return WarningOutline
    case 'error': return CloseCircleOutline
    default: return CheckmarkCircleOutline
  }
}

// 方法 - 获取状态颜色
function getStatusColor(signal: SignalData): string {
  const status = getSignalStatus(signal)
  
  switch (status?.type) {
    case 'success': return '#18a058'
    case 'warning': return '#f0a020'
    case 'error': return '#d03050'
    default: return '#18a058'
  }
}

// 方法 - 获取监控项样式类
function getMonitorItemClass(signal: SignalData): string {
  const status = getSignalStatus(signal)
  return `monitor-item--${status?.type || 'normal'}`
}

// 方法 - 获取值颜色
function getValueColor(value: string): string {
  if (value === '-') return '#999'
  return '#333'
}

// 工具方法 - 判断是否为数值类型
function isNumericType(dataType: string): boolean {
  return ['float', 'int'].includes(dataType)
}
</script>

<style scoped>
.dynamic-data-display {
  width: 100%;
}

/* 卡片视图样式 */
.cards-container {
  padding: 16px;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 24px 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--n-text-color);
}

.signal-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.signal-card {
  transition: all 0.3s ease;
}

.signal-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.signal-card--success {
  border-left: 4px solid #18a058;
}

.signal-card--warning {
  border-left: 4px solid #f0a020;
}

.signal-card--error {
  border-left: 4px solid #d03050;
}

.signal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.signal-name {
  font-weight: 500;
  font-size: 14px;
}

.signal-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.signal-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.value {
  font-size: 24px;
  font-weight: 600;
  color: var(--n-text-color);
}

.unit {
  font-size: 12px;
  color: var(--n-text-color-3);
}

.signal-trend {
  display: flex;
  align-items: center;
}

.mini-chart {
  margin-top: 12px;
}

/* 表格视图样式 */
.table-container {
  padding: 16px;
}

/* 图表视图样式 */
.charts-container {
  padding: 16px;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 16px;
}

.chart-card {
  min-height: 280px;
}

.chart-unit {
  color: var(--n-text-color-3);
  font-size: 12px;
  font-weight: normal;
}

/* 监控视图样式 */
.monitor-container {
  padding: 16px;
}

.monitor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.monitor-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  border-radius: 8px;
  background: var(--n-card-color);
  border: 1px solid var(--n-border-color);
  transition: all 0.3s ease;
}

.monitor-item:hover {
  transform: scale(1.02);
}

.monitor-item--success {
  border-color: #18a058;
  background: linear-gradient(135deg, rgba(24, 160, 88, 0.1), transparent);
}

.monitor-item--warning {
  border-color: #f0a020;
  background: linear-gradient(135deg, rgba(240, 160, 32, 0.1), transparent);
}

.monitor-item--error {
  border-color: #d03050;
  background: linear-gradient(135deg, rgba(208, 48, 80, 0.1), transparent);
}

.monitor-label {
  font-size: 12px;
  color: var(--n-text-color-3);
  margin-bottom: 8px;
  text-align: center;
}

.monitor-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--n-text-color);
  margin-bottom: 8px;
  text-align: center;
}

.monitor-unit {
  font-size: 12px;
  color: var(--n-text-color-3);
  font-weight: normal;
  margin-left: 4px;
}

.monitor-status {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .signal-cards {
    grid-template-columns: 1fr;
  }
  
  .chart-grid {
    grid-template-columns: 1fr;
  }
  
  .monitor-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }
}
</style>