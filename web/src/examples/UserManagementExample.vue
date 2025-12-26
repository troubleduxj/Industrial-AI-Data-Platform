<!--
用户管理页面示例
展示如何使用增强的权限控制系统
-->
<template>
  <div class="user-management">
    <n-card title="用户管理" class="mb-4">
      <!-- 页面级权限检查 -->
      <div v-if="!canAccess" class="no-permission">
        <n-result status="403" title="权限不足" description="您没有权限访问此页面">
          <template #footer>
            <n-button @click="$router.go(-1)">返回</n-button>
          </template>
        </n-result>
      </div>

      <div v-else>
        <!-- 工具栏 -->
        <div class="toolbar mb-4">
          <!-- 使用权限按钮组件 -->
          <PermissionButton permission="POST /api/v2/users" type="primary" @click="handleCreate">
            <template #icon>
              <n-icon><AddIcon /></n-icon>
            </template>
            新增用户
          </PermissionButton>

          <!-- 使用指令方式的权限控制 -->
          <n-button
            v-permission="'POST /api/v2/users/batch'"
            type="info"
            class="ml-2"
            @click="handleBatchImport"
          >
            批量导入
          </n-button>

          <!-- 角色权限控制 -->
          <n-button
            v-permission.role="'admin'"
            type="warning"
            class="ml-2"
            @click="handleSystemSettings"
          >
            系统设置
          </n-button>

          <!-- 多权限检查 - 需要所有权限 -->
          <n-button
            v-permission.all="['GET /api/v2/users/export', 'POST /api/v2/users/export']"
            type="success"
            class="ml-2"
            @click="handleExport"
          >
            导出数据
          </n-button>

          <!-- 权限不足时禁用而不是隐藏 -->
          <n-button
            v-permission.disable="'DELETE /api/v2/users/batch'"
            type="error"
            class="ml-2"
            @click="handleBatchDelete"
          >
            批量删除
          </n-button>
        </div>

        <!-- 数据表格 -->
        <n-data-table
          :columns="columns"
          :data="userData"
          :loading="loading"
          :pagination="pagination"
        />
      </div>
    </n-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { NCard, NButton, NDataTable, NResult, NIcon, useMessage } from 'naive-ui'
import { AddIcon } from '@vicons/ionicons5'
import { usePermission, usePagePermission, useButtonPermission } from '@/composables/usePermission'
import PermissionButton from '@/components/common/PermissionButton.vue'

const message = useMessage()

// 页面权限检查
const { canAccess, checkAccess } = usePagePermission(['GET /api/v2/users', 'user:read'])

// 按钮权限检查
const userPermissions = useButtonPermission('user')
const { hasPermission, checkMultiplePermissions, createPermissionGuard } = usePermission()

// 数据
const userData = ref([])
const loading = ref(false)

// 分页配置
const pagination = ref({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  onChange: (page) => {
    pagination.value.page = page
    loadUserData()
  },
  onUpdatePageSize: (pageSize) => {
    pagination.value.pageSize = pageSize
    pagination.value.page = 1
    loadUserData()
  },
})

// 表格列配置
const columns = computed(() => {
  const baseColumns = [
    {
      title: 'ID',
      key: 'id',
      width: 80,
    },
    {
      title: '用户名',
      key: 'username',
      width: 120,
    },
    {
      title: '邮箱',
      key: 'email',
      width: 200,
    },
    {
      title: '状态',
      key: 'is_active',
      width: 100,
      render: (row) => (row.is_active ? '启用' : '禁用'),
    },
    {
      title: '创建时间',
      key: 'created_at',
      width: 180,
    },
  ]

  // 根据权限动态添加操作列
  if (userPermissions.canUpdate.value || userPermissions.canDelete.value) {
    baseColumns.push({
      title: '操作',
      key: 'actions',
      width: 200,
      render: (row) => {
        return [
          // 编辑按钮
          userPermissions.canUpdate.value &&
            h(
              NButton,
              {
                size: 'small',
                type: 'primary',
                onClick: () => handleEdit(row),
              },
              { default: () => '编辑' }
            ),

          // 删除按钮
          userPermissions.canDelete.value &&
            h(
              NButton,
              {
                size: 'small',
                type: 'error',
                style: { marginLeft: '8px' },
                onClick: () => handleDelete(row),
              },
              { default: () => '删除' }
            ),

          // 重置密码按钮 - 使用权限守卫
          createPermissionGuard('POST /api/v2/users/{id}/actions/reset-password', () =>
            message.warning('您没有重置密码的权限')
          )() &&
            h(
              NButton,
              {
                size: 'small',
                type: 'warning',
                style: { marginLeft: '8px' },
                onClick: () => handleResetPassword(row),
              },
              { default: () => '重置密码' }
            ),
        ].filter(Boolean)
      },
    })
  }

  return baseColumns
})

// 批量权限检查
const batchPermissions = checkMultiplePermissions([
  { key: 'canBatchDelete', permission: 'DELETE /api/v2/users/batch' },
  { key: 'canExport', permission: 'GET /api/v2/users/export' },
  { key: 'canImport', permission: 'POST /api/v2/users/import' },
  { key: 'canViewAuditLog', type: 'role', roles: ['admin', 'auditor'] },
])

// 方法
const loadUserData = async () => {
  if (!checkAccess()) return

  loading.value = true
  try {
    // 模拟API调用
    await new Promise((resolve) => setTimeout(resolve, 1000))
    userData.value = [
      {
        id: 1,
        username: 'admin',
        email: 'admin@example.com',
        is_active: true,
        created_at: '2024-01-01 10:00:00',
      },
      {
        id: 2,
        username: 'user1',
        email: 'user1@example.com',
        is_active: true,
        created_at: '2024-01-02 10:00:00',
      },
    ]
    pagination.value.itemCount = userData.value.length
  } catch (error) {
    message.error('加载用户数据失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  message.info('打开新增用户对话框')
}

const handleEdit = (row) => {
  message.info(`编辑用户: ${row.username}`)
}

const handleDelete = (row) => {
  message.warning(`删除用户: ${row.username}`)
}

const handleResetPassword = (row) => {
  message.info(`重置用户密码: ${row.username}`)
}

const handleBatchImport = () => {
  if (!batchPermissions.value.canImport) {
    message.warning('您没有批量导入的权限')
    return
  }
  message.info('打开批量导入对话框')
}

const handleBatchDelete = () => {
  if (!batchPermissions.value.canBatchDelete) {
    message.warning('您没有批量删除的权限')
    return
  }
  message.warning('执行批量删除操作')
}

const handleExport = () => {
  if (!batchPermissions.value.canExport) {
    message.warning('您没有导出数据的权限')
    return
  }
  message.info('开始导出用户数据')
}

const handleSystemSettings = () => {
  message.info('打开系统设置页面')
}

// 生命周期
onMounted(() => {
  loadUserData()
})
</script>

<style scoped>
.user-management {
  padding: 16px;
}

.toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.no-permission {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.ml-2 {
  margin-left: 8px;
}

.mb-4 {
  margin-bottom: 16px;
}
</style>
