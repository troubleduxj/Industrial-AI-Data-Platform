<!--
  批量删除组合式函数使用示例
  展示如何在实际组件中使用 useBatchDelete
-->
<template>
  <div class="batch-delete-example">
    <n-card title="批量删除示例" class="mb-4">
      <template #header-extra>
        <n-space>
          <n-button type="primary" :loading="loading" @click="loadMockData"> 加载数据 </n-button>
          <n-button
            type="error"
            :disabled="!canBatchDelete"
            :loading="isLoading"
            @click="handleBatchDelete"
          >
            批量删除 ({{ selectedCount }})
          </n-button>
        </n-space>
      </template>

      <!-- 数据表格 -->
      <n-data-table
        ref="tableRef"
        :columns="columns"
        :data="tableData"
        :row-key="(row) => row.id"
        :checked-row-keys="selectedRowKeys"
        :loading="loading"
        :pagination="pagination"
        @update:checked-row-keys="handleSelectionChange"
      />

      <!-- 操作结果显示 -->
      <n-card v-if="lastOperation" title="最后操作结果" class="mt-4">
        <n-alert
          :type="lastOperation.success ? 'success' : 'error'"
          :title="getOperationSummary()"
          closable
          @close="resetOperationState"
        >
          <div v-if="getFailedItemsDetails().length > 0" class="mt-2">
            <n-text strong>失败详情：</n-text>
            <ul class="mt-1">
              <li v-for="item in getFailedItemsDetails()" :key="item.id">
                ID: {{ item.id }} - {{ item.reason }}
              </li>
            </ul>
          </div>
        </n-alert>
      </n-card>
    </n-card>
  </div>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import { NCard, NButton, NSpace, NDataTable, NAlert, NText, NTag, useMessage } from 'naive-ui'
import { useBatchDelete } from '@/composables/useBatchDelete'

defineOptions({ name: 'BatchDeleteExample' })

const message = useMessage()
const tableRef = ref(null)
const loading = ref(false)
const tableData = ref([])

// 分页配置
const pagination = {
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  showQuickJumper: true,
}

// 表格列配置
const columns = [
  {
    type: 'selection',
  },
  {
    title: 'ID',
    key: 'id',
    width: 80,
  },
  {
    title: '名称',
    key: 'name',
    ellipsis: {
      tooltip: true,
    },
  },
  {
    title: '类型',
    key: 'type',
    render: (row) => {
      const typeMap = {
        system: { type: 'error', text: '系统' },
        user: { type: 'info', text: '用户' },
        temp: { type: 'warning', text: '临时' },
      }
      const config = typeMap[row.type] || { type: 'default', text: '未知' }
      return h(NTag, { type: config.type }, { default: () => config.text })
    },
  },
  {
    title: '状态',
    key: 'status',
    render: (row) => {
      return h(
        NTag,
        {
          type: row.status === 'active' ? 'success' : 'default',
        },
        {
          default: () => (row.status === 'active' ? '启用' : '禁用'),
        }
      )
    },
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
  },
]

// 模拟批量删除API
const mockBatchDeleteApi = async (ids) => {
  console.log('调用批量删除API，IDs:', ids)

  // 模拟网络延迟
  await new Promise((resolve) => setTimeout(resolve, 1000))

  // 模拟部分失败的情况
  const failedItems = []
  const skippedItems = []
  let deletedCount = 0

  ids.forEach((id) => {
    const item = tableData.value.find((item) => item.id === id)
    if (!item) return

    // 系统类型的项目不能删除
    if (item.type === 'system') {
      skippedItems.push({
        id,
        reason: '系统保护项，不允许删除',
      })
    } else if (Math.random() < 0.1) {
      // 10% 概率失败
      failedItems.push({
        id,
        reason: '删除失败：数据库约束错误',
      })
    } else {
      deletedCount++
    }
  })

  return {
    success: true,
    message: '批量删除操作完成',
    data: {
      deleted_count: deletedCount,
      failed_items: failedItems,
      skipped_items: skippedItems,
    },
  }
}

// 模拟刷新数据
const refreshData = async () => {
  console.log('刷新数据')
  await loadMockData()
}

// 使用批量删除组合式函数
const {
  selectedItems,
  selectedRowKeys,
  isLoading,
  selectedCount,
  canBatchDelete,
  lastOperation,
  setSelectedItems,
  handleBatchDelete,
  getOperationSummary,
  getFailedItemsDetails,
  resetOperationState,
} = useBatchDelete({
  name: '测试项目',
  batchDeleteApi: mockBatchDeleteApi,
  refresh: refreshData,
  excludeCondition: (item) => item.type === 'system', // 系统项目不能删除
  validateItem: (item) => {
    if (item.status === 'locked') {
      return { valid: false, reason: '项目已锁定，无法删除' }
    }
    return { valid: true }
  },
  permission: 'test:batch_delete', // 权限检查
  maxBatchSize: 50,
})

// 处理选择变化
const handleSelectionChange = (keys) => {
  const items = tableData.value.filter((item) => keys.includes(item.id))
  setSelectedItems(items, keys)
}

// 加载模拟数据
const loadMockData = async () => {
  loading.value = true

  try {
    // 模拟API调用
    await new Promise((resolve) => setTimeout(resolve, 500))

    // 生成模拟数据
    const mockData = []
    for (let i = 1; i <= 25; i++) {
      mockData.push({
        id: i,
        name: `测试项目 ${i}`,
        type: i <= 3 ? 'system' : i % 3 === 0 ? 'temp' : 'user',
        status: Math.random() > 0.3 ? 'active' : 'inactive',
        created_at: new Date(
          Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000
        ).toLocaleString(),
      })
    }

    tableData.value = mockData
    message.success('数据加载成功')
  } catch (error) {
    message.error('数据加载失败')
  } finally {
    loading.value = false
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadMockData()
})
</script>

<style scoped>
.batch-delete-example {
  padding: 16px;
}

.mb-4 {
  margin-bottom: 16px;
}

.mt-4 {
  margin-top: 16px;
}

.mt-2 {
  margin-top: 8px;
}

.mt-1 {
  margin-top: 4px;
}
</style>
