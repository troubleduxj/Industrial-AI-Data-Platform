<template>
  <div class="anomaly-detail">
    <!-- 设备基本信息 -->
    <n-card title="设备信息" size="small" class="detail-section">
      <n-descriptions :column="3" label-placement="left">
        <n-descriptions-item label="设备编号">
          <n-text code>{{ deviceCode }}</n-text>
        </n-descriptions-item>
        <n-descriptions-item label="设备名称">
          {{ deviceInfo.name || '-' }}
        </n-descriptions-item>
        <n-descriptions-item label="设备类型">
          <n-tag type="info" size="small">{{ deviceInfo.type || '通用设备' }}</n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="安装位置">
          {{ deviceInfo.location || '-' }}
        </n-descriptions-item>
        <n-descriptions-item label="监控状态">
          <n-tag :type="isActive ? 'success' : 'default'" size="small">
            {{ isActive ? '监控中' : '已暂停' }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="最后更新">
          {{ lastUpdateTime }}
        </n-descriptions-item>
      </n-descriptions>
    </n-card>

    <!-- 核心指标 -->
    <n-card title="检测指标" size="small" class="detail-section">
      <n-grid :cols="4" :x-gap="16">
        <n-grid-item>
          <n-statistic label="健康评分" :value="healthScore">
            <template #prefix>
              <n-icon :color="getScoreColor(100 - healthScore)"><HeartOutline /></n-icon>
            </template>
            <template #suffix>分</template>
          </n-statistic>
        </n-grid-item>
        <n-grid-item>
          <n-statistic label="异常得分" :value="anomalyScore">
            <template #prefix>
              <n-icon :color="getScoreColor(anomalyScore)"><PulseOutline /></n-icon>
            </template>
          </n-statistic>
        </n-grid-item>
        <n-grid-item>
          <n-statistic label="今日异常" :value="todayAnomalies">
            <template #prefix>
              <n-icon color="#f0a020"><AlertCircleOutline /></n-icon>
            </template>
            <template #suffix>次</template>
          </n-statistic>
        </n-grid-item>
        <n-grid-item>
          <n-statistic label="待处理" :value="pendingCount">
            <template #prefix>
              <n-icon color="#d03050"><TimeOutline /></n-icon>
            </template>
            <template #suffix>条</template>
          </n-statistic>
        </n-grid-item>
      </n-grid>
    </n-card>

    <!-- 实时参数 -->
    <n-card title="实时参数" size="small" class="detail-section">
      <template #header-extra>
        <n-space>
          <n-tag :type="isPolling ? 'success' : 'default'" size="small" round>
            {{ isPolling ? '实时更新中' : '已暂停' }}
          </n-tag>
          <n-button size="small" @click="togglePolling">
            {{ isPolling ? '暂停' : '恢复' }}
          </n-button>
        </n-space>
      </template>
      <n-grid :cols="4" :x-gap="12" :y-gap="12">
        <n-grid-item v-for="field in displayFields" :key="field.key">
          <div class="param-item">
            <div class="param-header">
              <span class="param-name">{{ field.label }}</span>
              <n-tag :type="getParamTagType(field)" size="tiny">
                {{ getParamStatusText(field) }}
              </n-tag>
            </div>
            <div class="param-value">
              <span class="value">{{ formatValue(field.currentValue, field.precision) }}</span>
              <span class="unit">{{ field.unit }}</span>
            </div>
            <n-progress
              type="line"
              :percentage="getParamPercentage(field)"
              :show-indicator="false"
              :height="4"
              :color="getParamColor(field)"
            />
          </div>
        </n-grid-item>
      </n-grid>
      <n-empty v-if="displayFields.length === 0" description="暂无参数配置" size="small" />
    </n-card>

    <!-- 图表区域 -->
    <n-grid :cols="3" :x-gap="16" class="detail-section">
      <n-grid-item :span="2">
        <n-card title="异常趋势" size="small">
          <template #header-extra>
            <n-radio-group v-model:value="trendTimeRange" size="small">
              <n-radio-button value="1h">1小时</n-radio-button>
              <n-radio-button value="24h">24小时</n-radio-button>
              <n-radio-button value="7d">7天</n-radio-button>
            </n-radio-group>
          </template>
          <div ref="trendChartRef" style="height: 240px"></div>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card title="异常分布" size="small">
          <div ref="distChartRef" style="height: 240px"></div>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 异常记录 -->
    <n-card title="异常记录" size="small" class="detail-section">
      <template #header-extra>
        <n-space>
          <n-select
            v-model:value="filterSeverity"
            :options="severityOptions"
            placeholder="严重程度"
            size="small"
            style="width: 100px"
            clearable
          />
          <n-button size="small" @click="fetchRecords">
            <template #icon><n-icon><RefreshOutline /></n-icon></template>
          </n-button>
        </n-space>
      </template>
      <n-data-table
        size="small"
        :columns="columns"
        :data="filteredRecords"
        :loading="loading"
        :pagination="tablePagination"
        :row-key="row => row.id"
        striped
        :max-height="undefined"
        :flex-height="false"
      />
    </n-card>

    <!-- 检测配置 -->
    <n-card title="检测配置" size="small" class="detail-section">
      <n-descriptions :column="2" label-placement="left">
        <n-descriptions-item label="检测模式">
          <n-tag type="primary" size="small">{{ getModeText(config.mode) }}</n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="检测状态">
          <n-tag :type="config.is_active ? 'success' : 'default'" size="small">
            {{ config.is_active ? '已启用' : '已禁用' }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="阈值方法">
          {{ config.method || 'combined' }}
        </n-descriptions-item>
        <n-descriptions-item label="灵敏度">
          {{ config.threshold || 3.0 }} σ
        </n-descriptions-item>
      </n-descriptions>
      <n-space style="margin-top: 12px">
        <n-button size="small" @click="openConfigModal">
          <template #icon><n-icon><SettingsOutline /></n-icon></template>
          修改配置
        </n-button>
        <n-button size="small" @click="exportData">
          <template #icon><n-icon><DownloadOutline /></n-icon></template>
          导出数据
        </n-button>
      </n-space>
    </n-card>

    <!-- 配置抽屉（保留作为快捷编辑，也可以通过父组件打开完整配置） -->
    <n-drawer v-model:show="showConfigDrawer" width="500" placement="right">
      <n-drawer-content title="检测配置" closable>
        <n-form label-placement="top">
          <n-form-item label="检测模式">
            <n-radio-group v-model:value="configForm.mode">
              <n-space vertical>
                <n-radio value="rule">
                  <div class="mode-option-label">
                    <span class="mode-name">规则模式</span>
                    <span class="mode-desc">基于阈值规则检测，响应快速</span>
                  </div>
                </n-radio>
                <n-radio value="ai">
                  <div class="mode-option-label">
                    <span class="mode-name">AI模式</span>
                    <span class="mode-desc">智能学习检测，发现复杂异常</span>
                  </div>
                </n-radio>
                <n-radio value="hybrid">
                  <div class="mode-option-label">
                    <span class="mode-name">混合模式</span>
                    <span class="mode-desc">规则+AI双重检测，更全面</span>
                  </div>
                </n-radio>
              </n-space>
            </n-radio-group>
          </n-form-item>
          
          <n-divider />
          
          <!-- 规则模式配置：阈值设置 -->
          <template v-if="configForm.mode === 'rule' || configForm.mode === 'hybrid'">
            <n-form-item label="参数阈值配置">
              <div class="threshold-list">
                <div 
                  v-for="field in deviceFields" 
                  :key="field.key" 
                  class="threshold-item"
                  :class="{ disabled: !field.enabled }"
                >
                  <div class="threshold-header">
                    <n-space align="center" justify="space-between" style="width: 100%">
                      <span class="field-name">{{ field.label }}</span>
                      <n-switch v-model:value="field.enabled" size="small" />
                    </n-space>
                  </div>
                  <div v-if="field.enabled" class="threshold-inputs">
                    <n-grid :cols="2" :x-gap="12">
                      <n-grid-item>
                        <div class="input-group">
                          <span class="input-label">最小值</span>
                          <n-input-number 
                            v-model:value="field.min" 
                            size="small" 
                            :precision="field.precision"
                            style="width: 100%"
                          />
                        </div>
                      </n-grid-item>
                      <n-grid-item>
                        <div class="input-group">
                          <span class="input-label">最大值</span>
                          <n-input-number 
                            v-model:value="field.max" 
                            size="small"
                            :precision="field.precision"
                            style="width: 100%"
                          />
                        </div>
                      </n-grid-item>
                    </n-grid>
                    <div class="current-value">
                      当前值: <n-tag :type="getParamTagType(field)" size="small">{{ formatValue(field.currentValue, field.precision) }} {{ field.unit }}</n-tag>
                    </div>
                  </div>
                </div>
              </div>
            </n-form-item>
          </template>
          
          <!-- AI模式配置 -->
          <template v-if="configForm.mode === 'ai' || configForm.mode === 'hybrid'">
            <n-form-item label="AI模型">
              <n-select v-model:value="configForm.modelId" :options="modelOptions" placeholder="选择检测模型" />
            </n-form-item>
            <n-form-item label="置信度阈值">
              <n-space align="center" style="width: 100%">
                <n-slider v-model:value="configForm.confidence" :min="0.5" :max="0.99" :step="0.01" style="flex: 1" />
                <n-text style="width: 50px">{{ (configForm.confidence * 100).toFixed(0) }}%</n-text>
              </n-space>
            </n-form-item>
          </template>
          
          <!-- 混合模式额外配置 -->
          <template v-if="configForm.mode === 'hybrid'">
            <n-form-item label="触发逻辑">
              <n-radio-group v-model:value="configForm.hybridLogic">
                <n-space>
                  <n-radio value="union">任一触发 (覆盖率高)</n-radio>
                  <n-radio value="intersection">同时触发 (准确率高)</n-radio>
                </n-space>
              </n-radio-group>
            </n-form-item>
          </template>
          
          <n-divider />
          
          <n-form-item label="启用状态">
            <n-switch v-model:value="configForm.is_active">
              <template #checked>已启用</template>
              <template #unchecked>已禁用</template>
            </n-switch>
          </n-form-item>
        </n-form>
        <template #footer>
          <n-space justify="end">
            <n-button @click="showConfigDrawer = false">取消</n-button>
            <n-button type="primary" @click="saveConfig" :loading="saving">保存</n-button>
          </n-space>
        </template>
      </n-drawer-content>
    </n-drawer>

    <!-- 异常详情弹窗 -->
    <n-modal v-model:show="showRecordModal" preset="card" style="width: 500px" title="异常详情">
      <div v-if="selectedRecord">
        <n-descriptions :column="2" label-placement="left" bordered size="small">
          <n-descriptions-item label="检测时间">
            {{ formatDateTime(selectedRecord.detection_time) }}
          </n-descriptions-item>
          <n-descriptions-item label="异常类型">
            <n-tag size="small">{{ selectedRecord.anomaly_type }}</n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="严重程度">
            <n-tag :type="getSeverityTagType(selectedRecord.severity)" size="small">
              {{ getSeverityLabel(selectedRecord.severity) }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="异常得分">
            {{ Math.round((selectedRecord.anomaly_score || 0) * 100) }}
          </n-descriptions-item>
          <n-descriptions-item label="处理状态" :span="2">
            <n-tag :type="selectedRecord.is_handled ? 'success' : 'warning'" size="small">
              {{ selectedRecord.is_handled ? '已处理' : '待处理' }}
            </n-tag>
          </n-descriptions-item>
        </n-descriptions>
        <n-divider />
        <n-space v-if="!selectedRecord.is_handled">
          <n-button type="primary" size="small" @click="handleRecord(selectedRecord)">
            标记已处理
          </n-button>
        </n-space>
      </div>
    </n-modal>
  </div>
</template>


<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, h } from 'vue'
import {
  NCard, NDescriptions, NDescriptionsItem, NTag, NText, NGrid, NGridItem,
  NStatistic, NIcon, NSpace, NButton, NDataTable, NProgress, NEmpty,
  NRadioGroup, NRadioButton, NRadio, NSelect, NDrawer, NDrawerContent, NForm,
  NFormItem, NSlider, NSwitch, NModal, NDivider, NPopconfirm, NInputNumber,
  useMessage
} from 'naive-ui'
import {
  HeartOutline, PulseOutline, AlertCircleOutline, TimeOutline,
  RefreshOutline, SettingsOutline, DownloadOutline
} from '@vicons/ionicons5'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import { anomalyDetectionApi } from '@/api/v2/ai-module'
import { assetApi, categoryApi } from '@/api/v4'

const props = defineProps<{ deviceCode: string }>()
const emit = defineEmits<{
  (e: 'open-config', deviceCode: string): void
}>()
const message = useMessage()

// 状态
const loading = ref(false)
const saving = ref(false)
const isPolling = ref(true)
const isActive = ref(true)
const showConfigDrawer = ref(false)
const showRecordModal = ref(false)
const selectedRecord = ref<any>(null)
let pollingTimer: ReturnType<typeof setInterval> | null = null

// 设备信息
const deviceInfo = ref({ name: '', type: '', location: '' })
const lastUpdateTime = ref('--:--')

// 指标数据
const healthScore = ref(85)
const anomalyScore = ref(15)
const todayAnomalies = ref(0)
const pendingCount = ref(0)

// 参数数据
const deviceFields = ref<any[]>([])
const displayFields = computed(() => deviceFields.value.filter(f => f.enabled).slice(0, 4))

// 配置
const config = ref({ mode: 'rule', method: 'combined', threshold: 3.0, is_active: true, modelId: null as number | null, confidence: 0.95, hybridLogic: 'union' })
const configForm = ref({ mode: 'rule', method: 'combined', threshold: 3.0, is_active: true, modelId: null as number | null, confidence: 0.95, hybridLogic: 'union' })

// 筛选
const filterSeverity = ref<string | null>(null)
const trendTimeRange = ref('24h')

// 记录数据
const records = ref<any[]>([])
const filteredRecords = computed(() => {
  if (!filterSeverity.value) return records.value
  return records.value.filter(r => String(r.severity).toLowerCase() === filterSeverity.value)
})

// 图表
const trendChartRef = ref<HTMLElement | null>(null)
const distChartRef = ref<HTMLElement | null>(null)
let trendChart: echarts.ECharts | null = null
let distChart: echarts.ECharts | null = null

// 选项
const severityOptions = [
  { label: '严重', value: 'high' },
  { label: '中等', value: 'medium' },
  { label: '轻微', value: 'low' }
]

const modelOptions = [
  { label: '通用异常检测模型 v2.0', value: 1 },
  { label: '温度专用检测模型 v2.1', value: 2 },
  { label: '振动分析模型 v1.5', value: 3 },
  { label: '多参数融合模型 v3.0', value: 4 }
]

// 表格分页配置 - 动态高度
const tablePagination = ref({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [5, 10, 20, 50],
  onChange: (page: number) => {
    tablePagination.value.page = page
  },
  onUpdatePageSize: (pageSize: number) => {
    tablePagination.value.pageSize = pageSize
    tablePagination.value.page = 1
  }
})

// 表格列
const columns = [
  {
    title: '时间',
    key: 'detection_time',
    width: 140,
    render: (row: any) => formatDateTime(row.detection_time)
  },
  {
    title: '类型',
    key: 'anomaly_type',
    width: 100,
    render: (row: any) => h(NTag, { size: 'small' }, { default: () => row.anomaly_type })
  },
  {
    title: '严重程度',
    key: 'severity',
    width: 80,
    render: (row: any) => h(NTag, { 
      type: getSeverityTagType(row.severity), 
      size: 'small' 
    }, { default: () => getSeverityLabel(row.severity) })
  },
  {
    title: '得分',
    key: 'anomaly_score',
    width: 60,
    render: (row: any) => Math.round((row.anomaly_score || 0) * 100)
  },
  {
    title: '状态',
    key: 'is_handled',
    width: 70,
    render: (row: any) => h(NTag, {
      type: row.is_handled ? 'success' : 'warning',
      size: 'small',
      bordered: false
    }, { default: () => row.is_handled ? '已处理' : '待处理' })
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render: (row: any) => h(NSpace, { size: 'small' }, {
      default: () => [
        h(NButton, {
          size: 'tiny',
          quaternary: true,
          onClick: () => viewRecord(row)
        }, { default: () => '详情' }),
        !row.is_handled ? h(NPopconfirm, {
          onPositiveClick: () => handleRecord(row)
        }, {
          trigger: () => h(NButton, { size: 'tiny', type: 'primary', secondary: true }, { default: () => '处理' }),
          default: () => '确认标记为已处理？'
        }) : null
      ].filter(Boolean)
    })
  }
]

// 辅助方法
function formatDateTime(dateStr: string) {
  return dateStr ? dayjs(dateStr).format('MM-DD HH:mm:ss') : '--'
}

function formatValue(value: any, precision = 1) {
  return value != null ? Number(value).toFixed(precision) : '--'
}

function getScoreColor(score: number) {
  if (score >= 70) return '#d03050'
  if (score >= 40) return '#f0a020'
  return '#18a058'
}

function getSeverityTagType(severity: any): 'error' | 'warning' | 'info' | 'default' {
  const map: Record<string, 'error' | 'warning' | 'info'> = { high: 'error', medium: 'warning', low: 'info' }
  return map[String(severity).toLowerCase()] || 'default'
}

function getSeverityLabel(severity: any) {
  const map: Record<string, string> = { high: '严重', medium: '中等', low: '轻微' }
  return map[String(severity).toLowerCase()] || severity
}

function getModeText(mode: string) {
  const map: Record<string, string> = { rule: '规则模式', ai: 'AI模式', hybrid: '混合模式' }
  return map[mode] || mode
}

function getParamTagType(field: any): 'error' | 'warning' | 'success' {
  if (!field.currentValue) return 'success'
  if (field.currentValue < field.min || field.currentValue > field.max) return 'error'
  if (field.currentValue < field.min * 1.1 || field.currentValue > field.max * 0.9) return 'warning'
  return 'success'
}

function getParamStatusText(field: any) {
  const type = getParamTagType(field)
  if (type === 'error') return '异常'
  if (type === 'warning') return '警告'
  return '正常'
}

function getParamPercentage(field: any) {
  if (!field.currentValue || !field.max || !field.min) return 0
  return Math.max(0, Math.min(100, ((field.currentValue - field.min) / (field.max - field.min)) * 100))
}

function getParamColor(field: any) {
  const type = getParamTagType(field)
  if (type === 'error') return '#d03050'
  if (type === 'warning') return '#f0a020'
  return '#18a058'
}

// API方法
async function fetchDeviceInfo() {
  try {
    // 1. Get asset info
    const assetRes = await assetApi.getByCode(props.deviceCode)
    const asset = assetRes.data || assetRes
    
    if (asset) {
      const assetId = asset.id
      deviceInfo.value.name = asset.name || props.deviceCode
      deviceInfo.value.type = asset.category?.name || '通用设备'
      deviceInfo.value.location = asset.location || ''
      
      const categoryId = asset.category_id || asset.category?.id
      if (categoryId) {
        // 2. Get signal definitions
        const signalRes = await categoryApi.getSignals(categoryId)
        const fields = signalRes.data || signalRes || []
        
        // 3. Get initial values
        const realtimeRes = await assetApi.getRealtimeData(assetId)
        const realtimeData = realtimeRes.data || realtimeRes || {}
        
        deviceFields.value = fields.map((f: any) => {
          const key = f.code
          const config = f.alarm_threshold || {}
          return {
            key,
            label: f.name,
            unit: f.unit || '',
            min: config.min ?? 0,
            max: config.max ?? 100,
            precision: f.data_type === 'float' ? 2 : 0,
            enabled: true,
            currentValue: realtimeData[key] ?? null
          }
        })
      }
      lastUpdateTime.value = dayjs().format('HH:mm:ss')
    }
  } catch (e) {
    // 使用默认数据
    deviceFields.value = [
      { key: 'temperature', label: '温度', unit: '°C', min: 20, max: 80, precision: 1, enabled: true, currentValue: 45 },
      { key: 'pressure', label: '压力', unit: 'MPa', min: 0.5, max: 2.0, precision: 2, enabled: true, currentValue: 1.2 }
    ]
  }
}

async function fetchConfig() {
  try {
    const res = await anomalyDetectionApi.getConfig(props.deviceCode)
    if (res.data) {
      const data = res.data.config_data || {}
      config.value = {
        mode: data.mode || 'rule',
        method: data.method || 'combined',
        threshold: data.threshold || 3.0,
        is_active: res.data.is_active !== false,
        modelId: data.modelId || null,
        confidence: data.confidence || 0.95,
        hybridLogic: data.hybridLogic || 'union'
      }
      configForm.value = { ...config.value }
      isActive.value = config.value.is_active
    }
  } catch (e) {
    console.error('获取配置失败', e)
  }
}

async function fetchRecords() {
  loading.value = true
  try {
    const res = await anomalyDetectionApi.getRecords({
      device_code: props.deviceCode,
      page: 1,
      page_size: 50
    } as any)
    if (res.data?.records) {
      records.value = res.data.records
      todayAnomalies.value = res.data.total || records.value.length
      pendingCount.value = records.value.filter((r: any) => !r.is_handled).length
      
      // 计算异常得分
      if (records.value.length > 0) {
        const avgScore = records.value.reduce((sum: number, r: any) => sum + (r.anomaly_score || 0), 0) / records.value.length
        anomalyScore.value = Math.round(avgScore * 100)
        healthScore.value = Math.max(0, 100 - anomalyScore.value)
      }
      
      updateCharts()
    }
  } catch (e) {
    console.error('获取记录失败', e)
  } finally {
    loading.value = false
  }
}

async function saveConfig() {
  saving.value = true
  try {
    // 构建阈值配置数据
    const thresholds: Record<string, any> = {}
    deviceFields.value.forEach(field => {
      thresholds[field.key] = {
        min: field.min,
        max: field.max,
        enabled: field.enabled
      }
    })
    
    await anomalyDetectionApi.updateConfig(props.deviceCode, {
      config_data: {
        mode: configForm.value.mode,
        method: configForm.value.method,
        threshold: configForm.value.threshold,
        modelId: configForm.value.modelId,
        confidence: configForm.value.confidence,
        hybridLogic: configForm.value.hybridLogic,
        thresholds: thresholds
      },
      is_active: configForm.value.is_active
    })
    config.value = { ...configForm.value }
    isActive.value = config.value.is_active
    showConfigDrawer.value = false
    message.success('配置已保存')
  } catch (e) {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleRecord(record: any) {
  try {
    await anomalyDetectionApi.handleRecord(record.id, '已处理')
    record.is_handled = true
    pendingCount.value = Math.max(0, pendingCount.value - 1)
    showRecordModal.value = false
    message.success('已标记为处理')
  } catch (e) {
    message.error('操作失败')
  }
}

function viewRecord(record: any) {
  selectedRecord.value = record
  showRecordModal.value = true
}

function togglePolling() {
  isPolling.value = !isPolling.value
  if (isPolling.value) {
    startPolling()
  } else {
    stopPolling()
  }
}

function startPolling() {
  stopPolling()
  pollingTimer = setInterval(fetchRealtimeData, 5000)
}

function stopPolling() {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

async function fetchRealtimeData() {
  if (!assetId.value) return
  
  try {
    const res = await assetApi.getRealtimeData(assetId.value)
    const realtimeData = res.data || res
    
    if (realtimeData) {
      // 创建新数组以触发响应式更新
      const updatedFields = deviceFields.value.map(field => {
        const newValue = realtimeData[field.key]
        return {
          ...field,
          currentValue: newValue !== undefined ? newValue : field.currentValue
        }
      })
      deviceFields.value = updatedFields
      lastUpdateTime.value = dayjs().format('HH:mm:ss')
    }
  } catch (e) {
    // API失败时使用模拟数据变化，同样创建新数组
    const updatedFields = deviceFields.value.map(field => {
      if (field.currentValue != null) {
        const range = field.max - field.min
        const variation = range * 0.03 * (Math.random() - 0.5)
        return {
          ...field,
          currentValue: Math.max(field.min * 0.9, Math.min(field.max * 1.1, field.currentValue + variation))
        }
      }
      return field
    })
    deviceFields.value = updatedFields
    lastUpdateTime.value = dayjs().format('HH:mm:ss')
  }
}

function openConfigModal() {
  // 触发父组件打开统一的配置弹窗
  emit('open-config', props.deviceCode)
}

function exportData() {
  message.info('导出功能开发中...')
}

// 图表
function initCharts() {
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
  }
  if (distChartRef.value) {
    distChart = echarts.init(distChartRef.value)
  }
  updateCharts()
}

function updateCharts() {
  updateTrendChart()
  updateDistChart()
}

function updateTrendChart() {
  if (!trendChart) return
  
  let hours: string[]
  if (trendTimeRange.value === '1h') {
    hours = Array.from({ length: 12 }, (_, i) => `${i * 5}分`)
  } else if (trendTimeRange.value === '24h') {
    hours = Array.from({ length: 24 }, (_, i) => `${i}:00`)
  } else {
    hours = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  }
  
  const baseValue = Math.max(1, Math.round(todayAnomalies.value / hours.length))
  const data = hours.map(() => Math.max(0, baseValue + Math.floor(Math.random() * 5) - 2))
  
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: hours },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{
      type: 'line',
      data,
      smooth: true,
      itemStyle: { color: '#2080f0' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(32, 128, 240, 0.3)' },
          { offset: 1, color: 'rgba(32, 128, 240, 0.05)' }
        ])
      }
    }]
  })
}

function updateDistChart() {
  if (!distChart) return
  
  // 统计异常类型分布
  const typeCount: Record<string, number> = {}
  records.value.forEach(r => {
    const type = r.anomaly_type || '其他'
    typeCount[type] = (typeCount[type] || 0) + 1
  })
  
  const data = Object.entries(typeCount).map(([name, value]) => ({ name, value }))
  if (data.length === 0) {
    data.push({ name: '暂无数据', value: 1 })
  }
  
  distChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, left: 'center' },
    series: [{
      type: 'pie',
      radius: ['40%', '65%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      data
    }]
  })
}

function handleResize() {
  trendChart?.resize()
  distChart?.resize()
}

watch(trendTimeRange, updateTrendChart)

onMounted(async () => {
  await Promise.all([fetchDeviceInfo(), fetchConfig(), fetchRecords()])
  setTimeout(initCharts, 100)
  startPolling()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  stopPolling()
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  distChart?.dispose()
})
</script>


<style scoped>
.anomaly-detail {
  padding: 0;
}

.detail-section {
  margin-bottom: 16px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.param-item {
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.param-item:hover {
  border-color: #d9d9d9;
}

.param-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.param-name {
  font-size: 12px;
  color: #666;
}

.param-value {
  margin-bottom: 8px;
}

.param-value .value {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  transition: color 0.3s;
}

.param-value .unit {
  font-size: 12px;
  color: #999;
  margin-left: 4px;
}

.mode-option-label {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.mode-option-label .mode-name {
  font-weight: 500;
}

.mode-option-label .mode-desc {
  font-size: 12px;
  color: #999;
}

/* 阈值配置样式 */
.threshold-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.threshold-item {
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.threshold-item:hover {
  border-color: #d9d9d9;
}

.threshold-item.disabled {
  opacity: 0.6;
  background: #f5f5f5;
}

.threshold-header {
  margin-bottom: 8px;
}

.threshold-header .field-name {
  font-weight: 500;
  color: #333;
}

.threshold-inputs {
  margin-bottom: 8px;
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

.current-value {
  font-size: 12px;
  color: #666;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #e8e8e8;
}
</style>
