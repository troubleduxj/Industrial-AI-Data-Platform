/**
 * 权限配置管理路由配置
 */

const permissionConfigRoutes = [
  {
    path: '/system/permission-config',
    name: 'PermissionConfig',
    component: () => import('@/views/system/PermissionConfig.vue'),
    meta: {
      title: '权限配置管理',
      requiresAuth: true,
      permissions: ['system:permission:config'],
      icon: 'material-symbols:security',
      breadcrumb: [
        { title: '系统管理', path: '/system' },
        { title: '权限配置管理', path: '/system/permission-config' },
      ],
    },
  },
  {
    path: '/system/permission-config/role',
    name: 'RolePermissionConfig',
    component: () => import('./RolePermissionConfig.vue'),
    meta: {
      title: '角色权限配置',
      requiresAuth: true,
      permissions: ['system:role:permission'],
      icon: 'material-symbols:person-check',
      breadcrumb: [
        { title: '系统管理', path: '/system' },
        { title: '权限配置管理', path: '/system/permission-config' },
        { title: '角色权限配置', path: '/system/permission-config/role' },
      ],
    },
  },
  {
    path: '/system/permission-config/user',
    name: 'UserPermissionView',
    component: () => import('./UserPermissionView.vue'),
    meta: {
      title: '用户权限查看',
      requiresAuth: true,
      permissions: ['system:user:permission:view'],
      icon: 'material-symbols:person-search',
      breadcrumb: [
        { title: '系统管理', path: '/system' },
        { title: '权限配置管理', path: '/system/permission-config' },
        { title: '用户权限查看', path: '/system/permission-config/user' },
      ],
    },
  },
  {
    path: '/system/permission-config/editor',
    name: 'PermissionEditor',
    component: () => import('./PermissionEditor.vue'),
    meta: {
      title: '权限配置编辑器',
      requiresAuth: true,
      permissions: ['system:permission:editor'],
      icon: 'material-symbols:edit-note',
      breadcrumb: [
        { title: '系统管理', path: '/system' },
        { title: '权限配置管理', path: '/system/permission-config' },
        { title: '权限配置编辑器', path: '/system/permission-config/editor' },
      ],
    },
  },
  {
    path: '/system/permission-config/import-export',
    name: 'ConfigImportExport',
    component: () => import('./ConfigImportExport.vue'),
    meta: {
      title: '配置导入导出',
      requiresAuth: true,
      permissions: ['system:permission:import', 'system:permission:export'],
      icon: 'material-symbols:import-export',
      breadcrumb: [
        { title: '系统管理', path: '/system' },
        { title: '权限配置管理', path: '/system/permission-config' },
        { title: '配置导入导出', path: '/system/permission-config/import-export' },
      ],
    },
  },
]

export default permissionConfigRoutes
