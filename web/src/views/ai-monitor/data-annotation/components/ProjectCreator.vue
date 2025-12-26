<template>
  <n-modal
    v-model:show="showModal"
    preset="card"
    title="创建标注项目"
    style="width: 600px"
    :mask-closable="false"
  >
    <n-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-placement="left"
      label-width="100px"
    >
      <n-form-item label="项目名称" path="name">
        <n-input v-model:value="formData.name" placeholder="请输入项目名称" />
      </n-form-item>

      <n-form-item label="项目描述" path="description">
        <n-input
          v-model:value="formData.description"
          type="textarea"
          placeholder="请输入项目描述"
          :rows="3"
        />
      </n-form-item>

      <n-form-item label="项目类型" path="type">
        <n-select
          v-model:value="formData.type"
          :options="projectTypeOptions"
          placeholder="选择项目类型"
          @update:value="onTypeChange"
        />
      </n-form-item>

      <!-- 分类项目配置 -->
      <template v-if="formData.type === 'classification'">
        <n-form-item label="类别标签" path="labels">
          <n-dynamic-tags v-model:value="formData.labels" placeholder="添加类别标签" />
        </n-form-item>
      </template>

      <!-- 检测项目配置 -->
      <template v-if="formData.type === 'detection'">
        <n-form-item label="目标类别" path="labels">
          <n-dynamic-tags v-model:value="formData.labels" placeholder="添加目标类别" />
        </n-form-item>

        <n-form-item label="标注格式">
          <n-radio-group v-model:value="formData.annotationFormat">
            <n-radio value="bbox">边界框</n-radio>
            <n-radio value="polygon">多边形</n-radio>
          </n-radio-group>
        </n-form-item>
      </template>

      <!-- 分割项目配置 -->
      <template v-if="formData.type === 'segmentation'">
        <n-form-item label="分割类别" path="labels">
          <n-dynamic-tags v-model:value="formData.labels" placeholder="添加分割类别" />
        </n-form-item>

        <n-form-item label="分割类型">
          <n-radio-group v-model:value="formData.segmentationType">
            <n-radio value="semantic">语义分割</n-radio>
            <n-radio value="instance">实例分割</n-radio>
          </n-radio-group>
        </n-form-item>
      </template>

      <!-- 回归项目配置 -->
      <template v-if="formData.type === 'regression'">
        <n-form-item label="目标变量" path="targetVariable">
          <n-input v-model:value="formData.targetVariable" placeholder="请输入目标变量名称" />
        </n-form-item>

        <n-form-item label="数值范围">
          <n-space>
            <n-input-number
              v-model:value="formData.valueRange.min"
              placeholder="最小值"
              style="width: 120px"
            />
            <n-text>-</n-text>
            <n-input-number
              v-model:value="formData.valueRange.max"
              placeholder="最大值"
              style="width: 120px"
            />
          </n-space>
        </n-form-item>
      </template>

      <n-form-item label="数据格式">
        <n-checkbox-group v-model:value="formData.dataFormats">
          <n-space>
            <n-checkbox value="image">图像</n-checkbox>
            <n-checkbox value="text">文本</n-checkbox>
            <n-checkbox value="audio">音频</n-checkbox>
            <n-checkbox value="video">视频</n-checkbox>
          </n-space>
        </n-checkbox-group>
      </n-form-item>

      <n-form-item label="质量要求">
        <n-slider
          v-model:value="formData.qualityThreshold"
          :min="50"
          :max="100"
          :step="5"
          :marks="{ 60: '60%', 80: '80%', 95: '95%' }"
        />
      </n-form-item>

      <n-form-item label="标注指南">
        <n-input
          v-model:value="formData.guidelines"
          type="textarea"
          placeholder="请输入标注指南和注意事项"
          :rows="4"
        />
      </n-form-item>
    </n-form>

    <template #footer>
      <n-space justify="end">
        <n-button @click="handleCancel">取消</n-button>
        <n-button type="primary" :loading="submitting" @click="handleSubmit"> 创建项目 </n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import {
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NDynamicTags,
  NRadioGroup,
  NRadio,
  NInputNumber,
  NCheckboxGroup,
  NCheckbox,
  NSlider,
  NButton,
  NSpace,
  NText,
  useMessage,
} from 'naive-ui'

// Message
const message = useMessage()

// Props
const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
})

// Emits
const emit = defineEmits(['update:show', 'project-created'])

// Modal显示状态
const showModal = ref(props.show)
watch(
  () => props.show,
  (val) => {
    showModal.value = val
  }
)
watch(showModal, (val) => {
  emit('update:show', val)
})

// 表单引用
const formRef = ref(null)

// 表单数据
const formData = reactive({
  name: '',
  description: '',
  type: 'classification',
  labels: [],
  annotationFormat: 'bbox',
  segmentationType: 'semantic',
  targetVariable: '',
  valueRange: {
    min: 0,
    max: 100,
  },
  dataFormats: ['image'],
  qualityThreshold: 80,
  guidelines: '',
})

// 项目类型选项
const projectTypeOptions = [
  { label: '图像分类', value: 'classification' },
  { label: '目标检测', value: 'detection' },
  { label: '图像分割', value: 'segmentation' },
  { label: '数值回归', value: 'regression' },
]

// 表单验证规则
const rules = {
  name: {
    required: true,
    message: '请输入项目名称',
    trigger: 'blur',
  },
  description: {
    required: true,
    message: '请输入项目描述',
    trigger: 'blur',
  },
  type: {
    required: true,
    message: '请选择项目类型',
    trigger: 'change',
  },
  labels: {
    type: 'array',
    min: 1,
    message: '请至少添加一个标签',
    trigger: 'change',
  },
  targetVariable: {
    required: true,
    message: '请输入目标变量名称',
    trigger: 'blur',
  },
}

// 提交状态
const submitting = ref(false)

// 项目类型变化处理
const onTypeChange = (type) => {
  // 重置相关字段
  formData.labels = []
  formData.annotationFormat = 'bbox'
  formData.segmentationType = 'semantic'
  formData.targetVariable = ''

  // 根据类型设置默认标签
  if (type === 'classification') {
    formData.labels = ['类别1', '类别2']
  } else if (type === 'detection') {
    formData.labels = ['目标1', '目标2']
  } else if (type === 'segmentation') {
    formData.labels = ['前景', '背景']
  }
}

// 处理取消
const handleCancel = () => {
  showModal.value = false
  resetForm()
}

// 处理提交
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()

    submitting.value = true

    // 模拟创建项目
    await new Promise((resolve) => setTimeout(resolve, 1000))

    const projectData = {
      id: Date.now(),
      ...formData,
      createdAt: new Date().toISOString(),
      status: 'active',
      progress: 0,
    }

    emit('project-created', projectData)
    message.success('项目创建成功')

    showModal.value = false
    resetForm()
  } catch (error) {
    message.error('请检查表单输入')
  } finally {
    submitting.value = false
  }
}

// 重置表单
const resetForm = () => {
  Object.assign(formData, {
    name: '',
    description: '',
    type: 'classification',
    labels: [],
    annotationFormat: 'bbox',
    segmentationType: 'semantic',
    targetVariable: '',
    valueRange: {
      min: 0,
      max: 100,
    },
    dataFormats: ['image'],
    qualityThreshold: 80,
    guidelines: '',
  })
}
</script>

<style scoped>
/* 组件样式 */
</style>
