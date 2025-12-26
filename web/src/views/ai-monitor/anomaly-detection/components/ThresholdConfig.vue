<template>
  <div class="threshold-config">
    <n-grid :cols="2" :x-gap="16" :y-gap="16">
      <n-grid-item v-for="(item, key) in configData" :key="key">
        <n-card :title="getParameterName(key)" size="small" hoverable>
          <template #header-extra>
            <n-switch
              v-model:value="item.enabled"
              @update:value="handleEnabledChange(key, $event)"
            />
          </template>

          <div class="threshold-item" :class="{ disabled: !item.enabled }">
            <n-space vertical>
              <div class="threshold-range">
                <n-space align="center">
                  <span class="label">最小值:</span>
                  <n-input-number
                    v-model:value="item.min"
                    :disabled="!item.enabled"
                    :precision="getDecimalPlaces(key)"
                    :step="getStep(key)"
                    :min="getMinLimit(key)"
                    :max="item.max"
                    size="small"
                    style="width: 120px"
                    @update:value="handleValueChange"
                  />
                  <span class="unit">{{ getUnit(key) }}</span>
                </n-space>
              </div>

              <div class="threshold-range">
                <n-space align="center">
                  <span class="label">最大值:</span>
                  <n-input-number
                    v-model:value="item.max"
                    :disabled="!item.enabled"
                    :precision="getDecimalPlaces(key)"
                    :step="getStep(key)"
                    :min="item.min"
                    :max="getMaxLimit(key)"
                    size="small"
                    style="width: 120px"
                    @update:value="handleValueChange"
                  />
                  <span class="unit">{{ getUnit(key) }}</span>
                </n-space>
              </div>

              <!-- 当前值显示 -->
              <div class="current-value">
                <n-space align="center">
                  <span class="label">当前值:</span>
                  <n-tag :type="getCurrentValueStatus(key)" size="small">
                    {{ getCurrentValue(key) }}{{ getUnit(key) }}
                  </n-tag>
                </n-space>
              </div>

              <!-- 阈值状态指示器 -->
              <div class="status-indicator">
                <n-progress
                  type="line"
                  :percentage="getProgressPercentage(key)"
                  :status="getProgressStatus(key)"
                  :show-indicator="false"
                  :height="6"
                />
                <div class="progress-labels">
                  <span class="min-label">{{ item.min }}</span>
                  <span class="max-label">{{ item.max }}</span>
                </div>
              </div>
            </n-space>
          </div>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 操作按钮 -->
    <div class="actions">
      <n-space>
        <n-button type="primary" @click="saveConfig">
          <template #icon>
            <n-icon><SaveOutline /></n-icon>
          </template>
          保存配置
        </n-button>
        <n-button @click="resetConfig">
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
          </template>
          重置默认
        </n-button>
        <n-button @click="importConfig">
          <template #icon>
            <n-icon><CloudUploadOutline /></n-icon>
          </template>
          导入配置
        </n-button>
        <n-button @click="exportConfig">
          <template #icon>
            <n-icon><CloudDownloadOutline /></n-icon>
          </template>
          导出配置
        </n-button>
      </n-space>
    </div>

    <!-- 配置预设 -->
    <n-card title="配置预设" class="mt-4" size="small">
      <n-space>
        <n-button
          v-for="preset in presets"
          :key="preset.name"
          size="small"
          @click="applyPreset(preset)"
        >
          {{ preset.name }}
        </n-button>
      </n-space>
    </n-card>

    <!-- 高级设置 -->
    <n-card title="高级设置" class="mt-4" size="small">
      <n-grid :cols="2" :x-gap="16">
        <n-grid-item>
          <n-form-item label="检测频率">
            <n-select
              v-model:value="advancedConfig.frequency"
              :options="frequencyOptions"
              size="small"
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="异常持续时间">
            <n-input-number
              v-model:value="advancedConfig.duration"
              :min="1"
              :max="300"
              suffix="秒"
              size="small"
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="置信度阈值">
            <n-slider
              v-model:value="advancedConfig.confidence"
              :min="50"
              :max="100"
              :step="5"
              :format-tooltip="(value) => `${value}%`"
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="自动处理">
            <n-switch v-model:value="advancedConfig.autoHandle" />
          </n-form-item>
        </n-grid-item>
      </n-grid>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useMessage } from 'naive-ui'
import {
  SaveOutline,
  RefreshOutline,
  CloudUploadOutline,
  CloudDownloadOutline,
} from '@vicons/ionicons5'

const props = defineProps({
  config: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['update', 'reset'])

const message = useMessage()

// 响应式数据
const configData = ref({ ...props.config })

// 模拟当前设备值
const currentValues = ref({
  temperature: 75.2,
  pressure: 1.8,
  vibration: 3.5,
  current: 28.6,
})

// 高级配置
const advancedConfig = ref({
  frequency: 'normal', // 检测频率
  duration: 30, // 异常持续时间（秒）
  confidence: 85, // 置信度阈值
  autoHandle: false, // 自动处理
})

// 频率选项
const frequencyOptions = [
  { label: '低频 (5分钟)', value: 'low' },
  { label: '正常 (1分钟)', value: 'normal' },
  { label: '高频 (30秒)', value: 'high' },
  { label: '实时 (10秒)', value: 'realtime' },
]

// 配置预设
const presets = [
  {
    name: '严格模式',
    config: {
      temperature: { min: 25, max: 75, enabled: true },
      pressure: { min: 0.8, max: 1.8, enabled: true },
      vibration: { min: 0, max: 8, enabled: true },
      current: { min: 10, max: 45, enabled: true },
    },
  },
  {
    name: '标准模式',
    config: {
      temperature: { min: 20, max: 80, enabled: true },
      pressure: { min: 0.5, max: 2.0, enabled: true },
      vibration: { min: 0, max: 10, enabled: true },
      current: { min: 5, max: 50, enabled: true },
    },
  },
  {
    name: '宽松模式',
    config: {
      temperature: { min: 15, max: 85, enabled: true },
      pressure: { min: 0.3, max: 2.5, enabled: true },
      vibration: { min: 0, max: 15, enabled: true },
      current: { min: 0, max: 60, enabled: true },
    },
  },
]

// 方法
const getParameterName = (key) => {
  const nameMap = {
    temperature: '温度',
    pressure: '压力',
    vibration: '振动',
    current: '电流',
  }
  return nameMap[key] || key
}

const getUnit = (key) => {
  const unitMap = {
    temperature: '°C',
    pressure: 'MPa',
    vibration: 'mm/s',
    current: 'A',
  }
  return unitMap[key] || ''
}

const getDecimalPlaces = (key) => {
  const decimalMap = {
    temperature: 1,
    pressure: 1,
    vibration: 1,
    current: 1,
  }
  return decimalMap[key] || 0
}

const getStep = (key) => {
  const stepMap = {
    temperature: 1,
    pressure: 0.1,
    vibration: 0.5,
    current: 1,
  }
  return stepMap[key] || 1
}

const getMinLimit = (key) => {
  const limitMap = {
    temperature: -50,
    pressure: 0,
    vibration: 0,
    current: 0,
  }
  return limitMap[key] || 0
}

const getMaxLimit = (key) => {
  const limitMap = {
    temperature: 200,
    pressure: 10,
    vibration: 50,
    current: 100,
  }
  return limitMap[key] || 100
}

const getCurrentValue = (key) => {
  return currentValues.value[key] || 0
}

const getCurrentValueStatus = (key) => {
  const current = getCurrentValue(key)
  const config = configData.value[key]

  if (!config || !config.enabled) return 'default'

  if (current < config.min || current > config.max) {
    return 'error'
  } else if (current <= config.min * 1.1 || current >= config.max * 0.9) {
    return 'warning'
  }
  return 'success'
}

const getProgressPercentage = (key) => {
  const current = getCurrentValue(key)
  const config = configData.value[key]

  if (!config || !config.enabled) return 0

  const range = config.max - config.min
  const position = current - config.min
  return Math.max(0, Math.min(100, (position / range) * 100))
}

const getProgressStatus = (key) => {
  const status = getCurrentValueStatus(key)
  const statusMap = {
    error: 'error',
    warning: 'warning',
    success: 'success',
    default: 'default',
  }
  return statusMap[status] || 'default'
}

const handleEnabledChange = (key, enabled) => {
  configData.value[key].enabled = enabled
  handleValueChange()
}

const handleValueChange = () => {
  emit('update', configData.value)
}

const saveConfig = () => {
  emit('update', configData.value)
  message.success('配置已保存')
}

const resetConfig = () => {
  emit('reset')
  configData.value = { ...props.config }
  message.info('配置已重置')
}

const applyPreset = (preset) => {
  configData.value = { ...preset.config }
  emit('update', configData.value)
  message.success(`已应用${preset.name}配置`)
}

const importConfig = () => {
  // 模拟导入配置
  message.info('配置导入功能开发中...')
}

const exportConfig = () => {
  // 模拟导出配置
  const configJson = JSON.stringify(
    {
      thresholds: configData.value,
      advanced: advancedConfig.value,
    },
    null,
    2
  )

  // 创建下载链接
  const blob = new Blob([configJson], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `threshold-config-${new Date().toISOString().split('T')[0]}.json`
  a.click()
  URL.revokeObjectURL(url)

  message.success('配置已导出')
}

// 监听配置变化
watch(
  () => props.config,
  (newConfig) => {
    configData.value = { ...newConfig }
  },
  { deep: true }
)

// 模拟实时数据更新
setInterval(() => {
  // 随机更新当前值
  Object.keys(currentValues.value).forEach((key) => {
    const config = configData.value[key]
    if (config && config.enabled) {
      const range = config.max - config.min
      const variation = range * 0.1 * (Math.random() - 0.5)
      currentValues.value[key] = Math.max(
        config.min * 0.8,
        Math.min(config.max * 1.2, currentValues.value[key] + variation)
      )
    }
  })
}, 5000) // 5秒更新一次
</script>

<style scoped>
.threshold-config {
  width: 100%;
}

.threshold-item {
  transition: opacity 0.3s ease;
}

.threshold-item.disabled {
  opacity: 0.5;
}

.threshold-range {
  margin-bottom: 8px;
}

.label {
  display: inline-block;
  width: 60px;
  font-size: 12px;
  color: #666;
}

.unit {
  font-size: 12px;
  color: #999;
  margin-left: 4px;
}

.current-value {
  padding: 8px 0;
  border-top: 1px solid #f0f0f0;
}

.status-indicator {
  position: relative;
}

.progress-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: #999;
  margin-top: 2px;
}

.actions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.mt-4 {
  margin-top: 16px;
}
</style>
