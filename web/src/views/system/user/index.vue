<script setup lang="ts">
import {
  h,
  onMounted,
  ref,
  resolveDirective,
  withDirectives,
  onActivated,
} from 'vue'
import {
  NButton,
  NCheckbox,
  NCheckboxGroup,
  NForm,
  NFormItem,
  NInput,
  NSpace,
  NSwitch,
  NTag,
  NPopconfirm,
  NTreeSelect,
  NTree,
  useMessage,
  useDialog,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import BatchDeleteButton from '@/components/common/BatchDeleteButton.vue'
import PermissionButton from '@/components/Permission/PermissionButton.vue'

import { formatDate, renderIcon } from '@/utils'
import { useCRUD } from '@/composables/useCRUD'
import { useUserBatchDelete } from '@/composables/useBatchDelete'
import systemV2Api from '@/api/system-v2'
import TheIcon from '@/components/icon/TheIcon.vue'
import { useUserStore } from '@/store'

defineOptions({ name: 'SystemUser' })

// ==================== 类型定义 ====================

interface QueryItems {
  [key: string]: any
}

interface UserInfo {
  id: string | number
  username: string
  email?: string
  password?: string
  confirmPassword?: string
  is_superuser?: boolean
  is_active?: boolean
  roles?: any[]
  role_ids?: any[]
  dept_id?: string | number
  dept?: any
  [key: string]: any
}

const queryItems = ref<QueryItems>({})
const vPermission = resolveDirective('permission')
const $message = useMessage()
const $dialog = useDialog()

// CRUD anagement for modal
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
  name: '用户',
  initForm: {} as any,
  doCreate: systemV2Api.createUser,
  doUpdate: systemV2Api.updateUser,
  doDelete: systemV2Api.deleteUser,
  refresh: () => getUsers(),
})

// 用户保护检查函数
const isCurrentUser = (user) => {
  if (!user || typeof user.id === 'undefined') return false
  const userStore = useUserStore()
  return user.id === userStore.userInfo?.id
}

const isAdminUser = (user) => {
  if (!user || !user.username) return false
  // 大小写不敏感的admin用户检查
  return user.username.toLowerCase() === 'admin'
}

const isSuperUser = (user) => {
  if (!user) return false
  return user.is_superuser === true
}

const canDelete = (user) => {
  // 处理空值情况
  if (!user) {
    return { 
      valid: false, 
      reason: '用户数据无效',
      type: 'error',
      severity: 'high'
    }
  }

  // 按照设计文档中的检查顺序：当前用户 -> admin用户 -> 超级管理员
  if (isCurrentUser(user)) {
    return { 
      valid: false, 
      reason: '不能删除当前登录用户',
      type: 'warning',
      severity: 'medium',
      icon: '⚠️'
    }
  }

  if (isAdminUser(user)) {
    return { 
      valid: false, 
      reason: '不能删除admin管理员账户',
      type: 'error',
      severity: 'high',
      icon: '🚫'
    }
  }

  if (isSuperUser(user)) {
    return { 
      valid: false, 
      reason: '不能删除超级管理员',
      type: 'error',
      severity: 'high',
      icon: '🔒'
    }
  }

  return { 
    valid: true,
    type: 'success',
    severity: 'low'
  }
}

// 批量删除组合式函数
const {
  selectedItems,
  selectedRowKeys,
  selectedCount,
  isLoading: batchDeleteLoading,
  handleBatchDelete,
  setSelectedItems,
} = useUserBatchDelete({
  batchDeleteApi: systemV2Api.users.batchDelete,
  refresh: () => getUsers(),
  validateItem: canDelete,
})

const roleOption = ref([])
const deptOption = ref([])

/**
 * 将平铺的部门数据转换为树状结构
 * @param {Array} deptList - 平铺的部门数据数组
 * @returns {Array} 树状结构的部门数据
 */
function buildDeptTree(deptList) {
  if (!Array.isArray(deptList) || deptList.length === 0) {
    return []
  }

  // 创建一个映射表，用于快速查找部门
  const deptMap = new Map()
  const result = []

  // 首先将所有部门放入映射表，并初始化children数组
  deptList.forEach((dept) => {
    deptMap.set(dept.id, {
      ...dept,
      children: [],
    })
  })

  // 构建树状结构
  deptList.forEach((dept) => {
    const deptNode = deptMap.get(dept.id)
    if (dept.parent_id && dept.parent_id !== 0) {
      // 如果有父部门，将当前部门添加到父部门的children中
      const parentNode = deptMap.get(dept.parent_id)
      if (parentNode) {
        parentNode.children.push(deptNode)
      } else {
        // 如果找不到父部门，作为根节点处理
        result.push(deptNode)
      }
    } else {
      // 没有父部门，作为根节点
      result.push(deptNode)
    }
  })

  return result
}
const tableData = ref([])
const loading = ref(false)

// pagination
const pagination = ref({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
})

// page events
function handlePageChange(page) {
  pagination.value.page = page
  getUsers()
}

function handlePageSizeChange(pageSize) {
  pagination.value.page = 1
  pagination.value.pageSize = pageSize
  getUsers()
}

function handleSearch() {
  pagination.value.page = 1
  getUsers()
}

async function getUsers() {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      pageSize: pagination.value.pageSize,
      ...queryItems.value,
    }
    
    // 直接调用API，不使用safeDataFetch避免自动退出登录
    const [userRes, roleRes, deptRes] = await Promise.all([
      systemV2Api.getUserList(params),
      systemV2Api.getRoleList({ page: 1, pageSize: 100 }),
      systemV2Api.getDepts()
    ])
    
    tableData.value = userRes.data || []
    pagination.value.itemCount = userRes.total || 0
    roleOption.value = roleRes.data || []
    // 将平铺的部门数据转换为树状结构
    deptOption.value = buildDeptTree(deptRes.data || [])
    
  } catch (error) {
    console.error('获取用户数据失败:', error)
    
    // 检查是否是认证错误
    if (error.response?.status === 401 || error.code === 401) {
      console.warn('检测到认证错误，可能需要重新登录')
      $message?.error('登录已过期，请重新登录。请手动刷新页面或点击登录按钮重新登录。', {
        duration: 0, // 不自动消失
        closable: true
      })
      
      // 不自动清除认证信息，让用户自己决定
      // 不自动跳转，让用户自己操作
    } else {
      $message?.error('获取用户数据失败: ' + (error.message || '未知错误'))
    }
    
    // 最后的兜底处理
    tableData.value = []
    pagination.value.itemCount = 0
    roleOption.value = []
    deptOption.value = []
  } finally {
    loading.value = false
  }
}

// 处理表格行选择
const handleTableSelection = (rowKeys, rows) => {
  setSelectedItems(rows || [], rowKeys || [])
}

onMounted(() => {
  getUsers()
})

onActivated(() => {
  getUsers()
})

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
    width: 80,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '用户名',
    key: 'username',
    width: 120,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h(
        'span',
        {
          style: {
            color: row.is_active ? 'inherit' : 'var(--n-text-color-disabled)',
          },
        },
        row.username
      )
    },
  },
  {
    title: '用户角色',
    key: 'role',
    width: 150,
    align: 'center',
    render(row) {
      const roles = row.roles ?? []
      const group = []
      for (let i = 0; i < roles.length; i++)
        group.push(
          h(NTag, { type: 'info', style: { margin: '2px 3px' } }, { default: () => roles[i].name })
        )
      return h('span', group)
    },
  },
  {
    title: '部门',
    key: 'dept',
    width: 120,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h('span', row.dept?.name || '未分配部门')
    },
  },
  {
    title: '邮箱',
    key: 'email',
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h(
        'span',
        {
          style: {
            color: row.is_active ? 'inherit' : 'var(--n-text-color-disabled)',
          },
        },
        row.email || '未设置'
      )
    },
  },
  {
    title: '超级用户',
    key: 'is_superuser',
    width: 100,
    align: 'center',
    render(row) {
      return h(
        NTag,
        { type: 'info', style: { margin: '2px 3px' } },
        { default: () => (row.is_superuser ? '是' : '否') }
      )
    },
  },
  {
    title: '上次登录时间',
    key: 'last_login',
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h(
        'span',
        { class: 'text-sm' },
        row.last_login !== null ? formatDate(row.last_login) : '-'
      )
    },
  },
  {
    title: '状态',
    key: 'is_active',
    width: 80,
    align: 'center',
    render(row) {
      // 使用PermissionButton包装Switch，但保持Switch的外观
      return h(
        'div',
        {},
        h(PermissionButton, {
          permission: 'PUT /api/v2/users/{id}',
          type: 'default',
          size: 'small',
          style: 'padding: 0; border: none; background: transparent;',
          onClick: () => handleUpdateDisable(row)
        }, {
          default: () => h(NSwitch, {
            size: 'small',
            rubberBand: false,
            value: row.is_active,
            loading: !!row.publishing,
            checkedValue: true,
            uncheckedValue: false,
            disabled: false, // 由PermissionButton控制禁用状态
          })
        })
      )
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 300,
    align: 'center',
    fixed: 'right',
    render(row) {
      // 检查用户是否可以删除
      const deleteCheck = canDelete(row)
      const canDeleteUser = deleteCheck.valid
      
      const actions = []
      
      // 编辑按钮 - 始终显示
      actions.push(
        h(PermissionButton, {
          permission: 'PUT /api/v2/users/{id}',
          size: 'small',
          type: 'primary',
          style: 'margin-right: 8px;',
          onClick: () => {
            handleEdit(row)
            modalForm.value.dept_id = row.dept?.id
            modalForm.value.role_ids = (row.roles || []).map((e) => e.id)
            delete modalForm.value.dept
          },
        }, {
          default: () => '编辑',
          icon: renderIcon('material-symbols:edit', { size: 16 }),
        })
      )
      
      // 删除按钮 - 仅在用户可删除时显示
      if (canDeleteUser) {
        actions.push(
          h(PermissionButton, {
            permission: 'DELETE /api/v2/users/{id}',
            size: 'small',
            type: 'error',
            style: 'margin-right: 8px;',
            needConfirm: true,
            confirmTitle: '删除确认',
            confirmContent: '确定删除该用户吗？此操作不可恢复。',
            onConfirm: () => handleDelete({ user_id: row.id }, false)
          }, {
            default: () => '删除',
            icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
          })
        )
      } else {
        // 显示保护状态提示 - 增强用户体验
        const protectionInfo = deleteCheck
        actions.push(
          h(
            NButton,
            {
              size: 'small',
              type: 'default',
              disabled: true,
              style: 'cursor: not-allowed; opacity: 0.6; margin-right: 8px;',
              title: protectionInfo.reason
            },
            {
              default: () => h('span', { 
                style: 'color: var(--text-color-disabled); font-size: var(--font-size-xs);' 
              }, `${protectionInfo.icon || '🛡️'} 受保护`),
              icon: renderIcon('material-symbols:shield', { size: 14 }),
            }
          )
        )
      }
      
      // 重置密码按钮 - 仅对非超级用户显示
      if (!row.is_superuser) {
        actions.push(
          h(PermissionButton, {
            permission: 'POST /api/v2/users/{id}/actions/reset-password',
            size: 'small',
            type: 'warning',
            style: 'margin-right: 8px;',
            needConfirm: true,
            confirmTitle: '重置密码确认',
            confirmContent: '确定重置用户密码为123456吗？',
            onConfirm: async () => {
              try {
                await systemV2Api.resetPassword({ user_id: row.id })
                $message.success('密码已成功重置为123456')
                await getUsers()
              } catch (error) {
                // 错误已经由HTTP拦截器处理，这里只记录日志
                console.error('重置密码失败:', error)
                // 检查错误是否已经被处理过，避免重复提示
                if (!(error && typeof error === 'object' && error.success === false)) {
                  $message.error('重置密码失败: ' + error.message)
                }
              }
            }
          }, {
            default: () => '重置密码',
            icon: renderIcon('material-symbols:lock-reset', { size: 16 }),
          })
        )
      }
      
      return h('div', { style: 'display: flex; align-items: center; justify-content: center; flex-wrap: nowrap;' }, actions)
    },
  },
]

// 修改用户禁用状态
async function handleUpdateDisable(row) {
  if (!row.id) return
  const userStore = useUserStore()
  if (userStore.userId === row.id) {
    $message.error('当前登录用户不可禁用！')
    return
  }
  
  // 保存原始状态，用于错误时恢复
  const originalStatus = row.is_active
  
  try {
    row.publishing = true
    
    // 切换状态
    const newStatus = !row.is_active
    
    // 准备更新数据
    const role_ids = []
    if (row.roles && Array.isArray(row.roles)) {
      row.roles.forEach((e) => {
        role_ids.push(e.id)
      })
    }
    
    // 简化更新数据，只更新必要字段
    const updateData = {
      id: row.id,
      is_active: newStatus
    }
    
    console.log('🔄 更新用户状态:', {
      userId: row.id,
      username: row.username,
      originalStatus,
      newStatus,
      updateData
    })
    
    // 调用API更新用户
    const response = await systemV2Api.updateUser(updateData)
    console.log('✅ API响应:', response)
    
    // 检查响应中的实际状态
    if (response && response.data && typeof response.data.is_active !== 'undefined') {
      const actualStatus = response.data.is_active
      console.log('🔍 API返回的实际状态:', actualStatus)
      
      if (actualStatus === newStatus) {
        // 更新本地状态
        row.is_active = newStatus
        $message?.success(newStatus ? '用户已启用' : '用户已禁用')
      } else {
        console.warn('⚠️ API返回的状态与期望不符:', { expected: newStatus, actual: actualStatus })
        $message?.warning('状态更新可能未成功，请刷新页面查看')
      }
    } else {
      console.warn('⚠️ API响应格式异常:', response)
      // 更新本地状态（假设成功）
      row.is_active = newStatus
      $message?.success(newStatus ? '用户已启用' : '用户已禁用')
    }
    
    await getUsers()
  } catch (err) {
    // 有异常恢复原来的状态
    row.is_active = originalStatus
    $message?.error('更新用户状态失败: ' + (err.message || '未知错误'))
    console.error('更新用户状态失败:', err)
  } finally {
    row.publishing = false
  }
}

let lastClickedNodeId = null

const nodeProps = ({ option }) => {
  return {
    onClick() {
      if (lastClickedNodeId === option.id) {
        queryItems.value.dept_id = undefined
        handleSearch()
        lastClickedNodeId = null
      } else {
        queryItems.value.dept_id = option.id
        handleSearch()
        lastClickedNodeId = option.id
      }
    },
  }
}

const validateAddUser = {
  username: [
    {
      required: true,
      message: '请输入名称',
      trigger: ['input', 'blur'],
    },
  ],
  email: [
    {
      required: true,
      message: '请输入邮箱地址',
      trigger: ['input', 'change'],
    },
    {
      trigger: ['blur'],
      validator: (rule: any, value: any) => {
        // 更新邮箱验证正则表达式，支持用户名中的点号
        const re = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
        if (modalForm.value.email && !re.test(modalForm.value.email)) {
          return new Error('邮箱格式错误')
        }
        return true
      },
    },
  ],
  password: [
    {
      required: true,
      message: '请输入密码',
      trigger: ['input', 'blur', 'change'],
    },
  ],
  confirmPassword: [
    {
      required: true,
      message: '请再次输入密码',
      trigger: ['input'],
    },
    {
      trigger: ['blur'],
      validator: (rule: any, value: any) => {
        if (value && value !== modalForm.value.password) {
          return new Error('两次密码输入不一致')
        }
        return true
      },
    },
  ],
  role_ids: [
    {
      type: 'array' as const,
      required: true,
      message: '请至少选择一个角色',
      trigger: ['blur', 'change'],
    },
  ],
}
</script>

<template>
  <CommonPage show-footer title="用户列表" class="system-user-page system-management-page standard-page">
    <template #action>
      <div class="flex items-center gap-3">
        <BatchDeleteButton
          :selected-items="selectedItems"
          :selected-count="selectedCount"
          resource-name="用户"
          permission="DELETE /api/v2/users/batch"
          :exclude-condition="(user) => !canDelete(user).valid"
          :loading="batchDeleteLoading"
          @batch-delete="handleBatchDelete"
        />
        
        <PermissionButton 
          permission="POST /api/v2/users" 
          type="primary" 
          @click="handleAdd"
        >
          <TheIcon icon="material-symbols:add" :size="18" class="mr-1" />新建用户
        </PermissionButton>
      </div>
    </template>

    <!-- 用户管理页面内容区域 -->
    <div class="h-full flex">
      <!-- 左侧部门树 -->
      <div class="w-220px flex-shrink-0 border-r standard-sidebar bg-base border-light">
        <div class="p-3">
          <div class="dept-filter-title mb-3 text-lg text-gray-900 font-bold">部门筛选</div>
          <NTree
            block-line
            :data="deptOption"
            key-field="id"
            label-field="name"
            :node-props="nodeProps"
            default-expand-all
            class="dept-tree"
          />
        </div>
      </div>

      <!-- 右侧用户列表 -->
      <div class="min-w-0 flex-1">
        <!-- 表格 -->
        <CrudTable
          v-model:query-items="queryItems"
          v-model:checked-row-keys="selectedRowKeys"
          :columns="columns"
          :data="tableData"
          :loading="loading"
          :pagination="pagination"
          :scroll-x="1400"
          @on-page-change="handlePageChange"
          @on-page-size-change="handlePageSizeChange"
          @on-checked="handleTableSelection"
        >
          <template #queryBar>
            <QueryBarItem label="名称" :label-width="40">
              <NInput
                v-model:value="queryItems.username"
                clearable
                type="text"
                placeholder="请输入用户名称"
                @keypress.enter="handleSearch"
              />
            </QueryBarItem>
            <QueryBarItem label="邮箱" :label-width="40">
              <NInput
                v-model:value="queryItems.email"
                clearable
                type="text"
                placeholder="请输入邮箱"
                @keypress.enter="handleSearch"
              />
            </QueryBarItem>
          </template>
        </CrudTable>
      </div>
    </div>

    <!-- 新增/编辑 弹窗 -->
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
        :rules="validateAddUser"
      >
        <NFormItem label="用户名称" path="username">
          <NInput v-model:value="modalForm.username" clearable placeholder="请输入用户名称" />
        </NFormItem>
        <NFormItem label="邮箱" path="email">
          <NInput v-model:value="modalForm.email" clearable placeholder="请输入邮箱" />
        </NFormItem>
        <NFormItem v-if="modalAction === 'add'" label="密码" path="password">
          <NInput
            v-model:value="modalForm.password"
            show-password-on="mousedown"
            type="password"
            clearable
            placeholder="请输入密码"
          />
        </NFormItem>
        <NFormItem v-if="modalAction === 'add'" label="确认密码" path="confirmPassword">
          <NInput
            v-model:value="modalForm.confirmPassword"
            show-password-on="mousedown"
            type="password"
            clearable
            placeholder="请确认密码"
          />
        </NFormItem>
        <NFormItem label="角色" path="role_ids">
          <NCheckboxGroup v-model:value="modalForm.role_ids">
            <NSpace item-style="display: flex;">
              <NCheckbox v-for="item in roleOption" :key="item.id" :value="item.id">
                {{ item.name }}
              </NCheckbox>
            </NSpace>
          </NCheckboxGroup>
        </NFormItem>
        <NFormItem label="超级用户" path="is_superuser">
          <NSwitch
            v-model:value="modalForm.is_superuser"
            size="small"
            :checked-value="true"
            :unchecked-value="false"
          ></NSwitch>
        </NFormItem>
        <NFormItem label="启用状态" path="is_active">
          <NSwitch
            v-model:value="modalForm.is_active"
            :checked-value="true"
            :unchecked-value="false"
            :default-value="true"
          />
        </NFormItem>
        <NFormItem label="部门" path="dept_id">
          <NTreeSelect
            v-model:value="modalForm.dept_id"
            :options="deptOption"
            key-field="id"
            label-field="name"
            placeholder="请选择部门"
            clearable
            default-expand-all
          ></NTreeSelect>
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>

<style scoped>
/* 部门筛选标题样式 */
.dept-filter-title {
  font-size: var(--font-size-lg) !important;
  font-weight: var(--font-weight-bold) !important;
  color: var(--text-color-primary) !important;
  line-height: var(--line-height-normal);
  letter-spacing: 0.025em;
}

.dept-tree {
  font-size: var(--font-size-sm);
}

.dept-tree :deep(.n-tree-node-content) {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-base);
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.dept-tree :deep(.n-tree-node-content:hover) {
  background-color: var(--background-color-light);
}

.dept-tree :deep(.n-tree-node-content--selected) {
  background-color: var(--primary-color-light);
  color: var(--primary-foreground);
}

/* 确保左侧部门树区域的边框样式 */
.w-220px {
  width: 220px;
}
</style>
