<template>
  <div class="threshold-form">
    <n-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      :label-placement="labelPlacement"
      :label-width="labelWidth"
      :size="size"
    >
      <!-- 基础阈值配置 -->
      <n-card title="基础阈值配置" size="small" class="config-section">
        <n-form-item label="阈值名称" path="name">
          <n-input
            v-model:value="formData.name"
            placeholder="请输入阈值配置名称"
            :disabled="readonly"
          />
        </n-form-item>

        <n-form-item label="阈值类型" path="type">
          <n-select
            v-model:value="formData.type"
            :options="thresholdTypeOptions"
            placeholder="请选择阈值类型"
            :disabled="readonly"
            @update:value="handleTypeChange"
          />
        </n-form-item>

        <n-form-item label="监控指标" path="metric">
          <n-select
            v-model:value="formData.metric"
            :options="metricOptions"
            placeholder="请选择监控指标"
            :disabled="readonly"
            @update:value="handleMetricChange"
          />
        </n-form-item>

        <n-form-item label="描述" path="description">
          <n-input
            v-model:value="formData.description"
            type="textarea"
            placeholder="请输入阈值配置描述"
            :autosize="{ minRows: 2, maxRows: 4 }"
            :disabled="readonly"
          />
        </n-form-item>
      </n-card>

      <!-- 阈值设置 -->
      <n-card title="阈值设置" size="small" class="config-section">
        <!-- 单一阈值 -->
        <div v-if="formData.type === 'single'">
          <n-form-item label="阈值" path="threshold.value">
            <n-input-number
              v-model:value="formData.threshold.value"
              :precision="precision"
              :step="step"
              placeholder="请输入阈值"
              :disabled="readonly"
              style="width: 100%"
            >
              <template #suffix>
                <span class="threshold-unit">{{ unit }}</span>
              </template>
            </n-input-number>
          </n-form-item>

          <n-form-item label="比较方式" path="threshold.operator">
            <n-select
              v-model:value="formData.threshold.operator"
              :options="operatorOptions"
              :disabled="readonly"
            />
          </n-form-item>
        </div>

        <!-- 范围阈值 -->
        <div v-if="formData.type === 'range'">
          <n-form-item label="下限" path="threshold.min">
            <n-input-number
              v-model:value="formData.threshold.min"
              :precision="precision"
              :step="step"
              placeholder="请输入下限值"
              :disabled="readonly"
              style="width: 100%"
            >
              <template #suffix>
                <span class="threshold-unit">{{ unit }}</span>
              </template>
            </n-input-number>
          </n-form-item>

          <n-form-item label="上限" path="threshold.max">
            <n-input-number
              v-model:value="formData.threshold.max"
              :precision="precision"
              :step="step"
              placeholder="请输入上限值"
              :disabled="readonly"
              style="width: 100%"
            >
              <template #suffix>
                <span class="threshold-unit">{{ unit }}</span>
              </template>
            </n-input-number>
          </n-form-item>
        </div>

        <!-- 多级阈值 -->
        <div v-if="formData.type === 'multi-level'">
          <n-form-item label="阈值级别">
            <n-dynamic-input
              v-model:value="formData.threshold.levels"
              :on-create="createThresholdLevel"
              :disabled="readonly"
            >
              <template #default="{ value, index }">
                <div class="threshold-level-item">
                  <n-select
                    v-model:value="value.level"
                    :options="levelOptions"
                    placeholder="级别"
                    style="width: 100px; margin-right: 8px"
                  />
                  <n-input-number
                    v-model:value="value.value"
                    :precision="precision"
                    :step="step"
                    placeholder="阈值"
                    style="width: 120px; margin-right: 8px"
                  />
                  <n-select
                    v-model:value="value.operator"
                    :options="operatorOptions"
                    placeholder="比较方式"
                    style="width: 100px"
                  />
                </div>
              </template>
            </n-dynamic-input>
          </n-form-item>
        </div>

        <!-- 百分位阈值 -->
        <div v-if="formData.type === 'percentile'">
          <n-form-item label="百分位" path="threshold.percentile">
            <n-input-number
              v-model:value="formData.threshold.percentile"
              :min="1"
              :max="99"
              :step="1"
              placeholder="请输入百分位值"
              :disabled="readonly"
              style="width: 100%"
            >
              <template #suffix>
                <span class="threshold-unit">%</span>
              </template>
            </n-input-number>
          </n-form-item>

          <n-form-item label="统计窗口" path="threshold.window">
            <n-input-number
              v-model:value="formData.threshold.window"
              :min="1"
              placeholder="统计窗口大小"
              :disabled="readonly"
              style="width: 100%"
            >
              <template #suffix>
                <span class="threshold-unit">{{ windowUnit }}</span>
              </template>
            </n-input-number>
          </n-form-item>
        </div>
      </n-card>

      <!-- 告警配置 -->
      <n-card title="告警配置" size="small" class="config-section">
        <n-form-item label="启用告警">
          <n-switch v-model:value="formData.alert.enabled" :disabled="readonly" />
        </n-form-item>

        <div v-if="formData.alert.enabled" class="alert-config">
          <n-form-item label="告警级别" path="alert.level">
            <n-select
              v-model:value="formData.alert.level"
              :options="alertLevelOptions"
              :disabled="readonly"
            />
          </n-form-item>

          <n-form-item label="告警消息" path="alert.message">
            <n-input
              v-model:value="formData.alert.message"
              placeholder="请输入告警消息模板"
              :disabled="readonly"
            />
          </n-form-item>

          <n-form-item label="通知方式" path="alert.channels">
            <n-checkbox-group v-model:value="formData.alert.channels" :disabled="readonly">
              <n-space>
                <n-checkbox value="email">邮件</n-checkbox>
                <n-checkbox value="sms">短信</n-checkbox>
                <n-checkbox value="webhook">Webhook</n-checkbox>
                <n-checkbox value="dashboard">仪表板</n-checkbox>
              </n-space>
            </n-checkbox-group>
          </n-form-item>

          <n-form-item label="冷却时间" path="alert.cooldown">
            <n-input-number
              v-model:value="formData.alert.cooldown"
              :min="0"
              placeholder="告警冷却时间"
              :disabled="readonly"
              style="width: 100%"
            >
              <template #suffix>
                <span class="threshold-unit">分钟</span>
              </template>
            </n-input-number>
          </n-form-item>
        </div>
      </n-card>

      <!-- 高级设置 -->
      <n-card title="高级设置" size="small" class="config-section">
        <n-form-item label="数据平滑">
          <n-switch v-model:value="formData.advanced.smoothing.enabled" :disabled="readonly" />
        </n-form-item>

        <div v-if="formData.advanced.smoothing.enabled" class="smoothing-config">
          <n-grid :cols="2" :x-gap="16">
            <n-grid-item>
              <n-form-item label="平滑方法" path="advanced.smoothing.method">
                <n-select
                  v-model:value="formData.advanced.smoothing.method"
                  :options="smoothingMethodOptions"
                  :disabled="readonly"
                />
              </n-form-item>
            </n-grid-item>

            <n-grid-item>
              <n-form-item label="窗口大小" path="advanced.smoothing.window">
                <n-input-number
                  v-model:value="formData.advanced.smoothing.window"
                  :min="3"
                  :max="100"
                  :disabled="readonly"
                />
              </n-form-item>
            </n-grid-item>
          </n-grid>
        </div>

        <n-form-item label="异常检测">
          <n-switch
            v-model:value="formData.advanced.anomalyDetection.enabled"
            :disabled="readonly"
          />
        </n-form-item>

        <div v-if="formData.advanced.anomalyDetection.enabled" class="anomaly-config">
          <n-grid :cols="2" :x-gap="16">
            <n-grid-item>
              <n-form-item label="检测算法" path="advanced.anomalyDetection.algorithm">
                <n-select
                  v-model:value="formData.advanced.anomalyDetection.algorithm"
                  :options="anomalyAlgorithmOptions"
                  :disabled="readonly"
                />
              </n-form-item>
            </n-grid-item>

            <n-grid-item>
              <n-form-item label="敏感度" path="advanced.anomalyDetection.sensitivity">
                <n-slider
                  v-model:value="formData.advanced.anomalyDetection.sensitivity"
                  :min="0.1"
                  :max="1"
                  :step="0.1"
                  :marks="{ 0.1: '低', 0.5: '中', 1: '高' }"
                  :disabled="readonly"
                />
              </n-form-item>
            </n-grid-item>
          </n-grid>
        </div>

        <n-form-item label="自动调整">
          <n-switch v-model:value="formData.advanced.autoAdjust.enabled" :disabled="readonly" />
        </n-form-item>

        <div v-if="formData.advanced.autoAdjust.enabled" class="auto-adjust-config">
          <n-form-item label="调整周期" path="advanced.autoAdjust.interval">
            <n-select
              v-model:value="formData.advanced.autoAdjust.interval"
              :options="adjustIntervalOptions"
              :disabled="readonly"
            />
          </n-form-item>
        </div>
      </n-card>

      <!-- 操作按钮 -->
      <div v-if="!readonly" class="form-actions">
        <n-space>
          <n-button @click="resetForm">重置</n-button>
          <n-button @click="validateForm">验证配置</n-button>
          <n-button @click="previewThreshold">预览效果</n-button>
          <n-button type="primary" :loading="submitting" @click="submitForm">
            {{ submitText }}
          </n-button>
        </n-space>
      </div>
    </n-form>

    <!-- 预览模态框 -->
    <n-modal v-model:show="showPreview" preset="card" title="阈值预览" style="width: 600px">
      <div class="threshold-preview">
        <n-alert type="info" style="margin-bottom: 16px"> 以下是当前阈值配置的预览效果 </n-alert>

        <n-descriptions :column="2" bordered>
          <n-descriptions-item label="阈值类型">
            {{ getThresholdTypeLabel(formData.type) }}
          </n-descriptions-item>
          <n-descriptions-item label="监控指标">
            {{ getMetricLabel(formData.metric) }}
          </n-descriptions-item>
          <n-descriptions-item label="阈值设置" :span="2">
            {{ getThresholdDescription() }}
          </n-descriptions-item>
          <n-descriptions-item v-if="formData.alert.enabled" label="告警级别">
            <n-tag :type="getAlertTagType(formData.alert.level)">
              {{ getAlertLevelLabel(formData.alert.level) }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item v-if="formData.alert.enabled" label="通知方式">
            <n-space>
              <n-tag v-for="channel in formData.alert.channels" :key="channel" size="small">
                {{ getChannelLabel(channel) }}
              </n-tag>
            </n-space>
          </n-descriptions-item>
        </n-descriptions>
      </div>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useMessage } from 'naive-ui'

// Props
const props = defineProps({
  // 初始数据
  modelValue: {
    type: Object,
    default: () => ({}),
  },
  // 是否只读
  readonly: {
    type: Boolean,
    default: false,
  },
  // 表单大小
  size: {
    type: String,
    default: 'medium',
  },
  // 标签位置
  labelPlacement: {
    type: String,
    default: 'left',
  },
  // 标签宽度
  labelWidth: {
    type: [String, Number],
    default: 120,
  },
  // 提交按钮文本
  submitText: {
    type: String,
    default: '保存配置',
  },
  // 提交状态
  submitting: {
    type: Boolean,
    default: false,
  },
})

// Emits
const emit = defineEmits(['update:modelValue', 'submit', 'validate', 'reset', 'preview'])

// 响应式数据
const formRef = ref(null)
const message = useMessage()
const showPreview = ref(false)

// 表单数据
const formData = reactive({
  name: '',
  type: 'single',
  metric: '',
  description: '',
  threshold: {
    value: null,
    operator: 'gt',
    min: null,
    max: null,
    levels: [
      { level: 'warning', value: null, operator: 'gt' },
      { level: 'critical', value: null, operator: 'gt' },
    ],
    percentile: 95,
    window: 24,
  },
  alert: {
    enabled: true,
    level: 'warning',
    message: '',
    channels: ['dashboard'],
    cooldown: 5,
  },
  advanced: {
    smoothing: {
      enabled: false,
      method: 'moving_average',
      window: 5,
    },
    anomalyDetection: {
      enabled: false,
      algorithm: 'isolation_forest',
      sensitivity: 0.5,
    },
    autoAdjust: {
      enabled: false,
      interval: 'daily',
    },
  },
})

// 选项数据
const thresholdTypeOptions = [
  { label: '单一阈值', value: 'single' },
  { label: '范围阈值', value: 'range' },
  { label: '多级阈值', value: 'multi-level' },
  { label: '百分位阈值', value: 'percentile' },
]

const metricOptions = [
  { label: 'CPU使用率', value: 'cpu_usage', unit: '%', precision: 1, step: 0.1 },
  { label: '内存使用率', value: 'memory_usage', unit: '%', precision: 1, step: 0.1 },
  { label: '磁盘使用率', value: 'disk_usage', unit: '%', precision: 1, step: 0.1 },
  { label: '网络流量', value: 'network_traffic', unit: 'MB/s', precision: 2, step: 0.01 },
  { label: '温度', value: 'temperature', unit: '°C', precision: 1, step: 0.1 },
  { label: '压力', value: 'pressure', unit: 'Pa', precision: 0, step: 1 },
  { label: '振动', value: 'vibration', unit: 'Hz', precision: 2, step: 0.01 },
  { label: '异常分数', value: 'anomaly_score', unit: '', precision: 3, step: 0.001 },
]

const operatorOptions = [
  { label: '大于', value: 'gt' },
  { label: '大于等于', value: 'gte' },
  { label: '小于', value: 'lt' },
  { label: '小于等于', value: 'lte' },
  { label: '等于', value: 'eq' },
  { label: '不等于', value: 'ne' },
]

const levelOptions = [
  { label: '信息', value: 'info' },
  { label: '警告', value: 'warning' },
  { label: '严重', value: 'critical' },
  { label: '紧急', value: 'emergency' },
]

const alertLevelOptions = [
  { label: '信息', value: 'info' },
  { label: '警告', value: 'warning' },
  { label: '严重', value: 'critical' },
  { label: '紧急', value: 'emergency' },
]

const smoothingMethodOptions = [
  { label: '移动平均', value: 'moving_average' },
  { label: '指数平滑', value: 'exponential_smoothing' },
  { label: '中位数滤波', value: 'median_filter' },
]

const anomalyAlgorithmOptions = [
  { label: '孤立森林', value: 'isolation_forest' },
  { label: '局部异常因子', value: 'local_outlier_factor' },
  { label: '单类SVM', value: 'one_class_svm' },
  { label: '统计方法', value: 'statistical' },
]

const adjustIntervalOptions = [
  { label: '每小时', value: 'hourly' },
  { label: '每天', value: 'daily' },
  { label: '每周', value: 'weekly' },
  { label: '每月', value: 'monthly' },
]

// 计算属性
const currentMetric = computed(() => {
  return metricOptions.find((option) => option.value === formData.metric)
})

const unit = computed(() => currentMetric.value?.unit || '')
const precision = computed(() => currentMetric.value?.precision || 0)
const step = computed(() => currentMetric.value?.step || 1)
const windowUnit = computed(() => {
  switch (formData.metric) {
    case 'cpu_usage':
    case 'memory_usage':
    case 'disk_usage':
      return '小时'
    case 'network_traffic':
      return '分钟'
    default:
      return '个数据点'
  }
})

// 表单验证规则
const formRules = {
  name: {
    required: true,
    message: '请输入阈值配置名称',
    trigger: 'blur',
  },
  type: {
    required: true,
    message: '请选择阈值类型',
    trigger: 'change',
  },
  metric: {
    required: true,
    message: '请选择监控指标',
    trigger: 'change',
  },
}

// 创建阈值级别
const createThresholdLevel = () => {
  return {
    level: 'warning',
    value: null,
    operator: 'gt',
  }
}

// 处理阈值类型变化
const handleTypeChange = (type) => {
  // 重置阈值配置
  switch (type) {
    case 'single':
      formData.threshold = {
        ...formData.threshold,
        value: null,
        operator: 'gt',
      }
      break
    case 'range':
      formData.threshold = {
        ...formData.threshold,
        min: null,
        max: null,
      }
      break
    case 'multi-level':
      formData.threshold = {
        ...formData.threshold,
        levels: [
          { level: 'warning', value: null, operator: 'gt' },
          { level: 'critical', value: null, operator: 'gt' },
        ],
      }
      break
    case 'percentile':
      formData.threshold = {
        ...formData.threshold,
        percentile: 95,
        window: 24,
      }
      break
  }
}

// 处理指标变化
const handleMetricChange = (metric) => {
  const metricConfig = metricOptions.find((option) => option.value === metric)
  if (metricConfig) {
    // 根据指标类型设置默认告警消息
    formData.alert.message = `${metricConfig.label}超出阈值`
  }
}

// 获取标签方法
const getThresholdTypeLabel = (type) => {
  return thresholdTypeOptions.find((option) => option.value === type)?.label || type
}

const getMetricLabel = (metric) => {
  return metricOptions.find((option) => option.value === metric)?.label || metric
}

const getAlertLevelLabel = (level) => {
  return alertLevelOptions.find((option) => option.value === level)?.label || level
}

const getChannelLabel = (channel) => {
  const channelMap = {
    email: '邮件',
    sms: '短信',
    webhook: 'Webhook',
    dashboard: '仪表板',
  }
  return channelMap[channel] || channel
}

const getAlertTagType = (level) => {
  const typeMap = {
    info: 'info',
    warning: 'warning',
    critical: 'error',
    emergency: 'error',
  }
  return typeMap[level] || 'default'
}

// 获取阈值描述
const getThresholdDescription = () => {
  const { type, threshold } = formData
  const unitText = unit.value ? ` ${unit.value}` : ''

  switch (type) {
    case 'single':
      return `${getOperatorText(threshold.operator)} ${threshold.value}${unitText}`
    case 'range':
      return `${threshold.min}${unitText} - ${threshold.max}${unitText}`
    case 'multi-level':
      return threshold.levels
        .map(
          (level) => `${level.level}: ${getOperatorText(level.operator)} ${level.value}${unitText}`
        )
        .join(', ')
    case 'percentile':
      return `第${threshold.percentile}百分位，窗口: ${threshold.window}${windowUnit.value}`
    default:
      return '未配置'
  }
}

const getOperatorText = (operator) => {
  const operatorMap = {
    gt: '>',
    gte: '>=',
    lt: '<',
    lte: '<=',
    eq: '=',
    ne: '!=',
  }
  return operatorMap[operator] || operator
}

// 验证表单
const validateForm = async () => {
  try {
    await formRef.value?.validate()
    message.success('配置验证通过')
    emit('validate', formData)
    return true
  } catch (error) {
    message.error('配置验证失败，请检查输入')
    return false
  }
}

// 提交表单
const submitForm = async () => {
  const isValid = await validateForm()
  if (isValid) {
    emit('submit', formData)
  }
}

// 重置表单
const resetForm = () => {
  formRef.value?.restoreValidation()
  Object.assign(formData, props.modelValue)
  emit('reset')
}

// 预览阈值
const previewThreshold = () => {
  showPreview.value = true
  emit('preview', formData)
}

// 监听外部数据变化
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal) {
      Object.assign(formData, newVal)
    }
  },
  { immediate: true, deep: true }
)

// 监听表单数据变化
watch(
  formData,
  (newVal) => {
    emit('update:modelValue', newVal)
  },
  { deep: true }
)

// 暴露方法
defineExpose({
  validate: validateForm,
  submit: submitForm,
  reset: resetForm,
  preview: previewThreshold,
  getFormData: () => formData,
})
</script>

<style scoped>
.threshold-form {
  width: 100%;
}

.config-section {
  margin-bottom: 16px;
}

.config-section:last-of-type {
  margin-bottom: 24px;
}

.threshold-level-item {
  display: flex;
  align-items: center;
  width: 100%;
}

.alert-config,
.smoothing-config,
.anomaly-config,
.auto-adjust-config {
  margin-top: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
}

.threshold-unit {
  color: #999;
  font-size: 12px;
}

.form-actions {
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
  text-align: right;
}

.threshold-preview {
  padding: 16px 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .form-actions {
    text-align: center;
  }

  .threshold-level-item {
    flex-direction: column;
    gap: 8px;
  }

  .threshold-level-item > * {
    width: 100% !important;
    margin-right: 0 !important;
  }
}
</style>
