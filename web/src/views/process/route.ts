import type { RouteRecordRaw } from 'vue-router'

/**
 * 流程管理模块路由配置
 * @description 定义流程相关页面的路由信息
 */

const Layout = () => import('@/layout/index.vue')

const route: RouteRecordRaw = {
  path: '/process',
  name: 'Process',
  component: Layout,
  redirect: '/process/process-card',
  meta: {
    title: '流程管理',
    icon: 'ep:operation',
    rank: 4,
  },
  children: [
    {
      path: '/process/process-card',
      name: 'ProcessCard',
      component: () => import('./process-card/index.vue'),
      meta: {
        title: '工艺卡片',
        icon: 'ep:document',
        showParent: true,
      },
    },
  ],
}

export default route

