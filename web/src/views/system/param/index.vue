<template>
  <CommonPage
    show-footer
    title="系统参数管理"
    class="system-param-page system-management-page standard-page"
  >
    <template #action>
      <div class="flex items-center gap-3">
        <BatchDeleteButton
          :selected-items="selectedItems"
          :selected-count="selectedCount"
          resource-name="系统参数"
          permission="system_param:batch_delete"
          :exclude-condition="(item) => item.is_system"
          @batch-delete="handleBatchDelete"
        />
        <PermissionButton permission="POST /api/v2/system/params" type="primary" @click="handleAdd">
          <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />
          新增系统参数
        </PermissionButton>
      </div>
    </template>
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :extra-params="extraParams"
      :scroll-x="1800"
      :columns="columns"
      :get-data="systemV2Api.getSystemParamList"
      @on-checked="onChecked"
      @on-data-change="(data) => handleDataChange(data)"
    >
      <template #queryBar>
        <QueryBarItem label="参数名称" :label-width="60">
          <NInput
            v-model:value="queryItems.param_name"
            type="text"
            placeholder="请输入参数名称"
            clearable
          />
        </QueryBarItem>
        <QueryBarItem label="参数键" :label-width="60">
          <NInput
            v-model:value="queryItems.param_key"
            type="text"
            placeholder="请输入参数键"
            clearable
          />
        </QueryBarItem>
        <QueryBarItem label="参数类型" :label-width="60">
          <NSelect
            v-model:value="queryItems.param_type"
            clearable
            placeholder="请选择参数类型"
            :options="paramTypeOptions"
          />
        </QueryBarItem>
        <QueryBarItem label="状态" :label-width="50">
          <NSelect
            v-model:value="queryItems.is_active"
            clearable
            placeholder="请选择状态"
            :options="statusOptions"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <!-- 新增/编辑弹窗 -->
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
        :label-width="80"
        :model="modalForm"
        :rules="modalRules"
      >
        <NFormItem label="参数名称" path="param_name">
          <NInput v-model:value="modalForm.param_name" placeholder="请输入参数名称" />
        </NFormItem>
        <NFormItem label="参数键" path="param_key">
          <NInput v-model:value="modalForm.param_key" placeholder="请输入参数键" />
        </NFormItem>
        <NFormItem label="参数值" path="param_value">
          <NInput
            v-if="
              modalForm.param_type === 'string' ||
              modalForm.param_type === 'text' ||
              !modalForm.param_type
            "
            v-model:value="modalForm.param_value"
            placeholder="请输入参数值"
            clearable
          />
          <NInput
            v-else-if="
              modalForm.param_type === 'number' ||
              modalForm.param_type === 'int' ||
              modalForm.param_type === 'float'
            "
            v-model:value="modalForm.param_value"
            type="number"
            placeholder="请输入参数值"
            clearable
          />
          <NSwitch
            v-else-if="modalForm.param_type === 'boolean'"
            :value="modalForm.param_value === 'true' || modalForm.param_value === true"
            @update:value="(val) => (modalForm.param_value = val ? 'true' : 'false')"
          />
          <NInput
            v-else-if="modalForm.param_type === 'json'"
            v-model:value="modalForm.param_value"
            type="textarea"
            :rows="3"
            placeholder="请输入JSON格式参数值"
            clearable
          />
          <NInput
            v-else
            v-model:value="modalForm.param_value"
            placeholder="请输入参数值"
            clearable
          />
        </NFormItem>
        <NFormItem label="参数类型" path="param_type">
          <NSelect
            v-model:value="modalForm.param_type"
            placeholder="请选择参数类型"
            :options="paramTypeOptions"
            :disabled="!modalForm.is_editable"
          />
        </NFormItem>
        <NFormItem label="参数描述" path="description">
          <NInput
            v-model:value="modalForm.description"
            type="textarea"
            placeholder="请输入参数描述"
          />
        </NFormItem>
        <NFormItem label="是否可编辑" path="is_editable">
          <NSwitch v-model:value="modalForm.is_editable" />
        </NFormItem>
        <NFormItem label="是否系统内置" path="is_system">
          <NSwitch v-model:value="modalForm.is_system" />
        </NFormItem>
        <NFormItem label="状态" path="is_active">
          <NSwitch v-model:value="modalForm.is_active" />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>

<script setup lang="ts">
import {
  NButton,
  NInput,
  NSelect,
  NSwitch,
  NForm,
  NFormItem,
  NSpace,
  NTag,
  NPopconfirm,
  useMessage,
} from 'naive-ui'
import { ref, reactive, onMounted, onActivated, h } from 'vue'
import systemV2Api from '@/api/system-v2'
import { useCRUD } from '@/composables/useCRUD'
import { renderIcon, isNullOrUndef } from '@/utils'
import BatchDeleteButton from '@/components/common/BatchDeleteButton.vue'
import { useSystemParamBatchDelete } from '@/composables/useBatchDelete'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import PermissionButton from '@/components/Permission/PermissionButton.vue'

defineOptions({ name: 'SystemParamManagement' })

const $table = ref(null)
const queryItems = ref({})
const extraParams = ref({})
const message = useMessage()

// 批量删除功能
const {
  selectedItems,
  selectedCount,
  setSelectedItems,
  clearSelection,
  handleBatchDelete: executeBatchDelete,
  isLoading: batchDeleteLoading,
} = useSystemParamBatchDelete({
  batchDeleteApi: systemV2Api.batchDeleteSystemParams,
  refresh: () => $table.value?.handleSearch(),
  excludeCondition: (item) => item.is_system, // 系统内置参数不能删除
})

// 参数类型选项
const paramTypeOptions = [
  { label: '字符串', value: 'string' },
  { label: '数字', value: 'number' },
  { label: '布尔值', value: 'boolean' },
  { label: 'JSON', value: 'json' },
  { label: '文本', value: 'text' },
]

// 状态选项
const statusOptions = [
  { label: '启用', value: true },
  { label: '禁用', value: false },
]

// 表格列配置
const columns = [
  { type: 'selection', fixed: 'left', width: 50 },
  { title: 'ID', key: 'id', width: 80, align: 'center', ellipsis: { tooltip: true } },
  { title: '参数名称', key: 'param_name', width: 200, ellipsis: { tooltip: true } },
  { title: '参数键', key: 'param_key', width: 200, ellipsis: { tooltip: true } },
  { title: '参数值', key: 'param_value', width: 250, ellipsis: { tooltip: true } },
  {
    title: '参数类型',
    key: 'param_type',
    width: 120,
    align: 'center',
    render(row) {
      return h(NTag, { type: 'info', size: 'small' }, { default: () => row.param_type })
    },
  },
  { title: '参数描述', key: 'description', width: 300, ellipsis: { tooltip: true } },
  {
    title: '系统内置',
    key: 'is_system',
    width: 100,
    align: 'center',
    render: (row) => {
      return row.is_system ? '是' : '否'
    },
  },
  {
    title: '可编辑',
    key: 'is_editable',
    width: 100,
    align: 'center',
    render: (row) => {
      return row.is_editable ? '是' : '否'
    },
  },
  {
    title: '状态',
    key: 'is_active',
    width: 80,
    align: 'center',
    render: (row) => {
      return row.is_active ? '启用' : '禁用'
    },
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    align: 'center',
    ellipsis: { tooltip: true },
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
            permission: 'PUT /api/v2/system/params/{id}',
            size: 'small',
            type: 'primary',
            style: 'margin-right: 8px;',
            disabled: !row.is_editable, // 不可编辑的参数不能修改
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
            permission: 'DELETE /api/v2/system/params/{id}',
            size: 'small',
            type: 'error',
            needConfirm: true,
            confirmTitle: '删除确认',
            confirmContent: '确定删除该系统参数吗？此操作不可恢复。',
            onConfirm: () => handleDelete([row.id]),
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

// CRUD操作
const {
  modalVisible,
  modalAction,
  modalTitle,
  modalLoading,
  handleAdd,
  handleDelete,
  handleEdit,
  handleSave,
  modalForm,
  modalFormRef,
} = useCRUD({
  name: '系统参数',
  initForm: {
    param_name: '',
    param_key: '',
    param_value: '',
    param_type: 'string',
    description: '',
    is_editable: true,
    is_system: false,
    is_active: true,
  },
  doCreate: systemV2Api.createSystemParam,
  doDelete: systemV2Api.deleteSystemParam,
  doUpdate: systemV2Api.updateSystemParam,
  refresh: () => $table.value?.handleSearch(),
})

// 表单验证规则
const modalRules = {
  param_name: [{ required: true, message: '请输入参数名称', trigger: ['input', 'blur'] }],
  param_key: [{ required: true, message: '请输入参数键', trigger: ['input', 'blur'] }],
  param_value: [{ required: true, message: '请输入参数值', trigger: ['input', 'blur'] }],
  param_type: [{ required: true, message: '请选择参数类型', trigger: ['change', 'blur'] }],
}

// 处理选中项
function onChecked(rowKeys, rows) {
  if (rowKeys.length) {
    extraParams.value.selectedRowKeys = rowKeys
    setSelectedItems(rows || [], rowKeys)
  } else {
    extraParams.value.selectedRowKeys = []
    clearSelection()
  }
}

// 处理数据变化
function handleDataChange(data) {
  console.log('系统参数数据变化:', data)
}

// 处理批量删除
async function handleBatchDelete() {
  try {
    await executeBatchDelete()
  } catch (error) {
    console.error('批量删除系统参数失败:', error)
    message.error(`批量删除失败：${error.message || '未知错误'}`)
  }
}

onMounted(() => {
  $table.value?.handleSearch()
})

onActivated(() => {
  $table.value?.handleSearch()
})
</script>
