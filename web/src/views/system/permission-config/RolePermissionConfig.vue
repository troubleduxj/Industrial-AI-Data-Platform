<template>
  <div class="role-permission-config">
    <CommonPage show-footer title="角色权限配置" class="permission-config-page">
      <template #action>
        <div class="flex items-center gap-3">
          <NButton type="primary" :loading="saving" @click="handleSaveAll">
            <TheIcon icon="material-symbols:save" :size="18" class="mr-1" />
            保存配置
          </NButton>
          <NButton @click="handleRefresh">
            <TheIcon icon="material-symbols:refresh" :size="18" class="mr-1" />
            刷新
          </NButton>
          <NButton @click="handleExport">
            <TheIcon icon="material-symbols:download" :size="18" class="mr-1" />
            导出配置
          </NButton>
          <NButton @click="handleImport">
            <TheIcon icon="material-symbols:upload" :size="18" class="mr-1" />
            导入配置
          </NButton>
        </div>
      </template>

      <div class="config-layout">
        <!-- 左侧角色列表 -->
        <div class="role-list-panel">
          <NCard title="角色列表" class="role-list-card">
            <template #header-extra>
              <NButton size="small" @click="handleAddRole">
                <TheIcon icon="material-symbols:add" :size="16" />
                新增角色
              </NButton>
            </template>

            <div class="role-search">
              <NInput
                v-model:value="roleSearchText"
                placeholder="搜索角色..."
                clearable
                @input="handleRoleSearch"
              >
                <template #prefix>
                  <TheIcon icon="material-symbols:search" />
                </template>
              </NInput>
            </div>

            <div class="role-list">
              <div
                v-for="role in filteredRoles"
                :key="role.id"
                class="role-item"
                :class="{ active: selectedRole?.id === role.id }"
                @click="handleSelectRole(role)"
              >
                <div class="role-info">
                  <div class="role-name">{{ role.name }}</div>
                  <div class="role-desc">{{ role.description || '暂无描述' }}</div>
                  <div class="role-meta">
                    <NTag size="small" :type="role.is_active ? 'success' : 'default'">
                      {{ role.is_active ? '启用' : '禁用' }}
                    </NTag>
                    <span class="user-count">{{ role.user_count || 0 }} 用户</span>
                  </div>
                </div>
                <div class="role-actions">
                  <NButton size="tiny" @click.stop="handleEditRole(role)">
                    <TheIcon icon="material-symbols:edit" :size="14" />
                  </NButton>
                  <NPopconfirm @positive-click="handleDeleteRole(role)">
                    <template #trigger>
                      <NButton size="tiny" type="error" @click.stop>
                        <TheIcon icon="material-symbols:delete" :size="14" />
                      </NButton>
                    </template>
                    确定删除角色 "{{ role.name }}" 吗？
                  </NPopconfirm>
                </div>
              </div>
            </div>
          </NCard>
        </div>

        <!-- 右侧权限配置 -->
        <div class="permission-config-panel">
          <div v-if="!selectedRole" class="empty-state">
            <TheIcon icon="material-symbols:person-check" :size="64" class="empty-icon" />
            <p class="empty-text">请选择一个角色来配置权限</p>
          </div>

          <div v-else class="permission-tabs">
            <NTabs v-model:value="activeTab" type="line" animated>
              <!-- 菜单权限 -->
              <NTabPane name="menu" tab="菜单权限">
                <div class="permission-section">
                  <div class="section-header">
                    <h3>菜单权限配置</h3>
                    <div class="section-actions">
                      <NButton size="small" @click="handleExpandAllMenus">
                        <TheIcon icon="material-symbols:expand-all" :size="16" class="mr-1" />
                        展开全部
                      </NButton>
                      <NButton size="small" @click="handleCollapseAllMenus">
                        <TheIcon icon="material-symbols:collapse-all" :size="16" class="mr-1" />
                        收起全部
                      </NButton>
                      <NButton size="small" @click="handleSelectAllMenus">
                        <TheIcon icon="material-symbols:select-all" :size="16" class="mr-1" />
                        全选
                      </NButton>
                      <NButton size="small" @click="handleDeselectAllMenus">
                        <TheIcon icon="material-symbols:deselect" :size="16" class="mr-1" />
                        取消全选
                      </NButton>
                    </div>
                  </div>

                  <MenuPermissionTree
                    ref="menuTreeRef"
                    v-model:checked-keys="selectedRole.menu_permissions"
                    :loading="menuLoading"
                    @update:checked-keys="handleMenuPermissionChange"
                  />
                </div>
              </NTabPane>

              <!-- API权限 -->
              <NTabPane name="api" tab="API权限">
                <div class="permission-section">
                  <div class="section-header">
                    <h3>API权限配置</h3>
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

                  <ApiPermissionTree
                    ref="apiTreeRef"
                    v-model:checked-keys="selectedRole.api_permissions"
                    :search-text="apiSearchText"
                    :group-filter="apiGroupFilter"
                    :loading="apiLoading"
                    @update:checked-keys="handleApiPermissionChange"
                  />
                </div>
              </NTabPane>

              <!-- 数据权限 -->
              <NTabPane name="data" tab="数据权限">
                <div class="permission-section">
                  <div class="section-header">
                    <h3>数据权限配置</h3>
                    <p class="section-desc">配置角色可以访问的数据范围</p>
                  </div>

                  <div class="data-permission-config">
                    <NForm
                      :model="selectedRole.data_permissions"
                      label-placement="left"
                      label-width="120px"
                    >
                      <NFormItem label="数据范围">
                        <NRadioGroup v-model:value="selectedRole.data_permissions.scope">
                          <NSpace vertical>
                            <NRadio value="all">全部数据</NRadio>
                            <NRadio value="dept">本部门数据</NRadio>
                            <NRadio value="dept_and_sub">本部门及下级部门数据</NRadio>
                            <NRadio value="self">仅本人数据</NRadio>
                            <NRadio value="custom">自定义数据权限</NRadio>
                          </NSpace>
                        </NRadioGroup>
                      </NFormItem>

                      <NFormItem
                        v-if="selectedRole.data_permissions.scope === 'custom'"
                        label="部门权限"
                      >
                        <DepartmentTree
                          v-model:checked-keys="selectedRole.data_permissions.departments"
                          multiple
                          checkable
                        />
                      </NFormItem>

                      <NFormItem label="字段权限">
                        <div class="field-permissions">
                          <div
                            v-for="field in dataFields"
                            :key="field.key"
                            class="field-permission-item"
                          >
                            <NCheckbox
                              :checked="selectedRole.data_permissions.fields?.includes(field.key)"
                              @update:checked="handleFieldPermissionChange(field.key, $event)"
                            >
                              {{ field.label }}
                            </NCheckbox>
                            <span class="field-desc">{{ field.description }}</span>
                          </div>
                        </div>
                      </NFormItem>
                    </NForm>
                  </div>
                </div>
              </NTabPane>

              <!-- 权限预览 -->
              <NTabPane name="preview" tab="权限预览">
                <div class="permission-section">
                  <div class="section-header">
                    <h3>权限预览</h3>
                    <p class="section-desc">查看角色的完整权限配置</p>
                  </div>

                  <div class="permission-preview">
                    <NGrid :cols="2" :x-gap="16" :y-gap="16">
                      <NGi>
                        <NCard title="菜单权限" size="small">
                          <div class="permission-list">
                            <div
                              v-for="menu in selectedMenus"
                              :key="menu.id"
                              class="permission-item"
                            >
                              <TheIcon :icon="menu.icon" :size="16" />
                              <span>{{ menu.title }}</span>
                            </div>
                          </div>
                        </NCard>
                      </NGi>

                      <NGi>
                        <NCard title="API权限" size="small">
                          <div class="permission-list">
                            <div v-for="api in selectedApis" :key="api.id" class="permission-item">
                              <NTag size="small" :type="getMethodTagType(api.method)">
                                {{ api.method }}
                              </NTag>
                              <span>{{ api.path }}</span>
                            </div>
                          </div>
                        </NCard>
                      </NGi>
                    </NGrid>

                    <NCard title="数据权限" size="small" class="mt-4">
                      <div class="data-permission-summary">
                        <div class="summary-item">
                          <span class="label">数据范围:</span>
                          <span class="value">{{
                            getDataScopeLabel(selectedRole.data_permissions?.scope)
                          }}</span>
                        </div>
                        <div
                          v-if="selectedRole.data_permissions?.departments?.length"
                          class="summary-item"
                        >
                          <span class="label">授权部门:</span>
                          <span class="value"
                            >{{ selectedRole.data_permissions.departments.length }} 个部门</span
                          >
                        </div>
                        <div
                          v-if="selectedRole.data_permissions?.fields?.length"
                          class="summary-item"
                        >
                          <span class="label">字段权限:</span>
                          <span class="value"
                            >{{ selectedRole.data_permissions.fields.length }} 个字段</span
                          >
                        </div>
                      </div>
                    </NCard>
                  </div>
                </div>
              </NTabPane>
            </NTabs>
          </div>
        </div>
      </div>
    </CommonPage>

    <!-- 角色编辑模态框 -->
    <CrudModal
      v-model:visible="roleModalVisible"
      :title="roleModalTitle"
      :loading="roleModalLoading"
      @save="handleSaveRole"
    >
      <NForm
        ref="roleFormRef"
        :model="roleForm"
        :rules="roleFormRules"
        label-placement="left"
        label-width="80px"
      >
        <NFormItem label="角色名称" path="name">
          <NInput v-model:value="roleForm.name" placeholder="请输入角色名称" />
        </NFormItem>
        <NFormItem label="角色描述" path="description">
          <NInput
            v-model:value="roleForm.description"
            type="textarea"
            placeholder="请输入角色描述"
            :rows="3"
          />
        </NFormItem>
        <NFormItem label="状态" path="is_active">
          <NSwitch v-model:value="roleForm.is_active">
            <template #checked>启用</template>
            <template #unchecked>禁用</template>
          </NSwitch>
        </NFormItem>
      </NForm>
    </CrudModal>

    <!-- 导入配置模态框 -->
    <NModal v-model:show="importModalVisible" preset="dialog" title="导入权限配置">
      <div class="import-config">
        <NUpload
          :file-list="importFileList"
          :max="1"
          accept=".json"
          @change="handleImportFileChange"
        >
          <NUploadDragger>
            <div class="upload-content">
              <TheIcon icon="material-symbols:upload-file" :size="48" class="upload-icon" />
              <p class="upload-text">点击或拖拽文件到此区域上传</p>
              <p class="upload-hint">支持 JSON 格式的权限配置文件</p>
            </div>
          </NUploadDragger>
        </NUpload>

        <div v-if="importPreview" class="import-preview">
          <h4>配置预览</h4>
          <NCode :code="JSON.stringify(importPreview, null, 2)" language="json" />
        </div>
      </div>

      <template #action>
        <NSpace>
          <NButton @click="importModalVisible = false">取消</NButton>
          <NButton type="primary" :disabled="!importFileList.length" @click="handleConfirmImport">
            确认导入
          </NButton>
        </NSpace>
      </template>
    </NModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  NButton,
  NCard,
  NInput,
  NTabs,
  NTabPane,
  NTag,
  NPopconfirm,
  NForm,
  NFormItem,
  NRadioGroup,
  NRadio,
  NCheckbox,
  NSpace,
  NGrid,
  NGi,
  NSelect,
  NSwitch,
  NModal,
  NUpload,
  NUploadDragger,
  NCode,
  useMessage,
  useDialog,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import MenuPermissionTree from '@/components/system/MenuPermissionTree.vue'
import ApiPermissionTree from '@/components/system/ApiPermissionTree.vue'
import DepartmentTree from '@/components/system/DepartmentTree.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

import systemV2Api from '@/api/system-v2'

defineOptions({ name: 'RolePermissionConfig' })

const $message = useMessage()
const $dialog = useDialog()

// 数据状态
const roles = ref([])
const selectedRole = ref(null)
const activeTab = ref('menu')
const saving = ref(false)
const menuLoading = ref(false)
const apiLoading = ref(false)

// 搜索和筛选
const roleSearchText = ref('')
const apiSearchText = ref('')
const apiGroupFilter = ref(null)

// 角色模态框
const roleModalVisible = ref(false)
const roleModalTitle = ref('')
const roleModalLoading = ref(false)
const roleForm = ref({})
const roleFormRef = ref(null)

// 导入配置
const importModalVisible = ref(false)
const importFileList = ref([])
const importPreview = ref(null)

// 树组件引用
const menuTreeRef = ref(null)
const apiTreeRef = ref(null)

// 计算属性
const filteredRoles = computed(() => {
  if (!roleSearchText.value) return roles.value
  return roles.value.filter(
    (role) =>
      role.name.toLowerCase().includes(roleSearchText.value.toLowerCase()) ||
      (role.description &&
        role.description.toLowerCase().includes(roleSearchText.value.toLowerCase()))
  )
})

const selectedMenus = computed(() => {
  if (!selectedRole.value?.menu_permissions) return []
  // 这里应该根据选中的菜单ID获取菜单详情
  return []
})

const selectedApis = computed(() => {
  if (!selectedRole.value?.api_permissions) return []
  // 这里应该根据选中的API ID获取API详情
  return []
})

const apiGroupOptions = computed(() => {
  // 这里应该从API数据中提取分组选项
  return [
    { label: '用户管理', value: 'user' },
    { label: '角色管理', value: 'role' },
    { label: '菜单管理', value: 'menu' },
    { label: '系统管理', value: 'system' },
  ]
})

// 数据字段配置
const dataFields = ref([
  { key: 'user_info', label: '用户信息', description: '查看用户基本信息' },
  { key: 'user_contact', label: '联系方式', description: '查看用户联系方式' },
  { key: 'salary_info', label: '薪资信息', description: '查看薪资相关数据' },
  { key: 'performance', label: '绩效数据', description: '查看绩效评估数据' },
])

// 表单验证规则
const roleFormRules = {
  name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' },
    { min: 2, max: 50, message: '角色名称长度在 2 到 50 个字符', trigger: 'blur' },
  ],
  description: [{ max: 200, message: '描述不能超过 200 个字符', trigger: 'blur' }],
}

// 生命周期
onMounted(() => {
  loadRoles()
})

// 监听选中角色变化
watch(selectedRole, (newRole) => {
  if (newRole) {
    loadRolePermissions(newRole.id)
  }
})

// 方法
async function loadRoles() {
  try {
    const response = await systemV2Api.getRoles()
    roles.value = response.data || []
  } catch (error) {
    $message.error('加载角色列表失败')
    console.error('Load roles error:', error)
  }
}

async function loadRolePermissions(roleId) {
  try {
    menuLoading.value = true
    apiLoading.value = true

    const response = await systemV2Api.getRolePermissions(roleId)
    const permissions = response.data || {}

    selectedRole.value = {
      ...selectedRole.value,
      menu_permissions: permissions.menu_permissions || [],
      api_permissions: permissions.api_permissions || [],
      data_permissions: permissions.data_permissions || {
        scope: 'dept',
        departments: [],
        fields: [],
      },
    }
  } catch (error) {
    $message.error('加载角色权限失败')
    console.error('Load role permissions error:', error)
  } finally {
    menuLoading.value = false
    apiLoading.value = false
  }
}

function handleSelectRole(role) {
  selectedRole.value = { ...role }
  activeTab.value = 'menu'
}

function handleRoleSearch() {
  // 搜索逻辑已在计算属性中处理
}

function handleAddRole() {
  roleForm.value = {
    name: '',
    description: '',
    is_active: true,
  }
  roleModalTitle.value = '新增角色'
  roleModalVisible.value = true
}

function handleEditRole(role) {
  roleForm.value = { ...role }
  roleModalTitle.value = '编辑角色'
  roleModalVisible.value = true
}

async function handleSaveRole() {
  try {
    await roleFormRef.value?.validate()
    roleModalLoading.value = true

    if (roleForm.value.id) {
      await systemV2Api.updateRole(roleForm.value.id, roleForm.value)
      $message.success('角色更新成功')
    } else {
      await systemV2Api.createRole(roleForm.value)
      $message.success('角色创建成功')
    }

    roleModalVisible.value = false
    await loadRoles()
  } catch (error) {
    $message.error('保存角色失败')
    console.error('Save role error:', error)
  } finally {
    roleModalLoading.value = false
  }
}

async function handleDeleteRole(role) {
  try {
    await systemV2Api.deleteRole(role.id)
    $message.success('角色删除成功')

    if (selectedRole.value?.id === role.id) {
      selectedRole.value = null
    }

    await loadRoles()
  } catch (error) {
    $message.error('删除角色失败')
    console.error('Delete role error:', error)
  }
}

function handleMenuPermissionChange(checkedKeys) {
  if (selectedRole.value) {
    selectedRole.value.menu_permissions = checkedKeys
  }
}

function handleApiPermissionChange(checkedKeys) {
  if (selectedRole.value) {
    selectedRole.value.api_permissions = checkedKeys
  }
}

function handleFieldPermissionChange(fieldKey, checked) {
  if (!selectedRole.value.data_permissions.fields) {
    selectedRole.value.data_permissions.fields = []
  }

  const fields = selectedRole.value.data_permissions.fields
  const index = fields.indexOf(fieldKey)

  if (checked && index === -1) {
    fields.push(fieldKey)
  } else if (!checked && index > -1) {
    fields.splice(index, 1)
  }
}

async function handleSaveAll() {
  if (!selectedRole.value) {
    $message.warning('请先选择一个角色')
    return
  }

  try {
    saving.value = true

    const permissionData = {
      menu_permissions: selectedRole.value.menu_permissions,
      api_permissions: selectedRole.value.api_permissions,
      data_permissions: selectedRole.value.data_permissions,
    }

    await systemV2Api.updateRolePermissions(selectedRole.value.id, permissionData)
    $message.success('权限配置保存成功')
  } catch (error) {
    $message.error('保存权限配置失败')
    console.error('Save permissions error:', error)
  } finally {
    saving.value = false
  }
}

function handleRefresh() {
  loadRoles()
  if (selectedRole.value) {
    loadRolePermissions(selectedRole.value.id)
  }
}

async function handleExport() {
  try {
    const response = await systemV2Api.exportRolePermissions()
    const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `role-permissions-${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
    $message.success('权限配置导出成功')
  } catch (error) {
    $message.error('导出权限配置失败')
    console.error('Export error:', error)
  }
}

function handleImport() {
  importModalVisible.value = true
  importFileList.value = []
  importPreview.value = null
}

function handleImportFileChange({ fileList }) {
  importFileList.value = fileList

  if (fileList.length > 0) {
    const file = fileList[0].file
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        importPreview.value = JSON.parse(e.target.result)
      } catch (error) {
        $message.error('文件格式错误，请上传有效的JSON文件')
        importFileList.value = []
      }
    }
    reader.readAsText(file)
  }
}

async function handleConfirmImport() {
  try {
    await systemV2Api.importRolePermissions(importPreview.value)
    $message.success('权限配置导入成功')
    importModalVisible.value = false
    await loadRoles()
  } catch (error) {
    $message.error('导入权限配置失败')
    console.error('Import error:', error)
  }
}

// 树操作方法
function handleExpandAllMenus() {
  menuTreeRef.value?.expandAll()
}

function handleCollapseAllMenus() {
  menuTreeRef.value?.collapseAll()
}

function handleSelectAllMenus() {
  menuTreeRef.value?.selectAll()
}

function handleDeselectAllMenus() {
  menuTreeRef.value?.deselectAll()
}

// 工具方法
function getMethodTagType(method) {
  const typeMap = {
    GET: 'info',
    POST: 'success',
    PUT: 'warning',
    DELETE: 'error',
    PATCH: 'default',
  }
  return typeMap[method] || 'default'
}

function getDataScopeLabel(scope) {
  const labelMap = {
    all: '全部数据',
    dept: '本部门数据',
    dept_and_sub: '本部门及下级部门数据',
    self: '仅本人数据',
    custom: '自定义数据权限',
  }
  return labelMap[scope] || '未设置'
}
</script>

<style scoped>
.role-permission-config {
  height: 100%;
}

.config-layout {
  display: flex;
  gap: 16px;
  height: calc(100vh - 200px);
}

.role-list-panel {
  width: 320px;
  flex-shrink: 0;
}

.role-list-card {
  height: 100%;
}

.role-search {
  margin-bottom: 16px;
}

.role-list {
  max-height: calc(100% - 120px);
  overflow-y: auto;
}

.role-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.role-item:hover {
  border-color: var(--primary-color);
  background-color: var(--hover-color);
}

.role-item.active {
  border-color: var(--primary-color);
  background-color: var(--primary-color-hover);
}

.role-info {
  flex: 1;
}

.role-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.role-desc {
  font-size: 12px;
  color: var(--text-color-secondary);
  margin-bottom: 8px;
}

.role-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-count {
  font-size: 12px;
  color: var(--text-color-secondary);
}

.role-actions {
  display: flex;
  gap: 4px;
}

.permission-config-panel {
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

.permission-tabs {
  height: 100%;
}

.permission-section {
  padding: 16px 0;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

.section-desc {
  margin: 4px 0 0 0;
  font-size: 12px;
  color: var(--text-color-secondary);
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

.data-permission-config {
  max-width: 600px;
}

.field-permissions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.field-permission-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-desc {
  font-size: 12px;
  color: var(--text-color-secondary);
  margin-left: 24px;
}

.permission-preview {
  padding: 16px 0;
}

.permission-list {
  max-height: 200px;
  overflow-y: auto;
}

.permission-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 12px;
}

.data-permission-summary {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.summary-item .label {
  font-weight: 500;
  min-width: 80px;
}

.summary-item .value {
  color: var(--text-color-secondary);
}

.import-config {
  padding: 16px 0;
}

.upload-content {
  text-align: center;
  padding: 32px;
}

.upload-icon {
  color: var(--text-color-secondary);
  margin-bottom: 16px;
}

.upload-text {
  margin: 0 0 8px 0;
  font-size: 14px;
}

.upload-hint {
  margin: 0;
  font-size: 12px;
  color: var(--text-color-secondary);
}

.import-preview {
  margin-top: 16px;
  max-height: 300px;
  overflow-y: auto;
}

.import-preview h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
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
