<template>
  <div class="dynamic-data-display">
    <!-- 视图切换 -->
    <div v-if="showViewToggle" class="view-toggle">
      <n-radio-group v-model:value="currentView" size="small">
        <n-radio-button value="cards">
          <n-icon :component="GridOutline" />
          卡片
        </n-radio-button>
        <n-radio-button value="table">
          <n-icon :component="ListOutline" />
          表格
        </n-radio-button>
        <n-radio-button value="charts">
          <n-icon :component="StatsChartOutline" />
          图表
        </n-radio-button>
        <n-radio-button value="monitor">
          <n-icon :component="PulseOutline" />
          监控
        </n-radio-button>
      </n-radio-group>
    </div>

    <!-- 加载状态 -->
    <n-spin :show="loading">
      <!-- 卡片视图 -->
      <div v-if="currentView === 'cards'" class="cards-container">
        <template v-for="group in signalGroups" :key="group.name">
          <div v-if="group.signals.length > 0" class="group-section">
            <div class="group-header">
              <n-icon :component="getGroupIcon(group.name)" :size="18" />
              <span>{{ group.title }}</span>
            </div>
            <div class="signal-cards">
              <SignalCard
                v-for="signal in group.signals"
                :key="signal.code"
                :signal="signal"
                :value="getSignalValue(signal.code)"
                :previous-value="getPreviousValue(signal.code)"
                :show-trend="showTrend"
                :show-mini-chart="showMiniChart"
                :history-data="getHistoryData(signal.code)"
                @click="handleSignalClick(signal)"
              />
            </div>
          </div>
        </template>
      </div>

      <!-- 表格视图 -->
      <div v-else-if="currentView === 'table'" class="table-container">
        <n-data-table
          :columns="tableColumns"
          :data="tableData"
          :pagination="false"
          :bordered="false"
          size="small"
          striped
        />
      </div>

      <!-- 图表视图 -->
      <div v-else-if="currentView === 'charts'" class="charts-container">
        <div class="chart-grid">
          <SignalChart
            v-for="signal in chartSignals"
            :key="signal.code"
            :signal="signal"
            :data="getHistoryData(signal.code)"
            :height="chartHeight"
          />
        </div>
      </div>

      <!-- 实时监控视图 -->
      <div v-else-if="currentView === 'monitor'" class="monitor-container">
        <RealtimeMonitor
          :signals="monitorSignals"
          :data="signalData"
          :refresh-interval="refreshInterval"
          @refresh="handleRefresh"
        />
      </div>
    </n-spin>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, h } from 'vue'
import { NRadioGroup, NRadioButton, NIcon, NSpin, NDataTable, NTag } from 'naive-ui'
import { 
  GridOutline, 
  ListOutline, 
  StatsChartOutline, 
  PulseOutline,
  SettingsOutline,
  ThermometerOutline,
  FlashOutline,
  SpeedometerOutline,
  TrendingUpOutline,
  TrendingDownOutline,
  RemoveOutline
} from '@vicons/ionicons5'
import { useSignalDefinitions } from '../composables/useSignalDefinitions'
import SignalCard from './SignalCard.vue'
import SignalChart from './SignalChart.vue'
import RealtimeMonitor from './RealtimeMonitor.vue'

// Props
const props = defineProps({
  // 资产类别ID
  categoryId: {
    type: [Number, String],
    required: true
  },
  // 信号数据
  signalData: {
    type: Object,
    default: () => ({})
  },
  // 历史数据
  historyData: {
    type: Object,
    default: () => ({})
  },
  // 上一次数据（用于趋势显示）
  previousData: {
    type: Object,
    default: () => ({})
  },
  // 显示模式
  defaultView: {
    type: String,
    default: 'cards'
  },
  // 显示选项
  showViewToggle: {
    type: Boolean,
    default: true
  },
  showTrend: {
    type: Boolean,
    default: true
  },
  showMiniChart: {
    type: Boolean,
    default: false
  },
  // 图表高度
  chartHeight: {
    type: Number,
    default: 200
  },
  // 刷新间隔（毫秒）
  refreshInterval: {
    type: Number,
    default: 5000
  },
  // 加载状态
  loading: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['signal-click', 'refresh'])

// 使用信号定义组合式函数
const { 
  signals, 
  signalGroups, 
  realtimeSignals,
  formatSignalValue,
  getGroupTitle
} = useSignalDefinitions(props.categoryId)

// 当前视图
const currentView = ref(props.defaultView)

// 图表信号（数值类型且有历史数据）
const chartSignals = computed(() => {
  return signals.value.filter(s => 
    isNumericType(s.data_type) && 
    props.historyData[s.code]?.length > 0
  )
})

// 监控信号
const monitorSignals = computed(() => {
  return realtimeSignals.value
})

// 表格列配置
const tableColumns = computed(() => {
  const columns = [
    {
      title: '信号名称',
      key: 'name',
      width: 150,
      fixed: 'left'
    },
    {
      title: '当前值',
      key: 'value',
      width: 120,
      render: (row) => {
        return h('span', {
          style: { fontWeight: 'bold' }
        }, row.formattedValue)
      }
    },
    {
      title: '单位',
      key: 'unit',
      width: 80
    },
    {
      title: '趋势',
      key: 'trend',
      width: 80,
      render: (row) => {
        if (!row.trend) return '-'
        const icon = row.trend === 'up' ? TrendingUpOutline : 
                     row.trend === 'down' ? TrendingDownOutline : RemoveOutline
        const color = row.trend === 'up' ? '#18a058' : 
                      row.trend === 'down' ? '#d03050' : '#999'
        return h(NIcon, { component: icon, color, size: 18 })
      }
    },
    {
      title: '状态',
      key: 'status',
      width: 100,
      render: (row) => {
        const statusMap = {
          normal: { type: 'success', text: '正常' },
          warning: { type: 'warning', text: '警告' },
          error: { type: 'error', text: '异常' }
        }
        const status = statusMap[row.status] || statusMap.normal
        return h(NTag, { type: status.type, size: 'small' }, () => status.text)
      }
    }
  ]
  return columns
})

// 表格数据
const tableData = computed(() => {
  return signals.value.map(signal => {
    const value = getSignalValue(signal.code)
    const previousValue = getPreviousValue(signal.code)
    
    return {
      code: signal.code,
      name: signal.name,
      value,
      formattedValue: formatSignalValue(value, signal),
      unit: signal.unit || '-',
      trend: getTrend(value, previousValue, signal.data_type),
      status: getSignalStatus(value, signal)
    }
  })
})

// 获取信号值
function getSignalValue(code) {
  return props.signalData[code]
}

// 获取上一次值
function getPreviousValue(code) {
  return props.previousData[code]
}

// 获取历史数据
function getHistoryData(code) {
  return props.historyData[code] || []
}

// 获取趋势
function getTrend(current, previous, dataType) {
  if (!isNumericType(dataType) || previous === undefined || previous === null) {
    return null
  }
  const curr = Number(current)
  const prev = Number(previous)
  if (curr > prev) return 'up'
  if (curr < prev) return 'down'
  return 'stable'
}

// 获取信号状态
function getSignalStatus(value, signal) {
  if (!signal.value_range || !isNumericType(signal.data_type)) {
    return 'normal'
  }

  const numValue = Number(value)
  const { min, max } = signal.value_range

  if ((min !== undefined && numValue < min) || (max !== undefined && numValue > max)) {
    return 'error'
  }

  // 警告范围检查
  if (min !== undefined && max !== undefined) {
    const range = max - min
    const warningLow = min + range * 0.1
    const warningHigh = max - range * 0.1
    if (numValue <= warningLow || numValue >= warningHigh) {
      return 'warning'
    }
  }

  return 'normal'
}

// 获取分组图标
function getGroupIcon(groupName) {
  const icons = {
    core: SettingsOutline,
    temperature: ThermometerOutline,
    power: FlashOutline,
    speed: SpeedometerOutline,
    other: SettingsOutline,
    default: SettingsOutline
  }
  return icons[groupName] || SettingsOutline
}

// 判断是否为数值类型
function isNumericType(dataType) {
  return ['float', 'int', 'double', 'bigint'].includes(dataType)
}

// 处理信号点击
function handleSignalClick(signal) {
  emit('signal-click', signal)
}

// 处理刷新
function handleRefresh() {
  emit('refresh')
}
</script>

<style scoped>
.dynamic-data-display {
  width: 100%;
}

.view-toggle {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}

.cards-container {
  padding: 8px;
}

.group-section {
  margin-bottom: 24px;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
  color: var(--n-text-color);
}

.signal-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.table-container {
  padding: 8px;
}

.charts-container {
  padding: 8px;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 16px;
}

.monitor-container {
  padding: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .signal-cards {
    grid-template-columns: 1fr;
  }

  .chart-grid {
    grid-template-columns: 1fr;
  }

  .view-toggle {
    justify-content: center;
  }
}
</style>
