<template>
  <div class="model-config-form">
    <n-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      :label-placement="labelPlacement"
      :label-width="labelWidth"
      :size="size"
    >
      <!-- 基础配置 -->
      <n-card title="基础配置" size="small" class="config-section">
        <n-form-item label="模型名称" path="name">
          <n-input
            v-model:value="formData.name"
            placeholder="请输入模型名称"
            :disabled="readonly"
          />
        </n-form-item>

        <n-form-item label="模型类型" path="type">
          <n-select
            v-model:value="formData.type"
            :options="modelTypeOptions"
            placeholder="请选择模型类型"
            :disabled="readonly"
            @update:value="handleTypeChange"
          />
        </n-form-item>

        <n-form-item label="模型版本" path="version">
          <n-input
            v-model:value="formData.version"
            placeholder="例如: 1.0.0"
            :disabled="readonly"
          />
        </n-form-item>

        <n-form-item label="模型描述" path="description">
          <n-input
            v-model:value="formData.description"
            type="textarea"
            placeholder="请输入模型描述"
            :autosize="{ minRows: 2, maxRows: 4 }"
            :disabled="readonly"
          />
        </n-form-item>
      </n-card>

      <!-- 训练参数 -->
      <n-card title="训练参数" size="small" class="config-section">
        <n-grid :cols="2" :x-gap="16">
          <n-grid-item>
            <n-form-item label="学习率" path="learningRate">
              <n-input-number
                v-model:value="formData.learningRate"
                :min="0.0001"
                :max="1"
                :step="0.0001"
                :precision="4"
                placeholder="0.001"
                :disabled="readonly"
              />
            </n-form-item>
          </n-grid-item>

          <n-grid-item>
            <n-form-item label="批次大小" path="batchSize">
              <n-input-number
                v-model:value="formData.batchSize"
                :min="1"
                :max="1024"
                placeholder="32"
                :disabled="readonly"
              />
            </n-form-item>
          </n-grid-item>

          <n-grid-item>
            <n-form-item label="训练轮数" path="epochs">
              <n-input-number
                v-model:value="formData.epochs"
                :min="1"
                :max="1000"
                placeholder="100"
                :disabled="readonly"
              />
            </n-form-item>
          </n-grid-item>

          <n-grid-item>
            <n-form-item label="验证比例" path="validationSplit">
              <n-input-number
                v-model:value="formData.validationSplit"
                :min="0.1"
                :max="0.5"
                :step="0.1"
                :precision="1"
                placeholder="0.2"
                :disabled="readonly"
              />
            </n-form-item>
          </n-grid-item>
        </n-grid>

        <n-form-item label="优化器" path="optimizer">
          <n-select
            v-model:value="formData.optimizer"
            :options="optimizerOptions"
            placeholder="请选择优化器"
            :disabled="readonly"
          />
        </n-form-item>

        <n-form-item label="损失函数" path="lossFunction">
          <n-select
            v-model:value="formData.lossFunction"
            :options="lossFunctionOptions"
            placeholder="请选择损失函数"
            :disabled="readonly"
          />
        </n-form-item>
      </n-card>

      <!-- 模型结构 -->
      <n-card title="模型结构" size="small" class="config-section">
        <n-form-item label="输入维度" path="inputDim">
          <n-input
            v-model:value="formData.inputDim"
            placeholder="例如: 128 或 [28, 28, 1]"
            :disabled="readonly"
          />
        </n-form-item>

        <n-form-item label="输出维度" path="outputDim">
          <n-input-number
            v-model:value="formData.outputDim"
            :min="1"
            placeholder="输出类别数或维度"
            :disabled="readonly"
          />
        </n-form-item>

        <n-form-item label="隐藏层" path="hiddenLayers">
          <n-dynamic-input
            v-model:value="formData.hiddenLayers"
            :on-create="createHiddenLayer"
            :disabled="readonly"
          >
            <template #default="{ value, index }">
              <div class="hidden-layer-item">
                <n-input-number
                  v-model:value="value.units"
                  :min="1"
                  placeholder="神经元数量"
                  style="margin-right: 8px; width: 120px"
                />
                <n-select
                  v-model:value="value.activation"
                  :options="activationOptions"
                  placeholder="激活函数"
                  style="width: 120px"
                />
              </div>
            </template>
          </n-dynamic-input>
        </n-form-item>

        <n-form-item label="Dropout率" path="dropoutRate">
          <n-input-number
            v-model:value="formData.dropoutRate"
            :min="0"
            :max="0.9"
            :step="0.1"
            :precision="1"
            placeholder="0.2"
            :disabled="readonly"
          />
        </n-form-item>
      </n-card>

      <!-- 高级配置 -->
      <n-card title="高级配置" size="small" class="config-section">
        <n-form-item label="早停策略">
          <n-switch v-model:value="formData.earlyStopping.enabled" :disabled="readonly" />
        </n-form-item>

        <div v-if="formData.earlyStopping.enabled" class="early-stopping-config">
          <n-grid :cols="2" :x-gap="16">
            <n-grid-item>
              <n-form-item label="监控指标" path="earlyStopping.monitor">
                <n-select
                  v-model:value="formData.earlyStopping.monitor"
                  :options="monitorOptions"
                  :disabled="readonly"
                />
              </n-form-item>
            </n-grid-item>

            <n-grid-item>
              <n-form-item label="耐心值" path="earlyStopping.patience">
                <n-input-number
                  v-model:value="formData.earlyStopping.patience"
                  :min="1"
                  :max="100"
                  :disabled="readonly"
                />
              </n-form-item>
            </n-grid-item>
          </n-grid>
        </div>

        <n-form-item label="学习率调度">
          <n-switch v-model:value="formData.learningRateScheduler.enabled" :disabled="readonly" />
        </n-form-item>

        <div v-if="formData.learningRateScheduler.enabled" class="scheduler-config">
          <n-grid :cols="2" :x-gap="16">
            <n-grid-item>
              <n-form-item label="调度类型" path="learningRateScheduler.type">
                <n-select
                  v-model:value="formData.learningRateScheduler.type"
                  :options="schedulerOptions"
                  :disabled="readonly"
                />
              </n-form-item>
            </n-grid-item>

            <n-grid-item>
              <n-form-item label="衰减因子" path="learningRateScheduler.factor">
                <n-input-number
                  v-model:value="formData.learningRateScheduler.factor"
                  :min="0.1"
                  :max="0.9"
                  :step="0.1"
                  :precision="1"
                  :disabled="readonly"
                />
              </n-form-item>
            </n-grid-item>
          </n-grid>
        </div>
      </n-card>

      <!-- 操作按钮 -->
      <div v-if="!readonly" class="form-actions">
        <n-space>
          <n-button @click="resetForm">重置</n-button>
          <n-button @click="validateForm">验证配置</n-button>
          <n-button type="primary" :loading="submitting" @click="submitForm">
            {{ submitText }}
          </n-button>
        </n-space>
      </div>
    </n-form>
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
const emit = defineEmits(['update:modelValue', 'submit', 'validate', 'reset'])

// 响应式数据
const formRef = ref(null)
const message = useMessage()

// 表单数据
const formData = reactive({
  name: '',
  type: '',
  version: '1.0.0',
  description: '',
  learningRate: 0.001,
  batchSize: 32,
  epochs: 100,
  validationSplit: 0.2,
  optimizer: 'adam',
  lossFunction: 'categorical_crossentropy',
  inputDim: '',
  outputDim: null,
  hiddenLayers: [
    { units: 128, activation: 'relu' },
    { units: 64, activation: 'relu' },
  ],
  dropoutRate: 0.2,
  earlyStopping: {
    enabled: true,
    monitor: 'val_loss',
    patience: 10,
  },
  learningRateScheduler: {
    enabled: false,
    type: 'reduce_on_plateau',
    factor: 0.5,
  },
})

// 选项数据
const modelTypeOptions = [
  { label: '异常检测', value: 'anomaly-detection' },
  { label: '趋势预测', value: 'trend-prediction' },
  { label: '健康评分', value: 'health-scoring' },
  { label: '分类模型', value: 'classification' },
  { label: '回归模型', value: 'regression' },
]

const optimizerOptions = [
  { label: 'Adam', value: 'adam' },
  { label: 'SGD', value: 'sgd' },
  { label: 'RMSprop', value: 'rmsprop' },
  { label: 'AdaGrad', value: 'adagrad' },
]

const lossFunctionOptions = [
  { label: 'Categorical Crossentropy', value: 'categorical_crossentropy' },
  { label: 'Binary Crossentropy', value: 'binary_crossentropy' },
  { label: 'Mean Squared Error', value: 'mse' },
  { label: 'Mean Absolute Error', value: 'mae' },
  { label: 'Huber Loss', value: 'huber' },
]

const activationOptions = [
  { label: 'ReLU', value: 'relu' },
  { label: 'Sigmoid', value: 'sigmoid' },
  { label: 'Tanh', value: 'tanh' },
  { label: 'Softmax', value: 'softmax' },
  { label: 'Linear', value: 'linear' },
]

const monitorOptions = [
  { label: '验证损失', value: 'val_loss' },
  { label: '验证准确率', value: 'val_accuracy' },
  { label: '训练损失', value: 'loss' },
  { label: '训练准确率', value: 'accuracy' },
]

const schedulerOptions = [
  { label: '平台衰减', value: 'reduce_on_plateau' },
  { label: '指数衰减', value: 'exponential_decay' },
  { label: '步长衰减', value: 'step_decay' },
]

// 表单验证规则
const formRules = {
  name: {
    required: true,
    message: '请输入模型名称',
    trigger: 'blur',
  },
  type: {
    required: true,
    message: '请选择模型类型',
    trigger: 'change',
  },
  version: {
    required: true,
    message: '请输入模型版本',
    trigger: 'blur',
  },
  learningRate: {
    required: true,
    type: 'number',
    message: '请输入有效的学习率',
    trigger: 'blur',
  },
  batchSize: {
    required: true,
    type: 'number',
    message: '请输入有效的批次大小',
    trigger: 'blur',
  },
  epochs: {
    required: true,
    type: 'number',
    message: '请输入有效的训练轮数',
    trigger: 'blur',
  },
  outputDim: {
    required: true,
    type: 'number',
    message: '请输入输出维度',
    trigger: 'blur',
  },
}

// 创建隐藏层
const createHiddenLayer = () => {
  return {
    units: 64,
    activation: 'relu',
  }
}

// 处理模型类型变化
const handleTypeChange = (type) => {
  // 根据模型类型调整默认配置
  switch (type) {
    case 'anomaly-detection':
      formData.lossFunction = 'mse'
      formData.outputDim = 1
      break
    case 'trend-prediction':
      formData.lossFunction = 'mse'
      formData.outputDim = 1
      break
    case 'health-scoring':
      formData.lossFunction = 'mse'
      formData.outputDim = 1
      break
    case 'classification':
      formData.lossFunction = 'categorical_crossentropy'
      formData.outputDim = 10
      break
    case 'regression':
      formData.lossFunction = 'mse'
      formData.outputDim = 1
      break
  }
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
  getFormData: () => formData,
})
</script>

<style scoped>
.model-config-form {
  width: 100%;
}

.config-section {
  margin-bottom: 16px;
}

.config-section:last-of-type {
  margin-bottom: 24px;
}

.hidden-layer-item {
  display: flex;
  align-items: center;
  width: 100%;
}

.early-stopping-config,
.scheduler-config {
  margin-top: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
}

.form-actions {
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
  text-align: right;
}

/* 响应式 */
@media (max-width: 768px) {
  .form-actions {
    text-align: center;
  }

  .hidden-layer-item {
    flex-direction: column;
    gap: 8px;
  }

  .hidden-layer-item > * {
    width: 100% !important;
    margin-right: 0 !important;
  }
}
</style>
