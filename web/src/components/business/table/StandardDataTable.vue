<template>
  <div class="standard-data-table">
    <!-- 查询栏 -->
    <div v-if="showQueryBar" class="table-query-bar">
      <slot name="query-bar" :query-params="queryParams" :loading="loading">
        <QueryBar @search="handleSearch" @reset="handleReset">
          <slot name="query-fields" :query-params="queryParams" />
        </QueryBar>
      </slot>
    </div>

    <!-- 工具栏 -->
    <div v-if="showToolbar" class="table-toolbar">
      <div class="toolbar-left">
        <slot name="toolbar-left" :selected-rows="selectedRows" :loading="loading">
          <!-- 批量操作按钮 -->
          <n-space v-if="selectedRows.length > 0">
            <n-tag type="info" size="small"> 已选择 {{ selectedRows.length }} 项 </n-tag>
            <slot name="batch-actions" :selected-rows="selectedRows">
              <n-button v-if="showBatchDelete" type="error" size="small" @click="handleBatchDelete">
                <template #icon>
                  <n-icon :component="TrashOutline" />
                </template>
                批量删除
              </n-button>
            </slot>
            <n-button size="small" @click="clearSelection"> 取消选择 </n-button>
          </n-space>
        </slot>
      </div>

      <div class="toolbar-right">
        <slot name="toolbar-right" :loading="loading" :refresh="handleRefresh">
          <n-space>
            <!-- 刷新按钮 -->
            <n-button v-if="showRefresh" size="small" :loading="loading" @click="handleRefresh">
              <template #icon>
                <n-icon :component="RefreshOutline" />
              </template>
              刷新
            </n-button>

            <!-- 导出按钮 -->
            <n-button v-if="showExport" size="small" @click="handleExport">
              <template #icon>
                <n-icon :component="DownloadOutline" />
              </template>
              导出
            </n-button>

            <!-- 列设置 -->
            <n-dropdown
              v-if="showColumnSettings"
              trigger="click"
              :options="columnOptions"
              @select="handleColumnToggle"
            >
              <n-button size="small">
                <template #icon>
                  <n-icon :component="SettingsOutline" />
                </template>
                列设置
              </n-button>
            </n-dropdown>

            <!-- 密度设置 -->
            <n-dropdown
              v-if="showDensitySettings"
              trigger="click"
              :options="densityOptions"
              @select="handleDensityChange"
            >
              <n-button size="small">
                <template #icon>
                  <n-icon :component="ResizeOutline" />
                </template>
                密度
              </n-button>
            </n-dropdown>
          </n-space>
        </slot>
      </div>
    </div>

    <!-- 数据表格 -->
    <n-data-table
      ref="tableRef"
      :remote="remote"
      :loading="loading"
      :columns="visibleColumns"
      :data="tableData"
      :row-key="rowKey"
      :checked-row-keys="checkedRowKeys"
      :pagination="paginationConfig"
      :scroll-x="scrollX"
      :max-height="maxHeight"
      :size="tableSize"
      :bordered="bordered"
      :striped="striped"
      :single-line="singleLine"
      :flex-height="flexHeight"
      :virtual-scroll="virtualScroll"
      :cascade="cascade"
      :children-key="childrenKey"
      :indent="indent"
      @update:checked-row-keys="handleCheckedRowKeysChange"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
      @update:sorter="handleSorterChange"
      @update:filters="handleFiltersChange"
    >
      <!-- 空状态 -->
      <template #empty>
        <slot name="empty">
          <LoadingEmptyWrapper :loading="false" :empty="true" empty-description="暂无数据" />
        </slot>
      </template>
    </n-data-table>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import {
  NDataTable,
  NButton,
  NIcon,
  NSpace,
  NTag,
  NDropdown,
  useMessage,
  useDialog,
} from 'naive-ui'
import {
  RefreshOutline,
  DownloadOutline,
  SettingsOutline,
  TrashOutline,
  ResizeOutline,
} from '@vicons/ionicons5'
import LoadingEmptyWrapper from '@/components/common/LoadingEmptyWrapper.vue'
import QueryBar from '@/components/query-bar/QueryBar.vue'

/**
 * 标准数据表格组件
 * 提供完整的数据表格功能，包括查询、分页、排序、筛选、导出等
 *
 * @component StandardDataTable
 * @example
 * <StandardDataTable
 *   :columns="columns"
 *   :load-data="loadData"
 *   :show-query-bar="true"
 *   @selection-change="handleSelectionChange"
 * >
 *   <template #query-fields="{ queryParams }">
 *     <n-form-item label="名称">
 *       <n-input v-model:value="queryParams.name" placeholder="请输入名称" />
 *     </n-form-item>
 *   </template>
 * </StandardDataTable>
 */

const props = defineProps({
  // 表格列配置
  columns: {
    type: Array,
    required: true,
  },

  // 静态数据（非远程加载时使用）
  data: {
    type: Array,
    default: () => [],
  },

  // 数据加载函数
  loadData: {
    type: Function,
    default: null,
  },

  // 是否远程加载
  remote: {
    type: Boolean,
    default: true,
  },

  // 行键
  rowKey: {
    type: [String, Function],
    default: 'id',
  },

  // 初始查询参数
  initialQuery: {
    type: Object,
    default: () => ({}),
  },

  // 分页配置
  pagination: {
    type: [Object, Boolean],
    default: () => ({
      page: 1,
      pageSize: 20,
      showSizePicker: true,
      showQuickJumper: true,
      pageSizes: [10, 20, 50, 100],
    }),
  },

  // 表格尺寸
  size: {
    type: String,
    default: 'medium',
    validator: (value) => ['small', 'medium', 'large'].includes(value),
  },

  // 是否显示边框
  bordered: {
    type: Boolean,
    default: true,
  },

  // 是否显示斑马纹
  striped: {
    type: Boolean,
    default: false,
  },

  // 是否单行显示
  singleLine: {
    type: Boolean,
    default: true,
  },

  // 是否自适应高度
  flexHeight: {
    type: Boolean,
    default: false,
  },

  // 最大高度
  maxHeight: {
    type: [Number, String],
    default: undefined,
  },

  // 横向滚动宽度
  scrollX: {
    type: [Number, String],
    default: undefined,
  },

  // 是否启用虚拟滚动
  virtualScroll: {
    type: Boolean,
    default: false,
  },

  // 树形数据相关
  cascade: {
    type: Boolean,
    default: false,
  },

  childrenKey: {
    type: String,
    default: 'children',
  },

  indent: {
    type: Number,
    default: 16,
  },

  // UI控制
  showQueryBar: {
    type: Boolean,
    default: true,
  },

  showToolbar: {
    type: Boolean,
    default: true,
  },

  showRefresh: {
    type: Boolean,
    default: true,
  },

  showExport: {
    type: Boolean,
    default: true,
  },

  showColumnSettings: {
    type: Boolean,
    default: true,
  },

  showDensitySettings: {
    type: Boolean,
    default: true,
  },

  showBatchDelete: {
    type: Boolean,
    default: false,
  },

  // 自动加载
  autoLoad: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits([
  'load',
  'search',
  'reset',
  'refresh',
  'export',
  'selection-change',
  'batch-delete',
  'page-change',
  'page-size-change',
  'sorter-change',
  'filters-change',
  'column-change',
  'density-change',
])

const message = useMessage()
const dialog = useDialog()

// 响应式数据
const tableRef = ref()
const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const queryParams = ref({ ...props.initialQuery })
const checkedRowKeys = ref([])
const hiddenColumns = ref(new Set())
const tableSize = ref(props.size)

// 计算属性
const selectedRows = computed(() => {
  return tableData.value.filter((row) => {
    const key = typeof props.rowKey === 'function' ? props.rowKey(row) : row[props.rowKey]
    return checkedRowKeys.value.includes(key)
  })
})

const visibleColumns = computed(() => {
  return props.columns.filter((column) => !hiddenColumns.value.has(column.key))
})

const columnOptions = computed(() => {
  return props.columns.map((column) => ({
    label: column.title,
    key: column.key,
    icon: hiddenColumns.value.has(column.key) ? undefined : () => '✓',
  }))
})

const densityOptions = computed(() => [
  { label: '紧凑', key: 'small', icon: tableSize.value === 'small' ? () => '✓' : undefined },
  { label: '默认', key: 'medium', icon: tableSize.value === 'medium' ? () => '✓' : undefined },
  { label: '宽松', key: 'large', icon: tableSize.value === 'large' ? () => '✓' : undefined },
])

const paginationConfig = computed(() => {
  if (props.pagination === false) return false

  return {
    ...props.pagination,
    itemCount: total.value,
    prefix: ({ itemCount }) => `共 ${itemCount} 条`,
  }
})

// 数据加载
async function loadTableData() {
  if (!props.loadData) {
    tableData.value = props.data
    total.value = props.data.length
    return
  }

  loading.value = true

  try {
    // 过滤空值参数
    const filteredParams = Object.fromEntries(
      Object.entries(queryParams.value).filter(([key, value]) => {
        return value !== '' && value !== null && value !== undefined
      })
    )

    const params = {
      ...filteredParams,
      page: paginationConfig.value.page || 1,
      pageSize: paginationConfig.value.pageSize || 20,
    }

    const result = await props.loadData(params)

    tableData.value = result.data || result.items || []
    total.value = result.total || result.count || 0

    emit('load', { data: tableData.value, total: total.value, params })
  } catch (error) {
    console.error('加载数据失败:', error)
    message.error('加载数据失败')
    tableData.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 事件处理
function handleSearch() {
  if (paginationConfig.value) {
    paginationConfig.value.page = 1
  }
  loadTableData()
  emit('search', queryParams.value)
}

function handleReset() {
  queryParams.value = { ...props.initialQuery }
  if (paginationConfig.value) {
    paginationConfig.value.page = 1
  }
  loadTableData()
  emit('reset')
}

function handleRefresh() {
  loadTableData()
  emit('refresh')
}

function handleExport() {
  emit('export', {
    data: tableData.value,
    columns: visibleColumns.value,
    selectedRows: selectedRows.value,
    queryParams: queryParams.value,
  })
}

function handleBatchDelete() {
  if (selectedRows.value.length === 0) {
    message.warning('请先选择要删除的数据')
    return
  }

  dialog.warning({
    title: '确认删除',
    content: `确定要删除选中的 ${selectedRows.value.length} 项数据吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: () => {
      emit('batch-delete', selectedRows.value)
      clearSelection()
    },
  })
}

function clearSelection() {
  checkedRowKeys.value = []
}

function handleCheckedRowKeysChange(keys) {
  checkedRowKeys.value = keys
  emit('selection-change', selectedRows.value)
}

function handlePageChange(page) {
  emit('page-change', page)
  nextTick(() => {
    loadTableData()
  })
}

function handlePageSizeChange(pageSize) {
  emit('page-size-change', pageSize)
  nextTick(() => {
    loadTableData()
  })
}

function handleSorterChange(sorter) {
  emit('sorter-change', sorter)
  // 如果是远程排序，重新加载数据
  if (props.remote) {
    loadTableData()
  }
}

function handleFiltersChange(filters) {
  emit('filters-change', filters)
  // 如果是远程筛选，重新加载数据
  if (props.remote) {
    loadTableData()
  }
}

function handleColumnToggle(key) {
  if (hiddenColumns.value.has(key)) {
    hiddenColumns.value.delete(key)
  } else {
    hiddenColumns.value.add(key)
  }
  emit('column-change', { key, visible: !hiddenColumns.value.has(key) })
}

function handleDensityChange(size) {
  tableSize.value = size
  emit('density-change', size)
}

// 公开方法
function refresh() {
  loadTableData()
}

function getSelectedRows() {
  return selectedRows.value
}

function setSelectedRows(keys) {
  checkedRowKeys.value = keys
}

function scrollTo(options) {
  tableRef.value?.scrollTo(options)
}

// 生命周期
onMounted(() => {
  if (props.autoLoad) {
    loadTableData()
  }
})

// 监听外部数据变化
watch(
  () => props.data,
  (newData) => {
    if (!props.remote) {
      tableData.value = newData
      total.value = newData.length
    }
  },
  { deep: true }
)

// 暴露方法
defineExpose({
  refresh,
  loadTableData,
  getSelectedRows,
  setSelectedRows,
  clearSelection,
  scrollTo,
  tableRef,
})
</script>

<style scoped>
.standard-data-table {
  width: 100%;
}

.table-query-bar {
  margin-bottom: 16px;
}

.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-color);
}

.toolbar-left {
  flex: 1;
}

.toolbar-right {
  flex: 0 0 auto;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .table-toolbar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .toolbar-left,
  .toolbar-right {
    flex: none;
  }
}

/* 暗色主题适配 */
.dark .table-toolbar {
  border-bottom-color: var(--border-color);
}
</style>
