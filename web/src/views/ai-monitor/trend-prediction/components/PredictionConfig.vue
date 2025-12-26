<template>
  <div class="prediction-config">
    <n-grid :cols="2" :x-gap="24" :y-gap="16">
      <!-- 算法配置 -->
      <n-grid-item>
        <n-card title="算法配置" size="small" hoverable>
          <n-space vertical>
            <n-form-item label="算法来源">
              <n-radio-group v-model:value="configData.sourceType" @update:value="handleConfigChange">
                <n-radio-button value="preset">系统预设</n-radio-button>
                <n-radio-button value="custom">自定义模型</n-radio-button>
              </n-radio-group>
            </n-form-item>

            <n-form-item label="预测算法" v-if="configData.sourceType === 'preset'">
              <n-select
                v-model:value="configData.algorithm"
                :options="algorithmOptions"
                @update:value="handleConfigChange"
              />
            </n-form-item>

            <n-form-item label="选择模型" v-if="configData.sourceType === 'custom'">
              <ModelSelector
                v-model:modelValue="configData.modelId"
                model-type="trend-prediction"
                :show-stats="false"
                :show-selected-info="true"
                @change="handleModelChange"
              />
            </n-form-item>

            <!-- 自定义模型参数展示 -->
            <template v-if="configData.sourceType === 'custom' && selectedModel">
              <n-divider dashed>模型参数</n-divider>
              <n-descriptions label-placement="left" size="small" :column="1" bordered>
                <n-descriptions-item label="算法类型">
                  {{ selectedModel.trainingParameters?.algorithm || '未知' }}
                </n-descriptions-item>
                <n-descriptions-item label="时间窗口">
                  {{ selectedModel.trainingParameters?.window_size || configData.timeWindow }} 天
                </n-descriptions-item>
                <n-descriptions-item label="特征数量">
                  {{ selectedModel.features?.length || 0 }} 个
                </n-descriptions-item>
              </n-descriptions>
            </template>

            <n-form-item label="时间窗口" v-if="configData.sourceType === 'preset'">
              <n-input-number
                v-model:value="configData.timeWindow"
                :min="7"
                :max="365"
                suffix="天"
                @update:value="handleConfigChange"
              />
            </n-form-item>

            <n-form-item label="风险阈值">
              <n-slider
                v-model:value="configData.threshold"
                :min="0.1"
                :max="1.0"
                :step="0.05"
                :format-tooltip="(value) => `${(value * 100).toFixed(0)}%`"
                @update:value="handleConfigChange"
              />
            </n-form-item>

            <n-form-item label="更新频率">
              <n-radio-group
                v-model:value="configData.updateFrequency"
                @update:value="handleConfigChange"
              >
                <n-space>
                  <n-radio value="hourly">每小时</n-radio>
                  <n-radio value="daily">每日</n-radio>
                  <n-radio value="weekly">每周</n-radio>
                </n-space>
              </n-radio-group>
            </n-form-item>
          </n-space>
        </n-card>
      </n-grid-item>

      <!-- 特征参数配置 -->
      <n-grid-item>
        <n-card title="特征参数" size="small" hoverable>
          <n-space vertical>
            <div class="feature-list">
              <n-alert v-if="configData.sourceType === 'custom'" type="info" class="mb-2" show-icon>
                使用模型预设特征，不可修改
              </n-alert>
              <n-checkbox-group
                v-model:value="configData.features"
                :disabled="configData.sourceType === 'custom'"
                @update:value="handleConfigChange"
              >
                <n-space vertical>
                  <n-checkbox
                    v-for="feature in availableFeatures"
                    :key="feature.value"
                    :value="feature.value"
                    :label="feature.label"
                  />
                </n-space>
              </n-checkbox-group>
            </div>

            <n-divider />

            <n-form-item label="数据质量要求">
              <n-slider
                v-model:value="configData.dataQuality"
                :min="0.5"
                :max="1.0"
                :step="0.05"
                :format-tooltip="(value) => `${(value * 100).toFixed(0)}%`"
                @update:value="handleConfigChange"
              />
            </n-form-item>

            <n-form-item label="最小样本数">
              <n-input-number
                v-model:value="configData.minSamples"
                :min="100"
                :max="10000"
                :step="100"
                @update:value="handleConfigChange"
              />
            </n-form-item>
          </n-space>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 高级配置 -->
    <n-card title="高级配置" class="mt-4" size="small">
      <n-grid :cols="3" :x-gap="16">
        <n-grid-item>
          <n-form-item label="模型复杂度">
            <n-select
              v-model:value="advancedConfig.complexity"
              :options="complexityOptions"
              @update:value="handleAdvancedConfigChange"
            />
          </n-form-item>
        </n-grid-item>

        <n-grid-item>
          <n-form-item label="交叉验证折数">
            <n-input-number
              v-model:value="advancedConfig.cvFolds"
              :min="3"
              :max="10"
              @update:value="handleAdvancedConfigChange"
            />
          </n-form-item>
        </n-grid-item>

        <n-grid-item>
          <n-form-item label="早停轮数">
            <n-input-number
              v-model:value="advancedConfig.earlyStopRounds"
              :min="5"
              :max="100"
              @update:value="handleAdvancedConfigChange"
            />
          </n-form-item>
        </n-grid-item>

        <n-grid-item>
          <n-form-item label="学习率">
            <n-input-number
              v-model:value="advancedConfig.learningRate"
              :min="0.001"
              :max="0.1"
              :step="0.001"
              :precision="3"
              @update:value="handleAdvancedConfigChange"
            />
          </n-form-item>
        </n-grid-item>

        <n-grid-item>
          <n-form-item label="批次大小">
            <n-input-number
              v-model:value="advancedConfig.batchSize"
              :min="16"
              :max="512"
              :step="16"
              @update:value="handleAdvancedConfigChange"
            />
          </n-form-item>
        </n-grid-item>

        <n-grid-item>
          <n-form-item label="正则化强度">
            <n-input-number
              v-model:value="advancedConfig.regularization"
              :min="0.0"
              :max="1.0"
              :step="0.01"
              :precision="2"
              @update:value="handleAdvancedConfigChange"
            />
          </n-form-item>
        </n-grid-item>
      </n-grid>
    </n-card>

    <!-- 模型性能指标 -->
    <n-card title="模型性能" class="mt-4" size="small">
      <n-grid :cols="4" :x-gap="16">
        <n-grid-item>
          <n-statistic label="准确率" :value="modelMetrics.accuracy" suffix="%" tabular-nums>
            <template #prefix>
              <n-icon color="#18a058"><CheckmarkCircleOutline /></n-icon>
            </template>
          </n-statistic>
        </n-grid-item>

        <n-grid-item>
          <n-statistic label="精确率" :value="modelMetrics.precision" suffix="%" tabular-nums>
            <template #prefix>
              <n-icon color="#2080f0"><CheckmarkCircleOutline /></n-icon>
            </template>
          </n-statistic>
        </n-grid-item>

        <n-grid-item>
          <n-statistic label="召回率" :value="modelMetrics.recall" suffix="%" tabular-nums>
            <template #prefix>
              <n-icon color="#f0a020"><SearchOutline /></n-icon>
            </template>
          </n-statistic>
        </n-grid-item>

        <n-grid-item>
          <n-statistic label="F1分数" :value="modelMetrics.f1Score" suffix="%" tabular-nums>
            <template #prefix>
              <n-icon color="#722ed1"><StatsChartOutline /></n-icon>
            </template>
          </n-statistic>
        </n-grid-item>
      </n-grid>
    </n-card>

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

      <n-divider />

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
          重置配置
        </n-button>

        <n-button @click="trainModel">
          <template #icon>
            <n-icon><PlayOutline /></n-icon>
          </template>
          训练模型
        </n-button>

        <n-button @click="validateModel">
          <template #icon>
            <n-icon><CheckmarkOutline /></n-icon>
          </template>
          验证模型
        </n-button>

        <n-button @click="exportConfig">
          <template #icon>
            <n-icon><DownloadOutline /></n-icon>
          </template>
          导出配置
        </n-button>
      </n-space>
    </n-card>

    <!-- 训练进度对话框 -->
    <n-modal v-model:show="showTrainingModal" preset="dialog" title="模型训练">
      <div class="training-progress">
        <n-space vertical>
          <div>
            <span>训练进度: </span>
            <n-progress
              type="line"
              :percentage="trainingProgress"
              :show-indicator="true"
              status="info"
            />
          </div>

          <div>
            <span>当前轮次: {{ currentEpoch }} / {{ totalEpochs }}</span>
          </div>

          <div>
            <span>训练损失: {{ trainingLoss.toFixed(4) }}</span>
          </div>

          <div>
            <span>验证损失: {{ validationLoss.toFixed(4) }}</span>
          </div>

          <n-log :log="trainingLog" :rows="8" language="text" />
        </n-space>
      </div>

      <template #action>
        <n-space>
          <n-button :disabled="!isTraining" @click="stopTraining"> 停止训练 </n-button>
          <n-button @click="showTrainingModal = false"> 关闭 </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useMessage } from 'naive-ui'
import {
  CheckmarkCircleOutline,
  SearchOutline,
  StatsChartOutline,
  SaveOutline,
  RefreshOutline,
  PlayOutline,
  CheckmarkOutline,
  DownloadOutline,
} from '@vicons/ionicons5'
import ModelSelector from '@/components/ai-monitor/common/ModelSelector.vue'

const props = defineProps({
  config: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['update', 'reset'])

const message = useMessage()

// 响应式数据
const configData = ref({
  sourceType: 'preset', // 'preset' | 'custom'
  modelId: null,
  ...props.config
})
const selectedModel = ref(null)
const showTrainingModal = ref(false)
const isTraining = ref(false)
const trainingProgress = ref(0)
const currentEpoch = ref(0)
const totalEpochs = ref(100)
const trainingLoss = ref(0.5)
const validationLoss = ref(0.52)
const trainingLog = ref('')

// 高级配置
const advancedConfig = ref({
  complexity: 'medium',
  cvFolds: 5,
  earlyStopRounds: 10,
  learningRate: 0.001,
  batchSize: 64,
  regularization: 0.01,
})

// 模型性能指标
const modelMetrics = ref({
  accuracy: 92.5,
  precision: 89.3,
  recall: 91.7,
  f1Score: 90.5,
})

// 算法选项
const algorithmOptions = [
  { label: 'LSTM (长短期记忆网络)', value: 'lstm' },
  { label: 'GRU (门控循环单元)', value: 'gru' },
  { label: 'Random Forest (随机森林)', value: 'rf' },
  { label: 'XGBoost (极端梯度提升)', value: 'xgboost' },
  { label: 'SVM (支持向量机)', value: 'svm' },
  { label: 'Prophet (时间序列预测)', value: 'prophet' },
]

// 可用特征
const availableFeatures = [
  { label: '温度', value: 'temperature' },
  { label: '压力', value: 'pressure' },
  { label: '振动', value: 'vibration' },
  { label: '电流', value: 'current' },
  { label: '转速', value: 'speed' },
  { label: '功率', value: 'power' },
  { label: '噪音', value: 'noise' },
  { label: '湿度', value: 'humidity' },
]

// 复杂度选项
const complexityOptions = [
  { label: '简单', value: 'simple' },
  { label: '中等', value: 'medium' },
  { label: '复杂', value: 'complex' },
]

// 配置预设
const presets = [
  {
    name: '快速预测',
    config: {
      sourceType: 'preset',
      algorithm: 'rf',
      timeWindow: 7,
      features: ['temperature', 'pressure'],
      threshold: 0.8,
      updateFrequency: 'hourly',
      dataQuality: 0.7,
      minSamples: 500,
    },
  },
  {
    name: '标准配置',
    config: {
      sourceType: 'preset',
      algorithm: 'lstm',
      timeWindow: 30,
      features: ['temperature', 'pressure', 'vibration', 'current'],
      threshold: 0.7,
      updateFrequency: 'daily',
      dataQuality: 0.8,
      minSamples: 1000,
    },
  },
  {
    name: '高精度模式',
    config: {
      sourceType: 'preset',
      algorithm: 'xgboost',
      timeWindow: 60,
      features: ['temperature', 'pressure', 'vibration', 'current', 'speed', 'power'],
      threshold: 0.6,
      updateFrequency: 'daily',
      dataQuality: 0.9,
      minSamples: 2000,
    },
  },
]

// 方法
const handleModelChange = (val: any, option: any) => {
  if (option && option.model) {
    configData.value.modelId = val
    selectedModel.value = option.model
    
    // 如果模型包含特征配置，自动更新特征参数
    if (option.model.features && Array.isArray(option.model.features)) {
      configData.value.features = [...option.model.features]
      message.success(`已根据模型"${option.model.name}"自动加载特征参数`)
    }
    
    // 如果模型包含时间窗口配置，自动更新
    if (option.model.trainingParameters?.window_size) {
      configData.value.timeWindow = option.model.trainingParameters.window_size
    }

    handleConfigChange()
  } else {
    selectedModel.value = null
  }
}

const handleConfigChange = () => {
  emit('update', configData.value)
}

const handleAdvancedConfigChange = () => {
  // 高级配置变化时的处理
  console.log('Advanced config changed:', advancedConfig.value)
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

const trainModel = () => {
  showTrainingModal.value = true
  isTraining.value = true
  trainingProgress.value = 0
  currentEpoch.value = 0
  trainingLog.value = '开始训练模型...\n'

  // 模拟训练过程
  const trainingInterval = setInterval(() => {
    currentEpoch.value++
    trainingProgress.value = (currentEpoch.value / totalEpochs.value) * 100

    // 模拟损失值变化
    trainingLoss.value = Math.max(0.1, trainingLoss.value - Math.random() * 0.01)
    validationLoss.value = Math.max(0.12, validationLoss.value - Math.random() * 0.008)

    trainingLog.value += `Epoch ${currentEpoch.value}/${
      totalEpochs.value
    } - loss: ${trainingLoss.value.toFixed(4)} - val_loss: ${validationLoss.value.toFixed(4)}\n`

    if (currentEpoch.value >= totalEpochs.value) {
      clearInterval(trainingInterval)
      isTraining.value = false
      trainingLog.value += '训练完成！\n'
      message.success('模型训练完成')

      // 更新模型性能指标
      modelMetrics.value = {
        accuracy: 92.5 + Math.random() * 5,
        precision: 89.3 + Math.random() * 5,
        recall: 91.7 + Math.random() * 4,
        f1Score: 90.5 + Math.random() * 4,
      }
    }
  }, 200)
}

const stopTraining = () => {
  isTraining.value = false
  trainingLog.value += '训练已停止\n'
  message.info('训练已停止')
}

const validateModel = () => {
  message.info('正在验证模型...')

  setTimeout(() => {
    message.success('模型验证完成')
    // 更新性能指标
    modelMetrics.value = {
      accuracy: 91.2 + Math.random() * 3,
      precision: 88.5 + Math.random() * 3,
      recall: 90.8 + Math.random() * 3,
      f1Score: 89.6 + Math.random() * 3,
    }
  }, 2000)
}

const exportConfig = () => {
  const configJson = JSON.stringify(
    {
      basic: configData.value,
      advanced: advancedConfig.value,
      metrics: modelMetrics.value,
    },
    null,
    2
  )

  const blob = new Blob([configJson], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `prediction-config-${new Date().toISOString().split('T')[0]}.json`
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
</script>

<style scoped>
.prediction-config {
  width: 100%;
}

.feature-list {
  max-height: 200px;
  overflow-y: auto;
}

.training-progress {
  padding: 16px 0;
}

.mt-4 {
  margin-top: 16px;
}
</style>
