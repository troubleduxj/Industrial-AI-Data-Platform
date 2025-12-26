<template>
  <CommonPage
    show-footer
    title="API分组管理"
    class="system-api-groups-page system-management-page standard-page"
  >
    <template #action>
      <div class="flex items-center gap-3">
        <BatchDeleteButton
          :selected-items="selectedItems"
          :selected-count="selectedCount"
          resource-name="API分组"
          permission="sys:api_group:delete"
          :exclude-condition="(group) => group.is_system || group.api_count > 0"
          :loading="batchDeleteLoading"
          @batch-delete="handleBatchDelete"
        />

        <NButton v-permission="['sys:api_group:create']" type="primary" @click="handleAdd">
          <TheIcon icon="material-symbols:add" :size="18" class="mr-1" />
          新增分组
        </NButton>
      </div>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      v-model:checked-row-keys="selectedRowKeys"
      :extra-params="extraParams"
      :columns="columns"
      :get-data="systemV2Api.getApiGroupList"
      :pagination="pagination"
      :scroll-x="1200"
      @on-page-change="handlePageChange"
      @on-page-size-change="handlePageSizeChange"
      @on-checked="handleTableSelection"
    >
      <template #queryBar>
        <QueryBarItem label="分组名称" :label-width="80">
          <NInput
            v-model:value="queryItems.search"
            type="text"
            placeholder="请输入分组名称"
            clearable
            class="w-200px"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <!-- 新增/编辑分组弹窗 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      :show-footer="true"
      @save="handleSave"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="80"
        :model="modalForm"
        :rules="modalRules"
      >
        <NFormItem label="分组名称" path="group_name">
          <NInput v-model:value="modalForm.group_name" clearable placeholder="请输入分组名称" />
        </NFormItem>
        <NFormItem label="分组代码" path="group_code">
          <NInput v-model:value="modalForm.group_code" clearable placeholder="请输入分组代码" />
        </NFormItem>
        <NFormItem label="分组描述" path="description">
          <NInput
            v-model:value="modalForm.description"
            type="textarea"
            :rows="3"
            clearable
            placeholder="请输入分组描述"
          />
        </NFormItem>
      </NForm>
    </CrudModal>

    <!-- 批量移动API弹窗 -->
    <NModal v-model:show="moveApiModalVisible" preset="dialog" title="批量移动API">
      <div class="space-y-4">
        <div>
          <div class="mb-2 text-sm text-gray-600">
            选择要移动到分组 "{{ currentGroup?.group_name }}" 的API：
          </div>
          <NTransfer
            v-model:value="selectedApiIds"
            :options="apiOptions"
            :render-source-label="renderApiLabel"
            :render-target-label="renderApiLabel"
            source-title="可选API"
            target-title="已选API"
          />
        </div>
      </div>
      <template #action>
        <NSpace>
          <NButton @click="moveApiModalVisible = false">取消</NButton>
          <NButton type="primary" :loading="moveApiLoading" @click="handleMoveApis">
            确认移动
          </NButton>
        </NSpace>
      </template>
    </NModal>

    <!-- 操作结果对话框 -->
    <NModal
      v-model:show="operationResult.visible"
      :mask-closable="false"
      preset="card"
      :style="{ maxWidth: '600px', width: '90%' }"
      :title="operationResult.title"
      size="medium"
      :bordered="false"
      segmented
    >
      <template #header-extra>
        <NButton quaternary circle size="small" @click="closeOperationResult">
          <TheIcon icon="material-symbols:close" :size="18" />
        </NButton>
      </template>

      <!-- 操作结果内容 -->
      <div class="space-y-4">
        <!-- 主要消息 -->
        <NAlert :type="operationResult.type" :show-icon="true" :closable="false">
          {{ operationResult.message }}
        </NAlert>

        <!-- 详细信息 -->
        <div v-if="operationResult.details.length > 0" class="space-y-3">
          <div v-for="(detail, index) in operationResult.details" :key="index">
            <div class="mb-2 flex items-center">
              <TheIcon
                :icon="getDetailIcon(detail.type)"
                :size="16"
                :class="getDetailIconClass(detail.type)"
                class="mr-2"
              />
              <span class="text-gray-700 font-medium">{{ detail.title }}</span>
            </div>

            <NList bordered class="rounded-md">
              <NListItem v-for="(item, itemIndex) in detail.items" :key="itemIndex">
                <div class="w-full flex items-center justify-between">
                  <div class="flex items-center">
                    <span class="font-medium">{{ item.name }}</span>
                    <NTag
                      v-if="item.type"
                      :type="item.type === 'soft' ? 'warning' : 'error'"
                      size="small"
                      class="ml-2"
                    >
                      {{ item.type === 'soft' ? '软删除' : '永久删除' }}
                    </NTag>
                  </div>
                  <span v-if="item.reason" class="text-sm text-gray-500">{{ item.reason }}</span>
                </div>
              </NListItem>
            </NList>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <template #footer>
        <NSpace justify="end">
          <NButton @click="closeOperationResult"> 关闭 </NButton>
          <NButton
            v-if="operationResult.type === 'success'"
            type="primary"
            @click="closeOperationResult"
          >
            确定
          </NButton>
        </NSpace>
      </template>
    </NModal>
  </CommonPage>
</template>

<script setup lang="ts">
import { h, onMounted, ref, computed, resolveDirective, withDirectives } from 'vue'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NPopconfirm,
  NModal,
  NSpace,
  NTransfer,
  NTag,
  NAlert,
  NList,
  NListItem,
  NDivider,
  NText,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import BatchDeleteButton from '@/components/common/BatchDeleteButton.vue'

import { useCRUD } from '@/composables/useCRUD'
import { useApiGroupBatchDelete } from '@/composables/useBatchDelete'
import { systemV2Api } from '@/api'
import { renderIcon } from '@/utils'

defineOptions({ name: 'ApiGroupManagement' })

const $table = ref(null)
const queryItems = ref({})
const extraParams = ref({})

// 操作结果对话框状态
const operationResult = ref({
  visible: false,
  type: 'success', // 'success' | 'warning' | 'error'
  title: '',
  message: '',
  details: [], // 详细信息数组
})

// 批量删除组合式函数
const {
  selectedItems,
  selectedRowKeys,
  selectedCount,
  isLoading: batchDeleteLoading,
  handleBatchDelete: originalHandleBatchDelete,
  executeBatchDelete,
  setSelectedItems,
  clearSelection,
} = useApiGroupBatchDelete({
  batchDeleteApi: systemV2Api.batchDeleteApiGroups,
  refresh: () => $table.value?.handleSearch(),
  excludeCondition: (item) => item.id === 1, // 默认分组不能删除
})

// 显示批量删除确认对话框（与部门管理页面样式一致）
function showBatchDeleteConfirmation(selectedItems, excludeCondition) {
  return new Promise((resolve) => {
    const validItems = excludeCondition
      ? selectedItems.filter((item) => !excludeCondition(item))
      : selectedItems
    const invalidItems = excludeCondition
      ? selectedItems.filter((item) => excludeCondition(item))
      : []

    if (validItems.length === 0) {
      if (invalidItems.length > 0) {
        window.$message?.warning('选中的API分组包含系统保护项，无法删除', { duration: 6000 })
      } else {
        window.$message?.warning('请选择要删除的API分组')
      }
      resolve(false)
      return
    }

    let content = `确定要删除选中的 ${validItems.length} 个API分组吗？`

    if (invalidItems.length > 0) {
      const protectedNames = invalidItems.map((item) => item.name || `分组${item.id}`).slice(0, 3)
      const moreCount = invalidItems.length > 3 ? invalidItems.length - 3 : 0
      const protectedSummary = `以下API分组为系统保护项，将跳过删除：\n${protectedNames.join(
        '、'
      )}${moreCount > 0 ? ` 等${moreCount}个` : ''}`
      content += `\n\n${protectedSummary}`
    }

    window.$dialog?.warning({
      title: '批量删除API分组',
      content,
      positiveText: '确定删除',
      negativeText: '取消',
      onPositiveClick: () => resolve(true),
      onNegativeClick: () => resolve(false),
      onMaskClick: () => resolve(false),
    })
  })
}

// 自定义批量删除处理函数
const handleBatchDelete = async () => {
  try {
    // 显示确认对话框
    const confirmed = await showBatchDeleteConfirmation(
      selectedItems.value,
      (item) => item.id === 1
    )
    if (!confirmed) {
      return
    }

    // 直接执行删除操作，跳过内置确认对话框
    await executeBatchDelete()
  } catch (error) {
    console.error('批量删除失败:', error)
    displayBatchDeleteError(error, selectedRowKeys.value)
  }
}

// 显示操作结果对话框
function showOperationResult(type, title, message, details = [], autoClose = false) {
  operationResult.value = {
    visible: true,
    type,
    title,
    message,
    details,
  }

  if (autoClose) {
    setTimeout(() => {
      closeOperationResult()
    }, 3000)
  }
}

// 关闭操作结果对话框
function closeOperationResult() {
  operationResult.value.visible = false
}

// 处理批量删除成功
function handleBatchDeleteSuccess(result, attemptedIds) {
  console.log('批量删除成功:', result)

  const data = result.data || {}
  const deletedGroups = data.deleted || []
  const failedGroups = data.failed || []
  const totalDeleted = data.deleted_count || deletedGroups.length
  const totalFailed = data.failed_count || failedGroups.length

  // 构建成功消息
  let successMessage = `成功删除 ${totalDeleted} 个API分组`

  // 准备详细信息
  const details = []

  // 成功删除的分组
  if (deletedGroups.length > 0) {
    details.push({
      type: 'success',
      title: '成功删除的分组',
      items: deletedGroups.map((group) => ({
        name: group.group_name || group.name || `分组${group.id}`,
        id: group.id,
      })),
    })
  }

  // 如果有部分失败的情况
  if (failedGroups.length > 0) {
    details.push({
      type: 'warning',
      title: '删除失败的分组',
      items: failedGroups.map((group) => ({
        name: group.group_name || group.name || `分组${group.id}`,
        reason: group.reason || '可能包含关联的API',
      })),
    })

    // 显示警告类型的结果
    showOperationResult('warning', '批量删除部分成功', successMessage, details, false)
  } else {
    // 完全成功
    showOperationResult('success', '批量删除成功', successMessage, details, true)
  }

  // 清空选择并刷新列表
  clearSelection()
  $table.value?.handleSearch()
}

// 显示批量删除错误
function displayBatchDeleteError(errorInfo, attemptedIds) {
  console.error('批量删除错误详情:', errorInfo)

  let errorMessage = errorInfo.message || '批量删除操作失败'
  const details = []

  // 如果有详细错误信息
  if (errorInfo.details && errorInfo.details.length > 0) {
    const errorsByType = {}
    errorInfo.details.forEach((detail) => {
      if (!errorsByType[detail.code]) {
        errorsByType[detail.code] = []
      }
      errorsByType[detail.code].push(detail)
    })

    Object.entries(errorsByType).forEach(([code, errors]) => {
      let title = ''
      let items = []

      switch (code) {
        case 'HAS_APIS':
          title = '包含API的分组'
          items = errors.map((error) => ({
            name: error.field || `分组${error.value}`,
            reason: '该分组包含API，请先移除或删除相关API',
          }))
          break
        case 'DEFAULT_GROUP':
          title = '默认分组'
          items = errors.map((error) => ({
            name: error.field || `分组${error.value}`,
            reason: '默认分组不能删除',
          }))
          break
        default:
          title = '其他错误'
          items = errors.map((error) => ({
            name: error.field || `分组${error.value}`,
            reason: error.message || '未知错误',
          }))
      }

      if (items.length > 0) {
        details.push({ type: 'error', title, items })
      }
    })
  }

  showOperationResult('error', '批量删除失败', errorMessage, details, false)
}

// 获取详细信息图标
function getDetailIcon(type) {
  switch (type) {
    case 'success':
      return 'material-symbols:check-circle-outline'
    case 'warning':
      return 'material-symbols:warning-outline'
    case 'error':
      return 'material-symbols:error-outline'
    default:
      return 'material-symbols:info-outline'
  }
}

// 获取详细信息图标样式
function getDetailIconClass(type) {
  switch (type) {
    case 'success':
      return 'text-green-500'
    case 'warning':
      return 'text-orange-500'
    case 'error':
      return 'text-red-500'
    default:
      return 'text-blue-500'
  }
}

// 分页配置
const pagination = ref({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  showQuickJumper: true,
  prefix: ({ itemCount }) => `共 ${itemCount} 条`,
  suffix: ({ startIndex, endIndex }) => `显示 ${startIndex}-${endIndex} 条`,
})

// 分页事件处理
const handlePageChange = (page) => {
  console.log('API分组页面 - 页码变化:', page)
  pagination.value.page = page
}

const handlePageSizeChange = (pageSize) => {
  console.log('API分组页面 - 页大小变化:', pageSize)
  pagination.value.page = 1
  pagination.value.pageSize = pageSize
}

// 批量移动API相关
const moveApiModalVisible = ref(false)
const moveApiLoading = ref(false)
const currentGroup = ref(null)
const selectedApiIds = ref([])
const apiOptions = ref([])

// 渲染API标签
const renderApiLabel = ({ option }) => {
  return h('div', { class: 'flex items-center space-x-2' }, [
    h(NTag, { type: 'info', size: 'small' }, { default: () => option.method }),
    h('span', option.label),
  ])
}

// 加载所有API数据
const loadAllApis = async () => {
  try {
    const response = await systemV2Api.getApiList({ page: 1, page_size: 1000 })
    if (response.success) {
      apiOptions.value = response.data.map((api) => ({
        label: `${api.path} - ${api.summary}`,
        value: api.id,
        method: api.method,
        path: api.path,
        summary: api.summary,
      }))
    }
  } catch (error) {
    console.error('加载API列表失败:', error)
  }
}

// 处理批量移动API
const handleMoveApis = async () => {
  if (!selectedApiIds.value.length) {
    window.$message?.warning('请选择要移动的API')
    return
  }

  moveApiLoading.value = true
  try {
    const response = await systemV2Api.moveApisToGroup(currentGroup.value.id, selectedApiIds.value)
    if (response.success) {
      window.$message?.success(`成功移动 ${response.data.updated_count} 个API到分组`)
      moveApiModalVisible.value = false
      selectedApiIds.value = []
      $table.value?.handleSearch()
    }
  } catch (error) {
    console.error('移动API失败:', error)
  } finally {
    moveApiLoading.value = false
  }
}

// 打开批量移动API弹窗
const handleBatchMove = (row) => {
  currentGroup.value = row
  selectedApiIds.value = []
  loadAllApis()
  moveApiModalVisible.value = true
}

// 处理表格行选择
const handleTableSelection = (rowKeys, rows) => {
  setSelectedItems(rows || [], rowKeys || [])
}

const {
  modalVisible,
  modalAction,
  modalTitle,
  modalLoading,
  handleAdd,
  handleEdit,
  handleDelete,
  handleSave,
  modalForm,
  modalFormRef,
  handleReset,
} = useCRUD({
  name: 'API分组',
  initForm: { group_name: '', group_code: '', description: '' },
  doCreate: systemV2Api.createApiGroup,
  doUpdate: systemV2Api.updateApiGroup,
  doDelete: systemV2Api.deleteApiGroup,
  refresh: () => $table.value?.handleSearch(),
})

const modalRules = {
  group_name: [{ required: true, message: '请输入分组名称', trigger: 'blur' }],
  group_code: [
    { required: true, message: '请输入分组代码', trigger: 'blur' },
    {
      pattern: /^[a-zA-Z0-9_-]+$/,
      message: '分组代码只能包含字母、数字、下划线和横线',
      trigger: 'blur',
    },
  ],
}

const vPermission = resolveDirective('permission')

const columns = [
  {
    type: 'selection',
    minWidth: 50,
    align: 'center',
    disabled: (row) => row.id === 1, // 默认分组不能选择
  },
  {
    title: 'ID',
    key: 'id',
    minWidth: 60,
    align: 'center',
  },
  {
    title: '分组名称',
    key: 'group_name',
    minWidth: 120,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '分组代码',
    key: 'group_code',
    minWidth: 120,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '分组描述',
    key: 'description',
    minWidth: 400,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: 'API数量',
    key: 'api_count',
    minWidth: 100,
    align: 'center',
    render: (row) => {
      return h(NTag, { type: 'info' }, { default: () => row.api_count })
    },
  },
  {
    title: '创建时间',
    key: 'created_at',
    minWidth: 180,
    align: 'center',
    ellipsis: { tooltip: true },
    render: (row) => {
      return row.created_at ? new Date(row.created_at).toLocaleString() : '-'
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 180,
    align: 'center',
    fixed: 'right',
    render: (row) => {
      const buttons = [
        withDirectives(
          h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              onClick: () => handleEdit(row),
            },
            {
              default: () => '编辑',
              icon: renderIcon('material-symbols:edit', { size: 16 }),
            }
          ),
          [[vPermission, ['sys:api_group:update']]]
        ),
        row.id !== 1 &&
          withDirectives(
            h(
              NPopconfirm,
              {
                onPositiveClick: () => handleDelete(row.id),
                onNegativeClick: () => {},
              },
              {
                trigger: () =>
                  h(
                    NButton,
                    {
                      size: 'small',
                      type: 'error',
                    },
                    {
                      default: () => '删除',
                      icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
                    }
                  ),
                default: () =>
                  h('div', { style: 'max-width: 300px;' }, [
                    h(
                      'p',
                      { style: 'margin: 0 0 8px 0; font-weight: 500;' },
                      `确定删除API分组"${row.group_name}"吗？`
                    ),
                    h(
                      'p',
                      {
                        style:
                          'margin: 0; font-size: var(--font-size-xs); color: var(--text-color-secondary);',
                      },
                      '删除后将无法恢复，请谨慎操作。'
                    ),
                  ]),
              }
            ),
            [[vPermission, ['sys:api_group:delete']]]
          ),
      ].filter(Boolean)

      return h(NSpace, { size: 'small' }, { default: () => buttons })
    },
  },
]

onMounted(() => {
  $table.value?.handleSearch()
})
</script>
