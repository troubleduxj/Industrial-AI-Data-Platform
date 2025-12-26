<script setup lang="ts">
import { h, onMounted, ref, resolveDirective, withDirectives, computed } from 'vue'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NPopconfirm,
  NTag,
  NTree,
  NDrawer,
  NDrawerContent,
  NTabs,
  NTabPane,
  NGrid,
  NGi,
  useMessage,
} from 'naive-ui'
import { useI18n } from 'vue-i18n'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import MenuPermissionTree from '@/components/system/MenuPermissionTree.vue'
import BatchDeleteButton from '@/components/common/BatchDeleteButton.vue'

import { formatDate, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import { useRoleBatchDelete } from '@/composables/useBatchDelete'
import systemV2Api from '@/api/system-v2'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '角色管理' })

const $table = ref(null)
const $message = useMessage()
const { t } = useI18n()
const queryItems = ref({})
const vPermission = resolveDirective('permission')

// 分页状态管理
const pagination = ref({
  page: 1,
  pageSize: 10,
})

// 分页事件处理函数
function handlePageChange(page) {
  pagination.value.page = page
}

function handlePageSizeChange(pageSize) {
  pagination.value.page = 1
  pagination.value.pageSize = pageSize
}

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
  name: '角色',
  initForm: {},
  doCreate: systemV2Api.createRole,
  doDelete: systemV2Api.deleteRole,
  doUpdate: systemV2Api.updateRole,
  refresh: () => $table.value?.handleSearch(),
})

// 批量删除功能
const {
  selectedItems,
  selectedRowKeys,
  selectedCount,
  isLoading: batchDeleteLoading,
  handleBatchDelete,
  setSelectedItems,
  clearSelection,
} = useRoleBatchDelete({
  batchDeleteApi: (ids) => systemV2Api.roles.batchDelete(ids),
  refresh: () => $table.value?.handleSearch(),
  excludeCondition: (item) => item.is_system || item.is_protected,
})

const pattern = ref('')
const menuOption = ref([]) // 菜单选项
const active = ref(false)
const menu_ids = ref([])
const role_id = ref(0)
const apiOption = ref([])
const api_ids = ref([])
const apiTree = ref([])

function buildApiTree(data) {
  const groupedData = {}

  // 过滤只保留v2接口
  const v2Data = data.filter((item) => item.path && item.path.startsWith('/api/v2/'))

  console.log('buildApiTree处理的V2数据:', v2Data)

  v2Data.forEach((item) => {
    const groupName = item['group_name'] || '默认分组'
    const groupCode = item['group_code'] || 'default'
    // 去掉/api/v2前缀，使格式与角色权限数据保持一致
    const path = item['path'].replace('/api/v2', '')
    const unique_id = item['method'].toLowerCase() + path
    console.log('构建API树节点 unique_id:', unique_id, '来源:', item, '处理后路径:', path)

    if (!(groupCode in groupedData)) {
      groupedData[groupCode] = {
        id: `group_${groupCode}`, // 为父级分组节点添加id字段
        unique_id: groupCode,
        path: groupCode,
        summary: groupName,
        children: [],
      }
    }

    groupedData[groupCode].children.push({
      id: item['id'],
      path: item['path'],
      method: item['method'],
      summary: `${item['summary'] || `${item['method']} ${item['path']}`} (${item['method']} ${
        item['path']
      })`,
      unique_id: unique_id,
    })
  })

  const processedData = Object.values(groupedData)
  console.log('构建完成的API树:', processedData)
  return processedData
}

// 角色列表数据获取函数
const getRoleListData = async (params) => {
  try {
    console.log('调用角色列表API v2，参数:', params)
    const res = await systemV2Api.getRoleList({
      ...params,
      page: params.page || 1,
      pageSize: params.pageSize || params.page_size || 10,
    })
    console.log('角色API v2原始响应:', res)

    if (res?.success !== false) {
      console.log('角色API v2返回数据:', res.data)
      // 适配器已经处理了嵌套结构，res.data现在直接是角色数组
      const roleItems = Array.isArray(res.data) ? res.data : res.data?.items || []
      const processedData = roleItems.map((item) => ({
        ...item,
        id: item.id, // 确保id字段存在
        name: item.role_name || item.name || '',
        desc: item.remark || item.desc || item.description || '',
        created_at: item.created_at || new Date().toISOString(),
      }))

      console.log('角色处理后的数据:', processedData)
      console.log('第一个角色的ID:', processedData[0]?.id)
      return {
        data: processedData,
        total: res.total || res.meta?.total || 0,
      }
    }
    return { data: [], total: 0 }
  } catch (err) {
    console.error('角色列表API v2错误:', err)
    $message?.error(t('system.role.list.load_failed', { error: err.message || 'Unknown error' }))
    return { data: [], total: 0 }
  }
}

onMounted(() => {
  $table.value?.handleSearch()
})

// 测试函数 - 用于调试
window.testRoleSelection = () => {
  console.log('=== 角色选择状态测试 ===')
  console.log('selectedRowKeys:', selectedRowKeys.value)
  console.log('selectedRows:', selectedRows.value)
  console.log('表格数据:', $table.value?.tableData)
  console.log('hasSelectedRoles:', hasSelectedRoles.value)
}

// 测试批量删除函数
window.testBatchDelete = () => {
  console.log('=== 测试批量删除 ===')
  handleBatchDelete()
}

// 测试多语言函数
window.testI18n = () => {
  console.log('=== 测试多语言 ===')
  console.log('当前语言:', t('lang'))
  console.log('批量删除提示:', t('system.role.batch_delete.select_first'))
  console.log('删除成功:', t('system.role.batch_delete.success', { count: 3 }))
}

const columns = [
  {
    type: 'selection',
    width: 40,
    align: 'center',
    fixed: 'left',
  },
  {
    title: '角色名',
    key: 'name',
    width: 80,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h(NTag, { type: 'info' }, { default: () => row.name })
    },
  },
  {
    title: '角色描述',
    key: 'desc',
    width: 80,
    align: 'center',
  },
  {
    title: '创建日期',
    key: 'created_at',
    width: 60,
    align: 'center',
    render(row) {
      return h('span', formatDate(row.created_at))
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 80,
    align: 'center',
    fixed: 'right',
    render(row) {
      return [
        withDirectives(
          h(
            NButton,
            {
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
          [[vPermission, 'PUT /api/v2/roles/{id}']]
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete({ role_id: row.id }, false),
            onNegativeClick: () => {},
          },
          {
            trigger: () =>
              withDirectives(
                h(
                  NButton,
                  {
                    size: 'small',
                    type: 'error',
                    style: 'margin-right: 8px;',
                  },
                  {
                    default: () => '删除',
                    icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
                  }
                ),
                [[vPermission, 'DELETE /api/v2/roles/{id}']]
              ),
            default: () => h('div', {}, '确定删除该角色吗?'),
          }
        ),
        withDirectives(
          h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              onClick: async () => {
                try {
                  console.log('加载角色权限数据，角色ID:', row.id)
                  // 使用 Promise.all 来同时发送所有请求
                  const [menusResponse, apisResponse, roleAuthorizedResponse] = await Promise.all([
                    systemV2Api.getMenus({ page: 1, page_size: 100 }), // 获取所有菜单数据
                    systemV2Api.getApis({ page: 1, page_size: 100 }),
                    systemV2Api.getRoleAuthorized({ id: row.id }),
                  ])

                  console.log('菜单响应:', menusResponse)
                  console.log('API响应:', apisResponse)
                  console.log('角色权限响应:', roleAuthorizedResponse)

                  // 处理每个请求的响应
                  menuOption.value = menusResponse.data || []
                  apiOption.value = buildApiTree(apisResponse.data || [])
                  menu_ids.value = (roleAuthorizedResponse.data?.menus || []).map((v) => v.id)
                  // 使用V2版本的sys_api数据，构建已选中的API unique_id列表（匹配树组件的key-field）
                  console.log('V2 sys_apis数据:', roleAuthorizedResponse.data?.v2_sys_apis)
                  api_ids.value = (roleAuthorizedResponse.data?.v2_sys_apis || []).map((v) => {
                    const uniqueId = v.http_method.toLowerCase() + v.api_path
                    console.log('生成API unique_id:', uniqueId, '来源:', v)
                    return uniqueId
                  })
                  console.log('设置的api_ids:', api_ids.value)

                  active.value = true
                  role_id.value = row.id
                  console.log('权限数据加载完成')
                } catch (error) {
                  // 错误处理
                  console.error('加载权限数据失败:', error)
                  $message?.error(
                    t('system.role.permissions.load_failed', {
                      error: error.message || 'Unknown error',
                    })
                  )
                }
              },
            },
            {
              default: () => '设置权限',
              icon: renderIcon('material-symbols:edit-outline', { size: 16 }),
            }
          ),
          [[vPermission, 'GET /api/v2/roles/{id}/permissions']]
        ),
      ]
    },
  },
]

async function updateRoleAuthorized() {
  try {
    console.log('更新角色权限，角色ID:', role_id.value)
    console.log('菜单权限:', menu_ids.value)
    console.log('API权限:', api_ids.value)

    const checkData = apiTree.value.getCheckedData()
    const sysApiIds = []
    checkData &&
      checkData.options.forEach((item) => {
        if (item && !item.children && item.id) {
          // 确保ID是整数类型
          const apiId = parseInt(item.id, 10)
          if (!isNaN(apiId)) {
            sysApiIds.push(apiId)
          }
        }
      })

    console.log('提取的API权限ID:', sysApiIds)

    const result = await systemV2Api.updateRoleAuthorized({
      id: role_id.value,
      menu_ids: menu_ids.value,
      sys_api_ids: sysApiIds,
    })

    console.log('权限更新结果:', result)

    if (result.success !== false) {
      $message?.success(t('system.role.permissions.update_success'))
      active.value = false // 关闭抽屉

      // 刷新角色权限数据
      const roleResult = await systemV2Api.getRoleAuthorized({ id: role_id.value })
      menu_ids.value = (roleResult.data?.menus || []).map((v) => v.id)
      // 使用V2版本的sys_api数据，构建已选中的API unique_id列表
      api_ids.value = (roleResult.data?.v2_sys_apis || []).map(
        (v) => v.http_method.toLowerCase() + v.api_path
      )
    } else {
      $message?.error(result.message || t('system.role.permissions.update_failed'))
    }
  } catch (error) {
    console.error('更新角色权限失败:', error)
    // 检查错误是否已经被HTTP拦截器处理过，避免重复提示
    if (!(error && typeof error === 'object' && error.success === false)) {
      $message?.error(
        t('system.role.permissions.update_error', { error: error.message || 'Unknown error' })
      )
    }
  }
}

function handleMenuSelectionChange(selectionInfo) {
  console.log('菜单选择变化:', selectionInfo)
  // selectionInfo 包含 { selectedMenus, selectedCount, totalCount }
  menu_ids.value = selectionInfo.selectedMenus
}

// 批量选择处理函数
function handleChecked(rowKeys, rows) {
  console.log('表格选择事件触发，rowKeys:', rowKeys, 'rows:', rows)

  // 如果没有传递rows，从表格数据中查找
  const selectedRows =
    rows || $table.value?.tableData?.filter((row) => rowKeys.includes(row.id)) || []

  // 使用批量删除组合函数设置选中项目
  setSelectedItems(selectedRows, rowKeys || [])

  console.log(
    '更新后的选中状态 - selectedRowKeys:',
    selectedRowKeys.value,
    'selectedItems:',
    selectedItems.value
  )
}
</script>

<template>
  <CommonPage
    v-permission="'GET /api/v2/roles'"
    show-footer
    title="角色列表"
    class="system-role-page system-management-page standard-page"
  >
    <template #action>
      <div class="flex items-center gap-3">
        <BatchDeleteButton
          :selected-items="selectedItems"
          :selected-count="selectedCount"
          resource-name="角色"
          permission="DELETE /api/v2/roles/batch"
          :loading="batchDeleteLoading"
          :exclude-condition="(item) => item.is_system || item.is_protected"
          @batch-delete="handleBatchDelete"
        />
        <NButton v-permission="'POST /api/v2/roles'" type="primary" @click="handleAdd">
          <TheIcon icon="material-symbols:add" :size="18" class="mr-1" />新建角色
        </NButton>
      </div>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="getRoleListData"
      :pagination="pagination"
      row-key="id"
      :checked-row-keys="selectedRowKeys"
      @on-page-change="handlePageChange"
      @on-page-size-change="handlePageSizeChange"
      @on-checked="handleChecked"
    >
      <template #queryBar>
        <QueryBarItem label="角色名" :label-width="50">
          <NInput
            v-model:value="queryItems.role_name"
            clearable
            type="text"
            placeholder="请输入角色名"
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
        :label-width="80"
        :model="modalForm"
        :disabled="modalAction === 'view'"
      >
        <NFormItem
          label="角色名"
          path="role_name"
          :rule="{
            required: true,
            message: '请输入角色名称',
            trigger: ['input', 'blur'],
          }"
        >
          <NInput v-model:value="modalForm.role_name" placeholder="请输入角色名称" />
        </NFormItem>
        <NFormItem label="角色描述" path="remark">
          <NInput v-model:value="modalForm.remark" placeholder="请输入角色描述" />
        </NFormItem>
      </NForm>
    </CrudModal>

    <NDrawer v-model:show="active" placement="right" :width="500"
      ><NDrawerContent>
        <NGrid x-gap="24" cols="12">
          <NGi span="8">
            <NInput
              v-model:value="pattern"
              type="text"
              placeholder="筛选"
              style="flex-grow: 1"
            ></NInput>
          </NGi>
          <NGi offset="2">
            <NButton
              v-permission="'PUT /api/v2/roles/{id}/permissions'"
              type="info"
              @click="updateRoleAuthorized"
              >确定</NButton
            >
          </NGi>
        </NGrid>
        <NTabs>
          <NTabPane name="menu" tab="菜单权限" display-directive="show">
            <MenuPermissionTree
              :menu-data="menuOption"
              :selected-menus="menu_ids"
              :show-route-path="true"
              :show-component="true"
              @update:selected-menus="(v) => (menu_ids = v)"
              @menu-selection-change="handleMenuSelectionChange"
            />
          </NTabPane>
          <NTabPane name="resource" tab="接口权限" display-directive="show">
            <NTree
              ref="apiTree"
              :data="apiOption"
              :checked-keys="api_ids"
              :pattern="pattern"
              :show-irrelevant-nodes="false"
              key-field="unique_id"
              label-field="summary"
              checkable
              :default-expand-all="true"
              :block-line="true"
              :selectable="false"
              cascade
              @update:checked-keys="(v) => (api_ids = v)"
            />
          </NTabPane>
        </NTabs>
        <template #header> 设置权限 </template>
      </NDrawerContent>
    </NDrawer>
  </CommonPage>
</template>

<style scoped>
/* 优化表格勾选框样式 */
:deep(.n-data-table .n-data-table-th--selection),
:deep(.n-data-table .n-data-table-td--selection) {
  padding: var(--spacing-sm) var(--spacing-xs) !important;
  width: 50px !important;
  min-width: 50px !important;
  max-width: 50px !important;
  text-align: center !important;
  vertical-align: middle !important;
}

:deep(.n-data-table .n-checkbox) {
  transform: scale(1.1) !important;
  display: inline-block !important;
  vertical-align: middle !important;
}

:deep(.n-data-table .n-checkbox .n-checkbox-box) {
  border-width: 1.5px !important;
  border-color: var(--border-color-base) !important;
  width: 16px !important;
  height: 16px !important;
  border-radius: var(--border-radius-sm) !important;
}

:deep(.n-data-table .n-checkbox:hover .n-checkbox-box) {
  border-color: var(--primary-color-hover) !important;
}

:deep(.n-data-table .n-checkbox--checked .n-checkbox-box) {
  background-color: var(--primary-color) !important;
  border-color: var(--primary-color) !important;
}

/* 移除可能的下划线或横杠 */
:deep(.n-data-table .n-data-table-td--selection::after),
:deep(.n-data-table .n-data-table-th--selection::after) {
  display: none !important;
}

:deep(.n-data-table .n-checkbox::after),
:deep(.n-data-table .n-checkbox::before) {
  display: none !important;
}
</style>
