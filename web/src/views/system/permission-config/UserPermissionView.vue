<template>
  <div class="user-permission-view">
    <CommonPage show-footer title="用户权限查看" class="permission-view-page">
      <template #action>
        <div class="flex items-center gap-3">
          <NButton @click="handleRefresh">
            <TheIcon icon="material-symbols:refresh" :size="18" class="mr-1" />
            刷新
          </NButton>
          <NButton @click="handleExportUserPermissions">
            <TheIcon icon="material-symbols:download" :size="18" class="mr-1" />
            导出权限
          </NButton>
        </div>
      </template>

      <div class="view-layout">
        <!-- 左侧用户列表 -->
        <div class="user-list-panel">
          <NCard title="用户列表" class="user-list-card">
            <div class="user-search">
              <NInput
                v-model:value="userSearchText"
                placeholder="搜索用户..."
                clearable
                @input="handleUserSearch"
              >
                <template #prefix>
                  <TheIcon icon="material-symbols:search" />
                </template>
              </NInput>
            </div>

            <div class="user-filters">
              <NSelect
                v-model:value="departmentFilter"
                placeholder="筛选部门"
                clearable
                :options="departmentOptions"
                @update:value="handleDepartmentFilter"
              />
              <NSelect
                v-model:value="roleFilter"
                placeholder="筛选角色"
                clearable
                :options="roleOptions"
                @update:value="handleRoleFilter"
              />
            </div>

            <div class="user-list">
              <div
                v-for="user in filteredUsers"
                :key="user.id"
                class="user-item"
                :class="{ active: selectedUser?.id === user.id }"
                @click="handleSelectUser(user)"
              >
                <div class="user-avatar">
                  <NAvatar :size="32" :src="user.avatar">
                    {{ user.username?.charAt(0)?.toUpperCase() }}
                  </NAvatar>
                </div>
                <div class="user-info">
                  <div class="user-name">{{ user.username }}</div>
                  <div class="user-dept">{{ user.department_name || '未分配部门' }}</div>
                  <div class="user-roles">
                    <NTag
                      v-for="role in user.roles"
                      :key="role.id"
                      size="small"
                      class="role-tag"
                    >
                      {{ role.name }}
                    </NTag>
                  </div>
                </div>
                <div class="user-status">
                  <NTag :type="user.is_active ? 'success' : 'default'" size="small">
                    {{ user.is_active ? '启用' : '禁用' }}
                  </NTag>
                </div>
              </div>
            </div>
          </NCard>
        </div>

        <!-- 右侧权限详情 -->
        <div class="permission-detail-panel">
          <div v-if="!selectedUser" class="empty-state">
            <TheIcon icon="material-symbols:person-search" :size="64" class="empty-icon" />
            <p class="empty-text">请选择一个用户来查看权限详情</p>
          </div>

          <div v-else class="permission-details">
            <!-- 用户基本信息 -->
            <NCard class="user-basic-info">
              <div class="user-header">
                <NAvatar :size="48" :src="selectedUser.avatar">
                  {{ selectedUser.username?.charAt(0)?.toUpperCase() }}
                </NAvatar>
                <div class="user-meta">
                  <h3 class="user-title">{{ selectedUser.username }}</h3>
                  <p class="user-subtitle">{{ selectedUser.email || '未设置邮箱' }}</p>
                  <div class="user-tags">
                    <NTag type="info" size="small">{{ selectedUser.department_name || '未分配部门' }}</NTag>
                    <NTag
                      v-for="role in selectedUser.roles"
                      :key="role.id"
                      type="primary"
                      size="small"
                    >
                      {{ role.name }}
                    </NTag>
                  </div>
                </div>
              </div>
            </NCard>

            <!-- 权限详情标签页 -->
            <NTabs v-model:value="activeTab" type="line" animated class="permission-tabs">
              <!-- 权限概览 -->
              <NTabPane name="overview" tab="权限概览">
                <div class="permission-overview">
                  <NGrid :cols="3" :x-gap="16" :y-gap="16">
                    <NGi>
                      <NStatistic label="菜单权限" :value="userPermissions.menu_count">
                        <template #suffix>个</template>
                      </NStatistic>
                    </NGi>
                    <NGi>
                      <NStatistic label="API权限" :value="userPermissions.api_count">
                        <template #suffix>个</template>
                      </NStatistic>
                    </NGi>
                    <NGi>
                      <NStatistic label="数据权限" :value="getDataScopeLabel(userPermissions.data_scope)">
                      </NStatistic>
                    </NGi>
                  </NGrid>

                  <div class="permission-summary">
                    <NCard title="权限来源分析" size="small">
                      <div class="permission-source">
                        <div
                          v-for="role in selectedUser.roles"
                          :key="role.id"
                          class="role-permissions"
                        >
                          <div class="role-header">
                            <NTag type="primary">{{ role.name }}</NTag>
                            <span class="role-desc">{{ role.description }}</span>
                          </div>
                          <div class="role-stats">
                            <span class="stat-item">菜单: {{ role.menu_count || 0 }}</span>
                            <span class="stat-item">API: {{ role.api_count || 0 }}</span>
                          </div>
                        </div>
                      </div>
                    </NCard>
                  </div>
                </div>
              </NTabPane>

              <!-- 菜单权限 -->
              <NTabPane name="menu" tab="菜单权限">
                <div class="menu-permissions">
                  <div class="section-header">
                    <h4>可访问菜单</h4>
                    <div class="section-actions">
                      <NButton size="small" @click="handleExpandAllMenus">
                        展开全部
                      </NButton>
                      <NButton size="small" @click="handleCollapseAllMenus">
                        收起全部
                      </NButton>
                    </div>
                  </div>
                  
                  <NTree
                    ref="menuTreeRef"
                    :data="userMenuTree"
                    :render-label="renderMenuLabel"
                    :render-prefix="renderMenuIcon"
                    block-line
                    expand-on-click
                    :default-expanded-keys="defaultExpandedKeys"
                  />
                </div>
              </NTabPane>

              <!-- API权限 -->
              <NTabPane name="api" tab="API权限">
                <div class="api-permissions">
                  <div class="section-header">
                    <h4>可访问API</h4>
                    <div class="section-actions">
                      <NInput
                        v-model:value="apiSearchText"
                        placeholder="搜索API..."
                        clearable
                        class="api-search"
                      >
                        <template #prefix>
                          <TheIcon icon="material-symbols:search" />
                        </template>
                      </NInput>
                      <NSelect
                        v-model:value="apiGroupFilter"
                        placeholder="筛选分组"
                        clearable
                        :options="apiGroupOptions"
                        class="api-group-filter"
                      />
                    </div>
                  </div>

                  <div class="api-list">
                    <div
                      v-for="group in filteredApiGroups"
                      :key="group.name"
                      class="api-group"
                    >
                      <div class="group-header">
                        <h5>{{ group.label }}</h5>
                        <NTag size="small">{{ group.apis.length }} 个API</NTag>
                      </div>
                      <div class="group-apis">
                        <div
                          v-for="api in group.apis"
                          :key="api.id"
                          class="api-item"
                        >
                          <NTag :type="getMethodTagType(api.method)" size="small">
                            {{ api.method }}
                          </NTag>
                          <span class="api-path">{{ api.path }}</span>
                          <span class="api-desc">{{ api.summary || '无描述' }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </NTabPane>

              <!-- 数据权限 -->
              <NTabPane name="data" tab="数据权限">
                <div class="data-permissions">
                  <NCard title="数据访问范围" size="small">
                    <div class="data-scope-info">
                      <div class="scope-item">
                        <span class="label">数据范围:</span>
                        <NTag type="info">{{ getDataScopeLabel(userPermissions.data_scope) }}</NTag>
                      </div>
                      
                      <div v-if="userPermissions.departments?.length" class="scope-item">
                        <span class="label">授权部门:</span>
                        <div class="dept-list">
                          <NTag
                            v-for="dept in userPermissions.departments"
                            :key="dept.id"
                            size="small"
                            class="dept-tag"
                          >
                            {{ dept.name }}
                          </NTag>
                        </div>
                      </div>

                      <div v-if="userPermissions.fields?.length" class="scope-item">
                        <span class="label">字段权限:</span>
                        <div class="field-list">
                          <NTag
                            v-for="field in userPermissions.fields"
                            :key="field.key"
                            size="small"
                            class="field-tag"
                          >
                            {{ field.label }}
                          </NTag>
                        </div>
                      </div>
                    </div>
                  </NCard>

                  <NCard title="权限继承关系" size="small" class="mt-4">
                    <div class="permission-inheritance">
                      <div
                        v-for="role in selectedUser.roles"
                        :key="role.id"
                        class="inheritance-item"
                      >
                        <div class="inheritance-header">
                          <NTag type="primary">{{ role.name }}</NTag>
                          <span class="inheritance-desc">来自角色权限</span>
                        </div>
                        <div class="inheritance-details">
                          <div class="detail-item">
                            <span class="detail-label">数据范围:</span>
                            <span class="detail-value">{{ getDataScopeLabel(role.data_scope) }}</span>
                          </div>
                          <div v-if="role.departments?.length" class="detail-item">
                            <span class="detail-label">部门权限:</span>
                            <span class="detail-value">{{ role.departments.length }} 个部门</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </NCard>
                </div>
              </NTabPane>

              <!-- 权限历史 -->
              <NTabPane name="history" tab="权限历史">
                <div class="permission-history">
                  <div class="section-header">
                    <h4>权限变更历史</h4>
                    <div class="section-actions">
                      <NDatePicker
                        v-model:value="historyDateRange"
                        type="daterange"
                        clearable
                        @update:value="handleHistoryDateChange"
                      />
                    </div>
                  </div>

                  <NTimeline>
                    <NTimelineItem
                      v-for="record in permissionHistory"
                      :key="record.id"
                      :type="getHistoryItemType(record.action)"
                    >
                      <template #header>
                        <div class="history-header">
                          <span class="history-action">{{ getHistoryActionLabel(record.action) }}</span>
                          <span class="history-time">{{ formatDate(record.created_at) }}</span>
                        </div>
                      </template>
                      
                      <div class="history-content">
                        <p class="history-desc">{{ record.description }}</p>
                        <div class="history-details">
                          <span class="history-operator">操作人: {{ record.operator_name }}</span>
                          <span class="history-ip">IP: {{ record.ip_address }}</span>
                        </div>
                      </div>
                    </NTimelineItem>
                  </NTimeline>
                </div>
              </NTabPane>
            </NTabs>
          </div>
        </div>
      </div>
    </CommonPage>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import {
  NButton,
  NCard,
  NInput,
  NSelect,
  NTabs,
  NTabPane,
  NTag,
  NAvatar,
  NGrid,
  NGi,
  NStatistic,
  NTree,
  NDatePicker,
  NTimeline,
  NTimelineItem,
  useMessage,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import systemV2Api from '@/api/system-v2'
import { formatDate } from '@/utils'

defineOptions({ name: 'UserPermissionView' })

const $message = useMessage()

// 数据状态
const users = ref([])
const selectedUser = ref(null)
const userPermissions = ref({})
const userMenuTree = ref([])
const permissionHistory = ref([])
const activeTab = ref('overview')

// 搜索和筛选
const userSearchText = ref('')
const departmentFilter = ref(null)
const roleFilter = ref(null)
const apiSearchText = ref('')
const apiGroupFilter = ref(null)
const historyDateRange = ref(null)

// 树组件引用
const menuTreeRef = ref(null)

// 选项数据
const departmentOptions = ref([])
const roleOptions = ref([])
const apiGroupOptions = ref([
  { label: '用户管理', value: 'user' },
  { label: '角色管理', value: 'role' },
  { label: '菜单管理', value: 'menu' },
  { label: '系统管理', value: 'system' },
])

// 计算属性
const filteredUsers = computed(() => {
  let filtered = users.value

  // 文本搜索
  if (userSearchText.value) {
    const searchText = userSearchText.value.toLowerCase()
    filtered = filtered.filter(user => 
      user.username.toLowerCase().includes(searchText) ||
      user.email?.toLowerCase().includes(searchText) ||
      user.department_name?.toLowerCase().includes(searchText)
    )
  }

  // 部门筛选
  if (departmentFilter.value) {
    filtered = filtered.filter(user => user.department_id === departmentFilter.value)
  }

  // 角色筛选
  if (roleFilter.value) {
    filtered = filtered.filter(user => 
      user.roles?.some(role => role.id === roleFilter.value)
    )
  }

  return filtered
})

const filteredApiGroups = computed(() => {
  if (!userPermissions.value.api_groups) return []

  let groups = [...userPermissions.value.api_groups]

  // 分组筛选
  if (apiGroupFilter.value) {
    groups = groups.filter(group => group.name === apiGroupFilter.value)
  }

  // API搜索
  if (apiSearchText.value) {
    const searchText = apiSearchText.value.toLowerCase()
    groups = groups.map(group => ({
      ...group,
      apis: group.apis.filter(api => 
        api.path.toLowerCase().includes(searchText) ||
        api.summary?.toLowerCase().includes(searchText)
      )
    })).filter(group => group.apis.length > 0)
  }

  return groups
})

const defaultExpandedKeys = computed(() => {
  return userMenuTree.value.map(item => item.key)
})

// 生命周期
onMounted(() => {
  loadUsers()
  loadDepartments()
  loadRoles()
})

// 方法
async function loadUsers() {
  try {
    const response = await systemV2Api.getUsers()
    users.value = response.data || []
  } catch (error) {
    $message.error('加载用户列表失败')
    console.error('Load users error:', error)
  }
}

async function loadDepartments() {
  try {
    const response = await systemV2Api.getDepartments()
    departmentOptions.value = (response.data || []).map(dept => ({
      label: dept.name,
      value: dept.id
    }))
  } catch (error) {
    console.error('Load departments error:', error)
  }
}

async function loadRoles() {
  try {
    const response = await systemV2Api.getRoles()
    roleOptions.value = (response.data || []).map(role => ({
      label: role.name,
      value: role.id
    }))
  } catch (error) {
    console.error('Load roles error:', error)
  }
}

async function loadUserPermissions(userId) {
  try {
    const [permissionsRes, menuTreeRes, historyRes] = await Promise.all([
      systemV2Api.getUserPermissions(userId),
      systemV2Api.getUserMenuTree(userId),
      systemV2Api.getUserPermissionHistory(userId)
    ])

    userPermissions.value = permissionsRes.data || {}
    userMenuTree.value = menuTreeRes.data || []
    permissionHistory.value = historyRes.data || []
  } catch (error) {
    $message.error('加载用户权限失败')
    console.error('Load user permissions error:', error)
  }
}

function handleSelectUser(user) {
  selectedUser.value = user
  activeTab.value = 'overview'
  loadUserPermissions(user.id)
}

function handleUserSearch() {
  // 搜索逻辑已在计算属性中处理
}

function handleDepartmentFilter() {
  // 筛选逻辑已在计算属性中处理
}

function handleRoleFilter() {
  // 筛选逻辑已在计算属性中处理
}

function handleRefresh() {
  loadUsers()
  if (selectedUser.value) {
    loadUserPermissions(selectedUser.value.id)
  }
}

async function handleExportUserPermissions() {
  if (!selectedUser.value) {
    $message.warning('请先选择一个用户')
    return
  }

  try {
    const response = await systemV2Api.exportUserPermissions(selectedUser.value.id)
    const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `user-permissions-${selectedUser.value.username}-${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
    $message.success('用户权限导出成功')
  } catch (error) {
    $message.error('导出用户权限失败')
    console.error('Export error:', error)
  }
}

function handleExpandAllMenus() {
  menuTreeRef.value?.expandAll()
}

function handleCollapseAllMenus() {
  menuTreeRef.value?.collapseAll()
}

function handleHistoryDateChange() {
  if (selectedUser.value) {
    loadUserPermissions(selectedUser.value.id)
  }
}

// 渲染方法
function renderMenuLabel({ option }) {
  return h('span', { class: 'menu-label' }, [
    h('span', { class: 'menu-title' }, option.title),
    option.path && h('span', { class: 'menu-path' }, ` (${option.path})`)
  ])
}

function renderMenuIcon({ option }) {
  return h(TheIcon, { icon: option.icon || 'material-symbols:folder', size: 16 })
}

// 工具方法
function getMethodTagType(method) {
  const typeMap = {
    GET: 'info',
    POST: 'success',
    PUT: 'warning',
    DELETE: 'error',
    PATCH: 'default'
  }
  return typeMap[method] || 'default'
}

function getDataScopeLabel(scope) {
  const labelMap = {
    all: '全部数据',
    dept: '本部门数据',
    dept_and_sub: '本部门及下级部门数据',
    self: '仅本人数据',
    custom: '自定义数据权限'
  }
  return labelMap[scope] || '未设置'
}

function getHistoryItemType(action) {
  const typeMap = {
    grant: 'success',
    revoke: 'error',
    modify: 'warning',
    login: 'info'
  }
  return typeMap[action] || 'default'
}

function getHistoryActionLabel(action) {
  const labelMap = {
    grant: '授予权限',
    revoke: '撤销权限',
    modify: '修改权限',
    login: '登录系统'
  }
  return labelMap[action] || action
}
</script>

<style scoped>
.user-permission-view {
  height: 100%;
}

.view-layout {
  display: flex;
  gap: 16px;
  height: calc(100vh - 200px);
}

.user-list-panel {
  width: 320px;
  flex-shrink: 0;
}

.user-list-card {
  height: 100%;
}

.user-search {
  margin-bottom: 12px;
}

.user-filters {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.user-list {
  max-height: calc(100% - 180px);
  overflow-y: auto;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.user-item:hover {
  border-color: var(--primary-color);
  background-color: var(--hover-color);
}

.user-item.active {
  border-color: var(--primary-color);
  background-color: var(--primary-color-hover);
}

.user-info {
  flex: 1;
}

.user-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.user-dept {
  font-size: 12px;
  color: var(--text-color-secondary);
  margin-bottom: 6px;
}

.user-roles {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.role-tag {
  font-size: 10px;
}

.permission-detail-panel {
  flex: 1;
  overflow: hidden;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-color-secondary);
}

.empty-icon {
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
}

.permission-details {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.user-basic-info {
  flex-shrink: 0;
}

.user-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-meta {
  flex: 1;
}

.user-title {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 500;
}

.user-subtitle {
  margin: 0 0 8px 0;
  color: var(--text-color-secondary);
  font-size: 14px;
}

.user-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.permission-tabs {
  flex: 1;
  overflow: hidden;
}

.permission-overview {
  padding: 16px 0;
}

.permission-summary {
  margin-top: 24px;
}

.permission-source {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.role-permissions {
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
}

.role-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.role-desc {
  color: var(--text-color-secondary);
  font-size: 12px;
}

.role-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  font-size: 12px;
  color: var(--text-color-secondary);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.api-search {
  width: 200px;
}

.api-group-filter {
  width: 120px;
}

.api-list {
  max-height: 400px;
  overflow-y: auto;
}

.api-group {
  margin-bottom: 24px;
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
}

.group-header h5 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
}

.group-apis {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.api-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background-color: var(--card-color);
  border-radius: 4px;
  font-size: 12px;
}

.api-path {
  font-family: monospace;
  font-weight: 500;
}

.api-desc {
  color: var(--text-color-secondary);
  margin-left: auto;
}

.data-scope-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.scope-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.scope-item .label {
  font-weight: 500;
  min-width: 80px;
  margin-top: 2px;
}

.dept-list,
.field-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.permission-inheritance {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.inheritance-item {
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
}

.inheritance-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.inheritance-desc {
  color: var(--text-color-secondary);
  font-size: 12px;
}

.inheritance-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.detail-label {
  font-weight: 500;
  min-width: 60px;
}

.detail-value {
  color: var(--text-color-secondary);
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.history-action {
  font-weight: 500;
}

.history-time {
  font-size: 12px;
  color: var(--text-color-secondary);
}

.history-content {
  margin-top: 8px;
}

.history-desc {
  margin: 0 0 8px 0;
  font-size: 14px;
}

.history-details {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-color-secondary);
}

.menu-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.menu-title {
  font-weight: 500;
}

.menu-path {
  font-size: 12px;
  color: var(--text-color-secondary);
  font-family: monospace;
}

.mr-1 {
  margin-right: 4px;
}

.mt-4 {
  margin-top: 16px;
}

.flex {
  display: flex;
}

.items-center {
  align-items: center;
}

.gap-3 {
  gap: 12px;
}
</style>