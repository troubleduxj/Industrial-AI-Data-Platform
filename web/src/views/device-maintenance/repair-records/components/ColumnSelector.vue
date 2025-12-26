<template>
  <div class="column-selector">
    <!-- 列显示控制按钮 -->
    <NDropdown trigger="click" :options="[]" :show="false" placement="bottom-end">
      <template #default>
        <NButton size="small" @click="showColumnModal = true">
          <TheIcon icon="material-symbols:view-column" :size="16" class="mr-1" />
          列显示
        </NButton>
      </template>
    </NDropdown>

    <!-- 列显示控制弹窗 -->
    <NModal
      v-model:show="showColumnModal"
      preset="card"
      title="列显示设置"
      size="medium"
      :mask-closable="false"
      style="width: 600px"
    >
      <div class="column-config">
        <!-- 操作按钮 -->
        <div class="mb-4 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <NButton size="small" @click="selectAll"> 全选 </NButton>
            <NButton size="small" @click="selectNone"> 全不选 </NButton>
            <NButton size="small" @click="resetToDefault"> 恢复默认 </NButton>
          </div>
          <div class="text-sm text-gray-500">已选择 {{ selectedCount }} / {{ totalCount }} 列</div>
        </div>

        <!-- 列配置列表 -->
        <div class="column-list max-h-400 overflow-y-auto">
          <div v-for="group in columnGroups" :key="group.name" class="column-group mb-4">
            <div class="group-header mb-2">
              <h4 class="text-sm text-gray-700 font-medium">{{ group.label }}</h4>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div v-for="column in group.columns" :key="column.key" class="column-item">
                <NCheckbox
                  :checked="visibleColumns[column.key]"
                  :disabled="column.fixed"
                  @update:checked="(checked) => updateColumnVisibility(column.key, checked)"
                >
                  <span class="text-sm">{{ column.title }}</span>
                </NCheckbox>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2">
          <NButton @click="showColumnModal = false"> 取消 </NButton>
          <NButton type="primary" @click="applyChanges"> 确定 </NButton>
        </div>
      </template>
    </NModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { NButton, NModal, NCheckbox, NDropdown } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'

/**
 * 列选择器组件
 * 用于控制表格列的显示和隐藏
 */

const props = defineProps({
  /**
   * 列配置数组
   */
  columns: {
    type: Array,
    required: true,
  },
  /**
   * 当前可见列的配置
   */
  modelValue: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['update:modelValue', 'change'])

// 弹窗显示状态
const showColumnModal = ref(false)

// 当前可见列状态（本地副本）
const visibleColumns = ref({})

// 列分组配置
const columnGroups = computed(() => [
  {
    name: 'basic',
    label: '基础信息',
    columns: props.columns.filter((col) =>
      [
        'selection',
        'serial_number',
        'repair_date',
        'category',
        'device_number',
        'brand',
        'model',
        'device_name',
      ].includes(col.key)
    ),
  },
  {
    name: 'company',
    label: '公司信息',
    columns: props.columns.filter((col) =>
      ['company', 'manufacturer', 'installation_location', 'application_department'].includes(
        col.key
      )
    ),
  },
  {
    name: 'fault',
    label: '故障信息',
    columns: props.columns.filter((col) =>
      ['fault_reason', 'fault_content', 'applicant'].includes(col.key)
    ),
  },
  {
    name: 'repair',
    label: '维修信息',
    columns: props.columns.filter((col) =>
      [
        'repair_person',
        'repair_completion_date',
        'repair_cost',
        'spare_parts_used',
        'repair_notes',
        'maintenance_type',
      ].includes(col.key)
    ),
  },
  {
    name: 'status',
    label: '状态信息',
    columns: props.columns.filter((col) =>
      ['downtime_hours', 'warranty_status', 'repair_status'].includes(col.key)
    ),
  },
  {
    name: 'actions',
    label: '操作',
    columns: props.columns.filter((col) => col.key === 'actions'),
  },
])

// 统计信息
const selectedCount = computed(() => {
  return Object.values(visibleColumns.value).filter(Boolean).length
})

const totalCount = computed(() => {
  return props.columns.length
})

/**
 * 初始化可见列状态
 */
const initVisibleColumns = () => {
  const result = {}
  props.columns.forEach((col) => {
    // 从props中获取当前状态，如果没有则使用默认值
    result[col.key] =
      props.modelValue[col.key] !== undefined
        ? props.modelValue[col.key]
        : col.defaultVisible !== false // 默认显示，除非明确设置为false
  })
  visibleColumns.value = result
}

/**
 * 更新列可见性
 */
const updateColumnVisibility = (key, visible) => {
  visibleColumns.value[key] = visible
}

/**
 * 全选
 */
const selectAll = () => {
  props.columns.forEach((col) => {
    if (!col.fixed) {
      visibleColumns.value[col.key] = true
    }
  })
}

/**
 * 全不选
 */
const selectNone = () => {
  props.columns.forEach((col) => {
    if (!col.fixed) {
      visibleColumns.value[col.key] = false
    }
  })
}

/**
 * 恢复默认设置
 */
const resetToDefault = () => {
  props.columns.forEach((col) => {
    visibleColumns.value[col.key] = col.defaultVisible !== false
  })
}

/**
 * 应用更改
 */
const applyChanges = () => {
  emit('update:modelValue', { ...visibleColumns.value })
  emit('change', { ...visibleColumns.value })
  showColumnModal.value = false
}

// 监听props变化，更新本地状态
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue) {
      visibleColumns.value = { ...newValue }
    }
  },
  { immediate: true }
)

// 监听columns变化，重新初始化
watch(
  () => props.columns,
  () => {
    initVisibleColumns()
  },
  { immediate: true }
)
</script>

<style scoped>
.column-selector {
  display: inline-block;
}

.column-config {
  padding: 0;
}

.column-list {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 16px;
}

.column-group:last-child {
  margin-bottom: 0;
}

.group-header {
  border-bottom: 1px solid #f3f4f6;
  padding-bottom: 10px;
  margin-bottom: 12px;
}

.group-header h4 {
  font-size: 15px;
  font-weight: 600;
  color: #374151;
  margin: 0;
}

.column-item {
  padding: 6px 0;
}

.column-item :deep(.n-checkbox) {
  width: 100%;
}

.column-item :deep(.n-checkbox__label) {
  font-size: 14px;
  color: #374151;
  line-height: 1.5;
}

.column-item :deep(.n-checkbox__box) {
  margin-right: 10px;
}

/* 统计信息样式 */
.text-sm {
  font-size: 14px;
}

.text-gray-500 {
  color: #6b7280;
}

/* 操作按钮区域 */
.mb-4 {
  margin-bottom: 16px;
}

/* 网格布局优化 */
.grid {
  display: grid;
}

.grid-cols-2 {
  grid-template-columns: repeat(2, 1fr);
}

.gap-2 {
  gap: 8px;
}

/* 最大高度和滚动 */
.max-h-400 {
  max-height: 400px;
}

.overflow-y-auto {
  overflow-y: auto;
}

/* 弹性布局 */
.flex {
  display: flex;
}

.items-center {
  align-items: center;
}

.justify-between {
  justify-content: space-between;
}

.justify-end {
  justify-content: flex-end;
}
</style>
