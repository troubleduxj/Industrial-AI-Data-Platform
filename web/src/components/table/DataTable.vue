<template>
  <div class="data-table">
    <!-- 表格工具栏 -->
    <div v-if="showToolbar" class="table-toolbar">
      <div class="toolbar-left">
        <slot name="toolbar-left">
          <n-space>
            <!-- 刷新按钮 -->
            <n-button v-if="showRefresh" :loading="loading" size="small" @click="handleRefresh">
              <template #icon>
                <n-icon><RefreshOutline /></n-icon>
              </template>
              刷新
            </n-button>

            <!-- 导出按钮 -->
            <n-button v-if="showExport" size="small" @click="handleExport">
              <template #icon>
                <n-icon><DownloadOutline /></n-icon>
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
                  <n-icon><SettingsOutline /></n-icon>
                </template>
                列设置
              </n-button>
            </n-dropdown>
          </n-space>
        </slot>
      </div>

      <div class="toolbar-right">
        <slot name="toolbar-right">
          <!-- 搜索框 -->
          <n-input
            v-if="showSearch"
            v-model:value="searchValue"
            placeholder="搜索..."
            clearable
            size="small"
            style="width: 200px"
            @input="handleSearch"
          >
            <template #prefix>
              <n-icon><SearchOutline /></n-icon>
            </template>
          </n-input>
        </slot>
      </div>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="showBatchActions && checkedRowKeys.length > 0" class="batch-actions">
      <n-alert type="info" :show-icon="false">
        <template #header>
          <n-space align="center">
            <span>已选择 {{ checkedRowKeys.length }} 项</span>
            <slot name="batch-actions" :checked-row-keys="checkedRowKeys">
              <n-button size="small" @click="handleBatchDelete">
                <template #icon>
                  <n-icon><TrashOutline /></n-icon>
                </template>
                批量删除
              </n-button>
            </slot>
            <n-button size="small" @click="clearSelection">取消选择</n-button>
          </n-space>
        </template>
      </n-alert>
    </div>

    <!-- 数据表格 -->
    <n-data-table
      ref="tableRef"
      :columns="visibleColumns"
      :data="tableData"
      :loading="loading"
      :row-key="rowKey"
      :checked-row-keys="checkedRowKeys"
      :pagination="paginationConfig"
      :scroll-x="scrollX"
      :max-height="maxHeight"
      :size="size"
      :bordered="bordered"
      :striped="striped"
      :single-line="singleLine"
      :flex-height="flexHeight"
      @update:checked-row-keys="handleCheckedRowKeysChange"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
      @update:sorter="handleSorterChange"
      @update:filters="handleFiltersChange"
    />

    <!-- 空状态 -->
    <div v-if="!loading && tableData.length === 0" class="empty-state">
      <slot name="empty">
        <n-empty description="暂无数据">
          <template #icon>
            <n-icon size="48"><DocumentOutline /></n-icon>
          </template>
        </n-empty>
      </slot>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import {
  RefreshOutline,
  DownloadOutline,
  SettingsOutline,
  SearchOutline,
  TrashOutline,
  DocumentOutline,
} from '@vicons/ionicons5'

const props = defineProps({
  // 表格数据
  data: {
    type: Array,
    default: () => [],
  },
  // 表格列配置
  columns: {
    type: Array,
    default: () => [],
  },
  // 加载状态
  loading: {
    type: Boolean,
    default: false,
  },
  // 行键
  rowKey: {
    type: [String, Function],
    default: 'id',
  },
  // 分页配置
  pagination: {
    type: [Object, Boolean],
    default: () => ({
      page: 1,
      pageSize: 20,
      itemCount: 0,
      showSizePicker: true,
      showQuickJumper: true,
      pageSizes: [10, 20, 50, 100],
    }),
  },
  // 表格尺寸
  size: {
    type: String,
    default: 'medium',
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
  // 是否显示工具栏
  showToolbar: {
    type: Boolean,
    default: true,
  },
  // 是否显示刷新按钮
  showRefresh: {
    type: Boolean,
    default: true,
  },
  // 是否显示导出按钮
  showExport: {
    type: Boolean,
    default: true,
  },
  // 是否显示列设置
  showColumnSettings: {
    type: Boolean,
    default: true,
  },
  // 是否显示搜索框
  showSearch: {
    type: Boolean,
    default: true,
  },
  // 是否显示批量操作
  showBatchActions: {
    type: Boolean,
    default: true,
  },
  // 搜索防抖时间
  searchDebounce: {
    type: Number,
    default: 300,
  },
})

const emit = defineEmits([
  'refresh',
  'export',
  'search',
  'batch-delete',
  'page-change',
  'page-size-change',
  'sorter-change',
  'filters-change',
  'selection-change',
])

const message = useMessage()
const dialog = useDialog()
const tableRef = ref()
const searchValue = ref('')
const checkedRowKeys = ref([])
const hiddenColumns = ref(new Set())
const searchTimer = ref(null)

// 表格数据
const tableData = computed(() => props.data)

// 分页配置
const paginationConfig = computed(() => {
  if (props.pagination === false) {
    return false
  }

  return {
    ...props.pagination,
    prefix: ({ itemCount }) => `共 ${itemCount} 条`,
  }
})

// 可见列
const visibleColumns = computed(() => {
  return props.columns.filter((column) => !hiddenColumns.value.has(column.key))
})

// 列设置选项
const columnOptions = computed(() => {
  return props.columns.map((column) => ({
    label: column.title,
    key: column.key,
    icon: hiddenColumns.value.has(column.key) ? undefined : () => '✓',
  }))
})

// 监听选中行变化
watch(
  checkedRowKeys,
  (newKeys) => {
    emit('selection-change', newKeys)
  },
  { deep: true }
)

// 处理刷新
const handleRefresh = () => {
  emit('refresh')
}

// 处理导出
const handleExport = () => {
  emit('export', {
    data: tableData.value,
    columns: visibleColumns.value,
    selectedRows: checkedRowKeys.value,
  })
}

// 处理搜索
const handleSearch = (value) => {
  if (searchTimer.value) {
    clearTimeout(searchTimer.value)
  }

  searchTimer.value = setTimeout(() => {
    emit('search', value)
  }, props.searchDebounce)
}

// 处理列显示/隐藏切换
const handleColumnToggle = (key) => {
  if (hiddenColumns.value.has(key)) {
    hiddenColumns.value.delete(key)
  } else {
    hiddenColumns.value.add(key)
  }
}

// 处理批量删除
const handleBatchDelete = () => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除选中的 ${checkedRowKeys.value.length} 项吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: () => {
      emit('batch-delete', checkedRowKeys.value)
      checkedRowKeys.value = []
    },
  })
}

// 清除选择
const clearSelection = () => {
  checkedRowKeys.value = []
}

// 处理选中行变化
const handleCheckedRowKeysChange = (keys) => {
  checkedRowKeys.value = keys
}

// 处理分页变化
const handlePageChange = (page) => {
  emit('page-change', page)
}

// 处理页大小变化
const handlePageSizeChange = (pageSize) => {
  emit('page-size-change', pageSize)
}

// 处理排序变化
const handleSorterChange = (sorter) => {
  emit('sorter-change', sorter)
}

// 处理过滤变化
const handleFiltersChange = (filters) => {
  emit('filters-change', filters)
}

// 获取选中的行数据
const getSelectedRows = () => {
  return tableData.value.filter((row) => {
    const key = typeof props.rowKey === 'function' ? props.rowKey(row) : row[props.rowKey]
    return checkedRowKeys.value.includes(key)
  })
}

// 设置选中行
const setSelectedRows = (keys) => {
  checkedRowKeys.value = keys
}

// 刷新表格
const refresh = () => {
  nextTick(() => {
    tableRef.value?.scrollTo({ top: 0 })
  })
}

// 暴露方法
defineExpose({
  getSelectedRows,
  setSelectedRows,
  clearSelection,
  refresh,
})
</script>

<style scoped>
.data-table {
  width: 100%;
}

.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 0;
}

.toolbar-left {
  flex: 1;
}

.toolbar-right {
  flex: 0 0 auto;
}

.batch-actions {
  margin-bottom: 16px;
}

.empty-state {
  padding: 40px 0;
  text-align: center;
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
</style>
