<template>
  <div class="dynamic-property-form">
    <!-- 分组显示 -->
    <template v-if="schema.groups && schema.groups.length > 0">
      <div v-for="group in schema.groups" :key="group.name" class="property-group">
        <div 
          class="group-header" 
          :class="{ collapsed: collapsedGroups.has(group.name) }"
          @click="toggleGroup(group.name)"
        >
          <span class="group-icon">{{ collapsedGroups.has(group.name) ? '▶' : '▼' }}</span>
          <span class="group-label">{{ group.label }}</span>
        </div>
        <div v-show="!collapsedGroups.has(group.name)" class="group-content">
          <template v-for="fieldName in group.fields" :key="fieldName">
            <PropertyField
              v-if="getFieldByName(fieldName) && shouldShowField(getFieldByName(fieldName)!, formData)"
              :field="getFieldByName(fieldName)!"
              :value="formData[fieldName]"
              @update:value="handleFieldChange(fieldName, $event)"
            />
          </template>
        </div>
      </div>
    </template>

    <!-- 无分组显示 -->
    <template v-else>
      <template v-for="field in schema.fields" :key="field.field">
        <PropertyField
          v-if="shouldShowField(field, formData)"
          :field="field"
          :value="formData[field.field]"
          @update:value="handleFieldChange(field.field, $event)"
        />
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import PropertyField from './PropertyField.vue'
import { 
  type NodePropertySchema, 
  type NodePropertyField,
  shouldShowField,
  getNodeDefaultProperties 
} from '../../utils/nodePropertySchemas'

// Props
const props = defineProps<{
  schema: NodePropertySchema
  modelValue: Record<string, any>
}>()

// Emits
const emit = defineEmits<{
  (e: 'update:modelValue', value: Record<string, any>): void
  (e: 'change', field: string, value: any): void
}>()

// 响应式数据
const collapsedGroups = ref<Set<string>>(new Set())
const formData = ref<Record<string, any>>({})

// 初始化表单数据
function initFormData() {
  const defaults = getNodeDefaultProperties(props.schema.nodeType)
  formData.value = { ...defaults, ...props.modelValue }
}

// 监听外部值变化
watch(() => props.modelValue, (newValue) => {
  formData.value = { ...formData.value, ...newValue }
}, { deep: true })

// 监听schema变化
watch(() => props.schema, () => {
  initFormData()
  // 初始化折叠状态
  if (props.schema.groups) {
    props.schema.groups.forEach(group => {
      if (group.collapsed) {
        collapsedGroups.value.add(group.name)
      }
    })
  }
}, { immediate: true })

// 获取字段定义
function getFieldByName(fieldName: string): NodePropertyField | undefined {
  return props.schema.fields.find(f => f.field === fieldName)
}

// 切换分组折叠状态
function toggleGroup(groupName: string) {
  if (collapsedGroups.value.has(groupName)) {
    collapsedGroups.value.delete(groupName)
  } else {
    collapsedGroups.value.add(groupName)
  }
}

// 处理字段值变化
function handleFieldChange(field: string, value: any) {
  formData.value[field] = value
  emit('update:modelValue', { ...formData.value })
  emit('change', field, value)
}

// 生命周期
onMounted(() => {
  initFormData()
})
</script>

<style scoped>
.dynamic-property-form {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.property-group {
  margin-bottom: 8px;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f5f5f5;
  border-radius: 4px;
  cursor: pointer;
  user-select: none;
  transition: background 0.15s ease;
}

.group-header:hover {
  background: #e8e8e8;
}

.group-header.collapsed {
  margin-bottom: 0;
}

.group-icon {
  font-size: 10px;
  color: #8c8c8c;
  width: 12px;
}

.group-label {
  font-size: 13px;
  font-weight: 600;
  color: #262626;
}

.group-content {
  padding: 12px 0 0 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
