<template>
  <div class="property-field" :class="{ required: field.required, disabled: field.disabled }">
    <label class="field-label">
      <span class="label-text">{{ field.label }}</span>
      <span v-if="field.required" class="required-mark">*</span>
    </label>

    <!-- 输入框 -->
    <template v-if="field.type === 'input'">
      <input
        type="text"
        class="field-input"
        :value="value"
        :placeholder="field.placeholder"
        :disabled="field.disabled"
        @input="handleInput($event)"
        @blur="handleBlur"
      />
    </template>

    <!-- 文本域 -->
    <template v-else-if="field.type === 'textarea'">
      <textarea
        class="field-textarea"
        :value="value"
        :placeholder="field.placeholder"
        :disabled="field.disabled"
        :rows="field.props?.rows || 3"
        @input="handleInput($event)"
        @blur="handleBlur"
      />
    </template>

    <!-- 数字输入 -->
    <template v-else-if="field.type === 'number'">
      <input
        type="number"
        class="field-input field-number"
        :value="value"
        :placeholder="field.placeholder"
        :disabled="field.disabled"
        :min="field.props?.min"
        :max="field.props?.max"
        :step="field.props?.step || 1"
        @input="handleNumberInput($event)"
        @blur="handleBlur"
      />
    </template>

    <!-- 下拉选择 -->
    <template v-else-if="field.type === 'select'">
      <select
        class="field-select"
        :value="value"
        :disabled="field.disabled"
        @change="handleSelectChange($event)"
      >
        <option value="" disabled>{{ field.placeholder || '请选择' }}</option>
        <option 
          v-for="option in field.options" 
          :key="String(option.value)" 
          :value="option.value"
          :disabled="option.disabled"
        >
          {{ option.label }}
        </option>
      </select>
    </template>

    <!-- 多选 -->
    <template v-else-if="field.type === 'multiselect'">
      <div class="field-multiselect">
        <label 
          v-for="option in field.options" 
          :key="String(option.value)" 
          class="multiselect-option"
          :class="{ checked: isOptionSelected(option.value), disabled: option.disabled }"
        >
          <input
            type="checkbox"
            :checked="isOptionSelected(option.value)"
            :disabled="field.disabled || option.disabled"
            @change="handleMultiselectChange(option.value, $event)"
          />
          <span class="option-label">{{ option.label }}</span>
        </label>
      </div>
    </template>

    <!-- 开关 -->
    <template v-else-if="field.type === 'switch'">
      <label class="field-switch">
        <input
          type="checkbox"
          :checked="value"
          :disabled="field.disabled"
          @change="handleSwitchChange($event)"
        />
        <span class="switch-slider"></span>
        <span class="switch-label">{{ value ? '是' : '否' }}</span>
      </label>
    </template>

    <!-- JSON编辑器 -->
    <template v-else-if="field.type === 'json'">
      <div class="field-json">
        <textarea
          class="json-textarea"
          :value="jsonString"
          :placeholder="field.placeholder || '{}'"
          :disabled="field.disabled"
          :rows="field.props?.rows || 4"
          @input="handleJsonInput($event)"
          @blur="handleJsonBlur"
        />
        <div v-if="jsonError" class="json-error">{{ jsonError }}</div>
      </div>
    </template>

    <!-- 代码编辑器 -->
    <template v-else-if="field.type === 'code'">
      <div class="field-code">
        <textarea
          class="code-textarea"
          :value="value"
          :placeholder="field.placeholder"
          :disabled="field.disabled"
          :rows="field.props?.rows || 6"
          :style="{ height: field.props?.height ? `${field.props.height}px` : 'auto' }"
          @input="handleInput($event)"
          @blur="handleBlur"
        />
        <div class="code-language">{{ field.props?.language || 'text' }}</div>
      </div>
    </template>

    <!-- 颜色选择 -->
    <template v-else-if="field.type === 'color'">
      <div class="field-color">
        <input
          type="color"
          class="color-picker"
          :value="value || '#1890ff'"
          :disabled="field.disabled"
          @input="handleInput($event)"
        />
        <input
          type="text"
          class="color-text"
          :value="value"
          :placeholder="#1890ff"
          :disabled="field.disabled"
          @input="handleInput($event)"
        />
      </div>
    </template>

    <!-- 滑块 -->
    <template v-else-if="field.type === 'slider'">
      <div class="field-slider">
        <input
          type="range"
          class="slider-input"
          :value="value"
          :min="field.props?.min || 0"
          :max="field.props?.max || 100"
          :step="field.props?.step || 1"
          :disabled="field.disabled"
          @input="handleNumberInput($event)"
        />
        <span class="slider-value">{{ value }}</span>
      </div>
    </template>

    <!-- 日期选择 -->
    <template v-else-if="field.type === 'datepicker'">
      <input
        type="datetime-local"
        class="field-input field-date"
        :value="value"
        :disabled="field.disabled"
        @input="handleInput($event)"
      />
    </template>

    <!-- 默认：文本输入 -->
    <template v-else>
      <input
        type="text"
        class="field-input"
        :value="value"
        :placeholder="field.placeholder"
        :disabled="field.disabled"
        @input="handleInput($event)"
        @blur="handleBlur"
      />
    </template>

    <!-- 字段描述 -->
    <div v-if="field.description" class="field-description">
      {{ field.description }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { NodePropertyField } from '../../utils/nodePropertySchemas'

// Props
const props = defineProps<{
  field: NodePropertyField
  value: any
}>()

// Emits
const emit = defineEmits<{
  (e: 'update:value', value: any): void
}>()

// JSON相关状态
const jsonString = ref('')
const jsonError = ref('')

// 初始化JSON字符串
watch(() => props.value, (newValue) => {
  if (props.field.type === 'json') {
    try {
      jsonString.value = typeof newValue === 'string' 
        ? newValue 
        : JSON.stringify(newValue, null, 2)
      jsonError.value = ''
    } catch {
      jsonString.value = ''
    }
  }
}, { immediate: true })

// 检查多选选项是否被选中
function isOptionSelected(optionValue: any): boolean {
  if (!Array.isArray(props.value)) return false
  return props.value.includes(optionValue)
}

// 处理输入
function handleInput(event: Event) {
  const target = event.target as HTMLInputElement | HTMLTextAreaElement
  emit('update:value', target.value)
}

// 处理数字输入
function handleNumberInput(event: Event) {
  const target = event.target as HTMLInputElement
  const value = target.value === '' ? null : Number(target.value)
  emit('update:value', value)
}

// 处理下拉选择
function handleSelectChange(event: Event) {
  const target = event.target as HTMLSelectElement
  emit('update:value', target.value)
}

// 处理多选变化
function handleMultiselectChange(optionValue: any, event: Event) {
  const target = event.target as HTMLInputElement
  const currentValue = Array.isArray(props.value) ? [...props.value] : []
  
  if (target.checked) {
    if (!currentValue.includes(optionValue)) {
      currentValue.push(optionValue)
    }
  } else {
    const index = currentValue.indexOf(optionValue)
    if (index > -1) {
      currentValue.splice(index, 1)
    }
  }
  
  emit('update:value', currentValue)
}

// 处理开关变化
function handleSwitchChange(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:value', target.checked)
}

// 处理JSON输入
function handleJsonInput(event: Event) {
  const target = event.target as HTMLTextAreaElement
  jsonString.value = target.value
}

// 处理JSON失焦
function handleJsonBlur() {
  try {
    const parsed = JSON.parse(jsonString.value || '{}')
    jsonError.value = ''
    emit('update:value', parsed)
  } catch (e) {
    jsonError.value = 'JSON格式错误'
  }
}

// 处理失焦
function handleBlur() {
  // 可以在这里添加验证逻辑
}
</script>

<style scoped>
.property-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.property-field.disabled {
  opacity: 0.6;
}

.field-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 500;
  color: #262626;
}

.required-mark {
  color: #ff4d4f;
}

.field-input,
.field-textarea,
.field-select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 13px;
  color: #262626;
  background: #ffffff;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.field-input:focus,
.field-textarea:focus,
.field-select:focus {
  outline: none;
  border-color: #40a9ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.field-input:disabled,
.field-textarea:disabled,
.field-select:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.field-textarea {
  resize: vertical;
  min-height: 60px;
  font-family: inherit;
}

.field-number {
  width: 120px;
}

.field-select {
  cursor: pointer;
}

/* 多选样式 */
.field-multiselect {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.multiselect-option {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.15s ease;
}

.multiselect-option:hover {
  border-color: #40a9ff;
}

.multiselect-option.checked {
  border-color: #1890ff;
  background: #e6f7ff;
  color: #1890ff;
}

.multiselect-option.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.multiselect-option input {
  display: none;
}

/* 开关样式 */
.field-switch {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.field-switch input {
  display: none;
}

.switch-slider {
  position: relative;
  width: 40px;
  height: 22px;
  background: #d9d9d9;
  border-radius: 11px;
  transition: background 0.2s ease;
}

.switch-slider::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  background: #ffffff;
  border-radius: 50%;
  transition: transform 0.2s ease;
}

.field-switch input:checked + .switch-slider {
  background: #1890ff;
}

.field-switch input:checked + .switch-slider::after {
  transform: translateX(18px);
}

.switch-label {
  font-size: 13px;
  color: #595959;
}

/* JSON编辑器样式 */
.field-json {
  position: relative;
}

.json-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  color: #262626;
  background: #fafafa;
  resize: vertical;
  min-height: 80px;
}

.json-textarea:focus {
  outline: none;
  border-color: #40a9ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.json-error {
  margin-top: 4px;
  font-size: 12px;
  color: #ff4d4f;
}

/* 代码编辑器样式 */
.field-code {
  position: relative;
}

.code-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  color: #262626;
  background: #1e1e1e;
  color: #d4d4d4;
  resize: vertical;
  min-height: 100px;
}

.code-textarea:focus {
  outline: none;
  border-color: #40a9ff;
}

.code-language {
  position: absolute;
  top: 4px;
  right: 8px;
  font-size: 10px;
  color: #8c8c8c;
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 6px;
  border-radius: 3px;
}

/* 颜色选择样式 */
.field-color {
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-picker {
  width: 36px;
  height: 36px;
  padding: 0;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
}

.color-text {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 13px;
  font-family: monospace;
}

/* 滑块样式 */
.field-slider {
  display: flex;
  align-items: center;
  gap: 12px;
}

.slider-input {
  flex: 1;
  height: 4px;
  -webkit-appearance: none;
  background: #d9d9d9;
  border-radius: 2px;
  cursor: pointer;
}

.slider-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  background: #1890ff;
  border-radius: 50%;
  cursor: pointer;
}

.slider-value {
  min-width: 40px;
  text-align: right;
  font-size: 13px;
  color: #595959;
}

/* 日期选择样式 */
.field-date {
  width: auto;
}

/* 字段描述 */
.field-description {
  font-size: 12px;
  color: #8c8c8c;
  line-height: 1.4;
}
</style>
