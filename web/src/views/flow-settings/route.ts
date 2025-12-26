import type { RouteRecordRaw } from 'vue-router'

const Layout = () => import('@/layout/index.vue')

const route: RouteRecordRaw = {
  name: 'FlowSettings',
  path: '/flow-settings',
  component: Layout,
  redirect: '/flow-settings/workflow-design',
  meta: {
    title: '流程设置',
    icon: 'material-symbols:workflow',
    order: 5,
  },
  children: [
    {
      name: 'WorkflowDesign',
      path: 'workflow-design',
      component: () => import('./workflow-design/index.vue'),
      meta: {
        title: '工作流设计',
        icon: 'material-symbols:design-services',
        keepAlive: true,
      },
    },
    {
      name: 'WorkflowManage',
      path: 'workflow-manage',
      component: () => import('./workflow-manage/index.vue'),
      meta: {
        title: '工作流管理',
        icon: 'material-symbols:manage-accounts',
        keepAlive: true,
      },
    },
  ],
}

export default route

