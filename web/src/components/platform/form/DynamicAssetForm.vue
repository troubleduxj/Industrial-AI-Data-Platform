<template>
  <div class="dynamic-asset-form">
    <!-- 表单标题 -->
    <div v-if="showHeader" class="form-header">
      <h3>{{ formTitle }}</h3>
      <p v-if="formDescription" class="form-description">{{ formDescription }}</p>
    </div>

    <!-- 加载状态 -->
    <n-spin :show="signalsLoading">
      <n-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        :label-placement="labelPlacement"
        :label-width="labelWidth"
        :size="size"
        :disabled="readonly"
      >
        <!-- 按分组渲染字段 -->
        <template v-for="group in groupedFormFields" :key="group.name">
          <!-- 分组标题 -->
          <n-divider v-if="group.name !== 'default' && group.fields.length > 0" title-placement="left">
            <div class="group-title">
              <n-icon :component="getGroupIcon(group.name)" :size="18" />
              <span>{{ group.title }}</span>
            </div>
          </n-divider>

          <!-- 分组内的字段 -->
          <div class="field-group" :class="`group-${group.name}`">
            <n-grid :cols="gridCols" :x-gap="16" :y-gap="0" responsive="screen">
              <n-gi v-for="field in group.fields" :key="field.name" :span="getFieldSpan(field)">
                <SignalFieldRenderer
                  :field="field"
                  :value="formData[field.name]"
                  :error="validationErrors[field.name]"
                  :readonly="readonly"
                  @update:value="handleFieldChange(field.name, $event)"
                />
              </n-gi>
            </n-grid>
          </div>
        </template>

        <!-- 表单操作按钮 -->
        <n-form-item v-if="showActions" class="form-actions">
          <n-space>
            <n-button
              type="primary"
              :loading="isSubmitting"
              :disabled="readonly"
              @click="handleSubmit"
            >
              {{ submitText }}
            </n-button>
            <n-button v-if="showReset" :disabled="readonly" @click="handleReset">
              重置
            </n-button>
            <n-button v-if="showCancel" @click="handleCancel">
              取消
            </n-button>
          </n-space>
        </n-form-item>
      </n-form>
    </n-spin>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { 
  NForm, NFormItem, NButton, NSpace, NDivider, NIcon, NSpin, NGrid, NGi 
} from 'naive-ui'
import { 
  SettingsOutline, 
  ThermometerOutline, 
  FlashOutline, 
  SpeedometerOutline,
  ResizeOutline,
  BarChartOutline,
  EllipsisHorizontalOutline 
} from '@vicons/ionicons5'
import { useDynamicForm } from '../composables/useDynamicForm'
import SignalFieldRenderer from './SignalFieldRenderer.vue'

// Props
const props = defineProps({
  // 资产类别ID
  categoryId: {
    type: [Number, String],
    required: true
  },
  // 初始数据
  initialData: {
    type: Object,
    default: () => ({})
  },
  // 表单配置
  formTitle: {
    type: String,
    default: ''
  },
  formDescription: {
    type: String,
    default: ''
  },
  showHeader: {
    type: Boolean,
    default: false
  },
  showActions: {
    type: Boolean,
    default: true
  },
  showReset: {
    type: Boolean,
    default: true
  },
  showCancel: {
    type: Boolean,
    default: false
  },
  submitText: {
    type: String,
    default: '提交'
  },
  labelPlacement: {
    type: String,
    default: 'top'
  },
  labelWidth: {
    type: [String, Number],
    default: 'auto'
  },
  size: {
    type: String,
    default: 'medium'
  },
  readonly: {
    type: Boolean,
    default: false
  },
  // 布局配置
  gridCols: {
    type: [Number, String],
    default: '1 s:1 m:2 l:3 xl:4'
  }
})

// Emits
const emit = defineEmits(['submit', 'reset', 'cancel', 'change'])

// 使用动态表单组合式函数
const {
  formRef,
  formData,
  validationErrors,
  isDirty,
  isSubmitting,
  signalsLoading,
  groupedFormFields,
  formRules,
  hasErrors,
  validate,
  resetForm,
  getFormData,
  setFormData,
  initializeFormData
} = useDynamicForm(props.categoryId, {
  initialData: props.initialData,
  readonly: props.readonly
})

// 获取分组图标
function getGroupIcon(groupName) {
  const icons = {
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

// 获取字段跨度
function getFieldSpan(field) {
  // 根据字段类型决定跨度
  if (field.type === 'textarea' || field.type === 'json') {
    return '1 s:1 m:2 l:3 xl:4' // 全宽
  }
  return 1
}

// 处理字段变化
function handleFieldChange(fieldName, value) {
  formData[fieldName] = value
  emit('change', { field: fieldName, value, formData: getFormData() })
}

// 提交表单
async function handleSubmit() {
  const isValid = await validate()
  if (!isValid) {
    return
  }

  isSubmitting.value = true
  try {
    const data = getFormData()
    emit('submit', data)
  } finally {
    isSubmitting.value = false
  }
}

// 重置表单
function handleReset() {
  resetForm()
  emit('reset')
}

// 取消操作
function handleCancel() {
  emit('cancel')
}

// 监听初始数据变化
watch(() => props.initialData, (newData) => {
  initializeFormData(newData)
}, { deep: true })

// 暴露方法给父组件
defineExpose({
  validate,
  resetForm,
  getFormData,
  setFormData,
  formRef
})
</script>

<style scoped>
.dynamic-asset-form {
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

.group-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.field-group {
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 8px;
  background: var(--n-color-embedded);
}

.field-group.group-core {
  border-left: 3px solid #18a058;
}

.field-group.group-temperature {
  border-left: 3px solid #f0a020;
}

.field-group.group-power {
  border-left: 3px solid #2080f0;
}

.field-group.group-speed {
  border-left: 3px solid #7c3aed;
}

.field-group.group-dimension {
  border-left: 3px solid #06b6d4;
}

.field-group.group-pressure {
  border-left: 3px solid #ec4899;
}

.form-actions {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--n-border-color);
}

:deep(.n-divider) {
  margin: 24px 0 16px 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dynamic-asset-form {
    padding: 12px;
  }

  .field-group {
    padding: 8px;
  }
}
</style>
