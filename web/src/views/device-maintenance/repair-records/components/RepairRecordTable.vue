<template>
  <div class="repair-record-table">
    <!-- 表格工具栏 -->
    <div class="table-toolbar">
      <div class="toolbar-left">
        <NButton @click="showColumnConfig = true">
          <TheIcon icon="material-symbols:view-column" :size="16" class="mr-1" />
          列设置
        </NButton>
        <PermissionButton 
          permission="GET /api/v2/device/maintenance/repair-records"
          @click="refreshData"
          no-permission-text="您没有权限刷新维修记录数据"
        >
          <TheIcon icon="material-symbols:refresh" :size="16" class="mr-1" />
          刷新
        </PermissionButton>
      </div>
      
      <div class="toolbar-right">
        <span class="data-count">共 {{ pagination.itemCount }} 条记录</span>
      </div>
    </div>

    <!-- 数据表格 -->
    <NDataTable
      :columns="visibleColumns"
      :data="data"
      :loading="loading"
      :row-key="(row) => row.id"
      :scroll-x="scrollX"
      size="small"
      striped
    />

    <!-- 列配置弹窗 -->
    <NModal
      v-model:show="showColumnConfig"
      title="列显示设置"
      preset="card"
      style="width: 600px;"
    >
      <div class="column-config">
        <div class="config-header">
          <NButton size="small" @click="selectAllColumns">全选</NButton>
          <NButton size="small" @click="deselectAllColumns">全不选</NButton>
          <NButton size="small" @click="resetColumnConfig">重置</NButton>
        </div>
        
        <div class="config-content">
          <NCheckboxGroup v-model:value="selectedColumns">
            <div class="column-grid">
              <NCheckbox
                v-for="column in configurableColumns"
                :key="column.key"
                :value="column.key"
                :label="column.title"
                class="column-item"
              />
            </div>
          </NCheckboxGroup>
        </div>
      </div>
      
      <template #footer>
        <div class="flex justify-end gap-2">
          <NButton @click="showColumnConfig = false">取消</NButton>
          <NButton type="primary" @click="applyColumnConfig">确定</NButton>
        </div>
      </template>
    </NModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, h, type VNodeChild } from 'vue'
import { 
  NDataTable, 
  NButton, 
  NModal, 
  NCheckboxGroup, 
  NCheckbox,
  NTag,
  NPopconfirm,
  type DataTableColumn,
  type DataTableColumns,
  type PaginationProps
} from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import { PermissionButton } from '@/components/Permission'
import type { RepairRecordData } from '../composables/useDataExport'

// ==================== 类型定义 ====================

interface Props {
  data?: RepairRecordData[]
  loading?: boolean
  pagination?: PaginationProps
}

interface Emits {
  (e: 'edit', record: RepairRecordData): void
  (e: 'delete', id: string | number): void
  (e: 'refresh'): void
}

// Props
const props = withDefaults(defineProps<Props>(), {
  data: () => [],
  loading: false,
  pagination: () => ({})
})

// Emits
const emit = defineEmits<Emits>()

// 状态
const showColumnConfig = ref<boolean>(false)
const selectedColumns = ref<string[]>([])

// 所有可配置的列定义
const allColumns = [
  {
    title: '序号',
    key: 'index',
    width: 60,
    fixed: 'left',
    align: 'center',
    render: (row, index) => index + 1,
    configurable: false
  },
  {
    title: '报修日期',
    key: 'repair_date',
    width: 120,
    fixed: 'left',
    align: 'center',
    configurable: false
  },
  {
    title: '类别',
    key: 'category',
    width: 140,
    align: 'center',
    ellipsis: { tooltip: true },
    configurable: true
  },
  {
    title: '焊机编号',
    key: 'device_number',
    width: 120,
    fixed: 'left',
    align: 'center',
    configurable: false
  },
  {
    title: '品牌',
    key: 'brand',
    width: 80,
    align: 'center',
    configurable: true
  },
  {
    title: '型号',
    key: 'model',
    width: 120,
    align: 'center',
    configurable: true
  },
  {
    title: '接口类型',
    key: 'pin_type',
    width: 80,
    align: 'center',
    configurable: true
  },
  {
    title: '公司',
    key: 'company',
    width: 200,
    align: 'center',
    ellipsis: { tooltip: true },
    configurable: true
  },
  {
    title: '部门',
    key: 'department',
    width: 120,
    align: 'center',
    configurable: true
  },
  {
    title: '车间',
    key: 'workshop',
    width: 120,
    align: 'center',
    configurable: true
  },
  {
    title: '施工单位',
    key: 'construction_unit',
    width: 120,
    align: 'center',
    configurable: true
  },
  {
    title: '申请人',
    key: 'applicant',
    width: 100,
    align: 'center',
    configurable: true
  },
  {
    title: '电话',
    key: 'phone',
    width: 120,
    align: 'center',
    configurable: true
  },
  {
    title: '是否故障',
    key: 'is_fault',
    width: 80,
    align: 'center',
    configurable: true,
    render: (row) => {
      return h(NTag, {
        type: row.is_fault ? 'error' : 'success',
        size: 'small'
      }, { default: () => row.is_fault ? '故障' : '正常' })
    }
  },
  {
    title: '故障原因',
    key: 'fault_reason',
    width: 120,
    align: 'center',
    configurable: true
  },
  {
    title: '损坏类别',
    key: 'damage_category',
    width: 120,
    align: 'center',
    configurable: true
  },
  {
    title: '故障内容',
    key: 'fault_content',
    width: 200,
    align: 'center',
    ellipsis: { tooltip: true },
    configurable: true
  },
  {
    title: '故障部位',
    key: 'fault_location',
    width: 120,
    align: 'center',
    configurable: true
  },
  {
    title: '维修内容',
    key: 'repair_content',
    width: 200,
    align: 'center',
    ellipsis: { tooltip: true },
    configurable: true
  },
  {
    title: '配件名称',
    key: 'parts_name',
    width: 120,
    align: 'center',
    configurable: true
  },
  {
    title: '维修人',
    key: 'repairer',
    width: 100,
    align: 'center',
    configurable: true
  },
  {
    title: '维修完成日期',
    key: 'repair_completion_date',
    width: 120,
    align: 'center',
    configurable: true
  },
  {
    title: '备注',
    key: 'remarks',
    width: 150,
    align: 'center',
    ellipsis: { tooltip: true },
    configurable: true
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    align: 'center',
    fixed: 'right',
    configurable: false,
    render: (row) => {
      return [
        h(PermissionButton, {
          permission: 'PUT /api/v2/device/maintenance/repair-records/{id}',
          size: 'small',
          type: 'primary',
          secondary: true,
          style: 'margin-right: 6px;',
          noPermissionText: '您没有权限编辑维修记录',
          onClick: () => emit('edit', row)
        }, { default: () => '编辑' }),
        h(PermissionButton, {
          permission: 'DELETE /api/v2/device/maintenance/repair-records/{id}',
          size: 'small',
          type: 'error',
          secondary: true,
          needConfirm: true,
          confirmTitle: '删除确认',
          confirmContent: '确定删除这条维修记录吗？此操作不可恢复。',
          noPermissionText: '您没有权限删除维修记录',
          onConfirm: () => emit('delete', row)
        }, { default: () => '删除' })
      ]
    }
  }
]

// 可配置的列
const configurableColumns = computed(() => {
  return allColumns.filter(col => col.configurable)
})

// 默认显示的列
const defaultColumns = [
  'category', 'brand', 'model', 'company', 'department', 
  'applicant', 'phone', 'is_fault', 'fault_reason', 
  'fault_content', 'repairer', 'repair_completion_date'
]

// 当前显示的列
const visibleColumns = computed(() => {
  // 分离固定列：左侧固定列和操作列
  const leftFixedColumns = allColumns.filter(col => !col.configurable && col.key !== 'actions')
  const actionsColumn = allColumns.find(col => col.key === 'actions')
  const selectedConfigurableColumns = allColumns.filter(col => 
    col.configurable && selectedColumns.value.includes(col.key)
  )
  
  // 确保操作列始终在最后
  return [...leftFixedColumns, ...selectedConfigurableColumns, actionsColumn].filter(Boolean)
})

// 计算表格滚动宽度
const scrollX = computed(() => {
  return visibleColumns.value.reduce((total, col) => total + (col.width || 100), 0)
})

// 方法
const selectAllColumns = () => {
  selectedColumns.value = configurableColumns.value.map(col => col.key)
}

const deselectAllColumns = () => {
  selectedColumns.value = []
}

const resetColumnConfig = () => {
  selectedColumns.value = [...defaultColumns]
}

const applyColumnConfig = () => {
  // 保存到本地存储
  localStorage.setItem('repair-record-columns', JSON.stringify(selectedColumns.value))
  showColumnConfig.value = false
}

const refreshData = () => {
  emit('refresh')
}

// 初始化列配置
onMounted(() => {
  const savedColumns = localStorage.getItem('repair-record-columns')
  if (savedColumns) {
    try {
      selectedColumns.value = JSON.parse(savedColumns)
    } catch (error) {
      selectedColumns.value = [...defaultColumns]
    }
  } else {
    selectedColumns.value = [...defaultColumns]
  }
})
</script>

<style scoped>
.repair-record-table {
  background: white;
  border-radius: 6px;
}

.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e0e0e6;
  background-color: #fafafa;
}

.toolbar-left {
  display: flex;
  gap: 8px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.data-count {
  font-size: 14px;
  color: #666;
}

.column-config {
  padding: 16px 0;
}

.config-header {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e0e0e6;
}

.config-content {
  max-height: 400px;
  overflow-y: auto;
}

.column-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
}

.column-item {
  padding: 8px;
  border: 1px solid #e0e0e6;
  border-radius: 4px;
  background-color: #fafafa;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .table-toolbar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .toolbar-left,
  .toolbar-right {
    justify-content: center;
  }
  
  .column-grid {
    grid-template-columns: 1fr;
  }
}

/* 表格样式优化 */
:deep(.n-data-table) {
  border-radius: 0 0 6px 6px;
}

:deep(.n-data-table-th) {
  background-color: #f8f9fa;
  font-weight: 600;
  border-bottom: 2px solid #e0e0e6;
  text-align: center;
}

:deep(.n-data-table-td) {
  border-bottom: 1px solid #f0f0f0;
  text-align: center;
}

:deep(.n-data-table-tr:hover .n-data-table-td) {
  background-color: #f8f9fa;
}
</style>