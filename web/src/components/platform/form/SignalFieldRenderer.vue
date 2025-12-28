<template>
  <n-form-item
    :label="field.label"
    :path="field.name"
    :show-require-mark="field.required"
    :validation-status="error ? 'error' : undefined"
    :feedback="error ? error[0] : undefined"
  >
    <!-- 数值输入 -->
    <n-input-number
      v-if="field.type === 'number'"
      :value="value"
      :placeholder="field.placeholder"
      :disabled="readonly || field.disabled"
      :precision="field.precision"
      :min="field.min"
      :max="field.max"
      :step="field.precision === 0 ? 1 : 0.01"
      style="width: 100%"
      @update:value="handleUpdate"
    >
      <template v-if="field.unit" #suffix>
        <span class="input-unit">{{ field.unit }}</span>
      </template>
    </n-input-number>

    <!-- 文本输入 -->
    <n-input
      v-else-if="field.type === 'input'"
      :value="value"
      :placeholder="field.placeholder"
      :disabled="readonly || field.disabled"
      :maxlength="field.maxlength"
      :show-count="field.showCount"
      clearable
      @update:value="handleUpdate"
    />

    <!-- 多行文本 -->
    <n-input
      v-else-if="field.type === 'textarea'"
      :value="value"
      type="textarea"
      :placeholder="field.placeholder"
      :disabled="readonly || field.disabled"
      :rows="field.rows || 3"
      :maxlength="field.maxlength"
      :show-count="field.showCount"
      @update:value="handleUpdate"
    />

    <!-- 开关 -->
    <n-switch
      v-else-if="field.type === 'switch'"
      :value="value"
      :disabled="readonly || field.disabled"
      @update:value="handleUpdate"
    >
      <template #checked>开启</template>
      <template #unchecked>关闭</template>
    </n-switch>

    <!-- 日期选择 -->
    <n-date-picker
      v-else-if="field.type === 'date'"
      :value="value"
      type="date"
      :placeholder="field.placeholder"
      :disabled="readonly || field.disabled"
      style="width: 100%"
      @update:value="handleUpdate"
    />

    <!-- 日期时间选择 -->
    <n-date-picker
      v-else-if="field.type === 'datetime'"
      :value="value"
      type="datetime"
      :placeholder="field.placeholder"
      :disabled="readonly || field.disabled"
      style="width: 100%"
      @update:value="handleUpdate"
    />

    <!-- 选择器 -->
    <n-select
      v-else-if="field.type === 'select'"
      :value="value"
      :options="field.options || []"
      :placeholder="field.placeholder"
      :disabled="readonly || field.disabled"
      :multiple="field.multiple"
      clearable
      @update:value="handleUpdate"
    />

    <!-- JSON编辑器 -->
    <n-input
      v-else-if="field.type === 'json'"
      :value="jsonValue"
      type="textarea"
      :placeholder="field.placeholder || '请输入JSON格式数据'"
      :disabled="readonly || field.disabled"
      :rows="5"
      @update:value="handleJsonUpdate"
    />

    <!-- 默认文本输入 -->
    <n-input
      v-else
      :value="value"
      :placeholder="field.placeholder"
      :disabled="readonly || field.disabled"
      clearable
      @update:value="handleUpdate"
    />

    <!-- 字段说明 -->
    <template v-if="field._signal?.description && !error" #feedback>
      <span class="field-description">{{ field._signal.description }}</span>
    </template>
  </n-form-item>
</template>

<script setup>
import { computed } from 'vue'
import { 
  NFormItem, NInput, NInputNumber, NSelect, NSwitch, NDatePicker 
} from 'naive-ui'

// Props
const props = defineProps({
  field: {
    type: Object,
    required: true
  },
  value: {
    type: [String, Number, Boolean, Object, Array],
    default: null
  },
  error: {
    type: Array,
    default: null
  },
  readonly: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['update:value'])

// JSON值处理
const jsonValue = computed(() => {
  if (props.value === null || props.value === undefined) return ''
  if (typeof props.value === 'string') return props.value
  try {
    return JSON.stringify(props.value, null, 2)
  } catch {
    return ''
  }
})

// 处理值更新
function handleUpdate(newValue) {
  emit('update:value', newValue)
}

// 处理JSON值更新
function handleJsonUpdate(newValue) {
  try {
    const parsed = JSON.parse(newValue)
    emit('update:value', parsed)
  } catch {
    // 如果解析失败，保存原始字符串
    emit('update:value', newValue)
  }
}
</script>

<style scoped>
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

:deep(.n-form-item) {
  margin-bottom: 16px;
}
</style>
