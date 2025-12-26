<script setup lang="ts">
import { h, onMounted, ref, watch, resolveDirective, withDirectives, onActivated } from 'vue'
import { NButton, NInput, NPopconfirm, NSwitch, NSelect, NForm, NFormItem } from 'naive-ui'
import { useRoute } from 'vue-router'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import BatchDeleteButton from '@/components/common/BatchDeleteButton.vue'
import PermissionButton from '@/components/Permission/PermissionButton.vue'

import { formatDateTime, renderIcon } from '@/utils'
import { useCRUD } from '@/composables/useCRUD'
import { useDictDataBatchDelete } from '@/composables/useBatchDelete'
import systemV2Api from '@/api/system-v2'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '字典数据管理' })

const route = useRoute()
const $table = ref<any>(null)
const queryItems = ref<Record<string, any>>({})
const dictTypeId = ref<string | number | null>(null)
const dictTypeName = ref<string>('')
const vPermission = resolveDirective('permission')

// 字典类型选择器数据
const dictTypeOptions = ref<any[]>([])

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
  name: '字典数据',
  initForm: {
    dict_type_id: null,
    data_label: null,
    data_value: null,
    sort_order: 0,
    is_enabled: true,
  },
  doCreate: systemV2Api.createDictData,
  doUpdate: systemV2Api.updateDictData,
  doDelete: systemV2Api.deleteDictData,
  refresh: () => $table.value?.handleSearch(),
})

// 批量删除功能
const {
  selectedItems,
  selectedRowKeys,
  isLoading: batchDeleteLoading,
  setSelectedItems,
  handleBatchDelete,
  clearSelection,
} = useDictDataBatchDelete({
  batchDeleteApi: systemV2Api.batchDeleteDictData,
  refresh: () => $table.value?.handleSearch(),
  validateItem: (item) => {
    // 字典数据通常没有特殊的删除限制，但可以在这里添加业务规则
    // 例如：检查是否被其他系统组件引用
    return { valid: true }
  },
})

onMounted(async () => {
  // 从路由参数获取dictTypeId
  if (route.query.dictTypeId) {
    dictTypeId.value = parseInt(route.query.dictTypeId)
    dictTypeName.value = route.query.dictTypeName || ''
    queryItems.value.dict_type_id = dictTypeId.value
    modalForm.value.dict_type_id = dictTypeId.value // 设置默认字典类型ID
  }

  // 加载字典类型选项
  await loadDictTypeOptions()

  $table.value?.handleSearch()
})

onActivated(async () => {
  // 从路由参数获取dictTypeId
  if (route.query.dictTypeId) {
    dictTypeId.value = parseInt(route.query.dictTypeId)
    dictTypeName.value = route.query.dictTypeName || ''
    queryItems.value.dict_type_id = dictTypeId.value
    modalForm.value.dict_type_id = dictTypeId.value // 设置默认字典类型ID
  }

  // 加载字典类型选项
  await loadDictTypeOptions()

  $table.value?.handleSearch()
})

// 监听dictTypeId变化，用于当用户直接通过URL参数切换字典类型时
watch(
  () => route.query.dictTypeId,
  (newId) => {
    if (newId) {
      dictTypeId.value = parseInt(newId)
      dictTypeName.value = route.query.dictTypeName || ''
      queryItems.value.dict_type_id = dictTypeId.value
      modalForm.value.dict_type_id = dictTypeId.value
      $table.value?.handleSearch()
    }
  }
)

async function loadDictTypeOptions() {
  try {
    const res = await systemV2Api.getDictTypeList({ page: 1, page_size: 100 })
    
    // 兼容多种返回结构
    let items = []
    if (res.data && Array.isArray(res.data.items)) {
      items = res.data.items
    } else if (res.items && Array.isArray(res.items)) {
      items = res.items
    } else if (res.data && Array.isArray(res.data.data)) {
      items = res.data.data
    } else if (res.data && Array.isArray(res.data)) {
      items = res.data
    } else if (Array.isArray(res)) {
      items = res
    }

    if (items.length > 0) {
      dictTypeOptions.value = items.map((item) => ({
        label: item.type_name,
        value: item.id,
      }))
    }
  } catch (error) {
    console.error('加载字典类型选项失败:', error)
  }
}

// 表格列配置 - 参照系统参数管理页面的表格模式
const columns = [
  { type: 'selection', fixed: 'left', width: 50 },
  { title: 'ID', key: 'id', width: 80, align: 'center', ellipsis: { tooltip: true } },
  {
    title: '所属字典类型',
    key: 'dict_type_id',
    width: 200,
    ellipsis: { tooltip: true },
    render(row) {
      const type = dictTypeOptions.value.find((opt) => opt.value === row.dict_type_id)
      return type ? type.label : '未知类型'
    },
  },
  { title: '数据标签', key: 'data_label', width: 150, ellipsis: { tooltip: true } },
  { title: '数据值', key: 'data_value', width: 150, ellipsis: { tooltip: true } },
  { title: '排序', key: 'sort_order', width: 100, align: 'center' },
  {
    title: '是否启用',
    key: 'is_enabled',
    width: 100,
    align: 'center',
    render(row) {
      return h(NSwitch, {
        size: 'small',
        rubberBand: false,
        value: row.is_enabled,
        onUpdateValue: (val) => handleUpdateEnabled(row, val),
      })
    },
  },
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
            permission: 'PUT /api/v2/dict/data/{id}',
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
            permission: 'DELETE /api/v2/dict/data/{id}',
            size: 'small',
            type: 'error',
            needConfirm: true,
            confirmTitle: '删除确认',
            confirmContent: '确定删除该字典数据吗？此操作不可恢复。',
            onConfirm: () => handleDelete({ data_id: row.id }, false),
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

const getDictDataListData = async (params) => {
  const res = await systemV2Api.getDictDataList({
    ...params,
    page: params.page || 1,
    page_size: params.page_size || 10,
    dict_type_id: dictTypeId.value, // 确保筛选条件包含字典类型ID
    ...(queryItems.value.data_label && { data_label: queryItems.value.data_label }),
    ...(queryItems.value.data_value && { data_value: queryItems.value.data_value }),
  })
  return {
    data: res.data,
    total: res.total,
  }
}

async function handleUpdateEnabled(row, val) {
  // 检查权限
  if (!window.$permission?.hasPermission({ action: 'update', resource: 'dict_data' })) {
    window.$message?.error('没有权限执行此操作')
    return
  }

  row.is_enabled = val
  try {
    await systemV2Api.updateDictData(row.id, { is_enabled: val })
    window.$message?.success('状态更新成功')
  } catch (error) {
    console.error('状态更新失败:', error)
    // 检查错误是否已经被HTTP拦截器处理过，避免重复提示
    if (!(error && typeof error === 'object' && error.success === false)) {
      window.$message?.error('状态更新失败')
    }
    row.is_enabled = !val // 恢复原状态
  }
}

// 处理选择变化
const handleSelectionChange = (keys, rows) => {
  setSelectedItems(rows || [], keys || [])
}

// 监听字典类型变化，清除选择状态
watch(dictTypeId, () => {
  clearSelection()
})

const validateDictData = {
  dict_type_id: [
    {
      required: true,
      message: '请选择所属字典类型',
      trigger: ['input', 'blur'],
      type: 'number',
    },
  ],
  data_label: [
    {
      required: true,
      message: '请输入数据标签',
      trigger: ['input', 'blur'],
    },
  ],
  data_value: [
    {
      required: true,
      message: '请输入数据值',
      trigger: ['input', 'blur'],
    },
  ],
}
</script>

<template>
  <CommonPage
    show-footer
    :title="dictTypeName ? `字典数据管理 (${dictTypeName})` : '字典数据管理'"
    class="system-dict-data-page system-management-page standard-page"
  >
    <template #action>
      <div class="flex items-center gap-3">
        <BatchDeleteButton
          :selected-items="selectedItems"
          :selected-count="selectedRowKeys.length"
          resource-name="字典数据"
          permission="dict_data:batch_delete"
          :loading="batchDeleteLoading"
          @batch-delete="handleBatchDelete"
        />
        <PermissionButton permission="POST /api/v2/dict/data" type="primary" @click="handleAdd">
          <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建字典数据
        </PermissionButton>
      </div>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :checked-row-keys="selectedRowKeys"
      :scroll-x="1600"
      :columns="columns"
      :get-data="getDictDataListData"
      :pagination="pagination"
      @on-page-change="handlePageChange"
      @on-page-size-change="handlePageSizeChange"
      @on-checked="handleSelectionChange"
    >
      <template #queryBar>
        <QueryBarItem label="所属类型" :label-width="70">
          <NSelect
            v-model:value="dictTypeId"
            :options="dictTypeOptions"
            placeholder="选择字典类型"
            clearable
            @update:value="
              (value) => {
                queryItems.dict_type_id = value
                modalForm.dict_type_id = value
                $table?.handleSearch()
              }
            "
          />
        </QueryBarItem>
        <QueryBarItem label="标签" :label-width="40">
          <NInput
            v-model:value="queryItems.data_label"
            clearable
            type="text"
            placeholder="请输入数据标签"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="值" :label-width="40">
          <NInput
            v-model:value="queryItems.data_value"
            clearable
            type="text"
            placeholder="请输入数据值"
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
        :rules="validateDictData"
      >
        <NFormItem label="所属字典类型" path="dict_type_id">
          <NSelect
            v-model:value="modalForm.dict_type_id"
            :options="dictTypeOptions"
            placeholder="请选择所属字典类型"
            :disabled="!!dictTypeId"
          />
        </NFormItem>
        <NFormItem label="数据标签" path="data_label">
          <NInput v-model:value="modalForm.data_label" clearable placeholder="请输入数据标签" />
        </NFormItem>
        <NFormItem label="数据值" path="data_value">
          <NInput v-model:value="modalForm.data_value" clearable placeholder="请输入数据值" />
        </NFormItem>
        <NFormItem label="排序" path="sort_order">
          <NInput
            v-model:value="modalForm.sort_order"
            clearable
            type="number"
            placeholder="请输入排序值"
          />
        </NFormItem>
        <NFormItem label="是否启用" path="is_enabled">
          <NSwitch v-model:value="modalForm.is_enabled" />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
