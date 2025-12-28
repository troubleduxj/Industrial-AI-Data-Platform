<!-- 动态表单组件 - 基于元数据驱动的表单渲染 -->

<template>
  <div class="dynamic-form-container">
    <!-- 表单标题 -->
    <div class="form-header" v-if="showHeader">
      <h3>{{ formTitle }}</h3>
      <p class="form-description" v-if="formDescription">{{ formDescription }}</p>
    </div>

    <!-- 动态表单 -->
    <n-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      :label-placement="labelPlacement"
      :label-width="labelWidth"
      :size="size"
    >
      <!-- 按分组渲染字段 -->
      <template v-for="group in fieldGroups" :key="group.name">
        <!-- 分组标题 -->
        <n-divider v-if="group.name !== 'default' && group.fields.length > 0">
          <n-icon :component="getGroupIcon(group.name)" />
          {{ getGroupTitle(group.name) }}
        </n-divider>

        <!-- 分组内的字段 -->
        <div class="field-group" :class="`group-${group.name}`">
          <template v-for="field in group.fields" :key="field.code">
            <!-- 根据字段类型渲染不同的表单项 -->
            <n-form-item
              :label="field.name"
              :path="field.code"
              :show-require-mark="field.is_required"
            >
              <!-- 数值输入 -->
              <n-input-number
                v-if="field.data_type === 'float' || field.data_type === 'int'"
                v-model:value="formData[field.code]"
                :placeholder="`请输入${field.name}`"
                :precision="field.data_type === 'float' ? 2 : 0"
                :min="field.value_range?.min"
                :max="field.value_range?.max"
                :step="field.data_type === 'float' ? 0.01 : 1"
                style="width: 100%"
              >
                <template #suffix v-if="field.unit">
                  <span class="input-unit">{{ field.unit }}</span>
                </template>
              </n-input-number>

              <!-- 文本输入 -->
              <n-input
                v-else-if="field.data_type === 'string'"
                v-model:value="formData[field.code]"
                :placeholder="`请输入${field.name}`"
                :maxlength="field.validation_rules?.maxLength || 255"
                :show-count="field.validation_rules?.showCount"
                clearable
              />

              <!-- 布尔值开关 -->
              <n-switch
                v-else-if="field.data_type === 'bool'"
                v-model:value="formData[field.code]"
                :checked-value="true"
                :unchecked-value="false"
              >
                <template #checked>开启</template>
                <template #unchecked>关闭</template>
              </n-switch>

              <!-- 日期选择 -->
              <n-date-picker
                v-else-if="field.data_type === 'date'"
                v-model:value="formData[field.code]"
                type="date"
                :placeholder="`请选择${field.name}`"
                style="width: 100%"
              />

              <!-- 日期时间选择 -->
              <n-date-picker
                v-else-if="field.data_type === 'datetime'"
                v-model:value="formData[field.code]"
                type="datetime"
                :placeholder="`请选择${field.name}`"
                style="width: 100%"
              />

              <!-- 选择器 (基于枚举值) -->
              <n-select
                v-else-if="field.validation_rules?.enum"
                v-model:value="formData[field.code]"
                :options="getEnumOptions(field.validation_rules.enum)"
                :placeholder="`请选择${field.name}`"
                clearable
              />

              <!-- JSON编辑器 -->
              <json-editor
                v-else-if="field.data_type === 'json'"
                v-model:value="formData[field.code]"
                :height="200"
              />

              <!-- 默认文本输入 -->
              <n-input
                v-else
                v-model:value="formData[field.code]"
                :placeholder="`请输入${field.name}`"
                clearable
              />

              <!-- 字段说明 -->
              <template #feedback v-if="field.description">
                <span class="field-description">{{ field.description }}</span>
              </template>
            </n-form-item>
          </template>
        </div>
      </template>

      <!-- 表单操作按钮 -->
      <n-form-item v-if="showActions">
        <n-space>
          <n-button
            type="primary"
            :loading="loading"
            @click="handleSubmit"
          >
            {{ submitText }}
          </n-button>
          <n-button @click="handleReset" v-if="showReset">
            重置
          </n-button>
          <n-button @click="handleCancel" v-if="showCancel">
            取消
          </n-button>
        </n-space>
      </n-form-item>
    </n-form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { NForm, NFormItem, NInput, NInputNumber, NSelect, NSwitch, NDatePicker, NButton, NSpace, NDivider, NIcon, useMessage } from 'naive-ui'
import { 
  SettingsOutline, 
  ThermometerOutline, 
  FlashOutline, 
  SpeedometerOutline,
  ResizeOutline,
  BarChartOutline,
  EllipsisHorizontalOutline 
} from '@vicons/ionicons5'
import JsonEditor from './JsonEditor.vue'

// 类型定义
interface SignalDefinition {
  code: string
  name: string
  data_type: string
  unit?: string
  description?: string
  is_required?: boolean
  value_range?: {
    min?: number
    max?: number
  }
  validation_rules?: {
    maxLength?: number
    showCount?: boolean
    enum?: string[]
  }
  display_config?: {
    group?: string
    order?: number
  }
}

interface FieldGroup {
  name: string
  title: string
  icon: any
  fields: SignalDefinition[]
}

// Props
interface Props {
  // 信号定义列表
  signalDefinitions: SignalDefinition[]
  // 初始数据
  initialData?: Record<string, any>
  // 表单配置
  formTitle?: string
  formDescription?: string
  showHeader?: boolean
  showActions?: boolean
  showReset?: boolean
  showCancel?: boolean
  submitText?: string
  labelPlacement?: 'left' | 'top'
  labelWidth?: string | number
  size?: 'small' | 'medium' | 'large'
  // 加载状态
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showHeader: true,
  showActions: true,
  showReset: true,
  showCancel: false,
  submitText: '提交',
  labelPlacement: 'top',
  labelWidth: 'auto',
  size: 'medium',
  loading: false
})

// Emits
const emit = defineEmits<{
  submit: [data: Record<string, any>]
  reset: []
  cancel: []
}>()

// 响应式数据
const formRef = ref()
const formData = ref<Record<string, any>>({})
const message = useMessage()

// 计算属性 - 字段分组
const fieldGroups = computed<FieldGroup[]>(() => {
  const groups: Record<string, SignalDefinition[]> = {
    core: [],
    temperature: [],
    power: [],
    speed: [],
    dimension: [],
    pressure: [],
    other: [],
    default: []
  }

  // 按分组归类字段
  props.signalDefinitions.forEach(field => {
    const groupName = field.display_config?.group || 'default'
    if (groups[groupName]) {
      groups[groupName].push(field)
    } else {
      groups.default.push(field)
    }
  })

  // 每个分组内按order排序
  Object.keys(groups).forEach(groupName => {
    groups[groupName].sort((a, b) => {
      const orderA = a.display_config?.order || 999
      const orderB = b.display_config?.order || 999
      return orderA - orderB
    })
  })

  // 转换为FieldGroup数组
  return Object.entries(groups)
    .filter(([_, fields]) => fields.length > 0)
    .map(([name, fields]) => ({
      name,
      title: getGroupTitle(name),
      icon: getGroupIcon(name),
      fields
    }))
})

// 计算属性 - 表单验证规则
const formRules = computed(() => {
  const rules: Record<string, any[]> = {}

  props.signalDefinitions.forEach(field => {
    const fieldRules: any[] = []

    // 必填验证
    if (field.is_required) {
      fieldRules.push({
        required: true,
        message: `请输入${field.name}`,
        trigger: ['blur', 'input']
      })
    }

    // 数值范围验证
    if (field.value_range && (field.data_type === 'float' || field.data_type === 'int')) {
      if (field.value_range.min !== undefined) {
        fieldRules.push({
          type: 'number',
          min: field.value_range.min,
          message: `${field.name}不能小于${field.value_range.min}`,
          trigger: ['blur', 'input']
        })
      }
      if (field.value_range.max !== undefined) {
        fieldRules.push({
          type: 'number',
          max: field.value_range.max,
          message: `${field.name}不能大于${field.value_range.max}`,
          trigger: ['blur', 'input']
        })
      }
    }

    // 字符串长度验证
    if (field.validation_rules?.maxLength && field.data_type === 'string') {
      fieldRules.push({
        max: field.validation_rules.maxLength,
        message: `${field.name}长度不能超过${field.validation_rules.maxLength}个字符`,
        trigger: ['blur', 'input']
      })
    }

    if (fieldRules.length > 0) {
      rules[field.code] = fieldRules
    }
  })

  return rules
})

// 方法 - 获取分组标题
function getGroupTitle(groupName: string): string {
  const titles: Record<string, string> = {
    core: '核心参数',
    temperature: '温度相关',
    power: '功率相关',
    speed: '速度相关',
    dimension: '尺寸相关',
    pressure: '压力相关',
    other: '其他参数',
    default: '基本信息'
  }
  return titles[groupName] || groupName
}

// 方法 - 获取分组图标
function getGroupIcon(groupName: string) {
  const icons: Record<string, any> = {
    core: SettingsOutline,
    temperature: ThermometerOutline,
    power: FlashOutline,
    speed: SpeedometerOutline,
    dimension: ResizeOutline,
    pressure: BarChartOutline,
    other: EllipsisHorizontalOutline,
    default: SettingsOutline
  }
  return icons[groupName] || SettingsOutline
}

// 方法 - 获取枚举选项
function getEnumOptions(enumValues: string[]) {
  return enumValues.map(value => ({
    label: value,
    value: value
  }))
}

// 方法 - 初始化表单数据
function initializeFormData() {
  const data: Record<string, any> = {}

  props.signalDefinitions.forEach(field => {
    // 设置初始值
    if (props.initialData && props.initialData[field.code] !== undefined) {
      data[field.code] = props.initialData[field.code]
    } else {
      // 根据数据类型设置默认值
      switch (field.data_type) {
        case 'float':
        case 'int':
          data[field.code] = null
          break
        case 'bool':
          data[field.code] = false
          break
        case 'string':
          data[field.code] = ''
          break
        case 'json':
          data[field.code] = {}
          break
        default:
          data[field.code] = null
      }
    }
  })

  formData.value = data
}

// 方法 - 提交表单
async function handleSubmit() {
  try {
    await formRef.value?.validate()
    
    // 数据类型转换
    const submitData = { ...formData.value }
    
    props.signalDefinitions.forEach(field => {
      const value = submitData[field.code]
      
      // 数值类型转换
      if (field.data_type === 'int' && value !== null && value !== '') {
        submitData[field.code] = parseInt(value)
      } else if (field.data_type === 'float' && value !== null && value !== '') {
        submitData[field.code] = parseFloat(value)
      }
    })
    
    emit('submit', submitData)
  } catch (error) {
    message.error('表单验证失败，请检查输入')
  }
}

// 方法 - 重置表单
function handleReset() {
  formRef.value?.restoreValidation()
  initializeFormData()
  emit('reset')
}

// 方法 - 取消操作
function handleCancel() {
  emit('cancel')
}

// 监听初始数据变化
watch(
  () => props.initialData,
  () => {
    initializeFormData()
  },
  { deep: true }
)

// 监听信号定义变化
watch(
  () => props.signalDefinitions,
  () => {
    initializeFormData()
  },
  { deep: true }
)

// 组件挂载时初始化
onMounted(() => {
  initializeFormData()
})

// 暴露方法给父组件
defineExpose({
  validate: () => formRef.value?.validate(),
  restoreValidation: () => formRef.value?.restoreValidation(),
  getFormData: () => formData.value,
  setFormData: (data: Record<string, any>) => {
    formData.value = { ...formData.value, ...data }
  }
})
</script>

<style scoped>
.dynamic-form-container {
  padding: 16px;
}

.form-header {
  margin-bottom: 24px;
}

.form-header h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--n-text-color);
}

.form-description {
  margin: 0;
  color: var(--n-text-color-2);
  font-size: 14px;
}

.field-group {
  margin-bottom: 16px;
}

.field-group.group-core {
  border-left: 3px solid #18a058;
  padding-left: 12px;
}

.field-group.group-temperature {
  border-left: 3px solid #f0a020;
  padding-left: 12px;
}

.field-group.group-power {
  border-left: 3px solid #2080f0;
  padding-left: 12px;
}

.field-group.group-speed {
  border-left: 3px solid #7c3aed;
  padding-left: 12px;
}

.input-unit {
  color: var(--n-text-color-3);
  font-size: 12px;
}

.field-description {
  color: var(--n-text-color-3);
  font-size: 12px;
  line-height: 1.4;
}

:deep(.n-form-item-label) {
  font-weight: 500;
}

:deep(.n-divider) {
  margin: 24px 0 16px 0;
}

:deep(.n-divider .n-divider__title) {
  font-weight: 600;
  color: var(--n-text-color);
}
</style>