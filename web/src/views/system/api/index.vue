<script setup lang="ts">
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NPopconfirm,
  NSelect,
  NTag,
  useMessage,
  useDialog,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import BatchDeleteButton from '@/components/common/BatchDeleteButton.vue'
import PermissionButton from '@/components/Permission/PermissionButton.vue'

import { renderIcon } from '@/utils'
import { useCRUD } from '@/composables/useCRUD'
import { useApiBatchDelete } from '@/composables/useBatchDelete'
// import { loginTypeMap, loginTypeOptions } from '@/constant/data'
import systemV2Api from '@/api/system-v2'

defineOptions({ name: 'API管理' })

const $table = ref<any>(null)
const queryItems = ref<Record<string, any>>({})
const vPermission = resolveDirective('permission')
const $message = useMessage()
const $dialog = useDialog()

// 分页状态
const pagination = ref({
  page: 1,
  pageSize: 10,
})

// 处理分页变化
const handlePageChange = (page) => {
  pagination.value.page = page
}

const handlePageSizeChange = (pageSize) => {
  pagination.value.pageSize = pageSize
  pagination.value.page = 1 // 重置到第一页
}

// 批量删除功能
const {
  selectedItems,
  selectedRowKeys,
  selectedCount,
  isLoading: batchDeleteLoading,
  setSelectedItems,
  clearSelection,
  handleBatchDelete,
} = useApiBatchDelete({
  batchDeleteApi: systemV2Api.batchDeleteApis,
  refresh: () => $table.value?.handleSearch(),
  validateItem: (item) => {
    // API验证逻辑：检查是否为系统内置API
    if (item.is_system || item.system_api) {
      return { valid: false, reason: '系统内置API不允许删除' }
    }
    return { valid: true }
  },
})

// 处理表格选择变化
const handleTableSelection = (rowKeys, rows) => {
  setSelectedItems(rows || [], rowKeys || [])
}

const {
  modalVisible,
  modalAction,
  modalTitle,
  modalLoading,
  handleAdd: originalHandleAdd,
  handleDelete,
  handleEdit: originalHandleEdit,
  handleSave,
  modalForm,
  modalFormRef,
} = useCRUD({
  name: 'API',
  initForm: { group_id: null },
  doCreate: systemV2Api.createApi,
  doUpdate: (data) => systemV2Api.updateApi(data.id, data),
  doDelete: systemV2Api.deleteApi,
  refresh: () => $table.value?.handleSearch(),
})

// 自定义编辑处理函数，确保分组数据已加载
const handleEdit = async (row) => {
  // 确保分组数据已加载
  if (groupOptions.value.length === 0) {
    await loadApiGroups()
  }
  originalHandleEdit(row)
  // 设置角色数据（如果存在）
  if (row.roles) {
    modalForm.value.roles = row.roles.map((e) => e.id)
  }
}

// 自定义新增处理函数，确保分组数据已加载
const handleAdd = async () => {
  // 确保分组数据已加载
  if (groupOptions.value.length === 0) {
    await loadApiGroups()
  }
  originalHandleAdd()
}

// 自定义保存处理函数，确保保存后刷新表格
const handleSaveWithRefresh = async () => {
  await handleSave()
  // 保存成功后刷新表格数据，确保分组信息正确显示
  $table.value?.handleSearch()
}

const groupOptions = ref([])

// HTTP方法选项
const methodOptions = [
  { label: 'GET', value: 'GET' },
  { label: 'POST', value: 'POST' },
  { label: 'PUT', value: 'PUT' },
  { label: 'DELETE', value: 'DELETE' },
  { label: 'PATCH', value: 'PATCH' },
]

// 加载API分组数据
const loadApiGroups = async () => {
  try {
    const response = await systemV2Api.getAllApiGroups()

    // 处理响应数据，兼容不同的数据结构
    let apiGroups = []
    if (response && response.success && response.data) {
      apiGroups = Array.isArray(response.data) ? response.data : []
    } else if (response && Array.isArray(response)) {
      // 兼容直接返回数组的情况
      apiGroups = response
    } else if (response && response.data && Array.isArray(response.data)) {
      // 兼容嵌套data的情况
      apiGroups = response.data
    }

    if (apiGroups.length > 0) {
      groupOptions.value = apiGroups.map((group) => ({
        label: group.group_name || group.name,
        value: group.id,
      }))
    } else {
      console.warn('未获取到API分组数据')
      groupOptions.value = []
    }
  } catch (error) {
    console.error('加载API分组失败:', error)
    groupOptions.value = []
  }
}

// 清除选择状态（在数据刷新时）
const handleDataRefresh = () => {
  clearSelection()
  $table.value?.handleSearch()
}

onMounted(() => {
  loadApiGroups()
  handleDataRefresh()
})

async function handleRefreshApi() {
  await $dialog.confirm({
    title: '提示',
    type: 'warning',
    content: '此操作会根据后端 app.routes 进行路由更新，确定继续刷新 API 操作？',
    async confirm() {
      await systemV2Api.refreshApi()
      $message.success('刷新完成')
      clearSelection()
      $table.value?.handleSearch()
    },
  })
}

const addAPIRules = {
  path: [
    {
      required: true,
      message: '请输入API路径',
      trigger: ['input', 'blur', 'change'],
    },
  ],
  method: [
    {
      required: true,
      message: '请输入请求方式',
      trigger: ['input', 'blur', 'change'],
    },
  ],
  summary: [
    {
      required: true,
      message: '请输入API简介',
      trigger: ['input', 'blur', 'change'],
    },
  ],
  tags: [
    {
      required: true,
      message: '请输入Tags',
      trigger: ['input', 'blur', 'change'],
    },
  ],
}

// 表格列配置 - 参照系统参数管理页面的表格模式
const columns = [
  { type: 'selection', fixed: 'left', width: 50 },
  { title: 'API路径', key: 'path', width: 300, ellipsis: { tooltip: true } },
  {
    title: '请求方式',
    key: 'method',
    width: 100,
    align: 'center',
    render(row) {
      const methodColors = {
        GET: 'success',
        POST: 'info',
        PUT: 'warning',
        DELETE: 'error',
        PATCH: 'default',
      }
      return h(
        NTag,
        {
          type: methodColors[row.method] || 'default',
          size: 'small',
        },
        { default: () => row.method }
      )
    },
  },
  { title: 'API简介', key: 'summary', width: 250, ellipsis: { tooltip: true } },
  { title: 'Tags', key: 'tags', width: 150, ellipsis: { tooltip: true } },
  { title: 'API分组', key: 'group_name', width: 150, ellipsis: { tooltip: true } },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    align: 'center',
    fixed: 'right',
    hideInExcel: true,
    render: (row) => {
      return [
        h(
          PermissionButton,
          {
            permission: 'PUT /api/v2/apis/{id}',
            size: 'small',
            type: 'primary',
            style: 'margin-right: 8px;',
            onClick: () => handleEdit(row),
          },
          {
            default: () => '编辑',
            icon: renderIcon('material-symbols:edit', { size: 16 }),
          }
        ),
        h(
          PermissionButton,
          {
            permission: 'DELETE /api/v2/apis/{id}',
            size: 'small',
            type: 'error',
            style: 'margin-right: 8px;',
            needConfirm: true,
            confirmTitle: '删除确认',
            confirmContent: '确定删除该API吗？此操作不可恢复。',
            onConfirm: () => handleDelete({ api_id: row.id }, false),
          },
          {
            default: () => '删除',
            icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
          }
        ),
      ]
    },
  },
]
</script>

<template>
  <!-- 业务页面 -->
  <CommonPage
    show-footer
    title="API列表"
    class="system-api-page system-management-page standard-page"
  >
    <template #action>
      <div class="flex items-center gap-3">
        <BatchDeleteButton
          :selected-items="selectedItems"
          :selected-count="selectedCount"
          resource-name="API"
          permission="api:batch_delete"
          :loading="batchDeleteLoading"
          :exclude-condition="(item) => item.is_system || item.system_api"
          @batch-delete="handleBatchDelete"
        />
        <PermissionButton permission="POST /api/v2/apis" type="primary" @click="handleAdd">
          <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建API
        </PermissionButton>
        <PermissionButton
          permission="POST /api/v2/apis/refresh"
          type="warning"
          @click="handleRefreshApi"
        >
          <TheIcon icon="material-symbols:refresh" :size="18" class="mr-5" />刷新API
        </PermissionButton>
      </div>
    </template>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      v-model:checked-row-keys="selectedRowKeys"
      :scroll-x="1500"
      :columns="columns"
      :get-data="systemV2Api.getApiList"
      :pagination="pagination"
      @on-page-change="handlePageChange"
      @on-page-size-change="handlePageSizeChange"
      @on-checked="handleTableSelection"
    >
      <template #queryBar>
        <QueryBarItem label="路径" :label-width="40">
          <NInput
            v-model:value="queryItems.path"
            clearable
            type="text"
            placeholder="请输入API路径"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="API简介" :label-width="70">
          <NInput
            v-model:value="queryItems.summary"
            clearable
            type="text"
            placeholder="请输入API简介"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="Tags" :label-width="40">
          <NInput
            v-model:value="queryItems.tags"
            clearable
            type="text"
            placeholder="请输入API模块"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="API分组" :label-width="70">
          <NSelect
            v-model:value="queryItems.group_id"
            :options="groupOptions"
            placeholder="请选择API分组"
            clearable
            @update:value="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <!-- 新增/编辑 弹窗 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      @save="handleSaveWithRefresh"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="80"
        :model="modalForm"
        :rules="addAPIRules"
      >
        <NFormItem label="API名称" path="path">
          <NInput v-model:value="modalForm.path" clearable placeholder="请输入API路径" />
        </NFormItem>
        <NFormItem label="请求方式" path="method">
          <NSelect
            v-model:value="modalForm.method"
            :options="methodOptions"
            placeholder="请选择请求方式"
            clearable
          />
        </NFormItem>
        <NFormItem label="API简介" path="summary">
          <NInput v-model:value="modalForm.summary" clearable placeholder="请输入API简介" />
        </NFormItem>
        <NFormItem label="Tags" path="tags">
          <NInput v-model:value="modalForm.tags" clearable placeholder="请输入Tags" />
        </NFormItem>
        <NFormItem label="API分组" path="group_id">
          <NSelect
            v-model:value="modalForm.group_id"
            :options="groupOptions"
            placeholder="请选择API分组"
            clearable
          />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
