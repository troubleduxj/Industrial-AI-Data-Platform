import type { RouteRecordRaw } from 'vue-router'

const Layout = () => import('@/layout/index.vue')

const route: RouteRecordRaw = {
  name: 'System',
  path: '/system',
  component: Layout,
  redirect: '/system/user',
  meta: {
    title: '系统管理',
    icon: 'mdi:cog-outline',
    order: 1,
  },
  children: [
    {
      name: 'User',
      path: '/system/user',
      component: () => import('./user/index.vue'),
      meta: {
        title: '用户管理',
        icon: 'mdi:account-multiple-outline',
        keepAlive: true,
      },
    },
    {
      name: 'Role',
      path: '/system/role',
      component: () => import('./roleV2/index.vue'),
      meta: {
        title: '角色管理',
        icon: 'mdi:account-key-outline',
        keepAlive: true,
      },
    },
    {
      name: 'Menu',
      path: '/system/menu',
      component: () => import('./menu/index.vue'),
      meta: {
        title: '菜单管理',
        icon: 'mdi:menu',
        keepAlive: true,
      },
    },
    {
      name: 'Dept',
      path: '/system/dept',
      component: () => import('./dept/index.vue'),
      meta: {
        title: '部门管理',
        icon: 'mdi:office-building-outline',
        keepAlive: true,
      },
    },
    {
      name: 'Api',
      path: '/system/api',
      component: () => import('./api/index.vue'),
      meta: {
        title: 'API管理',
        icon: 'mdi:api',
        keepAlive: true,
      },
    },
    {
      name: 'ApiGroups',
      path: '/system/api/groups',
      component: () => import('./api/groups/index.vue'),
      meta: {
        title: 'API分组管理',
        icon: 'mdi:folder-multiple-outline',
        keepAlive: true,
      },
    },
    {
      name: 'DictType',
      path: '/system/dict',
      component: () => import('./dict/DictType/index.vue'),
      meta: {
        title: '字典类型',
        icon: 'mdi:book-outline',
        keepAlive: true,
      },
    },
    {
      name: 'DictData',
      path: '/system/dict/data',
      component: () => import('./dict/DictData/index.vue'),
      meta: {
        title: '字典数据',
        icon: 'mdi:database-outline',
        keepAlive: true,
      },
    },

    {
      name: 'SystemParam',
      path: '/system/param',
      component: () => import('./param/index.vue'),
      meta: {
        title: '系统参数',
        icon: 'mdi:tune',
        keepAlive: true,
      },
    },
    {
      name: 'AuditLog',
      path: '/system/auditlog',
      component: () => import('./auditlog/index.vue'),
      meta: {
        title: '审计日志',
        icon: 'mdi:file-document-outline',
        keepAlive: true,
      },
    },

    {
      name: 'ComponentManagement',
      path: '/system/components',
      component: () => import('./components/index.vue'),
      meta: {
        title: '组件管理',
        icon: 'material-symbols:widgets',
        keepAlive: true,
      },
    },
  ],
}

export default route

