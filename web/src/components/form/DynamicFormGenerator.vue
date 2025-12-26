<template>
  <n-form
    ref="formRef"
    :model="formData"
    :rules="dynamicRules"
    :label-width="labelWidth"
    :label-placement="labelPlacement"
    :require-mark-placement="requireMarkPlacement"
  >
    <template v-for="field in fields" :key="field.name">
      <!-- 文本输入框 -->
      <n-form-item
        v-if="field.type === 'input'"
        :label="field.label"
        :path="field.name"
        :show-feedback="field.showFeedback !== false"
      >
        <n-input
          v-model:value="formData[field.name]"
          :placeholder="field.placeholder"
          :disabled="field.disabled || readonly"
          :clearable="field.clearable !== false"
          :maxlength="field.maxlength"
          :show-count="field.showCount"
          @blur="handleFieldBlur(field)"
          @input="handleFieldInput(field, $event)"
        />
      </n-form-item>

      <!-- 数字输入框 -->
      <n-form-item
        v-else-if="field.type === 'number'"
        :label="field.label"
        :path="field.name"
        :show-feedback="field.showFeedback !== false"
      >
        <n-input-number
          v-model:value="formData[field.name]"
          :placeholder="field.placeholder"
          :disabled="field.disabled || readonly"
          :min="field.min"
          :max="field.max"
          :step="field.step || 1"
          :precision="field.precision"
          style="width: 100%"
          @blur="handleFieldBlur(field)"
          @update:value="handleFieldInput(field, $event)"
        />
      </n-form-item>

      <!-- 文本域 -->
      <n-form-item
        v-else-if="field.type === 'textarea'"
        :label="field.label"
        :path="field.name"
        :show-feedback="field.showFeedback !== false"
      >
        <n-input
          v-model:value="formData[field.name]"
          type="textarea"
          :placeholder="field.placeholder"
          :disabled="field.disabled || readonly"
          :rows="field.rows || 3"
          :autosize="field.autosize"
          :maxlength="field.maxlength"
          :show-count="field.showCount"
          @blur="handleFieldBlur(field)"
          @input="handleFieldInput(field, $event)"
        />
      </n-form-item>

      <!-- 选择器 -->
      <n-form-item
        v-else-if="field.type === 'select'"
        :label="field.label"
        :path="field.name"
        :show-feedback="field.showFeedback !== false"
      >
        <n-select
          v-model:value="formData[field.name]"
          :options="field.options || []"
          :placeholder="field.placeholder"
          :disabled="field.disabled || readonly"
          :multiple="field.multiple"
          :clearable="field.clearable !== false"
          :filterable="field.filterable"
          @update:value="handleFieldInput(field, $event)"
        />
      </n-form-item>

      <!-- 开关 -->
      <n-form-item
        v-else-if="field.type === 'switch'"
        :label="field.label"
        :path="field.name"
        :show-feedback="field.showFeedback !== false"
      >
        <n-switch
          v-model:value="formData[field.name]"
          :disabled="field.disabled || readonly"
          @update:value="handleFieldInput(field, $event)"
        >
          <template v-if="field.checkedText" #checked>{{ field.checkedText }}</template>
          <template v-if="field.uncheckedText" #unchecked>{{ field.uncheckedText }}</template>
        </n-switch>
      </n-form-item>

      <!-- 日期选择器 -->
      <n-form-item
        v-else-if="field.type === 'date'"
        :label="field.label"
        :path="field.name"
        :show-feedback="field.showFeedback !== false"
      >
        <n-date-picker
          v-model:value="formData[field.name]"
          :type="field.dateType || 'date'"
          :placeholder="field.placeholder"
          :disabled="field.disabled || readonly"
          :clearable="field.clearable !== false"
          style="width: 100%"
          @update:value="handleFieldInput(field, $event)"
        />
      </n-form-item>

      <!-- 时间选择器 -->
      <n-form-item
        v-else-if="field.type === 'time'"
        :label="field.label"
        :path="field.name"
        :show-feedback="field.showFeedback !== false"
      >
        <n-time-picker
          v-model:value="formData[field.name]"
          :placeholder="field.placeholder"
          :disabled="field.disabled || readonly"
          :clearable="field.clearable !== false"
          style="width: 100%"
          @update:value="handleFieldInput(field, $event)"
        />
      </n-form-item>

      <!-- 动态输入 -->
      <n-form-item
        v-else-if="field.type === 'dynamic'"
        :label="field.label"
        :path="field.name"
        :show-feedback="field.showFeedback !== false"
      >
        <n-dynamic-input
          v-model:value="formData[field.name]"
          :disabled="field.disabled || readonly"
          :on-create="field.onCreate || (() => ({}))"
          :min="field.min || 0"
          :max="field.max"
        >
          <template #default="{ value, index }">
            <component
              :is="field.itemComponent"
              v-model="formData[field.name][index]"
              :field="field"
              :index="index"
              :readonly="field.disabled || readonly"
            />
          </template>
        </n-dynamic-input>
      </n-form-item>

      <!-- 自定义组件 -->
      <n-form-item
        v-else-if="field.type === 'custom'"
        :label="field.label"
        :path="field.name"
        :show-feedback="field.showFeedback !== false"
      >
        <component
          :is="field.component"
          v-model="formData[field.name]"
          :field="field"
          :readonly="field.disabled || readonly"
          @update:model-value="handleFieldInput(field, $event)"
        />
      </n-form-item>

      <!-- 分组 -->
      <n-card
        v-else-if="field.type === 'group'"
        :title="field.label"
        :bordered="field.bordered !== false"
        class="mb-4"
      >
        <DynamicFormGenerator
          v-model="formData[field.name]"
          :fields="field.fields"
          :readonly="field.disabled || readonly"
          :label-width="labelWidth"
          :label-placement="labelPlacement"
          @field-change="handleNestedFieldChange(field, $event)"
        />
      </n-card>

      <!-- 分割线 -->
      <n-divider
        v-else-if="field.type === 'divider'"
        :title-placement="field.titlePlacement || 'left'"
      >
        {{ field.label }}
      </n-divider>
    </template>
  </n-form>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { useMessage } from 'naive-ui'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({}),
  },
  fields: {
    type: Array,
    default: () => [],
  },
  readonly: {
    type: Boolean,
    default: false,
  },
  labelWidth: {
    type: [String, Number],
    default: '120px',
  },
  labelPlacement: {
    type: String,
    default: 'left',
  },
  requireMarkPlacement: {
    type: String,
    default: 'right-hanging',
  },
  validateOnChange: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['update:modelValue', 'field-change', 'validate'])

const message = useMessage()
const formRef = ref()

// 表单数据
const formData = reactive({ ...props.modelValue })

// 动态验证规则
const dynamicRules = computed(() => {
  const rules = {}

  props.fields.forEach((field) => {
    if (field.rules) {
      rules[field.name] = field.rules
    } else if (field.required) {
      rules[field.name] = {
        required: true,
        message: field.requiredMessage || `请输入${field.label}`,
        trigger: field.trigger || ['blur', 'input'],
      }
    }
  })

  return rules
})

// 监听表单数据变化
watch(
  formData,
  (newValue) => {
    emit('update:modelValue', { ...newValue })
  },
  { deep: true }
)

// 监听外部数据变化
watch(
  () => props.modelValue,
  (newValue) => {
    Object.assign(formData, newValue)
  },
  { deep: true }
)

// 字段值变化处理
const handleFieldInput = (field, value) => {
  formData[field.name] = value

  // 触发字段变化事件
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

// 字段失焦处理
const handleFieldBlur = (field) => {
  if (field.onBlur) {
    field.onBlur(formData[field.name], formData, field)
  }
}

// 嵌套字段变化处理
const handleNestedFieldChange = (groupField, event) => {
  emit('field-change', {
    field: `${groupField.name}.${event.field}`,
    value: event.value,
    formData: { ...formData },
  })
}

// 验证单个字段
const validateField = async (fieldName) => {
  try {
    await formRef.value?.validate(undefined, (rule) => {
      return rule.key === fieldName
    })
    return true
  } catch (error) {
    return false
  }
}

// 验证整个表单
const validate = async () => {
  try {
    await formRef.value?.validate()
    emit('validate', { valid: true, data: { ...formData } })
    return { valid: true, data: { ...formData } }
  } catch (errors) {
    emit('validate', { valid: false, errors, data: { ...formData } })
    return { valid: false, errors, data: { ...formData } }
  }
}

// 重置表单
const resetForm = () => {
  formRef.value?.restoreValidation()

  // 重置为初始值
  props.fields.forEach((field) => {
    if (field.defaultValue !== undefined) {
      formData[field.name] = field.defaultValue
    } else {
      delete formData[field.name]
    }
  })
}

// 设置字段值
const setFieldValue = (fieldName, value) => {
  formData[fieldName] = value
}

// 获取字段值
const getFieldValue = (fieldName) => {
  return formData[fieldName]
}

// 设置字段属性
const setFieldProps = (fieldName, props) => {
  const field = props.fields.find((f) => f.name === fieldName)
  if (field) {
    Object.assign(field, props)
  }
}

// 暴露方法
defineExpose({
  validate,
  resetForm,
  setFieldValue,
  getFieldValue,
  setFieldProps,
  validateField,
  formRef,
})
</script>

<style scoped>
.mb-4 {
  margin-bottom: 16px;
}
</style>
