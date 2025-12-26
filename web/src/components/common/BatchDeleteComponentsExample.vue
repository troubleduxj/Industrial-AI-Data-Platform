<!--
批量删除UI组件使用示例
展示 BatchDeleteButton 和 BatchDeleteConfirmDialog 组件的集成使用
-->
<template>
  <div class="batch-delete-components-example">
    <n-card title="批量删除UI组件示例" class="mb-4">
      <template #header-extra>
        <n-space>
          <n-button type="primary" :loading="loading" @click="loadMockData"> 加载数据 </n-button>

          <!-- 批量删除按钮组件 -->
          <batch-delete-button
            :selected-items="selectedItems"
            :selected-count="selectedCount"
            resource-name="测试项目"
            :exclude-condition="excludeCondition"
            permission="test:batch_delete"
            :loading="isDeleting"
            @batch-delete="handleBatchDeleteClick"
            @validation-error="handleValidationError"
          />
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

      <!-- 批量删除确认对话框组件 -->
      <batch-delete-confirm-dialog
        v-model:visible="showConfirmDialog"
        :items="validItems"
        :invalid-items="invalidItemsWithReasons"
        :warnings="confirmWarnings"
        resource-name="测试项目"
        :confirm-loading="isDeleting"
        :before-confirm="beforeConfirm"
        @confirm="handleConfirmDelete"
        @cancel="handleCancelDelete"
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
import { ref, h, computed, onMounted } from 'vue'
import { NCard, NButton, NSpace, NDataTable, NAlert, NText, NTag, useMessage } from 'naive-ui'
import { BatchDeleteButton, BatchDeleteConfirmDialog } from '@/components/common'

defineOptions({ name: 'BatchDeleteComponentsExample' })

const message = useMessage()
const tableRef = ref(null)
const loading = ref(false)
const isDeleting = ref(false)
const tableData = ref([])
const selectedItems = ref([])
const selectedRowKeys = ref([])
const showConfirmDialog = ref(false)
const lastOperation = ref(null)

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

// 计算属性
const selectedCount = computed(() => selectedItems.value.length)

// 排除条件：系统类型的项目不能删除
const excludeCondition = (item) => {
  return item.type === 'system'
}

// 有效项目（可以删除的）
const validItems = computed(() => {
  return selectedItems.value.filter((item) => !excludeCondition(item))
})

// 无效项目（不能删除的）及其原因
const invalidItemsWithReasons = computed(() => {
  return selectedItems.value
    .filter((item) => excludeCondition(item))
    .map((item) => ({
      item,
      reason: '系统保护项，不允许删除',
    }))
})

// 确认对话框警告信息
const confirmWarnings = computed(() => {
  const warnings = []

  if (invalidItemsWithReasons.value.length > 0) {
    warnings.push({
      type: 'warning',
      title: '注意',
      message: `${invalidItemsWithReasons.value.length} 个系统项目将被跳过`,
    })
  }

  if (validItems.value.length > 10) {
    warnings.push({
      type: 'info',
      title: '提示',
      message: '批量删除大量数据可能需要较长时间，请耐心等待',
    })
  }

  return warnings
})

// 模拟批量删除API
const mockBatchDeleteApi = async (ids) => {
  console.log('调用批量删除API，IDs:', ids)

  // 模拟网络延迟
  await new Promise((resolve) => setTimeout(resolve, 2000))

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
    } else if (Math.random() < 0.15) {
      // 15% 概率失败
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

// 处理选择变化
const handleSelectionChange = (keys) => {
  const items = tableData.value.filter((item) => keys.includes(item.id))
  selectedItems.value = items
  selectedRowKeys.value = keys
}

// 处理批量删除按钮点击
const handleBatchDeleteClick = (data) => {
  console.log('批量删除按钮点击:', data)
  showConfirmDialog.value = true
}

// 处理验证错误
const handleValidationError = (error) => {
  console.log('验证错误:', error)
  message.warning(error.message)
}

// 确认前的自定义验证
const beforeConfirm = async (data) => {
  console.log('确认前验证:', data)

  // 可以在这里添加额外的验证逻辑
  if (data.validItems.length === 0) {
    message.warning('没有可删除的项目')
    return false
  }

  return true
}

// 处理确认删除
const handleConfirmDelete = async (data) => {
  console.log('确认删除:', data)

  try {
    isDeleting.value = true

    // 提取有效项目的ID
    const ids = validItems.value.map((item) => item.id)

    // 调用批量删除API
    const response = await mockBatchDeleteApi(ids)

    // 处理响应
    if (response && response.success) {
      const { data: responseData } = response
      const deletedCount = responseData?.deleted_count || 0
      const failedItems = responseData?.failed_items || []
      const skippedItems = responseData?.skipped_items || []

      // 记录操作结果
      lastOperation.value = {
        success: true,
        deletedCount,
        failedItems,
        skippedItems,
        totalAttempted: validItems.value.length,
      }

      // 显示结果消息
      if (failedItems.length > 0 || skippedItems.length > 0) {
        const failedCount = failedItems.length + skippedItems.length
        const successCount = deletedCount

        message.warning(
          `批量删除完成：成功删除 ${successCount} 个，失败 ${failedCount} 个测试项目`,
          { duration: 5000 }
        )
      } else {
        message.success(`成功删除 ${deletedCount} 个测试项目`)
      }

      // 清除选择并刷新数据
      selectedItems.value = []
      selectedRowKeys.value = []
      showConfirmDialog.value = false

      // 刷新数据
      await loadMockData()
    } else {
      throw new Error(response?.message || '批量删除测试项目失败')
    }
  } catch (error) {
    console.error('批量删除失败:', error)

    // 记录失败结果
    lastOperation.value = {
      success: false,
      error: error.message || '未知错误',
      totalAttempted: validItems.value.length,
    }

    message.error(`批量删除测试项目失败：${error.message || '网络错误'}`)
  } finally {
    isDeleting.value = false
  }
}

// 处理取消删除
const handleCancelDelete = () => {
  console.log('取消删除')
  showConfirmDialog.value = false
}

// 获取操作结果摘要
const getOperationSummary = () => {
  if (!lastOperation.value) return ''

  const { success, deletedCount, failedItems, skippedItems, error, totalAttempted } =
    lastOperation.value

  if (!success) {
    return `删除失败：${error}`
  }

  const failedCount = (failedItems?.length || 0) + (skippedItems?.length || 0)

  if (failedCount > 0) {
    return `部分成功：删除了 ${deletedCount}/${totalAttempted} 个测试项目`
  }

  return `全部成功：删除了 ${deletedCount} 个测试项目`
}

// 获取失败项目详情
const getFailedItemsDetails = () => {
  if (!lastOperation.value) return []

  const details = []

  if (lastOperation.value.failedItems) {
    details.push(
      ...lastOperation.value.failedItems.map((item) => ({
        ...item,
        type: 'failed',
      }))
    )
  }

  if (lastOperation.value.skippedItems) {
    details.push(
      ...lastOperation.value.skippedItems.map((item) => ({
        ...item,
        type: 'skipped',
      }))
    )
  }

  return details
}

// 重置操作状态
const resetOperationState = () => {
  lastOperation.value = null
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
.batch-delete-components-example {
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
