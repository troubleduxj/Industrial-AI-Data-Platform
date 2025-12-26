<template>
  <n-modal
    v-model:show="showModal"
    preset="dialog"
    title="新建模型训练"
    :style="{ width: '600px' }"
    :mask-closable="false"
  >
    <n-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-placement="left"
      label-width="100px"
      require-mark-placement="right-hanging"
    >
      <n-form-item label="模型名称" path="name">
        <n-input v-model:value="formData.name" placeholder="请输入模型名称" clearable />
      </n-form-item>

      <n-form-item label="模型描述" path="description">
        <n-input
          v-model:value="formData.description"
          type="textarea"
          placeholder="请输入模型描述"
          :rows="3"
          clearable
        />
      </n-form-item>

      <n-form-item label="模型类型" path="type">
        <n-select
          v-model:value="formData.type"
          placeholder="请选择模型类型"
          :options="typeOptions"
        />
      </n-form-item>

      <n-form-item label="版本号" path="version">
        <n-input v-model:value="formData.version" placeholder="例如: v1.0.0" clearable />
      </n-form-item>

      <n-form-item label="算法" path="algorithm">
        <n-select
          v-model:value="formData.algorithm"
          placeholder="请选择算法"
          :options="algorithmOptions"
          filterable
          tag
        />
      </n-form-item>

      <n-form-item label="框架" path="framework">
        <n-select
          v-model:value="formData.framework"
          placeholder="请选择框架"
          :options="frameworkOptions"
          filterable
          tag
        />
      </n-form-item>

      <n-divider title-placement="left">训练配置</n-divider>

      <n-form-item label="训练数据集" path="training_dataset">
        <n-input 
          v-model:value="formData.training_dataset" 
          placeholder="请输入数据集标识或路径" 
          clearable 
        />
      </n-form-item>

      <n-form-item label="训练参数">
        <n-card size="small" style="width: 100%">
          <template #header>
            <n-space justify="space-between">
              <span>参数配置</span>
              <n-button size="small" @click="addParameter"> 添加参数 </n-button>
            </n-space>
          </template>

          <n-space vertical>
            <div
              v-for="(param, index) in formData.parameters"
              :key="index"
              style="display: flex; gap: 8px; align-items: center"
            >
              <n-input v-model:value="param.key" placeholder="参数名" style="flex: 1" />
              <n-input v-model:value="param.value" placeholder="参数值" style="flex: 1" />
              <n-button size="small" quaternary type="error" @click="removeParameter(index)">
                <template #icon>
                  <n-icon><trash-outline /></n-icon>
                </template>
              </n-button>
            </div>

            <n-empty v-if="formData.parameters.length === 0" description="暂无参数" size="small" />
          </n-space>
        </n-card>
      </n-form-item>
    </n-form>

    <template #action>
      <n-space>
        <n-button @click="handleCancel">取消</n-button>
        <n-button type="primary" :loading="loading" @click="handleSubmit">
          {{ loading ? '提交中...' : '开始训练' }}
        </n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NIcon,
  NCard,
  NSpace,
  NButton,
  NEmpty,
  NDivider,
  useMessage,
} from 'naive-ui'
import { TrashOutline } from '@vicons/ionicons5'
import { modelManagementApi } from '@/api/v2/ai-module'

// Props
const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
})

// Emits
const emit = defineEmits(['update:show', 'success'])

// 响应式数据
const formRef = ref(null)
const loading = ref(false)

// 表单数据
const formData = ref({
  name: '',
  description: '',
  type: null,
  version: '',
  algorithm: '',
  framework: '',
  training_dataset: '',
  parameters: [
    { key: 'epochs', value: '100' },
    { key: 'batch_size', value: '32' },
    { key: 'learning_rate', value: '0.001' }
  ],
})

// 模型类型选项
const typeOptions = [
  { label: '异常检测', value: 'anomaly_detection' },
  { label: '趋势预测', value: 'trend_prediction' },
  { label: '健康评分', value: 'health_scoring' },
  { label: '分类模型', value: 'classification' },
  { label: '回归模型', value: 'regression' },
]

// 算法选项
const algorithmOptions = [
  { label: 'Random Forest (随机森林)', value: 'RandomForest' },
  { label: 'LSTM (长短期记忆网络)', value: 'LSTM' },
  { label: 'Isolation Forest (孤立森林)', value: 'IsolationForest' },
  { label: 'SVM (支持向量机)', value: 'SVM' },
  { label: 'XGBoost', value: 'XGBoost' },
  { label: 'Linear Regression (线性回归)', value: 'LinearRegression' },
  { label: 'K-Means (K-均值聚类)', value: 'KMeans' },
  { label: 'CNN (卷积神经网络)', value: 'CNN' },
  { label: 'Transformer', value: 'Transformer' },
  { label: 'Autoencoder (自编码器)', value: 'Autoencoder' },
]

// 框架选项
const frameworkOptions = [
  { label: 'Scikit-learn', value: 'Scikit-learn' },
  { label: 'PyTorch', value: 'PyTorch' },
  { label: 'TensorFlow', value: 'TensorFlow' },
  { label: 'Keras', value: 'Keras' },
  { label: 'XGBoost', value: 'XGBoost' },
  { label: 'LightGBM', value: 'LightGBM' },
  { label: 'Prophet', value: 'Prophet' },
]

// 表单验证规则
const rules = {
  name: {
    required: true,
    message: '请输入模型名称',
    trigger: ['input', 'blur'],
  },
  description: {
    required: true,
    message: '请输入模型描述',
    trigger: ['input', 'blur'],
  },
  type: {
    required: true,
    message: '请选择模型类型',
    trigger: ['change', 'blur'],
  },
  version: {
    required: true,
    message: '请输入版本号',
    trigger: ['input', 'blur'],
  },
  algorithm: {
    required: true,
    message: '请输入算法名称',
    trigger: ['input', 'blur'],
  },
  framework: {
    required: true,
    message: '请输入框架名称',
    trigger: ['input', 'blur'],
  },
  training_dataset: {
    required: true,
    message: '请输入训练数据集',
    trigger: ['input', 'blur'],
  },
}

// 计算属性
const showModal = computed({
  get: () => props.show,
  set: (value) => emit('update:show', value),
})

// 消息提示
const message = useMessage()

// 添加参数
const addParameter = () => {
  formData.value.parameters.push({
    key: '',
    value: '',
  })
}

// 移除参数
const removeParameter = (index) => {
  formData.value.parameters.splice(index, 1)
}

// 重置表单
const resetForm = () => {
  formData.value = {
    name: '',
    description: '',
    type: null,
    version: '',
    algorithm: '',
    framework: '',
    training_dataset: '',
    parameters: [
      { key: 'epochs', value: '100' },
      { key: 'batch_size', value: '32' },
      { key: 'learning_rate', value: '0.001' }
    ],
  }
  if (formRef.value) {
    formRef.value.restoreValidation()
  }
}

// 取消操作
const handleCancel = () => {
  resetForm()
  showModal.value = false
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true

    // 1. 创建模型
    const createData = {
      model_name: formData.value.name,
      model_version: formData.value.version,
      description: formData.value.description,
      model_type: formData.value.type,
      algorithm: formData.value.algorithm,
      framework: formData.value.framework,
      training_dataset: formData.value.training_dataset,
      training_parameters: formData.value.parameters.reduce((acc, curr) => {
        if (curr.key) acc[curr.key] = curr.value
        return acc
      }, {})
    }

    const createRes = await modelManagementApi.create(createData)
    const modelId = createRes.data.id

    // 2. 触发训练
    const trainData = {
      training_dataset: formData.value.training_dataset,
      training_parameters: createData.training_parameters
    }
    
    await modelManagementApi.train(modelId, trainData)

    message.success('模型创建成功，开始后台训练')
    emit('success')
    resetForm()
    showModal.value = false
  } catch (error) {
    console.error(error)
    message.error('操作失败: ' + (error.response?.data?.message || error.message))
  } finally {
    loading.value = false
  }
}
</script>
