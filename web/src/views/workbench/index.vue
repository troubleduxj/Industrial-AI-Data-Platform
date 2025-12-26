<template>
  <AppPage :show-footer="false">
    <div class="workbench-container">
      <!-- 用户欢迎区域 -->
      <n-card class="welcome-card" :bordered="false">
        <div class="welcome-content">
          <div class="user-info">
            <div class="avatar-container">
              <img
                class="user-avatar"
                :src="userStore.avatar || '/default-avatar.png'"
                :alt="userStore.name || 'User'"
              />
              <div class="status-indicator"></div>
            </div>
            <div class="user-details">
              <h1 class="welcome-title">
                {{ $t('views.workbench.text_hello', { username: userStore.name || '用户' }) }} 🎉
              </h1>
              <p class="welcome-subtitle">{{ $t('views.workbench.text_welcome') }}</p>
            </div>
          </div>
          <div class="quick-actions">
            <n-button size="large" type="tertiary" @click="handleCardClick('/dashboard')">
              <Icon icon="ant-design:dashboard-outlined" class="mr-2" />
              快速监控
            </n-button>
            <n-button
              v-if="
                userStore.isSuperUser ||
                userStore.role.some((r) => r.name === '管理员' || r.name === 'admin')
              "
              size="large"
              type="tertiary"
              @click="handleCardClick('/device')"
            >
              <Icon icon="ant-design:setting-outlined" class="mr-2" />
              系统设置
            </n-button>
          </div>
        </div>
      </n-card>

      <!-- 统计数据卡片 -->
      <div class="stats-section">
        <n-grid cols="2 s:2 m:4 l:4 xl:4 2xl:4" responsive="screen" :x-gap="16" :y-gap="16">
          <n-gi>
            <n-card class="stat-card" :bordered="false">
              <div class="stat-content">
                <div class="stat-icon online">
                  <Icon icon="ant-design:check-circle-outlined" />
                </div>
                <div class="stat-info">
                  <div class="stat-value">1,234</div>
                  <div class="stat-label">在线设备</div>
                  <div class="stat-trend positive">↗ 12 较昨日</div>
                </div>
              </div>
            </n-card>
          </n-gi>
          <n-gi>
            <n-card class="stat-card" :bordered="false">
              <div class="stat-content">
                <div class="stat-icon warning">
                  <Icon icon="ant-design:warning-outlined" />
                </div>
                <div class="stat-info">
                  <div class="stat-value">23</div>
                  <div class="stat-label">告警数量</div>
                  <div class="stat-trend negative">↗ 3 较昨日</div>
                </div>
              </div>
            </n-card>
          </n-gi>
          <n-gi>
            <n-card class="stat-card" :bordered="false">
              <div class="stat-content">
                <div class="stat-icon success">
                  <Icon icon="ant-design:database-outlined" />
                </div>
                <div class="stat-info">
                  <div class="stat-value">98.5%</div>
                  <div class="stat-label">数据处理</div>
                  <div class="stat-trend positive">↗ 1.2% 较昨日</div>
                </div>
              </div>
            </n-card>
          </n-gi>

          <n-gi>
            <n-card class="stat-card" :bordered="false">
              <div class="stat-content">
                <div class="stat-icon info">
                  <Icon icon="ant-design:thunderbolt-outlined" />
                </div>
                <div class="stat-info">
                  <div class="stat-value">45%</div>
                  <div class="stat-label">系统负载</div>
                  <div class="stat-trend neutral">→ 正常范围</div>
                </div>
              </div>
            </n-card>
          </n-gi>
        </n-grid>
      </div>

      <!-- 功能模块区域 -->
      <div class="modules-section">
        <h2 class="section-title">
          <Icon icon="ant-design:appstore-outlined" class="mr-2" />
          功能模块
        </h2>

        <!-- 功能模块网格 -->
        <n-grid
          v-if="hasAnyModulePermission"
          cols="1 s:2 m:3 l:4 xl:4 2xl:4"
          responsive="screen"
          :x-gap="20"
          :y-gap="20"
        >
          <n-gi v-if="hasWorkbenchModulePermission('/dashboard')">
            <n-card class="module-card dashboard" hoverable @click="handleCardClick('/dashboard')">
              <div class="module-header">
                <div class="module-icon">
                  <Icon icon="ant-design:dashboard-outlined" />
                </div>
                <div class="module-badge">实时</div>
              </div>
              <div class="module-content">
                <h3 class="module-title">监测看板</h3>
                <p class="module-description">实时监控设备状态和运行数据</p>
              </div>
              <div class="module-footer">
                <span class="module-action">进入看板</span>
              </div>
            </n-card>
          </n-gi>
          <n-gi v-if="hasWorkbenchModulePermission('/device')">
            <n-card class="module-card device" hoverable @click="handleCardClick('/device')">
              <div class="module-header">
                <div class="module-icon">
                  <Icon icon="ant-design:appstore-outlined" />
                </div>
                <div class="module-badge">管理</div>
              </div>
              <div class="module-content">
                <h3 class="module-title">设备管理</h3>
                <p class="module-description">管理和配置所有连接的设备</p>
              </div>
              <div class="module-footer">
                <span class="module-action">设备列表</span>
              </div>
            </n-card>
          </n-gi>
          <n-gi v-if="hasWorkbenchModulePermission('/device-monitoring')">
            <n-card
              class="module-card monitoring"
              hoverable
              @click="handleCardClick('/device-monitoring')"
            >
              <div class="module-header">
                <div class="module-icon">
                  <Icon icon="ant-design:monitor-outlined" />
                </div>
                <div class="module-badge">监测</div>
              </div>
              <div class="module-content">
                <h3 class="module-title">设备监测</h3>
                <p class="module-description">实时监测设备运行状态和参数</p>
              </div>
              <div class="module-footer">
                <span class="module-action">开始监测</span>
              </div>
            </n-card>
          </n-gi>
          <n-gi v-if="hasWorkbenchModulePermission('/device-maintenance')">
            <n-card
              class="module-card maintenance"
              hoverable
              @click="handleCardClick('/device-maintenance')"
            >
              <div class="module-header">
                <div class="module-icon">
                  <Icon icon="ant-design:tool-outlined" />
                </div>
                <div class="module-badge">维护</div>
              </div>
              <div class="module-content">
                <h3 class="module-title">设备维护</h3>
                <p class="module-description">设备维护计划和维修记录管理</p>
              </div>
              <div class="module-footer">
                <span class="module-action">维护管理</span>
              </div>
            </n-card>
          </n-gi>
          <n-gi v-if="hasWorkbenchModulePermission('/statistics')">
            <n-card
              class="module-card statistics"
              hoverable
              @click="handleCardClick('/statistics')"
            >
              <div class="module-header">
                <div class="module-icon">
                  <Icon icon="ant-design:bar-chart-outlined" />
                </div>
                <div class="module-badge">分析</div>
              </div>
              <div class="module-content">
                <h3 class="module-title">数据统计</h3>
                <p class="module-description">设备数据分析和统计报表</p>
              </div>
              <div class="module-footer">
                <span class="module-action">查看统计</span>
              </div>
            </n-card>
          </n-gi>
          <n-gi v-if="hasWorkbenchModulePermission('/alarm')">
            <n-card class="module-card alarm" hoverable @click="handleCardClick('/alarm')">
              <div class="module-header">
                <div class="module-icon">
                  <Icon icon="ant-design:bell-outlined" />
                </div>
                <div class="module-badge">告警</div>
              </div>
              <div class="module-content">
                <h3 class="module-title">告警中心</h3>
                <p class="module-description">设备异常告警和通知管理</p>
              </div>
              <div class="module-footer">
                <span class="module-action">告警管理</span>
              </div>
            </n-card>
          </n-gi>
          <n-gi v-if="hasWorkbenchModulePermission('/workflow')">
            <n-card class="module-card workflow" hoverable @click="handleCardClick('/workflow')">
              <div class="module-header">
                <div class="module-icon">
                  <Icon icon="ant-design:apartment-outlined" />
                </div>
                <div class="module-badge">编排</div>
              </div>
              <div class="module-content">
                <h3 class="module-title">流程编排</h3>
                <p class="module-description">自动化流程设计和任务编排</p>
              </div>
              <div class="module-footer">
                <span class="module-action">流程管理</span>
              </div>
            </n-card>
          </n-gi>

          <n-gi v-if="hasWorkbenchModulePermission('/data-model')">
            <n-card class="module-card data-model" hoverable @click="handleCardClick('/data-model')">
              <div class="module-header">
                <div class="module-icon">
                  <Icon icon="ant-design:database-outlined" />
                </div>
                <div class="module-badge">模型</div>
              </div>
              <div class="module-content">
                <h3 class="module-title">数据模型</h3>
                <p class="module-description">数据模型管理和配置</p>
              </div>
              <div class="module-footer">
                <span class="module-action">模型管理</span>
              </div>
            </n-card>
          </n-gi>

          <n-gi v-if="hasWorkbenchModulePermission('/ai-monitoring')">
            <n-card class="module-card ai" hoverable @click="handleCardClick('/ai-monitoring')">
              <div class="module-header">
                <div class="module-icon">
                  <Icon icon="ant-design:robot-outlined" />
                </div>
                <div class="module-badge">AI</div>
              </div>
              <div class="module-content">
                <h3 class="module-title">AI监测</h3>
                <p class="module-description">智能分析和预测性维护</p>
              </div>
              <div class="module-footer">
                <span class="module-action">AI分析</span>
              </div>
            </n-card>
          </n-gi>
          <n-gi v-if="hasWorkbenchModulePermission('/notification')">
            <n-card class="module-card notification" hoverable @click="handleCardClick('/notification')">
              <div class="module-header">
                <div class="module-icon">
                  <Icon icon="ant-design:notification-outlined" />
                </div>
                <div class="module-badge">通知</div>
              </div>
              <div class="module-content">
                <h3 class="module-title">通知管理</h3>
                <p class="module-description">系统通知与消息模板</p>
              </div>
              <div class="module-footer">
                <span class="module-action">通知设置</span>
              </div>
            </n-card>
          </n-gi>
          <n-gi v-if="hasWorkbenchModulePermission('/system')">
            <n-card class="module-card system" hoverable @click="handleCardClick('/system')">
              <div class="module-header">
                <div class="module-icon">
                  <Icon icon="ant-design:setting-outlined" />
                </div>
                <div class="module-badge">管理</div>
              </div>
              <div class="module-content">
                <h3 class="module-title">系统管理</h3>
                <p class="module-description">系统配置和用户权限管理</p>
              </div>
              <div class="module-footer">
                <span class="module-action">系统设置</span>
              </div>
            </n-card>
          </n-gi>
        </n-grid>

        <!-- 无权限时的空状态提示 -->
        <div v-else class="empty-modules-state">
          <n-empty description="暂无可用功能模块" size="large" style="margin: 60px 0">
            <template #icon>
              <Icon icon="ant-design:appstore-outlined" style="font-size: 48px; color: #d9d9d9" />
            </template>
            <template #extra>
              <div class="empty-state-content">
                <p style="color: #666; margin: 16px 0; font-size: 16px">
                  您当前没有任何功能模块的访问权限
                </p>
                <p style="color: #999; margin: 8px 0; font-size: 14px">
                  请联系系统管理员为您分配相应的菜单权限
                </p>
                <div style="margin-top: 24px">
                  <n-button @click="refreshPermissions" type="primary">
                    <Icon icon="ant-design:reload-outlined" style="margin-right: 4px" />
                    刷新权限
                  </n-button>
                </div>
              </div>
            </template>
          </n-empty>
        </div>
      </div>

    </div>
  </AppPage>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useUserStore, useChatWidgetStore, usePermissionStore } from '@/store'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import { getCachedConfig } from '@/api/index.js'

// 获取菜单的第一个可访问子菜单路径
const getFirstChildMenuPath = (modulePath) => {
  // 定义模块路径映射（与权限检查保持一致）
  const modulePathMappings = {
    '/dashboard': ['dashboard', '/dashboard', 'monitoring-dashboard', 'monitor-dashboard', '监测看板'],
    '/device': ['device', '/device', 'device-management', '设备管理'],
    '/device-monitor': ['device-monitoring', '/device-monitoring', 'device-monitor', '/device-monitor', '设备监测'],
    '/device-monitoring': ['device-monitoring', '/device-monitoring', 'device-monitor', '/device-monitor', '设备监测'],
    '/device-maintenance': ['device-maintenance', '/device-maintenance', '设备维护'],
    '/statistics': ['statistics', '/statistics', 'data-statistics', '数据统计'],
    '/alarm': ['alarm', '/alarm', 'alarm-center', '告警中心'],
    '/workflow': ['workflow', '/workflow', 'flow-settings', '流程编排'],
    '/data-model': ['data-model', '/data-model', 'data-models', 'model-management', '数据模型', '数据模型管理'],
    '/ai-monitoring': ['ai-monitoring', '/ai-monitoring', 'ai-monitor', 'AI监测'],
    '/notification': ['notification', '/notification', '系统通知', '通知管理', 'notification/list', 'notification/email-server', 'notification/email-template', 'notification/send-config'],
    '/system': ['system', '/system', 'system-management', '系统管理'],
  }
  
  // 获取可能的路径匹配列表
  const possiblePaths = modulePathMappings[modulePath] || [modulePath]
  
  // 递归查找菜单
  const findMenu = (menus, pathList, depth = 0) => {
    for (const menu of menus) {
      // 只使用path字段（字符串），不使用component（可能是函数）
      const menuPath = typeof menu.path === 'string' ? menu.path : ''
      const menuPathClean = menuPath.replace(/^\/+/, '')
      const menuName = menu.name || menu.title || ''
      
      // 跳过工作台菜单本身
      if (menuName.includes('工作台') && depth === 0) {
        // 但要检查其子菜单
        if (menu.children && menu.children.length > 0) {
          const result = findMenu(menu.children, pathList, depth + 1)
          if (result) return result
        }
        continue
      }
      
      // 检查是否匹配任何可能的路径
      const isMatch = pathList.some(targetPath => {
        const targetPathClean = targetPath.replace(/^\/+/, '')
        // 精确匹配或名称匹配
        return menuPathClean === targetPathClean || 
               (menuName && targetPathClean && menuName.includes(targetPathClean))
      })
      
      if (isMatch) {
        console.log(`🔍 匹配到菜单: "${menuName}" (path: ${menuPath})`)
        
        // 如果有子菜单，返回第一个子菜单的路径
        if (menu.children && menu.children.length > 0) {
          const firstChild = menu.children[0]
          // 只使用path字段
          let childPath = typeof firstChild.path === 'string' ? firstChild.path : null
          if (childPath) {
            // 如果子路径不是以 / 开头，需要拼接父路径
            if (!childPath.startsWith('/')) {
              childPath = menuPath ? `${menuPath}/${childPath}` : `/${childPath}`
            }
            console.log(`✅ 找到菜单 "${menuName}" 的第一个子菜单: ${childPath}`)
            return childPath
          }
        }
        
        // 没有子菜单，返回当前菜单路径
        if (menuPath) {
          console.log(`✅ 找到菜单 "${menuName}" (无子菜单): ${menuPath}`)
          return menuPath
        }
      }
      
      // 递归查找子菜单
      if (menu.children && menu.children.length > 0) {
        const result = findMenu(menu.children, pathList, depth + 1)
        if (result) return result
      }
    }
    return null
  }
  
  // 如果没有菜单数据，直接返回原路径
  if (!permissionStore.menus || permissionStore.menus.length === 0) {
    console.log(`⚠️ 菜单数据未加载，使用默认路径: ${modulePath}`)
    return modulePath
  }
  
  const foundPath = findMenu(permissionStore.menus, possiblePaths)
  if (!foundPath) {
    console.log(`⚠️ 未找到匹配的菜单，使用默认路径: ${modulePath}`)
  }
  return foundPath || modulePath
}

const handleCardClick = (route) => {
  // 获取第一个子菜单路径
  const targetPath = getFirstChildMenuPath(route)
  console.log(`🔗 卡片点击: ${route} -> ${targetPath}`)
  
  // 确保targetPath是字符串
  if (typeof targetPath === 'string') {
    router.push(targetPath)
  } else {
    console.error(`❌ 无效的路径类型: ${typeof targetPath}`, targetPath)
    // 使用原始路径作为后备
    router.push(route)
  }
}

const { t } = useI18n({ useScope: 'global' })
const router = useRouter()
const chatWidgetStore = useChatWidgetStore()

const statisticData = computed(() => [
  {
    id: 0,
    label: t('views.workbench.label_number_of_items'),
    value: '25',
  },
  {
    id: 1,
    label: t('views.workbench.label_upcoming'),
    value: '4/16',
  },
  {
    id: 2,
    label: t('views.workbench.label_information'),
    value: '12',
  },
])

// 菜单数据和处理函数已移至 UnifiedChatContainer 组件中

const userStore = useUserStore()
const permissionStore = usePermissionStore()

// 检查是否有任何模块权限
const hasAnyModulePermission = computed(() => {
  // 超级用户拥有所有权限
  if (userStore.isSuperUser) {
    return true
  }

  // 检查所有工作台模块权限
  const modulePermissions = [
    '/dashboard',
    '/device',
    '/device-monitoring',
    '/device-maintenance',
    '/statistics',
    '/alarm',
    '/workflow',
    '/ai-monitoring',
    '/notification',
    '/data-model',
    '/system',
  ]

  return modulePermissions.some((module) => hasWorkbenchModulePermission(module))
})

// 刷新权限数据
const refreshPermissions = async () => {
  try {
    console.log('🔄 刷新权限数据...')
    await Promise.all([permissionStore.generateRoutes(), permissionStore.getAccessApis()])
    console.log('✅ 权限数据刷新成功')
  } catch (error) {
    console.error('❌ 权限数据刷新失败:', error)
  }
}

// 权限检查方法 - 增强版本，支持多种匹配模式
const hasMenuPermission = (menuPath) => {
  // 超级管理员拥有所有权限
  if (userStore.isSuperUser) {
    console.log(`🔓 超级用户权限: ${menuPath} - 允许访问`)
    return true
  }

  // 管理员角色拥有所有权限
  if (userStore.role && userStore.role.some((r) => r.name === '管理员' || r.name === 'admin')) {
    console.log(`👑 管理员角色权限: ${menuPath} - 允许访问`)
    return true
  }

  // 检查权限数据是否已加载
  if (!permissionStore.menus || permissionStore.menus.length === 0) {
    console.log(`⚠️ 菜单权限数据未加载: ${menuPath} - 拒绝访问`)
    return false
  }

  // 递归检查菜单权限 - 支持多种匹配模式
  const checkMenuAccess = (menus, targetPath) => {
    for (const menu of menus) {
      // 1. 精确匹配路径
      if (menu.path === targetPath) {
        console.log(`✅ 精确匹配: ${menu.path} === ${targetPath}`)
        return true
      }

      // 2. 匹配组件路径
      if (menu.component === targetPath) {
        console.log(`✅ 组件匹配: ${menu.component} === ${targetPath}`)
        return true
      }

      // 3. 路径包含匹配（处理带前缀的路径）
      if (menu.path && targetPath) {
        // 移除开头的斜杠进行比较
        const menuPathClean = menu.path.replace(/^\/+/, '')
        const targetPathClean = targetPath.replace(/^\/+/, '')

        if (menuPathClean === targetPathClean) {
          console.log(`✅ 清理路径匹配: ${menuPathClean} === ${targetPathClean}`)
          return true
        }

        // 检查是否为子路径
        if (
          targetPathClean.startsWith(menuPathClean + '/') ||
          menuPathClean.startsWith(targetPathClean + '/')
        ) {
          console.log(`✅ 子路径匹配: ${menuPathClean} <-> ${targetPathClean}`)
          return true
        }
      }

      // 4. 菜单名称匹配（处理中文菜单名）
      if (menu.name || menu.title) {
        const menuName = menu.name || menu.title
        if (menuName.includes('设备维护') && targetPath.includes('device-maintenance')) {
          console.log(`✅ 名称匹配: ${menuName} 匹配 ${targetPath}`)
          return true
        }
        if (menuName.includes('设备管理') && targetPath.includes('device')) {
          console.log(`✅ 名称匹配: ${menuName} 匹配 ${targetPath}`)
          return true
        }
        if (menuName.includes('监测看板') && targetPath.includes('dashboard')) {
          console.log(`✅ 名称匹配: ${menuName} 匹配 ${targetPath}`)
          return true
        }
        if (menuName.includes('数据模型') && targetPath.includes('data-model')) {
          console.log(`✅ 名称匹配: ${menuName} 匹配 ${targetPath}`)
          return true
        }
      }

      // 5. 递归检查子菜单
      if (menu.children && menu.children.length > 0) {
        if (checkMenuAccess(menu.children, targetPath)) {
          console.log(`✅ 子菜单匹配: 在 ${menu.path || menu.name} 的子菜单中找到 ${targetPath}`)
          return true
        }
      }
    }
    return false
  }

  const hasAccess = checkMenuAccess(permissionStore.menus, menuPath)
  console.log(`🔍 菜单权限检查: ${menuPath} - ${hasAccess ? '允许' : '拒绝'}访问`)

  // 如果没有找到匹配，输出调试信息
  if (!hasAccess) {
    console.log(
      `🔍 调试信息 - 用户菜单列表:`,
      permissionStore.menus?.map((m) => ({
        path: m.path,
        name: m.name || (m.meta?.title as string),
        component: m.component,
        children: m.children?.length || 0,
      }))
    )
  }

  return hasAccess
}

// 工作台模块权限检查 - 专门处理工作台功能模块的权限匹配
const hasWorkbenchModulePermission = (modulePath) => {
  // 超级管理员拥有所有权限
  if (userStore.isSuperUser) {
    return true
  }

  // 定义模块路径的多种可能匹配方式
  const modulePathMappings = {
    '/dashboard': [
      'dashboard',
      '/dashboard',
      'monitoring-dashboard',
      'monitor-dashboard',
      '监测看板',
      '仪表板',
      'dashboard-weld',
      'dashboard-test',
      'dashboard-cut',
    ],
    '/device': [
      'device',
      '/device',
      'device-management',
      'device/baseinfo',
      'device/type',
      '设备管理',
      '设备信息管理',
      '设备分类管理',
    ],
    '/device-monitoring': [
      'device-monitoring',
      '/device-monitoring',
      'device-monitor',
      '/device-monitor',
      'device-monitor/monitor',
      'device-monitor/history',
      '设备监测',
      '设备实时监测',
    ],
    '/device-maintenance': [
      'device-maintenance',
      '/device-maintenance',
      'device-maintenance/repair-records',
      '设备维护',
      '维修记录',
      '设备维护管理',
    ],
    '/statistics': [
      'statistics',
      '/statistics',
      'data-statistics',
      'statistics/online-rate',
      'statistics/weld-time',
      'statistics/welding-report',
      'statistics/weld-record',
      '数据统计',
      '统计分析',
    ],
    '/alarm': [
      'alarm',
      '/alarm',
      'alarm-center',
      'alarm/alarm-info',
      'alarm/alarm-analysis',
      '告警中心',
      '报警信息',
      '报警分析',
    ],
    '/workflow': [
      'workflow',
      '/workflow',
      'flow-settings',
      'process',
      '流程编排',
      '工作流',
      '流程设计',
    ],
    '/ai-monitoring': [
      'ai-monitoring',
      '/ai-monitoring',
      'ai-monitor',
      'artificial-intelligence',
      'AI监测',
      '智能监测',
      '人工智能',
    ],
    '/notification': [
      'notification',
      '/notification',
      'notification/list',
      'notification/email-server',
      'notification/email-template',
      'notification/send-config',
      '系统通知',
      '通知管理',
    ],
    '/data-model': [
      'data-model',
      '/data-model',
      'data-models',
      'model-management',
      '数据模型',
      '模型管理',
      '数据模型管理',
    ],
    '/system': [
      'system',
      '/system',
      'system-management',
      'system/user',
      'system/role',
      'system/menu',
      'system/api',
      '系统管理',
      '用户管理',
      '角色管理',
    ],
  }

  // 获取当前模块的所有可能路径
  const possiblePaths = modulePathMappings[modulePath] || [modulePath]

  // 检查是否有任何一个可能的路径匹配用户权限
  for (const path of possiblePaths) {
    if (hasMenuPermission(path)) {
      console.log(`✅ 工作台模块权限匹配: ${modulePath} 通过路径 ${path} 匹配成功`)
      return true
    }
  }

  console.log(`❌ 工作台模块权限检查失败: ${modulePath}`)
  return false
}

// 增强的权限检查方法 - 支持多种权限类型
const hasPermission = (permission, type = 'menu') => {
  // 超级管理员拥有所有权限
  if (userStore.isSuperUser) {
    return true
  }

  switch (type) {
    case 'menu':
      return hasMenuPermission(permission)
    case 'workbench-module':
      return hasWorkbenchModulePermission(permission)
    case 'api':
      return permissionStore.accessApis?.includes(permission) || false
    case 'role':
      return userStore.role?.some((r) => r.name === permission) || false
    default:
      return false
  }
}

// 确保在workbench页面中显示边栏触发器
onMounted(async () => {
  // 设置为collapsed模式以显示SidebarTrigger
  chatWidgetStore.setDisplayMode('collapsed')

  // 获取用户信息以显示在欢迎卡片中
  try {
    await userStore.getUserInfo()
  } catch (error) {
    console.error('Failed to fetch user info:', error)
  }

  // 确保权限数据已加载
  try {
    if (!permissionStore.accessRoutes || permissionStore.accessRoutes.length === 0) {
      await permissionStore.generateRoutes()
    }
  } catch (error) {
    console.error('Failed to load permission routes:', error)
  }

  // 保持获取 AI_ASSISTANT_ENABLED 配置的逻辑，但不影响页面显示
  try {
    const response = await getCachedConfig('AI_ASSISTANT_ENABLED')
    if (response.data && response.data.param_value === 'true') {
      console.log('AI Assistant is enabled.')
    } else {
      console.log('AI Assistant is disabled.')
    }
  } catch (error) {
    console.error('Failed to fetch AI_ASSISTANT_ENABLED config:', error)
  }
})
</script>

<style scoped>
/* 工作台容器 */
.workbench-container {
  padding: 24px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 欢迎卡片 */
.welcome-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 16px;
  overflow: visible;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  min-height: 180px;
  position: relative;
  z-index: 1;
  margin-bottom: 24px;
}

.welcome-content {
  padding: 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 24px;
  min-height: 116px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.avatar-container {
  position: relative;
}

.user-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 4px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.status-indicator {
  position: absolute;
  bottom: 8px;
  right: 8px;
  width: 16px;
  height: 16px;
  background: #52c41a;
  border: 3px solid white;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}

.user-details h1.welcome-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 8px 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.welcome-subtitle {
  font-size: 16px;
  opacity: 0.9;
  margin: 0;
}

/* 响应式布局优化 */
@media (max-width: 768px) {
  .welcome-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
    padding: 24px;
  }

  .user-info {
    width: 100%;
  }

  .quick-actions {
    width: 100%;
    justify-content: center;
  }

  .welcome-card {
    min-height: 220px;
  }
}

.quick-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.quick-actions .n-button {
  border: 2px solid rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.1);
  color: white;
  font-weight: 600;
  transition: all 0.3s ease;
}

.quick-actions .n-button:hover {
  background: rgba(255, 165, 0, 0.8);
  border-color: rgba(255, 165, 0, 0.9);
  color: white;
  transform: translateY(-2px);
}

.quick-actions .n-button {
  border-radius: 12px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 统计数据区域 */
.stats-section {
  margin: 0;
}

.stat-card {
  border-radius: 16px;
  overflow: hidden;
  background: white;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border: 1px solid rgba(0, 0, 0, 0.05);
  min-height: 160px;
  height: auto;
  display: flex;
  flex-direction: column;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.stat-content {
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  min-height: 0;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
  flex-shrink: 0;
}

.stat-icon.online {
  background: linear-gradient(135deg, #52c41a, #73d13d);
}

.stat-icon.warning {
  background: linear-gradient(135deg, #faad14, #ffc53d);
}

.stat-icon.success {
  background: linear-gradient(135deg, #1890ff, #40a9ff);
}

.stat-icon.info {
  background: linear-gradient(135deg, #722ed1, #9254de);
}

.stat-icon.maintenance {
  background: linear-gradient(135deg, #ff7a45, #ff9c6e);
}

.stat-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #262626;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #8c8c8c;
  margin-bottom: 4px;
}

.stat-trend {
  font-size: 12px;
  font-weight: 500;
}

.stat-trend.positive {
  color: #52c41a;
}

.stat-trend.negative {
  color: #ff4d4f;
}

.stat-trend.neutral {
  color: #8c8c8c;
}

/* 功能模块区域 */
.modules-section {
  margin: 0;
}

.section-title {
  font-size: 24px;
  font-weight: 700;
  color: #262626;
  margin: 0 0 24px 0;
  display: flex;
  align-items: center;
}

.module-card {
  border-radius: 16px;
  overflow: hidden;
  background: white;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  cursor: pointer;
  border: 1px solid rgba(0, 0, 0, 0.05);
  min-height: 220px;
  height: auto;
  display: flex;
  flex-direction: column;
}

.module-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.module-card.dashboard:hover {
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.08), rgba(64, 169, 255, 0.08));
}

.module-card.device:hover {
  background: linear-gradient(135deg, rgba(82, 196, 26, 0.08), rgba(115, 209, 61, 0.08));
}

.module-card.monitoring:hover {
  background: linear-gradient(135deg, rgba(245, 34, 45, 0.08), rgba(255, 77, 79, 0.08));
}

.module-card.maintenance:hover {
  background: linear-gradient(135deg, rgba(255, 122, 69, 0.08), rgba(255, 156, 110, 0.08));
}

.module-card.statistics:hover {
  background: linear-gradient(135deg, rgba(250, 140, 22, 0.08), rgba(255, 197, 61, 0.08));
}

.module-card.alarm:hover {
  background: linear-gradient(135deg, rgba(114, 46, 209, 0.08), rgba(146, 84, 222, 0.08));
}

.module-card.ai:hover {
  background: linear-gradient(135deg, rgba(19, 194, 194, 0.08), rgba(54, 207, 201, 0.08));
}

.module-card.data-model:hover {
  background: linear-gradient(135deg, rgba(47, 84, 235, 0.08), rgba(89, 126, 247, 0.08));
}

.module-card.workflow:hover {
  background: linear-gradient(135deg, rgba(235, 47, 150, 0.08), rgba(247, 89, 171, 0.08));
}

.module-card.system:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.08), rgba(118, 75, 162, 0.08));
}

.module-card.notification:hover {
  background: linear-gradient(135deg, rgba(250, 173, 20, 0.08), rgba(255, 214, 102, 0.08));
}

.module-header {
  padding: 20px 20px 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.module-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #667eea;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
}

.module-card.dashboard .module-icon {
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.1), rgba(64, 169, 255, 0.1));
  color: #1890ff;
}

.module-card.device .module-icon {
  background: linear-gradient(135deg, rgba(82, 196, 26, 0.1), rgba(115, 209, 61, 0.1));
  color: #52c41a;
}

.module-card.monitoring .module-icon {
  background: linear-gradient(135deg, rgba(245, 34, 45, 0.1), rgba(255, 77, 79, 0.1));
  color: #f5222d;
}

.module-card.maintenance .module-icon {
  background: linear-gradient(135deg, rgba(255, 122, 69, 0.1), rgba(255, 156, 110, 0.1));
  color: #ff7a45;
}

.module-card.statistics .module-icon {
  background: linear-gradient(135deg, rgba(250, 140, 22, 0.1), rgba(255, 197, 61, 0.1));
  color: #fa8c16;
}

.module-card.alarm .module-icon {
  background: linear-gradient(135deg, rgba(114, 46, 209, 0.1), rgba(146, 84, 222, 0.1));
  color: #722ed1;
}

.module-card.flow .module-icon {
  background: linear-gradient(135deg, rgba(235, 47, 150, 0.1), rgba(247, 89, 171, 0.1));
  color: #eb2f96;
}

.module-card.ai .module-icon {
  background: linear-gradient(135deg, rgba(19, 194, 194, 0.1), rgba(54, 207, 201, 0.1));
  color: #13c2c2;
}

.module-card.data-model .module-icon {
  background: linear-gradient(135deg, rgba(47, 84, 235, 0.1), rgba(89, 126, 247, 0.1));
  color: #2f54eb;
}

.module-card.workflow .module-icon {
  background: linear-gradient(135deg, rgba(235, 47, 150, 0.1), rgba(247, 89, 171, 0.1));
  color: #eb2f96;
}

.module-card.system .module-icon {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  color: #667eea;
}

.module-card.notification .module-icon {
  background: linear-gradient(135deg, rgba(250, 173, 20, 0.1), rgba(255, 214, 102, 0.1));
  color: #faad14;
}

.module-badge {
  background: rgba(0, 0, 0, 0.1);
  color: #666;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.module-card.dashboard .module-badge {
  background: linear-gradient(135deg, #1890ff, #40a9ff);
  color: white;
}

.module-card.device .module-badge {
  background: linear-gradient(135deg, #52c41a, #73d13d);
  color: white;
}

.module-card.monitoring .module-badge {
  background: linear-gradient(135deg, #f5222d, #ff4d4f);
  color: white;
}

.module-card.maintenance .module-badge {
  background: linear-gradient(135deg, #ff7a45, #ff9c6e);
  color: white;
}

.module-card.statistics .module-badge {
  background: linear-gradient(135deg, #fa8c16, #ffc53d);
  color: white;
}

.module-card.alarm .module-badge {
  background: linear-gradient(135deg, #722ed1, #9254de);
  color: white;
}

.module-card.ai .module-badge {
  background: linear-gradient(135deg, #13c2c2, #36cfc9);
  color: white;
}

.module-card.data-model .module-badge {
  background: linear-gradient(135deg, #2f54eb, #597ef7);
  color: white;
}

.module-card.workflow .module-badge {
  background: linear-gradient(135deg, #eb2f96, #f759ab);
  color: white;
}

.module-card.system .module-badge {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.module-card.notification .module-badge {
  background: linear-gradient(135deg, #faad14, #ffd666);
  color: white;
}

.module-content {
  padding: 20px 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.module-title {
  font-size: 18px;
  font-weight: 700;
  color: #262626;
  margin: 0 0 12px 0;
  line-height: 1.3;
}

.module-description {
  font-size: 14px;
  color: #8c8c8c;
  line-height: 1.6;
  margin: 0;
  word-wrap: break-word;
}

.module-footer {
  padding: 0 20px 20px 20px;
  margin-top: auto;
}

.module-action {
  display: block;
  width: 100%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  font-size: 14px;
  font-weight: 600;
  padding: 12px 16px;
  border-radius: 8px;
  transition: all 0.3s ease;
  text-decoration: none;
  cursor: pointer;
  text-align: center;
  box-sizing: border-box;
}

.module-card.dashboard .module-action {
  background: linear-gradient(135deg, #1890ff, #40a9ff);
}

.module-card.device .module-action {
  background: linear-gradient(135deg, #52c41a, #73d13d);
}

.module-card.monitoring .module-action {
  background: linear-gradient(135deg, #f5222d, #ff4d4f);
}

.module-card.maintenance .module-action {
  background: linear-gradient(135deg, #ff7a45, #ff9c6e);
}

.module-card.statistics .module-action {
  background: linear-gradient(135deg, #fa8c16, #ffc53d);
}

.module-card.alarm .module-action {
  background: linear-gradient(135deg, #722ed1, #9254de);
}

.module-card.ai .module-action {
  background: linear-gradient(135deg, #13c2c2, #36cfc9);
}

.module-card.data-model .module-action {
  background: linear-gradient(135deg, #2f54eb, #597ef7);
}

.module-card.workflow .module-action {
  background: linear-gradient(135deg, #eb2f96, #f759ab);
}

.module-card.system .module-action {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.module-card.notification .module-action {
  background: linear-gradient(135deg, #faad14, #ffd666);
}

.module-card:hover .module-action {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .stat-card {
    min-height: 150px;
    height: auto;
  }

  .stat-content {
    padding: 20px;
    gap: 14px;
  }

  .stat-value {
    font-size: 26px;
  }

  .stat-label {
    font-size: 13px;
  }
}

@media (max-width: 768px) {
  .workbench-container {
    padding: 16px;
    gap: 16px;
  }

  .welcome-content {
    padding: 24px;
    flex-direction: column;
    text-align: center;
  }

  .user-details h1.welcome-title {
    font-size: 24px;
  }

  .quick-actions {
    justify-content: center;
  }

  .stat-card {
    min-height: 140px;
    height: auto;
  }

  .stat-content {
    padding: 20px 16px;
    gap: 12px;
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    font-size: 20px;
  }

  .stat-value {
    font-size: 24px;
  }

  .stat-label {
    font-size: 13px;
  }

  .stat-trend {
    font-size: 11px;
  }

  .module-card {
    height: auto;
    min-height: 180px;
  }

  .module-content {
    padding: 16px 20px;
  }

  .module-title {
    font-size: 16px;
  }

  .module-description {
    font-size: 13px;
  }

  .section-title {
    font-size: 20px;
  }
}
/* 暗黑模式支持 */
.dark .workbench-container {
  background: var(--background);
  color: var(--foreground);
}

.dark .welcome-card {
  background: var(--card);
  color: var(--card-foreground);
  border-color: var(--border);
}

.dark .welcome-content {
  color: var(--card-foreground);
}

.dark .user-details h1.welcome-title {
  color: var(--foreground);
}

.dark .user-details .welcome-subtitle {
  color: var(--muted-foreground);
}

.dark .section-title {
  color: var(--foreground);
}

.dark .stat-card {
  background: var(--card);
  border-color: var(--border);
}

.dark .stat-content {
  color: var(--card-foreground);
}

.dark .stat-value {
  color: var(--foreground);
}

.dark .stat-label {
  color: var(--muted-foreground);
}

.dark .stat-trend {
  color: var(--muted-foreground);
}

.dark .module-card {
  background: var(--card);
  border-color: var(--border);
}

.dark .module-card:hover {
  border-color: var(--ring);
  box-shadow: 0 4px 12px rgba(255, 255, 255, 0.1);
}

.dark .module-content {
  color: var(--card-foreground);
}

.dark .module-title {
  color: var(--foreground);
}

.dark .module-description {
  color: var(--muted-foreground);
}

.dark .module-badge {
  background: var(--muted);
  color: var(--muted-foreground);
}

/* 暗黑模式下的卡片图标背景调整 */
.dark .module-card.dashboard .module-icon {
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.2), rgba(64, 169, 255, 0.2));
}

.dark .module-card.device .module-icon {
  background: linear-gradient(135deg, rgba(82, 196, 26, 0.2), rgba(115, 209, 61, 0.2));
}

.dark .module-card.monitoring .module-icon {
  background: linear-gradient(135deg, rgba(245, 34, 45, 0.2), rgba(255, 77, 79, 0.2));
}

.dark .module-card.statistics .module-icon {
  background: linear-gradient(135deg, rgba(250, 140, 22, 0.2), rgba(255, 197, 61, 0.2));
}

.dark .module-card.alarm .module-icon {
  background: linear-gradient(135deg, rgba(114, 46, 209, 0.2), rgba(146, 84, 222, 0.2));
}

.dark .module-card.workflow .module-icon {
  background: linear-gradient(135deg, rgba(235, 47, 150, 0.2), rgba(247, 89, 171, 0.2));
}

.dark .module-card.ai .module-icon {
  background: linear-gradient(135deg, rgba(19, 194, 194, 0.2), rgba(54, 207, 201, 0.2));
}

.dark .module-card.data-model .module-icon {
  background: linear-gradient(135deg, rgba(47, 84, 235, 0.2), rgba(89, 126, 247, 0.2));
}

.dark .module-card.system .module-icon {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
}
</style>
