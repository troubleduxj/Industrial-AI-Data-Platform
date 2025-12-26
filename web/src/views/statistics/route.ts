import type { RouteRecordRaw } from 'vue-router'

const Layout = () => import('@/layout/index.vue')

const route: RouteRecordRaw = {
  name: 'Statistics',
  path: '/statistics',
  component: Layout,
  redirect: '/statistics/online-rate',
  meta: {
    title: '数据统计',
    icon: 'material-symbols:analytics',
    order: 4,
  },
  children: [
    {
      name: 'OnlineRate',
      path: '/statistics/online-rate',
      component: () => import('./online-rate/index.vue'),
      meta: {
        title: '在线率',
        icon: 'material-symbols:wifi',
        keepAlive: true,
      },
    },
    {
      name: 'WeldTime',
      path: '/statistics/weld-time',
      component: () => import('./weld-time/index.vue'),
      meta: {
        title: '焊接时长',
        icon: 'material-symbols:schedule',
        keepAlive: true,
      },
    },
    {
      name: 'WeldingReport',
      path: '/statistics/welding-report',
      component: () => import('./welding-report/index.vue'),
      meta: {
        title: '焊机日报',
        icon: 'material-symbols:description',
        keepAlive: true,
      },
    },
    {
      name: 'WeldRecord',
      path: '/statistics/weld-record',
      component: () => import('./weld-record/index.vue'),
      meta: {
        title: '焊接记录',
        icon: 'material-symbols:history',
        keepAlive: true,
      },
    },
  ],
}

export default route

