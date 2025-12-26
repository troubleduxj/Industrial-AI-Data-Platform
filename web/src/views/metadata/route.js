/**
 * 元数据管理路由配置
 * 
 * 说明：此文件定义"元数据管理"菜单及其子路由
 * 整合了原有的"设备字段配置"和"数据模型管理"
 */

const Layout = () => import('@/layout/index.vue')

export default {
  name: 'MetadataManagement',
  path: '/metadata',
  component: Layout,
  redirect: '/metadata/fields',
  meta: {
    title: '元数据管理',
    icon: 'database', // 使用 database 图标
    order: 20, // 排序：在系统管理之前，设备分类之后
    requiresAuth: true,
  },
  children: [
    {
      name: 'UnifiedConfig',
      path: 'unified',
      component: () => import('./unified/index.vue'),
      meta: {
        title: '统一配置管理',
        icon: 'settings',
        requiresAuth: true,
      },
    },
    {
      name: 'DeviceFieldConfig',
      path: 'fields',
      component: () => import('./fields/index.vue'),
      meta: {
        title: '字段配置管理',
        icon: 'list',
        requiresAuth: true,
      },
    },
    {
      name: 'DataModelConfig',
      path: 'models',
      component: () => import('./models/index.vue'),
      meta: {
        title: '数据模型管理',
        icon: 'chart-graph', // 使用图表图标
        requiresAuth: true,
      },
    },
    {
      name: 'DataModelMapping',
      path: 'mapping',
      component: () => import('@/views/data-model/mapping/index.vue'),
      meta: {
        title: '字段映射管理',
        icon: 'link',
        requiresAuth: true,
      },
    },
    {
      name: 'DataModelPreview',
      path: 'preview',
      component: () => import('@/views/data-model/preview/index.vue'),
      meta: {
        title: '模型预览测试',
        icon: 'eye',
        requiresAuth: true,
      },
    },
  ],
}
