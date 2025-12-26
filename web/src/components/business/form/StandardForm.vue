<template>
  <n-form
    ref="formRef"
    :model="formData"
    :rules="computedRules"
    :label-width="labelWidth"
    :label-placement="labelPlacement"
    :require-mark-placement="requireMarkPlacement"
    :size="size"
    :disabled="disabled || readonly"
    class="standard-form"
    :class="formClass"
  >
    <!-- 表单标题 -->
    <div v-if="title" class="form-title">
      <h3>{{ title }}</h3>
      <p v-if="description" class="form-description">{{ description }}</p>
    </div>

    <!-- 表单字段 -->
    <template v-for="field in processedFields" :key="field.name">
      <!-- 分组标题 -->
      <n-divider
        v-if="field.type === 'divider'"
        :title-placement="field.titlePlacement || 'left'"
        class="form-divider"
      >
        {{ field.label }}
      </n-divider>

      <!-- 分组容器 -->
      <n-card
        v-else-if="field.type === 'group'"
        :title="field.label"
        :bordered="field.bordered !== false"
        class="form-group"
      >
        <StandardForm
          v-model="formData[field.name]"
          :fields="field.fields"
          :readonly="field.disabled || readonly"
          :size="size"
          :label-width="labelWidth"
          :label-placement="labelPlacement"
          @field-change="handleNestedFieldChange(field, $event)"
          @validate="handleNestedValidate(field, $event)"
        />
      </n-card>

      <!-- 普通表单项 -->
      <n-form-item
        v-else
        :label="field.label"
        :path="field.name"
        :show-feedback="field.showFeedback !== false"
        :show-require-mark="field.required"
        :require-mark-placement="field.requireMarkPlacement"
        :label-style="field.labelStyle"
        :feedback-style="field.feedbackStyle"
        class="form-item"
        :class="getFieldClass(field)"
      >
        <!-- 字段帮助文本 -->
        <template v-if="field.help" #feedback>
          <div class="field-help">{{ field.help }}</div>
        </template>

        <!-- 动态字段组件 -->
        <component
          :is="getFieldComponent(field)"
          v-model:value="formData[field.name]"
          v-bind="getFieldProps(field)"
          @blur="handleFieldBlur(field)"
          @focus="handleFieldFocus(field)"
          @update:value="handleFieldChange(field, $event)"
        >
          <!-- 传递插槽 -->
          <template v-for="(_, slotName) in field.slots" :key="slotName" #[slotName]="slotProps">
            <slot :name="`field-${field.name}-${slotName}`" v-bind="slotProps" />
          </template>
        </component>

        <!-- 字段后缀内容 -->
        <div v-if="field.suffix || $slots[`field-${field.name}-suffix`]" class="field-suffix">
          <slot :name="`field-${field.name}-suffix`" :field="field" :value="formData[field.name]">
            {{ field.suffix }}
          </slot>
        </div>
      </n-form-item>
    </template>

    <!-- 表单操作按钮 -->
    <div v-if="showActions" class="form-actions" :class="actionsClass">
      <slot name="actions" :loading="loading" :validate="validate" :reset="resetForm">
        <n-space :justify="actionsAlign">
          <n-button v-if="showResetButton" :disabled="loading" @click="resetForm">
            {{ resetButtonText }}
          </n-button>

          <n-button v-if="showSubmitButton" type="primary" :loading="loading" @click="handleSubmit">
            {{ submitButtonText }}
          </n-button>
        </n-space>
      </slot>
    </div>
  </n-form>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick, onMounted } from 'vue'
import {
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSelect,
  NSwitch,
  NDatePicker,
  NTimePicker,
  NRadioGroup,
  NCheckboxGroup,
  NSlider,
  NRate,
  NColorPicker,
  NUpload,
  NCard,
  NDivider,
  NButton,
  NSpace,
  useMessage,
} from 'naive-ui'

/**
 * 标准表单组件
 * 提供统一的表单生成和验证功能
 *
 * @component StandardForm
 * @example
 * <StandardForm
 *   v-model="formData"
 *   :fields="formFields"
 *   title="用户信息"
 *   @submit="handleSubmit"
 *   @field-change="handleFieldChange"
 * />
 */

const props = defineProps({
  // 表单数据
  modelValue: {
    type: Object,
    default: () => ({}),
  },

  // 字段配置
  fields: {
    type: Array,
    required: true,
  },

  // 表单标题
  title: {
    type: String,
    default: '',
  },

  // 表单描述
  description: {
    type: String,
    default: '',
  },

  // 表单尺寸
  size: {
    type: String,
    default: 'medium',
    validator: (value) => ['small', 'medium', 'large'].includes(value),
  },

  // 标签宽度
  labelWidth: {
    type: [String, Number],
    default: '120px',
  },

  // 标签位置
  labelPlacement: {
    type: String,
    default: 'left',
    validator: (value) => ['left', 'top'].includes(value),
  },

  // 必填标记位置
  requireMarkPlacement: {
    type: String,
    default: 'right-hanging',
  },

  // 是否只读
  readonly: {
    type: Boolean,
    default: false,
  },

  // 是否禁用
  disabled: {
    type: Boolean,
    default: false,
  },

  // 是否显示操作按钮
  showActions: {
    type: Boolean,
    default: true,
  },

  // 是否显示提交按钮
  showSubmitButton: {
    type: Boolean,
    default: true,
  },

  // 是否显示重置按钮
  showResetButton: {
    type: Boolean,
    default: true,
  },

  // 提交按钮文本
  submitButtonText: {
    type: String,
    default: '提交',
  },

  // 重置按钮文本
  resetButtonText: {
    type: String,
    default: '重置',
  },

  // 操作按钮对齐方式
  actionsAlign: {
    type: String,
    default: 'end',
    validator: (value) =>
      ['start', 'center', 'end', 'space-around', 'space-between'].includes(value),
  },

  // 加载状态
  loading: {
    type: Boolean,
    default: false,
  },

  // 实时验证
  validateOnChange: {
    type: Boolean,
    default: true,
  },

  // 表单布局
  layout: {
    type: String,
    default: 'vertical',
    validator: (value) => ['vertical', 'horizontal', 'inline'].includes(value),
  },

  // 栅格配置
  grid: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits([
  'update:modelValue',
  'submit',
  'reset',
  'field-change',
  'field-focus',
  'field-blur',
  'validate',
])

const message = useMessage()
const formRef = ref()

// 表单数据
const formData = reactive({ ...props.modelValue })

// 字段组件映射
const fieldComponents = {
  input: NInput,
  number: NInputNumber,
  textarea: NInput,
  password: NInput,
  select: NSelect,
  switch: NSwitch,
  date: NDatePicker,
  time: NTimePicker,
  radio: NRadioGroup,
  checkbox: NCheckboxGroup,
  slider: NSlider,
  rate: NRate,
  color: NColorPicker,
  upload: NUpload,
}

// 计算属性
const formClass = computed(() => ({
  [`standard-form--${props.layout}`]: props.layout !== 'vertical',
  [`standard-form--${props.size}`]: props.size !== 'medium',
  'standard-form--readonly': props.readonly,
  'standard-form--disabled': props.disabled,
}))

const actionsClass = computed(() => ({
  [`form-actions--${props.actionsAlign}`]: props.actionsAlign !== 'end',
}))

const processedFields = computed(() => {
  return props.fields
    .map((field) => ({
      ...field,
      // 设置默认值
      name: field.name || field.key,
      type: field.type || 'input',
      placeholder: field.placeholder || `请输入${field.label}`,
      clearable: field.clearable !== false,
      // 处理条件显示
      visible: field.when ? evaluateCondition(field.when, formData) : true,
    }))
    .filter((field) => field.visible)
})

const computedRules = computed(() => {
  const rules = {}

  processedFields.value.forEach((field) => {
    if (field.rules) {
      rules[field.name] = Array.isArray(field.rules) ? field.rules : [field.rules]
    } else if (field.required) {
      rules[field.name] = [
        {
          required: true,
          message: field.requiredMessage || `请输入${field.label}`,
          trigger: field.trigger || ['blur', 'input'],
        },
      ]
    }

    // 添加自定义验证规则
    if (field.validator) {
      if (!rules[field.name]) rules[field.name] = []
      rules[field.name].push({
        validator: field.validator,
        trigger: field.trigger || ['blur', 'input'],
      })
    }
  })

  return rules
})

// 方法
function getFieldComponent(field) {
  if (field.component) {
    return field.component
  }

  const component = fieldComponents[field.type]
  if (!component) {
    console.warn(`未知的字段类型: ${field.type}`)
    return NInput
  }

  return component
}

function getFieldProps(field) {
  const baseProps = {
    placeholder: field.placeholder,
    disabled: field.disabled || props.disabled || props.readonly,
    clearable: field.clearable,
    size: field.size || props.size,
  }

  // 根据字段类型添加特定属性
  switch (field.type) {
    case 'textarea':
      return {
        ...baseProps,
        type: 'textarea',
        rows: field.rows || 3,
        autosize: field.autosize,
        maxlength: field.maxlength,
        showCount: field.showCount,
      }

    case 'password':
      return {
        ...baseProps,
        type: 'password',
        showPasswordOn: field.showPasswordOn || 'mousedown',
      }

    case 'number':
      return {
        ...baseProps,
        min: field.min,
        max: field.max,
        step: field.step || 1,
        precision: field.precision,
      }

    case 'select':
      return {
        ...baseProps,
        options: field.options || [],
        multiple: field.multiple,
        filterable: field.filterable,
        remote: field.remote,
        onSearch: field.onSearch,
      }

    case 'date':
      return {
        ...baseProps,
        type: field.dateType || 'date',
        format: field.format,
        valueFormat: field.valueFormat,
      }

    case 'switch':
      return {
        ...baseProps,
        checkedValue: field.checkedValue,
        uncheckedValue: field.uncheckedValue,
      }

    default:
      return {
        ...baseProps,
        ...field.props,
      }
  }
}

function getFieldClass(field) {
  return {
    [`form-item--${field.type}`]: true,
    'form-item--required': field.required,
    'form-item--readonly': field.readonly || props.readonly,
    'form-item--disabled': field.disabled || props.disabled,
    [`form-item--span-${field.span}`]: field.span,
  }
}

function evaluateCondition(condition, data) {
  if (typeof condition === 'function') {
    return condition(data)
  }

  if (typeof condition === 'object') {
    const { field, value, operator = '===' } = condition
    const fieldValue = data[field]

    switch (operator) {
      case '===':
        return fieldValue === value
      case '!==':
        return fieldValue !== value
      case '>':
        return fieldValue > value
      case '<':
        return fieldValue < value
      case '>=':
        return fieldValue >= value
      case '<=':
        return fieldValue <= value
      case 'includes':
        return Array.isArray(fieldValue) && fieldValue.includes(value)
      case 'in':
        return Array.isArray(value) && value.includes(fieldValue)
      default:
        return true
    }
  }

  return true
}

// 事件处理
function handleFieldChange(field, value) {
  formData[field.name] = value

  emit('field-change', {
    field: field.name,
    value,
    formData: { ...formData },
  })

  // 字段联动处理
  if (field.onChange) {
    field.onChange(value, formData, field)
  }

  // 实时验证
  if (props.validateOnChange && field.validateOnChange !== false) {
    nextTick(() => {
      validateField(field.name)
    })
  }
}

function handleFieldFocus(field) {
  emit('field-focus', {
    field: field.name,
    value: formData[field.name],
  })

  if (field.onFocus) {
    field.onFocus(formData[field.name], formData, field)
  }
}

function handleFieldBlur(field) {
  emit('field-blur', {
    field: field.name,
    value: formData[field.name],
  })

  if (field.onBlur) {
    field.onBlur(formData[field.name], formData, field)
  }
}

function handleNestedFieldChange(groupField, event) {
  emit('field-change', {
    field: `${groupField.name}.${event.field}`,
    value: event.value,
    formData: { ...formData },
  })
}

function handleNestedValidate(groupField, event) {
  emit('validate', {
    field: `${groupField.name}`,
    ...event,
  })
}

async function handleSubmit() {
  const result = await validate()
  if (result.valid) {
    emit('submit', result.data)
  }
}

// 表单操作方法
async function validate() {
  try {
    await formRef.value?.validate()
    const result = { valid: true, data: { ...formData } }
    emit('validate', result)
    return result
  } catch (errors) {
    const result = { valid: false, errors, data: { ...formData } }
    emit('validate', result)
    return result
  }
}

async function validateField(fieldName) {
  try {
    await formRef.value?.validate(undefined, (rule) => {
      return rule.key === fieldName
    })
    return true
  } catch (error) {
    return false
  }
}

function resetForm() {
  formRef.value?.restoreValidation()

  // 重置为初始值或默认值
  processedFields.value.forEach((field) => {
    if (field.defaultValue !== undefined) {
      formData[field.name] = field.defaultValue
    } else {
      delete formData[field.name]
    }
  })

  emit('reset', { ...formData })
}

function setFieldValue(fieldName, value) {
  formData[fieldName] = value
}

function getFieldValue(fieldName) {
  return formData[fieldName]
}

function setFieldProps(fieldName, props) {
  const field = processedFields.value.find((f) => f.name === fieldName)
  if (field) {
    Object.assign(field, props)
  }
}

// 监听器
watch(
  formData,
  (newValue) => {
    emit('update:modelValue', { ...newValue })
  },
  { deep: true }
)

watch(
  () => props.modelValue,
  (newValue) => {
    Object.assign(formData, newValue)
  },
  { deep: true }
)

// 生命周期
onMounted(() => {
  // 设置字段默认值
  processedFields.value.forEach((field) => {
    if (field.defaultValue !== undefined && formData[field.name] === undefined) {
      formData[field.name] = field.defaultValue
    }
  })
})

// 暴露方法
defineExpose({
  validate,
  validateField,
  resetForm,
  setFieldValue,
  getFieldValue,
  setFieldProps,
  formRef,
})
</script>

<style scoped>
.standard-form {
  width: 100%;
}

/* 表单标题 */
.form-title {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.form-title h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color);
}

.form-description {
  margin: 0;
  font-size: 14px;
  color: var(--text-color-secondary);
  line-height: 1.5;
}

/* 表单分组 */
.form-group {
  margin-bottom: 24px;
}

.form-divider {
  margin: 24px 0 16px 0;
}

/* 表单项 */
.form-item {
  margin-bottom: 16px;
}

.form-item--required :deep(.n-form-item-label) {
  font-weight: 500;
}

.field-help {
  font-size: 12px;
  color: var(--text-color-secondary);
  margin-top: 4px;
}

.field-suffix {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-color-secondary);
}

/* 表单操作 */
.form-actions {
  margin-top: 32px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.form-actions--start {
  text-align: left;
}

.form-actions--center {
  text-align: center;
}

.form-actions--end {
  text-align: right;
}

/* 布局样式 */
.standard-form--horizontal .form-item {
  margin-bottom: 20px;
}

.standard-form--inline {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.standard-form--inline .form-item {
  margin-bottom: 0;
  flex: 0 0 auto;
}

/* 尺寸样式 */
.standard-form--small .form-item {
  margin-bottom: 12px;
}

.standard-form--large .form-item {
  margin-bottom: 20px;
}

/* 状态样式 */
.standard-form--readonly {
  opacity: 0.8;
}

.standard-form--disabled {
  opacity: 0.6;
  pointer-events: none;
}

/* 栅格布局 */
.form-item--span-1 {
  width: 8.333%;
}
.form-item--span-2 {
  width: 16.666%;
}
.form-item--span-3 {
  width: 25%;
}
.form-item--span-4 {
  width: 33.333%;
}
.form-item--span-6 {
  width: 50%;
}
.form-item--span-8 {
  width: 66.666%;
}
.form-item--span-12 {
  width: 100%;
}

/* 暗色主题适配 */
.dark .form-title {
  border-bottom-color: var(--border-color);
}

.dark .form-actions {
  border-top-color: var(--border-color);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .standard-form--horizontal {
    display: block;
  }

  .standard-form--inline {
    flex-direction: column;
  }

  .form-actions {
    text-align: center;
  }

  .form-actions--start,
  .form-actions--end {
    text-align: center;
  }

  /* 移动端栅格自适应 */
  .form-item--span-1,
  .form-item--span-2,
  .form-item--span-3,
  .form-item--span-4,
  .form-item--span-6,
  .form-item--span-8 {
    width: 100%;
  }
}
</style>
