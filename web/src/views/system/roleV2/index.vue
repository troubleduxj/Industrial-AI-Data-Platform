<!--
增强的角色管理页面
展示如何使用权限树组件进行角色权限管理
-->
<template>
  <div class="role-management">
    <n-card title="角色管理">
      <!-- 工具栏 -->
      <template #header-extra>
        <n-space>
          <PermissionButton permission="POST /api/v2/roles" type="primary" @click="handleCreate">
            <template #icon>
              <n-icon><AddIcon /></n-icon>
            </template>
            新增角色
          </PermissionButton>

          <PermissionButton permission="GET /api/v2/roles" @click="refreshData">
            <template #icon>
              <n-icon><RefreshIcon /></n-icon>
            </template>
            刷新
          </PermissionButton>
        </n-space>
      </template>

      <!-- 角色列表 -->
      <n-data-table
        :columns="columns"
        :data="roleData"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row) => row.id"
        :scroll-x="1000"
      />
    </n-card>

    <!-- 角色编辑对话框 -->
    <n-modal
      v-model:show="showEditModal"
      :mask-closable="false"
      preset="card"
      :title="editingRole.id ? '编辑角色' : '新增角色'"
      class="role-edit-modal"
      :style="{ width: '80%', maxWidth: '1200px' }"
    >
      <n-form
        ref="formRef"
        :model="editingRole"
        :rules="formRules"
        label-placement="left"
        label-width="100px"
      >
        <n-grid :cols="24" :x-gap="24">
          <!-- 基本信息 -->
          <n-form-item-gi :span="12" label="角色名称" path="role_name">
            <n-input
              v-model:value="editingRole.role_name"
              placeholder="请输入角色名称"
              :disabled="editingRole.id && editingRole.role_name === 'admin'"
            />
          </n-form-item-gi>

          <n-form-item-gi :span="12" label="角色描述" path="remark">
            <n-input v-model:value="editingRole.remark" placeholder="请输入角色描述" />
          </n-form-item-gi>
        </n-grid>

        <!-- 权限配置 -->
        <n-divider title-placement="left">
          <n-text strong>权限配置</n-text>
        </n-divider>

        <n-tabs type="line" animated>
          <!-- API权限 -->
          <n-tab-pane name="api" tab="API权限">
            <div class="permission-section">
              <n-alert type="info" class="mb-4">
                <template #header>
                  <n-icon><InfoIcon /></n-icon>
                  权限说明
                </template>
                请为角色选择相应的API访问权限。权限采用树形结构，支持按模块和操作类型进行批量选择。
              </n-alert>

              <PermissionTree
                :permissions="allPermissions"
                :selected-permissions="editingRole.apis || []"
                @update:selected-permissions="handleApiPermissionsChange"
              />
            </div>
          </n-tab-pane>

          <!-- 菜单权限 -->
          <n-tab-pane name="menu" tab="菜单权限">
            <div class="permission-section">
              <n-alert type="info" class="mb-4">
                <template #header>
                  <n-icon><InfoIcon /></n-icon>
                  菜单权限说明
                </template>
                选择角色可以访问的菜单项。菜单权限控制用户在系统中可以看到的导航菜单。
              </n-alert>

              <n-tree
                :data="menuTreeData"
                :checked-keys="selectedMenuKeys"
                checkable
                :cascade="false"
                virtual-scroll
                block-line
                @update:checked-keys="handleMenuPermissionsChange"
              >
                <template #default="{ option }">
                  <div class="menu-node">
                    <n-icon class="menu-icon">
                      <component :is="getMenuIcon(option)" />
                    </n-icon>
                    <span class="menu-label">{{ option.name }}</span>
                    <n-tag v-if="option.component" size="small" type="info">
                      {{ option.component }}
                    </n-tag>
                  </div>
                </template>
              </n-tree>
            </div>
          </n-tab-pane>

          <!-- 权限预览 -->
          <n-tab-pane name="preview" tab="权限预览">
            <div class="permission-preview">
              <n-grid :cols="2" :x-gap="24">
                <n-gi>
                  <n-card title="API权限" size="small">
                    <n-scrollbar style="max-height: 300px">
                      <n-space vertical size="small">
                        <div
                          v-for="api in editingRole.apis || []"
                          :key="`${api.method}_${api.path}`"
                          class="permission-item"
                        >
                          <n-tag :type="getMethodTagType(api.method)" size="small">
                            {{ api.method }}
                          </n-tag>
                          <span class="permission-path">{{ api.path }}</span>
                          <span class="permission-summary">{{ api.summary }}</span>
                        </div>
                      </n-space>
                    </n-scrollbar>
                  </n-card>
                </n-gi>

                <n-gi>
                  <n-card title="菜单权限" size="small">
                    <n-scrollbar style="max-height: 300px">
                      <n-space vertical size="small">
                        <div v-for="menu in selectedMenus" :key="menu.id" class="permission-item">
                          <n-icon class="menu-icon">
                            <component :is="getMenuIcon(menu)" />
                          </n-icon>
                          <span class="menu-name">{{ menu.name }}</span>
                          <span class="menu-path">{{ menu.path }}</span>
                        </div>
                      </n-space>
                    </n-scrollbar>
                  </n-card>
                </n-gi>
              </n-grid>
            </div>
          </n-tab-pane>
        </n-tabs>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showEditModal = false">取消</n-button>
          <PermissionButton
            permission="PUT /api/v2/roles/{role_id}"
            type="primary"
            :loading="saving"
            @click="
              () => {
                console.log('保存按钮被点击')
                handleSave()
              }
            "
          >
            保存
          </PermissionButton>
        </n-space>
      </template>
    </n-modal>

    <!-- 权限详情对话框 -->
    <n-modal
      v-model:show="showPermissionModal"
      preset="card"
      title="角色权限详情"
      :style="{ width: '70%', maxWidth: '800px' }"
    >
      <div v-if="viewingRole">
        <n-descriptions :column="2" bordered>
          <n-descriptions-item label="角色名称">
            {{ viewingRole.role_name }}
          </n-descriptions-item>
          <n-descriptions-item label="角色描述">
            {{ viewingRole.remark || '无' }}
          </n-descriptions-item>
          <n-descriptions-item label="API权限数量">
            {{ viewingRole.apis?.length || 0 }}
          </n-descriptions-item>
          <n-descriptions-item label="菜单权限数量">
            {{ viewingRole.menus?.length || 0 }}
          </n-descriptions-item>
        </n-descriptions>

        <n-divider />

        <n-tabs type="line">
          <n-tab-pane name="apis" tab="API权限">
            <n-data-table
              :columns="apiPermissionColumns"
              :data="viewingRole.apis || []"
              :pagination="{ pageSize: 10 }"
              size="small"
            />
          </n-tab-pane>

          <n-tab-pane name="menus" tab="菜单权限">
            <n-data-table
              :columns="menuPermissionColumns"
              :data="viewingRole.menus || []"
              :pagination="{ pageSize: 10 }"
              size="small"
            />
          </n-tab-pane>
        </n-tabs>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h, nextTick } from 'vue'
import {
  NCard,
  NButton,
  NDataTable,
  NModal,
  NForm,
  NFormItemGi,
  NGrid,
  NInput,
  NSpace,
  NIcon,
  NTabs,
  NTabPane,
  NTree,
  NAlert,
  NTag,
  NText,
  NDivider,
  NScrollbar,
  NDescriptions,
  NDescriptionsItem,
  useMessage,
  useDialog,
} from 'naive-ui'
import {
  AddOutline as AddIcon,
  RefreshOutline as RefreshIcon,
  InformationCircleOutline as InfoIcon,
  EyeOutline as ViewIcon,
  CreateOutline as EditIcon,
  TrashOutline as DeleteIcon,
  FolderOutline as FolderIcon,
  DocumentOutline as DocumentIcon,
} from '@vicons/ionicons5'

import PermissionTree from '@/components/system/PermissionTree.vue'
import PermissionButton from '@/components/common/PermissionButton.vue'
import { usePermission } from '@/composables/usePermission'
import { createSystemApis } from '@/utils/api-v2-migration.js'
import { systemApi } from '@/api/system-v2.js'

const message = useMessage()
const dialog = useDialog()
const { hasPermission } = usePermission()

// 创建系统API实例
const systemApis = createSystemApis()

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const showEditModal = ref(false)
const showPermissionModal = ref(false)
const formRef = ref(null)

const roleData = ref([])
const allPermissions = ref([])
const allMenus = ref([])
const editingRole = ref({})
const viewingRole = ref(null)

// 分页配置
const pagination = ref({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
})

// 表单验证规则
const formRules = {
  role_name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' },
    { min: 2, max: 20, message: '角色名称长度在2-20个字符', trigger: 'blur' },
  ],
}

// 表格列配置
const columns = computed(() => [
  {
    title: 'ID',
    key: 'id',
    minWidth: 80,
  },
  {
    title: '角色名称',
    key: 'role_name',
    minWidth: 150,
    render: (row) => h('strong', row.role_name),
  },
  {
    title: '角色描述',
    key: 'remark',
    minWidth: 200,
    ellipsis: {
      tooltip: true,
    },
  },
  {
    title: 'API权限',
    key: 'api_count',
    minWidth: 100,
    render: (row) =>
      h(NTag, { type: 'info', size: 'small' }, { default: () => `${row.apis?.length || 0}个` }),
  },
  {
    title: '菜单权限',
    key: 'menu_count',
    minWidth: 100,
    render: (row) =>
      h(NTag, { type: 'success', size: 'small' }, { default: () => `${row.menus?.length || 0}个` }),
  },
  {
    title: '创建时间',
    key: 'created_at',
    minWidth: 180,
  },
  {
    title: '操作',
    key: 'actions',
    width: 300,
    fixed: 'right',
    render: (row) =>
      h(
        NSpace,
        { size: 'small', align: 'center', justify: 'start', wrap: false },
        {
          default: () =>
            [
              h(
                NButton,
                {
                  size: 'small',
                  type: 'info',
                  onClick: () => handleViewPermissions(row),
                },
                {
                  default: () => '查看权限',
                  icon: () => h(NIcon, null, { default: () => h(ViewIcon) }),
                }
              ),

              hasPermission('PUT /api/v2/roles/{id}') &&
                h(
                  NButton,
                  {
                    size: 'small',
                    type: 'primary',
                    onClick: () => handleEdit(row),
                  },
                  {
                    default: () => '编辑',
                    icon: () => h(NIcon, null, { default: () => h(EditIcon) }),
                  }
                ),

              hasPermission('DELETE /api/v2/roles/{id}') &&
                row.role_name !== 'admin' &&
                h(
                  NButton,
                  {
                    size: 'small',
                    type: 'error',
                    onClick: () => handleDelete(row),
                  },
                  {
                    default: () => '删除',
                    icon: () => h(NIcon, null, { default: () => h(DeleteIcon) }),
                  }
                ),
            ].filter(Boolean),
        }
      ),
  },
])

// 权限详情表格列
const apiPermissionColumns = [
  { title: '方法', key: 'method', width: 80 },
  { title: '路径', key: 'path', ellipsis: { tooltip: true } },
  {
    title: '权限名称',
    key: 'summary',
    ellipsis: { tooltip: true },
    render: (row) => {
      return `${row.summary || '未命名权限'} (${row.method} ${row.path})`
    },
  },
  { title: '标签', key: 'tags', width: 100 },
]

const menuPermissionColumns = [
  { title: '菜单名称', key: 'name', width: 150 },
  { title: '路径', key: 'path', width: 200 },
  { title: '组件', key: 'component', ellipsis: { tooltip: true } },
  { title: '图标', key: 'icon', width: 100 },
]

// 菜单树数据
const menuTreeData = computed(() => {
  const buildTree = (menus, parentId = 0) => {
    return menus
      .filter((menu) => menu.parent_id === parentId)
      .map((menu) => ({
        ...menu,
        key: menu.id,
        label: menu.name,
        children: buildTree(menus, menu.id),
      }))
  }
  return buildTree(allMenus.value)
})

// 选中的菜单键
const selectedMenuKeys = computed({
  get: () => (editingRole.value.menus || []).map((menu) => menu.id),
  set: (keys) => {
    const selectedMenus = allMenus.value.filter((menu) => keys.includes(menu.id))
    editingRole.value.menus = selectedMenus
  },
})

// 选中的菜单
const selectedMenus = computed(() => editingRole.value.menus || [])

// 方法
const loadRoleData = async () => {
  loading.value = true
  try {
    // 调用真实的API获取角色列表
    const response = await systemApis.roles.list({
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
    })

    if (response.success) {
      roleData.value = response.data || []
      pagination.value.itemCount = response.total || 0
    } else {
      throw new Error(response.message || '获取角色列表失败')
    }
  } catch (error) {
    console.error('加载角色数据失败:', error)
    message.error('加载角色数据失败: ' + (error.message || '网络错误'))
  } finally {
    loading.value = false
  }
}

const loadPermissions = async () => {
  try {
    // 调用真实的API获取可用权限
    const response = await systemApis.roles.getAvailablePermissions()

    if (response.success) {
      const { v1_apis, v2_sys_apis, menus } = response.data

      // 获取API分组信息
      let apiGroups = []
      try {
        const groupsResponse = await systemApi.apiGroupApi.list()
        if (groupsResponse.success) {
          apiGroups = groupsResponse.data
        }
      } catch (error) {
        console.warn('获取API分组失败:', error)
      }

      // 处理V1 API权限
      const v1Permissions = v1_apis.map((api) => ({
        id: api.id,
        method: api.method,
        path: api.path,
        summary: api.summary || api.path,
        tags: api.tags || '未分组',
        type: 'v1',
      }))

      // 处理V2 SysApiEndpoint权限
      const v2Permissions = v2_sys_apis.map((api) => {
        // 查找对应的分组名称
        const group = apiGroups.find((g) => g.id === api.group_id)
        const groupName = group ? group.name : '未分组'

        return {
          id: api.id,
          method: api.method,
          path: api.path,
          summary: api.summary || api.path,
          tags: groupName,
          type: 'v2',
          group_id: api.group_id,
        }
      })

      // 合并所有权限
      allPermissions.value = [...v1Permissions, ...v2Permissions]

      // 处理菜单权限
      allMenus.value = menus || []
    } else {
      message.error('获取权限数据失败: ' + response.message)
    }
  } catch (error) {
    console.error('加载权限数据失败:', error)
    message.error('加载权限数据失败: ' + (error.message || '网络错误'))
  }
}

const loadMenus = async () => {
  try {
    // 模拟加载菜单数据
    allMenus.value = [
      {
        id: 1,
        name: '系统管理',
        path: '/system',
        component: 'Layout',
        icon: 'system',
        parent_id: 0,
      },
      {
        id: 2,
        name: '用户管理',
        path: '/system/user',
        component: '/system/user',
        icon: 'user',
        parent_id: 1,
      },
      {
        id: 3,
        name: '角色管理',
        path: '/system/role',
        component: '/system/role',
        icon: 'role',
        parent_id: 1,
      },
    ]
  } catch (error) {
    message.error('加载菜单数据失败')
  }
}

const refreshData = async () => {
  await Promise.all([loadRoleData(), loadPermissions(), loadMenus()])
}

const handleCreate = () => {
  editingRole.value = {
    role_name: '',
    remark: '',
    apis: [],
    menus: [],
  }
  showEditModal.value = true
}

const handleEdit = async (role) => {
  try {
    // 先显示模态框
    showEditModal.value = true

    // 复制基本角色信息
    editingRole.value = {
      ...role,
      apis: [], // 先设置空数组
      menus: [],
    }

    // 获取角色的详细权限信息
    const response = await systemApis.roles.getPermissions(role.id)

    if (response.success) {
      // V2接口返回格式：{ api_permissions: [...], menu_permissions: [...] }
      const { api_permissions, menu_permissions } = response.data

      // 处理API权限 - V2接口返回的都是SysApiEndpoint类型
      const allPermissions = (api_permissions || []).map((api) => ({
        id: api.id,
        method: api.http_method || api.method, // 兼容不同字段名
        path: api.api_path || api.path, // 兼容不同字段名
        summary: api.api_name || api.summary || api.api_path || api.path,
        tags: api.group_id ? '已分组' : '未分组',
        type: 'v2', // V2接口返回的都是SysApiEndpoint，标记为v2类型
        group_id: api.group_id,
      }))

      // 使用nextTick确保组件已渲染后再设置权限
      await nextTick()

      console.log('V2接口返回的权限数据:', api_permissions)
      console.log('处理后的权限数据:', allPermissions)
      editingRole.value.apis = allPermissions
      console.log('editingRole.value.apis设置完成:', editingRole.value.apis)

      // 设置菜单权限
      selectedMenuKeys.value = (menu_permissions || []).map((menu) => menu.id)
      editingRole.value.menus = menu_permissions || []
    } else {
      console.warn('获取角色权限失败:', response.message)
      editingRole.value.apis = []
      editingRole.value.menus = []
      selectedMenuKeys.value = []
    }
  } catch (error) {
    console.error('加载角色权限失败:', error)
    message.error('加载角色权限失败: ' + (error.message || '网络错误'))
    editingRole.value.apis = []
    editingRole.value.menus = []
    selectedMenuKeys.value = []
  }
}

const handleDelete = (role) => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除角色"${role.role_name}"吗？此操作不可恢复。`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        // 调用真实的删除API
        const response = await systemApis.roles.delete(role.id)
        if (response.success) {
          message.success('删除成功')
          await loadRoleData()
        } else {
          throw new Error(response.message || '删除失败')
        }
      } catch (error) {
        console.error('删除失败:', error)
        message.error('删除失败: ' + (error.message || '网络错误'))
      }
    },
  })
}

const handleViewPermissions = (role) => {
  viewingRole.value = role
  showPermissionModal.value = true
}

const handleSave = async () => {
  try {
    console.log('开始表单验证，editingRole:', editingRole.value)
    await formRef.value?.validate()
    console.log('表单验证通过')
    saving.value = true

    // 准备权限数据
    const selectedApis = editingRole.value.apis || []

    // 分离V1和V2权限
    const v1ApiIds = selectedApis.filter((api) => api.type === 'v1').map((api) => api.id)

    const v2SysApiIds = selectedApis.filter((api) => api.type === 'v2').map((api) => api.id)

    const permissionData = {
      api_ids: v1ApiIds, // V1 API权限
      sys_api_ids: v2SysApiIds, // V2 SysApiEndpoint权限
      menu_ids: selectedMenuKeys.value || [],
    }

    if (editingRole.value.id) {
      // 更新角色权限
      const response = await systemApis.roles.assignPermissions(
        editingRole.value.id,
        permissionData
      )
      if (response.success) {
        message.success('权限更新成功')
      } else {
        throw new Error(response.message || '权限更新失败')
      }
    } else {
      // 创建新角色 - 修复字段名映射，移除已弃用的v1 API权限
      console.log('创建角色时的editingRole.value:', editingRole.value)
      console.log('editingRole.value.role_name:', editingRole.value.role_name)

      const roleData = {
        role_name: editingRole.value.role_name, // 前端role_name字段映射到后端role_name
        remark: editingRole.value.remark, // 前端remark字段映射到后端remark
        role_key:
          editingRole.value.role_key ||
          editingRole.value.role_name?.toLowerCase().replace(/\s+/g, '_'),
        role_sort: editingRole.value.role_sort || 1,
        status: editingRole.value.status || '0',
        data_scope: editingRole.value.data_scope || '1',
        menu_check_strictly: editingRole.value.menu_check_strictly !== false,
        dept_check_strictly: editingRole.value.dept_check_strictly !== false,
        parent_id: editingRole.value.parent_id || null,
        sys_api_ids: v2SysApiIds, // 只使用v2版本的API权限
        menu_ids: selectedMenuKeys.value,
      }

      console.log('发送到后端的roleData:', roleData)

      const response = await systemApis.roles.create(roleData)
      if (response.success) {
        message.success('角色创建成功')
      } else {
        throw new Error(response.message || '角色创建失败')
      }
    }

    showEditModal.value = false
    await loadRoleData()
  } catch (error) {
    if (error.length) {
      message.error('请检查表单输入')
    } else {
      console.error('保存失败:', error)
      message.error('保存失败: ' + (error.message || '网络错误'))
    }
  } finally {
    saving.value = false
  }
}

const handleApiPermissionsChange = (permissions) => {
  editingRole.value.apis = permissions
}

const handleMenuPermissionsChange = (keys) => {
  selectedMenuKeys.value = keys
}

const getMethodTagType = (method) => {
  const typeMap = {
    GET: 'info',
    POST: 'success',
    PUT: 'warning',
    DELETE: 'error',
  }
  return typeMap[method] || 'default'
}

const getMenuIcon = (menu) => {
  // 根据菜单类型返回不同图标
  if (menu.children && menu.children.length > 0) {
    return FolderIcon
  }
  return DocumentIcon
}

// 生命周期
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.role-management {
  padding: 16px;
}

.role-edit-modal :deep(.n-card__content) {
  padding: 24px;
}

.permission-section {
  padding: 16px 0;
}

.menu-node {
  display: flex;
  align-items: center;
  gap: 8px;
}

.menu-icon {
  flex-shrink: 0;
}

.menu-label {
  font-weight: 500;
}

.permission-preview {
  padding: 16px 0;
}

.permission-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  border-bottom: 1px solid #f0f0f0;
}

.permission-path,
.menu-path {
  color: var(--text-color-secondary);
  font-family: monospace;
  font-size: var(--font-size-xs);
}

.permission-summary,
.menu-name {
  color: var(--text-color-primary);
  font-size: var(--font-size-sm);
}

.mb-4 {
  margin-bottom: 16px;
}
</style>
