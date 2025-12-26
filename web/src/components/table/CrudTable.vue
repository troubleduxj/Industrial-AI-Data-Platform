<template>
  <div v-bind="$attrs" class="crud-table-container">
    <QueryBar v-if="$slots.queryBar" mb-30 @search="handleSearch" @reset="handleReset">
      <slot name="queryBar" />
    </QueryBar>

    <div class="table-wrapper">
      <n-data-table
        :remote="remote"
        :loading="loading"
        :columns="columns"
        :data="props.getData ? tableData : props.data"
        :scroll-x="scrollX || undefined"
        :row-key="(row) => row[rowKey]"
        :checked-row-keys="internalCheckedRowKeys"
        :pagination="isPagination ? internalPagination : false"
        :cascade="cascade"
        :children-key="childrenKey"
        :default-expand-all="defaultExpandAll"
        :expanded-row-keys="expandedRowKeys"
        :indent="indent"
        @update:checked-row-keys="(rowKeys) => onChecked(rowKeys, null)"
        @update:expanded-row-keys="onExpandedRowKeysUpdate"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
const props = defineProps({
  /**
   * @remote true: 后端分页  false： 前端分页
   */
  remote: {
    type: Boolean,
    default: true,
  },
  /**
   * @remote 是否分页
   */
  isPagination: {
    type: Boolean,
    default: true,
  },
  scrollX: {
    type: [Number, String],
    default: null,
  },
  rowKey: {
    type: String,
    default: 'id',
  },
  columns: {
    type: Array,
    required: true,
  },
  data: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  pagination: {
    type: Object,
    default: () => ({}),
  },
  /**
   * @remote 远程数据加载方法
   */
  getData: {
    type: Function,
    default: null,
  },
  /**
   * 查询参数
   */
  queryItems: {
    type: Object,
    default: () => ({}),
  },
  /**
   * 树形表格相关配置
   */
  cascade: {
    type: Boolean,
    default: false,
  },
  childrenKey: {
    type: String,
    default: 'children',
  },
  defaultExpandAll: {
    type: Boolean,
    default: false,
  },
  expandedRowKeys: {
    type: Array,
    default: () => [],
  },
  /**
   * 树形表格缩进大小
   */
  indent: {
    type: Number,
    default: 24,
  },
  /**
   * 选中的行keys
   */
  checkedRowKeys: {
    type: Array,
    default: () => [],
  },
})

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const queryParams = ref({})

// 内部管理选中的行keys，避免直接绑定外部prop导致的问题
const internalCheckedRowKeys = ref([])

const emit = defineEmits([
  'onSearch',
  'onReset',
  'onChecked',
  'onPageChange',
  'onPageSizeChange',
  'update:queryItems',
  'load',
  'update:expandedRowKeys',
  'update:checkedRowKeys',
])

// 是否启用分页 - 直接使用props.isPagination
// 注意：不再使用computed，因为props.isPagination已经是响应式的

// 监听外部checkedRowKeys变化，同步到内部状态
watch(
  () => props.checkedRowKeys,
  (newVal) => {
    if (Array.isArray(newVal)) {
      internalCheckedRowKeys.value = [...newVal]
    }
  },
  { immediate: true }
)

// 监听queryItems变化，同步到内部queryParams
watch(
  () => props.queryItems,
  (newVal) => {
    queryParams.value = { ...newVal }
  },
  { immediate: true, deep: true }
)

const internalPagination = computed(() => {
  if (!props.isPagination) return false

  // 优先使用外部传入的itemCount，如果没有则使用内部total
  const itemCount = props.pagination?.itemCount ?? total.value
  const pageSize = props.pagination?.pageSize || 10

  return {
    ...props.pagination,
    page: props.pagination?.page || 1,
    pageSize: pageSize,
    pageCount: Math.ceil(itemCount / pageSize),
    itemCount: itemCount,
    showSizePicker: props.pagination?.showSizePicker ?? true,
    pageSizes: props.pagination?.pageSizes || [10, 20, 50, 100],
    showQuickJumper: props.pagination?.showQuickJumper ?? true,
    prefix: props.pagination?.prefix || ((info) => `共 ${info.itemCount} 条`),
    onUpdatePage: (page) => {
      console.log('分页组件页码变化:', page)
      onPageChange(page)
    },
    onUpdatePageSize: (pageSize) => {
      console.log('分页组件页大小变化:', pageSize)
      onPageSizeChange(pageSize)
    },
    // 兼容旧版本的事件名
    'onUpdate:page': (page) => {
      console.log('分页组件页码变化(兼容):', page)
      onPageChange(page)
    },
    'onUpdate:pageSize': (pageSize) => {
      console.log('分页组件页大小变化(兼容):', pageSize)
      onPageSizeChange(pageSize)
    },
  }
})

// 加载数据
async function loadData() {
  if (props.getData) {
    loading.value = true
    try {
      // 过滤掉空字符串和null/undefined的参数
      const filteredParams = Object.fromEntries(
        Object.entries(queryParams.value).filter(([key, value]) => {
          return value !== '' && value !== null && value !== undefined
        })
      )

      const res = await props.getData({
        page: internalPagination.value.page,
        page_size: internalPagination.value.pageSize,
        ...filteredParams,
      })
      tableData.value = res.data || []
      total.value = res.total || 0
      // 在nextTick中触发load事件，确保表格DOM已渲染完成
      nextTick(() => {
        emit('load', { data: tableData.value, total: total.value })
      })
    } catch (err) {
      console.error('加载数据失败:', err)
    } finally {
      loading.value = false
    }
  }
}

// 使用指定页码和页大小加载数据
async function loadDataWithPage(page, pageSize) {
  if (props.getData) {
    loading.value = true
    try {
      // 过滤掉空字符串和null/undefined的参数
      const filteredParams = Object.fromEntries(
        Object.entries(queryParams.value).filter(([key, value]) => {
          return value !== '' && value !== null && value !== undefined
        })
      )

      const res = await props.getData({
        page: page,
        page_size: pageSize,
        ...filteredParams,
      })
      tableData.value = res.data || []
      total.value = res.total || 0
      // 在nextTick中触发load事件，确保表格DOM已渲染完成
      nextTick(() => {
        emit('load', { data: tableData.value, total: total.value })
      })
    } catch (err) {
      console.error('加载数据失败:', err)
    } finally {
      loading.value = false
    }
  }
}

function onPageChange(page) {
  // 通知父组件更新分页状态
  emit('onPageChange', page)
  // 直接加载数据，使用传入的page参数
  loadDataWithPage(page, internalPagination.value.pageSize)
}

function onPageSizeChange(pageSize) {
  // 通知父组件更新分页状态
  emit('onPageSizeChange', pageSize)
  // 直接加载数据，重置到第一页
  loadDataWithPage(1, pageSize)
}

function handleSearch() {
  internalPagination.value.page = 1
  loadData()
  emit('onSearch')
}

function handleReset() {
  // 清空内部查询参数
  queryParams.value = {}
  // 通知外部清空查询条件，保持原有结构但清空值
  const resetItems = {}
  if (props.queryItems) {
    Object.keys(props.queryItems).forEach((key) => {
      // 对于布尔类型或undefined，重置为null（NSelect可以接受null）
      // 对于其他类型，重置为空字符串
      resetItems[key] =
        typeof props.queryItems[key] === 'boolean' || props.queryItems[key] === undefined
          ? null
          : ''
    })
  }
  emit('update:queryItems', resetItems)
  // 重置分页到第一页
  internalPagination.value.page = 1
  // 重新加载数据
  loadData()
  // 触发重置事件
  emit('onReset')
}

// 初始化加载
onMounted(() => {
  if (props.getData) {
    loadData()
  }
})

function onChecked(rowKeys, rows) {
  if (props.columns.some((item) => item.type === 'selection')) {
    // 确保rowKeys是ID数组而不是对象数组
    const validRowKeys = Array.isArray(rowKeys)
      ? rowKeys.filter((key) => typeof key === 'number' || typeof key === 'string')
      : []

    // 更新内部状态
    internalCheckedRowKeys.value = validRowKeys

    // 如果没有传递rows参数，从tableData中查找对应的行数据
    const selectedRows =
      rows ||
      (props.getData ? tableData.value : props.data).filter((row) =>
        validRowKeys.includes(row[props.rowKey])
      )

    emit('onChecked', validRowKeys, selectedRows)
    emit('update:checkedRowKeys', validRowKeys)
  }
}

function onExpandedRowKeysUpdate(expandedKeys) {
  emit('update:expandedRowKeys', expandedKeys)
}

defineExpose({
  handleSearch,
  handleReset,
  tableData,
  loading,
  total,
})
</script>

<style scoped>
.crud-table-container {
  width: 100%;
  overflow: hidden;
}

.table-wrapper {
  width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
}

/* 确保表格在没有设置scroll-x时能够自适应 */
.table-wrapper :deep(.n-data-table) {
  min-width: 100%;
}

/* 当表格内容超出容器宽度时，显示水平滚动条 */
.table-wrapper :deep(.n-data-table-wrapper) {
  overflow-x: auto;
}
</style>
