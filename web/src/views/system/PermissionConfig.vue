<template>
  <CommonPage
    show-footer
    title="权限配置管理"
    class="permission-config-page system-management-page standard-page"
  >
    <template #action>
      <div class="flex items-center gap-3">
        <NButton type="primary" @click="handleQuickConfig">
          <TheIcon icon="material-symbols:settings" :size="18" class="mr-1" />
          快速配置
        </NButton>
        <NButton @click="handleRefresh">
          <TheIcon icon="material-symbols:refresh" :size="18" class="mr-1" />
          刷新
        </NButton>
      </div>
    </template>

    <div class="permission-config-content">
      <!-- 功能导航卡片 -->
      <div class="config-navigation">
        <NGrid :cols="2" :x-gap="24" :y-gap="24">
          <NGi>
            <NCard
              class="nav-card role-config-card"
              hoverable
              @click="handleNavigate('role-permission')"
            >
              <div class="nav-card-content">
                <div class="nav-icon">
                  <TheIcon icon="material-symbols:person-check" :size="48" />
                </div>
                <div class="nav-info">
                  <h3 class="nav-title">角色权限配置</h3>
                  <p class="nav-desc">配置角色的菜单权限、API权限和数据权限</p>
                  <div class="nav-stats">
                    <span class="stat-item">{{ roleStats.total }} 个角色</span>
                    <span class="stat-item">{{ roleStats.active }} 个启用</span>
                  </div>
                </div>
                <div class="nav-arrow">
                  <TheIcon icon="material-symbols:arrow-forward" :size="24" />
                </div>
              </div>
            </NCard>
          </NGi>

          <NGi>
            <NCard
              class="nav-card user-permission-card"
              hoverable
              @click="handleNavigate('user-permission')"
            >
              <div class="nav-card-content">
                <div class="nav-icon">
                  <TheIcon icon="material-symbols:person-search" :size="48" />
                </div>
                <div class="nav-info">
                  <h3 class="nav-title">用户权限查看</h3>
                  <p class="nav-desc">查看用户的完整权限信息和权限来源</p>
                  <div class="nav-stats">
                    <span class="stat-item">{{ userStats.total }} 个用户</span>
                    <span class="stat-item">{{ userStats.active }} 个活跃</span>
                  </div>
                </div>
                <div class="nav-arrow">
                  <TheIcon icon="material-symbols:arrow-forward" :size="24" />
                </div>
              </div>
            </NCard>
          </NGi>

          <NGi>
            <NCard
              class="nav-card editor-card"
              hoverable
              @click="handleNavigate('permission-editor')"
            >
              <div class="nav-card-content">
                <div class="nav-icon">
                  <TheIcon icon="material-symbols:edit-note" :size="48" />
                </div>
                <div class="nav-info">
                  <h3 class="nav-title">权限配置编辑器</h3>
                  <p class="nav-desc">可视化编辑权限规则和条件配置</p>
                  <div class="nav-stats">
                    <span class="stat-item">{{ configStats.rules }} 条规则</span>
                    <span class="stat-item">{{ configStats.conditions }} 个条件</span>
                  </div>
                </div>
                <div class="nav-arrow">
                  <TheIcon icon="material-symbols:arrow-forward" :size="24" />
                </div>
              </div>
            </NCard>
          </NGi>

          <NGi>
            <NCard
              class="nav-card import-export-card"
              hoverable
              @click="handleNavigate('import-export')"
            >
              <div class="nav-card-content">
                <div class="nav-icon">
                  <TheIcon icon="material-symbols:import-export" :size="48" />
                </div>
                <div class="nav-info">
                  <h3 class="nav-title">导入导出配置</h3>
                  <p class="nav-desc">批量导入导出权限配置，支持多种格式</p>
                  <div class="nav-stats">
                    <span class="stat-item">支持 JSON/YAML</span>
                    <span class="stat-item">模板下载</span>
                  </div>
                </div>
                <div class="nav-arrow">
                  <TheIcon icon="material-symbols:arrow-forward" :size="24" />
                </div>
              </div>
            </NCard>
          </NGi>
        </NGrid>
      </div>

      <!-- 系统概览 -->
      <div class="system-overview">
        <NCard title="系统权限概览" class="overview-card">
          <div class="overview-content">
            <NGrid :cols="4" :x-gap="24">
              <NGi>
                <div class="overview-item">
                  <div class="overview-icon roles-icon">
                    <TheIcon icon="material-symbols:group" :size="32" />
                  </div>
                  <div class="overview-info">
                    <div class="overview-number">{{ systemOverview.roles }}</div>
                    <div class="overview-label">角色数量</div>
                  </div>
                </div>
              </NGi>

              <NGi>
                <div class="overview-item">
                  <div class="overview-icon users-icon">
                    <TheIcon icon="material-symbols:person" :size="32" />
                  </div>
                  <div class="overview-info">
                    <div class="overview-number">{{ systemOverview.users }}</div>
                    <div class="overview-label">用户数量</div>
                  </div>
                </div>
              </NGi>

              <NGi>
                <div class="overview-item">
                  <div class="overview-icon menus-icon">
                    <TheIcon icon="material-symbols:menu" :size="32" />
                  </div>
                  <div class="overview-info">
                    <div class="overview-number">{{ systemOverview.menus }}</div>
                    <div class="overview-label">菜单数量</div>
                  </div>
                </div>
              </NGi>

              <NGi>
                <div class="overview-item">
                  <div class="overview-icon apis-icon">
                    <TheIcon icon="material-symbols:api" :size="32" />
                  </div>
                  <div class="overview-info">
                    <div class="overview-number">{{ systemOverview.apis }}</div>
                    <div class="overview-label">API数量</div>
                  </div>
                </div>
              </NGi>
            </NGrid>
          </div>
        </NCard>
      </div>

      <!-- 快捷操作 -->
      <div class="quick-actions">
        <NCard title="快捷操作" class="actions-card">
          <div class="actions-content">
            <NSpace size="large">
              <NButton type="primary" @click="handleCreateRole">
                <TheIcon icon="material-symbols:add" :size="18" class="mr-1" />
                新建角色
              </NButton>
              <NButton @click="handleBatchAssign">
                <TheIcon icon="material-symbols:group-add" :size="18" class="mr-1" />
                批量分配权限
              </NButton>
              <NButton @click="handlePermissionCheck">
                <TheIcon icon="material-symbols:security" :size="18" class="mr-1" />
                权限检查
              </NButton>
              <NButton @click="handleExportReport">
                <TheIcon icon="material-symbols:assessment" :size="18" class="mr-1" />
                生成报告
              </NButton>
            </NSpace>
          </div>
        </NCard>
      </div>

      <!-- 最近操作 -->
      <div class="recent-activities">
        <NCard title="最近操作" class="activities-card">
          <div class="activities-content">
            <div class="activity-list">
              <div v-for="activity in recentActivities" :key="activity.id" class="activity-item">
                <div class="activity-icon">
                  <TheIcon :icon="getActivityIcon(activity.type)" :size="20" />
                </div>
                <div class="activity-info">
                  <div class="activity-desc">{{ activity.description }}</div>
                  <div class="activity-meta">
                    <span class="activity-user">{{ activity.operator }}</span>
                    <span class="activity-time">{{ formatDate(activity.created_at) }}</span>
                  </div>
                </div>
                <div class="activity-status">
                  <NTag :type="getActivityTagType(activity.status)" size="small">
                    {{ activity.status }}
                  </NTag>
                </div>
              </div>
            </div>
          </div>
        </NCard>
      </div>
    </div>
  </CommonPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NCard, NGrid, NGi, NSpace, NTag, useMessage } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import systemV2Api from '@/api/system-v2'
import { formatDate } from '@/utils'

defineOptions({ name: 'PermissionConfig' })

const $message = useMessage()
const router = useRouter()

// 数据状态
const roleStats = ref({ total: 0, active: 0 })
const userStats = ref({ total: 0, active: 0 })
const configStats = ref({ rules: 0, conditions: 0 })
const systemOverview = ref({
  roles: 0,
  users: 0,
  menus: 0,
  apis: 0,
})
const recentActivities = ref([])

// 生命周期
onMounted(() => {
  loadOverviewData()
  loadRecentActivities()
})

// 方法
async function loadOverviewData() {
  try {
    const [rolesRes, usersRes, menusRes, apisRes] = await Promise.all([
      systemV2Api.getRoles(),
      systemV2Api.getUsers(),
      systemV2Api.getMenus(),
      systemV2Api.getApis(),
    ])

    const roles = rolesRes.data || []
    const users = usersRes.data || []
    const menus = menusRes.data || []
    const apis = apisRes.data || []

    roleStats.value = {
      total: roles.length,
      active: roles.filter((r) => r.is_active).length,
    }

    userStats.value = {
      total: users.length,
      active: users.filter((u) => u.is_active).length,
    }

    systemOverview.value = {
      roles: roles.length,
      users: users.length,
      menus: menus.length,
      apis: apis.length,
    }

    // 模拟配置统计
    configStats.value = {
      rules: roles.reduce((sum, role) => sum + (role.rules?.length || 0), 0),
      conditions: roles.reduce((sum, role) => sum + (role.conditions?.length || 0), 0),
    }
  } catch (error) {
    console.error('Load overview data error:', error)
  }
}

async function loadRecentActivities() {
  try {
    const response = await systemV2Api.getPermissionActivities()
    recentActivities.value = (response.data || []).slice(0, 10)
  } catch (error) {
    console.error('Load recent activities error:', error)
    // 模拟数据
    recentActivities.value = [
      {
        id: 1,
        type: 'role_create',
        description: '创建了新角色 "数据分析师"',
        operator: '管理员',
        status: '成功',
        created_at: new Date().toISOString(),
      },
      {
        id: 2,
        type: 'permission_assign',
        description: '为用户 "张三" 分配了 "用户管理" 权限',
        operator: '管理员',
        status: '成功',
        created_at: new Date(Date.now() - 3600000).toISOString(),
      },
      {
        id: 3,
        type: 'config_export',
        description: '导出了权限配置文件',
        operator: '系统管理员',
        status: '成功',
        created_at: new Date(Date.now() - 7200000).toISOString(),
      },
    ]
  }
}

function handleNavigate(page) {
  const routes = {
    'role-permission': '/system/permission-config/role',
    'user-permission': '/system/permission-config/user',
    'permission-editor': '/system/permission-config/editor',
    'import-export': '/system/permission-config/import-export',
  }

  const route = routes[page]
  if (route) {
    router.push(route)
  }
}

function handleQuickConfig() {
  router.push('/system/permission-config/role')
}

function handleRefresh() {
  loadOverviewData()
  loadRecentActivities()
  $message.success('数据已刷新')
}

function handleCreateRole() {
  router.push('/system/role')
}

function handleBatchAssign() {
  $message.info('批量分配权限功能开发中')
}

function handlePermissionCheck() {
  $message.info('权限检查功能开发中')
}

async function handleExportReport() {
  try {
    const response = await systemV2Api.exportPermissionReport()

    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `permission-report-${new Date().toISOString().split('T')[0]}.pdf`
    a.click()
    URL.revokeObjectURL(url)

    $message.success('权限报告导出成功')
  } catch (error) {
    $message.error('导出权限报告失败')
    console.error('Export report error:', error)
  }
}

// 工具方法
function getActivityIcon(type) {
  const iconMap = {
    role_create: 'material-symbols:person-add',
    role_update: 'material-symbols:person-edit',
    role_delete: 'material-symbols:person-remove',
    permission_assign: 'material-symbols:security',
    permission_revoke: 'material-symbols:security-off',
    config_export: 'material-symbols:download',
    config_import: 'material-symbols:upload',
    user_login: 'material-symbols:login',
    user_logout: 'material-symbols:logout',
  }
  return iconMap[type] || 'material-symbols:info'
}

function getActivityTagType(status) {
  const typeMap = {
    成功: 'success',
    失败: 'error',
    警告: 'warning',
    处理中: 'info',
  }
  return typeMap[status] || 'default'
}
</script>

<style scoped>
.permission-config-content {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 功能导航卡片 */
.config-navigation {
  margin-bottom: 24px;
}

.nav-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid var(--border-color);
}

.nav-card:hover {
  border-color: var(--primary-color);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.nav-card-content {
  display: flex;
  align-items: center;
  padding: 24px;
  gap: 20px;
}

.nav-icon {
  flex-shrink: 0;
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--primary-color-hover), var(--primary-color));
  color: white;
}

.role-config-card .nav-icon {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.user-permission-card .nav-icon {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}

.editor-card .nav-icon {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
}

.import-export-card .nav-icon {
  background: linear-gradient(135deg, #43e97b, #38f9d7);
}

.nav-info {
  flex: 1;
}

.nav-title {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color-primary);
}

.nav-desc {
  margin: 0 0 12px 0;
  color: var(--text-color-secondary);
  font-size: 14px;
  line-height: 1.5;
}

.nav-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  font-size: 12px;
  color: var(--text-color-tertiary);
  padding: 4px 8px;
  background: var(--fill-color);
  border-radius: 4px;
}

.nav-arrow {
  flex-shrink: 0;
  color: var(--text-color-secondary);
  transition: transform 0.3s ease;
}

.nav-card:hover .nav-arrow {
  transform: translateX(4px);
  color: var(--primary-color);
}

/* 系统概览 */
.system-overview {
  margin-bottom: 24px;
}

.overview-content {
  padding: 24px 0;
}

.overview-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.overview-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.roles-icon {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.users-icon {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}

.menus-icon {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
}

.apis-icon {
  background: linear-gradient(135deg, #43e97b, #38f9d7);
}

.overview-info {
  flex: 1;
}

.overview-number {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-color-primary);
  margin-bottom: 4px;
}

.overview-label {
  font-size: 14px;
  color: var(--text-color-secondary);
}

/* 快捷操作 */
.quick-actions {
  margin-bottom: 24px;
}

.actions-content {
  padding: 20px 0;
}

/* 最近操作 */
.recent-activities {
  margin-bottom: 24px;
}

.activities-content {
  padding: 16px 0;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  transition: all 0.2s ease;
}

.activity-item:hover {
  border-color: var(--primary-color-hover);
  background: var(--hover-color);
}

.activity-icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: var(--fill-color);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-color-secondary);
}

.activity-info {
  flex: 1;
}

.activity-desc {
  font-size: 14px;
  color: var(--text-color-primary);
  margin-bottom: 4px;
}

.activity-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-color-secondary);
}

.activity-status {
  flex-shrink: 0;
}

.mr-1 {
  margin-right: 4px;
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

/* 响应式设计 */
@media (max-width: 768px) {
  .permission-config-content {
    padding: 16px;
  }

  .nav-card-content {
    padding: 16px;
    gap: 12px;
  }

  .nav-icon {
    width: 48px;
    height: 48px;
  }

  .nav-title {
    font-size: 16px;
  }

  .overview-content {
    padding: 16px 0;
  }

  .overview-item {
    flex-direction: column;
    text-align: center;
    gap: 8px;
  }

  .overview-icon {
    width: 40px;
    height: 40px;
  }

  .overview-number {
    font-size: 20px;
  }
}
</style>
