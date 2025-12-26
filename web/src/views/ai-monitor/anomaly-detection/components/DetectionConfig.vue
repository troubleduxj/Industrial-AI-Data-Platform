<template>
  <div class="detection-config">
    <!-- 顶部操作栏 -->
    <div class="config-header">
      <n-space justify="space-between" align="center">
        <n-space align="center">
          <!-- 新增模式：显示设备选择器 -->
          <DeviceSelector
            v-if="props.mode === 'add'"
            v-model:modelValue="selectedDeviceId"
            :auto-load="true"
            :filterable="true"
            placeholder="请选择需要监控的设备"
            style="width: 280px"
            @change="handleDeviceChange"
          />
          <!-- 编辑模式：显示设备信息 -->
          <div v-else class="device-info-display">
            <n-tag type="info" size="large">
              <template #icon><n-icon><ServerOutline /></n-icon></template>
              {{ currentDeviceName || currentDeviceCode }}
            </n-tag>
          </div>
          <n-switch v-model:value="isSimulationEnabled" size="medium">
            <template #checked>模拟数据</template>
            <template #unchecked>实时数据</template>
          </n-switch>
        </n-space>
        <n-space>
          <n-button
            :type="isDetecting ? 'error' : 'primary'"
            @click="toggleDetection"
          >
            <template #icon>
              <n-icon>
                <StopOutline v-if="isDetecting" />
                <PlayOutline v-else />
              </n-icon>
            </template>
            {{ isDetecting ? '停止检测' : '开始检测' }}
          </n-button>
        </n-space>
      </n-space>
    </div>

    <!-- 检测状态统计卡片 -->
    <n-grid :cols="4" :x-gap="16" class="mb-4">
      <n-grid-item>
        <n-card size="small" :bordered="false" class="stats-card">
          <n-statistic label="检测状态" :value="detectionStatusText">
            <template #prefix>
              <n-icon :color="isDetecting ? '#18a058' : '#d03050'">
                <PlayCircleOutline v-if="isDetecting" />
                <PauseCircleOutline v-else />
              </n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small" :bordered="false" class="stats-card">
          <n-statistic label="今日异常" :value="todayAnomalies" tabular-nums>
            <template #prefix>
              <n-icon color="#f0a020"><WarningOutline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small" :bordered="false" class="stats-card">
          <n-statistic label="检测精度" :value="detectionAccuracy" suffix="%" tabular-nums>
            <template #prefix>
              <n-icon color="#2080f0"><CheckmarkCircleOutline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small" :bordered="false" class="stats-card">
          <n-statistic label="待处理" :value="processingCount" tabular-nums>
            <template #prefix>
              <n-icon color="#722ed1"><TimeOutline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 检测模式配置 -->
    <n-card title="检测模式" size="small" class="mb-4" :bordered="false">
      <template #header-extra>
        <n-tag :type="getModeTagType(configData.mode)" size="small">
          {{ getModeLabel(configData.mode) }}
        </n-tag>
      </template>
      <n-space vertical :size="16">
        <n-radio-group v-model:value="configData.mode" name="detectionMode" @update:value="handleModeChange">
          <n-space>
            <n-radio-button value="rule">
              <n-space align="center" :size="4">
                <n-icon><OptionsOutline /></n-icon>
                <span>规则模式</span>
              </n-space>
            </n-radio-button>
            <n-radio-button value="ai">
              <n-space align="center" :size="4">
                <n-icon><HardwareChipOutline /></n-icon>
                <span>AI模型模式</span>
              </n-space>
            </n-radio-button>
            <n-radio-button value="hybrid">
              <n-space align="center" :size="4">
                <n-icon><GitMergeOutline /></n-icon>
                <span>混合模式</span>
              </n-space>
            </n-radio-button>
          </n-space>
        </n-radio-group>
        <n-alert :type="getModeAlertType(configData.mode)" :show-icon="false">
          <span v-if="configData.mode === 'rule'">基于预设阈值进行判断，响应快速，可解释性强，适合已知异常模式的检测。</span>
          <span v-if="configData.mode === 'ai'">基于机器学习模型进行异常识别，可发现复杂模式异常，适合未知异常的探索。</span>
          <span v-if="configData.mode === 'hybrid'">同时使用规则和AI模型，取并集或交集作为最终结果，兼顾准确性和覆盖率。</span>
        </n-alert>
      </n-space>
    </n-card>

    <!-- AI模型配置 (仅在AI或混合模式下显示) -->
    <n-card 
      v-if="configData.mode !== 'rule'" 
      title="AI模型配置" 
      size="small" 
      class="mb-4"
      :bordered="false"
    >
      <n-grid :cols="2" :x-gap="24">
        <n-grid-item>
          <n-form-item label="选择模型">
            <ModelSelector
              v-model:modelValue="configData.modelId"
              model-type="anomaly_detection"
              :model-status="modelStatusFilter"
              :show-stats="false"
              :show-selected-info="true"
              @change="handleModelChange"
            />
          </n-form-item>
          <!-- 混合策略配置 -->
          <n-form-item v-if="configData.mode === 'hybrid'" label="决策逻辑">
            <n-radio-group v-model:value="configData.hybridLogic">
              <n-space vertical>
                <n-radio value="union">
                  <n-space align="center" :size="4">
                    <n-icon color="#f0a020"><GitMergeOutline /></n-icon>
                    <span>并集模式 (任一触发即报警，覆盖率高)</span>
                  </n-space>
                </n-radio>
                <n-radio value="intersection">
                  <n-space align="center" :size="4">
                    <n-icon color="#18a058"><CheckmarkCircleOutline /></n-icon>
                    <span>交集模式 (同时触发才报警，准确率高)</span>
                  </n-space>
                </n-radio>
              </n-space>
            </n-radio-group>
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="实时异常得分">
            <div class="anomaly-score-container">
              <n-progress
                type="dashboard"
                gap-position="bottom"
                :percentage="currentAnomalyScore"
                :color="getScoreColor(currentAnomalyScore)"
                :rail-color="getScoreRailColor(currentAnomalyScore)"
                :stroke-width="12"
              >
                <template #default>
                  <div class="score-content">
                    <div class="score-label">异常得分</div>
                    <div class="score-value" :style="{ color: getScoreColor(currentAnomalyScore) }">
                      {{ currentAnomalyScore }}
                    </div>
                    <div class="score-status">{{ getScoreStatus(currentAnomalyScore) }}</div>
                  </div>
                </template>
              </n-progress>
            </div>
          </n-form-item>
        </n-grid-item>
      </n-grid>
    </n-card>

    <!-- 实时监控图表 -->
    <n-grid :cols="2" :x-gap="16" class="mb-4">
      <n-grid-item>
        <n-card title="实时异常趋势" size="small" :bordered="false">
          <template #header-extra>
            <n-tag type="info" size="small" round>近1小时</n-tag>
          </template>
          <div ref="trendChartRef" style="height: 200px"></div>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card title="异常类型分布" size="small" :bordered="false">
          <div ref="pieChartRef" style="height: 200px"></div>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 规则阈值配置 (仅在规则或混合模式下显示) -->
    <n-card 
      v-if="configData.mode !== 'ai' && Object.keys(dynamicThresholds).length > 0" 
      title="阈值配置" 
      size="small" 
      class="mb-4"
      :bordered="false"
    >
      <template #header-extra>
        <n-space>
          <n-button size="small" quaternary @click="resetThresholds">
            <template #icon><n-icon><RefreshOutline /></n-icon></template>
            重置阈值
          </n-button>
        </n-space>
      </template>
      <n-grid :cols="2" :x-gap="16" :y-gap="16">
        <n-grid-item v-for="(item, key) in dynamicThresholds" :key="key">
          <div class="threshold-card" :class="{ disabled: !item.enabled, warning: isThresholdWarning(key), error: isThresholdError(key) }">
            <div class="threshold-header">
              <n-space align="center" justify="space-between" style="width: 100%">
                <n-space align="center" :size="8">
                  <n-icon :size="18" :color="getThresholdIconColor(key)">
                    <ThermometerOutline v-if="key.includes('temp')" />
                    <SpeedometerOutline v-else-if="key.includes('pressure')" />
                    <PulseOutline v-else-if="key.includes('vibration')" />
                    <FlashOutline v-else />
                  </n-icon>
                  <span class="threshold-title">{{ item.label || getParameterName(key) }}</span>
                </n-space>
                <n-switch
                  :value="item.enabled"
                  size="small"
                  @update:value="handleEnabledChange(key, $event)"
                />
              </n-space>
            </div>
            
            <div class="threshold-body" :class="{ disabled: !item.enabled }">
              <div class="threshold-inputs">
                <div class="input-group">
                  <span class="input-label">最小值</span>
                  <n-input-number
                    :value="item.min"
                    :disabled="!item.enabled"
                    :precision="item.precision || getDecimalPlaces(key)"
                    :step="item.step || getStep(key)"
                    :min="item.minLimit || getMinLimit(key)"
                    :max="item.max"
                    size="small"
                    style="width: 100%"
                    @update:value="(val) => handleThresholdUpdate(key, 'min', val)"
                  />
                </div>
                <div class="input-group">
                  <span class="input-label">最大值</span>
                  <n-input-number
                    :value="item.max"
                    :disabled="!item.enabled"
                    :precision="item.precision || getDecimalPlaces(key)"
                    :step="item.step || getStep(key)"
                    :min="item.min"
                    :max="item.maxLimit || getMaxLimit(key)"
                    size="small"
                    style="width: 100%"
                    @update:value="(val) => handleThresholdUpdate(key, 'max', val)"
                  />
                </div>
              </div>
              
              <div class="threshold-visual">
                <div class="current-value-display">
                  <span class="cv-label">当前值:</span>
                  <n-tag :type="getCurrentValueStatus(key)" size="small" round>
                    {{ getCurrentValue(key) }} {{ item.unit || getUnit(key) }}
                  </n-tag>
                </div>
                <n-progress
                  type="line"
                  :percentage="getProgressPercentage(key)"
                  :status="getProgressStatus(key)"
                  :show-indicator="false"
                  :height="8"
                  :border-radius="4"
                />
                <div class="range-labels">
                  <span>{{ item.min }} {{ item.unit || getUnit(key) }}</span>
                  <span>{{ item.max }} {{ item.unit || getUnit(key) }}</span>
                </div>
              </div>
            </div>
          </div>
        </n-grid-item>
      </n-grid>
    </n-card>

    <!-- 无设备选择提示（仅在新增模式且未选择设备时显示） -->
    <n-card v-if="props.mode === 'add' && !selectedDeviceId" size="small" class="mb-4" :bordered="false">
      <n-empty description="请先选择需要监控的设备">
        <template #icon>
          <n-icon size="48" color="#d03050">
            <ServerOutline />
          </n-icon>
        </template>
        <template #extra>
          <n-text depth="3">选择设备后将自动加载该设备的监控参数和阈值配置</n-text>
        </template>
      </n-empty>
    </n-card>

    <!-- 异常记录列表 -->
    <n-card 
      v-if="hasSelectedDevice" 
      title="最近异常记录" 
      size="small" 
      class="mb-4"
      :bordered="false"
    >
      <template #header-extra>
        <n-space>
          <n-select
            v-model:value="filterStatus"
            :options="statusOptions"
            placeholder="筛选状态"
            style="width: 100px"
            size="small"
            clearable
          />
          <n-button size="small" @click="refreshAnomalyList">
            <template #icon><n-icon><RefreshOutline /></n-icon></template>
            刷新
          </n-button>
        </n-space>
      </template>
      <AnomalyList
        v-if="anomalyList.length > 0"
        :data="filteredAnomalyList"
        :loading="listLoading"
        @view-detail="viewAnomalyDetail"
        @handle-anomaly="handleAnomaly"
        @ignore-anomaly="ignoreAnomaly"
      />
      <n-empty v-else description="暂无异常记录" size="small" />
    </n-card>

    <!-- 操作按钮 -->
    <div class="actions-bar">
      <n-space justify="space-between" style="width: 100%">
        <n-space>
          <n-button @click="exportConfig">
            <template #icon><n-icon><CloudDownloadOutline /></n-icon></template>
            导出配置
          </n-button>
          <n-button @click="resetConfig">
            <template #icon><n-icon><RefreshOutline /></n-icon></template>
            重置默认
          </n-button>
        </n-space>
        <n-button type="primary" @click="saveConfig">
          <template #icon><n-icon><SaveOutline /></n-icon></template>
          保存配置
        </n-button>
      </n-space>
    </div>

    <!-- 异常详情抽屉 -->
    <n-drawer v-model:show="showDetailDrawer" :width="500" placement="right">
      <n-drawer-content title="异常详情">
        <div v-if="selectedAnomaly">
          <n-descriptions :column="1" bordered label-placement="left">
            <n-descriptions-item label="异常ID">
              <n-text code>{{ selectedAnomaly.id }}</n-text>
            </n-descriptions-item>
            <n-descriptions-item label="设备名称">{{ selectedAnomaly.deviceName }}</n-descriptions-item>
            <n-descriptions-item label="异常类型">
              <n-tag :type="getAnomalyTypeColor(selectedAnomaly.type)">
                {{ selectedAnomaly.typeName }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="严重程度">
              <n-tag :type="getSeverityColor(selectedAnomaly.severity)">
                {{ selectedAnomaly.severityName }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="检测时间">{{ selectedAnomaly.detectedAt }}</n-descriptions-item>
            <n-descriptions-item label="异常描述">{{ selectedAnomaly.description }}</n-descriptions-item>
            <n-descriptions-item label="AI置信度">
              <n-progress
                type="line"
                :percentage="selectedAnomaly.confidence"
                :height="16"
                :border-radius="8"
                indicator-placement="inside"
              />
            </n-descriptions-item>
          </n-descriptions>

          <n-divider />
          
          <n-alert type="info" title="处理建议">
            {{ selectedAnomaly.suggestion }}
          </n-alert>

          <div class="drawer-actions">
            <n-space>
              <n-button type="primary" @click="handleSelectedAnomaly">标记已处理</n-button>
              <n-button @click="ignoreSelectedAnomaly">忽略异常</n-button>
            </n-space>
          </div>
        </div>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>


<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useMessage } from 'naive-ui'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import {
  SaveOutline,
  RefreshOutline,
  CloudDownloadOutline,
  OptionsOutline,
  HardwareChipOutline,
  GitMergeOutline,
  PlayOutline,
  StopOutline,
  PlayCircleOutline,
  PauseCircleOutline,
  WarningOutline,
  CheckmarkCircleOutline,
  TimeOutline,
  ThermometerOutline,
  SpeedometerOutline,
  PulseOutline,
  FlashOutline,
  ServerOutline
} from '@vicons/ionicons5'
import ModelSelector from '@/components/ai-monitor/common/ModelSelector.vue'
import DeviceSelector from '@/components/ai-monitor/common/DeviceSelector.vue'
import AnomalyList from './AnomalyList.vue'
import { deviceFieldApi } from '@/api/device-field'
import { anomalyDetectionApi } from '@/api/v2/ai-module'

// ==================== 类型定义 ====================
interface ThresholdItem {
  min: number
  max: number
  enabled: boolean
  label?: string
  unit?: string
  precision?: number
  step?: number
  minLimit?: number
  maxLimit?: number
  defaultMin?: number
  defaultMax?: number
}

interface AnomalyRecord {
  id: string | number
  deviceId: string
  deviceName: string
  type: string
  typeName: string
  severity: string
  severityName: string
  status: string
  statusName: string
  detectedAt: string
  description: string
  confidence: number
  suggestion: string
}

// ==================== Props & Emits ====================
const modelStatusFilter = ['deployed']

const props = defineProps({
  config: {
    type: Object,
    required: true,
  },
  // 传入设备编码时，直接加载该设备配置（编辑模式）
  deviceCode: {
    type: String,
    default: null
  },
  // 模式：add=新增设备，edit=编辑已有设备配置
  mode: {
    type: String as () => 'add' | 'edit',
    default: 'add'
  }
})

const emit = defineEmits(['update', 'reset', 'save'])

const message = useMessage()

// ==================== 默认配置 ====================
const defaultConfig = {
  mode: 'rule',
  modelId: null,
  hybridLogic: 'union',
  thresholds: {} as Record<string, ThresholdItem>
}

// ==================== 响应式数据 ====================
const configData = ref({
  ...defaultConfig,
  ...props.config,
  thresholds: props.config.thresholds || props.config
})

if (!configData.value.mode) configData.value.mode = 'rule'

const selectedDeviceId = ref<number | null>(null)
const currentDeviceCode = ref<string | null>(null)
const currentDeviceName = ref<string | null>(null) // 设备名称（编辑模式显示用）
const isSimulationEnabled = ref(false)
const isDetecting = ref(true)  // 默认启用检测
const listLoading = ref(false)
const showDetailDrawer = ref(false)
const selectedAnomaly = ref<AnomalyRecord | null>(null)
const filterStatus = ref<string | null>(null)

// 统计数据
const todayAnomalies = ref(0)
const detectionAccuracy = ref(94.8)
const processingCount = ref(0)
const currentAnomalyScore = ref(15)

// 设备配置和实时数据
const deviceConfig = ref<Record<string, any>>({})
const currentValues = ref<Record<string, number>>({})

// 异常记录
const anomalyList = ref<AnomalyRecord[]>([])

// 图表引用
const trendChartRef = ref<HTMLElement | null>(null)
const pieChartRef = ref<HTMLElement | null>(null)
let trendChart: ECharts | null = null
let pieChart: ECharts | null = null

// 定时器
let pollingTimer: ReturnType<typeof setInterval> | null = null
let scoreTimer: ReturnType<typeof setInterval> | null = null
let autoRefreshTimer: ReturnType<typeof setInterval> | null = null

// 筛选选项
const statusOptions = [
  { label: '待处理', value: 'pending' },
  { label: '处理中', value: 'processing' },
  { label: '已解决', value: 'resolved' },
  { label: '已忽略', value: 'ignored' },
]

// ==================== 计算属性 ====================
const detectionStatusText = computed(() => isDetecting.value ? '运行中' : '已停止')

// 是否已选择设备（编辑模式使用 currentDeviceCode，新增模式使用 selectedDeviceId）
const hasSelectedDevice = computed(() => {
  return props.mode === 'edit' ? !!currentDeviceCode.value : !!selectedDeviceId.value
})

const dynamicThresholds = computed(() => {
  if (!hasSelectedDevice.value || Object.keys(deviceConfig.value).length === 0) {
    return {}
  }
  
  const result: Record<string, any> = {}
  
  for (const [key, fieldConfig] of Object.entries(deviceConfig.value)) {
    const localConfig = configData.value.thresholds[key] || {}
    const fc = fieldConfig as any
    
    result[key] = {
      ...fc,
      min: localConfig.min !== undefined ? localConfig.min : fc.defaultMin,
      max: localConfig.max !== undefined ? localConfig.max : fc.defaultMax,
      enabled: localConfig.enabled !== undefined ? localConfig.enabled : true,
    }
  }
  
  return result
})

const filteredAnomalyList = computed(() => {
  if (!filterStatus.value) return anomalyList.value
  return anomalyList.value.filter(item => item.status === filterStatus.value)
})

// ==================== 方法 ====================

// 模式相关
const getModeTagType = (mode: string) => {
  const map: Record<string, string> = { rule: 'info', ai: 'success', hybrid: 'warning' }
  return map[mode] || 'default'
}

const getModeLabel = (mode: string) => {
  const map: Record<string, string> = { rule: '规则模式', ai: 'AI模式', hybrid: '混合模式' }
  return map[mode] || mode
}

const getModeAlertType = (mode: string) => {
  const map: Record<string, 'info' | 'success' | 'warning'> = { rule: 'info', ai: 'success', hybrid: 'warning' }
  return map[mode] || 'info'
}

const handleModeChange = () => {
  emit('update', configData.value)
}

const handleModelChange = (val: number, option: any) => {
  if (option && option.model) {
    message.success(`已选择模型: ${option.model.name}`)
    configData.value.modelId = val
    emit('update', configData.value)
  }
}

// 异常得分相关
const getScoreColor = (score: number) => {
  if (score < 30) return '#18a058'
  if (score < 70) return '#f0a020'
  return '#d03050'
}

const getScoreRailColor = (score: number) => {
  if (score < 30) return 'rgba(24, 160, 88, 0.1)'
  if (score < 70) return 'rgba(240, 160, 32, 0.1)'
  return 'rgba(208, 48, 80, 0.1)'
}

const getScoreStatus = (score: number) => {
  if (score < 30) return '正常'
  if (score < 70) return '警告'
  return '异常'
}

// 阈值相关
const getParameterName = (key: string) => {
  const nameMap: Record<string, string> = {
    temperature: '温度', pressure: '压力', vibration: '振动', current: '电流',
  }
  return nameMap[key] || key
}

const getUnit = (key: string) => {
  const unitMap: Record<string, string> = {
    temperature: '°C', pressure: 'MPa', vibration: 'mm/s', current: 'A',
  }
  return unitMap[key] || ''
}

const getDecimalPlaces = (key: string) => {
  const decimalMap: Record<string, number> = {
    temperature: 1, pressure: 1, vibration: 1, current: 1,
  }
  return decimalMap[key] || 0
}

const getStep = (key: string) => {
  const stepMap: Record<string, number> = {
    temperature: 1, pressure: 0.1, vibration: 0.5, current: 1,
  }
  return stepMap[key] || 1
}

const getMinLimit = (key: string) => {
  const limitMap: Record<string, number> = {
    temperature: -50, pressure: 0, vibration: 0, current: 0,
  }
  return limitMap[key] || 0
}

const getMaxLimit = (key: string) => {
  const limitMap: Record<string, number> = {
    temperature: 200, pressure: 10, vibration: 50, current: 100,
  }
  return limitMap[key] || 100
}

const getCurrentValue = (key: string) => {
  return currentValues.value[key] || 0
}

const getCurrentValueStatus = (key: string) => {
  const current = getCurrentValue(key)
  const config = configData.value.thresholds[key]
  if (!config || !config.enabled) return 'default'
  if (current < config.min || current > config.max) return 'error'
  if (current <= config.min * 1.1 || current >= config.max * 0.9) return 'warning'
  return 'success'
}

const getProgressPercentage = (key: string) => {
  const current = getCurrentValue(key)
  const config = configData.value.thresholds[key]
  if (!config || !config.enabled) return 0
  const range = config.max - config.min
  const position = current - config.min
  return Math.max(0, Math.min(100, (position / range) * 100))
}

const getProgressStatus = (key: string) => {
  const status = getCurrentValueStatus(key)
  const statusMap: Record<string, 'error' | 'warning' | 'success' | 'default'> = {
    error: 'error', warning: 'warning', success: 'success', default: 'default',
  }
  return statusMap[status] || 'default'
}

const getThresholdIconColor = (key: string) => {
  const status = getCurrentValueStatus(key)
  if (status === 'error') return '#d03050'
  if (status === 'warning') return '#f0a020'
  return '#18a058'
}

const isThresholdWarning = (key: string) => getCurrentValueStatus(key) === 'warning'
const isThresholdError = (key: string) => getCurrentValueStatus(key) === 'error'

const handleEnabledChange = (key: string, enabled: boolean) => {
  if (!configData.value.thresholds[key]) {
    configData.value.thresholds[key] = {
      min: deviceConfig.value[key]?.defaultMin || 0,
      max: deviceConfig.value[key]?.defaultMax || 100,
      enabled: true
    }
  }
  configData.value.thresholds[key].enabled = enabled
  emit('update', configData.value)
}

const handleThresholdUpdate = (key: string, field: 'min' | 'max', value: number | null) => {
  if (value === null) return
  if (!configData.value.thresholds[key]) {
    configData.value.thresholds[key] = {
      min: deviceConfig.value[key]?.defaultMin || 0,
      max: deviceConfig.value[key]?.defaultMax || 100,
      enabled: true
    }
  }
  configData.value.thresholds[key][field] = value
  emit('update', configData.value)
}

const resetThresholds = () => {
  for (const key in deviceConfig.value) {
    const fc = deviceConfig.value[key]
    configData.value.thresholds[key] = {
      min: fc.defaultMin,
      max: fc.defaultMax,
      enabled: true
    }
  }
  message.info('阈值已重置为默认值')
  emit('update', configData.value)
}

// 设备相关
const handleDeviceChange = (deviceId: number, option: any) => {
  selectedDeviceId.value = deviceId
  if (deviceId && option && option.device) {
    const deviceCode = option.device.device_code || option.device.code
    currentDeviceCode.value = deviceCode
    if (deviceCode) {
      fetchDeviceConfigAndData(deviceCode)
      startPolling(deviceId, deviceCode)
      refreshAnomalyList()
    }
  } else {
    stopPolling()
    resetValues()
    deviceConfig.value = {}
    currentDeviceCode.value = null
    anomalyList.value = []
  }
}

const fetchDeviceConfigAndData = async (deviceCode: string) => {
  try {
    const res = await deviceFieldApi.getRealtimeWithConfig(deviceCode)
    if (res.data) {
      // 设置设备名称（编辑模式显示用）
      currentDeviceName.value = res.data.device_name || deviceCode
      
      const fields = res.data.monitoring_fields || []
      const newConfig: Record<string, any> = {}
      const newValues: Record<string, number> = {}
      
      fields.forEach((field: any) => {
        const key = field.field_code
        let minLimit = -9999, maxLimit = 9999, defaultMin = 0, defaultMax = 100
        
        if (field.data_range) {
          if (field.data_range.min !== undefined) {
            minLimit = field.data_range.min
            defaultMin = field.data_range.min
          }
          if (field.data_range.max !== undefined) {
            maxLimit = field.data_range.max
            defaultMax = field.data_range.max
          }
        }
        
        newConfig[key] = {
          label: field.field_name,
          unit: field.unit || '',
          precision: field.field_type === 'float' ? 2 : 0,
          step: field.field_type === 'float' ? 0.1 : 1,
          minLimit, maxLimit, defaultMin, defaultMax,
        }
        
        const realtimeData = res.data.realtime_data || {}
        newValues[key] = realtimeData[key] !== undefined && realtimeData[key] !== null ? realtimeData[key] : 0
      })
      
      deviceConfig.value = newConfig
      currentValues.value = newValues
      
      // 获取用户保存的配置
      try {
        const configRes = await anomalyDetectionApi.getConfig(deviceCode)
        if (configRes.data && configRes.data.config_data && Object.keys(configRes.data.config_data).length > 0) {
          const savedConfig = configRes.data.config_data
          if (savedConfig.mode) configData.value.mode = savedConfig.mode
          if (savedConfig.modelId) configData.value.modelId = savedConfig.modelId
          if (savedConfig.hybridLogic) configData.value.hybridLogic = savedConfig.hybridLogic
          
          // 加载检测启用状态
          isDetecting.value = configRes.data.is_active !== false
          
          if (savedConfig.thresholds) {
            for (const key in savedConfig.thresholds) {
              configData.value.thresholds[key] = { ...configData.value.thresholds[key], ...savedConfig.thresholds[key] }
            }
          }
          // 不在加载配置时触发 update 事件，只在用户主动保存时触发
        } else {
          for (const key in newConfig) {
            if (!configData.value.thresholds[key]) {
              configData.value.thresholds[key] = {
                min: newConfig[key].defaultMin,
                max: newConfig[key].defaultMax,
                enabled: true
              }
            }
          }
        }
      } catch (error) {
        for (const key in newConfig) {
          if (!configData.value.thresholds[key]) {
            configData.value.thresholds[key] = {
              min: newConfig[key].defaultMin,
              max: newConfig[key].defaultMax,
              enabled: true
            }
          }
        }
      }
    }
  } catch (error) {
    console.error('获取设备配置及数据失败:', error)
    message.error('获取设备配置失败')
  }
}

const startPolling = (deviceId: number, deviceCode: string) => {
  stopPolling()
  pollingTimer = setInterval(() => {
    fetchDeviceRealtimeDataOnly(deviceCode)
  }, 5000)
}

const fetchDeviceRealtimeDataOnly = async (deviceCode: string) => {
  try {
    if (isSimulationEnabled.value) {
      const newValues: Record<string, number> = {}
      for (const key in deviceConfig.value) {
        const config = deviceConfig.value[key]
        const min = config.minLimit !== undefined ? config.minLimit : 0
        const max = config.maxLimit !== undefined ? config.maxLimit : 100
        const range = max - min
        let value = min + Math.random() * range
        const precision = config.precision !== undefined ? config.precision : 2
        value = Number(value.toFixed(precision))
        newValues[key] = value
      }
      currentValues.value = newValues
      return
    }

    const res = await deviceFieldApi.getRealtimeWithConfig(deviceCode)
    if (res.data && res.data.realtime_data) {
      const realtimeData = res.data.realtime_data
      for (const key in currentValues.value) {
        if (realtimeData[key] !== undefined && realtimeData[key] !== null) {
          currentValues.value[key] = realtimeData[key]
        }
      }
    }
  } catch (error) {
    console.error('轮询设备数据失败:', error)
  }
}

const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

const resetValues = () => {
  currentValues.value = {}
}

// 检测控制
const toggleDetection = async () => {
  if (isDetecting.value) {
    await stopDetection()
  } else {
    await startDetection()
  }
}

const startDetection = async () => {
  if (!selectedDeviceId.value) {
    message.warning('请先选择需要监控的设备')
    return
  }
  isDetecting.value = true
  message.success('异常检测已启动')
  await refreshAnomalyList()
  startAutoRefresh()
}

const stopDetection = async () => {
  isDetecting.value = false
  message.info('异常检测已停止')
  stopAutoRefresh()
}

const startAutoRefresh = () => {
  stopAutoRefresh()
  autoRefreshTimer = setInterval(async () => {
    if (isDetecting.value && currentDeviceCode.value) {
      await runRealtimeDetection()
      await refreshAnomalyList()
    }
  }, 10000)
}

const stopAutoRefresh = () => {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
}

const runRealtimeDetection = async () => {
  if (!currentDeviceCode.value) return
  
  try {
    const dataSeries: number[] = []
    for (const key in currentValues.value) {
      dataSeries.push(currentValues.value[key])
    }
    
    if (dataSeries.length > 0) {
      await anomalyDetectionApi.detect({
        device_code: currentDeviceCode.value,
        data: dataSeries,
        method: 'combined',
        threshold: 3.0,
        save_to_db: true
      })
    }
  } catch (error) {
    console.warn('实时检测执行失败:', error)
  }
}

// 异常记录相关
const refreshAnomalyList = async () => {
  if (!currentDeviceCode.value) return
  
  try {
    listLoading.value = true
    const response = await anomalyDetectionApi.getRecords({
      page: 1,
      page_size: 20,
      device_code: currentDeviceCode.value,
    } as any)

    if (response.data && response.data.records) {
      anomalyList.value = response.data.records.map((record: any) => ({
        id: record.id,
        deviceId: record.device_code,
        deviceName: record.device_name || record.device_code,
        type: mapAnomalyType(record.anomaly_type),
        typeName: record.anomaly_type,
        severity: mapSeverityLevel(record.severity_level),
        severityName: getSeverityName(record.severity_level),
        status: record.is_handled ? 'resolved' : 'pending',
        statusName: record.is_handled ? '已解决' : '待处理',
        detectedAt: formatDateTime(record.detection_time),
        description: record.description || '检测到异常数据',
        confidence: Math.round(record.confidence_score * 100 * 10) / 10,
        suggestion: generateSuggestion(record),
      }))

      todayAnomalies.value = response.data.total || anomalyList.value.length
      processingCount.value = anomalyList.value.filter(r => r.status === 'pending').length
      
      updateCharts()
    }
  } catch (error) {
    console.error('刷新异常列表失败:', error)
  } finally {
    listLoading.value = false
  }
}

const mapAnomalyType = (type: string): string => {
  const typeMap: Record<string, string> = {
    'temperature_high': 'temperature', 'temperature_low': 'temperature',
    'pressure_high': 'pressure', 'pressure_low': 'pressure',
    'vibration_high': 'vibration',
    'current_high': 'current', 'current_low': 'current',
  }
  return typeMap[type] || 'other'
}

const mapSeverityLevel = (level: number): string => {
  if (level >= 4) return 'high'
  if (level >= 2) return 'medium'
  return 'low'
}

const getSeverityName = (level: number): string => {
  if (level >= 4) return '高'
  if (level >= 2) return '中'
  return '低'
}

const formatDateTime = (dateStr: string): string => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    }).replace(/\//g, '-')
  } catch {
    return dateStr
  }
}

const generateSuggestion = (record: any): string => {
  const suggestions: Record<string, string> = {
    'temperature_high': '立即检查冷却系统，确认冷却液是否充足，检查散热风扇是否正常工作。',
    'temperature_low': '检查加热系统，确认环境温度是否适宜，检查温度传感器是否正常。',
    'pressure_high': '检查压力调节阀，确认管道是否堵塞，适当降低工作压力。',
    'pressure_low': '检查气压调节阀，确认气源是否充足，检查管道是否泄漏。',
    'vibration_high': '检查设备固定螺栓是否松动，确认设备基础是否稳固，检查轴承是否磨损。',
    'current_high': '检查负载是否过大，确认电路是否正常，检查电机是否过载。',
    'current_low': '检查电源是否稳定，确认接线是否松动，检查设备是否正常工作。',
  }
  return suggestions[record.anomaly_type] || '请联系技术人员进行详细检查，确保设备安全运行。'
}

const viewAnomalyDetail = (anomaly: AnomalyRecord) => {
  selectedAnomaly.value = anomaly
  showDetailDrawer.value = true
}

const handleAnomaly = async (anomaly: AnomalyRecord) => {
  try {
    await anomalyDetectionApi.handleRecord(anomaly.id as number, '已处理')
    const index = anomalyList.value.findIndex(item => item.id === anomaly.id)
    if (index !== -1) {
      anomalyList.value[index].status = 'resolved'
      anomalyList.value[index].statusName = '已解决'
    }
    processingCount.value = Math.max(0, processingCount.value - 1)
    message.success(`异常 ${anomaly.id} 已标记为已解决`)
  } catch (error) {
    console.error('处理异常失败:', error)
    message.error('处理异常失败')
  }
}

const ignoreAnomaly = async (anomaly: AnomalyRecord) => {
  try {
    await anomalyDetectionApi.handleRecord(anomaly.id as number, '已忽略')
    const index = anomalyList.value.findIndex(item => item.id === anomaly.id)
    if (index !== -1) {
      anomalyList.value[index].status = 'ignored'
      anomalyList.value[index].statusName = '已忽略'
    }
    processingCount.value = Math.max(0, processingCount.value - 1)
    message.info(`异常 ${anomaly.id} 已忽略`)
  } catch (error) {
    console.error('忽略异常失败:', error)
    message.error('忽略异常失败')
  }
}

const handleSelectedAnomaly = () => {
  if (selectedAnomaly.value) {
    handleAnomaly(selectedAnomaly.value)
    showDetailDrawer.value = false
  }
}

const ignoreSelectedAnomaly = () => {
  if (selectedAnomaly.value) {
    ignoreAnomaly(selectedAnomaly.value)
    showDetailDrawer.value = false
  }
}

const getAnomalyTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    temperature: 'error', pressure: 'warning', vibration: 'info', current: 'success',
  }
  return colorMap[type] || 'default'
}

const getSeverityColor = (severity: string) => {
  const colorMap: Record<string, string> = {
    high: 'error', medium: 'warning', low: 'info',
  }
  return colorMap[severity] || 'default'
}

// 图表相关
const initCharts = () => {
  nextTick(() => {
    if (trendChartRef.value) {
      trendChart = echarts.init(trendChartRef.value)
      updateTrendChart()
    }
    if (pieChartRef.value) {
      pieChart = echarts.init(pieChartRef.value)
      updatePieChart()
    }
  })
}

const updateCharts = () => {
  updateTrendChart()
  updatePieChart()
}

const updateTrendChart = () => {
  if (!trendChart) return
  
  const timeMap = new Map<string, number>()
  anomalyList.value.forEach(anomaly => {
    if (anomaly.detectedAt) {
      const hour = anomaly.detectedAt.split(' ')[1]?.substring(0, 5) || '00:00'
      timeMap.set(hour, (timeMap.get(hour) || 0) + 1)
    }
  })
  
  const sortedTrend = Array.from(timeMap.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .slice(-6)
  
  const times = sortedTrend.map(([time]) => time)
  const values = sortedTrend.map(([, value]) => value)
  
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { top: 20, right: 20, bottom: 30, left: 40 },
    xAxis: { type: 'category', data: times, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed' } } },
    series: [{
      name: '异常数量',
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      data: values,
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(208, 48, 80, 0.4)' },
          { offset: 1, color: 'rgba(208, 48, 80, 0.05)' }
        ])
      },
      itemStyle: { color: '#d03050' },
      lineStyle: { width: 2 }
    }]
  })
}

const updatePieChart = () => {
  if (!pieChart) return
  
  const typeMap = new Map<string, number>()
  anomalyList.value.forEach(anomaly => {
    typeMap.set(anomaly.typeName, (typeMap.get(anomaly.typeName) || 0) + 1)
  })
  
  const colors = ['#ff6b6b', '#ffa726', '#42a5f5', '#ab47bc', '#66bb6a']
  const data = Array.from(typeMap.entries()).map(([name, value], index) => ({
    name, value, itemStyle: { color: colors[index % colors.length] }
  }))
  
  pieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', left: 'left', top: 'center', textStyle: { fontSize: 11 } },
    series: [{
      name: '异常类型',
      type: 'pie',
      radius: ['35%', '65%'],
      center: ['60%', '50%'],
      data: data.length > 0 ? data : [{ name: '暂无数据', value: 1, itemStyle: { color: '#e0e0e0' } }],
      label: { show: false },
      emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
    }]
  })
}

const handleResize = () => {
  if (trendChart) trendChart.resize()
  if (pieChart) pieChart.resize()
}

// 配置操作
const saveConfig = async () => {
  try {
    if (currentDeviceCode.value) {
      await anomalyDetectionApi.updateConfig(currentDeviceCode.value, { 
        config_data: configData.value,
        is_active: isDetecting.value 
      })
      message.success('配置已保存，新配置将在下次检测时生效')
      // 保存成功后触发 save 事件（用于关闭弹窗和刷新列表）
      emit('save', configData.value)
    } else {
      message.warning('请先选择设备')
      return
    }
  } catch (error) {
    console.error('保存配置失败:', error)
    message.error('保存配置失败')
  }
}

const resetConfig = () => {
  configData.value = JSON.parse(JSON.stringify(defaultConfig))
  emit('reset')
  message.info('配置已重置')
}

const exportConfig = () => {
  const configJson = JSON.stringify(configData.value, null, 2)
  const blob = new Blob([configJson], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `detection-config-${new Date().toISOString().split('T')[0]}.json`
  a.click()
  URL.revokeObjectURL(url)
  message.success('配置已导出')
}

// 监听配置变化
watch(
  () => props.config,
  (newConfig) => {
    if (newConfig.thresholds) {
      configData.value = { ...configData.value, ...newConfig }
    } else {
      configData.value.thresholds = { ...newConfig }
    }
  },
  { deep: true }
)

// 监听设备编码变化（编辑模式下自动加载设备配置）
watch(
  () => props.deviceCode,
  async (newDeviceCode) => {
    if (props.mode === 'edit' && newDeviceCode) {
      // 重置状态
      resetComponentState()
      currentDeviceCode.value = newDeviceCode
      await fetchDeviceConfigAndData(newDeviceCode)
      startPolling(0, newDeviceCode)
      refreshAnomalyList()
    }
  },
  { immediate: true }
)

// 重置组件状态
function resetComponentState() {
  deviceConfig.value = {}
  currentValues.value = {}
  configData.value = {
    ...defaultConfig,
    thresholds: {}
  }
  anomalyList.value = []
  todayAnomalies.value = 0
  processingCount.value = 0
  currentAnomalyScore.value = 15
}

// 生命周期
onMounted(async () => {
  initCharts()
  window.addEventListener('resize', handleResize)
  
  scoreTimer = setInterval(() => {
    if (isSimulationEnabled.value) {
      Object.keys(currentValues.value).forEach(key => {
        const config = configData.value.thresholds[key]
        if (config && config.enabled) {
          const range = config.max - config.min
          const variation = range * 0.1 * (Math.random() - 0.5)
          currentValues.value[key] = Math.max(
            config.min * 0.8,
            Math.min(config.max * 1.2, currentValues.value[key] + variation)
          )
        }
      })
    }
    
    if (configData.value.mode !== 'rule') {
      const change = Math.random() * 10 - 5
      currentAnomalyScore.value = Math.max(0, Math.min(100, Math.floor(currentAnomalyScore.value + change)))
    }
  }, 2000)
})

onUnmounted(() => {
  stopPolling()
  stopAutoRefresh()
  window.removeEventListener('resize', handleResize)
  if (scoreTimer) clearInterval(scoreTimer)
  if (trendChart) trendChart.dispose()
  if (pieChart) pieChart.dispose()
})
</script>


<style scoped>
.detection-config {
  width: 100%;
  padding: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
}

.config-header {
  margin-bottom: 20px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.device-info-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mb-4 {
  margin-bottom: 16px;
}

.stats-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}

.stats-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

:deep(.n-card) {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  background: #fff;
}

:deep(.n-card-header) {
  padding: 16px 20px 12px;
}

:deep(.n-card__content) {
  padding: 16px 20px;
}

.anomaly-score-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px;
}

.score-content {
  text-align: center;
}

.score-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.score-value {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
}

.score-status {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.threshold-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #e8e8e8;
  transition: all 0.3s ease;
}

.threshold-card:hover {
  border-color: #18a058;
  box-shadow: 0 4px 12px rgba(24, 160, 88, 0.1);
}

.threshold-card.warning {
  border-color: #f0a020;
  background: linear-gradient(135deg, #fff 0%, #fffbf0 100%);
}

.threshold-card.error {
  border-color: #d03050;
  background: linear-gradient(135deg, #fff 0%, #fff5f5 100%);
}

.threshold-card.disabled {
  opacity: 0.6;
  background: #fafafa;
}

.threshold-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.threshold-title {
  font-weight: 600;
  font-size: 14px;
  color: #333;
}

.threshold-body {
  transition: opacity 0.3s ease;
}

.threshold-body.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.threshold-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.input-label {
  font-size: 12px;
  color: #666;
}

.threshold-visual {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 12px;
}

.current-value-display {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.cv-label {
  font-size: 12px;
  color: #666;
}

.range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: #999;
  margin-top: 4px;
}

.actions-bar {
  margin-top: 24px;
  padding: 16px 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.drawer-actions {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

:deep(.n-statistic .n-statistic-value) {
  font-size: 24px;
  font-weight: 600;
}

:deep(.n-statistic .n-statistic__label) {
  font-size: 12px;
  color: #666;
}

:deep(.n-radio-button__state-border) {
  border-radius: 8px;
}

:deep(.n-radio-group) {
  gap: 8px;
}

:deep(.n-form-item .n-form-item-label) {
  font-weight: 500;
}

:deep(.n-alert) {
  border-radius: 8px;
}

:deep(.n-progress.n-progress--line) {
  border-radius: 4px;
}

:deep(.n-empty) {
  padding: 40px 0;
}
</style>
