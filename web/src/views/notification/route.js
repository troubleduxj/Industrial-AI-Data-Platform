
const Layout = () => import('@/layout/index.vue')

export default {
  path: '/notification-center',
  component: Layout,
  redirect: '/notification-center/index',
  meta: {
    title: '通知中心',
    isHidden: true,
  },
  children: [
    {
      name: 'NotificationCenter',
      path: '', // Default child route
      component: () => import('./center/index.vue'),
      meta: {
        title: '通知中心',
        icon: 'notification',
      },
    },
  ],
}
