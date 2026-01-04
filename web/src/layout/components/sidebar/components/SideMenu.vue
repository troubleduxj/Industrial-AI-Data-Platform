<template>
  <n-menu
    ref="menu"
    class="side-menu"
    accordion
    :indent="18"
    :collapsed-icon-size="22"
    :collapsed-width="64"
    :options="menuOptions"
    :value="activeKey"
    @update:value="handleMenuSelect"
  />
</template>

<script setup>
import { usePermissionStore, useAppStore } from '@/store'
import { renderCustomIcon, renderIcon, isExternal } from '@/utils'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const curRoute = useRoute()
const permissionStore = usePermissionStore()
const appStore = useAppStore()
const { t, te } = useI18n()

const activeKey = computed(() => curRoute.meta?.activeMenu || curRoute.name)

const menuOptions = computed(() => {
  return permissionStore.menus.map((item) => getMenuItem(item)).sort((a, b) => a.order - b.order)
})

const menu = ref(null)
watch(curRoute, async () => {
  await nextTick()
  menu.value?.showOption()
})

function resolvePath(basePath, path) {
  if (isExternal(path)) return path
  return (
    '/' +
    [basePath, path]
      .filter((path) => !!path && path !== '/')
      .map((path) => path.replace(/(^\/)|(\/$)/g, ''))
      .join('/')
  )
}

function getMenuItem(route, basePath = '') {
  let menuItem = {
    label: getTitle(route),
    key: route.name,
    path: resolvePath(basePath, route.path),
    icon: getIcon(route.meta),
    order: route.meta?.order || 0,
  }

  const visibleChildren = route.children
    ? route.children.filter((item) => item.name && !item.meta?.isHidden)
    : []

  if (!visibleChildren.length) return menuItem

  if (visibleChildren.length === 1) {
    // 单个子路由处理
    const singleRoute = visibleChildren[0]
    menuItem = {
      ...menuItem,
      label: getTitle(singleRoute),
      key: singleRoute.name,
      path: resolvePath(menuItem.path, singleRoute.path),
      icon: getIcon(singleRoute.meta),
    }
    const visibleItems = singleRoute.children
      ? singleRoute.children.filter((item) => item.name && !item.meta?.isHidden)
      : []

    if (visibleItems.length === 1) {
      menuItem = getMenuItem(visibleItems[0], menuItem.path)
    } else if (visibleItems.length > 1) {
      menuItem.children = visibleItems
        .map((item) => getMenuItem(item, menuItem.path))
        .sort((a, b) => a.order - b.order)
    }
  } else {
    menuItem.children = visibleChildren
      .map((item) => getMenuItem(item, menuItem.path))
      .sort((a, b) => a.order - b.order)
  }
  return menuItem
}

const segmentMap = {
  'system': 'menu.system.title',
  'user': 'menu.user.title',
  'role': 'menu.role.title',
  'menu': 'menu.menu.title',
  'dept': 'menu.dept.title',
  'api': 'menu.api.title',
  'dict': 'menu.dict.title',
  'device': 'menu.device_management.title',
  'device-monitor': 'menu.device_monitoring.title',
  'ai-monitor': 'menu.ai_monitoring.title',
  'flow-settings': 'menu.workflow.title',
  'data-model': 'menu.data_model.title',
  'statistics': 'menu.statistics.title',
  'alarm': 'menu.alarm.title',
   'notification': 'menu.notification.title',
   'users': 'menu.user.title',
   'roles': 'menu.role.title',
   'logs': 'menu.auditlog.title',
   'alerts': 'menu.alarm.title',
   'monitoring': 'menu.device_monitoring.title',
   'departments': 'menu.dept.title',
   'groups': 'menu.dept.title',
   'permissions': 'menu.role.title',
 }
 
 const nameMap = {
  'System': 'menu.system.title',
  'User': 'menu.user.title',
  'Role': 'menu.role.title',
  'Menu': 'menu.menu.title',
  'Dept': 'menu.dept.title',
  'Api': 'menu.api.title',
  'Dict': 'menu.dict.title',
  'Device': 'menu.device_management.title',
  'DeviceManagement': 'menu.device_management.title',
  'DeviceMonitor': 'menu.device_monitoring.title',
  'DeviceMonitoring': 'menu.device_monitoring.title',
  'Workflow': 'menu.workflow.title',
  'FlowSettings': 'menu.workflow.title',
  'AiMonitor': 'menu.ai_monitoring.title',
  'DataModel': 'menu.data_model.title',
  'Statistics': 'menu.statistics.title',
  'BaseInfo': 'menu.baseinfo.title',
  'Type': 'menu.type.title',
  'Monitor': 'menu.monitor.title',
  'History': 'menu.history.title',
  'Alarm': 'menu.alarm.title',
  'Notification': 'menu.notification.title',
  'Reports': 'menu.reports.title',
  'Dashboard': 'menu.dashboard.title',
  'System Management': 'menu.system.title',
  'User Management': 'menu.user.title',
  'Role Management': 'menu.role.title',
  'Menu Management': 'menu.menu.title',
  'Department Management': 'menu.dept.title',
  'API Management': 'menu.api.title',
  'Dict Management': 'menu.dict.title',
  'Device Management': 'menu.device_management.title',
  'Device Monitoring': 'menu.device_monitoring.title',
  'Data Model': 'menu.data_model.title',
  'Flow Orchestration': 'menu.workflow.title',
  'Alarm Center': 'menu.alarm.title',
  'Report Center': 'menu.reports.title',
   'Logs': 'menu.auditlog.title',
   'Alerts': 'menu.alarm.title',
   'Monitoring': 'menu.device_monitoring.title',
   'Departments': 'menu.dept.title',
   'Groups': 'menu.dept.title',
   'Permissions': 'menu.role.title',
   
   // V5 High Level Maps
   'Overview': 'menu.overview.title',
   'Assets': 'menu.assets.title',
   'Signals': 'menu.signals.title',
   'Data Ingestion': 'menu.data_ingestion.title',
   'Data Flow': 'menu.data_flow.title',
   'Analytics & AI': 'menu.analytics_ai.title',
   'Alerts & Rules': 'menu.alerts_rules.title',
   'Dashboards & Apps': 'menu.dashboards_apps.title',
   'Data Management': 'menu.data_management.title',
   'Security & Access': 'menu.security_access.title',
   'Platform Admin': 'menu.platform_admin.title',
   
   // V5 Detailed Items
   'Registry': 'menu.asset_registry.title',
   'Hierarchy': 'menu.asset_hierarchy.title',
   'Maintenance': 'menu.asset_maintenance.title',
   'Tag Manage': 'menu.tag_manage.title',
   'Tag Management': 'menu.tag_manage.title',
   'Real_time Data': 'menu.real_time_data.title',
   'Real-time Data': 'menu.real_time_data.title',
   'Real Time Data': 'menu.real_time_data.title',
   'Computed Tags': 'menu.computed_tags.title',
   'Pipelines': 'menu.pipelines.title',
   'Quality Rules': 'menu.quality_rules.title',
   'Flow Designer': 'menu.flow_designer.title',
   'Stream Process': 'menu.stream_process.title',
   'Stream Processing': 'menu.stream_processing.title',
   'Data Routing': 'menu.data_routing.title',
   'Model Registry': 'menu.model_registry.title',
   'Training Jobs': 'menu.training_jobs.title',
   'Inference Services': 'menu.inference_services.title',
   'Notebooks': 'menu.notebooks.title',
   'Alert Definitions': 'menu.alert_definitions.title',
   'Notify Channels': 'menu.notify_channels.title',
   'Incident Management': 'menu.incident_management.title',
   'On-call Shedules': 'menu.on_call_schedules.title',
   'On-call Schedules': 'menu.on_call_schedules.title',
   'Dashbords': 'menu.dashboards.title',
   'Dashboards': 'menu.dashboards.title',
   'App Builder': 'menu.app_builder.title',
   'Industrial Apps': 'menu.industrial_apps.title',
   'Schema Registry': 'menu.schema_registry.title',
   'Metadata Store': 'menu.metadata_store.title',
   'Storage Polices': 'menu.storage_policies.title',
   'Storage Policies': 'menu.storage_policies.title',
   
   // V5 Adapter Names
   'AssetExplorer': 'menu.asset_explorer.title',
   'AssetTypes': 'menu.asset_types.title',
   'AssetModels': 'menu.asset_models.title',
   'AssetRelations': 'menu.asset_relations.title',
   'DigitalTwin': 'menu.digital_twin.title',
   'MaintenanceApp': 'menu.maintenance_app.title',
 }
 
 function getTitle(route) {
  // 1. Try route.meta.title as a key (if it is a key)
  if (route.meta?.title && te(route.meta.title)) return t(route.meta.title)
  
  // 2. Try generated key from name: menu.<name>.title
  if (route.name) {
    // 2.1 Try name map
    if (nameMap[route.name] && te(nameMap[route.name])) return t(nameMap[route.name])
    
    // 2.2 Try generated key
    const key = `menu.${route.name.toLowerCase()}.title`
    if (te(key)) return t(key)
  }

  // 3. Try generated key from path
  if (route.path) {
    // 过滤掉 index 和空段
    const segments = route.path.split('/').filter(s => s && s.toLowerCase() !== 'index')
    
    if (segments.length > 0) {
      const lastSegment = segments[segments.length - 1].toLowerCase()
      
      // 3.1 尝试映射表
      if (segmentMap[lastSegment] && te(segmentMap[lastSegment])) {
        return t(segmentMap[lastSegment])
      }

      // 3.2 尝试替换连字符为下划线 (e.g. data-model -> data_model)
      const snakeSegment = lastSegment.replace(/-/g, '_')
      const snakeKey = `menu.${snakeSegment}.title`
      if (te(snakeKey)) return t(snakeKey)

      // 3.3 尝试原始片段
      const lastKey = `menu.${lastSegment}.title`
      if (te(lastKey)) return t(lastKey)
    }
  }
  
  // 4. Fallback with Debug Log
  const fallbackTitle = route.meta?.title || route.name
  console.warn('SideMenu Translation Failed:', {
    name: route.name,
    path: route.path,
    metaTitle: route.meta?.title,
    fallback: fallbackTitle
  })
  return fallbackTitle
}

function getIcon(meta) {
  if (meta?.customIcon) return renderCustomIcon(meta.customIcon, { size: 18 })
  if (meta?.icon) return renderIcon(meta.icon, { size: 18 })
  return null
}

function handleMenuSelect(key, item) {
  if (isExternal(item.path)) {
    window.open(item.path)
  } else {
    if (item.path === curRoute.path) {
      appStore.reloadPage()
    } else {
      router.push(item.path)
    }
  }
}
</script>

<style lang="scss">
/* n-menu CSS变量覆盖 */
:deep(.n-menu) {
  --n-item-text-color-child-active-hover: var(--primary-color) !important;
  --n-item-text-color-child-active: var(--primary-color) !important;
  --n-item-icon-color-child-active-hover: var(--primary-color) !important;
  --n-item-icon-color-child-active: var(--primary-color) !important;
  --n-arrow-color-child-active-hover: var(--primary-color) !important;
  --n-arrow-color-child-active: var(--primary-color) !important;
}

.side-menu:not(.n-menu--collapsed) {
  .n-menu-item-content {
    margin: 4px 12px;
    border-radius: 8px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;

    &::before {
      left: 0;
      right: 0;
      border-radius: 8px;
      border-left: none;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    // 激活状态：卡片式效果，背景色为主题色，文字为白色，轻微放大
    &.n-menu-item-content--selected {
      transform: scale(1.05);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);

      &::before {
        background: var(--primary-color) !important;
      }

      .n-menu-item-content__icon {
        color: white !important;
      }

      .n-menu-item-content-header {
        color: white !important;
        font-weight: 500;
      }

      // 激活状态悬停时保持白色文字
      &:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);

        &::before {
          background: var(--primary-color) !important;
        }

        .n-menu-item-content__icon {
          color: white !important;
        }

        .n-menu-item-content-header {
          color: white !important;
        }
      }
    }

    // 悬停状态：卡片式效果，背景色为主题色*10%，文字为主题色，轻微放大
    &:hover:not(.n-menu-item-content--selected) {
      transform: scale(1.05);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

      &::before {
        background: color-mix(in srgb, var(--primary-color) 10%, transparent) !important;
      }

      .n-menu-item-content__icon {
        color: var(--primary-color) !important;
      }

      .n-menu-item-content-header {
        color: var(--primary-color) !important;
      }
    }
  }

  // 子菜单激活时父菜单样式
  .n-submenu.n-submenu--child-active > .n-menu-item-content {
    .n-menu-item-content__icon,
    .n-menu-item-content-header,
    .n-submenu-arrow {
      color: var(--primary-color) !important;
    }
  }

  // 子菜单项样式
  .n-submenu-children .n-menu-item-content {
    margin: 2px 12px 2px 18px;
    border-radius: 6px;

    &.n-menu-item-content--selected {
      transform: scale(1.03);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

      &::before {
        background: var(--primary-color) !important;
      }

      .n-menu-item-content__icon {
        color: white !important;
      }

      .n-menu-item-content-header {
        color: white !important;
        font-weight: 500;
      }
    }

    &:hover:not(.n-menu-item-content--selected) {
      transform: scale(1.03);
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);

      &::before {
        background: color-mix(in srgb, var(--primary-color) 8%, transparent) !important;
      }

      .n-menu-item-content__icon {
        color: var(--primary-color) !important;
      }

      .n-menu-item-content-header {
        color: var(--primary-color) !important;
      }
    }
  }
}

// 收起状态的菜单样式
.side-menu.n-menu--collapsed {
  .n-menu-item-content {
    margin: 4px 8px;
    border-radius: 8px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;

    // 确保图标容器居中
    .n-menu-item-content__icon {
      display: flex !important;
      justify-content: center !important;
      align-items: center !important;
      width: 100% !important;
      margin: 0 !important;
      padding: 0 !important;
      position: relative !important;
      left: 0 !important;
      right: 0 !important;
      text-align: center !important;
    }

    // 确保图标元素本身也居中
    .n-menu-item-content__icon > * {
      margin: 0 auto !important;
      display: block !important;
    }

    &::before {
      left: 0;
      right: 0;
      border-radius: 8px;
      border-left: none;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    // 激活状态：保持主题色背景，白色图标，圆角效果
    &.n-menu-item-content--selected {
      &::before {
        background: var(--primary-color) !important;
      }

      .n-menu-item-content__icon {
        color: white !important;
      }

      // 激活状态悬停时保持样式
      &:hover {
        &::before {
          background: var(--primary-color) !important;
        }

        .n-menu-item-content__icon {
          color: white !important;
        }
      }
    }

    // 悬停状态：背景色为主题色*15%，图标为主题色
    &:hover:not(.n-menu-item-content--selected) {
      &::before {
        background: color-mix(in srgb, var(--primary-color) 15%, transparent) !important;
      }

      .n-menu-item-content__icon {
        color: var(--primary-color) !important;
      }
    }
  }
}
</style>
