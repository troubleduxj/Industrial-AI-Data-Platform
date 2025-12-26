import type { RouteRecordRaw } from 'vue-router'

const Layout = () => import('@/layout/index.vue')

const route: RouteRecordRaw = {
  path: '/device-maintenance',
  name: 'DeviceMaintenance',
  component: Layout,
  meta: {
    title: '设备维护',
    icon: 'material-symbols:build',
    requiresAuth: true,
  },
  children: [
    {
      path: '',
      name: 'DeviceMaintenanceIndex',
      component: () => import('./index.vue'),
      meta: {
        title: '设备维护管理',
        icon: 'material-symbols:build',
        requiresAuth: true,
      },
    },
    {
      path: 'maintenance-dashboard',
      name: 'DeviceMaintenanceDashboard',
      component: () => import('./maintenance-dashboard/index.vue'),
      meta: {
        title: '维护看板',
        icon: 'material-symbols:dashboard',
        requiresAuth: true,
        keepAlive: true,
      },
    },
    {
      path: 'repair-records',
      name: 'DeviceRepairRecords',
      component: () => import('./repair-records/index.vue'),
      meta: {
        title: '维修记录',
        icon: 'material-symbols:build-circle',
        requiresAuth: true,
        keepAlive: true,
      },
    },
    // 后续可扩展其他维护功能
    // {
    //   path: '/device-maintenance/maintenance-plans',
    //   name: 'DeviceMaintenancePlans',
    //   component: () => import('./maintenance-plans/index.vue'),
    //   meta: {
    //     title: '维护计划',
    //     icon: 'material-symbols:schedule',
    //     requiresAuth: true,
    //     keepAlive: true,
    //   },
    // },
  ],
}

export default route

