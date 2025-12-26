import type { RouteRecordRaw } from 'vue-router'

const Layout = () => import('@/layout/index.vue')

const route: RouteRecordRaw = {
  path: '/device',
  name: 'Device',
  component: Layout,
  redirect: '/device/baseinfo',
  meta: {
    title: '设备管理',
    icon: 'mdi-air-humidifier',
    requiresAuth: true,
  },
  children: [
    {
      path: 'baseinfo',
      name: 'DeviceBaseinfo',
      component: () => import('./baseinfo/index.vue'),
      meta: {
        title: '设备信息管理',
        icon: 'mdi-content-save-cog-outline',
        requiresAuth: true,
        keepAlive: true,
      },
    },
    {
      path: 'type',
      name: 'DeviceType',
      component: () => import('./type/index.vue'),
      meta: {
        title: '设备分类管理',
        icon: 'material-symbols:category',
        requiresAuth: true,
        keepAlive: true,
      },
    },
  ],
}

export default route

