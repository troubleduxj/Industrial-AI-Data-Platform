<!-- 
  角色管理页面 - 修复版本
  主要修复：
  1. 改进错误处理和用户反馈
  2. 优化模态框状态管理
  3. 增强删除操作的安全性
-->
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
  NSpace,
  useMessage,
  useDialog,
} from 'naive-ui'
import { useI18n } from 'vue-i18n'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import MenuPermissionTree from '@/components/system/MenuPermissionTree.vue'
import ApiPermissionTree from '@/components/system/ApiPermissionTree.vue'
import BatchDeleteButton from '@/components/common/BatchDeleteButton.vue'
import PermissionButton from '@/components/Permission/PermissionButton.vue'

import { formatDate, renderIcon } from '@/utils'
import { useCRUD } from '@/composables/useCRUD-fix' // 使用修复版本
import { useRoleBatchDelete } from '@/composables/useBatchDelete'
import systemV2Api from '@/api/system-v2'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '角色管理' })

// ==================== 类型定义 ====================

interface QueryItems {
  [key: string]: any
}

interface PaginationInfo {
  page: number
  pageSize: number
}

interface RoleInfo {
  id: string | number
  name: string
  code?: string
  description?: string
  menus?: any[]
  apis?: any[]
  role_name?: string
  remark?: string
  [key: string]: any
}

const $table = ref<any>(null)
const $message = useMessage()
const $dialog = useDialog()
const { t } = useI18n()
const queryItems = ref<QueryItems>({})
const vPermission = resolveDirective('permission')

// 分页状态管理
const pagination = ref<PaginationInfo>({
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

// 修复：增强的CRUD配置
const {
  modalVisible,
  modalAction,
  modalTitle,
  modalLoading,
  handleAdd,
  handleDelete: originalHandleDelete,
  handleEdit,
  handleSave: originalHandleSave,
  modalForm,
  modalFormRef,
} = useCRUD({
  name: '角色',
  initForm: {} as any,
  doCreate: systemV2Api.createRole,
  doDelete: systemV2Api.deleteRole,
  doUpdate: systemV2Api.updateRole,
  refresh: () => $table.value?.handleSearch(),
})

// 修复：增强的保存处理，包含更好的错误反馈
async function handleSave() {
  try {
    await originalHandleSave()
  } catch (error) {
    // 显示具体的错误信息
    const errorMessage = error.response?.data?.message || error.message || '操作失败'
    $message.error(`${modalAction.value === 'add' ? '创建' : '更新'}角色失败: ${errorMessage}`)
  }
}

// 修复：增强的删除处理，包含更好的确认和错误处理
async function handleDelete(params) {
  // 参数验证
  if (!params || (!params.role_id && !params.id)) {
    $message.warning('删除操作缺少必要参数')
    return
  }

  // 显示确认对话框
  $dialog.warning({
    title: '确认删除',
    content: '确定要删除这个角色吗？此操作不可撤销。',
    positiveText: '确定删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await originalHandleDelete(params)
        $message.success('角色删除成功')
      } catch (error) {
        const errorMessage = error.response?.data?.message || error.message || '删除失败'
        $message.error(`删除角色失败: ${errorMessage}`)
      }
    }
  })
}

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
const apiTreeRef = ref(null)

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

// 角色列表数据获取函数 - 使用统一错误处理
const getRoleListData = async (params) => {
  try {
    console.log('调用角色列表API v2，参数:', params)
    
    // 直接调用API，不使用safeDataFetch避免自动退出登录
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
    
    // 检查是否是认证错误
    if (err.response?.status === 401 || err.code === 401) {
      console.warn('检测到认证错误，可能需要重新登录')
      $message.error('登录已过期，请重新登录。请手动刷新页面或点击登录按钮重新登录。', {
        duration: 0, // 不自动消失
        closable: true
      })
      
      // 不自动清除认证信息，让用户自己决定
      // 不自动跳转，让用户自己操作
    } else {
      $message.error('获取角色列表失败: ' + (err.message || '未知错误'))
    }
    
    // 兜底处理
    return { data: [], total: 0 }
  }
}

onMounted(() => {
  $table.value?.handleSearch()
})

// 测试函数 - 用于调试
;(window as any).testRoleSelection = () => {
  console.log('=== 角色选择状态测试 ===')
  console.log('selectedRowKeys:', selectedRowKeys.value)
  console.log('selectedItems:', selectedItems.value)
  console.log('表格数据:', $table.value?.tableData)
  console.log('selectedCount:', selectedCount.value)
}

// 测试批量删除函数
;(window as any).testBatchDelete = () => {
  console.log('=== 测试批量删除 ===')
  handleBatchDelete()
}

// 测试多语言函数
;(window as any).testI18n = () => {
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
    title: 'ID',
    key: 'id',
    width: 60,
    align: 'center',
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
      return h(
        NSpace,
        {
          size: 'small',
          align: 'center',
          justify: 'start',
          wrap: false,
        },
        () => [
          h(PermissionButton, {
            permission: 'PUT /api/v2/roles/{id}',
            size: 'small',
            type: 'primary',
            onClick: () => {
              handleEdit(row)
            },
          }, {
            default: () => '编辑',
            icon: renderIcon('material-symbols:edit-outline', { size: 16 }),
          }),
          h(PermissionButton, {
            permission: 'DELETE /api/v2/roles/{id}',
            size: 'small',
            type: 'error',
            needConfirm: true,
            confirmTitle: '删除确认',
            confirmContent: '确定删除该角色吗？此操作不可恢复。',
            onConfirm: () => handleDelete({ role_id: row.id })
          }, {
            default: () => '删除',
            icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
          }),
          h(PermissionButton, {
            permission: 'PUT /api/v2/roles/{id}/permissions',
            size: 'small',
            type: 'primary',
            onClick: async () => {
                  try {
                    console.log('加载角色权限数据，角色ID:', row.id)
                    
                    // 分页加载所有API（后端限制page_size最大100）
                    console.log('开始加载API列表...')
                    let allApis = []
                    let currentPage = 1
                    let hasMore = true
                    
                    while (hasMore) {
                      const apiResponse = await systemV2Api.getApis({ 
                        page: currentPage, 
                        page_size: 100 
                      })
                      
                      const apis = apiResponse.data || []
                      allApis = allApis.concat(apis)
                      
                      // 检查是否还有更多数据
                      const total = apiResponse.total || apiResponse.meta?.total || 0
                      hasMore = allApis.length < total
                      currentPage++
                      
                      console.log(`加载第${currentPage-1}页，当前总数: ${allApis.length}/${total}`)
                      
                      // 安全限制：最多加载10页
                      if (currentPage > 10) {
                        console.warn('已达到最大页数限制(10页)')
                        break
                      }
                    }
                    
                    console.log(`API加载完成，总数: ${allApis.length}`)
                    
                    // 使用 Promise.all 来同时发送其他请求
                    console.log('开始发送其他请求...')
                    const [menusResponse, roleAuthorizedResponse] = await Promise.all([
                      systemV2Api.menus.getTree({ include_hidden: false }), // 使用树形视图获取所有菜单数据（不受分页限制）
                      systemV2Api.getRoleAuthorized({ id: row.id }),
                    ])
                    console.log('请求完成，开始处理响应...')
                    console.log('角色权限API原始响应:', roleAuthorizedResponse)

                    // 处理每个请求的响应
                    // 树形视图返回的数据结构: { tree: [...], total: ..., tree_depth: ... }
                    menuOption.value = menusResponse.data?.tree || menusResponse.data || []
                    apiOption.value = buildApiTree(allApis)
                    
                    // 处理菜单权限数据 - 使用正确的字段名menu_permissions
                    menu_ids.value = (roleAuthorizedResponse.data?.menu_permissions || []).map((v) => v.id)
                    
                    // 调试：查看角色权限API返回的完整数据结构
                    console.log('角色权限API返回的原始数据:', roleAuthorizedResponse.data)
                    console.log('角色权限API返回的所有字段:', Object.keys(roleAuthorizedResponse.data || {}))
                    
                    // 修正数据结构映射：后端返回api_permissions，前端期望v2_sys_apis
                    const v2_sys_apis = roleAuthorizedResponse.data?.api_permissions || []
                    const api_permissions = roleAuthorizedResponse.data?.api_permissions || []
                    
                    console.log('修正后 - v2_sys_apis:', v2_sys_apis)
                    console.log('修正后 - v2_sys_apis长度:', v2_sys_apis?.length)
                    console.log('修正后 - api_permissions:', api_permissions)
                    console.log('修正后 - api_permissions长度:', api_permissions?.length)
                    
                    // 如果v2_sys_apis有数据，打印前几个项目的详细结构
                    if (v2_sys_apis && v2_sys_apis.length > 0) {
                      console.log('修正后 - v2_sys_apis第一个项目详细结构:', v2_sys_apis[0])
                      console.log('修正后 - v2_sys_apis第一个项目的所有字段:', Object.keys(v2_sys_apis[0]))
                    }
                    
                    // 如果api_permissions有数据，打印前几个项目的详细结构
                    if (api_permissions && api_permissions.length > 0) {
                      console.log('修正后 - api_permissions第一个项目详细结构:', api_permissions[0])
                      console.log('修正后 - api_permissions第一个项目的所有字段:', Object.keys(api_permissions[0]))
                    }
                    
                    // 使用修正后的v2_sys_apis数据，构建已选中的API unique_id列表（匹配树组件的key-field）
                    api_ids.value = (v2_sys_apis || []).map((v) => {
                      console.log('处理单个API权限项:', v)
                      // 修复：统一字段名映射，确保与buildApiTree函数生成的unique_id一致
                      // buildApiTree使用item['method']和去掉/api/v2前缀的path
                      // 后端返回的字段是http_method和api_path，需要进行字段映射和路径处理
                      const method = v.http_method || v.method
                      const fullPath = v.api_path || v.path
                      // 去掉/api/v2前缀，与buildApiTree保持一致
                      const path = fullPath ? fullPath.replace('/api/v2', '') : ''
                      const uniqueId = method?.toLowerCase() + path
                      console.log('生成API unique_id:', uniqueId, '方法:', method, '路径:', path, '来源:', v)
                      return uniqueId
                    })
                    console.log('设置的api_ids:', api_ids.value)

                    active.value = true
                    role_id.value = row.id
                    console.log('权限数据加载完成')
                    
                    // 构建API权限树 - 使用修正后的数据
                    buildApiTree(v2_sys_apis || [])
                  } catch (error) {
                    // 修复：更好的错误处理
                    console.error('加载权限数据失败:', error)
                    console.error('错误详情:', {
                      message: error.message,
                      response: error.response,
                      stack: error.stack
                    })
                    const errorMessage = error.response?.data?.message || error.message || 'Unknown error'
                    $message?.error(
                      t('system.role.permissions.load_failed', { error: errorMessage })
                    )
                  }
                }
            }, {
            default: () => '设置权限',
            icon: renderIcon('material-symbols:edit-outline', { size: 16 }),
          }),
        ]
      )
    },
  },
]

// 修复：增强的权限更新处理
async function updateRoleAuthorized() {
  console.log('=== updateRoleAuthorized 函数被调用 ===')
  try {
    console.log('开始更新角色权限，角色ID:', role_id.value)
    console.log('菜单权限ID:', menu_ids.value)
    console.log('接口权限ID:', api_ids.value)
    console.log('接口权限ID类型:', typeof api_ids.value, '是否为数组:', Array.isArray(api_ids.value))
    console.log('apiOption数据:', apiOption.value)

    // 使用ApiPermissionTree组件的getCheckedData方法获取选中的API数据
    let sysApiIds = []
    try {
      console.log('检查apiTreeRef:', apiTreeRef.value)
      console.log('检查getCheckedData方法:', apiTreeRef.value?.getCheckedData)
      
      if (apiTreeRef.value && typeof apiTreeRef.value.getCheckedData === 'function') {
        console.log('调用ApiPermissionTree的getCheckedData方法')
        const checkedData = apiTreeRef.value.getCheckedData()
        console.log('从ApiPermissionTree获取的选中数据:', checkedData)
        sysApiIds = checkedData.map(item => {
          const apiId = parseInt(item.id, 10)
          return !isNaN(apiId) ? apiId : undefined
        }).filter(id => id !== undefined)
        console.log('提取的API ID列表:', sysApiIds)
      } else {
        // 降级处理：从api_ids中提取实际的API ID
        console.warn('ApiPermissionTree组件不可用，使用降级方法')
        console.log('apiTreeRef.value:', apiTreeRef.value)
        console.log('api_ids.value:', api_ids.value)
        console.log('apiOption.value长度:', apiOption.value?.length)
        
        // 递归遍历树形结构，提取所有叶子节点（实际API）的ID
        const extractApiIds = (nodes) => {
          nodes.forEach((node) => {
            // 如果有children，说明是分组节点，递归处理
            if (node.children && node.children.length > 0) {
              extractApiIds(node.children)
            } else {
              // 叶子节点，检查是否被选中
              if (node.unique_id && api_ids.value.includes(node.unique_id)) {
                console.log('添加API ID:', node.id, '对应unique_id:', node.unique_id)
                const apiId = parseInt(node.id, 10)
                if (!isNaN(apiId)) {
                  sysApiIds.push(apiId)
                }
              }
            }
          })
        }
        
        extractApiIds(apiOption.value)
      }
    } catch (methodError) {
      console.error('调用getCheckedData方法时出错:', methodError)
      // 使用降级方法 - 递归遍历树形结构
      const extractApiIds = (nodes) => {
        nodes.forEach((node) => {
          if (node.children && node.children.length > 0) {
            extractApiIds(node.children)
          } else if (node.unique_id && api_ids.value.includes(node.unique_id)) {
            const apiId = parseInt(node.id, 10)
            if (!isNaN(apiId)) {
              sysApiIds.push(apiId)
            }
          }
        })
      }
      extractApiIds(apiOption.value)
    }

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
      menu_ids.value = (roleResult.data?.menu_permissions || []).map((v) => v.id)
      // 使用修正后的api_permissions数据，构建已选中的API unique_id列表
      const refreshed_v2_sys_apis = roleResult.data?.api_permissions || []
      api_ids.value = (refreshed_v2_sys_apis || []).map((v) => {
        // 统一字段名映射，确保与buildApiTree函数生成的unique_id一致
        const method = v.http_method || v.method
        const fullPath = v.api_path || v.path
        // 去掉/api/v2前缀，与buildApiTree保持一致
        const path = fullPath ? fullPath.replace('/api/v2', '') : ''
        return method?.toLowerCase() + path
      })
    } else {
      $message?.error(result.message || t('system.role.permissions.update_failed'))
    }
  } catch (error) {
    console.error('更新角色权限失败:', error)
    // 修复：更好的错误处理
    const errorMessage = error.response?.data?.message || error.message || 'Unknown error'
    $message?.error(t('system.role.permissions.update_error', { error: errorMessage }))
  }
}

function handleMenuSelectionChange(selectionInfo) {
  console.log('菜单选择变化:', selectionInfo)
  // selectionInfo 包含 { selectedMenus, selectedCount, totalCount }
  menu_ids.value = selectionInfo.selectedMenus
}

function handleApiSelectionChange(selectedApis) {
  console.log('接口选择变化:', selectedApis)
  // selectedApis 是选中的接口ID数组
  api_ids.value = selectedApis
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
  <CommonPage v-permission="'GET /api/v2/roles'" show-footer title="角色列表" class="system-role-page system-management-page standard-page">
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
        <PermissionButton
          permission="POST /api/v2/roles"
          type="primary"
          @click="handleAdd"
        >
          <TheIcon icon="material-symbols:add" :size="18" class="mr-1" />新建角色
        </PermissionButton>
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

    <NDrawer 
      v-model:show="active" 
      placement="right" 
      :width="600"
      :height="'100%'"
      class="permission-drawer"
    >
      <NDrawerContent class="permission-drawer-content">
        <template #header>
          <div class="drawer-header">
            <span class="drawer-title">设置权限</span>
          </div>
        </template>
        
        <div class="drawer-body">
          <div class="action-bar">
            <PermissionButton
              permission="PUT /api/v2/roles/{id}/permissions"
              type="primary"
              block
              @click="updateRoleAuthorized"
            >
              <TheIcon icon="material-symbols:check" :size="16" class="mr-1" />
              确定
            </PermissionButton>
          </div>
          
          <NTabs class="permission-tabs" type="line" animated>
            <NTabPane name="menu" tab="菜单权限" display-directive="show">
              <div class="tab-content">
                <MenuPermissionTree
                  :menu-data="menuOption"
                  :selectedMenus="menu_ids"
                  :show-route-path="true"
                  :show-component="true"
                  @update:selectedMenus="(v) => (menu_ids = v)"
                  @menu-selection-change="handleMenuSelectionChange"
                />
              </div>
            </NTabPane>
            <NTabPane name="resource" tab="接口权限" display-directive="show">
              <div class="tab-content">
                <ApiPermissionTree
                  ref="apiTreeRef"
                  :api-data="apiOption"
                  :selected-apis="api_ids"
                  :show-method="true"
                  :show-path="true"
                  @update:selected-apis="(v) => (api_ids = v)"
                  @api-selection-change="handleApiSelectionChange"
                />
              </div>
            </NTabPane>
          </NTabs>
        </div>
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

/* 权限抽屉样式优化 */
.permission-drawer :deep(.n-drawer-body-content-wrapper) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.permission-drawer-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.drawer-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color-1);
}

.drawer-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
}

.action-bar {
  flex-shrink: 0;
  padding: 16px 0;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 12px;
}

.permission-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.permission-tabs :deep(.n-tabs-nav) {
  flex-shrink: 0;
}

.permission-tabs :deep(.n-tabs-content) {
  flex: 1;
  overflow: hidden;
}

.permission-tabs :deep(.n-tab-pane) {
  height: 100%;
  overflow: hidden;
}

.tab-content {
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 优化权限树在抽屉中的显示 */
.permission-drawer :deep(.api-permission-tree),
.permission-drawer :deep(.menu-permission-tree) {
  height: 100%;
  max-height: calc(100vh - 250px);
}

.permission-drawer :deep(.tree-section) {
  max-height: calc(100vh - 400px);
}
</style>