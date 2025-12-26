<template>
  <NFormItem :label="field.field_name" :path="fieldPath">
    <!-- 文本输入 -->
    <NInput
      v-if="field.field_type === 'text'"
      :value="modelValue"
      :placeholder="`请输入${field.field_name}`"
      :required="field.is_required"
      :disabled="disabled"
      @update:value="handleUpdate"
    />

    <!-- 选择框 -->
    <NSelect
      v-else-if="field.field_type === 'select' || field.field_type === 'dict_select'"
      :value="modelValue"
      :options="fieldOptions"
      :placeholder="`请选择${field.field_name}`"
      :required="field.is_required"
      :disabled="disabled"
      clearable
      @update:value="handleUpdate"
    />

    <!-- 日期选择 -->
    <NDatePicker
      v-else-if="field.field_type === 'date'"
      :value="modelValue"
      type="date"
      :placeholder="`请选择${field.field_name}`"
      :required="field.is_required"
      :disabled="disabled"
      style="width: 100%"
      @update:value="handleUpdate"
    />

    <!-- 日期时间选择 -->
    <NDatePicker
      v-else-if="field.field_type === 'datetime'"
      :value="modelValue"
      type="datetime"
      :placeholder="`请选择${field.field_name}`"
      :required="field.is_required"
      :disabled="disabled"
      style="width: 100%"
      @update:value="handleUpdate"
    />

    <!-- 数字输入 -->
    <NInputNumber
      v-else-if="field.field_type === 'number'"
      :value="modelValue"
      :placeholder="`请输入${field.field_name}`"
      :required="field.is_required"
      :disabled="disabled"
      :precision="field.precision || 0"
      :min="field.min_value"
      :max="field.max_value"
      style="width: 100%"
      @update:value="handleUpdate"
    />

    <!-- 多行文本 -->
    <NInput
      v-else-if="field.field_type === 'textarea'"
      :value="modelValue"
      type="textarea"
      :placeholder="`请输入${field.field_name}`"
      :required="field.is_required"
      :disabled="disabled"
      :rows="field.rows || 3"
      @update:value="handleUpdate"
    />

    <!-- 布尔选择 -->
    <NRadioGroup
      v-else-if="field.field_type === 'boolean'"
      :value="modelValue"
      :disabled="disabled"
      @update:value="handleUpdate"
    >
      <NRadio :value="true">是</NRadio>
      <NRadio :value="false">否</NRadio>
    </NRadioGroup>

    <!-- 开关 -->
    <NSwitch
      v-else-if="field.field_type === 'switch'"
      :value="modelValue"
      :disabled="disabled"
      @update:value="handleUpdate"
    />

    <!-- 多选框 -->
    <NCheckboxGroup
      v-else-if="field.field_type === 'checkbox'"
      :value="modelValue"
      :disabled="disabled"
      @update:value="handleUpdate"
    >
      <NCheckbox v-for="option in fieldOptions" :key="option.value" :value="option.value">
        {{ option.label }}
      </NCheckbox>
    </NCheckboxGroup>

    <!-- 颜色选择器 -->
    <NColorPicker
      v-else-if="field.field_type === 'color'"
      :value="modelValue"
      :disabled="disabled"
      @update:value="handleUpdate"
    />

    <!-- 文件上传 -->
    <NUpload
      v-else-if="field.field_type === 'file'"
      :disabled="disabled"
      :max="field.max_files || 1"
      :accept="field.accept"
      @update:file-list="handleFileUpdate"
    >
      <NButton :disabled="disabled">
        <TheIcon icon="material-symbols:upload" :size="16" class="mr-1" />
        选择文件
      </NButton>
    </NUpload>

    <!-- 默认文本输入 -->
    <NInput
      v-else
      :value="modelValue"
      :placeholder="`请输入${field.field_name}`"
      :required="field.is_required"
      :disabled="disabled"
      @update:value="handleUpdate"
    />
  </NFormItem>
</template>

<script setup>
import { computed } from 'vue'
import {
  NFormItem,
  NInput,
  NInputNumber,
  NSelect,
  NDatePicker,
  NRadioGroup,
  NRadio,
  NSwitch,
  NCheckboxGroup,
  NCheckbox,
  NColorPicker,
  NUpload,
  NButton,
} from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'

const props = defineProps({
  field: {
    type: Object,
    required: true,
  },
  modelValue: {
    type: [String, Number, Boolean, Date, Array, Object],
    default: null,
  },
  fieldPath: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])

// 字段选项
const fieldOptions = computed(() => {
  if (props.field.options && Array.isArray(props.field.options)) {
    return props.field.options
  }

  // 如果是字典选择类型，返回字典选项
  if (props.field.field_type === 'dict_select' && props.field.dict_options) {
    return props.field.dict_options
  }

  return []
})

// 处理值更新
const handleUpdate = (value) => {
  emit('update:modelValue', value)
}

// 处理文件上传
const handleFileUpdate = (fileList) => {
  if (props.field.max_files === 1) {
    emit('update:modelValue', fileList[0] || null)
  } else {
    emit('update:modelValue', fileList)
  }
}
</script>

<style scoped>
/* 字段渲染器样式 */
:deep(.n-form-item-label) {
  font-weight: 500;
}

:deep(.n-checkbox-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

:deep(.n-upload) {
  width: 100%;
}
</style>
