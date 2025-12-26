<script setup lang="ts">
import { h, onMounted, ref, onActivated } from 'vue'
import { NButton, NInput, NPopconfirm } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import BatchDeleteButton from '@/components/common/BatchDeleteButton.vue'
import PermissionButton from '@/components/Permission/PermissionButton.vue'

import { formatDateTime, renderIcon } from '@/utils'
import { useCRUD } from '@/composables/useCRUD'
import { useDictTypeBatchDelete } from '@/composables/useBatchDelete'
import systemV2Api from '@/api/system-v2'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '字典类型管理' })

const $table = ref<any>(null)
const queryItems = ref<Record<string, any>>({})

// 分页状态管理
const pagination = ref<{ page: number; pageSize: number }>({
  page: 1,
  pageSize: 10,
})

// 分页事件处理
const handlePageChange = (page) => {
  pagination.value.page = page
}

const handlePageSizeChange = (pageSize) => {
  pagination.value.page = 1
  pagination.value.pageSize = pageSize
}

// 批量删除组合式函数
const {
  selectedItems,
  selectedRowKeys,
  selectedCount,
  isLoading: batchDeleteLoading,
  canBatchDelete,
  validCount,
  invalidCount,
  handleBatchDelete,
  setSelectedItems,
  clearSelection,
} = useDictTypeBatchDelete({
  batchDeleteApi: systemV2Api.batchDeleteDictTypes,
  refresh: () => $table.value?.handleSearch(),
  validateItem: (item) => {
    // 基本验证：检查必要字段
    if (!item.id) {
      return { valid: false, reason: '字典类型ID无效' }
    }

    // 检查是否为系统内置类型
    if (item.is_system === true || item.type_code === 'system') {
      return { valid: false, reason: '系统内置字典类型不能删除' }
    }

    return { valid: true }
  },
  excludeCondition: (item) => {
    // 排除系统内置的字典类型
    return item.is_system === true || item.type_code === 'system'
  },
})

// 处理表格行选择
const handleTableSelection = (rowKeys, rows) => {
  setSelectedItems(rows || [], rowKeys || [])
}

const {
  modalVisible,
  modalTitle,
  modalAction,
  modalLoading,
  handleSave,
  modalForm,
  modalFormRef,
  handleEdit,
  handleDelete,
  handleAdd,
} = useCRUD({
  name: '字典类型',
  initForm: {
    type_code: null,
    type_name: null,
    description: null,
  },
  doCreate: systemV2Api.createDictType,
  doUpdate: systemV2Api.updateDictType,
  doDelete: systemV2Api.deleteDictType,
  refresh: () => $table.value?.handleSearch(),
})

onMounted(() => {
  $table.value?.handleSearch()
})

onActivated(() => {
  $table.value?.handleSearch()
})

// 表格列配置 - 参照系统参数管理页面的表格模式
const columns = [
  { type: 'selection', fixed: 'left', width: 50 },
  { title: 'ID', key: 'id', width: 80, align: 'center', ellipsis: { tooltip: true } },
  { title: '字典类型编码', key: 'type_code', width: 200, ellipsis: { tooltip: true } },
  { title: '字典类型名称', key: 'type_name', width: 200, ellipsis: { tooltip: true } },
  { title: '描述', key: 'description', width: 300, ellipsis: { tooltip: true } },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return formatDateTime(row.created_at)
    },
  },
  {
    title: '更新时间',
    key: 'updated_at',
    width: 180,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return formatDateTime(row.updated_at)
    },
  },
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
            permission: 'PUT /api/v2/dict/types/{id}',
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
            permission: 'DELETE /api/v2/dict/types/{id}',
            size: 'small',
            type: 'error',
            needConfirm: true,
            confirmTitle: '删除确认',
            confirmContent: '确定删除该字典类型吗？此操作不可恢复。',
            onConfirm: () => handleDelete({ type_id: row.id }, false),
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

const getDictTypeListData = async (params) => {
  const res = await systemV2Api.getDictTypeList({
    ...params,
    page: params.page || 1,
    page_size: params.page_size || 10,
    // 可以在这里添加根据type_code或type_name进行搜索的逻辑
    ...(queryItems.value.type_code && { type_code: queryItems.value.type_code }),
    ...(queryItems.value.type_name && { type_name: queryItems.value.type_name }),
  })
  return {
    data: res.data,
    total: res.total,
  }
}

const validateDictType = {
  type_code: [
    {
      required: true,
      message: '请输入字典类型编码',
      trigger: ['input', 'blur'],
    },
  ],
  type_name: [
    {
      required: true,
      message: '请输入字典类型名称',
      trigger: ['input', 'blur'],
    },
  ],
}
</script>

<template>
  <CommonPage
    show-footer
    title="字典类型管理"
    class="system-dict-type-page system-management-page standard-page"
  >
    <template #action>
      <div class="flex items-center gap-3">
        <BatchDeleteButton
          :selected-items="selectedItems"
          :selected-count="selectedRowKeys.length"
          resource-name="字典类型"
          permission="dict_type:batch_delete"
          :loading="batchDeleteLoading"
          :exclude-condition="(item) => item.is_system === true || item.type_code === 'system'"
          @batch-delete="handleBatchDelete"
        />
        <PermissionButton permission="POST /api/v2/dict/types" type="primary" @click="handleAdd">
          <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建字典类型
        </PermissionButton>
      </div>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      v-model:checked-row-keys="selectedRowKeys"
      :scroll-x="1400"
      :columns="columns"
      :get-data="getDictTypeListData"
      :pagination="pagination"
      @on-page-change="handlePageChange"
      @on-page-size-change="handlePageSizeChange"
      @on-checked="handleTableSelection"
    >
      <template #queryBar>
        <QueryBarItem label="编码" :label-width="40">
          <NInput
            v-model:value="queryItems.type_code"
            clearable
            type="text"
            placeholder="请输入类型编码"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="名称" :label-width="40">
          <NInput
            v-model:value="queryItems.type_name"
            clearable
            type="text"
            placeholder="请输入类型名称"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      @save="handleSave"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="100"
        :model="modalForm"
        :rules="validateDictType"
      >
        <NFormItem label="字典类型编码" path="type_code">
          <NInput v-model:value="modalForm.type_code" clearable placeholder="请输入字典类型编码" />
        </NFormItem>
        <NFormItem label="字典类型名称" path="type_name">
          <NInput v-model:value="modalForm.type_name" clearable placeholder="请输入字典类型名称" />
        </NFormItem>
        <NFormItem label="描述" path="description">
          <NInput
            v-model:value="modalForm.description"
            clearable
            type="textarea"
            placeholder="请输入描述"
          />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
