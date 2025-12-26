<script setup lang="ts">
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NForm, NFormItem, NInput, NPopconfirm, NSelect, NSwitch, NTag, useDialog, useMessage } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import PermissionButton from '@/components/Permission/PermissionButton.vue'

import { formatDate, formatDateTime, renderIcon } from '@/utils'
import { useCRUD } from '@/composables/useCRUD'
import api from '@/api'
// ✅ Shared API 迁移 (2025-10-25)
import { deviceTypeApi, deviceApi } from '@/api/device-shared'
import TheIcon from '@/components/icon/TheIcon.vue'
import IconPicker from '@/components/icon/IconPicker.vue'
import { useRouter } from 'vue-router'

defineOptions({ name: '设备类型管理' })

const router = useRouter()
const dialog = useDialog()
const message = useMessage()

const $table = ref(null)
const checkedRowKeys = ref([])
const queryItems = ref({
  type_name: '',
  type_code: '',
  is_active: undefined,
})
const vPermission = resolveDirective('permission')

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
  name: '设备类型',
  initForm: {
    type_name: '',
    type_code: '',
    tdengine_stable_name: '',
    description: '',
    icon: 'material-symbols:precision-manufacturing',
    is_active: true,
  },
  // ✅ Shared API 迁移
  doCreate: deviceTypeApi.create,
  doDelete: deviceTypeApi.delete,
  doUpdate: deviceTypeApi.update,
  refresh: () => $table.value?.handleSearch(),
})

onMounted(() => {
  $table.value?.handleSearch()
})

const handleDeleteType = async (row) => {
  const executeDelete = async (cascade = false) => {
    try {
      await deviceTypeApi.delete(row.type_code, { cascade })
      message.success('删除成功')
      $table.value?.handleSearch()
    } catch (error: any) {
      message.error(`删除失败: ${error.message || '未知错误'}`)
    }
  }

  try {
    // 查询真实关联设备数量 (使用 deviceApi 获取实时数据)
    const res = await deviceApi.list({ 
        device_type: row.type_code, 
        page: 1, 
        page_size: 1 
    })
    
    // 获取总数 (兼容不同的响应格式)
    // 注意：res 可能是 { data: [], total: 10, meta: {...} }
    const count = res.total ?? res.meta?.total ?? res.data?.total ?? 0
    
    if (count > 0) {
       dialog.warning({
           title: '关联设备删除确认',
           content: `检测到该类型下有 ${count} 台关联设备。\n\n删除设备类型将自动删除所有关联设备及其数据（不可恢复），是否继续？`,
           positiveText: '确认级联删除',
           negativeText: '取消',
           onPositiveClick: () => executeDelete(true)
       })
    } else {
       dialog.warning({
           title: '删除确认',
           content: '确定删除该设备类型吗？',
           positiveText: '确认',
           negativeText: '取消',
           onPositiveClick: () => executeDelete(false)
       })
    }
  } catch (e) {
     // 降级处理
     dialog.warning({
         title: '删除确认',
         content: '确定删除该设备类型吗？',
         positiveText: '确认',
         negativeText: '取消',
         onPositiveClick: () => executeDelete(false)
     })
  }
}

const handleBatchDeleteType = async () => {
  if (checkedRowKeys.value.length === 0) return
  
  dialog.warning({
    title: '批量删除确认',
    content: `确定删除选中的 ${checkedRowKeys.value.length} 个设备类型吗？\n\n⚠️ 注意：这将自动级联删除这些类型下的所有关联设备及其数据，且操作不可恢复！`,
    positiveText: '确认删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await deviceTypeApi.batchDelete(checkedRowKeys.value, { cascade: true })
        message.success('批量删除成功')
        checkedRowKeys.value = []
        $table.value?.handleSearch()
      } catch (e: any) {
        message.error(`批量删除失败: ${e.message}`)
      }
    }
  })
}

const columns = [
  { type: 'selection' },
  {
    title: '图标',
    key: 'icon',
    width: 80,
    align: 'center',
    render(row) {
      return h(TheIcon, { 
        icon: row.icon || 'material-symbols:precision-manufacturing', 
        size: 24,
        class: 'text-primary'
      })
    },
  },
  {
    title: '类型名称',
    key: 'type_name',
    width: 150,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '类型编码',
    key: 'type_code',
    width: 200,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h(NTag, { type: 'info' }, { default: () => row.type_code })
    },
  },
  {
    title: 'TDengine超级表',
    key: 'tdengine_stable_name',
    width: 200,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h(NTag, { type: 'warning' }, { default: () => row.tdengine_stable_name })
    },
  },
  {
    title: '状态',
    key: 'is_active',
    width: 80,
    align: 'center',
    render(row) {
      return h(
        NTag,
        { type: row.is_active ? 'success' : 'error' },
        { default: () => (row.is_active ? '激活' : '禁用') }
      )
    },
  },
  {
    title: '描述',
    key: 'description',
    minWidth: 200,
    align: 'left',
    ellipsis: { tooltip: true },
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    align: 'center',
    render(row) {
      return h('span', formatDateTime(row.created_at))
    },
  },
  {
    title: '更新时间',
    key: 'updated_at',
    width: 180,
    align: 'center',
    render(row) {
      return h('span', formatDateTime(row.updated_at))
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 280,
    align: 'center',
    fixed: 'right',
    render(row) {
      return [
        h(
          PermissionButton,
          {
            permission: 'PUT /api/v2/devices/types/{id}',
            size: 'small',
            type: 'primary',
            style: 'margin-right: 8px;',
            onClick: () => {
              handleEdit(row)
            },
          },
          {
            default: () => '编辑',
            icon: renderIcon('material-symbols:edit-outline', { size: 16 }),
          }
        ),
        h(
          NButton,
          {
            size: 'small',
            type: 'info',
            style: 'margin-right: 8px;',
            onClick: () => {
              // 跳转到统一配置页面，并预填充设备类型
              router.push({
                path: '/metadata/unified',
                query: {
                  device_type: row.type_code,
                  tab: 'models',
                },
              })
            },
          },
          {
            default: () => '模型配置',
            icon: renderIcon('mdi:database-cog', { size: 16 }),
          }
        ),
        h(
          PermissionButton,
          {
            permission: 'DELETE /api/v2/devices/types/{id}',
            size: 'small',
            type: 'error',
            onClick: () => handleDeleteType(row),
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
  <CommonPage show-footer title="设备类型列表">
    <template #action>
      <PermissionButton
        permission="DELETE /api/v2/devices/types/{id}"
        type="error"
        :disabled="checkedRowKeys.length === 0"
        class="mr-4"
        @click="handleBatchDeleteType"
      >
        <TheIcon icon="material-symbols:delete-outline" :size="18" class="mr-5" />批量删除
      </PermissionButton>
      <PermissionButton permission="POST /api/v2/devices/types" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建设备类型
      </PermissionButton>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="deviceTypeApi.list"
      v-model:checked-row-keys="checkedRowKeys"
    >
      <template #queryBar>
        <QueryBarItem label="类型名称" :label-width="70">
          <NInput
            v-model:value="queryItems.type_name"
            clearable
            type="text"
            placeholder="请输入类型名称"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="类型编码" :label-width="70">
          <NInput
            v-model:value="queryItems.type_code"
            clearable
            type="text"
            placeholder="请输入类型编码"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="激活状态" :label-width="70">
          <NSelect
            v-model:value="queryItems.is_active"
            clearable
            placeholder="请选择状态"
            :options="[
              { label: '激活', value: true },
              { label: '禁用', value: false },
            ]"
            @update:value="$table?.handleSearch()"
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
        :label-width="80"
        :model="modalForm"
        :disabled="modalAction === 'view'"
      >
        <NFormItem
          label="类型编码"
          path="type_code"
          :rule="{
            required: true,
            message: '请输入类型编码',
            trigger: ['input', 'blur'],
          }"
        >
          <NInput
            v-model:value="modalForm.type_code"
            placeholder="请输入类型编码"
            :disabled="modalAction === 'edit'"
          />
        </NFormItem>
        <NFormItem
          label="类型名称"
          path="type_name"
          :rule="{
            required: true,
            message: '请输入类型名称',
            trigger: ['input', 'blur'],
          }"
        >
          <NInput v-model:value="modalForm.type_name" placeholder="请输入类型名称" />
        </NFormItem>
        <NFormItem
          label="TDengine超级表名"
          path="tdengine_stable_name"
          :rule="{
            required: true,
            message: '请输入TDengine超级表名',
            trigger: ['input', 'blur'],
          }"
        >
          <NInput
            v-model:value="modalForm.tdengine_stable_name"
            placeholder="请输入TDengine超级表名"
          />
        </NFormItem>
        <NFormItem label="设备图标" path="icon">
          <IconPicker v-model:value="modalForm.icon" />
        </NFormItem>
        <NFormItem label="状态" path="is_active">
          <NSwitch v-model:value="modalForm.is_active">
            <template #checked>激活</template>
            <template #unchecked>禁用</template>
          </NSwitch>
        </NFormItem>
        <NFormItem label="描述" path="description">
          <NInput
            v-model:value="modalForm.description"
            type="textarea"
            placeholder="请输入描述"
            :autosize="{
              minRows: 3,
              maxRows: 5,
            }"
          />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
