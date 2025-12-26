<template>
  <div class="annotation-form">
    <n-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      :label-placement="labelPlacement"
      :label-width="labelWidth"
      :size="size"
    >
      <!-- 基础信息 -->
      <n-card title="基础信息" size="small" class="config-section">
        <n-form-item label="标注名称" path="name">
          <n-input
            v-model:value="formData.name"
            placeholder="请输入标注名称"
            :disabled="readonly"
          />
        </n-form-item>

        <n-form-item label="标注类型" path="type">
          <n-select
            v-model:value="formData.type"
            :options="annotationTypeOptions"
            placeholder="请选择标注类型"
            :disabled="readonly"
            @update:value="handleTypeChange"
          />
        </n-form-item>

        <n-form-item label="数据源" path="dataSource">
          <n-select
            v-model:value="formData.dataSource"
            :options="dataSourceOptions"
            placeholder="请选择数据源"
            :disabled="readonly"
            @update:value="handleDataSourceChange"
          />
        </n-form-item>

        <n-form-item label="描述" path="description">
          <n-input
            v-model:value="formData.description"
            type="textarea"
            placeholder="请输入标注描述"
            :autosize="{ minRows: 2, maxRows: 4 }"
            :disabled="readonly"
          />
        </n-form-item>
      </n-card>

      <!-- 分类标注配置 -->
      <n-card
        v-if="formData.type === 'classification'"
        title="分类标注配置"
        size="small"
        class="config-section"
      >
        <n-form-item label="分类方式" path="classification.mode">
          <n-radio-group v-model:value="formData.classification.mode" :disabled="readonly">
            <n-space>
              <n-radio value="single">单分类</n-radio>
              <n-radio value="multi">多分类</n-radio>
            </n-space>
          </n-radio-group>
        </n-form-item>

        <n-form-item label="分类标签">
          <n-dynamic-input
            v-model:value="formData.classification.labels"
            :on-create="createClassificationLabel"
            :disabled="readonly"
          >
            <template #default="{ value, index }">
              <div class="label-item">
                <n-input
                  v-model:value="value.name"
                  placeholder="标签名称"
                  style="width: 150px; margin-right: 8px"
                />
                <n-input
                  v-model:value="value.description"
                  placeholder="标签描述"
                  style="width: 200px; margin-right: 8px"
                />
                <n-color-picker
                  v-model:value="value.color"
                  :show-alpha="false"
                  style="width: 60px"
                />
              </div>
            </template>
          </n-dynamic-input>
        </n-form-item>

        <n-form-item label="默认标签" path="classification.defaultLabel">
          <n-select
            v-model:value="formData.classification.defaultLabel"
            :options="classificationLabelOptions"
            placeholder="请选择默认标签"
            :disabled="readonly"
          />
        </n-form-item>
      </n-card>

      <!-- 目标检测配置 -->
      <n-card
        v-if="formData.type === 'detection'"
        title="目标检测配置"
        size="small"
        class="config-section"
      >
        <n-form-item label="检测类别">
          <n-dynamic-input
            v-model:value="formData.detection.classes"
            :on-create="createDetectionClass"
            :disabled="readonly"
          >
            <template #default="{ value, index }">
              <div class="class-item">
                <n-input
                  v-model:value="value.name"
                  placeholder="类别名称"
                  style="width: 120px; margin-right: 8px"
                />
                <n-input
                  v-model:value="value.description"
                  placeholder="类别描述"
                  style="width: 180px; margin-right: 8px"
                />
                <n-color-picker
                  v-model:value="value.color"
                  :show-alpha="false"
                  style="width: 60px; margin-right: 8px"
                />
                <n-input-number
                  v-model:value="value.minSize"
                  placeholder="最小尺寸"
                  :min="1"
                  style="width: 100px"
                />
              </div>
            </template>
          </n-dynamic-input>
        </n-form-item>

        <n-form-item label="标注工具" path="detection.tools">
          <n-checkbox-group v-model:value="formData.detection.tools" :disabled="readonly">
            <n-space>
              <n-checkbox value="rectangle">矩形框</n-checkbox>
              <n-checkbox value="polygon">多边形</n-checkbox>
              <n-checkbox value="circle">圆形</n-checkbox>
              <n-checkbox value="point">点标注</n-checkbox>
            </n-space>
          </n-checkbox-group>
        </n-form-item>

        <n-form-item label="最小置信度" path="detection.minConfidence">
          <n-slider
            v-model:value="formData.detection.minConfidence"
            :min="0"
            :max="1"
            :step="0.01"
            :marks="{ 0: '0%', 0.5: '50%', 1: '100%' }"
            :disabled="readonly"
          />
        </n-form-item>
      </n-card>

      <!-- 时序标注配置 -->
      <n-card
        v-if="formData.type === 'timeseries'"
        title="时序标注配置"
        size="small"
        class="config-section"
      >
        <n-form-item label="标注粒度" path="timeseries.granularity">
          <n-select
            v-model:value="formData.timeseries.granularity"
            :options="granularityOptions"
            :disabled="readonly"
          />
        </n-form-item>

        <n-form-item label="事件类型">
          <n-dynamic-input
            v-model:value="formData.timeseries.eventTypes"
            :on-create="createEventType"
            :disabled="readonly"
          >
            <template #default="{ value, index }">
              <div class="event-type-item">
                <n-input
                  v-model:value="value.name"
                  placeholder="事件名称"
                  style="width: 120px; margin-right: 8px"
                />
                <n-select
                  v-model:value="value.severity"
                  :options="severityOptions"
                  placeholder="严重程度"
                  style="width: 100px; margin-right: 8px"
                />
                <n-color-picker
                  v-model:value="value.color"
                  :show-alpha="false"
                  style="width: 60px"
                />
              </div>
            </template>
          </n-dynamic-input>
        </n-form-item>

        <n-form-item label="时间窗口" path="timeseries.timeWindow">
          <n-input-number
            v-model:value="formData.timeseries.timeWindow"
            :min="1"
            placeholder="时间窗口大小"
            :disabled="readonly"
            style="width: 100%"
          >
            <template #suffix>
              <span class="time-unit">{{ timeUnit }}</span>
            </template>
          </n-input-number>
        </n-form-item>

        <n-form-item label="重叠允许" path="timeseries.allowOverlap">
          <n-switch v-model:value="formData.timeseries.allowOverlap" :disabled="readonly" />
        </n-form-item>
      </n-card>

      <!-- 标注规则 -->
      <n-card title="标注规则" size="small" class="config-section">
        <n-form-item label="质量控制">
          <n-switch v-model:value="formData.rules.qualityControl.enabled" :disabled="readonly" />
        </n-form-item>

        <div v-if="formData.rules.qualityControl.enabled" class="quality-control-config">
          <n-form-item label="最小标注数" path="rules.qualityControl.minAnnotations">
            <n-input-number
              v-model:value="formData.rules.qualityControl.minAnnotations"
              :min="1"
              :disabled="readonly"
            />
          </n-form-item>

          <n-form-item label="一致性检查" path="rules.qualityControl.consistencyCheck">
            <n-switch
              v-model:value="formData.rules.qualityControl.consistencyCheck"
              :disabled="readonly"
            />
          </n-form-item>

          <n-form-item label="交叉验证" path="rules.qualityControl.crossValidation">
            <n-switch
              v-model:value="formData.rules.qualityControl.crossValidation"
              :disabled="readonly"
            />
          </n-form-item>
        </div>

        <n-form-item label="自动标注">
          <n-switch v-model:value="formData.rules.autoAnnotation.enabled" :disabled="readonly" />
        </n-form-item>

        <div v-if="formData.rules.autoAnnotation.enabled" class="auto-annotation-config">
          <n-form-item label="预训练模型" path="rules.autoAnnotation.model">
            <n-select
              v-model:value="formData.rules.autoAnnotation.model"
              :options="pretrainedModelOptions"
              :disabled="readonly"
            />
          </n-form-item>

          <n-form-item label="置信度阈值" path="rules.autoAnnotation.threshold">
            <n-slider
              v-model:value="formData.rules.autoAnnotation.threshold"
              :min="0"
              :max="1"
              :step="0.01"
              :marks="{ 0: '0%', 0.5: '50%', 1: '100%' }"
              :disabled="readonly"
            />
          </n-form-item>

          <n-form-item label="人工审核" path="rules.autoAnnotation.humanReview">
            <n-switch
              v-model:value="formData.rules.autoAnnotation.humanReview"
              :disabled="readonly"
            />
          </n-form-item>
        </div>
      </n-card>

      <!-- 导出设置 -->
      <n-card title="导出设置" size="small" class="config-section">
        <n-form-item label="导出格式" path="export.formats">
          <n-checkbox-group v-model:value="formData.export.formats" :disabled="readonly">
            <n-space>
              <n-checkbox value="json">JSON</n-checkbox>
              <n-checkbox value="xml">XML</n-checkbox>
              <n-checkbox value="csv">CSV</n-checkbox>
              <n-checkbox value="coco">COCO</n-checkbox>
              <n-checkbox value="yolo">YOLO</n-checkbox>
            </n-space>
          </n-checkbox-group>
        </n-form-item>

        <n-form-item label="包含元数据" path="export.includeMetadata">
          <n-switch v-model:value="formData.export.includeMetadata" :disabled="readonly" />
        </n-form-item>

        <n-form-item label="压缩输出" path="export.compress">
          <n-switch v-model:value="formData.export.compress" :disabled="readonly" />
        </n-form-item>
      </n-card>

      <!-- 操作按钮 -->
      <div v-if="!readonly" class="form-actions">
        <n-space>
          <n-button @click="resetForm">重置</n-button>
          <n-button @click="validateForm">验证配置</n-button>
          <n-button @click="previewAnnotation">预览标注</n-button>
          <n-button type="primary" :loading="submitting" @click="submitForm">
            {{ submitText }}
          </n-button>
        </n-space>
      </div>
    </n-form>

    <!-- 预览模态框 -->
    <n-modal v-model:show="showPreview" preset="card" title="标注配置预览" style="width: 700px">
      <div class="annotation-preview">
        <n-alert type="info" style="margin-bottom: 16px"> 以下是当前标注配置的预览效果 </n-alert>

        <n-descriptions :column="2" bordered>
          <n-descriptions-item label="标注类型">
            {{ getAnnotationTypeLabel(formData.type) }}
          </n-descriptions-item>
          <n-descriptions-item label="数据源">
            {{ getDataSourceLabel(formData.dataSource) }}
          </n-descriptions-item>

          <!-- 分类标注预览 -->
          <template v-if="formData.type === 'classification'">
            <n-descriptions-item label="分类方式">
              {{ formData.classification.mode === 'single' ? '单分类' : '多分类' }}
            </n-descriptions-item>
            <n-descriptions-item label="标签数量">
              {{ formData.classification.labels.length }}
            </n-descriptions-item>
            <n-descriptions-item label="分类标签" :span="2">
              <n-space>
                <n-tag
                  v-for="label in formData.classification.labels"
                  :key="label.name"
                  :color="{ color: label.color, textColor: '#fff' }"
                  size="small"
                >
                  {{ label.name }}
                </n-tag>
              </n-space>
            </n-descriptions-item>
          </template>

          <!-- 目标检测预览 -->
          <template v-if="formData.type === 'detection'">
            <n-descriptions-item label="检测类别数">
              {{ formData.detection.classes.length }}
            </n-descriptions-item>
            <n-descriptions-item label="标注工具">
              {{ formData.detection.tools.join(', ') }}
            </n-descriptions-item>
            <n-descriptions-item label="检测类别" :span="2">
              <n-space>
                <n-tag
                  v-for="cls in formData.detection.classes"
                  :key="cls.name"
                  :color="{ color: cls.color, textColor: '#fff' }"
                  size="small"
                >
                  {{ cls.name }}
                </n-tag>
              </n-space>
            </n-descriptions-item>
          </template>

          <!-- 时序标注预览 -->
          <template v-if="formData.type === 'timeseries'">
            <n-descriptions-item label="标注粒度">
              {{ getGranularityLabel(formData.timeseries.granularity) }}
            </n-descriptions-item>
            <n-descriptions-item label="事件类型数">
              {{ formData.timeseries.eventTypes.length }}
            </n-descriptions-item>
            <n-descriptions-item label="事件类型" :span="2">
              <n-space>
                <n-tag
                  v-for="event in formData.timeseries.eventTypes"
                  :key="event.name"
                  :color="{ color: event.color, textColor: '#fff' }"
                  size="small"
                >
                  {{ event.name }}
                </n-tag>
              </n-space>
            </n-descriptions-item>
          </template>

          <n-descriptions-item label="导出格式">
            {{ formData.export.formats.join(', ') }}
          </n-descriptions-item>
          <n-descriptions-item label="质量控制">
            {{ formData.rules.qualityControl.enabled ? '启用' : '禁用' }}
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
  type: 'classification',
  dataSource: '',
  description: '',
  classification: {
    mode: 'single',
    labels: [
      { name: '正常', description: '设备正常运行', color: '#52c41a' },
      { name: '异常', description: '设备异常状态', color: '#ff4d4f' },
    ],
    defaultLabel: '',
  },
  detection: {
    classes: [{ name: '缺陷', description: '设备缺陷', color: '#ff4d4f', minSize: 10 }],
    tools: ['rectangle'],
    minConfidence: 0.5,
  },
  timeseries: {
    granularity: 'minute',
    eventTypes: [
      { name: '故障', severity: 'high', color: '#ff4d4f' },
      { name: '维护', severity: 'medium', color: '#faad14' },
    ],
    timeWindow: 60,
    allowOverlap: false,
  },
  rules: {
    qualityControl: {
      enabled: true,
      minAnnotations: 1,
      consistencyCheck: true,
      crossValidation: false,
    },
    autoAnnotation: {
      enabled: false,
      model: '',
      threshold: 0.8,
      humanReview: true,
    },
  },
  export: {
    formats: ['json'],
    includeMetadata: true,
    compress: false,
  },
})

// 选项数据
const annotationTypeOptions = [
  { label: '分类标注', value: 'classification' },
  { label: '目标检测', value: 'detection' },
  { label: '时序标注', value: 'timeseries' },
]

const dataSourceOptions = [
  { label: '传感器数据', value: 'sensor' },
  { label: '图像数据', value: 'image' },
  { label: '视频数据', value: 'video' },
  { label: '音频数据', value: 'audio' },
  { label: '文本数据', value: 'text' },
]

const granularityOptions = [
  { label: '秒', value: 'second' },
  { label: '分钟', value: 'minute' },
  { label: '小时', value: 'hour' },
  { label: '天', value: 'day' },
]

const severityOptions = [
  { label: '低', value: 'low' },
  { label: '中', value: 'medium' },
  { label: '高', value: 'high' },
  { label: '紧急', value: 'critical' },
]

const pretrainedModelOptions = [
  { label: 'ResNet-50', value: 'resnet50' },
  { label: 'YOLO v5', value: 'yolov5' },
  { label: 'BERT', value: 'bert' },
  { label: '自定义模型', value: 'custom' },
]

// 计算属性
const classificationLabelOptions = computed(() => {
  return formData.classification.labels.map((label) => ({
    label: label.name,
    value: label.name,
  }))
})

const timeUnit = computed(() => {
  const unitMap = {
    second: '秒',
    minute: '分钟',
    hour: '小时',
    day: '天',
  }
  return unitMap[formData.timeseries.granularity] || '分钟'
})

// 表单验证规则
const formRules = {
  name: {
    required: true,
    message: '请输入标注名称',
    trigger: 'blur',
  },
  type: {
    required: true,
    message: '请选择标注类型',
    trigger: 'change',
  },
  dataSource: {
    required: true,
    message: '请选择数据源',
    trigger: 'change',
  },
}

// 创建方法
const createClassificationLabel = () => {
  return {
    name: '',
    description: '',
    color: '#1890ff',
  }
}

const createDetectionClass = () => {
  return {
    name: '',
    description: '',
    color: '#1890ff',
    minSize: 10,
  }
}

const createEventType = () => {
  return {
    name: '',
    severity: 'medium',
    color: '#1890ff',
  }
}

// 处理类型变化
const handleTypeChange = (type) => {
  // 根据标注类型调整默认配置
  switch (type) {
    case 'classification':
      formData.export.formats = ['json', 'csv']
      break
    case 'detection':
      formData.export.formats = ['json', 'coco', 'yolo']
      break
    case 'timeseries':
      formData.export.formats = ['json', 'csv']
      break
  }
}

// 处理数据源变化
const handleDataSourceChange = (dataSource) => {
  // 根据数据源调整配置
  switch (dataSource) {
    case 'image':
    case 'video':
      if (formData.type === 'detection') {
        formData.detection.tools = ['rectangle', 'polygon']
      }
      break
    case 'sensor':
      if (formData.type === 'timeseries') {
        formData.timeseries.granularity = 'minute'
      }
      break
  }
}

// 获取标签方法
const getAnnotationTypeLabel = (type) => {
  return annotationTypeOptions.find((option) => option.value === type)?.label || type
}

const getDataSourceLabel = (dataSource) => {
  return dataSourceOptions.find((option) => option.value === dataSource)?.label || dataSource
}

const getGranularityLabel = (granularity) => {
  return granularityOptions.find((option) => option.value === granularity)?.label || granularity
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

// 预览标注
const previewAnnotation = () => {
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
  preview: previewAnnotation,
  getFormData: () => formData,
})
</script>

<style scoped>
.annotation-form {
  width: 100%;
}

.config-section {
  margin-bottom: 16px;
}

.config-section:last-of-type {
  margin-bottom: 24px;
}

.label-item,
.class-item,
.event-type-item {
  display: flex;
  align-items: center;
  width: 100%;
}

.quality-control-config,
.auto-annotation-config {
  margin-top: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
}

.time-unit {
  color: #999;
  font-size: 12px;
}

.form-actions {
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
  text-align: right;
}

.annotation-preview {
  padding: 16px 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .form-actions {
    text-align: center;
  }

  .label-item,
  .class-item,
  .event-type-item {
    flex-direction: column;
    gap: 8px;
  }

  .label-item > *,
  .class-item > *,
  .event-type-item > * {
    width: 100% !important;
    margin-right: 0 !important;
  }
}
</style>
