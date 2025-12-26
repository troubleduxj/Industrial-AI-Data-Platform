<template>
  <div class="module-navigation">
    <CommonPage>
      <!-- 模块头部信息 -->
      <div class="module-header">
        <h1 class="module-title">{{ moduleConfig.title }}</h1>
        <p class="module-description">{{ moduleConfig.description }}</p>
      </div>

      <!-- 子模块导航卡片 -->
      <div v-if="availableSubModules.length > 0" class="module-cards">
        <div
          v-for="subModule in availableSubModules"
          :key="subModule.path"
          class="module-card"
          :class="{ 'module-card--disabled': subModule.disabled }"
          @click="navigateToSubModule(subModule)"
        >
          <div class="card-icon">
            <TheIcon :icon="subModule.icon" :size="48" />
          </div>
          <div class="card-content">
            <h3 class="card-title">{{ subModule.title }}</h3>
            <p class="card-description">{{ subModule.description }}</p>
            <div v-if="subModule.badge" class="card-badge">
              <n-tag :type="subModule.badge.type" size="small">
                {{ subModule.badge.text }}
              </n-tag>
            </div>
          </div>
          <div class="card-arrow">
            <TheIcon icon="material-symbols:arrow-forward-ios" :size="20" />
          </div>
        </div>
      </div>

      <!-- 无权限时的空状态 -->
      <div v-else class="empty-state">
        <n-empty description="暂无可用功能" size="large" style="margin: 60px 0">
          <template #icon>
            <TheIcon :icon="moduleConfig.icon" :size="48" style="color: #d9d9d9" />
          </template>
          <template #extra>
            <div class="empty-state-content">
              <p style="color: #666; margin: 16px 0; font-size: 16px">
                您当前没有{{ moduleConfig.title }}的任何子功能权限
              </p>
              <p style="color: #999; margin: 8px 0; font-size: 14px">
                请联系系统管理员为您分配相应的功能权限
              </p>
              <div style="margin-top: 24px">
                <n-button type="primary" @click="$router.push('/workbench')">
                  <TheIcon icon="material-symbols:home" :size="16" style="margin-right: 4px" />
                  返回工作台
                </n-button>
              </div>
            </div>
          </template>
        </n-empty>
      </div>
    </CommonPage>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NEmpty, NTag, NButton } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import { usePermissionStore, useUserStore } from '@/store'

const props = defineProps({
  // 模块配置
  moduleConfig: {
    type: Object,
    required: true,
    validator: (config) => {
      return config.title && config.description && config.icon && config.basePath
    },
  },
  // 子模块配置
  subModules: {
    type: Array,
    default: () => [],
  },
  // 是否自动从路由生成子模块
  autoGenerateFromRoutes: {
    type: Boolean,
    default: true,
  },
})

const router = useRouter()
const route = useRoute()
const permissionStore = usePermissionStore()
const userStore = useUserStore()

// 权限检查方法
const hasPermission = (permission) => {
  // 超级用户拥有所有权限
  if (userStore.isSuperUser) {
    return true
  }

  // 检查菜单权限
  if (!permissionStore.menus || permissionStore.menus.length === 0) {
    return false
  }

  // 递归检查菜单权限
  const checkMenuAccess = (menus, targetPermission) => {
    for (const menu of menus) {
      // 多种匹配方式
      if (
        menu.path === targetPermission ||
        menu.component === targetPermission ||
        (menu.name || menu.title || '').toLowerCase().includes(targetPermission.toLowerCase()) ||
        menu.path?.includes(targetPermission) ||
        targetPermission.includes(menu.path)
      ) {
        return true
      }

      // 递归检查子菜单
      if (menu.children && menu.children.length > 0) {
        if (checkMenuAccess(menu.children, targetPermission)) {
          return true
        }
      }
    }
    return false
  }

  return checkMenuAccess(permissionStore.menus, permission)
}

// 从路由自动生成子模块配置
const generateSubModulesFromRoutes = () => {
  if (!props.autoGenerateFromRoutes) {
    return props.subModules
  }

  // 获取当前模块的所有子路由
  const currentRoute = router.getRoutes().find((r) => r.path === props.moduleConfig.basePath)
  if (!currentRoute || !currentRoute.children) {
    return props.subModules
  }

  // 预定义的子模块配置映射
  const subModuleConfigs = {
    // 设备维护模块
    'repair-records': {
      title: '维修记录',
      description: '管理设备维修记录，支持故障报修、维修过程跟踪和维修历史查询',
      icon: 'material-symbols:build-circle',
      permission: 'repair-records',
    },
    'maintenance-dashboard': {
      title: '维护看板',
      description: '设备维护状态总览，实时监控设备健康度和维护任务',
      icon: 'material-symbols:dashboard',
      permission: 'maintenance-dashboard',
    },

    // 设备管理模块
    baseinfo: {
      title: '设备信息管理',
      description: '管理设备基本信息，包括设备档案、参数配置等',
      icon: 'material-symbols:info',
      permission: 'baseinfo',
    },
    type: {
      title: '设备分类管理',
      description: '管理设备类型和分类，定义设备属性模板',
      icon: 'material-symbols:category',
      permission: 'type',
    },

    // 设备监测模块
    monitor: {
      title: '设备实时监测',
      description: '实时监控设备运行状态和关键参数',
      icon: 'material-symbols:monitor',
      permission: 'monitor',
    },
    history: {
      title: '历史数据查询',
      description: '查询和分析设备历史运行数据',
      icon: 'material-symbols:history',
      permission: 'history',
    },

    // 数据统计模块
    'online-rate': {
      title: '在线率统计',
      description: '统计设备在线率和可用性指标',
      icon: 'material-symbols:signal-wifi-4-bar',
      permission: 'online-rate',
    },
    'weld-time': {
      title: '焊接时长统计',
      description: '统计焊机设备的焊接时长和效率',
      icon: 'material-symbols:timer',
      permission: 'weld-time',
    },
    'welding-report': {
      title: '焊机日报',
      description: '生成焊机设备的日常运行报表',
      icon: 'material-symbols:description',
      permission: 'welding-report',
    },
    'weld-record': {
      title: '焊接记录',
      description: '查看和管理焊接作业记录',
      icon: 'material-symbols:list-alt',
      permission: 'weld-record',
    },

    // 告警中心模块
    'alarm-info': {
      title: '报警信息',
      description: '查看和处理设备报警信息',
      icon: 'material-symbols:warning',
      permission: 'alarm-info',
    },
    'alarm-analysis': {
      title: '报警分析',
      description: '分析报警趋势和故障模式',
      icon: 'material-symbols:analytics',
      permission: 'alarm-analysis',
    },

    // 监测看板模块
    'dashboard-weld': {
      title: '焊机监测看板',
      description: '焊机设备的实时监测看板',
      icon: 'material-symbols:dashboard',
      permission: 'dashboard-weld',
    },
    'dashboard-test': {
      title: '测试看板',
      description: '系统测试和调试看板',
      icon: 'material-symbols:bug-report',
      permission: 'dashboard-test',
    },
    'dashboard-cut': {
      title: '切割机监测看板',
      description: '切割机设备的实时监测看板',
      icon: 'material-symbols:content-cut',
      permission: 'dashboard-cut',
    },

    // 系统管理模块
    user: {
      title: '用户管理',
      description: '管理系统用户账号和基本信息',
      icon: 'material-symbols:person',
      permission: 'user',
    },
    role: {
      title: '角色管理',
      description: '管理用户角色和权限分配',
      icon: 'material-symbols:admin-panel-settings',
      permission: 'role',
    },
    menu: {
      title: '菜单管理',
      description: '管理系统菜单结构和权限',
      icon: 'material-symbols:menu',
      permission: 'menu',
    },
    api: {
      title: 'API管理',
      description: '管理系统API接口权限',
      icon: 'material-symbols:api',
      permission: 'api',
    },
    dept: {
      title: '部门管理',
      description: '管理组织架构和部门信息',
      icon: 'material-symbols:corporate-fare',
      permission: 'dept',
    },
    auditlog: {
      title: '审计日志',
      description: '查看系统操作审计日志',
      icon: 'material-symbols:history-edu',
      permission: 'auditlog',
    },
  }

  // 生成子模块列表
  const generatedSubModules = currentRoute.children
    .filter((child) => child.path && child.path !== '') // 过滤空路径
    .map((child) => {
      const pathKey = child.path
      const config = subModuleConfigs[pathKey] || {}

      return {
        path: child.path,
        fullPath: `${props.moduleConfig.basePath}/${child.path}`,
        title: config.title || child.meta?.title || child.name || pathKey,
        description:
          config.description || child.meta?.description || `${config.title || pathKey}功能模块`,
        icon: config.icon || child.meta?.icon || 'material-symbols:extension',
        permission: config.permission || pathKey,
        disabled: config.disabled || false,
        badge: config.badge || null,
      }
    })

  // 合并手动配置的子模块
  return [...generatedSubModules, ...props.subModules]
}

// 获取有权限的子模块
const availableSubModules = computed(() => {
  const allSubModules = generateSubModulesFromRoutes()

  return allSubModules.filter((subModule) => {
    // 检查权限
    const permissionChecks = [
      subModule.permission,
      subModule.path,
      subModule.fullPath,
      `${props.moduleConfig.basePath}/${subModule.path}`,
      subModule.title,
    ]

    return permissionChecks.some((permission) => hasPermission(permission))
  })
})

// 导航到子模块
const navigateToSubModule = (subModule) => {
  if (subModule.disabled) {
    return
  }

  const targetPath = subModule.fullPath || `${props.moduleConfig.basePath}/${subModule.path}`
  router.push(targetPath)
}

// 调试信息
onMounted(() => {
  console.log('ModuleNavigation 组件加载:', {
    moduleConfig: props.moduleConfig,
    availableSubModules: availableSubModules.value,
    userPermissions: permissionStore.menus?.length || 0,
  })
})
</script>

<style scoped>
.module-navigation {
  padding: 20px;
}

.module-header {
  text-align: center;
  margin-bottom: 40px;
}

.module-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--n-title-text-color);
  margin: 0 0 12px 0;
}

.module-description {
  font-size: 16px;
  color: var(--n-text-color-2);
  margin: 0;
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.6;
}

.module-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.module-card {
  display: flex;
  align-items: center;
  padding: 24px;
  background: var(--n-color);
  border: 1px solid var(--n-border-color);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.module-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px var(--n-box-shadow-color);
  border-color: var(--n-primary-color);
}

.module-card--disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.module-card--disabled:hover {
  transform: none;
  box-shadow: none;
  border-color: var(--n-border-color);
}

.card-icon {
  flex-shrink: 0;
  margin-right: 20px;
  color: var(--n-primary-color);
}

.card-content {
  flex: 1;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--n-title-text-color);
  margin: 0 0 8px 0;
}

.card-description {
  font-size: 14px;
  color: var(--n-text-color-2);
  margin: 0 0 8px 0;
  line-height: 1.5;
}

.card-badge {
  margin-top: 8px;
}

.card-arrow {
  flex-shrink: 0;
  margin-left: 16px;
  color: var(--n-text-color-3);
}

.empty-state {
  text-align: center;
  margin-top: 40px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .module-cards {
    grid-template-columns: 1fr;
  }

  .module-card {
    padding: 20px;
  }

  .card-icon {
    margin-right: 16px;
  }
}
</style>
